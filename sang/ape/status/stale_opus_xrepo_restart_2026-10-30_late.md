You are opus-xrepo (cross-repo coordinator for japes). Read CLAUDE.md first, then this file. Route, do not build in builder paths. Never push, never write to GitHub, never bump a version unasked. One-off files go in /tmp with short names. No em-dashes, no AI attribution. Check ListAgents before relaying (a /rename breaks messaging). Archive of the older state: docs/status/stale_opus_xrepo_restart_2026-10-30.md.

## State, 2026-10-30
- Branch v2.6.7 (SDK 2.6.7; Plato and client 0.2.7 since 0dc33fb5, user-approved 2026-10-30), writer prompt 97885fe1, derived metadata 35c0337a, all unpushed. sonnet-ui has uncommitted blueprints.html work; tests/test_plato_page_trace_header.py[blueprints.html] fails until it lands. Released: main e5c7128e, dev a95556c3, origin/plato cb256157; local plato 0f1e473e is a tree-equal sync of dev (user pushes it). jaci dev fb14dee (aliases, vocabulary, pack 0.2.19, mlflow 3.17.2, Pulte packs with guide coverage and topic index; nothing published) is 3 ahead (bb5b95d, 0d35ea0, fb14dee), unpushed (user pushes after pre_push_check.sh). sonnet-jaci holds for E1-E6 and the user's answers (workshop bank, taxonomy mapping, client adoption step 1).
- Local Plato :8000 on 46ee72a7. Restart only with no run in flight: `JAPES_RUN_BUDGET_USD=7 JAPES_PAGE_CACHE_DIR="<japes>/docs/status/Acra/Acra Lending/e2e/page_cache" scripts/local/plato_worktree.sh restart <rev>`. The browser check does not block work; restart on the final tip when the user is ready for it.
- Landed on v2.6.7 this round: rerun latest, typed stop_reason, workspace disambiguation B C D (A and E HELD; no sub_tenant or workspace terms), clause links by exported id, sequence assignment, Plato-to-SDK eval move (eval.py 362 to 121 lines), typed no_baseline, ExperimentOutcome, subject baselines (table eval_subject_baseline, migration 0036), seed pack synced to 0.2.19.
- Identity regen-6 done (0.128 USD): mnemonics and sections complete, slug median 9; equivalence vs K-Studio 0.159 (v17) and 0.05 (v7) strict, grain differs; a person reads a label sample before anyone quotes it. Outputs ape/local/coverage/regen_6.

## Queued with sonnet-runtime (user approved; runtime was idle at last look, confirm it is on C-E)
1. C, D, E of docs/plans/plan_job_export_derivations.md.
2. single_case_dataset (the workbench will increase SDK use).
3. Writer-prompt skeptic pass, then the edit; the measuring run needs its own typed approval with a figure.
4. Plan, then build, of pack option rerun.when_unchanged: continue | stop_copy | stop_empty (default continue; keyed on no_impacted_rules).
5. Squash prep when I ask: hold until 1 and 2 land unless the user wants 2.6.7 cut earlier.
Squash flow: tree-neutral record of origin/dev on v2.6.7, real merge of any origin/plato content, squash_to_plato.sh, full-range review rounds from /Users/sangit/src/japes-review (git checkout --detach plato; REVIEW_UPSTREAM=origin/plato), user pushes, PRs target plato.

## Pulte home-mortgage blueprint (user decisions 2026-10-30)
- Edition: June 2026 Selling Guide. Adopt existing jobs (Pulte catalog 115, Rule Map links unreviewed), no generation spend; guide stored as one guideline set (blob) with SourceRef provenance. jaci commits Pulte content (packs, coverage, topic index); publishing to local Plato waits for the user. Blueprint seed file goes to sonnet-packs (japes seed_blueprints). Plans: plan_batched_section_planning (built), plan_adopt_existing_jtbds, plan_source_documents_as_blob_content. Rules library may keep evolving, folds into 2.6.7. Pending reports: sonnet-packs (workbench jtbd_audit and codec helper candidates).

## 2.6.7 squash headline (user, 2026-10-30)
Option A for now, final wording when the last items settle: `v2.6.7 (plato v0.2.7): evaluation control plane in the SDK, guide-scale policy adoption with model links kept apart from checked, batched planning with a spend ceiling, guide-style job export`. Before the squash: import reads from loan_metrics with the bracket-qualifier lint (runtime), sonnet-packs helpers (LIB_VERSION 1.1.2), topic index and resolver only if the user wants provenance verification in 2.6.7 (lean: defer to 2.6.8). 58 commits past origin/dev at last count; user pushes.

## 2.6.8 started (2026-10-30)
User pushed plato (18bbded9, headline A; origin/plato confirmed by runtime's fetch). Branch v2.6.8 cut from the v2.6.7 tip, Start 2.6.8 = 2a2098f5 (Plato and client stay 0.2.7), checked out in the shared tree. origin/dev is still a95556c3 (0 behind, 95 ahead of v2.6.8): when dev takes the 2.6.7 squash, v2.6.8 needs the tree-neutral record (`git merge -s ours origin/dev`) after the carries-everything check. Carried list: plan_2_6_8_carried_from_2_6_7 (scratch). Still the user's: PR plato to dev then main; jaci commit of the Pulte 0.2.1 bump (needs yes in the jaci session) and push; Q-10, eight readings, 0.13 USD measuring figure (packs); Hub answers on ontology fields; Plato restart. Safety branches to delete when the user likes: plato-sync-before-2.6.7-squash, plato-pre-resquash*.

## 2.6.7 squash state (2026-10-30)
Local plato 67bf1929 = squash with headline A, parents origin/plato cb256157 and origin/dev a95556c3; tree-equal to v2.6.7 (tip d66a69f2 after the tree-neutral record of origin/dev); suite 11373 green. Old sync kept on plato-sync-before-2.6.7-squash: do NOT push it first (push the squash alone, fast-forward from cb256157). Full-range review running (user launches it from /Users/sangit/src/japes-review, REVIEW_UPSTREAM=origin/plato; worktree lacks `common`, no tests there). v2.6.7 FROZEN until findings are weighed; fixes via the owner, then re-run the squash. After review: user pushes plato, PR targets plato; jaci dev 3 ahead plus the Pulte 0.2.1 commit to come (user pushes).

## Case and subject (user, 2026-10-30)
Neutral terms: Case (unit of work, fabric.canonical CaseContext) and subject (the entity: loan, customer, patient). Default metrics key `subject_metrics`, interchange key per pack (`metrics_key: loan_metrics` for Pulte and Acra); graph IRIs not moving in 2.6.x; lock key subject-keyed `{subject_id}:{operation}` (user decided; two cases on one subject serialize on purpose). sonnet-runtime building (plan_case_and_subject_words.md); then squash prep (v2.6.7 is 3 behind origin/dev: tree-neutral record first). Local plato 0f1e473e (7 ahead of origin/plato, tree-equal to dev) is ready for the user to push.

## Other sessions
sonnet-ui: assistants.py rename done; its queue is its own. sonnet-packs: Acra note final, repointing build.py at the status copy. sonnet-jaci: holds job_examples.yaml out of jaci.

## Mine
- Policy-workbench team: no question to send (user, 2026-10-30). They follow their own path and adopt SDK functionality when ready.
- Scratch repo (named paths only): the git mv of note_acra_vs_ours_differences_and_provenance.md to status is staged, CHANGELOG.md modified, docs/status/Acra/acra_vs_ours_differences/ untracked, this file and the stale archive uncommitted. Refresh /tmp/commit_restart_files.sh before running it.

## Still the user's
Push local plato (Dependabot is clean, 2026-10-30; the browser check does not block squash prep); Plato/client 0.2.7; the eight readings; bundles route; billed DocIntel figure (~20.6 USD est.); repeat hybrid (~0.4 USD); /tmp/message_to_aditya.md and optionally /tmp/message_to_roberto.md; the platform's scope-name answer (then revise /tmp/pr101_comment.md); pushing jaci.
