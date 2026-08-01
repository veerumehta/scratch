# Charter Alignment — v4 Addendum: Agent Framework & Prompt Composability

**For: Claude Code execution**
**Date: April 2026**
**Applies after:** v2 plan + v3 patch. Read those first. Where this conflicts, this takes precedence.

Two related design questions are resolved here:
1. The apparent tension between JACI-AML's single-runtime choice and the v2.0 platform's multi-runtime claim.
2. Whether prompts should be composable `.md` files or per-domain `.py` files.

---

## Part 1: Agent Framework — Per-Vertical Single Runtime is Correct

The JazzX v2.0 Adapter Layer is a **platform-level capability**. A Domain Pack
choosing one agent runtime for its vertical is correct and intentional — the Pack
picks one; the platform supports many. JACI-AML using the OpenAI Agents SDK
(flex_gpt-5.4 at 80% disposition accuracy) does not contradict v2.0 slide 22.

**Do not add multi-SDK abstraction during Phases 7–10.**

### The real question: downstream customer interop

A bank deploying JACI-AML may have enterprise Anthropic access. The question is
whether this requires a code variant or whether the API surface handles it.

**What is transparent — no variant needed:**
- All six mode prompts in `prompts/` are model-agnostic text instructions.
- Pydantic output contracts (`DispositionRecommendation`, `CaseFile`, etc.) are model-agnostic.
- Evidence tools, `ToolRegistry`, and eval harness are model-agnostic.
- `reasoner_anthropic.py` already demonstrates the swap: different SDK client,
  same prompt file, same Pydantic output schema.

**The seam that needs attention — three items:**

1. **Structured output enforcement.** OpenAI Agents SDK enforces `response_format`
   JSON schema natively. Anthropic SDK requires prompt-level instruction plus
   explicit response parsing. Only `reasoner_anthropic.py` handles this; the other
   five modes do not yet have Anthropic variants.

2. **Tool call wire format.** `ToolRegistry` emits OpenAI-format tool definitions.
   An Anthropic customer path needs Anthropic-format definitions or a thin adapter
   in `jaci_handler.py`.

3. **SDK client injection.** Modes currently construct their own SDK clients.
   A clean customer path requires injectable clients (passed in, not constructed
   inside each mode).

### Three options

**Option A — Prompt-only abstraction (active, PoC, no new code)**
Stay on OpenAI Agents SDK. `prompts/` files are model-agnostic; customer adapts
SDK glue themselves. Correct for PoC phase.

**Option B — SDK adapter pattern (backlog, pre-OEM/customer delivery, ~1 day)**
Extend `reasoner_anthropic.py` pattern to all six modes. Each mode receives an
injected client. Prompt files remain shared. Pydantic schemas remain shared.
`conductor.py` takes `sdk: Literal["openai", "anthropic"]` from `config/settings.py`.

New files when Option B executes:
```
src/jaci/modes/investigator_anthropic.py
src/jaci/modes/verifier_anthropic.py
src/jaci/modes/governor_anthropic.py
src/jaci/modes/narrator_anthropic.py
```

Targeted amendments when Option B executes:
```
config/settings.py          Add sdk: Literal["openai", "anthropic"] setting
src/jaci/conductor.py       Read sdk setting; inject client into mode constructors
src/jaci/tools/registry.py  Tool definition format selected by sdk setting
```

Acceptance criteria for Option B:
- All 10 gold cases pass at >=0.80 disposition accuracy on both sdk=openai and sdk=anthropic
- No mode constructs its own SDK client
- Prompt files in prompts/ unchanged — both SDK paths use the same prompts
- ToolRegistry emits correctly formatted definitions for the configured SDK

**Option C — JAPES adapter registration (deferred, production readiness, ~2-3 days)**
Formal adapter contract in `jaci_handler.py`. Correct long-term JazzX pattern.
Depends on JAPES adapter spec being finalized on the platform side.

### Current decision

| Option | Status |
|--------|--------|
| Option A | **Active — Phases 7–10** |
| Option B | **Backlog — after Phase 9, before any OEM/customer code handoff** |
| Option C | **Deferred — production readiness** |

### Hard constraints

- Do NOT introduce multi-SDK mode abstraction during Phases 7–10.
- Anthropic variants follow `reasoner_anthropic.py` exactly: new file, shared prompt,
  shared schema, no Conductor changes.
- `reasoner_anthropic.py` must not be wired into Conductor until Option B executes.

### Pack yaml annotation (add in Phase 10)

```yaml
runtime:
  primary_sdk: openai_agents
  # Per-vertical single-runtime choice is correct — v2.0 Adapter Layer is platform capability.
  anthropic_variant_status: partial
  # reasoner_anthropic.py exists as eval artifact; other modes pending Option B.
  multi_sdk_readiness: option_b_pending
  # Option B design: docs/CHARTER_ALIGNMENT_PLAN_V4_ADAPTER.md Part 1
```

---

## Part 2: Prompt Composability — Two-Layer Structure Required

### What the Charter says

Domain Pack component 6 is **"Cognitive Mode Tuning (All 13)"** — per-mode charter,
I/O schemas, tool permissions, autonomy ranges, reasoning strategies, handoff
contracts, and evaluation rubrics. This is explicitly **pack-owned content**,
versioned alongside the pack. The modes themselves (Investigator, Verifier, etc.)
are **platform-owned**. The AML-specific tuning of those modes is **pack-owned**.

The current `prompts/*.md` files violate this boundary — they combine the
platform-owned mode contract with pack-owned AML-specific content in a single file.
This is a PoC shortcut that must be resolved before a second Domain Pack is built.

### Target structure

```
prompts/
  base/
    investigator.md     # platform-owned: mode contract, cognitive invariants,
                        # output schema, handoff protocol, what this mode never does
    verifier.md
    reasoner.md
    governor.md
    narrator.md
    sentinel.md
    evaluator.md        # added in Phase 8

config/packs/
  aml_investigation_core/
    mode_tuning/
      investigator.md   # pack-owned: AML typologies, evidence strategy, thresholds,
                        # hypothesis generation guidance, convergence criteria
      reasoner.md       # pack-owned: AML decision rubrics, confidence calibration,
                        # false positive patterns, typology differentiation matrix
      governor.md       # pack-owned: BSA/FinCEN clause namespaces, policy gate rules
      narrator.md       # pack-owned: SAR section templates, citation requirements,
                        # 15-day deadline context, regulatory artifact standards
      evaluator.md      # pack-owned: AML-specific quality rubric, signal taxonomy
```

At runtime, the Conductor assembles each mode's system prompt:

```python
def load_mode_prompt(mode_name: str, pack_id: str) -> str:
    base = Path(f"prompts/base/{mode_name}.md").read_text()
    tuning_path = Path(f"config/packs/{pack_id}/mode_tuning/{mode_name}.md")
    if tuning_path.exists():
        tuning = tuning_path.read_text()
        return f"{base}\n\n---\n\n## Domain-Specific Tuning\n\n{tuning}"
    return base
```

### Why not .py per domain

`.py` per domain conflates two separate concerns: SDK implementation and domain
knowledge. Changing a SAR narrative rubric should not require touching Python code.
Swapping SDK clients should not require touching domain logic. The prompt content
always lives in `.md` files — Python loads it, it doesn't contain it.

`reasoner_anthropic.py` is correctly named: it is an SDK variant, not a domain
variant. It loads the same `prompts/base/reasoner.md` and the same
`config/packs/aml_investigation_core/mode_tuning/reasoner.md`. The Python file
only changes how the LLM call is made and how the output is parsed.

### What to split from the current prompts

Current `prompts/investigator.md` contains both layers mixed together. The split:

**Goes to `prompts/base/investigator.md` (platform-owned):**
- What the Investigator mode is and does
- Output schema (HypothesisUpdate with required fields)
- Cognitive invariants: never fabricate evidence, always cite evidence_id
- Convergence protocol: when and how to signal convergence
- Handoff contract to Verifier
- What Investigator never does (does not assess guilt, does not draft SAR)

**Goes to `config/packs/aml_investigation_core/mode_tuning/investigator.md` (pack-owned):**
- The four AML typology definitions and differentiation guidance
- Alert-driven typology selection rules
- Evidence request strategy for AML (core → corroborating → policy order)
- AML-specific convergence criteria (minimum evidence types, confidence thresholds)
- Confidence calibration guidance for AML cases

Same split applies to reasoner.md, governor.md, narrator.md.

### Composability consequence for the second Domain Pack

When a Mortgage Domain Pack is built, it gets:
- `config/packs/mortgage_underwriting/mode_tuning/investigator.md` — mortgage
  evidence strategy, property valuation heuristics, DTI threshold guidance
- `config/packs/mortgage_underwriting/mode_tuning/reasoner.md` — underwriting
  decision rubrics, FNMA/FHLMC policy references, denial reason codes

The base prompts in `prompts/base/` are shared unchanged. The Conductor loads the
right tuning layer based on `pack_id`. No new `.py` files needed per domain.

### Execution timing

Do NOT refactor the current prompts during Phases 7–10. That is scope creep while
the EVOLVE layer is unbuilt.

**Execute the prompt split as part of Phase 10:**
1. Create `prompts/base/` directory
2. Split each current `prompts/*.md` into base + AML tuning layers
3. Create `config/packs/aml_investigation_core/mode_tuning/` directory with the
   AML-specific sections
4. Update `conductor.py` to use `load_mode_prompt(mode_name, pack_id)` instead
   of reading flat prompt files directly
5. Run full eval to confirm no regression (all 10 gold cases, >=0.80 accuracy)

Add to `config/packs/aml_investigation_core.yaml` under `cognitive_mode_tuning`:

```yaml
cognitive_mode_tuning:
  tuning_directory: config/packs/aml_investigation_core/mode_tuning/
  base_prompt_directory: prompts/base/
  assembly: base_then_tuning
  # Conductor loads base prompt, appends pack tuning if present.
  # Base prompt = platform-owned mode contract.
  # Tuning layer = pack-owned domain configuration.
  modes_with_tuning:
    - investigator
    - reasoner
    - governor
    - narrator
    - evaluator
  modes_base_only:
    - verifier    # AML verification logic is general enough to stay in base
    - sentinel    # Pure Python, no LLM prompt
```

### Phase 10 acceptance criteria additions (prompt split)

- `prompts/base/` directory exists with all six mode base prompts
- `config/packs/aml_investigation_core/mode_tuning/` exists with five tuning files
- `load_mode_prompt("investigator", "aml-investigation-core")` returns a string
  containing both the base contract section and the AML typology section
- `load_mode_prompt("investigator", "nonexistent-pack")` returns base prompt only
  (graceful fallback, no error)
- All 10 gold cases pass at >=0.80 disposition accuracy after the split
  (prompt content unchanged, just reorganized)
- `prompts/*.md` flat files are removed or archived after split is validated
