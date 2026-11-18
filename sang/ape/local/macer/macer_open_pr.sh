#!/usr/bin/env bash
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
# Push the macer japes-2.7.4 branch and open a pull request against main. Run by hand; each step asks first.
# Run `git switch japes-2.7.4` in /Users/sangit/src/macer first (the branch is already there, not checked out).
set -euo pipefail
cd /Users/sangit/src/macer

BRANCH=japes-2.7.4
TITLE="move macer to japes 2.7.4"
BODY=/Users/sangit/src/japes/docs/status/macer/note_macer_japes_274_pr_body.md

[ "$(git branch --show-current)" = "$BRANCH" ] || { echo "refusing: not on $BRANCH (run: git switch $BRANCH)" >&2; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "refusing: uncommitted changes to tracked files" >&2; exit 1; }
[ -f "$BODY" ] || { echo "refusing: $BODY is missing" >&2; exit 1; }
git remote get-url origin | grep -q "JazzX-LLC/macer" || { echo "refusing: origin is not JazzX-LLC/macer" >&2; exit 1; }
grep -q '"japes @ git+https://github.com/JazzX-LLC/japes.git@c60775fb1bd2aa94e8b921164b6d70285987f2af"' pyproject.toml \
  || { echo "refusing: the japes pin is not the 2.7.4 main squash c60775fb" >&2; exit 1; }

echo "branch $BRANCH, commits over origin/main:"
git log --format='  %h %s' origin/main..HEAD
echo
read -r -p "Push $BRANCH to origin? [y/N] " ok
[ "$ok" = "y" ] || { echo "not pushed."; exit 0; }
git push -u origin "$BRANCH"

read -r -p "Open the PR $BRANCH -> main? [y/N] " ok
[ "$ok" = "y" ] || { echo "no PR opened."; exit 0; }
gh pr create --repo JazzX-LLC/macer --base main --head "$BRANCH" --title "$TITLE" --body-file "$BODY"
