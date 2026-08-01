# Plan: PRD Demo Arc and Trap Fixtures

Author: Virendra Mehta · 2026-07-28 (rev 3, supersedes rev 2 in place)
Repo: jaci · Baseline: 0.9.8 (dev)

Rev 3 corrects a false premise in rev 2. That revision claimed `CI_PIPELINE` was a code literal and that the demo should migrate onto `CL_SPREAD_PIPELINE`. Both pipelines are YAML-declared, `cl_of_core` covers only the spread phase while the demo needs the credit phase too, and `plan_conductor_collapse.md` is already converging `CIConductor` onto `ConductorEngine` using the `ci-spread-core` descriptor. No conductor swap. The demo gains a step instead.

**Status warning added 2026-07-30.** This plan has no `done_`/`status_` file under any revision, but work from rev 2 landed and is recorded in `docs/status/CHANGELOG.md`. Phase 1 and Phase 6 are done. Do not treat the absence of a status file as evidence that a phase is open, and read the CHANGELOG before starting anything here. A status file reconciling every phase against the CHANGELOG is owed and is the first task.

Depends on: nothing unlanded for Phases 1, 3, 4 and 6. Phase 2's cleanest form wants `plan_conductor_collapse.md` finished. Phase 5 needs fixture packages arriving from outside, a scheduling dependency rather than a code one.

Driver: the demo opens on a clean public filer and walks a happy path. The PRD's argument (section 2.4) is that the hard part is packages where the face of the statements misleads you, and section 9.3 names six traps the product must permanently guard. This plan restructures the demo around those failure classes and makes the demo beats and the eval fixtures the same artifact.

## Grounding notes (verified 2026-07-28 against dev)

- `config/packs/ci-spread-core/pipelines.yaml` declares two pipelines, `credit_analysis` (13 steps, investigation loop, max 6 iterations) and `spread` (5 steps), loaded by `CIConductor` via `ConductorPipeline.from_yaml`. Steps carry `component:` as descriptive display strings, not resolvable references, plus `label`, `emits`, `execution`, `note`, `phase` and `substeps`.
- `CIConductor` imports `BaseConductor, ConductorPipeline`, not `ConductorEngine`. Its `run()` is still hand-rolled. `plan_conductor_collapse.md` is in progress and maps every `credit_analysis` step id onto a component method.
- `config/packs/cl_of_core/pipelines.yaml` declares `spread_validate` only, with resolvable `impl:` ids through a `StepRegistry`. It does not cover the credit phase.
- Instrumentation exists only on the capability side: `run_cl_spread` brackets a run with `pipeline.run.started` and `completed` and wraps the registry with `instrument_registry` to emit `vp.activity.*`. It binds to a `StepRegistry`, so it does not apply to a component-bound pipeline.
- The `spread` pipeline's `spread_financials` step emits `FinancialSpread`. `spread_financials_package` in `capabilities/commercial_lending/spread_package.py` emits `SpreadPackage` with per-cell `DecimalValue`, `SourceCoordinate`, `ProvenanceEntry` and `Confidence`. The demo currently runs the former and therefore has no per-cell provenance.
- `_run_ci_spread_phase()` in `demo_page.py` already runs `run_cl_spread` over `CL_SPREAD_PIPELINE` and stores the real `SpreadPackage` in `st.session_state["ci_spread_package"]`, from both the Acts tab's Run Act 1 button and the Trace tab's Run spread phase button. It is already passed as `spreader_template_trace(_live_spread, package=_live_package)`, so per-cell confidence and source coordinate are computed on every run. An earlier revision of this note claimed the seam was unfed. It is fed.
- A Target Template tab is live in `demo_page.py`, static, rendering from `spread_template.yaml` with no run behind it. `render_spreading_tab()` has a second post-run template viewer reconciling against `_YETI_TRUTH`, four keys. Two template surfaces in different tabs.
- `demo_page.py` holds `_YETI_SEC_ASFILED`, thirty rows whose labels match the template exactly, plus `curated_template_values(fd)`. Module constants, not case-parameterized.
- `docs/LoanSamples/YETI/yeti_financials.json` is the only financials fixture. The other four CI gold cases carry an `application` block of aggregates and an `expected_decision`, no statements. There is no per-line-item C&I gold corpus.
- `build_assessment` in `scenarios/ci_spread/credit_outcome.py` scores covenants from `values` keyed by metric id, plus `extra_covenants`. `concerns` is free text.
- The corpus six defect classes and the PRD's six traps are different, partially overlapping sets.

## Phase 1 - Governed spread in the pipeline the demo already runs — LANDED (rev 2)

Done. `_run_ci_spread_phase()` runs `CL_SPREAD_PIPELINE`, the `SpreadPackage` reaches session state, and `spreader_template_trace` receives it. Nothing to do here.

**The remaining gap is narrower and belongs to Phase 3.** `spreader_template_trace`'s return value carries `cells: {period: {confidence, source}}` per row, and the Target Template table (`demo_page.py`, around line 1944) reads none of it. It renders match-kind text only. The provenance is computed and sitting in memory one field away from being a column. That is a small, low-risk addition, not a pipeline migration.

## Phase 2 - Instrumentation seam and live pipeline map

Run state on the pipeline map, sourced from events rather than UI bookkeeping.

The seam is the work. `instrument_registry` binds to a `StepRegistry`, so it does not reach a component-bound pipeline. Generalize emission to `ConductorEngine` level so both binding styles emit the same `vp.activity.*` events. That single change instruments `credit_analysis` and `spread` as well as the capability pipeline, rather than solving it once per binding style.

This is cleanest after `plan_conductor_collapse.md` lands, since a hand-rolled `run()` has no engine to emit from. Coordinate rather than duplicate: do not re-map steps to components here, that plan owns it.

Add a Fills column naming which template sections each step populates: statement sections for `spread_financials`, credit metrics and working-capital days for the metrics step, nothing for the credit-phase steps, which consume rather than fill. Derive it from the template asset, not a hand-written list.

The Fills column is what stitches the pipeline view to the output format and depends on none of the above. Build it first and separately.

Acceptance: the map reflects which steps executed in the current session for both pipelines, from events. The Fills column is derived from `spread_template.yaml`.

## Phase 3 - Column-progressive template view

Extend the live Target Template tab so one table accrues columns as the run proceeds, and retire the duplicate post-run viewer in the spreading tab so there is one template surface. **Do not rebuild the tab.** The static render works; what is missing is the accrual and the duplication.

- Before any run: line items plus as-filed reference columns from `_YETI_SEC_ASFILED`. Opening on the institution's own figures beats opening on blanks.
- After the spread step: extracted columns with per-row match kind and confidence from `spreader_template_trace`.
- After the metrics step: credit metrics and working-capital days fill, visibly by a different mechanism.
- After the credit phase: rows the decision depends on, deferred to Phase 6.

Label the columns as filed, curated reference, and extracted. Three different things; conflating them will not survive a question. Put the as-filed coverage count in the caption, since thirty of roughly eighty rows carry a reference figure.

Acceptance: renders with no run in session state, and each step adds columns without re-rendering a different table.

## Phase 4 - Trap fixtures as gold cases

Reconcile the corpus six defect classes and the PRD's six traps into one set, each fixture tagged with both provenances rather than parallel suites. PRD traps: the LTM sign-label note, the bad-debt add-back inconsistency, footnote-only items, a cross-document comparative discrepancy, a compilation omitting the cash-flow statement, and interim-versus-year-end balance-sheet confusion.

Each becomes a gold case under `tests/eval/gold_cases/ci/` with the expected finding as its assertion, and each is a demo beat. Nothing authored twice.

Where a fixture arrives from outside, take it as given and record its provenance in the case file. Where one is synthesized, say so in the case file rather than a comment, so the demo narration is accurate without anyone having to remember.

Acceptance: every trap has a case that fails before its guard exists and passes after. The suite reports which traps are covered and which are declared but unguarded.

## Phase 5 - The three acts

Wire the acts as an explicit sequence rather than tabs a presenter navigates from memory.

- **Act 1, clean path.** YETI, tightened by Phases 2 and 3.
- **Act 2, three failure classes.** A silent parsing error propagating into EBITDA, leverage and covenant headroom, caught by the tie-out and refused by the confidence gate. The bad-debt add-back applied in one year and nowhere else, flagged rather than reproduced. Footnote-only items surfaced from the notes into the credit view.
- **Act 3, the LTM column.** Built from a mixed-assurance stack, showing the derivation and each component's assurance, the cash-flow gap flagged rather than silently tied out, and the sign-label trap where the source note states the formula wrongly and the engine encodes the verified one.

Act 3 has no UI today though `construct_ltm` is complete, so it is the largest build. It maps to the MVP exit criterion, so it should not be the one that gets cut.

Acceptance: each act runs from the demo page without a presenter editing state by hand, and every beat corresponds to a gold case in CI.

## Phase 6 - Decision dependency marking

Separated from Phase 3 because it is the only part of that view not backed by existing data. No field on `CreditRecommendation`, `Outcome` or `Evidence` names template rows; `rationale`, `key_risks` and `key_concerns` are free text and `guidance_refs` point at playbook sections.

**Do not add a `cited_rows` field and do not ask the credit-phase prompt to emit row keys.** `row_key` is `(section, label)` from `template.py`, a presentation construct owned by the pack's output template. Emitting it from a cognitive mode couples the reasoner to one institution's layout, so a relabelled row silently breaks citation. Asking a free-text reasoning prompt to also emit structured references is the prompt-fragility pattern we avoid.

Derive it. `build_assessment` scores covenants from metric ids. `metrics.yaml` binds each metric id to a formula whose `SCOA_LINE` inputs are canonical keys. `spread_template.yaml` binds rows to metric ids and canonical keys. So:

- Metric rows: the metric ids in the covenant evaluation.
- Statement rows: the transitive closure over those metrics' input bindings, following `CUSTOM_METRIC` bindings to their `SCOA_LINE` leaves.

A graph walk over pack data, possible only because the chart of accounts and metric catalog landed. More honest than a model self-report: it shows what the decision mathematically depended on rather than what the reasoner said it considered.

Label it as rows this decision depends on, not rows it cited. The free-text concerns (intercreditor resolution, field exam, the QoE recall) will not light up rows, and that is correct rather than a gap. Do not paper over it by fuzzy-matching prose against row labels.

Acceptance: on YETI the marked set is exactly the covenant-scored metrics plus their binding closure, asserted against an explicit expected set. Renaming a template row label changes which row is marked and breaks no citation, proven by a test.

## Out of scope

Swapping the demo's conductor. Retiring `CI_PIPELINE`, `CIConductor` or the `cl_of_core` pipeline. Converging `component:` display strings onto resolvable `impl:` ids, which is real and worth doing but is not needed here and should not ride along. A borrower selector on the spread surface, since only one borrower has statements. Per-case ground-truth fixtures and retiring `_CURATED_BS`. The governed workbook export. The review queue surface.

## Sequencing

Phase 1 first; it is small and everything visual depends on the demo having a `SpreadPackage`. Phase 2's Fills column depends on nothing and can land any time; its run-state half should wait for the conductor collapse. Phase 3 is the opener and the highest-value screen. Phase 4 is authoring and runs in parallel with any of them. Phase 6 depends only on landed pack assets and is the least demo-critical. Phase 5 depends on Phases 1 through 4 and on fixture packages, so start that conversation before the build.
