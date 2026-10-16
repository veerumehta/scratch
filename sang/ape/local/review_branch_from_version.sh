#!/usr/bin/env bash
# Publishes a version branch as one squash commit on a new remote review branch off a base, and cuts
# the next version branch, without touching the base or moving the checkout's HEAD:
#   1. one commit: parent <base>, tree = the tip of <src> (a tree copy, so it is exact and cannot
#      conflict; checked first that the base's history is already inside <covers>'s, and that
#      <covers>'s tree is in <src>'s history, so nothing on the base is reverted);
#   2. local branch <branch> at that commit, pushed to origin after a Dependabot check and a typed y;
#   3. local branch <next> at <next-from>'s tip, default <src> (not switched to, not bumped).
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   review_branch_from_version.sh --src v2.6.2 --branch review/v2.6.2 --next v2.6.3 \
#       --message "<headline>" [--base origin/dev] [--covers origin/plato] [--next-from <ref>]
#
# The push is push_review_branch.sh (NO_VERIFY=1 passes --no-verify; JAPES_SKIP_SUITE=1 skips the suite). A session working in the checkout is not disturbed.
set -euo pipefail

BASE=origin/dev
COVERS=origin/plato
SRC="" BRANCH="" NEXT="" MESSAGE="" NEXT_FROM=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --src) SRC="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --next) NEXT="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    --base) BASE="$2"; shift 2 ;;
    --covers) COVERS="$2"; shift 2 ;;
    --next-from) NEXT_FROM="$2"; shift 2 ;;
    *) echo "unknown argument: $1"; exit 2 ;;
  esac
done
for name in SRC BRANCH NEXT MESSAGE; do
  [[ -n "${!name}" ]] || { echo "missing --$(echo "$name" | tr 'A-Z' 'a-z')"; exit 2; }
done

NEXT_FROM="${NEXT_FROM:-$SRC}"
cd /Users/sangit/src/japes
git fetch origin

# Preconditions.
git merge-base --is-ancestor "$BASE" "$COVERS" \
  || { echo "$BASE has commits $COVERS lacks: a tree copy would revert them. Stop."; exit 1; }
covers_tree=$(git rev-parse "$COVERS^{tree}")
# `grep -c`, not `grep -q`: -q exits at the first match and git log then dies of SIGPIPE, which
# `pipefail` reports as a failed check.
matches=$(git log --format=%T "$SRC" | grep -c -x "$covers_tree" || true)
[ "${matches:-0}" -gt 0 ] \
  || { echo "$SRC's history never had $COVERS's tree: the branches have diverged. Stop."; exit 1; }
git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1 \
  && { echo "origin/$BRANCH already exists. Stop."; exit 1; }
for b in "$BRANCH" "$NEXT"; do
  git show-ref --verify --quiet "refs/heads/$b" && { echo "local branch $b already exists. Stop."; exit 1; }
done

tip=$(git rev-parse "$SRC")
tree=$(git rev-parse "$tip^{tree}")
echo "source: $SRC at $(git rev-parse --short "$tip")"
echo "versions: SDK $(git show "$tip:pyproject.toml" | grep -m1 '^version' | cut -d'"' -f2)," \
     "client $(git show "$tip:jazzx_plato_client/pyproject.toml" | grep -m1 '^version' | cut -d'"' -f2)"
echo "base: $BASE at $(git rev-parse --short "$BASE"); $(git rev-list --count "$BASE..$SRC") commits collapse to one"

new=$(git commit-tree "$tree" -p "$BASE" -m "$MESSAGE")
[ "$(git rev-parse "$new^{tree}")" = "$tree" ] || { echo "tree mismatch. Stop."; exit 1; }
git branch "$BRANCH" "$new"
next_tip=$(git rev-parse "$NEXT_FROM")
git branch "$NEXT" "$next_tip"
echo "created $BRANCH at $(git rev-parse --short "$new") and $NEXT at $(git rev-parse --short "$next_tip") ($NEXT_FROM)"
git diff --stat "$BASE" "$BRANCH" | tail -1

"$(cd "$(dirname "$0")" && pwd)/push_review_branch.sh" "$BRANCH" || exit $?

late=$(git rev-list --count "$next_tip..$NEXT_FROM")
[ "$late" = "0" ] || echo "WARNING: $NEXT_FROM moved on by $late commit(s) during this run; they are not in $NEXT: $(git log --oneline "$next_tip..$NEXT_FROM")"
echo "done. Next: tell the sessions to 'git switch $NEXT', then bump the versions on it."
