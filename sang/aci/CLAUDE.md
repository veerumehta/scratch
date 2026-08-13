# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Recent Session Status (2026-08-11)

jaci `dev` is at `a6b068b` (local, unpushed) plus a large uncommitted working tree (see
`git status` — everything below is real but not yet committed; commit only when asked). Version
is unchanged at `0.19.2` this round — do not bump without explicit user sign-off (default to a
patch bump if/when one is requested). Full suite: 809 passed, 8 skipped, 4 xfailed, 1 xpassed,
**1 known pre-existing failure**
(`test_decision_canonical.py::TestDecisionType::test_decision_type_all_values` — asserts
`len(DecisionType) == 3`, actual is 4; last touched June 6, untouched this session, unrelated to
anything below — a stale test, not a regression).

**This round: document upload → Knowledge-Hub-backed "document packet" pipeline, built up in
stages across one long session.** In order:

1. **Upload widget** (`src/jaci/scenarios/shared/document_upload.py`, new `shared/` package):
   `render_document_upload()` — a zip stands in for a folder upload (browsers can't upload
   directories), unpacked via `jazzx_sdk`'s own `unpack_zip`. Wired into `ci_spread` (evidence-
   seeding for `CIToolRegistry`, new `_seed_uploaded_financials`), `cre_underwriting`,
   `portfolio_monitoring`, `insurance_diligence`. Fixed a real bug found along the way:
   `ci_spread`'s `_run_fabric` never set `FabricConfig.local_cache_dir`, so LOCAL-mode
   `fabric.docs` silently missed the per-loan `artifact_dir` entirely.
2. **`.japes` local-markdown-cache convention generalized.** `commercial_lending/docintel.py`'s
   `.japes/`-or-co-located-`.md` staging fallback (used only by `ci_spread` before) is now also
   wired into `cre_underwriting`, `portfolio_monitoring`, `insurance_diligence` (swapped their
   raw `jazzx_sdk` `convert_document` import for the `.japes`-aware wrapper) — behavior-preserving
   for their current (tiny) sample docs, but means large real docs there would get the same
   truncate-and-cache treatment `scripts/shrink_source_pdfs.py` gives the YETI/MAA 10-Ks.
3. **YETI/MAA 10-K PDFs shrunk and committed.** `scripts/shrink_source_pdfs.py`: swap a 50-70MB
   source PDF for a small labeled stub + its real `.japes/<stem>.md`; `docintel.convert_document`
   resolves the real content regardless of the stub's actual bytes (existence-only check, no
   hash). Originals preserved under a sibling `_originals/` (gitignored). Committed the stubs +
   `.japes/` caches to git via `git add -f` (`docs/LoanSamples` is fully gitignored, but explicit
   force-adds still work) — MAA's staging was co-located `.md` (no `.japes/` subfolder), migrated
   to the `.japes/` convention in the process.
4. **Knowledge-Hub push/pull tier added to `docintel.py`.** `ensure_local_cache`/
   `ensure_local_caches` (async — deliberately *not* a `fabric=` param on the sync
   `convert_document`, since bridging an async fabric fetch inside an already-sync function risks
   "asyncio.run() cannot be called from a running event loop" for callers that are themselves
   async): if no local cache, try a pushed **derived** doc first (cheap), then fall back to
   pulling the **original** and converting it locally (the one place real conversion cost can
   land on a pull). `check_staleness()` — cheap metadata-only hash comparison, flags when a doc
   was updated remotely since last pull (never auto-resolves). `shared/fabric.py`'s
   `build_fabric()` (connected-KH-vs-local-Mock switch, factored out of three separate copies)
   and `cached_build_fabric()` — **a real bug found and fixed**: `MockKnowledgeHubClient` doesn't
   persist across process invocations at all (no save-back to `data_dir`, confirmed by reading
   the source — filed as japes issue, see below), and since Streamlit reruns the whole script on
   every interaction, an uncached `build_fabric()` would forget a just-pushed packet before a user
   could ever see it in a dropdown. Fixed with `st.session_state` caching, verified against
   `AppTest`'s real session machinery, not a hand-rolled substitute.
5. **Named "document packet" system**
   (`src/jaci/capabilities/commercial_lending/document_packet.py`,
   `src/jaci/scenarios/shared/packet_picker.py`). Deliberately called **"packet", not "pack"** —
   `config/packs/` already means governed domain packs in this repo (`pack_id`,
   `pack_manifest.yaml`, certification status); a document packet is unrelated, kept distinct to
   avoid colliding with that concept anywhere it's grepped for. `push_folder_as_packet()` pushes
   *both* tiers (original + derived) per file, dedups via `fabric.docs.ensure()`'s content-hash
   idempotency (not reimplemented), and auto-flags `local_path` when the source folder is already
   inside the repo (vendored, zero-fabric-dependency pick — same story as the YETI/MAA stubs).
   `config/demo_document_packets.json` (repo root, explicitly *not* under `config/packs/`) is the
   committed offline registry `list_all_packets()` always reads first, merged with live KH
   results on top. Three CLI scripts: `scripts/push_source_docs_to_fabric.py`,
   `scripts/refresh_and_push_japes.py` (regenerate + push back derived-only, preserving the prior
   `original_doc_id`), `scripts/export_document_packet_manifest.py` (pull the live KH registry
   into the committed manifest — the "run on a cloud instance with real KH access, commit the
   result" workflow). `packet_picker` wired into `ci_spread`'s upload flow (tries the picker
   first, falls through to direct upload).
6. **Two japes (jazzx_sdk) papercuts found, worked around in jaci, filed upstream** (can't be
   fixed from this repo — japes is a pinned git dependency, not an editable sibling here, though a
   local checkout exists at `../japes`):
   [japes#57](https://github.com/JazzX-LLC/japes/issues/57) — (a) `MockKnowledgeHubClient`'s
   `data_dir` never actually persists writes (load-only), (b) `FabricConfig.validate_for_mode()`
   requires `knowledge_hub_url` even when `kh_client` is the Mock (which already carries
   `is_mock=True` specifically for this kind of check).

**Deliberately not done, flagged rather than silently skipped:**
- `cre_underwriting`/`portfolio_monitoring`/`insurance_diligence`'s core intake call chains are
  synchronous; the fabric pre-hydrate step (`_hydrate_from_fabric`) is only wired at the
  Streamlit-boundary (`asyncio.run()`) ahead of the upload path, not deep inside the sync parsing
  pipeline — making the whole chain async is a bigger, more invasive change than this round
  attempted.
- `portfolio_monitoring`/`insurance_diligence`'s *default* (non-uploaded) review cases are built
  eagerly at Python import time (`cases.py` module load, before any per-request hydration could
  run) — fabric pre-hydration only covers the upload/packet-pick path, not that eager-import path.
- No direct Azure Blob backend (bypassing Knowledge Hub) was built — confirmed the real
  `jazzx_sdk.clients.knowledge_hub_client.KnowledgeHubClient` is HTTP-only (`httpx`,
  `base_url=".../hub..."`), no Blob SDK usage anywhere in japes; a real KH deployment is already
  Blob-backed server-side, so `build_fabric()`'s existing connected-KH branch already covers it.
  Revisit only if a concrete "KH unreachable but Blob is" deployment gap shows up.

**Convention captured in Claude Code memory** (not duplicated here — see
`~/.claude/projects/-Users-sangit-src-jaci/memory/`): the jaci-vs-japes repo boundary (demo/dev
convenience → jaci; general platform capability → japes), the full document-packet convention
(naming, file locations, the cloud-export-then-commit workflow), and "never bump the version
without asking; default to patch."

Prior round (2026-08-08, kept for history): `CLSpreadContext.control_tolerance` threaded through
so the four arithmetic controls (FR-VAL-1/3/4/5) became reachable in the governed pipeline
(previously dead code despite being implemented/tested); fixed a stale hardcoded "3.0x" leverage
ceiling in `ci_spread`'s UI (real ceiling is 3.5x, read from `CI_REGISTRY` now); investigated and
mostly disproved a "scenarios are inconsistent" premise across all 8 scenarios; found (but didn't
fix) that no conductor populates `CanonicalTrace.steps` with granular per-mode entries, so the
Trace tabs' thinness is a real backend data gap, not presentation; surveyed the `web/commercial-
lending-demo` submodule for portable feature concepts (provenance tooltips, chain-of-thought
banner, DSCR scenario builder, risk-rating panel — none built, just scoped).

---

> **Branch: `dev`** — JACI with AML and KYC scenarios (May 2026)
>
> This branch includes both the original AML investigation and the new KYC/CDD (Know Your Customer / Customer Due Diligence) scenario.
> The KYC scenario uses Anthropic Client SDK instead of OpenAI Agents SDK to validate JAPES's agent platform adapter role.
>
> **KYC Scenario Features:**
> - ✅ SDK: Anthropic Client SDK (`anthropic` package) with claude-sonnet-4-5
> - ✅ Adapter: `src/jaci/sdk/anthropic_adapter.py` for structured output + tool use
> - ✅ Schemas: KYC-specific (RiskTier, ReviewTrigger, RiskTierRecommendation, ReviewFile)
> - ✅ Evidence: 8 KYC tools (identity, BO records, sanctions, adverse media, etc.)
> - ✅ Skills: `prompts/kyc/` with KYC-tuned domain skills for each mode
> - ✅ Conductor: Same loop logic, different convergence criteria
>
> See `docs/JACI_KYC_BUILD_PLAN.md` for full architecture and implementation plan.
>
> **AML Scenario Status:** Charter Alignment Phases 7–10 **COMPLETE** (April 28, 2026)
> - ✅ Phase 7: Canonical cross-linkage (CanonicalTrace, Outcome schemas)
> - ✅ Phase 10: Pack governance (config/packs/aml_investigation_core.yaml)
> - ✅ Phase 8: Evaluator mode (split Python/LLM evaluation)
> - ✅ Phase 9: Curator stub (Layer 1 routing, Layer 2 deferred)

## Build & Test Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Install UI dependencies (for Streamlit dashboard)
pip install -e ".[ui]"

# Run all tests
make test
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/unit/test_schemas.py -v

# Run a single test
python -m pytest tests/unit/test_schemas.py::TestCaseContext::test_open_case -v

# Lint and format
make lint                    # Check only
make format                  # Auto-format
ruff check src/ tests/
ruff format src/ tests/

# Build Docker image
make build

# Run evaluation harness
make eval

# Launch Streamlit dashboard
streamlit run app.py
```

## Streamlit Dashboard

**New in April 2026**: Interactive dashboard for visualizing evaluations and debugging agent flows.

**Features:**
- 📊 **Dashboard**: Compare skill versions, track accuracy trends, analyze costs
- 🔄 **Flow Viewer**: See end-to-end agent execution (Investigator → Verifier → Reasoner → Governor → Narrator)
- 📁 **Case Explorer**: Browse gold cases and compare with evaluation results
- ▶️ **Run Evaluation**: Trigger single/multi-run evaluations from UI
- ✏️ **Skills Editor**: Edit and test domain skills (coming soon)

**Setup:**
```bash
pip install -e ".[ui]"
streamlit run app.py
```

See `APP_README.md` for detailed usage instructions.

## Architecture

JACI is a domain pack built on the JAPES extension framework for AML/KYC investigation.

**SDK Runtime:**
- **AML scenario:** OpenAI Agents SDK (`openai-agents` package)
- **KYC scenario:** Anthropic Client SDK (`anthropic` package) — validates JAPES's agent platform adapter role

**Note:** The old `kyc` branch has been archived as `kyc-archived`. All KYC work is now in `dev`.

### Core Loop Pattern

The **Conductor** (`src/jaci/conductor.py` for AML, `src/jaci/conductor_kyc.py` for KYC) orchestrates a cyclic investigation loop in plain Python (NOT an SDK handoff chain):

```
Conductor (Python loop + guards)
└── calls SDK adapter for each mode:
    Investigator → evidence retrieval → Verifier → back to Investigator
    (repeats until convergence or guard fires)
    → Reasoner → Governor → Narrator (if escalating)

SDK Adapter Layer:
  - AML: OpenAI Agents SDK (Runner.run with output_type)
  - KYC: Anthropic Client SDK (client.messages.create with output_format)
```

### Seven Modes (6 Investigation + 1 EVOLVE)

Each mode in `src/jaci/modes/` is an LLM agent with domain skills loaded from `prompts/`.
Skills are the domain knowledge that make each mode effective (typologies, decision frameworks, policy expertise):

| Mode | Purpose | Tools | When Called |
|------|---------|-------|-------------|
| **Investigator** | Generates hypotheses, requests evidence | All 8 tools | Investigation loop |
| **Verifier** | Attests or flags evidence objects | None (read-only) | Investigation loop |
| **Reasoner** | Produces Close/Escalate recommendation | None | Post-loop |
| **Governor** | Enforces policy gates | None | Post-loop |
| **Narrator** | Drafts SAR narrative | None | Post-loop (Escalate only) |
| **Sentinel** | Monitors loop health (no LLM, pure Python) | None | Investigation loop |
| **Evaluator** | Assesses post-case quality (EVOLVE layer) | None | Post-case (eval harness) |

**Note:** Evaluator is NEVER called by Conductor. It runs post-case in the evaluation harness or periodic review processes.

### Key Data Flow

**Investigation (Conductor):**
1. `AlertTrigger` → Conductor opens `CaseContext`
2. Loop: Investigator updates `Hypothesis[]` → requests `EvidenceRequest[]` → ToolRegistry returns `EvidenceObject[]` → Verifier attests → Sentinel checks guards
3. Post-loop: Reasoner produces `DispositionRecommendation` → Governor checks → Narrator drafts `SARDraft`
4. Output: `CaseFile` with `CanonicalTrace` for BPMN/Flowable handoff

**Post-Case EVOLVE Layer (Evaluation Harness):**
5. L3/FIU review → `Outcome` (human override detection)
6. `compute_deterministic_metrics()` → Python-computed scores (decision_accuracy, evidence_efficiency, policy_compliance, loop_efficiency)
7. `EvaluatorMode.run()` → LLM assessment (SAR quality + improvement signals with closed tag set)
8. `process_evaluation_report()` → Curator routes signals to Knowledge Hub buckets
9. Output: `EvaluationReport` + routed signals for compounding learning

### Tool Registry

`src/jaci/tools/registry.py` implements 8 evidence retrieval tools with circuit breaker pattern. Use `use_mocks=True` for testing without real Integration Hub.

### Configuration

- Environment: `config/settings.py` loads from `.env`
- Autonomy levels: `config/autonomy_ceilings.py` maps risk tiers to action limits
- Model selection: Each mode can use different models (GPT-4o default, claude-sonnet candidates for Governor/Verifier)

---

## Agent Framework & Model Provider — Resolved (2026-08-02, was "Design Decision, April 2026")

JACI-AML uses the OpenAI Agents SDK as its primary runtime, via japes's shared operational
modes (Investigator/Verifier/Reasoner/Governor/Narrator). This is intentional and consistent
with JazzX v2.0 — a Domain Pack choosing one runtime for its vertical is correct.

**The April 2026 "Option A vs Option B" question below is resolved, not by building the
backlogged adapter, but because it turned out to be unnecessary.** japes's `ReasoningAgent`
(the execution mechanism all five shared modes run through) resolves a model by name across
providers — an Anthropic `model_name` (e.g. `"claude-sonnet-4-5-20250929"`) passed to the
*same* `ReasonerMode`/`InvestigatorMode`/etc. used for GPT just works: same prompt, same
Pydantic schema, same Conductor wiring, different model underneath. Verified live end-to-end
(`AMLConductor(reasoner_model="claude-sonnet-4-5-20250929", ...)`, a real Anthropic API call,
a correct `DispositionRecommendation` back) — see "Recent Session Status" above. No SDK
adapter pattern, new per-mode files, or Conductor changes are needed for the shared modes.

(`reasoner_anthropic.py`, referenced below as the prior pattern for a manual per-mode swap,
no longer exists — `kyc_anthropic/modes/reasoner.py`'s `KYCAnthropicReasonerMode` was the
closest surviving example of that hand-built-adapter shape, and it is *not* reusable for
AML: its `review_trigger`/`hypotheses`/`evidence` interface and KYC-specific prompt are
unrelated to AML's `CaseContext`/`DispositionRecommendation` shape. Confirmed by trying and
finding the real, better fix above, not by inspection alone.)

Original framing, kept for context (now historical, not active):

> JACI-AML uses the OpenAI Agents SDK as its primary runtime. This is intentional
> and consistent with JazzX v2.0. The v2.0 Adapter Layer is a platform-level
> capability — a Domain Pack choosing one runtime for its vertical is correct.
>
> For downstream customer interop (e.g. a bank with Anthropic enterprise access):
> the API surface (domain skills in `prompts/`, Pydantic schemas, evidence tools) handles
> most of this transparently. Three seams need attention for a full Anthropic path:
> structured output enforcement, tool call wire format, and SDK client injection.
>
> **Active decision:** Option A (prompt-only, no new code) for Phases 7–10.
> **Backlog item:** Option B (SDK adapter pattern across all six modes, ~1 day) —
> execute after Phase 9 completes, before any OEM or customer code handoff.
>
> Full design: `docs/CHARTER_ALIGNMENT_PLAN_V4_ADAPTER.md` Part 1

---

## Skills Composability — Two-Layer Structure (April 2026)

**Terminology:** "Skills" are the domain knowledge that make modes effective. The term "prompts"
is deprecated in favor of "skills" to better reflect their nature as domain expertise.

The current `prompts/*.md` files combine platform-owned mode base layer with
pack-owned AML-specific skills in a single file. This is a PoC shortcut.

**Target structure (execute as part of Phase 10, not before):**
```
prompts/base/                           # platform-owned mode base layer
  investigator.md, reasoner.md, ...
config/packs/aml_investigation_core/
  mode_tuning/                          # pack-owned AML domain skills
    investigator.md                     # typologies, evidence strategy, thresholds
    reasoner.md                         # decision rubrics, confidence calibration
    governor.md                         # BSA/FinCEN clause namespaces
    narrator.md                         # SAR section templates
    evaluator.md                        # AML quality rubric
```

Conductor assembles: `base_layer + domain_skills` at mode instantiation via context engineering.
Runtime context (evidence, hypotheses, policies, tool results) is composed separately at invocation.

Do NOT use `.py` files per domain — skill content always lives in `.md`.
Python loads it; it does not contain it.

Do NOT refactor skills during Phases 7–10. Execute the split in Phase 10
alongside the pack yaml. Full spec: `docs/CHARTER_ALIGNMENT_PLAN_V4_ADAPTER.md` Part 2

---

## Testing

- Unit tests: `tests/unit/` - schemas, tools
- Integration tests: `tests/integration/` - full conductor loop (requires API key)
- Evaluation: `tests/eval/` - gold cases in `gold_cases/*.json`

Integration/eval tests needing a live LLM call are marked `@pytest.mark.requires_api_key`
(not a bare `@pytest.mark.skip`) — `conftest.py`'s collection hook auto-skips them only when
none of `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`/`GEMINI_API_KEY` is set; no decorator to remove,
just set a key and they run for real. A few individual tests carry their own hardcoded
`@pytest.mark.skip(reason=...)` on top of this for a specific, real reason (e.g. a feature
genuinely not built yet) — check the reason string before assuming a whole file is gated
only by API-key absence.

---

## Performance & Prompt Engineering (April 2026)

### Performance Regression Incident (April 15-20, 2026)

**Timeline:**
- Initial baseline: 60% disposition accuracy with base prompts
- April 15: Model-specific prompt variants created for gpt-5.2 and gpt-5.4-mini
- Result: Performance **regressed to 40% accuracy** (gpt-5.4-mini eval)
- April 20: Root cause identified and fixed

**Root Cause:**
Model-specific prompts in `prompts/gpt-5.2/` and `prompts/gpt-5.4-mini/` became overly prescriptive:
- 50%+ length increase (229 lines vs 150 baseline)
- Heavy use of MANDATORY/CRITICAL framing
- Complex decision tables and examples
- **Result:** Premature convergence (1.0 avg iterations, 0% evidence coverage)

**Classic anti-pattern:** Adding more rules to fix edge cases → performance degrades → add more rules → worse performance.

**Fixes Applied (April 20):**

1. **Conductor Guardrails** (`src/jaci/conductor.py:146-169`):
   ```python
   # Minimum iteration requirement: Must complete at least 2 iterations
   if update.converged and ctx.iteration_count < 2:
       logger.warning("Forcing evidence gathering - minimum iteration not met")
       update.converged = False

   # Minimum evidence coverage: Require at least 2 distinct evidence types
   evidence_types = set(e.evidence_type for e in ctx.evidence)
   if update.converged and len(evidence_types) < 2:
       logger.warning("Forcing more evidence - minimum coverage not met")
       update.converged = False
   ```

2. **Updated Base Prompts** (`prompts/investigator.md`, `prompts/reasoner.md`):
   - Clearer convergence criteria with explicit requirements
   - Explicit warning: "Do NOT converge on your first turn"
   - Evidence gathering requirements: ≥2 tool types

3. **Disabled Model-Specific Prompts**:
   - Renamed `prompts/gpt-5.2/` → `prompts/gpt-5.2.bak/`
   - Renamed `prompts/gpt-5.4-mini/` → `prompts/gpt-5.4-mini.bak/`
   - All models now use improved base prompts

**Validated Results:**
- case_01 (ESCALATE structuring): ✓ PASS (4 iterations, 0.90 confidence)
- case_06 (CLOSE verified business): ✓ PASS (2 iterations, 0.95 confidence)
- Full eval: [Results TBD - eval in progress]

### Prompt Engineering Guidelines

**Lessons Learned:**

1. **Simplicity over specificity**: Focused, concise prompts outperform long prescriptive ones
2. **Guardrails in code > rules in prompts**: Enforce critical constraints in Python, not prose
3. **Test, don't guess**: Validate prompt changes with eval harness before committing
4. **Avoid prompt bloat**: If a prompt needs complex decision trees, the underlying design may be wrong

**Model-Specific Prompt Policy (April 20 forward):**

- **Default:** All models use base prompts in `prompts/*.md`
- **Exceptions:** Only create model-specific variants (`prompts/{model}/`) if:
  - A specific model has a documented, reproducible issue with base prompts
  - The fix is minimal (<10 line addition)
  - The variant improves eval metrics by ≥5% over base
  - Document the rationale in this file

**Current State (April 20):**
- Base prompts: Investigator (150 lines), Reasoner (158 lines), others (<100 lines)
- Model-specific prompts: None (all disabled as of April 20)
- Guardrails: Minimum 2 iterations, minimum 2 evidence types (enforced in conductor)
- **Result:** Evidence coverage improved to 100%, but accuracy dropped to 40% (guardrails forced more evidence, confusing reasoner)

### Prompt Improvements Round 2 (April 23, 2026)

**Problem:** Guardrails improved evidence coverage (70% → 100%) but hurt accuracy (60% → 40%)

**Root Cause Analysis:**
- Guardrails force 2+ iterations and 2+ evidence types
- Investigator gathers 8-12 evidence objects (some duplicate)
- Reasoner struggles with larger evidence sets:
  - Wrong typology selection (case_03, case_04, case_05)
  - Over-escalation of false positives (case_06, case_07, case_08, case_10)
  - High LLM variance between runs

**Improvements Applied:**

1. **Reasoner Prompt - Typology Differentiation Matrix** (`prompts/reasoner.md`):
   - Added explicit section distinguishing 4 main typologies
   - Each typology gets: Pattern, Key Indicators, Eliminators, Common Confusion, Example
   - Typology Selection Priority rules (most specific wins, core vs secondary, pattern match)
   - Addresses failure pattern: correct disposition but wrong typology

2. **Reasoner Prompt - Evidence Assessment Framework**:
   - Quality over quantity guidance
   - Evidence weighting: High/Medium/Low quality categories
   - Handling large evidence sets: de-duplicate mentally, core evidence first, corroboration > accumulation
   - Addresses issue: 8-12 evidence objects overwhelming the reasoner

3. **Reasoner Prompt - Decision Pathway**:
   - 4-step framework: False Positives → Hypothesis State → Typology ID → Recommendation
   - Clearer thresholds: <0.15 = CLOSE, ≥0.85 = ESCALATE, 0.70-0.84 = likely CLOSE
   - Reasoning examples for each decision type

4. **Investigator Prompt - Focused Hypothesis Generation** (`prompts/investigator.md`):
   - Alert-driven typology selection (1-3 hypotheses, not all 4)
   - When to investigate each typology (alert triggers, immediate evidence, confirms/eliminates)
   - Evidence request strategy (core → corroborating → policy)
   - Confidence calibration guidance (avoid common errors)

**Expected Impact:**
- Better typology identification (address 10% typology accuracy)
- Reduced over-escalation (distinguish false positives from true alerts)
- Better handling of 8-12 evidence objects (quality over quantity)
- Target: 60%+ disposition accuracy, 40%+ typology accuracy

**Validation Results (flex_gpt-5.2):**
- Prompt length: Reasoner 250 lines (was 158), Investigator 306 lines (was 155)
- Added frameworks, not just rules (structured decision-making)
- **Disposition accuracy: 40%** (unchanged from April 22)
- **Typology accuracy: 30%** (3x improvement from 10%)
- **Efficiency: 3.5 iterations** (was 4.5), **0% guard fires** (was 20%)
- **Cost: $0.084/case** (was $0.125/case, 33% reduction)
- **Passed cases: 3/10** (case_01, case_02, case_09 all structuring)

**Analysis:**
- ✅ Typology differentiation matrix helped (10% → 30% typology accuracy)
- ✅ Efficiency improved (fewer iterations, no guard fires, lower cost)
- ❌ **Still over-escalating:** All 4 CLOSE cases failed (case_06, case_07, case_08, case_10)
- ❌ flex_gpt-5.2 not reliably applying false positive checks despite explicit prompts

**Model Testing (April 23):**

After identifying flex_gpt-5.2 over-escalation issue, tested **flex_gpt-5.4**:
- Quick test on case_01 (ESCALATE structuring): ✓ PASS
- Quick test on case_06 (CLOSE verified business): ✓ PASS (flex_gpt-5.2 failed this)
- **Key finding:** flex_gpt-5.4 correctly applies false positive checks
- **Full eval result (exp_015):** 80% disposition accuracy, 30% typology accuracy, 6/10 passed, $0.65/eval

**Prompt Update Results (April 23, post-exp_015):**

After achieving 80% with flex_gpt-5.4, four targeted prompt fixes were applied to address remaining failures:
1. UNUSUAL_WIRE_PATTERN → shell_company_layering mapping (case_03)
2. ATM withdrawals + salary cycle → eliminate structuring (case_07)
3. PEP confirmation overrides corporate counterparty count (case_04)
4. "trade cancelled" returns → round_tripping (case_05)

**Results with updated prompts:**
- **exp_016 (flex_gpt-5.4, first run):** 50% accuracy, 4/10 passed - REGRESSION
  - New failures: case_06, case_08 now escalate (were passing before)
  - Fixes didn't help target cases
- **exp_018 (flex_gpt-5.4, rerun):** 70% accuracy, 5/10 passed - PARTIAL RECOVERY
  - Fixed: case_08 (PEP name collision) now passes
  - Still failing: case_06, case_07 (over-escalating), case_05 (under-escalating)
- **exp_017 (flex_gpt-5.4-mini):** 40% accuracy, 3/10 passed, 20% guard fire rate
  - Too weak for this task, not recommended

**Current Status:**
- **Best result:** exp_015 (80% accuracy, 6/10 passed) with original prompts
- Prompt updates introduced instability and contradictory guidance
- flex_gpt-5.4 is the recommended model

**Cost Comparison (per eval, from MLflow token_metrics):**
- flex_gpt-5.4-mini: $0.12/eval (40% accuracy - not cost-effective)
- gpt-4o: $0.25/eval (50% accuracy - historical baseline)
- flex_gpt-5.2: $0.84/eval (40% accuracy with improved prompts)
- **flex_gpt-5.4**: $0.65/eval (80% accuracy - BEST) ✓
- gpt-5.4 (non-flex): Expected to be significantly more expensive

---

## Synthetic Dataset — Design Decisions (April 2026)

The following was established in a design session outside Claude Code and is the
authoritative spec. Do not revert these decisions without understanding the rationale.

### What changed and why

The PoC was built using the build plan. A separate design session
then produced a richer synthetic dataset and resolved schema conflicts between the
auto-generated fixtures and the eval harness. Key decisions:

**1. Fixture architecture: two-layer separation**

The original `src/jaci/tools/mock_connectors.py` contained generic placeholder data
(e.g. "John Doe", hardcoded $9,500 deposits). This was fine for unit tests but useless
for eval — it returns the same data regardless of which case is running, making
disposition accuracy non-deterministic.

The new design separates concerns:

- `tests/fixtures/case_fixtures.py` — the DATA layer. Contains rich, case-specific
  evidence payloads for all 10 gold cases, keyed by `case_id` and `tool_name`.
  Also exports `POLICY_CLAUSES` (14 entries) and `TYPOLOGY_LIBRARY` (9 entries)
  as shared reference data used across the system.
- `tests/fixtures/test_context.py` — thread-local active case ID injector.
  Call `set_active_case_id("case_01")` before running a case, `clear_active_case_id()`
  in teardown. This is how the mock connectors know which fixture to return.
- `src/jaci/tools/mock_connectors.py` — the CONNECTOR layer. Now routes to
  `case_fixtures.py` when a case ID is active, falls back to generic placeholder
  data when no case ID is set (preserving existing `test_tools.py` behaviour).

**2. Gold case schema: unified `expected_outcome` key**

The original two gold cases (`structuring_escalate.json`, `false_positive_close.json`)
used `expected_outcome` as the assertion key. The new cases were initially generated
with `expected_disposition` instead. This was a conflict — `run_eval.py` reads
`gold_case["expected_outcome"]`.

Decision: standardise on `expected_outcome` throughout. The new cases have been
written with this key. The two original thin cases have been retired to
`docs/eval/*.json.bak` — they are superseded by cases 01 and 06 respectively.

The `expected_outcome` block now carries both the fields `run_eval.py` needs
(`recommendation`, `confirmed_typology`, `min_confidence`, `required_evidence_types`,
`required_policy_citations`) and richer assertion fields used by future eval logic
(`eliminated_typologies`, `close_rationale_keywords`, `min_attested_evidence_count`).

**3. Transaction field naming: ISO 20022 alignment**

All transaction records in `case_fixtures.py` use ISO 20022-aligned field names:
`instructed_amount`, `debtor_agent`, `creditor_agent`, `purpose_code`,
`remittance_info`, `end_to_end_id`. This is a data model choice, not a wire format
implementation — no XML envelopes. The rationale: these are the field names real
bank connectors will expose when the Integration Hub is wired, so aligning now
avoids a rename sweep later.

**4. Gold case distribution**

10 cases covering:

| # | Label | Typology | Difficulty |
|---|-------|----------|------------|
| case_01 | ESCALATE | Structuring — single account | baseline |
| case_02 | ESCALATE | Structuring — multi-account | intermediate |
| case_03 | ESCALATE | Shell company layering | intermediate |
| case_04 | ESCALATE | PEP + rapid movement | intermediate |
| case_05 | ESCALATE | Round-tripping | baseline |
| case_06 | CLOSE | Unusual cash — cash-intensive business | baseline |
| case_07 | CLOSE | Structuring pattern — salary cycle | baseline |
| case_08 | CLOSE | PEP watchlist — name collision | intermediate |
| case_09 | ESCALATE | Edge: SAR deadline guard fires | edge |
| case_10 | CLOSE | Edge: signal decay guard fires | edge |

**5. TBML (trade-based money laundering) excluded from PoC**

TBML was considered and explicitly excluded. It requires trade document evidence
(invoices, bills of lading) that the mock connector layer does not model and the
Integration Hub does not yet expose. It is a Phase 2+ addition once the loop is
validated on the current typology set.

### How to add a new gold case

**Directory-based structure (current as of May 2026):**

1. Create directory: `tests/eval/gold_cases/{scenario}/case_NN/`
2. Write `trigger.json` with `alert` and `expected_outcome`
3. (Optional for AML) Add `CASE_NN` dict to `tests/fixtures/case_fixtures.py` if using mock fixtures
4. (Recommended for KYC) Generate source documents and verification reports using scripts in `scripts/`

**Example structure:**
```
tests/eval/gold_cases/aml/case_NN/
├── trigger.json         # Alert trigger + expected outcome
└── README.md           # Case documentation (optional)

tests/eval/gold_cases/kyc_anthropic/case_NN/
├── trigger.json         # Review trigger + expected outcome
├── evidence.json        # Evidence objects (if applicable)
├── documents/
│   ├── source/         # Source PDFs (passports, bank statements, etc.)
│   └── reports/        # Verification reports (HTML)
└── README.md           # Case documentation
```

No changes needed to evaluation harnesses - they automatically discover cases in the directory structure.

### How to use fixtures in a test

```python
from tests.fixtures.test_context import set_active_case_id, clear_active_case_id
from jaci.tools.registry import ToolRegistry

def test_structuring_escalate():
    set_active_case_id("case_01")
    try:
        registry = ToolRegistry(use_mocks=True)
        # ... run conductor, assert disposition ...
    finally:
        clear_active_case_id()
```

Or use the pytest fixture in `conftest.py` (add one if needed):

```python
@pytest.fixture
def active_case(request):
    case_id = request.param
    set_active_case_id(case_id)
    yield case_id
    clear_active_case_id()
```

### Eval metrics targets (from build plan Phase 6)

| Metric | Target | Notes |
|--------|--------|-------|
| Disposition accuracy | ≥ 0.80 | CI gate in `run_eval.py` |
| Evidence coverage | All required types retrieved | Per `required_evidence_types` in `expected_outcome` |
| Citation completeness | ≥ 1 evidence citation per SAR section | Escalate cases only |
| Loop efficiency | avg iterations < 5 | Non-edge cases only |
| Guard fire rate | baseline only | Cases 09, 10 must fire their respective guards |
| Hallucination rate | 0 | SAR narrative claims without EvidenceObject citation |

---

## Charter Alignment — COMPLETE ✅

**Status:** Phases 7, 10, 8, 9 completed April 28, 2026.

All three charter gaps have been closed. The EVOLVE layer is operational and integrated into the evaluation harness.

### Implementation Summary

**Phase 7: Canonical Cross-Linkage** ✅
- Extended `DispositionRecommendation` with canonical fields: `decision_id`, `policy_refs`, `evidence_refs`, `trace_id`, `pack_id`
- Created `CanonicalTrace` schema (src/jaci/schemas/canonical_trace.py) with execution lineage
- Created `Outcome` schema (src/jaci/schemas/outcome.py) for L3/FIU review outcomes
- Conductor emits `CanonicalTrace` with full cross-linkage to decisions, evidence, and policies
- All II canonical objects follow Schema Spec §8 cross-linkage invariants

**Phase 10: Pack Governance** ✅
- Created `config/packs/aml_investigation_core.yaml` as traceable reference for pack_id
- Documents autonomy ceilings, policy families, typology library, human checkpoints
- Runtime values remain hardcoded in `config/autonomy_ceilings.py` (appropriate for PoC draft status)
- Pack governance chain (ABA, JAP, Overlay) deferred to production readiness

**Phase 8: Evaluator Mode** ✅
- Implemented v3 split design: Python-computed metrics + LLM qualitative assessment
- Created `src/jaci/modes/evaluator.py`:
  - `compute_deterministic_metrics()` — Pure Python, no LLM, O(n) over evidence
  - `EvaluatorMode` — LLM call for SAR quality (Escalate only) + improvement signals (all cases)
- Created `src/jaci/schemas/evaluation_report.py` with explicit field sourcing:
  - Python: `scores`, `findings`, `human_override_detected`
  - LLM: `sar_quality_score`, `sar_quality_assessment`, `improvement_signals`
- Created `prompts/evaluator.md` with closed 6-tag signal set
- Created `tests/unit/test_evaluator.py` — 17 unit tests, no API key required, all passing

**Phase 9: Curator Stub** ✅
- Implemented Layer 1 (Python routing), Layer 2 (LLM synthesis) deferred to production
- Created `src/jaci/schemas/curator_queue.py`:
  - `CuratorQueueEntry` — Individual improvement signal queue entry
  - `KnowledgeHubBucket` — Signal collection by tag type
  - `SignalTag` enum — Closed set of 6 valid tags
  - `QueueStatus` enum — Signal processing states
- Created `src/jaci/modes/curator_stub.py`:
  - `parse_signal_tag()` — Validates tags against closed set, rejects invalid signals
  - `route_improvement_signals()` — Routes to Knowledge Hub buckets
  - `process_evaluation_report()` — Main entry point, creates audit trail
- Tag validation enforced in code and prompts

**Integration** ✅
- Modified `tests/eval/run_eval.py` to call EVOLVE layer after each case:
  1. Constructs `Outcome` from gold case expected vs actual
  2. Calls `compute_deterministic_metrics()` → Python scores
  3. Calls `EvaluatorMode.run()` → LLM assessment
  4. Calls `process_evaluation_report()` → Curator routing
  5. Tracks signals and reports for MLflow logging
- Created `tests/eval/test_evolve_integration.py` — 4 integration tests, all passing
- Created `tests/eval/test_evolve_validation.py` — Quick validation script (1-2 cases)

### Three Gaps Closed

**Gap 1 — EVOLVE layer absent:** ✅ CLOSED
- Evaluator mode assesses post-case quality (deterministic metrics + LLM qualitative)
- Curator routes improvement signals to Knowledge Hub buckets for compounding learning
- Compounding loop now operational (Layer 1 routing; Layer 2 synthesis deferred)

**Gap 2 — Pack governance orphaned:** ✅ CLOSED
- `pack_id = "aml-investigation-core"` now has traceable parent reference
- Documented in `config/packs/aml_investigation_core.yaml`
- Runtime hardcoded values appropriate for PoC draft status

**Gap 3 — Canonical cross-linkage partial:** ✅ CLOSED
- `DispositionRecommendation` extended with canonical fields
- `CanonicalTrace` and `Outcome` schemas created
- Full cross-linkage: decision ← trace → evidence, policies
- Schema Spec §8 invariants enforced

### Key Design Decisions Implemented

1. **No `CanonicalDecision` wrapper.** Extended `DispositionRecommendation` directly with canonical fields.

2. **Split evaluation architecture.** Python computes deterministic metrics (fast, no LLM cost). LLM assesses SAR quality and generates improvement signals (1 call per case).

3. **Closed signal tag set.** Only 6 valid tags: `evidence_checklist`, `typology_threshold`, `policy_clause`, `loop_guard`, `sar_template`, `other`. Enforced in prompt and code.

4. **Two-layer Curator.** Layer 1 (Python routing) operational. Layer 2 (LLM synthesis when bucket ≥ 3) deferred to production.

5. **Unit tests without API keys.** `tests/unit/test_evaluator.py` (17 tests) validates deterministic metrics with no LLM calls.

### How to Use the EVOLVE Layer

**Quick validation (1-2 cases):**
```bash
python tests/eval/test_evolve_validation.py
```

**Full evaluation (11 cases):**
```bash
python tests/eval/run_eval.py
```

**What you get:**
- `EvaluationReport` per case with:
  - Python scores: decision_accuracy, evidence_efficiency, policy_compliance, loop_efficiency
  - LLM assessment: sar_quality (Escalate only), improvement_signals (all cases)
  - Auto-generated findings for scores < 0.7
- Improvement signals routed to Knowledge Hub buckets
- Signal distribution tracked in MLflow
- Full reports saved to `output/evaluations/`

**Example output:**
```
case_01:
  Investigation: escalate (conf=0.96)
  Outcome: sar_filed (match=True)
  Scores: decision_accuracy=1.00
  Signals: 4 generated, 4 routed
  Buckets: khub_policy_clause, khub_evidence_checklist, khub_sar_template

Total improvement signals: 6
Signal distribution: {evidence_checklist: 2, policy_clause: 2, sar_template: 2}
```

### Closed Signal Tag Reference

| Tag | Purpose | Example |
|-----|---------|---------|
| `evidence_checklist` | Evidence types, depth, quantity issues | "Missing BO records for corporate entities" |
| `typology_threshold` | Confidence calibration, threshold tuning | "Confidence too conservative for clear patterns" |
| `policy_clause` | Missing or incorrect policy clauses | "Missing CDD clause for structuring cases" |
| `loop_guard` | Iteration limits, convergence criteria | "Premature convergence, min iterations not met" |
| `sar_template` | SAR structure, citations, missing fields | "Narrative missing transaction quantification" |
| `other` | Anything not fitting above 5 categories | "Alert validation step needed" |

### Files Created

**Schemas (Phase 7 & 8 & 9):**
- `src/jaci/schemas/canonical_trace.py` — Execution lineage for investigation
- `src/jaci/schemas/outcome.py` — L3/FIU review outcome
- `src/jaci/schemas/evaluation_report.py` — Post-case quality assessment
- `src/jaci/schemas/curator_queue.py` — Signal routing queue and buckets

**Modes (Phase 8 & 9):**
- `src/jaci/modes/evaluator.py` — Deterministic metrics + LLM assessment
- `src/jaci/modes/curator_stub.py` — Layer 1 signal routing (Layer 2 deferred)

**Prompts (Phase 8):**
- `prompts/evaluator.md` — Evaluator system prompt with closed tag set

**Configuration (Phase 10):**
- `config/packs/aml_investigation_core.yaml` — Pack governance reference

**Tests (Phase 8 & 9):**
- `tests/unit/test_evaluator.py` — 17 unit tests for deterministic metrics
- `tests/eval/test_evolve_integration.py` — 4 integration tests
- `tests/eval/test_evolve_validation.py` — Quick validation script (1-2 cases)

**Modified:**
- `src/jaci/schemas/case_context.py` — Extended DispositionRecommendation, added canonical_trace to CaseFile
- `src/jaci/conductor.py` — Emits CanonicalTrace with cross-linkage
- `tests/eval/run_eval.py` — Integrated EVOLVE layer (Outcome → Evaluator → Curator)
- `src/jaci/settings.py` — Added evaluator_model config
- `config/autonomy_ceilings.py` — Linked to pack yaml

### Implementation Notes

**Design Invariants (maintained):**
- Evaluator is NEVER called inside the live investigation loop
- Curator Layer 1 routing is pure Python (NOT an LLM call)
- SAR filing remains human-only (regulatory requirement)
- Gold cases reused for evaluation (no second dataset needed)

**Deferred to Production:**
- Curator Layer 2 LLM synthesis (when bucket ≥ 3 signals)
- Pack loader (`config/pack_loader.py`)
- BPMN workflow diagrams (replaced by `docs/process_design.md`)

**Validation Results:**
- 17/17 unit tests passing (tests/unit/test_evaluator.py)
- 4/4 integration tests passing (tests/eval/test_evolve_integration.py)
- Validation run (2 cases): $0.09 total cost, 6 improvement signals generated, 100% routing success

---

## Policy Regulatory Sources

**Overview:** All JACI-AML Policy objects are `PolicyType.REGULATORY`, based on authoritative US federal AML/BSA regulations and international standards. These are regulatory floor requirements (Layer 1) — banks cannot deviate downward.

**Critical Design Point:** Typology definitions and detection heuristics live in Domain Pack prompts (`prompts/investigator.md`), NOT as Policy objects. Policy objects encode only government-issued regulatory requirements.

### Primary Regulatory Sources

**1. FinCEN Regulations (31 CFR)**

| Regulation | Purpose | Effective Date | Policy Objects |
|------------|---------|----------------|----------------|
| **31 CFR 1020.320** | Suspicious Activity Report (SAR) filing requirements | July 1, 2002 | BSA_SAR_POLICY (5 rules) |
| **31 CFR 1010.311** | Currency Transaction Report (CTR) filing | Oct 26, 1970 | BSA_CTR_POLICY (2 rules) |
| **31 CFR 1010.230** | Customer Due Diligence (CDD) — Beneficial Ownership | May 11, 2018 | BSA_CDD_POLICY (7 rules) |

**2. US Federal Statute**

| Statute | Purpose | Effective Date | Referenced In |
|---------|---------|----------------|---------------|
| **31 USC § 5324** | Structuring Transactions to Evade Reporting | Oct 27, 1986 | BSA_CTR_POLICY (structuring offense) |

**3. FATF International Standards**

| Recommendation | Purpose | Effective Date | Referenced In |
|----------------|---------|----------------|---------------|
| **FATF R.12** | Politically Exposed Persons (PEPs) | Feb 16, 2012 | BSA_CDD_POLICY (EDD-PEP) |
| **FATF R.24** | Transparency of Legal Persons — Beneficial Ownership | Feb 16, 2012 | BSA_CDD_POLICY (beneficial ownership) |

**4. FFIEC Guidance**

| Guidance | Purpose | Effective Date | Referenced In |
|----------|---------|----------------|---------------|
| **BSA/AML Examination Manual** | Enhanced Due Diligence (EDD) for PEPs and high-risk customers | 2014 | BSA_CDD_POLICY (EDD rules) |

**5. FinCEN Advisories**

| Advisory | Purpose | Effective Date | Referenced In |
|----------|---------|----------------|---------------|
| **FIN-2014-A005** | Round-Trip Transactions — SAR Indicators | 2014 | BSA_SAR_POLICY (round-tripping detection) |
| **FinCEN SAR Guidance** | SAR filing procedures | 2012 | BSA_SAR_POLICY (filing procedures) |

### Policy Object → Regulation Mapping

**BSA_SAR_POLICY** (5 rules)
- `BSA-SAR-TRIGGER-001`: $5,000 SAR threshold ← 31 CFR 1020.320(a)(2)
- `BSA-SAR-DEADLINE-30DAY`: 30-day filing deadline ← 31 CFR 1020.320(b)(3)
- `BSA-SAR-STRUCTURING-001`: Structuring detection ← 31 CFR 1020.320 + FIN-2014-A005
- `BSA-SAR-ROUND-TRIP-001`: Round-trip detection ← FIN-2014-A005
- `BSA-SAR-001`: (Sunset legacy alias → BSA-SAR-TRIGGER-001)

**BSA_CTR_POLICY** (2 rules)
- `BSA-CTR-001`: $10,000 cash transaction threshold ← 31 CFR 1010.311
- `AML-STRUCTURING-001`: (Sunset legacy alias → BSA-CTR-001)

**BSA_CDD_POLICY** (7 rules)
- `CDD-BO-003`: 25% beneficial ownership threshold ← 31 CFR 1010.230
- `CDD-RULE-001`: Customer Due Diligence requirements ← 31 CFR 1010.230
- `CDD-LINKED-ACCOUNTS-001`: Linked account identification ← FinCEN CDD Final Rule
- `EDD-PEP-001`: Enhanced Due Diligence for PEPs ← FATF R.12 + FFIEC Manual
- `EDD-HIGH-RISK`: EDD for high-risk customers ← FFIEC Manual
- `FATF-R12-PEP`: PEP identification ← FATF R.12
- `FATF-R24-BO`: Beneficial ownership transparency ← FATF R.24

### SourceRef Object Structure

Each Policy object contains `source_refs[]` with full citations:

```python
SourceRef(
    ref_id="sar_trigger_31cfr",
    title="Suspicious Activity Reporting Requirements",
    authority="FinCEN",
    ref_type="regulation",
    section="31 CFR 1020.320(a)(2)",
    url="https://www.fincen.gov/resources/statutes-and-regulations",
    effective_date=datetime(2002, 7, 1)
)
```

Each Rule cites these via `citations=["sar_trigger_31cfr"]` linking to parent Policy's source_refs.

### What's NOT in Policy Objects

**Vendor Interpretation (NOT Policy objects):**
- Typology definitions (structuring, layering, PEP, round-tripping) → `prompts/investigator.md`
- Detection heuristics and thresholds → `prompts/investigator.md`
- Confidence calibration rules → `prompts/reasoner.md`
- SAR section templates → `prompts/narrator.md`

These are pack-owned guidance assets in the mode tuning layer, not government-issued regulations.

**Institutional Policies (NOT in PoC):**
- Bank-specific risk appetite thresholds
- Customer-specific enhanced monitoring rules
- Internal escalation procedures beyond regulatory requirements

These would be delivered via Certified Client Overlay (policy_type=INSTITUTIONAL, overlay_id set).

### Immutability Contract

A Policy is **immutable within its effective period**. When regulations change:
1. Create new Policy version (increment MAJOR semver)
2. Set `supersedes="OLD_POLICY_ID"` on new Policy
3. Set `expiry_date` on old Policy
4. Old CaseFiles retain policy_refs to historical version (audit trail preserved)

Example: When FinCEN updated SAR rules in 2024 (hypothetical):
```python
BSA_SAR_POLICY_V2 = Policy(
    policy_id="BSA_SAR_POLICY",
    version="2.0.0",  # ← Major version bump
    supersedes="BSA_SAR_POLICY:1.0.0",
    effective_date=datetime(2024, 1, 1),
    ...
)
```

### References

**Complete documentation:**
- Detailed regulatory sources: `docs/POLICY_REGULATORY_SOURCES.md`
- Policy implementation: `src/jaci/pack/policy_registry.py`
- Canonical schema: `docs/CANONICAL_POLICY_SCHEMA_REFERENCE.md`
- Unified architecture: `docs/UNIFIED_POLICY_ARCHITECTURE.md`

**External resources:**
- FinCEN: https://www.fincen.gov/resources/statutes-and-regulations
- FATF Recommendations: https://www.fatf-gafi.org/en/publications/Fatfrecommendations/
- FFIEC BSA/AML Manual: https://www.ffiec.gov/bsa_aml_infobase/
- 31 USC § 5324: https://www.law.cornell.edu/uscode/text/31/5324

### Git Commit and Push Policy

**Commits: ✅ ALLOWED**
- Create commits with descriptive messages
- Stage changes with `git add`
- Use the commit workflow from system instructions

**Pushing: ❌ FORBIDDEN WITHOUT APPROVAL**
- **NEVER** run `git push` without explicit user request
- **NEVER** run `git push origin <branch>` automatically
- User must review commits and decide when to push
- User needs to verify attribution and commit messages
- Never show AI attribution (e.g. Co-Authored-By: Claude Sonnet 4.5)

**Rationale:**
- User needs to review all commits before they go to remote
- Attribution must be verified
- Commit messages may need adjustment
- User controls when work is shared with team


Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Documentation and attribution
- Code should not look like it came from AI, including any comments or commits that say Co-authored
by Claude Sonnet etc
- CHANGELOG, README, and ARCHITECTURE md files should be regularly updated
- If signitificant changes, the bump up at least patch version. For major version update, enquire
---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

