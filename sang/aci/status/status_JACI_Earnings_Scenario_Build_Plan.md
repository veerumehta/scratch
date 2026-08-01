# JACI Earnings Review — Scenario Build Plan

**Claude Code Execution Plan**

Branch: `dev` | Scenario: `src/jaci/scenarios/earnings_anthropic/`

---

## 1. What This Is

A fourth scenario in the JACI repo that ingests Anthropic's Earnings Reviewer agent and wraps it with JazzX governance. Follows the exact same pattern as `kyc_anthropic` — decompose Anthropic's prompt + skills into JACI modes, add governance modes they don't have, run through the Conductor loop, produce canonical objects.

The demo: feed a recent public earnings release (10-Q + earnings call transcript) through both the raw Anthropic prompt and the JACI-governed flow. Compare outputs.

**Why this matters beyond KYC:** Two compliance scenarios (AML, KYC) prove governance depth. Adding an investment research scenario proves domain breadth — same 5 Experts, same canonical chain, completely different domain. A customer watching this demo sees three domains running through one framework.

---

## 2. What Anthropic Ships

The Earnings Reviewer agent has:

- **System prompt:** `agents/earnings-reviewer.md` — workflow for processing earnings
- **4 skills:**
  - `earnings-analysis` — how to extract guidance revisions, management commentary, and key metrics from a transcript
  - `model-update` — how to map earnings data into model assumptions
  - `3-statement-model` — how to build/update income statement, balance sheet, cash flow
  - Document research via MCP (Aiera for transcripts, FactSet/Capital IQ for filings)
- **Subagents:**
  - `transcript-reader` — leaf worker with Read+Grep only, reads the earnings transcript in isolated context
  - `modeler` — builds/updates the financial model
- **Steering event:** "Process earnings: <ticker> <period>"
- **Outputs:** Research note draft + updated financial projections

### What Anthropic Doesn't Have

| Missing capability | Why it matters for earnings |
|---|---|
| Evidence attestation | Did the revenue number actually come from the 10-Q, or did the model hallucinate it? |
| Policy enforcement | Investment research independence rules, compliance restrictions on covered companies |
| Canonical trace | Which line items changed, why, and what source document justified the change |
| Compounding | Did last quarter's model update guidance improve this quarter's forecast accuracy? |
| Audit package | If the research note is challenged, can you replay the reasoning? |

---

## 3. Scenario Structure

Following the established pattern from `aml/`, `kyc/`, and `kyc_anthropic/`:

```
src/jaci/scenarios/earnings_anthropic/
├── __init__.py
├── README.md
│
├── modes/
│   ├── __init__.py
│   ├── investigator.py       ← From Anthropic's earnings-analysis skill
│   ├── reasoner.py           ← From Anthropic's model-update + 3-statement-model skills
│   ├── verifier.py           ← NEW: attestation that numbers match source documents
│   ├── governor.py           ← NEW: research independence, compliance policy enforcement
│   ├── narrator.py           ← From Anthropic's note-writing workflow + NEW: citation structure
│   └── evaluator.py          ← NEW: forecast accuracy tracking, note quality assessment
│
├── schemas/
│   ├── __init__.py
│   └── earnings_schemas.py
│
├── tools/
│   ├── __init__.py
│   └── earnings_mock_connectors.py
│
├── conductor.py              ← Earnings review loop orchestrator
│
└── pack/
    └── earnings_policy_registry.py

prompts/earnings-anthropic/
├── investigator.md
├── reasoner.md
├── verifier.md
├── governor.md
├── narrator.md
└── evaluator.md

config/packs/
└── earnings_review.yaml

tests/eval/gold_cases/earnings/
├── case_01.json              ← Beat & raise (straightforward)
├── case_02.json              ← Miss with lowered guidance
├── case_03.json              ← Mixed (beat revenue, miss EPS, maintained guidance)
├── case_04.json              ← Restatement / revision to prior period
├── case_05.json              ← Segment reorganization mid-year
├── case_06.json              ← Management commentary contradicts numbers
└── case_07.json              ← Edge: first earnings post-M&A (pro forma vs GAAP)
```

---

## 4. Schemas

### 4.1 Trigger

```python
class EarningsTrigger(BaseModel):
    """Analogous to AlertTrigger (AML) and ReviewTrigger (KYC)."""
    ticker: str
    company_name: str
    period: str              # "Q1 2026", "FY 2025"
    filing_type: str         # "10-Q", "10-K", "8-K"
    filing_date: date
    transcript_available: bool
    prior_period: str | None = None
    prior_model_version: str | None = None
    sector: str | None = None
    market_cap_tier: str | None = None  # mega, large, mid, small
```

### 4.2 Core Decision Object

```python
class EarningsAssessment(BaseModel):
    """Analogous to DispositionRecommendation (AML) / RiskTierRecommendation (KYC)."""
    assessment_type: EarningsOutcome  # beat, miss, mixed, restatement
    confidence: float

    # Key metrics with attestation
    revenue_actual: float | None = None
    revenue_consensus: float | None = None
    eps_actual: float | None = None
    eps_consensus: float | None = None

    guidance_change: GuidanceDirection  # raised, maintained, lowered, withdrawn, initiated
    key_guidance_items: list[GuidanceItem]

    model_updates: list[ModelUpdate]  # what changed in the financial model and why
    thesis_impact: ThesisImpact       # reinforced, challenged, neutral, requires_revision

    # Canonical cross-linkage
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    policy_refs: list[str] = []
    evidence_refs: list[str] = []
    trace_id: str | None = None
    pack_id: str = "earnings_review"
```

### 4.3 Evidence Types

| Evidence Type | Tool | Description |
|---|---|---|
| `filing_data` | `get_filing_data` | Structured financials from 10-Q/10-K (revenue, EPS, margins, segments) |
| `transcript_excerpt` | `get_transcript_excerpts` | Relevant passages from earnings call (guidance, management commentary) |
| `consensus_estimates` | `get_consensus_estimates` | Street consensus for the reported period and forward periods |
| `prior_model` | `get_prior_model` | Previous quarter's model assumptions for delta comparison |
| `peer_context` | `get_peer_context` | How peers reported on same metrics this cycle |
| `price_reaction` | `get_price_reaction` | Post-earnings price/volume data (for evaluation, not for the note) |

### 4.4 Output

```python
class EarningsReviewFile(BaseModel):
    """Analogous to CaseFile (AML) / ReviewFile (KYC)."""
    review_id: str
    trigger: EarningsTrigger
    evidence: list[EvidenceObject]
    assessment: EarningsAssessment
    governor_decision: GovernorDecision
    research_note: str | None = None       # Narrator output
    model_update_summary: str | None = None
    canonical_trace: CanonicalTrace | None = None
    created_at: datetime
    status: str  # draft, pending_review, published
```

---

## 5. Policies — Earnings Domain

Different from AML/KYC — these are investment research policies, not regulatory compliance:

### `RESEARCH_INDEPENDENCE_POLICY`
- `RI-001`: Research note must not contain forward-looking price targets without basis in model
- `RI-002`: Material non-public information (MNPI) cannot be incorporated; only public filings and transcripts
- `RI-003`: Covered company restriction list checked before note generation

### `MODEL_INTEGRITY_POLICY`
- `MI-001`: Every model assumption change must cite a source document (filing line item, transcript passage)
- `MI-002`: Revenue and EPS figures must be attested against the actual filing (not hallucinated)
- `MI-003`: Guidance items must quote or closely paraphrase management's actual language
- `MI-004`: Pro forma vs GAAP adjustments must be explicitly flagged

### `NOTE_QUALITY_POLICY`
- `NQ-001`: Research note must contain: summary, key metrics table, guidance changes, model updates, thesis impact
- `NQ-002`: Every factual claim in the note must cite a specific evidence object
- `NQ-003`: Tone must be analytical, not promotional (no superlatives, no buy/sell language)

### `REVIEW_WORKFLOW_POLICY`
- `RW-001`: Draft note staged for senior analyst review (human-in-the-loop)
- `RW-002`: Model updates require second-check before publishing
- `RW-003`: SLA: note draft within 4 hours of transcript availability

---

## 6. Mode Decomposition from Anthropic Content

| Mode | Source from Anthropic | JazzX additions |
|---|---|---|
| **Investigator** | `earnings-analysis` skill → extract key metrics, guidance revisions, management commentary themes | Add hypothesis structure: "revenue beat driven by segment X" with evidence requirements |
| **Reasoner** | `model-update` + `3-statement-model` skills → map earnings data into model assumptions, update projections | Add thesis impact assessment, confidence calibration, guidance_refs for compounding |
| **Verifier** | None — NEW | Attest every number against source document: "revenue $X.XXB" matches filing page N, line M |
| **Governor** | None — NEW | Research independence checks, MNPI gate, covered company restriction, model integrity rules |
| **Narrator** | Part of Anthropic's note-writing workflow | Add citation structure (every claim → evidence_ref), section completeness checks |
| **Evaluator** | None — NEW | Forecast accuracy tracking (did last quarter's model updates improve this quarter's estimate?), note quality rubric |

---

## 7. Gold Cases

Using real public filings makes this demo dramatically more compelling than synthetic data. Suggested approach:

| # | Company | Period | Scenario | Why interesting |
|---|---------|--------|----------|----------------|
| 01 | Nvidia | Recent Q | Beat & raise | Clean case, massive guidance revision, tests model update |
| 02 | Intel or similar | Recent Q | Miss with lowered guidance | Tests handling of negative revision, thesis challenge |
| 03 | A large cap with mixed results | Recent Q | Mixed signals | Beat revenue, miss EPS — tests nuanced assessment |
| 04 | Company with restatement | Recent | Restatement | Tests prior period revision handling, Governor GAAP/pro forma gate |
| 05 | Recent post-M&A reporter | Recent | Segment reorg | Tests handling of non-comparable periods |
| 06 | Company where call contradicts filing | Recent | Narrative contradiction | Tests Verifier contradiction detection |
| 07 | Company with withdrawn guidance | Recent | Guidance withdrawal | Edge case for guidance direction assessment |

**Fixture approach:** For the PoC, mock connectors return structured data extracted from real filings. The gold case JSON includes the actual key metrics from the filing so the eval can check attestation accuracy. Future: wire to real filing APIs (SEC EDGAR, FactSet MCP).

---

## 8. Execution Plan

### Phase 1 — Scaffolding + Content Ingestion (1.5 days)

- Create `src/jaci/scenarios/earnings_anthropic/` directory structure
- Read and decompose Anthropic's earnings reviewer files:
  - `agents/earnings-reviewer.md` → investigator + narrator prompts
  - `skills/earnings-analysis/SKILL.md` → investigator prompt
  - `skills/model-update/SKILL.md` → reasoner prompt
  - `skills/3-statement-model/SKILL.md` → reasoner prompt
- Create 6 mode prompts in `prompts/earnings-anthropic/`
- Create `earnings_schemas.py` with all schema types
- Create `earnings_policy_registry.py` with 4 policy families
- Create `earnings_review.yaml` pack governance
- Document provenance

### Phase 2 — Modes + Conductor (2 days)

- Implement 6 mode classes (same pattern as `kyc_anthropic/modes/`)
- Implement `EarningsConductor` in `conductor.py`
- Create 6 evidence tools in `earnings_mock_connectors.py`
- Create 3–4 gold cases with real filing data
- Wire end-to-end: trigger → conductor loop → EarningsReviewFile

### Phase 3 — Eval + Demo (1.5 days)

- Create `tests/eval/run_earnings_eval.py`
- Metrics: number attestation accuracy, guidance extraction accuracy, citation completeness, note quality
- Add to Streamlit dashboard as fourth scenario tab
- Create side-by-side demo: raw Anthropic prompt vs. JACI governed

---

## 9. Estimated Effort

| Phase | Effort |
|---|---|
| Phase 1: Scaffolding + ingestion | 1.5 days |
| Phase 2: Modes + Conductor | 2 days |
| Phase 3: Eval + demo | 1.5 days |
| **Total** | **~5 days** |

Faster than KYC (~8 days) because the shared infrastructure (SDK adapter, base modes, Conductor pattern, eval harness, Streamlit dashboard) already exists. This is pure domain content + wiring.

---

## 10. What This Adds to the Demo Portfolio

After this, the JACI repo has 4 scenarios on `dev`:

| Scenario | Domain | Content Source | Proves |
|---|---|---|---|
| `aml` | AML investigation | JazzX-native (OpenAI SDK) | Original JACI pattern works |
| `kyc` | KYC/CDD review | JazzX-native (Anthropic SDK) | SDK portability, domain extension |
| `kyc_anthropic` | KYC/CDD review | Anthropic KYC screener (ingested) | Third-party agent co-opt |
| `earnings_anthropic` | Investment research | Anthropic Earnings Reviewer (ingested) | **Cross-vertical generality** |

The earnings scenario is the one that breaks out of compliance/regulatory into investment research — a completely different domain with different policies, different evidence types, different decision schemas, and a different audience (analysts vs. compliance officers). Same 5 Experts, same canonical chain, same governance machinery.

For an exec watching the demo: "We showed you AML. We showed you KYC. Now here's earnings analysis — different domain, different policies, same platform. And we ingested two of Anthropic's 10 agents in under two weeks."

---

*End of Document*
