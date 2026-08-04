# Design note: a Reasoning substrate — floor (a) + ceiling (b), one primitive

> **Shipped as v2.3.0 (2026-08-02, commit `7f270b5`, pushed after v2.2.4 shipped separately as
> `3b72431`).** This whole arc — run-kit modernization through the `ReasoningAgent` chassis, the
> five mode migrations, and the `AgentExecutionService.run()` fix — was originally accumulating
> inside a single growing "v2.2.4" commit. Split out once it clearly outgrew that scope: v2.2.4
> shipped first with just the original policy/manifest/hooks/SSRF/agent-definition-store bundle,
> then this arc landed as v2.3.0 on top. See `docs/status/CHANGELOG.md`'s `[2.3.0]` section for
> the itemized detail.

> **Status (2026-08-02): Floor implemented.** `jazzx_sdk/agents/reasoning/agent.py` —
> `ReasoningAgent(agents: AgentExecutionService, ...)`. `run(tools=None/[])` is the floor;
> `run(tools=[...])` is the ceiling, same method. Resolves models via the shared `resolve_model`
> (guarded so a non-OpenAI model never touches `agents.openai`, which raises with no OpenAI key
> configured); drives execution via `run_kit.run_agent()` unmodified. 6 new tests
> (`tests/test_reasoning_agent.py`), full suite green (2168 passed). Naming (`ReasoningAgent`)
> accepted by proceeding, not a separate explicit sign-off — revisit if it stops fitting.
> Not yet done: migrating the five existing modes onto it, and P1/P2/P6/P8 ceiling extensions.

> **Status (2026-08-02): ReasonerMode migrated.** `jazzx_sdk/modes/operational/reasoner.py`'s
> `run()` now calls `self._reasoning.run(...)` (a `ReasoningAgent` constructed in `__init__`,
> lazily imported so `jazzx_sdk.modes` callers who never instantiate a Reasoner don't pull in the
> OpenAI Agents SDK) instead of `self.ctx.runtime.agents.run(...)`. No public constructor/`.run()`
> signature change — `output_schema`/`temperature`/`system_prompt`/prompt construction all
> unchanged; `model_settings` now built via `build_model_settings(max_tokens=4096)` +
> `.temperature =` (unchanged effective values, just built the SDK-blessed way). 4 new behavioral
> tests (`tests/test_reasoner_mode_reasoning_agent.py`) — existing tests only covered
> importability/instantiation, not `.run()` behavior, so this is genuinely new coverage, not a
> port of old assertions. The one that matters: a `ModelBehaviorError` now gets retried with
> schema feedback and can still succeed, where before it failed the mode outright on the first
> occurrence — confirmed end-to-end through the real chain, not mocked at the boundary. Full
> suite green (2172 passed, was 2168).
>
> **Found, not fixed (pre-existing, unrelated, dead code)**: `experts/policy/default.py` and
> `experts/playbook/default.py`'s `reasoner_mode` lazy-load property calls `ReasonerMode(pack_id=
> ..., prompt_resolver=...)` — missing the required `ctx`/`output_schema` args, would raise
> `TypeError` if ever invoked. Confirmed via grep that this property is never actually called
> anywhere (no other reference, no test) — dead code, not something this migration touches or
> should fix unprompted.
>
> **Status (2026-08-02): InvestigatorMode migrated too.** Same pattern exactly —
> `jazzx_sdk/modes/operational/investigator.py`'s `run()` now calls `self._reasoning.run(...)`
> instead of `self.ctx.runtime.agents.run(...)`; `output_type=HypothesisUpdate[THypothesisContent]`
> preserved verbatim (including whatever an unbound-TypeVar-subscripted generic actually resolves
> to at runtime — pre-existing, not this migration's concern to fix). Same pre-existing dead-code
> pattern found again: `experts/playbook/default.py`'s `investigator_mode` property also
> constructs `InvestigatorMode(pack_id=..., prompt_resolver=...)` missing the required `ctx` arg
> — never called anywhere, left alone. 4 new behavioral tests
> (`tests/test_investigator_mode_reasoning_agent.py`), same shape as the Reasoner ones. Full suite
> green (2176 passed, was 2172).
>
> **Status (2026-08-02): GovernorMode migrated too.** Same pattern — `run()` now calls
> `self._reasoning.run(...)` for the LLM-reached path; the authority-gate short-circuit
> (`_authority_gate`, unchanged) still bypasses `ReasoningAgent` entirely when a matrix is
> supplied and the cell is inadmissible — confirmed with a new test, not just relying on the
> existing `tests/test_authority.py` coverage (which only checked the old `agents.run` attribute
> was untouched; that assertion happens to still pass post-migration since the normal path no
> longer calls it either, but it wasn't checking the right thing anymore, so this migration adds
> a check against `ReasoningAgent` directly). Same pre-existing dead-code pattern found a third
> time: `experts/policy/default.py`'s `governor_mode` property, never called, left alone. Two
> pre-existing, unrelated `test_authority.py` failures found during this step
> (`test_policy_profile_get_and_fail_closed`/`test_profiles_from_yaml`, a `PolicyProfile`/
> `SourcePrecedencePolicy` pydantic model-rebuild ordering issue) — confirmed via `git stash`
> against the clean committed state (fails identically, isolation-only — doesn't surface in the
> full-suite run). 4 new behavioral tests (`tests/test_governor_mode_reasoning_agent.py`). Full
> suite green (2180 passed, was 2176).
>
> **Status (2026-08-02): VerifierMode migrated too.** Same pattern — `run()` now calls
> `self._reasoning.run(...)` for the LLM-reached path; the empty-batch early return (no evidence
> to verify) is untouched and still bypasses `ReasoningAgent` entirely — confirmed with a new
> test. **Found, not fixed (pre-existing, unrelated)**: that early-return branch constructs
> `VerifierReport(evidence_id="batch", status="no_evidence", quality_score=1.0, findings=...,
> flags=[], attestation=None)` — none of those are real fields on the actual `VerifierReport`
> schema (`evidence_results`/`notes`/`attestations`/`flagged_count`/...). Doesn't crash (pydantic
> silently drops the unrecognized kwargs and fills declared fields with their defaults), so it's
> a silent-empty-report bug, not a broken one — confirmed via direct construction, not assumed.
> Out of scope for this migration (a different branch entirely), left alone. 4 new behavioral
> tests (`tests/test_verifier_mode_reasoning_agent.py`). Full suite green (2184 passed, was 2180).
>
> **Status (2026-08-02): NarratorMode migrated — all five operational modes now on
> `ReasoningAgent`.** Same pattern, `max_tokens=8192` (Narrator's own larger budget, narratives
> can be long) preserved via `build_model_settings(max_tokens=8192)`. Added a test specifically
> for `IncompleteOutputError` (truncated output) getting retried-with-feedback rather than
> surfacing as an opaque parse failure — the mode most exposed to that failure mode given its
> token budget is the largest of the five. 4 new behavioral tests
> (`tests/test_narrator_mode_reasoning_agent.py`). Full suite green (2188 passed, was 2184).
>
> **Floor migration complete.** `ReasonerMode`, `InvestigatorMode`, `GovernorMode`,
> `VerifierMode`, `NarratorMode` all now get real retry/schema-feedback/truncated-output handling
> via `run_kit.run_agent()` instead of the generic tier's bare, string-matched retry loop — the
> gap this whole design note opened with. No public constructor/`.run()` signature changed on any
> of them. Each migration's own short-circuit path (Governor's authority gate, Verifier's
> empty-batch return) is untouched and confirmed still bypasses the LLM. Three instances of the
> same pre-existing dead-code pattern found along the way (`reasoner_mode`/`investigator_mode`/
> `governor_mode` lazy-load properties in `experts/policy/default.py`/`experts/playbook/
> default.py`, all missing required constructor args, none ever called) — left alone, out of
> scope. One pre-existing schema-mismatch bug found in `VerifierMode`'s empty-batch branch — also
> left alone.
>
> Remaining: the ceiling extensions (P1/P2/P6/P8) — nothing yet uses `ReasoningAgent`'s
> `tools=[...]` path.

> **Status (2026-08-02): `AgentExecutionService.run()`'s generic tier fixed too — item 2 from
> above.** Scoped narrowly on purpose, after finding the real shape of the gap:
>
> - `OpenAIProvider.run()` (`jazzx_sdk/agents/openai_provider.py`) now has a fast path — no
>   `tools`, exactly one single user-role message (the *only* shape any real caller in japes has
>   ever used, confirmed via grep) — that routes through `run_kit.run_agent()` exactly like
>   `ReasoningAgent`/the five modes, with `output_type=output_schema` passed straight to the real
>   `Agent` so a schema mismatch is a real `ModelBehaviorError` `run_agent` retries with feedback,
>   instead of the old raw `response_format` dict + a hand-rolled `validate()` call afterward with
>   no way to correct a bad response.
> - The tool-calling branch (tools present, or multi-turn `messages`) is **left untouched on
>   purpose**: `tool_executor` is accepted as a parameter but never referenced anywhere in the
>   method body, and `format_tools()`'s dict-shaped output was never wired to real
>   `agents.FunctionTool` execution — confirmed via grep, no real caller anywhere (inside japes)
>   exercises this path with actual tools. Bridging that to `run_kit.run_agent` (which needs real
>   `FunctionTool` objects, not generic dicts + a callback) is a separate, larger design task, not
>   a retry-loop fix — noted, not attempted here.
> - **`AnthropicProvider.run()` is out of scope, and stays that way for a real reason, not an
>   oversight**: it doesn't use the OpenAI Agents SDK at all — it drives the raw Anthropic API
>   with its own hand-rolled tool-use loop. `run_kit.run_agent()` can't be reused there directly;
>   improving its retry robustness is a parallel, architecturally distinct task.
> - **Two more confirmed-dead branches found and removed as a natural byproduct, not a separate
>   cleanup pass**: `agent.temperature = temperature` / `agent.max_tokens = max_tokens` (old
>   code) set attributes `Agent` — a real dataclass with a fixed field list — doesn't have; they
>   were silently inert. The new fast path sets these correctly via `ModelSettings`, which is
>   what `Agent.model_settings` actually reads. Also: `result.messages`/`result.tool_calls` in the
>   old trace-building code were always empty (`RunResult` has neither field) — confirmed via
>   `dataclasses.fields()`, not assumed; dropped from the new path's trace construction since they
>   never carried real data.
> - Found substantial existing test coverage (`tests/agents/test_openai_provider.py`,
>   `tests/agents/test_service.py`) that I almost missed on a narrower directory glob — re-ran
>   before and after. One test needed updating (`test_structured_output_success`: its mock
>   returned a raw JSON string, matching the old manual-parse behavior; the new path needs an
>   already-parsed instance, matching what the real SDK actually returns when `output_type` is
>   set correctly) — a correction to match improved behavior, not a regression patch. Added 7 new
>   tests covering fast-path routing (tools/multi-turn correctly fall back) and the retry/schema-
>   feedback fix itself. Full suite green (2195 passed, was 2188).
>
> Remaining: the ceiling extensions (P1/P2/P6/P8); `AnthropicProvider.run()`'s comparable (but
> architecturally distinct) retry robustness, as a separate future item.

Local design note (gitignored). Author: Virendra Mehta / drafted by Claude, 2026-08-02.
Companion to `reasoner-chassis-analysis.md`, `policy-ir-abstraction.md`,
`design_note_p1_p2_sizing.md`. Answers the question those docs left open: not a chassis named
after adjudication or after one mode, but a substrate any mode can sit on — floor is a robust
single-shot structured call (fixing a real, confirmed gap shared by all five existing modes),
ceiling is MACER's proven agentic/batched/grounded/ensembled pattern, same primitive underneath.

## Why one substrate, not two things

`run_kit.run_agent()` already collapses cleanly between floor and ceiling depending on `tools`:

- `tools=[]` → the model can't loop (nothing to call), so it resolves in one turn. What's left is
  exactly the floor: retry-with-backoff on transient errors, feedback-and-retry on schema
  validation failure, feedback-and-retry on truncated output — all through
  `jazzx_sdk.failures.classify_failure`, one taxonomy.
- `tools=[...]` → the same function is the ceiling: MaxTurns continuation, batched multi-item
  prompts, and (once P6/P8 land, per the companion docs) precomputed grounding and
  applicability short-circuits sit on top of the same loop without changing its shape.

So the substrate isn't "build two things and pick one per mode" — it's one execution primitive
where `tools=[]` *is* the floor, not a special case of it.

## The gap this closes — confirmed, not assumed

Read directly, not inferred:

- `AgentExecutionService.run()` (`jazzx_sdk/agents/openai_provider.py:184-346`) builds a plain
  `OpenAIResponsesModel` with no `RetryingModel`, then retries the whole `Runner.run()` call via
  its own `_run_with_retry` (`:348-405`) — retryability decided by lowercasing the exception and
  string-matching `"429"`/`"500"`/`"rate limit"` in the text. No handling at all for
  `ModelBehaviorError`, `MaxTurnsExceeded`, or truncated output.
- Every existing mode implementation calls this same generic tier:
  `jazzx_sdk/modes/operational/{reasoner,investigator,governor,verifier,narrator}.py` all call
  `self.ctx.runtime.agents.run(...)`. A `ModelBehaviorError` today just fails the mode outright
  (`ModeResult(success=False)`) — no feedback loop, no retry. This isn't hypothetical: this
  session's own Phase 0 measurement against MACER hit a real `ModelBehaviorError` and watched
  `run_kit.run_agent()` catch and self-correct it. `ReasonerMode` today has no equivalent.
- `InteractiveAgent`'s agentic path (`interactive/agent.py:761`) drives `Runner.run()` almost
  directly too — only a narrow context-overflow-specific retry, no MaxTurns/schema handling
  either. So **no existing japes execution path has this mechanism** — it exists only in
  `run_kit.py`, currently reached only via MACER.
- `AgentExecutionService.openai.build_agent()` (the provider-specific tier `InteractiveAgent`/
  `DocumentAgent` actually use) is *not* part of this gap — it already calls `resolve_model()`
  correctly. The gap is specifically the generic tier's `run()` + the two chassis' own
  Runner-driving code, not model resolution.
- Today's `ReasonerMode`/`InvestigatorMode` are also, separately, tool-free by design —
  `has_tools=False`, with `InvestigatorMode`'s own comment: *"Tools are fulfilled externally by
  Conductor, not by the agent."* Evidence assembly happens across separate mode invocations at
  the Conductor level, not via an in-session tool loop. That's a genuinely different shape from
  MACER's proven pattern (one call, in-session tools, batched across items) — which is exactly
  why this is a ceiling *extension*, not just a robustness patch on the existing shape.

## Shape

A new class — working name `ReasoningAgent` (open; picked for the same "name the shape of work"
convention as `InteractiveAgent`/`DocumentAgent`, not a mode name or "Adjudication," per
`reasoner-chassis-analysis.md` §4b's own argument against over-claiming one mode) —
constructor-injected with `agents: AgentExecutionService`, matching the existing chassis pattern
exactly (`InteractiveAgent(spec, agents=ctx.runtime.agents)`, `DocumentAgent(spec, agents=
agent_service)`), not a new method bolted onto `AgentExecutionService` itself.

Internally:

- Resolves the model via the *same* `resolve_model()` `openai_provider.build_agent()` already
  calls — no third implementation, no duplicating `RetryingModel`. For OpenAI, needs the
  underlying `AsyncOpenAI` client, already held by `agents.openai.client`.
- Drives execution via `run_kit.run_agent()`'s loop directly (already provider-agnostic — takes
  a resolved `model: Any`, not an OpenAI-specific type). Not reimplemented, not wrapped in a new
  retry mechanism — called as-is.
- Floor call: `await reasoning.run(instructions=..., query=..., output_type=..., session=None)`
  — `tools` omitted/empty, single robust structured call. This is the direct replacement for
  `ctx.runtime.agents.run(...)` inside the mode implementations, once they migrate (separate
  step, below).
- Ceiling call: same method, `tools=[...]` (+ `continuation_tools`, `max_retries`,
  `max_session_size_kb` already on `run_agent`'s signature) — the agentic, MaxTurns-continuing,
  batched-multi-item shape MACER proved out. `precompute`/grounding (P6) and ensemble replication
  (P1/P2, gated on `stochastic` per P8) are additions *on top of* this call, not a different
  execution path — a pack that never needs them just doesn't pass them.

## What this does NOT do yet (deliberately out of this note's scope)

1. **Migrate the five existing modes onto the new substrate.** That's a real, separate change —
   touches `ReasonerMode`/`InvestigatorMode`/`GovernorMode`/`VerifierMode`/`NarratorMode` and
   whatever calls them; needs its own blast-radius check before touching, the same way the MACER
   migration checked call sites before each step. Worth doing (it's the direct payoff of the
   floor), but as its own plan, not bundled into building the substrate itself.
2. **Fix `AgentExecutionService.run()`'s generic tier in place.** An alternative (or
   complementary) path to the same floor benefit: make `openai_provider.run()` itself delegate to
   `run_kit.run_agent()` instead of `_run_with_retry`/`_MetricsHooks`. Would fix the gap for
   *any* caller of `ctx.runtime.agents.run()`, not just modes that migrate to the new substrate
   class — but changes a more widely-depended-on method, so wants its own caller audit first.
3. **P1 (`run_replicated_segments`)/P2 (`EnsembleCollapse`)/P6 (`PrecomputedGrounding`)/P8
   (`ConditionEvaluator` registry) themselves** — `design_note_p1_p2_sizing.md` already sizes
   P1/P2's defaults from real measurement; this note just fixes where they land (on top of
   `ReasoningAgent`'s ceiling call, not a parallel Agent/Runner-driving implementation).

## Open items

- Confirm naming (`ReasoningAgent` is a placeholder, not a decision).
- Decide whether item 2 above (fixing `AgentExecutionService.run()` directly) should happen
  *before* or *instead of* building the new class — it's the smaller, more surgical fix and
  benefits existing callers immediately; the new class is still needed for the ceiling regardless.
- The existing modes' "Conductor supplies evidence, agent has no tools" shape vs. MACER's
  "agent has tools, gathers its own evidence in-session" shape are both real, valid patterns for
  different needs — this substrate should support both, not force a migration off one shape.
