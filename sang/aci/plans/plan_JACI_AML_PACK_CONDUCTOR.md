# AML on a pack-declared conductor

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: done 2026-10-05 (phases 2-5), but for case_09's deadline-guard iteration cap (a pending japes
change). Commits 32085d6..f6f6e04. First Plato eval: disposition 82% (9/11) vs the in-process 80%,
typology 82%, $0.53; case_09 waits on the iteration cap, case_11 closes where it should escalate.

Asked for in the PR #5 review round: move AML from jaci's
`AMLConductor` to the generic, config-driven path DSCR now uses (`conductor:` block in the pack,
run by japes / Plato).

## Where AML is today

- `scenarios/aml/conductor.py:AMLConductor` already runs japes' generic investigation pipeline
  (`build_investigation_pipeline` / `run_investigation_pipeline`), but jaci wires it in Python:
  mode objects, an `InvestigationSpec`, a SAR-deadline guard (`_deadline_imminent`), a narrator gate
  (governor approved and ESCALATE), a persist step override (`_step_persist`: CanonicalTrace, the
  disposition↔trace links, the canonical decision, checkpointing), a governor remap to jaci's
  `GovernorDecision`, and its own `CaseFile` assembly. It also records per-mode token usage.
- The AML "pack" is a stub: `config/packs/aml_investigation_core.yaml` (reference only, its own
  header says not loaded at runtime) plus `aml_investigation_core/mode_tuning/`. No
  `pack_manifest.yaml`, no JSON schemas, no `evidence_tools.yaml`, no fixtures in the pack. Policies
  live in `scenarios/aml/policies/policies.yaml`; evidence comes from `scenarios/aml/tools/`
  mock connectors keyed by a thread-local active case id (`tests/fixtures/case_fixtures.py`).
- Callers of `AMLConductor`: `japes_handler.py` (server/queue `investigate`), the AML demo page,
  the eval harnesses (`run_eval.py`, `run_eval_anthropic.py`, `quick_eval.py`,
  `test_evolve_validation.py`), integration tests. All consume jaci's `CaseFile`
  (`disposition`, `case_context`, `canonical_trace`, `sar_draft`).

## Target

Same shape as dscr-core 0.2.3: `config/packs/aml_investigation_core/pack_manifest.yaml` declares a
`conductor_pipeline` (investigation → governor → `human_checkpoint` SAR_FILING_APPROVAL → narrate,
gated on `decision_in: [escalate]`), with the pack owning schemas, evidence tools + fixtures,
policies and mode tuning. AML runs on Plato (`POST /packs/aml-investigation-core/runs`), the page
and handler read japes' `CaseResult`, and `AMLConductor` is retired.

The human checkpoint is a better fit than today's code: SAR filing is human-only by regulation, and
the pipeline would now pause for that decision instead of leaving it implicit.

## Gaps

japes closed its side on v2.6.1 (486a5c91, 3ba66119, f92ce422; not yet on `plato`, which will be
pushed before jaci is):

| Need | Status |
|---|---|
| SAR-deadline guard (gold case_09) | japes: `deadline: {field: sar_deadline, within_hours: 48}` on the investigation step; `CaseResult.investigation` says `status: guard_fired`, `guard_reason: deadline`. |
| Per-mode token usage and cost | japes: `CaseResult.usage = {modes: {mode: {model, calls, ...tokens, cost_usd}}, total}`, priced per call. |
| Model sweeps for evals | japes: eval plane only, `run_case(mode_overrides=...)` / the `case_run` eval entity's `config["modes"]`. |
| Per-case evidence | already supported: evidence_tools `source: fixture`, keyed by subject id. |
| SAR filing approval, narrator gate | already supported: `human_checkpoint`, `narrate` gate `decision_in: [escalate]`. |

jaci's side: the pack (manifest, generated JSON schemas for the alert input, hypothesis and
`DispositionRecommendation`, `evidence_tools.yaml` + per-case fixtures moved out of
`tests/fixtures/case_fixtures.py`, policies), a `scenarios/aml/plato_review.py` adapter over
`CaseResult` (the DSCR pattern; `CanonicalTrace` from Plato's persisted trace), the page, and the
eval harness on Plato's eval plane.

## Phases

1. **japes** (done on v2.6.1, see above).
2. **Author the pack**, publish to local Plato, run one gold case end to end.
3. **Page and adapter** on Plato; the page runs only on Plato (no in-process path, as DSCR).
4. **Eval harness** on Plato's eval plane (`case_run` entity, `config["modes"]` for model sweeps,
   cost from `usage`); match the recorded in-process baseline (exp_015, 80% disposition accuracy).
5. **Retire** `AMLConductor`, the in-process mock connectors and tool registry, the handler's
   `investigate` operation, and the in-process eval scripts.

## Decisions (2026-10-05)

1. No in-process AML path, not even during the eval comparison: jaci is a PoC showcase, never
   shipped; scenarios run on Plato, as each scenario's own production app will through
   jazzx-plato-client. The in-process 80% (exp_015) stays as the recorded baseline to match.
2. Retire the handler's `investigate` operation: Plato's case-run route serves it.
3. Gold-case evidence ships with the pack as fixtures, keyed by subject id.
