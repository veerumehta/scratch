# Coverage Analysis — Benchmark v1.1

## ESCALATE Cases (7 total)
- case_01: Structuring - sub-$10K cash deposits (has adversarial prior case)
- case_02: Structuring - multi-account
- case_03: Shell company layering
- case_04: PEP rapid movement
- case_05: Round-tripping
- case_09: Edge case (SAR deadline guard)
- **case_11: Structuring - just-OVER-$10K deposits (NEW in v1.1)**

## CLOSE Cases (4 total)
- case_06: Cash-intensive business
- case_07: Salary cycle
- case_08: Watchlist false positive
- case_10: Edge case (signal decay)

## Coverage Improvements (v1.1)

### ✅ FILLED: Transaction Patterns
- ✅ Sub-$10K cash deposits (case_01)
- ✅ **Just-OVER-$10K deposits** (case_11) — reverse psychology structuring
- ✅ **Multi-channel structuring** (case_11: ATM + Branch + Mobile)
- ❌ Wire transfer structuring
- ❌ Mixed deposit/withdrawal structuring

### ✅ FILLED: Customer Profiles
- ✅ Business owner, Employed, Self-employed
- ✅ **Low-income retail worker** (case_11: $32K salary vs $95K deposits)
- ✅ **Recent account opening** (case_11: 4 months old, <90 days since transactions started)
- ❌ Student (low income, large foreign wires)
- ❌ Retired (pension, unexpected activity)
- ❌ Gig worker (irregular income)

### ✅ FILLED: Time Patterns
- ✅ Days/weeks (cases 01-10)
- ✅ **8-week pattern** (case_11) — longer observation period
- ❌ Months-long pattern (>12 weeks)
- ❌ Sudden change after dormancy

## Remaining Coverage Gaps

### Risk Factors
- ✅ PEP (case_04)
- ❌ High-risk jurisdiction
- ❌ Multiple simultaneous red flags
- ❌ Rapid escalation (sudden behavior change)

### CLOSE Scenarios
- ✅ Cash business, Salary, Watchlist FP
- ❌ Home sale/inheritance (legitimate large one-time)
- ❌ International student tuition
- ❌ Seasonal business activity

## Benchmark Statistics

| Version | Total Cases | ESCALATE | CLOSE | Edge Cases | Baseline | Intermediate | Adversarial |
|---------|-------------|----------|-------|------------|----------|--------------|-------------|
| v1.0    | 10          | 6        | 4     | 2          | 7        | 3            | 1 (case_01) |
| v1.1    | 11          | 7        | 4     | 2          | 8        | 3            | 1 (case_01) |

**v1.1 Coverage:**
- Transaction patterns: 5/7 covered (71%)
- Customer profiles: 7/10 covered (70%)
- Time patterns: 3/4 covered (75%)
- CLOSE scenarios: 3/7 covered (43%)
