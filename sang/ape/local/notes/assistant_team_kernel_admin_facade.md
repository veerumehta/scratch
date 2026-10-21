Kernel administration through the SDK: what to use instead of bringing the v1 services over

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

You asked for AgentService, ToolService, LLMService, NotepadService and AgentConfigService, and the public model
types. The SDK now has these on `KernelClient`, one namespace per service, over the same generated Kernel client the
assistant already depends on. Nothing from v1 needs to come across.

What exists (all on the SDK's v2.6.5 branch, shipping in the next plato release):

  kernel.agents    list(page_size=, limit=), iter(), get(id), find(name), create(AgentSpec)
  kernel.tools     list, iter, get(id), find(name), create(ToolSpec)
  kernel.llms      list, get(id), create(LlmSpec), update(id, LlmUpdate)
  kernel.notepads  list(creator_id=, creator_source=, tag=), get(id), create(NotepadSpec)
  kernel.config    upload_agent_config(ConfigUpload(filename, content)), download_agent_config(agent_id) -> bytes
  kernel.chat      completion(llm_id, system, messages, ...)

Model types are in `jazzx_sdk.clients.kernel_admin_types`: AgentSpec, ToolSpec, LlmSpec, LlmUpdate, NotepadSpec,
ConfigUpload, the read records (KernelAgent, KernelTool, KernelLlm, Notepad), and the enums AgentType, ToolType,
CreatorSource, AgentAutonomy, LearningStrategy. ReasoningEffort, TextVerbosity and AgentConfigOverrides are re-exported
(AgentConfigOverrides is the invocation's override type, not an upload parameter). Errors are one family:
KernelNotFound, KernelRejected (400, 409, 422; the server's text unchanged in `.detail`), KernelUnavailable (5xx or a
failed connection, the retryable class) and KernelAdminError for the rest.

Your two call sites map directly: `app/utils.py` (LLM, tool and agent bootstrap) and `app/assistant/promotion.py`
(search by name, upload and download of agent config). The one-page mapping from your generated-client calls to the
facade, with the differences to expect, is `docs/KERNEL_ADMIN.md` in the SDK.

Four things to know before you adopt it:

1. `kernel.llms` is Kernel's registry of LLM records, the same thing your bootstrap writes today. It is not how a model
   is called. The SDK equivalent for calling models is `jazzx_sdk.llm` (LLMManager, model cards, overlays); it
   registers nothing in Kernel.
2. Uploading agent config: the pinned generated `BodyUploadAgentConfig` sends the file as a text field with no
   filename. The facade sends a real file part. Do not use the generated body.
3. Kernel changed on 2026-10-19: `upload_agent_config` now rejects an agent whose LLM names an unavailable model,
   where it used to skip it. It surfaces as KernelRejected with Kernel's wording unchanged, so code that parses the
   refusal text keeps working, but a bundle that was silently partly applied before will now be refused whole.
4. The tools API on Kernel can list, read and create tools; there is no endpoint to call a tool. `call_tool` keeps
   raising a clear error. Call the tool's agent, or an MCP server.

For tests, `StubKernel` has the same public signatures as the real services (held equal by a contract test), can mark
models unavailable the way Kernel now does, and can fail the next call.

When: it ships with the next plato push (the v2.6.5 squash). Until then it is readable on the SDK branch. Tell us which
calls you hit first and we will make sure those are covered by a test against a payload shaped like Kernel's.
