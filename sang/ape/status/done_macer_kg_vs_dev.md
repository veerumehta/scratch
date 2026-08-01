# MACER kg Branch vs dev Branch - Analysis Report

**Analysis Date:** May 23, 2026  
**Branches Compared:** `dev` (baseline) vs `kg` (research branch)  
**Commit Difference:** 1,251 commits (kg ahead of dev)  
**Line Changes:** +1,776,121 insertions, -110 deletions  

---

## Executive Summary

The `kg` branch represents 6+ months of intensive Knowledge Graph extraction research and experimentation. It contains:
- **Production-Ready Features:** Already migrated to JAPES or ready to merge
- **Research Infrastructure:** KG ontology system, evaluation framework
- **Experimental Data:** 472 experiment result files (19 experiments × ~25 loans)
- **Streamlit Dashboard:** Experiment comparison and visualization UI

**Key Finding:** Most valuable features have been migrated to JAPES (v1.1.3). Remaining items are MACER-specific research infrastructure.

---

## 1. Already Migrated to JAPES ✅

### Knowledge Graph Store (Completed)
- **JAPES v1.1.3** now provides:
  - `BaseKGStore` interface
  - `InMemoryKGStore` (from MACER design)
  - `KnowledgeHubKGStore` (production backend)
  - `Triple` model with `chunk_label` field
  - Serialization (to_json/from_json)
  - Source migration validator

- **MACER kg branch** uses:
  - `MACERKnowledgeGraphStore` wrapper extending JAPES
  - MACER-specific methods: merge_name_variants, merge_similar_subjects, format_for_prompt, to_html

**Status:** ✅ Complete - MACER uses JAPES platform storage

---

## 2. Production-Ready Code in kg Branch

### A. Knowledge Graph Infrastructure (MACER-Specific)

#### 1. KG Ontology System
**Files:**
- `src/macer/jtbd/kg_ontology.py` (510 lines)
- `ontologies/base/mortgage_kg_ontology.yaml` (2,487 lines)
- `ontologies/base/mortgage_kg_extensions.yaml` (auto-generated predicates)
- `ontologies/promoted/promoted_predicates.yaml` (user-approved predicates)

**Capabilities:**
- Load mortgage ontology from YAML (entity types, predicates, ranges)
- Normalize extracted predicates to canonical forms (e.g., "annual_income" → "borrower.income_monthly")
- Merge k9 inherited predicates from parent ontology layers
- Post-extraction triple normalization and validation
- Prompt formatting with ontology guidance

**Purpose:** Solve predicate explosion problem (2,869 unique predicates, 75% singletons)

**Recommendation:** Keep in MACER - this is mortgage domain-specific

#### 2. KG Extraction & Orchestration
**Files:**
- `src/macer/jtbd/kg_extraction_agent.py` - Phase 1 extraction from document chunks
- `src/macer/jtbd/kg_orchestration.py` - Multi-phase KG extraction pipeline
- ~~`src/macer/jtbd/kg_chunking.py`~~ - **✅ MIGRATED to JAPES v1.1.4** (May 23, 2026)
- `src/macer/jtbd/kg_prompts.py` - Extraction prompt templates
- `src/macer/jtbd/kg_proposals.py` - Enrichment proposals generation
- `src/macer/jtbd/kg_compaction.py` - KG cleanup and deduplication

**Pipeline:**
1. **Phase 1:** Extract triples from document chunks (per-section)
2. **Phase 2:** Enrich with cross-document inferences
3. **Phase 3:** Compact and deduplicate
4. **Phase 4:** Normalize predicates via ontology

**Status:**
- ✅ **kg_chunking.py** - Migrated to JAPES as `jazzx_sdk.document.chunking` (v1.1.4)
  - MACER wrapper: 236 → 101 lines (-57%)
  - JAPES commit: 24bed5f
  - MACER commit: 193c85e
- 🟡 **Other files** - Keep in MACER (mortgage-specific extraction logic)

#### 3. Knowledge Graph Tools (OpenAI Agents Functions)
**File:** `src/macer/tools/knowledge_graph.py` (413 lines)

**Functions:**
- `query_knowledge_graph_tool()` - @function_tool decorator for OpenAI Agents
- `list_entities_tool()` - Entity discovery
- `get_entity_relationships_tool()` - Relationship queries

**Purpose:** Expose KG to JTBD agents as function calling tools

**Recommendation:** Keep in MACER - OpenAI Agents integration wrapper

### B. Run Configuration & Experiment Framework

#### 1. Run Config System
**Files:**
- `src/macer/models/run_config.py` (150 lines)
- `tests/test_run_config.py` (292 lines)

**Purpose:**
- Define experiment parameters (model, KG mode, JTBD version, etc.)
- Enable reproducible research runs
- Track configuration across experiments

**Recommendation:** Keep in MACER - research infrastructure

#### 2. Streamlit Dashboard
**Files:**
- `src/macer/streamlit_app/app.py` (84 lines)
- `src/macer/streamlit_app/pages/experiments.py` (886 lines)
- `src/macer/streamlit_app/pages/run_new.py` (261 lines)
- `src/macer/streamlit_app/services/data_service.py` (883 lines)
- `src/macer/streamlit_app/services/ui_service.py` (332 lines)

**Capabilities:**
- Compare experiment results side-by-side
- Visualize accuracy vs cost trade-offs
- Launch new experiment runs
- Explore KG extraction quality metrics

**Recommendation:** Keep in MACER - research visualization tool

### C. Model & Settings Updates

#### 1. JTBD Model Enhancements
**File:** `src/macer/models/jtbd.py`

**New Fields:**
- `ExtractedTriple` model - triples extracted during verification
- `JTBDResult.extracted_triples: list[ExtractedTriple]` - inline KG extraction

**Purpose:** Allow JTBDs to extract KG triples during verification (not just separate phase)

**Recommendation:** Keep in MACER - mortgage JTBD enhancement

#### 2. Settings Enhancements
**File:** `src/macer/settings.py`

**New Settings:**
- OpenTelemetry configuration (trace_id, span_id, OTLP endpoint)
- Model cost tracking
- Experiment configuration paths

**Recommendation:** OpenTelemetry settings should go to JAPES if not already there

### D. OpenTelemetry Integration (Partial)

**Commits:**
- `870065d` - feat: add OTel tracing and logging via common telemetry pattern
- `7011a9a` - feat: propagate OTel trace ID into JSON log context via logging filter
- Several style/fix commits

**Files:** (not present in kg branch checkout - may have been reverted or not merged)
- Expected: `src/macer/telemetry.py` with decorators
- Expected: 36 unit tests

**Status:** ⚠️ Unclear - commits exist but files may not be in current kg state

**Recommendation:** Check if JAPES already has OTel tracing (it has opentelemetry-sdk dependency)

---

## 3. Research Infrastructure (Keep in MACER)

### A. Experiment Scripts (32 scripts)

**Analysis Scripts:**
- `analyze_experiment.py` - Compare experiment results
- `analyze_kg_quality.py` - KG extraction quality metrics
- `analyze_kg_extraction_gap.py` - Coverage analysis
- `analyze_kg_queries.py` - Query pattern analysis
- `analyze_jtbd_sizes.py` - Token usage analysis
- `compare_experiments.py` - Multi-experiment comparison
- `compare_baseline.py` - Baseline comparison

**Pipeline Scripts:**
- `extract_kg.py` - Run KG extraction pipeline
- `run_loan_pipeline.sh` - End-to-end loan processing
- `generate_experiment_scripts.py` - Experiment generation
- `collect_experiment_results.py` - Results aggregation

**Utility Scripts:**
- `export_predicates_to_k9.py` - Export to k9 ontology
- `update_cross_loan_table.py` - Cross-loan tracking
- `build_opus_baseline.py` - Baseline generation

**Recommendation:** Keep in MACER - essential research infrastructure

### B. Ontology Files

**Files:**
- `ontologies/base/mortgage_kg_ontology.yaml` (2,487 lines) - Core ontology
- `ontologies/base/mortgage_kg_chunking.yaml` - Document chunking rules
- `ontologies/base/mortgage_kg_extensions.yaml` - Auto-generated extensions
- `ontologies/promoted/promoted_predicates.yaml` - Approved predicates

**Recommendation:** Keep in MACER - mortgage domain knowledge

### C. Documentation

**File:** `docs/kg_predicate_normalization_proposal.md` (180 lines)

**Content:**
- Analysis of predicate explosion problem (2,869 predicates, 75% singletons)
- Proposed canonical predicates (24 core, ~200 total)
- Implementation options (post-extraction normalization vs strict enforcement)
- Impact estimates (93% predicate reduction, 35-45% triple reduction)

**Recommendation:** Keep in MACER - valuable research documentation

---

## 4. Experimental Data (Exclude from dev)

### A. Experiment Results

**Location:** `experiments/` directory

**Contents:**
- 19 experiments across 25+ loans
- Each experiment contains:
  - README.md with results summary
  - knowledge_graph.json (extraction results)
  - knowledge_graph.csv (tabular format)
  - knowledge_graph.html (interactive visualization)
  - novel_predicates.json (new predicates discovered)
  - run.sh (experiment execution script)

**Total Size:** ~1.7M lines of JSON data

**Recommendation:** ❌ DO NOT merge to dev - keep in kg branch for research reference

### B. Loan Data

**Location:** `loans/` directory

**Contents:**
- PDF loan files for 25+ loans
- Extracted markdown from Document Intelligence
- File sizes: 10KB - 5MB per loan

**Recommendation:** ❌ DO NOT merge to dev - keep in kg branch or separate data store

---

## 5. Test Coverage

### New Tests in kg Branch:

**Files:**
- `tests/test_knowledge_graph.py` (1,058 lines) - KG store, extraction, serialization
- `tests/test_kg_ontology.py` (159 lines) - Ontology normalization
- `tests/test_kg_compaction.py` (653 lines) - Deduplication, merging
- `tests/test_kg_tools.py` (642 lines) - OpenAI Agents tool wrappers
- `tests/test_run_config.py` (292 lines) - Run configuration
- `tests/test_jtbd_models.py` (26 lines) - JTBD model updates
- `tests/test_settings.py` (31 lines) - Settings updates
- `tests/test_agent_utils.py` (14 lines) - Agent utilities

**Total:** 2,875 lines of new tests (54 tests in test_knowledge_graph.py alone)

**Recommendation:** ✅ Merge relevant tests when merging corresponding features to dev

---

## 6. Dependency & Version Changes

### pyproject.toml Changes:
- JAPES version updated (points to dev branch with v1.1.3)
- OpenTelemetry packages (if added)
- Model cost tracking libraries (if any)

### poetry.lock Changes:
- Dependency version updates
- New transitive dependencies

**Recommendation:** Review and merge dependency updates to dev

---

## 7. Recommendations for MACER dev Branch

### Ready to Merge to dev:

1. **✅ KG Infrastructure (Completed - v1.1.3)**
   - Already merged: JAPES migration commits
   - Files: macer_kg_store.py, models/knowledge_graph.py, all import updates
   - Tests: test_knowledge_graph.py (54 tests passing)

2. **✅ Document Chunking (Completed - v1.1.4, May 23, 2026)**
   - **MIGRATED TO JAPES:** `jazzx_sdk.document.chunking`
   - MACER wrapper: 236 → 101 lines (-57%)
   - All existing MACER imports continue to work (full backward compatibility)
   - Benefit: Cross-domain reusability (AML, compliance, k9)
   - JAPES: commit 24bed5f (+817 lines: module + tests + docs)
   - MACER: commit 193c85e (-135 lines: delegates to JAPES)

3. **🟡 KG Ontology System (Review First)**
   - Files: kg_ontology.py, ontologies/*.yaml, kg_extraction_agent.py
   - Tests: test_kg_ontology.py, test_kg_compaction.py
   - **Decision needed:** Is predicate normalization ready for production or still research?

3. **🟡 KG Tools (Review First)**
   - File: tools/knowledge_graph.py (OpenAI Agents wrappers)
   - Tests: test_kg_tools.py
   - **Decision needed:** Are these needed for production JTBDs or just experiments?

4. **🟡 Run Config System (Optional)**
   - Files: models/run_config.py, utils/run.py
   - Tests: test_run_config.py
   - **Decision needed:** Keep in research branch or promote to production?

5. **❌ Experimental Data**
   - experiments/, loans/ directories
   - **Action:** Keep in kg branch indefinitely - do not merge

6. **❌ Streamlit Dashboard**
   - streamlit_app/ directory
   - **Action:** Keep in kg branch - research tool, not production

7. **❌ Analysis Scripts**
   - scripts/analyze_*, scripts/compare_*
   - **Action:** Keep in kg branch - research infrastructure

### Suggested Merge Strategy:

#### Option A: Conservative (Recommended)
1. Keep kg branch as-is for ongoing research
2. Cherry-pick production-ready features to dev as needed
3. Already completed: JAPES migration (v1.1.3)

#### Option B: Aggressive
1. Merge all KG infrastructure to dev (ontology, extraction, tools)
2. Exclude experimental data (experiments/, loans/)
3. Exclude research tools (streamlit_app/, analysis scripts)
4. Risk: May bring in untested experimental code

#### Option C: Branch Reorganization
1. Create new branch: `research` for experiments/dashboard
2. Merge production-ready KG features to dev
3. Keep kg branch for ongoing work
4. Periodically sync research findings back to dev

---

## 8. JAPES Platform Considerations

### Should Any kg Features Go to JAPES?

**Already in JAPES v1.1.3:**
- ✅ BaseKGStore, InMemoryKGStore, KnowledgeHubKGStore
- ✅ Triple model with chunk_label
- ✅ Serialization (to_json, from_json)
- ✅ Source migration validator

**Already in JAPES v1.1.4 (May 23, 2026):**
- ✅ **Document chunking framework** (`jazzx_sdk.document.chunking`)
  - Config-driven YAML rules with pattern matching
  - Section-based splitting with regex patterns
  - Size-based merging and mode-based rule disabling
  - Auto-chunking for large documents in relaxed mode
  - **Migrated from:** MACER kg_chunking.py
  - **Test coverage:** 13 tests, all passing
  - **Documentation:** CHANGELOG.md, ARCHITECTURE.md, README.md
  - **Benefits:**
    - MACER: -135 lines (-57%), leverages platform code
    - k9: Can now chunk large regulatory documents
    - Future packs: AML transaction reports, compliance filings
  - **Commits:** JAPES 24bed5f, MACER 193c85e

**Could Be Generalized for JAPES v1.2.0:**
- **🟡 Ontology normalization framework** (make it domain-agnostic)
  - Current: Mortgage-specific predicates in kg_ontology.py
  - Generalized: Load any domain ontology from YAML
  - Benefit: Other domain packs could use same pattern

- **🟡 Base KG compaction** (extract universal operations)
  - Current: kg_compaction.py mixes universal and mortgage logic
  - Generalized: Base class with hooks for entity normalization
  - Universal: confidence filtering, low-value removal, dedup
  - Benefit: Domain packs extend for their entity types

- **❌ KG extraction pipeline** (too domain-specific)
  - Keep in MACER - mortgage loan document extraction logic

**Recommendation:** Consider generalizing ontology normalization for v1.2.0

---

## 9. Statistics Summary

### Code Volume:
- **Source files changed:** 19 files in src/macer/
- **New source code:** ~4,000 lines (excluding tests)
- **New tests:** ~2,900 lines
- **Total files changed:** 472 files (mostly experimental data)

### Commits:
- **Total commits in kg not in dev:** 1,251
- **Production-worthy commits:** ~50 (KG infrastructure, settings, telemetry)
- **Experimental commits:** ~1,200 (loan processing, experiments, analysis)

### Test Coverage:
- **New test files:** 8 files
- **Total new tests:** ~100+ test cases
- **All tests passing:** ✅ 54 tests in test_knowledge_graph.py

---

## 10. Action Items

### For MACER Team:

1. **✅ COMPLETED:** Migrate KG store to JAPES v1.1.3
2. **✅ COMPLETED:** Migrate document chunking to JAPES v1.1.4 (May 23, 2026)
3. **TODO:** Review and merge KG ontology system to dev (if production-ready)
4. **TODO:** Review and merge KG tools to dev (if needed for production)
5. **TODO:** Decide on run config system (research vs production)
6. **TODO:** Keep kg branch for ongoing research (do not merge experimental data)

### For JAPES Platform:

1. **✅ COMPLETED:** Document chunking framework (v1.1.4, May 23, 2026)
2. **CONSIDER:** Generalize ontology normalization framework (v1.2.0)
3. **CONSIDER:** Extract base KG compaction class (v1.2.0)
4. **MONITOR:** OpenTelemetry integration progress in MACER

### For k9 (Ontology Generator):

1. **AVAILABLE:** Can now use JAPES document chunking for regulatory documents
2. **CONSIDER:** Integrate chunking into document_processor.py
3. **BENEFIT:** Process large documents more efficiently for ontology extraction

---

---

## Appendix: Migration History

### Document Chunking Migration (May 23, 2026)

**Status:** ✅ COMPLETED

**What Was Migrated:**
- `src/macer/jtbd/kg_chunking.py` (236 lines) → `jazzx_sdk.document.chunking` (375 lines)
- MACER wrapper reduced to 101 lines (-57%)

**Implementation:**
- **DocumentChunker** class with YAML-driven config
- **ChunkingConfig/ChunkingRule** dataclasses
- Pattern matching (fnmatch wildcards)
- Section splitting (regex patterns)
- Skip patterns for unwanted sections
- Size-based merging (max_chunk_kb)
- Mode-based rule disabling (tight/medium/relaxed)
- Auto-chunking for large docs

**Test Coverage:**
- 13 comprehensive tests in JAPES
- All tests passing

**Documentation:**
- CHANGELOG.md: v1.1.4 entry with full description
- ARCHITECTURE.md: Document Processing section
- README.md: Version updated to 1.1.4

**Backward Compatibility:**
- ✅ All MACER imports continue to work
- ✅ Settings integration preserved
- ✅ MACER-specific config loading maintained

**Benefits:**
- **MACER:** -135 lines maintenance burden, uses platform code
- **JAPES:** +753 lines reusable infrastructure (module + tests + docs)
- **k9:** Can now chunk large regulatory documents
- **Future packs:** AML, compliance domains benefit

**Commits:**
- **JAPES dev:** `24bed5f` - Add document chunking framework v1.1.4
- **MACER kg:** `193c85e` - Migrate to JAPES document chunking framework

**Next Candidates for Generalization:**
1. Ontology normalization framework (kg_ontology.py)
2. Base KG compaction class (kg_compaction.py)

---

**Report Generated:** May 23, 2026
**Last Updated:** May 23, 2026 (Added document chunking migration appendix)
**Prepared By:** Analysis of MACER kg branch (commit c268292) vs dev branch

**Note:** This is a planning document for internal reference only. Not committed to git.
See `.gitignore` pattern: `plan_*.md`
