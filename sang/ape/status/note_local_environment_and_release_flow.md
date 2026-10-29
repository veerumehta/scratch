# Local environment and release flow (moved out of the session file, 2026-10-28)

Author: Virendra Mehta

Reference for the workstation setup and the path from a version branch to `main`. The session file keeps only the short rules.

## Local services

- **Plato (:8000)** runs from its own worktree, `/Users/sangit/src/japes-plato`, pinned to a commit, so a branch switch in the main
  checkout cannot break a running server (it did on 2026-10-11: a lazy import of a moved module failed every extraction run).
  `scripts/local/plato_worktree.sh pin|start|stop|restart [rev]|status`. The env file, pack blobs and cache, and documents stay in
  the main checkout, named absolutely. Log: `.plato-local.log`. It starts from `$MAIN/.venv`, so the venv needs the CI extras
  (`poetry install --extras "mcp templating finance pptx mlflow gemini formal plato azure"`). A restart must pass
  `JAPES_RUN_BUDGET_USD` (per run) and `JAPES_PAGE_CACHE_DIR` (cached page reads are borrower data: keep it under the gitignored
  Acra Lending tree). Never restart during a run, ingest or regen.
- **Postgres 17.11 on :55432**, data in `~/.local/share/japes-pg/17`, started by hand with
  `pg_ctl -D ~/.local/share/japes-pg/17 -o "-p 55432 -k /tmp" -l ~/.local/share/japes-pg/17.log start` (no launchd entry, it does not
  survive a reboot). The 16 data directory and a dump stay beside it for rollback (`scripts/local/pg_upgrade_local_17.sh`).
- **Review worktree** `/Users/sangit/src/japes-review`: `git checkout --detach plato`, then
  `REVIEW_UPSTREAM=origin/plato scripts/local/adversarial_review.sh japes` launched detached (a token-heavy run, about 3 to 4 USD a slice).
  Check that no review process is running and the main tree has no tracked changes first.

## From version branch to main

1. Work lands on the version branch (`vX.Y.Z`, cut from `dev`). Never commit to `dev`.
2. `scripts/local/squash_to_plato.sh --src vX.Y.Z --no-fetch --no-edit --apply --message "<headline>"` makes ONE commit on local `plato`
   with parents `origin/plato` and `origin/dev` (plato must not be checked out; the first plato commit carries the version in its headline).
3. Review from the worktree until PASS; fixes go on the version branch, then re-squash.
4. The user checks Dependabot (alerts follow `main`'s dependency graph, not the pushed branch), rebuilds `.venv` from the lock, runs
   `scripts/local/pre_push_check.sh --ci-versions` from a `plato` checkout, then `scripts/local/push_plato.sh`. Its PR title and body
   are hard-coded and stale: open the PR by hand.
5. PR `plato` to `dev`, then `dev` to `main`; record each squash on the other branches with a tree-preserving merge
   (`scripts/local/record_squash_on_main.sh`) so ancestry stays usable. Fixes for a PR round go on `dev` first, then carry.

## Squash merges break ancestry

`git log A ^B` overstates what is missing after a squash. Compare trees: walk the source branch for the commit whose tree matches the
target, and take the delta from there. A `git merge --squash` from a long-diverged branch hits stale-base conflicts every time; where the
target provably carries no work of its own, `git read-tree -u --reset <source>` is exact and conflict-free. Check that precondition first:
`dev` once carried a security fix `v2.5.4` lacked, and a tree copy would have reverted three CVE alerts.

## PR comments

`scripts/local/pr_new_comments.sh <pr>` lists bot comments since your last reply; `scripts/local/resolve_pr75_threads.py` replies to and
resolves threads. Run the full-range review (`REVIEW_UPSTREAM=origin/main` for a PR to main) before a PR round, not only per-commit
ones: per-commit reviews cannot see untouched code, which is what the bot kept finding.

## Spend and borrower data

Loan files are real borrower data: `docs/status/Acra/Acra Lending/` is gitignored in the scratch repo (which has a GitHub remote and is
never pushed), masked loan-N only, and nobody opens the PDFs. Any run that sends documents to a provider needs the user's own typed
approval in the builder session (a relayed approval does not count), a ceiling, and a ledger row (`acra-cost-ledger`). DocIntel is
0.01 USD a page; a 325-page loan packet costs about 3.4 USD cold and about 0.3 USD with a warm page cache.
