# JACI-KYC — Ingest & Govern Anthropic's Financial Agents

**Claude Code Execution Plan | PoC**

JazzX Platform | May 2026 | Draft v2.0

---

## 1. Purpose — What the Execs Want to Show

A customer says: "We saw Anthropic's KYC screener. Why do we need JazzX?"

The demo answers: "You don't choose between us. We took that exact agent — same prompt, same rules, same Claude model — and ran it inside JazzX. Here's what it produces on its own. Here's what it produces with governance. Same brain, different accountability."

This PoC builds a KYC use case in the JACI repo (separate `kyc` branch) that:

1. **Ingests** the system prompt and skill content from Anthropic's `financial-services` repo (already cloned at `anthropic-fs-ref/`)
2. **Runs locally** via the Anthropic Client SDK (`pip install anthropic`) — no external Managed Agents dependency
3. **Wraps with JazzX governance** — Governor policy gates, Verifier evidence attestation, canonical object chain, CanonicalTrace, EVOLVE loop
4. **Produces a side-by-side demo** — raw Anthropic output vs. JazzX-governed output from the same cognitive work

This validates v2.0 Workstream 06 (Composable Runtime) exit criterion: "OpenAI / Claude / Google / custom agents run through a common lifecycle and trace model."

---

## 2. What Anthropic Actually Shipped (and What It Isn't)

The `anthropics/financial-services` repo (Apache-2.0, 20k+ stars, May 5 2026) contains 10 named agent templates. Each agent is:

```
plugins/agent-plugins/<slug>/
├── .claude-plugin/plugin.json    # manifest
├── agents/<slug>.md              # canonical system prompt
└── skills/                       # markdown knowledge files
    └── kyc-rules/SKILL.md        # domain rules (for KYC)

managed-agent-cookbooks/<slug>/
├── agent.yaml                    # Managed Agent deploy manifest
├── subagents/*.yaml              # leaf workers
└── steering-examples.json        # sample trigger events
```

**What this IS:** Curated prompt packs with a delivery mechanism. The KYC screener is a system prompt (`agents/kyc-screener.md`) plus a `kyc-rules` skill (markdown file encoding CDD/KYC rules and a risk-rating output schema). Skills are "onboarding guides" that Claude reads on demand.

**What this ISN'T:** There is no investigation loop, no evidence attestation, no policy-as-code enforcement, no canonical objects, no audit trace, no compounding loop. No Python runtime code. The "agent" is Claude + a prompt + skill files. The Managed Agents API handles execution infrastructure (sandboxing, state, tool execution) but adds no domain governance.

**The gap is precisely what JazzX fills.** The Anthropic repo is the cognitive starting point; JazzX is the institutional intelligence layer.

---

## 3. Integration Architecture — "Ingest & Govern"

### 3.1 What We Ingest

From `anthropic-fs-ref/plugins/agent-plugins/kyc-screener/`:

| Source file | What it contains | Where it goes in JACI |
|-------------|------------------|-----------------------|
| `agents/kyc-screener.md` | System prompt: workflow steps, output format, persona | Decomposed across `prompts/kyc/investigator.md`, `reasoner.md`, `narrator.md` |
| `skills/kyc-rules/SKILL.md` | CDD/KYC rules, risk-rating rubric, evidence checklist | Split into `prompts/kyc/governor.md` (policy rules) + `config/packs/kyc_cdd_lifecycle.yaml` (governance) + `src/jaci/pack/kyc_policy_registry.py` (Policy objects) |
| `steering-examples.json` | Sample trigger events (entity onboarding/review scenarios) | Adapted into `tests/eval/gold_cases/kyc/` gold case JSON files |

The ingestion is **decomposition, not copy-paste**. Anthropic's single flat prompt gets split into JACI's multi-mode, multi-layer structure. Their rules become our Policy objects. Their output schema becomes our canonical Decision with cross-linkage. Their examples become our eval gold cases.

### 3.2 What We Add (The Governance Layer)

| JazzX capability | What it does | Anthropic equivalent |
|------------------|--------------|---------------------|
| **Governor gate** | Enforces institutional CDD policies, EDD triggers, approval authority, autonomy ceilings at runtime | None — rules are in the prompt but not enforced programmatically |
| **Verifier attestation** | Each evidence object gets provenance, freshness, completeness checks with explicit attestation status | None — agent reads documents but doesn't attest them |
| **Canonical chain** | Policy → Evidence → Decision → Trace → Outcome as first-class linked objects | Flat JSON risk-rating output |
| **CanonicalTrace** | Full execution lineage: which mode ran, what it consumed, what it produced, who approved | Managed Agents has session logs, but not governed trace objects |
| **EVOLVE loop** | Evaluator assesses quality, Curator routes improvement signals back to pack assets | None — stateless between runs |
| **Certified Client Overlay** | Per-institution policy variants (different EDD thresholds, risk appetite, jurisdiction rules) | "Fork the prompt and edit it" |
| **Autonomy ceilings** | L1 Recommend for risk-tier, L2 Execute with Approval for low-risk, human-only for high-risk sign-off | "Every output staged for human sign-off" (blanket, not tiered) |

### 3.3 How It Runs

```
                    ┌─────────────────────────────────┐
                    │   Anthropic Client SDK           │
                    │   pip install anthropic           │
                    │   claude-sonnet-4-5 model calls   │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │   JACI Conductor (plain Python)   │
                    │   Same loop as JACI-AML           │
                    │   Different trigger, schemas,     │
                    │   convergence criteria            │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        Investigator     Verifier          Reasoner
        (Anthropic SDK)  (Anthropic SDK)   (Anthropic SDK)
              │                │                │
              ▼                ▼                ▼
        Governor         Narrator          Evaluator
        (Anthropic SDK)  (Anthropic SDK)   (Anthropic SDK)
              │
              ▼
        CanonicalTrace → BPMN/Flowable → Human checkpoint
```

All mode calls go through `src/jaci/sdk/anthropic_adapter.py` — a thin wrapper around `client.messages.create()` that handles the tool-use loop and structured output mapping. The Conductor doesn't know which SDK is underneath; it calls the same mode interface as JACI-AML.

---

## 4. Execution Plan — Phases

### Phase 0 — Branch Setup + Anthropic SDK Adapter (1 day)

**Tasks:**
- `git checkout -b kyc` from `main` in jaci repo
- Add `anthropic` to `pyproject.toml` dependencies
- Create `src/jaci/sdk/anthropic_adapter.py`:
  - `AnthropicModeRunner` class implementing the same interface as the OpenAI Agents SDK mode calls
  - Accepts: system prompt, messages, tool definitions, Pydantic output schema
  - Handles: tool-use loop (`while stop_reason == "tool_use"`), structured output via `output_format`
  - Returns: parsed Pydantic model matching mode contract
- Create `.env.template` additions: `ANTHROPIC_API_KEY`
- Verify existing AML tests still pass (shared code untouched)

**Acceptance criteria:**
- `AnthropicModeRunner` makes a successful structured-output call to Claude
- AML eval harness still runs on `kyc` branch

### Phase 1 — Content Ingestion from Anthropic Repo (1.5 days)

**Tasks:**
- Read and decompose `anthropic-fs-ref/plugins/agent-plugins/kyc-screener/`:
  - `agents/kyc-screener.md` → extract workflow steps, output format, persona directives
  - `skills/kyc-rules/SKILL.md` → extract CDD rules, risk-rating rubric, evidence requirements
  - `managed-agent-cookbooks/kyc-screener/steering-examples.json` → extract trigger scenarios
- Create JACI-KYC prompts by splitting Anthropic's single prompt into governed modes:
  - `prompts/kyc/investigator.md` — evidence gathering strategy, adapted from their workflow steps
  - `prompts/kyc/verifier.md` — identity/BO verification, freshness checks (NEW — not in Anthropic's version)
  - `prompts/kyc/reasoner.md` — risk-tier rubric, adapted from their `kyc-rules` skill
  - `prompts/kyc/governor.md` — CDD policy enforcement rules, adapted from their `kyc-rules` skill
  - `prompts/kyc/narrator.md` — review narrative structure (NEW — not in Anthropic's version)
  - `prompts/kyc/evaluator.md` — KYC quality rubric (NEW — not in Anthropic's version)
- Create `src/jaci/pack/kyc_policy_registry.py` — Policy objects for CDD, PEP, BO, EDD rules
- Create `config/packs/kyc_cdd_lifecycle.yaml` — pack governance reference
- Document provenance: which content came from Anthropic (Apache-2.0) vs. new JazzX additions

**Design note:** The decomposition creates three entirely new capabilities that don't exist in Anthropic's version: Verifier (evidence attestation), Narrator (structured review narrative), and Evaluator (quality assessment + compounding). These are the governance differentiators.

**Acceptance criteria:**
- All prompts load correctly via prompt composability (`base + kyc_tuning`)
- Policy objects validate via Pydantic
- Provenance document tracks every adaptation

### Phase 2 — KYC Schemas + Evidence Tools (1 day)

**Tasks:**
- Create `src/jaci/schemas/kyc_context.py`:
  - `ReviewTrigger` (analogous to `AlertTrigger`)
  - `RiskTier` enum (Low / Medium / High / Prohibited)
  - `RiskTierRecommendation` (analogous to `DispositionRecommendation`, with canonical cross-linkage)
  - `ReviewFile` (analogous to `CaseFile`)
- Create KYC evidence tools in `src/jaci/tools/kyc_tools.py` (8 tools: identity verification, BO records, sanctions screening, adverse media, transaction summary, source of wealth, prior reviews, corporate registry)
- Create `tests/fixtures/kyc_case_fixtures.py` with synthetic data for 6–8 gold cases
- Create gold case JSON files in `tests/eval/gold_cases/kyc/`

**Gold cases (adapted from Anthropic's steering examples + new JazzX additions):**

| # | Label | Risk Tier | EDD | Source |
|---|-------|-----------|-----|--------|
| kyc_01 | Low-risk individual, clean review | Low | No | Anthropic steering example, adapted |
| kyc_02 | Corporate with BO complexity | Medium | No | New |
| kyc_03 | PEP-linked entity, mandatory EDD | High | Yes | Anthropic steering example, adapted |
| kyc_04 | BO discrepancy (declared vs registry) | High | Yes | New |
| kyc_05 | Adverse media hit (Amber RAG) | High | Yes | New |
| kyc_06 | Downgrade review (High → Medium) | Medium | No | New |
| kyc_07 | Edge: SLA deadline approaching | varies | varies | New (mirrors AML case_09 pattern) |
| kyc_08 | Edge: prohibited jurisdiction | Prohibited | Yes | New |

**Acceptance criteria:**
- All schemas validate
- All tools return case-specific fixtures
- Gold cases cover the risk-tier and EDD decision space

### Phase 3 — KYC Conductor + Mode Wiring (2 days)

**Tasks:**
- Create `src/jaci/conductor_kyc.py` — KYC-specific Conductor:
  - Same loop structure as `conductor.py`
  - Different trigger: `ReviewTrigger` instead of `AlertTrigger`
  - Different convergence: evidence checklist per risk tier, not typology confirmation
  - Different output: `ReviewFile` instead of `CaseFile`
  - Different autonomy: L2 (Execute with Approval) for low-risk reviews
  - Uses `AnthropicModeRunner` for all mode calls
- Wire all 6 modes through `AnthropicModeRunner`
- Integrate EVOLVE layer (reuse existing Evaluator + Curator, KYC-tuned prompts)
- Emit `CanonicalTrace` with full cross-linkage

**Key design decision:** The Conductor is parameterized, not subclassed. A config object specifies trigger type, convergence criteria, output type, mode runner class, and autonomy ceilings. This makes future domain extensions (JACI-Clin etc.) a config change, not a code fork.

**Acceptance criteria:**
- Full review loop runs on kyc_01 (low-risk individual)
- Output is a valid `ReviewFile` with `CanonicalTrace`
- EVOLVE layer generates improvement signals

### Phase 4 — Side-by-Side Demo (1.5 days)

**Tasks:**
- Create `scripts/demo_raw_vs_governed.py`:
  - **Raw mode:** Calls Claude directly with Anthropic's original system prompt + `kyc-rules` skill (loaded verbatim from `anthropic-fs-ref/`). Produces their flat risk-rating JSON.
  - **Governed mode:** Runs the same review through JACI-KYC's Conductor loop with full governance. Produces `ReviewFile` with canonical chain.
  - **Comparison output:** Side-by-side markdown showing what each produces for the same input
- Create Streamlit dashboard tab for KYC (extend existing `app.py`):
  - Visual comparison: raw JSON vs. governed canonical chain
  - Trace viewer: full investigation lineage
  - Policy citations: which CDD rules were checked
  - Evidence attestation: which documents were verified, with what status
- Run full eval across all gold cases, track in MLflow

**Demo narrative for execs:**

"Same model (Claude Sonnet 4.5). Same KYC rules. Same customer file. On the left: what Anthropic's agent produces — a risk rating with a few bullet points. The analyst gets a recommendation, but their examiner gets nothing.

On the right: what JazzX produces — a governed review package. Every piece of evidence is attested with provenance. Every policy rule that was checked is cited. The risk tier decision links to the evidence that supports it. The full execution trace is replayable. And when the compliance officer overrides the recommendation, that override flows back through the EVOLVE loop to make the next review better.

The cognitive work is the same. The institutional value is not even close."

**Acceptance criteria:**
- Side-by-side script runs cleanly on 3+ cases
- Streamlit dashboard shows the comparison visually
- MLflow tracks KYC eval metrics

### Phase 5 — Eval Harness + Documentation (1 day)

**Tasks:**
- Create `tests/eval/run_kyc_eval.py` (mirrors `run_eval.py`)
- KYC-specific metrics: risk-tier accuracy, EDD decision accuracy, evidence completeness, policy citation completeness
- Update `CLAUDE.md` with KYC branch documentation
- Create `docs/ANTHROPIC_INTEGRATION_GUIDE.md` documenting:
  - What was ingested from `anthropics/financial-services`
  - How content was decomposed into JACI modes
  - Apache-2.0 license compliance
  - How to repeat this pattern for other Anthropic agents (GL Reconciler, Statement Auditor, etc.)

**Acceptance criteria:**
- Full eval runs, metrics tracked
- Documentation sufficient for another developer to repeat the integration for a different agent

---

## 5. Estimated Effort

| Phase | Effort | What it proves |
|-------|--------|----------------|
| Phase 0: Branch + SDK adapter | 1 day | Anthropic SDK works under JACI's Conductor |
| Phase 1: Content ingestion | 1.5 days | Anthropic's prompt pack decomposes into governed modes |
| Phase 2: Schemas + tools | 1 day | KYC domain extends the JACI pattern |
| Phase 3: Conductor + wiring | 2 days | Full governed review loop runs on Claude |
| Phase 4: Side-by-side demo | 1.5 days | The value gap is visible |
| Phase 5: Eval + docs | 1 day | Repeatable for other agents |
| **Total** | **~8 days** | |

---

## 6. What This Proves to Three Audiences

### To Customers
"You like Anthropic's KYC screener? Great. Run it inside JazzX. You get the same cognitive quality plus governance, audit trail, and compounding. Your examiner will thank you."

### To Execs
Three v2.0 claims validated in one PoC:
1. **Agent Framework Adapter** works — same Conductor, different SDK, different model, same governance.
2. **Domain Pack extensibility** works — AML to KYC with shared infrastructure, not a fork.
3. **Third-party agent co-opt** works — Anthropic's reference architecture becomes JazzX-governed without fighting it.

### To Engineering
The integration guide (`docs/ANTHROPIC_INTEGRATION_GUIDE.md`) is a repeatable playbook. When a customer says "we also want the GL Reconciler," the pattern is: clone the agent plugin, decompose prompt into modes, create domain schemas, wire through Conductor, run eval. The same 8-day template applies.

---

## 7. Repeatable Pattern for Other Agents

The `financial-services` repo has 10 agents. The KYC screener is the proof of concept. The same ingest-and-govern pattern applies to any of them:

| Anthropic Agent | JazzX Relevance | Priority |
|-----------------|-----------------|----------|
| **KYC screener** | Direct AML/KYC adjacency, this PoC | **Now** |
| Statement auditor | Compliance/audit workflow, close to MACER pattern | High |
| GL reconciler | Financial operations, fund admin use case | Medium |
| Valuation reviewer | Commercial lending adjacency | Medium |
| Model builder | Financial modeling, could enhance MACER | Lower |
| Pitch agent | IB workflow, not core JazzX vertical | Low |
| Others (5) | Market research, meetings, earnings — not regulated judgment | Low |

The statement auditor and GL reconciler are the most natural next candidates after KYC — both involve regulated judgment where governance adds the most value.

---

## 8. Open Questions

1. **Prompt split for AML too?** Phase 1 creates `prompts/kyc/` with the composable structure (`base + domain`). Should this also trigger the overdue split for AML prompts (`prompts/aml/`)? Doing both now keeps the architecture consistent; deferring saves 0.5 days.

2. **Conductor parameterization scope.** Phase 3 proposes a config-driven Conductor instead of subclassing. How far does parameterization go — just trigger/output types, or also convergence logic and autonomy ceiling selection?

3. **License tracking.** Anthropic's repo is Apache-2.0. Do we need a formal attribution file, or is the provenance doc in `docs/ANTHROPIC_INTEGRATION_GUIDE.md` sufficient?

4. **Cost ceiling.** JACI-AML best eval is $0.65/case on flex_gpt-5.4. Claude Sonnet 4.5 pricing may differ. Is there a per-review cost target?

5. **Which Anthropic agents to demo beyond KYC?** If execs want breadth (show we can ingest any of the 10), a lightweight "hello world" integration for one more agent (e.g., statement auditor) would add ~2 days.

---

*End of Document*
