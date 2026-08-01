# JAPES 1.2: Agent Execution Layer - Design Spec

**Status:** DRAFT | **Author:** Virendra Mehta | **Date:** May 23, 2026 | **For:** Team review

---

## 1. Aspiration

### What

The run-time SDK provides governed multi-provider agent execution as a platform service. Extensions declare cognitive tasks - prompts, tools, output schemas - and the platform handles provider selection, structured output enforcement, tool format translation, execution tracing, cost attribution, and governance hook points. An extension never imports an LLM SDK directly.

### Why

Four production extensions (MACER, K9, Juno, JACI-AML) each independently `pip install openai-agents` and solve the same set of problems inside their own handler code. JACI-KYC built a 268-line `AnthropicAdapter` from scratch. The platform treats all of this as a black box.

The duplication is concrete: MACER built its own `cost.py` for LLM cost computation, which was later extracted into the Runtime SDK as a universal utility - but only after the pattern had already been copied. Each extension configures its own MLflow tracking independently. Structured output parsing, tool format conversion, and retry logic are rebuilt per extension with no shared learning.

The platform's current posture is **"technology freedom inside the handler"** - which is correct for general extensibility (a handler that shells out to FFmpeg shouldn't need platform support). But for agent SDK capabilities specifically, this is **platform abdication disguised as flexibility**. The platform cannot:

- **Trace** what happened inside LLM calls (tokens, tool-use iterations, model, latency)
- **Attribute cost** per pack, per mode, per case
- **Enforce governance hooks** at the LLM call boundary (pre-call Governor checks, post-call Sentinel monitoring)
- **Feed the EVOLVE loop** with process-level execution data (not just outcome data)
- **Upgrade models centrally** - a new model requires updating 4+ extensions independently
- **Enforce structured output** consistently - each extension re-solves the OpenAI vs Anthropic divergence
- **Translate tool formats** - each extension maintains its own converter

### How

A new `ctx.runtime.agents` surface in the Runtime SDK - the Agent Execution Layer. It owns the LLM SDK dependencies, provides a generic provider-portable API and a provider-specific tier for unique capabilities (extended thinking, agent handoffs), and emits unified execution traces that feed governance, cost attribution, and the EVOLVE loop. Full design in sections 4-7 below.

### When

Phase 1 (consolidation) extracts existing adapter code from JACI-KYC and JACI-AML into the Runtime SDK - no greenfield, mostly relocation. Phase 2 adds governance hooks and provider-specific features. Phase 3 validates the contract with a third provider. Detailed phasing in section 8.

---

## 2. Lineage

This spec implements a concept that appears in the v2.0 architecture at three levels:

- **Substrate Key Services (#02)** names an "Agent Framework Adapter" as a platform service providing unified lifecycle, routing, tracing, and promotion across agent runtimes. This spec is the implementation design for that capability, realized as a layer in the Runtime SDK.
- **Architecture Overview (Layer 2)** positions the "Multi-framework Adapter Layer" as infrastructure alongside Flowable, Memory Service, and Learning Service. The `AgentProvider` protocol and `AgentExecutionLayer` in this spec are the concrete realization.
- **Charter Alignment v4 Addendum** resolved the per-vertical vs. platform multi-runtime tension by defining three options (A: prompt-only, B: SDK adapter pattern, C: JAPES adapter registration). Option A is where we are today. This spec delivers Options B and C as Phases 1 and 2-3 respectively.

The v2.0 architecture also explicitly calls for stopping the "custom Kernel agent loop as the only runtime path" in favor of a "pluggable Adapter Layer." This spec is that pluggable layer.

---

## 3. Design Principles

1. **Extensions declare WHAT, platform handles HOW.** A mode says "run this prompt with these tools and give me this Pydantic model back." The platform picks the provider, converts tool formats, enforces structured output, traces everything.
2. **Two-tier API: generic + provider-specific.** The generic tier is provider-portable. The provider-specific tier exposes unique capabilities (extended thinking, prompt caching, agent handoffs) for extensions that deliberately choose to bind.
3. **SDK dependencies move to the Runtime SDK, not extensions.** Extensions never `import openai` or `import anthropic`. The Runtime SDK owns the dependency, the client lifecycle, and the credential management.
4. **Backward compatible.** The "handler as black box" contract doesn't break. An extension that uses LangChain or another framework outside the platform's provider set can still bring its own SDK. But the strong path - and the one that gets platform tracing, governance, and EVOLVE loop integration - is `ctx.runtime.agents`.
5. **Governance hooks are first-class.** Pre-call and post-call hooks allow Governor, Sentinel, and Evaluator to observe and (where authorized) intercept LLM execution.

---

## 4. Architecture

### 4.1 New Runtime SDK Layer: `ctx.runtime.agents`

Sits alongside `.kernel`, `.knowledge_hub`, `.process`, `.canonical_objects` as a first-class Runtime SDK capability.

```jsx
JazzX Runtime SDK
├── Infrastructure Layer (queues, lifecycle, tracing)
├── Client Layer (kernel, knowledge_hub, process)
├── Canonical Objects (policy, evidence, decision, trace, outcome)
├── Cognitive Modes (BaseMode, MODE_REGISTRY, prompt resolution)
├── Universal Tools (BaseToolRegistry, 15 KH tools)
├── Expert Layer (5 experts, 19 named operations)
└── Agent Execution Layer  ← NEW (this spec)
    ├── AgentProvider protocol (common contract)
    ├── OpenAI Provider (openai-agents SDK)
    ├── Anthropic Provider (anthropic SDK)
    ├── Tool Format Translator
    ├── Structured Output Normalizer
    ├── Execution Tracer
    ├── Governance Hook Engine
    └── Credential & Model Manager
```

### 4.2 The Generic Tier

Provider-portable execution. Most modes use this most of the time.

```python
# Extension code - no openai or anthropic import anywhere
async def handle(self, ctx: HandlerContext) -> ResponseMessage:
    result = await ctx.runtime.agents.run(
        system_prompt=prompt_text,
        messages=[{"role": "user", "content": "..."}],
        tools=my_tool_definitions,
        output_schema=MyPydanticModel,
        # Provider resolved from pack config, or explicit:
        provider="openai",   # optional override
        model="gpt-4o",      # optional override
    )
    # result.output → MyPydanticModel (parsed, validated)
    # result.trace → AgentExecutionTrace
```

### 4.3 The Provider-Specific Tier

For extensions that deliberately choose provider-unique capabilities.

```python
# Anthropic-specific: extended thinking with governance capture
result = await ctx.runtime.agents.anthropic.run(
    system_prompt=prompt_text,
    messages=[...],
    output_schema=MyModel,
    extended_thinking=True,
    prompt_caching=True,
)
# result.thinking → captured in trace for EVOLVE loop
# result.cache_metrics → tracked for cost attribution

# OpenAI-specific: agent handoffs (Agents SDK native pattern)
result = await ctx.runtime.agents.openai.run_with_handoffs(
    agents=[investigator_agent, verifier_agent],
    handoff_rules=[...],
)
# Handoffs mapped to mode transitions in trace
```

### 4.4 Integration with Cognitive Modes

`BaseMode` subclasses currently construct their own SDK clients. With the Agent Execution Layer, modes call `ctx.runtime.agents.run()` instead.

```python
# BEFORE (each mode brings its own SDK)
class InvestigatorMode(BaseMode):
    async def run(self, context, tool_registry) -> ModeResult:
        client = openai.agents.Agent(...)  # extension-owned
        result = await Runner.run(client, messages)
        return ModeResult(output=result)

# AFTER (platform-provided execution)
class InvestigatorMode(BaseMode):
    async def run(self, context, tool_registry) -> ModeResult:
        result = await self.ctx.runtime.agents.run(
            system_prompt=self.get_prompt(),
            messages=context.messages,
            tools=tool_registry.definitions,
            output_schema=self.output_type,
        )
        return ModeResult(output=result.output, trace=result.trace)
```

The mode still owns its prompt, tool selection, and output schema - all the domain intelligence. It just doesn't own the plumbing.

---

## 5. Five Platform Capabilities

These are the capabilities that accumulate value at the platform level and justify moving agent execution out of the handler black box.

### 5.1 Structured Output Normalization

| Provider | How structured output works | Platform responsibility |
| --- | --- | --- |
| OpenAI Agents SDK | `response_format` natively enforced | Pass through, validate result |
| Anthropic | Prompt-level instruction + `betas=["structured-outputs"]`  • response parsing | Inject schema instruction, parse, retry on failure |
| Gemini (future) | TBD | Implement per Gemini spec |

The extension says "I want `MyPydanticModel` back." The platform makes it happen. Parse failures trigger corrective retries with the error message fed back. One implementation, tested and hardened, used by every extension.

### 5.2 Tool Format Translation

`BaseToolRegistry` (v0.4.0) emits tool definitions as plain dicts. The Agent Execution Layer translates to provider-specific wire format internally:

- OpenAI: `{"type": "function", "function": {"name": ..., "parameters": ...}}`
- Anthropic: `{"name": ..., "input_schema": ...}`
- Tool result format differences handled transparently

When a provider changes their tool schema (and they do), one update to the Runtime SDK fixes it everywhere.

### 5.3 Unified Execution Tracing

Every `ctx.runtime.agents.run()` call produces an `AgentExecutionTrace`:

```python
@dataclass
class AgentExecutionTrace:
    trace_id: str
    provider: str           # "openai" | "anthropic"
    model: str              # actual model used
    tokens_input: int
    tokens_output: int
    tokens_cache_read: int  # Anthropic prompt caching
    tokens_cache_write: int
    tool_calls: list[ToolCallRecord]  # name, args, result, latency
    tool_use_iterations: int
    latency_ms: float
    structured_output_attempts: int  # retries on parse failure
    thinking_content: str | None     # Anthropic extended thinking
    cost_usd: float         # computed from model pricing table
    pack_id: str
    mode_name: str | None
    case_id: str | None     # if available from context
```

This trace flows into the platform's Postgres tracing infrastructure. The platform can now answer: "How many LLM calls did the AML pack make last week, at what cost, with what cache hit rate, with what structured output success rate?"

### 5.4 Governance Hook Engine

Pre-call and post-call hooks registered by the pack or by platform governance modes.

```python
# Hook registration (pack config or code)
ctx.runtime.agents.register_hook(
    stage="pre_call",
    hook=governor_pre_check,    # can block or modify the call
)
ctx.runtime.agents.register_hook(
    stage="post_call",
    hook=sentinel_health_check, # can flag anomalies
)
ctx.runtime.agents.register_hook(
    stage="post_call",
    hook=evaluator_trace_capture, # subscribes to all traces
)
```

Capabilities:

- **Governor** can inspect system prompt before it's sent
- **Sentinel** can check response for anomalies before it's returned
- **Evaluator** can subscribe to all execution traces for post-hoc quality assessment
- **Autonomy enforcement** - ceiling checks happen at the execution boundary, not inside the mode

### 5.5 Credential & Model Management

API keys resolved from Azure Key Vault or managed identity - not from `.env` files each extension manages. Model selection driven by pack config, overridable per mode, centrally upgradable.

```yaml
# Pack manifest - runtime section
runtime:
  default_provider: openai
  default_model: gpt-4o
  mode_overrides:
    sentinel:
      model: gpt-4o-mini        # lighter model for loop health
    reasoner:
      provider: anthropic       # extended thinking helps here
      model: claude-sonnet-4-5
  providers:
    openai:
      features: [agent_handoffs, streaming]
    anthropic:
      features: [extended_thinking, prompt_caching]
  cost_budget:
    daily_usd: 500
    alert_threshold: 0.8
```

---

## 6. Relationship to LLM Gateway, Observability, and Canonical Trace

The v2.0 architecture defines the LLM Gateway and Agent Framework Adapter as two separate substrate services. In practice, the Agent Execution Layer is the right place to embed the Gateway's core capabilities for PoC and early production, because every LLM call already flows through `ctx.runtime.agents.run()`. A separate network hop to a Gateway service is unnecessary when the execution layer already has the call boundary.

### 6.1 Gateway Planes Embedded in the Execution Layer

| Gateway Plane | What it does | How it maps to the Agent Execution Layer |
| --- | --- | --- |
| Enforcement | Provider abstraction, routing, failover, model/version pinning | `AgentProvider` protocol = provider abstraction. Pack manifest `runtime.mode_overrides` = per-task routing. Failover = provider-level retry with fallback provider config |
| Cost | Token metering, tenant budgets, quotas, cost-per-outcome | `AgentExecutionTrace` already captures tokens + cost. Add budget enforcement and quota checks as pre-call config checks |
| Safety | Prompt/output guardrails, privacy masking | Governance hook engine: pre-call hooks for prompt guardrails and PII masking, post-call hooks for output guardrails |
| Observability | Trace IDs, provider latency, token usage, quality signals | `AgentExecutionTrace` is this plane. Every call gets a trace_id, latency_ms, token counts, and structured output success rate |
| Control | Model approvals, policies, exceptions | Pack manifest `runtime.providers` section + model allow-lists per environment |
| Experiment | A/B testing, traffic controls, rollback | Phase 2+. The routing infrastructure supports this: provider + model are config-driven, so traffic splitting is a config concern |

The Gateway remains a valid long-term architectural target for multi-tenant production (centralized rate limiting, cross-tenant budget enforcement, fleet-wide model governance). But for the current stage, embedding these capabilities in the Runtime SDK means extensions get governed model access without waiting for a separate Gateway service to be built and deployed.

### 6.2 MLflow and Observability Integration

JACI currently uses MLflow for experiment tracking with per-extension setup. The Runtime SDK already has OpenTelemetry + OpenAI Agents SDK tracing support in `jazzx_sdk/tracing.py`. The Agent Execution Layer creates the single integration point:

- Every `AgentExecutionTrace` can optionally emit to MLflow (experiment tracking), OpenTelemetry (distributed tracing), or both, based on pack/environment config
- Extension code never configures MLflow directly - the Runtime SDK handles it
- Experiment metadata (model, prompt_version, pack_id, case_id) flows automatically from the execution context
- Cost-per-case and cost-per-mode become queryable without extension-level instrumentation

This replaces the current pattern where each extension sets up its own MLflow tracking, its own `TraceHooks` class, and its own `compute_cost_from_metrics()` calls.

### 6.3 Relationship to Canonical Trace

The canonical `CanonicalTrace` (Schema Spec section 5) captures mode-level execution steps. Each `TraceStep` records which mode ran, what it consumed and produced, and how long it took. But `TraceStep` does not capture LLM-level detail - how many LLM calls happened inside that mode invocation, what tokens were consumed, whether structured output parsing required retries.

`AgentExecutionTrace` fills this gap as sub-step detail. The relationship is:

```
CanonicalTrace (one per workflow execution)
  └── TraceStep[] (one per mode invocation)
        └── AgentExecutionTrace[] (one per LLM call within that mode)
```

A single `TraceStep` (actor: "investigator", action: "hypothesis_update") may trigger multiple LLM calls (initial generation, tool-use loop iterations, structured output retry). Each of those is an `AgentExecutionTrace` linked to the parent `TraceStep` via `step_id`.

This means:

- **Examiners** see the `CanonicalTrace` - process-level steps, decisions, overrides
- **Operators** see `AgentExecutionTrace` - cost, latency, token usage, cache hit rates
- **The EVOLVE loop** sees both - process-level outcomes linked to LLM-level execution patterns for learning

The `TraceStep` schema already has `model_version` (optional) and `duration_ms`. The Schema Spec also defines `tools_invoked` on `TraceStep`. The Agent Execution Layer populates these fields automatically from the `AgentExecutionTrace` data, so mode implementations don't need to track them manually.

---

## 7. Core Interfaces

### 7.1 AgentProvider Protocol

```python
from typing import Protocol, Any
from pydantic import BaseModel

class AgentProvider(Protocol):
    """Contract every provider adapter must satisfy."""

    provider_name: str  # "openai", "anthropic", etc.

    async def run(
        self,
        model: str,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        output_schema: type[BaseModel] | None = None,
        tool_executor: Callable | None = None,
        **provider_kwargs,
    ) -> AgentResult: ...

    def format_tools(
        self,
        tool_definitions: list[dict],
    ) -> list[dict]: ...

    def get_supported_features(self) -> set[str]: ...
```

### 7.2 AgentResult

```python
@dataclass
class AgentResult:
    output: Any                      # parsed Pydantic model or raw text
    raw_response: dict               # provider's raw response (for audit)
    trace: AgentExecutionTrace       # full execution trace
    provider: str
    model: str
```

### 7.3 AgentExecutionService (the `ctx.runtime.agents` surface)

```python
class AgentExecutionService:
    """Platform-provided agent execution."""

    # Generic tier
    async def run(self, *, system_prompt, messages, tools=None,
                  output_schema=None, provider=None, model=None,
                  tool_executor=None, **kwargs) -> AgentResult: ...

    # Provider-specific tier
    @property
    def openai(self) -> OpenAIProvider: ...

    @property
    def anthropic(self) -> AnthropicProvider: ...

    # Governance hooks
    def register_hook(self, stage: str, hook: Callable) -> None: ...

    # Administration
    def get_available_providers(self) -> list[str]: ...
    def get_provider_features(self, provider: str) -> set[str]: ...
```

---

## 8. Migration Path

### 8.1 Phase 1 - Consolidation (extract what exists)

**Goal:** Move existing adapter code into the Runtime SDK.

- Extract JACI-KYC's `AnthropicAdapter` (268 lines) → `jazzx_sdk/agents/anthropic_provider.py`
- Extract OpenAI Agents SDK patterns from MACER/JACI-AML → `jazzx_sdk/agents/openai_provider.py`
- Create `AgentProvider` protocol, `AgentResult`, `AgentExecutionTrace` in `jazzx_sdk/agents/base.py`
- Wire `ctx.runtime.agents` into `HandlerContext`
- Add `AgentExecutionTrace` to Postgres tracing

**Acceptance criteria:**

- JACI-KYC runs with zero `anthropic` imports in its own code
- JACI-AML runs with zero `openai-agents` imports in its own code
- Both produce `AgentExecutionTrace` visible in platform traces
- All existing tests pass unchanged

### 8.2 Phase 2 - Governance hooks + provider-specific features

- Implement pre-call / post-call hook engine
- Add Anthropic-specific: extended thinking capture, prompt caching metrics
- Add OpenAI-specific: agent handoff mapping to mode transitions
- Wire Governor and Sentinel as default platform hooks
- Cost metering from execution traces

**Acceptance criteria:**

- Governor can block a mode call if autonomy ceiling is exceeded
- Sentinel receives all execution traces and can flag anomalies
- Cost per pack/mode/case is queryable from trace data

### 8.3 Phase 3 - Third provider + validation

- Add Gemini provider (validates that `AgentProvider` protocol is genuinely open)
- Pack manifest `runtime` section formalized
- Model upgrade can be done centrally (change pack config, zero code changes in extensions)

**Acceptance criteria:**

- A third provider works end-to-end without changes to the `AgentExecutionLayer` core
- MACER, K9, Juno migrated to `ctx.runtime.agents` (or migration path documented)

---

## 9. Extension Dependency Impact

### Before

```
# JACI-AML pyproject.toml
openai-agents>=0.6.1

# JACI-KYC pyproject.toml
anthropic>=0.25.0

# MACER pyproject.toml
openai-agents>=0.6.1

# K9 pyproject.toml
openai-agents>=0.6.1
```

### After

```
# All extensions: pyproject.toml
jazzx-runtime-sdk>=1.2.0   # includes agents layer
# No LLM SDK dependencies in extension code
```

The Runtime SDK bundles provider SDKs (or uses extras: `jazzx-runtime-sdk[openai,anthropic]`). The extension's container image gets the right SDK because the Runtime SDK includes it.

---

## 10. Relationship to Existing SDK Lines

| SDK Line | Version | Relationship to Agent Execution Layer |
| --- | --- | --- |
| Canonical Objects (0.2.x) | Stable | Execution traces link to canonical `Trace` objects via `trace_id` |
| Cognitive Modes (0.3.x) | Stable | Modes call `ctx.runtime.agents.run()` instead of constructing SDK clients |
| Universal Tools (0.4.x) | Stable | `BaseToolRegistry` output fed directly to Agent Execution Service; format translation handled internally |
| Expert Layer (0.5.0) | Stable | Experts compose modes; execution traces aggregate across expert operations |
| **Agent Execution (NEW)** | **0.6.x target** | **This spec** |

---

## 11. What This Proves (v2.0 Claims)

| v2.0 Claim | How this validates it |  |  |
| --- | --- | --- | --- |
| Agent Framework Adapter | `AgentProvider` protocol + OpenAI/Anthropic providers = the adapter layer is real code, not a diagram |  |  |
| No vendor lock-in | Generic tier is provider-portable; switching is a config change |  |  |
| Unified tracing | Every LLM call traced uniformly regardless of provider |  |  |
| Governed execution | Pre/post hooks give Governor, Sentinel, Evaluator visibility into every call |  |  |
| EVOLVE loop depth | Process-level execution data (not just outcomes) feeds Evaluator and Curator |  |  |
| Per-task routing | Pack manifest can route different modes to different providers/models |  |  |

---

## 12. Open Questions

1. **Streaming.** Should the generic tier support streaming responses, or is that provider-specific only? Streaming complicates structured output enforcement and governance hooks.
2. **Tool execution ownership.** Who executes the tool when the LLM returns a tool call - the Agent Execution Layer (using `tool_executor` callback) or the mode itself? The former is cleaner for tracing; the latter gives modes more control.
3. **Multi-agent patterns.** OpenAI Agents SDK has native multi-agent handoffs. Should the generic tier support a multi-agent pattern, or is that always provider-specific? Relates to how Conductor orchestration maps to agent-level handoffs.
4. **Extras vs bundled.** Should provider SDKs be bundled in the Runtime SDK or installed as extras (`jazzx-runtime-sdk[openai]`)? Bundled is simpler; extras keep container images smaller when a pack only needs one provider.
5. **EVOLVE loop integration depth.** How deeply should execution traces feed the Curator? Should the Curator be able to modify prompts based on execution trace patterns, or only surface signals for human review?

---

## 13. Implementation Task Spec

When this design is approved, the implementation task is:

1. Create `jazzx_sdk/agents/` module with `base.py`, `openai_provider.py`, `anthropic_provider.py`
2. Implement `AgentProvider` protocol, `AgentResult`, `AgentExecutionTrace`
3. Wire `AgentExecutionService` into `HandlerContext` as `ctx.runtime.agents`
4. Migrate JACI-KYC's `AnthropicAdapter` into `anthropic_provider.py`
5. Create OpenAI provider wrapping `openai-agents` patterns from MACER/JACI-AML
6. Add execution trace integration with existing Postgres tracing
7. Unit tests for both providers (structured output, tool format translation, trace capture)
8. Update `CHANGELOG.md` and `README.md`

**Estimated scope:** ~600-800 lines of new code + tests. Most is extraction/consolidation of existing adapter code, not greenfield.

**Branch:** `feature/agent-execution-service` from `dev`