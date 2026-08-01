# Canonical Objects via JAPES — Architecture and Migration Plan

**Date:** 2026-04-29  
**Status:** Design — ready for implementation  
**Scope:** Policy object first; extend to all five canonical objects  
**Goal:** Canonical objects live in knowledge-hub, accessed by JACI/MACER through japes SDK facade

---

## 1. Current State

```
JACI
└── src/jaci/schemas/policy_clause.py   ← deprecated, inline Pydantic models
└── tests/fixtures/policy_registry.py   ← in-memory dict of 14 PolicyClause objects
└── japes_handler.py                    ← uses ctx.runtime.knowledge_hub (KH client)
```

JACI depends on `japes @ git+https://github.com/JazzX-LLC/japes.git@dev` (pyproject.toml).

The japes SDK exposes:
```
jazzx_runtime_sdk/
├── client_layer.py          ← ClientLayer with .kernel, .knowledge_hub, .process
├── clients/
│   └── knowledge_hub_client.py  ← KnowledgeHubClient wrapping auto-gen KH API
│       ├── Collections / Documents (RAG)
│       ├── Ontologies / Entities / Triples (knowledge graph)
│       └── Policies (Rego/OPA — NOT II canonical Policy objects)
```

**Key observation:** KnowledgeHubClient already has `create_policy` / `read_policy` / `read_policies` methods — but these are **Rego/OPA policies** (executable rule bundles for the OPA engine), NOT the JazzX canonical `Policy` objects (Schema Spec v1.0 Section 2). These are different things. The canonical Policy objects need their own storage path.

---

## 2. Target Architecture

```
knowledge-hub (KH)            ← authoritative store for canonical objects
     ↑ client-api (auto-gen)  ← KH background team: add canonical object CRUD endpoints
     ↑
japes / jazzx_runtime_sdk     ← facade layer (our change now)
     ├── canonical_objects/
     │   ├── models.py        ← Pydantic models for II canonical objects
     │   ├── policy_store.py  ← CRUD + caching for Policy objects
     │   └── __init__.py
     └── client_layer.py      ← add .canonical_objects property
     ↑
JACI / MACER                  ← consumers (read only for policy)
     └── ctx.runtime.canonical_objects.get_policy("BSA_SAR_POLICY")
```

### Phasing

**Phase 1 (now):** Add canonical object models and in-memory store to japes SDK.  
JACI switches from local `policy_clause.py` / `policy_registry.py` to `ctx.runtime.canonical_objects`.  
Knowledge-hub stores them via the existing **entity** mechanism (entity_type="canonical_policy").

**Phase 2 (KH team, background):** KH adds native canonical object endpoints to client-api.  
japes `policy_store.py` switches its backing store from entity-based to native endpoints.  
JACI/MACER callsites are unchanged.

---

## 3. What Needs to Be Built in japes

### 3.1 New directory: `jazzx_runtime_sdk/canonical_objects/`

#### `models.py` — Canonical II object Pydantic models

These are the Pydantic representations of the JazzX Schema Spec v1.0 types.  
Source of truth: `docs/CANONICAL_POLICY_SCHEMA_REFERENCE.md`.

```python
# jazzx_runtime_sdk/canonical_objects/models.py

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class PolicyType(str, Enum):
    REGULATORY = "regulatory"
    INSTITUTIONAL = "institutional"
    OPERATIONAL = "operational"
    MODEL_GOVERNANCE = "model_governance"
    ESCALATION = "escalation"
    AUTHORITY_DELEGATION = "authority_delegation"
    CONSENT = "consent"
    COMMITMENT = "commitment"


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class RuleAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_EVIDENCE = "require_evidence"
    NOTIFY = "notify"
    LOG = "log"


class SourceRef(BaseModel):
    ref_id: str
    title: str
    authority: str
    section: Optional[str] = None
    url: Optional[str] = None
    effective_date: Optional[datetime] = None


class Expression(BaseModel):
    """Machine-readable condition expression. Domain-specific encoding."""
    field: str
    operator: str  # >, <, >=, <=, ==, !=, in, not_in
    value: Any
    # domain_extensions for additional context
    domain_extensions: Optional[dict[str, Any]] = None


class Rule(BaseModel):
    """Individual clause within a Policy. Canonical Rule sub-schema (Schema Spec v1.0 §2)."""
    rule_id: str
    condition: Optional[Expression] = None  # None = unconditional rule
    action: RuleAction
    parameters: Optional[dict[str, Any]] = None  # e.g. approval_authority, fail_action
    priority: int = 100
    description: str
    citations: list[str] = Field(default_factory=list)  # refs to source_refs entries
    domain_extensions: Optional[dict[str, Any]] = None


class Policy(BaseModel):
    """
    Canonical Policy object — Schema Spec v1.0 Section 2.
    Versioned, executable specification of rules, constraints, authority matrices.
    """
    policy_id: str  # Format: policy_{uuid} or semantic slug (e.g. BSA_SAR_POLICY)
    version: str    # semver major.minor.patch
    name: str
    description: str
    policy_type: PolicyType
    jurisdiction: Optional[str] = None
    effective_date: datetime
    expiry_date: Optional[datetime] = None
    status: PolicyStatus = PolicyStatus.ACTIVE
    rules: list[Rule] = Field(default_factory=list)
    exception_rules: list[Rule] = Field(default_factory=list)
    supersedes: Optional[str] = None  # policy_id of prior version
    source_refs: list[SourceRef] = Field(default_factory=list)
    pack_id: str
    overlay_id: Optional[str] = None
    domain_extensions: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    @property
    def is_active(self) -> bool:
        if self.status != PolicyStatus.ACTIVE:
            return False
        if self.expiry_date is None:
            return True
        return datetime.utcnow() <= self.expiry_date

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
```

#### `policy_store.py` — Backed by KH entities (Phase 1), native endpoints (Phase 2)

```python
# jazzx_runtime_sdk/canonical_objects/policy_store.py

"""
PolicyStore — facade for canonical Policy objects.

Phase 1: Stores/retrieves Policy objects as KH entities with entity_type="canonical_policy".
Phase 2: KH team adds native endpoints; switch backing store here without touching callers.

Usage from handler:
    store = ctx.runtime.canonical_objects
    policy = await store.get_policy("BSA_SAR_POLICY")
    rules = policy.rules
    rule = policy.get_rule("BSA-SAR-DEADLINE-30DAY")
"""

import json
import logging
from typing import Optional, TYPE_CHECKING

from jazzx_runtime_sdk.canonical_objects.models import Policy

if TYPE_CHECKING:
    from jazzx_runtime_sdk.clients.knowledge_hub_client import KnowledgeHubClient

logger = logging.getLogger(__name__)

# Collection name for canonical objects in KH
_CANONICAL_COLLECTION_NAME = "jazzx-canonical-objects"
_ENTITY_TYPE = "canonical_policy"


class PolicyStore:
    """
    CRUD facade for canonical Policy objects.

    Backed by KH entity store in Phase 1.
    In-memory cache keyed by policy_id for read-heavy access patterns.
    """

    def __init__(self, kh_client: "KnowledgeHubClient"):
        self._kh = kh_client
        self._cache: dict[str, Policy] = {}
        self._collection_id: Optional[str] = None

    async def _ensure_collection(self) -> str:
        """Get or create the canonical objects collection in KH."""
        if self._collection_id:
            return self._collection_id
        collection = await self._kh.get_collection_by_name(_CANONICAL_COLLECTION_NAME)
        if collection is None:
            collection = await self._kh.create_collection(
                name=_CANONICAL_COLLECTION_NAME,
                description="JazzX canonical II objects (Policy, etc.)",
            )
        self._collection_id = collection["id"]
        return self._collection_id

    async def put_policy(self, policy: Policy, ontology_id: str) -> str:
        """
        Store a Policy object in KH.

        Args:
            policy: Policy object to store
            ontology_id: KH ontology ID to associate with (use canonical_objects ontology)

        Returns:
            KH entity ID
        """
        collection_id = await self._ensure_collection()
        json_value = json.loads(policy.model_dump_json())
        response = await self._kh.create_entity(
            name=policy.policy_id,
            collection_id=collection_id,
            ontology_id=ontology_id,
            entity_type=_ENTITY_TYPE,
            json_value=json_value,
        )
        if hasattr(response, "parsed") and response.parsed is not None:
            result = response.parsed.to_dict() if hasattr(response.parsed, "to_dict") else dict(response.parsed)
            entity_id = result.get("id", "")
            self._cache[policy.policy_id] = policy
            logger.info(f"Policy stored: {policy.policy_id} -> entity {entity_id}")
            return entity_id
        raise RuntimeError(f"Failed to store policy {policy.policy_id}: HTTP {response.status_code}")

    async def get_policy(self, policy_id: str) -> Optional[Policy]:
        """
        Retrieve a Policy by policy_id.

        Uses in-memory cache; falls back to KH entity query.
        """
        if policy_id in self._cache:
            return self._cache[policy_id]

        collection_id = await self._ensure_collection()
        # Query entities by name (policy_id used as entity name)
        entities = await self._kh.read_entities(
            odata_query=f"name eq '{policy_id}' and entity_type eq '{_ENTITY_TYPE}'"
        )
        if not entities:
            logger.warning(f"Policy not found in KH: {policy_id}")
            return None

        entity = entities[0]
        jv = entity.get("json_value") or {}
        policy = Policy.model_validate(jv)
        self._cache[policy_id] = policy
        return policy

    async def list_policies(
        self,
        pack_id: Optional[str] = None,
        policy_type: Optional[str] = None,
    ) -> list[Policy]:
        """List policies, optionally filtered by pack_id or policy_type."""
        collection_id = await self._ensure_collection()
        odata = f"entity_type eq '{_ENTITY_TYPE}'"
        entities = await self._kh.read_entities(odata_query=odata, limit=500)

        policies = []
        for entity in entities:
            jv = entity.get("json_value") or {}
            try:
                policy = Policy.model_validate(jv)
                if pack_id and policy.pack_id != pack_id:
                    continue
                if policy_type and policy.policy_type.value != policy_type:
                    continue
                policies.append(policy)
            except Exception as e:
                logger.warning(f"Failed to parse policy entity: {e}")
        return policies

    def preload(self, policies: list[Policy]) -> None:
        """
        Pre-populate the in-memory cache from a static list.

        Use this in test/dev environments or during bootstrap to avoid
        KH round-trips when KH is not available.

        Example:
            store.preload(BSA_POLICIES)  # from pack's policy registry
        """
        for policy in policies:
            self._cache[policy.policy_id] = policy
        logger.info(f"PolicyStore: preloaded {len(policies)} policies into cache")

    def clear_cache(self) -> None:
        """Clear the in-memory cache (forces re-fetch from KH on next access)."""
        self._cache.clear()


class CanonicalObjectStore:
    """
    Top-level store for all canonical II objects.
    Accessed as ctx.runtime.canonical_objects

    Currently implements Policy. Evidence, Decision, Trace, Outcome to follow.
    """

    def __init__(self, kh_client: "KnowledgeHubClient"):
        self._policy_store = PolicyStore(kh_client)

    @property
    def policy(self) -> PolicyStore:
        return self._policy_store

    # Convenience pass-throughs:
    async def get_policy(self, policy_id: str) -> Optional[Policy]:
        return await self._policy_store.get_policy(policy_id)

    def preload_policies(self, policies: list[Policy]) -> None:
        self._policy_store.preload(policies)
```

#### `__init__.py`

```python
# jazzx_runtime_sdk/canonical_objects/__init__.py
from jazzx_runtime_sdk.canonical_objects.models import (
    Policy, Rule, Expression, SourceRef,
    PolicyType, PolicyStatus, RuleAction,
)
from jazzx_runtime_sdk.canonical_objects.policy_store import (
    PolicyStore, CanonicalObjectStore,
)

__all__ = [
    "Policy", "Rule", "Expression", "SourceRef",
    "PolicyType", "PolicyStatus", "RuleAction",
    "PolicyStore", "CanonicalObjectStore",
]
```

### 3.2 Wire into `ClientLayer`

In `client_layer.py`, add a `canonical_objects` property alongside `knowledge_hub`:

```python
# In ClientLayer.__init__, add:
self._canonical_object_store = None

# New property:
@property
def canonical_objects(self) -> "CanonicalObjectStore":
    if self._canonical_object_store is None:
        from jazzx_runtime_sdk.canonical_objects import CanonicalObjectStore
        self._canonical_object_store = CanonicalObjectStore(self.knowledge_hub)
    return self._canonical_object_store
```

### 3.3 Export from SDK `__init__.py`

Add to `jazzx_runtime_sdk/__init__.py`:

```python
from jazzx_runtime_sdk.canonical_objects import (
    Policy, Rule, Expression, SourceRef,
    PolicyType, PolicyStatus, RuleAction,
    CanonicalObjectStore,
)
```

And add all to `__all__`.

---

## 4. What Changes in JACI

### 4.1 Remove deprecated dependency

`policy_clause.py` and `policy_registry.py` (in tests/fixtures) are replaced.

The canonical Policy objects for JACI-AML are defined in a new file:

```
src/jaci/pack/policy_registry.py   ← replaces tests/fixtures/policy_registry.py
```

This file defines the BSA_SAR_POLICY, BSA_CTR_POLICY, BSA_CDD_POLICY objects using
the canonical `Policy` / `Rule` models from japes, and registers them at startup.

### 4.2 Handler startup: preload policies

In `japes_handler.py`, during `startup()`:

```python
from jaci.pack.policy_registry import AML_POLICIES

async def startup(self) -> None:
    # Preload canonical policy objects into in-memory cache
    # In dev/test: uses preload() (no KH round-trip)
    # In prod: preload() for fast bootstrap, KH for authoritative refresh
    pass  # handled by runtime bootstrap (see below)
```

Or in `main()`, after creating the runtime:

```python
from jaci.pack.policy_registry import AML_POLICIES

runtime = JazzXRuntime(...)
# Preload pack-defined policy objects into canonical store
runtime.client_layer.canonical_objects.preload_policies(AML_POLICIES)
```

### 4.3 Governor: switch policy access

Before:
```python
from tests.fixtures.policy_registry import POLICY_REGISTRY
clause = POLICY_REGISTRY.get(clause_id)
```

After:
```python
# In governor.py, receive canonical_store via constructor or ctx:
policy = await ctx.runtime.canonical_objects.get_policy("BSA_SAR_POLICY")
rule = policy.get_rule(rule_id)
```

Or for the common case of checking a single rule threshold:
```python
sar_policy = await ctx.runtime.canonical_objects.get_policy("BSA_SAR_POLICY")
deadline_rule = sar_policy.get_rule("BSA-SAR-DEADLINE-30DAY")
threshold = deadline_rule.condition.value  # 30
```

### 4.4 CanonicalTrace.policies_applied and Decision.policy_refs

These already use `policy_id` strings. After migration, those strings reference
`Policy.policy_id` values (e.g. `"BSA_SAR_POLICY"`). No field type change — just
ensuring the IDs used at runtime match what's in the store.

---

## 5. JACI Pack Policy Registry (new file)

```python
# src/jaci/pack/policy_registry.py
"""
JACI-AML canonical Policy objects.

These are the pack-owned, canonical II Policy objects for the AML investigation domain.
They are loaded into the CanonicalObjectStore at runtime and accessed via:
    ctx.runtime.canonical_objects.get_policy("BSA_SAR_POLICY")

All three policy objects are policy_type=REGULATORY (FinCEN/BSA regulatory floor).
Institution-specific overlays are handled by Certified Client Overlay pattern, not here.

Structure:
  BSA_SAR_POLICY   — SAR trigger detection, 30-day deadline, human-only filing
  BSA_CTR_POLICY   — CTR $10K threshold, structuring detection
  BSA_CDD_POLICY   — CDD/KYC, EDD for high-risk, beneficial ownership, PEP screening
"""

from datetime import datetime
from jazzx_runtime_sdk.canonical_objects import (
    Policy, Rule, Expression, SourceRef,
    PolicyType, PolicyStatus, RuleAction,
)

_PACK_ID = "aml-investigation-core"
_FINCEN_SOURCE = SourceRef(
    ref_id="FINCEN-BSA-2025",
    title="Bank Secrecy Act Regulations",
    authority="FinCEN",
    url="https://www.fincen.gov/resources/statutes-and-regulations",
    effective_date=datetime(2025, 1, 1),
)

BSA_SAR_POLICY = Policy(
    policy_id="BSA_SAR_POLICY",
    version="1.0.0",
    name="BSA/AML SAR Filing Requirements",
    description="Rules governing when to file a SAR, filing deadlines, and human-only decision authority.",
    policy_type=PolicyType.REGULATORY,
    jurisdiction="US-FEDERAL",
    effective_date=datetime(2025, 1, 1),
    status=PolicyStatus.ACTIVE,
    pack_id=_PACK_ID,
    source_refs=[_FINCEN_SOURCE],
    rules=[
        Rule(
            rule_id="BSA-SAR-TRIGGER-001",
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={"evidence_types": ["transaction_pattern", "kyc_artifact", "entity_profile"]},
            priority=10,
            description="File SAR when transaction activity is suspicious and may involve criminal proceeds or structuring.",
            citations=["FINCEN-BSA-2025"],
        ),
        Rule(
            rule_id="BSA-SAR-DEADLINE-30DAY",
            condition=Expression(field="days_since_detection", operator="<=", value=30),
            action=RuleAction.ESCALATE,
            parameters={"fail_action": "FORCE_CONVERGE", "escalation_reason": "30-day SAR deadline"},
            priority=5,
            description="SAR must be filed within 30 calendar days of initial detection of suspicious activity.",
            citations=["FINCEN-BSA-2025"],
        ),
        Rule(
            rule_id="BSA-SAR-HUMAN-ONLY",
            action=RuleAction.REQUIRE_APPROVAL,
            parameters={"approval_authority": "bsa_officer", "human_only": True},
            priority=1,
            description="SAR filing decision is human-only. No AI system may approve SAR submission. Autonomy level 0.",
            citations=["FINCEN-BSA-2025"],
        ),
    ],
)

BSA_CTR_POLICY = Policy(
    policy_id="BSA_CTR_POLICY",
    version="1.0.0",
    name="BSA Currency Transaction Report Requirements",
    description="Rules governing CTR filing for cash transactions and structuring detection.",
    policy_type=PolicyType.REGULATORY,
    jurisdiction="US-FEDERAL",
    effective_date=datetime(2025, 1, 1),
    status=PolicyStatus.ACTIVE,
    pack_id=_PACK_ID,
    source_refs=[_FINCEN_SOURCE],
    rules=[
        Rule(
            rule_id="BSA-CTR-001",
            condition=Expression(field="cash_transaction_amount_usd", operator=">", value=10000),
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={"evidence_types": ["transaction_summary"], "filing": "CTR"},
            priority=10,
            description="File CTR for cash transactions exceeding $10,000 in a single business day.",
            citations=["FINCEN-BSA-2025"],
        ),
        Rule(
            rule_id="BSA-STRUCTURING-001",
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={"evidence_types": ["transaction_pattern"], "typology": "structuring"},
            priority=20,
            description="Detect and report structuring: deliberate transactions below $10K to evade CTR reporting.",
            citations=["FINCEN-BSA-2025"],
        ),
    ],
)

BSA_CDD_POLICY = Policy(
    policy_id="BSA_CDD_POLICY",
    version="1.0.0",
    name="Customer Due Diligence and KYC Requirements",
    description="CDD, EDD, beneficial ownership, and PEP screening rules.",
    policy_type=PolicyType.REGULATORY,
    jurisdiction="US-FEDERAL",
    effective_date=datetime(2025, 1, 1),
    status=PolicyStatus.ACTIVE,
    pack_id=_PACK_ID,
    source_refs=[_FINCEN_SOURCE],
    rules=[
        Rule(
            rule_id="BSA-CDD-001",
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={"evidence_types": ["kyc_artifact"]},
            priority=30,
            description="Verify customer identity and business purpose at onboarding and on material change.",
            citations=["FINCEN-BSA-2025"],
        ),
        Rule(
            rule_id="BSA-EDD-HIGH-RISK",
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={"evidence_types": ["kyc_artifact", "entity_profile"], "edd": True},
            priority=20,
            description="Apply Enhanced Due Diligence for high-risk customers (PEPs, high-risk jurisdictions, complex structures).",
            citations=["FINCEN-BSA-2025"],
        ),
        Rule(
            rule_id="BSA-BENEFICIAL-OWNERSHIP",
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={"evidence_types": ["beneficial_ownership_record"]},
            priority=20,
            description="Identify and verify beneficial owners (>=25% ownership) for legal entity customers.",
            citations=["FINCEN-BSA-2025"],
        ),
        Rule(
            rule_id="BSA-PEP-SCREENING",
            action=RuleAction.REQUIRE_EVIDENCE,
            parameters={"evidence_types": ["pep_screening_result"], "typology": "pep"},
            priority=15,
            description="Screen all customers and beneficial owners against PEP lists; apply EDD if PEP match.",
            citations=["FINCEN-BSA-2025"],
        ),
    ],
)

# All pack policies — pass to runtime.canonical_objects.preload_policies()
AML_POLICIES = [BSA_SAR_POLICY, BSA_CTR_POLICY, BSA_CDD_POLICY]

# Convenience index: rule_id → (policy, rule) for direct rule lookup
RULE_INDEX: dict[str, tuple[Policy, Rule]] = {
    rule.rule_id: (policy, rule)
    for policy in AML_POLICIES
    for rule in policy.rules
}
```

---

## 6. What the KH Team Needs (Phase 2 background work)

The KH team needs to add native canonical object endpoints to the `client-api` generated client:

```
POST   /api/v1/canonical/policies            → create_canonical_policy
GET    /api/v1/canonical/policies/{id}       → read_canonical_policy
GET    /api/v1/canonical/policies            → list_canonical_policies (OData filter)
PUT    /api/v1/canonical/policies/{id}       → update_canonical_policy
DELETE /api/v1/canonical/policies/{id}       → delete_canonical_policy
```

When this is available, `policy_store.py`'s `put_policy` / `get_policy` / `list_policies`
methods switch their backing implementation from entity queries to direct API calls.
**No changes in JACI or any other consumer** — the facade absorbs the backend change.

Pass them the `Policy` Pydantic model from `jazzx_runtime_sdk/canonical_objects/models.py`
as the schema definition. They can generate the OpenAPI spec from it.

---

## 7. Implementation Sequence

### Step 1 — japes: add `canonical_objects/` module

Files to create:
- `jazzx_runtime_sdk/canonical_objects/__init__.py`
- `jazzx_runtime_sdk/canonical_objects/models.py`
- `jazzx_runtime_sdk/canonical_objects/policy_store.py`

Wire into:
- `jazzx_runtime_sdk/client_layer.py` — add `canonical_objects` property
- `jazzx_runtime_sdk/__init__.py` — export canonical object types

Commit to `dev` branch. No breaking changes to existing exports.

### Step 2 — JACI: add pack policy registry

Files to create:
- `src/jaci/pack/__init__.py`
- `src/jaci/pack/policy_registry.py` (content above)

Wire into:
- `src/jaci/japes_handler.py` — preload AML_POLICIES at startup

### Step 3 — JACI: migrate consumers off `policy_clause.py`

- `src/jaci/modes/governor.py` — switch to `ctx.runtime.canonical_objects.get_policy()`
- `tests/fixtures/case_fixtures.py` — replace inline `POLICY_CLAUSES` dict with import from `src/jaci/pack/policy_registry.RULE_INDEX`
- `src/jaci/tools/mock_connectors.py` — update policy_clause lookup to use RULE_INDEX

### Step 4 — JACI: remove deprecated schemas

Once all references are migrated:
- Delete `src/jaci/schemas/policy_clause.py`
- Remove PolicyClause/PolicyLayer from `src/jaci/schemas/__init__.py`

### Step 5 (MACER, parallel) — same pattern

MACER gets `src/macer/pack/policy_registry.py` with Fannie/Freddie Policy objects.
MACER's `JTBDSet` maps to `DomainPack` derived object (separate work).

---

## 8. Testing Strategy

### Unit tests in japes (new)

```
tests/test_canonical_objects/
├── test_models.py           — Policy/Rule Pydantic validation
└── test_policy_store.py     — PolicyStore with mock KH client
```

Key cases:
- `preload()` populates cache; `get_policy()` returns cached value without KH call
- `get_policy()` on cache miss hits KH entity query
- `put_policy()` creates entity with correct entity_type and json_value

### Unit tests in JACI (migrate existing)

`tests/unit/test_policy_clause.py` (currently tests PolicyClause) →  
`tests/unit/test_pack_policies.py` (tests the three Policy objects)

Key cases:
- All three BSA policies load correctly
- `RULE_INDEX` covers all rule IDs used in evaluation gold cases
- `BSA-SAR-DEADLINE-30DAY` rule has `condition.value == 30`
- `BSA-CTR-001` rule has `condition.value == 10000`
- No `AML_POLICIES` entry has `status == DEPRECATED`

---

## 9. Open Questions / Decisions Needed

| # | Question | Options | Recommended |
|---|----------|---------|-------------|
| 1 | KH entity vs native endpoint for Phase 1 | Entity (now) vs wait for native | Entity now; migrate later |
| 2 | Ontology ID for canonical_policy entities | Separate `canonical-objects` ontology vs reuse existing | New ontology, KH team creates |
| 3 | `preload()` vs always-KH in prod | Preload at startup (fast, stale risk) vs live KH reads | Preload + TTL-based refresh |
| 4 | Policy versioning in KH | One entity per policy_id (overwrite) vs append-only with version in name | Append-only: `BSA_SAR_POLICY:1.0.0` |
| 5 | MACER timing | In parallel with JACI or after JACI is stable | After JACI Step 3 complete |

---

*See also:*  
- `docs/CANONICAL_POLICY_SCHEMA_REFERENCE.md` — canonical schema field reference  
- `docs/POLICY_OBJECT_WIRING.md` — original PolicyClause migration (superseded)  
- JazzX Schema Spec v1.0 Section 2 (Policy), Section 7.8 (DomainPack)
