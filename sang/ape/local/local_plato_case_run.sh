#!/usr/bin/env bash
# Optionally upgrade and restart local Plato, wait for it, then run a case over one loan file.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   local_plato_case_run.sh [--upgrade [<rev>]] [--seed] --tenant <tenant> --pack <id> --file <pdf> ...
#
# `--seed` publishes the bundled seed packs into the tenant first (`POST /packs/initialize`,
# idempotent), for a tenant that has none: a run on an unpublished pack is a 404.
# Everything after the optional leading flags goes to case_run_with_documents.py
# (--base-url, --tenant, --pack, --file, --loan-id, --timeout-minutes). LOCAL Plato only: the run
# stores the extracted values of the file.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE_URL=http://localhost:8000
WAIT_SECONDS=120
if [[ "${1:-}" == "--upgrade" ]]; then
  shift
  rev=""
  if [[ "${1:-}" != "" && "${1:0:2}" != "--" ]]; then rev="$1"; shift; fi
  "$HERE/local_plato_upgrade.sh" $rev || { echo "upgrade or restart failed; not running the case"; exit 1; }
fi
SEED=0
if [[ "${1:-}" == "--seed" ]]; then SEED=1; shift; fi
for _ in $(seq 1 $((WAIT_SECONDS / 2))); do
  curl -fsS -o /dev/null "$BASE_URL/" 2>/dev/null && break
  sleep 2
done
"$HERE/plato_worktree.sh" status
if [[ "$SEED" == "1" ]]; then
  tenant=""
  args=("$@")
  for i in "${!args[@]}"; do [[ "${args[$i]}" == "--tenant" ]] && tenant="${args[$((i + 1))]}"; done
  [[ -n "$tenant" ]] || { echo "--seed needs --tenant"; exit 2; }
  echo "seeding $tenant:"
  curl -fsS -X POST -H "X-Tenant-Id: $tenant" -H "X-Trace-Id: $(uuidgen)" "$BASE_URL/api/v1/packs/initialize"
  echo
fi
cd /Users/sangit/src/japes || exit 1
exec python "$HERE/case_run_with_documents.py" --base-url "$BASE_URL" "$@"
