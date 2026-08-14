# Plan: Japes / eval-service contract convergence

> **Status (2026-08-10): Phases 0-5 built, uncommitted.** New package `jazzx_eval_contracts/`
> (own `pyproject.toml`, `pydantic`-only — verified via a throwaway venv install) with every
> contract listed below across `identity.py`/`feedback.py`/`evidence.py`/`attribution.py`/
> `learning.py`/`scoring.py`/`execution.py`, plus a JSON-Schema snapshot test per model
> (`tests/test_schema_snapshots.py` + `scripts/regenerate_schema_snapshots.py`). Japes-side:
> `jazzx_sdk/evaluation/eval_service_adapters.py` (all seven adapters — feedback submission,
> two canonical-promotion adapters, learning-candidate→signal, scorer/case→verdict/evaluation,
> failure→FailureV1), `jazzx_sdk/evaluation/feedback_sink.py` (`EvalServiceFeedbackSink`),
> `jazzx_sdk/evaluation/attribution_protocols.py` (`EvidenceProvider`/`AttributionAnalyzer`
> Protocols). Additive edits: `DecisionType.ATTRIBUTION` (`fabric/canonical/decision.py`),
> `GuidanceProvenance.attribution_id`/`evidence_ids`/`learning_candidate_id`/
> `learning_candidate_version` (`fabric/guidance/schema.py`), `ImprovementSignal.attribution_id`/
> `evidence_ids` (`modes/schemas.py`), `synthesize_bucket` provenance propagation
> (`modes/evolve/curator.py`), `Feedback.to_signal()` docstring labeled local/offline-only. Full
> suite green (2576 passed, 3 skipped) — zero regressions. **Phase 6 not started** (hard-blocked
> on eval-service Phase E, which doesn't exist yet). eval-service Phases A-F untouched (different
> repo). Nothing pushed or committed — see the CLAUDE.md push-gate policy.

Source: `046e37e4-df2d-470d-a655-28212258ba66_Japes_and_eval-service_contract_convergence_Proposal.pdf`
(baselined against Japes `dev`@`dc4e376`/2.3.3 2026-08-05, eval-service `main`@`edd3cfb` 2026-07-30).
Japes is currently at `dev`@`95e2fa1`/2.3.5 (2026-08-10); the 5 commits between the proposal's
baseline and here touch `agents/definition_store*`, `agents/interactive/*`, `manifest/spec_binding.py`,
and add one field (`agent_id`) to `jazzx_sdk/evaluation/feedback.py` — none of it conflicts with or
overlaps this plan.

**Scope note:** jaci is excluded from this plan by design — it's a private downstream consumer, not
a party to the Japes/eval-service contract. This plan covers only what Japes-repo work can ship
unilaterally, plus the eval-service-side phases it depends on (tracked here as coordination
checkpoints, not implemented from this repo).

## Two grounding decisions the proposal left open

**1. The contract package must be a physically separate distribution, not "japes with no extras."**
Checked `pyproject.toml`: `fastapi`, `starlette`, `uvicorn`, `sqlalchemy`, `asyncpg`, and
`azure-storage-queue` are core (unconditional) dependencies of the `japes` package today — not
listed under `[tool.poetry.extras]` (only `mcp`/`jinja2`/`openpyxl`/`google-genai`/`mlflow`/`litellm`/
`redis`/`azure-ai-documentintelligence` are optional). So `pip install japes` — regardless of what
gets imported at runtime — pulls the full server/queue dependency tree. The proposal's constraint
("must not import FastAPI, SQLModel, queues, MLflow, Kernel clients, or JazzXRuntime") can't be met
by import-laziness alone; it needs a real second package.

Correction from build time: `common/pyproject.toml` turned out to be a *git submodule* pointing at
a separate `JazzX-LLC/common` repo, not proof this repo's own tooling multi-builds from one tree —
and it uses `package-mode = false` (dependency management only, not a distributable). Neither
applies here: `jazzx_eval_contracts/` is a real subdirectory of *this* repo with its own
`pyproject.toml`, default package mode (buildable/installable — eval-service needs to actually
depend on it), and `pydantic` as its only dependency — verified by installing it into a throwaway
venv and confirming zero of fastapi/starlette/sqlalchemy/asyncpg/azure-storage-queue/mlflow load.

**2. Reaction-vocabulary reconciliation.** Japes' internal `Reaction` enum
(`jazzx_sdk/evaluation/feedback.py`) is three-valued (`positive`/`negative`/`neutral`, defaulting to
neutral). The proposal's wire-level `FeedbackReaction` is binary (`thumbs_up`/`thumbs_down`,
required, never defaulted). Resolution: the wire enum and the mapping live in the adapter (Phase 1),
not by changing Japes' internal enum — `positive→thumbs_up`, `negative→thumbs_down`, and `neutral`
is rejected at the adapter boundary (raise, don't silently pick a side) per the proposal's explicit
rule that neutral "remains unclassified and requires explicit producer or reviewer action; it is
never silently mapped." Existing in-process `Feedback(reaction=...)` callers are unaffected.

**3. Attribution/evidence/approved-learning must not become a second parallel vocabulary next to
Japes' existing IIF-Charter canonical spine.** `jazzx_sdk/fabric/canonical/{decision,evidence,trace}.py`
already ships spec-compliant `CanonicalDecision` (evidence-backed, confidence-scored, `evidence_refs`/
`guidance_refs`/`trace_id`, produced by an actor), `CanonicalEvidenceObject` (`attestation`,
`confidence`, `freshness`, `provenance_chain`, `content_hash`), and `CanonicalTrace` — the proposal
was written with no visibility into this layer and reinvents pieces of it under new names. Checked
each proposed type against it (see Phases 2 and 6 below for the resulting changes):

- **`ApprovedLearningAssetV1` — dropped entirely.** `fabric/guidance/schema.py::GuidanceAsset` +
  `GuidanceProvenance` already have every field the proposal wants (confidence, provenance incl.
  `feedback_id`, trigger_patterns, version, applicability≈scope), and `GuidanceAsset.to_guidance_ref()`
  already bridges into `CanonicalDecision.guidance_refs` (making Guidance Effectiveness §10.4
  computable). `EvalServiceGuidanceStore` already returns `GuidanceAsset` — it fabricates fields
  today only because eval-service's endpoint doesn't exist yet. No new wire type needed.
- **`EvidenceRefV1`/`EvidenceBundleV1` — kept, but as a lean runtime form that must promote to
  `CanonicalEvidenceObject`, not a permanent second vocabulary.** The one real gap canonical evidence
  lacks — `EvidenceAvailability` (not_found/unavailable/access_denied/error; canonical evidence
  currently assumes evidence exists once captured) — is worth adding. This mirrors the pattern
  `CanonicalEvidenceObject`'s own docstring already sanctions elsewhere ("Domain Packs may use leaner
  operational forms during runtime... and promote to canonical when assembling final artifacts").
- **`CandidateCauseV1`/`FeedbackAttributionV1` — kept as a lean runtime form for the same reason**,
  not force-fit into `CanonicalDecision` (which mandates `pack_id`/`autonomy_level`/
  `human_review_required` — an awkward fit for feedback that isn't always pack-scoped). But a
  `→ CanonicalDecision` promotion adapter is now a required deliverable, not optional — otherwise
  attribution never enters the audit trail everything else in Japes is committed to.
- **`TraceRefV1`, `LearningCandidateV1`, `FeedbackSubmissionV1`/`FeedbackAcceptedV1`,
  `ScorerVerdictV1`/`CaseEvaluationV1`/`ExecutionResultV1` — no canonical overlap, kept as proposed.**
  `TraceRefV1` is a correlation pointer, `CanonicalTrace` is the full audit object it may point to —
  different scope, not competing. `LearningCandidateV1` is genuinely new: `ImprovementSignal`
  (`jazzx_sdk/modes/schemas.py`) is deliberately a thin routing hint, not a governed proposal with
  evidence/scope/regression-risk.

## Sequencing rule

Phases 0–5 are Japes-repo-only and additive: new contract types plus adapters over Japes' *existing*
types (`Feedback`, `ScorerResult`, `CaseResult`, `EvalServiceClient`, `EvalServiceGuidanceStore`).
None of them change existing behavior for callers who don't touch the new surface, and none of them
require eval-service to have shipped anything first — they can all merge on Japes' own timeline.
Only two things are genuinely blocked on the other repo: Phase 1's *live* integration test (needs
eval-service to accept `FeedbackSubmissionV1`) and Phase 6 (needs eval-service's approved-learning
read endpoint to exist at all — there's nothing to adapt to yet). Everything else is unblocked.

---

## Phase 0 — Contract package scaffold

New package `jazzx-eval-contracts` (own `pyproject.toml`, `package-mode = false` like `common`),
subdirectory of this repo, dependency = `pydantic>=2.0` only.

- `EntityRefV1`, `SourceRefV1`, `TraceRefV1` (identity/correlation contracts — no others yet).
- `FeedbackReaction` (binary, wire-level) as its own enum, distinct from Japes' internal `Reaction`.
- JSON Schema export + a snapshot test so an accidental breaking field change fails CI, not a
  consumer's deploy.
- **Exit criteria:** package builds and installs standalone; `python -c "import
  jazzx_eval_contracts"` pulls zero of fastapi/starlette/sqlalchemy/asyncpg/azure-storage-queue/
  mlflow. Zero consumers yet — pure definition.

## Phase 1 — Feedback contract + Japes-side adapters

- Add `FeedbackContextV1`, `FeedbackSubmissionV1`, `FeedbackAcceptedV1` to the contract package.
- `jazzx_sdk`: adapter `Feedback → FeedbackSubmissionV1` implementing the reaction mapping from
  decision 2 above. Lives alongside `Feedback`, doesn't change its defaults.
- Add `EvalServiceFeedbackSink` — a write counterpart to the existing read-only
  `jazzx_sdk/clients/eval_service_client.py::EvalServiceClient` — POSTs `FeedbackSubmissionV1`,
  returns `FeedbackAcceptedV1`. Client generates `event_id` once per logical submission so retries
  are replay-safe by construction (matches "eval-service generates `feedback_id`; `event_id` is the
  producer idempotency key").
- `InProcessFeedbackStore`/`DbFeedbackStore` untouched — this sink is additive, not a replacement
  (explicit non-goal: "Making Japes local feedback storage a second production source of truth").
- **Exit criteria:** contract round-trips against Phase 0's JSON Schema fixtures; sink has a
  mocked-httpx test suite mirroring `EvalServiceClient`'s existing test pattern. Live
  integration test is a separate, later checkpoint — gated on eval-service Phase B below.

## Phase 2 — Evidence & attribution contracts + Protocols

- Add `EvidenceAvailability`, `EvidenceRefV1`, `SignalCheckV1`, `EvidenceBundleV1`,
  `AttributionStrength`, `CandidateCauseV1`, `FeedbackAttributionV1`, `AttributionJobStatus` to the
  contract package — lean runtime forms per decision 3 above, not replacements for the canonical
  types.
- Define `EvidenceProvider` and `AttributionAnalyzer` as `Protocol`s in `jazzx_sdk` (Japes owns
  "generic attribution analysis" per the proposal's ownership table — pluggable, not eval-service-
  owned). Ship the typed seam only; zero concrete providers/analyzers.
- **New, required (not in the original proposal):** two promotion adapters in `jazzx_sdk`:
  `EvidenceBundleV1 → list[CanonicalEvidenceObject]` (mapping `EvidenceAvailability` into
  `attestation`/a new not-null-safe `content` state — canonical evidence has no "absent" case
  today, this is where that gap actually gets closed) and `FeedbackAttributionV1 →
  CanonicalDecision` (`DecisionType` gets a new `ATTRIBUTION` value; `confidence`/`evidence_refs`/
  `created_by` map directly, `rationale` takes `summary`+`observed_behavior`). Both adapters are
  best-effort/optional-call, not a mandatory step in the flow — attribution and evidence still work
  without KH promotion; this just makes promotion possible where a caller wants the audit trail.
- **Exit criteria:** a fixture-based test with a fake in-repo provider/analyzer implementing each
  Protocol proves the seam typechecks and is usable end to end; the two promotion adapters round-trip
  a `FeedbackAttributionV1`/`EvidenceBundleV1` fixture into valid `CanonicalDecision`/
  `CanonicalEvidenceObject` instances. No behavior change anywhere else.
- This unblocks eval-service wrapping its existing Juno meta-profile client (`app/feedback/
  juno_client.py`) as the first real `AttributionAnalyzer` — that implementation is eval-service's,
  not built here.

## Phase 3 — Learning-candidate contract + provenance-aware conversion

- Add `LearningIntent`, `LearningChangeType`, `LearningCandidateV1` to the contract package.
- New adapter `LearningCandidateV1 → ImprovementSignal`, carrying `feedback_id` + `attribution_id` +
  `evidence_ids` through to Curator routing (`jazzx_sdk/modes/evolve/curator.py`).
- Existing `Feedback.to_signal()` stays working (no breaking change) but its docstring gets an
  explicit "local/offline use only" label per the proposal's line that direct conversion should be
  "deprecated or explicitly labeled local/offline only" for service-backed feedback. Surgical —
  docstring only, no deprecation warnings, no callers touched.
- **Exit criteria:** Curator can synthesize a `GuidanceAsset(status=DRAFT)` from a
  `LearningCandidateV1` batch through the new adapter; existing `to_signal()` callers unaffected.

## Phase 4 — Scoring & execution contracts

- Add `QualityVerdict`, `ScorerRefV1`, `ScorerVerdictV1`, `CaseEvaluationV1`, `ExecutionStatus`,
  `ExecutionResultV1` to the contract package.
- Lossless adapters: `ScorerResult → ScorerVerdictV1` (`skipped=True → SKIP`, else
  `passed → PASS/FAIL`) and `CaseResult → CaseEvaluationV1`. Pure translation; Japes' own
  `jazzx_sdk/evaluation/scorers.py` / `harness/results.py` shapes are untouched.
- **Exit criteria:** round-trip tests proving zero information loss (name/score/confidence/
  threshold/metrics/comment/metadata all preserved) — this is acceptance criterion #13 from the
  proposal, verified directly rather than assumed.

## Phase 5 — Trace contract generalization

- Add `TraceRefV1` (kind-tagged: `mlflow`/`otel`/`japes`/other) to the contract package.
- Extend the `Feedback → FeedbackContextV1` adapter (Phase 1) to populate `trace_refs:
  list[TraceRefV1]` alongside the existing single `trace_id` string. Additive field; the old
  string stays for back-compat.
- **Exit criteria:** existing `TraceSource.read_trace` callers unaffected; new adapter path
  available for any producer wanting multi-trace-kind linkage.

## Phase 6 — Approved-learning read model (blocked on eval-service Phase E)

- **No new contract type** (revised per decision 3 above — `ApprovedLearningAssetV1` is dropped;
  `GuidanceAsset`/`GuidanceProvenance` already are the contract).
- Replace `jazzx_sdk/fabric/guidance/eval_service_store.py::EvalServiceGuidanceStore
  ._to_guidance_asset`'s fabricated fields — flat `1.0` score, truncated-text-as-trigger-pattern,
  hardcoded `ConfidenceWeight.STANDARD`, hardcoded `GuidanceStatus.DEPLOYED` — with real values read
  directly off eval-service's response once its endpoint returns `GuidanceAsset`-shaped fields
  (confidence/provenance/trigger_patterns/version/applicability) plus a per-query relevance score.
- **Hard external dependency.** This is the one Japes change that's actually blocked on the other
  repo shipping something new, not just benefiting from convergence — there's no endpoint to point
  the adapter at yet.
- **Exit criteria:** `EvalServiceGuidanceStore`'s test suite asserts real (not fabricated) fields;
  the `_TRIGGER_PATTERN_MAX_LEN` truncation workaround and its accompanying "eval-service has no
  confidence-weight concept" comment become removable.

---

## eval-service-side phases (tracked, not executed from this repo)

Listed so Japes' own sequencing above is legible against what it's actually waiting on. Each names
the specific Japes phase it unblocks.

| Phase | Deliverable | Unblocks |
|---|---|---|
| A | Adopt `jazzx-eval-contracts` as a pinned dependency; typed nullable `rating: [0,1]` on `FeedbackCreate` and the durable row | — |
| B | Accept `FeedbackSubmissionV1`, generate `feedback_id`, dedupe on `event_id`, return `FeedbackAcceptedV1`; entity-binding table for `SourceRefV1` resolution | Japes Phase 1 live integration |
| C | Transactional outbox + resumable Attribution Coordinator; generic evidence-provider / `AttributionAnalyzer` registries implementing Japes Phase 2's Protocols; wrap the existing Juno client as the first analyzer adapter | Japes Phase 2 has a real implementation to point at |
| D | Learning Candidate Builder (reaction + rating + attribution + quality/actionability → `LearningCandidateV1`); candidate review/approval events | Japes Phase 3 has real candidates to consume |
| E | Publish the approved-learning read endpoint returning `GuidanceAsset`-shaped fields (real scope/confidence/provenance/version) plus a per-query retrieval score — not a bespoke `ApprovedLearningAssetV1` shape, since Japes already owns that object | **Japes Phase 6** |
| F | Persist `CaseEvaluationV1` independent of `TestCaseRun.status` | Japes Phase 4 has a live producer |

## Non-goals (carried from the proposal, unchanged)

Replacing MLflow in eval-service; hosting the eval-service API/control plane on `JazzXRuntime`;
sharing SQLModel persistence classes between the two repos; making Japes local feedback storage a
second production source of truth; requiring Juno as the permanent attribution engine; copying all
source-system evidence into eval-service; forcing external conversation/message/invocation/trace
IDs into UUID; auto-converting raw feedback into production guidance; treating every thumbs-up/down
as sufficiently specific to produce learning on its own.
