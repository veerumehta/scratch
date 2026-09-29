# Plan: the chat runtime coordinator (jazzx-assistant's second requirements page)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-29. Proposed, not yet approved. Source: the Notion page "Requirements on
plato 2.5.6 for chat.py" (JazzX Platform v2.0 / Jazzx-Assistant), edited 2026-09-29.

Prior art, read before this:
- `status/done_chat_lifecycle.md`: the first requirements page, and the lifecycle built for it on
  `v2.5.6` (`d7238eaa..df4bd2a6`, then folded).
- `status/done_JAPES_resilient_interactive_run.md`: the design behind `jazzx_sdk.runs` (durable
  turn record and journal, cooperative stop, per-conversation FIFO, reaper). The coordinator
  below builds on it.
- `plans/note_assistant_turn_requirements.md` (2026-09-11): own / seam / theirs over the same
  assistant. Two of its judgments are revisited here:
  - **R4: bounded delivery was a seam**, with japes not owning the wait. The page now asks for a
    bounded outlet. It is acceptable as a transport-neutral protocol with a reference
    implementation, and the wait on a real socket stays the adapter's.
  - **"A 752-line coordinator" was not to be copied.** The page asks for a reference coordinator
    too, but built from primitives (keyed admission, a terminal state machine, a store protocol,
    an outlet). The coordinator composes them and holds no persistence, delivery or outcome
    logic of its own. That composition, not the monolith, is what is being proposed. A consumer
    whose policy does not fit uses the primitives directly.

The page was edited 2026-09-29. It is a superset of the first page ("Requirements for japes 2.5.6
chat.py"), which v2.5.6 already answers. It adds a process-local coordination runtime on top of
the lifecycle: a turn-store protocol, durability ordering, keyed coordination, sessions, typed
events with outlets, deadlines, disconnect policy, and a reference coordinator with drain and
close. It is, roughly, jazzx-assistant's `ws/` package lifted into japes: `turn.py` (1,388
lines), `router.py` (793), `registry.py` (325), `session.py` (252), `publisher.py` (313),
`grounding.py` (295), `store_backend.py` (351), plus the queue `handler.py` (783).

## Already built on v2.5.6

- **§1 Lifecycle** (prepare, refusal skips ground and answer, application-owned values, same
  lifecycle for blocking and streaming, no transport frames, no coordinator needed):
  `run_chat_lifecycle` / `stream_chat_lifecycle`, `prepare`, `ChatRun`.
  - Value precedence already uses `is not None`, so a false-y value is not conflated with
    absence.
- **§3 Errors:** `ChatError` (code, stage, user_message, operator_detail, retryable),
  `chat_step_error`, convert or propagate, halt or substitute, `CancelledError` never
  converted, callbacks cannot alter the result.
- **§9, part:** `cancel_after_answer` (`deliver` / `drop`); cooperative checkpoints via the
  engine's `stop_requested`; a direct call propagates a hard cancel after observation.
- **§13, part:** one observation per terminal path (completed, failed, raised, interrupted,
  abandoned); a borrowed run is never closed.

## Changed since the first page, and in conflict with what we built

1. **Persistence keeps four values, and a session id must stay usable.** We collapsed to
   `persistence="agent" | "caller"`, and `caller` refuses a turn with a `session_id` (the only
   way to guarantee `InteractiveAgent` writes nothing today). The page now asks for:
   - an explicit no-persist mode on `InteractiveAgent.respond()` / `respond_stream()`;
   - a `session_id` that stays usable for correlation and resource lookup.
   That is a fair ask: refusing the id makes it unusable for correlation. The fix belongs in
   the agent (a `persist=False` / conversation-write switch), after which `caller` can allow a
   `session_id`. `external` vs `none` still behave the same inside japes, but they differ for a
   coordinator (§6 `none` means no store call at all), so the four values are worth keeping at
   the coordinator level.
2. **Generic error categories.** Japes owns categories: stage failure, deadline, capacity,
   cancellation, abandonment, resource, persistence, delivery. `ChatError.code` is free text
   today (`<stage>_failed`, `workspace_acquire_failed`, `persist_failed`); a `category` enum
   alongside it is additive.
3. **Explicit cancel signal and reason.** A coordinator cancels with a reason (user,
   supersession, deadline, drain), not only `Task.cancel()`. `ChatTurn.cancel` is an Event
   with a single `cancel_reason`; this fits as a typed reason on the signal.
4. **Public API surface and a migration guide.** Exports, import-boundary tests, a guide from
   the current chat APIs, and stable serialized discriminators. We have none of this for the
   lifecycle yet (it lives in `pipelines.chat`, with no `__all__`).

## New: the coordination runtime (§2, §5-§8, §10-§12, §14)

- Typed `LifecycleSpec` / `CoordinatorSpec` / `SessionSpec` plus a facade.
- A turn-store protocol: begin, commit, fail, interrupt, reconcile an indeterminate write,
  with fencing tokens and commit markers.
- `DurabilityPolicy`: commit before delivery, delivery before best-effort persist, caller
  managed, none. One ordered terminal state machine per policy.
- Keyed coordination: namespace plus key, `ReplacementPolicy` reject / wait (FIFO) /
  supersede (with a fence for late events), duplicate-turn policy with TTL, and a handle
  (start, idempotent cancel, result replay, outlet attach/detach, the pre-start race).
- Deadlines (total, per phase, protected-write grace, monotonic clocks) and
  `DisconnectPolicy` cancel / detach / abandon.
- Sessions: capacity, drain, idle expiry, resource providers with single-flight,
  per-turn context providers, retained follow-up work, capacity domains in order.
- Typed events with a per-turn sequence and delivery class, a bounded outlet with
  backpressure, coalescing and acknowledged delivery.
- A reference coordinator, plus bounded `drain` / `close` that report unsettled work.

## Our view

**Direction: agree.** jazzx-assistant is the canonical assistant, and the aim is that the next
assistant is close to zero code. This is the right layer to absorb.

**Symmetry: this must not become a second run runtime.** japes already has one in `jazzx_sdk.runs`:
- a turn store protocol (`TurnRunStore`, in-process and DB backends);
- per-conversation FIFO with a single running turn (`claim_next`: the page's `wait`);
- conversation-wide stop of queued and running turns (the start of `supersede`);
- a durable stop flag;
- a journal with a monotonic per-run `seq` and replay from it (the page's event sequence and
  result replay);
- claim, heartbeat and reaper;
- `CaseRunner` for conductor runs on the same store.

The page's coordinator differs in three ways:
- it is process-local;
- the application owns the store's records;
- durability ordering relative to delivery is a policy.

Those are shape differences, not a reason for a parallel system. Proposed:
- `TurnRunStore` becomes (or implements) the page's turn-store protocol, and the
  application-owned store is an adapter behind it.
- The reference coordinator generalizes `TurnDispatcher` / `ResilientRunner` / `CaseRunner`,
  gaining replacement policy, durability policy and deadlines, rather than being a new module
  beside them.
- The journal (`TurnRunEvent`) is the event model: typed events carry the same `seq`.

Otherwise japes ends with two keyed-FIFO run managers and two event sequences, and the next fix
lands in one and not the other.

**Scope: phase it, and push back on a few items.**
- **Phase A (small, fixes our own conflict):** the `InteractiveAgent` no-persist switch; let
  `caller` keep a `session_id`; `ChatError.category`; a typed cancel reason; a public export
  surface for the lifecycle plus a migration note.
- **Phase B:** the coordinator on the runs layer. Replacement policy (reject / wait /
  supersede with a fence), durability policy and terminal ordering, deadlines, disconnect
  policy, handle, drain and close.
- **Phase C:** sessions and resources (capacity domains, single-flight, context providers,
  follow-up work) and bounded outlets.
- **Push back on:**
  - Duplicate-turn retention with TTL, and single-flight semantics for late followers. Both
    are policy-heavy; we should see jazzx-assistant's actual behavior before specifying them.
  - "Stable serialized discriminators" as a contract before the first consumer has run on
    this. Stabilize after jazzx-assistant adopts it, not before.
- **One gap in the page itself:** it says cross-replica exclusion is the application's
  (store fencing). japes' DB-backed `TurnRunStore` already does claim fencing across replicas,
  so building on it gives that for free, which is another reason to reuse it.

## Fit to the two consumers this should serve (2026-09-29)

### Evidence: three copies of one coordination layer

| Concern | `jazzx_sdk.runs` | jazzx-assistant `ws/` | policy-workbench `policyforge` |
| --- | --- | --- | --- |
| Turn record + store | `TurnRunStore` (in-process, DB) | `ws/store_backend.py` | `pf_agent_jobs`, `pf_messages` |
| One active turn per key | `claim_next` (FIFO wait) | barge-in = supersede (`ws/router.py`) | partial unique index; a new turn cancels (supersede) or `on_busy="refuse"` (reject); no wait |
| Stop | durable flag, polled | `task.cancel()` + supersede fence | DB `request_cancel` + Redis kill channel |
| Liveness | heartbeat + `Reaper` | session idle reaper | 30s heartbeat, orphan sweep, 10 min cancel reap |
| Event journal + resume | `TurnRunEvent` seq, SSE `from_seq` | Redis stream + `done.seq` | `pf_agent_events` seq; SSE always from the start, resume by polling |
| Durability order | not a policy | commit before delivery (socket), after (queue) | user message first, assistant once, terminal event last |
| Capacity | none | session cap | lanes (interactive 20 / reasoning 2 / bulk 1), 3 per (project, user, lane) |
| Workers | in-process task | in-process | in-API loop + standalone worker, drain and max lifetime |

Three implementations of the same shape is the case for japes owning it. It is also the case
for owning it **once, durably**. policy-workbench needs a cross-replica queue with workers, which
a process-local reference coordinator (as the page specifies) does not give it, and
`TurnRunStore`'s DB backend already does.

### Do we agree?

- **Consistent:** the lifecycle asks (done) are. The coordinator asks are consistent only if
  they generalize `jazzx_sdk.runs` (`TurnDispatcher`, `ResilientRunner`, `CaseRunner`). A
  process-local coordinator beside it would be a fourth copy.
- **Symmetric:** make replacement policy (reject / wait / supersede) and durability policy
  properties of the runs layer, so chat turns, case runs and a queue worker share them.
  Process-local is then a store choice (`InProcessTurnRunStore`), not a separate runtime.
- **Generalizable:** strong for admission, stop, journal, durability ordering and deadlines,
  all shared by three consumers. Weak for session-scoped resources, single-flight and
  late-follower semantics: one consumer (jazzx-assistant's per-loan grounding cache) and no
  second. Defer those until a second one needs them.
- **Missing from the page:** capacity lanes and fairness caps (policy-workbench's
  interactive / reasoning / bulk lanes and per-user caps). The page's "capacity domains" is
  the start of it; lanes should be in the design from the first cut.
- **Evolutionary:** yes, if phased as above, with Phase B landing inside `jazzx_sdk.runs`.

### Will it help bring up a jazzx-assistant for Acra Lending on Plato?

Only partly, as written. The page targets a Python service that supplies its own components and
adapters. Plato cannot take Python from a pack, and today Plato's chat routes do not run
`pipelines.chat` at all: `plato/api/assistants.py` calls `agent.respond`, and the stream route
runs `agent.respond_stream` through `ResilientRunner`. So none of the lifecycle (prepare, gate,
ground, compose) reaches a Plato-hosted assistant yet. Two things are missing, and neither is
on the page:

1. **Plato's chat routes run the lifecycle,** blocking and streaming, through the same runs layer
   and coordinator policies (barge-in as supersede, commit before delivery). Then the
   coordinator work serves Plato and jazzx-assistant alike.
2. **Declarative stage kinds for an assistant pack,** the chat twin of the conductor kinds
   (`investigation_loop`):
   - `gate`: the manifest scope classifier, with structured refusal wording (mostly exists).
   - `ground`: declared sources, knowledge bindings and document grounding into the turn
     workspace (bindings exist; workspace grounding does not).
   - `answer`: an `InteractiveAgent` with specialist skills (exists).
   - `compose`: citations from sources (exists), identifier humanizing and leak checks as
     output guardrail kinds, an email draft as a declared output schema.
   - The preliminary fast answer: a two-agent answer kind.
   With those, an Acra assistant pack is data on Plato, which is what "the next assistant is
   near zero" means.

### Will it help move policy-workbench's assistant onto the SDK with minimal work?

Yes, for the coordination, if the coordinator is the runs layer; less so as written.
- **Maps directly:**
  - Its RouterAgent classification is a `gate`, and dispatch to five sub-agents is an `answer`
    component.
  - The per-session git worktree is the turn `workspace` (an async context manager, released on
    every path).
  - Staging reconcile plus the single assistant write is `persist` / `compose` under
    `persistence="application_hook"` and commit-before-delivery.
  - Its cancel-on-busy and `on_busy="refuse"` are supersede and reject.
  - It gains SSE resume from `from_seq`, which it lacks today.
- **It keeps its answer executor:** claude-agent-sdk with an in-process MCP tool server. The
  lifecycle takes any `answer` component, and its thinking / tool_call / tool_result events go
  through `turn.publish`. It does not have to move to `InteractiveAgent`, so the OpenAI-vs-Claude
  agent SDK question is not on the critical path. It is if they later want `InteractiveAgent`
  itself.
- **Gaps japes would have to fill for it:**
  - lanes and per-(project, user, lane) caps;
  - a standalone worker process with drain and max lifetime (the runs layer has claim and
    reaper, but no worker loop);
  - moving their job kinds (MACER compare) onto `CaseRunner`-style run kinds.
- **What it would delete:** most of `agent_jobs.py` (1,168 lines), the coordination half of
  `router.py` (3,277), and `worker.py` (633).
