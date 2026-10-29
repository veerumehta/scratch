# Acra jobs: regen-5 (ours) against K-Studio sets

Workbook: `jobs_vs_kstudio_regen5.xlsx` in this folder (sheets: Summary, 1 Sections, 2 Clauses per program, 3 Granularity, 4 Thresholds and readings, 5 Wording and shape, 6 Unmatched and duplicates, 7 Cause labels). Read-only analysis, no run. Decisions needed from the user: `readings_for_decision_regen5.md`.

**Scope.** Ours = regen-5 jobs (acra-regen-5; 114 Standard, 81 Platinum Select). Theirs = K-Studio: Standard v17.0.0 (124), Platinum v7 (108), Standard v9 (123, section counts only). Guidelines: the two consolidated Word documents (123 Standard and 94 Platinum numbered clauses).

**Method.** Each numbered clause was matched to the jobs that check it on each side by reading skill, rules and figures (a similarity ranking proposed candidates; every match was read). Identities are matched by what a job checks, never by mnemonic or section string. Read-only: no run, no provider call.

**Caveat.** Matching is my judgement, one reader, not double checked. Variance between identical runs is unmeasured, so every 'ours' difference below could be run noise. No difference is credited to the model without evidence; where evidence is missing the cause is 'unknown'.

**1 Sections.** Platinum: ours 81 jobs in 8 sections + 'Unassigned Provisions' (9 jobs, outside their closed list); theirs 108 jobs in 7 sections (no Identification Requirements; Loan Program Eligibility 39). Standard: ours 114, theirs 124; ours is heavier in Identification (25 vs 11), Credit (21 vs 13) and Asset (14 vs 6), lighter in Loan Program Eligibility (13 vs 35), Compliance (12 vs 25) and Income (9 vs 16). The same clause lands in the same section for 53 of 80 matched Platinum clauses and 70 of 104 Standard ones (entity clauses: ours Compliance, theirs Loan Program Eligibility; foreign-national documents: ours Identification, theirs Compliance).

**2 Clause to job.** Platinum (94 clauses): both sides have a job on 81, ours only 1, theirs only 11, neither 1. Standard (123): both 105, ours only 0, theirs only 14, neither 4. Theirs covers 92 of 94 and 119 of 123 clauses; ours 82 and 105. Nothing of ours is unmatched to a clause.

**3 Granularity.** Theirs splits finer on entity documents (9 jobs vs 1 on STD-6.10 and PLAT-5.10), matrix tiers (4 vs 1), listed-for-sale loan conditions on Standard. Ours splits finer on listed-for-sale in Platinum (12 vs 5), per-check overlays (escrow waiver, 1 or no score, reserve triggers, foreign-national seasoning). Duplicated checks: ours has 14 of 81 Platinum jobs and 17 of 114 Standard jobs in near-duplicate pairs (the same check twice, e.g. vacant, cash-out lease, rent loss reserve, repatriation); theirs 4 of 108 and 12 of 124 (mostly sibling tiers and products).

**4 Thresholds and readings.** Figures agree on most matched clauses (differences flagged on 21 of 80 Platinum and 38 of 104 Standard, mostly extraction noise). Real differences are on sheet 4: a missing published cap (Condo and Two-Unit 75%), missing footnotes (cash-in-hand), a 55% vs 60% reading, theirs filling interest-only minimums the guideline does not print, DTI alternative kept by ours and dropped by theirs, and aggregate 'governing' jobs only theirs has.

**Gaps in ours.** No job on ARM terms, state prepayment restrictions, One- to Four-Family Rider, REO listing scope, Business Purpose Attestation, cash-in-hand footnotes (both programs); HELOC CLTV rule and excessive lease rent (Standard); previous credit events and the Condo and Two-Unit cap (Platinum).

**Within-pipeline variance.** 35 clause pairs have near-identical text in both guidelines. Ours has a job on one and none on its twin in 3 (excessive rent, business entity eligibility, interest-only payment definition); theirs in 0. This is the only noise estimate available; a repeat run is still owed.

**5 Wording and shape.** Theirs: skills about 2x longer, declarative ('Confirms'), requirement text about 2x longer, 2.5 to 2.9 rules per job in 'condition: TRUE = pass, FALSE = fail' form, loan_metrics (180 and 89) and entity_types on every job, investors FNMA/FHLMC/FHA/VA. Ours: imperative skills, 1.6 to 1.9 rules per job in sentences, no loan_metrics or entity_types, investors Standard/Platinum with NO_CHANGE. These are export and template choices (sonnet-runtime), not model effects.

**First judgement.** Structural: sections, shape, aggregate jobs, bundling. Pipeline or prompt, probably: missing footnotes, table-adjacent and list clauses, values left in data, referral jobs for open questions (ours refers 11 Platinum and 7 Standard jobs; theirs encodes the same questions as conditional outcomes). Model-sensitive and unproven: wording, the interest-only baseline, DTI retention, entity splitting. Unknown: the clause-level drops in R8 to R14. A Claude-model pass of the same pipeline (needs the user's spend approval, not run) would settle these first: dropped clauses and referral jobs, then a repeat run of each model to size noise.
