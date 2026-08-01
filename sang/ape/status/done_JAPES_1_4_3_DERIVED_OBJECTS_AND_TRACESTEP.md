# JAPES v1.4.3 - Derived Objects + TraceStep Alignment
## Claude Code Handoff

**Author:** Virendra Mehta  
**Branch:** dev (v1.4.x line)  
**Repo:** `japes/` only  
**IIF reference:** Schema Spec v1.0 §5 (TraceStep), §7 (Derived Objects)

---

## Why this is v1.4.3, not v1.5

Both pieces of work are Schema Spec v1.0 completion - the schema was defined in v1.0 and
verbatim republished in v1.5 (ADM D6/D25, no field changes). The five canonical stores are
already in `fabric/canonical/` from v0.2.x work. This adds the remaining eight derived
objects and aligns TraceStep to the v1.0 spec fields that were never implemented.

The one TraceStep concern that IS v1.5 (version bundle fields moving from TraceStep to
Trace.metadata) is explicitly OUT OF SCOPE here - those fields stay on TraceStep per v1.0.
That relocation is handled in a separate v1.5.0 handoff.

---

## Part 1 - TraceStep alignment to Schema Spec v1.0 §5

### Current state vs. spec

The existing `TraceStep` in `jazzx_sdk/fabric/canonical/trace.py` has:
- `step_id` - correct
- `iteration` - JAPES-specific (not in spec; keep as domain_extensions candidate)
- `actor` - correct but ActorRef is missing `role` field
- `action` - correct
- `inputs` / `outputs` - `list[str]` but spec says `object` (dict of refs)
- `timestamp` - WRONG: spec has `started_at` + `completed_at` (two Required fields)
- `duration_ms` - JAPES-specific (not in spec; keep)
- `notes` - JAPES-specific (not in spec; keep)

**Missing Required fields:**
- `sequence: integer` - execution order (0-indexed)
- `mode: enum` - one of the 13 canonical modes
- `started_at: datetime` - step start timestamp
- `completed_at: datetime` - step completion timestamp
- `status: enum` - completed | failed | skipped | escalated
- `autonomy_level: integer` - effective runtime level (0-4)

**Missing Optional fields per v1.0 spec:**
- `model_version: string`
- `tools_invoked: array[ToolCall]`
- `schema_version: string` (Required in v1.0; will move to Trace.metadata in v1.5)
- `prompt_version: string` (Optional in v1.0)
- `policy_bundle_version: string` (Optional in v1.0)
- `connector_config_version: string` (Optional in v1.0)
- `evaluation_suite_version: string` (Optional in v1.0)
- `overlay_version: string` (Conditional in v1.0)

**Note on version bundle fields:** Per v1.0, these live on TraceStep. In v1.5 they move to
`Trace.metadata` with step_id correlation. Add them to TraceStep now (v1.0 compliance).
The v1.5 migration handoff will handle the relocation.

### ActorRef alignment

Current `ActorRef` has `actor_id` and `actor_type`. Spec also defines:
- `role: string` (Optional) - e.g. "l2_investigator", "bsa_officer"

Add `role: str | None = None` to `ActorRef`.

### CanonicalTrace alignment

Current `CanonicalTrace` is missing:
- `status: enum` - running | completed | failed | suspended | cancelled (Required)
- `started_at: datetime` (Required)
- `completed_at: datetime` (Conditional - required when status is terminal)
- `pack_version: string` (Required)
- `participants: array[ParticipantRef]` (Required)
- `binding_id: string` (Required - ABA/SBA identifier)
- `deployment_id: string` (Required - JAP/EP identifier)
- `outcomes_linked: array[string]` (Optional - populated post-hoc)
- `metadata: object` (Optional)
- `domain_extensions: object` (Optional)

Add `ParticipantRef` sub-schema (from Schema Spec §1.3):
```python
class ParticipantRef(BaseModel):
    participant_id: str
    participant_type: str  # "assistant" | "human" | "service" | "system"
    role: str | None = None
    joined_at: datetime | None = None
```

### OverrideEvent alignment

Current `OverrideEvent` is missing several Required fields from Schema Spec §5:
- `override_type: enum` - decision_override | approval_override | evidence_insufficiency |
  policy_interpretation | route_change | hold | escalation
- `authority_basis: string` - policy_id or authority_matrix entry that authorized this
- `reason_code: enum` - compensating_factor | missing_evidence | policy_exception |
  risk_appetite | customer_relationship | domain_judgment | safety_concern | process_error
- `policy_refs: array[string]` (Optional)
- `evidence_delta_refs: array[string]` (Optional)
- `free_text_rationale: string` (Required - currently named `reason`)
- `state_before: string` (Required)
- `state_after: string` (Required)
- `superseding_decision_id: string` (Conditional)

Current field `reason` becomes `free_text_rationale`. Add backward-compat alias.
Current field `overridden_output` becomes `overridden_object_id`. Add backward-compat alias.

### ToolCall sub-schema (new)

Needed for `TraceStep.tools_invoked`:

```python
class ToolCall(BaseModel):
    tool_id: str
    tool_version: str | None = None
    tool_type: str  # "kh_tool" | "connector" | "mcp_tool" | "skill"
    inputs_digest: str   # hash of inputs - never raw data
    outputs_digest: str  # hash of outputs - never raw data
    started_at: datetime
    completed_at: datetime
    status: str = "completed"
    cost_amount: float | None = None
    latency_ms: int | None = None
```

---

## Part 2 - Eight derived objects (Schema Spec v1.0 §7)

Create `jazzx_sdk/fabric/canonical/derived.py` with all eight derived object models.
Add stores to `store.py`. Export from `__init__.py`.

### 2.1 Case Context (`ctx_{uuid}`)

```python
class CaseContext(BaseModel):
    case_context_id: str = Field(default_factory=lambda: f"ctx_{uuid4()}")
    case_id: str
    parent_case_id: str | None = None
    source_case_ids: list[str] = Field(default_factory=list)
    subject: dict[str, Any]  # entity reference - domain defines structure
    state: str
    active_policies: list[str] = Field(default_factory=list)
    evidence_bundle: list[str] = Field(default_factory=list)
    decisions_history: list[str] = Field(default_factory=list)
    assigned_participants: list[AssignmentRef] = Field(default_factory=list)
    autonomy_ceiling: int = Field(ge=0, le=4)
    sla: dict[str, Any] | None = None
    pending_dependencies: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str
    pack_id: str
    domain_extensions: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

Add `AssignmentRef` (from Schema Spec §1.3):
```python
class AssignmentRef(BaseModel):
    participant_id: str
    participant_type: str  # "assistant" | "human" | "service" | "system"
    role: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
```

**Note on JACI alignment:** `jaci/src/jaci/schemas/japes_types.py` has `AMLContext` which
is the operational form. `CaseContext` is the governed fabric form. Domain Packs emit
`CaseContext` objects to `fabric.canonical` for persistence; they use `AMLContext` at
runtime. The Conductor assembles `CaseContext` from `AMLContext` state.

### 2.2 Case File (`casefile_{uuid}`)

```python
class CaseFileEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"event_{uuid4()}")
    timestamp: datetime
    event_type: str
    description: str
    actor: str | None = None
    object_refs: list[str] = Field(default_factory=list)

class CaseFile(BaseModel):
    case_file_id: str = Field(default_factory=lambda: f"casefile_{uuid4()}")
    case_id: str
    timeline: list[CaseFileEvent] = Field(default_factory=list)
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    findings: str
    remediation_recs: list[dict[str, Any]] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    pack_id: str
    domain_extensions: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Note on modes/schemas.py:** `jazzx_sdk/modes/schemas.py` has a `CaseFile` generic model.
That operational form stays as-is for runtime use. This `CaseFile` in `fabric/canonical/`
is the governed persisted form. They are complementary - the Conductor promotes from
the operational form to the canonical form at case completion.

### 2.3 Scenario Report (`scenario_{uuid}`)

```python
class ScenResult(BaseModel):
    scenario_id: str
    probability: float = Field(ge=0.0, le=1.0)
    outcome_description: str
    key_drivers: list[str] = Field(default_factory=list)

class ScenarioReport(BaseModel):
    scenario_report_id: str = Field(default_factory=lambda: f"scenario_{uuid4()}")
    scenario_type: str
    parameters: dict[str, Any]
    assumptions: list[str] = Field(default_factory=list)
    results: list[ScenResult] = Field(default_factory=list)
    sensitivity_analysis: dict[str, Any] | None = None
    calibration_history: list[dict[str, Any]] = Field(default_factory=list)
    linked_decision_id: str | None = None
    pack_id: str
    domain_extensions: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.4 Artifact (`artifact_{uuid}`)

```python
class Citation(BaseModel):
    claim: str
    object_ref: str       # evidence_id or policy_id
    section: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class ArtifactStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    FILED = "filed"
    REJECTED = "rejected"

class Artifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"artifact_{uuid4()}")
    artifact_type: str   # e.g. "sar_narrative", "credit_memo", "audit_packet"
    content: dict[str, Any]
    citations: list[Citation] = Field(default_factory=list)
    disclosures: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    audience: str
    approval_status: ArtifactStatus = ArtifactStatus.DRAFT
    approver: str | None = None  # Required when approved or filed
    pack_id: str
    domain_extensions: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.5 Engagement Plan (`engage_{uuid}`)

```python
class EngageStep(BaseModel):
    step_id: str = Field(default_factory=lambda: f"estep_{uuid4()}")
    sequence: int
    channel: str           # "email" | "sms" | "in_app" | "phone" | "letter"
    content_ref: str       # reference to template or content asset
    timing: dict[str, Any] # delay, schedule, trigger conditions
    branching: dict[str, Any] = Field(default_factory=dict)

class EngagementPlan(BaseModel):
    engagement_plan_id: str = Field(default_factory=lambda: f"engage_{uuid4()}")
    subject_id: str
    objective: str
    steps: list[EngageStep] = Field(default_factory=list)
    consent_refs: list[str] = Field(default_factory=list)
    outcome_linkage: dict[str, Any] | None = None
    linked_decision_id: str | None = None
    pack_id: str
    domain_extensions: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.6 Agreement Record (`agree_{uuid}`)

```python
class AgreementRecord(BaseModel):
    agreement_record_id: str = Field(default_factory=lambda: f"agree_{uuid4()}")
    agreement_type: str
    parties: list[dict[str, Any]] = Field(default_factory=list)
    terms: dict[str, Any]
    concessions: list[dict[str, Any]] = Field(default_factory=list)
    linked_decision_id: str | None = None
    effective_date: datetime | None = None
    expiry_date: datetime | None = None
    pack_id: str
    domain_extensions: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.7 Evaluation Report (`eval_{uuid}`)

**Note:** `jazzx_sdk/modes/schemas.py` already has a good `EvaluationReport`. Promote
that model here into `fabric/canonical/` with governance fields added, and make the
`modes/schemas.py` version import from canonical. Do NOT duplicate - one definition.

```python
class EvaluationReport(BaseModel):
    # Identity and linkage
    report_id: str = Field(default_factory=lambda: f"eval_{uuid4()}")
    case_id: str
    decision_id: str | None = None
    trace_id: str | None = None
    outcome_id: str | None = None

    # Time period
    period_start: datetime
    period_end: datetime = Field(default_factory=datetime.utcnow)

    # Scores (Python-computed)
    scores: dict[str, float] = Field(default_factory=dict)
    findings: list[str] = Field(default_factory=list)
    human_override_detected: bool = False

    # LLM-generated
    qualitative_assessment: str | None = None
    improvement_signals: list[Any] = Field(default_factory=list)

    # Governance fields (new vs. modes/schemas.py version)
    pack_id: str
    evaluation_suite_version: str | None = None
    domain_extensions: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = ""
```

Update `jazzx_sdk/modes/schemas.py` to import `EvaluationReport` from
`jazzx_sdk.fabric.canonical.derived` rather than defining it locally.

### 2.8 Domain Pack (`pack_{uuid}`)

```python
class PackStatus(str, Enum):
    DRAFT = "draft"
    CERTIFIED = "certified"
    SUSPENDED = "suspended"
    RETIRED = "retired"

class DomainPack(BaseModel):
    pack_id: str  # semantic slug, not UUID - e.g. "jaci-aml"
    pack_name: str
    pack_version: str
    domain_thesis: str
    scope_boundary: str
    supported_autonomy_range: dict[str, int]  # {"min": 0, "max": 2}
    cognitive_mode_activations: dict[str, str] = Field(default_factory=dict)
    policy_family_refs: list[str] = Field(default_factory=list)
    evidence_type_refs: list[str] = Field(default_factory=list)
    playbook_refs: list[str] = Field(default_factory=list)
    evaluation_asset_refs: list[str] = Field(default_factory=list)
    pattern_pack_refs: list[str] = Field(default_factory=list)
    certification_status: PackStatus = PackStatus.DRAFT
    change_log_ref: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## Part 3 - Derived object stores in store.py

Add one store class per derived object in `store.py`. All follow the same pattern as
existing canonical stores (KH entity-backed, in-memory cache, same collection).

Add entity type constants:
```python
_ENTITY_TYPE_CASE_CONTEXT = "canonical_case_context"
_ENTITY_TYPE_CASE_FILE = "canonical_case_file"
_ENTITY_TYPE_SCENARIO_REPORT = "canonical_scenario_report"
_ENTITY_TYPE_ARTIFACT = "canonical_artifact"
_ENTITY_TYPE_ENGAGEMENT_PLAN = "canonical_engagement_plan"
_ENTITY_TYPE_AGREEMENT_RECORD = "canonical_agreement_record"
_ENTITY_TYPE_EVALUATION_REPORT = "canonical_evaluation_report"
_ENTITY_TYPE_DOMAIN_PACK = "canonical_domain_pack"
```

Add store classes: `CaseContextStore`, `CaseFileStore`, `ScenarioReportStore`,
`ArtifactStore`, `EngagementPlanStore`, `AgreementRecordStore`,
`EvaluationReportStore`, `DomainPackStore`.

Each store needs `put(obj, ontology_id)` and `get(id)` methods minimum.

Add properties to `CanonicalObjectStore`:
```python
@property
def case_context(self) -> CaseContextStore: ...

@property
def case_file(self) -> CaseFileStore: ...

@property
def scenario_report(self) -> ScenarioReportStore: ...

@property
def artifact(self) -> ArtifactStore: ...

@property
def engagement_plan(self) -> EngagementPlanStore: ...

@property
def agreement_record(self) -> AgreementRecordStore: ...

@property
def evaluation_report(self) -> EvaluationReportStore: ...

@property
def domain_pack(self) -> DomainPackStore: ...
```

Also add a convenience method to `CanonicalObjectStore`:
```python
async def put_completed_case(
    self,
    case_context: CaseContext,
    case_file: CaseFile,
    artifact: Artifact | None,
    evaluation_report: EvaluationReport | None,
    outcome: Outcome | None,
    ontology_id: str,
) -> dict[str, str]:
    """
    Persist all objects from a completed case in one call.
    Returns dict of {object_type: entity_id}.
    """
```

---

## Part 4 - Update __init__.py

Add all new exports from `derived.py`:
- `CaseContext`, `AssignmentRef`
- `CaseFile`, `CaseFileEvent`
- `ScenarioReport`, `ScenResult`
- `Artifact`, `Citation`, `ArtifactStatus`
- `EngagementPlan`, `EngageStep`
- `AgreementRecord`
- `EvaluationReport` (canonical form - modes/schemas.py imports from here)
- `DomainPack`, `PackStatus`

Add new store exports:
- `CaseContextStore`, `CaseFileStore`, `ScenarioReportStore`, `ArtifactStore`
- `EngagementPlanStore`, `AgreementRecordStore`, `EvaluationReportStore`, `DomainPackStore`

Add new sub-schema exports from `trace.py`:
- `ParticipantRef`, `ToolCall`, `TraceStepStatus`, `OverrideType`, `OverrideReasonCode`

---

## Part 5 - Update modes/schemas.py

`EvaluationReport` and `CaseFile` exist in `modes/schemas.py` as runtime-layer generics.
Handle each differently:

**EvaluationReport:** Import from canonical and re-export for backward compatibility.
The canonical version adds `pack_id`, `evaluation_suite_version`, `domain_extensions`,
`created_by`. Existing callers using the modes version will get those fields as Optional
with defaults, so no breaking change.

```python
# In modes/schemas.py - replace local definition with:
from jazzx_sdk.fabric.canonical.derived import EvaluationReport  # noqa: F401
```

**CaseFile (generic):** Keep the generic `CaseFile[TInput, THypothesisContent, TDecision]`
in `modes/schemas.py` - it serves a different purpose (runtime operational form with
generic type parameters). Rename the canonical version `CanonicalCaseFile` to avoid
name collision, OR keep `CaseFile` in canonical and rename the generic in modes to
`CaseFileContext`. Decision: rename canonical to `CanonicalCaseFile` to avoid breakage.

---

## What does NOT change

- `jaci/src/jaci/` - no changes in this handoff (JACI adoption is separate work)
- Existing canonical store CRUD methods - no changes
- `fabric/canonical/policy.py`, `evidence.py`, `decision.py`, `outcome.py` - no changes
- `fabric/canonical/policy_registry.py` - no changes
- fabric.docs, fabric.graph, fabric.rag, fabric.policy stores - no changes

---

## Acceptance checks

```bash
cd /Users/foo/src/research/sangit/japes

# 1. All eight derived objects importable
python -c "
from jazzx_sdk.fabric.canonical.derived import (
    CaseContext, CaseFile, ScenarioReport, Artifact,
    EngagementPlan, AgreementRecord, EvaluationReport, DomainPack,
)
print('OK: All 8 derived objects import')
"

# 2. TraceStep has required v1.0 fields
python -c "
from jazzx_sdk.fabric.canonical.trace import TraceStep
required = {'step_id','sequence','mode','action','inputs','outputs',
            'started_at','completed_at','status','actor','autonomy_level','schema_version'}
fields = set(TraceStep.model_fields.keys())
missing = required - fields
assert not missing, f'Missing TraceStep fields: {missing}'
print('OK: TraceStep has all v1.0 required fields')
"

# 3. OverrideEvent has required v1.0 fields
python -c "
from jazzx_sdk.fabric.canonical.trace import OverrideEvent
required = {'override_event_id','overridden_object_id','override_type',
            'actor','authority_basis','reason_code','free_text_rationale',
            'state_before','state_after'}
fields = set(OverrideEvent.model_fields.keys())
missing = required - fields
assert not missing, f'Missing OverrideEvent fields: {missing}'
print('OK: OverrideEvent has all v1.0 required fields')
"

# 4. CanonicalObjectStore has derived object stores
python -c "
from jazzx_sdk.fabric.canonical.store import CanonicalObjectStore
props = ['case_context','case_file','artifact','evaluation_report','domain_pack']
for p in props:
    assert hasattr(CanonicalObjectStore, p), f'Missing store property: {p}'
print('OK: CanonicalObjectStore has all derived object stores')
"

# 5. EvaluationReport is sourced from canonical (not duplicated)
python -c "
from jazzx_sdk.modes.schemas import EvaluationReport as ModesER
from jazzx_sdk.fabric.canonical.derived import EvaluationReport as CanonER
assert ModesER is CanonER, 'EvaluationReport is duplicated - should be same class'
print('OK: EvaluationReport is single canonical definition')
"

# 6. Full test suite passes
python -m pytest tests/ -x -q 2>&1 | tail -5
```

---

## CHANGELOG entry for v1.4.3

```markdown
## [1.4.3] - 2026-06-XX

**Schema Spec v1.0 Completion:** Implements all eight derived objects and aligns
TraceStep, CanonicalTrace, and OverrideEvent to Schema Spec v1.0 §5-7.

### Added
- `jazzx_sdk/fabric/canonical/derived.py` - All 8 derived objects (Schema Spec v1.0 §7)
  - CaseContext (ctx_{uuid}) - governed work-item envelope
  - CanonicalCaseFile (casefile_{uuid}) - investigation artifact
  - ScenarioReport (scenario_{uuid}) - scenario analysis
  - Artifact (artifact_{uuid}) - audience-facing deliverables with citations
  - EngagementPlan (engage_{uuid}) - engagement sequence
  - AgreementRecord (agree_{uuid}) - negotiation outcomes
  - EvaluationReport (eval_{uuid}) - canonical evaluation report (promoted from modes layer)
  - DomainPack (pack_{uuid}) - governed Pack artifact
- 8 new KH-backed stores on CanonicalObjectStore
- `put_completed_case()` convenience method on CanonicalObjectStore

### Changed
- `TraceStep` - added Required fields: sequence, mode, started_at, completed_at,
  status, autonomy_level, schema_version; added Optional fields: model_version,
  prompt_version, policy_bundle_version, tools_invoked; timestamp field kept as
  backward-compat alias for started_at
- `CanonicalTrace` - added status, started_at, completed_at, pack_version,
  participants, binding_id, deployment_id, outcomes_linked, metadata, domain_extensions
- `OverrideEvent` - aligned to v1.0 spec; added override_type, authority_basis,
  reason_code, free_text_rationale, state_before, state_after, superseding_decision_id;
  reason/overridden_output kept as backward-compat aliases
- `ActorRef` - added optional role field
- `modes/schemas.py` - EvaluationReport now imports from fabric.canonical.derived
```
