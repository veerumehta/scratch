# Acra taxonomy as a document reference (sonnet-runtime, 2026-10-17)

Request: opus-xrepo (user approved). Sheet: `docs/status/Acra/Updated_Loan_Document_Taxonomy.xlsx`, "Master Taxonomy",
title rows above the header (row 4), 152 entries. Not copied into the repo, not committed.

1. Reader gaps (SDK): `DocumentColumns.header_row` (1-based, default 1), `aliases` (+ `alias_separator`, default `;`)
   and `cues` columns. `DocumentEntry` gains `aliases` and `cues` (empty by default; omitted from the stored JSON
   when empty so earlier references keep their digest). `adopt` carries both into the record (`aliases`, `cues`).
   Priority maps through `attributes`; the ID prefix stays in the verbatim code (category is the Category column).
2. Load: `acra-taxonomy@2026-10-17` through the upload route with the declared mapping; a script for the user
   (local Plato still runs 0.2.4, no document-references routes: pin to the tip, migrate to 0035, restart).
3. Report (script `scripts/local/acra_taxonomy_report.py`, read-only, no adoption into acra-dscr-policy): proposals
   of taxonomy entries against the BytePro reference by name (unmatched listed, nothing merged), the taxonomy
   entries no job reads (`coverage(..., registry)` over the taxonomy registry and the regen job documents) and
   the job-named documents matching no entry.
Tests first: reader (header row, aliases, cues, bad row), digest stable for an entry without them, adopt carries them.
