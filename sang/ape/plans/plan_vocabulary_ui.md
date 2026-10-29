# Plan: reviewing and editing vocabulary and generated code on Plato, with version compare

sonnet-ui, 2026-10-23. Status: slices 1-3 built on v2.6.6 (`b2981797`..`aa79e6f4`), not browser-checked; helper compare waits on sonnet-runtime's manifests; alias status column waits on the vocabulary model. Builds on `note_two_tier_vocabulary.md` (sonnet-runtime); that note owns
the model (core, aliases, pin, resolution), this plan owns the pages and the compare view.

## 1. Prior art (reuse, do not rebuild)

| Have | Where | Use |
|---|---|---|
| Two-sided file diff, per file and per rule, with aligned word-marked rows | `pack/diff.py` (`diff_files`, `diff_rows`), draft routes `/packs/drafts/{id}/diff[/rows]`, review diff rows | the line-level view of any file in two versions |
| Release report: jobs, rules, documents, catalog (keys only), coverage, gold cases; xlsx | `pack/release_report.py`, `GET /packs/{id}/release-report?from&to` | the entity-level frame; its catalog section is entity keys only, no field detail |
| Guideline diff by file and section digest | `pack/guidelines.py` `GuidelineDiff` | the shape for "added/removed/changed" lists |
| Reference catalogs, adopt, `x-source` pins | `plato/api/catalogs.py`, `ontology.html` | the editing surface (draft, then publish) |
| `lib_version` on a rule, flagged by lint_fix when it differs from `LIB_VERSION` | `pack/lint_fix.py`, `rule_view.py` | the "re-test" signal |
| `check_computability` verdicts, `needs_field` | job metadata, `ledger.py` `needs_fields` | the code review columns |
| `render_api()` text of the helper list | `rules/api.py` | the helper list, as structured rows |

Gaps: no field-level catalog diff, no alias or pin (the note's design), no route that lists rules with `lib_version` and verdicts, no
structured helper list. No prior plan covers a vocabulary page (grepped plans/ and status/).

## 2. The compare view (shared, built once)

One page module, `vocab_compare.js` (inlined like `cost.js`), taking `{left, right}` as two loaded documents of one kind and a `kind` that
says how to key and label them. Rows are keyed by a stable name, then listed `added | removed | changed | unchanged` (unchanged folded):

| Kind | Key | Cell content | "Changed" means |
|---|---|---|---|
| catalog / core | `Entity.field` | type, unit, enum values, description | any of these differs |
| alias map | pack term | the core term it maps to | target differs, added, removed |
| rule | `policy_id/rule_id` | `lib_version`, reads, verdict, needs-fields | any differs |
| helper | name | signature, first sentence | either differs |

- Side by side, left older. A changed row opens to the aligned old/new text (the `diff_rows` row shape, not a new one).
- Header: counts per change, a filter, and a link to the same pair as xlsx (the release workbook's sheet style).
- **Affected rules** panel on a core or catalog compare: rules whose reads include a changed or removed term, each flagged "re-test".
  Computed on the server from the two versions and the rules' recorded reads, never in the browser.
- Tolerant: a side with no catalog or no alias map shows "none", an unreadable file lists as unreadable, a missing version names which.

## 3. Routes (SDK `pack/vocab_compare.py`, Plato hosts; minimal)

- `GET /catalogs/references/{id}/compare?from=&to=` and `GET /packs/{id}/catalog/compare?from=&to=`: field-level change list (the one
  new SDK function, `diff_catalogs`, over `catalog_entities`; the release report's catalog section then reuses it, so the two cannot
  disagree).
- `GET /packs/{id}/vocabulary/compare?from=&to=`: the alias map change list plus the pinned core version on each side (after the note's
  manifest `vocabulary:` key exists).
- `GET /packs/{id}/{version}/rules`: rules with `lib_version`, check verdicts, needs-fields, reads; and
  `GET /packs/{id}/rules/compare?from=&to=` built on it, with the affected-rules list.
- `GET /rules/lib`: the helper rows `{name, signature, summary, lib_version}` (the structured form of `render_api`), and
  `GET /rules/lib/compare?from=&to=` only once two library versions are retrievable (today only the running `LIB_VERSION` exists, so
  this one waits, see section 6).

## 4. Pages (plain HTML and JS, one commit each, nav entries)

1. **Ontology page, Compare tab** (existing page): pick a reference or pack catalog and two versions, show the compare view. Read
   only. This is the first slice.
2. **Vocabulary page** `/vocabulary/ui`: the core catalog tree, a pack's alias map as a table (pack term, core term, status: aliased,
   pack-only, core term missing), edit by draft then publish (writes the draft's `aliases.yaml` through the existing draft file
   write, digest-guarded), compare of two core versions or two alias maps. Waits on the note's `vocabulary:` key.
3. **Code page** `/code/ui` (or a tab on Coverage, to settle): a pack version's rules table (rule, policy, `lib_version`, verdict,
   needs-fields, reads, link to the rule source via the existing rule route); filters for "lib_version differs from current" and
   "needs a field"; the compare of two versions with the affected-rules flags. Edit: none in the first cut (rule edits already go
   through the draft file editor; the page links there).
4. **Helpers panel** on the Code page: the helper list, with the library version; compare when section 6 allows.

Editing everywhere is draft-then-publish through the existing draft routes and the review gate; no page writes a published version.

## 5. Order and first slice (small)

1. **Slice 1:** `diff_catalogs` (SDK) with tests, the two catalog compare routes, `vocab_compare.js`, the Compare tab on the Ontology
   page. Release report's catalog section moves onto `diff_catalogs`. No dependency on the note's alias design.
2. Rules list and rules compare routes, the Code page (reads, filters, compare, affected flags).
3. Alias map and core compare, the Vocabulary page (after sonnet-runtime builds `vocabulary:` and resolution).
4. Helper rows and compare.

Each page: node tests over the fake DOM (as the stability and extraction pages), string checks for routes, CHANGELOG under 2.6.6.

## 6. Open questions

- **Helper versions:** only `LIB_VERSION` of the running code is known. A helper compare needs either a stored `rules_lib` manifest per
  version (a JSON of `render_api` rows, written at each version bump) or a pack's recorded `lib_version` only. Which? Recommend the
  manifest, written by whoever bumps `LIB_VERSION` (sonnet-runtime).
- **Where the affected-rules list reads from:** rules record `lib_version`; the note proposes also recording the core version and terms
  read. Until that lands the list falls back to the reads the rule's condition already declares (`missing_reads` and read names).
- **Code page vs Coverage tab:** one more page, or a tab on Coverage? Recommend a tab (Coverage already reads the ledger).
- **Core as SDK data:** compare of two core versions needs both stored; the note ships one. Load each version as a reference-library
  entry (`jazzx-core@x`), so core compare is reference compare and needs no extra route.

## 7. How each page is checked in a browser

Added to `scripts/local/restart/sonnet_ui_browser_check.md` as items 8-10 when each lands (local Plato, Acra pack, two published
versions needed: publish a tweaked copy to get a second one):

- **Ontology Compare tab:** pick `pack:acra-dscr-policy`, versions N-1 and N. Expect counts, a changed field opening to old and new
  text, "none" when a side has no catalog, no red bar.
- **Code page:** rules table fills with `lib_version` and verdicts; the "differs from current" filter narrows; compare of two versions
  shows added/removed/changed rules and the re-test flags.
- **Vocabulary page:** alias table fills; edit one alias in the draft; the page shows the draft diff; publish goes through review.
- Until a human runs it, the claim stays "node-tested, not browser-checked".

## 8. Not in scope

Writing the core vocabulary content, the alias resolution and the suggestion loop (sonnet-runtime's note); a new diff engine; any
model call on these pages.

## 9. Built, and what is left (2026-10-23)

Shared parts in the shared page script: `version_compare.js` (`versionCompare`, `loadCompare`, `referenceCompare`), `draft_editor.js`
(`draftEditor`), CSS `table.vc`, the page list at head and foot of every page. Pages: Ontology Compare section, `/code/ui`, `/vocabulary/ui`.
Routes: reference and pack catalog compare, rules list and compare. Client: `compare_catalog_versions`, `compare_pack_catalog`,
`pack_rules`, `compare_pack_rules`.

Left: helper list and its compare (sonnet-runtime's manifests); alias status column and resolution (their model); a changed (not
removed) catalog field does not yet flag rules to re-test.

Retrofits not done (cheap each, one commit apiece): the release report's catalog section onto `diff_catalogs`; the guideline version
diff and the coverage page's release table onto `versionCompare` (their shapes differ: file/section lists, item changes); the review
page's draft diff onto the shared editor's diff; the Packs page's file editor onto `draftEditor`.

## 10. Model update (sonnet-runtime, 2026-10-23, still a proposal)

The manifest takes a chain (`vocabulary: {chain: [jazzx-core@x, jazzx-finance@x, ...], aliases: aliases.yaml}`), lowest layer first; the
first layer defining a term owns it; layers are reference-library entries, so a layer compares as a reference (route exists). When built,
the Vocabulary page shows each term with its owning layer and version, a layer picker over the chain, and a pack compare of one rows-block
per chain entry plus the pack's catalog and the alias map (alias added, removed, retargeted). Nothing is built here until the loader and a
pack-level vocabulary route exist.
