# Claude Reasoner Comparison — Setup Summary

**Date:** April 25, 2026
**Status:** Ready to run

## What Was Built

### 1. Anthropic-Native Reasoner (`src/jaci/modes/reasoner_anthropic.py`)

A parallel implementation of ReasonerMode that uses Anthropic's API directly instead of the OpenAI Agents SDK.

**Key features:**
- Direct Anthropic API integration
- Same interface as ReasonerMode
- Configurable temperature
- Token usage tracking
- JSON response parsing from Claude models

**Supported models:**
- `claude-sonnet-4-5-20250929` (Sonnet 4.5)
- `claude-sonnet-4-6` (Sonnet 4.6)
- `claude-opus-4-5-20251101` (Opus 4.5)
- `claude-opus-4-7` (Opus 4.7)

### 2. Anthropic Evaluation Harness (`tests/eval/run_eval_anthropic.py`)

Modified evaluation script that uses AnthropicReasonerMode while keeping all other modes on OpenAI.

**Usage:**
```bash
# Sonnet 4.5
ANTHROPIC_REASONER_MODEL=claude-sonnet-4-5-20250929 python tests/eval/run_eval_anthropic.py

# Opus 4.7
ANTHROPIC_REASONER_MODEL=claude-opus-4-7 python tests/eval/run_eval_anthropic.py

# Sonnet 4.6
ANTHROPIC_REASONER_MODEL=claude-sonnet-4-6 python tests/eval/run_eval_anthropic.py
```

**Tracks in MLflow:**
- `reasoner_type: anthropic`
- `reasoner_model: claude-*`
- `reasoner_temperature`
- All standard evaluation metrics

### 3. Comparison Script (`run_claude_comparison.sh`)

Automated runner that executes:
1. Sonnet 4.5 eval
2. Opus 4.7 eval
3. GPT-5.4 baseline eval (for comparison)

**Run:**
```bash
./run_claude_comparison.sh
```

**Duration:** ~30-40 minutes (11 cases × 3 models, 10s delay between cases)

### 4. Sanity Test (`tests/test_anthropic_reasoner.py`)

Quick verification that both Sonnet and Opus models work correctly.

**Run:**
```bash
python tests/test_anthropic_reasoner.py
```

**Output:**
```
✓ Sonnet 4.5 Success - Tokens: ~4100
✓ Opus 4.7 Success - Tokens: ~6000
✅ Both models work correctly!
```

## Comparison Hypothesis

### Current Baseline (GPT-5.4)
- **Accuracy:** 43.3% ± 25.2% (high variance)
- **Issue:** Inconsistent multi-factor reasoning, over-escalates false positives
- **Temperature:** Default (~1.0)

### Expected Results

**Sonnet 4.5:**
- Better nuanced reasoning than GPT-5.4
- Lower variance (15-20% std dev)
- Better false positive detection
- Lower cost than Opus
- **Predicted accuracy:** 55-65%

**Opus 4.7:**
- Best multi-factor reasoning capability
- Lowest variance (10-15% std dev)
- Best false positive vs true alert differentiation
- Higher cost (2-3x Sonnet)
- **Predicted accuracy:** 65-75%

## Files Created/Modified

```
src/jaci/modes/reasoner_anthropic.py     (created - 200 lines)
src/jaci/modes/__init__.py               (modified - added AnthropicReasonerMode export)
tests/eval/run_eval_anthropic.py         (created - 250 lines)
tests/test_anthropic_reasoner.py         (created - sanity test)
run_claude_comparison.sh                 (created - comparison runner)
docs/CLAUDE_REASONER_COMPARISON.md       (this file)
```

## Running the Comparison

### Option 1: Full Automated Comparison (Recommended)
```bash
./run_claude_comparison.sh
```

Runs all three models sequentially. Total time: ~35 minutes.

### Option 2: Individual Runs

**Sonnet 4.5 only:**
```bash
ANTHROPIC_REASONER_MODEL=claude-sonnet-4-5-20250929 \
python tests/eval/run_eval_anthropic.py
```

**Opus 4.7 only:**
```bash
ANTHROPIC_REASONER_MODEL=claude-opus-4-7 \
python tests/eval/run_eval_anthropic.py
```

**GPT-5.4 baseline (for comparison):**
```bash
python tests/eval/run_eval.py
```

### Option 3: Multi-Run Variance Testing

Test variance with 3 runs per model:

```bash
# Sonnet 4.5 (3 runs)
for i in {1..3}; do
  ANTHROPIC_REASONER_MODEL=claude-sonnet-4-5-20250929 \
  python tests/eval/run_eval_anthropic.py
  sleep 5
done

# Opus 4.7 (3 runs)
for i in {1..3}; do
  ANTHROPIC_REASONER_MODEL=claude-opus-4-7 \
  python tests/eval/run_eval_anthropic.py
  sleep 5
done
```

## Viewing Results

### Experiment Metadata (JSON)
```bash
# View last 3 experiments
cat experiments/experiments.json | jq '.experiments[-3:]'

# Filter by reasoner type
cat experiments/experiments.json | jq '.experiments[] | select(.model | contains("anthropic"))'
```

### MLflow UI
```bash
mlflow ui
```

Navigate to runs and filter by:
- `reasoner_type = anthropic`
- `reasoner_model = claude-sonnet-4-5-20250929`
- `reasoner_model = claude-opus-4-7`

### Evaluation Reports
```bash
# List recent reports
ls -lht output/evaluations/ | head -10

# View Sonnet 4.5 report
cat output/evaluations/eval_anthropic_sonnet-4-5-20250929_*.json | jq '.summary'

# View Opus 4.7 report
cat output/evaluations/eval_anthropic_opus-4-7_*.json | jq '.summary'
```

## Cost Estimation

Based on Anthropic pricing (April 2026):

| Model | Input | Output | Est. Cost/Case | Est. Total (11 cases) |
|-------|-------|--------|----------------|----------------------|
| Sonnet 4.5 | $3/MTok | $15/MTok | ~$0.08 | ~$0.88 |
| Opus 4.7 | $15/MTok | $75/MTok | ~$0.30 | ~$3.30 |
| GPT-5.4 (baseline) | varies | varies | ~$0.08 | ~$0.88 |

**Full comparison (3 models):** ~$5.06

## Success Criteria

**Minimum acceptable improvement:**
- Disposition accuracy: 43% → 55%+ (GPT baseline → Claude)
- Variance: 25% → <15% std dev

**Strong evidence for Claude adoption:**
- Disposition accuracy: 60%+
- Variance: <10% std dev
- Consistent ESCALATE case handling (no systematic closing)

**Decision matrix:**

| Sonnet 4.5 Result | Opus 4.7 Result | Recommendation |
|-------------------|-----------------|----------------|
| >60%, <15% var | >70%, <10% var | Adopt Opus 4.7 (best capability) |
| >60%, <15% var | 60-70%, similar var | Adopt Sonnet 4.5 (cost efficiency) |
| >55%, 15-20% var | >65%, <15% var | Adopt Opus 4.7 (variance matters) |
| <55% or >20% var | <60% or >15% var | Investigate prompt tuning first |

## Next Steps After Comparison

### If Claude models perform well:
1. Update CLAUDE.md with recommended model
2. Set default reasoner to best-performing Claude model
3. Document cost/performance trade-offs
4. Consider ensemble voting (if variance still >10%)

### If Claude models don't improve enough:
1. Analyze failure modes (same as GPT or different?)
2. Try prompt engineering for Claude-specific reasoning patterns
3. Consider structured outputs with Claude
4. Investigate Investigator mode variance (may be root cause)

### If results are mixed:
1. Hybrid approach: Claude for ESCALATE decisions, GPT for CLOSE
2. Ensemble: Run both, use confidence-weighted voting
3. Case-specific routing: Complex cases → Opus, simple → Sonnet

## Technical Notes

### AnthropicReasonerMode Implementation

**Key differences from ReasonerMode:**
- Uses `anthropic.Anthropic()` client directly (not Agents SDK)
- Manual JSON response parsing (no automatic structured output)
- Temperature passed to API (not just ModelSettings)
- Token counting from response.usage

**Compatible with:**
- All existing prompts in `prompts/reasoner.md`
- Same CaseContext input format
- Same DispositionRecommendation output format
- Conductor pattern (no changes needed)

### Why Not Use Agents SDK?

The OpenAI Agents SDK doesn't support Anthropic models. We could:
1. Use this custom implementation (current approach)
2. Switch to a multi-provider agents framework (e.g., LangChain)
3. Refactor modes to be provider-agnostic

Current approach is fastest for testing. If Claude performs well, consider #3 for production.

## Summary

✅ **Anthropic reasoner integration complete**
✅ **Sanity tested: Sonnet 4.5 and Opus 4.7 both work**
✅ **Comparison script ready to run**
✅ **MLflow tracking configured**

**Ready to run:** `./run_claude_comparison.sh`
