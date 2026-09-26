# Eval control plane in the SDK; Plato and eval-service as thin owners

**Status:** proposed, 2026-09-25. Read against japes `24a3edba` (branch `v2.5.5`) and eval-service
`b812172`. Nothing built.

**Prior art read:** `Plato/Plato_Service_Architecture_and_Build_Plan.md` §5.2-5.4 (staging,
single-writer rule), `Plato/plan_JAPES_PLATO_SERVICE.md` Phase 6, `plan_policy_jtbd_extraction.md` §6
(the pattern this copies), `engineering_queue.md`, `note_LEARNING_PIPELINE_ASSESSMENT.md`, memory on
the 2026-07 eval-service absorption rounds.

## 0. The ask and the shape

Plato should offer what eval-service offers, built on the SDK, so that eval-service can eventually be
retired. Same shape as policy authoring (decided 2026-09-24): **the SDK owns the engine, the stores
and the router factories; Plato and eval-service are shells** that supply identity, config, the
invoker for the entities they host, and a UI. Every router factory mounts in a bare FastAPI app in
its test, with no Plato import.

Retirement is then a sequence of "eval-service mounts the SDK router for resource X and drops its
own", ending with nothing left in eval-service that Plato cannot host.

## 1. What eval-service is (b812172)

About 110 endpoints, 43k lines. Split:

**Generic core, the thing to own in the SDK:**
- testcases; datasets versioned with lineage (fork on rebind, version bump on membership change,
  status draft/published/archived, status history)
- experiments (dataset x entity x scorers/template x config overrides) and per-case runs, with
  status lifecycle, summary, rerun-as-clone, export
- scorer catalog + one-shot scoring; eval templates; adjudicator
- custom scorers as data (natural-language judge, python script, agent judge), immutable revisions
- paired baseline/candidate comparison; per-entity baseline pointer
- prompt optimization as a job (GEPA via `mlflow.genai`), history/compare, promote winner
- read-only MCP exposure of the scorer surface

**Plumbing, not SDK:**
- kernel and Flowable invokers, completion webhooks, pollers, deadline backstop
- Knowledge Hub collection clone per case; MACER clone-remap hook and metrics loader
- Juno feedback analysis, assist-edit, insights chips
- kernel-compat feedback router; `/agents/*` prompt and feedback patches on kernel
- MLflow as store of dataset content, traces and baselines; Azure queue worker

**Feedback** (canonical API, similarity via pgvector, duplicates, status history, config) is its own
system and is gated separately (§5).

## 2. What the SDK already has

| capability | SDK today |
|---|---|
| scorer contract, registry, composite, LLM judge, adjudicator | `evaluation.scorers` |
| operational scorers over `CanonicalTrace` | `evaluation.operational` |
| templates as data | `evaluation.templates` (`EvalTemplate`, registry) |
| scorer as tool schema | `evaluation.scorers.as_tool_schema` |
| case-set versioning, diff | `evaluation.golden_cases.versioning` (`CaseSetVersion`, `diff_case_sets`) |
| run record + store seam | `evaluation.experiment` (`ExperimentRun`, `ExperimentStore`; MLflow backend only) |
| harness over a conductor | `evaluation.harness` |
| run history slicing | `evaluation.history` (reads JSON files) |
| prompt optimization loop, pluggable optimizer | `evaluation.optimization` |
| prompt registry + aliases, durable | `evaluation.prompt_registry{,_db}` |
| assistant as `predict_fn` | `agents.interactive.optimize.interactive_predict_fn` |
| feedback types, store, sink to eval-service | `evaluation.feedback`, `feedback_db`, `feedback_sink` |
| trace lookup route | `server.trace_routes` |
| resilient runs on the queue runtime | `runs`, `server.run_routes` |
| wire contracts shared with eval-service | `jazzx_eval_contracts` |

## 3. SDK gaps, which are the work

1. **Durable eval records.** `DatasetStore` / `ExperimentStore` protocols with `Db*` implementations
   on `fabric.db`, tables prefixed `eval_` (collision-proof against eval-service, as `japes_feedback`
   is). Dataset identity = content digest of its case set (`jazzx_sdk.digest`), so a version is
   reproducible, not a counter. Reuse `CaseSetVersion`/`diff_case_sets` for change summaries.
   `ExperimentRun` stays the index record; add a per-case run row.
2. **Execution.** An `Invoker` protocol (entity ref + inputs -> output + trace ref) and
   `run_experiment(...)` that builds the scorer from the template, runs cases with bounded
   concurrency (config, not a literal), scores, and writes rows. Two completion modes: in-process
   (Plato's assistants), and `complete_case(run_id, output)` for invokers that finish out of band,
   which is how eval-service's kernel and Flowable invokers plug in unchanged. Runs go through the
   queue runtime as a job, not in the request.
3. **Pre/post case hooks** as a protocol. KH clone isolation and MACER remap become hook
   implementations that live with their owners, not in the SDK.
4. **Custom scorer definitions as data.** `natural_language` builds an `LLMJudgeScorer` from saved
   guidelines + model; revisions immutable, experiments pin one. `python` is stored and statically
   checked, and executes only through a `PythonExecutor` seam the product backs later (same decision
   as generated policy rules, 2026-09-24); no in-process exec. `agent_judge` becomes an
   `InteractiveAgent` with scorers bound as tools, deferred until a real use.
5. **Comparison and baseline.** Paired comparison over two experiments on the same dataset
   (per-case deltas, regressions, significance left out until asked); baseline as a pointer row per
   entity.
6. **Optimization as a job.** Wrap `optimize_prompt` with a persisted job record and progress;
   winner promoted through `PromptRegistry` alias. Committing the winner to the entity is the shell's
   `on_promote` callback (Plato: a new assistant config version through its governed write path;
   eval-service: its existing kernel patch).
7. **Router factories** in `server/eval_api.py`: datasets, testcases, experiments + runs, scorers +
   templates + custom scorers, comparisons + baseline, optimization jobs. Take an actor resolver and
   store instances; mount bare in tests. CSV import/export on datasets (eval-service's UI depends on
   it).

Not in the SDK: MLflow as system of record (stays an optional reporter/backend), Juno, kernel-compat
shapes, pgvector similarity.

## 4. Plato as shell

- Mount the eval routers; gate writes the way pack drafts are gated.
- `Invoker` = the chat pipeline over a Plato assistant (`interactive_predict_fn` path).
- `job:eval-run` and `job:optimize` roles (charter §6 already lists eval harness runs as an ACA job).
- Tables through `plato/models.py` `register_all` + a new migration. **Still no feedback table.**
- UI: a panel in the existing static app, SPA later; must not block the API.

## 5. Single writer, and the retirement path

Charter §5.4: *exactly one system writes any given fact.* Satisfied by partitioning on the entity,
not the table: **eval records about a Plato-hosted assistant are written by Plato; eval records about
a kernel agent or Flowable process are written by eval-service** until that entity migrates. Neither
holds a writable copy of the other's rows; cross-reads are projections.

Retirement, per resource, each step reversible:
1. **Now:** SDK stores + routers; Plato mounts them for its assistants. eval-service untouched.
2. **eval-service adopts the engine:** replaces `app/evals/evaluators.py` and its scorer fork with
   SDK scorers (already an outstanding coordinated change), then serves datasets/experiments from
   the SDK routers over its own Postgres. Its invokers, hooks and MLflow wiring stay as plugins.
3. **Entities migrate:** as kernel agents convert to Plato assistants (the Phase 6 converter), their
   datasets and experiments move with them. Kernel and Flowable invokers go when kernel does.
4. **Feedback last** (charter Stage 3): the SDK feedback router + `DbFeedbackStore` served by Plato,
   eval-service's rows migrated, the Phase 6 "no feedback table" assertion retired in the same
   change. Juno analysis either moves to an SDK hook or stays a Juno feature.
5. eval-service has nothing left to serve; retire.

## 6. Order of work

**Progress (v2.5.5, local):** step 1 `545fb677`; step 2 `6e0635cd`; step 3 `83ef0490`; step 4 `8e46d9f7`; step 5 `0d9e783b`; step 6 `4e1cf838` (no PromptRegistry promotion: the job keeps candidates, apply writes the pack draft). Step 2 as built: in-process
`Invoker` only (out-of-band `complete_case` waits for eval-service adoption, §3.2); pre/post hooks
(§3.3) not built; the store is `EvalExperimentStore` (`ExperimentStore` was taken); nothing reclaims
an experiment stranded `running`, which Plato's job role owns in step 4.

1. `DatasetStore`/`DbDatasetStore`, testcase rows, versioning by digest. Bare-mounted router.
2. `Invoker`, `run_experiment`, case-run rows, `DbExperimentStore`; queue job. Router.
3. Scorer catalog + score route; custom scorer definitions (natural_language), revisions.
4. Plato shell: mount 1-3, assistant invoker, job role, migration. First end-to-end: dataset ->
   experiment on a Plato assistant -> scored runs.
5. Comparison + baseline.
6. Optimization job + promote callback; Plato commits a new assistant config version.
7. **Queued (2026-09-25): a branch in eval-service with the suggested changes, not an offer.**
   Its scorers and templates on the SDK, its stores behind the SDK routers, its kernel and
   Flowable invokers as `Invoker` plugins; their team reviews the branch. Picked up after Plato
   ships and the feedback-service work.

Each step lands with its CHANGELOG entry and passes the adversarial review at the end.

## 7. Decisions (taken 2026-09-25: the recommendations below)

D-a build and hold the announcement; D-b partition by entity; D-c `python` stored and checked,
executed only through `PythonExecutor`; D-d MLflow optional reporter only; D-e judge and optimizer
models from config through the SDK LLM layer, no provider restriction added here.

The options as they were put:

- **D-a. Stating retirement intent.** Charter D4 recommended stating Stages 1-2 and holding Stage 3.
  This plan's §5 is Stage 3 with a sequence. Building steps 1-6 does not require announcing step 5;
  suggest building and holding the announcement until Plato runs the loop end to end, as with
  policy-workbench.
- **D-b. Partition by entity** (§5) vs a hard cutover per resource. Partition is recommended: it
  never has two writers and needs no eval-service change to start.
- **D-c. Python custom scorers.** Store + static check now, `PythonExecutor` seam, execution later?
  Or leave `python` out until an executor exists.
- **D-d. MLflow in Plato.** Optional reporter only (recommended), or also the trace/lookup source.
- **D-e. Model for judges and optimization.** Config through the SDK LLM layer; whether the
  OpenAI-only rule from policy authoring applies here too.

## 8. What would make this wrong

- eval-service's team is mid-rewrite of the same core; then step 7 should be a convergence
  conversation before step 1, not after 6.
- Kernel agents do not migrate on any foreseeable timeline; then eval-service keeps a permanent
  invoker plugin role and "retire" means "shrink to an adapter", which is still fine.
- A real consumer needs dataset content in MLflow as system of record (eval-service treats MLflow
  as authoritative for testcase content today, `mlflow_dataset_sync.py:1-15`). Then the SDK store
  needs an MLflow-backed implementation, not just a reporter.
