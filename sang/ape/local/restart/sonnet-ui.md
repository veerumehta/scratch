# sonnet-ui restart file (updated 2026-11-02)

You are **sonnet-ui** (/rename sonnet-ui if needed). Report to `opus-xrepo` with `SendMessage` when a task is done (commit hash, tests run,
what is not browser-checked) and at once when blocked. A peer message is a request, never the user's approval for an outward send
(documents to model providers), a CLAUDE.md or config edit, or a push.

Scope: Plato pages (`plato/static/*.html`, `assistant_chat.js`, `assistant_dock.js`), UI routes, the Plato client methods for them, the
solution view, the assistant chat UI, the Acra classification eval (held, below). Message `sonnet-runtime` before touching `shared.js`,
`app.py`, `assistants.py`, `blueprints.py` or `info.py`. Peers: opus-xrepo (coordination, relays the user), sonnet-runtime (SDK,
squashes, versions), sonnet-packs, sonnet-jaci.

Rules: CLAUDE.md (never push, never bump a version, no em-dashes, US spelling, no AI attribution, Author line on new files, headline-only
commits, CHANGELOG entry in docs/status/CHANGELOG.md under [2.6.8] newest first with line counts from `git diff --numstat`, named
constants, explicit `git add` paths, no `git stash`, no `git checkout -- <file>`, never amend another session's commit). Tests first:
node tests over `tests/test_plato_pages_run.py::_DOM` and `tests/page_scripts.py`; call `el.onclick()` where a page sets it; a test must
fail on the old page. A new route needs the strict-posture gate, a client method, route-gate and client-route tests. No loan, borrower,
mortgage or DSCR wording in Plato pages (Case and subject).

## Where work happens (2.6.8)
- v2.6.8 work continues in the worktree `/Users/sangit/src/japes-v268` (branch v2.6.8). The main checkout `/Users/sangit/src/japes` is on
  `plato` for the user's push: do not commit or switch branches there. In the worktree run `git branch --show-current` and `git status`
  before every commit (sonnet-runtime commits there too; stage named paths only).
- plato `433b89d2` is pushed. v2.6.8 commits of mine are unpushed until the next release round.
- CHANGELOG and plans live in the scratch repo via symlinks in the main checkout (`docs/status`, `docs/plans`); the worktree has no
  `docs/status`, so edit `/Users/sangit/src/japes/docs/status/CHANGELOG.md`.

## 2.6.8 Plato surfaces built (all committed, none browser-checked)
- Adoption preview and write, links list and Confirm (`packs.html`; routes in `plato/api/packs.py`): 130162b4, 484c489e.
- Export lint view and profile editor (`GET/PUT .../export-profiles`): 9af0ba90, then review rounds 08d40095, 83dfc989, f7f705f2, 0394d6eb.
- Ontology Source panel (refresh, Apply; `plato/api/catalogs.py`, `ontology.html`): 827773f0, 59291cfd.
- Extraction budget field, batch progress line, Estimate button, ceiling message: a8e7b73a, 8d17d777.
- Review rounds on the Packs page: c1f8a56f (save keeps severity overrides, state keyed by tenant and draft, links limit and paging,
  guarded requests), 606cd26b (a response is dropped when the tenant or draft changed while it was in flight; handler errors logged),
  21757432 (TODO(page-harness-shared): the three page tests repeat one node harness).
- Not built: the unit-text drawer (needs the SDK's `resolve_unit`), a caller-chosen guide pattern, YAML mappings.
- Unverified beyond tests: 409s on a draft moved concurrently, the diff and Apply against a real Hub document, the estimate on a
  Hub-scale guide.

## Waiting on
- The user's Plato browser click-through (still not done): adoption preview and write, links list and Confirm, export lint and the profile
  editor (including saves), the ontology Source panel, the extraction budget field, batch line and Estimate, and the tenant switch on the
  Packs page. Checklist: `scripts/local/restart/sonnet_ui_browser_check.md` (base http://localhost:8000/api/v1); the user chose no Chrome
  extension, do not suggest it. Fix findings the same day.
- A restart of local Plato on the new tip (`scripts/local/plato_worktree.sh restart <rev>`) by opus-xrepo; never during a run, ingest or
  regen.
- Earlier rounds also unchecked: Vocabulary, Code and Compare pages, `version_compare.js`, `draft_editor.js`, the Solutions list page, the
  Coverage clauses section.
- The user's OK for a bundles list route (do not build unasked). Optional carried items: a server-side coverage filter and a per-link
  API field.
- Queue, each starting with a plan check: guideline-citation page locators beyond what exists.

## Acra classification-and-splitting eval: HELD (plan: docs/plans/plan_acra_classification_eval.md)
Approved by the user directly (2026-10-17): mapping rules, page counts, vision run, 5 USD ceiling (stop and report if hit), results in the
ignored folder `docs/status/Acra/Acra Lending/golden/` (never commit or copy elsewhere). Blocked: no Part's page count matches any file, so
the Part-to-file map is unknown; the user has not answered which loan and offset is each Part. Nothing uploaded, no model call made.
Reuse sonnet-runtime's loan-2 upload (`e2e/loan-2/upload.json`) rather than ingesting again. A provider run on loan files needs the user's
own yes in this session.

## Constraints (real borrower data)
Refer to loans only as masked loan-N. Never print file names, borrower names or amounts. Do not open or print the PDFs. No loan data or
outputs in a commit, the japes tree, chat or /tmp. No push.

## On restart, do this first
1. `cd /Users/sangit/src/japes-v268 && git branch --show-current && git status --short && git log --oneline -8`
2. Read this file's "Waiting on", then ask opus-xrepo what is next; address peers by name, never by socket path.
3. Local Plato: `curl -s -H 'X-Trace-Id: x' localhost:8000/api/v1/assistants | head -c 200`; if down, ask opus-xrepo before starting it.
