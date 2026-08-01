# Temperature Tuning Experiment - Status

**Started:** April 25, 2026 01:35 UTC
**Status:** Running (Run 1/3 in progress)
**Expected Completion:** 30-60 minutes

## What Was Changed

Following the recommendations from `IMPROVING_GPT_PERFORMANCE.md`, I implemented the **fastest experiment to test variance reduction**: temperature tuning.

### Code Changes

1. **`src/jaci/modes/reasoner.py`** - Added temperature support
   - Added `temperature` parameter to `__init__`
   - Modified `_create_agent()` to use `ModelSettings(temperature=...)`
   - Imported `ModelSettings` from agents SDK

2. **`src/jaci/settings.py`** - Added temperature configuration
   - Added `reasoner_temperature: float | None = None` field
   - Reads from `JACI_REASONER_TEMPERATURE` env var

3. **`src/jaci/conductor.py`** - Pass temperature to reasoner
   - Added `reasoner_temperature` parameter to `__init__`
   - Passed it to `ReasonerMode` constructor

4. **`tests/eval/run_eval.py`** - Use temperature from settings
   - Added `reasoner_temperature=settings.reasoner_temperature` when creating Conductor

5. **`.env`** - Set experiment value
   - Added `JACI_REASONER_TEMPERATURE=0.3`

## Experiment Configuration

| Parameter | Baseline | Experiment |
|-----------|----------|------------|
| Model | flex_gpt-5.4 | flex_gpt-5.4 |
| Prompts | v2.2.0 | v2.2.0 |
| **Temperature** | **Default (~1.0)** | **0.3** ← ONLY CHANGE |
| Runs | 3 | 3 |

## Baseline Results (Default Temperature)

From previous v2.2.0 runs:
- Run 1: 70% (exp 027)
- Run 2: 40% (exp 028)
- Run 3: 20% (exp 029)
- **Mean: 43.3% ± 25.2%** ← High variance!

## Success Criteria

✅ **PASS:** Standard deviation drops below 10%
→ Temperature is a major factor, continue temp tuning

❌ **FAIL:** Standard deviation remains above 15%
→ Temperature is NOT the root cause, model has fundamental instability
→ Next step: Switch to claude-sonnet-4-5 or implement ensemble voting

## Why Temperature First?

From `IMPROVING_GPT_PERFORMANCE.md` Priority 0 (Fast Wins):

1. ✅ **Temperature tuning** - 1 hour, minimal code change
2. Structured outputs - 1 day
3. Remove edge cases - 1 hour

Temperature is the fastest test to rule in/out a simple explanation before investing in more complex solutions.

## Monitoring

```bash
# Check progress
tail -f /tmp/claude/tasks/b6ac2cd.output

# View results when complete
cat output/multi_eval/multi_eval_*.json | jq '.aggregated_metrics'
```

## Next Steps (After Results)

### If variance drops below 10%
1. Test other temperature values (0.5, 0.7) to find optimal
2. Apply temperature to Investigator mode
3. Document optimal temperature in production config

### If variance remains high (>15%)
1. Update analysis: Temperature is NOT the factor
2. Try structured outputs (JSON schema forcing false positive checks)
3. If that fails, prepare claude-sonnet-4-5 integration plan
4. Or implement ensemble voting (3x reasoner calls, majority vote)

---

## ⚠️ EXPERIMENT COMPLETED - FAILED

**Results:** Temperature=0.3 caused REGRESSION
- Accuracy: 46.7% ± 5.8% (vs baseline 43.3% ± 25.2%)
- Variance reduced (✅) but accuracy worse (❌)
- **CRITICAL:** Model systematically CLOSES cases that should ESCALATE
  - ESCALATE pass rate: 33% → 11% (-22pp)
  - Cases 01-05 (all ESCALATE): 0% pass rate, stable failures

**Conclusion:** Lower temperature makes model TOO conservative for AML use case.

See `TEMPERATURE_EXPERIMENT_RESULTS.md` for full analysis.
