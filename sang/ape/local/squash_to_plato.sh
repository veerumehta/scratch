#!/usr/bin/env bash
# Squash a source branch onto local plato as ONE commit (parents: origin/plato and origin/dev).
#
#   scripts/local/squash_to_plato.sh [--src BRANCH] [--message TEXT] [--no-fetch] [--no-edit] [--apply]
#
# Dry run by default: prints what would change and every precondition's result, touches nothing.
# --apply opens your editor on the commit message (an empty message aborts), then moves the local
# `plato` branch to the new commit. It never pushes (push_plato.sh does,
# after the review) and never writes to GitHub; the fetch is a read, skipped by --no-fetch.
#
#   --src      the branch to squash (default: the checked-out branch, or the highest local vX.Y.Z
#              branch when plato, dev or main is checked out)
#   --message  the commit's headline (default: the subject of origin/plato's tip, i.e. the same release)
#   --no-edit  with --apply, take the message as given without opening the editor
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SRC="" MSG="" FETCH=1 APPLY=0 EDIT=1
while [ $# -gt 0 ]; do
  case "$1" in
    --src) SRC="${2:?--src needs a branch}"; shift 2 ;;
    --message) MSG="${2:?--message needs text}"; shift 2 ;;
    --no-fetch) FETCH=0; shift ;;
    --no-edit) EDIT=0; shift ;;
    --apply) APPLY=1; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
done

HERE=$(git symbolic-ref --short HEAD 2>/dev/null || true)
if [ -z "$SRC" ]; then
  case "$HERE" in
    plato|dev|main|"")
      SRC=$(git for-each-ref --format='%(refname:short)' 'refs/heads/v[0-9]*' | sort -V | tail -n 1)
      [ -n "$SRC" ] || { echo "no source: pass --src BRANCH" >&2; exit 2; } ;;
    *) SRC="$HERE" ;;
  esac
fi
fail=0
ok()   { printf '  ok    %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=1; }

[ "$FETCH" = 1 ] && git fetch --quiet origin
for ref in "refs/heads/$SRC" refs/remotes/origin/plato refs/remotes/origin/dev; do
  git rev-parse --verify --quiet "$ref" >/dev/null || { echo "no such ref: $ref" >&2; exit 1; }
done
SRC_SHA=$(git rev-parse "refs/heads/$SRC")
PLATO=$(git rev-parse refs/remotes/origin/plato)
DEV=$(git rev-parse refs/remotes/origin/dev)
LOCAL_PLATO=$(git rev-parse --verify --quiet refs/heads/plato || true)
MSG="${MSG:-$(git log -1 --format=%s "$PLATO")}"

echo "source        $SRC $(git rev-parse --short "$SRC_SHA")  $(git log -1 --format=%s "$SRC_SHA")"
echo "origin/plato  $(git rev-parse --short "$PLATO")  $(git log -1 --format=%s "$PLATO")"
echo "origin/dev    $(git rev-parse --short "$DEV")  $(git log -1 --format=%s "$DEV")"
if [ -n "$LOCAL_PLATO" ]; then
  echo "local plato   $(git rev-parse --short "$LOCAL_PLATO")  $(git log -1 --format=%s "$LOCAL_PLATO")"
else
  echo "local plato   (none)"
fi
echo
echo "preconditions:"

case "$SRC" in plato|dev|main) bad "source is $SRC; squash a version branch" ;; *) ok "source is a working branch" ;; esac
[ -z "$(git status --porcelain --untracked-files=no)" ] && ok "tracked files are clean" || bad "tracked files are dirty"
if [ "$HERE" = plato ]; then
  echo "  note  plato is checked out: --apply switches to $SRC, moves plato, and switches back"
else
  ok "plato is not checked out"
fi

MERGED=$(git merge-tree --write-tree "$SRC_SHA" "$DEV" 2>/dev/null | head -1 || true)
if [ -n "$MERGED" ] && [ "$MERGED" = "$(git rev-parse "$SRC_SHA^{tree}")" ]; then
  ok "$SRC already carries everything origin/dev has"
else
  bad "origin/dev has changes $SRC lacks (merge or cherry-pick them into $SRC first)"
fi

if [ -n "$LOCAL_PLATO" ] && [ "$LOCAL_PLATO" != "$PLATO" ]; then
  if git merge-base --is-ancestor "$PLATO" "$LOCAL_PLATO"; then
    echo "  note  local plato is $(git rev-list --count "$PLATO..$LOCAL_PLATO") commit(s) ahead of origin/plato; --apply replaces them"
    git log --format='          %h %s' "$PLATO..$LOCAL_PLATO"
  else
    bad "origin/plato is not an ancestor of local plato (it diverged); inspect before replacing"
  fi
fi

if [ "$(git rev-parse "$SRC_SHA^{tree}")" = "$(git rev-parse "$PLATO^{tree}")" ]; then
  bad "origin/plato already has $SRC's tree; nothing to squash"
fi

echo
echo "would create one commit with $SRC's tree, parents origin/plato and origin/dev:"
echo "  message: $MSG"
echo "  change vs origin/plato: $(git diff --shortstat "$PLATO" "$SRC_SHA")"
echo "  commits on $SRC not in origin/dev: $(git rev-list --count "$DEV..$SRC_SHA") (some already squashed onto origin/plato)"
git diff --stat=100 "$PLATO" "$SRC_SHA" | tail -n 12
echo
echo "checks before you push: the review (REVIEW_UPSTREAM=origin/dev scripts/local/adversarial_review.sh)," \
     "open Dependabot alerts on main (push_plato.sh lists them)."

if [ "$fail" != 0 ]; then echo; echo "NOT applying: a precondition failed."; exit 1; fi
if [ "$APPLY" != 1 ]; then echo; echo "dry run. Add --apply to move local plato."; exit 0; fi

if [ "$EDIT" = 1 ]; then
  FILE=$(mktemp "${TMPDIR:-/tmp}/squash_to_plato.XXXXXX")
  trap 'rm -f "$FILE"' EXIT
  {
    printf '%s\n' "$MSG"
    printf '\n# Squash of %s onto plato (parents: origin/plato, origin/dev).\n' "$SRC"
    printf '# Lines starting with # are dropped; an empty message aborts.\n#\n'
    printf '# %s\n#\n' "$(git diff --shortstat "$PLATO" "$SRC_SHA")"
    git log --format='# %h %s' "$DEV..$SRC_SHA" | head -n 40
  } > "$FILE"
  eval "$(git var GIT_EDITOR)" "$FILE"
  MSG=$(grep -v '^#' "$FILE" || true)
  [ -n "$(printf '%s' "$MSG" | tr -d '[:space:]')" ] || { echo "empty message: aborted, nothing changed." >&2; exit 1; }
fi

NEW=$(git commit-tree "$SRC_SHA^{tree}" -p "$PLATO" -p "$DEV" -m "$MSG")
if [ "$HERE" = plato ]; then
  git checkout --quiet "$SRC"
  git branch -f plato "$NEW"
  git checkout --quiet plato
else
  git branch -f plato "$NEW"
fi
echo
echo "local plato is now $(git rev-parse --short "$NEW") (was ${LOCAL_PLATO:+$(git rev-parse --short "$LOCAL_PLATO")})."
echo "Not pushed. Review, then scripts/local/push_plato.sh."
