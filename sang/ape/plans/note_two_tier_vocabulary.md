# A layered vocabulary: SDK layers, optional domain packs, and a pack's aliases (sonnet-runtime, 2026-10-23, rev 2)

Author: Virendra Mehta

Proposal for the user to review. Nothing here is merged data, built code or a version change.

## Principle

The catalog is pack data. The job writer and the code generator take read names, units and types only from the pack's catalog
(`pack.schemas`, `JtbdTemplate.bound_to_catalog`). Helpers (`rules/lib.py`) are typed against a **base vocabulary** that ships
with the SDK; a pack aliases its terms to base terms, so a helper accepts a pack term through its base term.

## Prior art

- **2.6.1 Ontology build** (kept): JSON Schema catalog in the manifest, tenant reference library (`catalog_reference`, migration 0023),
  field-by-field adoption with `x-source`, catalog extraction into `Proposal(kind="catalog")`, `merge-catalog`, the Ontology page.
- **`plan_pack_ontology_authoring`** left composition (`extends:` a base pack) as a later item; reference ontologies cover reuse.
- **SBP-00** names a Shared Entity Ontology and a Canonical Object Schema among the substrate specifications. Found: only the
  Canonical Object Schema Specification (`aml/Institutional Intelligence/Canonical_Object_Schema_Specification_v1_0.docx`), and it
  specifies the five canonical governance objects and eight derived ones (Policy, Evidence, Decision, Trace, Outcome, Case Context
  ...), which `fabric/canonical` already implements: it is not a vocabulary of parties, money and loans. The Shared Entity Ontology
  document is not in that folder or any docx in it. So the layers below are derived, as agreed.
- **The finance entities already exist in `mortgage-app-ontology`** (`design/`: `jazz_mortgage_ontology_v2`, `los_loan_data`,
  `loan_metrics`, `mortgage_guideline_ontology_v1`, `mortgage_jtbd_ontology_v1`): the `LoanCore`, `Borrower`, `SubjectProperty` names
  of the Acra seed come from it. They are the source for the finance layer's first content, with Acra's terms checked against them.
- The blueprint narrowing chain's rule is the layering rule: a layer only adds; it never changes or widens a lower layer's meaning.

## What is missing in the Ontology flow

1. No alias: adoption copies a name, nothing says "this pack term is that base term".
2. No chain: a pack declares no vocabulary layers, and `x-source` pins only a reference version per field.
3. No SDK-shipped base: references are tenant rows.
4. No re-test on a vocabulary change (`lint_fix` flags a `LIB_VERSION` change, nothing flags a term).
5. No path from a gap to a proposal: W4's `needs_field` names and repeated hand-written code stay in `missing_reads` and the ledger.
6. No way to start a catalog without a document or a reference.

## Shape: a chain

Manifest:

```yaml
vocabulary:
  chain: [jazzx-core@0.1.0, jazzx-finance@0.1.0]   # SDK layers, lowest first; later: pack:<domain-pack>@version
  aliases: aliases.yaml                            # pack term -> a term in the chain (flat, Entity.field both sides)
```

The pack's own catalog is its `catalog:`. **Resolution** walks pack term -> alias -> the chain from the most specific entry to the
lowest; the first layer that defines the term owns it. A pack-only term (no alias, in no layer) is typed by the pack's own catalog.

- **Layers** are SDK data, each a JSON Schema catalog under `jazzx_sdk/vocabulary/<layer>/`, also loadable into the reference
  library so the Ontology page reads each as a reference. `jazzx-core`: party, money, date, address, document. `jazzx-finance`:
  loan, borrower, property, guarantor, collateral, generic metrics. Insurance and the like are later layers.
- **Only adds**: a layer that defines a lower term with another type or unit is refused when the chain is loaded.
- **Cheap to move**: one file per entity under its layer's namespace, and one table, `layers.yaml`, saying which layer owns which
  entity. Aliases name terms, not layers, so moving an entity edits the table and the file, nothing in a pack.
- **Domain extensions** (DSCR, commercial lending, commercial insurance terms) are where a pack is justified: shared by several
  packs, evolving on its own. Not built; the first one is made when a second pack needs the same terms (CRE is the likely trigger),
  and it enters the chain as `pack:<id>@version`.
- **Change**: a rule records the chain versions and terms it reads (as it records `lib_version`); a layer version that changes a term
  flags the rules reading it for re-test.
- **Suggestion loop**: `needs_field` names and repeated code patterns become `Proposal(kind="catalog")` aimed at a layer, reviewed on
  the Ontology page, never merged unreviewed.

## First content (a proposal; not merged)

Derive `jazzx-finance` from `mortgage-app-ontology` and the Acra seed (`loan_application.json`: 54 fields; the last regeneration's
Schema backlog: 295 data names no field holds). Start Acra as the first alias set; no speculative entities.

**Units** (core): `percent` (0-100), `fraction` (0-1), `usd`, `months`, `days`, `count`, `ratio`. **Types**: `string`, `number`,
`integer`, `boolean`, `date`, `enum`.

| Layer | Entity | Terms (type, unit) | Acra alias |
|---|---|---|---|
| core | `Money`, `Address`, `Party`, `DateRange` | amount (number, usd), state (enum), name | pack-only until a rule reads them |
| finance | `Property` | `appraised_value_usd`, `property_type`, `occupancy`, `units`, `is_vacant`, `is_rural`, `is_listed_for_sale`, `last_listed_date`, `lowest_listing_price_usd`, `lease_end_date` | `SubjectProperty.*` |
| finance | `Borrower` | `citizenship`, `entity_type`, `is_first_time_homebuyer`, `credit_score`, `months_since_bankruptcy` | `Borrower.*`, `CreditReport.representative_score` |
| finance | `Loan` | `amount_usd`, `purpose`, `note_rate_percent`, `cltv_percent`, `dscr` (ratio), `channel`, `prepayment_penalty_structure`, `application_date`, `closing_date`, `escrow_status`, `reserves_months`, `reserves_usd` | `LoanCore.*`, `RatioSet.*`, `MortgageLoanInformation.*` |

Pack-only to start: Acra's underwriting flags (`UnderwritingSummary.*`, `CondoProject.*`, `TitleInformation.*`) and derived booleans.
The backlog's top names (calculated DSCR, application date, impound status, reserves basis, last listing date, prepayment term,
entity foreign-owned) are the first suggestions. Acra will guess some layer boundaries wrong; the table above is why that is cheap.

## Generalization

jaci's `config/packs/clinical-intake-core` (healthcare patient intake; `ontology/clinical_intake.yaml`, 9 rules; a synthetic demo)
exists and is different enough (patient, encounter, symptom) to test that core stays domain-neutral and finance does not leak into it:
the second alias set after Acra's, a later `jazzx-health` layer only if it earns one. jaci changes go through sonnet-jaci.

## Order

1. `rules/lib.py` 1.1.1 and the catalog's types in the generator (built).
2. `jazzx-core@0.1.0` and `jazzx-finance@0.1.0` as SDK data, Acra's `aliases.yaml`, the `vocabulary:` key, resolution, the
   only-adds check; loaded through the Ontology page.
3. Re-test flags on a layer change; the suggestion loop from `needs_field`.
