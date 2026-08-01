# plan_JAPES_2_5_0_INVOCATION_AUTHORIZATION

Author: Virendra Mehta · 2026-07-30 · Grounded against japes 2.2.2 (`jazzx_sdk/_version.py`)

## TLDR

A user's request is currently treated as a series of independent hops. Identity propagates, but
authorization does not. `capture_identity_headers` / `set_propagated_headers` in
`jazzx_sdk/handlers.py` carry *who* the caller is across the async-dispatch boundary; nothing carries
*what they may reach*, and no hop between an assistant turn and a downstream tool call re-checks.

This plan introduces `InvocationContext` — one authorization context, cascaded — and a check at every
hop from assistant turn to skill sub-agent to tool to conductor step. ABA §7.4 non-bypass invariants
are the normative spec. It is the only item in the Unified Assistant Framework concept note that is
genuinely new architecture rather than packaging over an existing primitive.

**The design must be canonical-independent.** Mortgage has not adopted the Institutional Charter and
may never. If it has no decision classes, it has no `AuthorityMatrixV2`, so a cascade built on the
matrix would leave the largest production surface unprotected. Build on permission scope, which every
caller has, and treat the matrix as an additional narrowing layer when a pack is bound.

## Landed state (verified)

| Primitive | Location | Relevance |
|---|---|---|
| `check_action` | `jazzx_sdk/authority/resolver.py` | Returns `EffectiveAuthority \| Refusal`. Already handles `OUT_OF_SCOPE` / `AUTHORITY_EXCEEDED` / `HUMAN_ONLY_ACTION` / `PRECONDITION_FAILED` |
| `resolve_effective_autonomy` | same | Most-restrictive intersection over cell / `SurfaceBinding` / `ClientOverlay` / `ExecutionProfile` / runtime downgrades, with `contributing_layers` recording why |
| Existing `check_action` call sites | `agents/document/agent.py`, `automation/governed.py`, `modes/operational/governor.py`, `statemachine/engine.py` | Four hops already governed. `agents/interactive/` is the hole |
| Identity propagation | `jazzx_sdk/handlers.py` — `_security_context_var`, `_propagated_headers_var`, `capture_identity_headers`, `set_propagated_headers` | The ContextVar pattern and the async-task-boundary problem are already solved here. Reuse, do not reinvent |
| `Refusal` / `RefusalClass` | `jazzx_sdk/fabric/canonical/refusal.py` | A refusal is a recordable outcome, never an exception |
| `TraceStepContextHelper` | `jazzx_sdk/fabric/canonical/trace.py` | Where a denial gets recorded |

## Design intent

**One context, cascaded top to bottom.** The context is established once at the entry hop and every
downstream call inherits it. Nothing may escalate in the middle. A hop that reaches outside the
context is refused, not silently narrowed.

**Two tiers, one mechanism.** Tier one is permission scope: a principal, an actor class, and a set of
resource selectors the request may reach. Always present, always checked. Tier two is the authority
matrix, checked additionally when the bound manifest resolves a pack. A plain assistant gets tier one
and nothing about it feels degraded; a charter-governed assistant gets both.

**Fail closed on absence of context, fail open on absence of a matrix.** Missing `InvocationContext`
at a hop that requires one is a bug and must raise. A missing matrix is a legitimate plain-tier
configuration and must not.

**Denial is an outcome.** Every refused hop emits a `TraceStep` and returns a typed `Refusal`. A
denial that leaves no trace is worse than no check, because it is unauditable.

---

## Phase 1 — `InvocationContext` and propagation

**New file:** `jazzx_sdk/authority/context.py`

```python
class InvocationContext(BaseModel):
    principal_ref: str                       # who
    actor_class: str                         # the actor_class check_action already expects
    permission_scope: PermissionScope        # what may be reached (tier one)
    human_initiated: bool = False            # feeds check_action's existing kwarg
    matrix: AuthorityMatrixV2 | None = None  # tier two, when a pack is bound
    binding: SurfaceBinding | None = None
    overlay: ClientOverlay | None = None
    execution_profile: ExecutionProfile | None = None
    trace_id: str | None = None
    depth: int = 0                           # hop count, for loop detection and trace legibility


class PermissionScope(BaseModel):
    resource_selectors: list[str]            # opaque to the SDK; a pack or host defines the grammar
    denied_selectors: list[str] = Field(default_factory=list)

    def admits(self, selector: str) -> bool: ...
    def narrow(self, selectors: list[str]) -> "PermissionScope": ...   # intersect, never widen
```

`resource_selectors` stays opaque deliberately. The SDK must not learn what a loan id or a
collection id is. `admits` does prefix and exact matching over strings; a host that needs richer
semantics supplies its own `PermissionScope` subclass.

Propagation mirrors `handlers.py` exactly:

```python
_invocation_context_var: ContextVar[InvocationContext | None] = ContextVar(
    "japes_invocation_context", default=None
)

def set_invocation_context(ctx: InvocationContext | None) -> Token: ...
def get_invocation_context() -> InvocationContext | None: ...
def require_invocation_context() -> InvocationContext: ...   # raises if absent
```

Add capture and restore around the dispatched turn in `ResilientRunner` (`jazzx_sdk/runs/runner.py`,
class at line 25), at the same anchor where `capture_identity_headers` and `set_propagated_headers`
already bracket execution — `create_run` captures, `execute` restores.
The 2.2.2 changelog entry records that identity silently dropped across that boundary and juno #242
hit it live — the context will drop the same way if it is not captured at the same point.

**Acceptance checks** (`tests/test_invocation_context.py`, new):

```python
def test_context_survives_async_task_boundary()      # the juno #242 shape, for context not headers
def test_require_raises_when_absent()
def test_narrow_intersects_and_never_widens()
def test_denied_selectors_win_over_allowed()
def test_depth_increments_per_hop()
```

---

## Phase 2 — The hop check

**New in** `jazzx_sdk/authority/context.py`:

```python
def check_hop(
    selector: str,
    *,
    cell_id: str | None = None,
    evidence_types_present: Iterable[str] | None = None,
) -> EffectiveAuthority | Refusal: ...
```

Reads the context from the ContextVar. Order:

1. `permission_scope.admits(selector)` — on failure return
   `Refusal(reason_class=AUTHORITY_EXCEEDED)` naming the selector. Always runs.
2. If `cell_id` and `ctx.matrix` are both present, delegate to the existing `check_action`, passing
   `ctx.actor_class`, `ctx.binding`, `ctx.overlay`, `ctx.execution_profile`, and
   `ctx.human_initiated`. Do not reimplement any of its logic.
3. If no matrix, return an `EffectiveAuthority` carrying the surface ceiling with
   `contributing_layers={"permission_scope": ...}` so a plain-tier trace still shows why the hop was
   admitted.

Every `Refusal` path emits a `TraceStep` via `TraceStepContextHelper` before returning.

**Acceptance checks** (`tests/test_authority_hop.py`, new):

```python
def test_hop_refuses_selector_outside_scope()
def test_hop_admits_without_matrix()                    # plain tier, no degradation
def test_hop_delegates_to_check_action_with_matrix()    # assert on call args, not reimplemented logic
def test_hop_emits_tracestep_on_denial()
def test_hop_raises_without_context()
```

---

## Phase 3 — Wire the interactive path

The four existing `check_action` call sites keep working unchanged. This phase adds the missing
ones, all in `jazzx_sdk/agents/interactive/`.

| Hop | Anchor | Selector |
|---|---|---|
| Turn entry | `agent.py` `respond` and the streaming variant, alongside the existing input-guardrail call | the assistant's own `assistant_id` |
| Skill sub-agent invocation | where `skill_defs` become `as_tool` sub-agents | `skill:<name>` |
| Direct tool call | the tool catalog resolution path | `tool:<name>` |
| Knowledge binding | `knowledge.py`, per `KnowledgeBinding` resolution | `canonical:<type>` or `docs:<collection>` |

Each hop narrows before descending: a skill sub-agent runs with a context narrowed to that skill's
declared `tools` and `references`, so a sub-agent cannot reach a tool its own skill definition did
not declare even if the parent could. This is the invariant that makes the cascade meaningful rather
than decorative.

A refused hop returns the `Refusal` to the parent as a tool result, not an exception. The parent
model sees "that was refused and why" and can answer around it — matching how the four existing
governed call sites already behave.

**Acceptance checks** (`tests/test_interactive_authorization.py`, new):

```python
def test_turn_refused_when_assistant_outside_scope()
def test_subagent_cannot_reach_tool_outside_its_skill_definition()   # the core invariant
def test_subagent_context_is_narrower_than_parent()
def test_refusal_returns_as_tool_result_not_exception()
def test_knowledge_binding_refused_outside_scope()
def test_no_context_configured_leaves_existing_behavior_unchanged()  # regression, opt-in
```

That last check is load-bearing. Every existing caller that never sets an `InvocationContext` must
behave exactly as it does today. This lands as opt-in and becomes mandatory in a later version, once
jazzx-assistant and juno have both adopted it.

---

## Phase 4 — Conductor and sub-agent continuation

Extend the cascade past the interactive boundary so a skill that invokes a conductor pipeline, and a
pipeline step that invokes a sub-agent, both inherit the same context.

`statemachine/engine.py` and `automation/governed.py` already call `check_action` with an explicit
matrix and actor class. Change them to prefer the ambient `InvocationContext` when present and fall
back to their current explicit arguments when not. No behavior change for existing callers.

**Acceptance checks** (extend `tests/test_authority.py`):

```python
def test_statemachine_prefers_ambient_context()
def test_statemachine_falls_back_to_explicit_args()
def test_context_survives_assistant_to_skill_to_conductor_to_subagent()   # the end-to-end shape
```

---

## Sequencing and exit criteria

Strictly ordered: 1 gates 2 gates 3 gates 4.

Exit: a request entering at an assistant turn cannot reach any resource outside its originating
permission scope at any depth, every denial is on the trace with the layer that produced it, and a
caller that sets no context sees byte-identical behavior to 2.4.0.

## Open questions for the executor to surface, not resolve

- Whether `PermissionScope.resource_selectors` should be a pack-supplied grammar rather than opaque
  strings. Opaque is the right v1 because it keeps the SDK domain-free, but the first real pack will
  pressure it.
- Where `human_initiated` is authoritatively set. Phase 4 of the 2.4.0 plan parks it on the bound
  spec for `AUTOMATION` surfaces; the permanent home is probably the entry hop that constructs the
  context, which means the host sets it, which means it is spoofable by a compromised host. Worth a
  decision before this ships.
- Whether a refused hop should count against `max_turns`. Currently it would.

## Notes for the executor

- Read `docs/status/CHANGELOG.md` first. This plan assumes 2.4.0 has landed.
- `jazzx_sdk/authority/` is named for pure logic, not governance — the module docstring in
  `resolver.py` explains the naming choice against `skills/governance`. Keep new code there pure and
  free of I/O.
- Do not add a top-level import from `authority/` into `agents/interactive/` without checking the
  cycle: `fabric/canonical/authority.py` and `fabric/canonical/profiles.py` both import from
  `manifest/`, and `authority/resolver.py` imports from both. The four existing `check_action`
  callers all import lazily inside the function. Follow that.
