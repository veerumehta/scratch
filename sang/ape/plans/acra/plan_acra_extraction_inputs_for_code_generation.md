# Acra code generation: the extraction side of the gap

Author: Virendra Mehta <virendra.mehta@jazzx.ai>. Owner: sonnet-docs. Status: approved by opus-xrepo; P1 to P4 only, no spend. Branch `acra-extraction` (cut from plato). Field names and document ids agreed with sonnet-packs. No provider call was made; every claim below is read from files, marked **[registry]** (seed pack `document_types.yaml`), **[schema]** (`schemas/loan_document_fields.json`, identical to jaci's copy, pack 0.3.1), **[ledger]** (`scripts/local/coverage/regen_5/coverage.json`) or **[code]** (SDK source).

Goal: raise "coded" from 52% toward 93% (`note_acra_code_generation_baseline_and_std_needs_2026-11-19.md`). This plan is the part that supplies the inputs coded rules read: raw fields, dates and loan-record facts. Derived figures (`cltv_percent`, `reserves_months`, DSCR, months since an event) are std and derived-field declarations, owned by sonnet-runtime. Seed-pack data edits are sonnet-packs' (through jaci first); this plan proposes names and sources and does not edit them.

## 1. How a field gets supplied (the mechanism the plan works inside)

- A field reaches a rule when some live document type lists it in `yields` [registry, `supplied_fields()` in `pack/document_registry.py`]; a document that states `yields` is read for those fields only [code, `taxonomy()`]. So a schema field with no yielding document is never extracted, whatever the schema says.
- The caller's own values (`ProcessingTurn.submitted`) are never replaced by a document read [code, `pipelines/document/process.py` and `reconcile.py`]. That is the loan-record path, and it needs no document.
- Per-field source preference between documents is `ProcessingTurn.precedence` (field to document classes, best first).

## 2. The baseline's schema

The regen-5 baseline ran on seed pack 0.2.18 (47 schema fields); pack 0.3.1 added 14, including the HELOC limit and balance, subordinate financing type, lease rent, listing price and LTV. Against 0.3.1 the schema [schema] holds `LoanCore.heloc_limit_usd`, `heloc_balance_usd`, `subordinate_financing_type`, `note_rate_percent`, `lease_rent_usd`, `lowest_recent_listing_price_usd`, `is_escrow_waived`, `channel`, `prepayment_penalty_structure`, `dscr_qualification_method`, `is_interest_only`, `occupancy_subtype`, `is_first_time_homebuyer`, `listed_for_sale_last_6_months`, `entity_documents_complete`, `tradelines_meet_requirement` and the ARM caps. Of its 67 properties, **41 are yielded by no document type [registry]** (sonnet-packs counts 38 of 61 dotted names). The gap is mostly `yields` and missing document types, not missing schema fields. `LoanCore.cltv_percent` is not a schema field (only `ltv_percent` is): it needs a derived declaration, not extraction.

## 3. Item by item (each checked against the registry)

Registry today: 17 types. Yielding: `loan_application` (12 fields), `appraisal_report` (8), `lease_agreement` (3), `rent_roll` (2), `credit_report` (6), `entity_documents` (1), `title_commitment` (2), `hoa_questionnaire` (1), `listing_history` (1). Yielding nothing: `bank_statement`, `hazard_insurance`, and the five closing documents. No type for the Note, the closing disclosure or settlement statement, a purchase contract, a rent schedule (1007/1025), a tax certificate, a HELOC statement or a mortgage statement.

### 3a. Raw inputs

| Input | Schema | Yielded today | Proposed field (agree with sonnet-packs) | Source documents |
|---|---|---|---|---|
| Purchase price | absent | no | `SubjectProperty.purchase_price_usd` | `loan_application` (loan and property section), new `purchase_contract`, new `closing_disclosure`; precedence closing disclosure, contract, 1003 |
| Subordinate lien amounts | type, HELOC limit and balance present; no amount for a non-HELOC lien | no | `LoanCore.subordinate_lien_amounts_usd` (list of numbers, so `loan_to_value(liens, values)` takes it whole) | `title_commitment` (liens of record), `credit_report` (mortgage tradelines), `loan_application` (liabilities); HELOC limit and balance from new `heloc_statement`; type from any of them |
| Annual taxes | absent | no | `SubjectProperty.annual_property_tax_usd` | new `tax_certificate`, `appraisal_report`, `closing_disclosure` (escrow), `title_commitment` |
| Property insurance (annual) | absent | `hazard_insurance` yields nothing | `SubjectProperty.annual_insurance_premium_usd` | `hazard_insurance` (declarations page), `closing_disclosure` |
| Association dues (annual) | absent | no | `SubjectProperty.annual_association_dues_usd` | `hoa_questionnaire`, `appraisal_report`, new `hoa_statement` |
| First payment under the Note | absent | no | `LoanCore.first_payment_amount_usd` | new `promissory_note`, `closing_disclosure` |
| Note rate | present, unyielded | no | `LoanCore.note_rate_percent` (exists) | `promissory_note`, `closing_disclosure` |
| Term, interest-only term | absent | no | `LoanCore.loan_term_months`, `LoanCore.interest_only_term_months` | `promissory_note`, `closing_disclosure` |
| Bureau scores | `representative_score` only | yes (`credit_report`) | `CreditReport.bureau_scores` (list of stated scores; `middle_score` needs them) | `credit_report` |
| Market rent (1007, 1025) | absent (`lease_rent_usd` is the lease, unyielded) | no | `SubjectProperty.market_rent_usd` | new `rent_schedule` (child of `appraisal_report`; forms 1007 and 1025); `lease_agreement` should yield the existing `lease_rent_usd` |
| Verified assets | absent | `bank_statement` yields nothing | `Borrower.asset_accounts` (list: institution, account type, balance, statement date), not a bare total: which assets count is policy, so extraction supplies the accounts and std totals them | `bank_statement`, new `asset_statement` (retirement, brokerage) |

Periods stay as the document states them (the first payment and rents are monthly, taxes, insurance and dues annual); each field's description says which, and the derived declarations normalize with `monthly`. HELOC stays in its own fields (STD-10.7 takes the greater of limit and balance).

### 3b. Dates for `months_between`

Each is an ISO date field; the months-since fields become derived through `months_between(date, as_of)`. The existing integer `Borrower.months_since_bankruptcy_or_foreclosure` and `months_since_short_sale_dil_or_modification` (2 jobs each in the unsupplied list [ledger]) are then derived, not read.

| Date | Proposed field | Source |
|---|---|---|
| Application | `LoanCore.application_date` | loan record; `loan_application` signature date as fallback |
| Closing | `LoanCore.closing_date` | `closing_disclosure`, `promissory_note`; loan record |
| Last listed | `SubjectProperty.last_listed_date` | `listing_history`; derives `listed_for_sale_last_6_months` |
| Lease end | `SubjectProperty.lease_end_date` | `lease_agreement` |
| Bankruptcy, foreclosure | `Borrower.bankruptcy_date`, `Borrower.foreclosure_date` | `credit_report` public records |
| Short sale, deed in lieu | `Borrower.short_sale_dil_date` | `credit_report`; mortgage history |

### 3c. Facts rules read (document or loan record)

| Fact | Unsupplied reads [ledger] | Proposed source |
|---|---|---|
| `is_first_time_homebuyer` | 11 jobs | loan record; fallback derived from `loan_application` declarations (no ownership in three years) |
| `listed_for_sale_last_6_months` | 16 | derived from `last_listed_date` (3b); document `listing_history` |
| `occupancy_subtype` | 11 | loan record; `loan_application` occupancy and `appraisal_report` occupant as evidence |
| `is_escrow_waived` | 11 | loan record; `closing_disclosure` escrow section as evidence |
| `channel` | 6 | loan record only (no document states the channel) |
| `prepayment_penalty_structure` | 8 | `promissory_note` or prepayment rider (new type `prepayment_addendum`); loan record |
| `dscr_qualification_method` | 10 | loan record (program and underwriting choice); no document |
| `is_interest_only` | 10 | derived: `interest_only_term_months` above zero; document `promissory_note` |
| `entity_documents_complete` | 3 | derived from the package completeness report (`DocumentAgent` already reports `missing` documents against `required`), not extracted |
| `tradelines_meet_requirement` | 3 | `CreditReport.tradelines` (list: count, age, status) from `credit_report`; std counts against the requirement |

## 4. What I build (SDK, my paths only)

Nothing above needs a new pipeline. The SDK work is to prove the existing extraction carries these field shapes, then fix what does not:

- **P1, shapes (fakes, no provider).** Found and fixed: the chunk merge counted a default (`False`, `0`) as a report, so an earlier chunk's default hid a later chunk's value (committed on `acra-extraction`). Remaining: Tests that `DocumentAgent.extract` and `extract_located` handle: a list of numbers, a list of objects (accounts, tradelines; `Borrower.reo_properties` is the precedent in the schema), an ISO date, money as `Decimal`-safe numbers, and a missing value staying unknown rather than 0 (note `ownership_months` and the months fields default to 0 in the current schema: a default of 0 reads as "none", which is wrong for an unsupplied field; sonnet-packs agreed: unsupplied numbers default to `null`). Each failing shape gets a fix in `tools/documents/` with a test that failed first.
- **P2, reconcile.** `precedence` entries for each new field, as pack data in the turn; verify with fakes that two documents disagreeing on purchase price or taxes surface as a conflict and that a `submitted` loan-record value is never replaced.
- **P3, loan-record path.** A fakes e2e: a turn with `submitted` holding channel, first-time buyer, escrow waived and DSCR method reaches the rule context unreplaced, with no document naming them. Document the caller contract in the pipeline's docstring.
- **P4, measure (done, no spend).** `scripts/local/acra/extraction/field_sources.yaml` gives each of the 19 unsupplied reads in regen-5 a source, and `check_field_sources.py <coverage.json>` checks it against the report: all 19 covered. By source: 11 derived (96 job-reads), 7 loan record (52), 1 document (8). So extraction alone moves 1 field and 16 new raw fields (listed by the script) feed the 11 derived ones; the larger lever is the derived-field declarations (pack data) and loan-record supply, not more document reads. Two raw fields beyond the agreed list were needed: `SubjectProperty.acquisition_date` (ownership months) and `CreditReport.monthly_liabilities_usd` (total monthly obligation); both agreed with sonnet-packs (`acquisition_date` is the closing or vesting date of the borrower's acquisition; `monthly_liabilities_usd` is monthly, null if not stated) and go in the jaci schema edit. Declaration notes from sonnet-packs: a derived declaration replaces the stored field for its rules, not beside it; reserves divide the annual amounts by 12 once in one named place and a missing component gives unknown, passing `None` (not 0) for dues; the tradelines rule needs a clause-confirmed std function. Fields for the uncoded derived jobs (purchase price, market rent, taxes, insurance, dues, assets) are on top of these.
- **Not mine, proposed only:** the schema and `document_types.yaml` edits (sonnet-packs, jaci first), the std functions and derived declarations (sonnet-runtime), the code prompt and the regenerate loop (sonnet-packs).

## 5. Agreements needed before building

1. Done (sonnet-packs, schema and `document_types.yaml` edits go through jaci, from sonnet-jaci): the field names in section 3 and the new document types (`purchase_contract`, `closing_disclosure`, `promissory_note`, `rent_schedule`, `tax_certificate`, `heloc_statement`, `hoa_statement`, `asset_statement`, `prepayment_addendum`), their mapping to the Master Taxonomy ids (theirs, from the taxonomy workbook), and `null` defaults.
2. Done (sonnet-runtime): own branch from `plato`, folded in before the squash. They provide functions only (`loan_to_value`, `months_between`, `pitia`, `dscr`, `middle_score`); the derived-declaration names are pack data, sonnet-packs'. My field names stay the extraction schema's own.
3. The user: any live extraction on synthetic or loan documents to prove a field (a typed figure per run). The plan has none.

## 6. Residuals and unknowns

- Whether the classifier separates a 1007 or 1025 from the appraisal it travels with is not checked (needs cues, not a run).
- Which documents Acra's real files carry for each new type is unchecked (no loan file was opened).
- The 41 unyielded fields include ARM caps and others no job reads; only those the 72 coded and 39 uncoded-by-extraction jobs read matter, and that join is the P4 output.
