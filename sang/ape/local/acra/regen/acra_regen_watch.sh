#!/bin/bash
# Run in a second pane while the regen runs. Every 30s prints: the newest policy_extract progress line from
# local Plato's log, how many model calls the last minute made (0 for several minutes means stuck), and the
# regen processes still alive. Ctrl-C to stop.
LOG=/Users/sangit/src/japes/.plato-local.log
while true; do
  now=$(date +%H:%M:%S)
  progress=$(grep -E "policy_extract: [0-9]+ of [0-9]+" "$LOG" | tail -1 | sed -E 's/.*(policy_extract: .*)/\1/')
  calls=$(grep -c "api.openai.com/v1/responses" <(tail -n 400 "$LOG"))
  alive=$(pgrep -f "acra_(rerun_extractions|ledger_live)" | wc -l | tr -d ' ')
  echo "$now  ${progress:-no progress line yet}  | model calls in the last 400 log lines: $calls  | regen processes: $alive"
  sleep 30
done
