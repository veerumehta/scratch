# DSCR eligibility grid — encoding notes

Companion to `profiles/dscr_profile.yaml`, `policies/process.yaml`, `policies/standard.yaml`,
`policies/platinum_select.yaml`, `tests/scenarios/dscr/test_dscr_eligibility.py`.
Source of truth for the Standard corpus: **Acra DSCR Standard Consolidated Guidelines v1.0**
(DSCR Program Summary 8.17.2026 with the Seller's Guide DSCR excerpt of 2026-08-28); rule
descriptions cite its STD-x numbers. Platinum Select's is its own consolidation (PLAT-x). Source of truth for the condo/entity/fraud gates (§1a): **Commercial DSCR Loan
Process Flow, July 2026** — an operational runbook with no CLTV/DSCR content of its own,
covering broker-submission validation, underwriting, account management, and closing.

**Status, 2026-08-14:** landed at these paths (D3 rev 2 Phases 0-2.3 all shipped, jaci `68cfcae`/
v0.19.9). Every field the corpus reads resolves on `LoanApplication` (Phase 1), cap composition
is real (`compose_caps`, G3 resolved), the conductor runs the deterministic assessment before
the model loop and Governor enforces it (Phase 2.3), and the profile-literal drift lint (A5, G4
resolved) keeps 9 policy/`custom` twins honest. `pack_manifest.yaml` is wired: it declares
`policies: {dir: policies}` and `profiles: {dir: profiles}`, so `Pack.policy_registry()` and
`policy_profile()` resolve the corpus declaratively (`registry:` with a Python `PolicyRegistry`
per `jazzx_sdk.pack.pack._resolve`'s `module.path:attr` contract is the other, unused route).
Direct `load_policies()`/`PolicyProfile.from_yaml()` calls remain in the tests, which read the
files by path. Remaining: Phase 3 (UI, gold cases), G2 (LTV calculator). G1 (`AllOf`/`AnyOf`) is
resolved japes-side as of 2026-08-14 — see §3 — and now has a real consumer: `DSCR-NMLS-VERIFIED`
(§1a), the first rule in this corpus to use `kind: all_of`.

**Same day, later: 8 condo/entity/fraud gates added (§1a)**, sourced from the Process Flow doc
rather than the Program Summary — policy `version` bumped `1.1.0` → `1.2.0`, and the state
prepayment rules described below took it to the `1.3.0` the file now ships. These are the first
rules in this corpus with no CLTV/DSCR content at all; three fields have no numeric standard to
encode against (`hoa_reserves_adequate`, `entity_documents_complete` — qualitative
review-determination fields, not computed thresholds; see §1a for why).

**2026-08-17: scenario renamed Acra DSCR → DSCR** (directory, pack, module/class names, rule-ID
prefix — see the top-level jaci commit for the full list); Acra Lending remains only as a
`source_refs`/`institution_ref` citation, not the scenario's identity. Same day: conductor's
model defaults bumped `gpt-4o` → `flex_gpt-5.4` (matching `cre_underwriting`/`ci_spread`/`aml`),
and its identity-mapping `model_tier_parser` swapped for the real `jaci.settings.parse_model_tier`
(needed to parse the new `flex_` prefix at all — the old one was never exercised against a
prefixed model name). And the 13-state PPP buyout rules (§1b) landed, closing the last "Not
authored" item G1 was blocking. Remaining: Phase 3 (UI, gold cases), G2 (LTV calculator).

## 0. What changed since the build plan was written

The plan proposed `MatrixCondition` as a platform ask. **It's built and committed** (japes `272f1e3`:
`fabric/canonical/{policy,profiles,condition_evaluator,__init__}.py`, 13 matrix tests in
`tests/test_condition_evaluator.py`, 3 in `tests/test_default_policy_expert.py`). The set-membership
operator gap is closed in the same commit — `_MEMBERSHIP_OPS`, fixing a live bug where
`Expression(operator=IN, …)` silently fell through to "always VIOLATED".

So the ask was not "build it," it was "review and land it" — these artifacts were the first real
consumer, exercised it end to end, and surfaced the two defects in §2 (now also fixed, `44f9b55`).

## 1. What is authored here

| Artifact | Contents |
|---|---|
| `profiles/dscr_profile.yaml` | Standard: 19 tables (the grid, sub-1.0, STR, property-type and ITIN tables of **99 + 3 + 3 + 12 + 33 cells**, and 14 overlay tables from the 8.17 consolidation), 12 ratio thresholds, 25 custom scalars. Platinum Select (`plat_*`): 4 tables (**12 + 3 + 3 + 3 cells**), 2 ratio thresholds, 10 custom scalars. One of the 49 threshold and custom keys, `dscr_min_no_ratio_floor`, is referenced by no rule (see §3 G4). |
| `policies/process.yaml` + `policies/standard.yaml` | **77 rules**: the 8 condo/entity/fraud gates (§1a, all of `process.yaml`: `DSCR_PROCESS`, core to every program), and `DSCR_STANDARD`'s 69: 54 program rules citing STD-x and 15 state PPP-buyout rules (§1b). By `condition` kind: 39 `expression`, 20 `matrix`, 10 `ratio`, 7 `all_of`, 1 `any_of`; 28 rules use `all_of`/`any_of` somewhere. (Counts re-derived from the files.) |
| `policies/platinum_select.yaml` | **44 rules** (`DSCR_PLATINUM_SELECT`, program `platinum_select`) from the Platinum Select consolidated guidelines v1.0: 29 program rules citing PLAT-x.y, plus the 15 state PPP-buyout rules copied from `standard.yaml`. Thresholds are the profile's `plat_*` keys. Its header lists the provisions not yet encoded. |
| `tests/scenarios/dscr/test_dscr_eligibility.py` | 69 behavioural cases + a grid-completeness test |

`max_cltv_grid` holds **99 cells** = 3 loan-amount bands × 11 FICO bands × 3 purposes, of which **70 are eligible values and 29 are authored `"NA"`**. The published grid shows 78 cells; the extra 21 exist because the FICO axis is normalized across all three bands (the PDF prints a ragged grid — 10, 10, and 6 tiers — plus prose rows "<620" and "<700"). Normalizing is deliberate: `MatrixEvaluator` returns **INDETERMINATE when no band matches**, and INDETERMINATE reads as "we couldn't tell" rather than "ineligible." Every reachable combination must resolve to a *present* cell, with ineligibility expressed as an authored `"NA"` (which `_NA_SENTINELS` turns into VIOLATED). **An absent cell raises `KeyError` at runtime** — hence `test_grid_is_fully_authored`.

**Coverage is a reference slice, not the whole program.** Authored: the primary CLTV grid, loan-amount floor/ceiling, ineligible states, the >80% LTV gates (DSCR 1.20, 6-month reserves, property-type restriction), sub-1.0 and No-Ratio caps, the >$2M DSCR floor, FICO<620 reserves, short-term rental, property-type overlays, ITIN, escrow-waiver citizenship, IO minimums, the condo/entity/fraud gates (§1a), and the 13-state prepayment-penalty buyout rules (§1b). **Not authored:** credit-event/housing-history overlays, tradeline and thin-file rules, declining-market and rural modifiers, FTHB, ARM margin-by-FICO, vacant-property rules, seller concessions and gifting.

### 1b. State prepayment-penalty (PPP) buyout rules

14 rules (`DSCR-PPP-*`), all citing `dscr_program_summary_6_15_2026_v1_1`'s "Prepayment Penalty
Requirements" table — 13 states, Illinois split into its two independent triggers. New
`LoanApplication` fields: `prepayment_penalty_requested` (the selected PPP structure, default
`"unspecified"` -- the structure is a term of the loan, so an application that does not state it
has not been checked against these rules and is denied by them, while `"no_prepay"` is the stated
value that clears them), `residential_unit_count`
(no default: derived as `1` for a single-unit `property_type`, and *required* for
`two_to_four_unit`, because the Mississippi, Ohio and Pennsylvania gates read it and a field
that is absent makes those gates INDETERMINATE, which skips the rule silently),
`interest_rate` (no default either, and required for the Illinois >$250k individual case for
the same reason).

**That requirement lives in the consumer's schema, not in this pack.** `LoanApplication` is
authoring-repo code; the pack ships only the rules. So any *other* consumer that hand-builds a
policy context -- including the copy vendored into plato's seed packs, where no
`LoanApplication` exists at all -- gets the silent skip these fields were made required to
prevent: `DSCR-PPP-MS`, `-OH`, `-PA` and `-IL-2` report NOT_APPLICABLE rather than denying when
the field is absent. The IR cannot express "gate on this field being present", so the pack
cannot close it; a consumer must supply `residential_unit_count` and, for Illinois,
`interest_rate`, or accept that four of the fourteen PPP rules do not run.

**"Residential 1-4" needed no unit-count check.** Every `PropertyType` this corpus already has
(sfr / warrantable_condo / townhome / pud / non_warrantable_condo / condotel / manufactured /
two_to_four_unit -- there is no bare `condo`, which this list said for a while while every rule
correctly matched the two qualified spellings) tops out at 4 units, so a bare
`property_state` match already covers Kansas/Maryland/Michigan/Minnesota/New Mexico. Only the
narrower carve-outs — Ohio/Pennsylvania's "Residential 1-2" and Mississippi's "single unit" —
needed `residential_unit_count`, since `two_to_four_unit` alone can't tell 2 from 3-4.

**G1 (`AllOf`/`AnyOf`) gets its first real consumer in this corpus here** — 9 of the 14 rules
(Illinois ×2, Mississippi, New Jersey, Ohio, Pennsylvania, Rhode Island, Virginia, Vermont — the
multi-predicate ones; the plain five are Kansas, Maryland, Michigan, Minnesota, New Mexico)
combine `property_state` with entity type, loan amount, unit count, rate, or
purpose via `kind: all_of`. This is exactly the "Illinois PPP buyout" example G1's own gap
description used — no longer hypothetical.

**Mississippi's reading is an interpretive call, flagged as such.** The source table's "5 Yr
(step), 3 Year (3x3), 2 Yr (2x3), or 1 Yr (1x3)" is read as naming four already-catalogued
structures by shorthand (step/percent-years), not introducing new ones — restricting Mississippi
single-unit loans to that subset (plus `no_prepay`) rather than the full national menu. Worth
re-confirming against Acra directly if a real Mississippi DSCR loan ever needs this rule.

**No profile-literal tracking for these thresholds — but the reason has expired.**
`find_profile_literal_drift` now walks `all_of`/`any_of` children (japes `_declaring_expressions`),
so a `profile_custom_key` on a nested Expression *is* checked; `DSCR-IO-MIN-LOAN` depends on that.
These four (Illinois's `$250,000`, `8%`; Pennsylvania's `$319,777`; Vermont's `$1,000,000`) were
left as plain literals because nesting them was decorative at the time, which is no longer true —
linking them is now possible and worth doing when these rules are next touched. Matching how
single-use thresholds elsewhere in this corpus (e.g.
`DSCR-ITIN-LOAN-MAX`'s `$1,000,000`) already do -- which that rule did *not* until it was linked
to `itin_loan_amount_max`; this sentence cited it as an example while it was a bare literal.

33 new test cases (`tests/scenarios/dscr/test_dscr_eligibility.py`) — one VIOLATED + one
SATISFIED per rule, plus NOT_APPLICABLE spot-checks on every multi-predicate rule proving a
partial match doesn't fire. Four cases in two later tests build the context through
`LoanApplication`, so the *default* is what the rule sees.

That last pair is the gap the first cut left. Every case in the table sets
`prepayment_penalty_requested` itself, so none of them reached the default, which was
`"no_prepay"`, the one value satisfying every buyout rule, and so reported a clean result in all
13 states for a loan whose prepay terms nobody had asked about. The default is `"unspecified"`
now and those rules deny until the structure is stated.

### 1a. Condo/entity/fraud gates (process-runbook sourced, not the rate/CLTV grid)

Eight rules, all citing `dscr_commercial_process_flow_jul_2026` (not the Program Summary —
this document has no CLTV/DSCR content). `LoanApplication` gained ten new fields; each field's
default is chosen individually, not uniformly (see the schema docstring for the reasoning):

| Rule | Gate | Field(s) | Default |
|---|---|---|---|
| `DSCR-DUPLICATE-SSN-CLEARED` | Stage 1 duplicate-SSN check ran and cleared | `duplicate_ssn_cleared` | `False` (fail-closed — an affirmative check a human must perform) |
| `DSCR-NMLS-VERIFIED` | Broker + Loan Officer NMLS credentials verified | `broker_nmls_verified`, `loan_officer_nmls_verified` (via `kind: all_of` — G1's first real consumer) | `False` each (fail-closed) |
| `DSCR-REFI-LISTING-CHECK` | Refinance only: property not currently listed for sale | `property_currently_listed_for_sale` | `False` (clean) |
| `DSCR-CONDO-HOA-RESERVES` | Condo/condotel: HOA budget/reserves adequate | `hoa_reserves_adequate` | `True` (clean — no numeric standard exists to fail closed against; see below) |
| `DSCR-CONDO-HOA-LITIGATION` | Condo/condotel: no active/pending HOA litigation | `hoa_litigation_pending` | `False` (clean) |
| `DSCR-ENTITY-BORROWER-1` | Entity borrower: entity is Borrower 1 on all docs | `entity_is_borrower_1` (applicability: `borrower_entity_type != individual`) | `False` (fail-closed) |
| `DSCR-ENTITY-TITLE-TRANSFERS` | Entity borrower: no multiple title transfers among entity/guarantors | `title_multiple_transfers_among_related_parties` | `False` (clean) |
| `DSCR-ENTITY-DOCS` | Entity borrower: Operating Agreement, Articles, Certificate of Good Standing on file | `entity_documents_complete` | `False` (fail-closed) |

**Why the defaults split two ways.** `check_compliance` skips (never fails) a rule whose condition
reads `INDETERMINATE` — so a field left unset (`None`) would silently never block, which is worse
than a wrong default for an affirmative attestation. The three fields above defaulting `False`
are process steps a human must actively perform and record (duplicate-SSN check, NMLS lookup,
entity-document collection) — a caller that forgets to set them gets a real `VIOLATED`, not a
silent pass. The others default to the "clean" value because they're findings that are normally
absent and only become a problem when someone actively flags them (a listing, a litigation, a
title-transfer history) — defaulting to "flagged" would be paranoid, not fail-closed.

**No numeric HOA-reserve or owner-occupancy-ratio standard exists in either source document.**
The Process Flow doc's condo-review checklist says "review reserve fund adequacy against program
guidelines" and "verify [owner-occupancy] ratio meets program guidelines" without stating the
guideline. `DSCR-CONDO-HOA-RESERVES` is authored as the AM's own qualitative determination
(`hoa_reserves_adequate: bool`), not a computed threshold — do not backfill a number here without
a real source; an owner-occupancy-ratio rule was **not authored at all** for the same reason (no
threshold to encode against a boolean would just be `DSCR-CONDO-HOA-RESERVES` again under a
different name).

**All five existing gold cases/demo fixtures (`cases.py`, `tests/eval/gold_cases/dscr/*.json`,
`test_dscr_conductor_engine.py`'s `_trigger()`) were updated** to set
`duplicate_ssn_cleared`/`broker_nmls_verified`/`loan_officer_nmls_verified` explicitly `true` —
the three fail-closed fields — so pre-existing "clean pass" fixtures stay clean rather than
newly violating on fields they were never written to know about. The condo/entity rules needed
no fixture changes: none of the five existing loans are entity borrowers, and the one condo
fixture (`DOUBLE_CAP`, non-warrantable condo) is already clean on the new fields' defaults.

## 2. Two IR defects found by authoring this — status, 2026-08-13

Both failed **late** — validated cleanly at authoring time, raised `ValueError` at evaluation.
Both fixed in japes `44f9b55`.

**D1 — `RatioCondition.direction` accepted operators the evaluator couldn't execute. Fixed —
but the workaround below is NOT removable, and that's by design, not an oversight.**
The field was typed `ComparisonOperator` (9 values); the evaluator only ever handled two
(`RatioDirection.AT_LEAST ">="` / `.AT_MOST "<="`). Authoring `direction: "<"` — the natural way
to write "DSCR below 1.0" — passed pydantic and raised `ValueError` on first evaluation.
*Landed fix:* `RatioCondition.direction` is now typed `RatioDirection` directly, so an invalid
value fails at construction with a message naming both legal values, plus a validator explaining
why: `evaluate_ratio` reports margin-to-threshold, and a strict boundary would make zero margin
mean pass on one side and fail on the other. **`RatioDirection` was deliberately NOT widened to
support strict `<`/`>`** — that was the explicit recommendation the bug report made and the fix
followed. Practical consequence: **`DSCR-SUB-1-DSCR-CLTV` / `DSCR-SUB-1-DSCR-FICO`'s
`dscr_sub_1_ceiling: "0.9999"` inversion is the correct, intended pattern for expressing a strict
ratio bound under the current design — not a scar, and left unchanged here.** A future `AllOf`/
composite-condition kind (§3 G1) doesn't change this either; expressing "ratio < X" still needs
either this `<=`-against-an-adjusted-threshold pattern or a precomputed flat context field checked
via `Expression`'s now-working `<` (D2 below) — the latter would mean computing DSCR outside the
`RatioCondition` machinery, a bigger change than this pack needs today.

**D2 — `Expression` float-cast the actual value for every non-membership operator. Fixed and
un-scarred here.**
`Expression(field="citizenship_type", operator="==", value="itin")` used to raise
`ValueError: could not convert string to float: 'itin'` — `float(actual)` ran before operator
dispatch. String equality is the natural way to write a borrower- or occupancy-type overlay, and
it was unusable; the membership operators were correctly exempted from the cast, equality was not.
*Landed fix:* `==`/`!=` now compare raw values (no numeric coercion — `"5" == 5` is correctly
`False`, a deliberate strictness change); ordering operators still cast, but a cast failure is
`INDETERMINATE`, never a raise. *Un-scarred here*: the six single-element `in`/`not_in` occurrences
that stood in for `==`/`!=` (`DSCR-STR-CLTV`, `DSCR-ITIN-CLTV`, `DSCR-ITIN-LOAN-MAX`,
`DSCR-FOREIGN-NATIONAL-ESCROW`, `DSCR-NO-RATIO-CLTV`, `DSCR-NO-RATIO-FICO`) are now plain `==`/`!=`
in `policies/standard.yaml`. Re-verified 18/18 green after the rewrite. Genuine multi-value
membership (`DSCR-HIGH-LTV-PROPERTY-TYPE`'s and `DSCR-PROPERTY-TYPE-CLTV`'s `in [...]` lists,
and `DSCR-STATE-INELIGIBLE`'s `not_in`, which mirrors the profile's `ineligible_states` list) is
untouched — those were never a workaround.

## 3. Four modelling gaps

**G1 — RESOLVED japes-side 2026-08-14, and consumed here since.** `Rule.applicability` was a
single `Condition` with no boolean-combinator kind, blocking several natively-conjunctive DSCR
rules:

- "warrantable condo **outside Florida**" in the >80% LTV property-type list;
- the **−5% CLTV Florida modifier** on non-warrantable condo and condotel;
- Illinois PPP buyout: *residential 1-4* **and** *(entity or individual)* **and** *amount ≤ $250,000*, with a second rule keyed on amount **and** rate > 8%;
- Pennsylvania: *individual* **and** *residential 1-2* **and** *< $319,777*.

*Landed fix:* `AllOfCondition`/`AnyOfCondition` — a real boolean-combinator `Condition` kind
(`jazzx_sdk/fabric/canonical/{policy,condition_evaluator}.py`; verdict algebra VIOLATED >
INDETERMINATE > SATISFIED, depth cap 5, no short-circuit — every limb evaluates). Committed to
japes (squashed into `74cb161`), not yet released as a version bump. This was option (a) of the
three considered; (b) fold the extra axis into the matrix and (c) bury the predicate in
`DslExpression` were both rejected for the reasons below, unchanged.

**Now authored:** 28 of the 77 rules in `process.yaml` and `standard.yaml` use `kind: all_of`/`any_of`, among them
the nine state prepayment-penalty rules G1 was blocking (`DSCR-PPP-IL-1`/`-2`, `-MS`, `-NJ`,
`-OH`, `-PA`, `-RI`, `-VA`, `-VT`), `DSCR-NMLS-VERIFIED`, and two added since: the
`DSCR-IO-MIN-LOAN` pair of legs and `DSCR-OVER-2M-NO-RATIO`'s gate. Of those twelve, ten are
applicability gates; two are conditions. §1a/§1b below describe them. The two Florida
carve-outs are authored too: `DSCR-HIGH-LTV-PROPERTY-TYPE` admits a warrantable condo only
outside Florida, and `DSCR-FL-CONDO-CLTV` caps a Florida non-warrantable condo or condotel at
the property-type cap less 5%.

**G2 — "DSCR < 1.0" and "No Ratio" are different conditions and must not share a rule.** The program summary groups them ("DSCR < 1.0 or No Ratio"), but on a no-ratio file the ratio evaluator returns **INDETERMINATE**, so an applicability probe written as a ratio silently yields NOT_APPLICABLE — the caps would quietly not apply, in the permissive direction. Encoded here as two rule pairs: `DSCR-SUB-1-DSCR-*` (ratio applicability) and `DSCR-NO-RATIO-*` (keyed on an explicit `dscr_documentation_type` field). **This requires the loan context to carry an explicit no-ratio flag** — it cannot be inferred from a missing DSCR.

**G3 — cap composition. RESOLVED, 2026-08-14.** `eligibility/compose.py::compose_caps` +
`ComposedCap` (D3 rev 2 Phase 2.2): `min()` across every applicable max-CLTV rule (structural
match on `condition.kind=="matrix" and compare_field=="cltv_pct"`, not a hardcoded rule list),
binding rule named. An authored `"NA"` cell is tracked separately (`ineligible_via`) rather than
folded into the `min()`; an unresolvable cap rule (`blocked_by_indeterminate`) forces
`passed=False` regardless of the known caps. Wired into `DSCRConductor` (Phase 2.3) via
`eligibility/assessment.py::run_eligibility_assessment` — Governor now enforces the deterministic
verdict, a model approval can't override a real violation.

**G4 — `Expression.value` takes literals, `RatioCondition.threshold` may not. RESOLVED,
2026-08-14 (A5, the lint option).** New `jazzx_sdk.fabric.canonical.policy_lint.
find_profile_literal_drift`: any `Expression` declaring `domain_extensions["profile_custom_key"]`
is checked against its named `PolicyProfile.custom` twin. Eight rules linked here (`DSCR-LA-MIN`,
`DSCR-LA-MAX`, `DSCR-STATE-INELIGIBLE`, `DSCR-HIGH-LTV-PROPERTY-TYPE`, `DSCR-HIGH-LTV-RESERVES`,
`DSCR-FICO-LT-620-RESERVES`, `DSCR-IO-MIN-LOAN`, `DSCR-NO-RATIO-FICO`) — `tests/scenarios/
dscr/test_profile_literal_drift.py` asserts zero drift against the real corpus.
`Expression.value` was *not* extended to accept `profile:` references — that would be a larger
`Expression.value` semantics change (today unambiguously a literal for every operator, string
and list included) for a field `RatioCondition.threshold` doesn't share. **Unreferenced keys:** one threshold, `dscr_min_no_ratio_floor`, has no consuming rule. The
STR FICO floor, seller concession cap and rural/FTHB/thin-file DSCR floors that were once on this
list are read by the 8.17 rules.

## 4. Encoding decisions worth knowing

- **Bands are `[min, max)`.** FICO 780 lands in the top tier; loan amount exactly $1,500,000 lands in band 1, and $1,500,001 in band 2. Both boundaries are tested. Loan amounts are quoted in $50 increments, so the half-open boundary is faithful.
- **Cell keys are `|`-joined band keys in `axes` order.** Reordering `axes` silently invalidates every key in the table. Treat axis order as part of the table's contract; if a table is ever re-cut, regenerate rather than hand-edit.
- **Values are whole percents** (`85`, not `0.85`), matching the source document so a reviewer can diff the YAML against the PDF by eye. `compare_field` is therefore `cltv_pct`, also whole percents.
- **Out-of-range loan amounts are caught by rules, not cells.** The matrix bands span $100,000–$3,000,000; below and above are `DSCR-LA-MIN` / `DSCR-LA-MAX` at priority 5, ahead of the grid at 10. A loan outside the range gets INDETERMINATE from the grid and VIOLATED from the range rule — correct, but only because the range rules exist. Don't delete them.
- **The profile is versioned to the source document** (`dscr_v6_15_2026_v1_1`). When Acra reissues the matrix, add a new profile rather than editing this one; the policy's `version` and `supersedes` carry the change.
- **`policy_type: institutional`** — this is Acra's own program, not a regulatory floor. It belongs in the Certified Client Overlay per ABA §11.1, not in pack semantics.

## 5. Running the tests

Paths in this section are relative to the authoring repo. This file also ships inside plato's
bundled seed packs, where neither the tests nor the pack path below exists.

`tests/scenarios/dscr/test_dscr_eligibility.py` expects the pack at
`config/packs/dscr_core/`. `cd jaci && pytest tests/scenarios/dscr/ -q` — 82 passed, run
directly from jaci's own environment (`pytest-asyncio`, `asyncio_mode = "auto"` already configured
in `pyproject.toml`). No import stub or import-order workaround needed from this location — the
ones noted in the original authoring sandbox were an artifact of running outside a full jaci
install and don't apply once the file lives under `tests/scenarios/`.
