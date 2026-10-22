# DocIntel fallback on loan-2 (sonnet-runtime, 2026-10-22)

Run: the loan-2 document read with `engine: {default: vision, fallback: docintel:prebuilt-read}` (scratch pack
`acra-e2e-fallback` 0.0.1, split on), approved by the user in session. Counts only; the summary is
`docs/status/Acra/Acra Lending/e2e/loan-2/fallback_run.json`.

| | earlier vision-only read | fallback read |
|---|---|---|
| documents | 38 | 37 |
| pages read by an engine | 325 | 325 |
| read by vision | 325 (4 failed) | 321 |
| read by DocIntel as fallback | 0 | 4 (all four vision failures: ModelBehaviorError after 3 retries) |
| pages still failed | 4 | 0 |
| cache hits | n/a | 0 (every page was sent again) |
| model cost | 0.55 USD | 0.56 USD |

Findings
- The fallback closes the four failed pages; nothing else changed in which engine read what.
- The vision page cache served nothing because it is off unless `JAPES_PAGE_CACHE_DIR` names a directory, and the local
  Plato does not set it: not a keying problem. Documented in `docs/DEPLOYMENT_ENV.md`; set it to make a re-read free.
- DocIntel pages billed were 4, as read: the first summary summed per-document tallies wrongly (the run's own usage and the
  per-item tallies agree). No accounting defect.
- The split differs by one document between the two reads (38 and 37): known nondeterminism of classification; not chased.
- DocIntel cost for 4 pages is negligible (about 0.006 USD at the read price).
