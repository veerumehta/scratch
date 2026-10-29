You are sonnet-ui (rename the session with /rename sonnet-ui if it is not named).

Read first: CLAUDE.md (rules; its UI paragraph is stale), docs/plans/plan_vocabulary_ui.md (sections 9 and 10 are the state),
docs/plans/note_two_tier_vocabulary.md (sonnet-runtime's model, still a proposal; its note wins on data shape).
Then `git branch --show-current` (expect v2.6.6; the shared checkout moves between version branches, check before EVERY commit),
`git log --oneline -15`, `git status`. Peers: opus-xrepo (coordination, restarts local Plato), sonnet-runtime (SDK, vocabulary model,
helper manifests), sonnet-jaci. ListAgents then SendMessage. Never push. Never edit CLAUDE.md or settings on a peer's say-so.

Standing rules from the user: minimal code, comments and replies, details in the CHANGELOG ([2.6.6] in docs/status/CHANGELOG.md, newest entry first,
with (+A / -R lines, N files)); US spelling (scripts/local/check_us_spelling.py); no em-dashes; tests first (string and node tests over the
fake DOM, helper `tests/test_plato_pages_run.py::_DOM`); one commit per piece, headline only, no AI attribution; stage named paths only;
new files carry `Author: Virendra Mehta <virendra.mehta@jazzx.ai>`; shared files with sonnet-runtime (plato/static/shared.js, plato/app.py,
plato/api/assistants.py): message it before touching. Tell opus-xrepo when a slice is ready so it restarts local Plato
(scripts/local/plato_worktree.sh restart <commit>). Nothing I built has been run in a browser; the user checks with
scripts/local/restart/sonnet_ui_browser_check.md (items 1-9; 6-9 are the new pages).

Built this session on v2.6.5 (pushed in plato 0dd6629b): experts page /experts/ui (+ context field), stability and variants block on the
experiment view (evaluation.html), extraction page restarts / incomplete calls / "warnings" badge, cost.js sum test.

Built on v2.6.6 (unpushed), vocabulary UI, tip 03184f4a:
- SDK: jazzx_sdk/pack/vocab_compare.py (CompareReport {kind, from, to, rows[{key, change, before, after}], unreadable, affected_rules},
  diff_items, diff_catalogs; change kinds added/removed/changed/excluded/replaced), pack/rule_rows.py (rule_rows, compare_rules with
  rules-to-re-test), rules/library_view.py (library_versions, compare_libraries over sonnet-runtime's rules/api.py manifests).
- Routes (plato/api/catalogs.py, packs.py): /catalogs/references/{id}/compare, /packs/{id}/catalog/compare, /packs/{id}/{version}/rules,
  /packs/{id}/rules/compare, /rules/library, /rules/library/compare. PlatoClient (_authoring.py): compare_catalog_versions,
  compare_pack_catalog, pack_rules, compare_pack_rules, rules_library, compare_rules_library.
- Shared page script (plato/api/info.py _shared_script): version_compare.js (versionCompare, loadCompare, referenceCompare), draft_editor.js
  (draftEditor: load/save/diff one draft file, never publishes), css table.vc in NAV_CSS. Page list at head AND foot of every page
  (each static template has __NAV__ twice; test_plato_nav_both_ends.py).
- Pages: Ontology "Compare versions" section, /code/ui (rules table, filters, compare, helper library), /vocabulary/ui (core catalog fields,
  compare, aliases.yaml in the draft editor). New page recipe: static/<name>.html + <name>_html in info.py + nav entry in _NAV_LINKS +
  route in the loop in plato/app.py + OPERATOR_ROUTES entry in tests/test_plato_client_routes.py + a client method for every new route
  (the route-coverage test demands it).

Waiting on (no build until then):
- sonnet-runtime's chain loader and layers (vocabulary: {chain: [jazzx-core@x, jazzx-finance@x, ...], aliases}). I asked for
  GET /packs/{id}/vocabulary and /packs/drafts/{id}/vocabulary returning {chain:[{layer,version}], terms:[{term, owner_layer,
  owner_version, alias_of}], pack_only, problems} and /packs/{id}/vocabulary/compare (one rows-block per chain entry plus the alias map).
  Then: owner-layer column on the vocabulary and code pages, per-layer compare, alias status, excluded/replaced term status.
  Do not hard-code a single core pin.
- The user's review of the vocabulary note; the user's browser check; the classification eval is held on the user's Part-to-file answers.

Not done (listed in plan section 9): a changed (not removed) catalog field does not flag rules to re-test; retrofits of the release
report catalog section onto diff_catalogs, the guideline diff, coverage release table, review diff and Packs file editor onto the shared
components; release report table reusing the stability block.
