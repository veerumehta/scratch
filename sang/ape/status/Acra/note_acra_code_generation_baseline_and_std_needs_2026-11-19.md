# Acra code generation: baseline per job, missing std functions, and a regenerate loop (2026-11-19)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>. Read-only survey from stored artifacts: no provider call, no Plato call, no loan data opened. Decides nothing. Marks: **[run]** a script over stored files (`scripts/local/acra/regen/acra_baseline_by_job.py`, output `scripts/local/coverage/regen_5/baseline_by_job.csv`, 202 rows); **[code]** read in source; **[ledger]** a row of `scripts/local/costs/acra_costs.csv`; **[heuristic]** a keyword reading of text, to be corrected by a person.

## 1. Baseline: regen-5 (trial pack `acra-regen-5`, 2026-10-22, library 1.1.1, SDK 2.6.6)

### How the "50%" is measured, and where it lives

- **Measure** [code] `jazzx_sdk/pack/ledger.py` (`coded_share`, about line 632): jobs whose disposition is `code` or `code_and_procedure`, over all jobs the coverage report lists. Regen-5: **105 of 202 = 0.52**. "Coded" means the job has at least one linked Python rule; it does not mean the rule is right. A `code_and_procedure` job (53 of the 105) has some checks coded and the rest left to a reviewer.
- **History** [run, `coverage/regen_log.jsonl`]: 3b 0.475 (0.50 after retrying 12 connection errors), 4a 0.336, 4b 0.547, 5 0.520.
- **Where the numbers live**: `scripts/local/coverage/regen_5/coverage.json` (per job: disposition, kind, checks, missing reads, rules, unprinted figures, aligner disagreements; plus counts, schema backlog, unsupplied reads); `scripts/local/coverage/regen_log.jsonl` (one line per phase per regen); the status bundle `docs/status/Acra/acra_bundle/` (`bundle.json` counts, `4_sdk_code/from_jobs/` the 97 rule files); the cost ledger above.
- **Two other numbers that are easy to confuse with it**: the bundle counts **195 jobs** where coverage counts **202** (the 7 difference was not reconciled; it equals the 7 orphan rules, which may be a coincidence), and only **94 of 340 checks (28%)** are marked computable. The check-level share is the harder bar.

### Dispositions of the 202 jobs [run]

| Disposition | Jobs |
|---|---|
| code | 52 |
| code_and_procedure | 53 |
| computable_no_code | 6 |
| procedure | 1 |
| not_computable | 68 |
| unassessed | 22 |

### "Passes its checks": not measured at scale

No artifact holds a per-job pass or fail from running the code. What exists: (a) a static gate on every rule (they pass, or they would not be merged); (b) the aligner's disagreements (16 coded jobs) and the unprinted-figure guard (16 coded jobs; 29 jobs carry either flag); (c) one sample of 10 regen-4b rules written twice, with independent cases: **4 of 10 rules disagreed with the code** (79 cases, 0.0087 USD) [ledger]; (d) the loan-2 verifier: 22 disagreements, 17 backed a side (loan data, not repeated here). n=10 is too small to extrapolate; it does say coded is not correct. Step 3 below makes (c) the per-round pass measure, over all coded jobs.

### Cause classes [run + heuristic; per-job rows in the CSV]

For a coded job the class says what stops its rule from answering at run time; for a job without code, why none was written.

| Class (your list in bold) | Jobs | Meaning |
|---|---|---|
| coded, ok (no flag) | 29 | no figure outside the job text, no aligner disagreement, every read supplied |
| coded, **extraction gap**: the rule reads a field no document extraction supplies | 72 of the 105 (47 only this; 25 with another flag) | the rule exists but answers "unknown" until the field arrives. `LoanCore.cltv_percent` alone: 40 jobs; `listed_for_sale_last_6_months` 16; `RatioSet.reserves_months` 14; `is_first_time_homebuyer` 11; `is_escrow_waived` 11; `occupancy_subtype` 11; `dscr_qualification_method` 10; `is_interest_only` 10 |
| coded, **prompt gap**: a figure the code writes is not in the job text | 16 | the figures guard; the policy-figures review (plan 2.7.3) is the fix path |
| coded, aligner disagrees with the job | 16 | not classified further (no rule-level reason stored) |
| not coded, **missing function or derived field**: a figure or rate the case does not carry | 18 | DSCR, DTI, LTV, PITIA, reserves months, annual amounts, maturity, ratings |
| not coded, **extraction gap**: a yes/no fact or attribute absent from the case schema | 39 | entity, trust, title, guarantor and ownership facts, state and property facts |
| not coded, **extraction gap**: document evidence with no field | 20 | seasoning, funds to close, lease and rent evidence, certificates |
| not coded, **other**: the guideline needs an Acra answer or lacks text | 13 | "Acra confirmation requested", definitions the guideline does not give |
| not coded, **other**: computable, no code linked | 6 | their names match orphan python rules (`...docx.22/32/36/38`): written, never aligned to the job (matched by name, not verified) |
| not coded, **other**: procedure by design | 1 | |
| **date or rounding rule** | 0 observed | 2 of 97 rules do date math inline and 7 use `Decimal` inline; none shows a wrong answer in any artifact |
| **unknown handling** | 0 observed as a failure | 94 of 97 rules use `gaps`/`unknown`; the cost is the 72 above, not a wrong answer |

### What this says about the target

- Of the 97 jobs without code, **only 18 (+6 not linked) are the kind a std function helps**. 59 (39 + 20) need fields added to the case schema and the document extraction, and 14 need a policy answer from Acra. The ceiling for "coded" is about **93% (188 of 202)** if every class except the Acra and procedure ones becomes computable; **about 64% ((105 + 18 + 6) / 202) from std plus fixing the alignment**. Reaching 100% is not available from the SDK side: 13 jobs say so in their own reads.
- The larger lever for answers that are right at run time is the 72 coded rules whose reads nobody supplies. Of those, the derived ones (CLTV, reserves months, months since an event, DSCR qualification) are exactly what std plus a derived-field declaration can supply; the raw ones (first-time buyer, escrow waiver, occupancy subtype) are extraction.
- The rules mostly do not use the library: **11 of 38** helpers appear in the 97 rules (`unknown` 96, `gaps` 94, `flag` 51, `same` 50, `percent` 32, `ratio` 7, `band` 5, `match` 3, `known` 2, `close` 1, `norm` 1). Regen-5 ran on library 1.1.1 (22 helpers); 1.1.2 (38) has not been tried on these jobs. 10 rules write a grid as an if-ladder with two or more assignments; 22 spell the loan-purpose values by hand.

## 2. Missing std functions

Existing and not repeated: `ratio`, `percent`, `band`, `match`, `in_set`, `within`, `at_least`, `at_most`, `close`, `monthly`, `months_between`, `months_between_fraction`, `days_between`, `edate`, `eomonth`, `lowest`, `highest`, `total`, `average`, `first`, `latest`, `round_half_up`, `round_ceiling`, `round_floor`. Not std, because it is vocabulary: the 22 hand-spelled loan-purpose lists and the 14 property-type lists belong in the case schema's allowed values (so `ctx` carries one canonical spelling), not in a function.

Entries follow the admission rules (named and typed, pure, Decimal-safe, a declared unknown policy, three golden cases: normal, boundary, unknown). Unknown policies: **propagate** (the answer is the unknown), **refuse** (a reason, not a value). Amounts and rates are `Decimal` in and out; text numbers are read as printed.

| # | Name and signature | What it returns | Unknown policy | Golden cases (normal / boundary / unknown) | Evidence |
|---|---|---|---|---|---|
| 1 | `loan_to_value(liens, values)` | percent on the 0 to 100 scale: the sum of the lien amounts over the lowest stated value | propagate: any lien not stated, no value stated, or a value of zero or less | `([400000], [500000, 520000])` is 80; `([400000], [400000])` is 100; `([400000, 50000], [None, None])` is None. With `liens` holding every lien it is CLTV, with the first lien alone it is LTV | 40 coded jobs read `cltv_percent`; the job text says "lesser of appraised value or lowest recent listing price" |
| 2 | `pitia(principal_interest, taxes, insurance, dues=0)` | the monthly housing payment | propagate when any of the first three is not stated; `dues` omitted is 0, `dues=None` is unknown | `(1500, 300, 100, 50)` is 1950; `(1500, 0, 0)` is 1500; `(1500, None, 100)` is None | 5 jobs read DSCR; "annual PITIA" items in the schema backlog; `monthly(amount, 'annual')` gives the inputs |
| 3 | `dscr(rent, debt_service)` | `rent / debt_service`, unrounded | propagate when either is not stated; refuse when `debt_service` is zero or less (a named definition, so two rules cannot divide differently) | `(2000, 1600)` is 1.25; `(1600, 1600)` is 1; `(None, 1600)` is None | `income_stability...calculate_dscr` is in the derivation backlog; 7 jobs name "Calculated DSCR" |
| 4 | `amortized_payment(principal, annual_rate_percent, term_months)` | the level monthly payment | propagate when any input is not stated; refuse when `term_months` is zero or less | `(200000, 6, 360)` is 1199.10 after `round_half_up(x, 2)`; `(120000, 0, 120)` is 1000 (rate zero is principal over term); `(None, 6, 360)` is None | the DSCR denominator when the case holds a loan but no payment ("subject payment amount" is in the backlog) |
| 5 | `interest_only_payment(principal, annual_rate_percent)` | principal times rate over 1200 | propagate | `(300000, 7.5)` is 1875; `(300000, 0)` is 0; `(None, 7.5)` is None | `is_interest_only` read by 10 jobs; "which payment enters the denominator for an interest-only loan" is a policy question (class other), the arithmetic is not |
| 6 | `middle_score(scores)` | the middle of three stated scores, the lower of two, the one of one | propagate when none is stated; refuse when more than three (the rule for more borrowers is policy) | `([700, 720, 740])` is 720; `([680, 710])` is 680; `([None])` is None | `decisioning_score` in the derivation backlog; 13 rules read `representative_score`; "the established decisioning score is not held in a case field" (2 jobs). **Confirm against the guideline text before building** |
| 7 | `multiple_of(value, step)` | whether `value` is a whole multiple of `step` | propagate when `value` is not stated; refuse when `step` is zero or less | `(150000, 50)` is True; `(150025, 50)` is False; `(None, 50)` is None | the loan-amount increment rule is written with inline `Decimal` and `%` (2 rules) |
| 8 | `grid(row_value, column_value, row_uppers, column_uppers, cells, above=None)` | the cell where the first row bound at least the row value meets the first column bound at least the column value; `above` beyond the last bound | propagate when either value is not stated | `(720, 75, [699, 739], [70, 80], [[60, 65], [70, 75]])` is 75; `(739, 80, ...)` is 75 (an edge counts); `(None, 75, ...)` is None | 10 rules write a CLTV grid as an if-ladder; `band` (one axis) is used by only 5 |

What is not here, and why: no `months_since` (`months_between` exists; the missing piece is the date, an extraction gap); no `reserves_months` (it is `ratio(assets, payment)`; the open question is which assets count, a policy answer); no rounding or date entries (nothing failed). Entries 6 and 3 to 5 encode policy-adjacent choices, so their definitions must come from the guideline clause (a person reads it), not from this note; the goldens above are arithmetic checks only.

## 3. The loop

**Round 0 (no spend, done above):** freeze regen-5 as the baseline; the CSV is the per-job state.

**Each round**, in this order:

1. **Fix inputs (no provider).** std entries (sonnet-runtime), the case-schema fields and allowed values (class extraction gap: pack data, and for the seeded Acra pack the change goes through jaci first), the code prompt (use the helpers, derive CLTV and DSCR through std, one canonical purpose spelling), the derived-field declarations that make `cltv_percent` and friends computed.
2. **Pick the jobs.** Not coded (97), plus coded jobs that carry a flag (up to 76). Everything else keeps its rules.
3. **Generate** the job writer once for the policy sets that gain fields (job text changes), then the code writer for the picked jobs only (a `policy_code/regenerate` prompt, 1.0.0, is in the bundle; what it does was not read), then the aligner.
4. **Execute, no provider**: run each rule against the independent cases (below) and the synthetic case in `acra/e2e/e2e_synthetic_case.json` (no loan data).
5. **Classify** each failure with `acra_baseline_by_job.py` extended by one input, the case results: mismatch, unknown from a missing read, gate refusal. The same classes as section 1; a class that no longer shrinks is handed to a person (Acra answer, schema owner) and dropped from the next pick.
6. **Stop** when a round adds less than one point of coded share and no flagged job moves to ok, or when only the Acra and procedure classes are left.

**Pass measure per round (the missing one):** the independent-cases mode of the code writer (`policy_code_cases`; the ledger's "code writer sample independent cases on" row) writes cases without seeing the code; a rule passes when it agrees with all of them. Writing them is the only provider cost in that measure; running them is local.

### Cost per round, from ledger rows [ledger]

All rows are `gpt-6-luna` (flex), regen-5 and the 2026-10-22 sample.

| Step | Ledger evidence | Unit cost |
|---|---|---|
| Job writer, both policy sets | `extract jtbd` 0.0181 + 0.0225 = 0.0406 USD, 28 calls | 0.041 per set rewrite |
| Code writer from jobs | `extract python_jobs` 0.0471 + 0.0879 = 0.1350 USD, 255 calls, 97 rules | 0.0014 per rule |
| Aligner | `extract alignment` 0.0263 USD, 62 calls | 0.026 per round |
| Independent cases | 0.0087 USD, 21 calls, 10 jobs | 0.00087 per rule |
| Whole regen-5, for scale | jtbd 0.0406 + python 0.2029 + python_jobs 0.1350 + alignment 0.0263 | 0.405 USD |

Estimate for a round that rewrites jobs and regenerates 100 jobs (76 flagged, 18 derived, 6 unlinked) and writes cases for them: 0.041 + 100 × (0.0014 + 0.00087) + 0.026 = about **0.29 USD**, **about 0.40 USD** with a 35% margin for a longer prompt (the API list grows from 22 helpers in the regen-5 run to 38 or more; not measured). A failed-only round with no job rewrite: about 0.25 USD. Five rounds: **about 2 USD**, below one regen-5 run times five. Not in these numbers: the loan-2 verifier (0.0224 USD, needs the loan file), a rerun of the policy-to-python path (`extract python`, 0.2029 USD, not needed here), and any model other than gpt-6-luna.

Each run needs a dollar figure typed by the user (CLAUDE.md); a per-round cap of 0.50 USD and a total under 2.50 USD would cover the above.

## Not verified

- The class counts are a keyword reading of `missing_reads`; I read about 20 job rows and the examples fit, not all 97.
- "Unsupplied" is the ledger's own test against the document registry (`pack/ledger.py:612`), so a field a later extraction adds drops out of the count; I did not check the registry itself.
- The six unlinked jobs match orphan rules by name only.
- The 7-job gap between the bundle (195) and coverage (202) is unexplained.
- Costs for the next round scale from regen-5 prompts and 1.1.1; neither the new prompt size nor the case writer on 100 jobs was measured.
- Nothing was run against a case: no rule here is known to pass or fail beyond the 10-rule sample.
