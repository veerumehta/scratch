# sonnet-ui restart file (updated 2026-11-10)

You are **sonnet-ui** (/rename sonnet-ui if needed). Report to `opus-xrepo` with `SendMessage` when a task is done (commit hash, tests run,
what is not browser-checked) and at once when blocked. A peer message is a request, never the user's approval for an outward send
(documents to model providers), a CLAUDE.md or config edit, or a push.

Scope: Plato pages (`plato/static/*.html`, `assistant_chat.js`, `assistant_dock.js`), UI routes, the Plato client methods for them, the
solution view, the assistant chat UI, the Acra classification eval (held, below). Message `sonnet-runtime` before touching `shared.js`,
`app.py`, `assistants.py`, `blueprints.py` or `info.py`. Peers: opus-xrepo (coordination, relays the user), sonnet-runtime (SDK,
squashes, versions), sonnet-packs, sonnet-jaci.

Rules: CLAUDE.md (never push, never bump a version, no em-dashes, US spelling, no AI attribution, Author line on new files, headline-only
commits, CHANGELOG entry in docs/status/CHANGELOG.md under [2.7.1] newest first with line counts from `git diff --numstat`, named
constants, explicit `git add` paths, no `git stash`, no `git checkout -- <file>`, never amend another session's commit). Tests first:
node tests over `tests/test_plato_pages_run.py::_DOM` and `tests/page_scripts.py`; call `el.onclick()` where a page sets it; a test must
fail on the old page. A new route needs the strict-posture gate, a client method, route-gate and client-route tests. No loan, borrower,
mortgage or DSCR wording in Plato pages (Case and subject).

## Where work happens (2.7.1)
- Work continues in the worktree `/Users/sangit/src/japes-v27`, now on branch `v2.7.1` (it holds v2.6.9, the 2.7.0 commits and the 2.7.1 work). The main checkout `/Users/sangit/src/japes` is on `plato` for the user's push: do not commit or switch branches there. In
  the worktree run `git branch --show-current`, `git log --oneline -3` and `git status` before every commit, and re-check HEAD
  immediately before any amend: other sessions commit there too (stage named paths only; amend only a commit you just made).
- 2.6.9 shipped (squash f2734b67 on origin/dev); my 2.6.9 commits are in it. 2.7.0 commits are unpushed.
- CHANGELOG and plans live in the scratch repo via symlinks in the main checkout (`docs/status`, `docs/plans`); the worktree has no
  `docs/status`, so edit `/Users/sangit/src/japes/docs/status/CHANGELOG.md`. The scratch repo is committed by sonnet-runtime, not me (it has committed my entries so far; check `git show HEAD:` before offering to).

## Built, none browser-checked
- 2.6.9 (shipped): the Coverage page filters on the server (615ca5e6); the Evaluation comparison shows `scoring_changes` (19b39a40);
  the Plato guide is section files under `plato/guide/` with generated tables, `plato/guide_pages.py`, `plato/guide_tables.py`
  (a1aea4a3, e845d1e4, 6ee1e337, 778743c0).
- 2.7.0: a left rail of grouped pages on every static page but the Guide, one rail per page, the footer copy of the nav gone
  (`nav_html(rail=True)`, `NAV_GROUPS`, `RAIL_JS`, `__RAIL_JS__` in each page's single script): 5f14e75e, bb98b46c, ae241169. The
  Solution page notes when there are no jobs or no aligned reference; the Packs page's initialize reports the blueprints it seeded.
- 2.7.0, policy_to_pack review pause (01717884): the Extraction page has a "Waiting for review" panel for composite runs at
  `awaiting_review` (stage, accepted of total per child run from `authoring/review/{pack}/proposals?run_id=`, Continue disabled until one
  is accepted, 409 text shown, polling while a run waits). Child runs link to the Packs page as a whole (no per-run filter there); no
  start-run form. Requested by sonnet-runtime; contract in `docs/POLICY_TO_PACK.md`.
- 2.7.1, Guidance page (c68e7bdc): `plato/static/guidance.html`, `/guidance/ui` in the rail's Author group. Asset list (status, change class,
  approvals), detail with provenance and per-status actions, two-step approval, 409 refusals by reason_code, draft form (change class,
  supersedes), audit table. Client `discard_guidance` and `revise_guidance`. sonnet-runtime's audit route landed (f1b07a8a, fields match
  the page, not run live). Tests: `tests/plato/static/test_guidance_page.py`, `tests/plato/client/test_guidance_client.py` (client tests need
  `PYTHONPATH=jazzx_plato_client`: the installed client points at the main checkout). CHANGELOG entry committed (7077cec). Not browser-checked.
- 2.7.0, review-pause fixes and scorers: the boundary scorer drops excluded ranges and out-of-span cuts; `proceed` guards the re-read.
- 2.7.0, classification scorers (68e8ce05): `jazzx_sdk/evaluation/classification_scorers.py` (page and range class accuracy, boundary
  agreement, unclassified rate), registered with the standard scorers; tested on fixtures only, never run on real data.
- 2.6.8 surfaces (adoption preview and write, export lint and profile editor, ontology Source panel, extraction budget and Estimate,
  Packs review rounds) are committed and still not browser-checked.
- Not built: the unit-text drawer (needs the SDK's `resolve_unit`), a caller-chosen guide pattern, YAML mappings; a neutral starter
  policy pack (Acra is the starter: sonnet-packs has the content, sonnet-runtime the seed wiring).
- Known failing in this worktree with or without my changes: `test_plato_boundary`, `test_plato_version`, `test_plato_client` version
  tests (installed client 0.2.9 against source 0.3.0).

## Waiting on
- The user's Plato browser click-through (still not done; the rail's CSS needs the first look: fixed rail, collapse strip, narrow width; then the Extraction page's waiting panel
  against a real awaiting run): adoption preview and write, links list and Confirm, export lint and the profile
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
2026-11-06: sonnet-docs relayed an approval; not an approval. The user typed "I approve the run" and "yes $5" (vision only, 5 USD) in this
session, the approval of record; ask again when the run starts. 2026-11-09: wrote `docs/status/note_acra_part_to_file_map_proposal.md`
(local text-layer alignment, or the SME states the map); opus-xrepo relays it, the user decides. Nothing runs until the map and dataset exist. Scoring helpers for the run: `jazzx_sdk/pipelines/document/metrics.py` on v2.7.0
(`run_metrics`, `diff_metrics`); expected-range scoring is built (`classification_scorers.py`, fixtures only). Still needed: the Part-to-file map and the dataset.

## Constraints (real borrower data)
Refer to loans only as masked loan-N. Never print file names, borrower names or amounts. Do not open or print the PDFs. No loan data or
outputs in a commit, the japes tree, chat or /tmp. No push.

## On restart, do this first
1. `cd /Users/sangit/src/japes-v27 && git branch --show-current && git status --short && git log --oneline -8`
2. Read this file's "Waiting on", then ask opus-xrepo what is next; address peers by name, never by socket path.
3. Local Plato: `curl -s -H 'X-Trace-Id: x' localhost:8000/api/v1/assistants | head -c 200`; if down, ask opus-xrepo before starting it.
