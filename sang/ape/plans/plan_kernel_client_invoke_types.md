# KernelClient.invoke_agent with SDK-owned request types

Plan, sonnet-runtime, 2026-10-16, from opus-xrepo's request. Status: written, one decision for the user (section 5).
Goal: a consumer never imports `kernel_client.models`; the assistant team stops bypassing the SDK client.

## 1. What the consumer does today (assistant `chat_handler.py`, read)

- Builds `AgentInvocationRequest(agent_id, messages=<user and assistant turns>)`, optional `agent_config_overrides`
  (`AgentConfigOverrides.from_dict`), `hooks_config` (one `on_complete` webhook), `streaming` = `{"enabled": true}`,
  `parent_notepad_id`, and sends the project id as the `x-request-project-id` header.
- Calls the generated `invoke_agent` and keeps the returned invocation id. It does not poll: the result arrives by
  the webhook, or for streaming through the stream (below).

## 2. What kernel does (kernel source, read)

- `AgentInvocationRequest`: `agent_id`, `messages` (user, assistant, tool_call_result; content text, file or tool
  call request), `parent_notepad_id`, `streaming: dict` ("Expected: {"enabled": True/False}"), `hooks_config`,
  `agent_config_overrides`, `mlflow_context`.
- Hooks: `HookType.ON_COMPLETE` only; executor `WEBHOOK` only; `WebhookConfig` (url, method POST, headers,
  timeout 5 s, retries 3, backoff 5 s).
- Overrides (all optional): `agent_prompt`, `llm_id`, `temperature`, `reasoning_effort` (none, low, medium, high,
  xhigh), `text_verbosity` (low, medium, high), `max_steps`, `use_feedback`, `output_schema`, `tools`,
  `callable_agent_ids`, `mcp_servers`.
- Streaming: not SSE over the invoke call. Kernel publishes events to a Redis stream `invocation:{id}`
  (`common.core.streaming` events: delta, final_result, done, error); the generated client has no reader for it.
  The invoke call itself returns only the invocation id (HTTP 200). japes already reads that stream
  (`jazzx_sdk/streaming/sse_reader.py`).

## 3. Design (all SDK, no pack data)

New module `jazzx_sdk/clients/kernel_invoke.py`, our names, pydantic models:
- `AgentMessage(role: user|assistant|tool_result, text, tool_call_id?)` and `file`/`tool_call` content kept as small
  typed parts; `messages=` takes a list of them or plain `{"role","content"}` dicts.
- `AgentOverrides` (the fields above, `ReasoningEffort` and `TextVerbosity` enums of ours).
- `AgentHook(type=ON_COMPLETE, url, method, headers, timeout_seconds, retries, retry_backoff_seconds)`; executor
  fixed to webhook (the only one).
- `StreamingConfig(enabled=True)`; `parent_notepad_id`, `project_id` (sent as `x-request-project-id`).
- One mapping function to the generated models, inside the client; serialization ours (build the JSON body and post
  it with the generated client's httpx client, so a generated model's field rename cannot change what we send).
- `KernelClient.invoke_agent(agent_name, input_text, session_id=None, *, messages=None, overrides=None, hooks=None,
  streaming=None, parent_notepad_id=None, project_id=None, poll_*)`: existing signature unchanged; `messages`
  replaces `input_text` as history when given; `session_id` stays a documented no-op.
- `KernelClient.start_agent(...) -> invocation_id` (no polling; the assistant's pattern: hook or stream delivers the
  result). `invoke_agent` is `start_agent` plus the existing poll.
- Test against the generated models: build each SDK type, map it, and assert the generated model's `to_dict()` equals
  our JSON; plus a field-set test (every generated field has an SDK field or is named as left out), so a client bump
  that renames a field fails here.

## 4. Left out, and why

- Nothing of streaming: it is in scope, see section 5.
- `mlflow_context`, other hook types and executors: kernel has one of each; added when kernel adds one.

## 5. Decision for the user (recommendation first)

`jazzx_sdk/streaming/sse_reader.py` already reads the Redis stream `invocation:{id}` and yields frames
(`stream_invocation_sse`, over `common.core.redis_streams`, `streaming` extra), so the streaming variant is small:
`stream_agent(...)` starts the invocation with streaming enabled and yields that reader's events for the returned
id. Recommended: build it, with the Redis connection taken from the same settings the reader uses, and keep
`start_agent` for callers (the assistant today) that read the stream themselves. Say if the streaming variant
should wait: `start_agent` and the typed request cover everything the assistant calls now.

## 6. Built (sonnet-runtime, 2026-10-16, `v2.6.3`)

`jazzx_sdk/clients/kernel_invoke.py` (types, `request_wire`, `build_request`), `KernelClient.start_agent`,
`stream_agent` and the extended `invoke_agent`, re-exports in `jazzx_sdk.clients`, `MockKernelClient` updated;
`tests/test_kernel_invoke_types.py`. Deviation: the request is sent through the generated `invoke_agent` call built
from the mapped model (so the existing header and test path is unchanged); our JSON (`request_wire`) is what the
tests hold equal to the generated model's `to_dict()`. Streaming reads with `replay=True, tail=True`.
