# Acra DSCR eligibility grid — encoding notes

Companion to `profiles/acra_dscr_profile.yaml`, `policies/eligibility.yaml`, `tests/test_acra_eligibility.py`.
Source of truth: **Acra Lending DSCR Program Summary, version 6.15.2026 V1.1**.
Verified against japes 2.4.1 plus the uncommitted `MatrixCondition` change set, 2026-08-13 — **17/17 behavioural cases green**.

## 0. What changed since the build plan was written

The plan proposed `MatrixCondition` as a platform ask. **It already exists** — implemented and uncommitted in the japes working tree (`fabric/canonical/{policy,profiles,condition_evaluator,__init__}.py`, +476 lines with 13 matrix tests in `tests/test_condition_evaluator.py` and 3 in `tests/test_default_policy_expert.py`). The set-membership operator gap is closed in the same diff — `_MEMBERSHIP_OPS`, fixing a live bug where `Expression(operator=IN, …)` silently fell through to "always VIOLATED".

So the ask is not "build it," it is **"review and land it."** These artifacts are the first real consumer, and they exercise it end to end.

## 1. What is authored here

| Artifact | Contents |
|---|---|
| `profiles/acra_dscr_profile.yaml` | 5 tables (**99 + 3 + 3 + 12 + 33 cells**), 6 ratio thresholds, 11 custom scalars |
| `policies/eligibility.yaml` | **19 rules** — 5 `matrix`, 4 `ratio`, 10 `expression` |
| `tests/test_acra_eligibility.py` | 17 behavioural cases + a grid-completeness test |

`max_cltv_grid` holds **99 cells** = 3 loan-amount bands × 11 FICO bands × 3 purposes, of which **70 are eligible values and 29 are authored `"NA"`**. The published grid shows 78 cells; the extra 21 exist because the FICO axis is normalized across all three bands (the PDF prints a ragged grid — 10, 10, and 6 tiers — plus prose rows "<620" and "<700"). Normalizing is deliberate: `MatrixEvaluator` returns **INDETERMINATE when no band matches**, and INDETERMINATE reads as "we couldn't tell" rather than "ineligible." Every reachable combination must resolve to a *present* cell, with ineligibility expressed as an authored `"NA"` (which `_NA_SENTINELS` turns into VIOLATED). **An absent cell raises `KeyError` at runtime** — hence `test_grid_is_fully_authored`.

**Coverage is a reference slice, not the whole program.** Authored: the primary CLTV grid, loan-amount floor/ceiling, ineligible states, the >80% LTV gates (DSCR 1.20, 6-month reserves, property-type restriction), sub-1.0 and No-Ratio caps, the >$2M DSCR floor, FICO<620 reserves, short-term rental, property-type overlays, ITIN, escrow-waiver citizenship, and IO minimums. **Not authored:** the 13-state prepayment-penalty rules, credit-event/housing-history overlays, tradeline and thin-file rules, declining-market and rural modifiers, FTHB, ARM margin-by-FICO, vacant-property rules, seller concessions and gifting. Those are straightforward once the four gaps below are settled.

## 2. Two IR defects found by authoring this

Both fail **late** — they validate cleanly at authoring time and raise `ValueError` at evaluation. Both are cheap to fix and worth fixing before a pack author who is not an SDK engineer hits them.

**D1 — `RatioCondition.direction` accepts operators the evaluator cannot execute.**
The field is typed `ComparisonOperator` (9 values); `condition_evaluator.py:234` maps it onto `RatioDirection`, which has exactly two (`AT_LEAST ">="`, `AT_MOST "<="`, `tools/ratio_evaluator.py:20-23`). Authoring `direction: "<"` — the natural way to write "DSCR below 1.0" — passes pydantic and raises `ValueError: '<' is not a valid RatioDirection` on the first evaluation.
*Fix:* narrow the field's type to the two-value enum (or validate at model level).
*Worked around here* by inverting to `<=` against a `dscr_sub_1_ceiling: "0.9999"` profile threshold — which is exactly the kind of thing that should not appear in a governance-reviewed artifact.

**D2 — `Expression` float-casts the actual value for every non-membership operator.**
`condition_evaluator.py:129` does `float(actual)` before dispatch, so `Expression(field="citizenship_type", operator="==", value="itin")` raises `ValueError: could not convert string to float: 'itin'`. String equality is the most natural way to write a borrower- or occupancy-type overlay, and it is unusable. The new membership operators are correctly exempted from the cast; equality is not.
*Fix:* only cast for ordering operators (`>`, `>=`, `<`, `<=`); compare `==`/`!=` on the raw values.
*Worked around here* by writing every string equality as a single-element `in` / `not_in` — four rules carry that scar.

## 3. Four modelling gaps

**G1 — no composite applicability (`AND` of two predicates).** `Rule.applicability` is a single `Condition`, and no boolean-combinator kind exists. Several Acra rules are natively conjunctive:

- "warrantable condo **outside Florida**" in the >80% LTV property-type list;
- the **−5% CLTV Florida modifier** on non-warrantable condo and condotel;
- Illinois PPP buyout: *residential 1-4* **and** *(entity or individual)* **and** *amount ≤ $250,000*, with a second rule keyed on amount **and** rate > 8%;
- Pennsylvania: *individual* **and** *residential 1-2* **and** *< $319,777*.

Three options, in preference order: (a) add an `AllOf`/`AnyOf` combinator kind — additive, and the registry is open; (b) fold the extra axis into the matrix (`property_state` becomes an axis, multiplying cells by 50); (c) use `DslExpression` for applicability and rely on the expression DSL — but it is arithmetic-oriented, and burying eligibility predicates in formula strings defeats the reviewability that `RatioCondition`'s "threshold must be `profile:`" rule exists to protect. **Recommend (a)**, and note it is the single thing standing between this slice and the full program encoding.

**G2 — "DSCR < 1.0" and "No Ratio" are different conditions and must not share a rule.** The program summary groups them ("DSCR < 1.0 or No Ratio"), but on a no-ratio file the ratio evaluator returns **INDETERMINATE**, so an applicability probe written as a ratio silently yields NOT_APPLICABLE — the caps would quietly not apply, in the permissive direction. Encoded here as two rule pairs: `ACRA-SUB-1-DSCR-*` (ratio applicability) and `ACRA-NO-RATIO-*` (keyed on an explicit `dscr_documentation_type` field). **This requires the loan context to carry an explicit no-ratio flag** — it cannot be inferred from a missing DSCR.

**G3 — cap composition is a presentation concern, and nobody owns it yet.** Multiple max-CLTV rules can bind at once (grid 80%, non-warrantable condo 75%, Florida −5%, STR 70%). Each rule evaluates independently and reports its own verdict; the IR has no notion of "the binding cap." The underwriter needs **`min()` across all satisfied cap rules, with the binding one named**. `RuleOutcome.inputs` carries `cell_key` and `cell_value` for every matrix rule, so the data is there — someone must own the fold. Natural home: the DSCR calculation worksheet (B7 in the build plan), which is also where it becomes the auditable artifact.

**G4 — `Expression.value` takes literals, `RatioCondition.threshold` may not.** Ratio thresholds must be `profile:<key>` so they stay reviewable in one place; expression thresholds are literals inline. So `reserves_months >= 6` and `loan_amount <= 3000000` are hardcoded in the policy YAML while `dscr_min_high_ltv` sits in the profile. The scalars are duplicated into `profile.custom` here for review, but **nothing enforces that they match**. Either extend `Expression.value` to accept a `profile:` reference, or add a lint that fails when a policy literal has a diverging `custom` twin.

## 4. Encoding decisions worth knowing

- **Bands are `[min, max)`.** FICO 780 lands in the top tier; loan amount exactly $1,500,000 lands in band 1, and $1,500,001 in band 2. Both boundaries are tested. Loan amounts are quoted in $50 increments, so the half-open boundary is faithful.
- **Cell keys are `|`-joined band keys in `axes` order.** Reordering `axes` silently invalidates every key in the table. Treat axis order as part of the table's contract; if a table is ever re-cut, regenerate rather than hand-edit.
- **Values are whole percents** (`85`, not `0.85`), matching the source document so a reviewer can diff the YAML against the PDF by eye. `compare_field` is therefore `cltv_pct`, also whole percents.
- **Out-of-range loan amounts are caught by rules, not cells.** The matrix bands span $100,000–$3,000,000; below and above are `ACRA-LA-MIN` / `ACRA-LA-MAX` at priority 5, ahead of the grid at 10. A loan outside the range gets INDETERMINATE from the grid and VIOLATED from the range rule — correct, but only because the range rules exist. Don't delete them.
- **The profile is versioned to the source document** (`acra_dscr_v6_15_2026_v1_1`). When Acra reissues the matrix, add a new profile rather than editing this one; the policy's `version` and `supersedes` carry the change.
- **`policy_type: institutional`** — this is Acra's own program, not a regulatory floor. It belongs in the Certified Client Overlay per ABA §11.1, not in pack semantics.

## 5. Running the tests

`tests/test_acra_eligibility.py` expects the pack at `config/packs/acra_dscr_core/`. It needs `pytest-asyncio`. It does **not** need jaci — only `jazzx_sdk.fabric.canonical`.

The evaluation harness used to verify these artifacts imported the real evaluator modules with one stub (`jazzx_sdk.tools.documents.extraction.structure_region`, pulled in transitively via `finance.structure` and untouched by policy evaluation) and one import-order shim (`import jazzx_sdk.finance` first — `finance.vocabulary` → `periods` → `structure` → `vocabulary` is a real cycle that the package `__init__` resolves by import order). Neither affects the semantics under test, but both are worth knowing if you reproduce it outside a full install.
