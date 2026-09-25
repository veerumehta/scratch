#!/usr/bin/env bash
# Print a pull request's inline review comments.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   ./scripts/local/pr_review_comments.sh 72
#
# Read-only. `gh pr view --comments` shows only the conversation tab, which on a bot-reviewed PR
# is the security check and nothing else; the review findings are inline comments on the diff.
set -euo pipefail

pr="${1:?usage: pr_review_comments.sh <pr-number>}"
repo="${PR_REPO:-JazzX-LLC/japes}"

gh api "repos/${repo}/pulls/${pr}/comments?per_page=100" --paginate \
  --jq '.[] | "=== \(.path):\(.line // .original_line)  [\(.user.login)]  \(.created_at[0:10])\n\(.body)\n"'
