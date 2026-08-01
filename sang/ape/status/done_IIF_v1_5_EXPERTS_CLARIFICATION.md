# IIF v1.5 - Expert Architecture Clarification
## Claude Code Handoff

**Author:** Virendra Mehta  
**Repos affected:** `japes/`, `jaci/`  
**Status:** Design reference - no immediate code changes required; read before touching Expert-related code

---

## Why this document exists

"Expert" is used in three different senses across the JazzX codebase, and v1.5 of the IIF formally distinguishes all three. This causes real confusion when reading architecture docs and deciding where to put new code. This note settles the definitions and maps current code to them.

---

## The three senses of "Expert"

### Sense 1: Python class in jaci/ (the five AML specializations)

Files: `jaci/src/jaci/experts/aml_*.py`

These are **T1 Pack-exported Skills** in v1.5 terms. Each one:
- Activates a specific cognitive mode posture for one task class
- Operates within the L2 Investigation Workspace surface
- Is covered by ONE SBA (the L2 Workspace SBA) - not separate SBAs per Expert
- Produces **Decision Candidates** - not operative Decisions until an Authority Matrix gate fires

Current mapping to v1.5 primitives:

| File | Mode activation | v1.5 Registry/Matrix | Output classification |
|------|----------------|----------------------|----------------------|
| `aml_investigative.py` | Investigator (Primary, D53/D54) | Investigation Playbook Registry + Investigation Decision Authority Matrix | Decision Candidate until D54 gate |
| `aml_policy.py` | Reasoner (Primary, D52) | Reasoner Decision Logic Registry + Decision Authority Matrix | Decision Candidate until D52 gate |
| `aml_evidence.py` | Verifier (Activated, D57/D58) | Verification Asset Registry + Evidence Admissibility Authority Matrix | Candidate Evidence until D58 attests |
| `aml_playbook.py` | Conductor (Activated, D59/D60) | Workflow Asset Registry + Workflow Execution Authority Matrix | Operational Receipt / workflow step |
| `aml_governance.py` | Governor (Activated, ambient floor) | Enforces all matrices | ALLOW / DENY / ESCALATE verdict |

**What this means for new code:** Expert specializations belong in `jaci/src/jaci/experts/`, not in `japes/`. They are Pack-owned T1 Skills. The platform SDK (`japes/jazzx_sdk/experts/`) provides the base contracts; JACI subclasses them.

### Sense 2: Platform Expert contracts in japes/jazzx_sdk/experts/

Files: `japes/jazzx_sdk/experts/base.py`, `catalog.py`, `registry.py`, per-Expert subdirs

These are the **T0/T1 base contracts** - platform-provided abstract base classes that JACI's Expert specializations extend. The `EXPERT_REGISTRY` in `catalog.py` defines the ExpertContracts. This layer is correct as designed.

**What this means for new code:** Platform-level Expert infrastructure (BaseExpert, ExpertContract, ExpertRegistry) stays here. Domain-specific Expert implementations (AML*, KYC*) always live in the domain repo (jaci/).

### Sense 3: Advisory API/Service surfaces ("Policy Expert", "Playbook Expert")

In the AML Pack reference design, the Policy Expert and Playbook Expert are **actual API/Service surfaces** - a different surface type from the five intra-workspace specializations above. They:
- Have their own SBAs (separate from the L2 Workspace SBA)
- Are advisory only (L0 autonomy posture at launch)
- Return `guidance_refs` output only - never `authority_basis`
- Are deployed as separate EPs

These do not yet exist as deployed surfaces in JACI. They are planned as stubs. When built, they belong as separate JAPES extensions (API/Service surface type), not as more entries in `jaci/src/jaci/experts/`.

---

## The output classification rule (MSC §7.5)

This is the most important behavioral change implied by the v1.5 framework that current JACI does not enforce.

Every Expert output must be **explicitly classified** before it can be used downstream:

```python
# Classification vocabulary (from MSC §7.5)
class OutputClassification(str, Enum):
    DECISION_CANDIDATE = "decision_candidate"      # Not operative until Authority Matrix gate
    CANDIDATE_EVIDENCE = "candidate_evidence"      # Not admissible until Verifier/D58 attests
    DRAFT_ARTIFACT = "draft_artifact"              # Not external until Narrator releases via D62
    OPERATIONAL_RECEIPT = "operational_receipt"    # Workflow step completion record
    GUIDANCE_REFS = "guidance_refs"                # Advisory only; never authority_basis
    TELEMETRY = "telemetry"                        # Observability only; never governs
```

Current JACI behavior: Expert outputs flow more directly into disposition without explicit classification. This is not a blocking defect today (JACI is Pilot/Incubating maturity) but must be addressed before Certified status.

**Where to add this:** `japes/jazzx_sdk/experts/base.py` - the `ExpertResponse` model should carry an `output_classification` field. JACI Expert subclasses set it per operation.

---

## What does NOT change

The existing Python class hierarchy is structurally sound:

```
japes/jazzx_sdk/experts/
    base.py          # BaseExpert[T], ExpertRequest, ExpertResponse - correct
    catalog.py       # EXPERT_REGISTRY with 5 ExpertContracts - correct
    {expert}/base.py # Per-Expert abstract base contracts - correct
    {expert}/default.py # Default implementations - correct

jaci/src/jaci/experts/
    aml_*.py         # T1 Pack-exported Skills - correct home, correct pattern
```

The `BaseExpert` -> `AMLInvestigativeExpert` inheritance chain is the right design. Nothing needs to be moved. What needs to be added are the governance-layer fields: `output_classification`, `skill_manifest_ref`, `action_class_refs`, `matrix_cell_ref` on ExpertResponse.

---

## The DiscoveryExpert (sixth Expert)

`japes/jazzx_sdk/experts/discovery/` already exists as a directory.

In v1.5 terms, DiscoveryExpert maps to:
- **Surface type:** Automation (not API/Service, not Workspace)
- **Pattern:** Expert Surface Pattern + Automation surface type
- **Autonomy:** Advisory only (L0) at launch - Phase 0 read-only pilot
- **Outputs:** Decision Candidate (propose step) until Authority Matrix gate fires
- **SBA:** Separate from the L2 Workspace SBA and from the Policy Expert API/Service SBA - Automation surface needs its own SBA

Do not deploy DiscoveryExpert as a Workspace Expert or an API/Service Expert. It is an Automation surface Expert.

---

## Anti-patterns to avoid when writing new Expert code

- **Expert-as-Pack** - do not give an Expert its own Pack manifest, its own ontology, its own policy library
- **Expert-as-surface** - do not create a separate SBA or EP per intra-workspace Expert specialization
- **Expert-to-Expert direct call** - all cross-Expert invocation must go through the orchestrator (Conductor mode). No direct Python imports between `aml_investigative.py` and `aml_evidence.py` for substantive work.
- **Expert output as authority** - `expert_response.result` is a Decision Candidate. The Authority Matrix gate (Governor enforcement) must fire before it becomes an operative Decision.
- **Global-Expert authority leakage** - consuming Policy Expert or Playbook Expert API output as `authority_basis`. These surfaces are advisory-only; their output is always `guidance_refs`.

---

## Acceptance checks

If you have modified Expert-related code, verify:

```bash
# 1. JACI Expert specializations stay in jaci/
ls jaci/src/jaci/experts/aml_*.py

# 2. Platform Expert contracts stay in japes/
ls japes/jazzx_sdk/experts/base.py japes/jazzx_sdk/experts/catalog.py

# 3. No Expert in jaci/ imports another Expert directly for substantive work
grep -r "from jaci.experts import" jaci/src/jaci/experts/

# 4. ExpertResponse carries output_classification (once added)
grep "output_classification" japes/jazzx_sdk/experts/base.py

# 5. DiscoveryExpert surface type is declared as Automation
grep -r "automation\|AUTOMATION" japes/jazzx_sdk/experts/discovery/
```

---

## Related docs

- IIF v1.5 Charter & Migration Guide: https://www.notion.so/3732471607bf81e89c78de00f86c0b2a (Section 12)
- AML Pack mode composition table: same page, Section 11
- MSC output classification rule: IIF v1.5 Migration Guide sections 24-27
- Pack-Builder's Handbook Expert Surface Pattern: IIF v1.5 Migration Guide sections 32-35
