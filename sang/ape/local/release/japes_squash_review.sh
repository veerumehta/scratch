#!/bin/bash
# Squash v2.6.3 onto local plato without the editor, check it moved, then run the full-range review.
set -u
cd /Users/sangit/src/japes || exit 1
MSG="v2.6.3 (plato v0.2.4): fold a job stated twice and map its missing data to catalog fields, a blueprint narrowing chain on the solution page, the extraction page refreshes while a run goes, KernelClient runs without a token, KernelClient takes SDK types to start, invoke and stream an agent, mcp floor 1.30.0"
before=$(git rev-parse refs/heads/plato)
scripts/local/squash_to_plato.sh --src v2.6.3 --apply --no-edit --message "$MSG" || { echo "squash failed"; exit 1; }
after=$(git rev-parse refs/heads/plato)
if [ "$before" = "$after" ]; then echo "local plato did not move: stopping before the review"; exit 1; fi
echo "local plato moved: $(git rev-parse --short "$before") -> $(git rev-parse --short "$after")"
FULL=1 /Users/sangit/src/japes/scripts/local/release/japes_review_plato_263.sh
