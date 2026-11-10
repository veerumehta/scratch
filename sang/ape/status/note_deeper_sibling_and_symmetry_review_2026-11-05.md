# Deeper sibling and symmetry review, 2026-11-05

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Read only. Five parallel reads of the `japes-v268` tree (v2.6.9) and the sibling clones, one per theme: the clone work, tenancy and unique keys, macer's
metrics engine, the Plato guide, and a capability matrix across the three layers (library, SDK, Plato). Nothing was run and no provider was called. Claims
marked VERIFIED were read in code (the ones marked checked below were re-read by the coordinator); INFERRED means reasoned, not run. Builds on
`note_sibling_survey_2026-11-03.md`, `_11-04.md` and `_11-05.md`.

Corrections to the earlier notes: BSD-5511 is the multi-tenancy integration branch (tenant columns, RLS, workspace and sub-tenant), not the clone work, and
"sandbox integration" is only the merge branch's name. The clone work is PAGI-2082, BSD-5915, #135, #138, #159 and #177. macer's "refs in conditions" is
document-reference carry-over in merged conditions, not formula references. macer's income-worksheet engine is a generated copy of a mortgage-app tool.

## 1. Strict posture and error model across the clients (library and fabric; the largest family)

One gap in four places: an outage reads as "absent". Checked by the coordinator: `raise_on_unavailable` has no non-test caller outside the docs store's own
docstring and guard, so `fabric.docs.get_or_none` always refuses on a default hub (`TODO(get-or-none-needs-strict-hub-client)`); `KernelClient.get_agent`
returns None on any exception; `fabric.blob.get` returns None and `delete` False on any exception.
- 1a. `ClientLayer.knowledge_hub` sets `raise_on_unavailable` when `strict_mode()`; closes the TODO. About 15 lines plus a test.
- 1b. `KernelClient` gets the same flag and a typed `KernelUnavailable` mapping (the admin services already use it). About 60 lines.
- 1c. `fabric.blob` and `fabric.entities` get a strict option or a typed error instead of None and False. About 40 lines.
- 1d. One named `RetryPolicy` taken by both clients (reuse `concurrency.rate_limit.RetryPolicy`); today there are four shapes (none on KH and Kernel,
  `retry_async` in `fabric.docs`, DocIntel's own 429 loop, PlatoClient's opt-in `_retry.py`). About 100 lines. INFERRED that one policy fits.
- 1e. A `KernelLike` protocol and a parity test, as KH has (`kh_protocol.py`); `MockKernelClient` lacks `.agents`, `.tools`, `.llms`, `.notepads`, `.chat`,
  `.config`, `get_agent` and `call_parallel`. About 120 lines.
- Bigger idea A: one `ServiceClient` base for the KH, Kernel and DocIntel wrappers holding the error model, posture, retry policy, limits and transport
  arguments and the mock protocol. It would not merge the generated clients, change wire behavior or touch PlatoClient.

## 2. Tenancy (SDK store layer and Plato migrations; a decision comes first)

- VERIFIED (checked): `uq_eval_dataset_version` and `uq_eval_custom_scorer_revision` still exist beside their tenant-leading twins (`datasets_db.py:67`,
  `custom_scorers_db.py:53`, `0007_eval.py`); migration `0013_tenant_keys.py` added the twins and never dropped the old keys. Fix: one migration plus the
  model edits, about 40 lines.
- Design gaps, VERIFIED by the agent: single-column primary keys with no tenant (`eval_dataset.dataset_id`, `eval_custom_scorer.scorer_id`,
  `eval_optimization_job.job_id`, `eval_experiment.experiment_id`, `config_audit_event.event_id`); tables with no tenant column (`agent_definition`,
  `japes_queue_execution`, the conversation tables); a thin guard test with a stale docstring; `TODO(tenant-keyed-store-reads)` in `fabric/tenancy.py:107`.
- Two models: japes enforces a free-form string tenant in the application (default `"default"`); common uses a UUID platform tenant with `DB_TENANCY_MODE`
  and `PLATFORM_TENANT_ID`. Which to keep is the user's decision. Adopting common's classification is a separate programme (UUID tenant, rebuilt keys).
- common 0.4.0: no-go until the branch is rebased onto main and tagged (it was cut from an old base and deletes the co-borrower events; it renames
  `IDENTITY_TENANT_ID`). With the default `off` its boot refusal passes. Then about a day: the pin bump plus a boot test with `observe` and no tenant that
  expects a refusal, and one with `off` that expects success.
- BSD-5632 (PR #101): the workspace claim fits as an opt-in claim to kernel; common also reads `x-workspace-id` while the claim declares only
  `x-sub-tenant-id`.
- eval-service also added RLS and hides workspace traces from base listings (tag `sub_tenant_id`); japes has neither. A gap only if Plato's trace listing
  serves a workspace-mixed backend.

## 3. Metrics and conditions (SDK; pack-neutral; none needs the MACER decision)

- 3a. Evaluate a pack's metrics in dependency order (about 25 lines). Checked: `_derive` in `pack/assessment.py` loops the definitions in file order and
  passes only the input lines; `evaluate` reads a `CUSTOM_METRIC` binding from `context.metrics` (`expressions/evaluate.py:179`). INFERRED: nothing fills
  `context.metrics`, so a metric that reads another is refused. Reuse `validate._circular_references`.
- 3b. A NOT_APPLICABLE verdict closes prior conditions with a reason (about 15 lines); today a gated NOT_APPLICABLE rule returns a fresh outcome with no
  conditions. INFERRED; the file reference the agent gave does not exist in the tree, so re-find the carry-over code first.
- 3c. Metric notices as pack data (`notices: [{when, message}]`, about 20 lines), only if a pack needs to flag a computed value.
- 3d. Labeled links to upstream metrics in `MetricDerivation.inputs` (medium); waits for 3a.
- Not proposed, because japes shows no matching problem: per-year dict corrections, action-key dedup, a cycle check on aliases.

## 4. Plato surface (Plato and SDK)

- 4a. The guide is one hand-written file, `plato/guide.md` (73 lines), with a hand-typed 11-route table that already misses the cases, coverage, vocabulary,
  ontology, document-catalog, blueprints, experts and reviews routes, and no test ties nav, routes or pages to it. The proposed structure: a "Start here"
  page with the three-layer map and a glossary; Library, SDK and Plato groups; a page tour keyed by nav label; tables generated from `platform_catalog`, the
  lint codes and remedies, the rules-library manifests, model cards, the route list and the scope-claim names. Section files with `<!-- generated: x -->`
  markers expanded into markdown tables; an anti-rot test over nav labels, route prefixes, lint codes and rules functions. Four small stages of about 80 to
  120 lines each, starting with the page tour, a generated route table and the coverage test.
- 4b. A server-side list contract (`filter`, `offset`, `limit`, `total`, `matching`), with `page_coverage` as the prototype. Four pages still filter in the
  browser: `solution.html:239` (the route has no paging), `compare.html:288`, `extraction.html:252` and `logs.html:143` (the `/logs` route already takes
  level and conversation). About 80 lines each, solution first.
- 4c. Plato routes with no PlatoClient method: `/database` (3), `/logs`, `/models/overlay` (2), `/packs/initialize`, `/packs/samples` (2), `/metrics`. Add
  methods or state they are UI-only. About 40 lines. The reverse check (a client method with no route) was not completed.
- 4d. Bigger idea B: a route-descriptor registry in the SDK (path, tenant scope, filters, paging, client method, page declared once; routes, client method
  list and a parity test derive from it). It would not generate client code or pages.
- 4e. Three copies of a one-entry tenant cache in `plato/wiring/default.py:412-435`; one small `GenerationCache` helper, about 40 lines.
- 4f. The JTBD export lint (K gates) is outside the stored lint-runs triage and the publish gate (`PUBLISH_BLOCKING` has no K code). Decide whether any K gate
  blocks; then include it in lint-runs. About 50 lines.

## 5. Decided not to absorb

- The KH cloner, project and membership copying, the macer rule sets and integrity check, the prepared-clone table and its claim and heartbeat machinery
  (service-side; the cloner itself says it is meant to be retired when KH supports entity filtering). No japes code shows a need.
- Candidates only, with no demonstrated need: a pure id-rewrite function; a layer-merge rule that treats an empty result as an error (japes
  `input_overrides.py` has no such guard).

## 6. Suggested order (for the user to rank)

1. 1a (15 lines), 3a (25 lines), the two legacy-key drop (40 lines): small, verified, symmetric.
2. The Plato guide stage 1 and 4b for the solution page.
3. 1b, 1c, 1e (the Kernel posture and mock parity), then 1d (the shared retry policy), then idea A as the umbrella.
4. Decisions needed first: tenancy model (string versus common's UUID), K gates in the publish path, the gateway and Flipt question (PR #108), PR #101's home
   for the workspace claim.

## 7. Platform service coverage (deferred, needs a product decision)

Question raised after the capability matrix: if Plato is to act as the whole platform, which platform services does japes not reach at all? client-api builds
a client for seven services (`repo_clients/`: assistant, kernel, keto, knowledge-hub, mlflow-async, notifications-hub, python-sandbox) and has none for
integration-hub. Checked by the coordinator: `pyproject.toml` takes only `kernel-client` (line 93) and `knowledge-hub-client` (line 95) from client-api.

| Service | client-api client | japes library client | Plato surface |
|---|---|---|---|
| Knowledge Hub | yes | yes (wrapper, mock, protocol, posture) | yes (documents, ontology, catalogs) |
| Kernel | yes | yes (wrapper, admin services, mock without a protocol) | partial (assistants page; no admin page) |
| Keto (authorization) | yes | referenced in `client_layer.py` and `safety/oidc.py` (not read; probably a role check, not a client) | none seen |
| python-sandbox | yes | none (no mention in `jazzx_sdk` or `plato`) | none |
| notifications-hub | yes | none (one word in `queue/processor.py`) | none |
| assistant (service) | yes | a reference in `eval_service_client.py` (not read) | assistants page (this is japes's own) |
| mlflow-async | yes | observability backend env only (`observability/backends/mlflow/env.py`) | logs and metrics pages |
| integration-hub | no (its `docs/openapi.json` exists; not in the expected shape) | none beyond Kernel's `integration` tool type | none |

Why japes does not need these today (the honest reading): (1) the project is consumer-driven, and no consumer has asked; juno and jaci reach integrations
through Kernel tools (Kernel has a `ToolType.integration`, mirrored in `kernel_admin_types.py:58` and listed by `tools/platform/discovery.py`), and
notifications are raised by services, not by pack authors. (2) Plato today is the authoring, review and understanding surface for packs, policy and
evaluation, not an operations console. Neither reason argues the services are unneeded: under a "Plato as the whole platform" aim they are the gap, and the
library layer reaches two of eight services.

To decide before any build: which platform operations an engineer should be able to do or inspect from Plato (configure integrations and webhook
endpoints, see incoming events and audit, manage notification rules and recipients, run a sandbox job, view authorization relations). Then the order per
service is the same three steps we already use for Knowledge Hub: a generated client in client-api, a japes wrapper with the strict-posture options and a
mock, and a Plato page driven by the route-descriptor idea (4d). Adding a service should be data (a small descriptor), not a new pattern each time; that is
idea A and idea B together.

To add integration-hub to client-api (deferred): integration-hub commits `integration-hub_openapi_schema.yaml` at its repo root (it has `docs/openapi.json`
and `scripts/generate_openapi.py`, but its vendored `common` lacks `core/client_api/generate_openapi_schema.py`), and client-api adds an `integration-hub`
entry to `REPOSITORIES` in `scripts/update_schema.py` and runs `scripts/update_schema.py --repo integration-hub` (needs a `GITHUB_TOKEN`) to download the
schema and generate `repo_clients/integration-hub-client`. Both are other teams' repos; we prepare patches and the user applies them.

### 7a. Integration Hub (read by a read-only agent; its `common/` submodule is empty in this checkout)

- Object model: incoming endpoint configs (handler type assistant, agent, tool or process; dedup and validator config; v1 and v2 routers) and incoming events
  (status and raw payload); outgoing endpoint configs (base URL, JSON actions, ten auth methods, draft or published, secret references) and outgoing events
  (request and response bodies stored through a redacting type); two integration templates (Postman, OpenAPI) with a stateless `validate-openapi` import;
  providers and provider users (token references); OAuth2 (PKCE); audit through version tables; secrets behind a provider interface (Azure Key Vault, AWS
  Secrets Manager, in-memory), the database holding references only.
- Consumers: juno has its own vendored, generated Integration Hub client (`api/rest/integration_hub/`, not from client-api) and ranks integrations
  client-side over the first 200 rows; kernel's `rest_api_with_integration_id_v2` triggers outbound calls by config UUID. This is a real consumer that already
  maintains its own client, which weakens "no consumer has asked" and favors a shared library client.
- Read-only candidates for Plato: list and get outgoing and incoming configs (secrets are masked or excluded in the read models), providers, provider users
  (references only), templates, audit history, and event metadata (omit `raw_payload`, which can hold borrower data). Stay in the service: all writes,
  `trigger-outbound-*`, `test-connection`, OAuth authorize and token, delete, import, sync, and `GET /templates/{id}/actions` (a read that triggers a lazy write).
- Proposed `IntegrationHubClient` (read-only): list and get for outgoing and incoming configs, incoming and outgoing events, providers, provider users, audit
  recent and history; list methods return `(rows, total)` from `X-Total-Count`; the same error model as `KnowledgeHubClient` (typed access, not-found,
  unavailable only with `raise_on_unavailable`); a mock with a protocol and parity test.
- Risks: the hub has no tenant concept, so every Plato read is global to the hub (a tenancy risk); the Kernel header allowlist excludes `x-user-*` as spoofable
  while the hub's reads and OAuth need `x-user-id` (a decision: KH-style versus Kernel-style forwarding); the catch-all middleware returns a bare 500; the
  generated client would carry duplicate schema names, free-form dict bodies, a trailing-slash route, two names for one path id and secret-bearing request
  models a wrapper must never expose; the README documents `body_template` and `transformations` fields that the models and `docs/openapi.json` do not have.
- Plato surface: GET routes under an `/integrations` prefix on the coverage list contract (`q`, `filter`, `offset`, `limit` returning `{rows, total,
  matching}`; `total` and `matching` need two hub queries), one page with a table, a detail drawer showing auth method, credential binding and references,
  and events and audit tabs.

### 7b. Notifications Hub

- Its design doc is stale; the model is in `app/`: an immutable `BackendEvent` (event type, entity type and id, source service, free-form action type, state
  payload, expiry, optional idempotency key); recipients are resolved from per-user subscriptions (no subscription means the event is dropped with a 200);
  each recipient gets an inbox row with read state; asynchronous events are stored and pushed, realtime events are pushed only; expiry defaults to 30 days.
  The `SourceService` enum has eight values (kernel, assistant, integration_hub, notifications_hub, frontend, knowledge_hub, builder_studio, juno) and no
  plato or japes value.
- Producers today: knowledge_hub (bulk-download and zip-upload status, realtime entity events) and juno (one event per finished chat run, failures swallowed).
  The consumer is the web client's bell; Plato consumes nothing.
- japes hook points: `EventEmitter.subscribe` exists in `events_domain.py` but nothing in `plato/wiring` builds one; `ChatSpec.on_complete` is a per-spec
  callback; `queue/processor.py` `_deliver_webhook` is a best-effort push that never fails a run. No emit points for review decisions, experiment completion
  or the publish gate; no posture or budget alert exists.
- Proposed `NotificationsHubClient`: `publish`, `inbox`, `unread_count`, `set_status`, `ensure_subscription`; tolerant `publish` that never raises (an outage
  must not fail a run), strict reads under `strict_mode()`; a mock and protocol. The hub needs five identity headers including `x-user-session-id`, which was
  not found in `identity.py`: check before building.
- Plato: consumer first (a read-only `/notifications` route and a nav badge or page) needs no hub change. Becoming a producer needs a `SourceService` value
  from the hub team (do not borrow another service's value) and one `EventEmitter` in `plato/wiring` mapping a few events to `publish`. Decide first whether a
  Plato user maps to a hub user UUID and session and who creates subscriptions. The latest dated schema in client-api (2026-06-29) may predate juno's use.

### 7c. Knowledge Hub changes since client-api's schema (2026-10-07)

KH's bulk entity delete (`POST /api/v1/reasoning/entities/bulk-delete`, async with a dry run, added 2026-09-21) is already in client-api's schema and generated
client, which japes pins (rev 767b3d6c); the japes wrapper has no bulk-delete method (it wraps the bulk download). Later KH changes are not in the generated
client: `GET /collections/llm-references/{llm_id}`, OR conditions and match-priority ranking in `POST /entities/filter`, synthetic-object marking (PAGI-2084),
a structured duplicate-collection-name error (BSD-4977), the assistant-scope delete (PAGI-2139), and JSON and JSONL parsing. From commit titles; which of them
change the OpenAPI schema was not checked. Regenerate with `scripts/update_schema.py --repo knowledge_hub` (needs `GITHUB_TOKEN`), then bump the pin.

## 8. Not verified

- Nothing was run. The reverse route check was noisy. Test pinning in the matrix was judged from file names and a few greps. The clone agent did not read
  the cloner body. The tenancy agent did not read common 0.4.0's dependency list, and no one examined knowledge_hub's pin. Guides outside `docs/*.md` and
  `plato/guide.md` were not searched.
