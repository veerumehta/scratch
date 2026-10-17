#!/usr/bin/env bash
# Review the v2.6.3 squash commit on local plato against origin/plato: the delta only (about 19 files).
# Run after `scripts/local/squash_to_plato.sh --src v2.6.3 --apply`. Uses the review worktree so the
# shared checkout stays on v2.6.3. FULL pass, because the incremental pass passed defects the
# pre-push hook later found. Read-only for the review itself; it writes only its transcripts.
set -euo pipefail

WT=/private/tmp/japes-plato-review
MAIN=/Users/sangit/src/japes

[ "$(git -C "$MAIN" rev-parse --short plato)" != "$(git -C "$MAIN" rev-parse --short origin/plato)" ] \
    || { echo "local plato is origin/plato: run the squash first"; exit 1; }
git -C "$WT" checkout -q --detach "$(git -C "$MAIN" rev-parse plato)"
cd "$WT"
echo "reviewing $(git rev-parse --short HEAD) against origin/plato:"
git diff --shortstat origin/plato HEAD
REVIEW_UPSTREAM=origin/plato REVIEW_FULL=1 "$MAIN/scripts/local/adversarial_review.sh"
