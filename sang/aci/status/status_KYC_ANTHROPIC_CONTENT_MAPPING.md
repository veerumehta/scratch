# Anthropic KYC Screener → JACI KYC-Anthropic Content Mapping

## Source Material

From `anthropic-fs-ref/plugins/agent-plugins/kyc-screener/`:

```
agents/kyc-screener.md           # Main system prompt (34 lines)
skills/kyc-doc-parse/SKILL.md    # Document parsing skill (49 lines)
skills/kyc-rules/SKILL.md        # Rules engine skill (48 lines)
skills/xlsx-author/SKILL.md      # Excel output skill (shared)
```

From `managed-agent-cookbooks/kyc-screener/`:

```
agent.yaml                       # Managed Agent manifest
steering-examples.json           # Trigger scenarios
subagents/doc-reader.yaml        # Document parsing subagent
subagents/rules-engine.yaml      # Rules evaluation subagent
subagents/escalator.yaml         # Output formatting subagent
```

## Anthropic's Architecture (What They Built)

**Single orchestrator agent + 3 subagents:**

```
kyc-screener (orchestrator)
├── doc-reader → Extracts entity data from untrusted docs
├── rules-engine → Applies firm rules + screening MCP
└── escalator → Formats compliance packet
```

**Workflow:** Sequential handoff (doc-reader → rules-engine → escalator → done)

**Output:** Escalation packet (flat JSON risk rating + gaps + hits)

**No:** Evidence attestation, policy governance, canonical chain, compounding loop

## JACI KYC-Anthropic Architecture (What We're Building)

**Multi-mode governed loop:**

```
KYCAnthropicConductor
├── Investigator → Extract entity data + screen for risk factors
├── Verifier → Attest evidence (NEW - not in Anthropic)
├── Reasoner → Apply risk tier rubric + cite rules
├── Governor → Enforce policy gates (NEW - not in Anthropic)
└── Narrator → Format review report (NEW - not in Anthropic)
```

**Workflow:** Iterative loop with convergence + governance gates

**Output:** ReviewFile with CanonicalTrace (canonical Decision + cross-linkage)

**Adds:** Evidence attestation, Policy objects, canonical chain, EVOLVE loop

## Content Decomposition Map

| Anthropic Source | Lines | JACI Destination | What Gets Extracted |
|-----------------|-------|------------------|---------------------|
| **agents/kyc-screener.md** | 34 | Multiple prompts | Workflow steps split across modes |
| Lines 1-17 (What you produce, Workflow) | | `prompts/kyc-anthropic/investigator.md` | Evidence gathering steps (entity extraction, screening) |
| Lines 18-24 (Guardrails) | | `prompts/kyc-anthropic/verifier.md` | Untrusted doc handling, schema validation |
| **skills/kyc-doc-parse/SKILL.md** | 49 | `prompts/kyc-anthropic/investigator.md` | Document inventory, field extraction, gap flagging |
| Lines 12-24 (Inventory the packet) | | Tool schema for entity extraction | |
| Lines 26-44 (Extract structured fields) | | `schemas/kyc_anthropic_schemas.py` → `EntityFile` schema | |
| Lines 46-48 (Flag obvious gaps) | | `prompts/kyc-anthropic/investigator.md` | Evidence completeness checks |
| **skills/kyc-rules/SKILL.md** | 48 | Multiple destinations | Rules grid → Policy objects + Reasoner rubric |
| Lines 12-25 (Risk-rate factors) | | `prompts/kyc-anthropic/reasoner.md` | Risk tier rubric |
| Lines 12-25 (Risk-rate factors) | | `src/jaci/pack/kyc_anthropic_policy_registry.py` | Policy objects (CDD rules) |
| Lines 27-30 (Required-document check) | | `prompts/kyc-anthropic/governor.md` | Document checklist enforcement |
| Lines 32-35 (Rule outcomes) | | `prompts/kyc-anthropic/governor.md` | Policy citation requirements |
| Lines 37-47 (Disposition logic) | | `prompts/kyc-anthropic/reasoner.md` | Clear/Request-docs/Escalate-EDD/Decline mapping |
| **steering-examples.json** | varies | `tests/eval/gold_cases/kyc_anthropic/` | Trigger scenarios → gold cases |
| Each example | | One `kyc_anthropic_NN.json` file | ReviewTrigger + expected outcome |

## NEW Content (Not in Anthropic - JazzX Additions)

| JACI File | Purpose | Why Not in Anthropic |
|-----------|---------|---------------------|
| `prompts/kyc-anthropic/verifier.md` | Evidence attestation with provenance | Anthropic has no attestation layer |
| `prompts/kyc-anthropic/governor.md` | Policy gate enforcement at runtime | Anthropic rules are in prompt, not enforced |
| `prompts/kyc-anthropic/narrator.md` | Structured review narrative with citations | Anthropic has flat escalation packet |
| `prompts/kyc-anthropic/evaluator.md` | Quality assessment + improvement signals | Anthropic is stateless, no compounding |
| `schemas/kyc_anthropic_schemas.py` → canonical fields | Decision ID, trace ID, policy refs, evidence refs | Anthropic has flat JSON output |
| `src/jaci/pack/kyc_anthropic_policy_registry.py` | Policy objects as first-class entities | Anthropic has markdown rules |
| `config/packs/kyc_anthropic_cdd_lifecycle.yaml` | Pack governance reference | Anthropic has no pack concept |

## Decomposition Strategy

### Investigator Mode (Evidence Gathering)

**Source content:**
- `agents/kyc-screener.md` lines 20-21: "Read the packet. A doc-reader worker extracts structured fields..."
- `skills/kyc-doc-parse/SKILL.md` entire file: Inventory, extract fields, flag gaps

**JACI adaptation:**
- Keep: Document inventory checklist (identity, entity formation, ownership, address, source of funds, tax)
- Keep: Structured field extraction schema (applicant_type, legal_name, dob, nationality, id_documents, beneficial_owners, controllers)
- Add: Evidence attestation requests (each extracted field becomes an EvidenceRequest)
- Add: Convergence criteria (all required docs inventoried + structured fields extracted)

**Output:** `RiskFactorHypothesis` (adapted from their entity file) + `EvidenceRequest[]`

### Verifier Mode (Evidence Attestation)

**Source content:**
- `agents/kyc-screener.md` lines 27-28: "Onboarding documents are untrusted. The doc-reader has Read/Grep only..."
- `subagents/doc-reader.yaml` output_schema: Schema validation with length caps, regex patterns

**JACI adaptation:**
- Keep: Untrusted document handling principles
- Keep: Schema validation requirements (maxLength, pattern constraints)
- Add: Attestation status (attested, flagged, rejected)
- Add: Provenance tracking (source system, retrieval timestamp, freshness)

**Output:** `VerifierReport` with attestation status for each evidence object

### Reasoner Mode (Risk Tier Assessment)

**Source content:**
- `skills/kyc-rules/SKILL.md` lines 12-25: Risk-rating factors (jurisdiction, applicant type, ownership opacity, PEP, sanctions, source of funds)
- `skills/kyc-rules/SKILL.md` lines 37-47: Disposition logic (clear, request-docs, escalate-EDD, decline-recommend)

**JACI adaptation:**
- Keep: Risk tier factors (jurisdiction, PEP, sanctions, BO complexity, source of funds clarity)
- Keep: Rating levels (low, medium, high) + add Prohibited tier
- Map: "clear" → Low, "request-docs" → Medium, "escalate-EDD" → High, "decline-recommend" → Prohibited
- Add: Confidence score (0.0-1.0)
- Add: EDD decision (NotRequired, Required, AlreadyInProgress)
- Add: Policy clause citations

**Output:** `RiskTierRecommendation` with canonical cross-linkage

### Governor Mode (Policy Enforcement)

**Source content:**
- `skills/kyc-rules/SKILL.md` lines 27-30: Required-document check
- `skills/kyc-rules/SKILL.md` lines 32-35: Rule outcomes (rule_id, rule_text, outcome, evidence)

**JACI adaptation:**
- Keep: Required document checklist by applicant type
- Keep: Rule outcome tracking (pass/fail/n/a with evidence reference)
- Add: Policy violation blocking (approved=False if required docs missing)
- Add: Deadline enforcement (SLA guard)
- Add: Autonomy ceiling checks (L2 Execute with Approval for low-risk, human-only for high-risk)

**Output:** `GovernorDecision` (approved, blocking_reason, required_actions, policy_violations)

### Narrator Mode (Review Report)

**Source content:**
- `agents/kyc-screener.md` line 16: "Escalation packet — gaps, hits, and recommended risk rating, formatted for compliance sign-off"
- `skills/xlsx-author/SKILL.md`: Excel output formatting

**JACI adaptation:**
- Keep: Compliance packet structure (entity profile, rules result, screening result, escalation summary)
- Add: Structured sections (customer profile, risk assessment, evidence analysis, risk factors, recommendations)
- Add: Evidence citations per section
- Add: Completeness flags per section
- Add: Missing required fields tracking

**Output:** `ReviewReportDraft` (analogous to SARDraft)

## Provenance & Attribution

### Apache-2.0 License Compliance

**Source:** `anthropics/claude-for-financial-services` (Apache-2.0)

**Attribution in JACI:**
```markdown
# prompts/kyc-anthropic/investigator.md

This prompt incorporates content from Anthropic's claude-for-financial-services
repository (https://github.com/anthropics/claude-for-financial-services),
licensed under Apache-2.0.

Original content: plugins/agent-plugins/kyc-screener/agents/kyc-screener.md
                  plugins/agent-plugins/kyc-screener/skills/kyc-doc-parse/SKILL.md

Adaptations for JazzX governance: [list modifications]
```

**What we keep verbatim:**
- Document type categories (identity, entity formation, ownership, address, source of funds, tax)
- Risk factor categories (jurisdiction, PEP, sanctions, BO opacity, source of funds)
- Field extraction schema (legal_name, dob, nationality, beneficial_owners structure)

**What we modify:**
- Workflow: Single-shot → Iterative loop
- Output: Flat JSON → Canonical objects with cross-linkage
- Enforcement: Prompt-only → Policy-as-code gates
- Audit: Session logs → CanonicalTrace

## Side-by-Side Comparison (Phase 4)

### Input (Same)
```json
{
  "packet_id": "onboard_2026_001",
  "applicant_type": "entity",
  "legal_name": "Acme Trading LLC",
  "jurisdiction": "BVI",
  "beneficial_owners": [
    {"name": "John Doe", "pct": 35, "nationality": "RU"},
    {"name": "Jane Smith", "pct": 30, "nationality": "US"}
  ],
  "pep_declared": false
}
```

### Output 1: Anthropic KYC Screener (Raw)
```json
{
  "risk_rating": "high",
  "disposition": "escalate-EDD",
  "missing_documents": ["UBO verification (layer 2)"],
  "escalation_reasons": ["rule 4.2: High-risk jurisdiction (BVI)", "rule 3.1: Potential PEP exposure (RU beneficial owner)"],
  "rule_outcomes": [
    {"rule_id": "2.1", "outcome": "pass", "evidence": "Entity formation docs provided"},
    {"rule_id": "3.1", "outcome": "fail", "evidence": "Beneficial owner from high-risk jurisdiction"},
    {"rule_id": "4.2", "outcome": "fail", "evidence": "Registered in BVI (FATF grey list)"}
  ]
}
```

### Output 2: JACI KYC-Anthropic (Governed)
```json
{
  "review_file": {
    "review_id": "review_001",
    "customer_id": "Acme Trading LLC",
    "recommendation": {
      "risk_tier": "high",
      "edd_decision": "required",
      "confidence": 0.85,
      "rationale": "Entity registered in high-risk jurisdiction (BVI, FATF grey list). Beneficial ownership includes Russian national (35%), triggering mandatory enhanced screening per Policy KYC_GEO_001. Missing UBO verification for layer 2 ownership.",
      "decision_id": "decision_a1b2c3",
      "policy_refs": ["KYC_GEO_001", "KYC_BO_002", "KYC_EDD_003"],
      "evidence_refs": ["ev_entity_formation_001", "ev_bo_registry_002", "ev_sanctions_003"],
      "trace_id": "trace_xyz789"
    },
    "canonical_trace": {
      "trace_id": "trace_xyz789",
      "investigation_steps": [
        {"mode": "investigator", "iteration": 1, "hypotheses_generated": 3, "evidence_requested": 5},
        {"mode": "verifier", "evidence_attested": 4, "evidence_flagged": 1},
        {"mode": "investigator", "iteration": 2, "converged": true},
        {"mode": "reasoner", "risk_tier": "high", "edd_decision": "required"},
        {"mode": "governor", "approved": true, "policy_clauses_cited": 3}
      ],
      "decision_refs": ["decision_a1b2c3"],
      "policy_refs": ["KYC_GEO_001", "KYC_BO_002", "KYC_EDD_003"],
      "evidence_refs": ["ev_entity_formation_001", "ev_bo_registry_002", "ev_sanctions_003", "ev_pep_004", "ev_adverse_media_005"]
    },
    "governor_decision": {
      "approved": true,
      "blocking_reason": null,
      "required_actions": ["Obtain enhanced UBO verification", "Conduct adverse media screening on Russian BO"],
      "policy_violations": []
    }
  }
}
```

### Value Gap Highlighted

| Feature | Raw Anthropic | JACI Governed |
|---------|---------------|---------------|
| **Risk assessment** | ✓ (high) | ✓ (high, 0.85 confidence) |
| **EDD trigger** | ✓ (escalate-EDD) | ✓ (required, with trigger reason) |
| **Rule citations** | ✓ (rule IDs only) | ✓ (policy clause IDs + full text) |
| **Evidence tracking** | Implicit | ✓ (5 evidence objects with attestation status) |
| **Execution trace** | No | ✓ (CanonicalTrace with full lineage) |
| **Policy enforcement** | No (rules in prompt) | ✓ (Governor gate with blocking authority) |
| **Cross-linkage** | No | ✓ (Decision → Policy → Evidence → Trace) |
| **Compounding** | No (stateless) | ✓ (EVOLVE loop with improvement signals) |
| **Examiner-ready** | No (analyst output) | ✓ (compliance packet with full provenance) |

## Implementation Checklist

### Phase 1: Content Ingestion (Current)

- [x] Read Anthropic source files
- [x] Create content mapping document
- [ ] Extract entity file schema → `EntityFile` Pydantic model
- [ ] Extract risk factors → `RiskFactorType` enum
- [ ] Extract document checklist → `DocumentType` enum
- [ ] Extract rule outcomes → Policy registry structure
- [ ] Read steering-examples.json → Identify gold case scenarios

### Phase 2: Prompt Decomposition

- [ ] Create `prompts/kyc-anthropic/investigator.md` (from kyc-doc-parse skill)
- [ ] Create `prompts/kyc-anthropic/verifier.md` (NEW - attestation guidance)
- [ ] Create `prompts/kyc-anthropic/reasoner.md` (from kyc-rules skill)
- [ ] Create `prompts/kyc-anthropic/governor.md` (NEW - policy enforcement)
- [ ] Create `prompts/kyc-anthropic/narrator.md` (NEW - review report structure)
- [ ] Add Apache-2.0 attribution headers to all prompts

### Phase 3: Schema & Policy Layer

- [ ] Create `schemas/kyc_anthropic_schemas.py`
- [ ] Create `pack/kyc_anthropic_policy_registry.py`
- [ ] Create `config/packs/kyc_anthropic_cdd_lifecycle.yaml`

### Phase 4: Modes & Conductor

- [ ] Implement 5 modes (Investigator, Verifier, Reasoner, Governor, Narrator)
- [ ] Create `conductor_kyc_anthropic.py`
- [ ] Wire all modes through AnthropicAdapter

### Phase 5: Side-by-Side Demo

- [ ] Create `scripts/demo_raw_vs_governed.py`
- [ ] Create gold cases from steering-examples.json
- [ ] Run comparison on 3+ cases
- [ ] Document value gap in output

## Next Step

Start with **EntityFile schema extraction** from `skills/kyc-doc-parse/SKILL.md` lines 26-44.
