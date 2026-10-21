#!/usr/bin/env bash
# Record main's v2.6.3 squash on dev with a real merge (tree unchanged), so the next dev -> main PR
# does not conflict. Plumbing only: no checkout, the shared working tree stays on its branch.
# Local dev may be behind origin/dev; it is moved to the merge, which contains origin/dev.
# Rerunnable if the push was interrupted. The push skips the suite; its review still runs.
set -euo pipefail
cd /Users/sangit/src/japes

git fetch origin --quiet
dev=$(git rev-parse origin/dev)
main=$(git rev-parse origin/main)

git worktree list --porcelain | grep -q "branch refs/heads/dev$" && { echo "dev is checked out in a worktree"; exit 1; }
git merge-base --is-ancestor "$main" "$dev" && { echo "main is already in origin/dev"; exit 0; }

push_dev() {
    read -r -p "Push dev to origin, skipping the suite? [y/N] " answer
    [ "$answer" = "y" ] && JAPES_SKIP_SUITE=1 git push origin dev || echo "not pushed; local dev holds the merge"
}

local_dev=$(git rev-parse dev)
# Resume: an earlier run made the merge locally and its push did not finish.
if [ "$(git rev-parse "$local_dev^2" 2>/dev/null || true)" = "$main" ] \
    && [ "$(git rev-parse "$local_dev^1")" = "$dev" ]; then
    echo "local dev $(git rev-parse --short dev) is the merge, not yet pushed"
    push_dev
    exit 0
fi
git merge-base --is-ancestor "$local_dev" "$dev" || {
    echo "local dev has commits origin/dev lacks; reconcile first"; git log --oneline "$dev..$local_dev"; exit 1; }

tree=$(git merge-tree --write-tree "$dev" "$main")
[ "$tree" = "$(git rev-parse "$main^{tree}")" ] && [ "$tree" = "$(git rev-parse "$dev^{tree}")" ] || {
    echo "dev and main trees differ, or the merge is not tree-neutral:"
    git diff --stat "$dev" "$main" | tail -5
    exit 1
}

commit=$(git commit-tree "$tree" -p "$dev" -p "$main" \
    -m "Merge main into dev: record the v2.6.3 squash")
git update-ref refs/heads/dev "$commit" "$local_dev"
echo "local dev is now $(git rev-parse --short dev) (was $(git rev-parse --short "$local_dev"))"
git rev-list --left-right --count origin/main...dev
push_dev
