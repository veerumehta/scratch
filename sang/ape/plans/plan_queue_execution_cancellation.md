# Operator/caller-triggered cancellation via QueueExecutionStore

**Status:** scoped, not started

## Context

PR #37 (`akshatG-jazzx`, "Added cancellation support", opened 2026-06-11, closed 2026-08-19)
proposed a dedicated `japes-cancel` Azure queue: `run_once()` polled it every 10s, and a matching
`{"correlation_key": ...}` message cancelled the in-flight handler via `CancelledError`. It also
fixed two real bugs it found in the pre-QueueExecutionStore runtime: no response was ever sent to
`japes-response` on a mid-flight cancel/SIGTERM (caller hung forever), and the invocation message
was never deleted (Azure kept redelivering it after the visibility timeout).

Closed rather than merged, for two independent reasons:

1. **Structurally stale, not just conflicting.** `run_once()`/`_process_message()` have since been
   rewritten around `QueueExecutionStore`'s durable claim/heartbeat/lease protocol
   (`jazzx_sdk/queue_execution.py`, wired into `runtime.py::_process_message`). PR #37's diff
   assumed the old shape (`dequeue_message` → `_process_message` → manual `send_response`/
   `delete_message` in `run_once` itself) — that code no longer exists in that form.
2. **The design itself doesn't fit the current architecture even ported forward.**
   `check_cancel_queue()` dequeues up to 32 messages and requeues (`visibility_timeout=0`) every
   one that doesn't match — every worker, every 10s poll, forever for a cancel message that never
   finds its target (no TTL). Azure Storage Queues can't filter by correlation key, so this is an
   inherent cost of the "broadcast queue" shape, not an implementation bug to fix in place. It also
   maps a plain SIGTERM onto the same "send cancelled response" path as an explicit user cancel —
   conflating infra-triggered termination (which today correctly falls through to lease-expiry and
   pickup by another replica) with an intentional user action.

The **underlying capability — a caller or operator ending a long-running job before its lease
naturally expires — is still a real, unaddressed gap.** Today the only way a stuck/unwanted job
stops is waiting out `idempotency_lease_seconds` (default 300s) or killing the whole worker
(SIGTERM), which just gets the job retried elsewhere via `QueueExecutionStore`, not stopped.

## Design

Record cancellation as durable state on the same `QueueExecution` row `_process_message` already
claims/heartbeats — no new queue, no cross-worker scanning.

### `QueueExecution` / `QueueExecutionStore` — additive fields

```python
class QueueExecution(BaseModel):
    ...
    cancel_requested: bool = Field(default=False)
    cancel_reason: str | None = Field(default=None)
```

```python
@runtime_checkable
class QueueExecutionStore(Protocol):
    ...
    async def request_cancel(self, key: str, *, reason: str | None = None) -> None: ...
```

`request_cancel` **upserts**: if no record exists yet for `key` (the cancel arrived before any
worker claimed the message), create one with `cancel_requested=True` and no `claim_token`/
`lease_expires_at`, so the eventual `claim()` sees the flag already set rather than creating a
fresh, unflagged record. Implement on both `InProcessQueueExecutionStore` and
`DbQueueExecutionStore` (the latter needs a migration — additive nullable columns, same pattern as
every other `QueueExecutionRecord` field).

### Wiring — `_process_message`'s existing heartbeat loop

`runtime.py::_process_message` already runs `renew_leases()` in the background, calling
`extend_visibility(...)` every `renewal_seconds` (≤60s, min'd against `visibility_timeout // 3` and
`lease_seconds // 3` — see `runtime.py:436-442`). Add a cancellation check to the same loop instead
of a second poller:

```python
async def renew_leases() -> None:
    while True:
        await asyncio.sleep(renewal_seconds)
        await extend_visibility(...)
        execution = await self.queue_execution_store.get(execution_key)
        if execution is not None and execution.cancel_requested:
            running_task = asyncio.current_task()  # the task awaiting handler.handle(), not this one
            if running_task is not None and not running_task.done():
                running_task.cancel(msg=f"Cancelled: {execution.cancel_reason or 'no reason given'}")
            return
```

On `CancelledError` from this path, `_process_message` sends a `ResponseMessage(status="cancelled")`
through the **normal durable-settlement path** (`store_result` → `send_response` →
`mark_response_sent`), not a bespoke cleanup routine — this is the actual improvement over PR #37's
`_send_cancelled_and_delete`/`_run_to_completion_shielded` machinery: cancellation becomes a third
outcome of the existing claim lifecycle (`processing → cancelled` alongside `processing → ready →
delivering → completed`), so it inherits the existing shielding/idempotency/retry guarantees for
free instead of re-deriving them.

**SIGTERM stays untouched by this feature.** No new signal handler, no treating external
cancellation as user cancellation. A killed worker's claim still just expires and gets picked up by
another replica — exactly today's behavior. Only `cancel_requested` (set exclusively through
`request_cancel`) triggers the cancelled-response path.

### Caller/operator-facing surface

Not yet decided — **the open question below**. `job_id_for(message) == message.header.message_id`,
which the caller already has at submission time (they built the message), so whatever surface is
chosen needs no new correlation id — `request_cancel(message_id, reason=...)` is directly callable
with data the caller already holds.

## Explicitly out of scope for v1

- No change to `process_queue_until_empty` (mirrors PR #37's own scoping decision — MACER's entry
  point is `run_once`).
- No cancellation of a message still sitting undequeued with literally zero worker interest in it
  (nothing to cancel — it just never gets claimed if the caller gives up first; that's a caller-side
  concern, not a queue-execution one).
- No retroactive cancellation of an already-`COMPLETED`/`DELIVERING` execution — `request_cancel`
  on a terminal-state key is a no-op (log and return), not an error.

## Open questions that must be resolved before shipping, not glossed over

1. **Where does `request_cancel` get called from?** Options: (a) a new `server/app.py` HTTP route
   (`POST /cancel/{message_id}`) for remote callers, (b) direct store access for same-process/
   same-deployment callers (e.g. MACER, if it has DB access to the same `QueueExecutionStore`), or
   (c) both. This determines auth/scoping requirements the current design doesn't address — a cancel
   endpoint needs the same security-context checks as any other mutating route (see
   `server/governed_http.py`'s existing `Idempotency-Key` precedent for the shape of that
   reasoning).
2. **Poll granularity regression vs. PR #37.** Piggybacking on `renew_leases` means cancellation
   latency is bounded by `renewal_seconds` (up to 60s), not PR #37's dedicated 10s poll. Confirm
   that's acceptable for the actual use case before building — if sub-60s cancellation matters, the
   heartbeat cadence itself may need tightening (a `QueueSettings` knob), not a separate poller.
3. **Does `heartbeat()`'s own return contract need to carry this instead of a second `get()` call?**
   `extend_visibility` already calls `self.queue_execution_store.heartbeat(...)` every cycle;
   folding `cancel_requested` into `heartbeat`'s return value (vs. a separate `get()` right after)
   avoids one extra store round-trip per renewal. Worth deciding at implementation time based on
   how invasive changing `heartbeat`'s signature is for existing callers/tests.

## Tests (when implemented)

- `request_cancel` on a not-yet-claimed key creates a placeholder record; a subsequent `claim()`
  sees `cancel_requested=True` immediately.
- `request_cancel` on an in-flight (`PROCESSING`) key is picked up by the next heartbeat cycle and
  cancels the running handler.
- `request_cancel` on a terminal (`COMPLETED`/`DELIVERING`) key is a no-op, not an error.
- The cancelled response goes through `store_result`/`mark_response_sent` like any other outcome —
  a duplicate delivery of the same `message_id` after cancellation replays the persisted
  `cancelled` response rather than re-running the handler.
- SIGTERM with no `cancel_requested` set still falls through to lease expiry — unaffected by this
  feature (a regression test against the conflation PR #37 would have introduced).
- `DbQueueExecutionStore`: the new columns round-trip; migration is additive/nullable.

## Verification

1. New unit tests above, run alongside `tests/test_queue_execution_store.py` /
   `tests/test_dual_runtime.py` — no regressions.
2. Manually drive a long-running handler in a local job, call `request_cancel` mid-flight, confirm
   the caller receives `status="cancelled"` and the queue message is settled (not redelivered).
3. Confirm a plain SIGTERM (no `request_cancel` call) during the same test still results in
   lease-expiry-and-retry-elsewhere, not a cancelled response — the explicit regression check for
   the conflation this design deliberately avoids.
