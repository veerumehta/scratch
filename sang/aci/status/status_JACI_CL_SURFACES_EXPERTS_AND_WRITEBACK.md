# Plan: JACI Commercial Lending Surfaces, Expert Services, and AU-1 Writeback

**Status: predecessor plan's phases shipped; this plan's own Phases 1-7 not started (2026-07-27
audit).** Per this plan's own framing note below, `plan_JACI_COMMERCIAL_LENDING_LIVE_WIRING.md`'s
Phase 0 (submodule intake), server-shape SPA serving, `/scenario.json`, settings router, badge
overlay, and the multi-stage Dockerfile already shipped — that predates and is distinct from this
plan. This plan's own Phase 1 (`web_api.py` `/api` router, `GovernedRouter`), Phase 2 (X1/X2 expert
request/response services), Phase 3 (AU-1 writeback, `los/` adapter, `AU1Writeback`), and Phases
4-7 (event wiring, SPA seam, observability, environment/deploy) are all absent — `japes_handler.py`
still only has `investigate`/`cre-underwriting`, matching this plan's own "before" grounding notes
verbatim. One Sequencing-section item is already satisfied incidentally: `docs/plans/CAandPM/`
(the stale ~8.7MB dist snapshot Phase 7's sequencing names for deletion) was removed 2026-07-27 as
unrelated repo cleanup, ahead of the phase it was scoped under.

**Flag (from `docs/CL_SOURCE_RECONCILIATION.md`, 2026-07-27):** this plan's Phase 3 (AU-1/LOS
writeback seam) is the concrete artifact for the Financial Spreading PRD's residual open item
"first LOS/credit-platform integration target" — worth a cross-reference for whoever picks this up
next, not a scope change.

Author: Virendra Mehta · 2026-07-13 · Rev 2026-07-16 (added Phases 6-7 and hygiene items from the production-readiness review; see the framing note)
Repo: jaci · Baseline: 0.9.7 (dev) · Depends on: pack foundation plan (registers, schemas), wedge plan (operations it exposes), JAPES events/statemachine/automation plan (GovernedRouter, chassis, envelope)

Framing note (2026-07-16): an external production-readiness review of the Lovable SPA (Notion "Commercial Lending UI Application Production readiness check") reads the demo repo as a codebase to harden in place (18-48 week refactor: MFE split, Redux migration, decompose 5,738-line files, WCAG). That contradicts the seam strategy this plan encodes: the scripted SPA is a requirements input that JACI serves and retires screen by screen behind the governed /api, not the production artifact. Most of the review's P1 refactor list (MFE, state-management migration, oversized-file decomposition, bundle splitting on demo screens) is effort we do not spend, because those screens get replaced at the seam. The review's genuinely load-bearing findings that ARE ours map to phases here: no backend/API (Phase 1, the whole point of this plan), no RBAC/authorization (server-side authority matrix, JAPES authority plan + Phase 1 headers), no audit trail (JudgmentLedgerEntry/receipts/VersionBundle, already core), plus new hygiene and observability items folded in as Phases 6-7 and the pre-seam hygiene list below.
Supersedes: the unbuilt phases of plan_JACI_COMMERCIAL_LENDING_LIVE_WIRING.md (2026-07-03). Honest ledger of that plan: Phase 0 (submodule intake), server-shape SPA serving, /scenario.json, settings router, badge overlay, and the multi-stage Dockerfile shipped. The /api router (web_api.py), the web run shape, and the submodule seam (runtimeConfig.ts / JACI_WEB_MODE) were never built; the badge calling operation cre-underwriting is the entire live integration today. This plan replaces those phases with the corpus contract shapes rather than the older ad-hoc endpoint list (assess/verify-evidence/trace), which the corpus has since made obsolete.

Grounding notes (verified 2026-07-13 against dev):
- src/jaci/main.py dispatches JAPES_RUN_MODE ui|server|both|queue. No web shape. server shape = SDK serve() with /invoke + /health + /stream, static SPA from web/commercial-lending-demo/dist, extra_routes: settings router + scenario router.
- src/jaci/japes_handler.py operations: investigate (AML), cre-underwriting (demo badge). scenario_data.py serves /scenario.json from insurance_diligence cases; commercial_lending data is a TODO.
- Submodule pinned at 34a1666 (fresh Lovable export, branch lovable-demo, ignore dirty); dist committed; scripted CA/PM/CID scenarios; JACI-side web/japes/japesClient.ts + japesBadge.tsx overlaid at Docker build.
- Experts exist as in-conductor advisory classes (SDK DefaultPolicyExpert/DefaultPlaybookExpert configured from pack data, output GUIDANCE_REFS); no standalone endpoints.
- No LOS adapter, no writeback, no receipts anywhere.

## Phase 1 - /api router on the server shape

New src/jaci/web_api.py using the JAPES GovernedRouter (events/statemachine/automation plan Phase 4), mounted via extra_routes beside the existing settings/scenario routers. Do not add a new run shape; the corpus surfaces ride the existing server shape (decision recorded: the old plan's separate web shape is dropped, one less mode to deploy).
Endpoints, matching the corpus openapi.json paths and semantics:
- GET /api/health (liveness + pack/corpus versions).
- GET /api/config.json (surface config for the SPA seam: mode scripted|live per scenario, api base).
- POST /api/pipeline/runs -> wedge plan run_spread; mutating, Idempotency-Key = SourceFile content_hash; business_context required, parent_loan_ref required for servicing contexts (422 otherwise); refusals surface typed.
- POST /api/w1/{case_id}/promote-spread -> wedge plan promotion; declared cell_ref cl.am.004 path; 422 incomplete-package, 409 already-promoted returns existing ref.
- GET /api/traces/{trace_id} -> canonical TraceStore read (JudgmentLedgerEntry projection).
- POST /api/experts/x1/query, POST /api/experts/x2/query (Phase 2).
- POST /api/automation/au1/write (Phase 3).
Headers per corpus: X-Trace-Id, X-Actor-Ref, X-Surface-Ref on every op (GovernedRouter enforces); every mutating op appends to the trace.

Acceptance: contract tests against the corpus openapi.json for implemented paths (schemathesis or hand-rolled: status codes, required headers, refusal body shapes); /invoke and badge behavior unchanged.

## Phase 2 - X1/X2 expert services

- src/jaci/scenarios/commercial_lending/experts.py: wrap pack-configured DefaultPolicyExpert/DefaultPlaybookExpert as request/response services returning ExpertEvidence with attestation_state candidate. Corpus discipline: read-only, cited answers, never an approval; 422 out-of-scope; 409 conflict-unresolved returns BOTH citations without choosing (the DefaultPolicyExpert overlay conflict detection already identifies this case; surface it instead of resolving it).
- Attestation seam: POST /api/experts/evidence/{id}/attest (human, cell cl.eadm.002) flips candidate -> attested via the state machine; unattested expert evidence cannot be cited in governed outputs (wedge plan's Governor consumes this rule; expert.evidence.attested event emitted).
- X1 agency functions (evaluate_agency_requirement etc.) are declared in the router but return typed OUT_OF_SCOPE refusals until the agency overlay activates; the corpus treats scope refusal as a designed outcome, use it.
- X3 pricing: stub only. Router path exists, internal-network guard, returns OUT_OF_SCOPE refusal; real pricing binding is engagement-gated (credentials, internal_only_fields custody).

Acceptance: X1 query on the imported OCC policy assets returns cited ExpertEvidence(candidate); conflicting overlay fixture yields 409 with two citations; attested evidence flows into a Governor check; unattested is rejected there.

## Phase 3 - AU-1 writeback skeleton

- src/jaci/scenarios/commercial_lending/los/: MockLOSAdapter (fabric.entities-backed record store simulating nCino-class LOS with mutable external state for drift tests) + field mapping loaded from the imported connector_field_mapping data (object, field, jazzx_source, write_direction, human_gate per row).
- AU1Writeback(GovernedAutomation) using the JAPES chassis: idempotency_key + matrix_cell_ref mandatory; tier discipline from the imported matrix (D1/D2 auto, D3 only when overlay-enumerated, M/W require approval_ref); read-before-write drift check -> conflict receipt + 409-class refusal routed to human; WritebackReceipt with pre/post values persisted to fabric.canonical; writeback.receipt.confirmed event. No receipt means the write did not happen; the mock adapter test kills the process mid-write to prove the invariant.
- Wire the wedge plan's evidence-to-LOS staging as the first writeback consumer (spread fields to LOS after promotion).

Acceptance: REL-AU1-01-shaped tests: 100% of effected writes receipted; duplicate submit returns original receipt; drift fixture produces conflict receipt and no write; M-tier without approval_ref refuses 403-class.

## Phase 4 - Event emission wiring

- Register the imported event catalog (pack foundation) with the JAPES EventEmitter on server startup (hooks.py is the anchor for startup wiring); route through a CollectorChannel by default, WebhookChannel per settings for downstream consumers.
- Emit across the wedge + this plan: pipeline.run.* family, validation.finding.created, spread.decision.affirmed, spread.supersession.created, decision.recorded, outcome.recorded, expert.evidence.attested, writeback.receipt.confirmed, notification.sent (AU-3 minimal: log-only channel now, engagement rules later).

Acceptance: an end-to-end YETI run emits a catalog-valid event sequence; test asserts the sequence contains pipeline.run.started before any stage event and decision.recorded exactly once per affirmation.

## Phase 5 - React SPA seam (scripted -> live, one screen)

Submodule work on a JACI-driven branch of commercial-lending-demo (respect the pristine-submodule rule: changes land in the submodule repo, JACI bumps the pin; the Docker overlay trick stays for the badge only):
- src/lib/runtimeConfig.ts fetching /api/config.json (mode per scenario, defaults scripted so Lovable previews still work).
- CA scenario first (matches CID-first intent from the old plan being superseded by CA because the wedge makes CA the live-capable persona): DealPage financial highlights read from a live SpreadPackage via a thin fetch client; scripted fixtures remain the fallback when mode=scripted or fetch fails.
- Everything else stays scripted; the transition ledger (docs/status/CL_DEMO_TRANSITION_LEDGER.md, create it now) tracks screen-by-screen status; submodule retires when the ledger empties.

Acceptance: JACI_WEB_MODE-equivalent config flips CA highlights to live data from a real run; scripted mode byte-identical to today; ledger committed.

Pre-seam hygiene (do in Phase 5 alongside the CA screen, cheap and independent of architecture, from the production-readiness review):
- dangerouslySetInnerHTML audit: every use in the submodule becomes a latent XSS vector the moment live /api data flows through it. Sanitize or replace before the CA screen goes live; a lint rule bans new uses. This is gated by live data, so it belongs with the first live screen, not later.
- PII out of the bundle: lending documents and borrower data (names, emails, loan values) are shipped as static public assets today. Move them behind the /api (or into fixtures not served as public files) so no real-shaped PII sits in build artifacts. Even scripted, this is a data-handling issue.
- Dependency + lint hygiene: resolve the npm high-severity advisories that have fixes, and clear the lint error set on any file the seam touches (do not boil the ocean on demo-only screens that will retire).

## Phase 6 - Observability and error tracking

The /api is the productionized surface, so observability lives on it, not on the scripted screens. Server-side, on the JACI /api and handlers:
- Structured request logging keyed by trace_id (already propagated via X-Trace-Id), actor_ref, surface_ref, and outcome (success / typed refusal / error), so a refusal is distinguishable from a failure in logs and metrics.
- Error tracking on the server (Sentry-class), capturing unhandled exceptions with trace_id correlation; typed Refusals are NOT errors and must not page.
- Minimal usage/latency metrics per endpoint feeding the VP-2 2h-P90 instrumentation the wedge plan already emits (reuse vp.activity.* events; do not build a second telemetry path).
- SPA-side error tracking is deferred until a screen is live and non-scripted; scripted screens do not warrant it.

Acceptance: a run produces correlated logs (trace_id joins /api request -> pipeline events -> receipt); an induced server exception is captured with trace_id; a typed refusal appears in metrics as a refusal, not an error or a 5xx.

## Phase 7 - Environment and deploy strategy

The JACI image + ACA path already exist (Dockerfile multi-stage, server shape); this phase makes environments explicit rather than building CI from zero:
- Documented dev / staging / prod environment strategy: per-environment PolicyProfile/ExecutionProfile pins, corpus root pin, and connector instances (mock LOS in dev/staging, real only where an EP authorizes it); no governance constant baked into the image.
- CI gates on the JACI repo: lint + type check + the cl_mvdp test set + the corpus validator (make validate-cl from the foundation plan) on every PR; the image builds only on green.
- Config, not code, per environment: JAPES_RUN_MODE, JACI_WEB_MODE, JACI_CL_CORPUS_ROOT, connector creds via vault, never committed.

Acceptance: staging and prod differ only by pinned config (profile, corpus root, connectors), provably from one image; CI blocks a merge that fails validate-cl.

## Out of scope

A1/A2/A4/A5 assistants and W2 (later waves; A1 blocked on RM Cockpit option selection, A2 counsel-gated), AU-2 boarding (needs cl_sp runtime), real LOS/core connectors, AU-3 engagement rules, Streamlit consuming /api (worthwhile follow-up; note in ledger), agency endpoints activation.

## Sequencing

Phase 1 after JAPES GovernedRouter lands (or with a local shim replicating header/idempotency checks, deleted later). Phase 2 needs only pack foundation + wedge Phase 3 attestation cells. Phase 3 needs the JAPES automation chassis. Phases 4-5 last. Delete docs/plans/CAandPM/ (6.8 MB stale dist snapshot) as part of Phase 5 cleanup, per the old plan's own instruction. Phases 6-7 run alongside Phase 1 onward (observability on the /api from the moment it exists; environment strategy before the first non-dev deploy), not at the end. The pre-seam hygiene items land with the Phase 5 CA screen.
