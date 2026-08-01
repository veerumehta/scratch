# plan_JACI_YETI_DEMO_DECK_ALIGNMENT.md

**Author:** Virendra Mehta  
**Created:** Monday, June 15, 2026 · 5:04 AM PT  
**Branch:** `dev` (all edits in `src/jaci/` and `ui/`)  
**Purpose:** Close the four gaps between what the JazzX Platform vNext deck claims the YETI demo shows and what the demo actually shows. This plan is written for Claude Code execution.

---

## Context and constraints

The deck (slides 5-7) makes four claims about the YETI demo. The demo has the plumbing but
not the visibility. This plan adds UI surface only - it does not modify the conductor,
experts, spreader, or any canonical object contracts. Every piece of logic being exposed
already runs; we are surfacing it.

Before making any changes, read the following files in full:

```
src/jaci/scenarios/ci_spread/ui/demo_page.py
src/jaci/scenarios/commercial_lending/ui/shared.py   (or wherever render_spread_analytics / render_spreading_tab live - locate via __init__.py)
src/jaci/scenarios/ci_spread/experts/policy.py
src/jaci/scenarios/ci_spread/experts/playbook.py
src/jaci/scenarios/commercial_lending/spreader.py
tests/fixtures/golden_cases/ci_spread/yeti_abl.json
docs/LoanSamples/YETI/yeti_financials.json
```

Also check:

```
src/jaci/scenarios/ci_spread/policies/registry.py   (to understand CI_REGISTRY structure)
config/packs/ci-spread-core/pack_manifest.yaml       (playbook asset_ids)
config/packs/ci-spread-core/diagnose_map.yaml        (playbook rule structure)
```

---

## What this plan does NOT change

- `conductor.py` - no changes
- `experts/policy.py`, `experts/playbook.py` - no changes
- `spreader.py`, `spread_schema.py` - no changes
- Any JAPES SDK file
- Any canonical object schema
- Any existing tab order or tab names
- The curated fixture (`yeti_financials.json`) - read-only reference

---

## Gap 1 — Three-column spread view (reported / adjustment / adjusted)

**Deck claim (slide 6):** "Produce the spread from the extracted financials: reported, adjustment, and adjusted columns."

**Current state:** The Spread tab (`tab1`) shows a single-column spread from `yeti_financials.json`. The `FinancialSpread` schema already supports three columns via the `statements` list (the `SpreadLine.values` list is period-aligned). The YETI spreader, when run via the 10-K Spreading tab, produces a `FinancialSpread` stored in `st.session_state["ci_spread_result"]`.

**What to build:**

In `demo_page.py` > `tab1` block, add a three-column reconciliation view that runs only when the live spread result is available (`st.session_state.get("ci_spread_result")`). When it is not available, keep the existing curated view unchanged.

The three-column view should show, for each income statement line that has a corresponding entry in `yeti_financials.json`:

- **Reported** - value from the `FinancialSpread` (as extracted from the 10-K, exact)
- **Adjustment** - the delta between the curated adjusted value and the reported value (read from `yeti_financials.json`); show null/`—` for lines with no adjustment
- **Adjusted** - the curated adjusted value from `yeti_financials.json`

Show this as a `st.dataframe` with columns: `Line Item | FY2025 Reported | FY2025 Adj | FY2025 Adjusted`. Keep it to FY2025 only (the year where the BBC and XBRL ground truth are pinned). Below the table add a one-line caption: "Reported = extracted from 10-K. Adjusted = analyst spread with QoE add-back."

The matching between `FinancialSpread` lines and `yeti_financials.json` keys should use the `key` field on `SpreadLine` (e.g. `net_sales`, `gross_profit`, `net_income`). Map these to the corresponding `income_statement` list keys in `yeti_financials.json`. If a key is not present in both, skip it silently.

Note on the FY2022 QoE add-back: the `yeti_financials.json` already has the add-back baked in. The `qoe_notes.one_time_items` list in the fixture has the recall amount and period. Surface it as a `st.warning` below the table with the exact period, amount, and description from `_recall` (already computed at the top of the tab block).

**Acceptance check:**

```bash
# After running the 10-K Spreading tab, Spread tab should show three-column table.
# Without running it, the existing curated view should be unchanged.
```

---

## Gap 2 — PolicyExpert source citations visible in the fixture path

**Deck claim (slide 7):** "It advises rather than blocks, and every answer points back to its source."

**Current state:** `CIPolicyExpert.check_compliance()` returns a `ComplianceResult` with `rationale` and `applied_policies` (rule IDs). This runs in the conductor but is only visible when "Run conductor" is clicked, buried in the Governor/Reasoner expander. In the fixture path (no conductor run) the Covenants tab shows a scorecard derived from the curated fixture.

**What to build:**

Step 1 - Read the policy registry to understand the source attribution available.
In `src/jaci/scenarios/ci_spread/policies/registry.py`, check what metadata exists on `Policy` and `Rule` objects - specifically whether there is a `source` field, `regulation_ref`, or similar. Also check `docs/POLICY_REGULATORY_SOURCES.md` for the source documents referenced.

Step 2 - Add a "Policy sources" expander to the Covenants tab (`tab3`) in `demo_page.py`, placed below the scorecard dataframe. This expander should be fixture-driven (always visible, no conductor run needed).

Content of the expander: a table with columns `Policy | Rule | Source document | Threshold`. Populate it from the policies directly - call `covenant_policy("ci")` (already imported) and iterate `policy.rules`. For each rule that has a `condition`, extract `rule_id`, the policy `name`, the condition field + value, and whatever source reference is available on the rule or policy object (check for `source`, `regulation_ref`, `citation`, or similar fields - use what exists, do not invent fields).

If source attribution fields are absent on the Rule objects (they may not exist yet), fall back to a static mapping dict at the top of the expander: 

```python
_POLICY_SOURCES = {
    "CI_CORE_LEVERAGE_POLICY": "OCC Comptroller's Handbook: Commercial Loans",
    "CI_CORE_FCCR_POLICY": "OCC Comptroller's Handbook: Commercial Loans",
    "CI_CORE_ABL_POLICY": "FDIC Risk Management Manual of Examination Policies",
    "CI_CORE_LIEN_POLICY": "FDIC Risk Management Manual of Examination Policies",
}
```

Read the actual policy IDs from `CI_CORE_POLICY_IDS` in the registry rather than hardcoding them. The dict above is only for the source label fallback.

Add a caption below the table: "PolicyExpert is advisory - advises on compliance, never blocks. Binding enforcement is the Governor's job."

**Acceptance check:**

```bash
# Covenants tab should show policy source table without any conductor run.
# table should have at least 4 rows (the 4 core C&I policies).
```

---

## Gap 3 — Accuracy scorecard visible in the fixture path

**Deck claim (slide 6, Phase 4):** "Grade the spread against the analyst's YETI Credit Package and generate an accuracy scorecard."

**Current state:** The Overview tab has a static hardcoded comparison table (`st.dataframe` with fixed strings). The `EvaluationReport` is generated by the conductor when ground truth is present but is shown in a collapsed expander only after "Run conductor".

**What to build:**

Step 1 - Promote the comparison table on the Overview tab. The existing static table ("Our pipeline vs Curated package") is the right framing but needs to be clearly labeled as an **accuracy scorecard**, not just a comparison. Change the section header from "Our automated outcome vs. the curated loan package" to "Accuracy scorecard - YETI $20M ABL". Add a subtitle: "Graded against the analyst's spread (YETI Credit Package, SEC EDGAR)."

Step 2 - Make the scorecard partially live. The `yeti_financials.json` fixture has the exact values we extracted; the `validate_spread` function (in `spreader.py`) takes a `FinancialSpread` and a `truth` dict and returns per-check results. When `st.session_state.get("ci_spread_result")` is set (live spread run), replace the static table with the output of `validate_spread`. When it is not set, keep the static table.

For the live path: call `validate_spread` with the `FinancialSpread` from session state and the `_yeti_truth` dict already defined in `demo_page.py` (it is passed to `render_spreading_tab`). Show results as a dataframe with columns: `Line | Period | Extracted | Ground Truth | Match | Delta`. Color `Match` column green/red using `st.dataframe` column config (use `column_config.CheckboxColumn` or just show "✅"/"❌").

Step 3 - In the live Trace tab (when conductor has run), promote the `EvaluationReport` expander: change it from collapsed to `expanded=True` and move it to the top of the live trace section (before the Investigator hypotheses expander).

**Acceptance check:**

```bash
# Overview tab: scorecard section header updated.
# After 10-K Spreading run: live validation results replace static table.
# After conductor run: EvaluationReport expander is expanded and at top.
```

---

## Gap 4 — KG / entity view and Playbook Expert in the fixture path

**Deck claim (slide 6, Phase 1):** "Build the commercial lending ontology and schema." Slide 7: "Dynamic ontology and schema - generated and kept current as documents arrive."

**Deck claim (slide 7):** Playbook Expert is one of the "three key areas to focus on for this demo."

**Current state for KG:** Phase 1 entity extraction runs in the conductor (`_run_entity_extraction`) and writes KG triples via `fabric.graph`. Nothing surfaces this in the UI except a brief mention in the Overview tab expander.

**Current state for Playbook:** `CIPlaybookExpert.recommend()` runs in the conductor and the Trace tab has a "PLAYBOOK" expander - but only after "Run conductor". The fixture trace path (`_render_fixture_trace`) has no playbook section.

**What to build - KG view:**

Add a "🕸 KG / Entities" expander to the Overview tab, placed after the "How some pack assets are crafted" section. This is a fixture-driven view (no conductor run needed).

Content: show the YETI deal's entity graph as a static representation derived from the golden case fixture (`yeti_abl.json`). Parse the `loan_application` object and build a simple entity list:

- Borrower entity: `company`, `ein`, `state_of_incorporation`
- Facility entity: `loan_id`, `loan_type`, `requested_amount`
- Lien entity: `existing_facility_lender`, `existing_facility_amount`, `intercreditor_required`

Show these as a `st.dataframe` with columns: `Entity Type | Entity Name | Key Attributes`. This is a simplified but honest representation - label it explicitly: "Entity extraction snapshot — YETI deal. In production, the conductor writes these as KG triples to `fabric.graph` during Phase 1."

Then add a note that the live conductor run (Trace tab) writes the actual triples and a link/pointer: "See the 🔗 Trace tab > Entity extraction to see Phase 1 run live."

Do NOT attempt to render a graph visualization. A simple table is correct for a demo environment.

**What to build - Playbook Expert in fixture path:**

In `_render_fixture_trace()` (the fixture-path trace renderer), add a "PLAYBOOK EXPERT" expander analogous to the INVESTIGATOR / VERIFIER / GOVERNOR expanders that already exist there.

Content of this expander:

- Load `config/packs/ci-spread-core/diagnose_map.yaml` and `pack_manifest.yaml` directly (same way `CIPlaybookExpert.__init__` does it - check the path resolution in `playbook.py`).
- Compute a fixture-based diagnosis: build a mock context from the golden case (`loan_application.loan_type`, `expected_decision.required_issue_types` as `risk_flags`, `expected_decision.expected_leverage_x` as `leverage_x`) and run through the diagnose rule matching logic inline (it is pure Python, no LLM, no async - you can replicate the rule walk from `CIPlaybookExpert.diagnose()` as a synchronous helper in the fixture renderer).
- Show: matched playbook ID, confidence, and a table of `guidance_refs` (asset_id, section_id, title).
- Caption: "PlaybookExpert — config-driven (diagnose_map.yaml). Matches the case to the right procedure and emits guidance_refs. No LLM call needed for this step."

**Acceptance check:**

```bash
# Overview tab: KG/Entities expander visible without conductor run.
# Trace tab fixture path: PLAYBOOK EXPERT expander visible without conductor run.
# guidance_refs table should show at least 2 rows from the playbook markdown sections.
```

---

## File change summary

| File | Change type | Description |
|------|-------------|-------------|
| `src/jaci/scenarios/ci_spread/ui/demo_page.py` | Edit | Gaps 1, 2, 3, 4 - all UI changes land here |
| `src/jaci/scenarios/commercial_lending/ui/shared.py` | Read-only | Check `render_spread_analytics` signature before editing demo_page |

No other files should need changes. All logic already exists - this plan only adds UI surface.

---

## Execution order

Do these in order. Each gap is independent and self-contained; if one hits an
unexpected blocker, note it and continue to the next.

1. Gap 2 (Policy sources) - smallest, lowest risk, no session state dependency
2. Gap 4 Playbook fixture path - pure Python, no new imports
3. Gap 4 KG view - pure fixture parsing, no new imports
4. Gap 3 Scorecard header + live path - introduces `validate_spread` call
5. Gap 1 Three-column spread - most complex, depends on live spread session state

After each gap: verify the demo loads without error (`streamlit run app.py`, select "C&I Spread"
scenario) before moving to the next.

---

## Known risks and where to look

**`shared.py` location:** The `__init__.py` for `commercial_lending.ui` re-exports from
`shared.py` but the actual file location was not directly readable. Locate it via:

```bash
python -c "import jaci.scenarios.commercial_lending.ui.shared as m; print(m.__file__)"
```

or grep the jaci src tree. Do not modify it - only read it to understand `render_spread_analytics`'s
signature and what it expects in `ci_spread_result`.

**`validate_spread` async:** `validate_spread` in `spreader.py` is synchronous (no async). Safe
to call directly from Streamlit without `asyncio.run()`.

**`CIPlaybookExpert.diagnose` is async:** For the fixture path in `_render_fixture_trace`, do
not call the expert directly (it requires an event loop). Instead replicate the rule-walk logic
inline as a synchronous function - the logic is ~15 lines from `playbook.py`. This is
intentional: the fixture path must work without any LLM or async machinery.

**Policy registry access:** `CI_REGISTRY` is the policy registry. Import it in `demo_page.py`
as: `from jaci.scenarios.ci_spread.policies.registry import CI_REGISTRY, CI_CORE_POLICY_IDS`.
Check whether `Policy` objects expose a `source` or `citation` field before using it; fall back
to the `_POLICY_SOURCES` dict defined in Gap 2 if not.

**`yeti_abl.json` path:** Already resolved in `_load_fixtures()` as
`base / "tests/fixtures/golden_cases/ci_spread/yeti_abl.json"`. Use the same base path
pattern for the KG entity view.
