# Plato — Platform Two

**`japes-plato`: hosting the JAPES SDK as a service — charter, architecture, and build plan**

> "…to divide things again by classes, where the natural joints are, and not to try to break any part, after the manner of a bad carver."
> — Plato, *Phaedrus* 265e

Author: Virendra Mehta · 2026-08-24, status updated 2026-08-27 · **`plato` `0.1.1`**
Status: **being built.** Phases 0 and 1 have shipped on the `plato` branch; the argument below stands as written and the decisions in §10 are still open. D1 and D2 are with the Studio owner as `note_D1_D2_DECISION_MEMO.md`.

**Written against** `japes` **HEAD `83fe10a`** on the **`plato` branch**, read 2026-08-27, plus the `ape/` plan and status tree. Companion build plan for Claude Code, with per-phase state: `plan_JAPES_PLATO_SERVICE.md`.

**Not read:** the `eval-service` repo (last known `edd3cfb`, 2026-07-30 — now four weeks stale), and the sibling consumer repos `jaci`, `jazzx-assistant`, `kernel`, `assistant`, `macer`, on which several caller audits below depend.

---

## 0. TLDR

**The UAF plan shipped 13 of 13 phases into 2.4.x.** Manifest versioning and rollback, session lifecycle, the always-on guardrail floor, the LLM Gateway on the agentic path, traced router and guardrail decisions, the invocation-context middleware, the skill record with `version`/`visibility`/`invokes`/`inputs`/`outputs`, the A/B harness on manifests. The config-versioning plan then shipped its Phases 1 and 2: actor attribution, optimistic concurrency, stable `agent_id`, and an append-only `ConfigAuditEvent`.

**What that plan could not ship is the list this document is about.** Its own "blocked on someone else" section names five things, and four of them are one thing wearing four hats: *there is no deployable*. Every primitive it built is an in-process ABC with no durable backing and no HTTP surface in front of it.

**Plato is that deployable, and it now exists.** `japes-plato` hosts the SDK behind an assistant-id-addressed, multi-tenant HTTP surface, with its own Postgres database as the durable control plane for assistant configuration. It is deliberately the answer to the config-versioning addendum's **D1 shape 3**, which that document records as *"under active consideration."* As of `83fe10a` it is **3,020 lines across 25 modules on the `plato` branch**, versioned independently at `0.1.1`, with its own alembic chain and six tables: chat, streaming, session and feedback surfaces serve; the release and promotion half waits on D1.

Five planes: **(A)** assistant-addressed runtime, **(B)** config control plane and database, **(C)** generated per-skill action APIs, **(D)** trace, session and feedback, **(E)** operator console and versioned reference data. It ships as one image in the roles japes already supports — `JAPES_RUN_MODE=queue|server|dual|ui` — against a database on the existing Postgres server.

The stated long-run intent is that Plato **replaces Kernel and `jazzx-assistant`, and absorbs eval-service's durable control plane behind Plato-owned contracts** (§5, staged and explicit about which parts are political rather than technical).

Two things will kill this: Plato becoming a **second source of truth** while eval-service and Studio are still live (§5.4), and Plato accreting **product semantics** the way jstack did (§3.3).

---

## 1. Why Plato — the argument the tree already makes

### 1.1 The UAF plan's own blocked list

From `status/done_JAPES_2_4_0_UAF_PHASE1_ADDITIVE.md`, "Blocked on someone else, not on us," verbatim in substance:

| # | Item | Status |
|---|---|---|
| 5 | **Per-skill action APIs and the multi-tenant assistant-id-addressed service** — *"the PRD's actual Phase-1 product outcome."* `ProfileRegistry` already hosts many agents on one `SkillRegistry`; `build_from_manifest` produces a live agent with no handler code; `GovernedRouter` supplies the governed route primitive. But *"`server/app.py` is one handler per process with no assistant lookup, `add_api_route` appears exactly once in the tree."* | **Plato, Planes A + C** |
| 6 | **Starting a BPMN process** — *"Name an owner before Phase 1 is committed to, or two of the PRD's acceptance criteria have no backend."* | **Plato, Plane C** (proposed) |
| 7 | **Keycloak / OIDC** — *"Who verifies the token is a service-boundary decision, not a japes delta."* | **Plato, P0** |
| 9 | **The trace format of record** — *"Cheap to decide now, expensive later."* | **Plato, Plane D** |

Item 8 (multi-session and user-level memory) is correctly deferred and stays deferred. Contested item **4** — per-skill IO contracts driving generated tool signatures — gates item 5 and is the one genuine design argument left; §4 Plane C takes a position.

**Three of those four are literally "a service boundary decision."** They have no owner because there is no service.

### 1.2 The same conclusion, reached independently, from the config side

`plans/plan_JAPES_2_6_0_CONFIG_VERSIONING_D1_D2_D3_ADDENDUM.md` puts three shapes on the table for who owns configuration, and states shape 3 as:

> **A dedicated JAPES SDK service — its own deployable container, with its own DB — becomes the shared control plane.** Under active consideration. Builder Studio (and any other authoring surface) publishes *into* it; every consuming service (jaci, jazzx-assistant, …) resolves versioned skills/profiles/releases *from* it… This is a new deployment mode, not a bigger library.

**Plato is shape 3, named.** The addendum also supplies the strongest evidence for it, found by accident:

> The separate "Assistant Repo" (`app/assistant/promotion.py`, ~1100 lines, a real shipped PR) is a working cross-instance "release" system for exactly this class of asset… a team hit the exact gap this plan exists to close and built a **1100-line, name-keyed, per-asset-kind-routed workaround** because no proper immutable-release primitive existed to reach for.

And its warning about what a proper primitive must achieve: *"A proper japes release primitive should aim to let `assistant` retire this hand-rolled system, not add a fourth option beside Studio's own DB, each service's own DB, and this one."* **That is Plato's acceptance test for Plane B**, and it is a better one than anything I would have invented.

### 1.3 Everything else deferred to "the service layer"

Still unowned, still service-shaped, from the Kernel salvage assessment: the **Python sandbox client** (*"a library must not host quota sandboxing… name the owner"*), **MCP refresh cadence**, **Integration Hub / Perplexity credentialed gateways** (referenced in a docstring at `tools/base_registry.py:52`, never implemented), and the **async feedback validation stage**. *(Gateway security headers were on this list until `3714a5e` — `server/security_headers.py` now ships them on by default, with `spa_csp()` for the `static_dir` case.)*

### 1.4 The structural point

The architect assessment records japes describing itself two ways — README's *"increasingly standing-in for the kernel"* against `docs/ARCHITECTURE.md`'s *"a standardized way to run custom code… without modifying the core platform."* That is what happens when something is asked to be the core while shipping as a wheel. Plato gives the first description a deployable to be true in, and lets `jazzx_sdk` stay honestly a library.

And the bill compounds: *"Every mortgage capability landed through Juno produces a kernel-agent artifact… with no v2 representation… the single most time-sensitive item in this document, because it is the only one that gets strictly worse with every successful sprint."* A kernel-agent row can only be *converted* if there is a v2 runtime to convert it into.

---

## 2. Name, versioning, and conventions

- **Project name: Plato — Platform Two.** The pun is the point and survives being noticed; the Academy reading comes free.
- **Service name: `japes-plato`.**
- **Repo: `japes`** — not a separate repository. Rationale and four guardrails in §3.4.
- **Python package: `plato/`,** a top-level sibling of `jazzx_sdk/` — not `japes_plato/`, not `jazzx_sdk/plato/`. The sibling placement is load-bearing (§3.4 guardrail 1). `plato` imports `jazzx_sdk` and `common`; `jazzx_sdk` never imports `plato`, enforced in CI.
- **Database: `plato`** on the existing Postgres server, schemas per §7.
- **Plato versions independently** — `plato/_version.py` (`0.1.1`), separate from `jazzx_sdk`'s. Decided during Phase 0 and not anticipated here: it removes the version-churn cost §3.4 told the reader to accept, rather than living with it. The SDK-side deltas Plato depends on still ride the SDK's version.

**Version numbering.** 2.5.0 is Plato's. Two `ape/plans/` filenames still carry that number — `plan_JAPES_2_5_0_INVOCATION_AUTHORIZATION` (shipped at `f50a498` with no bump) and `plan_JAPES_2_5_0_LOCATOR_AND_INVENTORY_DISCIPLINE` (its Revision 2 body targets 2.4.2) — but **both were retargeted to earlier 2.4.x releases**, so the filenames are legacy labels, not claims. Plato is the first thing to actually take 2.5.0, which is the right weight for it: a new deployable is a minor bump at least.

**Vocabulary rule**, inherited: the Canonical Object Schema Specification's vocabulary wins; anything else is a local implementation name that must not appear in a manifest or on a wire contract. Plato is the first system with a public API, so it is the first place a bad name becomes a data migration.

**Two naming challenges, deliberately deferred.** *"It should start with `ja-`"* — the service name already carries the prefix, the package need not carry it twice. *"If it replaces Kernel, call it Kernel"* — no: Plato must **co-exist** with Kernel for the whole strangler, and naming the replacement after the thing it replaces destroys the only vocabulary that makes progress legible (*"is this on Kernel or Plato yet?"*). Revisit when §9 P6's inventory reaches zero.

---

## 3. What Plato is, and what it must not become

### 3.1 Boundary

| System | Role after Plato | Plato's relationship |
|---|---|---|
| `jazzx_sdk` (JAPES) | Unchanged: contracts, runtime, modes, fabric, evaluation toolkit | Plato's only substantive dependency; Plato adds no agent semantics |
| **`japes-plato`** | **The deployable: hosting, tenancy, config system-of-record, HTTP surface** | — |
| Kernel | Strangled (§5.1) | Replacement target; holds a Kernel client during transition |
| `jazzx-assistant` | Strangled — becomes a manifest + pack in Plato | Plato hosts what it used to be a process for |
| `assistant` | `promotion.py` retired in favour of Plato releases | The §1.2 acceptance test |
| eval-service | Absorbed over time (§5.2) | Client first, host later — never both at once |
| Juno / Builder Studio | Authoring UI over Plato's control-plane API | Plato serves; Juno writes; Studio stops writing kernel rows |
| jstack | Unchanged, plus one Plato service definition | A service jstack can bring up |

### 3.2 Non-goals for v1

No new agent framework — if it can live in `jazzx_sdk`, it does. No domain knowledge: the moment `plato/` contains "mortgage" or "SAR," something has gone wrong. Not a second source of truth (§5.4). Not a UI — Studio and JACI are the surfaces; Plane E is an operator console, which is a different thing.

### 3.3 The jstack constraint

The architect assessment on jstack: *"jstack is enabling infrastructure and must not own product semantics. Every liability above is an instance of it doing so."* Its concrete failures were a Go constant listing assistant grants, reaching into other services' databases, and a hard-coded surface *"that must later be re-derived rather than migrated."*

**Constraint: every product-semantic value Plato serves derives from a manifest, a pack, or a release row in Plato's own database. Nothing product-shaped is a constant in `plato/`.** The review question is *what row does this value come from?*

### 3.4 Why Plato lives in the `japes` repo

The reason a Dockerfile in `japes` felt wrong when macer started was the library owning the deployment of a **consumer** — which inverts the dependency. Plato is not a consumer; **Plato is japes deployed as itself.** Macer, k9 and juno keep importing the library and ignore the service. Nothing inverts.

Colocation also earns something while Plato is young: the SDK-side changes Plato depends on — wiring `Skill.inputs`/`outputs` into execution, `VersionBundle` extensions, the config-asset protocols — land in the same PR as the service code that consumes them, instead of across a version bump and a pin.

**Four guardrails, all P0:**

1. **Sibling top-level package.** `plato/` next to `jazzx_sdk/`, never nested inside it. Keeps a later split to a mechanical `git filter-repo` and makes import direction visible in a diff.
2. **A CI-enforced import contract.** One import-linter config. Without it the first "just reach into the store from the SDK" PR ends the experiment quietly. **This is the guardrail that decides whether colocation works.**
3. **A `plato` extra — don't make the dependency surface worse.** Stated honestly: `fastapi`, `sqlalchemy[asyncio]` and `asyncpg` are **already core dependencies** of japes, so every consumer pulls them today. What Plato adds — `alembic`, console deps — goes behind `japes[plato]`, matching the established convention (`mcp`, `templating`, `finance`, `gemini`, `mlflow`, `litellm`, `streaming`, `azure`, `pptx`).
4. **Write down the alembic exception.** Both DB stores carry the note that *"table DDL belongs in the consuming service's alembic."* Plato in-repo means the repo gains an alembic tree — it is Plato's, targeting Plato's metadata only, and `jazzx_sdk` still ships none. Say so in `plato/`'s module docstring or someone follows the wrong precedent.

**Costs to accept:** japes PRs wait on a service suite wanting Postgres; and `tests/test_version_sync.py` ties one version to the repo, so Plato deploys bump the version consumers pin — noise, not breakage.

**One thing colocation sharpens rather than solves:** it makes README's "standing in for the kernel" physically true. That is an argument for finally picking one in `docs/ARCHITECTURE.md` as a deliberate P0 edit, not something a reader infers from a directory listing.

**Split when:** Plato gets its own on-call; a consumer is blocked on a floor Plato caused; deploy cadence forces more than ~one SDK version bump a week; or SDK CI time becomes the complaint. Guardrail 1 keeps that day cheap.

---

## 4. The five planes

```
                          ┌─────────────────────────────────────────┐
   JACI · Studio · apps ──▶│  Plane A   assistant-addressed runtime  │
                          │  /v1/assistants/{id}/chat|stream|sessions│
                          ├─────────────────────────────────────────┤
   Studio · CI · assistant▶│  Plane B   config control plane          │
                          │  manifests · profiles · skills · releases│
                          │  aliases · audit   ── system of record   │
                          ├─────────────────────────────────────────┤
   frontend devs      ───▶│  Plane C   generated skill action APIs   │
                          │  /skills/{skill}/invoke  + OpenAPI       │
                          ├─────────────────────────────────────────┤
   ops · eval · SMEs  ───▶│  Plane D   trace · session · feedback    │
                          ├─────────────────────────────────────────┤
   operators · Studio ───▶│  Plane E   console · reference data      │
                          └──────────────┬──────────────────────────┘
                                         │  imports
                                  ┌──────▼───────┐
                                  │  jazzx_sdk   │  ← unchanged library
                                  └──────┬───────┘
                    ┌────────────────────┼───────────────────┐
              Knowledge Hub          Kernel (strangling)   eval-service
                                                          (client → host)
```

**The recurring shape across all five planes: the primitive shipped, the durable backing and the surface did not.** `AssistantManifestStore`, `SessionStore`, `ConfigAuditStore` are ABCs with in-process implementations. That is not a criticism of the SDK — it is exactly right for a library. It is also exactly the half a service supplies.

### Plane A — the assistant-addressed runtime

**Shipped:** `AssistantManifestStore` with `put`/`get(version)`/`history`/`rollback` and content-addressed `ManifestRecord` (UAF Phase 12) — *in-process only*, confirmed no DB implementation. `SessionStore` + `SessionRecord` with `created_at`/`last_active_at`/`SessionStatus`/TTL and touch semantics (Phase 8) — in-process only. `ProfileRegistry` hosting many agents on one `SkillRegistry`. `build_from_manifest` producing a live agent with no handler code. `runs/` for durable resumable SSE with cooperative stop and one-active-run-per-conversation, plus `Reaper(ttl_seconds, interval_seconds)`. `GovernedRouter` for X-Trace-Id and Idempotency-Key discipline.

**Plato adds:** durable implementations of both stores; tenant-scoped `ProfileRegistry` instances; an assistant-id → bound-agent cache keyed on `(tenant, assistant_id, release_id)`; and the routes. `server/app.py` remains *"one handler per process with no assistant lookup"* — that gap is the whole of Plane A.

**Identity.** `ServerSettings.require_identity` shipped (UAF Phase 11): non-`/health` requests without resolvable identity get 401, and the middleware establishes the `InvocationContext` so `admit_hop` can no longer be reached with none ambient. It defaults **off** because flipping it on is a per-deployment call. **For Plato it is not a choice: P0 acceptance is that Plato refuses to boot in a deployed posture with it off.** That is a stronger statement than the SDK can make for its consumers, and it is the kind of thing a deployable gets to decide.

**Still absent:** Keycloak/OIDC verification. Identity is header-borne. UAF item 7 assigns this to the service boundary; Plato is the service boundary.

### Plane B — the config control plane and database

**Shipped (config-versioning Phases 1–2):** actor attribution (`created_by`/`updated_by` resolved from the authenticated caller, never request JSON), `revision` + `If-Match` optimistic concurrency behind a `strict_concurrency` flag, the shared `server/concurrency.py` helper written explicitly so *"a later alias-promotion/rollback endpoint is expected to reuse it verbatim rather than fork it"*, stored `agent_id` closing the silent-identity-change defect, and the append-only `ConfigAuditEvent` store with before/after digests and trace correlation.

**Plato is D1 shape 3.** The protocol stays in `jazzx_sdk`; the durable implementation lives in Plato; Studio becomes a client of Plato's API rather than a second writer. This also resolves that plan's Risk 4 — *"the plan ships stores with no caller"* — by giving Phase 2's audit store and Phase 3's versioned stores a real adopter.

**The invariant worth restating**, because it is the whole point: *"Rolling back to `M1` restores old manifest bytes and then binds them to today's profile and today's skills… revalidation against today's graph, not reproduction of yesterday's graph."* Plato pins the closure. A release is an immutable snapshot with a `closure_digest`; promotion and rollback are alias moves; the runtime verifies the digest at load and refuses to run a release whose closure does not reproduce.

**Two decisions the addendum already answered**, and Plato should adopt rather than relitigate:
- **D2 — settled and shipped.** `jazzx_sdk/digest.py` in 2.4.7: `content_digest()` as a new dependency-free primitive, `content_version()` delegating to it and returning a byte-identical hash. Add-beside, never widen — the 12-hex prefix is shared unmodified by `PromptVersion`, `GuidanceAsset` and `ManifestRecord`, so widening would have been a silent three-subsystem migration.
- **D3 — answered: no tenant column or scoping mechanism exists anywhere in japes' config stores.** The only `common/core` hit is a telemetry attribute. The addendum's conclusion applies directly: *"if D1 lands on shape 3… this stops being a 'nice to have later' and becomes a launch requirement for that service."*

**The acceptance test comes from `assistant`.** Plane B is done when `app/assistant/promotion.py` — 1100 lines of hand-rolled, name-keyed, per-asset-kind-routed release machinery — can be retired against Plato rather than coexisting with it. Its design detail is worth carrying forward, not discarding: **publish routes each part of a bundle to whichever service owns that asset kind** (kernel for agents/tools/LLMs, Flowable for BPMN/DMN, KH for collections), with the assistant row created last so a partial failure is resumable. Not every asset in a release belongs in the same store.

### Plane C — generated per-skill action APIs

**Shipped (UAF Phase 3, "metadata only, execution path untouched"):** `Skill` already carries `version`, `visibility`, `invokes`, `inputs` and `outputs` — the last two as JSON Schema. The record exists. **The execution path was deliberately left alone**, which was the right call: it kept the contested design question open rather than answering it by accident.

**So Plane C is no longer "add fields."** It is (a) settle contested item 4, (b) wire the schemas into `_build_parent_tools`, (c) generate routes and OpenAPI from the resolved release.

**Position on (a)**, unchanged from the gap analysis and the UAF plan's own out-of-scope note: the schemas are **auto-derived from the wrapped agent/tool/process wherever possible, not hand-authored**. Today def-backed (`as_tool`) and `spec_ref` skills are both exposed as `(query: str) -> str` — a forced string port with no declared IO — while a bare name resolving to a catalog callable keeps its native signature. That last branch is the one to generalize.

**Plato's part** is route generation off the resolved release: for each skill with `visibility` admitting the caller, mint `POST /v1/assistants/{id}/skills/{skill}/invoke` on `GovernedRouter`, validate against the declared input schema, and emit an OpenAPI document per assistant from the repo-wide `describe()` convention. `add_api_route` appears exactly once in the tree today, so this is new code over an existing governed primitive.

**Acceptance is the PRD's, unmodified** — *"a frontend developer builds a working screen with no core engineering involvement"* — which the gap analysis rightly calls *"an unfakeable acceptance test. Keep it exactly as written."*

**Process-start.** Nothing in the SDK starts a BPMN process instance; `tools/platform/workflow.py` is read-only and there is no POST to `runtime/process-instances` anywhere, including `common/` and `tests/`. It is a credentialed outbound integration, which is service-layer by the Kernel salvage assessment's own verdict column. **Proposal: Plato owns it.** That closes UAF item 6 and unblocks two acceptance criteria that currently have no backend.

### Plane D — trace, session and feedback

**Shipped:** UAF Phase 10 traced the two previously invisible decisions (router selection, guardrail verdict). `observability/trace_routes.py:trace_router()` serves a read-only `GET /traces/{trace_id}` on `GovernedRouter` — lookup-only *"deliberately… a write path here would prejudge the trace format-of-record question left open elsewhere."* `mlflow_bridge.span_to_trace_step` / `spans_to_canonical_trace` do the mechanical conversion, with a working precedent in `agents/adjudication/tracing.py`.

**So the plumbing is done and UAF item 9 — the format-of-record decision — is still open.** Plato is where it gets made, because Plato is the thing that has to answer *what ran*.

**Position: `CanonicalTrace` is the format of record.** Operational spans stay operational; the bridge produces the canonical trace; Plato persists it and serves the existing route under `/v1`. Two inherited constraints, not locally negotiable: `TraceStep` is `extra="forbid"` with no `domain_extensions` — *"the most common v1.5 failure mode"* — so the only sanctioned hatch is `CanonicalTrace.metadata` keyed by `step_id` via `TraceStepContextHelper`; and Spec v1.5 declared the schema frozen, so anything beyond that hatch is a governed cross-team change.

`VersionBundle.skills_version` is a single `str | None` for an arbitrary number of independently versioned skills. A Plato-served trace should name the exact `agent_release_id` and every skill version actually invoked.

**Feedback — v1 is pass-through, not storage.** `POST /v1/feedback` forwards through the `EvalServiceFeedbackSink` path with a stable `event_id`, propagated identity, and the convergence proposal's own first proof: *"a forced ambiguous retry produces exactly one eval-service feedback row and returns the same `FeedbackAcceptedV1`."* Absorption is later and on purpose (§5.2).

Engineering-queue **0.4** — `DbFeedbackStore` and eval-service *"both currently claim a table named `feedback`"* — is confirmed still open. Plato's schema discipline (§7) makes the collision structurally impossible rather than conventionally avoided.

### Plane E — the operator console and versioned reference data

**More of this exists than the planning documents suggest, and in the right shape:** `server/web.py:mount_spa` serves a built SPA same-origin with deep-link fallback, called only when `ServerSettings.static_dir` is set (*"the k9 / k9-ui pattern"*). `ui/` is a React 18 + MUI + Redux + Vite app already covering extension registry, queue monitoring, message inspection, health and testing, with `ExtensionPicker.tsx` exported to builder-studio over Module Federation. `platform_catalog.py` exists to feed exactly this — `MODES`, `EXPERTS`, `PIPELINES`, `FABRIC_SURFACES`, `CANONICAL_OBJECTS`, derived from the registries so they cannot drift, stated as *"UIs render from here instead of hand-maintaining (and drifting) their own lists."* `settings_api.py` serves the settings catalog with secrets masked over a pluggable store — and since `3714a5e` its `PATCH` carries an ETag, honours `If-Match` with a 412, and writes an audit record of the actor and the key names (never the values). `server/console_api.py` serves the read-only inventory. `server/security_headers.py` sets CSP, X-Frame-Options, X-Content-Type-Options and Referrer-Policy on by default, with HSTS off until a deployment opts in.

**Should the console mount by default? No — and it already doesn't.** `static_dir` unset means no SPA. Keep that: a console surfacing configs, traces, pricing and registry contents is an information-disclosure surface, and turning it on for every `create_app` consumer is a per-deployment decision, not something inherited from a patch.

**The console data API landed in `3714a5e`** — `create_console_router()`, opt-in through `extra_routes`, every route a GET on `GovernedRouter`, serving `platform_inventory` / `model_data_inventory` / `registry_inventory`. Its own docstring makes the point this section was going to: *"the facts a console or an operator needs… are all already computed in-process. They just have no way out."*

**Two things Plato still owns.** Release and alias inventory is absent from the console only because Plane B does not exist yet — it belongs there when it does. And the console's auth is `deps`-supplied, i.e. whatever the deployment requires: correct for a library, insufficient for Plato, which forces identity (§4 Plane A). Same shape for `settings_api`'s `If-Match`, which is honoured-when-supplied rather than required because requiring it would break existing callers — **Plato's posture should require it, and that is Plato's call to make, not the SDK's.**

#### Reference data: code-derived vs versioned

**Code-derived** — mode registry, expert registry, pipeline catalog, tool signatures. Facts about the running build. `platform_catalog.py` reflects these correctly; don't store them.

**Operationally-mutable reference data** — **model data is the type specimen**, and v2.4.7 already did most of the work. `llm/model_data.json` holds pricing and cards for 45 models, loaded once by `_model_data.py`; `cost.py` builds `MODEL_PRICING` + `PRICING_SOURCES`; `model_cards.py` builds `MODEL_CARDS`. Provenance is per-row — `Provenance(source, retrieved, reviewed_by, reviewed_on, note)` with a `reviewed` property and `unreviewed_models()` as a work list — on the stated principle that *"a machine-read rate stays unreviewed until a person says otherwise."* A weekly Action fails on staleness. The overlay is `register_model_pricing()` / `register_model_card()`, `overwrite=False` by default so a consumer's stand-in cannot outrank the SDK's real card once it ships.

**`3714a5e` closed most of the gap this section originally named.** `cost.MODEL_DATA_VERSION` is now a content digest of the loaded blob — derived, so a reformat that changes no value is not a new version. `OverlayRegistration(model, kind, source, overwrote)` records every runtime registration with the registering module inferred from the caller's frame, on the reasoning that *"two processes on the same `MODEL_DATA_VERSION` can answer differently and nothing records why."* `model_data_version_tags()` stamps version and overlay count onto a run.

**Two things remain, and they are the Plato-shaped halves:**

1. **The stamp reaches MLflow run tags, not the canonical trace.** That was a deliberate choice with the right reason — `VersionBundle` is Spec-v1.5-frozen and `extra` is the sanctioned hatch. But run tags and the canonical trace are different audiences, and only one of them is the compliance record. **Plane D has to decide** whether operational tagging is sufficient provenance for cost, or whether a governed run must carry it.
2. **The overlay is recorded but not distributed.** `_OVERLAY_LOG` is a module-level list; `_model_data.py` reads the JSON at import; `register_model_*` mutate in-process dicts. Fine in one process. The moment `role=api` scales past one replica, an operator updating pricing through an API updates one replica and the others answer differently — with, now, a record of why, which is an improvement but not a fix.

**Position:** the durable overlay is versioned reference data in `plato_reference`, replicas read it, and the in-process `register_*` stays a consumer-side boot-time override. The console already renders the rest — `console_api.model_data_inventory` serves rates, limits, `model_provenance`, `unreviewed_models()`, the data version and the overlay log in one payload.

---

## 5. The absorption path

Stated openly: **Plato is intended to become the v2 control plane, and Kernel, `jazzx-assistant` and eval-service's durable state are intended to end up behind Plato-owned contracts.** Intent is not sequencing, and the sequencing determines whether this works.

### 5.1 Kernel and `jazzx-assistant` — the easy half

Uncontested in direction; do it first.

1. **Plato holds a Kernel client** and proxies what it does not yet own. No behavior change.
2. **Write the kernel-agent → `InteractiveAgentSpec` mapping** — the architect assessment's most time-sensitive item — and run it as a converter. Measure the remaining inventory weekly; it is the only honest progress metric.
3. **Port the Kernel capabilities marked KEEP or SERVICE-LAYER** into Plato where the verdict says service-layer. Two are architectural holes rather than features and both are Plato-shaped: *"no state channel from a parent agent to a sub-agent (only an LLM-authored string)"* — the Notepad/Artifact gap, where `models.py:58 notepad_pointer_id` exists and **nothing in the SDK reads it**; and *"no record of who approved a suspended step."* Note `ape/plans/design_note_k7_parent_child_artifacts.md` exists and should be read before designing the first.
4. **`jazzx-assistant` becomes a manifest and a pack.** When its process is deleted, that half is done.

### 5.2 eval-service — the hard half, and why it goes second

Eval-service is **v2, not legacy**. The convergence proposal named it the control plane, we accepted that in writing, and we wrote *"we had omitted eval-service from our systems map entirely; that was our error and it is corrected."* Reopening it six weeks later has to be done carefully or it reads as bad faith.

**The version that holds up: the split we accepted was control-plane-vs-toolkit, and it did not say which control plane.** The proposal's own pattern — *"the richest implementation becomes the first adapter behind a contract owned by the control plane"* — is precisely how eval-service's stores become adapters behind Plato contracts, if Plato is the control plane for assistant configuration and execution. None of the ten invariants is violated by moving where tables live; invariant 9 in particular is a property of the workflow, not the host.

- **Stage 1 — client (v1, now).** Plato consumes `jazzx-eval-contracts`, stores no feedback, attribution or learning candidates. Eval-service unaffected. Also the fastest way to prove the contracts, which the proposal wanted narrow anyway.
- **Stage 2 — co-locate what is already configuration (v2).** **Scorer thresholds as `policy_ref` + `policy_version` resolved from the pack's canonical `Policy` objects.** This was already our position — response §1 argued thresholds are domain policy *"being placed outside the policy system."* Stage 2 is that objection carried to its conclusion, not a new claim.
- **Stage 3 — absorption (later, decide separately).** Feedback, attribution and learning-candidate state behind Plato contracts, eval-service's implementations as first adapters. **No date, and not in a roadmap deck yet.** Gate it on Stage 1 proving the contracts and Stage 2 landing without a fight.

### 5.3 What we owe eval-service's authors

Their §5 objection was ours: *"an ownership table is only binding if someone owns the table."* We asked them for authorship, status, a supersedes line, and a named accepter per row. §10 is written to that bar.

### 5.4 The failure mode this section exists to prevent

The config-versioning plan states it: *"a JAPES service may cache or project immutable releases in its own DB, but must not become a second source of truth."*

**At every strangler stage, exactly one system writes any given fact.** Plato may hold a read projection of anything; it may not hold a second writable copy of anything. Concretely: while eval-service owns feedback, Plato's database has no feedback table — not empty, not shadow, not "cache." A projection is read-only with the source's version stamped on it. If that slips, the estate has two control planes and reconciling them costs more than everything in §9.

---

## 6. Azure shape

`launcher.py:VALID_MODES = ("queue", "server", "dual", "ui")` — **`dual` is HTTP and queue in one process**, reported through `/health` as `{"interfaces": {"http": …, "queue": …}}`. Build on that; ACA jobs are an addition, not what it already means. A Postgres server exists separately; Plato adds a database. **japes has no Dockerfile and no alembic tree today** — both arrive with Plato.

| Concern | Shape | Note |
|---|---|---|
| Image | One image, several roles | `JAPES_RUN_MODE` extended. One build, one digest, role by env var. |
| `role=api` | Container App, scale on HTTP concurrency | Planes A–E HTTP surfaces; the only ingress. `ServerSettings.http_concurrency_limit` already bounds per-replica work. |
| `role=worker` | Container App, KEDA on queue depth | `queue_processor.py` already reports `approximate_message_count` — the KEDA metric exists. |
| `role=job:*` | ACA Jobs | Session/run reaping, closure-digest reverification, eval harness runs, backfills, alembic-as-a-job (never at container start). |
| Database | `plato` DB on the existing server | §7. Alembic owned by `plato/`. |
| Async | Azure Storage Queue | One inherited bug to fix: `queue_processor.py:95 _processed_message_ids` is **in-memory**, so at-least-once means duplicates across restarts. Point it at `automation/idempotency.py`, which exists. |
| Streaming | Redis, as `runs/` already uses | Journal `from_seq` makes a blip recoverable rather than fatal. |
| Identity | Entra workload identity outbound; **Keycloak/OIDC inbound** | UAF item 7. Genuinely absent today. |
| Authorization | Keto, already in `common/core/keto/` | *"Scope that as wiring, not building."* |
| Secrets | Key Vault via workload identity | No connection strings in env. |
| Observability | MLflow bridge + OTel → App Insights; `CanonicalTrace` → Postgres | Two audiences, two stores, one bridge. Do not merge them. |
| Security headers | **Shipped in 2.4.7** | `server/security_headers.py`, on by default. Plato's `role=api` serves a SPA, so it passes `spa_csp()` rather than the API default, and enables HSTS since TLS terminates in front of it. |

---

## 7. The database

### 7.1 Owns, projects, never

**Owns (writer):** assistant manifests and version history; profiles and skills as versioned config assets; releases, dependencies, closure digests; environment aliases; config audit events; sessions; runs and journals; durable suspensions; idempotency keys; canonical traces; versioned reference data and its overlays.

**Projects (reader, versioned, read-only):** pack metadata resolved at publish time; approved learning assets from eval-service; anything another system writes.

**Never:** another service's tables. The jstack finding — *"jstack reaches inside other services' databases. A schema change in `assistant` or `kernel` breaks a different repo's local bring-up, at runtime"* — is what not to repeat during the strangler, when the temptation peaks.

### 7.2 Schema layout

One database, five schemas. The prefix is what makes the `feedback` collision structurally impossible rather than avoided by convention.

```
plato_control    config assets, versions, drafts, releases, dependencies,
                 aliases, manifests, tenants, audit_events
plato_runtime    sessions, conversations, runs, run_journal, suspensions,
                 idempotency_keys
plato_trace      canonical_traces, trace_steps, override_events
plato_reference  versioned reference data + overlays: model_data versions,
                 pricing/card overlays with actor and provenance
plato_projection read-only projections of other systems' facts, every row
                 carrying source + source_version
```

`plato_projection` is named so a write into it looks wrong in a diff.

### 7.3 Control-plane shapes

Config-versioning Phases 3–5, with Plato as the durable implementation; protocols stay in `jazzx_sdk`.

- `config_asset(asset_id, tenant_id, kind[skill|profile|manifest], name, created_by, created_at)`
- `config_asset_version(asset_id, version_id, content, content_digest, semver, created_by, created_at, trace_id)` — **append-only**, unique on `(asset_id, version_id)` **at the DB level**; the nearest existing analogue has an autoincrement PK with plain indexes and only a read-first check, which is not race-safe
- `config_draft(asset_id, tenant_id, content, revision, updated_by, updated_at)` — mutable, `If-Match` on `revision`
- `agent_release(release_id, tenant_id, agent_id, status[candidate|approved|retired], closure_digest, resolved_pack_version, created_by, approved_by, …)`
- `agent_release_dependency(release_id, kind, asset_id, version_id, digest, floating, exception_ref)`
- `agent_alias(agent_id, environment, release_id, revision, updated_by, updated_at)` — promotion and rollback are pointer moves
- `audit_event(…)` — the shipped `ConfigAuditEvent`, pointed at a durable backend

Four rules, cheap now and expensive later:

1. **`content_digest()`** — shipped in 2.4.7 as `jazzx_sdk/digest.py`, canonical JSON with sorted keys. `closure_digest` builds on it rather than re-canonicalising.
2. **`closure_digest` is canonical JSON, sorted keys, one shared serializer, over an explicitly ordered graph.** Unstable ordering makes the digest worthless and the rollback test flap.
3. **Reuse `server/concurrency.py` verbatim** for the alias move — its docstring already anticipates exactly this caller.
4. **Status transitions ride `jazzx_sdk.statemachine`** following `GUIDANCE_LIFECYCLE`, which gives actor-class enforcement, terminal immutability and typed `Refusal`s for free. A blocked promotion is a designed governance outcome, not a 500.

### 7.4 Tenancy

`tenant_id` in **every key and lookup**, not in UI filtering. **D3 is answered: no tenant column or scoping exists anywhere in japes' config stores today.** Per the addendum, that makes the column shape a decision with Studio rather than a japes-local one — and under shape 3 it is *"a launch requirement for that service,"* not a later addition. It belongs in the same conversation as D1, because *"where is tenancy enforced"* and *"who owns the store"* are the same question asked twice.

---

## 8. API surface

All mutating routes on `GovernedRouter` (X-Trace-Id required, Idempotency-Key on mutation, `cell_ref`). All routes require a resolved `InvocationContext`; `require_identity` is forced on in a deployed posture.

### 8.1 Three tiers

**Plato exposes resources, not functions.** Putting a library's modules behind HTTP is a remote-procedure surface over a wheel: every internal refactor becomes a breaking API change. The public surface is five nouns; everything else is reached *through* them — a skill invocation already runs modes, fabric, conductor, guardrails and the authority resolver without a client needing `POST /modes/reason`.

| Tier | Contents | Contract |
|---|---|---|
| **Public product API** | assistants, releases, skills/actions, runs/sessions, traces | Versioned, frozen, generated docs; breaking changes cost something |
| **Operator API** | `platform_catalog`, model data + provenance + `unreviewed_models()`, release/alias inventory, `describe()` output, pack health | Unversioned, operator-auth, **explicitly not a customer contract** — where "expose more of the SDK" is cheap and safe |
| **Never exposed** | anything mutating a runtime registry out of band, or writing config outside release and closure discipline | One convenience endpoint undoes Plane B |

Test per endpoint: *does a client need this to build a product surface?* If it is only needed to debug or operate, it is tier 2.

### 8.2 Routes

**Plane A — runtime**
```
POST   /v1/assistants/{assistant_id}/chat
POST   /v1/assistants/{assistant_id}/chat/stream        → SSE
POST   /v1/assistants/{assistant_id}/sessions
GET    /v1/assistants/{assistant_id}/sessions/{sid}
DELETE /v1/assistants/{assistant_id}/sessions/{sid}
POST   /v1/runs                    /v1/runs/{id}/stop
GET    /v1/runs/{id}/stream?from_seq=                   → resumable
```

**Plane B — control plane**
```
GET|POST   /v1/assistants
GET|PUT    /v1/assistants/{id}/draft                    If-Match on revision → 409
GET        /v1/assistants/{id}/versions
POST       /v1/releases                                 resolve → freeze → digest
GET        /v1/releases/{release_id}
POST       /v1/releases/{release_id}/approve
PUT        /v1/aliases/{environment}                    If-Match → promote / rollback
GET        /v1/audit?target_id=&action=
GET|POST   /v1/skills          /v1/skills/{name}/versions
```

**Plane C — generated actions**
```
POST   /v1/assistants/{id}/skills/{skill}/invoke        sync; validated against Skill.inputs
POST   /v1/assistants/{id}/skills/{skill}/actions       async → 202 + operation ref
GET    /v1/operations/{operation_id}
GET    /v1/assistants/{id}/openapi.json                 generated from the release
GET    /v1/assistants/{id}/docs
```

**Plane D / E**
```
GET    /v1/traces/{trace_id}         /v1/traces/{trace_id}/steps
GET    /v1/traces?assistant_id=&release_id=&from=&to=
POST   /v1/feedback                  → eval-service, idempotent on stable event_id
GET    /v1/console/catalog           platform_catalog
GET    /v1/console/model-data        cards + pricing + provenance + unreviewed
GET    /v1/console/inventory         releases, aliases, packs, health
```

**Design rule for Plane C:** the route set is **derived from the resolved release**, never registered by hand. If adding a skill to an assistant requires a code change in `plato/`, Plane C has failed and we have rebuilt jstack's Go constant in Python.

---

## 9. Build plan

Sizes are relative, not calendar. Every phase names its adopter — the config-versioning plan's Risk 4 ("stores with no caller") applies to services too. The executable form, with per-phase anchors and the Claude Code protocol, is `plan_JAPES_PLATO_SERVICE.md`.

### Phase status (2026-08-27)

| | State |
|---|---|
| **P-1** — the six items queued for 2.4.7 | **Shipped** in `3714a5e` |
| **P0** — foundations | **Shipped.** Package, two import contracts, Dockerfile, alembic chain, six tables, OIDC, tenancy, posture, and `schema_version.py` — the image refuses to start when its expected schema revision does not match the database's |
| **P1** — assistant-addressed runtime | **Shipped.** Chat, streaming with resume from `?from_seq=`, cooperative stop, sessions — all on `GovernedRouter`. Its acceptance criterion is in the CHANGELOG nearly verbatim |
| **P2** — releases and aliases | **Split, and half is un-gated.** `release.py` computes and validates a release as a value, storing nothing — *"which is what lets it exist before the question of who owns the durable store is settled."* That half is in the tree, tested, uncommitted. The durable half waits on D1/D2 |
| **P3** — skill IO, generated routes, process-start | Not started. Gated on D5 |
| **P4** — trace of record | Not started |
| **P5** — reference data and console | **Shipped** bar the console's release view, which needs P2's storage half. The multi-replica overlay landed as `plato/reference/model_overlay.py` |
| **P6** — feedback seam and strangler | Feedback pass-through shipped, the `feedback` table name released to eval-service, and the kernel-agent converter built with the unconverted count as its metric. **Start reporting that count** |

Two things worth carrying forward from what shipped. **Every startup precondition Plato has is a refusal, not a warning** — identity enforcement, posture, and schema revision all fail the container rather than degrade it, on the stated reasoning that a container booting into a broken state *"looks healthy to an orchestrator and takes traffic."* And **P1's acceptance criterion tested the half that was easy to test**: it passed on the manifest while pack bytes still came from the container image, so a new tenant was still a deploy. `plato/packs/sources.py` fixed it. Worth remembering when writing P3's.

### P0 — Foundations (S)
`plato/` package as a sibling of `jazzx_sdk/`; the four §3.4 guardrails; the `docs/ARCHITECTURE.md` self-description edit; first Dockerfile and first alembic tree; roles over `JAPES_RUN_MODE`; health; alembic-as-a-job; Key Vault; `require_identity` **forced on**; Keycloak/OIDC verification; Keto wiring; the `plato` DB and its five schemas; durable backends for the shipped `ConfigAuditStore`, `SessionStore` and `AssistantManifestStore`.
**Acceptance:** CI fails a PR in which `jazzx_sdk` imports `plato`; installing `japes` without the extra pulls no `alembic`; **Plato refuses to boot in a deployed posture with `require_identity` off**; a manifest survives a process restart with `history()` intact.

### P1 — Plane A: the assistant-addressed runtime (M) ← *the proof*
Tenant-scoped `ProfileRegistry`, agent cache keyed on `(tenant, assistant_id, release_id)`, chat + stream + sessions over the durable stores.
**Acceptance: two assistants with different manifests, packs and personas served from one running Plato instance, added by writing configuration, with no deploy and no code change.** A stream survives reconnect and resumes from `from_seq`. A session past TTL is reaped and its resume returns a typed refusal, not a 500.
*Ship this before arguing about the rest.*

### P2 — Plane B: versioned assets, releases, aliases (L)
Config-versioning Phases 3–5 with Plato as the durable store. Backfill current config as version 1 with `actor_type="migration"`.
**Acceptance, written first: rollback to a prior release reproduces the same `closure_digest` and the same effective spec, on a graph whose registries have since changed.** Publishing a new skill version alters no existing release. Two concurrent draft writes: one 200, one 409. A release whose stored digest does not match its recomputed closure fails at load, before any turn runs. No backfilled row carries `actor_type="user"`.
**And the real one: `assistant`'s `promotion.py` can be retired against this rather than coexisting with it.**

### P3 — Plane C: skill IO on the execution path, generated routes, process-start (L)
Settle contested item 4; derive schemas from the wrapped agent/tool/process and give the def-backed and `spec_ref` branches real typed signatures; generate routes and OpenAPI; own process-start.
**Acceptance:** the PRD's test, unmodified — **a frontend developer builds a working screen against the generated docs with no core engineering involvement.** A malformed body is rejected by schema before reaching a model. An async action returns 202 and its operation resolves. A BPMN process instance can be started.

### P4 — Plane D: trace of record (M)
Settle UAF item 9. Persist `CanonicalTrace` and serve it by extending `observability/trace_routes.py` under `/v1` rather than adding a second lookup. Carry `agent_release_id` and per-dependency refs — in `VersionBundle.extra` until a named field clears the governed schema change. Dual-read with a `legacy_unversioned` marker.
**Acceptance:** a trace from a released assistant names the exact release and every skill version actually invoked; a legacy trace carries `legacy_unversioned` and no release id; the marker is emitted from **day one** — *"a migration window with no marker is indistinguishable from a migration that already finished."*

### P5 — Plane D: feedback seam (S–M)
Stage 1 of §5.2 only.
**Acceptance:** a forced ambiguous retry produces exactly one eval-service row and returns the same `FeedbackAcceptedV1`. `plato` contains no feedback table.

### P6 — Strangler (ongoing, no estimate)
Kernel-agent → `InteractiveAgentSpec` converter; the KEEP/SERVICE-LAYER items; `jazzx-assistant` as a manifest; Studio writing to Plato's control plane.
**Metric, reported weekly:** count of kernel-agent rows with no v2 representation. The only number that says whether this is working.

```
P-1 (2.4.7) ──► P0 ─┬─► P1 ─┬─► P2 ─► P3
                    │       └─► P4
                    └─► P5  (independent)
                                P6 (starts after P1, runs alongside)
```

---

## 10. Decisions that gate work

Named accepter per row, per §5.3.

| # | Decision | Gates | Accepter |
|---|---|---|---|
| **D1** | **Adopt shape 3** — Plato is the durable system of record for assistant config. **Recommended in writing** in `note_D1_D2_DECISION_MEMO.md`, with the Studio owner since 2026-08-24. Its deciding argument is sharper than this document's: since v2 capability *is* configuration rather than code, a configuration version **is** the release, and a release whose digest does not match its recomputed closure has to fail *at load* — and the thing that loads a release is Plato. | **P2's storage half**, and by now most of what remains | SDK owner **+** Studio owner |
| **D2** | **Does Studio write to Plato's API, or keep its own store?** Recommended in the same memo: Studio writes to Plato's API and Plato stays the only writer. If both write, there are two writers on day one and §5.4 is already lost. | P2, P6 | Studio owner |
| **D3** | **Is Plato the owner of process-start?** UAF item 6's *"name an owner"* is still open. | P3 | Platform architect **+** Kernel owner |
| **D4** | **Do we state the eval-service absorption intent now, or hold at Stage 1?** Recommendation: state Stages 1–2, hold Stage 3. | Nothing technically; everything politically | Platform lead |
| **D5** | **Contested item 4 — per-skill IO on the execution path.** The record shipped; the execution path was deliberately left alone. Nothing generates routes until this is settled. | P3 | SDK owner |

Already settled, do not relitigate: **addendum D2 shipped** as `jazzx_sdk/digest.py` in 2.4.7, and **tenancy is absent everywhere, so under shape 3 it is a launch requirement, not a later column** (addendum D3).

---

## 11. Risks

1. **Plato becomes a second source of truth.** Highest probability, and it looks like progress while it happens. Mitigation: `plato_projection` read-only by schema and by review rule; no writable copy of another system's fact at any stage.
2. **Plato accretes product semantics.** jstack's exact failure. Mitigation: §3.3's review question — *what row does this value come from?*
3. **Colocation erodes the SDK/service boundary.** The price of §3.4, and the first violating PR will look reasonable. Mitigation is guardrails 1 and 2, and they only work if they land in **P0** — a boundary added after the first violation is a refactor, not a rule.
4. **P2 grows into a registry refactor.** The config-versioning plan's own top risk, inherited whole. Its task-3 boundary is the mitigation: the versioned store is additive, `_registry.py` and `agents/interactive/registry.py` untouched until runtime pinning. A diff there means scope escaped.
5. **P3 stalls on D5.** Plane C is worthless without declared IO on the execution path, and that change touches `_build_parent_tools` — *"the deepest change."* Mitigation: settle D5 before P3 starts; if it slips, P4 moves ahead of P3.
6. **The eval-service conversation goes badly.** Mitigation: §5.2's staging and §5.3's ownership bar. Stage 1 is genuinely cooperative and it is all v1 commits to.
7. **The tree moves faster than the plan.** Now four instances in four days — the six 2.4.7 items, then Phases 0, 1, 5 and most of 6: thirteen UAF phases and two config-versioning phases had landed before the first read; then all six items this document queued for 2.4.7 landed in `3714a5e` while the draft was being circulated. Expect more. Re-verify every anchor before estimating; **if an anchor is gone, stop and report.**

---

## 12. Open questions

- **The eval-service repo was not read** — last known `edd3cfb` (2026-07-30), now four weeks stale. §5.2's staging assumes its shape has not moved.
- **Sibling consumer repos were not read** — `jaci`, `jazzx-assistant`, `kernel`, `assistant`, `macer`. The caller audits behind P-1 item 6, P0's forced `require_identity`, and P2's `promotion.py` retirement all need them. `assistant/app/assistant/promotion.py` in particular should be read in full before P2 is designed.
- **`JAPES_2_3_6_RECONCILIATION.md` and its five submission blockers** — the engineering queue's standing "one thing to find," not present in `ape/` either. Gates P5.
- **Whether `jazzx-eval-contracts` was published.** `jazzx_eval_contracts/` exists in the tree; its publication state was not checked.
- **The Postgres server** — version, sizing, Flexible vs Single Server, and whether adding a database is a ticket or a terraform change.
