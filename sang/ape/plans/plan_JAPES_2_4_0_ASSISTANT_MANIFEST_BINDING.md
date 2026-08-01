# plan_JAPES_2_4_0_ASSISTANT_MANIFEST_BINDING

Author: Virendra Mehta · 2026-07-30 · Grounded against japes 2.2.2 (`jazzx_sdk/_version.py`)

## TLDR

Every primitive the Unified Assistant Framework concept note asks for already exists in the SDK.
None of them are wired to the interactive runtime. `AssistantManifest` is imported by exactly two
places: the `jazzx_sdk/__init__.py` re-export and `tests/test_assistant_primitives.py`. `check_action`
is called from `agents/document/agent.py`, `automation/governed.py`, `modes/operational/governor.py`,
and `statemachine/engine.py` — never from `agents/interactive/`. So `manifest.autonomy_level`,
`in_scope_action_classes`, `out_of_scope_action_classes`, `integration_surface`, and
`governance_profile_ref` are all declared and inert.

This plan closes the wire. Four phases, no new architecture: a fail-closed bridge from manifest to
spec, `router` as a declared field, a stock scope guardrail built from the manifest, and a surface
defaults table. Per-hop authorization is deliberately out of scope — see
`plan_JAPES_2_5_0_INVOCATION_AUTHORIZATION.md`.

## Landed state (verified, do not rebuild)

| Primitive | Location | State |
|---|---|---|
| `AssistantManifest` | `jazzx_sdk/manifest/assistant_manifest.py` | Structural model, 44 lines. Has `pack_id`, `pack_version_range`, `allowed_skills`, `in_scope_action_classes`, `out_of_scope_action_classes`, `autonomy_level`, `integration_surface`, `governance_profile_ref`, `archetype_type`, `primary_persona` |
| `load_manifest` / `resolve_pack` | `jazzx_sdk/manifest/loader.py` | Sync load with fail-fast skill resolution; opt-in async pack version-range check against `DomainPackStore` |
| `AutonomyLevel` | `jazzx_sdk/manifest/autonomy.py` | Five-member ladder with pinned legacy alias migration |
| `SurfaceType` | `jazzx_sdk/manifest/surface_types.py` | Five members. Declaration only, module docstring says so explicitly |
| `check_action` / `resolve_effective_autonomy` | `jazzx_sdk/authority/resolver.py` | Returns `EffectiveAuthority \| Refusal`; narrowing over cell / `SurfaceBinding` / `ClientOverlay` / `ExecutionProfile` |
| `Refusal` / `RefusalClass` | `jazzx_sdk/fabric/canonical/refusal.py` | Typed taxonomy incl. `OUT_OF_SCOPE`; `RefusalRegistry` for pack reason codes |
| `InteractiveAgentSpec` | `jazzx_sdk/agents/interactive/spec.py` | `from_dir` / `from_yaml` / `from_dict`; skills, guardrails, compaction, guidance, streaming |
| `SkillRegistry` / `ProfileRegistry` / `GuardrailRegistry` | `jazzx_sdk/agents/interactive/registry.py` | On `NamedRegistry`; `ProfileRegistry.validate` already cross-checks skills and guardrail phases |
| `with_safety` | `jazzx_sdk/agents/interactive/safety.py` | Domain-neutral prompt fragment. Prompt text, not an enforced gate |
| `build_interactive_agent` | `jazzx_sdk/agents/interactive/factory.py` | Spec-level one-call factory, 40 lines |

## Design intent

**The manifest and the spec stay separate objects.** The manifest is the governed, pack-bound,
certifiable outer artifact. The spec is runtime configuration. Merging them would put pack binding
and autonomy into every scripted test spec, and would make `ProfileRegistry` meaningless. The
relationship is narrowing, per ABA §1 operational narrowing order: the manifest narrows a profile,
never widens it.

**Widening is a certification violation and must fail closed.** If a profile's `spec.skills`
contains a name absent from `manifest.allowed_skills`, that is a governance breach, not a warning.
`from_dir` already warns on the inverse case (skill file present but not in the allow-list) at
`spec.py` in `InteractiveAgentSpec.from_dir` — follow that precedent for logging, but raise here.

**Do not rename `spec.scope`.** It means "required invocation params" (`spec.py`,
`InteractiveAgentSpec.scope`) and is a different concept from the manifest's topic boundary. Renaming
breaks every existing profile. New code uses `action_classes` and never the word "scope" for the
topic boundary.

---

## Phase 1 — Manifest to spec bridge

**New file:** `jazzx_sdk/manifest/spec_binding.py`

Named `spec_binding`, not `binding`, because `jazzx_sdk/agents/interactive/binding.py` already exists
and means something unrelated (`ConversationBinding`, the Agents-SDK session adapter). Two files
named `binding.py` would be a standing source of confusion.

**Change to** `jazzx_sdk/manifest/assistant_manifest.py`: add one field to `AssistantManifest`.

```python
profile_ref: str | None = None   # InteractiveAgentSpec name in a ProfileRegistry; None -> assistant_id
```

Optional with an `assistant_id` fallback so no existing manifest or test fixture breaks.

**Signatures:**

```python
def bind_spec(
    manifest: AssistantManifest,
    profile: InteractiveAgentSpec,
    *,
    skill_registry: SkillRegistry,
) -> InteractiveAgentSpec: ...

def build_from_manifest(
    manifest: AssistantManifest,
    *,
    profiles: ProfileRegistry,
    skill_registry: SkillRegistry,
    **extra: Any,
) -> InteractiveAgent: ...
```

`bind_spec` returns a narrowed copy via `model_copy(update=...)`, matching how
`InvocationConfig.apply_to` already produces a derived spec in `spec.py`. It must:

1. Raise `ValueError` listing every offender if `set(profile.skills) - set(manifest.allowed_skills)`
   is non-empty. Message names the manifest's `assistant_id` and the unauthorized skills, mirroring
   the wording style of the unresolved-skills raise in `loader.load_manifest`.
2. Intersect `skills` to `manifest.allowed_skills`. **If the intersection is empty while
   `profile.skills` was non-empty, raise — never return the narrowed spec.** `agent.py:208` uses
   `if self.spec.skills:` as the switch between two entirely different execution paths: non-empty
   runs the agentic Runner loop with sub-agents and tools, empty runs a single-shot call with no
   tools at all. A narrowing that empties `skills` would silently downgrade the agent to single-shot
   rather than refusing it, which is the worst possible failure — it looks like it worked. The
   error message must say that explicitly so the next reader doesn't "fix" it by allowing the
   empty case.
3. Apply the surface defaults table from Phase 4.
4. Attach the scope guardrail name from Phase 3 to `spec.guardrails["input"]`.
5. Leave `persona`, `model`, `knowledge`, `compaction`, and `guidance_*` untouched — those are
   profile concerns the manifest has no opinion on.

`build_from_manifest` resolves `profile_ref or assistant_id` against `profiles`, calls `bind_spec`,
then delegates to `build_interactive_agent` in `agents/interactive/factory.py`. Import
`build_interactive_agent` lazily inside the function; `jazzx_sdk/manifest/` must not acquire a
module-level dependency on `agents/`, since `fabric/canonical/authority.py` and
`fabric/canonical/profiles.py` both already import from `manifest/` and a top-level back-edge would
cycle.

**Acceptance checks** (`tests/test_assistant_manifest_binding.py`, new):

```python
def test_bind_spec_refuses_widening()          # profile skill outside allowed_skills -> ValueError naming it
def test_bind_spec_refuses_narrowing_to_empty()  # would silently flip agentic -> single-shot (agent.py:208)
def test_bind_spec_narrows_skills()            # result.skills == intersection, order stable
def test_bind_spec_preserves_profile_fields()  # persona/model/knowledge/compaction unchanged
def test_build_from_manifest_falls_back_to_assistant_id()   # profile_ref None
def test_manifest_module_has_no_toplevel_agents_import()    # assert on module source, guards the cycle
```

---

## Phase 2 — Router as a declared field

Today skill selection is implicit: skills with a definition become sub-agents exposed to the parent
via the `as_tool` pattern (`spec.py`, `Skill` docstring), and the parent model picks. That is one
routing policy presented as the only possibility. Name it, then allow a second.

**Change to** `jazzx_sdk/agents/interactive/spec.py`: add to `InteractiveAgentSpec`, adjacent to
`skills` / `skill_defs`.

```python
router: str = "default_llm"   # resolved against the router registry at wire time
```

**New file:** `jazzx_sdk/agents/interactive/router.py`

Follow the extensibility pattern `CompactionPolicy.strategy` already uses: a registry, resolution at
wire time not parse time, unknown name raises at agent construction. `CompactionPolicy._validate`
in `spec.py` documents this choice — do not enum-check `router` on the model.

```python
class Router(Protocol):
    async def select(
        self, query: str, history: list[dict], catalog: SkillRegistry, allowed: list[str]
    ) -> list[str] | None: ...

def register_router(name: str, router: Router) -> None: ...
```

Two built-ins:

- `default_llm` — returns `None`, meaning "no pre-selection, let the parent model choose". Exactly
  today's behavior. Registering it as a named default is what makes the field non-breaking.
- `intent_first` — one classifier call returning skill names, `None` on low confidence so the
  parent model handles the ambiguous tail. This is the concept note's August "intent detection as a
  lightweight first-pass" item, and it belongs here rather than in an app.

`InteractiveAgent` consumes the result in the agentic path by filtering which sub-agent tools are
exposed for the turn. A `None` return must produce a byte-identical tool set to today.

**Acceptance checks** (`tests/test_interactive_router.py`, new):

```python
def test_default_llm_router_is_noop()          # tool catalog identical with and without the field set
def test_unknown_router_raises_at_construction()   # not at spec parse
def test_intent_first_narrows_exposed_tools()
def test_intent_first_none_falls_back_to_full_catalog()
```

---

## Phase 3 — Stock scope guardrail from the manifest

`in_scope_action_classes` and `out_of_scope_action_classes` are the topic boundary as data. Nothing
reads them. Meanwhile `with_safety` in `safety.py` carries "**Stay in scope.** If a request falls
outside what you handle, decline briefly and plainly" as prompt text, which is advisory. Every
assistant that needs a real boundary writes its own classifier — jazzx-assistant did exactly that.

**New file:** `jazzx_sdk/agents/interactive/scope.py`

```python
def build_scope_guardrail(
    in_scope: list[str], out_of_scope: list[str], *, model: str | None = None
) -> Guardrail: ...

SCOPE_GUARDRAIL_NAME = "manifest_scope"
```

Returns a `Guardrail` (the dataclass in `registry.py` carrying a check and its phase) with
`phase="input"`. Phase 1's `bind_spec` registers it under `SCOPE_GUARDRAIL_NAME` and prepends the
name to `spec.guardrails["input"]`, so a manifest-built agent inherits the boundary without
declaring it. A profile that already declares the name keeps its position — do not double-register.

Follow the gate pattern the SDK already documents rather than inventing one. "Building Agents using
jazzx-sdk" §Shape A describes a classifier plus an output guardrail that maps a verdict to a policy
decision with a pure function — one LLM round-trip for both the classification and the decision,
and it records that this is exactly how jazzx-assistant's own safety gate works. The scope guardrail
is that pattern with the manifest's action classes supplying the boundary instead of hand-written
prose.

**Change to** `jazzx_sdk/agents/interactive/agent.py`: `_run_guardrails` currently returns
`str | None`. Extend the accepted return type of a guardrail check to `str | Refusal | None`, and
have `_run_guardrails` return the `Refusal.message` while stashing the typed `Refusal` for the
caller. Keep the existing `str` behavior intact — this is additive.

Note that `(text) -> str | None` is now a **publicly documented** contract, not just an internal
one. Widening it is safe; narrowing it later would not be. Update the doc page in the same change.

The typed `Refusal` matters because `RefusalClass.OUT_OF_SCOPE` already exists and
`DEFAULT_HTTP_STATUS` already maps it to 422. An out-of-scope refusal should be the same auditable
object the authority path produces, not a bare string. The refusal-is-an-outcome-not-an-exception
principle is stated at the top of `fabric/canonical/refusal.py`; honor it here.

**Acceptance checks** (`tests/test_interactive_scope.py`, new):

```python
def test_scope_guardrail_blocks_out_of_scope_class()
def test_scope_guardrail_admits_in_scope_class()
def test_bind_spec_attaches_scope_guardrail()
def test_bind_spec_does_not_double_register_declared_guardrail()
def test_run_guardrails_accepts_refusal_return()      # message surfaces, Refusal retrievable
def test_run_guardrails_str_return_unchanged()        # regression
```

---

## Phase 4 — Surface defaults table

`manifest.integration_surface` is inert. Its module docstring in `surface_types.py` is explicit that
no dispatch logic lives there, which is correct for the enum but leaves the field meaningless at
runtime. Give it behavior at bind time rather than building new runtime paths.

**In** `jazzx_sdk/manifest/spec_binding.py`, a module-level table applied by `bind_spec`:

| `SurfaceType` | `conversation` | `stream_tool_events` |
|---|---|---|
| `WORKSPACE` | True *(store required, see below)* | True |
| `ASSISTANT` | True *(store required, see below)* | True |
| `API_SERVICE` | False | False |
| `AUTOMATION` | False | False |
| `GATEWAY` | unchanged | unchanged |

Defaults only. A profile that sets these explicitly wins — this is a floor for profiles that say
nothing, not an override. `GATEWAY` is dispatch-only and must not have opinions imposed on it.

**`conversation: True` is inert on its own and must not be set blindly.** `_conversation_active`
(`agent.py:334`) returns `self.spec.conversation and self._store is not None and bool(session_id)`.
Setting the flag without a `store=` on the constructor and a `session_id=` on every `respond()` buys
nothing and reads as if memory is on. So `bind_spec` sets `conversation=True` for `WORKSPACE` /
`ASSISTANT` only when a store is being supplied, and otherwise leaves it False and logs at warning
naming both missing pieces. A conversational surface with no memory should be loud, not silent.

**`stream=True` conflicts with structured output.** `respond_stream()` cannot produce a typed
reply; the streaming-plus-structured combination is served by `respond()` with
`stream_tool_events=True`. The defaults table therefore sets `stream_tool_events=True` for the two
interactive surfaces and leaves `stream` alone — `spec.stream` is advisory (a UI capability flag),
and the caller decides which method to invoke. Do not set `stream=True` here.

`AUTOMATION` additionally records `human_initiated=False` on the bound spec for Phase 2 of the
authorization plan to consume. Carry it as a private attribute or a `model_config` extra now; the
authorization plan defines where it lands permanently.

**Acceptance checks** (extend `tests/test_assistant_manifest_binding.py`):

```python
def test_surface_defaults_applied_per_type()
def test_explicit_profile_setting_wins_over_surface_default()
def test_gateway_surface_leaves_flags_untouched()
def test_conversation_not_enabled_without_store()      # flag stays False, warning names store + session_id
def test_surface_defaults_never_set_stream()           # stream is advisory; respond_stream can't do structured
```

---

## Sequencing and exit criteria

Phase 1 gates 3 and 4 (both extend `bind_spec`). Phase 2 is independent and can land in parallel.

Exit: a YAML manifest plus a profile folder produces a running, scope-bounded, skill-narrowed
`InteractiveAgent` through one call, with no handler code.

Demonstrate against `examples/loan_assistant/` rather than authoring a new fixture. It already
carries a `profile/` folder and a `harness.py`, so a manifest laid over it proves the binding on a
profile that exists independently of this plan — a stronger check than a fixture written to pass.
`tests/test_interactive_agent.py` (51 tests) is the regression surface; all must stay green, since
Phase 3 touches `_run_guardrails` and Phase 2 touches tool-catalog assembly.

## Out of scope

Per-hop authorization, canonical object emission from a turn, Governor on the interactive path,
memory scopes, multi-principal sessions, promoting `SkillRegistry` to a resolvable service. The
first is `plan_JAPES_2_5_0_INVOCATION_AUTHORIZATION.md`. The rest are deferred with named triggers:
canonical emission and Governor at the first charter-governed pack surface (CRE / CL / AML), the
registry service at first BYOF or cross-version skill demand.

## Notes for the executor

- `docs/status/CHANGELOG.md` is authoritative for landed state. Read it before assuming any phase
  here is still open.
- The `[Unreleased]` section currently carries 2.3.0 finance work. Add these entries beneath it
  without disturbing that block.
- Bump `jazzx_sdk/_version.py` and `pyproject.toml` together; `tests/test_version_sync.py` asserts
  they match.
