# Per-invocation completion hooks (producer-selected, not service-fixed)

**Status:** scoped, not started

## Context

Found while fixing `KernelClient.invoke_agent()` against kernel's real (regenerated) contract:
kernel's `AgentInvocationRequest.hooks_config` lets the *caller* attach a completion callback
inline on the invoke request itself (`{type: on_complete, config: {url, method, headers,
timeout_seconds, retries, retry_backoff_seconds}}`) — kernel builds and delivers it server-side
after the invocation finishes.

japes has the delivery mechanics already (`jazzx_sdk.channels`: `WebhookChannel` with retry +
optional HMAC, `WebSocketChannel`, `build_channel(name, **config)` registry, `notify_on_complete`/
`NotifyingHandler`) but not the caller-facing hook: `notify_on_complete` wraps a `Handler` with
**one channel fixed at deploy time by the service operator** — a producer calling that handler has
no way to say "notify *me*, at *this* url, for *this* invocation." That's the same gap `assistant`
independently hit and hand-rolled around (`response_consumer.py`'s bespoke webhook delivery,
identified in an earlier survey this session) — kernel's `hooks_config` is a validated, real-world
answer to the shape that gap should take.

**Explicitly not copying kernel's shape as-is** — two ways to do better, both using primitives
japes already has that kernel doesn't:

1. **Kernel's hook is hardcoded to a webhook** (`config: WebhookConfig`, always). japes already has
   a channel abstraction with more than one backend (`webhook`, `websocket`, whatever a pack
   registers via `register_channel`) and a data-driven builder (`build_channel(name, **config)`).
   A japes hook should name a channel (`{"channel": "webhook", "config": {...}}`) and dispatch
   through the existing registry, so any channel japes supports works as a completion notifier —
   not just webhook.
2. **Kernel's error payload is a plain string.** japes now has `jazzx_sdk.failures.classify_failure`/
   `StructuredFailure`/`redact_secrets` (shipped this session) — a completion hook's failure payload
   should carry a structured code/message/action and be redacted before it ever leaves the process,
   not a raw exception string handed to an external receiver.

## Design

### Wire contract — `MessageHeader.on_complete_hook`

Additive field, same pattern as `session_id`:

```python
class HookSpec(BaseModel):
    channel: str                       # a name build_channel() recognizes: "webhook", "websocket", ...
    config: dict[str, Any] = {}         # splatted into build_channel(channel, **config)

on_complete_hook: HookSpec | None = None   # on MessageHeader, alongside session_id/correlation_key
```

`build_invocation(..., on_complete_hook: HookSpec | None = None)` gets the matching kwarg,
unconditional pass-through (`None` is meaningful — no hook requested), same convention as
`session_id`.

### Delivery — new function in `jazzx_sdk/channels/notify.py`

```python
async def deliver_completion_hook(message: QueueMessage, response: ResponseMessage) -> None:
    hook = message.header.on_complete_hook
    if hook is None:
        return
    try:
        channel = build_channel(hook.channel, **hook.config)
        await channel.send(_hook_message(response))
    except Exception:  # best-effort — a bad hook spec must not break the invocation's own response
        logger.warning("completion hook delivery failed", exc_info=True)
```

`_hook_message` mirrors `_default_message`'s shape but replaces the raw `response.error` string
with `classify_failure(...)` output (redacted) when `response.status == "error"`.

**Distinct from `notify_on_complete`, not a replacement for it** — that decorator stays exactly as
it is (a service operator's static, always-on notification, e.g. an audit-log webhook every
invocation goes to regardless of caller). `deliver_completion_hook` is the new, orthogonal,
per-message, caller-selected path. Both can fire for the same invocation.

**Wiring point**: call `deliver_completion_hook(message, response)` from the same three places
`attach_incoming_trace_context` was wired into earlier this session (`runtime.py`, `server.py`,
`events.py`'s post-`handler.handle()` tail) — the precedent for "one new cross-cutting behavior,
wired at every entry point that produces a `ResponseMessage`," not just the queue path.

## Explicitly out of scope for v1

- Only one hook type (`on_complete`, fires on both success and failure — failure detail rides in
  the payload via `StructuredFailure`, not a separate `on_error` hook). Kernel itself only has
  `ON_COMPLETE` too — no evidence a split is needed yet; add `on_error`/`on_progress` only if a
  real caller asks (progress already has a channel: the existing SSE `/stream` tail).
- No change to `notify_on_complete`/`NotifyingHandler` — additive, parallel path.
- No per-hook retry/timeout override surface beyond what `hook.config` already lets through (since
  `config` is splatted straight into `build_channel`, a caller can already pass `timeout=`/
  `attempts=` for `WebhookChannel` today — no new plumbing needed for that).

## Open question that must be resolved before shipping, not glossed over

**SSRF**: `hook.config["url"]` (for a webhook hook) is caller-supplied and would cause japes's own
infrastructure to make an outbound HTTP call to an address the *caller* chose. This needs an
allowlist/deny-list policy (block private/link-local ranges at minimum) before this ships to any
multi-tenant deployment — not something to solve implicitly inside `WebhookChannel`. Flagging as a
hard prerequisite, not a nice-to-have.

## Tests (when implemented)

- `HookSpec` round-trips through `MessageHeader`/`build_invocation`, `None` by default.
- `deliver_completion_hook` builds the right channel from `hook.channel`/`hook.config` and calls
  `.send()` with the expected message (mock `build_channel`/a fake `Channel`).
- A failing response's hook payload carries a `classify_failure`-shaped, redacted failure — not the
  raw exception string.
- A bad/unknown `hook.channel` name degrades to a logged warning, never raises into the caller's
  own response path.
- `notify_on_complete`'s existing static path is unaffected when a message also carries a dynamic
  `on_complete_hook` (both fire, independently).

## Verification

1. New unit tests above, run alongside existing `tests/test_invocation_contract.py` /
   `tests/test_channels*.py` (whatever the actual channel test file is named — confirm at
   implementation time) — no regressions.
2. Manually confirm all three entry points (`runtime.py`, `server.py`, `events.py`) call
   `deliver_completion_hook` after producing a `ResponseMessage`, mirroring the
   `attach_incoming_trace_context` wiring precedent exactly.
