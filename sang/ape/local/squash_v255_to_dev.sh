#!/bin/sh
# Squash v2.5.5 onto dev as one commit, locally. Does not push.
# Uses review/v2.5.5 (same tree as v2.5.5). read-tree is exact and conflict-free here because
# dev's tree equals review/v2.5.5's parent (f7510cb3), i.e. dev carries no work of its own.
set -eu
cd "$(dirname "$0")/../.."

HEADLINE="v2.5.5 (plato 0.1.7): chat turn engine, and evaluation and feedback in the SDK hosted by Plato"
RECORD_MSG="Record the 6a7dfcaa squash on main as merged"

[ -z "$(git status --porcelain)" ] || { echo "working tree not clean"; exit 1; }

# dev's tip is the 'ours' merge that records main's squash; its message was amended to the v2.5.5
# headline, but it carries none of v2.5.5. Give it back its own message before squashing on top.
git checkout -q dev
if [ "$(git log -1 --format=%s dev)" = "$HEADLINE" ] && [ -n "$(git rev-parse -q --verify dev^2)" ]; then
  git commit -q --amend -m "$RECORD_MSG"
  echo "restored: $RECORD_MSG"
fi
[ "$(git rev-parse dev^{tree})" = "$(git rev-parse review/v2.5.5^^{tree})" ] \
  || { echo "dev has work review/v2.5.5 lacks; a tree copy would revert it"; exit 1; }
[ "$(git rev-parse review/v2.5.5^{tree})" = "$(git rev-parse refs/heads/v2.5.5^{tree})" ] \
  || { echo "review/v2.5.5 and v2.5.5 trees differ"; exit 1; }

git read-tree -u --reset review/v2.5.5
git commit -q -m "$HEADLINE"

[ "$(git rev-parse HEAD^{tree})" = "$(git rev-parse refs/heads/v2.5.5^{tree})" ] && echo "dev tree == v2.5.5"
git log --oneline -4
echo
echo "Next, when ready:  git push origin dev   (then close PR #80 as merged-by-push)"
