# Plato runs domain packs: pack-declared case runs and self-contained assistant packs

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-24. Nothing built. Written against japes `5534f5e` on `v2.5.4` (Plato 0.1.6).
Target: next minor, to be assigned.

Companion (consumer side): jaci `docs/plans/plan_JACI_PLATO_PILOTS.md`. Two jaci scenarios are the
pilots — **DSCR** (a governed case run) and **clinical intake** (an assistant) — because together
they exercise both halves of what Plato is missing, and each is small.

Builds on, and must not contradict:

| Plan | What it already decided that this one keeps |
|---|---|
| `plan_pack_store.md` Rev 3 §8-§10 | the SDK receives pack **rows, never pack knowledge**; `plato/` holds no domain words; stores are a protocol + Db implementation in `jazzx_sdk`, Plato registers and migrates them; stores are tenant-scoped at construction; a published `(pack_id, version)` is immutable |
| `plan_pack_upload.md` | publishing is not activating; correcting a pack is a new version (409 on an existing one) |
| `plan_plato_authoring.md` | nothing that has answered a request can change afterwards |
| `plan_queue_execution_cancellation.md` | cancellation is a durable flag checked on the heartbeat, not `task.cancel()`; terminal is a no-op |
| `plan_streaming_chat_pipeline.md` | streaming is out of band through a sink; one step still emits one value |
| `plan_agent_definition_store_and_facade.md` | `SuspensionStore` / `DurableSuspension` is the resume primitive |

---

## 1. What Plato can and cannot do today

Plato hosts **assistants** (manifest + profile + skills → `build_from_manifest` → an
`InteractiveAgent`) and a **pack registry** (upload, draft, publish, activate, per-file read).
`/invoke` refuses by design (`plato/app.py` `NoInvokeHandler`). Verified at `5534f5e`:

1. **No domain-pack runtime.** `published_registries` skips any row without `assistant_id`
   (`plato/packs/loader.py:244-247`). Activating a domain pack answers 409 (`load_pack` wants a
   `manifest.yaml`). `jazzx_sdk.pack.domain.published_domain_packs` exists and nothing calls it.
2. **No way to name an SDK conductor from YAML.** `Pack.conductor` only resolves a dotted Python
   pointer (`pack/pack.py:393-405`). `StepRegistry` is never populated outside tests.
   `PIPELINE_REGISTRY` / `MODE_REGISTRY` are metadata strings. `experts.*.class` and
   `modes.*.class` are read by nothing. The ci-spread-core seed manifest already carries
   `TODO(conductor-pipeline-from-yaml)`.
3. **Modes need Python types.** `InvestigatorMode(hypothesis_content_type=...)` and
   `ReasonerMode(output_schema=...)` take Pydantic classes; `InvestigationSpec.fulfill_evidence` is a
   required callable. None of that can come from an uploaded pack as it stands.
4. **Durable runs are not wired.** Neither `plato/wiring/default.py` nor `local.py` sets
   `runner` / `dispatcher` / `run_store`, so `/chat/stream`, `/runs/{id}/stream` and
   `/runs/{id}/stop` are never mounted. No reaper runs. `TurnRun` is chat-shaped (required
   `conversation_id`, completion = an event with `.done`, `partial_output` from `.delta`, `drain`
   reads only `messages`/`scope`/`session_id`). `ConductorEngine` has no stop check. There is no
   status for "suspended awaiting a human", and `conductor_suspension` is not in Plato's models or
   migrations (0001-0005).
5. **Assistants get only an LLM.** `agent_extra={"llm_manager": ...}` (`default.py:852`) — no fabric,
   no tools, no guardrails. A profile naming a guardrail fails at turn time
   (`agents/interactive/agent.py:506-526`); `plato/packs/check.py:175` says such a guardrail is
   "dropped at build time, silently", which is wrong — one of the two needs correcting.
6. **Assistants write nothing canonical.** `agents/interactive` has no `put_evidence` /
   `put_trace` / `put_decision` / `put_outcome`. jaci hand-wires this for clinical intake
   (`scenarios/clinical_intake/session.py`), and its own docstring calls it a japes gap.
7. **An assistant pack cannot carry domain assets.** The loader wants root `manifest.yaml` +
   exactly `profile/profile.yaml`; the store tells the shapes apart by `assistant_id`. A pack that
   is both — clinical intake has policies, an intake protocol *and* an agent — has no shape.
8. **No archive download, no dry-run check for domain packs, no documents upload, no HTTP client.**
   `GET /packs/{id}/{version}` returns per-file text only. `check.py` covers assistant packs only.
   Nothing in `jazzx_sdk.clients` targets Plato.
9. **A laptop Plato on the `deployed` profile cannot be used for either pilot.** `dev-daily` with
   `PLATO_PACK_BLOB_BACKEND=local` refuses every publish; no Knowledge Hub URL 503s every chat turn;
   the local wiring's `activator()` is None, so activation answers 501.

## 2. The rule that shapes the design

**An uploaded pack is data. Plato never imports Python from a pack.** Packs arrive continuously,
production included (`plan_pack_upload.md`), so a `class:` pointer in an upload is a remote-code
path. Therefore:

- What a pack can *run* is a closed set of **conductor kinds** and **step kinds** that ship in
  `jazzx_sdk`. A pack selects one and configures it.
- Anything genuinely custom is an **image-level plugin**: a Python package installed into the image
  and registered through an entry point (`jazzx_sdk.conductor_kinds`, `jazzx_sdk.step_kinds`,
  `jazzx_sdk.evidence_connectors`, `jazzx_sdk.guardrail_kinds`). Deploying one is a release, not an
  upload.
- A pack that names a kind the image does not have fails **at publish** (the check), not mid-run.

Both pilots fit in SDK kinds with no plugin, which is the evidence the rule is not too tight
(§4.3, §5.2).

**Amended 2026-09-24: generated Python rules are allowed in packs; executing them is undecided.**
A `python` condition (see `plan_policy_jtbd_extraction.md` §2b) is pack data that Plato stores,
checks statically at publish, and does not execute unless the deployment installs a
`PythonExecutor`. Without one the rule evaluates INDETERMINATE (`policy_not_activated`), which
withholds an allow rather than skipping it. The rule above still holds for `class:` pointers and
conductor code; this amendment covers rule conditions only.

## 3. Shared plumbing (Phase 0)

| # | Work | Where |
|---|---|---|
| 0.1 | Wire `runner` / `dispatcher` / `run_store` in `default.py` and `local.py`, so the streaming routes mount. Keep ownership on the run (`plato_tenant_id`) as the assistants router already does. | `plato/wiring/*` |
| 0.2 | `job:run-reaper` role: `Reaper` over `turn_run` (`reap_stale`, `purge_terminal`) per tenant, the shape of `job:session-reaper`. | `plato/jobs.py` |
| 0.3 | Local profile usable for pack work: `local.py` gets an `activator()`, accepts publish with the local blob backend (local tier only — the durability refusal stays for every deployed tier), and defaults the tenant when identity is off. | `plato/wiring/local.py` |
| 0.4 | Hand the fabric to assistants: `agent_extra` gains `fabric=client_layer.fabric`. The 503 readiness gate on a missing Knowledge Hub URL stays for deployed tiers; the local profile serves against the Mock and says so in `/info`. | `plato/wiring/default.py` |
| 0.5 | `GET {prefix}/packs/{pack_id}/{version}/archive` — the published archive bytes (gated like `pack_version_detail`). Lets a client materialize exactly what Plato serves. | `plato/api/packs.py` |
| 0.6 | `POST {prefix}/packs/check` — multipart archive, no publish; returns `PackCheckReport` for **both** shapes: assistant (`check_assistant_pack`) and domain (`lint_pack` + typed `DomainPack` + the conductor-kind resolution of §4.3). The same function runs inside publish, so check and publish cannot disagree. | `plato/packs/check.py`, `jazzx_sdk/pack/lint.py` |
| 0.7 | `jazzx_sdk.clients.plato_client.PlatoClient` (httpx, async): tenant header, packs (check / publish / activate / archive / list), runs (§4.5), assistants (sessions / chat / stream / close / outcome, §5.4), and SSE resume by `from_seq`. Typed replies reuse the router models. | `jazzx_sdk/clients/` |
| 0.8 | Reconcile the guardrail contradiction in §1.5 (the check should report an unresolvable guardrail as an error, since the turn raises). | `plato/packs/check.py` |

## 4. Case runs (DSCR pilot)

### 4.1 What DSCR does today, and what of it is already SDK

`jaci/scenarios/dscr/conductor.py`:

1. **Deterministic assessment before any model call.** It builds a flat context from the loan,
   runs `DefaultPolicyExpert.check_compliance` over the pack's policy + `PolicyProfile` (SDK), then
   `compose_caps` (jaci): the minimum over every matrix rule comparing `cltv_pct`, naming the
   binding rule. The result becomes an attested `Evidence` and `ctx.metadata` entry.
2. **Investigation loop.** `investigation_loop` with the five operational modes (SDK), prompts from
   jaci's `prompts/dscr/`, Pydantic `DSCRHypothesisContent` / `EligibilityRecommendation`, and a
   two-tool mock `DSCRToolRegistry`.
3. **Post-processing.** Reasoner fallback (a literal `REFER_TO_UNDERWRITER`), governor remap, and
   `_enforce_deterministic_verdict` — a model approval cannot override a deterministic violation.
   The narrator gate is `governor.approved and decision == INELIGIBLE`.

Everything jaci-specific in that list is either a derivation (`cltv_pct = 100 * loan_amount /
property_value`), a schema, a literal, a predicate, or the cap composition. None of it needs pack
Python if the SDK gains the pieces below.

### 4.2 SDK additions

| # | Addition | Notes |
|---|---|---|
| 4.2.1 | **`policy_assessment` step kind.** Inputs → derived fields (pack `metrics:` as `MetricDefinition`s, evaluated by `jazzx_sdk.expressions`) → `DefaultPolicyExpert.check_compliance` with the pack's policy registry + profile → optional **cap composition** → a typed `PolicyAssessment` (allowed, violations, rationale, composed caps, derivations). | Lifts jaci's `compose_caps` into `fabric.canonical` as generic matrix-cap composition keyed by `compare_field` and `strategy: min`. "Several caps bind; which one wins" is not DSCR-specific. |
| 4.2.2 | **Schemas from pack JSON Schema.** `schema_from_json(path) -> type[BaseModel]` (via `pydantic.create_model`) so a pack supplies `input_schema`, `hypothesis_schema`, `decision_schema`. Supported subset stated and checked at publish (objects, enums, arrays, nested refs, required, defaults); anything outside it fails the check. | Default hypothesis/decision schemas ship in the SDK for packs that do not supply one. |
| 4.2.3 | **Pack-declared evidence tools.** `evidence_tools:` maps each evidence type to a source: `input` (a path into the run input), `fixture` (a JSON file in the pack, by subject id with a default), or `connector` (a name resolved in the image's `jazzx_sdk.evidence_connectors` registry). The SDK builds `fulfill_evidence` from it, degrading to `UNAVAILABLE` evidence the way `DSCRToolRegistry.execute` does. | Fixtures keep a demo pack runnable with no vendor. |
| 4.2.4 | **Gates and literals as expressions.** `narrator_gate`, `convergence_gate`, `deadline_guard` as expression strings over `{governor, decision, ctx}`; `on_reasoner_failure` as a literal decision object validated against `decision_schema`. | Reuses the expression grammar — no `eval`. |
| 4.2.5 | **`deterministic_verdict: authoritative`.** When set, a failed `policy_assessment` overrides a governor approval and merges its violated rule ids — jaci's `_enforce_deterministic_verdict`, generalized. | |
| 4.2.6 | **Engine stop.** `ConductorEngine(stop_requested=async () -> bool)`, checked between steps; a stopped run halts with `status="interrupted"`. | Durable-flag model, per `plan_queue_execution_cancellation.md`. |
| 4.2.7 | **Canonical output.** A run persists `CanonicalTrace` **with one `TraceStep` per mode call** (the granular steps no conductor emits today), `CanonicalDecision` (policy_refs from violations + governor), and its evidence, through `fabric.canonical`; the run row carries the same as `output`. | Closes the thin-trace gap jaci found in 2026-08. |

### 4.3 Conductor kinds, and the manifest block

`jazzx_sdk.pipelines.kinds` — a registry of conductor kinds, populated by the SDK at import and
extended by the `jazzx_sdk.conductor_kinds` entry point. First kind: **`investigation_loop`**, which
builds an `InvestigationSpec` from pack config. `Pack.conductor` resolves `kind:` through the
registry; the dotted `pipeline:` pointer keeps working for in-process callers (jaci) and is refused
by Plato's check.

DSCR's manifest block (illustrative — exact keys settled in 4.2 review):

```yaml
conductor:
  kind: investigation_loop
  input_schema: schemas/loan_application.json
  subject_field: loan_id
  pre_loop:
    - kind: policy_assessment
      metrics: metrics.yaml            # cltv_pct
      compose_caps: {compare_field: cltv_pct, strategy: min}
  modes: {investigator: {model: flex_gpt-5.4}, verifier: {}, reasoner: {temperature: 0.7}, governor: {}, narrator: {}}
  hypothesis_schema: schemas/hypothesis.json
  decision_schema: schemas/eligibility_recommendation.json
  evidence_tools: evidence_tools.yaml
  max_iterations: 5
  on_reasoner_failure: {decision: REFER_TO_UNDERWRITER, rationale: "Reasoner failed - deferring to manual underwriter review"}
  narrator_gate: "governor.approved and decision.decision == 'INELIGIBLE'"
  deterministic_verdict: authoritative
```

Prompts come from `mode_tuning/<mode>.md` through `compose_mode_prompt`, as for every other pack.

### 4.4 Runs as a second kind of `TurnRun`

Reuse the run infrastructure rather than add a parallel one; its store, journal, claim, heartbeat,
reaper and SSE resume are already generic.

- Migration `0006`: `turn_run` gains `kind` (`turn` | `case`, default `turn`), `output` (JSON), and
  status `SUSPENDED`. The FIFO key stays `conversation_id`; a case run sets it to
  `case:{pack_id}:{subject_id}`, so two runs of the same case serialize and different cases run
  concurrently.
- `CaseRunner`: builds the conductor from the pinned pack version, adapts `ConductorEngine.on_step`
  events into journal events (`{"step", "status", "emitted_summary"}`, a final `{"done": true,
  "output": ...}`), passes `stop_requested` from the run's durable flag, and writes `output`.
- Dispatch stays in-process `asyncio.create_task` for the pilot, as chat is today. A queue worker
  role is a separate decision, deliberately out of this plan.
- The run records `pack_id` + `pack_version` + archive digest at submit, so a decision always names
  the pack version that produced it (`plan_pack_store.md` §4.1).

### 4.5 New routes

| Route | What it does |
|---|---|
| `POST {prefix}/packs/{pack_id}/assess` | Synchronous `policy_assessment` against the active version (or `?version=`). No LLM, no run row; body is the conductor's input schema. The cheap call a UI makes on every keystroke — DSCR shows the grid before anyone clicks Run. |
| `POST {prefix}/packs/{pack_id}/runs` | Validate input against `input_schema` (422 on mismatch), create a `case` run, start it, 202 `{run_id, conversation_id, stream}`. Governed: `Idempotency-Key` honoured. |
| `GET {prefix}/runs/{run_id}` | Status, pack pin, `output` when terminal. Tenant-owned; another tenant's run is a 404. |
| `GET {prefix}/runs/{run_id}/stream?from_seq=` | SSE journal; resumable, same framing as the assistant stream. |
| `POST {prefix}/runs/{run_id}/stop` | Durable stop flag. |
| `GET {prefix}/runs?pack_id=&subject_id=` | A case's runs, newest first. |
| `POST {prefix}/runs/{run_id}/resume` *(Phase 3)* | Resolve a suspension: `{resolution, approver_ref, authority_basis}` → `resume_durable`. |

### 4.6 Activation for domain packs

Activating a domain pack pins the version `assess` and `runs` use for that tenant (today it 409s).
It does not touch assistant registries. `published_domain_packs` becomes the lookup; `pins_for`
already persists the pointer.

### 4.7 Human checkpoints (Phase 3)

`human_checkpoints` in the manifest (DSCR: `ELIGIBILITY_DECISION_APPROVAL`) becomes a real suspension
after the governor: register and migrate `DbSuspensionStore` (`conductor_suspension`, tenant-scoped),
the run goes `SUSPENDED`, `/resume` continues it. Until then a DSCR run completes with
`human_review_required=true` on the decision and the client records the human's answer as an
`Outcome` (§5.4's outcome route generalizes to runs: `POST {prefix}/runs/{run_id}/outcome`).

## 5. Self-contained assistant packs (clinical-intake pilot)

### 5.1 What clinical intake does today

jaci builds an `InteractiveAgent` from `config/packs/clinical-intake-core/agent/`, passes guardrails
built in Python from the pack's policies (keyword lists in `rule.parameters.keywords`, block reason
`"[<rule_id>] <description>"`), and wraps every turn in `IntakeSession`: patient utterance →
`Evidence`, a `TraceStep` per turn, an escalation `Decision` bound to the fired clause, a
completeness check against `intake_protocol.yaml` at close, and a nurse `Outcome`. The client tags
each turn with the protocol section it answers.

### 5.2 SDK additions

| # | Addition | Notes |
|---|---|---|
| 5.2.1 | **Guardrail kinds from pack data.** A registry of guardrail kinds (`jazzx_sdk.guardrail_kinds` entry point for more); first kind **`policy_keywords`**: `{policy_id, direction: input|output}` → the detector jaci has in `guardrails.py`. Profile guardrail names resolve against the pack's `guardrails.yaml` first, then the deployment catalog. A block carries a structured `block_rule_id`, not just a formatted string. | The keyword lists already live in the policy YAML; only the matcher moves. |
| 5.2.2 | **Session recorder.** Opt-in on the profile (`record: {ontology_id, evidence_type, subject: scope.encounter_id}`): per turn an `Evidence` and a `TraceStep` (governor-escalated or narrated), on a block a `DISPOSITION`/`ESCALATION` `CanonicalDecision` bound to `block_rule_id`. | jaci's `IntakeSession` minus the demo bits. |
| 5.2.3 | **Completeness contracts.** `protocol:` in the pack (sections, required flags) and a session-level coverage set fed by `scope.section` on each turn. `close()` computes complete / missing and writes the terminal decision (`INTAKE_COMPLETE` / `…_INCOMPLETE_FLAGGED` / `ESCALATED` are pack literals, not SDK words). | Section attribution by the client is the pilot; model attribution is a later step. |

### 5.3 One pack, both halves

Decision D3 below. Recommended: an assistant pack's root `manifest.yaml` may name
`domain_manifest: pack_manifest.yaml`; when present, the loader reads policies, profiles,
`guardrails.yaml` and `protocol:` from it through `Pack`, and the store still classifies the pack by
`assistant_id`. jaci's `agent/` becomes `profile/` (same file format — mechanical).

### 5.4 New routes

| Route | What it does |
|---|---|
| `POST {prefix}/assistants/{aid}/sessions/{sid}/close` | Completeness + terminal `Decision` + `Trace`; returns `{decision, decision_id, trace_id, completeness, escalated_rule_id, summary}`. Idempotent: a closed session returns the same answer. |
| `POST {prefix}/assistants/{aid}/sessions/{sid}/outcome` | The human's review → linked `Outcome` (`confirmed`, `override`, `notes`). 409 before close. |
| `GET {prefix}/assistants/{aid}/sessions/{sid}/record` | The session's canonical chain: evidence ids, trace, decision, outcome. |

`ChatRequest.scope` already exists; `scope.section` needs no route change. `ChatReply` gains
`block_rule_id`.

## 6. Phases

| Phase | Contents | Unblocks |
|---|---|---|
| 0 | §3 plumbing | both pilots against a local Plato |
| 1 | §5 assistant packs + guardrail kinds + recorder + protocol + routes | jaci clinical intake on Plato |
| 2 | §4.2-§4.6 conductor kinds, `policy_assessment`, schemas, evidence tools, case runs, `assess` | jaci DSCR on Plato |
| 3 | §4.7 suspension/resume + run outcomes; documents upload (DSCR's optional appraisal) | HITL in the run, not the client |
| Later | a second conductor kind (`conductor_pipeline`: `ConductorEngine` over a pack `pipelines.yaml` with SDK step kinds — ci-spread-core's shape); a queue worker for runs | C&I and the rest of jaci |

Phase 1 is first because it is smaller and has no migration. Phase 2's migration `0006` is the
only schema change before Phase 3.

## 7. Decisions

| # | Question | Recommendation |
|---|---|---|
| D1 | Case runs: extend `turn_run` or a new table? | Extend (§4.4). The infrastructure is generic except for four chat assumptions, all addressable by a runner variant; a second table duplicates claim/heartbeat/reaper for no gain. |
| D2 | Where custom behaviour lives | Closed SDK kinds + image-level entry-point plugins; never pack Python (§2). |
| D3 | A pack that is both assistant and domain | `manifest.yaml` + `domain_manifest:` (§5.3). Alternative: a domain `pack_manifest.yaml` with an `assistant:` block — rejected because the store's classifier and every assistant path already key on `manifest.yaml`. |
| D4 | Section attribution for completeness | Client-supplied `scope.section` for the pilot. |
| D5 | What activating a domain pack means | Pins the version for `assess`/`runs`; no registry effect (§4.6). |
| D6 | JSON Schema subset for pack schemas | State it, enforce it at check (§4.2.2). |
| D7 | Whether `compose_caps` is SDK | Yes — generic matrix-cap composition (§4.2.1). |
| D8 | Dispatch for case runs | In-process for the pilot; queue worker decided separately. |

## 8. Acceptance

- **Phase 0:** a local-profile Plato accepts `POST /packs/check`, publish and activate of jaci's
  `dscr_core` and `clinical-intake-core` archives; `/chat/stream` and `/runs/*` are mounted;
  `PlatoClient` round-trips each route in tests against `create_plato_app`.
- **Phase 1:** a clinical-intake session over HTTP reproduces jaci's gold personas: the chest-pain
  persona blocks on `CI-ESC-*` with `block_rule_id` set; close yields `ESCALATED`; the record route
  shows Evidence per turn, one Trace, one Decision, and after `/outcome` one Outcome.
- **Phase 2:** `POST /packs/dscr-core/assess` returns the same `allowed`, violations and binding cap
  as jaci's in-process `run_eligibility_assessment` for every `tests/eval/gold_cases/dscr` case;
  `POST /packs/dscr-core/runs` completes, streams one event per step, persists a Trace with one step
  per mode call, and a deterministic violation is never overridden by a governor approval; stop
  interrupts between steps.
- A pack naming an unknown kind, a `class:` pointer, or a schema outside the subset fails
  `/packs/check` and publish with a named finding.

## 9. Not in this plan

- Executing pack-supplied Python in any form.
- Moving jaci's other scenarios (C&I, CRE, AML, KYC) — they follow the `conductor_pipeline` kind.
- A queue worker, multi-replica run dispatch, or a Flowable handoff.
- The bundled `plato/data/seed_packs` copies: seeding only, not production, untouched here; jaci's
  `config/packs/` is the authoring source and publishes into Plato.
