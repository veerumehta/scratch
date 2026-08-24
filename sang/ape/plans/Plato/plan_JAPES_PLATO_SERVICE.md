# plan_JAPES_PLATO_SERVICE — the deployable the SDK has been deferring work to

Repos: `japes` (new `plato/` package + SDK-side deltas). Consumers to check before any phase that changes shared behavior: `jaci`, `jazzx-assistant`, `juno`, `macer`, `k9`. Cross-repo reads required by name: `assistant` (`app/assistant/promotion.py`), `eval-service`.

**Target release: JAPES 2.5.0 — Plato.** (The two `ape/plans/` filenames still reading `2_5_0` were retargeted to earlier 2.4.x releases; those numbers are legacy labels, not claims.)

**Revision 2** — written against `japes` **HEAD `3714a5e`** on `dev` (v2.4.7, committed, unpushed; `_version.py` reads `2.4.7`). Every anchor below was read in the working tree, not carried over from prose. **R2 folds in the six items R1 queued for 2.4.7, all of which landed in `3714a5e` while R1 was being written** — see *Already landed in 2.4.7*. Three of the six shipped in a better shape than R1 proposed; the differences are recorded rather than smoothed over, because they change what remains. Companion architecture/charter doc (audience: platform architects, the D1/Studio conversation): *Plato — Platform Two*, in project knowledge.

**Read first.** `CLAUDE.md` §§1–7 — especially **§2 Simplicity First** (this plan adds a package, a Dockerfile, an alembic tree and five schemas; every one must be defensible as the minimum that solves the problem), **§3 Surgical Changes** (the SDK-side deltas must not become a refactor), and **§7 Symmetry** (Plato supplies durable backings for three ABCs that all share the same in-process shape — do the family, not the nearest sibling). Also `plans/plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT.md` and its **D1/D2/D3 addendum** (this plan is that addendum's **shape 3**, made concrete), `status/done_JAPES_2_4_0_UAF_PHASE1_ADDITIVE.md` (its "blocked on someone else" list is this plan's scope), and `plans/engineering_queue.md`.

**In code.** `jazzx_sdk/server/{app,agent_config,concurrency,governed_http,web,settings_api}.py`, `jazzx_sdk/launcher.py`, `jazzx_sdk/manifest/{store,assistant_manifest,spec_binding,loader,bundle,publish}.py`, `jazzx_sdk/agents/interactive/{spec,registry,session}.py`, `jazzx_sdk/agents/{definition_store,definition_store_db}.py`, `jazzx_sdk/audit/{events,events_db}.py`, `jazzx_sdk/authority/context.py`, `jazzx_sdk/observability/trace_routes.py`, `jazzx_sdk/fabric/canonical/trace.py`, `jazzx_sdk/llm/{cost,model_cards,_model_data}.py` + `model_data.json`, `jazzx_sdk/platform_catalog.py`, `jazzx_sdk/runs/`, `jazzx_sdk/queue_processor.py`, `common/core/keto/`.

---

## The one-sentence version

Thirteen UAF phases and two config-versioning phases shipped the *primitives* — manifest store with rollback, session lifecycle, audit events, optimistic concurrency, the skill IO record, the context middleware — as **in-process ABCs with no durable backing and no HTTP surface**, so `plato/` supplies the missing half: durable stores, an assistant-id-addressed multi-tenant API, generated skill routes, and the config system-of-record that the addendum's D1 shape 3 describes.

---

## Already landed in 2.4.7 — what R1 queued, and what changed

All six items R1 listed for the patch release shipped in `3714a5e` (33 files, +3337/-183) before R1 was circulated. Recorded here because three shipped differently, and the differences change what remains.

| R1 item | Shipped as | Difference that matters |
|---|---|---|
| `content_digest()` | `jazzx_sdk/digest.py` — dependency-free, canonical JSON, sorted keys | **Better placement than R1 proposed.** R1 said "beside `content_version()`"; the layering argument R1 missed is that `llm` sits *below* `evaluation` (which imports `llm` in nine places, never the reverse), so a digest under `llm` could not reach it without inverting the dependency. `content_version()` now delegates and is byte-identical. |
| Version the model data | `cost.MODEL_DATA_VERSION` = digest of the loaded blob | **Derived, not hand-maintained.** A reformat that changes no value is not a new version. |
| Record overlay registrations | `OverlayRegistration(model, kind, source, overwrote)` + `overlay_registrations()`, `source` inferred from the caller's frame | Richer than asked. Its rationale is the one this plan cares about: *"two processes on the same `MODEL_DATA_VERSION` can answer differently and nothing records why."* |
| Stamp the version into the run | `model_data_version_tags()` → `observability.build_run_tags` / `ensure_run` extra | **Run tags, not the canonical trace.** Its docstring gives the same reason this plan does — `VersionBundle` is Spec-v1.5-frozen and `extra` is the sanctioned hatch. **So Phase 4 still has a decision**: whether MLflow run tags are sufficient provenance, or the `CanonicalTrace` needs the model-data version too. They are different audiences and only one of them is the compliance record. |
| Security headers | `server/security_headers.py`, **on by default**, plus `spa_csp()` | Also sets Referrer-Policy; HSTS off by default with the right reason (*"a browser caches it… there is no convenient undo"*). **Open pre-push item:** the default `default-src 'none'` breaks a `static_dir`-served SPA. |
| Console data router | `server/console_api.py:create_console_router()`, opt-in, all GETs on `GovernedRouter` | Missing only release/alias inventory, because Plane B does not exist yet. Auth is `deps`-supplied — the deployment's call, which Plato overrides. |
| Govern `settings_api` `PATCH` | ETag + `If-Match` → 412 + `_audit_write` (key names, never values) | `If-Match` is **honoured, not required** — a deliberate compatibility choice. Plato should require it. |

**What this leaves for Phase 5:** the overlay record exists; its **distribution** does not. `_OVERLAY_LOG` is a module-level list and `register_model_*` still mutate in-process dicts, so an operator updating pricing through an API still updates one replica. That is Phase 5 task 4 and it is now the only substantial item in that phase.

**And note what this says about the plan's own Risk 7.** This is the third time in three days that work this plan listed as to-do had already shipped. Re-verify before estimating, always.

---

## Grounding — verified at `3714a5e`, do not re-derive

**Shipped, and this plan builds on rather than rebuilds:**

- `manifest/store.py` — `AssistantManifestStore` ABC (`put`/`get(version)`/`history`/`rollback`), `ManifestRecord` with content-addressed `_derive_version`, `supersedes`, status. **In-process only.** `rg "AssistantManifestStore"` returns the ABC, the in-process impl, and one docstring mention in `loader.py`. There is no `store_db.py`.
- `agents/interactive/session.py` — `SessionRecord` (`created_at`, `last_active_at`, `SessionStatus`), `SessionStore` Protocol, `InProcessSessionStore` with touch semantics. **In-process only.**
- `audit/` — `ConfigAuditEvent`, `ConfigAuditStore`, `InProcessConfigAuditStore`, `events_db.py`. Wired into the `PUT /agents/{name}` write path.
- `server/concurrency.py` — `check_if_match`, `PreconditionRequired`, `RevisionMismatch`, `strict`. Its docstring already names the alias-promotion endpoint as the expected second caller: **reuse verbatim, do not fork.**
- `agents/definition_store.py` — stored `agent_id` with `_derive_agent_id`, `created_by`, `updated_by`, `revision`, and a shared actor/revision stamp helper.
- `server/app.py` — `ServerSettings.require_identity` (default `False`) installs a middleware that 401s any non-`/health` request without resolvable identity and sets/clears the `InvocationContext`. `static_dir` gates `web.py:mount_spa`. `create_app` takes `extra_routes: list[APIRouter]`. `runtime_mode` is reported in `/health` with `http`/`queue` interface status.
- `launcher.py` — `VALID_MODES = ("queue", "server", "dual", "ui")`; `dual` is HTTP **and** queue in one process.
- `agents/interactive/spec.py:Skill` — already carries `version`, `visibility`, `invokes`, `inputs`, `outputs` (both JSON Schema), plus `reads`, `spec_ref`, `tool_use_behavior`, per-skill `model`/`reasoning_effort`/`max_turns`. **Metadata only — the execution path was deliberately not touched.**
- `observability/trace_routes.py` — read-only `GET /traces/{trace_id}` on `GovernedRouter`, lookup-only on purpose so it does not prejudge the format-of-record question.
- `platform_catalog.py` — `MODES`/`EXPERTS`/`PIPELINES`/`FABRIC_SURFACES`/`CANONICAL_OBJECTS`, derived from the registries.
- `llm/model_data.json` (45 models) + `_model_data.py` + `cost.py` (`MODEL_PRICING`, `PRICING_SOURCES`, `Provenance`, `model_provenance`, `unreviewed_models`, `register_model_pricing`) + `model_cards.py` (`MODEL_CARDS`, `register_model_card`, `is_carded`).

**Absent, verified by grep, not assumed:**

- **No Dockerfile** anywhere in the repo. **No alembic tree.**
- **No `ConfigAsset` / `AgentRelease` / `closure_digest`** — zero hits.
- **No tenant column or scoping** anywhere in the config stores (the addendum ran the greps; re-confirmed).
- **No process-start** — `tools/platform/workflow.py` is read-only; no POST to `runtime/process-instances` anywhere.
- **No model-data version on the canonical trace** — `MODEL_DATA_VERSION` now exists and reaches MLflow run tags; `VersionBundle` still has no model-data field, by design.
- **No durable/multi-replica overlay** — `_OVERLAY_LOG` and the `register_model_*` tables are per-process.

**Five findings that change what to build:**

**F1 — `create_app` already has the mount seam; do not build a second one.** `extra_routes` + `app.state.japes_handler` / `japes_client_layer` is how `trace_router` and `run_router` already mount. Plato's routers mount the same way. A parallel `create_plato_app` that duplicates middleware, CORS, health and identity handling is the wrong shape — Plato composes `create_app`.

**F2 — the three in-process stores share one shape, so build one durable pattern, not three.** `prompt_registry` / `prompt_registry_db` is the house three-file pattern (protocol → in-process → `fabric.db`). §7 Symmetry says do the family: `AssistantManifestStore`, `SessionStore` and `ConfigAuditStore` all need the same treatment, and inventing a different persistence idiom for each is the failure mode.

**F3 — `Skill.inputs`/`outputs` exist but nothing reads them.** So P3 is not "add fields," it is "wire the fields that were added on purpose and left disconnected." Check before starting: `rg -n "\.inputs|\.outputs" --include=*.py jazzx_sdk/agents` — if something now consumes them, this phase shrinks.

**F4 — `queue_processor.py:_processed_message_ids` is in-memory**, so at-least-once means duplicates across restarts. `automation/idempotency.py` already exists. This is a latent correctness bug that only bites once Plato runs multi-replica workers; fix it in P0, not after.

**F5 — `settings_api.py` `PATCH` is an ungoverned config-write path.** Default `EnvFileSettingsStore` writes `.env` and mutates `os.environ`. It bypasses `GovernedRouter`, `check_if_match` and `ConfigAuditEvent`. Fine as a dev convenience; not fine in Plato's deployed posture.

---

## Answering the objections this will draw

**"This is a whole new service to fix a problem nobody has hit."** Someone hit it and shipped 1100 lines around it: `assistant/app/assistant/promotion.py` is a working closure-walking, name-keyed, per-asset-kind-routed release system built because no immutable-release primitive existed. The addendum found it by accident and drew the right conclusion — a proper primitive should *retire* that system, not become a fourth option beside it.

**"Put it in each consuming service's DB, as today."** That is addendum shape 2, and it is the status quo that produced two-plus independent databases with no owner of "what is the current version of this skill." It does not get better with more consumers.

**"Studio should own it."** That is shape 1 and it is a live alternative — this plan does not pretend otherwise. What it does is make shape 3 concrete enough to compare. **D1 is a real decision, not a formality; Phase 2 does not start until someone picks.**

**"Just add HTTP routes to `server/app.py`."** That is Phase 1 and it is genuinely small. The rest of the plan exists because routes over in-process stores lose every manifest, session and audit event on restart, and because a multi-tenant service with no tenant column is a data-isolation incident waiting to happen.

---

## Decisions that gate work

| # | Decision | Gates | Notes |
|---|---|---|---|
| **D1** | Addendum shape 1, 2 or **3**. Plato is shape 3. | Phase 2 | SDK owner + Studio owner. Phases 0–1 unaffected. |
| **D2** | Does Studio write to Plato's API or keep its own store? | Phase 2, Phase 6 | Two writers on day one loses the whole point. |
| **D3** | Who owns process-start? | Phase 3 | UAF item 6, still open. |
| **D4** | Per-skill IO on the execution path (contested item 4). | Phase 3 | The record shipped; nothing generates routes until the execution-path question is settled. |

Already answered in the addendum; **adopt, do not relitigate**: `content_digest()` beside `content_version()`; tenancy is absent everywhere, so under shape 3 it is a launch requirement.

---

## Phase 0 — the package, the boundary, and the deployable (S–M)

**No gate.** Nothing here depends on D1.

**Tasks**

1. **`plato/` as a top-level sibling of `jazzx_sdk/`.** Not `japes_plato/`, not `jazzx_sdk/plato/`. `plato` imports `jazzx_sdk` and `common`; the reverse never happens.
2. **Import-linter contract in CI** enforcing that direction. One config file. **Land this in the same PR as task 1** — a boundary added after the first violation is a refactor, not a rule.
3. **`japes[plato]` extra** for `alembic` and any console-only dependency, matching the existing extras convention (`mcp`, `templating`, `finance`, `gemini`, `mlflow`, `litellm`, `streaming`, `azure`, `pptx`). Note `fastapi`/`sqlalchemy`/`asyncpg` are already core — do not move them, just do not add more.
4. **First Dockerfile**; roles selected by `JAPES_RUN_MODE` (+ Plato's own roles). One image, one digest.
5. **First alembic tree, owned by `plato/`**, targeting Plato's metadata only. Say so in `plato/__init__.py`'s docstring, because the house rule elsewhere is "DDL belongs in the consuming service's alembic" and a reader needs to know this is that service, not an exception to the rule. Migrations run as a job, never at container start.
6. ~~Security-header middleware~~ — **landed in 2.4.7** (`server/security_headers.py`, on by default, wired in `create_app`). One follow-up remains and it is a pre-push question, not a Plato phase: the default CSP is `default-src 'none'`, which is correct for JSON and **breaks any consumer serving a SPA through `static_dir`**. `spa_csp()` exists for that case, but somebody has to check whether `k9`/`k9-ui` or any other consumer is serving one today and set the policy before this pushes.
7. **Force `require_identity` on in a deployed posture.** Plato refuses to boot otherwise. Do not change the SDK default — this is Plato's decision to make for itself.
8. **Keycloak/OIDC verification** on the inbound path, and **Keto wiring** from `common/core/keto/` (wiring, not building).
9. **The `plato` database and five schemas** (`plato_control`, `plato_runtime`, `plato_trace`, `plato_reference`, `plato_projection`), with `tenant_id` in every key from the first migration.
10. **Durable backings for the three shipped ABCs** — `AssistantManifestStore`, `SessionStore`, `ConfigAuditStore` — following the `prompt_registry`/`prompt_registry_db` three-file pattern (F2). One idiom, three stores.
11. **Fix F4** — point `queue_processor.py`'s dedupe at `automation/idempotency.py`.

**Acceptance**

- CI fails a PR in which `jazzx_sdk` imports `plato`.
- `pip install japes` (no extra) pulls no `alembic`.
- Plato refuses to start in a deployed posture with `require_identity` false; the refusal names the setting.
- A manifest `put` survives a process restart with `history()` and `rollback()` intact — asserted against the durable store, and the existing in-process tests still pass unchanged.
- Every one of the five schemas' tables has `tenant_id` in its primary key or a unique constraint including it. A test asserts no table is missing it.
- Two workers restarted mid-queue process a duplicated message exactly once.
- All four security headers present on every response including `/health`.

**Size:** S–M. **Risk:** task 6's CSP default is the only contested bit; get the `k9-ui` answer before picking.

---

## Phase 1 — the assistant-addressed runtime (M) — *the proof*

**No gate.** This is the phase that justifies the project; ship it before arguing about Phase 2.

**Tasks**

1. **Compose `create_app`, don't fork it** (F1). Plato's routers mount through `extra_routes`.
2. **Tenant-scoped `ProfileRegistry`** instances, and an assistant → bound-agent cache keyed on `(tenant_id, assistant_id, release_id)` — include `release_id` from the start even before Phase 2 populates it, or the cache key changes shape later.
3. **Routes:** `POST /v1/assistants/{id}/chat`, `/chat/stream`, session create/get/delete. Resolve the manifest from the durable store, bind with `build_from_manifest`, serve.
4. **Reuse `runs/` verbatim** for durable resumable SSE, cooperative stop and one-active-run-per-conversation. Do not re-implement streaming.
5. **Session TTL sweeper** on the `runs/dispatcher.py:Reaper(ttl_seconds, interval_seconds)` pattern, as a `role=job:*`.
6. Keep `session` and `conversation` distinct — a conversation holds runs; `agent.py` and `runs/` already model it that way.

**Acceptance**

- **Two assistants with different manifests, packs and personas served from one running instance, added by writing configuration — no deploy, no code change.** This is the phase's definition of done; write it first.
- A stream survives a client reconnect and resumes from `from_seq`.
- A session past TTL is reaped; a resume attempt returns a typed refusal, not a 500.
- A request for an assistant in another tenant returns 404, not 403 — do not leak existence.

**Size:** M. **Risk:** scope creep into Phase 2. If a Phase 1 diff touches release or closure concepts, it has escaped.

---

## Phase 2 — versioned config assets, releases, aliases (L)

**Gate: D1 and D2, in writing.** Do not start otherwise. Phases 0–1 give real work while that is pending.

Implements the config-versioning plan's Phases 3–5 with Plato as the durable store. Read that plan's F1–F7 before starting — they still apply and are not repeated here.

**Tasks**

1. ~~`content_digest()` beside `content_version()`~~ — **landed in 2.4.7**, in a better place than this plan proposed: `jazzx_sdk/digest.py`, a dependency-free bottom-layer module, because `llm` sits *below* `evaluation` and could not otherwise reach it. Canonical JSON with sorted keys and fixed separators — which is exactly the property `closure_digest` needs, so build on it rather than re-canonicalising. `content_version()` delegates and returns a byte-identical hash.
2. `ConfigAsset` / `ConfigAssetVersion` / `ConfigDraft`, one shape serving `kind in {skill, profile, manifest}`. Version rows append-only, unique on `(asset_id, version_id)` **at the DB level**.
3. `AgentRelease` + `AgentReleaseDependency` + `closure_digest` over an **explicitly ordered** resolved graph, canonical JSON, one shared serializer. Fix the ordering rule in the docstring before writing code — an unstable digest makes the acceptance test flap and the whole plan pointless.
4. **Resolve, then freeze.** Manifest, profile, every skill, every `spec_ref` child, the pack version, model pins. Reuse `ProfileRegistry.validate()`'s aggregation *logic* (dangling refs, guardrail-phase mismatch, `spec_ref` cycles, one aggregated error) and change only the lookup key from live registry to exact-version set. Do not fork it.
5. `AgentAlias` with promotion and rollback as atomic pointer moves, `If-Match` via **`server/concurrency.py` verbatim**, status transitions on `jazzx_sdk.statemachine` following `GUIDANCE_LIFECYCLE`.
6. Every promote/rollback emits a `ConfigAuditEvent` carrying the approver and before/after release ids.
7. Reuse `manifest/bundle.py:pack_bundle` as the closure carrier; add a **create-or-verify-digest** publisher policy and state in `publish.py` that upsert-by-name is not admissible for a versioned asset. Check `juno`/`jaci` for existing `Publisher` implementations first — this changes a documented contract.
8. Backfill current config as version 1 with `actor_type="migration"`.
9. **Read `assistant/app/assistant/promotion.py` in full before designing the publish path.** Its "route each part of the bundle to whichever service owns that asset kind, create the assistant row last so a partial failure is resumable" is a load-bearing detail proven in production.

**Acceptance**

- **Rollback to a prior release reproduces the same `closure_digest` and the same effective spec, on a graph whose registries have since changed.** Write this test first; it is the definition of done.
- Publishing a new skill version alters no existing release's effective spec or digest.
- Two concurrent draft writes: one 200, one 409.
- A release whose stored digest does not match its recomputed closure fails **at load**, before any turn runs.
- A floating external dependency either blocks a production publish or appears on an approved-exception list.
- Re-publishing an identical release is a no-op; a different payload under an existing `version_id` fails loud.
- No backfilled row carries `actor_type="user"`.
- **The real one:** a written assessment of what `assistant`'s `promotion.py` still does that Plato cannot, with a retirement path or an explicit statement of what stays.

**Size:** L. **Risk:** growing into a registry refactor. `_registry.py` and `agents/interactive/registry.py` stay untouched until Phase 4. A diff there means scope escaped.

---

## Phase 3 — skill IO on the execution path, generated routes, process-start (L)

**Gate: D4 (and D3 for the process-start half).**

**Tasks**

1. **Derive** JSON Schema for `Skill.inputs`/`outputs` from the wrapped agent/tool/process wherever possible — not hand-authored, not templated. The fields already exist (F3); this wires them.
2. Give the def-backed (`as_tool`) and `spec_ref` branches of `_build_parent_tools` **real typed signatures**, generalizing what the bare-name-to-catalog-callable branch already does — it is the one shape that keeps its native signature today.
3. Generate `POST /v1/assistants/{id}/skills/{skill}/invoke` per skill from the **resolved release**, on `GovernedRouter`, validating against the declared input schema. Respect `Skill.visibility`.
4. Async shape: `POST .../actions` → `202` + operation ref; `GET /v1/operations/{id}`.
5. Per-assistant OpenAPI from the repo-wide `describe()` convention.
6. **Process-start client** (D3): the first POST to `runtime/process-instances` in the estate. A credentialed outbound integration, so it belongs in the service, not the library.

**Acceptance**

- **A frontend developer builds a working screen against the generated docs with no core engineering involvement.** The PRD's own test, unmodified.
- A malformed body is rejected by schema before reaching a model.
- Adding a skill to an assistant changes **no code in `plato/`** — if it does, this phase failed.
- An async action returns 202 and its operation reaches a terminal state.
- A BPMN process instance can be started and its completion observed.

**Size:** L. **Risk:** task 2 is *"the deepest change"* — it rewrites the tool-building path every assistant uses. Full suite plus a dependent-pack check before it lands.

---

## Phase 4 — trace of record (M)

**Gate: UAF item 9 decided.** Recommendation in the companion doc: `CanonicalTrace` is the format of record.

**Tasks**

1. Persist `CanonicalTrace` from the conversational path; serve by **extending `observability/trace_routes.py` under `/v1`**, not adding a second lookup.
2. Carry `agent_release_id` and per-dependency version refs. `VersionBundle` lives in the Spec-v1.5-frozen `trace.py`, so use `extra` now; a named field is a governed cross-team change, not a code edit. Same for `TraceStep` — `extra="forbid"`, no `domain_extensions`; the only hatch is `CanonicalTrace.metadata` keyed by `step_id` via `TraceStepContextHelper`.
3. Stamp the resolved **model-data version** (see Phase 5) alongside the model pins.
4. **Dual-read** with a `legacy_unversioned` marker, emitted from day one.

**Acceptance**

- A trace from a released assistant names the exact release and every skill version actually invoked.
- A trace from a legacy definition carries `legacy_unversioned` and no release id.
- The existing interactive suite passes with dual-read on and no releases present.

**Size:** M.

---

## Phase 5 — versioned reference data and the operator console (M)

Independent of Phases 2–4; can run in parallel. **Items 1–3 are small enough to land in 2.4.7 ahead of Plato** — see the sequencing note.

**Tasks**

1. ~~Version `model_data.json`~~ — **landed**: `cost.MODEL_DATA_VERSION = content_digest(MODEL_DATA, length=12)`, derived rather than hand-maintained, so a reformat that changes no value is not a new version.
2. **Record overlay registrations.** `register_model_pricing` / `register_model_card` currently mutate an in-process dict with no record of who registered what against which base. Keep the `overwrite=False` default and its reasoning; add the record.
3. **Stamp the resolved model-data version into the run** (via `VersionBundle.extra`, per Phase 4 task 2) so cost on an old trace is reproducible at the price that was actually in force.
4. **Durable overlay in `plato_reference`**, read by every replica — the in-process `register_*` stays a consumer-side boot-time override. Without this, an operator updating pricing through an API updates one replica.
5. ~~Read-only console data router~~ — **landed**: `server/console_api.py:create_console_router()`, opt-in via `extra_routes`, all GETs on `GovernedRouter`, serving `platform_inventory` / `model_data_inventory` / `registry_inventory`. Release and alias inventory is the only piece missing, and only because Plane B does not exist yet — add it in **Phase 2**, not here. Note auth is `deps`-supplied, i.e. the deployment's call; **Plato requires it** (Phase 0 task 7).
6. ~~Govern or gate `settings_api.py`'s `PATCH`~~ — **landed**, in the "govern it" direction: an ETag over the raw stored values (deliberately not the masked catalogue, since two different secrets both rendered as the mask must not read as the same state), `If-Match` → 412, and `_audit_write` recording actor and **key names only, never values**. One deliberate choice to know about: `If-Match` is *honoured when supplied, not required*, because requiring it would break every existing caller. **Plato's own posture should require it** — that is a Plato decision, not an SDK one.
7. Do **not** mount the SPA by default. `static_dir` gating is already correct; leave it.

**Acceptance**

- Two replicas serve the same overlaid price after one is updated through the API.
- A trace names the model-data version in force; recomputing cost from an old trace uses that version's rates, not today's.
- `GET /v1/console/model-data` returns provenance and the unreviewed list.
- A `PATCH` to settings in a deployed posture either produces an audit event or is refused.
- Installing without the console enabled exposes no console route.

**Size:** M.

---

## Phase 6 — feedback seam, then the strangler (S–M, then ongoing)

**Tasks**

1. `POST /v1/feedback` as a **pass-through** to eval-service — stable `event_id`, propagated identity, no Plato-side storage. Engineering-queue Tier 1.2's sub-tasks are the work.
2. Resolve **queue 0.4** — the `feedback` table-name collision — which Plato's schema prefix makes structural rather than conventional.
3. Kernel-agent → `InteractiveAgentSpec` converter. Report the count of unconverted rows weekly; it is the only honest progress metric.
4. `jazzx-assistant` as a manifest + pack hosted in Plato.
5. Port the Kernel salvage assessment's SERVICE-LAYER items — sandbox client, MCP refresh cadence, Integration Hub / credentialed gateways, async feedback validation — into Plato, not the SDK. Read `plans/design_note_k7_parent_child_artifacts.md` before designing the Notepad/parent-child-artifact gap.

**Acceptance**

- A forced ambiguous retry produces exactly one eval-service row and returns the same `FeedbackAcceptedV1`.
- `plato` contains no feedback table.
- The unconverted kernel-agent count is reported and trending down.

**Size:** S–M for 1–2; no estimate for 3–5 until the caller audit is done.

---

## Deliberately not in this plan

- **Absorbing eval-service's durable state.** Stage 3 in the companion doc; no date, gated on Stage 1 proving the contracts. Plato stores no feedback, attribution or learning-candidate state.
- **Multi-session and user-level memory.** Correctly deferred by the PRD and by this tree; `spec.py` reserves `memory: MemoryBinding` for the Memory Fabric.
- **BYO-framework adapters.** No LangChain / Semantic Kernel / Claude-SDK adapter, correctly deferred.
- **Merging `AssistantManifest` and `InteractiveAgentSpec`.** Contested item 3, open since 2026-08-03. Plato's record shape holds either way — same neutrality `manifest/store.py` already adopted.
- **`GuardrailRegistry` / `TemplateRegistry` versioning.** Same overwrite-by-name shape, no product requirement pinning a version. Documented as out, not overlooked.

---

## Sequencing

```
Phase 0  (package, boundary, deployable, durable stores)  ──► no gate, start now
Phase 1  (assistant-addressed runtime)                    ──► after 0. THE PROOF.
Phase 5  (reference data + console; items 1-3 in 2.4.7)   ──► parallel, no gate
Phase 2  (versioned assets, releases, aliases)            ──► gate: D1 + D2 in writing
Phase 3  (skill IO, generated routes, process-start)      ──► gate: D4 (+ D3)
Phase 4  (trace of record)                                ──► gate: UAF item 9
Phase 6  (feedback seam, then strangler)                  ──► 1-2 anytime; 3-5 after Phase 1
```

**Land Phase 1 before arguing about Phase 2.** It is the smallest thing that makes the case, and if it does not convince anyone, nothing later will.

**Already in 2.4.7** — Phase 5 items 1–3 and 6, Phase 2 task 1, and Phase 0 task 6. See *Already landed in 2.4.7*.

**Still available for 2.4.7 before it pushes, no gate:** queue **0.4** (the `feedback` table name — the one Tier 0 item that is cleanly takeable); and the security-headers CSP question for any `static_dir` consumer. Per `engineering_queue.md`: 0.2 shipped in v2.4.0, **0.1 is disputed and needs a decision rather than the queue's literal ask**, 0.3 could not be located and may be eval-service-side.

---

## Risks

1. **Second source of truth.** `plato_projection` is read-only by schema and by review rule. No writable copy of another system's fact at any stage. Most likely failure, and it looks like progress while it happens.
2. **Product semantics leak into `plato/`.** Review question on every PR: *what manifest, pack or release row does this value come from?*
3. **The `jazzx_sdk` → `plato` import boundary erodes.** Only guardrails Phase 0 tasks 1–2 prevent it, and only if they land together.
4. **Phase 2 becomes a registry refactor.** Its own top risk, inherited. `_registry.py` untouched until Phase 4.
5. **`closure_digest` is unstable across runs.** Canonical JSON, sorted keys, one serializer, and a test that computes the digest twice from independently constructed objects.
6. **Phase 3 task 2 breaks every assistant.** It rewrites `_build_parent_tools`. Full suite plus dependent-pack checks; do not land it in the same PR as anything else.
7. **The tree moves faster than the plan.** Thirteen UAF phases and two config-versioning phases landed between the source documents and this read, several of which earlier drafts listed as work to do. Re-verify before estimating.

---

## Running this with Claude Code

**One phase per session.** Open every phase by re-verifying its anchors at current HEAD — line numbers and file paths here are from `3714a5e` and will drift:

```
git -C /Users/sangit/src/japes log --oneline -1
rg -n "<the symbol named in the task>" --include=*.py jazzx_sdk
```

If an anchor has moved, fix the anchor and continue. **If an anchor is gone, stop and report** — something landed this plan did not account for. This has already happened three times in three days — twice to this plan's predecessors and once to this plan itself (see *Already landed in 2.4.7*).

Then, per CLAUDE.md §4: restate the phase's acceptance criteria as the success condition, write the failing test first where the criterion is a behavior, and loop until it passes. For Phase 1 that is the two-assistants-one-instance test; for Phase 2 it is the rollback-reproduces-the-closure test. Both get written before any implementation.

**Guardrails**

- **Do not put Plato inside `jazzx_sdk/`.** Sibling package, always. A diff that adds `jazzx_sdk/plato/` is wrong even if it works.
- **Do not let `jazzx_sdk` import `plato`.** If the import-linter contract is not in place yet, that is Phase 0 task 2 and it comes first.
- **Do not fork `server/concurrency.py`, `ProfileRegistry.validate()`, `manifest/bundle.py:pack_bundle`, or `runs/`.** Each is named in a task as reuse; forking any of them is the failure this plan is trying to avoid.
- **Do not widen `content_version()`.** Add beside.
- **Do not touch `_registry.py` or `agents/interactive/registry.py`** before Phase 4.
- **Do not add a named field to `VersionBundle` or `TraceStep`.** Spec v1.5 is frozen; use `extra` / `CanonicalTrace.metadata` and raise the schema change separately.
- **Do not edit `common/`** without flagging it as a cross-repo change with its own review.
- **Do not `git push`** (CLAUDE.md). Commits are fine. **No AI-attribution trailer** — commits read as the user's.
- **Use `>=` floors**, never `^` or upper caps.
- **Bump `_version.py` and `pyproject.toml` together** (`tests/test_version_sync.py` asserts equality). Ask before any major bump.
- **Full suite green after every phase**; diff `-X importtime` against `docs/_importtime_baseline.txt` for any phase touching import structure (0, 3, 5). **CHANGELOG updated per phase.**
- Per CLAUDE.md §1: if a task here is ambiguous or a simpler shape exists, **say so before implementing**. Several tasks state a recommendation and name the decision as open — those are invitations to push back, not settled instructions.
- Before recommending a push, check open Dependabot alerts on `main`.
