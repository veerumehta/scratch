#!/bin/bash
# Squashes v2.6.3 onto local plato as one commit (parents origin/plato and origin/dev), with the
# headline below. Dry run by default: prints every precondition and changes nothing.
#   /Users/sangit/src/japes/scripts/local/release/japes_squash_263.sh            dry run
#   APPLY=1 /Users/sangit/src/japes/scripts/local/release/japes_squash_263.sh    applies (moves local plato; never pushes)
# Plato must not be checked out (the checkout is on v2.6.3). The review and push come after:
#   REVIEW_UPSTREAM=origin/plato (review from plato), then scripts/local/push_plato.sh.
MESSAGE="v2.6.3 (plato v0.2.4): typed condition outcomes, adjudication segments with per-rule evidence, email drafts, case runs from the runs page, page questions for the assistant, client methods for the solution workbook and drafts"
FLAGS=""
[ "${APPLY:-}" = "1" ] && FLAGS="--apply --no-edit"
exec /Users/sangit/src/japes/scripts/local/squash_to_plato.sh --src v2.6.3 --message "$MESSAGE" $FLAGS
