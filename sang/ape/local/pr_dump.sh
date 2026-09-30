#!/usr/bin/env bash
# Dump a PR's metadata and every review comment's full body to /tmp, read-only.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# `pr_new_comments.sh` prints the first line of each bot comment; this writes the whole body, plus
# the PR's head/base and the open PRs, so a triage can read what the reviewer actually said.
#
#   scripts/local/pr_dump.sh 82          # -> /tmp/pr82_dump.md
#   scripts/local/pr_dump.sh             # open PRs only -> /tmp/pr_open.md
#
# `REPO` overrides the repository (default: the one `gh` resolves for this checkout).
set -euo pipefail

repo="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"

gh pr list --repo "$repo" --state open \
    --json number,title,author,headRefName,baseRefName,updatedAt \
    -q '.[] | "#\(.number)  \(.headRefName) -> \(.baseRefName)  \(.author.login)  \(.updatedAt)  \(.title)"' \
    > /tmp/pr_open.md
echo "open PRs -> /tmp/pr_open.md"

pr="${1:-}"
[ -z "$pr" ] && exit 0
out="/tmp/pr${pr}_dump.md"
{
    gh pr view "$pr" --repo "$repo" \
        --json number,title,author,headRefName,baseRefName,headRefOid,state,mergeable \
        -q '"# #\(.number) \(.title)\n\(.headRefName) (\(.headRefOid[0:8])) -> \(.baseRefName)  \(.state)  mergeable=\(.mergeable)  by \(.author.login)\n"'
    echo "## Review comments"
    gh api "repos/$repo/pulls/$pr/comments" --paginate | jq -r -s 'add // [] | .[] |
        "\n### \(.id)  \(.user.login)  \(.path):\(.line // .original_line)  \(.created_at)  reply_to=\(.in_reply_to_id // "-")\n\(.body)"'
    echo
    echo "## Reviews"
    gh api "repos/$repo/pulls/$pr/reviews" --paginate | jq -r -s 'add // [] | .[] |
        select((.body // "") != "") | "\n### \(.user.login)  \(.state)  \(.submitted_at)\n\(.body)"'
    echo
    echo "## Conversation"
    gh api "repos/$repo/issues/$pr/comments" --paginate | jq -r -s 'add // [] | .[] |
        "\n### \(.user.login)  \(.created_at)\n\(.body)"'
} > "$out"
echo "PR #$pr -> $out"
