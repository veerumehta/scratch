# plan_JAPES_RECIPES_GAPS

Author: Virendra Mehta · 2026-11-06 · Status: not started

## Status and modifications

How to use this section: the plan author may read it and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last. Branch: v2.7.0, nothing pushed. Target: all of this plan lands in 2.7.0 (user decision 2026-11-06).

- 2026-11-07 owner `sonnet-runtime` (Track A). Done: R7 (the four status headers corrected, each checked against the code first); R1 4fbc2631 (optional package and validate stages, SpreadResult, 0.85 for an unresolved key, 0.98 stays ceiling and fallback); R2.5 1e1d1c45, R2.6 65d24faf, R2.2 37d7637e, R2.3 a3be811d, R2.1 3eb74e01; R2.4 37c46c3b (eval case adjudicated the way a case run is; parity test).
- 2026-11-07 R3 done in part: run-health gate (lost parts fail the run, retryable), `Rule.determines` and `derived:<rule_id>` reads with lint (0bb809ed), job code reads determinations (32a4db5c), consolidate pass behind `template.consolidate` (f54dacec). Deferred with reasons: code-yield item 6 (needs a measured failure) and the ledger "left to reviewer" column.
- 2026-11-07 R5 done in part: `remaining_text` with dedupe, zero-width leak patterns refused, `gate.model`. Deferred: usage for streamed turns (needs a usage channel in three provider streams and a billed call to verify).
- 2026-11-07 modification: R2.1 defaults are `unverified_cites: keep` (the documented behavior) and `merge_duplicate_conditions` on.
- 2026-11-07 R4 done in part: sentinel `progress_signals` per pack (e599bd16; `confidence`, `attested_evidence`, default both, so behavior is unchanged). Correction to the plan: `rerun.when_unchanged` is already a pack setting but only the adjudication step reads it; the investigation step ignores the rerun basis, and the basis carries no investigation result to copy. Deferred pending the user's decision (recommendation: defer; the saving is about 0.08 USD per no-change rerun, and a copied answer skips the governor and any re-approval).
- 2026-11-07 R6 done: `KGAgent(judge=ReasoningProposalJudge(...))` scores pending proposals for the `judged` policy (097b010b); a caller's `judge_scores` win, a failed call leaves the proposal proposed.
- 2026-11-07 decision (user): the R4 `when_unchanged` item for the investigation loop is deferred until a measured run shows the cost matters. R4 is closed with the sentinel half done.
- 2026-11-07 left: nothing in this plan. Tenancy (its own plan) is in progress beside it.

## Goal

Close the gaps that make Recipes look thinner than the code underneath it: capabilities that exist but are not wired into their pipeline, pass-through defaults, and planned items that never started. The document processing pipeline has its own plan (`plan_JAPES_DOCUMENT_PROCESSING_PIPELINE.md`).

## Before starting

Verify in this order: the latest CHANGELOG entries, this plan, the plans it cites, then the source. Line numbers are from a read on 2026-11-06.

## R1. Financial spread: wire validation and lineage into the pipeline
- `pipelines/financial/spread.py` returns a `FinancialSpread` and never calls `finance/validation.py` (about 17 detectors) or the per-cell package step in `finance/package.py`.
- Add optional `validate` and `package` stages after `merge`, registered in `pipelines/catalog.py`.
- Replace the fixed `_SOURCED_SCORE = 0.98` (`package.py` around 52) with confidence from the structuring step's own signals; keep 0.98 only as a fallback.
- Add one test that runs against a recorded model response rather than a fake model only.
- Acceptance: a spread run returns detector results and per-cell lineage; a balance-control failure appears in the result.

## R2. ACER (AdjudicationAgent)
1. `_reconcile` passes outcomes through (`agents/adjudication/agent.py` around 170-172). Add a default admissibility pass: drop or downgrade verdicts whose citations failed validation, and merge duplicate conditions across sections (`note_macer_needs_vs_adjudication_agent.md`, "Cross-section condition dedup").
2. Voting is "most adverse wins" (`conductor/strategies/ensemble.py` around 35-62). Add majority vote with a tie order as an option on the spec, matching Macer.
3. The case step passes no planner (`pipelines/steps.py` around 2019-2027). Let the pack choose a planner; keep section binning as the default.
4. The eval path builds one segment with only `model` and `replicas` (`eval_invoker.py`, `AdjudicationInvoker.invoke`). Make it run the same setup as case runs. Needed before `plan_JAPES_MEASUREMENT_BASELINES.md` M3.
5. `resolve_run_mode` is never called; wire it or remove it. Read or remove the declared but unread spec fields (`spec.py` around 102-105).
6. `_emit` sees only `rule_id: status` lines; give it conditions and cited evidence so the narrative is useful.
- Acceptance: tests for each item; an eval run and a case run on the same input produce the same outcomes.

## R3. Policy to Code
- Carry out the open items of `plan_JAPES_2_9_0_JOB_WRITER_COVERAGE_AND_CODABILITY.md`: W3 (cross-program consolidation) and W5 (`derived:` reads so rules can use earlier rules' results, with "left to reviewer" output).
- Carry out `plan_code_yield_hardening.md` item 6.
- Add the run-health gate from `plan_JAPES_MEASUREMENT_BASELINES.md` M2 so lost jobs fail the run.
- Acceptance: a rule can read another rule's result; a run with a lost job is marked failed.

## R4. Cognitive modes and investigation loop
- Sentinel's progress signal is hard-coded (`modes/sentinel.py` around 219, TODO). Make it configurable per pack.
- Default `when_unchanged` for the investigation loop to skip on a no-change rerun where the pack allows it (loan-2 spent about 0.08 USD rerunning with no change).
- Leave simulator, optimizer, influencer and negotiator unbuilt unless a use case asks; keep the catalog honest about which modes run.

## R5. Chat
- `plan_preliminary_remaining_text.md`: add `remaining_text` so the final answer does not repeat the early text.
- Offer a model-based scope check as a pack option alongside the keyword default (`agents/interactive/scope.py`).
- Report usage for streamed turns with no skills (`agent.py` around 850, TODO). Reject leak-check patterns that can only match empty text (`compose.py` around 252, TODO).

## R6. Knowledge graph agent
- The "judged" admission policy needs scores the caller supplies (`agents/graph/agent.py` around 150). Add an optional built-in judge using the reasoning agent.

## R7. Housekeeping
- Update stale status headers that say "not built" for built work: `plan_job_writer_fold_and_data_mapping.md`, `plan_pack_ontology_authoring.md`, `plan_adjudication_evidence_scoping.md`, `plan_rerun_when_unchanged.md`.

## Order

R7 first (minutes), then R2.4 and R1 (they unblock measurement), then the rest of R2, R3, R5, R4, R6.
