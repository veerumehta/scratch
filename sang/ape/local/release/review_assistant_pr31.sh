#!/bin/bash
# Adversarial review of jazzx-assistant PR #31 (JAPES-V2 -> main), run from a throwaway worktree.
# The diff is ~9,200 lines (66 files), over the default 4,000-line cap, so the cap is raised.
# Removes a stale worktree from an earlier (hung) run first.
set -u
REPO=/Users/sangit/src/jazzx-assistant
WT=/tmp/jazzx-assistant-pr31
cd "$REPO" || exit 1
git worktree remove --force "$WT" 2>/dev/null
git worktree prune
git fetch origin main JAPES-V2 || exit 1
git worktree add --detach "$WT" origin/JAPES-V2 || exit 1
cd "$WT" || exit 1
REVIEW_UPSTREAM=origin/main REVIEW_MAX_LINES=12000 REVIEW_FULL=1 \
  /Users/sangit/src/japes/scripts/local/adversarial_review.sh jazzx-assistant-pr31
STATUS=$?
echo "review exit $STATUS; remove the worktree with: git -C $REPO worktree remove --force $WT"
exit $STATUS
