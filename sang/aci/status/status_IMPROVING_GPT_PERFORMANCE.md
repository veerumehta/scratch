# Improving GPT-5.4 Performance Through Prompt Engineering
## April 26, 2026

## Background

After comparing GPT-5.4 flex with Claude models (Sonnet 4.5, Opus 4.7), we decided to improve GPT-5.4 through targeted prompt engineering.

**Decision rationale:**
- Maintain platform consistency (OpenAI Agents SDK)
- GPT already performs well on complex structuring cases
- Cost difference is small ($0.0702 GPT vs $0.0525 Sonnet)
- Opportunity to reach 80%+ accuracy through prompt improvements

## Performance Analysis (Baseline: v2.0.0 prompt)

### GPT-5.4 Baseline: 63.6% accuracy (7/11 cases)

**Failed Cases Analysis:**
1. case_03: Shell company - closed instead of escalate
2. case_04: PEP rapid movement - closed instead of escalate
3. case_05: Round-tripping - wrong typology (said structuring)
4. case_07: Salary cycle - escalated instead of close
5. case_10: Signal decay - escalated instead of close

## First Iteration Results (v2.0.0-improved)

**CRITICAL FAILURE:** Improved prompt dropped accuracy from 63.6% to **36.4%** (4/11 cases)

### Test Results (flex_gpt-5.4, MLflow run: 966825d81a77423e90c7d7d648833365)

**Passed (3 cases):**
- case_08: PEP name collision ✓
- case_09: SAR deadline edge ✓
- case_10: Signal decay ✓ (FIXED - was failing in baseline)

**Failed (8 cases):**
- case_01: Baseline structuring ✗ (REGRESSION - closed instead of escalate)
- case_02: Multi-account structuring ✗ (REGRESSION - closed instead of escalate)
- case_03: Shell company ✓ disposition, ✗ typology
- case_04: PEP rapid movement ✗ (still failing - closed instead of escalate)
- case_05: Round-tripping ✗ (still failing - wrong typology)
- case_06: Cash-intensive business ✗ (REGRESSION - escalated instead of close)
- case_07: Salary cycle ✗ (still failing - escalated instead of close)
- case_11: Reverse psychology ✗ (REGRESSION - closed instead of escalate)

**Net result:** Fixed 1 case (case_10), broke 4 cases (01, 02, 06, 11) = -3 net

### Root Cause Analysis

**1. Over-emphasis on false positive checks backfired:**
- Added "CRITICAL: Check these BEFORE considering typology evidence" framing
- Made reasoner too conservative about prior case history
- **case_01 failure:** Reasoner saw prior false positive and closed a real structuring case
  - Rationale: "prior case history shows... alert was previously closed as a false positive"
  - **Wrong:** The current pattern is strong and recent, prior FP shouldn't override current evidence

**2. Signal decay check works but creates other issues:**
- **case_10 fixed:** Signal decay detection now working ✓
- But the aggressive false-positive-first framing caused other failures

**3. PEP and shell company emphasis ineffective:**
- **case_03:** Now gets disposition right (escalate) but wrong typology
- **case_04:** Still failing - PEP emphasis didn't help

**4. Potential fixture loading issue (case_06):**
- Gold case expects `cash_intensive_business_flag: True`
- Actual customer_profile lacks `entity_type`, `business_licence_verified`, `cash_intensive_business_flag`
- Either fixture not loading OR investigator not requesting right evidence
- Need to investigate whether this is prompt issue or test harness issue

### Lessons Learned

1. **Avoid over-emphasis:** Adding "CRITICAL" framing made the model too rigid
2. **Balance is key:** False positive checks are important but shouldn't override strong current evidence
3. **Incremental changes:** Should have tested ONE change at a time
4. **Regression testing:** Need to ensure fixes don't break passing cases

## Second Iteration Results (v2.0.1 - Measured Approach)

**Approach:** Minimal changes - added only signal decay check and refined prior case guidance

### Test Results (flex_gpt-5.4, MLflow run: 5c9fd58c31594aa1803f905488c995e1)

**Disposition accuracy:** 63.6% (7/11) - SAME as baseline
**Fully passed:** 4/11 (36.4%) - WORSE than baseline's 7/11

**Passed fully (4 cases):**
- case_01: Baseline structuring ✓✓
- case_02: Multi-account structuring ✓✓
- case_09: SAR deadline edge ✓✓
- case_11: Reverse psychology ✓✓

**Disposition correct, typology wrong (3 cases):**
- case_03: Shell company ✓✗
- case_04: PEP rapid movement ✓✗
- case_05: Round-tripping ✓✗

**Disposition wrong (4 cases):**
- case_06: Cash-intensive business ✗ (should close, escalated)
- case_07: Salary cycle ✗ (should close, escalated)
- case_08: PEP name collision ✗ (should close, escalated) - REGRESSION
- case_10: Signal decay ✗ (should close, escalated) - Signal decay check didn't work

### Analysis

**What improved:**
- case_03, case_04, case_05 now get disposition right (baseline had these as wrong disposition)
- This is good progress on non-structuring typologies

**What broke:**
- case_08: REGRESSION (was passing in baseline, now escalates when should close)
- case_10: Signal decay check didn't work as intended

**Unchanged failures:**
- case_06, case_07: Still failing (baseline also failed these)

**Net result:** Same disposition accuracy (63.6%), but fewer fully passed cases (4 vs 7)

### Key Insights

1. **Typology recognition improved:** Getting disposition right on cases 03, 04, 05 is progress
2. **Signal decay check ineffective:** Case_10 still fails despite adding the check
3. **Need to investigate why:** case_08 regressed and signal decay didn't work
4. **Trade-off:** Better at escalate decisions, worse at close decisions

## CRITICAL BUG DISCOVERED (April 28, 2026)

**All previous evaluation results are INVALID.**

### Root Cause

The evaluation harness (`tests/eval/run_eval.py`) was NOT calling `set_active_case_id()` before running each case. This caused the mock connectors to fall back to generic placeholder data ("John Doe" structuring pattern) instead of loading case-specific fixtures.

**Evidence:**
- case_08 reasoner output mentioned "cash deposits clustered near $10,000 threshold"
- But case_08 is a WATCHLIST_HIT with NO transactions
- case_06 customer_profile missing `cash_intensive_business_flag` field
- All cases were seeing similar structuring-like data

### Fix Applied

```python
# tests/eval/run_eval.py
from tests.fixtures.test_context import set_active_case_id, clear_active_case_id

for gold_case in gold_cases:
    try:
        set_active_case_id(gold_case["case_id"])  # ← ADDED
        # ... run investigation ...
    finally:
        clear_active_case_id()  # ← ADDED
```

### Impact

- **Baseline results (63.6%):** Invalid - used generic data, not real cases
- **v2.0.0-improved results (36.4%):** Invalid - same issue
- **v2.0.1 results (63.6%):** Invalid - same issue

All prompt engineering work done so far was based on incorrect data. Need to re-run baseline evaluation with correct fixture loading to establish true baseline performance.

## TRUE Baseline Results (v2.0.0 with correct fixtures)

**MLflow run:** 18da84a217cb4c728efd4f3d272b4318
**Timestamp:** 20260428_100723

### Summary Metrics

**Disposition accuracy:** 81.8% (9/11 cases) - **EXCEEDS 80% TARGET** ✓
**Typology accuracy:** 45.5% (5/11 cases)
**Fully passed:** 9/11 cases
**Evidence coverage:** 81.8%
**Citation completeness:** 100%
**Average iterations:** 2.55
**Guard fire rate:** 18.2% (2/11 cases)
**Cost:** $0.5554 ($0.0505/case average)

### Passed Cases (9/11)

1. ✓ case_01: Baseline structuring
2. ✓ case_03: Shell company layering
3. ✓ case_04: PEP rapid movement
4. ✓ case_05: Round-tripping
5. ✓ case_06: Cash-intensive business (CLOSE)
6. ✓ case_07: Salary cycle (CLOSE)
7. ✓ case_08: PEP name collision (CLOSE)
8. ✓ case_09: SAR deadline edge
9. ✓ case_10: Signal decay (CLOSE)

### Failed Cases (2/11)

1. ✗ case_02: Multi-account structuring (guard fired, disposition wrong)
2. ✗ case_11: Reverse psychology (guard fired, disposition wrong)

### Analysis

**Key Findings:**

1. **Baseline exceeds target:** 81.8% disposition accuracy exceeds the 80% target from the build plan
2. **Guard fire correlation:** Both failures had signal_decay guard fires after 4 iterations
3. **Typology accuracy gap:** Only 45.5% typology accuracy suggests reasoner is getting disposition right but sometimes selecting wrong typology
4. **Efficiency:** Average 2.55 iterations is well below the <5 target
5. **Cost-effective:** $0.0505/case is reasonable for GPT-5.4 flex tier

**Why the fixture bug masked this:**
- With generic data, all cases looked like basic structuring
- Reasoner couldn't apply false positive checks (no cash-intensive business flags, no salary codes, etc.)
- Non-structuring typologies couldn't be tested (PEP, shell company, round-tripping all need specific evidence)
- The 63.6% with wrong data was the model trying to reason about generic placeholder patterns

**Implications:**

1. **Prompt engineering may not be needed:** Baseline already meets the 80% target
2. **Focus should shift to:**
   - Understanding case_02 and case_11 guard fires
   - Improving typology accuracy (45.5% → 80%+)
   - Ensuring guard behavior is correct (not blocking valid escalations)

### Next Steps

1. Investigate why case_02 and case_11 trigger signal_decay guard and fail
2. Determine if 81.8% is acceptable or if we should aim for 90%+
3. Consider whether typology accuracy improvements are priority
4. May not need Claude model comparison if GPT already exceeds target

