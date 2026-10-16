#!/usr/bin/env bash
# Commit the working tree on the version branch, then fold it into ONE unpushed commit on local plato.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   scripts/local/commit_and_fold_plato.sh -m "headline" [--src v2.6.1] [--plato-message TEXT] [--no-commit] [--add] [--apply]
#
# Dry run by default: lists what would be committed and every precondition. With --apply it
#   1. refuses unless the source branch is checked out (a commit on plato is how the two drift),
#   2. fetches (a read), so plato is built on origin/plato as it is now, never a stale copy,
#   3. commits the changed and untracked files (not ignored ones) on the source branch with -m,
#   4. points local plato at ONE commit on origin/plato whose tree is the source branch's: unpushed
#      local plato commits are folded into it and keep their message unless --plato-message is
#      given; with none unpushed, the commit takes -m. The old plato tip is kept as
#      backup/plato-before-fold.
# --add puts the commit on top of local plato as it is (parent: local plato), for a plato that
# carries a recorded merge (record_dev_squash_on_plato.sh) a fold onto origin/plato would drop.
# It never pushes and never writes to GitHub. Anything already on origin/plato is only built on,
# never rewritten. --no-commit folds an already-committed source.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SRC="" MSG="" PMSG="" COMMIT=1 APPLY=0 ADD=0
while [ $# -gt 0 ]; do
  case "$1" in
    --src) SRC="${2:?--src needs a branch}"; shift 2 ;;
    -m) MSG="${2:?-m needs text}"; shift 2 ;;
    --plato-message) PMSG="${2:?--plato-message needs text}"; shift 2 ;;
    --no-commit) COMMIT=0; shift ;;
    --add) ADD=1; shift ;;
    --apply) APPLY=1; shift ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
done

HERE=$(git symbolic-ref --short HEAD 2>/dev/null || true)
case "$HERE" in v[0-9]*) [ -n "$SRC" ] || SRC="$HERE" ;; esac   # a version branch checked out is the source
[ -n "$SRC" ] || SRC=$(git for-each-ref --format='%(refname:short)' 'refs/heads/v[0-9]*' | grep -v -- '-' | sort -V | tail -n 1)
[ -n "$SRC" ] || { echo "no source branch: pass --src" >&2; exit 2; }
[ "$HERE" = "$SRC" ] || { echo "check out $SRC first (on '$HERE'): committing elsewhere makes plato drift" >&2; exit 1; }
[ "$COMMIT" = 0 ] || [ -n "$MSG" ] || { echo "-m is required to commit (or pass --no-commit)" >&2; exit 2; }

git fetch --quiet origin
git rev-parse --verify --quiet refs/remotes/origin/plato >/dev/null || { echo "no origin/plato" >&2; exit 1; }
[ -z "$(git diff --cached --name-only)" ] || echo "note: staged changes are included in the commit"

changed=$( (git diff HEAD --name-only; git ls-files --others --exclude-standard) | sort -u )
LOCAL=$(git rev-parse --verify --quiet refs/heads/plato || true)
UNPUSHED=0
[ -n "$LOCAL" ] && UNPUSHED=$(git rev-list --count origin/plato..refs/heads/plato)
if git merge-base --is-ancestor origin/plato "${LOCAL:-origin/plato}" 2>/dev/null; then BASED=yes; else BASED=NO; fi
echo "source         $SRC $(git rev-parse --short HEAD)"
echo "origin/plato   $(git rev-parse --short origin/plato)"
echo "local plato    ${LOCAL:+$(git rev-parse --short "$LOCAL")} ($UNPUSHED unpushed, built on origin/plato: $BASED)"
echo "to commit      $(printf '%s\n' "$changed" | grep -c . || true) file(s)"
[ "$APPLY" = 1 ] || { echo "dry run; --apply to commit and fold"; exit 0; }

if [ "$COMMIT" = 1 ]; then
  [ -n "$changed" ] || { echo "nothing to commit" >&2; exit 1; }
  printf '%s\n' "$changed" | xargs git add --
  git commit -q -m "$MSG"
fi

if [ "$ADD" = 1 ]; then
  [ -n "$LOCAL" ] || { echo "--add needs a local plato" >&2; exit 1; }
  PARENT="$LOCAL"; PMSG="${PMSG:-${MSG:-$(git log -1 --format=%B HEAD)}}"
else
  PARENT=origin/plato
  if [ -z "$PMSG" ]; then
    if [ "$UNPUSHED" -gt 0 ] && [ "$BASED" = yes ]; then PMSG=$(git log -1 --format=%B "$LOCAL"); else PMSG="${MSG:-$(git log -1 --format=%B HEAD)}"; fi
  fi
fi
[ -z "$LOCAL" ] || git branch -f backup/plato-before-fold "$LOCAL"
NEW=$(git commit-tree 'HEAD^{tree}' -p "$PARENT" -m "$PMSG")
git update-ref refs/heads/plato "$NEW" ${LOCAL:+"$LOCAL"}
[ "$(git rev-parse 'plato^{tree}')" = "$(git rev-parse 'HEAD^{tree}')" ] || { echo "plato's tree differs from $SRC" >&2; exit 1; }
echo "plato is $(git rev-list --count origin/plato..plato) commit(s) ahead of origin/plato with $SRC's tree: $(git rev-parse --short plato)"
