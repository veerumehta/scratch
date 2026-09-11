#!/usr/bin/env bash
# Replace the message on dev's tip commit (the v2.5.1 squash) without touching its content.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# Why this exists: the squash landed with a headline pitched at the implementation ("a pack store")
# instead of the product ("pack studio"), and a 22-line body where a headline was wanted. The tree
# is correct; only the message is wrong.
#
# What it does, in order, stopping on the first surprise:
#   1. fetches and asserts dev's tip is still the expected commit, with nothing on top of it
#   2. rewrites only the message, then asserts the tree hash is byte-identical
#   3. pushes with --force-with-lease, which refuses if anyone moved dev in the meantime
#
# Run it from anywhere:  ./scripts/local/fix_dev_squash_message.sh
# Nothing is pushed until the last line, and it prints the old and new message first.
#
# Read before running: this rewrites one commit that is already on a shared branch. Anyone who
# fetched dev in the last few minutes will see a divergence and needs `git fetch && git reset
# --hard origin/dev` on their own dev checkout. Also, PR #68's page will keep pointing at the old
# SHA, which will no longer be in the branch; the PR stays MERGED either way.

set -euo pipefail

EXPECTED_TIP="e4eabd4d6910ff21619575dba3ca2afcc971f6ad"
EXPECTED_TREE="7cd31ec7501194624baeba1a533d7fa81c381f34"

# The new message. Headline only -- the detail is in the changelog, which is where it belongs.
NEW_SUBJECT="v2.5.1: pack studio, and the gates around it"
NEW_BODY="A published pack is served, versioned and gated on its activation status, with an
operator page of its own. Every job role now delivers its documented exit code.
Plato is documented in the README and ARCHITECTURE."

cd "$(git rev-parse --show-toplevel)"

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }

say "1/3  checking dev is where the fix expects it"
git fetch --quiet origin dev

tip="$(git rev-parse origin/dev)"
if [[ "$tip" != "$EXPECTED_TIP" ]]; then
    echo "  ! dev's tip is $tip, not $EXPECTED_TIP."
    echo "    Something landed on dev since this script was written. Stopping: rewriting now would"
    echo "    discard that. Nothing has been changed."
    exit 1
fi
echo "  dev tip is the expected squash commit, and nothing is stacked on it."

say "2/3  rewriting the message on a detached copy (content untouched)"
git log -1 --format='  old subject: %s' "$EXPECTED_TIP"

# Detached, so the current branch and working tree are not disturbed whatever happens next.
start_ref="$(git rev-parse --abbrev-ref HEAD)"
cleanup() { git checkout --quiet "$start_ref" 2>/dev/null || true; }
trap cleanup EXIT

git checkout --quiet --detach "$EXPECTED_TIP"
printf '%s\n\n%s\n' "$NEW_SUBJECT" "$NEW_BODY" | git commit --quiet --amend --file=-

rewritten="$(git rev-parse HEAD)"
if [[ "$(git rev-parse HEAD^{tree})" != "$EXPECTED_TREE" ]]; then
    echo "  ! the tree changed, which a message-only amend must never do. Stopping before any push."
    exit 1
fi
echo "  tree hash identical: $EXPECTED_TREE"
git log -1 --format='  new subject: %s' "$rewritten"
echo
git log -1 --format='%B' "$rewritten" | sed 's/^/    | /'

say "3/3  pushing dev with --force-with-lease"
echo "  This is the only step that reaches GitHub. Ctrl-C now to stop with nothing published."
echo "  --force-with-lease refuses the push if dev moved after the fetch above."
read -r -p "  push? [y/N] " reply
[[ "$reply" == "y" || "$reply" == "Y" ]] || { echo "  stopped; nothing pushed."; exit 0; }

git push --force-with-lease="dev:$EXPECTED_TIP" origin "HEAD:dev"

say "done"
echo "  dev is now $(git rev-parse --short "$rewritten") with the corrected message."
echo "  PR #68 stays MERGED but its page still names $(git rev-parse --short "$EXPECTED_TIP"),"
echo "  which is no longer in the branch. Nothing to do about that; it is cosmetic."
echo "  Anyone with a dev checkout: git fetch && git reset --hard origin/dev"
