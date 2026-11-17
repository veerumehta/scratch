# Gateway: settings injection, an embeddings accessor, and the Claude model gap

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Scope note, 2026-11-17. Decides nothing, queues no work; for the 2.7.5 choice. No code written. Evidence: japes 2.7.4 (`jazzx_sdk/llm/gateway/`, `jazzx_sdk/agents/anthropic_gateway.py`) against macer 47473a32 (`src/macer/runtime/ai_gateway.py`, `src/macer/agents/__init__.py`, `src/macer/jtbd/condition_dedup/embedding.py`, `src/macer/models/anthropic_gateway.py`).

## What macer does that the SDK route does not

macer calls `common.core.ai_gateway` directly:

- `use_ai_gateway(flag, settings)` and `ause_ai_gateway(flag, settings)` with `settings = gateway_settings()`: an `AIGatewaySettings` built from macer's own config loader (defaults, operator overlay, project-root `.env`, environment), never the process environment alone.
- `async_openai_client(settings, timeout=...)` for chat clients (agents/__init__.py, flex and long-timeout variants cached by decision).
- `openai_base_url(settings)` and `api_key(settings)` for the embeddings call, which goes through LiteLLM with an explicit `api_base`.

`jazzx_sdk.llm.gateway` covers the first and third of those only in shape, not in substance:

1. **Settings.** `CommonGatewayRoute(flag_key)` calls `use_ai_gateway(flag_key)`, `ause_ai_gateway(flag_key)` and `async_openai_client(**kwargs)` with no `settings`, so `common` builds its own `AIGatewaySettings` from the process environment and a `.env` in the current directory. A host whose values live in its own config layer gets a different answer (gateway off, or the wrong host) without any error.
2. **Embeddings.** The route has `enabled()` and `openai_client(**kwargs)` and nothing that returns the gateway's base URL or key. An embeddings call that is not an OpenAI-SDK client (LiteLLM with `api_base`, as macer's) has nothing to ask.
3. **Claude.** japes already has the model macer wrote by hand: `jazzx_sdk.agents.anthropic_gateway.AnthropicGatewayModel` (chat completions over the gateway client; cache breakpoints from `apply_cache_control`; thinking blocks replayed on tool turns; `verbosity` dropped; usage normalized). What differs is how thinking is switched on: macer replays when the Agents SDK `ModelSettings.reasoning.effort` is set; japes reads `extra_args["thinking"]` (the native option) and sends thinking off, with a log line, when the model does not accept it. A host that sets `reasoning.effort` would need the mapping, or japes would need to read both.

## What it would take (additive, consumer-neutral)

- **Settings injection**: `CommonGatewayRoute(flag_key, settings=None)`, passed to the four `common` calls; `None` keeps today's behavior. A host with its own config layer builds `AIGatewaySettings` once and hands it over. About 15 lines and a test that a route built with explicit settings ignores a conflicting environment variable (fails on the current route).
- **Embeddings accessor**: add `base_url()` and `api_key()` to the `GatewayRoute` protocol (optional, like `prepare`), implemented in `CommonGatewayRoute` over `openai_base_url(settings)` and `api_key(settings)`, plus `gateway_embedding_target()` in `route.py` returning `(base_url, key)` or `None` when the route is off. About 25 lines and tests with a fake route and with `CommonGatewayRoute`.
- **Claude thinking input**: either accept `reasoning.effort` as an alias of the thinking request in `AnthropicGatewayModel._thinking`, or leave it to the host to translate. Needs a decision on the effort-to-budget mapping before any code: macer's chat-completions request carries `reasoning_effort` (OpenAI shape, which LiteLLM maps to a thinking budget it chooses), while japes sends an explicit `extra_body.thinking`; not measured here which budget each ends up with.

Size: three small changes in `jazzx_sdk/llm/gateway/`, one test file each, one CHANGELOG entry; no new module. Risk: low for the first two (default `None` changes nothing); the third is a behavior question, not a code one.

## Order for macer if it is taken

1. Settings injection and the embeddings accessor land in japes (2.7.5).
2. macer replaces `runtime/ai_gateway.py` and the direct `common.core.ai_gateway` calls with `set_gateway_route(CommonGatewayRoute("ai-gateway-macer", settings=gateway_settings()))` and the accessor; its tests that patch `common.core.ai_gateway.flag.httpx.post` keep working because the route calls the same functions.
3. `GatewayAnthropicModel` goes only after the `reasoning.effort` question is settled and macer's `tests/test_anthropic_gateway_model.py` runs against `AnthropicGatewayModel`.

Not checked: Flipt behavior under the injected settings (same code path in `common`), and macer's flex-tier and per-timeout client caching (they build clients by timeout; the route's `openai_client(**kwargs)` already passes `timeout` through).
