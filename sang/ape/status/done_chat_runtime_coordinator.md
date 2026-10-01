# Plan: the chat runtime coordinator (jazzx-assistant's second requirements page)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-29. Phases A and B built and reviewed clean on `v2.5.6` (shipped in 2.5.6);
Phase C built on `v2.5.7` (see "Phase C built" below). Source: the Notion page "Requirements on
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

## Phase B design: the coordinator on `jazzx_sdk.runs` (2026-09-29)

One run runtime, extended in place. Every increment lands in `jazzx_sdk/runs/`, keeps
`TurnDispatcher` / `ResilientRunner` / `CaseRunner` working, and serves chat turns and case runs
alike.

- **B1: admission and terminal ordering.**
  - `TurnRunStore.admit(run, replacement=...)`, atomic per key:
    - `wait`: today's FIFO;
    - `reject`: `TurnRejected` while the key has an active run;
    - `supersede`: cancel the key's queued runs, stop its running one (the existing
      `request_stop_conversation`), then queue the new one, which `claim_next` admits only once
      the old one is terminal. The old run's events stay on its own `run_id`, which is the fence.
  - Both runners commit a run's terminal state before journaling its `done` event, so a reader
    that sees `done` finds the run terminal. Today both journal first.
- **B2: stop reasons and deadlines.**
  - `TurnRun.stop_reason`, the typed `CancelReason` (`user`, `superseded`, `deadline`, `drain`),
    set with the stop flag, so a superseded run and a user-stopped run are told apart.
  - A total deadline per run (`deadline_seconds`, monotonic) stops it with `deadline`. Phase
    deadlines wait for a consumer that needs them.
- **B3: lanes and capacity.**
  - `TurnRun.lane` (e.g. interactive / reasoning / bulk).
  - Per-lane concurrency limits and a per-(tenant, principal, lane) cap, enforced in
    `claim_next` against RUNNING rows, so they hold across replicas with the DB store.
  - A capacity refusal leaves the run queued, and the next drain of any key in that lane picks it
    up.
  - This is policy-workbench's lane model.
- **B4: the chat coordinator.**
  - A turn runs `stream_chat_lifecycle` as a run, from a turn factory that rebuilds the
    `ChatTurn` from the run's stored input. Stages and adapters are the application's.
  - The coordinator journals the lifecycle's events with the run's `seq`.
  - It applies `DurabilityPolicy` (commit before delivery, delivery before best-effort persist,
    caller managed, none) through an application commit hook, called at most once.
  - It maps `DisconnectPolicy` (cancel / detach / abandon) onto the stop flag and the journal.
  - A handle gives start, idempotent cancel with a reason, and result.
  - Plato's streaming chat route moves onto it, which is what puts the lifecycle under
    Plato-hosted assistants.
- **B5: drain and close.**
  - A bounded `drain` / `close` on the coordinator settles admitted runs and reports what it
    could not.
  - A standalone worker loop (claim across keys, heartbeat, drain, max lifetime) for
    policy-workbench's worker process.

Deferred, as above: session-scoped resources, single-flight, bounded outlets beyond the journal,
duplicate-turn TTL.

### Built (2026-09-29, on `v2.5.6`)

- B1-B3: `aa59ddc6`, `2e6b3cf0`, `d77b39d3`, `45f569e0`.
- B4: `569baeeb`. `runs.ChatCoordinator` in `jazzx_sdk/runs/chat.py`; Plato's `chat/stream` runs
  on it. Deviations from the page:
  - `DurabilityPolicy` has three values. `caller_managed` behaves as `none` here, since the
    journal is the runs layer's own record, so it is not a separate value.
  - "Delivery" is the terminal journal event. `delivery_before_best_effort_persist` awaits the
    commit inside `execute`; no follow-up work is retained.
  - An abandoned turn is never committed; the page's "only when configured" is not configurable
    yet.
  - A disconnect reason is `disconnected` (cancel) or `abandoned` (abandon), both new
    `CancelReason` values.
- B5: `ef1d483e`. `runs.settle_runs`, `ChatCoordinator.close`, `runs.RunWorker`.
- Open: phase deadlines, per-phase grace, typed indeterminate commit state. The Postgres advisory
  lock test is done (v2.5.7, `tests/test_db_locking.py`).

## Phase C design (2026-09-30), from jazzx-assistant's `ws/` (its `origin/dev`, ea690dd)

Read before designing: `ws/` has one session per socket (and loan), 25 sessions and 2 parallel
turns per socket, a 900s monotonic idle TTL swept by japes' own `SessionReaper`, a per-session
grounding single-flight (followers replay history then follow live; a follower's cancel leaves the
leader; a failed or degraded result is not cached), per-turn contextvars (identity, trace,
publisher), a `followups` set that drain waits 5s for, a bounded 256-frame send queue (ephemeral
frames dropped when full, a durable frame evicts the oldest ephemeral, all-durable detaches), a
superseded-id fence dropping non-durable frames, a live duplicate id refused, completed duplicates
left to the store's idempotency, a 300s work timeout with a 5s write grace, and a failed or
timed-out required write that fails the turn and never reads as success.

- C1 **Deadlines** (built): `DeadlinePolicy(total_seconds, stages, persist_grace_seconds)` on
  `ChatTurn`. Work stages share the total; `persist` has only its grace; `finalize` is outside the
  total. A stage past budget is a `deadline` `ChatError` (retryable).
- C2 **Commit grace and indeterminate commits:** `ChatCoordinator(commit_grace_seconds=,
  reconcile=)`. A commit past its grace is `CommitState` `indeterminate`, recorded on the run; a
  `commit_before_delivery` turn with one fails as `commit_indeterminate`, never delivered as a
  success. `reconcile(run_id)` asks the application (`confirmed` / `failed` / `indeterminate` /
  `superseded`) and records the answer. A `supersede` on a key whose latest run is still
  indeterminate is refused (`TurnRejected`), as `ws/` refuses a barge-in whose interrupted write
  failed.
- C3 **Persistence values:** the page's four (`agent_owned`, `application_hook`, `external`,
  `none`), with `agent` and `caller` read as `agent_owned` and `external`.
- C4 **Namespaces and duplicate turns:** a `turn_id` on submit. A live duplicate is refused; a
  completed one within `duplicate_ttl_seconds` returns the existing run (replay), since the
  consumers' stores are idempotent on that id. `coordination_key(namespace, key)` names a key in
  an explicit namespace.
- C5 **Sessions and resources** (`jazzx_sdk.runs.session`): `ChatSession` (resources, followups,
  monotonic `last_active`), `SessionRegistry` (capacity, per-session turn cap, draining refuses
  first, `reap_stale` for `SessionReaper` that skips a session with pending work, bounded `drain`
  reporting what did not settle), `SingleFlight` (start-or-join, replayed progress, `cacheable`
  predicate, failures and cancellations never cached, a follower's cancel does not cancel the
  work), and per-turn async context providers entered inside the turn task.
- C6 **Typed events and a bounded outlet:** a `TurnEvent` envelope (turn id, key, session id,
  per-turn seq, kind, `ephemeral` or `required`) and `BoundedOutlet` (capacity, drop-ephemeral /
  evict-oldest-ephemeral / detach-when-all-required, terminal flush timeout, a supersede fence).
- C7 **Declarative assistant stages:** an assistant profile's `lifecycle:` block declares gate,
  ground and compose kinds from data, so Plato builds an assistant's components without Python.

### Phase C built (2026-09-30, on `v2.5.7`)

C1 `f8b99120`, C2 `4ee7eca1`, C3 `f91c24ab`, C4 `2923a840`, C5 `6b26001e`, C6 `0afdab3a`,
C7 `e9fffcbc`; with the page's small items first (`d8c8ecf5` runs exports pinned, `429dea26`
Plato's blocking `/chat` on the lifecycle plus `ChatTurn.trace_id`) and the guide `docs/CHAT_LIFECYCLE.md`.
Deviations and what is still open:
- C4 replays a live duplicate (joins the original) by default where `ws/` refuses it; `reject`
  is the `ws/` behaviour. The duplicate window is the key's newest `RECENT_RUNS_CHECKED` runs.
- C5's session is process-local and not tied to the coordinator: a turn factory reaches it
  (`ChatTurnSpec.context=[session.turn]`). Reconnection and adoption stay the application's.
- C6's `required` / `ephemeral` split is by default classifier (delta, error, terminal required),
  which matches `ws/`'s durable set (`llm_chunk`, `final_result`, `done`, `error`).
- C7 declares policies and a `scope` gate only. Open: declarative ground (workspace grounding from
  declared sources) and compose kinds (identifier humanizing, leak checks as output-guardrail
  kinds, an email draft as a declared output schema), and the two-agent preliminary answer.
- `TODO(sqlite-read-then-write-unserialized)`: the store's claim paths on sqlite.
