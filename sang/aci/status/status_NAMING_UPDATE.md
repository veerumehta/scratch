# JACI Naming and Scope Update

**Date:** 2026-06-04  
**Version:** 0.6.2

## Background

JACI originally stood for "JazzX **AML** Case Intelligence" - a hypothesis-driven investigation agent focused on Anti-Money Laundering use cases.

With the addition of KYC, CRE, and Earnings scenarios, JACI has evolved into a **multi-domain investigation platform** demonstrating JAPES's versatility across different investigation contexts.

## New Branding

### JACI Now Means:
**JazzX Contextual Intelligence**

- **Contextual** - Operates across different investigation contexts (compliance, lending, financial analysis)
- **Intelligence** - Autonomous decision-making and recommendation generation
- Avoids buzzwords while accurately describing multi-domain capability

### Tagline:
"Multi-domain hypothesis-driven investigation platform built on JAPES"

## Files Updated

### 1. README.md
**Before:**
```markdown
# JACI (JazzX AML Case Intelligence)
**Hypothesis-driven investigation agent built on JAPES**
```

**After:**
```markdown
# JACI (JazzX Contextual Intelligence)
**Multi-domain hypothesis-driven investigation platform built on JAPES**
```

**Changes:**
- ✅ Updated title from "AML Case Intelligence" → "AI Case Intelligence"
- ✅ Updated branch description to mention all 4 domains (AML, KYC, CRE, Earnings)
- ✅ Expanded scenario comparison table to include CRE and Earnings
- ✅ Changed "AML Use Case" section → "Domain Examples" with all scenarios

### 2. pyproject.toml
**Before:**
```toml
description = "JazzX AML Case Intelligence - Hypothesis-driven AML investigation agent with real source connectors"
```

**After:**
```toml
description = "JazzX Contextual Intelligence - Multi-domain hypothesis-driven investigation platform (AML, KYC, CRE, Earnings) built on JAPES"
```

### 3. src/jaci/__init__.py
**Before:**
```python
"""
JACI - JazzX AML Case Intelligence

Hypothesis-driven AML investigation agent for the JazzX platform.
"""
```

**After:**
```python
"""
JACI - JazzX Contextual Intelligence

Multi-domain hypothesis-driven investigation platform built on JAPES.

Operates across multiple investigation contexts:
- AML (Anti-Money Laundering)
- KYC (Know Your Customer / Customer Due Diligence)
- CRE (Commercial Real Estate Underwriting)
- Earnings (Financial Earnings Review)
"""
```

### 4. app.py
**Before:**
```python
"""
JACI Evaluation Dashboard

Streamlit app for visualizing evaluation results, case flows, and testing prompts.
"""
```

**After:**
```python
"""
JACI Multi-Domain Evaluation Dashboard

Streamlit app for visualizing evaluation results, case flows, and testing prompts
across multiple investigation domains (AML, KYC, CRE, Earnings).
"""
```

### 5. CHANGELOG.md
Added "Changed - Branding" section documenting the naming evolution.

## Rationale

### Why "Contextual Intelligence"?

1. **Accurate Representation**: JACI operates across different investigation contexts (AML compliance context, CRE lending context, Earnings analysis context, etc.)
2. **Domain-Agnostic**: "Contextual" works for compliance, lending, financial analysis - any domain with investigative context
3. **Not Buzzwordy**: Professional, descriptive term that accurately describes the capability
4. **Future-Proof**: Easy to add new contexts/domains without rebranding
5. **Maintains Continuity**: "JACI" acronym preserved, minimizes disruption

### What Didn't Change?

- ✅ **Package name** (`jaci`) - Stays the same, no breaking changes
- ✅ **Repository name** - Can stay as-is or rename later
- ✅ **API/Code** - No functional changes, purely descriptive updates
- ✅ **Folder structure** - `scenarios/` already organized by domain

## Domain Positioning

| Domain | Status | Evidence Tools | Golden Cases | Evaluation | Use Case |
|--------|--------|----------------|--------------|------------|----------|
| **AML** | ✅ Production-ready | 8 tools | 11 cases | Full harness | Transaction monitoring → SAR filing |
| **KYC** | ✅ Production-ready | 8 tools | 10 cases | Full harness | Customer review → Risk tier + EDD |
| **CRE** | ✅ Complete | 8 tools | 1 case (MAA) | Full harness (NEW) | Loan underwriting → Approve/Decline |
| **Earnings** | ⏳ Proof-of-concept | 4 tools | 1 demo case | Not yet | Earnings review → Material assessment |

## Communication Guidelines

### External Messaging
- "JACI is a contextual intelligence platform for multi-domain investigations"
- "Built on JAPES, operating across AML, KYC, CRE, and Earnings investigation contexts"
- "Demonstrates hypothesis-driven investigation with context-aware intelligence"

### Internal Shorthand
- Still OK to say "the AML scenario" or "AML pack"
- JACI itself is now domain-agnostic platform
- Each scenario is a domain-specific pack

### Documentation Standards
- ✅ **README**: Multi-domain positioning front and center
- ✅ **Scenario docs**: Domain-specific, can use full terminology (AML, CRE, etc.)
- ✅ **JAPES integration docs**: Emphasize JACI as multi-domain reference implementation

## Migration Impact

### Breaking Changes
**None** - This is a descriptive/documentation update only.

### Developer Impact
**None** - No code changes required. Existing imports, APIs, and functionality unchanged.

### User Impact
**Positive** - Clearer positioning of JACI's capabilities and scope.

## Related Work

This naming update complements the **Scenario Registry Architecture** (v0.6.2) which removed hardcoded AML assumptions from the codebase:

1. **Scenario Registry** (technical) - Made code multi-domain
2. **Naming Update** (descriptive) - Made messaging multi-domain

Together, these changes complete JACI's transformation from single-domain (AML) to multi-domain AI platform.

---

**Approved by:** User (Sangit)  
**Implementation:** Complete  
**Documentation:** This file + CHANGELOG.md + REFACTOR_SUMMARY.md
