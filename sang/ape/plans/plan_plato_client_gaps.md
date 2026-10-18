# Plato and client gaps from a consumer audit: standalone document reads, document listing, governed guidance, outcomes outside a run, reaction values, resume and retries

Plan, sonnet-runtime, 2026-10-17, from opus-xrepo's request (source audit: `plan_JACI_PLATO_CLIENT_ADOPTION.md`, section
"Gaps"; it names a consumer, this plan does not). Branch `v2.6.4`. Status: written, decisions in section 8; nothing built.
Consumer-neutral: every route takes its pack, set and subject from the caller.

## 1. What exists (read from the code)

- Documents: `POST /documents` (content-addressed `BlobDocumentStore`; the id is the sha256), `GET /documents/{id}` and
  `.../content`. The store is blobs with a metadata sidecar and **no index**: nothing can list or group.
- Reading a document: only inside a case run's `document_ingest` step (`DocumentAgent.process_blob`, the pack's
  `document_agent.yaml`/registry taxonomy, `fields_schema`, `split`, the engine, metered). The step's loop is fused
  with the case state (filling the record, conflicts), so it cannot be called alone.
- Guidance: `fabric.guidance` has `GuidanceAsset` (draft, approved, deployed, deactivated; content-versioned;
  provenance with a feedback id), `GuidanceStore` (in-process, RAG-backed, eval-service read-only), `GuidanceLifecycle`
  (approve, deploy, deactivate, supersede, rollback), and `modes.evolve.curator.synthesize_bucket` (a model drafts one
  asset from a batch of same-tag improvement signals). The interactive agent applies deployed guidance. Plato
  mounts no guidance route and wires no durable guidance store.
- Feedback: `POST /feedback/{id}/process` exists; the client has no method for it.
- Outcomes: a canonical Outcome needs a `decision_id` and a `trace_id`; `case_runs.record_outcome` writes a reviewer's
  answer to a run's Decision. A case run persists Trace and Decision (`_persist`). The hosted ground kinds are
  `guidelines`, `pack_policy`, `case_run` (by run id) and `case_documents`: none reads a subject's Decision or Outcome,
  which is why a chat scoped to a subject finds nothing without a run.
- Client: `stream_case_run(run_id, from_seq=0)` already reads only what is new. `DEFAULT_REACTION` is the only
  reaction constant; the accepted values are the SDK's `Reaction` (`positive`, `negative`, `neutral`). `_call` raises
  `PlatoError` on any non-2xx and never retries; every mutating call carries an `Idempotency-Key` (one per call).

## 2. Resume and retries (the client behaviours)

- **Resume.** The replay after a resume is the consumer's own `follow_case_run` (it skips from seq 0); the client
  already takes `from_seq`. The fix on the SDK side is a client `follow_case_run(run_id, from_seq=0)` that tracks the
  last `seq`, and on a dropped connection reconnects from it (bounded attempts, a named constant), so no consumer
  writes the loop. Tell the consumer to pass `from_seq` meanwhile.
- **Retries.** An opt-in `RetryPolicy` on `PlatoClient(retry=...)`: attempts, backoff (jittered, a named constant),
  and what is retried. Default **off** (no behaviour change). When on: GETs and a connection that failed before any
  byte was sent are retried; 429 and 502/503/504 honour `Retry-After`; a mutating call is retried only when it
  carries the idempotency key the client already generates (one key reused across the attempts), which governed
  routes replay. `PlatoError` gains `retryable` and `attempts`.

## 3. Items

**C1. Read a stored document on its own (SDK, Plato, client; pack data drives it).**
`jazzx_sdk.pack.document_read.read_document(pack, ref, step=None, ...)` extracts the reading from `_run_document_ingest`
(classify, split, extract with the pack's taxonomy, schema and engine, metered) into a function that returns the items
(`doc_type`, `doc_type_path`, pages, `fields` with their sources, usage) and touches no case state; the step then calls
it. `POST /documents/{id}/read` `{pack_id, version?, step?, split?}` answers 202 with a run (the run store, queue, cost,
stop and stream all apply; a read is minutes for a long file) and `GET /runs/{run_id}` returns the items. Client:
`classify_document(...)` starts it, `read_document(...)` waits. The pack is the only configuration: no model, schema or
taxonomy is named by the route.

**C2. Index and list stored documents (SDK table, Plato, client).** A table `document_record` (tenant, document id,
filename, media type, size, `subject`, `labels`, uploaded at/by), written when a document is stored (migration 0034).
`POST /documents` takes optional `subject` and `labels`; uploading the same bytes again merges the labels. `GET /documents
?subject=&label=&limit=&after=` lists (newest first, cursor); `PATCH /documents/{id}` sets subject and labels on one
already stored. Documents stored before the index exist by id only (a backfill is a small script over the blob prefix,
offered, not run).

**C3. Governed guidance routes (SDK store, Plato, client).** A `DbGuidanceStore` (table `guidance_asset`, versions
immutable, content-addressed as today) implements `GuidanceStore` and is what Plato wires as `fabric.guidance`, so
what the routes deploy is what the agent applies. Routes, per pack: `GET /packs/{pack_id}/guidance?status=`,
`PUT /packs/{pack_id}/guidance` (a draft), `POST /packs/{pack_id}/guidance/{asset_id}/{approve|deploy|deactivate}`
through `GuidanceLifecycle` (its refusals are the answers; author role required), and
`POST /packs/{pack_id}/guidance/from-feedback {feedback_ids}`, which drafts one asset from reviewed feedback through
`synthesize_bucket` (a model call, metered; the draft needs a person's approval). Client: `guidance`, `put_guidance`,
`approve_guidance`, `deploy_guidance`, `deactivate_guidance`, `draft_guidance_from_feedback`, and the missing
`process_feedback(feedback_id)`.

**C4. Record an outcome for a subject outside a run (SDK, Plato, client).** `POST /subjects/{subject_id}/outcomes`
`{pack_id, recommendation, confidence?, rationale?, confirmed?, notes?, observed_at?}` writes a Trace, a Decision and an
Outcome to the canonical store as a case run would (`source: external`, no steps), and answers their ids. A new hosted
ground kind `subject_record` reads the subject's latest Decision and Outcomes from the canonical store (the
subject from `scope`, the tenant as the other kinds read it), so `chat(scope={subject})` is grounded on a result
computed elsewhere. Client: `record_outcome(subject_id, ...)`.

**C5. Reaction values (client).** `jazzx_plato_client.contracts.REACTIONS = ("positive", "negative", "neutral")` and
the client's `turn_feedback` refuses another value with the list; a test holds the tuple equal to the SDK enum's
values so they cannot drift. Export `REACTIONS`.

## 4. SDK, Plato, client, pack data, and what a consumer adopts

- SDK: `read_document`, the `document_record` and `guidance_asset` tables and stores, the `subject_record` ground kind,
  external outcome recording. Plato: the routes. Client: the methods, `follow_case_run`, `RetryPolicy`, `REACTIONS`.
- Pack data: the pack's `document_ingest` step already carries the taxonomy, schema and engine C1 uses.
- A consumer: passes `from_seq` (or calls `follow_case_run`), uses `classify_document` and `documents(subject=)`
  in place of its in-process intake, `put_guidance` and `record_outcome` in place of local seeding, and drops its own
  `Reaction` import.

## 5. Build order (one commit each, tests first, CHANGELOG under 2.6.4)

1. C5 and the client plumbing: `REACTIONS`, `process_feedback`, `follow_case_run`, `RetryPolicy` (smallest, no server work).
2. C2: the index, upload fields, list and label routes.
3. C1: `read_document`, the read route, client methods.
4. C4: external outcome recording and the `subject_record` ground kind.
5. C3: the guidance store, routes and client methods.

## 6. Tests (each fails on the old code; stubs shaped like production)

Reaction tuple equals the SDK enum; a dropped stream resumes from the last seq and yields each event once; retries on
503 with `Retry-After` and on a connect error, not on 4xx, a mutating retry reusing one key, default off; documents
indexed on upload, listed by subject and label, labels merged on a repeat upload, a tenant's list its own; a document
read returns the same classes and fields the case run's step does for the same file (one shared function); the
guidance lifecycle through the routes with each refusal named, and `from-feedback` producing a draft that is not
deployed; an externally recorded outcome grounds a subject chat and a second subject's does not.

## 7. What this does not do

No guidance is deployed or approved by a model; no document is read without a pack; a retry never repeats a mutating call
that has no idempotency key; nothing is backfilled without a script the user runs.

## 8. Decisions for the user (recommendation first)

1. **C1 as a run** (202 and the run store, recommended: reads are long) or a blocking call with a timeout.
2. **C3 store.** A new `DbGuidanceStore` wired as Plato's `fabric.guidance` (recommended: durable, one source for the
   routes and the agent), or the RAG-backed store where a RAG exists.
3. **C4 reads from the canonical store** through a new `subject_record` ground kind (recommended), or only through the
   run-based `case_run` kind (then an external outcome needs a stored run).
4. **Retries.** Opt-in, default off (recommended; mutating retries only with the generated key), or default on for GETs.
5. **C2 subject and labels** are free text the caller sets (recommended), not tied to a pack.

## 9. Built (sonnet-runtime, 2026-10-17, `v2.6.4`)

Decisions taken as recommended. Commits: client plumbing and `REACTIONS` `cccf02d3`; document index `6124f6ff`; standalone
read `83d8a2bf`; outcome for a subject `667f80bc`; guidance store `c74953e4`, routes `43c933d2`, per-tenant wiring
`5fbd2733`. Deviations:

- C4: no `subject_record` ground kind. The SDK already has a `canonical` ground kind (a profile declares `model:
  Decision` or `Outcome` with `where: [[subject_id, eq, <subject>]]`); only the writing was missing, so C4 is the route
  and `record_subject_outcome`, with a test that the existing kind finds what was recorded.
- C3: the per-tenant wiring was not in the first plan: the agent reads the process-wide `fabric.guidance`, which has no
  tenant, so `AssistantRuntime(agent_extra_for=)` and `FabricWithGuidance` give each tenant's assistants their own
  `DbGuidanceStore`. A pack's `guidance_pack_id` on the assistant profile is still what selects which pack's guidance applies.
- C1: the read run is the case-run machinery with a `document_read` input marker (queue key per document; listed
  by `GET /runs?pack_id=&subject_id=<document id>`).
- Guidance and `documents/satisfying` routes are plain (not governed) routes that check their gate before their
  input, as the other pack routes do; their writes carry no idempotency key (a draft `PUT` without an `asset_id` makes
  a new asset each time).
- Canonical objects are keyed by `ontology_id=pack_id` and not by tenant, for recorded outcomes as for run decisions: two
  tenants with the same pack id and subject share a canonical Decision. Not changed here.
- Not built: the backfill script for documents stored before the index (a document is indexed by `PATCH`).
