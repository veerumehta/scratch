#!/usr/bin/env bash
# Cherry-pick the v2.5.3 review fixes onto dev, so PR #72 carries them to main.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   ./scripts/local/cherry_pick_to_dev.sh
#
# Commits locally and pushes nothing. Verified in a throwaway worktree at dev: it applies with no
# conflict and the suite passes (5737, with `test_common_submodule_deps` excluded -- a worktree
# has no submodule checked out).
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

REVIEW=04ed57f    # Close the loose ends the pull request review found

[ -z "$(git status --porcelain)" ] || { echo "working tree is dirty; commit or stash first" >&2; exit 1; }
git checkout dev

git cherry-pick "$REVIEW"

git log --oneline -3
echo
echo "Nothing pushed. Review, then push dev yourself."
