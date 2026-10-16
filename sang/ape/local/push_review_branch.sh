#!/usr/bin/env bash
# Pushes a local review branch to origin: prints the open Dependabot alerts on main, asks for a typed
# y, then pushes with upstream tracking.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   push_review_branch.sh <branch>
#
# The pre-push hook runs the test suite and the adversarial review over the pushed range.
# JAPES_SKIP_SUITE=1 skips only the suite; NO_VERIFY=1 skips the hook (`git push --no-verify`).
set -euo pipefail
BRANCH="${1:?usage: push_review_branch.sh <branch>}"
cd /Users/sangit/src/japes
git show-ref --verify --quiet "refs/heads/$BRANCH" || { echo "no local branch $BRANCH"; exit 1; }
git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1 \
  && { echo "origin/$BRANCH already exists; not pushing."; exit 1; }

echo "open Dependabot alerts on main:"
gh api repos/JazzX-LLC/japes/dependabot/alerts \
  -q '.[] | select(.state=="open") | "  \(.security_advisory.severity) \(.dependency.package.name): \(.security_advisory.summary)"' \
  || echo "  (could not read alerts)"
read -r -p "push $BRANCH to origin? type y: " answer
[ "$answer" = "y" ] || { echo "not pushed."; exit 0; }
if [ "${NO_VERIFY:-}" = "1" ]; then
  git push --no-verify -u origin "$BRANCH"
else
  git push -u origin "$BRANCH"
fi
