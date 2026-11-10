# MACER needs read as adjudication-agent needs

**Status: a note, nothing decided.** It queues no work. Every addition below needs the user's yes, and anything past a fix needs a
plan first. `sonnet-runtime` owns the adjudication code; this note edits nothing in `jazzx_sdk`.

Written 2026-10-31 by sonnet-packs. Lens from the user: the SDK's equivalent of MACER is the adjudication agent
(`jazzx_sdk/agents/adjudication/*`), so MACER needs are read as adjudication-agent needs, and MACER might be supported through it.
Context: MACER consolidation was deprioritized earlier and the workbench still runs MACER; this survey asks whether the adjudication
agent is the right path.

`macer-japes` is a copy of the `macer` repo and was not read. Everything below about MACER is from `/Users/sangit/src/macer`, the
workbench's MACER files (`app/services/macer.py`, `app/api/macer_api.py`, `app/services/macer_compare.py`,
`app/services/findings_compare.py`, `eval_compare/eval_findings.py`) and `docs/engineering-notes/macer.md`.

## How this was checked

- Two read-only surveys by subagents (MACER end to end; what the adjudication agent offers), line numbers carried from them. I
  re-checked four claims myself: `MAX_UNIT_RULES = 10` and `bin_by_section` (`agents/adjudication/planner.py:67,82`); the eval
  invoker builds one segment with every live rule and carries only `model` and `replicas` (`pack/eval_invoker.py:102,147,153`); a
  `NOT_APPLICABLE` verdict exists (`fabric/canonical/policy.py:58`); the segment module has no python tool.
- Nothing was run. No MACER prompt or output was compared with an adjudication run, so every "close fit" below is a reading, not a
  measurement.

## 1. What MACER does

- **Shape.** A queue-triggered job container on the japes SDK: one Azure Storage Queue message (`operation: jtbd_agent`) per
  container, then exit (`macer/japes/main.py:1625-1667`). The workbench never calls it directly; it starts a Flowable process, or an
  Evaluation Studio experiment on that process, that puts the message on the queue.
- **Inputs** (`japes/payload.py:88-198`): the loan collection (documents and LOS entities), the findings and documents ontologies,
  the JTBD set entity, optional guidelines collection, `sections`, `loan_program`, `config`, `force_full_run`,
  `include_previous_context`, `finding_set_id`. It reads all of them from the Knowledge Hub.
- **Unit of work.** A section, not a job: all applicable JTBDs of a section go to one agent call that returns one result per
  requirement in order (`jtbd/jtbd_runner.py:642-652`, `jtbd_agent.py:1648-1763`). This matches the adjudication segment (rules in
  one batched prompt).
- **The agent.** Tool-using (`list_documents`, `read_document`, `read_reference`, `search_documents`, sandboxed `python_repl`;
  `jtbd_agent.py:1934-1940`), strict structured output `JTBDResult` (status PASS, FAIL, CONDITIONAL, NOT_APPLICABLE, INFO;
  observations and facts as strings with filenames and `[Page N]`; conditions; `loan_metrics`). Validators (`models/jtbd.py:372-484`):
  CONDITIONAL needs conditions, metric keys must be in the expected set, cited pages must exist, a computed metric needs its
  `calculation_markdown` and a `python_repl` call. Failures go back to the model by field location, never by value
  (`agents/validated_output.py`); retries are bounded per error class (`agents/agent_utils.py:29-381`).
- **Repeated runs.** N independent inferences per section (default 3, `jtbd_runner.py:483-505`). Failed inferences do not vote.
  Status is voted in code, most frequent wins, ties CONDITIONAL > FAIL > NOT_APPLICABLE > INFO > PASS
  (`jtbd/condition_labels.py:24-45`); a summarizer writes "majority report plus ALTERNATIVE VIEW". Loan metrics are voted
  deterministically per normalized key and borrower set, and every display field is copied from the single winning run
  (`jtbd/loan_metrics_utils.py:496-747`). Each condition is labeled against all runs (nine evidence labels, `Cleared` dropped).
- **Condition work after the vote.** Stable `condition_id`s continue from the highest earlier id; cross-section dedup with
  embeddings, HDBSCAN and an LLM clustering pass, prior clusters as anchors (`jtbd/condition_dedup/`); per-job resolution against
  previous conditions on re-runs; an exclusion index so evidence an underwriter rejected is never reused.
- **Outputs.** Files (`findings.csv` per job and inference, `findings_summary.csv/json`, `merged_conditions.json`,
  `run_metrics.json`, MLflow artifacts) and Knowledge Hub entities written back into the loan collection: `Finding` (one per job,
  deterministic id, `loan_metrics` as an array on it, not rows), `FindingSet`, `MergedConditionSet`
  (`japes/findings_converter.py:1580-2050`). `macerStatus` is not MACER code; it is a Flowable output.
- **Baseline.** Offline report (`macer_compare.py`, `findings_compare.py`, `eval_findings.py:3557`): findings matched by mnemonic,
  regression, incremental benefit and lost coverage, an LLM judge with a verdict cache, HTML, JSON and a reviewer workbook; a
  pinned `MacerBaseline` per (job set, loan); and an inline baseline sent as `expected_output.baseline` under the eval runner.
- **Loan cloning.** MACER writes `Finding`, `FindingSet` and `MergedConditionSet` back into the collection it evaluates, so a shared
  loan accumulated run output (84 Findings against 16 documents on one sandbox collection). The workbench copies the loan first
  (byte-for-byte documents, entities with a deep document-id remap, run guard that trusts the record over the name; the caller's
  token handed through Redis, read once).
- **Needs from the host.** Queue and response queue, security and trace context from the message, the Knowledge Hub client, MLflow,
  Redis (optional), an embedding model, a Flowable process, durable job lanes for compare and clone.

## 2. Per need: what the adjudication agent offers today

Fit: **yes** (offers it), **part** (offers part), **no**. G is general (consumer-neutral), M is MACER-specific.

| Need | Adjudication today (verified, per the survey) | Fit | G/M | Gap and rough size |
|---|---|---|---|---|
| Section as a work unit, many rules in one prompt | `SegmentSpec` batches live rules into one prompt per replica (`segment.py:53,684`); `bin_by_section` groups into `<section>#<n>`, at most 10 rules (`planner.py:67-103`). Default off, set only from a pack's `adjudication.yaml`; a job maps to a unit only through `jtbd.section` metadata | yes | G | Config only. Cap is a rule count, not a size cap (a 400k-character prompt only warns, `spec.py` EvidenceSpec) |
| Job set as rules | A job is a `Rule` carrying `domain_extensions["jtbd"]` (`pipelines/policy/jtbdset.py:329`) | yes | G | None found |
| Per-job expected metric keys and labels | Metrics are deterministic `MetricDefinition`s computed in the assessment step, never produced by the model (`pack/assessment.py:149-167`) | no | M | The model-reads-a-value-from-documents path (`loan_metrics` with `calculation_markdown`, `provenance`) has no analogue in adjudication; it belongs to extraction. Design choice, see section 3 |
| Statuses PASS, FAIL, CONDITIONAL, NOT_APPLICABLE, INFO | Closed `Verdict` plus a pack `status` word (`segment.py:155`, `policy.py:440`); declared outcomes on a rule limit the words; conditions forced or forbidden by `carries_conditions` (`segment.py:371-381`) | part | M | Mapping is pack data; INFO has no verdict (not verified how it would map). `status_vocabulary` on the spec is read only by corrections (`spec.py` TODO `adjudication-spec-fields-unread`) |
| Repeated inferences | `replicas` k per segment, collapse per rule, `votes` tally with `split` and `dissent` (`segment.py:819-842`, `steps.py:1577`). The spec notes k=3 measured zero variance gain at 3x cost | part | G | Collapse is "most adverse wins", not majority; MACER's tie order is a majority vote with a fixed tie order. A pluggable vote is small (about 40 lines); whether MACER's choice is better is unmeasured |
| Voting over metric values | Votes are over verdicts only | no | G (if metrics were model-read) | About 100 lines if ever needed, tied to the model-reads-metrics decision |
| Failure isolation per inference | A failed segment is `failed_segments`, a dropped rule is excluded from the vote, all dropped gives INDETERMINATE (`segment.py:827-834`, `agent.py:70-170`) | yes | G | None found |
| Validated output, repair loop, no data in errors | Schema-repair path through `ReasoningAgent` (`agents/run_kit.py` REVALIDATING); cites checked against run documents and page counts, two feedback rounds (`segment.py:122,402`) | part | G | Not read in detail; whether failures redact values as MACER's wrapper does is unverified |
| Tools over documents, restricted python | `tools` evidence mode: list, read, search over a scratch dir; read cap with a continue footer (`steps.py:1804`, `segment.py:518`) | part | G | No python tool seen in adjudication; MACER's mandatory `python_repl` for computed metrics has no equivalent. Search-output compression is not in adjudication |
| Evidence cites with file and page | `EvidenceCite`, cites bound to run documents and pages (`segment.py:97`) | yes | G | Page bound only where a page count is known |
| Conditions: types, timing, party, stable ids across runs | `_BatchCondition`, prior conditions restated or resolved, ids `C<n>` continue from `condition_watermark`, vocabulary from `condition_vocabulary.yaml` (`segment.py:125-328`, `conditions.py`) | yes | G | MACER-only parts: nine evidence labels per condition, `Cleared` drop, one borrower / one document / one period per condition |
| Cross-section condition dedup | Not in the agent (`_reconcile` is a pass-through, `agent.py:172`) | no | G | Embedding plus clustering plus LLM, with anchors; about 300 lines and a model. Valuable well beyond MACER |
| Rejected-evidence exclusion | Reviewer rejection bars the evidence in the prompt and drops its cites (`segment.py:587-610`) | yes | G | None found |
| Rerun when inputs changed | `rerun: {of: latest}`: diff record fields and document classes, re-judge only impacted rules, carry the rest, `no_impacted_rules` stop without a model call (`pipelines/rerun.py`, `impact.py:31`) | yes | G | Field-name granularity, not document digests; staleness of date-reading rules is a documented gap |
| Result record per case | `CaseRunner` journals steps, `state.adjudication` has outcomes, open conditions, stop reason, usage, provenance (`pipelines/kinds.py:190-215`, `steps.py:2058-2096`) | yes | G | Output shape differs from MACER's `Finding`; see adapter below |
| Output as Knowledge Hub entities | Not in the agent; results live in the case store | no | M | An adapter from `AdjudicationResult` to `Finding`, `FindingSet`, `MergedConditionSet`; about 300 to 500 lines, host side; needs MACER's schema and the hub ontology |
| Isolation of input from writes (loan clone) | No clone operation (dataset `fork` copies a dataset version only, `evaluation/datasets.py:170`) | not needed | G | The defect exists because MACER writes results into the source collection; adjudication writes to the case store, so the whole class of problem is absent unless an adapter writes into the source |
| Baseline pin and compare | Baseline per entity or subject, `select_baseline`, compare with a noise floor (`evaluation/experiments.py:158-266`, `experiment_comparison.py:124`) | part | G | A baseline is an experiment, not a stored expected output; comparison is score-level per case, not finding-level (regression, incremental benefit, lost coverage). See workbench note on set reconcile (G2) |
| Scoring against expected output | `VerdictAgreementScorer` (verdict only), vote stability, condition typing; no scorer for expected conditions, statuses or metrics (`evaluation/adjudication_scorers.py:32-140`) | part | G | About 150 lines for expected status plus expected conditions plus metric comparison, reusing `jazzx_eval_contracts` primitives (not verified end to end) |
| N-repeat orchestration | None: no `repeats=N`; the caller starts N reruns (`ExperimentSpec`); stability and noise floor read them | no | G | About 100 lines in `evaluation/` |
| Eval path parity | `AdjudicationInvoker` builds one segment with all live rules, context is the case record only, and only `model` and `replicas` carry (`pack/eval_invoker.py:102-153`); no binning, documents, grounding or rerun | no | G | The biggest gap for testing a MACER-shaped pack in experiments; about 80 to 150 lines to run the same step the case path runs |
| Borrower identity tokens | `SubjectRoster` maps tokens S1.. back to ids for conditions only; raw record and documents go to the model unredacted (`conditions.py:46`, `segment.py:556`) | part | G | MACER tokenizes and swaps back after the last agent; about 150 lines; also a data-handling question |
| Compaction, prompt-cache keys, cost accounting | Not in adjudication (compaction exists for interactive agents); usage is carried (`steps.py` `usage`) | part | G | Not read in detail |
| Queue job runtime, caller token hand-off, MLflow, durable compare and clone jobs | SDK has `runs/`, queue, MLflow backend; the token hand-off was not found (see the earlier survey) | part | G | Host concerns; already listed in the workbench note |
| Mortgage data model, program and investor model, MACER's metric contract, English and PII prompt rules | Pack content, not SDK | n/a | M | Pack data in a MACER-shaped pack |

## 3. What "support MACER through the adjudication agent" could mean, smallest first

1. **A MACER-shaped pack with config only (no SDK change).** The Pulte job set imported as rules with `jtbd.section` metadata,
   `bin_by_section: true`, `replicas: 3`, a status vocabulary and condition vocabulary matching MACER's, document evidence in tools
   mode. Run it through a case run on one section and compare findings with MACER's output on the same loan by hand. This answers the
   fit question for statuses, conditions and evidence at no SDK cost; it does not answer metrics, voting or the Knowledge Hub shape.
2. **Small SDK additions, all general.** In order: (a) eval invoker runs the same step as the case path (binning, documents,
   replicas, rerun) so experiments can test a MACER-shaped pack; (b) a pluggable vote (majority with a tie order) beside "most
   adverse"; (c) scorers for expected status, conditions and metric values; (d) N-repeat orchestration with a consensus verdict
   (`repeats=N`); (e) digest skip in the eval harness. About 80 to 150 lines each.
3. **Medium additions, general but sizable.** Cross-section condition dedup (embedding, clustering, anchors); evidence labels per
   condition across replicas (Mandatory, Majority, Corroborated, and so on); identity tokenization of the whole prompt; a
   finding-level comparison against a baseline (the workbench's set-reconcile primitives, G2). Each is a plan.
4. **Decision, not code: where metrics come from.** MACER lets the model read metric values from documents with a calculation and
   provenance, and votes them. The SDK computes metrics deterministically from extracted fields. Supporting MACER's metric contract
   inside adjudication would add a model-read metric path the SDK does not otherwise want; the SDK-first answer is to extract the fields
   (document to object) and compute the metric, which changes MACER's output on purpose. This needs the user's call.
5. **Host adapter, MACER-specific.** An adapter from `AdjudicationResult` and open conditions to the Knowledge Hub `Finding`,
   `FindingSet` and `MergedConditionSet` entities (deterministic finding ids, FindingSet updated on re-runs), a queue entry point, and
   the Flowable and Evaluation Studio contract (`macerStatus`, `macerResponse`). Not SDK. About 300 to 500 lines if Plato hosts it.

## 4. Assessment: is adjudication-agent support the right path?

- The overlap is real and the unit of work matches (a section of jobs in one prompt, replicas, voting, conditions with stable ids,
  carry-forward on re-runs, cites, rejected evidence). Steps 1 and 2 are cheap and general, so they are worth doing whatever is decided
  about MACER; they strengthen the adjudication agent.
- The differences that decide it: model-read metrics versus computed metrics; most-adverse voting versus majority with alternative view;
  no cross-section condition dedup; MACER writes Knowledge Hub entities and the SDK writes case results. Supporting MACER's output
  contract exactly is a host adapter plus a metrics decision, not a pack.
- Risk if MACER's behavior must be matched: a different vote rule or a different metric source changes outputs that the Flowable
  process, the workbench comparison and users already read. Any claim of parity needs a measured side-by-side on the same loans,
  and that means a provider run, which needs the user's typed approval with a figure.
- The workbench comparison hides a dropped metric key when another job still produces it, and MACER keeps both rows for a shared key
  (see the earlier answer); a MACER-shaped pack would inherit the Pulte duplicate keys (9 shared, 2 with different calculations).

## 5. Gaps for `sonnet-runtime` (adjudication code), in the order above

1. Eval invoker parity with the case-run path (`pack/eval_invoker.py:102-153`).
2. Pluggable vote across replicas, and a vote over metric values only if metrics become model-read.
3. Scorers for expected statuses, conditions and metric values (`evaluation/adjudication_scorers.py`).
4. `repeats=N` with a consensus verdict in `evaluation/`.
5. Input-digest skip in the eval harness (rerun-when-unchanged exists only for case runs).
6. Token or character cap on a unit (today only a rule-count cap of 10, and a prompt past 400k characters only warns).
7. Spec fields declared and unread (`status_vocabulary`, `regime_values`, `segments`) and `resolve_run_mode` with no caller found.
8. Cross-section condition dedup, condition evidence labels, whole-prompt identity tokenization (plans first).

## 6. What was not verified

- No MACER output was compared with any adjudication output; fit statements are readings of code.
- MACER: the planner, `condition_dedup`, cluster and manual resolver bodies, `entity_extraction`, the LLM title and policy-reference
  converters, most of `eval_findings.py` (sampled), the Evaluation Studio scorer `macer_compare_findings_id` and the clone hook (in the
  eval service, not in either repo), the Flowable BPMN and how `macerStatus` is derived. `macerStatus` is not in MACER code.
- Adjudication: `ReasoningAgent` internals and the schema-repair loop, replication and ensemble bodies, prompts, `fan_out`,
  `job_aggregate.py` and `jtbd_computable.py` (named only), corrections and the correction scorer (likely the closest per-rule gold
  mechanism), `evaluation/variants.py`, the Acra and mortgage packs and their `adjudication.yaml`, and whether INFO maps to a verdict.
- Plato was read only for the runs route and the eval wiring named above.
