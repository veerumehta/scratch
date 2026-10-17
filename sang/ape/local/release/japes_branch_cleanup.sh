#!/bin/bash
# Removes the plato-kernel-fix worktree and branch, plato-squash-262*, and backup/plato-*.
# Logs each branch tip first so a branch can be recovered with `git branch <name> <sha>`.
set -u
cd /Users/sangit/src/japes
LOG=/tmp/japes_branch_cleanup.log
: > "$LOG"
git worktree remove --force /private/tmp/japes-plato-kernel-fix 2>&1 | tee -a "$LOG"
for b in plato-kernel-fix \
    $(git branch --list 'plato-squash-262*' --format='%(refname:short)') \
    $(git branch --list 'backup/plato-*' --format='%(refname:short)'); do
  echo "$b $(git rev-parse "$b")" | tee -a "$LOG"
  git branch -D "$b"
done
git worktree prune
echo "tips logged in $LOG"
