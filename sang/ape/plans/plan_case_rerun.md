# Case rerun: a run that starts from a prior run of the same case

Status: live. Written 2026-10-04 on `v2.6.1`. Prior art read: `status/done_conductor_pipeline.md`
(case runs, human checkpoint), `plan_plato_authoring_review.md` (reviewer roles). No earlier rerun plan.

## Why

The SDK already has the parts of an incremental, reviewer-driven rerun and no way to reach them from a
case run: `AdjudicationAgent.adjudicate(prior_outcomes=, changed_fields=, rejected=)` (carry-forward,
impact narrowing, rejected evidence, open conditions kept), `RunMode`/`resolve_run_mode`. The
`adjudication` step passes none of them, and `POST /packs/{id}/runs` has no way to say "this is the
same case again". For Acra (an underwriter rejects an appraisal page, a borrower sends a replacement
lease) and clinical intake (a referral packet gains a missing document) the loop is the product: the
second run should cost a fraction of the first, keep what a reviewer already settled, and never
re-clear a rule on evidence a reviewer threw out.

## Decisions (made on judgment, the user stepped away; reversible, listed so they can be changed)

1. **A rerun is a new run, not a mutation.** It names the run it follows: `rerun: {of: <run_id>,
   rejected: {rule_id: [{document, page?}]}}` inside the submit body, beside `documents`. Runs stay
   immutable and the chain (`GET /runs?pack_id&subject_id`) is the history.
2. **Same case, same version, by default.** The prior run must belong to the tenant, be terminal and
   complete, and be of the same pack and subject. The rerun pins the prior run's version and digest
   unless `?version=` says otherwise; a different version runs in full (`FORCED_FULL`): rule ids are
   not comparable across versions, so nothing is carried, though open conditions are still offered by
   rule id.
3. **What changed is computed, not declared.** Changed fields = keys of the submitted record whose
   value differs from the prior run's record; changed documents = documents whose sha256 the prior
   run did not ingest, and the classes they were admitted as are added to the changed fields (rules
   read document text under the class name). No change and no rejection = `NO_OP`: the prior
   outcomes are the result and no model call is made.
4. **Rejections force a re-judgement.** A rule named in `rejected` is impacted whatever changed.
5. **Prior outcomes are copied into the new run's input**, so a resume reads the same state the run
   started from and the prior run can be pruned.
6. **Reuse documents, do not re-read them.** An unchanged document (same sha256, same agent spec
   digest) takes its item from the prior run instead of being converted, classified and extracted
   again (phase 3).
7. **No API for rejecting evidence on its own.** Rejection travels with the rerun that acts on it.
   A checkpoint resolution that carries rejections and starts the rerun itself is out of scope.

## Phases

Each phase is one commit with tests that fail on the old code; a CHANGELOG entry per phase.

### P1: SDK (`jazzx_sdk.pipelines`, `jazzx_sdk.pack.case_runs`)
- `RerunSpec` (`of`, `rejected`) validated in `CaseRunService.submit`; reserved key `rerun` popped
  in `_start` like `documents`, carried on `CaseState.rerun` with the prior outcomes, record and
  document digests (`RerunBasis`).
- `_run_adjudication` passes `prior_outcomes`, `changed_fields`, `rejected` to `adjudicate`;
  `impacted_rules` gains `force` (rule ids always impacted); `resolve_run_mode` decides NO_OP and
  FORCED_FULL.
- A pack with no `adjudication` step refuses `rejected` (nothing to reject against).
- Tests: carry-forward of an unimpacted rule, a changed field re-runs only its readers, a rejection
  forces its rule, NO_OP calls no model, different version runs in full, wrong tenant/subject/
  incomplete prior is refused.

### P2: Plato route and client
- `POST /packs/{id}/runs` accepts the `rerun` object; refusals map to 404 (not found or another
  tenant's) and 409 (prior not complete, other subject).
- `view()` carries `rerun_of`; OpenAPI documents the body.
- `jazzx_plato_client`: `submit_run(..., rerun=)`, `RerunRequest` contract, `RunView.rerun_of`;
  the contract test that holds client and server shapes together.

### P3: document reuse
- `document_ingest` copies a prior item when the document's sha256 and the agent spec digest match;
  fills/conflicts are recomputed from the items either way.

### P4: document focus
- The adjudication prompt says, per rule, which documents are new since the prior run and which pages
  the prior verdict cited, so the model rereads what moved. Segment-level `DocumentFocus` block.

### P5: Plato UI (see the UI note below)
- A run page's "Rerun" action: pick changed inputs, add documents, reject a cite from a verdict's
  citation list; the result shows what was carried, re-judged and settled.

## Not in scope
- Checkpoint-resolution-triggered reruns, cross-case dedup of conditions, a rerun of a failed run
  (resubmit as a new case run), per-rule `rejected` persistence beyond the run that used it.

## Open
- Whether a rerun may change the pack version silently on an activation change between runs
  (decision 2 pins the prior version; the UI should offer "rerun on the active version").
