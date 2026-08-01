# Plan: Governed Workbook Export

Author: Virendra Mehta · 2026-07-29
Repo: japes (reporter) with a jaci pack asset in Phase 2 · Baselines: japes 2.2.0, jaci 0.9.8
Depends on: Wave 1 (landed). Uses `SpreadPackage`, `MetricResult`, `ValidationFinding`, `SourceResolution`, `NormalizationAdjustment` and the severity model.

Driver: Wave 3a of `plan_JACI_CL_PRD_COMPLETION.md`. FR-OUT is the lowest-coverage P0 area at 17%. Appendix G specifies the deliverable precisely and nothing implements it. This is also what turns the spread from something demonstrable in a tab into something a credit file can hold.

Covers FR-OUT-1, FR-OUT-2, FR-OUT-3.

## Grounding notes (verified 2026-07-29 against dev)

- **Two near-duplicate exporters exist.** `jazzx_sdk/finance/excel.py` and `jaci/capabilities/commercial_lending/excel.py` share `_write_cover`, `_write_statement_sheet` and `_write_trends` almost verbatim, down to the `1F4E78` header fill and the `#,##0;(#,##0)` format. The jaci copy adds `_write_template_sheet` and its docstring already names itself "a candidate to promote to a JAPES skill." This is the fifth instance of the duplication pattern we spent Wave 1 collapsing; do not make it a sixth.
- **Both build from `FinancialSpread`**, which carries values and nothing else. No confidence, no source coordinate, no provenance. FR-OUT-2's cell notes are therefore not an extension of either exporter; they need a different input.
- The existing `_write_trends` writes live `=IFERROR((cur-prev)/prev,"")` formulas referencing another sheet by name and row. So the live-formula precedent FR-OUT-1 asks for already exists and works.
- `openpyxl` is imported lazily in the japes copy and eagerly in the jaci copy. Keep it lazy so importing `jazzx_sdk.finance` stays dependency-free.
- Appendix G names nine worksheets: Income Statement, Balance Sheet, Cash Flow, Ratios and Metrics, Inputs, Exceptions and Inconsistencies, Commentary and Notes, Assumptions, Sources and Provenance.
- Appendix G's on-cell spec: a note per delivered value carrying confidence tier plus source plus provenance; a subtle traffic-light tier indicator; assumptions and overrides styled distinctly from reported figures; values hyperlinking to the Sources tab.
- `apply_normalization` already produces a derivation decomposing a normalized figure into base plus named add-backs. That decomposition *is* FR-OUT-3's reported / adjustment / adjusted triple; it does not need recomputing.

## Phase 1 - The reporter, built on governed inputs

New `jazzx_sdk/finance/workbook.py`. A `GovernedWorkbook` reporter taking a `SpreadPackage`, its `MetricResult`s, its `ValidationFinding`s, its `SourceResolution`s and a layout, and emitting bytes.

Sheet content is driven by the layout, not hardcoded. The reporter knows how to render a sheet of rows against periods with cell notes and tier indicators; it does not know that a C&I spread has an Income Statement tab. That distinction is what makes it a platform reporter rather than a C&I exporter living in the wrong repo.

Retire the duplication as part of this phase, not after it. `jaci/capabilities/commercial_lending/excel.py` becomes a thin call into the SDK, and its `_write_template_sheet` moves behind the layout. Do not leave two exporters plus a third governed one.

Every cell carries: value, confidence tier, source document and page or region, provenance status. Where any of those is absent, the cell is not written silently. An unsupported or below-floor value renders as blank with an Exceptions entry, per the design tenet the rest of the stack already holds.

Acceptance: the reporter emits from `SpreadPackage` alone. A cell whose line item has no source coordinate produces an Exceptions row rather than a bare number. `spread_to_xlsx_bytes` in both existing modules produces byte-identical output to before, or is deleted with its callers moved.

## Phase 2 - Layout as a pack asset

New `config/packs/ci-spread-core/workbook_layout.yaml`, declaring the nine Appendix G sheets: sheet id, display title, source (which canonical object populates it), row bindings to canonical keys or metric ids, whether values are static or live formulas, and column set.

The Inputs sheet is the normalized as-reported data. The spread sheets reference Inputs by live formula rather than repeating values, which is what FR-OUT-1's "live, inspectable formulas" means and what lets a customer re-drive the workbook. The existing Trends sheet is the pattern to follow.

Common-size percentages and YoY growth are live formulas, not computed values. They are presentation arithmetic and belong in the sheet.

Acceptance: the layout loads, every row binding resolves against the chart of accounts or the metric catalog, and a second layout (`workbook_layout_rb.yaml`) produces RB's sheet set from the same reporter with no code change.

## Phase 3 - Notes, tiers and styling

The on-cell treatment, which is the substance of FR-OUT-2 and the reason the face can stay clean.

- Cell note per delivered value: confidence tier, source document and page, provenance status. Sourced from `ProvenanceEntry` and `Confidence`, not reconstructed.
- Traffic-light tier indicator, subtle. Conditional formatting or a small marker glyph, not a filled cell; a red-filled spread is unreadable and Appendix G says subtle.
- Assumptions and overrides styled distinctly from reported figures. This is a hard requirement rather than a nicety: FR-CUS-6 says an assumption must never be mistaken for a reported figure, and the styling is where that promise is kept in the deliverable. Drive it from `ProvenanceType`, so the Wave 1b values (`ADJUSTMENT_CANDIDATE`, `APPROVED_ADJUSTMENT`, `POLICY_ADJUSTED`) each get a treatment rather than collapsing into "not reported."
- Every value hyperlinks to its row on the Sources and Provenance sheet.

Acceptance: a spread containing a reported value, a policy-adjusted value, an approved add-back and an assumption renders four visually distinct treatments, asserted by reading back cell styles. Every delivered value has a note and a working hyperlink.

## Phase 4 - Exceptions and the Moody's presentation

**Exceptions and Inconsistencies sheet.** Every finding: description, severity, affected cell as a hyperlink into the spread sheet, source, suggested action. This sheet is also FR-HIL-4's per-spread exception summary for the credit file, so agree its shape with `plan_JACI_CL_REVIEW_SURFACE.md` rather than building two.

**Reported / adjustment / adjusted columns.** FR-OUT-3, matching the YETI strict spreads. Read the decomposition out of `apply_normalization`'s derivation; the adjustment column is labelled by the provenance of the adjustment that produced it. Do not recompute the arithmetic in the sheet, because a difference between the sheet's arithmetic and the engine's is a defect that will surface in front of a customer.

**Assumptions sheet.** Every assumption with value, basis and owner, per Appendix G. Sourced from assumption-bound inputs, which the DSL's `BindingKind.ASSUMPTION` already identifies.

Acceptance: every finding appears once with a hyperlink that resolves to the right cell. On the YETI package the adjusted column equals the reported column plus the adjustment column exactly, in `Decimal`, asserted against `MetricResult` rather than against the sheet.

## Out of scope

Borrowing-base and CRE outputs, appendix binders (FR-OUT-4, P1). API and LOS integration (FR-OUT-5, P1). Live refreshable portfolio views (FR-OUT-6, P2). Commentary sheet content, which is analyst input rather than generated; the sheet exists and is empty. Reading a customer workbook to derive a layout, which is template ingestion in Wave 4b and will emit into Phase 2's schema.

## Sequencing

Phase 1 is the reporter and the deduplication, and the deduplication should not be deferred. Phase 2 is authoring and can run alongside. Phase 3 is where FR-OUT-2 is actually satisfied and is the phase most likely to be under-built, because a workbook that looks right with no notes passes casual inspection. Phase 4 depends on the severity model from Wave 1c and on coordination with the review surface plan.
