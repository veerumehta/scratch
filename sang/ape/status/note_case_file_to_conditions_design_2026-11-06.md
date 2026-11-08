# Design note: `case_file_to_conditions` and `case_update_to_verdicts` (sonnet-runtime, 2026-11-06)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

For the user's decision before anything is built. Read from the `v2.7.0` tree at `65ba37cd`; nothing was run. "Read" means I opened the code; "inferred" is marked.

## 1. What the plan asked for

Catalog plan P5 lists two more presets beside `case_to_verdicts` (built): `case_file_to_conditions` ("a loan or case file to the list of open conditions to clear, each citing its rule and evidence", from Case to Verdicts plus completeness and ACER's structured conditions) and `case_update_to_verdicts` ("re-judge only the rules a changed input affects, carry the rest forward").

## 2. `case_update_to_verdicts` already exists, and is not a step list

A rerun is a submit option, not a pipeline: the submit names the run it follows (`rerun: {of, rejected}`, `pipelines/rerun.py`: `RERUN_KEY`, `RerunBasis`, `when_unchanged` of `continue`, `stop_copy` or `stop_empty`), the adjudication step takes `prior` outcomes and a `focus` and re-judges only what a changed input touches (`pipelines/steps.py` around `_document_focus`, `reconsider=`), and condition ids stay stable across reruns through a watermark (`assign_condition_ids`, `condition_watermark`). Read. A step preset would be the same steps as `case_to_verdicts`, so it adds a name and no behavior. Recommendation: do not add it as a preset; list it in the pipeline catalog as a documented mode of `case_to_verdicts` (one line, no new code) or leave it out.

## 3. `case_file_to_conditions`: most of it exists, three things do not

What exists (read):
- **Structured conditions.** `OutcomeCondition` (`fabric/canonical/policy.py:233`): `id`, `kind`, `title`, `description`, `timing`, `party`, `resolution` (empty while open), `subject_id`, `documents` (registry ids). A pack's `ConditionVocabulary` bounds `kind`, `timing`, `party` and `resolution`; `SubjectRoster` ties a condition to a borrower or property (`agents/adjudication/conditions.py`).
- **The adjudication step** (`kind: adjudication`, `AdjudicationStep`, `pipelines/steps.py`) judges the live rules with ACER, adds each outcome's citations from the documents it read, and its view carries `open_conditions` (`open_condition_rows`: each open condition with its `rule_id`), `denied`, `violated`, `settled`, `indeterminate`, `pending`.
- **Completeness** is the document step's `required_classes`: a required class with no admitted document is recorded in `state.documents.missing` (read at `steps.py:166`, `:712`) and left for review.
- A scorer and a ground kind already read `open_conditions` (`evaluation/adjudication_scorers.py`, `pack/ground_kinds.py`).
- No seed pack uses `kind: adjudication` today (grep over `plato/data` and `tests/data` found none; the DSCR pack uses `investigation`). So the step is built but has not run in a shipped pack manifest.

What is missing:
1. **Missing documents are not conditions.** `state.documents.missing` is a list of class names on the case state; nothing turns each into an `OutcomeCondition` (`kind: document`, `documents: [class]`, a title such as "Provide the credit report"), so the "open conditions to clear" list leaves out what is simply not in the file.
2. **A condition does not cite its evidence.** `open_condition_rows` returns the condition and its `rule_id` but not the outcome's `citations` (`RuleOutcome.citations`, which the adjudication step fills with `SourceCoordinate`s). The plan says "each citing its rule and evidence".
3. **There is no step that assembles the list**, and no named result for it. The adjudication view and the document state both exist, but a run's output has no single `conditions` list.

## 4. Proposal

- A new step kind `conditions` (reads the adjudication view and `documents.missing`; writes `state.conditions`), small:
  - one row per open adjudication condition: the `OutcomeCondition` fields plus `rule_id`, `source: "rule"`, and `citations` taken from the same outcome;
  - one row per missing required class: `kind: document`, `title`, `documents: [class]`, `source: "document"`, the `timing` and `party` the pack's required-class entry names if it names them (inferred: `ClassNeed` has no such fields today; they would default empty), no rule.
  - Stable ids for the document rows from the class name, so a rerun does not renumber them.
- Preset `case_file_to_conditions`: `documents` (`document_ingest`), `assessment` (`policy_assessment`), `adjudication`, `conditions`, `approval` (`human_checkpoint`); no `narrative`. A pack supplies each step's settings as for `case_to_verdicts`.
- The run's output gains `conditions`; the existing `open_conditions` view and its scorer are unchanged.
- Size (estimate): the step and its row builder about 120 lines, the preset and catalog entry about 20, a citations addition to `open_condition_rows` about 10, tests about 150 including a case with a missing document and a rerun that keeps ids. About one slice.

## 5. Open questions for the user

1. Should a missing document be a condition (the proposal), or stay a separate `missing_documents` list beside the conditions? A condition can be cleared (`resolution`) and carried across reruns; a plain list cannot.
2. Is the DSCR pack, which runs `investigation` rather than `adjudication`, the pack to prove this on, or is there another (the 2.6.x loan-file work used ACER on a different pack)? I found no shipped manifest that uses the adjudication step.
3. Who clears a condition and where is `resolution` set? This note leaves clearing out (no route or step writes `resolution` after the run in what I read; inferred, not searched in `plato/api`), so "open conditions to clear" would be read-only in this slice.
4. Keep `approval` (a human checkpoint) in the preset, or end at the conditions list?
5. `case_update_to_verdicts`: documented as a mode of `case_to_verdicts` (my recommendation), or dropped?

## 6. Not verified

Whether the adjudication step runs inside `conductor_pipeline` end to end on any real pack (no manifest uses it); whether any Plato route lets a reviewer set a condition's `resolution`; the `timing` and `party` a required-class entry could carry.
