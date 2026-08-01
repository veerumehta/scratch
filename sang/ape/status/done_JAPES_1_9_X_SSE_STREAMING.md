# JAPES 1.9.x: SSE Streaming for Server Mode

Author: Virendra Mehta
Created: Wednesday, July 1, 2026
Status: Draft for discussion — corrected after Claude Code review
Repos affected: `japes/`

## Why this plan exists

JAPES's `StreamPublisher` already publishes typed events (`LLMChunkEvent`, `ToolStartEvent`,
`ToolEndEvent`, `DoneEvent`, `ErrorEvent`) to a Redis stream keyed by `invocation:{streaming_id}`
via `common.core.redis_streams.RedisStreamClient`. The event vocabulary is shared with the
platform via `common.core.streaming`. However, nothing in the SDK currently reads that Redis
stream and surfaces it to an HTTP caller over SSE. The `server.py` `/invoke` endpoint is fully
synchronous - it blocks on `await handler.handle(ctx)` and returns a `JSONResponse` only after
the handler completes. This is the gap: JAPES publishes to Redis correctly but has no last-mile
bridge from Redis to the client.

Juno solves this differently - it streams OpenAI SDK tokens directly inside the HTTP response,
skipping Redis entirely, because Juno's handlers run in-process with the HTTP request. JAPES's
queue-mode handlers are decoupled (queue workers, not in-request), so the Redis bridge is the
right architecture for queue-mode JAPES.

The goal of this plan is to add a general, clean SSE streaming capability to the SDK so that any
JAPES-based solution - and eventually Juno - can share the same streaming contract without
adopting a bespoke pattern per solution.

## Architecture decision: two-step invocation/observation

**Decision: Option B - two-step.** The client supplies a `streaming_id` UUID in the `/invoke`
request body (see Gap 1 below). The handler picks it up via `set_streaming_id()` and publishes
events to `invocation:{streaming_id}`. A separate `GET /stream/{streaming_id}` endpoint tails
that Redis stream as SSE.

Reasons:
- Invocation and observation are decoupled in queue-mode JAPES (handler runs in a separate
  worker). Keeping them decoupled at the HTTP layer is the consistent design.
- A separate GET endpoint supports `?replay=true` (return buffered events only, no tail) - the
  same pattern as Juno's `sse_api.py`.
- Multiple consumers can observe the same invocation stream (e.g., audit surface + UI) without
  re-invoking.
- Any solution - Juno, Jazz Assistant, future domain pack UIs - can converge on
  `GET /stream/{streaming_id}` without changing its invocation path.

## Resolved design gaps (from Claude Code review of first draft)

**Gap 1 - streaming_id was not in the /invoke response.** The original plan claimed
`streaming_id` was "already in the current response." It is not. `streaming_id` exists only as a
server-side ContextVar (`set_streaming_id`/`get_streaming_id`); it is not a field on
`ResponseMessage` and is not returned by `/invoke`. Fix: the client supplies `streaming_id` in the
`/invoke` request body as an optional field. The handler reads it from `HandlerContext` and calls
`set_streaming_id()`. This works symmetrically across server mode and queue mode and does not
require extending `ResponseMessage`.

**Gap 2 - server-mode /invoke is synchronous.** In `create_app()`'s server mode,
`await handler.handle(ctx)` runs in-process inside the HTTP request; by the time `/invoke`
returns, the handler is done and the stream is complete. Live tailing (`replay=False`) is only
meaningful when a queue worker runs the invocation concurrently with the SSE consumer. In server
mode, `GET /stream/{id}` degenerates to replay-only. The plan explicitly targets queue-mode
deployments for live tail; server-mode callers should use `replay=True`.

**Wrap-common correction.** The first draft used a raw `redis.asyncio.Redis.xread` call,
reinventing what `common.core.redis_streams.RedisStreamClient.subscribe(stream_name, count,
block, last_id) -> (messages, new_last_id)` already provides - and the write side already goes
through `RedisStreamClient`. The reader takes a `RedisStreamClient` (not a raw Redis client) and
calls `subscribe()`, symmetric with the write side.

**Replay truncation bug.** The first draft read one `xread(count=100)` batch then returned on
`if replay: return`, silently capping replay at 100 events. Fix: in replay mode, loop advancing
`last_id` with non-blocking reads until a batch comes back empty.

**Minor corrections.** `StreamEventModel` import in `sse_reader` was unused (removed).
`asyncio.get_event_loop().time()` inside a coroutine corrected to
`asyncio.get_running_loop().time()`.

## What this plan does NOT change

- Does not change `POST /invoke`, `HandlerContext`, or `ResponseMessage` fields - existing callers
  are unaffected. `streaming_id` on the invoke body is optional; omitting it means no events are
  published and `GET /stream` is a no-op.
- Does not change `StreamPublisher` or the Redis event vocabulary.
- Does not introduce solution-specific event types; the canonical `common.core.streaming` types
  are the only vocabulary.
- Does not force Juno or any other solution to migrate.
- Does not implement authentication on the SSE endpoint. Auth strategy is left to the deploying
  solution via FastAPI dependency injection.
- Does not add Redis buffering or persistence beyond what the stream's retention policy provides.

## Phase 1: SSEStreamReader

A new utility in `jazzx_sdk/streaming/` that reads typed events from a Redis stream via
`RedisStreamClient` and yields them as SSE frames.

New file: `jazzx_sdk/streaming/sse_reader.py`

```python
import asyncio
import json
import logging
from collections.abc import AsyncIterator

from jazzx_sdk.streaming.publisher import invocation_stream

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_MS = 15_000
DONE_EVENT_TYPES = {"done", "error"}  # StreamEventType.done / .error


async def stream_invocation_sse(
    stream_client: "RedisStreamClient",  # common.core.redis_streams.RedisStreamClient
    streaming_id: str,
    *,
    replay: bool = False,
    heartbeat_interval_ms: int = HEARTBEAT_INTERVAL_MS,
    timeout: float | None = None,
) -> AsyncIterator[str]:
    """Read typed events from a Redis stream and yield SSE-formatted strings.

    Yields:
        "data: {json}\\n\\n" for events, ": heartbeat\\n\\n" for keepalive.

    Args:
        stream_client: A RedisStreamClient (same type used by StreamPublisher.publish).
        streaming_id: The invocation streaming_id; stream name is invocation:{streaming_id}.
        replay: If True, read all buffered events from offset 0 and stop; do not tail.
        heartbeat_interval_ms: Milliseconds passed to subscribe(block=...) for keepalive.
        timeout: Hard wall-clock timeout in seconds; yields an error frame and exits.
    """
    stream_name = invocation_stream(streaming_id)
    last_id = "0-0" if replay else "$"
    deadline = asyncio.get_running_loop().time() + timeout if timeout else None

    while True:
        if deadline and asyncio.get_running_loop().time() > deadline:
            yield _sse_frame({"event_type": "error", "message": "stream timeout"})
            return

        try:
            if replay:
                # block=None omits the BLOCK argument entirely — plain non-blocking XREAD.
                # block=0 would mean "block forever", which hangs after the buffer drains.
                messages, new_last_id = await stream_client.subscribe(
                    stream_name, count=100, block=None, last_id=last_id
                )
            else:
                # Blocking read; timeout elapses → emit heartbeat and loop.
                messages, new_last_id = await stream_client.subscribe(
                    stream_name, count=100, block=heartbeat_interval_ms, last_id=last_id
                )
        except Exception as e:
            logger.warning("SSEStreamReader: subscribe failed (%s); yielding error frame", e)
            yield _sse_frame({"event_type": "error", "message": str(e)})
            return

        if not messages:
            if replay:
                return  # backfill complete; empty batch means no more events
            # live-tail block timeout; emit heartbeat and continue
            yield ": heartbeat\n\n"
            continue

        last_id = new_last_id
        for _msg_id, fields in messages:
            try:
                event = json.loads(fields.get("event", "{}"))
            except json.JSONDecodeError:
                logger.warning("SSEStreamReader: malformed event in %s", stream_name)
                continue
            yield _sse_frame(event)
            if event.get("event_type") in DONE_EVENT_TYPES:
                return


def _sse_frame(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
```

Per-file changes:

| File | Change |
|---|---|
| `jazzx_sdk/streaming/sse_reader.py` | new |
| `jazzx_sdk/streaming/__init__.py` | export `stream_invocation_sse` |

## Phase 2: Client-supplied streaming_id on /invoke + SSE endpoint

**Part A - streaming_id in InvokeRequest.** `InvokeRequest` in `server.py` gains an optional
`streaming_id: str | None = None` field. When present, the handler context carries it and the
handler calls `set_streaming_id(streaming_id)` at the top of `handle()`. When absent, no events
are published and the stream endpoint is a no-op for that invocation.

**Part B - GET /stream/{streaming_id}.** Added to `create_app()`. Gated on an optional
`stream_client: RedisStreamClient | None` parameter; if `None`, the endpoint returns 503 and is
not registered (backward compatible).

Per-file changes:

| File | Change |
|---|---|
| `jazzx_sdk/server.py` | `InvokeRequest.streaming_id: str | None = None`; `create_app()` gains `stream_client` and `stream_auth_dep` optional params; `GET {prefix}/stream/{streaming_id}` endpoint added |
| `jazzx_sdk/server.py` | `ServerSettings.stream_heartbeat_interval_ms: int = 15_000` |

Endpoint sketch:

```python
@app.get(f"{prefix}/stream/{{streaming_id}}")
async def stream_events(
    streaming_id: str,
    replay: bool = False,
    _auth=Depends(stream_auth_dep) if stream_auth_dep else None,
):
    if stream_client is None:
        return JSONResponse({"error": "streaming not configured"}, status_code=503)

    async def generate():
        async for frame in stream_invocation_sse(
            stream_client,
            streaming_id,
            replay=replay,
            heartbeat_interval_ms=settings.stream_heartbeat_interval_ms,
        ):
            yield frame

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

**Deployment note:** live tail (`replay=False`) is meaningful only in queue-mode deployments where
a worker runs the invocation concurrently with the SSE consumer. In server-mode deployments (where
`/invoke` is synchronous and the handler completes before returning), the stream is already
complete by the time the client opens `GET /stream`; callers in server mode should use
`replay=True`.

## Phase 3: Handler convention guide

Handlers must always emit a terminal event so `SSEStreamReader` exits cleanly.

New section in `jazzx_sdk/streaming/` docs (or appended to `TRACING_AND_OUTCOME_GUIDE.md`):
- Always call `set_streaming_id(ctx.streaming_id)` at the top of `handle()` before the first
  `publish()`.
- Always emit `DoneEvent` at the end of the success path.
- Always emit `ErrorEvent` before raising from `handle()`; the timeout on `stream_invocation_sse`
  is a safety net, not the primary exit mechanism.
- In server mode, `streaming_id` on the invoke request is optional; omit it for non-streaming
  invocations.

## Phase 4: Heartbeat tuning in ServerSettings

`ServerSettings.stream_heartbeat_interval_ms: int = 15_000` (added in Phase 2) surfaces the
keepalive tuning to deployers without code changes. 15 seconds is chosen to keep the connection
alive through nginx/ALB idle timeouts (typically 60 seconds) during slow reasoning runs.

## Sequencing

Phase 1 is the core primitive, prerequisite for Phase 2. Phases 3 and 4 are independent.
Recommended order: 1, 2, 4, 3 (documentation last).

## What Juno convergence looks like (non-binding, for context)

Juno currently streams OpenAI tokens directly inside the HTTP response. A Juno migration path:

1. `skill_service.stream_message()` publishes canonical `common.core.streaming` events to Redis
   via `StreamPublisher` instead of yielding dicts directly.
2. Juno's `/messages/stream` endpoint becomes a thin wrapper over `stream_invocation_sse`.
3. Juno's custom event types (`agent_start`, `handoff`, `content_delta`, `tool_call`,
   `tool_result`) either map to canonical types or are added to `common.core.streaming` as
   platform-wide vocabulary.

The SDK needs only to be capable and consistent; convergence happens at Juno's pace.

## Acceptance checks

```bash
# Phase 1
python -c "from jazzx_sdk.streaming import stream_invocation_sse"

# Phase 2
grep "streaming_id" jazzx_sdk/server.py
grep "stream_client" jazzx_sdk/server.py
grep "stream_auth_dep" jazzx_sdk/server.py

# Phase 4
grep "stream_heartbeat_interval_ms" jazzx_sdk/server.py

# Integration (queue-mode): start a queue worker, POST /invoke with streaming_id,
# open GET /stream/{id} concurrently, assert DoneEvent frame arrives and connection closes.
# Integration (server-mode): POST /invoke with streaming_id, then GET /stream/{id}?replay=true,
# assert full event history returned and connection closes.
```

## Resolved decisions

- Client supplies `streaming_id`; not returned by `/invoke`.
- Reader uses `RedisStreamClient.subscribe()`, symmetric with `StreamPublisher` write side.
- Replay loops until empty batch; no event cap.
- Live tail targets queue-mode deployments; server-mode callers use replay.
- `get_running_loop()` inside coroutines; `StreamEventModel` import removed.

## Open questions

- Should `stream_invocation_sse` be exposed as an MCP tool or only as an HTTP endpoint? Likely
  HTTP-only for now.
- Should the `HandlerContext` carry `streaming_id` explicitly (cleaner than a ContextVar for
  non-async paths), or stay with the current ContextVar pattern?
