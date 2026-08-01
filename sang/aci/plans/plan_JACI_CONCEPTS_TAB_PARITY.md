# Plan: Concepts Tab Parity Across Scenarios

Author: Virendra Mehta · 2026-07-31
Repo: jaci · Baseline: 0.13.0 (dev)
Depends on: nothing unlanded for Phases 0–4. Phase 5 consumes the generic resolution-view seam from `plan_JACI_CL_POLICY_EXPERT.md` Phase 6. That plan is the priority; this one fills in behind it.

Driver: the Concepts tab (`ui/concepts_view.py`) is the domain-assembly story that precedes every demo — platform layer authored once, domain layer read from the pack manifest, graceful degradation when a scenario has no pack. C&I is the only scenario near full strength. The registry was designed for this to be cheap (`pack_id` is a one-line declaration, `Scenario.pack()` resolves the manifest), so the gap is mostly authoring, not machinery. This plan closes it scenario by scenario, honestly: where a pack is skeletal, the work is pack assets, and no amount of UI wiring substitutes.

Inventory as verified 2026-07-31 against dev:

| Scenario | pack_id declared | Pack assets on disk | pipeline_target |
|---|---|---|---|
| ci_spread | ci-spread-core | full (ontology, policies, playbooks, templates, mode tuning) | yes + focus |
| clinical_intake | clinical-intake-core | present (verify in Phase 0) | no |
| aml | — | `aml_investigation_core/`: discovery.yaml + mode_tuning only; manifest `aml_investigation_core.yaml` is 0.1.0-draft | yes |
| cre_underwriting | — | `cre_underwriting_core/`: mode_tuning only | yes |
| kyc_anthropic | — | none | yes |
| earnings_anthropic | — | `earnings_review.yaml` manifest at packs root | yes |
| insurance_diligence | — | none | no |
| portfolio_monitoring | — | none | no |

## Phase 0 — Inventory and truth table

For each scenario: does `Pack.from_manifest(pack_id, packs_root)` load, what does the Concepts tab actually render today, and what does the manifest declare vs. what exists on disk. Verify the clinical-intake pack really loads (it declares `pack_id` but nobody has audited its Concepts rendering). Record the matrix in this plan's status doc. No code changes.

## Phase 1 — Cheap wiring (registry one-liners)

Where assets already load, declare them: `pack_id="aml_investigation_core"` (if the draft manifest loads — mode tunings and the discovery asset render, which is more than the current fallback), `pack_id` for earnings if `earnings_review.yaml` is a loadable manifest. Nothing is authored in this phase; it only surfaces what exists. Acceptance: each wired scenario's Concepts tab shows its domain layer without error, and scenarios left unwired degrade exactly as before.

## Phase 2 — AML pack authoring (the richest gap)

The AML domain artifacts already exist in project knowledge (`AML_Domain_Pack_Appendix.md`, extracted from the retired jaci-aml v1.5 plan cluster): the 15-cell authority matrix, the outcome taxonomy with observation windows, the 8-row SEO entity map, ECAP Tier-1 promotion thresholds. They live outside the repo, which is the defect. Author them as pack assets under `config/packs/aml_investigation_core/` — ontology from the SEO entity map, policies from the authority matrix, evaluation gates from the ECAP thresholds — and bump the manifest off 0.1.0-draft. The Concepts tab then renders them with zero UI work, including the doc→object provenance blocks `concepts_view` already draws.

## Phase 3 — CRE pack authoring

Source is `CRE_Domain_Reference.md` (policy-matrix scale, TAT targets, the 9-assistant table) plus the CRE conductor's existing schemas. Author ontology + core policies into `cre_underwriting_core/`, declare `pack_id`. Smaller than AML; the domain reference is business-case heavy, so keep only what the Concepts tab can show truthfully — entities, relationships, the covenant/underwriting policies the CRE pipeline actually enforces.

## Phase 4 — The demo-only pair

insurance_diligence and portfolio_monitoring have no pack and no `pipeline_target`. Decide per scenario: if a deterministic pipeline object exists in their capability code, declare `pipeline_target` so Concepts at least shows the assembly diagram; if not, the platform-layer-only rendering is the accepted state — record that as a decision, not a gap. kyc_anthropic keeps its pipeline fallback; a KYC pack is real authoring work that should wait for the scenario's own roadmap rather than being stubbed for a tab.

## Phase 5 — Policy resolution view adoption

Once `plan_JACI_CL_POLICY_EXPERT.md` Phase 6 lands its generic seam (resolution result in, rows out, nothing ci-specific in `concepts_view`), feed it from any scenario that gains a policy set here — AML first (Phase 2 gives it real policies with authority-matrix lineage). Acceptance: AML's Concepts tab shows a resolved policy ladder the same way C&I's does, from the same shared renderer.

## Sequencing

Phases 0–1 are an afternoon and pure gain. Phase 2 is the substantial one and has its source material ready. Phase 3 follows when CRE returns to focus. Phase 4 is a decision plus at most two registry lines. Phase 5 trails the PolicyExpert plan by design. Every phase leaves all eight scenarios rendering.
