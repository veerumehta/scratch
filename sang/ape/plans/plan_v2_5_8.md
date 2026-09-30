# Plan: v2.5.8

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: branch `v2.5.8` cut 2026-09-30 from `dev` at `2a2ad60b` (PR #86's squash of 2.5.7), SDK 2.5.8,
Plato 0.1.9. No shared history with `v2.5.7`.

## Carried in

- `eacaac6d`, cherry-picked from v2.5.7's `28587bb9` (pack programs vs their policies,
  repeated-rule warning, band edges vs the profile; DSCR seed regrouped into `process.yaml`).
  Owes a review (`REVIEW_UPSTREAM=origin/dev`).

## Flow

Work lands on `v2.5.8`, then `plato`, then `dev`, then `main`. `plato` still needs `dev` (`2a2ad60b`)
recorded on it before the next squash (`/tmp/japes_record_dev_after_86.sh`).

## Deferred from 2.5.7 (TODOs in the code)

`reasoned-assess-runs-twice`, `case-run-assess-unreasoned`, `switched-store-not-backfilled`,
`sqlite-read-then-write-unserialized`, `zero-width-only-pattern-accepted`,
`supersede-check-outside-admit-lock`.
