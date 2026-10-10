# R3 baseline: the generated Python rules over the synthetic gold loans

51 Python proposals, trialled by policy over 5 gold loans (band_boundary, clean_pass, double_cap, na_cell, sub_1_dscr_cashout), records only, no documents, no model call.

## Verdicts

- (proposal, case) pairs: 255; satisfied 132 (52%), violated 118 (46%), indeterminate 5 (2%)
- Proposals indeterminate on every case: 1/51
- Proposals satisfied on every case: 22/51; violated on every case: 21/51 (a rule that fails every loan, good or bad, is suspect)

- Violations resting on a read the loan leaves unspecified (None, blank, 'unspecified'): 28 of 118; the rest fail on stated values

## Fields the rules needed and the loans did not supply

- `interest_rate`: 5 (proposal, case) pairs

## Decision with and without the proposals overlaid

Each row: published `allowed`, `allowed` with all of that policy's proposals, gold `allowed`.

- DSCR_PLATINUM_SELECT: band_boundary: True -> False (gold True); clean_pass: True -> False (gold True); double_cap: False -> False (gold False); na_cell: False -> False (gold False); sub_1_dscr_cashout: False -> False (gold False)
- DSCR_STANDARD: band_boundary: True -> False (gold True); clean_pass: True -> False (gold True); double_cap: False -> False (gold False); na_cell: False -> False (gold False); sub_1_dscr_cashout: False -> False (gold False)

Cases whose decision the overlay changed: 4 of 10.

## Per case (verdict counts over all proposals)

- band_boundary: {'satisfied': 27, 'violated': 23, 'indeterminate': 1}
- clean_pass: {'satisfied': 27, 'violated': 23, 'indeterminate': 1}
- double_cap: {'satisfied': 24, 'violated': 26, 'indeterminate': 1}
- na_cell: {'satisfied': 26, 'violated': 24, 'indeterminate': 1}
- sub_1_dscr_cashout: {'satisfied': 28, 'violated': 22, 'indeterminate': 1}

## Reading the baseline

- **A product bug was hiding 34 rules.** Before the fix, 69% of (rule, case) pairs were
  indeterminate and 35 of 51 rules were indeterminate on every loan. The cause was not missing data:
  a typed fact catalog normalises numbers to `Decimal`, which the executor's JSON could not carry, so
  every python rule reading such a number was withheld as "not activated" (the old
  `TODO(rule-reads-not-json-coerced)`). Fixed in `PythonEvaluator` (a whole `Decimal` reaches the
  rule as an int, otherwise a float); after it, 2% are indeterminate (all `interest_rate`, which the
  gold loans do not state). Any python rule trialled or run before the fix was silently inert.
- **The overlay denies loans gold allows.** With every proposal of a policy overlaid,
  `band_boundary` and `clean_pass` go from allowed to denied (gold: allowed), in both programs: 4 of
  10 decisions changed, all toward denial. 118 of 255 verdicts are violations (46%), 21 rules violate
  every loan, and 28 of the 118 rest on a field the synthetic loan leaves unspecified. This is the
  false-fail class R4 and R5 exist for; without per-rule gold the baseline cannot say which of the
  118 are wrong, only that the decision-level gold is contradicted twice per program.
- **What the baseline cannot say yet:** per-rule gold (R4), boundary false fails (needs a rule's
  threshold), and document-read effects (these were records, not documents).
