# A two-tier vocabulary: a core one, and a pack's aliases to it (sonnet-runtime, 2026-10-23)

Author: Virendra Mehta

Proposal for the user to review. Nothing here is merged data, built code or a version change.

## Principle

The catalog is pack data. The job writer and the code generator take read names, units and types only from the pack's catalog
(`pack.schemas`, `JtbdTemplate.bound_to_catalog`). Helpers (`rules/lib.py`) are typed against a **core vocabulary**; a pack's
catalog aliases its terms to core terms, so a helper accepts a pack term through its core term.

## What exists (2.6.1 Ontology build)

- A manifest's `catalog:` is JSON Schema 2020-12 (entities under `$defs`); `jazzx_sdk.pack.catalog` reads it as the authored
  ontology and writes it back; `catalog_reads` gives the names, units and types the template and the writers take.
- A tenant **reference library** (`catalog_reference` table, migration 0023; `GET/PUT/DELETE /catalogs/references`), and a
  published pack's catalog readable as `pack:<id>[@version]`.
- **Adoption** (`catalog_adopt`, `POST /packs/{id}/catalog/adopt`): named fields of a reference entity copied into the draft
  field by field, each piece recording `x-source: <reference id>@<version>#<pointer>`; a field that differs is a conflict.
- **Catalog extraction** (`representation=catalog`): candidates from documents classed against the draft's catalog and the chosen
  references (`matched`, `reusable`, `conflicting`, `new`), filed as `Proposal(kind="catalog")`; `merge-catalog` writes the
  accepted ones. Lint: `unused_adopted_field`. Plato's **Ontology page** is this flow (Draft, Reference catalogs, Extract, the
  catalog tree, Proposals).

## What is missing there

1. **No alias.** Adoption copies a name. There is no "this pack term is that core term" (`grep alias` in `pack/catalog*` finds
   none), so nothing resolves a pack term to a helper's type.
2. **No pin.** `x-source` records a reference version per field, but a pack declares no core version.
3. **No global tier.** References are tenant rows; the core would have to be loaded into each tenant, or shipped as SDK data.
4. **No re-test on a core change.** `lint_fix` flags rules recorded at another `LIB_VERSION`; nothing flags a rule coded against a
   term that changed.
5. **No path from a gap to a proposal.** W4's `needs_field` names and repeated hand-written patterns stay in `missing_reads` and the
   ledger; extraction proposes only from documents.
6. **No catalog from nothing.** The page crafts a catalog from a document or a reference; starting one from a seed pack's schema
   needs a document or an upload.

## Shape

- **Core**: a versioned JSON Schema catalog, `jazzx-core@0.1.0`, shipped as SDK data and loadable into the library (so the Ontology
  page reads it as a reference). Entities, field types, units. Financial first.
- **Pack**: manifest `vocabulary: {core: jazzx-core@0.1.0, aliases: aliases.yaml}`; `aliases.yaml` maps pack terms to core terms
  (`SubjectProperty.appraised_value_usd: Property.appraised_value_usd`); a pack-only term has no alias and is allowed.
- **Resolution**: pack term -> core term -> helper. A read is typed by its core term; a pack-only term by the pack's own catalog.
- **Core change**: a rule records the core version and terms it reads (as it records `lib_version`); a core version that
  changes a term flags the rules reading it for re-test, as `lint_fix` does for the library.
- **Suggestion loop**: `needs_field` names and repeated code patterns become `Proposal(kind="catalog")` aimed at the core, shown on
  the Ontology page for review, never merged unreviewed.

## First content, derived from the Acra seed (a proposal; not merged)

Source: `acra_dscr_policy` (`schemas/loan_application.json`: 54 fields; `jtbd_template.yaml` reads and units; `metrics.yaml`) and the
coverage workbook's Schema backlog from the last regeneration (295 data names no field holds). No external specification is
needed; the one that exists (`Canonical_Object_Schema_Specification_v1_0.docx`, in the `aml` checkout) can be compared later.

**Units**: `percent` (0-100), `fraction` (0-1), `usd`, `months`, `days`, `count`, `ratio`. **Types**: `string`, `number`, `integer`,
`boolean`, `date`, `enum`.

| Core entity | Terms (type, unit) | Acra alias |
|---|---|---|
| `Property` | `appraised_value_usd` (number, usd), `property_type` (enum), `occupancy` (enum), `units` (integer, count), `is_vacant`, `is_rural`, `is_mixed_use`, `is_listed_for_sale` (boolean), `last_listed_date` (date), `lowest_listing_price_usd` (number, usd), `state` (enum), `lease_end_date` (date) | `SubjectProperty.*` |
| `Borrower` | `citizenship` (enum), `entity_type` (enum), `is_first_time_homebuyer` (boolean), `credit_score` (integer), `months_since_bankruptcy`, `months_since_short_sale` (integer, months) | `Borrower.*`, `CreditReport.representative_score` |
| `Loan` | `amount_usd` (number, usd), `purpose` (enum), `note_rate_percent` (number, percent), `cltv_percent` (number, percent), `dscr` (number, ratio), `channel` (enum), `prepayment_penalty_structure` (enum), `is_interest_only` (boolean), `application_date`, `closing_date` (date), `escrow_status` (enum), `reserves_months` (integer, months), `reserves_usd` (number, usd) | `LoanCore.*`, `RatioSet.*`, `MortgageLoanInformation.*` |

Pack-only to start: the Acra underwriting flags (`UnderwritingSummary.*`, `CondoProject.*`, `TitleInformation.*`) and the derived
booleans (`tradelines_meet_requirement`, `entity_documents_complete`). The `needs_field` backlog's top names (calculated DSCR,
application date, impound status, reserves basis, last listing date, prepayment term, entity foreign-owned) are the first
suggestions for core terms; nothing speculative beyond them.

## Generalization

jaci has a second domain: `config/packs/clinical-intake-core` (healthcare patient intake: `ontology/clinical_intake.yaml`, 9 rules in
`policies/core.yaml`, a conversational profile; demo, synthetic patients). It is different enough (patient, encounter, symptom) to
test that the core stays financial and the alias layer carries a second domain; it is a demo with a YAML ontology, so its
terms would be the second alias set after Acra's, not core content. jaci changes go through sonnet-jaci.

## Order

1. `rules/lib.py` helpers at `LIB_VERSION` 1.1.1 (decided), `type_problems` over the catalog's types, the code generator reading the
   catalog (decided).
2. `jazzx-core@0.1.0` and `aliases.yaml` for Acra, loaded through the Ontology page; the `vocabulary:` manifest key and resolution.
3. Re-test flags on a core change; the suggestion loop from `needs_field`.
