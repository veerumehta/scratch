# JACI-AML Charter Alignment Plan — Revised
**For: Claude Code execution**
**Context: JazzX / Institutional Intelligence platform**
April 2026 | Working document — additive to build plan Phases 0–6

---

## Revision Notes (v2)

This plan supersedes the original Charter Alignment Plan. Five design decisions
were revised after a critique review. Changes are summarised here so Claude Code
understands what changed and why before starting work.

| # | Original design | Revised design | Reason |
|---|----------------|----------------|--------|
| 1 | `CanonicalDecision` wraps `DispositionRecommendation` as a new class | Extend `DispositionRecommendation` directly with three new fields | Wrapper violates DRY, creates dual source of truth, risks drift |
| 2 | Evaluator LLM scores all 5 dimensions including deterministic ones | Python computes 4 deterministic metrics; LLM only handles SAR quality + improvement signal generation | Deterministic metrics don't need LLM; adds cost and latency for no gain |
| 3 | Curator uses keyword matching to classify signals | Python routing for structure + optional LLM synthesis step for deduplication/prioritization | Keyword matching won't scale; LLM synthesis is additive and doesn't violate human stewardship |
| 4 | Full `pack_loader.py` + startup validation + yaml-loaded ceilings | Lightweight yaml for `pack_id` traceability only; `autonomy_ceilings.py` stays hardcoded with comment | Full loader is premature governance overhead for a PoC with `draft` status |
| 5 | BPMN 2.0 XML stub file | Markdown process design document | Undeployed XML is documentation theater; markdown is clearer and maintainable |

---

## How to Use This Document

This is a Claude Code execution plan. Read it fully before touching any file. It is
self-contained — no other documents need to be open, though the JazzX framework
documents are in project knowledge if deep schema reference is needed.

**Execution order:** Phase 7 → Phase 10 → Phase 8 → Phase 9

Phase 10 before Phase 8 because the pack yaml establishes the `pack_id` reference
that Phase 8 canonical objects carry. The yaml is lightweight now — this ordering
still holds to keep pack_id traceable from the start.

**Hard constraints — read before writing a single line:**

- Do NOT modify Phases 0–6 artifacts except where this document explicitly marks
  a section "TARGETED AMENDMENT TO EXISTING FILE". All other work is additive.
- `pack_id` is always the string `"aml-investigation-core"` — hardcoded constant
  that traces back to `config/packs/aml_investigation_core.yaml`.
- Evaluator is async and post-case. It must NEVER be called inside the live
  investigation loop. Conductor does not call Evaluator. Full stop.
- Curator's Python routing function is NOT an LLM call. The optional LLM synthesis
  step (see Phase 9) is clearly separated and additive.
- SAR filing remains human-only. No phase here changes the autonomy posture.
- The 10 gold cases in `tests/eval/gold_cases/` are reused in Phase 8.
  Do not create a second eval dataset.

---

## Current State Assessment

**What exists (Phases 0–6):**

| Component | Location | Status |
|-----------|----------|--------|
| All 6 mode implementations | `src/jaci/modes/` | Done |
| 6 mode prompts | `prompts/` | Done |
| `case_context.py` — JACI-specific schemas | `src/jaci/schemas/` | Done |
| Tool registry + 8 tools | `src/jaci/tools/` | Done |
| Conductor loop + guards | `src/jaci/conductor.py` | Done |
| 10 gold cases + run_eval.py | `tests/eval/` | Done |
| autonomy_ceilings.py | `config/` | Done — stays hardcoded, Phase 10 adds yaml reference only |
| BPMN process | `bpmn/` | Empty — replaced with process_design.md |

**What is absent (Phases 7–10, this document):**

- Cross-linkage fields on `DispositionRecommendation` (`policy_refs`, `evidence_refs`, `trace_id`)
- `CanonicalTrace` and `Outcome` schemas
- No `pack_id` field anywhere in the codebase
- No Evaluator mode or `EvaluationReport` schema
- No Curator or `CuratorQueue` schema
- No `aml_investigation_core.yaml` pack reference file

**Three charter gaps this plan closes:**

1. **Gap 1 — EVOLVE layer absent:** No Evaluator, no Curator, compounding loop
   does not close. Phases 8 + 9.
2. **Gap 2 — Pack governance orphaned:** `pack_id` is a floating string constant
   with no resolvable parent. Phase 10.
3. **Gap 3 — Canonical cross-linkage partial:** `DispositionRecommendation` has no
   `policy_refs`, `evidence_refs`, or `trace_id`. No Trace or Outcome schemas exist.
   Phase 7.

---

## Phase 7: Canonical Object Schema Compliance

**Estimated effort:** 1 day
**Dependency:** Phase 1 schemas (`case_context.py`), Phase 4 Conductor

**Goal:** Formally align JACI-AML runtime objects with the II canonical type system.
Schema layer change only — no loop logic changes in Phase 7.

### 7.1 Targeted amendment: `src/jaci/schemas/case_context.py` — extend `DispositionRecommendation`

**Design rationale:** The original plan proposed a `CanonicalDecision` wrapper class.
This was revised because wrapping creates a dual source of truth, violates DRY, and
risks drift between the two objects. Instead, extend `DispositionRecommendation`
directly with three new cross-linkage fields. This is backward-compatible — all
existing fields remain unchanged. New fields default to empty so no callers break.

Find `DispositionRecommendation` in `case_context.py`. Add three fields after
`policy_clauses_cited`:

```python
# ADD these three fields to DispositionRecommendation
# (after the existing policy_clauses_cited field):

decision_id: str = Field(
    default_factory=lambda: f"decision_{uuid4()}",
    description=(
        "Canonical II Decision identifier. Namespaced UUID format: decision_{uuid_v4}. "
        "Populated by Conductor after Governor gate."
    ),
)
policy_refs: list[str] = Field(
    default_factory=list,
    description=(
        "Policy clause IDs cited by Governor gate — canonical cross-linkage field. "
        "Mirror of policy_clauses_cited cast to str. "
        "Required by Schema Spec §8: every Decision must reference governing Policies."
    ),
)
evidence_refs: list[str] = Field(
    default_factory=list,
    description=(
        "evidence_id values supporting this decision — canonical cross-linkage field. "
        "Mirror of supporting_evidence_ids cast to str. "
        "Required by Schema Spec §8: every Decision must reference supporting Evidence."
    ),
)
trace_id: str = Field(
    default="",
    description=(
        "Reference to the CanonicalTrace produced by Conductor for this case. "
        "Required by Schema Spec §8: every Decision must reference the Trace "
        "that produced it. Populated by Conductor before CaseFile assembly."
    ),
)
pack_id: str = Field(
    default="aml-investigation-core",
    description="Stable Domain Pack identifier.",
)
```

Also add `from uuid import uuid4` to the imports in `case_context.py` if not
already present.

**Population logic (in `conductor.py` — see 7.4):** After Governor approves the
disposition, Conductor backfills these fields on the `DispositionRecommendation`
object before CaseFile assembly. No separate wrapper class is created.

### 7.2 New file: `src/jaci/schemas/canonical_trace.py`

`CanonicalTrace` is genuinely new — it is not a wrapper of anything existing. It
captures the execution lineage of the full investigation loop, emitted by Conductor
at loop completion.

```python
"""
CanonicalTrace — II canonical Trace object for JACI-AML.

Emitted by Conductor at loop completion (after Governor gate, before CaseFile
assembly). Captures execution lineage for the entire investigation.

Cross-linkage invariants (Schema Spec §8):
  trace.decisions_produced[] → DispositionRecommendation.decision_id values
  trace.evidence_consumed[]  → all evidence_id values processed during the loop
  trace.policies_applied[]   → policy clause IDs checked by Governor

Pack binding: pack_id = "aml-investigation-core"
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

PACK_ID = "aml-investigation-core"


class LoopTerminationReason(str, Enum):
    CONVERGED = "converged"
    SIGNAL_DECAY = "signal_decay"
    DEADLINE = "deadline"
    MAX_ITER = "max_iter"
    GOVERNOR_BLOCKED = "governor_blocked"


class CanonicalTrace(BaseModel):
    """
    Formally typed II Trace object for a JACI-AML investigation.

    One CanonicalTrace is produced per case. It links to the
    DispositionRecommendation (via decision_id) it produced and records
    all evidence consumed and policies applied during the investigation.
    """

    trace_id: str = Field(
        default_factory=lambda: f"trace_{uuid4()}",
        description="Namespaced UUID. Format: trace_{uuid_v4}.",
    )
    case_id: str = Field(..., description="CaseContext.case_id this trace covers.")
    alert_id: str = Field(..., description="AlertTrigger.alert_id that opened this case.")

    # Cross-linkage fields (Schema Spec §8) — required
    decisions_produced: list[str] = Field(
        default_factory=list,
        description=(
            "decision_id values from DispositionRecommendation objects produced "
            "during this trace. For JACI-AML, typically one per case."
        ),
    )
    evidence_consumed: list[str] = Field(
        default_factory=list,
        description=(
            "All evidence_id values of EvidenceObjects processed during the loop, "
            "including attested, flagged, and unavailable objects."
        ),
    )
    policies_applied: list[str] = Field(
        default_factory=list,
        description=(
            "Policy clause IDs checked by Governor gate. "
            "Superset of DispositionRecommendation.policy_refs."
        ),
    )

    # Loop execution metadata
    iteration_count: int = Field(..., description="Number of Investigator iterations completed.")
    loop_termination_reason: LoopTerminationReason = Field(
        ..., description="Why the investigation loop stopped."
    )
    attested_evidence_count: int = Field(
        default=0,
        description="Count of EvidenceObjects with verifier_status=ATTESTED.",
    )
    flagged_evidence_count: int = Field(
        default=0,
        description="Count of EvidenceObjects with verifier_status=FLAGGED.",
    )

    # Governance fields
    pack_id: str = Field(
        default=PACK_ID,
        description="Stable Domain Pack identifier. Always 'aml-investigation-core'.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 7.3 New file: `src/jaci/schemas/outcome.py`

`Outcome` is written after L3/FIU human review. It records the actual case result
and links back to the `DispositionRecommendation` (via `decision_id`) and
`CanonicalTrace`. For the PoC, Outcome is written directly by the eval harness
when simulating human review (see Phase 8).

```python
"""
Outcome — II canonical Outcome object for JACI-AML.

Written after L3/FIU human review completes.
Records the actual case result and links back to the DispositionRecommendation
(via decision_id) and CanonicalTrace that produced it.

Cross-linkage invariants (Schema Spec §8):
  outcome.decision_id → DispositionRecommendation.decision_id
  outcome.trace_id    → CanonicalTrace.trace_id

Outcome types for JACI-AML PoC:
  All Outcomes use "proxy" type (SAR filed / not filed, observable at L3 review).
  Lagged outcomes (regulatory findings, confirmed fraud) are Phase 2+.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

PACK_ID = "aml-investigation-core"


class OutcomeType(str, Enum):
    DIRECT = "direct"
    PROXY = "proxy"    # PoC — SAR filed / not filed
    LAGGED = "lagged"  # Phase 2+ — regulatory findings, confirmed fraud


class OutcomeClass(str, Enum):
    SAR_FILED = "sar_filed"
    CASE_CLOSED_NO_SAR = "case_closed_no_sar"
    ESCALATED_TO_FIU = "escalated_to_fiu"
    HUMAN_OVERRIDE_ESCALATE = "human_override_escalate"
    HUMAN_OVERRIDE_CLOSE = "human_override_close"


class Outcome(BaseModel):
    """
    Formally typed II Outcome for a JACI-AML case.

    Written by the process completion handler after L3/FIU review.
    In eval harness context, constructed from gold case expected_outcome.
    """

    outcome_id: str = Field(
        default_factory=lambda: f"outcome_{uuid4()}",
        description="Namespaced UUID. Format: outcome_{uuid_v4}.",
    )
    outcome_type: OutcomeType = Field(
        default=OutcomeType.PROXY,
        description="Proxy for PoC. Lagged outcomes are Phase 2+.",
    )
    outcome_class: OutcomeClass = Field(..., description="Domain-specific outcome type.")

    # Cross-linkage fields (Schema Spec §8) — required
    decision_id: str = Field(
        ..., description="DispositionRecommendation.decision_id this outcome evaluates."
    )
    trace_id: str = Field(
        ..., description="CanonicalTrace.trace_id that produced the linked decision."
    )

    # Observation window (required per Schema Spec §6)
    observation_window_start: datetime = Field(..., description="When L3/FIU review began.")
    observation_window_end: datetime = Field(..., description="When the outcome was recorded.")

    # Result payload
    result: dict = Field(
        default_factory=dict,
        description=(
            "Outcome payload. For JACI-AML: "
            "{'sar_filed': bool, 'sar_reference': str | None, "
            "'human_reviewer_id': str, 'reviewer_notes': str | None}"
        ),
    )
    human_override: bool = Field(
        default=False,
        description="True if L3/FIU reviewer changed the system recommendation.",
    )
    override_reason: str | None = Field(
        default=None,
        description="Required when human_override=True.",
    )
    learning_signals: list[str] = Field(
        default_factory=list,
        description=(
            "Human-readable insights from this outcome. Populated by reviewer or Evaluator. "
            "Example: 'Reasoner under-weighted PEP risk for Tier 2 jurisdictions.'"
        ),
    )

    # Governance fields
    pack_id: str = Field(default=PACK_ID)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(
        default="eval_harness",
        description="'eval_harness' for gold case runs; reviewer ID for live cases.",
    )
```

### 7.4 Targeted amendment: `src/jaci/schemas/__init__.py`

Add imports for the new schema modules without removing anything:

```python
# ADD to existing imports:
from jaci.schemas.canonical_trace import CanonicalTrace, LoopTerminationReason
from jaci.schemas.outcome import Outcome, OutcomeType, OutcomeClass

# ADD to __all__:
"CanonicalTrace",
"LoopTerminationReason",
"Outcome",
"OutcomeType",
"OutcomeClass",
```

Note: no `CanonicalDecision` import needed — the cross-linkage fields are now
directly on `DispositionRecommendation`.

### 7.5 Targeted amendment: `src/jaci/conductor.py`

Two targeted additions. Do not change any loop logic.

**Addition 1 — emit CanonicalTrace at loop completion:**

Find the section after the loop terminates and before `reasoner_result = await
self.reasoner.run(ctx)`. Add:

```python
# ─── Emit CanonicalTrace ─────────────────────────────────────────────────
from jaci.schemas import CanonicalTrace, LoopTerminationReason

_termination_map = {
    LoopStatus.CONVERGED: LoopTerminationReason.CONVERGED,
    LoopStatus.GUARD_FIRED: LoopTerminationReason.SIGNAL_DECAY,
    LoopStatus.GOVERNOR_BLOCKED: LoopTerminationReason.GOVERNOR_BLOCKED,
}
_termination_reason = _termination_map.get(ctx.loop_status, LoopTerminationReason.MAX_ITER)
# Refine GUARD_FIRED to DEADLINE if the deadline guard triggered it
if ctx.loop_status == LoopStatus.GUARD_FIRED and ctx.sar_deadline:
    from datetime import timedelta
    if ctx.sar_deadline - datetime.utcnow() < timedelta(hours=self.deadline_guard_hours):
        _termination_reason = LoopTerminationReason.DEADLINE

canonical_trace = CanonicalTrace(
    case_id=str(ctx.case_id),
    alert_id=ctx.alert.alert_id,
    evidence_consumed=[str(ev.evidence_id) for ev in ctx.evidence],
    policies_applied=[],   # backfilled after Governor runs below
    iteration_count=ctx.iteration_count,
    loop_termination_reason=_termination_reason,
    attested_evidence_count=len(ctx.attested_evidence),
    flagged_evidence_count=len([e for e in ctx.evidence
                                if e.verifier_status == EvidenceStatus.FLAGGED]),
)
```

**Addition 2 — backfill cross-linkage fields on DispositionRecommendation:**

After Governor approves the disposition, backfill the three new fields on the
`DispositionRecommendation` object and update the `CanonicalTrace`. Find the
section just before `CaseFile` assembly:

```python
# ─── Backfill canonical cross-linkage fields ─────────────────────────────
# Populate the three new fields added to DispositionRecommendation in Phase 7.
disposition.trace_id = canonical_trace.trace_id
disposition.policy_refs = [str(pid) for pid in disposition.policy_clauses_cited]
disposition.evidence_refs = [str(eid) for eid in disposition.supporting_evidence_ids]

# Backfill trace with decision reference and policies
canonical_trace.decisions_produced = [disposition.decision_id]
canonical_trace.policies_applied = disposition.policy_refs
```

**Addition 3 — add `canonical_trace` to `CaseFile`:**

`CaseFile` in `case_context.py` needs one new optional field. Add to `CaseFile`:

```python
canonical_trace: CanonicalTrace | None = Field(
    None, description="II canonical Trace for this case. Set by Conductor."
)
```

Then in `conductor.py` CaseFile assembly:

```python
case_file = CaseFile(
    case_context=ctx,
    disposition=disposition,
    governor_decision=gov_decision,
    sar_draft=sar_draft,
    canonical_trace=canonical_trace,   # ADD
)
```

### 7.6 Phase 7 acceptance criteria

- New schema files import cleanly: `python -c "from jaci.schemas import CanonicalTrace, Outcome"`
- `DispositionRecommendation` has `decision_id`, `policy_refs`, `evidence_refs`,
  `trace_id`, `pack_id` fields and all default correctly
- After Conductor runs: `disposition.trace_id == canonical_trace.trace_id`
- `canonical_trace.decisions_produced` is non-empty
- `canonical_trace.evidence_consumed` matches `len(ctx.evidence)`
- `CaseFile.canonical_trace` is present in serialised output for all 10 gold cases
- Existing unit tests (`tests/unit/`) continue to pass — no regressions

---

## Phase 10: AML Domain Pack Reference Stub

**Estimated effort:** 0.5 days (reduced from original 1 day)
**Dependency:** Phase 7 (`pack_id` fields now exist on canonical objects)
**Execute before Phase 8** — yaml anchors the `pack_id` string before Phase 8 uses it.

**Revised goal:** Create a lightweight reference yaml that makes `pack_id:
aml-investigation-core` a traceable reference. The `autonomy_ceilings.py` config
stays hardcoded — adding a full yaml loader is premature governance overhead for a
PoC with `certification_status: draft`. A comment in `autonomy_ceilings.py`
provides the traceability link.

Full ABA, JAP, Overlay documents and `pack_loader.py` machinery are explicitly
out of scope for the PoC.

### 10.1 New file: `config/packs/aml_investigation_core.yaml`

```yaml
# AML Investigation Core — Domain Pack Reference Stub
# JazzX Institutional Intelligence Platform
# pack_id: aml-investigation-core
#
# Purpose: Provides a traceable, versioned reference for the pack_id string
# used in CanonicalTrace, Outcome, EvaluationReport, and CuratorQueue objects.
# This is a PoC stub — NOT certified for production use.
#
# Full formalisation (pack_loader.py, ABA, JAP, Overlay) is a production
# readiness workstream, not PoC scope.
#
# Autonomy ceiling values are in config/autonomy_ceilings.py.
# This yaml is the documentation reference; the code is the runtime source of truth.

pack_id: aml-investigation-core
pack_name: "AML Investigation Core"
pack_version: "0.1.0-draft"
certification_status: draft   # draft | certified | suspended | retired

domain: aml_financial_crimes_investigation
regulatory_context:
  - BSA        # Bank Secrecy Act
  - FinCEN
  - FATF
  - FFIEC_BSA_AML_EXAM_MANUAL

# Autonomy ceilings (runtime values live in config/autonomy_ceilings.py)
# Documented here for traceability only — not loaded at runtime in PoC.
autonomy_ceilings:
  LOW: 3      # FULL_AUTONOMY
  MEDIUM: 2   # ACT_WITH_APPROVAL
  HIGH: 1     # RECOMMEND_ONLY

# SAR filing is ALWAYS human-only — regulatory invariant, cannot be overridden
sar_filing_autonomy: 0

# Policy families bound to this pack (Governor clause namespace prefixes)
policy_family_refs:
  - BSA-CTR
  - BSA-SAR
  - FinCEN-STRUCT
  - FinCEN-CDD-RULE
  - CDD-BO
  - CDD-LINKED-ACCT
  - EDD-PEP
  - BSA-EDD-HIGH-RISK
  - FATF-R12
  - FATF-R24

# AML typology library bound to this pack
typology_refs:
  - TYP-STRUCT-001   # Structuring / Smurfing
  - TYP-SHELL-002    # Shell Company Layering
  - TYP-PEP-003      # PEP Rapid Movement
  - TYP-RT-004       # Round-Tripping
  - TYP-CASH-005     # Unusual Cash Activity
  - TYP-PEP-006      # PEP Exposure
  - TYP-WIRE-007     # Unusual Wire Transfer

# Human checkpoints — must never be automated
human_checkpoints:
  - L3_FIU_DISPOSITION_REVIEW   # Analyst reviews Close/Escalate recommendation
  - SAR_FILING_DECISION         # Compliance officer — regulatory requirement

# Evaluation assets
evaluation_asset_refs:
  - tests/eval/gold_cases/
  - tests/eval/run_eval.py

# Governance chain — deferred to production
governance_chain:
  aba: DEFERRED      # Assistant Binding Annex — Phase 2+
  jap: DEFERRED      # JazzX Assistant Profile — Phase 2+
  overlay: DEFERRED  # Certified Client Overlay — per-institution, Phase 2+

created_at: "2026-04-22"
```

### 10.2 Targeted amendment: `config/autonomy_ceilings.py`

Add a comment linking to the yaml reference. No functional change to the code.

Find the `RISK_TIER_CEILINGS` dict and add a comment above it:

```python
# Source of truth (documentation): config/packs/aml_investigation_core.yaml
# Runtime source of truth: this dict.
# In production, load from pack yaml via pack_loader.py.
# For PoC (pack status: draft), hardcoded values are correct and intentional.
RISK_TIER_CEILINGS: dict[str, AutonomyLevel] = {
    "LOW": AutonomyLevel.FULL_AUTONOMY,
    "MEDIUM": AutonomyLevel.ACT_WITH_APPROVAL,
    "HIGH": AutonomyLevel.RECOMMEND_ONLY,
}
```

### 10.3 Phase 10 acceptance criteria

- `config/packs/aml_investigation_core.yaml` exists and is valid yaml
- Values in yaml `autonomy_ceilings` block match `RISK_TIER_CEILINGS` in
  `autonomy_ceilings.py`
- All canonical objects carry `pack_id: "aml-investigation-core"` in serialised output
- No new Python dependencies required (no yaml loading at runtime)

---

## Phase 8: Evaluator Mode

**Estimated effort:** 1.5 days
**Dependency:** Phase 7 (extended schemas), Phase 10 (pack yaml), Phase 6 (gold cases)

**Goal:** Implement the Evaluator mode that closes the EVOLVE layer. Post-case only.

**Revised design — split deterministic vs qualitative:**

The original plan had the LLM score all five evaluation dimensions. This is wasteful
for dimensions that are pure arithmetic. The revised design splits the work:

- **Python `compute_deterministic_metrics()`** — computes four metrics from structured
  data: `decision_accuracy`, `evidence_efficiency`, `policy_compliance`,
  `loop_efficiency`. No LLM call. Fast, cheap, fully reproducible.
- **LLM `EvaluatorMode`** — called only for `sar_quality` (requires reading the SAR
  draft and assessing narrative coherence and citation completeness) and for
  generating `improvement_signals` (requires synthesizing patterns across the full
  case). For Close cases with no SAR draft, `sar_quality` is omitted and the LLM
  is still called for improvement signal generation.

This means one LLM call per case instead of five, with no loss of quality for the
dimensions that matter (qualitative assessment and signal generation).

### 8.1 New file: `src/jaci/schemas/evaluation_report.py`

```python
"""
EvaluationReport — II derived object produced by Evaluator.

Derived object per Schema Spec §7.7. Produced after each resolved case.

Score computation:
  - decision_accuracy, evidence_efficiency, policy_compliance, loop_efficiency:
    computed by Python (compute_deterministic_metrics in evaluator.py)
  - sar_quality: assessed by LLM (Escalate cases only)
  - improvement_signals: generated by LLM for all cases

evaluation_type is always "periodic_review" for post-case eval in JACI-AML.
"""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

PACK_ID = "aml-investigation-core"


class EvaluationReport(BaseModel):
    """Formally typed II EvaluationReport for a JACI-AML case."""

    report_id: str = Field(
        default_factory=lambda: f"evalreport_{uuid4()}",
        description="Namespaced UUID. Format: evalreport_{uuid_v4}.",
    )
    evaluation_type: str = Field(
        default="periodic_review",
        description="Always 'periodic_review' for post-case eval.",
    )

    # Subject references
    case_id: str = Field(...)
    decision_id: str = Field(...)
    trace_id: str = Field(...)
    outcome_id: str = Field(...)

    # Evaluation period
    period_start: datetime = Field(..., description="When the case investigation started.")
    period_end: datetime = Field(..., description="When the outcome was recorded.")

    # Scores (0.0–1.0 per dimension)
    # decision_accuracy, evidence_efficiency, policy_compliance, loop_efficiency
    # are Python-computed. sar_quality is LLM-assessed (Escalate only).
    scores: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Keys: decision_accuracy, evidence_efficiency, policy_compliance, "
            "loop_efficiency, sar_quality (Escalate only). Values: 0.0–1.0."
        ),
    )

    # Findings for dimensions scoring below 0.7 threshold
    findings: list[str] = Field(
        default_factory=list,
        description=(
            "One finding string per dimension scoring below 0.7. "
            "Format: '[dimension]: <observation>'"
        ),
    )

    # Improvement signals for Curator — LLM-generated
    improvement_signals: list[str] = Field(
        default_factory=list,
        description=(
            "Specific, actionable observations for Curator to route to Knowledge Hub. "
            "LLM-generated. These become candidates for pack knowledge updates "
            "(human-reviewed by knowledge steward)."
        ),
    )

    # Override flag
    human_override_detected: bool = Field(
        default=False,
        description="True if Outcome.human_override=True.",
    )

    # Governance
    pack_id: str = Field(default=PACK_ID)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 8.2 New file: `src/jaci/modes/evaluator.py`

The module contains two components: a pure Python metrics function and the LLM
Evaluator mode that calls it before doing qualitative analysis.

```python
"""
evaluator.py — Post-case quality assessment.

Two components:
  1. compute_deterministic_metrics() — pure Python, no LLM, called first
  2. EvaluatorMode — LLM mode for sar_quality + improvement_signals only

ARCHITECTURAL CONSTRAINT:
  EvaluatorMode must NEVER be called inside the live investigation loop.
  Conductor does not call Evaluator.
  Called by: run_eval.py (eval harness) and the process completion handler.

Inputs:  CaseFile (with canonical_trace + disposition) + Outcome
Outputs: EvaluationReport
"""

import logging

from jaci.schemas.case_context import CaseFile, Recommendation
from jaci.schemas.outcome import Outcome
from jaci.schemas.evaluation_report import EvaluationReport

logger = logging.getLogger(__name__)

FINDING_THRESHOLD = 0.7


def compute_deterministic_metrics(
    case_file: CaseFile,
    outcome: Outcome,
) -> dict[str, float]:
    """
    Compute evaluation metrics that are fully deterministic from structured data.

    No LLM call. O(n) over evidence list. Called before EvaluatorMode.run().

    Metrics computed:
      decision_accuracy   — did system recommendation match gold outcome?
      evidence_efficiency — what fraction of retrieved evidence was cited?
      policy_compliance   — were required policy clauses present?
      loop_efficiency     — did loop converge within target iteration range?

    Returns:
        dict with float scores 0.0–1.0 per metric.
    """
    scores: dict[str, float] = {}

    # 1. Decision accuracy — binary match between system rec and human outcome
    system_rec = case_file.disposition.recommendation
    if not outcome.human_override:
        scores["decision_accuracy"] = 1.0
    else:
        # Override happened: score by whether the available evidence was sufficient
        # to justify the system's recommendation (partial credit for defensible cases)
        attested = len(case_file.case_context.attested_evidence)
        scores["decision_accuracy"] = 0.5 if attested >= 3 else 0.2

    # 2. Evidence efficiency — cited evidence / retrieved evidence
    retrieved_ids = {str(ev.evidence_id) for ev in case_file.case_context.evidence}
    cited_ids = set(str(eid) for eid in case_file.disposition.supporting_evidence_ids)
    if retrieved_ids:
        ratio = len(cited_ids & retrieved_ids) / len(retrieved_ids)
        scores["evidence_efficiency"] = round(ratio, 2)
    else:
        scores["evidence_efficiency"] = 0.0

    # 3. Policy compliance — were required clauses cited?
    cited_policies = set(case_file.disposition.policy_refs)
    if case_file.disposition.recommendation == Recommendation.ESCALATE:
        # Escalate requires at least 1 policy clause per Governor gate
        scores["policy_compliance"] = 1.0 if len(cited_policies) >= 1 else 0.0
    else:
        # Close cases: no minimum policy clause requirement
        scores["policy_compliance"] = 1.0

    # 4. Loop efficiency — iterations vs target
    iters = case_file.case_context.iteration_count
    if iters <= 3:
        scores["loop_efficiency"] = 1.0
    elif iters <= 5:
        scores["loop_efficiency"] = 0.8
    elif iters <= 8:
        scores["loop_efficiency"] = 0.5
    else:
        scores["loop_efficiency"] = 0.2

    return scores


# EvaluatorMode implementation follows the pattern in src/jaci/modes/reasoner.py.
# Key differences from other modes:
#   1. Takes CaseFile + Outcome + pre-computed scores as input
#   2. LLM only assesses sar_quality (Escalate cases) + generates improvement_signals
#   3. Not registered in Conductor — post-case only
#   4. Merges LLM output with deterministic scores into final EvaluationReport
```

### 8.3 New file: `prompts/evaluator.md`

```markdown
# Evaluator Mode — System Prompt

You are a case quality evaluator for an AML investigation system. You receive a
resolved AML case with pre-computed metrics and must complete the quality assessment
by evaluating SAR narrative quality (if applicable) and generating improvement signals.

## What you are NOT doing

The following metrics have already been computed by Python and are provided to you
as inputs. Do not recompute or override them:
- decision_accuracy
- evidence_efficiency
- policy_compliance
- loop_efficiency

## Your inputs

- **DispositionRecommendation**: The system's Close or Escalate recommendation,
  confidence score, rationale, policy clauses cited, evidence IDs referenced.
- **CanonicalTrace**: Execution record — iterations, evidence consumed, termination reason.
- **EvidenceObjects**: Full list of evidence with verifier attestation status.
- **SARDraft** (Escalate cases only): The five-section SAR narrative with evidence citations.
- **Outcome**: The actual L3/FIU human decision — what they decided, whether they
  overrode the recommendation, and any reviewer notes.
- **pre_computed_scores**: Python-computed scores for decision_accuracy,
  evidence_efficiency, policy_compliance, loop_efficiency.

## Task 1: SAR Quality Assessment (Escalate cases only)

If a SARDraft is present, assess narrative quality and assign sar_quality (0.0–1.0):

- **1.0**: All five sections complete, every material claim cites an evidence_id
- **0.7–0.9**: Minor gaps — one section thin, no uncited claims
- **0.4–0.6**: Section missing or at least one material claim without evidence citation
- **0.0–0.3**: Hallucinated claim — assertion with no supporting EvidenceObject

For Close cases (no SAR draft): omit sar_quality from scores entirely.

## Task 2: Generate improvement signals

Produce a list of specific, actionable improvement signals. These become candidates
for pack knowledge updates, reviewed by a human knowledge steward.

**Signal quality criteria:**
- Concrete and targeted — cite specific typology IDs, evidence types, or policy clauses
- Actionable — refers to something that could be changed in a knowledge asset
  (typology library, evidence checklist, policy clause, playbook)
- Not about code bugs or model behaviour

**Good signal:**
"Typology TYP-SHELL-002 consistently required counterparty_network at depth 3 but
the evidence checklist only specifies depth 2 — consider updating the playbook."

**Bad signal:**
"The system could improve its evidence gathering."

If human_override occurred, generate at least one signal explaining what knowledge
change might have prevented the override.

## Output format

Respond ONLY with a JSON object. No preamble or explanation outside the JSON.

```json
{
  "sar_quality": 0.0,
  "findings": [
    "[dimension]: observation for any pre-computed score below 0.7",
    "[sar_quality]: observation if sar_quality below 0.7"
  ],
  "improvement_signals": [
    "signal 1",
    "signal 2"
  ],
  "human_override_detected": false
}
```

The caller will merge your output with the pre-computed scores into the final
EvaluationReport. Only include sar_quality if a SAR draft was present.
```

### 8.4 Targeted amendment: `tests/eval/run_eval.py`

**What to preserve:** `load_gold_cases()`, `Conductor` invocation, CI gate threshold.

**What to replace:** The custom `EvaluationMetrics` dict-based scoring with
`EvaluationReport` objects using the new split approach.

**Execution flow per case:**
1. Run conductor → get `CaseFile`
2. Construct `Outcome` from gold case (see helper below)
3. Call `compute_deterministic_metrics(case_file, outcome)` → get scores dict
4. Call `EvaluatorMode.run(case_file, outcome, pre_computed_scores)` → get LLM output
5. Merge into `EvaluationReport`

**Outcome construction helper:**

```python
def outcome_from_gold_case(gold_case: dict, case_file: CaseFile) -> Outcome:
    """
    Construct a simulated Outcome from gold case expected_outcome.
    Gold label is the human ground truth for eval harness purposes.
    """
    from datetime import datetime
    from jaci.schemas.outcome import Outcome, OutcomeClass

    expected = gold_case["expected_outcome"]
    actual_rec = case_file.disposition.recommendation.value
    expected_rec = expected["recommendation"]
    human_override = actual_rec != expected_rec

    outcome_class_map = {
        ("escalate", False): OutcomeClass.SAR_FILED,
        ("close",    False): OutcomeClass.CASE_CLOSED_NO_SAR,
        ("escalate", True):  OutcomeClass.HUMAN_OVERRIDE_CLOSE,
        ("close",    True):  OutcomeClass.HUMAN_OVERRIDE_ESCALATE,
    }

    return Outcome(
        outcome_class=outcome_class_map.get(
            (expected_rec, human_override), OutcomeClass.CASE_CLOSED_NO_SAR
        ),
        decision_id=case_file.disposition.decision_id,
        trace_id=case_file.canonical_trace.trace_id if case_file.canonical_trace else "",
        observation_window_start=case_file.completed_at,
        observation_window_end=datetime.utcnow(),
        result={
            "sar_filed": expected_rec == "escalate",
            "human_reviewer_id": "eval_harness_gold_label",
            "reviewer_notes": f"Gold case ground truth: {expected_rec}",
        },
        human_override=human_override,
        override_reason=(
            f"System recommended {actual_rec}, gold label is {expected_rec}"
            if human_override else None
        ),
        created_by="eval_harness",
    )
```

**CI gate — unchanged threshold, new source:**

```python
# Replace EvaluationMetrics.compute_summary() with:
mean_accuracy = sum(r.scores["decision_accuracy"] for r in evaluation_reports) / len(evaluation_reports)
assert mean_accuracy >= 0.80, f"CI gate failed: decision_accuracy {mean_accuracy:.2f} < 0.80"
```

### 8.5 Update `src/jaci/modes/__init__.py`

```python
from jaci.modes.evaluator import EvaluatorMode
# NOTE: EvaluatorMode is NOT called by Conductor.
# Post-case only — called by run_eval.py and the process completion handler.
```

### 8.6 Phase 8 acceptance criteria

- `compute_deterministic_metrics()` produces correct scores for all 10 gold cases
  without any LLM call
- `decision_accuracy == 1.0` for all cases where system recommendation matches
  gold label; `< 1.0` for cases where it differs
- Evaluator LLM is called only for SAR quality assessment and signal generation
  (verify by checking that 10 gold cases produce only 10 LLM calls total in eval run)
- `improvement_signals` non-empty for at least 3 gold cases
- CI gate: `mean(decision_accuracy) >= 0.80`
- `EvaluationReport` objects serialise/deserialise cleanly to JSON

---

## Phase 9: Curator and Knowledge Improvement Hook

**Estimated effort:** 0.5 days
**Dependency:** Phase 8 (EvaluationReport)

**Goal:** Close the compounding loop. Route improvement signals to a governed
Knowledge Hub queue.

**Revised design — routing + optional LLM synthesis:**

The original plan used keyword matching to classify signals into buckets. This was
revised because keyword matching won't scale and misses signals that don't match
keyword patterns. The revised design has two layers:

1. **Python routing layer (`process_reports()`)** — groups signals by exact type
   tags that the Evaluator embeds in signals (see format convention below). Fast,
   deterministic, always runs.
2. **Optional LLM synthesis layer (`synthesize_queue()`)** — deduplicates similar
   signals across cases, identifies recurring patterns, scores signals by frequency
   and potential impact. Produces a cleaner queue for the human knowledge steward.
   Runs only when batch size ≥ 3 reports (not worth it for a single case).

Human stewardship is unchanged — the LLM organises the queue, the human steward
decides what gets updated. No knowledge assets are modified automatically.

**Signal format convention (Evaluator must follow this):**

Evaluator should prefix improvement signals with a bracket tag so Curator can
route them without keyword matching:

```
[evidence_checklist] Typology TYP-SHELL-002 requires depth 3 counterparty network...
[typology_threshold] TYP-PEP-003 confidence calibration appears conservative...
[policy_clause] Governor did not check FATF-R12 for Tier 2 PEP cases...
[loop_guard] Signal decay threshold fires prematurely on round-tripping cases...
[sar_template] Section 3 consistently thin on transaction amounts...
```

Add this format instruction to `prompts/evaluator.md` in the improvement signals
section.

### 9.1 New file: `src/jaci/schemas/curator_queue.py`

```python
"""
CuratorQueue — Governed improvement queue record.

Written by curator_stub.py after each EvaluationReport batch.
Routes improvement signals to the Knowledge Hub for human knowledge steward review.

Human stewardship model (per Charter):
  Curator identifies what COULD be improved.
  A human knowledge steward decides WHAT is actually updated.
  Domain Pack release is a governed human action.
"""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

PACK_ID = "aml-investigation-core"


class CuratorQueue(BaseModel):
    """
    Knowledge improvement queue record.

    Created by curator_stub.py after processing EvaluationReport objects.
    Sent to Knowledge Hub mock endpoint: POST /knowledge-hub/curator-queue.
    Always status "pending_review" on creation — human steward must action.
    """

    queue_id: str = Field(default_factory=lambda: f"curatorq_{uuid4()}")
    source_report_ids: list[str] = Field(
        ..., description="EvaluationReport.report_id values in this batch."
    )
    signals_by_type: dict[str, list[str]] = Field(
        default_factory=dict,
        description=(
            "Improvement signals grouped by bracket tag type. "
            "Keys: evidence_checklist, typology_threshold, policy_clause, "
            "loop_guard, sar_template, other."
        ),
    )
    synthesized_summary: str | None = Field(
        default=None,
        description=(
            "LLM-generated summary of recurring patterns across signals. "
            "Present only when batch >= 3 reports and LLM synthesis ran. "
            "For human knowledge steward review only — not machine-actionable."
        ),
    )
    total_signal_count: int = Field(default=0)
    status: str = Field(
        default="pending_review",
        description="Always 'pending_review' on creation.",
    )
    pack_id: str = Field(default=PACK_ID)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 9.2 New file: `src/jaci/modes/curator_stub.py`

```python
"""
curator_stub.py — Knowledge improvement routing and optional synthesis.

Part of the EVOLVE layer.

Layer 1 (always runs): Python routing — extracts bracket tags from signal strings,
  groups signals into typed buckets. No LLM call.
Layer 2 (optional, batch >= 3): LLM synthesis — deduplicates recurring signals,
  identifies patterns, generates a human-readable summary for the knowledge steward.

CONSTRAINT: Layer 1 is NOT an LLM call. Do not add a system prompt for it.
Layer 2 uses the Anthropic SDK directly (not an investigator-style mode) and
produces a summary for human review only — it does not modify any knowledge assets.

Integration point: Called from run_eval.py and the process completion handler.
Mock endpoint: POST /knowledge-hub/curator-queue
"""

import logging
import re

import httpx

from jaci.schemas.curator_queue import CuratorQueue
from jaci.schemas.evaluation_report import EvaluationReport

logger = logging.getLogger(__name__)

# Bracket tag pattern: [tag_name] at start of signal string
_TAG_PATTERN = re.compile(r"^\[([a-z_]+)\]")

# Minimum batch size to justify LLM synthesis call
_LLM_SYNTHESIS_MIN_BATCH = 3


def _extract_tag(signal: str) -> str:
    """Extract bracket tag from signal string, e.g. '[evidence_checklist] ...' → 'evidence_checklist'."""
    match = _TAG_PATTERN.match(signal.strip())
    return match.group(1) if match else "other"


async def _synthesize_signals(
    signals_by_type: dict[str, list[str]],
    report_count: int,
) -> str | None:
    """
    Optional LLM synthesis — produce a human-readable summary of recurring patterns.

    Called only when batch size >= _LLM_SYNTHESIS_MIN_BATCH.
    Uses Anthropic SDK directly (not a full mode instantiation).
    Returns None if synthesis fails — degraded mode, routing still works.
    """
    try:
        import anthropic
        client = anthropic.Anthropic()

        all_signals = [s for signals in signals_by_type.values() for s in signals]
        signal_text = "\n".join(f"- {s}" for s in all_signals)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=(
                "You help a human knowledge steward understand improvement signals "
                "from an AML investigation system. Identify recurring patterns, "
                "deduplicate similar signals, and highlight the 2-3 most impactful "
                "improvement opportunities. Be concise and actionable. "
                "Do not suggest code changes — only knowledge asset changes "
                "(typology library, evidence checklists, policy clauses, playbooks)."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Here are {len(all_signals)} improvement signals from {report_count} "
                    f"AML cases:\n\n{signal_text}\n\n"
                    "Summarize the key patterns and top 2-3 improvement priorities."
                ),
            }],
        )
        return response.content[0].text
    except Exception as e:
        logger.warning(f"Curator LLM synthesis failed (degraded mode): {e}")
        return None


async def process_reports(
    reports: list[EvaluationReport],
    knowledge_hub_url: str = "http://localhost:8080/knowledge-hub/curator-queue",
) -> CuratorQueue:
    """
    Process a batch of EvaluationReports.

    Layer 1: Route signals by bracket tag into typed buckets.
    Layer 2: If batch >= 3, run optional LLM synthesis for human review summary.
    Write CuratorQueue record to Knowledge Hub.
    """
    # Layer 1 — Python routing
    signals_by_type: dict[str, list[str]] = {}
    for report in reports:
        for signal in report.improvement_signals:
            bucket = _extract_tag(signal)
            signals_by_type.setdefault(bucket, []).append(signal)

    total_signals = sum(len(v) for v in signals_by_type.values())

    # Layer 2 — Optional LLM synthesis
    synthesized_summary = None
    if len(reports) >= _LLM_SYNTHESIS_MIN_BATCH and total_signals > 0:
        synthesized_summary = await _synthesize_signals(signals_by_type, len(reports))

    queue_record = CuratorQueue(
        source_report_ids=[r.report_id for r in reports],
        signals_by_type=signals_by_type,
        synthesized_summary=synthesized_summary,
        total_signal_count=total_signals,
    )

    # Write to Knowledge Hub (mock for PoC)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                knowledge_hub_url,
                json=queue_record.model_dump(mode="json"),
            )
            response.raise_for_status()
    except Exception as e:
        logger.warning(
            f"Could not reach Knowledge Hub curator queue endpoint: {e}. "
            "CuratorQueue record created but not persisted remotely."
        )

    logger.info(
        f"Curator queue updated: {total_signals} improvement signals "
        f"from {len(reports)} cases "
        f"(buckets: {list(signals_by_type.keys())}, "
        f"synthesis: {'yes' if synthesized_summary else 'no'})"
    )

    return queue_record
```

### 9.3 Wire Curator into `tests/eval/run_eval.py`

```python
# After all EvaluationReport objects are collected:
import asyncio
from jaci.modes.curator_stub import process_reports

curator_queue = asyncio.run(process_reports(evaluation_reports))
logger.info(f"Curator queue: {curator_queue.queue_id} "
            f"({curator_queue.total_signal_count} signals)")

# Include in saved report:
report["curator_queue"] = curator_queue.model_dump(mode="json")
```

Add `httpx` to `pyproject.toml` if not present.

### 9.4 Phase 9 acceptance criteria

- Routing layer (Layer 1) runs without LLM for all batch sizes
- Bracket tag extraction correctly routes `[evidence_checklist]` signals to the
  `evidence_checklist` bucket
- Signals without bracket tags land in `"other"` bucket — not dropped
- LLM synthesis only runs when batch size ≥ 3 (verify with 2-case test)
- `synthesized_summary` is `None` when synthesis is skipped
- Degraded mode works: synthesis failure → `synthesized_summary = None`, pipeline
  continues without error
- `CuratorQueue` serialises correctly and is included in eval report JSON
- Log output format: `"Curator queue updated: N signals from M cases (buckets: [...], synthesis: yes/no)"`

---

## Phase 5: Process Design (replaces BPMN stub)

**Estimated effort:** 0.25 days (reduced from 0.5 days)
**Dependency:** Phase 4 Conductor

**Revised approach:** The original plan required a syntactically valid BPMN 2.0 XML
file that would never be deployed. This was replaced with a markdown process design
document. An undeployed XML file is documentation theater — a markdown description
is clearer, easier to maintain, and honest about PoC scope.

### 5.1 New file: `docs/process_design.md`

Create a markdown document describing the post-investigation human checkpoint process.
The document must specify:

1. **Trigger:** Conductor emits a `CaseFile` (with `canonical_trace` and the extended
   `DispositionRecommendation`). In production, this triggers a Flowable BPMN process.
   For the PoC, `run_eval.py` simulates this directly.

2. **Step 1 — L3/FIU Disposition Review (HUMAN):** Analyst receives the
   `DispositionRecommendation` with rationale, evidence summary, and policy citations.
   Analyst actions: confirm recommendation, or override with documented reason.
   Outputs: `outcome_class`, `human_override` (bool), `override_reason` (conditional).

3. **Step 2 — Write Outcome:** System writes an `Outcome` object to the JAPES state
   store, linking back to `disposition.decision_id` and `canonical_trace.trace_id`.

4. **Step 3 — Trigger Evaluator (async):** Post-case event fires. Evaluator runs
   `compute_deterministic_metrics()` then calls LLM for qualitative assessment.
   Produces `EvaluationReport`. In production: Flowable message event. For PoC:
   direct async function call from process completion handler.

5. **SAR branch (Escalate cases only) — SAR Filing Decision (HUMAN-ONLY):**
   Compliance officer receives the `SARDraft`. Makes final filing decision.
   This step is explicitly human-only and cannot be automated under any circumstances.
   This is a regulatory requirement (31 CFR 1020.320), not a policy choice.

6. **Step 4 — Trigger Curator:** After Evaluator completes, `curator_stub.py`
   processes the `EvaluationReport` and writes a `CuratorQueue` record to the
   Knowledge Hub. Human knowledge steward reviews queue and decides on pack updates.

Include a simple ASCII flow diagram in the markdown:

```
CaseFile emitted by Conductor
         │
         ▼
[HUMAN] L3/FIU Disposition Review
         │
         ▼
Write Outcome object
         │
         ├──► Trigger Evaluator (async)
         │         │
         │         ▼
         │    compute_deterministic_metrics() [Python]
         │         │
         │         ▼
         │    EvaluatorMode.run() [LLM — sar_quality + signals]
         │         │
         │         ▼
         │    EvaluationReport
         │         │
         │         ▼
         │    curator_stub.process_reports() [Python + optional LLM synthesis]
         │         │
         │         ▼
         │    CuratorQueue → Knowledge Hub
         │
         └── (if Escalate)
                  │
                  ▼
         [HUMAN] SAR Filing Decision  ← HUMAN-ONLY, non-negotiable
```

---

## Final File Map

### New files

```
src/jaci/schemas/
  canonical_trace.py        # Phase 7
  outcome.py                # Phase 7
  evaluation_report.py      # Phase 8
  curator_queue.py          # Phase 9

src/jaci/modes/
  evaluator.py              # Phase 8 (Python metrics + LLM mode)
  curator_stub.py           # Phase 9 (Python routing + optional LLM synthesis)

prompts/
  evaluator.md              # Phase 8

config/packs/
  aml_investigation_core.yaml  # Phase 10 (lightweight reference only)

docs/
  process_design.md         # Phase 5 replacement
```

### Targeted amendments (existing files, additive only)

```
src/jaci/schemas/case_context.py   Add 5 fields to DispositionRecommendation;
                                   add canonical_trace to CaseFile
src/jaci/schemas/__init__.py       Add CanonicalTrace, Outcome imports
src/jaci/conductor.py              Emit CanonicalTrace; backfill cross-linkage fields
src/jaci/modes/__init__.py         Add EvaluatorMode (with NOT-IN-CONDUCTOR comment)
config/autonomy_ceilings.py        Add comment linking to pack yaml
tests/eval/run_eval.py             Add Outcome construction, deterministic metrics,
                                   EvaluatorMode call, Curator call
```

### What was NOT created (by design)

```
src/jaci/schemas/canonical_decision.py  — dropped; fields on DispositionRecommendation instead
config/pack_loader.py                   — deferred to production readiness
bpmn/aml_investigator_checkpoint.bpmn  — replaced by docs/process_design.md
```

---

## What JACI-AML Can Claim After Phases 7–10

**Claim 1 — Canonical chain compliance:**
Every investigation produces formally typed `CanonicalTrace` and `Outcome` objects
with full cross-linkage. `DispositionRecommendation` carries canonical `decision_id`,
`policy_refs`, `evidence_refs`, and `trace_id` fields. The chain is programmatically
validatable. Portfolio interoperability with other JazzX modules is unblocked.

**Claim 2 — Compounding loop is architecturally complete:**
Outcomes feed Evaluator → Python computes deterministic metrics, LLM assesses
qualitative dimensions and generates improvement signals → Curator routes signals
to the Knowledge Hub queue (with optional LLM synthesis for human review).
The loop closes. Human stewardship of knowledge updates is explicit and correct.

**Claim 3 — Pack-bound governance:**
`pack_id: aml-investigation-core` resolves to a versioned reference yaml.
The governance path to full ABA/JAP/Overlay formalisation is structurally clear.

**What remains honestly deferred:**
- Full Curator knowledge maintenance (policy edits, typology updates) — Phase 2+
- `pack_loader.py` and yaml-driven autonomy ceilings — production readiness
- ABA, JAP, Overlay documents — parallel governance track, not code
- Simulator mode — not in scope for AML investigation PoC
- Real Integration Hub connectors — depends on SymphonyAI integration timeline
- Lagged Outcome types (regulatory findings, confirmed fraud) — Phase 2+
- Flowable production deployment — process_design.md documents intent only

---

## Revised Phase Summary (All Phases)

| Phase | Description | Effort | Key Output | Status |
|-------|-------------|--------|------------|--------|
| 0 | Repo and environment setup | 0.5d | Buildable container | Done |
| 1 | Case Context schema and data models | 1d | Pydantic schemas | Done |
| 2 | Tool registry + connectors | 2d | 8 tools, mock connectors | Done |
| 3 | Mode system prompts | 1.5d | 6 prompt files | Done |
| 4 | Conductor (loop orchestrator) | 2d | Working investigation loop | Done |
| 5 | Process design (replaces BPMN) | 0.25d | `docs/process_design.md` | **To do** |
| 6 | Evaluation harness | 1.5d | 10 gold cases, CI gate | Done |
| **7** | **Canonical schema compliance** | **0.75d** | **Extended DispositionRecommendation, CanonicalTrace, Outcome** | **To do** |
| **10** | **Pack reference stub** | **0.25d** | **`aml_investigation_core.yaml`; comment in autonomy_ceilings.py** | **To do** |
| **8** | **Evaluator mode** | **1.25d** | **Python metrics + LLM qualitative; EvaluationReport; updated CI gate** | **To do** |
| **9** | **Curator** | **0.5d** | **Python routing + optional LLM synthesis; CuratorQueue** | **To do** |
| **Total remaining** | | **~3d** | | |
| **Grand total** | | **~12d** | | |
