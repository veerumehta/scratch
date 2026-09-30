#!/bin/sh
# Squash v2.5.6 onto dev and onto plato (one commit each), then push both as fast-forwards.
#   dev:   its tree is v2.5.6's base (7a7a0950, the formal squash), so the copy adds only 2.5.6.
#   plato: its tree is v2.5.5's (730c6c39), which v2.5.6 contains, so the copy adds formal + 2.5.6.
# Each precondition is re-checked below; a tree copy onto a branch with work of its own would revert it.
set -eu
cd "$(dirname "$0")/../.."

DEV_HEADLINE="v2.5.6 (plato 0.1.7): python custom scorers run on a workstation through a local executor"
PLATO_HEADLINE="v2.5.6 (plato 0.1.7): formal SMT verification, and python custom scorers through a local executor"
SRC=refs/heads/v2.5.6

tree() { git rev-parse "$1^{tree}"; }

[ -z "$(git status --porcelain)" ] || { echo "working tree not clean"; exit 1; }
git fetch -q origin
for b in dev plato; do
  [ "$(git rev-parse refs/heads/$b)" = "$(git rev-parse refs/remotes/origin/$b)" ] \
    || { echo "local $b differs from origin/$b"; exit 1; }
done
[ "$(tree refs/heads/dev)" = "$(tree 7a7a0950)" ] || { echo "dev has moved past 7a7a0950"; exit 1; }
[ "$(tree refs/heads/plato)" = "$(tree 730c6c39)" ] || { echo "plato has moved past 730c6c39"; exit 1; }
git merge-base --is-ancestor 730c6c39 $SRC || { echo "v2.5.6 does not contain 730c6c39"; exit 1; }

squash() {  # branch headline
  git checkout -q "$1"
  git read-tree -u --reset $SRC
  git commit -q -m "$2"
  [ "$(tree HEAD)" = "$(tree $SRC)" ] && echo "$1 tree == v2.5.6"
  git log --oneline -2
}
squash dev "$DEV_HEADLINE"
squash plato "$PLATO_HEADLINE"
git checkout -q v2.5.6

git push origin refs/heads/dev:refs/heads/dev refs/heads/plato:refs/heads/plato
