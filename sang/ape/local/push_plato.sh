#!/usr/bin/env bash
# Push local plato (the squash of the current version branch) and open the PR plato -> dev.
set -euo pipefail
cd /Users/sangit/src/japes
git fetch origin
git merge-base --is-ancestor refs/remotes/origin/plato refs/heads/plato \
  || { echo "refusing: origin/plato is not an ancestor of local plato" >&2; exit 1; }
git merge-base --is-ancestor refs/remotes/origin/dev refs/heads/plato \
  || { echo "refusing: origin/dev is not in plato's history" >&2; exit 1; }
echo "plato $(git rev-parse --short refs/heads/plato): $(git log -1 --format=%s refs/heads/plato)"
echo "Open Dependabot alerts on main:"
gh api repos/JazzX-LLC/japes/dependabot/alerts \
  -q '.[] | select(.state=="open") | "\(.number) \(.security_advisory.severity) \(.dependency.package.name)"' || true
read -r -p "Push plato? [y/N] " ok
[ "$ok" = "y" ] || { echo "not pushed."; exit 0; }
git push origin refs/heads/plato:refs/heads/plato
read -r -p "Open the PR plato -> dev? [y/N] " ok
[ "$ok" = "y" ] || exit 0
gh pr create --repo JazzX-LLC/japes --base dev --head plato \
  --title "SDK 2.6.1 and Plato 0.2.1" \
  --body "SDK 2.6.1, Plato 0.2.1 and jazzx-plato-client 0.2.1."
