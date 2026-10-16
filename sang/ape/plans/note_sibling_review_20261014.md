# Sibling review, 2026-10-14 (windows per lens)

Note on method: `git log --since=YYYY-MM-DD` keeps the current time of day, which drops early commits. These windows use `"YYYY-MM-DD 00:00"`.

Quiet lenses: policy-workbench has nothing new since 10-13 beyond what is already recorded (ontology refresh reset, cost hint removed). assistant `origin/JAPES_V2` has **not moved**: it still equals `origin/main` (`74d90ad`). (jazzx-assistant is a different repo; its `origin/JAPES-V2`, hyphen, is PR #31, the chat pipeline migration, reviewed.) assistant main does not depend on the japes package. `app/japes/` talks to a hosted japes over queue and HTTP.

## Ranked gaps

1. **Which document wins a field (kernel-lab).** `kernel-lab:codec-suite/workflows/reader_v2/reader2.py`, `domains.py` (on branch `feat/reader-v2-all-tables`, not merged). It routes each paper to table groups using yes/no questions, recall first (threshold 0.2). It then does one small structured read per paper and group. In code it merges rows by key, and each column comes from the **most authoritative paper**: prefix order first, then the paper's date. It also links foreign keys and records provenance for every cell. Measured on 7 loans:
   - values that differ between two runs: 21% → 1.5%
   - gold rows found: about 50% → 98%
   - gpt-6-luna xhigh scored the same as gpt-6-sol medium at about 1/12 of the read cost (worth a note on our model card).
   
   japes: in `jazzx_sdk/pipelines/steps.py` (document_ingest fill, about lines 1323-1334) the **first document read wins**, and a later value that differs only goes into `conflicts`. There is no precedence between documents. Suggestion: precedence as pack data (document class order, then date) on extraction targets.

2. **Assistant eval overrides (assistant + eval-service).** `assistant:app/conversation/models.py::IEvalMessagesInput.validate_agent_config_overrides` (#266) accepts `agent_prompt, llm_id, temperature, reasoning_effort, text_verbosity, max_steps, use_feedback, output_schema, tools, callable_agent_ids, mcp_servers`. It refuses unknown keys and checks each field's type. `chat_handler.py` forwards them to Kernel, and `eval-service:app/evals/assistant_invoker.py::invoke_eval_agent` (2c5a8b2) sends them. japes: `server/eval_api.py::AssistantInvoker` and `::AssistantSessionInvoker` pass only `config["scope"]`. `pack/eval_invoker.py::CaseRunInvoker` already has `modes` and `::AdjudicationInvoker` has `model`/`replicas`. This is the recorded "per-experiment overrides" gap, now built end to end by the siblings. It is cheap to close for the assistant entity type.

3. **Document throughput and hygiene (imdoc v0.3.0-0.5.0).**
   - `imdoc:python/src/imdoc/common/redis_gcra.py`, `adiratelimit/admission.py`: a shared admission limiter across replicas (Redis GCRA) that defers on 429 before calling. japes: `concurrency/rate_limit.py::RateGate` is per process and only reacts to a refusal.
   - `transcription/worker.py`: classify and publish without transcripts, then a queue worker transcribes each source document once. Failures are split into retryable (backoff, max age) and `failed_permanent`. japes `agents/document/agent.py` transcribes inline (cached by hash).
   - #23: every output imdoc uploads is tagged with the pipeline that made it, so derived files never come back as sources. japes has `derived_from` on split parts. Could not determine whether the documents store can return its own outputs as sources.
   - #22: `uploaded_by`, `linked_condition_id` and page range are stamped at publish. japes documents carry no submitter or condition link.
   - #22: classification schedules the largest documents first. japes has no ordering.

4. **Rerun document scope ledger (macer).** `macer:src/macer/jtbd/rerun/document_history.py`, `design/rerun_cost_optimization.md` (branch `swaralee/download-docs`). Each run stores an entry that is never changed afterwards: the documents it downloaded plus the sections it ran. "Considered" walks those entries oldest first, counts only documents routed into sections that were actually run, and narrows to what the loan holds now. A document removed and then re-added reads as new. japes: `pipelines/rerun.py::RerunBasis` copies the items of one prior run. Could not determine whether a rerun that re-judges only some rules marks documents as considered for the rules it did not judge (the gap macer's section narrowing closes).

5. **Subject tokens in prompts (macer).** `macer:src/macer/jtbd/jtbd_agent.py` (aebb4929, branch `akshG/borrower-token-prompts`): the model sees borrowers as `B1`/`B2` tokens, never UUIDs, and code maps the tokens back. japes aliases documents only (`steps.py::_document_alias`). A party or subject alias would go together with the recorded typed-conditions gap (one subject per condition).

6. **Stuck experiments (eval-service #143).** `eval-service:app/evals` ends the read transaction before slow scoring (Azure Postgres closes connections idle in a transaction after 60 s). A failed run now always finalizes its experiment. japes is mostly ahead: `evaluation/_reclaim.py::reclaim_stale_rows` (heartbeat) and `experiments.py` `finish(..., run_token)`. Could not determine whether any japes store holds a transaction open across an LLM call.

7. **Low.**
   - kernel-lab f7ff8020: a dedupe key that read the wrong column names was always empty, so nothing was deduplicated. Lesson for japes: refuse an empty merge key.
   - kernel-lab 63cff60b, cb6d7f7f: verify-not-reject (already recorded).
   - assistant 22f0a82: Keto direct project and team assignment scope. japes P6 user directory is a seam only.
   - assistant 3ffdde8: `MessageTrace` completion. japes `runs.ChatTurnStore` commit/fail/reconcile is ahead.
   - macer `hairsh/refactor-config-mgmt` (from 09-24): layered settings (code < packaged YAML < overlay < env) and a frozen per-invocation `RunConfig` in a ContextVar.

## Where japes is ahead

- Experiments: heartbeat reclaim and run tokens (eval-service only now patches its stuck-run paths).
- Assistant turns: a turn store with interrupt and reconcile (vs assistant's MessageTrace).
- Document split windows and votes, and short document aliases.
- Reruns: `RerunBasis` carries rejected cites and re-judges only the rules a change touches.
- A typed eval invoker per entity, with drafts pinned by digest.

## Could not determine

- Whether `RerunBasis` reruns treat documents as considered for rules they did not re-judge (item 4).
- Whether the japes documents store can hand back its own derived outputs as sources (item 3).
- Whether any japes store holds a transaction open across an LLM or scoring call (item 6).
- Whether reader_v2's per-paper routing beats japes extraction targets on cost: no comparable japes measurement exists.
- macer `main` had no new commits since 10-13. The 10-13 work is on unmerged branches, so adoption is not confirmed.
