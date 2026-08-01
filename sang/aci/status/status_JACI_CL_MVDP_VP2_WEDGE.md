# Plan: JACI Commercial Lending MVDP VP-2 Wedge

**Status: Phases 1-3 done; Phase 5's instrumentation shipped (2026-07-27 audit).**
`SpreadPackage`/`SpreadLineItem` (`capabilities/commercial_lending/spread_package.py`),
`normalize.py`, `validation.py` (has `defect_class`), `promotion.py` (`SpreadDecision`,
`promote_spread`, `SpreadOverrideEvent`) all exist, confirming Phases 1-3. `cl_events.py`'s
`instrument_registry`/`cl_event_emitter` (Phase 5's `vp.activity.*` events) exists and is exactly
what `plan_JACI_CL_PRD_DEMO_ARC.md` rev 2 Phase 2 now sources its live pipeline-map run state
from — the eval-runner P90 timing-report half of Phase 5's acceptance is unconfirmed. **Phase 4
not started:** no `scripts/import_cl_tests.py`, no `tests/eval/cl_mvdp/`, no
`tests/fixtures/cl_defects/`.

**Note (from `docs/CL_SOURCE_RECONCILIATION.md`, 2026-07-27):** this plan's own docstring for
Phase 1 says the corpus schema generation (`plan_JACI_CL_PACK_FOUNDATION.md` Phase 3) reconciles
`SpreadPackage` to the corpus object-model shape later. It never did — see the flag on that plan's
own status file.

Author: Virendra Mehta · 2026-07-13 · Rev 2026-07-15 (Governor metadata contract + doc-chassis gate notes)
Repo: jaci · Baseline: 0.9.7 (dev) · Depends on: plan_JACI_CL_PACK_FOUNDATION.md (packs, schemas, registers), JAPES governed-value plan (Money/DecimalValue, Confidence, Refusal), JAPES authority plan (matrix, resolver; Phases 1-5 shipped on the 2.0.0 line)
Driver: the corpus MVDP certification scope is 85 L4 rows: the C&I Generalist + Manufacturing & Distribution VP-2 wedge (ingest -> classify -> extract -> map -> normalize -> compute -> validate -> package), the A3 credit-analyst review and CI-DC-04 affirmation, W1 promotion with underwriter supersession and effective view, plus the AU-1 writeback seam (surfaces plan). YETI, the corpus's own Manufacturing & Distribution certification fixture, is already our canonical ci_spread worked case, so this wedge extends our strongest scenario rather than starting fresh. Exit bar: MVDP-priority tests green including six defect fixtures, EADM-003-01 / REL-PIPE-01, and the 2h P90 cycle bar on clean fixture packets.

Grounding notes (verified 2026-07-13 against dev):
- src/jaci/scenarios/commercial_lending/: spreader.py (DocIntel markdown -> FinancialSpread, as-reported), analytics.py (compute_metrics C&I + compute_cre_metrics), pipeline.py (classify_document, run_document_intake, run_entity_extraction), policies.py (covenant_policy, document_checklist_policy, assess_package), docintel.py, excel.py, template.py.
- src/jaci/scenarios/ci_spread/: CIConductor two pipelines from pipelines.yaml: spread (Phase 1: intake -> entity extraction -> spread_financials -> validate_spread vs SEC XBRL -> persist) and credit_analysis (Phase 2 loop). Emits FinancialSpread, CreditMetrics, CanonicalTrace, CanonicalCaseFile, EvaluationReport.
- Gold cases tests/eval/gold_cases/ci: yeti, ace, techflow, overleveraged, tight_availability (5).
- Values are floats throughout; no SpreadPackage/SpreadDecision/ValidationFinding-with-defect-classes objects; no supersession beyond policy clauses; no XF gates as tests.

## Phase 1 - Pipeline objects to spec shape

Adopt the generated canonical schemas (foundation plan Phase 3) at the pipeline boundary. In src/jaci/scenarios/commercial_lending/:
- spreader.py: output becomes SpreadPackage containing SpreadLineItem rows (as-reported layer append-only) with per-line Provenance {provenance_type: sourced, source_coordinates} pointing into the DocIntel result (page/region where available, sheet/cell for workbook sources) and Confidence with tier resolved via profile floors. Keep FinancialSpread emission for one release behind a compat flag so existing Streamlit views do not break; crosswalk doc governs the rename.
- New normalize.py: NormalizationAdjustment objects for add-backs/reclassifications, each carrying provenance_type reviewer_entered|computed and a rationale; the add-back policy keys come from PolicyProfile, not constants.
- analytics.py: compute_metrics returns MetricResult objects with recomputed=true and derivation {formula, inputs[]} where every input carries its source ref (XF-3: never trust a stated ratio; LTM is a derivation with declared method/components). Values move to DecimalValue/Money. This is the file where float death happens; do it here first.
- pipeline.py: SourceFile with content_hash (idempotent ingestion), PipelineRun with the corpus PipelineRun state machine attached via the JAPES TransitionEngine (started/stage_completed/partial/completed/failed/cancelled/invalidated states as imported); document classification emits ExtractedField objects.

Acceptance: run_spread on the YETI packet produces a SpreadPackage where 100% of line items carry provenance and confidence (XF-1 gate, asserted as a test not a sample); zero float leaks (test walks the package tree asserting no float-typed values).

Note (2026-07-15): this phase's objects (SourceFile + content_hash, ExtractedField + SourceCoordinate + Confidence, the XF-1 gate) are the gate contract for the JAPES document-agent chassis (plan_JAPES_2_0_0_PACK_COMPOSITION_AND_CAPABILITY_SEAMS.md Phase 3). Land this phase with clean seams in scenarios/commercial_lending/ (not scenario packages) so the chassis can adopt the spreader path without re-plumbing; the chassis does not block, and this phase must not wait for it.

## Phase 2 - Validation and the six defect classes

- New validation.py: ValidationFinding with defect_class enum exactly matching the corpus six (sign/label errors, cross-period inconsistent add-backs, cross-document contradictions, content-free stubs, scale errors, hardcoded plugs) plus contradiction/staleness/precedence finding types; severity blocking|advisory. Blocking findings prevent package promotion (state machine guard, not an if-statement in UI code).
- Port the existing validate_spread SEC-XBRL reconciliation into this shape (it becomes one validator among several).
- Sub-confidence admission is a Refusal: values below profile floor refuse admission per cell cl.eadm.003 with the typed Refusal from JAPES; the pipeline records the refusal on the trace and continues with the value excluded (XF-2: a refusal, not a degraded write; silent low-confidence writes must be zero).
- Six synthetic defect fixtures under tests/fixtures/cl_defects/ (one per class, known ground truth, corpus fixture model): construct from mutated YETI statements; each fixture's manifest names the planted defect and the expected finding.

Acceptance: XF4-DEF-01..06 tests: each fixture yields exactly its planted finding class, zero silent absorptions; EADM-003-01 test: a below-floor value produces Refusal with reason_code and no write.

## Phase 3 - CI-DC-04 affirmation, promotion, supersession

- SpreadDecision: A3 (credit analyst) affirmation of evidence + spread, writer_of_record const A3-credit-analyst, matrix_cell_ref cl.am.004, evaluated through the JAPES authority resolver (human affirmation required; programmatic path refuses). Decision recorded via canonical DecisionStore; decision.recorded event emitted.
- Governor metadata contract (from the shipped JAPES authority Phase 5 deviation 3): the SDK Governor is domain-agnostic and reads cell_id from decision.matrix_cell_ref and actor_class from ctx.metadata under documented keys. SpreadDecision carries matrix_cell_ref as a schema const already; this plan's conductor calls MUST populate the actor_class metadata key on every gated action, and a test asserts a gated action with the key absent refuses rather than passing ungoverned.
- W1 promotion: promote_spread(case_id) operation (HTTP surface in the surfaces plan; the operation itself lives here): 422-class refusal on open blocking findings or missing affirmation; idempotent (re-promotion returns existing ref).
- Supersession: SpreadOverrideEvent (matrix_cell_ref cl.am.004-ovr, reason-coded, maps onto JAPES OverrideEvent semantics) producing EffectiveUnderwritingSpreadView; the as-reported layer and the affirmed package are never edited (append-only; terminal-state rule enforced by the state machine). spread.supersession.created and spread.reopened events.
- Wire ci_spread Phase 2 (credit_analysis loop) to consume the effective view instead of raw FinancialSpread.

Acceptance: authority tests: promotion without affirmation refuses; affirmation via API without human flag refuses (403-class); supersession preserves both versions with lineage and the effective view resolves to the override; re-promotion idempotent.

## Phase 4 - MVDP test import and gold cases

- scripts/import_cl_tests.py: from corpus data/test_cases.csv, import the MVDP-priority rows (authority/negative/refusal/defect/reliability kinds keyed to matrix cells our wedge exercises) as pytest parametrized cases under tests/eval/cl_mvdp/, each carrying its corpus test id and matrix_cell_id/control_id in the test id string for traceability.
- Gold cases: YETI stays the anchor (Mfg & Distribution); add RockCrusher (Generalist) when fixture assets arrive (fixture manifest tracks gold-label status; FIX-RB and FIX-CDIVE are corpus-acknowledged as unassembled, so do not block on four archetypes).
- Wire into the existing eval harness (SDK GoldenCase/ExperimentRun; TruthMode SME_REVIEWED once labels are signed, RULE_FIXTURE for the synthetic defect set).

Acceptance: pytest -k cl_mvdp green; every imported test names a resolvable cell/control.

## Phase 5 - Cycle instrumentation

- Emit vp.activity.started / vp.activity.completed / vp.exception.raised events (from the imported catalog) around each pipeline stage with l4_id refs from the backlog mapping; add a timing report to the eval runner computing P90 wall-clock on the clean-fixture set. The 2h P90 bar is a report first, a CI gate at certification (numeric targets are institution-set per ENG-03; do not hard-code the 2h as a test failure yet, print it).

Acceptance: eval run prints per-stage timings and P90; events validate against the catalog.

## Out of scope

VP-1/VP-3..VP-6 activities beyond what promotion touches, the 91-row CRE Multifamily demo slice (demo_only; separate decision), AU-1 writeback execution (surfaces plan; this plan stages evidence-to-LOS field mapping only via the imported connector_field_mapping data), agency overlay, A3/W1 UI (surfaces plan), byte-identical replay.
