# Bringing more of the SDK into juno

**Status:** proposed, 2026-10-30. Read against japes `2a2098f5` (branch `v2.6.8`) and juno `main` (local checkout; the user's local
`JAPES_V2` branch is off main, unpushed). Plan only: no juno edit, no spend, no push. Author: sonnet-runtime, for opus-xrepo and the user.
Earlier decision U6 (`plan_models_prompts_crossrepo.md`: leave juno alone) is superseded by the user's new willingness; nothing here changes
juno without the juno team agreeing.

## Principles (as for the policy-workbench host)
Tiered and additive: each step ships alone and leaves juno no worse off. A named consumer comes first, and SDK features stay
consumer-neutral (no juno names in the SDK). Logic lives in the SDK, the host supplies tenant, gates and pin. Anything marked
"not verified" below was not run or measured.

## 1. What juno does today (read-only, juno main)

| Area | Evidence |
|---|---|
| SDK use | One import: `app/core/jazzx_clients.py:12` (`ClientLayer`), plus `tests/core/test_jazzx_clients.py:8`. A lazy singleton, Knowledge Hub only; refuses to build without a URL (`:34-44`) |
| Pin | `pyproject.toml:60` `japes = { git = ..., branch = "main" }`; `poetry.lock` resolves japes `1.4.5` at `8a32e45e` (`poetry.lock:2178-2224`). The SDK is now 2.6.8, so juno is a major version behind (see section 4) |
| Auth and headers | `ClientLayer(knowledge_hub_url=..., request_headers_provider=get_request_headers)` (`jazzx_clients.py:56`); `common/middleware/context_headers.py:18` whitelists `x-user-` and `x-request-`; no bearer token |
| KH access | Through the layer: `get_jazzx_clients().knowledge_hub` at about 20 sites (`skill_service.py:2714`, `navigation/finders.py:235`, `knowledge_tools.py` x11, `ontology_updates.py:128`, `dataset_generation_tools.py:1742,1754,2304`, `jazz_app_tools.py:823`). Methods used: `read_entity` (4), `read_ontology` (2), `get_document` (2), `read_ontologies`, `list_collections` (grep counts of `kh.` and `knowledge_hub.` calls; other KH traffic may use the generated client under `api/rest/knowledge_hub/`, not traced) |
| Models and prompts | OpenAI Agents SDK (`app/copilot/service.py:19-21`, `Runner.run` at `:1060`), model resolved through the MLflow gateway (`app/main.py:53-55`, `app/copilot/mlflow_gateway.py`); prompts are files under `app/copilot/profiles_data/*/prompt.md` and `skills_data/` |
| Eval skills | `app/copilot/skills/tool_defs/eval_tools.py`: generated eval-service clients (`:78-136`, `EVAL_SERVICE_API_URL` at `config.py:32`), plus local validation of testcases and custom scorers |
| Feedback analysis | `app/feedback_labeling/` (1,222 lines: `eval_client.py`, `service.py`, `schedule.py`, `executor.py`, `kh_config.py`); calls eval-service feedback and label endpoints through the generated client with a fixed service identity (`eval_client.py:1-40`). `app/harness_learning/` (`service.py`, `outbox.py`, `memory.py`, `policy.py`) is a second learning loop (not read in depth) |
| Memory | mem0 on pgvector in juno's own Postgres: `app/core/memory.py`, `app/copilot/memory_tools.py`, `app/harness_learning/memory.py`. Usage detail in `plan_memory_scoping_and_sdk_principles.md` ("What juno actually uses"): `add` and `search` only, scopes user UUID and `"system"` |
| Streaming and runs | FastAPI `StreamingResponse` with `text/event-stream` in `app/juno_tasks/stack_ops_api.py:445-470`; background work in `app/queue/`, `app/scheduler/`, `app/juno_tasks/` (`decider_loop.py`); no SDK `runs/` use |
| Tracing | Custom `MLflowTracingProcessor` for the Agents SDK (`app/copilot/mlflow_trace_processor.py`), `cost_hooks.py`; `set_tracing_disabled` in `service.py` |
| Guardrails | `app/copilot/guardrails/` (`input_guards.py` 263 lines, `output_guards.py` 462, `bypass.py`), own implementation |

## 2. SDK equivalents, gaps, gains

| Area | SDK today (verified present in code) | Missing, would be SDK work | Juno gains |
|---|---|---|---|
| KH access | `ClientLayer.fabric` (`client_layer.py:473`) returns a `KnowledgeFabric`. Fabric has no `fabric.kh` verb set of its own; `fabric.kh` is the raw client for "non-semantic" operations (`fabric/fabric.py:245`). Equivalents (checked by `tests/test_fabric_kh_parity.py`, `be6be1be`; the first four match the raw call, `docs.get` does not): `read_entity` is `fabric.entities.get` (`entities/store.py:182`); `read_ontology` is `fabric.graph.get_ontology` (`graph/store.py:400`); `read_ontologies` is `fabric.graph.list_ontologies` (`:422`); `list_collections` is `fabric.collections.list` (`collections/store.py:24`); `get_document` has no drop-in: `fabric.docs.get` (`docs/store.py:567`) raises on a missing document where the raw call answers `None`, and follows the retrieval mode (a LOCAL fabric never asks the hub). Graph reads wrap a transport failure in `KnowledgeFabricError` | Parity is measured for the four matching calls. Juno checks `is None` at `knowledge_tools.py:277`, `dataset_generation_tools.py:2324` and the entity and ontology reads, so for `get_document` it keeps `fabric.kh.get_document`; an SDK hub-read-by-id that answers `None` is optional | Typed stores, the mock-backed `local_fabric` for tests (replaces juno's mocks of the raw client), one place for retries and access errors (`KnowledgeHubAccessError`) |
| Pin and version | `jazzx_sdk._version` 2.6.8; contract tests exist in japes | Nothing in the SDK; a juno-side floor and lock | Reproducible installs |
| Models and prompts | `jazzx_sdk/llm` (model cards, routing, cost tracker, structured calls), `jazzx_sdk/prompts` (loader, compose, sync, ref), `agents/openai_provider.py` | A way to resolve a model through an external gateway as one provider (the MLflow gateway today). Not verified whether `llm/providers/` already takes a base URL for an OpenAI-compatible gateway | Model cards and pricing in one json, prompt refs with provenance, per-turn cost (`llm/turn_cost.py`) |
| Eval skills | `evaluation/` (datasets, experiments, custom scorers, optimization, reclaim, dbs), the SDK eval control plane (`plan_sdk_eval_control_plane.md`), `clients/eval_service_client.py` (feedback config, static feedback, `find_similar` only) | An SDK client for the eval-service operations juno calls today (datasets, testcases, experiments, scorers). Not in `eval_service_client.py`. Decide against the control plane: the SDK owns this logic, so the better path may be the control plane, not a new REST wrapper | Drops the generated client and the duplicate validation in `eval_tools.py` |
| Feedback analysis | `evaluation/feedback/` (records, processing, retrieval, learning, sink, quality), `plan_feedback_service.md`, Plato hosts the service | Labeling schedule and RCA run input (`feedback_labeling/schedule.py`, `service.py`) have no SDK twin that I verified | One feedback store and one learning loop instead of two |
| Memory | `agents/interactive/memory.py` (conversation stores and compaction, not a vector memory); no mem0 anywhere in the SDK (grep of `jazzx_sdk` finds no `mem0`) | The memory plane in `plan_memory_scoping_and_sdk_principles.md`. Moving juno is a behavior change (LLM-invoked `save_memory` writes active shared memory without approval) | Scoped, approvable memory. High risk, last |
| Streaming and runs | `runs/` (store, runner, worker, chat), `streaming/` (publisher, SSE reader, platform codec) | Not verified that `runs/` fits `juno_tasks` jobs; juno's decider loop is its own design | Durable run records, one SSE codec |
| Tracing | `observability/` (`agents_tracing.py`, `run_tracer.py`, `backends/`), `evaluation/backends/mlflow/` | Whether the SDK's Agents-SDK tracing replaces `MLflowTracingProcessor` one for one: not verified | Trace ids tied to runs and spend |
| Guardrails | `agents/interactive/guardrail_kinds.py`, `safety.py`, `safety/` (net, paths, sanitize, odata) | Not compared with `input_guards.py` and `output_guards.py` (rules not read in depth) | Shared kinds; low priority |
| Auth and headers | `ClientLayer(request_headers_provider=...)` already used; `clients/_header_hooks.py` | Nothing | Already adopted |

## 3. Ordered plan (smallest first; each step is its own PR on `JAPES_V2`, and each stops cleanly)

| # | Step | Owner | Tests | Risk | Stop point |
|---|---|---|---|---|---|
| 0 | Agreement: the user and the juno team accept the approach and the pin policy (section 4). No code | user | none | none | juno unchanged |
| 1 | **Pin and lock.** Replace `branch = "main"` by a `>=` floor on a released SDK version, regenerate the lock, run juno's suite. Includes the 1.4.5 to 2.6.x jump | juno PR | juno full suite; the one SDK-touching test file; a smoke of `get_jazzx_clients()` against a mock KH | Medium: a major jump, breaking changes not enumerated (not verified). Mitigate by reading the SDK CHANGELOG for 1.4.5 to 2.6.8 first | Juno on a known SDK; nothing else changed |
| 2 | **KH access through the fabric surface.** One adapter module in juno exposing the five calls (`entities.get`, `graph.get_ontology`, `graph.list_ontologies`, `collections.list`, `docs.get`) over `get_jazzx_clients().fabric`; move the call sites one file at a time | SDK for any parity fix; juno PR for call sites | Parity already pinned in japes for four calls; add juno-side tests that the wrapped errors and `None` handling still behave; `local_fabric` for the tool tests; one test that fails if a call site still touches `.knowledge_hub` | Low to medium: shapes may differ per store (not verified); `docs.get` v1 fallback | Any prefix of call sites is fine; the raw client stays for the rest |
| 2a | **OData literal escaping.** Juno builds `name eq '<value>'` filters by interpolation at 8 sites with four local escape idioms (`skill_service.py:2651` via `_escape_odata_string`, `component_clone.py:1647`, `shared_tools.py:539,905,993,1314`, `integration_tools.py:139`, `ontology_updates.py:190`); `shared_tools.py:1314` shows no escape at the site (the value may be validated earlier: not checked). Replace them with `jazzx_sdk.safety.odata.escape_odata_literal` (`'` becomes `''`). Not `app/core/odata.py`: that is a case-insensitive OData-to-SQLAlchemy visitor, unrelated | juno PR | one test per site: a value with a quote stays inside the literal; fails on a site that still interpolates raw | Low | Any subset of sites |
| 2b | **Text sanitizing before storage** (`safety.sanitize.strip_nulls`). Not verified that juno ever stores NUL characters in Postgres text; do it only if a real case exists | juno PR | a NUL in a stored field | Low | Skip if no case |
| 2c | **URL check: swap once on the new predicate.** The SDK now has `safety.net.is_blocked_literal_host` (`e4a9fd10`, no DNS, tests forbid a resolver). It covers every case in juno's `_is_private_host` and is stricter on reserved, multicast and unspecified ranges, so the swap tightens slightly. Original finding: Juno's webhook validator (`app/copilot/runs/schemas.py:22-70`) deliberately resolves no DNS (the comment names the event-loop block and the rebinding limit); the SDK's `validate_url_safe` resolves with blocking `socket.gethostbyname` and fails closed on unresolvable hosts, so adopting it changes behavior. Keep juno's `_BLOCKED_HOSTNAMES` via the `blocked_names` argument | juno PR | juno's existing webhook cases, plus one reserved-range case | Low | Stay on juno's own |
| 3 | **Test seam.** Replace juno's KH mocks with `local_fabric` | juno PR | the existing tests, unchanged in intent | Low | Stop here for a minimal adoption |
| 4 | **Model and cost.** Read model cards and turn cost from `jazzx_sdk/llm` beside the gateway, no routing change (additive; the gateway stays the route) | SDK (gateway provider question) then juno | cost parity on recorded turns | Medium; needs the gateway answer | Juno keeps its gateway |
| 5 | **Eval skills onto the SDK control plane**, behind a flag; the generated client stays as the fallback | SDK (client or control plane surface) then juno | contract tests with `jazzx_eval_contracts`; one old-code-fails test per validation moved | Medium to high: tenant and pin supplied by the host | Flag off means today's path |
| 6 | **Feedback labeling onto the SDK feedback service** (Plato-hosted) | SDK then juno | replay of recorded feedback rows through both paths | Medium | Flag off |
| 7 | **Tracing and runs**, only if 4 to 6 land and the juno team asks | SDK then juno | trace parity | Medium | Skip |
| 8 | **Memory plane** (decision in `plan_memory_scoping_and_sdk_principles.md` first) | SDK then juno | behavior tests for approval and scope | High: a behavior change | Do not start without an explicit decision |

SDK work in steps 2, 4, 5, 6 follows the usual flow here (plan, tests that fail on old code, CHANGELOG, no juno name in code or docs).
Steps 1 to 3 need no SDK release beyond a tagged version.

## SDK work that would ease the move (consumer-neutral)
1. **Installable from git without local paths.** `jazzx-eval-contracts` and `jazzx-plato-client` are path dependencies (`pyproject.toml:101-102`), so a git consumer's lock fails (`Path .../jazzx_eval_contracts does not exist`). The user chose git subdirectory dependencies, decision deferred; Plato's Dockerfile (`:47-103`), `import-boundaries.yml:44` and the editable dev loop all change with it.
2. **Light core install.** Measured with both packages blocked: `client_layer`, `fabric`, `llm`, `prompts`, `observability`, `safety`, `streaming`, `agents`, `tools`, `concurrency`, `skills`, `mcp` and `clients.eval_service_client` import; `runs` and `pack` need plato-client, `evaluation`, `evaluation.feedback` and `fabric.guidance` need eval contracts. Optional extras (`eval`, `plato`) would let a host install only what it uses; Poetry still locks optional path deps, so this follows item 1.
3. **Done (`e4a9fd10`): a no-DNS literal-host predicate in `safety.net`** (loopback, link-local, private literals plus a named blocklist), async-safe, for validating a URL a host will store and call later. The existing `is_private_ip` resolves synchronously and is advisory (its own TODO names the rebinding gap).
4. **Done for four calls (`be6be1be`): fabric parity with the raw KH calls** juno uses. `get_document` is a pinned difference; decide whether the SDK adds a hub-read-by-id that answers `None`.
5. **An external-gateway model route** (OpenAI-compatible base URL as a provider), only if the SDK lacks one (not verified); decides plan step 4.
6. **A release tag per version** (japes has no `v2.6.x` tag), so a host can pin by tag.
7. Direction the other way, to consider: juno's case-insensitive OData-to-SQLAlchemy visitor (`app/core/odata.py`) is a pattern the SDK has not been shown to have (not searched).

## 4. The pin question
Juno tracks `main` unpinned; its lock already sits at `1.4.5` (`8a32e45e`), so the "tracking" is really a stale lock. Propose
`japes = { git = "...", tag = "v2.6.x" }` as the lock source with a `>=` floor in the stated constraint, per our dependency policy
(floors, never `^` or caps; update the lock to take a release). Poetry accepts `rev` or `tag` for git dependencies; the floor and the
tag together need checking against juno's Poetry version (not verified). The tag must exist on the remote before the juno PR, and the user
creates it (never us). Whether a git dependency stays or the SDK is published to an index is the user's call (question 3).

## 5. Open questions for the user
1. Does the juno team agree to step 0 and a PR from `JAPES_V2`? Who reviews on their side?
2. Is the 1.4.5 to 2.6.x jump acceptable in one PR, or should juno first move to an intermediate release?
3. Git tag or an index for the pin? Which released version is the floor (2.6.7 is pushed; 2.6.8 is in progress)?
4. Gateway: must the MLflow gateway stay the only model route? That decides step 4's SDK work.
5. Eval: juno's skills call eval-service directly today. Do they move to the SDK control plane (step 5) or stay on eval-service REST?
6. Memory: stay on mem0 indefinitely, or take the behavior change in step 8?
7. `app/harness_learning/` runs a second learning loop beside feedback labeling: keep, merge into the SDK, or out of scope?
8. Juno's `common` is a submodule with local changes (`git status` shows `M common`): does any step touch it?

## Not verified
Argument and return parity of the five fabric calls against the raw KH calls; whether a gateway base URL is supported by the SDK
providers; juno's other KH traffic via `api/rest/knowledge_hub/`; breaking changes between 1.4.5 and 2.6.8; guardrail rule parity;
`harness_learning` internals; juno's Poetry version.
