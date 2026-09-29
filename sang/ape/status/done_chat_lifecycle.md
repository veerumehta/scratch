# Done: the chat lifecycle (jazzx-assistant's first requirements page)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: done. Source: the Notion page "Requirements for japes 2.5.6 chat.py". Built on
`v2.5.6` in the order below (`d7238eaa..df4bd2a6`, reviewed clean after 4 rounds, then folded into
`ab080492` and squashed to `plato` as `43c13d18`). The adoption note for jazzx-assistant follows
the review. The follow-on page is `plans/plan_chat_runtime_coordinator.md`.

# Review: "Requirements for japes 2.5.6 chat.py" (JazzX Assistant lifecycle)

Checked against `jazzx_sdk/pipelines/chat.py` on v2.5.6 (3c1cc377) and jazzx-assistant
`origin/dev` (`engine.py` ReasoningEngine).

## Verdict

Agree with the direction, and all six needs are real. Four of them are gaps chat.py has today.
Disagree on the shape in three places, each of which would add a parallel mechanism where
japes already has one:
- two runner families;
- a new error-policy type beside `StepErrorHandler`;
- a four-value persistence enum threaded into `InteractiveAgent`.
Also, one ask contradicts a deliberate rule: compose, persist and finalize are exempt from
cancellation.

Also, "changes must be additive" is stricter than we need. The only chat.py consumers are jaci's
demo page and Plato's authoring chat, and jazzx-assistant is the first real one. So the better
move is to evolve `run_chat_turn`/`stream_chat_turn` onto the generic core, not to fork a second
pair.

## Per ask

1. **prepare**: agree, cheap, symmetric. The motivation is real. ReasoningEngine's own comment
   records the drift: the gate classified over untrimmed history while the orchestrator answered
   over trimmed history. japes has the same split today, with `gate_messages` (a window) against
   `turn_messages` (a budget).
   Shape: an optional stage, bound through `overrides` and added by `pipeline_for` when bound,
   exactly as `compose` was. The reference gate and answer read `state.emitted["prepare"]` when
   it is a `PreparedTurn` (`messages`, plus an application slot); otherwise they call
   `turn_messages()` as now. This mirrors the investigation kind's `pre_loop`.
   Push back on "application-owned opaque value": give it a small typed envelope (`messages` +
   `app: Any`). Otherwise the reference gate and answer can't use it, and it only helps fully
   custom stacks.

2. **Generic result**: agree on the need. `_final_response` drops anything that isn't an
   `InteractiveResponse`, which forces the ".output on an InteractiveResponse" workaround.
   - Shape: one core `ChatRun[T]` (`value`, `route`, `conductor: ConductorRun`, `status`,
     `error`). Make `run_chat_turn` an adapter that resolves `InteractiveResponse` from it, not a
     second runner.
   - Align the status vocabulary with the engine's: `ConductorRun.status` is
     complete/halted/interrupted/suspended, and `TurnRun` uses interrupted/completed/failed/
     cancelled. A fourth vocabulary (completed/cancelled/incomplete/failed) is drift. The
     resolution order (finalize, compose, branch, incomplete) matches `_delivered` today.
   - Agree: `stream_chat_turn` should not require `agent=` when every stage is custom.
   - `ChatFinalEvent` is fine, as long as there is one terminal event type per stream.
   - "Application events typed through a protocol or generic parameter" is over-specified.
     `turn.publish` already carries `Any` and the stream refuses a stage's `done`; keep it.

3. **Persistence ownership**: the need is real; the enum is heavier than necessary.
   - Zero agent writes is already reachable. `InteractiveAgent` persists only when
     `spec.conversation`, a store and a `session_id` are all present, and caller-owned history
     goes on `ChatTurn.history` (`check_history_ownership` refuses both at once). What is
     missing is an assertion, not a mode.
   - Proposed: `ChatTurn.persistence: Literal["agent", "caller"]` (default "agent"). "caller"
     makes the runner refuse a turn that could write through the agent: a `session_id` with a
     conversation-active agent, or a bound reference `persist`. That is enforceable at the
     boundary without threading a policy into `InteractiveAgent.respond`.
   - "external" and "none" are indistinguishable to japes (japes writes nothing either way);
     collapse them. "application_hook" is simply a bound `persist` component, and it already
     runs after compose and before finalize.
   - `required`/`best_effort`: agree. Today a bound persist that raises goes through
     `on_step_error` and degrades the whole turn, while the reference side-branch persist is
     fail-soft. A per-binding failure policy is reasonable.

4. **Safe errors**: agree on the leak, disagree on the new type.
   - `default_step_error` copies `reason(exc)` into `InteractiveResponse.incomplete_reason`,
     which clients can show. That is a real user-boundary leak.
   - Keep `StepErrorHandler` (it already can halt, substitute or raise). Add a `ChatError` value
     (`code`, `stage`, `user_message`, `operator_detail`, `retryable`). The default handler logs
     `operator_detail` and puts only `code` and `user_message` in the reply.
   - Workspace acquire and release failures are unclassified today: they raise raw, outside the
     engine. Agree on classifying them.
   - Symmetry: the same class of leak exists in our new `CaseRunner`, which serves `str(exc)` as
     `error` on `GET /runs/{id}` and in the journal. Fix both with one error value.

5. **Cancellation**: two parts.
   - Stream cleanup: agree, it is a bug. On `GeneratorExit` and `CancelledError`,
     `stream_chat_turn` calls `run_task.cancel()` without awaiting the task, so workspace
     release can race the still-unwinding engine.
   - Checkpoints: use the engine's `stop_requested` (added in 2.5.6, checked before every step)
     wired to `turn.cancel`, instead of adding more per-guard checks. That gives "before every
     phase" by construction.
   - Conflict: chat.py deliberately does not cancel-guard compose, persist or finalize, so an
     answer produced before the cancel is still delivered. The ask wants cancel before compose,
     persist and finalize, which drops produced answers. That fits barge-in, but it is a policy
     choice, not a fix. Make it explicit (for example `cancel_after_answer: "deliver" | "drop"`),
     with jazzx-assistant choosing "drop".

6. **Completion on every path**: agree.
   - Raw propagation (`on_step_error=None`), workspace failures and abandonment currently skip
     `on_complete`. Abandonment only logs `chat.abandoned`.
   - One `on_complete(ChatRun)` with a distinct abandoned status is the generalizable form.
   - Keep the borrowed-run rule as it is.

## Evolutionary path (suggested order)

1. `ChatRun` core + adapters (2), with the status vocabulary aligned.
2. `prepare` (1).
3. `ChatError` and the safe default (4), plus the same change in `CaseRunner`.
4. Engine `stop_requested` for chat, the await-on-abandon fix, and the explicit post-answer
   cancel policy (5).
5. Completion on every path (6).
6. The `persistence="caller"` assertion and the persist failure policy (3).

Each step stands alone and is testable on the jazzx-assistant parity checklist the doc lists.

## What jazzx-assistant's code shows (origin/dev, and origin/feat/preliminary-answer)

- **Their core is `ReasoningEngine.answer`** (`engine.py:262`), a straight line: trim history once,
  gate, ground, orchestrator, compose. It returns `AnswerResult` and never raises for an expected
  failure. The engine persists nothing; the two adapters do.
- **Ask 1 (prepare) is their proven rule.** `engine.py:~290` bounds history once over history plus
  the question, and says why: per-consumer trimming drifted. That is exactly the gate/answer split
  in japes. The prepared value is the trimmed messages plus `request.config`.
- **Ask 2 (generic result) and ask 4 (safe errors) mirror `AnswerResult`.** It has
  `outcome: answered|refused|error`, `error_code`, `user_message` (what a user reads) and
  `error_detail` (what an operator reads, possibly a URL or a status). The doc's `ChatError` is
  that triple. A refusal is a successful outcome, not an error, matching `route="refuse"`.
  Adopting the split in japes is the absorb-from-the-canonical-assistant move.
- **Ask 3 (persistence) is a guarantee, not a missing mode.** They already get zero agent writes:
  the gate calls `respond(..., session_id=None)` (`gate/gate.py:119`), and the orchestrator calls
  `respond(messages=messages)` with no session (`engine.py:663`). Their two adapters order
  persistence oppositely: the queue adapter writes after delivery, best-effort; the WebSocket
  coordinator (`ws/turn.py`) writes before delivery, and a failed write fails the turn. That
  confirms `required`/`best_effort`, and it keeps ordering relative to delivery out of japes,
  since delivery is theirs. So the `persistence="caller"` assertion is enough for them.
- **Ask 5 (cancellation) matters in one place, stream cleanup.** Barge-in and cancel are both a
  hard `task.cancel()` (`ws/router.py:527,549`), not a cooperative flag. Barge-in then
  `await asyncio.wait({task})` so the replacement starts only after the old turn is terminal.
  `stream_chat_turn`'s unawaited `run_task.cancel()` breaks that guarantee: the outer task can
  finish while the engine is still unwinding, and the grounding directory may still be in use.
  Fix that first. The cooperative checkpoint list and the post-answer cancel policy matter less
  to them, because hard cancel stops at any await. Keep it as the explicit policy suggested
  above, for callers that use `turn.cancel`.
  - Their core relies on `CancelledError` propagating: `ws/turn.py` swallows it at exactly one
    boundary and records the turn as `interrupted`. japes must never convert it, which the doc
    already requires and `run_chat_turn` already does.
- **Their newest branch (`feat/preliminary-answer`) is not in the doc, but fits it.** A fast
  specialist answers first and that answer is shown on screen; the orchestrator is then told so
  and writes only what it adds. That is a pre-answer publish (through `turn.publish`, which
  accepts anything but `done`) plus a compose that joins the two halves. No new stage is needed,
  but `ChatRun.value` has to be compose's joined result, and it is under the doc's resolution
  order.
- **They stream progress, not tokens.** The orchestrator call is blocking; the stream carries
  status and reasoning events and one final result (their own `FinalResultEvent` and
  `TurnDoneEvent`). So the generic stream runner mainly needs typed application events plus one
  terminal event, which matches ask 2's shape.

## Net

Agree with all six needs. Every one is evidenced in their code, and 1, 2 and 4 are patterns
their assistant proved that japes should absorb. Counter-proposals stand: one core runner with
adapters, not two families; `ChatError` on the existing `StepErrorHandler`; a `caller` assertion
instead of the four-value enum; the engine's `stop_requested` for checkpoints. Priority for them:
the stream-cleanup await (5), then the `ChatRun` generic result (2), prepare (1) and `ChatError`
(4), then completion on every path (6), then the persistence assertion (3).


# japes 2.5.6 chat lifecycle: what jazzx-assistant can use

Built on japes `v2.5.6` (local, unpushed): commits `d7238eaa..df4bd2a6`.

```python
from jazzx_sdk.pipelines.chat import (
    ChatTurn, PreparedTurn, build_chat_components, run_chat_lifecycle, stream_chat_lifecycle,
    ChatFinalEvent, ChatRun, ChatError)

components = build_chat_components(agent=None, overrides={
    "prepare": prepare_jazz_turn,        # emit PreparedTurn(messages=trimmed, app=config) or your own
    "gate": run_jazz_gate,               # read state.emitted["prepare"]
    "ground": resolve_jazz_grounding,
    "answer": run_jazz_orchestrator,     # publish progress via state.context.publish
    "compose": compose_jazz_answer,      # return AnswerResult
    "persist": None,                     # your transports own durability
})
turn = ChatTurn(message=q, history=history, persistence="caller", cancel_after_answer="drop")
run: ChatRun = await run_chat_lifecycle(turn, components=components)   # run.value is AnswerResult
async for ev in stream_chat_lifecycle(turn, components=components):
    if isinstance(ev, ChatFinalEvent): final = ev.run
```

How the asks were mapped:
- **prepare.** An optional stage. `PreparedTurn` (messages ending with the user's message, plus
  `app`) is read by the reference stages; your own prepare may emit anything.
- **Generic result.** `ChatRun`: `status` is completed, interrupted, failed or abandoned; also
  `value`, `route`, `conductor`, `error` and `diagnostics`. A refusal is completed with
  route=refuse. `run_chat_turn` and `stream_chat_turn` keep their contracts, as adapters.
- **Errors.** `chat_step_error` (the default) gives a `ChatError`: code `<stage>_failed`, a
  generic `user_message`, the exception text in `operator_detail`. `on_step_error=None`
  propagates raw, and `CancelledError` is never converted. Workspace acquire and release failures
  are classified.
- **Persistence.** With `persistence="caller"`, the runner refuses a turn with a session_id, or
  with the reference persist bound. With those gone, zero agent or session writes are
  guaranteed. `persist_failure` is `required` or `best_effort`. "external" and "none" collapse
  into `caller`.
- **Cancellation.**
  - A stream now waits for its engine to unwind (and the workspace to be released) before it
    ends, on abandonment and on task cancel.
  - With `cancel_after_answer="drop"`, `turn.cancel` is checked before every stage, so a
    barge-in supersedes a produced answer.
  - Hard `task.cancel()` propagates, as your coordinator expects.
- **Completion.** `on_complete(ChatRun)` fires exactly once on every path: completed, failed,
  raised raw (then re-raised), interrupted and abandoned. A raising callback changes nothing.
