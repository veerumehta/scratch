# Plan: v2.5.8

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: branch `v2.5.8` cut 2026-09-30 from the `v2.5.7` tip, SDK 2.5.8, Plato 0.1.9. v2.5.7 is PR
#86 (plato -> dev, `origin/plato` `3ec88c32`, tree = `v2.5.7` `32a6001c`).

## Carried in

- `28587bb9` (pack programs vs their policies, repeated-rule warning, band edges vs the profile;
  DSCR seed regrouped into `process.yaml`): landed on v2.5.7 after #86 was cut; in 2.5.8 by
  decision. Owes a review (`REVIEW_UPSTREAM=32a6001c`).

## Flow

Work lands on `v2.5.8`, then `plato`, then `dev`, then `main`. A fix for PR #86 lands here and is
cherry-picked to `plato` alone (a tree copy would carry `28587bb9`). When #86 squashes into `dev`,
record `dev` on `v2.5.8` and on `plato` (a merge commit keeping the tree, after checking `dev`'s tree
is one the branch contains).

## Deferred from 2.5.7 (TODOs in the code)

`reasoned-assess-runs-twice`, `case-run-assess-unreasoned`, `switched-store-not-backfilled`,
`sqlite-read-then-write-unserialized`, `zero-width-only-pattern-accepted`,
`supersede-check-outside-admit-lock`.
