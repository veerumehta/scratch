# plan_JAPES_2_0_CONSISTENCY_AND_ENRICHMENT.md

**Author:** Virendra Mehta
**Execute with:** Claude Code from `/Users/sangit/src/japes/`
**Status:** Ready for execution
**Verified against:** JAPES v1.9.5 — filesystem read June 28, 2026

---

## Purpose

This plan addresses internal JAPES SDK consistency gaps and targeted enrichments
needed to support multiple concurrent scenarios and clients — the Jazz Assistant
(MACER-based conversational surface), JACI domain packs (AML, KYC, CI Spread,
CRE), and future domain assistants. Items are derived from a full filesystem audit
of the live codebase against the drift audit (`plan_II_drift_audit_2026-06-07.md`),
the JAPES CHANGELOG, and the Juno codebase comparison.

Items are batched by version increment and ordered within each batch by blocking
priority. Claude Code should work through one batch at a time and run the
acceptance checks before moving to the next.

---

## Verified baseline state (do not re-derive — read from code)

The following were confirmed by direct filesystem read before writing this plan.
Claude Code must re-read each file before editing — do not rely on the descriptions
below as the authoritative source of current content.

| Component | State |
|---|---|
| `jazzx_sdk/skills/` | Exists with `governance/`, `evidence/`, `investigation/` — all have `base.py` |
| `jazzx_sdk/experts/governance/`, `evidence/`, `investigative/` | Directories exist but are empty (`__pycache__` only, no Python files) |
| `jazzx_sdk/experts/catalog.py` `EXPERT_REGISTRY` | Already 3-entry (policy, playbook, discovery) |
| `jazzx_sdk/experts/registry.py` `_get_default_expert_class` | Still routes `evidence`/`governance`/`investigative` to empty dirs — **latent bug** |
| `modes/schemas.py` — `Attestation`/`Freshness`/`Outcome` collision | **Already fixed** in v1.6.3 (PLAT-01 done). Imports from `fabric.canonical` |
| `fabric/pack/__init__.py` | Exists as back-compat shim pointing to `jazzx_sdk.pack` |
| `jazzx_sdk/pack/` | Exists with `Pack`, `DomainPackHelper`, `DomainPackFabric`, `PackManifestLoader` |
| `fabric.pack` property on `KnowledgeFabric` | **Not wired** — `fabric.py` has no `.pack` property |
| `agents/interactive/agent.py` `_respond_agentic` | No `hooks=` threading to Runner or sub-agents — **gap** |
| `agents/interactive/agent.py` `_respond_agentic` | No general `model_settings=` on non-responses agentic path — **gap** |
| `jazzx_sdk/streaming/` | Does not exist |
| `jazzx_sdk/clients/` | Has `KernelClient`, `KnowledgeHubClient` only — no `AssistantClient` |
| Security context `ContextVar` | Not in SDK — each extension hand-rolls it |
| `HandlerContext.security_context` | Field exists but not auto-wired into `ClientLayer` headers |

---

## Batch 1 — Bug fixes and critical gaps (v1.9.6)

Real bugs or gaps that cause `ImportError` or silent wrong behavior in the current
release. Fix first, before any enrichment.

### Change 1.1 — Fix `ExpertRegistry._get_default_expert_class` stale routing

**File:** `jazzx_sdk/experts/registry.py`

**Problem:** `_get_default_expert_class` routes `evidence`, `governance`, and
`investigative` to `jazzx_sdk.experts.evidence`, `.governance`, and `.investigative`.
Those directories exist but are empty (no `__init__.py`, no Python files after the
v1.5 restructure). Any call to `registry.get_expert("evidence")` raises
`ModuleNotFoundError` at runtime.

The Skills bases are now abstract — there are no concrete `Default*` implementations
to auto-instantiate for these three types. The correct pattern is `register_instance`.

**Fix:** Replace the three stale routes with a clear `ValueError` directing callers
to the Skill base + `register_instance` pattern:

```python
def _get_default_expert_class(self, expert_type: str) -> Type[BaseExpert]:
    if expert_type == "policy":
        from jazzx_sdk.experts.policy import DefaultPolicyExpert
        return DefaultPolicyExpert
    elif expert_type == "playbook":
        from jazzx_sdk.experts.playbook import DefaultPlaybookExpert
        return DefaultPlaybookExpert
    elif expert_type in ("evidence", "governance", "investigative"):
        raise ValueError(
            f"'{expert_type}' is a Skill bundle (IIF v1.5), not an Expert surface. "
            f"Subclass the appropriate base from jazzx_sdk.skills and register "
            f"an instance via ExpertRegistry.register_instance('{expert_type}', instance). "
            f"Expert surfaces are: policy, playbook, discovery."
        )
    else:
        raise ValueError(
            f"Unknown expert_type: {expert_type}. "
            f"Expert surfaces: policy, playbook, discovery. "
            f"Skill bundles (use register_instance): governance, evidence, investigative."
        )
```

**Also update** the `ExpertRegistry` class docstring — remove the examples that call
`register_expert("governance", ...)` etc. Replace with IIF v1.5 examples showing
`register_instance` for Skill bundles.

**Acceptance:**
```python
from jazzx_sdk.experts.registry import ExpertRegistry
r = ExpertRegistry(pack_id="test")
try:
    r.get_expert("governance")
    assert False, "should have raised"
except ValueError as e:
    assert "Skill bundle" in str(e) and "register_instance" in str(e)
print("1.1 ok")
```

---

### Change 1.2 — Wire `fabric.pack` property on `KnowledgeFabric`

**File:** `jazzx_sdk/fabric/fabric.py`

**Problem:** PLAT-03 from the drift audit. `ARCHITECTURE.md` documents `fabric.pack`
as the pack-registration surface. `jazzx_sdk.pack.DomainPackFabric` registers a
pack's ontology and policy bundle into the fabric at init — but `KnowledgeFabric`
exposes no `.pack` property. Scenarios have no facade-level path to register a pack.

Read `jazzx_sdk/fabric/fabric.py` and `jazzx_sdk/pack/loader.py` in full before
editing to confirm current constructor signatures.

**Fix:** Add a lazy-initialized `pack` property to `KnowledgeFabric`:

```python
@property
def pack(self) -> "DomainPackFabric":
    """Domain Pack fabric accessor — registers ontology + policy bundle.

    Use pack to load a pack's manifest and register its ontology and policy set
    into this fabric instance. The full Pack access object (Pack.bind(runtime))
    lives at jazzx_sdk.pack and composes fabric + modes + experts + conductor.

    Returns:
        DomainPackFabric helper backed by this fabric instance.
    """
    if not hasattr(self, "_pack_fabric") or self._pack_fabric is None:
        from jazzx_sdk.pack.loader import DomainPackFabric
        self._pack_fabric = DomainPackFabric(
            kh_client=self._kh_client,
            config=self._config,
        )
    return self._pack_fabric
```

Add `self._pack_fabric = None` in `__init__` so the attribute is declared.

Adjust the `DomainPackFabric` constructor call if `loader.py` uses different
parameter names — read it first.

**Acceptance:**
```python
from jazzx_sdk.fabric import fabric_from_env
f = fabric_from_env()
assert f.pack is not None
print("1.2 ok — fabric.pack accessible")
```

---

### Change 1.3 — Remove empty expert ghost directories

**Problem:** `jazzx_sdk/experts/evidence/`, `jazzx_sdk/experts/governance/`, and
`jazzx_sdk/experts/investigative/` exist with only `__pycache__`. They are misleading
to tooling and developers. The v1.5 restructure plan intended them to be deleted.

**Fix:** Delete the three directories. No Python code imports from them after Change 1.1.

```bash
rm -rf jazzx_sdk/experts/evidence/
rm -rf jazzx_sdk/experts/governance/
rm -rf jazzx_sdk/experts/investigative/
```

**Acceptance:**
```python
import os
for d in ["evidence", "governance", "investigative"]:
    assert not os.path.exists(f"jazzx_sdk/experts/{d}"), f"{d} still exists"
print("1.3 ok")
```

---

### Change 1.4 — `AgentHooks` pass-through on `InteractiveAgent`

**File:** `jazzx_sdk/agents/interactive/agent.py`

**Problem:** `_respond_agentic` calls `Runner.run(agent, input=list(messages))` with
no `hooks=` argument. `_build_parent_tools` builds sub-agents via `build_agent(...)`
with no `hooks=`. Any streaming-capable assistant surface needs per-tool streaming
events. Without hooks threading, tool-level events are dark regardless of what the
caller constructs.

Read `agent.py` in full before editing.

**Fix — three touchpoints:**

1. Add `hooks: Any | None = None` to `__init__`, store as `self._hooks`.

2. In `_build_parent_tools`, add `hooks=self._hooks` to sub-agent `build_agent` calls.

3. In `_respond_agentic`, pass `hooks=self._hooks` to both:
   - The parent agent `build_agent` call inside `_respond_agentic`
   - The `Runner.run(agent, input=list(messages), hooks=self._hooks)` call inside
     the lambda passed to `run_with_context_window_fallback`

**Acceptance:**
```python
from unittest.mock import MagicMock
from jazzx_sdk.agents.interactive.agent import InteractiveAgent
from jazzx_sdk.agents.interactive.spec import InteractiveAgentSpec

spec = InteractiveAgentSpec(name="t", skills=[])
mock_hooks = MagicMock()
ia = InteractiveAgent(spec, agents=MagicMock(), hooks=mock_hooks)
assert ia._hooks is mock_hooks
print("1.4 ok")
```

---

### Change 1.5 — General `model_settings` pass-through on `_respond_agentic`

**Files:** `jazzx_sdk/agents/interactive/spec.py`, `agent.py`

**Problem:** On the non-responses agentic path, `build_kwargs` never includes
`model_settings`. Callers that want `reasoning_effort` or `service_tier` (flex)
have no way to pass them through. The setting is silently ignored.

Read `spec.py` and `agent.py` in full before editing.

**Fix in `spec.py`:** Add two optional fields to `InteractiveAgentSpec`:

```python
reasoning_effort: str | None = None   # "high" | "medium" | "low"
service_tier: str | None = None       # "flex" | None
```

**Fix in `agent.py`, `_respond_agentic`:** After the `responses` check but before
building the parent agent, add:

```python
if not responses and (self.spec.reasoning_effort or self.spec.service_tier):
    from jazzx_sdk.agents.models import build_model_settings
    build_kwargs["model_settings"] = build_model_settings(
        reasoning_effort=self.spec.reasoning_effort,
        service_tier=self.spec.service_tier,
    )
```

Additive — when neither field is set, behavior is unchanged.

**Acceptance:**
```python
from jazzx_sdk.agents.interactive.spec import InteractiveAgentSpec
s = InteractiveAgentSpec(name="t", reasoning_effort="high", service_tier="flex")
assert s.reasoning_effort == "high" and s.service_tier == "flex"
print("1.5 ok")
```

---

## Batch 2 — Security context and streaming infrastructure (v1.9.7)

Reduce boilerplate that every extension currently hand-rolls independently.

### Change 2.1 — SDK-owned security context `ContextVar`

**New file:** `jazzx_sdk/context.py`

**Problem:** Every extension handler declares its own `ContextVar[str]` for security
context and wires a `request_headers_provider` into `ClientLayer`. Pure boilerplate.
`HandlerContext.security_context` already carries the value but nothing propagates it.

**Fix:** Create `jazzx_sdk/context.py`:

```python
"""
Platform-level execution context propagation.

Author: Virendra Mehta

Provides a ContextVar for security context so extensions propagate caller
identity through async call chains without passing it explicitly.
The ClientLayer reads this via the default request_headers_provider when
no explicit provider is injected.

Usage in extension handlers:
    from jazzx_sdk.context import set_security_context

    async def handle(self, ctx: HandlerContext) -> ResponseMessage:
        set_security_context(ctx.security_context)
        # All downstream ClientLayer calls now forward x-security-context
        ...
"""

from contextvars import ContextVar

_security_context_var: ContextVar[str] = ContextVar(
    "jazzx_security_context", default=""
)


def set_security_context(value: str | None) -> None:
    """Set the security context for the current async task."""
    _security_context_var.set(value or "")


def get_security_context() -> str:
    """Return the security context for the current async task, or empty string."""
    return _security_context_var.get()


def default_request_headers_provider() -> dict[str, str]:
    """Default header provider for ClientLayer — forwards security context when set."""
    sc = _security_context_var.get()
    return {"x-security-context": sc} if sc else {}
```

**Wire into `HandlerContext`:** In `handlers.py`, add a dispatch helper to `BaseHandler`
that sets the context before delegating to `handle()`:

```python
async def _dispatch(self, ctx: HandlerContext) -> ResponseMessage:
    from jazzx_sdk.context import set_security_context
    set_security_context(ctx.security_context)
    return await self.handle(ctx)
```

**Wire into `ClientLayer`:** In `client_layer.py`, import and use
`default_request_headers_provider` as the fallback when no `request_headers_provider`
is passed:

```python
from jazzx_sdk.context import default_request_headers_provider as _default_headers

# In __init__, change:
self._request_headers_provider = (
    request_headers_provider
    if request_headers_provider is not None
    else _default_headers
)
```

Read `client_layer.py` in full before editing — confirm the exact field name.
This is backward compatible.

**Acceptance:**
```python
from jazzx_sdk.context import set_security_context, get_security_context, default_request_headers_provider
set_security_context("tok_abc")
assert get_security_context() == "tok_abc"
assert default_request_headers_provider()["x-security-context"] == "tok_abc"
set_security_context(None)
assert default_request_headers_provider() == {}
print("2.1 ok")
```

---

### Change 2.2 — `StreamPublisher` platform primitive

**New directory and files:** `jazzx_sdk/streaming/__init__.py`,
`jazzx_sdk/streaming/publisher.py`

**Problem:** No streaming event publication primitive exists in the SDK. Any extension
that publishes tool breadcrumbs or done events to a Redis stream hand-rolls the Redis
write pattern. This is the third cross-extension infrastructure item to standardize.

**`jazzx_sdk/streaming/__init__.py`:**
```python
"""Streaming event publication for JAPES extensions."""
from jazzx_sdk.streaming.publisher import StreamPublisher, StreamEvent
__all__ = ["StreamPublisher", "StreamEvent"]
```

**`jazzx_sdk/streaming/publisher.py`:**
```python
"""
StreamPublisher — publish structured events to a Redis stream.

Author: Virendra Mehta

Redis key pattern: invocation:{streaming_id}
Message format:   {"type": event.type, "payload": json, "ts": epoch_ms}

Usage:
    publisher = StreamPublisher.from_client(redis_client, streaming_id=sid)
    await publisher.publish(StreamEvent(type="tool_start", payload={"name": "get_findings"}))
"""
from __future__ import annotations
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    streaming_id: str | None = None

    @property
    def payload_json(self) -> str:
        return json.dumps(self.payload, default=str)


class StreamPublisher:
    """Publishes StreamEvents to a Redis stream keyed by streaming_id.

    When no Redis client is provided (noop mode), publish() is a silent no-op.
    Extensions that do not configure streaming use StreamPublisher.noop().
    """

    def __init__(self, client: Any | None = None, *, streaming_id: str = "") -> None:
        self._client = client
        self._streaming_id = streaming_id

    @classmethod
    def from_client(cls, client: Any, *, streaming_id: str = "") -> "StreamPublisher":
        return cls(client=client, streaming_id=streaming_id)

    @classmethod
    def noop(cls) -> "StreamPublisher":
        """Silent publisher for non-streaming contexts."""
        return cls(client=None, streaming_id="")

    def with_streaming_id(self, streaming_id: str) -> "StreamPublisher":
        """Return a new publisher bound to a specific invocation streaming_id."""
        return StreamPublisher(client=self._client, streaming_id=streaming_id)

    @property
    def enabled(self) -> bool:
        return self._client is not None and bool(self._streaming_id)

    async def publish(self, event: StreamEvent) -> None:
        if not self.enabled:
            return
        sid = event.streaming_id or self._streaming_id
        key = f"invocation:{sid}"
        message = {
            "type": event.type,
            "payload": event.payload_json,
            "ts": str(int(time.time() * 1000)),
        }
        try:
            await self._client.xadd(key, message)
        except Exception as exc:
            logger.warning("StreamPublisher.publish failed for %s: %s", key, exc)

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
```

**Wire `streaming_id` into `HandlerContext`:** In `handlers.py`, add
`streaming_id: str | None = None` to `HandlerContext`. Read `handlers.py` in full
before editing to find the right position.

**Acceptance:**
```python
from jazzx_sdk.streaming import StreamPublisher, StreamEvent
import asyncio
p = StreamPublisher.noop()
asyncio.run(p.publish(StreamEvent(type="done", payload={})))
assert not p.enabled
print("2.2 ok — noop publisher works")
```

---

### Change 2.3 — `AssistantClient` in `jazzx_sdk/clients/`

**New file:** `jazzx_sdk/clients/assistant_client.py`

**Problem:** Every conversational assistant extension needs to fetch prior turns from
the JazzX assistant API, parse message history, and trim to a size budget. There is
no SDK primitive for this — each extension will write its own.

**`jazzx_sdk/clients/assistant_client.py`:**
```python
"""
AssistantClient — fetch conversation history from the JazzX assistant API.

Author: Virendra Mehta

Usage:
    from jazzx_sdk.clients import AssistantClient
    client = AssistantClient(base_url=ASSISTANT_URL)
    turns = await client.get_turns(conversation_id, max_session_size_kb=256)
"""
from __future__ import annotations
import json
import logging
from collections.abc import Callable
from typing import Any
import httpx

logger = logging.getLogger(__name__)

Turn = dict[str, Any]


class AssistantClient:
    """Fetch and trim conversation turns from the JazzX assistant API."""

    def __init__(
        self,
        base_url: str,
        *,
        request_headers_provider: Callable[[], dict[str, str]] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers_provider = request_headers_provider
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        base = {"Content-Type": "application/json"}
        if self._headers_provider:
            base.update(self._headers_provider())
        return base

    async def get_turns(
        self,
        conversation_id: str,
        *,
        max_session_size_kb: int = 256,
        roles: tuple[str, ...] = ("user", "assistant"),
    ) -> list[Turn]:
        """Fetch prior turns for a conversation, trimmed to budget.

        Returns oldest-first list of turn dicts. Returns [] on any error.
        max_session_size_kb=0 disables trimming.
        """
        url = f"{self._base_url}/conversations/{conversation_id}/messages"
        async with httpx.AsyncClient(timeout=self._timeout) as http:
            try:
                resp = await http.get(url, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                logger.warning("AssistantClient.get_turns failed for %s: %s",
                               conversation_id, exc)
                return []

        messages: list[Turn] = (
            data if isinstance(data, list) else data.get("messages", [])
        )
        turns = [m for m in messages if m.get("role") in roles]

        if max_session_size_kb > 0:
            turns = _trim_to_budget(turns, max_session_size_kb * 1024)
        return turns

    async def get_latest_question(self, conversation_id: str) -> str:
        """Return the most recent user message content, or empty string."""
        turns = await self.get_turns(conversation_id, max_session_size_kb=0)
        for turn in reversed(turns):
            if turn.get("role") == "user":
                return str(turn.get("content", ""))
        return ""


def _trim_to_budget(turns: list[Turn], max_bytes: int) -> list[Turn]:
    """Drop oldest turns until total JSON size is under max_bytes."""
    while turns:
        if len(json.dumps(turns, default=str).encode()) <= max_bytes:
            break
        turns = turns[1:]
    return turns
```

**Update `clients/__init__.py`:** Add `AssistantClient` and `Turn` to imports and
`__all__`. Read the file first.

**Acceptance:**
```python
from jazzx_sdk.clients import AssistantClient
from jazzx_sdk.clients.assistant_client import _trim_to_budget
turns = [{"role": "user", "content": "x" * 500}] * 10
trimmed = _trim_to_budget(turns, 1000)
assert len(trimmed) < 10
print("2.3 ok")
```

---

## Batch 3 — `InteractiveAgent` skill enrichment (v1.9.8)

Extend the `Skill` data model to support MCP-per-skill and structured output.

### Change 3.1 — Add `mcp_servers` to `InteractiveAgentSpec.Skill`

**Files:** `jazzx_sdk/agents/interactive/spec.py`, `agent.py`

**Problem:** `spec.mcp_servers` applies to the parent agent only. Skills that need
their own MCP connections (a credit assistant skill calling SEC EDGAR, a KYC skill
calling a sanctions database) have no way to declare them.

Read both files in full before editing.

**Fix in `spec.py`:** Add to the `Skill` model:
```python
mcp_servers: list[str] = Field(default_factory=list)
```

**Fix in `agent.py`, `_build_parent_tools`:** Resolve and pass per-skill MCP servers:
```python
sub_mcp = [self._resolve_mcp(n) for n in (sdef.mcp_servers or [])]
sub_agent = self._agents.openai.build_agent(
    name=name,
    instructions=self._skill_instructions(sdef),
    tools=sub_tools,
    model=model,
    mcp_servers=sub_mcp,    # <-- add
    hooks=self._hooks,       # from Change 1.4
)
```

**Acceptance:**
```python
from jazzx_sdk.agents.interactive.spec import Skill
s = Skill(name="edgar-reader", mcp_servers=["edgar-mcp"])
assert s.mcp_servers == ["edgar-mcp"]
print("3.1 ok")
```

---

### Change 3.2 — Add `output_schema` to `InteractiveAgentSpec.Skill`

**Files:** `jazzx_sdk/agents/interactive/spec.py`, `agent.py`

**Problem:** Skill sub-agents return free text. When a skill is designed to produce
structured output (citation list, formatted memo section), callers must parse text
manually. Adding `output_schema` (JSON Schema string) lets a skill declare its
return shape.

**Fix in `spec.py`:**
```python
output_schema: str | None = None  # JSON Schema string for structured sub-agent output
```

**Fix in `agent.py`, `_build_parent_tools`:** When `sdef.output_schema` is set:
```python
output_type = None
if getattr(sdef, "output_schema", None):
    import json as _json
    from jazzx_sdk.agents.run_kit import RawJsonSchemaOutput
    try:
        schema = _json.loads(sdef.output_schema)
        output_type = RawJsonSchemaOutput(schema, name=name)
    except Exception:
        pass  # malformed schema — fall back to free text

sub_agent = self._agents.openai.build_agent(
    name=name,
    instructions=self._skill_instructions(sdef),
    tools=sub_tools,
    model=model,
    mcp_servers=sub_mcp,
    output_type=output_type,
    hooks=self._hooks,
)
```

**Acceptance:**
```python
from jazzx_sdk.agents.interactive.spec import Skill
import json
schema = json.dumps({"type": "object", "properties": {"citations": {"type": "array"}}})
s = Skill(name="citer", output_schema=schema)
assert s.output_schema is not None
print("3.2 ok")
```

---

## Batch 4 — Outcome linkage reference implementation (v1.9.9)

This closes the compounding loop for the reference scenario (AML). This change
is in JACI, not JAPES. Execute in `/Users/sangit/src/jaci/`.

### Change 4.1 — AML: link Outcome in the live handler path

**File:** `jaci/src/jaci/aml/japes_handler.py`

**Problem:** XCUT-OUTCOME-01 from the drift audit. `japes_handler.py` calls
`put_case_file(case_file)` without `outcome=`. The `Outcome.from_case_file` method
exists in `jaci/src/jaci/aml/schemas/outcome.py`. The compounding loop closes only
in the eval harness — the live handler never creates an Outcome.

Read `japes_handler.py`, `schemas/outcome.py`, and the `put_case_file` signature
in `jazzx_sdk/fabric/canonical/store.py` before editing.

**Fix:** At case completion, before calling `put_case_file`, construct an Outcome:

```python
from jaci.aml.schemas.outcome import Outcome as AMLOutcome

outcome = AMLOutcome.from_case_file(case_file)
await ctx.runtime.fabric.canonical.put_case_file(case_file, outcome=outcome)
```

Adjust class paths and parameter names to match actual signatures.

This is the reference pattern for every other scenario (KYC, CRE, CI Spread) to copy.
Document it in a comment above the call:
```python
# Outcome linkage: close the compounding loop in the live handler path.
# Other scenarios copy this pattern — do not remove.
```

**Acceptance:** Run AML eval harness and confirm `outcome_id` is non-null on case
results. Spot-check that `outcome.decision_id` matches the case's
`CanonicalDecision.decision_id`.

---

## Batch 5 — Discovery surface and docstring cleanup (v1.9.9)

### Change 5.1 — `ExpertRegistry` class docstring update

**File:** `jazzx_sdk/experts/registry.py`

Read the file first. Remove examples that call `register_expert("governance", ...)`,
`register_expert("evidence", ...)`, etc. These are now wrong. Replace the class-level
docstring example block with the IIF v1.5 pattern:

```
Expert surfaces (register_expert): policy, playbook, discovery.
Skill bundles (register_instance): governance, evidence, investigative.

Example — Expert surface:
    registry.register_expert("policy", MyPolicyExpert)

Example — Skill bundle:
    from jazzx_sdk.skills.governance import BaseGovernanceSkill
    class AMLGovernanceSkill(BaseGovernanceSkill):
        async def enforce(...): ...
    registry.register_instance("governance", AMLGovernanceSkill(pack_id="aml"))
```

### Change 5.2 — Discovery Expert migration note in `experts/__init__.py`

**File:** `jazzx_sdk/experts/__init__.py`

Read the file first. Above the Discovery Expert imports, add a comment:

```python
# DiscoveryExpert is planned for migration to the Automation surface
# (jazzx_sdk.automation). It remains here for backward compatibility but is
# not a first-class Expert surface in IIF v1.5. For new domain pack work,
# use the Automation surface for proactive knowledge acquisition.
```

This is documentation-only — no import changes.

---

## Batch 6 — Version bumps after each batch

After each batch's acceptance tests pass:

- `jazzx_sdk/_version.py`: bump version string
- `pyproject.toml`: bump `version =` to match (keep in sync)
- `CHANGELOG.md`: add entry under `[Unreleased]`

**Version sequence:**
| Batch | Changes | Version |
|---|---|---|
| 1 | 1.1-1.5 | 1.9.6 |
| 2 | 2.1-2.3 | 1.9.7 |
| 3 | 3.1-3.2 | 1.9.8 |
| 4-5 | 4.1, 5.1-5.2 | 1.9.9 |

---

## Full smoke test sequence

Run after all batches complete from `/Users/sangit/src/japes/`:

```python
# Batch 1 — bug fixes
from jazzx_sdk.experts.registry import ExpertRegistry
r = ExpertRegistry(pack_id="smoke")
try:
    r.get_expert("governance")
    assert False
except ValueError as e:
    assert "Skill bundle" in str(e) and "register_instance" in str(e)

from jazzx_sdk.fabric import fabric_from_env
f = fabric_from_env()
assert f.pack is not None

import os
for d in ["evidence", "governance", "investigative"]:
    assert not os.path.exists(f"jazzx_sdk/experts/{d}"), f"{d} still exists"

from unittest.mock import MagicMock
from jazzx_sdk.agents.interactive.agent import InteractiveAgent
from jazzx_sdk.agents.interactive.spec import InteractiveAgentSpec
ia = InteractiveAgent(InteractiveAgentSpec(name="t", skills=[]), agents=MagicMock(), hooks=MagicMock())
assert ia._hooks is not None

s = InteractiveAgentSpec(name="t2", reasoning_effort="high", service_tier="flex")
assert s.reasoning_effort == "high" and s.service_tier == "flex"

# Batch 2 — infrastructure
from jazzx_sdk.context import set_security_context, default_request_headers_provider
set_security_context("tok_test")
assert default_request_headers_provider()["x-security-context"] == "tok_test"
set_security_context(None)
assert default_request_headers_provider() == {}

from jazzx_sdk.streaming import StreamPublisher, StreamEvent
import asyncio
p = StreamPublisher.noop()
asyncio.run(p.publish(StreamEvent(type="done", payload={})))
assert not p.enabled

from jazzx_sdk.clients import AssistantClient
from jazzx_sdk.clients.assistant_client import _trim_to_budget
turns = [{"role": "user", "content": "x" * 500}] * 10
assert len(_trim_to_budget(turns, 1000)) < 10

# Batch 3 — skill enrichment
from jazzx_sdk.agents.interactive.spec import Skill
import json
s = Skill(name="t", mcp_servers=["edgar-mcp"], output_schema=json.dumps({"type": "object"}))
assert s.mcp_servers == ["edgar-mcp"] and s.output_schema is not None

# Import smoke
import jazzx_sdk.streaming
import jazzx_sdk.context
import jazzx_sdk.clients.assistant_client
import jazzx_sdk.experts.registry
import jazzx_sdk.fabric.fabric

print("All smoke tests passed")
```

---

## What this plan does NOT address

These items from the drift audit are excluded to keep scope focused. They belong in
separate plans or in JACI-side remediation passes:

- **PLAT-02** (DomainPack v1.5 manifest-minimum version fields) — partially present
  in `DomainPackHelper`; full enforcement is a JACI scenarios remediation item
- **XCUT-FABRIC-01** (`use_mocks=True` production defaults) — JACI-side fix
- **SCN-* items** (per-scenario promotion, pack-registration, policy externalization)
  — JACI-side fixes; each scenario needs a dedicated pass
- **AML-02** (TraceStep emission reference implementation) — separate focused plan;
  should follow Change 4.1 since AML live handler must be the reference scenario first
- **`ToolNamespaceRegistry`** with `defer_loading` grouping (Juno pattern) — useful
  but not blocking; separate enrichment plan
- **`GuardrailRegistry` platform base entries** for safety categories — Jazz Assistant
  will drive this; separate plan once the assistant design is finalized

---

## Jazz Assistant canonical chain design constraint

Jazz Assistant reads MACER findings as opaque grounding context. MACER findings have
not yet been ported to canonical Evidence/Decision split. This constraint governs
what Jazz Assistant may and may not do canonically:

**Must NOT:**
- Emit `CanonicalDecision` objects that reference MACER `finding_id` values as
  `evidence_refs` — the provenance chain would have a broken link
- Write a `CanonicalDecision` for an answer that claims canonical grounding when
  the underlying evidence is not yet canonical

**Must:**
- Write its answer as a `Finding` entity via `fabric.docs` (the fifth fabric store),
  not a raw Knowledge Hub write — this keeps it addressable through the fabric facade
  when the canonical promotion path is ready
- Carry `policy_refs` and `doc_refs` in that Finding — these are already structured
  and meaningful today
- Use `streaming_id` and `trace_id`/`span_id` from the invocation for observability

**Evolution path (not yet actionable):** Once MACER findings are canonical Evidence,
the assistant's Finding becomes promotable to a `CanonicalDecision` with `evidence_refs`
pointing to the grounding Evidence objects. No code change is needed at that point if
the interim pattern above is followed — the upgrade is additive.

Document this constraint on the Jazz Assistant engineering design Notion page, not in
code, so it does not couple JAPES to the Jazz Assistant timeline.
