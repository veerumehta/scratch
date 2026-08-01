# JAPES Enrichment - Focused Implementation Plan
## Priority: JAPES → JACI → K9 → Juno/Macer Proposal

**Version:** 1.0
**Date:** 2026-05-28
**Status:** Ready to implement

---

## Overview

This plan focuses on enriching **JAPES** first with patterns extracted from extensions we control (JACI, K9), then migrating those extensions to prove the value, and finally proposing changes to Juno/Macer.

**Phases:**
1. **Phase 1** (6 weeks): Enrich JAPES with Agent Execution Layer + Advanced Cost Tracking
2. **Phase 2** (2 weeks): Migrate JACI to use enriched JAPES
3. **Phase 3** (1 week): Migrate K9 to use enriched JAPES
4. **Phase 4** (1 week): Document benefits, create Juno/Macer proposal

**Total timeline:** 10 weeks

---

## Phase 1: Enrich JAPES (v1.2.0)
### Duration: 6 weeks

This phase extracts proven patterns from JACI and Macer into JAPES core.

### Week 1: Agent Execution Layer - Core Interfaces

**Goal:** Establish foundation for provider-agnostic agent execution

#### Tasks

**1.1: Create module structure**
```bash
cd /Users/foo/src/research/sangit/japes
mkdir -p jazzx_sdk/agents
touch jazzx_sdk/agents/__init__.py
touch jazzx_sdk/agents/base.py
touch jazzx_sdk/agents/exceptions.py
touch jazzx_sdk/agents/service.py
```

**1.2: Implement base.py**

Create:
- `AgentProvider` protocol (interface for all providers)
- `AgentExecutionTrace` dataclass (comprehensive execution metrics)
- `ToolCallRecord` dataclass (tool use tracking)
- `AgentResult` dataclass (unified result container)

Source reference: Design spec section 2 (Core Interfaces)

**1.3: Implement exceptions.py**

Create:
- `AgentExecutionError` (base exception)
- `ProviderError` (provider-specific failures)
- `StructuredOutputError` (parsing failures)
- `ToolExecutionError` (tool call failures)
- `RetryExhaustedError` (retry limit reached)

**1.4: Write initial tests**

Create:
```bash
mkdir -p tests/agents
touch tests/agents/__init__.py
touch tests/agents/conftest.py
touch tests/agents/test_base.py
```

Test:
- AgentExecutionTrace creation and serialization
- AgentResult structure
- ToolCallRecord validation

**Deliverables:**
- ✅ 3 new files in `jazzx_sdk/agents/`
- ✅ 3 new test files in `tests/agents/`
- ✅ ~400 lines of code
- ✅ 10+ unit tests passing

---

### Week 2: Agent Execution Layer - Anthropic Provider

**Goal:** Extract JACI's Anthropic adapter into JAPES

#### Tasks

**2.1: Extract AnthropicProvider**

Source: `/Users/foo/src/research/sangit/jaci/src/jaci/sdk/anthropic_adapter.py`

Create: `jazzx_sdk/agents/anthropic_provider.py`

Key patterns to preserve:
- Structured output via JSON schema injection
- Tool use loop (iterate until `stop_reason == "end_turn"`)
- Enum normalization helper
- Retry logic with exponential backoff
- JSON markdown fence stripping

**2.2: Adapt to AgentProvider protocol**

Changes from JACI version:
- Rename `AnthropicAdapter` → `AnthropicProvider`
- Add `provider_name = "anthropic"`
- Implement `format_tools()` method
- Create `AgentExecutionTrace` instead of returning raw metrics
- Use JAPES `compute_cost()` from `utils/cost.py`

**2.3: Add retry decorator**

Create: `jazzx_sdk/agents/utils.py`

Implement:
```python
@retry_with_backoff(
    max_retries=3,
    retryable_errors=(AnthropicAPIError,),
    backoff_multiplier=2.0,
)
async def run(...):
    ...
```

**2.4: Write provider tests**

Create: `tests/agents/test_anthropic_provider.py`

Test scenarios:
- Structured output parsing (happy path)
- Tool use loop (multiple iterations)
- Enum normalization (case mismatch handling)
- Retry logic (transient errors)
- Token metrics capture
- Cost computation accuracy

**Deliverables:**
- ✅ `anthropic_provider.py` (~450 lines)
- ✅ `utils.py` (retry decorator, ~80 lines)
- ✅ `test_anthropic_provider.py` (15+ tests)
- ✅ All tests passing with mock Anthropic client

---

### Week 3: Agent Execution Layer - OpenAI Provider

**Goal:** Extract JACI's OpenAI Agents SDK patterns into JAPES

#### Tasks

**3.1: Extract TraceHooks pattern**

Source: `/Users/foo/src/research/sangit/jaci/src/jaci/hooks.py`

Create internal class in `openai_provider.py`:
```python
class _RuntimeTraceHooks(RunHooks):
    """Internal hooks for capturing OpenAI Agents SDK metrics."""
```

Key patterns:
- Token metrics capture from `response.usage`
- Cached token extraction (`input_tokens_details.cached_tokens`)
- Reasoning token extraction (`output_tokens_details.reasoning_tokens`)
- Token separation (regular vs cached vs reasoning)
- Counter-based metrics accumulation

**3.2: Implement OpenAIProvider**

Create: `jazzx_sdk/agents/openai_provider.py`

Key features:
- OpenAI Agents SDK integration (`agents.Agent`, `agents.Runner`)
- Flex tier support (parse `flex_` prefix, extended timeout)
- Client pooling (separate clients for flex vs standard)
- Structured output via `AgentOutputSchema`
- TraceHooks integration for metrics
- Retry logic for rate limits

**3.3: Handle flex tier parsing**

Implement:
```python
def _parse_model_tier(self, model: str) -> tuple[str, bool]:
    """Parse model tier.

    Returns:
        (clean_model_name, is_flex)

    Examples:
        "flex_gpt-5.4" → ("gpt-5.4", True)
        "gpt-4o" → ("gpt-4o", False)
    """
```

**3.4: Write provider tests**

Create: `tests/agents/test_openai_provider.py`

Test scenarios:
- Structured output with OpenAI Agents SDK
- Flex tier model parsing and timeout
- TraceHooks metrics capture
- Cached token tracking
- Reasoning token tracking (o1/o3 models)
- Cost computation

**Deliverables:**
- ✅ `openai_provider.py` (~500 lines)
- ✅ `test_openai_provider.py` (15+ tests)
- ✅ All tests passing with mock OpenAI client

---

### Week 4: Agent Execution Layer - Service Integration

**Goal:** Wire providers into ClientLayer as platform service

#### Tasks

**4.1: Implement AgentExecutionService**

Update: `jazzx_sdk/agents/service.py`

Key features:
- Generic tier: `run()` method (provider-portable)
- Provider-specific tier: `.openai`, `.anthropic` properties
- Lazy provider initialization
- Context enrichment (pack_id, mode_name, case_id)
- Hook registration (foundation for Phase 2 governance)

**4.2: Wire to ClientLayer**

Update: `/Users/foo/src/research/sangit/japes/jazzx_sdk/client_layer.py`

Add property:
```python
@property
def agents(self) -> AgentExecutionService:
    """Access to Agent Execution Layer."""
    if self._agent_execution_service is None:
        from jazzx_sdk.agents import AgentExecutionService

        self._agent_execution_service = AgentExecutionService(
            pack_id=self._pack_id,  # TODO: Wire from context
            default_provider="openai",
            default_model="gpt-4o",
        )

    return self._agent_execution_service
```

**4.3: Update __init__.py exports**

Update: `jazzx_sdk/agents/__init__.py`

Export:
```python
from jazzx_sdk.agents.base import (
    AgentProvider,
    AgentExecutionTrace,
    AgentResult,
    ToolCallRecord,
)
from jazzx_sdk.agents.service import AgentExecutionService
from jazzx_sdk.agents.anthropic_provider import AnthropicProvider
from jazzx_sdk.agents.openai_provider import OpenAIProvider
from jazzx_sdk.agents.exceptions import (
    AgentExecutionError,
    ProviderError,
    StructuredOutputError,
    ToolExecutionError,
)

__all__ = [
    "AgentProvider",
    "AgentExecutionTrace",
    "AgentResult",
    "ToolCallRecord",
    "AgentExecutionService",
    "AnthropicProvider",
    "OpenAIProvider",
    "AgentExecutionError",
    "ProviderError",
    "StructuredOutputError",
    "ToolExecutionError",
]
```

**4.4: Write service integration tests**

Create: `tests/agents/test_service.py`

Test scenarios:
- Generic tier routing (default provider)
- Provider-specific tier access
- Context enrichment (pack_id, mode_name)
- Provider selection via parameter
- Error handling and propagation

**Deliverables:**
- ✅ `service.py` completed (~300 lines)
- ✅ ClientLayer integration
- ✅ `test_service.py` (10+ tests)
- ✅ All integration tests passing

---

### Week 5: Advanced Cost Tracking

**Goal:** Elevate Macer's comprehensive cost system to JAPES

#### Tasks

**5.1: Enhance cost.py with Macer's models**

Update: `/Users/foo/src/research/sangit/japes/jazzx_sdk/utils/cost.py`

Source: `/Users/foo/src/research/sangit/macer/src/macer/utils/cost.py`

Add:
- 40+ model definitions with tier-specific pricing
- Token type separation logic:
  ```python
  def compute_cost_from_trace(
      trace: AgentExecutionTrace,
      model_name: str,
  ) -> float:
      """Compute cost from execution trace.

      Handles:
      - Regular input/output tokens
      - Cached tokens (lower rate)
      - Cache creation tokens (higher rate)
      - Reasoning tokens (o1/o3 models)
      """
  ```

**5.2: Update AnthropicProvider to capture cache tokens**

Update: `jazzx_sdk/agents/anthropic_provider.py`

Add cache token extraction:
```python
if hasattr(response, "usage"):
    # Regular tokens
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    # Cache tokens (Anthropic-specific)
    cache_read = getattr(response.usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(response.usage, "cache_creation_input_tokens", 0) or 0

    # Separate cached from regular
    input_tokens -= cache_read
```

**5.3: Update OpenAIProvider TraceHooks**

Update: `_RuntimeTraceHooks` in `openai_provider.py`

Add cached/reasoning token separation (already designed in Week 3, validate implementation)

**5.4: Write cost computation tests**

Create: `tests/utils/test_cost_advanced.py`

Test scenarios:
- All 40+ models have correct pricing
- Cached token cost computation (Anthropic)
- Cache creation cost computation (Anthropic)
- Reasoning token cost computation (o1/o3)
- Flex tier dynamic pricing
- Known token counts → expected costs (fixtures)

**Deliverables:**
- ✅ Enhanced `cost.py` (~+300 lines for model definitions)
- ✅ AnthropicProvider cache token capture
- ✅ OpenAIProvider cache/reasoning token capture
- ✅ `test_cost_advanced.py` (20+ tests)
- ✅ Cost accuracy validated (within 0.5% of known costs)

---

### Week 6: Documentation and Version Bump

**Goal:** Complete JAPES v1.2.0 release with comprehensive docs

#### Tasks

**6.1: Update pyproject.toml**

Update: `/Users/foo/src/research/sangit/japes/pyproject.toml`

Changes:
```toml
[tool.poetry]
version = "1.2.0"  # Was 1.1.4

[tool.poetry.dependencies]
# Make LLM SDKs optional dependencies
anthropic = {version = "^0.25.0", optional = true}
openai-agents = {version = "^0.17.0", optional = true}  # Already exists

[tool.poetry.extras]
agents-openai = ["openai-agents"]
agents-anthropic = ["anthropic"]
agents-all = ["openai-agents", "anthropic"]
```

**6.2: Update CHANGELOG.md**

Update: `/Users/foo/src/research/sangit/japes/CHANGELOG.md`

Add complete v1.2.0 section (use content from enrichment proposal)

**6.3: Update README.md**

Update: `/Users/foo/src/research/sangit/japes/README.md`

Add section after Quick Start:
- Agent Execution Layer overview
- Generic tier example
- Provider-specific tier example
- Installation instructions with extras

**6.4: Create migration guide**

Create: `/Users/foo/src/research/sangit/japes/docs/migrations/v1.2.0-agent-execution-layer.md`

Content:
- Why Agent Execution Layer exists
- Generic tier vs provider-specific tier
- Migration from direct SDK usage
- Migration from custom adapters (JACI example)
- Breaking changes (none, additive only)

**6.5: Update __version__**

Update: `/Users/foo/src/research/sangit/japes/jazzx_sdk/__init__.py`

```python
__version__ = "1.2.0"
```

**6.6: Run full test suite**

```bash
cd /Users/foo/src/research/sangit/japes
poetry install
poetry run pytest -v --cov=jazzx_sdk --cov-report=term-missing
```

Target: 90%+ coverage, all tests passing

**6.7: Create git commit**

```bash
git add .
git commit -m "Add Agent Execution Layer and Advanced Cost Tracking (v1.2.0)

- Agent Execution Layer for provider-agnostic agent execution
- AnthropicProvider with structured output and tool loop
- OpenAIProvider with Agents SDK integration and flex tier
- Advanced cost tracking with 40+ models and token type separation
- Comprehensive test suite (60+ new tests)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Deliverables:**
- ✅ Version bumped to 1.2.0
- ✅ CHANGELOG.md updated
- ✅ README.md updated with examples
- ✅ Migration guide created
- ✅ Full test suite passing (90%+ coverage)
- ✅ Git commit created

---

## Phase 2: Migrate JACI
### Duration: 2 weeks

This phase proves the value by migrating JACI to use enriched JAPES.

### Week 7: Migrate JACI-KYC (Anthropic)

**Goal:** Replace JACI's Anthropic adapter with `ctx.runtime.agents.anthropic`

#### Tasks

**7.1: Update pyproject.toml**

Update: `/Users/foo/src/research/sangit/jaci/pyproject.toml`

Change:
```toml
[tool.poetry.dependencies]
jazzx-runtime-sdk = {git = "https://github.com/JazzX-LLC/japes.git", branch = "main"}
# Or: jazzx-runtime-sdk = "^1.2.0" (if published to PyPI)

# Remove: anthropic = "^0.25.0" (now from JAPES extras)
```

Add:
```toml
[tool.poetry.dependencies]
jazzx-runtime-sdk = {git = "https://github.com/JazzX-LLC/japes.git", branch = "main", extras = ["agents-anthropic"]}
```

**7.2: Update KYC Anthropic modes**

Files to update:
- `/Users/foo/src/research/sangit/jaci/src/jaci/scenarios/kyc_anthropic/modes/investigator.py`
- `/Users/foo/src/research/sangit/jaci/src/jaci/scenarios/kyc_anthropic/modes/document_examiner.py`
- Any other modes using `AnthropicAdapter`

Before:
```python
from jaci.sdk.anthropic_adapter import AnthropicAdapter

adapter = AnthropicAdapter()
result = await adapter.run(
    model="claude-sonnet-4-5",
    system_prompt=prompt,
    messages=messages,
    output_schema=RiskTierRecommendation,
)
```

After:
```python
result = await ctx.runtime.agents.anthropic.run(
    model="claude-sonnet-4-5",
    system_prompt=prompt,
    messages=messages,
    output_schema=RiskTierRecommendation,
)

# Access trace for metrics
logger.info(f"Cost: ${result.trace.cost_usd:.4f}")
logger.info(f"Tokens: {result.trace.tokens_total}")
```

**7.3: Remove deprecated code**

Delete:
- `/Users/foo/src/research/sangit/jaci/src/jaci/sdk/anthropic_adapter.py` (~334 lines)
- Remove imports in `__init__.py`

**7.4: Run JACI test suite**

```bash
cd /Users/foo/src/research/sangit/jaci
poetry install
poetry run pytest -v
```

Target: All tests passing (no regressions)

**7.5: Validate cost accuracy**

Compare:
- Old cost computation (JACI's adapter)
- New cost computation (JAPES trace)

Validate within 0.5% for same inputs

**Deliverables:**
- ✅ JACI-KYC modes migrated
- ✅ `anthropic_adapter.py` deleted (-334 lines)
- ✅ All JACI tests passing
- ✅ Cost accuracy validated

---

### Week 8: Migrate JACI-AML (OpenAI)

**Goal:** Replace JACI's OpenAI Agents SDK integration with `ctx.runtime.agents`

#### Tasks

**8.1: Update AML modes**

Files to update:
- `/Users/foo/src/research/sangit/jaci/src/jaci/modes/investigator.py`
- Other modes using OpenAI Agents SDK

Before:
```python
from jaci.common.agents import get_model
from jaci.hooks import TraceHooks

model = get_model()
agent = Agent(
    name="Investigator",
    instructions=prompt,
    model=model,
    output_type=AgentOutputSchema(HypothesisUpdate),
)

with TraceHooks() as hooks:
    result = await Runner.run(agent, prompt, hooks=hooks)

# Extract metrics from hooks
metrics = hooks.metrics
cost = compute_cost(metrics, model_name)
```

After:
```python
result = await ctx.runtime.agents.run(
    system_prompt=prompt,
    messages=messages,
    output_schema=HypothesisUpdate,
    model="flex_gpt-5.4",
)

# Trace automatically captured
logger.info(f"Cost: ${result.trace.cost_usd:.4f}")
logger.info(f"Tool calls: {len(result.trace.tool_calls)}")
```

**8.2: Remove deprecated code**

Delete:
- `/Users/foo/src/research/sangit/jaci/src/jaci/hooks.py` (~213 lines)
- `/Users/foo/src/research/sangit/jaci/src/jaci/common/agents/__init__.py` (~200 lines)
- Update imports

**8.3: Run JACI test suite**

```bash
cd /Users/foo/src/research/sangit/jaci
poetry run pytest -v
```

Target: All tests passing

**8.4: Measure benefits**

Calculate:
- Lines of code removed: ~747 lines (anthropic_adapter + hooks + agents)
- Cost accuracy improvement (if any)
- Developer experience (subjective feedback)

**8.5: Create git commit**

```bash
git add .
git commit -m "Migrate to JAPES Agent Execution Layer (v1.2.0)

Replace custom LLM adapters with ctx.runtime.agents:
- JACI-KYC: Use ctx.runtime.agents.anthropic
- JACI-AML: Use ctx.runtime.agents.openai

Benefits:
- Removed 747 lines of LLM wrapper code (96% reduction)
- Unified tracing and cost computation
- Automatic retry logic and error handling
- Structured output without custom parsing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Deliverables:**
- ✅ JACI-AML modes migrated
- ✅ ~747 lines removed total
- ✅ All JACI tests passing
- ✅ Benefits documented
- ✅ Git commit created

---

## Phase 3: Migrate K9
### Duration: 1 week

This phase extends K9's JAPES usage to include Agent Execution Layer.

### Week 9: Migrate K9 to Agent Execution Layer

**Goal:** Replace K9's direct LLM calls with structured agent runs

#### Tasks

**9.1: Update pyproject.toml**

Update: `/Users/foo/src/research/sangit/k9/pyproject.toml`

Change:
```toml
[tool.poetry.dependencies]
jazzx-runtime-sdk = {git = "https://github.com/JazzX-LLC/japes.git", branch = "main", extras = ["agents-openai"]}
```

K9 primarily uses OpenAI, so only need `agents-openai` extra.

**9.2: Update LLM Manager methods**

Update: `/Users/foo/src/research/sangit/k9/src/ontology_generator/core/llm_manager.py`

Target methods:
- `extract_ontology_proposals()` → Use structured output
- `extract_categorized_proposals()` → Use structured output
- `generate_ontology()` → Use structured output (if JSON-LD schema defined)
- `validate_ontology()` → Use structured output

Before:
```python
async def extract_ontology_proposals(
    self,
    document_content: str,
    domain: str,
    ontology_context: str | None = None,
    mode: str = "mode2",
) -> dict[str, Any]:
    prompt = self._build_extraction_prompt(...)

    result = await self.japes_llm.run(
        prompt=prompt,
        task_type="extraction",
        temperature=0.1,
    )

    # Manual JSON parsing
    json_str = self._extract_json(result.content)
    return json.loads(json_str)
```

After:
```python
async def extract_ontology_proposals(
    self,
    document_content: str,
    domain: str,
    ontology_context: str | None = None,
    mode: str = "mode2",
) -> ProposalSet:  # Return Pydantic model
    prompt = self._build_extraction_prompt(...)

    result = await self.ctx.runtime.agents.run(
        system_prompt="You are an ontology extraction specialist...",
        messages=[{"role": "user", "content": prompt}],
        output_schema=ProposalSet,  # Pydantic model
        model="gpt-4o",
    )

    return result.output  # Already parsed
```

**9.3: Define Pydantic schemas**

Create: `/Users/foo/src/research/sangit/k9/src/ontology_generator/core/schemas.py`

Define:
```python
from pydantic import BaseModel, Field

class EntityProposal(BaseModel):
    name: str
    type: str  # "class" | "property" | "relationship"
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]

class ProposalSet(BaseModel):
    entities: list[EntityProposal]
    relationships: list[EntityProposal]
    domain: str
    extraction_mode: str
```

**9.4: Update conductors to use agents**

Update:
- `/Users/foo/src/research/sangit/k9/src/ontology_generator/conductors/ontology_conductor.py`
- `/Users/foo/src/research/sangit/k9/src/ontology_generator/conductors/regulation_conductor.py`

Replace `ctx.runtime.llm.run()` calls with `ctx.runtime.agents.run()` where structured output is needed.

**9.5: Run K9 test suite**

```bash
cd /Users/foo/src/research/sangit/k9
poetry install
PYTHONPATH=src .venv/bin/python -m pytest -v
```

Target: All 68 tests passing

**9.6: Update CHANGELOG**

Update: `/Users/foo/src/research/sangit/k9/CHANGELOG.md`

Add v0.5.0 section:
```markdown
## [0.5.0] - 2026-06-XX

**Agent Execution Layer Integration**

### Changed

- **LLM Manager**: Migrated to JAPES Agent Execution Layer (v1.2.0)
  - Methods now use `ctx.runtime.agents.run()` for structured output
  - Removed manual JSON parsing (~50 lines)
  - Automatic retry logic and error handling
  - Unified tracing with token metrics and cost

### Added

- **Pydantic Schemas** (`core/schemas.py`) — Structured output models
  - `EntityProposal`, `ProposalSet` for ontology extraction
  - `ValidationResult` for ontology validation

### Benefits

- ✅ Structured output enforcement (no more parsing errors)
- ✅ Automatic cost tracking per extraction
- ✅ Better error messages (validation at model level)
```

**9.7: Create git commit**

```bash
git add .
git commit -m "Integrate JAPES Agent Execution Layer (v0.5.0)

Migrate LLM Manager to use ctx.runtime.agents:
- Replace direct LLM calls with structured agent runs
- Define Pydantic schemas for all extraction outputs
- Remove manual JSON parsing logic

Benefits:
- Structured output enforcement (no parsing errors)
- Automatic cost tracking and tracing
- Better error messages with validation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Deliverables:**
- ✅ K9 migrated to Agent Execution Layer
- ✅ Pydantic schemas defined
- ✅ ~50 lines of JSON parsing removed
- ✅ All 68 tests passing
- ✅ CHANGELOG updated
- ✅ Git commit created

---

## Phase 4: Document Benefits and Create Proposal
### Duration: 1 week

This phase documents the proven value and creates a proposal for Juno/Macer.

### Week 10: Benefits Documentation and Juno/Macer Proposal

**Goal:** Create compelling case for Juno/Macer to adopt enriched JAPES

#### Tasks

**10.1: Document JAPES v1.2.0 benefits**

Create: `/Users/foo/src/research/sangit/japes/docs/v1.2.0-adoption-benefits.md`

Content:
- Code reduction metrics (JACI: -747 lines, K9: -50 lines)
- Before/after code examples
- Cost accuracy improvements
- Developer experience improvements
- Reliability improvements (structured output, retry logic)

**10.2: Create Juno migration guide**

Create: `/Users/foo/src/research/sangit/juno/docs/JAPES_v1.2.0_Migration_Plan.md`

Content:
- Current state analysis (JunoCostHooks, direct OpenAI Agents SDK usage)
- Migration steps:
  1. Update to jazzx-runtime-sdk v1.2.0 with `agents-openai` extra
  2. Replace `JunoCostHooks` with JAPES TraceHooks (built-in)
  3. Replace direct OpenAI Agents SDK usage with `ctx.runtime.agents.openai`
  4. Remove 110 lines from `cost_hooks.py`
- Benefits:
  - Accurate cost tracking (cached tokens, reasoning tokens)
  - Unified tracing
  - No maintenance burden for hooks
- Estimated effort: 1 week
- Risk assessment: Low (additive change, can migrate incrementally)

**10.3: Create Macer migration guide**

Create: `/Users/foo/src/research/sangit/macer/docs/JAPES_v1.2.0_Migration_Plan.md`

Content:
- Current state analysis (custom cost module, TraceHooks, Anthropic wrapper)
- Migration steps:
  1. Update to jazzx-runtime-sdk v1.2.0 with `agents-anthropic` extra
  2. Replace custom Anthropic wrapper with `ctx.runtime.agents.anthropic`
  3. Contribute cost module to JAPES (if not already in v1.2.0)
  4. Remove ~750 lines (models, hooks, cost utils)
- Benefits:
  - Zero maintenance for LLM wrappers
  - Cost tracking maintained upstream
  - Structured output support
- Estimated effort: 2 weeks
- Risk assessment: Medium (large refactor, needs testing)

**10.4: Create presentation deck**

Create: `/Users/foo/src/research/sangit/japes/docs/v1.2.0-adoption-presentation.pdf` (or .md)

Slides:
1. Title: "JAPES v1.2.0 Agent Execution Layer"
2. Problem: Code duplication across extensions
3. Solution: Centralized agent execution service
4. Architecture: Generic tier + provider-specific tier
5. Proven value: JACI results (-747 lines, unified tracing)
6. Proven value: K9 results (-50 lines, structured output)
7. Proposal: Juno adoption plan
8. Proposal: Macer adoption plan
9. Timeline: 1-2 weeks per extension
10. ROI: $82K/year cost savings, 93% code reduction

**10.5: Schedule review meetings**

- Juno team: Present migration plan, answer questions
- Macer team: Present migration plan, discuss cost module contribution

**Deliverables:**
- ✅ Benefits documentation created
- ✅ Juno migration guide created
- ✅ Macer migration guide created
- ✅ Presentation deck created
- ✅ Review meetings scheduled

---

## Success Criteria

### Phase 1 (JAPES Enrichment)
- ✅ Agent Execution Layer implemented (~2,000 lines)
- ✅ 60+ tests passing (90%+ coverage)
- ✅ JAPES v1.2.0 released
- ✅ Documentation complete (README, CHANGELOG, migration guide)

### Phase 2 (JACI Migration)
- ✅ JACI migrated to ctx.runtime.agents
- ✅ 747 lines removed from JACI
- ✅ All JACI tests passing (no regressions)
- ✅ Cost accuracy maintained (within 0.5%)

### Phase 3 (K9 Migration)
- ✅ K9 migrated to structured agent runs
- ✅ 50+ lines of JSON parsing removed
- ✅ All 68 K9 tests passing
- ✅ Pydantic schemas defined

### Phase 4 (Proposal)
- ✅ Benefits documented with metrics
- ✅ Juno migration guide created
- ✅ Macer migration guide created
- ✅ Presentation delivered to teams

---

## Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| JACI tests fail after migration | Low | High | Phased migration, test at each step |
| Cost computation changes | Low | High | Validate against known costs before migration |
| K9 JSON parsing breaks | Low | Medium | Define strict Pydantic schemas, comprehensive tests |
| Provider API changes | Medium | Medium | Version lock SDKs (anthropic==0.25.0, openai-agents==0.17.0) |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Juno/Macer resist adoption | Medium | Medium | Prove value with JACI/K9 first, show concrete benefits |
| Timeline slips | Medium | Low | Phase 1-3 can proceed independently of Phase 4 |
| JAPES becomes bottleneck | Low | Medium | Comprehensive tests, clear ownership, documentation |

---

## Dependencies

### Phase 1 Dependencies
- JACI codebase access (read-only, for extraction)
- Macer codebase access (read-only, for cost module patterns)
- JAPES write access
- OpenAI API key (for testing)
- Anthropic API key (for testing)

### Phase 2 Dependencies
- Phase 1 complete (JAPES v1.2.0 released)
- JACI write access
- JACI test environment

### Phase 3 Dependencies
- Phase 1 complete (JAPES v1.2.0 released)
- K9 write access
- K9 test environment

### Phase 4 Dependencies
- Phase 1-3 complete
- Juno/Macer team availability for review meetings

---

## Open Questions

1. **Testing Strategy:** Should we use real API keys or mock all LLM responses?
   - **Recommendation:** Mock for unit tests, real API for integration tests (small quota)

2. **Version Publishing:** Should JAPES v1.2.0 be published to PyPI or remain git-only?
   - **Recommendation:** Git-only for now, PyPI when 2+ external consumers exist

3. **Backward Compatibility:** Should we keep JACI's old adapters during migration?
   - **Recommendation:** No, clean cut. Old code becomes dead code if kept.

4. **Cost Module Source:** Should we use JACI's or Macer's cost module as base?
   - **Recommendation:** Macer's (more comprehensive, 40+ models vs ~15 in JACI)

5. **MLflow Gateway:** Should Juno's MLflow Gateway be elevated to JAPES now?
   - **Recommendation:** No, keep Juno-specific. Revisit if 2+ extensions need it.

---

## Next Steps

**Immediate Actions:**

1. **Review this plan** with team (30-minute sync)
2. **Assign owner** for Phase 1 implementation
3. **Set up JAPES development environment** (if not already)
4. **Create tracking issue** in JAPES repo (link to this plan)
5. **Begin Week 1 tasks** (core interfaces)

**Week 1 Kickoff Checklist:**
- [ ] Development environment ready
- [ ] JACI codebase cloned (for reference)
- [ ] Macer codebase cloned (for reference)
- [ ] Test API keys available
- [ ] Team aligned on priorities

---

## Appendix: Quick Reference

### Key Files to Create (Phase 1)

JAPES files:
```
jazzx_sdk/agents/
├── __init__.py
├── base.py                      # Week 1
├── exceptions.py                # Week 1
├── anthropic_provider.py        # Week 2
├── utils.py                     # Week 2
├── openai_provider.py           # Week 3
└── service.py                   # Week 4

tests/agents/
├── __init__.py
├── conftest.py
├── test_base.py                 # Week 1
├── test_anthropic_provider.py   # Week 2
├── test_openai_provider.py      # Week 3
└── test_service.py              # Week 4
```

Documentation files:
```
docs/
├── migrations/
│   └── v1.2.0-agent-execution-layer.md   # Week 6
└── v1.2.0-adoption-benefits.md            # Week 10
```

### Key Files to Update (Phase 1)

```
jazzx_sdk/client_layer.py          # Week 4
jazzx_sdk/utils/cost.py            # Week 5
jazzx_sdk/__init__.py              # Week 6
pyproject.toml                             # Week 6
CHANGELOG.md                               # Week 6
README.md                                  # Week 6
```

### Key Files to Update (Phase 2 - JACI)

```
src/jaci/scenarios/kyc_anthropic/modes/investigator.py        # Week 7
src/jaci/scenarios/kyc_anthropic/modes/document_examiner.py   # Week 7
src/jaci/modes/investigator.py                                # Week 8
pyproject.toml                                                # Week 7
```

Delete:
```
src/jaci/sdk/anthropic_adapter.py    # Week 7
src/jaci/hooks.py                     # Week 8
src/jaci/common/agents/__init__.py    # Week 8
```

### Key Files to Update (Phase 3 - K9)

```
src/ontology_generator/core/llm_manager.py                      # Week 9
src/ontology_generator/core/schemas.py (new)                    # Week 9
src/ontology_generator/conductors/ontology_conductor.py         # Week 9
src/ontology_generator/conductors/regulation_conductor.py       # Week 9
pyproject.toml                                                  # Week 9
CHANGELOG.md                                                    # Week 9
```

---

## Contact and Ownership

**Plan Owner:** TBD
**Implementation Lead:** TBD
**Review Cadence:** Weekly check-ins on Monday mornings
**Status Tracking:** GitHub Project board (TBD)

---

**End of Implementation Plan**
