#!/usr/bin/env bash
# Run the suite as parallel shards on this machine (CI's file split, `scripts/shard_tests.py`) with failures visible while it runs.
#   suite_shards.sh run [N] [dir]   start N shards (default 6) from <dir> (default: the current checkout) in the background
#   suite_shards.sh status          per shard: tests done, failures so far, finished or running; then every failure by name
# Run from the checkout whose venv and tree should be tested. Logs: /tmp/suite_shards/<stamp>/shard_<k>.log (-v: one line per test).
set -euo pipefail
ROOT=/tmp/suite_shards
case "${1:-status}" in
  run)
    N="${2:-6}"; DIR="${3:-$PWD}"; STAMP="$(date +%Y%m%dT%H%M%S)"; OUT="$ROOT/$STAMP"
    mkdir -p "$OUT"; ln -sfn "$OUT" "$ROOT/latest"
    cd "$DIR"
    for k in $(seq 1 "$N"); do
      python scripts/shard_tests.py --shard "$k" --shards "$N" > "$OUT/files_$k.txt"
      test -s "$OUT/files_$k.txt" || { echo "empty shard $k" >&2; exit 1; }
      ( python -m pytest -v -rfs -p no:cacheprovider $(cat "$OUT/files_$k.txt") > "$OUT/shard_$k.log" 2>&1
        echo "exit $?" > "$OUT/done_$k" ) > /dev/null 2>&1 &
    done
    echo "started $N shards in $OUT (status: $0 status)" ;;
  status)
    OUT="$ROOT/latest"; [ -d "$OUT" ] || { echo "no run"; exit 1; }
    for log in "$OUT"/shard_*.log; do
      k="${log##*_}"; k="${k%.log}"
      done_n=$(grep -cE ' (PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS)' "$log" || true)
      bad=$(grep -cE ' (FAILED|ERROR)( |$)' "$log" || true)
      state=running; [ -f "$OUT/done_$k" ] && state="$(cat "$OUT/done_$k")"
      echo "shard $k: $done_n tests, $bad failed, $state"
    done
    echo "--- failures so far"
    grep -hE '^tests/.* (FAILED|ERROR)' "$OUT"/shard_*.log | sed -E 's/ +\[ *[0-9]+%\]//' | sort -u ;;
  *) echo "usage: $0 run [N] [dir] | status" >&2; exit 2 ;;
esac
