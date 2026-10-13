# Document registry and job shape: the config that lets jobs line up with a hand-built set

Plan, opus-xrepo, 2026-10-12. Status: written, not started. Owner: sonnet-runtime builds the SDK and Plato parts; the
Acra seed data goes through the jaci session (the seed is `SYNCED_FROM` jaci). Decisions owed are in section 8.

## 1. Why

Comparing our extracted job sets with Acra's hand-built ones (`plans/note_acra_jtbd_rules_review.md`) showed
that the content agrees (97% matched) but the shape does not. The gaps trace to config the pack lacks:

- **Documents.** Three unconnected vocabularies in the Acra seed: the classifier taxonomy
  (`document_agent.yaml`, 15 labels), rule evidence types (`evidence_types.yaml`, 10 ids) and nothing in the
  job template, so the writer names documents as free text. Acra's 123 jobs name about 350 distinct
  "reference documents" as free text, with variants of the same document ("Appraisal", "Appraisal
  Report", "Appraisal / MLS"; case variants of "Lock Confirmation"). Some are not documents at all: the
  most cited, "LOS transmittal (1008)" with 35 citations, is a system record, and some are conditions
  (`CreditReport.representative_score >= 640`). Many have no classifier class: Note, Closing
  Disclosure, 1008, lock confirmation, Form 1007/1025, passport, power of attorney, business-purpose
  attestation, rent-loss insurance.
- **Entities.** Acra's jobs read an entity model: LoanCore (68 jobs), Borrower (55), SubjectProperty
  (34), CreditReport (29), RatioSet (27), Asset, RealEstateOwned, Liability and others. Their metric
  keys look like `LoanCore.cltv_percent`. The Acra seed reads flat facts (`schemas/loan_application.json`
  as `conductor.input_schema`, e.g. `cltv_pct`, `fico`), so the template's `entities` and `metric_keys`
  stay empty.
- **Names.** Acra uses our 11 section names but names jobs by topic family: BET, DSCR, LPE and PPT
  under Loan Program Eligibility, BOR and FN under Identification Requirements. `MnemonicRules.prefixes`
  allows one prefix per section (`jtbd_shape.py`).
- **Variants.** Every Acra job carries five investor blocks (COMMON, FNMA, FHLMC, FHA, VA); the four
  agency blocks say "no change", inherited structure. Our programs (Standard and Platinum) are the real
  variant dimension.
- **Kind.** Nothing in the template says what kind of job a job is, so the grain drifts. Acra's grain is
  one decision per job; ours bundles.
- **Extraction targets.** 52 Acra jobs name an entity to extract and a mode (47 `ASK_USER`, 5
  `AUTO_APPROVE`). We write none.
- **Determinations.** Conditions such as "any borrower is a Foreign National" recur inside job text
  instead of being declared once.

Mortgage section names are one domain's instance. Everything below is pack data with neutral defaults;
nothing names a client or a repo.

## 2. Prior art (read before building)

| Piece | Where | State |
|---|---|---|
| Ontology plan: JSON Schema catalog, reference library, `catalog` extraction and proposals, merge, the tab | `plans/plan_pack_ontology_authoring.md` | phases A-E built on v2.6.1 (2026-10-07) |
| `JtbdTemplate` (`sections`, `section_types`, `mnemonics`, `roles`, `entities`, `metric_keys`, `evidence_types`, `units`, `requirement_template`), `bound_to_catalog` | `pipelines/policy/jtbd.py` | built; `evidence_types` is a bare id list |
| `MnemonicRules` | `pipelines/policy/jtbd_shape.py` | one prefix per section |
| Classifier taxonomy with levels, `classify_path`, `class_fields` | `agents/document/spec.py`, `agent.py` | built |
| **The production mortgage ontology family (primary reference)** | `mortgage-app-ontology` `main` `11361c9` (2026-09-15, has a production deploy workflow), `common/resources/ontologies/` | see section 2b |
| An external Acra document taxonomy: 485 types, 16 categories, cues, aliases, condition codes, PII markers | `status/IMDOC_ACRA_TAXONOMY_FOR_DSCR.md`; removed from that repo's tree in `ffa034a` (now read from Knowledge Hub), recoverable from `ffa034a^` | secondary reference, for gaps |
| Job set readiness checks, contract as pack data | `plans/plan_jtbdset_readiness.md` | routed, not built |
| Job ledger: jobs, `computable_checks`, `missing_reads`, coverage | `pack/ledger.py` | built |

## 2b. The production ontology as the reference (checked 2026-10-12)

The production family is the right source; ci-spread-core was never the DSCR basis (the Acra seed has
no catalog, and the Ontology work referenced the mortgage copies).

**Entities.** `mortgage_ontology_v2.json` has 45 entities and 631 fields. The copies elsewhere
diverge: macer has 39/424, mortgage-app 49/693 (the extras are user and invitation entities, not
needed) and policy-workbench 49/690.

The hand-built Acra set resolves against production:
- all 15 of its entities exist;
- 44 of its 47 metric keys resolve;
- the other 3 use filtered or nested paths (`Liability[is_subject_property_lien=True].monthly_payment_usd`,
  `RealEstateOwned[is_subject_property=True].gross_rental_income_usd`,
  `LoanCore.down_payment.percent_of_purchase_price`). D2 must say whether a catalog read may
  carry a filter, or whether those become derived fields (recommended: derived fields, keeping
  reads plain).

**Documents.** `document_classification_ontology.json` has 23 types, 406 subtypes and 224
sub-subtypes. It covers most of what Acra's jobs cite: 1003, ClosingDisclosure, 1007, 1025,
Passport, PowerOfAttorney, TitleCommitment, BankStatement, CreditReport, the appraisal family,
LockConfirmation, RentalAgreement, UnderwritingTransmittal (the 1008),
HomeownersAssociationCertification, PropertyInsuranceBinder and ArticlesOfIncorporation.

It lacks the investor and entity documents DSCR needs: operating agreement, certificate of good
standing or formation, EIN letter, MLS or listing history, business-purpose attestation, rent roll
and rent-loss insurance. The secondary Acra list (its borrowing-entity category) fills those, as
`new` registry entries with their source recorded.

**The rest of the family** maps onto planned work:

| File | Use |
|---|---|
| `condition_ontology.json` 2.1.0 | timing, responsible party and resolution vocabularies for typed conditions (pack data), the `AdjudicationAgent` condition gap |
| `finding_ontology.json` 1.4.0 | outcome statuses already match ours (PASS, FAIL, CONDITIONAL, NOT_APPLICABLE); facts and observations to compare with `Decision` |
| `mortgage_jtbd_ontology_v1.json` 1.0.0 | field names for D3/D4: program requirements, entity and document types, condition mapping, timing rules |
| `reverse_document_mapping_ontology.json` | which document sections feed which fields: a source for the registry's `yields` |
| `mortgage_guideline_ontology_v1.json` | guideline, program and file roles: compare in the guideline release plan |

`upload_mortgage_references.py` adds the production copy (`mortgage-prod`) as the first reference.

## 2a. Posture: tolerant first (the user, 2026-10-12)

Everything here is optional and advisory at first:

- A pack without a registry, catalog, kinds or families works exactly as today.
- Findings are warnings, never publish blockers: stray ids, vanished ids, a job without a kind, and
  grain.
- Where the writer meets a document or field the pack does not declare, it keeps the name, marks it
  undeclared, and proposes it as a new registry or catalog entry, rather than dropping it or
  failing.
- A pack can raise any finding to an error later with `strict:` in its template.

## 3. D1. Document registry (the anchor)

- **The registry.** A pack declares one registry, `document_types.yaml`, named in the manifest. Each
  entry:
  - `id` and `label`, with `aliases` and an optional `parent` (category), which gives the classifier
    its levels;
  - `kind`: `borrower_supplied`, `third_party`, `closing`, `system_record` or `other`;
  - `cues`, the classifier description;
  - `yields`: the catalog fields the document can supply, as `Entity.field` or flat names;
  - `valid_for_days`, optional staleness;
  - `sensitive`, optional.
- **What derives from it:**
  - **Classifier:** `DocumentAgentSpec.taxonomy` comes from the registry when the pack declares one.
    `document_agent.yaml` keeps only its thresholds; a pack without a registry works as today.
  - **Evidence types:** `Pack.evidence_types` and the job template's `evidence_types` are registry
    ids. Lint warns about an id a rule or job names that the registry lacks.
  - **Job writer:** the writer is given the registry's ids, labels and kinds. A job's documents are a
    list of ids where they match; otherwise the name is kept, marked undeclared, and proposed for
    the registry. "Reference Documents" in the requirement text is rendered from labels, grouped
    by `parent`. A `system_record` is shown under its own heading, not as a document to request.
  - **Ledger:** each job lists its documents. Coverage adds two gaps: a document no classifier class
    can recognise, and a fact no document `yields`. These sit alongside `missing_reads`.
  - **Later:** conditions and release rules name registry ids, out of scope here.
- **Building it.** A registry is pulled by need from references, like the catalog (the Ontology
  plan's principle):
  - an extraction pass over the policies proposes the documents they name;
  - an import pass takes the references the documents cited in a hand-built job set;
  - each candidate is matched to a reference taxonomy (uploaded into the tenant reference library,
    which the Ontology work built) and proposed `reuse`, `new` or `alias of`;
  - a person reviews in the existing proposal store and merge path.
- **Ids are stable across versions.** These rules apply to registry ids, and to catalog field ids
  and job mnemonics, which D2 and D3 hold to the same:
  - an id is never reused for a different document;
  - a renamed id keeps the old one in `aliases`;
  - a retired id is marked `retired: true` with an optional `replaced_by`, never deleted.
  - Lint across two pack versions (the draft against the last published) warns about an id that
    vanished without a successor. References elsewhere (rules, jobs, gold cases, corrections) resolve through
    aliases.
- **Provenance.** An entry adopted from a reference records `x-source: <reference>@<version>#<id>`,
  as catalog fields do.
- **Verify:**
  - the seed with a registry classifies the Acra appraisal as before;
  - deleting an id in a draft is a lint warning, while renaming one with an alias is not;
  - a job written with the registry names only ids;
  - lint flags a stray id;
  - coverage shows the two new gaps on the trial pack.

## 4. D2. Entity catalog for the Acra seed (mostly running existing tools)

- Run the Ontology tab's catalog extraction on the two Acra guidelines, with the mortgage reference
  copies as references, to build `catalog.schema.json` holding only what the documents need.
- **Entity names are the code vocabulary** (the user, 2026-10-12). Rules, generated code, jobs'
  metric keys and the export all use `Entity.field`, as the hand-built set does (`LoanCore.cltv_percent`,
  `CreditReport.representative_score`), so comparison and export match key for key.
- **Migrate the hand-built seed only; regenerate everything generated** (the user, 2026-10-12). We are
  in the dev phase, so there is no compatibility layer.
  - **Migrated** with a one-off mapping table (a script, not SDK code), moving flat facts (`cltv_pct`,
    `fico`) to entity fields with their units: the hand-built DSCR seed's rules, metrics, profiles,
    input schema, fixtures and gold cases.
  - **Discarded, not migrated:** generated data, meaning the trial pack `acra-ledger-trial`,
    extraction runs and proposals, drafts made from them, and coverage and comparison outputs.
  - **Regenerated** from the Acra guidelines once D1-D3 land.
  - **Kept:** today's numbers, as the baseline the regenerated set is measured against (68/49 jobs,
    97% matched, partial 41/123 Standard, code 40%, 50% with segment code, lacks data 60%; in
    `note_acra_jtbd_rules_review.md` and `ape/local/coverage/`).
- **The skew of the hand-built ontology stays in the catalog.** Rules name fields; the catalog says
  which entity a field lives in. Re-cutting an entity later is a catalog change plus D1's stable-id
  alias rule, not a code rewrite.
- `bound_to_catalog` then gives the writer `entities` and `metric_keys`.
- **SDK check:** assessment, the fact catalog, lint, the Z3 compiler, the python executor and derived
  metrics all accept dotted `Entity.field` reads (the Ontology work moved the catalog to JSON
  Schema; this checks every reader of a fact name). Whatever does not accept them is the SDK change
  in this phase.
- **Ownership:** the jaci session commits the seed (it is `SYNCED_FROM` jaci); japes changes only
  where a reader refuses dotted names.
- **Verify:**
  - the DSCR seed's assessments give the same verdicts, reasons and derived values on every fixture
    and gold case, before and after, compared through the mapping table;
  - a rewritten job names `Entity.field` metric keys;
  - the aligned comparison against the hand-built set matches metric keys directly.

## 5. D3. Job kind and grain

- **`JtbdTemplate.kinds`** (pack data, neutral default), each kind with a description and what it
  maps to:

| Kind | Maps to in code |
|---|---|
| `determination` (a named fact about the case, e.g. "a borrower is a foreign national") | a derived field |
| `limit` (a cap, threshold or matrix) | a threshold or matrix rule in pack tables |
| `verification` (a document proves a fact) | a per-check rule where the fact is in the catalog, else a procedure |
| `condition` (something to obtain or clear) | a procedure plus, later, a release rule |
| `judgment` | a procedure |

- **Writer rules:**
  - one decision per job;
  - a job that needs a determination names it instead of restating it;
  - determinations are written first, so later jobs can cite them.
- **Ledger:**
  - the disposition considers kind: a `limit` with no code is a stronger gap than a `judgment` with
    none;
  - determinations proposed as derived fields join the field-derivation backlog.
- **Verify:** rerun the live trial pack.
  - Job count and grain move toward Acra's (we had 68 to their 123).
  - The aligned comparison's "partial" share falls; the baseline is 41 of 123 Standard.
  - Computable share rises.

## 6. D4. Small items that follow

- **Prefix families.** `MnemonicRules.families: {section: {family: description}}`.
  - The writer picks a family within the section; `prefixes` stays as the one-family case.
  - The readiness checks' `duplicate-id` covers uniqueness.
- **Variant dimension.**
  - `JtbdTemplate.variants`: the dimension name and its values, e.g. program with Standard and
    Platinum. Core jobs are written once; overlay jobs carry the variant (the rule overlays exist).
  - The export profile, which is the readiness plan's consumer contract, says which fixed blocks a
    downstream engine needs and fills them with "no change". This is pack data, not code.
- **Extraction targets.**
  - Derived per job from its documents' `yields` and its reads: the entity, and fields from the
    catalog.
  - The mode defaults from pack data (`ASK_USER` unless the pack says a kind of document is
    auto-approved).
  - Exported in the job set.

## 7. Order and size

- D1 is one build pass; D2 runs in parallel because it is mostly data. D3 comes after D1, since jobs
  must name documents before kind has teeth.
- D4 follows D3. Its variant and export half waits for the readiness checks.
- Each phase ends with the live trial-pack rerun and the aligned comparison against Acra's set. The
  measures are matched share, the partial share, computable share and coverage. A run costs about
  $0.2.

## 8. Decisions for the user

1. **The reference document taxonomy.** Settled 2026-10-12: the production document classification
   ontology is primary, and the 485-type Acra list fills the investor and entity gaps (section 2b).
2. **Registry vs classifier file.** Should the registry replace `document_agent.yaml`'s taxonomy
   when present (recommended), or should both stay with a link?
3. **Variant dimension for Acra.** Program only, with the investor blocks filled at export
   (recommended)? Or should investors stay a dimension too?
4. **Grain target.** Should the writer aim at one decision per job even where that roughly doubles
   the count (recommended, as it is what code needs)? Or keep a coarser job with fine checks inside?
