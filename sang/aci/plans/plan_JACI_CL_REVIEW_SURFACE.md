# Plan: Review Surface and Override Lineage

Author: Virendra Mehta · 2026-07-29
Repo: jaci · Baseline: 0.9.8 (dev)
Depends on: Wave 1 (landed) for the severity model, source coordinates and `SourceResolution`. Coordinates with `plan_JAPES_2_3_0_GOVERNED_WORKBOOK.md` Phase 4 on the exception summary.

Driver: Wave 3b of `plan_JACI_CL_PRD_COMPLETION.md`. FR-HIL is at 25% P0. The approval chassis exists and is better than I expected, but it has a gap that matters more than the missing UI: **corrections are captured and never applied.**

Covers FR-HIL-1, FR-HIL-2, FR-HIL-3, and completes FR-HIL-4.

## Grounding notes (verified 2026-07-29 by reading hitl_approval.py)

What exists, and it is a real suspend-and-resume loop rather than a stub. `spread_approval_engine` builds a three-step `ConductorEngine` pipeline (flag, approve, apply). `_approve` raises `SuspendRun` with an `ApprovalRequest` payload when there are flagged lines and auto-approves when there are none. The driver resumes with an `SmeDecision`, which the engine injects as that step's output. `_apply` affirms and promotes through `affirm_spread` and `promote_spread`, both authority-gated and blocking-gated. `_record_learning` writes a `Feedback` into a `FeedbackStore` so the judgment feeds `synthesize_cases_from_feedback` and `optimize_prompt`.

The gaps, in order of how much they matter:

- **`decision.corrections` is never applied.** It is a bare `dict[str, Any]` of line key to corrected value, and `_apply` passes it only into `_record_learning`'s feedback metadata. The spread is promoted unchanged. Approval currently means "the flagged findings are rectified by fiat," via `remaining = [f for f in ctx.findings if f not in flagged]`, not "the corrections are applied and the findings re-evaluated." FR-HIL-3's re-propagation is absent, and so is the correction itself. This is the same shape as the inert reclassification path in `normalize.py`: a field that exists, is populated, and does nothing.
- **Override lineage is decision-level, not correction-level.** `SmeDecision` carries one `sme_id` and one `reason` for the whole decision. FR-HIL-3 requires author, timestamp, superseded value, category and rationale **per correction**. A dict value cannot carry any of them.
- **No risk ranking.** `_flag` returns `blocking_findings(...)`, a flat list in detection order. FR-HIL-1's whole point is that reviewers should not spend time on clean data.
- **No side-by-side source view.** Coordinates exist on every line item as of Wave 1; nothing renders them.
- **Maker-checker is one role, not three.** `affirm_spread` and `promote_spread` are two transitions but both take the same `decision.sme_id`. FR-HIL-4 wants analyst, then reviewer, then approver.

## Phase 1 - Correction as a governed object

Replace `SmeDecision.corrections: dict[str, Any]` with a list of `Correction` objects carrying: target (line key and period, or mapping, or classification, or metric input), the new value, the superseded value read from the package rather than supplied by the caller, author, timestamp, category, and a required rationale.

Superseded value is read, not passed. A caller-supplied "previous value" is unverifiable and the package already knows what the value was.

Rationale is required, matching `reviewer_add_back` in `normalize.py`, which already refuses an empty rationale. Be consistent with the precedent rather than inventing a second posture.

Category comes from a declared set so corrections are countable by type, which is what FR-HIL-5 will later need as training signal.

Keep the dict form accepted for one release, coerced into a `Correction` with author from `sme_id` and a rationale from `reason`, so the existing driver does not break.

Acceptance: a correction without a rationale is refused. The superseded value on a `Correction` matches the package's value for that cell, asserted rather than trusted. Existing dict-form callers still work.

## Phase 2 - Apply and re-propagate

The phase that closes the actual gap. `_apply` applies the corrections to the package, re-runs validation against the corrected package, and promotes against the resulting findings.

Design intent, stated because the current behaviour is the opposite: approval does not dismiss findings. It applies corrections and then asks the validators again. A finding that survives a correction is still open, and a finding the correction fixed disappears because the arithmetic changed, not because someone signed a form.

Corrections produce a new layer, not a mutation. As-reported stays immutable, exactly as add-backs and reclassifications do. A corrected value carries `OVERRIDE` provenance, which means extending `ProvenanceType` with the member Wave 1b deliberately left out.

Re-propagation is transitive: a corrected line changes the metrics that bind it, which changes the covenant tests that read those metrics. The binding closure from `plan_JACI_CL_PRD_DEMO_ARC.md` Phase 6 is the same graph walk and should be shared, not written twice.

Where a correction cannot be applied, because the target does not exist or the value fails admission, refuse the correction and keep the run suspended. Do not promote a spread with a silently dropped correction.

Acceptance: correcting a line that feeds `leverage_x` changes the covenant test result, and the correction appears in the derivation of every downstream figure. Findings are recomputed rather than filtered. A correction targeting a nonexistent key refuses rather than being ignored.

## Phase 3 - Risk-ranked review queue

`rank_for_review(findings, package)` ordering by expected reviewer value rather than detection order. Inputs available today: finding severity from the Wave 1c model, the confidence of the affected cell, the magnitude of the affected line relative to the statement, and whether the cell feeds a covenant test through the binding closure.

That last input is the one that matters and the one only we can compute. A low-confidence cell nobody's covenant depends on is worth less review time than a high-confidence cell one basis point from a covenant breach.

Ranking weights are profile config, not constants. Which risks an institution cares about is policy.

Acceptance: on a package with a mix of findings, a covenant-feeding item outranks a same-severity item that feeds nothing, and the ordering changes when the profile's weights change.

## Phase 4 - Side-by-side source view

The Streamlit surface. Clicking a spread value shows the source document region from its `SourceCoordinate`, and the reverse lookup lists every spread cell a given source region feeds.

Reverse lookup is the half that is usually skipped and is explicitly in FR-HIL-2. It is also cheap now, because coordinates are stored per cell and inverting the index is a dictionary.

Render the region rather than the whole page where the coordinate carries a bounding box; page-level display when it does not, with the imprecision visible rather than implied.

Acceptance: every populated cell on the YETI and RB packages resolves to a viewable source region or reports why it cannot. Reverse lookup from a source region returns the correct cell set.

## Phase 5 - Maker-checker roles

Extend the loop from one SME to the three FR-HIL-4 names: analyst prepares, reviewer reviews, approver approves. Each transition carries its own actor and is authority-gated through the matrix, which `affirm_spread` and `promote_spread` already consult.

Exceptions surface to the approver, and the per-spread exception summary for the credit file is the same artifact as the governed workbook's Exceptions sheet. Build it once in a shared shape and let both consume it.

Same actor in two roles is a policy question, not a code question. Read whether self-review is permitted from the profile; do not hardcode either answer.

Acceptance: a spread requires two distinct actors when the profile forbids self-review and one when it permits it. The exception summary is identical in content to the workbook's Exceptions sheet.

## Out of scope

Corrections as training signal beyond the existing `FeedbackStore` capture (FR-HIL-5, P1), and specifically the FR-MAP-6 learn-and-persist path, which must not let a deal-level override change institution policy. That constraint is worth respecting now even though the feature is later: nothing in this plan writes to a pack asset.

## Sequencing

Phase 1 first; it is a schema change everything else reads. Phase 2 is the plan's reason for existing and should not be deferred behind UI work, because the current behaviour promotes spreads with unapplied corrections. Phases 3 and 4 are independent of each other and both depend on Phases 1 and 2. Phase 5 touches live authority-gated transitions, so it lands last.
