# Note: Acra regeneration log (mine later)

Author: opus-xrepo. Machine log: `ape/local/coverage/regen_log.jsonl` (one JSON line per phase: extractions, code,
retry-failed, align, coverage, note). `acra_ledger_live.py` appends to it from now on; regen 2 and 3b are backfilled.
Per-run folders: `ape/local/coverage/regen_2`, `regen_3b` (`runs.json`, `state.json`, `coverage.json`, `coverage.xlsx`).

| | regen 2 | regen 3b | regen 3b after retry |
|---|---|---|---|
| Template | synced seed | + `fold:` and `data_mapping:` (`/tmp/acra_template_extra.yaml`) | same |
| jtbd proposals Standard / Platinum | 130 / 128 | 121 / 110 | |
| Jobs in coverage | 270 | 236 | 240 (6 orphans proposed as jobs) |
| code, code_and_procedure | 47, 103 (56%) | 34, 78 (47%) | 37, 83 (50%) |
| computable_no_code, not_computable, unassessed | 9, 91, 20 | 9, 85, 29 | 9, 84, 26 |
| Code proposals Standard / Platinum | 23 / 24 | 23 / 25 | |
| Failed code jobs | 0 | 12 (7 / 5), APIConnectionError | 0 (10 proposals; 2 standard jobs got no code) |
| Folds, mapped | n/a | 3, 7 | |

Findings so far
- 3b's lower coded share is mostly 12 code jobs lost to connection errors (the run reported succeeded; failures show only
  in `failed_segments`). Retry: `/tmp/acra_retry_failed_3b.sh` (phase `retry-failed`).
- Fewer jobs in 3b comes mostly from fewer jtbd proposals (-27), not fold (3 folds).
- The 3 folds look right against Acra's set: citizenship (Acra has one BOR-CITZ job); listed-for-sale determination
  (matches Acra's PRE-LISTDEF; Acra keeps PRE-LISTCOND, the conditions, apart and so do we); cash-out current lease
  (Acra has no separate job).
- Schema backlog: "calculated DSCR" (11), "DSCR" (8), "FICO" (5) no longer separate rows. "Acra confirmation ... (Q-07)"
  is an open question, not a data field: a job-writing quality case.
- Runs, spend: Acra ledger is rebuilt separately (memory `acra-cost-ledger`).
- Product asks: failed segments should retry automatically and show on the run summary and coverage.
- After the retry: coded 120 of 240 (50%), against regen 2's 150 of 270 (56%). The retry recovered 8. Disagreements 6 to 9, jobs with unprinted figures 10 to 13 (the new code).
