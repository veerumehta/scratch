# Plan: JACI 1.6.0 — CI Phase 2 Lite Demo

**Author:** Virendra Mehta  
**Status:** Ready for Claude Code execution  
**Scope:** UI layer only — no schema, conductor, policy, or tool registry changes

---

## Objective

Wire a live "Run credit analysis" button into `_render_ci_lite_demo` for the four
application-stage gold cases, showing the Phase 2 conductor loop (Investigator →
Reasoner → PolicyExpert → Governor) produce a real decision with policy-gate
evidence. The executive sponsor can see two runs side by side: HighLev Corp
declined on leverage (7.5x), TechFlow Manufacturing approved (2.59x).

YETI remains the spreading showcase (Phase 1). The application-stage cases become
the policy-gate showcase (Phase 2). The two stories are additive and sequential.

---

## Background

### Gold cases available

| Case ID | Company | Loan Type | Expected Decision | Key Metric |
|---|---|---|---|---|
| case_02_ace | ACE Hardware Corporation | ABL | approved | BB utilization ~68% |
| case_03_techflow | TechFlow Manufacturing | term_loan | approved | leverage 2.59x |
| case_04_overleveraged | HighLev Corp | term_loan | declined | leverage 7.5x |
| case_05_tight_availability | MidMarket Distributors | ABL | approved_with_conditions | BB utilization 77% |

### Why no spread required

`run_analysis()` accepts `structured_data: dict | None`. With this path the conductor
runs Phase 0 (document intake, skipped if no documents), Phase 1 (entity extraction,
best-effort), then enters the investigation loop. The Investigator requests evidence,
the `CIToolRegistry` fulfills via mock fallback (YETI financials for the financial
statements call — acceptable for the demo), and the Reasoner synthesizes
`CreditRecommendation` including `leverage_x` and `fccr_x` computed from the
application's own `ebitda` / `total_liabilities` / `requested_amount` fields. The
PolicyExpert then gates on those Reasoner-computed ratios. No spread or documents
required for the four application-stage cases.

### `LoanApplication` field mapping from gold case `application` dict

All fields map directly:

```
company               -> company
loan_id               -> loan_id
loan_type             -> LoanType(loan_type)   # "ABL" | "term_loan"
requested_amount      -> requested_amount
revenue               -> revenue
ebitda                -> ebitda
accounts_receivable   -> accounts_receivable
inventory             -> inventory
total_assets          -> total_assets
total_liabilities     -> total_liabilities
```

`loan_purpose` is absent from the gold case inputs; default `LoanPurpose.WORKING_CAPITAL`
is correct. `intercreditor_required` defaults to `False` for all four cases.

### Policy gate behavior expected per case

**HighLev Corp (case_04):** pro-forma leverage = (20M + 25M) / 6M = 7.5x  
Both tiers of `CI_CORE_LEVERAGE_POLICY` fire (>3.0 require_evidence, >3.5 require_approval).  
Governor blocks. Decision = DECLINED.

**TechFlow (case_03):** pro-forma leverage = (18M + 15M) / 12.75M = 2.59x  
All gates pass. Decision = APPROVED with covenants.

**ACE Hardware (case_02):** ABL, leverage not the primary gate. Borrowing base
adequate (~$379M availability vs $50M request). Decision = APPROVED.

**MidMarket (case_05):** ABL, BB = (25M × 0.85) + (35M × 0.50) = $38.75M.
$30M request = 77% utilization. Tight but within limits. Decision = APPROVED_WITH_CONDITIONS.

---

## Files changed

### 1. `src/jaci/scenarios/ci_spread/ui/demo_page.py`

Three additions:

**A. `_run_analysis_for_case(case: dict) -> CaseFile`**

Builds a `LoanApplication` from the gold case `application` dict, constructs a
`CIConductor` with the configured LLM model, calls `run_analysis` with
`structured_data=case["application"]`, returns the `CaseFile`. Uses the same
`_build_runtime_ctx()` and `_run_fabric()` helpers already in the file.

**B. `_render_phase2_result(case_file: CaseFile, case: dict) -> None`**

Renders the Phase 2 result:
- Decision badge (color-coded: green APPROVED, yellow APPROVED_WITH_CONDITIONS,
  red DECLINED)
- Key metrics row: leverage_x, fccr_x, approved_amount (columns)
- Policy gates table: rule_id, field, actual, threshold, result — derived from
  `recommendation.key_concerns` (already populated by the PolicyExpert violations
  wiring in the conductor)
- Rationale expander (full recommendation.rationale text)
- Iteration count + termination reason from `case_file.iterations`
- If `case_file.evaluation_report` present, show pass/fail score vs expected decision

**C. Button wiring in `_render_ci_lite_demo`**

In the existing function that renders the four application-stage case cards, add
below each application overview:
- "Run credit analysis" button keyed by `case_id`
- On click: spinner, call `_run_analysis_for_case`, store result in
  `st.session_state[f"phase2_result_{case_id}"]`, rerun
- If session state has a result for that case_id, call `_render_phase2_result`

No changes to the tab structure, existing YETI rendering, or any other function
in `demo_page.py`.

### 2. No other files change

- `conductor.py` — no change
- `schemas/__init__.py` — no change
- `experts/policy.py` — no change
- `tools/registry.py` — no change
- Gold case JSON files — no change

---

## Detailed code for each addition

### A. `_run_analysis_for_case`

Insert after `_run_and_read` (around line 430 of demo_page.py):

```python
def _run_analysis_for_case(case: dict) -> dict:
    """Run Phase 2 conductor loop on an application-stage gold case.

    Builds LoanApplication from case["application"], calls run_analysis with
    structured_data so Phase 0 intake seeds the context without documents.
    Returns a plain dict with keys: case_file, fabric_mode, error.
    """
    import asyncio
    from jaci.scenarios.ci_spread.conductor import CIConductor
    from jaci.scenarios.ci_spread.schemas import (
        LoanApplication, LoanType, LoanPurpose,
    )
    from jaci.scenarios.commercial_lending._llm import llm_model

    app = case["application"]
    try:
        application = LoanApplication(
            loan_id=app["loan_id"],
            company=app["company"],
            loan_type=LoanType(app["loan_type"]),
            loan_purpose=LoanPurpose.WORKING_CAPITAL,
            requested_amount=app["requested_amount"],
            revenue=app.get("revenue"),
            ebitda=app.get("ebitda"),
            accounts_receivable=app.get("accounts_receivable"),
            inventory=app.get("inventory"),
            total_assets=app.get("total_assets"),
            total_liabilities=app.get("total_liabilities"),
        )

        artifact_dir = _artifact_dir(app["loan_id"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        fabric, fabric_mode = _run_fabric(artifact_dir)

        _m = llm_model()
        conductor = CIConductor(
            ctx=_build_runtime_ctx(),
            investigator_model=_m,
            verifier_model=_m,
            reasoner_model=_m,
            governor_model=_m,
            narrator_model=_m,
            ground_truth=case.get("expected_decision"),
        )
        case_file = asyncio.run(
            conductor.run_analysis(
                application,
                structured_data=app,
                fabric=fabric,
            )
        )
        return {"case_file": case_file, "fabric_mode": fabric_mode, "error": None}
    except Exception as e:  # noqa: BLE001
        import traceback
        return {"case_file": None, "fabric_mode": "error", "error": traceback.format_exc()}
```

### B. `_render_phase2_result`

Insert immediately after `_run_analysis_for_case`:

```python
def _render_phase2_result(result: dict, case: dict) -> None:
    """Render the Phase 2 conductor result for an application-stage case."""
    if result.get("error"):
        st.error("Conductor run failed")
        st.code(result["error"], language="text")
        return

    case_file = result["case_file"]
    if case_file is None or case_file.recommendation is None:
        st.warning("No recommendation produced — check logs.")
        return

    rec = case_file.recommendation
    decision = rec.decision

    # Decision badge
    _badge = {
        "approved": ("✅ APPROVED", "success"),
        "approved_with_conditions": ("⚠️ APPROVED WITH CONDITIONS", "warning"),
        "declined": ("❌ DECLINED", "error"),
        "refer_to_committee": ("🔁 REFER TO COMMITTEE", "warning"),
    }.get(decision.value if decision else "", ("— UNKNOWN", "warning"))

    getattr(st, _badge[1])(f"**Decision: {_badge[0]}**")

    # Key metrics
    _mc1, _mc2, _mc3 = st.columns(3)
    _mc1.metric(
        "Leverage",
        f"{rec.leverage_x:.2f}x" if rec.leverage_x else "—",
        delta="policy max 3.0x" if rec.leverage_x else None,
        delta_color="off",
    )
    _mc2.metric(
        "FCCR",
        f"{rec.fccr_x:.2f}x" if rec.fccr_x else "—",
        delta="policy min 1.15x" if rec.fccr_x else None,
        delta_color="off",
    )
    _mc3.metric(
        "Approved amount",
        f"${rec.approved_amount / 1e6:.1f}M" if rec.approved_amount else "—",
    )

    # Policy gate concerns (populated by PolicyExpert violations wiring in conductor)
    if rec.key_concerns:
        with st.expander(
            f"Policy gates — {len(rec.key_concerns)} concern(s)", expanded=True
        ):
            st.caption(
                "CIPolicyExpert advisory output — forwarded to Governor for binding "
                "enforcement. Gates are deterministic threshold comparisons; no LLM."
            )
            for concern in rec.key_concerns:
                st.markdown(f"- {concern}")
    else:
        st.success("All policy gates passed.")

    # Rationale
    with st.expander("Rationale", expanded=False):
        st.markdown(rec.rationale or "_No rationale produced._")

    # Covenants
    if rec.covenants:
        with st.expander(f"Covenants ({len(rec.covenants)})", expanded=False):
            for c in rec.covenants:
                st.markdown(f"- {c}")

    # Eval score vs expected decision
    exp = case.get("expected_decision", {})
    exp_decision = exp.get("decision")
    if exp_decision and decision:
        match = decision.value == exp_decision
        st.caption(
            f"Expected: **{exp_decision.upper()}** — "
            + ("✅ matches" if match else "⚠ mismatch")
        )

    st.caption(
        f"Conductor: {case_file.iterations} iteration(s) · "
        f"intake mode: {case_file.intake_mode} · "
        f"fabric: {result['fabric_mode']}"
    )
```

### C. Button wiring in `_render_ci_lite_demo`

Locate `_render_ci_lite_demo` in `demo_page.py`. The function renders case cards
with `st.expander` per case. At the bottom of each case expander (after the existing
application overview metrics), add:

```python
# -- inside the per-case loop / expander, after existing overview --
_sess_key = f"phase2_result_{_case['case_id']}"
_existing_result = st.session_state.get(_sess_key)

if _existing_result:
    st.markdown("---")
    _render_phase2_result(_existing_result, _case)
    if st.button("Reset", key=f"reset_{_case['case_id']}"):
        st.session_state.pop(_sess_key, None)
        st.rerun()
else:
    if st.button(
        "▶ Run credit analysis",
        key=f"run_phase2_{_case['case_id']}",
        type="primary",
    ):
        with st.spinner(
            f"Running conductor on {_case['application']['company']} "
            "(Investigator → PolicyExpert → Governor)..."
        ):
            _r = _run_analysis_for_case(_case)
            st.session_state[_sess_key] = _r
            st.rerun()
```

---

## Acceptance checks

Run these manually after Claude Code applies the changes:

1. `streamlit run app.py` — app starts without import errors
2. Navigate to C&I demo, select any application-stage case (not YETI)
3. Click "Run credit analysis" — spinner appears, run completes, result renders
4. HighLev Corp: decision badge shows DECLINED, at least one policy gate concern
   containing `leverage_x` or similar
5. TechFlow: decision badge shows APPROVED, all policy gates passed message
6. Expected vs actual decision caption appears and shows "matches" for both
7. YETI Phase 1 and Phase 2 tabs unaffected — existing behavior preserved
8. Reset button clears result and re-shows the Run button

---

## What this does NOT change

- `conductor.py` — no change
- `experts/policy.py` — no change
- `tools/registry.py` — no change
- Gold case JSON files — no change
- YETI Phase 1 spreading path — no change
- YETI Phase 2 "Run credit analysis" button (existing) — no change
- Eval harness, eval registry, test fixtures — no change
- Any JAPES SDK file — no change

---

## Narrative for the demo

**Setup:** "We have four additional companies in the eval harness. Let's run two
live — a manufacturing expansion that should pass and a highly leveraged request
that should be declined. Same policy engine, same conductor, different inputs."

**TechFlow run:** 2.59x leverage, all gates pass, APPROVED. "The platform checked
FCCR, leverage, advance rates — three policy objects, deterministic gates, all
cited in the trace."

**HighLev run:** 7.5x leverage, Governor blocks, DECLINED. "Same conductor, same
policies. The PolicyExpert flagged both leverage tiers. The Governor enforced.
The rationale cites the specific rule that fired."

**Transition to YETI:** "For a borrower with documents, Phase 1 runs first — that
is what the YETI case shows. The spread output feeds Phase 2 as financial evidence.
That hand-off is the next wiring step."
