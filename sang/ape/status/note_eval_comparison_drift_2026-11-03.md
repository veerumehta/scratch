# Eval comparison drift check: eval-service commits against the SDK evaluation control plane (sonnet-runtime, 2026-11-03)

Read-only survey for plan item 22. Source: the five eval-service commits named in the plan, read from `/Users/sangit/src/eval-service` (diffs of `9200af5`, `eafe21b`, `c945df0`, and
the messages and file lists of `8059398` and `039f67b`). SDK side: `jazzx_sdk/evaluation/` read by grep and by opening `experiment_comparison.py`, `path_comparison.py`
and `reclaim.py`. Nothing was run. "Not checked" means I did not open that code.

| Commit | What it does | SDK counterpart | Gap |
|---|---|---|---|
| `9200af5` comparisons report scoring differences instead of rejecting them | Adds `scoring_changes` (a diff of the snapshotted evaluator config and eval context) to a comparison, a warning, and marks the interpretation as not directly comparable; a noise reference must still match scoring | `compare_experiments` (`experiment_comparison.py`) never rejected different scorers, and it reports `by_scorer` deltas | Was: a comparison did not say the two experiments were scored differently. Now `ExperimentComparison.scoring_changes` lists the scorer and threshold paths that differ |
| `eafe21b` honor explicit scorer pass verdicts | An overall pass comes from the scorers' own `passed` when they report one (single scorer: its verdict; several: any failure fails, all passing passes), else the threshold over the weighted score; records `verdict_source` | `CompositeScorer` in `jazzx_eval_contracts/scorers/core.py` (the SDK's `evaluation/scorers.py` re-exports it): `passed = every required sub-scorer passed and weighted mean >= threshold` (default 1.0) | A sub-scorer's own `passed` counts only if it is listed `required`. With the default threshold, a scorer that reports `passed=True` at a score of 0.9 fails the composite, the case `eafe21b` fixes in eval-service. A different rule, not a bug found in a run; changing it changes every existing pass rate, so it is the user's call |
| `c945df0` rank digit-letter model tokens such as `gpt-4o` in the override guard | eval-service's `parse_model_name` in `app/config.py` ranks model ids so an override cannot pick an older model than the default | None: the SDK has no override guard on a model choice (`model_identity.normalize_model_name` only normalizes ids) | None to fix in the SDK; a host choice, not a drift |
| `8059398` compare process experiments by outcome, execution path, definition changes and noise floor | A 1,658-line `process_comparison.py` plus changes to `comparison.py`, the export and the router | Partly: `noise_floor_from` and `noise_floor` exist, and `path_comparison.py` compares execution paths | Comparing definition versions (what changed in the entity's definition between runs) was not found in the SDK. Whether the SDK should have it is a product question: it is eval-service's process-eval domain |
| `039f67b` finalize stuck process evals and Macer clone remap integrity | Ends the read transaction before slow work so an idle-in-transaction timeout does not kill the final write; a lost connection rolls back and retries; failing a run finalizes its experiment | `reclaim.py` fails experiments a dead process left running; `assert_no_open_db_session` (fabric) catches a session held across a slow call | The hazard is handled by design in the SDK (a guard and a sweep). The Macer clone remap is eval-service only |

## What is worth doing

1. **`scoring_changes` for `compare_experiments`** was the one clear gap. Built the same day: `Experiment.template` already records the scorers and threshold, so the comparison now lists the paths that differ.
2. **The pass rule differs from `eafe21b`'s** (above). `jazzx_eval_contracts` is a separate distribution eval-service can depend on, so a change there moves both. Ask before touching it.
3. The other three are not SDK drift.

Item 1 is built (an additive field Plato's evaluation page does not show yet); item 2 is a decision, not built.
