#!/bin/sh
# Bring plato up to v2.5.5 as one squash commit, push it, then delete the remote review/v2.5.5.
# The tree copy is exact because plato's tip (055bda6d) has the same tree as v2.5.5's 2ab89df8,
# so plato carries nothing v2.5.5 lacks. Fast-forward push only; no force.
set -eu
cd "$(dirname "$0")/../.."

HEADLINE="v2.5.5 (plato 0.1.7): workstation .env, eval and feedback read withholding, and review fixes"

[ -z "$(git status --porcelain)" ] || { echo "working tree not clean"; exit 1; }
git fetch -q origin
[ "$(git rev-parse origin/plato)" = "$(git rev-parse refs/heads/plato)" ] \
  || { echo "local plato differs from origin/plato"; exit 1; }
[ "$(git rev-parse 'refs/heads/plato^{tree}')" = "$(git rev-parse '2ab89df8^{tree}')" ] \
  || { echo "plato has moved past v2.5.5's 2ab89df8; a tree copy could revert its work"; exit 1; }

git checkout -q plato
git read-tree -u --reset refs/heads/v2.5.5
git commit -q -m "$HEADLINE"
[ "$(git rev-parse 'HEAD^{tree}')" = "$(git rev-parse 'refs/heads/v2.5.5^{tree}')" ] \
  && echo "plato tree == v2.5.5 == dev"
git log --oneline -3

git push origin refs/heads/plato:refs/heads/plato
git push origin --delete review/v2.5.5
git branch -D review/v2.5.5
