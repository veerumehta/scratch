
---

## Charter Alignment — Next Work (Phases 7, 10, 8, 9)

**Status as of April 2026:** Phases 0–6 complete. Three charter gaps remain open.
The full execution plan is in `docs/CHARTER_ALIGNMENT_PLAN.md` (v2, revised) —
read that document before starting any of the phases below.

**Execute in this order: Phase 7 → Phase 10 → Phase 8 → Phase 9**

### Three gaps being closed

**Gap 1 — EVOLVE layer absent (Phases 8 + 9):**
No Evaluator mode, no Curator. Compounding loop does not close.

**Gap 2 — Pack governance orphaned (Phase 10):**
`pack_id` is a floating string constant with no resolvable parent reference.

**Gap 3 — Canonical cross-linkage partial (Phase 7):**
`DispositionRecommendation` has no `policy_refs`, `evidence_refs`, or `trace_id`.
No `CanonicalTrace` or `Outcome` schemas exist.

### Key design decisions (v2 revised from original plan)

1. **No `CanonicalDecision` wrapper class.** Extend `DispositionRecommendation`
   directly with `decision_id`, `policy_refs`, `evidence_refs`, `trace_id`, `pack_id`.
   Wrapper violated DRY and created dual source of truth.

2. **Evaluator uses Python for deterministic metrics.** `compute_deterministic_metrics()`
   computes `decision_accuracy`, `evidence_efficiency`, `policy_compliance`,
   `loop_efficiency` in Python — no LLM. LLM only handles `sar_quality` and
   `improvement_signals`. One LLM call per case, not five.

3. **Curator has two layers.** Layer 1: Python routing by bracket tag
   (`[evidence_checklist]`, `[policy_clause]`, etc). Layer 2: Optional LLM synthesis
   for deduplication/prioritization when batch ≥ 3 reports. Human steward still
   makes all knowledge update decisions.

4. **Pack governance is a lightweight yaml reference only.** `aml_investigation_core.yaml`
   anchors the `pack_id` string and documents autonomy ceiling values. No
   `pack_loader.py`, no startup validation. `autonomy_ceilings.py` stays hardcoded
   with a comment linking to the yaml. Full loader is production readiness work.

5. **BPMN replaced by `docs/process_design.md`.** Undeployed XML is documentation
   theater. Markdown with ASCII flow diagram is clearer and honest about PoC scope.

### Hard constraints (must not be violated)

- Do not modify Phases 0–6 except where `CHARTER_ALIGNMENT_PLAN.md` marks
  "TARGETED AMENDMENT TO EXISTING FILE"
- Evaluator must never be called inside the live investigation loop
- Curator Layer 1 routing is NOT an LLM call
- SAR filing remains human-only — design invariant
- Gold cases are reused in Phase 8 — no second eval dataset

### New files to create

```
src/jaci/schemas/canonical_trace.py   Phase 7
src/jaci/schemas/outcome.py           Phase 7
src/jaci/schemas/evaluation_report.py Phase 8
src/jaci/schemas/curator_queue.py     Phase 9
src/jaci/modes/evaluator.py           Phase 8
src/jaci/modes/curator_stub.py        Phase 9
prompts/evaluator.md                  Phase 8
config/packs/aml_investigation_core.yaml  Phase 10
docs/process_design.md                Phase 5 replacement
```

### Existing files with targeted amendments

```
src/jaci/schemas/case_context.py  Add 5 fields to DispositionRecommendation;
                                  add canonical_trace to CaseFile
src/jaci/schemas/__init__.py      Add CanonicalTrace, Outcome imports
src/jaci/conductor.py             Emit CanonicalTrace; backfill cross-linkage fields
src/jaci/modes/__init__.py        Add EvaluatorMode (with NOT-IN-CONDUCTOR comment)
config/autonomy_ceilings.py       Add comment linking to pack yaml
tests/eval/run_eval.py            Add Outcome construction, deterministic metrics,
                                  EvaluatorMode, Curator call
```

### NOT created (by design)

```
src/jaci/schemas/canonical_decision.py  — dropped; fields on DispositionRecommendation
config/pack_loader.py                   — deferred to production readiness
bpmn/aml_investigator_checkpoint.bpmn  — replaced by docs/process_design.md
```
