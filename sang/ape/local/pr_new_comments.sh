#!/usr/bin/env bash
# List a PR's bot review comments newer than a cutoff, one line each: path:line time first-line.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# Read-only. Pages through every comment (`gh api` alone stops at 30). The cutoff defaults to your
# latest comment on the PR, so what prints is what the bot said since you last replied; pass an
# ISO time to choose another, or `all` for every bot comment.
#
#   scripts/local/pr_new_comments.sh 75
#   scripts/local/pr_new_comments.sh 75 2026-09-26T06:30:00Z
#   scripts/local/pr_new_comments.sh 75 all
#
# `REPO` overrides the repository (default: the one `gh` resolves for this checkout).
set -euo pipefail

pr="${1:?usage: pr_new_comments.sh <pr-number> [since|all]}"
repo="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
comments="$(gh api "repos/$repo/pulls/$pr/comments" --paginate | jq -s 'add // []')"

since="${2:-}"
if [ -z "$since" ]; then
    me="$(gh api user -q .login)"
    since="$(jq -r --arg me "$me" '[.[] | select(.user.login == $me) | .created_at] | max // ""' <<<"$comments")"
fi
[ "$since" = "all" ] && since=""

echo "== $repo#$pr: bot comments ${since:+after $since}"
jq -r --arg since "$since" '
  [.[] | select(.user.type == "Bot" and .created_at > $since)] | sort_by(.created_at) | .[]
  | "\(.path):\(.line // .original_line)  \(.created_at)  \(.body | split("\n")[0] | .[0:160])"
' <<<"$comments"
count="$(jq --arg since "$since" '[.[] | select(.user.type == "Bot" and .created_at > $since)] | length' <<<"$comments")"
echo "== $count comment(s)"
