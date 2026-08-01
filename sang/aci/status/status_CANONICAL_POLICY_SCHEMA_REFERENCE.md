# Canonical Policy Schema Reference

**Source:** JazzX Canonical Object & Derived Object Schema Specification v1.0, Section 2  
**Purpose:** Authoritative schema context for JACI policy object refactoring and MACER integration alignment  
**Status:** Read-only reference — do not extend or reinterpret fields here; use `domain_extensions` in code

---

## 1. Policy Object (Canonical, Section 2)

A versioned, executable specification of rules, constraints, authority matrices, and escalation logic that bounds runtime behavior.

### 1.1 Top-Level Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `policy_id` | string | Required | Unique identifier. Format: `policy_{uuid}` |
| `version` | string | Required | Semantic version. Format: `major.minor.patch` |
| `name` | string | Required | Human-readable name (e.g., `'BSA/AML SAR Filing Requirements'`) |
| `description` | string | Required | Concise description of what this policy governs |
| `policy_type` | enum | Required | One of: `regulatory`, `institutional`, `operational`, `model_governance`, `escalation`, `authority_delegation`, `consent`, `commitment` |
| `jurisdiction` | string | Optional | Jurisdiction code (e.g., `'US'`, `'UK'`, `'EU'`) |
| `effective_date` | datetime | Required | When this policy version becomes active |
| `expiry_date` | datetime | Optional | When this policy version expires. Null = no expiry |
| `status` | enum | Required | One of: `draft`, `active`, `deprecated`, `archived` |
| `rules` | array[Rule] | Required | Ordered list of executable rules. See Rule sub-schema |
| `authority_matrix` | AuthMatrix | Conditional | Required when `policy_type = authority_delegation` |
| `consent_registry` | ConsentReg | Conditional | Required when `policy_type = consent` |
| `commitment_tracker` | CommitTrack | Conditional | Required when `policy_type = commitment` |
| `exception_rules` | array[Rule] | Optional | Rules defining valid exceptions including required justification and approval authority |
| `escalation_paths` | array[EscPath] | Required | Ordered escalation paths when policy cannot resolve at current authority level |
| `supersedes` | string | Optional | `policy_id` of prior version this replaces. Cross-object linkage |
| `source_refs` | array[SourceRef] | Required | References to external regulations, standards, or institutional documents this policy encodes |
| `pack_id` | string | Required | Stable identifier of the Domain Pack that owns this policy (semantic slug, not runtime UUID) |
| `overlay_id` | string | Optional | Client-specific overlay identifier, if this policy is an institutional override |
| `domain_extensions` | object | Optional | Domain-specific extension fields. Must not override canonical fields |
| `created_at` | datetime | Required | Timestamp of creation |
| `updated_at` | datetime | Required | Timestamp of last update |
| `created_by` | string | Required | Identity of creator (human or system) |

### 1.2 Rule Sub-Schema

Individual clause within a Policy. This is the canonical equivalent of JACI's `PolicyClause` and MACER's JTBD-style rule.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rule_id` | string | Required | Unique identifier within this policy |
| `condition` | Expression | Required | Evaluable condition expression (boolean logic over context variables) |
| `action` | enum | Required | One of: `allow`, `deny`, `escalate`, `require_approval`, `require_evidence`, `notify`, `log` |
| `parameters` | object | Optional | Action-specific parameters (e.g., `approval_authority`, `notification_target`) |
| `priority` | integer | Required | Evaluation priority. Lower numbers evaluate first. Ties resolved by `rule_id` order |
| `description` | string | Required | Human-readable explanation of what this rule enforces and why |
| `citations` | array[string] | Required | References to `source_refs` entries that this rule implements |

**Note on `condition: Expression`:** The schema specifies `Expression` as the type for boolean logic over context variables. The current JACI `machine_readable_threshold: dict[str, Any]` is a domain-specific encoding of this concept. Refactoring should map `machine_readable_threshold` into `condition` (for the evaluable predicate) and `parameters` (for action-specific metadata like `fail_action`, `escalation_reason`).

### 1.3 Authority Matrix Sub-Schema

Required when `policy_type = authority_delegation`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | Required | Role identifier (e.g., `'l2_investigator'`, `'bsa_officer'`) |
| `action_scope` | array[string] | Required | Actions this role is authorized to perform (e.g., `'approve_sar'`, `'close_case'`) |
| `ceiling` | object | Required | Thresholds beyond which this role must escalate (e.g., `{ 'amount': 100000, 'risk_tier': 'high' }`) |
| `escalation_target` | string | Required | Role that receives escalations from this role |
| `delegation_chain` | array[string] | Optional | Ordered list of alternate roles when primary is unavailable |

### 1.4 Policy Versioning Rules

- Increment **MAJOR** when rule conditions, actions, authority entries, or escalation semantics change
- Increment **MINOR** for additive, backward-compatible policy content
- Increment **PATCH** for clerical fixes or metadata-only corrections that do not alter runtime behavior

---

## 2. DomainPack Derived Object (Section 7.8)

The versioned collection container. MACER's `JTBDSet` maps here — not to a new `RequirementSet` object.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain_pack_object_id` | string | Required | Unique identifier. Format: `packobj_{uuid}` |
| `pack_id` | string | Required | Stable identifier of this Domain Pack (semantic slug or governed semantic ID) |
| `version` | string | Required | Semantic version of this Domain Pack instance |
| `domain_name` | string | Required | Primary domain or subdomain served by the pack |
| `thin_slices` | array[string] | Required | Bounded workflow slices in scope |
| `personas` | array[string] | Required | Primary and secondary personas supported |
| `decision_classes` | array[string] | Required | Decision classes formalized by the pack |
| `primary_artifacts` | array[string] | Required | Artifact families formalized by the pack |
| `pack_supported_range` | object | Required | `{ min: integer, max: integer }` autonomy range |
| `ontology_refs` | array[string] | Required | References to ontology, entity, state-machine, and event-taxonomy assets |
| `policy_family_refs` | array[string] | Required | Policy families formalized by the pack |
| `evidence_type_refs` | array[string] | Required | Admissible evidence classes and source families |
| `playbook_refs` | array[string] | Optional | Playbooks, rubrics, templates, and governed guidance assets |
| `evaluation_asset_refs` | array[string] | Required | Evaluation and certification assets |
| `pattern_pack_refs` | array[string] | Optional | Pattern packs or reusable accelerators |
| `certification_status` | enum | Required | One of: `draft`, `certified`, `suspended`, `retired` |
| `change_log_ref` | string | Optional | Reference to governed release notes or change log |
| `created_at` | datetime | Required | Timestamp |
| `updated_at` | datetime | Required | Timestamp |

**Interpretation note:** Domain Pack is a derived object — a versioned, governed product artifact composed from canonical semantics, guidance assets, policy families, evidence rules, evaluation assets, and workflow boundaries. It is produced and governed outside a single runtime workflow.

---

## 3. Overlay Pattern

The canonical overlay pattern is the mechanism for institutional/investor-specific variants. It does **not** require a new `InvestorRequirement` model.

**How it works:**
- The regulatory floor is encoded as a `Policy` object with `policy_type: regulatory`
- Institutional/investor-specific variants are separate `Policy` objects with `policy_type: institutional` and `overlay_id` set
- The Certified Client Overlay (CCO) narrows values, thresholds, or permitted families — it does not fork the schema
- `overlay_id` on a `Policy` object is the linkage to the client overlay that governs it

**For MACER investor variants:**
- FNMA-specific DTI rule → `Policy` with `policy_type: institutional`, `overlay_id: fnma-overlay`, `rules[0].condition: { dti <= 50 }`
- FHLMC-specific DTI rule → separate `Policy` with `overlay_id: fhlmc-overlay`, `rules[0].condition: { dti <= 45 }`
- Do NOT create a new `InvestorRequirement` Pydantic model; use overlay-scoped `Policy` objects

**What overlays may narrow:** thresholds, role mappings, jurisdiction filters, autonomy ceilings, templates, risk appetite  
**What overlays may not change:** canonical schema structure, required field semantics, cross-object linkage invariants

---

## 4. Refactoring Guidance for JACI `policy_clause.py`

### Q1: Should `PolicyClause` be renamed to `Rule` and become a sub-schema of a parent `Policy`?

**Yes.** The canonical `PolicyClause` is the `Rule` sub-schema. `PolicyClause` as a standalone top-level Pydantic model is a pre-framework design artifact. Refactoring path:

1. Rename `PolicyClause` → `Rule` (or keep as a domain alias that validates against the canonical `Rule` sub-schema)
2. Introduce a `Policy` Pydantic model as the container
3. Move `policy_registry.py` from `clause_id → PolicyClause` to `policy_id → Policy`, with `Policy.rules[]` containing the individual clauses

### Q2: Should `machine_readable_threshold` be refactored to `condition: Expression`?

**Yes, partially.** The mapping is:
- `machine_readable_threshold` (the predicate, e.g., `{ field: 'amount', operator: '>', value: 10000 }`) → `Rule.condition`
- `fail_action`, `escalation_reason`, etc. → `Rule.parameters`

The `Expression` type is not explicitly typed in the canonical schema (it's described as "boolean logic over context variables") — the domain can define a concrete `Expression` sub-schema in `domain_extensions` that encodes the field/operator/value pattern.

### Q3: Should the 14 `PolicyClause` objects become Option A (grouped) or Option B (separate)?

**Option A is correct:** Group by regulatory regime into `Policy` containers.

Suggested groupings for the existing 14 clauses:
- `BSA_CTR_POLICY` — all CTR-related rules (BSA-CTR-001, etc.)
- `BSA_SAR_POLICY` — SAR trigger, deadline, and filing rules
- `BSA_CDD_POLICY` — CDD/KYC/EDD/beneficial ownership rules
- `BSA_MONITORING_POLICY` — structuring detection, ongoing monitoring rules

This matches how regulators issue guidance — by regulatory topic, not one rule per document.

### Q4: Should `POLICY_REGISTRY` become hierarchical?

**Yes.** New structure:

```python
# Registry of Policy objects (top-level)
POLICY_REGISTRY: dict[str, Policy] = {
    "BSA_SAR_POLICY": Policy(..., rules=[...]),
    "BSA_CTR_POLICY": Policy(..., rules=[...]),
}

# Convenience index for clause-level access (derived, not primary)
RULE_INDEX: dict[str, tuple[str, Rule]] = {
    "BSA-CTR-001": ("BSA_CTR_POLICY", rule_object),
    ...
}
```

### Q5: Three-layer model mapping

- `REGULATORY_FLOOR` → `policy_type: regulatory` (no `overlay_id`)
- `VENDOR_INTERPRETATION` → lives in Domain Pack prompts, playbooks, and rubrics — **not** as `Policy` objects. Pack-authored heuristics are guidance assets, not executable policy.
- `INSTITUTION_POLICY` → `policy_type: institutional` with `overlay_id` set, governed by Certified Client Overlay

The `PolicyLayer` enum in current JACI code can be retained as a `domain_extensions` field for query convenience, but it should not replace the canonical `policy_type` enum.

---

## 5. Cross-Object Linkage Invariants (Section 8)

These are non-bypass. Any `Policy` refactoring must preserve these at runtime:

| From | To | Via Field | Requirement |
|------|----|-----------|-------------|
| Decision | Policy | `decision.policy_refs[]` | Every Decision must reference governing Policies |
| Decision | Evidence | `decision.evidence_refs[]` | Every Decision must reference supporting Evidence |
| Decision | Trace | `decision.trace_id` | Every Decision must reference the Trace that produced it |
| Trace | Policy | `trace.policies_applied[]` | Every Trace must reference Policies it applied |
| Artifact | Evidence/Policy | `artifact.citations[].object_ref` | Every Artifact claim must cite an Evidence or Policy object |

---

## 6. MACER Integration Mapping

| MACER Concept | Canonical Mapping | Notes |
|---------------|-------------------|-------|
| `PolicyReference` (doc_id, link, policy_ref) | `Policy.source_refs[]` (SourceRef) | MACER's link fields map to SourceRef structure |
| `JTBD` (verification task) | `Rule` with `action: require_evidence` | JTBD is an operational verification task, not a standalone policy object |
| `InvestorRequirement` (FNMA/FHLMC/FHA variant) | Overlay-scoped `Policy` per investor with `overlay_id` | Do not create a new Pydantic model |
| `JTBDSet` (versioned collection) | `DomainPack` derived object | `JTBDSet` maps to `DomainPack.policy_family_refs[]` + `DomainPack.version` |
| `PolicyLayer.REGULATORY_FLOOR` | `policy_type: regulatory` | Direct mapping |
| `PolicyLayer.INSTITUTION_POLICY` | `policy_type: institutional` + `overlay_id` | Overlay-governed |
| `PolicyLayer.VENDOR_INTERPRETATION` | Domain Pack guidance assets (playbooks, rubrics) | Not a Policy object |

---

*Generated: 2026-04-29 | Source: JazzX Canonical Object & Derived Object Schema Specification v1.0*  
*Do not modify this file to add domain-specific content — use `domain_extensions` in code and link back here.*
