# Plan: Knowledge Hub client bump (v2 idempotency + RBAC alignment)

Local planning doc (gitignored). Tracks what changes in the japes KH surface when the generated
`knowledge_hub_client` is regenerated against current KH `main`.

## Why

KH `main` (Jul 2026) shipped a v2 API surface that japes can't reach yet because our vendored
`knowledge_hub_client` is generated against an older schema. The japes-side abstractions are already in
place (`fabric.entities.ensure` / `fabric.docs.ensure` / `Repository.ensure`, `CallerIdentity`), designed
so the bump lights up native behaviour **without changing any caller**.

## KH changes to align to

- **Entity idempotency** (`POST /api/v2/reasoning/entities`, `createEntityV2`): uniqueness moved from
  `(collection_id, name)` → `(collection_id, SHA-256(json_value))`; duplicate content → `200`, first →
  `201`; new nullable `content_hash` column. v1 keeps name-uniqueness.
- **Document idempotency** (`POST /api/v2/collections/{id}/documents` + `/newdocuments`): dedup on
  `SHA-256(file bytes)`; duplicate → `200 {"document_id": …}` (id only), first → `201`; DB partial-unique
  index. **v1 now returns `409` on duplicate content** (was silent-dup / `500`).
- **RBAC**: `read_entity` enforces `has_project_permission(read, project_id)` for `project`-scoped
  collections; `public`/`assistant` pass. Audit columns `created_by_user_id`/`updated_by_user_id` on
  `entity`/`document`/`ontology`, populated from `X-User-Id`.
- Entity create gained ontology JSON-schema validation (new error response).

## What the bump changes in japes (no caller-visible API change)

1. Regenerate `knowledge_hub_client` from the current `knowledge_hub_openapi_schema.yaml`.
2. `KnowledgeHubClient.create_entity` / `create_document`: route to the v2 endpoints; map the native
   `200` (idempotent hit) vs `201` (created) into the return so the fabric layer's `ensure()` can read
   `created` from the backend instead of inferring it from a pre-check. Hydrate the id-only `200` doc
   response with a follow-up `get_document`.
3. `fabric.docs.ensure` / `entities.ensure`: once the backend returns native `created`, the client-side
   pre-check becomes a fast-path optimisation rather than the source of truth. Keep the pre-check (still
   correct against v1 + gives us the hash up front); prefer the backend's `created` when present.
4. Confirm `content_fingerprint(bytes)` == KH's `sha256(file)` (it does — plain sha256 hex) so our
   stamped `sha256` key and KH's native one continue to agree.
5. Identity: `CallerIdentity.propagation_headers()` already forwards `x-user-id` — verify the regen'd
   client forwards it on the write paths so audit columns populate, and that `read_entity` 403s surface
   as `KnowledgeHubAccessError` (denied-response hook already covers this).

## Reference implementation: kernel (already on the v2 client)

Kernel has already regenerated its `knowledge_hub_client` with the v2 endpoints and shipped the
idempotent helpers — use it as the reference when bumping japes:

- **Entities** — `app/agent/tools/document_utils/entity_create_v2.py::create_entity_v2_idempotent`
  calls `knowledge_hub_client.api.reasoning_v2.create_entity_v2` and maps status → `(entity, is_new)`:
  201→new, 200→existing, 5xx→`KnowledgeHubServerError` (retried). japes's `WriteOutcome{created,
  content_hash, provenance}` is a superset — have the bumped `create_entity` return native `created`
  so `ensure()` can drop the pre-check to a fast-path.
- **Retry** — kernel wraps the call in `@async_retry_with_backoff(**KH_RETRY_CONFIG)` + a shared
  httpx-error handler. Fold retry-on-5xx into japes's KH client create paths (japes has
  `concurrency.retry_async`).
- **Documents** — kernel `#749` moved the document service to KH v2 (SAS-URL download,
  `indexing_enabled` only, `storage_only` dropped). Mirror in `fabric.docs` on the bump.
- **creator_user_id** — kernel `#735` lets a bulk-create body carry `creator_user_id`, falling back to
  request identity. When KH create bodies gain `created_by_user_id`, thread it from
  `CallerIdentity.user_id` with an explicit-override fallback (the KH analogue of `Repository`'s audit
  stamping).

## Not doing

- Zip upload + async task-status endpoints: no japes consumer. Wire an `AsyncOperation`/task-handle
  abstraction only when a pack needs it.
