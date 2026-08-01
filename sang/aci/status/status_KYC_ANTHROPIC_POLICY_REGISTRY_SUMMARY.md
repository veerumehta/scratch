# KYC-Anthropic Policy Registry — Implementation Summary

**Created**: May 15, 2026
**Status**: Complete ✅
**File**: `src/jaci/pack/kyc_anthropic_policy_registry.py`

## Overview

The KYC-Anthropic policy registry transforms Anthropic's markdown-based KYC rules into formal JAPES Policy objects with full regulatory source attribution. This enables runtime enforcement, governance, and canonical cross-linkage.

## What Was Extracted from Anthropic

**Source**: `anthropics/claude-for-financial-services` (Apache-2.0)
**Files**:
- `plugins/agent-plugins/kyc-screener/skills/kyc-rules/SKILL.md`
- `plugins/agent-plugins/kyc-screener/agents/kyc-screener.md`

### Anthropic's Rule Grid (Markdown)

From their `kyc-rules/SKILL.md`, we extracted 4 core rules:

| Anthropic Rule | Description | JACI Policy Clause |
|----------------|-------------|-------------------|
| **Rule 1.1** | Sanctions prohibition (OFAC/UN/EU) | `KYC-SANCTIONS-001` |
| **Rule 2.1** | Document requirements per applicant type | `KYC-DOC-001` |
| **Rule 3.1** | PEP identification triggers EDD | `KYC-PEP-001` |
| **Rule 4.2** | High-risk jurisdiction triggers EDD | `KYC-GEO-001` |

**Additional patterns extracted:**
- Risk-rating factors (jurisdiction, PEP, sanctions, BO opacity, source of funds)
- Disposition logic (clear, request-docs, escalate-EDD, decline-recommend)
- Document requirements by applicant type (individual, entity, trust)
- EDD trigger criteria (PEP, high-risk jurisdiction, adverse media, BO complexity, regulatory enforcement, sanctions)

## What We Created (JazzX Policy Objects)

### 4 Policies, 11 Rules

#### Policy 1: KYC_SANCTIONS_POLICY (2 rules)
**Content Source**: Anthropic rule 1.1 + prohibited jurisdiction logic
**Regulatory Sources**: FinCEN 31 CFR 501, Anthropic KYC Screener

| Rule ID | Condition | Action | Purpose |
|---------|-----------|--------|---------|
| `KYC-SANCTIONS-001` | `sanctions_hit == true` | DENY | OFAC/UN/EU sanctions match → decline |
| `KYC-SANCTIONS-002` | `prohibited_jurisdiction == true` | DENY | FATF blacklist/firm blocklist → decline |

#### Policy 2: KYC_CDD_POLICY (3 rules)
**Content Source**: Anthropic rule 2.1 + BO complexity
**Regulatory Sources**: FinCEN CDD Final Rule, FATF R.10, FATF R.24

| Rule ID | Condition | Action | Purpose |
|---------|-----------|--------|---------|
| `KYC-DOC-001` | `applicant_type in [individual, entity, trust]` | REQUIRE_EVIDENCE | Baseline docs per applicant type |
| `KYC-BO-001` | `applicant_type == entity` | REQUIRE_EVIDENCE | BO identification (≥25% ownership) |
| `KYC-BO-002` | `bo_layer_count ≥ 3` | REQUIRE_APPROVAL | Enhanced scrutiny for complex BO structures |

#### Policy 3: KYC_EDD_POLICY (2 rules)
**Content Source**: Anthropic rule 3.1, 4.2 + EDD triggers
**Regulatory Sources**: FFIEC EDD Guidance, FATF R.12

| Rule ID | Condition | Action | Purpose |
|---------|-----------|--------|---------|
| `KYC-PEP-001` | `pep_status == true` | REQUIRE_APPROVAL | Foreign PEP → mandatory EDD, domestic → risk-based |
| `KYC-GEO-001` | `high_risk_jurisdiction == true` | REQUIRE_APPROVAL | FATF high-risk/grey list → EDD |

#### Policy 4: KYC_OPERATIONAL_POLICY (4 rules) — JazzX Addition
**Content Source**: JazzX governance (NOT in Anthropic)
**Regulatory Sources**: JazzX KYC-Anthropic Pack v0.1

| Rule ID | Condition | Action | Purpose |
|---------|-----------|--------|---------|
| `OPS-DOC-COMPLETENESS` | `missing_required_documents > 0` | DENY | Block Low/Medium if docs missing |
| `OPS-AUTONOMY-HIGH-RISK` | `risk_tier == high` | REQUIRE_APPROVAL | High tier → L1 (recommend only) |
| `OPS-AUTONOMY-PROHIBITED` | `risk_tier == prohibited` | REQUIRE_APPROVAL | Prohibited tier → L0 (human only) |
| `OPS-HUMAN-CHECKPOINT-LOW-MEDIUM` | `risk_tier in [low, medium]` | ALLOW | Low/Medium → L2 (auto-approve if clean) |

## Key Enhancements Over Anthropic

### 1. Regulatory Source Attribution

**Anthropic**: Rules in markdown, no source refs
**JACI**: Every Policy has `source_refs` with regulatory citations

```python
source_refs=[
    SourceRef(
        ref_id="fincen_cdd_final_rule",
        title="FinCEN Customer Due Diligence Requirements",
        authority="FinCEN",
        section="31 CFR 1010.230",
        effective_date=datetime(2018, 5, 11),
    ),
    SourceRef(ref_id="anthropic_kyc_screener", ...),
]
```

### 2. Escalation Paths

**Anthropic**: No escalation routing
**JACI**: 2-level escalation chain with role-based routing

```python
escalation_paths=[
    EscalationPath(
        path_id="ESC-KYC-COMPLIANCE-OFFICER",
        target_role="compliance_officer",
        condition="review_cannot_be_completed_at_analyst_level",
    ),
    EscalationPath(
        path_id="ESC-KYC-SENIOR-COMPLIANCE",
        target_role="senior_compliance_officer",
        condition="prohibited_tier_or_complex_case",
    ),
]
```

### 3. Authority Matrix

**Anthropic**: No approval routing
**JACI**: 3-tier approval structure with action scope and ceilings

```python
authority_matrix=AuthMatrix(entries=[
    AuthorityEntry(
        role="l2_analyst",
        action_scope=["recommend_tier", "request_documents"],
        ceiling={"risk_tier": "medium"},
        escalation_target="compliance_officer",
    ),
    AuthorityEntry(
        role="compliance_officer",
        action_scope=["approve_low_tier", "approve_medium_tier", "initiate_edd"],
        ceiling={"risk_tier": "high"},
        escalation_target="senior_compliance_officer",
    ),
    AuthorityEntry(
        role="senior_compliance_officer",
        action_scope=["approve_high_tier", "decline_relationship"],
        ceiling={},  # No ceiling
    ),
])
```

### 4. Autonomy Ceilings (Runtime Enforcement)

**Anthropic**: Rules in prompt only, no runtime enforcement
**JACI**: Code-enforced autonomy ceilings in `KYC_OPERATIONAL_POLICY`

| Risk Tier | Autonomy Level | Auto-Approval? | Human Checkpoint |
|-----------|----------------|----------------|------------------|
| Low | L2 (Execute with Approval) | Yes, if clean | Optional |
| Medium | L2 (Execute with Approval) | Yes, if clean | Optional |
| High | L1 (Recommend Only) | **No** | Mandatory |
| Prohibited | L0 (Human Only) | **No** | Mandatory (senior) |

Governor enforces these at runtime:
```python
# From governor.py
if risk_tier == "high":
    approved = False
    required_actions.append("Human approval required for High tier")
    autonomy_level = "L1"
```

### 5. Document Completeness Enforcement

**Anthropic**: Checks in prompt, no blocking
**JACI**: Governor blocks Low/Medium tier approvals if docs missing

```python
Rule(
    rule_id="OPS-DOC-COMPLETENESS",
    condition=Expression(field="missing_required_documents", operator=ComparisonOperator.GT, value=0),
    action=RuleAction.DENY,
    parameters={
        "applies_to_tiers": ["low", "medium"],
        "edd_exception": True,  # High tier (EDD) can proceed
    },
)
```

## Policy Object Structure

Each `Policy` contains:
- **policy_id**: Unique identifier (e.g., `KYC_SANCTIONS_POLICY`)
- **version**: Semantic versioning (e.g., `1.0.0`)
- **policy_type**: `REGULATORY` or `OPERATIONAL`
- **jurisdiction**: `US-FEDERAL`
- **rules**: List of `Rule` objects
- **source_refs**: List of `SourceRef` objects (regulatory citations)
- **escalation_paths**: 2-level escalation chain
- **authority_matrix**: Approval routing (CDD and EDD policies)
- **domain_extensions**: Pack-specific metadata (e.g., Anthropic rule mapping)

Each `Rule` contains:
- **rule_id**: Clause identifier (e.g., `KYC-SANCTIONS-001`)
- **condition**: `Expression` (field, operator, value)
- **action**: `RuleAction` (DENY, REQUIRE_APPROVAL, REQUIRE_EVIDENCE, ALLOW)
- **parameters**: Action-specific config (e.g., approval authority, evidence types)
- **priority**: Execution order (0 = highest)
- **description**: Human-readable explanation
- **citations**: List of `source_ref` IDs

## Usage in Modes

### Governor Mode
```python
from jaci.pack.kyc_anthropic_policy_registry import get_rule, get_policy

# Check if EDD is mandatory
policy_id, pep_rule = get_rule("KYC-PEP-001")
if pep_status and edd_decision != "required":
    policy_violations.append(f"EDD mandatory per {pep_rule.rule_id}")
    approved = False
```

### Reasoner Mode
```python
from jaci.pack.kyc_anthropic_policy_registry import POLICY_CLAUSES

# Cite policy clauses in recommendation
policy_refs = []
if high_risk_jurisdiction:
    policy_refs.append("KYC-GEO-001")
if pep_confirmed:
    policy_refs.append("KYC-PEP-001")

recommendation = RiskTierRecommendation(
    risk_rating="high",
    disposition="escalate-EDD",
    policy_refs=policy_refs,
    ...
)
```

### Conductor
```python
from jaci.pack.kyc_anthropic_policy_registry import KYC_ANTHROPIC_POLICIES
from jazzx_runtime_sdk.canonical_objects import preload_policies

# Preload policies at startup
preload_policies(KYC_ANTHROPIC_POLICIES)
```

## Registry API

The policy registry provides a clean accessor API:

```python
from jaci.pack.kyc_anthropic_policy_registry import (
    KYC_ANTHROPIC_POLICIES,  # List of all policies
    POLICY_REGISTRY,          # Dict[policy_id, Policy]
    RULE_INDEX,               # Dict[rule_id, (policy_id, Rule)]
    POLICY_CLAUSES,           # Dict[policy_id, metadata]
    get_policy,               # Get Policy by ID
    get_rule,                 # Get Rule by ID
    current_policies,         # Active policies only
    current_rules,            # Active rules only
)

# Get a policy
edd_policy = get_policy("KYC_EDD_POLICY")

# Get a rule
policy_id, pep_rule = get_rule("KYC-PEP-001")
print(pep_rule.description)  # "Foreign PEPs require mandatory EDD..."

# Get all active rules
active_rules = current_rules()
```

## Anthropic Rule ID Mapping

For backward compatibility with Anthropic's rule grid, we maintain a mapping in `domain_extensions`:

```python
domain_extensions={
    "anthropic_rule_mapping": {
        "1.1": "KYC-SANCTIONS-001",
        "2.1": "KYC-DOC-001",
        "3.1": "KYC-PEP-001",
        "4.2": "KYC-GEO-001",
    },
}
```

This allows tracing JACI policy clauses back to Anthropic's original rule IDs.

## Side-by-Side Comparison

### Input: High-Risk Entity Review

```json
{
  "applicant_type": "entity",
  "legal_name": "Acme Trading LLC",
  "jurisdiction": "BVI",
  "beneficial_owners": [{"name": "John Doe", "pct": 35, "nationality": "RU"}],
  "pep_declared": false,
  "screening_result": {"pep_hit": true, "confidence": 0.85}
}
```

### Anthropic's Rule Citations (Markdown)

```
escalation_reasons: [
  "rule 4.2: High-risk jurisdiction (BVI)",
  "rule 3.1: PEP exposure (RU beneficial owner)"
]
```

### JACI's Policy Citations (Canonical Objects)

```json
{
  "policy_refs": ["KYC-GEO-001", "KYC-PEP-001", "KYC-EDD-002"],
  "decision_id": "decision_a1b2c3",
  "trace_id": "trace_xyz789",
  "pack_id": "kyc_anthropic_cdd_lifecycle"
}
```

**Value Gap:**
- Anthropic: Rule IDs in response text (not machine-readable)
- JACI: Policy clause IDs with full cross-linkage to Decision, Trace, Evidence

## Next Steps

### Phase 2 Remaining
- [x] Policy registry complete
- [ ] Wire modes to Conductor
- [ ] Create KYC tools (reuse from custom kyc scenario)

### Phase 3: Demo
- [ ] Create gold cases from Anthropic's steering-examples.json
- [ ] Build side-by-side comparison script (Raw Anthropic vs JACI Governed)
- [ ] Run evaluation with policy citation metrics

## Files Modified

**Created:**
- `src/jaci/pack/kyc_anthropic_policy_registry.py` (550 lines)

**Updated:**
- `src/jaci/scenarios/kyc_anthropic/README.md` (marked policy registry complete)
- `docs/KYC_ANTHROPIC_POLICY_REGISTRY_SUMMARY.md` (this file)

## Attribution

All policy content derived from Anthropic's KYC Screener is clearly attributed with:
- Apache-2.0 license headers
- Original file references in docstrings
- `anthropic_kyc_screener` SourceRef in every policy
- `anthropic_rule_mapping` in domain_extensions

JazzX governance additions (autonomy ceilings, escalation paths, authority matrix) are marked as "JazzX Addition" in all documentation.
