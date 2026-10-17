# opus-xrepo restart file (saved 2026-10-17, before a computer reboot)

You are opus-xrepo, the cross-repo coordinator for japes (jaci, jazzx-assistant, assistant and the rest). Route work to
the builder sessions; do not build in their paths. Never push, never write to GitHub (`gh api` reads are blocked for
you; `scripts/local/pr_new_comments.sh <pr>` and `gh pr view/checks` work). Scripts go to `scripts/local/` (not /tmp,
which a reboot can clear), generic logic in scripts/local. No em-dashes, no AI attribution, no version bumps unasked.
Read CLAUDE.md (cross-repo paragraph) after this file. Sessions: `scripts/local/restart_session.sh list`.

## First, on restart
1. `cd /Users/sangit/src/japes && scripts/local/restart_session.sh list` (who is live, who saved a restart file).
2. Local Plato does not survive a reboot: `scripts/local/plato_worktree.sh start` (pinned worktree
   /Users/sangit/src/japes-plato, :8000, database at 0035). Check `curl localhost:8000/health` (version 0.2.5).
   If it does not start, `scripts/local/plato_worktree.sh status`; the helper's `stop` bug is fixed (fcfaea6 in scratch).
3. `git fetch origin; git status; git log --oneline -3 v2.6.4; git branch --show-current` in /Users/sangit/src/japes.
4. Tell the user, in one short paragraph, what you understood and what waits on them (section "Waiting on the user").

## Where things stand
- Released: v2.6.2 is on main (#95, 5d8f5ef2); v2.6.3 is on dev (#92 squash 6277834e). dev recorded on local plato
  (0abeacdd, parents 1a35ec41 and 6277834e, tree unchanged, NOT pushed yet). origin/plato = 1a35ec41.
- v2.6.4 is cut from dev (417abf1c: SDK 2.6.4, Plato and client 0.2.5; do not bump again). The shared checkout
  /Users/sangit/src/japes is on v2.6.4; second clone /Users/sangit/src/other/japes for isolated work.
- v2.6.4 builder commits, all unpushed and UNREVIEWED: sonnet-runtime (assessment engine modes with hybrid the
  DEFAULT 54bb5550 and a both-in-force warning, document types with external codes/cardinality/scope/attributes,
  tabular catalog reader with header_row, versioned document references and routes, adopt/suggest, descendant
  expansion, unread/single-instance reporting, five jaci client gaps: documents index 0034, document read, record
  outcome, guidance store 0035, reactions, follow_case_run from_seq, RetryPolicy, assess route/client engine_mode;
  tip 1dac85f6), sonnet-ui (chain findings on the packs page, show_job card, runs page ask_page actions, document
  catalog page /document-catalog/ui, single-instance conflicts on the runs page).
- Dependabot: no alerts (user checked). CodeQL alerts on #95 fixed and carried to v2.6.3 (regex, trial path, solution id).

## Acra end-to-end (the active programme)
- Goal from the user: one end-to-end run on ONE real loan packet with our jobs, our code, hybrid, both, compared with
  Acra's K-Studio JTBDs, to show how far we are. sonnet-runtime leads (plans/plan_acra_end_to_end_run.md,
  scripts/local/acra_e2e_run.py, scratch packs acra-e2e-kstudio 0.0.1 and acra-e2e-ours 0.2.18 on local Plato).
  Pairing K-Studio vs ours (guidelines only): standard same 39 / differs 19 / partial 48 / none 17 of 123; platinum 37/11/48/12 of 108.
- References loaded on local Plato (tenant acra-lending): acra-taxonomy@2026-10-17 (152 entries from
  docs/status/Acra/Updated_Loan_Document_Taxonomy.xlsx, sheet Master Taxonomy, header row 5) and bytepro@2026-07-29
  (471 entries). 141 of 152 taxonomy entries are read by no job (72 Core); 4 job documents match no entry
  (loan_application, listing_history, entity_documents, title_agent_verification). Jobs name only 11 coarse documents:
  after jaci adopts the taxonomy into the registry, regenerating jobs should name fine entries (not yet asked).
- sonnet-ui owns the classification eval (docs/plans/plan_acra_classification_eval.md; label_mapping.csv and
  golden/dataset_parts.json in the ignored Acra folder). Step 0 (page counts only) is done: loan-1 786, loan-2 534
  (smallest), loan-3 788, loan-4 551, loan-5 1063; the workbook's six Parts (101, 90, 52, 117, 35, 69 pages) match no file,
  so the Part-to-file map is unknown. Waiting on the user: which loan/offset each Part is; and ingest loan-2 whole
  (about 0.5 USD vision, inside the 5 USD ceiling; my recommendation: yes).
- PRIVACY: docs/status/Acra/Acra Lending/ holds real borrower data (176 files, about 600 MB). It is gitignored in the
  scratch repo (which has a GitHub remote, ahead of origin, NEVER push it). Refer to loans only as loan-N; never print
  file or borrower names; never read the PDFs in a session; outputs only under that ignored folder; reports to the user
  aggregate-only. sonnet-ui printed the loan file names once by mistake (reported to the user). Spend: classification
  eval 5 USD; end-to-end 30 USD total, 8 per variant (the per-variant cap cannot interrupt a server-side reasoned
  assess; I recommended leaving it).
- A session must have the user's OWN approval for anything that sends real documents to providers; my relays do not
  count (sonnet-ui and sonnet-runtime correctly refused them). The user approved step 0 directly in sonnet-ui.
- Acra bundle: docs/status/Acra/acra_bundle is regen 3b (121/110 jobs, 43/56 code). `scripts/local/acra_bundle.py
  --trial X` builds a candidate in /tmp/acra_bundle_candidate; `--promote --archive-as NAME` archives the current best
  and replaces it. The user syncs the folder to SharePoint. Regen 3b coded 50% (120/240) vs regen 2 56% (150/270);
  alignment with Acra's whole set was never measured for 3b (acra_compare_sets.py).

## Waiting on the user
- Own approvals for the loan runs, typed in the builder sessions (sonnet-ui: classification/ingest; sonnet-runtime:
  the end-to-end run). Which loan/offset each Part is. Ingest loan-2 whole (yes recommended).
- Confirm the hybrid default for assessment (54bb5550); run the review over the whole unpushed v2.6.4 range before any push.
- Push local plato (0abeacdd, tree-neutral record of dev; `git push --no-verify` is fine for it).
- Golden set for loan decisions (policy verdicts) and a sanitized Acra loan package are still missing; Acra's case date;
  browser check of every new page (nothing has been opened in a browser); qualifying_rent; Docker for the executor check.

## Mine, not done
- Fix scripts/local/pre_push_check.sh so the hook checks the pushed ref, not HEAD (the last hook review covered 42
  lines = the last commit of v2.6.3, because the hook reviews HEAD and v2.6.3 has no upstream). Design: parse stdin
  refs; if the pushed tree differs from HEAD's tree or tracked files are dirty, run the steps in a throwaway worktree
  at the pushed sha (PYTHONPATH add jazzx_plato_client and jazzx_eval_contracts, unset GIT_DIR, symlink scripts/local,
  absolute STAMP_DIR from the main root); REVIEW_UPSTREAM = the remote sha; stamp by the pushed sha. Test with a toy
  repo and a bare remote. Not started editing.
- Test-suite audit: plans/plan_test_suite_audit.md (615 files, about 8,100 tests, serial ~15 min; try xdist and
  markers). Needs a fresh session in 2.6.4; write its kickoff file under scripts/local/restart/ when the user wants it.
- Minor: gemini-3-flash provenance note in model_data.json still describes the preview as the only entry (sent to
  sonnet-runtime, low). Roberto = the assistant team, Poddar = the jazzx-assistant team (memory).

## How a release goes (what I did this time)
squash_to_plato.sh --src vX --apply (parents origin/plato and origin/dev; use --no-edit if the editor step does not
move plato) -> review (scripts/local/release/japes_review_plato_263b.sh style, REVIEW_FULL=1, from the review worktree
/private/tmp/japes-plato-review) -> push_plato.sh (the hook runs the full suite, about 15 min, never skip it for real
code) -> PR plato->dev squash-merge -> record_dev_squash_on_plato.sh --apply -> cut the next version from dev. A
dev->main squash: merge main back into dev with a tree-neutral merge (scripts/local/release/japes_merge_main_into_dev_262.sh).

## Where the moved files are
On 2026-10-17 the /tmp scripts and notes moved to scripts/local/release (japes_*.sh), acra (acra_*.sh), restart (restart
and kickoff notes) and notes. CLAUDE.md paths were rewritten. Old /tmp paths in older messages are stale.
