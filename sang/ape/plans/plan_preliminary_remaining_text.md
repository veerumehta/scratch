# Preliminary answer: return only the part not already sent (sonnet-runtime, 2026-10-17)

State today (`pipelines/chat/preliminary.py`, `compose.py`): the preliminary lane publishes one skill's early reply
(`preliminary` event, recorded as `turn.preliminary_answer`). The final compose joins it as `prefix + answer` before
the compose steps run, so the final answer repeats whatever the full reply says again; only a separator is added.

## Design
- `InteractiveResponse.remaining_text: str | None`: set when the lane showed something; the final answer text minus the
  part already sent. `answer` keeps the joined text (what the record, the citations and a non-stream reader use);
  `remaining_text` is what a streaming consumer appends after the `preliminary` event.
- How the remainder is found (no model call): the compose join takes the early text as the prefix; when the
  full reply begins with that text (normalised for whitespace and case) the remainder is the reply after it; otherwise
  the early text and the full reply differ, the remainder is the whole reply, and the join stays as today. A lane
  can declare `dedupe: prefix | none` (default `prefix`).
- Stream delivery: the final event carries `remaining_text` in place of repeating the answer; a non-stream
  response returns `answer` (joined) and `remaining_text`. Both record the joined text in the turn store.
- Citations: built over the joined text (early text plus remainder), with the early text's sources already published;
  the remainder's cite markers are numbered after them so a reader of the stream never sees a marker twice.
- A blocked or leak-failed final answer: `remaining_text` is None and the early text stays withdrawn as it is.
## Tests
Reply that repeats the early text: remainder is the tail only, `answer` the joined text; unrelated reply: remainder is
the whole reply; stream and non-stream record the same joined text; citation numbering continues; no lane: unchanged;
`dedupe: none` keeps today's output.
## Open
Whether a lane may declare a marker line to cut at instead of matching the prefix (more robust to paraphrase, needs a
prompt change in the pack).
