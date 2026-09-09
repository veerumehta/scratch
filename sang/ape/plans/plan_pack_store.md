# The pack store: three tables, three representations, and four layers of narrowing

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: design, Revision 3, 2026-09-08. Nothing built. Written against japes `7921746` on `dev`.

**Consolidates three independent designs of the same table**, which is the finding that shapes how
this document is organised:

| Source | Date | What it contributed | Disposition |
|---|---|---|---|
| `status/PLATO_PACK_TABLE_DESIGN.md` | 2026-09-02 | the three-table schema, immutability as the design, dependency edges, certification as an event log, binding placed elsewhere | **the spine — §4 is its schema** |
| `plans/plan_pack_store.rev1.md` | 2026-09-08 | the directory-tree finding, blob + digest with materialize-skip, the loader-root decision | **§2, §5, §6** |
| Rev 2 of this file | 2026-09-08 | the three pack representations, §7.8's KH-facing writer, the IIF layer, the union inventory | **§3, §7, §8, §9** |

Companions, still live and not superseded: `status/PLATO_DB_TABLE_MAPPING.md` (the four-schema
union, buckets A–D), `status/PLATO_ORG_SCHEMA_DESIGN.md` (which owns the binding relation, §7.4),
and `status/done_JAPES_PACK_OBJECT.md` — whose *"Relationship to the canonical `DomainPack`
(confirmed)"* section already settles how the five pack objects compose, and is load-bearing for §3
and D4/D6 below.

Two facts from those notes are corrected here: Plato has **7** tables, not the 3 recorded on
2026-09-02 (§4.5); and *"there is no pack row anywhere"* needs qualifying — there is a store and a
write path for the §7.8 governance record, pointing at Knowledge Hub, but it is unwired and holds
nothing (§3b). The distinction decides D6.

---

## 1. What is being decided

A pack — an ontology, a policy set, playbooks, evidence types, skills, mode tuning, expert and
conductor config, an evaluation suite — is authored **outside** the SDK and today lives only on a
filesystem. The SDK should assume that information is available to it behind a protocol, backed by
persistence it does not own. Plato supplies that persistence.

That is not a new pattern. `AssistantManifestStore`, `SessionStore` and `ConfigAuditStore` are all
*protocol in `jazzx_sdk`, durable implementation in Plato*, and `plato/packs/sources.py` already
made the same split one layer down. A `PackStore` protocol plus a `plato.packs` implementation is
the fourth instance of an argument made three times.

It also keeps the non-goal intact: the SDK receives pack **rows**, never pack knowledge, and
`plato/` still contains no "mortgage" and no "SAR" — only the table those words live in. The review
question stays answerable: *what row does this value come from?*

---

## 2. The finding that shapes the schema (Rev 1)

**A `pack_record` table is the easy half.** `PackManifestLoader` does not read a manifest
*document* — it reads a **directory tree**, and roughly a third of its accessors hand back a `Path`
or read a file relative to `self._root`:

| Accessor | Returns |
|---|---|
| `root()` | `Path` |
| `policy_files()` | `list[Path]` |
| `get_agent_dir()` | `Path \| None` |
| `get_mode_tuning_path(mode)` | `Path \| None` |
| `load_playbook_content(asset_id)` | reads `self._root / ref` |
| `load_ontology()`, `load_vocabulary()`, `load_diagnose_map()` | read under `_root` |
| `resolve_dependencies(packs_root)` | walks the filesystem for `depends_on` |
| `from_pack_id(pack_id, packs_root)` | tries three directory spellings |

Storing the manifest as a JSON column leaves every one of those on disk, so an uploaded pack would
be half-configured — the metadata queryable and the content missing. **So the design is a table
plus a blob plus a loader change**, and §5 and §6 are the second and third of those.

### 2.1 The question that decides the schema

**Does the table hold the pack, or point at it?** Pointing at a path keeps the filesystem as the
source of truth and makes the row a cache of a directory nobody can version — worth almost nothing.
Holding it makes Plato the registry: published once, immutable thereafter, same bytes for every
deployment.

**Hold it** — because the value is not storage, it is being able to answer *which pack version
produced this decision*, six months later, when the working tree has moved on. That answer needs
the version to be immutable and addressable, which a path is not.

---

## 3. The second finding: there are three pack representations, and one persists elsewhere

Rev 1 saw two. There are three, with different authoring files, different loaders and different
persistence — and the one carrying the governed IIF semantics **has a persistence path that points
at Knowledge Hub, not Plato**. Whether anything is actually written down it is a separate matter,
and §3(b) is careful about the difference.

| # | Authored as | Loader | Carries | Persists today in |
|---|---|---|---|---|
| **1** | `pack_manifest.yaml` + tree (`policies/`, playbooks, ontology, vocabulary, diagnose map, mode tuning, agent dir) | `PackManifestLoader` → `pack.Pack` | the pack's **runtime assets** | **the filesystem only** |
| **2** | `*_domain_pack.yaml` | `DomainPackHelper.from_yaml` → canonical `DomainPack` → `DomainPackStore` | the pack's **governed metadata** — Schema Spec §7.8 | **nowhere yet** — the write path points at the KH entity store, `entity_type="canonical_domain_pack"`, and is unwired (§3b) |
| **3** | `manifest.yaml` + `profile/{profile.yaml,persona.md,skills/*.yaml}` | `plato/packs/loader.py:load_pack` (+ `sources.py`) | **what one assistant is**, and how a host may run it | manifest in `plato_control`; profile bytes via `PackSource` |

Three consequences:

**(a) This plan's tables are representation 1, and must say so.** `pack_id`, `pack_version`,
`certification_status`, `domain`, `segment`, `regulatory_context`, `depends_on` are
`PackManifestLoader`'s accessors. The tables are named for the pack of record; the docstring has to
narrow that, or the next reader will assume all three live there.

**(b) Representation 2 has a writer that is not Plato — and it is currently unwired.**
`DomainPackStore` is a CRUD facade (`id_field="pack_id"`, KH-backed), and the intended startup
sequence is `put_domain_pack(DomainPackHelper.from_yaml(...))` →
`DomainPackFabric(...).initialize()` → `PackManifestLoader` for asset access. But
`done_JAPES_PACK_OBJECT.md` records the gap plainly: **steps 1–2 are unwired in jaci** —
*"governance records are never persisted to `fabric.canonical`, ontology/policy never promoted into
fabric stores"* — and the manifest *"currently has only the operational keys, so
`DomainPackHelper.from_yaml` would fail validation today."*

So the honest statement is: **the writer exists in code, points at KH, and writes nothing yet.**
That matters two ways. If the path gets wired (its Stage B), `plato/schemas.py`'s rule applies
directly — *"A JAPES service may hold a read projection of another system's facts, and may not
become a second writable copy of them… Every row in it carries the source and the source's
version"* — and representation 2 is **projected into `plato_projection`**, one row per
`(pack_id, pack_version)` with `source='knowledge_hub'` and `source_version`, so a resolver reads
§7.8 governance beside the assets without Plato becoming its second writer. If it stays unwired,
there is nothing to project and D6 is a live choice rather than a settled boundary. Either way this
plan must not write `canonical_domain_pack` into `plato_control`.

**And nothing here persists `pack.Pack`.** That note is explicit that `Pack` is a *"runtime access
handle… never persisted"*, composed rather than merged with the governance record. What §4 stores is
the authored manifest and the asset bytes; the governance record is `fabric.canonical`'s. A table
for `Pack` would be a category error.

**(c) Representation 3 is already solved, and is the pattern §6 copies.** `plato/packs/sources.py`
split *where the bytes come from* from *what they mean* — `PackSource` as a protocol rather than a
`backend="..."` string, because *"a pack can legitimately arrive from a directory, a bundle, a
config store that does not exist yet, or a tenant's own upload"* — and documents
`MappingPackSource` as *"the seam Phase 2 lands on, since `ConfigAssetVersion` rows resolve to
exactly this shape."* That seam is what §5's store plugs into.

**The vocabulary hazard, narrowed.** "Pack" names five objects in this tree — `pack.Pack`,
`fabric.canonical.DomainPack`, `DomainPackFabric`, `DomainPackHelper`, `PackManifestLoader` — and
that is **not drift**: `done_JAPES_PACK_OBJECT.md` enumerates all five with their roles and confirms
them as *"distinct, composed — not merged."* `plato.packs` is a sixth spelling and the only one
added since.

What remains a hazard is the **three YAML dialects** and the bare word on a wire contract. The
inherited rule applies to both: **the Canonical Object Schema Specification's vocabulary wins;
anything else is a local implementation name that must not appear in a manifest or on a wire
contract.** Plato is the first system with a public API, so it is the first place a bad name becomes
a data migration.

---

## 4. The tables

Three, from `PLATO_PACK_TABLE_DESIGN.md`. Each carries `tenant_id` **in the primary key**, per
`plato/tenancy.py` — verified: the rule is *"`tenant_id` appears in the primary key or in a unique
constraint, not merely as a column"*, and `verify_tables` enforces it over registered metadata.
This supersedes Rev 1's unique-constraint-only version, which satisfies the letter of the rule and
not its reason.

### 4.1 Immutability is the design

A published `(pack_id, version)` never changes. Everything mutable is modelled *around* it:

- **Certification moves; the version does not.** `draft → certified → suspended → retired` is a
  lifecycle over a fixed artefact. Keeping it in the pack row means the row changes after
  publication, so it goes in its own event table and the current value is derived. **This
  supersedes Rev 1 and Rev 2, which both made it a column on the version row.**
- **Correcting a pack means publishing a new version.** No edit path. Same bargain every package
  registry makes, and what makes provenance work.

### 4.2 `pack_version`

One row per published version. The unit of everything else.

| column | notes |
|---|---|
| `tenant_id`, `pack_id`, `version` | composite PK. Three parts, because a pack id means nothing across tenants |
| `manifest` | JSONB — the whole manifest **as authored**. Queryable, so "which packs declare this regulatory context" is a query rather than a filesystem walk |
| `content_digest` | sha256 over the pack's asset bytes. What makes the version verifiable |
| `content_ref` | blob location for the bytes (`fabric.blob`). Assets are authored and read as a unit, so they are stored as one |
| `domain`, `segment` | denormalised out of the manifest — the two things everything filters on |
| `published_at`, `published_by_user_id` | |
| `visibility` | `tenant` or `platform`. See D2 |

**Why the manifest is JSONB and the assets are a blob.** The manifest is small, structured and
queried; the assets are large, opaque to SQL and read whole. Splitting them that way avoids both a
table nobody can query and a row nobody wants to fetch.

**Why not a row per asset.** Tempting — ontology, policies, playbooks each in their own table — and
wrong for the reason a package registry does not shred a wheel: the pack is authored, reviewed and
versioned as a unit, so shredding it makes publication non-atomic and reassembly a join. The pack's
*content* becomes queryable through the vocabulary and policy stores it loads into, which exist.

### 4.3 `pack_dependency`

The `depends_on` closure, as edges. One row per declared dependency.

| column | notes |
|---|---|
| `tenant_id`, `pack_id`, `version`, `depends_on_pack_id` | composite PK |
| `version_spec` | as declared — a pin or a range |
| `resolved_version` | what it resolved to at publication, so the closure is reproducible later |
| `fragments` | which fragment kinds are imported; the loader already validates the kind set |

**Why edges rather than the JSON list inside the manifest** — which is where they live today, and
which Rev 1 proposed keeping: the question asked in practice is the reverse one, *what breaks if
this pack is retired*, and that is a query over edges, not a scan of every manifest. Recording
`resolved_version` beside the spec is what makes a six-month-old closure re-derivable; a range alone
is not. **This supersedes Rev 1's "`depends_on` stays inside `manifest_json`."** The manifest still
carries it as authored; the edge table is the derived index.

The loader's existing failure modes must survive the move: `resolve_dependencies` raises
`PackDependencyError` on a cycle **or an asset-id collision across packs**, and `merged_assets`
refuses to merge kinds whose shape it cannot merge rather than guessing. Publishing a closure must
not turn either into a silent success.

### 4.4 `pack_status`

Certification as an append-only log.

| column | notes |
|---|---|
| `event_id`, `tenant_id` | composite PK |
| `pack_id`, `version` | composite FK to the version row |
| `status` | `draft`, `certified`, `suspended`, `retired` — the values `PackStatus` already defines |
| `reason` | free text; a suspension without a reason is not actionable |
| `occurred_at`, `actor_user_id` | |

Current status is the latest event. That costs a query and buys the history: *when was this
suspended, and by whom* is the question asked during an incident, and a mutable column cannot
answer it.

**Reconciling with the manifest's own field.** `pack_manifest.yaml` and the canonical `DomainPack`
both carry `certification_status`, and the model's validator keys on it (§7.3). Those are the
**authored** status — what the pack claims about itself at publication. The durable, operated status
is derived from this log. Where they disagree, the log wins, and the publish path is where the
authored value becomes the first event.

### 4.5 Schema placement, and a naming decision

Placement is `plato_control` — a pack decides what the deployment *is*, which is the same reason
`assistant_manifest_record`, `config_audit_event` and `plato_setting` are there. `TABLE_SCHEMAS`
must gain a row per table or `schema_for` raises, *"rather than letting it land in the default
schema"* — the intended forcing function. And `register_all` is *"deliberately not every store
japes ships"*, so a `DbPackStore` must be instantiated there or autogenerate will not see it and
the tables will silently leave the migration chain.

**Plato's tables today — seven, not the three that note recorded:**

| Table | Schema | Origin |
|---|---|---|
| `assistant_manifest_record`, `config_audit_event` | `plato_control` | SDK |
| `plato_setting` | `plato_control` | Plato's own |
| `agent_session`, `turn_run`, `turn_run_event` | `plato_runtime` | SDK |
| `model_overlay` | `plato_reference` | Plato's own |

So Plato registers 5 of the SDK's 17 declared tables, plus 2 of its own. Twelve SDK tables are
still declared-but-absent from the chain, which is the backdrop for §8.

**The naming decision.** The earlier note proposed `plato_pack_version` / `plato_pack_dependency` /
`plato_pack_status`. Recommend dropping the prefix: the **schema** is what prefixes, and
`schemas.py` says so explicitly — *"the prefix is what makes a table-name collision structurally
impossible rather than avoided by convention."* `plato_control.plato_pack_version` prefixes twice.
`plato_setting` is the one existing outlier and has a reason (it is Plato's own settings table, not
an SDK store, and `setting` unqualified is too generic). A pack table has no such collision risk.
Small, but it is a data migration once written.

---

## 5. Where the bytes go

`fabric.blob` already has the two operations this needs: `put(data, key=...) -> pointer` and
`get(pointer) -> bytes | None`. So: **one archive per pack version**, `content_ref` in the row,
`content_digest` beside it.

The digest is not decoration. `fabric.docs.materialize` already keeps a manifest of
`sha256:`/`updated_at:` digests to avoid re-downloading unchanged documents, and a pack tree wants
exactly that: **materialize once per version, skip when the digest matches.**

Format: a zip of the pack directory, via the existing `pack_bundle`/`unpack_bundle` path that
`BundlePackSource` already uses — which inherits zip-slip protection and the manifest check rather
than reimplementing them. That matters because an uploaded bundle is untrusted input. `fabric.docs`
also unpacks zips, and its member-naming collision handling was non-trivial; read it before
repeating it.

---

## 6. Getting the loader a root

Every current caller does `Pack.from_manifest(pack_id, packs_root)`. A database-backed pack needs a
loader that resolves from the registry, and the filesystem path becomes the local-development case.
That is an SDK change, and the schema is not usable without it. Two options:

**(a) Materialize to a directory, keep the loader as it is.** `PackStore.materialize(record) ->
Path` fetches the archive, unpacks under a cache dir keyed by `content_digest`, hands the path to
`PackManifestLoader.from_pack_id`. Every path-based accessor in §2 keeps working untouched.
*Against*: needs writable local storage, and `depends_on` resolution needs the whole closure
materialized before the merge runs.

**(b) Abstract the path accessors behind a reader** with `open(relpath)` / `iterdir(relpath)`, one
filesystem implementation and one blob implementation. *Against*: touches every accessor in §2,
rewrites `packs_root`-walking dependency resolution, and buys nothing until a deployment cannot
write to disk.

**Recommendation: (a)**, for two reasons. It is smaller and reversible — a reader abstraction over a
materialized directory is a strictly smaller step from (a) than from today. And
`plato/packs/loader.py` already chose it for representation 3, materialising to a temp directory so
`InteractiveAgentSpec.from_dir` does the parsing, explicitly *"a deliberate reuse rather than a
shortcut"*, because *"a second mapping-based implementation of the same rules would be a place for
the two to disagree about what a pack means."* Choosing (b) for representation 1 would create the
disagreement that reasoning avoided.

---

## 7. The IIF layer: what the governed documents specify and the schema must not contradict

### 7.1 The identifier rule is normative

Schema Spec §1.2: runtime object instances use `policy_{uuid}`-style namespaced UUIDs, while
*"configuration/package/deployment identifiers may use governed semantic IDs or semantic slugs"* —
`aml-investigation-core`, `AML-INVESTIGATION-L2`, `barclays-aml-uk` — stable across releases unless
governance retires them, and *"do not force configuration/package identifiers into runtime UUID
patterns."*

§4.2's PK satisfies this, but by construction rather than by statement. Say it in the model
docstring: `pack_id` is a governed slug and is the wire contract; there is no surrogate id, and
adding one would be a defect, not a normalisation.

### 7.2 Seven §7.8-required fields are absent from the implemented model, and one is renamed

This is checkable, and it matters because whatever the table denormalises hardens today's vocabulary
into tomorrow's migration:

| §7.8 (Schema Spec v1.0) | `fabric.canonical.derived.DomainPack` (v1.5) |
|---|---|
| `domain_pack_object_id` (`packobj_{uuid}`) | absent |
| `domain_name` | absent — `PackManifestLoader.domain` is dialect 1's spelling |
| `thin_slices`, `personas`, `decision_classes`, `primary_artifacts` | absent |
| `ontology_refs` | absent (the assets exist; the ref list does not) |
| `pack_supported_range {min,max}` | **renamed** `supported_autonomy_range` |
| — | **added**: `domain_thesis`, `scope_boundary`, `cognitive_mode_activations` |
| — | **added v1.5**: `skill_bundle_version`, `per_pack_registry_versions`, `authority_matrix_versions`, `cross_pack_engagement_contracts`, `shared_entity_ontology_version`, `ipdv_policy_version` |

`domain` and `segment` — the two columns §4.2 denormalises — come from **dialect 1, not from
§7.8**, and `regulatory_context` is in neither. Not a reason to drop them; a reason for the
migration to record that `domain` is dialect 1's spelling of §7.8's `domain_name`, so the rename is
a documented alias rather than future archaeology. See D5.

### 7.3 Certification is a gate, and most of it already exists

**Implemented and fail-closed:** `DomainPack._enforce_certified_manifest_minimums`. A `DRAFT` pack
may omit the v1.5 bindings; a `CERTIFIED` one may not, and construction raises listing exactly what
is missing — `skill_bundle_version`, `shared_entity_ontology_version`, `ipdv_policy_version`, a
`per_pack_registry_versions[mode]` for every activated authority-bearing mode plus the universal
Evaluator registry, and an `authority_matrix_versions[mode]` for every activated matrix-bearing
mode. That is a certification gate expressed as a model validator, and it is the strongest piece of
IIF machinery already in the code.

**Also present:** `pack/lint.py` — `lint_pack` reads a pack's ontology, derivations and policies
*together* and reports what cannot reach what, separating `errors` from warnings (*"warnings are
things to know, not things that stop the pack working"*).

**So the publish gate is a composition, not new work:** parse → `lint_pack` → construct the typed
`DomainPack` → write `pack_version` + edges + the first `pack_status` event, in one transaction.
Refuse on lint errors or validator failure. Running it at publication and refusing a pack that fails
is the difference between a store and a dumping ground.

**Policy proposal:** a `draft` pack **may** be published — that is what a registry is for — but may
not be bound by an alias any deployment resolves, and may not raise `pack_supported_range.max`
above 0. Uploadable, not servable.

**What is missing is the rest of the lifecycle,** and the ABA already specifies it: launch gates,
promotion gates and rollback triggers (§10.5–10.7), recertification triggers (§11.5), against the
maturity model (L0 skeleton → L1 lighthouse-ready → L2 production-ready → L3 compounding). Plato's
aliases give promote and rollback *mechanically*; these are the **criteria**, and without them
`pack_status` is a log somebody appends to by hand.

### 7.4 A pack row is layer 1 of 4

The IIF documents specify a **narrowing order**, and it is what makes a pack store a control plane
rather than a file cabinet:

```
Pack semantics + Schema  ->  ABA  ->  Overlay  ->  JAP  ->  Runbooks/Ops
```

with an explicit precedence rule — *"No lower layer may widen a higher-layer boundary"* — and a
resolution order when documents disagree. Four separately-versioned artefacts, so four keys:

| Layer | Artefact | Key | What it fixes |
|---|---|---|---|
| 1 | Domain Pack | `(tenant_id, pack_id, version)` | the universe of valid semantics; `pack_supported_range` |
| 2 | Assistant Binding Annex | `(binding_id, binding_version)` + `supported_pack_version_range` | `annex_ceiling`, per archetype and per action class |
| 3 | Certified Client Overlay | overlay slug, e.g. `barclays-aml-uk` | `overlay_configured_posture`; narrows values, never structure |
| 4 | JAP | deployment id | `deployment_actual_posture` — what this deployment has earned |

**The invariant is one expression, and should be enforced as a refusal:**

```
runtime_effective_level <= deployment_actual_posture <= overlay_configured_posture
                        <= annex_ceiling <= pack_supported_range.max
```

That fits the posture Plato already has, where **every startup precondition is a refusal, not a
warning** — identity, posture and schema revision all fail the container rather than degrade it,
because a container booting into a broken state *"looks healthy to an orchestrator and takes
traffic."* A resolved binding whose chain violates the inequality is the same class of fault and
belongs at load, not at the turn that needs the authority.

**ABA §2 also names the dependency edges a release closure must cover** — `binding_id`,
`binding_version`, `pack_id`, `supported_pack_version_range`, `schema_spec_version`,
`supported_overlay_template_version`, `minimum_jap_version`, `evaluation_suite_id`, plus
`relay_family_id` / `peer_binding_compatibility` / `relay_integration_suite_id` for a governed
relay. §4.3's edges cover pack→pack only. If a release's `closure_digest` is meant to be the thing
that reproduces or refuses, these are the edges it is currently missing.

**Layers 2–4 are not this plan's work.** §7.4 exists so layer 1 does not foreclose them.
Concretely: keep `pack_supported_range` reachable from the manifest JSONB; do **not** let
`pack_version` acquire an `annex_ceiling` or `autonomy_ceiling` column (layer 2 owns those); and do
not overload `visibility` or `pack_status.status` to mean deployment posture.

**Binding stays out of this schema.** Which project or assistant uses which pack version belongs
with the organisation schema — `plato_project_resource` in `PLATO_ORG_SCHEMA_DESIGN.md` already has
the shape (`resource_type='pack'`, `resource_id`) and needs one addition: **a pack binding must
name a version, not just a pack.** Left as a note there rather than a fourth table here, because
the alternative is two tables that both claim to say what a project uses.

---

## 8. Why Plato, and the union that follows

`PLATO_PACK_TABLE_DESIGN.md` left this open — *"does this belong in Plato or in the JAPES service?"*
— and it should be closed: **Plato**, for the reason in §1 (the fourth instance of a shipped
pattern), and because the wider intent needs it.

**The intent:** Plato's database becomes a useful union of what are today four separate service
databases, so functionality now consolidated in the SDK can co-exist in **one container** instead of
v1's fleet. The tree supports it — one database, five prefixed schemas, one image in the roles japes
already supports (`api` / `worker` / `job:*`), and a stated strangler intent to replace Kernel and
`jazzx-assistant`.

**The strongest argument is not fewer containers — it is one transaction boundary.**
`app/assistant/promotion.py` is 1100 lines whose job is fanning a publish across services that own
different asset kinds — kernel for agents/tools/LLMs, Flowable for BPMN/DMN, KH for collections —
with the assistant row written last *so a partial failure is resumable*. Resumable is what you build
when you cannot be atomic. Co-locate those config tables and a pack publish becomes a transaction,
which is precisely what §7.3's publish gate needs.

**The discipline: union by migration, not by mirroring.** *"Never: another service's tables"* and
*"not a second source of truth"* are not in tension with the union — they forbid the interim state
where Plato holds a writable copy of a table its old owner still writes. Same database, separate
prefixed schemas, and a table moves only when its previous owner **stops writing**, with the
unconverted count reported as the cutover metric.

`PLATO_DB_TABLE_MAPPING.md` already bucketed kernel and assistant (8 covered, 6 to KH, 9 missing,
17 not ported). What Rev 2's inventory adds is the other two databases and one caution:

| Service | Shape | Absorbable? |
|---|---|---|
| **kernel** | config half — `agent`, `tool`, `llm`, `mcp_server_config`, `mcp_tool`; engine half — `chunk`, `embedding_vector`, `text_search_vector`, `collection`, `document` | **Config half yes** (the strangler target). **Engine half no** — that is KH's, per bucket B |
| **assistant** | `assistant`, `assistant_*` bindings, `configuration`, `conversation`/`message`/`invocation`, plus project/team/role/membership | **Config half yes** — what `promotion.py` writes. Organisation half is `PLATO_ORG_SCHEMA_DESIGN.md`'s |
| **juno** | ~100 table names, but **most are MLflow's own schema** — `runs`, `metrics`, `params`, `experiments`, `logged_models`, `registered_models`, `spans`, `trace_info` — plus gateway/permission tables and a long tail of fixtures (`mytable`, `my_table`, `thing`, `venue`, `some_table`) | **Mostly no.** The absorbable set is narrow and nameable: `juno_skill`, `juno_task_*`, `juno_schedule*`, `copilot_*`. Do not describe juno's database as a thing to merge |
| **eval-service** | `feedback`, `feedback_config`, `feedback_embedding`, `feedback_status_history`, `dataset`/`testcase`/`testcaserun`, `experiment`, `custom_scorer*`, `eval_template` | **Deliberately not.** `plato/models.py` says it: *"plato contains no feedback table"*, because a second durable copy makes "which one is right" a question somebody answers under pressure — **and a test asserts it** |

*Counting note:* `PLATO_DB_TABLE_MAPPING.md`'s 21/19 excluded tests and migrations, which is the
right method; the juno and kernel figures above include fixtures and should not be quoted as table
counts.

**Two honest limits.** The union collapses **config stores**, not **execution engines**: Flowable
and KH are runtimes, and `DomainPackStore` writing `canonical_domain_pack` into KH is a live
instance of that — which is why §3(b) projects it rather than absorbing it. And the `feedback`
collision is the recorded proof that two services claiming one table name is not hypothetical here.

**Tenancy at union scope.** Neither kernel nor assistant tables carry `tenant_id` at all; assistant
scopes by `project_id` and `creator_user_id`. So nothing transplants unchanged — every ported table
is re-keyed, and `verify_tables` says so mechanically. `pack_version` is the first table where
getting it wrong means one tenant reading another's domain configuration.

---

## 9. Decisions

Merged from all three sources; duplicates collapsed, accepters named.

| # | Decision | Gates | Accepter |
|---|---|---|---|
| **D1** | **Does publication go through Plato, or land here after the fact?** If a pack is authored in a repo and CI publishes it, Plato is a registry with a write API. If packs are *edited* in Plato, this schema needs a draft workspace that §4.1's immutability rule deliberately excludes. `certification_status: draft` in today's manifests suggests the latter was assumed; `depends_on` version-pinning suggests the former. **Everything else waits on this** — registry-after-the-fact and edit-in-place are different products. (Was the earlier note's Q2, and Rev 2's D6; the same question.) Note it does **not** wait on the config-versioning D1/D2 stalemate: that one is about who writes *assistant config*, where Studio is a rival writer, and no second surface currently claims to write packs | everything | Studio owner + SDK owner |
| **D2** | **Platform packs versus tenant packs.** A pack used by every tenant does not fit `tenant_id` in the PK. Three options: a reserved tenant id (simple, slightly dishonest); a `visibility` column with a nullable tenant (breaks the tenancy rule); copy-on-adopt, each tenant holding its own row (honest, duplicates rows — though `content_digest` means the blob is shared). **Recommend copy-on-adopt** unless it proves painful | `pack_version`'s PK | SDK owner |
| **D3** | **`packs_root` and the loader.** §6 recommends (a) materialize. Needs a yes, because the schema is unusable without a loader that resolves from the registry | §6, and the SDK change | SDK owner |
| **D4** | **Who makes the manifest carry the governance fields?** *Not* "which representation is canonical" — `done_JAPES_PACK_OBJECT.md` settles that the objects are deliberately distinct and composed. The live gap is its own: the manifest *"currently has only the operational keys, so `DomainPackHelper.from_yaml` would fail validation today"*, which is the same defect §7.2 found from the spec side. So: does Pack Studio emit the governance keys directly, or does a converter derive them from dialect 1? Shipping these tables for dialect 1 without answering it quietly elects the converter | §3(a), §7.2, D6 | Platform architect + Studio owner |
| **D5** | **Do the seven absent §7.8 fields get added to `DomainPack`, or does the spec get a v1.5 erratum?** One of the two has to happen: the freeze guidance says update the documents to reference the version, and the vocabulary rule says the spec wins | the migration's alias notes | Owner of the IIF spec set |
| **D6** | **Does KH or Plato own §7.8 after the strangler?** The *design* is settled — `DomainPack` is persisted via `DomainPackStore`, confirmed — but the path is **unwired**, so no records exist and the boundary has never been exercised. Two real options: wire it (that note's Stage B) and have Plato project it read-only, or let Plato own the governance record since it will own the release that pins it. Recommend the former, because reversing it later is a migration in two services; but decide it rather than inheriting it from an unwired call | the projection table, §7.4's resolver | Platform architect + KH owner |
| **D7** | **Table naming — drop the `plato_` prefix?** §4.5 recommends yes, since the schema prefixes. Trivial now, a migration later | the DDL | SDK owner |

**Already settled, do not relitigate:** the content digest primitive shipped as `jazzx_sdk/digest.py`
(add-beside, never widen); tenancy requires `tenant_id` in a key, not a column; `plato` holds no
feedback table, and eval-service owns that name.

---

## 9.1 D1, answered (2026-09-08)

**Both, in stages.** Veeru: *"We want the pack to both be importable from pack studio/jaci but also
the pack's own app to be able to craft/update it. We can do this in multiple stages though."*

This does **not** break §4.1, and the distinction is the whole reason §4.1 is worth keeping:

* a **published** `(pack_id, version)` stays immutable, because that is what answers *which pack
  version produced this decision*;
* *"the pack's own app crafts/updates it"* is a **draft**, and a draft is not a `pack_version` row.
  It gets its own mutable row and becomes an immutable `pack_version` at publish.

So the draft workspace D1 said edit-in-place needs is real and is deliberately outside the version
table, exactly where §4.1 put it. Two stages, in this order:

| Stage | Surface | Table |
|---|---|---|
| **1** | import a built pack — Studio or jaci's `config/packs/`, via CI or upload | `pack_version`, immutable |
| **2** | craft and update in the pack's own app | `pack_draft`, mutable; publish promotes it to a `pack_version` |

Stage 1 is §10's steps 2–3 unchanged. Stage 2 is additive and is what the acceptance criterion in
step 2 does *not* cover, so it needs its own.

**Taken as recommended, since each already carries one** (say so if any is wrong):

* **D2** copy-on-adopt — each tenant holds its own row, blob shared by digest.
* **D3** §6(a) materialize to a digest-keyed cache directory; the loader keeps its `Path` accessors.
* **D7** no `plato_` prefix — the schema prefixes. `pack_version`, `pack_dependency`, `pack_status`.

**One correction to §1's premise, from the code.** §1 and §8 say the pattern is *"protocol in
`jazzx_sdk`, durable implementation in Plato"*. It is not: `AssistantManifestStore` is an ABC in
`jazzx_sdk/manifest/store.py` and `DbAssistantManifestStore` is in
`jazzx_sdk/manifest/store_db.py` -- **both in the SDK**. Plato owns the *registration*
(`register_all`), the schema assignment (`TABLE_SCHEMAS`) and the migration, and its own stores are
only the Plato-specific ones (`settings_store.py`, `reference/model_overlay.py`). So a pack store
goes in `jazzx_sdk/pack/{store,store_db}.py` beside the loader it feeds, and the SDK-versus-Plato
split stays where the three existing instances put it. The non-goal is unaffected -- the SDK still
receives rows, never pack knowledge.

Also inherited from that pair, and not optional: **tenant scoping at construction, not per call.**
`DbAssistantManifestStore.__init__` takes `tenant_id` because *"a caller cannot omit the tenant on
a query, which is the mistake a per-call argument invites and the database cannot catch."*

---

## 10. Order of work

1. **Settle D1.** Nothing below is worth building against the wrong product shape.
2. **`pack_version` alone, with a loader that reads it** (§6a). That is enough to answer the
   provenance question, which is the point. Its acceptance criterion: *a pack published to a running
   Plato serves a new tenant with no deploy and no code change* — the criterion P1 claimed and did
   not test, because pack bytes still came from the container image.
3. **The publish gate** (§7.3): `lint_pack` + typed `DomainPack` construction + the first
   `pack_status` event, in one transaction. Refuse on failure. This is what stops the registry
   becoming a dumping ground, and it is mostly composition of things that exist.
4. **`pack_dependency`** when a second pack depends on a first in anger — cheap against an immutable
   version row, expensive to retrofit against a mutable one.
5. **`pack_status`** when certification is operated rather than declared; the projection of
   `canonical_domain_pack` (§3b) alongside it, since the two answer the same governance question
   from different sides.
6. **The resolver** (§7.4) when layer 2 exists. Not before — a resolver over one layer is an
   accessor.

Steps 2 and 3 carry the value. 4 and 5 are additive by construction, which is the whole reason §4.1
puts nothing mutable in the version row.
