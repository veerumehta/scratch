# R1 before and after: regenerating the generated Python rules with the library prompt

51 rules; regenerated 51; spent $0.0084 of a $10.0 ceiling; 0 not regenerated.
Regenerated rules importing `rules_lib`: 38; using `unknown`: 50.

## Verdict shares over (rule, gold loan) pairs, the regenerated rules only

- before: satisfied 132 (52%), violated 118 (46%), indeterminate 5 (2%), not_applicable 0 (0%) of 255
- after:  satisfied 93 (36%), violated 37 (15%), indeterminate 65 (25%), not_applicable 60 (24%) of 255

## The rules that violated every loan before

- 21 rules. Why they failed (by what the rule's own reads and constants show): {'unstated_read': 2, 'enum_spelling': 12, 'stated_value': 7}
- After regeneration, of those: {'changed': 17, 'still violated': 4}; their verdicts now: {'indeterminate': 25, 'satisfied': 37, 'violated': 23, 'not_applicable': 20}

## Decision with and without the overlay (published -> with all of a policy's rules)

- before: DSCR_PLATINUM_SELECT: band_boundary True->False, clean_pass True->False; DSCR_STANDARD: band_boundary True->False, clean_pass True->False
- after:  DSCR_PLATINUM_SELECT: band_boundary True->False, clean_pass True->False; DSCR_STANDARD: band_boundary True->False, clean_pass True->False

Gold for clean_pass and band_boundary is `allowed`.

## Reading it

- **Cost: $0.04 in all** (51 regenerations at the deployment default model; the first pass's meter showed
  $0.034 for 42, the rest $0.008). The ceiling was never the constraint.
- **The library did what mining said it would.** Violations fell from 46% to 15% of (rule, loan) pairs;
  of the 21 rules that violated every loan, 17 now do not. 38 of 51 regenerated rules use `rules_lib`
  and 50 use `unknown`. Indeterminate rose from 2% to 25% and not-applicable from 0 to 24%: rules that
  failed on a field the loan leaves unstated or spelled another way now say so instead of denying.
- **Why the 21 failed before** (by the rules' own reads and constants): 12 enum spelling, 2 an unstated
  read, 7 a stated value past a threshold. The 12 and the 2 are what the helpers fix; the 7 are not
  false fails of that kind.
- **The decision flips remain.** clean_pass and band_boundary still go from allowed to denied with a
  policy's rules overlaid. The remaining violations on clean_pass are not spelling or missing data:
  rules that state a conditional requirement without its condition (entity documents complete, for an
  individual borrower), rules that state a program's definition as a requirement (occupancy must be
  non-owner for a loan the synthetic record calls standard), and rules over fields the synthetic loan
  states as a default (False). A library cannot fix scope; that is what per-rule gold (R4) and the fix
  loop (R5) are for, and what the extraction prompt's applicability handling should be looked at for.
- **Two regenerations failed the static check in the first pass** (a rule read a field not in its declared
  reads); the second pass produced a passing rule for each. The extractor raises rather than retries, so a
  batch run should retry once.
