# Status: Per-invocation completion hooks (producer-selected, not service-fixed)

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_invocation_completion_hooks.md

**Core mechanism built and tested. The plan's own hard SSRF prerequisite is closed — and turned
out to be a real, live gap in an EXISTING mechanism the plan didn't know about, not just a
hypothetical for the new one.** One architectural question is deliberately left open below rather
than decided unilaterally. This is a `status_` file, not `done_`, because of that open question and
because verification (#2 below) — a live click-through of all three entry points — hasn't happened.

## Real finding not in the plan: an overlapping mechanism already ships

While researching this, found that `MessageHeader.webhook_url`/`webhook_secret` already exist and
already do almost exactly what this plan asks for — a per-invocation, caller-selected webhook
notification, delivered by `QueueProcessor._deliver_webhook` (shipped 2.2.2). It differs from what
this plan wants in exactly the two ways the plan's own critique of kernel's shape predicted:
hardcoded to webhook (not channel-agnostic), and delivers `response.model_dump()` raw with no
`classify_failure`/redaction — plus it's queue-path only (`send_response` is never called from
`server.py`'s `/invoke` or `events.py`'s inbound router).

**Open decision, not made here**: should the new `on_complete_hook`/`HookSpec` absorb/replace
`webhook_url`/`webhook_secret`, or should the two stay parallel indefinitely? Left both fields on
`MessageHeader` (removing a shipped, tested field is a breaking change with no evidence anyone
does or doesn't depend on it — not a call to make unilaterally while the plan owner is away) and
documented the overlap directly in `HookSpec`'s own docstring so it isn't silently forgotten.

## A real, live SSRF gap found and fixed (independent value, not just a new-feature prerequisite)

The plan's own text flags SSRF on `hook.config["url"]` as a hard, must-not-skip prerequisite for
the *new* mechanism. Checking `WebhookChannel.send()` directly (the shared delivery path both the
old and new mechanisms use) found it had **zero URL validation at all** — meaning the SSRF gap was
already live today via the shipped `webhook_url` path, not hypothetical.

Fixed by extracting `jazzx_sdk/tools/documents.py`'s tested SSRF guard
(`_is_private_ip`/`_validate_url_safe`, originally built for `read_from_url`) into a new shared
`jazzx_sdk/net_safety.py` (`is_private_ip`/`validate_url_safe`), and calling
`validate_url_safe(url)` from `WebhookChannel.send()` before every POST — covers both the old
`webhook_url` path and the new `HookSpec` path in one fix, since both ultimately go through the
same `WebhookChannel`. `documents.py` keeps a thin local `_validate_url_safe` (aliasing the shared
`is_private_ip`) specifically so its own existing monkeypatch-based test
(`tests/test_read_from_url_ssrf.py`) keeps passing unchanged rather than needing rewiring.

No redirect-revalidation logic was needed for `WebhookChannel` (unlike `read_from_url`'s manual
redirect loop) — confirmed directly that `httpx.AsyncClient`'s default is `follow_redirects=False`,
and `WebhookChannel.send()` never overrides that, so a malicious redirect target is never actually
fetched in the first place; only the direct-URL case needed guarding.

**Existing tests broke and were fixed, not silently patched around**: `tests/test_channels.py`'s
webhook tests and `tests/test_queue_processor.py`'s webhook-delivery tests all use `.example`
placeholder domains with no DNS mocking — `validate_url_safe`'s real `socket.gethostbyname` call
against an unregistered TLD raises `socket.gaierror`, which `is_private_ip` treats as private
(fail-closed default), which broke 4 previously-passing tests. Fixed with an autouse
`monkeypatch.setattr(net_safety, "is_private_ip", lambda h: False)` fixture in each file — avoids
real DNS lookups in tests entirely, rather than switching to real-but-obscure resolvable domains.

2 new tests in `tests/test_channels.py` cover a private channel URL and a private per-message
`target` override, both refused before any request is made.

## The core mechanism

- **`HookSpec`** (`jazzx_sdk/models.py`): `channel: str`, `config: dict = {}`. New
  `MessageHeader.on_complete_hook: HookSpec | None = None` field, alongside `webhook_url`/
  `webhook_secret` (see open decision above). `build_invocation(..., on_complete_hook=None)` — same
  unconditional-pass-through convention as `session_id`.
- **`deliver_completion_hook(message, response)`** (`jazzx_sdk/channels/notify.py`): reads
  `message.header.on_complete_hook`; if set, `build_channel(hook.channel, **hook.config)` and
  sends a message mirroring `_default_message`'s shape via a new `_hook_message(response)`, except
  a failing response's raw `error` dict is replaced with a `classify_failure`-derived
  `{code, message, action}` (message run through `redact_secrets`) rather than a raw string.
  Best-effort throughout — a bad channel name or a failed send is logged, never raised into the
  caller's own response path (verified: `test_bad_channel_name_degrades_to_a_warning_never_raises`,
  `test_a_failing_channel_send_is_logged_never_raised`).
- **Wired at the exact three entry points named** (`attach_incoming_trace_context`'s precedent):
  - `runtime.py` — restructured the try/except (which previously `return`ed from two separate
    branches) into a single tail so `deliver_completion_hook` fires once regardless of success/
    failure, inside the same `finally`-guarded block.
  - `server.py` — guarded with `isinstance(response, ResponseMessage)`, since a handler may return
    a typed `Refusal` there instead (confirmed directly: `Refusal` has no `.header`/`.status`/
    `.error` shape this function needs, and a hook is asking about invocation completion, not a
    designed refusal outcome).
  - `events.py` — cleanest; `response` is always a `ResponseMessage` here, placed right after the
    existing `finally` block, before the `JSONResponse` return.
  - All three verified by running their own existing test files (58 tests across
    `test_handler_context_job_id.py`/`test_server.py`/`test_events.py`/`test_events_domain.py`/
    `test_governed_http.py`/`test_rbac_forwarding.py`/`test_runs_server.py`/
    `test_automation_governed.py`/`test_otel_tracking.py`) — all still pass.

## Tests (matching the plan's own list, plus the SSRF prerequisite's own coverage)

New `tests/test_completion_hooks.py` (7 tests): no-hook no-op, delivers with the expected message
shape, `hook.config` reaches `build_channel` (and a real, narrow footgun found doing this: a config
key literally named `"name"` collides with `build_channel(name, **config)`'s own positional
parameter and raises `TypeError` — caught by the existing best-effort guard, degrades to a logged
warning, never breaks the invocation; not fixed, since it's a pre-existing property of
`build_channel`'s own signature and out of this plan's scope, flagging for whoever next touches
that signature), error payload is structured+redacted (verified against a monkeypatched
`classify_failure` carrying a real secret, not relying on the real classifier's own — mostly
templated, not raw-text-echoing — messages to exercise the redaction path meaningfully), bad
channel name warns not raises, failing send warns not raises, and the plan's own explicit
acceptance item — `notify_on_complete`'s static path and a message's dynamic `on_complete_hook`
both fire independently for the same invocation, proven by actually running both and checking both
channels received a message with the same `correlation_key`.

Plus 2 new `tests/test_invocation_contract.py` tests (`on_complete_hook` defaults to `None`, round-
trips through `ResponseMessage.header` the same way `session_id`/`webhook_url` already do) and the
2 new SSRF tests in `tests/test_channels.py` above.

Full japes suite: 2028 passed (up from 2019 before this feature — the 9 new tests above), 3
skipped, no failures.

## Deliberately not done / not decided (stated, not silently dropped)

- **webhook_url vs on_complete_hook coexistence** — the real open question above. Recommend the
  plan owner decide explicitly before either field gains more callers.
- **No per-hook retry/timeout override surface beyond `hook.config`** — matches the plan's own
  explicit "out of scope for v1."
- **Only `on_complete`, no `on_error`/`on_progress`** — matches the plan's own explicit scope.
- **The `build_channel(name=...)` collision noted above** — not fixed, out of scope, flagged.
- **Manual click-through verification of the three live entry points** — not done (no running
  server/queue environment available in this pass); only the existing test suites for each entry
  point were re-run and confirmed unaffected.
