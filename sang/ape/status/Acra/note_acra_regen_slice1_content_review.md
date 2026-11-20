# Acra regeneration after slice 1: content review of 4a and 4b, code status (2026-10-22)

Author: Virendra Mehta
Reads: `scripts/local/coverage/regen_4a|4b/jobs/*_policy.yaml` and `coverage.xlsx`, `note_acra_regen_slice1_results.md`, japes tree at `afb09aa5` (2.6.5). `regen_5` was still in its code phase while this was written (template extra `independent_cases: true`, the cases-in-a-second-call change) and is not read here.

## TLDR

Slice 1 (W1 one unit one section, W2 per-check units and headings, W6a coverage by check) is in the tree, commits `cd891cc0` through `5a9fa5b1` on 2026-10-20, plus `e5a96929` (test cases written without seeing the code), `baf48c67` (`rules_lib.percent`) and `2b5ed223` (lint a rule citing no clause) on the 21st. The structural fix held: no citation spans two sections in either arm, the worst Platinum clause went from 32 jobs to 10, Platinum near-duplicates from 22 to 7 and 10, and the declining-market reduction, the Standard ARM terms and No Ratio now have jobs of their own. Coded share did not move (50 to 55%), which the slice did not promise.

Reading the content rather than the counts turns up three defects that the counts hide, two of them regressions from 3b, all cheap to fix before the next arm:

1. The planner returns section names with their definitions glued on ("Appraisal Review: property eligibility"). Nothing snaps the returned name back to the template's section, so rule ids, section slugs and `section_type` carry the definition text, and the mnemonic prefix lookup fails: 64 of 100 Standard jobs and 55 of 76 Platinum jobs have no mnemonic (3b had one on every job). `JtbdExtractor._taxonomy()` renders "- Name: definition"; `segment()` keys on `_slug(planned.name)`.
2. The matrix tier labels still do not reach the code writer, the one case W2 was written for. For a unit that opens with no marker of its own, `units()` sets `clause.marker = clause.marker or heading`, so `_own_heading()` sees heading == marker and returns empty; `clause_parts` for the three FICO/CLTV tables carry `heading: ""`. The label survives only inside the citation string. In 4b the matrix job was also marked `computable_checks: []` by the writer although it reads all four fields it needs (`total_loan_amount_usd`, `representative_score`, `loan_purpose`, `cltv_percent`), so it has no code at all; 3b at least had the hedged version. 4a split the matrix into three per-tier FICO-floor jobs that are coded (correctly, but FICO floor only) plus an uncoded CLTV matrix job.
3. Platinum has an "Unassigned provisions" section holding four determinations (first-time homebuyer, foreign national, short-term rental, vacant), each a near-duplicate of a job in a named section. These are the units the planner left out, written as a section of their own; they should either be planned or dropped as duplicates.

## Numbers behind the reading

| | Std 3b | Std 4a | Std 4b | Plat 3b | Plat 4a | Plat 4b |
|---|---|---|---|---|---|---|
| Jobs / code rules | 121 / 43 | 112 / 41 | 100 / 44 | 110 / 56 | 79 / 34 | 76 / 38 |
| Guide clauses (STD/PLAT-x.y) cited in some job's clause | 116/123 | 115/123 | 121/123 | 91/94 | 94/94 | 91/94 |
| Jobs with reads and `computable_checks == []` | 56 | 61 | 34 | 19 | 38 | 27 |
| Jobs without a mnemonic | 0 | n/a | 64 | 0 | n/a | 55 |
| Sections used | 11 | | 8 | 11 | | 9 (one is Unassigned) |

Clauses sheet (4b): 80 units, 77 checked, 3 cited only. The three cited-only rows are segment-code rules, not jobs. Note the unit here is the heading-level unit (a section such as "2.1 Matrix as printed"), not the STD-x.y clause; a unit with ten clauses counts as checked when one check cites it. The sheet is a real improvement over citation coverage but is still coarser than the guide's own clause numbering, which is the granularity the hand-built set works at.

Near-duplicate pairs left in 4b (check-text Jaccard >= 0.6) are mostly legitimate siblings now (condotel vs non-warrantable condo caps, vacant rate-and-term vs cash-out), which the metric cannot tell apart. The ones that are real: Standard `reserves_for_fico_below_620` under Asset Assessment and `reserves_below_620` under Credit (identical checks); Platinum `eligible_citizenship_status` under Identification and `borrower_citizenship` under Loan Program Eligibility (identical); short-term rental under Appraisal and under Income; cash-out lease under Income and under Loan Program Eligibility. These are the fold's job (W6 fold change, not in this slice), and they confirm why the fold must compare checks and ignore kind.

Code quality in 4b, spot-read: the per-tier FICO rules in 4a are the first matrix code that is right for what it covers. Partial code still returns True for checks left to a reviewer with no mark in the result (W5). `rule_quality.json` for 4a: one rule with boundary findings, two per program with unprinted figures, which is at or below 3b.

## What to change before the next arm

- Snap the planner's section names to the template: in `SectionSegmenter.segment()`, match `planned.name` to a template section by `section_key` on the part before a colon, or on a prefix match, and use the template's own name for the slug and the segment marker; tell the prompt to return names exactly as listed (the taxonomy line already lists them). Test: a plan returning "Appraisal Review: property eligibility" groups under "Appraisal Review".
- Keep a unit's heading when the unit has no marker of its own: in `units()`, only assign `clause.marker = heading` as a citation fallback, and make `_own_heading()` return the heading whenever the unit's text does not begin with it (or carry `had_marker` on the segment). Test: a markdown table under "Loan amount <= $1,500,000" yields a clause part whose heading is that label, and `_clause_to_encode()` renders it above the table.
- Plan the leftovers: when `leftover` is non-empty, send those units back to the planner once with the taxonomy ("file each of these under one of the sections") before falling back to the Unassigned section; a unit still unplaced is reported, not written as a section.
- Then W4 (computability as a second pass per check): the matrix job, with every field it needs, marked not computable is the clearest case yet that the writer's one-shot answer is the gate to replace.

Measurement note: `acra_regen_measure.py` counts near-duplicate pairs by check text; after W1 most survivors are siblings that share a template sentence. A pair should count only when the two jobs also share a citation or the figures match; otherwise the number will stop moving for the wrong reason.
