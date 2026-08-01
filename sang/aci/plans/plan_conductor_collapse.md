# Plan: collapse jaci conductors onto `japes` `ConductorEngine`

**Status:** in progress (started on `CIConductor`)
**japes dependency:** `jazzx_sdk.conductor.ConductorEngine` (Stage 2, japes commit `6dca222`) — editable install.

## Goal

Each pack conductor's hand-written `run()` (the `while` loop + step sequencing + guards)
moves into `japes` `ConductorEngine`. The pack keeps only:
- its `ConductorPipeline` descriptor (already loaded from `config/packs/*/pipelines.yaml`),
- a map of `{step_id: component}` (small methods lifted from `run()`),
- a per-loop convergence predicate.

The **same descriptor now both renders (`describe()`) and runs**.

## Engine contract (recap)

```python
ConductorEngine(pipeline, {step_id: component}, loop_converged={loop_id: predicate})
run = await engine.run(context=ctx)
# run.emitted[step_id], run.emitted_for(step_id), run.steps, run.iterations,
# run.status (complete|halted), run.loop_status[loop_id] (converged|max_iterations|halted)
```

- `component(state)` → sync/async; `state.context` is the pack ctx, `state.emitted` the
  step→object map, `state.iteration` the current loop iteration; return the emitted object.
- A loop group repeats its member steps until `loop_converged[loop_id](state)` is True or
  `Loop.max_iterations`. Unwired steps are `skipped`. A component sets `state.halt` to stop.

## The parity-critical decision

The engine runs the **whole loop body then checks the predicate** (vs the original
`while ctx.loop_status == ACTIVE` at the top). To keep exact parity, **each loop component
guards on `ctx.loop_status`** and no-ops once the loop is no longer ACTIVE; the predicate is
then literally the original loop condition:

```python
loop_converged={"investigation": lambda s: s.context.loop_status != LoopStatus.ACTIVE}
```

## CIConductor mapping (`scenarios/ci_spread/conductor.py`)

Step ids from `config/packs/ci-spread-core/pipelines.yaml::credit_analysis`:

| step id | component | source block in run_analysis |
|---|---|---|
| `document_intake` | `_step_document_intake` | Phase 0 (`_run_document_intake`) + `intake_mode` |
| `entity_extraction` | `_step_entity_extraction` | Phase 1 (`_run_entity_extraction`) |
| `investigator` (loop) | `_step_investigator` | investigator.run + apply_hypothesis_update + convergence guard → sets `ctx.loop_status` |
| `evidence_fulfillment` (loop) | `_step_evidence` | tool_registry.execute per request (guarded) |
| `verifier` (loop) | `_step_verifier` | verifier.run + apply_verifier_report (guarded) |
| `sentinel` (loop) | `_step_sentinel` | sentinel.run + guard + iteration checkpoint (guarded) |
| `playbook` | `_step_playbook` | playbook_expert.execute(recommend) |
| `reasoner` | `_step_reasoner` | synthesizing checkpoint + reasoner.run + attach guidance_refs (halt on fail) |
| `policy_check` | `_step_policy` | policy_expert.execute(check_compliance) + append concerns |
| `governor` | `_step_governor` | governor.run + block handling |
| `narrator` | `_step_narrator` | narrator.run if approved |
| `evaluator` | `_step_evaluator` | compute_deterministic_metrics if ground truth → EvaluationReport |
| `persist` | `_step_persist` | CanonicalTrace.for_pack + put_trace + put_canonical_case_file + final checkpoint |

`run_analysis` shrinks to: build ctx → open checkpoint → `ConductorEngine(...).run(ctx)` →
map `loop_status==max_iterations` to `GUARD_FIRED` → build `CaseFile` from `ctx` +
`run.emitted_for("reasoner")` + `run.emitted_for("evaluator")` + `run.iterations`.

### Semantic decisions (review these)

1. **Body-then-check** → solved by `loop_status` guards on loop components (exact parity).
2. **Checkpoints** fold into components (`sentinel`=iteration, `reasoner`=synthesizing,
   `persist`=final); "run opened" stays in `run_analysis`.
3. **Iteration counter** — `ctx.iteration_count = state.iteration` set in `_step_investigator`.
4. **CanonicalTrace stays pack-side** — built in `_step_persist`; the engine's `ConductorRun`
   is the generic record, the pack owns the v1.5 canonical artifact (mode/actor/autonomy).

## Steps to walk

1. [x] `CIConductor`: add `_components()` + the `_step_*` methods (lift bodies verbatim).
2. [x] Rewrite `run_analysis` to drive `ConductorEngine`; `run_spread` kept as-is.
3. [x] Offline orchestration parity test (`tests/unit/test_ci_conductor_engine.py`) — mocks
       at the mode/expert boundary, real engine + real `CIContext`; covers the convergence
       path (3 iters) and the max-iter→guard path (6 iters). 2 passed; 250 unit tests still
       import; the 28 ci/spread tests pass.
   - [x] **LLM eval before/after on case_01 (real OpenAI via `.env`):** original and collapsed
       BOTH fail the case identically — approval 100% / amount 100% / advance_rate failing
       (pre-existing golden-case gap, not a regression). Decision parity holds; the collapsed
       run executes the full pipeline end-to-end. Only diff = reported iterations (orig 2 vs
       new 1 = the documented off-by-one; both run one actual investigation pass).
   - Fix landed while walking: the engine now respects the runtime `max_iterations`
       (`CI_PIPELINE.model_copy` overrides the descriptor's loop cap), so the eval's
       `max_iterations=1` is honored. **Full 5-case before/after worth running before merge.**
4. [ ] Repeat for `run_spread` (the `spread` pipeline) once the eval confirms parity.
5. [ ] Generalize: AML / KYC / CRE / Earnings conductors.
6. [ ] Eval harness `conductor_factory` → build a generic engine-backed conductor from a
       descriptor + component registry (one graded execution path).

### Off-by-one note (intentional)
The former loop set `iteration_count` to `max+1` on the max guard (incremented before the
`> max` break), so `CaseFile.iterations` was 7 for a 6-iteration run. The engine reports the
true count (6). Only the non-converging max-iter path differs; the convergence path is exact.

## Caveat

Parity must be proven against jaci's own test suite. The two spots to watch: loop-guard
timing (the converging iteration's evidence/verify/sentinel must no-op) and checkpoint folding.
