# plan_acra_measured_code_generation_loop

Author: Virendra Mehta · 2026-11-19 · Status: slice A0 in progress

## Status and modifications

The plan author may read and update this section; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-19 drafted from the comparison of our job-to-code path with codec (kernel-lab `codec-core`), at the user's request. Round 1 of the coverage loop is running (trial pack `acra-regen-7b`).
- 2026-11-19 A0, codec half read (no spend): its clause coverage counts a JTBD clause that names a deliverable as covered when the evaluator source tags it with an ask branch or a reasoned no-ask (`code_generator_agents/clause_coverage.py`), a traceability count at clause level. Its accuracy is the merge gate's eight numbers (`customers/revolution/merge_gate.json`): recall and precision against LOS and SME keys for conditions and calculations. Revolution baseline half not written yet.

## Goal

Move Acra code generation from "a rule is linked" (`coded_share`, 52% in regen-5) to "a rule is right", and raise the share of jobs that get a rule, using the parts of codec that are better than ours, without taking its customer-shaped parts (a fixed catalog, a 252-table ontology, filesystem hand-off).

## Before starting

Read, in this order: `status/Acra/note_acra_code_generation_baseline_and_std_needs_2026-11-19.md` (baseline, cause classes, std table), `plans/note_codec_m1_lessons_for_policy_to_code.md` (codec milestone 1: tiers, hybrid checks, answer keys), `plans/note_kernel_lab_codegen_lessons_for_job_code.md` (worked example per job kind), `plans/plan_revolution_codec_vs_sdk_comparison.md` (the Revolution side by side, which this plan does not repeat), `plans/acra/plan_acra_extraction_inputs_for_code_generation.md` (schema and document inputs, owned by the documents session). This plan adds what those do not: measurement and repair of generated rules on Acra.

## What codec does that we adopt, and what we leave

| Codec | Our slice | Why |
|---|---|---|
| Ground-truth scoring, patch, re-measure, rollback | A1, A2 | We have no per-job pass or fail, so no number says a rule is right |
| Dependency tiers, upstream findings readable | A3 | Derived figures (DSCR, qualifying rent, governing CLTV) feed other rules |
| Demand manifest: fields each rule reads drive extraction | A4 | 72 of 105 coded rules read fields no document yields |
| Gap analysis step proposing schema additions | A5 | Our cause classes are this output, made by hand |
| Completion gate and run fingerprints | A6 | Round 1 lost its client mid-run and could not resume |
| Fixed catalog, 252-table ontology, filesystem hand-off | not adopted | Customer-shaped; our pack schema, gap analysis and Plato runs are the general shape |

## Rules

- No ground truth is invented. Labels come from Acra or the K-Studio reference sets; independent cases are a proxy and are reported as such.
- Never tune on the data a number is reported on: a holdout of jobs or cases is fixed before the first repair.
- Every repair is a patch to one rule, kept only when the measured result improves and no protected case fails; otherwise it is rolled back.
- Spend: every model-backed step is estimated from the ledger first; the total ceiling is 50 USD (typed by the user in this session), stop and report at 40 USD, ask before any round estimated above 5 USD.
- Never restart Plato mid-run; no provider call on loan files.

## Slices

### A0. Facts first (no spend)
- Codec's recorded accuracy on Revolution and Pulte, with dates, and whether its clause-coverage gate counts a rule linked or a rule that passes ground truth. Output: the side-by-side definition table asked for by the coordinator.
- Revolution baseline in the shape of the Acra note (per JTBD coded or not, cause class).
- Acceptance: a note under `status/` with both, citing file and date for every number.

### A1. Per-job result store
- Record, for each generated rule, the independent-case outcomes (passed, mismatched, case count) in the run ledger, and expose them in the coverage report beside `coded_share`.
- Report three figures: linked share, share whose independent cases all pass, share passing a labeled key (when A2 has one).
- Acceptance: regen-7b's report carries all stored outcomes; a rule with a mismatch is listed, not hidden.

### A2. Answer key and repair loop
- An Acra-labeled key for a small set of masked cases and the derived figures (DSCR, qualifying rent, governing CLTV, middle score). Ask Acra through opus-xrepo for the labels; until they exist, the K-Studio reference sets are the weaker key.
- A loop in the SDK, per pack: score, group failures by rule, patch one rule at a time, re-score, keep or roll back, hold back protected passes and a holdout.
- Acceptance: a run records baseline, each kept or rolled-back patch with its measured delta, and the holdout result; promotion into the pack is a separate explicit step.

### A3. Derived reads and tiers
- Let a rule read another rule's reported value (`derived:<rule_id>`), run rules in dependency order, and treat a missing upstream value as unknown. Folds into the work already planned for derived figures; this slice only names Acra's need.
- Acceptance: DSCR and qualifying rent computed once and read by the jobs that use them.

### A4. Demand manifest
- From the generated rules' `reads`, produce the list of fields per rule and per document type, and the fields no document yields (the 72 of 105 count today). Hand it to the documents session as the input list for extraction and schema work.
- Acceptance: the list regenerates from a run with no model call and matches the baseline script's unsupplied reads.

### A5. Gap analysis as a report
- Turn `acra_baseline_by_job.py` into a coverage-report section: cause class per uncoded job, with the schema or document-type change each class would need, for review.
- Acceptance: no ontology or schema is changed by the report.

### A6. Gates and resume
- A regen stage consumes only a complete run whose input hashes match; the client polls existing run ids to resume instead of starting new ones.
- Acceptance: killing the client mid-stage and rerunning finishes the same runs and spends nothing extra.

## Order and spend

A0 first (reads only). Then A1 and A4 (code and report changes, no provider calls beyond a regen). A2 needs labels from Acra before anything else; its model-backed repair rounds are estimated from the ledger (about 0.03 USD per rule rewrite pass) and stay far below 5 USD per round. A3 and A6 wait for the SDK session's slot. Total expected under 5 USD against the 50 USD ceiling.

## Open decisions

- Who supplies the Acra labels, and for how many cases.
- Whether the repair loop lives under `pipelines/policy/` beside the code writer or as its own package (placement decided at A2, not now).
- Whether A3 is part of the existing derived-figures plan or this one.
