# Case 11 Addition — Completion Summary

**Date:** April 25, 2026
**Benchmark Version:** v1.1

## What Was Completed

### 1. Created case_11 Gold Case
**File:** `tests/eval/gold_cases/case_11.json`

**Design characteristics:**
- **Label:** ESCALATE
- **Typology:** structuring
- **Difficulty:** baseline (clean, no adversarial elements)
- **Coverage additions:**
  - Transaction pattern: Just-OVER-$10K deposits ($10,100-$10,800)
  - Customer profile: Low-income retail worker ($32K salary vs $93K deposits)
  - Time pattern: 8 weeks (longer than existing 2-4 week cases)
  - Channel mix: ATM + Branch + Mobile (multi-channel structuring)
  - Account velocity: Recent account (4 months old)
  - No prior cases (clean baseline vs case_01's adversarial prior case)

### 2. Created case_11 Fixture Data
**File:** `tests/fixtures/case_fixtures.py`

**Added CASE_11 with:**
- 9 cash deposits totaling $93,350 over 8 weeks
- Customer: Sarah Chen, 28, retail sales associate
- Annual income: $32,000 (income/deposit mismatch of 2.9x)
- No prior cases (empty list)
- 2 similar escalated cases (ESCALATE_SAR_FILED)
- Geographic spread: San Francisco, Oakland, Berkeley
- Registered in FIXTURES dict as `"case_11": CASE_11`

### 3. Updated Documentation

**Created:**
- `docs/BENCHMARK_VERSION.md` — Version history and comparability guide
- `docs/COVERAGE_ANALYSIS.md` — Updated coverage matrix for v1.1

**Modified:**
- `tests/fixtures/case_fixtures.py` — Updated docstring to reflect 11 cases (v1.1)
- Referenced benchmark versioning in fixture comments

### 4. Verification

**Fixture integrity verified:**
```
✓ case_11 loaded from FIXTURES
✓ Transactions: 9
✓ Customer: Sarah Chen
✓ Annual income: $32,000
✓ Total deposits: $93,350
✓ Prior cases: 0 (clean baseline)
✓ Similar cases: 2 (both ESCALATE_SAR_FILED)
✓ Policy clauses: 3 (BSA-CTR-001, FinCEN-STRUCT-002, BSA-SAR-TRIGGER-001)
✓ Multi-channel: BRANCH, ATM, MOBILE
```

**Gold case count:**
```
Total: 11 cases
ESCALATE: 7 cases
CLOSE: 4 cases
```

## Benchmark Versioning

**v1.0 → v1.1 Comparison:**
- cases 01-10 unchanged (fully comparable)
- case_11 added (new baseline ESCALATE structuring)
- Historical metrics on cases 01-10 remain valid
- Total accuracy denominator changed from 10 to 11

**Metric conversion:**
```python
# To compare v1.1 to v1.0 historical results
v1_1_comparable = (passed_count for cases 01-10) / 10
v1_1_full = (passed_count for cases 01-11) / 11
```

## Coverage Improvements (v1.0 → v1.1)

| Coverage Area | v1.0 | v1.1 | Improvement |
|---------------|------|------|-------------|
| Transaction patterns | 4/7 | 5/7 | +1 (reverse psychology structuring) |
| Customer profiles | 5/10 | 7/10 | +2 (low income, recent account) |
| Time patterns | 2/4 | 3/4 | +1 (8-week observation) |
| CLOSE scenarios | 3/7 | 3/7 | — |
| **Total cases** | **10** | **11** | **+1** |

## Next Steps

### Recommended Actions:

1. **Run baseline eval with case_11:**
   ```bash
   MODEL_NAME=flex_gpt-5.4 python tests/eval/run_eval.py
   ```
   Expected: case_11 should pass (baseline, clean fixture)

2. **Compare v1.0 vs v1.1 metrics:**
   - Run eval on cases 01-10 only (v1.0 comparable)
   - Run full eval on cases 01-11 (v1.1 full)
   - Verify case_11 adds expected coverage

3. **Update CLAUDE.md:**
   - Reference benchmark v1.1 in synthetic dataset section
   - Note case_01 as "adversarial" baseline
   - Note case_11 as "clean" baseline for structuring

4. **Document in evaluation results:**
   - Tag all future evals with benchmark version (v1.0 or v1.1)
   - Separate metrics: overall accuracy vs baseline-only accuracy

## Files Modified

```
tests/eval/gold_cases/case_11.json          (created)
tests/fixtures/case_fixtures.py             (modified: added CASE_11, updated docstring)
docs/BENCHMARK_VERSION.md                   (created)
docs/COVERAGE_ANALYSIS.md                   (created)
docs/CASE_11_COMPLETION.md                  (this file)
```

## Summary

✅ **Benchmark v1.1 complete** with 11 gold cases (7 ESCALATE, 4 CLOSE)
✅ **Backward compatible** with v1.0 (cases 01-10 unchanged)
✅ **Coverage expanded** across 3 dimensions: transaction patterns, customer profiles, time patterns
✅ **Clean baseline added** for structuring (case_11) alongside adversarial baseline (case_01)

**User request fulfilled:** "don't just copy 1 to 11, pick some other characteristics also so the benchmark grows in coverage" ✓
