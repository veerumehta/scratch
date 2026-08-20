# Claude Session Status

**Last Updated**: 2026-08-17

## Working Principles

**Critical: Use Professional Judgment**
- Do NOT blindly accept every user suggestion
- Push back when you see better alternatives or tradeoffs
- Explain architectural concerns, performance implications, security issues
- Present alternatives: "Your proposal has X benefit, but Y tradeoff. Consider Z instead?"
- The user WANTS critical thinking, not agreement
- If uncertain, present options with pros/cons and let user decide

## Sibling Repos (local checkouts)

All JazzX repos are checked out as siblings of this one, at `/Users/sangit/src/<name>` (i.e.
`../<name>` from here) — check there before assuming a repo needs GitHub API access or isn't
available locally. Branch shown is what's currently checked out (drifts over time; re-check with
`git -C /Users/sangit/src/<name> branch --show-current` rather than trusting this list blindly).

| Repo | Branch (as of 2026-08-20) | What it is |
|---|---|---|
| `jaci` | dev | Primary real-usage consumer of japes; PoC-stage, only-we-use-it repo (per user, 2026-08-20) |
| `jazzx-assistant` | dev | JazzX Assistant for chatting with a loan — **the most real usage of japes today** (per user, 2026-08-20), distinct from `assistant` below |
| `assistant` | main | Separate "Assistant Repo" — confirm scope/relationship to `jazzx-assistant` before assuming which is meant |
| `juno` | main | Builder Studio copilot on OpenAI Agents SDK; jazzx_sdk footprint historically minimal |
| `kernel` | main | The GenAI kernel powering JazzX; deprecating in favor of japes patterns (absorb, don't dismiss) |
| `kernel-lab` | dev | — |
| `knowledge_hub` | main | Knowledge Hub service (KH) |
| `eval-service` | main | Eval service; contract convergence work with japes' own `jazzx_eval_contracts` |
| `common` | main | Shared submodule (also vendored into japes as a git submodule — see the common-submodule note below) |
| `client-api` | main | — |
| `macer` | main | MACER — deprioritized, don't resume unasked (see memory) |
| `macer-japes` | japes | — |
| `k9` / `k9-ui` | dev | — |
| `policy-workbench` | main | Live example for the InteractiveAgent openai-agents-SDK vs claude-agent-SDK generalization question |
| `commercial-lending-demo` | lovable-demo | — |
| `flowable-core` | fix/macer-response-nested-tracking | — |
| `jazzx-cli`, `jstack`, `ontofun`, `mortgage-*`, `anthropic-fs-ref` | various | Lower-priority/reference repos |

Don't assume a repo's role from its name alone (`assistant` vs `jazzx-assistant` is a real trap) —
skim its own README/CLAUDE.md when working in it for the first time in a session.

## Current Session Context

### Version Status: 2.4.1 (per `_version.py`, committed through `0476e81`); InteractiveAgent
### reasoning-streaming work uncommitted on top (see the 2026-08-17 entry below). The Adjudication
### chassis/eval-service-convergence/condition-evaluator bullets right below this line all landed
### and are committed (squashed into `74cb161` v2.4.1 and `0476e81`) — left as history, not stale.
- **jazzx_sdk/_version.py**: single source of truth (`__version__`); `pyproject.toml`'s
  `version` must match — enforced by `tests/test_version_sync.py`. Currently `2.4.1`.
- **AdjudicationAgent chassis (Phase 4 of `docs/plans/reasoner-chassis-analysis.md`) — built,
  uncommitted.** New package `jazzx_sdk/agents/adjudication/` (`workspace.py` P4
  `EvidenceWorkspace`/`Mount`; `partition.py` P8 DETERMINISTIC/LIVE `Rule` split;
  `spec.py` `AdjudicationAgentSpec`; `pipeline.py` `run_segment` — P1 replication + P2 collapse
  over batched LIVE obligations; `agent.py` `AdjudicationAgent` facade). Closed one real P8 gap
  along the way: added `NaturalLanguageCondition`/`NaturalLanguageEvaluator` to
  `fabric.canonical.policy`/`condition_evaluator` (the `Condition` union had no LLM-backed kind).
  Added `name_patterns` to `observability.mlflow_bridge.span_to_trace_step`/
  `spans_to_canonical_trace` — its existing `mode_map` is keyed on span_type (`LLM`/`TOOL`/...),
  too coarse to tell an adjudicate call from an emit call apart (both are plain `LLM` spans);
  `agents/adjudication/tracing.py` supplies the chassis's own name-pattern list.
  `examples/adjudication_demo/` ships as the toy pack.
- **Phase 6 (P3/P7) also built, same session, uncommitted.** Reordering decision: benchmarking
  (Phase 0) and MACER-parity shadow-running (Phase 5) deferred to the end — MACER may never adopt
  this chassis, but the primitives are worth building for japes's other consumers regardless.
  `run_segment` now honors `Rule.applicability` (a real gap found this session — it didn't before);
  new `agents/adjudication/planner.py` (`SegmentPlanner`/`plan_or_fallback`, P7's fail-closed
  dynamic-segmentation seam) and `impact.py` (`impacted_rules`/`merge_with_carry_forward`/
  `RunMode`/`resolve_run_mode`, P3 keyed off `evidence_contract()` rather than MACER's document-
  triple join). Both wired into `AdjudicationAgent.adjudicate` as optional params
  (`planner`/`changed_fields`/`prior_outcomes`) — omitting all three is unchanged from Phase 4.
  Full suite green (2513 passed, 3 skipped). Phase 0/5 (benchmarking + MACER-parity validation)
  still not started — everything above is verified against toy/mocked evidence only. See
  `docs/plans/reasoner-chassis-analysis.md`'s 2026-08-07 "Phase 4 shipped"/"Reordering decision"/
  "Phase 6 shipped" notes for the full breakdown.
- **Three corrections landed 2026-08-08, from an independent completeness audit**
  (`design_note_mode_chassis_completeness.md`, `plan_JACI_CL_SPREAD_ADJUDICATION.md` in jaci —
  both verified against code before acting). (1) `replicas` default fixed `3` → `1` in
  `spec.py`/`pipeline.py`/`conductor/replication.py` — the shipped default contradicted
  `design_note_p1_p2_sizing.md`'s own measurement (zero variance reduction at 3.1x cost). (2)
  `ConditionEvaluator.stochastic` documented as currently redundant with `execution == LIVE`
  (verified true across all four registered evaluators) rather than wired into
  `partition_rules` — no evaluator yet needs the distinction, wiring it now would be an untested
  seam. (3) `modes/catalog.py`'s five AML literals (`canonical_produces`/`canonical_consumes`/
  `derived_object` on investigator/conductor/narrator) nulled per
  `domain-neutrality-and-config.md`'s fix #1 — verified nothing in `jazzx_sdk/` reads them first;
  `test_operational_modes.py` updated. Full suite still green (2513 passed, 3 skipped).
- **`EvaluatorMode` migrated onto `ReasoningAgent`, same audit, 2026-08-08.** The one EVOLVE-layer
  mode left out of the v2.3.0 five-mode migration: previously held its own `AsyncOpenAI` client
  (an Anthropic-only deployment couldn't run it at all) and parsed a bare `json.loads` with no
  retry — a truncated/malformed response either raised or silently yielded an empty
  `improvement_signals` list, stopping the compounding loop with no error anywhere. Now inherits
  `BaseMode`, constructor takes `ctx: HandlerContext` (matching the other five), `run()` returns
  `ModeResult` (was bare `EvaluationReport`) — verified zero real callers depended on the old
  shape (only docstring mentions + re-exports anywhere in japes). Caught a real, previously-latent
  bug along the way: a dict-typed field on any `output_type` pydantic model (typed or bare) breaks
  OpenAI's strict-schema mode outright (`additionalProperties should not be set`) — confirmed this
  would *also* break `NarratorMode`'s `NarrativeOutput.sections: dict[str, str]` in a real call;
  fixed only for the new `_EvaluatorLlmOutput` model via `AgentOutputSchema(...,
  strict_json_schema=False)`, scoped to this one call site. 8 new tests
  (`tests/test_evaluator_mode.py`), including a boundary contract test for the strict-schema bug
  (mocked-`ReasoningAgent` tests alone would never have caught it — none of them construct the
  real `AgentOutputSchema`).
- **`NarratorMode` got the same strict-schema fix, 2026-08-08.** `NarrativeOutput`'s
  `sections`/`citations`/`metadata` are all dict-typed — same `output_type=` fix
  (`AgentOutputSchema(NarrativeOutput, strict_json_schema=False)`), same blind spot in its
  existing test file (`test_narrator_mode_reasoning_agent.py` mocks at the `Runner.run()` level
  via the `runner=` test seam, so none of its tests ever reached the real
  `get_output_schema()`/`AgentOutputSchema` construction either) — added the same boundary
  contract test there.
- **`VerifierMode` got the same fix, 2026-08-08** — `VerifierReport`'s `evidence_results`/`notes`/
  `attestations` are all dict-typed, identical `AgentOutputSchema(..., strict_json_schema=False)`
  treatment, same test blind spot, same added contract test. Also cleaned up (while in the same
  method): the empty-evidence early return built `VerifierReport(evidence_id=..., status=...,
  quality_score=..., findings=..., flags=..., attestation=...)` — none of those are real
  `VerifierReport` fields; pydantic v2 silently ignores unknown kwargs by default (verified
  empirically — no crash), so this was always producing the same bare-defaults object a plain
  `VerifierReport()` would, just via misleading dead code. Not a behavior change, a clarity one.
  `GovernorMode`/`GovernorDecision` and `InvestigatorMode`/`HypothesisUpdate` remain clean
  (list/bool/str only, confirmed); `ReasonerMode`'s `output_schema` is pack-supplied, not an SDK
  schema, so not japes's to fix. Full suite green (2523 passed, 3 skipped).
- **`BaseMode.system_prompt` no longer swallows a missing pack asset, 2026-08-08.** Was: catch
  `FileNotFoundError`, log a warning, substitute `f"You are the {mode_name} mode."` — a mode
  running on a fabricated nine-word prompt with no visible error. `resolve_mode_prompt` (the
  default resolver) documents its own contract as raising `FileNotFoundError` on a genuine miss;
  `BaseMode` was silently defeating that. Now lets it propagate — every mode's `run()` already
  wraps `self.system_prompt` access in a broad `except Exception` returning
  `ModeResult(success=False, error=...)`, so this surfaces as a real, checkable failure instead of
  a crash or a silent bad prompt. 2 new tests in `tests/test_modes_framework.py` (a minimal
  concrete `BaseMode` subclass didn't exist there before). Full suite green (2525 passed, 3
  skipped).
- **v2.3.5, 2026-08-10**: agent identity for eval/feedback attribution (`agent_id` on
  spec/response/feedback/manifest-binding/inventory) + per-skill/parent `tool_use_behavior`
  overrides. Unrelated to the eval-service convergence work below beyond both touching
  `evaluation/feedback.py` (additive `agent_id` field, no conflict).
- **Japes/eval-service contract convergence, Phases 0-5 built same day, uncommitted.** Reviewed
  an external proposal PDF (`docs/plans/046e37e4-..._Proposal.pdf`, gitignored) for merging
  Japes' and eval-service's feedback/attribution/learning contracts; found it reinvented pieces
  of Japes' own IIF-Charter canonical spine (`fabric.canonical.{decision,evidence}`) and the
  existing `GuidanceAsset`/`GuidanceProvenance` guidance layer — dropped the proposal's
  `ApprovedLearningAssetV1` entirely (redundant with `GuidanceAsset`), kept evidence/attribution
  as lean runtime forms with new required promotion adapters into canonical
  (`evidence_bundle_to_canonical`, `attribution_to_canonical_decision`, new
  `DecisionType.ATTRIBUTION`). Full build: new standalone package `jazzx_eval_contracts/` (own
  `pyproject.toml`, `pydantic`-only — verified zero fastapi/sqlalchemy/asyncpg/azure-storage-
  queue/mlflow load via a throwaway venv), all contracts through Phase 5 (identity/feedback/
  evidence/attribution/learning/scoring/execution), `jazzx_sdk/evaluation/
  eval_service_adapters.py` (7 adapters), `feedback_sink.py` (`EvalServiceFeedbackSink`),
  `attribution_protocols.py` (`EvidenceProvider`/`AttributionAnalyzer` Protocols), plus additive
  provenance fields on `ImprovementSignal`/`GuidanceProvenance` and `synthesize_bucket`
  propagation. Full suite green (2576 passed, 3 skipped). **Phase 6 not started** — hard-blocked
  on eval-service publishing an approved-learning endpoint that doesn't exist yet; eval-service's
  own Phases A-F (different repo) untouched. See `docs/plans/
  plan_eval_service_contract_convergence.md` (gitignored) for the full phase breakdown and the
  canonical-spine reconciliation decisions.

- **Two hardening passes landed 2026-08-12, generalized to every matching call site, not just the
  first one found.** (1) **NUL-byte sanitization at every JSON-column SQL write boundary.**
  `fabric.entities.store` already sanitized (`strip_nulls`) at its write boundary; audited every
  other `mapped_column(JSON)` store in `jazzx_sdk` and found 6 more that didn't:
  `fabric/conversation_store.py::SqlConversationStore`, `evaluation/feedback_db.py`,
  `evaluation/prompt_registry_db.py` (sanitizes before hashing, so `version` stays consistent with
  what's stored), `conductor/suspension_store_db.py`, `runs/store_db.py` (7 call sites collapsed
  onto one `_sanitized_dump` helper), `agents/definition_store_db.py`, `llm/cost_store_db.py`
  (its one open `dict[str, Any]` field). All now sanitize. (2) **New shared primitive,
  `jazzx_sdk.concurrency.call_maybe_async(fn, *args, timeout=None, **kwargs)`** — decides sync-vs-
  async *before* invoking a caller-pluggable callable (never calls it eagerly, so a blocking sync
  callable can't defeat a timeout the way the old `if isawaitable(fn(...))` idiom could), offloads
  a sync callable via `run_offloaded`, and uniformly times out either branch. Replaced 12 hand-
  rolled instances of the same "call this pluggable callable, sync or async, check
  `isawaitable`/`iscoroutinefunction`" pattern across `tools/base_registry.py`,
  `evaluation/scorers.py` (`FunctionScorer`, `AdjudicatorScorer`), `evaluation/pass_bars.py`,
  `evaluation/optimization.py`, `agents/document/{agent,pipeline}.py`,
  `agents/interactive/{agent,chat,registry}.py`, and — the most consequential find — **`conductor/
  engine.py`'s step/guard/loop-convergence dispatch**, the core execution path every pack
  conductor run goes through: the old `_maybe_await(comp(state))` shape called `comp(state)`
  eagerly, so a blocking sync step component stalled the loop *before* any timeout could bound it;
  `call_maybe_async` closes that for real, not just cosmetically. Removed `conductor/engine.py`'s
  now-dead `_maybe_await` helper and simplified `_emit_step_event`'s timeout branching in the same
  pass. `jazzx_sdk.__all__` gained `call_maybe_async`. 13 new/updated tests across
  `test_fabric_conversation.py`, `test_base_tool_registry_execute.py` (new),
  `test_concurrency.py`. Full suite green (2589 passed, 3 skipped).

- **`run_with_recovery` — schema-validation/truncated-output/API-status retry for a caller that
  builds its own `Agent`, 2026-08-12.** `InteractiveAgent` had none of `run_agent`'s recoverable-
  failure handling (`ModelBehaviorError`/`IncompleteOutputError`/`APIStatusError`) since it builds
  its own `Agent` (skills-as-sub-agents) and calls `Runner.run()` directly rather than going
  through `run_agent`. New `jazzx_sdk.agents.run_kit.run_with_recovery(run_once, *, feedback,
  name, max_retries=3, on_retry=None)` — the same retry mechanism over a caller-supplied
  `run_once()`/`feedback()` instead of owning Agent construction (so it skips MaxTurns
  continuation, which needs to rebuild the Agent — stays `run_agent`-only). `run_agent`'s own two
  feedback-message bodies extracted into shared `_model_behavior_feedback`/
  `_incomplete_output_feedback` helpers so wording can't drift between the two; `run_agent` itself
  otherwise untouched (33 existing tests re-run unchanged, confirming the refactor is behavior-
  neutral). Wired into `InteractiveAgent._respond_agentic` — `feedback` appends to the active
  session when one exists, or to the input list directly when stateless; not wired into
  `_stream_agentic` (already documents why: can't retry after partial output streamed). Checked
  `DocumentAgent`: needs no change — its `classify`/`extract` already route through
  `OpenAIProvider`'s no-tools/single-message fast path → `run_agent`, so already covered; the new
  primitive is there for whenever it (or a future agent) builds its own `Agent` directly. 8 new
  tests in `test_agents_run_kit.py`, 2 in `test_interactive_agent.py` (stateless + active-session
  retry through `respond()`). Full suite green (2597 passed, 3 skipped).

- **`DocumentAgent` closes its "fat agent" source-description gaps, 2026-08-12.** Surveyed how
  much of the `ReasoningAgent`/`InteractiveAgent` shape `DocumentAgent` already had before adding
  anything (its own docstring already calls out this family) — most of it: `DocumentAgentSpec`
  (policy, YAML-loadable) + `DocTurn`/`run_document` (per-invocation, conductor-routed source
  description already unifying folder/KH-collection/standalone-zip into one auto-detected
  "collection" route via `process_dir`'s incremental+manifest+concurrent machinery) already mirror
  `InteractiveAgentSpec` + `respond()`. Three real, narrow gaps closed: (1) no "downloadable"
  source — new `jazzx_sdk.tools.documents.local.download_to_file`/`download_files` (SSRF-safe,
  sharing `read_from_url`'s per-redirect-hop-validated `_safe_fetch`, now extracted as a shared
  helper; concurrent via the same `conductor.fan_out` `process_package` already uses; a failing
  URL is skipped not batch-sinking; Content-Disposition filenames sanitized against path
  traversal). (2) "fabric accessible" was collection-only — new `DocumentAgent.materialize_blob_to`
  (durable counterpart to the existing temp-file-only `process_blob`). (3) no one-call front door —
  new `DocumentAgent.run(turn: DocTurn, ...)` wraps `build_document_pipeline`/
  `build_document_components`/`run_document` in one call, mirroring `respond()` (local import
  inside the method to avoid `pipeline.py`↔`agent.py` circularity). `DocTurn` gained `urls:
  list[str]` and `blob_pointers: dict[str, str]` (pointer→filename, required per-pointer since a
  blob key carries no extension and `convert_document` routes on it), both auto-routing to the
  existing "collection" branch — a downloaded `.zip` gets unpacked by `process_dir`'s existing
  `include_zips` handling for free, no new zip logic needed. Confirmed, not changed: template
  routing (`route_template`) already "use a registered template if available, else schema-only."
  15 new tests (`test_download_files.py` new, `test_document_pipeline.py`,
  `test_document_agent.py`). Full suite green (2612 passed, 3 skipped). Planned in plan-mode first
  (`/Users/sangit/.claude/plans/atomic-doodling-sun.md`) given the multi-file scope.
- **`MatrixCondition` — a table-valued `Condition` kind (P8, D2), 2026-08-13, uncommitted.**
  Motivated by a real client engagement (Acra DSCR, jaci `docs/plans/
  Acra_DSCR_on_Platform_v2_Reuse_and_Build_Plan.md`) whose eligibility grid had no clean
  encoding in the existing four kinds. Generalizes `RatioCondition`'s single `profile:<key>`
  threshold to an N-axis lookup (numeric-banded or categorical per axis); resolved cell values
  live in a new `PolicyProfile.tables` bucket (`profile_table:<name>`, fail-closed
  `get_table()`) — never a literal, same discipline as `RatioCondition`. An explicit
  `NA`/`False`/`None` cell is `VIOLATED`, not `INDETERMINATE`. Fully additive — confirmed by
  reading every `condition.kind` dispatch site (`DefaultPolicyExpert.check_compliance`,
  `agents/adjudication/{segment,partition,impact}.py`) already goes through the open
  `get_condition_evaluator` registry, so none needed editing. Also fixed a real latent gap
  found along the way: `ComparisonOperator.IN`/`NOT_IN`/`CONTAINS` were declared on the enum but
  never implemented in `ExpressionEvaluator` (silently always-`VIOLATED`) — now implemented,
  closing D2's secondary "N states → N rules" ask on the existing `Expression` kind rather than
  extending the (purely numeric) DSL. 34 new tests across `test_condition_evaluator.py` /
  `test_default_policy_expert.py`, all synthetic/toy data (no real Acra numbers exist in-repo).
  Full suite green (2911 passed, 3 skipped). No jaci-side wiring yet — `acra_dscr`'s pack has no
  `MatrixCondition` usage until real Acra grid data exists.
- **HITL suspend inside a `Loop` (D3), 2026-08-13, uncommitted.** Same Acra doc, same-day
  follow-on to D2. `ConductorEngine` previously turned a `SuspendRun` raised inside a loop's body
  straight into a `RuntimeError` ("supported only for top-level steps") — Acra's per-condition
  and per-property exception approvals are loops, and more generally no investigation-loop
  scenario could ever pause mid-iteration for a human. Fix: `_run_loop` catches a mid-body
  suspend per-step (knows exactly which step/iteration) and gained a resume-aware entry point
  that finishes the interrupted iteration's remaining steps without re-running earlier ones,
  then continues the loop and the rest of the pipeline normally; `_execute`'s local bookkeeping
  (`steps`/`seq`/`loop_status`/`done_loops`/`max_iterations`) became optional seeded params so
  the post-loop continuation reuses its existing `done_loops`-skip logic unchanged.
  `Suspension`/`DurableSuspension` gained additive `loop_id`/`loop_iteration` (no DB migration —
  `DurableSuspension` round-trips through one JSON column in both stores). New
  `ConductorPipeline.get_loop()`. A second suspend inside the same resumed loop, and
  `resume_durable` through a loop suspend, both work via the same one resume path — no
  special-casing. Replaced the one test asserting the old `RuntimeError` with 5 real tests. Full
  suite green (2915 passed, 3 skipped). No jaci-side usage yet — same scope discipline as D2.
- **Two condition-evaluator bugs fixed, 2026-08-13, uncommitted, reported externally (not
  self-found).** Verified both against code before fixing. (1) `RatioCondition.direction` was
  typed `ComparisonOperator` (9 values) but `RatioEvaluator` only ever handled 2 (`>=`/`<=`) —
  a strict operator like `<` validated at construction, then raised `ValueError` at first
  evaluation. Narrowed the field to `RatioDirection` (the existing 2-member enum
  `evaluate_ratio` already expects) directly — confirmed empirically pydantic already coerces a
  `ComparisonOperator.GTE` instance and rejects `.LT` with its own clear message, so the type
  narrowing alone fixes it; added a validator on top only to explain *why* (margin-to-threshold
  semantics) and point to `Expression` for strict comparisons. Grepped both repos first: every
  existing call site already used `>=`/`<=`, so non-breaking. (2) `ExpressionEvaluator.evaluate()`
  unconditionally `float()`-cast the actual value for every non-membership operator — a
  string-typed field (`citizenship_type == "itin"`) raised `ValueError`. `==`/`!=` now compare
  raw values (`"5" == 5` is correctly `VIOLATED` now, a real behavior change, called out
  explicitly); ordering operators still cast but a cast failure is `INDETERMINATE`, not a raise
  — matches `DslEvaluator`'s own existing convention. `_OPS` (the full numeric map) kept intact
  for `MatrixEvaluator`'s continued reuse; only `ExpressionEvaluator.evaluate()`'s own dispatch
  changed. 10 new tests in `test_condition_evaluator.py`. Full suite green (2925 passed, 3
  skipped); jaci's own suite re-run too (695 passed, 2 skipped, same pre-existing unrelated
  `DecisionType` failure) since `RatioCondition` is core policy IR.
- **`InteractiveAgent` reasoning-streaming, 2026-08-17, uncommitted.** Prompted by an external
  review of three specific gaps (un-hardcode `Reasoning.summary`, stream reasoning deltas from
  `respond()`, forward nested skill sub-agent deltas via `as_tool`'s `on_stream`); verified each
  against code before agreeing, then generalized rather than patching the three literally.
  Core design: reasoning deltas join the same `publish_event` sink `ToolStreamHooks` already
  uses, rather than a second generator-yield channel like `respond_stream()`'s text deltas — one
  new `InteractiveAgentSpec.stream_reasoning: bool` flag governs both the parent run and every
  skill sub-agent, mirroring `stream_tool_events`'s exact scope, just via a different SDK
  mechanism per event kind (tool lifecycle = `AgentHooks`, works under `Runner.run` either way;
  reasoning/text deltas only exist on the streaming path at all). `build_model_settings` gained
  `reasoning_summary` (was hardcoded `summary="auto"`); `_respond_agentic` switches its internal
  `_run_once` to `Runner.run_streamed` + full drain only when `stream_reasoning` is set (`respond()`'s
  own return contract unchanged) — explicitly documented cost: `run_with_recovery`/context-window
  fallback don't apply in that mode, the same tradeoff `_stream_agentic` already accepted for the
  same reason (can't retry after publishing partial output); `_build_parent_tools` passes
  `on_stream=` to `sub_agent.as_tool(...)` under the same flag. New shared classifier
  `stream_hooks.reasoning_delta_text`/`publish_reasoning_delta` — one function serves both the
  top-level `stream_events()` drain and the nested `on_stream` callback, since
  `AgentToolStreamEvent["event"]` is the identical `RawResponsesStreamEvent` shape either way
  (verified against the installed SDK, not assumed). Uses `common.core.streaming.ReasoningEvent` —
  already reserved ahead of any producer in the `common` submodule (Veeru's own local, unpushed
  commit `cffefc4`, checked out but not yet bumped into japes' recorded submodule pointer),
  imported guarded like `FinalResultEvent` so an older pinned `common` degrades to a silent no-op
  rather than an ImportError. **Real gap found, not papered over**: `ReasoningEvent` (and
  `ToolStartEvent`/`ToolEndEvent`) carry no per-event agent attribution field — nested skill
  reasoning publishes unattributed, same pre-existing limitation the whole event family already
  has, not new to this change; fixing it needs a `common` schema change, out of scope for a
  japes-side pass. Did not touch anything under `common/` (submodule, not japes' to edit here).
  10 new tests (`test_reasoning_stream_hooks.py`, `test_agent_models.py`, `test_interactive_agent.py`).
  Full suite green (2998 passed, 3 skipped).

Design docs (gitignored, `docs/plans/`): `reasoner-chassis-analysis.md` (P1/P2/P6/P8 build
sequence + Phase 4 chassis), `policy-ir-abstraction.md` (P8 detail),
`design_note_reasoning_substrate.md`, `plan_eval_service_contract_convergence.md` (eval-service
contract convergence, Phases 0-5 shipped).

### Related repos
- **jaci** (`/Users/sangit/src/jaci`) — the primary real consumer validating this version.
  Its `dev` venv has japes editable-installed against this checkout (`pip show japes` →
  `Editable project location: /Users/sangit/src/japes`), so it's always running live
  against whatever's in the working tree here, regardless of jaci's own git-pin/lockfile
  state (which is separately known-stale — see jaci's own CLAUDE.md).

### sdk-layout refactor — folded into the v2.3.0 commit
Module-reorganization only, no behavior/API change — per `docs/plans/REFACTOR-2.3-sdk-layout.md`
(gitignored). Built and verified on `refactor/sdk-layout-2.3` first (branched from `dev`@`33f1605`)
deliberately, not applied to `dev` directly: macer/jaci/juno run live `.pth` path installs against
this working tree, so a direct `dev` edit would have hit them immediately with no version-bump
gate. All 5 phases done and verified independently (full suite green throughout, `-X importtime`
diffed against a Phase-0 baseline after every phase — confirms no new eager dependency, and that
`mlflow` actually *left* the eager path — import-boundary suite green, a live `create_app()` smoke
test against `/health`/`/invoke`/`/stream`). `git merge --squash` + `git commit --amend`'d into the
same `dev` commit as the rest of v2.3.0 — deliberately, since a minor bump is exactly the point
at which a layout change like this is acceptable to make. That commit is now pushed (see Version
Status above); the refactor branch itself was fully folded and has since been deleted. Two
jaci-side one-line fixes (settings_fields.py, demo_page.py) landed immediately on jaci's own
`dev`, since jaci's live path install saw the new layout right away rather than waiting for a
japes push. Of the other external consumers: macer and jazzx-assistant are both pinned to specific
refs (not floating), so this doesn't reach them until they bump; juno floats on `main` (not `dev`),
so it's untouched until this promotes there.

## Notes
- Always update CLAUDE.md after significant discoveries or decisions
- This file is gitignored (see .gitignore:67) - local session tracking only
- Purpose: Maintain context across Claude sessions after accidental quits
- Keep this section current, not an append-only log — replace stale status rather than
  stacking a new dated section on top of old ones; git history already has the archive.

---

## Documentation Standards

### What Goes Where

**Commit to Repository:**
- ✅ **CHANGELOG.md** - All user-facing changes, new features, breaking changes
- ✅ **README.md** - Current version, quick start, high-level capabilities
- ✅ **ARCHITECTURE.md** - System design, patterns, technical decisions
- ✅ **docs/** - User guides, tutorials, integration examples

**DO NOT Commit:**
- ❌ **Planning documents** - Analysis reports, comparison docs, decision matrices
- ❌ **Temporary reports** - Branch analysis, migration planning, feasibility studies
- ❌ **AI conversation artifacts** - Claude work summaries, task breakdowns

### Rationale

**Planning documents are transient:**
- They capture a moment in time during development
- They become outdated as soon as decisions are implemented
- They add noise to the repository history
- They don't help users understand the current system

**Commit the outcomes, not the planning:**
- ✅ Decision → Document in ARCHITECTURE.md with rationale
- ✅ New feature → Document in CHANGELOG.md with usage
- ✅ API changes → Update README.md and relevant docs
- ❌ "Should we do X or Y?" analysis → Use for decision, discard after

### Examples

**WRONG:**
```
docs/
├── macer_kg_vs_dev_report.md          ❌ Transient analysis
├── document_chunking_evaluation.md    ❌ Planning document
└── migration_options_comparison.md    ❌ Decision matrix
```

**RIGHT:**
```
CHANGELOG.md                           ✅ "Added document chunking framework"
ARCHITECTURE.md                        ✅ "Document Module Design"
docs/DOCUMENT_CHUNKING.md             ✅ "How to use chunking in your pack"
```

### Development Workflow

When implementing a new feature:

1. **Analyze** - Create planning docs in `/tmp/` if needed (or docs/plan_*.md which is gitignored)
2. **Decide** - Document the decision and rationale in ARCHITECTURE.md
3. **Implement** - Write code and tests
4. **Document** - Update CHANGELOG.md, README.md, and user guides
5. **Commit** - Commit code + documentation (NOT planning docs)
6. **NEVER PUSH** - ⚠️ **CRITICAL: Never run `git push` without explicit user approval**

### Git Commit and Push Policy

**Commits: ✅ ALLOWED**
- Create commits with descriptive messages
- Stage changes with `git add`
- Use the commit workflow from system instructions

**Pushing: ❌ FORBIDDEN WITHOUT APPROVAL**
- **NEVER** run `git push` without explicit user request
- **NEVER** run `git push origin <branch>` automatically
- User must review commits and decide when to push
- User needs to verify attribution and commit messages (no Co-Authored-By trailer or other
  AI-attribution marker — see "Documentation and attribution" below; commits should read as
  if the user wrote them)
- Before saying work is "ready to push" (or recommending it), check open Dependabot alerts
  on `main` (`gh api repos/JazzX-LLC/japes/dependabot/alerts -q '.[] | select(.state=="open")'`)
  — alerts reflect the default branch's dependency graph, not whatever branch is being worked
  on, so they're easy to miss otherwise. Flag anything open, don't just push past it.

**Rationale:**
- User needs to review all commits before they go to remote
- Attribution must be verified
- Commit messages may need adjustment
- User controls when work is shared with team

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Documentation and attribution
- Code should not look like it came from AI, including any comments or commits that say Co-authored
by Claude Sonnet etc
- CHANGELOG, README, and ARCHITECTURE md files should be regularly updated
- If signitificant changes, the bump up at least patch version. For major version update, enquire

## 6. Dependency version specs
- Use `>=` floors, never `^` or upper caps — don't lock us into a version ceiling. e.g.
`openai-agents = ">=0.17.0"`, not `^0.17.0`. (To pick up a newer release, update the installed/locked
version, not the spec.) Other JazzX repos may use `^`; in our repos prefer `>=`.

## 7. Symmetry & cross-cutting consistency
- Japes is v2; the services built on it (juno, kernel, assistant, knowledge-hub) are still v1-shaped.
That gap is real leverage, not just cleanup debt — japes can absorb patterns those services already
proved out and make them the consistent default, rather than leaving each service to re-derive its
own version.
- When a fix or feature touches one client/module, ask "does this same gap exist in the sibling(s)?"
before calling the work done. Precedent: adding `request_headers_provider` to `KernelClient` because
`KnowledgeHubClient` already had it. The same question applies to any other family that shares a
shape — e.g. `fabric.db` vs `fabric.blob`, other client wrappers, conductor entry points.
- Check the full family, not just the nearest sibling. If three modules share a pattern and only one
got the fix, the other two are latent bugs until proven otherwise — not intentional differences.
- When a cross-repo survey (kernel/assistant/knowledge-hub/juno/macer) surfaces a gap, generalize it
into japes properly rather than patching only the one reported instance.
- Prefer the more architecturally consistent shape over the fastest patch, given japes's exposure
(number of existing external consumers depending on current behavior) is still comparatively small —
this is the window to fix a leaning wall, not wallpaper over it.
---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

