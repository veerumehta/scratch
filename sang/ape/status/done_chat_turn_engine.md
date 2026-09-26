# The chat pipeline as an application turn engine

Status: done, 2026-09-25, in v2.5.5 (japes `a1aa7f79`..`f70c8f10` on `v2.5.5`). Written against `578744f3`.

Source: the Notion page "jazzx-assistant to JAPES chat.py Transition" (author not shown on the page),
read as input rather than instruction. Measured against jazzx-assistant `origin/dev`
(`src/jazzx_assistant/engine.py`, `ReasoningEngine`).

Prior art, both built in v2.5.2 and still sitting in `plans/`: `plan_streaming_chat_pipeline.md`
(whole pipeline on the streaming path, `components=` on `stream_chat_turn`) and
`plan_chat_turn_history_contract.md` (`ChatTurn.history`, one byte budget, gate window). Both move
to `status/done_*` as part of this work.

## 1. The spec against the code

The spec was written against japes v2.5.0 (`ef01fe00`, jazzx-assistant's pin). Four of its
"missing" items shipped in v2.5.2.

| Spec says missing | Current `chat.py` |
|---|---|
| Caller-supplied history, one budget, same view for gate and agent | **Done.** `ChatTurn.history`, `history_budget_bytes`, `turn_messages`, `gate_messages`. `trim_to_byte_budget` is byte-for-byte jazz's `trim_history` (kb x 1024). |
| One lifecycle for blocking and streaming | **Mostly done.** `stream_chat_turn` runs the full pipeline via `answer_stream_step` + a rendezvous sink. |
| Streaming routes only validate/gate errors through `on_step_error` | **False now.** Both paths hand every stage to `on_step_error`. |
| Workspace hold/release | **Done.** `_turn_workspace`. |
| Component overrides on streaming | **Done.** `components=`. |

Genuinely missing, for jazz:

1. **Typed grounding.** Jazz grounds with one provider returning a `GroundedContext`.
2. **An answer that is not `InteractiveAgent.respond`.** Jazz builds an orchestrator per turn.
3. **A compose phase** between the answer and `finalize` (citations, LOS recipients, source
   humanization, relay flush, leak checks). `finalize` today is also where persistence happens.
4. **An application value on the terminal result**, on both paths.
5. **A stable error code** alongside the existing user (`answer`) / operator (`incomplete_reason`)
   split.
6. **Persistence the caller owns.** `finalize_step` always persists escalate/refuse via the agent.
7. **Gate output beyond route + reason**: jazz keeps a `GateVerdict` and a gate-produced refusal.
8. **Cancellation between stages.** Documented on `ChatTurn.cancel`, not implemented.

Defects in the existing code:

- `stream_chat_turn` derives its pipeline from `escalate is not None` and `bool(turn.sources)`, so a
  caller's `components["escalate"]`, or `components["ground"]` on a turn without `sources`, is
  silently dropped. Jazz's grounding is the second case.
- `run_chat_turn` and `stream_chat_turn` resolve the final value differently: `run_chat_turn` can
  return `None` for a turn `stream_chat_turn` would answer with a decline or a cancelled reply.
- Stale prose: the module docstring, `build_gate_pipeline`'s docstring, `ChatTurn.grounded`,
  `ground_step`, `_notify_turn_complete`, `stream_chat_turn`, and `ChatTurn.cancel`.

## 2. Design principle: the house pattern, not new vocabulary

The spec proposes `ChatSpec` (typed hooks), `ChatResult` (a new terminal type), a `prepare` step and
a persistence-policy enum. Against the other japes pipelines, each introduces a concept the house
pattern already covers:

- **Optional behaviour is an optional step id.** `investigation_loop` declares `persist` unbound;
  `document_ingest` does the same for `package`/`collection`. An unbound step is recorded skipped,
  and a bound one gets tracing, `on_step` and `on_step_error` for free, which a bare hook does not.
- **Builders take kwargs plus `overrides=`.** Spread, document, vocabulary and policy pipelines have
  no Spec class. `InvestigationSpec` is the exception, not the norm.
- **One runner per pipeline, returning what the pipeline produces.**

So:

| Spec | This plan |
|---|---|
| `prepare` step | Dropped. History trim already on `ChatTurn`; config/ids ride `ChatTurn.metadata`. |
| `ChatSpec` of hooks | Dropped. Jazz's phases are step components via `overrides=`, reading `state.emitted`. |
| `persistence_policy` enum + `persist` hook | A `persist` step. Default component = agent persistence (today's behaviour); override = app writes; `{"persist": None}` = caller writes. |
| `ChatResult` + new runners | Dropped. `InteractiveResponse` stays the turn envelope, as `refuse_step`, `default_step_error` and `cancelled_response` already use it. App value on `.output`; new `error_code` field. |
| `execute` step id | Stays `answer`; `on_step` consumers key on ids. |

Known cost: a failed step is still `incomplete=True`, the flag the agent uses for max-turns;
`error_code` is what separates them. Cost of the component style: `(state) -> value` is less
self-documenting than a typed hook signature, which every other japes pipeline already accepts.

## 3. The design

Pipeline: `validate -> gate -> [ground] -> (escalate | answer | refuse) -> compose -> persist -> finalize`.

- **compose**: new step id, unbound by default (skipped). A bound one reads the branch's value and
  returns the turn's `InteractiveResponse`. Runs on every route including refuse.
- **persist**: new step id. Default component is the current side-branch persistence moved out of
  `finalize_step`. `finalize_step` becomes pure resolution.
- **finalize**: returns `compose`'s value when it ran, else the branch's.
- **Pipeline from components**: `stream_chat_turn` builds its pipeline from what is bound.
- **One resolver** (`_final_response`) for both runners.
- **Cancel**: every chat guard also requires the turn not cancelled; the resolver returns
  `cancelled_response`. `asyncio.CancelledError` still propagates.
- **Fields**: `ChatTurn.metadata: dict`; `GateDecision.verdict: Any`, `.refusal: str`;
  `InteractiveResponse.error_code: str`. `default_step_error` sets `error_code=f"{step.id}_failed"`.
  `refuse_step` uses `gate.refusal` when set.
- **`build_chat_components(..., overrides=None)`**, merged last, as `build_investigation_components`.
- **Streaming a custom answer**: the sink is exposed on the turn so a bound `answer` component can
  publish tool/reasoning/delta events; japes defines no frames.

## 4. Jazz mapping

| `ReasoningEngine` | chat pipeline |
|---|---|
| `trim_history` over history + question | `ChatTurn.history`, `history_budget_bytes = max_session_size_kb * 1024` |
| `_run_gate` | `classify` returning `GateDecision(route, reason, verdict, refusal)` |
| `_ground` + `GroundingProvider` | `overrides={"ground": ...}` emitting `GroundedContext` |
| `_run_orchestrator` + feedback | `overrides={"answer": ...}` emitting `AssistantReply` |
| `_compose` | `overrides={"compose": ...}` returning `InteractiveResponse(output=AnswerResult)` |
| `AnswerResult(outcome="error", error_code=...)` | `on_step_error` returning `InteractiveResponse(incomplete=True, error_code=...)` |
| adapter persistence | `overrides={"persist": None}` |

Status lanes stay jazz's: `on_step` start/end events, or inside the components.

## 5. Sequencing (one branch, one review round per step)

1. Existing-code fixes: pipeline from components, one resolver, cancel between stages, stale prose.
2. `compose` and `persist` step ids, `finalize_step` split, `overrides=`.
3. Fields: `ChatTurn.metadata`, `GateDecision.verdict`/`refusal`, `InteractiveResponse.error_code`;
   sink exposed for a custom streaming answer.
4. Docs: ARCHITECTURE (chat turn engine), CHANGELOG, a jazz-shaped example.
5. Move the two built plans to `status/done_*`; this one when step 4 lands.

## 6. What would make this wrong

- **If jazz wants to keep `ReasoningEngine` as the spine** and only borrow pieces. Then steps 1 and
  3 are the deliverable and step 2 is speculative. Confirm with the Notion page's author.
- **If a second consumer needs a `prepare` step** for something other than history. Add it then.
- **If `.output` as the app value proves too loose** for a consumer that wants typing. A generic
  `InteractiveResponse[T]` is the extension, not a second envelope.
