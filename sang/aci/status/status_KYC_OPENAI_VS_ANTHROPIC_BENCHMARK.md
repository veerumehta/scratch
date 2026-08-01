# KYC OpenAI vs Anthropic Benchmark

This document describes how to run benchmarks comparing the OpenAI-based KYC implementation against the Anthropic-based KYC implementation.

## Overview

JACI now includes two complete KYC implementations:

1. **`kyc`** (OpenAI-based) - Uses OpenAI (gpt-4o) via JAPES Agent Execution Layer
2. **`kyc-anthropic`** - Uses Anthropic (claude-sonnet-4-5) with extended thinking and financial tool support

Both implementations use:
- The same gold case test suite
- The same KYC tool registry for evidence gathering
- The same evaluation metrics (accuracy, confidence, cost, latency)

## Architecture Comparison

### KYC (OpenAI-based)
```
Pack ID: kyc-openai-core
Models: gpt-4o (all modes)
Provider: OpenAI via JAPES Agent Execution Layer

Modes:
- KYCInvestigatorMode (OpenAI)
- KYCVerifierMode (OpenAI)
- KYCReasonerMode (OpenAI)
- KYCGovernorMode (OpenAI)
- KYCNarratorMode (OpenAI)

Conductor: KYCConductor
```

### KYC-Anthropic
```
Pack ID: kyc-anthropic-cdd-lifecycle
Models: claude-sonnet-4-5 (all modes)
Provider: Anthropic with extended thinking

Modes:
- KYCAnthropicInvestigatorMode
- KYCAnthropicVerifierMode
- KYCAnthropicReasonerMode
- KYCAnthropicGovernorMode
- KYCAnthropicNarratorMode

Conductor: KYCAnthropicConductor
```

## Running Evaluations

### Prerequisites

```bash
# Ensure API keys are set
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Install dependencies
poetry install
```

### Run OpenAI Evaluation

```bash
# Run OpenAI-based KYC evaluation
poetry run python tests/eval/run_kyc_openai_eval.py

# With custom notes
poetry run python tests/eval/run_kyc_openai_eval.py "Testing gpt-4o performance on KYC gold cases"
```

Output location: `output/kyc_openai_evaluations/run_YYYYMMDD_HHMMSS/`

### Run Anthropic Evaluation

```bash
# Run Anthropic-based KYC evaluation
poetry run python tests/eval/run_kyc_eval.py

# With custom notes
poetry run python tests/eval/run_kyc_eval.py "Testing claude-sonnet-4-5 with extended thinking"
```

Output location: `output/kyc_evaluations/run_YYYYMMDD_HHMMSS/`

### Run Both for Direct Comparison

```bash
# Run both evaluations back-to-back
poetry run python tests/eval/run_kyc_openai_eval.py "OpenAI baseline" && \
poetry run python tests/eval/run_kyc_eval.py "Anthropic baseline"

# Compare results
python tests/eval/compare_kyc_results.py \
  output/kyc_openai_evaluations/run_*/report.json \
  output/kyc_evaluations/run_*/report.json
```

## Evaluation Metrics

Both evaluations report the same metrics for direct comparison:

### Accuracy Metrics
- **Risk Rating Accuracy**: % of cases where risk tier (LOW/MEDIUM/HIGH/PROHIBITED) matches gold standard
- **Disposition Accuracy**: % of cases where disposition (clear/request-docs/escalate-EDD/decline) matches
- **EDD Decision Accuracy**: % of cases where EDD decision (required/not_required) matches
- **Policy Citation Completeness**: % of cases where all required policy references are cited

### Performance Metrics
- **Avg Iterations**: Average number of investigation iterations per case
- **Total Cost**: Total API cost in USD for all cases
- **Avg Cost Per Case**: Average cost per case
- **Total Latency**: Total processing time in seconds
- **Avg Latency Per Case**: Average processing time per case

### Pass Criteria
A case passes if **both** risk rating AND disposition are correct.

## Gold Cases

Both evaluations use the same gold cases from `tests/eval/gold_cases/kyc_anthropic/`:

- **case_01.json**: BVI + PEP → HIGH/escalate-EDD
- **case_02.json**: Clean Canadian → LOW/clear
- **case_03.json**: Missing docs → MEDIUM/request-docs
- **case_04.json**: OFAC Sanctions → PROHIBITED/decline-recommend
- **case_09.json**: Iran Sanctions → PROHIBITED/decline-recommend

Each case includes:
- `review_trigger`: Customer profile and review context
- `expected_outcome`: Gold standard risk rating, disposition, and required policy refs

## Expected Results

### Hypothesis: Anthropic Outperforms on Financial Reasoning

We expect Anthropic to perform better because:
1. **Extended thinking**: Claude Sonnet 4.5 has specialized reasoning for financial compliance
2. **Financial tool support**: Anthropic's KYC Screener provides domain-specific prompts
3. **Policy understanding**: Better at parsing complex regulatory requirements

### Hypothesis: OpenAI Competes on Cost

We expect OpenAI to be more cost-effective:
1. **Lower token costs**: gpt-4o generally cheaper per token than claude-sonnet-4-5
2. **Faster inference**: OpenAI typically has lower latency
3. **Structured output**: Both support structured outputs equally well

### Preliminary Benchmarks

| Metric | KYC-OpenAI (gpt-4o) | KYC-Anthropic (claude-sonnet-4-5) |
|--------|---------------------|-----------------------------------|
| Risk Rating Accuracy | TBD | TBD |
| Disposition Accuracy | TBD | TBD |
| Avg Cost Per Case | TBD | TBD |
| Avg Latency Per Case | TBD | TBD |

**TODO**: Run initial benchmarks and populate this table.

## Analyzing Results

### Compare Accuracy

```bash
# View OpenAI results
cat output/kyc_openai_evaluations/run_*/report.json | jq '.summary'

# View Anthropic results
cat output/kyc_evaluations/run_*/report.json | jq '.summary'

# Compare disposition accuracy
echo "OpenAI: $(cat output/kyc_openai_evaluations/run_*/report.json | jq '.summary.disposition_accuracy')"
echo "Anthropic: $(cat output/kyc_evaluations/run_*/report.json | jq '.summary.disposition_accuracy')"
```

### Compare Cost

```bash
# Compare total costs
echo "OpenAI Total Cost: $(cat output/kyc_openai_evaluations/run_*/report.json | jq '.summary.total_cost_usd')"
echo "Anthropic Total Cost: $(cat output/kyc_evaluations/run_*/report.json | jq '.summary.total_cost_usd')"

# Compare per-case costs
echo "OpenAI Avg Cost: $(cat output/kyc_openai_evaluations/run_*/report.json | jq '.summary.avg_cost_per_case_usd')"
echo "Anthropic Avg Cost: $(cat output/kyc_evaluations/run_*/report.json | jq '.summary.avg_cost_per_case_usd')"
```

### Compare Latency

```bash
# Compare average latency
echo "OpenAI Avg Latency: $(cat output/kyc_openai_evaluations/run_*/report.json | jq '.summary.avg_latency_per_case_seconds')s"
echo "Anthropic Avg Latency: $(cat output/kyc_evaluations/run_*/report.json | jq '.summary.avg_latency_per_case_seconds')s"
```

### Review Individual Cases

```bash
# Find cases where OpenAI passed but Anthropic failed (or vice versa)
python -c "
import json
from pathlib import Path

# Load reports
openai_report = json.load(open(list(Path('output/kyc_openai_evaluations').glob('run_*/report.json'))[0]))
anthropic_report = json.load(open(list(Path('output/kyc_evaluations').glob('run_*/report.json'))[0]))

# Compare results
for o_res, a_res in zip(openai_report['results'], anthropic_report['results']):
    if o_res['passed'] != a_res['passed']:
        print(f\"DIFFERENCE: {o_res['case_id']}\")
        print(f\"  OpenAI: {'PASS' if o_res['passed'] else 'FAIL'}\")
        print(f\"  Anthropic: {'PASS' if a_res['passed'] else 'FAIL'}\")
        print()
"
```

## Implementation Details

### Key Files

**OpenAI-based (kyc):**
- `src/jaci/scenarios/kyc/conductor.py` - Main orchestrator
- `src/jaci/scenarios/kyc/modes/investigator.py` - Risk hypothesis generation
- `src/jaci/scenarios/kyc/modes/reasoner.py` - Risk tier recommendation
- `src/jaci/scenarios/kyc/modes/verifier.py` - Evidence attestation
- `src/jaci/scenarios/kyc/modes/governor.py` - Policy enforcement
- `src/jaci/scenarios/kyc/modes/narrator.py` - Report generation
- `tests/eval/run_kyc_openai_eval.py` - Evaluation harness

**Anthropic-based (kyc-anthropic):**
- `src/jaci/scenarios/kyc_anthropic/conductor.py` - Main orchestrator
- `src/jaci/scenarios/kyc_anthropic/modes/investigator.py` - Risk hypothesis generation
- `src/jaci/scenarios/kyc_anthropic/modes/reasoner.py` - Risk tier recommendation
- `src/jaci/scenarios/kyc_anthropic/modes/verifier.py` - Evidence attestation
- `src/jaci/scenarios/kyc_anthropic/modes/governor.py` - Policy enforcement
- `src/jaci/scenarios/kyc_anthropic/modes/narrator.py` - Report generation
- `tests/eval/run_kyc_eval.py` - Evaluation harness

### Shared Components

Both implementations share:
- `src/jaci/scenarios/kyc/schemas/kyc_schemas.py` - Data models
- `src/jaci/scenarios/kyc/tools/kyc_registry.py` - Evidence gathering tools
- `tests/fixtures/kyc_case_fixtures.py` - Test data fixtures
- `tests/eval/gold_cases/kyc_anthropic/` - Gold standard test cases

## Next Steps

1. **Run Initial Benchmarks**: Execute both evaluations on gold cases
2. **Analyze Trade-offs**: Compare accuracy, cost, and latency
3. **Tune Hyperparameters**: Adjust temperature, max_tokens, etc. for better performance
4. **Expand Gold Cases**: Add more complex scenarios (multi-jurisdiction, complex BO structures)
5. **Add Model Variants**: Test gpt-4o-mini, claude-haiku, etc. for cost optimization
6. **Cost Attribution**: Integrate JAPES cost tracker for precise cost measurement

## Questions for Investigation

1. Does Anthropic's extended thinking meaningfully improve accuracy on complex KYC cases?
2. Can OpenAI match Anthropic's accuracy at lower cost?
3. Which provider is better for specific risk tiers (LOW vs HIGH vs PROHIBITED)?
4. Does latency impact production deployment decisions?
5. How do confidence scores calibrate across providers?

## Contributing

To add more gold cases or evaluation metrics:

1. Add new test cases to `tests/eval/gold_cases/kyc_anthropic/case_NN.json`
2. Add corresponding fixtures to `tests/fixtures/kyc_case_fixtures.py`
3. Update both evaluation harnesses if metrics change
4. Document expected outcomes in case files

---

**Last Updated**: 2026-05-27
**JACI Version**: 1.1.0
