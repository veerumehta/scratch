# Done: Validation Completion (Arithmetic Controls, Cross-Foot, Disclosure, Severity)

Author: Virendra Mehta · Completed 2026-07-29
Repo: jaci · Landed: dev `178bffd` (unpushed, no version bump)
Plan: docs/plans/plan_JACI_CL_VALIDATION_COMPLETION.md (superseded by this file)

All 4 phases landed. Wave 1c of `plan_JACI_CL_PRD_COMPLETION.md`, absorbing Wave 2a's severity
model. One genuine scope ambiguity in the plan text was resolved by asking the user rather than
guessing (FR-VAL-5's exact meaning for a statement with no separate opening/closing columns);
getting it wrong would have made the detector misfire on every real filing.

## What shipped

- Four new `DefectClass` members + detectors, gated behind `validate_package`'s new
  `control_tolerance` param (`None` by default — off, since tolerance is institution policy, never
  a module default):
  - `detect_balance_control` (FR-VAL-1): total assets vs. liabilities + equity, reports the
    discrepancy amount.
  - `detect_cash_flow_tie` (FR-VAL-3): cash-flow ending cash vs. balance-sheet cash.
  - `detect_equity_rollforward` (FR-VAL-4): opening equity + net income + contributions -
    distributions vs. closing equity; distinguishes "unverifiable" (no contributions/distributions
    separately reported) from "mismatch" — an unverifiable control and a passing one are different
    results, per the plan's own instruction.
  - `detect_period_continuity` (FR-VAL-5): a balance-sheet line's period-over-period change
    against the cash-flow statement's own "change in X" line for the same concept — the reading
    chosen after asking the user, verified against a real 10-K (direction ties exactly; magnitude
    only approximately, due to non-cash items — hence a real policy tolerance, not near-zero).
- `detect_income_statement_cross_foot` (extends FR-VAL-2, the follow-up `detect_hardcoded_plugs`'s
  own docstring names): reads the sequential subtotal chain from the chart of accounts'
  `is_subtotal`/`parent` fields in declaration order, never hardcoded. Deliberately stops before
  `interest_expense_income_net`/`other_income_expense_net`/`income_tax_expense` — verified against
  a real 10-K that those use a signed-addition convention, not this chain's unsigned subtraction;
  extending the chain there would misfire on every real filing.
- `DisclosedObligation`/`detect_undisclosed_obligations` (FR-VAL-8, the MVP exit-criterion item):
  a typed, caller-supplied input (footnote extraction, FR-EXT-4, is unbuilt — this is the stubbed
  interface it will fill); recomputes funded debt and leverage via the existing
  `compute_metric_results`, reporting reported/recomputed side by side.
- `Severity` expanded from 2 to the PRD's 6 values (Critical/High/Medium/Low/Policy/Data);
  `BLOCKING`/`ADVISORY` kept as their own distinct values (not a true Python enum alias — a true
  alias would break `Severity("blocking")`, which an existing test and profile convention already
  relies on) with a new `.blocks_promotion` property covering both. New `aggregate_status`
  (`pass`/`pass_with_flags`/`blocked`); `promotion_refusal` now consumes it. Existing defect
  classes' default severities untouched — zero behavior change to `promotion_refusal` for
  pre-existing findings.
- New chart-of-accounts keys: `capital_contributions`, `distributions_to_owners`.

## Acceptance criteria — verified

- Each new detector fires on a fixture with a planted break and is silent on a clean fixture;
  equity roll-forward reports unverifiable (not passing) when contributions/distributions aren't
  separately stated.
- Income-statement cross-foot: a fixture where gross profit ≠ revenue − COGS produces a finding;
  a *fixture vocabulary* (not the real chart of accounts) with an added subtotal proves the chain
  is read generically, not hardcoded to real key names.
- Disclosure check: a fixture obligation absent from the balance sheet produces a finding naming
  the amount and source coordinate, with recomputed leverage reported alongside the reported
  figure.
- Every existing finding still maps correctly through `promotion_refusal`, asserted by the
  pre-existing test suite passing unchanged.
- Independently re-verified in Wave 1e against the real Regional Bank reference case: the
  $573,000 unrecorded ERC tax obligation and the reference workbook's own real cash-tie and
  equity-rollforward discrepancies all reproduce through these exact detectors on real figures.
- 42 tests in `test_validation.py` (was 26); full jaci suite 554 passed at landing time, no
  regressions.
