# Done: Reclassification and Break-Out Engine

Author: Virendra Mehta · Completed 2026-07-29
Repo: jaci · Landed: dev `0eb0663` (unpushed, no version bump)
Plan: docs/plans/plan_JACI_CL_RECLASSIFICATION_ENGINE.md (superseded by this file)

All 4 phases landed. Wave 1d of `plan_JACI_CL_PRD_COMPLETION.md`. One design fork surfaced before
any code was written and was resolved by asking the user, because it shaped every phase
downstream: whether the projected/reclassified package needed to be a real alternate
`SpreadPackage` (so `detect_hardcoded_plugs` could run against it unmodified and stay silent) or
just numeric adjustment records. The user chose the fuller, more faithful path.

## What shipped

- `reclassification.py` / `reclassifications.yaml`: Appendix A's move/split/conditional_move rules
  as pack data (19 rules). `ClassificationCategory` uses six distinct values (current/non-current/
  intangible-asset, current/non-current-liability, net-worth) rather than a shared current/
  non-current pair, so a rule's target is unambiguous without inspecting which balance-sheet side
  its source line sits on. Conditions are DSL expressions over `{"flag": 0|1}`, mirroring
  `addback_library.py`'s own convention. The unrelated-party term-debt "split" Appendix A names
  turned out to be two confirmatory moves, not a runtime split — jaci already models CPLTD and
  long-term-debt-net-of-current as two separate canonical keys.
- `apply_reclassifications`/`project_effective_package`: a MOVE/resolved CONDITIONAL_MOVE emits
  one adjustment; a SPLIT emits two, asserted to sum to the original exactly. The projection
  relabels a reclassified line's section to its target category and recomputes only the three
  chart-of-accounts subtotals with an existing home (`total_current_assets`/
  `total_current_liabilities`/`total_stockholders_equity`); the three homeless categories
  (non-current asset, intangible, non-current liability) get relabeled with nothing to check
  against — `detect_hardcoded_plugs`'s own zero-subtotals-means-nothing-to-check guard handles
  that case already.
- `breakouts.py`/`breakouts.yaml`: all 4 Appendix A break-out cases (officer/owner comp out of
  SG&A, interest embedded in COGS, D&A wherever it sits, the combined interest/amortization
  split). `owner_compensation` is the exact key `addbacks.yaml` (Wave 1b) already sources from —
  coordinated, not a parallel set. Always assumption-provenance; an unresolved break-out (no fact
  supplied) leaves the parent line completely untouched, never estimated.
- `tangible_net_worth` (FR-RAT-2): a pure DSL metric in `metrics.yaml`; the "where policy
  requires" related-party-receivable exclusion is a DSL `if()` reading an `ASSUMPTION` binding,
  not new Python.
- `standardized_template_rows` (FR-SPR-1/2): turned out to need no `spread_template.yaml` edits at
  all — its existing rows already reference the same canonical keys `project_effective_package`
  updates in place, so "pointing at effective classifications" is a matter of which package backs
  the render, composed with the existing, unmodified template render.
- 11 new chart-of-accounts keys the above bind to (restricted cash, CSV of life insurance,
  deposits/deferred charges, related-party A/R and notes, third-party notes receivable,
  related-party debt, reserves, subordinated debt, interest-embedded-in-COGS, the combined
  interest/amortization line, D&A-embedded-elsewhere).

## Acceptance criteria — verified

- Total assets provably unchanged after reclassification (the subtotal is never touched by
  construction); current assets changes exactly by what moved; every split sums to the original
  exactly; `detect_hardcoded_plugs` runs against the projected package unmodified and stays
  silent.
- Break-out: officer comp disclosed via a fact breaks out with assumption provenance and SG&A
  reduced by exactly that amount, operating income unchanged; without the disclosure, an
  unresolved outcome and untouched SG&A.
- Tangible net worth verified against real YETI FY2023 10-K figures
  (`723,610 − 54,293 − 117,629 = 551,688`), not an invented fixture.
- Standardized current-assets subtotal reflects a reclassification while total assets in the same
  render stays identical to the as-reported figure.
- 32 new tests (`test_reclassification.py` ×15, `test_breakouts.py` ×5, plus 2 existing suites
  updated for the new metric/key counts); full jaci suite 574 passed at landing time, no
  regressions.
