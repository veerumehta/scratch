# Design note: tool-level zero data retention (ZDR)

Local design note (gitignored). Author: Virendra Mehta / assessed by Claude, 2026-08-01.
Prompted by kernel PR #726 (`app/zdr_redaction.py`) during a kernel-vs-japes sweep — kernel is
slated for deprecation in favor of japes, so a capability kernel has and japes doesn't gets a real
"how would this generalize" sketch, not just a dismissal. **Not a build plan — no japes consumer
has asked for this yet.** Sized so it's ready to build quickly once one does, per the same
"design when a need shows up once, build on the second instance" discipline as `plan_memory_
fabric.md`, except kernel's own shipped/proven need already counts as the first instance.

## What kernel built (#726, PAGI-1543)

A per-tool opt-in flag (`tool.zero_data_retention`). When set, `ToolPayloadRetentionPolicy`
blanket-replaces that tool's call args, response text, and error detail with fixed placeholders —
consistently across DB persistence, SSE streaming, span attributes, and logs. Not content-pattern
redaction (scan text, redact matches); a whole-payload suppression keyed on tool identity. Touches
9 files in kernel (`agentic_flow.py`, `api.py`, `context_loader.py`, `models.py`,
`tool_crud_service.py`, `unified_tool_execution.py`, `utils.py`, `llm_service.py`,
`kernel_handler.py`) because kernel has that many separate places tool payloads flow through.

## Why this is genuinely different from what japes has

`jazzx_sdk.failures.redact_secrets`/`redact_code_blocks`/`redact_fields` are content-pattern-based
— scan text, redact what matches a known-secret shape, regardless of which tool produced it. There
is no existing "this specific tool's payloads are never retained in any form, full stop" primitive
in japes. `agents.interactive.registry.redact_before` composes a redact function with a guardrail
*check* — a different use (deciding whether to flag content), not a persistence/streaming gate.

## Where it would plug into japes — checked against real code, not guessed

Two separate execution paths carry tool-call data in japes today, and they're at different
maturity levels for this specific concern:

### 1. The "generic tier" (`AgentExecutionService.run(tools=..., tool_executor=...)`)

`ToolCallRecord` (`jazzx_sdk/agents/base.py`) is constructed at exactly two sites —
`anthropic_provider.py:231,248` and `openai_provider.py:311` — each time a tool call completes or
errors, feeding `AgentExecutionTrace.tool_calls`. **Checked whether this list is auto-persisted or
streamed anywhere downstream: it is not.** `tool_calls` shows up elsewhere only as a bare count
(`tracing.py:923`, `evaluation/operational.py`) — the actual `ToolCallRecord` objects are returned
to the caller as part of `AgentResult.trace` and nothing in japes itself logs, persists, or streams
their content automatically. This means: (a) there's currently no automatic leak surface here
that isn't already the caller's own choice to build, but also (b) there's no existing "one choke
point" to redact at that would automatically protect every downstream consumer — a claim worth
stating precisely rather than assuming, since it initially looked like a clean win and turned out
not to be. A `redact_before_persistence`-style flag added at the two `ToolCallRecord` construction
sites would only protect callers that read `trace.tool_calls` for logging/display — real, but
narrower than kernel's blanket coverage.

### 2. The agentic/Skills path (`InteractiveAgent` + OpenAI Agents SDK `Runner`) — now fully traced

This path has *real* persistence and *real* streaming, confirmed precisely (not just plausible):

- **Persistence — one choke point.** The SDK's `Runner` drives persistence itself via the
  `Session` protocol, not via `agent.py`'s own `_persist_turn` (which only runs on the non-agentic
  path — `respond()` gates on `persisted_by_session`, and it's `True` here, so `_persist_turn`
  never fires). `binding.py`'s `ConversationStoreSession` implements that protocol:
  `add_items(items)` (line 94-95) calls `self._store.append(session_id, self._from(list(items)))`,
  where `_from` is `_from_responses_items` (line 59-63) — **currently a pure pass-through**
  (`return [dict(m) for m in items]`, no transform). The `items` the SDK hands to `add_items` are
  full Responses-API turn items, confirmed to include `function_call`/`function_call_output` types
  (`_to_responses_items`'s own docstring on the read side reasons about them explicitly for
  output-masking). So a skill's tool call args *and* result do land in persisted, `load()`-able
  history today, with **`_from_responses_items` as the single function** where a redaction step
  would sit — the same place `OutputMaskPolicy` masking already applies conceptually.
- **Streaming — a second, separate choke point, and already narrower than persistence.**
  `stream_hooks.py`'s `ToolStreamHooks` (an Agents-SDK `AgentHooks`, attached to every
  skill/parent agent): `on_tool_start` (line 86-92) builds a `ToolStartEvent` carrying raw
  `tool_args` — a real leak point. `on_tool_end` (line 94+) only carries `tool_name`/`success`, no
  result field at all — the tool *result* never reaches the stream today, only args do.

**So: 2 real choke points, not kernel's 9** (kernel has persistence/streaming/spans/logs as four
separate systems each touched per-call-site across multiple files; japes' two systems — the store
and the stream publisher — each already funnel through one function apiece). Neither location has
any redaction hook today.

**A real placement wrinkle, flagged not resolved**: `Skill.tools` (`spec.py`) is a list of name
strings; the actual tool objects are third-party `agents.FunctionTool` instances living in
`self._tools` (`agent.py:138`), not a japes-owned type — so `Skill.zero_data_retention` can't just
be "add a field and read it off the tool object" the way kernel's own DB-backed `Tool` row could.
It needs a side-map (tool name → retention flag) threaded alongside `self._tools`, or a wrapper
around the tool object. Whoever builds this should resolve that shape deliberately, not by
convention-guessing.

## Sketch, if/when this gets built

- **Declare the flag where tools are already declared as data**: `Skill.zero_data_retention: bool
  = False` (`agents/interactive/spec.py`) for the Skills path, with the name→flag side-map above
  resolving where the flag actually lives at call time; a parallel flag on whatever the generic
  tier's tool-definition dict/catalog entry shape is for path 1.
- **One small `jazzx_sdk.agents.retention` module** (mirroring kernel's `ToolPayloadRetentionPolicy`
  *shape*, not its code) — a policy object with `args_for_persistence`/`response_for_persistence`/
  `error_for_persistence`/`allows_stream` methods. Call it at: the two `ToolCallRecord` construction
  sites (path 1); `binding.py`'s `_from_responses_items` (path 2 persistence); `stream_hooks.py`'s
  `on_tool_start` (path 2 streaming, args only — `on_tool_end` needs no change, it carries no
  result today). Four call sites total, not nine.
- **Redaction placeholder text**: reuse the *pattern* kernel proved (fixed, category-labeled
  placeholders) rather than `redact_secrets` (wrong tool — that's content-pattern redaction of an
  otherwise-visible payload; ZDR suppresses the whole payload unconditionally, regardless of
  content).

## Not doing now — and the real open question, corrected

Not building this yet. The tracing above is complete and precise, but **the one thing that would
actually justify building it — confirmed real usage of `zero_data_retention=true` by a specific,
currently-deployed kernel tool that a migrating consumer depends on — is still unverified.** An
earlier pass in this same investigation over-inferred from a unit test's illustrative tool name
(`generate_random_password`) as if it were evidence of real production usage; it isn't — the flag
is a per-tool row on kernel's own `tool` DB table, invisible to a repo grep, and no seed/fixture
data or in-repo ticket text confirms which (if any) real tool has it set. The PR's title
("security bypass") is real signal that *something* needed fixing, but not proof of which consumer
or how many. Resolving that (via kernel's DB, Jira, or whoever owns the tool catalog) is the actual
gate before this gets built — not the tracing, which is now done and ready to build against
whenever that answer arrives.
