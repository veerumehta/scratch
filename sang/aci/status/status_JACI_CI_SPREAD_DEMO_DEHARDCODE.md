# JACI CI Spread Demo - Remove Hardcoded Content
# Plan for Claude Code Execution
# Author: Virendra Mehta
# Date: 2026-06-10 12:55 AM PT

## Objective

Replace every hardcoded string in `demo_page.py` (Tab 5 trace expanders, metric
labels, warning text, condition lists, hypothesis types) with content read
dynamically from two authoritative sources:

1. `tests/fixtures/golden_cases/ci_spread/yeti_abl.json` - case metadata,
   expected decision, conditions, issue types, assertions
2. `docs/LoanSamples/YETI/yeti_financials.json` - all financials (already used
   in Tabs 1-3 but Tab 5 ignores it)

The conductor does NOT run yet. The UI reads fixture files and renders their
content. This is the minimum bar before the live conductor wiring.

## What This Does NOT Change

- Tabs 1, 2, 3 (Spread, Borrowing Base, Covenants) - already read from
  `yeti_financials.json`, no hardcoding there
- Tab 4 (Jazz) - live LLM call, no hardcoding
- `dashboard.py` - not touched
- The conductor itself, tools, schemas, policies - not touched
- `yeti_abl.json` or `yeti_financials.json` content - not touched

## Files Changed

| File | Change |
|------|--------|
| `src/jaci/scenarios/ci_spread/ui/demo_page.py` | Rewrite Tab 5 to be fixture-driven; extract shared loader |

## Per-File Change Table

### `demo_page.py`

| Location | Before | After |
|----------|--------|-------|
| Tab 5 `st.expander` bodies | Hardcoded strings | Read from `_golden` / `fd` |
| Investigator expander | `"Ingested yeti_financials.json..."` hardcoded | Built from `_golden["loan_application"]` fields |
| Verifier expander | BBC variance numbers hardcoded | Read from `fd["borrowing_base_indicative"]` |
| Governor expander | Leverage / liquidity numbers hardcoded | Read from `_golden["expected_decision"]` and `fd["credit_ratios"]` |
| Reasoner expander | Decision / risk rating hardcoded | Read from `_golden["expected_decision"]` |
| Narrator expander | Conditions list hardcoded | Read from `_golden["expected_decision"]["required_conditions"]` |
| Run conductor button | `st.info(...)` stub | `st.warning("Live conductor: coming in next build")` - no hardcoded prose |

## Exact Steps

### Step 1 - Add a `_load_fixtures()` helper at module top

Insert after the existing `_get_jazz_response` function:

```python
def _load_fixtures() -> tuple[dict, dict]:
    """Load golden case and financials from fixture files.

    Returns:
        (golden_case, financials) dicts. Raises FileNotFoundError with
        a clear message if either file is missing.
    """
    base = Path(__file__).parents[6]

    golden_path = (
        base / "tests/fixtures/golden_cases/ci_spread/yeti_abl.json"
    )
    fin_path = base / "docs/LoanSamples/YETI/yeti_financials.json"

    if not golden_path.exists():
        raise FileNotFoundError(f"Golden case not found: {golden_path}")
    if not fin_path.exists():
        raise FileNotFoundError(f"Financials not found: {fin_path}")

    return (
        json.loads(golden_path.read_text()),
        json.loads(fin_path.read_text()),
    )
```

### Step 2 - Replace the duplicate file-loading block in `render_demo_page()`

Currently `render_demo_page()` loads `yeti_financials.json` inline and also
has a second `_gc_path` load inside Tab 5. Replace both with a single call to
`_load_fixtures()` at the top of `render_demo_page()`:

```python
def render_demo_page(scenario: str) -> None:
    if scenario != "C&I Spread":
        ...
        return

    try:
        _golden, fd = _load_fixtures()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    # _golden: full golden case dict
    # fd: full financials dict
    # All downstream code uses _golden and fd - no second file load
```

Remove the existing:
- `DATA_PATH = Path(...) / "yeti_financials.json"` block
- `with open(DATA_PATH) as f: fd = json.load(f)` block
- `_gc_path = Path(...) / "yeti_abl.json"` block inside Tab 5
- `_golden = json.loads(_gc_path.read_text()) if _gc_path.exists() else {}`

### Step 3 - Rewrite Tab 5 expanders to read from `_golden` and `fd`

Replace the entire `with tab5:` block with the following. Every string is
derived from the fixture data - no literals except structural labels.

```python
with tab5:
    st.subheader("Governance trace - evidence chain")
    st.caption(
        "Fixture-driven trace from the YETI ABL golden case. "
        "Use 'Run conductor' to generate a live trace."
    )

    _app       = _golden.get("loan_application", {})
    _expected  = _golden.get("expected_decision", {})
    _assertions = _golden.get("test_assertions", {})
    _bbc       = fd.get("borrowing_base_indicative", {})
    _rat       = fd.get("credit_ratios", {})
    _cols      = fd.get("income_statement", {}).get("columns", [])
    _fy25_idx  = _cols.index("FY2025") if "FY2025" in _cols else -1

    # --- Investigator: document intake ---
    _doc_sources = []
    if _app.get("financials_years_available", 0) > 0:
        _doc_sources.append(
            f"{_app['financials_years_available']}-year financials "
            f"({_golden.get('source', 'fixture')})"
        )
    if _app.get("bbc_available"):
        _doc_sources.append("borrowing base certificate")
    if _app.get("ar_aging_available"):
        _doc_sources.append("A/R aging")

    _issue_types = _expected.get("required_issue_types", [])

    with st.expander(
        f"INVESTIGATOR - Document intake + hypothesis generation "
        f"({len(_issue_types)} issue type(s) identified)"
    ):
        st.markdown(
            f"**Case:** {_golden.get('name', _golden.get('case_id', ''))}"
        )
        st.markdown(
            f"**Borrower:** {_app.get('company', '')}  |  "
            f"**Facility:** ${_app.get('requested_amount', 0):,.0f} "
            f"{_app.get('loan_type', '')} revolver"
        )
        st.markdown(
            f"**Documents ingested:** {', '.join(_doc_sources) if _doc_sources else 'via mock tools'}"
        )
        if _issue_types:
            st.markdown("**Hypotheses raised:** " + ", ".join(f"`{t}`" for t in _issue_types))
        _assertions_met = [k for k, v in _assertions.items() if v is True]
        if _assertions_met:
            st.markdown(
                "**Required assertions:** "
                + ", ".join(f"`{a}`" for a in _assertions_met[:4])
            )

    # --- Investigator: spread build ---
    _recall_items = []
    for item in fd.get("income_statement", {}).get("one_time_items", []):
        if item.get("type") == "non_recurring":
            _recall_items.append(
                f"{item['period']}: {item['description']} "
                f"(${item['amount']:,.0f}K)"
            )

    with st.expander("INVESTIGATOR - Financial spread build"):
        _periods = fd.get("income_statement", {}).get("columns", [])
        st.markdown(f"**Periods spread:** {', '.join(_periods)}")
        if _fy25_idx >= 0:
            _gm_vals = fd.get("credit_ratios", {}).get("gross_margin_pct", [])
            _ebitda_m = fd.get("credit_ratios", {}).get("adj_ebitda_margin_pct", [])
            if _gm_vals:
                st.markdown(
                    f"**FY2025 gross margin:** {_gm_vals[_fy25_idx]:.1f}%  |  "
                    f"**Adj. EBITDA margin:** "
                    f"{_ebitda_m[_fy25_idx]:.1f}% (if available)"
                    if _ebitda_m else f"**FY2025 gross margin:** {_gm_vals[_fy25_idx]:.1f}%"
                )
        if _recall_items:
            for item_str in _recall_items:
                st.warning(f"One-time item flagged: {item_str}")

    # --- Verifier: BBC recomputation ---
    _stated_bbc_list = _bbc.get("application_stated_bbc") or []
    _computed_bbc_list = _bbc.get("indicative_bbc") or []
    _stated  = _stated_bbc_list[-1] if _stated_bbc_list else 0
    _computed = _computed_bbc_list[-1] if _computed_bbc_list else 0
    _variance = _stated - _computed

    with st.expander(
        f"VERIFIER - Borrowing base recomputation "
        f"(variance: ${_variance:,.0f}K)"
    ):
        st.markdown(f"**Computed BBC (conservative):** ${_computed:,.0f}K")
        st.markdown(f"**Application-stated BBC:** ${_stated:,.0f}K")
        st.markdown(f"**Variance:** ${_variance:,.0f}K")
        if _bbc.get("note"):
            st.info(_bbc["note"])
        _expected_bbc = _expected.get("expected_bbc")
        if _expected_bbc:
            st.markdown(f"**Expected BBC (golden):** ${_expected_bbc:,.0f}K")

    # --- Governor: policy gate ---
    _lev_vals = _rat.get("leverage_funded_debt_ebitda") or []
    _lev_fy25 = _lev_vals[_fy25_idx] if _lev_vals and _fy25_idx >= 0 else None
    _lev_expected = _expected.get("expected_leverage_x")
    _fccr_min = _expected.get("expected_fccr_x_min")
    _intercreditor = _app.get("intercreditor_required", False)

    with st.expander("GOVERNOR - Policy gate evaluation"):
        if _lev_fy25 is not None:
            _lev_pass = _lev_fy25 <= 3.0
            st.markdown(
                f"**Leverage:** {_lev_fy25:.2f}x vs <=3.0x policy - "
                + ("PASS" if _lev_pass else "FAIL")
            )
        elif _lev_expected is not None:
            st.markdown(f"**Leverage (expected):** {_lev_expected:.2f}x - PASS")
        if _fccr_min is not None:
            st.markdown(f"**FCCR floor:** >= {_fccr_min:.2f}x required - PASS")
        _cash_vals = fd.get("balance_sheet", {}).get("cash_and_equivalents") or []
        _cash_fy25 = _cash_vals[_fy25_idx] if _cash_vals and _fy25_idx >= 0 else None
        if _cash_fy25:
            _liq_pass = _cash_fy25 >= 25_000
            st.markdown(
                f"**Liquidity:** ${_cash_fy25/1e3:,.0f}M vs $25M floor - "
                + ("PASS" if _liq_pass else "FAIL")
            )
        if _intercreditor:
            st.error(
                "**Intercreditor / lien resolution:** OPEN - "
                "pre-closing condition required before commitment"
            )
        else:
            st.success("**Lien position:** first lien confirmed")

    # --- Reasoner: credit synthesis ---
    _decision_raw = _expected.get("decision", "")
    _decision_label = _decision_raw.replace("_", " ").title()
    _risk_rating = (_expected.get("risk_rating") or "").upper()
    _approved_amt = _expected.get("approved_amount")

    with st.expander(f"REASONER - Credit synthesis: {_decision_label}"):
        if _approved_amt:
            st.markdown(f"**Approved amount:** ${_approved_amt:,.0f}")
        if _risk_rating:
            st.markdown(f"**Risk rating:** {_risk_rating}")
        if _lev_expected is not None:
            st.markdown(f"**Leverage:** {_lev_expected:.2f}x")
        if _fccr_min is not None:
            st.markdown(f"**FCCR (minimum):** {_fccr_min:.2f}x")
        _description = _golden.get("description", "")
        if _description:
            st.markdown(f"**Case summary:** {_description}")

    # --- Narrator: credit memo ---
    _conditions = _expected.get("required_conditions") or []
    _min_cond = _expected.get("min_conditions", 0)

    with st.expander(
        f"NARRATOR - Credit memo output "
        f"({len(_conditions)} condition(s) precedent)"
    ):
        _periods = fd.get("income_statement", {}).get("columns", [])
        _has_bbc = _app.get("bbc_available", False)
        _artifacts = ["financial spread"]
        if _periods:
            _artifacts[0] += f" ({len(_periods)}-year)"
        if _has_bbc:
            _artifacts.append("borrowing base analysis")
        _artifacts.append("covenant scorecard")
        st.markdown("**Produced:** " + ", ".join(_artifacts))
        if _conditions:
            st.markdown("**Conditions precedent:**")
            for c in _conditions:
                st.markdown(f"- {c}")
        elif _min_cond:
            st.markdown(f"**Minimum conditions required:** {_min_cond}")

    # --- Run conductor stub ---
    st.markdown("---")
    if st.button("Run conductor (live trace)", key="ci_run_conductor"):
        st.warning(
            "Live conductor execution not yet wired. "
            "See plan: JACI_CI_SPREAD_DEMO_LIVE_CONDUCTOR.md"
        )
```

## Acceptance Checks

```bash
# 1. No hardcoded YETI-specific strings remain in demo_page.py
# (excluding import paths and dict keys which are structural)
grep -n '"YETI\|Existing Bank\|$73.5M\|$128.9M\|0.27x\|3.2x\|3.6x\|3.0x\|~' \
  src/jaci/scenarios/ci_spread/ui/demo_page.py
# Expected: 0 matches

# 2. Streamlit renders without error
cd /Users/sangit/src/jaci
streamlit run app.py --server.headless true &
sleep 5 && curl -s http://localhost:8501 | grep -c "JACI" && kill %1
# Expected: >= 1

# 3. fixture files exist and parse
python -c "
import json
from pathlib import Path
base = Path('.')
gc = json.loads((base / 'tests/fixtures/golden_cases/ci_spread/yeti_abl.json').read_text())
fd = json.loads((base / 'docs/LoanSamples/YETI/yeti_financials.json').read_text())
assert gc.get('case_id') == 'yeti_abl_001'
assert 'income_statement' in fd
print('fixtures OK')
"
```

## What Changes After This Plan

Nothing else changes. Tab 5 content comes from fixtures. No hardcoded prose.
The "Run conductor" button tells the user to look at the next plan doc.
