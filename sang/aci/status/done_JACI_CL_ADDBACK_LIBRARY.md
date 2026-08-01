# Done: Add-Back Library, Candidate/Approved Layer, and Cross-Period Consistency

Author: Virendra Mehta · Completed 2026-07-29
Repo: jaci (+ one japes edit) · Landed: jaci dev `e50a28a`, japes dev `d5d9b47` (both unpushed, no
version bump on either repo)
Plan: docs/plans/plan_JACI_CL_ADDBACK_LIBRARY.md (superseded by this file)

All 5 phases landed. Wave 1b of `plan_JACI_CL_PRD_COMPLETION.md`. Two real corrections to the
plan's own grounding, found during authoring rather than propagated: `ProvenanceType` already had
five members, not the two the plan's grounding note implied (the prescribed action — add three
more — was unaffected); Phase 4's own text had already self-corrected an earlier revision's
"build `detect_cross_period_addbacks` from scratch" claim before this pass started — it exists and
was extended, not rebuilt.

## What shipped

- japes `jazzx_sdk/fabric/canonical/evidence.py`: `ProvenanceType` gains `ADJUSTMENT_CANDIDATE`,
  `APPROVED_ADJUSTMENT`, `POLICY_ADJUSTED` (FR-ADJ-3) — not the full eight-value enum the PRD
  names; the remaining members are a later addition once a consumer needs them.
- `config/packs/ci-spread-core/addbacks.yaml`: categorized, conditional, cappable add-back entries
  (category, source key, DSL condition, DSL cap, default disposition, rationale template) as pack
  data, superseding `normalize.addback_keys`'s flat list for new callers (the old function/list
  stays, unchanged, for existing callers).
- `capabilities/commercial_lending/addback_library.py`: `AddbackLibrary`/`AddbackEntry`/
  `AddbackCategory`, `load_addback_library()` (validates every DSL condition/cap parses and every
  source key resolves against the chart of accounts at load time), `build_add_backs_from_library()`
  (evaluates conditions/caps via the DSL; an unevaluable condition or cap — missing flag, missing
  ceiling — emits a *candidate* with the reason recorded, never a silent skip or an unconditional
  add-back).
- `normalize.apply_normalization` gains `official: bool = False` (default preserves existing
  behavior): when `True`, a still-`ADJUSTMENT_CANDIDATE` add-back is refused (typed `Refusal`, not
  an exception) rather than summed into an official/covenant-bound metric.
- `validation.detect_cross_period_addback_inconsistency`, alongside the existing
  `detect_cross_period_addbacks` (not replacing it — its own tests stay unchanged): takes
  `adjustments_by_period` (what was actually *applied*, not just what's *present*), so a line
  reported in every period but added back in only one is now distinguishable from one genuinely
  present in only one period. Severity optionally profile-resolved.
- `metrics.yaml`: `cit_ebitda` (RB's own house EBITDA — gross profit less SG&A less rent),
  `cit_ebitda_bridge_from_textbook_ebitda` (the FR-ADJ-5-required reconciliation, as its own
  computed metric, not a footnote), `ebitdar`, `fixed_charge_coverage_ratio`.
- New chart-of-accounts keys the above bind to: `bad_debt_expense`, `litigation_settlements`,
  `gain_loss_on_sale_of_assets`, `owner_compensation`, `relief_and_one_time_income`,
  `rent_expense`.
- 36 new tests (`test_addback_library.py` ×16, `test_normalize.py` +4, `test_validation.py` +5,
  `test_metrics_catalog.py` +11 covering the house definitions).

## Acceptance criteria — verified

- Library loads, every condition/cap parses, every source key resolves.
- Owner compensation exceeding a policy ceiling emits at the ceiling with both the uncapped and
  capped figures in the derivation; bad debt with no non-recurring flag emits as a candidate, not
  approved and not silently dropped.
- The exit-criterion bad-debt case (present and non-trivial in three periods, applied in one)
  produces exactly one finding naming all three periods and their amounts — the thing the
  presence-only detector structurally cannot see.
- `cit_ebitda`/`ebitdar`/`fixed_charge_coverage_ratio` compute correctly on a hand-built fixture;
  independently re-verified against the real Regional Bank reference case in Wave 1e
  (`cit_ebitda` = 11,810 on the LTM Sep-2023 column, matching the reference workbook's own
  `First Citizens Format!J12` exactly).
- Full jaci suite green (538 passed at landing time), no regressions.
