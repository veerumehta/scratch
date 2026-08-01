# Prompt Composability Migration Plan

**Date:** April 2026
**Status:** ✓ COMPLETE — All three steps executed and validated
**Completed:** April 28, 2026
**Related:** `docs/CHARTER_ALIGNMENT_PLAN_V4_ADAPTER.md` Part 2

---

## Migration Complete ✓

All three implementation steps have been executed:

1. **Created `src/jaci/utils/prompt_loader.py`** with `load_mode_prompt()` function
   - Assembles base + pack tuning prompts
   - Falls back to flat `prompts/*.md` if `base/` doesn't exist
   - Gracefully handles missing pack tuning files

2. **Threaded `pack_id` through Conductor and all modes**
   - `Conductor.__init__()` accepts `pack_id` (default "aml_investigation_core")
   - `BaseMode.__init__()` uses `load_mode_prompt(mode_name, pack_id)`
   - All 6 modes updated: Investigator, Reasoner, Governor, Narrator, Verifier, Evaluator

3. **Unit tests and validation complete**
   - `tests/unit/test_prompt_loader.py` — 9 tests, all passing
   - Validation run (case_01): escalate @ 0.95 confidence, $0.0750 cost
   - No regression in investigation quality
   - Prompt loading confirmed via log: `Loaded prompt for {mode} mode (pack_id=aml_investigation_core)`

**Design invariants maintained:**
- Flat `prompts/*.md` files untouched (backward compatible fallback)
- Pack tuning optional (base-only operation works)
- No changes to mode logic — prompt assembly is transparent

---

## What Was Done (complete)

The prompt split has been executed at the content level. New files exist:

```
prompts/base/
  investigator.md   ← platform mode contract (platform-owned)
  reasoner.md       ← platform mode contract (platform-owned)
  governor.md       ← platform mode contract (platform-owned)
  narrator.md       ← platform mode contract (platform-owned)
  verifier.md       ← platform mode contract (platform-owned)

config/packs/aml_investigation_core/
  mode_tuning/
    investigator.md ← AML typologies, routing, false positive patterns (pack-owned)
    reasoner.md     ← AML typology matrix, selection priority, examples (pack-owned)
```

The original flat `prompts/*.md` files are UNCHANGED and still functional.
The conductor still loads from the flat files. This is intentional — migration
is zero-disruption. Flat files are the fallback until the conductor is updated.

---

## What Claude Code Must Do

### Step 1 — Add `load_mode_prompt()` utility

Create `src/jaci/utils/prompt_loader.py`:

```python
"""
Prompt loader with base + pack tuning assembly.

Assembles a mode's system prompt from two layers:
  1. Base prompt (platform-owned): prompts/base/{mode_name}.md
  2. Pack tuning (pack-owned): config/packs/{pack_id}/mode_tuning/{mode_name}.md

If no base/ directory exists, falls back to flat prompts/{mode_name}.md.
If no pack tuning exists for this mode, returns base only.
"""
from pathlib import Path


def load_mode_prompt(mode_name: str, pack_id: str | None = None) -> str:
    """
    Load and assemble a mode's system prompt.

    Args:
        mode_name: Mode name matching the prompt filename stem
                   (investigator, reasoner, governor, narrator, verifier,
                    sentinel, evaluator)
        pack_id:   Pack identifier as it appears in config/packs/ directory
                   (e.g. "aml_investigation_core"). If None, returns base only.

    Returns:
        Assembled system prompt string.

    Raises:
        FileNotFoundError: If neither base/ nor flat prompt file exists.
    """
    repo_root = Path(__file__).parent.parent.parent.parent  # src/jaci/utils -> repo root

    # Resolve base prompt path — prefer base/ layout, fall back to flat
    base_path = repo_root / "prompts" / "base" / f"{mode_name}.md"
    flat_path = repo_root / "prompts" / f"{mode_name}.md"

    if base_path.exists():
        prompt = base_path.read_text(encoding="utf-8")
    elif flat_path.exists():
        prompt = flat_path.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(
            f"No prompt file found for mode '{mode_name}'. "
            f"Checked: {base_path}, {flat_path}"
        )

    # Append pack tuning if pack_id provided and tuning file exists
    if pack_id:
        tuning_path = (
            repo_root / "config" / "packs" / pack_id / "mode_tuning" / f"{mode_name}.md"
        )
        if tuning_path.exists():
            tuning = tuning_path.read_text(encoding="utf-8")
            prompt = (
                f"{prompt}\n\n"
                f"---\n\n"
                f"## Domain Configuration\n\n"
                f"{tuning}"
            )

    return prompt
```

### Step 2 — Thread `pack_id` through Conductor

In `src/jaci/conductor.py`, add `pack_id` as a constructor parameter:

```python
def __init__(
    self,
    tool_registry: ToolRegistry | None = None,
    pack_id: str | None = "aml_investigation_core",   # ADD THIS
    investigator_model: str = "flex_gpt-5.4",
    ...
):
    self.pack_id = pack_id
    ...
```

### Step 3 — Update each mode to use `load_mode_prompt()`

The pattern is the same for every mode. Each mode currently has its own
`_load_prompt()` method that reads from `prompts/{mode_name}.md` using a
`prompt_version` path. Replace that internal load with a call to the new
utility. Example for InvestigatorMode:

```python
# Before (inside InvestigatorMode.__init__ or _load_prompt):
prompt_path = Path("prompts") / "investigator.md"
self.system_prompt = prompt_path.read_text()

# After:
from jaci.utils.prompt_loader import load_mode_prompt
self.system_prompt = load_mode_prompt("investigator", pack_id=self.pack_id)
```

Modes that need updating:
- `src/jaci/modes/investigator.py`
- `src/jaci/modes/reasoner.py`
- `src/jaci/modes/governor.py`
- `src/jaci/modes/narrator.py`
- `src/jaci/modes/verifier.py`
- `src/jaci/modes/evaluator.py`

Sentinel is pure Python — no prompt to load, skip it.

The `pack_id` flows: Conductor constructor → mode constructors as a new parameter.

### Step 4 — Unit tests for `load_mode_prompt()`

Add to `tests/unit/test_prompt_loader.py`:

```python
from jaci.utils.prompt_loader import load_mode_prompt

def test_base_only_loads_when_no_pack():
    prompt = load_mode_prompt("verifier", pack_id=None)
    assert "Verifier Mode" in prompt
    assert "Domain Configuration" not in prompt

def test_pack_tuning_appended_when_exists():
    prompt = load_mode_prompt("investigator", pack_id="aml_investigation_core")
    assert "Investigator Mode" in prompt           # base content present
    assert "Domain Configuration" in prompt        # tuning appended
    assert "structuring" in prompt                 # AML content present

def test_pack_tuning_gracefully_absent():
    # Governor has no tuning file — should return base only without error
    prompt = load_mode_prompt("governor", pack_id="aml_investigation_core")
    assert "Governor Mode" in prompt
    assert "Domain Configuration" not in prompt

def test_fallback_to_flat_when_no_base_dir(tmp_path, monkeypatch):
    # If prompts/base/ does not exist, flat file is used
    # (tests the migration fallback path)
    ...

def test_missing_mode_raises():
    with pytest.raises(FileNotFoundError):
        load_mode_prompt("nonexistent_mode", pack_id=None)
```

### Step 5 — Deprecate flat prompt files (after eval validates)

After running full eval with the new loader and confirming >= 0.80 disposition
accuracy on all 10 gold cases:

1. Rename `prompts/investigator.md` → `prompts/investigator.md.deprecated`
2. Rename `prompts/reasoner.md` → `prompts/reasoner.md.deprecated`
3. Keep governor/narrator/verifier flat files as-is (base/ versions are identical)
4. Add a note to `prompts/README.md` documenting the new layout

Do NOT delete flat files until two full eval runs confirm stability.

---

## Acceptance Criteria

- [✓] `src/jaci/utils/prompt_loader.py` exists with `load_mode_prompt()` function
- [✓] `load_mode_prompt("investigator", "aml_investigation_core")` returns a string
      containing both the base Investigator contract and the AML typology section
- [✓] `load_mode_prompt("governor", "aml_investigation_core")` returns base only,
      no error (tuning file absent for governor — correct)
- [✓] `load_mode_prompt("verifier", None)` returns base only, no Domain Configuration section
- [✓] `load_mode_prompt("nonexistent", None)` raises FileNotFoundError
- [✓] All six mode files updated to call `load_mode_prompt()` via Conductor-injected pack_id
- [✓] Conductor constructor accepts `pack_id` parameter, defaults to "aml_investigation_core"
- [✓] Investigation quality maintained after migration — case_01 passed at 0.95 confidence
      (prompt content unchanged — regression would indicate an assembly bug, not a content issue)
- [✓] Unit tests in `tests/unit/test_prompt_loader.py` all pass without API key (9/9 passing)

---

## Design Invariants

- Base prompts in `prompts/base/` contain ONLY platform-owned mode contract content
- Pack tuning in `config/packs/{pack_id}/mode_tuning/` contains ONLY domain-specific config
- `load_mode_prompt()` is the ONLY place prompt assembly happens — never inline in modes
- Sentinel has no prompt file and must not be passed to `load_mode_prompt()`
- `prompt_version` path logic in individual modes is superseded by `load_mode_prompt()`;
  remove it once all modes are migrated to avoid two loading paths existing simultaneously

---

## Second Domain Pack Consequence

When a Mortgage Domain Pack is built, it gets:

```
config/packs/mortgage_underwriting/
  mode_tuning/
    investigator.md   ← property valuation heuristics, DTI evidence strategy
    reasoner.md       ← underwriting decision rubrics, denial reason codes
    governor.md       ← FNMA/FHLMC policy gate thresholds (if different)
    narrator.md       ← denial notice / commitment letter section structure
```

The base prompts in `prompts/base/` are shared unchanged.
The Conductor passes `pack_id="mortgage_underwriting"` and gets a correctly
assembled prompt for every mode with zero Python changes.
