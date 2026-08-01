# plan_JACI_CI_ONTOLOGY_SPREAD_OBJECTS.md

**Author:** Virendra Mehta  
**Created:** Monday, June 15, 2026 · 6:14 AM PT  
**Target file:** `config/packs/ci-spread-core/ontology/ci_lending.yaml`  
**Purpose:** Extend the CI lending ontology with domain objects that exist in code
but are absent from the ontology: the financial spread, the credit metrics computed
from it, the borrowing base, and the credit decision. This is offline pack crafting —
a YAML edit, no code changes anywhere.

---

## Context

`ci_lending.yaml` currently defines the transaction and borrower layer well:
`Borrower`, `Facility`, `CollateralPool`, `Lien`, `FinancialPeriod`, `Covenant`,
`CreditEvent`, `IndustryContext`, plus derived concepts `BorrowingBase`,
`ExcessAvailability`, `Leverage`, `FCCR`, `UCAcashFlow`, `DebtServiceCoverage`.

What is missing is the **spread layer** — the objects produced when the platform
processes the loan package — and the **decision layer** — the structured output of
the credit analysis loop. These have exact schema definitions in code
(`jazzx_sdk.finance.spread`, `schemas/__init__.py`) and a canonical template format
in `YETI_Spread_Template.csv`. The ontology should name and describe them so the KG,
the demo, and Pack Studio can reference them as first-class domain objects.

---

## What NOT to change

- No code changes anywhere.
- Do not modify any entity or concept that already exists in `ci_lending.yaml`.
- Do not change the `version`, `domain`, `segment`, or `regulatory_context` fields.
- Do not modify `pack_manifest.yaml` — the ontology path is already registered there.

---

## Changes to make

All changes are additions to `config/packs/ci-spread-core/ontology/ci_lending.yaml`.

### 1. Bump version and add a changelog comment

Change `version: "0.1.0"` to `version: "0.2.0"`.

Add a comment block directly below the version line:

```yaml
# v0.2.0 — added spread layer (FinancialSpread, SpreadStatement, SpreadLine,
#           CreditMetrics, WorkingCapitalMetrics, BorrowingBaseResult) and
#           decision layer (CreditDecision, CreditCondition).
#           Derived concepts promoted from concept_graph: BorrowingBase and
#           FCCR are now entities with their own fields, not formulas only.
#           Source schemas: jazzx_sdk.finance.spread, ci_spread.schemas.
```

### 2. New entities — spread layer

Add the following four entities to the `entities:` block, after `IndustryContext`
and before `relationships:`.

Read `jazzx_sdk/finance/spread.py` first to confirm field names on `FinancialSpread`,
`Statement`, and `SpreadLine`. Read `ci_spread/schemas/__init__.py` to confirm fields
on `BorrowingBase`. Use exact field names from those classes.

```yaml
  FinancialSpread:
    description: >
      The standardized, as-reported spread of a borrower's financial statements.
      Produced by the spreading engine from converted 10-K documents. Carries the
      raw statement lines exactly as reported — no derived analytics. One spread
      covers multiple periods (columns). Source schema: jazzx_sdk.finance.spread.
    source_schema: jazzx_sdk.finance.FinancialSpread
    fields:
      company: {type: str, required: true}
      periods: {type: list, required: true,
                description: "Fiscal-year labels in column order, e.g. [FY2023, FY2024, FY2025]"}
      currency: {type: str, default: USD}
      units: {type: str, default: thousands,
              description: "thousands | millions | ones"}
      source: {type: str,
               description: "Provenance — path to source document or 'merged: ...'"}
      statement_types: {type: list,
                        description: "Statement types present: income_statement | balance_sheet | cash_flow"}

  SpreadStatement:
    description: >
      One financial statement within a FinancialSpread — income statement, balance
      sheet, or cash flow. Contains an ordered list of SpreadLines. Source schema:
      jazzx_sdk.finance.Statement.
    source_schema: jazzx_sdk.finance.Statement
    fields:
      statement_type: {type: str, required: true,
                       description: "income_statement | balance_sheet | cash_flow"}
      title: {type: str, required: true,
              description: "As-reported statement title from the filing"}
      line_count: {type: int}

  SpreadLine:
    description: >
      One line item in a SpreadStatement. Values are index-aligned to the parent
      FinancialSpread's periods list. The as-reported label is preserved; the
      normalized key enables cross-borrower comparison. Source schema:
      jazzx_sdk.finance.SpreadLine.
    source_schema: jazzx_sdk.finance.SpreadLine
    fields:
      label: {type: str, required: true,
              description: "As-reported line label, e.g. 'Net sales'"}
      key: {type: str,
            description: "Normalized key for cross-borrower comparison, e.g. 'net_sales'"}
      section: {type: str,
                description: "Sub-section grouping: revenue | current_assets | operating | etc."}
      is_subtotal: {type: bool, default: false,
                    description: "True for subtotal/total lines such as Gross profit, Total assets"}
      values: {type: list,
               description: "Value per period, index-aligned to FinancialSpread.periods. null if not reported."}

  BorrowingBaseResult:
    description: >
      The computed borrowing base for an ABL facility — the maximum advance the
      lender will extend against eligible collateral at a point in time. Distinct
      from CollateralPool (the collateral schedule) and from the BorrowingBase
      concept_graph entry (the formula). This is the computed result with all
      inputs resolved. Produced by the Verifier and Reasoner during the conductor
      loop. Source schema: ci_spread.schemas.BorrowingBase.
    source_schema: jaci.scenarios.ci_spread.schemas.BorrowingBase
    fields:
      as_of_date: {type: str}
      gross_ar: {type: float}
      ineligible_ar: {type: float}
      eligible_ar: {type: float, required: true}
      ar_advance_rate: {type: float, required: true, default: 0.85}
      ar_availability: {type: float, required: true}
      gross_inventory: {type: float}
      ineligible_inventory: {type: float}
      eligible_inventory: {type: float, required: true}
      inventory_advance_rate: {type: float, required: true, default: 0.50}
      inventory_availability: {type: float, required: true}
      reserves: {type: float}
      total_availability: {type: float, required: true}
      outstanding_balance: {type: float}
      excess_availability: {type: float}
      borrower_stated_bbc: {type: float,
                            description: "BBC as stated by borrower — may differ from computed"}
      variance_to_stated: {type: float,
                           description: "Computed - stated. Negative = borrower overstated."}
      field_exam_required: {type: bool, default: true}
```

### 3. New entities — credit metrics layer

These are the computed outputs of `analytics.compute_metrics()` and
`template.py`'s CREDIT METRICS / WORKING CAPITAL METRICS sections. They map
directly to the bottom two sections of `YETI_Spread_Template.csv`.

```yaml
  CreditMetrics:
    description: >
      Per-period credit ratios and profitability metrics derived from the
      FinancialSpread. Computed deterministically by the platform — not extracted
      from the filing. Corresponds to the CREDIT METRICS section of the spread
      template. Source: commercial_lending.analytics.compute_metrics().
    fields:
      period: {type: str, required: true}
      gross_margin_pct: {type: float, description: "Gross profit / net sales (%)"}
      operating_margin_pct: {type: float, description: "Operating income / net sales (%)"}
      ebitda: {type: float, description: "Operating income + D&A ($000s)"}
      ebitda_margin_pct: {type: float, description: "EBITDA / net sales (%)"}
      free_cash_flow: {type: float, description: "Operating cash flow - capex ($000s)"}
      leverage_x: {type: float, description: "Total funded debt / EBITDA (x)"}
      net_leverage_x: {type: float, description: "(Total funded debt - cash) / EBITDA (x)"}
      current_ratio: {type: float, description: "Current assets / current liabilities (x)"}

  WorkingCapitalMetrics:
    description: >
      Per-period working capital efficiency metrics derived from the FinancialSpread.
      Corresponds to the WORKING CAPITAL METRICS section of the spread template.
      Source: jazzx_sdk.tools.financial.working_capital_days().
    fields:
      period: {type: str, required: true}
      dso_days: {type: float,
                 description: "Days sales outstanding — A/R / (net sales / 365)"}
      dio_days: {type: float,
                 description: "Days inventory outstanding — inventory / (COGS / 365)"}
      dpo_days: {type: float,
                 description: "Days payable outstanding — A/P / (COGS / 365)"}
      ccc_days: {type: float,
                 description: "Cash conversion cycle — DSO + DIO - DPO"}
```

### 4. New entities — decision layer

```yaml
  CreditDecision:
    description: >
      The structured output of the CI credit analysis loop. Produced by the
      Reasoner, gated by the Governor, narrated by the Narrator. Contains the
      credit recommendation, key ratios validated against policy, and conditions
      precedent. Promoted to a CanonicalCaseFile in fabric.canonical at loop
      completion. Source schema: ci_spread.schemas.CreditRecommendation.
    source_schema: jaci.scenarios.ci_spread.schemas.CreditRecommendation
    fields:
      decision: {type: str, required: true,
                 description: "approved | approved_with_conditions | declined | refer_to_committee"}
      approved_amount: {type: float}
      risk_rating: {type: str,
                    description: "pass | pass_watch | special_mention | substandard | doubtful | loss"}
      advance_rate_ar: {type: float}
      advance_rate_inventory: {type: float}
      leverage_x: {type: float, description: "Funded debt / adj. EBITDA at decision"}
      fccr_x: {type: float, description: "Fixed charge coverage ratio at decision"}
      rationale: {type: str}
      strengths: {type: list}
      key_risks: {type: list}
      conditions_count: {type: int, description: "Number of conditions precedent"}
      covenants: {type: list}
      policy_refs: {type: list, description: "Policy IDs evaluated by PolicyExpert"}
      guidance_refs: {type: list,
                      description: "PlaybookExpert guidance refs — asset_id + section_id anchors"}

  CreditCondition:
    description: >
      An individual condition precedent or ongoing covenant attached to an approved
      credit facility. Conditions precedent must be satisfied before commitment.
      Source schema: ci_spread.schemas.CICondition.
    source_schema: jaci.scenarios.ci_spread.schemas.CICondition
    fields:
      condition_type: {type: str, required: true,
                       description: "pre_closing | ongoing_covenant | reporting"}
      category: {type: str}
      description: {type: str, required: true}
      responsible_party: {type: str, default: borrower}
      severity: {type: str, default: required, description: "required | recommended"}
```

### 5. New relationships

Add to the `relationships:` list. Preserve all existing relationships unchanged.

```yaml
  # Spread layer
  - {subject: Borrower,       predicate: has_spread,         object: FinancialSpread,      cardinality: one_to_many,
     note: "One spread per filing run; multi-filing spreads are merged into one"}
  - {subject: FinancialSpread, predicate: contains_statement, object: SpreadStatement,     cardinality: one_to_many}
  - {subject: SpreadStatement, predicate: contains_line,      object: SpreadLine,          cardinality: one_to_many}
  - {subject: FinancialSpread, predicate: yields_metrics,     object: CreditMetrics,       cardinality: one_to_many,
     note: "One CreditMetrics node per period"}
  - {subject: FinancialSpread, predicate: yields_wc_metrics,  object: WorkingCapitalMetrics, cardinality: one_to_many,
     note: "One WorkingCapitalMetrics node per period"}
  - {subject: Facility,        predicate: has_bbc_result,     object: BorrowingBaseResult, cardinality: one_to_many,
     note: "One per BBC computation; typically one per fiscal period"}
  - {subject: BorrowingBaseResult, predicate: computed_from,  object: CollateralPool,      cardinality: many_to_one}

  # Decision layer
  - {subject: Facility,        predicate: has_decision,       object: CreditDecision,      cardinality: one_to_many,
     note: "One per conductor run; the most recent is the active decision"}
  - {subject: CreditDecision,  predicate: has_condition,      object: CreditCondition,     cardinality: one_to_many}
  - {subject: CreditDecision,  predicate: validated_against,  object: Covenant,            cardinality: one_to_many}
  - {subject: CreditDecision,  predicate: backed_by_spread,   object: FinancialSpread,     cardinality: many_to_one}
  - {subject: CreditDecision,  predicate: backed_by_bbc,      object: BorrowingBaseResult, cardinality: many_to_one}
```

### 6. Promote existing concept_graph entries that now have entity backing

`BorrowingBase` in `concept_graph` is a formula. Now that `BorrowingBaseResult` is a
proper entity, add a `resolved_by` field to the existing `BorrowingBase` concept_graph
entry pointing to the new entity:

```yaml
  BorrowingBase:
    description: "Maximum ABL advance against eligible collateral"
    formula: "(ar_eligible * advance_rate_ar) + (inventory_eligible * advance_rate_inventory)"
    inputs: [CollateralPool.ar_eligible, CollateralPool.inventory_eligible,
             CollateralPool.advance_rate_ar, CollateralPool.advance_rate_inventory]
    policy_ref: CI_CORE_ABL_POLICY
    resolved_by: BorrowingBaseResult   # add this line only
```

Similarly for `FCCR`:

```yaml
  FCCR:
    description: "Fixed charge coverage..."
    formula: "..."
    inputs: [...]
    policy_ref: CI_CORE_FCCR_POLICY
    resolved_by: CreditDecision.fccr_x   # add this line only
```

---

## Acceptance checks

After editing, verify the file is valid YAML:

```bash
python -c "import yaml; yaml.safe_load(open('config/packs/ci-spread-core/ontology/ci_lending.yaml'))"
```

Verify entity count — should be 15 (9 existing + 6 new):

```bash
python -c "
import yaml
d = yaml.safe_load(open('config/packs/ci-spread-core/ontology/ci_lending.yaml'))
print('entities:', list(d['entities'].keys()))
print('relationships:', len(d['relationships']))
print('concept_graph:', list(d['concept_graph'].keys()))
"
```

Expected output:
- entities: `[Borrower, Guarantor, Facility, CollateralPool, Lien, FinancialPeriod, Covenant, CreditEvent, IndustryContext, FinancialSpread, SpreadStatement, SpreadLine, BorrowingBaseResult, CreditMetrics, WorkingCapitalMetrics, CreditDecision, CreditCondition]`
- relationships: 17 (8 existing + 9 new)
- concept_graph: `[BorrowingBase, ExcessAvailability, Leverage, FCCR, UCAcashFlow, DebtServiceCoverage]` (unchanged)
