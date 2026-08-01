# Plan: JACI Capabilities Layer — promote commercial_lending to the capability tier

**Status: Phases 0-2 done (commits `899728b`, `6ccfdb3`; 2026-07-27 audit).** `capability.yaml`
exists for all 5 capabilities (`commercial_lending`, `document_intake`, `financial_spreading`,
`credit_validation`, `underwriting_decision`); the old `scenarios/commercial_lending/` re-export
shim is gone with zero remaining references — further along than Phase 5 admits (see below).
**Phase 3 not started:** `config/packs/cl_of_core/pipelines.yaml` still uses un-namespaced
`impl: cl.ingest/cl.spread/cl.gate` ids, and no pack manifest has a `capabilities:` key.
**Phase 4 not started:** zero hits for `kyb-screening`/`kyb_screening` anywhere. **Phase 5
partially done:** per this plan's own inline note below, Phase 1's atomic import rewrite already
folded in Phase 5's "update consumer sites, delete the shim" half; only Phase 5's other half
(removing the transitional `cl.*` impl-alias map) remains, and it's still live in
`cl_capability.py:56-61`.

Author: Virendra Mehta · 2026-07-16 · DRAFT
Repo: jaci (primary) · Baseline: 0.9.x (dev) · Depends on: JAPES 2.0 pack-composition seams (StepRegistry +
`depends_on`/fragments — shipped) and the CL wedge (spread_package / metric_result / normalize / validation
/ promotion / pipeline_objects / cl_capability / cl_events — shipped in `scenarios/commercial_lending/`).
Driver: JACI's three-layer architecture — **capabilities** (domain-agnostic ability modules pairing code
with pack fragments), **packs** (vertical knowledge declaring capability dependencies), **scenarios** (thin
declarative compositions). `scenarios/commercial_lending/` is the prototype capability library; the
foundation plan (L64) deferred its promotion to this dedicated plan and mandated it be a **move, not an
untangling** (shared code already lands there, not in scenario packages). This plan relocates it into a
first-class capabilities tier, splits it along real seams, and rewires packs/scenarios to consume it by
declaration.

## Grounding notes (verified 2026-07-16 against dev)

- `src/jaci/scenarios/commercial_lending/` (19 modules): spreading (`spreader`, `spread_schema`,
  `spread_package`, `template`, `excel`, `_llm`, `spread_anchors.yaml`), analytics (`analytics`,
  `metric_result`, `normalize`), intake (`pipeline`, `pipeline_objects`, `docintel`), `validation`,
  `promotion`, `policies`, `insurance_loe`, and the wiring (`cl_capability` = StepRegistry + the
  `pipelines.yaml`-loaded `CL_SPREAD_PIPELINE`, `cl_events` = the vp.activity.* catalog + instrumenter).
- Consumers (import `scenarios.commercial_lending`): `ci_spread` (conductor, credit_outcome, ui),
  `cre_underwriting` (case, insurance_loe, ui ×2), `insurance_diligence` (ui). 8 import sites — the move
  must preserve these paths through the transition.
- Step impls are already registered by id (`cl.ingest` … `cl.gate`) via `build_cl_step_registry`; the pack
  pipeline (`config/packs/cl_of_core/pipelines.yaml`) binds steps by `impl:`; `Pack.conductor` resolves it.
  The registry seam is the capability publish mechanism — this plan formalizes the *packaging* around it.
- japes provides no `Capability` type; per the standing rule (which capabilities exist is JACI's), the
  capability descriptor is a thin JACI construct over the japes StepRegistry + `depends_on`/fragments.

## The capability contract (Phase 0)

A **capability** is a self-contained package under `src/jaci/capabilities/<name>/` pairing:
- **code** — the modules + a `provides.py` exposing one entrypoint `register(registry: StepRegistry) -> None`
  that registers the capability's named step impls (idempotent), plus any public objects/functions;
- **pack fragment** (optional) — `config/packs/<name>-core/` with the fragment assets the capability owns
  (evidence_types, playbooks, mode_tuning, anchors), importable by a vertical pack via `depends_on`;
- **a manifest** — `capability.yaml`: `capability_id`, `version`, `provides.step_impls` (list of
  `{impl_id, emits, execution}`), `provides.fragments` (which pack-fragment kinds it ships), `depends_on`
  (other capabilities), `description`.

New `src/jaci/capabilities/registry.py`:
- `Capability` (pydantic): the parsed `capability.yaml`.
- `CapabilityRegistry.discover(root)` — load every `capabilities/*/capability.yaml`; `resolve(ids)` returns
  the dependency-ordered closure (reuse the `depends_on` DFS/cycle-detection discipline from
  `PackManifestLoader`); `build_step_registry(ids)` composes a japes `StepRegistry` from the closure's
  `register()` entrypoints (collision-fail-loud on duplicate impl_id across capabilities).
- No import-time scanning magic — `register()` is called explicitly by the composer.

Acceptance: a fixture capability with a `capability.yaml` + `provides.register` loads, resolves, and yields
a `StepRegistry` whose impls match the manifest's declared `emits`; a duplicate impl_id across two
capabilities fails loud.

> **Status (2026-07-16): Phase 0 + Phase 1 SHIPPED** (`899728b`). Deviation from the shim approach below:
> the consumers lean on submodule-path imports (`._llm`, `.spreader`, `.template`, `.ui`, …) that a
> package `__init__` re-export shim can't cover cleanly, and a `sys.modules` submodule-alias shim risks
> double-loaded modules. So Phase 1 was done as an **atomic mechanical import rewrite** of all references
> (no shim) — which folds Phase 5's umbrella-path consumer migration into the move. Phase 5 now only needs
> to remove the transitional `cl.*` impl aliases introduced by the Phase-2 split.

## Phase 1 — establish the tier + relocate the prototype (move, not untangle)

- Create `src/jaci/capabilities/`. Move `scenarios/commercial_lending/` → `capabilities/commercial_lending/`
  **verbatim** (git mv; no code changes), add its `capability.yaml` (declares the `cl.*` step impls already
  in `build_cl_step_registry`, fragments it will own).
- Leave `scenarios/commercial_lending/__init__.py` as a **re-export shim** (`from jaci.capabilities.commercial_lending import *` + explicit names) so the 8 consumer sites keep working unchanged. The shim is temporary (removed in Phase 5).
- `cl_capability.build_cl_step_registry` becomes the capability's `provides.register`; `CL_SPREAD_PIPELINE`
  keeps loading from `config/packs/cl_of_core/pipelines.yaml`.

Acceptance: full suite green with zero consumer edits (shim holds); `capabilities/commercial_lending/capability.yaml`
loads via `CapabilityRegistry`; `build_step_registry(["commercial-lending"])` reproduces today's registry.

> **Refinement (2026-07-16): Phase 2 done as a LOGICAL split.** The wedge modules depend on the shared
> spreading library (spreader/spread_schema/analytics/_llm), so any physical carve leaves the capabilities
> depending on `commercial_lending` regardless — and physically moving modules re-breaks consumer
> submodule imports. So each capability is a real package owning its **step-impl code** (`provides.py`,
> namespaced impl ids `intake.*`/`spread.*`/`credit.*`) over the shared `commercial_lending` library, which
> stays intact as the domain implementation. `cl.*` impls are retained as aliases (registered by the
> umbrella) so the pack pipeline keeps working until Phase 3 migrates it. Physical module relocation into
> per-capability dirs is deferred as an optional cleanup (low value, high churn).

## Phase 2 — split along the real seams

Split the monolith into cohesive capabilities (each its own dir + `capability.yaml` + `provides.register`),
keeping a `commercial_lending` umbrella that `depends_on` them so the shim's surface is unchanged:
- **document-intake** — `pipeline`, `pipeline_objects`, `docintel` (SourceFile/ExtractedField/PipelineRun,
  classify). Impls `intake.ingest`, `intake.classify`. Cross-vertical (ci/cre/clinical/kyc).
- **financial-spreading** — `spreader`, `spread_schema`, `spread_package`, `template`, `excel`, `analytics`,
  `metric_result`, `normalize`, `_llm`, `spread_anchors.yaml`. Impls `spread.spread`, `spread.metrics`.
  Fragment: spread anchors + financials evidence_types + the ABL/term playbooks (moved from ci-spread-core).
- **credit-validation** — `validation` (+ `policies` covenant/checklist helpers). Impl `validation.validate`,
  the promotion gate. Fragment: defect-severity policy.
- **underwriting-decision** — `promotion` (affirm/promote/supersede). Authority cell refs stay pack data.
- `insurance_loe` moves with document-intake or its own small capability (consumed by cre/insurance only).
The `cl.*` impl ids are re-registered under capability-namespaced ids (`intake.ingest` …); a compatibility
alias map keeps `cl.ingest` resolving during transition (pipelines.yaml migrates to the new ids in Phase 3).

Acceptance: each capability's tests pass in isolation; `build_step_registry(["financial-spreading",
"document-intake", "credit-validation", "underwriting-decision"])` equals the umbrella registry; no import
cycles between capabilities (only declared `depends_on`).

## Phase 3 — packs declare capability dependencies; scenarios thin to compositions

- `cl_of_core` / `cl_sp_core` manifests gain a `capabilities:` key (or reuse `depends_on` against the
  capability packs) naming the capabilities they compose; `pipelines.yaml` migrates its `impl:` refs to the
  namespaced ids. `Pack` resolves the composed `StepRegistry` from its declared capabilities.
- `ci_spread` / `cre_underwriting` conductors become thin: build the registry from declared capabilities +
  bind only their scenario-specific steps/overrides (the engine's explicit-component override already
  supports scenario specialization). Delete duplicated logic now living in the capability.
- Vertical clustering stays registry metadata (a `vertical` tag on `SCENARIO_CONFIG`), not directories.

Acceptance: `ci_spread` and `cre_underwriting` run their pipelines resolving steps from capabilities (no
direct `commercial_lending` imports beyond the capability API); YETI spread output is unchanged
(equivalence test against the pre-move fixture).

## Phase 4 — kyb-screening as the cross-vertical proof

Extract KYC/KYB screening (today a fintech-only scenario) into a `kyb-screening` capability with its own
pack fragment, consumed by **both** `aml_investigation_core` and `cl_of_core` via `depends_on`. This is the
proof that the tier is genuinely cross-vertical, not a CL-only rename.

Acceptance: one screening capability, two consuming packs; an AML scenario and a CL scenario each resolve
the screening step from the shared capability; no duplication.

## Phase 5 — remove the shim, registry-based discovery

- Update the 8 consumer import sites to the capability API; delete the `scenarios/commercial_lending/`
  re-export shim and the `cl.*` alias map.
- `CapabilityRegistry.discover` becomes the one source of truth; a CI test asserts every pack's declared
  capabilities resolve and every pipeline `impl:` is registered (mirrors the pack-foundation referential
  gate).

Acceptance: no references to `scenarios.commercial_lending` remain; `make` test target green; a
capability/pack referential-integrity test passes.

## Out of scope

japes changes (the seams are shipped; a `Capability` type in the SDK is a *later* possibility once ≥2
repos want it — not this plan); the doc-processing agent chassis (japes pack-composition Phase 3, gated on
the wedge — separate); wedge P4 corpus import (parked on `JACI_CL_CORPUS_ROOT`); marketplace/studio UI;
new domain behavior (this is a relocation + packaging plan, behavior-neutral per phase).

## Sequencing

Phase 0 + Phase 1 first (the move is low-risk behind the shim and unblocks everything). Phase 2 is
independent per capability — split in the order document-intake → financial-spreading → credit-validation →
underwriting-decision (dependency order). Phase 3 follows the split. Phase 4 (kyb) can run in parallel once
the contract (Phase 0) exists. Phase 5 last (shim removal), after consumers are migrated. Each phase is
behavior-neutral and independently shippable; keep the equivalence test (YETI spread + the 116 wedge tests)
green throughout.
