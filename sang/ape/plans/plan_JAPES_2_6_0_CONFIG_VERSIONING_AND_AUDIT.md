# plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT — a version is a snapshot, not a label

Repos: `japes` (control-plane contracts + stores + runtime pinning). Consumers to check before each phase lands: `jaci`, `jazzx-assistant`, `juno` (Builder Studio side).

**Revision 1** — written against `japes` **HEAD `a93ed14`** on `dev`, one commit past the `d26bc0e` (`v2.4.4`) anchor the source design note cites; `_version.py:9` still reads `2.4.4`. Every file:line citation below was re-read in the working tree, not carried over from the note. Source design: *Skill, profile, and agent versioning and audit* (Notion, JazzX Platform v2.0). This plan is the executable form of that note's **Immediate recommendation**, plus seven findings from the verification pass that change the design in specific places.

**Read first.** `ape/CLAUDE.md` §§1–7 — in particular **§2 Simplicity First** (this plan adds five new tables and one new protocol family; every one of them must be defensible as "the minimum that solves the problem"), **§3 Surgical Changes**, and **§7 Symmetry** (the versioning gap exists identically in `SkillRegistry`, `ProfileRegistry`, `GuardrailRegistry`, and `TemplateRegistry` — §7's "check the full family, not just the nearest sibling" applies directly and Phase 3 decides how far to take it). Also `ape/plans/plan_JAPES_2_5_0_LOCATOR_AND_INVENTORY_DISCIPLINE.md` for the breaking-change discipline this plan inherits — a `strict_*` flag, a typed error, a CHANGELOG **"Breaking"** heading, and pre-landing checks against dependent packs — and `ape/plans/engineering_queue.md` for where this sits against everything else queued.

**In code.** `jazzx_sdk/agents/definition_store.py`, `jazzx_sdk/agents/definition_store_db.py`, `jazzx_sdk/server/agent_config.py`, `jazzx_sdk/agents/interactive/{spec,registry}.py`, `jazzx_sdk/_registry.py`, `jazzx_sdk/manifest/{store,assistant_manifest,spec_binding,loader,bundle,publish}.py`, `jazzx_sdk/evaluation/{prompt_registry,prompt_registry_db}.py`, `jazzx_sdk/fabric/db/store.py`, `jazzx_sdk/fabric/guidance/{schema,lifecycle}.py`, `jazzx_sdk/fabric/canonical/trace.py`, `jazzx_sdk/handlers.py`, `common/core/models.py`, `jazzx_sdk/statemachine/`.

---

## The one-sentence version

Skills, profiles, and agents are identified by **name** and resolved against **whatever is currently stored under that name**, so publishing a new skill silently changes every agent that referenced it and a rollback restores yesterday's bytes against today's dependency graph — Phases 1–2 stop the data loss that is happening right now, Phases 3–5 make a version an immutable snapshot, and Phase 6 is the only phase that changes what runtime actually executes.

---

## What the verification pass confirmed, and seven things it changed

Every anchor in the source note holds at `a93ed14`. Restating the load-bearing ones, because Claude Code should not re-derive them:

- `NamedRegistry._put` is `self._items[self._key(name)] = item` (`_registry.py:32-33`). One object per name, overwrite on re-register. `SkillRegistry.register` (`registry.py:76-77`) and `ProfileRegistry.register` (`registry.py:137-138`) both go through it. Tiering (`registry.py:60-68`) blocks a *lower-trust* shadow; it does not preserve a version.
- `Skill.version` is declared catalog metadata that "none of these five touch execution" in its own comment (`spec.py:83-86`). `SkillRegistry.catalog_text` renders it (`registry.py:120`) and nothing else reads it.
- `InteractiveAgentSpec` (`spec.py:178+`) has `agent_id` and no version field of any kind.
- `AgentDefinition` (`definition_store.py:29-53`) carries `created_at`/`updated_at` and nothing else. `DbAgentDefinitionStore.put` is `s.merge(...)` on a `name`-primary-key row (`definition_store_db.py:35`, `73-78`). `PUT /agents/{name}` preserves `created_at` and replaces everything else (`agent_config.py:129-152`); `DELETE` removes the only row (`agent_config.py:154-165`).
- `ManifestRecord` is the one immutable-history shape in the tree — content hash, `supersedes`, status, `created_at` (`manifest/store.py:50-72`) — with `get(version)`/`history`/`rollback` (`:141-165`), in-memory only. **Confirmed:** `rg "AssistantManifestStore" --include=*.py jazzx_sdk` returns the ABC, the in-process impl, and one docstring mention in `loader.py:32`. There is no DB-backed manifest store despite `tests/test_fabric_materialize_db_manifest.py` and `tests/test_client_layer_fabric_manifest_store.py` existing — those are about pack/fabric manifests, a different artifact. Do not assume otherwise.
- `AssistantManifest.profile_ref` and `allowed_skills` are `str` and `list[str]` (`assistant_manifest.py:43`, `59`), resolved against live registries at build time (`spec_binding.py:245-247`). `resolve_pack` checks `pack_version_range` against the one current pack (`loader.py:129-170`).
- `VersionBundle.skills_version` is a single `str | None` (`trace.py:128`) for an arbitrary number of independently versioned skills.
- The audit seam exists and is unused: `CallerIdentity.from_context()` (`handlers.py:369-390`), `AuditModel` (`common/core/models.py:92-96`), `Repository._stamp_created` (`fabric/db/store.py:153-160`).

Seven findings that are **not** in the source note and that change what to build:

**F1 — `manifest/bundle.py` and `manifest/publish.py` already are the closure-export and promotion seam.** `pack_bundle(groups, name=...)` packs `{group: {entry_name: bytes}}` into one zip with a `BundleManifest` descriptor (`bundle.py:47-61`), zip-slip-safe on unpack. That shape *is* an `AgentRelease` closure carrier: `{"skills": {...}, "profiles": {...}, "manifest": {...}}`. Phase 4 must reuse it rather than invent a second export format.

**F2 — but `Publisher`'s documented conflict policy is the exact anti-pattern this plan exists to remove.** `publish.py:5-7`: *"A `Publisher` owns its own conflict policy entirely — upsert-by-name, skip-duplicate, reuse-existing-by-name."* Publishing an **immutable version** cannot be upsert-by-name. The correct policy for a versioned asset is **create-or-verify-digest**: if the `version_id` already exists, assert the digest matches and treat it as published; if the digest differs, fail loud. Phase 4 adds that as a named policy and states plainly that the existing three are not admissible for versioned config. This is a change to a module's contract, so it gets the breaking-change pattern.

**F3 — there is no optimistic-concurrency precedent anywhere in `jazzx_sdk`.** `rg -i "if-match|etag|expected_revision|optimistic" --include=*.py jazzx_sdk` returns exactly one hit: `knowledge_hub_client.py:2154`, where japes is the *client* passing `if_none_match` to someone else's ETag. Nothing in japes *serves* a conditional write, and nothing raises `409`. Phase 1's expected-revision check is therefore **new machinery, not a copy of a sibling** — which per §7 means it should be designed once as a small shared helper and applied to drafts and aliases both, not hand-rolled twice.

**F4 — `jazzx_sdk.statemachine` + `GUIDANCE_LIFECYCLE` is the house precedent for actor-gated status transitions, and it applies here.** `GUIDANCE_LIFECYCLE` (`fabric/guidance/lifecycle.py:35-46`) is a data transition table admitted by `TransitionEngine`, giving actor-class enforcement, terminal immutability, and typed `Refusal`s for free. `manifest/store.py:12-19` deliberately declined it because *"that machine encodes a human-reviewer approval workflow, which this phase never asked for."* **That reasoning does not carry over.** `AgentRelease.status` (`candidate | approved | retired`) and the alias move *are* a human approval workflow with an approver identity — the note's own acceptance criteria demand a queryable approver. So Phase 5 rides `statemachine`; it does not add a bare enum plus hand-rolled checks.

**F5 — `_stamp_created` stamps only on the create path, and `DbAgentDefinitionStore` bypasses `Repository` entirely.** `fabric/db/store.py:153-160` stamps both created-by and updated-by attrs from `CallerIdentity`, inside the create branch, and no-ops silently when the model lacks those attributes. `DbAgentDefinitionStore` calls `db.repository(AgentDefinitionRecord)` only to register metadata (`definition_store_db.py:48`) and then uses `s.merge()` directly (`:76`). Two consequences for Phase 1: adding audit columns alone would stamp nothing, and there is no update-path stamping to inherit. Both must be built.

**F6 — `content_version()` is 12 hex chars of SHA-256 and is shared by three artifacts.** `prompt_registry.py:21-23`, reused by `GuidanceAsset._derive_version` (`fabric/guidance/schema.py:77-87`) and `ManifestRecord._derive_version` (`manifest/store.py:63-72`). Widening it in place changes every stored `PromptVersion.version`, `GuidanceAsset.version`, and `ManifestRecord.version` value — a silent data migration across three subsystems. Add `content_digest()` (full 64-hex, canonical JSON) as a **new** function beside it; keep `content_version()` as the display tag the note itself says it is good for.

**F7 — `AgentDefinition.agent_id` is a computed property over mutable content, and it is an indexed lookup key.** `definition_store.py:41-53` returns `spec.agent_id or spec.name`; `definition_store_db.py:37` indexes it; `GET /agents/by-agent-id/{agent_id}` resolves against it (`agent_config.py:107-116`). So a `PUT` that fills in a previously-`None` `spec.agent_id` **changes the agent's identity** while the row keeps its name, and every prior reference by the old id 404s. The note treats `agent_id` as "the stable logical identity" — at HEAD it is not stable. Phase 1 must store `agent_id` at creation and refuse a `PUT` that would change it.

---

## Answering the objection this will draw

**"This is five new tables and a protocol family to fix a problem nobody has hit."** Two answers. First, the failure is silent by construction: an agent whose behavior changed because a shared skill was re-registered produces no error, no trace marker, and no diff — the absence of reported incidents is not evidence, it is the symptom. Second, Phases 1–2 are not new architecture; they stop concurrent editors from overwriting each other on a write path that already exists and already has authenticated callers. Land those two on their own merits and re-argue 3–7 afterwards if the appetite is not there.

**"Just add `version` and `updated_by` to the existing rows."** The source note pre-empts this and it is worth keeping verbatim: that would *label state without preserving it*. A `version` string on a row that still gets overwritten tells you the name of the thing you just lost.

**"`AssistantManifestStore` already does versioning — extend that."** It versions the manifest's own bytes and resolves `profile_ref`/`allowed_skills` against live registries at build time (`spec_binding.py:245-247`). Rolling back to `M1` restores old manifest bytes and then binds them to today's profile and today's skills. The note's phrasing is exact: **revalidation against today's graph, not reproduction of yesterday's graph.** Extending it without pinning the closure would make the gap harder to see, not smaller.

---

## Three decisions that gate real work

**D1 — Who is the durable system of record?** The note recommends Builder Studio owns authoring/governance and JAPES owns contracts/validation/runtime, with the JAPES DB acceptable as the *first* control-plane store behind a protocol. That conditional has to be resolved before Phase 3 chooses whether `DbConfigAssetStore` is a reference impl or the production store, because it determines whether tenant scoping is enforced in japes or inherited from Studio. **Owner: SDK owner + Studio owner. Gate for Phase 3.** Phases 1, 2 are unaffected — they operate on a store that already exists.

**D2 — `content_digest()` beside `content_version()`, or widen in place?** Per F6, widening touches three subsystems' stored values. The recommendation is a new function; **confirm before Phase 3.** If widening is chosen it needs its own migration phase and this plan grows one.

**D3 — Is there any tenant column in these stores today?** The note requires tenant isolation "in every key and lookup, not only in UI filtering," but the verification pass did not audit this. Before Phase 3, run:

```
rg -n "tenant_id|tenant" --include=*.py jazzx_sdk/agents jazzx_sdk/manifest jazzx_sdk/evaluation jazzx_sdk/fabric/db
rg -n "tenant" --include=*.py common/core
```

If tenancy is entirely absent from japes' config stores, adding it in Phase 3 is a schema decision with Studio, not a japes-local one — escalate to D1's owners rather than inventing a column shape. If it is present somewhere, match that shape.

---

## Phase 1 — actor attribution and optimistic concurrency on the write path that exists (P0)

**Why P0 and why first:** `PUT /agents/{name}` is last-write-wins today, authenticated, and has consumers. Every day it stays that way is a day of unrecoverable overwrites. This phase adds no new stores and no new concepts — it is the only phase in this plan that is pure defect-closure, and it is a prerequisite for every other phase's audit criteria.

**Tasks**

1. **Store `agent_id`; stop computing it.** Per F7: `AgentDefinition` gains a stored `agent_id: str` set at creation from `spec.agent_id or spec.name`, with the computed property retained as a deprecated alias for one release. `PUT` refuses (422) a body that would change a stored `agent_id`. Keep `definition_store_db.py`'s indexed column; it now indexes a stable value.
2. **Actor columns that actually get written.** `AgentDefinition` gains `created_by`/`updated_by`. Per F5, `DbAgentDefinitionStore.put` must stamp them itself — it bypasses `Repository`, and `Repository._stamp_created` has no update path anyway. Resolve the actor once via `CallerIdentity.from_context()` (`handlers.py:369-390`), never from request JSON.
3. **Fail closed on an unresolved actor in a deployed posture.** `_stamp_audit` with `uid=None` writes NULL silently, which is right for optional business-record audit and wrong for publishing agent behavior. Add an explicit check in the write path: when `deployed_posture()` is true and `CallerIdentity.from_context().is_anonymous`, raise. This mirrors `agent_config.py:86-91`'s existing `_require_write_auth` shape — put it next to that function, not in the store.
4. **`revision` + `If-Match`.** `AgentDefinition` gains a monotonic `revision: int`. `PUT /agents/{name}` reads `If-Match`; a mismatch is `409`, a missing header on an existing row is `428 Precondition Required` (or `409` — pick one and document it; do not default to last-write-wins). Per F3 this is new machinery: build it as one small helper (`jazzx_sdk/server/concurrency.py` or similar) that Phase 5's alias move reuses verbatim. Do not hand-roll it twice.
5. **Do not touch `DELETE` in this phase.** Retiring hard delete is Phase 7 and is breaking; leaving it alone keeps Phase 1 non-breaking except for the new required header, which lands behind a `strict_concurrency` flag defaulting off for one release, on in japes' own CI immediately.

**Acceptance**

- Two concurrent `PUT`s with the same `If-Match` value: one succeeds, one returns `409`. Neither silently wins. Asserted against both `InProcessAgentDefinitionStore` and `DbAgentDefinitionStore` — `tests/test_agent_config_api.py` and `tests/test_agent_definition_store.py` are the homes.
- A `PUT` under an authenticated context persists that caller's id in `updated_by`, readable back through `GET`. A second `PUT` by a different caller changes `updated_by` and leaves `created_by` alone.
- With `deployed_posture()` true and no resolvable caller, the write is refused — not stored with a NULL actor.
- A `PUT` whose body would change a stored `agent_id` returns 422; `GET /agents/by-agent-id/{old}` keeps resolving.
- `strict_concurrency=False` reproduces today's behavior byte-for-byte on the existing suite.

**Size:** S–M. **Risk:** the `428`-vs-`409` choice and the flag default are the only contested bits; both are one-line decisions.

---

## Phase 2 — `ConfigAuditEvent`, append-only (P0, S)

**Why P0:** state attribution on a row answers *who last wrote this*. It cannot answer *who approved it*, *who rolled it back*, or *what the intent was* — and those are three of the note's acceptance criteria. Phase 1 without Phase 2 gives a last-writer name and no history.

**Tasks**

1. The record, per the source note: `event_id`, `tenant_id`, `target_kind`, `target_id`, `target_version_id`, `action` (`create|edit|publish|approve|promote|rollback|retire`), `actor_id`, `actor_type` (`user|service|migration`), `occurred_at`, `request_id`/`trace_id`, `source`, `reason`/`change_summary`, `before_digest`/`after_digest`.
2. Correlate with the existing trace context rather than inventing a request id — `handlers.py`'s `inject_current_trace_context` / `with_trace_context` (`handlers.py:340-344`) is already the one place that assembly lives. Read it before adding a field.
3. Protocol + in-process impl + `fabric.db` impl, in that order, matching the `prompt_registry` / `prompt_registry_db` pairing exactly (`prompt_registry.py:35-56` protocol, `:58-95` in-process, `prompt_registry_db.py:42+` durable). **Table DDL belongs in the consuming service's alembic** — the same note both DB stores in this tree carry (`definition_store_db.py:7-10`, `prompt_registry_db.py:4-6`). Point `target_metadata` at the store's `metadata`.
4. Emit from Phase 1's write path. An audit store with no emitter is the capability-without-a-caller defect the 2.5.0 plan's Risk 6 names.

**Acceptance**

- A `PUT` writes exactly one `edit` (or `create`) event carrying the resolved actor, the trace id, and `before_digest`/`after_digest`.
- Events are append-only: no code path in `jazzx_sdk` updates or deletes one. Asserted by test, not by convention.
- Querying by `target_id` returns the full ordered history for that target.

**Size:** S. Independent of Phase 1's concurrency work; can be built in parallel but must land after task 4's emitter has something to emit from.

---

## Phase 3 — versioned immutable `Skill` and `AgentProfile` stores behind protocols (M–L)

**Gate: D1, D2, D3 all resolved.** Do not start otherwise.

**The reuse seed is `prompt_registry`, with five named gaps.** `PromptRegistry` (`prompt_registry.py:35-56`) already gives content-hash versioning, explicit version lookup, movable aliases, a protocol seam so a client's own registry conforms, and a durable `fabric.db` backend with a two-table shape (`prompt_registry_db.py:24-39`). What it does not give, and what this phase adds:

1. **No actor.** `PromptVersion` has `name`/`version`/`content`/`metadata`. Add `created_by`, per Phase 1's resolution path.
2. **No tenant scope** (pending D3).
3. **12-hex digest** (F6) — add `content_digest()`, keep both on a published version, and be explicit that semver communicates compatibility while the digest proves content.
4. **No optimistic concurrency on the alias row.** `set_alias` (`prompt_registry_db.py:101-117`) is a blind read-then-write inside one session — two concurrent promotions race. Phase 5 needs `AgentAlias.revision`; add `revision` to the draft/alias shape here and reuse Phase 1's helper.
5. **No unique constraint.** `PromptVersionRow` has an autoincrement `id` PK with plain indexes on `name`/`version` (`prompt_registry_db.py:27-29`) — nothing prevents two rows for the same `(name, version)` beyond the store's own read-first check, which is not race-safe. Add the constraint.

**Tasks**

1. `ConfigAsset` / `ConfigAssetVersion` / `ConfigDraft` per the source note's envelope, one shape serving `kind in {skill, profile}`. Released version rows append-only; an edit creates a row.
2. Protocol first, in-process impl, `fabric.db` impl. Same three-file shape as `prompt_registry`.
3. **Do not change `SkillRegistry`/`ProfileRegistry` in this phase.** They stay the runtime-facing name→object catalogs. The versioned store is a new, additive layer that Phase 4 resolves *from*; nothing in the interactive-agent path changes until Phase 6. Per CLAUDE.md §3, this keeps the blast radius at "new module" rather than "every agent construction site."
4. Backfill: import current skills/profiles/definitions as version 1 with `actor_type="migration"`, preserving original timestamps where known. This is the note's migration step 4 and it is a real script with a real test, not a footnote.
5. **§7 check:** `GuardrailRegistry` and `TemplateRegistry` share `NamedRegistry`'s overwrite-by-name shape. Decide explicitly whether they are in scope. Recommendation: **out** of this phase, documented as out, because no product requirement pins a guardrail version yet — but say so in the module docstring so the asymmetry reads as a decision rather than an oversight.

**Acceptance**

- Two versions of one skill coexist and are independently fetchable by `version_id`.
- Registering byte-identical content returns the existing version (dedup), and does **not** create a second row.
- A stale draft update returns `409`.
- The version author is queryable with a timestamp and a trace correlation.
- `(asset_id, version_id)` is unique at the DB level; a forced duplicate insert raises.
- The existing `tests/test_skill_registry.py` and `tests/test_prompt_registry.py` suites pass unchanged — this phase adds, it does not modify.

**Size:** M–L. **Risk:** scope creep into the registries. The task-3 boundary is the mitigation and it is not negotiable.

---

## Phase 4 — the release resolver and closure digest (L)

**Tasks**

1. `Agent` / `AgentRelease` / `AgentReleaseDependency` per the source note. `closure_digest` over the **ordered** resolved dependency graph — fix the ordering rule in the docstring, because an unstable ordering makes the digest useless for the rollback-reproduces-the-closure acceptance test.
2. **Resolve, then freeze.** Manifest, profile, every skill, every `spec_ref`'d child profile, pack, and any other dependency get pinned to exact version ids at publish time. `Skill.spec_ref` (`spec.py:72-81`) is the composition edge — it pins a child profile version, and `ProfileRegistry._spec_ref_edges`/`_find_composition_cycle` (`registry.py:169-207`) is the existing graph walk to reuse.
3. **Reuse `ProfileRegistry.validate()`'s logic, not its lookup.** `registry.py:209-269` already checks dangling skills, unknown MCP servers, guardrail-phase mismatches, and composition cycles, and raises one aggregated `ValueError` listing all problems. That aggregation behavior is the right shape for a publish gate. Change only the lookup key: from a live name→object registry to an exact-version reference set. Do not fork it.
4. **`pack_version_range` resolves to one exact pack version at publish time.** `resolve_pack` (`loader.py:129-170`) evaluates the range against the one current pack — correct as a deploy-time gate, insufficient as a runtime pin. Record the resolved `pack_version` on the release.
5. **Floating dependencies are explicit or fatal.** An external Kernel/MCP capability with no immutable version/digest/ETag is marked floating; a production release either fails to publish or carries a visibly approved exception. Nothing in between.
6. **Closure export reuses `pack_bundle`** (F1). `{"manifest": ..., "profiles": ..., "skills": ...}` is already the shape it takes (`bundle.py:47-61`).
7. **Add a `create-or-verify-digest` publisher policy** (F2) and state in `publish.py`'s docstring that upsert-by-name is not admissible for a versioned asset. This changes a documented contract — CHANGELOG **Breaking** heading, and check `juno`/`jaci` for existing `Publisher` implementations first.

**Acceptance**

- Publishing a new version of a skill does not alter any existing release's effective spec or `closure_digest`.
- Rollback to a prior release reproduces the same `closure_digest` **and** the same effective spec, on a graph whose current registries have since changed. This is the single test that proves the whole plan; write it first.
- A release with an unresolved dependency fails publishing with an aggregated message naming every problem at once (matching `validate()`'s existing behavior).
- A floating external dependency either blocks a production publish or appears in an approved-exception list on the release.
- Re-publishing an identical release is a no-op; re-publishing a *different* payload under an existing `version_id` fails loud.

**Size:** L. **Risk:** the ordering rule for `closure_digest` and the floating-dependency vocabulary are both design surface. Settle both in writing before code.

---

## Phase 5 — aliases, promotion, rollback (M)

**Tasks**

1. `AgentAlias(agent_id, environment, release_id, revision, updated_at, updated_by)`. Promotion and rollback are atomic pointer moves; releases are never mutated.
2. **Ride `jazzx_sdk.statemachine`** (F4). `AgentRelease.status` transitions (`candidate → approved`, `approved → retired`) go in a transition table like `GUIDANCE_LIFECYCLE` (`fabric/guidance/lifecycle.py:35-46`), which gives actor-class enforcement, terminal immutability, and typed `Refusal`s without new code. A blocked promotion is a designed governance outcome, not an exception — that is the house posture and it is the right one here.
3. Alias updates take `If-Match` on `revision`, reusing Phase 1's helper.
4. Every promote/rollback emits a Phase 2 audit event carrying the approver and the before/after release ids.

**Acceptance**

- A stale alias update returns `409`.
- Rollback is an alias move: both releases are byte-identical before and after.
- Approver, promoter, and rollback actor are each queryable with timestamps.
- A promotion attempted by an actor without the required class is refused with a typed `Refusal`, not a 500.

**Size:** M. Depends on Phase 4.

---

## Phase 6 — pin runtime and trace, dual-read first (M)

This is the only phase that changes what executes. Everything before it is additive control plane.

**Tasks**

1. Runtime input carries `agent_id` + exact `release_id`, resolved once from the environment alias at dispatch. The worker loads the release, **verifies the closure digest**, and does not re-resolve skill names against a mutable registry.
2. **Dual-read.** When no release exists, read the legacy definition and emit a `legacy_unversioned` trace marker. Per the note: do not silently call legacy content reproducible.
3. Extend `VersionBundle` (`trace.py:116-129`): add `agent_release_id` and a structured per-dependency ref list. Retain `skills_version` and `extra` as the compatibility bridge — `model_versions` is already a required non-empty dict with a validator (`trace.py:132-138`), so follow that precedent for whichever new field is genuinely required.
4. Stamp per run/turn: `agent_id`, `agent_release_id`, manifest and profile version ids + digests, each invoked skill's asset/version id + digest, tool/guardrail/pack/model pins actually used, and any approved floating exception.

**Acceptance**

- A trace from a released agent names the exact release and every skill version actually invoked.
- A trace from a legacy definition carries `legacy_unversioned` and no release id.
- A release whose stored `closure_digest` does not match its recomputed closure fails at load, before any turn runs.
- The existing interactive-agent suite passes with dual-read on and no releases present.

**Size:** M. Depends on Phases 4–5.

---

## Phase 7 — retire mutable production writes (breaking, no estimate)

`PUT /agents/{name}` becomes a **draft** write, never a deployed-definition replacement. Production promotion requires the release endpoint. Hard `DELETE` becomes archive/retire; immutable versions and audit events are not deleted through ordinary product APIs.

Full breaking-change pattern: `strict_*` flag, typed error, CHANGELOG **Breaking** heading, and a pre-landing audit of every caller in `jaci`, `jazzx-assistant`, and `juno`. **Do not put a day estimate on this phase** until that audit is done — the 2.5.0 plan's Phase 4 convention.

---

## Deliberately not in this plan

- **`GuardrailRegistry` / `TemplateRegistry` versioning.** Same overwrite-by-name shape, no product requirement pinning a version. Phase 3 task 5 documents the exclusion as a decision. Revisit when a pack needs a pinned guardrail.
- **Policy/client/execution profiles** (`fabric/canonical/profiles.py`). Their `version` string overlaps this vocabulary by name only; they are not assistant profiles. Phase 0's naming work must say so in the docs, and nothing else here touches them.
- **A shared cross-tenant JAPES config store.** The note is explicit: a JAPES service may cache or project immutable releases in its own DB, but must not become a second source of truth. This matches `DbAgentDefinitionStore`'s existing posture — each consuming service owns its database and migrations.
- **Semver auto-classification from schema diffs.** A prompt-only edit can be breaking. Major/minor/patch stays author-reviewed and eval-gated.
- **Merging `AssistantManifest` and `InteractiveAgentSpec`.** `manifest/store.py:6-10` records that the manifest-vs-profile question is contested and that the record shape holds either way. This plan inherits that neutrality; it does not settle it.

---

## Sequencing and gates

```
Phase 1  (actor + concurrency, P0, S–M)   ──►  start now, no gate. Highest value per day.
Phase 2  (audit events, P0, S)            ──►  build in parallel with 1; land after 1's emitter
Phase 0  (name the concepts, XS)          ──►  anytime; docs + type aliases only
Phase 3  (versioned stores, M–L)          ──►  gate = D1 (system of record), D2 (digest),
                                                D3 (tenant audit). All three, in writing.
Phase 4  (release resolver, L)            ──►  after Phase 3. Write the rollback-reproduces-
                                                the-closure test FIRST.
Phase 5  (aliases + promotion, M)         ──►  after Phase 4
Phase 6  (runtime + trace pinning, M)     ──►  after Phase 5; dual-read before pinning
Phase 7  (retire mutable PUT, breaking)   ──►  after Phase 6 AND after the caller audit.
                                                No estimate until then.
```

**Phases 1 and 2 stand alone.** If appetite for the full arc is not there, they are still worth landing: they close an active data-loss path on an authenticated endpoint. Do not hold them hostage to D1.

**One ordering trap.** Phase 6's dual-read must land before anything disables the legacy path, and the `legacy_unversioned` marker must be emitted from the first day of dual-read — not added later. A migration window with no marker is indistinguishable from a migration that already finished.

---

## Risks

1. **Phase 3 grows into a registry refactor.** The single most likely failure. Mitigation: task 3's boundary — the versioned store is additive, the registries are untouched until Phase 6. If a Phase 3 diff touches `registry.py` or `_registry.py`, it has gone wrong.
2. **`closure_digest` is unstable across runs.** A dict-ordering or float-formatting difference makes the rollback test flap and the digest worthless. Mitigation: canonical JSON with sorted keys, one shared serializer, and a test that computes the digest twice from independently constructed objects.
3. **D1 never gets answered and Phase 3 starts anyway.** Mitigation: Phases 1, 2, 0 are all unblocked, so there is real work available while the decision is pending. There is no schedule pressure to guess.
4. **The plan ships stores with no caller** — the defect the 2.5.0 plan's Risk 6 names, and it is live here in Phases 2 and 3. Mitigation: every phase names its adopter. Phase 2's is Phase 1's write path. Phase 3's is Phase 4's resolver. **Phase 3 must not land before Phase 4 has started**, or japes gains three tables nobody reads.
5. **`common` is a submodule.** `AuditModel` lives in `common/core/models.py`. If Phase 1 or 3 needs a change there it is a cross-repo change with its own review, not an edit in this tree. Check before assuming.
6. **HEAD moves fast.** `a93ed14` landed the same day this plan was written, and the source note was anchored one commit earlier. Re-run every `rg` in this document before estimating; prefer re-running them to trusting the counts.
7. **Backfill (Phase 3 task 4) silently mis-attributes.** Importing current state as version 1 with a `migration` actor is correct; importing it with a *real* actor id inferred from a timestamp is fabrication. Mitigation: `actor_type="migration"` is not optional on backfilled rows, and a test asserts no backfilled row carries `actor_type="user"`.

---

## Why this is the right slice

The source note's own framing is the strongest argument for the ordering above: the platform can answer *what is configured now* and cannot answer *what ran, who approved it, whether rollback restores behavior, or whether two editors collided*. Phase 1 answers the fourth question in a week and stops the bleeding. Phase 2 answers the second. Phases 3–5 answer the first and third, and they are the ones that need D1 settled.

And the ratio is better than it looks, because the harder halves are already built: an immutable-record store with content hashing, supersession, history, and rollback (`manifest/store.py`); an aggregating validator that already walks the composition DAG and reports every problem at once (`registry.py:209-269`); a versioned-plus-aliased store with a protocol seam and a durable backend (`prompt_registry`); a zip-slip-safe closure bundler and a promotion orchestrator (`manifest/bundle.py`, `manifest/publish.py`); an actor-gated transition engine with typed refusals (`statemachine` + `GUIDANCE_LIFECYCLE`); and a caller-identity seam wired into the DB layer (`handlers.py:369-390`, `fabric/db/store.py:153-160`). What is missing is that none of them are pointed at *configuration*. That is a wiring-and-contracts plan, not an architecture plan — with the honest exception of Phase 4, which is genuinely new.

---

## Running this with Claude Code

**Per-phase protocol.** One phase per session. Open every phase by re-verifying its anchors at current HEAD — line numbers in this document are from `a93ed14` and will drift:

```
git -C /Users/sangit/src/japes log --oneline -1
rg -n "<the symbol named in the task>" --include=*.py jazzx_sdk
```

If an anchor has moved, fix the anchor and continue. If an anchor is *gone*, stop and report — something landed that this plan did not account for.

Then, per CLAUDE.md §4: restate the phase's acceptance criteria as the success condition, write the failing test first where the acceptance criterion is a behavior, and loop until it passes. For Phase 4 specifically, the rollback-reproduces-the-closure test is the definition of done and gets written before any implementation.

**Guardrails.**

- **Do not touch** `_registry.py`, `agents/interactive/registry.py`, or `agents/interactive/spec.py`'s runtime fields before Phase 6. A diff there in Phases 1–5 means scope has escaped.
- **Do not widen `content_version()`** (F6). Add beside it.
- **Do not edit `common/`** without flagging it as a cross-repo change (Risk 5).
- **Do not add DDL to japes' alembic.** Table DDL belongs in the consuming service's migrations; point `target_metadata` at the store's `metadata`, matching `definition_store_db.py:7-10` and `prompt_registry_db.py:4-6`.
- **Do not `git push`** (CLAUDE.md, Git Commit and Push Policy). Commits are fine; pushing is the user's call. No AI-attribution trailer in commit messages.
- **Do not infer semver from a diff.** A prompt-only change can be breaking.
- Per CLAUDE.md §1: if a task here is ambiguous or a simpler shape exists, say so before implementing rather than picking silently. Several tasks above deliberately state a recommendation and name the decision as open — those are invitations to push back, not settled instructions.

**Bump `_version.py` and `pyproject.toml` together** (`tests/test_version_sync.py` asserts equality). Phases 1–2 are a minor bump; Phase 7 is the one that needs the major-version conversation CLAUDE.md §5 asks for.
