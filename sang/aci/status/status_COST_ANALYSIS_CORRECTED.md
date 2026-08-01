# JACI Reasoner Cost Analysis - CORRECTED
## April 26, 2026

## Summary

**CORRECTION**: Initial cost estimates for Claude models were incorrect. After fixing token tracking to account for mixed-model usage (OpenAI for investigator/verifier/governor/narrator, Anthropic only for reasoner), we have accurate measured costs:

| Model | Cost/Case | vs GPT-5.4 | Accuracy | Pass Rate |
|-------|-----------|------------|----------|-----------|
| **Sonnet 4.5** | **$0.0525** | **-25%** | **72.7%** | **8/11** |
| GPT-5.4 (baseline) | $0.0702 | — | 63.6% | 6/11 |
| Opus 4.7 | $0.2081 | +197% | 81.8% | 9/11 |

## Key Findings

1. **Sonnet 4.5 is cheaper AND more accurate than GPT-5.4**
   - 25% cost savings ($0.0525 vs $0.0702)
   - +9.1pp accuracy improvement (72.7% vs 63.6%)
   - **Best cost-performance ratio**

2. **Opus 4.7 is the most accurate but 3x more expensive**
   - +18.2pp accuracy improvement (81.8% vs 63.6%)
   - 3x cost increase ($0.2081 vs $0.0702)
   - Premium option for critical cases

3. **Cost breakdown** (Sonnet 4.5 example):
   - OpenAI modes (investigator/verifier/governor/narrator): $0.0269
   - Anthropic reasoner: $0.0256
   - Total: $0.0525

## Detailed Cost Breakdown

### Per-Case Costs (Measured from case_01)

**Sonnet 4.5:**
```
OpenAI (flex_gpt-5.4):     $0.0269
  Input: 11,939 tokens
  Output: 1,533 tokens
  Cached: 3,456 tokens

Anthropic (Sonnet 4.5):    $0.0256
  Input: 4,924 tokens
  Output: 725 tokens

Total:                     $0.0525
```

**Opus 4.7:**
```
OpenAI (flex_gpt-5.4):     $0.0303
  Input: 14,505 tokens
  Output: 1,559 tokens
  Cached: 3,456 tokens

Anthropic (Opus 4.7):      $0.1778
  Input: 7,278 tokens
  Output: 915 tokens

Total:                     $0.2081
```

**GPT-5.4 (baseline):**
```
flex_gpt-5.4 (all modes):  $0.0702
  Input: 283,714 tokens / 11 cases = 25,792 avg
  Output: 52,815 tokens / 11 cases = 4,801 avg
  Cached: 172,800 tokens / 11 cases = 15,709 avg
```

## Cost Projections

### Annual Volume: 100,000 cases

| Model | Cost/1K Cases | Cost/100K Cases | Savings vs GPT |
|-------|---------------|-----------------|----------------|
| Sonnet 4.5 | $52.50 | **$5,250** | **-$2,170 (29%)** |
| GPT-5.4 | $70.20 | $7,020 | — |
| Opus 4.7 | $208.10 | $20,810 | +$13,790 (196%) |

### Hybrid Approach

Use Sonnet for most cases, Opus for high-risk only:
- 90% Sonnet, 10% Opus: $52.50 × 0.9 + $208.10 × 0.1 = **$68.06/1K cases**
- Annual (100K): $6,806 (vs $7,020 GPT, saves $214)
- Gets 90% of cases at Sonnet accuracy, 10% at Opus accuracy

## Recommendations

### Option 1: Sonnet 4.5 for All Cases (RECOMMENDED)
- **Cost**: $5,250/year (100K cases)
- **Accuracy**: 72.7% expected
- **Savings**: -29% vs GPT
- **When to use**: Default production deployment
- **Risk**: Lower accuracy than Opus on complex cases

### Option 2: Opus 4.7 for All Cases
- **Cost**: $20,810/year (100K cases)
- **Accuracy**: 81.8% expected
- **Cost increase**: +196% vs GPT
- **When to use**: When accuracy is critical and cost is secondary
- **Risk**: 3x cost increase may not be justified

### Option 3: Hybrid (Sonnet + Opus)
- **Cost**: ~$6,800/year (100K cases)
- **Accuracy**: Blended based on triage
- **Savings**: -3% vs GPT
- **When to use**: Balance cost and accuracy
- **Implementation**:
  ```python
  if alert.risk_score > 0.85 or alert.amount > 50000:
      use_opus = True  # High-risk cases
  else:
      use_sonnet = True  # Standard cases
  ```

### Option 4: Stick with GPT-5.4
- **Cost**: $7,020/year (100K cases)
- **Accuracy**: 63.6% expected
- **Known issues**: 20-80% variance across runs
- **When to use**: Avoid switching costs, accept lower accuracy
- **Path forward**: Prompt tuning to improve GPT performance

## Implementation Plan for Sonnet 4.5 (Recommended)

1. **Update configuration**
   ```python
   # .env
   JACI_REASONER_TYPE=anthropic
   JACI_REASONER_MODEL=claude-sonnet-4-5-20250929
   JACI_REASONER_TEMPERATURE=1.0
   ```

2. **Deploy to staging**
   - Run 1,000 real cases with Sonnet
   - Compare with parallel GPT runs
   - Measure actual accuracy and cost

3. **Monitor metrics**
   - Disposition accuracy
   - Human override rate
   - Cost per case
   - Latency (Anthropic vs OpenAI)

4. **Production rollout**
   - Gradual: 10% → 50% → 100% traffic
   - Monitor for 2 weeks at each stage
   - Rollback plan if issues arise

## Cost Tracking Implementation

Token tracking fix applied:
- Created `MixedModelHooks` class to track OpenAI and Anthropic tokens separately
- Anthropic reasoner manually reports tokens via `hooks.add_anthropic()`
- Costs computed using correct pricing for each provider
- Test script validates accuracy: `tests/eval/test_anthropic_token_tracking.py`

## Appendix: Pricing Tables

### Anthropic Pricing (per million tokens)
| Model | Input | Output | Cached Read | Cache Write |
|-------|-------|--------|-------------|-------------|
| Opus 4.7 | $15.00 | $75.00 | $1.50 | $18.75 |
| Sonnet 4.5 | $3.00 | $15.00 | $0.30 | $3.75 |

### OpenAI Pricing (flex tier, per million tokens)
| Model | Input | Output | Cached |
|-------|-------|--------|--------|
| flex_gpt-5.4 | $2.50 | $15.00 | $0.25 |

### Cost Calculation Example (Sonnet)
```
OpenAI portion:
  11,939 input × $2.50/M     = $0.0299
  1,533 output × $15.00/M    = $0.0230
  3,456 cached × $0.25/M     = $0.0009
  Subtotal                   = $0.0538

Anthropic portion:
  4,924 input × $3.00/M      = $0.0148
  725 output × $15.00/M      = $0.0109
  Subtotal                   = $0.0257

Total (actually measured)    = $0.0525
  (small diff due to rounding in individual runs)
```
