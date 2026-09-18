#!/usr/bin/env bash
# Re-base this session's work as a *new* commit on top of the pushed one, instead of an amend of it.
#
# Why: `1e3123e` is pushed and is the commit the deployed image was built from -- the Dockerfile
# bakes JAPES_GIT_COMMIT and `/info` reports it. A force-push would erase the SHA a running replica
# names. Amending it again would keep the branch diverged.
#
# What this does: moves HEAD back to the pushed commit while KEEPING every change staged, then
# commits them as a second commit. No history is rewritten, nothing is pushed, nothing is lost.
set -euo pipefail

PUSHED="1e3123e"
BRANCH="v2.5.2"
MESSAGE="${1:-Bundle a demo assistant pack, diagnose the connection string, and split the common deps into extras}"

cd "$(git rev-parse --show-toplevel)"

# Refuse unless the situation is the one this script was written for.
[ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || { echo "not on $BRANCH"; exit 1; }
git rev-parse --verify "$PUSHED^{commit}" >/dev/null || { echo "$PUSHED not found"; exit 1; }
[ "$(git rev-parse "origin/$BRANCH")" = "$(git rev-parse "$PUSHED")" ] || {
  echo "origin/$BRANCH is no longer $PUSHED -- someone pushed. Stop and re-read."; exit 1; }
git merge-base --is-ancestor "$(git rev-parse "$PUSHED^")" HEAD || {
  echo "HEAD does not descend from the pushed commit's parent"; exit 1; }

echo "Before:"; git log --oneline -2; echo

# A tag, so the amended commit is recoverable if any of this turns out wrong.
git tag -f "pre-unwind-$(date +%Y%m%d%H%M%S)" HEAD >/dev/null

# Soft: index and working tree untouched, so every change becomes staged content of the new commit.
git reset --soft "$PUSHED"
git add -A
git commit -m "$MESSAGE"

echo; echo "After:"; git log --oneline -3
echo
echo "Branch is now $(git rev-list --left-right --count "origin/$BRANCH"...HEAD | awk '{print $2" ahead, "$1" behind"}')"
echo "Nothing pushed. Review with: git show --stat HEAD"
