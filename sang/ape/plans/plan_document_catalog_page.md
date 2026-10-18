# Plan: the document catalog page (browse a reference, adopt, show unmapped job documents)

sonnet-ui, 2026-10-16. Status: written, waits on the SDK routes below. Source: `note_bytepro_document_list.md`.
Pack-neutral: the page names no client or LoS; BytePro is data (a reference library entry).

## 1. What the page is
`/documents/catalog/ui`, in the style of the Ontology page (`ontology.html`, which browses reference catalogs and adopts
fields into a draft). Three sections, list-first, plain HTML and JS with `shared.js`:

1. **Reference**: the library's document catalogs (id, version, scope such as Commercial, row count). Pick one: a
   table of its entries (category, name, code, single-instance flag), with filters (category, text, only the
   origination-relevant categories the pack adopts by default), a checkbox per row and "Adopt N".
2. **This draft's registry**: the pack's document types after adoption, each marked with its source
   (`x-source: bytepro@2026-07-29#CODE`) and a link back to its reference row. Adoption is a draft write the
   reviewer publishes, never a change to a published version.
3. **Unmapped job documents**: what the jobs name that no document type covers, and the reference types no job reads
   (the coverage report already carries `unrecognised_documents` and `unsupplied_reads`; the page shows them with an
   "adopt a candidate" action: a fuzzy suggestion from the reference, confirmed by a person, never applied alone).

## 2. Routes the page needs (SDK side, sonnet-runtime)
- `GET {prefix}/catalogs/references?kind=document_catalog` (or the existing list with a kind field) and
  `GET .../references/{id}?version=` returning entries: `{category, name, code, single_instance, applies_to}`.
- `POST {prefix}/packs/{pack_id}/documents/adopt` like `catalog/adopt`: `{reference, version, codes: [...]}`;
  answers what was adopted, what already existed (conflict, tolerant: listed, not overwritten) and the new
  entries; 409 when the draft moved (digest).
- `GET {prefix}/packs/drafts/{pack_id}/documents` the draft's registry with sources (may exist as the registry reader).
- Coverage's unrecognised documents (exists) plus a suggestion call: `GET .../documents/suggest?name=` returning the
  best reference matches with a score (a page can fall back to client-side text match if it is not built).
- `los_code`, `single_instance`, `applies_to` shown only when the registry rows carry them.

## 3. Behaviour (tolerant first)
- A reference without codes still lists and adopts by name. A row already adopted shows "in the draft", not a second adopt.
- Adoption never edits the reference; a failed adopt names the entries it refused and keeps the rest.
- No guess is applied: a suggested mapping for a job document is shown with its score and a Confirm button.
- Large lists (460 rows): client-side filter, rows capped per render with "show more" (a named constant).
- Page context (`platoContext`) carries the pack, the reference and the selected rows, so the dock assistant can
  answer "which of these are origination documents".

## 4. Build order (one commit each, string/node tests, CHANGELOG under 2.6.4)
1. Page shell, reference list and entries table with filters (read only), nav entry.
2. Adopt (selection, result, conflicts) and the draft registry section.
3. Unmapped job documents with suggestions and confirm.

## 5. Open questions for the user
- Commercial is the sheet for Acra's DSCR loans? Which categories do processors use at intake (the default adopt set)?
- The right type for "Listing history" and "Rent roll", and the evidence-type groupings (a human map).
