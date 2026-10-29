# Note: comparing job-set versions (ours vs ours, ours vs K-Studio, Standard vs Platinum)

sonnet-ui, 2026-10-26. Asked by opus-xrepo for the user's review of regens and Acra's sets. A note, nothing built.

## What compares today

| Need | Have | Where |
|---|---|---|
| Two job sets, paired 1:1, differing fields per pair | `POST /packs/compare` (`jtbd_compare`, `jtbd_match`), xlsx | `/compare/ui` (`compare.html`) |
| Sets of different grain (our 1 : their n) | `aligned: true`, model label per left job, stored per side (`alignment_db`) | same page, "aligned" mode |
| A side | `pack:<id>@<version>`, `draft:<id>`, or an uploaded JTBDSet JSON (the K-Studio shape) | `_comparison_side` |
| Pack versions: jobs, rules, documents, catalog keys, coverage, gold cases | release report `GET /packs/{id}/release-report?from&to` | packs page |
| Catalog, rules, helper library compare | `vocab_compare`, `rule_rows`, `library_view` | Ontology, Code pages |
| Guideline versions by section digest | `GuidelinesDiff` | guideline routes |

So a pack version against a K-Studio file is already possible (upload one side), and so are two versions of one pack.

## What is missing, by the user's dimensions

1. **Programs.** `items_from_policies` flattens a pack's policies; an item carries no program, so Standard vs Platinum inside one
   pack cannot be picked as two sides, and the same clause in both programs is not shown as one row. Needs a `program` on `JtbdItem`
   and a side spec `{pack_id, version, program}` (overlay applied), plus a cross-program view keyed by clause.
2. **Section coverage.** No view of sections per set (jobs per section, sections only one side has). The pair report lists jobs, not sections.
3. **Clause-to-job coverage.** Coverage exists per pack version (ledger, `coverage_trial.xlsx`) but is not compared to a K-Studio set,
   which has no clause links in our ledger. Needs the guideline clauses as the shared key: per clause, jobs on each side.
4. **Granularity.** `aligned` finds 1:n but is a model call per job and its result is a flat list. Missing: a clause-keyed
   "one clause, n jobs left vs m right" row and counts (split ratio per section).
5. **Thresholds and readings.** Pair differences list changed fields; there is no table of thresholds/metric keys per job that
   puts two values side by side with the delta, filterable to "differs".
6. **Wording and shape.** Wording is a field difference without the aligned word diff; shape (steps, checks, metrics, evidence
   types) shows only as facet name sets.
7. **Regen N vs N+1 as a first-class pick.** Versions are chosen by typing `pack:<id>@<version>`; no picker of archived bundles, and
   no run metadata (trial pack, date, models and provider per stage, prompt versions, SDK and Plato version, counts) shown on each side.
8. **Shared components.** `/compare/ui` predates `version_compare.js`; it does not use the common change kinds, filter or xlsx link.

## Suggested order (each a small slice, SDK half first)

A. `program` on items and on the side spec; cross-program rows keyed by clause. B. Section and clause coverage tables over the
same sides (no model). C. Threshold/reading and wording columns in the pair rows. D. Bundle picker with metadata header, once
the manifest exists. E. Move `/compare/ui` onto the shared component.

## Answers from sonnet-runtime (2026-10-26)

- Bundles are a filesystem artifact (`scripts/local/acra_bundle.py`, folder plus `archive/<n>`), not served by Plato; no list route.
  Its proposed `bundle.json` (version, trial_pack_id, generated_at, sdk and plato version, stages {provider, model, prompt_versions},
  counts, template_digest, library_version) is a plan awaiting opus-xrepo. So the bundle picker (D) is dropped: compare reads the
  pack's jtbdset (published or draft) per program, plus uploads. Run metadata shows only if a route serves it later.
- Per-program export (planned, not built): one JTBDSet per program, each value with `rule_id` beside `mnemonic`; `program` may be stamped on each value.
- Key rows by `rule_id` and program, never `mnemonic` (the export reused a job's own mnemonic, so 85 of 195 looked like seed jobs).
- K-Studio sets stay uploads; no job-set reference kind planned.

Nothing to build until the per-program export lands.

## Landed (sonnet-runtime, SDK `ee9f8015`, 2026-10-26)

- Exported jobs carry `rule_id`; a per-program export also carries `program`. Key cross-program rows by `rule_id` + `program`.
- `jtbdset_export.export_program_sets(pack, version=, programs={program: policy_id})` returns `{program: JTBDSet}`; no Plato route calls it yet
  (`GET /packs/drafts/{id}/jtbdset` still answers one combined set). A `?program=` or sets route is mine to specify if slice A needs it.
- `bundle.json` exists per bundle folder on disk only (`docs/status/Acra/acra_bundle`, `archive/`); no Plato route. Not used by the UI.
- Sets on disk: `3_sdk_jtbds/jtbdset_standard.json`, `jtbdset_platinum_select.json`; K-Studio `2_kstudio_jtbds/acra_New_Guideline_JTBD[_Platinum].json`
  (uploadable as sides today).

## Built (v2.6.6, unpushed, not browser-checked)

- A `program` on a comparison side (`82f3b774`): `#<program>` on the page.
- Jobs per section and section type (`1ee9cd7f`), sections sheet.
- Clauses the jobs cite, per side, for pack and draft sides only (`06ccb356`); a set side has none.
- Changed words and a `figures` difference per differing pair (`47abfc5f`).
- Not done: E (the shared component). `/compare/ui` rows are pairs, aligned matches and notes, not keyed old/new cells, so moving it
  means rewriting the page, not reusing the component; no gain for the user's review, so left.
