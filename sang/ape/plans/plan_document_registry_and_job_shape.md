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
| An external Acra document taxonomy: 485 types, 16 categories, cues, aliases, condition codes, PII markers | `status/IMDOC_ACRA_TAXONOMY_FOR_DSCR.md`; removed from that repo's tree in `ffa034a` (now read from Knowledge Hub), recoverable from `ffa034a^` | assessment only |
| Job set readiness checks, contract as pack data | `plans/plan_jtbdset_readiness.md` | routed, not built |
| Job ledger: jobs, `computable_checks`, `missing_reads`, coverage | `pack/ledger.py` | built |

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
    ids. Lint flags an id a rule or job names that the registry lacks.
  - **Job writer:** the writer is given the registry's ids, labels and kinds, and a job's documents
    are a list of ids. "Reference Documents" in the requirement text is rendered from labels, grouped
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
- **Verify:**
  - the seed with a registry classifies the Acra appraisal as before;
  - a job written with the registry names only ids;
  - lint flags a stray id;
  - coverage shows the two new gaps on the trial pack.

## 4. D2. Entity catalog for the Acra seed (mostly running existing tools)

- Run the Ontology tab's catalog extraction on the two Acra guidelines, with the mortgage reference
  copies as references, to build `catalog.schema.json` holding only what the documents need.
- The flat facts the rules read today become derived or aliased fields (`cltv_pct` from
  `LoanCore.cltv_percent`, with the unit), so no rule changes.
- `bound_to_catalog` then gives the writer `entities` and `metric_keys`.
- Check: a pack catalog can declare an alias or derivation from an entity field to a flat fact. If it
  cannot, that is the one SDK change in this phase.
- The jaci session commits the seed change; japes changes only for the alias gap.
- **Verify:**
  - the DSCR seed's assessments are unchanged byte for byte (the Ontology plan's risk rule);
  - a rewritten job names `Entity.field` metric keys.

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

1. **The reference document taxonomy.** Recover the 485-type taxonomy from history and upload it to
   the tenant reference library as the first reference (recommended), or build the registry from the
   policies and Acra's set alone?
2. **Registry vs classifier file.** Should the registry replace `document_agent.yaml`'s taxonomy
   when present (recommended), or should both stay with a link?
3. **Variant dimension for Acra.** Program only, with the investor blocks filled at export
   (recommended)? Or should investors stay a dimension too?
4. **Grain target.** Should the writer aim at one decision per job even where that roughly doubles
   the count (recommended, as it is what code needs)? Or keep a coarser job with fine checks inside?
