# One history per turn: the contract `pipelines.chat` should have

Status: design, 2026-09-11. Target 2.5.2. Written against japes `138cc90` on `v2.5.2`.

Follows `note_chat_pipeline_vs_assistant_turn.md`, which found the defect. That note ended by
asking the consumer which of two fixes they would rather adopt. This supersedes that question: the
design is ours, so the job is to pick the contract that serves the assistants we know about and the
ones we do not, rather than to match one consumer's current call site.

## 1. The invariant

**A turn has exactly one history, resolved once, and every stage reads it.**

Everything below follows from that one line. The defect in §2 of the note is the invariant absent:
the gate classifies over the current message alone while the answer runs against store-loaded
history, so two stages of the same turn disagree about what the conversation is.

The canonical assistant states the same invariant in a marked comment, having already paid for it:

> **The one place history is bounded.** ... Trimming per consumer is what this replaced, and it had
> already drifted -- the gate classified over *untrimmed* history while the orchestrator answered
> over a trimmed copy, so a long conversation could be gated on turns the answer never saw.

## 2. What the code allows, which decides the shape

Three facts, checked rather than assumed:

- `InteractiveAgent.respond` takes `messages: list[dict]`, and on the **single-shot** path computes
  `convo = await self._load_history(session_id) + list(messages)`.
- `_load_history(None)` returns `[]` (`agent.py:477`). So a caller with **no session** that passes
  `history + [question]` gets exactly its own list, with nothing prepended.
- On the **agentic** path (a spec with skills), the substrate session supplies history and persists
  itself, so only the new turn is passed.

So history is injectable *today*, with no API change, provided the turn is stateless. And it is not
safely injectable alongside an active session, because the store would prepend its own copy.

That is not a limitation to work around. It is the contract, and it should be stated rather than
discovered: **whoever owns the history owns the whole of it.**

## 3. The contract

```python
@dataclass
class ChatTurn:
    message: str
    history: list[dict] = field(default_factory=list)   # prior messages, oldest first, no question
    ...
```

| The turn has | History comes from | The answer step passes |
|---|---|---|
| `history`, no active session | the caller | `history + [message]` |
| no `history`, an active session | the agent's store | `[message]` (today's behaviour) |
| neither | there is none | `[message]` |
| **both** | ambiguous | **refused, loudly** |

The last row is the only new failure. It is worth failing on: a caller that supplies history *and*
a session-backed store has two histories that will diverge, and silently prepending one to the
other is how a conversation acquires duplicated turns nobody can attribute.

**Bounded once.** A single UTF-8 byte budget over `history + [message]` together, oldest-first,
always keeping the last message even when it alone exceeds the budget. The question's own bytes
come out of the same budget -- trimming it separately lets a turn exceed the budget by exactly the
size of what the user just typed.

## 4. The scenarios this is for

Ordered by how confident I am each is real. The first four are observed; the rest are designed for
and should be read as predictions.

### S1: the follow-up (observed, and the defect)

> "What is the DSCR minimum?" → "And for a condo?"

The second message is meaningless alone. A gate that sees it alone refuses it as out of scope or
routes it to the wrong branch. **Needs:** the gate sees recent turns.

### S2: the drift, which pulls the other way (observed in shape, not in the wild)

> ten turns about a loan → "write me a poem"

A gate handed the *whole* conversation sees an overwhelmingly in-scope context and can route the
outlier as direct. More history helps S1 and hurts S2, so "give the gate history" is not the
answer by itself.

**The resolution is two-part**, and both halves matter:

1. The gate sees a **small recent window** (`gate_history_turns`, default 2 exchanges) -- enough to
   resolve a reference, not enough to drown the message being judged.
2. The classifier prompt **names what it is scoring**. Today's default says *"Classify the user's
   message"* in the singular, which is correct when one message is all it gets and actively
   misleading once prior turns are in the list. It becomes: prior turns are context, the last
   message is the subject.

`gate_history_turns=0` restores today's behaviour exactly, for a gate that is a pure content policy
and wants no context.

### S3: history that does not live in japes (observed)

The canonical assistant's queue ingress fetches the conversation from the Assistant API; its socket
ingress reads a KH `CanonicalConversation`. Neither is japes' conversation store, and the agent is
run with no session at all. **Needs:** injectable history. This is the scenario that decides the
contract -- a design where history can only be store-resolved cannot serve the assistant we already
have.

### S4: history that does live in japes (observed)

A simpler assistant uses `InteractiveAgent`'s own store and supplies nothing. **Needs:** unchanged
behaviour, which the empty default gives.

### S5: the prompt budget (observed)

Long conversations must be bounded, and every consumer must agree on the bound. **Needs:** the byte
budget of §3. Today japes has no size-based compaction at all: its four strategies (`summarize`,
`drop`, `segment_tail`, `reasoning_group_evict`) are turn-count-based or structural, and
`memory._char_count` counts **characters, not bytes** -- which understates a non-ASCII
conversation's real cost against a model limit by up to four times.

### S6: the escalation gets what the gate saw (predicted)

`escalate_step` hands the turn to a heavier engine. Today that turn carries no history, so the
escalation path re-derives it or does without. With history on the turn, the reasoner sees exactly
what the gate judged. **Needs:** nothing new; it falls out.

### S7: grounding that depends on the conversation (predicted)

> "show me the other one"

The retrieval query needs the resolved reference. `turn.sources` are caller-supplied thunks, so a
caller can already close over whatever it likes -- but it cannot close over history the pipeline
resolved, because today there is none. **Needs:** history resolved before `ground` runs, which the
stage order already gives.

### S8: replay and evaluation (predicted, and the most valuable of the predictions)

A golden case is a fixed conversation plus a question, and its whole point is determinism. Injected
history is exactly that: the case supplies the list, no store is touched, and the same case
produces the same gate decision every run. Today a chat golden case either has no history or needs
a pre-seeded store, which is state a case should not carry.

### S9: two ingresses, one conversation (predicted)

A turn arrives over the queue, the next over a socket. Each ingress supplies history from its own
system; the pipeline holds no opinion. Works by construction rather than by design, which is the
point of making history an input.

## 5. What this does not change

- **`InteractiveAgent`'s API.** No new parameter. The stateless path already accepts a full
  messages list; this design uses it rather than adding a way to suppress the store load.
- **The agentic path.** A spec with skills lets its substrate session own history, and that stays
  true. Such an agent is the "active session" row of the table.
- **Persistence.** `finalize_step` already persists the refuse and escalate branches through
  `agent.persist_turn`. A stateless turn persists nothing, which is correct -- the caller owning
  history owns writing to it too.
- **`InteractiveResponse`.** No new fields.

## 6. Sequencing

1. **`byte_budget` compaction strategy** in `memory.py`, registered beside the other four. Smallest,
   independent, and useful on its own to any consumer bounding a working view.
2. **`ChatTurn.history` + the resolution table of §3**, applied once in `run_chat_turn` /
   `stream_chat_turn`, including the loud refusal for the ambiguous row.
3. **The gate window**: `gate_history_turns`, the tail slice, and the classifier prompt that names
   its subject.

Each on its own review. (2) is the defect fix and the one to land before the canonical assistant
reads `chat.py`; (3) is what makes the fix correct rather than merely present, since (2) alone
hands the gate history without telling it what to do with it.

## 7. What would make this wrong

- **If `gate_history_turns=2` is the wrong default.** It is a guess. Two exchanges resolves the
  pronoun cases I can name and keeps the current message dominant, but nobody has measured a gate's
  accuracy against window size, and this design makes that measurable rather than answering it.
- **If a real consumer wants both injected history and a session store.** §3 refuses that
  combination. If it turns out to be a legitimate shape -- a cache in front of a durable store, say
  -- the refusal becomes a precedence rule instead, and the table grows a row.
- **If scope can never shift mid-conversation for a given pack.** Then S2 is not real for it,
  `gate_history_turns` can be large, and the tension the design resolves was not worth resolving.
  That is a per-pack fact, which is why it is a parameter and not a constant.
