# plan_JACI_SPREAD_TAB_TEMPLATE_COMPARISON.md

**Author:** Virendra Mehta  
**Created:** Monday, June 15, 2026 · 6:40 AM PT  
**Target file:** `src/jaci/scenarios/ci_spread/ui/demo_page.py`  
**Also touches:** `src/jaci/scenarios/commercial_lending/template.py` (one new function, no changes to existing)  
**Purpose:** Replace the Spread tab with an always-visible template comparison table.
The Curated column is always populated from the fixture. The Spreader column shows `—`
until the 10-K Spreading tab is run, then fills in live from the extracted spread.

---

## Context

Read these files in full before writing any code:

```
src/jaci/scenarios/ci_spread/ui/demo_page.py       — the Spread tab is tab1
src/jaci/scenarios/commercial_lending/template.py  — _TEMPLATE, template_rows()
src/jaci/scenarios/commercial_lending/analytics.py — _vals(), compute_metrics()
docs/LoanSamples/YETI/yeti_financials.json         — the curated fixture
```

The curated fixture (`yeti_financials.json`) has five period columns
(FY2021-FY2025). The live spread will have three (FY2025/FY2024/FY2023 from
one filing) or six (FY2020-FY2025 from the multi-year run). The comparison
table must handle this: show the periods that exist in the curated fixture, and
for each period show the spreader value only if that period is also in the live
spread.

---

## What NOT to change

- `template.py` existing functions (`template_rows`, `template_csv_text`) — unchanged.
- The 10-K Spreading tab (tab6) — unchanged.
- The download buttons for Excel/CSV — unchanged, still live on tab6.
- Any other tab.
- The curated view fallback on `render_spread_analytics` — this function is called
  elsewhere (CRE demo); leave it alone.

---

## Part 1 — New helper in `template.py`

Add one new function at the bottom of `template.py`. Do not modify any existing
function.

```python
def curated_template_values(fd: dict) -> dict[str, dict[str, float | None]]:
    """Extract curated values from yeti_financials.json keyed by template line label.

    Returns: {template_label: {period: value_or_none}}

    Maps each _TEMPLATE line to the corresponding key and section in the fixture.
    Only covers lines that exist in the fixture; everything else maps to None.
    Used by the Spread tab to populate the Curated column without a spread run.
    """
```

Inside this function, build a mapping from template label to fixture key+section.
The mapping should be a local dict — do not add module-level state. Use the
`_TEMPLATE` list directly to drive the row order so the output is always
aligned to template row order.

The fixture structure to read from:

```python
inc = fd.get("income_statement", {})   # keys: net_sales, cost_of_goods_sold, etc.
bal = fd.get("balance_sheet", {})      # keys: cash_and_equivalents, accounts_receivable_net, etc.
cf  = fd.get("cash_flow", {})          # keys: operating_cash_flow, capex, etc.
rat = fd.get("credit_ratios", {})      # keys: gross_margin_pct, leverage_funded_debt_ebitda, etc.
```

All of these are period-indexed lists aligned to their respective `columns` list.

Build a `periods` list from `inc["columns"]` (the five curated periods).

For each `(section_header, lines)` in `_TEMPLATE`, and for each `(label, locator)`
in `lines`:

- Use the locator tuple to identify which fixture dict and key to read. The mapping
  from locator to fixture is:

  | Locator prefix | Fixture section | Key translation |
  |---|---|---|
  | `("is", key, ...)` | `inc` | use the first candidate key that exists in `inc` |
  | `("bs", key, ...)` | `bal` | special cases below |
  | `("cf", key, ...)` | `cf`  | use the first candidate key that exists in `cf` |
  | `("m", metric, fmt)` | `rat` | metric key translation below |

  BS special cases (the fixture uses different key names than the template locators):
  - `"cash"` → `bal["cash_and_equivalents"]`
  - `"accounts_receivable"` → `bal["accounts_receivable_net"]`
  - `"inventory"` → `bal["inventory"]`
  - `"prepaid"` → `bal["prepaid_and_other_current"]`
  - `"total_current_assets"` → `bal["total_current_assets"]`
  - `"property_and_equipment"` → `bal["ppe_net"]`
  - `"right_of_use"` → `bal["operating_lease_rou"]`
  - `"goodwill"` → `bal["goodwill"]`
  - `"intangible"` → `bal["intangibles_net"]`
  - `"total_assets"` → `bal["total_assets"]`
  - `"accounts_payable"` → `bal["accounts_payable"]`
  - `"accrued_expenses"` → `bal["accrued_and_other_current"]`
  - `"current_maturities"` → `bal["current_maturities_ltd"]`
  - `"total_current_liabilities"` → `bal["total_current_liabilities"]`
  - `"long_term_debt_net"` → `bal["long_term_debt"]`
  - `"total_stockholders_equity"` → `bal["stockholders_equity"]`
  - All other BS locator keys → `None` (not in fixture)

  Metric key translation (`"m"` locator):
  - `"gross_margin_pct"` → `rat["gross_margin_pct"]`
  - `"operating_margin_pct"` → `rat["operating_margin_pct"]`
  - `"ebitda"` → `inc["adj_ebitda"]` (the fixture stores adj_ebitda, not raw ebitda)
  - `"ebitda_margin_pct"` → `rat["adj_ebitda_margin_pct"]`
  - `"leverage_x"` → `rat["leverage_funded_debt_ebitda"]`
  - `"net_leverage_x"` → `rat["net_leverage"]`
  - `"current_ratio"` → `rat["current_ratio"]`
  - `"da"` → `inc["da_amortization"]`
  - `"stock_based_compensation"` → `None` (not in fixture)
  - `"free_cash_flow"` → `cf.get("free_cash_flow")` (sparse in fixture, many nulls)
  - Working capital days (`"dso_days"`, `"dio_days"`, etc.) → `None` (not in fixture)

- For each period in `periods`, read `vals[period_index]` from the fixture list.
  Return a dict: `{label: {period: value_or_none}}` where `value_or_none` is the
  float from the fixture, or `None` if the key is absent or the value is null.

Return value: `{"periods": periods, "values": {label: {period: value_or_none}}}`.

---

## Part 2 — New helper in `template.py`

Add a second new function immediately after `curated_template_values`:

```python
def spreader_template_values(spread) -> dict[str, dict[str, float | None]]:
    """Extract spreader values from a live FinancialSpread, keyed by template line label.

    Returns: {"periods": spread.periods, "values": {label: {period: value_or_none}}}

    Uses the same _TEMPLATE locators as template_rows() but returns a dict keyed
    by label+period instead of a flat row list, so the comparison table can look
    up any cell by (label, period).
    """
```

Implementation: iterate `_TEMPLATE` exactly as `template_rows()` does, but instead
of building a list of rows, build `{label: {period: value}}`. The period-to-value
mapping comes from `zip(spread.periods, vals)`.

For `("m", ...)` locators: call `compute_metrics(spread)` once at the start and
cache the result. Use the same `_fmt`-to-float conversion: for `"n"` kind, the raw
float from `compute_metrics`; for `"p"` kind, the float directly; for `"x"` and
`"d"` kinds, the float directly. Store `None` where the value is `None`.

Return: `{"periods": spread.periods, "values": {label: {period: value_or_none}}}`.

---

## Part 3 — Replace Spread tab body in `demo_page.py`

Replace the entire body of `with tab1:` block. The new body has two states:
**always-visible** (curated column only) and **post-run** (curated + spreader columns
+ match indicator).

### 3a — Imports to add at the top of `demo_page.py`

Add to the existing `from jaci.scenarios.commercial_lending.ui import (...)` block:

```python
from jaci.scenarios.commercial_lending.template import (
    curated_template_values,
    spreader_template_values,
    _TEMPLATE,
)
```

### 3b — New tab1 body

```python
with tab1:
    _live_spread = st.session_state.get("ci_spread_result")

    # --- Header ---
    _n_matched, _n_checked = 0, 0
    if _live_spread is not None:
        # compute match stats for subtitle
        from jaci.scenarios.commercial_lending.spreader import validate_spread
        _checks = validate_spread(_live_spread, _YETI_TRUTH, key_statement=_yeti_truth_stmt())
        _n_checked = len(_checks)
        _n_matched = sum(1 for c in _checks if c["ok"])

    if _live_spread is None:
        st.caption(
            "**Curated reference** (analyst-built) shown. "
            "Run the **📄 10-K Spreading** tab to populate the Spreader column."
        )
    else:
        (st.success if _n_matched == _n_checked else st.warning)(
            f"Spreader reconciles **{_n_matched}/{_n_checked}** key figures to the "
            f"filing (≤1% tolerance). Full comparison below."
        )

    # --- Build lookup tables ---
    _cur = curated_template_values(fd)
    _cur_periods = _cur["periods"]          # always FY2021..FY2025 from fixture
    _cur_vals = _cur["values"]

    _sp_vals = {}
    _sp_periods = []
    if _live_spread is not None:
        _sp = spreader_template_values(_live_spread)
        _sp_vals = _sp["values"]
        _sp_periods = _sp["periods"]

    # Display period columns: union of curated periods, most recent 3 only to
    # keep the table readable. Use the last 3 curated periods (FY2023/FY2024/FY2025).
    _display_periods = _cur_periods[-3:]

    # --- Build the comparison dataframe ---
    # Columns: Line Item | (for each period: Curated | Spreader | Δ)
    # Section headers get a special row with no values.
    def _fv(v, fmt="n"):
        """Format a float value for display."""
        if v is None:
            return "—"
        if fmt == "p":
            return f"{v:.1f}%"
        if fmt == "x":
            return f"{v:.2f}x"
        if fmt == "d":
            return f"{v:.0f}d"
        return f"{v:,.0f}"  # n: integers

    def _match_icon(cv, sv, fmt):
        """✅ if within 1% / 1 unit, ⚠ otherwise, — if either missing."""
        if cv is None or sv is None:
            return "—"
        if fmt in ("p", "x", "d"):
            return "✅" if abs(cv - sv) <= 0.1 else "⚠"
        # dollar values: 1% tolerance or $1K absolute
        tol = max(abs(cv) * 0.01, 1.0)
        return "✅" if abs(cv - sv) <= tol else "⚠"

    rows = []
    for section_header, lines in _TEMPLATE:
        # Section header row — bold label, no values
        rows.append({
            "Line Item": f"**{section_header}**",
            **{f"{p} · Curated": "" for p in _display_periods},
            **{f"{p} · Spreader": "" for p in _display_periods},
            **{f"{p} · Δ": "" for p in _display_periods},
        })
        for label, locator in lines:
            fmt = locator[2] if locator[0] == "m" else "n"
            row = {"Line Item": label}
            for p in _display_periods:
                cv = _cur_vals.get(label, {}).get(p)
                sv = _sp_vals.get(label, {}).get(p) if _live_spread else None
                row[f"{p} · Curated"] = _fv(cv, fmt)
                row[f"{p} · Spreader"] = _fv(sv, fmt)
                row[f"{p} · Δ"] = _match_icon(cv, sv, fmt) if _live_spread else "—"
            rows.append(row)
        # blank separator
        rows.append({"Line Item": "", **{k: "" for k in rows[-1] if k != "Line Item"}})

    _df = pd.DataFrame(rows)

    # Reorder columns: Line Item, then for each period (Curated, Spreader, Δ)
    _period_cols = []
    for p in _display_periods:
        _period_cols += [f"{p} · Curated", f"{p} · Spreader", f"{p} · Δ"]
    _df = _df[["Line Item"] + _period_cols]

    st.dataframe(
        _df,
        width="stretch",
        hide_index=True,
        height=min(900, 28 * (len(_df) + 1)),
    )

    if _live_spread is None:
        st.caption(
            "Spreader and Δ columns will populate when you run **📄 10-K Spreading**. "
            "Curated = hand-built analyst reference from the YETI Credit Package."
        )
    else:
        st.caption(
            f"Curated = analyst-built reference (yeti_financials.json).  "
            f"Spreader = extracted from the {', '.join(_live_spread.periods)} 10-K(s).  "
            "Δ: ✅ within 1% · ⚠ outside tolerance · — not in curated or not yet extracted."
        )
        st.caption(
            "Note: some Δ ⚠ are expected — the curated fixture uses rounded estimates for "
            "FY2024/FY2025 equity and some cash flow lines. The spreader has the exact "
            "filing values. See the comparison explanation in the Overview tab."
        )
```

---

## Part 4 — Remove the old Spread tab content

The old `tab1` body had two branches:
1. `if _live_spread is not None: render_spread_analytics(_live_spread, "ci")`
2. `else:` — the full curated income statement / balance sheet / credit ratios
   dataframes + the revenue/EBITDA chart

Both branches are fully replaced by Part 3. Delete them.

`render_spread_analytics` is still called on the CRE demo page — do not remove
it from `shared.py`. Just remove the call from the CI Spread tab1 block.

The three-column reconciliation view added in the previous plan
(`plan_JACI_YETI_DEMO_DECK_ALIGNMENT.md`, Gap 1) was also in tab1. That is now
superseded by the full comparison table here. Remove it.

---

## Acceptance checks

```bash
# 1. App loads without error on CI Spread scenario
streamlit run app.py
# Select "C&I Spread", select YETI. Spread tab should show the full template
# with Curated column populated and Spreader/Δ columns showing "—".

# 2. Section headers are bold and span the row with no values.

# 3. After running 10-K Spreading tab (FY2025 single filing):
# Spread tab Spreader column populates for FY2025 only.
# FY2023/FY2024 Spreader cells stay "—" (not in the single-filing spread).
# Δ column shows ✅ for exact matches (net_sales, A/R, inventory, cash).

# 4. After running 10-K Spreading tab (multi-year):
# Spreader column populates for FY2023, FY2024, FY2025.
# Net income FY2025 shows ⚠ (curated=$174,400, spreader=$165,387 — curated is wrong).
# Equity rows show ⚠ (curated rounded; spreader has exact values).

# 5. curated_template_values and spreader_template_values are importable:
python -c "from jaci.scenarios.commercial_lending.template import curated_template_values, spreader_template_values; print('ok')"
```

---

## Known risks

**`_TEMPLATE` import:** `_TEMPLATE` is a module-level list in `template.py` —
it starts with an underscore but that is convention, not enforcement. Import it
directly. If Claude Code sees a linting warning about importing a private name,
add a re-export alias `SPREAD_TEMPLATE = _TEMPLATE` at the bottom of `template.py`
and import that instead. Either is fine.

**Period alignment in `curated_template_values`:** The fixture stores all list
values index-aligned to their own `columns` list. Read `inc["columns"]` as the
canonical period list and build `period_index = {p: i for i, p in enumerate(columns)}`
before iterating. Use this to map period → list index safely rather than assuming
a fixed ordering.

**`adj_ebitda` nulls in fixture:** The curated fixture has `null` for FY2021 and
FY2022 in `adj_ebitda`. These will correctly map to `None` and display as `—`.

**`spreader_template_values` calling `compute_metrics`:** `compute_metrics` is not
cheap but it is synchronous and fast enough for a Streamlit callback. Call it once
at the top of the function and reuse the result for all `("m", ...)` locators.

**Column width:** With three sub-columns per period × three periods = nine value
columns plus "Line Item", the table will be wide. `width="stretch"` handles this
in Streamlit — the user can scroll horizontally. Do not try to paginate or truncate.
