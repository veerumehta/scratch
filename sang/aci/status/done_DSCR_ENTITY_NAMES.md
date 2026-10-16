# DSCR pack: fact names moved to the mortgage ontology's `Entity.field`

- **Author:** Virendra Mehta <virendra.mehta@jazzx.ai>
- **Repo:** jaci (`config/packs/acra_dscr_policy`), synced to japes `plato/data/seed_packs/acra_dscr_policy`
- **Landed:** jaci `4e3e87a` (acra-dscr-policy 0.2.17); japes seed sync `0635663c` on v2.6.2 (local, unpushed)
- **Plan:** `.scratch/sang/ape/plans/plan_document_registry_and_job_shape.md`, section 4 (D2)
- **Status:** the names below were accepted **for now** (2026-10-13). They are provisional and can be revisited.

The Acra DSCR pack used to name its facts with short local names (`fico`, `cltv_pct`). It now
uses the production mortgage ontology's `Entity.field` names, as Acra's hand-built job sets do
(`CreditReport.representative_score`, `LoanCore.cltv_percent`). So jobs, rules, generated code and
exports can be compared key for key. This was a one-pass rename with no aliases for the old names:
the pack's rules, metrics, input and document schemas, job template, document registry and gold
cases all use the new names.

**Sources, in priority order:**
1. **Acra jobs:** the `Entity.field` keys in Acra's hand-built job sets (Standard and Platinum).
2. **Ontology:** `mortgage_ontology_v2.json` from `mortgage-app-ontology` (45 entities, 631 fields), the production copy.
3. **Provisional:** no field in either source fits, so the name is new: the most plausible entity plus a field named after the fact.

## The names (49 facts and 2 derived metrics)

| Old name | New name | Source |
|---|---|---|
| `loan_amount` | `LoanCore.total_loan_amount_usd` | Acra jobs |
| `loan_purpose` | `LoanCore.loan_purpose` | Acra jobs |
| `property_type` | `SubjectProperty.property_type` | Acra jobs |
| `property_address` | `SubjectProperty.address` | Acra jobs |
| `property_state` | `SubjectProperty.state` | Acra jobs (not in ontology) |
| `property_value` | `SubjectProperty.appraised_value_usd` | Acra jobs |
| `fico` | `CreditReport.representative_score` | Acra jobs |
| `citizenship_type` | `Borrower.citizenship_status` | Acra jobs |
| `gross_rental_income` | `RatioSet.total_monthly_income_usd` | Acra jobs |
| `pitia` | `RatioSet.total_monthly_obligation_usd` | Acra jobs |
| `reserves_months` | `RatioSet.reserves_months` | Acra jobs |
| `occupancy_subtype` | `SubjectProperty.occupancy_subtype` | **provisional** |
| `dscr_documentation_type` | `LoanCore.dscr_qualification_method` | Acra jobs (not in ontology) |
| `escrow_waiver_requested` | `LoanCore.is_escrow_waived` | Acra jobs |
| `product_is_interest_only` | `MortgageLoanInformation.is_interest_only` | ontology |
| `borrower_entity_type` | `Borrower.entity_type` | Acra jobs (not in ontology) |
| `entity_is_borrower_1` | `Borrower.is_entity_borrower_1` | **provisional** |
| `entity_documents_complete` | `Borrower.entity_documents_complete` | **provisional** |
| `title_multiple_transfers_among_related_parties` | `TitleInformation.has_related_party_transfers` | **provisional** |
| `duplicate_ssn_cleared` | `UnderwritingSummary.duplicate_ssn_cleared` | **provisional** |
| `broker_nmls_verified` | `UnderwritingSummary.broker_nmls_verified` | **provisional** |
| `loan_officer_nmls_verified` | `UnderwritingSummary.loan_officer_nmls_verified` | **provisional** |
| `property_currently_listed_for_sale` | `SubjectProperty.is_listed_for_sale` | **provisional** |
| `hoa_reserves_adequate` | `CondoProject.hoa_reserves_adequate` | **provisional** |
| `hoa_litigation_pending` | `CondoProject.hoa_litigation_pending` | **provisional** |
| `prepayment_penalty_requested` | `LoanCore.prepayment_penalty_structure` | **provisional** |
| `residential_unit_count` | `SubjectProperty.number_of_units` | Acra jobs |
| `interest_rate` | `LoanCore.note_rate_percent` | Acra jobs |
| `channel` | `LoanCore.channel` | Acra jobs |
| `housing_history` | `CreditReport.housing_history_rating` | **provisional** |
| `mortgage_history_0x30x24` | `CreditReport.mortgage_0x30x24` | **provisional** |
| `current_lease_in_place` | `SubjectProperty.has_current_lease` | **provisional** |
| `bankruptcy_or_foreclosure` | `Borrower.has_bankruptcy_or_foreclosure` | **provisional** |
| `months_since_bankruptcy_or_foreclosure` | `Borrower.months_since_bankruptcy_or_foreclosure` | **provisional** |
| `short_sale_dil_or_modification` | `Borrower.has_short_sale_dil_or_modification` | **provisional** |
| `months_since_short_sale_dil_or_modification` | `Borrower.months_since_short_sale_dil_or_modification` | **provisional** |
| `credit_score_count` | `CreditReport.score_count` | **provisional** |
| `tradelines_meet_requirement` | `CreditReport.tradelines_meet_requirement` | **provisional** |
| `seller_concession_pct` | `LoanCore.seller_concession_percent` | **provisional** |
| `ownership_months` | `SubjectProperty.ownership_months` | **provisional** |
| `mixed_use` | `SubjectProperty.is_mixed_use` | Acra jobs |
| `interest_only_10_40` | `LoanCore.is_interest_only_10_40` | **provisional** |
| `first_time_homebuyer` | `Borrower.is_first_time_homebuyer` | Acra jobs |
| `rural_property` | `SubjectProperty.is_rural` | **provisional** |
| `vacant_property` | `SubjectProperty.is_vacant` | **provisional** |
| `delayed_financing` | `LoanCore.is_delayed_financing` | **provisional** |
| `listed_for_sale_last_6_months` | `SubjectProperty.listed_for_sale_last_6_months` | **provisional** |
| `cltv_pct` | `LoanCore.cltv_percent` | Acra jobs |
| `dscr` | `RatioSet.dscr` | **provisional** |

**Derived metrics** (`metrics.yaml`):

| Old name | New name | Source |
|---|---|---|
| `cltv_pct` | `LoanCore.cltv_percent` | Acra jobs |
| `dscr` | `RatioSet.dscr` | **provisional** |

**Kept as they were:**
- **Identifiers:** `loan_id` (the run's subject), `program_id`, `submission_date`, `source_system`.
- **Names no rule reads:** `borrower_name`, `sponsor_name`, `loan_officer`. The ontology has no single field for any of them.
- **Profile keys** such as `reserves_months_fthb` and `max_cltv_grid`. These name thresholds, not facts.
- **The gold cases' `expected` block** (`cltv_pct`, `binding_cap_pct`, ...). These are jaci's own assertion names.
- **The evidence fixtures' payload fields** (`fixtures/appraisal.json`, `fixtures/credit_report.json`). The assessment doesn't read them, so they're left for a separate decision.

**Values are unchanged.** Every new name holds the same value, in the same unit, as the old one.
Coded values stay the pack's own, e.g. `condotel`, `itin`, `foreign_national`, `unspecified`. The ontology's enums differ for `loan_purpose`, `property_type`, `citizenship_type` and `channel`, and some pack values have no ontology member.

## Decisions taken for now (open to revisit)

1. **28 provisional names.** These have no ontology field, so they are new names.
   - Most are yes/no facts or month counts the pack works out itself, e.g. `UnderwritingSummary.duplicate_ssn_cleared` and `Borrower.months_since_bankruptcy_or_foreclosure`.
   - Where the ontology does have a related field, using it would change the value, not just the name:
     - **Month counts:** the ontology holds bankruptcy and foreclosure *dates*.
     - **Seller concessions:** Acra's metric is in dollars (`ClosingFee.seller_paid_at_closing_usd`), not a percent of the price.
     - **Score count:** the ontology has the `CreditReport.scores` array, not a count.
     - **HOA facts:** the ontology uses `CondoProject` enums, not booleans.
2. **Ontology fields replaced three earlier names** used in the japes rename test:
   - `loan_amount` → `LoanCore.total_loan_amount_usd`, not `LoanCore.loan_amount`
   - `property_value` → `SubjectProperty.appraised_value_usd`, not `SubjectProperty.value`
   - `interest_rate` → `LoanCore.note_rate_percent`, not `LoanCore.interest_rate`
3. **`SubjectProperty.state`.** This is Acra's own spelling. The ontology has the state only nested in `SubjectProperty.address`. 19 rules read it.
4. **`pitia` → `RatioSet.total_monthly_obligation_usd`.** This is the denominator of Acra's DSCR jobs. The alternative was `proposed_housing_expense_usd`.
5. **`cltv_pct` → `LoanCore.cltv_percent`.** The ontology defines this as a stored field. A loan record that also supplies it would clash with the pack's computed value, and the computed value should win. The pack's formula is really a first-lien LTV.
6. **`Borrower.entity_type`, `Borrower.is_entity` and `LoanCore.dscr_qualification_method`.** Acra's jobs name these, but the ontology lacks them. They're candidates for the catalog.

## Acceptance criteria: verified

- **Same results before and after.** Every in-process assessment the DSCR and unit tests run (93 distinct loans, including the five gold cases) was recorded before and after the rename. All 93 give identical verdicts, reasons and derived values once old names are translated to new.
  - Only one thing changed: where a rule names several fields (e.g. `property_state, property_type`), the list is sorted by name, so the new names sort it differently. The same fields are named.
- **Test suite:** DSCR, unit, integration and eval tests: 1075 passed, 4 skipped, 2 xfailed.
- **Model and schemas:**
  - In code, `LoanApplication` keeps its old field names. As JSON it reads and writes the new ones, and it accepts either on input. The mapping is `ENTITY_NAMES` in `src/jaci/scenarios/dscr/schemas/dscr_schemas.py`.
  - `schemas/loan_application.json` and `schemas/loan_document_fields.json` were regenerated from that model.
- **No old names left** in any rule field, ratio numerator or denominator, matrix comparison, metric, manifest field reference, job-template `reads` or `units`, registry `yields`, or gold-case record.

## Follow-ups

- **japes tests still use flat DSCR records.** With the seed synced, about 100 japes tests fail: `tests/data/dscr_gold_cases`, inline loans, and `test_dotted_fact_names.py`, which renames from the flat seed. `sonnet-runtime` is updating them to the new names; Plato's runtime isn't affected.
- **Older notes in `ENCODING_NOTES.md`** keep the old names. A new 0.2.17 paragraph explains the rename.
- **The evidence fixtures' payload fields** wait on a decision. The draft targets are e.g. `fico_score` → `CreditReport.representative_score` and `appraised_value` → `AppraisalSummary.appraised_value_usd`.
- **Extraction targets.** Now that the registry's `yields` are `Entity.field` names, the job set's extraction targets can appear; that's the second regeneration run.
