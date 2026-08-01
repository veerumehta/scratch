# Done: Governed Workbook Layouts (FR-OUT-1/2/3)

Author: Virendra Mehta · Completed 2026-07-30
Repo: jaci (+ japes reporter) · Landed: jaci dev `87e65f0` (v0.11.0), japes dev `08319dc`
(unpushed, japes stays 2.2.2)
Plan: docs/plans/plan_JAPES_2_3_0_GOVERNED_WORKBOOK.md (superseded by this file)

Wave 3a of `plan_JACI_CL_PRD_COMPLETION.md`. All 4 phases landed. Full detail (the reporter
itself, the two real bugs found and fixed, the Protocol-based architectural correction) is in
japes' own `docs/status/done_JAPES_2_3_0_GOVERNED_WORKBOOK.md` — this file covers the jaci-side
pack assets and their tests.

## What shipped

- `config/packs/ci-spread-core/workbook_layout.yaml`: the primary governed-workbook layout —
  every statement's full chart-of-accounts row set (income statement 18, balance sheet 38, cash
  flow 28 lines), the 16-metric catalog, an EBITDA Bridge (FR-OUT-3, targeting `ebitda` — the
  add-back library's own default normalization target), and an Inputs + live-formula display
  sheet pair per statement (FR-OUT-1).
- `config/packs/ci-spread-core/workbook_layout_rb.yaml`: RB's own smaller, differently-shaped
  sheet set (10 income-statement rows, 2 cash-flow rows, 3 summary-balance-sheet rows, 4 metrics)
  transcribed from `spread_template_rb.yaml`'s own bound rows — deliberately no Inputs/live-formula
  split and no EBITDA Bridge, to prove the reporter is genuinely layout-driven rather than just
  accepting a trimmed copy of the same shape.
- `capabilities/commercial_lending/workbook_layout.py`: `load_ci_workbook_layout`/
  `load_rb_workbook_layout`, mirroring `load_rb_template`/`load_addback_library`'s own
  default-path-plus-validate convention — every STATEMENT row's key must resolve against the
  chart of accounts *for that sheet's own statement type* (not just any statement), every METRICS
  row against the metric catalog, fail loud at load time rather than silently rendering a blank
  cell for an unresolvable row.
- `excel.py`: cover/statement/trends sheets now delegate to `jazzx_sdk.finance.excel`'s own
  writers instead of a near-duplicate reimplementation (the fifth instance of a pattern Wave 1
  already collapsed elsewhere); `_write_template_sheet` (a genuinely C&I-specific tab) stays
  local. Byte-for-byte content-equivalent to the pre-refactor output (verified via a key-aligned
  pickled-snapshot diff), except one caption line jaci's copy had that japes' own copy was
  missing — fixed upstream in japes rather than kept as a jaci-side patch.
- 21 new tests across 4 files: `test_excel_export.py` (delegation), `test_workbook_layout.py`
  (both layouts load/validate/render, plus load-time rejection of a wrong-statement key and an
  unknown metric id), `test_governed_workbook.py` (all four provenance-driven cell treatments
  together on a real `SpreadPackage`, every delivered value has a note and a working internal
  hyperlink), `test_governed_workbook_normalization.py` (a real `MetricResult` via
  `apply_normalization` + real computed and assumption-provenance `NormalizationAdjustment`s,
  Exceptions and Assumptions sheets against real data).

## Acceptance criteria — verified

- Both layouts load and every row binding resolves against the chart of accounts or metric
  catalog; a bad layout (wrong-statement key, unknown metric) is rejected at load time with a
  clear error, not a silently blank cell.
- `workbook_layout_rb.yaml` produces RB's own sheet set from the same `GovernedWorkbook` reporter
  with zero reporter code changes.
- On a YETI-shaped package: the EBITDA Bridge's Reported + Adjustment columns sum to exactly
  `apply_normalization`'s own `MetricResult.value.decimal` (280 = 250 base + 20 computed add-back +
  10 assumption add-back) — asserted against the `MetricResult`, never independently recomputed.
- Full jaci suite: 721 passed (was 715 before Wave 3a's own tests), 8 skipped, 5 xfailed; the 6
  failures present both before and after this work (AML/KYC reasoner signature mismatch,
  threat-intel handler, anthropic token tracking) are confirmed unrelated — none touch
  `commercial_lending`, none appear in this session's diff. Full japes suite: 1932 passed, 3
  skipped, no regressions.
- `docs/plans/PRD_COVERAGE_REGISTER.md` updated: OUT area 17% → 100% P0 coverage, FR-OUT-1/2/3
  struck through in the P0 gap list with the UI-wiring caveat noted (below).

## Deliberately deferred (stated, not silently dropped)

- Common-size %/YoY-growth as additional live formulas — not in Phase 2's literal acceptance; the
  Ratios and Metrics sheet already carries the relevant `*_pct` metrics.
- Migrating the Streamlit download buttons (`ui/shared.py`) off the old `FinancialSpread`-only
  exporter onto `GovernedWorkbook` — needs the UI to assemble a `SpreadPackage` +
  `MetricResult`s + `ValidationFinding`s + a layout at request time; a separate integration task.
- Coordinating this reporter's Exceptions-sheet shape with `plan_JACI_CL_REVIEW_SURFACE.md`'s
  (Wave 3b, not yet started) per-spread exception summary as one shared artifact.
