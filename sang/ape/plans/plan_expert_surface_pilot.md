# Expert surface for the read-only pilot: answer envelope, route, authority guard (sonnet-runtime, 2026-10-18)

Scope (opus-xrepo, user-approved routing): P1 (`ExpertAnswer`), P2 (Expert route and client method), P5's Governor guard
only, from `plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT.md`. P3, P4, the P5 scorers, 2.7.1 and 2.8.0 wait.
User decisions applied: no version bump (ignore every "bump to 2.7.0"); `ExpertBinding` is not a new record (reuse
`SurfaceBinding`, `surface_type=API_SERVICE`, with a per-pack list when P3 comes); the attestation key and forum
membership are the user's to decide, so the attestation carries a `key_id`. Read-only: no connector path under any flag.
Written against `v2.6.4` at the HEAD the plan names (`3647d21a`; `git log --oneline -1` read the same).

## Anchors re-verified at HEAD

Hold as written: `experts/base.py` `OutputClassification` (:27, `GUIDANCE_REFS`), `ExpertRequest` (:52), `ExpertResponse`
(:68, `output_classification`, no `answer`); `experts/policy/base.py` `PolicyResolutionResult` (:22: `applicable_policies`,
`precedence_order`, `conflicts`, `stale_policies`, `not_yet_effective`, `policy_versions`), `ComplianceResult` (:54),
`InterpretationResult` (:83: `cited_clauses`, `confidence`), `StalenessReport` (:102); `DefaultPolicyExpert` with
`from_pack(pack)` (default.py:157) and `execute` (:191, stamps `output_classification`); `playbook/base.py`
`PlaybookRecommendation`; `SurfaceType.API_SERVICE`; `fabric/canonical/profiles.py:294` `SurfaceBinding` (has `pack_id`,
`extra`); `GovernedRouter` (`server/governed_http.py:62`); `content_digest` (`util/digest.py:17`) already exists, so no new
digest and `content_version` is untouched; `VersionBundle` (`fabric/canonical/trace.py`); the `citation_support` scorer
(`evaluation/citation_scorer.py`); `GuidanceReference` does not exist (new).

Do not hold (the plan's anchor is wrong; the design is fixed to the real code):
1. **P2 version selection.** `TenantPackRegistries.registries_for` (`pack/activation.py:162`) composes *assistant*
   registries (profiles, skills), not a pack's policies. The code that picks the served pack version is the assess route:
   `domain_pack_record(store, pack_id, version, pinned=...)` (`pack/domain.py:26`) plus `select_case_version`
   (`pack/assessment.py:602`) over `DbPackActivationStore.list(pack_id)`, inline in `plato/api/packs.py` (~1580-1596). That is
   Plato logic that belongs in the SDK: P2 first lifts it into one SDK function both routes call.
2. **P2 "one `TraceStep` with `output_classification`".** `TraceStep` has no such field (extra forbidden); the
   classification rides in the step's metadata beside the version bundle, which `trace.py` already says is the home of
   per-step version bundles.
3. **P5 "Decision whose `authority_basis`".** No Decision type at HEAD has an `authority_basis`. The Governor judges a pack-defined
   `TDecision` and reads opt-in attributes by name (`policy_clauses_cited`, `matrix_cell_ref`); `GovernorDecision`
   (`modes/schemas.py:593`) has none. The only `authority_basis` in the SDK is a free string on a checkpoint resolution
   (`pipelines/kinds.py:689-720`, `pack/case_runs.py:328-353`). The guard needs the contract defined first (see P5).
4. `rg authority_basis|guidance_refs modes/operational/governor.py` is still empty, as the plan says.

## P1 - the `ExpertAnswer` envelope (S-M, three commits)

`jazzx_sdk/experts/answer.py` (models only) and `experts/policy/answer.py` (the mapping). `ExpertResponse` gains
`answer: ExpertAnswer | None = None`; nothing else on it changes.

- `GuidanceReference{asset_id, asset_kind, version, section, pack_id, effective_from, jurisdiction}` with a `key`
  (`pack_id:asset_id@version`) the guard and the ledger compare. `asset_kind` is a plain string now (`policy`, `rule`,
  `interpretation_note`, `playbook`, `learned_guidance`); 2.7.1's closed `GuidanceKind` can narrow it later, and 2.7.1's
  citation index reuses this one shape.
- `FreshnessState{pinned_version, newer_published, superseded, not_yet_effective}`; 2.8.0's generic supersession can feed
  `superseded` later, today it comes from `stale_policies`.
- `ConflictPosition{source, position}`.
- `AdvisoryAttestation{key_id, algorithm, digest, signature, issued_at, pack_versions}`: `digest` is
  `content_digest(canonical answer without the attestation)`; `signature` is an HMAC-SHA256 over it by the key `key_id` names.
  An `AttestationKeyring` protocol (`sign(digest) -> (key_id, signature)`, `verify(key_id, digest, signature)`) keeps
  per-deployment and per-tenant both possible: the keyring maps a tenant to a `key_id`, several keys may be live (rotation).
  The default keyring reads `PLATO_EXPERT_ATTESTATION_KEYS` (JSON `{key_id: secret}`) and `..._ACTIVE_KEY_ID`.
- `ExpertAnswer{status, answer, references, conflict_unresolved, positions, evidence_floor, freshness, label,
  attestation | None, output_classification=GUIDANCE_REFS, digest}`; `status` is `answered | uncited | conflict | not_found`.

Mapping from `DefaultPolicyExpert` (no behavior change in the experts; a builder over their results, called by the
surface, not inside `execute`, so every in-process caller keeps its `ExpertResponse` untouched):
- `resolve`: `policy_versions` -> one `GuidanceReference` per applicable policy (kind `policy`, version from the map, section none);
  `conflicts` (rule id, two overlays, description) -> `positions` and `status=conflict`, `answer=None`, per the deck;
  `stale_policies` -> `freshness.superseded`, `not_yet_effective` -> `freshness.not_yet_effective`.
- `check_compliance`: `applied_policies` (+ their versions from the registry) -> references; `allowed`, violations and
  `rationale` -> `answer` text; unapproved-threshold `refusals` -> `evidence_floor`.
- `interpret`: `cited_clauses` -> references (kind `rule`), `interpretation` -> `answer`, `ambiguities` -> `evidence_floor`.
- `detect_staleness`: `StalenessReport` -> `freshness`, `recommended_actions` -> `evidence_floor`.
- Playbook: `PlaybookRecommendation.guidance_refs` -> references (kind `playbook`), the same way; only if it is in the pilot.

**Uncited answers and tolerant-first.** The deck makes an answer with no reference invalid; some experts return none today
(an empty registry makes `resolve` a no-op; an `interpret` may cite nothing). Both hold if the rule lives at the
*surface*, not in the experts: the model validator says `status=answered` needs at least one reference; the builder, when
an expert returns none, produces `status=uncited` with `answer=None` and a reason (and `references=[]`), served as 200 with
a trace warning, never as an error and never as answer text. In-process `ExpertResponse.result` is unchanged, so no existing
caller breaks. There is no `allow_uncited` switch: serving unsourced advice is the contract violation this surface exists to
prevent (the "refuse only what would write wrong data" case), and the experts that cite nothing are visible in the trace, not hidden.

Tests (each fails on old code): uncited builder output is `uncited` and carries no answer text; two overlays defining one rule
give `conflict` with both positions and `answer=None`; a stale policy is always in `freshness.superseded`; the attestation
verifies and fails on any byte change, with the `key_id` of a rotated key still verifying; existing expert suites pass unchanged.

## P5 guard - an advisory answer is never a Decision's authority (S, after P1)

Contract (the open anchor): a decision schema opts in by declaring `authority_basis`, as it opts in to `policy_clauses_cited`:
a string, a list of strings, or typed entries `{kind, ref}`. A basis entry is **advisory** when (a) it is typed
`kind in {guidance_reference, expert_answer}` or carries `output_classification == guidance_refs`; or (b) its `ref` equals the
`digest` of an `ExpertAnswer` or the `key` of a `GuidanceReference` recorded for this case (`ctx.metadata["advisory_refs"]`,
filled by whatever called the Expert for the case; the pilot route is stateless, so (a) is what the pilot exercises and (b)
is the hook for the case-run integration); an entry the guard cannot classify passes (it cannot tell; a plain string with
no ledger is not refused on a guess).
Where: a deterministic gate in `GovernorMode.run` beside `_authority_gate`, before any model call, refusing with a typed
`Refusal` (`RefusalClass.AUTHORITY_EXCEEDED`, reason code `advisory_as_authority`, the offending refs named) and a
`GovernorDecision(approved=False, policy_checks=["authority_basis"], violations=[...])` exactly as `_authority_gate` shapes its refusal.
The sibling of the same family: the checkpoint resolution's `authority_basis` string (`kinds.py:689-720`,
`case_runs.py:328-353`) gets the same check against the ledger, so a human cannot cite advice as the basis of a replacement
decision either. Tests: typed advisory refused; digest in the ledger refused; unclassifiable string passes; no `authority_basis`
declared is unchanged; the resume path refuses a ledgered digest.

## P2 - the Expert route and client method (M, four commits)

1. Lift the served-version choice out of the assess route into `jazzx_sdk/pack/served_version.py`
   (`resolve_served_version(store, activations, tenant, pack_id, version, inputs) -> (record, selection)`), the assess route
   calling it; behavior-preserving, with the assess route tests as the proof (tests first, then the lift).
2. `jazzx_sdk/server/expert_api.py`: `create_expert_router(...)` holds the serving logic (SDK first): load the served pack
   (`materialized_domain_pack`), build `DefaultPolicyExpert.from_pack(pack)`, run the operation, build the `ExpertAnswer`
   (freshness: `newer_published` from the store's published versions against the served one; `pinned_version` the served one),
   sign it, and record one trace step. Body is a closed schema (`question`, `context`, `program_id`, `case_date`, `version`);
   any other key, a connector name included, is a 422 by `extra="forbid"`, and the code has no connector path: the expert is
   built with no tools. Operations: `resolve`, `check_compliance`, `detect_staleness` (deterministic) and `interpret`
   (the one that calls a model; it reports its usage like other model routes).
   `GET .../experts` lists the experts a pack serves and their operations (`policy`, plus `playbook` where the pack has one).
3. `plato/api/experts.py` only mounts it (tenant, store, activations, auth, keyring from `app.py`); Plato holds no serving logic.
4. `jazzx_plato_client`: `expert(pack_id, expert, operation, context=..., case_date=..., version=...)` and `experts(pack_id)`,
   typed `ExpertAnswer` contracts held equal to the SDK's by a test; the route-coverage sweep requires both routes have a method.
Reuse, not duplicate: `content_digest` for the answer digest; `citation_support` stays the scorer for P5-later (its input is an
adjudication's `{rule_id, verdict}` outcomes plus `cited_texts`, so judging "do the cited clauses support this answer" needs an
adapter that feeds the answer as the rule text and the references' clause text; it is not drop-in, and that is for the scorer phase).
Acceptance: served against the activated version a question returns an `ExpertAnswer` naming it; the same question with
`case_date` in a `by_case_date` window names the window's version; an unknown pack/version is 404/422 as on assess; a body with a
connector key is 422; the trace step carries `guidance_refs` and the served version; no route has a write side effect (a test asserts the
draft and canonical stores are untouched).

## The authority-leakage scorer (P5, planned only, not built)

Method must be chosen before anyone builds it. Options: (1) deterministic: the answer text matched against a pack-data list of
decision phrases ("clear to pay", "approved", "you may proceed", "is eligible") with negation handling; cheap, repeatable, misses
paraphrase; (2) model-judged through the existing `JudgeFn` and judge cache (as `citation_support`): catches paraphrase, costs a
call per answer, and is itself an advisory judgment. Recommendation: deterministic as the gate (a failing phrase fails the
case; the list is pack data and the seed is the "clear to pay" regression case), the model judge as an optional second scorer
that can only add failures, never clear one. Not built until the user picks.

## Decisions taken (user, via opus-xrepo)

1. Attestation key per deployment, with `key_id` on the attestation so per-tenant keys or another scheme follow without
   breaking old answers (the keyring verifies by `key_id`). The secret lives in the deployment's settings mechanism, read
   with `env_text` and listed on the config catalogue as a secret: `PLATO_EXPERT_ATTESTATION_KEYS` (JSON `{key_id: secret}`,
   several live for rotation) and `PLATO_EXPERT_ATTESTATION_KEY_ID` (the one that signs). With no key configured the
   route serves `attestation=null` and the `unsigned` freshness warning, not a refusal (tolerant first).
2. Forum membership is not for this work: it gates the 2.7.1 approvers only. For later: the forum definition and its
   members live in the tenant's pack data (a published pack is keyed `(tenant_id, pack_id, version)`); core and seed packs
   ship the definition with members empty; no base/derived machinery is built.
3. Layering for P2: the served pack is resolved per tenant from that tuple, so the route and the lifted `served_version`
   are tenant-scoped throughout (tenant is an argument, never ambient state).
4. No version bump.

## Order and effort

P1 (S-M) -> P5 guard (S) -> P2 (M). The guard needs P1's types; P2 uses both. Queue behind the 2.6.5 items in flight.
Consumers to check before each lands: jaci's CRE Policy Expert subclass (`from_pack` kwargs unchanged) and jazzx-assistant.
