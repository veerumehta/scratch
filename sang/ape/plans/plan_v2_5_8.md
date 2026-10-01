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

## Scope (decided 2026-09-30: "let's do them all")

In order:

1. Human checkpoints: `SUSPENDED`, `/resume` (`plan_plato_domain_pack_runtime.md` §4.7, Phase 3).
   **Built** `327a063a` (suspend/resume, run outcomes). Left: documents upload, suspended-run TTL.
2. Config versioning and audit, all phases (`plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT.md`).
   D1: JAPES DB is the first control-plane store, behind a protocol. D2: new `content_digest()`
   beside `content_version()`. D3: audit tenancy in the stores first, match any shape found.
3. Formal checks as a Verifier asset (`plan_formal_verifier.md`): counterexample in
   findings/metadata for V1, no `witness` field.
4. Queue execution cancellation (`plan_queue_execution_cancellation.md`): `request_cancel` from
   both a governed HTTP route and a direct store call; latency rides `renew_leases`, with a
   `QueueSettings` knob.
5. Vision document ingest (`plan_vision_document_ingest.md`).
6. Pack store reader and tiered materialize (`plan_pack_store.md`, `plan_tiered_materialize.md`),
   re-verified against HEAD first.
7. anthropic 1.0 check (what 2.5.7's `strip_unsupported_params` already covers).
8. The six deferred TODOs below.
9. Eval step 7, as a local branch in eval-service.

Blocked: feedback step 8 (PR #54 unmerged), Acra cap adjustments and 4.9 (Acra).

## Deferred from 2.5.7 (TODOs in the code)

`reasoned-assess-runs-twice`, `case-run-assess-unreasoned`, `switched-store-not-backfilled`,
`sqlite-read-then-write-unserialized`, `zero-width-only-pattern-accepted`,
`supersede-check-outside-admit-lock`.
