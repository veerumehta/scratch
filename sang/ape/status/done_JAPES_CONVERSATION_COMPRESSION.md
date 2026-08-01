# plan_JAPES_1_8_6_CONVERSATION_COMPRESSION.md

**Author:** Virendra Mehta  
**JAPES target version:** 1.8.6 (implemented in **1.9.4**, 2026-06-23)  
**Status:** ✅ Implemented — `CompressionConfig` + `compression` field (spec.py), `_apply_compression`/`_SlidingWindowStore` (agent.py), exports, tests (`tests/test_compression_config.py`). Two tightenings vs the plan: the `keep_recent < max_messages` check is scoped to `strategy="summarize"` only (meaningless for `drop`); the `_SlidingWindowStore` unbounded-storage caveat is in its docstring.  

---

## TLDR

`InteractiveAgentSpec` gets a declarative `compression` block. `InteractiveAgent.__init__` reads it and auto-wires `CompactingMemoryStore` or a sliding-window drop store around whatever `MemoryStore` the caller passes. Callers stop hand-constructing compression wrappers. Pack authors configure compression in YAML.

No new public classes. No breaking changes to existing call sites. `memory: "none"` and bare `memory: "session"` (no compression block) remain valid and behave identically to today.

---

## What does NOT change

- `MemoryStore`, `InMemoryStore`, `CompactingMemoryStore`, `llm_summarizer` — no modifications
- `InteractiveAgent.respond()` signature — unchanged
- `AgentExecutionService`, `OpenAIProvider`, `AnthropicProvider` — not touched
- `run_kit.InputFilter` and `strip_session` — not touched
- Any JACI pack code — not touched
- Schema Specification canonical objects — not touched

---

## Changes required

### 1. `jazzx_sdk/agents/interactive/spec.py`

Add a `CompressionConfig` model and wire it into `InteractiveAgentSpec`.

**Add after the `KnowledgeBinding` class:**

```python
class CompressionConfig(BaseModel):
    """Declarative compression policy for session memory.

    strategy:
        "summarize"  — CompactingMemoryStore (LLM summarizes oldest turns). Default when
                       a compression block is present.
        "drop"       — Sliding window: keep the last ``keep_recent`` turns, discard older
                       ones without summarization.

    trigger:
        "count"      — fire when len(history) > max_messages
        "char_budget" — fire when total char length > max_chars
        "both"       — fire when either threshold is exceeded (default)

    Fields:
        strategy      "summarize" | "drop"          default "summarize"
        trigger       "count" | "char_budget" | "both"  default "both"
        max_messages  int                            default 20
        keep_recent   int                            default 6
        max_chars     int | None                     default 40_000 (None = no char limit)
        model         str | None                     model for summarization LLM call;
                                                     None = agent-execution default (cheapest
                                                     capable model is recommended)
    """

    strategy: str = "summarize"       # "summarize" | "drop"
    trigger: str = "both"             # "count" | "char_budget" | "both"
    max_messages: int = 20
    keep_recent: int = 6
    max_chars: int | None = 40_000
    model: str | None = None

    @model_validator(mode="after")
    def _validate(self) -> "CompressionConfig":
        if self.strategy not in ("summarize", "drop"):
            raise ValueError(f"compression.strategy must be 'summarize' or 'drop', got {self.strategy!r}")
        if self.trigger not in ("count", "char_budget", "both"):
            raise ValueError(f"compression.trigger must be 'count', 'char_budget', or 'both', got {self.trigger!r}")
        if self.keep_recent + 1 >= self.max_messages:
            raise ValueError("compression.keep_recent + 1 must be < max_messages")
        return self
```

**Add import at top of file** (alongside existing imports):
```python
from pydantic import BaseModel, Field, model_validator
```
(replace existing `from pydantic import BaseModel, Field` if present)

**Add field to `InteractiveAgentSpec`** (after the `memory` field):
```python
    memory: str = "none"                      # none | session
    compression: CompressionConfig | None = None  # None = no compression
    stream: bool = False
```

**Export `CompressionConfig` from `__init__.py`** — see section 4.

---

### 2. `jazzx_sdk/agents/interactive/agent.py`

`InteractiveAgent.__init__` reads `spec.compression` and wraps the caller-supplied `memory` store automatically. The caller never needs to touch `CompactingMemoryStore` directly.

**Replace the `__init__` body's memory assignment line:**

Current:
```python
        self._memory = memory
```

Replace with:
```python
        self._memory = _apply_compression(spec, memory, agents)
```

**Add this module-level helper** (after the imports, before the class):

```python
def _apply_compression(
    spec: "InteractiveAgentSpec",
    memory: Any,
    agents: Any,
) -> Any:
    """Wrap ``memory`` with the compression policy declared in ``spec``.

    - No compression block, or memory is None/none -> return as-is.
    - strategy="summarize" -> CompactingMemoryStore via llm_summarizer.
    - strategy="drop"      -> _SlidingWindowStore wrapper.
    """
    from jazzx_sdk.agents.interactive.memory import (
        CompactingMemoryStore,
        InMemoryStore,
        llm_summarizer,
    )

    if spec.compression is None or spec.memory == "none":
        return memory

    cfg = spec.compression
    store = memory if memory is not None else InMemoryStore()

    if cfg.strategy == "summarize":
        summarizer = llm_summarizer(agents, model=cfg.model)
        max_chars = cfg.max_chars if cfg.trigger in ("char_budget", "both") else None
        max_messages = cfg.max_messages if cfg.trigger in ("count", "both") else 10_000
        return CompactingMemoryStore(
            store,
            summarizer,
            max_messages=max_messages,
            keep_recent=cfg.keep_recent,
            max_chars=max_chars,
        )

    if cfg.strategy == "drop":
        return _SlidingWindowStore(store, keep=cfg.keep_recent)

    return store  # unreachable after validator, but safe
```

**Add `_SlidingWindowStore`** (after `_apply_compression`, still module-level):

```python
class _SlidingWindowStore:
    """Thin drop wrapper: keeps the last ``keep`` turns, silently discards older ones.

    Not exported — internal to the agent wiring. Implements the MemoryStore interface
    without subclassing (duck-typed) to avoid a circular import.
    """

    def __init__(self, store: Any, *, keep: int) -> None:
        self._store = store
        self._keep = keep

    async def load(self, session_id: str) -> list[dict]:
        history = await self._store.load(session_id)
        return history[-self._keep:] if len(history) > self._keep else history

    async def append(self, session_id: str, messages: list[dict]) -> None:
        await self._store.append(session_id, messages)
        history = await self._store.load(session_id)
        if len(history) > self._keep:
            excess = history[: -self._keep]
            # Re-write: clear and rewrite only the window.
            # Only possible if the backing store supports clear().
            if hasattr(self._store, "clear"):
                await self._store.clear(session_id)
                await self._store.append(session_id, history[-self._keep:])
            # If the store has no clear(), load() already slices — we accept the
            # storage waste and let the caller use a compacting-capable store.

    async def clear(self, session_id: str) -> None:
        if hasattr(self._store, "clear"):
            await self._store.clear(session_id)
```

**Add import at top of `agent.py`** (if not already there):
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jazzx_sdk.agents.interactive.spec import InteractiveAgentSpec
```

---

### 3. `jazzx_sdk/agents/interactive/memory.py`

**No changes.** `CompactingMemoryStore` already supports both `max_messages` and `max_chars`; `_apply_compression` passes the right values based on the trigger policy.

---

### 4. `jazzx_sdk/agents/interactive/__init__.py`

Add `CompressionConfig` to exports:

```python
from jazzx_sdk.agents.interactive.spec import (
    InteractiveAgentSpec,
    KnowledgeBinding,
    Skill,
    CompressionConfig,          # <-- add
)

__all__ = [
    ...
    "CompressionConfig",        # <-- add
    ...
]
```

---

## YAML usage (pack authors)

After this change, a profile YAML can declare compression without any Python:

```yaml
# profiles/juno/profile.yaml
name: juno
persona: persona.md
memory: session
compression:
  strategy: summarize
  trigger: both
  max_messages: 30
  keep_recent: 8
  max_chars: 60000
  model: gpt-4o-mini
```

Drop-only (no LLM call, cheapest):
```yaml
compression:
  strategy: drop
  keep_recent: 10
```

No compression (existing behavior, explicit):
```yaml
memory: session
# no compression block
```

---

## Call-site migration

Existing callers that hand-wire `CompactingMemoryStore` today continue to work — they pass an already-wrapped store and set no `compression` block in the spec, so `_apply_compression` returns the store as-is. No forced migration.

New callers should let the spec drive it:

```python
# Before (caller-side wiring)
summarizer = llm_summarizer(ctx.runtime.agents, model="gpt-4o-mini")
store = CompactingMemoryStore(InMemoryStore(), summarizer, max_messages=20, keep_recent=6)
agent = InteractiveAgent(spec, agents=ctx.runtime.agents, fabric=ctx.runtime.fabric, memory=store)

# After (spec-driven)
# spec.yaml has the compression block; caller just passes InMemoryStore or nothing
agent = InteractiveAgent(spec, agents=ctx.runtime.agents, fabric=ctx.runtime.fabric)
```

---

## Acceptance checks

```bash
# 1. Schema validation round-trips
python - <<'EOF'
from jazzx_sdk.agents.interactive import InteractiveAgentSpec, CompressionConfig

# summarize + both trigger
s = InteractiveAgentSpec.from_dict({
    "name": "test", "memory": "session",
    "compression": {"strategy": "summarize", "trigger": "both",
                    "max_messages": 20, "keep_recent": 6, "max_chars": 40000}
})
assert s.compression.strategy == "summarize"

# drop strategy
s2 = InteractiveAgentSpec.from_dict({
    "name": "test2", "memory": "session",
    "compression": {"strategy": "drop", "keep_recent": 8}
})
assert s2.compression.strategy == "drop"

# no compression block — backward compat
s3 = InteractiveAgentSpec.from_dict({"name": "test3", "memory": "session"})
assert s3.compression is None

print("schema: OK")
EOF

# 2. Validator rejects bad inputs
python - <<'EOF'
from pydantic import ValidationError
from jazzx_sdk.agents.interactive import InteractiveAgentSpec
try:
    InteractiveAgentSpec.from_dict({
        "name": "bad", "memory": "session",
        "compression": {"strategy": "rag"}    # invalid
    })
    assert False, "should have raised"
except ValidationError:
    pass
try:
    InteractiveAgentSpec.from_dict({
        "name": "bad2", "memory": "session",
        "compression": {"keep_recent": 20, "max_messages": 20}  # keep >= max
    })
    assert False, "should have raised"
except ValidationError:
    pass
print("validation: OK")
EOF

# 3. _apply_compression returns CompactingMemoryStore for summarize strategy
python - <<'EOF'
import asyncio
from unittest.mock import AsyncMock, MagicMock
from jazzx_sdk.agents.interactive.spec import InteractiveAgentSpec, CompressionConfig
from jazzx_sdk.agents.interactive.memory import CompactingMemoryStore
from jazzx_sdk.agents.interactive.agent import _apply_compression

spec = InteractiveAgentSpec(name="t", memory="session",
    compression=CompressionConfig(strategy="summarize"))
mock_agents = MagicMock()
mock_agents.run = AsyncMock(return_value=MagicMock(output="summary"))
result = _apply_compression(spec, None, mock_agents)
assert isinstance(result, CompactingMemoryStore), f"got {type(result)}"
print("wiring: OK")
EOF

# 4. Existing tests still pass
cd /Users/sangit/src/japes && python -m pytest tests/agents/ -q --tb=short
```

---

## File change table

| File | Change type | Description |
|---|---|---|
| `jazzx_sdk/agents/interactive/spec.py` | Modify | Add `CompressionConfig` model; add `compression` field to `InteractiveAgentSpec` |
| `jazzx_sdk/agents/interactive/agent.py` | Modify | Add `_apply_compression` helper and `_SlidingWindowStore`; wire in `__init__` |
| `jazzx_sdk/agents/interactive/__init__.py` | Modify | Export `CompressionConfig` |
| `jazzx_sdk/agents/interactive/memory.py` | None | No changes |
| Any JACI pack file | None | No changes |
