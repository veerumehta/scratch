# Local Dev Tooling

Workspace-specific scripts for day-to-day work in this checkout — not build/deploy automation (see
`scripts/README.md` for that), and not meant to be shared: this whole directory is gitignored.
Assumes the usual sibling-repo layout under `~/src/` (japes, juno, eval-service, macer, jaci, kernel,
client-api, knowledge_hub, jazzx-assistant, assistant, ...).

## `sister_repo_activity.sh` - Recent commits across sibling repos

Read-only survey of recent commits in the other JazzX repos under `~/src/` — for "anything
interesting land in X lately?" instead of manually `cd`-ing and running `git log` in each.

**Usage:**
```bash
./scripts/local/sister_repo_activity.sh                      # default repos, last 7 days
./scripts/local/sister_repo_activity.sh juno eval-service     # specific repos only
./scripts/local/sister_repo_activity.sh --days 1              # today only, default repos
./scripts/local/sister_repo_activity.sh --days 14 macer       # wider window, one repo
./scripts/local/sister_repo_activity.sh --no-fetch            # skip network fetch, use local state
```

Fetches (`--all`) before listing unless `--no-fetch`; never modifies a sibling repo. Override the
assumed `~/src/`-equivalent root via `SISTER_REPOS_SRC_DIR` if this checkout doesn't live there.

## `squash_to_plato.sh` - Squash a version branch onto local plato (dry run by default)

`squash_to_plato.sh [--src BRANCH] [--message TEXT] [--no-fetch] [--no-edit] [--apply]`. Builds one commit with
the source branch's tree and parents `origin/plato` and `origin/dev` (default source: the checked-out
branch; default message: origin/plato's tip subject). Without `--apply` it only reports: the refs, each
precondition (clean tree, plato not checked out, the source already carries everything `origin/dev`
has, local plato not diverged, something to squash), the diffstat, and the message. `--apply` opens
your editor on the commit message first (`--no-edit` skips it; an empty message aborts), then moves
local `plato`; it never pushes. Run `push_plato.sh` after the review.

## `push_plato.sh` - Push the local plato squash and open the PR to dev

Pushes local `plato` (one squash commit of the current version branch, parents `origin/plato` and
`origin/dev`) and opens the PR `plato` -> `dev`, after checking both ancestries and listing open
Dependabot alerts on `main`. Asks before the push and before the PR; run it yourself, since nothing
else pushes.

## Promoted out of here

`plato_wiring.py` now lives in `scripts/` (tracked): the wall it clears -- Plato refusing to start
without a `PLATO_WIRING` -- is not workstation-specific, so every clone needs it.

## `check_attribution.py` - New files carry attribution, and no AI markers

Every file added to this repo carries `Author: Virendra Mehta <virendra.mehta@jazzx.ai>`, and
nothing may hint the work was AI-assisted. Both are easy to miss on a file created mid-task and
awkward to spot in a large diff.

**Usage:**
```bash
python scripts/local/check_attribution.py                  # new files vs origin/dev + untracked
python scripts/local/check_attribution.py --base main      # compare against a different base
python scripts/local/check_attribution.py path/to/file.py  # just these paths
```

Checks `.py/.yml/.yaml/.sh/.toml/.md` (data files have nowhere to put a header). Exits 1 on a miss,
so it can gate a commit. Lives here rather than in `scripts/`: it enforces a personal convention and
names the marker strings it searches for, neither of which belongs in a shared repo.

## Adding a new local script

Same bar as anything else here: read-only or clearly-scoped, documented above, executable
(`chmod +x`). If it turns out to be useful enough that other clones of this repo should have it too,
promote it into `scripts/` proper (tracked) instead of leaving it here.

## `commit_and_fold_plato.sh` - Commit on the version branch, fold into one commit on plato

Replaces the hand-run `git commit` then `git commit-tree` pair. Dry run by default; `--apply`
commits the changed files on the checked-out version branch (refusing on any other branch, which is
how plato drifted), fetches, and points local `plato` at ONE commit on the current `origin/plato`
with the version branch's tree. Unpushed plato commits fold into it and keep their message; what is
already on `origin/plato` is built on, never rewritten. Keeps the old tip as
`backup/plato-before-fold`. Never pushes.

```bash
./scripts/local/commit_and_fold_plato.sh -m "Fix the review" --apply
./scripts/local/commit_and_fold_plato.sh --no-commit --apply   # fold an already-committed branch
```

For a PR's comments use `pr_dump.sh <pr>` (whole bodies, read-only), not an ad hoc script.

## `record_dev_squash_on_plato.sh` - Register dev's squash of plato as merged

After a plato -> dev squash-merge: one merge commit on local `plato` (parents plato and
`origin/dev`, tree unchanged) so the next plato -> dev is not a conflict. Mirror of
`record_squash_on_main.sh`. Checks only by default; `--apply` records it. Refuses unless dev's tree
equals `origin/plato`'s (nothing on dev to discard) and plato is built on `origin/plato`. Keeps
unpushed plato work, unlike `plato_take_release.sh`, which takes the release's tree. Never pushes.
