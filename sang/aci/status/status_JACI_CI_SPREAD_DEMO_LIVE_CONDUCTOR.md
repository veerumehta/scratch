# JACI CI Spread Demo - Live Conductor End-to-End
# Plan for Claude Code Execution
# Author: Virendra Mehta
# Date: 2026-06-10 12:55 AM PT

## Objective

Wire the "Run conductor" button in Tab 5 to execute `CIConductor.run_analysis()`
with the YETI golden case and `use_mocks=True`, then render the live `CaseFile`
result - hypotheses, evidence chain, policy gate results, `CreditRecommendation`,
`CanonicalTrace` - replacing all fixture-driven content with live conductor output.

After this plan executes, the full CI spread analysis loop runs in the UI on
button click, using no hardcoded content and no LLM calls (mock tools only
unless the OpenAI key is present for the full agent flow).

## Prerequisite

`JACI_CI_SPREAD_DEMO_DEHARDCODE.md` must be complete and passing. This plan
builds on that state.

## What This Does NOT Change

- Tabs 1-4 (Spread, BBC, Covenants, Jazz) - not touched
- `conductor.py`, schemas, policies, tools/registry - not touched
- `yeti_abl.json`, `yeti_financials.json` - not touched
- `dashboard.py` - not touched
- JAPES SDK - not touched

## Files Changed

| File | Change |
|------|--------|
| `src/jaci/scenarios/ci_spread/ui/demo_page.py` | Wire run button; add `_run_conductor_cached()`; rewrite Tab 5 to render live `CaseFile` |
| `src/jaci/scenarios/ci_spread/ui/__init__.py` | No change |

## Architecture

```
Button click
  -> st.session_state["ci_case_file"] = None (invalidate cache)
  -> _run_conductor_cached(golden_case) is called
      -> builds LoanApplication from _golden["loan_application"]
      -> CIConductor(use_mocks=True, ground_truth=_golden["expected_decision"])
      -> asyncio.run(conductor.run_analysis(application))
      -> returns CaseFile
  -> st.session_state["ci_case_file"] = case_file
  -> st.rerun()

Tab 5 render:
  if "ci_case_file" in st.session_state and st.session_state["ci_case_file"]:
      _render_live_trace(case_file, _golden, fd)
  else:
      _render_fixture_trace(_golden, fd)   # existing fixture path
```

The fixture path remains as the default so the tab is never blank on first load.

## Per-File Change Table

### `demo_page.py`

| Location | Change |
|----------|--------|
| Imports | Add `asyncio`, `LoanApplication`, `LoanType`, `LoanPurpose`, `CIConductor` |
| New function `_run_conductor_cached()` | Builds `LoanApplication` from golden fixture, runs conductor with mocks |
| New function `_render_live_trace()` | Renders `CaseFile` live content into Tab 5 expanders |
| Existing `_render_fixture_trace()` | Rename existing Tab 5 body to this function |
| Tab 5 body | Dispatch between fixture and live based on `st.session_state` |
| Run conductor button | Wire to `_run_conductor_cached()` + `st.rerun()` |

## Exact Steps

### Step 1 - Add imports at top of `demo_page.py`

```python
import asyncio
import traceback as _tb

from jaci.scenarios.ci_spread.conductor import CIConductor
from jaci.scenarios.ci_spread.schemas import (
    LoanApplication,
    LoanType,
    LoanPurpose,
    CaseFile,
)
```

### Step 2 - Add `_run_conductor_cached()`

Insert after `_load_fixtures()`:

```python
def _run_conductor_cached(golden: dict) -> "CaseFile":
    """Run CIConductor on the YETI golden case with mock tools.

    Builds LoanApplication from the golden case fixture so no hardcoded
    values exist here. Returns CaseFile.

    Raises on conductor failure - caller wraps in try/except.
    """
    app_data = golden["loan_application"]

    application = LoanApplication(
        loan_id=app_data["loan_id"],
        company=app_data["company"],
        loan_type=LoanType(app_data["loan_type"]),
        loan_purpose=LoanPurpose(app_data.get("loan_purpose", "working_capital")),
        requested_amount=app_data["requested_amount"],
        program_id=app_data.get("program_id"),
        industry=app_data.get("industry"),
        ein=app_data.get("ein"),
        state_of_incorporation=app_data.get("state_of_incorporation"),
        revenue=app_data.get("revenue"),
        ebitda=app_data.get("ebitda"),
        funded_debt=app_data.get("funded_debt"),
        cash=app_data.get("cash"),
        accounts_receivable=app_data.get("accounts_receivable"),
        inventory=app_data.get("inventory"),
        capex=app_data.get("capex"),
        operating_cash_flow=app_data.get("operating_cash_flow"),
        leverage_x=app_data.get("leverage_x"),
        existing_facility_amount=app_data.get("existing_facility_amount"),
        existing_facility_lender=app_data.get("existing_facility_lender"),
        intercreditor_required=app_data.get("intercreditor_required", False),
        financials_years_available=app_data.get("financials_years_available", 0),
        bbc_available=app_data.get("bbc_available", False),
        ar_aging_available=app_data.get("ar_aging_available", False),
    )

    conductor = CIConductor(
        ctx=None,           # HandlerContext - None triggers internal default
        ground_truth=golden.get("expected_decision"),
    )

    return asyncio.run(conductor.run_analysis(application))
```

NOTE: `CIConductor.__init__` currently requires `ctx: HandlerContext`. If it
raises on `ctx=None`, add a minimal stub:

```python
from unittest.mock import MagicMock
ctx = MagicMock()
ctx.runtime = MagicMock()
conductor = CIConductor(ctx=ctx, ground_truth=golden.get("expected_decision"))
```

Prefer the real HandlerContext if the import chain is clean. Use MagicMock only
if HandlerContext requires external services to initialize.

### Step 3 - Add `_render_live_trace()`

```python
def _render_live_trace(case_file: "CaseFile", golden: dict, fd: dict) -> None:
    """Render Tab 5 content from a live CaseFile returned by the conductor."""
    ctx = case_file.context
    rec = case_file.recommendation

    # Summary bar
    col1, col2, col3 = st.columns(3)
    col1.metric("Iterations", case_file.iterations)
    col2.metric("Loop status", ctx.loop_status.value if ctx.loop_status else "unknown")
    col3.metric(
        "Decision",
        rec.decision.value.replace("_", " ").title() if rec and rec.decision else "incomplete",
    )

    # Hypotheses
    with st.expander(
        f"INVESTIGATOR - Hypotheses ({len(ctx.hypotheses)} raised)"
    ):
        for h in ctx.hypotheses:
            c = h.content
            severity = getattr(c, "severity", "")
            icon = {"high": "🔴", "critical": "🔴", "medium": "🟡", "low": "🟢"}.get(
                severity, "⚪"
            )
            st.markdown(
                f"{icon} **{getattr(c, 'issue_type', h.hypothesis_id).value if hasattr(getattr(c, 'issue_type', None), 'value') else getattr(c, 'issue_type', '')}** "
                f"[{severity}] - {getattr(c, 'description', '')}"
            )

    # Evidence chain
    with st.expander(
        f"VERIFIER - Evidence chain ({len(ctx.evidence)} item(s))"
    ):
        for ev in ctx.evidence:
            _status = getattr(ev, "status", None)
            _status_label = _status.value if hasattr(_status, "value") else str(_status or "")
            st.markdown(f"- `{ev.evidence_type}` | status: `{_status_label}` | source: {ev.source}")

    # Policy gate
    with st.expander("GOVERNOR - Policy gate evaluation"):
        if rec:
            _lev = rec.leverage_x
            _fccr = rec.fccr_x
            if _lev is not None:
                st.markdown(f"**Leverage:** {_lev:.2f}x")
            if _fccr is not None:
                st.markdown(f"**FCCR:** {_fccr:.2f}x")
            if rec.key_concerns:
                st.markdown("**Policy concerns:**")
                for concern in rec.key_concerns:
                    st.warning(concern)
            else:
                st.success("All policy gates passed")

    # Reasoner
    with st.expander("REASONER - Credit synthesis"):
        if rec:
            if rec.decision:
                st.markdown(f"**Decision:** {rec.decision.value.replace('_', ' ').title()}")
            if rec.risk_rating:
                st.markdown(f"**Risk rating:** {rec.risk_rating.value.upper()}")
            if rec.approved_amount:
                st.markdown(f"**Approved amount:** ${rec.approved_amount:,.0f}")
            if rec.rationale:
                st.markdown(f"**Rationale:** {rec.rationale[:500]}")
            if rec.strengths:
                st.markdown("**Strengths:** " + "; ".join(rec.strengths[:3]))
            if rec.key_risks:
                st.markdown("**Key risks:** " + "; ".join(rec.key_risks[:3]))

    # Narrator
    with st.expander("NARRATOR - Credit memo output"):
        if rec and rec.conditions:
            st.markdown(f"**Conditions ({len(rec.conditions)}):**")
            for cond in rec.conditions:
                st.markdown(f"- {cond.description}")
        elif rec and rec.covenants:
            st.markdown("**Covenants:**")
            for cov in rec.covenants:
                st.markdown(f"- {cov}")

    # Evaluation report if present
    if case_file.evaluation_report:
        er = case_file.evaluation_report
        with st.expander("EVALUATOR - Ground truth grading"):
            for metric, score in (er.scores or {}).items():
                st.metric(metric, f"{score:.3f}" if isinstance(score, float) else score)

    # Raw trace for platform review
    with st.expander("CanonicalTrace metadata"):
        st.json({
            "case_id": str(ctx.context_id),
            "iterations": case_file.iterations,
            "intake_mode": case_file.intake_mode,
            "loop_status": ctx.loop_status.value if ctx.loop_status else None,
            "evidence_count": len(ctx.evidence),
            "hypothesis_count": len(ctx.hypotheses),
        })
```

### Step 4 - Wrap existing Tab 5 body as `_render_fixture_trace()`

Move the entire current Tab 5 content (post-dehardcode) into:

```python
def _render_fixture_trace(golden: dict, fd: dict) -> None:
    """Render Tab 5 from fixture files when the conductor has not run yet."""
    # ... existing fixture-driven expander content from DEHARDCODE plan ...
```

### Step 5 - Rewrite Tab 5 dispatch block

```python
with tab5:
    st.subheader("Governance trace - evidence chain")

    _case_file = st.session_state.get("ci_case_file")

    if _case_file is not None:
        st.caption("Live conductor output.")
        _render_live_trace(_case_file, _golden, fd)
    else:
        st.caption(
            "Fixture-driven trace (golden case). "
            "Click 'Run conductor' to generate a live trace."
        )
        _render_fixture_trace(_golden, fd)

    st.markdown("---")

    _run_col, _reset_col = st.columns([3, 1])

    with _run_col:
        if st.button("Run conductor (live trace)", key="ci_run_conductor"):
            with st.spinner(
                f"Running {_golden.get('name', 'CI analysis')} with mock tools..."
            ):
                try:
                    _case_file = _run_conductor_cached(_golden)
                    st.session_state["ci_case_file"] = _case_file
                    st.rerun()
                except Exception as e:
                    st.error(f"Conductor failed: {e}")
                    st.code(_tb.format_exc(), language="text")

    with _reset_col:
        if st.button("Reset trace", key="ci_reset_trace"):
            st.session_state.pop("ci_case_file", None)
            st.rerun()
```

## HandlerContext Dependency Resolution

Check `CIConductor.__init__` signature. If `ctx` is used only for LLM calls
(passed into `InvestigatorMode`, `VerifierMode`, etc.) and those modes are
called via `asyncio.run()`, the mock path may work with `ctx=MagicMock()`.

If HandlerContext initialization is cheap (no external calls):

```python
from jazzx_sdk.handlers import HandlerContext
ctx = HandlerContext()
```

Confirm which is the case before Step 2 executes. If `HandlerContext()` raises,
fall back to MagicMock. Document the decision in a comment.

## Acceptance Checks

```bash
# 1. No hardcoded YETI strings remain
grep -n '"YETI\|Existing Bank\|0.27x\|3.2x\|3.6x\|$128.9\|$73.5' \
  src/jaci/scenarios/ci_spread/ui/demo_page.py
# Expected: 0 matches

# 2. Imports resolve
cd /Users/sangit/src/jaci
python -c "
from jaci.scenarios.ci_spread.ui.demo_page import (
    _load_fixtures, _run_conductor_cached, _render_live_trace, _render_fixture_trace
)
print('imports OK')
"

# 3. _load_fixtures() returns valid dicts
python -c "
from jaci.scenarios.ci_spread.ui.demo_page import _load_fixtures
g, f = _load_fixtures()
assert g['case_id'] == 'yeti_abl_001'
assert 'income_statement' in f
print('fixtures OK')
"

# 4. Conductor runs with mocks and returns CaseFile
python -c "
import asyncio
from jaci.scenarios.ci_spread.ui.demo_page import _load_fixtures, _run_conductor_cached
g, _ = _load_fixtures()
cf = _run_conductor_cached(g)
assert cf.loan_id == g['loan_application']['loan_id']
assert cf.recommendation is not None
assert cf.iterations >= 1
print(f'conductor OK: {cf.iterations} iterations, decision={cf.recommendation.decision}')
"

# 5. Streamlit renders without error
streamlit run app.py --server.headless true &
sleep 6 && curl -s http://localhost:8501 | grep -c "JACI" && kill %1
```

## What Changes After This Plan

The "Run conductor" button executes the full JACI loop (Investigator, Verifier,
Reasoner, PolicyExpert, Governor, Narrator) on the YETI case with mock tools.
Tab 5 shows live hypotheses, evidence, policy gate results, and recommendation.
No hardcoded content anywhere in the file.
