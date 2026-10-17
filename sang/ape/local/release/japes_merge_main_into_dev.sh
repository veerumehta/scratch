#!/usr/bin/env bash
# Record main's v2.6.1 squash (and its CODEOWNERS change) on dev with a real merge, so the next
# dev -> main PR does not conflict. Builds the merge commit with plumbing: no checkout, so the
# shared working tree stays on its branch. Pushes only after you confirm.
set -euo pipefail
cd /Users/sangit/src/japes

git fetch origin --quiet
dev=$(git rev-parse origin/dev)
main=$(git rev-parse origin/main)

git worktree list --porcelain | grep -q "branch refs/heads/dev$" && { echo "dev is checked out in a worktree"; exit 1; }
git merge-base --is-ancestor "$main" "$dev" && { echo "main is already in origin/dev"; exit 0; }

push_dev() {
    # The pre-push hook runs the suite; JAPES_SKIP_SUITE=1 keeps its review and skips the suite.
    read -r -p "Push dev to origin, skipping the suite? [y/N] " answer
    [ "$answer" = "y" ] && JAPES_SKIP_SUITE=1 git push origin dev || echo "not pushed; local dev holds the merge"
}

# Resume: an earlier run made the merge locally and its push did not finish.
local_dev=$(git rev-parse dev)
if [ "$local_dev" != "$dev" ]; then
    [ "$(git rev-parse "$local_dev^1")" = "$dev" ] && [ "$(git rev-parse "$local_dev^2")" = "$main" ] \
        && [ "$(git rev-parse "$local_dev^{tree}")" = "$(git rev-parse "$main^{tree}")" ] \
        || { echo "local dev is neither origin/dev nor the merge of main into it; reconcile first"; exit 1; }
    echo "local dev $(git rev-parse --short dev) is the merge, not yet pushed"
    push_dev
    exit 0
fi

# The merge must be clean, and its tree must be exactly main's (dev plus main's own changes).
tree=$(git merge-tree --write-tree "$dev" "$main")
[ "$tree" = "$(git rev-parse "$main^{tree}")" ] || {
    echo "merged tree differs from main's tree; dev has work main lacks:"
    git diff --stat "$tree" "$main^{tree}" | tail -5
    exit 1
}

echo "main-only changes (the merge brings these to dev):"
git diff --stat "$dev" "$main" | tail -5

commit=$(git commit-tree "$tree" -p "$dev" -p "$main" \
    -m "Merge main into dev: record the v2.6.1 squash and the CODEOWNERS update")
git update-ref refs/heads/dev "$commit" "$dev"
echo "local dev is now $(git rev-parse --short dev) (was $(git rev-parse --short "$dev"))"
git rev-list --left-right --count origin/main...dev

push_dev
