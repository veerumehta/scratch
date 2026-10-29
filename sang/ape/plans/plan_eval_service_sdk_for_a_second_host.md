# Plan: what in Plato's eval code belongs in the SDK for a second host (sonnet-runtime, 2026-10-29)

Audit and plan only, no build, no spend. Read: `plato/api/eval.py` (362 lines), the SDK modules it mounts (`jazzx_sdk/server/eval_api.py`,
`jazzx_sdk/evaluation/*`, `jazzx_sdk/pack/eval_invoker.py`, `rule_trial.py`), the Plato eval page's baseline calls, and, read-only,
`policy-workbench` `JAPES_V2` `backend/app/services/eval_runner.py` (705 lines) with the names of its sibling services.

## 1. Finding: Plato's eval surface is already mostly SDK

`plato/api/eval.py` is wiring. The datasets, experiments, scorers and optimization routers (`create_*_router`), the runner
(`ExperimentRunner`), the stores (`Db*Store`), the invokers (`AssistantInvoker`, `CaseRunInvoker`, `AdjudicationInvoker`,
`RuleTrialInvoker`, `PackAssessmentInvoker`), baselines per entity type (`set_baseline`/`get_baseline`, `eval/baselines/...`),
comparisons (`experiment_comparison`, `variants`, `path_comparison`), input overrides (`evaluation/input_overrides.py`) and the
judge cache are all in `jazzx_sdk`. A second host can already import them. The Plato-only part is the composition, listed below.

## 2. Plato-only logic in `plato/api/eval.py`, and where it goes

| Plato code | What it is | Belongs in the SDK? |
|---|---|---|
| `_invokers(tenant)` (about 60 lines): builds the entity-to-invoker table, `pack_for` (host pin via `pinned_version`, `domain_pack_record`, `MaterializedPacks`), `draft_for`, `proposals_for`, the external-adjudicator switch | The composition every host of pack evaluation repeats | Yes: `jazzx_sdk.pack.eval_invoker.build_eval_invokers(db, tenant_id, runtime, pack_store_for, pinned_version, agents, documents_for, python_executor, adjudicator_url)`; Plato passes its pin lookup and the env value |
| `_modes_for(pack)`: `sdk_mode_factory(SimpleNamespace(runtime=...))` | Glue to give a case run its modes | Yes: a named function next to `sdk_mode_factory` taking `(agents, fabric)`; the `SimpleNamespace` stops being a contract |
| `_runner/_catalog/_builtins/_optimizer` (per-tenant caches in dicts: runners, judge-cached scorers, optimization runners) | A tenant registry | Yes: one `TenantEvalServices` (runner, catalog, optimizer per tenant, built once) in `jazzx_sdk.server`, so a host mounts routers over `services.runner_for` |
| `_fix_router` (rule fix `expand` and `redo`, about 55 lines; `fix_proposal`, `latest_trial`, `retrial_spec` are SDK) | A route plus its role gates | Yes: `create_rule_fix_router(...)` in `jazzx_sdk.server` beside the other eval routers; the gates come in as arguments |
| `_require_author`, `_reviewer_starts_adjudication` (use `AuthoringRoles`, an SDK class) | Role policy for starting a costly experiment | Yes, as `before_start` defaults of the experiments router for the pack entities (one place; Plato overrides nothing) |
| `backend_optimizers()` (reads `PLATO_OPTIMIZER_REFLECTION_MODEL`, checks mlflow) | Optional searches | Split: the search factory takes the model as an argument in `evaluation.backends.mlflow.prompt_optimizers`; Plato keeps the env name only |
| `eval_authoring_chat_assistant` | A built-in assistant over the tenant's experiments | Mostly SDK already (`eval_authoring_builtin`); the `describe` closure over `runtime.agent_for` moves with a `runtime` protocol |
| tenant resolution, write and read gates, identity, route prefix | Host policy | No: stays in Plato (thin routes) |

After this, `plato/api/eval.py` is about 80 lines: tenant, gates, prefix and one `TenantEvalServices(...)` plus the mounts. Size: 2 days,
all tests exist for the pieces (the move keeps behavior), no spend.

## 3. What the workbench runner is, and what it duplicates

`eval_runner.py` does not use Plato's eval. It is a client of the *platform's* Evaluation Studio (a separate service: `eval_service`
over HTTP, the knowledge hub, `macer`): per Reasoner Send it creates a one-case dataset (the service copies the loan), starts the
experiment when the copy is ready, polls it, scores `macerStatus` as success, and records a `MacerRun` row. So it duplicates
*concepts* the SDK owns, not SDK code, and a host on the SDK would drop the HTTP client and use `ExperimentRunner`:

| Workbench logic | SDK today | Gap to close for a second host |
|---|---|---|
| Baseline per (loan, JTBD entity): the loan's current baseline, a baseline of the same entity wins, else the newest (`baseline_run`, table `MacerBaseline`) | Baseline per entity type only (`eval_baseline`, `GET eval/baselines/{entity_type}`) | A baseline scoped to a subject: optional `subject` on `set_baseline`/`get_baseline` and one selection rule (`select_baseline(entity, subject, prefer_entity)`: same entity first, else newest). The per-loan rule is a generic "per case" rule |
| A comparison with no baseline is a completed run with an error string matched by suffix (`no_baseline()` matches the scorer's message) | A comparison against a missing baseline raises | A typed `no_baseline` result on the comparison and the experiment summary instead of text matching |
| A dataset of one case from a record (`start_eval_run`) | `Dataset` of cases | A helper `single_case_dataset(entity, case, expected=...)` |
| Experiment status vocabulary of the remote service (ended: failed, cancelled, error, timeout, aborted...; in progress: pending, queued, running, scoring...) | One `ExperimentStatus` enum | None for the SDK; this list is the remote service's. A host switching to the SDK deletes it |
| A row left in "starting" is retried after a stale window (replica restarted mid-start) | Not verified: I did not read `ExperimentRunner.start`'s recovery of a start interrupted by a restart | Check, and if missing add the same stale-start retry (the case-run side has heartbeat and restart) |
| Outcome extraction from an experiment's output (score, passed, report, clone collection, MLflow run id) | Experiment result views and scorers | Probably a read model (`ExperimentOutcome`) so a host does not parse `evaluation_result` itself; confirm against `experiments.py` |
| Findings compare and Macer-specific scoring (`findings_compare.py`, `macer_compare.py`) | `RuleCorrectionScorer`, comparisons over rule outcomes | Host (macer) logic; not the SDK's |

Not found in Plato, so not audited: "stage links for the Runs step" (they are in the workbench UI; Plato's `runs.html` has none) and an
"assistant eval overrides" route in `plato/api` (the overrides are `evaluation/input_overrides.py` and the assistant invoker, both SDK).

## 4. Order
1. The composition move (section 2), since it changes no behavior and is what a second host first needs: 2 days.
2. Subject-scoped baselines with the selection rule and the typed no-baseline result: 1 to 1.5 days, with a migration for the
   baseline table (`subject` nullable, so existing rows are entity-wide).
3. `single_case_dataset` and, if the read confirms a gap, the outcome read model and the stale-start retry: 1 day.
The layering rule holds throughout: logic in the SDK, Plato routes thin, the workbench a host that supplies its own tenant, gates and
pin lookup. Pinned dependency: the workbench pins `japes>=2.6.4`; every addition is additive, so it can take them on upgrade.

## 5. Not decided
Whether the workbench moves from the platform's Evaluation Studio to the SDK runner at all (a product decision, not an SDK one); until
it does, items 2 and 3 are the SDK's own generalization, not requested work.
