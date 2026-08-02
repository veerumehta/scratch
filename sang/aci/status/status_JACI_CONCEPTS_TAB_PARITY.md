# Status: Concepts Tab Parity Across Scenarios

Author: Virendra Mehta · Updated 2026-08-01
Repo: jaci · Plan: docs/plans/plan_JACI_CONCEPTS_TAB_PARITY.md

**Phases 0, 1, 4 done — Phase 1's own premise turned out false for both scenarios it named; Phase 4
did have one genuine cheap win. Phases 2-3 (AML/CRE pack authoring) not started — real authoring
work, not wiring, exactly as the plan itself expected.** Phase 5 depends on Phase 2 landing first.

## Phase 0 — Inventory, verified directly against real code (not the plan's own table)

- **`Pack.from_manifest`'s actual convention** (`jazzx_sdk/pack/manifest_loader.py:87-99`): it only
  ever looks for `packs_root/<pack_id>/pack_manifest.yaml` (trying `-`/`_` variants of the id) —
  never a loose YAML sitting at the packs root under a different filename. Checked this directly
  before trusting the plan's own inventory table.
- **`clinical-intake-core` genuinely loads and renders clean** — the plan's own ask ("verify... 
  nobody has audited its Concepts rendering"). Ran `Pack.from_manifest("clinical-intake-core",
  packs_root)` directly: loads, and every accessor `concepts_view.render()` touches
  (`.ontology`, `.policies`, `.policy_registry`, `.playbooks`, `.modes`, `.experts`, `.segment`,
  `.policy_sources`, `.playbook_sources`, `.conductor`) resolves without error (empty list/dict
  where nothing's authored, real content for ontology/modes, `.conductor is None` degrading
  cleanly to `scenario.pipeline()`). `pack_id="clinical-intake-core"` is already declared in
  `ui/registry.py` — **this scenario was already fully done before this pass**, nothing to wire.
- **`aml_investigation_core.yaml` and `earnings_review.yaml` do NOT load, at all** — checked by
  actually calling `Pack.from_manifest` with every plausible id spelling
  (`aml_investigation_core`/`aml-investigation-core`/`earnings-review`/`earnings_review`): all four
  raise `FileNotFoundError`. Both files sit as loose YAML at `config/packs/` root, not inside their
  own `<pack_id>/pack_manifest.yaml`. This is the plan's own inventory table's "present (verify in
  Phase 0)" language turning out optimistic for these two specifically — they are documentation
  stubs, not loadable manifests, and neither has the `ontology:`/`policies:`/`playbooks:` pointer
  keys `PackManifestLoader` expects even setting the filename issue aside. **Confirms the plan's
  own Phase 2 framing exactly**: "they live outside the repo, which is the defect" — real authoring,
  not relocation, is what closes this gap.
- **`cre_underwriting_core/` has only `mode_tuning/`** — no ontology/policies at all, matching the
  table. **`portfolio_monitoring` and `insurance_diligence` have no pack directory** — matching the
  table.

## Phase 1 — Cheap wiring: not available for either scenario it named

The plan's Phase 1 text ("declare `pack_id=aml_investigation_core` if the draft manifest loads...
declare `pack_id` for earnings if `earnings_review.yaml` is a loadable manifest") is conditional on
a premise Phase 0 just disproved for both. Declaring either `pack_id` today would make
`Scenario.pack()` raise `FileNotFoundError` instead of degrading to the pipeline-only fallback it
currently uses — strictly worse than doing nothing. **Not wired, correctly, not by omission.**

## Phase 4 — The demo-only pair: one real cheap win, one honest non-gap

- **`portfolio_monitoring` had a real, already-built, unwired `ConductorPipeline`** —
  `src/jaci/scenarios/portfolio_monitoring/conductor.py`'s module-level
  `PORTFOLIO_REVIEW_PIPELINE` (steps: `spread → reconcile → occupancy → risk → assemble`), the
  exact "deterministic pipeline object in their capability code" the plan's Phase 4 asks to check
  for. Wired: `pipeline_target=("jaci.scenarios.portfolio_monitoring.conductor",
  "PORTFOLIO_REVIEW_PIPELINE")` in `ui/registry.py`. Verified directly:
  `scenario.pipeline()` resolves to the real `ConductorPipeline` object with its 5 steps.
  (Noted, not touched: the pipeline's own `.name` reads `"CRE Annual Review"` — a pre-existing
  copy-paste artifact from wherever this was adapted, unrelated to this wiring change and out of
  scope for a registry-only pass.)
- **`insurance_diligence` has no conductor/pipeline file anywhere** — checked directly
  (`find src/jaci/scenarios/insurance_diligence -iname "*conductor*" -o -iname "*pipeline*"`:
  empty). Per the plan's own instruction, this is recorded as **the accepted state** (platform-
  layer-only Concepts rendering), not a gap to chase — there is no deterministic pipeline object to
  point at.
- `kyc_anthropic` — untouched, keeps its existing pipeline fallback per the plan's own explicit
  instruction (a KYC pack is separate roadmap work).

Full jaci suite: 798 passed (unchanged), 8 skipped, 5 xfailed, same 6 pre-existing unrelated
failures — no regressions, as expected for a pure additive `pipeline_target` on a scenario that
previously had none.

## Deliberately not done (stated, not silently dropped)

- **Phase 2 (AML pack authoring)** and **Phase 3 (CRE pack authoring)** — real content-authoring
  work (ontology from the SEO entity map, policies from the authority matrix, evaluation gates from
  ECAP thresholds for AML; ontology + core policies from the CRE domain reference for CRE), not UI
  wiring. Not started. The plan's own source material references
  (`AML_Domain_Pack_Appendix.md`, `CRE_Domain_Reference.md`) live outside this repo per the plan's
  own text ("They live outside the repo, which is the defect") — locating and ingesting them is
  itself part of Phase 2/3's scope, not yet begun.
- **Phase 5 (policy resolution view adoption for AML)** — blocked on Phase 2 landing real AML
  policies first; the generic seam itself (`Scenario.policy_resolution_target`/
  `.policy_resolution_renderer()`) already exists and is already proven working for C&I
  (`plan_JACI_CL_POLICY_EXPERT.md` Phase 6, done) — so this phase is pure reuse once Phase 2 lands,
  not new machinery.
