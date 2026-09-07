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
