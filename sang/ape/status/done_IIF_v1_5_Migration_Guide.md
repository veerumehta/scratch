# IIF v1.0 to v1.5 Migration Guide
## Architecture and Engineering Reference

**Author:** Virendra Mehta  
**Status:** Living document - updated as v1.5 corpus is ingested  
**Last updated:** June 2026  
**Source corpus:** IIF v1.5 (43 documents - Manifest + 42 corpus docs)

---

## How to use this document

This guide is the engineering-facing translation of the IIF v1.0-to-v1.5 delta. It is updated incrementally as each v1.5 document is ingested and reviewed. Read it top to bottom for a full orientation, or jump to the section relevant to the work in front of you.

Documents ingested so far: Manifest, Charter (01), ADM (04), Domain Pack Strategy (02), Canonical Object Schema Spec (05), SEO (06), IPDV (07), MIS (09).  
Remaining: 35 corpus documents.

---

## 1. Release Character

v1.5 is a **completion-and-hardening release**, not an architectural revision. The thesis, the 13 modes, the 5 categories, the 9 design principles, and the canonical chain are all preserved from v1.0. What changed is the operating system around them.

**Scale of the release:**
- 43 total reader-facing files (Manifest + 42 corpus docs)
- 16 refreshed from v1.0
- 26 brand new in v1.5

**ADM D1 is the root citation** for the completion-and-hardening posture. Every document in the corpus cites it.

---

## 2. Terminology Changes (v1.0 -> v1.5)

These are renames or formalizations. Existing code and docs using v1.0 terms should be updated.

| v1.0 term | v1.5 term | Notes |
|-----------|-----------|-------|
| ABA (Assistant Binding Annex) | SBA (Surface Binding Annex) | Scope broadened from Assistant-only to all four surface types |
| JAP (JazzX Assistance Profile) | EP (Execution Profile) | Renamed; same concept - live deployed posture at the leaf of the narrowing tree |
| Overlay | Overlay (Certified Client Overlay) | Unchanged name; "Certified" now part of formal title |
| (no prior term) | CPEC (Cross-Pack Engagement Contract) | New formalized name for cross-Pack composition contracts, hosted at the SBA |
| (no prior term) | ECAP | Evaluation, Certification and Autonomy Promotion Framework - new in v1.5 |
| (no prior term) | ADM | Architecture Decision Memo - new in v1.5; the architectural decision register |
| (no prior term) | GOM | Governance Operating Model - new in v1.5 |
| (no prior term) | GKAF | Governed Knowledge Asset Framework - new in v1.5 |
| (no prior term) | TSPS | Trust, Safety, Privacy and Security Framework - new in v1.5 |
| (no prior term) | MIS | Minimum Interoperability Specification - new in v1.5 |
| (no prior term) | OTCC | Observability, Telemetry and Cost Attribution Contract - new in v1.5 |
| (no prior term) | IPDV | Identity, Permissions and Data Visibility Specification - new in v1.5 |
| (no prior term) | IEF | Institutional Experience Framework - new in v1.5 |
| (no prior term) | SEO | Shared Entity Ontology - new in v1.5 |
| (no prior term) | MSC | Multi-Surface Composition and Engagement Pattern Spec - new in v1.5 |

---

## 3. Narrowing Tree

The narrowing tree is now fully formalized. The structure is unchanged from v1.0 intent but terminology is locked and every layer has a formal spec owner.

```
Charter + Schema  (anchors - sit above the tree; not a narrowing layer)
    |
Domain Pack       (Pack owner - domain semantics, Authority Matrices, Registries)
    |
SBA               (Pack owner per surface - per-surface permission ceiling, CPEC host)
    |
Certified Client Overlay  (institution - jurisdiction, roles, thresholds)
    |
Execution Profile (deployment owner - live deployed posture, earned autonomy)
    |
Runbooks / operational aids  (operationalize an EP; cannot widen it; not a governance artifact)
```

**The invariant (non-negotiable, ADM D2-D5):** Every downstream layer may narrow, never widen, the layer above it. No Runbook may widen an EP.

**No Composition Layer exists.** Five candidate constructs were considered and rejected by the ADM: Composition Layer, Composition Binding Annex, Composition Execution Profile, Composition Overlay, and recursive cross-Pack composition. Cross-Pack work stays inside the existing stack via CPECs (ADM D2-D5, D10).

**Effective Autonomy Record formula (new in v1.5):**
```
runtime_effective_level
  <= deployment_actual_posture (EP)
  <= overlay_configured_posture (Overlay)
  <= annex_ceiling (SBA)
  <= pack_supported_range.max (Pack)
```

Runtime downgrades (evidence floor failure, policy conflict, IPDV restriction, data-quality failure, Sentinel signal, stale asset, expired consent, connector degradation, evaluation regression) may further narrow `runtime_effective_level` below every configured ceiling.

---

## 4. The ADM Decision Register (D1-D63)

The ADM is the single authoritative source for architectural decisions. When any document appears to conflict with another on architecture, the ADM controls. D-numbers are stable, never reused, and cited across the corpus.

**Key decisions every engineer should know:**

| D# | What it locks | Engineering implication |
|----|---------------|------------------------|
| D1 | v1.5 is completion and hardening, not new architecture | No new canonical objects, no new composition layers, no new derived objects |
| D2-D5 | No Composition Layer / CBA / CEP / Composition Overlay | Cross-Pack work lives in SBA-hosted CPECs only |
| D6, D25 | Schema v1.5 has no substantive field changes | v1.0 Pack authors need no schema-layer migration |
| D7, D15 | Shared Entity Ontology is platform-owned | Packs bind to SEO via EntityRef discipline; no Pack-owned top-level entity redefinition |
| D8 | Skills implement action classes; never grant authority | A Skill cannot widen authority, visibility, or evidence obligations |
| D9 | Solution Blueprint is non-governance packaging | Blueprints enumerate Packs; they don't grant authority |
| D10 | No cross-Pack composition recursion | A composed surface cannot itself participate in another CPEC as if it were a Pack |
| D12 | Four atomic surface types; presentation topology has zero governance significance | Dashboard is not a surface type; UI placement is not governance |
| D16 | Cross-Pack ownership is explicit | anchor_pack_id and cross_pack_owner must be recorded in every CPEC |
| D18 | Financial-crime reference examples are illustrative only | Not product specs, not implementation commitments |
| D29 | IPDV is standalone | Identity, permissions, visibility are owned by the IPDV spec, not embedded in Pack policy |
| D30 | Framework Architect is sole authority for D-number changes | Only the Framework Architect may add, supersede, or retire decisions |
| D48 | C0-C6 connector risk-tier scale | Risk tier is side-effect blast radius, orthogonal to the autonomy ladder |
| D50 | AggregationAuthorizationRecord is a runtime precondition | Required before cross-tenant/cross-Pack aggregation outside the originating visibility envelope |
| D63 | Evaluation Asset Registry is universal | Every certifiable Pack requires this regardless of which modes are activated |

**D-number themes at a glance:**

| Theme | Decisions |
|-------|-----------|
| Architectural posture and composition | D1-D5, D10, D16 |
| Object model, Schema, ontology | D6, D7, D15, D25 |
| Skills, connectors, implementation boundaries | D8, D14, D17, D47-D49 |
| Surfaces, Packs, navigation, reference examples | D9, D12, D13, D18, D19 |
| Corpus governance, citation, lifecycle | D20-D24, D26, D28, D30-D33 |
| Identity, visibility, aggregation | D29, D50 |
| Mode-contract posture | D11, D27 |
| Per-mode governed knowledge, authority, taxonomy | D34-D46, D51-D63 |

**Declined constructs (must not be reintroduced):** Composition Layer, Composition Binding Annex, Composition EP, Composition Overlay, Governance Record as a ninth derived object, Verification Bundle as a derived object, Workflow Instance as a derived object, Governor-specific Registry or Authority Matrix, Curator-specific Registry or Authority Matrix, Evaluator Authority Matrix.

---

## 5. Mode Governance Spine (new in v1.5)

Every authority-bearing cognitive mode now has a formal governance pattern: per-Pack Registry + per-Pack Authority Matrix + (where applicable) ADM-elevated class taxonomy. This is the biggest structural addition in v1.5 for Pack builders.

| Mode | Registry (D#) | Authority Matrix (D#) | Class taxonomy |
|------|--------------|----------------------|----------------|
| Reasoner | Decision Logic Registry (D51) | Decision Authority Matrix (D52) | - |
| Investigator | Investigation Playbook Registry (D53) | Investigation Decision Authority Matrix (D54) | Exception taxonomy, 9 classes (D55) |
| Simulator | Confidence Model Registry (D37) | Scenario Decision Authority Matrix (D38) | - |
| Governor | - (universal enforcer) | - (consumes all matrices) | - |
| Verifier | Verification Asset Registry (D57) | Evidence Admissibility Authority Matrix (D58, cross-mode) | Verdict taxonomy, 4 classes (D56): PASS/FAIL/INDETERMINATE/PARTIAL |
| Sentinel | Detector Registry (D35) | Response Authority Matrix (D36) | Signal taxonomy, 15 classes (D34) |
| Conductor | Workflow Asset Registry (D59) | Workflow Execution Authority Matrix (D60) | - |
| Optimizer | Allocation Policy Registry (D39) | Allocation Decision Authority Matrix (D40) | Constraint taxonomy, 8 classes (D41) |
| Narrator | Communication Asset Registry (D61) | Artifact Release Authority Matrix (D62) | - |
| Influencer | Engagement Playbook Registry (D42) | Engagement Decision Authority Matrix (D43) | - |
| Negotiator | Negotiation Strategy Registry (D44) | Negotiation Decision Authority Matrix (D45) | Concession taxonomy, 8 classes (D46) |
| Curator | - (universal steward) | - | - |
| Evaluator | Evaluation Asset Registry (D63) - UNIVERSAL | - | - |

**Three modes are deliberately outside the Registry-and-Matrix pattern:**
- Governor enforces Policy and existing matrices; a Governor-specific Registry would duplicate Policy or shift authority into a Pack-versioned artifact
- Curator stewards the governed knowledge asset system; it doesn't need a meta-Registry
- Evaluator computes and attests gate evidence; final release/promotion authority stays with Policy, Governor, certification forums, and accountable humans

**D63 is universal:** Every certifiable Pack requires the Evaluation Asset Registry regardless of which cognitive modes are activated.

**Count summary:** 12 Tier-1 Registries, 10 ADM-elevated Authority Matrices (mode-specific or cross-mode), plus one general Pack Authority Matrix for primary decision classes = up to 11 total Authority Matrix obligations per certifiable Pack.

---

## 6. New Concepts in v1.5

### 6.1 Non-Bypass Rules (Charter §5 / ADM §7)

Nine enforceable rules that close common enterprise AI drift paths.

| Rule | What it forbids | Engineering implication |
|------|-----------------|------------------------|
| 5.1 Skills implement; never grant authority | Treating Skill availability as permission | Authority comes from Pack, SBA, Overlay, EP, Governor, IPDV, ECAP |
| 5.2 Connectors provide access; never grant authority | Connector access as transitive permission | C0-C6 risk tier is side-effect blast radius, not autonomy level |
| 5.3 Governed knowledge assets influence behavior; never authority | Registry-listed assets as runtime authority | Assets shape behavior only inside the active authority envelope |
| 5.4 Identity narrows; never widens | Using identity-derived rights to expand Pack authority | Identity cannot lower evidence floors, bypass accountability, or override TSPS |
| 5.5 Telemetry measures; never controls | Dashboards or alerts as action surfaces | Observability informs; it does not authorize |
| 5.6 Presentation topology has zero governance significance | UI placement as governance | Dashboard is not a surface type (ADM D12) |
| 5.7 Cross-Pack composition uses the existing stack | Introducing a Composition Layer | Cross-Pack work flows through SBA-hosted CPECs; no recursion |
| 5.8 Operational views are not schema objects | Promoting operational records to canonical/derived objects | Verification Bundles, Workflow Instances, Curator packets are not schema objects |
| 5.9 Governance records are not schema objects | Promoting governance records to canonical/derived objects | AccessReviewRecords, AggregationAuthorizationRecords are not canonical objects |

### 6.2 Cross-Pack Engagement Contracts (CPEC)

Cross-Pack behavior requires explicit contracts hosted at SBAs (ADM D3). Every CPEC declares:
- `engagement_pattern` (governed_relay / orchestration with subtype / peer_collaboration)
- `authority_boundary` - which Pack may originate, approve, modify, or execute which action classes
- `effective_rights_rule` - INTERSECTION ONLY; rights cannot be composed by union
- `writer_of_record` per canonical object family
- `trace_correlation_rule` with `cross_pack_correlation_id`
- `shared_entity_scope` (SEO classes crossing boundaries)
- AAR linkage where cross-tenant/portfolio aggregation is involved (D50)
- `d10_non_recursion_attestation`
- `anchor_pack_id` and `cross_pack_owner` (named accountable human with succession protocol) per D16

Composition recursion is prohibited (D10). A composed surface MUST NOT participate in a further cross-Pack engagement as if it were a Pack.

### 6.3 Three Engagement Patterns

| Pattern | Used when | Core rule |
|---------|-----------|-----------|
| Governed Relay | Work moves from one surface to another with authority transfer | Handoff packet, trace continuity, acceptance, writer-of-record discipline |
| Orchestration | One surface invokes or coordinates another (3 subtypes: Service Invocation, Embedded/Co-Present, Delegated Execution) | Classify outputs, preserve trace ownership, avoid hidden side effects |
| Peer Collaboration | Multiple surfaces or Packs contribute to a shared judgment or artifact | Contribution is not approval; final responsible actor and writer-of-record remain explicit; malformed without named final responsible actor |

### 6.4 ECAP Gate Families (new in v1.5)

| Gate | Question | Failure outcome |
|------|----------|-----------------|
| Conformance | Does the artifact satisfy MIS floor and ECAP coverage requirements? | Not certifiable |
| Launch | Is this configuration ready to operate in this environment? | Cannot go live |
| Promotion | Has this configuration earned higher autonomy on this cell? | Stay at current effective level |
| Recertification | Has a material change invalidated prior evidence? | Step-down or rollback |

Promotion is cell-level (Authority Matrix cell), not Pack-wide. A Pack may be certified while specific cells remain at lower autonomy. Certification is not autonomy.

### 6.5 Eleven Standing Governance Functions (new in v1.5)

| # | Function | Steward |
|---|----------|---------|
| 1 | Architectural Review | Framework Architect (chair) |
| 2 | Cross-Cutting Standards | Cross-cutting spec stewards |
| 3 | Pack Certification | Pack certification chair |
| 4 | Surface Binding Review | SBA review chair |
| 5 | Client Overlay Certification | Overlay certification chair |
| 6 | Deployment Readiness | Deployment readiness chair |
| 7 | Evaluation and Autonomy Promotion | ECAP framework lead |
| 8 | Trust, Safety, Privacy and Security Review | TSPS Steward |
| 9 | Governed Asset Review | Lead Curator |
| 10 | Incident and Remediation | Incident Commander |
| 11 | Audit and Regulator Liaison | Compliance officer |

### 6.6 Domain Pack - Seven Real-Pack Tests (formalized in v1.5)

A Pack is only real if it passes all seven:

| Test | Question |
|------|----------|
| 1 - Canonical-Chain | Can the primary workflow emit Policy → Evidence → Decision → Trace → Outcome with durable linkage? |
| 2 - Knowledge-Location | Does domain knowledge live in versioned Pack assets, not in prompts, agent instructions, or code? |
| 3 - Governed-Autonomy | Is autonomy bounded by published Authority Matrix, evidence floors, named human-only action classes, and ECAP-gated promotion? |
| 4 - Narrowing-Chain | Can Pack capabilities be safely narrowed by SBA, Overlay, EP without forking Pack semantics? |
| 5 - Surface-Discipline | Is every capability bound to exactly one of the four atomic surface types through an SBA? |
| 6 - Evaluation | Can the Pack be evaluated before launch and monitored after launch using the D63 Evaluation Asset Registry? |
| 7 - Replayability | Can a material runtime action be reconstructed after the fact from canonical objects, Trace, version pins, and governed-asset references? |

### 6.7 Pack Lifecycle Stages (formalized in v1.5)

Ideation → Incubating → MVDP → Pilot → Certified → Scaled → Sustaining → Suspended / Retired

MVDP = Minimum Viable Domain Pack: the smallest Pack slice that emits the canonical chain end-to-end, can be safely narrowed to one surface and institution, can be evaluated and monitored, and produces signals that update reusable Pack assets. Target: 60-90 days internally, 90-120 days with partners.

### 6.8 Thirteen-Factor Moat Formula (v1.5 expansion from 6 factors in v1.0)

MOAT = Ontology Depth × SEO/IPDV Coherence × Policy Richness × Authority Precision × Evidence Discipline × Registry & Asset Maturity × Skill Coverage × Connector Family Maturity × Mode Tuning × Evaluation Maturity × Versioned Replayability × Outcome Linkage × Speed to Deploy

Note: Policy Richness and Authority Precision are kept separate by design - a Pack can have rich policy content with thin Authority Matrix enforcement, or vice versa. Both failure modes appear in the field.

### 6.9 Anti-Pattern Catalog (v1.5 expansion - 20 named patterns)

The Domain Pack Strategy documents 20 anti-patterns. The ones most directly relevant to current JazzX work:

| Anti-pattern | Why it matters to us |
|--------------|----------------------|
| Prompt-pack masquerading as Domain Pack | Our shift to Policy objects, Authority Matrices, Registries addresses this |
| Pack-wide promotion | Cell-level eval harness in JACI-AML is correct. Don't promote on aggregate |
| Skill-as-authority | Skills implement; authority comes from the narrowing chain and IPDV |
| Policy in prompts | Policy changes must land in governed assets and versioned releases |
| Outcome orphaning | Decisions not linked to Outcomes = no compounding; design at Pack level |
| Silent registry mutation / Silent behavior change | Version-pin contract on every Trace; compatibility ledger required |
| Client fork disguised as Overlay | Overlays narrow; they don't fork or widen |
| Pack-namespaced SEO entity redefinition | Top-level SEO classes are platform-owned; Pack binds, not redefines |
| Composition recursion attempt | D10 non-recursion attestation is a certification gate |
| AAR-less aggregation | Valid in-scope AggregationAuthorizationRecord is a runtime precondition |
| Authority Matrix without policy backing | Authority Matrix cells must trace back to specific Policy objects |
| Silent retirement | Pack retirement is a governed transition with GDR, successor mapping, customer notice |

---

## 7. What Did NOT Change

- The five canonical objects: Policy, Evidence, Decision, Trace, Outcome (frozen, ADM D6/D25)
- The eight derived objects (set is closed at v1.5)
- The 13 cognitive modes and 5 categories
- The nine design principles
- The autonomy ladder levels L0-L4
- The two-sentence thesis (preserved verbatim from v1.0)
- **Schema field-level definitions: no field-level changes from v1.0.** Pack authors who built against v1.0 can cite v1.5 with no schema-layer migration (ADM D6, D25). The v1.5 Schema Spec is a verbatim republish of v1.0 §§1-11; all new content is in Appendix A as interpretation only.
- The three engagement patterns (formalized but not changed from v1.0 concepts)
- The four surface types (formalized but not changed from v1.0 concepts)

---

## 8. Schema Spec - Key Engineering Details (doc 05)

The Schema Spec is a verbatim republish. §§1-11 are unchanged from v1.0. Appendix A is the only addition - it maps v1.5 concepts (Skills, SEO, CPEC, IPDV, surface taxonomy, mode-specific patterns) onto the unchanged type system.

**Compatibility guarantee:** Pack authors building against v1.0 find no schema-layer change that affects them.

**Key sub-schemas engineers should know:**
- `ActorRef` / `ParticipantRef` / `AssignmentRef` - shared actor and participant reference types used across all canonical objects
- `GuidanceRef` sub-schema on Decision - links a Decision to the governed guidance/rule/asset/registry entry that shaped it
- `TraceStep` sub-schema - carries `matrix_cell_ref` for the Authority Matrix cell that authorized the step, plus version-bundle identifier for audit replay. **Does NOT carry metadata or domain_extensions - this is the most common v1.5 implementation failure mode.**
- `OverrideEvent` sub-schema on Trace - captures structured override: actor, authority_basis, reason_code, evidence_delta_refs, state_before/state_after
- `Attestation` and `Freshness` sub-schemas on Evidence

**Cross-Pack Trace correlation:** Each Pack remains writer-of-record for its own canonical objects. `cross_pack_correlation_id` ties Traces across Pack boundaries via Trace.metadata.

**Schema Evolution Protocol** is deferred to a future version (ADM D14).

---

## 9. SEO - Shared Entity Ontology and Object Spine (doc 06)

### Core concept

The SEO is the platform-owned semantic reference layer for business entities. It is NOT an extension of the canonical chain - it is the subject-matter layer that the canonical chain references. The fundamental distinction:

- **Governance objects** (canonical/derived) - what institutional actions exist; closed set; frozen
- **Subject-matter entities** (SEO) - what those actions are *about*; open under platform governance

Conflating these breaks the framework. A Customer is not a canonical object; it is a subject-matter primitive referenced from Evidence, Decision etc. through EntityRef.

### The three spines (must hold simultaneously)

| Spine | Question | Owner |
|-------|----------|-------|
| Canonical Object Spine | What institutional objects exist and how do they link? | Schema Spec |
| Shared Entity Spine | What real-world subjects is this work about? | SEO Spec |
| Authority and Visibility Spine | Who may relate the two - see, correlate, disclose, act? | IPDV Spec |

A Pack with strong object design but weak entity continuity fragments across workflows. Strong entity continuity but weak visibility discipline leaks. Strong visibility but weak canonical linkage doesn't compound. All three must hold simultaneously.

### SEO structure

Three artifact families owned by the platform team:
- **Class Catalog** - top-level entity classes, sensitivity defaults, subtype namespacing rules
- **Entity Reference and Resolution Index** - how entities are identified, resolved, linked across source systems
- **Relationship Reference Catalog** - relationship types, evidence requirements, visibility rules

**Two-tier catalog:**

Tier 1 (framework-anchored, permanent) - five classes frozen across v1.5 corpus. Adding/renaming/redefining requires ADM addendum under D31:

| Class ID | Aliases | Default sensitivity |
|----------|---------|---------------------|
| `seo.customer` | borrower, applicant, member, consumer | high |
| `seo.counterparty` | vendor, broker, merchant, payer | medium-high |
| `seo.account` | bank account, loan account, wallet, policy | high |
| `seo.transaction` | payment, transfer, claim, encounter | high |
| `seo.alert` | fraud alert, AML alert, care gap alert | medium-high |

Tier 2 (initial catalog, platform-governed evolution) - 15 additional classes including `seo.case`, `seo.patient`, `seo.beneficial_owner`, `seo.watchlist_match`, `seo.submission`, `seo.cohort`, etc.

**Important distinction:** `seo.case` is a source-system work item (a matter, loan file, investigation case). It is NOT the Schema-defined Case Context derived object (`ctx_{uuid}`) and NOT the Case File derived object. Three separate things.

### EntityRef reference contract

EntityRef is a reference VIEW (not a schema field) that bundles identity, class, source aliases, resolution status, visibility, tenant scope, purpose of use, and lineage into one coherent reference.

Required minimum fields: `entity_id`, `entity_class_id`, `resolution_status`, `visibility_class`, `tenant_scope`, `purpose_of_use`. Required for material use: `ontology_version`.

**Eight non-bypass invariants (Object Spine Contract):**
1. No Decision without `policy_refs`, `evidence_refs`, and `trace_id`
2. No subject claim without an EntityRef when entity identity is material
3. No EntityRef without `entity_class_id`
4. No silent resolution-status transition
5. No authority granted by entity attribute
6. No visibility granted by entity reference alone
7. No cross-Pack correlation without `ontology_version` pinning and effective-rights intersection
8. No silent merge or split

**Resolution lifecycle states:** unresolved, candidate, resolved, disputed, source_local_only, merged, split, deprecated. Notably ABSENT: masked, not_permitted, suppressed (these belong in IPDV controls, not resolution status).

### Relationship model

15 relationship families: identity, ownership, participation, transactional, evidence, policy, decision, trace, scenario, engagement, negotiation, care, monitoring, spatial, lineage.

**Sensitive-inference rule:** Relationships can disclose sensitive facts even when individual entities are independently visible. A patient-provider relationship at a specialty clinic discloses a health condition. Relationship visibility is NOT the union of endpoint visibility. Three graded-disclosure tiers: existence-only, category-only, full-detail.

### Pack-builder obligations

Every Pack needs a Required SEO Mapping Table classifying each Pack-local concept into one of six categories:
- SEO-mapped, SEO-subtyped, Pack-local, Source-artifact, Governed object, Candidate for platform review

Pack subtype naming convention: `<pack_id>::<subtype-name>` e.g. `symphony-aml::Counterparty-Sanctions-Adjacent`.

### Seven supplemental evaluation indicators

Owned by SEO spec, not Schema-level compounding metrics. ECAP determines elevation:
1. Entity Linkage Rate, 2. Entity Resolution Defect Rate, 3. Cross-Pack Correlation Precision, 4. Trace Entity Completeness, 5. Writer-of-Record Conflict Rate, 6. Visibility Violation Rate, 7. Relationship Evidence Coverage.

### JazzX implications

- **Mortgage ontology:** Borrower → `seo.customer` subtyped as `jazzx-mortgage::Subject-Borrower`. Property → `seo.asset`. Rate lock → `seo.agreement_subject`. Loan file = Source-artifact (reference via Evidence, not EntityRef).
- **AML ontology:** Customer/Counterparty/Account/Transaction/Alert all map directly to the five Tier-1 framework-anchored classes. UBO → `seo.beneficial_owner`. SAR draft → `seo.submission`. Watchlist match → `seo.watchlist_match`.
- **Cross-Pack JACI-AML + JACI-KYC:** When these Packs reference the same Customer, they bind to the same `seo.customer` EntityRef. Cross-Pack correlation requires SEO `ontology_version` pin and explicit CPEC with named SEO classes.
- **KG research:** The Knowledge Graph is the platform's implementation of the SEO Resolution Index and Relationship Reference Catalog. This validates why KnowledgeExpert is not needed as a separate mode - KG capabilities are the SEO substrate layer, not a cognitive mode.

---

## 10. IPDV - Identity, Permissions and Data Visibility (doc 07)

### Core concept

IPDV is the standalone normative reference (per ADM D29) for who is acting, what they may do, and what they may see. Introduces no new canonical fields and does not expand ActorRef.actor_type (fixed at five values per D6/D25).

**Critical four-way distinction (never collapse these):**
- **Authority** - whether an action may have operative effect
- **Permission** - whether an actor or surface may perform an operation
- **Visibility** - which data may be seen, transformed, included, or disclosed
- **Topology** - where on a screen or in an architecture a surface appears (zero governance significance)

### Effective rights formula

```
runtime_effective_rights =
  (structural_intersection ∩ applicable_CPEC_effective_rights_rule ∩ runtime_downgrade_overlay)
  bounded by most_restrictive_visibility_envelope

structural_intersection =
  Pack universe ∩ SBA ceiling ∩ Overlay narrowing ∩ EP actual posture ∩ identity-derived rights
```

**Runtime downgrade overlay** (ten triggers): Governor DENY/ESCALATE, Verifier signal, Sentinel signal, Evaluator signal, data-quality stop, consent expiration, evidence floor failure, identity expiration, tenant boundary check, CPEC violation.

**Most-restrictive envelope** governs all visibility: narrowest bound across tenant, jurisdiction, role, field, purpose-of-use, consent, time, external-recipient class, and CPEC restrictions.

### TraceStep clarification (critical - most common implementation failure)

**TraceStep does NOT carry metadata or domain_extensions.** This is explicitly named as the most consequential v1.5 implementation failure mode in Schema §A.11.2. Adding TraceStep.domain_extensions is a substantive schema change, closed in v1.5 (per D6/D25).

Per-step IPDV records go on: (a) parent Trace.metadata or Trace.domain_extensions with step_id correlation, (b) Case Context.domain_extensions, or (c) standalone IPDV runtime record keyed by trace_id and step_id.

### Principal subclassing (IPDV runtime layer only - NOT canonical schema)

Fine-grained classification in IPDV runtime records only. ActorRef.actor_type remains fixed at five values.

| Principal subclass | Maps to actor_type |
|-------------------|-------------------|
| human_user | human |
| assistant_persona | assistant |
| task_executor | assistant, service, or workflow |
| platform_service | service |
| workflow_instance | workflow |
| connector_principal | service |
| skill_invocation | service or assistant |
| external_partner | human, service, or system |
| system_monitor | system |

### Data visibility states (11-state taxonomy)

raw, field_scoped, masked, redacted, summarized, deidentified, aggregate_only, metadata_only, escrowed, externalized_by_ref, denied.

**Masking vs. Redaction:**
- Masking: field value replaced with token/hash/partial value while preserving record structure. A masked field is STILL THE SAME FIELD - never treat masked as missing.
- Redaction: content removed from artifact, external communication, log export, or support/debug views.

### Data classification registry (13 classes)

public, internal, tenant_confidential, customer_confidential, regulated_personal, regulated_health, regulated_financial, sensitive_attribute, secrets_credentials, system_prompt_hidden_policy, legally_privileged, safety_privacy_security_sensitive, disclosure_sensitive.

**Critical:** `secrets_credentials` (API keys, OAuth tokens, signing certs) are NEVER visible to LLM context, user-facing artifacts, ordinary traces, or memory. Vault references only.

### Permission classes (11 verbs)

read, compute, display, persist, modify, approve, invoke, export_or_disclose, learn_from, support_debug, break_glass.

A runtime may have `compute` rights over a record without having `display`, `persist`, `learn_from`, or `export_or_disclose` rights. These must be evaluated separately at every step.

### Ten runtime record families (not canonical objects)

| # | Record family | Trigger |
|---|---------------|---------|
| 1 | IdentityContextRecord | Every material runtime action, access, disclosure |
| 2 | PermissionEvaluationRecord | Every denied, escalated, downgraded, cross-Pack access |
| 3 | DataVisibilityDecisionRecord | Every field/object/payload visibility transform |
| 4 | ConsentPurposeEvaluationRecord | Every access affected by consent or purpose restriction |
| 5 | CrossPackDisclosureRecord | Every cross-Pack handoff, orchestration payload |
| 6 | ProviderEgressRecord | Every connector/provider call transmitting data |
| 7 | SupportAccessRecord | Every support/debug access touching raw payload |
| 8 | BreakGlassRecord | Every emergency/break-glass access |
| 9 | AggregationAuthorizationRecord | Every cross-tenant or cross-deployment aggregation |
| 10 | LearningUseRecord | Every use of runtime data for memory, evaluation, curation |

### Protected attributes discipline (portfolio-level rule)

Protected and sensitive attributes (race, ethnicity, gender identity, health status, etc.) are **protection-and-routing controls only**. They route steps to additional human review, evidence requirements, and fairness controls. They are NEVER segmentation strategies, targeting strategies, exploitation strategies, or denial-of-access criteria.

### Purpose-of-use classes (12 classes)

identity_verification, evidence_attestation, decision_support, workflow_execution, regulated_communication, engagement_or_outreach, negotiation_or_commitment, monitoring_and_detection, evaluation_and_certification, governed_learning, investigation_or_incident_response, support_debug.

Support/debug is a controlled purpose class - requires ticket link, approver, time limit, post-use review.

### Consent state taxonomy (7 states)

allowed, conditional, missing, revoked, expired, not_required, unknown.

### Cross-Pack identity rule

A receiving Pack does not inherit the originating Pack's identity-derived rights. `cross_pack_correlation_id` is a correlation key, not a permission key. Every actor authorized in Pack A must be re-resolved against Pack B's authority model for Pack B's segment.

### JazzX implications

- **JAPES Agent Execution Layer:** Every tool/Skill invocation inherits caller's effective rights. A Skill under a service identity with broader rights than the calling user = "Skill-mediated authority widening" anti-pattern. Adapters must pass scoped inputs.
- **JACI-AML Expert layer:** AMLGovernanceExpert = Governor runtime. It evaluates effective-rights intersection at every gate, validates authority_basis on every override, enforces human-only decision classes (SAR filing = L0, no bypass).
- **Trace design:** Per-step IPDV context goes on Trace.metadata with step_id correlation or Case Context.domain_extensions. NOT TraceStep - it has no metadata or domain_extensions.
- **JACI-KYC cross-Pack with AML:** Cross-Pack disclosure of KYC data requires explicit CrossPackDisclosureRecord with permitted_visibility_state and purpose_of_use. Beneficial owner data (`seo.beneficial_owner`, default sensitivity high) requires graded-disclosure rules.
- **AnthropicAdapter:** principal_subclass = `task_executor`. Purpose-of-use must be declared per invocation (decision_support, evidence_attestation, etc.).
- **MACER:** LLM prompt context must not receive raw secrets, credentials, or raw PII. Minimum-necessary discipline applies to context assembled per JTBD prompt.

---

## 11. MIS - Minimum Interoperability Specification (doc 09)

### What the MIS is

The MIS is the cross-cutting normative floor extracted from Domain Pack Strategy v1.0 §9.1 into a standalone specification. It defines eight artifact-based conformance classes and aggregates the full v1.5 substrate into a single conformance contract.

**The MIS is a floor, not a substantive owner.** Each section forward-references the sister spec that owns the full standard.

### Eight conformance classes

| Class | Applies to |
|-------|-----------|
| MIS-PACK | Every Domain Pack |
| MIS-SURFACE | Every operational surface |
| MIS-OVERLAY | Every Certified Client Overlay |
| MIS-DEPLOYMENT | Every Execution Profile |
| MIS-ENGAGEMENT | Every SBA including Cross-Pack Engagement Contracts |
| MIS-SKILL | Every Skill invoked by a certified Pack |
| MIS-ENTITY | Every SEO reference used for cross-Pack continuity |
| MIS-PARTNER | Partner-built Packs (same bar as internal, not a relaxed path) |

Typical: Single-surface Pack = MIS-PACK + MIS-SURFACE + MIS-DEPLOYMENT. Cross-Pack solution adds MIS-ENGAGEMENT + MIS-ENTITY.

### Six non-negotiable invariants

| Invariant | Failure consequence |
|-----------|-------------------|
| Canonical-chain | Blocks Pilot, Certified, Scaled |
| Schema-stability | Violations require Schema/ADM review before certification |
| Narrowing-chain | Any widening below Pack/SBA layer blocks certification and may trigger rollback |
| Data-sovereignty | Raw cross-tenant leakage is a trust/security incident and blocks certification |
| Human-accountability | Missing named accountable human blocks promotion and certified production |
| Versioned-behavior | Silent behavior change is a hard certification failure |

### Ambient-control floor (MIS §6.1)

Regardless of declared mode disposition, the following MUST be in force for every consequential execution:
- **Governor** - runtime policy enforcement at every material action point
- **Conductor** - managed workflow and Trace context for every workflow instance
- **Sentinel** - anomaly and drift detection baseline (once Pack enters Pilot maturity; required before Level 2+ promotion)
- **Evaluator** - evaluation-suite execution at launch, every promotion, every recertification

Verifier is mandatory wherever material claims, evidence admissibility, provenance, freshness, verification assets, or regulated artifacts are in scope.

### Version bundle (Trace replay contract)

Every Trace MUST record an execution version bundle. Components stored at TraceStep level: schema_version, policy_bundle_version, model_version/prompt_version, connector_config_version, evaluation_suite_version, overlay_version, skill_id/skill_version/skill_tier (in tools_invoked). Additional components at Trace.metadata level: pack_version, skill_bundle_version, per_Pack Registry versions, cross_pack_engagement_contract. Authority Matrix via Decision.domain_extensions.matrix_cell_ref.

### Mandatory evaluation assets

Gold-case library (required), edge-case library (required), policy regression suite (required), artifact quality rubric (required for regulated artifacts), adversarial test suite, monitoring baseline (required for Level 2+), cross-Pack composition suite (required for MIS-ENGAGEMENT), mode-specific evaluation (required for primary/supporting modes).

### Pack manifest minimums - v1.5 additions (new fields vs. v1.0)

`skill_bundle_version`, `per_pack_registry_versions`, `authority_matrix_versions`, `cross_pack_engagement_contracts`, `shared_entity_ontology_version`, `ipdv_policy_version`.

### Four trace modes (required for certified implementations)

1. Full-fidelity protected - all fields; for audit/compliance/regulator review
2. Redacted - user views where actor lacks field visibility for some content
3. Abstracted - cross-Pack or cross-tenant learning where raw data is prohibited
4. Evidence-preserving - regulatory review; citations must remain inspectable

### v1.0 to v1.5 MIS migration delta

| What changed | Migration action |
|--------------|-----------------|
| Cross-Pack composition (informal) | Must migrate to formal SBA Cross-Pack Engagement Contracts (MIS-ENGAGEMENT) |
| Skills (informal) | Pack Skill manifests required; MIS-SKILL conformance |
| Domain entities as canonical-object-shaped | Must migrate to SEO via EntityRef |
| Identity/visibility (ad-hoc) | Must meet IPDV floor (MIS-ENTITY) |
| Mode-specific patterns (absent) | Per-Pack Registries and Authority Matrices required for activated modes |
| Trace four-mode discipline (absent) | Required for any cross-tenant or regulator-facing deployment |
| Single conformance class | Now eight artifact-based conformance classes |

### JazzX implications

- **JACI-AML current state vs. MIS:** Incubating/Pilot. Canonical chain exists. Missing: formal Outcome objects, version bundle on Trace, Cross-Pack Engagement Contracts. Known gaps to close before Certified status.
- **Every JazzX Pack:** needs v1.5 manifest fields added - `skill_bundle_version`, `per_pack_registry_versions`, `authority_matrix_versions`.
- **JAPES extension handlers:** Need formal Skill manifests per MIS Appendix C: skill_id, skill_version, skill_tier (pack_exported for JACI extensions, platform for JAPES platform Skills), approved_surface_ids, action_classes_implemented, trace_requirements.
- **MACER as Pack:** Must declare all 13 mode dispositions. Governor + Conductor are ambient controls even if Sentinel/Evaluator are not yet primary. The 10 gold cases map to the MIS gold-case library requirement.

---

## 12. Four Atomic Surface Types (formalized in v1.5)

| Surface | Governance character |
|---------|----------------------|
| Assistant | Persona-centered foreground judgment surface serving one bounded human role |
| Workspace | Case-centered persistent collaborative surface managing shared state and multi-persona authority |
| API/Service | Programmatic intelligence service responding to structured requests from other systems |
| Automation | Background execution surface turning governed intelligence into repeated operational action |

"Dashboard" is explicitly NOT a surface type (ADM D12). Presentation topology has zero governance significance. A new surface is created by different governance profile, not different UX.

**Surface split rule:** Material distinctness requires at least one of: persona served, state ownership, decision and action rights, object rights, data access, autonomy ceiling, or evaluation burden.

---

## 13. New Substrate Specifications (all new in v1.5)

| Doc # | Spec | What it owns |
|-------|------|--------------|
| 04 | ADM | Locked architectural decisions; resolves cross-document conflicts; 63 decisions |
| 06 | Shared Entity Ontology and Object Spine Spec | Platform-owned semantic reference layer for business entities; EntityRef contract; three-spine architecture |
| 07 | IPDV | Who acts, what they may do, what they may see; effective-rights intersection; 10 runtime record families; AggregationAuthorizationRecord |
| 08 | Skill Architecture and Governance Spec | Four-tier Skill model (T0-T3); Skill Manifest; registry layers; sandbox profile; lifecycle states |
| 09 | MIS | Cross-cutting minimum floor; eight conformance classes; ambient-control floor definition |
| 10 | Versioning and Dependency Compatibility Spec | Version-pin discipline; lifecycle states; recertification triggers; rollback; audit replay |
| 11 | OTCC | Standard Event Envelope; event families; dashboard families; cost attribution as observability |
| 12 | Integration and Connector Framework | Connector Family Manifest; C0-C6 risk tiers; 20 capability classes; side-effect and idempotency discipline |

---

## 14. New Operating Standards (all new in v1.5)

| Doc # | Standard | What it owns |
|-------|----------|--------------|
| 13 | ECAP | Evaluation, certification, autonomy-promotion mechanics; four gate families; promotion clock; recertification triggers |
| 14 | GKAF | Governed knowledge asset lifecycle; 12 Tier-1 Registry classes; Curator Publication Pipeline |
| 15 | TSPS | Trust, safety, privacy, security; 6-class data classification; Sensitive-Topic Catalog; Dark-Pattern Prohibition Catalog; Trust Gates |
| 16 | GOM | Who decides, in what forum, on what evidence, with what record and rollback path; 11 governance functions; Six-Part Governance Test |
| 17 | MSC | Three engagement patterns; Cross-Pack Engagement Contracts; composition discipline; writer-of-record rules; autonomy-chain inequality |
| 18 | IEF | How governed intelligence becomes usable and inspectable; Three Hard Bright Lines; Trust Surfaces; five-level explainability model |

**Three Hard Bright Lines (IEF):**
1. The UI cannot widen authority
2. The UX cannot bypass visibility redaction
3. Experience telemetry cannot become a runtime control surface

**Six-Part Governance Test (GOM):** Every governable change must have: named accountable owner, named decision class, named approving authority, named evidence package, named record, and named rollback/sunset rule. Absence of any of the six is itself a governance defect.

---

## 15. Implications for Current JazzX Work

*Updated as documents are ingested. See sections 9-11 for SEO, IPDV, and MIS-specific implications.*

### JAPES v2 / Knowledge Fabric

- **Terminology update required:** SBA replaces ABA everywhere; EP replaces JAP everywhere.
- `SurfaceType` enum must reflect the four atomic surface types: Assistant, Workspace, API, Automation. "Dashboard" and "Hybrid" are not surface types.
- The non-bypass rules should be enforced at the platform layer: Skills, connectors, telemetry, and governed assets must not carry authority claims. Governor is the runtime enforcement point.
- Agent Execution Layer: the two-tier API design aligns with non-bypass rule 5.1. Provider-portability implements action classes; it does not grant authority.
- `fabric.docs` store: the governance envelope (typed `doc_type`, `version`, `pack_id`) aligns with the GKAF concept of versioned, owned, publication-controlled knowledge assets.
- `jazzx_sdk/documents/` as source-agnostic ETL pipeline aligns with "processing utilities below governed semantic surfaces."
- The Knowledge Fabric v2 design should reference the three-spine architecture: Canonical Object Spine + Shared Entity Spine + Authority and Visibility Spine.
- TraceStep does NOT carry metadata or domain_extensions. Per-step context goes on Trace.metadata with step_id correlation. Platform SDK must enforce this.

### JACI-AML

- **Cell-level promotion validated** by anti-pattern "Pack-wide promotion." Our eval harness (10 gold cases, 80% disposition accuracy baseline) is the right unit.
- **Policy canonical objects** in `jazzx_runtime_sdk/canonical_objects/` align correctly with "Policy-as-runtime" and ADM D51/D52.
- **AML governance artifacts:** ABA -> SBA; JAP -> EP. Autonomy ceiling logic currently orphaned in code belongs in the SBA's `annex_ceiling` field.
- **CPEC for cross-Pack work:** JACI-AML invoking KYC = CPEC hosted in SBA, with `anchor_pack_id`, `cross_pack_owner`, `d10_non_recursion_attestation`, `shared_entity_scope` (seo.customer, seo.account etc.).
- **Five AML Expert specializations** map to mode activations: AMLInvestigativeExpert → Investigator (D53), AMLGovernanceExpert → Governor, AMLEvidenceExpert → Verifier (D57), AMLPolicyExpert → Reasoner (D51), AMLPlaybookExpert → Conductor (D59).
- **EVOLVE layer:** Evaluator owns D63 universal Evaluation Asset Registry - our eval harness gold cases should migrate there. Curator stewards Publication Pipeline.
- **SAR filing is human-only (L0)** - correct. Governor enforces; no bypass path.
- **Current MIS status:** Incubating/Pilot. Missing: formal Outcome objects, version bundle on Trace, Cross-Pack Engagement Contracts. Known gaps for Certified status.

### JACI-KYC

- Both branches operate correctly as Pack implementations. No structural change required.
- The AnthropicAdapter wrapping pattern aligns with non-bypass rule 5.1: implements action class contract; does not grant authority. principal_subclass = task_executor.
- Cross-Pack disclosure from KYC to AML requires explicit CrossPackDisclosureRecord. Beneficial owner data (high sensitivity) requires graded-disclosure rules per IPDV.
- kyc-anthropic branch decomposing reference content into governed JACI modes aligns with "knowledge lives in governed assets, not prompts."

### MACER / Knowledge Graph

- No schema-layer migration required (ADM D6, D25).
- KG is the platform's implementation of SEO Resolution Index and Relationship Reference Catalog. This is SEO substrate layer, not a separate cognitive mode.
- Outcome linkage: MACER eval harness work should eventually feed into Outcome objects. "Outcome orphaning" is a named anti-pattern.
- The 30KB content injection cap and chunking architecture align with the principle that governed knowledge assets should be versioned and selectively cited, not bulk-injected.
- LLM prompt context must not receive raw secrets or raw PII per IPDV minimum-necessary discipline.

### DiscoveryExpert / Automation Surface

- Automation is one of the four formal surface types with "background execution" as its governance character. DiscoveryExpert's scan-assess-propose-validate cycle fits the Automation surface pattern.
- `SurfaceType` enum on handler metadata: the v1.5 surface taxonomy confirms this is the right design. Automation has real infrastructure needs distinct from Assistant/Workspace/API.

---

## 16. Document Ingestion Log

| Doc | Title | Status | Key delta notes |
|-----|-------|--------|-----------------|
| Manifest | IIF v1.5 Document Set Manifest | Done | 43 files total; 16 refreshed, 26 new; full corpus map |
| 01 | Institutional Intelligence Charter | Done | 60% trim; non-bypass rules; CPEC; ECAP gate families; 11 governance functions; 13 anti-patterns |
| 02 | Domain Pack Strategy | Done | Seven real-Pack tests; 13-factor moat formula; 20 anti-patterns; MVDP checklist; Pack lifecycle stages; Pattern Packs; retirement discipline |
| 03 | Cognitive Modes - Market Opportunities | Pending | |
| 04 | ADM | Done | New in v1.5; D1-D63 decision register; declined constructs list; cross-document ownership rules; aggregation rules; mode authority boundaries |
| 05 | Canonical Object Schema Spec | Done | Verbatim v1.0 republish; no field-level changes; Appendix A maps v1.5 concepts; Schema Evolution Protocol deferred |
| 06 | Shared Entity Ontology and Object Spine | Done | New in v1.5; three-spine architecture; 20-class entity catalog (5 Tier-1 anchored); EntityRef contract; 8 non-bypass invariants; 15 relationship families; 7 supplemental eval indicators; no-recertification guarantee |
| 07 | IPDV | Done | New in v1.5; four-way Authority/Permission/Visibility/Topology distinction; effective rights formula; TraceStep has NO metadata/domain_extensions; 9 principal subclasses; 11 visibility states; 13 data classes; 11 permission verbs; 10 runtime record families; protected attributes = routing controls only |
| 08 | Skill Architecture and Governance | Pending | New in v1.5 |
| 09 | MIS | Done | New in v1.5; 8 conformance classes; 6 non-negotiable invariants; ambient-control floor (Governor+Conductor+Sentinel+Evaluator); version bundle as Trace replay contract; 4 mandatory trace modes; v1.0->v1.5 migration delta table |
| 10 | Versioning and Dependency Compatibility | Pending | New in v1.5 |
| 11 | OTCC | Pending | New in v1.5 |
| 12 | Integration and Connector Framework | Pending | New in v1.5 |
| 13 | ECAP | Pending | New in v1.5 |
| 14 | GKAF | Pending | New in v1.5 |
| 15 | TSPS | Pending | New in v1.5 |
| 16 | GOM | Pending | New in v1.5 |
| 17 | MSC | Pending | New in v1.5 |
| 18 | IEF | Pending | New in v1.5 |
| 19 | Domain Pack Spec Template | Pending | Refreshed from v1.0 |
| 20 | SBA Template | Pending | Refreshed from v1.0 (was ABA) |
| 21 | Certified Client Overlay Template | Pending | Refreshed from v1.0 |
| 22 | EP Template | Pending | Refreshed from v1.0 (was JAP) |
| 23 | Pack-Builder's Handbook | Pending | New in v1.5 |
| 24 | Solution-Builder's Handbook | Pending | New in v1.5 |
| 25 | Reasoner Deep Dive | Pending | Refreshed |
| 26 | Investigator Deep Dive | Pending | Refreshed |
| 27 | Simulator Deep Dive | Pending | New in v1.5 |
| 28 | Governor Deep Dive | Pending | Refreshed |
| 29 | Verifier Deep Dive | Pending | Refreshed |
| 30 | Sentinel Deep Dive | Pending | New in v1.5 |
| 31 | Conductor Deep Dive | Pending | Refreshed |
| 32 | Optimizer Deep Dive | Pending | New in v1.5 |
| 33 | Narrator Deep Dive | Pending | Refreshed |
| 34 | Influencer Deep Dive | Pending | New in v1.5 |
| 35 | Negotiator Deep Dive | Pending | New in v1.5 |
| 36 | Curator Deep Dive | Pending | Refreshed |
| 37 | Evaluator Deep Dive | Pending | Refreshed |
| 38 | AML Investigation Pack - Worked Example | Pending | New in v1.5 |
| 39 | SBA Worked Examples | Pending | New in v1.5 |
| 40 | Certified Client Overlay - US Regional Bank | Pending | New in v1.5 |
| 41 | EP Worked Examples | Pending | New in v1.5 |
| 42 | Reference Solution Blueprint - FinCrime Suite | Pending | New in v1.5 |
