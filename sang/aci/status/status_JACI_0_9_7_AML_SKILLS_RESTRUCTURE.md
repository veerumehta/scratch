# plan_JACI_0_9_7_AML_SKILLS_RESTRUCTURE.md

**Author:** Virendra Mehta  
**Repo:** `jaci/`  
**Status:** Ready for Claude Code execution  

---

## Objective

IIF v1.5 formalizes a 3-Expert platform (Policy, Playbook, Discovery). Governance,
Evidence, and Investigation are Skills - action-class implementations that domain
packs subclass. The JAPES SDK (`jazzx_sdk`) already reflects this: `catalog.py`
has 3 Expert contracts, and `skills/` provides `BaseGovernanceSkill`,
`BaseEvidenceSkill`, `BaseInvestigationSkill`.

JACI AML at v0.9.6 is structurally correct in behavior (the conductor only registers
PolicyExpert and PlaybookExpert) but the file layout is wrong: all five classes live
in `scenarios/aml/experts/`, mixing two actual Expert surfaces with three Skills.
The module name implies they are all Experts, which conflicts with v1.5.

This plan restructures the AML pack to match v1.5's distinction cleanly.

---

## What Changes

### 1. New directory: `scenarios/aml/skills/`

Move the three Skill files out of `experts/` into a new `skills/` directory:

```
scenarios/aml/skills/
    __init__.py
    evidence.py       # was experts/evidence.py (AMLEvidenceExpert -> AMLEvidenceSkill)
    governance.py     # was experts/governance.py (AMLGovernanceExpert -> AMLGovernanceSkill)
    investigation.py  # was experts/investigative.py (AMLInvestigativeExpert -> AMLInvestigativeSkill)
```

### 2. Rename classes

| Old name | New name | Base class | Lives in |
|---|---|---|---|
| `AMLEvidenceExpert` | `AMLEvidenceSkill` | `BaseEvidenceSkill` | `skills/evidence.py` |
| `AMLGovernanceExpert` | `AMLGovernanceSkill` | `BaseGovernanceSkill` | `skills/governance.py` |
| `AMLInvestigativeExpert` | `AMLInvestigativeSkill` | `BaseInvestigationSkill` | `skills/investigation.py` |
| `AMLPolicyExpert` | unchanged | `BasePolicyExpert` | `experts/policy.py` |
| `AMLPlaybookExpert` | unchanged | `DefaultPlaybookExpert` | `experts/playbook.py` |

### 3. Update `experts/__init__.py`

Only export the two Expert surfaces:

```python
from jaci.scenarios.aml.experts.policy import AMLPolicyExpert
from jaci.scenarios.aml.experts.playbook import AMLPlaybookExpert

__all__ = ["AMLPolicyExpert", "AMLPlaybookExpert"]
```

### 4. New `skills/__init__.py`

```python
from jaci.scenarios.aml.skills.evidence import AMLEvidenceSkill
from jaci.scenarios.aml.skills.governance import AMLGovernanceSkill
from jaci.scenarios.aml.skills.investigation import AMLInvestigativeSkill

__all__ = ["AMLEvidenceSkill", "AMLGovernanceSkill", "AMLInvestigativeSkill"]
```

### 5. Update conductor.py

`_register_aml_pack_experts()` already only registers Policy and Playbook - no
change needed there. Update the log message from "5 AML Experts" to "2 AML Expert
surfaces":

```python
# In _register_aml_pack_experts():
logger.info(
    f"ExpertRegistry initialized with 2 AML Expert surfaces for pack_id={self.pack_id}"
)
```

The conductor's mode calls are already direct (`self.investigator`, `self.verifier`,
etc.) - the `AMLInvestigativeSkill` wrapper is not used by the conductor. No
conductor logic changes required.

### 6. Update `scenarios/aml/__init__.py` if it re-exports

Check for any re-exports and update paths.

### 7. Update test files

Four test files reference the old Expert class names:

| Test file | Old import | New import |
|---|---|---|
| `tests/unit/test_aml_evidence_expert.py` | `AMLEvidenceExpert` | `AMLEvidenceSkill` from `jaci.scenarios.aml.skills` |
| `tests/unit/test_aml_governance_expert.py` | `AMLGovernanceExpert` | `AMLGovernanceSkill` from `jaci.scenarios.aml.skills` |
| `tests/unit/test_aml_investigative_expert.py` | `AMLInvestigativeExpert` | `AMLInvestigativeSkill` from `jaci.scenarios.aml.skills` |
| `tests/unit/test_aml_policy_expert.py` | `AMLPolicyExpert` | `AMLPolicyExpert` from `jaci.scenarios.aml.experts` (unchanged) |
| `tests/unit/test_aml_playbook_expert.py` | `AMLPlaybookExpert` | `AMLPlaybookExpert` from `jaci.scenarios.aml.experts` (unchanged) |

Rename test files to match:
- `test_aml_evidence_expert.py` -> `test_aml_evidence_skill.py`
- `test_aml_governance_expert.py` -> `test_aml_governance_skill.py`
- `test_aml_investigative_expert.py` -> `test_aml_investigative_skill.py`

### 8. Search and replace across repo

Run a broad search for `AMLEvidenceExpert`, `AMLGovernanceExpert`, `AMLInvestigativeExpert`
across the full repo and update all references:

```bash
grep -r "AMLEvidenceExpert\|AMLGovernanceExpert\|AMLInvestigativeExpert" \
    src/ tests/ --include="*.py" -l
```

---

## What Does NOT Change

- All class logic, method implementations, and docstrings stay identical
  (this is a rename + relocate, not a rewrite)
- The conductor investigation loop is unchanged
- `AMLPolicyExpert` and `AMLPlaybookExpert` stay in `experts/` with their
  current implementations
- The JAPES SDK is not touched
- Eval gold cases and the eval harness are unchanged
- The 80% eval baseline is not at risk - no mode, prompt, or
  tool logic changes

---

## Acceptance Checks

```bash
# 1. Skills live in the right place
ls src/jaci/scenarios/aml/skills/
# -> evidence.py  governance.py  investigation.py  __init__.py

# 2. Experts directory has only Expert surfaces
ls src/jaci/scenarios/aml/experts/
# -> __init__.py  policy.py  playbook.py  (no evidence.py, governance.py, investigative.py)

# 3. Class names updated
grep -r "AMLEvidenceExpert\|AMLGovernanceExpert\|AMLInvestigativeExpert" \
    src/ tests/ --include="*.py"
# -> no results

# 4. New names present
grep -r "AMLEvidenceSkill\|AMLGovernanceSkill\|AMLInvestigativeSkill" \
    src/ tests/ --include="*.py"
# -> results in skills/ and test files only

# 5. Version sync test passes
pytest tests/test_version_sync.py -v

# 6. Full test suite passes (guards eval baseline)
pytest tests/ -v --tb=short
```

---

## Notes for Claude Code

- Do NOT delete the old expert files until all imports are updated and tests pass
- Move files, update class names inside them, update all imports, then delete originals
- The `AMLInvestigativeSkill` (formerly `AMLInvestigativeExpert`) wraps the conductor
  and is primarily used by tests and external integrations, not by the conductor itself -
  leave its internal logic intact
- If `scenarios/aml/__init__.py` imports from `experts/`, update those imports too
- Check `app.py` and any demo scripts at the repo root for Expert imports
