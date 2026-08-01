# Durable, single-consumer conductor resume (non-BPMN case)

**Status:** done

## Why

`ConductorEngine.resume()`'s `Suspension.resumed` flag is in-process only: if a `Suspension` is
persisted and reloaded by more than one process, nothing stops two processes from resuming it
concurrently and running the downstream side effect twice. `jazzx_sdk.runs.TurnRunStore` already
solves the identical shape of problem (atomic claim, claim-token fencing, heartbeat, fenced
stale-reap) for conversational turn runs. This closes the same gap for conductor HITL suspensions,
for scenarios running without a BPMN/Flowable process engine in front of them (Flowable's own
user/receive task already owns durability for the BPMN case — not duplicated here).

## What shipped

- `jazzx_sdk/conductor/suspension_store.py` — `SuspensionStatus` enum, `DurableSuspension` schema,
  `SuspensionStore` protocol (mirrors `TurnRunStore`'s method shapes), `InProcessSuspensionStore`.
- `jazzx_sdk/conductor/suspension_store_db.py` — `DbSuspensionStore` on `fabric.db` (plain SQLAlchemy
  2.0, `FOR UPDATE SKIP LOCKED` claim with a sqlite plain-select fallback, fenced `reap_stale`).
  Lazy-imported, not re-exported by `conductor/__init__.py` — same SQLAlchemy-opt-in split as
  `jazzx_sdk.runs`.
- `ConductorEngine` gained an optional `suspension_store` constructor param (`None` preserves
  existing behavior byte-for-byte) and a new `resume_durable(suspension_id, resolution, *,
  claim_token=None)` method: claims the suspension atomically first — the actual distributed
  single-consumer guarantee — then runs the tail through the same `_resume_tail` helper `resume()`
  uses, marking the suspension `resumed` or `failed` on the way out. `Suspension` gained a
  `suspension_id` field, set when a store is wired.
- `resume()` and `Suspension.resumed` are untouched for callers that don't need cross-process
  durability.

## Explicitly out of scope

- Wiring into any specific JACI scenario/conductor — this is an SDK primitive; adoption is separate.
- Periodic mid-tail heartbeating (only claim-time heartbeat).
- A real Postgres partial-unique-index migration — same as `TurnRunStore`, left to the consuming
  service's own migration.

## Tests

`tests/test_suspension_store.py` (create/get, claim, second-claim-returns-None, claim-fenced
heartbeat/mark_resumed/mark_failed, fenced `reap_stale` sparing a renewed heartbeat — run against
both `InProcessSuspensionStore` and the sqlite-backed `DbSuspensionStore`); `tests/test_conductor_engine.py`
additions (`resume_durable` happy path, missing-store raises, tail-failure marks the suspension
failed, and the concurrency race: two concurrent `resume_durable` calls on the same suspension via
`asyncio.gather` — exactly one wins, the tail runs once).
