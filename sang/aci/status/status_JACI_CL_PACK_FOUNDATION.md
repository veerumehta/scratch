# Plan: JACI Commercial Lending Pack Foundation (cl_of / cl_sp)

**Status: Phase 1 done (2026-07-27 audit).** `config/packs/cl_of_core/` and `config/packs/cl_sp_core/`
exist with `pack_manifest.yaml`; `tests/unit/test_cl_pack_foundation.py` passes, confirming both
declare `depends_on: ci-spread-core` with `fragments: [playbooks]` (importing `ci-spread-core`'s
`pb-ci-abl-001`/`pb-ci-term-001` by reference, not duplication) — already ahead of the plan's own
written sequencing below. **Phases 2-5 not started:** no `scripts/import_cl_corpus.py`; no
`authority/`/`lifecycle/`/`events/`/`metrics/`/`governance/` subdirs in either pack; no
`scripts/generate_cl_schemas.py`; no `docs/CL_corpus/ontology_crosswalk.md`; no `validate-cl`
Makefile target.

**Flag (from `docs/CL_SOURCE_RECONCILIATION.md`, 2026-07-27):** Phase 3 below generates pydantic
models from `cls_object_model.schema.json` as though no domain object model exists yet — but
`SpreadPackage`/`SpreadLineItem` (hand-authored against JAPES primitives in
`capabilities/commercial_lending/spread_package.py`, via `plan_JACI_CL_MVDP_VP2_WEDGE.md` Phase 1)
now exist and were never reconciled to the corpus schema shape. Rescope or retire Phase 3 before
anyone executes it as written.

Author: Virendra Mehta · 2026-07-13 · Rev 2026-07-15 (capability-layer alignment; see the new section before Sequencing)
Repo: jaci · Baseline: 0.9.7 (dev) · Depends on: JAPES authority plan Phases 2-3 for typed loading (can land earlier against raw dicts; see Sequencing); JAPES pack-composition plan Phase 1 for depends_on (adoption optional at first landing)
Driver: the Commercial Lending Suite engineering corpus v1.0 ships its requirements as machine registers (54-cell authority matrix, 166-transition state machines, 47-event index, 63-object JSON Schema, evidence catalogs, metrics dictionaries, decision classes, calculation contracts). Per the code/config boundary, every one of these becomes pack data under config/packs/, imported by script, never retyped by hand. This plan creates the two spec packs and the import pipeline. No scenario behavior changes yet.

Grounding notes (verified 2026-07-13 against dev):
- config/packs/ has ci-spread-core (most complete: manifest 0.2.0-draft, ontology ci_lending.yaml ~30 entities, policies with OCC/FDIC source_refs, playbooks, evidence_types.yaml, pipelines.yaml, mode_tuning), cre_underwriting_core (mode_tuning only, no manifest), aml_investigation_core, clinical-intake-core.
- Packs load via jazzx_sdk.pack.Pack.from_manifest (see ui/registry.py Scenario.pack()). PackManifestLoader keys: pack_id, pack_version, certification_status, domain, segment, regulatory_context, policies, modes, experts, playbooks, ontology, diagnose_map, conductor, agent, evaluation.
- config/autonomy_ceilings.py is AML-shaped (RECOMMEND_ONLY/ACT_WITH_APPROVAL/FULL_AUTONOMY + SAR human-only rule); not a matrix.
- Corpus location: external, proprietary, validator-hashed (corpus_manifest.json, sha256 per file). It must NOT be vendored into the repo.

## Corpus custody decision (encoded in this plan)

The corpus root path is supplied via env JACI_CL_CORPUS_ROOT. Imported pack assets ARE committed (they are our derived pack data), and each generated file carries a provenance header: source file, corpus manifest sha256 of that file, corpus version, import script version. scripts/import_cl_corpus.py fails if the corpus's own validate_corpus.py does not PASS first.

## Phase 1 - Pack scaffolds

Create config/packs/cl_of_core/ and config/packs/cl_sp_core/ with pack_manifest.yaml each:
- cl_of_core: pack_id cl-of-core, domain commercial_lending, segment cl_of (origination and fulfillment, VP-1..VP-4), certification_status draft, regulatory_context from corpus README source list (OCC CRE + ARIF handbooks, 12 CFR 364), experts (policy + playbook, output_classification GUIDANCE_REFS at launch), autonomy_ceilings default 1, human_checkpoints seeded from human-only cells (Phase 2 fills), evaluation stanza pointing at gold_cases path (wedge plan populates).
- cl_sp_core: pack_id cl-sp-core, segment cl_sp (servicing and portfolio, VP-5..VP-6). Ownership note in manifest comments: cl_of owns the application case and never the loan asset; cl_sp owns the loan asset and never re-originates; CPEC-1 (boarding relay) and CPEC-2 (renewal return) are the only bridges.
- Reuse, do not duplicate: both manifests reference the shared ontology work in Phase 4 and the ci-spread-core playbooks where applicable (ABL revolver, term loan). ci-spread-core remains untouched and running; it becomes an ancestor, not a casualty.

## Phase 2 - Register import script

New scripts/import_cl_corpus.py (argparse: --corpus-root, --target cl_of|cl_sp|both, --check-only). Transforms, per pack:
- data/matrix_registers.csv (54 cells) -> config/packs/{pack}/authority/authority_matrix.yaml, split by cell namespace (cl.* to cl_of, sp.* to cl_sp, cre.agy.*/agency.* parked in cl_of under an agency: subsection). Column mapping is 1:1 with JAPES AuthorityCell fields.
- decision classes (from CI_decision_classes.csv, CRE_decision_classes.csv, decision_class_sentinels.csv) -> authority/decision_classes.yaml.
- data/state_machines.csv (166 transitions, 30 objects) -> lifecycle/state_machines.yaml per pack by object ownership (LoanApplicationCase, PipelineRun, SpreadPackage, Condition, TermSheet etc. to cl_of; LoanAsset, LoanHealthState, Tickler, CovenantScheduleItem etc. to cl_sp; shared objects like Decision duplicated with a shared: true marker).
- engineering/events/event_index.json + the 47 *.event.schema.json -> events/event_catalog.yaml (+ schemas embedded or referenced) in the JAPES EventCatalog.from_index consumable shape.
- data/CI_evidence_catalog.csv + CRE_evidence_catalog.csv -> evidence_types additions merged with the existing 7 in ci-spread-core style.
- data/CI_metrics_dictionary.csv + CRE_metrics_unified.csv -> metrics/metrics_dictionary.yaml. Preserve the agency basis labels: DSCR-on-NCF (Fannie) and DCR-on-NOI (Freddie) are distinct metrics and must import as distinct rows; the import script asserts both exist and are not merged.
- data/control_registers.csv (10 controls) -> governance/controls.yaml.
- EP template: design/EP-CHB doc is prose; create profiles/execution_profile_template.yaml + profiles/policy_profile_template.yaml carrying every threshold key the corpus guards reference, values left as REQUIRED placeholders (no numeric defaults; institution supplies at deployment).
- Idempotent: re-run replaces generated files; provenance headers make drift reviewable in git diff.

Acceptance: --check-only run prints counts matching the corpus (54 cells, 166 transitions, 47 events, 10 controls) and exits 0; generated YAML loads via the JAPES typed loaders (or raw-dict fallback pre-JAPES-landing, see Sequencing); a second run produces zero git diff.

## Phase 3 - Schema bindings for domain objects

Domain objects belong to JACI, not the SDK. Generate pydantic models from the corpus canonical schema:
- scripts/generate_cl_schemas.py using datamodel-code-generator against engineering/schemas/cls_object_model.schema.json -> src/jaci/scenarios/commercial_lending/schemas/canonical/ (one module per lifecycle area: foundations, pipeline, spread, case, closing, servicing, portfolio, agency). Foundation types (Money, SourceCoordinate, Provenance, Confidence, VersionBundle, EntityRef) are NOT generated; the generator maps them to the JAPES primitives (custom type mapping config checked in beside the script).
- Preserve the schema's const constraints (SpreadDecision.writer_of_record, matrix_cell_ref consts, MetricResult.recomputed true) and additionalProperties: false on the 13 MVDP-path objects; generation config asserts these survive.
- Do not delete existing spread_schema.py/ontology objects; Phase 4 crosswalks.

Acceptance: generated modules import cleanly; a round-trip test validates one corpus fixture instance per MVDP-path object against both the JSON Schema and the pydantic model.

## Phase 4 - Ontology crosswalk

- New docs/CL_corpus/ontology_crosswalk.md (in-repo doc, not corpus material): table mapping ci_lending.yaml entities to corpus canonical names (FinancialSpread -> SpreadPackage, SpreadStatement/SpreadLine -> SpreadLineItem, CreditDecision -> Decision + SpreadDecision, CreditCondition -> Condition, CreditMetrics -> MetricResult set, SourceDocument -> SourceFile, etc.), with a keep/rename/alias verdict per row.
- Rule adopted from the gap analysis: rename only at the wedge-plan boundary objects (the 13 MVDP-path objects); everything else aliases until touched. config/packs/cl_of_core/ontology/ imports ci_lending.yaml entities via the crosswalk rather than forking the file.

## Phase 5 - Validator in CI

- Makefile target validate-cl: runs corpus validate_corpus.py against JACI_CL_CORPUS_ROOT (when set), then scripts/import_cl_corpus.py --check-only, then the schema round-trip tests. CI job skips gracefully when the corpus root is absent (external contributors), runs on the internal runner where the corpus is mounted.
- tests/unit/test_cl_pack_foundation.py: manifests load through Pack.from_manifest; authority YAML row count 54; every state-machine cell_ref resolves into the imported matrix; every emitted_event resolves into the imported catalog (mirroring the corpus validator's referential-integrity gates on our side of the boundary).

Acceptance: make validate-cl green locally with corpus mounted; CI green without it.

## Capability-layer alignment (added 2026-07-15)

JACI is adopting a three-layer architecture: capabilities (domain-agnostic ability modules pairing code with pack fragments), packs (vertical knowledge declaring capability dependencies), scenarios (thin declarative compositions). SDK seams land via plan_JAPES_2_0_0_PACK_COMPOSITION_AND_CAPABILITY_SEAMS.md (depends_on manifest key with narrowing merge, conductor StepRegistry). Consequences for this plan:
- The cl_of_core/cl_sp_core manifests (Phase 1) should declare shared assets via depends_on once the JAPES key lands, rather than copying: first candidates are the ci-spread-core playbooks (ABL revolver, term loan) and a future kyb-screening capability pack (KYC/KYB stops being a fintech-only scenario and becomes a capability both AML and cl_of consume). Until the key lands, keep the Phase 1 reference-not-duplicate instruction as manual discipline; convert to depends_on as a follow-up commit, not a blocker.
- scenarios/commercial_lending/ (the shared spreading/covenant/doc-intake library) is the prototype capability and will be promoted to the capabilities layer in a later dedicated plan; nothing in this plan moves it, but new shared code written under this plan and the wedge should land in that library, not in scenario packages, so the promotion is a move, not a untangling.
- Vertical clustering (lending, healthcare, finserv) is registry metadata: add a vertical tag to SCENARIO_CONFIG entries in config/scenario_registry.py rather than reorganizing directories.

## Out of scope

Pipeline/scenario behavior (wedge plan), surfaces and endpoints (surfaces plan), agency overlay activation (imported but dormant; Form 4660 and Freddie extraction are engagement-gated), MACER, Notion updates (do after first landing), the capability-layer extraction itself (dedicated plan once the SDK seams land).

## Sequencing

Phases 1-2 can start immediately: the import script emits YAML whose shape matches the JAPES typed loaders, and until those land the pack loads them as raw dicts behind a small src/jaci/pack/cl_loaders.py shim (delete the shim when JAPES authority/events/statemachine modules ship). Phase 3 depends only on JAPES value primitives for the foundation-type mapping. Phase 5 last.
