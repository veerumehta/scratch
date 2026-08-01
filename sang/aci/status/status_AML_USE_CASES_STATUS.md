# AML Use Cases Implementation Status

**Last Updated:** 2026-05-11
**JACI Version:** 0.3.x (using JAPES v0.3.2)
**Source:** JazzX Platform v2.0 Roadmap Presentation (May 11, 2026)

## Executive Summary

This document tracks the implementation status of 14 AML use cases identified in the JazzX Platform v2.0 roadmap. These use cases span the complete AML transaction monitoring workflow from L1 triage through SAR filing and ongoing monitoring.

**Current State:**
- ✅ **4 use cases fully implemented** (28%)
- ✅ **2 use cases enabled by JAPES v0.3.2** (14%)
- 🟡 **4 use cases partially implemented** (29%)
- ❌ **4 use cases not yet started** (29%)

**Strategic Alignment:**
- JAPES v0.3.2 (May 2026) delivered EVOLVE modes (Evaluator + Curator)
- Enables Tier 0 capabilities: Evaluation Framework, Learning Service, Trust Governance
- Closes compounding learning loop for AML quality improvement

---

## Use Case Status Matrix

| ID | Use Case | Role/Phase | Status | Priority | Notes |
|----|----------|------------|--------|----------|-------|
| A01 | Alert intake and context assembly | L1 · Triage | ✅ Complete | - | Conductor + CaseContext |
| A02 | Counterparty screening and history check | L1 · Triage | 🟡 Partial | HIGH | Mock implementation only |
| A03 | Triage disposition and narrative generation | L1 · Triage | 🟡 Partial | MEDIUM | No L1-specific mode |
| A04 | Flow of funds analysis and typology detection | L2 · Investigation | ✅ Complete | - | InvestigatorMode (4 typologies) |
| A05 | Related party investigation (UBO, sanctions, PEP, adverse media) | L2 · Investigation | 🟡 Partial | HIGH | No graph traversal |
| A06 | Enhanced Due Diligence | L2 · Investigation | 🟡 Partial | MEDIUM | No EDD workflow |
| A07 | Case narrative synthesis and disposition recommendation | L2 · Investigation | ✅ Complete | - | ReasonerMode |
| A08 | QA validation of completed investigation | L3 · Senior Review | ✅ **ENABLED** | HIGH | EvaluatorMode (JAPES v0.3.2) |
| A09 | Coaching and feedback loop to L2 | L3 · Senior Review | ✅ **ENABLED** | HIGH | Curator (JAPES v0.3.2) |
| A10 | SAR narrative drafting from case file | SAR · Filing | ✅ Complete | - | NarratorMode |
| A11 | SAR form completion with data accuracy gate | SAR · Filing | ❌ Not Started | HIGH | No FinCEN form mapping |
| A12 | Continuing SAR tracking | SAR · Ongoing | ❌ Not Started | MEDIUM | No lifecycle tracking |
| A13 | RFI management across phases | L1/L2 · Cross-phase | ❌ Not Started | HIGH | No RFI workflow |
| A14 | Case and SAR history retrieval across customer and related parties | L1/L2 · Cross-phase | ❌ Not Started | MEDIUM | No history lookup |

---

## Detailed Use Case Analysis

### ✅ Fully Implemented (4 use cases)

#### A01: Alert Intake and Context Assembly
**Description:** Automatically ingests a transaction monitoring alert and assembles the full customer context — account history, prior alerts, KYC data — so L1 analysts start each review fully loaded, not hunting across systems.

**JACI Implementation:**
- **Component:** `CaseContext` initialization in Conductor
- **Location:** `src/jaci/conductor.py:73-95`
- **Schema:** `src/jaci/schemas/case_context.py` - `CaseContext`, `AlertTrigger`
- **Status:** Production-ready

**Key Features:**
- Parses `AlertTrigger` with alert type and entities
- Initializes `CaseContext` with empty evidence list, hypothesis list
- Tracks iteration count, convergence state, guard fires
- Thread-safe session management for conversation persistence

**No gaps identified.**

---

#### A04: Flow of Funds Analysis and Typology Detection
**Description:** Traces money movement across accounts and entities to identify structuring, layering, or other known AML typologies — giving L2 investigators a visual and narrative map of the pattern.

**JACI Implementation:**
- **Component:** InvestigatorMode with hypothesis-driven investigation
- **Location:** `jazzx_runtime_sdk.modes.operational.investigator` (migrated to JAPES v0.3.1)
- **Schema:** `src/jaci/schemas/case_context.py` - `Hypothesis`, `HypothesisUpdate`
- **Status:** Production-ready with 4 typologies

**Supported Typologies:**
1. `structuring` - Deposits/withdrawals just under reporting thresholds
2. `shell_company_layering` - Unusual wire patterns with unverified entities
3. `pep_rapid_movement` - High-risk individual with complex fund flows
4. `round_tripping` - Circular money movement with cancelled trades

**Evidence Requests:**
- Transaction patterns (deposits, withdrawals, wires)
- Counterparty details and beneficial ownership
- Account activity timelines
- Sanctions/PEP screening results

**No critical gaps.** May need additional typologies for production (TBML, trade finance, etc.)

---

#### A07: Case Narrative Synthesis and Disposition Recommendation
**Description:** Synthesizes all L2 investigative work into a coherent case narrative and issues a disposition recommendation with supporting rationale — ready for senior review with no manual reformatting.

**JACI Implementation:**
- **Component:** ReasonerMode with disposition logic
- **Location:** `jazzx_runtime_sdk.modes.operational.reasoner` (migrated to JAPES v0.3.1)
- **Schema:** `src/jaci/schemas/case_context.py` - `DispositionRecommendation`
- **Status:** Production-ready

**Key Features:**
- Analyzes all hypotheses and evidence collected during investigation
- Generates disposition: `CLOSE` or `ESCALATE`
- Provides confidence score (0.0-1.0) with calibration
- Identifies primary typology from investigation
- Lists policy citations (BSA/FinCEN clauses)
- Generates structured rationale with evidence references

**Disposition Logic:**
- Confidence < 0.15 → CLOSE (false positive)
- Confidence 0.70-0.84 → likely CLOSE (weak evidence)
- Confidence ≥ 0.85 → ESCALATE (strong suspicion)

**No gaps identified.** Current performance: 80% disposition accuracy (eval exp_015).

---

#### A10: SAR Narrative Drafting from Case File
**Description:** Translates a completed investigation case file into a draft SAR narrative that meets FinCEN language and structural requirements — eliminating the blank-page problem for filing teams.

**JACI Implementation:**
- **Component:** NarratorMode with SAR generation
- **Location:** `jazzx_runtime_sdk.modes.operational.narrator` (migrated to JAPES v0.3.1)
- **Schema:** `src/jaci/schemas/case_context.py` - `SARDraft`
- **Status:** Production-ready

**Key Features:**
- Generates FinCEN-compliant SAR narrative from case file
- Structures narrative into required sections:
  - Subject identification
  - Suspicious activity description
  - Transaction details with amounts/dates
  - Typology classification
  - Evidence summary with citations
- Only runs for ESCALATE cases (skipped for CLOSE)
- Uses case context, disposition, evidence objects as input

**Gap:** No validation against FinCEN 314 character limits per field (see A11).

---

### ✅ Enabled by JAPES v0.3.2 (2 use cases)

#### A08: QA Validation of Completed Investigation
**Description:** Runs an automated quality check against L2 case packages — verifying completeness, logical consistency, and documentation standards before the case reaches a senior reviewer.

**JACI Implementation:**
- **Component:** EvaluatorMode (JAPES v0.3.2)
- **Location:** `jazzx_runtime_sdk.modes.evolve.evaluator`
- **Schema:** `src/jaci/schemas/evaluation_report.py` - `EvaluationReport`
- **Status:** ✅ **Implemented in eval harness** (May 2026)
- **Integration:** `tests/eval/run_eval.py:246-280`

**Architecture - Split Evaluation:**

1. **Deterministic Metrics** (Python, no LLM cost):
   - `decision_accuracy`: Did reasoner match ground truth? (binary: 1.0 or 0.0)
   - `evidence_efficiency`: % of required evidence types retrieved
   - `policy_compliance`: % of required policy citations present
   - `loop_efficiency`: Iterations vs. max allowed (1.0 if < 5 iterations)
   - **Function:** `compute_deterministic_metrics()` - O(n) over evidence list

2. **Qualitative Assessment** (LLM, single call per case):
   - SAR quality score (0.0-1.0) for ESCALATE cases only
   - SAR quality rationale (narrative assessment)
   - Improvement signals (1-5 signals per case) with closed tag set

**Improvement Signal Tags (Closed Set):**
- `evidence_checklist` - Missing or insufficient evidence types
- `typology_threshold` - Confidence calibration issues
- `policy_clause` - Missing or incorrect policy citations
- `loop_guard` - Iteration or convergence problems
- `sar_template` - SAR structure or citation issues
- `other` - Anything not fitting above categories

**Cost:** ~$0.01-0.02 per case (single LLM call for qualitative assessment)

**Current Integration:**
- ✅ Runs automatically in eval harness after each case
- ✅ Logs metrics to MLflow
- ✅ Saves full `EvaluationReport` to `output/evaluations/`
- ❌ **Gap:** No L3 reviewer UI to view results

**Next Steps:**
1. Build L3 review dashboard to surface evaluation reports
2. Expose deterministic metrics as case scorecard
3. Display improvement signals for L2 analyst review
4. Add batch evaluation mode for QA team

---

#### A09: Coaching and Feedback Loop to L2
**Description:** Surfaces L3-level feedback on weak or incomplete investigations back to L2 analysts in structured, actionable form — compressing the learning cycle and reducing rework.

**JACI Implementation:**
- **Component:** Curator utilities (JAPES v0.3.2)
- **Location:** `jazzx_runtime_sdk.modes.evolve.curator`
- **Schema:** `src/jaci/schemas/curator_queue.py` - `CuratorQueueEntry`, `KnowledgeHubBucket`
- **Status:** ✅ **Layer 1 routing implemented** (May 2026)
- **Integration:** `tests/eval/run_eval.py:282-300`

**Architecture - Two Layer Design:**

**Layer 1: Python Routing (Implemented)**
- Parses improvement signals from `EvaluationReport`
- Validates signal tags against closed set
- Routes to Knowledge Hub buckets by tag type:
  - `khub_evidence_checklist` - Evidence strategy issues
  - `khub_typology_threshold` - Confidence calibration
  - `khub_policy_clause` - Policy citation problems
  - `khub_loop_guard` - Investigation loop issues
  - `khub_sar_template` - SAR structure problems
  - `khub_other` - Miscellaneous issues
- Creates `CuratorQueueEntry` with audit trail
- **Cost:** Zero (pure Python, no LLM)

**Layer 2: LLM Synthesis (Deferred to Production)**
- When bucket reaches threshold (e.g., ≥3 signals of same type)
- LLM synthesizes pattern across signals
- Generates coaching recommendation or prompt refinement
- Triggers pack promotion workflow
- **Status:** Intentionally deferred (not needed for MVP)

**Current Integration:**
- ✅ Routes all signals from evaluator to Knowledge Hub
- ✅ Tracks signal distribution in MLflow
- ✅ Logs routing success/failure
- ❌ **Gap:** No L3 UI to review routed signals
- ❌ **Gap:** No Layer 2 synthesis (intentional deferral)

**Next Steps:**
1. Build L3 signal review dashboard (view by bucket/tag)
2. Add signal annotation workflow (L3 can validate/dismiss signals)
3. Track signal resolution (which signals led to prompt changes)
4. Implement Layer 2 synthesis when pattern detection needed

**Compounding Loop Status:**
```
Investigation → Evaluation → Signal Generation → Routing → [Gap: L3 Review UI] → Prompt Refinement
     ✅              ✅              ✅              ✅              ❌                    Future
```

---

### 🟡 Partially Implemented (4 use cases)

#### A02: Counterparty Screening and History Check
**Description:** Screens all transaction counterparties against sanctions lists, adverse media, and internal watchlists in real time, surfacing hits with confidence scores so L1 can disposition faster.

**JACI Implementation:**
- **Component:** Tool registry with `get_counterparty_screening_results`
- **Location:** `src/jaci/tools/registry.py:241-268`
- **Schema:** Tool returns dict with `screening_status`, `risk_score`, `hits`
- **Status:** 🟡 **Mock implementation only**

**Current Capabilities:**
- Accepts `counterparty_name` and `counterparty_account` as input
- Returns hardcoded mock screening results
- Mock data includes:
  - `screening_status`: "clear" or "potential_hit"
  - `risk_score`: 0.0-1.0 (randomly generated)
  - `hits`: List of watchlist matches (always empty in mock)

**Gaps:**
- ❌ No real watchlist integration (OFAC, PEP lists, UN sanctions)
- ❌ No adverse media search
- ❌ No confidence scoring for fuzzy name matches
- ❌ No historical screening results (prior hits for same entity)
- ❌ No continuous monitoring (re-screening when lists update)

**Priority:** **HIGH** - Critical for L1 triage workflow in production

**Recommended Implementation:**
1. **Near-term (Demo):** Enhance mocks with realistic screening scenarios from gold cases
2. **Production:** Integrate with SymphonyAI watchlist feeds or ComplyAdvantage API
3. **Advanced:** Add fuzzy matching with confidence scores for name variants

**Estimated Effort:** 3-5 days (mock enhancement) or 2-3 weeks (production integration)

---

#### A03: Triage Disposition and Narrative Generation
**Description:** Drafts an L1 closure or escalation narrative based on assembled context and screening results — reducing write-up time from minutes to seconds while maintaining audit trail quality.

**JACI Implementation:**
- **Component:** ReasonerMode (used for L2 disposition, not L1 triage)
- **Location:** `jazzx_runtime_sdk.modes.operational.reasoner`
- **Status:** 🟡 **No L1-specific mode**

**Current Capabilities:**
- ReasonerMode can generate dispositions for any case
- Full investigation loop runs even for obvious false positives
- Generates detailed rationale with evidence citations

**Gaps:**
- ❌ No lightweight L1 triage mode (should be faster than full investigation)
- ❌ No triage-specific prompt (different from L2 investigation prompt)
- ❌ No early exit logic (L1 should close obvious false positives without L2 investigation)
- ❌ No L1 vs L2 escalation criteria (when to hand off to L2)

**Priority:** **MEDIUM** - Nice to have but not blocking MVP

**Recommended Implementation:**

**Option A: Reuse ReasonerMode with Triage Prompt**
- Create `prompts/reasoner_triage.md` for L1 use case
- Shorter, faster reasoning focused on quick elimination:
  - Known false positive patterns (e.g., salary deposits flagged as structuring)
  - Counterparty screening hits
  - Simple rule-based checks
- Run with lower iteration limit (1-2 iterations max)
- **Effort:** 2-3 days

**Option B: Create Dedicated TriageMode**
- New mode inheriting from BaseMode
- Lighter weight than full InvestigatorMode
- Fast screening-based disposition
- Escalate to L2 if any uncertainty
- **Effort:** 1 week

**Recommended:** Option A (reuse existing mode, faster to implement)

---

#### A05: Related Party Investigation (UBO, Sanctions, PEP, Adverse Media)
**Description:** Expands the investigation to beneficial owners, associated entities, and politically exposed persons, synthesizing findings from multiple data sources into a single coherent risk picture.

**JACI Implementation:**
- **Component:** Tool registry with `get_beneficial_ownership`
- **Location:** `src/jaci/tools/registry.py:270-300`
- **Schema:** Tool returns dict with `beneficial_owners` list
- **Status:** 🟡 **Basic implementation only**

**Current Capabilities:**
- Accepts `entity_name` and `entity_id` as input
- Returns list of beneficial owners with ownership percentages
- Mock data includes entity name, ownership %, entity type

**Gaps:**
- ❌ No UBO graph traversal (only returns direct beneficial owners, not chains)
- ❌ No cross-referencing with PEP lists (ownership + PEP screening not connected)
- ❌ No sanctions screening for UBOs
- ❌ No adverse media search for related entities
- ❌ No entity relationship visualization
- ❌ No "associated entities" detection (same address, phone, email)

**Priority:** **HIGH** - Complex ownership structures are core to AML

**Recommended Implementation:**

**Phase 1: UBO Graph Traversal (2 weeks)**
1. Extend `get_beneficial_ownership` to recursively fetch ownership chains
2. Build in-memory ownership graph (NetworkX or similar)
3. Identify ultimate beneficial owners (≥25% ownership or control)
4. Return flattened UBO list with ownership paths

**Phase 2: Cross-Reference Screening (1 week)**
1. For each UBO, call `get_counterparty_screening_results`
2. Aggregate PEP hits, sanctions hits, adverse media
3. Risk-score the ownership structure (higher risk if UBO has hits)

**Phase 3: Associated Entities (2 weeks)**
1. Add tool `get_associated_entities` that searches by:
   - Shared address
   - Shared phone/email
   - Shared authorized signers
   - Shared IP address (for online banking)
2. Build entity network graph
3. Screen entire network for risk

**Estimated Total Effort:** 5-6 weeks for full implementation

**Integration with Knowledge Fabric (v2.0 Roadmap):**
- UBO graph and entity network are perfect use cases for Knowledge Fabric dynamic ontology
- Store entity relationships in Knowledge Hub graph
- Enable semantic queries: "Find all entities with PEP connections within 2 degrees"

---

#### A06: Enhanced Due Diligence
**Description:** Produces a deep-dive risk profile for high-risk customers or flagged relationships — pulling together source of wealth, business purpose, geographic risk, and regulatory red flags in one structured document.

**JACI Implementation:**
- **Component:** InvestigatorMode (can request EDD evidence types)
- **Location:** `jazzx_runtime_sdk.modes.operational.investigator`
- **Status:** 🟡 **No dedicated EDD workflow**

**Current Capabilities:**
- InvestigatorMode can request evidence via tool registry
- Tools available:
  - `get_account_profile` - Account details, business type
  - `get_beneficial_ownership` - UBO information
  - `get_counterparty_screening_results` - Risk screening
- Evidence types support EDD data collection

**Gaps:**
- ❌ No EDD workflow orchestration (when to trigger EDD, what's required)
- ❌ No source of wealth analysis
- ❌ No geographic risk scoring (high-risk jurisdictions)
- ❌ No business purpose verification
- ❌ No EDD report template (structured output)
- ❌ No EDD risk scoring framework
- ❌ No regulatory flagging (e.g., "customer in high-risk jurisdiction with PEP ownership")

**Priority:** **MEDIUM** - Important but can defer to post-v1.0

**Recommended Implementation:**

**Phase 1: EDD Workflow (2 weeks)**
1. Create `EDDMode` that orchestrates EDD-specific investigation
2. Trigger conditions:
   - High-risk customer (PEP, sanctions hit)
   - High-risk jurisdiction
   - Unusual transaction volumes
   - Regulatory requirement (periodic review)
3. Define EDD evidence checklist:
   - Source of wealth documentation
   - Business purpose verification
   - UBO ownership structure
   - Geographic risk assessment
   - Regulatory red flags

**Phase 2: EDD Report (1 week)**
1. Create `EDDReport` schema (similar to `SARDraft`)
2. Sections:
   - Customer overview
   - Risk factors identified
   - Source of wealth analysis
   - UBO structure and screening results
   - Geographic risk summary
   - Recommendation (approve, enhanced monitoring, decline)

**Phase 3: Risk Scoring (1 week)**
1. Implement EDD risk scoring framework
2. Weight risk factors:
   - PEP status (high weight)
   - Sanctions hits (very high weight)
   - High-risk jurisdiction (medium weight)
   - Opaque ownership (medium weight)
   - Cash-intensive business (low weight)
3. Generate overall EDD risk score (0.0-1.0)

**Estimated Total Effort:** 4-5 weeks for full implementation

**Integration Point:** Could be triggered by GovernorMode as policy gate (e.g., "EDD required for all PEPs before account approval")

---

### ❌ Not Yet Implemented (4 use cases)

#### A11: SAR Form Completion with Data Accuracy Gate
**Description:** Populates all structured SAR form fields from the case file and runs a pre-submission accuracy gate to catch mismatches, missing fields, or data inconsistencies before filing.

**Current State:** ❌ **Not implemented**

**Related Component:** NarratorMode generates SAR narrative (A10) but doesn't map to FinCEN form fields

**Requirements:**

**FinCEN Form Fields (SAR-MSB, SAR-DI):**
- Part I: Filing institution information (BSA ID, name, address, TIN)
- Part II: Subject information (name, SSN/TIN, address, DOB, occupation)
- Part III: Suspicious activity classification (checkboxes for 35+ activity types)
- Part IV: Transaction location and amount information
- Part V: Suspicious activity narrative (free text, 314 char/field limit)
- Part VI: Filing institution contact information

**Gaps:**
- ❌ No schema for structured SAR form (only `SARDraft` with free text)
- ❌ No field extraction from case context (map case data → form fields)
- ❌ No FinCEN activity type classification (map typology → checkboxes)
- ❌ No character limit validation (Part V narrative has 314 char limit per field)
- ❌ No pre-submission accuracy gate:
  - Check for missing required fields
  - Validate TIN format
  - Verify amounts match transaction evidence
  - Check date ranges are consistent
- ❌ No FinCEN XML generation (BSA E-Filing System format)

**Priority:** **HIGH** - Required for production SAR filing

**Recommended Implementation:**

**Phase 1: SAR Form Schema (1 week)**
1. Create `SARForm` schema matching FinCEN SAR-MSB/SAR-DI structure
2. Define all required fields with validation rules
3. Add FinCEN activity type enum (35 categories)

**Phase 2: Field Extraction (2 weeks)**
1. Build `SARFormMapper` that extracts from `CaseContext`:
   - Subject info from alert trigger
   - Amounts from transaction evidence
   - Typology → activity type mapping
   - Narrative from `SARDraft`
2. Handle missing/incomplete data gracefully
3. Flag fields that require manual review

**Phase 3: Validation Gate (1 week)**
1. Implement pre-submission validation:
   - Required field checks
   - TIN format validation
   - Amount/date consistency checks
   - Character limit enforcement
   - Cross-field validation (e.g., "if activity type X, then field Y required")
2. Generate validation report with errors/warnings

**Phase 4: FinCEN XML Export (1 week)**
1. Generate FinCEN BSA E-Filing XML from `SARForm`
2. Validate against FinCEN XSD schema
3. Add batch filing support (multiple SARs in one submission)

**Estimated Total Effort:** 5-6 weeks

**Integration with Process Engine (v2.0 Roadmap):**
- SAR filing workflow maps to BPMN process
- Human review checkpoints before submission
- Auto-retry on validation errors
- Submission confirmation tracking

---

#### A12: Continuing SAR Tracking
**Description:** Monitors open SARs for triggering activity that requires a continuing report, auto-flagging cases and pre-populating the continuation form based on new transaction data.

**Current State:** ❌ **Not implemented**

**Requirements:**

**Continuing SAR Triggers:**
- Same subject, same activity type, within 90 days of original SAR
- Cumulative amounts exceed thresholds
- New information about subject or activity
- Regulatory requirement for periodic updates

**Gaps:**
- ❌ No SAR lifecycle tracking (filed SARs not tracked in system)
- ❌ No ongoing monitoring of SAR subjects
- ❌ No trigger detection for continuing reports
- ❌ No continuing SAR workflow
- ❌ No pre-population of continuation form from original SAR
- ❌ No regulatory deadline tracking (continuing SARs also have 30-day deadline)

**Priority:** **MEDIUM** - Important but post-filing workflow

**Recommended Implementation:**

**Phase 1: SAR Registry (1 week)**
1. Create `SARRegistry` schema to track filed SARs:
   - SAR reference number
   - Subject identifiers
   - Activity type(s)
   - Filing date
   - Status (filed, continuing, closed)
2. Store in Knowledge Hub with 5-year retention
3. Index by subject ID for fast lookup

**Phase 2: Ongoing Monitoring (2 weeks)**
1. Add trigger: New alert for SAR subject → check SAR registry
2. If match found within 90 days:
   - Flag as potential continuing SAR
   - Route to SAR filing team
   - Pre-populate continuation form
3. Track cumulative amounts across original + continuing activity

**Phase 3: Continuation Workflow (1 week)**
1. Create `ContinuingSARDraft` that references original SAR
2. Copy subject info, activity type from original
3. Add new transaction details since original filing
4. Generate supplemental narrative describing new activity
5. Maintain audit trail linking continuation to original

**Estimated Total Effort:** 4 weeks

**Integration with A14 (Case History):** Continuing SAR detection benefits from comprehensive case history retrieval across customer and related parties.

---

#### A13: RFI Management Across Phases
**Description:** Manages the full lifecycle of Requests for Information — drafting, tracking responses, and routing answers back to the relevant case — across L1 and L2 phases without manual handoffs.

**Current State:** ❌ **Not implemented**

**Requirements:**

**RFI Lifecycle:**
1. **Request Creation:** L1 or L2 analyst identifies missing information needed for disposition
2. **Drafting:** Generate RFI with specific questions for customer/branch/third party
3. **Routing:** Send RFI to appropriate party via appropriate channel
4. **Tracking:** Monitor RFI status (pending, overdue, received)
5. **Response Integration:** Route response back to case, update evidence
6. **Deadline Management:** Track response deadlines, escalate overdue RFIs

**Gaps:**
- ❌ No RFI schema
- ❌ No RFI generation workflow
- ❌ No RFI tracking system
- ❌ No integration with case context (RFIs not linked to evidence gaps)
- ❌ No response routing (how does response get back to case?)
- ❌ No deadline tracking
- ❌ No RFI templates (common questions for different scenarios)

**Priority:** **HIGH** - Common real-world requirement

**Recommended Implementation:**

**Phase 1: RFI Schema & Workflow (2 weeks)**
1. Create `RFIRequest` schema:
   - RFI ID (unique)
   - Case ID (linked case)
   - Requested by (L1/L2 analyst)
   - Request date
   - Response deadline
   - Questions (list of specific questions)
   - Target (customer, branch, third party)
   - Status (draft, sent, pending, received, overdue, closed)
2. Create `RFIResponse` schema:
   - RFI ID (linked request)
   - Received date
   - Responder
   - Answers (list of answers to questions)
   - Attachments (supporting documents)

**Phase 2: RFI Generation (1 week)**
1. Add RFI generation to InvestigatorMode or as separate mode
2. Detect evidence gaps during investigation
3. Generate targeted RFI questions:
   - "Please provide documentation for source of funds for [transaction]"
   - "Please explain business purpose for [wire transfer]"
   - "Please provide updated KYC documentation"
4. Use RFI templates for common scenarios

**Phase 3: Tracking & Integration (1 week)**
1. Add RFI tracking dashboard:
   - Show all open RFIs by case
   - Highlight overdue RFIs
   - Track average response time
2. When RFI response received:
   - Route to original case
   - Add response to case evidence
   - Resume investigation if paused
   - Notify assigned analyst

**Phase 4: Cross-Phase Handoff (1 week)**
1. When L1 escalates to L2, transfer all open RFIs
2. L2 can view L1 RFIs and responses
3. L2 can issue additional RFIs
4. Maintain complete RFI history in case file

**Estimated Total Effort:** 5 weeks

**Integration with Process Engine:** RFI workflow is perfect for BPMN modeling with wait states, timeouts, and escalation paths.

---

#### A14: Case and SAR History Retrieval Across Customer and Related Parties
**Description:** Instantly surfaces prior cases, SARs, and alert history for a customer and all linked entities — giving analysts the institutional memory needed to detect repeat patterns and meet lookback requirements.

**Current State:** ❌ **Not implemented**

**Requirements:**

**History Lookup Scenarios:**
1. **Customer history:** All prior cases and SARs for same customer
2. **Related party history:** Cases/SARs for beneficial owners, authorized signers, associated entities
3. **Pattern detection:** Similar typologies across multiple customers
4. **Lookback requirement:** Regulatory requirement to review prior activity (e.g., 5-year lookback)

**Gaps:**
- ❌ No case history storage (cases not persisted after completion)
- ❌ No SAR registry (see A12)
- ❌ No entity graph (related parties not linked)
- ❌ No semantic search across case narratives
- ❌ No pattern detection across historical cases
- ❌ No timeline view of customer activity

**Priority:** **MEDIUM** - Important for repeat offender detection but not MVP-blocking

**Recommended Implementation:**

**Phase 1: Case History Storage (1 week)**
1. Persist completed `CaseFile` to Knowledge Hub
2. Index by:
   - Subject ID
   - Case ID
   - Disposition
   - Typology
   - Filing date
3. Retain for regulatory period (5+ years)

**Phase 2: Entity Graph (2 weeks)**
1. Build entity relationship graph:
   - Customer → Beneficial Owners
   - Customer → Authorized Signers
   - Customer → Associated Entities (shared address, phone, etc.)
2. Store in Knowledge Hub graph structure
3. Query: "Find all entities within N degrees of customer X"

**Phase 3: History Retrieval (2 weeks)**
1. Create `get_case_history` tool:
   - Input: Customer ID or entity ID
   - Returns: List of prior cases with disposition, typology, date
   - Includes SAR references if filed
2. Create `get_related_party_history` tool:
   - Input: Customer ID
   - Returns: Cases for all related entities (UBOs, authorized signers)
   - Groups by entity with relationship type

**Phase 4: Pattern Detection (2 weeks)**
1. Add semantic search across case narratives:
   - "Find cases similar to current typology"
   - "Find customers with same counterparties"
2. Surface historical patterns during investigation:
   - "This customer had 2 prior structuring alerts that were closed"
   - "Beneficial owner has 3 SAR filings in past 2 years"

**Estimated Total Effort:** 7 weeks

**Integration with Knowledge Fabric (v2.0 Roadmap):**
- This use case is the **canonical example** of Knowledge Fabric value
- Dynamic ontology: Entities, relationships, and case history form knowledge graph
- Semantic layer: Enable natural language queries across historical cases
- Continuous hydration: Graph updates as new cases are investigated

**Architecture Alignment:**
- Knowledge Fabric (Tier 1 on roadmap): "Generate a knowledge graph for each run time object (eg: mortgage loan or AML case)"
- This is exactly what A14 requires for case history

---

## Priority Matrix

### Immediate Priorities (Next 2 Weeks)

| Use Case | Complexity | Customer Impact | Implementation |
|----------|------------|-----------------|----------------|
| **A08: L3 QA Validation** | Low | High | Build UI for EvaluatorMode results |
| **A09: L3 Coaching Loop** | Low | High | Build signal review dashboard |
| **A02: Counterparty Screening** | Medium | High | Enhance mocks or integrate real feeds |
| **A11: SAR Form Completion** | Medium | High | Map NarratorMode → FinCEN form |

**Rationale:**
- A08/A09 leverage newly delivered JAPES v0.3.2 capabilities
- A02 is critical for L1 triage workflow
- A11 is required for production SAR filing

### Near-Term Priorities (Next Month)

| Use Case | Complexity | Customer Impact | Implementation |
|----------|------------|-----------------|----------------|
| **A05: Related Party Investigation** | High | High | UBO graph traversal + screening |
| **A13: RFI Management** | Medium | High | Full RFI workflow |
| **A03: L1 Triage** | Low | Medium | Lightweight reasoner for L1 |

**Rationale:**
- A05 is core AML functionality for complex ownership
- A13 is common real-world workflow requirement
- A03 improves efficiency but not blocking

### Medium-Term Priorities (Q3 2026)

| Use Case | Complexity | Customer Impact | Implementation |
|----------|------------|-----------------|----------------|
| **A06: Enhanced Due Diligence** | High | Medium | EDD workflow + risk scoring |
| **A12: Continuing SAR Tracking** | Medium | Medium | SAR lifecycle management |
| **A14: Case History Retrieval** | High | Medium | Graph-based history lookup |

**Rationale:**
- A06/A12/A14 are important but can defer to post-MVP
- A14 benefits from Knowledge Fabric (Tier 1 in v2.0 roadmap)

---

## Technical Dependencies

### JAPES Platform Capabilities Required

| Use Case | Required JAPES Component | Status | Notes |
|----------|---------------------------|--------|-------|
| A08 | EvaluatorMode | ✅ v0.3.2 | Available now |
| A09 | Curator | ✅ v0.3.2 | Layer 1 only |
| A02 | Integration Hub | 🟡 Tier 1 | Need watchlist connectors |
| A05 | Knowledge Fabric | 🟡 Tier 1 | Need graph support |
| A11 | Process Engine | ✅ v0.3.0+ | BPMN available |
| A12 | Memory Service | 🟡 Tier 1 | Need persistent SAR registry |
| A13 | Process Engine | ✅ v0.3.0+ | RFI workflow in BPMN |
| A14 | Knowledge Fabric | 🟡 Tier 1 | Need graph + semantic search |

### JACI Schema Extensions Required

| Use Case | New Schema | Priority |
|----------|------------|----------|
| A11 | `SARForm` | HIGH |
| A12 | `SARRegistry`, `ContinuingSARDraft` | MEDIUM |
| A13 | `RFIRequest`, `RFIResponse` | HIGH |

---

## Success Metrics

### Phase 1 (Immediate - 2 weeks)
- [ ] L3 can view EvaluationReport for any completed case
- [ ] L3 can see improvement signals routed by tag type
- [ ] Counterparty screening returns realistic results for demo
- [ ] SAR form can be exported with all required fields populated

### Phase 2 (Near-term - 1 month)
- [ ] UBO graph traversal works for 3+ ownership layers
- [ ] RFI workflow supports full lifecycle (create, track, respond, integrate)
- [ ] L1 triage mode can disposition obvious false positives in <30 seconds

### Phase 3 (Medium-term - Q3 2026)
- [ ] EDD workflow generates structured risk reports
- [ ] Continuing SAR detection auto-flags within 90 days
- [ ] Case history retrieval surfaces related party cases

---

## Appendix: Use Case to Platform Component Mapping

### Canonical Chain Alignment

| Canonical Object | Use Cases Supported | JACI Schema |
|------------------|---------------------|-------------|
| **Policy** | All (policy citations) | Policy registry |
| **Evidence** | A01, A02, A04, A05, A06 | EvidenceObject |
| **Decision** | A03, A07, A08 | DispositionRecommendation |
| **Trace** | A08, A09 | CanonicalTrace |
| **Outcome** | A08, A09 | Outcome |

### Cognitive Modes Alignment

| Cognitive Mode | Use Cases Supported | Status |
|----------------|---------------------|--------|
| **Investigator** | A01, A04, A05, A06 | ✅ Operational |
| **Reasoner** | A03, A07 | ✅ Operational |
| **Verifier** | A08 (implicit) | ✅ Operational |
| **Governor** | A06 (EDD gate) | ✅ Operational |
| **Narrator** | A10 | ✅ Operational |
| **Sentinel** | Loop health | ✅ Operational |
| **Evaluator** | A08 | ✅ EVOLVE (v0.3.2) |
| **Curator** | A09 | ✅ EVOLVE (v0.3.2) |

---

## Contact & Updates

**Document Owner:** JACI Team
**Last Updated:** 2026-05-11
**Next Review:** After A08/A09 UI implementation

**Related Documents:**
- `ARCHITECTURE.md` - JACI architecture overview
- `CLAUDE.md` - Build & test instructions
- `docs/CHARTER_ALIGNMENT_PLAN_V4_ADAPTER.md` - Platform alignment strategy
- JazzX Platform v2.0 Roadmap Presentation (May 11, 2026)
