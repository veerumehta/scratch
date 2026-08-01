# Done: Governed Workbook Reporter (FR-OUT-1/2/3)

Author: Virendra Mehta · Completed 2026-07-30
Repo: japes (+ jaci pack asset + loader + tests) · Landed: japes dev `08319dc` (unpushed, no
version bump, stays 2.2.2)
Plan: docs/plans/plan_JAPES_2_3_0_GOVERNED_WORKBOOK.md (superseded by this file)

All 4 phases landed. This is Wave 3a of jaci's `plan_JACI_CL_PRD_COMPLETION.md`. One correction to
the plan's own grounding, found before writing any code: two real bugs found and fixed while
building out Phase 3's hyperlink verification, not assumed away.

## Correction to the plan's own grounding

The plan names `SpreadPackage`, `MetricResult`, `ValidationFinding`, `NormalizationAdjustment` as
this reporter's inputs without noting they're jaci-only classes — only `SourceResolution` is
japes-native. Since japes cannot depend on jaci, the reporter's inputs are `typing.Protocol`
structural types (`GovernedPackage`, `GovernedLineItem`, `GovernedMetric`, `GovernedFinding`,
`GovernedAdjustment`, etc.) that jaci's existing pydantic models satisfy without any jaci-side
change — proven with local duck-typed stand-ins in japes' own test suite (no jaci import) and
separately against real jaci `SpreadPackage` objects in jaci's own tests.

## What shipped

- `jazzx_sdk/finance/workbook.py` (new): `GovernedWorkbook` — builds a workbook sheet-by-sheet
  from a `WorkbookLayout`; cell-level `Comment` (confidence tier + score, source locator,
  provenance type), a tier-color left border, a distinct fill+italic treatment for non-`sourced`
  provenance (`ADJUSTMENT_CANDIDATE`/`APPROVED_ADJUSTMENT`/`POLICY_ADJUSTED`/`ASSUMPTION`/
  `REVIEWER_ENTERED`), and a hyperlink to a deduplicated row on a Sources and Provenance sheet
  (FR-OUT-2). A line item with no provenance at all renders blank plus an Exceptions-sheet entry,
  distinct from a legitimately valueless `ASSUMPTION`.
- FR-OUT-1: a non-live "Inputs" statement sheet holds literal governed values; a `live_formula=True`
  display sheet of the same rows references Inputs by formula (`='Inputs'!B5`) rather than
  repeating them, while still carrying the same cell note.
- FR-OUT-3: "EBITDA Bridge" (`SheetSource.NORMALIZATION`) reads reported/adjustment straight out of
  a `MetricResult.derivation.inputs` (first entry = base, rest = adjustments); "Adjusted" is a live
  `=B{row}+C{row}` formula, so the sheet's own arithmetic can never diverge from the engine's.
- `WorkbookLayout`/`WorkbookSheet`/`RowBinding`/`SheetSource`, `load_workbook_layout` (generic,
  path-agnostic), `default_layout` (derived from the package's own statement types/keys when no
  pack-authored layout exists).
- jaci: `config/packs/ci-spread-core/workbook_layout.yaml` (the primary layout, every statement's
  full chart-of-accounts row set + the 16-metric catalog + an EBITDA Bridge) and
  `workbook_layout_rb.yaml` (RB's smaller, differently-shaped sheet set — no Inputs/live-formula
  split, no EBITDA Bridge — proving the reporter is genuinely layout-driven with no code change).
  `capabilities/commercial_lending/workbook_layout.py`: `load_ci_workbook_layout`/
  `load_rb_workbook_layout`, validating every row against the chart of accounts (scoped to the
  sheet's own statement type) or the metric catalog at load time.
- `excel.py` dedup: jaci's near-duplicate cover/statement/trends writers now import and call
  japes' own (the fifth instance of the pattern Wave 1 already collapsed elsewhere); kept only
  `_write_template_sheet` (a genuinely C&I-specific tab) local.

## Two real bugs found and fixed, not assumed away

1. A plain string hyperlink assignment (`cell.hyperlink = "#'Sheet'!A1"`) serializes to OOXML as an
   **external** relationship (`TargetMode="External"`, an `r:id` pointing at a relationship whose
   target happens to start with `#`) rather than an in-workbook jump — confirmed by inspecting the
   raw `.xlsx` XML. Some readers may refuse to navigate it since it isn't a real URL. Fixed at all
   three hyperlink sites (`_write_governed_cell`, both findings-sheet cell references) to use
   `openpyxl.worksheet.hyperlink.Hyperlink(location=..., target=None)`, verified via the same raw-XML
   inspection to produce no external relationship at all.
2. `_write_sources_sheet` wrote its own "Sources and Provenance" title and its header row at the
   same cell (`A1`), so the header silently clobbered the title on every real workbook. Fixed by
   giving the sheet the same title-row-then-header-row shape every other sheet in this reporter
   already has (`_SOURCES_HEADER_ROW = 4`), with the hyperlink-target row math (`_sources_row`)
   defined once so the writer and the citing cells can't drift apart again.

Found while building Phase 3's "every delivered value has a working hyperlink" test — not by
inspection alone.

## Acceptance criteria — verified

- Reporter builds correctly from the Protocol shape alone (no jaci import) — japes' own test
  suite, local duck-typed stand-ins.
- Both jaci layouts (`workbook_layout.yaml`, `workbook_layout_rb.yaml`) load, every row resolves
  against the chart of accounts or metric catalog, and both render through the same reporter with
  no code change (`jaci/tests/unit/test_workbook_layout.py`).
- All four visually distinct cell treatments (reported, policy-adjusted, approved add-back,
  assumption) verified together against a real jaci `SpreadPackage`; every delivered value in a
  real multi-sheet workbook carries a note and a working (internal, not external-relationship)
  hyperlink (`jaci/tests/unit/test_governed_workbook.py`).
- A real `MetricResult` via `apply_normalization` + real `NormalizationAdjustment`s (computed +
  policy-assumption add-backs) on a YETI-shaped package: the sheet's Reported + Adjustment columns
  sum to exactly the engine's own `MetricResult.value.decimal`, asserted against the `MetricResult`
  itself, never independently recomputed. Exceptions sheet flags a real missing-provenance line;
  Assumptions sheet carries both a real `ASSUMPTION`-provenance line item and a real
  `ASSUMPTION`-provenance adjustment with its rationale
  (`jaci/tests/unit/test_governed_workbook_normalization.py`).
- Full japes suite green (1932 passed, 3 skipped); full jaci suite green modulo 6 pre-existing,
  unrelated failures (AML/KYC reasoner signature mismatch, threat-intel handler, anthropic token
  tracking — none touch `commercial_lending`, confirmed by diff scope) — no regressions from this
  work.

## Deliberately deferred (stated, not silently dropped)

- Common-size %/YoY-growth as additional live formulas (mentioned in the plan's descriptive prose,
  not in its literal Phase 2 acceptance) — the existing Ratios and Metrics sheet already carries
  `gross_margin_pct`/`revenue_growth_pct`/etc.
- Migrating the Streamlit download buttons (`jaci/.../ui/shared.py`) off the old
  `FinancialSpread`-only exporter onto `GovernedWorkbook` — needs the UI to gather
  `SpreadPackage`+`MetricResult`s+`ValidationFinding`s+a layout, a separate integration task beyond
  this plan's stated acceptance.
- Coordinating this reporter's Exceptions-sheet shape with `plan_JACI_CL_REVIEW_SURFACE.md`'s
  (Wave 3b) per-spread exception summary as one shared artifact — Wave 3b hasn't started yet; noted
  for whoever picks it up.
