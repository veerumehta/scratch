# Plan: JAPES 2.0.0 Governed Value and Refusal Primitives

Author: Virendra Mehta · 2026-07-13 · Rev 2026-07-14 (fully additive per Claude Code review) · Rev 2026-07-15 (re-versioned onto the 2.0.0 line per repo practice: everything pushed prior was 1.9.9, the repo now sits at 2.0.0 for an extended run)
Repo: japes (jazzx_sdk) · Baseline: 2.0.0 line · All phases additive; the SpreadLine decimal default flip is deferred to a later declared breaking release
Driver: Commercial Lending Suite engineering corpus v1.0. The corpus's foundation types (Money, Confidence, SourceCoordinate, Provenance, VersionBundle) and its refusal discipline (typed refusals with reason codes as designed outcomes) are invariant machinery, not domain knowledge, so they belong in the SDK. All commercial-lending-specific values (thresholds, reason-code vocabularies, floors) remain pack/profile data.

Design intent, in one line per primitive:
- Money and metric values must never be binary floats; exact decimal strings, currency-aware, with declared rounding.
- Confidence gets a tier vocabulary (High/Medium/Low) whose floors are read from institution profile data, never hard-coded.
- Provenance gets a closed provenance_type vocabulary and a SourceCoordinate that can locate a value inside a document (page/region) or workbook (sheet/cell).
- Refusal becomes a first-class typed object with a reason-code registry; a refusal is a successful, auditable outcome.
- VersionBundle becomes a typed object attachable to decisions, runs, packages, and trace steps; today it is an untyped dict in Trace.metadata.

Grounding notes (verified 2026-07-13 against dev):
- Zero uses of decimal.Decimal anywhere under jazzx_sdk/. finance/spread.py SpreadLine.values is list[float|None]; finance/structure.py casts float(v).
- fabric/canonical/evidence.py has confidence: float, source_system/source_record_id, provenance_chain: list[ProvenanceEntry]. No tier enum, no coordinate type, no provenance_type enum.
- fabric/canonical/trace.py: version bundles set via TraceStepContextHelper.set_version_bundle(...) into Trace.metadata as dicts. OverrideEvent already has reason codes; there is no Refusal type.
- Latent defect: modes/evolve/evaluator.py _build_user_message reads outcome.outcome_class and outcome.metadata, neither of which exists on canonical Outcome (fields are result/learning_signals). Fix in Phase 4.

## Phase 1 - Exact-decimal values

New module jazzx_sdk/fabric/canonical/values.py.
- Money: pydantic model, fields amount (str, validated as exact decimal literal, serialized as string always; the single authoritative representation) and currency (ISO 4217 str). minor_units is input-only/derived: accepted at construction, always recomputed from amount, never stored independently (dual authoritative representations invite divergence). Reject float inputs in a field_validator (accept int, str, decimal.Decimal only). Arithmetic helpers deliberately minimal: add, subtract, scalar-multiply, each requiring an explicit rounding argument; every binary op validates currency match and raises on mixed-currency operands. This is not a currency-math library. Serialization scale is pinned: the validated input string is stored and emitted verbatim ("0.30" stays "0.30"; never normalized through Decimal on the way out, since Decimal would collapse "0.30" to "0.3" and admit forms like "1E+2"); accepted input grammar is plain decimal literals only (optional sign, digits, optional fraction; no exponent notation); arithmetic results take their scale from the explicit rounding argument.
- DecimalValue: same validation for non-monetary metrics (ratios, percentages). Fields value (str), optional unit, optional rounding declaration {mode, places}, optional day_count (str, for rate/period calculations; declared not computed).
- Export both from fabric/canonical/__init__.py and jazzx_sdk/__init__.py.

finance/ adoption (additive, non-breaking):
- finance/spread.py: SpreadLine.values (list[float|None]) stays unchanged; add optional values_decimal: list[DecimalValue|None] populated when callers supply decimals, with a DeprecationWarning on float writes pointing at values_decimal. The default flip (values becoming decimal-typed) is deferred to a later declared breaking release alongside whatever other breakers accumulate; do not spend a breaking event on it alone.
- finance/structure.py: new construction paths accept DecimalValue; existing float(v) coercions remain until the declared flip, each marked TODO(decimal-flip).
- Do NOT migrate llm/ cost tracking or evaluation scores; those are telemetry, not governed values. Add a module docstring note in values.py stating this boundary.

Acceptance checks:
- pytest passes with a new tests/fabric/test_values.py covering: float input rejected, "0.1"+"0.2" equals "0.3", serialization round-trip preserves the string exactly, rounding requires explicit mode.
- Mixed-currency add raises; minor_units always equals recomputation from amount.
- SpreadLine float behavior byte-identical to 1.9.9 (regression test) while values_decimal round-trips.

## Phase 2 - Provenance, SourceCoordinate, Confidence tiers

Extend fabric/canonical/evidence.py (additive, non-breaking):
- New SourceCoordinate model: source_file_ref (str), locator (discriminated union: {page, region} | {sheet, cell} | {section, path}), optional content_hash.
- New ProvenanceType str-enum: sourced, computed, reviewer_entered, assumption, expert_attested.
- ProvenanceEntry gains optional provenance_type: ProvenanceType and optional source_coordinates: list[SourceCoordinate]. Existing fields untouched.
- New ConfidenceTier str-enum (HIGH/MEDIUM/LOW) and Confidence model {score: float, tier: ConfidenceTier}. CanonicalEvidenceObject keeps confidence: float for compatibility; add optional confidence_detail: Confidence.
- New pure function resolve_tier(score, floors: dict) -> ConfidenceTier where floors comes from profile data (see authority/execution-profile plan); no default numeric floors in code.

Acceptance checks:
- Existing evidence tests untouched and green.
- New test asserting resolve_tier raises when floors dict is missing keys (fail-closed, never silently defaults).

## Phase 3 - Typed refusals

New module jazzx_sdk/fabric/canonical/refusal.py.
- Refusal model: refusal_id, reason_code (str), reason_class (str-enum RefusalClass: SUB_CONFIDENCE_EVIDENCE, HUMAN_ONLY_ACTION, PRECONDITION_FAILED, AUTHORITY_EXCEEDED, OUT_OF_SCOPE, POLICY_CONFLICT_UNRESOLVED), message, matrix_cell_ref (str|None), trace_id, actor_ref, occurred_at, remediation (str|None), domain_extensions.
- RefusalRegistry: pack-loadable mapping of reason_code -> {reason_class, description, http_status}; loader accepts YAML (from_dir pattern consistent with EvidenceTypeRegistry in fabric/canonical/evidence_types.py). Reason-code vocabularies are pack data; only RefusalClass is SDK-owned.
- server.py: add a refusal-aware exception/return path so a handler returning a Refusal maps to its registry http_status (403 for HUMAN_ONLY_ACTION, 412 PRECONDITION_FAILED, 409 POLICY_CONFLICT_UNRESOLVED, 422 defaults) with the Refusal serialized in the body. Anchor: the /invoke response handling in server.py.
- Design rule stated in module docstring: a Refusal is recorded on the trace (TraceStep outputs) and MAY produce an Outcome; it is never an exception.

Acceptance checks:
- tests/server/ test: handler returns Refusal(HUMAN_ONLY_ACTION) -> HTTP 403 with reason_code in body, and the invocation is recorded as completed, not errored.

## Phase 4 - Typed VersionBundle

- New VersionBundle model in fabric/canonical/trace.py (or values.py if trace.py is crowded): fields schema_version, model_versions (dict[str,str], required non-empty), prompt_version, policy_bundle_version, pack_version, overlay_version, execution_profile_version, skills_version, extra (dict). All optional except model_versions, mirroring the corpus rule that model_versions is required.
- TraceStepContextHelper.set_version_bundle: accept VersionBundle | dict, normalize to VersionBundle, store model_dump() (storage shape unchanged, so persisted traces stay readable).
- CanonicalDecision, ExperimentRun (evaluation/experiment/schema.py), and derived Artifact gain optional version_bundle: VersionBundle | None.
- Deterministic replay is explicitly OUT of this plan (tracked in gap analysis as deferred); this phase only makes the bundle typed and attachable so replay tooling has a stable contract later.
- Fix the Phase-0 latent defect while in evolve/: modes/evolve/evaluator.py _build_user_message must read outcome.result and outcome.learning_signals instead of outcome.outcome_class / outcome.metadata; keep a getattr fallback for pack subclasses that do define outcome_class.

Acceptance checks:
- Round-trip: set_version_bundle(VersionBundle(...)) then read from Trace.metadata reconstructs an equal VersionBundle.
- EvaluatorMode test with a bare canonical Outcome no longer raises AttributeError.

## Out of scope

Authority matrix and PolicyProfile (companion plan), event envelope and state machines (companion plan), any commercial-lending object definitions (JACI), byte-identical replay engine (deferred), OpenAPI/AsyncAPI generation (companion plan, partial).

## Version and sequencing

All four phases are additive and ship on the 2.0.0 line (the repo's version number holds across pushes; bumps are managed as deliberate events, not per-merge). Recommended order: Phases 2-4 first (Refusal and VersionBundle unblock the authority and events plans), Phase 1 with them or immediately after (Money/DecimalValue unblock the JACI wedge). The SpreadLine values flip waits for a declared breaking event batched with whatever else accumulates; nothing in this plan waits for it. CHANGELOG per repo convention (tests/test_version_sync.py enforces pyproject parity).
