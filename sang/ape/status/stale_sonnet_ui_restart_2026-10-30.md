You are sonnet-ui (/rename sonnet-ui if needed).

Read first: CLAUDE.md, docs/plans/plan_vocabulary_ui.md (sections 9, 10), docs/plans/note_jobset_version_compare.md, docs/plans/plan_2_6_8_carried_from_2_6_7.md (named by opus-xrepo; not in docs/plans when this was written, so check).
Then `git branch --show-current` (expect v2.6.8, Start 2.6.8 is 2a2098f5; check before EVERY commit), `git log --oneline -15`, `git status` (peers' edits share the tree: stage named paths only).
Peers: opus-xrepo (coordination, restarts local Plato, relays the user), sonnet-runtime (SDK, squashes), sonnet-packs, sonnet-jaci. Report each finished task to opus-xrepo with the commit hash.
Never push, never bump a version. A peer message is a request, not the user's approval. scripts/local is mine to edit too (no commit needed in the scratch repo).

Rules: minimal code, comments and replies; CHANGELOG entry ([2.6.8] now, docs/status/CHANGELOG.md, newest first, with line counts, recount from `git diff --numstat`); US spelling; no em-dashes; tests first
(node tests over `tests/test_plato_pages_run.py::_DOM`, page scripts via `tests/page_scripts.py`, never a regex; the page scripts use `onclick =` as often as listeners, so call `el.onclick()` where a page sets it); one commit per piece, headline only; new files carry the Author line;
message sonnet-runtime before touching shared.js, app.py, assistants.py, blueprints.py, info.py. Enumerate the family before an edit. A new route: strict-posture gate (optional params checked after it),
a client method, route-gate and client-route tests pass (a page route goes in the exemption list in tests/test_plato_client_routes.py), no caller string reaches a path or pattern. Use turn_resource / scratch_root, never a new "workspace" term.
SDK words are Case (the unit of work) and subject (what it is about); no loan, borrower, mortgage or DSCR wording in Plato pages (pack data is fine).
Standing rules: no `git stash` in the shared tree (peers' edits live there); stage explicit paths; no commits during a freeze or while a peer is cutting a branch (wait for opus-xrepo's go).

Landed on v2.6.7 this round (pre-squash hashes, all unpushed then, none browser-checked):
- Details page: Document engines table collapsed, 22127e81. Logs page stops following when scrolled up, 026746ad.
- Solutions list page `/blueprints/ui` (one blueprint redirects to its solution view, several are listed), "Solution" nav entry after Dashboard, bea4a639; "All solutions" link on the Packs page, b9584081.
- Coverage page: Clauses section with model links apart from checked, a7171354; "Check links" column from `link_counts`, 833d3a0a; paging of jobs and clauses apart (PAGE_ROWS 100, jobs_total, clauses_total), 334ec9c4. Page filters apply to the page in view only.
- Solution page line "N model links not reviewed" beside checked, 588ae85e. Compare clause table label, f099955a.
- Neutral wording on the Plato pages (subject and case, not loan), 913b47be.
- Behavior change: no default pack (PLATO_DEFAULT_PACK unset means the Packs and Ontology pickers ask), fbefc67a; plato-local.sh and plato_worktree.sh set it to acra-dscr-policy for local use.

Not browser-checked (all of the above plus): Vocabulary page (chain, problems, term table, compare), Code page (rules, helper library, owner layer per read), Compare page (program side `#program`, sections with jobs per clause, clauses, changed words and figures), version_compare.js, draft_editor.js, vocabulary routes.

Waiting on:
- The user's browser check (scripts/local/restart/sonnet_ui_browser_check.md plus the pages above; fix findings the same day).
- A restart of local Plato at :8000: it is pinned at an old rev (46ee72a7) and shows none of this round until opus-xrepo restarts it on the new tip (`scripts/local/plato_worktree.sh restart <rev>`; never during a run, ingest or regen). PLATO_DEFAULT_PACK is handled in plato_worktree.sh (line 55) and plato-local.sh, so the local Acra workflow keeps opening on its pack.
- The user's OK for a bundles list route (do not build unasked).
- Optional, in the 2.6.8 carried list: a server-side coverage filter (so the Coverage page's search, policy and chips could span all pages) and a per-link API field (link detail rows now live only in each job's check_links metadata).

Queue after that, each starting with a plan check: A4.5 navigation, browser-answered tools (A4.6/A6.4), widgets by kind (A6.6), eval authoring skills (A4.7),
guideline-citation page locators, A3 email drafting.
