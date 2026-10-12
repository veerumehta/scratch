# AdjudicationAgent vs macer: function-by-function parity

Date: 2026-10-12. Read-only. japes at `plato` HEAD `1b6972b6`; macer at `f1fd4093` (2026-10-12).

Scope read on the japes side: `jazzx_sdk/agents/adjudication/*`, `agents/reasoning/{agent,grounding}.py`,
`agents/run_kit.py`, `pipelines/steps.py` (adjudication step, lines ~1350-1615), `pipelines/rerun.py`,
`fabric/canonical/condition_evaluator.py` (NL and procedure evaluators), `fabric/canonical/policy.py`,
`pipelines/policy/{jtbd,jtbdset}.py`, `pack/assessment.py` (`policies_in_force`, `through_metrics`),
`conductor/strategies/ensemble.py`, `evaluation/adjudication_scorers.py`, prompt files under
`prompts/files/adjudication/`.

Macer side: `jtbd/jtbd_runner.py`, `jtbd/jtbd_agent.py`, `models/jtbd.py`, `jtbd/summarization_*.py`,
`jtbd/condition_resolver.py`, `jtbd/manual_condition_resolver.py`, `jtbd/cluster_condition_resolver.py`,
`jtbd/condition_dedup/*`, `jtbd/rerun/*`, `jtbd/rerun_orchestrator.py`, `jtbd/evidence_exclusion.py`,
`jtbd/borrower_roster.py`, `agents/{agent_utils,validated_output}.py`, `utils/retry.py`,
`compression/headroom_store.py`, `tools/{documents,repl}.py`, `japes/findings_converter.py` (outline),
`design/japes.md` (head).

Note on "japes mode": macer's `src/macer/japes/main.py` uses japes only as the queue runtime
(`jazzx_sdk.Handler`, `JazzXRuntime`, `QueueSettings`, `KnowledgeHubClient`). It does not call
`AdjudicationAgent` or any `jazzx_sdk.agents.adjudication` symbol. The two engines are parallel
implementations, not producer and consumer.

## 1. Pipeline shape side by side

macer `jtbd_runner._run_jtbd_traced`:
1. Parse `JTBDSet`, filter by requested sections (`validate_requested_sections`), validate metric keys
   (`validate_jtbd_loan_metrics`).
2. Loan program: payload or `loan_program_agent.detect_loan_program` (agent with document tools).
3. Optional orchestrator (`orchestrator_agent.plan_jtbd_groups`, default on): applicability triage and
   domain grouping, fail-open to section grouping; skipped jobs get LLM reasons
   (`explain_skipped_jtbds`) or carried NOT_APPLICABLE reasons on reruns.
4. Per section (`_process_section_traced`): per-investor requirement text (COMMON + overlay, LLM merge,
   Redis-cached), guideline snippet enrichment (cached), then N parallel inferences
   (`_process_single_run` -> `jtbd_agent.verify_all_jtbds`, one tool-using agent call per section).
5. Per-job summarization of N inferences (`summarization_utils.summarize_single_jtbd`, LLM majority
   and minority report, failed inferences excluded, single survivor bypass).
6. Borrower tokens swapped back to UUIDs; section-wide condition ids assigned from a watermark.
7. Cross-section condition dedup (`condition_dedup.pipeline.merge_conditions`) with prior clusters as
   anchors.
8. Rerun: per-job condition resolution (`condition_resolver.merge_conditions_with_previous`), manual
   condition resolution (`manual_condition_resolver.resolve_manual_conditions`), resolution
   propagation onto clusters, cluster resolution against new documents
   (`cluster_condition_resolver.resolve_clusters_with_new_documents`).
9. Serialize merged conditions, CSV/JSON artifacts, MLflow params, metrics and run_metrics.json.

japes `pipelines/steps.py::_run_adjudication` -> `AdjudicationAgent.adjudicate`:
1. Rules in force = `policies_in_force(pack, record)` active rules whose ids are in the assessment's
   outcomes; LIVE partition only; pending rules held back unless documents supply all reads.
2. Document texts by class (`_document_texts`): every admitted document converted again, marked with
   alias `D<n>`, page markers and printed page labels, keyed by its class and each ancestor class.
3. Rerun: `RerunBasis` (prior record, items, outcomes, rejected cites); nothing moved -> prior
   verdicts stand; else `changed_fields` (record fields + document classes) widened by
   `through_metrics`.
4. ONE `SegmentSpec(key=config.id, rules=live)`; `AdjudicationAgent.adjudicate` -> `run_segment`:
   applicability gates, deterministic partition, batchable/evidence-missing split, one
   `ReasoningAgent.run` per replica with no tools, `DeterministicVote` collapse on verdict.
5. Outcomes get `SourceCoordinate` citations (`_citations`) and rule actions; state records
   denied/violated/settled/indeterminate/pending; narrative from `_emit`.

## 2. Function-by-function table

Legend: YES = AdjudicationAgent (or its step) does it; PARTIAL; NO; BUILT-UNWIRED = the SDK has the
primitive but the adjudication path does not call it.

### 2.1 Loading the job set and guidelines

| macer | japes | Status |
|---|---|---|
| `JTBDSet.model_validate`, section filter `validate_requested_sections` (jtbd_runner.py:~960-990) | Jobs are pack policies, imported once by `pipelines/policy/jtbdset.py::import_jtbdset` (procedure rule per job, per-section policy, overlay per program). Runtime filter is the assessment's rules in force, not a section list. | YES (different shape: compile-time import) |
| Metric-key validation against the ontology (`validate_jtbd_loan_metrics`) | `loan_metrics` kept only as `domain_extensions.jtbd` metadata (`jtbdset.py:_META`); never read at adjudication | NO |
| Guideline snippet index, LLM heading selection, Redis cache, browse block (`guideline_enrichment.enrich_jtbd`, `tools/documents.set_block_guidelines_browsing`) | `agents/reasoning/grounding.py::PrecomputedGrounding`, `BrowseGate` exist; nothing in `agents/adjudication` or the step calls them. The adjudication context carries no reference corpus. | BUILT-UNWIRED |
| Per-investor requirement text: COMMON + overlay merged into one requirement by LLM, cached (`jtbd_agent.determine_jtbd_text_for_program`, runner ~L366-395); `NOT_APPLICABLE` and `NO_CHANGE` short-circuits | Overlay becomes a separate rule `{mnemonic}.{program}` judged on the overlay text alone; `NOT_APPLICABLE` becomes a `RuleSuppression` (`jtbdset.py:import_jtbdset`). Not verified: how a superseded base rule is kept out of the adjudication batch (the step takes ids in `state.assessment.outcomes`). | PARTIAL |

### 2.2 Selecting jobs by program / investor

| macer | japes | Status |
|---|---|---|
| `_get_loan_program_result`: payload, else `detect_loan_program` agent with document tools | `pack/assessment.py::_program_policy_ids`: program from `inputs[program_field]` or `default_program`; raises when neither. No detection. | PARTIAL |
| Orchestrator applicability triage, skip reasons, fail-open (`plan_jtbd_groups`, `explain_skipped_jtbds`) | Deterministic `Rule.applicability` gate in `segment.py::_apply_applicability_gate` (NOT_APPLICABLE or INDETERMINATE when blocked). LLM planning seam `planner.py::SegmentPlanner`/`plan_or_fallback` exists, fail-open, but the step passes no planner. | PARTIAL / BUILT-UNWIRED |
| Rerun: previously-NA reasons carried forward, previously skipped jobs reconsidered (`split_previous_classification`) | Prior outcomes carried for rules not impacted (`impact.py::merge_with_carry_forward`); no "reconsider applicability" step | PARTIAL |

### 2.3 Per-job agent runs

| macer | japes | Status |
|---|---|---|
| Work units by section or orchestrator domain (`group_jtbds_by_section`, `rerun/section_bins.sections_as_units`) | `AdjudicationAgent` fans out segments (`fan_out`, `segment_concurrency`), but the step always builds ONE segment of all live rules (`steps.py:_run_adjudication`, `[SegmentSpec(key=config.id, rules=live)]`) | PARTIAL (agent YES, step NO) |
| All jobs in a unit batched into one agent call (`verify_all_jtbds`, `_build_all_jtbds_prompt`) | `run_segment` batches LIVE rules in one prompt (`_render_batch_prompt`) | YES |
| Results matched by position; a missing result is substituted as NOT_APPLICABLE (`verify_all_jtbds`, end) | Matched by `rule_id`; a dropped rule is excluded from the vote and, with no votes, becomes INDETERMINATE `CONDITION_UNEVALUABLE` (`segment.py:run_segment`) | japes stronger |
| N parallel inferences (default 3, `macer_num_parallel_inferences`) | `replicas` (default 1, `spec.py`), `run_replicated_segments` | YES |
| Failed inference rows marked ERROR and excluded from the vote (`summarize_single_jtbd`) | Failed replicas excluded (`replicated.failed_replicas`); failed segment -> `failed_segments`, rules INDETERMINATE in the step | YES |
| INFO (information-only) status | Pack-declared `ProcedureOutcome`; `DEFAULT_OUTCOMES` has PASS, CONDITIONAL, FAIL, NOT_APPLICABLE only (`pipelines/policy/jtbd.py:53`) | PARTIAL (pack data) |

### 2.4 Evidence gathering and document access

| macer | japes | Status |
|---|---|---|
| Tool-using agent: `list_documents`, `read_document` (10 KB read cap, errors rather than truncates), `search_documents` (rg), `read_reference`, `python_repl` (`tools/documents.py`, `tools/repl.py`) | `run_segment` calls `ReasoningAgent.run` with no `tools`. Evidence is inlined: each rule's `reads` rendered by `_batch_evidence` as `context.get(field)` (`condition_evaluator.py`). The step puts whole document texts into context by class. | NO |
| Hard read cap | `workspace.py::enforce_read_cap`/`ReadTooLarge` defined; no caller anywhere in `jazzx_sdk` or `plato` | BUILT-UNWIRED |
| Per-unit access scoping | `EvidenceWorkspace.open()` narrows the ambient scope; the step never sets `workspace` | BUILT-UNWIRED |
| Document identity: filenames with `[Page N]` in free text, post-parsed (`postprocess_observations`) | Structured `EvidenceCite{document, page, ref}`, short aliases `D<n>` (`steps.py:_document_alias`), page markers with printed labels, `_citations` -> `SourceCoordinate` with content hash | japes stronger |
| Evidence duplication | Not applicable (agent reads on demand) | japes defect: `_render_batch_prompt` renders evidence per rule, so a document class read by k rules is inlined k times in the one prompt |
| Rerun document focus: NEW relevant to section, NEW other, cited with pages, uncited count (`rerun/document_focus.RunDocumentIndex.focus_for`, `document_focus_prompt`) | `DocumentFocus{new, cited}` (`segment.py`), built by `steps.py:_document_focus`; no section relevance split | PARTIAL |

### 2.5 Loan metrics and calculation_context

| macer | japes | Status |
|---|---|---|
| Per-job `loan_metrics` with display value, status, indicator, borrower, provenance, `calculation_markdown` (`models/jtbd.LoanMetricValue`); keys validated against the job's declared set (`validate_loan_metric_keys`); `calculation_context` requires `python_repl` to have been called and markdown present (`validate_calculation_markdown`); metric mnemonic to key swap (`_swap_mnemonics_to_keys`); reconciled across inferences (`reconcile_loan_metrics`) | Deterministic metrics only: pack metric definitions evaluated by the assessment (`pack/assessment.py::_derive`), exposed to adjudication as `state.assessment.derived`; `through_metrics` widens rerun impact. Adjudication returns no extracted values. | NO (for LLM-extracted metrics); deterministic computation is japes-side stronger |

### 2.6 Condition generation

| macer | japes | Status |
|---|---|---|
| `ConditionInfo{condition_type (document_missing / verification_required / explanation_required), title, description, timing (6 values), responsible_party (6 values), borrower_ids}` (`models/jtbd.py:94-233`) | `_BatchItemVerdict.conditions: list[str]` (`segment.py:81`); stored as `narrative["conditions"]` strings via `_procedure_outcome` | NO (untyped) |
| CONDITIONAL must carry >=1 condition; other statuses none (`JTBDResult.validate_conditions_match_status`, retried) | No check; a NaturalLanguage rule's `batch_outcome` discards conditions | NO |
| CONDITIONAL counted as open in summary stats | `DEFAULT_OUTCOMES` maps CONDITIONAL to `Verdict.SATISFIED`; the step lists it under `settled` (`steps.py:_run_adjudication`) with its conditions only inside the outcome narrative | PARTIAL (no case-level open-conditions view) |
| Stable condition ids, section-wide, continued from the prior run's watermark (`assign_section_condition_ids`, `prior_condition_id_watermark`) | Conditions keyed by normalized text (`segment.py:_condition_key`) | NO |

### 2.7 One borrower per condition

| macer | japes | Status |
|---|---|---|
| `validate_single_borrower_per_condition`, `validate_borrower_conditions_have_borrowers`, non-borrower party clears ids, ids validated against known LOS borrowers (`validate_borrower_ids_exist`) | none | NO |
| Borrower roster tokens (`BOWW<n>`), schema narrowed to a `Literal` of tokens (`token_scoped_models`), names substituted in free text (`_detokenize`), swap back after summarization; retired borrowers kept (#239, 2026-09-26) | none | NO |

### 2.8 Dedup and clustering of conditions

| macer | japes | Status |
|---|---|---|
| Within-job dedup across inferences by the summarization agent | Collapse picks one winning vote; losing votes' conditions dropped (`DeterministicVote.collapse`) | PARTIAL |
| Cross-section clustering `merge_conditions`: candidate blocks (embedding, HDBSCAN), LLM clustering per block, singleton re-batching, cross-block reconcile, anchors from prior merged set never merge (`split_multi_anchor`), VR/ER reason gate (`reason_gate.apply_reason_gate`), label synthesis for new merged clusters, diverse-member sampling (#273, 2026-10-01); no fallback on embedding failure | none | NO |
| Persisted merged condition set with sources and `merged_from` (`persistence.serialize_merged_conditions`); display-name substitution (#272) | none | NO |

### 2.9 Condition resolution (rerun, manual, cluster)

| macer | japes | Status |
|---|---|---|
| Per-job LLM merge of previous and new conditions: carry, AUTO_RESOLVED with message and evidence ids, ids only from inputs (`condition_resolver.ResolvedCondition.validate_condition_id_is_known`); FAIL bypasses LLM | Same batch call: prompt lists the rule's prior open conditions, model restates or lists `resolved` (`segment.py:_render_batch_prompt`, `_carry_conditions`); `CARRIED_` and `RESOLVED_NARRATIVE_KEY`. No resolution message or evidence per condition. Only for re-judged rules. | PARTIAL |
| Manual (underwriter-created) conditions resolved by a tool agent per condition (`manual_condition_resolver`) | No input for externally created conditions (`RerunSpec` has `of`, `rejected` only) | NO |
| Cluster resolution against new documents, one call per open cluster, cite required, nothing resolved on absence (`cluster_condition_resolver`) | none | NO |
| Resolution propagated to siblings; UW_REJECTED durable until re-evaluated (`condition_dedup/resolution.py`) | none | NO |
| UW-rejected resolution evidence excluded per condition, hard gate (`evidence_exclusion.build_exclusion_index`, `apply_exclusion_hard_gate`) | Rejected evidence per rule: barred in prompt, cites dropped, a verdict resting only on it becomes INDETERMINATE, `resolved` voided (`segment.py:_without_rejected`, `run_segment`); mapped across runs by document id (`steps.py:_rejected_in_this_run`) | PARTIAL (rule granularity, not condition) |

### 2.10 Reruns and document history

| macer | japes | Status |
|---|---|---|
| `determine_run_mode` INITIAL / INCREMENTAL / FORCED_FULL with FindingSet existence reconcile | `impact.py::resolve_run_mode` (adds NO_OP), not called by the step; step uses `rerun.full` (pack version differs) and "nothing moved" | BUILT-UNWIRED (step has its own simpler logic) |
| Impacted sections from new documents and changed LOS entities (`compute_rerun_scope`, `sections_for_documents`) | Field-level impact: `changed_fields` (record + document classes added or removed) through `impacted_rules` on declared reads; `reconsider` forces rules with rejected evidence or never judged | YES (finer grained) |
| `LoanDocumentScope` history of documents each run considered, removals honoured (`rerun/document_history.py`) | `RerunBasis.items` holds the followed run's items only; removed files enter `changed_fields` | PARTIAL |
| Previous finding (status, description, facts, conditions) injected in prompt (`_format_previous_finding_for_prompt`) | Prior cites and prior open conditions only; no prior status or rationale | PARTIAL |
| Stale verdict guard | A re-judged rule that gets no answer becomes INDETERMINATE rather than keeping its old verdict (`agent.py:adjudicate`) | japes stronger |

### 2.11 Retries and validation feedback

| macer | japes | Status |
|---|---|---|
| `ValidatedOutput` with error locations, no values (`agents/validated_output.py`) | `run_kit.ValidatedOutput`, `MAX_FEEDBACK_ERRORS` | YES |
| Output validators that drive the retry: page exists in document (`validate_page_numbers` with `DOCUMENT_PAGE_COUNTS`), no page 0, conditions vs status, metric keys, borrower ids, calculation markdown | `_BatchVerdict` has no validators; bad cites dropped silently (`valid_cites`, `_citations` drops unknown documents and page < 1) | NO |
| Retry sends only a short directive, never the query again (#277, 2026-10-02, `agent_utils.run_agent` `pending_feedback`) | `run_kit.run_agent` adds feedback to the session and then reruns with `current_query = query` (and prefixes the query again after MaxTurns). The installed agents SDK saves run input to the session before the model call (`.venv/.../agents/run.py` ~L952-966), so each schema or truncation retry stores the full batch prompt a second time. | NO (japes defect) |
| One transient classification for every retry site (`utils/retry.py`, #266, 2026-10-12) | `concurrency.is_transient_error` is used by `RetryingModel`, but `run_kit.run_agent`/`run_with_recovery` retry every `APIStatusError` (400/401/404 included) | PARTIAL |

### 2.12 Tool use, compression, headroom

| macer | japes | Status |
|---|---|---|
| `search_documents` output compressed reversibly, `read_reference` recall (`compression/headroom_store.py`) | `tools/agent/tool_compression.py`, `tool_recall.py`, `read_reference` exist; adjudication has no tools | BUILT-UNWIRED |
| `InputFilter` session size cap, `strip_session` | `run_kit.InputFilter`, `strip_session`; `ReasoningAgent.run(max_session_size_kb=)` default 0, adjudication does not set it | PARTIAL |
| `truncation` model setting, default disabled (#279, 2026-10-02) | no truncation setting found in `jazzx_sdk` | NO (minor) |
| Prompt cache key per (run, section, inference) | `run_kit.run_agent` mints a `prompt_cache_key` | YES |

### 2.13 Output contract

| macer | japes | Status |
|---|---|---|
| Statuses PASS / FAIL / CONDITIONAL / NOT_APPLICABLE / INFO (`JTBDResult.status`) | Pack status (procedure outcomes) plus closed `Verdict` and `IndeterminateReason` on every `RuleOutcome` | YES (richer) |
| Ensemble: LLM summarization with majority and minority report, tie order CONDITIONAL > FAIL > NOT_APPLICABLE > INFO > PASS | `DeterministicVote(ADJUDICATION_PRIORITY, status_of=verdict)`; vote tally with dissent rationales on `inputs[VOTES_INPUT_KEY]`. PASS and CONDITIONAL are both SATISFIED, so with replicas > 1 the tie goes to whichever vote `min` meets first, and a CONDITIONAL's conditions can be lost. `LlmFold` exists, unused. | PARTIAL |
| Findings conversion: deterministic finding ids, LLM title, structured `policy_ref`, missing-documents classification per condition, doc_refs, FindingSet/MergedConditionSet upload (`findings_converter.py`) | `RuleOutcome` with `citations` (`SourceCoordinate`), `action`; persistence is the case run output. No guideline reference on the outcome, no title. | PARTIAL |
| Narrative | `_emit` one narrator call (`emit_instructions.md`), failure tolerated | japes only |

### 2.14 Tracing and cost

| macer | japes | Status |
|---|---|---|
| MLflow spans per section, per inference, guideline precompute, borrower roster, merge_conditions; per-section and per-job token/cost (`aggregate_section_metrics`, run_metrics.json); CSV artifacts per inference | `RunTracer` through `fan_out`/`run_replicated_segments`; `tracing.adjudication_name_patterns` maps spans to canonical trace modes; `ReasoningAgent.run` meters each call with prompt refs, sampling, schema digest; step records usage under the `adjudication` mode (`_MeteredService`) | YES (per-segment cost not broken out in the step) |

## 3. What japes has that macer lacks

- Deterministic partition: rules whose evaluator is not LIVE are computed with no LLM call
  (`partition.py`, `segment.py:_evaluate_deterministic`), including Python rules on the isolated executor.
- Deterministic applicability gates with blocked versus inapplicable outcomes (`_apply_applicability_gate`).
- Evidence-missing refusal before any call (`_split_batchable`, `missing_evidence`), and pending rules
  held out of adjudication in the step.
- Rule-id matching of batched answers and INDETERMINATE for dropped rules (macer substitutes NOT_APPLICABLE).
- Closed governance `Verdict` and `IndeterminateReason` beside the pack's status word.
- Structured, page-precise citations bound to content hashes and printed page labels (`_citations`).
- Reviewer-rejected evidence that demotes an answer resting on it (`_without_rejected`).
- Field-level rerun impact through declared reads and metric dependencies; stale-verdict guard; pack-version
  change forces a full run.
- Vote tally with dissent recorded per outcome, and eval scorers `VerdictAgreementScorer` (fails on any
  false pass) and `VoteStabilityScorer` (`evaluation/adjudication_scorers.py`).
- Versioned prompt files with refs metered per call; canonical trace mode tagging.
- Downstream governance in the same case run: governor overrides, `policy_check`, human checkpoint
  (`steps.py`), none of which macer has.
- Documents pinned by sha256 before adjudication reads them (`_document_texts`).

## 4. Ranked gaps (for an engine: pack jobs + loan file in, outcomes with conditions out)

1. **Structured conditions with validated subject.** japes conditions are free strings
   (`segment.py:81`, `condition_evaluator.py::_procedure_outcome`). Absorb: a canonical
   `OutcomeCondition{id, kind, title, description, timing, party, subject_ids}` in
   `fabric/canonical/policy.py`, with the vocabularies (kinds, timings, parties) declared in pack data
   next to the outcomes, and `ProcedureOutcome.carries_conditions` so "CONDITIONAL needs >= 1, others none"
   is checked by a validator on the batch model and retried via `ValidatedOutput`. Subjects come from a
   run roster the step builds from a pack-named record collection, tokenized for the model and swapped
   back after the call (generalizing macer's borrower roster); "at most one subject per condition" is a
   pack flag, not SDK vocabulary. Stable ids continue from a watermark kept on `RerunBasis`.
2. **Evidence access that scales.** The step sends one segment with every live rule and every document's
   full text inline, rendered once per rule that reads it (`steps.py:_run_adjudication`,
   `segment.py:_render_batch_prompt`, `condition_evaluator.py::_batch_evidence`); no tools, no read cap.
   Absorb: segment by policy (section) in the step; render each evidence field once per segment; an
   opt-in tool mode in `run_segment` that hands the reasoning agent `tools/agent/dir_tools.build_source_tools`
   over the run's documents inside `EvidenceWorkspace.open()`, with `enforce_read_cap` and tool compression;
   `PrecomputedGrounding` for a pack's reference corpus. All of these exist and are unwired.
3. **Retry resends the full prompt.** `run_kit.run_agent` re-runs `query` after adding feedback to the
   session (ModelBehaviorError, IncompleteOutputError, MaxTurns, APIStatusError). Fix as macer #277 did:
   send only the directive on retries. Applies to every `ReasoningAgent` caller, not only adjudication.
   Also retry only `is_transient_error` statuses in `run_agent`/`run_with_recovery`.
4. **Case-level condition set: cross-rule dedup with prior anchors.** Nothing in japes. Absorb as
   `agents/adjudication/conditions.py`: partition by subject and party, embed via the SDK's embedding
   layer, LLM clustering per block, anchors never merge, a reason gate for kinds the pack marks as frozen
   on rerun, label synthesis for new merged groups, fail the run rather than persist an undeduplicated set.
   Output a `ConditionSet` on `state.adjudication`.
5. **Condition resolution on rerun.** japes resolves prior conditions only for re-judged rules, without a
   resolution message or cite. Absorb: resolution fields on `OutcomeCondition`, a resolve phase over open
   conditions and the run's new documents (one call per open group, cite required, nothing resolved on
   absence), externally created conditions accepted in the rerun submit, rejected resolution evidence per
   condition (extend `RejectedCite` with a condition key).
6. **Output validators with retry.** No page-range or document-name check on cites; bad cites are dropped
   silently (`EvidenceCite`, `_citations`). Absorb: validators on `_BatchVerdict` reading a page-count map of
   the run's documents through a context variable, retried through `ValidatedOutput`.
7. **Ensemble on pack status, not verdict.** `DeterministicVote(..., status_of=verdict)` ties PASS and
   CONDITIONAL; losing votes' conditions vanish. Absorb: collapse on status with a pack-declared priority
   (the unread `AdjudicationAgentSpec.status_vocabulary` order), and union or `LlmFold`-merge the
   conditions of the votes that share the winning status.
8. **Extracted values with provenance.** No per-rule extraction of displayed values or calculation traces.
   Absorb: a rule declares the fact-catalog keys it reports; the batch item returns values with cites;
   anything computable goes to the existing deterministic metrics or the Python executor rather than a REPL.
9. **Rerun context.** Prior status and rationale not shown; no multi-run document scope history;
   `resolve_run_mode` unused. Medium-low: japes impact is already finer than macer's.
10. **LLM applicability triage.** `SegmentPlanner` seam exists unwired; japes judges every rule without a
    gate. A cost item, not a correctness one; skip reasons would come from the planner.
11. **Program detection and overlay text merge.** Program must be supplied; overlays are judged as separate
    rules. Low: intake can fill the program; the overlay semantics question is listed below.
12. **Spec fields declared but never read.** `AdjudicationAgentSpec.persona` (docstring says it is the
    system prompt; `run_segment` loads `adjudication/instructions` instead), `regime_values`,
    `status_vocabulary`, `mounts`, `segments`. Also `segment_concurrency: int = 6` is a bare literal
    default in `agent.py:63`.
13. Minor: no `truncation` model setting; per-segment cost not broken out in `CaseTrace.usage`.

## 5. Could not determine

- Whether a base rule superseded by its program overlay is excluded from the adjudication batch
  (the step selects ids in `state.assessment.outcomes`; supersession is in assessment metadata).
- The duplicate-prompt behaviour in `run_kit.run_agent` is from reading the code and the installed agents
  SDK, not from a run.
- Whether CONDITIONAL-as-SATISFIED in `settled` changes any decision downstream (governor and checkpoint
  read `denied`, `settled`, `indeterminate`; I did not trace every reader).
- Macer measured quality or cost numbers beyond the one quoted in `validated_output.py`.
- `findings_converter.py` and `japes/main.py` were read by outline and targeted diffs, not in full.
