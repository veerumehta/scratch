# Benchmark Version Tracking — Implementation Summary

**Date:** April 25, 2026
**Status:** ✅ Complete

## What Was Added

### 1. Benchmark Version Constant
**File:** `tests/eval/run_eval.py`

```python
# Benchmark version - increment when gold cases or fixtures change
# v1.0: cases 01-10 (April 23, 2026)
# v1.1: cases 01-11 (April 25, 2026) - added case_11
BENCHMARK_VERSION = "1.1"
```

**Location:** Lines 41-44 (after EXPERIMENTS_FILE constant)

### 2. MLflow Parameter Logging
**File:** `tests/eval/run_eval.py`

**Added to MLflow run parameters** (line 322):
```python
client.log_param(run_id, "benchmark_version", BENCHMARK_VERSION)
```

Now MLflow tracks:
- `benchmark_version` (NEW)
- `model_name`
- `service_tier`
- `max_iterations`
- `inter_case_delay`
- `total_gold_cases`

### 3. Experiment Metadata JSON
**File:** `tests/eval/run_eval.py`

**Updated `log_experiment_metadata()` function:**
- Added `benchmark_version` parameter
- Added to experiment dict (line 107)
- Updated description to include benchmark version

**experiments/experiments.json entries now include:**
```json
{
  "id": "001",
  "mlflow_run_id": "...",
  "benchmark_version": "1.1",
  "prompt_version": "v2.2.0",
  "model": "flex_gpt-5.4",
  "metrics": {...}
}
```

### 4. Evaluation Report JSON
**File:** `tests/eval/run_eval.py`

**Added to report dict** (line 439):
```python
report = {
    "timestamp": "...",
    "mlflow_run_id": "...",
    "benchmark_version": BENCHMARK_VERSION,  # NEW
    "model_name": "...",
    "service_tier": "...",
    "summary": {...},
    "token_metrics": {...},
    "results": [...]
}
```

**output/evaluations/eval_report_*.json files now include benchmark_version**

### 5. Multi-Run Aggregated Results
**File:** `tests/eval/run_multi_eval.py`

**Updated multi_report dict:**
```python
multi_report = {
    "timestamp": "...",
    "benchmark_version": BENCHMARK_VERSION,  # NEW
    "model_name": "...",
    "prompt_version": "...",
    "num_runs": 3,
    "aggregated_metrics": {...},
    "case_stability": {...}
}
```

**Updated console output** to show benchmark version:
```
MULTI-RUN EVALUATION SUMMARY
============================================================
Benchmark: v1.1
Model: flex_gpt-5.4
Prompt Version: v2.2.0
Runs: 3
```

**output/multi_eval/multi_eval_*.json files now include benchmark_version**

## Files Modified

```
tests/eval/run_eval.py        (6 changes: constant, MLflow param, metadata, report)
tests/eval/run_multi_eval.py  (3 changes: import, multi_report, console output)
```

## Impact on Existing Data

### Historical Experiments (v1.0)
All experiments run **before April 25, 2026** were on benchmark v1.0 (cases 01-10).

**To identify v1.0 experiments:**
- Check `experiments/experiments.json` entries without `benchmark_version` field
- Check MLflow runs without `benchmark_version` parameter
- Check `total_cases = 10` in summary metrics

### New Experiments (v1.1)
All experiments run **on/after April 25, 2026** will be tagged with:
- `benchmark_version: "1.1"` in all outputs
- MLflow parameter: `benchmark_version=1.1`

### Comparison Guidelines

**Comparing across versions:**
```python
# For v1.0 → v1.1 comparison, use only cases 01-10
v1_0_accuracy = passed_cases_01_to_10 / 10
v1_1_comparable_accuracy = passed_cases_01_to_10 / 10  # Same denominator

# Full v1.1 accuracy includes case_11
v1_1_full_accuracy = passed_cases_01_to_11 / 11
```

**Filtering experiments by benchmark version:**
```python
# From experiments.json
v1_0_experiments = [e for e in experiments if e.get("benchmark_version") is None or e["benchmark_version"] == "1.0"]
v1_1_experiments = [e for e in experiments if e.get("benchmark_version") == "1.1"]

# From MLflow
from mlflow import MlflowClient
client = MlflowClient()
v1_1_runs = client.search_runs(
    experiment_ids=["..."],
    filter_string="params.benchmark_version = '1.1'"
)
```

## Verification

**Test that benchmark version is tracked:**
```bash
# Run single eval
python tests/eval/run_eval.py

# Check output report
cat output/evaluations/eval_report_*.json | jq '.benchmark_version'
# Expected: "1.1"

# Check MLflow parameter
mlflow ui
# Navigate to run → Parameters → benchmark_version: 1.1

# Check experiment metadata
cat experiments/experiments.json | jq '.experiments[-1].benchmark_version'
# Expected: "1.1"
```

**Test multi-run eval:**
```bash
# Run multi-eval
python tests/eval/run_multi_eval.py --runs 3

# Check output
cat output/multi_eval/multi_eval_*.json | jq '.benchmark_version'
# Expected: "1.1"
```

## Future Maintenance

**When adding/modifying gold cases:**

1. Update `BENCHMARK_VERSION` constant in `tests/eval/run_eval.py`:
   ```python
   # v1.2: cases 01-12 (Date) - added case_12
   BENCHMARK_VERSION = "1.2"
   ```

2. Update `docs/BENCHMARK_VERSION.md` with changelog

3. Update fixture docstring in `tests/fixtures/case_fixtures.py`

4. All future experiments will automatically use new version

**Semantic versioning:**
- **Major (2.0):** Complete redesign (different typologies, structure)
- **Minor (1.2):** Add/remove cases, modify fixtures
- **Patch (1.1.1):** Bug fixes in existing fixtures (no new cases)

## Summary

✅ **All experiment metadata now tracks benchmark version**
✅ **MLflow parameters include benchmark_version**
✅ **Experiment JSON files include benchmark_version**
✅ **Evaluation reports include benchmark_version**
✅ **Multi-run aggregated reports include benchmark_version**
✅ **Console output displays benchmark version**

**Next run** will automatically tag everything with v1.1.
