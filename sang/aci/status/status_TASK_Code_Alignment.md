# Code Alignment Tasks: Notion Page Decisions → JAPES + JACI

**Priority:** Medium (terminology and structural alignment, not behavioral changes)
**Repos:** `japes` (jazzx_runtime_sdk) and `jaci` (scenarios)

These tasks bring the codebase in line with architectural decisions documented on the "From Vision to Code" Notion page during the May 21 session.

---

## 1. Conductor Naming (JACI)

**Decision:** Each scenario has a named Conductor. The Conductor is the process definition, not a generic class.

**Status:** Partially done. `kyc_anthropic` already has `KYCAnthropicConductor`. AML scenario may still use generic `Conductor`.

**Task:** Verify all scenarios export a named Conductor as primary entry point:
- `scenarios/aml/` → `AMLConductor`
- `scenarios/kyc/` → `KYCConductor`
- `scenarios/kyc_anthropic/` → `KYCAnthropicConductor` (already done)
- `scenarios/earnings_anthropic/` → `EarningsConductor`

Update `__init__.py` exports, `app.py` scenario selector, and all test imports accordingly.

See `docs/TASK_Conductor_Refactor.md` for full specification.

---

## 2. Skills Terminology (JAPES + JACI)

**Decision:** "Skills" is the term for domain knowledge that makes a mode effective. "Prompts" is deprecated as a concept name. The two-layer system is "platform base layer + domain skill," composed at runtime via context engineering.

**Current state:** Code still uses `prompts/` directories, `prompt_resolver`, `load_mode_prompt()`, `resolve_mode_prompt()`. The JAPES SDK `__init__.py` changelog says "pack-aware prompt resolver."

**Task:** This is a terminology migration, not a behavioral change. Phase it:

Phase A (documentation only, no code changes):
- Update `CLAUDE.md` in both repos to use "skills" terminology
- Update docstrings on `BaseMode`, `prompt_resolver`, `load_mode_prompt` to say "loads the skill content for this mode" rather than "loads the prompt"
- Add a note in `jazzx_runtime_sdk/modes/__init__.py` that `prompt_resolver` is the skill loading mechanism

Phase B (future, when refactoring):
- Consider renaming `prompts/` directories to `skills/` (breaking change, coordinate across scenarios)
- Consider renaming `prompt_resolver` to `skill_resolver` and `load_mode_prompt` to `load_mode_skill`
- These are bigger changes that touch every scenario and should be done in a coordinated pass

**Do Phase A only for now.**

---

## 3. Context Engineering Framing (JAPES)

**Decision:** Modes operate with "context engineering" (platform base + domain skill + runtime evidence/hypotheses/policies/tool results), not just "prompts."

**Current state:** `BaseMode` and `resolve_mode_prompt()` handle the two-layer composition. Runtime context (evidence, hypotheses) is passed as arguments to `mode.run()`. The framing is correct in code but the naming suggests it's just prompt assembly.

**Task:** Update docstrings in JAPES SDK:
- `BaseMode` class docstring: describe the context engineering model (platform base layer + domain skill + runtime context)
- `resolve_mode_prompt()` or equivalent: note that this assembles the skill layers, while runtime context (evidence, hypotheses, tool results) is composed by the Conductor at call time
- `MODE_REGISTRY` entries: add a note that each mode's canonical I/O spec defines what runtime context it expects

No behavioral changes. Documentation/docstring updates only.

---

## 4. PolicyExpert vs GovernanceExpert Boundary (JAPES)

**Decision:** PolicyExpert is a knowledge service ("what do the rules say?"). GovernanceExpert.enforce() is the gate that applies policy to a specific decision via GovernorMode ("does this decision comply?"). PolicyExpert.check_compliance() is advisory. GovernanceExpert.enforce() blocks.

**Current state:** Expert Layer base classes in JAPES v0.5.0 define both. Need to verify docstrings clearly distinguish advisory (PolicyExpert) from enforcement (GovernanceExpert).

**Task:** Update Expert base class docstrings:
- `PolicyExpert`: "Knowledge service. Resolves which policies apply, interprets ambiguity, checks staleness. check_compliance() is advisory, it does not block."
- `GovernanceExpert`: "Enforcement service. enforce() applies policies to a specific decision through GovernorMode. This is the gate with blocking authority."
- `GovernanceExpert.generate_audit_package()`: "Structured assembly of canonical objects into a reviewable artifact. Distinct from Narrator (which generates prose). The audit package may include a Narrator-generated narrative as one component."

---

## 5. PlaybookExpert Scope (JAPES)

**Decision:** PlaybookExpert retrieves and scaffolds from playbooks. It does not execute playbook steps. Execution is the Conductor's job.

**Task:** Update PlaybookExpert base class docstring to clarify: "Retrieves, scaffolds, and measures from versioned playbooks. Does not execute playbook steps. The Conductor determines when and how scaffolded templates are used."

---

## 6. InvestigativeExpert Composition (JAPES + JACI)

**Decision:** InvestigativeExpert composes InvestigatorMode + VerifierMode + ReasonerMode (not "all 6 operational modes"). GovernanceExpert is a dependency, not a composed mode. The Conductor invokes InvestigativeExpert operations as steps, not the other way around.

**Current state:** The AML Conductor directly instantiates all modes and calls them in sequence. InvestigativeExpert exists as a base class but the Conductor doesn't route through it.

**Task:** Update docstrings:
- `InvestigativeExpert` base class: "Composes InvestigatorMode + VerifierMode + ReasonerMode. Dependencies: EvidenceExpert, GovernanceExpert, PlaybookExpert. The Conductor invokes InvestigativeExpert operations as process steps."
- Remove any references to InvestigativeExpert "starting" or "owning" the Conductor loop

---

## 7. Trace Linkage for BPMN Observability (JACI)

**Decision:** Agentic activities inside a Conductor step emit Trace events for each iteration. The BPMN activity instance ID maps to the Trace's trace_id, enabling two levels of visibility: process level (BPMN) and activity level (Trace).

**Current state:** CanonicalTrace captures mode invocations but may not distinguish iteration boundaries within a single Conductor step.

**Task:** Verify that the Trace captures:
- Which Conductor step is running (step identifier)
- Iteration count within iterative steps (e.g., investigation loop iterations)
- Mode invocations per iteration with inputs/outputs

If iteration boundaries aren't captured, add a `step_id` and `iteration` field to Trace events. This is a schema addition, not a behavioral change.

---

## 8. Compounding Loop Terminology (JAPES)

**Decision:** The compounding loop has three distinct components: Eval (benchmarking, gold cases), Feedback (overrides, outcomes, human corrections), and Learning (the full loop that uses both to evolve pack assets). For v2, learning operates at the process level with outcome attribution.

**Current state:** Evaluator mode and Curator mode exist. The terminology in code may not distinguish eval from feedback from learning.

**Task:** Documentation only for now:
- Update Evaluator mode docstring: "Benchmarks quality against gold cases and quality rubrics. Measures whether the system is improving."
- Update Curator mode docstring: "Proposes versioned updates to pack assets (skills, policies, playbooks) based on eval signals and feedback."
- Add a note in EVOLVE category documentation: "Eval measures. Feedback provides signals. Learning is the full loop: feedback + eval + knowledge update + validation + promotion."

---

## Execution Order

1. Task 1 (Conductor naming) — already has a detailed spec, execute first
2. Tasks 2A, 3, 4, 5, 6, 8 — docstring/documentation updates, can be batched
3. Task 7 (Trace iteration boundaries) — schema check, may require a small addition

All tasks are non-breaking. No behavioral changes. Tests should pass without modification after every task.
