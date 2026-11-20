#!/usr/bin/env bash
# Delete the stray remote branch origin/devclear (its tip is contained in origin/dev).
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
set -euo pipefail
cd /Users/sangit/src/japes
git fetch origin
git merge-base --is-ancestor origin/devclear origin/dev
git push origin --delete devclear
git branch -dr origin/devclear 2>/dev/null || true
