# Plan: v2.6.0 (begun as v2.5.8)

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

## Scope (decided 2026-09-30: "let's do them all")

| # | Item | State |
|---|---|---|
| 1 | Human checkpoints (`plan_plato_domain_pack_runtime.md` §4.7) | Built `327a063a`, approver fix `2bd5c865`. Left: documents upload (no design yet), suspended-run TTL. |
| 2 | Config versioning Rev 2 (`plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT.md`) | Built `1438607c`: audit trail, `If-Match` activation, releases. Phase 3 superseded by the pack store, Phase 7 dropped. Left: `TODO(stream-release-id)`, release on traces (VersionBundle frozen). |
| 3 | Formal checks as a Verifier asset | Already built (attestation, witness in findings). Rest has no consumer; not built. |
| 4 | Queue execution cancellation | Built `282e6782`. Consumers' migrations add two columns. |
| 5 | Vision ingest | Mostly already built; identity veto `c216effe`, token buckets `2b8d22d7`. Accuracy unmeasured. |
| 6 | Pack store / tiered materialize | Tiered `95898f11`. Pack store's remaining steps gated on conditions not met. Grounding breakdown still unmeasured. |
| 7 | anthropic 1.0 | Compatible `9ea2e161`; lock still 0.111. |
| 8 | Deferred TODOs | sqlite double-claim fixed `0582d9f9`; five stand. |
| 9 | Eval step 7 (eval-service branch) | Not started: eval-service is changing daily (11k lines in core); needs the user's call (convergence talk first, per that plan's §8). |
| + | Plato client package (`plan_plato_client_package.md`) | Phases 1-2 built `a4ff0566`, `baacd9ac`. Phase 3 is jaci's. |

Blocked: feedback step 8 (PR #54 unmerged), Acra cap adjustments and 4.9 (Acra).

## Deferred from 2.5.7 (TODOs in the code)

`reasoned-assess-runs-twice`, `case-run-assess-unreasoned`, `switched-store-not-backfilled`,
`sqlite-read-then-write-unserialized`, `zero-width-only-pattern-accepted`,
`supersede-check-outside-admit-lock`.
