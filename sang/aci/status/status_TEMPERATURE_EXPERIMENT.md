# Temperature Tuning Experiment

**Date:** April 25, 2026
**Hypothesis:** Lower temperature (0.3) will reduce disposition variance in flex_gpt-5.4

## Background

Analysis of 15 historical runs shows extreme variance:
- Best: 80% (exp 015, v2.0.0)
- Worst: 20% (exp 029, v2.2.0)
- Mean: 50.0% ± 21.9%
- **Variance is independent of prompt version**

This suggests model instability at the default temperature (~1.0).

## Experiment Design

### Baseline (Default Temperature)
- Model: flex_gpt-5.4
- Prompts: v2.2.0
- Temperature: Default (~1.0)
- Runs: 3
- Results: 70%, 40%, 20% (mean 43.3% ± 25.2%)

### Experiment (Low Temperature)
- Model: flex_gpt-5.4
- Prompts: v2.2.0 (same as baseline)
- **Temperature: 0.3** ← Only change
- Runs: 3
- Expected: If variance drops below 10%, temperature is a key factor

## Implementation

Modified files:
1. `src/jaci/modes/reasoner.py` - Added temperature parameter and ModelSettings
2. `config/settings.py` - Added jaci_reasoner_temperature setting
3. `src/jaci/conductor.py` - Pass temperature to ReasonerMode
4. `tests/eval/run_eval.py` - Use settings.jaci_reasoner_temperature
5. `.env` - Set JACI_REASONER_TEMPERATURE=0.3

## Success Criteria

| Metric | Baseline | Target (temp=0.3) |
|--------|----------|-------------------|
| Mean Accuracy | 43.3% | ≥45% (not regress) |
| Std Dev | 25.2% | <10% (stability) |
| Min Accuracy | 20% | ≥30% (no catastrophic runs) |
| Max Accuracy | 70% | N/A (ceiling OK) |

**If variance drops below 10%:**
- Temperature is a major factor in variance
- Proceed with temp tuning across other modes
- Test temp=0.5, 0.7 to find optimal balance

**If variance remains >15%:**
- Temperature is NOT the root cause
- Model has fundamental instability
- Switch to claude-sonnet-4-5 or implement ensemble voting

## Run Command

```bash
cd /Users/foo/src/research/sangit/jaci
python tests/eval/run_multi_eval.py --runs 3 --prompt-version v2.2.0
```

## Results

[To be filled after experiment completes]
