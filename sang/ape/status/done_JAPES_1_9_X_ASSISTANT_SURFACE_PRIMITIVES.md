# JAPES 1.9.x: Assistant Surface Primitives

Author: Virendra Mehta
Status: Draft for discussion
Repos affected: `japes/`

## Why this plan exists

Platform 2.0's Single Assistant Framework proposal (Kunal Patel, June 29 2026) asks for a declarative Assistant Manifest, platform-level RBAC at a single invocation gateway, autonomy levels with HITL enforcement, and shared trace/evaluation across all assistant surfaces. JAPES already has the canonical chain, the Expert/Skill split, and an Assistant Binding Annex template that cover most of this. What's missing is a small set of concrete SDK primitives that would let JAPES be the place this converges, independent of whether the broader framework proposal proceeds. This plan scopes four additions, each useful on its own to JACI and to any future Assistant Manifest format.

Confirmed against current code (jazzx_sdk v1.9.6), corrected after Claude Code review of the first draft:
- No `AssistantManifest` model exists anywhere in `jazzx_sdk/`.
- No `AutonomyLevel` enum exists in the SDK. There is no "Advisory only (L0)" prose in `experts/discovery/*.py` to migrate; the earlier draft's claim there was wrong. The enum is purely additive, with no existing call sites to update.
- `gate_fns` already exists. It is an `EvaluationHarness.__init__` parameter (`runner.py`), applied in `_run_single_case`: each `gate_fn(case_file)` records a `gate.<name>` score on `CaseResult`, and any gate failure zeros `gates_passed`. This is documented at `results.py` and covered by `test_compliance_additions.py`. The real gap is narrower than the first draft claimed: the signature takes `case_file` only, with no role/claims input.
- No typed surface type exists for a pure dispatch/gateway layer. Current surface language is prose only (`experts/README.md`, `base.py`: "assistants, workspaces, APIs"), not an enum.

## What this plan does NOT change

- Does not commit JAPES to adopting or rejecting the Platform 2.0 Single Assistant Framework proposal.
- Does not touch `ExpertRegistry`, `BaseExpert`, or the Expert/Skill distinction settled in IIF v1.5.
- Does not change any existing JACI scenario code (ci_spread, AML, KYC).
- Does not introduce RBAC, Keycloak, or Ory Keto integration. Role/claims pass-through is scoped as an input shape only, not an identity system, and is inert until something actually sources claims into the harness call.
- Does not implement the Automation/Gateway surface runtime, only the surface type declaration.
- Does not modify the existing `gate_fn(case_file)` call sites; the claims parameter is added as optional so existing gate functions keep working unchanged.

## Phase 1: AssistantManifest model

**Goal:** a validated, declarative manifest format that resolves skill and domain pack references at load time and fails fast, per the ABA fields already in use.

Design correction from the first draft: reference resolution cannot live in a `model_validator` on the Pydantic model itself. `SkillRegistry` is an instance (`NamedRegistry[Skill]`), not a global singleton, and pack resolution needs a fabric-backed store handle. A bare model validator has access to neither. The model stays structural-only; resolution is the loader's job, with registries passed in explicitly.

New file: `jazzx_sdk/manifest/assistant_manifest.py`

```python
from enum import Enum
from pydantic import BaseModel, Field

class ArchetypeType(str, Enum):
    SPECIALIST = "specialist"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"
    ANALYST = "analyst"
    MANAGER = "manager"
    FILING_ASSISTANT = "filing_assistant"
    MONITOR = "monitor"

class AssistantManifest(BaseModel):
    assistant_id: str
    archetype_type: ArchetypeType
    pack_id: str
    pack_version_range: str
    primary_persona: str
    allowed_skills: list[str] = Field(default_factory=list)
    in_scope_action_classes: list[str] = Field(default_factory=list)
    out_of_scope_action_classes: list[str] = Field(default_factory=list)
    autonomy_level: "AutonomyLevel"
    governance_profile_ref: str | None = None
    # structural only — no reference resolution here, see loader.py
```

New file: `jazzx_sdk/manifest/loader.py`

```python
def load_manifest(
    path: Path,
    skill_registry: "SkillRegistry",
) -> AssistantManifest:
    """Load and structurally validate a manifest, with fail-fast skill
    resolution against the injected SkillRegistry. Sync; no I/O beyond
    reading the file. Raises ValueError on the first unresolved skill ref."""
    ...

async def resolve_pack(
    manifest: "AssistantManifest",
    pack_store: "DomainPackStore",
) -> "DomainPack | None":
    """Opt-in async pack-existence check when a fabric is present.
    Returns None if pack_id is not found in KH, or if the pack's version
    does not satisfy manifest.pack_version_range (logs a warning in both
    cases). Consistent with DomainPackStore.get() and the rest of the
    store layer, which return None on miss rather than raise.
    Callers own the null-check and decide how to handle a missing pack."""
    ...
```

Per-file changes:

| File | Change |
|---|---|
| `jazzx_sdk/manifest/__init__.py` | new, exports `AssistantManifest`, `ArchetypeType` |
| `jazzx_sdk/manifest/assistant_manifest.py` | new, structural Pydantic model only, no validator |
| `jazzx_sdk/manifest/loader.py` | new, `load_manifest(path, skill_registry) -> AssistantManifest` (sync, skill fail-fast) and `async resolve_pack(manifest, pack_store) -> DomainPack | None` (opt-in, returns None on miss or version mismatch) |
| `jazzx_sdk/__init__.py` | export `AssistantManifest` at top level |

Acceptance tests:
- `load_manifest` given a manifest referencing a nonexistent skill raises `ValueError` at load time, not at first invocation.
- A bare `AssistantManifest(**data)` construction with an unresolvable skill ref succeeds (structural validation only); resolution failure only surfaces through `load_manifest`.
- `resolve_pack` returns `None` (not raise) when pack_id is absent from KH.
- `resolve_pack` returns `None` (not raise) when pack is found but its version does not satisfy `pack_version_range`; a warning is logged in both cases, consistent with `DomainPackStore.get()` and the rest of the store layer.

## Phase 2: Unified AutonomyLevel

**Goal:** one enum, referenced by the manifest and (later) the Governor. This phase is now purely additive: no existing code references autonomy levels in a form this enum replaces, so there are no migration edits.

New file: `jazzx_sdk/manifest/autonomy.py`

```python
from enum import Enum

class AutonomyLevel(str, Enum):
    L0_ADVISORY = "l0_advisory"        # propose only, no execution
    L1_DRAFT = "l1_draft"              # may draft, human releases
    L2_APPROVAL = "l2_approval"        # may execute with required approval
    L3_AUTONOMOUS = "l3_autonomous"    # may execute, post-hoc review only
```

Per-file changes:

| File | Change |
|---|---|
| `jazzx_sdk/manifest/autonomy.py` | new |

No edits to `experts/discovery/*.py` or any other existing file. The enum exists so `AssistantManifest.autonomy_level` and any future Governor work have one canonical type to reference, rather than retrofitting prose that doesn't currently exist.

## Phase 3: claims parameter on the existing gate_fn signature

**Goal:** the hard-gate mechanism already shipped for ComplianceBench (`EvaluationHarness(gate_fns=...)`, `_run_single_case`, `gate.<name>` scores in `CaseResult`) gets an optional claims input, so a future role-aware gate can compose with the Authority Matrix gate instead of RBAC running as a fully separate system. This is a reframe of the existing mechanism, not new infrastructure.

Per-file changes:

| File | Change |
|---|---|
| `jazzx_sdk/evaluation/harness/runner.py` | in `_run_single_case`, change the gate call from `gate_fn(case_file)` to `gate_fn(case_file, claims=None)` for any gate fn that accepts the second parameter; existing single-arg gate fns continue to work unchanged (call via `inspect.signature` check or a try/except TypeError fallback) |
| `jazzx_sdk/evaluation/harness/config.py` | no change; `gate_fns` already lives on `EvaluationHarness.__init__`, not on the Pydantic `EvaluationConfig`, correctly, since a `Callable` doesn't belong on a serializable config |

Gate function signature:

```python
GateFn = Callable[["CaseFile"], bool] | Callable[["CaseFile", dict | None], bool]
```

This phase does not implement Keycloak/Ory Keto integration and does not source claims from anywhere real yet; the parameter is inert until a caller passes one. It only shapes the signature so that addition won't be a breaking change later.

## Phase 4: Automation/Gateway surface type declaration

**Goal:** name the fourth surface type implied by "single invocation gateway" so it doesn't get invented independently by the mortgage app, Juno, or any SI partner.

Per-file changes:

| File | Change |
|---|---|
| `jazzx_sdk/manifest/surface_types.py` | new, `SurfaceType` enum: `WORKSPACE`, `API_SERVICE`, `AUTOMATION`, `GATEWAY` |
| `jazzx_sdk/manifest/assistant_manifest.py` | `AssistantManifest.integration_surface: SurfaceType` field |
| `jazzx_sdk/experts/README.md` | update "assistants, workspaces, APIs" prose to align with the typed `SurfaceType` vocabulary (`WORKSPACE`, `API_SERVICE`, `AUTOMATION`, `GATEWAY`) so prose and enum don't drift |

This phase is a declaration only. No dispatch logic, no Keycloak call, no Process Engine routing. It exists so the manifest can describe a gateway-bound assistant without requiring the gateway itself to exist yet in this repo.

## Sequencing

Phase 2 and Phase 4 are clean and independent; both can land first with no open design questions. Phase 3 is a small, low-risk signature extension to existing, tested code. Phase 1 depends on Phase 2 (for `AutonomyLevel`) and should land after the loader-based resolution design is confirmed, since the original model-validator approach in the first draft does not work and needs the loader-injection design above signed off before implementation.

Recommended order: Phase 2, Phase 4, Phase 3, then Phase 1.

## Acceptance checks

```bash
# Phase 2 (done)
python -c "from jazzx_sdk.manifest.autonomy import AutonomyLevel; assert AutonomyLevel.L0_ADVISORY"

# Phase 4 (done)
python -c "from jazzx_sdk.manifest.surface_types import SurfaceType; assert SurfaceType.GATEWAY"

# Phase 3 (done)
grep "gate_claims" jazzx_sdk/evaluation/harness/runner.py
grep "_call_gate" jazzx_sdk/evaluation/harness/runner.py

# Phase 1 (pending)
python -c "from jazzx_sdk.manifest import AssistantManifest, ArchetypeType"
python -c "from jazzx_sdk.manifest.loader import load_manifest, resolve_pack"
```

## Open questions for execution

- Does the ABA template (jaci-side) get migrated to *be* an `AssistantManifest` instance, or does it stay a human-authored worksheet that compiles down to one? Recommend the latter for now, keep SME-facing authoring separate from the machine-validated artifact.
- `gate_claims` on the harness is inert until something sources real claims into the call. Whether that source is ever in scope for JAPES, or permanently Platform 2.0 gateway territory, is an open product decision; it does not affect Phase 1 implementation.

## Resolved decisions

- `AssistantManifest` lives under `jazzx_sdk/manifest/` (spans Experts, Skills, and pack refs, not Experts-only).
- `resolve_pack` returns `None` on miss or version mismatch, consistent with `DomainPackStore.get()` and the store layer convention throughout `fabric/canonical/store.py`; no typed exception hierarchy.
- `load_manifest` is sync, skill-check only; `resolve_pack` is the separate async opt-in step for pack existence and version-range validation.
- `archetype_type` is an `ArchetypeType` enum, not a free string.
