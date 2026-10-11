# Acra DSCR: JTBDs against Python rules, programs against each other, ours against Acra's

Note (decides nothing), 2026-10-11, opus-xrepo. Data: `ape/local/coverage/review_20261011/`
(`ours/`, `acra/`, `compare/`, `compare_python_v2/`, each JSON plus xlsx), runs in
`ape/local/coverage/runs_20261011.json`. Supersedes the 2026-10-09 coverage report in
`ape/local/coverage/coverage_report.*`, which had six parts missing and truncated rule code.

## What was run

Four fresh extractions on the local Plato (tenant acra-lending, pack acra-dscr-policy, default model
`flex_gpt-6-luna`), one per guideline and representation:

| Run | Result | Parts | Cost |
|---|---|---|---|
| JTBD Standard `633a72d5` | 68 jobs | 16 of 16 | $0.022 |
| JTBD Platinum `92c87928` | 49 jobs | 12 of 12 | $0.016 |
| Python Standard `66449c2d` + retry `bedb0ad9` | 26 rules | 48 of 48 across the two (1 lost in each, different parts) | $0.064 |
| Python Platinum `6b4bd374` + retry `86577f56` | 27 rules | 42 of 42 across the two (2 lost, then 1, different parts) | $0.047 |

Then three analyses, each pairing by lexical candidates and one model call per item (labels below):
coverage of jobs by Python rules (`acra_coverage_report.py`, with our JTBDs and with Acra's files as
the jobs), and five set comparisons (`acra_compare_sets.py`). Model cost about $0.45 in all.

Labels. Coverage: a job is `covered` (a rule implements all of it), `covered_partial`,
`computable_but_missing` (no rule, but comparisons over schema fields could decide it) or
`not_computable` (needs a document, judgment, a lookup, or a field the schema lacks). Comparisons:
`same` (same requirement, same numbers), `differs` (same requirement, a number or condition differs),
`partial` (overlaps part), `none`.

## Findings

### 1. Our JTBDs cover Acra's requirements almost completely, at coarser grain

| Acra jobs against our JTBDs | same | differs | partial | none | ours matched by nothing |
|---|---|---|---|---|---|
| Standard: 123 vs 68 | 66 | 12 | 41 | 4 | 0 |
| Platinum: 108 vs 49 | 47 | 13 | 45 | 3 | 0 |

- 97% of Acra's jobs have a counterpart in ours, and every one of ours maps to an Acra job: we
  invented nothing and missed little.
- What we miss is the same in both programs: entity-borrower document checks (`BET-NAME-MATCH`,
  `BET-GOODSTAND`, `BET-EIN-TAXID`), plus Standard's cash-in-hand limit (`LFC-CASHHAND`).
- Ours are coarser: about half of Acra's jobs overlap more than one of ours, and many pairs are
  `partial` because one of our jobs bundles several of theirs. That costs nothing for coverage but
  makes one-to-one id matching useless (best text score 0.23 against the matcher's 0.35 floor).
- The 25 `differs` pairs are interpretive, not extraction errors, and most touch Acra's open
  questions. Examples: listed-for-sale needs DSCR >= 1.0 (Acra) vs DSCR >= 1.0 or DTI <= 43% (ours);
  domestic funds seasoning beyond 30 days pending Q-12 (Acra) vs "impose none" (ours); first-time
  homebuyer as "every borrower flagged" (Acra) vs "all applicants never owned" (ours). Each one needs
  a human read; the list is the `differs` rows of the `acra_vs_jtbd_*` sheets.

### 2. Python rules decide a minority of the jobs, and most of the rest cannot be rules on this schema

| Jobs covered by Python rules | covered | partial | computable, no rule | not computable | rules matching no job |
|---|---|---|---|---|---|
| Our JTBDs, Standard (68) | 1 | 29 | 5 | 33 | 2 |
| Our JTBDs, Platinum (49) | 2 | 24 | 4 | 19 | 0 |
| Acra's jobs, Standard (123) | 3 | 33 | 6 | 81 | 4 |
| Acra's jobs, Platinum (108) | 4 | 31 | 8 | 65 | 4 |

- About half of our jobs (44% Standard, 53% Platinum) and a third of Acra's (29%, 32%) are touched
  by a rule, nearly always partly: one rule encodes the computable slice of a job (its CLTV cap, its
  FICO floor) and leaves the documentary part.
- The uncovered majority is mostly not computable: it needs a document's content (entity documents,
  appraisal designations, leases), judgment, or a field the schema lacks. Fields named most often:
  `tax_id_type`, the appraisal's declining-market designation, scheduled closing date, subordinate
  liens for CLTV, gift funds and own-funds amounts. That is the schema backlog if more is to be rules.
- **Computable but no rule**, the concrete gaps for the next extraction or hand-authored rules.
  Ours, Standard: `fico_reserves` (FICO < 620 needs 12 months), `foreign_national_restrictions`
  (no escrow waiver), `loan_amount_and_seller_contributions` (limits, $50 increments, 3% concessions),
  `establish_the_qualification_basis`, `check_ineligible_state` (SD). Ours, Platinum:
  `apply_dscr_housing_history_requirement` (0x30x12), `do_not_calculate_dti_for_dscr_qualification`,
  `state_prepayment_restriction_screening`, `verify_1007_requirement`. Acra's lists (6 and 8) are in
  `acra/coverage_report.xlsx`; they overlap ours (listed-for-sale definition, tradelines, IO limits).
- Rules matching no job: Standard 18 (tradelines met) and 38 (FICO 700 for an escrow waiver) match
  none of our JTBDs; against Acra's files a few more show as orphans, but some of those are retrieval
  misses across vocabularies (rule 31's "SD ineligible" is Acra's `PRE-LOCATION`).

### 3. Standard and Platinum share little verbatim

| Standard vs Platinum | same | differs | partial | none | Platinum-only |
|---|---|---|---|---|---|
| Acra's JTBDs (123 vs 108) | 36 | 37 | 26 | 24 | 10 |
| Our JTBDs (68 vs 49) | 9 | 21 | 26 | 12 | 4 |
| Our Python rules (26 vs 27) | 6 | 7 | 5 | 8 | 8 |

- By Acra's own files, 36 requirements are the same in both programs: that is the candidate core.
  The 37 that differ are overlay material, concentrated in the CLTV matrix (Platinum's 720 cash-out
  cap at 55%, its loan-amount step-down below $350,000 and above $1.5M), vacant property (Standard
  allows it under conditions, Platinum bars it), listed-for-sale (Platinum's DSCR minimum is by
  channel: 1.20 Correspondent, 1.00 Wholesale), escrow waiver (Standard: CLTV <= 80%, FICO >= 700,
  no Foreign National; Platinum: no Section 35 loans), reserves (LTV > 80% vs CLTV > 75%) and
  interest-only limits (80% vs 75%).
- Platinum-only in Acra's files: channel determination and the Correspondent CLTV cap, minimum DSCR,
  cash-out lease checks, housing history 0x30x12, unacceptable fund sources.
- Our sets show fewer `same` than Acra's because our two JTBD runs grouped each guideline
  differently; the requirement-level differences they find are the same ones.

### 4. Defects found (routed to sonnet-runtime with repros)

1. **Standard rule 10 compares a percent field against fractions** (blocking if accepted). The CLTV
   matrix rule tests `cltv_pct <= 0.80`, while `cltv_pct` is a percent (`metrics.yaml`:
   `100 * loan_amount / property_value`; template unit `percent`, which the prompt does show). Every
   loan up to $1.5M would fail the matrix. Its own generated cases share the unit, so they agree with
   it. The coverage report's "numbers in the code but not in the clause" column flags it (0.60 to
   0.85 against a clause printing 60% to 85%), so the check exists in effect; proposed as a static
   check in extraction.
2. **Python extraction drops parts whose code reads an undeclared field** (`fico`, `loan_purpose`,
   `reserves_months`, `gross_rental_income`, `pitia`): about 1 to 2 of 42 to 48 parts per run, every
   run, with no repair turn. Probably also the cause of the 2026-10-09 losses blamed on rate limits.
3. **An extraction run whose task raised stayed "running"** until the stall watchdog failed it.
   Fixed in `46b1ca8d`. The trigger was the local Plato serving a checkout that had switched branch;
   Plato now runs from a pinned worktree (`ape/local/plato_worktree.sh`).

Other numbers worth a look before acceptance (code numbers not printed in the clause): Standard 34
(`250000`, `3000000`), 17 and 36 (`1000000`); most other hits are `1500000` against "$1.5MM".

## Caveats

- Every label is one model's single judgement (`flex_gpt-6-luna`), unreviewed. Counts move between
  runs: with truncated code Standard had 7 jobs fully covered, with full code 1 (most moved to partial).
  Read the categories as sizes, and the rows as a review list.
- Acra's jobs are judged for computability against our schema through their own field names
  (`LoanCore.cltv_percent`); the model maps them by meaning, which is a source of error both ways.
- Candidates are lexical (top 6); a pair that shares no words is missed (rule 31 above).

## Conclusions

1. JTBD extraction is reliable as a requirements inventory: it reproduces Acra's hand-built set with
   no inventions and four or fewer misses per program. The remaining work is grain, not coverage.
2. Python rules are reliable only for the computable slice, and that slice is small on this schema.
   Rule coverage grows from schema fields (documents and appraisal designations as facts), not
   from more extraction.
3. Generated rules need gates before acceptance that today's checks lack: units, numbers against
   the clause, and undeclared reads with a repair turn.
4. For the core/overlay split, Acra's 36 shared requirements are the core candidates; our runs
   should not be used to decide sameness across programs, since their grouping differs per run.

## Process to repeat

1. `ape/local/plato_worktree.sh restart <rev>`: Plato on the commit under test.
2. `python ape/local/acra_rerun_extractions.py`: four runs, two at a time, each retried once if a
   part fails; writes `coverage/runs_<date>.json` (2 to 3 hours on the flex tier, about $0.15).
3. `ape/local/acra_review_all.sh coverage/runs_<date>.json`: both coverage reports and the five
   comparisons (about an hour on flex, about $0.45). It reads proposals from the running Plato, so
   do not restart it until this finishes.
4. Review in the xlsx files: `computable_but_missing` rows (rules to add), `differs` rows of
   `acra_vs_jtbd_*` (interpretations to settle with Acra), Python rows with numbers not in the clause.
