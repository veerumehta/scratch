# `pipelines.chat` against the canonical assistant's turn: what is missing before they adopt it

Status: audit, 2026-09-11. Decides nothing; proposes three changes. Written against japes `138cc90`
on `v2.5.2` and jazzx-assistant at `e5266c8`.

## Why this exists

jazzx-assistant uses `InteractiveAgent` and `InteractiveAgentSpec` but **not** `pipelines/chat.py`:
no reference anywhere to `run_chat_turn`, `stream_chat_turn`, `build_chat_pipeline` or
`ConductorEngine`. It hand-rolls the turn in `engine.py` (905 lines) instead. That is not a verdict
on `chat.py` -- the team has not had a chance to look at it yet and intends to -- so the job is to
find what would not survive contact when they do, and close it first.

The stake is bigger than one consumer: their turn shape is what the next assistant starts from, so
whatever `chat.py` cannot express becomes something the policy-workbench or DSCR assistant copies
out of theirs.

## 1. The two spines agree

This is the part worth stating first, because it means adoption is a real option rather than a
rewrite.

| Their `ReasoningEngine.answer` | `chat.py` |
|---|---|
| gate (deterministic pre-flight) | `gate` step + `chat_guards` routing |
| refuse before anything is downloaded (§10.2) | `"ground": lambda s: _route(s) != "refuse"` |
| ground (provider, not context) | `ground` step over `turn.sources` |
| orchestrator | `answer` step (`InteractiveAgent.respond`) |
| compose | `finalize` step |
| returns, never raises, for expected failures | `on_step_error` + `state.halt` |
| cancellation is not an error turn | `InteractiveResponse.cancelled` / `cancel_reason` |

Four things they had to build that `chat.py` already has, and that a naive reading of its docstring
("the turn is deliberately thin") would miss: **per-source degrading grounding** with progress and
a `required=` escalation, a **per-turn workspace** released whatever the outcome, **cooperative
cancellation** checked between stages, and **side-branch persistence** so a refused or escalated
turn does not leave a hole in history.

## 2. Gap one: the gate and the answer read different inputs (a defect, not a gap)

`structured_classifier_gate` classifies over exactly one message:

```python
messages=[{"role": "user", "content": turn.message}],
```

and `ChatTurn` has no `history` field at all (verified: its fields are `message`, `scope`,
`session_id`, `conversation_id`, `identity`, `sources`, `grounded`, `workspace`, `cancel`,
`cancel_reason`, `output_schema`). Meanwhile `answer_step` calls `agent.respond(...)`, and the
agent loads conversation history from its own store.

So the gate decides *route* -- including **refuse** -- with no prior turns, while the answer that
follows is produced with them. A follow-up whose meaning lives entirely in the conversation ("what
about the second one?", "and for a condo?") is classified as if it arrived cold, and the
predictable failure is a refusal on a question the conversation makes plainly in scope.

**They hit this exact class and wrote it down.** `engine.py`'s `answer` carries a marked comment:

> ⚠️ **The one place history is bounded.** ... Trimming per consumer is what this replaced, and it
> had already drifted -- the gate classified over *untrimmed* history while the orchestrator
> answered over a trimmed copy, so a long conversation could be gated on turns the answer never
> saw.

Their fix is the shape to copy: trim **once**, at the turn boundary, over `history + [question]`
together, and hand the same `messages` to gate and orchestrator. `chat.py` has the same disease in
a more advanced stage, because its gate sees no history rather than a differently-trimmed copy.

**Proposed:** `ChatTurn` gains `history: list[dict]`, the gate is built over `history + [message]`,
and the answer step is handed the same list rather than letting the agent load a second one. The
default stays today's behaviour for a turn that supplies no history, so no current caller changes.

## 3. Gap two: no byte-budget compaction

Their `trim_history` (39 lines) is a **UTF-8 byte** budget, applied oldest-first, always keeping the
last message even when it alone exceeds the budget.

The SDK's compaction strategies are `summarize`, `drop`, `segment_tail`, `reasoning_group_evict` --
turn-count-based or structural. None is a size budget, and the module's own `_char_count` counts
**characters, not bytes**. For a prompt budget that distinction is not cosmetic: a conversation in
a non-ASCII language is measured at up to a quarter of its real cost against the model's limit.

There is also a placement difference worth deciding deliberately rather than inheriting.
Compaction strategies compact the *store's working view*; their trim happens at the *turn
boundary*. Those are not the same thing, and §2 is the argument for the turn boundary: what the
gate and the answer must agree on is this turn's messages, not what the store happens to hold.

**Proposed:** a `byte_budget` compaction strategy in `memory.py` (registered alongside the other
four), plus the turn-boundary application in §2. The strategy is the reusable half; the turn
boundary is where it has to be applied for the two consumers of history to agree.

## 4. Gap three: the operator's detail travels in the user's response

Their `AnswerResult` splits the two deliberately:

> The **generic** wording for the user-facing stream. The split is deliberate and §15's: a user
> sees this, an operator sees `error_detail` (which can name a URL or a status).

`chat.py`'s `default_step_error` produces a generic `answer` and puts
`reason(exc, limit=SERVED_REASON_LIMIT)` into `incomplete_reason` -- the same split in spirit, but
both fields ride the same `InteractiveResponse` to the same caller. A consumer that renders
`incomplete_reason` (a reasonable thing to do with a field named that) shows the exception's text
to the end user. `reason()` is already length-limited and `redact_secrets` exists, so this is a
contract question rather than a live leak: nothing in japes says which of those two fields is safe
to display.

**Proposed:** say it in the field docs -- `incomplete_reason` is operator-facing and must not be
rendered to an end user -- rather than adding a field. A fourth error field on a response every
consumer already reads is a bigger change than the problem.

## 5. Checked, and deliberately not proposed

- **Citations.** Theirs are deterministic and rich (`build_citations`, `humanize_sources`,
  `serialize_citations`, a display-name swap). `InteractiveResponse.sources` carries the reference;
  the humanization is domain shaping and belongs pack-side.
- **Leak checks** (`identifier_leaks`, no grounding filename surviving into the answer). Their
  §13.1 is specific to grounding directories they own. The SDK's guardrail registry is the seam if
  this ever generalizes; nothing to move today.
- **Feedback injection** (`maybe_inject_feedback` off eval-service) and **cost**
  (`compute_cost_from_metrics`). Both already SDK-side; they are calling them, not reimplementing.
- **`AnswerResult`'s three outcomes vs `InteractiveResponse`'s flags.** Theirs is a tagged union,
  japes' is a flag set (`blocked`, `incomplete`, `cancelled`). Different taste, same information,
  and changing it would touch every consumer of the response. Not worth it.
- **The relay's flush-before-final ordering.** Real, and a streaming concern rather than a pipeline
  one -- `stream_chat_turn`'s own contract, if it turns out to need it.

## 6. Sequencing

1. **§2, the history asymmetry.** It is the only defect here, it is in shipped code, and it is the
   one that produces a wrong answer rather than a missing capability.
2. **§3, the byte-budget strategy.** Small, self-contained, and §2's turn-boundary trim wants it.
3. **§4, the field documentation.** A docstring change.

Each on its own review. §2 is the one to do before they read `chat.py`, because it is the first
thing a careful reader of that gate will ask about.

## 7. What would make this wrong

- **If their gate deliberately ignores history.** Worth confirming with them: a gate that reads
  only the current message is defensible as a *scope* check if scope cannot shift mid-conversation.
  Their own comment says otherwise for their case, but it is their design to state, not mine to
  infer.
- **If the agent's conversation store is meant to be the only history.** Then the fix is for the
  gate to read from the same store rather than for the turn to carry a list, and `ChatTurn` gains
  nothing. That is a smaller change and it is worth checking which one they would rather adopt
  before building either.
