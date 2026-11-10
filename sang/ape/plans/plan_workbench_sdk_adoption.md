# Bringing more of the SDK into policy-workbench, and its model layer

**Status:** proposed, 2026-10-31. Read-only on policy-workbench (`/Users/sangit/src/policy-workbench`, local `main` at `82ec7d8d`, which
contains `JAPES_V2`; backend under `backend/`) against japes `v2.6.8`. Plan only: no workbench edit, no spend, no push. Author:
sonnet-runtime. Same principles as `plan_juno_sdk_adoption.md`: tiered and additive, consumer-neutral SDK features, each step shippable
alone with a stop point, and nothing stated as measured that was not ([V] checked in code or run, [U] not verified).

## Status and modifications

How to use this section: the plan author may read it and update it; implementers append one dated line per slice. Newest line last.

- 2026-11-09 refreshed against japes 2.7.0 (`main` 2c8274b0) by opus-xrepo; read-only on policy-workbench; the text below still describes 2.6.8 except where a line says 2026-11-09. Nothing was run.
- Workbench now: `origin/main` d3b7d70f (2026-11-04); `backend/pyproject.toml` still pins japes at `f3101079` (2.6.4) with floor `>=2.6.4`; its `JAPES_V2` work is merged into `main`; a branch `ai-gateway-migration` exists on the workbench as on every sibling (same `common.core.ai_gateway` change; land the pin bump first so the two do not diverge on the common version).
- Pin target changes: a `main` commit of 2.7.0 (`2c8274b0`), not a plato rev (pinned revs are `main` commits or tags). The jump from 2.6.4 is one minor line plus its patches: read `docs/status/CHANGELOG.md` from 2.6.5 to 2.7.0 first. Known host-breaking items: five tenant-keyed stores take a required `tenant_id` (only if the workbench uses the SDK's stores; it uses four files of the SDK, so most likely not); pipeline ids were renamed with one deprecation warning per old id.
- Step 1 helper now exists: `function_tool_from_schema(name, description, schema, handler)` in `jazzx_sdk/agents/function_tools.py`, exported from `jazzx_sdk.agents`; the host-side adapter is no longer needed.
- Section 3 and 6 gap closed for Anthropic and Gemini: `AnthropicNativeModel` asks for thinking through `model_settings.extra_args["thinking"]` (`thinking_request`) and publishes the thinking blocks as reasoning-summary deltas, never into the answer stream (`agents/anthropic_native.py:137-140`, `:333-339`); `GeminiNativeModel` asks for thoughts and streams them (`gemini_native.py` `thinking_config`). Step 4 is therefore built for both; Ollama was not checked. What remains for the workbench's panel is verifying that its `StreamEvent(type="thinking")` mapping accepts these deltas.
- Still absent in the SDK at 2.7.0 (grepped): `BlobStore.copy` and prefix delete, `create_project_collection` and `delete_project` on the Knowledge Hub client (the global-config read was not re-checked). Steps 7 to 9 are unchanged and unverified.
- 2026-11-09 naming: Knowledge Studio is the new name of policy-workbench (user), so this plan is the Knowledge Studio plan; the roadmap deck's "Knowledge Studio" rows and this plan describe the same repo.
- Not re-checked: per-code parity of `jtbd_audit` with `jtbdset_lint`; anything the workbench did after 2026-11-04 on non-`main` branches.

## 1. What the workbench takes from the SDK today

| Area | Evidence |
|---|---|
| Pin | `backend/pyproject.toml:70` floor `japes>=2.6.4`; `:221` `[tool.uv.sources] japes = { git = ..., rev = "f3101079..." }` (japes 2.6.4, `uv.lock:1198`); uv, not poetry [V] |
| LLM pricing | `policyforge/llm_agents/claude_pricing.py:25` `from jazzx_sdk.llm import get_model_pricing, is_priced`; its own `ModelPricing` dataclass and 386 lines around them; `tests/test_claude_pricing.py:368,383` compare to the SDK's `compute_cost` [V] |
| Observability | `anthropic_provider.py:20` and `router.py:1329`: `flush_mlflow_async_trace_queue`, `sanitize_leaked_otel_env_vars` [V] |
| Prompts | `policyforge/prompts/__init__.py:8` `from jazzx_sdk.prompts import read_prompt` [V] |
| Guard | `tests/test_japes_dependency.py` imports seven pricing names and the two tracing names; I ran all of them, and `read_prompt`, against 2.6.8: all still exist [V] |
| Eval runner | opus-xrepo reports it already follows the SDK shape [U: not read] |

Four files import `jazzx_sdk`; everything else is the workbench's own.

## 2. Where it carries what the SDK now has, and where it does not match

| Workbench | SDK today | Reading |
|---|---|---|
| `mpr/ontology_store.py` (463) and `app/services/ontology_refresh.py` (287): gate, envelope unwrap, stamp, seed fallback, never raises | `pack/ontology_source.py` (`unwrap_ontology`, `reject_reason`, `OntologyStamp`, `OntologySource`) | The SDK module was built from these two; it has no disk persistence (the workbench saves atomically and feeds its prompt builder), no entity and field counts in the stamp, and two named ontologies are the workbench's config. Adopt the gate and the unwrap (about 60 workbench lines go); keep the store |
| `jtbd_audit/lint.py` (555) and `cycles.py` (307), `app/services/metric_cycles.py` (238) | `pack/jtbdset_lint.py` (14 checks), `job_references.py`, `metric_keys.py` | The workbench has check functions the SDK lacks (overlay references `lint.py:362`, planner visibility `:424`, generality `:455`, requirement structure `:251`); the SDK has the classified-edge cycles, `metric-key-shared` and the key grammar. Per-code parity was not enumerated [U] |
| `app/services/jtbd_export.py` (577), `jtbdset_import.py` (482), `jtbd_normalize.py` (121) | `pack/jtbdset_export.py`, `pipelines/policy/jtbdset.py` (`import_jtbdset`, `export_jtbdset`) | Different representation: the workbench parses JTBD **markdown files** with the vendored `mpr`; the SDK moves JTBDSet artifacts to and from canonical `Policy` rules. Not a drop-in. The shared ground is the artifact |
| `app/services/guideline_versioning.py` (1,556) | `pack/guidelines.py` (311), `guidelines_db.py` (280) | Different storage: git branches `guidelines/{audience}/v{N}` plus a Knowledge Hub collection (`:5-15`) against immutable DB versions with blob files. Investor classification (`:325` has the one direct `anthropic.Anthropic` call, `:356`) and entity generation are the workbench's. Overlap is version numbering and immutability only |
| `app/services/baseline_store.py` (102) | `evaluation/experiments.py` `set_baseline` / `get_baseline` | **Not the same thing.** The workbench's baseline is the customer's policy tree (`BaselineDoc` rows keyed by subpath, content-addressed); the SDK's baseline is an evaluation experiment baseline for a subject. No adoption; the pairing suggested earlier does not hold [V both files' headers] |
| `app/services/knowledge_hub.py` (757, own httpx, V1 entity API), `kh_config.py` (299, global-config `APP_CONFIG`) | `clients/knowledge_hub_client.py` (`create_collection` `:493`, `create_document` `:629`, `create_document_v2` `:706`) | The SDK client lacks project create and delete (`create_project_collection`, `delete_project`) and any global-config read [V grep]; the V1 entity upload path was not compared [U]. Partial |
| `app/services/object_store.py` (186: `put/get/delete/copy`, prefix delete; Azure blob, Azure Files stub, local) | `fabric/blob/store.py` (`BlobStore`: put, get, delete; azure and local) | The SDK store has no `copy` and no prefix delete [V]. `blobs.py` (77) is local directory helpers and unrelated |

## 3. The model layer

The workbench routes by model-name prefix in `llm_agents/factory.py:21-35`: `claude*` to `ClaudeAgentProvider`, `gpt-*`, `o1`, `o3`, `o4` to
`OpenAIAgentProvider`, anything else a `ValueError`. Both implement `LLMProvider` (`base.py`: `complete`, `complete_with_agent_loop`,
`stream_event`) over provider-agnostic `ToolDefinition(name, description, parameters, handler)`.

**OpenAI side (274 lines).** `openai_provider.py:143,165` is `Agent` and `Runner.run`, with each tool wrapped by `function_tool`
(`:46`): the stack the SDK's own agents use (`agents/openai_provider.py`, 447 lines, openai-agents). Same machinery, so it can move first.

**Claude side (992 lines) is not an API client.** `anthropic_provider.py` wraps `claude-agent-sdk`, which drives the **Claude Code CLI as a
subprocess**: `ClaudeSDKClient` (`:859`), tools served to the CLI by an in-process MCP server (`_build_mcp_server` `:545`,
`create_sdk_mcp_server`), `thinking={"type": "adaptive", "display": "summarized"}` (`:472`, `:639`) so reasoning text streams to the UI as
`StreamEvent(type="thinking")` (`:355`), a process registry so a stop can SIGKILL the subprocess, a per-run `CLAUDE_CONFIG_DIR` against
cross-session transcript bleed, and a Postgres store of the CLI's transcripts (`claude_session_store.py`, 365 lines; read by the reasoning
panel, cost aggregation and the orphan sweep). Resumption is already off (`base.py`: every call starts a fresh CLI conversation).

**What the SDK covers, checked in code:**

| The workbench needs | SDK | Verdict |
|---|---|---|
| A tool-call loop with a turn cap | openai-agents `Runner` over `AnthropicNativeModel` (`agents/anthropic_native.py`: Messages API, `tool_use` blocks as function calls); `run_kit.py` `max_turns` (default 30), `MaxTurnsExceeded` handled | Covered |
| Streaming of text and tool-call arguments | `AnthropicNativeModel.stream_response` (`:202-264`) | Covered |
| Streaming the model's thinking to a panel | `anthropic_native.py:264`: "Thinking deltas are not emitted: they would land in the answer stream" | **Gap.** The request side exists (`llm/providers/anthropic.py:33` `_apply_thinking`, card `thinking_shape`), the stream does not carry it |
| Provider-agnostic tool handlers | The same `function_tool` mapping the workbench's OpenAI provider uses | Covered |
| Stop a running call | task cancellation of the awaiting coroutine (no subprocess) | Different mechanism; the SIGKILL path would go away |
| Claude Code's own behavior (built-in tools, auto-compaction, retries, caching, MCP output limits `MAX_MCP_OUTPUT_TOKENS`) | none; the loop is openai-agents', and the workbench allows only its own MCP tools | Parity **not verified** |
| Transcript store, orphan sweep, cost per run | `runs/` journal, `llm/turn_cost`, `llm/cost_tracker` | Replace by design, not 1:1 |

So the SDK covers tool calls and streamed text, and does **not** cover streamed thinking; Claude Code's loop behavior has no SDK
equivalent whose parity anyone measured. The recommendation is therefore not to replace the Claude provider, but to add an SDK-backed one
beside it and move only on measured parity.

## 4. Ordered plan (reordered 2026-10-31: model layer first; each step its own workbench PR on its `JAPES_V2` branch, each stops cleanly)

| # | Step | Owner | Test | Risk | Stop point |
|---|---|---|---|---|---|
| 0 | **Pin.** `rev` to the japes 2.7.0 `main` commit (`2c8274b0`; 2026-11-09, was a 2.6.7 plato rev), floor `>=2.7.0`, `uv lock`; the suite | workbench PR | its suite; `test_japes_dependency.py` (every name it imports still exists in 2.6.8, [V]) | Low to medium. The `openai-agents` floor already matches: the workbench declares `>=0.22.0` (`pyproject.toml:71`) and locks 0.24.0 (`uv.lock:1837`), japes needs `>=0.22.0` [V]. What the lock gains: `jazzx-plato-client` 0.2.7 | Workbench on a known SDK |
| 1 | **OpenAI provider onto the SDK's agent builder.** `OpenAIAgentProvider` (274 lines: `Agent` plus `Runner.run` over `function_tool`) builds its agent with `jazzx_sdk.agents.openai_provider.OpenAIProvider.build_agent(name, instructions, model=, tools=, model_settings=)` (`:56`), keeping `LLMProvider` and `ToolDefinition` | workbench PR (the SDK helper now exists: `function_tool_from_schema`, 2026-11-09) | provider tests with the same fixtures; a tool with a nested array and object parameter keeps its schema; a handler that raises still returns `Tool error: ...` | Medium. See "Tool mapping" below | Flag off keeps today's |
| 2 | **Opt-in switch: `claude-*` on the same SDK path, as an EXPERIMENT.** `factory.get_provider` (`factory.py:21`) gains a switch (an env flag, default off) under which a `claude*` model returns the SDK-path provider from step 1 instead of `ClaudeAgentProvider`. The SDK already routes by name: `resolve_model` sends `claude-*` to `AnthropicNativeModel`, `gpt-*` to OpenAI, `gemini-*` to Gemini [V `agents/models.py:345-375`]. **The Claude Code CLI provider stays primary and the default** | workbench PR | the same fixtures through both; the factory test for the switch | Medium: behavior differs in ways not measured (below) | Switch off is today's behavior |
| 3 | **Measured side by side, later.** A recorded eval set run through both Claude paths, comparing answer, tool use, cost and latency | workbench, with the user's approval of any spend | the comparison itself | n/a | Report only; the default does not move on this alone |
| 4 | **An opt-in thinking stream in the SDK, only if the user decides it is a product need** (section 6; built for Anthropic and Gemini by 2026-11-09, see Status) | SDK, then workbench | provider-by-provider stream tests | Medium | Do not build without the decision |

Independent of the model layer, in this order when wanted: **5** delete the workbench pricing copy where `test_claude_pricing.py`'s parity tests already compare it to `compute_cost` (low); **6** import `unwrap_ontology` and `reject_reason` for the ontology gate (`ontology_refresh.py:234`, `ontology_store.py:182`), the store stays (low); **7** run `lint_jtbdset` beside `jtbd_audit` on `build_artifact`'s output and write the per-code parity table (report only); **8** the investor-classification call (`guideline_versioning.py:356`) through `jazzx_sdk.llm` instead of a bare `anthropic.Anthropic` (low); **9** KH project calls, global-config read, blob `copy` and prefix delete as SDK verbs only if the workbench wants them (SDK first). **Not now:** retiring the CLI path (subprocess, transcript store, sanitizer): only after step 3 shows parity, and only if the user decides to leave Claude Code.

**Tool mapping (step 1), checked.** The workbench builds each tool by `exec()`-generating a typed function from the schema's `properties` and only the types `string`, `integer`, `number` and `boolean` (`openai_provider.py:36-100`), so an array or object parameter does not keep its schema. `build_agent` takes ready agents-SDK tool objects and does not convert (`OpenAIProvider.format_tools` makes chat-completions function dicts, not agent tools) [V]. The installed `FunctionTool` takes `name`, `description`, `params_json_schema` and `on_invoke_tool` directly (agents 0.22.3) [V], and the SDK's own Anthropic and Gemini models read `params_json_schema` off a tool (`anthropic_native.py:143`, `gemini_native.py:117`) [V]. So the adapter is `ToolDefinition(parameters=schema, handler)` to `FunctionTool(params_json_schema=schema, on_invoke_tool=wrapper, strict_json_schema=False)`, passing the schema through whole. The SDK has no such helper; one small consumer-neutral `function_tool_from_schema(name, description, schema, handler)` would serve any host with JSON-schema tools (a host-side adapter of about 25 lines is the alternative). Not verified: that strict-mode off matches the exec path's behavior on every workbench tool.

**What the builder adds that the workbench does not have today** (behavior differences to measure, [U]): a retry-wrapped model (`resolve_model(..., retry=True)`), usage hooks, and, only when a model name carries `flex_`, OpenAI's flex tier (`with_cost_tier`, `agents/models.py:327`). **For the Claude experiment** (step 2): `AnthropicNativeModel._request` sends `model`, `messages`, `max_tokens` (default 4096), `system`, `tools` and `temperature` only, so **no `thinking` is requested** on this path [V `anthropic_native.py:153-168`], there are no Claude Code built-in tools, no MCP server, no auto-compaction and no transcript store; whether answers, tool use and cost are comparable is exactly what step 3 measures.

## 5. Open questions for the user
1. Is a workbench PR from its `JAPES_V2` branch agreed, and who reviews on the workbench side?
2. The pin: the 2.7.0 `main` commit `2c8274b0` (2026-11-09; the 2.6.7 and 2.6.8 targets are superseded).
3. Claude provider: does the workbench want to leave Claude Code (and its built-in loop behavior) at all? Steps 2 and 3 are an experiment beside it, not a commitment.
4. Streamed thinking: section 6 says who needs it and what exists; is it a product need? That decides step 4.
5. Do the KH project calls and `copy` / prefix delete belong in the SDK, or stay workbench-specific (step 4)?
6. Does `jtbd_audit` stay the source of the check set, with the SDK's new checks adopted into it, or the other way (step 3)?

## Not verified
Per-code parity of `jtbd_audit` with `jtbdset_lint`; the V1 entity upload path against the SDK client; `model_catalog.py` (440) and `run_cost.py` (49) against `llm.model_cards` and `llm.cost_tracker`; the eval runner; strict-schema-off tool parity with the exec path; what the retry-wrapped builder changes in the workbench's runs; parity of Claude Code's loop with the SDK's (step 3 measures it); `ClaudeAgentProvider`'s internals past the lines cited; the Gemini and Ollama behavior in section 6 beyond what the SDK and the cited hosts show.

## 6. Thinking: is it Anthropic-only, who needs it, what the SDK has

**Not Anthropic-only, and four different needs share one word.** Checked in code:

| Need | Where | Provider | Kind |
|---|---|---|---|
| Show the model's reasoning text | juno: `app/copilot/skill_service.py:4653-4657` asks `ModelSettings(reasoning=Reasoning(effort="low", summary="auto"))` and renders a "Thinking" phase from the stream; `run_skill.py:3664-3690` opens a Thinking step per sub-agent from the reasoning-summary events | **OpenAI** (openai-agents) | display |
| Show the model's reasoning text | workbench: `anthropic_provider.py:355` turns the CLI's `thinking` blocks into `StreamEvent(type="thinking")` for its reasoning panel; `:472,:639` ask `thinking={"type": "adaptive", "display": "summarized"}` | **Anthropic** (Claude Code CLI) | display |
| Control how hard the model thinks | MACER: defaults `reasoning_effort="high"` and `num_parallel_inferences=3` (named in `e2e/runner.py:105-112`); on Ollama it sends `reasoning_effort` only to a model that declares the `thinking` capability, since Ollama answers 400 otherwise (`e2e/runtime/local.py:32-36,79,102`) | OpenAI-compatible, Ollama | control, no display |
| A label that says "working" | kernel-lab: `ui_server.py:6939` yields a "Thinking" heartbeat while waiting, `cortex-assistant server.py:6630` sends the plan text as a `thinking` event | none | progress, not model reasoning |

**What the SDK exposes today, verified:**

| Provider | Control (request) | Display (stream) | Count |
|---|---|---|---|
| Anthropic | `llm/providers/anthropic.py:33` `_apply_thinking` (extended thinking; `adaptive` or `enabled` from the card's `thinking_shape`) on the `llm` path only. **Not on the agent path**: `AnthropicNativeModel._request` sends no `thinking` (`anthropic_native.py:153-168`) | **Dropped on purpose**: "Thinking deltas are not emitted: they would land in the answer stream" (`:264`); a `reasoning` input item is skipped (`:129`) | `reasoning_tokens=0` (`:488`) |
| OpenAI | `reasoning_effort` accepted on the `llm` path (`llm/config.py:115`), carded values via `supported_reasoning_efforts` and warned when wrong; agent path takes whatever `ModelSettings` the host passes | **Exists, opt-in.** `stream_reasoning` on an agent spec or skill (`interactive/spec.py:275`, `agent.py:1045-1057`, `:1403-1417`) publishes a `ReasoningEvent` for each `ResponseReasoningSummaryTextDeltaEvent` (`stream_hooks.py:188-203`); needs `common`'s `ReasoningEvent` to be importable | `reasoning_tokens` metered (`openai_provider.py:420-440`) |
| Gemini | none found for thought summaries (`include_thoughts` or a thinking config does not appear) | none | `thoughts_token_count` counted as reasoning (`gemini_native.py:345-361`); the provider lists `thinking` as a feature (`gemini_provider.py:80`) |
| Ollama | none in `llm/providers/local.py` | none | none |
| Kernel path | `reasoning_effort` on the invoke request (`clients/kernel_invoke.py:80,234`) | n/a | n/a |

So a host already gets reasoning text from an OpenAI-stack agent through one opt-in event, `ReasoningEvent`, fed by the Agents SDK's own provider-neutral raw event type. **The gap is that no other model class emits that event**: `AnthropicNativeModel` drops the thinking deltas and never asks for thinking; the Gemini model neither asks for nor streams thoughts; Ollama has no path.

**A consumer-neutral SDK feature, if wanted:** keep the one existing opt-in event and make each model class fill it when it can. (1) `AnthropicNativeModel`: when `ModelSettings` asks for reasoning (the Agents SDK's own `Reasoning(effort, summary)` field), send `thinking` per the card's `thinking_shape` and emit `ResponseReasoningSummaryTextDeltaEvent` for `thinking_delta`, never into the answer stream. (2) `GeminiNativeModel`: send the thinking config with thoughts included and emit the same event for thought parts. (3) Ollama: pass `reasoning_effort` only when the model declares `thinking`, as MACER does, and emit its reasoning content if the API returns it (not verified that it does). Hosts choose with `stream_reasoning` as today; nothing changes for one that does not. Size is not estimated here and the Anthropic, Gemini and Ollama stream shapes were not exercised.

**Who would use it:** juno already has it (OpenAI path; no change); the workbench's panel needs the Anthropic part if its Claude calls ever leave the CLI (step 2 onward); MACER needs only the effort control it already has; Plato chat could show reasoning for any model once the event is filled, which is a product decision for the user. Nobody needs it for kernel-lab, whose "thinking" is a progress label. So the SDK work is justified by the workbench panel and, optionally, Plato chat; it is not needed for the other consumers.
