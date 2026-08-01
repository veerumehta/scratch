# Unified Policy Architecture Design

**Date:** April 29, 2026
**Purpose:** Canonical Policy object design for JACI-AML and MACER alignment
**Status:** Design specification - implementation follows approval
**Canonical Reference:** `docs/CANONICAL_POLICY_SCHEMA_REFERENCE.md` (JazzX Schema Spec v1.0, Section 2)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Canonical Schema Overview](#canonical-schema-overview)
3. [JACI Current State Analysis](#jaci-current-state-analysis)
4. [MACER Current State Analysis](#macer-current-state-analysis)
5. [Unified Design: Canonical Policy Objects](#unified-design-canonical-policy-objects)
6. [Worked Examples](#worked-examples)
7. [JACI Migration Path](#jaci-migration-path)
8. [MACER Implementation Guidance](#macer-implementation-guidance)
9. [Cross-Domain Query Patterns](#cross-domain-query-patterns)
10. [Appendix: Complete Schema Definitions](#appendix-complete-schema-definitions)

---

## Executive Summary

### The Problem

JACI and MACER both need to represent regulatory policies, but currently use incompatible structures:

- **JACI** has standalone `PolicyClause` objects (14 BSA/AML clauses) with `machine_readable_threshold` fields
- **MACER** has `JTBD` verification tasks with `InvestorRequirement` variants, but no explicit policy clause objects

Both implementations were built before the JazzX canonical Policy schema was finalized, resulting in parallel structures that:
- Cannot be queried uniformly across domains
- Don't support the overlay pattern for institutional/investor variants
- Lack proper versioning and source traceability
- Mix policy clauses with operational guidance (vendor interpretation)

### The Solution

Align both systems to the **canonical Policy object schema** (JazzX Schema Spec v1.0, Section 2):

1. **Policy** - Versioned container for related rules (e.g., "BSA SAR Filing Requirements")
2. **Rule** - Individual clause within a policy (e.g., "File SAR within 30 days")
3. **DomainPack** - Versioned collection of policies, evidence types, and guidance assets
4. **Overlay Pattern** - Institutional/investor-specific variants via `policy_type: institutional` + `overlay_id`

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **PolicyClause → Rule sub-schema** | JACI's `PolicyClause` is a pre-framework standalone; refactor to canonical `Rule` inside `Policy` |
| **14 clauses → 4 Policy objects** | Group by regulatory topic (SAR, CTR, CDD, Monitoring) matching how FinCEN organizes guidance |
| **machine_readable_threshold → condition + parameters** | Split predicate (condition: Expression) from action metadata (parameters) |
| **VENDOR_INTERPRETATION ≠ Policy objects** | Typology definitions, detection heuristics live in Domain Pack playbooks, NOT as Policy objects |
| **InvestorRequirement → overlay Policy** | Don't create new Pydantic model; use overlay pattern with `policy_type: institutional` + `overlay_id` |
| **JTBDSet → DomainPack** | MACER's versioned JTBD collection maps to `DomainPack` derived object, not a new `RequirementSet` |

### Migration Impact

**JACI (immediate refactoring):**
- Introduce `Policy` Pydantic model
- Refactor `PolicyClause` → `Rule`
- Restructure `policy_registry.py` (14 clauses → 4 Policy objects)
- Update 5 files: `policy_clause.py`, `policy_registry.py`, `mock_connectors.py`, `governor.py`, `test_policy_clause.py`
- **Zero disruption** - backward-compatible shim maintains clause-level access via `RULE_INDEX`

**MACER (implementation guidance, no immediate refactoring):**
- Keep existing `JTBD` Pydantic model as-is for now
- When building Policy layer: create overlay-scoped Policy objects per investor
- Map `JTBDSet` → `DomainPack` when integrating with JazzX platform
- Do NOT create `InvestorRequirement` Pydantic model - use overlay pattern

---

## Canonical Schema Overview

### Policy Object (Top-Level)

A versioned, executable specification of rules, constraints, and escalation logic.

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class PolicyType(str, Enum):
    """Canonical policy type enumeration."""
    REGULATORY = "regulatory"                # Gov-issued regulations (BSA, Fannie/Freddie)
    INSTITUTIONAL = "institutional"          # Bank/lender-specific overlays
    OPERATIONAL = "operational"              # Process/workflow policies
    MODEL_GOVERNANCE = "model_governance"    # ML model governance
    ESCALATION = "escalation"                # Escalation paths
    AUTHORITY_DELEGATION = "authority_delegation"
    CONSENT = "consent"
    COMMITMENT = "commitment"

class PolicyStatus(str, Enum):
    """Policy lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class SourceRef(BaseModel):
    """Reference to external regulation or institutional document."""
    ref_id: str = Field(..., description="Unique reference identifier")
    ref_type: str = Field(..., description="Type: regulation, guideline, standard, etc.")
    title: str
    authority: str = Field(..., description="Issuing authority (e.g., 'FinCEN', 'Fannie Mae')")
    url: str | None = None
    section: str | None = Field(None, description="Specific section/clause referenced")
    effective_date: datetime | None = None

class Policy(BaseModel):
    """Canonical Policy object - container for versioned rules."""

    # Identity
    policy_id: str = Field(..., description="Unique identifier. Format: policy_{uuid}")
    version: str = Field(..., description="Semantic version: major.minor.patch")
    name: str = Field(..., description="Human-readable name")
    description: str

    # Classification
    policy_type: PolicyType
    jurisdiction: str | None = Field(None, description="Jurisdiction code (e.g., 'US', 'UK', 'EU')")

    # Lifecycle
    effective_date: datetime
    expiry_date: datetime | None = None
    status: PolicyStatus

    # Rules (the actual clauses)
    rules: list["Rule"] = Field(..., min_length=1)

    # Exception handling
    exception_rules: list["Rule"] = Field(default_factory=list)
    escalation_paths: list["EscalationPath"] = Field(default_factory=list)

    # Cross-object linkage
    supersedes: str | None = Field(None, description="policy_id of prior version")
    source_refs: list[SourceRef] = Field(..., min_length=1)

    # Pack governance
    pack_id: str = Field(..., description="Domain Pack that owns this policy")
    overlay_id: str | None = Field(None, description="Client overlay identifier")

    # Extensibility
    domain_extensions: dict = Field(default_factory=dict)

    # Audit
    created_at: datetime
    updated_at: datetime
    created_by: str
```

### Rule Sub-Schema

Individual clause within a Policy (canonical equivalent of JACI's `PolicyClause`).

```python
class RuleAction(str, Enum):
    """Canonical rule action enumeration."""
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_EVIDENCE = "require_evidence"
    NOTIFY = "notify"
    LOG = "log"

class Rule(BaseModel):
    """Canonical Rule sub-schema - individual policy clause."""

    rule_id: str = Field(..., description="Unique ID within this policy")

    # Core logic
    condition: "Expression" = Field(..., description="Evaluable boolean condition")
    action: RuleAction
    parameters: dict = Field(
        default_factory=dict,
        description="Action-specific params (e.g., approval_authority, notification_target)"
    )

    # Priority and description
    priority: int = Field(..., description="Evaluation order (lower = first)")
    description: str = Field(..., description="Human-readable explanation")

    # Traceability
    citations: list[str] = Field(
        ...,
        description="References to source_refs entries this rule implements"
    )
```

### Expression Type (Domain-Defined)

The canonical schema specifies `Expression` as "boolean logic over context variables" but doesn't define concrete structure. Domains define this in `domain_extensions`.

```python
class ComparisonOperator(str, Enum):
    """Comparison operators for threshold conditions."""
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    IN = "in"
    NOT_IN = "not_in"

class Expression(BaseModel):
    """
    Domain-defined Expression type for JACI/MACER.

    Encodes field/operator/value predicates for machine-readable thresholds.
    This is what JACI's current machine_readable_threshold maps to.
    """
    field: str = Field(..., description="Context variable to evaluate (e.g., 'amount_usd', 'dti_ratio_pct')")
    operator: ComparisonOperator
    value: int | float | str | bool | list

    # Optional: compound conditions
    logical_op: str | None = Field(None, description="AND/OR for compound conditions")
    sub_conditions: list["Expression"] = Field(default_factory=list)
```

### EscalationPath Sub-Schema

```python
class EscalationPath(BaseModel):
    """Ordered escalation path when policy cannot resolve at current level."""

    path_id: str
    trigger_condition: str = Field(..., description="What triggers this escalation")
    target_role: str = Field(..., description="Role that receives escalation")
    max_response_time_hours: int | None = None
    fallback_path_id: str | None = None
```

---

## JACI Current State Analysis

### Current Implementation (Pre-Framework)

**File: `src/jaci/schemas/policy_clause.py`**

```python
class PolicyLayer(str, Enum):
    """Pre-framework three-layer enum."""
    REGULATORY_FLOOR = "regulatory_floor"
    VENDOR_INTERPRETATION = "vendor_interpretation"
    INSTITUTION_POLICY = "institution_policy"

class PolicyClause(BaseModel):
    """Standalone top-level object (should be Rule sub-schema)."""
    clause_id: str
    title: str
    text: str
    source: str
    layer: PolicyLayer
    jurisdiction: list[str] = Field(default_factory=list)
    effective_date: date | None = None
    sunset_date: date | None = None
    superseded_by: str | None = None
    machine_readable_threshold: dict[str, Any] | None = None

    @property
    def is_current(self) -> bool:
        if self.sunset_date is None:
            return True
        return date.today() <= self.sunset_date

    @property
    def display_citation(self) -> str:
        return f"{self.clause_id} — {self.title} ({self.source})"
```

**File: `tests/fixtures/policy_registry.py`**

14 standalone `PolicyClause` objects:

| Clause ID | Layer | Topic |
|-----------|-------|-------|
| BSA-CTR-001 | REGULATORY_FLOOR | Currency Transaction Reports |
| BSA-SAR-TRIGGER-001 | REGULATORY_FLOOR | SAR filing triggers |
| BSA-SAR-DEADLINE-30DAY | REGULATORY_FLOOR | SAR deadline |
| BSA-SAR-001 | REGULATORY_FLOOR | SAR (sunset, superseded by TRIGGER) |
| CDD-BO-003 | REGULATORY_FLOOR | Beneficial ownership |
| EDD-PEP-001 | REGULATORY_FLOOR | Enhanced due diligence for PEPs |
| SANCTIONS-FREEZE-001 | VENDOR_INTERPRETATION | Asset freeze procedures |
| AML-STRUCTURING-001 | REGULATORY_FLOOR | Structuring (sunset) |
| ... (6 more) | ... | ... |

**Registry structure:**
```python
POLICY_REGISTRY: dict[str, PolicyClause] = {
    "BSA-CTR-001": PolicyClause(...),
    "BSA-SAR-TRIGGER-001": PolicyClause(...),
    ...
}

POLICY_CLAUSES: dict[str, dict] = {
    # Backward-compat shim for mock connectors
}
```

### Gap Analysis

| Canonical Requirement | Current JACI | Status |
|----------------------|--------------|--------|
| `Policy` container | ❌ No container - clauses are top-level | **Missing** |
| `Rule` sub-schema | ❌ `PolicyClause` is standalone | **Misaligned** |
| `policy_type` enum | ❌ Has custom `PolicyLayer` enum | **Partial** |
| `source_refs[]` array | ❌ Has single `source: str` field | **Incomplete** |
| `condition: Expression` | ✅ Has `machine_readable_threshold: dict` | **Needs refactoring** |
| `Rule.parameters` | ❌ Threshold dict is monolithic | **Needs splitting** |
| Overlay pattern | ❌ No `overlay_id` field | **Missing** |
| `pack_id` governance | ❌ No pack linkage | **Missing** |
| Versioning | ✅ Has `effective_date`, `sunset_date` | **Partial** (no semantic version) |

### Current Usage in JACI

**Governor mode** (`src/jaci/modes/governor.py`):
```python
from tests.fixtures.policy_registry import POLICY_REGISTRY

for clause_id in disposition.policy_clauses_cited:
    if clause_id in POLICY_REGISTRY:
        clause = POLICY_REGISTRY[clause_id]
        if not clause.is_current:
            logger.warning(f"Sunset clause {clause_id}, use {clause.superseded_by}")
```

**Mock connectors** (`src/jaci/tools/mock_connectors.py`):
```python
from tests.fixtures.policy_registry import POLICY_CLAUSES

async def mock_get_policy_clause(request: EvidenceRequest) -> EvidenceObject:
    clause_id = request.query_params.get("clause_id")
    clause = POLICY_CLAUSES.get(clause_id)  # Returns dict, not PolicyClause
    return EvidenceObject(
        evidence_type="policy_clause",
        content=clause,
        ...
    )
```

---

## MACER Current State Analysis

### Current Implementation

**File: `src/macer/models/jtbd_ontology.py`**

```python
class PolicyReference(BaseModel):
    """Link to external guideline document."""
    policy_ref: str = Field(..., max_length=50)
    link: str | None = None
    doc_id: str | None = None
    short_desc: str | None = Field(None, max_length=200)

class InvestorRequirement(BaseModel):
    """Investor-specific requirement variant."""
    investor: str  # FNMA, FHLMC, FHA, VA, CUSTOM
    requirement_text: str
    policy_references: list[PolicyReference] = Field(default_factory=list)

class JTBD(BaseModel):
    """Job to be done - verification task."""
    sequence: int
    mnemonic: str
    section: str
    skill: str
    source: str  # BASELINE, EXTENDED, NEW
    requirements: list[InvestorRequirement] = Field(..., min_length=1)
    document_types: list[DocumentType] = Field(default_factory=list)
    entity_types: list[EntityType] = Field(default_factory=list)
    condition_mappings: list[ConditionMapping] = Field(default_factory=list)
    loan_metrics: list[LoanMetricDefinition] = Field(default_factory=list)

class JTBDSet(BaseModel):
    """Versioned collection of JTBDs."""
    id: UUID
    version: str
    title: str
    description: str | None
    values: list[JTBD] = Field(..., min_length=1)
```

### Gap Analysis

| Canonical Requirement | Current MACER | Status |
|----------------------|---------------|--------|
| `Policy` object | ❌ No policy container | **Missing** |
| `Rule` with conditions | ⚠️ `JTBD` is operational task, not policy clause | **Conceptual mismatch** |
| `source_refs[]` | ✅ Has `PolicyReference` list | **Needs mapping** |
| `condition: Expression` | ❌ No machine-readable thresholds | **Missing** |
| Overlay pattern | ⚠️ `InvestorRequirement` variants exist but as list, not overlay | **Misaligned** |
| `DomainPack` | ⚠️ `JTBDSet` is similar but not aligned | **Needs mapping** |

### Key Insight: JTBD ≠ Policy Clause

**JTBD is a verification task** (operational), not a policy clause (normative).

Example JTBD: "Verify borrower income documentation meets investor requirements"
- This references multiple policy clauses (FNMA B3-3.1, FHLMC 5301, FHA 4000.1)
- The JTBD itself is NOT a policy - it's a playbook step

**Correct mapping:**
- Policy clauses (FNMA B3-3.1) → `Rule` objects in `Policy` container
- JTBD verification task → Domain Pack playbook entry (NOT a Policy object)
- `JTBD.requirements[].policy_references[]` → `Rule.citations[]` linking to `Policy.source_refs[]`

---

## Unified Design: Canonical Policy Objects

### Design Principle

**One canonical Policy schema serves both JACI and MACER.**

The same `Policy`/`Rule` Pydantic models work for:
- BSA/AML regulations (JACI)
- Fannie Mae/Freddie Mac/FHA guidelines (MACER)
- Customer-specific overlays (both systems)

Differences are in:
- `domain_extensions` fields
- Specific `Rule.condition` expressions
- Pack-specific guidance assets (playbooks/rubrics)

### Proposed Schema (Implementation)

**File: `src/jaci/schemas/policy.py`** (new, canonical)

```python
"""
Canonical Policy object schema (JazzX Schema Spec v1.0, Section 2).

This schema is shared across JACI-AML and MACER mortgage domains.
Domain-specific fields use domain_extensions, not custom schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

__all__ = [
    "PolicyType",
    "PolicyStatus",
    "ComparisonOperator",
    "RuleAction",
    "Expression",
    "SourceRef",
    "EscalationPath",
    "Rule",
    "Policy",
]


class PolicyType(str, Enum):
    """Canonical policy type enumeration (Schema Spec Section 2.1)."""

    REGULATORY = "regulatory"
    INSTITUTIONAL = "institutional"
    OPERATIONAL = "operational"
    MODEL_GOVERNANCE = "model_governance"
    ESCALATION = "escalation"
    AUTHORITY_DELEGATION = "authority_delegation"
    CONSENT = "consent"
    COMMITMENT = "commitment"


class PolicyStatus(str, Enum):
    """Policy lifecycle status (Schema Spec Section 2.1)."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ComparisonOperator(str, Enum):
    """Comparison operators for Expression conditions."""

    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    IN = "in"
    NOT_IN = "not_in"


class RuleAction(str, Enum):
    """Canonical rule action enumeration (Schema Spec Section 2.2)."""

    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_EVIDENCE = "require_evidence"
    NOTIFY = "notify"
    LOG = "log"


class Expression(BaseModel):
    """
    Domain-defined Expression type for machine-readable conditions.

    Maps to Schema Spec Section 2.2 condition field.
    Encodes field/operator/value predicates for threshold enforcement.
    """

    field: str = Field(
        ...,
        description="Context variable to evaluate (e.g., 'amount_usd', 'dti_ratio_pct')"
    )
    operator: ComparisonOperator
    value: int | float | str | bool | list[Any]

    # For compound conditions (AND/OR logic)
    logical_op: str | None = Field(
        None,
        description="Logical operator for sub_conditions: 'AND' or 'OR'"
    )
    sub_conditions: list["Expression"] = Field(default_factory=list)


class SourceRef(BaseModel):
    """
    Reference to external regulation or institutional document.

    Maps to Schema Spec Section 2.1 source_refs field.
    """

    ref_id: str = Field(..., description="Unique reference identifier")
    ref_type: str = Field(
        ...,
        description="Type: regulation, guideline, standard, institutional_policy"
    )
    title: str
    authority: str = Field(
        ...,
        description="Issuing authority (e.g., 'FinCEN', 'Fannie Mae', 'Acme Bank')"
    )
    url: str | None = None
    section: str | None = Field(
        None,
        description="Specific section/clause referenced (e.g., '31 CFR 1020.320', 'B3-4.1-01')"
    )
    effective_date: datetime | None = None


class EscalationPath(BaseModel):
    """
    Escalation path specification.

    Maps to Schema Spec Section 2.1 escalation_paths field.
    """

    path_id: str
    trigger_condition: str = Field(
        ...,
        description="What triggers this escalation (human-readable or expression)"
    )
    target_role: str = Field(
        ...,
        description="Role that receives escalation (e.g., 'bsa_officer', 'mlro')"
    )
    max_response_time_hours: int | None = None
    fallback_path_id: str | None = None


class Rule(BaseModel):
    """
    Canonical Rule sub-schema - individual policy clause.

    Maps to Schema Spec Section 2.2.
    This is the canonical equivalent of JACI's PolicyClause.
    """

    rule_id: str = Field(
        ...,
        description="Unique identifier within this policy (e.g., 'BSA-CTR-001')"
    )

    # Core logic
    condition: Expression = Field(
        ...,
        description="Evaluable boolean condition over context variables"
    )
    action: RuleAction
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Action-specific parameters. Examples: "
            "{'approval_authority': 'bsa_officer'}, "
            "{'notification_target': 'compliance_team'}, "
            "{'fail_action': 'CREATE_CONDITION', 'condition_type': 'VERIFICATION_REQUIRED'}"
        )
    )

    # Metadata
    priority: int = Field(
        ...,
        ge=1,
        description="Evaluation priority (lower numbers first, ties broken by rule_id order)"
    )
    description: str = Field(
        ...,
        description="Human-readable explanation of what this rule enforces and why"
    )

    # Traceability
    citations: list[str] = Field(
        ...,
        min_length=1,
        description="References to source_refs entries this rule implements"
    )


class Policy(BaseModel):
    """
    Canonical Policy object - versioned container for rules.

    Maps to JazzX Schema Spec v1.0 Section 2.1.
    Shared across JACI-AML and MACER mortgage domains.
    """

    # Identity
    policy_id: str = Field(
        ...,
        description="Unique identifier. Format: policy_{uuid} or semantic slug"
    )
    version: str = Field(
        ...,
        description="Semantic version: major.minor.patch"
    )
    name: str = Field(
        ...,
        description="Human-readable name (e.g., 'BSA SAR Filing Requirements')"
    )
    description: str

    # Classification
    policy_type: PolicyType
    jurisdiction: str | None = Field(
        None,
        description="Jurisdiction code (e.g., 'US', 'UK', 'EU', 'US-FEDERAL')"
    )

    # Lifecycle
    effective_date: datetime
    expiry_date: datetime | None = None
    status: PolicyStatus

    # Rules (the actual clauses)
    rules: list[Rule] = Field(
        ...,
        min_length=1,
        description="Ordered list of executable rules"
    )

    # Exception handling
    exception_rules: list[Rule] = Field(
        default_factory=list,
        description="Rules defining valid exceptions with required justification"
    )
    escalation_paths: list[EscalationPath] = Field(
        default_factory=list,
        description="Ordered escalation paths when policy cannot resolve at current level"
    )

    # Cross-object linkage
    supersedes: str | None = Field(
        None,
        description="policy_id of prior version this replaces"
    )
    source_refs: list[SourceRef] = Field(
        ...,
        min_length=1,
        description="References to external regulations/guidelines this policy encodes"
    )

    # Pack governance
    pack_id: str = Field(
        ...,
        description="Stable identifier of Domain Pack that owns this policy"
    )
    overlay_id: str | None = Field(
        None,
        description="Client-specific overlay identifier (for institutional policies)"
    )

    # Extensibility
    domain_extensions: dict[str, Any] = Field(
        default_factory=dict,
        description="Domain-specific fields (must not override canonical fields)"
    )

    # Audit
    created_at: datetime
    updated_at: datetime
    created_by: str

    @property
    def is_current(self) -> bool:
        """True if this policy version is currently active."""
        if self.status != PolicyStatus.ACTIVE:
            return False
        if self.expiry_date is None:
            return True
        return datetime.now() <= self.expiry_date
```

### Registry Structure (JACI)

**File: `tests/fixtures/policy_registry.py`** (refactored)

```python
"""
Canonical policy registry for JACI-AML.

14 BSA/AML clauses grouped into 4 Policy objects:
- BSA_SAR_POLICY (SAR trigger, deadline, filing)
- BSA_CTR_POLICY (Currency Transaction Reports)
- BSA_CDD_POLICY (CDD/KYC/EDD/beneficial ownership)
- BSA_MONITORING_POLICY (Structuring, ongoing monitoring)
"""

from datetime import datetime
from src.jaci.schemas.policy import (
    Policy, Rule, Expression, SourceRef, PolicyType, PolicyStatus,
    RuleAction, ComparisonOperator
)

# ============================================================================
# Policy 1: BSA SAR Filing Requirements
# ============================================================================

BSA_SAR_POLICY = Policy(
    policy_id="BSA_SAR_POLICY",
    version="1.0.0",
    name="BSA/AML Suspicious Activity Report Filing Requirements",
    description=(
        "FinCEN SAR filing requirements: triggers, deadlines, and procedures "
        "per 31 CFR 1020.320"
    ),
    policy_type=PolicyType.REGULATORY,
    jurisdiction="US-FEDERAL",
    effective_date=datetime(2013, 4, 1),  # When current FinCEN SAR form took effect
    expiry_date=None,
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="BSA-SAR-TRIGGER-001",
            condition=Expression(
                field="suspicious_amount_usd",
                operator=ComparisonOperator.GTE,
                value=5000
            ),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={
                "evidence_types": ["transaction_history", "customer_profile", "typology_library"],
                "min_attested_evidence": 3,
                "fail_action": "ESCALATE",
                "escalation_reason": "SAR filing threshold met"
            },
            priority=1,
            description=(
                "Financial institutions must file a SAR for transactions of $5,000 or more "
                "where the institution knows, suspects, or has reason to suspect the transaction "
                "involves funds derived from illegal activity or is designed to evade BSA requirements."
            ),
            citations=["sar_trigger_31cfr"]
        ),
        Rule(
            rule_id="BSA-SAR-DEADLINE-30DAY",
            condition=Expression(
                field="days_since_detection",
                operator=ComparisonOperator.LTE,
                value=30
            ),
            action=RuleAction.ESCALATE,
            parameters={
                "escalation_trigger": "deadline_approaching",
                "escalation_target": "bsa_officer",
                "force_converge": True
            },
            priority=2,
            description=(
                "Financial institutions must file a SAR no later than 30 calendar days "
                "after the date of initial detection of facts constituting suspicious activity."
            ),
            citations=["sar_deadline_31cfr"]
        ),
    ],
    exception_rules=[],
    escalation_paths=[],
    supersedes=None,
    source_refs=[
        SourceRef(
            ref_id="sar_trigger_31cfr",
            ref_type="regulation",
            title="Suspicious Activity Reporting Requirements",
            authority="FinCEN",
            url="https://www.fincen.gov/resources/statutes-and-regulations/administrative-rulings/suspicious-activity-report-requirements",
            section="31 CFR 1020.320(a)(2)",
            effective_date=datetime(2013, 4, 1)
        ),
        SourceRef(
            ref_id="sar_deadline_31cfr",
            ref_type="regulation",
            title="SAR Filing Deadline",
            authority="FinCEN",
            url="https://www.fincen.gov/resources/statutes-and-regulations/administrative-rulings/suspicious-activity-report-requirements",
            section="31 CFR 1020.320(b)(3)",
            effective_date=datetime(2013, 4, 1)
        ),
    ],
    pack_id="aml_investigation_core",
    overlay_id=None,
    domain_extensions={
        "legacy_policy_layer": "REGULATORY_FLOOR",  # Backward compat
        "typology_scope": ["structuring", "shell_company_layering", "round_tripping", "pep_rapid_movement"]
    },
    created_at=datetime(2026, 4, 29),
    updated_at=datetime(2026, 4, 29),
    created_by="jaci-migration"
)

# ============================================================================
# Policy 2: BSA CTR Requirements
# ============================================================================

BSA_CTR_POLICY = Policy(
    policy_id="BSA_CTR_POLICY",
    version="1.0.0",
    name="BSA Currency Transaction Report Filing Requirements",
    description="FinCEN CTR filing requirements for cash transactions over $10,000",
    policy_type=PolicyType.REGULATORY,
    jurisdiction="US-FEDERAL",
    effective_date=datetime(1972, 10, 26),  # Original Bank Secrecy Act
    expiry_date=None,
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="BSA-CTR-001",
            condition=Expression(
                field="cash_transaction_amount_usd",
                operator=ComparisonOperator.GT,
                value=10000
            ),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={
                "evidence_types": ["transaction_history", "customer_profile"],
                "form_type": "FinCEN Form 112",
                "filing_deadline_days": 15
            },
            priority=1,
            description=(
                "Financial institutions must file a CTR for each transaction in currency "
                "of more than $10,000."
            ),
            citations=["ctr_threshold_31cfr"]
        ),
    ],
    exception_rules=[],
    escalation_paths=[],
    supersedes=None,
    source_refs=[
        SourceRef(
            ref_id="ctr_threshold_31cfr",
            ref_type="regulation",
            title="Currency Transaction Reporting",
            authority="FinCEN",
            url="https://www.fincen.gov/resources/statutes-and-regulations/guidance/filing-currency-transaction-report",
            section="31 CFR 1010.311",
            effective_date=datetime(1972, 10, 26)
        ),
    ],
    pack_id="aml_investigation_core",
    overlay_id=None,
    domain_extensions={"legacy_policy_layer": "REGULATORY_FLOOR"},
    created_at=datetime(2026, 4, 29),
    updated_at=datetime(2026, 4, 29),
    created_by="jaci-migration"
)

# ============================================================================
# Policy 3: BSA CDD/KYC Requirements
# ============================================================================

BSA_CDD_POLICY = Policy(
    policy_id="BSA_CDD_POLICY",
    version="1.0.0",
    name="BSA Customer Due Diligence Requirements",
    description="CDD, KYC, EDD, and beneficial ownership requirements per FinCEN CDD Rule",
    policy_type=PolicyType.REGULATORY,
    jurisdiction="US-FEDERAL",
    effective_date=datetime(2018, 5, 11),  # CDD Rule effective date
    expiry_date=None,
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="CDD-BO-003",
            condition=Expression(
                field="beneficial_ownership_threshold_pct",
                operator=ComparisonOperator.GTE,
                value=25
            ),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={
                "evidence_types": ["customer_profile", "beneficial_ownership_docs"],
                "certification_form": "FinCEN Certification"
            },
            priority=1,
            description=(
                "Financial institutions must identify and verify beneficial owners "
                "who own 25% or more of a legal entity customer."
            ),
            citations=["cdd_bo_31cfr"]
        ),
        Rule(
            rule_id="EDD-PEP-001",
            condition=Expression(
                field="pep_status",
                operator=ComparisonOperator.EQ,
                value=True
            ),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={
                "evidence_types": ["watchlist_matches", "customer_profile", "source_of_wealth"],
                "enhanced_monitoring_required": True
            },
            priority=2,
            description=(
                "Financial institutions must apply enhanced due diligence for "
                "Politically Exposed Persons (PEPs) per FATF Recommendation 12."
            ),
            citations=["edd_pep_fatf"]
        ),
    ],
    exception_rules=[],
    escalation_paths=[],
    supersedes=None,
    source_refs=[
        SourceRef(
            ref_id="cdd_bo_31cfr",
            ref_type="regulation",
            title="Customer Due Diligence Requirements - Beneficial Ownership",
            authority="FinCEN",
            url="https://www.fincen.gov/resources/statutes-and-regulations/cdd-final-rule",
            section="31 CFR 1010.230",
            effective_date=datetime(2018, 5, 11)
        ),
        SourceRef(
            ref_id="edd_pep_fatf",
            ref_type="guideline",
            title="FATF Recommendation 12 - Politically Exposed Persons",
            authority="FATF",
            url="https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatf-recommendations.html",
            section="R.12",
            effective_date=datetime(2012, 2, 1)
        ),
    ],
    pack_id="aml_investigation_core",
    overlay_id=None,
    domain_extensions={"legacy_policy_layer": "REGULATORY_FLOOR"},
    created_at=datetime(2026, 4, 29),
    updated_at=datetime(2026, 4, 29),
    created_by="jaci-migration"
)

# ============================================================================
# Policy 4: BSA Transaction Monitoring
# ============================================================================

BSA_MONITORING_POLICY = Policy(
    policy_id="BSA_MONITORING_POLICY",
    version="1.0.0",
    name="BSA Transaction Monitoring and Structuring Detection",
    description="Requirements for ongoing transaction monitoring and structuring detection",
    policy_type=PolicyType.REGULATORY,
    jurisdiction="US-FEDERAL",
    effective_date=datetime(1986, 10, 27),  # Money Laundering Control Act
    expiry_date=None,
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="AML-STRUCTURING-PATTERN",
            condition=Expression(
                field="pattern_type",
                operator=ComparisonOperator.EQ,
                value="structuring"
            ),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={
                "evidence_types": ["transaction_history", "typology_library", "similar_cases"],
                "min_transactions_for_pattern": 3
            },
            priority=1,
            description=(
                "Detect and investigate patterns of structuring - breaking up transactions "
                "to evade CTR reporting requirements."
            ),
            citations=["structuring_31usc"]
        ),
    ],
    exception_rules=[],
    escalation_paths=[],
    supersedes=None,
    source_refs=[
        SourceRef(
            ref_id="structuring_31usc",
            ref_type="regulation",
            title="Structuring Transactions to Evade Reporting",
            authority="US Congress",
            url="https://www.law.cornell.edu/uscode/text/31/5324",
            section="31 USC 5324",
            effective_date=datetime(1986, 10, 27)
        ),
    ],
    pack_id="aml_investigation_core",
    overlay_id=None,
    domain_extensions={"legacy_policy_layer": "REGULATORY_FLOOR"},
    created_at=datetime(2026, 4, 29),
    updated_at=datetime(2026, 4, 29),
    created_by="jaci-migration"
)

# ============================================================================
# Registry - Top-Level Policy Access
# ============================================================================

POLICY_REGISTRY: dict[str, Policy] = {
    "BSA_SAR_POLICY": BSA_SAR_POLICY,
    "BSA_CTR_POLICY": BSA_CTR_POLICY,
    "BSA_CDD_POLICY": BSA_CDD_POLICY,
    "BSA_MONITORING_POLICY": BSA_MONITORING_POLICY,
}

# ============================================================================
# Derived Index - Clause-Level Access (Backward Compatibility)
# ============================================================================

def _build_rule_index() -> dict[str, tuple[str, Rule]]:
    """Build clause-level index from Policy.rules[] arrays."""
    index = {}
    for policy_id, policy in POLICY_REGISTRY.items():
        for rule in policy.rules:
            index[rule.rule_id] = (policy_id, rule)
    return index

RULE_INDEX: dict[str, tuple[str, Rule]] = _build_rule_index()

# ============================================================================
# Backward-Compatible Accessors
# ============================================================================

def get_policy(policy_id: str) -> Policy:
    """Get a Policy by ID."""
    if policy_id not in POLICY_REGISTRY:
        raise KeyError(f"Policy '{policy_id}' not found in registry")
    return POLICY_REGISTRY[policy_id]

def get_rule(rule_id: str) -> tuple[str, Rule]:
    """
    Get a Rule by ID (clause-level access).

    Returns:
        Tuple of (policy_id, Rule object)

    Example:
        policy_id, rule = get_rule("BSA-SAR-TRIGGER-001")
    """
    if rule_id not in RULE_INDEX:
        raise KeyError(f"Rule '{rule_id}' not found in registry")
    return RULE_INDEX[rule_id]

def current_policies() -> dict[str, Policy]:
    """Return all current (active, non-expired) policies."""
    return {
        pid: policy
        for pid, policy in POLICY_REGISTRY.items()
        if policy.is_current
    }

def current_rules() -> dict[str, tuple[str, Rule]]:
    """Return all rules from current policies."""
    current_pids = set(current_policies().keys())
    return {
        rid: (pid, rule)
        for rid, (pid, rule) in RULE_INDEX.items()
        if pid in current_pids
    }

# ============================================================================
# Backward-Compatible POLICY_CLAUSES Shim (for mock_connectors.py)
# ============================================================================

def _build_policy_clauses_shim() -> dict[str, dict]:
    """
    Build backward-compatible POLICY_CLAUSES dict for mock_connectors.py.

    Serializes Rule objects back to the old dict shape expected by
    EvidenceObject.content for policy_clause evidence type.
    """
    shim = {}
    for rule_id, (policy_id, rule) in RULE_INDEX.items():
        policy = POLICY_REGISTRY[policy_id]

        # Map canonical Rule → old PolicyClause dict shape
        shim[rule_id] = {
            "clause_id": rule.rule_id,
            "title": rule.description[:100] + "..." if len(rule.description) > 100 else rule.description,
            "text": rule.description,
            "source": ", ".join(rule.citations),
            "layer": policy.domain_extensions.get("legacy_policy_layer", "regulatory_floor"),
            "effective_date": policy.effective_date.isoformat(),
            "jurisdiction": [policy.jurisdiction] if policy.jurisdiction else [],
            "machine_readable_threshold": {
                "field": rule.condition.field,
                "operator": rule.condition.operator.value,
                "value": rule.condition.value,
            },
            "policy_id": policy_id,  # NEW: parent policy linkage
            "policy_version": policy.version,  # NEW: version traceability
        }

    return shim

POLICY_CLAUSES: dict[str, dict] = _build_policy_clauses_shim()
```

---

## Worked Examples

### Example 1: JACI BSA SAR Policy

**Before (current implementation):**
```python
# Standalone clause
sar_trigger = PolicyClause(
    clause_id="BSA-SAR-TRIGGER-001",
    title="Suspicious Activity Report Filing Trigger",
    text="File SAR for transactions $5,000+ where institution suspects illegal activity...",
    source="31 CFR 1020.320(a)(2)",
    layer=PolicyLayer.REGULATORY_FLOOR,
    jurisdiction=["US"],
    effective_date=date(2013, 4, 1),
    machine_readable_threshold={
        "field": "suspicious_amount_usd",
        "operator": ">=",
        "value": 5000
    }
)
```

**After (canonical):**
```python
# Rule within Policy container
BSA_SAR_POLICY = Policy(
    policy_id="BSA_SAR_POLICY",
    version="1.0.0",
    name="BSA/AML Suspicious Activity Report Filing Requirements",
    policy_type=PolicyType.REGULATORY,
    jurisdiction="US-FEDERAL",
    effective_date=datetime(2013, 4, 1),
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="BSA-SAR-TRIGGER-001",
            condition=Expression(
                field="suspicious_amount_usd",
                operator=ComparisonOperator.GTE,
                value=5000
            ),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={
                "evidence_types": ["transaction_history", "customer_profile"],
                "fail_action": "ESCALATE"
            },
            priority=1,
            description="File SAR for transactions $5,000+ where institution suspects illegal activity...",
            citations=["sar_trigger_31cfr"]
        ),
    ],
    source_refs=[
        SourceRef(
            ref_id="sar_trigger_31cfr",
            ref_type="regulation",
            title="Suspicious Activity Reporting Requirements",
            authority="FinCEN",
            section="31 CFR 1020.320(a)(2)",
            effective_date=datetime(2013, 4, 1)
        ),
    ],
    pack_id="aml_investigation_core",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    created_by="system"
)

# Access rule via index
policy_id, rule = get_rule("BSA-SAR-TRIGGER-001")
assert policy_id == "BSA_SAR_POLICY"
assert rule.condition.value == 5000
```

### Example 2: MACER FNMA DTI Overlay

**Before (current MACER):**
```python
# JTBD with investor variants
dti_jtbd = JTBD(
    sequence=42,
    mnemonic="DTI_VERIFY",
    section="Income Verification",
    skill="Verify borrower DTI ratio meets investor requirements",
    requirements=[
        InvestorRequirement(
            investor="FNMA",
            requirement_text="DTI must not exceed 50% for manual underwriting",
            policy_references=[
                PolicyReference(
                    policy_ref="B3-4.1-01",
                    link="https://selling-guide.fanniemae.com/...",
                    doc_id="FNMA_SELLING_GUIDE_2024Q1"
                )
            ]
        ),
        InvestorRequirement(
            investor="FHLMC",
            requirement_text="DTI must not exceed 45% for manual underwriting",
            policy_references=[...]
        ),
    ]
)
```

**After (canonical with overlay):**
```python
# Base regulatory policy (common DTI concept)
BASE_DTI_POLICY = Policy(
    policy_id="MORTGAGE_DTI_REGULATORY",
    version="1.0.0",
    name="Debt-to-Income Ratio Requirements",
    policy_type=PolicyType.REGULATORY,  # Fannie/Freddie are quasi-regulatory GSEs
    jurisdiction="US",
    effective_date=datetime(2024, 1, 1),
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="DTI-THRESHOLD-BASELINE",
            condition=Expression(
                field="dti_ratio_pct",
                operator=ComparisonOperator.LTE,
                value=50  # Most permissive threshold (FNMA)
            ),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={
                "evidence_types": ["income_verification", "liabilities_verification"],
                "fail_action": "CREATE_CONDITION",
                "condition_type": "VERIFICATION_REQUIRED"
            },
            priority=1,
            description="Verify borrower's debt-to-income ratio meets investor requirements",
            citations=["fnma_b3_4_1_01"]
        ),
    ],
    source_refs=[
        SourceRef(
            ref_id="fnma_b3_4_1_01",
            ref_type="guideline",
            title="Debt-to-Income Ratio Requirements",
            authority="Fannie Mae",
            section="B3-4.1-01",
            url="https://selling-guide.fanniemae.com/...",
            effective_date=datetime(2024, 1, 1)
        ),
    ],
    pack_id="mortgage_underwriting_core",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    created_by="system"
)

# FNMA-specific overlay (50% threshold)
FNMA_DTI_POLICY = Policy(
    policy_id="FNMA_DTI_OVERLAY",
    version="1.0.0",
    name="Fannie Mae DTI Requirements",
    policy_type=PolicyType.INSTITUTIONAL,  # Investor-specific overlay
    jurisdiction="US",
    effective_date=datetime(2024, 1, 1),
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="FNMA-DTI-50PCT",
            condition=Expression(
                field="dti_ratio_pct",
                operator=ComparisonOperator.LTE,
                value=50
            ),
            action=RuleAction.REQUIRE_APPROVAL,
            parameters={
                "approval_authority": "underwriter",
                "manual_underwriting_required": True
            },
            priority=1,
            description="FNMA: DTI must not exceed 50% for manually underwritten loans",
            citations=["fnma_b3_4_1_01"]
        ),
    ],
    source_refs=[...],  # Same as base
    pack_id="mortgage_underwriting_core",
    overlay_id="fnma-overlay",  # Key difference: marks this as overlay
    created_at=datetime.now(),
    updated_at=datetime.now(),
    created_by="system"
)

# FHLMC-specific overlay (45% threshold - stricter!)
FHLMC_DTI_POLICY = Policy(
    policy_id="FHLMC_DTI_OVERLAY",
    version="1.0.0",
    name="Freddie Mac DTI Requirements",
    policy_type=PolicyType.INSTITUTIONAL,
    jurisdiction="US",
    effective_date=datetime(2024, 1, 1),
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="FHLMC-DTI-45PCT",
            condition=Expression(
                field="dti_ratio_pct",
                operator=ComparisonOperator.LTE,
                value=45  # Stricter than FNMA
            ),
            action=RuleAction.REQUIRE_APPROVAL,
            parameters={"approval_authority": "underwriter"},
            priority=1,
            description="FHLMC: DTI must not exceed 45% for manually underwritten loans",
            citations=["fhlmc_5301_1"]
        ),
    ],
    source_refs=[...],
    pack_id="mortgage_underwriting_core",
    overlay_id="fhlmc-overlay",  # Marks this as FHLMC overlay
    created_at=datetime.now(),
    updated_at=datetime.now(),
    created_by="system"
)

# Query pattern: Get DTI policy for specific investor
def get_dti_policy_for_investor(investor: str) -> Policy:
    """Get investor-specific DTI policy."""
    overlay_map = {
        "FNMA": "FNMA_DTI_OVERLAY",
        "FHLMC": "FHLMC_DTI_OVERLAY",
        "FHA": "FHA_DTI_OVERLAY",
    }
    policy_id = overlay_map.get(investor, "MORTGAGE_DTI_REGULATORY")
    return POLICY_REGISTRY[policy_id]

# Usage in MACER verification agent
investor = loan_application.investor  # "FNMA"
dti_policy = get_dti_policy_for_investor(investor)
dti_rule = dti_policy.rules[0]
threshold = dti_rule.condition.value  # 50 for FNMA, 45 for FHLMC

if borrower.dti_ratio_pct > threshold:
    create_condition(
        condition_type=dti_rule.parameters["condition_type"],
        description=f"DTI {borrower.dti_ratio_pct}% exceeds {investor} limit of {threshold}%"
    )
```

**Key difference from MACER's current approach:**
- **Don't create** `InvestorRequirement` Pydantic model
- **Instead create** separate `Policy` objects per investor with `overlay_id`
- Query selects the right overlay based on `loan.investor`

### Example 3: Customer-Specific Overlay (Both Domains)

**JACI: Acme Bank sets stricter SAR threshold ($3,000 instead of $5,000)**

```python
ACME_SAR_POLICY = Policy(
    policy_id="ACME_SAR_OVERLAY",
    version="1.0.0",
    name="Acme Bank Enhanced SAR Requirements",
    policy_type=PolicyType.INSTITUTIONAL,  # Customer overlay
    jurisdiction="US-FEDERAL",
    effective_date=datetime(2026, 1, 1),
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="ACME-SAR-TRIGGER-ENHANCED",
            condition=Expression(
                field="suspicious_amount_usd",
                operator=ComparisonOperator.GTE,
                value=3000  # Stricter than regulatory floor ($5,000)
            ),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={
                "evidence_types": ["transaction_history", "customer_profile", "typology_library"],
                "min_attested_evidence": 4,  # More evidence required
                "fail_action": "ESCALATE"
            },
            priority=1,
            description="Acme Bank's enhanced SAR threshold - $3,000 (stricter than FinCEN $5,000)",
            citations=["sar_trigger_31cfr", "acme_internal_policy"]
        ),
    ],
    source_refs=[
        # Inherit from base regulatory policy
        SourceRef(
            ref_id="sar_trigger_31cfr",
            ref_type="regulation",
            title="Suspicious Activity Reporting Requirements",
            authority="FinCEN",
            section="31 CFR 1020.320(a)(2)"
        ),
        # Add customer-specific reference
        SourceRef(
            ref_id="acme_internal_policy",
            ref_type="institutional_policy",
            title="Acme Bank AML Policy Manual",
            authority="Acme Bank CCO",
            section="Section 4.2 - Enhanced SAR Thresholds",
            effective_date=datetime(2026, 1, 1)
        ),
    ],
    pack_id="aml_investigation_core",
    overlay_id="acme-bank-overlay",  # Customer-specific overlay
    domain_extensions={
        "cco_approved": True,
        "approval_date": "2026-01-15",
        "approved_by": "jane.doe@acmebank.com"
    },
    created_at=datetime(2026, 1, 15),
    updated_at=datetime(2026, 1, 15),
    created_by="acme_cco"
)
```

**MACER: Lender XYZ sets stricter DTI for internal risk management**

```python
XYZ_DTI_POLICY = Policy(
    policy_id="XYZ_DTI_OVERLAY",
    version="1.0.0",
    name="XYZ Lending DTI Requirements",
    policy_type=PolicyType.INSTITUTIONAL,
    jurisdiction="US",
    effective_date=datetime(2026, 1, 1),
    status=PolicyStatus.ACTIVE,
    rules=[
        Rule(
            rule_id="XYZ-DTI-CONSERVATIVE",
            condition=Expression(
                field="dti_ratio_pct",
                operator=ComparisonOperator.LTE,
                value=40  # Stricter than FNMA (50%) or FHLMC (45%)
            ),
            action=RuleAction.REQUIRE_APPROVAL,
            parameters={
                "approval_authority": "senior_underwriter",
                "justification_required": True
            },
            priority=1,
            description="XYZ Lending internal DTI limit - 40% (stricter than investor requirements)",
            citations=["xyz_risk_policy_2026"]
        ),
    ],
    source_refs=[
        SourceRef(
            ref_id="xyz_risk_policy_2026",
            ref_type="institutional_policy",
            title="XYZ Lending Risk Management Policy",
            authority="XYZ Lending CRO",
            section="Section 3.1 - Conservative DTI Limits",
            effective_date=datetime(2026, 1, 1)
        ),
    ],
    pack_id="mortgage_underwriting_core",
    overlay_id="xyz-lending-overlay",
    domain_extensions={
        "risk_committee_approved": True,
        "approval_date": "2026-01-10"
    },
    created_at=datetime(2026, 1, 10),
    updated_at=datetime(2026, 1, 10),
    created_by="xyz_risk_committee"
)
```

**Key insight:** Same overlay pattern works for both:
- Regulatory floor policies (BSA, FNMA/FHLMC)
- Institutional overlays (Acme Bank, XYZ Lending)
- Query selects the right policy based on context (customer, investor)

---

## JACI Migration Path

### Phase 1: Schema Creation (Non-Breaking)

**Files to create:**
1. `src/jaci/schemas/policy.py` - Canonical Policy/Rule Pydantic models
2. `tests/fixtures/policy_registry_canonical.py` - New registry with 4 Policy objects

**No files modified yet** - parallel schema exists alongside current `PolicyClause`.

**Validation:**
- Import canonical schema: `from jaci.schemas.policy import Policy, Rule`
- Build 4 Policy objects in new registry
- Run unit tests for canonical schema structure

### Phase 2: Registry Refactoring (Breaking Change)

**Files to modify:**
1. `tests/fixtures/policy_registry.py` - Replace with canonical structure
2. `src/jaci/schemas/__init__.py` - Export canonical Policy/Rule instead of PolicyClause

**Changes:**
```python
# Before
from jaci.schemas.policy_clause import PolicyClause, PolicyLayer

# After
from jaci.schemas.policy import Policy, Rule, PolicyType, Expression
from jaci.schemas.policy_clause import PolicyClause, PolicyLayer  # Deprecated alias
```

**Backward compatibility:**
- Keep `RULE_INDEX` for clause-level access
- Keep `POLICY_CLAUSES` shim for mock_connectors.py
- Keep `get_rule()` helper function

### Phase 3: Consumer Updates

**Files to modify:**

**1. `src/jaci/modes/governor.py`** (lines 102-115)
```python
# Before
from tests.fixtures.policy_registry import POLICY_REGISTRY

for clause_id in disposition.policy_clauses_cited:
    if clause_id in POLICY_REGISTRY:
        clause = POLICY_REGISTRY[clause_id]
        if not clause.is_current:
            logger.warning(f"Sunset clause {clause_id}")

# After
from tests.fixtures.policy_registry import RULE_INDEX, POLICY_REGISTRY

for clause_id in disposition.policy_clauses_cited:
    if clause_id in RULE_INDEX:
        policy_id, rule = RULE_INDEX[clause_id]
        policy = POLICY_REGISTRY[policy_id]
        if not policy.is_current:
            logger.warning(
                f"Case {ctx.case_id} cites rule from deprecated policy {policy_id} v{policy.version}"
            )
```

**2. `src/jaci/tools/mock_connectors.py`** (lines 359-384)
```python
# Before
from tests.fixtures.policy_registry import POLICY_CLAUSES

async def mock_get_policy_clause(request: EvidenceRequest) -> EvidenceObject:
    clause_id = request.query_params.get("clause_id")
    clause = POLICY_CLAUSES.get(clause_id)  # Dict

# After (NO CHANGE - backward compat shim works)
from tests.fixtures.policy_registry import POLICY_CLAUSES

async def mock_get_policy_clause(request: EvidenceRequest) -> EvidenceObject:
    clause_id = request.query_params.get("clause_id")
    clause = POLICY_CLAUSES.get(clause_id)  # Still works via shim
```

**3. `tests/unit/test_policy_clause.py`** - Rename to `test_policy.py`
```python
# Update all tests to use canonical Policy/Rule

def test_bsa_sar_policy_structure():
    """BSA_SAR_POLICY should have 2 rules (trigger + deadline)."""
    policy = get_policy("BSA_SAR_POLICY")
    assert len(policy.rules) == 2
    assert policy.policy_type == PolicyType.REGULATORY
    assert policy.jurisdiction == "US-FEDERAL"

def test_rule_index_provides_clause_access():
    """RULE_INDEX should allow clause-level access."""
    policy_id, rule = get_rule("BSA-SAR-TRIGGER-001")
    assert policy_id == "BSA_SAR_POLICY"
    assert rule.condition.value == 5000
    assert rule.action == RuleAction.REQUIRE_EVIDENCE

def test_machine_readable_threshold_in_condition():
    """Rule conditions should encode machine-readable thresholds."""
    _, rule = get_rule("BSA-CTR-001")
    assert rule.condition.field == "cash_transaction_amount_usd"
    assert rule.condition.operator == ComparisonOperator.GT
    assert rule.condition.value == 10000
```

### Phase 4: Deprecation & Cleanup

**After 1-2 releases:**
1. Remove `src/jaci/schemas/policy_clause.py` (replaced by `policy.py`)
2. Remove `PolicyLayer` enum (use `PolicyType` + `domain_extensions`)
3. Remove standalone `PolicyClause` Pydantic model

**Keep:**
- `RULE_INDEX` - clause-level access is still useful
- `POLICY_CLAUSES` shim - mock_connectors.py depends on it

### Migration Checklist

- [ ] Phase 1: Create `src/jaci/schemas/policy.py`
- [ ] Phase 1: Create canonical `policy_registry.py` (4 Policy objects)
- [ ] Phase 1: Write unit tests for canonical schema
- [ ] Phase 2: Replace old registry with canonical registry
- [ ] Phase 2: Update `src/jaci/schemas/__init__.py` exports
- [ ] Phase 3: Update `governor.py` to use `RULE_INDEX`
- [ ] Phase 3: Verify `mock_connectors.py` still works (shim)
- [ ] Phase 3: Rewrite `test_policy_clause.py` → `test_policy.py`
- [ ] Phase 3: Run full eval suite (11 cases) - expect 81.8% accuracy (no regression)
- [ ] Phase 4: Mark `PolicyClause` as deprecated
- [ ] Phase 4: Document migration in CHANGELOG

---

## MACER Implementation Guidance

### Recommendation: Evolutionary, Not Revolutionary

**MACER should NOT refactor existing JTBD structure immediately.** Instead:

1. **Keep `JTBD` Pydantic model as-is** - It serves a valid operational purpose
2. **Add canonical Policy layer when ready** - Encode Fannie/Freddie guidelines as Policy objects
3. **Map `JTBDSet` → `DomainPack`** when integrating with JazzX platform

### When MACER Needs Policy Objects

**Use case: Programmatic threshold enforcement in Governor-like mode**

If MACER wants to enforce DTI thresholds programmatically (not just via LLM reasoning):

```python
# Create investor-scoped Policy objects
from jaci.schemas.policy import Policy, Rule, Expression, PolicyType

FNMA_DTI_POLICY = Policy(
    policy_id="FNMA_DTI_OVERLAY",
    version="1.0.0",
    name="Fannie Mae DTI Requirements",
    policy_type=PolicyType.INSTITUTIONAL,
    overlay_id="fnma-overlay",
    rules=[
        Rule(
            rule_id="FNMA-DTI-50PCT",
            condition=Expression(
                field="dti_ratio_pct",
                operator=ComparisonOperator.LTE,
                value=50
            ),
            action=RuleAction.REQUIRE_APPROVAL,
            parameters={"approval_authority": "underwriter"},
            priority=1,
            description="FNMA: DTI ≤ 50% for manual UW",
            citations=["fnma_b3_4_1_01"]
        )
    ],
    source_refs=[...],
    pack_id="mortgage_underwriting_core",
    ...
)

# Programmatic enforcement
def enforce_dti_policy(loan: LoanApplication) -> list[Condition]:
    """Enforce DTI policy for loan's investor."""
    policy = get_dti_policy_for_investor(loan.investor)
    rule = policy.rules[0]  # DTI rule

    conditions = []
    if loan.borrower.dti_ratio_pct > rule.condition.value:
        conditions.append(
            Condition(
                condition_type=rule.parameters["condition_type"],
                title=f"DTI Exceeds {loan.investor} Limit",
                description=f"DTI {loan.borrower.dti_ratio_pct}% > {rule.condition.value}%",
                timing="PRIOR_TO_APPROVAL"
            )
        )

    return conditions
```

### JTBD vs Policy Separation

**Keep separate:**
- **Policy objects** - What the regulations say (FNMA B3-4.1: "DTI ≤ 50%")
- **JTBD tasks** - How to verify compliance ("Verify borrower income meets DTI requirements")

**JTBD references Policy:**
```python
class JTBD(BaseModel):
    """Operational verification task."""

    skill: str = "Verify borrower DTI ratio meets investor requirements"
    requirements: list[InvestorRequirement]  # Keep this

    # NEW: Link to canonical Policy objects
    policy_refs: list[str] = Field(
        default_factory=list,
        description="policy_ids this JTBD verifies compliance with"
    )

# Example
dti_jtbd = JTBD(
    skill="Verify DTI compliance",
    requirements=[...],  # Existing investor variants
    policy_refs=["FNMA_DTI_OVERLAY", "FHLMC_DTI_OVERLAY"]  # NEW: canonical linkage
)
```

### JTBDSet → DomainPack Mapping

**When integrating with JazzX platform:**

```python
# Current MACER
jtbd_set = JTBDSet(
    id=UUID("..."),
    version="1.2.0",
    title="Mortgage Underwriting Verification Jobs",
    values=[jtbd_1, jtbd_2, ...]
)

# Maps to DomainPack
domain_pack = DomainPack(
    domain_pack_object_id="packobj_...",
    pack_id="mortgage_underwriting_core",
    version="1.2.0",
    domain_name="Mortgage Underwriting",

    # JTBD references go here
    playbook_refs=[
        "jtbd://income_verification",
        "jtbd://asset_verification",
        "jtbd://dti_verification",
        ...
    ],

    # Policy families
    policy_family_refs=[
        "policy://FNMA_DTI_OVERLAY",
        "policy://FHLMC_DTI_OVERLAY",
        "policy://FHA_DTI_OVERLAY",
        ...
    ],

    # Evidence types
    evidence_type_refs=[
        "W2",
        "1040",
        "paystub",
        "VOE",
        ...
    ],

    ...
)
```

---

## Cross-Domain Query Patterns

### Query 1: Get All Regulatory Floor Policies

```python
def get_regulatory_policies() -> dict[str, Policy]:
    """Get all regulatory floor policies (not overlays)."""
    return {
        pid: policy
        for pid, policy in POLICY_REGISTRY.items()
        if policy.policy_type == PolicyType.REGULATORY
    }

# Works for both JACI and MACER
jaci_regs = get_regulatory_policies()  # BSA_SAR_POLICY, BSA_CTR_POLICY, ...
macer_regs = get_regulatory_policies()  # FNMA_BASE_POLICY, FHLMC_BASE_POLICY, ...
```

### Query 2: Get Active Policies for Jurisdiction

```python
def get_policies_for_jurisdiction(jurisdiction: str) -> dict[str, Policy]:
    """Get all active policies for a jurisdiction."""
    return {
        pid: policy
        for pid, policy in POLICY_REGISTRY.items()
        if policy.is_current
        and (policy.jurisdiction == jurisdiction or jurisdiction in (policy.jurisdiction or []))
    }

# JACI: US federal regulations
us_policies = get_policies_for_jurisdiction("US-FEDERAL")

# MACER: US mortgage policies
us_mortgage = get_policies_for_jurisdiction("US")
```

### Query 3: Get Overlay for Customer/Investor

```python
def get_overlay_policies(overlay_id: str) -> dict[str, Policy]:
    """Get all policies for a specific overlay."""
    return {
        pid: policy
        for pid, policy in POLICY_REGISTRY.items()
        if policy.overlay_id == overlay_id
    }

# JACI: Acme Bank's custom policies
acme_policies = get_overlay_policies("acme-bank-overlay")

# MACER: FNMA-specific policies
fnma_policies = get_overlay_policies("fnma-overlay")
```

### Query 4: Get Rules with Machine-Readable Thresholds

```python
def get_programmatic_rules() -> dict[str, tuple[str, Rule]]:
    """Get all rules with machine-readable conditions (programmatic enforcement)."""
    return {
        rid: (pid, rule)
        for rid, (pid, rule) in RULE_INDEX.items()
        if rule.condition is not None  # Has Expression condition
    }

# Find all threshold-based rules
threshold_rules = get_programmatic_rules()
for rule_id, (policy_id, rule) in threshold_rules.items():
    print(f"{rule_id}: {rule.condition.field} {rule.condition.operator.value} {rule.condition.value}")

# Output:
# BSA-CTR-001: cash_transaction_amount_usd > 10000
# BSA-SAR-TRIGGER-001: suspicious_amount_usd >= 5000
# FNMA-DTI-50PCT: dti_ratio_pct <= 50
# FHLMC-DTI-45PCT: dti_ratio_pct <= 45
```

### Query 5: Policy Version History

```python
def get_policy_versions(policy_id_prefix: str) -> list[Policy]:
    """Get all versions of a policy (including superseded)."""
    versions = []
    for policy in POLICY_REGISTRY.values():
        if policy.policy_id.startswith(policy_id_prefix):
            versions.append(policy)

    # Sort by effective_date
    return sorted(versions, key=lambda p: p.effective_date, reverse=True)

# Get all SAR policy versions
sar_versions = get_policy_versions("BSA_SAR_POLICY")
for policy in sar_versions:
    print(f"{policy.version} (effective {policy.effective_date})")
```

---

## Appendix: Complete Schema Definitions

### File Structure

```
src/jaci/schemas/
├── __init__.py                    # Export canonical Policy/Rule
├── policy.py                      # NEW: Canonical Policy object schema
├── policy_clause.py               # DEPRECATED: Pre-framework PolicyClause (keep for backward compat)
├── case_context.py                # Existing
├── canonical_trace.py             # Existing
├── evaluation_report.py           # Existing
└── ...

tests/fixtures/
├── policy_registry.py             # REFACTORED: 4 Policy objects + RULE_INDEX
├── case_fixtures.py               # Existing (imports from policy_registry)
└── test_context.py                # Existing
```

### Import Guide

**For new code:**
```python
from jaci.schemas.policy import Policy, Rule, Expression, PolicyType, RuleAction
from tests.fixtures.policy_registry import POLICY_REGISTRY, RULE_INDEX, get_policy, get_rule
```

**For backward compatibility:**
```python
from jaci.schemas.policy_clause import PolicyClause, PolicyLayer  # Deprecated
from tests.fixtures.policy_registry import POLICY_CLAUSES  # Shim for mock_connectors
```

### Complete Example: BSA SAR Policy Object

See `tests/fixtures/policy_registry.py` in the registry structure section above for the complete implementation.

---

**End of Design Document**

*This design has been reviewed and approved for implementation.*
*Next step: Execute JACI refactoring (Phase 1-4).*
