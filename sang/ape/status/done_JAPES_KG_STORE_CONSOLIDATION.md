# Plan: KG Store Consolidation (japes 1.6.7) + client migration

## Principle
Fabric is the only front door to Knowledge Hub. Callers use `ctx.runtime.fabric.*`;
nobody imports a KH client or constructs a store. One KG store: `fabric.graph`.

## Background
Two overlapping KG store families existed:
- `tools/kg_store.py`: `BaseKGStore` (ABC), `InMemoryKGStore`, `KnowledgeHubKGStore` — older,
  macer-derived; the legacy agent tools and macer's `MACERKnowledgeGraphStore` extended these.
- `fabric/graph/store.py`: `KGStore` — the KH-backed fabric surface (better triple path via
  `create_triple`, ontology ops, CRUD, defaulting).

`KnowledgeHubKGStore` was a strictly-worse duplicate of `fabric.graph.KGStore`. `BaseKGStore`'s
"in-memory vs KH" abstraction is now served by the KH-client interface (real vs Mock).
`InMemoryKGStore`'s real role was *working memory* (scratch), not a KH alternative.

Decisions (with user): Option A — fabric.graph is the one store; `MockKnowledgeHubClient` is the
local/transient backend. Transient scratch is first-class via `transient_graph()`.

## Phase 1 — japes (DONE, 1.6.7, tests green)
- `Triple` + helpers (`_normalize_key`, `format_triples_for_prompt`, `merge_subjects`) moved to
  `fabric/graph/triple.py` (leaf module; fixes the inverted dependency). Re-exported from
  `tools/kg_store.py` and `tools/__init__.py`.
- `fabric.graph.KGStore`: added `subjects()`, `predicates()` (folded the useful `InMemoryKGStore`
  bits). Id-based CRUD + `add_entity`/`count` shipped earlier in 1.6.7.
- Keystone: `KnowledgeFabric` in LOCAL/TEST with no `kh_client` backs graph/canonical/rag/policy
  with a Mock instead of `None`. STRICT still errors.
- `KnowledgeFabric.transient_graph()`: cached, Mock-backed, never-persisted scratch graph.
- Agent tools rewritten over `fabric.graph`: `query_graph`/`list_graph_entities`/
  `get_graph_neighbors` + `create_kg_tools(graph)` factory. Dropped `BaseKGStore`/client tools.
- Removed `BaseKGStore`, `InMemoryKGStore`, `KnowledgeHubKGStore`.
- `fabric.kh` docstring no longer lists ontology mgmt (now on `fabric.graph`).

## Phase 2 — ci_spread (jaci)
- Delete `_resolve_kg_store()` and the `KGStore(MockKnowledgeHubClient())` fallback; use
  `ctx.runtime.fabric.graph` (never None offline now).
- Replace the three hand-rolled `add_triple` calls with `add_entity(f"loan:{id}", {...})`.
- Call `delete_triples(subject=f"loan:{id}")` before re-writing (idempotent re-extraction).
- If/when ci_spread agents query the KG, use `create_kg_tools(ctx.runtime.fabric.graph)`.
- Repoint any `Triple` import to `jazzx_sdk.fabric.graph`.

## Phase 3 — k9
- Already on `fabric.graph`; repoint `Triple` import to `fabric.graph`; confirm zero `.kh`;
  adopt shared helpers/tools where it has its own equivalents.

## Phase 4 — macer
- `MACERKnowledgeGraphStore`: move run-scoped extraction/reasoning to
  `ctx.runtime.fabric.transient_graph()`; promote keepers to `fabric.graph` if any persist.
- Keep domain logic in-pack: `merge_name_variants`/`merge_similar_subjects` compute the alias
  mapping; apply via the shared `merge_subjects(triples, mapping)`. `to_html`/`to_json` stay
  as macer artifacts operating on `query()` output.
- Retire macer's local `@function_tool` KG tools for `create_kg_tools(...)`.
- Repoint imports off `jazzx_runtime_sdk` / `tools.kg_store` store classes.

## Sequencing
Push japes first, then ci_spread, then k9, then macer (each assumes japes is already updated).

## Not doing now (extend later if real use cases)
- `snapshot()/restore()` on fabric.graph (transient covers scratch; macer `to_json` is a domain artifact).
- Per-call `location=` transient flag on graph (handle is cleaner; cross-backend query merge not worth it).
- RDF/Turtle ingestion helper (would add `rdflib` to core; k9 keeps its own for now).
