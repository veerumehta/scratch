# Commercial Lending: Source Reconciliation

Author: Virendra Mehta · 2026-07-27
Status: reference note, not a plan. No phases, no acceptance criteria. Read this before writing a new CL plan.

## Why this exists

Two source documents drive the Commercial Lending work, authored weeks apart, both covering C&I spreading with YETI as a shared reference case. Plans written from one without reading the other have already drifted once. This note declares which source is authoritative for what, and records the places where they actually collide.

## The two sources

**Commercial Lending Suite engineering corpus v1.0.** A machine register: 54-cell authority matrix, 166-transition state machines, event index, `cls_object_model.schema.json`, evidence and metrics dictionaries, human-only cells. Drove `plan_JACI_CL_PACK_FOUNDATION.md`, `plan_JACI_CL_MVDP_VP2_WEDGE.md`, `plan_JACI_CL_CAPABILITIES_LAYER.md` and `plan_JACI_CL_SURFACES_EXPERTS_AND_WRITEBACK.md`, dated 2026-07-13 to 07-16.

**Financial Spreading PRD v0.4 (June 2026).** 117 functional requirements across 18 areas, MVP scoped to C&I, exit criterion the Regional Bank LTM Sep-2023 working spread. Drove `plan_JACI_CL_PRD_DEMO_ARC.md` and, indirectly, the spread template and chart-of-accounts work, dated 2026-07-26 to 07-27.

## The declared layering

They do not compete. They stack.

- The **corpus** is authoritative for governance and lifecycle: authority, states, transitions, events, object identity, segment ownership boundaries.
- The **PRD** is authoritative for functional capability: what the pipeline must do to a document, and what the output must contain.

Where both speak, the corpus wins on identity and the PRD wins on behaviour.

## Pack structure (settled, not in dispute)

An earlier reading treated `ci-spread-core`, `cl_of_core` and `cl_sp_core` as rival namings. They are not. The manifests declare a deliberate split with an explicit dependency edge:

- `ci-spread-core` is the C&I spreading and underwriting base. All live assets are here.
- `cl_of_core` is origination and fulfillment (VP-1..VP-4). Owns the application case, never the loan asset.
- `cl_sp_core` is servicing and portfolio (VP-5..VP-6). Owns the loan asset, never re-originates.

Both segment packs declare `depends_on: ci-spread-core` with `fragments: [playbooks]`, and both manifests state that ci-spread-core stays untouched and becomes an ancestor. CPEC-1 (boarding relay at funding) and CPEC-2 (renewal return) are the only bridges between the segments.

The two segment packs are currently scaffolds holding manifests only. The corpus import (`PACK_FOUNDATION` Phase 2) has not run, so no codebase artifact derives from corpus *content* yet, only from its architectural ideas.

## Actual collisions

**1. Two VP-2 spread pipelines.** `CI_PIPELINE`, a code literal from `CIConductor.describe()` declared by `ci-spread-core`, versus `CL_SPREAD_PIPELINE`, loaded from `cl_of_core/pipelines.yaml` with steps resolved by `impl:` through a `StepRegistry`. `cl_capability.py` acknowledges the mirroring and calls itself the prototype. **Resolved 2026-07-27: the declarative capability pipeline is the direction.** `plan_JACI_CL_PRD_DEMO_ARC.md` Phase 1 migrates the demo onto it. `CI_PIPELINE` stays reachable; retiring it is a separate decision.

**2. Object model.** `SpreadPackage` and `SpreadLineItem` were hand-authored against JAPES primitives, with the wedge plan's own docstring saying the corpus schema generation reconciles to this shape later. It never did. `PACK_FOUNDATION` Phase 3 still describes generating pydantic from `cls_object_model.schema.json` as though nothing exists. **Unresolved.** That phase needs rescoping or retiring before anyone executes it.

**3. Defect taxonomy.** Corpus six defect classes versus the PRD's six known traps and ten VAL checks; different, partially overlapping sets. **Resolution queued** in `plan_JACI_CL_PRD_DEMO_ARC.md` Phase 4: one set, each fixture tagged with both provenances.

**4. Exit criterion and reference case.** The corpus uses YETI as its Manufacturing and Distribution certification fixture. The PRD lists YETI as a reference package but gates MVP on the Regional Bank spread. All current work is YETI-only. `ci-spread-core` already carries an `rb_ci` policy overlay for program ids RB-CI-001 and RB-CI-002, so the two are closer than the plans read. **Unresolved:** nothing currently targets the RB exit criterion.

## Plan hygiene

`PACK_FOUNDATION`, `MVDP_VP2_WEDGE`, `CAPABILITIES_LAYER` and `SURFACES_EXPERTS_AND_WRITEBACK` are partially executed but still sit in `docs/plans/` with no status file, so they read as entirely unstarted. Converting them to `docs/status/` entries with honest per-phase completion would remove most of the felt proliferation without any code change. That conversion has not been done.

Convention reminder for anyone writing a new CL plan: read `docs/status/` alongside `docs/plans/` before grounding. A plan doc in the open directory is not evidence that its phases are open.
