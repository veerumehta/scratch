#!/bin/sh
# Push v2.5.5 to dev: review/v2.5.5 (f81806c2, review fixes on top of d8818f5c) and dev (730c6c39,
# one squash over the 815e1291 record merge). Both are fast-forwards; no force.
set -eu
cd "$(dirname "$0")/../.."

git fetch -q origin
git merge-base --is-ancestor origin/dev dev || { echo "dev is not a fast-forward of origin/dev"; exit 1; }
git merge-base --is-ancestor origin/review/v2.5.5 review/v2.5.5 \
  || { echo "review/v2.5.5 is not a fast-forward"; exit 1; }
[ "$(git rev-parse 'dev^{tree}')" = "$(git rev-parse 'refs/heads/v2.5.5^{tree}')" ] \
  || { echo "dev tree differs from v2.5.5"; exit 1; }

git push origin refs/heads/review/v2.5.5:refs/heads/review/v2.5.5 refs/heads/dev:refs/heads/dev
git log --oneline -3 origin/dev
