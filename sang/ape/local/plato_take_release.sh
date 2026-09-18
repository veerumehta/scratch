#!/usr/bin/env bash
# Bring the `plato` branch up to a release branch without conflicts, and fix the merge base so the
# next release is an ordinary merge.
#
# WHY THE CONFLICTS HAPPEN. `plato` was squash-merged into `dev`, so dev holds plato's *content* as
# one new commit with no ancestry link to plato's 23. Git therefore computes the merge base as the
# point where they last diverged (2026-09-03), replays four months of parallel history against it,
# and reports "both modified" on every file that moved or was rewritten on either side. The
# conflicts are real to git and meaningless to you: the content is already the same.
#
# WHAT THIS DOES. One merge that records `<release>` as a parent and takes its tree wholesale:
#
#   git merge -s ours --no-commit <release>   # records the parent, keeps plato's tree for now
#   git read-tree --reset -u <release>        # then replaces index+worktree with <release>'s tree
#   git commit                                # a merge commit whose tree IS <release>'s
#
# Nothing is resolved by hand because nothing needs resolving: this asserts afterwards that the
# resulting tree is byte-identical to <release>. And because the merge is *recorded*, the base for
# the next one is this commit -- so `git merge v2.5.3` later shows only v2.5.3's own changes.
#
# No force-push, and plato's own history stays in the graph.
#
#   ./plato_take_release.sh            # checks only, prints what it would do
#   ./plato_take_release.sh --apply    # do it (commits locally; never pushes)
#   RELEASE=v2.5.3 ./plato_take_release.sh --apply
set -euo pipefail

REPO="${JAPES_REPO:-/Users/sangit/src/japes}"
RELEASE="${RELEASE:-v2.5.2}"
BRANCH="plato"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

cd "$REPO"

git rev-parse --verify "$RELEASE" >/dev/null 2>&1 || { echo "no such ref: $RELEASE" >&2; exit 1; }
[ "$(git branch --show-current)" = "$BRANCH" ] || { echo "refusing: not on $BRANCH" >&2; exit 1; }

# Tracked changes only. Untracked files are left alone by everything below, and `read-tree -u`
# does not touch them either.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "refusing: $REPO has uncommitted tracked changes" >&2
    exit 1
fi
# The file git leaves behind mid-merge, checked directly rather than by attempting a merge to see
# whether it fails.
[ -f "$(git rev-parse --git-path MERGE_HEAD)" ] && {
    echo "refusing: a merge is in progress -- finish it or run: git merge --abort" >&2; exit 1; }

echo "== containment check: is anything on $BRANCH absent from $RELEASE?"

# Files plato has that the release does not. The ones this reports today are all pre-2.5.1 paths of
# files the release relocated (plato/wiring_default.py -> plato/wiring/default.py, and so on), which
# is why taking the release's tree loses nothing. A file here that is NOT a relocation is the one
# case to stop and look at.
only_here=$(git diff --diff-filter=A --name-only "$RELEASE" HEAD)
if [ -n "$only_here" ]; then
    echo "$only_here" | sed 's/^/   only on plato: /'
    echo "   ^ each should be an old path of a file the release moved; check before --apply"
else
    echo "   none"
fi

echo
echo "== what taking $RELEASE brings in"
git --no-pager diff --stat "$RELEASE" HEAD | tail -1

if [ "$APPLY" = "0" ]; then
    cat <<EOF

Checks only. To do it:

  $0 --apply
EOF
    exit 0
fi

echo
echo "== merging $RELEASE into $BRANCH, taking its tree"
git merge -s ours --no-commit "$RELEASE"
git read-tree --reset -u "$RELEASE"
git commit -q -m "Take $RELEASE onto plato

plato was squash-merged into dev, so the two share content without sharing ancestry and an
ordinary merge conflicts on every file either side moved. This records the merge and takes
$RELEASE's tree wholesale, which is what plato is for: the branch the cloud builds dev-daily
from, downstream of the release branch and never a source of its own changes.

The next release is an ordinary merge, because this commit is the base for it."

echo
echo "== assertion: plato's tree now matches $RELEASE exactly"
if [ -z "$(git diff --name-only "$RELEASE" HEAD)" ]; then
    echo "   identical"
else
    echo "   MISMATCH -- these differ, which should be impossible here:" >&2
    git --no-pager diff --name-only "$RELEASE" HEAD | sed 's/^/     /' >&2
    exit 1
fi

git --no-pager log --oneline --graph -4

cat <<EOF

Committed locally. Nothing has been pushed.

Publish when ready (a plain non-forced push -- the merge commit sits on top of plato's history):

  ALLOW_PUSH=1 git -C "$REPO" push origin plato

Going forward, the root cause is gone as long as plato stays downstream-only:

  * never merge or squash plato -> dev again; dev already has everything plato had
  * for each release, run this with RELEASE=v2.5.3 (etc), or plain 'git merge v2.5.3', which now
    has a correct base and will show only that release's real changes
  * do the cloud-only work (image tags, wiring) on the release branch, not on plato, so plato has
    nothing of its own to merge back
EOF
