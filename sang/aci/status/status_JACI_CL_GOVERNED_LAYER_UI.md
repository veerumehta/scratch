# Status: Surfacing the Governed Layer (Wave 3 UI)

Author: Virendra Mehta · Updated 2026-07-30
Repo: jaci · Landed: dev `7b425b6` (v0.13.0)
Plan: docs/plans/plan_JACI_CL_GOVERNED_LAYER_UI.md

**Phases 0-1 of 5 landed** (Phase 0 added during execution, not in the original plan). Phases 2-5
(review queue, source region view, corrections/approval loop UI, layered spread views) not
started. This is a `status_` file, not a `done_` file, because the plan itself is incomplete.

## Two real gaps found in the plan's own text, both confirmed and fixed before building on them

1. The plan asserted three things were "already exported and importable" (`load_ci_workbook_layout`/
   `load_rb_workbook_layout` plus a longer list) having verified only the longer list. Checked
   directly: those two were not exported (existed in `workbook_layout.py` since Wave 3a but never
   added to the package `__init__`).
2. The plan said to place the workbook download button "where the existing spread download
   buttons are" (`render_spreading_tab`) without reading that function's signature — it takes a
   plain `FinancialSpread` from a scenario-supplied `session_key`, no `SpreadPackage` parameter at
   all, and is a cross-capability helper (used by more than just this scenario), so hardcoding a
   `ci_spread_package` session-state read inside it would have been a layering violation. Fixed
   with an additive optional `package=`/`metrics=`/`findings=` triple, matching
   `spreader_template_trace(spread, package=...)`'s existing convention — provenance now arrives
   as an optional argument on functions that still work without it, consistently.

## Phase 0 (added, not in the original plan) — session-state capture, and a real bug found by reading real output

`_run_ci_spread_phase()` only ever captured `_run.emitted.get("spread")`; `CL_SPREAD_PIPELINE` has
emitted `metrics` (`MetricResult[]`) and `validate` (`ValidationFinding[]`) since Wave 1. Fixed to
capture both into `st.session_state["ci_spread_metrics"]`/`["ci_spread_findings"]`.

Per this plan's own revised acceptance ("a human reads it"), ran the real pipeline against the
real YETI 10-K (`docs/LoanSamples/YETI/.../YETI FY 2025 SEC 10-K_1.3.2026.pdf`, via its staged
`.japes/*.md`) outside Streamlit and read the actual `ValidationFinding` output by eye before
building the review queue or the workbook button on top of it.

**Found: 3 guaranteed-false `BLOCKING` findings on every run since Wave 1 landed.**
`detect_income_statement_cross_foot` deliberately excludes `interest_expense_income_net`/
`other_income_expense_net` from its subtraction chain (correct — their sign convention isn't
uniform across real filings) but then still checked the next subtotal
(`income_before_income_taxes`) against `operating_income - 0`, as if those excluded, genuinely
signed components didn't exist. Misfires on any filing with real interest expense — nearly all of
them. No existing test fixture (including RB's) built an income statement complete enough to
exercise the bug; RB's fixture stops at operating income.

Fixed: a subtotal reached after an unchecked (no-parent) line is now skipped entirely rather than
checked against an incomplete `pending` sum. Verified on the real pipeline: **YETI now reports 0
findings** (was 3) — the package is genuinely clean, not accidentally clean. Two regression tests
added (`test_validation.py`): the real shape (interest expense making pretax income lower than
operating income) no longer misfires; a genuine break earlier in the same chain (gross_profit)
still gets caught.

## Phase 1 — governed workbook download (CI-only)

- `load_ci_workbook_layout`/`load_rb_workbook_layout` exported from `jaci.capabilities.
  commercial_lending`'s `__init__`/`__all__`.
- `render_spreading_tab` (`ui/shared.py`) gains optional `package`/`metrics`/`findings` params
  (default `None`, every existing caller unaffected) and, when `package` is given, a second
  download button building a `GovernedWorkbook` from the session `SpreadPackage`/`MetricResult`s/
  `ValidationFinding`s via `load_ci_workbook_layout()` — labeled and captioned distinctly from the
  legacy `spread_to_xlsx_bytes` button above it.
- `demo_page.py`'s "📄 10-K Spreading" tab call site now passes `package=st.session_state.get(
  "ci_spread_package")` (and `metrics=`/`findings=` the same way) — populated whenever the Acts
  tab's "Run Act 1" or the Trace tab's "Run spread phase" button has already run in this session,
  since both write to the same `ci_spread_result`/`ci_spread_package` session keys this tab reads.
- **CI-only, as directed.** No RB button: there is no RB package anywhere in this demo (no file, no
  loading path, no button) for one to be built against — `load_rb_workbook_layout` is exported and
  tested (Wave 3a) but has nothing live to drive in this UI.

## Acceptance criteria — verified

- Phase 0: `metrics`/`findings` captured in session state; the real YETI finding set was read by a
  human before any surface was built on it, per the plan's own revised (Desktop) acceptance.
- Phase 1: verified end-to-end against the real pipeline (not a synthetic fixture) — built a
  `GovernedWorkbook` from the real YETI `SpreadPackage`/`MetricResult`s/`ValidationFinding`s,
  wrote it to `/tmp/yeti_governed_workbook.xlsx`, reloaded it with `openpyxl` and confirmed: all 13
  expected sheets present, the Income Statement's live-formula cell references Inputs correctly
  and carries a governance comment, the Sources and Provenance sheet's title is intact (not
  clobbered), and the Exceptions sheet is correctly empty (matching the real, now-genuinely-clean
  YETI finding set). **Not verified**: actually opening the file in Excel, or clicking the button
  in a running Streamlit session — this was a headless investigation with no browser available;
  said explicitly rather than claimed.
- Full jaci suite: 755 passed (was 752 before this work), 8 skipped, 5 xfailed; the same 6
  pre-existing, unrelated failures present before this work are unchanged.

## Follow-up (2026-07-30): the "two run paths" gap, found live and closed

A live Streamlit session surfaced exactly the risk the "Not verified" line above flagged: with
only the plain `spread_filings` run button clicked (8/8 reconciliation displayed), the governed
workbook button did not appear. Root cause was not a wiring omission at the call site (that part
was already correct — `package=`/`metrics=`/`findings=` were being read from session state) but
that tab6's own run button never called the pipeline that populates those keys in the first
place. Two independent runners were writing into the same `ci_spread_result` session key: the
plain `spread_filings()` (tab6's own button) and the governed `run_cl_spread()` via
`_run_ci_spread_phase()` (Acts tab "Run Act 1" / Trace tab "Run spread phase"), and only the
second populated `ci_spread_package`/`_metrics`/`_findings`.

Closed by unifying the two paths rather than leaving the presenter to know which tab to click
first:
- `render_spreading_tab` (`ui/shared.py`) gains optional `run_fn`/`run_fn_choice` params. When the
  radio selection equals `run_fn_choice`, the run button calls `run_fn()` instead of
  `spread_filings` — `run_fn` is responsible for writing `session_key` (and any governed
  `package`/`metrics`/`findings`) itself, exactly as `_run_ci_spread_phase` already does for its
  other two callers. Any other selection, or `run_fn=None`, keeps the previous `spread_filings`
  behavior unchanged — CRE's call site passes neither and is untouched.
- `demo_page.py`'s tab6 now passes `run_fn=lambda: _run_ci_spread_phase(_golden)` bound to the
  "One filing" radio choice only. The "Three filings" (multi-year merge) choice has no governed-
  pipeline equivalent — `run_cl_spread`/`CLSpreadContext` take one document, and there is no
  `SpreadPackage` merge across filings the way `merge_spreads` merges plain `FinancialSpread`s —
  so it deliberately keeps using `spread_filings`; the governed button stays absent for that
  choice, same as it already is for CRE.

Also found and fixed while investigating, ahead of Phase 2 needing them clean:
- `docintel.py`'s `convert_document` only checked a co-located `<stem>.md`, not the `.japes/`
  artifact-cache subdirectory `DocumentAgent.process_dir` actually writes/reuses its conversions
  under — the real cause of a live "reads as scanned/unreadable" failure on the YETI FY2025 10-K,
  which had a valid staged `.japes/*.md` the stub never looked at. Fixed: `.japes/<stem>.md` (when
  that directory exists) now takes priority over a co-located `<stem>.md`.
- The cross-foot fix (Phase 0, above) had never been run against RB's *actual* reported
  income-statement shape (real signed `interest_expense_income_net`/`gain_loss_on_sale_of_assets`/
  `other_income_expense_net`/`rent_expense` lines) — not by `test_rb_reference_case.py`'s own exit
  criterion, which never calls this detector, and not by either existing fixture in
  `test_validation.py` (`_rb_pkg` stops at `operating_income`; `_pretax_income_spread` omits
  `rent_expense`/`gain_loss_on_sale_of_assets`). Verified directly against RB's real FY2019–FY2022
  figures: zero false positives. Added as a permanent regression test.

Verified: real end-to-end run (`run_cl_spread` on the real YETI 10-K via its `.japes/` cache) →
28 metrics, 0 findings → `GovernedWorkbook.to_bytes()` → 13 sheets, reloads clean with `openpyxl`.
Full jaci suite: 756 passed (was 753), 8 skipped, 5 xfailed; same 5 pre-existing, unrelated
failures (`test_anthropic_reasoner`/`test_threat_intel_handler`, an unrelated signature drift)
unchanged. **Not verified**: clicking the button in a live browser session — still no browser
available; said explicitly rather than claimed.

## Deliberately not done (stated, not silently dropped)

- Phases 2-5 (review queue, source region view, corrections/approval-loop UI, layered spread
  views) — out of scope for this pass per explicit direction ("Go ahead with Phase 0 and Phase 1,
  CI-only").
- An RB package/loading path in the demo, which Phase 1's RB button would need — not built; a
  separate, larger lift than this pass.
- A `SpreadPackage` merge across multiple filings — the "Three filings" choice still has no
  governed-pipeline equivalent; a real, separate lift, not attempted here.
- Any Streamlit browser verification — headless session, stated explicitly per each item above
  rather than claimed.
