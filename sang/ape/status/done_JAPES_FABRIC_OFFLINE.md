# JAPES Plan — Fabric offline management (KH-first, local failover, transient opt-out)

**Author:** Virendra Mehta (drafted with Claude Code)
**Execute with:** Claude Code from `/Users/sangit/src/japes/` (branch v1.5)
**Scope:** Bring `fabric.graph` (then `fabric.canonical`, `fabric.policy`) to the same
RetrievalMode model `fabric.docs` already has. japes only.

---

## Goal

Every fabric store should behave consistently across `RetrievalMode`, with the **Knowledge Hub
as the system of record** and local storage as failover / dev-offline / transient:

- **STRICT** — KH only; fail loudly if unavailable.
- **CACHED** — KH-first; write-through to KH and cache locally; read KH, fall back to local.
- **LOCAL** — local only (no KH). The MacBook / no-KH dev + demo path.
- **TEST** — fixtures only.
- **Transient ("don't upload")** — an explicit local-only write for operational/scratch content
  that must never reach KH (mirrors `DocStore.put(location="local")`).

This is **not** "local-first." KH stays canonical. We borrow from k9 only the *local-tier
mechanism* (local JSON persistence, resolvable paths, graceful no-KH, non-blocking sync) to power
the failover / LOCAL / TEST / transient tiers.

`fabric.docs` already implements this exactly (default `location="hub"`, CACHED failover,
`location="local"` for transient). It is the template; the other stores should match it.

---

## Current state (verified)

| Store | Offline today | Local backend available |
|---|---|---|
| `fabric.docs` | ✅ STRICT/CACHED/LOCAL/TEST (`_get_hub`/`_get_local`), `location` hub/local | done — the template |
| `fabric.graph` | ❌ KH-only; `None` without kh_client | **yes, unused:** `jazzx_sdk.tools.kg_store.InMemoryKGStore` already has `add_triples`/`query_triples`/`to_json`/`from_json` |
| `fabric.canonical` | ❌ KH-only | no (would be local JSON per object) |
| `fabric.policy` | ❌ KH-only | no (local bundle files) |
| `fabric.rag` | ❌ KH-only | hard (needs vector backend) |
| `KnowledgeFabric` | builds canonical/graph/rag/policy **only if kh_client**, else `None` | — |

k9's strengths to adopt (local tier only): local JSON as the on-disk form (`InMemoryKGStore.to_json`
/ `save_local_file`); a `_resolve_path` that walks cwd/parent so paths work under Streamlit;
best-effort, non-blocking KH sync; never hard-fail when KH is absent in LOCAL mode.

---

## Design

### Change 1 — `fabric.graph` (KGStore) gets the RetrievalMode model  *(highest value — ready backend)*

- Give `KGStore` a `config: FabricConfig` (mode + `local_cache_dir`) like `DocStore`.
- Local backend = `InMemoryKGStore` persisted to `local_cache_dir/kg/<collection_id>.json`
  (`to_json`/`from_json`). It already supports the `query()` filters (subject/predicate/section/
  text_search/limit) and `add_triples`.
- Per-mode behavior, mirroring DocStore:
  - STRICT → KH (`create_triple`/`read_triples`/…).
  - CACHED → write-through to KH **and** the local InMemoryKGStore; reads try KH, fall back to local.
  - LOCAL / TEST → InMemoryKGStore only (no KH).
- **Transient triples** — add `location: Literal["hub","local"] = "hub"` to `add_triple`/`add_triples`
  (mirror DocStore). `location="local"` writes only to the local store (don't upload) regardless of
  CACHED — for scratch/intermediate KG.
- **Ontologies in the local tier** — `InMemoryKGStore` is triples-only, so register/get/list/resolve
  ontology in LOCAL/CACHED-fallback go to **local files** under `local_cache_dir/ontologies/`
  (`.ttl`/`.json`, k9-style), not the triple store. STRICT/CACHED-primary still use KH.

### Change 2 — `KnowledgeFabric` constructs offline-capable stores

- In LOCAL/TEST (no kh_client), build `self.graph` on the local backend instead of `None`.
- STRICT/CACHED still require a kh_client (as today).
- Same treatment for canonical/policy once their local tiers land (Changes 3–4).

### Change 3 — `fabric.canonical` local tier  *(medium)*

- Local JSON per object type under `local_cache_dir/canonical/<type>/<id>.json` so traces,
  decisions, evidence, outcomes persist in LOCAL/CACHED-failover. Same STRICT/CACHED/LOCAL/TEST
  rules. (Lets a no-KH ci_spread/CRE run still persist its `CanonicalTrace`.)

### Change 4 — `fabric.policy` local tier  *(medium)*

- Local bundle files under `local_cache_dir/policy/` for LOCAL/CACHED-failover (packs already ship
  bundles as files).

### Out of scope (for now)

- **`fabric.rag`** — offline RAG needs a local vector/embedding backend; larger effort. Defer;
  document `.rag` as KH-required until then.

### Shared

- Add a `_resolve_path()` helper (cwd/parent/grandparent walk) used by all local tiers so paths
  resolve under Streamlit (lifted from k9 `StorageManager`).
- Reuse the existing `FabricConfig.retrieval_mode` + `local_cache_dir`; no new config surface.

---

## Open decisions

- **D1 — transient API:** `location="hub"|"local"` arg on graph writes (mirrors DocStore) **[rec]**,
  vs a separate `persist=`/`temp=` flag.
- **D2 — CACHED write semantics:** write-through to **both** KH and local on `put` **[rec]**, vs
  KH-only-on-write + cache-only-on-read (what DocStore's *read* does). Decide write-side policy.
- **D3 — ontology local format:** `.ttl` (turtle, k9 default) vs `.json`. **[rec: .json]** for
  round-trip simplicity unless turtle is needed for interop.
- **D4 — canonical/policy now or later:** ship Change 1+2 first (graph), then 3/4 **[rec]**.
- **D5 — rag:** defer **[rec]**.

---

## Priority / sequencing

1. **Change 1 + 2 (fabric.graph + KnowledgeFabric offline)** — unblocks the ci_spread no-KH demo
   (LOCAL mode: register ontology to local file, write/query triples to local JSON, no mock needed).
2. Change 3 (canonical local) — offline trace/decision persistence.
3. Change 4 (policy local).
4. rag — deferred.

---

## Tests (offline, no KH)

- KGStore per-mode round-trips against `MockKnowledgeHubClient` (STRICT/CACHED) and a temp
  `local_cache_dir` (LOCAL/TEST): `add_triple`→`query`, `add_triples` bulk, `traverse`, delete.
- CACHED failover: KH raises → reads fall back to local; transient `location="local"` never hits KH.
- `KnowledgeFabric(config=LOCAL)` (no kh_client) → `fabric.graph` is non-None and persists to disk.
- Ontology local round-trip (register→get→list) in LOCAL mode via files.

---

## Driving consumers & k9 migration

The motivation for KH-first is not just `fabric.docs` parity — it's a real workflow requirement:

- **k9's local-first was a constraint, not a design choice.** When k9 was built there was no
  dev-daily cloud KH for a long stretch, and the KH client had no ontology support. Both are now
  resolved (cloud KH + ontology APIs in the client / `fabric.graph`). So k9's "local JSON is the
  source of truth, KH is a best-effort upsync" model is legacy and should be retired.
- **Async human-in-the-loop approval requires shared state.** k9's proposal-approval step happens
  asynchronously — an approver reviews/approves later, potentially from a different session or
  machine. That only works if proposals (and their approval status) are **KH-canonical**.
  Local-as-source-of-truth traps the proposal on the authoring box.

**Implication (follow-on k9 work, separate plan):** once this fabric offline model lands, migrate
k9 to be a fabric consumer — proposals / ontologies / KG persisted via `fabric` in **CACHED/STRICT**
(KH-canonical) in the cloud, **LOCAL** only for offline dev. Approval reads/writes proposal state
from KH. This replaces `StorageManager`-as-truth + the best-effort `schedule_fabric_task` upsync.
(jaci/ci_spread is the same shape: LOCAL on the MacBook, CACHED/STRICT deployed.)

---

## Notes

- Consistency target: after this, `fabric.graph`/`canonical`/`policy` match `fabric.docs`'s
  KH-first + failover + transient model. Callers pick behavior via `FabricConfig.retrieval_mode`,
  not by importing the KH client.
- ci_spread (caller) then runs LOCAL on the MacBook (persistent local KG/ontology, no KH) and
  CACHED/STRICT in deployment — same code, mode-driven. Supersedes the `_resolve_kg_store()`
  mock fallback in `ci_spread/conductor.py`.
- Reference: `fabric/docs/store.py` (the working template), `tools/kg_store.py` `InMemoryKGStore`
  (the local backend), k9 `services/storage_manager.py` (path-resolution + local-file patterns).
