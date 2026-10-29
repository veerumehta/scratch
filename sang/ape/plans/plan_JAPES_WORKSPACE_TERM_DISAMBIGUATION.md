# JAPES - Disambiguate "workspace" from the platform's Builder Studio workspace

Author: Virendra Mehta · 2026-10-29 · Status: draft for review

Written against japes `639c8e88` (2026-10-28), read from the working tree. Every anchor below was read, not inferred. If an anchor has moved, fix the anchor, not the design.

## 0. TLDR

The platform is settling "workspace" as the Builder Studio change-set (a draft overlay on a tenant's base, promoted by review and merge). The platform multi-tenancy design (Design Documents, "Platform Multi-Tenancy: Technical Deep Dive (v2)", DEC-1, DEC-7) makes `sub_tenant_id` the only scope column below tenant and bans new `workspace_id` columns, claims or headers.

The SDK uses "workspace" for four unrelated things and one field. None of the four means a change-set.

**Scope of this plan: B, C and D only.** These are SDK-internal names that don't depend on any platform decision. A and E touch shared vocabulary (the surface-type glossary and the scope below tenant) and are **held** until the platform clarifies its terms. Their sections stay below as the ready design, marked HELD; Claude Code must not implement them.

| # | Today | Meaning | Change | Status |
|---|---|---|---|---|
| A | `SurfaceType.WORKSPACE = "workspace"` | Interactive human surface (W1/W2 style) | New canonical value; old value accepted on read | **HELD**: needs D1 and platform glossary |
| B | `EvidenceWorkspace` | Named evidence mounts for one adjudication segment | Rename class, keep deprecated export | **In scope** |
| C | chat turn `workspace=` / `turn.workspace` / `ChatError(stage="workspace")` | Per-turn async resource | Rename param and attribute, keep deprecated kwarg | **In scope** (D2 consumer check first) |
| D | `ground_workspace`, `workspace_root` | Per-turn temp directory | Rename | **In scope** |
| E | `FeedbackOriginV1.workspace_id` | Platform scope below tenant | Rename to the platform's final term | **HELD**: needs the sub-tenant naming answer |

While A and E are held: do not add any new use of "workspace" in SDK code, manifests, errors or contracts, and do not add `sub_tenant_id` anywhere yet.

Out of scope: `tenant`. SDK and Plato usage of tenant (customer partition key, `X-Tenant-Id`, required when deployed) already matches the platform definition. Two small tenant notes are in §7.

## 1. A - SurfaceType.WORKSPACE (HELD, do not implement)

### 1.1 Where the value lives

Code and authored files:

- `jazzx_sdk/manifest/surface_types.py:14` defines it; `:27` puts it in `CONVERSATIONAL_SURFACES`.
- `jazzx_sdk/manifest/spec_binding.py:39` surface defaults; `assistant_manifest.py:42` field `integration_surface: SurfaceType`; `fabric/canonical/profiles.py:300` `SurfaceBinding.surface_type`.
- `pack/blueprint_chain.py:185` writes `b.surface_type.value` into its output.
- `plato/wiring/local.py:144`.
- Pack manifests: `plato/data/demo_pack/manifest.yaml:11` and `plato/data/sample_packs/{pulte-home-mortgage-core,acra-dscr-assistant,acme-clinical-intake-core,mesa-cre-spread-core}/manifest.yaml`; `tests/fixtures/manifest_binding/manifest.yaml:12`.
- Tests: about 20 call sites pass `SurfaceType.WORKSPACE`; `tests/test_assistant_primitives.py:33` asserts the full value list; `:127`/`:144` round-trip `"workspace"`.

Persisted, outside our control once written:

- `jazzx_sdk/manifest/store_db.py:49` `manifest_json` (written at `:119` from `model_dump(mode="json")`, read at `:61` with `model_validate`).
- Published pack archives and manifest-only rows in `jazzx_sdk/pack/store.py` (sha256 over archive bytes or manifest).
- Pack drafts in `jazzx_sdk/pack/draft_db.py` (draft files and draft events; Plato migration `0024` digests event text).
- Pack repos outside japes that author `integration_surface: workspace`.
- `js/`, `ui/`, `jazzx_plato_client/`: no occurrences found.

### 1.2 Decision D1 - the new value

Recommended: `WORKBENCH = "workbench"`. One word, an established term for an interactive professional tool ("analyst workbench"), and no collision with workspace, sub-tenant, tenant or project. Business display names ("Loan Application Workspace") are unaffected: they are surface names, not the type.

Alternative: `CASE_WORKSPACE = "case_workspace"`. Keeps the deck word but still invites "which workspace". W2 is asset-centric, not case-centric, so "case" is also slightly wrong.

The plan below uses `workbench`. If D1 lands elsewhere, substitute the value; nothing else changes.

### 1.3 Change

1. `surface_types.py`: add `WORKBENCH = "workbench"` as the canonical member. Redefine `WORKSPACE = "workbench"` directly below it so it becomes an Enum alias (`SurfaceType.WORKSPACE is SurfaceType.WORKBENCH`). Existing code keeps working with no edits.
2. Same file: add `_missing_` that maps the string `"workspace"` (case-insensitive, stripped) to `WORKBENCH` and emits one `DeprecationWarning` per process naming the legacy value. Every reader (`model_validate`, YAML loaders, `SurfaceBinding`) goes through Enum construction, so this is the single read-path alias. Do not add per-loader aliasing.
3. `CONVERSATIONAL_SURFACES` and `spec_binding.py:39`: reference `WORKBENCH`. Behaviour unchanged because the alias is the same member.
4. Writers emit the canonical value only. `model_dump(mode="json")` already emits `.value`, so new DB rows and `blueprint_chain` output say `"workbench"`.
5. Update the five Plato pack manifests and the test fixture to `integration_surface: workbench`. Leave `.plato-pack-cache/` alone (it is generated).
6. Tests: switch call sites to `SurfaceType.WORKBENCH`; update the value list in `test_assistant_primitives.py:33`; add the tests in §1.5.
7. Docs: `docs/ARCHITECTURE.md` and `docs/DOMAIN_PACK_QUICKSTART.md` list `workbench` as the surface type and add one line: "workspace" in platform material means the Builder Studio change-set (a sub-tenant kind), not a surface.

### 1.4 What we must not do

- Do not rewrite stored rows, archives or drafts. No data migration. Stored `"workspace"` keeps loading through `_missing_`.
- Do not change any digest. Draft and trial digests are computed over authored text (`plato/migrations/versions/0024_draft_event_baseline.py:37`) and archive bytes. Verify that nothing digests a re-serialised manifest (check `jazzx_sdk/pack/release_report.py:101` `_digest` and `pack/lint_runs.py:189`). If something does, a stored manifest re-dumped after load would change digest on next save: in that case digest over the stored form, or document that a re-save is a new content version, and stop for review before continuing.
- Do not remove the `WORKSPACE` alias or the `_missing_` mapping in this change. Removal needs: a count of stored rows carrying `"workspace"` (manifest store, pack store, drafts) at zero in every deployed environment, and the external pack repos updated. Add a `TODO(surface-workspace-alias)` at the alias with that condition.

### 1.5 Acceptance

- `SurfaceType("workspace") is SurfaceType.WORKBENCH` and warns once; `SurfaceType("workbench")` does not warn.
- An `AssistantManifest` validated from `{"integration_surface": "workspace"}` dumps `"workbench"`, and `is_conversational` is True.
- A `manifest_json` row written before the change (fixture with `"workspace"`) loads through `store_db` unchanged on disk.
- A published pack archive whose manifest says `workspace` loads, activates and serves; its stored sha256 is unchanged.
- `SurfaceBinding.from_yaml` accepts `surface_type: workspace`.
- Full suite green; `grep -rn '"workspace"' jazzx_sdk plato` finds only the alias line and its test.

## 2. B - EvidenceWorkspace

- `jazzx_sdk/agents/adjudication/workspace.py`: rename the class to `EvidenceScope` and the module to `evidence_scope.py`. Keep `workspace.py` as a one-line re-export module and keep `EvidenceWorkspace = EvidenceScope` exported from `jazzx_sdk/agents/__init__.py:97,151` with a deprecation warning on attribute access.
- `SegmentSpec.workspace` (`segment.py:53`, used at `:679`, `:816-818`; `planner.py:86,103`; `pipelines/steps.py:2008`): rename the field to `evidence`, accept `workspace=` as a deprecated constructor alias.
- `docs/PERMISSION_SELECTORS.md:23` and `examples/adjudication_demo/` (yaml comment, harness, README, test): update names.
- Selector family `mount:` is unchanged.

## 3. C - Chat turn resource

- `pipelines/chat/engine.py`: `workspace=` parameter on the lifecycle runners (`:795`, `:823`, `:896`, `:937`) becomes `turn_resource=`; `workspace=` stays as a deprecated keyword alias. `ChatTurn.workspace` (`:94`) becomes `turn_resource` with a read-only `workspace` property that warns. Internal helpers `_turn_workspace`, `_classified_workspace`, `_HeldWorkspace`, `_workspace_error`, `classify_workspace` are renamed without aliases.
- `runs/chat.py:117` (`ChatTurnSpec.workspace`), `runs/session.py:327-359`, `plato/api/assistants.py:371-616`: follow the rename.
- Error payloads (`engine.py:1485`, `:1503`, `:1517`): `stage="workspace"`, `workspace_acquire_failed`, `workspace_release_failed`, and the `workspace_release` detail key are externally visible. Decision D2: rename to `stage="turn_resource"`, `turn_resource_acquire_failed`, `turn_resource_release_failed`. No consumers were found in `ui/`, `js/` or `jazzx_plato_client/`; confirm with a grep of the mortgage app and Juno before merging, and list the change in release notes.
- `grounding.py:443` reads `turn.workspace`: switch to `turn.turn_resource`.
- `docs/CHAT_LIFECYCLE.md:42-46,124`: update.

## 4. D - Grounding scratch directory

- `pipelines/grounding.py:340` `ground_workspace` becomes `ground_scratch_dir`; keep the old name as a deprecated alias.
- `workspace_root` parameters (`engine.py:1222-1232`, `runs/session.py:327-331`, `GroundingSessions` in `plato/api/assistants.py:367`) become `scratch_root`, with `workspace_root=` accepted as a deprecated keyword. `GROUND_DIR_ENV` is unchanged.

## 5. Order

1. B, C, D together in one PR, tests and docs included. This is the whole of the current work.
2. A, after D1 and the platform glossary are settled.
3. E, after the platform's term for the scope below tenant is settled.

B, C, D acceptance:

- Old names (`EvidenceWorkspace`, `workspace=` kwarg on the chat runners and `SegmentSpec`, `turn.workspace`, `ground_workspace`, `workspace_root=`) still work and each warns once.
- New names are used everywhere inside japes; `grep -rn -i workspace jazzx_sdk plato` finds only the deprecated aliases, their tests, `SurfaceType.WORKSPACE`, and `jazzx_eval_contracts` `workspace_id` (A and E, untouched).
- Error codes per D2 are changed only if the consumer grep in §3 comes back clean; otherwise keep the old codes and leave a `TODO(turn-resource-error-codes)`.
- Full suite green.

## 6. E - FeedbackOriginV1.workspace_id (HELD, do not implement)

`jazzx_eval_contracts/jazzx_eval_contracts/identity.py:60`, with snapshots `tests/schema_snapshots/FeedbackOriginV1.json:68` and `FeedbackSubmissionV1.json:185`. Only internal producer: `jazzx_sdk/evaluation/eval_service_adapters.py:110` (sets `service` only).

This field means the platform's scope below tenant, so it should carry whatever the platform finally calls that scope. The platform term is `sub_tenant_id` today, and we are raising whether that word is right (see §8). Hold until that settles, then:

- Add the new field; accept `workspace_id` on input via a validation alias; emit only the new field; regenerate the two snapshots.
- Add `scope_kind` alongside only if the platform registry exposes `kind`.

## 7. Tenant notes (no change in this plan)

- `jazzx_sdk/llm/turn_cost.py:5,38` and `llm/cost_store_db.py:115` store the tenant in the cost record's `project_id`. The platform decided project is product data, not a scope (DEC-18). Worth a follow-up so cost records carry `tenant_id` explicitly.
- `DEFAULT_TENANT = "default"` (`jazzx_sdk/identity.py:16`) is used only locally; Plato refuses a missing `X-Tenant-Id` when deployed (`plato/wiring/default.py:521-529`). This matches the platform rule of no implicit defaults in deployed environments.

## 8. Open questions for the platform

1. Is "sub-tenant" the right name for a change-set overlay that reads through to base and is promoted or discarded? See the companion note.
2. Does Plato's pack draft (`pack/draft_db.py`: draft, review, merge to published) become a second overlay kind, or stay SDK-local?
3. Which surface-type value does the platform want in shared glossaries (D1)?
