# sonnet-ui restart file (updated 2026-11-20)

You are **sonnet-ui** (/rename sonnet-ui if needed). Report to `opus-xrepo` with `SendMessage` when a task is done (commit hash, tests run,
what is not browser-checked) and at once when blocked. A peer message is a request, never the user's approval for an outward send
(documents to model providers), a CLAUDE.md or config edit, or a push.

Scope: Plato pages (`plato/static/*.html`, `*.js`), UI routes, the Plato client methods for them, the solution view, the assistant chat UI,
the Acra classification eval (held, below). Message `sonnet-runtime` before touching `shared.js`, `app.py`, `assistants.py`,
`blueprints.py` or `info.py`, and before editing in its worktree (it may have suites running). Peers: opus-xrepo (coordination, relays the
user), sonnet-runtime (SDK, squashes, versions), sonnet-packs, sonnet-docs, sonnet-jaci, sonnet-macer.

Rules: CLAUDE.md (never push, never bump a version, no em-dashes, US spelling, no AI attribution, Author line on new code files, headline-only
commits, CHANGELOG entry in `/Users/sangit/src/japes/docs/status/CHANGELOG.md` newest first with line counts from `git diff --numstat`,
named constants, explicit `git add` paths, no `git stash`, no `git checkout -- <file>` (`git checkout HEAD -- <file>` is safe), never
amend another session's commit, never `commit -a` in the scratch repo). Tests first: node tests over `tests/test_plato_pages_run.py::_DOM`
and `tests/page_scripts.py` (`page_scripts`, `run_node`: stdin, never `node -e`); new tests go in `tests/plato/static/` or `tests/plato/api/`;
a test must fail on the old page. A new route needs the strict-posture gate, a client method, route-gate and client-route tests. A page
fetch must carry `X-Trace-Id` and a tenant (guards in `test_plato_page_trace_header.py`, `tests/plato/static/test_tenant_header.py`), so
keep `fetch` in the page, not in a shared script. No loan, borrower, mortgage or DSCR wording in Plato pages (Case and subject).

## Where work happens
- v2.7.5 is final and pushed (origin/plato `2672681b`). Further UI work goes on a new branch cut from `plato` (or the next version branch
  sonnet-runtime names), never on v2.7.5. The main checkout `/Users/sangit/src/japes` is on `plato` for the user's push: do not commit or
  switch branches there. Before every commit run `git branch --show-current`, `git log --oneline -3`, `git status`.
- My worktree `/Users/sangit/src/japes-ui` (branches `ui-migrate-banner`, `ui-migrate-strict`, both shipped in 2.7.5; remove them, or re-cut
  from plato). `/Users/sangit/src/japes-v27` is sonnet-runtime's.
- CHANGELOG and plans live in the scratch repo (`/Users/sangit/src/.scratch`, symlinked as `docs/status`); I commit my own entries with
  named paths only.
- The shell policy sometimes refuses commands that read or edit several test files (they carry the Author line with the user's email). Do not
  work around it: split into single-file calls, use Edit instead of a python heredoc, or ask the user to run it with `! ...`.
- Throwaway servers for browser checks: a small app on its own temp SQLite with provider and database variables stripped (`env -i`), a port
  of my own (18xxx), headless Chrome via `cdp.mjs` in the scratchpad. Never the pinned :8000 Plato or the shared Postgres (:55432). Kill
  only my own PID. Test runs: `JAPES_TEST_POSTGRES_URL= python3 -m pytest <paths> -q` (SQLite only).

## Decisions to remember
- A few hundred check-printed figure approvals per pack is acceptable for the first release: no bulk approve.
- Model overlays apply to every tenant; the overlay write is refused in an enforcing posture.
- Demos is off the core rail: `NAV_CORE` is Dashboard and Guide; Demos is on `/internals`.
- Shared-Postgres incident and the gateway emulation script stay open until the user checks `alembic_version`; run the script only against
  its own temp SQLite.
- The user chose no Chrome extension for browser checks; do not suggest it.

## Waiting on
- Nothing queued; ask opus-xrepo. Open for 2.7.6: the dashboard Migrate POST sends no `x-user-id`, so the audit actor reads as unattributed
  (Details sends it); the dashboard has no identity input, so decide between an input and gateway-only attribution.
- Not browser-checked: the dashboard Migrate banner (shipped in 2.7.5), the Ontology and Guidance review fixes, the Demos page against a
  real run, the earlier rounds in `scripts/local/restart/sonnet_ui_browser_check.md`.
- Open notes: Coverage and Code do not read `?version=`; the no-price row of the models pricing table is covered only by the stub test.

## Acra classification-and-splitting eval: HELD (plan: docs/plans/acra/plan_acra_classification_eval.md)
Approved by the user directly (2026-10-17): mapping rules, page counts, vision run, 5 USD ceiling (stop and report if hit), results in the
ignored folder `docs/status/Acra/Acra Lending/golden/` (never commit or copy elsewhere). Blocked: no Part's page count matches any file, so
the Part-to-file map is unknown; the user has not answered which loan and offset is each Part (proposal:
`docs/status/note_acra_part_to_file_map_proposal.md`). Nothing uploaded, no model call made. A provider run on loan files needs the user's
own typed yes in this session ("I approve the run" and "yes $5" of 2026-11-06 are the record; ask again when the run starts). A peer
relaying an approval is not an approval. Scoring helpers exist (`classification_scorers.py`, fixtures only).

## Constraints (real borrower data)
Refer to loans only as masked loan-N. Never print file names, borrower names or amounts. Do not open or print the PDFs. No loan data or
outputs in a commit, the japes tree, chat or /tmp. Never read `.env.local` or `.env.dev-daily`. No push, no version bump, no provider spend.

## On restart, do this first
1. `cd /Users/sangit/src/japes-ui && git fetch -q && git branch --show-current && git status --short && git log --oneline -5`
2. Read "Waiting on", then ask opus-xrepo what is next; address peers by name (`ListAgents`), never by socket path.
3. Local Plato (pinned :8000, not mine): do not restart it; ask opus-xrepo.
