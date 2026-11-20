# Sibling survey 2026-11-17: knowledge_hub client gaps, macer and common

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Survey of the repos under `/Users/sangit/src` (`scripts/local/sister_repo_activity.sh --days 10`, KH full commit bodies read). Decides nothing; asks are listed at the end.

## 1. knowledge_hub: does `KnowledgeHubClient` need enhancing

KH spec: 115 paths (`knowledge_hub_openapi_schema.yaml`, tags: collections 33, reasoner 26, reasoning 21, mappings 19, registry 18, taxonomies 9, prompts 9, fs 7, global-config 5, audit 4, reasoning_v2 6, upload and zip_upload 4, tasks 2). Our client wraps collections (create, get, by-name, list, delete), documents (create v1 and v2, get, retrieve, list, content, metadata, search, update, delete, download v1/v2, bulk download), ontologies (CRUD), entities (v1 and v2 CRUD, filter, bulk delete, JSON path), run findings, triples, ontology-registry resolve. Everything else in the spec is unwrapped.

Demand signal = which sibling repos import the generated KH client directly (bypassing ours):

| Consumer | Direct generated-client use | Gap it points at |
|---|---|---|
| jazzx-assistant `clients/app_config.py` | `global_config.list_configs` through the raw client | global-config read (5 endpoints, none wrapped) |
| juno (17 raw uses, mostly `dataset_generation_tools.py`, `knowledge_tools.py`) | `list_documents`, `get_document_content`, `create_collection`, `create_ontology`, `create_entity`, `filter_entities`, `get_run_findings`, `upload_binary_document`, `global_config.list_configs`, with `*_detailed` responses | raw responses (status and headers); binary upload; global-config. Most of these EXIST on our client, so the reason is response shape, not coverage: ask juno why |
| kernel (reasoning_v2 and collections, 30+ sites) | `read_entities_summary_v2`, `read_entities_minimal_v2`, `update_entity_v2`, `update_entity_json_v2`, `rego.evaluate_policy` | v2 summary and minimal reads, v2 update; `rego` is not in the current KH spec (stale generated module or other service) |
| macer `e2e/hub.py` | `create_collection` via `client._raw_client`, because it needs `project_id` | our `create_collection` has no `project_id` (nor `metadata`/`scope`) |
| assistant, eval-service | collections and entity CRUD | covered |

New on the KH side this week (BSD-5766, 2026-11-17): `POST /collections/{id}/clone` takes an optional `{"name"}` (400 NAME_REQUIRED, 409 NAME_TAKEN), the 202 body carries id, name, technical_name, status; `GET /collections/clone/{task_id}`; `POST /reasoning/ontologies/{id}/clone` (new). BSD-5861 tenant migration (all 29 tables get `tenant_id`, RLS, tenant-leading keys; `PLATFORM_TENANT_ID` required at startup, tenant columns excluded from audit, findings and fs-export payloads): behavior-neutral for clients, no client change, but a KH deployment now refuses to start without `PLATFORM_TENANT_ID`, which matters for any mock or local-stack recipe we document. BSD-5668: a workspace can edit global config without changing Host.

Recommendation, in order of evidence:
1. Global-config read (`list_configs` by name, plus get/create/update): two consumers reach for it through the raw client; one is jazzx-assistant's own documented upstream ask.
2. `create_collection` gains `project_id` (and `scope` via `PATCH .../scope` if used), plus `update_collection`: macer needs it.
3. v2 entity `summary`, `minimal`, `update` and `update_json` (kernel); `entities/aggregate`.
4. Collection and ontology clone (with the new `name`): the Knowledge Studio / workbench seam will want it, no consumer yet: defer until one asks (do not generalize unhit problems).
5. Not now: mappings sets (19, K-Studio sets: only if the Acra comparison needs a mapping-set read), taxonomies, prompts, registry beyond resolve, reasoner runs and feedback (eval-service owns that domain), fs, audit, upload and zip-upload (v2 presigned: check whether our `create_document_v2` already covers the flow).
6. A response-shape option (`raw`/`detailed`) on the wrappers, if juno confirms that is why it bypasses us.

Symmetry: `KernelClient` got the public full-request invoke and tool-record methods in 2.7.4 for the same reason (assistant PR 269 reached through `_raw_client`); the KH client is the sibling with the same pattern in four repos. Both clients' `with_headers` use should be checked for the shared-client mutation found in the assistant review (the generated `with_headers` updates the shared httpx client in place).

## 2. macer and `common`

macer imports `common` only for `common.core.ai_gateway` (7 files): `AIGatewaySettings`, `use_ai_gateway` / `ause_ai_gateway` (the Flipt flag decision), `api_key`, `openai_base_url`. Sites: `agents/__init__.py` (route decision and client factory), `jtbd/condition_dedup/embedding.py` (embedding `api_base`), `runtime/ai_gateway.py` (settings built from macer's config). macer vendors `common` as a submodule at e5f29d9 (common PR 268, v0.5.0).

japes already carries the same route: `jazzx_sdk/llm/gateway/` (`route.py`, `common.py` over the same `common.core.ai_gateway`, `anthropic_chat.py`: Claude on the gateway through OpenAI Chat Completions with the same `cache_control` breakpoints and thinking fields) and `providers/anthropic_gateway.py`. macer's `models/anthropic_gateway.py` (`GatewayAnthropicModel`) is a parallel implementation of the same thing, written at the same time (macer 73918d1e, Nov 9).

macer pins japes at 64d9099e (v2.4.9, 2026-09-03) and imports two SDK modules (`jazzx_sdk.queue_processor` and the top-level package). So the duplication is not a conflict with a current japes, it is a consumer far behind it.

Where macer can use japes instead of its own code (each needs macer on a current japes first):
- **Gateway route and flag decision**: use `jazzx_sdk.llm.gateway` (route decision, client factory) rather than calling `common.core.ai_gateway` directly; removes `runtime/ai_gateway.py` and the direct `common` dependency from `agents/__init__.py`. Embeddings: confirm our route covers the embeddings `api_base` (macer keeps LiteLLM for embeddings with `{host}/v1`); if not, that is an SDK ask.
- **Claude on the gateway**: `models/anthropic_gateway.py` versus `jazzx_sdk.llm.gateway.anthropic_chat`; diff the two for what macer has that we lack (thinking-block replay on tool turns, verbosity drop) and absorb it into japes instead of keeping two copies.
- **Pricing and cost**: macer commits 6a419482 (long-context tiers, per-request pricing, per-span `cost_usd` in MLflow, unrounded cost), 4e041450 (Claude model prices, no dash normalization), 0e51a36d. japes already has `LongContextPricing` (`llm/cost.py`), 17 long-context entries in `model_data.json`, `cost_tracker.py` and the per-span path. The 2.7.4 queue item "cost rounding in the MLflow span" is the same concern as macer's "unrounded cost". macer's `utils/cost.py` should become japes' `ModelCard` pricing (one json edit, shared model list).
- **Fireworks provider**: macer 47473a32 adds `models/fireworks.py` (176 lines, 322 lines of tests). japes has no Fireworks provider and it is on the 2.7.4 queue: absorb macer's as the starting point instead of building a second one (improve, do not copy: our provider seam in `llm/providers/`).
- **KH**: macer's `e2e/hub.py` raw `create_collection` (see section 1).

Not for macer: `common` things japes does not wrap (db session, tenancy, middleware) are not imported by macer today.

## 3. Other repos (activity only)

- juno (BSD-6052 role cards, J1.5 plan locking, common v0.5.0 gateway flag), eval-service (process overrides, AI gateway through `common.core.ai_gateway`, six-execution cap), kernel (BSD-5632 discard workspace, AI gateway for Claude, rate-limit retry port), client-api (kernel client regenerated 11-06, automate-regeneration PR 76), jazzx-assistant (installs japes' gateway route at startup, pins japes `main`), assistant (PR 269 reviewed separately; sends japes-valid `jazzx_context` on queued invocations).
- Every Python consumer except macer already goes through the gateway via `common.core.ai_gateway`; four of them (juno, eval-service, kernel, macer) wired it by hand in the same week, which is the argument for one SDK entry point.

## 4. Asks

- sonnet-runtime (after 2.7.4 lands): KH client: global-config read and write, `create_collection(project_id=...)`, `update_collection`, v2 summary/minimal/update reads; check `with_headers` use in both clients; confirm the gateway route covers embeddings.
- sonnet-runtime: Fireworks provider from macer's code; cost rounding; long-context pricing parity check against macer's table.
- Roberto and macer owners (user to ask): why juno uses `*_detailed` raw calls; move macer to a current japes before the gateway cleanup.
- User: whether to open a macer adoption thread now or after 2.7.4.
