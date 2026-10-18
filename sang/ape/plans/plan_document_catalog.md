# Document catalog: a pack carries an external document catalog, and the SDK handles many kinds of documents from pack data

Plan, sonnet-runtime, 2026-10-17, from opus-xrepo's request and sonnet-ui's page plan (`plan_document_catalog_page.md`).
Branch `v2.6.4`. Status: written, decisions in section 8; nothing built. Consumer-neutral: the values are a pack's (jaci
or the Plato pack-creation UI); no SDK code or default names a client or a loan system. Worked example only:
`note_bytepro_document_list.md` (two sheets, about 460 types, categories, a 20-character code per type, a
one-accepted-copy flag, Commercial and Consumer).

## 1. Already there (read from the code)

- `DocumentRegistry` / `DocumentType` (`pack/document_registry.py`): id, label, aliases, `parent` (a category, or
  the id of the document this is a kind of), kind, cues, yields, validity, sensitive, retired/replaced_by, `x-source`.
  `taxonomy()` nests at any depth; `render_references`; `registry_findings`; `vanished_ids`; `draft_registry`.
- `reference_registry` and `classify_document` (`pack/document_proposals.py`): entries from a reference ontology or a
  record list, classified `matched` / `reusable` / `alias` / `new`, written by `apply_changes`.
- The reference library for catalogs (`catalog_reference_db`, table `catalog_reference`, routes under
  `/catalogs/references`) holds **JSON Schema catalogs only**; `catalog_adopt.adopt` and
  `POST /packs/{id}/catalog/adopt` are the model for adopting.
- `DocumentType` has no `extra="forbid"`: an unknown key in `document_types.yaml` is dropped without a word.

## 2. Coarse request against fine type: what happens today (the check asked for first)

- `document_ingest` counts a classified document as its own class **and every level above it** in the taxonomy path
  (`document_classes`: "a W-2 is also Income"). A `required_classes` need such as `any_of: [income]` is therefore met
  by a fine document nested under it, provided the document went through the registry taxonomy (a `parent` that names
  another document, or a category, which is a class too).
- Not covered: (i) a class supplied without the path (inline evidence in the input) counts as exactly that class;
  (ii) `any_of` names and a job's evidence type names are compared as written, not resolved through the registry's
  aliases and labels; (iii) the reverse is absent: nothing answers "which fine types satisfy this coarse request",
  so a document request and `render_references` print the coarse name and not the types an uploader can send.
- So the expansion upward exists on one path; this plan makes it a registry function every path uses, adds the
  reverse, and resolves names through the registry first.

## 3. Items (SDK, with the pack data each reads)

**P1. Declared attributes on a document type (SDK; the values are pack data).** `DocumentType` gains
`external_ids: {system: code}` (kept verbatim, never normalised or truncated), `attributes: {name: value}` (free map,
kept and round-tripped), `cardinality: many | single_instance` (default `many`) and `applies_to: [scope]` (a scope such
as a loan type; empty means every case). Any other key is a registry-lint finding `document_type_unknown_key`
(a warning, tolerant first) and is kept in the file the draft writer round-trips, so nothing is dropped silently. The
draft writer, taxonomy and classifier ignore the new fields (they do not change a class). `render_references` can
print a system's code beside the label when the pack asks (`document_codes: <system>` in the template).

**P2. A document-catalog reference and a tabular loader (SDK).** A reference of its own kind, stored beside the catalog
references (a new table `document_reference`, same rules: keyed `(tenant, reference, version)`, immutable, same
content a no-op, different content under a version refused, a size cap by a named constant). Entries are
`{category, name, code, single_instance, applies_to, attributes}`. The loader reads a spreadsheet (xlsx) or CSV with a
**column mapping declared in the reference** (`columns: {category: "Category", name: "Name", code: "Code",
single_instance: "Only One Approved", ...}`, the truthy values of the flag, sheets as scopes: `applies_to` = the
sheet's declared scope name), and merges a row that appears on several sheets by code (scopes unioned). Routes:
`PUT /documents/references/{id}/{version}` (a file or JSON entries, with the mapping), `GET /documents/references`,
`GET /documents/references/{id}?version=`, `DELETE`. Every bad row is named and nothing is stored unless all rows
read (as the JTBD CSV import does).

**P3. Adopt into a draft (SDK).** `POST /packs/{pack_id}/documents/adopt` with `{reference, version, codes?,
categories?, category_map?, if_match?}`: writes entries into the draft's `document_types.yaml` with a stable id
(slug of the name; on a collision the code is appended), label and alias = the reference name, `parent` = the
category (or its `category_map` target), `external_ids`, `cardinality`, `applies_to` and `x-source:
reference@version#code`. Answers `adopted`, `already_present` (matched by `x-source`, external id, or name and alias;
listed, never overwritten: tolerant first) and `refused` (each with its reason), the registry's resulting digest,
and 409 when the draft moved (`if_match`). The reference is never edited and unadopted entries stay in it.
`GET /packs/{pack_id}/documents/suggest?name=` returns the best reference entries for a name with a score (the existing
lexical matching in `document_proposals`, no model); a person confirms, nothing is applied by it.

**P4. Expansion both ways (SDK).** `DocumentRegistry.ancestors(name)` and `descendants(name)` (self included, cycles
and retired successors respected). `document_classes` and the `required_classes` check resolve every name through the
registry first and expand a class supplied without a path (inline evidence) the same way. The reverse is
`GET /packs/{pack_id}/documents/satisfying?name=`, and `render_references` lists, under a coarse name, the fine types
that satisfy it. A lint finding `required_class_unreachable` when a need names a class no live document can be.

**P5. Reporting (SDK; the Plato page is sonnet-ui's).** The coverage report gains a `documents` section: job
documents unmapped to the registry (today `unrecognised_documents`), registry types no job reads (a classifiable
type that is neither named by a job nor a descendant or ancestor of one that is), and, per case run, the
`single_instance` types holding more than one document (`docs.single_instance_conflicts`, listed with the document
ids; the run is not stopped). The workbook gains the same as a sheet.

## 4. SDK, pack data, what the Acra seed adopts

- SDK: everything in section 3. Pack data: the reference file and its mapping (uploaded through Plato or a client),
  `category_map`, the adopted `document_types.yaml`, the `document_codes` setting, `cardinality`, `applies_to`.
- Acra seed (synced from jaci): adopts nothing automatically. After the build, Acra's registry is made by adopting
  the origination categories from the BytePro reference through the route (never hand-copied), with
  `external_ids: {bytepro: <code>}`; the coarse-to-fine grouping the jobs use is the registry's `parent` tree, a
  human map (section 8).

## 5. Build order (one commit each, tests first, CHANGELOG under 2.6.4)

1. P1: fields, lint finding, code beside the label.
2. P4: ancestors and descendants, name resolution in the required-class check, the `satisfying` route, grouped rendering.
3. P2: reference table (migration), tabular loader, reference routes, client methods.
4. P3: adopt and suggest, client methods.
5. P5: the `documents` section of coverage, the case-run conflicts, the workbook sheet.

sonnet-ui builds the page after commit 4 (reference list, entries, adopt, draft registry); the unmapped and unread views
after commit 5. Route paths and response shapes are as above and are sent to sonnet-ui once the plan is approved.

## 6. Tests (each fails on the old code; stubs shaped like production)

Unknown key kept and linted, never dropped; codes kept verbatim at 20 characters; a coarse need met by a fine document
with and without a path; an alias in `any_of`; descendants of a coarse type; a workbook with two sheets read with the
declared mapping, a row on both sheets merged, a bad row refusing the whole file; adopt idempotent (second call
`already_present`), a moved draft 409, a refused entry named and the rest kept; a `single_instance` pair of
documents reported on the run; the unmapped and unread lists on a pack.

## 7. Healthcare-shaped check

A fixture catalog of document types with no mortgage vocabulary (a patient record, a lab report, a referral, a consent
form; two scopes; a single-instance consent) goes through the same loader, adopt and expansion tests.

## 8. Decisions for the user (recommendation first)

1. **Storage.** A new table `document_reference` (recommended: a different content shape and lifecycle) or a `kind`
   column on `catalog_reference`.
2. **Cardinality.** `many | single_instance` as an enum (recommended, room for more) or a boolean flag.
3. **Default adopt set** for the sheet's categories: the reference's mapping carries `default_adopt: [categories]`
   (recommended) and the page offers the rest; which origination categories are Acra's is the user's or Acra's call.
4. **Single-instance conflicts.** Report only (recommended, tolerant first), or also pick the latest one for the
   evidence picker.
5. **Facts only you or Acra can give:** Commercial is the sheet for the DSCR loans; the right types for "Listing
   history" and "Rent roll"; the evidence-type groupings (a human map).
6. **sonnet-ui's optional suggest route:** built as in P3 (recommended; it reuses the lexical matcher), or left to the page.

## 9. Built (sonnet-runtime, 2026-10-17, `v2.6.4`): P1 `2eb97bca`, P4 `74bd27d5`, P2 `b273c0de`, P3 `7ace7833`, P5 `0bf53490`

Decisions taken as recommended (new table, `many | single_instance` enum, `default_adopt` left to the caller, report-only
conflicts, suggest built). Deviations from sections 3 and 5:

- Reference routes are under `/document-references` (not `/documents/references`: `/documents/{id}` would answer
  it), with `POST .../upload` for a file and `PUT` for JSON entries; suggest is per reference
  (`GET /document-references/{id}/suggest?name=`), since the match is against a reference, not a pack.
- `satisfying` is `GET /packs/{id}/{version}/documents/satisfying` and `GET /packs/drafts/{id}/documents/satisfying`
  (a version path cannot be `/packs/{id}/documents/...`). The draft's registry reader is
  `GET /packs/drafts/{id}/documents` (digest, entries, findings).
- Adopt never suffixes an id: an id another document holds refuses that entry (its reason named) and the rest are
  kept; two entries differing only in punctuation are one document (the second `already_present`, why `name`). A
  `default_adopt` is not stored: the caller names `categories` (the page offers the rest).
- `if_match` on adopt is the registry file's digest, checked before the write; the write itself is not a
  compare-and-write (no lock between the read and the write), as for the other draft-file writers.
- `required_class_unreachable` was not added as a lint finding: the publish check already refused a required class
  no taxonomy label can be, and now resolves aliases first (the bug it had).
- `default_adopt` and the sheet-to-scope declaration live in the column mapping the caller sends; nothing is stored
  with the reference but its entries.
- Not built: a pack manifest field naming the reference a registry was adopted from (the `x-source` on each entry
  says it); the Plato page (sonnet-ui).
