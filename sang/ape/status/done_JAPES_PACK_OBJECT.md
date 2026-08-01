# Pack as the primary domain object (design note)

Status: design / not yet built. Transient planning doc (gitignored).

## Vision

A **Pack is the single object that represents a domain** (a jaci "scenario").
The scenarios list is an **array of Packs**. Everything about a domain is reachable
from its Pack: the authored bundle (the "concepts") *and* references to the
runtime (transactions, traces, metrics). One handle for definition + execution.

## Two halves

1. **Authored / fixed — the concepts** (loaded from the pack):
   metadata · ontology · policies (`PolicyRegistry` of canonical `Policy` objects
   + their `source_refs`) · playbooks (+ provenance) · experts · modes ·
   conductor (`ConductorPipeline` via `describe()`).

2. **Runtime / live — references, not ownership**:
   the case fleet (gold cases) · transaction `CaseFile`s + `CanonicalTrace`s ·
   evaluation `RunHistory` + metrics · a domain-scoped lens on the fabric stores
   (canonical objects, KG, RAG, policy bundles).

## Design calls (where I'd diverge from a naive reading)

- **References / queries, not in-memory ownership.** Pack exposes *handles* into
  the runtime stores — `pack.traces(case_id=…)`, `pack.runs`, `pack.metrics` —
  resolved on demand. It must not accumulate every transaction in memory, or it
  becomes an unbounded stateful object with concurrency/lifecycle problems. The
  authored half is composed up front; the runtime half is queried.

- **One object, optional runtime binding.** `Pack.from_manifest(pack_id)` gives
  the authoring / UI / docs view (policies from the `PolicyRegistry` preload).
  `pack.bind(runtime)` adds the live fabric lens (policies served from the KH
  store, traces from the canonical-objects store). `pack.is_bound` says which.
  This keeps the dev-vs-prod policy source (the `PolicyRegistry` is explicitly
  the "test/dev preload path" per the `Policy` docstring) behind one accessor.

- **japes owns `Pack`; it stays UI-agnostic.** japes never imports jaci/streamlit.
  So UI presentation (icon, demo renderer) remains a thin jaci layer that *holds
  a Pack*. A jaci scenario = `Pack` + presentation. Conceptually scenario ≈ pack;
  mechanically the renderer lives outside the Pack.

## Why this helps (auditability / explainability / debugging / metrics)

Canonical objects already carry `pack_id`, `policy_refs`, `guidance_refs`, and
versions. With Pack as the **join point**, the chain becomes one traversal:

```
transaction → CaseFile → CanonicalTrace → TraceStep (mode/expert)
            → policy_refs → Policy(version) → source_refs (OCC/FDIC)
            → guidance_refs → Playbook(section)
```

- **Audit / explainability:** "which policy *version* governed this decision, and
  what does it cite?" is a walk from the Pack — no cross-system stitching.
- **Debugging:** one handle to compare *definition* (`pack.conductor.describe()`)
  against the *actual run* (the trace).
- **Metrics:** `pack.runs` is `RunHistory` (already built, sliceable by labels);
  live transaction metrics attach the same way.

## Relationship to existing pieces (compose, don't replace)

| Pack accessor | Backed by |
|---|---|
| `pack.metadata / .ontology / .playbooks / .modes` | `PackManifestLoader` (YAML reader, stays) |
| `pack.policies` | `PolicyRegistry` (authored) / fabric policy store (bound) |
| `pack.conductor` | `BaseConductor.describe()` → `ConductorPipeline` |
| `pack.cases / .traces` | `CaseFile` / `CanonicalTrace` (runtime, when bound) |
| `pack.runs / .metrics` | `load_run_history` / `RunHistory` |
| `pack.fabric` | domain-scoped lens on the four fabric stores (when bound) |

## Manifest additions (retire the UI stand-ins)

The `policy_registry_target` / `pipeline_target` I added to the **jaci UI**
registry are temporary stand-ins for pointers that belong in the **pack manifest**:

```yaml
policies:
  registry: "jaci.scenarios.ci_spread.policies.registry:CI_REGISTRY"
conductor:
  class: "...CIConductor"
  pipeline: <resolved from CIConductor.describe()>
```

Once the manifest declares them, japes resolves them and the UI targets are removed.

## Relationship to the canonical `DomainPack` (confirmed)

`Pack` (access/composition, never persisted) and `fabric.canonical.DomainPack`
(governance record, Schema Spec §7.8, persisted via `DomainPackStore`) are
**distinct, composed — not merged**. The five pack objects and their roles:

| object | role |
|---|---|
| `fabric.canonical.DomainPack` | governance **record**: identity, version, certification, *refs*, v1.5 version minimums (fail-closed validator). Persisted. |
| `pack.Pack` | runtime **access handle**: composes manifest + PolicyRegistry + ConductorPipeline; resolves refs → live assets. Never persisted. |
| `DomainPackHelper.from_yaml` | bridge: manifest → validated `DomainPack` governance record → `fabric.canonical.put_domain_pack`. |
| `DomainPackFabric.initialize` | bridge: promotes the pack's ontology → `fabric.graph` and policy bundle → `fabric.policy`. |
| `PackManifestLoader` | asset resolution: playbooks, ontology YAML, mode tuning, diagnose_map, conductor config. Runtime only. |

Intended startup (per spec): `put_domain_pack(DomainPackHelper.from_yaml(...))`
→ `DomainPackFabric(...).initialize()` → `PackManifestLoader` for asset access.

**Gap (jaci):** steps 1–2 are **unwired** — governance records are never persisted
to `fabric.canonical`, ontology/policy never promoted into fabric stores. `Pack`
should own this via `bind(runtime)`; `pack.record → DomainPack` once the manifest
carries the governance fields (it currently has only the operational keys, so
`DomainPackHelper.from_yaml` would fail validation today). → Stage B.

## Staged build

- **Stage A — authored core.** `jazzx_sdk.pack.Pack` composing loader +
  `PolicyRegistry` + `ConductorPipeline`; manifest gains `policies.registry` +
  conductor pipeline pointer; jaci manifests fill them; migrate the Concepts UI
  from the three stitched targets to `scenario.pack().*`. Retire the UI targets.
- **Stage B — runtime binding.** ✅ japes capability done: `pack.bind(runtime)` +
  `record()` / `trace(id)` / `case(id)` / `traces()` / `cases()` / `live_policies()` /
  `runs(dir)`; added `TraceStore.list` / `CaseFileStore.list` (pack-scoped). Remaining:
  jaci consumption (a Concepts/dashboard audit view) — gated on jaci wiring a bound
  runtime + the unwired startup sequence (`put_domain_pack` / `DomainPackFabric.initialize`).
- **Stage C — scenarios = packs (jaci).** The `SCENARIOS` registry yields Packs +
  presentation; dashboards and eval read `pack.*`.
