#!/usr/bin/env bash
# Push the PR #75 review fixes to `dev`, which updates the PR.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# `dev` is one cherry-picked commit ahead of origin/dev: the reasoning agent is checked before a
# rule's reads (procedure and natural-language evaluators), and a pack draft is stamped only when a
# file is really deleted. Verified in a worktree at dev: the policy, condition and pack suites pass.
# Checks nothing moved, shows open Dependabot alerts on main, asks, then pushes. Fast-forward only.
set -euo pipefail

REPO="/Users/sangit/src/japes"
EXPECT_LOCAL="b11194c0"
EXPECT_REMOTE="578744f3c2811596f069b8320628246c5aae7a47"

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
