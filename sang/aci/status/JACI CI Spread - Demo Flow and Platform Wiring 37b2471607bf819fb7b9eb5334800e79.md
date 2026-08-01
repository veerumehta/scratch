# JACI CI Spread - Demo Flow and Platform Wiring

**Author:** Virendra Mehta | **Updated:** 2026-06-10 | **Status:** Active

**TLDR:** The CI spread scenario runs YETI Holdings ($20M ABL revolver) through the full IIF v1.5 loop - all five canonical objects, seven cognitive modes, PolicyExpert advisory layer, fabric.canonical persistence. Two borrowers are now in the demo (YETI C&I + MAA REIT), sharing a common commercial-lending pipeline. The live conductor is wired and running tonight; end-to-end with live LLM is Monday's target.

---

## What the Demo Shows

Two borrowers, same platform machinery:

- **YETI Holdings** - $20M senior secured C&I ABL revolver. Financially strong (0.27x net leverage, net cash). Structural complexity: existing first-lien term loan requires intercreditor resolution before closing. Curated reference fixture (`yeti_financials.json`) plus an automated 10-K spreading flow.
- **Mid-America Apartment Communities (MAA)** - REIT/multifamily corporate facility. No hand-built fixture - every figure computed live from 10-K spreading (FY2021-FY2025). Different statement shape (NOI-based), different policy assets (DSCR/debt-yield covenants), same SDK.

Both share:

- `render_spread_analytics`, `render_spreading_tab`, `render_docs_and_policies`, `render_pipeline_map` - shared renderers in `jaci/scenarios/commercial_lending/ui/`
- `run_document_intake`, `run_entity_extraction` - shared pipeline functions
- `CIConductor` as the orchestrator (YETI only for the live trace; MAA trace is computed deterministically from the spread)

---

## IIF v1.5 Canonical Objects

All five canonical objects from Schema Spec §2-6 are in play.

**Policy**

- Four core policies loaded into `PolicyRegistry`: leverage, FCCR, ABL advance rates, lien position
- Each `Policy` contains `Rule` objects with `Expression` conditions (`ComparisonOperator.LTE/GTE/EQ` + numeric threshold)
- Source refs: OCC Comptroller's Handbook, FDIC Risk Management Manual
- `RB_CI_OVERLAY` provides institution-specific narrowings keyed by `program_id` (thresholds are placeholder - calibration pending)
- CRE policy assets: separate `covenant_policy("cre")` with DSCR/debt-yield/LTV rules; served by `render_docs_and_policies`

**Evidence**

- Each tool call returns an `Evidence` object via `BaseToolRegistry.execute()`
- Types in use: `FINANCIAL_STATEMENTS`, `BORROWING_BASE_CERT`, `DEBT_SCHEDULE`, `UCC_SEARCH`, `AR_AGING`, `BANK_STATEMENTS`
- Investigator requests by type; tools fulfill; Verifier attests to `VERIFIED`
- Phase 0 document intake also produces Evidence objects (from real loan-package files when present)

**Decision**

- Reasoner produces `CreditRecommendation`: `decision`, `approved_amount`, `risk_rating`, `leverage_x`, `fccr_x`, `BorrowingBase`, `UCAcashFlow`, `advance_rates`, `conditions`, `covenants`, `key_concerns`
- Governor may override to `DECLINED`, prepending `POLICY VIOLATION:` to rationale
- Maps to `CanonicalDecision` at case close

**Trace**

- `CanonicalTrace.for_pack()` emitted at end of every `run_analysis()` call
- Fields: `workflow_id="ci-spread-loop"`, `case_id`, `pack_id="ci-spread-core"`, `pack_version`
- `domain_extensions`: loan_id, iteration_count, termination_reason, final_status, evidence_count, hypothesis_count
- Persisted to `fabric.canonical` (JSON-backed offline via `MockKnowledgeHubClient`); read back and shown in Tab 5

**Outcome**

- Not yet emitted. Planned in the EVOLVE layer after eval baseline is established.

Derived objects: `EvaluationReport` (ground-truth grading, when `ground_truth` passed to conductor), `CanonicalCaseFile` (persisted alongside trace, includes trace_id back-reference).

---

## Cognitive Modes: IIF v1.5 Mapping

Seven modes run across the conductor. All constructed in `CIConductor.__init__()` via the JAPES SDK operational mode interfaces.

**THINK / Investigator** (`InvestigatorMode`)

- Generates `SpreadHypothesis` objects with typed `SpreadHypothesisContent`
- `issue_type` enum: `LIEN_CONFLICT`, `BORROWING_BASE_SHORTFALL`, `LEVERAGE_BREACH`, `FCCR_INSUFFICIENT`, `DATA_GAP`, etc.
- Convergence gate: `FINANCIAL_STATEMENTS` + at least one of `{BORROWING_BASE_CERT, DEBT_SCHEDULE, UCC_SEARCH}`, minimum 2 iterations

**TRUST / Verifier** (`VerifierMode`)

- Receives `ctx.pending_evidence`; attests quality, consistency, freshness
- Applies report via `ctx.apply_verifier_report()`

**EXECUTE / Governor** (`GovernorMode`)

- Binding enforcement; receives context + `CreditRecommendation`
- On `decision == "block"`: sets `DECLINED`, prepends `POLICY VIOLATION:` to rationale, sets `ctx.loop_status = GOVERNOR_BLOCKED`
- PolicyExpert is advisory only - it feeds `key_concerns` into the recommendation; Governor makes the binding call

**INTERACT / Narrator** (`NarratorMode`)

- Runs only when decision is `APPROVED` or `APPROVED_WITH_CONDITIONS`
- Produces credit-memo narrative, conditions precedent, covenant scorecard

**EVOLVE / Evaluator**

- `compute_deterministic_metrics()` in `modes/evaluator.py`
- Grades `CaseFile` against `ground_truth` from `yeti_abl.json`; produces `EvaluationReport` with scores
- Runs when `ground_truth` is passed to the conductor

**EVOLVE / Sentinel** (`SentinelMode`)

- Deterministic loop-health monitor; no LLM
- Fires `GUARD_FIRED` on signal decay (repeated evidence requests, no new hypotheses) or max iterations
- `signal_decay_threshold=2`, `max_iterations=6` defaults

**EVOLVE / Reasoner** (`ReasonerMode`)

- `output_schema=CreditRecommendation`; synthesizes recommendation from the full evidence + hypothesis set

---

## PolicyExpert: Advisory Layer

`CIPolicyExpert` subclasses `DefaultPolicyExpert`. Advisory-only; all responses carry `output_classification = GUIDANCE_REFS`.

**resolve()** - reads `program_id` from context, selects core policies + overlays via `OVERLAY_MAP`. Returns `PolicyResolutionResult` with `applicable_policies`, `precedence_order` (overlays first), `conflicts`.

**check_compliance()** - calls `resolve()`, walks precedence order evaluating each `Rule.condition` against values from `CreditRecommendation` (`leverage_x`, `fccr_x`, `ar_advance_rate`, `inventory_advance_rate`, `excess_availability_pct`, `lien_position`). First overlay wins on field conflicts. Returns `ComplianceResult` with `allowed`, `policy_violations`, `applied_policies`, `rationale`.

Violations are fed into `recommendation.key_concerns` as labeled policy gate strings. Governor evaluates them as part of its binding decision. Purely deterministic - no LLM.

---

## Tool Registry and Evidence Fulfillment

`CIToolRegistry` extends `BaseToolRegistry`. Seven tools registered: `get_financial_statements`, `get_borrowing_base_certificate`, `get_ar_aging`, `get_debt_schedule`, `get_bank_statements`, `get_ucc_search`, `get_policy_clause`.

Resolution priority: `fabric` (KnowledgeFabric, production) → legacy document store (deprecated) → mocks (YETI-contextualized).

`BaseToolRegistry.execute()` wraps each tool's return dict as `Evidence` with `evidence_type`, `data`, `source`, `status=PENDING`. Verifier moves to `VERIFIED`.

---

## Phase 0: Document Intake

Shared pipeline function `run_document_intake()` in `jaci/scenarios/commercial_lending/`. Classifies submitted files against `_DOC_TYPE_MAP` (filename-keyword → CI doc type). Required types: `{financial_statements, borrowing_base_cert, debt_schedule}`. Missing required types produce `DATA_GAP` hypotheses via `_gap_hypothesis()`. Best-effort, non-blocking - never aborts the loop.

---

## Phase 1: Entity Extraction + fabric.graph

Shared pipeline function `run_entity_extraction()`. Single focused LLM call against ingested evidence. Extracts borrower profile, facility terms, financial line items, covenants, key dates, existing liens. Writes to `fabric.graph` as triples: `has_borrower`, `has_facility`, `has_lien`.

Best-effort and non-blocking today. Does not yet drive downstream analysis. Path to ontology-anchored computed financials runs through promoting this to authoritative - spread computed from KG nodes, not LLM-asserted from prompts.

---

## fabric.canonical Persistence

The conductor resolves a `KnowledgeFabric` instance via `_resolve_fabric()`: prefers a fabric passed to `run_analysis()`, then `tool_registry.fabric`, else builds a LOCAL-mode Mock-backed fabric. Never None.

After the loop:

- `CanonicalTrace` written via `canonical.put_trace()`
- `CanonicalCaseFile` written via `canonical.put_canonical_case_file()` with `trace_id` in `domain_extensions`
- Both read back in `_run_and_read()` and surfaced in the Trace tab "Intermediate artifacts" expander
- Offline: JSON files written to `output/ci_spread/{loan_id}/`

---

## Demo UI: Tabs

Streamlit at `src/jaci/scenarios/ci_spread/ui/demo_page.py` via `app.py` → "C&I Demo". Borrower selector in sidebar switches between YETI and MAA.

**YETI tabs (8):**

- **Overview** - what the demo shows, curated-vs-automated contrast table, conductor step walkthrough, DocIntel stubbing, model calls, IIF concepts
- **Spread** - 5-year IS + BS + credit ratios + trend chart; shows live `ci_spread_result` from 10-K spreading if available, else curated reference
- **Borrowing Base** - 3-year indicative BBC, utilization bar, structural lien flag
- **Covenants** - scorecard (leverage, FCCR, liquidity, current ratio, excess availability, intercreditor) + stress scenario; thresholds read from `fd["covenant_policy"]`, not hardcoded
- **Jazz** - live `claude-sonnet-4-5` via JAPES `LLMManager`; quick-question shortcuts + free-form chat
- **Trace** - `render_pipeline_map()` + step outcomes; fixture-driven by default (all strings from `yeti_abl.json` + `yeti_financials.json`); "Run conductor" wires to `_run_conductor()` → `CIConductor.run_analysis()` → `_render_live_trace()`
- **10-K Spreading** - `render_spreading_tab()` shared renderer; FY2025-only or multi-year filing options
- **Docs & Policies** - `render_docs_and_policies()` shared renderer

**MAA tabs (7):** Overview, Spread (via `render_spread_analytics`), Covenants (CRE scorecard via `_maa_covenant_scorecard()`), Jazz, Trace (deterministic from spread + policy, no live conductor), 10-K Spreading, Docs & Policies.

---

## Pack Architecture

- Pack ID: `ci-spread-core`
- Zero imports from `jaci/` back into `jazzx_sdk/`
- Domain types in `jaci/scenarios/ci_spread/schemas/`: `LoanApplication`, `SpreadHypothesis`, `SpreadHypothesisContent`, `SpreadIssueType`, `CIContext`, `CreditRecommendation`, `CaseFile`, `LoanDecision`
- AML conductor is the reference implementation for the conductor pattern; CRE conductor is not used as a template
- Shared commercial-lending pipeline in `jaci/scenarios/commercial_lending/`: `run_document_intake`, `run_entity_extraction`, shared UI renderers

---

## Open Items

- End-to-end live LLM conductor run (Monday) - plan: `JACI_CI_SPREAD_DEMO_LIVE_CONDUCTOR.md`
- Narrator produces prose only; serializing `BorrowingBase` + `UCAcashFlow` to a formatted Excel/table is the spreadsheet deliverable
- `RB_CI_OVERLAY` thresholds are placeholders - calibration from institution program guidelines pending
- `Outcome` canonical object not yet emitted - deferred to EVOLVE layer
- Path B (ontology-anchored computed financials): spread computed from KG nodes rather than LLM-asserted - post-demo roadmap
- MAA live conductor (currently deterministic from spread; no `CIConductor` run for MAA yet)