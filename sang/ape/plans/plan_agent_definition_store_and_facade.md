# AgentDefinitionStore + a unified "invoke agent by name" facade

**Status:** scoped, not started

## Context

Investigating a jazzx-assistant report on a broken `KernelClient.invoke_agent()` surfaced kernel's
own agent model (`app/agent/models.py`'s `AgentCreate`/`Agent` table): a persisted, named,
CRUD-able registry of agent definitions (prompt, model, tools, autonomy tier, sub-agent handoffs,
resumable plan/step execution) — something japes has no equivalent of. `InteractiveAgentSpec`
(`jazzx_sdk/agents/interactive/spec.py`) is japes's declarative agent definition, but it's
constructed in Python at pack-load time; there's no persisted, name-keyed store behind it, and no
single call site that can invoke an agent by name without the caller already knowing whether it's
kernel-hosted or japes-native.

Checked field-by-field: most of kernel's columns aren't new capability japes lacks — they're
kernel's own reinvention of things japes (v2) already has more general primitives for:

| Kernel `AgentCreate` field | japes-native equivalent |
|---|---|
| `name` | `InteractiveAgentSpec.name` |
| `agent_prompt` | `InteractiveAgentSpec.persona` |
| `llm_id` (FK) | `InteractiveAgentSpec.model` |
| `max_steps` | `InteractiveAgentSpec.max_turns` |
| `tools` (kernel `ToolDirectory`) | `InteractiveAgentSpec.skills`/`skill_defs` |
| `mcp_servers` | `InteractiveAgentSpec.mcp_servers` (same name, already there) |
| `temperature` / `reasoning_effort` | same fields, already on `InteractiveAgentSpec` |
| existing-`Plan`/`Step` resume | `SuspensionStore`/`DurableSuspension` (shipped this session — a *better* primitive: claim-fenced, no double-execution risk kernel's plan-resume doesn't guard against) |
| `autonomy` (4-tier enum) | japes's Authority Matrix / execution profile (2.0.0) |
| `callable_agent_ids` (sub-agent handoff) | OpenAI Agents SDK `Handoff` (already what `AgentExecutionService` sits on) |
| `input_schema`/`output_schema` (JSON-schema strings) | `AgentExecutionService.run(output_schema=SomeBaseModel)` — typed, not stringified |
| `learning_strategy`/`use_feedback` | japes's compounding-loop / `Feedback` / `optimize_prompt` |

The one real gap: **no persisted, named registry of agent definitions**, and **no single facade
that invokes an agent by name without the caller pre-knowing its backend.**

## Part 1 — `AgentDefinitionStore`

Mirrors the exact shape already shipped twice this session (`TurnRunStore`/`DbTurnRunStore`,
`SuspensionStore`/`DbSuspensionStore`): a protocol + `InProcessAgentDefinitionStore` (dev/tests) +
`DbAgentDefinitionStore` on `fabric.db` (lazy-imported, not re-exported by default — same
SQLAlchemy-opt-in split). Each consuming service instantiates it against **its own** Postgres via
`fabric.db` — not kernel's database (that would be reaching into another service's tables behind
its own API, the exact coupling `fabric`'s HTTP-facade pattern exists to avoid) and not a new
shared central "japes db" (contradicts the established `fabric.db`-per-service pattern).

```python
class AgentDefinition(BaseModel):
    name: str                          # the registry key
    backend: Literal["kernel", "japes"]
    spec: InteractiveAgentSpec | None = None      # set when backend == "japes"
    kernel_agent_id: UUID | None = None           # set when backend == "kernel"
    created_at / updated_at: datetime

class AgentDefinitionStore(Protocol):
    async def get(self, name: str) -> AgentDefinition | None: ...
    async def put(self, definition: AgentDefinition) -> AgentDefinition: ...
    async def list(self) -> list[AgentDefinition]: ...
    async def delete(self, name: str) -> None: ...
```

No claim/heartbeat/reap needed here (unlike `TurnRunStore`/`SuspensionStore`) — this is a plain
name-keyed registry, not a concurrent-execution primitive; reuse `NamedRegistry`'s conventions for
the in-process variant where they fit, but it doesn't need that class's exact shape either.

## Part 2 — the facade

**Where it lives**: extend `AgentExecutionService` (`ctx.runtime.agents`, already the platform's
one entry point for agent execution) with a name-based path, rather than inventing a new
`fabric.agents` namespace. `fabric.*` is established for HTTP-domain-service/infra access
(KH, db, blob, policy) — agent execution already has its own established entry point; growing
that is more consistent than adding a second one.

```python
async def AgentExecutionService.invoke(
    self, name: str, input_text: str, **kwargs
) -> AgentResult:
    definition = await self._registry.get(name)
    if definition is None:
        raise ValueError(f"no agent named {name!r}")
    if definition.backend == "kernel":
        result = await self._kernel_client.invoke_agent(name, input_text, **kwargs)
        return AgentResult(output=result["output"], raw_response=result,
                           trace=None, provider="kernel", model=None)
    return await self._run_from_spec(definition.spec, input_text, **kwargs)  # existing local path
```

Kernel-hosted agents stay intentionally opaque behind this — `KernelClient.invoke_agent()` (already
fixed) does the resolve/invoke/poll/fetch dance; the facade doesn't try to mirror kernel's internal
plan/step state, only its name and result.

## Part 3 — the mapping path (this is what makes it more than routing)

Because the field mapping above is close to 1:1, a **kernel → japes import** becomes a real,
mechanical translation, not a re-design per agent:

```python
async def import_from_kernel(kernel_client: KernelClient, agent_name: str) -> InteractiveAgentSpec:
    """Fetch a kernel agent's definition and translate it into an InteractiveAgentSpec, using the
    field mapping above. Best-effort on fields with no direct equivalent yet (autonomy, handoffs) —
    logged, not silently dropped."""
```

This is the concrete migration lever: a kernel-hosted agent can be inspected, translated, and
registered in `AgentDefinitionStore` as a `backend="japes"` definition — turning "we're pulling
kernel functionality into japes" from a one-off rewrite (like `invoke_agent()`'s fix) into a
repeatable path per agent.

## Explicitly open, not solved by this plan

- **Autonomy mapping**: japes's Authority Matrix and kernel's 4-tier `autonomy` enum aren't the
  same shape yet — `import_from_kernel` needs an explicit (documented, not silently approximated)
  mapping decision before it can round-trip this field.
- **Handoffs mapping**: translating `callable_agent_ids` into Agents-SDK `Handoff` objects requires
  the *target* agents to already be resolvable (kernel IDs or japes names) — a chicken/egg import
  ordering question for agents that reference each other.
- **Should a kernel-hosted definition also get a shadow record in `AgentDefinitionStore`** (for
  `list()`/discovery), or does the facade call `KernelClient` live on every lookup? Leaning shadow
  record with a cache/refresh policy, but not settled here.

## Tests (when implemented)

- `AgentDefinitionStore` (InProcess + Db): put/get/list/delete round-trip.
- `AgentExecutionService.invoke()` dispatches to `KernelClient` for a `backend="kernel"` definition
  and to the existing local run path for `backend="japes"`; raises on an unknown name.
- `import_from_kernel` translates a fake `AgentRead`-shaped object through the mapping table into
  the expected `InteractiveAgentSpec` fields; a field with no mapping (autonomy/handoffs) is
  reported, not silently dropped.

## Verification

1. New unit tests above, run alongside `tests/test_kernel_client_invoke_agent.py` and whatever the
   `InteractiveAgentSpec`/`AgentExecutionService` test files are (confirm names at implementation
   time) — no regressions.
2. Manually invoke both a kernel-backed and a japes-backed definition through the same
   `agents.invoke(name, ...)` call and confirm identical `AgentResult` shape either way.
