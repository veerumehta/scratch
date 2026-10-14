#!/usr/bin/env bash
# Regenerate the Acra jobs and code from the synced seed on a fresh trial pack, end to end.
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#   acra_regen.sh <trial-pack-id> <output-dir>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY=/Users/sangit/src/japes/.venv/bin/python
export ACRA_TRIAL="$1" ACRA_DIR="$2"
mkdir -p "$ACRA_DIR"
cd "$HERE"
"$PY" acra_ledger_live.py seed
"$PY" acra_rerun_extractions.py --pack "$ACRA_TRIAL" --out "$ACRA_DIR/runs.json"
"$PY" acra_ledger_live.py merge-jobs
"$PY" acra_ledger_live.py code
"$PY" acra_ledger_live.py align
"$PY" acra_ledger_live.py coverage
echo "done: $ACRA_TRIAL -> $ACRA_DIR"
