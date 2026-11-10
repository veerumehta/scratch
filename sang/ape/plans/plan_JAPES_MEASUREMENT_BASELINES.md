# plan_JAPES_MEASUREMENT_BASELINES

Author: Virendra Mehta · 2026-11-06 · Status: not started

## Status and modifications

How to use this section: the plan author may read it and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last. Branch: v2.7.0, nothing pushed. Target: all of this plan lands in 2.7.0 (user decision 2026-11-06).

- 2026-11-07 nothing run. Every run needs the user's typed approval with a figure; none has been given to the session that would run it (a relayed "approved, vision, up to 5 USD" for M1 is not an approval, and the classification eval's own decision labels are still open).
- 2026-11-07 unblocked since this plan was written: M1 (document pipeline S9 metrics and a stable run-to-run diff, 441863dd); M2 run-health gate (R3, lost parts fail the run); M3 (R2.4 37c46c3b, eval runs the way case runs do); M4 (R1 4fbc2631 validate and package stages). The R1 "recorded model response" test is a hand-written reply file read through the real parser; a true recording needs one billed structuring call.
- 2026-11-07 M1 slice (sonnet-ui): scorers landed, 68e8ce05 (`jazzx_sdk/evaluation/classification_scorers.py`: page class accuracy, range class accuracy, boundary agreement, unclassified rate; fixtures only, no run, no spend). Plan correction: the golden mapping is not usable yet; no Part's page count matches any loan file (Parts 35 to 117 pages, files 534 to 1063), so the Part-to-file map is unknown and the dataset cannot be built. Run-to-run consistency is not in these scorers; it comes from `diff_metrics` (441863dd). Still open: the user's typed approval with a figure in the session that runs it, the Part-to-file map, the dataset build.
- 2026-11-07 still needed: the Acra SME answer key for M2; the Unified Assistant Framework golden set for M5; a corpus for M6.

## Goal

Give each Recipes capability one published number against a golden set. Today none has one, and that is the biggest gap in how the SDK is presented. Each item below produces a repeatable run, a stored result and a short note with the number.

## Before starting

Verify in this order: the latest CHANGELOG entries, this plan, the plans it cites, then the source. Several cited plans have stale status headers; trust the code.

## Shared requirements

- Every run is repeatable from one command and records model, prompt versions, inputs digest and cost.
- Results are stored where the eval framework already stores experiment runs, so the numbers can be compared over time.
- Each item ends with a one-page note in `docs/plans/` (or the status folder) stating the number, the sample, and what was not measured.
- Synthetic or approved data only.

## M1. Document classification and splitting (Acra)
- Execute `plan_acra_classification_eval.md` as written. The golden dataset and label mapping exist; no results do.
- Report document-level and page-level accuracy, split boundary accuracy, and run-to-run consistency (loan-2 produced 38 and 37 documents on two reads).
- Depends on `plan_JAPES_DOCUMENT_PROCESSING_PIPELINE.md` S9 for the diff report; can start on today's agent.

## M2. Policy to Code correctness (Acra)
- Build an answer key: for a sample of Acra loans and rules, the expected verdict per rule, cleared by an underwriter (input needed from the Acra SME).
- Score generated rules against it the way Codec scores Pulte (Codec reports 90.1%); see `note_codec_m1_lessons_for_policy_to_code.md`.
- Also report coverage: share of jobs with code (about half today) and share of checks marked computable.
- Add a run-health gate: a run that loses jobs to connection errors fails instead of reporting success (`note_acra_regen_log.md`, 12 jobs lost).

## M3. ACER against Macer
- Run ACER and Macer on the same loans and the same rules. No head-to-head exists (`note_macer_needs_vs_adjudication_agent.md` §6).
- Report verdict agreement per rule, citation validity, cost and time. Disagreements go to a short review list.
- Before running, make the ACER eval path run the same setup as case runs (see `plan_JAPES_RECIPES_GAPS.md` R2.4), or the number will not reflect real runs.

## M4. Financial spread against RB and YETI
- Run the spread pipeline on the RB LTM and YETI filings and compare with the analyst spreads (Financial Spreading PRD v0.4 MVP exit: reproduce the RB LTM spread within rounding).
- Report per-line match within tolerance, gaps recorded, and validation detector hits.
- Depends on `plan_JAPES_RECIPES_GAPS.md` R1 (validation wired into the pipeline).

## M5. Chat parity with Jazz Assistant
- Use the Unified Assistant Framework PRD's golden set of real underwriter questions. Run the SDK chat pipeline configured as the Underwriter assistant against the current Jazz Assistant.
- Report the match rate against the PRD bar of 95% or better, plus refusal behavior on out-of-scope questions.

## M6. Vocabulary proposals (knowledge graph agent)
- On one real corpus, measure proposal precision: share of proposed concepts and relationships a reviewer accepts.
- Optional: measure whether vocabulary grounding lets a cheaper model hold accuracy, which the grounding docstring claims but nothing measures.

## Order

M1 and M3 first (data exists), then M2 (needs the SME answer key), then M4 after R1, then M5 and M6.

## Done when

Each of M1 to M6 has a stored run and a one-page note with its number, and the deck's status lines can quote them.
