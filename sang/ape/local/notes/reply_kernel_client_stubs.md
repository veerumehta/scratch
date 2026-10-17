Thanks for flagging this, you're right.

**Does the SDK update the client stubs automatically?** No. The generated clients live in client-api. japes pins each one by git revision in its pyproject (kernel-client is pinned at the latest client-api revision, 1d0cc4ab). The SDK's wrapper code in `jazzx_sdk/clients/kernel_client.py` is hand-written against those models, and nothing regenerates or re-checks it when client-api changes.

**What's broken.** Four `KernelClient` methods still import model and API names the current client no longer has:
- `create_chat_completion` uses `LLMUserMessage`, `LLMMessageContent` and `LLMMessageContentType`; it should use `LLMUserMessageInput` and `LLMMessageTextContent`. It also sends every message as a user message, assistant turns included. That's a second bug we're fixing at the same time.
- `call_tool`, `list_tools` and `get_tool` import `kernel_client.api.tools` and `ToolCallRequest`, which are gone.

`invoke_agent` was already updated to the new names; these four were missed. Our unit tests mock the client, which is why none of this showed up.

**Fix.** It's on the `plato` branch now:
- `create_chat_completion` builds `LLMUserMessageInput` or `LLMAssistantMessageInput` from each message's role. System messages are merged into the request's system text.
- `temperature` and `max_tokens` are now actually sent. They were being dropped before.
- The pinned client has no tools API at all, so `call_tool`, `list_tools` and `get_tool` now raise `KernelToolsUnavailable`. Previously they silently returned empty results.
- A new contract test checks that every kernel-client name the SDK imports exists in the pinned client, and builds a real `ILLMChatRequest`, so a regenerated client can't silently break this again.

Pull the `plato` branch to pick it up.
