#!/usr/bin/env bash
# Rebuild the main checkout's .venv from poetry.lock with the CI extras (the local Plato worktree starts from this venv).
# Refuses while the local Plato service is up: never rebuild mid-run.
set -euo pipefail
cd /Users/sangit/src/japes
EXTRAS="mcp templating finance pptx mlflow gemini formal plato azure"
if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "refusing: something listens on :8000 (local Plato). Stop it first: scripts/local/plato_worktree.sh stop" >&2
  exit 1
fi
rm -rf .venv
python3 -m venv .venv
VIRTUAL_ENV="$PWD/.venv" PATH="$PWD/.venv/bin:$PATH" poetry install --extras "$EXTRAS"
.venv/bin/python -c "import jazzx_sdk, plato; print('venv ok')"
