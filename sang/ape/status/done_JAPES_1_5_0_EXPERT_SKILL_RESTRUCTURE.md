# JAPES v1.5.0 - Expert / Skill Restructure
## Claude Code Handoff

**Author:** Virendra Mehta  
**Branch:** v1.5 (from dev, which is now on v1.4.2)  
**Repos:** `japes/` (primary), `jaci/` (downstream - import updates only)

---

## Why this change

IIF v1.5 formalizes Expert nomenclature. Two named Expert surfaces exist: **Policy Expert** and **Playbook Expert**. The names Governance Expert, Evidence Expert, and Investigative Expert are retired at the platform layer because they directly shadow the Governor, Verifier, and Investigator cognitive modes, creating conceptual ambiguity.

The three retiring Expert subdirectories contain real, substantive content (result models, operation contracts, typed abstract methods). That content is not deleted - it is relocated:

- Result models and operation contracts → `jazzx_sdk/skills/` (new directory)
- JACI domain implementations → already in `jaci/src/jaci/experts/`, import paths updated

---

## What changes and what does NOT change

### Does NOT change

- `jazzx_sdk/experts/base.py` - BaseExpert, ExpertRequest, ExpertResponse - keep as-is
- `jazzx_sdk/experts/policy/` - PolicyExpert base - keep as-is
- `jazzx_sdk/experts/playbook/` - PlaybookExpert base - keep as-is  
- `jazzx_sdk/experts/discovery/` - DiscoveryExpert base - keep as-is (Automation surface Expert)
- `jazzx_sdk/experts/registry.py` - ExpertRegistry - keep as-is
- `jazzx_sdk/experts/stubs.py` - keep as-is
- `jaci/src/jaci/experts/aml_policy.py` - no change needed
- `jaci/src/jaci/experts/aml_playbook.py` - no change needed
- All modes, fabric, canonical objects, agents layer - no change

### Changes

**In `japes/`:**
1. Create `jazzx_sdk/skills/` directory with three new base modules
2. Remove `jazzx_sdk/experts/governance/`, `evidence/`, `investigative/` directories
3. Update `jazzx_sdk/experts/catalog.py` - EXPERT_REGISTRY trimmed from 6 to 3 entries
4. Update `jazzx_sdk/experts/__init__.py` - remove exports for removed types
5. Add `output_classification` field to `ExpertResponse` in `experts/base.py`

**In `jaci/`:**
1. Update imports in `aml_governance.py`, `aml_evidence.py`, `aml_investigative.py`

---

## Phase 1 - Create jazzx_sdk/skills/

Create the following directory structure. Content is migrated from the three retiring Expert bases.

### jazzx_sdk/skills/__init__.py

```python
"""
Platform Skill bundles - multi-operation action class implementations.

Skills implement action classes declared by cognitive modes. They are
T0/T1 artifacts in the Skill Architecture (IIF v1.5).

Unlike Expert surfaces (policy/, playbook/, discovery/), Skill bundles
are not surfaces. They are the action-class implementation layer that
domain Packs subclass.

Available platform Skill bundles:
  - governance: Implements Governor-mode action classes (enforce, capture_override, audit)
  - evidence: Implements Verifier-mode action classes (collect, verify, assess_sufficiency)
  - investigation: Implements Investigator-mode action classes (investigate, narrate, benchmark)
"""

from jazzx_sdk.skills.governance.base import (
    BaseGovernanceSkill,
    EnforcementResult,
    CeilingResult,
    OverrideRecord,
    AuditPackage,
)
from jazzx_sdk.skills.evidence.base import (
    BaseEvidenceSkill,
    EvidenceCollectionResult,
    VerificationReport,
    SufficiencyReport,
    FreshnessReport,
    ContradictionReport,
)
from jazzx_sdk.skills.investigation.base import (
    BaseInvestigationSkill,
    InvestigationResult,
    NarrativeResult,
    PatternRecognitionResult,
    BenchmarkReport,
)

__all__ = [
    "BaseGovernanceSkill",
    "EnforcementResult",
    "CeilingResult",
    "OverrideRecord",
    "AuditPackage",
    "BaseEvidenceSkill",
    "EvidenceCollectionResult",
    "VerificationReport",
    "SufficiencyReport",
    "FreshnessReport",
    "ContradictionReport",
    "BaseInvestigationSkill",
    "InvestigationResult",
    "NarrativeResult",
    "PatternRecognitionResult",
    "BenchmarkReport",
]
```

### jazzx_sdk/skills/governance/__init__.py and base.py

Move content verbatim from `jazzx_sdk/experts/governance/base.py` into
`jazzx_sdk/skills/governance/base.py` with these changes:

- Class renamed: `BaseGovernanceExpert` → `BaseGovernanceSkill`
- Base class changed: extends `ABC` directly (not `BaseExpert`)
- Remove `expert_type` property and `supported_operations()` - those are Expert surface concerns
- Keep all result models unchanged: `EnforcementResult`, `CeilingResult`, `OverrideRecord`, `AuditPackage`
- Keep all four abstract methods unchanged: `enforce()`, `enforce_ceiling()`, `capture_override()`, `generate_audit_package()`
- Update module docstring to reflect Skill framing

```python
# jazzx_sdk/skills/governance/base.py - key structural change

from abc import ABC, abstractmethod

class BaseGovernanceSkill(ABC):
    """
    Base Skill contract for Governor-mode action classes.

    Implements action classes declared by Governor mode:
    - enforce(): Policy gate evaluation (ALLOW/DENY/ESCALATE verdict)
    - enforce_ceiling(): Autonomy ceiling enforcement
    - capture_override(): Override event capture with audit trail
    - generate_audit_package(): Audit package assembly for regulators

    Domain Packs subclass this to provide domain-specific gate logic.
    The IIF v1.5 responsibility chain: Governor mode declares the action
    class; this Skill implements it; the Authority Matrix gates when it may run.

    Not a surface. Not an Expert. Does not grant authority.
    """

    def __init__(self, pack_id: str | None = None, **kwargs):
        self.pack_id = pack_id

    # Keep all four abstract methods verbatim from BaseGovernanceExpert
```

### jazzx_sdk/skills/evidence/__init__.py and base.py

Same migration pattern from `jazzx_sdk/experts/evidence/base.py`:

- Class renamed: `BaseEvidenceExpert` → `BaseEvidenceSkill`
- Base class: `ABC` directly
- Remove `expert_type` and `supported_operations()`
- Keep all five result models unchanged
- Keep all five abstract methods unchanged: `collect()`, `verify()`, `assess_sufficiency()`, `monitor_freshness()`, `detect_contradictions()`

### jazzx_sdk/skills/investigation/__init__.py and base.py

Same migration pattern from `jazzx_sdk/experts/investigative/base.py`:

- Class renamed: `BaseInvestigativeExpert` → `BaseInvestigationSkill`
- Base class: `ABC` directly
- Remove `expert_type` and `supported_operations()`
- Keep all four result models unchanged
- Keep all four abstract methods unchanged: `investigate()`, `narrate()`, `recognize_patterns()`, `benchmark()`

---

## Phase 2 - Update experts/catalog.py

Trim EXPERT_REGISTRY from 6 entries to 3. Remove `evidence`, `governance`, `investigative`.

```python
EXPERT_REGISTRY: dict[str, ExpertContract] = {
    "policy": ExpertContract(...),    # keep unchanged
    "playbook": ExpertContract(...),  # keep unchanged
    "discovery": ExpertContract(...), # keep unchanged
    # evidence, governance, investigative REMOVED
}
```

Also update `primary_modes` in remaining contracts if they referenced the removed types.

---

## Phase 3 - Update experts/base.py

Add `output_classification` field to `ExpertResponse`:

```python
from enum import Enum

class OutputClassification(str, Enum):
    """
    IIF v1.5 MSC §7.5 output classification vocabulary.
    Expert outputs must be explicitly classified before use downstream.
    """
    DECISION_CANDIDATE = "decision_candidate"   # Not operative until Authority Matrix gate
    CANDIDATE_EVIDENCE = "candidate_evidence"   # Not admissible until Verifier/D58 attests
    DRAFT_ARTIFACT = "draft_artifact"           # Not external until Narrator releases via D62
    OPERATIONAL_RECEIPT = "operational_receipt" # Workflow step completion record
    GUIDANCE_REFS = "guidance_refs"             # Advisory only; never authority_basis
    TELEMETRY = "telemetry"                     # Observability only; never governs


class ExpertResponse(BaseModel):
    success: bool = ...
    operation: str = ...
    result: Any = ...
    error: str | None = ...
    trace_id: str | None = ...
    metadata: dict[str, Any] = ...
    # NEW field:
    output_classification: OutputClassification | None = Field(
        None,
        description=(
            "IIF v1.5 MSC §7.5 output classification. "
            "Expert subclasses set this per operation. "
            "Downstream consumers must not treat output as operative until classification is set "
            "and the appropriate Authority Matrix gate has fired."
        ),
    )
```

---

## Phase 4 - Update experts/__init__.py

Remove exports for the three retired types. Keep:

```python
from jazzx_sdk.experts.base import BaseExpert, ExpertRequest, ExpertResponse, OutputClassification
from jazzx_sdk.experts.catalog import EXPERT_REGISTRY, ExpertContract, ...
from jazzx_sdk.experts.registry import ExpertRegistry
from jazzx_sdk.experts.stubs import NotImplementedExpert, ExpertNotImplementedError
from jazzx_sdk.experts.policy.base import BasePolicyExpert, ...
from jazzx_sdk.experts.playbook.base import BasePlaybookExpert, ...
from jazzx_sdk.experts.discovery.base import BaseDiscoveryExpert, ...
# DO NOT export: BaseGovernanceExpert, BaseEvidenceExpert, BaseInvestigativeExpert
# and their result models - those now live in jazzx_sdk.skills
```

Also add convenience re-exports for the new skills layer:

```python
# Skill bundles (IIF v1.5)
from jazzx_sdk.skills import (
    BaseGovernanceSkill, BaseEvidenceSkill, BaseInvestigationSkill,
    # result models...
)
```

---

## Phase 5 - Remove retiring Expert directories

After skills/ is created and tested:

```bash
rm -rf jazzx_sdk/experts/governance/
rm -rf jazzx_sdk/experts/evidence/
rm -rf jazzx_sdk/experts/investigative/
```

---

## Phase 6 - Update jaci/ imports

### jaci/src/jaci/experts/aml_governance.py

```python
# OLD
from jazzx_sdk.experts.governance import (
    BaseGovernanceExpert,
    EnforcementResult,
    CeilingResult,
    OverrideRecord,
    AuditPackage,
)

# NEW
from jazzx_sdk.skills.governance import (
    BaseGovernanceSkill,
    EnforcementResult,
    CeilingResult,
    OverrideRecord,
    AuditPackage,
)

# OLD class definition
class AMLGovernanceExpert(BaseGovernanceExpert):

# NEW class definition  
class AMLGovernanceExpert(BaseGovernanceSkill):
```

### jaci/src/jaci/experts/aml_evidence.py

```python
# OLD
from jazzx_sdk.experts.evidence import (
    BaseEvidenceExpert, EvidenceCollectionResult, ...
)

# NEW
from jazzx_sdk.skills.evidence import (
    BaseEvidenceSkill, EvidenceCollectionResult, ...
)

class AMLEvidenceExpert(BaseEvidenceSkill):  # was BaseEvidenceExpert
```

### jaci/src/jaci/experts/aml_investigative.py

```python
# OLD
from jazzx_sdk.experts.investigative import (
    BaseInvestigativeExpert, InvestigationResult, ...
)

# NEW
from jazzx_sdk.skills.investigation import (
    BaseInvestigationSkill, InvestigationResult, ...
)

class AMLInvestigativeExpert(BaseInvestigationSkill):  # was BaseInvestigativeExpert
```

---

## What this does NOT change

- The JACI `aml_governance.py`, `aml_evidence.py`, `aml_investigative.py` implementations themselves - only their base class imports change
- All result model field definitions - verbatim migration
- All abstract method signatures - verbatim migration
- Default implementations in `experts/governance/default.py`, `evidence/default.py`, `investigative/default.py` - these migrate to `skills/governance/default.py` etc. with the same rename pattern
- JACI `aml_policy.py` and `aml_playbook.py` - no changes needed
- All tests - update imports only, no logic changes

---

## Backward compatibility shim (optional, recommended)

After migration, add to `jazzx_sdk/experts/__init__.py`:

```python
# Backward compatibility - deprecated, remove in v1.6
import warnings

def __getattr__(name):
    _compat = {
        "BaseGovernanceExpert": ("jazzx_sdk.skills.governance", "BaseGovernanceSkill"),
        "BaseEvidenceExpert":   ("jazzx_sdk.skills.evidence",   "BaseEvidenceSkill"),
        "BaseInvestigativeExpert": ("jazzx_sdk.skills.investigation", "BaseInvestigationSkill"),
    }
    if name in _compat:
        module_path, new_name = _compat[name]
        warnings.warn(
            f"{name} moved to {module_path}.{new_name} (IIF v1.5 nomenclature). "
            f"Update your imports. This shim will be removed in v1.6.",
            DeprecationWarning,
            stacklevel=2,
        )
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, new_name)
    raise AttributeError(f"module 'jazzx_sdk.experts' has no attribute {name!r}")
```

---

## Acceptance checks

```bash
# 1. Skills directory exists with three modules
ls jazzx_sdk/skills/governance/base.py
ls jazzx_sdk/skills/evidence/base.py
ls jazzx_sdk/skills/investigation/base.py

# 2. Retiring Expert directories are gone
[ ! -d jazzx_sdk/experts/governance ] && echo "OK: governance removed"
[ ! -d jazzx_sdk/experts/evidence ]   && echo "OK: evidence removed"
[ ! -d jazzx_sdk/experts/investigative ] && echo "OK: investigative removed"

# 3. EXPERT_REGISTRY has exactly 3 entries
python -c "
from jazzx_sdk.experts.catalog import EXPERT_REGISTRY
assert set(EXPERT_REGISTRY.keys()) == {'policy', 'playbook', 'discovery'}, EXPERT_REGISTRY.keys()
print('OK: EXPERT_REGISTRY has exactly 3 entries')
"

# 4. OutputClassification is on ExpertResponse
python -c "
from jazzx_sdk.experts.base import ExpertResponse, OutputClassification
r = ExpertResponse(success=True, operation='test', output_classification=OutputClassification.GUIDANCE_REFS)
print('OK: OutputClassification on ExpertResponse:', r.output_classification)
"

# 5. JACI imports resolve
python -c "
from jaci.experts.aml_governance import AMLGovernanceExpert
from jaci.experts.aml_evidence import AMLEvidenceExpert
from jaci.experts.aml_investigative import AMLInvestigativeExpert
print('OK: JACI Expert imports resolve')
"

# 6. Backward compat shim works
python -c "
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter('always')
    from jazzx_sdk.experts import BaseGovernanceExpert  # should warn, not error
    assert len(w) == 1 and issubclass(w[0].category, DeprecationWarning)
    print('OK: Backward compat shim fires DeprecationWarning')
"

# 7. All existing tests pass
cd /Users/foo/src/research/sangit/japes && python -m pytest tests/ -x -q
```

---

## CHANGELOG entry for v1.5.0

```markdown
## [1.5.0] - 2026-06-XX

**IIF v1.5 Expert/Skill Restructure:** Aligns Expert layer with IIF v1.5 
nomenclature. Two named Expert surfaces (Policy, Playbook) are the architectural 
primitives. Governance, Evidence, and Investigation capabilities move to a new 
`jazzx_sdk/skills/` layer as Skill bundles.

### Added
- `jazzx_sdk/skills/` — Platform Skill bundle layer (IIF v1.5 Skill Architecture)
  - `skills/governance/` — Governor-mode action class implementations (BaseGovernanceSkill)
  - `skills/evidence/` — Verifier-mode action class implementations (BaseEvidenceSkill)
  - `skills/investigation/` — Investigator-mode action class implementations (BaseInvestigationSkill)
- `OutputClassification` enum on `ExpertResponse` (IIF v1.5 MSC §7.5)

### Changed
- `EXPERT_REGISTRY` trimmed from 6 to 3 entries: policy, playbook, discovery
- JACI Expert subclasses updated to extend Skill bundles

### Removed
- `jazzx_sdk/experts/governance/` — content migrated to `jazzx_sdk/skills/governance/`
- `jazzx_sdk/experts/evidence/` — content migrated to `jazzx_sdk/skills/evidence/`
- `jazzx_sdk/experts/investigative/` — content migrated to `jazzx_sdk/skills/investigation/`

### Deprecated
- `BaseGovernanceExpert`, `BaseEvidenceExpert`, `BaseInvestigativeExpert` names —
  shim available until v1.6; update imports to `jazzx_sdk.skills.*`

### Migration
Old: `from jazzx_sdk.experts.governance import BaseGovernanceExpert`
New: `from jazzx_sdk.skills.governance import BaseGovernanceSkill`
```
