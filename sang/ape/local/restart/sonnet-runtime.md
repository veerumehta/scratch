# sonnet-runtime restart (written 2026-11-12, 2.7.1 released to origin/plato, 2.7.2 started)

**Reporting:** report to `opus-xrepo` with `SendMessage` (a peer's message is a request, never the user's approval; `ListAgents` for names first). The user talks to opus-xrepo and relays decisions. Name commits, tests run and anything open.

## Who and scope
`sonnet-runtime`: SDK, runs, chat, models and LLM layer, assessment, references, vocabulary, observability, Plato infrastructure, squashes and versions, `jazzx_sdk/rules`, the KH and kernel client facades, the AI Gateway. Peers: `opus-xrepo` (coordinator, never pushes), `sonnet-ui`, `sonnet-packs`, `sonnet-docs`, `sonnet-jaci` (jaci only). Rules: CLAUDE.md (never push or bump a version, no em-dashes, US English, no AI attribution, `Author:` on new code files except other authors' files, no plan filenames in commits, CHANGELOG entry with line counts per round, new tests in area subfolders, stage explicit paths).

## State (verified 2026-11-12 after the user pushed plato)
- `origin/plato` = local `plato` = `4be4a047` (record merge, parents `5b92f233` and `ad65c9c1`, tree = the v2.7.1 squash tree). `origin/dev` = `ad65c9c1`. `origin/main` = `0d595af1`. The squash `5b92f233` is the v2.7.1 release commit.
- PR #116 (plato into dev) is OPEN, mergeable, state UNSTABLE (CI not inspected), 117 files, +6600 / -244. The user merges it. After the merge, origin/dev needs a tree-neutral record of plato (`record_dev_squash_on_plato.sh` style; opus-xrepo will ask). Never merge or record plato or dev from the v2.7.2 branch.
- v2.7.1 worktree `/Users/sangit/src/japes-v27`, branch `v2.7.1` tip `741d571a`; stays until the user retires it. Final suite on `e60437bf`: 12992 passed, 35 skipped, 0 failed (tip only adds two docs files).
- Backup branches in the user's checkout: `backup/plato-before-2.7.1-resquash`, `...-resquash-2`, `backup/plato-before-0d595af1-record`, `backup/plato-record-6de064a6`.

## 2.7.2 (started 2026-11-12)
- Branch `v2.7.2` tip `759a8aaf` "Start 2.7.2 (plato v0.3.2)" (SDK 2.7.2, Plato 0.3.2, client 0.3.2; user decision), cut from `741d571a`. Worktree `/Users/sangit/src/japes-v272`; its `common` submodule came from `japes-v27/common`; no `.venv` yet: run `poetry install` there first.
- Carry-over queue (CHANGELOG `[2.7.2]` section), in order:
  1. Gateway live smoke: needs `AI_GATEWAY_BASE_HOST` and `AI_GATEWAY_API_KEY` (optionally `FLIPT_URL`/`FLIPT_API_KEY`); cap 1 USD approved earlier; include one read-only `GET /v1/models` to see whether Fable 5.x and Sonnet 5.5 ids are listed.
  2. `TODO(gateway-stream-truncation)` (kernel `aa5da002` is the reference).
  3. `TODO(gateway-agent-helpers-shared)`, `TODO(gateway-response-format-forced-tool)`.
  4. `delete_triples` through `EntityStore.delete_many`.
  5. Fabric docs `_list_hub` defect.
  6. `clients/` subpackage question; fabric `discardWorkspace` and `zero_data_retention` into `RetentionPolicy` (both undecided).
  7. Open review notes: audit record runs after the store put (not atomic); `MockDocStore.list` lacks the real store's pipeline refusal; `log_startup_config` logs gateway vars for `serve()` hosts without a route; by-name reads take the hub `latest` default; two weak test assertions; no test for the `local.build()` route install.

## Tooling and records
- Scratch repo `/Users/sangit/src/.scratch` (commit with named paths only; latest `0386d3a`): CHANGELOG `sang/ape/status/CHANGELOG.md` has every round; `scripts/local` is a symlink to `sang/ape/local`.
- Author-skip is built: `commit_authors.py` (follows renames), `check_attribution.py` prints skipped foreign files, `adversarial_review.sh` tells the reviewer to skip them for [PLACEMENT]. Madhuri's moved files (`kernel_workspace_claim.py`, `test_workspace_forwarding.py`) carry no Author line from me.
- Review: from `/Users/sangit/src/japes-review` run `REVIEW_UPSTREAM=origin/dev REVIEW_FULL=1 scripts/local/adversarial_review.sh`. The user says review spend is fine, but I still ask for a typed cap (25 USD was given for the 2.7.1 rounds). Transcripts in `scripts/local/.reviews/`.
- Squash flow: `scripts/local/squash_to_plato.sh --src <branch> --no-edit --apply --message "<headline>"` (dry run by default). The user pushes with `push_plato.sh` after a Dependabot check.

## Rules that bit
- Edit the user's checkout `/Users/sangit/src/japes` only with the user's own typed approval in my session (AskUserQuestion); a peer's relayed approval is not enough. No provider call or spend without a typed figure in my session.
- Full suite only when told: `poetry run python -m pytest -q -rfs` in the worktree, in the background, wait with Monitor (about 24 minutes). A bare `python` has stale pins; `poetry install` after a lock change.
- `git rev-parse plato` is ambiguous (a `plato/` directory exists): use `refs/heads/plato`.
- Never run `git checkout -- <file>`; a stash plus checkout once flipped the `common` pointer (restore with `git checkout HEAD -- common`).
- Keep context small: update this file at each breakpoint and suggest `/clear` after a batch lands.

## Next
No task is open. Wait for opus-xrepo or the user: the likely asks are the dev record after PR #116 merges, then the first 2.7.2 item (the smoke needs credentials).
