#!/usr/bin/env bash
# Push the ninth round of PR #75 review fixes to `dev`, which updates the PR.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# `dev` is one commit ahead of origin/dev: the round from a full adversarial review of the PR range
# (origin/main..dev) plus the bot's latest five comments. The full-range review is clean.
# Checks nothing moved, shows open Dependabot alerts on main, asks, then pushes. Fast-forward only.
set -euo pipefail

REPO="/Users/sangit/src/japes"
EXPECT_LOCAL="f7510cb3"
EXPECT_REMOTE="c87b29bc29a6d4d6b667fcda636ce64ca42f2642"

cd "$REPO"
git fetch -q origin dev

remote="$(git rev-parse origin/dev)"
[ "$remote" = "$EXPECT_REMOTE" ] || { echo "refusing: origin/dev is $remote, expected $EXPECT_REMOTE" >&2; exit 1; }
local_head="$(git rev-parse --short=8 refs/heads/dev)"
[ "$local_head" = "$EXPECT_LOCAL" ] || { echo "refusing: dev is $local_head, expected $EXPECT_LOCAL" >&2; exit 1; }
git merge-base --is-ancestor origin/dev refs/heads/dev || { echo "refusing: not a fast-forward" >&2; exit 1; }

echo "== pushing onto origin/dev (PR #75)"
git --no-pager log --oneline origin/dev..refs/heads/dev

echo
echo "== open Dependabot alerts on main"
gh api repos/JazzX-LLC/japes/dependabot/alerts \
    -q '.[] | select(.state=="open") | "  #\(.number) \(.security_advisory.severity) \(.dependency.package.name) -> \(.security_vulnerability.first_patched_version.identifier // "no fix")"' \
    || echo "  (could not read alerts)"

echo
read -r -p "push dev to origin? [y/N] " answer
[ "$answer" = "y" ] || { echo "not pushed"; exit 0; }
ALLOW_PUSH=1 git push origin dev
