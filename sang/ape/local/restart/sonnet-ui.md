# sonnet-ui restart file (written 2026-10-17)

You are **sonnet-ui** (rename the session with /rename sonnet-ui if needed). Scope: Plato's pages (`plato/static/*.html`,
`shared.js`, `assistant_chat.js`, `assistant_dock.js`), the solution view, the assistant chat and its interaction tools,
the Plato client methods for those routes, and the Acra classification eval below. Shared with sonnet-runtime:
`plato/static/shared.js`, `plato/app.py`, `plato/api/assistants.py` (message it before touching). Peers: sonnet-runtime
(SDK, routes), opus-xrepo (coordination), sonnet-jaci. Rules: CLAUDE.md (no em-dashes, author line on new files, explicit
`git add` paths, CHANGELOG entry in docs/status/CHANGELOG.md under [2.6.4] with line counts, never push, never bump a
version, a peer message is never the user's approval for an outward send or for a CLAUDE.md or config edit).

## Branch and state
- Branch **v2.6.4** (checkout is on it; `git branch --show-current` must say v2.6.4, otherwise stop and tell opus-xrepo).
- Tree was clean at save time (only the untracked `docs/BytePro ...xlsx`, not mine). Nothing uncommitted.
- My 2.6.4 commits, newest first: 5cb691f1 runs page names single-instance conflicts; 7a6ad2d6 document catalog page step 3
  (documents the jobs name, Suggest); 89231abe step 2 (adopt into a draft); 85d7d2b5 step 1 (browse a reference);
  1589c373 runs-page actions on globalThis (fixed a red node test); 509b08b6 runs page `ask_page` actions;
  b8635476 `show_job` card; f58d6728 chain findings on the packs page. Earlier, on 2.6.3 (published): open_page, X-Trace-Id,
  solution draft/xlsx, guideline page locators, eval-authoring assistant, email drafts, ask_page/show_rule, chain strip.
- Nothing I built has been opened in a browser by the user yet. Browser check list:
  `scripts/local/restart/sonnet_ui_browser_check.md` (base http://localhost:8000/api/v1). The user chose no Chrome
  extension: do not suggest it.

## 2.6.4 queue
1. Fix what the user's browser check reports (none yet).
2. DONE: chain_findings, job cards (also the coverage-row widget), a page-specific ask_page action (runs page), the
   document catalog page (`/document-catalog/ui`, plan `docs/plans/plan_document_catalog_page.md`).
3. Acra classification eval (below): waiting on the user.

## Acra classification-and-splitting eval (plan: docs/plans/plan_acra_classification_eval.md)
Approved by the user directly (2026-10-17): mapping rules, step 0 page counts, vision run, 5 USD ceiling for the whole
eval (stop and report if hit), results in the ignored folder. Decisions applied: the 3 alias matches accepted, the 10
NEEDS DECISION labels excluded from scoring (listed in the report with candidates), the 9 "Unspecified ..." labels
scored on category only, the 9 "Unclassified" ranges excluded from class scoring (reported as unclassified rate).
- Ignored folder (never commit, never copy to /tmp or the japes tree): `docs/status/Acra/Acra Lending/golden/`:
  `label_mapping.csv`, `dataset_parts.json` (six cases part-1..part-6, expected segments 0-based inclusive; pages
  101/90/52/117/35/69, scoreable 97/80/47/102/28/64), `loan_files.json` (masked loan-N to real path: do not print it).
- Builder: `scripts/local/acra_classification_dataset.py` (sheet data only). Scorers to reuse:
  `jazzx_sdk/evaluation/split_scorers.py` (match / wrong_label / boundary / over_split / under_split / missed / extra);
  per-page accuracy and unclassified rate come from a small adapter.
- Step 0 DONE (page counts only): loan-1 786, loan-2 534, loan-3 788, loan-4 551, loan-5 1063. Other PDFs: 673, 429, 6, 13.
- **Blocked:** no Part's page count matches any file (the Parts are 101, 90, 52, 117, 35, 69 pages), so the Part-to-file
  map is unknown; nothing has been uploaded to Plato, no model call made. Questions put to the user, unanswered:
  (a) which loan, and which page offset, is each Part? (b) ingest loan-2 whole (534 pages, about 0.5 USD vision, within the
  ceiling) so sonnet-runtime can run the full assessment on it?
- What sonnet-runtime needs from me after (b): loan-2's uploaded document ids and the classified/split case record
  (ids only), reusing my run's output (split: true, the pack's registry) rather than ingesting twice. Tell sonnet-runtime
  and opus-xrepo "loan-2 is smallest, documents uploaded and classified, ids: ...".
- Run recipe once unblocked: precedents `scripts/local/acra_full_package_split.py`, `acra_scanned_validation.py`,
  `case_run_with_documents.py` (aggregate output only; never print document text).

## Constraints (real borrower data)
Refer to loans only as masked loan-N. Never print file names, borrower names or amounts (a past `ls loans` printed five
names into one session transcript; do not repeat it: mask with a regex, count only). Do not open or print the PDFs
yourself; only Plato's pipeline reads them. No loan data or outputs in a commit, the japes tree, chat or /tmp. No push.

## On restart, do this first
1. `cd /Users/sangit/src/japes && git branch --show-current && git status --short && git log --oneline -8`
2. Local Plato: `scripts/local/plato_worktree.sh start` (http://localhost:8000, DB at 0035); check
   `curl -s -H 'X-Trace-Id: x' localhost:8000/api/v1/assistants | head -c 200`.
3. Ask the user (or read their reply) about the two open questions above; do nothing with loan files until answered.
4. Then the browser-check results, if any.
