#!/usr/bin/env bash
# Run the local Plato (:8000) from its own git worktree, pinned to a commit, so a branch switch in
# the main checkout cannot change the code a running server lazily imports.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   plato_worktree.sh pin [<rev>]   create or move the worktree to <rev> (default: main checkout's HEAD)
#   plato_worktree.sh start         start Plato from the worktree (refuses if :8000 is taken)
#   plato_worktree.sh stop          stop whatever Plato listens on :8000
#   plato_worktree.sh restart [<rev>]  stop, pin, start
#   plato_worktree.sh status        the worktree's commit and the server's health
#
# State that must survive a re-pin lives in the main checkout and is named absolutely: the env file,
# pack blobs and cache, and documents. The database is Postgres, named by the env file.
set -euo pipefail

MAIN=/Users/sangit/src/japes
WT=/Users/sangit/src/japes-plato
PORT=8000
LOG="$MAIN/.plato-local.log"
HEALTH_WAIT_SECONDS=60

listener() { lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | head -1; }

pin() {
  local rev="${1:-$(git -C "$MAIN" rev-parse HEAD)}"
  if [ ! -d "$WT" ]; then
    git -C "$MAIN" worktree add --detach "$WT" "$rev"
  else
    git -C "$WT" checkout --detach "$rev"
  fi
  # The submodule from the main checkout's clone: no network, same commit the tree records.
  # safe.directory per command: git refuses the main checkout's module dir otherwise.
  git -C "$WT" -c protocol.file.allow=always -c submodule.common.url="$MAIN/common" \
    -c safe.directory="$MAIN/.git/modules/common" -c safe.directory="$MAIN/common" \
    submodule update --init common
  echo "pinned $WT at $(git -C "$WT" log --oneline -1)"
}

start() {
  if [ -n "$(listener)" ]; then
    echo "port $PORT is taken (pid $(listener)); stop it first" >&2
    exit 1
  fi
  [ -d "$WT" ] || pin
  (
    cd "$WT"
    export VIRTUAL_ENV="$MAIN/.venv" PATH="$MAIN/.venv/bin:$PATH"
    export JAPES_ENV_FILE="$MAIN/.env" JAPES_ENVIRONMENT=local PORT="$PORT"
    export PLATO_WIRING=plato.wiring.default:build PLATO_PROFILE=packs
    export PLATO_PACK_BLOB_DIR="$MAIN/.plato-pack-blobs" PLATO_PACK_CACHE_DIR="$MAIN/.plato-pack-cache"
    export JAPES_LOCAL_DATA_DIR="$MAIN/documents"
    echo "=== $(date -u +%FT%TZ) start from $WT at $(git log --oneline -1)" >> "$LOG"
    nohup python -m plato >> "$LOG" 2>&1 &
  )
  for _ in $(seq "$HEALTH_WAIT_SECONDS"); do
    if curl -sf "localhost:$PORT/health" >/dev/null; then status; return; fi
    sleep 1
  done
  echo "not healthy after ${HEALTH_WAIT_SECONDS}s; see $LOG" >&2
  exit 1
}

stop() {
  local pid; pid="$(listener)"
  [ -z "$pid" ] && { echo "nothing on :$PORT"; return; }
  kill "$pid"
  for _ in $(seq "$HEALTH_WAIT_SECONDS"); do [ -z "$(listener)" ] && { echo "stopped $pid"; return; }; sleep 1; done
  echo "pid $pid still listening" >&2
  exit 1
}

status() {
  [ -d "$WT" ] && echo "worktree: $(git -C "$WT" log --oneline -1)"
  local pid; pid="$(listener)"
  if [ -n "$pid" ]; then
    echo "server: pid $pid, cwd $(lsof -a -p "$pid" -d cwd -Fn | sed -n 's/^n//p'), $(curl -s "localhost:$PORT/health")"
  else
    echo "server: not running"
  fi
}

case "${1:-status}" in
  pin) pin "${2:-}" ;;
  start) start ;;
  stop) stop ;;
  restart) stop; pin "${2:-}"; start ;;
  status) status ;;
  *) echo "usage: $0 pin [rev] | start | stop | restart [rev] | status" >&2; exit 2 ;;
esac
