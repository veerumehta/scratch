#!/usr/bin/env bash
# Review each pushed ref's own range: a throwaway worktree at the pushed sha when it is not HEAD.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   PUSH_REFS="<local_ref> <local_sha> <remote_ref> <remote_sha>" review_pushed.sh [repo-name]
#
# PUSH_REFS is what git feeds a pre-push hook on stdin. With none (a run by hand) the review runs on HEAD.
# REVIEW_SCRIPT overrides the reviewer, for tests.
set -uo pipefail
ZERO=0000000000000000000000000000000000000000
root=$(git rev-parse --show-toplevel)
repo="${1:-$(basename "$root")}"
reviewer="${REVIEW_SCRIPT:-$root/scripts/local/adversarial_review.sh}"

if [[ -z "${PUSH_REFS:-}" ]]; then
    "$reviewer" "$repo"
    exit $?
fi

base_for_new_ref() {
    local sha=$1 b
    for b in origin/plato origin/dev origin/main; do
        git rev-parse --verify --quiet "$b" >/dev/null && { git merge-base "$sha" "$b"; return; }
    done
}

fail=0
while read -r _ lsha _ rsha; do
    [[ -z "${lsha:-}" || "$lsha" == "$ZERO" ]] && continue
    base=$rsha
    [[ "$rsha" == "$ZERO" ]] && base=$(base_for_new_ref "$lsha")
    if [[ "$lsha" == "$(git rev-parse HEAD)" ]]; then
        REVIEW_UPSTREAM=$base "$reviewer" "$repo" || fail=1
        continue
    fi
    wt=$(mktemp -d "${TMPDIR:-/tmp}/review-pushed.XXXXXX")
    if git worktree add -q --detach "$wt" "$lsha"; then
        ln -s "$root/scripts/local" "$wt/scripts/local"
        (cd "$wt" && REVIEW_UPSTREAM=$base "${REVIEW_SCRIPT:-$wt/scripts/local/adversarial_review.sh}" "$repo") || fail=1
        git worktree remove --force "$wt"
    else
        echo "  !  could not check out $lsha for review"
        fail=1
    fi
done <<< "$PUSH_REFS"
exit $fail
