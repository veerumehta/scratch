# What an assistant turn needs from `pipelines.chat`, and which of it we should own

Status: assessment, 2026-09-11. Decides nothing; sets the requirement list the chat plans build
against. Derived from the canonical assistant's use case rather than its code.

## The frame

A production assistant turn is the work `pipelines.chat` should enable out of the box. A consumer
is still free to write its own pipeline with specializations, but each thing it has to write
itself is either a requirement we missed or a decision we made that its use case disagrees with.

Below, each requirement is stated as a use case, then judged: **own it**, **seam** (we provide the
hook, the consumer provides the content), or **theirs** (a specialization we should not absorb).
Two are marked **disagree**, where I think the shape they arrived at is not the one to copy.

## The requirements

### R1. A turn ends in one of four outcomes, and an adapter switches on it

*Answered, refused, failed, interrupted.* The distinction is not cosmetic: a refusal is a
successful turn with no grounding and no citations, an interruption must be recorded as
interrupted rather than failed, and a failure carries operator detail a user must not see.

`InteractiveResponse` carries `blocked`, `incomplete`, `cancelled` as independent flags, so an
adapter asks three questions and has to know their precedence. Nothing prevents a response that is
both `blocked` and `cancelled`.

**Own it**, but as a derived `outcome` property over the existing flags rather than a restructure.
The information is already there; what is missing is one place that resolves precedence, so every
adapter resolves it the same way.

### R2. Work after the answer, before the caller sees it

Citations, humanisation, a display-name swap, an output leak check. All of it happens after the
model replies and before anything reaches the user.

`run_chat_turn` has `finalize` for this. `stream_chat_turn` has nowhere: it runs validate and gate
through the conductor and then branches by hand.

**Own it.** This is the single largest gap, and it is what
`plan_streaming_chat_pipeline.md` exists to close.

### R3. The turn is recorded before it is delivered

A durable conversation must contain the turn before the user is told it is finished, or a
reconnecting client reads a history missing the answer it just saw.

`chat.py` persists in `finalize` through `agent.persist_turn`, but only for the refuse and escalate
branches, and the ordering relative to delivery is incidental rather than guaranteed.

**Own it**, as an explicit ordering guarantee: the terminal event is emitted after the persist step
returns. Stating it is most of the work, since the pipeline already sequences stages.

### R4. Delivery is bounded

After the terminal frames are published, the turn waits for them to reach the wire, but a dead
connection must not hold the turn open.

`chat.py` has no concept of delivery at all.

**Seam.** japes should not own a transport, but the pipeline should expose the point where a
consumer can wait, with a timeout it sets. Owning the wait would mean owning the socket.

### R5. Interruption is an outcome, not an error

A user interrupting mid-turn is a normal event. It must not surface as a failure, and the partial
work must be recorded as interrupted.

`ChatTurn.cancel` and `InteractiveResponse.cancelled` cover this on the blocking path. The
streaming path has the harder version: a consumer abandoning the generator must cancel the run
rather than leave it writing into a queue nobody reads.

**Own it.** Half exists; the streaming half comes with R2.

### R6. Progress is per-source, not per-stage

Grounding fans out to several independent systems. A user watching a checklist wants to see each
one settle, and a source that fails must degrade rather than sink the turn.

`ground_step` plus `gather_degrading` already does this, including `required=` for the sources
whose absence must stop the turn.

**Already ours.** The only gap is that grounding is not a stage at all when streaming (R2).

### R7. The turn produces a result; the adapter delivers it

Their reasoning core publishes nothing terminal, because two ingresses answer *what is a turn
recorded as* differently, and a core that delivered could not satisfy both.

This is the requirement most in tension with our design instinct, and I think **they are right**.
It also means the sink design in `plan_streaming_chat_pipeline.md` §2 needs care: a pipeline that
owns delivery takes back exactly the separation this requirement protects. The resolution is that
the sink is *supplied* by the adapter and the pipeline only decides *when* to call it, which keeps
"when" with the turn and "how" with the transport.

**Own the ordering, seam the delivery.**

### R8. History is an input

Covered in `plan_chat_turn_history_contract.md`: the gate and the answer must read the same
conversation, bounded once. **Own it.**

### R9. A turn-scoped side task that cannot affect the outcome

Generating a conversation title, warming a cache, emitting an analytic. It runs alongside the turn
and its failure is not the turn's failure.

`chat.py` has `on_complete`, which fires after the turn with the final response, best-effort. That
covers the after case but not the alongside case.

**Seam**, and low priority until a second consumer wants it. One pack starting a background task is
not yet a pattern.

### R10. Prompt enrichment before the answer

Injecting retrieved feedback or examples into the prompt, from a source the SDK already speaks to.

**Seam, not a stage.** The content is domain-specific and the injection point is the agent's own
instructions. A pipeline stage here would be a hook with one caller and a name that suggests
generality it does not have.

### R11. Output must be checked before it leaves

No grounding filename, no internal identifier, no raw variable name in what a user reads.

japes has the guardrail registry and `InteractiveAgent` runs output guardrails already.

**Already ours.** Their specific checks are domain content for that seam.

## Where I would not follow them

**The error triple.** `AnswerResult` carries `error_code`, `user_message` and `error_detail` as
optional fields populated only on one of its outcomes. That is a tagged union expressed as a flat
record, and it has the same defect as `InteractiveResponse`'s flags in the other direction: the
type permits states the domain does not have. If we adopt R1 we should resolve it properly rather
than copy this shape.

**A 752-line coordinator.** The split between reasoning and transport is right and worth copying.
The transport half having accreted persistence, delivery, outcome resolution, interruption
handling and a background title task into one class is not, and a pipeline that made that the
natural shape would be reproducing the problem.

## What this changes about the existing plans

- `plan_streaming_chat_pipeline.md` stays the first piece, and R7 sharpens its §2: the sink is the
  adapter's, the pipeline decides only when to call it.
- `plan_chat_turn_history_contract.md` stays the second.
- R1 (a derived `outcome`) and R3 (persist-before-deliver as a stated guarantee) are new, small,
  and worth doing with R2 since they are the same reader's questions.
- R4 and R9 are seams to leave open, not features to build now.
