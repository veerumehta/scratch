# Plan: Surfacing the Governed Layer (Wave 3 UI)

Author: Virendra Mehta · 2026-07-30
Repo: jaci · Baseline: 0.12.0 (dev)
Depends on: nothing unlanded. Waves 1, 3a and 3b are all in per `docs/status/CHANGELOG.md` (0.10.0, 0.11.0, 0.12.0).

Driver: uncovered scope. Waves 3a and 3b each deferred their UI wiring for the same reason, and `plan_JACI_CL_PRD_DEMO_ARC.md` predates both waves so it covers neither. The governed workbook, corrections with lineage, the risk-ranked queue, the source-region view and the maker-checker roles are built, tested and have zero presence in `demo_page.py`. This plan owns that gap.

Ordered by demo value, so it can stop at any phase and still have improved the demo.

## Grounding notes (verified 2026-07-30 against dev)

- Everything below is exported from `jaci.capabilities.commercial_lending` and importable today: `rank_for_review`, `covenant_feeding_keys`, `resolve_source_region`, `reverse_lookup`, `cell_source_regions`, `cells_fed_by`, `SourceRegion`, `Correction`, `make_correction`, `apply_corrections`, `CorrectionCategory`, `CorrectionTarget`, `coerce_legacy_corrections`, `MakerCheckerRoles`, `check_maker_checker_roles`, `self_review_permitted`, `exception_summary`, `ExceptionSummaryRow`, `spread_approval_engine`, `ApprovalRequest`, `SmeDecision`, `aggregate_status`, `build_effective_view`, `EffectiveUnderwritingSpreadView`, `standardized_template_rows`, `project_effective_package`.
- **`load_ci_workbook_layout` and `load_rb_workbook_layout` are not exported.** `capabilities/commercial_lending/workbook_layout.py` exists per the 0.11.0 changelog entry but appears in neither the package `__init__` imports nor `__all__`. Fix that in Phase 1 rather than importing from the module path in UI code.
- `_run_ci_spread_phase()` already stores the real `SpreadPackage` in `st.session_state["ci_spread_package"]`, from both the Acts tab and the Trace tab. Every phase below reads it from there; none needs to re-run the pipeline.
- **But only the `spread` step's output is captured.** `CL_SPREAD_PIPELINE` also emits `metrics` (`MetricResult[]`) and `validate` (`ValidationFinding[]`), and `_run_ci_spread_phase()` stores neither. So the demo currently runs every Wave 1 validator on every spread and discards the results. Phase 0 fixes this and Phases 1 and 2 both depend on it.
- `render_spreading_tab()` in `ui/shared.py` is a generic cross-capability helper (CRE uses it too). It takes a plain `FinancialSpread` via a scenario-supplied `session_key` and has no `SpreadPackage` parameter. Extend it with an optional `package=`, matching its existing `truth=` pattern and the `spreader_template_trace(package=...)` seam. Do not reach into `ci_spread_package` from inside `ui/shared.py`; that would couple a shared helper to one scenario.
- `spread_approval_engine` is a **suspend and resume** loop: `_approve` raises `SuspendRun` with an `ApprovalRequest` payload, and the driver resumes with an `SmeDecision`. Streamlit reruns its whole script on every interaction, so the suspension object must live in session state across reruns. This is the one genuinely tricky piece in the plan.
- The provenance columns on the Target Template table are **not** in scope here. That gap is named and owned by `plan_JACI_CL_PRD_DEMO_ARC.md` Phase 3. Do not build it twice.

## Phase 0 - Capture what the pipeline already emits

Prerequisite to Phases 1 and 2, and small.

`_run_ci_spread_phase()` captures `_run.emitted.get("spread")` and nothing else. Capture the `metrics` and `validate` emissions into session state beside it. The pipeline already produces both on every run.

Worth pausing on what this means before building on it: the validate step has been running on every demo spread since Wave 1 landed, and every finding it produced has been thrown away. Balance control, cash-flow tie, equity roll-forward, period continuity, cross-period add-back inconsistency, disclosure checks — all computed, none surfaced.

So look at the captured findings on YETI before assuming Phase 2's queue will be short. It may be empty, which tells you the validators are clean on that package. It may not be, which is more interesting and should be understood before it appears on a screen in front of an audience.

Acceptance: `MetricResult[]` and `ValidationFinding[]` are in session state after a run, and the YETI finding set is printed and read by a human once.

## Phase 1 - Governed workbook download

The cheapest item with real demo value: the workbook is built, tested and layout-driven, and has nowhere to be clicked.

Export `load_ci_workbook_layout` and `load_rb_workbook_layout` from the package `__init__` first. Then a download button that builds from the session `SpreadPackage`, its `MetricResult`s and its `ValidationFinding`s, using the CI layout.

**CI only. Do not add an RB download button.** There is no RB package anywhere in the demo — no file, no loading path, no trigger — so an RB button would be dead code. Exposing the RB fixture as a demo data source is a real separate lift and it belongs to `plan_JACI_CL_PRD_DEMO_ARC.md` Phase 4, which owns fixture wiring. Export the RB loader anyway, since the asymmetry of exporting one and not the other is worse than an unused export, but give it no UI.

The layout-driven claim still needs to be visible, and it does not need a second button to be. `workbook_layout_rb.yaml` already loads, validates against the chart of accounts and metric catalog, and produces a differently-shaped sheet set, proven by test at 0.11.0. Show the two layout YAMLs side by side in the pack assets view instead. The claim is that a new institution is a new file, so two files is the more direct evidence, and it costs nothing.

Place the button in `render_spreading_tab()` alongside the existing spread downloads, fed by the new optional `package=` parameter rather than by a session-key lookup inside the shared helper. Label it distinctly from the legacy `spread_to_xlsx_bytes` export so the difference between the two artifacts is obvious to someone clicking both, and have the button absent rather than broken when no package is supplied, so CRE's use of the same tab is unaffected.

Acceptance: the CI workbook downloads from a live run and opens without repair prompts in Excel. Cell notes, tier indicators and the Sources sheet are populated, checked by opening the file rather than by asserting bytes. Both layout files are visible in the pack assets view.

**Decided 2026-07-30: unify the two spread paths. Done — see `docs/status/status_JACI_CL_GOVERNED_LAYER_UI.md`'s 2026-07-30 follow-up section.**

There are two ways to produce a spread in this tab and only one populates `ci_spread_package`. Tab6's own "Run spreading (10-K → spread)" button calls `spread_filings()` and yields a plain `FinancialSpread`. The Acts tab's Run Act 1 and the Trace tab's Run spread phase call `run_cl_spread()` and populate the package, metrics and findings.

The consequence is wider than the download button. `spreader_template_trace`'s per-cell confidence and source, the review queue, the source-region view and the governed workbook all read `ci_spread_package`. A presenter clicking the most prominent button in the most obvious tab gets a spread with none of the governed layer attached, and nothing on screen says why.

**Do not unify inside `ui/shared.py`.** CRE calls the same helper and has no capability pipeline; its call site passes no package, metrics or findings. Breaking CRE to fix C&I would trade one problem for a worse one.

The shape is an optional `run_fn=` callback on `render_spreading_tab`, defaulting to the current `spread_filings` behaviour. The C&I demo page passes `_run_ci_spread_phase`; CRE passes nothing and is untouched. Same additive-optional-parameter convention as `truth=`, `package=` and `spreader_template_trace(package=...)`.

Before repointing, check what the reconciliation display actually reads off the spread — the 8/8 key-figure match and the per-statement line counts. If `_run_ci_spread_phase` does not already produce all of it, extend that function rather than keeping a second button. One run path is the goal; two buttons that differ in what they populate is the defect.

Keep `spread_filings` itself. It is the CRE path and is used by tests. Only the C&I button stops calling it directly.

Acceptance: one run button in the C&I spreading tab. After clicking it the 8/8 reconciliation still displays, the governed workbook button appears, and the Target Template shows per-cell confidence and source. The CRE spreading tab is unchanged, verified by opening it.

## Phase 2 - Exceptions and the review queue

`rank_for_review` ordering the findings, rendered as the reviewer's worklist: severity, the affected cell, why it ranked where it did, and whether it feeds a covenant.

The ranking rationale is the part worth showing. A sorted list looks like any sorted list; a list that says "ranked first because this cell feeds the leverage covenant and its confidence is 0.71" is the argument. Surface `covenant_feeding_keys` membership explicitly.

Alongside it, `exception_summary` as the per-spread credit-file summary, and `aggregate_status` as a single pass, pass-with-flags or blocked indicator near the top of the surface. The status is the one-glance answer to whether this spread is deliverable, and it currently has no visual presence at all.

Acceptance: the queue renders from the session package with no re-run, the ordering changes when profile weights change, and the exception summary matches the workbook's Exceptions sheet content.

## Phase 3 - Source region view

Clicking a spread cell shows its source region via `resolve_source_region`; a source region lists the cells it feeds via `reverse_lookup` and `cells_fed_by`.

Render the reverse direction too. It is half of FR-HIL-2, it is the half usually skipped, and it is the more impressive one to watch: selecting a region of a filing and seeing every downstream figure light up is the provenance claim made visible in one gesture.

Where a coordinate carries no bounding box, show the page and say so. `resolve_source_region` already returns an honest reason when it cannot resolve; render the reason rather than an empty panel.

Acceptance: every populated cell on the YETI and RB packages either shows a region or displays why not. Reverse lookup from a region returns the correct cell set.

## Phase 4 - Corrections and the approval loop

The hardest phase and the one to attempt only with time to spare.

Drive `spread_approval_engine` from Streamlit: run it, and when `run.status == "suspended"`, hold `run.suspension` in session state and render the `ApprovalRequest`'s flagged lines. Collect corrections through `make_correction`, requiring the rationale the object already requires, then resume with an `SmeDecision`.

The Streamlit-specific hazard, stated because it will otherwise be discovered the hard way: the script reruns on every widget interaction, so the suspension and any partially entered corrections must survive a rerun in session state. Do not rebuild the engine per rerun and do not resume on a stale suspension.

Show the re-propagation. After applying a correction, display which metrics and covenant tests changed. That is what Wave 3b Phase 2 built and it is invisible unless the before and after are next to each other.

Maker-checker roles read from the profile through `self_review_permitted`. If the demo profile permits self-review, say so on screen rather than silently letting one actor do all three steps.

Acceptance: a correction entered in the UI applies, re-validates, and visibly changes a covenant test result. A rerun mid-entry loses nothing.

## Phase 5 - Layered spread views

`build_effective_view` and `standardized_template_rows` rendered as selectable layers over one spread: reported, normalized, reclassified, underwritten. FR-MAP-7, and it is the surface where the reclassification engine's work becomes visible at all.

`project_effective_package` gives the reclassified projection. Showing reported beside reclassified on the balance sheet, with total assets unchanged and current assets moved, is the clearest available demonstration that as-reported is preserved rather than overwritten.

Acceptance: switching layers changes subtotals and leaves totals identical, visible on screen without a re-run.

## Out of scope

Provenance columns on the Target Template table (demo arc Phase 3). The live pipeline map (demo arc Phase 2). Trap fixtures, the three acts, and wiring the RB package into the demo as a loadable data source (demo arc Phases 4 and 5). Corrections as training signal (FR-HIL-5). Any change to the governed objects themselves; this plan renders what exists and adds no capability.

## Sequencing

Phase 1 first and it is small. Phase 2 is the highest-value screen for a reviewer audience and depends on nothing but the session package. Phase 3 is the most persuasive to watch. Phase 4 is the only phase with real technical risk and should not be started if the remaining time is tight, because a half-driven suspend and resume loop is worse in a demo than no correction UI at all. Phase 5 is independent of all of them.
