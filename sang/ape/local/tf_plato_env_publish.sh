#!/usr/bin/env bash
# Publishes the two plato env-var branches: pushes the branch and opens the PR.
#
# THIS IS THE STEP THAT REACHES GITHUB. Run the prep scripts first -- they do the edits and the
# local commit, and this only pushes what they produced:
#
#   ./tf_plato_env_pr1_modules.sh      then   ./tf_plato_env_publish.sh 1
#   ./tf_plato_env_pr2_devenv.sh       then   ./tf_plato_env_publish.sh 2
#
# Takes an explicit argument so nothing is published by running it bare. `both` opens both PRs;
# that is fine -- it is the *merge* order that matters (modules first, since the environment repo
# pins the module at ?ref=main), and PR 2's body says so.
set -euo pipefail

usage() {
    cat <<'USAGE'
usage: tf_plato_env_publish.sh <1|2|both>

  1     terraform-azure-jaxi-modules -> main
  2     terraform-azure-jaxi         -> dev
  both  1 then 2

Run the matching prep script first; this publishes its branch and nothing else.
USAGE
    exit 64
}

[ $# -eq 1 ] || usage

MODULES_REPO="${TF_MODULES_REPO:-/Users/sangit/src/terraform-azure-jaxi-modules}"
ENV_REPO="${TF_ENV_REPO:-/Users/sangit/src/terraform-azure-jaxi}"
TMP="${TMPDIR:-/tmp}"

command -v gh >/dev/null || { echo "gh is not installed" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "gh is not authenticated; run: gh auth login" >&2; exit 1; }

publish() {
    local repo="$1" slug="$2" branch="$3" base="$4" body="$5" title="$6" prep="$7"

    echo "== $slug: $branch -> $base"

    [ -d "$repo" ] || { echo "not found: $repo" >&2; return 1; }
    git -C "$repo" rev-parse --verify "$branch" >/dev/null 2>&1 || {
        echo "branch $branch does not exist; run $prep first" >&2; return 1; }

    # The prep script is what writes the body, so a missing one means it was never run (or the
    # temp directory was cleared). Re-running it is safe: the edits are idempotent and the commit
    # is conditional.
    [ -f "$body" ] || { echo "PR body missing at $body; re-run $prep" >&2; return 1; }

    local ahead
    ahead=$(git -C "$repo" rev-list --count "origin/$base..$branch" 2>/dev/null || echo 0)
    [ "$ahead" -gt 0 ] || { echo "$branch has no commits ahead of origin/$base; nothing to open" >&2; return 1; }
    echo "   $ahead commit(s) ahead of origin/$base"

    git -C "$repo" push -u origin "$branch"

    local existing
    existing=$(gh pr list --repo "$slug" --head "$branch" --json url --jq '.[0].url' 2>/dev/null || true)
    if [ -n "$existing" ] && [ "$existing" != "null" ]; then
        echo "   PR already open, branch updated: $existing"
        return 0
    fi

    gh pr create --repo "$slug" --base "$base" --head "$branch" \
        --title "$title" --body-file "$body"
}

do_one() {
    publish "$MODULES_REPO" "JazzX-LLC/terraform-azure-jaxi-modules" \
        "feat/add-plato-pack-storage-and-tenants-env-vars" "main" \
        "$TMP/plato_pr1_body.md" \
        "feat: add PLATO_TENANTS, PLATO_PACK_BLOB_* and STORAGE__CONNECTION_STRING to the aca module" \
        "tf_plato_env_pr1_modules.sh"
}

do_two() {
    publish "$ENV_REPO" "JazzX-LLC/terraform-azure-jaxi" \
        "feat/add-plato-env-vars-dev-daily" "dev" \
        "$TMP/plato_pr2_body.md" \
        "feat: set plato env vars for dev-daily" \
        "tf_plato_env_pr2_devenv.sh"
}

case "$1" in
    1) do_one ;;
    2) do_two ;;
    both)
        do_one
        echo
        do_two
        echo
        echo "Merge the modules PR first: the environment repo pins the module at ?ref=main."
        ;;
    *) usage ;;
esac
