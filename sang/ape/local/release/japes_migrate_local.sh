#!/usr/bin/env bash
# Pin the local Plato worktree to the v2.6.2 tip, upgrade the local database to that tip's head
# (0028 pack_alignment, 0029 assistant_conversation, 0030 pack_activation: all add tables), then
# restart local Plato. Alembic does not read JAPES_ENV_FILE itself, so the env file is loaded first.
set -euo pipefail
MAIN=/Users/sangit/src/japes
WT=/Users/sangit/src/japes-plato
TOOL=/Users/sangit/src/.scratch/sang/ape/local/plato_worktree.sh
REV=$(git -C "$MAIN" rev-parse --short v2.6.2)
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
