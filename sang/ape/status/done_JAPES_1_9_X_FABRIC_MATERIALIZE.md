# JAPES 1.9.x: DocStore.materialize() and EntityStore Pagination

Author: Virendra Mehta
Created: Wednesday, July 1, 2026
Status: Draft for build
Repos affected: `japes/`

## Why this plan exists

The download-then-agent pattern — query entities from KH, download their documents to a
local directory, expose that directory to an agent via `build_directory_tools` — is used
by MACER today and will be used by Jazz Assistant and any future solution that grounds
agents in KH-backed document sets.

Currently MACER implements this directly against `KnowledgeHubClient`, bypassing the
fabric entirely (`jtbd_setup.py` calls `hub_client.read_entities(odata_filter=...)` and
`hub_client.download_documents(...)` directly). Jazz Assistant would have to replicate the
same logic. The SDK should own this so neither does.

Confirmed against current code:

- `fabric.entities.EntityStore` has `list(odata_query=...)` and `filter(...)` for entity
  queries but no auto-pagination. Large collections (>500 entities) require the caller to
  loop manually — MACER has its own `paginated_read_entities` utility for this.
- `fabric.docs.DocStore` has `download(collection_id, document_ids) -> bytes | None`
  returning raw archive bytes, not individual named files. No `materialize_to_dir()`
  exists.
- `KnowledgeFabric` exposes `fabric.entities` and `fabric.docs` as first-class surfaces;
  direct `fabric.kh` / `KnowledgeHubClient` calls are the documented escape hatch for
  operations not covered by fabric stores.

## What this plan does NOT change

- Does not change `EntityStore.list()`, `filter()`, or any existing method signatures.
- Does not change `DocStore.put()`, `get()`, `download()`, or any existing method.
- Does not add entity querying logic to `DocStore` — entity querying stays with
  `fabric.entities`. `materialize()` accepts pre-fetched entity dicts.
- Does not add `DocType` vocabulary for domain-specific document types (loan docs,
  guidelines, LOS entities). Those belong in domain pack extension metadata per the
  existing `DocType` docstring.
- Does not add MLflow tracing (MACER applies tracing at its own layer; the SDK primitive
  is tracing-agnostic).
- Does not add retry logic on individual document downloads — that belongs in the KH
  client layer, not in DocStore.

## Phase 1: EntityStore.list_all() — auto-paginating list

MACER's `paginated_read_entities` loops `list(skip=N, limit=500)` until an empty page
signals completion. This is a generic, reusable pattern that belongs in `EntityStore`
rather than being re-implemented by every caller.

Per-file changes:

| File | Change |
|---|---|
| `jazzx_sdk/fabric/entities/store.py` | Add `list_all()` method |

```python
async def list_all(
    self,
    *,
    odata_query: str | None = None,
    orderby: str | None = None,
    order_direction: str | None = None,
    page_size: int = 500,
) -> list[dict[str, Any]]:
    """Paginate through all matching entities, returning the complete list.

    Calls list() repeatedly with skip/limit until an empty page signals
    completion. Use instead of list() when the result set may exceed
    a single page (collections with hundreds or thousands of entities).

    Args:
        odata_query: OData filter expression (e.g.
            "collection_id eq '...' and entity_type eq 'ClassifiedDocument'").
        orderby: Field to order by.
        order_direction: "asc" or "desc".
        page_size: Entities per request (default 500).

    Returns:
        Complete list of all matching entity dicts.
    """
    results: list[dict[str, Any]] = []
    skip = 0
    while True:
        page = await self.list(
            skip=skip,
            limit=page_size,
            odata_query=odata_query,
            orderby=orderby,
            order_direction=order_direction,
        )
        if not page:
            break
        results.extend(page)
        if len(page) < page_size:
            break
        skip += page_size
    return results
```

Acceptance test: mock a KH that returns two pages of 500 then an empty page; assert
`list_all()` returns 1000 entities and made exactly three calls.

## Phase 2: DocStore.materialize() — download entities to a named local directory

`materialize()` takes pre-fetched entity dicts (from `fabric.entities.list_all()`),
downloads each entity's document by a caller-supplied ID field, writes named files to a
local directory using a caller-supplied naming function, and returns a list of
`MaterializedDoc` records for citation building and mapping files.

Separation of concerns is preserved: the caller queries entities via `fabric.entities`;
`DocStore.materialize()` owns only the download-and-write step.

New dataclass: `MaterializedDoc`

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class MaterializedDoc:
    """Record for one document successfully downloaded and written to disk."""
    filename: str             # as written to output_dir
    file_path: Path           # absolute path of written file
    entity_id: str            # KH entity wrapper id (for citation)
    doc_id: str               # KH document id that was downloaded
    display_name: str         # human-readable name from json_value
    metadata: dict[str, Any]  # caller-supplied fields from the entity json_value
```

New method on `DocStore`:

```python
async def materialize(
    self,
    entities: list[dict[str, Any]],
    output_dir: Path | str,
    *,
    doc_id_field: str,
    collection_id: str,
    name_fn: Callable[[dict[str, Any]], str],
    display_name_fn: Callable[[dict[str, Any]], str] | None = None,
    metadata_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    concurrency: int = 10,
    encoding: str = "utf-8",
) -> list[MaterializedDoc]:
    """Download entity documents to a local directory with caller-supplied naming.

    Entity querying is the caller's responsibility (via fabric.entities.list_all()).
    This method owns only the download-and-write step.

    Args:
        entities: Pre-fetched entity dicts (each has "id" and "json_value").
        output_dir: Directory to write downloaded files (created if absent).
        doc_id_field: Dot-path into json_value for the document ID to download
                      (e.g. "markdown_doc_id", "doc_id"). Entities where this
                      field is absent or empty are skipped with a warning.
        collection_id: KH collection ID to download documents from.
        name_fn: Callable(json_value) -> filename. Receives the entity's
                 json_value dict; returns the filename to write (e.g.
                 "Income_W2.md"). Caller supplies classification-based or
                 display-name-based naming — the SDK imposes no convention.
        display_name_fn: Optional callable(json_value) -> str for the
                         human-readable display name stored on MaterializedDoc.
                         Defaults to name_fn output.
        metadata_fn: Optional callable(json_value) -> dict for extra fields
                     to store on each MaterializedDoc.metadata (e.g. investor,
                     document_type). Defaults to empty dict.
        concurrency: Max concurrent downloads (default 10).
        encoding: Text encoding for decoding document bytes (default "utf-8").

    Returns:
        List of MaterializedDoc for each successfully downloaded file, in
        entity order. Failed downloads are logged and omitted from the list.

    Raises:
        KnowledgeFabricError: If the KH client is not configured.

    Example:
        entities = await ctx.runtime.fabric.entities.list_all(
            odata_query=(
                f"collection_id eq '{loan_collection_id}' "
                f"and entity_type eq 'ClassifiedDocument'"
            )
        )
        docs = await ctx.runtime.fabric.docs.materialize(
            entities=entities,
            output_dir=loan_dir,
            doc_id_field="markdown_doc_id",
            collection_id=loan_collection_id,
            name_fn=lambda jv: build_doc_filename(
                jv.get("document_type", ""),
                jv.get("document_subtype", ""),
                jv.get("document_subsubtype", ""),
            ),
            display_name_fn=lambda jv: jv.get("name", ""),
        )
    """
```

Implementation notes:

- Extract `doc_id` from each entity via dot-path resolution on `json_value` (simple
  `str.split(".")` walk; no external dependency).
- Skip entities where `doc_id` is absent or empty (log warning, do not raise).
- Deduplicate by `doc_id` before downloading (same doc referenced by multiple entities
  gets one download; both entities get a `MaterializedDoc` pointing to the same file).
- Download via `self._kh.download_documents(collection_id, [doc_id])` — **note: this returns
  a ZIP archive, not the document's raw bytes** (see its docstring). A one-document request
  yields an archive with a single member; **unzip and extract that member's bytes** before
  writing (`_extract_single` helper: `zipfile.ZipFile(io.BytesIO(archive))`, read the first
  non-directory member; if the payload isn't a zip, treat it as raw). The first draft decoded
  the zip bytes directly as text — that was a bug.
- Decode the extracted member bytes with `encoding` (errors="replace"); write with `path.write_text()`.
- Apply `name_fn` for filename; handle duplicate filenames by appending `_2`, `_3`, etc.
  (same logic as MACER's `filename_counts` counter).
- Run downloads with `asyncio.gather` bounded by a semaphore at `concurrency`.
- Return a `list[MaterializedDoc]` in the order entities were processed; failed
  downloads are omitted and logged, never raised.

Per-file changes:

| File | Change |
|---|---|
| `jazzx_sdk/fabric/docs/store.py` | Add `MaterializedDoc` dataclass and `materialize()` method |
| `jazzx_sdk/fabric/docs/__init__.py` | Export `MaterializedDoc` |

## Usage pattern (what callers write)

```python
from jazzx_sdk.fabric.docs import MaterializedDoc

# 1. Query entities (fabric.entities owns this)
entities = await ctx.runtime.fabric.entities.list_all(
    odata_query=(
        f"collection_id eq '{loan_collection_id}' "
        f"and entity_type eq 'ClassifiedDocument' "
        f"and json_value/state ne 'ARCHIVED'"
    )
)

# 2. Download and materialize (fabric.docs owns this)
docs = await ctx.runtime.fabric.docs.materialize(
    entities=entities,
    output_dir=loan_dir,
    doc_id_field="markdown_doc_id",
    collection_id=loan_collection_id,
    name_fn=lambda jv: my_naming_logic(jv),
    display_name_fn=lambda jv: jv.get("name", ""),
    metadata_fn=lambda jv: {"investor": jv.get("investor", "")},
)

# 3. Build mapping for citations (caller's responsibility)
mapping = {d.filename: {"entity_id": d.entity_id, "display_name": d.display_name}
           for d in docs}

# 4. Expose to agents (build_directory_tools plan)
tool_set = build_directory_tools({"loan": loan_dir, "guidelines": guidelines_dir})
```

## Acceptance tests

```python
async def test_list_all_paginates():
    # Mock returns 500 entities page 1, 500 page 2, 0 page 3
    store = EntityStore(mock_kh)
    results = await store.list_all(odata_query="entity_type eq 'X'", page_size=500)
    assert len(results) == 1000
    assert mock_kh.read_entities.call_count == 3

async def test_materialize_downloads_and_names():
    entities = [{"id": "eid1", "json_value": {"markdown_doc_id": "did1", "name": "W2"}}]
    mock_kh.download_documents.return_value = b"line1\nline2"
    docs = await store.materialize(
        entities=entities,
        output_dir=tmp_path,
        doc_id_field="markdown_doc_id",
        collection_id="col1",
        name_fn=lambda jv: jv.get("name", "doc") + ".md",
    )
    assert len(docs) == 1
    assert docs[0].filename == "W2.md"
    assert (tmp_path / "W2.md").read_text() == "line1\nline2"
    assert docs[0].entity_id == "eid1"

async def test_materialize_skips_missing_doc_id():
    entities = [{"id": "eid1", "json_value": {}}]  # no markdown_doc_id
    docs = await store.materialize(
        entities=entities, output_dir=tmp_path,
        doc_id_field="markdown_doc_id", collection_id="col1",
        name_fn=lambda jv: "doc.md",
    )
    assert docs == []

async def test_materialize_deduplicates_doc_ids():
    # Two entities pointing to the same doc_id
    entities = [
        {"id": "e1", "json_value": {"markdown_doc_id": "d1", "name": "A"}},
        {"id": "e2", "json_value": {"markdown_doc_id": "d1", "name": "B"}},
    ]
    mock_kh.download_documents.return_value = b"content"
    docs = await store.materialize(
        entities=entities, output_dir=tmp_path,
        doc_id_field="markdown_doc_id", collection_id="col1",
        name_fn=lambda jv: jv.get("name", "doc") + ".md",
    )
    assert mock_kh.download_documents.call_count == 1  # downloaded once
    assert len(docs) == 2  # both entities get a record
```

## Sequencing

Phase 1 (EntityStore.list_all) is independent and small — can land first.
Phase 2 (DocStore.materialize) depends on nothing here but benefits from Phase 1
being available so callers can write the idiomatic pattern end-to-end.
