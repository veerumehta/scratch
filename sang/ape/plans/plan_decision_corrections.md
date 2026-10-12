# Decision corrections: from a reviewer's correction to a gated pack change

Plan, opus-xrepo, 2026-10-12. Status: written, not started. Decisions the user owes are in section 7.

## 1. Why

A pack learns today only through us: we read results, fix rules and prompts, and rerun trials. The SDK
holds most of a learning loop (`status/done_learning_pipeline_assessment.md`: feedback, signals,
curator, guidance A/B, pass bars, compounding metrics, all composed once in
`tests/test_learning_loop_end_to_end.py`), but that loop produces **guidance assets for chat**
(`InteractiveAgent._apply_guidance`). Case runs read only the pack's fixed playbooks
(`pipelines/steps.py::_run_playbook`). Nothing takes a reviewer's correction of a case decision and
turns it into a better pack.

Principle (decided in conversation, 2026-10-12): for decisions such as credit, **learning means a
reviewed, versioned pack change, never feedback injected into the adjudicator at run time.** Runtime
injection stays the chat path. The loop here is:

```
correction (rule level) -> gold case -> diagnosis (which layer) -> proposed fix -> gates -> new version
```

## 2. What exists to build on

| Piece | Where | Use here |
|---|---|---|
| `Feedback` already carries `decision_id`, `outcome_id`, `pack_id`, `subject_id` | `evaluation/feedback/core.py` | the record a correction rides on |
| Feedback store, API, review, duplicates, history | `evaluation/feedback/`, `server/feedback_api.py`, Plato `/feedback` | storage and review, unchanged |
| Run outcome: `confirmed` + `notes` on a run's Decision | `plato/api/runs.py::run_outcome`, `CaseRunService.record_outcome` | decision-level, coarse; the capture point to deepen |
| Checkpoint resume: `approved`, `decision`, `rationale`, `reason_code` | `plato/api/runs.py::ResumeRequest` | second capture point |
| `feedback_case(record, input=, expected=)` | `evaluation/feedback/learning.py` | correction to gold case |
| `case_run` / `adjudication` eval entities, rule trials | `pack/eval_invoker.py`, `pack/rule_trial.py` | replaying gold cases against a version |
| Pass bars, resumable experiments, noise floor | `evaluation/pass_bars.py`, experiments | the gate |
| Job ledger: jobs, `computable_checks`, `missing_reads`, rule links | `pack/ledger.py` | where a diagnosis lands (schema backlog, job, rule) |
| `override_learning_rate`, `guidance_effectiveness` | `evaluation/compounding.py` | the measure of the loop (adapt to fixes) |

## 3. Phases

### C1. Rule-level correction capture

- `RuleCorrection` (canonical, consumer-neutral): `rule_id`, `given` (verdict and status the run
  produced), `expected` (verdict and status the reviewer says is right), optional `fact_corrections`
  (`{fact: correct value}` when the reviewer says an input was read wrong), `evidence` (document
  alias, page, quote), `answer_disputed: bool` (the reviewer is not sure the policy's answer is
  settled), `note`.
- `Feedback.corrections: list[RuleCorrection]`. This is a typed field, not `metadata`. A correction
  record also sets `decision_id`, `outcome_id`, `pack_id` and the run id. It uses its own
  `FeedbackSource` value (`REVIEWER`, if none fits).
- Capture points:
  - `RunOutcomeRequest` gains optional `corrections`. `record_outcome` writes the Outcome as today,
    plus one feedback record when corrections are present.
  - `ResumeRequest` gains the same field at the checkpoint.
  - Plato's run page gets a per-rule "correct this" control.
- **Bulk mode** (both modes are supported):
  - `GET .../runs/corrections-sheet?run_ids=...&format=xlsx` writes one row per rule outcome of the
    named runs: run id, pack version, rule id, rule title, given verdict and status, blank
    `expected`, `fact_corrections` (as `fact=value; ...`), `evidence`, `disputed`, `note`;
  - `POST .../runs/corrections-import` (xlsx or CSV) reads rows with `expected` filled and writes
    one feedback record per run, the same records the page writes;
  - the import is all or nothing: every row is checked first (unknown run or rule, a run not in
    this tenant, a status outside the pack's vocabulary), and a bad file is refused with a per-row
    report;
  - a row re-imported for a run and rule that already has a correction updates that record
    (revision bump), so one sheet can be edited and re-imported;
  - cells pass through `util.xlsx_safe`;
  - client methods and a CLI command for both.
- Status words come from the pack (`AdjudicationAgentSpec.status_vocabulary` precedent), so a pack
  with other statuses works unchanged.
- Verify:
  - a correction round-trips through the API, the store and the client;
  - an unknown `rule_id` for the run's pack version is refused (422).

### C2. A correction becomes a gold case in the pack's dataset

- On review approval of a correction record (the existing `review_status`), write a gold case into
  the pack's corrections dataset (one per pack, created on first use) via `feedback_case`:
  - **input:** the run's pinned inputs, i.e. the document digests and facts the run used, with the
    reviewer's `fact_corrections` held separately;
  - **expected:** `{rule_id: expected verdict}` for the corrected rules only.
- Scoring a case whose expected names only some rules scores those rules only. Check whether the
  adjudication and path scorers already treat a missing rule as "not scored"; fix them if not.
- An `answer_disputed` correction makes a case tagged `disputed`, kept out of pass bars until
  resolved.
- Verify:
  - an approved correction yields one case;
  - rerunning the old version fails it;
  - a version with the fix passes it (test with a scripted rule).

### C3. Diagnosis: which layer to fix

Deterministic first, a model only for the remainder. For each approved correction:

| Condition (checked in order) | Layer |
|---|---|
| `answer_disputed` | answer key / policy question (to the SME, not the pack) |
| the rule's reads are missing from the run's facts | schema or fact (joins the ledger's `missing_reads` backlog) |
| `fact_corrections` present and the rule recomputed on corrected facts gives `expected` | document reading (extraction or derivation) |
| the rule is code, its facts are right, and it still gives the wrong verdict | rule code or threshold |
| the rule is a procedure (model-judged) | job text or adjudication prompt (model diagnosis picks which, from the rule's reasoning and the evidence) |
| otherwise | unclassified, to a person |

- Re-evaluating code rules on corrected facts uses the existing assessment path, so it needs no
  model call.
- Output: a `Diagnosis` per correction (layer, rule, job via the ledger, short reason) and a ranked
  fix list per pack (counted by layer, then by rule), shown on the coverage page beside the ledger
  and exported with it.
- Verify: one test per row, each built from a scripted run whose cause is known.

### C4. Fix proposals through the gates (after C1-C3 have run on real corrections)

- **Rule-code and threshold diagnoses:**
  - the existing code-from-job writer re-runs for that job, given the corrected cases as examples;
  - the proposal is a draft rule like any other, tried with a rule trial against the corrections
    dataset plus the existing gold set, and held to pass bars;
  - a person publishes.
- **Job-text and prompt diagnoses:** go to the optimization job, which exists, with the corrections
  dataset as its training set.
- **Schema diagnoses:** stay a backlog; a person adds the fact.
- **Measure:** the share of approved corrections whose case passes in a later published version
  (adapt `override_learning_rate` from guidance assets to pack versions).

### C5. Adjudication traces to scorers (independent of C1-C4)

- A case run's adjudication outcome already carries citations.
- Add a scorer: does the cited evidence support the verdict (judge with the rule, the verdict and
  the cited text only).
- Register the existing trace scorers (`trajectory.py`, `operational.py`) in `standard_scorers`
  where an invoker attaches a trace.

## 4. Order and size

C1 and C2 together form one build pass, and C3 is a second. C4 waits until real corrections exist,
because writing fixes before seeing a diagnosis distribution is guessing. C5 can go in parallel.

## 5. Consumer neutrality

- No client or repo names.
- Statuses, verdict words and reason codes come from pack data.
- The fix layers are platform concepts: every pack has facts, documents, rules, jobs, prompts and
  answer keys.
- An external adjudication engine that pins the SDK can post corrections through the same API with
  its own rule ids.

## 6. Out of scope

- Runtime injection of feedback or guidance into case runs.
- Eval-service parity (external invokers, async cases, knowledge snapshots); see
  `plans/note_parity_eval_20261012.md`.
- The chat feedback loop, and the curator tag vocabulary questions in the learning assessment.

## 7. Decisions (the user, 2026-10-12)

1. sonnet-runtime builds it.
2. A correction becomes a gold case only after review approval (the existing `review_status`).
3. One corrections dataset per pack; each case pins the version it corrected.
4. Both modes: the per-rule control on the run page, and the sheet export and import (C1).
