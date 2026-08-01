# Task: DiscoveryExpert + Automation Surface Implementation

**Priority:** Medium (new capability, not fixing existing)
**Repos:** `japes` (jazzx_runtime_sdk) and `jaci` (scenarios)
**Branch:** `dev`
**Reference:** See Notion page "DiscoveryExpert + Automation Surface" under "From Vision to Code"

---

## JAPES Tasks

### Task 1: DiscoveryExpert Base Classes (2 days)

Create `jazzx_runtime_sdk/experts/discovery/`:

```
discovery/
├── __init__.py
├── base.py        # DiscoveryExpert base class
└── default.py     # Default implementation
```

**base.py** — `DiscoveryExpert` with 4 abstract operations:

```python
class DiscoveryExpert(BaseExpert[T]):
    """
    Proactive external knowledge acquisition.
    
    Searches outside the platform for new information, assesses relevance
    to domain packs, and proposes governed updates to pack assets.
    
    Distinct from EvidenceExpert: EvidenceExpert attests evidence for a
    specific case. DiscoveryExpert proposes knowledge updates for the pack.
    One serves decisions. The other serves learning.
    """
    
    async def scan(self, config: ScanConfig, trace_id: str | None = None) -> list[Finding]:
        """Search external sources for new findings."""
        
    async def assess(self, finding: Finding, target_packs: list[str]) -> RelevanceAssessment:
        """Evaluate relevance, classify by affected domain and pack assets."""
        
    async def propose(self, assessment: RelevanceAssessment, target_asset: str) -> UpdateProposal:
        """Generate specific update proposal for a target pack asset."""
        
    async def validate(self, proposal: UpdateProposal, gold_cases: list[str]) -> ValidationResult:
        """Run proposal against gold cases, check for regression."""
```

**default.py** — Default implementation with:
- Generic scan orchestration (iterate over configured sources, deduplicate against Knowledge Fabric)
- Source credibility scoring via VerifierMode
- Relevance scoring framework (domain-agnostic)
- Update proposal formatting (target pack, asset type, proposed content, provenance)
- Validation harness (load gold cases, run eval, report regression)

**New schemas** (in `jazzx_runtime_sdk/experts/discovery/schemas.py`):

```python
class ScanConfig(BaseModel):
    sources: list[str]           # Source identifiers
    domains: list[str]           # Target domains (aml, kyc, etc.)
    criteria: dict[str, Any]     # Domain-specific relevance criteria
    exclusions: list[str] = []   # Known patterns to skip

class Finding(BaseModel):
    finding_id: str
    source: str                  # Where it was found
    source_credibility: str      # HIGH, MEDIUM, LOW
    content_summary: str
    raw_content: str | None = None
    timestamp: datetime
    provenance_url: str | None = None

class RelevanceAssessment(BaseModel):
    finding_id: str
    relevance_score: float       # 0.0 - 1.0
    affected_domains: list[str]
    affected_assets: list[str]   # e.g. ["aml.investigator.skill", "kyc.governor.policy"]
    classification: str          # new_typology, modified_typology, regulatory_change, etc.
    rationale: str

class UpdateProposal(BaseModel):
    proposal_id: str
    finding_id: str
    target_pack: str
    target_asset_type: str       # skill, policy, evidence_pattern, playbook
    target_asset_id: str         # e.g. "investigator_skill"
    proposed_content: str
    provenance: dict[str, Any]   # source, cross_refs, assessment_rationale
    validation_status: str = "pending"  # pending, passed, failed, regression_detected

class ValidationResult(BaseModel):
    proposal_id: str
    gold_cases_run: int
    passed: int
    failed: int
    regression_detected: bool
    regression_details: list[str] = []
```

**Updates to existing files:**
- `jazzx_runtime_sdk/experts/catalog.py` — Add DiscoveryExpert to `EXPERT_REGISTRY` (now 6 ExpertContracts)
- `jazzx_runtime_sdk/experts/__init__.py` — Export DiscoveryExpert
- `jazzx_runtime_sdk/experts/README.md` — Document DiscoveryExpert alongside the other 5

### Task 2: AutomationHandler Base Class (1 day)

Create `jazzx_runtime_sdk/automation/`:

```
automation/
├── __init__.py
├── handler.py     # AutomationHandler base
└── schemas.py     # Automation-specific schemas
```

**handler.py** — `AutomationHandler` extending the existing Handler:

```python
class AutomationHandler(Handler):
    """
    Base handler for Automation surface executions.
    
    Extends Handler with:
    - trigger_type tracking (scheduled / event / manual)
    - run_id for idempotency across retries
    - stage_output() for writing proposals to Knowledge Fabric staging
    - automation-specific trace emission
    """
    
    @property
    def trigger_type(self) -> str:
        """Extract trigger_type from message payload."""
        return self.message.payload.get("trigger_type", "manual")
    
    @property
    def run_id(self) -> str:
        """Unique run ID for idempotency."""
        return self.message.payload.get("run_id", str(uuid4()))
    
    async def stage_output(self, proposals: list[UpdateProposal], staging_area: str) -> None:
        """Write proposals to Knowledge Fabric staging area with provenance."""
        
    async def emit_automation_trace(
        self, run_id: str, trigger: dict, findings: list, proposals: list
    ) -> CanonicalTrace:
        """Emit CanonicalTrace for the automation run."""
```

**schemas.py:**

```python
class AutomationTrigger(BaseModel):
    trigger_type: str            # scheduled, event, manual
    trigger_source: str          # flowable_timer, sanctions_feed, manual_invocation
    trigger_time: datetime
    scan_config: ScanConfig | None = None
    event_payload: dict[str, Any] | None = None

class AutomationRunRecord(BaseModel):
    run_id: str
    trigger: AutomationTrigger
    status: str                  # running, completed, failed
    findings_count: int = 0
    proposals_count: int = 0
    started_at: datetime
    completed_at: datetime | None = None
    trace_id: str | None = None
```

**Updates:**
- Add `trigger_type` field to message payload schema in `jazzx_runtime_sdk/models.py`
- Export AutomationHandler from `jazzx_runtime_sdk/handlers.py`

### Task 3: Flowable BPMN Templates (1 day)

Create `bpmn/templates/`:

```
bpmn/templates/
├── scheduled_automation.bpmn    # Timer start → enqueue → wait → human review → promote
├── event_triggered_automation.bpmn  # Signal start → enqueue → wait → route
└── README.md                    # How to customize for specific automations
```

**scheduled_automation.bpmn:**
- Timer start event (parameterized cron expression)
- Service task: enqueue invocation message with targetId and scan config
- Receive task: wait for japes-response
- Exclusive gateway: any proposed updates?
  - Yes: User task (compliance officer review)
    - Exclusive gateway: approved?
      - Yes: Service task (promote to live pack)
      - No: Service task (archive with rejection reason)
  - No: End event

**README.md** documents how to create a specific automation from the template (which targetId, which payload structure, which review flow).

---

## JACI Tasks

### Task 4: Threat Intelligence Scenario (3 days)

Create `src/jaci/scenarios/threat_intel/`:

```
threat_intel/
├── __init__.py
├── README.md
├── conductor.py                 # ThreatIntelConductor
├── modes/
│   ├── __init__.py
│   ├── investigator.py          # Search strategy for external sources
│   ├── reasoner.py              # Relevance assessment and classification
│   ├── verifier.py              # Source credibility and deduplication
│   └── governor.py              # Update threshold enforcement
├── schemas/
│   ├── __init__.py
│   └── threat_intel_schemas.py
├── tools/
│   ├── __init__.py
│   └── threat_intel_mock_connectors.py
└── pack/
    └── threat_intel_config.py
```

**conductor.py** — `ThreatIntelConductor` process:

1. Load scan config from pack
2. DiscoveryExpert.scan() — search external sources
3. DiscoveryExpert.assess() — evaluate each finding
4. EvidenceExpert.verify() — attest source credibility, deduplicate
5. GovernanceExpert.enforce() — check update threshold
6. DiscoveryExpert.propose() — generate update proposals
7. DiscoveryExpert.validate() — run against gold cases
8. Stage outputs in Knowledge Fabric
9. Emit CanonicalTrace

**prompts/threat-intel/:**
- `investigator.md` — External threat source search strategy
- `reasoner.md` — Relevance assessment and typology classification
- `verifier.md` — Source credibility scoring and deduplication
- `governor.md` — Update threshold enforcement rules

**Mock connectors** return pre-defined findings:
- Reuters article about drug mule network (new typology)
- OFAC SDN list update (sanctions trigger)
- FATF grey list revision (jurisdiction risk change)
- Blog post with unverified claims (low credibility, should be rejected)

**Gold cases** in `tests/eval/gold_cases/threat_intel/`:

| # | Scenario | Expected |
|---|----------|----------|
| ti_01 | Known typology in new source | Deduplicate, no update |
| ti_02 | New typology variant (mule network) | Propose new evidence pattern |
| ti_03 | Sanctions list update | Trigger re-screening, no skill update |
| ti_04 | New CDD regulation | Propose policy update |
| ti_05 | Low-credibility source | Reject below threshold |
| ti_06 | Finding affects multiple packs | Propose updates to both |
| ti_07 | Proposal causes gold case regression | Flag, do not auto-stage |

**Eval harness:** `tests/eval/run_threat_intel_eval.py`

### Task 5: AML DiscoveryExpert Specialization (1 day)

Create `src/jaci/scenarios/aml/experts/discovery.py`:

```python
class AMLDiscoveryExpert(DiscoveryExpert):
    """
    AML-specialized external knowledge acquisition.
    
    Scan sources: sanctions databases, FATF, FinCEN, adverse media
    Assessment criteria: new typology, modified typology, jurisdiction risk, entity risk
    Target assets: Investigator skills, Reasoner skills, Governor policies
    """
```

---

## Execution Order

1. JAPES Task 1 (DiscoveryExpert base) — foundation, do first
2. JAPES Task 2 (AutomationHandler) — can parallel with Task 1
3. JACI Task 4 (threat intel scenario) — depends on Tasks 1 and 2
4. JACI Task 5 (AML specialization) — depends on Task 4
5. JAPES Task 3 (BPMN templates) — can parallel, needed for production deployment

## Verification

After each task:
- `pytest tests/unit/` passes
- `pytest tests/integration/` passes
- New schemas validate via Pydantic
- Existing scenarios unaffected

After all tasks:
- ThreatIntelConductor runs end-to-end on mock data
- 7 gold cases produce expected outcomes
- DiscoveryExpert registered in EXPERT_REGISTRY alongside original 5
- AutomationHandler available for import

## Estimated Total: ~8 days
