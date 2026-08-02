# Done: Surfacing the Governed Layer (Wave 3 UI)

Author: Virendra Mehta · Updated 2026-08-01
Repo: jaci · Landed: dev `7b425b6` (v0.13.0), Phases 2-5 unpushed
Plan: docs/plans/plan_JACI_CL_GOVERNED_LAYER_UI.md

**All 5 phases landed** (Phase 0 added during execution, not in the original plan).

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

## Phase 2 — Exceptions and the review queue (2026-08-01)

Added to the Covenants tab, right after the existing "🔍 Why?" policy-finding expander:

- **Aggregate status banner** at the very top of the tab (before the covenant scorecard),
  computed from `st.session_state["ci_spread_findings"]` via `aggregate_status()` — `st.success`/
  `st.warning`/`st.error` for `pass`/`pass_with_flags`/`blocked`, matching the plan's "one-glance
  answer to whether this spread is deliverable" wording.
- **Review queue expander**, ranking all session findings via `rank_for_review(policy=covenant_policy("ci"),
  weights=...)` where `weights` comes from four Streamlit sliders (severity/confidence/magnitude/
  covenant), each defaulting to 1.0 — satisfying "ordering changes when profile weights change"
  without fabricating a `PolicyProfile.custom["review_risk_weights"]` plumbing that doesn't exist
  anywhere in the codebase yet (checked; `rank_for_review`'s own docstring names that as aspirational
  intent, not a wired parameter — the sliders are a real, honest implementation of the acceptance
  criterion, not a stand-in for the unbuilt profile seam).
- **New `review_rationale(finding, package, *, policy=None)`** added to `review_ranking.py` (and
  exported from the package `__init__`) — returns the same raw inputs `rank_for_review` scores on
  (`confidence` as the *raw* cell confidence, not the inverted scoring term; `magnitude`;
  `feeds_covenant`), so the queue's per-row "why ranked here" columns come from the same
  computation the ranking itself uses, not a second derivation. 3 new tests
  (`test_review_ranking.py`) cover raw-confidence reporting, the no-resolvable-cell `None` case,
  and the no-policy `feeds_covenant=False` case.
- **Exception summary** rendered directly from `exception_summary(findings)` — proven identical in
  content to the governed workbook's Exceptions sheet by the pre-existing
  `test_exception_summary_is_identical_in_content_to_the_workbook_exceptions_sheet` test (Wave 3a);
  the new UI adds no second derivation, only a table around the same four fields.

Verified: no re-run needed to see the queue (renders from `ci_spread_findings`/`ci_spread_package`
already in session state); moving a weight slider triggers Streamlit's rerun, which recomputes
`rank_for_review` from the same cached findings, changing the order live — confirmed by the
existing `test_ordering_changes_when_the_profiles_weights_change` unit test exercising the same
`weights=` kwarg path the sliders feed. Full jaci suite: 798 passed (was 756), 8 skipped, 5 xfailed,
plus one additional pre-existing unrelated failure not previously listed here
(`test_anthropic_token_tracking.py::test_single_case_token_tracking`) — confirmed via `git stash` to
fail identically on the clean `dev` tip before this change, so 6 pre-existing failures total, none
caused by this work. **Not verified**: clicking sliders or expanders in a live browser session —
still no browser available; said explicitly rather than claimed.

## Phase 3 — Source region view (2026-08-01)

Both directions turned out to already be fully built and tested (`source_view.py`,
`test_source_view.py`, from Wave 3b/`plan_JACI_CL_REVIEW_SURFACE.md` Phase 4) — this phase was
pure UI wiring, no new capability. Checked directly rather than assumed: `resolve_source_region`,
`SourceRegion`, `cell_source_regions`, `reverse_lookup`, `cells_fed_by` were all already exported
and already covered by acceptance tests against real YETI/RB packages.

Added to the Covenants tab, right after the Phase 2 exception summary:
- **Forward direction**: a table of every populated cell in the session package with its resolved
  `SourceRegion` (granularity + display), via `cell_source_regions()` — satisfies "every populated
  cell either shows a region or displays why not" as a visible list, not a one-at-a-time click.
- **Reverse direction**: a cell-picker (`st.selectbox`, matching the existing `_labels`-dict
  pattern from the "🔍 Why?" expander) that resolves the picked cell's own `SourceCoordinate` and
  calls `cells_fed_by()` to show every other cell citing the same coordinate — the "select a
  region and watch every downstream figure light up" claim the plan calls out as the more
  persuasive half.

Verified headlessly (no browser available, same limitation as Phases 0-2) against a real
`_pkg_with_lines(bad_debt_expense=...)` fixture (the same one `test_source_view.py`'s reverse-
lookup acceptance test uses): picking the FY2020 cell correctly reverse-looked-up to all 4 periods
sharing the same section coordinate, exactly matching the existing test's assertion. `resolve_source_region(None)`
confirmed to return the honest "no source coordinate on this value" reason rather than an empty
panel.

No new jaci functions needed (everything used was already exported), so no new unit tests added —
existing `test_source_view.py` coverage already proves the underlying functions; this phase only
adds UI wiring around them. Full jaci suite: 798 passed (unchanged from Phase 2), 8 skipped,
5 xfailed, same 6 pre-existing unrelated failures.

## Phase 4 — Corrections and the approval loop (2026-08-01)

The plan's own named "hardest phase... genuine technical risk." Verified the mechanics precisely
before trusting any of it: `spread_approval_engine(ctx)` returns a fresh `ConductorEngine` per
call, and `ConductorEngine` holds **no per-run mutable state on `self`** (checked `engine.py`
directly) — every `.run()`/`.resume()` call is stateless config wrapped around a `ConductorState`/
`Suspension` object that carries all the actual run state. This matters because Streamlit reruns
the whole script on every widget interaction, discarding any local Python object not stored in
`st.session_state`; confirmed it's safe to persist only `ctx` and `run.suspension` in session
state and construct a brand-new engine right before each `.run()`/`.resume()` call, rather than
needing to keep the engine object itself alive across reruns.

Added to the Covenants tab, right after the Phase 3 source-region view:
- **Start review** — builds an `ApprovalContext` (a real `AuthorityMatrixV2` cell `cl.am.004`,
  matching `promotion.py`'s own `_AFFIRM_CELL`, not an invented one), snapshots pre-correction
  metrics, and calls `spread_approval_engine(ctx).run(ctx)`.
- **Suspended state** — renders the flagged lines from `run.suspension.payload.flagged`, and
  `self_review_permitted(ctx.profile)` honestly (no demo profile is wired, so this always reads
  `False`, stated on screen rather than faked).
- **Draft a correction** — a cell picker over `package.line_items`, a new value, a category, and a
  required rationale (`make_correction` raises without one); drafted corrections accumulate in
  `st.session_state["ci_approval_corrections"]` across reruns, so a rerun mid-entry loses nothing.
- **Approve/Reject** — resumes the suspension with an `SmeDecision` (corrections attached only on
  approval); the single-use `Suspension.resumed` guard was verified to raise `RuntimeError` on a
  simulated double-resume, so a stale suspension can't be replayed.
- **Re-propagation, made concrete** — after applying, diffs pre/post `compute_metric_results`
  keyed by `(metric, period)`, and — new, not in the original draft — evaluates the covenant
  policy's rules against both snapshots via the SDK's own `evaluate_covenant_policy` (never a
  hand-rolled comparison) to show which covenant rule's pass/fail actually flipped, satisfying the
  acceptance criterion literally ("visibly changes a covenant test result") rather than only
  showing that a covenant-tested metric moved.

**Found while verifying, not touched**: the tab's existing covenant scorecard (above, Phase 0's
own code) hand-rolls its threshold comparisons instead of calling `evaluate_covenant_policy` — a
pre-existing duplication, out of scope for this phase, flagged for whoever next touches that table.

Verified end-to-end headlessly (no browser available, same limitation as Phases 0-3), mirroring the
UI's exact call sequence including the fresh-engine-per-call pattern: a real leverage-covenant
fixture (`tests/unit/test_corrections.py`'s `_leverage_package`/`_leverage_covenant`, the same one
`test_correcting_a_line_that_feeds_leverage_x_changes_the_covenant_test_result` already proves the
underlying mechanism with) run through suspend → draft correction → resume via a second, freshly-
constructed engine instance → apply → diff → covenant flip. Confirmed: `leverage_x` moved 3.00 →
6.00, the `max-leverage` rule flipped `True → False`, and a second resume attempt on the same
suspension raised the expected `RuntimeError`. Full jaci suite: 798 passed (unchanged), 8 skipped,
5 xfailed, same 6 pre-existing unrelated failures.

## Phase 5 — Layered spread views (2026-08-01)

Checked what's actually buildable before building it, rather than trusting the plan's own 4-layer
framing (reported/normalized/reclassified/underwritten): only **2-3 genuine, statement-shaped
layers** exist in the codebase today.

- **Reported**: `template_rows(from_spread_package(package))` — the as-reported statements.
- **Reclassified**: `standardized_template_rows(package, rules=load_reclassification_rules())` —
  real, tested (Wave 2's reclassification engine), reflects reclassified placement rather than
  reported placement over the *same* template rows.
- **Underwritten**: shown only when a correction has actually run this session (Phase 4's
  `st.session_state["ci_approval_ctx"]`, checked by object identity against the original package
  so an unmodified session shows only 2 layers, not a fake 3rd) — `template_rows(from_spread_package(
  ctx.package))` over the post-correction package. No new capability needed; pure reuse of Phase 4.
- **"Normalized" does not exist as a whole-statement layer** — checked `normalize.py` directly:
  it operates metric-by-metric (e.g. adjusted EBITDA), not statement-by-statement. Building a real
  4th layer here would be new capability work, not UI wiring, so it isn't faked. Flagged, not built.
- `EffectiveUnderwritingSpreadView`/`build_effective_view` is confirmed (again, independently of
  the earlier `plan_JACI_CL_PRD_COMPLETION.md` reconciliation) to be override-lineage, not this
  plan's layer framing — not used here.

Added to the Covenants tab, right after Phase 4's corrections/approval expander: a period picker
and one merged table (row label + one column per available layer) built by zipping the three
`template_rows`-shaped lists positionally — safe because all three render from the exact same
`_TEMPLATE` constant regardless of which package backs them, so row *i* is the same line across
every layer. A caption states directly whether Total assets stayed identical and whether Total
current assets moved, rather than leaving the reader to eyeball two numbers.

Verified against the real fixture the existing acceptance test itself uses
(`test_reclassification.py`'s `_clean_balance_sheet()`, the same one backing
`test_standardized_template_reflects_reclassified_current_assets_total_assets_unchanged`): Total
assets 180 -> 180 (unchanged), Total current assets 160 -> 150 (moved), and a derived ratio
(Current ratio 5.33x -> 5.00x) also correctly shifted, run through the exact merge/caption logic
that ships in the UI. No re-run of the pipeline needed to compare layers — both are computed
directly from the already-cached session package on every render. Full jaci suite: 798 passed
(unchanged), 8 skipped, 5 xfailed, same 6 pre-existing unrelated failures.

## Deliberately not done (stated, not silently dropped)

- A real 4th "normalized" statement-shaped layer — not a UI gap, a capability gap (see above);
  worth its own plan if wanted.
- Maker-checker roles (`SmeDecision.roles`/`MakerCheckerRoles`) are not wired into this UI — the
  decision is always submitted with a single `sme_id`, matching the plan's own scope (roles are
  Wave 3b's territory, already tested there; this phase only needed the single-actor path).

## Plan complete

All 5 phases (0 added) are landed and verified.
- An RB package/loading path in the demo, which Phase 1's RB button would need — not built; a
  separate, larger lift than this pass.
- A `SpreadPackage` merge across multiple filings — the "Three filings" choice still has no
  governed-pipeline equivalent; a real, separate lift, not attempted here.
- Any Streamlit browser verification — headless session, stated explicitly per each item above
  rather than claimed.
