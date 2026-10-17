#!/usr/bin/env bash
# Push the KernelClient fix and the werkzeug/multidict lock bump to origin/plato: branch plato-kernel-fix
# (8d50b9e3), one commit on origin/plato (1b6972b6) holding v2.6.2's 09916495 and 6b81e709 squashed.
# A fast-forward; nothing already pushed is rewritten. Local plato (the unpushed v2.6.2 squash) is not
# touched. Unreviewed: the review runs once at the end. The Dependabot alerts close only when main's lock
# changes, so this reaches main with the next dev -> main release.
set -euo pipefail
cd /Users/sangit/src/japes

BASE=1b6972b6; NEW=8d50b9e3; BRANCH=plato-kernel-fix
FILES="jazzx_sdk/clients/kernel_client.py poetry.lock tests/test_kernel_client_imports.py "
git fetch -q origin
[[ "$(git rev-parse --short=8 refs/remotes/origin/plato)" == "$BASE" ]] \
  || { echo "refusing: origin/plato is not $BASE" >&2; exit 1; }
[[ "$(git rev-parse --short=8 "refs/heads/$BRANCH")" == "$NEW" ]] \
  || { echo "refusing: $BRANCH is not $NEW" >&2; exit 1; }
git merge-base --is-ancestor refs/remotes/origin/plato "refs/heads/$BRANCH" \
  || { echo "refusing: origin/plato is not an ancestor of $BRANCH" >&2; exit 1; }
[[ "$(git rev-list --count "refs/remotes/origin/plato..refs/heads/$BRANCH")" == "1" ]] \
  || { echo "refusing: $BRANCH is not exactly one commit past origin/plato" >&2; exit 1; }
[[ "$(git diff --name-only refs/remotes/origin/plato "refs/heads/$BRANCH" | tr '\n' ' ')" == "$FILES" ]] \
  || { echo "refusing: $BRANCH touches more than: $FILES" >&2; exit 1; }

echo "Open Dependabot alerts on main:"
gh api repos/JazzX-LLC/japes/dependabot/alerts -q '.[] | select(.state=="open") | "  #\(.number) \(.security_advisory.severity) \(.dependency.package.name)"' || true

git diff --shortstat refs/remotes/origin/plato "refs/heads/$BRANCH"
read -r -p "Push $BRANCH to origin/plato? [y/N] " ok
[[ "$ok" == "y" ]] || { echo "aborted"; exit 1; }
git push origin "refs/heads/$BRANCH:refs/heads/plato"
git fetch -q origin
echo "$BRANCH vs origin/plato (ahead/behind): $(git rev-list --left-right --count "refs/heads/$BRANCH...refs/remotes/origin/plato")"
echo "Local plato (the v2.6.2 squash) is based on the old origin/plato: its next squash must parent on the new one."
