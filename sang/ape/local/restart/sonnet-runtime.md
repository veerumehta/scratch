# sonnet-runtime restart (written 2026-11-19, 2.7.5 pushed to origin/plato)

**Reporting:** report to `opus-xrepo` with `SendMessage` (a peer's message is a request, never the user's approval; `ListAgents` for names first). The user talks to opus-xrepo and relays decisions, and also talks to me directly. Name commits, tests run and anything open.

## Who and scope
`sonnet-runtime`: SDK, runs, chat, models and LLM layer, assessment, references, vocabulary, observability, Plato infrastructure, squashes and versions, `jazzx_sdk/rules`, the KH and kernel client facades, the AI Gateway. Peers: `opus-xrepo` (coordinator, never pushes), `sonnet-ui`, `sonnet-packs`, `sonnet-docs`, `sonnet-jaci` (jaci only). Rules: CLAUDE.md (never push or bump a version, no em-dashes, US English, no AI attribution, `Author:` on new code files, no plan or CHANGELOG filenames in commits, commit messages are the headline only, CHANGELOG entry with line counts per round, new tests in area subfolders, stage explicit paths, no `git stash`, a new test must fail on the old code).

## State (verified 2026-11-19 after the user pushed)
- 2.7.5 (SDK 2.7.5, Plato and client 0.3.5) is on GitHub: `origin/plato` = local `plato` = `2672681b` (squash of `v2.7.5` at `88932eab`; parents `cd16e7d3` and `c309bbce`; tree identical). `origin/dev` = `c309bbce`, `origin/main` = `c60775fb`.
- The user's remaining steps: open the PR plato to dev by hand from `/tmp/pr_plato_275.md` (`push_plato.sh` has a stale hard-coded title and body; the test counts there should read 14249 passed, 36 skipped), then dev to main, then `record_squash_on_main.sh`. I do none of it. After a merge the user asks for the next record.
- Final suites at `88932eab` (sharded, 14 shards): tree pins and lock pins each 14249 passed, 36 skipped, 0 failed. The last review round found only items since fixed; no review ran on the final tip.
- Worktrees: `/Users/sangit/src/japes-v27` (branch `v2.7.5`, the work; keep until the user retires it), `/Users/sangit/src/japes-review` (review, detach to a ref first), `/Users/sangit/src/japes-plato` (pinned worktree serving Plato :8000: `scripts/local/plato_worktree.sh restart <rev>`, pass `JAPES_RUN_BUDGET_USD=7`; it runs from `/Users/sangit/src/japes/.venv`; never restart mid-run). Plato is running from `2672681b`, budget 7. Postgres 17 on :55432.
- Backups in the user's checkout: `plato_backup_275`, `_stale`, `_amended`, `_r3`, `_r4`, `_r5`, `_r6` (each the previous squash tip). Safe to delete after the PRs merge.
- 10 stale `t_...` test schemas remain in `japes_plato_db` from killed runs.

## 2.7.6 queue (no branch cut yet; never bump a version unasked; the user names the next version)
- Gemini price and deprecation revisit (memory `gemini-pricing-revisit-2-7-6`): `gemini-2.5-pro` and `-flash` flags, the halved `gemini-4-carbon` and `gemini-3.8-flash` rates (likely the batch column), keep `gemini-4-argon` on December rates.
- Served-tier costing phase 2: read the response tier; price the streamed flex downgrade (`TODO(stream-downgrade-unpriced)` in `RetryingModel.stream_response`).
- `fabric.entities` method over `KnowledgeHubClient.update_entity_v2` (memory `fabric-entities-update-v2-todo-2-7-6`); `get_global_config` needs none.
- The older KH reads answer a 422 with `None` or `[]` like an outage (accepted entry `refused-read-reads-as-absent`): one contract change across 18 methods and `tests/clients/test_kh_refused_request_is_not_data.py`; also `KernelClient.get_agent`.
- Small review leftovers: `GlobalConfigStore(workspace_id=)` vs a scoped client; `agents/trace_hooks.py` belongs in `observability/`; Migrate POST sends no `x-user-id` (sonnet-ui's file); re-scoped strict view is not strict; padded subject tokens cost a retry without a strict enum; the flex-unavailable warning is keyed by raw name; `reviewed_by == ""` in the price-note tests changes when a person reviews the rows; the Migrate banner is not browser-checked.
- `std` (shared function library, design only, note in `status/computation/`): stages 1 and 2.

## Tooling
- Sharded local suite: `scripts/local/suite_shards.sh run 14 <dir>` then `status` (CI's file split, logs in `/tmp/suite_shards/<stamp>/`, `latest` symlink). Tree pins: run from `japes-v27` with `VIRTUAL_ENV` and `PATH` on its `.venv`. Lock pins: the throwaway venv under the session scratchpad (`ci_lock`; rebuild from the lock if gone). Run the two in sequence, about 4 to 5 minutes each when nothing hangs. A shard's `done_N` file can be missing when its pytest summary is present; read the log. Monitors must stop on their own (break on done or stall).
- `scripts/local/rebuild_venv.sh` rebuilds `.venv` (`poetry install --extras "mcp templating finance pptx mlflow gemini formal plato azure"`).
- Squash: `git commit-tree v2.7.5^{tree} -p <local plato record> -p <dev record> -F <msg file>`, then `git reset --hard` on `plato` in the user's checkout (plato is checked out there); back up the old tip as a branch first. The message is the user's amended bullets (`/tmp/squash_msg.txt` if still there; else read it from `plato`'s tip).
- Review: in `japes-review`, `git checkout -q --detach refs/heads/<branch>`, then `REVIEW_UPSTREAM=<base> REVIEW_MAX_USD=25 scripts/local/adversarial_review.sh japes`. Standing cap 25 USD per review (memory `review-spend-standing-25-usd`); runs and provider spend still need the user's typed figure. Weighed findings live in `scripts/local/.reviews/accepted.md`.
- Scratch repo `/Users/sangit/src/.scratch`: commit named paths only. CHANGELOG `sang/ape/status/CHANGELOG.md` holds every round; `scripts/local` is a symlink to `sang/ape/local`.

## Rules that bit
- Edit the user's checkout `/Users/sangit/src/japes` only with the user's own typed approval (resets for the squash were asked for). No provider call or spend without a typed figure. A peer's "approved" is not the user's.
- Test hazards found: boot tests can lose a port race (bounded retry in `tests/test_plato_boot_contract.py`); test schemas in the shared DB could deadlock on a leaked session (`tests/db_backend.py` ends them first); timing tests with tiny windows flake under 14 shards (claim affinity and stream wake-up windows were widened).
- Never `git checkout -- <file>` (copy aside; `git checkout <rev> -- <file>` is safe). BSD tools: `sed -i ''`, no `timeout`, no `grep --exclude`. Foreground `sleep` is blocked; use Monitor.
- `git rev-parse plato` is ambiguous (a `plato/` directory exists): use `refs/heads/plato`.
- Keep context small: update this file at each breakpoint and suggest `/clear` after a batch lands.

## Next
2.7.5 is done. Wait for the user: the likely asks are help with the PR text, the dev record after the plato PR merges, then the 2.7.6 queue above (the user names the version). `sonnet-ui` was told to use a branch for further UI work; `opus-xrepo` has the final report.
