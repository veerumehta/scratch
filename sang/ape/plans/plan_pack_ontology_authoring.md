# Plan: pack ontology authoring (an Ontology tab on Plato)

Status: proposed (2026-10-06), plan only; nothing built. Asked through opus-xrepo as user-directed.
The decisions at the end are the user's.

## What it is for

A pack's catalog (its entities, fields, enums, units and relationships) is what policy extraction
may name, what lint resolves rule inputs against, what grounding speaks in, and what the fact
catalog types. Today an author writes it by hand, per pack, in one of two shapes. The tab lets an
author build it from policy documents (or a starter), on top of a base that may be empty, reusing
pieces of reference ontologies instead of inventing duplicates, and review each addition with the
snippet that justifies it.

## Verified against the code (2026-10-06), with corrections to the survey

- Two catalog shapes in packs. `ci-spread-core` declares `ontology: ontology/ci_lending.yaml`
  (version, domain, entities with fields and relationships; `jazzx_sdk.pack.lint` and the
  vocabulary read it). `dscr_core` has no ontology: its facts come from `conductor.input_schema`
  (a JSON Schema) through `PackManifestLoader.fact_catalog()` (manifest_loader.py:260), which takes
  the schema's top-level primitive properties plus the metrics as facts. Hence lint's
  `no_ontology` and `unverifiable_rules` on a DSCR pack.
- `FactCatalog` is capped at 64 facts (`facts: tuple[...] = Field(max_length=64)`, facts.py:129).
- Existing machinery, as the survey says: `fabric/graph/vocabulary.py`, `proposal.py`,
  `proposal_store_db.py`, `proposal_comments.py`, `pipelines/vocabulary_build.py` (ingest, emit,
  observe, propose, decide, merge), `server/vocabulary_review.py` (list, decide, bulk decide,
  merge), the pack lint and check. `vocabulary_build` presupposes a schema: it turns admitted
  document fields into assertions against an existing vocabulary and proposes what is missing.
- **Correction:** a `Triple` carries `source`, `section`, `confidence` and `source_text` (the
  excerpt); there is no character span. Evidence snippets are excerpts, not offsets.
- No importer for JSON Schema ontologies. `util/schema_model.py` builds models from JSON Schema but
  refuses a `type` array ("write a union as anyOf"), and mortgage_ontology_v2.json writes every
  nullable field as `"type": ["string", "null"]`. No write-back of accepted proposals into a
  pack's catalog exists (accepted rules merge into a draft's policy file; vocabulary merge builds a
  `Vocabulary` object, not a file).
- **Correction:** `mortgage_ontology_v2.json` exists in three places (macer, mortgage-app,
  policy-workbench), all `version: 2.0.0` with the same `$id`, but they differ: 39, 49 and 44
  `$defs` (31, 39 and 34 entity objects). There is no single canonical copy yet. It is JSON Schema
  2020-12 with entities under `$defs`, `$ref` to shared types (UUID, CurrencyAmount...), inline
  enums and nullable type arrays, as the survey says.
- k9: `src/ontology_generator/templates/` has `proposal_extraction_3category_{system,user}.txt`
  and the `ontology_extension_json_*` prompts; `k9-ui/.../proposal_review.py` shows confidence
  stats and a high-confidence count. Ideas only; its pipeline is one call over truncated input.

## Design

1. **One catalog format**: JSON Schema 2020-12, entities under `$defs`, as the pack's single source
   (`catalog.schema.json`, named in the manifest). The fact catalog, grounding vocabulary, policy
   extraction's allowed `entity_types` and `metric_keys` and lint all derive from it. A loader
   reads the older `ontology:` YAML too and converts it, so ci-spread-core keeps working.
2. **Reference ontologies**: a library shown in a multi-select. Sources: files shipped with the
   SDK, uploaded JSON Schema files, or another pack's published catalog. Each extraction candidate
   is classified `already in the pack`, `reusable from <reference>`, `new` or `conflicting`, with
   document snippet evidence. Reuse is at entity or field granularity, pulling referenced types
   transitively, and records `x-source: <reference id>@<version>#<pointer>`. A new field that
   duplicates a reference field is a finding, so the tab prefers reuse.
3. **Pipeline**: chunked extraction (policy segmentation and `document_ingest`), cross-segment
   dedup, then proposals in the existing store as a new kind `catalog` (add entity, add field,
   change type, enum or unit). Review through the existing router and bulk decision; the model
   and prompts are versioned and recorded like the other pipelines (the provenance work), and the
   run shows its cost.
4. **Write-back**: accepted `catalog` proposals merge into the pack draft's catalog file (draft
   history and diff apply), then publish with notes. The merge is deterministic and validates the
   result as JSON Schema before writing.
5. **Downstream**: policy extraction is restricted to the catalog; lint reports a rule input whose
   path is not in the catalog; the 64-fact cap becomes a per-assessment scope (the facts the rules
   in force read), not a limit on the catalog.
6. **The tab**: the catalog tree; base and reference selection; upload documents and run with
   progress; proposals grouped by class with snippet and reference source; accept, reject or edit,
   accept all high-confidence; merge into the draft; publish. Page logic lives in the SDK, as for
   the packs page.
7. The earlier JTBD-shape items fold in: `jtbd_template.yaml` guide fields, the pack prompt
   override for `policy_jtbd`, manifest `exports:`, and extra draft fields restricted to the
   catalog.
8. Composition (`extends:` a base pack) is a later item; reference ontologies cover reuse until then.

## Phases (each lands on v2.6.1 with tests, a CHANGELOG entry and its client method)

A. Catalog format and loader: JSON Schema catalog, YAML adapter, derive facts, lint paths.
B. Reference library and importer: normalise type arrays, `$ref` closure, `x-source`; the three
   mortgage copies reconciled into one.
C. Extraction pipeline and `catalog` proposals; classification; versioned prompts; cost recorded.
D. Review, merge into the draft, publish; per-assessment fact scope replacing the cap.
E. The tab; then the JTBD-shape items; composition later.

## Risks

- A, B and D change how every pack's facts are derived; a single wrong derivation changes every
  assessment. The existing seed packs' assessments are pinned byte for byte before A starts.
- The mortgage reference has three diverging copies; reuse against the wrong one bakes the
  difference into DSCR's catalog.
- Classification quality (matched, new, conflicting) is a model judgment; the evidence snippet is
  what lets a reviewer check it, so a candidate without one is not proposed.
- ci-spread-core's `ontology:` YAML is read by lint, grounding and its vocabulary; moving it to the
  new format is breaking for jaci's CRE and spread flows unless the adapter holds.

## Decisions for the user

1. **One format.** JSON Schema as the single catalog source, with an adapter for the YAML (the
   recommendation), or keep two shapes and a mapping layer?
2. **The mortgage reference.** Which copy is canonical (macer's 31 entities, mortgage-app's 39,
   policy-workbench's 34), or should the three be merged into one first, and where does it live
   (SDK files, or a reference pack)?
3. **Reuse granularity and conflict policy.** Entity and field both; on a conflict between a
   document and a reference, does the reference win, the document win, or the reviewer decide
   (the recommendation, with the conflict shown)?
4. **Where reference ontologies are stored.** SDK files plus tenant uploads in the database, or only
   published packs' catalogs?
5. **The fact cap.** Replace it with a per-assessment scope (recommended), or raise it?
6. **First slice.** A to D without the tab (API and client), or the tab from the first phase?
7. **The ci-spread-core migration.** Convert its YAML to the new format in the same change, or leave
   it on the adapter until jaci asks?

## Decisions (user, 2026-10-06)

Recommendations accepted for all seven, with these refinements:
1. JSON Schema is the single catalog source; an adapter reads the existing YAML.
2. No canonical mortgage copy is needed for the first slice: all three copies are selectable references, and each adoption records which copy it came from. Merging them is a later, separate exercise done with this tool.
3. Reuse at entity and field level; a document-vs-reference conflict is the reviewer's call, shown side by side.
4. References are a tenant library in the database (uploads) plus published packs' catalogs, not SDK files.
5. The 64-fact cap is replaced by a per-assessment scope.
6. The first slice includes a minimal Ontology tab (with API and client): DSCR's catalog built from Acra's two policy documents, starting from an empty base with the mortgage copies as references.
7. ci-spread-core stays on the adapter.

Reference, not base: the catalog is pulled by the documents. Only what the documents need is adopted, field by field. Referenced types come in transitively only when an adopted field uses them, and a reference's `required` lists are not imported. Lint flags an adopted field no document or rule uses.

