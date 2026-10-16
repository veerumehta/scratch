#!/usr/bin/env bash
# Record dev's squash-merge of plato as an ancestor of local plato, so the next plato -> dev is not
# a conflict. The mirror of record_squash_on_main.sh, for the plato -> dev release.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# Squash-merging plato into dev gives dev plato's CONTENT as one commit with no ancestry to plato's
# commits, so git later finds a merge base releases ago and reports "both modified" everywhere.
# This adds one merge commit to local plato: parents local plato and origin/dev, plato's tree
# unchanged (the `-s ours` result, built with plumbing so no checkout is needed and unpushed work
# on plato is kept, which plato_take_release.sh would replace with dev's tree).
#
#   scripts/local/record_dev_squash_on_plato.sh            # checks only
#   scripts/local/record_dev_squash_on_plato.sh --apply    # make the merge commit (never pushes)
#
# It refuses unless there is nothing to lose: origin/dev's tree must equal origin/plato's, i.e. dev
# holds exactly what was pushed to plato and nothing else (a change made on dev since would be
# discarded by an `ours` merge, and is a real merge instead).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
APPLY=0; [ "${1:-}" = "--apply" ] && APPLY=1

git fetch --quiet origin
for ref in refs/heads/plato refs/remotes/origin/plato refs/remotes/origin/dev; do
  git rev-parse --verify --quiet "$ref" >/dev/null || { echo "no such ref: $ref" >&2; exit 1; }
done
PLATO=$(git rev-parse refs/heads/plato)
echo "local plato   $(git rev-parse --short "$PLATO")  ($(git rev-list --count origin/plato..plato) unpushed)"
echo "origin/plato  $(git rev-parse --short origin/plato)"
echo "origin/dev    $(git rev-parse --short origin/dev)  $(git log -1 --format=%s origin/dev | cut -c1-70)"

git merge-base --is-ancestor origin/dev refs/heads/plato && { echo "already recorded: origin/dev is an ancestor of plato"; exit 0; }
git merge-base --is-ancestor origin/plato refs/heads/plato \
  || { echo "refusing: local plato is not built on origin/plato (fetch, then rebuild it first)" >&2; exit 1; }
if [ "$(git rev-parse 'origin/dev^{tree}')" != "$(git rev-parse 'origin/plato^{tree}')" ]; then
  echo "refusing: origin/dev differs from origin/plato, so an ours-merge could discard dev's own change:" >&2
  git --no-pager diff --stat origin/plato origin/dev | tail -5 >&2
  exit 1
fi
echo "  ok  origin/dev's tree equals origin/plato's: nothing on dev to lose"
[ "$APPLY" = 1 ] || { echo "checks only; --apply to record it"; exit 0; }

NEW=$(git commit-tree "plato^{tree}" -p "$PLATO" -p origin/dev \
  -m "Record the squash of plato on dev as merged")
git branch -f backup/plato-before-dev-record "$PLATO"
git update-ref refs/heads/plato "$NEW" "$PLATO"
[ "$(git rev-parse 'plato^{tree}')" = "$(git rev-parse "$PLATO^{tree}")" ] || { echo "tree changed" >&2; exit 1; }
git merge-base --is-ancestor origin/dev refs/heads/plato || { echo "dev is not an ancestor" >&2; exit 1; }
echo "recorded: plato $(git rev-parse --short plato), tree unchanged, origin/dev is an ancestor"
