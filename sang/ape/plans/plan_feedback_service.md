# Feedback in the SDK; Plato hosts it

**Status:** proposed, 2026-09-26. Read against japes `v2.5.5` @ `51b0b572` and eval-service
`b812172`. Nothing built.

**Prior art:** `plan_sdk_eval_control_plane.md` §5 step 4 (feedback last, single writer by entity),
the Plato charter §5.2-5.4 (Stage 3), `note_LEARNING_PIPELINE_ASSESSMENT.md` (capture path missing,
two formats for approved learning), memory on the MemoryPlane gate (PR #54, unmerged).

## 0. The ask and the shape

Same shape as evaluation: the SDK owns the feedback record, its review lifecycle, its processing
pipeline and router factories; Plato hosts them for its own assistants; eval-service can mount
them later and keep only its kernel, Juno and MLflow plumbing. One writer per fact: Plato writes
feedback about the assistants it hosts, eval-service about kernel agents.

## 1. eval-service's feedback, split

**Generic, into the SDK:**
- the row: entity, invocation, reaction, text, category, source, trace/conversation/message refs,
  JSON metadata; soft delete
- two state machines: processing (unprocessed, validated, summarized, processed, failed, skipped)
  and review (pending_review, under_review, approved, rejected), with status history and edit
  history
- duplicates (mark, list, unmark), and a full-text duplicate hint at intake
- processing: moderation flags, context summary, overall summary, quality, actionable item,
  embeddings; resumable by processing status
- per-entity config with a global default: models, prompts, thresholds, max results, quality on/off
- retrieval: approved feedback similar to a turn, lexical and semantic
- list with filters, export (csv/ndjson), aggregate by field or time bucket
- feedback into learning: a feedback item into a dataset case, and approved feedback into
  `optimize_prompt` (which already takes `feedback=`)

**Specific, stays out:** kernel context fetch and `metadata.kernel.*`, the compat router and YAML
config, backfill state, Juno analysis and assist-edit, MLflow assessments and trace tags, the
assistant `message_traces` correlation, Azure blob and queue, source-url ID extraction.

## 2. What the SDK has

`evaluation.feedback` (`Feedback`, `FeedbackStore`, `InProcessFeedbackStore`), `feedback_db`
(`DbFeedbackStore`, table `japes_feedback`, append/list only), `feedback_sink`
(`EvalServiceFeedbackSink`), `feedback_quality` (`assess_feedback_quality`,
`extract_actionable_items`, `structure_feedback`), `feedback_render`, `feedback_text`,
`eval_service_adapters`, and `fabric.guidance` (approved learning as `GuidanceAsset`, with an
eval-service-backed store). **No embedding layer anywhere in the SDK.** Plato's
`api/feedback.py` pass-through is not mounted by any shipped wiring.

## 3. SDK work

1. **The record and its lifecycle.** `FeedbackRecord` = the submitted `Feedback` + entity +
   processing and review status + processor outputs + duplicate link + soft delete. A
   `FeedbackRepository` protocol: create (idempotent on `feedback_id`), get, list (filters,
   limit), edit text (history row, resets processing and review), set review status (history
   row, lifecycle-checked), soft delete, mark/unmark duplicate, status history. `Db*` on
   `fabric.db`, grown from `japes_feedback` (see F-e).
2. **Config.** `FeedbackConfig` per `(tenant, entity)` with a tenant default: summary and
   embedding models, prompts, thresholds, max results, quality on/off, categories. Resolved
   entity-first.
3. **Processing.** `FeedbackProcessor` with the host seam `FeedbackContextProvider` (turn text for
   a record: Plato reads its own conversation store; eval-service reads kernel). Stages as
   eval-service has them, blocking vs best-effort likewise, resumable. Moderation and summaries
   through the SDK LLM layer; quality and actionable item reuse `feedback_quality`. Runs as a job,
   not in the request.
4. **Retrieval.** `similar_feedback(entity, turn, top_n, threshold)` over approved, non-deleted
   rows. Lexical first (portable across sqlite and Postgres); semantic through `fabric.rag`
   (F-b).
5. **Router factories** in `server/feedback_api.py`: create, list/filter, get, edit, delete,
   review status, history, duplicates, similar, config get/put, export, aggregate. Mount bare in
   tests.
6. **Into learning.** `feedback -> GoldenCase` into an eval dataset (the caller supplies expected,
   as eval-service does); approved feedback as `optimize_prompt(feedback=)` for an optimization
   job.

## 4. Plato

- Mount the feedback routers per tenant; review writes gated like authoring.
- `FeedbackContextProvider` over Plato's conversation store (conversation_id / message_id on the
  record).
- `job:feedback-process` drains unprocessed rows (or the eval reclaim pattern: in-process with a
  heartbeat and a sweep).
- Migration adding the tables. **Retire the "Plato owns no feedback table" invariant and its test
  in the same change**, and replace the pass-through module.

## 5. Order

**Progress (v2.5.5, local):** step 1 `313e754c`; step 2 `6bd64d62`; step 3 `2886ea6a`; step 4 `6971cacc`; step 5 `304a7f8e`; step 6 `b7f202fc`; step 7 `1e19dd8c`.

1. Record, repository, lifecycle, history, duplicates; router (create/list/get/edit/review/delete).
2. Config, resolved per entity.
3. Processing pipeline (lexical duplicate hint, moderation, summaries, quality, actionable), as a
   job.
4. Plato hosting: routes, context provider, job, migration, invariant retired.
5. Lexical similar-feedback retrieval; export and aggregate.
6. Feedback into datasets and optimization jobs.
7. Semantic retrieval through `fabric.rag` (F-b).
8. Injection of approved feedback into Plato turns (F-c).

## 6. Decisions (taken 2026-09-26: the recommendations, with F-b as below)

- **F-a. Plato stores feedback for its assistants**, replacing the pass-through and retiring the
  Phase 6 invariant. Recommended: this is what "incorporate" means, and the one-writer rule holds
  by entity.
- **F-b. Semantic retrieval: through `fabric.rag`, not a new embedding layer.** `RAGStore` wraps
  Knowledge Hub, which embeds and searches server-side (vector/hybrid); the mock KH matches
  substrings, enough for tests. Approved feedback is indexed as one KH document per record in a
  collection per `(tenant, entity)` (KH search has no metadata filter, so the collection is the
  scope), added on approval and removed on reject, delete or edit. Lexical stays the default and
  the fallback when no KH is wired. Decided 2026-09-26.
- **F-c. Injecting approved feedback into turns.** The 2026-08-07 decision queued the "feedback
  spine" behind PR #54 (`MemoryPlane`), still unmerged. Recommended: build steps 1-7 now (they are
  the record and its processing, not memory), and keep injection (step 8) behind #54 as decided.
- **F-d. Config storage.** Recommended: DB per tenant and entity, editable by operators, as
  eval-service does; pack YAML can seed it later.
- **F-e. The table.** Recommended: grow `japes_feedback` into the full record (one table, the
  prefix already keeps it clear of eval-service's `feedback`), with `japes_feedback_history` and
  `japes_feedback_config` beside it. `DbFeedbackStore`'s append/list keep working over it.
- **F-f. Category vocabulary.** eval-service's is free text constrained by config; the learning
  pipeline's router has a closed tag set (the assessment's finding 2). Recommended: free text plus
  per-entity allowed categories in config, as eval-service does; reconciling with the router's
  tags is separate.
