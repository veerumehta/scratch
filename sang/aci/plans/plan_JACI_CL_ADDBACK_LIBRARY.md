# Plan: Add-Back Library, Candidate/Approved Layer, and Cross-Period Consistency

Author: Virendra Mehta · 2026-07-29
Repo: jaci (with one japes edit in Phase 1) · Baselines: jaci 0.9.8, japes 2.2.0
Depends on: plan_JAPES_2_2_0_EXPRESSION_DSL.md (landed; supplies the conditionals and caps this plan authors against) and plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md (landed; supplies the canonical keys add-backs bind to).

Driver: FR-ADJ is the worst-covered P0 area in `PRD_COVERAGE_REGISTER.md` at 7%, seven of eight requirements untouched, and simultaneously the cheapest, because the DSL already supports the conditionals and caps it needs. Wave 1b of `plan_JACI_CL_PRD_COMPLETION.md`. The bad-debt inconsistency in the MVP exit criterion is Phase 4 of this plan.

Covers FR-ADJ-2, FR-ADJ-3, FR-ADJ-4, FR-ADJ-5, FR-ADJ-6, FR-ADJ-7, and FR-VAL-7 (which is FR-ADJ-4 surfaced twice; implement once).

> **Status (2026-07-29): DONE, all 5 phases (jaci, unpushed; japes `evidence.py` edit, unpushed;
> no version bump on either repo).** Two real corrections to this plan's own grounding, made and
> documented rather than silently propagated:
> - Phase 1's note that `ProvenanceType` "has `COMPUTED` and `REVIEWER_ENTERED`" implied only two
>   members; it already had five (`SOURCED`/`COMPUTED`/`REVIEWER_ENTERED`/`ASSUMPTION`/
>   `EXPERT_ATTESTED`) before this landed. The prescribed action (add `ADJUSTMENT_CANDIDATE`/
>   `APPROVED_ADJUSTMENT`/`POLICY_ADJUSTED`) was unaffected and applied as written.
> - Phase 4's own text already corrected an earlier revision's "build from scratch" claim before
>   I started — `detect_cross_period_addbacks` existed and was extended, not rebuilt, per the
>   phase's own instruction. Added `detect_cross_period_addback_inconsistency` alongside it rather
>   than modifying its signature, so the existing detector's tests stay unchanged as required.
> - `apply_normalization` gained an `official: bool = False` parameter (default preserves existing
>   behaviour) that refuses (typed `Refusal`, not an exception) rather than sums a candidate
>   add-back into an official/covenant-bound metric.
> - `chart_of_accounts.yaml` gained the add-back source lines Phase 2 needed (bad debt, litigation
>   settlements, gain/loss on sale of assets, owner compensation, relief and one-time income) plus
>   `rent_expense` for Phase 5's house definitions — normal pack-evolution, not scope creep, since
>   these are the canonical keys the new library and metrics bind to.
> - Phase 5's `cit_ebitda`/`ebitdar`/`fixed_charge_coverage_ratio`/bridge metrics verified to
>   reconcile exactly on a hand-built RB-like fixture (`ebitda=160`, `cit_ebitda=120`,
>   `bridge=-40`, `160 + (-40) == 120`) via a committed pytest test, not just an ad-hoc script.
> - Full jaci suite green: 538 passed, 2 skipped (was 537/2 before this wave; one pre-existing
>   test's own demo fixture collided with the new `rent_expense` chart-of-accounts key and was
>   repointed to an unused key, not weakened).

## Grounding notes (verified 2026-07-29 against dev)

- `capabilities/commercial_lending/normalize.py` is the chassis. `NormalizationAdjustment` carries target, `kind` (`add_back` | `reclassification`), key, amount, `provenance_type`, rationale, source coordinate and confidence.
- `addback_keys(profile)` reads `profile.get("addback_keys")` and returns a **flat list of keys**. No caps, no conditions, no per-key metadata. This is the thing the library replaces.
- `build_add_backs` walks allowed keys, matches a reported line per key, and emits one unconditional add-back each. Nothing evaluates a condition and nothing applies a cap.
- `apply_normalization` sums only `add_back` adjustments. `reclassification` adjustments are recorded in the derivation but deliberately net-neutral to the target. So reclassification is currently a no-op on any total; the applier is absent. That is `plan` Wave 1d, not this plan, but do not mistake the recorded-but-inert path for a working one.
- `capabilities/commercial_lending/validation.py` already implements `detect_cross_period_addbacks`, plus `detect_staleness` and `detect_precedence_violations`. `Severity` has two values, `BLOCKING` and `ADVISORY`, with a `_DEFAULT_SEVERITY` map per defect class and `promotion_refusal` as a real state-machine guard.
- `ProvenanceType` has `COMPUTED` and `REVIEWER_ENTERED`. It has no candidate or approved value, so the FR-ADJ-3 distinction cannot currently be represented at all.
- `MetricResult` with method `normalization` is the output shape. Exact `Decimal` throughout, confidence is the weakest input. Preserve both.
- `dsl_catalog.py` holds `ebitda` and the eleven-metric catalog as pack data via `metrics.yaml`. House definitions are authored here, not in Python.

## Phase 1 - Provenance values for the candidate distinction (japes)

Extend `ProvenanceType` with the PRD's missing members, minimally: `ADJUSTMENT_CANDIDATE`, `APPROVED_ADJUSTMENT`, `POLICY_ADJUSTED`. This is a cross-repo edit and it is small, but it gates everything else here, because FR-ADJ-3 is unrepresentable without it.

Add the invariant as code, not convention: a value carrying `ADJUSTMENT_CANDIDATE` may not flow into a metric marked as official or covenant-bound. Enforce at the point of aggregation with a typed `Refusal`, the same posture as the confidence floor.

Do not extend to the full eight-value enum here. The remaining members (`ASSUMPTION`, `OVERRIDE`, `UNSUPPORTED`) belong with Wave 2b, which also builds the assumption value type. Adding enum members with no consumer is the pattern `profiles.py` explicitly warns against.

Acceptance: a candidate adjustment summed into a covenant metric raises, naming the adjustment. Existing `COMPUTED` and `REVIEWER_ENTERED` behaviour is unchanged.

## Phase 2 - The add-back library as pack data

New `config/packs/ci-spread-core/addbacks.yaml`. Each entry declares: key, display label, category (non-cash / non-recurring / owner-discretionary / relief-and-one-time), the canonical chart-of-accounts line it sources from, a condition expressed in the DSL, an optional cap expressed in the DSL, a default disposition (candidate or approved), and a rationale template.

Categories come from FR-ADJ-2. Populate at minimum: D&A, impairment, stock compensation, litigation, gains and losses on asset sales, owner compensation, and the relief and one-time bucket FR-ADJ-7 names.

`addback_keys(profile)` is superseded. The profile stops carrying a flat key list and instead names which library entries are enabled and supplies the numeric ceilings the caps reference, keeping thresholds on the profile where the fail-closed `get()` already guards them. Library structure is pack knowledge; ceilings are institution policy. Do not collapse the two.

Acceptance: the library loads, every entry's condition and cap parse under the DSL's static validation, and every sourced line resolves to exactly one chart-of-accounts key.

## Phase 3 - Conditional and capped evaluation

`build_add_backs` evaluates each enabled entry's condition before emitting, and applies its cap after. The two named cases from FR-ADJ-6 are the acceptance cases: owner compensation capped at a policy ceiling, and bad debt added back only when flagged non-recurring.

A condition that cannot be evaluated, because its input is missing or below the confidence floor, produces neither a silent skip nor an unconditional add-back. Emit the entry as a candidate with the unevaluable condition recorded. An add-back whose basis could not be established is exactly what a reviewer needs to see.

Capping is visible: the derivation records the uncapped amount, the ceiling applied, and the resulting figure. A capped add-back that renders as a bare number is indistinguishable from an uncapped one.

Acceptance: owner compensation exceeding the ceiling emits at the ceiling with both figures in the derivation. Bad debt with no non-recurring flag emits as a candidate, not as an approved add-back and not as nothing.

## Phase 4 - Cross-period consistency (extend, do not build)

**`detect_cross_period_addbacks` already exists in `validation.py`.** It groups line items by statement and key-or-label, collects the periods where the value is non-zero, and emits an advisory `CROSS_PERIOD_ADDBACK` finding when a key is present in some periods and missing in others, with `present` and `missing` lists in `detail`. An earlier revision of this plan said to build this from scratch. Read the existing detector first.

What it does not do, and what this phase adds:

- It keys off non-zero *value presence*, not off whether an add-back was *applied*. A line present but deliberately not added back looks identical to a line that was added back. The exit criterion's bad-debt case is exactly that: the line is present and non-trivial in every period and the add-back was applied in one. Take `adjustments_by_period` from Phase 3 as input so applied-versus-present becomes distinguishable. This is the substance of the phase.
- It takes `addback_keys: list[str]`, the flat list Phase 2 supersedes. Move the keys onto the library entries.
- It does not cover the inverse case FR-ADJ-4 names: a prior period carrying a disclosed charge treated differently from the current period's treatment of the same item.
- Its message names periods but not amounts. A reviewer needs the line amount per period to judge whether an omission was defensible.
- Severity is advisory via `_DEFAULT_SEVERITY`. Whether inconsistent treatment blocks promotion is institution policy and should read from the profile.

Acceptance: a fixture with bad debt present and non-trivial in all three periods but added back in one produces one finding naming all three periods and their amounts, which the current detector cannot do because presence looks uniform. A fixture where the line is genuinely absent in one period produces none. Existing detector tests pass unchanged.

## Phase 5 - House definitions

Author as metric definitions in `metrics.yaml`, no code: the RB CIT EBITDA as gross profit less SG&A less rent, EBITDAR, and the fixed-charge coverage variants. FR-ADJ-5, and it closes part of FR-CUS-8.

FR-ADJ-5 also requires that a house definition is reconcilable to textbook EBITDA. Author the bridge as its own metric so the difference is a computed, traceable figure rather than a footnote.

Acceptance: CIT EBITDA computes on the RB fixture, and the bridge from textbook EBITDA reconciles exactly.

## Out of scope

The reclassification applier (Wave 1d), which is why `apply_normalization`'s inert reclassification path stays inert here. The full eight-value provenance enum and the assumption value type (Wave 2b). Pass-through and entity-level tax handling (FR-ADJ-8, P1). Any UI for reviewing or approving candidates; this plan makes the distinction representable and enforced, not presented.

## Sequencing

Phase 1 first; it is small, cross-repo, and gates Phases 3 and 4. Phase 2 is authoring and can run alongside it. Phase 3 needs Phases 1 and 2. Phase 4 depends only on Phase 2's key structure and is the highest-value item in the plan, so if the wave compresses, do Phases 2 and 4 and defer capping. Phase 5 is pure authoring and independent of everything above it.
