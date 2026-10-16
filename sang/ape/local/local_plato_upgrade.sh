#!/usr/bin/env bash
# Pin the local Plato worktree to a revision, upgrade the local database to that revision's
# alembic head, and restart local Plato. Alembic does not read JAPES_ENV_FILE itself, so the env
# file is loaded first.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   local_plato_upgrade.sh [<rev>]    <rev> defaults to the tip of the working branch (v2.6.3)
set -euo pipefail
MAIN=/Users/sangit/src/japes
WT=/Users/sangit/src/japes-plato
TOOL="$(cd "$(dirname "$0")" && pwd)/plato_worktree.sh"
REV=$(git -C "$MAIN" rev-parse --short "${1:-v2.6.3}")
"$TOOL" pin "$REV"
export JAPES_ENV_FILE="$MAIN/.env" JAPES_ENVIRONMENT=local
cd "$WT"
"$MAIN/.venv/bin/python" - "$WT/plato/alembic.ini" <<'PY'
import sys
from jazzx_sdk.config.envvars import load_env_file
load_env_file()
from alembic.config import main
main(argv=["-c", sys.argv[1], "upgrade", "head"])
PY
"$TOOL" restart "$REV"
