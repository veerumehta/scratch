# JACI C&I Spread -- Build Plan

**Author:** Virendra Mehta
**Scope:** Full buildout of `ci_spread` scenario pack -- schema tree, policy expert, tool
registry, conductor (with PRD pipeline stages 1-3), two golden cases, Jazz assistant live
LLM wiring, prompt loader fix, and CRE conductor forward path.
**Execute with:** Claude Code from repo root `/Users/sangit/src/jaci/`

---

## STATUS: FULLY EXECUTED -- jaci 0.7.0 through 0.7.4

All 16 steps are done. Step 17 was skipped (obsolete -- see below).
The plan is retained as a historical record. The code is authoritative.

### Steps 1-12 (original buildout -- jaci 0.7.0-0.7.1)

| Step | Outcome |
|---|---|
| 1 Schemas | DONE -- LoanType/Purpose/Decision/RiskRating/SpreadIssueType, LoanApplication, SpreadHypothesis, BorrowingBase, UCAcashFlow, CICondition, CreditRecommendation, CIContext, CaseFile |
| 2 Policy registry | DONE -- 5 policies (4 core + RB overlay), CI_REGISTRY, CI_CORE_POLICY_IDS, OVERLAY_MAP |
| 3 CIPolicyExpert | DONE -- subclasses DefaultPolicyExpert, overlay-aware resolve(), check_compliance() against all 4 core policies |
| 4 CIToolRegistry | DONE -- 7 tools (financial_statements, bbc, ar_aging, debt_schedule, bank_statements, ucc_search, policy_clause), YETI mocks |
| 5 Conductor | DONE -- full AML-pattern loop (Investigator -> Verifier -> Sentinel -> Reasoner -> PolicyExpert -> Governor -> Narrator -> CanonicalTrace.for_pack()); base Context loop methods used |
| 6 Evaluator mode | DONE -- compute_deterministic_metrics (decision_accuracy, bbc_accuracy, lien_flag_accuracy, condition_coverage, risk_identification) |
| 7 Mode tuning prompts | DONE -- investigator.md, reasoner.md, governor.md, narrator.md in config/packs/ci-spread-core/mode_tuning/ |
| 8 prompt_loader fix | DONE -- ci_spread in scenario resolution map; prompts/ci_spread/.gitkeep |
| 9 Golden cases | DONE -- tests/fixtures/golden_cases/ci_spread/yeti_abl.json + techflow_term.json |
| 10 Jazz live LLM | DONE -- _get_jazz_response() calls Anthropic claude-sonnet-4-5 with YETI financial context; spinner + APIError handling |
| 11 __init__.py | DONE -- exports all schema classes + CIConductor |
| 12 Smoke tests | DONE -- all pass; 317 passed / 17 skipped |

### Steps 13-17 (PRD pipeline stages -- jaci 0.7.2-0.7.4)

| Step | Outcome | API corrections applied vs. plan |
|---|---|---|
| 13 Document intake (Phase 0) | DONE | `Evidence` has `data` (required dict), not `content`. `DocStore.put(content: bytes, name=...)` -- no pack_id/doc_id. `run_analysis` gains `document_paths=None, structured_data=None`. `CaseFile.intake_mode` added. |
| 14 Entity extraction + KG (Phase 1) | DONE (best-effort) | `LLMManager` not `LLMClient`; `LLMManager.run(system_prompt=, prompt=, model=, max_tokens=)` async. `KGStore` not `GraphStore` (fabric.graph properly wired in JAPES 1.6.5). `add_triple(subject, predicate, object, source=...)` -- no metadata param, needs kh_client. Entire body in one top-level try/except; skips when no evidence (tools path). |
| 15 Evaluator wiring | DONE | `EvaluationReport(scores=..., outcome_id=..., period_start=...)` -- not `metrics=`/`ground_truth_id=`. `CaseFile.evaluation_report` added. `CIConductor(ground_truth=...)`. |
| 16 Trace tab (Track A) | DONE | Fixture-driven trace from yeti_abl.json + Track B stub button. Golden-case path uses 6 parents to repo root. |
| 17 CRE TODO comment | **SKIPPED -- OBSOLETE** | CRE fixed in 0.7.3 (for_pack + base Context loop methods). JAPES patch shipped as 1.6.4. Planned comment would document non-existent bugs -- actively misleading, not added. |

**Verified (0.7.4):** structured_data + tools intake paths complete under mock ctx; evaluator
metrics all 1.0 on YETI golden case; EvaluationReport constructs; 317 passed / 17 skipped.
Phase 1 live LLM/KG calls are best-effort -- fail cleanly without keys/KH client, conductor
completes normally.

---

## What remains (forward work -- not in this plan)

These items were identified during execution but are out of scope for this plan:

**Phase 1 caller migration:** ci_spread Phase 1 uses `KGStore` but the call is best-effort
because no `kh_client` is wired at demo time. Once `fabric.graph` defaulting is resolved
(plan_JAPES_FABRIC_GRAPH.md), pass `MockKnowledgeHubClient` or real KH client so KG writes
actually land. See `plan_caller_migration_jaci_k9.md`.

**Track B -- live conductor from UI:** The "Run conductor" button in the Trace tab shows
a stub `st.info()`. Full async conductor execution from Streamlit (with live CanonicalTrace
rendering) is deferred. Requires resolving async/Streamlit threading before implementing.

**Shared commercial_lending pipeline:** Once ci_spread's Phase 0-1 is verified end-to-end
with real PDFs (not just the JSON fixture), extract `_run_document_intake()` and
`_run_entity_extraction()` into a shared `commercial_lending/pipeline.py` module. CRE
conductor imports from there rather than duplicating. This is the PRD's intended architecture
for the multi-segment commercial lending pack.

**CRE Phase 0-1:** CRE conductor is fixed (0.7.3) but has no document intake or entity
extraction. Inherits from shared pipeline module once that exists.

**AML investigator guide sync:** `k9/docs/aml_investigator_guide.md` (v1.0.0, 2026-04-28)
is newer and better than `config/packs/aml_investigation_core/mode_tuning/investigator.md`
(v2.1.0, 2026-04-23). Sync the k9 version into jaci. Check whether k9 has equivalent
improvements for governor/reasoner/verifier tuning files.

---

## Context & Constraints (retained for reference)

- Pack ID: `ci-spread-core`
- JAPES SDK at `/Users/sangit/src/japes/`, installed editable in jaci venv.
- Do NOT import anything from `ci_spread/` back into `japes/`.
- No em-dashes anywhere in code or comments -- use hyphens.
- The PRD ("Commercial Lending with Platform 2.0") defines three pipeline stages:
  Stage 1 (ingest/classify), Stage 2 (entity extraction/KG), Stage 3 (spread/grade).
  All three are now implemented in `run_analysis()`.

---

## File tree (complete -- all exist)

```
src/jaci/scenarios/ci_spread/
  __init__.py
  conductor.py                    -- run_analysis(app, document_paths=None, structured_data=None, ground_truth=None)
  schemas/
    __init__.py                   -- all schema classes incl. CaseFile(intake_mode, evaluation_report)
  experts/
    __init__.py
    policy.py                     -- CIPolicyExpert
  policies/
    __init__.py
    registry.py                   -- CI_REGISTRY, OVERLAY_MAP
  tools/
    __init__.py
    registry.py                   -- CIToolRegistry, 7 tools, YETI mocks
  modes/
    __init__.py
    evaluator.py                  -- compute_deterministic_metrics, EvaluatorMode
  ui/
    __init__.py
    demo_page.py                  -- 5 tabs; Jazz live via Anthropic; Trace fixture-driven
    dashboard.py

tests/fixtures/golden_cases/ci_spread/
  yeti_abl.json
  techflow_term.json

config/packs/ci-spread-core/
  mode_tuning/
    investigator.md
    reasoner.md
    governor.md
    narrator.md

prompts/ci_spread/.gitkeep
```

---

## Integration smoke tests (reference -- all pass as of 0.7.4)

```bash
cd /Users/sangit/src/jaci && source .venv/bin/activate

# structured_data intake path
python -c "
import asyncio, json
from pathlib import Path
from jaci.scenarios.ci_spread.conductor import CIConductor
from jaci.scenarios.ci_spread.schemas import LoanApplication, LoanType, LoanPurpose
from unittest.mock import MagicMock

fd = json.loads(Path('docs/LoanSamples/YETI/yeti_financials.json').read_text())
app = LoanApplication(
    company='YETI Holdings, Inc.',
    loan_type=LoanType.ABL,
    loan_purpose=LoanPurpose.WORKING_CAPITAL,
    requested_amount=20_000_000,
    intercreditor_required=True,
)
conductor = CIConductor(ctx=MagicMock())
case = asyncio.run(conductor.run_analysis(app, structured_data=fd))
assert case.intake_mode == 'structured_data'
assert len(case.context.evidence) >= 1
print('Phase 0 structured_data ok -- evidence count:', len(case.context.evidence))
"

# tools path (no documents)
python -c "
import asyncio
from jaci.scenarios.ci_spread.conductor import CIConductor
from jaci.scenarios.ci_spread.schemas import LoanApplication, LoanType, LoanPurpose
from unittest.mock import MagicMock

app = LoanApplication(
    company='TechFlow Manufacturing LLC',
    loan_type=LoanType.TERM_LOAN,
    loan_purpose=LoanPurpose.EXPANSION,
    requested_amount=15_000_000,
)
conductor = CIConductor(ctx=MagicMock())
case = asyncio.run(conductor.run_analysis(app))
assert case.intake_mode == 'tools'
print('Tools path ok -- iterations:', case.iterations)
"

# evaluator against YETI golden case
python -c "
import json
from pathlib import Path
from jaci.scenarios.ci_spread.modes.evaluator import compute_deterministic_metrics
from jaci.scenarios.ci_spread.schemas import (
    CaseFile, CIContext, LoanApplication, LoanType, LoanPurpose,
    CreditRecommendation, LoanDecision, CICondition,
    SpreadHypothesis, SpreadHypothesisContent, SpreadIssueType,
)
app = LoanApplication(
    company='YETI Holdings, Inc.',
    loan_type=LoanType.ABL,
    loan_purpose=LoanPurpose.WORKING_CAPITAL,
    requested_amount=20_000_000,
)
ctx = CIContext(input=app)
ctx.hypotheses = [
    SpreadHypothesis(
        content=SpreadHypothesisContent(
            issue_type=SpreadIssueType.LIEN_CONFLICT,
            category='structural',
            description='Existing blanket lien',
            impact_on_credit='Requires intercreditor',
            severity='critical',
        ),
        confidence=0.95,
        status='confirmed',
    )
]
rec = CreditRecommendation(
    decision=LoanDecision.APPROVED_WITH_CONDITIONS,
    conditions=[
        CICondition(condition_type='pre_closing', category='lien', description='Lien resolution'),
        CICondition(condition_type='ongoing_covenant', category='bbc', description='Monthly BBC'),
        CICondition(condition_type='ongoing_covenant', category='audit', description='Annual field exam'),
    ],
)
case = CaseFile(loan_id=app.loan_id, context=ctx, recommendation=rec)
gt = json.loads(Path('tests/fixtures/golden_cases/ci_spread/yeti_abl.json').read_text())
metrics = compute_deterministic_metrics(case, gt['expected_decision'])
assert metrics['decision_accuracy'] == 1.0
assert metrics['lien_flag_accuracy'] == 1.0
assert metrics['condition_coverage'] >= 1.0
print('Evaluator ok:', metrics)
"

# full import health
python -c "
from jaci.scenarios.ci_spread import CIConductor, LoanApplication, CaseFile
from jaci.scenarios.ci_spread.ui.demo_page import render_demo_page
print('All imports clean')
"
```
