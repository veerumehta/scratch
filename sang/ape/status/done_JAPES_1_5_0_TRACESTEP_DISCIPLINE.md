# JAPES v1.5.0 - TraceStep Discipline
## Claude Code Handoff (updated)

**Author:** Virendra Mehta  
**Branch:** v1.5  
**Repo:** `japes/` only  
**IIF v1.5 reference:** IPDV §11, ADM D6/D25, Versioning Spec §5

---

## Current state (post v1.4.3 + v1.5.0 Expert/Skill restructure)

- `jazzx_sdk/fabric/canonical/trace.py` - TraceStep and CanonicalTrace exist with v1.0 fields
- Version bundle fields (`schema_version`, `model_version`, `prompt_version`, `policy_bundle_version`,
  `connector_config_version`, `evaluation_suite_version`, `overlay_version`) are still ON TraceStep -
  correct for v1.0; must move to `Trace.metadata` for v1.5
- `TraceStepMode` enum has three wrong values: `EXPLAINER`, `DOCUMENTER`, `SCOUT` are not canonical
  mode names - must be corrected to the 13 IIF Charter modes
- `jazzx_sdk/experts/__init__.py` re-exports Skills from `jazzx_sdk.skills` - remove these;
  these are breaking changes, callers update imports directly, no compat shims needed

Three changes in this handoff: move version bundle off TraceStep, fix mode enum, remove Skills
re-exports from experts layer.

---

## Change 1 - Move version bundle fields off TraceStep

### Why

Per IIF v1.5 (IPDV §11, ADM D6/D25): version bundle fields do NOT live on TraceStep in v1.5.
They go on `Trace.metadata` with `step_id` correlation. TraceStep is frozen at the v1.0 locked
schema - adding per-step version context to TraceStep directly is the most common v1.5 failure mode.

### What to remove from TraceStep

In `jazzx_sdk/fabric/canonical/trace.py`, remove these fields from the `TraceStep` model:

```python
# REMOVE from TraceStep:
schema_version: str          # Required in v1.0 - moves to Trace.metadata in v1.5
model_version: str | None    # Optional in v1.0 - moves to Trace.metadata in v1.5
prompt_version: str | None
policy_bundle_version: str | None
connector_config_version: str | None
evaluation_suite_version: str | None
overlay_version: str | None
```

Also add `extra = "forbid"` to TraceStep's model Config if not already present - this
catches accidental field additions at runtime.

### What to add to CanonicalTrace

`Trace.metadata` already exists. Add a docstring convention and a helper. In the
`CanonicalTrace` class docstring, add:

```
Per-step version bundle convention:
    trace.metadata[f"step_{step_id}_version_bundle"] = {
        "schema_version": "1.5.0",
        "model_version": "gpt-5.4",
        "prompt_version": "aml-investigator-v1.2",
        "policy_bundle_version": "bsa-sar-2026-03",
        "overlay_version": "chb-aml-overlay-v1.1",  # when overlay is in force
    }
```

### Add TraceStepContextHelper

Add this helper class to `trace.py` (after the model definitions):

```python
class TraceStepContextHelper:
    """
    Helper for attaching per-step context to Trace.metadata.
    Enforces the step_id correlation convention.
    """
    def __init__(self, trace: CanonicalTrace):
        self._trace = trace

    def set_version_bundle(self, step_id: str, **kwargs) -> None:
        """Attach version bundle to a step via Trace.metadata."""
        self._trace.metadata[f"step_{step_id}_version_bundle"] = kwargs

    def set_ipdv_context(self, step_id: str, actor_role: str,
                         effective_rights: list[str], autonomy_resolved: int) -> None:
        """Attach IPDV runtime context to a step via Trace.metadata."""
        self._trace.metadata[f"step_{step_id}_ipdv"] = {
            "actor_role": actor_role,
            "effective_rights": effective_rights,
            "autonomy_resolved": autonomy_resolved,
        }

    def set_domain_context(self, step_id: str, pack_id: str, **kwargs) -> None:
        """Attach Pack-specific per-step state via Trace.metadata."""
        self._trace.metadata[f"step_{step_id}_{pack_id}"] = kwargs

    def get_step_context(self, step_id: str) -> dict[str, Any]:
        """Retrieve all metadata entries for a given step_id."""
        prefix = f"step_{step_id}_"
        return {k[len(prefix):]: v
                for k, v in self._trace.metadata.items()
                if k.startswith(prefix)}
```

Export `TraceStepContextHelper` from `jazzx_sdk/fabric/canonical/__init__.py`.

---

## Change 2 - Fix TraceStepMode enum

The current `TraceStepMode` enum has `EXPLAINER`, `DOCUMENTER`, `SCOUT` which are not
IIF Charter cognitive mode names. Replace the entire enum with the canonical 13:

```python
class TraceStepMode(str, Enum):
    """13 canonical cognitive modes per IIF Charter §Architecture."""
    # THINK
    REASONER = "reasoner"
    INVESTIGATOR = "investigator"
    SIMULATOR = "simulator"
    # TRUST
    GOVERNOR = "governor"
    VERIFIER = "verifier"
    SENTINEL = "sentinel"
    # EXECUTE
    CONDUCTOR = "conductor"
    OPTIMIZER = "optimizer"
    # INTERACT
    NARRATOR = "narrator"
    INFLUENCER = "influencer"
    NEGOTIATOR = "negotiator"
    # EVOLVE
    EVALUATOR = "evaluator"
    CURATOR = "curator"
```

This is a breaking change. Any TraceStep emitted with `mode=TraceStepMode.EXPLAINER` etc.
will fail validation after this change. Search the codebase for usage:

```bash
grep -r "EXPLAINER\|DOCUMENTER\|SCOUT" /Users/foo/src/research/sangit/japes/
grep -r "EXPLAINER\|DOCUMENTER\|SCOUT" /Users/foo/src/research/sangit/jaci/
```

Replace any matches with the correct canonical mode name.

---

## Change 3 - Remove Skills re-exports from experts/__init__.py

In `jazzx_sdk/experts/__init__.py`, remove the Skills convenience re-export block:

```python
# REMOVE this entire block:
from jazzx_sdk.skills import (
    BaseGovernanceSkill,
    EnforcementResult,
    CeilingResult,
    OverrideRecord,
    AuditPackage,
    BaseEvidenceSkill,
    EvidenceCollectionResult,
    VerificationReport,
    SufficiencyReport,
    FreshnessReport,
    ContradictionReport,
    BaseInvestigationSkill,
    InvestigationResult,
    NarrativeResult,
    PatternRecognitionResult,
    BenchmarkReport,
)
```

Also remove the corresponding entries from `__all__`.

Domain Packs import Skills directly from `jazzx_sdk.skills`:
```python
# Correct import path after this change:
from jazzx_sdk.skills.governance import BaseGovernanceSkill, EnforcementResult
from jazzx_sdk.skills.evidence import BaseEvidenceSkill, VerificationReport
from jazzx_sdk.skills.investigation import BaseInvestigationSkill, InvestigationResult
```

---

## What does NOT change

- TraceStep required fields: step_id, sequence, mode, action, inputs, outputs,
  started_at, completed_at, status, actor, autonomy_level - all stay
- TraceStep optional fields: tools_invoked, iteration, duration_ms, notes - all stay
- CanonicalTrace structure - no changes beyond adding TraceStepContextHelper
- JACI imports of Skills (already updated to `jazzx_sdk.skills.*` in v1.5.0)
- All mode implementations, fabric stores, canonical object models

---

## Acceptance checks

```bash
cd /Users/foo/src/research/sangit/japes

# 1. Version bundle fields are gone from TraceStep
python -c "
from jazzx_sdk.fabric.canonical.trace import TraceStep
forbidden = {'schema_version','model_version','prompt_version',
             'policy_bundle_version','connector_config_version',
             'evaluation_suite_version','overlay_version'}
present = forbidden & set(TraceStep.model_fields.keys())
assert not present, f'Version bundle fields still on TraceStep: {present}'
print('OK: Version bundle fields removed from TraceStep')
"

# 2. TraceStep rejects extra fields
python -c "
from jazzx_sdk.fabric.canonical.trace import TraceStep, TraceStepMode, ActorRef
from datetime import datetime
try:
    TraceStep(sequence=0, mode=TraceStepMode.GOVERNOR, action='test',
              actor=ActorRef(actor_id='x', actor_type='assistant'),
              autonomy_level=1, started_at=datetime.utcnow(),
              completed_at=datetime.utcnow(), status='completed',
              schema_version='1.5.0')
    print('FAIL: Should have rejected schema_version')
except Exception:
    print('OK: TraceStep rejects version bundle field')
"

# 3. TraceStepMode has exactly the 13 canonical modes
python -c "
from jazzx_sdk.fabric.canonical.trace import TraceStepMode
expected = {'reasoner','investigator','simulator','governor','verifier',
            'sentinel','conductor','optimizer','narrator','influencer',
            'negotiator','evaluator','curator'}
actual = {m.value for m in TraceStepMode}
assert actual == expected, f'Mode mismatch. Extra: {actual-expected}, Missing: {expected-actual}'
print('OK: TraceStepMode has exactly 13 canonical modes')
"

# 4. TraceStepContextHelper sets and retrieves per-step context
python -c "
from jazzx_sdk.fabric.canonical.trace import CanonicalTrace, TraceStepContextHelper
trace = CanonicalTrace(pack_id='test', pack_version='1.5.0',
                       workflow_id='test', case_id='case_1',
                       status='running', started_at=__import__('datetime').datetime.utcnow())
ctx = TraceStepContextHelper(trace)
ctx.set_version_bundle('step_abc', schema_version='1.5.0', model_version='gpt-5.4')
result = ctx.get_step_context('step_abc')
assert result['version_bundle']['schema_version'] == '1.5.0'
print('OK: TraceStepContextHelper stores and retrieves per-step context')
"

# 5. Skills are NOT importable from jazzx_sdk.experts
python -c "
try:
    from jazzx_sdk.experts import BaseGovernanceSkill
    print('FAIL: Skills still re-exported from experts')
except ImportError:
    print('OK: Skills not re-exported from experts')
"

# 6. Skills still importable from jazzx_sdk.skills
python -c "
from jazzx_sdk.skills.governance import BaseGovernanceSkill
from jazzx_sdk.skills.evidence import BaseEvidenceSkill
from jazzx_sdk.skills.investigation import BaseInvestigationSkill
print('OK: Skills importable from jazzx_sdk.skills')
"

# 7. No EXPLAINER/DOCUMENTER/SCOUT in codebase
grep -r "EXPLAINER\|DOCUMENTER\|SCOUT" \
    /Users/foo/src/research/sangit/japes/jazzx_sdk/ \
    /Users/foo/src/research/sangit/jaci/src/ 2>/dev/null \
    && echo "FAIL: Old mode names found" || echo "OK: No old mode names"

# 8. Full test suite passes
python -m pytest tests/ -x -q 2>&1 | tail -5
```

---

## CHANGELOG addition for v1.5.0

```markdown
### Changed (continued)

- `TraceStep` — version bundle fields removed (schema_version, model_version,
  prompt_version, policy_bundle_version, connector_config_version,
  evaluation_suite_version, overlay_version); use Trace.metadata with step_id
  correlation instead (IIF v1.5 IPDV §11 / ADM D6/D25)
- `TraceStep.extra = "forbid"` — rejects accidental field additions at runtime
- `TraceStepMode` — corrected to 13 canonical IIF Charter modes; removed
  EXPLAINER, DOCUMENTER, SCOUT; added SIMULATOR, OPTIMIZER, INFLUENCER, NEGOTIATOR

### Added
- `TraceStepContextHelper` — helper for attaching per-step context to
  Trace.metadata using the step_id correlation convention

### Removed
- Skills re-exports from `jazzx_sdk/experts/__init__.py` — import Skills
  directly from `jazzx_sdk.skills.*`
```
