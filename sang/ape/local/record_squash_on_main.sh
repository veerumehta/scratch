#!/usr/bin/env bash
# Record a squash-merge of dev -> main as an ancestor of dev, so the next merge is not a conflict.
#
# THE PROBLEM THIS SOLVES. Squash-merging dev into main gives main dev's *content* as one new
# commit with no ancestry to the commits it came from. Git then computes the merge base for the
# next dev -> main as the last point they genuinely shared -- releases ago -- replays everything
# since against it, and reports "both modified" on every file either side touched. It did this on
# PR #70: 51 conflicted files, 31 of them add/add, and every single resolution was "take dev".
#
# WHAT THIS DOES. One merge commit on dev with main as a second parent and dev's tree unchanged:
#
#   git merge -s ours origin/main
#
# `-s ours` keeps this branch's tree exactly and records the other side as a parent. It never
# conflicts. It is also the one command here that can silently lose work -- it discards the other
# side's content by design -- so this refuses to run until it has proved there is nothing to lose:
#
#   1. no file exists on main that is absent from dev
#   2. for every file the two differ on, main's exact blob appears somewhere in dev's own history
#      for that path -- i.e. main's version is a point in dev's lineage, not separate work
#
# If a hotfix ever lands on main directly, check 2 fails on that file and this stops. Then it is a
# real merge, not a bookkeeping one.
#
#   ./record_squash_on_main.sh            checks only
#   ./record_squash_on_main.sh --apply    check, then record
set -euo pipefail

REPO="${JAPES_REPO:-/Users/sangit/src/japes}"
BRANCH="${BRANCH:-dev}"
BASE="${BASE:-main}"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

cd "$REPO"
[ "$(git branch --show-current)" = "$BRANCH" ] || { echo "refusing: not on $BRANCH" >&2; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "refusing: uncommitted tracked changes" >&2; exit 1; }
[ -f "$(git rev-parse --git-path MERGE_HEAD)" ] && { echo "refusing: a merge is in progress" >&2; exit 1; }

git fetch origin "$BASE" "$BRANCH" --quiet

if git merge-base --is-ancestor "origin/$BASE" HEAD; then
    echo "origin/$BASE is already an ancestor of $BRANCH -- nothing to record"
    exit 0
fi

echo "== check 1: files on origin/$BASE that $BRANCH does not have"
missing=$(git diff --diff-filter=A --name-only HEAD "origin/$BASE")
if [ -n "$missing" ]; then
    echo "$missing" | sed 's/^/   /'
    echo "   ^ these would be DISCARDED. Stop: this is a real merge." >&2
    exit 1
fi
echo "   none"

echo "== check 2: is every differing file's main version a point in $BRANCH's own history?"
differing=$(git diff --name-only HEAD "origin/$BASE")
if [ -z "$differing" ]; then
    echo "   the trees are identical"
else
    unproven=0
    total=0
    while read -r f; do
        [ -n "$f" ] || continue
        total=$((total + 1))
        blob=$(git rev-parse "origin/$BASE:$f" 2>/dev/null) || continue
        found=no
        for c in $(git log --format=%H HEAD -- "$f"); do
            if [ "$(git rev-parse "$c:$f" 2>/dev/null || true)" = "$blob" ]; then found=yes; break; fi
        done
        if [ "$found" = "no" ]; then
            echo "   NOT in $BRANCH's history: $f" >&2
            unproven=$((unproven + 1))
        fi
    done <<< "$differing"
    echo "   $((total - unproven))/$total differing files are accounted for in $BRANCH's history"
    if [ "$unproven" -gt 0 ]; then
        echo "   ^ $unproven file(s) hold content that never existed on $BRANCH. Stop: real work on" >&2
        echo "     $BASE would be discarded by -s ours. Merge those by hand instead." >&2
        exit 1
    fi
fi

snapshot=""
base_tree=$(git rev-parse "origin/$BASE^{tree}")
for c in $(git log --format=%H HEAD); do
    if [ "$(git rev-parse "$c^{tree}")" = "$base_tree" ]; then snapshot="$c"; break; fi
done
[ -n "$snapshot" ] && echo "   (origin/$BASE's tree is $BRANCH at $(git log -1 --format='%h %s' "$snapshot"))"

if [ "$APPLY" = "0" ]; then
    echo
    echo "Checks pass. To record it:"
    echo
    echo "  $0 --apply"
    exit 0
fi

head_commit=$(git rev-parse --short "origin/$BASE")
echo
echo "== recording origin/$BASE ($head_commit) as merged into $BRANCH"
git merge -s ours "origin/$BASE" -m "Record the $head_commit squash on $BASE as merged

$BASE holds this branch's content as one squashed commit, with no ancestry to the commits it came
from. Left unrecorded, the next $BRANCH -> $BASE merge reaches back to the last shared point and
conflicts on every file either side touched, with every resolution being 'take $BRANCH'.

This records $BASE as a parent and keeps $BRANCH's tree, which the checks in
scripts/local/record_squash_on_main.sh proved is the right tree everywhere: no file on $BASE is
absent here, and every differing file's $BASE version is a point in this branch's own history."

if [ "$(git rev-parse HEAD^{tree})" = "$(git rev-parse HEAD^1^{tree})" ]; then
    echo "   tree unchanged -- $BRANCH's content is exactly as it was"
else
    echo "   MISMATCH: the merge changed the tree, which -s ours cannot do" >&2
    exit 1
fi

git --no-pager log --oneline --graph -3

cat <<EOF

Committed locally. Nothing has been pushed.

  ALLOW_PUSH=1 git -C "$REPO" push origin $BRANCH

After this, $BASE is an ancestor of $BRANCH again and the next release merge starts from here.
EOF
