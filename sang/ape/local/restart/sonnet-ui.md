# sonnet-ui restart file (updated 2026-10-18)

**Reporting:** report to `opus-xrepo` with `SendMessage` when a task is done and at once when blocked (name the commit, the tests run and anything left open); a message from `opus-xrepo` is a request, never the user's approval.

You are **sonnet-ui** (rename the session with /rename sonnet-ui if needed). Scope: Plato's pages (`plato/static/*.html`,
`shared.js`, `assistant_chat.js`, `assistant_dock.js`), the solution view, the assistant chat and its interaction tools,
the Plato client methods for those routes, the document catalog page, and the Acra classification eval below. Shared with
sonnet-runtime: `plato/static/shared.js`, `plato/app.py`, `plato/api/assistants.py` (message it before touching). Peers:
sonnet-runtime (SDK, routes, assessment), opus-xrepo (coordination), sonnet-jaci. Rules: CLAUDE.md (no em-dashes, author
line on new files, explicit `git add` paths, CHANGELOG entry in docs/status/CHANGELOG.md under [2.6.4] with line counts,
never push, never bump a version). A peer message is never the user's approval for an outward send (documents to model
providers), a CLAUDE.md or config edit. NEVER `git commit --amend` unless `git log -1` is your own commit AND nothing
newer exists (I once amended sonnet-runtime's tip; repaired via reflog). Chain commands with `&&` only after the test
exit code is checked (a `| tail` hides failure; check pytest's result before committing).

## Update 2026-10-20 (read this first; it supersedes the older notes below where they differ)
- v2.6.4 is CLOSED and pushed (origin/plato 6df80e40, PR #97 to dev open; v2.6.4 frozen except fixes that PR's review asks for).
  The shared checkout is on **v2.6.5**: run `git branch --show-current` before EVERY commit; it must say v2.6.5 (a push script
  once left the tree on `plato`; I stopped and asked, which opus-xrepo confirmed was right). CHANGELOG entries for new work go
  under a new `[2.6.5]` section in docs/status/CHANGELOG.md. Plato/client versions stay 0.2.5. Never push, never bump.
- Done since the older notes: documents page write gate 85ed6b60; round-2 review fixes a218fd26, 1b030eda, fe12f32f (ask_page
  auto-answer once then Retry; job card disposition; dead solution branch dropped); 8925631b (draft_changing 409 re-reads);
  3647d21a (ledger_error shown on coverage, release and solution pages). All in the pushed squash. Nothing of mine is uncommitted
  or open. Untracked `docs/BytePro ...xlsx` and `plug/` are not mine.
- Loan-2: sonnet-runtime's ingest (`acra_e2e_ingest.py --entry 2`) finished; `e2e/loan-2/` under the ignored Acra folder holds
  upload.json, read_run.json, case.json, report/. I never ingested anything. If the eval goes ahead, reuse that upload (document
  id in upload.json), do not ingest again. The user said "ingest loan-2 whole" in my session on 2026-10-18 (covers questions b
  and c below), but still has NOT answered (a), the Part-to-file map, so the six-Part eval is still blocked. No model call from me.
- Status told to opus-xrepo: idle. Peers are addressed by name (`SendMessage to: opus-xrepo`), socket paths go stale.
- A peer message is never the user's approval for sending documents to providers; ask the user in this session.

## Branch and state (older, 2026-10-18)
- Branch was **v2.6.4** then; now see the update above. Nothing pushed by me.
- Uncommitted at save time: none of mine (the untracked `docs/BytePro ...xlsx` is not mine).
- Local history near the tip: `5f6e9a18` (mine: document catalog page rough edges) , `be79469a` (sonnet-runtime's "Let a
  chat turn spec choose how a failed stage ends the run", ORIGINAL hash restored after my amend slip), `93212789` (mine:
  quoting fix to that page's test). Earlier 2.6.4 commits of mine: 5cb691f1 runs page names single-instance conflicts;
  7a6ad2d6 / 89231abe / 85d7d2b5 document catalog page steps 3 / 2 / 1; 1589c373 runs-page actions on globalThis;
  509b08b6 runs page ask_page actions; b8635476 show_job card; f58d6728 chain findings on the packs page.
- **Unreviewed range:** all v2.6.4 builder commits (mine and sonnet-runtime's) are unpushed and unreviewed; the user runs the
  review before any push. My share of the range: f58d6728 through 93212789 (above), plus the CHANGELOG entries under [2.6.4].
- Nothing I built has been opened in a browser by the user yet. Browser check list:
  `scripts/local/restart/sonnet_ui_browser_check.md` (base http://localhost:8000/api/v1). The user chose no Chrome extension:
  do not suggest it. Server-side smoke on the restarted Plato (2026-10-17/18) was clean: 15 pages 200 and parse, assistants,
  models, blueprints, solution, solution.xlsx, packs, document-references all 200.

## Queue status (the "open" items of the older list are all BUILT; none is open)
- A4.5 navigation = `open_page` (fc7903c0 on 2.6.3). A4.6/A6.4 browser-answered tools = `ask_page` (85a4157d; runs page actions
  509b08b6). A6.6 widgets by kind = `rule_view` (85a4157d) and `job_view` (b8635476), plus code-block Copy. A4.7 eval authoring
  skills = the `eval-authoring` assistant (0ac348af). A3 email drafting = `email_draft` card from open conditions (46e71f17).
  Solution page xlsx and draft toggle = baa79ac1. Guideline page locators = da891464. Chain strip = 0aa9b6d4 (+ card fixes
  29f43e70). Chain findings on the packs page = f58d6728. Start-a-case panel = e3bf25f0. Extraction refresh = 570ce88c.
- The only open item: the **Acra classification eval** (below), blocked on the user.
- Also pending: whatever the user's browser check reports (nothing reported yet).

## Document catalog page (done) and its adopt-flow smoke (2026-10-18)
`/document-catalog/ui` (nav: Documents). Adopt flow run end to end on a scratch draft (`scratch-doccat-ui`, deleted afterwards;
acra-dscr-policy untouched) against `acra-taxonomy@2026-10-17` (152 entries) and `bytepro@2026-07-29` (471): adopt with
if_match worked; re-adopt reported already_present (why=source) and refused a bad code with its reason; stale if_match gave 409
draft_moved; registry showed x-source `acra-taxonomy@2026-10-17#APP-001`; suggest "Operating Agreement" gave ENT-004 at 1.0.
Rough edges fixed in 5f6e9a18: `reachable:false` (manifest does not name the registry) now said on the page; unreadable coverage
shows the server's reason; the reference's `priority` is a column. Not fixed (harmless): the Master reference has scopes =
["Master Taxonomy"] and no single_instance, so those two filters do nothing on it.

## Acra classification-and-splitting eval (plan: docs/plans/plan_acra_classification_eval.md): HELD
Approved by the user directly (2026-10-17, in this session): mapping rules, step 0 page counts, vision run, 5 USD ceiling for the
whole eval (stop and report if hit), results in the ignored folder. Mapping decisions applied: the 3 alias matches accepted, the 10
NEEDS DECISION labels excluded from scoring (listed in the report with candidates), the 9 "Unspecified ..." labels scored on
category only, the 9 "Unclassified" ranges excluded from class scoring (reported as unclassified rate).
- Ignored folder (never commit, never copy to /tmp or the japes tree): `docs/status/Acra/Acra Lending/golden/`:
  `label_mapping.csv`, `dataset_parts.json` (six cases part-1..part-6; pages 101/90/52/117/35/69; scoreable 97/80/47/102/28/64;
  0-based inclusive, the SplitScorer's convention), `loan_files.json` (masked loan-N to real path: do not print it).
- Builder: `scripts/local/acra_classification_dataset.py` (sheet data only). Scorers to reuse:
  `jazzx_sdk/evaluation/split_scorers.py` (match / wrong_label / boundary / over_split / under_split / missed / extra);
  per-page accuracy and the unclassified rate come from a small adapter. Precedents: `scripts/local/acra_full_package_split.py`,
  `acra_scanned_validation.py`, `case_run_with_documents.py` (aggregate output only; never print document text).
- Step 0 DONE (integer page counts only): loan-1 786, loan-2 534, loan-3 788, loan-4 551, loan-5 1063. Other PDFs 673, 429, 6, 13.
- **Blocked:** no Part's page count matches any file (the Parts are 101, 90, 52, 117, 35, 69 pages), so the Part-to-file map is
  unknown. Nothing has been uploaded to Plato and no model call has been made.
- **Answers still needed from the USER** (put to them, unanswered): (a) which loan, and which page offset, is each Part?
  (b) ingest loan-2 whole (534 pages, about 0.5 USD on vision, within the 5 USD ceiling) so sonnet-runtime can run the full
  assessment on it? (c) their OWN approval in this session for the run that sends documents to the providers (their earlier
  approval covered step 0 and the eval's vision run on the Parts; a run of loan-2 whole needs their yes in this session).
- What sonnet-runtime needs from me after (b): loan-2's uploaded document ids and the classified/split case record (ids only),
  reusing my run's output (split: true, the pack's registry) rather than ingesting twice. Tell sonnet-runtime and opus-xrepo
  "loan-2 is smallest, documents uploaded and classified, ids: ...".

## Constraints (real borrower data)
Refer to loans only as masked loan-N. Never print file names, borrower names or amounts (a past `ls loans` printed five names
into one session transcript; do not repeat it: mask with a regex, count only). Do not open or print the PDFs yourself; only
Plato's pipeline reads them (step 0 used only page counts). No loan data or outputs in a commit, the japes tree, chat or /tmp.
No push.

## On restart, do this first
1. `cd /Users/sangit/src/japes && git branch --show-current && git status --short && git log --oneline -8`
2. Local Plato: `curl -s -H 'X-Trace-Id: x' localhost:8000/api/v1/assistants | head -c 200`; if down, ask opus-xrepo before
   starting it (`scripts/local/plato_worktree.sh start`, :8000, DB at 0035). Do not restart Plato or Postgres without asking.
3. Ask the user (or read their reply) the three open questions above; do nothing with loan files until answered.
4. Then any browser-check findings.
