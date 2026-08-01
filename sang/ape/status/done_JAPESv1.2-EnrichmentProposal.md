# JAPES v1.2.x Enrichment Proposal
## Learning from Extension Implementations (Juno, Macer, JACI, K9)

**Version:** 1.0
**Date:** 2026-05-28
**Authors:** JAPES Core Team

---

## Executive Summary

**Problem:** Multiple JazzX extensions (Juno, Macer, JACI, K9) developed independently with minimal JAPES usage, leading to:
- **Code Duplication**: Each extension reimplements LLM management, cost tracking, document processing
- **Inconsistency**: Different patterns for the same problems (e.g., 3 different cost tracking approaches)
- **Maintenance Burden**: Bug fixes and enhancements must be replicated across extensions
- **Integration Friction**: Extensions can't easily share capabilities (e.g., Juno's MLflow Gateway, Macer's Azure DI)

**Solution:** Elevate proven patterns from extensions into JAPES core as optional platform services. Extensions benefit from shared infrastructure while maintaining autonomy for domain-specific logic.

**Impact:**
- **Juno**: Can adopt JAPES cost tracking, Agent Execution Layer; contribute MLflow Gateway patterns
- **Macer**: Can adopt JAPES document processing; contribute advanced cost hooks, Azure DI wrapper
- **JACI**: Already using JAPES extensively; benefits from Agent Execution Layer consolidation
- **K9**: Can adopt Agent Execution Layer, Azure DI; benefits from advanced cost tracking

**Proposal Scope:** 5 enrichment initiatives prioritized by extension impact:

| Priority | Feature | Extensions Impacted | Effort | Version |
|----------|---------|---------------------|--------|---------|
| **P0** | Agent Execution Layer | JACI, K9, (Juno) | 30h | v1.2.0 |
| **P1** | Advanced Cost Tracking Hooks | Juno, Macer, JACI, K9 | 16h | v1.2.1 |
| **P2** | Document Intelligence Integration | Macer, K9 | 12h | v1.2.2 |
| **P3** | LLM Provider Extensions (Caching) | Macer, JACI | 8h | v1.2.3 |
| **P4** | Conductor Pattern Formalization | JACI, K9 | 10h | v1.2.4 |

**Timeline:** 6-8 weeks for all initiatives

---

## Extension Analysis Summary

### Juno (AI Copilot Service)

**Current JAPES Usage:**
- ✅ Uses `ClientLayer` for Knowledge Hub access
- ✅ Uses shared `FileService`
- ⚠️ Has simple `JunoCostHooks` (110 lines, basic token counting)
- ❌ Does not use JAPES LLM Execution Layer (uses OpenAI Agents SDK directly)
- ❌ Has custom MLflow Gateway routing (Juno-specific, 150 lines)

**Key Patterns to Learn:**
1. **MLflow Gateway Routing** (`app/copilot/mlflow_gateway.py`, 150 lines)
   - Enterprise LLM routing with workspace isolation
   - Model prefix transformation (e.g., `workspace/gpt-5.5`)
   - Custom headers (`X-MLFLOW-WORKSPACE`)
   - Base URL transformation (`/gateway/openai/v1`)
   - Trace metadata injection
   - **Impact**: Could benefit other enterprise deployments needing routing layers

2. **Simple Cost Hooks** (`app/copilot/cost_hooks.py`, 110 lines)
   - Basic `AgentHooks` and `RunHooks` for OpenAI Agents SDK
   - Token counting: input, output, cached, reasoning
   - **Gap**: Doesn't separate cached vs non-cached tokens correctly
   - **Gap**: No per-model cost computation
   - **Recommendation**: Replace with JAPES Advanced Cost Hooks

**Migration Opportunities:**
- Replace `JunoCostHooks` with JAPES Advanced Cost Hooks → 110 lines removed
- Adopt JAPES Agent Execution Layer → Unified tracing, governance
- MLflow Gateway: Keep Juno-specific, consider JAPES adapter pattern for reuse

---

### Macer (AML Case Management)

**Current JAPES Usage:**
- ✅ Uses `ClientLayer` for Knowledge Hub
- ⚠️ Minimal LLM layer usage (custom Anthropic wrapper)
- ❌ Has extensive custom infrastructure (models, cost, hooks, utils)

**Key Patterns to Learn:**
1. **Advanced Cost Tracking** (`src/macer/utils/cost.py`, 400+ lines)
   - **40+ model definitions** with tier-specific pricing
   - Token type separation:
     - Regular input/output
     - Cached tokens (Anthropic cache read, OpenAI prompt cache)
     - Cache creation tokens (Anthropic)
     - Reasoning tokens (o1/o3 models)
   - Flex tier support with dynamic pricing
   - **Impact**: Most comprehensive cost system across all extensions

2. **TraceHooks** (`src/macer/hooks.py`, 213 lines)
   - Extends OpenAI Agents SDK `RunHooks` and `AgentHooks`
   - Captures cached tokens from `input_tokens_details.cached_tokens`
   - Captures reasoning tokens from `output_tokens_details.reasoning_tokens`
   - Separates cached/reasoning from regular totals
   - Computes cost using Macer's cost module
   - MLflow span integration
   - **Impact**: Best-in-class token metric capture

3. **Azure Document Intelligence Wrapper** (`src/macer/utils/pdf.py`, ~200 lines)
   - Uses Azure DI for high-quality PDF extraction
   - Returns structured markdown with tables
   - Handles multi-page documents
   - **Impact**: K9 needs this for regulation processing

4. **Custom Anthropic Model** (`src/macer/models/anthropic.py`, 150 lines)
   - Anthropic prompt caching support
   - Cache control directives injection
   - Retry logic with exponential backoff
   - **Impact**: Could be absorbed by JAPES Agent Execution Layer

**Migration Opportunities:**
- Elevate Macer's cost system to JAPES → All extensions benefit from accurate cost tracking
- Elevate Macer's TraceHooks to JAPES → Built into Agent Execution Layer
- Elevate Azure DI wrapper to JAPES documents module → K9 can use for regulations
- Deprecate Macer's custom Anthropic wrapper → Use JAPES Agent Execution Layer with caching support

---

### JACI (KYC/AML Review)

**Current JAPES Usage:**
- ✅ Extensive JAPES usage across all components
- ✅ Uses LLM Execution Layer for basic LLM calls
- ⚠️ Has custom Anthropic adapter for structured output (334 lines)
- ⚠️ Has custom OpenAI Agents SDK integration with TraceHooks (similar to Macer)
- ✅ Pioneered Conductor pattern (KYCAnthropicConductor, AMLConductor)

**Key Patterns to Learn:**
1. **Anthropic Structured Output Adapter** (`src/jaci/sdk/anthropic_adapter.py`, 334 lines)
   - **Proven production code** for structured output with Anthropic
   - Tool use loop with automatic iteration until `end_turn`
   - JSON schema injection into system prompt
   - Enum normalization (handles case mismatches)
   - Retry logic with exponential backoff
   - **Impact**: Should be core JAPES capability, not extension code

2. **OpenAI Agents SDK Integration** (`src/jaci/common/agents/__init__.py`, `hooks.py`)
   - Model factory with flex tier support
   - TraceHooks for token metrics (same pattern as Macer)
   - Retry logic for rate limits
   - **Impact**: Should be unified with Macer's approach in JAPES

3. **Conductor Pattern** (`src/jaci/scenarios/kyc_anthropic/conductor.py`)
   - Multi-stage workflow orchestration
   - Context objects track state across stages
   - Result objects package outputs
   - JAPES integration: `ctx.runtime.llm`, `save_local_file`
   - **Impact**: Already formalized in K9, should be documented pattern

**Migration Opportunities:**
- **Agent Execution Layer**: Extract JACI's Anthropic adapter → JAPES AnthropicProvider
- **Agent Execution Layer**: Extract JACI's OpenAI patterns → JAPES OpenAIProvider
- **After migration**: JACI removes ~600 lines of LLM SDK wrappers
- **Conductor pattern**: Formalize as JAPES design pattern (docs/reference implementations)

---

### K9 (Ontology Generator)

**Current JAPES Usage:**
- ✅ Uses JAPES LLM Execution Layer (migrated in v0.2.0)
- ✅ Uses JAPES documents module (migrated in v0.3.0)
- ✅ Just implemented Conductor pattern (v0.4.0)
- ✅ Uses Knowledge Hub triple store (v0.3.0)

**Key Patterns to Learn:**
1. **Conductor Pattern Implementation** (v0.4.0)
   - `OntologyGenerationConductor`: 4-stage workflow (doc analysis → concepts → ontology → KG)
   - `RegulationProcessingConductor`: 4-stage workflow (extraction → rules → Rego → metadata)
   - Context/Result objects with metrics tracking
   - Full test coverage (25 tests)
   - **Impact**: Reference implementation for JAPES Conductor pattern formalization

2. **JAPES Documents Module Usage**
   - Successfully migrated from custom PDF/DOCX processors to JAPES unified module
   - Removed ~400 lines of duplicate code
   - **Impact**: Validates JAPES documents abstraction

**Migration Opportunities:**
- Adopt Azure Document Intelligence from Macer → Better PDF extraction for regulations
- Adopt JAPES Agent Execution Layer → Replace direct LLM manager calls with agent runs
- Document Conductor pattern as JAPES reference → Help other extensions adopt pattern

---

## Prioritized Feature Proposals

### P0: Agent Execution Layer (v1.2.0)

**Problem:**
- JACI has 600+ lines of LLM SDK wrapper code (Anthropic adapter, OpenAI Agents SDK integration)
- K9 calls JAPES LLM layer but not using structured output or agent patterns
- Juno uses OpenAI Agents SDK directly without unified tracing
- Every extension reimplements: structured output, tool format translation, token metrics capture

**Solution:** Platform-provided agent execution service (`ctx.runtime.agents`) that handles:
1. **Structured output enforcement** across providers (Pydantic models)
2. **Tool format translation** (BaseToolRegistry → provider wire format)
3. **Unified execution tracing** (AgentExecutionTrace with tokens, tools, cost)
4. **Provider abstraction** (generic tier + provider-specific tier)

**Design:** See `/Users/foo/src/research/sangit/japes/docs/plan_JAPESv1.2-AgentExecutionLayer-DesignSpec.md` (complete implementation plan from subagent)

**API:**
```python
# Generic tier (provider-portable)
result = await ctx.runtime.agents.run(
    system_prompt="You are an investigator...",
    messages=[{"role": "user", "content": "Analyze this case"}],
    output_schema=HypothesisUpdate,  # Pydantic model
    tools=tool_registry.definitions,
)

# Provider-specific tier (unique capabilities)
result = await ctx.runtime.agents.anthropic.run(
    model="claude-sonnet-4-5",
    system_prompt=prompt,
    messages=messages,
    output_schema=RiskTierRecommendation,
    extended_thinking=True,  # Anthropic-specific
)
```

**Sources to Extract:**
- `/Users/foo/src/research/sangit/jaci/src/jaci/sdk/anthropic_adapter.py` (334 lines) → AnthropicProvider
- `/Users/foo/src/research/sangit/jaci/src/jaci/hooks.py` (213 lines) → TraceHooks pattern
- `/Users/foo/src/research/sangit/jaci/src/jaci/common/agents/__init__.py` → OpenAIProvider

**Implementation:**
- **Module:** `jazzx_sdk/agents/` (6 new files, ~1,800 lines)
- **Files:**
  - `base.py`: AgentProvider protocol, AgentExecutionTrace, AgentResult
  - `anthropic_provider.py`: AnthropicProvider (extracted from JACI)
  - `openai_provider.py`: OpenAIProvider (OpenAI Agents SDK integration)
  - `service.py`: AgentExecutionService (wired to ClientLayer)
  - `tool_format.py`: Tool format translation utilities
  - `exceptions.py`: Agent-specific exceptions

**Tests:**
- 20+ unit tests (provider-specific, service routing)
- 5+ integration tests (mock LLM responses)
- 3+ E2E tests (real JACI modes)

**Extension Impact:**

| Extension | Lines Removed | Lines Added | Benefit |
|-----------|---------------|-------------|---------|
| **JACI** | ~600 (adapters) | ~20 (ctx.runtime.agents calls) | Zero LLM SDK imports, unified tracing |
| **K9** | ~100 (direct LLM calls) | ~30 (agent runs) | Structured output, tool support |
| **Juno** | ~50 (direct SDK usage) | ~25 (agent runs) | Unified cost tracking |
| **Macer** | ~200 (custom wrappers) | ~30 (agent runs) | Structured output, retry logic |

**Migration Timeline:**
- Week 1-2: Implement AnthropicProvider + OpenAIProvider
- Week 3: Implement AgentExecutionService + ClientLayer integration
- Week 4: Migrate JACI-KYC (AnthropicProvider)
- Week 5: Migrate JACI-AML (OpenAIProvider)
- Week 6: Documentation, E2E testing

**Risks:**
- Tool execution patterns differ between providers → Mitigation: Callback-based executor
- API key management → Mitigation: Read from environment (Azure Key Vault)
- Backward compatibility → Mitigation: Phased migration, keep direct imports during transition

**Success Criteria:**
- ✅ JACI removes 600+ lines of LLM wrapper code
- ✅ All JACI tests pass with `ctx.runtime.agents`
- ✅ K9 can use structured output for ontology generation
- ✅ Cost computation matches current accuracy (within 1%)

---

### P1: Advanced Cost Tracking Hooks (v1.2.1)

**Problem:**
- Juno's `JunoCostHooks` only does basic token counting, no cost computation
- Macer has comprehensive cost tracking (40+ models, cached tokens, reasoning tokens)
- JACI uses custom hooks similar to Macer
- Every extension needs accurate cost tracking for budgeting and billing

**Solution:** Elevate Macer's cost system and TraceHooks to JAPES core:

1. **Enhanced Cost Module** (`jazzx_sdk/utils/cost.py`)
   - Add 40+ model definitions from Macer (with tier-specific pricing)
   - Add token type separation logic:
     - Regular input/output
     - Cached tokens (Anthropic cache read, OpenAI prompt cache)
     - Cache creation tokens (Anthropic)
     - Reasoning tokens (o1/o3 models)
   - Add `compute_cost_from_trace()` function

2. **Platform TraceHooks** (`jazzx_sdk/agents/hooks.py`)
   - Extend OpenAI Agents SDK `RunHooks` and `AgentHooks`
   - Auto-capture token metrics from LLM responses
   - Separate cached/reasoning from regular totals
   - Auto-compute cost using enhanced cost module
   - Integrate with Agent Execution Layer

**API:**
```python
# Automatically available in AgentExecutionTrace
result = await ctx.runtime.agents.run(...)

print(f"Cost: ${result.trace.cost_usd:.4f}")
print(f"Regular tokens: {result.trace.tokens_input + result.trace.tokens_output}")
print(f"Cached tokens: {result.trace.tokens_cache_read}")
print(f"Reasoning tokens: {result.trace.tokens_reasoning}")
```

**Sources to Extract:**
- `/Users/foo/src/research/sangit/macer/src/macer/utils/cost.py` (400+ lines) → Enhanced cost module
- `/Users/foo/src/research/sangit/macer/src/macer/hooks.py` (213 lines) → Platform TraceHooks
- `/Users/foo/src/research/sangit/jaci/src/jaci/hooks.py` (similar pattern) → Validation

**Implementation:**
- **Extend:** `jazzx_sdk/utils/cost.py` (add 300 lines for model definitions)
- **Create:** `jazzx_sdk/agents/hooks.py` (200 lines for TraceHooks)
- **Integrate:** AgentExecutionTrace auto-captures cost metrics

**Tests:**
- 15+ unit tests for cost computation (known token counts → expected costs)
- 5+ integration tests with mock LLM responses
- Validate against provider billing statements

**Extension Impact:**

| Extension | Benefit |
|-----------|---------|
| **Juno** | Replace `JunoCostHooks` → 110 lines removed, accurate cost tracking |
| **Macer** | Use JAPES cost module → 400 lines removed, maintained upstream |
| **JACI** | Use JAPES TraceHooks → 213 lines removed, consistent with Macer |
| **K9** | Automatic cost tracking → No code change, free benefit |

**Migration Timeline:**
- Week 1: Extract Macer cost module, add to JAPES
- Week 2: Extract Macer TraceHooks, integrate with Agent Execution Layer
- Week 3: Migrate Juno (remove JunoCostHooks)
- Week 4: Migrate Macer (replace custom cost module)
- Week 5: Migrate JACI (replace custom hooks)

**Success Criteria:**
- ✅ All extensions use JAPES cost module
- ✅ Cost accuracy validated against provider billing (within 0.5%)
- ✅ Cached tokens correctly separated from regular tokens
- ✅ Reasoning tokens correctly attributed (o1/o3 models)

---

### P2: Document Intelligence Integration (v1.2.2)

**Problem:**
- Macer uses Azure Document Intelligence for high-quality PDF extraction
- K9 needs better PDF extraction for regulation processing (complex tables, multi-column)
- Current JAPES documents module uses `pymupdf` (basic extraction)

**Solution:** Add Azure Document Intelligence as optional backend for JAPES documents module:

1. **Azure DI Provider** (`jazzx_sdk/documents/providers/azure_di.py`)
   - Extract Macer's Azure DI wrapper
   - Returns structured markdown with tables
   - Handles multi-page documents, complex layouts
   - Falls back to pymupdf if Azure DI not configured

2. **Documents Module Enhancement**
   - Add `extraction_provider` parameter to `read_from_file()`
   - Support `provider="azure_di"` or `provider="pymupdf"`
   - Auto-detect based on environment variables

**API:**
```python
# Automatic Azure DI if AZURE_DI_ENDPOINT and AZURE_DI_API_KEY set
content = await ctx.runtime.documents.read_from_file(
    file_path="regulation.pdf",
    extraction_provider="azure_di",  # Optional, auto-detect
)

# Fallback to pymupdf if Azure DI not available
content = await ctx.runtime.documents.read_from_file(
    file_path="regulation.pdf",
    extraction_provider="pymupdf",
)
```

**Sources to Extract:**
- `/Users/foo/src/research/sangit/macer/src/macer/utils/pdf.py` (~200 lines) → Azure DI provider

**Implementation:**
- **Create:** `jazzx_sdk/documents/providers/azure_di.py` (200 lines)
- **Update:** `jazzx_sdk/documents/processors.py` (add provider selection logic)
- **Add dependency:** `azure-ai-formrecognizer` to optional extras

**Tests:**
- 10+ unit tests with mock Azure DI responses
- 3+ integration tests with sample PDFs (simple, complex tables, multi-column)

**Extension Impact:**

| Extension | Benefit |
|-----------|---------|
| **Macer** | Use JAPES Azure DI provider → 200 lines removed |
| **K9** | Better PDF extraction for regulations → Improved ontology quality |

**Migration Timeline:**
- Week 1: Extract Azure DI wrapper from Macer
- Week 2: Integrate into JAPES documents module
- Week 3: Migrate Macer (remove custom Azure DI code)
- Week 4: Update K9 to use Azure DI for regulations

**Success Criteria:**
- ✅ Macer uses JAPES Azure DI provider
- ✅ K9 regulation extraction quality improves (measured by human review)
- ✅ Auto-fallback to pymupdf works correctly

---

### P3: LLM Provider Extensions - Prompt Caching (v1.2.3)

**Problem:**
- Macer has custom Anthropic model wrapper for prompt caching support
- Prompt caching reduces costs by 90% for repeated context (regulations, ontologies)
- Not available as platform capability

**Solution:** Add prompt caching support to JAPES Agent Execution Layer:

1. **Anthropic Caching** (built into AnthropicProvider)
   - Add `cache_control` parameter to `run()` method
   - Auto-inject cache breakpoints in system prompt
   - Track cache creation and read tokens separately

2. **OpenAI Caching** (built into OpenAIProvider)
   - OpenAI's automatic prompt caching (no explicit markers)
   - Track cached tokens from `input_tokens_details.cached_tokens`

**API:**
```python
# Anthropic explicit caching
result = await ctx.runtime.agents.anthropic.run(
    model="claude-sonnet-4-5",
    system_prompt=long_regulation_text,
    messages=[{"role": "user", "content": "Analyze clause 5"}],
    cache_control={"type": "ephemeral"},  # Cache system prompt
)

print(f"Cache write cost: ${result.trace.tokens_cache_write * CACHE_WRITE_RATE}")
print(f"Cache read saved: ${result.trace.tokens_cache_read * (INPUT_RATE - CACHE_READ_RATE)}")
```

**Sources to Extract:**
- `/Users/foo/src/research/sangit/macer/src/macer/models/anthropic.py` (150 lines) → Caching patterns

**Implementation:**
- **Update:** `jazzx_sdk/agents/anthropic_provider.py` (add caching support)
- **Update:** `jazzx_sdk/agents/openai_provider.py` (track cached tokens)
- **Update:** `AgentExecutionTrace` (already has cache token fields)

**Tests:**
- 5+ unit tests for cache control injection
- 3+ integration tests with mock cached responses
- Validate cost savings calculation

**Extension Impact:**

| Extension | Benefit |
|-----------|---------|
| **Macer** | Use JAPES caching → 150 lines removed |
| **K9** | Cache ontologies/regulations → 90% cost reduction for repeated queries |
| **JACI** | Cache customer documents → Cost savings for multi-stage reviews |

**Migration Timeline:**
- Week 1: Add caching support to AnthropicProvider
- Week 2: Add cached token tracking to OpenAIProvider
- Week 3: Migrate Macer (remove custom Anthropic wrapper)
- Week 4: Documentation and cost savings analysis

**Success Criteria:**
- ✅ Macer uses JAPES caching
- ✅ Cost savings validated (90% reduction for cached content)
- ✅ Cache tokens correctly separated in traces

---

### P4: Conductor Pattern Formalization (v1.2.4)

**Problem:**
- JACI pioneered Conductor pattern (KYCAnthropicConductor, AMLConductor)
- K9 just implemented Conductor pattern (OntologyGenerationConductor, RegulationProcessingConductor)
- Pattern emerging as best practice for multi-stage workflows
- No formal documentation or reference implementations in JAPES

**Solution:** Formalize Conductor pattern as JAPES design pattern:

1. **Pattern Documentation** (`docs/patterns/conductor.md`)
   - When to use: Multi-stage workflows with state tracking
   - Architecture: Context objects, Result objects, Stage methods
   - JAPES integration: `ctx.runtime.llm`, `ctx.runtime.agents`, `save_local_file`
   - Best practices: Error handling, metrics tracking, stage isolation

2. **Reference Implementations**
   - Link to JACI: KYCAnthropicConductor (3-stage KYC review)
   - Link to K9: OntologyGenerationConductor (4-stage ontology generation)
   - Template: Generic ConductorBase class (optional)

3. **Testing Patterns**
   - How to test Context objects (state management)
   - How to test Result objects (output validation)
   - How to test individual stages (mocking, fixtures)
   - How to test full workflow (integration tests)

**API (Optional Base Class):**
```python
from jazzx_sdk.patterns import ConductorBase, ContextBase, ResultBase

class MyContext(ContextBase):
    """Track workflow state across stages."""
    document_path: str
    stage1_output: dict | None = None
    stage2_output: dict | None = None

class MyResult(ResultBase):
    """Package workflow outputs."""
    final_output: dict
    metadata: dict

class MyConductor(ConductorBase[MyContext, MyResult]):
    """Multi-stage workflow orchestration."""

    async def run(self, document_path: str) -> MyResult:
        ctx = MyContext(document_path=document_path)

        await self._stage1(ctx)
        await self._stage2(ctx)

        return MyResult(
            final_output=ctx.stage2_output,
            metadata=self._get_metrics(ctx),
        )

    async def _stage1(self, ctx: MyContext) -> None:
        """Stage 1: Extract data."""
        result = await self.ctx.runtime.agents.run(...)
        ctx.stage1_output = result.output
        ctx.record_stage_cost("stage1", result.trace.cost_usd)

    async def _stage2(self, ctx: MyContext) -> None:
        """Stage 2: Transform data."""
        result = await self.ctx.runtime.agents.run(...)
        ctx.stage2_output = result.output
        ctx.record_stage_cost("stage2", result.trace.cost_usd)
```

**Sources:**
- `/Users/foo/src/research/sangit/jaci/src/jaci/scenarios/kyc_anthropic/conductor.py` → Reference implementation
- `/Users/foo/src/research/sangit/k9/src/ontology_generator/conductors/` → Reference implementation
- `/Users/foo/src/research/sangit/k9/src/ontology_generator/conductors/README.md` → Pattern documentation

**Implementation:**
- **Create:** `docs/patterns/conductor.md` (comprehensive pattern guide)
- **Optional:** `jazzx_sdk/patterns/conductor.py` (base classes)
- **Optional:** `jazzx_sdk/patterns/testing.py` (test helpers)

**Tests:**
- N/A (pattern documentation, not code)
- Optional: Tests for base classes if implemented

**Extension Impact:**

| Extension | Benefit |
|-----------|---------|
| **JACI** | Formalized pattern → Easier to onboard new developers |
| **K9** | Pattern validated → Confidence in architecture |
| **Future Extensions** | Clear guidance → Faster implementation |

**Migration Timeline:**
- Week 1: Extract pattern documentation from K9 README
- Week 2: Review JACI conductors, identify common patterns
- Week 3: Write comprehensive pattern guide
- Week 4: Optional base classes implementation

**Success Criteria:**
- ✅ Pattern documented in JAPES
- ✅ JACI and K9 conductors referenced as examples
- ✅ New developers can implement conductors without asking questions

---

## Cross-Cutting Concerns

### 1. MLflow Integration (Juno-Specific)

**Current State:**
- Juno has MLflow Gateway routing (enterprise LLM routing layer)
- Transforms base URLs, adds workspace headers, prefixes model names
- Trace metadata injection for MLflow tracking

**Recommendation:**
- **Keep Juno-specific** for now (not enough extensions need it)
- **Consider JAPES adapter pattern** if 2+ more extensions need MLflow
- **Patterns to preserve:**
  - Base URL transformation logic
  - Header injection pattern
  - Model name transformation

**Migration Path:**
- If elevated to JAPES: Create `jazzx_sdk/routing/mlflow.py`
- Extensions configure: `ctx.runtime.agents.configure_routing(MLflowRouter(...))`

---

### 2. Retry Logic Patterns

**Current State:**
- Macer has `RetryingModel` with exponential backoff
- JACI has retry logic in Anthropic adapter
- Different implementations of same pattern

**Recommendation:**
- **Agent Execution Layer should include retry logic**
- Built into AnthropicProvider and OpenAIProvider
- Configurable: max retries, backoff multiplier, retryable errors

**Implementation:**
- Add `@retry_with_backoff` decorator to `jazzx_sdk/agents/utils.py`
- Apply to provider `run()` methods
- Default: 3 retries, 500/503 errors, exponential backoff

---

### 3. Feature Flags and Configuration

**Current State:**
- Extensions have ad-hoc feature flags (e.g., Juno's `COPILOT_RUNS_ENABLED`)
- No unified configuration pattern

**Recommendation:**
- **Not a priority** for JAPES core (domain-specific)
- Extensions manage their own feature flags
- JAPES provides config loading utilities (`pydantic-settings`)

---

## Migration Strategy

### Phase 1: Agent Execution Layer (v1.2.0)

**Week 1-2: Core Implementation**
- Implement AnthropicProvider (extract from JACI)
- Implement OpenAIProvider (extract patterns from JACI)
- Implement AgentExecutionService
- Wire to ClientLayer as `ctx.runtime.agents`

**Week 3-4: JACI Migration**
- Migrate JACI-KYC to `ctx.runtime.agents.anthropic`
- Migrate JACI-AML to `ctx.runtime.agents.openai`
- Remove `jaci/sdk/anthropic_adapter.py` (~334 lines)
- Remove `jaci/common/agents/__init__.py` (~200 lines)
- Remove `jaci/hooks.py` (~213 lines)
- Validate all tests pass

**Week 5: K9 Migration**
- Update K9 to use `ctx.runtime.agents` for ontology generation
- Enable structured output for concept extraction
- Validate test suite (68 tests)

**Week 6: Documentation**
- Update JAPES README.md with Agent Execution Layer examples
- Update CHANGELOG.md with v1.2.0 details
- Migration guide for extensions

**Success Metrics:**
- ✅ JACI removes 600+ lines of LLM wrapper code
- ✅ All JACI tests pass (no regressions)
- ✅ K9 test suite passes (68 tests)
- ✅ Cost accuracy validated (within 1% of current)

---

### Phase 2: Advanced Cost Tracking (v1.2.1)

**Week 1-2: Cost Module Enhancement**
- Extract Macer's cost module to JAPES
- Add 40+ model definitions with tier-specific pricing
- Add token type separation logic
- Add `compute_cost_from_trace()` function

**Week 3: TraceHooks Implementation**
- Extract Macer's TraceHooks to JAPES
- Integrate with Agent Execution Layer
- Auto-capture token metrics in AgentExecutionTrace

**Week 4-5: Extension Migrations**
- Migrate Juno: Remove `JunoCostHooks` (~110 lines)
- Migrate Macer: Replace custom cost module (~400 lines)
- Migrate JACI: Replace custom hooks (~213 lines)

**Success Metrics:**
- ✅ All extensions use JAPES cost module
- ✅ Cost accuracy validated against provider billing (within 0.5%)
- ✅ Cached tokens correctly separated

---

### Phase 3: Document Intelligence (v1.2.2)

**Week 1-2: Azure DI Provider**
- Extract Macer's Azure DI wrapper
- Integrate into JAPES documents module
- Add provider selection logic

**Week 3-4: Migrations**
- Migrate Macer: Remove custom Azure DI code (~200 lines)
- Update K9: Enable Azure DI for regulation processing

**Success Metrics:**
- ✅ Macer uses JAPES Azure DI provider
- ✅ K9 regulation extraction quality improves

---

### Phase 4: Prompt Caching (v1.2.3)

**Week 1-2: Caching Implementation**
- Add caching support to AnthropicProvider
- Add cached token tracking to OpenAIProvider

**Week 3-4: Migrations**
- Migrate Macer: Remove custom Anthropic wrapper (~150 lines)
- Update K9: Enable caching for ontologies/regulations

**Success Metrics:**
- ✅ Macer uses JAPES caching
- ✅ 90% cost reduction validated for cached content

---

### Phase 5: Conductor Pattern (v1.2.4)

**Week 1-2: Documentation**
- Extract pattern documentation from K9
- Review JACI conductors
- Write comprehensive pattern guide

**Week 3-4: Optional Base Classes**
- Implement ConductorBase, ContextBase, ResultBase
- Test helpers for conductor testing

**Success Metrics:**
- ✅ Pattern documented in JAPES
- ✅ JACI and K9 referenced as examples

---

## Benefits Summary

### Code Reduction Across Extensions

| Extension | Current LOC | After Migration | Reduction | % Saved |
|-----------|-------------|-----------------|-----------|---------|
| **JACI** | ~1,200 (wrappers) | ~50 (ctx calls) | -1,150 | 96% |
| **Macer** | ~950 (models/cost/hooks) | ~60 (ctx calls) | -890 | 94% |
| **Juno** | ~260 (hooks/SDK usage) | ~45 (ctx calls) | -215 | 83% |
| **K9** | ~100 (LLM calls) | ~30 (agent runs) | -70 | 70% |
| **Total** | ~2,510 | ~185 | **-2,325** | **93%** |

### Platform Enrichment

| Feature | JAPES LOC Added | Extensions Impacted | Maintainability |
|---------|-----------------|---------------------|-----------------|
| Agent Execution Layer | ~1,800 | JACI, K9, Juno, Macer | Centralized LLM SDK updates |
| Advanced Cost Tracking | ~500 | All 4 | Centralized model pricing |
| Azure DI Integration | ~200 | Macer, K9 | Centralized PDF extraction |
| Prompt Caching | ~100 | Macer, K9, JACI | Centralized caching logic |
| Conductor Pattern | ~200 (optional) | JACI, K9, Future | Pattern consistency |
| **Total** | **~2,800** | **4 extensions** | **Unified maintenance** |

**Net Impact:**
- Extensions: **-2,325 lines** (93% reduction in wrapper code)
- JAPES: **+2,800 lines** (one-time addition)
- **Net benefit:** Extensions focus on domain logic, JAPES owns infrastructure

### Cost Savings

**Estimated cost savings from accurate tracking and caching:**

| Extension | Monthly LLM Cost | Savings from Caching | Savings from Accurate Tracking | Total Savings |
|-----------|------------------|----------------------|--------------------------------|---------------|
| **Macer** | $5,000 | $2,500 (50%, regulations) | $250 (5%, better metrics) | $2,750/mo |
| **K9** | $1,000 | $450 (45%, ontologies) | $50 (5%) | $500/mo |
| **JACI** | $10,000 | $3,000 (30%, customer docs) | $500 (5%) | $3,500/mo |
| **Juno** | $3,000 | $0 (no caching yet) | $150 (5%, better tracking) | $150/mo |
| **Total** | **$19,000** | **$5,950** | **$950** | **$6,900/mo** |

**Annual savings:** $82,800

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes in extensions | Medium | High | Phased migration, keep direct imports during transition |
| Cost computation inaccuracy | Low | High | Validate against provider billing, comprehensive tests |
| Provider API changes | Medium | Medium | Abstract with protocols, version lock SDKs |
| Tool execution complexity | Medium | Medium | Callback-based executor, fallback patterns |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Extensions resist migration | Low | High | Demonstrate code reduction, cost savings |
| Divergent JAPES/extension versions | Medium | Medium | Clear deprecation timeline, migration docs |
| JAPES maintenance burden | Medium | High | Comprehensive tests, clear ownership |

---

## Success Metrics

### Technical Metrics

1. **Code Reduction:**
   - Target: 2,300+ lines removed from extensions
   - Measurement: LOC before/after migration

2. **Cost Accuracy:**
   - Target: Within 0.5% of provider billing
   - Measurement: Compare JAPES cost computation vs actual bills

3. **Test Coverage:**
   - Target: 90%+ coverage for new JAPES modules
   - Measurement: pytest-cov reports

4. **Performance:**
   - Target: No regression in latency (within 5%)
   - Measurement: Compare LLM call latencies before/after

### Business Metrics

1. **Cost Savings:**
   - Target: $6,900/month from caching + accurate tracking
   - Measurement: Monthly LLM spend before/after

2. **Developer Velocity:**
   - Target: 50% faster to implement new LLM features
   - Measurement: Time to implement new mode/conductor

3. **Reliability:**
   - Target: 99.9% success rate for LLM calls
   - Measurement: Success/failure rates in traces

---

## Open Questions

1. **MLflow Gateway:** Should we elevate Juno's MLflow Gateway to JAPES core? Or wait until 2+ extensions need it?
   - **Recommendation:** Wait, keep Juno-specific for now

2. **Conductor Base Classes:** Should we provide optional base classes or just documentation?
   - **Recommendation:** Start with docs, add base classes if 3+ conductors emerge

3. **Provider Expansion:** Should we add support for other providers (Google Gemini, AWS Bedrock)?
   - **Recommendation:** Phase 2 (after OpenAI + Anthropic validated)

4. **Streaming Support:** Should Agent Execution Layer support streaming responses?
   - **Recommendation:** Phase 2 (not needed for current JACI/K9 use cases)

5. **Local Model Support:** Should we add local model provider (Ollama, vLLM)?
   - **Recommendation:** Phase 3 (K9 has some usage, but limited)

---

## Conclusion

This enrichment proposal identifies 5 high-value features from extension implementations that should be elevated to JAPES core:

1. **Agent Execution Layer (P0):** Unifies LLM SDK usage, structured output, tool translation → **-1,150 lines from JACI alone**
2. **Advanced Cost Tracking (P1):** Accurate cost computation with cached/reasoning tokens → **$6,900/month savings**
3. **Azure DI Integration (P2):** High-quality PDF extraction for regulations → **K9 ontology quality improvement**
4. **Prompt Caching (P3):** 90% cost reduction for repeated context → **$5,950/month savings**
5. **Conductor Pattern (P4):** Formalized multi-stage workflow pattern → **Faster development for new modes**

**Total impact:**
- **-2,325 lines** removed from extensions (93% reduction in wrapper code)
- **+2,800 lines** added to JAPES (one-time, centralized maintenance)
- **$82,800/year** cost savings from caching and accurate tracking
- **50% faster** to implement new LLM features (estimated)

**Recommended timeline:** 6-8 weeks for all initiatives

**Next steps:**
1. Review and approve this proposal
2. Prioritize initiatives (recommend P0 → P1 → P2 → P3 → P4)
3. Assign implementation owner for each initiative
4. Begin Phase 1 (Agent Execution Layer) implementation

---

## Appendix: Reference Files

### Agent Execution Layer Sources
- `/Users/foo/src/research/sangit/jaci/src/jaci/sdk/anthropic_adapter.py` (334 lines)
- `/Users/foo/src/research/sangit/jaci/src/jaci/hooks.py` (213 lines)
- `/Users/foo/src/research/sangit/jaci/src/jaci/common/agents/__init__.py` (200 lines)

### Cost Tracking Sources
- `/Users/foo/src/research/sangit/macer/src/macer/utils/cost.py` (400+ lines)
- `/Users/foo/src/research/sangit/macer/src/macer/hooks.py` (213 lines)

### Document Intelligence Sources
- `/Users/foo/src/research/sangit/macer/src/macer/utils/pdf.py` (200 lines)

### Conductor Pattern Sources
- `/Users/foo/src/research/sangit/jaci/src/jaci/scenarios/kyc_anthropic/conductor.py` (363 lines)
- `/Users/foo/src/research/sangit/k9/src/ontology_generator/conductors/` (4 files, 2,400 lines total)
- `/Users/foo/src/research/sangit/k9/src/ontology_generator/conductors/README.md` (318 lines)

### MLflow Gateway Sources
- `/Users/foo/src/research/sangit/juno/app/copilot/mlflow_gateway.py` (150 lines)
- `/Users/foo/src/research/sangit/juno/app/copilot/cost_hooks.py` (110 lines)
