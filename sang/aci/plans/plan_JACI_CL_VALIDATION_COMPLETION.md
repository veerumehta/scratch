# Plan: Validation Completion

Author: Virendra Mehta · 2026-07-29
Repo: jaci · Baseline: 0.9.8 (dev)
Depends on: nothing unlanded. Absorbs Wave 1c of `plan_JACI_CL_PRD_COMPLETION.md` and pulls Wave 2a's severity model forward, because the four missing arithmetic controls and the severity model are one coherent unit of work rather than two.

Driver: an audit of `capabilities/commercial_lending/validation.py` on 2026-07-29 resolved the six `audit` entries in `PRD_COVERAGE_REGISTER.md` and found the area weaker than assumed. FR-VAL P0 coverage is 28%, not the 39% provisionally recorded. Four of the PRD's arithmetic controls are absent entirely, and one of them, FR-VAL-8, is named in the MVP exit criterion.

Covers FR-VAL-1, FR-VAL-3, FR-VAL-4, FR-VAL-5, FR-VAL-8, FR-VAL-10, and extends FR-VAL-2.

> **Status (2026-07-29): DONE, all 4 phases (jaci, unpushed; no version bump).** One real scope
> decision surfaced and was resolved with the user rather than guessed, since it affected
> correctness: FR-VAL-5 "period continuity" is under-specified for a balance sheet, which has no
> separate opening/closing columns the way cash (FR-VAL-3) and equity (FR-VAL-4) do. Verified
> against a real YETI 10-K that the chart of accounts' own `change_in_*` cash-flow keys are exactly
> the intended reconciliation surface (direction ties exactly; magnitude only approximately, due to
> non-cash items — confirmed empirically, not assumed), and built `detect_period_continuity`
> against that reading, per the user's explicit choice.
> - **Phase 1** (`detect_balance_control`/`detect_cash_flow_tie`/`detect_equity_rollforward`/
>   `detect_period_continuity`): four new `DefectClass` members, gated behind `validate_package`'s
>   new `control_tolerance` param (`None` by default — off, matching "tolerance is institution
>   policy, never a module default"). Equity roll-forward distinguishes "mismatch" from
>   "unverifiable" (no contributions/distributions separately reported) as the plan requires, with
>   `capital_contributions`/`distributions_to_owners` added to the chart of accounts to make that
>   distinction checkable at all.
> - **Phase 2** (`detect_income_statement_cross_foot`): reads `parent`/`is_subtotal` off a
>   `LineVocabulary` (default `CHART_OF_ACCOUNTS`) in declaration order — no hardcoded arithmetic
>   chain. Added `parent` to `cost_of_goods_sold`/`selling_general_and_administrative_expenses` in
>   the chart of accounts. Deliberately does not extend the chain past `operating_income`:
>   `interest_expense_income_net`/`other_income_expense_net`/`income_tax_expense` use a signed-
>   addition convention in real filings (verified against the same YETI 10-K), not this chain's
>   unsigned subtraction — extending it there would misfire on every real filing, so those lines
>   are left without a declared `parent` rather than guessed. Reuses `DefectClass.HARDCODED_PLUG`
>   (same defect, different scoping mechanism), not a new class.
> - **Phase 3** (`DisclosedObligation`/`detect_undisclosed_obligations`): the stubbed typed input
>   the plan calls for; recomputes funded debt and leverage via the existing
>   `compute_metric_results`, not a hand-rolled DSL call, so the reported/recomputed leverage pair
>   in the acceptance criterion is real, not a placeholder.
> - **Phase 4** (`Severity`): expanded to the PRD's six plus `BLOCKING`/`ADVISORY` kept as their
>   own distinct values (not a true Python enum alias) — a true alias would break
>   `Severity("blocking")`, which an existing test (and potentially a real profile) already relies
>   on. `Severity.blocks_promotion` covers both old and new blocking values; `blocking_findings`
>   updated to use it. New `aggregate_status` (`pass`/`pass_with_flags`/`blocked`);
>   `promotion_refusal` now consumes it. Existing `_DEFAULT_SEVERITY` entries for the original nine
>   defect classes are untouched (still `BLOCKING`/`ADVISORY`) — no behaviour change, zero existing
>   test breakage; the five new defect classes use the new canonical values directly.
> - No C&I gold-case suite exists yet to assert severities against (per the acceptance text); that
>   lands with Wave 1e's reference-case harness. 42 tests in `test_validation.py` (was 26, 16 new)
>   cover every phase's stated acceptance directly; full jaci suite 554 passed, 2 skipped, no
>   regressions (5 pre-existing unrelated failures confirmed via `git stash` to predate this work).

## Grounding notes (verified 2026-07-29 by reading validation.py)

What exists. `DefectClass` carries the six corpus classes plus `RECONCILIATION_MISMATCH`, `STALENESS` and `PRECEDENCE`. Detectors: `detect_content_free_stubs`, `detect_scale_errors`, `detect_sign_label_errors`, `detect_hardcoded_plugs`, `detect_cross_period_addbacks`, `detect_cross_document_contradictions`, `detect_reconciliation_mismatches`, `detect_staleness`, `detect_precedence_violations`. `ValidationFinding` carries defect class, severity, message, statement type, line key, period, source refs and a detail dict. `admit_line_items` is the XF-2 confidence gate emitting typed `Refusal`s at cell `cl.eadm.003`. `promotion_refusal` is a real state-machine guard at `cl.am.004`, not a UI check. `validate_package` composes the single-package detectors.

What is absent, and this is the substance of the plan:

- **FR-VAL-1 balance control.** No check that total assets equals total liabilities plus equity. `detect_hardcoded_plugs` compares a section's single subtotal against its components; it never compares across the two sides of the balance sheet.
- **FR-VAL-3 cash-flow tie.** No check that ending cash on the cash-flow statement equals balance-sheet cash.
- **FR-VAL-4 equity roll-forward.** Absent.
- **FR-VAL-5 period continuity.** Absent. Nothing compares prior-year closing balances to current-year opening balances.
- **FR-VAL-8 disclosure check.** Absent. Nothing detects a disclosed obligation missing from the balance sheet.
- **FR-VAL-2 cross-foot** is partial. `detect_hardcoded_plugs` is scoped to the balance sheet and fires only when a section has exactly one subtotal and at least two components. Its own docstring records that income-statement subtotals are sequential rather than additive and left as a follow-up. This plan is that follow-up.
- **FR-VAL-10 severity.** `Severity` has two members against the PRD's six, and `_DEFAULT_SEVERITY` is a module constant rather than profile-resolved. There is no aggregate spread status.

## Phase 1 - The four arithmetic controls

Each is a detector in the existing shape, returning `ValidationFinding`, added to `validate_package`. Tolerance is institution policy read from the `PolicyProfile`, never a module default, matching the posture `admit_line_items` already takes with its confidence floor.

- `detect_balance_control`: assets against liabilities plus equity, per period. The PRD notes the RB spread itself carries a balance-control discrepancy, so this must report the amount and not merely a boolean.
- `detect_cash_flow_tie`: ending cash on the cash-flow statement against balance-sheet cash, per period.
- `detect_equity_rollforward`: opening equity plus net income plus contributions less distributions against closing equity. Where contributions or distributions are not separately reported, emit a finding that the roll-forward is unverifiable rather than assuming zero. An unverifiable control and a passing control are different results.
- `detect_period_continuity`: prior-period closing balances against current-period opening balances, across the balance sheet.

New `DefectClass` members for each. Do not overload `HARDCODED_PLUG`, which means something specific and is already blocking by default.

Acceptance: each detector fires on a fixture with a planted break and is silent on the YETI package. The equity roll-forward reports unverifiable rather than passing when contributions are not separately stated.

## Phase 2 - Cross-foot on the income statement

Extend cross-footing to sequential subtotals: revenue less COGS equals gross profit, gross profit less operating expenses equals operating income, and so on down. This is the follow-up `detect_hardcoded_plugs` names in its own docstring.

The chain is now declarable rather than hardcoded, because `chart_of_accounts.yaml` carries `is_subtotal` and a parent per line. Derive the sequence from the vocabulary; do not write the arithmetic chain in Python.

Acceptance: a fixture where gross profit does not equal revenue less COGS produces a finding. The chain is read from the chart of accounts, proven by a test that adds a subtotal to a fixture vocabulary and sees it checked.

## Phase 3 - Disclosure check

FR-VAL-8, and it is in the exit criterion. Detect an obligation disclosed in the notes but absent from the balance sheet, the RB case being roughly $573K of unrecorded tax, so it is not omitted from leverage.

This has a hard prerequisite the other phases do not: footnote extraction. FR-EXT-4 is unbuilt, so nothing currently surfaces note content as structured data. Two options, and the plan chooses the second.

Building general footnote binding here would swallow the phase. Instead take disclosed obligations as a typed input, `DisclosedObligation` with description, amount, period, source coordinate and a recorded-on-balance-sheet flag, and have the detector compare that input against the spread. Populate it from the fixture for now, and from FR-EXT-4 extraction when Wave 4c lands. The detector is correct and testable either way, and the interface is what FR-EXT-4 will fill.

Say this in the plan rather than letting a later reader think the detector reads notes. It does not.

Acceptance: a fixture carrying a disclosed obligation absent from the balance sheet produces a finding naming the amount and the source coordinate, and the recomputed leverage including that obligation is reported alongside the reported figure.

## Phase 4 - Severity model and delivery gate

Replace the two-member `Severity` with the PRD's six: Critical blocks finalize, High requires analyst review, Medium requires review before approval, Low is informational, plus the Policy and Data classes FR-VAL-10 names.

`_DEFAULT_SEVERITY` becomes a profile-resolved mapping. Which defect class is serious enough to block is institution policy, and the module already acknowledges this in a comment while hardcoding it anyway.

Add an aggregate spread status derived from open findings: pass, pass with flags, blocked. `promotion_refusal` consumes the status rather than scanning for blocking findings itself, so the gate has one input.

Migration: keep `BLOCKING` and `ADVISORY` as aliases onto Critical and Low for one release. `promotion_refusal` and its state-machine guard must not change behaviour in this phase.

Acceptance: every existing finding maps to a severity with no behaviour change to `promotion_refusal`, asserted across the C&I gold cases. A profile that raises cross-period add-back inconsistency to Critical blocks promotion where the default does not.

## Out of scope

General footnote extraction (FR-EXT-4, Wave 4c); Phase 3 defines the interface it will fill. Reasonableness and anomaly detection (FR-VAL-9, P1). The review surface that consumes severities (Wave 3b). Any change to `admit_line_items` or the XF-2 gate.

## Sequencing

Phase 1 is four independent detectors and can be split across sessions. Phase 2 depends on the chart of accounts, which landed. Phase 3 is the exit-criterion item, so it should not be deferred despite being the one with a stubbed input. Phase 4 touches a live promotion gate, so it lands last and carries the no-behaviour-change regression.
