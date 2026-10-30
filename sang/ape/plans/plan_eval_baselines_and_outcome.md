# Plan: typed no_baseline, subject-scoped baselines, an experiment outcome read model (sonnet-runtime, 2026-10-29)

Plan only for the shape; (1) and (3) are built from it, (2) waits for a nod on the table choice. Additive for a `japes>=2.6.4` pin; no spend.
Source: the workbench runner audit (`plan_eval_service_sdk_for_a_second_host.md` section 3), read against `jazzx_sdk/evaluation/experiments.py`,
`experiments_db.py` and `server/eval_api.py`.

## 1. Typed `no_baseline` (built)

Today `ExperimentRunner._pair` raises a plain `KeyError(f"{type}/{id} has no baseline")`, and the routes turn every `KeyError` into a 404, so a caller
cannot tell "no such experiment" from "nothing to compare with" except by text (the workbench matches an error-string suffix).
- `NoBaseline(KeyError)` in `experiments.py` carries `entity` and `subject`; it is still a `KeyError`, so every existing caller and test is unchanged.
- The comparison routes answer 404 with a body `{"error": ..., "code": "no_baseline"}` for it and the existing text for any other `KeyError`.
- Not a refusal to compare: a host that wants "unscored, no baseline" catches `NoBaseline` (or reads the code) instead of parsing text.

## 2. Subject-scoped baselines (shape needs a nod)

The workbench's rule is per case: a loan's baseline is the loan's, a baseline of the same entity wins over another entity's, otherwise the newest.
The SDK holds one baseline per entity (`eval_baseline`, primary key tenant, entity type, entity id).

Recommended: a second table, not a column on the first. `eval_subject_baseline(tenant_id, entity_type, entity_id, subject, experiment_id,
set_at, set_by)`, primary key `(tenant_id, entity_type, entity_id, subject)`. Why: adding a nullable `subject` to the existing key means
rebuilding the primary key (a table rewrite on SQLite, a constraint swap on Postgres, a null in a key on neither) for rows that never have a
subject; a new table is one `create_table` migration and leaves `eval_baseline`, `set_baseline(entity, ...)` and every entity-wide caller
exactly as they are. The cost is two lookups where one would do, hidden behind one function.
- `set_baseline(entity, experiment_id, subject=None)`: no subject writes the entity-wide row as now; a subject writes the new table.
- `get_baseline(entity, subject=None)`: unchanged without a subject.
- `select_baseline(entity, subject, prefer_entity=True)`: the subject's baseline for the same entity first, else the newest baseline held for that
  subject by any entity (`prefer_entity=False` skips the first step), else None. The entity-wide baseline is not consulted: it is a different
  question (the whole dataset), and the caller falls back to it explicitly.
- Routes: `POST experiments/{id}/baseline` takes an optional `subject`; `GET baselines/{type}/{id}` an optional `?subject=`; comparisons take
  `?subject=` and use `select_baseline` when given.
- Migration `00NN_eval_subject_baseline` (additive, downgrade drops it); an existing database changes in nothing else.
Alternative (a nullable column plus a surrogate key) is possible and gives one table; I do not recommend it for the rewrite above.

## 3. `ExperimentOutcome` read model (built)

A host that runs one case per experiment (the workbench) reads `summary`, then `case_runs`, then `result.explanation` itself. One read model:
- `CaseOutcome`: `case_id`, `status`, `score`, `passed`, `explanation` (the scorer's, first non-empty), `error`, `trace_id`, `usage`.
- `ExperimentOutcome`: `experiment_id`, `status`, `score` (the summary's mean), `passed` (every completed case passed and none failed),
  `pass_rate`, `cases`, `usage`, `error`, `health`, `gate`, and `baseline` (`experiment_id` of the entity's baseline, or None).
- `ExperimentRunner.outcome(experiment_id)` and `GET {prefix}/experiments/{id}/outcome`; an experiment that has not finished answers with its
  status and no scores (never an error). It reads what is already stored; it computes nothing new.
