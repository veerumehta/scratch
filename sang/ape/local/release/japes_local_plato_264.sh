#!/usr/bin/env bash
# Move local Plato (:8000) to the v2.6.4 tip: stop the instance started from the main checkout,
# pin the Plato worktree to v2.6.4, migrate the local database to alembic head (0035), restart from
# the worktree. The migrations 0033 to 0035 only create tables and indexes.
# Do not run it during an extraction or a regen.
set -euo pipefail
MAIN=/Users/sangit/src/japes
cd "$MAIN"

if lsof -nP -iTCP:8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "stopping what listens on :8000"
    PLATO_PROFILE=packs scripts/plato-local.sh stop || true
fi
scripts/local/local_plato_upgrade.sh v2.6.4
echo
curl -s localhost:8000/health || true
echo
