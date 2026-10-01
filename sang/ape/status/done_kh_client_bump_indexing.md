# Note: bump the generated knowledge_hub_client (indexing_enabled)

Status: pending dependency regen. Owner: japes ↔ KH/client owners.

## Why
Knowledge Hub flipped the document-upload server default `indexing_enabled` from **true → false**
(KH commit `6b6bfef`, ~2026-07). japes' `KnowledgeHubClient.create_document` previously rode the old
default, so **japes-uploaded documents are now stored but NOT full-text indexed → RAG/search over them
silently returns nothing.**

## What japes did (prep, this change)
- `KnowledgeHubClient.create_document(..., indexing_enabled: bool = True)` — new param, defaults True
  (japes uploads for RAG, so indexed-by-default is correct).
- `fabric.docs.DocStore.put(..., indexing_enabled=True)` threads it through; mock put accepts it (no-op).
- The upload call **feature-detects** where the flag belongs: it's set on `BodyUploadBinaryDocument` or
  passed to `upload_binary_document.asyncio_detailed` **iff the generated client exposes it**; otherwise a
  one-time WARNING is logged and the flag is silently dropped (no crash). So today the param is accepted
  but **not honored** — uploads are still unindexed until the client is regenerated.

## What remains (the bump)
The installed `knowledge_hub_client` generated package does NOT expose `indexing_enabled` on the upload
endpoint (verified: `…/knowledge_hub_client/api/collections/upload_binary_document.py` takes only
`collection_id, client, body`). To actually honor the flag:
1. Regenerate / bump the `knowledge_hub_client` dependency against KH's current OpenAPI (which now carries
   `indexing_enabled` on `POST /collections/{id}/documents`).
2. Verify whether it lands as a **query param** (on `asyncio_detailed`) or a **body field** (on
   `BodyUploadBinaryDocument`) — the feature-detection covers both, so no japes code change is needed
   after the bump beyond confirming the WARNING no longer fires.
3. Remove the `TODO(kh-client-bump)` markers + this feature-detection once the bump is confirmed (the
   flag can then be passed unconditionally).

## Acceptance
- After the bump, uploading a document via `fabric.docs.put(...)` yields a searchable doc (RAG returns it),
  and the "indexing_enabled … not supported yet" WARNING is gone.

## Grounding refs
- japes: `jazzx_sdk/clients/knowledge_hub_client.py` (`create_document`, `_INDEXING_DEFAULT_HONORED_ONCE`),
  `jazzx_sdk/fabric/docs/store.py` / `mock.py` (`put`).
- KH: upload-default flip `6b6bfef`.
