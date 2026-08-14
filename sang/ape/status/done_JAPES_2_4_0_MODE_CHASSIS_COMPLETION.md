# plan_JAPES_2_4_0_MODE_CHASSIS_COMPLETION

**Status (2026-08-13): 7/7 phases shipped, in v2.4.0 (unpushed). Plan complete.** Phase 1 (replicas
default + `stochastic` wiring), Phase 2 (`EvaluatorMode` → `ReasoningAgent`), Phase 3
(`Curator.synthesize_bucket` → `ReasoningAgent`, `llm=` kept one release with a
`DeprecationWarning`), Phase 4 (`BaseMode.system_prompt` fails loud), Phase 5 (AML literals
nulled), Phase 6 (six `_reasoning` copies collapsed into `BaseMode`), and Phase 7
(`platform_catalog.MODES` derived from `MODE_REGISTRY` + `TraceStepMode` set-identity test) are
all done — full suite green (2841 passed, 3 skipped). Ready to move to `docs/status/`.

Repo: `japes`, branch `dev`. Target 2.4.0. **Revision 2** — reconciled against `ape/plans/`.
Written to be executed by Claude Code in the `japes` working tree.
Findings: `plans/design_note_mode_chassis_completeness.md` §1.

**Read first, in this order:** `plans/design_note_p1_p2_sizing.md` (Phase 1 below overturns a
shipped default on its authority — read the measurement before touching it),
`plans/domain-neutrality-and-config.md` §1 and §4, `plans/reasoner-chassis-analysis.md` §4b,
`jazzx_sdk/modes/base.py`, `jazzx_sdk/modes/operational/verifier.py` (smallest migrated mode — the
reference shape), `jazzx_sdk/modes/evolve/evaluator.py`.

**Standing constraints.** `ape/CLAUDE.md` governs: never `git push` without explicit approval;
surgical changes only ("every changed line should trace directly to the user's request"; "if you
notice unrelated dead code, mention it — don't delete it"); no abstractions for single-use code;
full-suite pass count recorded before and after every phase (2513 passed / 3 skipped is the current
baseline, with the Phase 4/6 chassis work uncommitted on top of 2.3.4); `_version.py` and
`pyproject.toml` move together (`tests/test_version_sync.py`); commit outcomes, not planning.
No `Literal["mortgage"|"aml"|...]` in `jazzx_sdk/` — the pattern `AdjudicationAgentSpec` follows.

**Note on the uncommitted tree.** `jazzx_sdk/agents/adjudication/` (Phase 4 + Phase 6) is built and
uncommitted as of 2026-08-07, and Phase 1 below modifies `spec.py` and `pipeline.py` inside it. Land
or stash-and-rebase deliberately; do not interleave.

---

## Phase 1 — P0: `replicas` default contradicts the measurement

**Files:** `jazzx_sdk/agents/adjudication/spec.py:46,59`, `jazzx_sdk/agents/adjudication/pipeline.py:132`,
`jazzx_sdk/conductor/replication.py:84`, `jazzx_sdk/agents/adjudication/partition.py`.

**Why first.** This is the only phase where the shipped code overrides a conclusion you measured and
wrote down. `design_note_p1_p2_sizing.md` measured 3 independent batched replicas agreeing on every
JTBD — 9/9, *"zero measured variance reduction, at the full 3.1x cost multiplier"* — and concluded:
*"**Default `replicas=1`, not 3.** MACER's k=3 was inherited, not measured… A chassis primitive
shouldn't bake in an unmeasured assumption."* The chassis ships `replicas: int = 3` in three places,
and `spec.py:46`'s docstring cites *"MACER's default is 3"* as the justification — the inherited
assumption, restated as rationale. Every pack that takes the defaults pays 3× for a benefit measured
at zero.

**Do:**

1. Change the default to `1` in all three locations. Rewrite `spec.py:46`'s docstring to state the
   measurement and the gate, not MACER's number: *"Ensemble size k for the LIVE partition. Default 1
   — k=3 showed zero variance reduction at 3.1× cost on the one fixture measured (see
   design_note_p1_p2_sizing.md); raise it per-pack only with a measurement behind it."*
2. **Wire `stochastic`.** `ConditionEvaluator.stochastic` exists — declared at
   `fabric/canonical/condition_evaluator.py:44`, `False` at `:82`/`:119`/`:177`, `True` at `:262`
   (`NaturalLanguageConditionEvaluator`) — and `partition_rules` reads only `.execution`, never
   `.stochastic`. Per the sizing note, a `stochastic=False` rule must force `k=1` unconditionally,
   regardless of the spec's `replicas`. Implement in `run_segment`: after partitioning, compute the
   effective k per rule and skip replication entirely for the non-stochastic set.
   This is the *third* instance of the SDK's "add the metadata slot and defer wiring it" pattern that
   `domain-neutrality-and-config.md` §2 names — worth stating in the commit message.
3. Update `examples/adjudication_demo/adjudication.yaml` to `replicas: 1` with a comment pointing at
   the sizing note, so the reference wiring teaches the right default.

**Deliberately NOT in this phase:** escalate-on-disagreement (the sizing note's fourth conclusion —
*"start at a low k (1 or 2), and only spend more replicas … when a cheap secondary signal suggests
real uncertainty"*). `AnyEscalate` collapses votes already paid for; it does not decide to buy more.
That is a genuinely new primitive and it needs its own sizing pass. Note it; don't build it here.

**Tests:** `tests/test_adjudication_pipeline.py` — a segment of `Expression`-condition rules makes
exactly one model call regardless of `spec.replicas`; a `NaturalLanguageCondition` rule with
`replicas=3` makes three; the default spec makes one. `tests/test_adjudication_spec.py` — default is 1.

---

## Phase 2 — P0: migrate `EvaluatorMode` onto `ReasoningAgent`

**File:** `jazzx_sdk/modes/evolve/evaluator.py`

**Problem.** `class EvaluatorMode(Generic[...])` (`:32`) does not inherit `BaseMode`. `__init__`
builds `AsyncOpenAI(api_key=...)` (`:94`), bypassing `AgentExecutionService` / `resolve_model` /
`RetryingModel` / the gateway — an Anthropic-only deployment cannot run it, which is the exact
portability win `aci/CLAUDE.md:181-200` records jaci getting from `ReasoningAgent` when
`AnthropicConductor` was deleted. `run()` does `response_format={"type": "json_object"}` →
`json.loads` → `.get()` per field (`:126-156`): a truncated response silently yields
`improvement_signals=[]`, stopping the compounding loop with no error. It returns `EvaluationReport`,
not `ModeResult`, so it contributes no `token_usage`.

**Scoping note for the commit message.** This is not a deferred item being picked up — `EvaluatorMode`,
`Curator`, and `modes.evolve` appear zero times across `design_note_reasoning_substrate.md`,
`design_note_p1_p2_sizing.md`, `CLAUDE.md`, and both REFACTOR plans. Every scoping sentence in the
migration says "the five." This is `CLAUDE.md` §7 (*"check the full family, not just the nearest
sibling… if three modules share a pattern and only one got the fix, the other two are latent bugs"*)
applied to the family that was never enumerated.

**Do:**

1. Add a local output model — do not reuse `EvaluationReport`, which carries Python-computed fields
   the model must not author:
   ```python
   class _QualitativeAssessment(BaseModel):
       qualitative_score: float | None = None
       qualitative_assessment: str = ""
       improvement_signals: list[ImprovementSignal] = Field(default_factory=list)
       metadata: dict[str, Any] = Field(default_factory=dict)
   ```
2. `class EvaluatorMode(BaseMode, Generic[...])`; implement `mode_name` → `"evaluator"`; drop the
   local `self.system_prompt` assignment in favour of `BaseMode.system_prompt` (which Phase 4 makes
   loud). Keep the existing `ValueError` on a missing `prompt_resolver`/`model_tier_parser` — that
   fail-loud discipline is already better than `BaseMode`'s and should not be lost.
3. Replace the `client` parameter with `agents: "AgentExecutionService"`. Accept `client=` for one
   release with a `DeprecationWarning`, since jaci subclasses this in three scenarios
   (`aml`, `ci_spread`, `cre_underwriting`) and is editable-installed against this checkout — a hard
   break lands in their tree immediately. Remove in 2.5.0.
4. Add the lazy `_reasoning` property, shape copied from `verifier.py:78-91`.
5. Replace the completions call with `self._reasoning.run(name=f"evaluator:{self.pack_id or 'default'}",
   instructions=self.system_prompt, query=user_message, output_type=_QualitativeAssessment,
   model_settings=build_model_settings(temperature=self.temperature))`. Leave every deterministic
   part untouched: threshold findings, `EvaluationReport` construction, the `pack_id` fallback chain.
6. Return `ModeResult(success=True, output=report, token_usage=usage, tokens_used=...)`, and keep a
   transitional `async def run_report(...) -> EvaluationReport` that unwraps, so jaci's
   `tests/eval/*` and `ui/pages/evaluation_runner.py` migrate in one line. `aci/CLAUDE.md:152`
   confirms the Evaluator is never called by the Conductor — it runs post-case in the harness — so
   the blast radius is the harness and the three subclasses, nothing on the hot path.

**Tests:** `tests/test_evaluator_mode.py` (new) with `ScriptedLLM` — populated report plus non-`None`
`token_usage`; schema-failure-then-success retries (assert two calls); `client=` warns; constructs
with no OpenAI key when the model is an Anthropic name.

**Done when:** `grep -rn "AsyncOpenAI" jazzx_sdk/modes/` is empty.

---

## Phase 3 — `Curator.synthesize_bucket`

**File:** `jazzx_sdk/modes/evolve/curator.py:240-276`

Layer 1 routing is pure Python and stays that way — `platform_catalog.MODE_KINDS` classifies
`curator` as `python`, deliberately. Layer 2 goes through `jazzx_sdk/llm/structured_call.py`, a
**third** execution path (`LLMManager`-shaped `llm=`) that the reasoning-substrate note's gap
analysis never surveyed, since it only audited callers of `ctx.runtime.agents.run(...)`. It validates
a schema but has no retry, no truncation handling, no token accounting.

**Do:** accept `agents: "AgentExecutionService"` and route through
`ReasoningAgent.run(name=f"curator:synthesize:{tag}", output_type=_SynthesizedGuidance)`; return
`(guidance, usage)`. Keep `llm=` for one release with a `DeprecationWarning` — jaci calls this at
`scenarios/ci_spread/demo_correction_to_guidance.py:23`.

**Tests:** extend `tests/test_curator_synthesis.py` with the retry case and a usage assertion.

---

## Phase 4 — P0: make prompt resolution fail loud

**File:** `jazzx_sdk/modes/base.py:132-152`

`BaseMode.system_prompt` catches `FileNotFoundError` and substitutes
`f"You are the {self.mode_name} mode."`. This contradicts the layer below it:
`plan_JAPES_2_2_2_DOMAIN_PACK_QUICKSTART_REFRESH.md:24` documents that `resolve_mode_prompt`
*"raises `FileNotFoundError` if none"* — designed to fail loud, and `BaseMode` discards the signal.
Governing conventions: `REFACTOR-2.4:491` (*"failing with a typed error rather than silently"*) and
*"capability fails loud, knowledge fails silently"* (`plan_assistant_sourav.md:40`, the principle
that justified the `resolve_knowledge` P0). A mode prompt is knowledge.

**Do:**

1. `strict_prompts: bool = True` on `BaseMode.__init__`. When `True`, let the resolver's
   `FileNotFoundError` propagate as `ModePromptNotFound(FileNotFoundError)` carrying `mode_name`,
   `pack_id`, and the attempted path.
2. When `False`, keep the fallback but log at ERROR and prefix the prompt with
   `"[UNGROUNDED FALLBACK PROMPT — no pack asset resolved for mode '<name>']"`, so the degradation is
   visible in any captured prompt or trace instead of invisible.
3. Default `True`. Breaking for a pack with a missing asset — which is the point. CHANGELOG under a
   **Breaking** heading, and check jaci's packs before landing (it is editable-installed against this
   tree; `aml_investigation_core.yaml` and `earnings_review.yaml` are already recorded as not loading
   at all in `aci/status/status_JACI_CONCEPTS_TAB_PARITY.md`, so expect at least those two to surface).

**Tests:** `tests/test_mode_prompt_resolution.py` — default raises and names the mode and pack;
`strict_prompts=False` returns the marked fallback and logs at ERROR.

---

## Phase 5 — the domain-neutrality fix that was reported as done

**Files:** `jazzx_sdk/modes/catalog.py`, plus a new `tests/test_domain_neutrality.py`.

`reasoner-chassis-analysis.md`'s header states a violation in `modes/catalog.py` *"is fixed there."*
Verified against the current tree — all five are still present: `:78` `canonical_consumes=["Alert"]`,
`:79` / `:141` `derived_object="case_file"`, `:160` `canonical_produces=["SARDraft"]`, `:162`
`derived_object="sar_draft"`.

`domain-neutrality-and-config.md` §4 already prescribes the fix and sizes it at *"a few hours for #1
and #3."* Do exactly what it says, no more:

1. Set those five fields to `None`, following the pattern the four unimplemented modes already got
   right (`None` = "not yet mapped"; a pack supplies the concrete type).
2. Add the AST-based lint (§4 fix #3). **AST, not grep** — the doc is explicit that a string-grep
   test false-positives on `modes/schemas.py` and `skills/*/base.py` docstrings, which intentionally
   show AML/Mortgage/Healthcare side by side as a *positive* pattern. Flag domain tokens only inside
   enum member assignments, dict-literal values, and `Field(default=...)`. Model it on
   `tests/test_version_sync.py` / `tests/test_import_boundary.py`. First assertion: every
   `canonical_produces` / `canonical_consumes` / `derived_object` across `MODE_REGISTRY` is `None` or
   in the allow-list (`Evidence`, `Decision`, `Policy`, `Trace`, `Outcome`, `Attestation`,
   `GovernorDecision`, `LoopStatus`, `EvaluationReport`, `SignalRoute`).
3. Add a `> **Status (2026-08-08):** …` blockquote to `domain-neutrality-and-config.md` recording
   what landed, and **correct the chassis doc's header claim** — a doc asserting a fix that didn't
   land is worse than one with an open TODO, because the next reader stops checking.

**Explicitly out of scope:** §4 fix #2 (wiring `Pack.domain`/`.segment`/`.regulatory_context`). The
doc itself calls it *"a design decision plus a half-day of wiring"* and offers a legitimate
alternative — declare it descriptive-only in the docstring. That decision is the user's, not this
plan's.

---

## Phase 6 — collapse the six copies of the lazy-`_reasoning` idiom

The identical property plus its identical six-line justification comment appears in
`investigator.py:111-123`, `verifier.py:78-90`, `reasoner.py:88-100`, `governor.py:93-105`,
`narrator.py:82-94`, and (after Phase 2) `evaluator.py`.

Move it to `BaseMode`, reading `self.ctx.runtime.agents` and `self.api_model_name`, with the
justification stated once and a clear error if `ctx` is unbound. Delete the six copies. Pure
deduplication — existing mode tests should pass untouched. Land after Phase 2 so it covers six, not
five.

---

## Phase 7 — one home for the 13-mode list

Three unlinked copies: `modes/catalog.py` `MODE_REGISTRY`, `fabric/canonical/trace.py`'s
`CognitiveMode` enum, and `platform_catalog.py:20` `MODES`. `reasoner-chassis-analysis.md` §4b flags
the first two (*"duplicated verbatim… with no import linking them — they can drift silently"*);
`REFACTOR-2.3` §4.4 flags the third and proposes deriving `MODES` from `MODE_REGISTRY`, keeping only
the presentation layer — deferred to 2.4 and then not scheduled in any 2.4 phase, so it is currently
orphaned between two plans. This phase adopts it.

**Do:** derive `platform_catalog.MODES` from `MODE_REGISTRY`; add a test asserting the
`CognitiveMode` enum's members and `MODE_REGISTRY`'s keys are set-identical (a test rather than a
derivation, because `trace.py` is a canonical-object module and importing `modes` from it would add
an edge into the `fabric.canonical` import cycle that `REFACTOR-2.4` §4.3 warns is undocumented and
untested).

**Handle with care:** `jaci/ui/platform_view.py:71-81` imports seven symbols from `platform_catalog`
inside `try/except ImportError` with a hardcoded fallback — a lost symbol makes jaci *"degrade
silently to stale data rather than failing."* Keep every currently-exported name.

---

## Deliberately not in this plan

**Mode-implementation resolution / mode-composition validation.** Revision 1 proposed a
`ModeImplRegistry` and a mode axis on `ProfileRegistry.validate()`. Dropped: `reasoner-chassis-analysis.md`
§4b already establishes that mode is not load-bearing at runtime and that this is a known state, and
`plan_assistant_sourav.md` records the house preference for *"the concrete, currently-enabled
reading… not speculative"* — it deliberately narrowed "contracts coherent" to a DAG check for the
same reason. A registry with no runtime consumer would be the fourth copy of the mode list, not a
fix. **Revisit when there is a caller.**

**The autonomy bridge.** §4b's genuinely good idea — the P8 DETERMINISTIC/LIVE partition is
simultaneously a cost boundary and a governance boundary, so a reproducible deterministic check can
launch at a higher rung while a LIVE judgment caps lower and routes to review, bounded by the
existing `CellKind.FINAL` guardrail. This would make the chassis the first runtime consumer of mode
and is the right way to connect `ModeContract.autonomy_default` (dead) to `AuthorityCell.autonomy_launch`
(live). It needs its own plan and a decision from you; it is not a side effect of this one.

**`ReasoningAgent` docstring wording.** The ceiling is composed above the agent by `run_segment`,
not layered inside it. One-paragraph amendment, fold into any phase touching that file.

---

## Order and gates

| Phase | Blocking | Gate |
|---|---|---|
| 1 replicas + `stochastic` | P0 | deterministic-only segment makes 1 call at any `spec.replicas`; defaults are 1 |
| 2 EvaluatorMode | P0 | `grep -rn "AsyncOpenAI" jazzx_sdk/modes/` empty; usage populated |
| 3 Curator | no | retry test green; usage returned |
| 4 strict prompts | P0 | missing asset raises; jaci packs checked; CHANGELOG breaking note |
| 5 domain neutrality | no | AST lint green; chassis-doc header corrected |
| 6 dedup `_reasoning` | no | existing mode tests pass untouched |
| 7 one mode list | no | set-identity test; every `platform_catalog` name still exported |

1, 2, and 4 are independent P0s. 6 lands after 2. Full suite between phases, pass count recorded.
