#!/usr/bin/env bash
# Prepare the squash-merge commit message for a dev -> main PR, then merge it.
#
# Two steps, deliberately separate, because the body is yours to write:
#
#   ./pr_squash_body.sh              writes the body to a file and opens it in $EDITOR
#   ./pr_squash_body.sh --merge      squash-merges the PR with that body
#
# The generated body lists only the headlines that are *new to main*. main currently holds a
# content snapshot of dev's own lineage (a previous squash), so most of `git log main..dev` is
# already there and listing it would describe the release as far larger than it is. This finds the
# commit in dev's history whose tree equals main's and lists what came after it.
#
#   PR=70 ./pr_squash_body.sh
set -euo pipefail

REPO="${JAPES_REPO:-/Users/sangit/src/japes}"
SLUG="${SLUG:-JazzX-LLC/japes}"
PR="${PR:-70}"
BRANCH="${BRANCH:-dev}"
BASE="${BASE:-main}"
BODY="${BODY:-${TMPDIR:-/tmp}/pr${PR}_squash_body.md}"

cd "$REPO"
command -v gh >/dev/null || { echo "gh is not installed" >&2; exit 1; }

if [ "${1:-}" = "--merge" ]; then
    [ -f "$BODY" ] || { echo "no body at $BODY -- run $0 first" >&2; exit 1; }
    grep -q "WRITE YOUR SUMMARY HERE" "$BODY" && {
        echo "refusing: $BODY still has the placeholder in it" >&2; exit 1; }

    subject=$(head -1 "$BODY" | sed 's/^# *//')
    [ -n "$subject" ] || { echo "refusing: the first line of $BODY is empty; it becomes the commit subject" >&2; exit 1; }

    echo "subject: $subject"
    echo
    tail -n +2 "$BODY"
    echo
    printf 'squash-merge PR #%s into %s with the above? [y/N] ' "$PR" "$BASE"
    read -r answer
    [ "$answer" = "y" ] || { echo "nothing done"; exit 0; }

    # --body-file takes everything after the first line; the subject is passed separately so the
    # commit reads as one headline plus a body, which is the convention in this repo's history.
    tail -n +2 "$BODY" > "$BODY.tail"
    gh pr merge "$PR" --repo "$SLUG" --squash --subject "$subject" --body-file "$BODY.tail"
    cat <<EOF

Merged. Now repair the ancestry, or the next dev -> main merge conflicts the same way this one did:

  ./scripts/local/record_squash_on_main.sh            # checks
  ./scripts/local/record_squash_on_main.sh --apply    # record it
EOF
    exit 0
fi

git fetch origin "$BASE" "$BRANCH" --quiet

# The commit on this branch's OWN line whose tree is identical to the base's: the base is a squash
# of that point, so everything after it is what this release actually adds.
#
# --first-parent throughout, and both uses matter. Searching without it finds the base's own squash
# commit once an ancestry-repair merge has pulled it in (same tree, newer date), and the range then
# starts after a commit that is not on this branch's line -- which re-lists every individual commit
# the squash had replaced. Logging without it lists that squash commit itself, which is already on
# the base. With it, the walk stays on this branch and the range is exactly the new work.
base_tree=$(git rev-parse "origin/$BASE^{tree}")
snapshot=""
for c in $(git log --first-parent --format=%H "origin/$BRANCH"); do
    if [ "$(git rev-parse "$c^{tree}")" = "$base_tree" ]; then snapshot="$c"; break; fi
done

if [ -n "$snapshot" ]; then
    range="$snapshot..origin/$BRANCH"
    echo "main's tree matches $BRANCH at $(git log -1 --format='%h %s' "$snapshot")"
    echo "listing headlines from $range"
else
    range="origin/$BASE..origin/$BRANCH"
    echo "no tree match found; listing every headline in $range"
fi

# sed, not a python one-liner: the pattern needs both quote characters and shell quoting mangles it.
version_of() { sed -n 's/^__version__[[:space:]]*=[[:space:]]*["'"'"']\([^"'"'"']*\).*/\1/p' "$1" | head -1; }
sdk=$(version_of jazzx_sdk/_version.py)
plato=$(version_of plato/_version.py)
[ -n "$sdk" ] && [ -n "$plato" ] || { echo "could not read the versions" >&2; exit 1; }

{
    echo "# v$sdk: WRITE YOUR SUMMARY HERE"
    echo
    echo "<!-- The first line above becomes the commit subject. Replace the placeholder; keep it to"
    echo "     one headline. Anything below is the commit body. Delete these comments. -->"
    echo
    echo "SDK $sdk, Plato $plato."
    echo
    echo "## What this carries"
    echo
    git log --first-parent --no-merges --format='- %s' "$range"
    echo
    echo "<!-- Your notes: what a reader of main's history needs that the headlines above do not say."
    echo "     Details belong in docs/status/CHANGELOG.md; keep this to what matters at a release. -->"
    echo
    echo "## Ancestry"
    echo
    echo "A squash gives \`$BASE\` this content without linking it to the $(git rev-list --count --first-parent --no-merges "$range") commits it came"
    echo "from. That only needs repairing if \`$BRANCH\` lives on: run"
    echo "\`BRANCH=$BRANCH BASE=$BASE scripts/local/record_squash_on_main.sh --apply\` to record the link."
    echo "A branch that retires here needs nothing."
} > "$BODY"

echo
echo "body written to $BODY"
echo "----------------------------------------------------------------"
cat "$BODY"
echo "----------------------------------------------------------------"
cat <<EOF

Edit it (first line = commit subject), then:

  $0 --merge

EOF

if [ -n "${EDITOR:-}" ]; then
    printf 'open %s in %s now? [y/N] ' "$BODY" "$EDITOR"
    read -r answer
    [ "$answer" = "y" ] && "$EDITOR" "$BODY"
fi
