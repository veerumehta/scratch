#!/bin/bash
# Re-run the 12 code jobs that failed with a connection error in regen 3b, merge them, re-align, re-read coverage.
# Does not restart Plato. Logs to ape/local/coverage/regen_log.jsonl. Output goes back into regen_3b (the
# first coverage.json is kept as coverage_before_retry.json).
set -u
HERE=/Users/sangit/src/.scratch/sang/ape/local
PY=/Users/sangit/src/japes/.venv/bin/python
export ACRA_TRIAL=acra-regen-3b ACRA_DIR="$HERE/coverage/regen_3b"
cp -n "$ACRA_DIR/coverage.json" "$ACRA_DIR/coverage_before_retry.json"
cp -n "$ACRA_DIR/coverage.xlsx" "$ACRA_DIR/coverage_before_retry.xlsx"
cd "$HERE"
"$PY" acra_ledger_live.py retry-failed && "$PY" acra_ledger_live.py align && "$PY" acra_ledger_live.py coverage
