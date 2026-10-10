# R0 mining: generated Python rules

Source: http://localhost:8000/api/v1, pack acra-dscr-policy, tenant acra-lending. 159 rule proposals, 51 Python (acra-platinum-fa8c8374 25, acra-standard-53ed2625 26). Rule kinds: {'procedure': 108, 'python': 51}.

## Metric baseline (R0 share of section 10)

- Deterministic share (rung 1 or 2: conditions and procedures over all rule proposals): 108/159 (68%)
- Computable coverage by schema (every read is a field of the loan application schema): 51/51
- Indeterminate honesty: rules whose verdict can be something other than True/False (None, 'unknown'): 0/51; rules whose verdict is an expression (Compare/BoolOp/Name): 38/51
- Generated cases: 466 agree with the rule, 2 disagree, 12 raised (1 KeyError) of 480
- Trial pass rate on gold and false fails at boundaries need real or synthetic document cases (R3); the generated cases above are the rule's own and prove less.

## What the rules repeat (share of Python rules)

| Pattern | Rules |
|---|---|
| reads a field with `ctx['x']` (KeyError when the field is missing) | 100% (51/51) |
| guards a read against None | 16% (8/51) |
| compares to string literals (enum values) | 28/51 use ==/in |
| normalises text (lower, strip, upper) | 12% (6/51) |
| rounds or uses Decimal/Fraction | 2% (1/51) |
| handles dates | 0% (0/51) |
| divides (ratios) | 14% (7/51) |
| converts units with 100 | 0% (0/51) |
| membership tests (in a list or set) | 37% (19/51) |
| defines its own helper function | 0% (0/51) |
| imports a module | 2% (1/51) |
| accesses a field not in its `reads` | 0% (0/51) |
| reads a field the loan schema does not have | 0% (0/51) |

Return values across rules: {'False': 82, 'True': 28, 'Compare': 22, 'BoolOp': 10, 'Name': 4, 'UnaryOp': 4, 'Subscript': 2}.
Rule length: median 11 lines, max 127.
Imports used: {'decimal': 1}.
Comparison operators: {'Lt': 43, 'Gt': 46, 'Eq': 83, 'LtE': 98, 'NotIn': 12, 'GtE': 27, 'NotEq': 9, 'In': 40, 'Is': 9, 'IsNot': 25}.

## Enum literals that differ only by case or separator across rules

- `borrower_entity_type`: 'ENTITY', 'entity'
- `loan_purpose`: 'Cash-Out Refinance', 'PURCHASE', 'Purchase', 'cash-out refinance', 'purchase'

## Most read fields

- `loan_amount`: 24 rules
- `loan_purpose`: 24 rules
- `cltv_pct`: 24 rules
- `fico`: 16 rules
- `property_type`: 11 rules
- `vacant_property`: 11 rules
- `gross_rental_income`: 9 rules
- `pitia`: 8 rules
- `citizenship_type`: 8 rules
- `property_state`: 8 rules
- `first_time_homebuyer`: 7 rules
- `channel`: 6 rules
- `occupancy_subtype`: 6 rules
- `delayed_financing`: 5 rules
- `rural_property`: 5 rules

## Reading the numbers (R0 findings)

- **The helper library is small.** In 51 rules: no date handling, no unit conversion, no helper
  function, one import (`decimal`, once), one rounding use, seven divisions. The earlier review's
  "same few mistakes 51 ways" is real but narrow: enum spelling (`loan_purpose` appears as
  `purchase`, `Purchase`, `PURCHASE`, `cash-out refinance`, `Cash-Out Refinance`; `borrower_entity_type`
  as `entity` and `ENTITY`), and missing-field handling.
- **No rule can say "I cannot tell".** 0 of 51 return None or an unknown marker; all 51 read with
  `ctx['x']` (a missing field raises, 1 of 480 generated cases hit it) and only 8 guard a read against
  None. The indeterminate convention is the larger win, as the plan's risk section expected.
- **A tuple return is a convention already in use** (`(verdict, {values})`, 18 returns); the verdict
  is often an expression (38 of 51 rules return a Compare/BoolOp/Name somewhere), so a rule's verdict
  is a bool only by luck of the expression: a comparison against a None value raises TypeError.
- **Candidate library functions, by evidence:** `lib.same(value, "purchase")` (case, spacing and
  separator-insensitive equality for enum values, 28 rules compare to string literals, 24 read
  `loan_purpose`); `lib.unknown(missing=[...])` and a missing-field-safe read; `lib.pct`/ratio
  helpers have 7 uses and wait for more evidence.
- **Computable coverage by schema is 51/51** once derived metrics (`cltv_pct`, `dscr`) from the
  pack's `metrics.yaml` count as available; by the loan application schema alone it is 27/51.
- **The generated cases agree with their rules 466 of 480 times, 2 disagree, 12 raised.** Those
  cases are the rule's own, so this proves little; R3 supplies gold.
