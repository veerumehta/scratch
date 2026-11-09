# plan_JAPES_2_7_1_KNOWLEDGE_LOOP_CHANGE_CLASSES - every change is classed, and the class sets the gate

Repo: `japes`. Consumers to check: `jaci` (CL and CRE packs, guidance assets), Plato authoring UI (`plato/api/guidance.py`, `packs.py`).

Author: Virendra Mehta. Written against `japes` HEAD `3647d21a` (`2.6.4`), anchors read at that commit. Source: Deck 4 slides 17 to 20 (the knowledge loop, six classes of change, which version answers) and slides 44 to 48 (the playbook library and how a playbook improves). Companion: `plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT.md`, which versions skills, profiles and agent releases; this plan covers governed knowledge assets (policy objects, interpretation notes, playbooks, evidence schemas, matrices) and does not duplicate that work.

## Status and modifications

How to use this section: implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last. Branch: v2.7.1, nothing pushed.

- 2026-11-09 drift check against v2.7.1 (`ca288834`): every anchor exists; none of the plan's new names did. Landed since the plan: `GuidanceReference` (`experts/answer.py`), version windows (`by_case_date`, `from_date`), tenant-scoped guidance route and tenant-keyed `DbGuidanceStore`. Plan facts that were wrong or missing: guidance transitions wrote no audit event; the PUT route could not set `supersedes`; maker-checker existed only for rule-proposal review (local-on, deployed-off posture); the Expert and chat retrieval already serve only deployed assets.
- 2026-11-09 user decisions (typed in `opus-xrepo`'s session): headline is P1 to P3, P4 to P7 deferred. (1) forum members live in the pack (`governance/guidance.yaml`); (2) from-feedback learning assets are `minor_behavioral`; (3) self-approval follows the existing posture, enforced by provenance at every class when off; (4) no emergency class in the first cut; (5) a pack with no forum refuses material changes (fail closed), minor ones pass; (6) the gate table is the SDK default, packs only tighten.
- 2026-11-09 P1 `4ebdb648`: `ChangeClass` (five classes), `ChangeGate`, `DEFAULT_GATES`, `tightened`, `unclassified_change`. The slide-19 matrix is not in the repo: defaults chosen so only the two material classes need a forum (administrative, minor narrowing and minor behavioral: owner), which `overlay_forum` and `owner_then_release` tighten.
- 2026-11-09 P2: see the CHANGELOG entry; plan deviations: the state table keeps one `reviewer` actor class and the lifecycle resolves the step; `emergency` and bundle-level rollback not built; the gate's tests are recorded, not run (P4/P6).

## TLDR

The deck's knowledge loop has eight parties with one job each and six classes of change where "the class sets the tests, the approver and the clock" and classification is not waivable (slide 19). At HEAD the loop's machinery is mostly built: immutable numbered guideline versions with section diffs (`pack/guidelines.py`), pack draft diff and publish (`plato/api/packs.py` `diff`, `publish`), a release report that replays gold cases across two versions (`pack/release_report.py`), guidance assets with a content-hash version, `supersedes`, and a reviewer-gated lifecycle (`fabric/guidance/schema.py:52`, `lifecycle.py:35`), corrections that become gold cases, and tenant activation. What is missing is the vocabulary that ties them together: a change class on every asset version, a gate table per class, a forum (not just a reviewer) as the approving actor class for material and widening changes, the Curator proposal and Sentinel signal as records, and the index from an asset to the authority cells that cite it so "recertify the cells that cite the note" can be computed. The playbook library also needs its kind and mode labels; today `GuidanceAsset.asset_type` is a free string defaulting to `"learning"`.

## What exists at HEAD

- `fabric/guidance/schema.py:52` `GuidanceAsset`: `asset_type: str = "learning"`, `version` (content hash), `supersedes`, `guidance`, `trigger_patterns`, `applicability`, `confidence`, `status`, `expires_at`, `review_at`, `provenance`, `pack_id`.
- `fabric/guidance/lifecycle.py:35` `GUIDANCE_LIFECYCLE`: draft to approved (`approve`, actor class `reviewer`), approved to deployed (`deploy`), approved to draft (`revise`), deployed to deactivated. One actor class, `reviewer`, on every transition. `GuidanceLifecycle.transition` (`:165`) returns `GuidanceAsset | Refusal`.
- `plato/api/guidance.py`: list, get, put, `from-feedback`, and `{asset_id}/{action}` transition routes, tenant-scoped.
- `pack/guidelines.py`: guideline set versions `G1`, `G2`, digest of file digests, section-level diff, withdraw never delete.
- `pack/release_report.py`: two loaded packs compared; gold cases listed as unchanged, newly passing, newly failing, answer changed, answer changed with the rule changed ("the candidate set for marking the case superseded").
- `pack/diff.py`, `pack/rule_trial.py`, `pack/correction_cases.py`, `pack/corrections.py`: diff, trial against baseline, corrections to cases.
- `pack/activation.py:202` `TenantPackRegistries.activate`; `pack/version_windows.py` case-date selection.
- `audit/events.py:26` `ConfigAuditEvent` with `ConfigAuditAction` (the 2.6.0 plan's Phase 2 shipped).
- `statemachine/` `TransitionEngine` with actor-class enforcement and typed `Refusal`.
- `modes/evolve/curator.py`, `modes/evolve/evaluator.py`, `modes/operational/sentinel.py` (`SentinelMetrics`, `SentinelResult` at `:27`, `:48`).
- AuthorityMatrixV2 and `AuthorityCell` (`authority/resolver.py`), each cell with `evidence_floor` and `human_only`.

## Gaps

| # | Gap | Slide |
|---|---|---|
| K1 | No `ChangeClass` on an asset version; no class to gate mapping | 19 |
| K2 | One approving actor class (`reviewer`); no forum, no owner-only path for administrative changes, no emergency path with rollback armed | 18, 19 |
| K3 | Curator proposals and Sentinel signals are mode outputs, not records with provenance that a transition can cite | 18 |
| K4 | No asset to cell citation index; "recertify the cells that cite the asset" is not computable | 19, 32 |
| K5 | Playbook assets have no kind or mode labels; retrieval by domain, stage, decision class and evidence pattern is not expressible | 44, 45, 46 |
| K6 | Gold, edge and regression cases bind to a pack version, not to an asset version | 32, 36, 54 |
| K7 | Case stability: `version_windows` selects by case date; the deck pins a case to the version in force when it opened until it closes, unless a mandatory effective date, a retirement or a migration deadline forces re-evaluation | 20 |

## Phase 1 - `ChangeClass` and the gate table (S)

`fabric/guidance/change_class.py`:

```python
class ChangeClass(StrEnum):
    ADMINISTRATIVE = "administrative"
    MINOR_NARROWING = "minor_narrowing"
    MINOR_BEHAVIORAL = "minor_behavioral"
    MATERIAL_BEHAVIORAL = "material_behavioral"
    BOUNDARY_WIDENING = "boundary_widening"
    EMERGENCY = "emergency"

class ChangeGate(BaseModel):            # one row per class, pack-overridable but never loosened
    tests: list[Literal["none", "compatibility", "regression", "gold", "edge", "recertify_cells", "full_recertification", "smoke_then_full"]]
    approver_class: Literal["owner", "overlay_forum", "owner_then_release", "owner_then_certification_forum", "certification_forum", "owner_plus_forum_chair"]
    clock: str                          # informational: "same day", "days", "weeks"
    rollback_armed: bool = False        # emergency only
```

The default table is the slide 19 matrix verbatim. A pack may add tests or a stricter approver to a class; it may not remove tests or lower the approver (the same narrowing rule as the ABA). `GuidanceAsset` gains `change_class: ChangeClass | None` (required when `supersedes` is set; a new asset with no prior is `administrative` by definition). Classification is not waivable: a transition with no class on a superseding version is a `Refusal`, reason `unclassified_change`.

Also record the deck's own warning as a check: the highest-impact part of a change sets its class. If the diff touches a field the pack marks `behavioral` (evidence rules, thresholds, decision logic) and the declared class is `administrative`, refuse with `class_too_low` and name the field.

Acceptance: a superseding version with no class is refused; a pack cannot register a gate table that drops a test from the default; an edit to a behavioral field under `administrative` is refused naming the field.

## Phase 2 - approvers by class on the lifecycle (S)

Replace the single `reviewer` actor class with the table-driven one. `GUIDANCE_LIFECYCLE` stays as the shape; the `approve` transition's `actor_class` is resolved from the gate table for the asset's class at transition time, so `administrative` approves with `owner`, `material_behavioral` requires `owner` then `certification_forum`, `boundary_widening` requires `certification_forum` and never a lower layer alone, and `emergency` requires `owner_plus_forum_chair` with `rollback_armed` and a `review_by` date. Two-step approvals are two transitions with two audit events, not one transition with two signatures.

Maker-checker is a rule of its own, separate from forum membership: the principal who authored or last edited the candidate version cannot be the one who approves it at any class, including `administrative`. The lifecycle refuses with reason `self_approval`, read from the asset's `provenance` and the audit trail, not from a flag the author sets.

The forum is a named group, not a role string: `ForumRecord(forum_id, pack_id, kind, members: list[PrincipalRef])` in the pack manifest, loaded by `pack/manifest_loader.py`. A transition by a principal not in the forum is a `Refusal`, reason `not_forum_member`.

Every transition emits a `ConfigAuditEvent` (reuse, do not add a parallel event) with `change_class`, the approver class satisfied, and the forum id.

Acceptance: a material change approved by the owner alone stays in `draft` with a refusal naming the missing forum; the author of a version cannot approve it at any class; an emergency publish without `rollback_armed` is refused; the audit trail for a material change shows two approve events with two actors; a `draft` asset is never served to a caller (the Expert route and `DefaultPolicyExpert` read `approved` and `deployed` only); rolling a pack version back restores every asset activation in that version atomically, and the audit trail shows one `rollback` event for the set.

Vocabulary: where this plan says "a published pack version" it means what the product calls a policy bundle; a bundle is published, activated and rolled back as one unit, and the per-asset class and gate decide what tests the bundle's publish must pass.

## Phase 3 - Curator proposal and Sentinel signal as records (S)

Two small records in `fabric/guidance/loop.py`: `LoopSignal` (from `SentinelResult`, with the evidence attached: override events, rejections, RFI counts, regulatory feed item, drift metric) and `ChangeProposal` (from the Curator: the candidate asset version id, the signal ids it answers, the proposed class, the owner it is routed to). `GuidanceAsset.provenance` gains `proposal_id`. The Curator never publishes on its own (slide 18): `ChangeProposal` has no transition to `approved`; only the owner's `approve` on the resulting asset does. `plato/api/guidance.py` `from-feedback` becomes one way to create a proposal; a Sentinel run is the other.

Acceptance: a published version can be traced back to the signal that started it; a proposal cannot reach `approved` without an asset version and an owner approval.

## Phase 4 - asset to cell citation index and recertification (M)

`authority/citations.py`: an index built at pack load from every `AuthorityCell` that names an asset in its `evidence_floor` or conditions, every policy rule that references a note, and every playbook a cell's mode composition declares. `cells_citing(asset_id) -> list[cell_ref]`, and beside it `directives_citing(asset_id) -> list[jtbd_ref]` built from the pack's JTBD set (`pack/jtbd_align.py`, `jtbd_match.py`) so an impact report can name every policy directive a change touches, with the matched text as the reason. For `material_behavioral` and `boundary_widening` the gate's `recertify_cells` test is exactly: run each cited cell's bound evaluation assets against the candidate version and refuse publish on any regression. This is what makes slide 32's "recertification of the cells that cite the note" a computed step rather than a reviewer's memory.

Acceptance: publishing a material change to an interpretation note runs the gold cases of every cell that cites it and nothing else; the impact report for that change lists the directives that cite it, each with the citing text; a boundary-widening change with a failing cited cell is refused naming the cell.

## Phase 5 - playbook library kinds and mode labels (S)

`GuidanceAsset.asset_type` becomes a closed `GuidanceKind` enum (keep `learning` for the existing rows): `interpretation_note`, `decision_rubric`, `exception_pattern`, `edge_case_library`, `scenario_library`, `anomaly_signature`, `investigation_sequence`, `reviewer_checklist`, `scaffold`, `engagement_script`, `negotiation_script`, `best_practice_sequence`, `failure_mode`, `exemplar_case`, `red_flag_indicator`, `learning`. Add `consumed_by_modes: list[ModeName]` (slide 45: a rubric handed to a Narrator is useless) and `owner: str` (a named human team). `applicability` already carries pack-defined dims; document the four the Playbook Expert retrieves by (domain, workflow stage, decision class, evidence pattern) so `DefaultPlaybookExpert` can filter on them rather than on `trigger_patterns` alone.

Acceptance: a `decision_rubric` is not returned to a Narrator query; a Reasoner query for `stage=sizing` returns only rubrics and scenario libraries labeled for it.

## Phase 6 - evaluation assets bound per asset (S)

`pack/correction_cases.py` cases gain `asset_refs: list[str]` (asset id and version). The release report already lists cases whose answers move; with `asset_refs` it can also say which asset moved them, and the per-class gates in Phase 1 can require the gold, edge and regression triple for the asset being changed. The three case kinds get a `case_kind` field with exactly those values.

Acceptance: a material change to one asset runs only the cases bound to it plus the cited cells' cases; a regression case bound to an asset is replayed on every revision of that asset.

## Phase 7 - case stability (S to M)

`pack/version_windows.py` gains a fourth activation mode, `case_stability`: a case is pinned to the version in force at its open date and keeps it until closed, except when a later version carries `mandatory_effective_from` at or before today, the pinned version is retired, or the activation names a `migration_deadline`. The selection `notes` say which rule applied. This is the slide 20 behavior; it is one mode, not a replacement for `by_case_date`.

Acceptance: a case opened under v4.0 is served v4.0 after v4.1 activates; it moves to v4.1 on a mandatory effective date; the Expert answer's `freshness` names the pinned version and the newer one.

## Decisions this plan does not make

- Whether the forum member list lives in the pack manifest or in Plato's control plane (the same question as the RBAC spec's 9.1). Default: manifest, with Plato as the writer once the single-writer rule is settled.
- Whether `learning` assets written by `from-feedback` get a class automatically (`minor_behavioral` is the safe default) or must be classed by the owner.

## Sequencing

P1 and P5 first (vocabulary; no behavior change until a pack declares classes). P2 and P3 next. P4 and P6 together, since the recertification test needs per-asset cases. P7 is independent and can land any time.

## Guardrails

- Do not add a second lifecycle; extend `GUIDANCE_LIFECYCLE` through its transition table.
- Do not add a parallel audit event type; `ConfigAuditEvent` carries the class and forum.
- Keep `asset_type` values backward compatible (`learning` stays).
- Re-verify anchors at HEAD per phase; commits only, no push.
