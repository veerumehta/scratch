# Plan: CiSpreadPolicyExpert — FR-SOP Closure

Author: Virendra Mehta · 2026-07-31
Repo: jaci (one small japes seam, flagged in Phase 1) · Baselines: jaci 0.13.0, japes 2.2.3
Depends on: nothing unlanded. Slots into `plan_JACI_CL_PRD_COMPLETION.md` as the FR-SOP closure; complements, does not duplicate, Wave 1b (`plan_JACI_CL_ADDBACK_LIBRARY.md`) and Wave 3b (`plan_JACI_CL_REVIEW_SURFACE.md`).

Driver: the pack has canonical Policies (`config/packs/ci-spread-core/policies/core.yaml`, `conventions.yaml`, the RB overlay) and a `PolicyRegistry`, but no Expert surface over them. Resolution wiring lives in module constants (`CI_CORE_POLICY_IDS`, `OVERLAY_MAP` in `scenarios/ci_spread/policies/registry.py`), compliance evaluation is scattered through validation, and nothing implements the PRD's scoping ladder (FR-SOP-1: institution → product → deal, with the per-package special-instructions file overriding the profile for that deal). This plan stands up `CiSpreadPolicyExpert` as the single governed answer to "which policy applies, is this compliant, and why."

Requirements closed: FR-SOP-1, FR-SOP-3, FR-SOP-4, FR-SOP-5. Out of scope: FR-SOP-2 (documentation matrices, V1 per the PRD), FR-SOP-6 (SOP-to-rules translation — that is Pack Studio's policy ingestion workspace, per the note in `policies/loaders.py`).

## Grounding notes (verified 2026-07-31 against dev)

- `jazzx_sdk/experts/policy/base.py` defines the four-operation contract (`resolve`, `check_compliance`, `interpret`, `detect_staleness`) with typed results. `DefaultPolicyExpert` (`experts/policy/default.py`) already evaluates flat-Expression and DSL rule conditions and builds violation rationales. Subclass it; do not rebuild condition evaluation.
- `scenarios/ci_spread/experts/` holds `playbook.py` and a stale `__pycache__/policy.cpython-312.pyc` — a `policy.py` existed and was deleted. Phase 0 checks git history for why before rebuilding.
- Wave 3b machinery is landed and importable from `jaci.capabilities.commercial_lending`: `Correction`/`make_correction`/`apply_corrections` (required rationale, superseded value, override lineage), `MakerCheckerRoles`/`check_maker_checker_roles`, `exception_summary`, `aggregate_status`. Phase 3 reuses these; it builds no new override machinery.
- `ValidationFinding` severities: Wave 2a replaced blocking/advisory with six severities. Threshold evaluation in Phase 3 must emit these, not a new flag vocabulary.
- Policies and the PolicyExpert already have three UI homes, corrected 2026-07-31 after a first draft of this plan claimed otherwise. (1) The **🧩 Concepts tab** (`ui/concepts_view.py`) — the shared landing tab under every scenario, manifest-driven (ontology graph, policies with doc→object provenance, playbooks, mode tunings), degrading gracefully when a scenario has no pack; C&I is the most fully populated instance, and it already names PolicyExpert in the platform-layer copy. (2) The demo's last tab, **Docs & Policies** (`render_docs_and_policies`, fed `CI_REGISTRY` + `extracted_policy_ids`). (3) The Covenants tab's **Policy sources** expander (per-rule source lineage, "PolicyExpert is advisory" caption). Phase 6 extends these existing surfaces; it builds no new panel. `plan_JACI_CL_GOVERNED_LAYER_UI.md` Phases 2–5 remain open and separate.

## Phase 0 — Grounding

Read `policies/registry.py`, `policies/loaders.py`, `DefaultPolicyExpert`, and the profile schema. `git log --diff-filter=D -- 'src/jaci/scenarios/ci_spread/experts/policy.py'` (and `git log -p` on the hit) to learn what the deleted expert did and why it went; fold anything worth keeping into Phase 2.

Decision to surface before coding, with a recommendation to be confirmed: which profile config is canonical Policy versus plain profile data. Recommendation: anything that can block or flag (thresholds, caps, precedence rules, exception policy) is a Policy; anything that only parameterizes rendering or math (tolerances, workbook layout, period method selection) stays profile config. FR-SOP-1 lists both kinds in one breath; the split is ours to draw, and it should be drawn once, here.

Acceptance: a short note in this plan's status doc recording the git findings and the confirmed Policy-vs-profile split.

## Phase 1 — Scoping ladder as data (pack YAML)

- Add `scope` metadata (`institution | product | deal`) to the existing policy YAMLs. Prefer carrying scope in canonical `Policy` metadata; if the schema cannot, that is the japes seam — flag it and stop rather than inventing a sidecar convention.
- Extend `config/packs/ci-spread-core/policies/overlays/` with the deal scope: the per-package special-instructions file parses into an ephemeral, deal-scoped overlay Policy. Highest precedence, never persisted into institution policy — the FR-HIL-5 guard against deal overrides silently mutating institution rules. Ephemeral means: constructed at package ingest, lives with the deal context, absent from the registry's persistent set.

Acceptance: `load_convention_policies()` and the overlay loaders round-trip scope metadata; a special-instructions fixture parses into a deal-scoped Policy that exists only in the deal context.

## Phase 2 — `CiSpreadPolicyExpert` (restore `experts/policy.py`)

Subclass `DefaultPolicyExpert`. Override `resolve()` with the precedence ladder: deal special-instructions → program overlay (`OVERLAY_MAP[program_id]`) → core (`CI_CORE_POLICY_IDS`) → conventions. Conflicts are reported in `PolicyResolutionResult.conflicts`, never silently merged — same aggressive-flagging stance the PRD takes everywhere else.

Retire `CI_CORE_POLICY_IDS` and `OVERLAY_MAP` as public wiring; they become construction details of the expert, and callers resolve through it. Keep the named Policy constants — tests and the demo cite them.

Acceptance: the RB package resolves `[deal-si (when present), RB_CI_OVERLAY, core ×4]` in that order; a fabricated conflicting overlay produces a populated `conflicts` list; no caller outside `policies/` imports `OVERLAY_MAP` directly.

## Phase 3 — Compliance = flags, not decisions (FR-SOP-3, FR-SOP-4)

`check_compliance()` evaluates threshold rules (minimum DSCR, max leverage, debt-yield floors, normalized-NOI minimums) into pass / fail / exception `ValidationFinding`s carrying the Wave 2a severities. It never emits a disposition; FR-SOP-3 is explicit that these are flags for the approver, not decisions.

Deviations route through the landed `Correction` path: required rationale, author, timestamp, superseded value (FR-SOP-4, RMA's "well supported and explained" rule). Wire `check_maker_checker_roles` as the approval gate on the override, reusing the cl.am.005 authority pattern `promote_spread` already uses.

Acceptance: a capped add-back exceeding its cap yields an exception finding citing policy id and rule id; an override without rationale is rejected; an override with rationale produces a new package layer and re-propagates downstream (existing `apply_corrections` behavior, asserted not rebuilt).

## Phase 4 — `interpret()` into the review surface, and version pinning (FR-SOP-5)

- `interpret()` on a flagged cell returns the clause-level citation plus that cell's SCOA mapping and adjustment provenance, reusing `resolve_source_region` for the source side. This is the "why was this value treated this way" answer behind FR-HIL-2's click-through.
- Policy version pinning: every spread records the resolved policy-set version that produced it. Check whether `SpreadPackage` already carries anything usable before adding a field; if it does not, add one field, populated at resolve time.

Acceptance: interpreting the capped add-back from Phase 3 returns the cap clause citation and the cell's derivation chain; a `SpreadPackage` produced after this phase answers "which policy version produced you."

## Phase 5 — Staleness and the gold case

- `detect_staleness()` over policy effective dates; a spread pinned to a superseded policy version is flagged.
- One gold case asserting the full ladder end to end: RB deal with a special-instructions file overriding one threshold — correct precedence order, the exception flagged with the right severity, the override carrying rationale, the version pinned. Register it beside the existing gold cases so regression covers the whole FR-SOP surface in one fixture.

Acceptance: the gold case passes; deleting the special-instructions file from the fixture changes resolution order and the assertion catches it.

## Phase 6 — Route the existing policy surfaces through the expert

The three surfaces in the grounding note all read the registry or pack YAML directly. This phase makes them read through `CiSpreadPolicyExpert`, so what the UI shows is what the runtime resolves — and adds the two things no surface shows today: precedence and conflicts.

- **Concepts tab (`ui/concepts_view.py`).** The Concepts tab is where the PolicyExpert concept lives — it already presents the platform/domain assembly story. Add a resolution view to the domain layer: the resolved policy set in ladder order (scope badge, effective date, the existing doc→object provenance rendering), conflicts, and the pinned policy-set version. Because `concepts_view` is shared across scenarios and degrades gracefully, take the expert (or its resolution result) as an optional input — scenarios without a policy expert render exactly as today. This is also the seam that lets other scenarios populate their Concepts tab the same way later; keep the rendering generic (resolution result in, rows out), with nothing ci-specific in `ui/concepts_view.py`.
- **Docs & Policies tab (demo tab 7).** `render_docs_and_policies` currently receives `credit_policies=list(CI_REGISTRY...)`. Feed it the expert's resolution instead, so the list carries precedence order and scope; keep `extracted_policy_ids` for the stub/extracted badging it already does.
- **Covenants tab, Policy sources expander.** Keep it; it already tells the advisory-vs-Governor story. Add the "why" affordance here and on policy-driven findings: `interpret()` renders the clause citation and the cell's derivation. Coordinate with `plan_JACI_CL_GOVERNED_LAYER_UI.md` Phase 2 (review queue rendering) — whichever lands second wires into the other's surface; do not build two queues.

Acceptance: the Concepts tab lists the resolved set in ladder order with the RB overlay visibly narrowing core when the RB program is selected, and non-C&I scenarios' Concepts tabs render unchanged; tab 7's policy list shows precedence and scope; clicking "why" on a policy finding shows the clause citation.

Adjacent scope, named so it is not lost: populating the Concepts tab for the other scenarios (AML, CRE, insurance diligence, KYC) to the C&I standard is a separate plan — the generic-input seam above is this plan's contribution to it.

## Sequencing

Phases 0–2 are one sitting. Phase 3 is the largest real work and gates Phases 4–5. Phase 6 can land any time after Phase 2 but reads better after Phase 4, when "why" has something to say. Each phase leaves the demo runnable.
