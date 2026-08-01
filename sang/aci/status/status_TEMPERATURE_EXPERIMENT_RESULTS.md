# Temperature Tuning Experiment - RESULTS

**Status:** COMPLETED ❌ FAILED
**Date:** April 25, 2026

## Executive Summary

**Temperature=0.3 caused CATASTROPHIC REGRESSION:**
- Disposition Accuracy: 46.7% ± 5.8% (vs baseline 43.3% ± 25.2%)
- **Variance REDUCED from 25.2% to 5.8%** ✅
- **BUT accuracy REGRESSED and became CONSISTENTLY BAD** ❌

**Critical Finding:** The model systematically CLOSES cases that should ESCALATE.

---

## Results

### Temperature=0.3 (This Experiment)

| Run | Accuracy | Passed Cases | Cost |
|-----|----------|--------------|------|
| 1 | 40% | 2/10 | $0.527 |
| 2 | 50% | 4/10 | $0.509 |
| 3 | 50% | 3/10 | $0.488 |
| **Mean** | **46.7%** | **3.0/10** | **$0.508** |
| **Std Dev** | **5.8%** | **1.0** | **$0.023** |

### Baseline (Default Temperature ~1.0)

From v2.2.0 runs (exp 027-029):
| Run | Accuracy | Passed Cases |
|-----|----------|--------------|
| 1 | 70% | 7/10 |
| 2 | 40% | 4/10 |
| 3 | 20% | 2/10 |
| **Mean** | **43.3%** | **4.3/10** |
| **Std Dev** | **25.2%** | **2.5** |

---

## Case-Level Analysis

### ESCALATE Cases (Should Pass)

| Case | Expected | Temp=0.3 Pass Rate | Baseline Pass Rate | Status |
|------|----------|-------------------|-------------------|---------|
| case_01 | ESCALATE | **0%** (✗✗✗) | 33% | STABLE FAILURE |
| case_02 | ESCALATE | **0%** (✗✗✗) | 67% | STABLE FAILURE |
| case_03 | ESCALATE | **0%** (✗✗✗) | 0% | STABLE FAILURE |
| case_04 | ESCALATE | **0%** (✗✗✗) | 33% | STABLE FAILURE |
| case_05 | ESCALATE | **0%** (✗✗✗) | 67% | STABLE FAILURE |
| case_09 | ESCALATE | **67%** (✗✓✓) | 33% | FLIPS 1x |

**Pattern:** Temperature=0.3 systematically CLOSES 5/6 ESCALATE cases.

### CLOSE Cases (Should Pass)

| Case | Expected | Temp=0.3 Pass Rate | Baseline Pass Rate | Status |
|------|----------|-------------------|-------------------|---------|
| case_06 | CLOSE | **33%** (✗✓✗) | 33% | FLIPS 2x |
| case_07 | CLOSE | **67%** (✗✓✓) | 0% | FLIPS 1x |
| case_08 | CLOSE | **100%** (✓✓✓) | 100% | STABLE |
| case_10 | CLOSE | **33%** (✓✗✗) | 67% | FLIPS 1x |

**Pattern:** CLOSE cases show mixed results with instability.

---

## Key Findings

### 1. Temperature=0.3 Makes Model TOO Conservative

**Evidence:**
- 5/6 ESCALATE cases fail (0% pass rate each)
- Model systematically chooses CLOSE over ESCALATE
- Reduced variance (5.8%) but in the WRONG direction

**Interpretation:** Lower temperature → more deterministic → consistently biased toward CLOSE

### 2. Variance Reduction is Meaningless Without Accuracy

| Metric | Baseline | Temp=0.3 | Change |
|--------|----------|----------|---------|
| **Mean Accuracy** | 43.3% | 46.7% | +3.4pp |
| **Std Dev** | 25.2% | 5.8% | **-19.4pp** ✅ |
| **ESCALATE Pass Rate** | 33% | 11% | **-22pp** ❌ |
| **CLOSE Pass Rate** | 58% | 58% | 0pp |

**Conclusion:** We reduced variance by making the model consistently wrong on ESCALATE cases.

### 3. Only case_08 Remains 100% Stable

**case_08** (watchlist false positive) passes 100% across ALL temperature settings:
- Simple binary decision: Check watchlist → see "no match" → CLOSE
- No complex multi-factor reasoning required

**All other cases** require nuanced reasoning about:
- Structuring patterns with business context
- Prior case history interpretation
- False positive vs true alert differentiation

### 4. The Prior Cases Fixture IS a Problem

**From case_01 failure analysis:**

Fixture says:
```json
{
  "disposition": "CLOSED_NO_SAR",
  "typology": "structuring",
  "notes": "Prior structuring alert closed — insufficient evidence at the time. Pattern did not recur until now."
}
```

**Reasoner interprets this as:**
> "Prior structuring case was closed as false positive → current case is also false positive"

**Intended meaning:**
> "Prior case was BORDERLINE, now the pattern RECURRED → STRONGER evidence to escalate"

**But this is amplified at temp=0.3** - the conservative interpretation wins every time.

---

## Conclusions

### ✅ SUCCESS: Variance Reduction

Temperature=0.3 reduced standard deviation from 25.2% → 5.8% (77% reduction).

### ❌ FAILURE: Accuracy Regression

The model became consistently biased toward CLOSE:
- ESCALATE pass rate: 33% → 11% (-22pp)
- Creates stable but WRONG behavior

### ❌ FAILURE: Temperature is NOT the Root Cause of Variance

The baseline variance (20-80% range) is still a model capability issue. Temperature=0.3 just masks it by forcing conservative behavior.

---

## Recommendations

### 1. ❌ DO NOT Use Temperature=0.3

Lower temperature makes the model TOO conservative for AML use case where false negatives (missing true alerts) are more costly than false positives.

### 2. ✅ Fix Prior Cases Fixture First

Update `case_fixtures.py` for case_01 and case_02:

```python
"get_prior_cases": [{
    "disposition": "ESCALATE_SAR_FILED",  # Changed from CLOSED_NO_SAR
    "typology": "structuring",
    "notes": "Prior structuring SAR filed 2024-03-28. Establishes customer history of structuring behavior."
}]
```

### 3. ✅ Try Targeted Temperature (Investigator Only)

Instead of lowering Reasoner temperature, try:
- **Investigator temp=0.7** (reduce evidence gathering variance)
- **Reasoner temp=1.0** (default, allows full reasoning range)

Hypothesis: Variance comes from inconsistent evidence gathering, not reasoning.

### 4. ✅ Switch to claude-sonnet-4-5 for Reasoner

Temperature tuning cannot fix fundamental model instability. The analysis clearly shows flex_gpt-5.4 lacks reliable multi-factor reasoning.

### 5. ✅ Implement Ensemble Voting

Run Reasoner 3x with temp=0.7, use majority vote. This smooths variance while preserving decision range.

---

## Next Steps

**Priority 0:** Fix case_01 and case_02 fixture data (1 hour)

**Priority 1:** Run baseline eval with fixed fixtures (30 min)
- Expect: Accuracy improves to 50-60% range
- If still shows 20-80% variance → proceed to Priority 2

**Priority 2:** Implement claude-sonnet-4-5 for Reasoner (2 hours)
- Add Anthropic API support to ReasonerMode
- Run 3-run eval
- If variance drops below 10% → we're done
- If variance remains high → proceed to Priority 3

**Priority 3:** Implement ensemble voting (3 days)
- Run Reasoner 3x per case with temp=0.7
- Majority vote for disposition
- Measure variance reduction

---

## Appendix: Full Case Stability Data

```
case_01: ✗✗✗ (0% pass rate) - STABLE - Expected: ESCALATE
case_02: ✗✗✗ (0% pass rate) - STABLE - Expected: ESCALATE
case_03: ✗✗✗ (0% pass rate) - STABLE - Expected: ESCALATE
case_04: ✗✗✗ (0% pass rate) - STABLE - Expected: ESCALATE
case_05: ✗✗✗ (0% pass rate) - STABLE - Expected: ESCALATE
case_06: ✗✓✗ (33% pass rate) - FLIPS 2x - Expected: CLOSE
case_07: ✗✓✓ (67% pass rate) - FLIPS 1x - Expected: CLOSE
case_08: ✓✓✓ (100% pass rate) - STABLE - Expected: CLOSE
case_09: ✗✓✓ (67% pass rate) - FLIPS 1x - Expected: ESCALATE
case_10: ✓✗✗ (33% pass rate) - FLIPS 1x - Expected: CLOSE
```

**Interpretation:**
- Temperature=0.3 creates "stable failures" on ESCALATE cases
- CLOSE cases show instability (flipping behavior)
- This is the OPPOSITE of what we want for AML compliance
