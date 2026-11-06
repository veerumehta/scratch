# Drift check: the 2.7.0 Expert plan against v2.6.9 code (sonnet-runtime, 2026-11-06)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Read only. Subject: `plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT.md`, written against v2.6.4 (HEAD 3647d21a). Code read: the `v2.6.9` worktree at `2066c67d`
(tree equal to `origin/plato` plus the scorer-context commit). Also read: the 2.7.0 addendum, the 2.7.1, 2.8.0 and 2.9.0 plan headings and TLDRs,
`plan_expert_surface_pilot.md` (the 2.6.5 slice that built part of this plan), and `note_2_7_0_candidates_and_sibling_pass_2026-11-06.md`. "Read" means I opened the file or ran a grep
and saw the line; "inferred" is marked. Nothing was run and no provider was called.

## 1. Result in four lines

- Three of the five gaps are closed or partly closed. G1 (envelope) and G2 (route) shipped in 2.6.5 (`388ba5ad`); the Governor half of G5 shipped in the same commit.
- Still open and still as written: G3 (multi-pack and per-audience binding), G4 (caller visibility envelope), and the three Expert scorers of G5.
- The plan's "What exists at HEAD" is stale in line numbers only; every cited file and symbol still exists. Two statements are now false (no Expert route; the Governor reads no `guidance_refs`).
- 2.7.0 therefore shrinks from five phases to about two and a half. The Expert theme is no longer the big item; its remainder is a pairing with the tenancy and strict-posture work.

## 2. "What exists at HEAD", claim by claim

| Claim in the plan | Still true | Evidence at v2.6.9 | Change needed |
|---|---|---|---|
| `experts/base.py:27` `OutputClassification`, `GUIDANCE_REFS` | Yes, moved | `:31`, `GUIDANCE_REFS` at `:52` (read) | Line number |
| `ExpertRequest` (`:52`), `ExpertResponse` (`:68`) | Yes, moved; `ExpertResponse` gained the optional `answer` | `:56`, `:72`, `answer: ExpertAnswer or None` at `:100` (read). `ExpertRequest.pack_id` is still one string (`:68`) | Line numbers; the "unchanged" guardrail held |
| `experts/policy/base.py` result models (`:22`, `:54`, `:83`, `:102`) | Yes, moved | `PolicyResolutionResult` `:22`, `ComplianceResult` `:59`, `InterpretationResult` `:88`, `StalenessReport` `:107` (read) | Line numbers |
| `DefaultPolicyExpert.execute` `:191`, resolve `:221`, check_compliance `:317`, interpret `:470`, detect_staleness `:495` | Yes, moved. The class is `DefaultPolicyExpert` (`experts/policy/default.py:121`, over `BasePolicyExpert` in `base.py:146`) | `execute` `:195`, `resolve` `:225`, `check_compliance` `:323`, `interpret` `:479`, `detect_staleness` `:504` (read) | Line numbers; `execute` still leaves `answer` unset, `experts/policy/answer.py` `answer_for` builds it (read from the field description, `base.py:100`) |
| `experts/playbook/base.py:20` `PlaybookRecommendation` | Yes | `:20`, `DiagnosisResult` `:38`, `ScaffoldResult` `:57`, `EffectivenessReport` `:73` (read) | None |
| `manifest/surface_types.py:16` `API_SERVICE`, `:18` `GATEWAY` | Yes, same lines | read | None |
| `authority/context.py`: `PermissionScope`, `InvocationContext`, `descend`, `admit_hop`, `check_hop` | Yes, moved | `PermissionScope` `:48`, `InvocationContext` `:123`, `descend` `:164`, `check_hop` `:346`, `admit_hop` `:459`; `require_invocation_context` `:219`, `require_tenant` `:336` exist (read) | Line numbers. Selectors now have a grammar that warns once (`:50`, `:68`) |
| `pack/activation.py:126` `TenantPackRegistries`, `pins_for`, `pinned`, `activate` | Yes, moved | class `:128`, `pins_for` `:146`, `pinned` `:158`, `registries_for` `:164`, `activate` `:204` (read) | Line numbers (`registries_for` was cited as `:162`) |
| `pack/version_windows.py`, `pack/guidelines.py` | Yes | both files exist (read); the route selects through `pack/served_version.py` `select_served_version` (read in `expert_api.py`) | Add `served_version` to the cited code |
| Plato `plato/api/packs.py`: publish, activate, history, active, assess, release-report, diff; "No route mentions an Expert" | The routes yes; the last sentence is false | `plato/api/experts.py` exists (55 lines) and mounts `jazzx_sdk/server/expert_api.py` (251 lines): `GET /packs/{id}/experts` and `POST /packs/{id}/experts/{expert}/{operation}` (read). Mounted at `plato/app.py:301` and in `extra_routes` `:488` | Rewrite: the Expert route exists |
| `server/console_api.py:39` lists `catalog.EXPERTS` | Yes, same line | read | None |
| Governor: "does not read `guidance_refs` at all; `rg` returns nothing" | False now | `modes/operational/governor.py:203` `_advisory_gate` refuses a decision whose `authority_basis` rests on advisory guidance; it uses `authority/advisory.py` (`advisory_entries` `:29`, `advisory_refusal` `:51`). Test file `tests/test_advisory_authority_guard.py` exists (read) | Rewrite; the guard is built |

## 3. The five gaps

| Gap | Status at v2.6.9 | Evidence | What remains |
|---|---|---|---|
| G1 `ExpertAnswer` envelope | Built (2.6.5) | `experts/answer.py`: `GuidanceReference` `:30`, `ConflictPosition` `:46`, `FreshnessState` `:51`, `AdvisoryAttestation` `:61`, `ExpertAnswer` `:72`; label `:82`; attestation optional `:83`; `conflict_unresolved` is derived (`DERIVED_FIELDS` `:23`); an answer with no references and no conflict is refused by validation (`:99`); a conflict needs two positions (`:104`). `experts/attestation.py` holds the keyring; Plato reads `PLATO_EXPERT_ATTESTATION_KEYS` and `PLATO_EXPERT_ATTESTATION_KEY_ID` (`plato/api/experts.py`). Tests: `test_expert_answer.py`, `test_expert_answer_builder.py`, `test_expert_attestation.py` | Nothing in the plan's acceptance. Differences from the plan: the envelope has a `status` (an uncited answer is served without text, test `test_the_other_operations_answer_and_an_uncited_one_is_served_without_text`), and the attestation carries a `key_id`, per the pilot plan. D1 (key per deployment or per tenant) is answered de facto: per deployment, by env |
| G2 Plato Expert route | Built (2.6.5) | See section 2. The request body is `ExpertCall` with `extra="forbid"` (`expert_api.py:45`), so a connector or any other key is a 422; a non-listed operation is a 422 (`:202`); the call writes one trace and changes no pack (test `test_serving_writes_a_trace_the_tenant_reads_back_and_changes_no_pack`). Client: `jazzx_plato_client` `client.py:226` `experts` and `:230` `expert` | Check, not built: whether the trace step carries the pinned version set for every operation (I read the trace construction at `expert_api.py:148-165` but not its fields). Two routes only (`policy`, `playbook`) holds per the addendum, read from the plan; I did not check what the listing returns for a third |
| G3 multi-pack and per-audience binding | Open | `ExpertRequest.pack_id` is still one string. `rg` for `pack_ids`, `ExpertBinding`, `CrossPackContract`, `cross_pack`, `audience` over `jazzx_sdk` returns only `safety/oidc.py`, `fabric/canonical/derived.py`, `authority/context.py`, `authority/principal.py` (unrelated audience claims) (read). `SurfaceBinding` is in `fabric/canonical/profiles.py:294`, not `manifest/spec_binding.py` as the plan says | The plan's D2 was decided by the user (reuse `SurfaceBinding`, `surface_type=API_SERVICE`, with a per-pack list), per the pilot plan header (read). Fix the cited location. The route has no per-audience concept |
| G4 caller visibility envelope | Open | The route has `strict`, `auth` and `identity_required` (`expert_api.py:80`) and `withholding(...)` (`config/posture.py:101`): in a strict posture with no auth and no required identity it withholds. It does not establish an `InvocationContext`, narrow by `PermissionScope`, or refuse with `principal_unresolved` (`rg` for `InvocationContext`, `visib`, `principal_unresolved` in `expert_api.py` finds nothing; read) | The plan's dependency on the RBAC P2 changed meaning: `ServerSettings.require_identity` (`server/app.py:57`, `:177`) adds `SecurityContextGate` (`server/asgi_middleware.py:116`), and `require_invocation_context` exists (`authority/context.py:219`), so the "refuse when no context is ambient" half is now a wiring job. The narrowing by scope is still to build. What is `doc_source:` scoping now: scope claims exist (`scope_claims.py`: `ScopeClaim` `:54`, `with_scope_claims` `:181`, header and token readers `:129`, `:137`), but they are host-declared claims forwarded to services, not retrieval narrowing (inferred from the module summary; I did not read how `DbGuidanceStore` would use them) |
| G5 authority leakage | Half built | The Governor guard is built (above). The three Expert scorers are not: `evaluation/citation_scorer.py` has only `CitationSupportScorer` (`:48`); `rg` for `citation_resolution`, `AuthorityLeak`, `leakage` in `evaluation` and `pack/eval_invoker.py` finds none, and `pack/eval_invoker.py` has no Expert path (read) | Three scorers (citation resolution to an approved version for the case date, freshness, authority leakage) and the invoker path that runs them for a pack binding an Expert |

## 4. What landed since v2.6.4 that touches this plan

Each is a read finding unless marked inferred.

- **Scope claims** (`scope_claims.py`, commits `46fa4296`, `9c3278b4`): identity-bound claims that are forwarded to named clients. They are the natural carrier of an audience or workspace but are not an audience binding. The Expert route does not use them yet.
- **Workspace claim**: PR #101 (home of the claim) is an open decision in the 2.7.0 candidate note; I did not read the PR.
- **Strict postures and `withholding`**: the route already refuses content to an unauthenticated caller in a strict posture. G4's "refuse when no ambient context" is partly met by that for the read route (inferred: it refuses on missing auth, not on a missing principal).
- **`require_identity` and `SecurityContextGate`**: see G4.
- **Run budget, evaluation, guide, sources provenance, identity contextvars**: none changes the Expert plan. The evaluation control plane now gives scorers `context["run"]` (`2066c67d`), which an Expert scorer can use to find the answer a run produced. The Plato guide has an Experts page (`experts_html` in `plato/app.py:514`, `:586`, read) and sources provenance (`source_index`, `resolve_source_ref`) gives a stable citation for a guideline span; whether `GuidanceReference` should carry a `SourceRef` is an open question (section 7).
- **Canonical store strictness** (review fix `e48bd1a4`): the canonical KH reads now raise a denial or an outage. The Expert route's guidance and policy reads go through `DbGuidanceStore` and the pack store, not the KH canonical store (inferred from the factories in `plato/api/experts.py`), so no change there.
- **`content_digest`**: exists (`util/digest.py`), so the plan's D2 note about adding it beside `content_version` is moot; the envelope uses it (`answer.py:119`).

## 5. Overlaps with other planned work

| Planned item | Overlap with the Expert remainder |
|---|---|
| Strict-posture umbrella (idea A in the sibling note, 2.7.0 candidate A) | G4's refusal posture is the same decision as the umbrella: what a strict deployment does with a read that has no principal. Build the umbrella first or the Expert route repeats its own variant (`withholding`). |
| Tenancy model (string versus common's UUID) | The attestation and the route's trace use the tenant string (`TENANT_KEY`, `tenant_of`). A tenancy change touches `expert_api.py` and the trace metadata. A per-tenant attestation key (plan D1) depends on it. |
| Visible trace failure (carried item 28) | The Expert route writes a trace per call. A lost trace there is silent the same way. The fix for item 28 should cover `expert_api.py`'s trace write; I did not read how that write handles a failure. |
| Log purge (carried item 29) | Expert traces are canonical Trace objects in KH; the purge scoping excludes governance records unless opted in. Say whether an Expert trace counts as one. |
| 2.7.1 knowledge loop | Phase 4 (asset to cell citation index and recertification) needs `GuidanceReference` as its key; it is built, so 2.7.1 can start from it. 2.7.1's Phase 6 (evaluation assets bound per asset) shares the scorer work of G5. |
| 2.8.0 supervision | Phase 3 (Sentinel to runtime downgrade) is independent. Its maker-checker object lists may cite Expert answers; that needs the Governor guard only (built). |
| 2.9.0 job-writer coverage | No overlap found in the plan headings and TLDR I read; I did not read its phases. |

## 6. Proposed 2.7.0 shape for the Expert theme

Sizes are my estimate from the plan's own S/M marks and the code now present.

1. **Plan correction (XS).** Update the plan's "What exists", gap table and acceptance to this note; move the three closed items to a done file. No code.
2. **P5b, the three Expert scorers (S).** Citation resolution, freshness, authority leakage, plus the `pack/eval_invoker.py` path for a pack that binds an Expert. Independent of the rest; uses `context["run"]`. Has a gold case already in the plan ("clear to pay").
3. **P4, visibility (S).** After the strict-posture umbrella: make the route require an ambient `InvocationContext` where `require_identity` is on, refuse with `principal_unresolved`, and narrow guidance reads by the caller's scope. The scope-narrowing half needs a decision on how `doc_source:` grants map to guidance assets (open question 3).
4. **P3, multi-pack and per-audience (M).** Last. It changes `ExpertRequest`, the route's body and the listing, so it is the only phase with consumer risk (jaci's CRE Policy Expert subclass, `plan_JACI_CL_EXPERTS_ON_PACKS`). Do it behind the optional `pack_ids` field as the plan says.

Order: 1, then 2 (no dependencies), then the strict-posture umbrella and the tenancy decision, then 3, then 4. In sum about 2 to 2.5 phases of real work instead of the five the plan lists, so the Expert theme fits beside the small items in candidate group A and is no longer the release's anchor.

## 7. Open questions for the user

1. The tenancy model decision gates the attestation key scope and the trace metadata keys. Settle it before P4 and P3 (it is already in the candidate note's group D).
2. Should `GuidanceReference` carry a `SourceRef` (sources provenance) so an answer's citation resolves to the exact guideline bytes? This is the one place 2.6.8's provenance work and the Expert surface meet. It is additive.
3. How should a caller's `PermissionScope` narrow guidance reads: by asset kind, by the pack's `doc_source:` selectors, or by the scope claims a host declares? I found no current mapping.
4. Is a lost Expert trace acceptable (it is today: logged, answer served), or should the route fail the call when its trace cannot be written? This is item 28's decision applied to a read-only route where the trace is the audit record.
5. Does jaci still need `ExpertRequest.pack_id` to stay single for one release (plan P3)? Only jaci can say; I did not read its repository.
6. Is an Expert trace a governance record for the log-purge scoping (item 29)?

## 8. Not verified

The 2.9.0 plan phases; the content of PR #101 and PR #108; the fields of the Expert trace step and the version bundle it pins; how the guidance store would use scope claims; the jaci side; whether the client package tests cover the Expert methods (the methods exist, `client.py:226`, `:230`). Line numbers are for `2066c67d` and will move again.
