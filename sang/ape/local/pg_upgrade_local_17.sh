#!/usr/bin/env bash
# Move the local dev Postgres (port 55432) from 16 to 17 by dump and restore.
# The 16 data directory is left untouched for rollback.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# Run only with local Plato stopped and no regen or ingest in flight:
#   scripts/local/plato_worktree.sh stop
#   scripts/local/pg_upgrade_local_17.sh
#   scripts/local/plato_worktree.sh start
# Rollback: stop 17, start 16 with the same pg_ctl line on PG16_DIR.
set -euo pipefail

PORT=55432
BASE="$HOME/.local/share/japes-pg"
PG16_DIR="$BASE/16"
PG17_DIR="$BASE/17"
DUMP="$BASE/dump_16_$(date +%Y%m%d_%H%M%S).sql"
SOCKET_DIR=/tmp
BREW=/opt/homebrew/opt
BIN16="$BREW/postgresql@16/bin"
BIN17="$BREW/postgresql@17/bin"
PG_USER="$(id -un)"

PORT_WAIT_SECONDS=15
for _ in $(seq "$PORT_WAIT_SECONDS"); do
  lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 || break
  sleep 1
done
if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Something still listens on :8000 (local Plato). Stop it first." >&2
  exit 1
fi

# Install it as the user that owns Homebrew: brew install postgresql@17
[ -x "$BIN17/postgres" ] || { echo "postgresql@17 is not installed or not executable by $PG_USER." >&2; exit 1; }
[ ! -e "$PG17_DIR" ] || { echo "$PG17_DIR exists; move it aside first." >&2; exit 1; }

echo "== dump from 16 =="
"$BIN16/pg_isready" -h "$SOCKET_DIR" -p "$PORT" >/dev/null \
  || "$BIN16/pg_ctl" -D "$PG16_DIR" -o "-p $PORT -k $SOCKET_DIR" -l "$BASE/16.log" -w start
"$BIN17/pg_dumpall" -h "$SOCKET_DIR" -p "$PORT" -U "$PG_USER" -f "$DUMP"
ls -lh "$DUMP"
"$BIN16/pg_ctl" -D "$PG16_DIR" -m fast -w stop

echo "== init and restore on 17 =="
"$BIN17/initdb" -D "$PG17_DIR" -U "$PG_USER" --auth-local=trust --auth-host=trust -E UTF8
"$BIN17/pg_ctl" -D "$PG17_DIR" -o "-p $PORT -k $SOCKET_DIR" -l "$BASE/17.log" -w start
"$BIN17/psql" -h "$SOCKET_DIR" -p "$PORT" -U "$PG_USER" -d postgres -v ON_ERROR_STOP=0 -q -f "$DUMP" >"$BASE/restore_17.log" 2>&1 || true

echo "== verify =="
"$BIN17/psql" -h "$SOCKET_DIR" -p "$PORT" -U "$PG_USER" -d postgres -Atc "select version()"
"$BIN17/psql" -h "$SOCKET_DIR" -p "$PORT" -U "$PG_USER" -d postgres -Atc \
  "select datname from pg_database where not datistemplate order by 1"
echo "Restore messages that are not 'already exists': "
grep -i -E "error|fatal" "$BASE/restore_17.log" | grep -v -i "already exists" || echo "none"
echo "Dump kept at $DUMP; 16 data kept at $PG16_DIR."
