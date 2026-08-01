# Plan: JAPES 2.0.0 Pack Composition and Capability Seams

Author: Virendra Mehta · 2026-07-15
Repo: japes (jazzx_sdk) · Baseline: 2.0.0 line · All phases additive
Driver: JACI is moving to a three-layer scenario architecture: capabilities (domain-agnostic ability modules pairing code with pack fragments, e.g. document intake, spreading, KYC/KYB screening), packs (vertical knowledge that declares capability dependencies), and scenarios (thin declarative compositions). The mirror of the CL corpus's own model, where the capability is the build unit and archetype nuance rides in data. Two small SDK seams unblock it, plus one chassis-level specialization that follows once its first consumer fixes the contract. Per the standing rule, this plan carries only invariant machinery; which capabilities exist and what knowledge they carry is JACI's.

Grounding notes (verified 2026-07-15 against dev, 2.0.0):
- pack/manifest_loader.py PackManifestLoader: flat getters over pack_manifest.yaml (pack_id, pack_version, certification_status, domain, segment, regulatory_context, policies, modes, experts, playbooks, ontology, diagnose_map, conductor, agent, evaluation, authority_matrix, surface_bindings). No inter-pack dependency concept.
- conductor/pipeline.py: ConductorPipeline is declarative (PipelineStep {id, mode, emits, execution: ExecutionKind live|deterministic|offline_asset|integration, substeps, loop}, Loop groups, from_yaml). Step implementations are bound in scenario code (each JACI conductor maps step ids to its own functions); there is no cross-pack way to reference a step implementation.
- agents/interactive/: InteractiveAgentSpec.from_dir, skills as sub-agents, guardrail registry - the precedent for a declarative agent chassis. tools/ has extraction/classify/documents/processors modules the doc chassis will compose rather than replace.
- JACI precedent: src/jaci/scenarios/commercial_lending/ is already a shared library consumed by ci_spread, cre_underwriting, and portfolio_monitoring; the capability layer promotes that pattern.

## Phase 1 - Pack dependency and fragment merge

pack/manifest_loader.py:
- New optional manifest key depends_on: list of {pack_id, version_range (optional), fragments (optional list limiting what is imported: evidence_types, policies, playbooks, mode_tuning, ontology)}. Absent key keeps today's behavior exactly.
- New resolve_dependencies(packs_root) on PackManifestLoader returning the ordered closure (depth-first, cycle detection raising PackDependencyError naming the cycle path).
- Merge semantics, pinned here because they are governance-relevant:
  1. The importing pack NARROWS, never widens: imported policies/evidence floors/autonomy postures may be tightened by the importer, and an importer's re-declaration of an imported rule must be at least as restrictive (same discipline as the Pack -> SBA -> Overlay -> EP chain; violations fail at load, not silently resolve).
  2. Asset id collisions across imported packs fail loud (no last-writer-wins); the importer must alias or exclude via the fragments filter.
  3. Provenance is preserved: every merged asset records source_pack_id + source_pack_version so citations and traces name the owning pack, not the importer.
- pack/pack.py Pack.from_manifest gains the same optional resolution (flag-gated resolve_deps=True default; single-pack behavior unchanged when no depends_on present).

Acceptance: fixture packs A -> B -> C resolve in order; cycle A -> B -> A raises with the path; a widening re-declaration fails at load; merged evidence type carries source_pack_id of its declaring pack.

## Phase 2 - Conductor step registry

conductor/ additions (schema untouched; binding layer new):
- New conductor/step_registry.py StepRegistry: register(step_impl_id, callable, emits=None, execution=None) and resolve(step_impl_id). Capability modules register named implementations at import time (or via entry-point-style explicit registration in pack binding code; no import-time magic scanning).
- PipelineStep gains optional impl: str (default None). When set, the conductor engine resolves the callable from the registry instead of expecting the scenario conductor to bind the id itself. When absent, today's scenario-bound behavior is untouched (AML/KYC/ci_spread keep working unmodified).
- Registry entries declare what they emit so pipeline validation can check impl.emits matches step.emits at load.
- Deliberately small: no versioning of step impls in this phase (the pack's version bundle already pins the code); no remote/dynamic loading.

Acceptance: a pipeline YAML with impl: on two steps runs against registry-provided callables; mismatched emits fails at pipeline load; existing pipelines without impl load byte-identically.

## Phase 3 - Document processing and classification agent chassis (gated)

Gate: do NOT start until JACI wedge Phase 1 lands. Its objects (SourceFile with content_hash, ExtractedField with SourceCoordinate + Confidence, classification outputs, the XF-1 100%-provenance gate) are the chassis contract, and the chassis must be built against its three real consumers: ci_spread spreader, kyc_anthropic document trees, clinical intake attachments. InteractiveAgent earned its shape the same way; the profiles trim in the authority plan is the standing warning against running ahead of consumers.
Sketch to be firmed post-gate (a one-page amendment to this plan, not a new plan):
- agents/document/ DocumentAgent: declarative spec (from_dir) composing the existing tools/ extraction, classify, documents, processors modules into an ingest -> classify -> extract -> emit pipeline that yields provenance-complete canonical objects; pluggable taxonomy (pack data); confidence tiers resolved via PolicyProfile floors; sub-floor admission returns the typed Refusal, never a degraded write.
- Registers its stages as StepRegistry implementations (Phase 2), so any pack pipeline can weave doc processing by reference.

Acceptance (post-gate amendment will pin): the three named consumers run on the chassis with zero unsourced values; the ci_spread spreader path produces results equivalent to its pre-chassis output on the YETI fixture.

## Out of scope

Which capabilities exist, their pack fragments, KYC/KYB knowledge, capability directory layout in JACI (all JACI); marketplace/studio UI; step-impl versioning; dynamic capability discovery.

## Sequencing

Phases 1 and 2 are independent, small, and unblock JACI's capability extraction immediately; ship on the 2.0.0 line. Phase 3 waits for its gate. JACI-side counterparts land as updates to plan_JACI_CL_PACK_FOUNDATION.md (depends_on adoption, capability fragments) and plan_JACI_CL_MVDP_VP2_WEDGE.md (chassis contract note).
