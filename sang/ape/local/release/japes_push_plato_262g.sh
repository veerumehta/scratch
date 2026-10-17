#!/usr/bin/env bash
# Push the v2.6.2 squash: branch plato-squash-262g (846d8bde), ONE commit on origin/plato (8d50b9e3, which
# already holds the KernelClient fix and the werkzeug/multidict lock) whose tree is the tree of v2.6.2's tip
# e0702c30. A fast-forward; nothing already pushed is rewritten.
#
# The adversarial review over the range is done: round 5 passed on the fixes; the Plato-to-SDK moves were
# reviewed (72cd283f..977d67c1, one defect fixed in 807ea245, which then passed); the rest is a docstring,
# seed description text, the version bump and a pricing data edit (model_data.json). Suite 8909 green on 807ea245. So the push skips the hook's review:
#
#   a. checks origin/plato, the branch's shape and its tree;
#   b. lists the open Dependabot alerts on main;
#   c. asks y/N;
#   d. pushes the branch to origin/plato with the normal hooks, JAPES_SKIP_REVIEW=1 (its lock, paths, deps
#      and suite steps still run);
#   e. fast-forwards local plato.
# Local plato is at origin/plato until then; backup/plato-7ea54543 holds the old stale squash.
set -euo pipefail
cd /Users/sangit/src/japes

BASE=8d50b9e3; NEW=846d8bde; BRANCH=plato-squash-262g; TIP=e0702c30

git fetch -q origin
[[ "$(git rev-parse --short=8 refs/remotes/origin/plato)" == "$BASE" ]] \
  || { echo "refusing: origin/plato is not $BASE" >&2; exit 1; }
[[ "$(git rev-parse --short=8 "refs/heads/$BRANCH")" == "$NEW" ]] \
  || { echo "refusing: $BRANCH is not $NEW (re-squashed? update this script)" >&2; exit 1; }
git merge-base --is-ancestor refs/remotes/origin/plato "refs/heads/$BRANCH" \
  || { echo "refusing: origin/plato is not an ancestor of $BRANCH" >&2; exit 1; }
[[ "$(git rev-list --count "refs/remotes/origin/plato..refs/heads/$BRANCH")" == "1" ]] \
  || { echo "refusing: $BRANCH is not exactly one commit past origin/plato" >&2; exit 1; }
[[ "$(git rev-parse "refs/heads/$BRANCH^{tree}")" == "$(git rev-parse "$TIP^{tree}")" ]] \
  || { echo "refusing: $BRANCH's tree is not tip $TIP's" >&2; exit 1; }
if [[ "$(git rev-parse --short=8 refs/heads/v2.6.2)" != "$TIP" ]]; then
  echo "note: v2.6.2 has moved past $TIP since this squash was built; those commits are not in it."
fi
git diff --shortstat refs/remotes/origin/plato "refs/heads/$BRANCH"

echo "Open Dependabot alerts on main:"
gh api repos/JazzX-LLC/japes/dependabot/alerts -q '.[] | select(.state=="open") | "  #\(.number) \(.security_advisory.severity) \(.dependency.package.name)"' || true

read -r -p "Push $BRANCH to origin/plato? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "aborted"; exit 1; }

JAPES_SKIP_REVIEW=1 git push origin "refs/heads/$BRANCH:refs/heads/plato"

# local plato follows origin/plato (it is not checked out; `plato` is also a directory name)
git fetch -q origin
git merge-base --is-ancestor refs/heads/plato refs/remotes/origin/plato \
  || { echo "refusing to move local plato: it is not behind origin/plato" >&2; exit 1; }
git branch -f plato refs/remotes/origin/plato
echo "local plato: $(git rev-parse --short=8 refs/heads/plato) ; origin/plato: $(git rev-parse --short=8 refs/remotes/origin/plato)"
