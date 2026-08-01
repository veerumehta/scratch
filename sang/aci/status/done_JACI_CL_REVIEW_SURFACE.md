# Done: Review Surface and Override Lineage

Author: Virendra Mehta · Completed 2026-07-30
Repo: jaci (+ 4 japes edits) · Landed: jaci dev `b4a552d` (v0.12.0), japes dev `b80698d`
(unpushed, japes stays 2.2.2)
Plan: docs/plans/plan_JACI_CL_REVIEW_SURFACE.md (superseded by this file)

All 5 phases landed. Wave 3b of `plan_JACI_CL_PRD_COMPLETION.md`. One real grounding gap in the
plan's own text found and fixed before writing Phase 5's code (not assumed away): the plan says
promotion is "already" authority-gated through the matrix, but `promote_spread` had no
`check_action` call at all — only `affirm_spread` did.

## Grounding correction: `promote_spread` was not actually authority-gated

The plan's Phase 5 text reads "Each transition carries its own actor and is authority-gated
through the matrix, which `affirm_spread` and `promote_spread` already consult" — checked
`promotion.py` directly and `promote_spread` never called `check_action`; it only checked the
ledger, the affirmation decision, and open blocking findings. Fixed by giving `promote_spread` an
**optional** authority gate (`matrix`/`approved_by`/`actor_class="approver"`/`evidence_types`,
new cell `cl.am.005`) that only activates when a caller passes `matrix` — every existing call site
(including `test_promotion.py`'s own direct tests) is completely unaffected, and
`hitl_approval._apply` only threads the matrix through when `decision.roles` is set, so a legacy
(roleless) decision keeps its exact pre-Phase-5 behavior.

## What shipped

- **Phase 1 — `Correction` as a governed object** (`corrections.py`): replaces
  `SmeDecision.corrections`' bare `dict[str, Any]` with `Correction` (target, new value,
  superseded value **read from the package**, author, timestamp, category, required rationale —
  same posture as `normalize.reviewer_add_back`'s existing rationale requirement). `CorrectionTarget`
  declares all four kinds the plan's text names (line value / classification / mapping / metric
  input); only `LINE_VALUE` is wired into `apply_corrections` today — the other three are real,
  constructible, but refused (not silently mis-applied) if submitted, since this plan states no
  acceptance criterion that exercises them. The old dict form still works for one release via
  `coerce_legacy_corrections`.
- **Phase 2 — apply and re-propagate** (`corrections.py` + `hitl_approval._apply`):
  `apply_corrections` produces a *new* `SpreadPackage` layer (as-reported never mutated, same
  discipline as add-backs/reclassifications), each corrected line carrying the new
  `ProvenanceType.OVERRIDE` (japes). `_apply` now applies corrections and re-validates the
  corrected package (`ctx.revalidate` or a plain `validate_package` default) instead of rectifying
  flagged findings by fiat — a finding is gone because the arithmetic changed, never because
  someone signed a form. Re-propagation needed no new graph: `compute_metric_results`/
  `validate_package` already trace to whatever value is currently in the package, so a corrected
  line automatically flows into every downstream metric and covenant test. A correction whose
  target doesn't resolve or whose kind isn't yet implemented refuses (typed `Refusal`) rather than
  being silently dropped or partially applied.
- **Phase 3 — risk-ranked review queue** (`review_ranking.py`): `rank_for_review` orders findings
  by severity + cell confidence + line magnitude (relative to its own statement) + whether the
  cell feeds a covenant test. The covenant-feeding input reuses `template.py`'s own
  chart-of-accounts binding closure — promoted from `_scoa_leaves_for_metric` to public
  `scoa_leaves_for_metric` rather than reimplemented — combined with `policies.covenant_metric_ids`.
  Weights are a plain dict override (institution policy, e.g. a profile's `custom` key), never
  hardcoded constants.
- **Phase 4 — side-by-side source view + reverse lookup** (`source_view.py`):
  `resolve_source_region` turns a cell's `SourceCoordinate` into what a reviewer should see (a
  named region, whole-page with the imprecision stated, a workbook cell, a named section, or an
  honest "no provenance" — never raises). `reverse_lookup`/`cells_fed_by` invert the per-cell
  coordinate index (cheap — coordinates are already stored per cell). **Correction to the plan's
  own assumption**: Phase 4's text says to render a region "where the coordinate carries a
  bounding box" — `PageLocator` has no bounding box, only `page: int` and an optional free-text
  `region: str`; implemented the distinction the schema actually supports (named region vs.
  whole-page) rather than inventing a bounding-box field. **Streamlit UI wiring is deliberately
  not done** — no browser available to verify rendering in this session, and the UI's current data
  model (`ui/shared.py` renders plain `FinancialSpread`, no provenance) doesn't carry
  `SpreadPackage`/`SourceCoordinate` objects yet; same deferral Wave 3a made for the download
  buttons, for the same reason.
- **Phase 5 — maker-checker roles** (`hitl_approval.py` + `promotion.py`): `MakerCheckerRoles`
  (analyst/reviewer/approver), `check_maker_checker_roles` (refuses when the same actor occupies
  two roles, unless `self_review_permitted` reads `allow_self_review` off the profile — `False`,
  the safer default, when the profile says nothing). `promote_spread`'s new optional gate (above)
  makes the approver role genuinely authority-checked. `exception_summary` — the per-spread
  exception summary the approver sees — is built from the exact same two functions
  (`suggested_action`, `locator_text`) the governed workbook's own Exceptions sheet uses, promoted
  from module-private to public in japes so the content is identical by construction, not by
  coincidence.
- 39 new tests across 5 files (`test_corrections.py` ×8, `test_review_ranking.py` ×4,
  `test_source_view.py` ×9, `test_maker_checker.py` ×10) plus fixes to 2 existing
  `test_hitl_approval.py` tests that encoded the exact "rectified by fiat" behavior this plan
  replaces.

## Acceptance criteria — verified

- A correction without a rationale is refused; the superseded value on a `Correction` is asserted
  against the real package, not trusted from the caller; existing dict-form callers still work.
- Correcting a line that feeds `leverage_x` (via a real `operating_income` correction) changes the
  covenant test result (`evaluate_covenant_policy`, pass → fail) and the correction appears in
  `ebitda`'s own re-derived `MetricResult.derivation.inputs`; a correction targeting a nonexistent
  key refuses rather than being ignored.
- A covenant-feeding finding outranks a same-severity, non-feeding finding by default weights; the
  ordering flips when `weights` de-emphasizes the covenant term and emphasizes confidence instead.
- Every populated cell on a real YETI package and a real RB package (`test_rb_reference_case`'s
  own `_pkg_with_lines` fixture, real reference-workbook bad-debt figures) resolves to a viewable
  region; reverse lookup from one coordinate returns every period of the line that shares it.
- A spread requires two distinct actors when the profile forbids self-review (the default) and one
  when it explicitly permits it (`custom={"allow_self_review": True}`); the approver identity is
  recorded on the resulting `PromotedSpread.promoted_by`. The exception summary is
  content-identical (description/severity/source/suggested-action, row for row) to a real
  `GovernedWorkbook`'s Exceptions sheet built from the same findings.
- Full jaci suite: 752 passed (was 742 before Wave 3b's own tests), 8 skipped, 5 xfailed; the same
  6 pre-existing, unrelated failures present before this work (AML/KYC reasoner signature
  mismatch, threat-intel handler, anthropic token tracking) are unchanged — confirmed none touch
  `commercial_lending`. Full japes suite: 1932 passed, 3 skipped, no regressions.
- `docs/plans/PRD_COVERAGE_REGISTER.md` updated: HIL area 25% → 100% P0 coverage, FR-HIL-1/2/3/4
  struck through in the P0 gap list with the same UI-wiring caveat FR-OUT-1/2/3 already carries.

## Deliberately deferred (stated, not silently dropped)

- `CorrectionTarget` kinds `classification`/`mapping`/`metric_input` — declared in the schema per
  the plan's own Phase 1 text, refused (not applied) by `apply_corrections` since this plan names
  no acceptance criterion exercising them.
- FR-HIL-5 (corrections as training signal beyond the existing `FeedbackStore` capture) and
  FR-MAP-6 (learn-and-persist into pack policy) — explicitly out of scope per the plan's own text.
- Streamlit UI wiring for the side-by-side source view (Phase 4) and the exception summary surface
  (Phase 5) — backend/logic done and tested; actual rendering not built or visually verified in
  this (headless) session.
- Wave 3c (debt schedule, proposed-debt scenarios) — a genuinely separate concern per the plan's
  own sequencing note, not started.
