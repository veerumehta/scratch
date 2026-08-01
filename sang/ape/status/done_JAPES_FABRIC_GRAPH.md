# JAPES Plan — Promote KG/Triple semantics to `fabric.graph`

**Author:** Virendra Mehta (plan drafted with Claude Code)
**Execute with:** Claude Code from `/Users/sangit/src/japes/`
**Scope:** `jazzx_sdk/fabric/graph/store.py` (+ `fabric.py` / `config.py` for defaulting). japes only.
**Verify with:** Offline smokes + a new pytest file, all against `MockKnowledgeHubClient`.

---

## Goal

Make `fabric.graph` (`KGStore`) the **complete, correctly-wired semantic entry point** for
knowledge-graph / triple / ontology operations, so callers (JACI packs, K9/DOG) use
`ctx.runtime.fabric.graph.*` directly and never reach down to `fabric.kh`. The KH client stays
the low-level REST transport; all semantic surface lives in the fabric.

This is the standing architecture (the `KnowledgeFabric` facade already documents `.kh` as the
escape hatch for "what the typed stores don't yet cover", and assigns "triples, ontologies,
traversal" to `fabric.graph`). The work here is to finish the wiring and close the gaps.

**Out of scope (explicitly):**
- **Fuseki / RDF.** `../knowledge_hub` `fuseki_handler.py` + `knowledge_graph_builder.py` are
  dead leftover — the KG is entity-backed. Do not wire to Fuseki. See memory
  `kh-knowledge-graph-is-entity-backed`.
- KH **server** changes — none. We only consume the existing KH client API.
- Caller migration (ci_spread Phase 1, K9) — separate follow-up; this plan only makes the
  fabric surface correct and usable.
- Generic entity CRUD on `fabric.graph` — entities are reached via `fabric.canonical` / `fabric.kh`.

---

## Verified facts (grounding — checked against the live SDK + mock)

- **KH client triple API** (real `KnowledgeHubClient` + `MockKnowledgeHubClient`, identical sigs):
  - `create_triple(subject, predicate, object_, collection_id, ontology_id, *, source="", section="", confidence=1.0)` → dict
  - `bulk_create_triples(triples: list[dict], collection_id, ontology_id)` → list[dict]
  - `read_triples(collection_id, ontology_id, *, section=None, subject=None, predicate=None, page_size=1000)` → list[dict]
- **KH client ontology API:** `create_ontology(name, rdfs_ontology, json_ontology=None)`,
  `read_ontology(ontology_id)`, `read_ontologies(skip, limit, odata_query, order_by, order_direction)`,
  `update_ontology(...)`, `delete_ontology(ontology_id)`, `upload_ontology(json_file_content: bytes, ...)`,
  `resolve_current_ontology(ontology_key)`.
- **Triples ARE entities.** `create_triple` stores an entity with `entity_type="triple"`,
  `json_value={subject,predicate,object,source,section,confidence}`. There is **no** triple
  update/delete on the KH client — mutation/deletion goes through `update_entity` /
  `delete_entity(entity_id)`.
- **Mock parity is functional.** `create_triple → read_triples` round-trips in-memory; all
  ontology + entity methods exist on the mock. So every change here is **offline-testable**.
- **`Triple`** (`jazzx_sdk/tools/kg_store.py`) fields: `subject, predicate, object, source,
  section, confidence, source_text, sources, chunk_label`; ignores extra keys → `Triple(**dict)`
  from `read_triples` is safe even if KH returns `id`/`name`/`collection_id`.
- **`fabric.graph` is `None` when `KnowledgeFabric` is built without a `kh_client`** (TEST mode).
  Offline use ⇒ `KnowledgeFabric(kh_client=MockKnowledgeHubClient())`.
- **`FabricConfig`** has `retrieval_mode, knowledge_hub_url, local_cache_dir, golden_cases_dir,
  api_key` — **no** collection/ontology. So "current collection/ontology" must be introduced.

### Current `KGStore` method audit

| Method | Delegates to | Status |
|---|---|---|
| `query(subject, predicate, section, text_search, limit, …)` | `read_triples(...)` | ✅ correct |
| `traverse(start, max_hops, predicate_filter, …)` | client-side BFS over `query` | ✅ correct |
| `add_triples(list[Triple])` | `bulk_create_triples(...)` | ✅ correct (passes `""` for collection/ontology — fix via Change 4) |
| `add_triple(...)` | `create_entity(entity_type="triple", name=, attributes=)` | ❌ stale — `attributes=` kwarg does not exist; never worked |
| `register_ontology(name, version, schema)` | `create_entity(entity_type="ontology", attributes=)` | ❌ stale + wrong shape (KH ontology = rdfs + json, no `version`) |
| `get_ontology(name)` | `read_entity(name=, entity_type=)` | ❌ stale — `read_entity(entity_id)` takes an id, not name+type |

---

## Changes

### Change 1 — Fix `add_triple` → `create_triple`

Replace the broken `create_entity(..., attributes=…)` call with the purpose-built API:

```python
result = await self._kh.create_triple(
    subject=subject,
    predicate=predicate,
    object_=object,
    collection_id=self._resolve_collection(collection_id),
    ontology_id=self._resolve_ontology(ontology_id),
    source=source,
    section=section,
    confidence=confidence,
)
return result.get("id", "") if isinstance(result, dict) else str(result)
```

(`_resolve_collection`/`_resolve_ontology` per Change 4.) Keep the `KnowledgeFabricError` wrap.

### Change 2 — Fix the ontology methods → real ontology API

The KH ontology model is `(name, rdfs_ontology: str, json_ontology: dict | None)` with no `version`
param (versioning is via the registry + `resolve_current_ontology`). Redesign both stub methods —
**these are signature-changing, but the methods never worked, so no real caller breaks:**

- `register_ontology(name, *, rdfs_ontology="", json_ontology=None) -> str`
  → `create_ontology(name, rdfs_ontology, json_ontology)`; return the ontology id.
  (Add an `upload_ontology(...)` passthrough later if file-content authoring is needed.)
- `get_ontology(ontology_id: str) -> dict` → `read_ontology(ontology_id)`.

### Change 3 — Add the missing semantic surface (so nobody needs `.kh`)

- `list_ontologies(*, limit=100, odata_query=None) -> list[dict]` → `read_ontologies(...)`.
- `resolve_ontology(ontology_key: str) -> dict` → `resolve_current_ontology(ontology_key)`.
- `delete_triple(triple_id: str) -> None` → `delete_entity(triple_id)` (triples are entities).
  **Implementation check:** confirm `read_triples` / `create_triple` surface the entity `id` so a
  caller can obtain `triple_id`; if `query` drops it, add an `id` field path-through on `Triple`
  or return ids from `query`. Decision D3 governs whether we ship this now.

### Change 4 — Collection / ontology resolution (the one real design addition)

KH `create_triple` / `read_triples` **require** `collection_id` + `ontology_id`; there is no
client- or config-level default today (passing `""` is what `add_triples` does now, which is wrong
for a live KH). Introduce a "current collection/ontology" notion:

- Add `default_collection_id: str | None` and `default_ontology_id: str | None` to
  `KGStore.__init__`.
- `KnowledgeFabric` populates them when constructing `KGStore` (from `FabricConfig` — add two
  optional fields — or from the pack/deployment binding).
- Per-call args override the defaults; if both are `None` after resolution, raise a clear
  `KnowledgeFabricError("collection_id/ontology_id required; no default configured")` rather than
  silently passing `""`.
- Fix `add_triples` to use the same resolution instead of `collection_id or ""`.
- **REQUIRED docs step (not optional):** the two new `FabricConfig` fields must be env-backed and
  documented, or they reproduce the "empty string" bug in a new form. Add `KH_COLLECTION_ID` /
  `KH_ONTOLOGY_ID` env mapping (field `default_factory=os.getenv(...)`) **and** add both to
  `.env.template` (japes repo env example) with a one-line comment each.

### Change 5 (optional) — offline ergonomics

`fabric.graph` is `None` without a `kh_client`. To let dev/test/demo use the semantic layer:
- Document the `KnowledgeFabric(kh_client=MockKnowledgeHubClient())` pattern, **or**
- (D4) auto-wire a `MockKnowledgeHubClient` when `retrieval_mode in {LOCAL, TEST}` and no
  `kh_client` is supplied, so `fabric.graph` is non-None offline.

---

## Design decisions — LOCKED 2026-06-08 (Veeru)

- **D1 — Collection/ontology defaulting:** **(a)** `KGStore` defaults + per-call override + **hard
  error when unresolved** (silent `""` passing is the current bug). `KnowledgeFabric` populates the
  defaults from `FabricConfig`. (Pack-bound (c) is the right long-term home but we lack a clean
  fabric-layer pack-binding mechanism, so (a) is the pragmatic step.)
- **D2 — Ontology versioning:** **(a)** drop `version` from `register_ontology`. Do NOT encode in
  name (a naming-convention tax on every caller). `resolve_current_ontology` is the versioning
  mechanism.
- **D3 — Triple mutation:** **(a)** expose `delete_triple` via entity ops. Append-only is a KH
  implementation detail, not a semantic contract callers should carry. (`update_triple` deferred.)
  Note: `read_triples` does NOT surface the entity id, so `delete_triple(triple_id)` takes the id
  returned by `add_triple`; query-then-delete is a KH limitation to revisit, not blocking.
- **D4 — Offline mock wiring:** **(a)** explicit `KnowledgeFabric(kh_client=MockKnowledgeHubClient())`
  — no auto-wiring. Auto-wiring in LOCAL/TEST risks silently substituting the mock for a real
  `kh_client` someone passed.

---

## Tests (all offline, against `MockKnowledgeHubClient`)

New `tests/fabric/test_kg_store.py` (japes):

```python
fab = KnowledgeFabric(kh_client=MockKnowledgeHubClient())  # or KGStore directly with defaults
g = fab.graph
# add_triple -> query round-trip
await g.add_triple("loan:L1", "has_borrower", "YETI", source="t", collection_id="c", ontology_id="o")
got = await g.query(subject="loan:L1", collection_id="c", ontology_id="o")
assert any(t.predicate == "has_borrower" for t in got)
# add_triples bulk; traverse; ontology register->get->list->resolve; delete_triple (if D3=a)
```

Also run the full japes suite + the four plan smokes from
`plan_JAPES_PLATFORM_GAPS_PATCH.md` style (import health, etc.).

---

## Versioning & notes

- Additive surface + fixes to non-functional stubs. The `register_ontology`/`get_ontology`
  signature changes are technically breaking but those methods never worked. **Recommend a minor
  bump** (new public semantic surface) — enquire before choosing major. Patch is defensible if we
  treat it purely as a correctness fix.
- Update `CHANGELOG.md`; the `KGStore` docstrings still say "Simplified … TBD" — replace with the
  real delegation once wired.
- **Caller follow-up (not in this plan):** migrate `ci_spread` Phase 1 and any K9/DOG KG usage to
  `fabric.graph`; pass `MockKnowledgeHubClient` (or real `kh`) so writes land. See
  `plan_caller_migration_jaci_k9.md`.
- Reference: KG is entity-backed; Fuseki is dead (memory `kh-knowledge-graph-is-entity-backed`).
