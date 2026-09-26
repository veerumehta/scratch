#!/usr/bin/env bash
# Publish `plato` with the feedback work squashed onto it.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# `plato` is one squash commit on origin/plato whose tree is v2.5.5's. This checks nothing moved,
# shows open Dependabot alerts on main, asks, then pushes. Fast-forward only; no tag, so no GHCR build.
set -euo pipefail

REPO="/Users/sangit/src/japes"
EXPECT_LOCAL="055bda6d"      # PR #75 rounds 6 to 9, on top of the pushed squash
EXPECT_REMOTE="07919ee2ae1e3059e5f515138a0f49ba79c0d082"

cd "$REPO"
git fetch -q origin plato

remote="$(git rev-parse origin/plato)"
[ "$remote" = "$EXPECT_REMOTE" ] || { echo "refusing: origin/plato is $remote, expected $EXPECT_REMOTE" >&2; exit 1; }
local_head="$(git rev-parse --short=8 refs/heads/plato)"
[ "$local_head" = "$EXPECT_LOCAL" ] || { echo "refusing: plato is $local_head, expected $EXPECT_LOCAL" >&2; exit 1; }
git diff --quiet refs/heads/plato v2.5.5 -- || { echo "refusing: plato's tree differs from v2.5.5" >&2; exit 1; }
git merge-base --is-ancestor origin/plato refs/heads/plato || { echo "refusing: not a fast-forward" >&2; exit 1; }

echo "== pushing $(git rev-list --count origin/plato..refs/heads/plato) commit(s) onto origin/plato"
git --no-pager log --oneline origin/plato..refs/heads/plato

echo
echo "== open Dependabot alerts on main"
gh api repos/JazzX-LLC/japes/dependabot/alerts \
    -q '.[] | select(.state=="open") | "  #\(.number) \(.security_advisory.severity) \(.dependency.package.name) -> \(.security_vulnerability.first_patched_version.identifier // "no fix")"' \
    || echo "  (could not read alerts)"

echo
read -r -p "push plato to origin? [y/N] " answer
[ "$answer" = "y" ] || { echo "not pushed"; exit 0; }
ALLOW_PUSH=1 git push origin plato
