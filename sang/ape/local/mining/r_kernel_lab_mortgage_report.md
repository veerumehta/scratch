# Mining kernel-lab mortgage evaluators for `rules_lib` helpers

Source: `kernel-lab/codec-core/workflows/evaluators` (115 evaluators, tests excluded; `codec-suite`
holds a near-copy and is not counted twice). Scripts: `mine_kernel_lab_mortgage.py` (counts) and
`show_helper_bodies.py NAME` (distinct bodies of one helper), both in this directory. Date: 2026-10-11.

**Read the counts with this in mind.** These are agency-guide evaluators (FNMA/FHLMC/FHA/VA), one
class of about 900 lines per JTBD, reading relational tables of rows. A Plato Python rule is one
check of 10 to 30 lines over flat schema facts. "Defined in N evaluators" means N files each wrote
its own copy, so it measures what a rule author reaches for, not what one rule does. Every count
below is the number of evaluator files unless it says hits.

## Two defects in the current lib (found by the mining, checked against `lib.py` 1.0.0)

1. **`ratio` refuses `Decimal`.** `ratio(Decimal("3"), Decimal("2"))` returns None, so a rule that
   uses Decimal reads "cannot tell". kernel-lab uses Decimal in all 115 evaluators
   (`Decimal(str(...))` in 70). R0 had one rule that imported `decimal`. Fix: accept
   `numbers.Real` / `Decimal` (still not `bool`). This changes an answer, so `LIB_VERSION` minor.
2. **`norm` keeps word boundaries; kernel-lab's 103 copies drop them.** `same("CashOut", "Cash-Out")`
   is False. `_clean` (58 files, 58 distinct), `_token` (31) and `_norm` (14) all reduce to uppercase
   alphanumerics only, so `CASHOUT`, `Cash-Out` and `cash out` are equal. R0's enum drift
   (`Cash-Out Refinance` vs `cash-out refinance`) is covered either way; the joined spelling
   (`CashOut`, `COOP` vs `Co-op`, `NotApplicable`) is covered only by the squashed form. Proposed:
   `norm` drops spaces as well (`"cash out" -> "cashout"`). Cost: two different words that only
   differ by spacing collide; no case found in either corpus. Answer change, so a `LIB_VERSION` bump.

## Candidates that clear the bar (3 or more)

| # | Helper | Count | Disagreement found | Layer |
|---|---|---|---|---|
| 1 | `day` | 41 `_safe_date` (39 distinct) + 17 `_date`; ISO parse in 64 files | `fromisoformat` of the whole string vs of `[:10]`; one strips `Z`, one does not | rule lib |
| 2 | `months_between` | 6 `_months_between` + 3 `_whole_months`, all 9 distinct; 147 `*_MONTHS`/`*_DAYS` constants in 47 files | a partial month counts in some (`max(months, 0)`) and not in others (`-1 if end.day < start.day`): a seasoning test gives different verdicts for the same dates | rule lib |
| 3 | `days_between` | `.days` in 23 files (48 hits), e.g. `(as_of - end).days > GENERAL_DOCUMENT_AGE_DAYS` | sign order varies by site | rule lib |
| 4 | `close` | `abs(a - b) <= TOL` 135 hits in 53 files; 58 files declare a tolerance (`AMOUNT_TOLERANCE = 1.00` x32+6, `5.00` x12, rate `0.125` x9); 5 sites relative (`max(abs_tol, x * pct)`) | `<` vs `<=` at the edge | rule lib |
| 5 | `flag` | 106 tri-state bool coercers (`_is_true` 26, `_as_bool` 20, `_bool` 16, `_to_bool` 13, `_truth` 9, `_true` 8, `_safe_bool` 7, `_is_false` 7); token sets in 90 files | `_is_true` answers False for missing, `_as_bool` answers None: an absent flag is "no" in one and "cannot tell" in the other | rule lib, if string flags reach rules (see note) |
| 6 | `band` | 15 files with tier ladders of 3+ `<= self.X_MAX` branches (IPC limit by LTV, reserves by unit count) | edge inclusivity per site | rule lib, but prefer pack threshold/matrix data where the pack declares the tiers |
| 7 | `first` | `_first_present` 4, `_first_value` 3, `_first_decimal` 10, `get_value(...) or get_value(...)` chains 5 | `or`-chains treat `0` as missing | rule lib |
| 8 | `monthly` | frequency maps in 3 files, `_monthly`/`_to_monthly` 3; `*12`/`/12` 16 hits in 9 files | biweekly as `26/12` in one, `x 2.1667` nowhere; consistent | derivation preferred; rule lib acceptable |
| 9 | `business_days_between` | 4 defs, 4 distinct | one counts after start up to before end, one through end; no holiday calendar in any | rule lib (weekdays only; holidays are data, not a pure helper) |

Proposed signatures (each pure, None-tolerant like the existing seven):

```python
def day(value):
    """``value`` as a date (date, datetime, or ISO text, of which the first 10 characters are read),
    or None when it is not one. Use when a rule reads a date field."""

def months_between(start, end):
    """Whole calendar months from ``start`` to ``end`` (a month counts once its day is reached), or
    None when either is not a date. Use for seasoning, history and lookback windows stated in months."""

def days_between(start, end):
    """``(end - start).days``, or None when either is not a date. Use for document age and windows
    stated in days."""

def business_days_between(start, end):
    """Weekdays after ``start`` up to and including ``end``, or None. No holidays: use when the
    policy says business days and the case gives no holiday list."""

def close(a, b, tolerance=0, relative=0):
    """Whether ``a`` and ``b`` differ by at most ``max(tolerance, relative * |b|)``, or None when
    either is not a stated number. Use when two sources should agree (LOS vs document, stated vs
    computed)."""

def flag(value):
    """True, False, or None from a bool or yes/no text (Y, yes, true, 1 / N, no, false, 0); None
    for anything else. Use when a yes/no field may be written as text or left blank."""

def band(value, bands, above=None):
    """The answer of the first ``(upper, answer)`` in ``bands`` with ``value <= upper``, else
    ``above``; None when ``value`` is not a stated number. Use for a tier table in the rule."""

def first(*values):
    """The first of ``values`` that `known` accepts, else None. Use when a policy names a fallback
    field (note date, else closing date)."""

def monthly(amount, frequency):
    """``amount`` per month for WEEKLY (52/12), BIWEEKLY (26/12), SEMIMONTHLY (2), MONTHLY (1),
    QUARTERLY (1/3), ANNUAL (1/12); None for another frequency or an unstated amount."""
```

All take the as-of date as an argument (a fact such as `closing_date`), never the clock: only 5 of
115 evaluators read `date.today()`, and the lib's no-clock rule stays.

## Already covered, or close to it

- `ratio`: `_ratio` 3; covered, but see defect 1.
- `known`/`gaps`/`unknown`: kernel-lab writes `value is None or value == ""` inline almost
  everywhere. 11 files also treat `N/A`, `NONE`, `NULL` as unstated; `UNSTATED` has none of them.
  Worth adding `"n/a"`, `"na"`, `"none"`, `"null"` with the defect fixes (same bump).
- `norm`/`same`/`match`: covered in intent; see defect 2.

## Belongs to another layer

- **Number coercion** (`_safe_decimal` 45, `_decimal` 26, `_safe_int` 53; 39 files strip `$`, `,`,
  `%`): kernel-lab reads raw extracted strings. A Plato rule reads schema-typed facts, so `"$1,234"`
  should be refused or converted at intake, not in each rule. Add a rule helper only if R3 shows
  string numbers reaching rules. `flag` (5) has the same caveat, but the tri-state answer is the
  real point there, so it is listed as a candidate.
- **Percent vs fraction**: 4 sites guess the scale (`value * 100 if value <= LTV_FRACTION_CEILING`,
  `result / 100 if result > 1`). This is the bug the field-unit declaration
  (`FieldUnit` in `pipelines/policy/conditions.py`) already removes. Do not add a guessing helper.
- **Aggregation over rows** (`sum(` 235 hits in 53 files: eligible assets, unsourced deposits,
  liabilities; averages and counts): needs array facts, and whether a row with a missing amount
  counts as 0 or makes the total unknown is a policy decision. That belongs to a declared derivation
  (sum/count/avg next to `RatioDerivation` in `fabric/graph/derive.py`, which today computes only
  ratios), not a rule helper. Same for **latest row by date** (`max(key=date)` in 25 files,
  `_latest_row` 11) and **dedupe** (11).
- **Name and address equivalence** (`_names_equivalent` 11, `_entities_equivalent` 6,
  `_addresses_equivalent` 5, `_normalize_address` 5; several fall back to an LLM): entity resolution
  at extraction or reconciliation, not a pure rule helper.
- **Display formatting** (`_money` 27, `_percent` 8, `_yes_no_unknown` 6, `.quantize` for display
  in 6 of 16 files): presentation of findings, not a verdict.
- **Rounding**: `.quantize` in 16 files, 2 of them with an explicit rounding mode (the rest take
  Decimal's half-even default). Real for verdicts only where a policy states rounding (DTI to two
  places); R0 had 1 of 51. Hold until a policy-stated rounding repeats in rules.

## Not seen often enough

`_last4` 7 and `_roman_to_int` 4 are identifier parsing for document matching, not rule checks.
`_trend` 12 (rental/income trend) is real but each one's categories are policy-specific, so a helper
would be a policy in disguise.

## Suggested order

1. Defects 1 and 2 plus the `UNSTATED` additions (one `LIB_VERSION` bump).
2. Dates: `day`, `months_between`, `days_between` (the strongest evidence: 9 distinct month counters
   that disagree).
3. `close`, `flag`, `first`.
4. `band`, `monthly`, `business_days_between` once a DSCR or CRE rule needs them; the bar is met
   here but not yet in a Plato corpus.
