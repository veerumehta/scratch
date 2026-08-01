# Knowledge Fabric — SDK Design Handoff

**Date:** 2026-05-30  
**Status:** Design approved — ready for implementation  
**Author:** Virendra Mehta  
**Scope:** Introduce `KnowledgeFabric` as the unified semantic surface in `jazzx_sdk`; deprecate direct `KnowledgeHubClient` usage by extension consumers

---

## Context

JAPES has grown from an extension service with a runtime SDK into a full platform-as-SDK. Over that growth, the knowledge layer accumulated as a collection of direct `KnowledgeHubClient` calls, raw KG triple tools, and an in-progress canonical object layer using the entity mechanism as a backing store. The naming `knowledge_hub` is now misleading — what exists is a semantic fabric: canonical objects, enriched triples, ontologies, RAG collections, and policy bundles.

This document defines the `KnowledgeFabric` layer that unifies all of these under a stable surface, hides the KH client as an implementation detail, and provides Domain Pack governance with a clean mount point.

---

## Design Goal

Consumers — cognitive modes, extension handlers — interact with:

```python
ctx.runtime.fabric.canonical   # canonical II objects
ctx.runtime.fabric.graph       # knowledge graph / triples / ontologies
ctx.runtime.fabric.rag         # document collections / semantic search
ctx.runtime.fabric.policy      # Rego/OPA bundles
```

They never import or call `KnowledgeHubClient` directly. The fabric delegates to KH internally; as KH adds native canonical endpoints, the fabric's backing store swaps without any consumer change.

---

## Directory Structure

Add to `japes/jazzx_sdk/`:

```
fabric/
├── __init__.py              # exports: KnowledgeFabric, KnowledgeFabricError
├── fabric.py                # KnowledgeFabric class — wires up the four stores
├── canonical/
│   ├── __init__.py
│   ├── models.py            # Pydantic models for all five canonical II objects
│   ├── store.py             # CanonicalObjectStore — CRUD, linker calls, KH entity backing
│   └── linker.py            # cross-linkage resolution (evidence_refs, policy_refs, trace_id)
├── graph/
│   ├── __init__.py
│   ├── store.py             # KGStore — triple CRUD, enrichment, query, multi-hop traversal
│   └── ontology.py          # OntologyManager — register/resolve domain ontologies
├── rag/
│   ├── __init__.py
│   └── store.py             # RAGStore — collection management, semantic search, chunk retrieval
├── policy/
│   ├── __init__.py
│   └── store.py             # PolicyStore — Rego/OPA bundle management (NOT canonical Policy objects)
└── pack/
    ├── __init__.py
    └── loader.py            # DomainPackFabric — reads pack YAML, registers ontology + bundle into fabric
```

---

## Key Design Decisions

### 1. KnowledgeFabric is the surface; KnowledgeHubClient is the backing

`KnowledgeFabric.__init__` receives a `KnowledgeHubClient` instance from `ClientLayer`. It constructs the four stores, passing the client to each. Consumers receive only the fabric reference.

```python
# fabric.py
class KnowledgeFabric:
    def __init__(self, kh_client: KnowledgeHubClient) -> None:
        self.canonical = CanonicalObjectStore(kh_client)
        self.graph = KGStore(kh_client)
        self.rag = RAGStore(kh_client)
        self.policy = PolicyStore(kh_client)
```

### 2. ClientLayer gains a `.fabric` property; `.knowledge_hub` is unchanged

`ctx.runtime.knowledge_hub` stays as a fully supported, non-deprecated property. MACER and Juno use it today and will continue to do so — they do not use canonical objects, enriched triples, or any of the new fabric capabilities, so there is no value in forcing them to migrate. `KnowledgeFabric` is additive: new extensions (JACI-AML, JACI-KYC, K9, and anything built after them) use `ctx.runtime.fabric`; existing extensions are untouched.

In `client_layer.py`:

```python
@property
def fabric(self) -> KnowledgeFabric:
    """Semantic fabric layer for extensions using canonical objects, KG, RAG, or Domain Packs.
    New extensions (JACI, K9, etc.) use this. Existing extensions (MACER, Juno) use .knowledge_hub.
    """
    if self._fabric is None:
        self._fabric = KnowledgeFabric(self._kh_client)
    return self._fabric

@property
def knowledge_hub(self) -> KnowledgeHubClient:
    """Direct KH client access. Supported indefinitely for MACER and Juno.
    New extensions should use .fabric instead.
    """
    return self._kh_client
```

No `DeprecationWarning`. No forced migration. When MACER or Juno eventually need canonical objects or KG enrichment, they can adopt `.fabric` on their own timeline.

### 3. Canonical object models carry required cross-linkage fields

In `canonical/models.py` — these are the five Charter objects with cross-linkage baked in. Do not use Optional for the linkage fields on Decision, Trace, Outcome — they are required for charter compliance.

```python
class CanonicalPolicy(BaseModel):
    policy_id: str
    pack_id: str
    clause_text: str
    effective_date: date
    superseded_by: str | None = None

class CanonicalEvidence(BaseModel):
    evidence_id: str
    policy_refs: list[str]          # links to CanonicalPolicy.policy_id
    source: str
    content: str
    confidence: float
    collected_at: datetime

class CanonicalDecision(BaseModel):
    decision_id: str
    policy_refs: list[str]
    evidence_refs: list[str]
    disposition: str
    rationale: str
    autonomy_level: int
    decided_at: datetime

class CanonicalTrace(BaseModel):
    trace_id: str
    decision_id: str
    mode_sequence: list[str]
    tool_calls: list[dict]
    started_at: datetime
    completed_at: datetime

class CanonicalOutcome(BaseModel):
    outcome_id: str
    trace_id: str
    decision_id: str
    human_override: bool
    override_reason: str | None = None
    recorded_at: datetime
```

### 4. CanonicalObjectStore backing — entity layer now, native endpoints later

Phase 1: store canonical objects as KH entities with `entity_type="canonical_{object_type}"`. This reuses the existing entity CRUD without waiting for KH to add native endpoints.

Phase 2 (KH team): KH adds `/canonical/policies`, `/canonical/decisions`, etc. The store's private methods swap backing; all public method signatures are unchanged.

```python
# canonical/store.py (phase 1 pattern)
class CanonicalObjectStore:
    ENTITY_TYPE_MAP = {
        "policy": "canonical_policy",
        "evidence": "canonical_evidence",
        "decision": "canonical_decision",
        "trace": "canonical_trace",
        "outcome": "canonical_outcome",
    }

    async def put_policy(self, policy: CanonicalPolicy) -> str:
        return await self._kh.create_entity(
            entity_type=self.ENTITY_TYPE_MAP["policy"],
            name=policy.policy_id,
            attributes=policy.model_dump(),
        )

    async def get_policy(self, policy_id: str) -> CanonicalPolicy:
        raw = await self._kh.read_entity(name=policy_id, entity_type=self.ENTITY_TYPE_MAP["policy"])
        return CanonicalPolicy(**raw["attributes"])
```

### 5. KGStore wraps existing triple tools as a stateful class

Move logic from `jazzx_sdk/tools/knowledge_graph.py` into `graph/store.py` as methods on `KGStore`. Flat surface — no sub-namespaces. K9/DOG uses the same methods as JACI; it just calls them with ontology-authoring intent.

```python
# graph/store.py
class KGStore:
    async def add_triple(self, subject: str, predicate: str, object: str, *, source: str, confidence: float = 1.0, section: str = "") -> str: ...
    async def query(self, *, subject: str = "", predicate: str = "", section: str = "", text_search: str = "", limit: int = 50) -> list[Triple]: ...
    async def traverse(self, start_subject: str, *, max_hops: int = 2, predicate_filter: list[str] | None = None) -> list[Triple]: ...
    async def register_ontology(self, name: str, version: str, schema: dict) -> str: ...
    async def get_ontology(self, name: str) -> dict: ...
```

K9 in v2 Knowledge Studio is a consumer of this surface, not a reason to complicate it.

### 6. DomainPackFabric reads pack YAML, registers into fabric at init

`pack/loader.py` is the Domain Pack governance hook. A pack declares what it brings to the fabric; `DomainPackFabric` loads it.

```python
# pack/loader.py
class DomainPackFabric:
    """
    Reads a Domain Pack's YAML manifest and registers its ontology and
    policy bundle into the provided KnowledgeFabric at initialization.
    
    Pack YAML shape:
        pack_id: aml_v1
        ontology:
          name: aml_ontology
          version: "1.0"
          schema_path: ontologies/aml_ontology_v1.json
        policy_bundle:
          name: bsa_sar_rules
          path: policies/bsa_sar_rules.tar.gz
        autonomy_ceiling: 1
    """
    def __init__(self, pack_yaml_path: str, fabric: KnowledgeFabric) -> None: ...

    async def initialize(self) -> None:
        """Load ontology and policy bundle into fabric. Call once at startup."""
        ...
```

In JACI-AML's `japes_handler.py`, add to `startup`:

```python
pack_fabric = DomainPackFabric("packs/aml_domain_pack.yaml", ctx.runtime.fabric)
await pack_fabric.initialize()
```

---

## Migration Path

**MACER and Juno — no changes required.**  
Both extensions use `ctx.runtime.knowledge_hub` directly. That path stays fully supported. Neither uses canonical objects, enriched triples, Domain Pack governance, or any of the new fabric capabilities, so there is no migration value and no migration pressure. When they eventually need fabric features, they can adopt `ctx.runtime.fabric` on their own schedule.

**JACI-AML — new fabric callsites, retire inline schema:**
- `jaci/src/jaci/schemas/policy_clause.py` — delete; use `ctx.runtime.fabric.canonical` models
- `tests/fixtures/policy_registry.py` — keep for eval harness; add a `FabricFixture` wrapper so eval code calls `ctx.runtime.fabric.canonical.get_policy()` identically to production
- `ctx.runtime.knowledge_hub.create_entity(entity_type="triple", ...)` → `ctx.runtime.fabric.graph.add_triple(...)`
- `ctx.runtime.knowledge_hub.read_triples(...)` → `ctx.runtime.fabric.graph.query(...)`

**JACI-KYC — build against fabric from day one.** No KH client usage.

**K9 — refactor callsites only.** Already platform-native; no structural changes needed. Replace direct `KnowledgeHubClient` calls with `ctx.runtime.fabric.graph.*` and `ctx.runtime.fabric.rag.*` equivalents. Purely mechanical.

**CORTEX — not in scope.** Currently an independent system. Bring-into-fold is a future integration effort; fabric design does not anticipate it.

---

## Implementation Sequence (suggested for Claude Code)

1. Create `fabric/__init__.py`, `fabric.py` with stub class
2. Implement `canonical/models.py` — five Pydantic models, no backing yet
3. Implement `canonical/store.py` — entity-backed CRUD for Policy first (unblocks JACI-AML charter Phase 7)
4. Add `.fabric` property to `ClientLayer`; wire CanonicalObjectStore
5. Implement `graph/store.py` — migrate `tools/knowledge_graph.py` logic
6. Implement `rag/store.py` — wrap existing KH collection/document methods
7. Implement `policy/store.py` — wrap OPA bundle methods
8. Implement `canonical/linker.py` — cross-linkage resolution
9. Implement `pack/loader.py` — DomainPackFabric with YAML parse
10. Migrate JACI-AML callsites; run full eval harness — confirm 80% baseline holds
11. Add DeprecationWarning to `.knowledge_hub` alias
12. Update `docs/ARCHITECTURE.md` and `docs/CANONICAL_OBJECTS_VIA_JAPES.md`

---

## What Does NOT Change

- `KnowledgeHubClient` — not modified; fabric delegates to it internally
- `ctx.runtime.knowledge_hub` — stays as a fully supported property; MACER and Juno depend on it
- Extension handler interface — `HandlerContext` gains `ctx.runtime.fabric`; `.knowledge_hub`, `.kernel`, `.process` untouched
- Eval harness — fixture data stays; only the JACI-AML call path through `mock_connectors.py` needs a `MockKnowledgeFabric` shim
- 80% eval baseline — this is a refactor of call paths, not prompt changes; baseline must be verified before PR merge

---

## Open Questions (resolve before Phase 2 KH native endpoints)

- Does KH's entity layer support batch writes? If not, `CanonicalObjectStore.put_many()` will be N serial HTTP calls — acceptable for now, needs flagging.
- Where does the canonical linker run validation — on `put_decision()` (strict) or lazily on `get_decision()` (permissive)? Recommend strict on write.
- `DomainPackFabric.initialize()` is async — handler startup hooks must await it. Confirm JAPES startup lifecycle supports async init.
