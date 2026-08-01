# Done: Assurance Attribution and Source Precedence Resolver

Author: Virendra Mehta · Completed 2026-07-29
Repo: japes · Landed: dev commit `320003d` (unpushed), no version bump (stays 2.2.2)
Plan: docs/plans/plan_JAPES_2_3_0_SOURCE_PRECEDENCE.md (superseded by this file)

All 4 phases landed as planned. No new 2.3.0 minor — the plan's own header flagged the version
line as unconfirmed, and per project policy version bumps are deliberate, not per-landing; work
accumulates under `docs/status/CHANGELOG.md`'s `[Unreleased]` section until a real release
decision. This is Wave 1a of jaci's `plan_JACI_CL_PRD_COMPLETION.md`; verified end-to-end against
a real reference case in Wave 1e (`jaci` `done_JACI_CL_RB_REFERENCE_CASE.md`) — the LTM
construction and tie-break machinery below reproduce the Regional Bank reference workbook's own
LTM Sep-2023 column exactly, and the cash-flow-gap refusal fires correctly against that package's
real compilation-with-no-cash-flow-statement period.

## What shipped

- `jazzx_sdk/finance/periods.py`, new section "Source precedence (FR-SRC-1/2/3)":
  `StatementBasis` (GAAP/TAX/CASH); `SourceStatement` (a document's account of a period, distinct
  from the period itself — `document_ref`, `statement_type`, `period`, `statement`, `assurance`,
  `basis`, `reporting_currency`, `scale`, `preparer`, `received_at`); `SourcePrecedencePolicy` on
  `PolicyProfile` (institution-declared assurance ranking, fail-closed — `resolve_sources` raises
  naming the profile when absent, `ASSURANCE_RANK` is never a silent fallback); `SourceCandidate`/
  `SourceResolution`; `resolve_sources()` (picks the winning source per period+statement type,
  reports every candidate considered with its rank, refuses an unresolvable tie rather than
  picking arbitrarily).
- "Policy-driven construction (FR-SRC-3, FR-SRC-4)": `SourcePrecedenceFinding` (a narrow,
  SDK-internal signal — not the platform's canonical Finding/Decision type);
  `construct_ltm_from_sources()` (resolves each LTM component's winning source via
  `resolve_sources` rather than requiring the caller to have already chosen one, delegates to the
  existing `construct_ltm`, and surfaces two FR-SRC-4 conditions: a lower-assurance interim
  feeding the decision-relevant column, and the spread relying on staler data than what's
  available).
- `jazzx_sdk/fabric/canonical/profiles.py`: `PolicyProfile.source_precedence` field (string
  forward-ref, resolved via `periods.py`'s own `model_rebuild()` call, mirroring the pre-existing
  `spread.py`↔`periods.py` cycle-resolution pattern already in the file).
- 19 tests in `tests/test_finance_source_precedence.py`.

## Correction found during authoring

`resolve_sources`'s tie-break (`tie_break="most_recent"`) originally used `period.end` to
discriminate ties, which is structurally impossible — two candidates for the *same* target period
always share an identical `period.end` by construction. Caught by writing the tie-break test
itself. Fixed by adding `SourceStatement.received_at: date | None` (a document-level timestamp,
distinct from the period it describes) and rewriting the tie-break to use it.

## Acceptance criteria — verified

- `resolve_sources` picks the correctly-ranked source, reports losers (not discarded — FR-AUD-1),
  and refuses (typed `Refusal`, not an arbitrary pick) on a genuine top-rank tie.
- `construct_ltm_from_sources` reproduces `construct_ltm`'s output exactly when given
  already-resolved sources, and additionally emits the two FR-SRC-4 findings on the fixtures built
  to trigger them.
- Full japes suite green (no regressions); cross-checked against jaci's real RB reference case in
  Wave 1e — not just synthetic fixtures.
