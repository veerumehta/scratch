# Done: Period Model and LTM Construction

Author: Virendra Mehta · Completed 2026-07-26
Repo: japes · Landed: 2.2.0 (dev, commit `ce169d6`, squashed)
Plan: docs/plans/plan_JAPES_2_2_0_PERIOD_MODEL.md (superseded by this file)

All 5 phases landed as planned, verified against the real Financial Spreading PRD v0.4 (jaci's
`docs/plans/Financial Spreading PRD v0.4 2.pdf`), no deviations from the acceptance criteria.

**Update 2026-07-27**: a desktop-app review caught a real Phase 2 gap after the squashed commit
was pushed — `default_line_semantics(statement_type)` existed, but there was no `semantics` field
on `SpreadLine` itself; the only override path was a `construct_ltm(..., line_semantics=...)`
call-time dict, which the plan's own language ("the default is wrong often enough to matter")
argued should be a durable, per-line property instead. Fixed in a follow-up commit: added
`SpreadLine.semantics: LineSemantics | None`, checked in `_semantics_for()` between the call-time
override dict (highest precedence — a one-off override for data the caller doesn't control) and
the per-statement-type default. Verified with 2 new tests plus the full japes (1810 passed) and
jaci (575 passed, same 7 pre-existing unrelated failures) suites.

## What shipped

- `jazzx_sdk/finance/periods.py`: `PeriodKind`, `LineSemantics` (+ `default_line_semantics()`),
  `Assurance` (+ `ASSURANCE_RANK`, ordered to FR-SRC-2's default source-precedence), `PeriodRef`,
  `PeriodDerivation`, `Period` (frozen; identity = date range + kind via `period_id`, not the
  display label), `PeriodSet`, `construct_ltm()`.
- `FinancialSpread.period_set: PeriodSet | None` added alongside the existing
  `periods: list[str]` (circular import with `spread.py` resolved via `TYPE_CHECKING` + a
  `model_rebuild(_types_namespace=...)` call at the bottom of `periods.py`).
- 18 tests in `tests/test_finance_periods.py`.

## Acceptance criteria — verified

- Phase 1: `test_period_set_from_three_yeti_filings_preserves_ordered_labels` — a `PeriodSet`
  built from three differing-calendar sources produces the same ordered labels the bare string
  list did, each period reporting its own kind and length.
- Phase 2: `test_no_statement_type_defaults_to_flow_on_balance_sheet` — no BS line silently
  defaults to `flow`.
- Phase 3: `test_appendix_d_ltm_flow_lines_compute_exactly` — the PRD's real Appendix D worked
  example (RB LTM Sept-2023) computes exactly: `57,581 + (61,443 - 44,326) = 74,698`. Guardrails
  (fiscal-cutoff mismatch, unequal interim lengths, missing prior-year interim) all verified as
  typed `Refusal`s, not fabricated values.
- Phase 4 (FR-PER-6): `test_engine_encodes_verified_formula_not_the_sources_wrong_sign_note` —
  the emitted derivation is the verified addition form; the reference workbook's incorrectly
  signed human note is never transcribed.
- Phase 5: `test_financial_spread_periods_unaffected_when_period_set_absent` +
  `test_financial_spread_period_set_is_additive` + jaci's full test suite run against the new
  SDK with **zero jaci changes** (confirmed both before and after squashing the japes commits).

## Notes for next time

- `Assurance`'s precedence *resolver* (picking a winning source when several disagree) is
  explicitly out of scope here — this plan only supplies the enum + ordering. A future plan wires
  the resolver.
- FR-PER-9 (annualization/TTM alternatives, 13-week/52-53-week and fiscal-month calendars) and
  FR-PER-10's use inside the Expression DSL's `ltm()` function (done — see
  `done_JAPES_2_2_0_EXPRESSION_DSL.md`) were the only two things this plan deliberately deferred
  or handed off.
