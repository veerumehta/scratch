# JACI - Clinical Intake Demo (clinical-intake-core)
## Claude Code Handoff

**Author:** Virendra Mehta
**Branch:** dev (jaci repo)
**IIF v1.5 reference:** Schema Spec (full canonical chain), Assistant Binding Annex, Charter INTERACT category
**Scenario type:** Demo. Mock-first, synthetic patients only, zero PHI. Not a product commitment.

---

## Why this matters

Every JACI scenario to date is a back-office case pipeline: documents in, evidence loop,
decision out. This demo is the opposite shape - a patient-facing, turn-based intake agent
in a new regulated vertical (healthcare). It proves three claims at once:

1. The SDK is genuinely domain-agnostic. Nothing below the pack layer knows this is healthcare.
2. The INTERACT surface works end to end: InteractiveAgent, ConversationStore, guardrails,
   and the Assistant Surface Primitives carry a live conversational agent.
3. Agent-as-config parity with the market reference (patient-facing healthcare agent vendors
   whose "agent" is a certified protocol on a shared substrate). Our version of their
   30-minute agent creation is a profile folder plus pack assets, zero platform code, with
   a governed canonical chain they do not surface: when our Governor escalates, the Trace
   shows which policy clause fired and why.

The demo hero moment: mid-intake, the synthetic patient mentions chest pain. The Governor
guardrail hard-blocks the turn, the intake script halts, the agent hands off to a human
nurse, and the UI surfaces the binding policy clause and the Trace step.

---

## Current state (verified against the codebase)

- `jazzx_sdk/agents/interactive/` has the full chassis: `InteractiveAgent`,
  `InteractiveAgentSpec` (persona, model, scope, knowledge bindings via fabric, skills as
  scoped sub-agents), `ConversationStore` (InProcess and Sql), compaction policies, and a
  guardrails hook. `InteractiveAgentSpec.from_dir()` loads a profile folder:
  `profile.yaml` + `persona.md` + `skills/*.yaml`.
- The `InteractiveAgent` constructor accepts `guardrails=` as either a `GuardrailRegistry`
  (phase-aware) or a plain `{name: callable}` catalog where each callable is
  `(text) -> str | None` and a returned reason string blocks the turn. The spec declares
  `guardrails: {input: [...], output: [...]}` by name. NOTE FOR IMPLEMENTATION: confirm
  where guardrail resolution happens inside `respond()` and whether a concrete
  `GuardrailRegistry` class exists; if it does not, use the plain catalog form. Do not
  invent a registry class in the SDK for this demo.
- The mode catalog (`jazzx_sdk/modes/catalog.py`) defines the INTERACT category, but
  `modes/operational/` has no INTERACT-class runtime mode. InteractiveAgent turn and
  guardrail events do not natively emit canonical objects; pack code wires that. Both are
  logged as JAPES Evolution gaps at the end of this plan - do not fix them in the SDK here.
- `config/packs/ci-spread-core/pack_manifest.yaml` is the manifest exemplar (assets,
  policies with core + overlays, mode_tuning, experts, conductor, evaluation,
  autonomy_ceilings, human_checkpoints).
- No JACI scenario currently uses InteractiveAgent. No healthcare pack assets exist.

Sequencing: this is JACI-only. No JAPES change is required or permitted in this plan.

---

## Change 1 - Pack scaffold

Create `config/packs/clinical-intake-core/pack_manifest.yaml`, patterned on
ci-spread-core (same section order and comment style). Key values and intent:

- `pack_id: clinical-intake-core`, `pack_name: "Clinical Intake Core"`,
  `pack_version: "0.1.0-draft"`, `certification_status: draft`,
  `domain: clinical_intake`, no `segment`.
- `regulatory_context`: `HIPAA_PRIVACY_RULE`, `STATE_NURSE_PRACTICE_ACTS`,
  `JOINT_COMMISSION_PROVISION_OF_CARE`. Demo-level references, not a compliance claim.
- `ontology: ontology/clinical_intake.yaml` - minimal: Patient, Medication, Allergy,
  Symptom, Encounter, ConsentRecord entities and their relations.
- `policies.core: policies/core.yaml` and one overlay slot (empty list is fine) to show
  the core + institution-overlay pattern carries over from CRE unchanged.
- `modes`: governor (temperature 0.0, tuning file), verifier (tuning file), narrator
  (tuning file), evaluator (deterministic class, see Change 6). No investigator, no
  reasoner - the point is packs select modes.
- `agent: agent/` - NEW manifest key pointing at the InteractiveAgent profile folder
  (Change 2). ci-spread-core has a `conductor:` section; this pack has an `agent:`
  section instead. Loader support: `Pack`/`PackLoader` may not know this key yet - if so,
  resolve the folder path in scenario code (Change 4) and leave the manifest key as
  declarative documentation. Do not modify the SDK loader.
- `autonomy_ceilings.default: 1` (RECOMMEND_ONLY). `human_checkpoints:`
  `NURSE_CHART_REVIEW` (nothing writes to a chart without nurse confirmation),
  `NURSE_ESCALATION_ACK` (an escalation is only closed by a human).
- `evaluation.gold_cases_path: tests/eval/gold_cases/clinical_intake`,
  `pass_threshold: 0.75`.

Create `config/packs/clinical-intake-core/intake_protocol.yaml` - the completeness
contract the Verifier checks against. Structure: an ordered list of `sections`, each with
`section_id`, `title`, `required: true|false`, and `fields` (field_id, prompt_hint,
evidence_type). Sections: identity_confirmation, visit_reason, current_medications,
allergies, medical_history, consent_confirmation. This file is config, not code - Pack
Studio should be able to edit it.

Create `config/packs/clinical-intake-core/policies/core.yaml` with roughly 8 policy
clauses in the same clause shape core.yaml uses in ci-spread-core. Two groups:

- Scope-of-practice hard blocks (mirroring the market reference's published exclusions):
  `CI-SCOPE-001` no diagnosis, `CI-SCOPE-002` no prescribing or medication changes,
  `CI-SCOPE-003` no dosing advice, `CI-SCOPE-004` no mental-health crisis counseling
  (escalate instead).
- Red-flag escalation clauses: `CI-ESC-001` chest pain or breathing difficulty,
  `CI-ESC-002` self-harm or harm-to-others disclosure, `CI-ESC-003` stated medication
  conflict or overdose signal, `CI-ESC-004` patient reports symptom of acute onset severe
  pain. Each clause carries `enforcement: hard_block` and an `escalation_target: human_nurse`.

Create `mode_tuning/governor.md`, `mode_tuning/verifier.md`, `mode_tuning/narrator.md` -
short domain-injection files in the ci-spread-core style. Governor tuning explains
red-flag semantics and that patients downplay symptoms (probe language is the agent's
job; the Governor's job is to catch the signal even when softened). Verifier tuning maps
protocol sections to completeness. Narrator tuning describes the nurse handoff summary
format (SBAR-lite: situation, collected data, gaps, escalations).

---

## Change 2 - Agent profile folder

Create `config/packs/clinical-intake-core/agent/` as an `InteractiveAgentSpec.from_dir()`
profile:

- `profile.yaml`: `name: clinical_intake_agent`, `persona: persona.md`,
  `scope: [patient_id, encounter_id]`, `conversation: true`,
  `compaction: {strategy: drop, keep_recent: 30}` (a demo session is short; drop is
  cheapest), `guardrails: {input: [clinical_governor_in], output: [clinical_governor_out]}`,
  `skills: [medication_capture, symptom_probe]`.
- `persona.md`: warm, plain-language intake assistant. States up front it is an AI
  assistant collecting information before the visit, it does not diagnose or prescribe,
  and a nurse reviews everything. Follows the protocol sections in order, one question at
  a time, confirms back what it heard. Never speculates about causes of symptoms.
- `skills/medication_capture.yaml`: sub-agent instructions for eliciting a complete
  medication list (name, dose as stated by patient, frequency), normalizing common
  phrasings, flagging uncertainty rather than guessing. `references:` the intake protocol
  medication section.
- `skills/symptom_probe.yaml`: sub-agent instructions for the visit_reason section -
  open question first, then targeted follow-ups (onset, duration, severity as the patient
  describes it). Explicitly instructed to record, not interpret.

Design intent: this folder is the whole "agent". The demo narrative line is that creating
the next healthcare agent means writing a new folder like this one.

---

## Change 3 - Governor guardrail

Create `src/jaci/scenarios/clinical_intake/guardrails.py`.

Two callables registered under the names the profile declares:

- `clinical_governor_in(text) -> str | None` - evaluates the incoming patient turn
  against the CI-ESC-* clauses. Mock-first: a deterministic keyword/pattern pass suffices
  for the demo (consistent with `use_mocks=True` elsewhere); structure the function so a
  GovernorMode-backed LLM evaluation can replace the matcher later without changing the
  signature. On trigger, return the escalation reason string (this blocks the turn) and
  invoke the emission helper below.
- `clinical_governor_out(text) -> str | None` - evaluates the agent's drafted reply
  against the CI-SCOPE-* clauses (defense in depth: the persona already forbids these,
  the guardrail enforces it).

Emission helper `emit_escalation(fabric, clause_id, utterance, session_id)`: writes a
CanonicalDecision (decision `ESCALATE_TO_NURSE`, `policy_refs=[clause_id]`, pack_id set)
and appends a Trace step recording the blocked turn and the binding clause. Follow the
existing canonical construction patterns in `jazzx_sdk.fabric.canonical` - verify required
fields (including `pack_id`) against the current Decision schema before writing.

Critical signature:

```python
def build_guardrails(fabric, policies) -> dict[str, Callable[[str], str | None]]:
    """Returns the {name: callable} catalog passed to InteractiveAgent(guardrails=...)."""
```

---

## Change 4 - Intake session wrapper

Create `src/jaci/scenarios/clinical_intake/session.py` - the canonical-chain wrapper
around `InteractiveAgent.respond()`. This is where the platform story lives; keep it thin.

`IntakeSession` responsibilities per turn:

1. Call `InteractiveAgent.respond(messages, scope, session_id)`.
2. Write the patient utterance as a canonical Evidence object with utterance provenance
   (speaker=patient, session_id, turn index, timestamp). Reuse the existing evidence
   types if one fits; otherwise use the generic Evidence with an `evidence_type` of
   `patient_utterance`. Do not add a new SDK evidence type.
3. Append a Trace step for the turn (question asked, section in progress).
4. Track protocol progress: after each turn, run a completeness pass mapping accumulated
   evidence to `intake_protocol.yaml` sections (deterministic field-presence check; the
   Verifier mode formalizes it at session end).

End of session (`IntakeSession.close()`):

1. Verifier completeness check against the protocol - produces the section-by-section
   completeness result.
2. Decision: `INTAKE_COMPLETE`, `INTAKE_INCOMPLETE_FLAGGED`, or `ESCALATED` (if the
   governor fired at any point, ESCALATED wins).
3. Narrator handoff summary for the nurse (SBAR-lite per the mode tuning).
4. Outcome stub: `record_nurse_review(confirmed: bool, notes: str)` writes the Outcome
   object linked by decision_id, including override capture when the nurse contradicts
   the agent's completeness call.

Wiring: `build_intake_session(pack_dir, fabric, agents, use_mocks=True)` factory that
loads the profile via `InteractiveAgentSpec.from_dir()`, builds guardrails (Change 3),
and constructs the InteractiveAgent. With `use_mocks=True`, the agent's LLM calls go
through the existing mock plumbing; scripted mock replies live in the gold-dialog
fixtures (Change 6) so the demo runs without keys.

---

## Change 5 - Streamlit chat demo page

Create `src/jaci/scenarios/clinical_intake/ui/demo_page.py`, registered wherever the
ci_spread demo page is registered (locate the demo page registry / launcher wiring and
add this page the same way).

Layout - mirror the ci_spread demo_page conventions (Concepts and SDK-at-work expanders,
same header style):

- Main column: `st.chat_input` / `st.chat_message` loop against an `IntakeSession` held
  in `st.session_state`. A sidebar selector for the synthetic patient (the four gold
  dialog personas from Change 6, plus free-play).
- Live canonical panel (right column or expanders): Evidence objects accruing per turn;
  a protocol completeness meter driven by the per-turn completeness pass; the Trace view.
- The Governor moment: when a turn is blocked, render a distinct escalation banner
  showing the clause id, the clause text from core.yaml, and the Trace step - then a
  "Nurse acknowledges" button that records the Outcome and closes the session.
- End of session: Narrator handoff summary, Decision, and nurse confirm/override buttons
  wired to `record_nurse_review`.
- Concepts expander: one paragraph on agent-as-config (the profile folder), one on the
  canonical chain in this scenario, one on what the market reference does and does not
  surface (no vendor names in the UI; say "leading patient-facing healthcare AI vendors").

Voice is out of scope; note in the Concepts expander that voice is a runtime concern
below the pack layer.

---

## Change 6 - Gold dialogs and evaluator

Create `tests/eval/gold_cases/clinical_intake/` with four scripted dialogs as YAML
fixtures (dialog turns plus expected results):

- `cooperative_patient.yaml` - clean run, expect INTAKE_COMPLETE, all sections present.
- `downplaying_patient.yaml` - patient minimizes a symptom ("just a little chest
  tightness, it's nothing"); expect ESCALATED on CI-ESC-001. This is the demo's
  centerpiece case.
- `redflag_patient.yaml` - explicit red-flag disclosure early in the session; expect
  immediate ESCALATED, remaining sections untouched.
- `medication_conflict_patient.yaml` - patient reports doubling a dose; expect ESCALATED
  on CI-ESC-003.

Each fixture doubles as the scripted mock-reply source for `use_mocks=True` (Change 4).

Create `src/jaci/scenarios/clinical_intake/modes/evaluator.py` - deterministic, no LLM,
same registration style as `jaci.scenarios.ci_spread.modes.evaluator`. Grades: (a)
completeness accuracy vs expected sections, (b) escalation correctness (fired when
expected, did not fire when not, correct clause id), (c) scope adherence (no output
guardrail violations). Emits an EvaluationReport - verify the current constructor
requires `pack_id` and pass it (a known ValidationError footgun).

Create `tests/eval/run_clinical_intake_eval.py` runner patterned on `run_ci_eval.py`.

---

## Acceptance checks

1. `build_intake_session(pack_dir, use_mocks=True)` constructs without network access.
2. Running the cooperative dialog end to end yields Decision INTAKE_COMPLETE, one
   Evidence object per patient turn, a Trace with one step per turn, and an Outcome after
   `record_nurse_review(confirmed=True)`.
3. Running the downplaying dialog yields a blocked turn, Decision ESCALATED with
   `policy_refs=["CI-ESC-001"]`, and the Trace step recording the block.
4. The output guardrail blocks a planted mock reply containing dosing advice
   (CI-SCOPE-003).
5. `run_clinical_intake_eval.py` passes all four gold cases at threshold 0.75.
6. The Streamlit page loads, runs a full session in mock mode, and renders the
   escalation banner with clause text on the downplaying persona.
7. Nothing under `jazzx_sdk/` is modified.

---

## Out of scope - logged as JAPES Evolution inputs

- INTERACT-category mode runtime class (catalog defines the category; no implementation
  exists in `modes/operational/`).
- Native canonical-object emission from InteractiveAgent turn and guardrail events
  (this demo wires it in pack code; the pattern belongs in the SDK eventually).
- Voice runtime and telephony surface.
- Real EHR connectivity; chart-write integration is mocked behind NURSE_CHART_REVIEW.
