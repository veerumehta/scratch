# plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT - the Expert as a callable, cited, advisory surface

Repo: `japes`. Consumers to check before each phase lands: `jaci` (CRE Policy Expert subclass, CL policies), `jazzx-assistant`.

Author: Virendra Mehta. Written against `japes` HEAD `3647d21a` on branch `v2.6.4` (`_version.py` reads `2.6.4`). Every file and symbol below was read in the working tree at that commit. Source: Deck 4, "Experts, Supervisors, Roles and Reuse", sections 1 to 3.

Read first: `ape/CLAUDE.md` sections 1 to 7, `ape/plans/plan_JAPES_2_5_0_LOCATOR_AND_INVENTORY_DISCIPLINE.md` for the breaking-change discipline, and `ape/plans/plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT.md` for the versioning vocabulary this plan reuses.

## TLDR

The deck defines an Expert as one API/Service surface, bound to one or more Packs, advisory on every cell, that returns a cited, version-pinned answer carrying a trust payload (slides 6, 11, 14, 15). The SDK has the Expert bases, the result models and the mode machinery behind them, and nothing that presents them as a surface: there is no Expert route on Plato, no typed answer envelope, no multi-Pack binding, no caller visibility envelope on the call, and nothing in the Governor that refuses an Expert answer as the authority behind a Decision. This plan adds those five things, additively, so the read-only Expert pilot on slide 42 can be served from Plato against the CRE pack.

## What exists at HEAD (do not rebuild)

- `jazzx_sdk/experts/base.py:27` `OutputClassification` with `GUIDANCE_REFS` ("advisory only; never authority_basis"); `ExpertRequest` (`:52`, `operation`, `context`, `pack_id`, `trace_id`); `ExpertResponse` (`:68`, `success`, `operation`, `result`, `error`, `trace_id`, `metadata`, `output_classification`).
- `jazzx_sdk/experts/policy/base.py`: `PolicyResolutionResult` (`:22`) already carries `applicable_policies`, `precedence_order`, `conflicts`, `stale_policies`, `not_yet_effective`, `policy_versions`; `ComplianceResult` (`:54`) carries `allowed`, `refusals`, `applied_policies`, `rationale`; `InterpretationResult` (`:83`) carries `cited_clauses`, `ambiguities`, `confidence`; `StalenessReport` (`:102`).
- `jazzx_sdk/experts/policy/default.py`: `DefaultPolicyExpert.execute` (`:191`) dispatches `resolve` (`:221`), `check_compliance` (`:317`), `interpret` (`:470`), `detect_staleness` (`:495`). Overlay-aware precedence and GUIDANCE_REFS stamping live here (jaci's `CREPolicyExpert` only wires registry, core ids and overlay map).
- `jazzx_sdk/experts/playbook/base.py`: `PlaybookRecommendation` (`:20`) with `guidance_refs`, `DiagnosisResult`, `ScaffoldResult`, `EffectivenessReport`.
- `jazzx_sdk/manifest/surface_types.py:16` `SurfaceType.API_SERVICE` and `:18` `GATEWAY`.
- `jazzx_sdk/authority/context.py`: `PermissionScope`, `InvocationContext`, `descend()`, `admit_hop`/`check_hop` (the RBAC spec `plan_JDK_RBAC_PERMISSION_SCOPE_AND_PACK_KEYS.md` names its fail-open branch; that spec is still a draft).
- `jazzx_sdk/pack/activation.py:126` `TenantPackRegistries` with `pins_for`, `pinned`, `activate`; `pack/version_windows.py` selects the version by case date with `notes` and `strict`; `pack/guidelines.py` numbered immutable guideline versions `G1`, `G2` with digests.
- Plato `plato/api/packs.py`: `publish`, `activate`, `history`, `active`, `assess`, `release-report`, `diff`. No route mentions an Expert.
- `jazzx_sdk/server/console_api.py:39` lists `catalog.EXPERTS` for the platform page only.

## Five gaps, one phase each

| # | Gap | Deck slide | Phase |
|---|---|---|---|
| G1 | No typed answer envelope: label, attestation, freshness state, guidance refs, evidence-floor reminders, both positions on conflict | 14, 15 | P1 |
| G2 | No Expert route on Plato; Experts are in-process only | 6, 14 "the one door" | P2 |
| G3 | One Pack per request (`ExpertRequest.pack_id` is a single string); no multi-Pack binding, no per-audience binding, no cross-Pack contract | 11, 12, 13; Studio deck step 5 | P3 |
| G4 | No caller visibility envelope on the call; the answer is not narrowed to what the caller may see | 8, 14 rule 5 | P4 |
| G5 | Governor does not refuse a Decision whose `authority_basis` is an Expert answer; "authority leakage" has no scorer | 11 trap 1, 15 | P5 |

## Phase 1 - `ExpertAnswer` envelope (S)

New module `jazzx_sdk/experts/answer.py`. Additive; `ExpertResponse` is unchanged and gains an optional `answer: ExpertAnswer | None`.

```python
class GuidanceReference(BaseModel):      # one citation
    asset_id: str; asset_kind: str        # policy | interpretation_note | playbook | evidence_schema | matrix
    section: str | None; version: str; effective_from: date | None
    jurisdiction: str | None; pack_id: str

class FreshnessState(BaseModel):
    pinned_version: str                   # the version this answer was served from
    newer_published: str | None           # "v4.2 published; not yet active here"
    superseded: list[GuidanceReference]   # cited content that is no longer current
    retired: list[GuidanceReference]

class ConflictPosition(BaseModel):
    source: GuidanceReference; position: str

class ExpertAnswer(BaseModel):
    answer: str | None                    # None when conflict_unresolved is True
    references: list[GuidanceReference]   # min_length=1 enforced by validator: an uncited answer is invalid
    conflict_unresolved: bool = False
    positions: list[ConflictPosition] = []   # required non-empty when conflict_unresolved
    evidence_floor: list[str] = []        # what the caller must still establish
    freshness: FreshnessState
    label: Literal["advisory only - not authority"] = ...
    attestation: AdvisoryAttestation      # signed; see below
    output_classification: Literal[OutputClassification.GUIDANCE_REFS]
```

`AdvisoryAttestation` is an HMAC over the canonical JSON of the answer with the Expert's binding id and `pack_version_set`, keyed by the deployment. It proves the answer came from a bound Expert and was not edited; it does not prove the answer is right (the caller's Verifier attests that, slide 15). Reuse `content_digest()` if the 2.6.0 plan's D2 has landed; otherwise add it beside `content_version()` as that plan says.

Map the existing results into the envelope in `DefaultPolicyExpert.execute`: `PolicyResolutionResult.conflicts` becomes `positions` with `conflict_unresolved=True` and `answer=None`; `stale_policies` and `not_yet_effective` become `freshness.superseded` and a `not_yet_effective` list; `policy_versions` and `cited_clauses` become `references`. `DefaultPlaybookExpert` maps `guidance_refs` the same way.

Acceptance: an `ExpertAnswer` with no references fails validation; a resolution with two conflicting policies yields `conflict_unresolved=True`, both positions, and `answer=None`; a stale citation always appears in `freshness.superseded`; the attestation verifies against the deployment key and fails on any byte change; the existing `tests/test_experts*` suites pass unchanged.

## Phase 2 - the Expert route on Plato (S to M)

`plato/api/experts.py`, mounted beside `packs.py`:

```
POST {prefix}/packs/{pack_id}/experts/{expert}/{operation}      expert in {policy, playbook}
GET  {prefix}/packs/{pack_id}/experts                            which Experts this pack binds, and their operations
```

The route resolves the tenant's activated pack version through `TenantPackRegistries.registries_for` (`pack/activation.py:162`) and the case date through `version_windows` when the caller passes one, so the three-version rule on slide 20 is answered by code that already exists: the pinned version serves, `history` supplies `newer_published`. Read-only: the route has no side effect and must not accept connectors (slide 11 trap 6); a request body naming a connector is a 422.

The route goes through `GovernedRouter` (`server/governed_http.py`) for `X-Trace-Id`; every call emits one `TraceStep` with `output_classification=guidance_refs` and the `VersionBundle` pinned to the served versions.

Add the operation to `jazzx-plato-client` so an outside application can call it with no SDK (slide 14 "the one door"). The Expert route is part of the externally exposed capability set alongside packs, runs, assessments and evaluation; the client package test suite covers it like the others.

There are exactly two Expert routes, `policy` and `playbook`. The Evidence Expert named in older material is a Skill (`jazzx_sdk/skills/evidence`), not a surface; do not add a third route.

Acceptance: a CRE policy question served against the activated version returns an `ExpertAnswer`; the same question with a case date in a `by_case_date` window returns the window's version and names it; a request carrying a connector is refused; the trace step for the call carries `guidance_refs` and the pinned versions.

## Phase 3 - multi-Pack and per-audience binding, and the cross-Pack contract (M)

`ExpertRequest.pack_id` stays for one release and gains `pack_ids: list[str]`. A new `ExpertBinding` record lives on the manifest side next to `SurfaceBinding` (`manifest/spec_binding.py`) and is keyed by Pack and by audience: one binding per Pack (slide 12 "bind to each Pack") and, within it, one envelope per calling surface (the RM co-worker, the underwriter Workspace, an outside application under a service contract). Each envelope declares visibility and the question classes it may ask. An Expert's ceiling is advisory on every cell by construction (slide 14 rule 2), so a per-audience "ceiling" narrows visibility and question classes only; a binding that tries to grant an Expert any autonomy above advisory fails validation. The answer's `references` name the Pack each citation came from (already in `GuidanceReference.pack_id`), and `freshness` is computed per Pack.

A `CrossPackContract` (slide 12, hosted on the anchor Pack's binding) is a declared, versioned record of which questions may cross from one Pack to another; a cross-Pack citation without a contract is refused with a typed `Refusal`, not silently answered. This is the smallest object that makes "the AML Pack may ask, the Sanctions Pack answers" checkable.

Acceptance: an Expert bound to two Packs returns citations from both, each named; the same question from two audiences on one Pack cites only what each audience's envelope admits; a binding declaring a non-advisory ceiling is refused at load; a citation from a third Pack with no contract is refused; the financial-crime story on slide 35 (sanctions policy plus AML evidence floor) runs as a test with both bindings and one contract.

## Phase 4 - caller visibility envelope (S)

The route establishes an `InvocationContext` for the caller (principal, `PermissionScope`, tenant) and the Expert narrows retrieval to the intersection of the caller's scope and every bound Pack's binding (slide 12 "never wider than its narrowest binding"). Depends on the RBAC spec's P2 (require-context middleware) landing in `warn` mode; until then the route refuses when no context is ambient rather than inheriting `admit_hop`'s fail-open branch.

Acceptance: the same question from two callers with different `doc_source:` scopes cites different assets; a caller with no ambient context is refused with `principal_unresolved`.

## Phase 5 - no authority leakage (S)

Two guards. In `modes/operational/governor.py`, refuse any Decision whose `authority_basis` resolves to a `GuidanceReference` or an `ExpertAnswer` (today the Governor does not read `guidance_refs` at all; `rg -n "guidance_refs|authority_basis" modes/operational/governor.py` returns nothing). In the evaluation framework, add three Expert scorers: citation resolution (every reference resolves to an approved version for the case date), freshness (no superseded citation without a warning), and authority leakage (the answer text is classified for decision language; the slide 36 regression case "clear to pay" is the seed). These are the "evaluated as advice" gates on slide 11 block 5.

Acceptance: a Decision citing an Expert answer as its basis is refused by the Governor with a typed reason; the three scorers run in `pack/eval_invoker.py` for any pack that binds an Expert; the "clear to pay" case fails the leakage scorer.

## Decisions this plan does not make

- D1: whether the attestation key is per deployment or per tenant (Plato `tenancy` decides; default per deployment).
- D2: whether `ExpertBinding` is a new record or a `SurfaceBinding` with `surface_type=API_SERVICE`. Recommendation: reuse `SurfaceBinding` and add the per-Pack list; decide before P3.
- D3: how far the RBAC spec has to land before P4; P1 to P3 and P5 do not depend on it.

## Sequencing

P1 and P5's Governor guard first (no route needed, both small). P2 next; it is what the read-only pilot needs. P3 and P4 after, in either order. jaci's `plan_JACI_CL_EXPERTS_ON_PACKS.md` binds the CRE pack to P2 and supplies the gold, edge and regression cases.

## Guardrails for Claude Code

- One phase per session; re-verify every anchor above at HEAD first (`git log --oneline -1`, `rg -n <symbol>`); fix the anchor, not the design.
- Do not change `ExpertResponse` fields; add the optional `answer`.
- Do not add a connector path to the Expert route under any flag.
- Do not widen `content_version()`; add `content_digest()` beside it if absent.
- Commits are fine; do not push.
