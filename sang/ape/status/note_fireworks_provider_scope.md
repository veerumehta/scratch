# Fireworks provider: what macer has, where it would sit in japes, and what is open

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Scope note, 2026-11-18. Decides nothing; asks one question at the end. Evidence: macer `src/macer/models/fireworks.py` (176 lines), `tests/test_fireworks_model.py` (322 lines), `agents/__init__.py` (`_get_fireworks_client`, routing), `utils/cost.py` (`FIREWORKS_PREFIX`, `fireworks_model_id`, pricing rows); japes `jazzx_sdk/agents/models.py` (`infer_provider`, `resolve_model`), `jazzx_sdk/llm/providers/`, `jazzx_sdk/llm/manager.py`.

## What macer built

A Fireworks model name is `fireworks/<fireworks model id>` (a tier prefix such as `flex_` may precede it). `FireworksModel` is an Agents SDK `OpenAIChatCompletionsModel` over an `AsyncOpenAI` pointed at `FIREWORKS_BASE_URL` with `FIREWORKS_API_KEY` (both required: a missing one raises `ValueError` naming it). Two behaviors beyond a plain Chat Completions model, both pinned by its tests:

1. **Tools and structured output are split.** Fireworks rejects a forced `tool_choice` combined with `response_format`, and under `auto` the model writes a schema-shaped guess instead of calling the tool. An agent with both runs in two requests: a tool step (tools, no `response_format`; a response with tool calls goes back to the runner as is) and, once the model answers in plain text, a structured step (the draft appended, a fixed prompt, `response_format`, no tools). Usage of the two is summed. `tool_choice="none"` skips the tool step. An agent with only tools or only an output type is one ordinary request.
2. **OpenAI-only request settings are dropped** (`verbosity`, `truncation`, `extra_args`, `store`, `prompt_cache_retention`). Streaming is not supported and says so.

Pricing in `cost.py` is per token for serverless models; a custom deployment (`<model>#<deployment>`) is billed by GPU time, which macer does not price.

## Where it sits in japes

japes has two tiers and macer's model belongs to one of them:

- **Agents tier** (`jazzx_sdk/agents/models.py`): `resolve_model(name)` picks a model by `infer_provider(name)` (`claude` -> Anthropic, `gemini` -> Gemini, otherwise OpenAI Responses) and wraps it in `RetryingModel`. A `FireworksModel` and a `fireworks` branch here is the direct counterpart of what macer does.
- **LLM tier** (`jazzx_sdk/llm/providers/`, `LLMManager`): `BaseProvider` implementations (OpenAI, Anthropic, Gemini, local) for the direct-call path. A `FireworksProvider` would be a small OpenAI-compatible provider (a different base URL and key), plus manager registration.

macer uses only the agents tier. The LLM tier would have no consumer today.

## Size

Agents tier alone: `FireworksModel` about 120 lines, the resolver branch and client (env, timeouts, pooling) about 50, tests about 300 (port of macer's, ruling out the macer-specific config): roughly 450 lines. With the LLM-tier provider, the manager registration, model cards and cost rows, a `check_new_models` probe and their tests: about 800. Past "a few hundred" either way, so this note comes first.

## Open points

1. **Which tier(s).** Recommendation: the agents tier only, as one item; the LLM tier when a consumer wants it (nobody calls Fireworks through `LLMManager`).
2. **Naming.** `sync_model_name` strips a `<provider>/` qualifier before `infer_provider` runs, so `fireworks/<id>` would lose its routing prefix; the resolver has to look for the prefix first. Fireworks ids are themselves paths (`accounts/fireworks/models/<name>`), so only the first segment may be treated as the provider.
3. **Configuration.** macer requires `FIREWORKS_BASE_URL` explicitly. The documented endpoint is public, so japes could default it; a default is a decision about being wrong silently if the endpoint moves.
4. **Prices.** Per-token serverless prices have a real source (`fireworks.ai/pricing`, fetched 2026-11-18, 586 KB, names Kimi, GLM and DeepSeek models); macer's rows agree where they overlap but are secondary. Cards and cost rows only from the page, none guessed; the custom-deployment GPU-time billing stays unpriced and the cost helper should say "unpriced", not 0.
5. **The two-step flow costs two requests.** It is what makes tools plus an output type work on Fireworks, but a caller should know; the usage sum already reports both.
6. **Contract test, no live call.** "Mocks miss bad names": a test that the model ids sent are the ids Fireworks serves needs either a recorded listing or a live call (the user's spend); macer has neither. A fixture of the served ids from the pricing page would pin the names without spend.

## Question for the user

Build the agents tier only (about 450 lines, one commit plus tests) now, with points 2 to 4 settled as above, and leave the LLM tier, cards and cost rows for when a consumer asks?
