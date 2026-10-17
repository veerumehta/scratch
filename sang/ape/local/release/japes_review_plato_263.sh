#!/bin/bash
# Adversarial review of the v2.6.3 squash on local plato, against origin/plato. Run it after:
#   APPLY=1 /Users/sangit/src/japes/scripts/local/release/japes_squash_263.sh
# It reviews from a detached worktree, so the main checkout (on v2.6.3, shared with the sessions) is
# not switched and plato is not left checked out (the squash script needs it free).
# Transcripts and the review state live in a kept directory, so a second round narrows to what
# changed since the last one. FULL=1 forces the whole range again.
# Findings go to v2.6.3; then re-squash (a new commit replaces local plato) and review again.
set -u
MAIN=/Users/sangit/src/japes
WT=/tmp/japes-plato-review
KEEP=/Users/sangit/src/.scratch/sang/ape/local/.reviews_plato
cd "$MAIN" || exit 1
git worktree remove --force "$WT" 2>/dev/null
git worktree prune
git worktree add --detach "$WT" plato || exit 1
mkdir -p "$KEEP" "$WT/scripts/local" || exit 1
rm -rf "$WT/scripts/local/.reviews"
ln -s "$KEEP" "$WT/scripts/local/.reviews"
cd "$WT" || exit 1
if [ "${FULL:-}" = "1" ]; then export REVIEW_FULL=1; fi
REVIEW_UPSTREAM=origin/plato "$MAIN/scripts/local/adversarial_review.sh" japes-plato-263
STATUS=$?
echo "review exit $STATUS (1 = a defect was reported); transcripts are in $KEEP"
echo "remove the worktree when done: git -C $MAIN worktree remove --force $WT"
exit $STATUS
