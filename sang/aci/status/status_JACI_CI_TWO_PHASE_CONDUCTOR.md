# plan_JACI_CI_TWO_PHASE_CONDUCTOR.md

**Author:** Virendra Mehta  
**Created:** Monday, June 15, 2026 · 7:13 AM PT  
**Files changed:**
- `src/jaci/scenarios/ci_spread/conductor.py` — add `CI_SPREAD_PIPELINE`, `run_spread` method
- `src/jaci/scenarios/ci_spread/ui/demo_page.py` — Trace tab: two-phase UI, honest wording
- `docs/DEMO_SCRIPT_CI_SPREAD.md` — update Trace tab section

---

## Context and constraints

Read these files in full before writing any code:

```
src/jaci/scenarios/ci_spread/conductor.py
src/jaci/scenarios/ci_spread/ui/demo_page.py   (Trace tab section, tab5)
docs/DEMO_SCRIPT_CI_SPREAD.md
```

**The core facts to keep in mind throughout:**

The spread pipeline (`spread_financials()` in `commercial_lending/spreader.py`) and the
conductor loop (`run_analysis()`) are currently disconnected. The conductor never calls
`spread_financials()`. The spreading tab (tab6) stores a `FinancialSpread` in
`st.session_state["ci_spread_result"]`; the conductor loop (tab5) stores a `CaseFile` in
`st.session_state["ci_case_result"]`. They share no data at runtime.

The conductor's investigation loop uses mock tool registry evidence, not the spread. The
PolicyExpert evaluates ratios from `CreditRecommendation` fields, not from the spread.
The PlaybookExpert runs a deterministic YAML rule walk - no LLM, no spread input.

This plan does NOT wire the spreading output into the conductor loop. That connection is
future work. This plan only splits the pipeline diagram and the demo UI to be honest about
what "Phase 1: Spread" actually does vs. what "Phase 2: Credit Analysis" does.

---

## Part 1 — New `CI_SPREAD_PIPELINE` in `conductor.py`

Add a second `ConductorPipeline` object below `CI_PIPELINE`. Do not modify `CI_PIPELINE`.

```python
CI_SPREAD_PIPELINE = ConductorPipeline(
    pack_id="ci-spread-core",
    name="C&I Spread Phase — Financial Spreading",
    steps=[
        PipelineStep(
            id="document_intake",
            label="Document intake",
            component="Intake pipeline + DocIntel",
            emits="Evidence · DATA_GAP hypotheses",
            execution=_INT,
            note="Azure Document Intelligence (stubbed locally)",
            phase="Intake",
        ),
        PipelineStep(
            id="entity_extraction",
            label="Entity extraction + KG",
            component="Extraction pipeline",
            emits="KG triples (fabric.graph)",
            execution=_LIVE,
            phase="Intake",
        ),
        PipelineStep(
            id="spread_financials",
            label="Financial spreading",
            component="spread_financials() + analytics",
            emits="FinancialSpread · CreditMetrics · WorkingCapitalMetrics",
            execution=_LIVE,
            note="LLM extracts as-reported lines; platform computes all derived metrics",
            phase="Spread",
        ),
        PipelineStep(
            id="validate_spread",
            label="Validate spread",
            component="validate_spread() — deterministic",
            emits="Reconciliation report (vs. SEC XBRL)",
            execution=_DET,
            phase="Spread",
        ),
        PipelineStep(
            id="persist_spread",
            label="Persist spread",
            component="fabric.canonical",
            emits="FinancialSpread · CanonicalTrace",
            execution=_INT,
            note="Knowledge Hub",
            phase="Record",
        ),
    ],
    loops=[],
)
```

Add to `__all__`:

```python
__all__ = ["CIConductor", "ci_spread_conductor", "CI_PIPELINE", "CI_SPREAD_PIPELINE"]
```

---

## Part 2 — `run_spread` method on `CIConductor`

Add a new `async def run_spread(...)` method to `CIConductor`, between `_run_entity_extraction`
and `_build_case_context`. This method runs only the spread phase steps.

```python
async def run_spread(
    self,
    application: LoanApplication,
    document_paths: list[str] | None = None,
    fabric=None,
) -> dict:
    """Run the spread phase only: document intake → entity extraction → spread → validate.

    Returns a dict with keys:
        spread:        FinancialSpread | None
        checks:        list[dict]  (validate_spread results)
        entities:      dict | None  (extracted entities from Phase 1)
        intake_mode:   str
        fabric_mode:   str

    Does NOT run the investigation loop, Reasoner, Governor, Narrator, or any
    decision-making steps. Those belong to run_analysis() (Phase 2).

    The spread is produced by spread_financials() in the spreading pipeline —
    the same function the 10-K Spreading tab calls. This method wires it into
    the conductor context so the spread is available as evidence for a subsequent
    run_analysis() call on the same application.
    """
    self._run_fabric = fabric
    if fabric is not None and getattr(self.tool_registry, "fabric", None) is None:
        self.tool_registry.fabric = fabric

    ctx = CIContext(
        input=application,
        context_id=f"ci_spread_{application.loan_id}_{int(datetime.utcnow().timestamp())}",
        loop_status=LoopStatus.ACTIVE,
    )

    # Phase 0: document intake
    try:
        await self._run_document_intake(ctx, document_paths, structured_data=None)
    except Exception as e:  # noqa: BLE001
        logger.warning("Spread phase 0 failed (non-blocking): %s", e)

    # Phase 1: entity extraction + KG
    entities = None
    try:
        entities = await self._run_entity_extraction(ctx)
    except Exception as e:  # noqa: BLE001
        logger.warning("Spread phase 1 failed (non-blocking): %s", e)

    # Phase 2: financial spreading (the spreading pipeline, not the conductor loop)
    spread = None
    checks = []
    if document_paths:
        try:
            from jaci.scenarios.commercial_lending import spread_filings
            from jaci.scenarios.commercial_lending.spreader import validate_spread
            from jaci.scenarios.commercial_lending.spread_schema import StatementType as ST

            spread = await spread_filings(
                document_paths,
                company=application.company,
                segment="ci",
            )

            # Validate against SEC XBRL ground truth where available.
            # The truth dict is sparse — only pin the lines we have XBRL data for.
            _truth = {}  # populated by caller if ground truth is available
            if _truth:
                checks = validate_spread(spread, _truth)
            logger.info(
                "Spread phase complete: %d statements × %d periods",
                len(spread.statements), len(spread.periods),
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Spread phase 2 failed (non-blocking): %s", e)

    # Persist FinancialSpread to fabric.canonical (best-effort)
    fabric_mode = "none"
    if spread is not None and fabric is not None:
        try:
            canonical = self._resolve_fabric().canonical
            _ont = self.pack_id or "ci-spread-core"
            trace = CanonicalTrace.for_pack(
                workflow_id="ci-spread-phase",
                case_id=str(ctx.context_id),
                pack_id=_ont,
                pack_version="0.1.0-draft",
                metadata={"loan_id": application.loan_id, "phase": "spread"},
                domain_extensions={
                    "periods": spread.periods,
                    "statement_count": len(spread.statements),
                    "source": spread.source or "",
                },
            )
            await canonical.put_trace(trace, ontology_id=_ont)
            fabric_mode = type(fabric).__name__
        except Exception as e:  # noqa: BLE001
            logger.debug("Spread phase persist failed (non-blocking): %s", e)

    return {
        "spread": spread,
        "checks": checks,
        "entities": entities,
        "intake_mode": "documents" if document_paths else "tools",
        "fabric_mode": fabric_mode,
        "context_id": str(ctx.context_id),
    }
```

**Note on ground truth:** The `_truth` dict in `run_spread` is left empty. The caller
(demo UI) passes `_YETI_TRUTH` directly to `validate_spread` after calling `run_spread`.
Do not try to pass it through `run_spread` — it is YETI-specific and has no place in
the conductor method signature.

---

## Part 3 — Trace tab (`tab5`) in `demo_page.py`

### 3a — New imports at top of `demo_page.py`

```python
from jaci.scenarios.ci_spread.conductor import CI_PIPELINE, CI_SPREAD_PIPELINE
```

(Replace the existing import of `CI_PIPELINE` from `conductor` wherever it appears.)

### 3b — Replace the pipeline map section in tab5

Currently `tab5` calls `render_pipeline_map()` which renders `CI_PIPELINE` (the full
13-step pipeline). Replace this with a two-phase view.

After `st.subheader("Conductor process — canonical-object trace")`, replace
`render_pipeline_map()` with:

```python
st.markdown(
    "The full C&I workflow has two phases. **Phase 1** is what this demo runs: "
    "document intake, entity extraction, and financial spreading. **Phase 2** — "
    "the credit analysis loop — takes the spread as input and produces a credit "
    "decision. Both phases are implemented and runnable; Phase 2 is shown as "
    "'next' here because the demo scope is spreading."
)

_phase_tab_a, _phase_tab_b = st.tabs(
    ["📄 Phase 1: Spread (this demo)", "🔒 Phase 2: Credit analysis (next)"]
)

with _phase_tab_a:
    st.caption(
        "What runs when you click **Run spread phase** below. "
        "Document intake → entity extraction → financial spreading → validate. "
        "Output: `FinancialSpread` + KG triples + `CanonicalTrace`. "
        "No investigation loop, no policy gates, no credit decision."
    )
    from ui.concepts_view import _conductor_graph   # or whatever the import is
    _conductor_graph(CI_SPREAD_PIPELINE)

with _phase_tab_b:
    st.caption(
        "The credit analysis loop — Investigator, Verifier, Sentinel, "
        "Reasoner, PolicyExpert, Governor, Narrator. Takes the spread produced "
        "in Phase 1 as its financial evidence input. Produces a `CreditRecommendation` "
        "gated by policy and persisted as a `CanonicalCaseFile`. "
        "**Policy and playbook assets are the Phase 2 story** — the PolicyExpert "
        "checks spread-derived ratios against canonical Policy objects; the "
        "PlaybookExpert matches the deal profile to a procedure. "
        "These assets exist and are wired; Phase 2 is the next demo milestone."
    )
    _conductor_graph(CI_PIPELINE)
```

**Locate `_conductor_graph`:** It is currently imported in `_render_run_conductor` as
`from ui.concepts_view import _conductor_graph`. Move that import to module level or
repeat it in the tab5 block — whichever is consistent with the rest of the file.

### 3c — Replace the two run buttons at the bottom of tab5

Currently there is one button: "Run conductor (live trace)". Replace with two buttons
side by side.

```python
st.markdown("---")
_btn1, _btn2, _btn_reset = st.columns([2, 2, 1])

with _btn1:
    if st.button("▶ Run spread phase", key="ci_run_spread", type="primary"):
        _golden_app = _golden["loan_application"]
        _pdf_root = (
            Path(__file__).parents[5]
            / "docs/LoanSamples/YETI/Yeti Application Package/Yeti FInancials"
        )
        _doc_paths = [str(_pdf_root / "YETI FY 2025 SEC 10-K_1.3.2026.pdf")]
        with st.spinner("Running spread phase (DocIntel stub + spreading pipeline)..."):
            try:
                from jaci.scenarios.ci_spread.schemas import LoanApplication, LoanPurpose, LoanType
                _app = LoanApplication(
                    loan_id=_golden_app["loan_id"],
                    company=_golden_app["company"],
                    loan_type=LoanType(_golden_app["loan_type"]),
                    loan_purpose=LoanPurpose(_golden_app.get("loan_purpose", "working_capital")),
                    requested_amount=_golden_app["requested_amount"],
                )
                _artifact_dir(_golden_app["loan_id"]).mkdir(parents=True, exist_ok=True)
                _fab, _fab_mode = _run_fabric(_artifact_dir(_golden_app["loan_id"]))
                _conductor = CIConductor(ctx=_build_runtime_ctx())   # import CIConductor at top
                _spread_result = asyncio.run(
                    _conductor.run_spread(_app, document_paths=_doc_paths, fabric=_fab)
                )
                # Store in the spreading session key so the Spread tab also updates
                if _spread_result.get("spread"):
                    st.session_state["ci_spread_result"] = _spread_result["spread"]
                st.session_state["ci_spread_phase_result"] = _spread_result
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Spread phase failed: {e}")
                st.code(_tb.format_exc(), language="text")

with _btn2:
    if st.button("▶ Run credit analysis (Phase 2)", key="ci_run_conductor"):
        with st.spinner("Running full conductor (live LLM, mock tools)..."):
            try:
                st.session_state["ci_case_result"] = _run_conductor(_golden)
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Conductor failed: {e}")
                st.code(_tb.format_exc(), language="text")

with _btn_reset:
    if st.button("Reset", key="ci_reset_trace"):
        for k in ("ci_case_result", "ci_spread_phase_result"):
            st.session_state.pop(k, None)
        st.rerun()
```

### 3d — Spread phase result display

After the pipeline map (step 3b) and before the buttons (step 3c), add a spread phase
result section. Show it when `st.session_state.get("ci_spread_phase_result")` is set.

```python
_spread_phase = st.session_state.get("ci_spread_phase_result")
if _spread_phase is not None:
    _sp = _spread_phase.get("spread")
    _ents = _spread_phase.get("entities") or {}
    st.markdown("---")
    st.markdown("##### Phase 1 result — spread complete")

    _c1, _c2, _c3 = st.columns(3)
    _c1.metric("Statements", len(_sp.statements) if _sp else 0)
    _c2.metric("Periods", len(_sp.periods) if _sp else 0)
    _c3.metric("Entities extracted", len([v for v in _ents.values() if v]) if _ents else 0)

    if _sp:
        with st.expander("SPREAD — statement lines extracted", expanded=True):
            st.caption(
                "As-reported lines extracted from the 10-K. "
                "LLM extracted labels and aligned columns; platform computed all derived metrics. "
                "Periods: " + ", ".join(_sp.periods)
            )
            for stmt in _sp.statements:
                st.markdown(f"**{stmt.title}** — {len(stmt.lines)} lines")

        # Reconciliation against XBRL ground truth
        from jaci.scenarios.commercial_lending.spreader import validate_spread
        _checks = validate_spread(_sp, _YETI_TRUTH, key_statement=_yeti_truth_stmt())
        if _checks:
            _ok = sum(1 for c in _checks if c["ok"])
            with st.expander(f"VALIDATE — {_ok}/{len(_checks)} key figures match SEC XBRL"):
                st.caption(
                    "Deterministic reconciliation — no LLM. "
                    "Each extracted value checked against the filing's reported number (≤1% tolerance)."
                )
                st.dataframe(pd.DataFrame([
                    {"Line": c["key"], "Period": c["period"],
                     "Extracted": f"{c['spread']:,.0f}",
                     "SEC filing": f"{c['truth']:,.0f}",
                     "Match": "✅" if c["ok"] else "⚠"}
                    for c in _checks
                ]), width="stretch", hide_index=True)

    if _ents:
        with st.expander("ENTITY EXTRACTION — KG triples written"):
            st.caption(
                "One focused LLM call over the first four evidence items. "
                "Results written as typed triples to fabric.graph."
            )
            for k, v in _ents.items():
                if v:
                    st.markdown(f"**{k}:** {v}")

    st.info(
        "Phase 2 (credit analysis) picks up from here — the spread becomes financial "
        "evidence in the investigation loop. Click **▶ Run credit analysis** to run "
        "the full conductor loop (Investigator → Verifier → Reasoner → Governor). "
        "Policy and playbook assets are the Phase 2 story."
    )
```

The existing fixture trace (`_render_fixture_trace`) and live trace (`_render_live_trace`)
remain. Show them under the spread phase result, with their existing logic unchanged.

---

## Part 4 — Update `docs/DEMO_SCRIPT_CI_SPREAD.md`

Update the Trace tab section (Part 2e). Replace entirely with the following.

**Navigate to:** 🔗 Trace tab

```
"This is the governance trace. Two tabs — Phase 1 is what this demo runs live. 
Phase 2 is the credit analysis loop — we'll show it as the architecture and 
explain that it's the next milestone."

Point to Phase 1 tab (active):
"Phase 1: document intake, entity extraction, financial spreading. Four steps. 
The output is a FinancialSpread artifact — the standardized multi-period spread 
with every number traceable to the filing — plus knowledge graph triples for the 
deal entities."

Click "Run spread phase":

While it runs (15-30 seconds):
"This is the spreading pipeline running through the conductor. DocIntel converts 
the 10-K, the LLM extracts the statement lines verbatim, we compute all derived 
metrics deterministically."

When complete - walk the three expanders:
"Spread: three statements, six periods, every line as reported. 
Validation: key figures checked against SEC XBRL — all match. 
Entities: borrower, facility, lien — written as KG triples."

Point to Phase 2 tab:
"Phase 2 is the credit analysis loop. The spread becomes financial evidence. 
The Investigator generates hypotheses, the Verifier attests them, the Reasoner 
synthesizes a recommendation. The PolicyExpert checks the computed ratios against 
policy rules — that's where the OCC Handbook thresholds we showed on the Covenants 
tab actually execute. The Governor gates the decision.

This is implemented and runnable — you can click 'Run credit analysis' and it will 
run. We're treating Phase 2 as the next demo milestone because the spread is the 
foundation everything else rests on, and that's what we wanted to show you today."

Optional - run Phase 2 if time permits:
Click "Run credit analysis". Walk the Investigator hypotheses and Governor decision 
the same way as before.
```

Also update the **Fallbacks** section:

```
**Spread phase fails:**
The Spread tab (tab1) already has the curated column. "The spreading pipeline 
had a problem, but the comparison table shows what the output looks like — 
curated column is the analyst's reference, Spreader column is what the platform 
would produce."

**Phase 2 / conductor fails:**
Skip it. "Phase 2 is the credit analysis loop — that's the next milestone. 
What you've seen today is the foundation: the spread is correct, traceable, 
and validated. The policy and playbook assets that Phase 2 uses are already 
built — you saw the sources on the Covenants tab."
```

---

## Part 5 — Wording principles for the demo UI

These are copy changes, not code changes. Apply them to the relevant expanders and captions.

**In the Phase 2 tab description (step 3b):**

The current language about PolicyExpert and PlaybookExpert implies they run during spreading.
They don't — they run in the credit analysis loop. The Phase 2 tab caption handles this
correctly. Ensure no other text in tab5 says "PolicyExpert checks the spread" — it
checks ratios on the `CreditRecommendation`, which is produced after the spread.

**On the Covenants tab (tab3):**

The caption currently says: "the same canonical form the conductor's PolicyExpert/Governor
enforce". This is accurate but incomplete — change to: "the same canonical form the
conductor's PolicyExpert/Governor enforce **in Phase 2**". One-word addition.

**In the Overview tab expander "The Conductor and the steps it follows":**

Add a sentence at the end:
"In this demo, **Phase 1** (steps 1-2 plus financial spreading) runs live. **Phase 2**
(steps 3-10) is built and runnable — it is the next demo milestone."

---

## Acceptance checks

```bash
# 1. conductor.py imports cleanly
python -c "from jaci.scenarios.ci_spread.conductor import CI_PIPELINE, CI_SPREAD_PIPELINE; print('ok')"

# 2. run_spread is callable
python -c "
from jaci.scenarios.ci_spread.conductor import CIConductor
import inspect
sig = inspect.signature(CIConductor.run_spread)
print('run_spread params:', list(sig.parameters))
"

# 3. Demo page loads without import errors
streamlit run app.py  # select C&I Spread, navigate to Trace tab
# Phase 1 / Phase 2 sub-tabs should be visible
# "Run spread phase" button should be present and labeled correctly
# "Run credit analysis (Phase 2)" button should be present

# 4. Clicking "Run spread phase" should:
#    - populate ci_spread_phase_result in session state
#    - also populate ci_spread_result (so Spread tab updates)
#    - show three expanders: Spread, Validate, Entity Extraction

# 5. Clicking "Run credit analysis (Phase 2)" should run the existing conductor
#    unchanged and populate ci_case_result
```

---

## What NOT to change

- `run_analysis()` — unchanged in every detail
- `CI_PIPELINE` — unchanged
- The investigation loop, Reasoner, Governor, Narrator, Evaluator — unchanged
- The fixture trace (`_render_fixture_trace`) — unchanged
- The live trace (`_render_live_trace`) — unchanged, still shown after Phase 2 runs
- The 10-K Spreading tab (tab6) — unchanged
- The `spread_financials()` function — unchanged

The `run_spread` method calls `spread_filings()` which calls `spread_financials()`.
`run_spread` is a new conductor method that wraps the existing spreading pipeline
and adds the conductor's Phase 0/1 (intake + entity extraction) around it.
