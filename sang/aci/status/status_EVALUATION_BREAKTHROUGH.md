# JACI Evaluation Breakthrough — April 28, 2026

## Executive Summary

**CRITICAL DISCOVERY:** All previous evaluation results were invalid due to a test harness bug. After fixing the bug and re-running with correct case-specific fixtures, GPT-5.4 baseline performance is **81.8% disposition accuracy**, exceeding the 80% target.

**Previous belief:** GPT-5.4 at 63.6% needed significant prompt engineering
**Reality:** GPT-5.4 at 81.8% already meets requirements

## The Bug

### Root Cause
The evaluation harness (`tests/eval/run_eval.py`) was not calling `set_active_case_id()` before running each case, causing mock connectors to return generic "John Doe" placeholder data instead of case-specific fixtures.

### Evidence
- case_08 (watchlist hit, no transactions) reasoner saw "cash deposits near $10K"
- case_06 (cash-intensive business) missing `cash_intensive_business_flag` field
- All cases appeared to be similar structuring patterns

### Fix Applied
```python
from tests.fixtures.test_context import set_active_case_id, clear_active_case_id

for gold_case in gold_cases:
    try:
        set_active_case_id(gold_case["case_id"])  # ADDED
        # ... run investigation ...
    finally:
        clear_active_case_id()  # ADDED
```

**Commit:** fixture loading bug fix in `tests/eval/run_eval.py`

---

## Results Comparison

| Metric | Wrong Data (Invalid) | Correct Data (Valid) | Δ |
|--------|---------------------|---------------------|---|
| **Disposition Accuracy** | 63.6% | **81.8%** | +18.2% |
| **Typology Accuracy** | ~10% | **45.5%** | +35.5% |
| **Passed Cases** | 7/11 | **9/11** | +2 |
| **Avg Iterations** | 3.5 | **2.55** | -27% |
| **Cost/case** | $0.077 | **$0.0505** | -34% |

---

## TRUE Baseline Performance (v2.0.0, correct fixtures)

**Model:** flex_gpt-5.4
**MLflow run:** 18da84a217cb4c728efd4f3d272b4318
**Timestamp:** 20260428_100723

### Metrics
- **Disposition accuracy:** 81.8% (9/11) ✅ **EXCEEDS 80% TARGET**
- **Typology accuracy:** 45.5% (5/11)
- **Evidence coverage:** 81.8%
- **Citation completeness:** 100%
- **Average iterations:** 2.55 (target: <5)
- **Guard fire rate:** 18.2% (2/11)
- **Cost:** $0.5554 total ($0.0505/case)

### Passed Cases (9/11)
✅ case_01: Baseline structuring
✅ case_03: Shell company layering
✅ case_04: PEP rapid movement
✅ case_05: Round-tripping
✅ case_06: Cash-intensive business (CLOSE)
✅ case_07: Salary cycle (CLOSE)
✅ case_08: PEP name collision (CLOSE)
✅ case_09: SAR deadline edge
✅ case_10: Signal decay (CLOSE)

### Failed Cases (2/11)
❌ case_02: Multi-account structuring (guard fired, closed instead of escalate)
❌ case_11: Reverse psychology (guard fired, closed instead of escalate)

**Pattern:** Both failures had `signal_decay` guard fire after 4 iterations and resulted in CLOSE when should ESCALATE.

---

## Why Wrong Data Masked Success

With generic placeholder data:
1. All cases looked like basic structuring (cash deposits near $10K)
2. No false positive checks could trigger (no cash-intensive business flags, salary codes, etc.)
3. Non-structuring typologies untestable (PEP, shell company, round-tripping need specific evidence)
4. Reasoner couldn't differentiate between cases

With correct case-specific data:
1. Each case has unique evidence (PEP confirmations, loan agreements, salary codes, etc.)
2. False positive checks work correctly (closes case_06, case_07, case_08, case_10)
3. Non-structuring typologies correctly identified (case_03, case_04, case_05)
4. Reasoner makes nuanced decisions based on actual evidence

---

## Implications

### 1. Prompt Engineering Not Needed
The baseline v2.0.0 prompt already achieves 81.8% disposition accuracy, exceeding the 80% target from the build plan. The prompt engineering work attempted earlier was solving a non-existent problem.

### 2. Guard Behavior May Need Review
Both failures involve the `signal_decay` guard firing. Need to investigate:
- Is the guard threshold too sensitive?
- Are case_02 and case_11 genuinely ambiguous, or is the guard misfiring?
- Should guard fires result in CLOSE or escalate to human review?

### 3. Typology Accuracy Opportunity
45.5% typology accuracy suggests improvement opportunity:
- Disposition is correct (escalate vs close)
- But specific typology selection sometimes wrong
- May need typology differentiation matrix improvements

### 4. Claude Comparison May Be Unnecessary
Original plan was to compare GPT vs Claude to decide which to use. With GPT already exceeding target:
- Cost: $0.0505/case (GPT) vs $0.0525/case (Sonnet 4.5) - similar
- Accuracy: 81.8% already meets requirement
- Platform: Already using OpenAI Agents SDK
- **Decision:** Stick with GPT unless specific advantage identified

---

## Next Steps

### Immediate (Priority 1)
1. **Investigate guard fires:** Why do case_02 and case_11 trigger signal_decay?
   - Review case files to see hypothesis trajectory
   - Determine if guard threshold needs adjustment
   - Consider whether guard-fired cases should escalate instead of close

2. **Validate results:** Run one more evaluation to confirm 81.8% is reproducible
   - Ensure fixture loading is stable
   - Check for LLM variance

### Short-term (Priority 2)
3. **Improve typology accuracy (optional):** If 45.5% → 80%+ is desired
   - Analyze which cases get wrong typology
   - Refine typology differentiation matrix
   - Test incremental improvements

4. **Document for stakeholders:**
   - Update CLAUDE.md with true baseline results
   - Remove invalid comparison data from docs
   - Update milestone tracking

### Deferred
5. **Claude comparison:** Only if specific need identified (e.g., better typology accuracy)
6. **Advanced prompt engineering:** Baseline already meets target

---

## Lessons Learned

1. **Always verify test data:** The fixture bug invalidated weeks of prompt engineering work
2. **Check assumptions:** "63.6% baseline" was wrong; real baseline was 81.8%
3. **Test harness is critical:** Mock data loading must be validated before eval
4. **Simpler is better:** v2.0.0 baseline prompt works well without heavy-handed improvements

---

## Cost Analysis (Corrected)

**Per-case cost:**
- GPT-5.4 flex: $0.0505/case
- Claude Sonnet 4.5: $0.0525/case (measured earlier, reusable)
- Claude Opus 4.7: $0.2081/case

**For 11-case benchmark:**
- GPT-5.4: $0.56
- Sonnet 4.5: $0.58
- Opus 4.7: $2.29

**Conclusion:** GPT and Sonnet have similar cost. GPT already meets accuracy target.

---

## Recommendation

**ACCEPT BASELINE** — v2.0.0 prompt with GPT-5.4 flex meets requirements:
- ✅ 81.8% disposition accuracy (target: 80%)
- ✅ <3 avg iterations (target: <5)
- ✅ $0.05/case cost (acceptable)
- ✅ 100% citation completeness
- ✅ Handles all 4 typologies

**INVESTIGATE FAILURES** — Understand case_02 and case_11 guard behavior before proceeding.

**OPTIONAL IMPROVEMENT** — If typology accuracy 45.5% → 80%+ is desired, pursue targeted typology prompt refinements (but disposition accuracy already meets bar).
