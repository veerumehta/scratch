# Handoff to the running sessions: slice 1 follow-ups before the next arm (2026-10-22)

Author: Virendra Mehta
Read with `note_acra_regen_slice1_content_review.md` (the findings) and `plan_JAPES_2_9_0_JOB_WRITER_COVERAGE_AND_CODABILITY.md` (corrected today).

## 1. Correction to the source plan and the assessment

Drop the "feed the run the Acra originals" item and the plan's decision 3 as it stood. Both JTBD sets were written from the same consolidated guidelines v1.0; the hand-built set cites the consolidation's own section numbers (§12.2, §3.18, §9.2) and its Appendix B.3. The replacement is a writer-prompt line: a check is written on the text as printed, and a Q-xx question the document raises is recorded on the job as an open item (`open_items` in the `jtbd` extension), never as "do not resolve" steps or a missing-data line that marks the check not computable. Fold it into W4. Nothing else in the plan changes.

## 2. Three fixes before regen 6, all in slice 1 code, with tests

1. Snap the planner's section names to the template. `_taxonomy()` renders "- Name: definition" and the planner returns "Name: definition" as the section name; `segment()` slugs that whole string. Match `planned.name` to a template section by `section_key` on the part before a colon (prefix match as fallback) and use the template's name for the slug and marker; tell `plan_prompt.md` to return names exactly as listed. Effect in 4b: 64 of 100 Standard and 55 of 76 Platinum jobs lost their mnemonic, `section_type` carries definition text, rule ids changed. Test: a plan returning "Appraisal Review: property eligibility" groups under "Appraisal Review" and the job gets a PRE/APR mnemonic.
2. Keep a unit's heading when the unit has no marker of its own. `units()` sets `clause.marker = clause.marker or heading`, so `_own_heading()` sees heading == marker and returns empty; the three FICO/CLTV tables reach `clause_parts` with `heading: ""` and the code writer still never sees the tier labels (the case W2 was written for). Record whether the unit had its own marker, and render the heading whenever the unit's text does not begin with it. Test: a markdown table under "Loan amount <= $1,500,000" yields a part with that heading and `_clause_to_encode()` prints it above the table.
3. Plan the leftovers once more before writing an Unassigned section. 4b Platinum has four determinations under `unassigned_provisions`, each a near-duplicate of a job in a named section. Send leftover units back to the planner with the taxonomy once; a unit still unplaced is reported in the run notes, not written as a section.

## 3. Measurement

`acra_regen_measure.py` near-duplicate pairs: after W1 most survivors are legitimate siblings sharing a template sentence (condotel vs non-warrantable condo caps, vacant rate-and-term vs cash-out). Count a pair only when the two jobs also share a citation or print the same figures, otherwise the number stops moving for the wrong reason. The real duplicates left in 4b (reserves below 620 in two sections, Platinum citizenship in two sections, short-term rental, cash-out lease) are the W6 fold's job and confirm it must compare checks and ignore kind.

The Clauses sheet counts heading-level units (80), not STD/PLAT-x.y clauses (123 and 94). A unit with ten clauses is "checked" when one check cites it. Add the clause-id granularity when the unit text carries clause ids, or say in the Summary that the unit is the heading.

## 4. regen_5

It ran with `independent_cases: true` on top of slice 1 and will carry defects 1 and 2 above. Read its code-quality numbers (cases that disagree, boundary findings, unprinted figures) as the measurement of the independent-cases change; do not read its job counts, mnemonics or the matrix rule as a slice-1 result. Regen 6 after the three fixes is the arm that measures slice 1 properly.

## 5. Then

W4 (computability as a second pass, per check) is next. The 4b matrix job, reading all four fields it needs and marked `computable_checks: []`, is the clearest case for replacing the writer's one-shot answer as the gate.
