# Making the streaming chat turn a real pipeline

Status: plan, 2026-09-11. Nothing built. Target 2.5.2. Written against japes `a665d93` on `v2.5.2`.

Supersedes the sequencing in `plan_chat_turn_history_contract.md`. That plan's contract is still
right and is folded in here as the smaller piece; what changed is which problem comes first.

## 1. Why this is the priority, and not the history contract

`pipelines/chat.py` has two entry points and only one of them is a pipeline.

| | `run_chat_turn` | `stream_chat_turn` |
|---|---|---|
| Stages in the conductor | all seven | **validate, gate** |
| Step overrides | a `components` dict, any entry replaceable | **none** |
| Grounding | a step, traced, with progress | outside the pipeline |
| Post-answer work | `finalize`, overridable | nowhere |

`stream_chat_turn` runs `build_gate_pipeline()` -- validate and gate -- then branches by hand. Its
docstring is honest about the reason: the conductor's contract is one step, one emitted value, and
a token stream is not one value.

That is the whole gap, because of who the consumer is. The canonical assistant's queue ingress is
the path being replaced and its socket ingress is the one being built. Measured against
`jazzx-assistant/src/jazzx_assistant/engine.py` (905 lines):

- On the **blocking** path `chat.py` absorbs the 92-line `answer()` spine and lets `_run_gate` (85),
  `_compose` (128) and `_run_orchestrator` (85) bind as step components. Roughly 10 to 15 percent
  of the file disappears and another third is reframed rather than rewritten.
- On the **streaming** path it absorbs validate and gate. `_compose` has nowhere to go, and their
  §2.5 requires it to run *before* the terminal frame, so the hand-rolled engine stays.

Adopting as-is therefore gives them the pipeline on the ingress they are retiring and the old shape
on the one they are building: two turn shapes instead of one, which is worse than what they have.

## 2. The design

**A streaming step publishes its deltas to a sink and returns its final value.** The conductor's
contract is untouched -- one step, one emitted value -- and the deltas travel out of band:

```python
def answer_stream_step(agent, sink):
    async def _run(state):
        final = None
        async for ev in agent.respond_stream(...):
            if ev.done:
                final = ev.response
            else:
                await sink(ev)          # deltas leave here
        return final                    # the step still emits exactly once
    return _run
```

With that, the *whole* pipeline runs on the streaming path: validate, gate, ground, answer, and
finalize. `stream_chat_turn` becomes `run_chat_turn` with a sink attached, and keeps its public
generator shape by owning the queue the sink writes into.

What this buys, in the order it matters:

1. **`finalize` exists on the streaming path.** A consumer's compose step runs after the answer and
   before the caller sees the final event, which is exactly the persistence-before-terminal
   ordering the canonical assistant's socket path requires.
2. **One `components` dict for both paths.** Any step is overridable either way, so a pack writes
   its turn once instead of twice.
3. **Grounding is a stage when streaming**, so its progress and per-source degrading behave the
   same on both paths.

## 3. The parts that are actually hard

**Backpressure.** A sink writing into an unbounded queue lets the pipeline outrun a slow consumer,
and the failure is memory rather than an error. The queue is bounded and the sink awaits, so a
consumer that stops draining stops the turn -- which is the correct coupling, and the opposite of
what an unbounded buffer does.

**Abandonment.** A consumer that breaks out of the generator must cancel the run rather than leave
a pipeline writing into a queue nobody reads. `stream_chat_turn` already records this case as
`chat.abandoned`; the pipeline version has to actually cancel, and the existing `ChatTurn.cancel`
is the obvious signal to set.

**Escalation is still one value.** A pack wanting a genuinely streaming escalation path needs its
own step; this plan keeps today's contract, where escalate and refuse resolve to a single response
wrapped as one final event. Worth stating so the symmetry does not look accidental.

**The existing signature keeps working.** `stream_chat_turn(turn, agent=..., classify=...)` stays,
now building the components dict internally. A caller passing `components=` gets the override
surface; one that does not sees no change.

## 4. The history contract, folded in

`plan_chat_turn_history_contract.md` stands, and is smaller than it looked beside this. Its core is
that the gate classifies over `turn.message` alone while the answer runs against store-loaded
history, so two stages of one turn disagree about the conversation. `ChatTurn` gains `history`,
bounded once by a byte budget, with the resolution table that plan sets out.

It lands **after** §2: the gate is a step on both paths only once §2 is done, and fixing it in one
path first means fixing it twice.

## 5. Sequencing

1. **`answer_stream_step` plus the sink**, with `stream_chat_turn` rebuilt on the full pipeline.
   Bounded queue, cancellation on abandonment, existing signature preserved.
2. **`components=` on `stream_chat_turn`**, the override surface that makes a consumer's compose
   step possible.
3. **`ChatTurn.history`** and the gate window, per the other plan.

Each on its own review. (1) and (2) could be one commit; they are split because (1) is a behaviour
change to an existing function and (2) is purely additive, and a review round reads better when
those are not mixed.

## 6. What would make this wrong

- **If the canonical assistant's socket path does not want japes to own the turn.** Their engine is
  deliberately transport-neutral and returns an `AnswerResult` for an adapter to deliver; a
  pipeline that owns the sink is a different division of labour. Worth asking before building (2),
  because it is the item that assumes they want the override surface rather than the shape.
- **If token-level streaming stops being how answers arrive.** A tool-call-heavy agentic turn
  already emits mostly non-text events, and if the interesting stream becomes tool events rather
  than deltas, the sink carries those instead and the design is unchanged -- but the argument for
  urgency weakens.
- **If backpressure through the pipeline proves wrong for a real consumer.** Coupling turn progress
  to consumer drain rate is a deliberate choice here; a consumer that wants the turn to complete
  regardless needs an explicit buffer, not a silent one.
