# plan_BLUEPRINT_UMBRELLA_OVER_PACKS: a named, versioned composition above domain packs and assistant packs

Author: Virendra Mehta
Status: proposal, nothing built.
Written: Oct 6, 2026, 5:39 PM PDT, against `japes` `255bcb8d`.
Audience: the Claude Code sessions working on pack availability in Plato.

## 1. The problem

"Pack" means two things in code today: a domain pack (policies, profiles, conductor, evaluation; `pack_manifest.yaml`) and an assistant pack (an `AssistantManifest` plus `profile/`; `manifest.yaml`). A deployable solution such as Acra DSCR needs both, and later an overlay, handoff contracts and a deployment profile. Nothing names or versions that set. The Commercial Lending corpus calls the design document for such a set a "solution blueprint" (SBP-00 to SBP-05) but specifies no runtime object for it.

## 2. What the code does today (read in the working tree)

- Two manifest names, `pack_manifest.yaml` and `manifest.yaml`, in `jazzx_sdk/pack/store.py` (`MANIFEST_NAMES`). `is_assistant_manifest` is simply `"assistant_id" in manifest`.
- A directory holding both manifests is refused by the seed sweep: "keep only the manifest for the role this pack serves". With an assistant manifest present, the domain manifest is not archived.
- Domain pack `dscr-core` (`plato/data/seed_packs/dscr_core/pack_manifest.yaml`): policies, profiles, an `investigation_loop` conductor, `autonomy_ceilings: default: 1`, one human checkpoint, and `governance_chain: aba / jap / overlay: DEFERRED`. No assistant.
- Assistant pack `acra-dscr-core` (`plato/data/sample_packs/acra-dscr-core/manifest.yaml`): one skill, `autonomy_level: l0_assist`, `pack_id: acra-dscr-core`, `pack_version: 1.1.0`, `pack_version_range: '>=1.0'`. Nothing in it refers to `dscr-core`.
- `AssistantManifest.pack_id` plus `pack_version_range` is meant to bind an assistant to a domain pack; `resolve_pack` in `jazzx_sdk/manifest/loader.py` checks existence and the version range. In the sample, `pack_id` is the assistant bundle's own store key, so it points at itself. I did not verify whether Plato calls `resolve_pack` at activation.
- `plato/data/demo_pack` (clinical intake) is an assistant pack that also carries `policies/core.yaml`, with `pack_id: clinical-intake-core`. It works as one merged pack.
- `jazzx_sdk/pack/activation.py` already composes a tenant's registries from a comma-separated list of `tenant/pack_id/version` pins (`parse_pack_reference`, `with_pack_reference`).
- Published versions are immutable; republishing the same version returns 409 (workshop runbook).

## 3. Reference from the corpus and project docs

Commercial Lending Corpus v1.0 narrowing chain: Domain Pack, then Surface Binding Annex, then Certified Client Overlay, then Execution Profile, each only narrowing the one above. The commercial lending suite is two packs (`cl_of`, `cl_sp`), 13 surface bindings, two cross-pack handoff contracts and an execution profile. Pack Store Design Rev 2 section 7.4 already gives each layer its own key. `AssistantManifest` is the closest existing thing to a surface binding annex (surface type, autonomy level, action classes, skills, pack reference). The corpus execution profile is probably the same layer the project docs call JAP; unverified.

## 4. Decision: a blueprint table, not an attribute on each pack

| | Attribute on each pack | Blueprint table with member rows |
|---|---|---|
| Change membership | New pack version needed (immutable) | Edit the blueprint only |
| One pack in several blueprints | No | Yes |
| Things belonging to the whole (overlay, profile, handoffs, pins) | No home | Natural home |
| Drift between members | Possible | One record |

Same `pack_id` for both roles is not an option: the store key is tenant, `pack_id`, version, so the two would collide. Roles must differ in the key, not only in the file name.

## 5. Sketch

```
blueprint        (blueprint_id, blueprint_version, domain, segment, client NULL, status, created_at)
blueprint_member (blueprint_id, blueprint_version, role, ref_id, version_range, required)
blueprint_pin    (tenant_id, blueprint_id, blueprint_version, ref_id, resolved_version, pinned_at)
```

Roles: `domain_pack`, `surface_binding`, `overlay`, `relay`, `execution_profile`.

Acra example:

| blueprint | role | ref_id | range |
|---|---|---|---|
| acra-dscr 0.1.0 | domain_pack | dscr-core | >=0.1.0 |
| acra-dscr 0.1.0 | surface_binding | acra-dscr-core | >=1.0 |

Validation at publish: at least one `domain_pack` member; every `surface_binding` member's pack reference is satisfied by a `domain_pack` member in the same blueprint; nothing in a lower role widens a higher one. At activation, ranges resolve to exact pins, stored per tenant, so a run record cites exact versions. `activation.py`'s pin list is the starting point; a blueprint is a named, versioned, validated form of it.

## 6. Order of work

1. Fix the reference: separate "the domain pack I bind to" from "my own bundle key" in `AssistantManifest`; point `acra-dscr-core` at `dscr-core`; fail activation when an assistant binds to nothing.
2. Decide the merged-pack case (clinical intake): allow an assistant pack to carry policies and say so, or split it.
3. Add the blueprint tables and a store protocol alongside `pack_version`, tenant-scoped.
4. Activate from a blueprint, writing pins.
5. Only then add overlay, relay and execution profile member roles.

## 7. Open questions

- Platform versus tenant blueprints: same question as Pack Store decision D2.
- Shared surfaces: the corpus tags the policy, playbook and pricing services and three automations as "shared", owned by neither pack.
- Execution profile versus JAP: confirm they are the same layer.
- Naming: keep `acra-dscr-core` for the assistant, or rename it to make its role obvious.
- Whether `dscr-core` should carry the Acra program grid, or whether the grid belongs in an overlay (corpus guidance puts institution numbers in the overlay).

## 8. Not verified

Plato's activation path, the `jaci` repo's pack layout, and whether any other repo names the domain pack `acra-dscr-core`.

## 9. Decisions (user, 2026-10-06)

1. **Customer-first.** The customer's packs are the primary objects: `acra-dscr-policy` and
   `acra-dscr-assistant`, whole and immutable, runnable with no composition step. Policy is
   customer-specific too (overlay numbers, learnings stay in it).
2. **Role suffixes `-policy` and `-assistant`** for the two kinds; the customer is the prefix.
   Generic ones, `dscr-core-policy` and `dscr-core-assistant`, exist only once a core is extracted.
3. **Composed packs carry provenance.** Each rule, threshold and skill records its origin
   (`core@version`, `overlay`, `customer`) and the core version it was composed from. The overlay
   is stored separately only when a core exists to layer it on.
4. **The core is extracted later**, from two or more customers' packs (JTBD compare and
   `rule_repeated_across_programs` show what is shared), not designed up front.
5. **The blueprint names the set** (policy, assistant, optional core reference) and does not compose.
   Rebasing a composed pack onto a newer core is an operation that yields a new composed version
   and a diff; provenance shows which customers are behind.

Open: whether rules, thresholds and skills have a field for an origin (believed not; a new field).
Order of work is unchanged, with step 1 (the assistant's reference to its policy pack) first.

## 10. Built (2026-10-07, v2.6.2)

- **Renames.** Seed `dscr-core` is `acra-dscr-policy` (directory `acra_dscr_policy`, version
  `0.2.0`: the old `0.1.0-draft` is not a PEP 440 version, so no range could select it). The sample
  assistant `acra-dscr-core` is `acra-dscr-assistant`. Old ids are not rewritten in a database: a
  tenant that published `dscr-core` still reads it, and a fresh tenant simply never has it. Nothing is
  retired. jaci changes every pin and reference of `dscr-core` to `acra-dscr-policy`, and of
  `acra-dscr-core` to `acra-dscr-assistant`.
- **Tables** `blueprint`, `blueprint_member` (one row per role; roles `policy`, `assistant`,
  `core`), `blueprint_pin` (migration 0025), tenant in every key. A blueprint version is immutable.
- **Validation at publish** (`jazzx_sdk.pack.blueprint`): one policy member, at most one assistant and
  one core, every required member resolves to a live version of the right kind (a domain pack for
  policy and core, an assistant pack for assistant), the assistant's `policy_pack_id` is the policy
  member, and the policy's resolved version satisfies the assistant's `policy_pack_version_range`.
- **Activation** resolves each range to the newest live version, activates core, policy, assistant
  through the pack activation route's own path, then writes the pins. A member that fails stops the
  rest and nothing is pinned.
- **Surface**: `GET/PUT /blueprints`, `POST /blueprints/{id}/{version}/activate`, client
  `blueprints`, `blueprint`, `put_blueprint`, `activate_blueprint`, CLI `blueprints`, `blueprint`,
  `blueprint-activate`, a "Solution blueprints" section on the packs page, and the seed blueprint
  `acra-dscr` that `POST /packs/initialize` publishes (with the sample assistant when it is missing).
- Run records cite the pins: a case run (`plato_blueprint` on its input), a chat or skill turn
  (trace metadata) and an assessment (answer) carry the blueprint id, version and every member's pin
  when the latest activation pinned exactly the pack version used.
- Non-PEP 440 pack versions are refused at publish (422); existing ones satisfy no range.
- Open questions of section 7 stay open.
