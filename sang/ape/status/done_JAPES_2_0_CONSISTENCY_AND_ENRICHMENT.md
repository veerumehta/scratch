# plan_JAPES_2_0_CONSISTENCY_AND_ENRICHMENT.md

**Author:** Virendra Mehta
**Execute with:** Claude Code from `/Users/sangit/src/japes/`
**Branch:** v2.0-consistency (from main)
**Status:** Ready for execution
**Scope:** Multi-scenario consistency, InteractiveAgent enrichment, assistant surface primitives.
**JAPES version at time of writing:** 1.9.5

---

## Context and ground truth

This plan was produced after reading the live filesystem at v1.9.5. Several items from
prior analysis were already implemented - the plan is grounded only in what is actually
missing after reading the code. Confirmed before writing:

- `jazzx_sdk/skills/` - exists and fully implemented (governance, evidence, investigation bases)
- `modes/schemas.py` PLAT-01 (Attestation/Freshness/Outcome re-declarations) - already fixed in 1.6.3
- `EXPERT_REGISTRY` - already has only 3 entries (policy, playbook, discovery)
- `TransactionContext` / `InvestigationContext` alias - both exist in schemas.py
- `fabric.canonical.domain_pack` (DomainPackStore) - exists in store.py
- `CompactionPolicy`, `ConversationStore`, `InProcessConversationStore` - fully implemented in 1.9.4/1.9.5
- `OpenAIAgentsBinding`, `ResponsesCompaction`, token-authoritative compaction - fully implemented in 1.9.5

**What is genuinely missing and addressed by this plan:**

1. `ExpertRegistry._get_default_expert_class` still routes `evidence`/`governance`/`investigative`
   to their former directories, which are now empty `__pycache__`-only dirs - live ImportError bug
2. `InteractiveAgent._respond_agentic` has no `hooks` parameter thread-through
3. `InteractiveAgent._respond_agentic` has no general `model_settings` on the plain (non-responses) path
4. `KnowledgeFabric` has no `fabric.pack` property (PLAT-03 - the DomainPackStore facade entry point)
5. `InteractiveAgentSpec.Skill` has no `mcp_servers` field - sub-agents built in `_build_parent_tools`
   cannot carry per-skill MCP servers despite `build_agent` accepting them
6. Security context ContextVar is repeated boilerplate in every extension - not in SDK
7. `StreamPublisher` for tool-level streaming events - not in SDK
8. `AssistantClient` for conversation history fetch - not in SDK
9. XCUT-OUTCOME-01 reference pattern: `put_case_file` already accepts `outcome=` param but no
   pack demonstrates the live production path calling it

---

## Pre-read before executing

Read these files before touching anything:
- `jazzx_sdk/agents/interactive/agent.py` - full InteractiveAgent
- `jazzx_sdk/agents/interactive/spec.py` - InteractiveAgentSpec and Skill model
- `jazzx_sdk/experts/registry.py` - ExpertRegistry with dead routes
- `jazzx_sdk/fabric/fabric.py` - KnowledgeFabric (confirm no `pack` property)
- `jazzx_sdk/fabric/canonical/store.py` - confirm DomainPackStore exists (it does)
- `jazzx_sdk/handlers.py` - HandlerContext (base for security context addition)

---

## Change 1 - Fix ExpertRegistry dead routes (live bug)

**File:** `jazzx_sdk/experts/registry.py`
**Problem:** `_get_default_expert_class` routes `evidence`, `governance`, and `investigative`
to `jazzx_sdk.experts.evidence`, `jazzx_sdk.experts.governance`, and
`jazzx_sdk.experts.investigative` - directories that now contain only `__pycache__`.
Any call to `registry.get_expert("evidence")` raises `ImportError`. These types moved to
`jazzx_sdk.skills.*` in v1.5.0 but the registry was not updated.

**Fix:** Remove the three dead routes. These Skill bases are ABCs - they cannot be
instantiated directly, so there is no "default expert" to return for them. Replace with
a clear `ValueError` that names the Skill base and tells the caller to subclass it.

```python
def _get_default_expert_class(self, expert_type: str) -> Type[BaseExpert]:
    if expert_type == "policy":
        from jazzx_sdk.experts.policy import DefaultPolicyExpert
        return DefaultPolicyExpert
    elif expert_type == "playbook":
        from jazzx_sdk.experts.playbook import DefaultPlaybookExpert
        return DefaultPlaybookExpert
    else:
        # Check if it's a skill-layer type with a helpful error
        _SKILL_TYPES = {
            "governance": "jazzx_sdk.skills.governance.BaseGovernanceSkill",
            "evidence": "jazzx_sdk.skills.evidence.BaseEvidenceSkill",
            "investigative": "jazzx_sdk.skills.investigation.BaseInvestigationSkill",
            "investigation": "jazzx_sdk.skills.investigation.BaseInvestigationSkill",
        }
        if expert_type in _SKILL_TYPES:
            raise ValueError(
                f"'{expert_type}' is a Skill type, not an Expert surface (IIF v1.5). "
                f"Subclass {_SKILL_TYPES[expert_type]} directly in your domain pack. "
                f"Use register_instance() to make it accessible from this registry if needed."
            )
        raise ValueError(
            f"Unknown expert_type: '{expert_type}'. "
            f"Valid Expert surfaces: policy, playbook. "
            f"Skill types (not auto-instantiable): governance, evidence, investigative."
        )
```

Also update the docstring on `ExpertRegistry` to remove references to `governance`,
`evidence`, and `investigative` as valid `get_expert()` targets. Update the example
in the class docstring to reflect IIF v1.5 (Skills, not Experts, for those three).

**Acceptance:**
```python
from jazzx_sdk.experts.registry import ExpertRegistry
r = ExpertRegistry(pack_id="test")
# These must raise ValueError (not ImportError)
try:
    r.get_expert("evidence")
    assert False, "should have raised"
except ValueError as e:
    assert "Skill type" in str(e)
    print("Change 1 evidence ok:", e)
try:
    r.get_expert("governance")
    assert False, "should have raised"
except ValueError as e:
    assert "Skill type" in str(e)
    print("Change 1 governance ok:", e)
# These must still work
pe = r.get_expert("policy")
print("Change 1 policy ok:", type(pe).__name__)
```

---

## Change 2 - `AgentHooks` pass-through on `InteractiveAgent`

**Files:** `jazzx_sdk/agents/interactive/agent.py`, `jazzx_sdk/agents/interactive/spec.py`
**Problem:** `_respond_agentic` calls `Runner.run(agent, input=list(messages))` with no
`hooks=` argument. `_build_parent_tools` builds sub-agents via `self._agents.openai.build_agent`
with no `hooks`. This means tool-level events are dark for every assistant surface built on
`InteractiveAgent` - no streaming breadcrumbs, no cost tracking per sub-agent.

**Fix part A:** Add `hooks: Any | None = None` to `InteractiveAgent.__init__`. Store as `self._hooks`.

```python
def __init__(
    self,
    spec: InteractiveAgentSpec,
    *,
    agents: Any,
    fabric: Any = None,
    tools: dict[str, Any] | None = None,
    guardrails: dict[str, Any] | None = None,
    skill_registry: Any = None,
    mcp_servers: dict[str, Any] | None = None,
    store: Any = None,
    reference_loader: Any = None,
    hooks: Any = None,           # <-- add this
):
    ...
    self._hooks = hooks           # <-- store it
```

**Fix part B:** Thread `self._hooks` into `build_agent` calls in `_build_parent_tools`:

```python
sub_agent = self._agents.openai.build_agent(
    name=name,
    instructions=self._skill_instructions(sdef),
    tools=sub_tools,
    model=model,
    hooks=self._hooks,      # <-- add
)
```

**Fix part C:** Thread hooks into `Runner.run` in `_respond_agentic`:

```python
async def _run_once() -> Any:
    kw = {"session": session} if session is not None else {}
    if self._hooks is not None:
        kw["hooks"] = self._hooks   # <-- add
    return await Runner.run(agent, input=list(messages), **kw)
```

Note: `build_agent` in `openai_provider.py` already accepts `hooks` - confirm this before adding
the call. If it does not, add `hooks: Any | None = None` to `build_agent`'s signature and pass it
to `Agent(... hooks=hooks ...)`. Read the current `build_agent` signature carefully first.

**Acceptance:**
```python
from jazzx_sdk.agents.interactive.agent import InteractiveAgent
import inspect
sig = inspect.signature(InteractiveAgent.__init__)
assert "hooks" in sig.parameters, "hooks param missing from __init__"
print("Change 2 ok: hooks in InteractiveAgent.__init__")
```

---

## Change 3 - `model_settings` on plain agentic path

**File:** `jazzx_sdk/agents/interactive/agent.py`
**Problem:** `_respond_agentic` applies `model_settings` only when
`pol.strategy == "responses"` (the compaction path). On all other runs, `build_kwargs` never
includes `model_settings`, so `reasoning_effort`, `verbosity`, and `service_tier` from the
caller's config have no effect even when the model supports them.

**Fix:** Accept `model_settings: Any | None = None` in `InteractiveAgent.__init__`. Store as
`self._model_settings`. In `_respond_agentic`, apply it when present AND not already overridden
by the `responses` compaction path:

```python
# In __init__:
self._model_settings = model_settings

# In _respond_agentic, after the responses block:
if not responses and self._model_settings is not None:
    build_kwargs["model_settings"] = self._model_settings
```

The responses path already sets `build_kwargs["model_settings"]` from
`model_settings_with_context_management` - do not overwrite it. The guard `if not responses` is
correct.

Also add `reasoning_effort: str | None = None` and `service_tier: str | None = None` as spec
fields on `InteractiveAgentSpec`, and build the `ModelSettings` from them when no explicit
`model_settings` object is passed to `__init__`. This lets YAML-declared profiles express these
without requiring the caller to construct `ModelSettings` manually:

```yaml
# profile.yaml
name: loan-assistant
model: gpt-5.2
reasoning_effort: high
service_tier: flex
```

In `InteractiveAgent.__init__`, if `model_settings` is None but `spec.reasoning_effort` or
`spec.service_tier` is set, build one:

```python
if model_settings is None and (spec.reasoning_effort or spec.service_tier):
    from jazzx_sdk.agents.models import build_model_settings
    model_settings = build_model_settings(
        reasoning_effort=spec.reasoning_effort,
        service_tier=spec.service_tier,
    )
self._model_settings = model_settings
```

**Spec changes in `spec.py`:**
```python
class InteractiveAgentSpec(BaseModel):
    ...
    reasoning_effort: str | None = None   # "low" | "medium" | "high" | None
    service_tier: str | None = None       # "flex" | "default" | None
```

**Acceptance:**
```python
from jazzx_sdk.agents.interactive.spec import InteractiveAgentSpec
spec = InteractiveAgentSpec(name="test", reasoning_effort="high", service_tier="flex")
assert spec.reasoning_effort == "high"
assert spec.service_tier == "flex"
print("Change 3 ok: spec fields present")
```

---

## Change 4 - `fabric.pack` property on `KnowledgeFabric`

**File:** `jazzx_sdk/fabric/fabric.py`
**Problem:** `ARCHITECTURE.md` documents `fabric.pack` as the entry point for registering and
retrieving `DomainPack` canonical objects. `DomainPackStore` exists in
`fabric/canonical/store.py` and `CanonicalObjectStore.domain_pack` exposes it. But
`KnowledgeFabric` has no `pack` property - callers must reach through
`fabric.canonical.domain_pack`, which is three levels deep and inconsistent with how other
fabric surfaces are accessed.

**Fix:** Add a `pack` property to `KnowledgeFabric` that returns the `DomainPackStore`
from `self.canonical.domain_pack`:

```python
@property
def pack(self) -> "DomainPackStore":
    """Entry point for DomainPack registration and retrieval.

    Exposes the governed DomainPack canonical store at the fabric facade level,
    so pack registration follows the same `fabric.<surface>` pattern as
    fabric.canonical, fabric.docs, fabric.graph, etc.

    Example:
        # Register a domain pack
        await ctx.runtime.fabric.pack.put(my_domain_pack)

        # Retrieve a registered pack
        pack = await ctx.runtime.fabric.pack.get("aml-investigation-core")
    """
    if self.canonical is None:
        raise KnowledgeFabricError(
            "fabric.pack requires a backing Knowledge Hub client "
            "(retrieval_mode=STRICT or CACHED)"
        )
    return self.canonical.domain_pack
```

Add `DomainPackStore` to the `TYPE_CHECKING` imports in `fabric.py`. Also export `pack` in the
`__init__.py` documentation comment so it appears in the fabric surface list.

**Acceptance:**
```python
from jazzx_sdk.fabric import local_fabric
import asyncio

async def test():
    fabric = await local_fabric()
    # pack property should exist
    assert hasattr(fabric, "pack"), "fabric.pack missing"
    # on a LOCAL fabric (Mock backing), canonical is not None
    # pack should return the DomainPackStore
    from jazzx_sdk.fabric.canonical.store import DomainPackStore
    assert isinstance(fabric.pack, DomainPackStore), f"Expected DomainPackStore, got {type(fabric.pack)}"
    print("Change 4 ok: fabric.pack returns DomainPackStore")

asyncio.run(test())
```

---

## Change 5 - `Skill.mcp_servers` on `InteractiveAgentSpec.Skill`

**File:** `jazzx_sdk/agents/interactive/spec.py`, `jazzx_sdk/agents/interactive/agent.py`
**Problem:** `InteractiveAgentSpec.Skill` has no `mcp_servers` field. Sub-agents built in
`_build_parent_tools` cannot carry per-skill MCP servers even though `build_agent` already
accepts `mcp_servers`. This matters for domain packs where different skills need different
external integrations (a credit assistant's `policy-resolver` skill needing a regulatory
database MCP; a KYC skill needing a sanctions MCP).

`InteractiveAgentSpec` has `mcp_servers` at the parent level (resolved from a catalog), but
skills have no equivalent.

**Fix part A:** Add `mcp_servers: list[str]` to `Skill` in `spec.py`:

```python
class Skill(BaseModel):
    """A named capability the agent can use — declared as data."""
    name: str
    instructions: str = ""
    description: str = ""
    tools: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    mcp_servers: list[str] = Field(default_factory=list)  # <-- add this
    # MCP server names resolved from the InteractiveAgent's mcp_servers catalog.
    # Each name must appear in the catalog passed to InteractiveAgent(mcp_servers=...).
```

**Fix part B:** Thread per-skill MCP servers into sub-agent construction in
`_build_parent_tools` in `agent.py`:

```python
sub_mcp = [self._resolve_mcp(n) for n in sdef.mcp_servers] if sdef.mcp_servers else []
sub_agent = self._agents.openai.build_agent(
    name=name,
    instructions=self._skill_instructions(sdef),
    tools=sub_tools,
    model=model,
    mcp_servers=sub_mcp if sub_mcp else [],   # <-- add
    hooks=self._hooks,
)
```

Note: Skill MCP server names are resolved from the same `self._mcp_servers` catalog as
parent-level MCP servers. A skill that names `"edgar-mcp"` uses `self._resolve_mcp("edgar-mcp")`.
No new catalog is needed.

**YAML example (in a skill definition file):**
```yaml
name: policy-resolver
description: Resolves which underwriting policies apply to a credit request
instructions: "You are the policy-resolver skill..."
tools:
  - search_policies
mcp_servers:
  - regulatory-db-mcp
```

**Acceptance:**
```python
from jazzx_sdk.agents.interactive.spec import Skill
s = Skill(name="test-skill", mcp_servers=["edgar-mcp"])
assert s.mcp_servers == ["edgar-mcp"]
print("Change 5 ok: Skill.mcp_servers present")
```

---

## Change 6 - Security context ContextVar as SDK primitive

**Files:** `jazzx_sdk/handlers.py` (or new `jazzx_sdk/context.py`), `jazzx_sdk/client_layer.py`

**Problem:** Every JAPES extension that needs to forward the security context to downstream
services (Knowledge Hub, Kernel) repeats the same pattern:

```python
# In every extension handler:
from contextvars import ContextVar
_security_context_var: ContextVar[str] = ContextVar("security_context", default="")

def _get_request_headers() -> dict[str, str]:
    sc = _security_context_var.get()
    return {"x-security-context": sc} if sc else {}
```

And then wires it manually into `ClientLayer(request_headers_provider=_get_request_headers)`.
This should be a zero-boilerplate SDK primitive.

**Fix:** Add to `jazzx_sdk/handlers.py` (keeping it co-located with `HandlerContext`):

```python
from contextvars import ContextVar

# Platform security context propagation. Extensions call set_security_context(ctx.security_context)
# at the start of handle() and the ClientLayer picks it up automatically when built via
# get_client_layer() or ClientLayer.with_security_context_propagation().
_security_context_var: ContextVar[str] = ContextVar("japes_security_context", default="")


def set_security_context(value: str | None) -> None:
    """Set the security context for the current async task.

    Call once at the top of handle() with ctx.security_context. All downstream
    KH/Kernel calls on this task will automatically forward the x-security-context header.

    Example:
        async def handle(self, ctx: HandlerContext) -> ResponseMessage:
            set_security_context(ctx.security_context)
            ...
    """
    _security_context_var.set(value or "")


def get_security_context() -> str:
    """Return the security context set for the current async task, or empty string."""
    return _security_context_var.get()


def _security_context_headers() -> dict[str, str]:
    """Header provider for ClientLayer - forwards security context when set."""
    sc = _security_context_var.get()
    return {"x-security-context": sc} if sc else {}
```

**Update `ClientLayer`** in `client_layer.py` to use `_security_context_headers` as the default
`request_headers_provider` when none is supplied by the caller:

```python
from jazzx_sdk.handlers import _security_context_headers

class ClientLayer:
    def __init__(
        self,
        *,
        ...
        request_headers_provider: Optional[Callable[[], Dict[str, str]]] = None,
        ...
    ):
        # Default to SDK security context propagation when caller doesn't supply one
        self._request_headers_provider = request_headers_provider or _security_context_headers
```

**Add to `jazzx_sdk/__init__.py` exports:**
```python
from jazzx_sdk.handlers import set_security_context, get_security_context
```

**Acceptance:**
```python
from jazzx_sdk.handlers import set_security_context, get_security_context, _security_context_headers

# Before set: empty
assert get_security_context() == ""
assert _security_context_headers() == {}

# After set: propagated
set_security_context("user-123|tenant-abc")
assert get_security_context() == "user-123|tenant-abc"
assert _security_context_headers() == {"x-security-context": "user-123|tenant-abc"}

# None clears it
set_security_context(None)
assert get_security_context() == ""
print("Change 6 ok: security context ContextVar works")
```

---

## Change 7 - `StreamPublisher` as platform primitive

**New file:** `jazzx_sdk/streaming/__init__.py` and `jazzx_sdk/streaming/publisher.py`

**Problem:** Every assistant surface that needs to stream tool-level events to the browser
(Jazz Assistant, future JACI domain assistants) must build its own Redis publisher,
`ContextVar`, and event-key convention. This should be SDK-owned infrastructure.

The pattern comes from `common.core.streaming` in the platform. JAPES wraps the key parts
without depending on `common` directly.

**New file `jazzx_sdk/streaming/publisher.py`:**

```python
"""
StreamPublisher — platform primitive for streaming tool-level events from agents.

Used by interactive agent surfaces (Jazz Assistant, JACI domain assistants) to
publish tool start/end and completion events to a Redis stream, consumed by the
UI SSE endpoint.

The publisher is async-context-aware: call set_streaming_id(id) once at the top
of handle() and all downstream publish() calls on that task use it automatically.
"""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from typing import Any

logger = logging.getLogger(__name__)

# Platform Redis key pattern for streaming: invocation:{streaming_id}
_REDIS_KEY_PREFIX = "invocation"

_streaming_id_var: ContextVar[str] = ContextVar("japes_streaming_id", default="")


def set_streaming_id(streaming_id: str | None) -> None:
    """Set the streaming ID for the current async task."""
    _streaming_id_var.set(streaming_id or "")


def get_streaming_id() -> str:
    """Return the streaming ID for the current async task, or empty string."""
    return _streaming_id_var.get()


class StreamPublisher:
    """Publish streaming events to Redis for consumption by the UI SSE endpoint.

    Usage:
        publisher = StreamPublisher(redis_client=ctx.runtime.redis)
        publisher.publish(ToolStartEvent(tool_name="get_findings", ...))

    Or with the context-based pattern:
        set_streaming_id(invocation_header.streaming_id)
        publisher = StreamPublisher.from_env()
        # all publish() calls use the context streaming_id automatically
    """

    def __init__(self, redis_client: Any, *, key_prefix: str = _REDIS_KEY_PREFIX) -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix

    @classmethod
    def from_env(cls) -> "StreamPublisher":
        """Build a publisher from environment (REDIS_URL / JAPES_REDIS_URL)."""
        import os
        import redis.asyncio as aioredis
        url = os.getenv("JAPES_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379")
        client = aioredis.from_url(url)
        return cls(client)

    def _key(self, streaming_id: str) -> str:
        return f"{self._key_prefix}:{streaming_id}"

    async def publish(self, event: dict[str, Any], streaming_id: str | None = None) -> None:
        """Publish an event dict to the stream.

        Args:
            event: Event dict. Must include a "type" field.
            streaming_id: Override; defaults to the ContextVar set by set_streaming_id().
        """
        sid = streaming_id or get_streaming_id()
        if not sid:
            logger.debug("StreamPublisher.publish: no streaming_id, event dropped: %s", event.get("type"))
            return
        try:
            await self._redis.rpush(self._key(sid), json.dumps(event))
        except Exception as e:
            logger.warning("StreamPublisher.publish failed (non-fatal): %s", e)


# Canonical event builders for tool-level streaming
def tool_start_event(tool_name: str, invocation_id: str | None = None) -> dict[str, Any]:
    return {"type": "tool_start", "tool_name": tool_name, "invocation_id": invocation_id}


def tool_end_event(tool_name: str, invocation_id: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {"type": "tool_end", "tool_name": tool_name, "invocation_id": invocation_id, "error": error}


def done_event(answer: str, citations: list[dict] | None = None) -> dict[str, Any]:
    return {"type": "done", "answer": answer, "citations": citations or []}
```

**New file `jazzx_sdk/streaming/__init__.py`:**

```python
"""Platform streaming primitives for interactive agent surfaces."""

from jazzx_sdk.streaming.publisher import (
    StreamPublisher,
    set_streaming_id,
    get_streaming_id,
    tool_start_event,
    tool_end_event,
    done_event,
)

__all__ = [
    "StreamPublisher",
    "set_streaming_id",
    "get_streaming_id",
    "tool_start_event",
    "tool_end_event",
    "done_event",
]
```

**Add `redis` as an optional dependency** in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
...
redis = {version = ">=5.0.0", extras = ["asyncio"], optional = true}

[tool.poetry.extras]
...
streaming = ["redis"]
```

**Note:** The publisher gracefully degrades when no streaming_id is set - it logs and skips.
This means extensions that do not need streaming can import and use the publisher without
any Redis dependency being required.

**Acceptance:**
```python
from jazzx_sdk.streaming import set_streaming_id, get_streaming_id, tool_start_event, done_event

set_streaming_id("inv-12345")
assert get_streaming_id() == "inv-12345"
evt = tool_start_event("get_findings")
assert evt["type"] == "tool_start"
assert evt["tool_name"] == "get_findings"
evt2 = done_event("The loan was approved.", citations=[{"type": "finding", "id": "f1"}])
assert evt2["type"] == "done"
print("Change 7 ok: streaming primitives work")
```

---

## Change 8 - `AssistantClient` in `jazzx_sdk/clients/`

**New file:** `jazzx_sdk/clients/assistant_client.py`

**Problem:** Every conversational assistant built on JAPES needs to fetch prior conversation
turns from the JazzX assistant API, forwarding the security context and trimming to a session
budget. Jazz Assistant's planned `assistant_client.py` is the first instance - KYC, CI, CRE
domain assistants will need the same. This is cross-cutting infrastructure.

**New file `jazzx_sdk/clients/assistant_client.py`:**

```python
"""
AssistantClient — fetches conversation history from the JazzX Assistant API.

Used by interactive agent surfaces (Jazz Assistant, JACI domain assistants) to
retrieve prior turns for conversation-aware grounded Q&A.

All network calls forward the security context via the platform header provider.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AssistantClient:
    """Fetch conversation history from the JazzX Assistant API.

    Args:
        base_url: Assistant API base URL (e.g. "https://api.jazzx.ai")
        request_headers_provider: Callable returning headers to forward
            (defaults to SDK security context propagation).
        max_session_size_kb: Trim conversation history to this size in KB.
            Messages are dropped from the oldest end. 0 means no limit.
        timeout: HTTP timeout in seconds.

    Example:
        client = AssistantClient(base_url=os.getenv("ASSISTANT_API_URL"))
        messages, question = await client.get_session(conversation_id, latest_message_id)
    """

    def __init__(
        self,
        base_url: str,
        *,
        request_headers_provider=None,
        max_session_size_kb: int = 128,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._max_size_bytes = max_session_size_kb * 1024 if max_session_size_kb > 0 else 0
        self._timeout = timeout
        if request_headers_provider is None:
            from jazzx_sdk.handlers import _security_context_headers
            request_headers_provider = _security_context_headers
        self._headers_provider = request_headers_provider

    def _headers(self) -> dict[str, str]:
        base = {"Content-Type": "application/json", "Accept": "application/json"}
        base.update(self._headers_provider())
        return base

    async def get_messages(
        self, conversation_id: str, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Fetch messages for a conversation, newest-first.

        Args:
            conversation_id: The conversation to fetch.
            limit: Maximum messages to return.

        Returns:
            List of message dicts with role and content, newest-first.
        """
        url = f"{self._base_url}/api/v1/conversations/{conversation_id}/messages"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers(), params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
            return data.get("messages", []) if isinstance(data, dict) else data

    async def get_session(
        self,
        conversation_id: str,
        latest_message_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        """Fetch session history and extract the latest user question.

        Returns:
            (messages, question): messages trimmed to max_session_size_kb in
            OpenAI chat format (oldest first, excluding latest user turn);
            question is the latest user message content.
        """
        raw = await self.get_messages(conversation_id)
        # raw is newest-first; reverse for processing
        messages = list(reversed(raw))

        # Extract the latest user turn as the question
        question = ""
        history = []
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if msg.get("role") == "user":
                question = msg.get("content", "")
                history = messages[:i]  # everything before it is history
                break

        # Convert to OpenAI chat format
        chat_history = [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in history
        ]

        # Trim to session budget
        if self._max_size_bytes > 0:
            chat_history = self._trim(chat_history)

        return chat_history, question

    def _trim(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Drop oldest messages until total size is within budget."""
        import json
        while messages:
            size = len(json.dumps(messages).encode("utf-8"))
            if size <= self._max_size_bytes:
                break
            messages = messages[1:]
        return messages
```

**Update `jazzx_sdk/clients/__init__.py`** to export `AssistantClient`.

**Acceptance:**
```python
from jazzx_sdk.clients.assistant_client import AssistantClient
import inspect
sig = inspect.signature(AssistantClient.__init__)
assert "conversation_id" in inspect.signature(AssistantClient.get_session).parameters
assert "max_session_size_kb" in sig.parameters
print("Change 8 ok: AssistantClient importable with correct signature")
```

---

## Change 9 - XCUT-OUTCOME-01: Document the live Outcome-linkage pattern

**Problem:** `put_case_file` already accepts an `outcome=` parameter and the store is wired.
But no pack demonstrates calling it in the live production path. The AML `japes_handler.py`
calls `put_case_file` without `outcome=`. The pattern needs a documented reference in the
JAPES SDK docs so every scenario can copy it.

This is documentation and a helper, not a code change. The goal is to make outcome-linkage
the path of least resistance.

**Fix part A:** Add a `Outcome.from_context` classmethod to
`jazzx_sdk/fabric/canonical/outcome.py` as a parallel to AML's
`Outcome.from_case_file`. This generic helper creates a linkage-correct `Outcome`
from any completed investigation or transaction context:

```python
@classmethod
def from_context(
    cls,
    *,
    decision_id: str,
    trace_id: str,
    pack_id: str,
    outcome_type: str = "case_completion",
    subject_id: str = "",
    domain_extensions: dict | None = None,
) -> "Outcome":
    """Create a linkage-correct Outcome from a completed conductor run.

    Args:
        decision_id: The CanonicalDecision.decision_id for this run.
        trace_id: The CanonicalTrace.trace_id for this run.
        pack_id: Domain Pack identifier (e.g. "aml-investigation-core").
        outcome_type: Outcome category (default "case_completion").
        subject_id: The primary entity this run was about (loan_id, alert_id, etc.)
        domain_extensions: Pack-specific outcome data.

    Returns:
        Outcome with decision_id and trace_id cross-linkage populated.
    """
    from uuid import uuid4
    return cls(
        outcome_id=f"outcome_{uuid4()}",
        outcome_type=outcome_type,
        decision_id=decision_id,
        trace_id=trace_id,
        pack_id=pack_id,
        subject_id=subject_id,
        domain_extensions=domain_extensions or {},
    )
```

Read `jazzx_sdk/fabric/canonical/outcome.py` before adding this to confirm the field names
and existing classmethods. Do not duplicate any existing `from_case_file` or `from_context`
method.

**Fix part B:** Add a `TRACING_AND_OUTCOME_GUIDE.md` to `docs/`:

```markdown
# Outcome Linkage in JAPES - The Reference Pattern

Every conductor run MUST create and persist an Outcome via put_case_file.
This closes the compounding loop: Decisions linked to Outcomes feed EVOLVE.

## Minimal correct pattern (in your Conductor.run() or handler):

```python
from jazzx_sdk.fabric.canonical.outcome import Outcome

# 1. Build the canonical objects (your existing code)
decision = CanonicalDecision.from_pack(...)
trace = CanonicalTrace.for_pack(...)

# 2. Persist Decision and Trace
entity_ids = await fabric.canonical.put_case_file(
    case_file=case_file,
    ontology_id=ONTOLOGY_ID,
    # outcome= is absent here intentionally - add it when the result is known
)

# 3. Create the Outcome (at case completion - immediately for automated decisions,
#    after human review for escalated cases)
outcome = Outcome.from_context(
    decision_id=decision.decision_id,
    trace_id=trace.trace_id,
    pack_id=PACK_ID,
    subject_id=alert_id,  # or loan_id, customer_id, etc.
    domain_extensions={"disposition": "ESCALATE", "sar_filed": True},
)

# 4. Persist the Outcome linked to the Decision and Trace
await fabric.canonical.put_outcome(outcome, ontology_id=ONTOLOGY_ID)
```

**Why this matters:** Outcomes are the compounding loop entry point. Without an Outcome
linked to every Decision, the EVOLVE layer has no signal to learn from. Gold cases need
an Outcome to validate against. The evaluation harness measures outcome alignment.
```

**Acceptance:** Confirm `Outcome.from_context` is importable and callable:

```python
from jazzx_sdk.fabric.canonical.outcome import Outcome
o = Outcome.from_context(
    decision_id="dec_123",
    trace_id="trace_456",
    pack_id="test-pack",
    subject_id="loan_789",
)
assert o.decision_id == "dec_123"
assert o.trace_id == "trace_456"
print("Change 9 ok: Outcome.from_context works:", o.outcome_id)
```

---

## Execution order

Execute in this order. Each change is independent but ordered by blast radius and test
dependencies:

1. **Change 1** - ExpertRegistry dead routes (bug fix, highest urgency, no dependencies)
2. **Change 4** - `fabric.pack` property (small, additive, no dependencies)
3. **Change 2** - `hooks` on InteractiveAgent (requires reading `build_agent` signature first)
4. **Change 3** - `model_settings` + spec fields (depends on Change 2 being done first)
5. **Change 5** - `Skill.mcp_servers` (depends on Change 2 for the hooks threading)
6. **Change 6** - Security context ContextVar (additive to `handlers.py`)
7. **Change 7** - `StreamPublisher` (new module, no dependencies)
8. **Change 8** - `AssistantClient` (new file in `clients/`, depends on Change 6 for headers)
9. **Change 9** - Outcome.from_context + guide (read `outcome.py` first, check existing methods)

---

## Smoke test sequence

Run after all changes:

```bash
cd /Users/sangit/src/japes && source /Users/sangit/src/jaci/.venv/bin/activate

python -c "
# Change 1: ExpertRegistry dead routes
from jazzx_sdk.experts.registry import ExpertRegistry
r = ExpertRegistry(pack_id='test')
try:
    r.get_expert('evidence')
    print('FAIL: should have raised ValueError')
except ValueError as e:
    assert 'Skill type' in str(e), f'Wrong error: {e}'
    print('C1 ok: evidence raises ValueError with Skill hint')
try:
    r.get_expert('governance')
    print('FAIL: should have raised ValueError')
except ValueError as e:
    assert 'Skill type' in str(e)
    print('C1 ok: governance raises ValueError with Skill hint')
pe = r.get_expert('policy')
print('C1 ok: policy still works:', type(pe).__name__)
"

python -c "
# Change 2: hooks on InteractiveAgent
import inspect
from jazzx_sdk.agents.interactive.agent import InteractiveAgent
sig = inspect.signature(InteractiveAgent.__init__)
assert 'hooks' in sig.parameters, 'hooks missing from __init__'
print('C2 ok: hooks in InteractiveAgent.__init__')
"

python -c "
# Change 3: model_settings / spec fields
from jazzx_sdk.agents.interactive.spec import InteractiveAgentSpec
spec = InteractiveAgentSpec(name='test', reasoning_effort='high', service_tier='flex')
assert spec.reasoning_effort == 'high'
assert spec.service_tier == 'flex'
print('C3 ok: spec fields present')
"

python -c "
# Change 4: fabric.pack
import asyncio
from jazzx_sdk.fabric import local_fabric
from jazzx_sdk.fabric.canonical.store import DomainPackStore

async def test():
    fabric = await local_fabric()
    assert hasattr(fabric, 'pack'), 'fabric.pack missing'
    assert isinstance(fabric.pack, DomainPackStore), f'Wrong type: {type(fabric.pack)}'
    print('C4 ok: fabric.pack returns DomainPackStore')

asyncio.run(test())
"

python -c "
# Change 5: Skill.mcp_servers
from jazzx_sdk.agents.interactive.spec import Skill
s = Skill(name='test-skill', mcp_servers=['edgar-mcp'])
assert s.mcp_servers == ['edgar-mcp']
print('C5 ok: Skill.mcp_servers present')
"

python -c "
# Change 6: security context ContextVar
from jazzx_sdk.handlers import set_security_context, get_security_context, _security_context_headers
assert get_security_context() == ''
assert _security_context_headers() == {}
set_security_context('user-123|tenant-abc')
assert get_security_context() == 'user-123|tenant-abc'
assert _security_context_headers() == {'x-security-context': 'user-123|tenant-abc'}
set_security_context(None)
assert get_security_context() == ''
print('C6 ok: security context ContextVar works')
"

python -c "
# Change 7: StreamPublisher
from jazzx_sdk.streaming import set_streaming_id, get_streaming_id, tool_start_event, done_event
set_streaming_id('inv-12345')
assert get_streaming_id() == 'inv-12345'
evt = tool_start_event('get_findings')
assert evt['type'] == 'tool_start' and evt['tool_name'] == 'get_findings'
evt2 = done_event('answer text', citations=[{'type': 'finding', 'id': 'f1'}])
assert evt2['type'] == 'done'
print('C7 ok: streaming primitives work')
"

python -c "
# Change 8: AssistantClient
from jazzx_sdk.clients.assistant_client import AssistantClient
import inspect
sig = inspect.signature(AssistantClient.__init__)
assert 'max_session_size_kb' in sig.parameters
assert 'get_session' in dir(AssistantClient)
print('C8 ok: AssistantClient importable with correct interface')
"

python -c "
# Change 9: Outcome.from_context
from jazzx_sdk.fabric.canonical.outcome import Outcome
o = Outcome.from_context(
    decision_id='dec_123',
    trace_id='trace_456',
    pack_id='test-pack',
    subject_id='loan_789',
)
assert o.decision_id == 'dec_123'
assert o.trace_id == 'trace_456'
print('C9 ok: Outcome.from_context works:', o.outcome_id)
"

python -c "
# Full import smoke test
import jazzx_sdk
import jazzx_sdk.agents.interactive
import jazzx_sdk.streaming
import jazzx_sdk.clients.assistant_client
import jazzx_sdk.experts
import jazzx_sdk.skills
import jazzx_sdk.fabric
print('All imports clean')
"
```

---

## Version bump

After all changes pass smoke tests, bump `_version.py` and `pyproject.toml` to `2.0.0`.

Update `CHANGELOG.md` with entries for each change above.

---

## What this plan does NOT address

The following items are tracked in `plan_II_drift_audit_2026-06-07.md` and remain for
separate work. They are out of scope here because they require scenario-side changes,
not SDK changes:

- AML live outcome linkage in `japes_handler.py` (AML-01) - scenario work
- CanonicalTrace/TraceStep emission in any scenario (AML-02) - scenario work
- Pack registration in any scenario (AML-04, SCN-*) - scenario work
- `use_mocks=True` production defaults in scenario ToolRegistries (XCUT-FABRIC-01) - scenario work
- Policy externalization in any scenario (SCN-CRE-02, SCN-KYC-04) - scenario work
- PLAT-02 (v1.5 manifest version fields on DomainPack) - still open, separate plan needed
- `fabric.pack` YAML-driven init / Pack Studio integration - future work
- Discovery/DiscoveryExpert placement in Automation surface - separate plan needed
- `TraceEmitter` / `V1 trace events` from Juno - separate plan, needs design alignment
