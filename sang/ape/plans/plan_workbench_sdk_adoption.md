# Bringing more of the SDK into policy-workbench, and its model layer

**Status:** proposed, 2026-10-31. Read-only on policy-workbench (`/Users/sangit/src/policy-workbench`, local `main` at `82ec7d8d`, which
contains `JAPES_V2`; backend under `backend/`) against japes `v2.6.8`. Plan only: no workbench edit, no spend, no push. Author:
sonnet-runtime. Same principles as `plan_juno_sdk_adoption.md`: tiered and additive, consumer-neutral SDK features, each step shippable
alone with a stop point, and nothing stated as measured that was not ([V] checked in code or run, [U] not verified).

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

## 4. Ordered plan (smallest first; each step is its own workbench PR on its `JAPES_V2` branch, and each stops cleanly)

| # | Step | Owner | Test | Risk | Stop point |
|---|---|---|---|---|---|
| 0 | **Pin.** `rev` to a pushed commit of japes 2.6.7 (`origin/plato` `18bbded9`), floor `>=2.6.7`, `uv lock`; the suite | workbench PR | its suite, `test_japes_dependency.py` (the surface still imports, [V]) | Medium: `openai-agents` moves to `>=0.22` (japes's floor; the workbench's own pin not read [U]), and the lock now carries `jazzx-plato-client` 0.2.7 | Workbench on a known SDK |
| 1 | **Pricing.** Delete the workbench copy where `test_claude_pricing.py`'s parity tests already compare it to `compute_cost`; keep a thin wrapper if the call sites need its shape | workbench PR | the existing parity tests, unchanged | Low | Stop; behavior identical |
| 2 | **Ontology gate and unwrap.** Import `unwrap_ontology` and `reject_reason` for `_extract_schema` and `reject_reason` (`ontology_refresh.py:234`, `ontology_store.py:182`); the store and prompt builder stay | workbench PR | its ontology tests plus one per envelope shape | Low | Stop |
| 3 | **Lint beside, not instead.** Run `lint_jtbdset` on the artifact `build_artifact` produces and show its findings next to `jtbd_audit`'s; per-code parity table written from the real output | SDK note, workbench PR | a fixture set both lints run on | Low | Report only |
| 4 | **KH and blob verbs the SDK lacks** (only if the workbench wants them moved): project create and delete, global-config read, blob `copy` and prefix delete, as consumer-neutral client and store methods | SDK first, then workbench | contract tests against the mock hub and a local blob | Medium | Skip if not wanted |
| 5 | **OpenAI provider onto the SDK agent stack** (`agents/openai_provider.py`), same `LLMProvider` interface | workbench PR | provider tests with the same fixtures | Medium | Flag off keeps today's |
| 6 | **The investor-classification call** (`guideline_versioning.py:356`) through `jazzx_sdk.llm` instead of a bare `anthropic.Anthropic` | workbench PR | the classify tests with a stub model | Low | Stop |
| 7 | **An SDK-backed Claude provider beside `ClaudeAgentProvider`**, behind a model-name or env switch; first needs the SDK to stream thinking (an opt-in event, not in the answer stream) | SDK (thinking stream), then workbench | a side-by-side run on a recorded eval set measuring answer, tool use, cost and latency | High: Claude Code's loop behavior differs and was not measured | Do not switch the default until parity is shown |
| 8 | **Retire the CLI path** (subprocess, session store, sanitizer) | workbench | none until 7 is proven | High | Only after 7 |

## 5. Open questions for the user
1. Is a workbench PR from its `JAPES_V2` branch agreed, and who reviews on the workbench side?
2. The pin: is `origin/plato` `18bbded9` (2.6.7) the target, or wait for the 2.6.8 squash (unpushed)?
3. Claude provider: does the workbench want to leave Claude Code (and its built-in loop behavior) at all? Step 7 is a measured experiment, not a commitment.
4. Streamed thinking: is it a product feature the reasoning panel needs? That decides whether the SDK builds the thinking stream.
5. Do the KH project calls and `copy` / prefix delete belong in the SDK, or stay workbench-specific (step 4)?
6. Does `jtbd_audit` stay the source of the check set, with the SDK's new checks adopted into it, or the other way (step 3)?

## Not verified
Per-code parity of `jtbd_audit` with `jtbdset_lint`; the V1 entity upload path against the SDK client; `model_catalog.py` (440) and `run_cost.py` (49) against `llm.model_cards` and `llm.cost_tracker`; the workbench's `openai-agents` pin; the eval runner; parity of Claude Code's loop with the SDK's; `ClaudeAgentProvider`'s internals past the lines cited.
