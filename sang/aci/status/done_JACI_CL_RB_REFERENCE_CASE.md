# Done: Regional Bank Reference Case and MVP Exit Criterion

Author: Virendra Mehta · Completed 2026-07-29 (balance sheet extension: same day, second pass)
Repo: jaci · Landed: dev `f8f64b1` (Phases 1-5), balance-sheet/leverage extension (unpushed, no
version bump)
Plan: docs/plans/plan_JACI_CL_RB_REFERENCE_CASE.md (superseded by this file)

All 5 phases landed. Wave 1e of `plan_JACI_CL_PRD_COMPLETION.md` — the acceptance harness for
Wave 1, executed last as the plan itself specifies. **Wave 1 (1a–1e) is now complete.** The Phase
5 gate test (`test_rb_mvp_exit_criterion`) passes, confirmed by a live, current run
(`tests/unit/test_rb_reference_case.py`), matching the plan's own framing: "expected to fail until
Wave 1 completes... it is the wave's definition of done."

**Revision history on this claim, in order — read this before quoting anything below:**
1. Initial landing: only 11 income-statement canonical keys existed for RB. A desktop-app review
   correctly caught that this meant the earnings half of the exit criterion (LTM income statement,
   CIT EBITDA, EBITDAR) was proven on real numbers while the leverage/coverage/liquidity half
   (needs CPLTD, total debt, current assets/liabilities) was implemented and tested only on
   synthetic fixtures, never on RB.
2. Same day, second pass: **the user pointed out this didn't need its own plan** — pull the 9/30/22
   and 9/30/23 balance sheet pages to canonical keys, extend the fixture with a balance-sheet
   block, and let the previously-synthetic-only checks run on real numbers. Done directly, no plan
   doc, per that instruction. **This closes the gap**: RB now has real balance-sheet figures for
   all six periods (four annual, from the reference workbook's own "Balance Sheet-Input" sheet;
   two interim, extracted directly from the raw 9-month PDFs), and `detect_balance_control`,
   `current_ratio`, `funded_debt`/`leverage_x`, and `ebitdar`/`fixed_charge_coverage_ratio` all now
   compute on real RB numbers for the first time. Doing this extraction also surfaced and corrected
   a real error in the equity-rollforward finding below (found by reading one more source document
   than the first pass had) — the review process catching real things, twice in a row, is the
   point of doing it this way rather than declaring victory after the first green run.
3. Same day, third pass: the user caught `depreciation_and_amortization` disagreeing by 1 unit
   between `_IS_KEYS` (2171) and `_CF_KEYS` (2172) for FY2022 and asked which it was — a real
   cross-statement inconsistency (a finding) or a transcription slip. Checked directly: "Profit or
   loss-Input"!L11 (income statement) and "Cash Flows"!L10 (cash flow) both report the identical
   $2,171,585 — no real inconsistency. The 2171/2172 split was this fixture's own artifact (two
   independent roundings of one number); standardized on 2171 to match the rest of the fixture's
   convention (the reference workbook's own displayed value). Third real catch from cross-checking
   in a row.

The Regional Bank package (borrower: C-DIVE, LLC) already existed at
`docs/LoanSamples/Regional Bank/` — 5 real CPA review/audit/compilation PDFs, a credit-app docx,
and the analyst's own working spread ("Output Cleaned.xlsx"). This was not synthesized; every
figure below was read directly from those documents. `docs/LoanSamples` is entirely gitignored
(same as the existing YETI/MAA samples), so the provenance file lives there uncommitted — only the
code is in git.

## What shipped

- `docs/LoanSamples/Regional Bank/PROVENANCE.yaml` (uncommitted, gitignored dir): per-document
  traceability (which figure came from which source and assurance level), not a real-vs-synthetic
  attestation — the plan's literal Phase 1 wording asked for the latter; the user redirected
  mid-phase to the former ("why does it matter whether it's real or synthetic — we just want to
  show provenance to match info to source"), and the file reflects that correction.
- `config/packs/ci-spread-core/spread_template_rb.yaml` / `rb_template.py`: the reference spread's
  own "First Citizens Format" tab transcribed row for row (36 rows). 21 bind to a chart-of-accounts
  key or metric id; 15 are explicitly unbound with a stated reason — margin metrics not yet
  authored for several house definitions, several rows needing the add-back/normalization layer
  composed at render time rather than a static DSL formula, and combined balance-sheet aggregates
  with no single matching canonical key. Deliberately not wired into `template.py`'s YETI-shaped
  render pipeline, which doesn't compose the add-back layer today.
- `tests/unit/test_rb_reference_case.py`: six real `SourceStatement`s (Phase 3) resolved through
  Wave 1a's `resolve_sources`/`construct_ltm_from_sources` reproduce the reference workbook's own
  LTM Sep-2023 income-statement column *exactly*, not approximately. The sign-error trap is
  asserted algebraically (the workbook's own note describes a different formula than the one its
  cell actually computes; the SDK's own output is shown to match the cell, not the note). The
  compilation period's missing cash-flow statement is asserted to refuse, not silently skip.
- **Balance-sheet extension (same day, second pass)**: real balance-sheet `SourceStatement`s for
  all six periods (nine canonical keys each — the top-level totals/subtotals actually needed for
  balance control, current ratio, and funded debt; not a full granular reconstruction of every
  AR/inventory/AP/accrued line, which stays out of scope). The four annual ones come from the
  reference workbook's own "Balance Sheet-Input" sheet; the two interim ones (9/30/22, 9/30/23)
  are read directly from the raw compilation and company-prepared PDFs, since the reference
  workbook itself only carries summary aggregates for those two periods. `construct_ltm_from_
  sources` now also constructs the LTM *balance sheet* (FR-PER-4: stock lines take the latest
  period-end balance, verified to equal CY9-23's own real balance sheet exactly). Cash-flow
  `SourceStatement`s for the four annual periods too (D&A, capital contributions, distributions,
  two `change_in_*` lines), confirming — by reading both interim PDFs directly — that *neither*
  9-month interim includes a cash-flow statement at all (not just the compilation, which
  PROVENANCE.yaml already flagged; the company-prepared 9/30/23 stub turns out to have none
  either).

## The three exit-criterion findings + the reference workbook's own two discrepancies (Phase 4)

- **Bad-debt inconsistency**: real figures from the source PDFs — bad debt expense $509,431
  (FY2020) / $380,492 (FY2021) / $3,662,933 (FY2022) / $19,302 (FY2023), present and non-trivial
  every year (**note**: the FY2020/FY2021 values were transposed in an earlier pass — the
  "2020 and 2021.pdf" comparative table presents the *current* year, 2021, in the first column
  and 2020 second; verified by cross-footing the table's own Total Cost of Revenues against
  Depreciation against `First Citizens Format`'s COGS figures, which only reconcile with this
  ordering). The reference spread's own "Adjustments" row adds it back only in FY2022. This
  finding runs on RB's real figures, not a synthetic fixture — the only one of the three findings
  that does (the other two are amounts from a footnote, not period-series data, so "real vs.
  synthetic" doesn't distinguish them the same way). Flagged by Wave 1b's
  `detect_cross_period_addback_inconsistency`.
- **Unrecorded tax obligation**: the real $573,000 figure, verbatim from "2022 and 2023.pdf" note
  24 ("does not contain a provision for taxes due, estimated to be $573,000"). Flagged by Wave 1c's
  `detect_undisclosed_obligations`.
- **Relief refund**: the real $2,331,124 ERC refund (same note), tagged via the existing
  `relief_and_one_time_income` add-back key (Wave 1b) as a candidate — excluded from an official/
  covenant-bound metric until an analyst promotes it (FR-ADJ-7).
- **Cash-tie discrepancy**: real and exact — the reference workbook's own Cash Flows-computed
  ending cash differs from its Balance Sheet-reported cash by $1–2 in three of five years (e.g.
  FY2019: $2,501,066 vs. $2,501,064, both real figures, `Balance Sheet-Input!F8` /
  `Cash Flows!F41`). Flagged by Wave 1c's `detect_cash_flow_tie`.
- **"Balance-control discrepancy"** — **the PRD's own FR-VAL-1 text says this never existed**:
  *"the RB spread carries a balance-control = 0 row."* Reading the actual documents confirms it
  directly: every one of the six real balance sheets ties to the dollar (e.g. 9/30/23:
  TOTAL ASSETS $78,889,888.56 = TOTAL LIABILITIES & EQUITY $78,889,888.56, both read straight off
  the source PDF). `detect_balance_control` runs against all six real periods and is silent on
  every one (`test_balance_control_ties_exactly_on_every_real_rb_period`) — this is the correct,
  provable outcome, not a gap. **The original plan's own grounding notes were wrong to ask for a
  balance-control discrepancy at all**, likely conflating it with the cash-tie gap above (which the
  PRD does name for RB).
  - A related but separate finding was reported here in an earlier pass: a $195,585 FY2023
    equity-roll-forward gap. Reading the audited statements' own "Statement of Changes in Members'
    Equity" (a document not fully read in that earlier pass) shows this was **not a genuine
    inconsistency in the source financial statements** — they report a $195,585 capital
    contribution explicitly, and with it the roll-forward ties to the dollar
    (`test_equity_rollforward_ties_exactly_against_the_audited_statement_of_changes_in_equity`).
    The $195,585 gap is real, but it's an artifact of one specific spreadsheet tab in the analyst's
    own working file (`Output Cleaned.xlsx`'s "Balance Sheet-Input", whose "Distributions" row is a
    back-solved plug with no separate contributions row) — not a defect in the underlying audited
    financials. Both are now tested explicitly: the complete-data case ties, and a fixture built
    from the incomplete spreadsheet-tab data reproduces the same $195,585 gap the plug produces
    (`test_equity_rollforward_flags_a_false_gap_when_the_analysts_own_spreadsheet_omits_
    contributions`) — a real demonstration of FR-VAL-4's value (an incomplete input produces a
    detectable, not silent, gap), correctly attributed to its actual source this time.

## One real correction to the plan's own grounding notes

"~$11.4MM of related-party receivables in 2020" is wrong — the real figure
(`Balance Sheet-Input!N28` = $11,378,858) is in **2023**; 2020's actual figure is $3,053,249.
Found by reading the actual reference workbook rather than trusting the plan's own prose.

## What's now proven on real numbers (updated after the balance-sheet extension)

- **Income statement side (Phase 1-5 landing)**: LTM Sep-2023 (all 11 lines, exact match); CIT
  EBITDA (gross profit − SG&A − rent).
- **Balance-sheet side (same-day extension)**: balance control ties exactly on all six real
  periods; the LTM balance sheet correctly takes CY9-23's own real balance (FR-PER-4); current
  ratio; funded debt / leverage (`funded_debt`/`leverage_x`, using real CPLTD — now available for
  both interim periods, extracted directly from the raw PDFs); EBITDAR and fixed-charge coverage
  (`ebitdar`/`fixed_charge_coverage_ratio`, jaci's own textbook-EBITDA lineage). None of this was
  provable before the extension — `current_maturities_of_long_term_debt` didn't exist as an RB
  canonical key for either interim period until the raw PDFs were read directly.

## Declared, not silently missing — what's still genuinely open

- **Full granular balance-sheet reconstruction** (individual AR/prepaid/AP/accrued lines, not just
  the nine top-level totals/subtotals used above) remains out of scope. This means
  `detect_hardcoded_plugs`-style cross-footing of RB's own balance sheet (do the components sum to
  the reported subtotal) hasn't been exercised on real RB figures — only the top-level totals
  themselves (which are taken as given, real, reported numbers, not derived from components in
  this fixture) have been checked.
- **EBITDAR/CIT FCC reproduction against the reference workbook's own figures**: jaci's `ebitdar`/
  `fixed_charge_coverage_ratio` now compute on real RB numbers (above), but they still don't match
  the reference workbook's own differently-lineaged "Adj. EBITDAR"/"CIT FCC" rows (add-back-
  adjusted EBITDA, and a cash-flow-based FCC formula). Named as a real, separate gap in
  `spread_template_rb.yaml`'s own unbound rows, not reattempted as a new claim.
- **Borrowing-base availability** and any RMA-peer-benchmarked ratio remain untouched.

**Bottom line**: the machinery is done and well-tested, and — following the balance-sheet
extension — both halves of the exit criterion (earnings and leverage/coverage/liquidity) are now
proven on real RB numbers, not synthetic fixtures. What remains open is narrower: full granular
balance-sheet cross-footing, and matching the reference workbook's own house EBITDAR/FCC
definitions specifically (a different, already-declared gap, not a blocker on the exit criterion
itself).

## Acceptance criteria — verified

- Every file in the package has a provenance entry (enforced by a failing test if not).
- The RB template loads; every row binds to a resolvable key/metric id or states a reason.
- LTM Sep-2023 constructs from resolver-chosen sources, reports three assurance levels
  (audited/compiled/company_prepared — not collapsed to "the best"), and the cash-flow-gap
  refusal fires. The sign-label trap is asserted at the pack level, not just the japes regression
  test.
- Three findings raised with severities; the reference workbook's genuine discrepancy (cash tie)
  detected and reported rather than reproduced (per the plan's own instruction: "if our figures
  agree with the reference workbook on those two cells, one of us is wrong") — and the
  balance-control claim corrected against the PRD's own text rather than force-fit.
- Balance control ties exactly on all six real periods; leverage, current ratio, and fixed-charge
  coverage all compute on real figures for the first time.
- The exit-criterion gate test exists **and passes**, with diagnostic failure messages (cell,
  both values, derivation) if it ever regresses.
- 16 tests in `test_rb_reference_case.py` (12 at initial landing, +4 from the balance-sheet
  extension net of the equity-rollforward test split into two correctly-attributed tests); full
  jaci suite 590 passed after the extension, no regressions.
