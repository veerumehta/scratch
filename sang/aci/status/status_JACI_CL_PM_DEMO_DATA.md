# Plan: Portfolio Manager Demo — data contract + conductor build

Author: Virendra Mehta · 2026-07-16 · DRAFT (sketch)
Repo: jaci · Driver: the "Commercial Portfolio Surveillance & Annual Review" demo (Portfolio Manager
storyboard, `docs/Portfolio Manager - Demo_v02 draft.pdf`). UI is built in **Lovable** and pulled into
jaci as the `web/commercial-lending-demo` submodule; **jaci owns the data + assets + the conductor that
builds them**. The demo reads its figures from jaci, not hard-coded fixtures — polished UI, real source.

## What already exists (verified 2026-07-16)

- `scenarios/portfolio_monitoring/` IS the PM Annual Review scenario: `PortfolioReviewCase`,
  `DscrReconciliation` (CCC vs loan-agreement definition), `Occupancy`, `RiskAction`
  (Reaffirm/Watchlist/Downgrade), `ReviewSection`; `BOOK` (japes `Portfolio` aggregate over `BookEntry`),
  `METRICS`, `PIPELINE` (stage labels), `REVIEWS` (keyed cases), `GROVE_COMMONS` (Cedar Grove).
- `portfolio_monitoring/intake.py` already builds a `PortfolioReviewCase` from source docs: spreads the
  **T-12** (shared `commercial_lending` spreader), parses the **loan agreement** (DSCR floor / debt
  service / maturity), the **CCC** (attested DSCR + reconciling item), the **rent roll** (occupancy) — all
  deterministic over SDK-converted markdown. This is today's "conductor" — bespoke functions, not the
  japes `ConductorEngine`.
- `scenario_data.py` serves `GET /scenario.json` (the seam the Lovable app reads); `build_scenario()`
  currently emits only `insurance_diligence` — **commercial-lending / PM is a TODO** ("CA/PM dashboards to
  follow, same pattern").
- Submodule pinned at `34a1666` (the older CA/PM/CID Lovable export); the Demo_v02 PM app will be a new
  Lovable build, pinned when ready.

So the work is: (1) define the demo's data contract, (2) serialize `portfolio_monitoring` into it, (3) move
`intake.py`'s assembly onto the capability pipeline (the "conductor"), (4) sort images/assets.

## Phase 1 — the data contract (the stable seam Lovable reads)

Pydantic models (`portfolio_monitoring/scenario_contract.py`) → JSON, mapped from the storyboard screens.
This is the FIRST concrete artifact — the Lovable build binds to it; agree it before the UI hardens.
Shape (derived from Demo_v02):
- `persona`: {name, title, business_unit, portfolio_context (institution, relationships_managed=42,
  outstanding≈$310M, asset_focus, reviews_due=12, covenant_tests=47)} — Screens 3–4.
- `dashboard`: `key_metrics` (Covenant Tests Run 47 · Servicing Assessments 12 · Avg Jazz AR Prep 14 min,
  each {value, color, hover}); `jazztrack_nodes` (5: New Reporting 6/42, Post-Review Conditions 2/42,
  Annual Reviews Due 12/42, Active Monitoring 42, Submitted to CO 9); `attention_zone` {count, sub_label,
  rows[]} — Screen 5.
- `annual_review_queue`: rows[] {relationship, borrower, exposure, last_rating, ar_due_days, jazz_signal
  (elevated/ready + reason), status} + per-row expand `detail` (the relationship card fields: focal
  collateral, loans, DSCR calc vs floor, occupancy vs floor, CCC status, guarantor PFS, site visit, Jazz
  prep, last outcome, trend) — Screens 7–9 (Cedar Grove, Shops at Worthington Square, Maple Run Plaza).
- `relationship_detail`: the full card per relationship (keyed by id) — the expand + "Open Relationship".

Every value keeps its provenance/confidence lineage available (the demo's "point to 14 minutes / Jazz did
the groundwork" story) — the contract carries `jazz_signal` + optional `provenance_ref` per figure.

Acceptance: `scenario_contract` round-trips the three Demo_v02 relationships to the exact storyboard
figures (Cedar Grove DSCR 1.15x/1.20x, occupancy 79%/80%, CCC discrepancy, PFS 18mo; Shops 1.24x rollover;
Maple Run 1.38x pass).

## Phase 2 — serialize portfolio_monitoring → contract; wire into /scenario.json

`portfolio_monitoring/scenario.py::to_scenario()` maps `BOOK`/`METRICS`/`REVIEWS`/cases → the Phase-1
contract; `scenario_data.build_scenario()` gains `"commercial_lending": to_scenario()` beside
`insurance_diligence`. Route unchanged. Scripted fallback stays (the app ships a static `scenario.json`
for Lovable previews; jaci overrides it live same-origin).

Acceptance: `GET /scenario.json` returns the PM payload; a contract test asserts the three relationships +
dashboard counts match the storyboard.

## Phase 3 — the conductor build (move intake.py onto the capability pipeline)

Recast `intake.py`'s bespoke assembly as a **cl_sp capability pipeline** on the JAPES `ConductorEngine` +
`StepRegistry` (reusing the capabilities already built), so the demo data is conductor-produced, not
hand-wired:
- Reuse **document-intake** (ingest/classify the T-12, loan agreement, CCC, rent roll → `SourceFile`/
  `ExtractedField`) and **financial-spreading** (T-12 → `SpreadPackage` → NOI/DSCR via `metric_result`).
- New **cl_sp** capability steps (register as impls; a `pipelines.yaml` binds them by `impl:`):
  - `sp.reconcile_ccc` — reconcile borrower-attested DSCR vs bank-side calc vs loan-agreement definition
    (`jazzx_sdk.reconcile` + `credit-validation`'s `detect_reconciliation_mismatches` /
    `detect_cross_document_contradictions`) → `DscrReconciliation` + a discrepancy finding.
  - `sp.covenant_test` — DSCR/occupancy vs floor (`tools.ratio_evaluator.evaluate_covenant_policy` +
    `validate_package`) → covenant findings; `detect_staleness` for the guarantor-PFS 18-month exception.
  - `sp.assemble_ar` — assemble the `PortfolioReviewCase` (AR package) from the above, provenance-complete.
  - `sp.risk_action` — Reaffirm / Watchlist / Downgrade from the findings + trend (the PM judgment surface;
    human-confirmed like the cl_of affirmation — reuse the `underwriting-decision` promotion pattern:
    Jazz drafts, PM confirms, submit to Credit Officer).
- Portfolio aggregate: run the per-relationship pipeline across the book, aggregate into `BOOK`/`METRICS`/
  JazzTrack nodes/attention zone via the japes `Portfolio` aggregate. `to_scenario()` (Phase 2) then
  serializes the conductor outputs — one source, scripted → live per screen (surfaces-plan discipline).

Acceptance: the pipeline reproduces the three relationships' figures end to end (equivalence with the
Phase-1 fixtures) with every emitted value provenance+confidence complete (XF-1).

## Images / assets

- **UI chrome** (Jordan headshot, Jazz avatar, logo, screen backgrounds) — bundled in the Lovable app's
  `public/`; not jaci's concern (the submodule owns them).
- **Data-driven images** (collateral photos per relationship — Cedar Grove Commons, Shops at Worthington
  Square, Maple Run Plaza) — referenced by URL in the contract (`relationship_detail.collateral_image`);
  served either from the app's `public/` keyed by relationship id, or a jaci `/assets/{id}.jpg` static
  route if we want them source-controlled with the data. Recommend app-`public/` for the demo (simplest),
  a jaci static route later if images become data. Keep image *references* in the JSON, bytes out of it.

## Sequencing

Phase 1 first (contract) — it unblocks the Lovable build and is the agreement point. Phase 2 (serialize +
serve) makes the demo live off `portfolio_monitoring` immediately, with the scripted fallback intact.
Phase 3 (conductor) can follow without changing the route or contract — it swaps the *source* behind
`to_scenario()` from `intake.py`'s functions to the capability pipeline. Images: decide app-`public/` vs
jaci static when the Lovable build lands.

## Out of scope

The Lovable UI itself (built there, pinned as the submodule); the `/api` GovernedRouter surface (surfaces
plan — `/scenario.json` is enough for a read-only demo; add `/api` when the demo needs live mutation);
writeback; the cl_sp pack registers (foundation plan, corpus-gated).
