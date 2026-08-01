# Anthropic KYC Reference vs JACI KYC Implementation

## Executive Summary

Anthropic's **KYC Screener** (from `claude-for-financial-services` repo) and JACI's **KYC Investigation** scenario solve **different KYC problems** using **different architectural patterns**.

| | Anthropic KYC Screener | JACI KYC Investigation |
|---|---|---|
| **Use Case** | Client onboarding screening | Periodic risk review |
| **Trigger** | New client / refresh | Review trigger event |
| **Architecture** | Managed Agents API + subagent delegation | Custom Anthropic adapter + Python Conductor |
| **Deployment** | Cowork plugin OR Managed Agent | JAPES-based investigation loop |
| **LLM Framework** | Claude Managed Agents (orchestration via API) | Anthropic Client SDK (orchestration in Python) |
| **Output** | Escalation packet (pass/fail + gaps) | Risk tier recommendation (Low/Medium/High/Prohibited) + EDD decision |

## Key Differences

### 1. Problem Domain

**Anthropic KYC Screener**: **Onboarding screening**
- Parse onboarding documents (passports, incorporation docs, UBO charts)
- Run firm's KYC/AML rules engine
- Screen against sanctions/PEP lists
- Flag gaps and hits for compliance sign-off
- **One-shot**: Document in → Escalation packet out

**JACI KYC Investigation**: **Periodic risk review**
- Generate risk factor hypotheses (PEP, sanctions, adverse media, BO complexity, geo risk)
- Iteratively gather evidence across multiple tools
- Assess risk tier and EDD requirements
- Produce risk tier recommendation with rationale
- **Iterative loop**: Investigation → evidence → convergence → recommendation

### 2. Architecture Pattern

**Anthropic KYC Screener**: **Managed Agents API with subagent delegation**

```yaml
# agent.yaml
name: kyc-screener
model: claude-opus-4-7
system: { file: kyc-screener.md }
tools: [read, grep, glob, mcp__screening__*]

callable_agents:
  - doc-reader     # Read-only, untrusted docs
  - rules-engine   # Apply rules, screening MCP
  - escalator      # Write escalation packet

# Orchestration: Claude Managed Agents handles handoffs
# Security: Three-tier isolation (untrusted → trusted → write)
```

**JACI KYC Investigation**: **Custom SDK adapter + Python Conductor**

```python
# Python orchestration in JACI Conductor
class KYCInvestigatorMode(BaseMode):
    def __init__(self, anthropic_api_key):
        self.adapter = AnthropicAdapter(api_key=anthropic_api_key)

    async def run(self, review_trigger, hypotheses, evidence, iteration):
        result = self.adapter.run(
            model="claude-sonnet-4-5",
            system_prompt=self.system_prompt,
            messages=messages,
            output_schema=RiskHypothesisUpdate,  # Pydantic structured output
        )
        return ModeResult(success=True, output=result)

# Orchestration: JACI Conductor (Python loop) sequences modes
# Security: Tool execution via ToolRegistry, evidence attestation via Verifier
```

### 3. Key Design Choices

#### Anthropic's Choices (Managed Agents)

✅ **Pros:**
- Native Claude API orchestration (no custom loop)
- Subagent delegation with security isolation
- Structured output via `output_schema` in agent.yaml
- Same source for Cowork plugin AND headless deployment
- Built-in handoff protocol (`handoff_request` events)

❌ **Cons:**
- Managed Agents API is "research preview"
- Subagent delegation requires external event loop (`scripts/orchestrate.py`)
- Less control over iteration logic
- Harder to integrate with existing orchestrators (BPMN, Flowable)

#### JACI's Choices (Custom Adapter + Conductor)

✅ **Pros:**
- Full control over orchestration logic (guards, convergence, iteration limits)
- Easy integration with JAPES platform and BPMN workflows
- SDK-agnostic architecture (swap OpenAI ↔ Anthropic)
- Evidence attestation and policy governance layers
- MLflow tracking and evaluation harness

❌ **Cons:**
- Custom adapter code to maintain
- Manual tool loop implementation
- Heavier infrastructure (Conductor, ToolRegistry, CaseContext)

### 4. Workflow Comparison

#### Anthropic KYC Screener Flow

```
1. Orchestrator receives onboarding packet ID
2. Handoff → doc-reader subagent
   - Reads untrusted docs (Read/Grep only)
   - Returns schema-validated JSON (length-capped)
3. Orchestrator receives structured entity file
4. Handoff → rules-engine subagent
   - Applies firm's rules grid
   - Calls screening MCP (sanctions/PEP)
   - Returns pass/fail per rule + hits
5. Orchestrator receives rules result
6. Handoff → escalator subagent
   - Formats compliance packet
   - Writes escalation-<packet>.xlsx
7. Done: Escalation packet ready for human review
```

#### JACI KYC Investigation Flow

```
1. Conductor receives ReviewTrigger
2. Loop:
   a. Investigator generates RiskFactorHypothesis
   b. Investigator requests evidence (identity, sanctions, PEP, adverse media, BO, geo)
   c. ToolRegistry retrieves evidence from Integration Hub
   d. Verifier attests evidence (attested/flagged)
   e. Sentinel checks loop health (iteration limit, evidence coverage)
   f. If not converged, repeat with updated hypotheses
3. Post-loop:
   a. Reasoner proposes RiskTierRecommendation (Low/Medium/High/Prohibited)
   b. Reasoner determines EDD decision (NotRequired/Required/AlreadyInProgress)
   c. Governor enforces policy gates
   d. Narrator drafts review report (if escalating)
4. Output: CaseFile with CanonicalTrace for BPMN handoff
```

### 5. Structured Output

**Anthropic KYC Screener**: Uses `output_schema` in agent.yaml

```yaml
# doc-reader.yaml
output_schema:
  type: object
  required: [packet_id, entity, ubos]
  properties:
    packet_id: { type: string, maxLength: 32 }
    entity:
      type: object
      properties:
        legal_name: { type: string, maxLength: 200 }
        country: { type: string, maxLength: 2 }
    ubos:
      type: array
      maxItems: 100
      items:
        type: object
        properties:
          name: { type: string, maxLength: 200 }
          pct: { type: number }
```

**JACI KYC Investigation**: Uses Pydantic schemas + Anthropic structured output API

```python
# kyc_schemas.py
class RiskFactorHypothesis(BaseModel):
    hypothesis_id: str
    risk_factor_name: str
    risk_factor_type: RiskFactorType  # Enum
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_required: list[str]
    evidence_gathered: list[str]
    status: str  # ACTIVE, CONFIRMED, ELIMINATED
    rationale: str
    impact_tier: RiskTier

# anthropic_adapter.py
json_schema = output_schema.model_json_schema()
response = self.client.messages.create(
    model=model,
    system=system_prompt,
    messages=messages,
    betas=["structured-outputs-2025-11-13"],
    output_format={
        "type": "json_schema",
        "json_schema": {"name": output_schema.__name__, "schema": json_schema}
    }
)
parsed = output_schema.model_validate(json.loads(response.content[0].text))
```

### 6. Tool Execution

**Anthropic KYC Screener**: Uses MCP servers

```yaml
# agent.yaml
tools:
  - { type: mcp_toolset, mcp_server_name: screening, default_config: { enabled: true } }

mcp_servers:
  - { type: url, name: screening, url: "${SCREENING_MCP_URL}" }

# Skills reference MCP tools
# Example: mcp__screening__sanctions(name="John Doe", dob="1980-01-01")
```

**JACI KYC Investigation**: Uses ToolRegistry with Integration Hub connectors

```python
# kyc/tools/registry.py
class KYCToolRegistry:
    """8 evidence retrieval tools for KYC investigation."""

    def get_identity_verification(self, customer_id: str) -> dict:
        # Calls Identity Verification Hub connector
        return self.connectors["identity"].verify(customer_id)

    def get_sanctions_screening(self, customer_id: str) -> dict:
        # Calls Sanctions Screening Hub connector (OFAC, UN, EU)
        return self.connectors["sanctions"].screen(customer_id)

    def get_pep_screening(self, customer_id: str) -> dict:
        # Calls PEP Screening Hub connector
        return self.connectors["pep"].screen(customer_id)

    # ... 5 more tools
```

### 7. Security Model

**Anthropic KYC Screener**: Three-tier isolation via subagents

| Tier | Touches Untrusted Docs? | Tools | MCP |
|---|---|---|---|
| `doc-reader` | **YES** | Read, Grep only | None |
| `rules-engine` / Orchestrator | No | Read, Grep, Glob, Agent | screening (read-only) |
| `escalator` (Write-holder) | No | Read, Write, Edit | None |

**JACI KYC Investigation**: Evidence attestation + policy governance

```python
# Verifier attests every evidence object
class VerifierMode:
    def run(self, evidence: EvidenceObject) -> VerifierReport:
        # Returns: attested, flagged, or rejected
        # Only attested evidence used by Reasoner

# Governor enforces policy gates
class GovernorMode:
    def run(self, recommendation: RiskTierRecommendation) -> GovernorDecision:
        # Checks: policy compliance, deadline enforcement, required actions
        # approved=False blocks progression
```

## Conclusion: Complementary Approaches

### When to Use Anthropic KYC Screener

✅ **Best for:**
- Client onboarding workflows
- Document parsing and rules engine
- Sanctions/PEP screening at intake
- Cowork plugin deployment
- Simple one-shot screening tasks

❌ **Not suitable for:**
- Iterative investigation loops
- Multi-mode orchestration (Investigator → Verifier → Reasoner)
- Complex convergence logic
- Policy governance layers
- Integration with existing BPMN orchestrators

### When to Use JACI KYC Investigation

✅ **Best for:**
- Periodic risk reviews
- Hypothesis-driven evidence gathering
- Risk tier assessment (Low/Medium/High/Prohibited)
- EDD decision workflows
- Integration with BPMN/Flowable
- Policy governance and attestation
- Evaluation and MLflow tracking

❌ **Not suitable for:**
- Quick onboarding screening
- Document parsing (use Anthropic's pattern)
- Cowork plugin deployment (not designed for it)

## Hybrid Approach (Recommended)

**Best of both worlds:**

1. **Onboarding**: Use Anthropic KYC Screener
   - Parse documents → Run rules → Screen sanctions/PEP → Flag gaps
   - Output: Initial risk rating + escalation packet

2. **Periodic Review**: Use JACI KYC Investigation
   - Triggered by: time-based review, alert, regulatory requirement
   - Input: Customer ID + initial risk tier (from onboarding)
   - Process: Hypothesis generation → Evidence gathering → Risk tier recommendation
   - Output: Updated risk tier + EDD decision + review report

3. **Integration Point**: Onboarding escalation packet → JACI ReviewTrigger
   ```python
   # Bridge: Anthropic escalation → JACI review
   escalation_packet = kyc_screener.run(packet_id="new_client_001")

   if escalation_packet["disposition"] in ["escalate-EDD", "request-docs"]:
       review_trigger = ReviewTrigger(
           review_id=f"review_{uuid4()}",
           review_type=ReviewType.ENHANCED_DUE_DILIGENCE,
           customer_id=escalation_packet["entity"]["legal_name"],
           review_timestamp=datetime.utcnow(),
           risk_score=escalation_packet["risk_rating"],
           initial_flags=escalation_packet["escalation_reasons"],
           current_risk_tier=map_rating(escalation_packet["risk_rating"]),
       )

       result = kyc_conductor.run(review_trigger)
   ```

## File Locations for Reference

### Anthropic Claude for Financial Services
```
anthropic-fs-ref/
├── plugins/agent-plugins/kyc-screener/
│   ├── agents/kyc-screener.md              # Main agent prompt
│   └── skills/
│       ├── kyc-doc-parse/SKILL.md          # Document parsing skill
│       └── kyc-rules/SKILL.md              # Rules engine skill
└── managed-agent-cookbooks/kyc-screener/
    ├── agent.yaml                          # Managed Agent manifest
    ├── steering-examples.json              # Steering event examples
    └── subagents/
        ├── doc-reader.yaml                 # Subagent: untrusted doc reader
        ├── rules-engine.yaml               # Subagent: rules evaluation
        └── escalator.yaml                  # Subagent: write escalation packet
```

### JACI KYC Investigation
```
jaci/
├── src/jaci/scenarios/kyc/
│   ├── modes/
│   │   ├── investigator.py                 # Risk hypothesis generation
│   │   └── reasoner.py                     # Risk tier recommendation
│   ├── schemas/kyc_schemas.py              # KYC data models
│   └── tools/registry.py                   # 8 evidence retrieval tools
├── src/jaci/sdk/anthropic_adapter.py       # Custom Anthropic adapter
└── prompts/kyc/
    ├── investigator.md                     # Investigator prompt
    └── reasoner.md                         # Reasoner prompt
```

## Next Steps

### Option 1: Adopt Anthropic's Onboarding Pattern
- Implement `kyc-doc-parse` and `kyc-rules` skills in JACI
- Use for new client intake before periodic review kicks in

### Option 2: Extend JACI with Document Parsing Mode
- Add `KYCDocumentParserMode` (using Anthropic adapter)
- Reuse Anthropic's skills as prompt templates
- Keep Python Conductor orchestration

### Option 3: Hybrid Integration
- Deploy Anthropic KYC Screener as Managed Agent
- JACI receives escalation packets as ReviewTriggers
- Seamless onboarding → periodic review pipeline

## Summary

| Feature | Anthropic KYC Screener | JACI KYC Investigation |
|---|---|---|
| **LLM Provider** | Anthropic (Claude Opus 4.7) | Anthropic (Claude Sonnet 4.5) |
| **Framework** | Managed Agents API | Custom Anthropic adapter |
| **Orchestration** | Claude API (subagent delegation) | JACI Conductor (Python loop) |
| **Use Case** | Onboarding screening | Periodic risk review |
| **Workflow** | One-shot (docs → escalation) | Iterative loop (hypotheses → evidence → tier) |
| **Output** | Escalation packet (pass/fail + gaps) | Risk tier + EDD decision + report |
| **Deployment** | Cowork plugin OR Managed Agent | JAPES platform + BPMN integration |
| **Code Location** | `anthropic-fs-ref/` (reference repo) | `jaci/src/jaci/scenarios/kyc/` (custom impl) |

**Bottom line**: Anthropic provides **onboarding screening** reference patterns. JACI implements **periodic risk assessment** with iterative investigation loops. Both use Anthropic LLMs but different architectural approaches for different KYC workflows.
