# Replicate stability on experiments (sonnet-runtime, 2026-10-17)

Exists: `noise_floor_from` on a comparison (a completed repeat of the baseline: same entity, same dataset) turns the
repeat's per-case score differences into a noise floor. Missing: a report over N repeats of one variant (more than the
single pair a noise floor needs), per metric and per case.

## Design
- `experiment_stability(experiments: list[Experiment]) -> StabilityReport` (SDK, `evaluation/stability.py`): refuses
  runs that are not repeats of one entity, config and dataset digest. Per metric: mean, standard deviation, min, max
  over the repeats' aggregate score. Per case: how many repeats passed, and a **flip** when the verdict differs across
  repeats; the report lists the flipping case ids and the flip rate (flips / cases). Output also carries each metric's
  `unstable` flag against a named threshold constant (spread over mean), tolerant first: a flag, not a refusal.
- Route `GET /eval/experiments/{id}/stability?repeats=id,id,...` (default: every completed experiment sharing the
  entity, config digest and dataset digest) and the comparison reads the same report for its baseline.
- Xlsx sheet in the comparison export (metric rows, flipping cases).
- Client `experiment_stability`; the page (sonnet-ui) draws the table.
## Tests
Two identical repeats: zero spread and no flips; one flipping case is listed; mixed datasets refused by name;
a single run answers "needs at least two".
## Not built
Cross-model variance, significance tests beyond the existing stats module.
