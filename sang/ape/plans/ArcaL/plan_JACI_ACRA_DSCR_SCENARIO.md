# plan_JACI_ACRA_DSCR_SCENARIO

**Repo:** jaci (HEAD `5719cf4`) · **Depends on:** japes 2.4.1 + the `MatrixCondition` change set (currently uncommitted in the japes working tree)
**Goal:** a working Acra Lending Commercial DSCR eligibility scenario — grid-driven assessment producing cited conditions — carved as its own scenario, reusing the `commercial_lending` capability rather than forking `cre_underwriting`.
**Non-goal:** the Acra deployment engagement. This is Phase 0 substrate: no Byte/LOS, no vendor integrations, no closing or funding.

## Why a new scenario rather than folding into `cre_underwriting`

Three verified reasons, so this isn't relitigated mid-build:

1. `cre_underwriting` has **no pack manifest** — `config/packs/cre_underwriting_core/` contains only `mode_tuning/`, and its policies live in-scenario at `policies/policies.yaml`. There is no `policies.overlays` slot to hang an Acra overlay on, so the mechanism that would make fold-in cheap isn't in use there.
2. Customer content is baked into its mock layer — `property_name: "Mesa Verde Apartments"` at `tools/registry.py:374,400,427,491`, `max_ltv: 0.75` hardcoded at `:505`, a two-item literal deal selector at `ui/demo_page.py:149`; 16 Mesa Verde references total.
3. Precedent: `insurance_diligence` was split **out** of `cre_underwriting` for exactly this reason — see `insurance_diligence/cases.py:6`.

Carve-out is cheap: the only mandatory shared-file edit is one entry in `SCENARIOS` (`ui/registry.py:96`).

**Do not imitate `cl_of_core` / `cl_sp_core`.** They are `0.1.0-draft` scaffolds with no consuming scenario, experts pointing back at `ci_spread`'s `CIPolicyExpert`, `governance_chain: DEFERRED`, and gold-case dirs that don't exist. The one thing worth copying from them is the `depends_on` fragment pattern at `cl_of_core/pack_manifest.yaml:34-38` (resolved by japes `jazzx_sdk/pack/pack.py:127-157`) — the only working reuse-by-reference seam in the repo.

---

## Phase 0 — Land the pack artifacts (no scenario code yet)

Four files exist and are verified green; they just need placing under the manifest that's already at `config/packs/acra_dscr_core/pack_manifest.yaml`.

```
config/packs/acra_dscr_core/
  pack_manifest.yaml            # exists (0.1.0-draft)
  profiles/acra_dscr_profile.yaml    # NEW - 5 tables, 99-cell grid, 6 thresholds, 11 scalars
  policies/eligibility.yaml          # NEW - 19 rules: 5 matrix, 4 ratio, 10 expression
tests/scenarios/acra_dscr/
  test_acra_eligibility.py           # NEW - 17 behavioural cases + grid completeness
```

Also add `ENCODING_NOTES.md` to the pack directory — it documents band semantics, the `|`-joined cell-key contract, the NA-sentinel discipline, and the four modelling gaps. A future author who reorders `MatrixCondition.axes` without reading it silently invalidates all 99 cell keys.

Update `pack_manifest.yaml` to point at the new files (it currently has no `policies:` or `profiles:` section) and leave `certification_status: draft`, `governance_chain: DEFERRED` as they are — both are accurate until the ABA set exists.

**Acceptance:** `pytest tests/scenarios/acra_dscr/ -q` → 18 passed. Requires `pytest-asyncio`. Adjust the `PACK` path constant in the test if the pack lands elsewhere.

**Known scars to preserve as-is, and to un-scar once the japes fixes land:** four rules use single-element `in` lists where `==` is meant, and the sub-1.0 DSCR probe compares `<=` against a `dscr_sub_1_ceiling: "0.9999"` threshold. Both are workarounds for japes defects, flagged in `ENCODING_NOTES.md` §2. Don't "clean them up" locally — they'll break.

---

## Phase 1 — Scenario package skeleton

```
src/jaci/scenarios/acra_dscr/
  __init__.py
  schemas/acra_case.py        # AcraLoanCase + AcraEligibilityResult
  policies/registry.py        # PolicyRegistry over the pack YAML
  cases.py                    # the ONE data seam - fixtures only, no logic
  eligibility.py              # rule evaluation + cap composition
  ui/demo_page.py             # render_demo_page(label)
```

**`schemas/acra_case.py`.** Copy `LoanCondition` / `ConditionType` / `UnderwritingRecommendation` from `cre_underwriting/schemas/case_context.py:61-67, 201-212, 215-240` — `ConditionType`'s four buckets (prior_to_closing / prior_to_funding / post_closing / ongoing_covenant) map onto Byte PTC/PTF directly, so they're the right vocabulary to carry forward. `AcraLoanCase` needs the fields the 19 rules read, and they must be named exactly as authored: `loan_amount`, `fico`, `loan_purpose`, `cltv_pct`, `property_state`, `property_type`, `occupancy_subtype`, `citizenship_type`, `gross_rental_income`, `pitia`, `reserves_months`, `dscr_documentation_type`, `escrow_waiver_requested`, `product_is_interest_only`. A field-name mismatch surfaces as INDETERMINATE, not as an error — write a test that asserts every field named across the 19 rules exists on the model, or this will bite silently.

`dscr_documentation_type` deserves a comment on the model: it is **not** derivable from a missing DSCR. A no-ratio file evaluates INDETERMINATE on a ratio probe, so the sub-1.0 caps would silently not apply without this explicit flag (`ENCODING_NOTES.md` §3 G2).

**`policies/registry.py`.** Mirror `cre_underwriting/policies/registry.py:16` — `ACRA_REGISTRY = PolicyRegistry(load_policies(_POLICIES_YAML))`, plus a module-level `PolicyProfile` load. Both are module constants; the profile must reach the evaluator through `RATIO_PROFILE_CONTEXT_KEY` in the context dict.

**`cases.py`.** Follow the `cre_underwriting/cases.py:1-6` discipline verbatim: *"Adding a case = a new record here (+ a selector entry), no new code."* Five synthetic loans, chosen to exercise the interesting geometry rather than to look realistic: one clean pass mid-grid; one at an exact band boundary ($1,500,000 vs $1,500,001, which flips the cap from 80% to 75%); one landing on an authored `NA` cell; one where two caps bind at once (non-warrantable condo in Florida — the case that proves the composition rule); one sub-1.0 DSCR cash-out. **Synthetic only** — no Acra loan data in the repo, redacted or otherwise.

---

## Phase 2 — Eligibility evaluation and cap composition

`eligibility.py` is where the real work is, and one piece of it is genuinely undesigned.

**Evaluation loop.** For each rule in priority order: evaluate `applicability` first (non-SATISFIED ⇒ skip, `Verdict.NOT_APPLICABLE`, no `condition` evaluation at all), then `condition`. The reference implementation is in the delivered test file's `_verdict()` helper. Do not re-implement dispatch — use `get_condition_evaluator(kind)`.

**Cap composition — the undesigned piece (`ENCODING_NOTES.md` §3 G3).** Several max-CLTV rules can bind simultaneously (grid 80%, non-warrantable condo 75%, Florida −5%, STR 70%). Each rule reports its own verdict independently; the IR has no notion of "the binding cap." The underwriter needs **`min()` across all satisfied cap rules, with the binding one named** — and this scenario is where that fold gets owned. `RuleOutcome.inputs` already carries `cell_key` and `cell_value` for every matrix rule, so the data is there.

Two rules for the implementation: the composed result must name **which** rule bound and why, and an INDETERMINATE cap rule must **not** silently drop out of the `min()` — an unknown cap is not an absent cap. Model it explicitly (composed result carries a `blocked_by_indeterminate` list) rather than letting a missing field read as a pass.

**Condition generation.** Every VIOLATED rule produces a `LoanCondition` carrying the `rule_id`, the rule's `description`, its `citations` (`acra_dscr_program_summary_6_15_2026_v1_1`), and the resolved `cell_key` / `cell_value` from `RuleOutcome.inputs`. This is the mechanical form of the ABA §5.9 invariant — no Decision without `policy_refs`, `evidence_refs`, `trace_id`, `produced_by` — and the honest answer to Acra's over-conditioning concern: **a condition that cannot cite a directive should not be issuable.** Enforce it as an assertion, not a convention.

Note `experts/policy/default.py:33-50` renders unrecognised Condition kinds as a bare kind string, so a grid violation currently reads `"matrix"` rather than naming the cell. Either wait for the japes fix or render `cell_key`/`cell_value` locally in this scenario — but don't ship a demo where the violation message says `matrix`.

---

## Phase 3 — Registry entry, UI, gold cases

**The one shared-file edit.** Add a `Scenario(...)` entry to `SCENARIOS` at `ui/registry.py:96`. Fields are defined at `:23-56`: `key, label, icon, display, dashboard_target, demo_target, pack_id, gold_dir, pipeline_target, focus_pipeline_target, focus_handoff, policy_resolution_target`. All targets are lazy `(module, attr)` pairs, so nothing imports at registry load. Set `pack_id: acra_dscr_core` — resolved lazily at `:78` via `Pack.from_manifest`, with `FileNotFoundError → None`, so a broken manifest degrades rather than crashing the app.

**No `app.py` edit needed** — tabs derive from `scenario.has_demo` / `has_dashboard` (`app.py:59,81,128-142`). Modes need no registration.

**`ui/common/data_loaders.py:137-148, 228-236`** carries string-literal `scenario ==` branches for trigger-field filtering and gold-case directory mapping. Add entries only if this scenario uses the Dashboard eval stack.

**`ui/pages/dashboard.py:25-41`** is a second, redundant hardcoded router paralleling `ui/dashboard_view.py:60`. Route through `dashboard_view` and leave the legacy path alone. (It's dead weight and worth deleting in a separate change — not this one.)

**Gold cases.** `tests/eval/gold_cases/acra_dscr/` — required for the Concepts case-fleet view (`ui/concepts_view.py:277-280`), and already referenced by the pack manifest's `evaluation.gold_cases_path` with `pass_threshold: 0.75`. Seed from the five `cases.py` fixtures.

**Demo page.** Deliberately small. `ci_spread/ui/demo_page.py` is 3,101 lines; that is the anti-pattern. Target ~300: a case selector, the grid resolution shown as *inputs → band keys → cell → verdict*, the composed cap with the binding rule named, and the generated conditions with their citations. The demo's job is to make the grid legible to an Acra underwriter, not to be a product.

---

## Phase 4 — Deferred, with a note on why

**LTV/CLTV calculation.** There is no appraisal-driven LTV calculator anywhere in the repo — only a book-LTV proxy and an explicit data-gap comment at `ui/property_case_page.py:83` (`"ltv_pct": None  # purchase price assumed -> needs appraisal`) and `ui/demo_page.py:44`. Phase 0–3 take `cltv_pct` as an input on the case model. **This is the largest single omission in the Acra deployment deck**, which schedules LTV for Phase 3 while making it the primary axis of the Phase 0/2 eligibility assessment. Includes the lien-stack rule and the HELOC treatment (CLTV computed on the greater of the credit-line limit or current balance).

**DSCR worksheet.** `OutputTemplate` / `TemplateField` / `TemplateFillAgent` do not exist in either repo (zero hits) — still proposed, not shipped. The `LineVocabulary` / `WorkbookLayout` / expression-DSL machinery that *does* ship is enough for a first worksheet if one is needed before those land.

**Explicitly out of scope for all phases here:** Byte/LOS anything (no LOS connector exists in either repo; zero hits for Encompass, nCino, Blend, Byte), the ten third-party vendors, broker outreach and the 48-hour escalation protocol, closing and funding.

---

## Acceptance

1. `pytest tests/scenarios/acra_dscr/ -q` green (18 tests), and green again after any japes IR change — this slice is a useful second consumer, exercising `matrix`, `ratio`, and `expression` kinds, `applicability` pre-checks, band boundaries, NA sentinels, and the INDETERMINATE path in one file.
2. Every field read by the 19 rules exists on `AcraLoanCase` (asserted by test, not by inspection).
3. For each of the five fixtures the demo shows the resolved cell key, the composed cap with the binding rule named, and one `LoanCondition` per violation, each citing a `rule_id` and the source directive.
4. No violation message renders as a bare `"matrix"`.
5. `git diff --stat` touches exactly one pre-existing file: `ui/registry.py` (plus `data_loaders.py` only if the Dashboard eval stack is used).

## Sequencing note

Phase 0 has no dependency on the japes fixes and can land immediately. Phases 1–3 are unaffected by them except cosmetically (P4b, violation rendering). The two IR defects only need to be fixed before the *next* tranche of program encoding — the prepayment-penalty family and the credit-event overlays — because that tranche needs composite applicability (`AllOf`/`AnyOf`), which is the one item that genuinely blocks.
