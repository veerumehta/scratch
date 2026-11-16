#!/usr/bin/env bash
# Read-only health check of the shared local Plato Postgres (:55432): the migration version against the
# newest migration in a tree, sessions left open, idle-in-transaction sessions and ungranted locks.
# Writes nothing: the session is read-only and only reads alembic_version and the pg_stat views.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   check_shared_postgres.sh [--tree <dir>] [--db <name>] [--port <n>] [--host <dir-or-host>] [--user <name>]
#
# Defaults: tree /Users/sangit/src/japes-v27, database japes_plato_db, port 55432, host /tmp (the socket
# directory the local server was started with), the current user. PSQL overrides the psql binary.
# Exit 0 when the version equals the tree's newest migration and nothing looks stuck; 1 otherwise; 2 on bad input.
set -euo pipefail

TREE=/Users/sangit/src/japes-v27
DB=japes_plato_db
PORT=55432
HOST=/tmp
PGUSER_ARG=""
PSQL_BIN="${PSQL:-psql}"
IDLE_IN_TX_SECONDS=60

while [ $# -gt 0 ]; do
  case "$1" in
    --tree) TREE="$2"; shift 2 ;;
    --db) DB="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --host) HOST="$2"; shift 2 ;;
    --user) PGUSER_ARG="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

VERSIONS="$TREE/plato/migrations/versions"
[ -d "$VERSIONS" ] || { echo "no migrations directory: $VERSIONS" >&2; exit 2; }
command -v "$PSQL_BIN" >/dev/null 2>&1 || { echo "psql not found (set PSQL=/path/to/psql)" >&2; exit 2; }

# The newest migration: the highest-numbered file, its revision id read from the file itself.
NEWEST_FILE=$(find "$VERSIONS" -maxdepth 1 -type f -name '[0-9]*_*.py' | sort | tail -1)
NEWEST_FILE=$(basename "${NEWEST_FILE:-}")
[ -n "$NEWEST_FILE" ] || { echo "no migration files in $VERSIONS" >&2; exit 2; }
EXPECTED=$(sed -n -E "s/^revision *(: *str)? *= *['\"]([^'\"]+)['\"].*/\2/p" "$VERSIONS/$NEWEST_FILE" | head -1)
[ -n "$EXPECTED" ] || EXPECTED="${NEWEST_FILE%.py}"

psql_args=(-h "$HOST" -p "$PORT" -d "$DB" -X -A -t -v ON_ERROR_STOP=1)
[ -n "$PGUSER_ARG" ] && psql_args+=(-U "$PGUSER_ARG")
run() { PGOPTIONS="-c default_transaction_read_only=on" "$PSQL_BIN" "${psql_args[@]}" -c "$1"; }

echo "database: $DB on $HOST:$PORT (read-only)"
echo "tree:     $TREE  newest migration: $NEWEST_FILE (revision $EXPECTED)"

status=0

echo
echo "== alembic_version"
CURRENT=$(run "select version_num from alembic_version" | tr '\n' ' ' | sed 's/ *$//')
echo "${CURRENT:-<no row>}"
if [ "$CURRENT" = "$EXPECTED" ]; then
  echo "ok: the database is at the tree's newest migration"
else
  echo "MISMATCH: expected $EXPECTED"
  status=1
fi

echo
echo "== sessions on $DB (pid | state | seconds in state | seconds in transaction | query)"
run "select pid, coalesce(state,'?'), extract(epoch from now()-state_change)::int,
            coalesce(extract(epoch from now()-xact_start)::int, 0), left(regexp_replace(query, '\s+', ' ', 'g'), 70)
     from pg_stat_activity where datname = '$DB' and pid <> pg_backend_pid() order by state_change" \
  | sed 's/|/ | /g'

STUCK=$(run "select count(*) from pg_stat_activity where datname = '$DB' and pid <> pg_backend_pid()
             and state like 'idle in transaction%' and now()-state_change > interval '$IDLE_IN_TX_SECONDS seconds'")
echo
echo "idle in transaction for more than ${IDLE_IN_TX_SECONDS}s: $STUCK"
[ "$STUCK" = "0" ] || status=1

echo
echo "== locks not granted"
WAITING=$(run "select count(*) from pg_locks l join pg_stat_activity a on a.pid = l.pid
               where not l.granted and a.datname = '$DB'")
echo "waiting lock requests: $WAITING"
if [ "$WAITING" != "0" ]; then
  status=1
  run "select a.pid, l.locktype, l.mode, left(regexp_replace(a.query, '\s+', ' ', 'g'), 70)
       from pg_locks l join pg_stat_activity a on a.pid = l.pid
       where not l.granted and a.datname = '$DB'" | sed 's/|/ | /g'
fi

echo
if [ "$status" -eq 0 ]; then echo "RESULT: ok"; else echo "RESULT: look at the lines above"; fi
exit "$status"
