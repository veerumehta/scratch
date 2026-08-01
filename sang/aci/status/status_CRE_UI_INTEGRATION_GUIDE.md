# CRE UI Integration Guide

**Date**: 2026-06-05  
**Purpose**: Replace hardcoded UI logic with dynamic rendering from canonical objects

---

## Infrastructure Built

### ✅ Complete (Production-Ready)
1. **`HypothesisCategorizer`** - Maps hypotheses → assessment categories
2. **`CategoryStatusCalculator`** - Computes status from hypothesis severity
3. **`CategorySummaryBuilder`** - Builds complete category summaries
4. **`FindingRenderer`** - Formats hypothesis data for display
5. **`PolicyContextProvider`** - Surfaces relevant policy rules *(partial)*

### 📦 Modules
- **`src/jaci/scenarios/cre_underwriting/ui_helpers.py`** - Core infrastructure
- **`tests/test_cre_ui_helpers.py`** - 12 passing tests

---

## Integration Examples

### Before: Hardcoded Categories (app.py:2680-2689)

```python
# HARDCODED
categories = [
    ("✅", "Loan Request & Structure", "cleared"),
    ("✅", "Entity & Ownership", "cleared"),
    ("✅", "Collateral & Valuation", "cleared"),
    ("✅", "Sponsor & Guarantor", "cleared"),
    ("✅", "Market & Comparable Analysis", "cleared"),
    ("⚠️", "Rental Income & Occupancy", "warning"),
    ("🔄", "Operating Expenses & Taxes", "review"),
    ("🔄", "Insurance", "review"),
]
```

### After: Dynamic from Case File

```python
from jaci.scenarios.cre_underwriting.ui_helpers import (
    CategorySummaryBuilder,
    CategoryStatus,
)

# DYNAMIC - derives from actual investigation results
if case_file:
    summaries = CategorySummaryBuilder.build_summaries(case_file)
    
    categories = [
        (
            CategorySummaryBuilder.get_status_icon(summary.status),
            summary.category.value,
            summary.status.value,
        )
        for summary in summaries
    ]
```

**Benefits:**
- ✅ Categories auto-update based on real findings
- ✅ Status icons reflect actual severity (not hardcoded)
- ✅ No manual UI updates when investigation changes

---

### Before: Hardcoded Finding Text (app.py:2748)

```python
# HARDCODED FINDING
st.error("""
**OM reports 94% physical occupancy. Unit-level rent roll reconciles to 89.4%.**

The 5-point gap is a ~$280K EGI swing.

**Resolution:** 9 units leased but non-paying must be resolved before DSCR finalization.
""")
```

### After: Dynamic from Hypotheses

```python
from jaci.scenarios.cre_underwriting.ui_helpers import FindingRenderer

# Get hypotheses for this category
rental_income_hyps = [
    h for h in ctx.hypotheses
    if h.content.category == "Rental Income & Occupancy"
]

# Render each finding
for hyp in rental_income_hyps:
    finding = FindingRenderer.render_finding_summary(hyp)
    severity_icon = FindingRenderer.get_severity_icon(finding["severity"])
    
    with st.expander(f"🔍 **FINDING: {finding['title']}**", expanded=True):
        st.error(f"""
**{finding['description']}**

**Impact:** {finding['impact']}

**Status:** {finding['status']}
        """)
```

**Benefits:**
- ✅ Finding text comes from actual hypothesis description
- ✅ Impact statement from hypothesis.content.impact_on_loan
- ✅ Supports multiple findings per category
- ✅ No hardcoded dollar amounts or percentages

---

### Before: Hardcoded Policy Thresholds (app.py:2774)

```python
# HARDCODED THRESHOLDS
st.markdown("""
✅ Exceeds policy minimums (Net worth $10M, Liquidity $2M)
""")
```

### After: Dynamic from PolicyRegistry

```python
from jaci.scenarios.cre_underwriting.ui_helpers import PolicyContextProvider
from jaci.scenarios.cre_underwriting.policies import CRE_REGISTRY

# Get relevant policies for this category
policies = PolicyContextProvider.get_relevant_policies(
    category=AssessmentCategory.SPONSOR_GUARANTOR,
    policy_registry=CRE_REGISTRY
)

# Display actual policy thresholds
st.markdown("**Policy Requirements:**")
for policy_id, rule in policies:
    threshold = PolicyContextProvider.format_policy_threshold(rule)
    st.markdown(f"- {rule.description}: {threshold}")
```

**Benefits:**
- ✅ Thresholds pulled from actual PolicyRegistry
- ✅ No hardcoded "$10M, $2M" values
- ✅ Auto-updates when policies change
- ✅ Shows source policy ID for traceability

---

## Complete Integration Example

```python
# app.py CRE Demo Section (Refactored)

from jaci.scenarios.cre_underwriting.ui_helpers import (
    CategorySummaryBuilder,
    FindingRenderer,
    PolicyContextProvider,
    AssessmentCategory,
)
from jaci.scenarios.cre_underwriting.policies import CRE_REGISTRY

# ... load case_file from conductor ...

if case_file:
    # Build category summaries from investigation
    summaries = CategorySummaryBuilder.build_summaries(case_file)
    
    # LEFT SIDEBAR: Assessment Categories (Dynamic)
    with col_left:
        st.subheader("Assessment Categories")
        
        for summary in summaries:
            icon = CategorySummaryBuilder.get_status_icon(summary.status)
            label = f"{icon} {summary.category.value}"
            
            if summary.hypothesis_count > 0:
                label += f" ({summary.hypothesis_count})"
            
            if st.button(label, key=f"cat_{summary.category.value}"):
                st.session_state.cre_selected_category = summary.category.value
                st.rerun()
    
    # RIGHT PANEL: Category Detail (Dynamic)
    with col_right:
        selected_category = st.session_state.cre_selected_category
        
        # Find summary for selected category
        summary = next(
            (s for s in summaries if s.category.value == selected_category),
            None
        )
        
        if summary:
            # Header
            icon = CategorySummaryBuilder.get_status_icon(summary.status)
            st.subheader(f"{icon} {summary.category.value}")
            
            if summary.hypothesis_count > 0:
                st.caption(f"{summary.hypothesis_count} Finding(s) • {summary.max_severity.title()} Severity")
            else:
                st.success("Category cleared - no issues identified")
            
            # Findings
            if summary.hypotheses:
                st.markdown("### Findings")
                for i, hyp in enumerate(summary.hypotheses, 1):
                    finding = FindingRenderer.render_finding_summary(hyp)
                    severity_icon = FindingRenderer.get_severity_icon(finding["severity"])
                    
                    with st.expander(
                        f"{severity_icon} {i}. {finding['title']} - {finding['severity'].upper()}",
                        expanded=(i == 1)
                    ):
                        st.markdown(f"**Description:** {finding['description']}")
                        st.markdown(f"**Impact:** {finding['impact']}")
                        st.markdown(f"**Status:** {finding['status']}")
            
            # Policy Context
            policies = PolicyContextProvider.get_relevant_policies(
                category=summary.category,
                policy_registry=CRE_REGISTRY
            )
            
            if policies:
                st.markdown("### Applicable Policy Requirements")
                for policy_id, rule in policies:
                    threshold = PolicyContextProvider.format_policy_threshold(rule)
                    st.markdown(f"- **{rule.rule_id}**: {rule.description} → {threshold}")
```

---

## Migration Path

### Phase 1: Categories & Status ✅ (Ready Now)
1. Replace hardcoded category list with `CategorySummaryBuilder.build_summaries()`
2. Use dynamic status icons from `get_status_icon()`
3. Test: Categories update based on investigation results

### Phase 2: Findings Display (Next)
4. Replace hardcoded finding text with `FindingRenderer`
5. Iterate over `summary.hypotheses` to display all findings
6. Test: Findings render from actual hypothesis data

### Phase 3: Policy Context (After)
7. Add `PolicyContextProvider.get_relevant_policies()` to each category
8. Display actual policy thresholds instead of hardcoded values
9. Test: Policy requirements pulled from registry

### Phase 4: Jazz Assistant (Future)
10. Replace pattern-matching in `get_jazz_response()` with RAG
11. Use case_file context for semantic search
12. Test: Assistant answers based on actual investigation data

---

## Benefits Summary

**Before (Hardcoded):**
- ❌ Manual updates when findings change
- ❌ No traceability to source data
- ❌ Policy thresholds can drift from registry
- ❌ Single finding per category
- ❌ Status icons manually set

**After (Dynamic):**
- ✅ Auto-updates from investigation
- ✅ Full traceability to hypothesis/policy source
- ✅ Thresholds always match registry
- ✅ Supports multiple findings per category
- ✅ Status computed from actual severity

**Code Quality:**
- ✅ 12 passing tests for UI logic
- ✅ Pure functions (no side effects)
- ✅ Reusable across UI frameworks
- ✅ Separation of concerns (data vs. presentation)

---

## Next Steps

1. **Integrate Phase 1** into app.py (categories + status)
2. **Verify in browser** - categories should update dynamically
3. **Integrate Phase 2** (findings display)
4. **Add integration test** - run conductor, verify UI renders correctly
5. **Document pattern** for other scenarios (AML, KYC)

---

## Files Modified

- ✅ `src/jaci/scenarios/cre_underwriting/ui_helpers.py` - New infrastructure
- ✅ `tests/test_cre_ui_helpers.py` - 12 passing tests
- 📝 `app.py` - Integration (pending)
- 📝 `docs/CRE_UI_INTEGRATION_GUIDE.md` - This guide
