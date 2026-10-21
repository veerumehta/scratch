# Kernel administration facade on KernelClient (sonnet-runtime, 2026-10-20)

Ask: the assistant team's option 2, a thin SDK facade over the generated kernel-client's admin calls, so a consumer never
imports `kernel_client.models`. Plan first; nothing built; no version bump; folds into 2.6.5 after slice 1.

## Verified at HEAD (installed pin `1d0cc4ab`)

- Present in `kernel_client.api`: agents `list_agents(skip=0, limit=100, query, orderby, order_direction)`, `get_agent_by_id`,
  `search_agent_by_name(name)`, `create_agent(body)`, `update_agent`, `delete_agent`, `upload_agent_config(body)`,
  `download_agent_config(agent_id)`, and **tools live under `api.agents`**, not a separate package: `list_tools` (same paging),
  `search_tool_by_name`, `get_tool_by_id`, `create_tool`, `delete_tool`, `upload_tool_config`, `download_tool_config`,
  `test_run_kernel_tool`; llm `list_llms(include_deleted)` (not paged), `create_llm`, `update_llm(llm_id, body)`,
  `get_llm_by_id`; notepads `list_notepads(creator_id, creator_source, tag, ...)`, `create_notepad`, `get_notepad_by_id`.
  All 13 named models are exported from `kernel_client.models`.
- `KernelClient` (`jazzx_sdk/clients/kernel_client.py`) holds `_raw_client` and already wraps `search_agent_by_name`
  (`get_agent`, `_agent_id`) but none of the admin calls. `NO_TOOLS_API` / `KernelToolsUnavailable` (lines 26-38, 134-146) is
  stale for list/get: the tools endpoints exist. `call_tool` has no endpoint (only `test_run_kernel_tool`, a dry run), so the
  message is narrowed to calling, not listing or reading.
- The invoke side already has the pattern: `kernel_invoke.py` holds SDK types (`AgentOverrides`, `ReasoningEffort`,
  `TextVerbosity`) and a test holds `request_wire` equal to the generated model. The facade reuses `ReasoningEffort` and
  `TextVerbosity` from there (no second enum).
- Generated calls return `Response` objects (status, parsed) and `asyncio()` helpers; the generated client does not raise for
  a 4xx unless asked. The assistant repo's own client raises `ServiceException`; that is the behavior to map, not copy.

## Design

One module for the types and services: `jazzx_sdk/clients/kernel_admin.py` (types and wire mapping in
`kernel_admin_types.py` if it grows past ~400 lines).

1. **Types, SDK-owned.** Writes: `AgentSpec` (the `AgentCreate` fields; `type_: AgentType`, `llm_id`, `tools`,
   `callable_agent_ids`, `mcp_servers`, `reasoning_effort`, `text_verbosity`, schemas, extra metadata), `ToolSpec`,
   `LlmSpec`, `LlmUpdate`, `NotepadSpec`, `AgentConfigOverrides` (the upload-side overrides), `ConfigUpload` (the
   `BodyUploadAgentConfig` file). Enums: `AgentType`, `ToolType`, `CreatorSource` as SDK enums whose values come from the
   generated enums (a test builds the SDK enum from the generated one's values and asserts equal member sets, so a client upgrade
   that adds a value fails there, not in a consumer). Reads: `KernelAgent`, `KernelTool`, `KernelLlm`, `Notepad` as pydantic models
   with `extra="allow"` over `to_dict()` of the generated read model (the ids, names and the fields consumers read are typed; the
   rest is kept, so a server field never breaks a consumer). Each write type has `wire()` (the JSON kernel receives), written here;
   a test holds `wire()` equal to `generated_model.to_dict()` for every type, as `kernel_invoke` does.
2. **Services** on `KernelClient`: `.agents` (`list`, `iter`, `get`, `find` by name, `create`, `update`, `delete`), `.tools`
   (`list`, `iter`, `find`, `get`, `create`, `delete`), `.llms` (`list`, `get`, `create`, `update`), `.notepads` (`list`,
   `get`, `create`), `.config` (`upload_agent_config`, `download_agent_config`, `upload_tool_config`,
   `download_tool_config`), `.chat` (a namespace over the existing `create_chat_completion`, no new behavior). Each service is
   a small class taking the raw client; the properties build them lazily. Update/delete beyond the ask are included only where the
   generated call is one line and the assistant repo needs the family (agents update/delete are not in the ask; leave them out
   until used: "ask" list only, plus `get`, which the lists need for symmetry).
3. **Pagination.** `list_agents` and `list_tools` page by `skip`/`limit`: `iter_agents(page_size=PAGE_SIZE)` is an async iterator
   that stops on a short page (named constant, default 100 = kernel's own default; the assistant's `limit=500` is passed as
   `page_size`), `list_agents(limit=None)` collects all pages (tolerant: a page error after some pages raises, it does not return a
   partial list silently). `list_llms` has no paging; `list_notepads` filters (`creator_id`, `creator_source`, `tag`), no skip.
4. **Errors.** One small family in `kernel_admin.py`: `KernelAdminError(RuntimeError)` with `status` and the server's detail;
   `KernelNotFound` (404, and an empty search), `KernelRejected` (422 with kernel's validation text, 400 with the
   upload-config failure text the assistant's promotion code parses today), `KernelUnavailable` (connection errors, 5xx). `find`
   by name returns None on 404 (what `get_agent` does today); everything else raises. This is a raise contract like the rest of
   `KernelClient`; `ToolResult.from_call` still wraps it for a caller that wants an envelope.
5. **Stub.** `jazzx_sdk/clients/kernel_stub.py`: `StubKernel` implements the same service protocols in memory (ids by uuid,
   name uniqueness, paging by skip/limit, upload-config upsert by name, scripted failures `fail_next(op, status)`). Production
   shape: its read types are the SDK read models, its errors the same family, `download_agent_config` returns bytes.
   Tests for the real services run against `httpx.MockTransport` through the generated client (so the generated request and
   response shapes are exercised), and the stub is held to the same contract tests as the real services (one parametrised suite).
6. **ClientLayer.** No wiring change: `ClientLayer.kernel` already returns a `KernelClient`; `layer.kernel.agents.find(name)`
   works. A `Protocol` per service (`AgentsAdmin`, ...) so a consumer types against the protocol and a stub drops in.
7. **LLMService.** `jazzx_sdk.llm` (`LLMManager`, model cards, overlays) calls models and does not register them in Kernel;
   there is nothing to absorb. The facade's `llms` service is only Kernel's registry (create/update/list of Kernel LLM
   records). The module docstring and the adoption note say so, one sentence each way.
8. **Tools message.** `list_tools`/`get_tool` on `KernelClient` become real (delegating to `.tools`) and return the same dict
   shape as today's signature (`list[dict]`, `dict | None`); `call_tool` keeps raising `KernelToolsUnavailable`
   with a narrowed message ("there is no endpoint that calls a tool; `test_run_kernel_tool` is a dry run"). The
   `call_parallel`/MCP paths that catch `KernelToolsUnavailable` are re-checked (grep first).

## Adoption note (one page, in the SDK docs)

`docs/KERNEL_ADMIN.md`: a table from the assistant repo's calls to the facade, taken from `app/utils.py` and
`app/assistant/promotion.py`: `client.llm.list_llms()` -> `kernel.llms.list()`; `client.llm.create_llm(ILLMCreate)` ->
`kernel.llms.create(LlmSpec)`; `update_llm(id, ILLMUpdate)` -> `kernel.llms.update(id, LlmUpdate)`; `client.agent.list_tools()`
-> `kernel.tools.list()`; `create_tool` -> `kernel.tools.create(ToolSpec)`; `list_agents(skip=0, limit=500)` ->
`kernel.agents.list()` (or `iter(page_size=500)`); `search_agent_by_name` -> `kernel.agents.find(name)`; `create_agent` ->
`kernel.agents.create(AgentSpec)`; `upload_agent_config` / `download_agent_config_with_http_info` ->
`kernel.config.upload_agent_config(file, overrides=...)` / `download_agent_config(id)`; `ServiceException` ->
`KernelAdminError` and its subclasses (what the upload-config text parsing in `promotion.py` reads moves to
`KernelRejected.detail`). Where their code reads a generated read model's attribute, the SDK read model carries it (typed) or it
is in `.extra`. Import-order and Pydantic-vs-attrs differences (they use attrs models with `UNSET`; ours omit unset fields) are
listed.

## Order and effort

1. Types and wire mapping with the `wire()`-equals-generated and enum-equality tests (M).
2. Services: agents, tools, config, with MockTransport tests against the generated client and the pagination rules (M).
3. llms, notepads, `.chat` namespace, error family (S-M).
4. Stub and the shared contract suite (S-M). 5. Tools-message narrowing on `KernelClient` and its callers (S).
6. Adoption note, CHANGELOG, README line (S). Total M-L, about five commits; all additive, no consumer changes in japes.
Risks: the generated read models are attrs with `UNSET` and nested optional types, so the read mapping is where defects will
be (each read model gets a round-trip test from a real-shaped payload); `upload_agent_config` takes a multipart file, which
needs one MockTransport test with a real body; paging is verified by test only, since there is no Kernel to call here.

## Addendum 2026-10-20: kernel config-upload now rejects, and the pinned client against the current OpenAPI

- Kernel commit `bd65ac42` makes `upload_agent_config` reject an agent whose LLM names an unavailable model, where it skipped it.
  Facade: it surfaces as `KernelRejected` with the server's detail text unchanged (the assistant's promotion code parses that
  text). Adoption note: say so, and that an upload that used to succeed with a skip can now fail. `StubKernel` contract suite: a
  stub upload of an agent whose LLM names an unavailable model must reject with that text; the real-service test feeds a 4xx with
  that body through `MockTransport` and asserts `KernelRejected.detail` equals it byte for byte.
- Pin check (read-only, pin untouched): compared every route of the pinned client (`1d0cc4ab`) with the current
  `kernel_openapi_schema.yaml` (kernel `12ab013a`, 2026-10-19) by method and path. All 14 admin routes in the facade's scope
  (list/get/search/create agent, upload/download agent config, list/search/create tool, list/create/update llm, list/create
  notepad) exist unchanged in both. Gone from the current spec, so a call through the pinned client would 404: the `/collections`
  routes (KH proxy removal) and the agent/step feedback routes (`/agents/feedback/*`, `/agent-invocations/{id}/feedback`,
  `/steps/{id}/feedback`); none is in the facade's scope. New in the spec and absent from the pinned client:
  `PATCH /agents/tools/{id}` (update tool), also outside the ask. Not checked: request and response body shapes (a field
  rename would not show in a route comparison); the real-shaped round-trip tests in the facade plan are what catch that.
  Conclusion: the pinned client serves the facade as scoped; a newer client-api rev is needed only to call update-tool or if body
  shapes changed, which a rev bump plus the wire-equality tests would show. The pin stays; changing it is the user's call.

## Findings while building step 1 (2026-10-20)

- `BodyUploadAgentConfig.file` is a `str` in the pinned client (the schema's `contentMediaType` was not mapped to a file), and its
  `to_multipart()` sends `str(file)` as a text field with no filename. Kernel expects a real file part, which the assistant's own
  client sends. The facade therefore does not use the generated body for an upload: `ConfigUpload(filename, content)` builds the
  file part and the service posts it through the raw httpx client (step 2); a test asserts the multipart body carries a filename and the
  exact bytes.
- `AgentConfigOverrides` is the invocation's `agent_config_overrides`, not an upload parameter. The SDK already has it as
  `kernel_invoke.AgentOverrides`; `kernel_admin_types.AgentConfigOverrides` is that type, so the name the assistant team lists exists
  without a second class.
