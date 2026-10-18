# Optimization job: first-predict watchdog and baseline reuse (sonnet-runtime, 2026-10-17)

Checked `evaluation/optimization_jobs.py` and `optimization.py`. Has: heartbeat `touch` and `reclaim_stale` (a job
whose worker stopped touching it is reclaimed), apply claims, supersede. Lacks both asks:
1. No deadline on the first predict. A job whose first `predict_fn` call hangs touches nothing new and is reclaimed
   only after the stale window, then fails with no reason naming the hang.
2. The seed prompt's baseline is predicted again (`_evaluate_prompt(config.seed_prompt, ...)`), though the experiment
   that motivated the job already holds outputs for the same prompt, entity and cases.

## Design
- `OptimizationSpec.first_predict_seconds` (named default constant): the runner awaits the first predict with that
  bound; on expiry the job fails with `first_predict_timeout` and the entity, case and seconds, retryable.
- `OptimizationSpec.baseline_from: experiment_id | None`: when set, the runner validates it (completed, same entity,
  same dataset digest, same prompt digest) and takes the seed score and per-case details from its stored scores
  instead of predicting; a mismatch is a refusal naming the field, not a silent re-predict. Without it, today's behaviour.
- The proposal route fills `baseline_from` when the job is started from an experiment's view.
## Tests
Hanging predict fails with the code within the bound; matching experiment skips seed predictions (count calls);
mismatched digest refused by name; no `baseline_from` unchanged.
