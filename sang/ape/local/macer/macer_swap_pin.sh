#!/usr/bin/env bash
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
# Swap the placeholder japes pin on the macer japes-2.7.4 branch for the 2.7.4 main squash sha, relock, smoke-test, commit.
# usage: scripts/local/macer_swap_pin.sh <full japes main sha> [macer checkout, default /Users/sangit/src/macer]
set -euo pipefail
SHA="${1:?usage: macer_swap_pin.sh <full japes sha> [macer checkout]}"
DIR="${2:-/Users/sangit/src/macer}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "refusing: give the full 40-character sha" >&2; exit 1; }
cd "$DIR"
[ "$(git branch --show-current)" = "japes-2.7.4" ] || { echo "refusing: not on japes-2.7.4 (run: git switch japes-2.7.4)" >&2; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "refusing: uncommitted changes to tracked files" >&2; exit 1; }
grep -q '"japes @ git+https://github.com/JazzX-LLC/japes.git@[0-9a-f]\{40\}"' pyproject.toml || { echo "refusing: no japes pin line found" >&2; exit 1; }

sed -i.bak "s|\"japes @ git+https://github.com/JazzX-LLC/japes.git@[0-9a-f]\{40\}\"|\"japes @ git+https://github.com/JazzX-LLC/japes.git@${SHA}\"|" pyproject.toml
rm -f pyproject.toml.bak
grep -n '"japes @' pyproject.toml
env -u VIRTUAL_ENV uv lock

# Smoke test in a throwaway copy, so the checkout gets no venv and no build output.
SMOKE="$(mktemp -d "${TMPDIR:-/tmp}/macer-swap.XXXXXX")"
trap 'rm -rf "$SMOKE"' EXIT
git archive HEAD | tar -x -C "$SMOKE"
cp pyproject.toml uv.lock "$SMOKE"/
( cd "$SMOKE" && env -u VIRTUAL_ENV uv sync --frozen --extra dev -q \
  && env -i HOME="$HOME" PATH="$PATH" JAPES_KNOWLEDGE_HUB_URL=http://hub PYTHONPATH=src:. .venv/bin/python -c "
import importlib.metadata as m
from jazzx_sdk import Handler, HandlerContext, JazzXRuntime, QueueSettings, ResponseMessage
import jazzx_eval_contracts, jazzx_plato_client, common.core.ai_gateway
print('japes', m.version('japes'), 'smoke ok')" )

git add pyproject.toml uv.lock
git commit -q -m "pin japes 2.7.4 (${SHA:0:8})"
echo
git log --oneline -1
echo "Review the diff, then push with:  git -C $DIR push origin japes-2.7.4"
echo "and take the PR out of draft:      gh pr ready --repo JazzX-LLC/macer japes-2.7.4"
