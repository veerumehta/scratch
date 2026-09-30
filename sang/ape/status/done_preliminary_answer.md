# Plan: the preliminary answer (a fast lane published before the full answer)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: done. P1-P4 built on `v2.5.7` 2026-09-30 (`4a465ff9` P1+P4, `7cc4ad2a` P2+P3, review fixes
to `406c182d`), review (`e037e55c..406c182d`) clean after 3 rounds;
Q1-Q4 decided as recommended (P4 works: the Agents SDK tool's `timeout_behavior="error_as_result"`
returns a result and the batch goes on). Plan dated 2026-09-30. The last open item of `plan_chat_runtime_coordinator.md` C7
("the preliminary fast answer: a two-agent answer kind"). Prior art read first:
`status/done_chat_lifecycle.md` ("their newest branch fits it: a pre-answer publish plus a compose
that joins the two halves"), `status/done_declarative_compose.md`, jazzx-assistant
`origin/feat/preliminary-answer` (`hooks/fast_answer.py`, design section 23).

## What jazzx-assistant built

- A fourth specialist, `fast_agent`: no tools, one model call, low reasoning effort, the loan's
  whole prior review injected as references. The orchestrator calls it on every turn, in the same
  tool batch as the specialists that read documents.
- An `AgentHooks.on_tool_end` on the orchestrator publishes its reply the moment it returns, while
  the others still work. Before publishing it runs the same delivery chain as the final answer
  (citations, then file names to display names, then leak checks); a leak drops it, since it is
  optional.
- The skill signs off with `COVERAGE: full | partial | none`; the hook strips it. `none` is not
  published; `full` and `partial` each open with their own label. The orchestrator always answers
  too (coverage decides wording, never delivery; its persona says not to repeat what is on screen).
- The turn delivers two chunks and one final result carrying both joined, citations rebuilt over
  the pair (not merged from two lists), and that joined text is what is recorded.
- Best-effort throughout: a failure in the lane never costs the turn. Only the first reply per
  turn is published.
- Open on their side: no wall-clock bound on the lane (`Skill` has no timeout), and the lane sits in
  the orchestrator's tool batch, so a slow one delays the full answer.

## What japes has

- Skills as sub-agents (`as_tool`), per-skill `model` / `reasoning_effort` / `max_turns`,
  references injected as prompt text.
- `ToolStreamHooks` publish tool start/end to the context-bound invocation publisher, without the
  result text, and not to the lifecycle's `turn.publish`. So nothing today can see a skill's reply
  before the parent's run ends.
- Declared compose (`ComposePlan`): exactly the chain the lane needs, as data.

## The design

### P1. Hearing a skill's reply as it returns (agents layer)

`InteractiveAgent.respond` / `respond_stream(on_skill_result=)`: an async callback
`(skill_name, text) -> None` called from the parent's `on_tool_end` for a skill tool, once per
call, best-effort (an exception is logged, never raised into the run). Built per turn into the
agentic run's hooks, composed with the agent's own (`CompositeAgentHooks`), so concurrent turns
on one agent do not share it. Generic: a UI that wants any specialist's result early uses the same
seam.

### P2. The preliminary lane, declared (pipelines layer)

```yaml
lifecycle:
  preliminary:
    skill: fast_agent
    marker: "COVERAGE:"          # optional: the sign-off line's prefix, read and stripped
    labels:                      # by marker value; a value with no label is not published
      full: "Found the following on a quick check of the loan's findings; looking deeper."
      partial: "So far, from the loan's findings; looking deeper to answer your query."
    label: ""                    # with no marker: the one label (may be empty)
    separator: "\n\n---\n\n"     # between it and the full answer
```

- `ChatLifecycleSpec.preliminary` (strict), compiled by `declared_lifecycle` into a
  `PreliminaryPlan`; the skill must be one of the agent's skills (lint).
- The answer stage passes `on_skill_result` when a lane is declared. For the lane's skill, the
  first reply per turn: parse the marker, withhold when its value has no label, run the declared
  compose steps over it (so its citations, display names and leak checks are the final answer's),
  drop it when a `leak_check` fails whatever its action, else publish
  `{"preliminary": {"text", "coverage", "sources", "checks"}}` through `turn.publish` (a required
  event) and keep the raw text on the turn.
- Compose joins: when the turn kept a preliminary, the compose stage makes the answer
  `label + text + separator + full answer` before its steps run, so `cite` and `humanize` run over
  both halves together (citations rebuilt, not merged) and the reply, the record under
  `application_hook` / `external`, and `ChatRun.value` all hold what the reader saw.
- The published event and the joined reply come from one compose chain, so what the reader sees
  first and what the final result says agree.

### P3. Plato

The stream carries the event; the blocking `/chat` publishes nothing early but returns the joined
answer. Pack check reports a lane naming no skill of the agent as `invalid_lifecycle`.

## What jazzx-assistant changes

`FastAnswerHook` becomes `lifecycle.preliminary` (their labels and suffix as data, `COVERAGE:` as
the marker); its citation, humanize and leak chain is their declared compose; `FAST_ANSWER_SKILL`,
`published` / `text` / `raw_answer` bookkeeping and the handler's join go away. Their stream
adapter maps the `preliminary` event to their `llm_chunk`. The persona rules (always call it in
the same step; do not repeat) stay theirs: they are prompt, not runtime.

## Open questions

- Q1 The event: a typed `preliminary` event (text, coverage, sources, checks), not a text delta,
  so a client can render it apart from the full answer and a replay can tell them apart.
  Recommend: typed.
- Q2 Declared on the lifecycle (`lifecycle.preliminary.skill`), not as a flag on the skill: which
  skill is the lane is a turn policy, and one skill can serve both. Recommend: lifecycle.
- Q3 The blocking route returns the joined answer (the preliminary included) even though nothing
  was shown early, so both routes deliver the same reply. Recommend: yes.
- Q4 A wall-clock bound per skill (`Skill.timeout_seconds`, a timed-out skill returns a declared
  fallback text to the parent), which is what their lane lacks and any slow specialist could use.
  Recommend: yes, as P4, if the Agents SDK tool wrapper lets a timeout return a result rather than
  fail the parent's batch; otherwise a TODO with that reason.
