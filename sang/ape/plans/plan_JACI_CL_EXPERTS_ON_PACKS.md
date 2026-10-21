# plan_JACI_CL_EXPERTS_ON_PACKS - the two Experts bound to the lending Packs, with the deck stories as cases

Repo: `jaci`. Depends on `japes` plans `plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT.md` (P1, P2) and `plan_JAPES_2_8_0_SUPERVISION_COORDINATOR_AND_DOWNGRADE.md` (P1). Nothing under `jazzx_sdk/` changes for this plan; packs import from japes, never the reverse.

Author: Virendra Mehta. Written against `jaci` HEAD `030eb83` on `dev` (`_version.py` reads `0.20.8`), anchors read at that commit. Source: Deck 4 slides 13, 28 to 32, 41, 42, 51 to 54, 63, 78, 80 and 83.

## TLDR

jaci already has a CRE Policy Expert that is a thin subclass of `DefaultPolicyExpert`, CL document-checklist and covenant policies as canonical `Policy` objects, and the spread affirmation, promotion and supersession path. What the deck asks of jaci is data and bindings, not code: one Policy Expert and one Playbook Expert bound to the origination and servicing Packs (two bindings each), the fictional bank's Overlay, a playbook library with the assets the stories name, and the three Northgate stories plus the CRE sizing question as gold, edge and regression cases. The result is the read-only Expert pilot on slide 42, servable from Plato.

## What exists at HEAD

- `src/jaci/scenarios/cre_underwriting/experts/policy.py:24` `CREPolicyExpert(DefaultPolicyExpert)`, `pack_id="cre-underwriting-core"`, wires registry, core ids and overlay map only.
- `src/jaci/capabilities/commercial_lending/policies.py`: `document_checklist_policy(segment)`, `covenant_policy(segment)`, `assess_package(...)` (advisory, "the PolicyExpert pattern, not a gate", `:503`).
- `src/jaci/capabilities/commercial_lending/promotion.py`: `affirm_spread`, `promote_spread`, `override_spread`, `build_effective_view` with their tests.
- `src/jaci/capabilities/commercial_lending/{normalize,addback_library,metrics_catalog,spreader}.py`: the one spreading engine (slide 80 "one engine").
- `config/packs/`: `cre_underwriting_core` (manifest, `policies/cre_policies.yaml`, `evidence_types.yaml`, `metrics.yaml`, `mode_tuning/`, `schemas/`, `fixtures/`), `ci-spread-core`, `cl_of_core` (manifest and pipelines only), `cl_sp_core`, `aml_investigation_core`, `acra_dscr_policy`.
- `pyproject.toml:29` pins `japes[server,documents] @ git+...@plato`; bump the pin when the japes phases land.

## Phases

### P1 - two Experts, two bindings each (S)

Declare the Policy Expert and the Playbook Expert in `cl_of_core` and `cl_sp_core` manifests as `API_SERVICE` surfaces with one binding per Pack (slide 28 "one Expert, two Packs, two bindings"), both advisory on every cell, no connectors, `evaluation` naming the three scorers from the japes plan. Reuse `CREPolicyExpert` as the Policy Expert for the origination Pack; add `CLPlaybookExpert(DefaultPlaybookExpert)` with the same thin shape. The internal pricing service stays an internal service, not an Expert (slide 63).

Acceptance: `GET /packs/cl_of_core/experts` lists both with their operations; a call carrying a connector is refused.

### P2 - the governed assets behind the stories (M, data)

Author, as pack assets with owners and versions:

- Credit policy v7 with §4.2 (sizing floors) and §5.3 (NOI normalization), effective-dated; the stress library v3.1; the agency guide rows as `pending configuration` seed content (slide 30: a benchmark is labeled a benchmark, a value not in the source is never invented).
- Interpretation note "Recurring versus one-time expenses" v2.1, owner Credit Methodology, scope stabilized multifamily (slide 32).
- Playbook "Rent roll to T-12 reconciliation" v4.1 (and v4.0, v4.2 as prior and published-not-active versions for the slide 20 test), kind `best_practice_sequence`, consumed by Investigator and Verifier (slide 54).
- Authority matrix rows for the DSCR exception tiers ($10M to $25M band) and the roles on slide 70, loadable through `AuthorityMatrixV2.from_records`.
- The evidence catalog for expense treatment and the rent roll to T-12 tie-out.

Acceptance: `plato packs check` passes on both Packs; every asset has an owner and a version; the release report between v4.1 and v4.2 of the playbook names the concession step.

### P3 - the fictional bank's Overlay (S, data)

One Overlay for the fictional bank on each Pack (slide 41): agency programs offered, property types, jurisdictions, DSCR floor 1.25x inside the certified range, tie-out tolerances, role mapping (who approves exceptions per exposure band, who signs agency pre-review), policy profile version v7, activation of playbook v4.1 with v4.2 published and not activated. The Overlay narrows only; `SkillRegistry`'s tier guard and `resolve_effective_autonomy` enforce it.

Acceptance: the Overlay loads; an Overlay value outside the certified range is refused at load; a second Overlay with a different DSCR floor yields a different cited answer from the same Expert with no code change.

### P4 - the stories as cases (M)

Gold, edge and regression cases bound per asset, in the corrections dataset shape (`pack/correction_cases.py` once the japes knowledge-loop P6 lands; until then as pack fixtures):

- Slide 31 (repair add-back): gold, the roof invoice routine scope must come back "operating expense; not excludable" with §5.3 and note v2.1 cited; edge, a mixed invoice must say "split or stop"; regression, a "non-recurring" label alone is never evidence.
- Slide 53 (rent roll bridge): gold, the bridge from $2,904,240 scheduled rent to collections with every line sourced; edge, a partial-period roll or cash-basis T-12 must request evidence, never plug; regression, a free month booked as bad debt.
- Slide 16 (DSCR and mandatory stress scenarios at 70 to 75% LTV): gold, 1.25x on net cash flow at the note rate with the four scenarios, the 1.20 to 1.25x benchmark labeled a benchmark; edge, the stress library changed last week (v3 to v3.1) must be flagged.
- Slide 30 conflict: our policy and the agency guide disagree on reserves; the answer is both positions with `conflict_unresolved`.
- Slide 36 shape, lending variant: an answer that reads like an approval fails the authority-leakage scorer.

Acceptance: all cases pass against the activated versions; the three Expert scorers run in CI for both Packs.

### P5 - supersession over the SDK primitive (S, after japes 2.8.0 P1)

Re-implement `promotion.py` as a binding over `jazzx_sdk.authority.supersession`; keep its tests as the acceptance suite; delete nothing until they pass on the new path.

### P6 - the demo path (S)

A scripted path: ask the three questions through `jazzx-plato-client` against a local Plato with both Packs activated for the fictional bank, show the answer envelope, the freshness notice for playbook v4.2, the conflict case, and one supersession in the effective view. Record it in the demo runbook, not in product code.

### P7 - generalization test on financial crime (S, after P1 and japes 2.7.0 P3)

Bind the Policy Expert to `config/packs/aml_investigation_core` in the four-binding shape from Deck 4 slide 13 (AML, Sanctions, KYC/CDD, Fraud; the latter three as thin seed packs if they do not exist), with one cross-Pack contract hosted on the AML binding for the Sanctions question. Run the slide 35 story (the partial-name sanctions hit) as gold, edge and regression cases: the evidence standard cited to version, "stop and request" on a missing decisive identifier, and the "clear to pay" leakage case. This proves the Expert surface and bindings are domain-neutral, which is what the SDK has to show before a financial-crime suite depends on it.

Acceptance: the same `CREPolicyExpert` shape, subclassed for AML, answers the sanctions question with citations from two Packs and one contract; no code under `jazzx_sdk/` changes; the three Expert scorers pass.

## Decisions this plan does not make

- Whether `cl_of_core` and `cl_sp_core` stay two Packs or fold into the CRE Pack; the deck binds two, this plan follows the deck.
- Whether the fictional bank's Overlay is committed under `config/packs/` or lives on Plato's control plane as a tenant; default `config/` for the pilot.

## Guardrails

- Nothing under `jazzx_sdk/` changes for this plan.
- No new spreading engine: the Playbook Expert returns the method, the engine computes (slide 80).
- Numbers that are not in a source are `pending configuration`, never invented.
- Commits only, no push.
