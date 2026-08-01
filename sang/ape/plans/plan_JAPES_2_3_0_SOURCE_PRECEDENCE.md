# Plan: Assurance Attribution and Source Precedence Resolver

> **Status (2026-07-29): DONE, all 4 phases (`japes@320003d`, unpushed, no version bump).** No new
> 2.3.0 minor — this plan's own header flagged the line as unconfirmed ("confirm before
> branching"), and per the project's version policy, not every commit needs one; version bumps are
> clubbed and made deliberately, not per-landing. Version stays 2.2.2 (already pushed) until a real
> release decision; this and future work accumulate under `docs/status/CHANGELOG.md`'s
> `[Unreleased]` section in the meantime.
>
> `SourceStatement` (Phase 1), `SourcePrecedencePolicy` on `PolicyProfile` via a forward-ref +
> `model_rebuild()` to avoid a `profiles.py` <-> `periods.py` import cycle (Phase 2), `resolve_sources`
> (Phase 3), `construct_ltm_from_sources` + FR-SRC-4 findings (Phase 4) — all in
> `jazzx_sdk/finance/periods.py`, following the plan as written.
>
> **One real gap found and fixed, not in the plan's own field list**: the tie-break rule "most
> recent document" is unimplementable with only the fields Phase 1 named. `resolve_sources` only
> considers candidates sharing the exact requested `period.period_id`, so same-period candidates'
> `period.end` is always identical by construction — comparing it can never discriminate a tie.
> Added `SourceStatement.received_at` (when the document itself was received/filed, distinct from
> the period it describes) and tie-break on that instead; a tie with no `received_at` on either
> side correctly falls through to a Refusal rather than picking arbitrarily. Caught by writing the
> tie-break test, not by re-reading the plan.
>
> 19 new tests (`tests/test_finance_source_precedence.py`), reusing `test_finance_periods.py`'s
> `rb_appendix_d` fixture so the resolver-driven path is checked against the exact same verified
> PRD number (74,698) as the explicit-component `construct_ltm` path. Full suite 1923 passed (was
> 1904), all 20 pre-existing period tests unchanged. `docs/status/CHANGELOG.md` updated.

Author: Virendra Mehta · 2026-07-29
Repo: japes · Baseline: 2.2.0 (dev) · Proposed line: 2.3.0 (a 2.3.0 plan already exists for the guidance-injection hook; confirm the line before branching)
Depends on: plan_JAPES_2_2_0_PERIOD_MODEL.md (landed; supplies `Assurance`, `ASSURANCE_RANK`, `Period`, `PeriodSet`, `construct_ltm`).

Driver: `PRD_COVERAGE_REGISTER.md` puts FR-SRC at 25% P0, the second-worst area, and Wave 1a of `plan_JACI_CL_PRD_COMPLETION.md` puts it first because the MVP exit criterion is a mixed-assurance LTM column. This is also a gap I created: the period model plan scoped the resolver out explicitly, delivered the enum and the ranking, and nothing picked up the rest.

Covers FR-SRC-1, FR-SRC-2, FR-SRC-3. FR-SRC-5 (the RB worked profile) is the acceptance case.

## Grounding notes (verified 2026-07-29 against dev)

- `jazzx_sdk/finance/periods.py` has `Assurance` (audited / reviewed / compiled / tax / company_prepared / internal_interim / management_schedule / derived) and `ASSURANCE_RANK`. `Period.assurance` exists. `construct_ltm` returns mixed assurance as a **set** of component levels, not a collapsed best-of.
- `construct_ltm` takes its component periods as explicit arguments. Component selection is entirely caller-supplied today; nothing chooses sources by policy.
- `jazzx_sdk/fabric/canonical/profiles.py` `PolicyProfile` is a frozen pydantic model with `confidence_floors`, `thresholds` and `custom` dicts plus a fail-closed `get()`. Its docstring states the modeling rule: only fields the resolver and Governor consume today are typed, everything else rides the `custom` escape hatch until a consumer reads it typed. A precedence policy *is* consumed by the resolver this plan adds, so typing it is correct under that rule rather than an exception to it.
- `PolicyProfile.get` raises naming the profile when a key is absent. Precedence resolution must preserve that posture: no SDK-side default ranking.
- Nothing anywhere attributes assurance to a source document. `Assurance` is currently only ever set by a caller onto a `Period`.

## Phase 1 - Assurance attribution

New `SourceStatement` in `jazzx_sdk/finance/periods.py` or a sibling module: a statement-and-period-scoped record carrying the document ref, statement type, period, `Assurance`, statement basis (GAAP / tax / cash), reporting currency and scale, and the preparer where stated.

This is the object FR-ING-6 and FR-SRC-1 both need, and it is the missing join. Assurance is not a property of a period, it is a property of *a document's account of a period*. Two documents can describe the same period at different assurance levels, which is exactly the RB case, and the current model cannot represent that.

Detection is out of scope here. This phase provides the typed record; classification populates it.

Acceptance: two `SourceStatement` records for the same period at different assurance levels coexist without conflict, and a `Period` can be constructed from either.

## Phase 2 - Precedence policy on the profile

Add a typed `source_precedence` field to `PolicyProfile`: an ordered ranking over `Assurance` values, plus optional per-statement-type overrides and a tie-break rule (most recent document, or explicit refusal on a tie).

No SDK default. Absent a declared ranking the resolver raises the same way `get()` does, naming the profile. `ASSURANCE_RANK` stays as a *reference* ordering the SDK ships for authoring convenience; it must not be silently substituted when a profile declares nothing, because a bank's precedence is policy and guessing it is exactly the failure this whole layer exists to prevent.

Acceptance: a profile with no `source_precedence` causes the resolver to raise naming the profile. `ASSURANCE_RANK` is never consulted as a fallback, asserted by a test.

## Phase 3 - The resolver

`resolve_sources(statements, *, policy, period, statement_type) -> SourceResolution`.

`SourceResolution` carries the winning `SourceStatement`, the ranking applied, every candidate considered with its rank, and the reason the winner won. The losers are part of the output, not discarded, because FR-AUD-1 lineage has to answer why a figure came from the compilation rather than the audit.

Ties resolve per the policy's tie-break rule. An unresolvable tie is a typed `Refusal`, not an arbitrary pick.

Acceptance: on the RB profile (2018 and 2019 reviewed, 2020 and 2021 audited, 9-month 2022 compiled, 9-month 2023 company-prepared), the resolver selects the audited full year as the anchor and the company-prepared stub as the current interim, and reports both the selection and the rejected candidates.

## Phase 4 - Policy-driven period construction

`construct_ltm` gains an optional path where components are chosen by the resolver rather than passed in. The existing explicit-argument signature stays and stays supported; this adds a policy-driven entry point beside it, it does not replace the caller-supplied one.

The mixed-assurance set `construct_ltm` already returns becomes derivable from the resolutions rather than assembled by the caller. FR-SRC-3.

Also surface the FR-SRC-4 conditions as findings rather than implementing the flagging UI: a lower-assurance interim feeding the most decision-relevant column, and a spread relying on older periods than the newest available data. Emit them; let the consumer decide severity. FR-SRC-4 is P1 and only the detection belongs here.

Acceptance: the RB LTM Sep-2023 column constructs from resolver-chosen components, carries the three-level mixed assurance set, and emits a finding that the current stub is company-prepared. The existing explicit-component tests pass unchanged.

## Out of scope

Detecting assurance from document text; this plan types the record, classification populates it. The special-instructions file as an override source (FR-ING-3), which is a separate ingestion concern that will write into this policy. Staleness UI. Any JACI adoption.

## Sequencing

Phases 1 and 2 are independent and additive. Phase 3 needs both. Phase 4 is the one that touches landed code, so it lands last and carries the regression that the explicit-component path is untouched. Nothing here changes an existing signature.
