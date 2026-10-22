# Bounded model calls, a stall watchdog, and long document reads (sonnet-runtime, 2026-10-22)

Plan only. Checked `agents/run_kit.py`, `agents/openai_provider.py`, `runs/worker.py`, `evaluation/optimization_jobs.py`,
`agents/adjudication/workspace.py`, `agents/metering.py`.

## (a) Bounded calls and a stalled-run watchdog

Has: `run_agent` and `run_with_recovery` retry a schema failure, a truncated answer and an API status error (Retry-After,
backoff); `AsyncOpenAI(timeout=600)` is the only request timeout; `runs/worker.py` settles tasks on shutdown;
optimization jobs heartbeat and are reclaimed when stale; `CallMeter` records usage per call.
Lacks: a per-call deadline above the client timeout, a stage no-progress limit, a hedged second attempt, an attempt ledger
(a timed-out or cancelled call records nothing, so its spend is invisible), and a restart of a stalled long run.

### Guard (S-M)
`agents/call_guard.py`, one wrapper around a model call: `guarded(call, *, request_timeout, deadline, attempts, backoff,
hedge_after=None)`.
- `request_timeout` goes to the client; `deadline` is the whole call across retries (`asyncio.timeout`).
- Retry a timeout or connection error with backoff up to `attempts`; `run_with_recovery` keeps schema/truncation feedback and
  calls the guard for transport faults (its `APIStatusError` branch moves there).
- `hedge_after`: no answer by then starts a second attempt; the first to answer wins and the other is cancelled.
- Every attempt is one ledger row (`CallMeter.record` with `attempt`, `outcome`, `usage_incomplete=True` for a timeout or
  cancel, since its tokens are unknown). Cost counts the known part and the step's `cost_is_upper_bound` flag reads it.
- Defaults are named constants in the model card config, not literals.

### Stage watchdog and restart (M)
- `util/progress.py` `Progress` already counts finished units; a watchdog task per stage fails it with
  `stalled` after `idle_limit` seconds with no change in finished units or call count.
- `scripts/local/restart_stalled.py`-shaped wrapper in the SDK (`runs/restart.py`): runs a long job, on `stalled` restarts it up
  to `max_restarts`, reusing the page cache and keeping partial outputs (units already done are skipped by id).
- Why: regeneration 3b lost 12 code jobs to connection errors while the run said `succeeded`; a run reports `failed_segments`
  today, but the transport fault is retried by nothing below the client's own retries.

### Overlap
- `plan_optimization_job_hardening`: its first-predict deadline is this guard applied to one call; build the guard first and that
  plan's item 1 becomes `guarded(predict, deadline=first_predict_seconds)`. Its baseline reuse is independent.
- `run_with_recovery`: keeps its three recoveries; only the transport branch and the ledger row move. No change to callers.
- Queue visibility timeouts and `reclaim_stale` stay: they recover a dead worker, the watchdog recovers a live stuck one.
- Tests: hanging call fails at the deadline with a ledger row `usage_incomplete`; a hedge's loser is cancelled and recorded; a
  stalled stage restarts once and skips finished units; an idle-limit of zero is refused.

## (b) Long document reads and a continuation footer

Checked first, as asked. The evidence read path has a hard cap that errors (`enforce_read_cap`, `ReadTooLarge`) and says to
page, but nothing in the SDK calls it (grep: only the exports), and I found no read tool with a start/end range in the
adjudication path. So a long document today reaches a segment either whole in the prompt or not at all; there is no
truncation to fix and no way to ask for the rest.
Decision: do not build the footer now. Build it when a read tool exists that can return part of a document: then
truncate there, end with `[truncated: N of M characters; ask for the rest with start=K]`, and let `ReadTooLarge` carry the same
text. Hit the problem first (a loan packet read through a tool) before adding the tool.
