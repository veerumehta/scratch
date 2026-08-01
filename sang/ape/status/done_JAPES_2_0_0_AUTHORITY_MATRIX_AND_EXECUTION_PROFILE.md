# Plan: JAPES 2.0.0 Authority Matrix, PolicyProfile, and Execution Profile

Author: Virendra Mehta · 2026-07-13 · Rev 2026-07-14 (per Claude Code review: pinned alias table, trimmed profile fields, authority/ package name; Phases 1-5 shipped) · Rev 2026-07-15 (re-versioned onto the 2.0.0 line per repo practice)
Repo: japes (jazzx_sdk) · Baseline: 2.0.0 line (additive) · Companion to plan_JAPES_2_0_0_GOVERNED_VALUE_AND_REFUSAL_PRIMITIVES.md (consumes Refusal, ConfidenceTier)
Driver: the Commercial Lending corpus makes governance executable at the decision cell: a 54-cell authority matrix (cell_id, decision_class_id, action_class, actor_class, autonomy_launch, human_only, evidence_floor, accountable_human, promotion_criteria), candidate/final cell splits, and a narrowing chain Pack -> Surface Binding -> Client Overlay -> Execution Profile where effective authority is the most-restrictive intersection evaluated per action. The cell model, the profile objects, and the intersection resolver are invariant machinery. The 54 cells themselves are pack data and live in JACI.

Grounding notes (verified 2026-07-13 against dev):
- fabric/canonical/policy.py has AuthMatrix + AuthorityEntry (role, action_scope, ceiling: dict, escalation_target, delegation_chain). Role/ceiling shaped, attached per-Policy; not cell/decision-class shaped and not institution-level.
- skills/governance/base.py BaseGovernanceSkill mentions evidence_floor and human-only in docstrings/params as free text; EnforcementResult/CeilingResult exist.
- manifest/autonomy.py AutonomyLevel: L0_ADVISORY/L1_DRAFT/L2_APPROVAL/L3_AUTONOMOUS. Canonical Decision.autonomy_level is numeric 0-4. Spec ladder: L0 Assist, L1 Recommend, L2 Execute-with-approval, L3 Policy-bounded-autonomy, L4 Self-improvement-within-bounds. Three vocabularies; must become one.
- manifest/surface_types.py SurfaceType: WORKSPACE/API_SERVICE/AUTOMATION/GATEWAY. Spec surface types: Workspace, Assistant, API/Service, Automation.
- Policy.overlay_id and experts/policy/default.py overlay_map precedence + conflict detection exist; no ClientOverlay or ExecutionProfile object.
- modes/operational/governor.py enforces policy gates procedurally; it does not consult a cell table.

## Phase 1 - One autonomy ladder

- manifest/autonomy.py: extend AutonomyLevel to five members with spec semantics: L0_ASSIST, L1_RECOMMEND, L2_EXECUTE_WITH_APPROVAL, L3_POLICY_BOUNDED, L4_SELF_IMPROVEMENT. Keep the old four names as deprecated aliases (module-level mapping OLD_AUTONOMY_ALIASES) so existing manifests load; loader warns.
- The alias mapping is governance-critical, not a mechanical rename: a wrong old-to-new mapping silently changes what autonomy an existing manifest grants. The mapping is pinned here, keyed to numeric levels; deviating requires amending this plan:
  L0_ADVISORY (propose only, no execution) -> L0_ASSIST, numeric 0
  L1_DRAFT (may draft, human releases) -> L1_RECOMMEND, numeric 1
  L2_APPROVAL (execute with approval) -> L2_EXECUTE_WITH_APPROVAL, numeric 2
  L3_AUTONOMOUS (bounded autonomy, ceiling-checked) -> L3_POLICY_BOUNDED, numeric 3
  L4_SELF_IMPROVEMENT: new, no legacy alias; nothing existing may silently gain L4.
  Semantics audit: L1_DRAFT and L1_RECOMMEND both mean output has no effect until a human releases it; L3_AUTONOMOUS was already policy-bounded in practice, so every legacy value keeps its numeric level.
- Value-string handling is pinned too, because pydantic and every persisted Decision/manifest deserialize str-enums by VALUE, not member name: new members take new value strings ("l0_assist", "l1_recommend", "l2_execute_with_approval", "l3_policy_bounded", "l4_self_improvement"), and the old value strings ("l0_advisory", "l1_draft", "l2_approval", "l3_autonomous") are registered in OLD_AUTONOMY_ALIASES and honored via the enum's _missing_ classmethod for value-based lookup, so persisted governance data loads without rewrite. Serializing back writes the new value string (one-way migration on rewrite; no silent break on read).
- Add to_numeric()/from_numeric() so canonical Decision.autonomy_level (0-4 int) and the enum are one vocabulary with two encodings. Document in the module docstring that the numeric form is the storage form.
- Sweep: grep for L1_DRAFT/L2_APPROVAL usages (manifest/loader.py, agents/interactive/, tests) and migrate to aliases-tolerant reads.

Acceptance: existing manifest fixtures load with a DeprecationWarning; round-trip enum<->numeric test; a pinned-table test asserting every legacy member resolves to exactly the numeric level in the table above (this test is the guard against silent autonomy drift); a fixture persisted with the OLD value strings ("l0_advisory" etc.) deserializes through pydantic to the correct new member at the correct numeric level.

## Phase 2 - AuthorityCell, DecisionClass, AuthorityMatrix

New module jazzx_sdk/fabric/canonical/authority.py.
- DecisionClass: decision_class_id, name, description, human_only (bool), default_evidence_floor (list[str] evidence_type ids), pack_id.
- AuthorityCell: cell_id, decision_class_id, action_class, actor_class, autonomy_launch (AutonomyLevel), human_only (bool), evidence_floor (list[str]), accountable_human (str role ref), promotion_criteria (str|None), matrix (str, register name), notes. Frozen model.
- CellKind derivation: property is_candidate/is_final by suffix convention (-cand/-fin/-ovr) with an explicit override field cell_kind for packs that do not use suffixes. Rule encoded in a validator: a final cell must have human_only true or autonomy_launch L0.
- AuthorityMatrixV2 (name avoids colliding with policy.py AuthMatrix): cells dict[cell_id, AuthorityCell], decision_classes dict, matrix_version, pack_id. Class methods from_records(list[dict]) and from_csv(path) so JACI can feed register CSVs directly. Lookup API: cell(cell_id), cells_for_decision_class(id), require_cell(cell_id) raising fail-closed.
- Do not delete policy.py AuthMatrix; add a docstring cross-reference (per-policy delegation vs institution-level matrix are different constructs; DomainPack.authority_matrix_versions continues to version the latter).

Acceptance: from_csv on a fixture with the corpus column set (matrix, cell_id, decision_class_id, action_class, actor_class, autonomy_launch, human_only, evidence_floor, accountable_human, promotion_criteria, notes) produces 100% typed cells; validator rejects a -fin cell with autonomy_launch above L0 unless human_only.

## Phase 3 - PolicyProfile, ClientOverlay, ExecutionProfile

Same module or fabric/canonical/profiles.py. Modeling rule for this phase (per review): only fields the resolver and Governor read now get typed; everything else rides an extra/custom escape hatch until JACI exercises it typed. This keeps four new objects from running ahead of their consumers.
- PolicyProfile: profile_id, version, institution_ref, confidence_floors (dict[str, float]), thresholds (dict[str, str|int] with decimal-string values), custom (dict). This is the object every guard/threshold key resolves against; the SDK never supplies default numeric values. get(key) raises KeyError fail-closed with a message naming the profile (no silent defaults). engagement_rules and source_precedence stay inside custom until a consumer reads them typed.
- ClientOverlay: overlay_id, version, policy_profile_ref, autonomy_narrowings (dict[action_class, AutonomyLevel]), enumerated_allowances (dict, e.g. writeback tier D3 lists; read by the automation chassis), extra (dict; asset_pins live here until the pinning consumer exists).
- ExecutionProfile: ep_id, version, overlay_ref, live_surfaces (list[str]), cell_activations (dict[cell_id, AutonomyLevel]), extra (dict; connector_instances, non_widening_attestation, environment live here until activation tooling reads them typed).
- SurfaceBinding (the SBA object): surface_id, surface_type, pack_id, autonomy_ceilings (dict[action_class, AutonomyLevel]), in_scope_action_classes/out_of_scope_action_classes, extra (dict; role_patterns and writer_of_record_for ride here until the workspace layer consumes them). manifest/surface_types.py: add ASSISTANT to SurfaceType (additive).
- All four load via from_dir/YAML consistent with PackManifestLoader conventions; PackManifestLoader (pack/manifest_loader.py) learns two optional keys: authority_matrix and surface_bindings (paths). Unknown-key tolerance preserved.

Acceptance: YAML fixtures for all four load and validate; PolicyProfile.get on a missing key raises with profile id in message.

## Phase 4 - Effective-authority resolver

New jazzx_sdk/authority/resolver.py (new package jazzx_sdk/authority/ with __init__ re-exports; named authority, not governance, to avoid colliding with skills/governance/, which stays the skill contract; the resolver is pure logic).
- resolve_effective_autonomy(cell: AuthorityCell, binding: SurfaceBinding|None, overlay: ClientOverlay|None, ep: ExecutionProfile|None, downgrades: list[AutonomyLevel]|None) -> EffectiveAuthority.
- Semantics: min() across every layer that expresses an opinion for the cell/action_class, then apply runtime downgrades, floor at L0. human_only anywhere in the chain forces L0 + human_only true. Returns EffectiveAuthority {autonomy: AutonomyLevel, human_only: bool, evidence_floor: list[str], contributing_layers: dict} so traces can show why.
- check_action(matrix, cell_id, actor_class, evidence_types_present, ...) -> EffectiveAuthority | Refusal: returns Refusal(HUMAN_ONLY_ACTION) for programmatic invocation of a human-only cell, Refusal(PRECONDITION_FAILED) when evidence_floor unmet, Refusal(AUTHORITY_EXCEEDED) when actor_class mismatched. Consumes the Refusal type from the companion plan.

Acceptance: table-driven test with at least: EP narrower than SBA wins; overlay human_only overrides EP L2; missing layers treated as no-opinion; evidence floor unmet yields typed Refusal with cell_id in matrix_cell_ref.

## Phase 5 - Governor integration

- modes/operational/governor.py: GovernorMode accepts optional authority_matrix + profiles at construction (injected like prompt_resolver); when present, every gate evaluation calls check_action first and short-circuits to the Refusal before any LLM step. Absent matrix keeps current behavior (backward compatible for AML/KYC scenarios).
- BaseGovernanceSkill.enforce_ceiling: accept EffectiveAuthority in addition to the current numeric ceiling arithmetic.
- TraceStep outputs must include the EffectiveAuthority.contributing_layers dict for any gated action (audit answers "which layer narrowed this").

Acceptance: governor unit test proving a human-only cell action never reaches the LLM path; existing governor tests green with no matrix supplied.

Shipped 2026-07-14 (commits 36810e1, 3fd91cf) with three accepted deviations, now the plan of record:
1. BaseGovernanceSkill.enforce_ceiling stays an untouched @abstractmethod; a concrete ceiling_from_effective(requested_level, effective) bridge converts EffectiveAuthority to CeilingResult instead. Right call: changing an abstract signature would not bind existing subclasses (JACI AML skills) and could break callers.
2. human_only is sourced from the AuthorityCell only; the trimmed profile models do not carry a typed layer-level human_only. Equivalent enforcement is available today via an overlay/EP narrowing to L0; layer-level human_only rides the extra hatch and gets typed when a consumer needs the distinction (L0 still permits assist output; human_only asserts no autonomous path exists).
3. The SDK Governor stays domain-agnostic: cell_id comes from decision.matrix_cell_ref and actor_class from ctx.metadata under documented keys, rather than assuming a richer decision shape. JACI packs must populate those keys (the wedge plan's SpreadDecision already carries matrix_cell_ref as a schema const).
   Downstream contract (JACI wedge checklist): matrix_cell_ref is covered by SpreadDecision, but actor_class is NOT yet populated anywhere — the wedge Phase 3 conductor calls must set ctx.metadata["actor_class"] to the invoking actor class before GovernorMode.run(), or the gate defaults it to "agent" and a cell whose actor_class differs refuses AUTHORITY_EXCEEDED. Add this to the JACI wedge Phase 3 checklist. (An overlay/EP narrowing to L0 reproduces the human-only enforcement outcome in the meantime; layer-level human_only earns a typed field only when a consumer needs the L0-vs-human_only distinction.)

## Out of scope

The 54 commercial-lending cells, decision classes CI-DC-*/SP-*, EP-CHB content (all JACI pack data); event emission on decisions (companion events plan); IPDV role-directory integration (engagement input).
