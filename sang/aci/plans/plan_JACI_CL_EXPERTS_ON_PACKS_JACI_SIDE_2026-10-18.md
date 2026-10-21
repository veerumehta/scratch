# CL Experts on packs, jaci side: anchor check and ordered steps (plan only)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-10-18. Nothing built. Routes `/Users/sangit/src/japes/docs/plans/plan_JACI_CL_EXPERTS_ON_PACKS.md`
(read in full; "the plan" below) to jaci. Checked at jaci HEAD `030eb83` on `dev`, japes checkout on `v2.6.4`.
User decisions carried in: no version bumps (ignore every bump line, fold into the version in progress); an
Expert is a `SurfaceBinding` with `surface_type=API_SERVICE`, not a new `ExpertBinding` record; forum
definitions (id, kind) go in the pack, members stay a placeholder for the Overlay; commits only, never push.

## 1. Anchors: what held, what drifted

Held at HEAD:
- `CREPolicyExpert(DefaultPolicyExpert)` at `cre_underwriting/experts/policy.py:24`, `pack_id="cre-underwriting-core"` at `:35`.
- `commercial_lending/policies.py`: `document_checklist_policy` `:409`, `covenant_policy` `:457`, `assess_package` `:498`
  (docstring says advisory, "the PolicyExpert pattern, not a gate", `:503`).
- `promotion.py`: `affirm_spread` `:56`, `promote_spread` `:97`, `override_spread` `:152`, `build_effective_view` `:186`;
  `tests/unit/test_promotion.py` exists. `spreader`, `normalize`, `addback_library`, `metrics_catalog` all present.
- Packs under `config/packs/`: `cre_underwriting_core` (manifest, `policies/cre_policies.yaml`, evidence types, metrics,
  mode_tuning, schemas, fixtures), `ci-spread-core`, `cl_of_core` (manifest + `pipelines.yaml` only), `cl_sp_core` (manifest only).
- `pyproject.toml:29` pins `japes[server,documents] @ ...@plato`; `_version.py` and pyproject read 0.20.8.
- japes side: `AuthorityMatrixV2.from_records` (`fabric/canonical/authority.py:124`), `SkillRegistry`
  (`agents/interactive/registry.py`), `resolve_effective_autonomy` (`authority/resolver.py`), `DefaultPlaybookExpert`,
  `DefaultPolicyExpert`, `SurfaceBinding` (`fabric/canonical/profiles.py`), `SurfaceType.API_SERVICE`.

Drifted or wrong:
1. **The plan's "reuse `CREPolicyExpert` for the origination Pack" is not what cl_of_core does.** Both CL manifests already
   have an `experts:` block, an interim reuse of the C&I classes (`ci_spread.experts.policy.CIPolicyExpert`,
   `ci_spread.experts.playbook.CIPlaybookExpert`, `output_classification: GUIDANCE_REFS`, `diagnose_map.yaml`). P1 replaces
   that block; it is not a first declaration.
2. **Pack ids are hyphenated.** The manifests say `cl-of-core` / `cl-sp-core`; the directories are `cl_of_core` / `cl_sp_core`.
   The plan's `GET /packs/cl_of_core/experts` would need the hyphenated id. `cre-underwriting-core` is the same.
3. **`CLPlaybookExpert` already has a close cousin.** `CIPlaybookExpert(DefaultPlaybookExpert)` exists
   (`ci_spread/experts/playbook.py:56`) and reads a `diagnose_map.yaml`. A new class is probably unnecessary.
4. **"`plato packs check`" is not a command I can find.** The check is `jazzx_sdk.pack.check.check_pack_archive`, the client's
   `check_pack`, or the publish scripts. Acceptance wording should name one of those.
5. **`pack/correction_cases.py` already exists in japes** (landed in v2.6.2, `739531a5`). P4's "until P6 lands, as pack
   fixtures" is stale in part: the corrections-dataset shape is real now, though it is built for approved rule
   corrections (a case per correction record, scored by `correction_scorer`). It fits a "corrected rule" case, not an
   "answer must say X" case; the Expert scorers P4 names do not exist yet.
6. **The two japes plans it depends on are not on disk.** `plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT.md` and
   `plan_JAPES_2_8_0_SUPERVISION_COORDINATOR_AND_DOWNGRADE.md` are not in japes `docs/plans`, so the three scorers, the
   answer envelope and `jazzx_sdk.authority.supersession` are unspecified. There is no `supersession` module (authority/
   has context, delegation, resolver). Expected, since they are being planned.
7. **No forum concept in the SDK.** `grep` finds none under `jazzx_sdk`. A forum definition in the pack has no consumer yet.
8. **The manifest has no typed home for owner, version or effective date on a playbook.** `playbooks:` entries are free
   dicts (`asset_id`, `path`, `title`, `type`, `applies_to`, `sme_review_status`, `authored_by`); the loader reads `asset_id`
   and `path`. Whether lint tolerates extra keys is unverified. See P2.
9. **`ClientOverlay` narrows by autonomy only** (`autonomy_narrowings`, `enumerated_allowances`, `extra` for `asset_pins`).
   It has no "certified range" to refuse an out-of-range value at load, so the plan's P3 acceptance ("an Overlay value
   outside the certified range is refused at load") needs either an SDK change or a jaci-side check; and the pack takes a
   single `client_overlay:` path, so "a second Overlay with a different DSCR floor" is two files and a way to pick one.
10. `cl_sp_core` has no policies, playbooks of its own, or registers; "authority matrix rows" and "evidence catalog" have no
    existing file to extend in either CL pack.
11. The deck (slides 13, 28-32, ...) is not in this repo or the shared plans folder. The only figures I can source are the
    ones the plan text itself states (below). The Northgate name appears only in the web demo's sample data
    (`web/commercial-lending-demo/.../LoansInProgressPage.tsx`: "Northgate Lofts - Refinance", $33.1M), not in any pack.

## 2. What can be built now, in order

No SDK change, data and fixtures only. Each step is its own commit; nothing is pushed.

**Step 0 - Settle the sources (no code).** Ask for the deck, or the text of: credit policy v7 (sections 4.2, 5.3), the
stress library v3.1, the interpretation note v2.1, the playbook v4.0/v4.1/v4.2 steps, and the slide 70 roles. Without them, every
number is `pending configuration`. The plan states these figures, which I can use with the slide cited: $2,904,240 scheduled rent
(slide 53), DSCR 1.25x on net cash flow at the note rate (slide 16) with a 1.20-1.25x benchmark labeled a benchmark, 70-75% LTV,
the $10M-$25M DSCR exception band (slide 70). Everything else stays unfilled.

**Step 1 - P2a: governed assets as pack files.** In `cl_of_core` (origination) and `cl_sp_core` (servicing) as the plan binds them:
- `policies/` : credit policy v7 as a canonical `Policy` with sections 4.2 and 5.3 as rules, effective-dated; thresholds not in a
  source carry `pending configuration` and are not evaluable (never a guessed number). A second file for the interpretation note.
  Reuse `document_checklist_policy` / `covenant_policy` and the CRE policies by reference; do not copy them.
- `playbooks/` : "Rent roll to T-12 reconciliation" v4.0, v4.1, v4.2 as three assets (`pb-...-v4-0` style ids, kind
  `best_practice_sequence`), v4.1 active, v4.2 published and not active, consumed by Investigator and Verifier. The concession step
  is the difference the release report must show.
- Owner and version: carry them as keys on the manifest entries and as a header in each file (e.g. `owner`, `version`,
  `effective_from`), following `ci-spread-core`'s `sme_review_status` / `authored_by` precedent. Verify lint accepts them in Step 1,
  not later.
- `authority_matrix.csv` (corpus column set, loadable by `AuthorityMatrixV2.from_csv`/`from_records`): the DSCR exception tiers
  ($10M-$25M) and the slide 70 roles; cells not in a source are omitted, not invented.
- Evidence catalog for expense treatment and the rent roll to T-12 tie-out, as `evidence_types.yaml` entries.
Acceptance: the pack check passes on both packs (use `check_pack_archive`); every asset has an owner and a version; a test builds
the v4.1 -> v4.2 difference and finds the concession step.

**Step 2 - P3: the fictional bank's Overlay.** One `ClientOverlay` YAML per pack (`client_overlay:` in the manifest):
`overlay_id`, `policy_profile_ref` = credit policy v7, `autonomy_narrowings` for exception approval and agency pre-review, DSCR
floor 1.25x and the tie-out tolerances under `enumerated_allowances`, role mapping and the playbook activation (`v4.1` active,
`v4.2` published) under `extra.asset_pins`. The overlay narrows only. A second overlay (DSCR floor 1.30x, say) lives beside it as a
test fixture. Two things need a call before this step is more than a file (Q2, Q3): where "certified range" is defined, and how a
pack selects among overlays. Forum: define `forum` (id, kind) in the pack's own YAML as plain data and leave `members: []` in the
Overlay; nothing reads it until the SDK does.

**Step 3 - P4: the cases as pack fixtures.** Under `config/packs/<pack>/fixtures/cases/` (or `tests/eval/gold_cases/cl_experts/`
if a CL gold dir fits better), one JSON per case with `input`, `expected` (answer text constraints, citations by asset id and
version, `conflict_unresolved` where stated) and `kind` (gold | edge | regression): roof invoice (3), rent roll bridge (3),
DSCR with the four stress scenarios and the v3 -> v3.1 stress-library flag (2), reserves conflict with the agency guide (1),
approval-sounding answer (1). A plain pytest asserts each fixture is well-formed and that every cited asset exists at the cited
version. The cases do not run an Expert yet; they are the acceptance data for P1.

**Step 4 - report back with what the data did not settle.**

## 3. Waits for the SDK

- **P1** (Experts as `API_SERVICE` surfaces, one binding per pack, advisory on every cell, the three scorers): needs japes 2.7.0 P1/P2.
  Jaci side when it lands: replace the interim `experts:` blocks in both CL manifests, add the `SurfaceBinding` YAML (`surface_type:
  API_SERVICE`, `pack_id`, `autonomy_ceilings` all advisory, `out_of_scope_action_classes` including connectors), keep the pricing
  service out of it, and decide whether `CIPlaybookExpert` is reused or subclassed.
- **P5** (supersession over the SDK primitive): needs 2.8.0 P1. `promotion.py` and `test_promotion.py` stay untouched until then.
- **P6** (workshop path) depends on P1 and a Plato with both packs activated.

## 4. Questions

- Q1. Where do the deck, or the source text for the governed assets, live? Without them Steps 1-3 write structure and
  `pending configuration`, not content.
- Q2. Is a "certified range" a japes concept still to be built (2.7.0 P2?), or should jaci check Overlay values against a range
  declared in the pack?
- Q3. One overlay per pack, or several selectable (the plan's second-bank test)?
- Q4. Do the CL packs keep their hyphenated ids (`cl-of-core`) with underscored dirs? The plan's route examples assume otherwise.
- Q5. P4 data: pack fixtures now (as above), or wait for the Expert scorers so the cases can be written against their input shape?

## 5. Guardrails kept

Nothing under `jazzx_sdk/` changes. No new spreading engine. No invented numbers. No version bump. Commits only; the user pushes.

## 6. Decisions relayed by opus-xrepo, 2026-10-18 (not yet confirmed by the user in this session)

- Plan order approved: steps 0-3, data only, one commit each; P1 and P5 wait for the SDK. No version bumps. Commits only.
- Q1: the deck is the user's. Source text (policy, note, playbook) or its path comes from the user; until then everything not
  in the plan text is `pending configuration`.
- Q2: "certified range" is not defined anywhere in the SDK. Define it as pack data in the tenant's pack and check it jaci-side
  at load (refuse an out-of-range value). **SDK gap, noted:** no certified-range type; revisit when a second consumer needs it.
- Q3: a published pack is keyed (tenant_id, pack_id, version) and the complete pack is the customer's own; there is no
  base/derived mechanism and none is to be built. The fictional bank is one tenant's pack (data), not a copy of another's;
  "a second overlay gives a different answer" is tested by loading a second pack/overlay path in a test. Core and seed packs hold
  no customer knowledge (no forum members, no customer thresholds).
- Q4: keep the hyphenated pack ids; the plan text was wrong.
- Q5: write the P4 cases as pack fixtures now, with the well-formedness test; scorers come later.
- Forum: definition (id, kind) and members both live in the tenant's pack data; core packs ship the forum with members empty.
  (This supersedes section 2's "members: [] in the Overlay".)
- The japes 2.7.0 and 2.8.0 plans are in `/Users/sangit/src/japes/docs/plans`, not jaci's `docs/plans`. Correction to drift item 6
  (they were looked for in the wrong folder); not yet read.

## 7. What the japes plans say that changes the jaci data shapes (read 2026-10-18)

Read from `~/.scratch/sang/ape/plans/` (the japes shared folder; the user pointed there): `plan_JAPES_2_7_0_...`,
`plan_JAPES_2_7_1_KNOWLEDGE_LOOP_CHANGE_CLASSES.md`, `plan_JAPES_2_8_0_...` and sonnet-runtime's `plan_expert_surface_pilot.md`
(P1 envelope, P2 route, P5 Governor guard; user decisions applied there: attestation key per deployment with a `key_id`, no version
bump, `SurfaceBinding` reused, forum membership not part of that work). Drift item 6 is withdrawn: the plans exist, in the other folder.

Shapes to author against, so Step 1 data does not need rework:
- **Governed assets are `GuidanceAsset`s in the SDK** (`fabric/guidance/schema.py:52`): `asset_id`, `asset_type`, `version`
  (a **content hash**, derived when empty), `supersedes`, `guidance`, `trigger_patterns` (min 1), `applicability` (pack-defined
  dims), `rationale`, `status` (draft -> approved -> deployed), `expires_at`, `review_at`, `provenance`, `pack_id`, `metadata`.
  There is no `owner` or effective-from field yet; 2.7.1 P5 adds `owner` and `consumed_by_modes` and a closed `GuidanceKind`
  (`interpretation_note`, `decision_rubric`, `best_practice_sequence`, `reviewer_checklist`, `scenario_library`, ...).
  So a human release label ("v2.1", "v4.1") cannot be the SDK version: carry it as a `release_label` in `metadata` (or
  `applicability`), keep `version` for the hash, and put `owner` in `metadata` until the field exists.
  The interpretation note "Recurring versus one-time expenses" is a `GuidanceAsset` of kind `interpretation_note`; the playbook
  is `best_practice_sequence`, `consumed_by_modes: [investigator, verifier]`.
- **Playbooks live in two places today:** manifest `playbooks:` entries (markdown files; the loader reads `asset_id` and `path`)
  and `GuidanceAsset`s. Which holds "Rent roll to T-12 reconciliation" v4.0/4.1/4.2 is a decision for Step 1 (Q6); the manifest
  entry is the existing, simpler path, and the 2.7.1 K5 label gap says the Playbook Expert cannot yet filter by stage or
  decision class either way.
- **Change classes (2.7.1 P1):** every superseding version carries a `change_class` (administrative, minor_narrowing,
  minor_behavioral, material_behavioral, boundary_widening, emergency), and none is waivable. The v4.1 -> v4.2 "concession step"
  is the example of a behavioral change; record the class on v4.2 (material_behavioral is my reading; the user or the owner
  should confirm).
- **Forum:** `ForumRecord(forum_id, pack_id, kind, members)` in the pack manifest (2.7.1 P2). Per the relayed decision the
  definition and members both go in the tenant's pack data, and core packs ship it with members empty. The fictional bank's
  tenant pack is where the members would live; with no source for names, `members: []` there too, marked pending configuration.
- **Cases bind per asset (2.7.1 P6):** `pack/correction_cases.py` cases gain `asset_refs` (asset id and version) and `case_kind`
  (gold | edge | regression). P4 fixtures should use those field names now: `case_kind`, `asset_refs: ["<asset_id>@<release_label>"]`.
- **Citations (2.7.0 / pilot P1):** `GuidanceReference` key is `pack_id:asset_id@version`; the well-formedness test should
  resolve citations in that form. `ExpertAnswer` requires at least one reference unless `conflict_unresolved`.
- **Supersession (2.8.0):** generalises jaci's `promotion.py`; that file is not touched until then.

New questions: Q6 - playbook versions as manifest `playbooks:` entries or as `GuidanceAsset`s? Q7 - confirm
material_behavioral as v4.2's class (the owner's call).

## 8. Status, 2026-10-18: Steps 1-3 done (three commits on `dev`, unpushed)

- `d82f726` Step 1: pack `workshop-bank-cl-of` (`config/packs/workshop_bank_cl_of/`): manifest, credit policy v7 (draft status,
  three rules: 4.2 DSCR floor 1.25x, 4.2 stress scenarios, 5.3 non-recurring support), interpretation note v2.1 (owner Credit
  Methodology), stress library v3 and v3.1, agency guide rows (seed), playbook v4.0/4.1/4.2 as manifest `playbooks:` entries
  (v4.1 active, v4.2 published not active, change_class material_behavioral), authority matrix (3 cells, the final one human-only),
  evidence catalog, a minimal ontology, `pending_configuration.yaml`. Pack check: zero findings.
- `32b6cbf` Step 2: `client_overlay.yaml` on both packs (`workshop-bank-cl-sp` is new: overlay, forums, playbook import), the
  forum definitions with `members: []`, `certified_ranges.yaml`, and `jaci.capabilities.commercial_lending.overlay.load_checked_overlay`
  (refuses a DSCR floor below the policy's 1.25x and an autonomy narrowing that widens a matrix cell).
- `abc5174` Step 3: ten cases under `fixtures/cases/` (4 gold, 3 edge, 3 regression) with `case_kind` and `asset_refs`, and a test
  that every cited asset exists at the cited version.
- Decisions I took, for the user to confirm: Q6 playbooks as manifest entries (not GuidanceAssets); Q7 v4.2 as material_behavioral;
  the pack ids `workshop-bank-cl-of` / `-cl-sp` are placeholders for the fictional bank's name; the credit policy file is `draft`
  with its authoring date because v7's real effective date is not in hand; the "free month is not bad debt" wording in the
  playbooks is mine and is marked for the owner to confirm; v4.0 and v4.1 are identical bodies (their difference is pending).
- Not done: no source text was given, so every figure beyond the plan's own is `pending configuration`; "a second overlay gives a
  different cited answer" is only tested as a different loaded floor, since no Expert runs until P1; P1 and P5 wait on the SDK.

## 9. P7, noted only (opus-xrepo, 2026-10-19; not built)

Added to the routed plan and to `addendum_JACI_CL_EXPERTS_roadmap_alignment.md`: a generalization test on financial crime. Bind the
Policy Expert to `config/packs/aml_investigation_core` in the four-binding shape (AML, Sanctions, KYC/CDD, Fraud) with one cross-Pack
contract hosted on the AML binding for the Sanctions question, and run the slide 35 partial-name sanctions story as gold, edge and
regression cases (the evidence standard cited to version; "stop and request" on a missing decisive identifier; the "clear to pay"
leakage case). Acceptance as stated there: the same `CREPolicyExpert` shape, subclassed for AML, answers with citations from two packs
and one contract; nothing under `jazzx_sdk/` changes; the three Expert scorers pass.

What I see at HEAD, for whoever builds it:
- `config/packs/` has `aml_investigation_core` (discovery, evidence tools and types, fixtures, mode_tuning, policies, schemas) and no
  Sanctions, KYC/CDD or Fraud pack. Three thin seed packs would be new. Per the relayed decision they are core/seed packs, so no customer
  knowledge in them (no forum members, no customer thresholds).
- It needs P1 and japes 2.7.0 P3 (multi-pack `SurfaceBinding` list and the cross-Pack contract), neither built; sonnet-runtime has
  P3 waiting. The same applies as for the CL packs: the cases can be written as fixtures first.
- The story's source text (evidence standard, the partial-name thresholds) is not in hand; the same `pending configuration` rule applies.
- The jaci pin in `pyproject.toml` moves when the japes phases land (a dependency pin, not release versioning); still no version bump.
