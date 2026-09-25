#!/usr/bin/env bash
# A local Postgres that Plato sees as dev-daily sees Azure's.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# dev-daily runs PLATO_DB_BACKEND=common against a Postgres named japes_plato_db, with the DSN in
# DB_ASYNC_CONNECTION_STR. `common` is the same backend on a laptop, so pointing that DSN at
# localhost exercises the store and the migration chain exactly as deployed.
# PLATO_DB_BACKEND=sqlite does not: migration 0001 branches on the backend and creates no schemas.
#
#   ./scripts/local/pg_dev_daily.sh            # init, start, create, migrate, verify
#   ./scripts/local/pg_dev_daily.sh --stop     # stop the server
#   ./scripts/local/pg_dev_daily.sh --drop     # drop the database, keep the cluster
#
# Its own cluster under $HOME, on its own port: /opt/homebrew/var/postgresql@* are mode 0700 under
# another account, and postmaster.pid lives in PGDATA and is not relocatable. The binaries are
# world-executable, so only the data directory has to move.
#
# Writes the environment to .env.local (gitignored at .gitignore:52), which nothing loads:
# Plato reads the process environment. `set -a; . .env.local; set +a` puts it there.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

PG_VERSION="${PG_VERSION:-16}"
PG_PREFIX="/opt/homebrew/opt/postgresql@${PG_VERSION}"
PG_DATA="${PLATO_PG_DATA:-${HOME}/.local/share/japes-pg/${PG_VERSION}}"
PG_LOG="${PG_DATA}.log"
# Not 5432: the other account's cluster claims that port when it runs.
PORT="${PGPORT:-55432}"
SOCKET_DIR="${PLATO_PG_SOCKET:-/tmp}"

DB_NAME="japes_plato_db"
DB_USER="${PLATO_PG_USER:-plato}"
DB_PASS="${PLATO_PG_PASSWORD:-plato}"
ENV_FILE=".env.local"

export PATH="${PG_PREFIX}/bin:${PATH}"
command -v initdb >/dev/null || { echo "no postgresql@${PG_VERSION} at ${PG_PREFIX}"; exit 1; }

psql_() { psql -h "${SOCKET_DIR}" -p "${PORT}" "$@"; }

start() {
  pg_isready -h "${SOCKET_DIR}" -p "${PORT}" -q && return 0
  pg_ctl -D "${PG_DATA}" -l "${PG_LOG}" -o "-p ${PORT} -k ${SOCKET_DIR}" start
  # `pg_ctl start` returns before the server accepts connections.
  for _ in $(seq 1 20); do pg_isready -h "${SOCKET_DIR}" -p "${PORT}" -q && return 0; sleep 0.5; done
  echo "server did not accept connections; see ${PG_LOG}"; exit 1
}

case "${1:-}" in
  --stop) pg_ctl -D "${PG_DATA}" stop; exit 0 ;;
  --drop) start; dropdb -h "${SOCKET_DIR}" -p "${PORT}" --if-exists "${DB_NAME}"
          echo "dropped ${DB_NAME}"; exit 0 ;;
esac

if [ ! -f "${PG_DATA}/PG_VERSION" ]; then
  mkdir -p "$(dirname "${PG_DATA}")"
  initdb -D "${PG_DATA}" --encoding=UTF8 --locale=C
fi

start

# The role owns the database. A superuser would work and would not resemble the Azure role.
psql_ -d postgres -v ON_ERROR_STOP=1 -q <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS}';
  END IF;
END \$\$;
SQL
psql_ -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
  || createdb -h "${SOCKET_DIR}" -p "${PORT}" -O "${DB_USER}" "${DB_NAME}"

# localhost, not the socket: this is the DSN Plato uses, and it must be the TCP form dev-daily has.
DSN="postgresql+asyncpg://${DB_USER}:${DB_PASS}@localhost:${PORT}/${DB_NAME}"
cat > "${ENV_FILE}" <<ENV
# Written by scripts/local/pg_dev_daily.sh. Nothing loads this; export it:
#   set -a; . ${ENV_FILE}; set +a
DB_ASYNC_CONNECTION_STR=${DSN}
PLATO_DB_BACKEND=common
ENV

export DB_ASYNC_CONNECTION_STR="${DSN}" PLATO_DB_BACKEND=common
python -m alembic -c plato/alembic.ini upgrade head

echo
psql_ -d "${DB_NAME}" -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY 1"
psql_ -d "${DB_NAME}" -c "SELECT version_num FROM alembic_version"
echo "cluster ${PG_DATA} on port ${PORT}; environment in ${ENV_FILE}"
