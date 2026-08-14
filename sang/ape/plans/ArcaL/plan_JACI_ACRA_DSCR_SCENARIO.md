# plan_JACI_ACRA_DSCR_SCENARIO — rev 2

**Repo:** jaci `de2609d` ("0.19.5: carve acra_dscr scenario skeleton") · **Depends on:** japes `44f9b55`
**Supersedes rev 1**, which was written against `5719cf4` — before the `acra_dscr` skeleton existed. Rev 1 proposed a standalone deterministic evaluation loop; that was written blind to the skeleton and is withdrawn. This rev is written against what is actually on disk.

## What is already on disk (verified, `de2609d`)

```
src/jaci/scenarios/acra_dscr/        601 LOC
  conductor.py                       307  AcraDSCRConductor on jazzx_sdk.pipelines.investigation_loop
  schemas/acra_schemas.py            145  LoanApplication, AcraHypothesisContent,
                                          LoanCondition, EligibilityRecommendation, enums
  tools/registry.py                   78  AcraToolRegistry - 2 mock evidence tools
  __init__.py                         41
config/packs/acra_dscr_core/
  pack_manifest.yaml                      0.1.0-draft, governance_chain: DEFERRED
```

Built directly on the shared `investigation_loop` primitive from day one (its five siblings were hand-rolled and migrated later), mirroring `KYCConductor`'s shape — no Sentinel, no checkpoint, convergence read off `Context.loop_status`. Modes: Investigator / Verifier / Reasoner / Governor / Narrator. Prompts load from `prompts/acra-dscr/{mode}.md`. Placeholder prompts, placeholder mock evidence, placeholder escalation gate.

The skeleton's own docstring already scopes this plan: *"real taxonomy, policy corpus (MatrixCondition-based eligibility grid), and vendor integrations are separate, not-yet-built work."*

## 1. The architecture question, settled

Rev 1 and the skeleton looked like competing designs for one scenario. They are not. They are two layers, and the mistake would be to pick one.

**The eligibility grid is arithmetic, not judgment.** 99 numeric cells, band lookups, fail-closed threshold comparisons. Evaluating it inside a mode loop would make a deterministic answer nondeterministic, spend a model call per evaluation, and — decisively — break the citation chain, which is the entire answer to Acra's own stated over-conditioning problem. A condition that says *"CLTV 85.01% exceeds the 85% maximum for $900,000 / FICO 740 / purchase, per DSCR Program Summary 6.15.2026 V1.1"* is defensible. A model's paraphrase of the same fact is not.

**Equally, a pure rule loop cannot do what Acra actually needs modes for**: cross-document discrepancy detection (lease rent vs. Form 1007 market rent), entity and title review, evidence sufficiency and freshness, borrower narrative. That is judgment, and it is why the skeleton is right to exist.

**Resolution — the grid is a deterministic step the loop consumes, not a mode:**

1. A **pre-loop evaluation step** runs the 19 rules over the loan context and emits a structured `EligibilityAssessment` (verdicts, resolved cell keys, composed cap, cited violations) into `Context` before the first model call.
2. The same evaluator is registered as a **tool** on `AcraToolRegistry` so the Investigator can ask targeted questions ("what is the max CLTV for this shape?") without re-deriving them.
3. **Governor enforces the deterministic verdicts.** A model-produced recommendation that contradicts a grid VIOLATED is a Governor block, not a negotiation.

This has precedent in the platform's own recorded decisions: computed rows are deterministic via the expression DSL and never model-inferred (the RB/Mesa Verde template invariants), and "deterministic pre-pass before any model call" is the recorded build order for `TemplateFillAgent`. Same discipline, same reason.

The practical consequence: **rev 1's `eligibility.py` survives, but as a step + tool under the conductor, not as a parallel entry point.** Nothing in the skeleton needs to be undone.

---

## Phase 0 — Land the policy corpus (no code changes)

Four artifacts exist and are verified green **in the authoring sandbox, not in the repo** — placing them is this phase.

```
config/packs/acra_dscr_core/
  profiles/acra_dscr_profile.yaml    5 tables; 99-cell CLTV grid; 6 thresholds; 11 scalars
  policies/eligibility.yaml          19 rules: 5 matrix, 4 ratio, 10 expression
  ENCODING_NOTES.md                  band semantics, cell-key contract, NA discipline, gaps
tests/scenarios/acra_dscr/
  test_acra_eligibility.py           17 behavioural cases + grid completeness
```

Point `pack_manifest.yaml` at `profiles/` and `policies/` (it currently declares neither). Leave `certification_status: draft` and `governance_chain: DEFERRED` — both are accurate until the ABA set exists.

**Acceptance:** `pytest tests/scenarios/acra_dscr/ -q` → 18 passed (needs `pytest-asyncio`); adjust the `PACK` path constant if the pack lands elsewhere.

**Two workaround scars are now removable.** The artifacts were authored before `44f9b55` and carry four single-element `in` lists standing in for `==`, plus a `dscr_sub_1_ceiling: "0.9999"` inversion. With A1/A2 landed, rewrite them to plain `==` and a direct comparison, and confirm the 18 tests stay green. `ENCODING_NOTES.md` §2 marks each one. **Update §2 to say "fixed in 44f9b55" rather than deleting it** — it is the record of why the artifacts looked odd.

---

## Phase 1 — Bind the corpus to the skeleton

Three concrete integration tasks. This is where rev 1's design meets the real schemas.

**1.1 — Context adapter (`eligibility/context.py`).** `LoanApplication`'s field names do not match what the 19 rules read, and the mismatch fails *silently* as INDETERMINATE rather than loudly:

| Rule reads | `LoanApplication` has | Action |
|---|---|---|
| `fico` | `fico_score` | map |
| `citizenship_type` | `citizenship` | map + normalize to the enum the rules use (`itin`, `foreign_national`, …) |
| `loan_purpose` | `loan_purpose` (enum) | map to the rules' string values |
| `property_state` | `property_address` only | **derive** — needs parsing or a new field |
| `cltv_pct` | `property_value`, `loan_amount` | **compute** — and see Phase 3 on why this is a proxy |
| `property_type` | free-form string | constrain to the overlay vocabulary (`non_warrantable_condo`, `condotel`, `manufactured`, `two_to_four_unit`, `sfr`, `warrantable_condo`, `townhome`, `pud`) |
| `gross_rental_income`, `pitia`, `reserves_months`, `occupancy_subtype`, `dscr_documentation_type` | absent | **add to `LoanApplication`** |

`dscr_documentation_type` deserves a comment on the model: it is **not** derivable from a missing DSCR. A no-ratio file evaluates INDETERMINATE on a ratio probe, so the sub-1.0 caps would silently not apply without an explicit flag (`ENCODING_NOTES.md` §3 G2).

**Write the guard as a test, not a convention:** assert that every field named across the 19 rules resolves on the adapter's output. Without it, a rename produces a quiet pass.

**1.2 — `LoanCondition` must carry its citation.** The skeleton's model has `condition_id`, `condition_type`, `category`, `description`, `responsible_party`, `severity` — and no link back to what was violated. Add `rule_id`, `policy_refs`, and the resolved `cell_key` / `cell_value`. This is the mechanical form of ABA §5.9 (*no Decision without `policy_refs`, `evidence_refs`, `trace_id`, `produced_by`*), and it is what makes conditions defensible rather than assertive. **Enforce it as an assertion: a condition without a citation is not constructible.**

**1.3 — `cases.py`, the one data seam.** Follow `cre_underwriting/cases.py:1-6` verbatim — *"adding a case = a new record here (+ a selector entry), no new code."* Five synthetic loans chosen for geometry, not realism: a clean mid-grid pass; an exact band boundary ($1,500,000 vs $1,500,001, cap flips 80% → 75%); an authored `NA` cell; two caps binding at once (non-warrantable condo in Florida); a sub-1.0 DSCR cash-out. **Synthetic only** — no Acra loan data in the repo, redacted or otherwise.

---

## Phase 2 — The evaluation step and cap composition

**2.1 — `eligibility/evaluate.py`.** For each rule in priority order: evaluate `applicability` first (non-SATISFIED ⇒ skip, `NOT_APPLICABLE`, no `condition` evaluation), then `condition`. Reference implementation is the `_verdict()` helper in the delivered test file. Use `get_condition_evaluator(kind)` — do not re-implement dispatch. The profile reaches the evaluator via `RATIO_PROFILE_CONTEXT_KEY` in the context dict.

**2.2 — Cap composition. This is the one genuinely undesigned piece in the platform.** Several max-CLTV rules can bind at once (grid 80%, non-warrantable condo 75%, Florida −5%, STR 70%). Each rule reports independently; the IR has no notion of "the binding cap." Needed: **`min()` across satisfied cap rules, with the binding rule named.** `RuleOutcome.inputs` already carries `cell_key` and `cell_value` for every matrix rule, so the data is there.

Two invariants: the composed result must name **which** rule bound and why; and an INDETERMINATE cap must **not** silently drop out of the `min()` — an unknown cap is not an absent cap. Model it explicitly (`blocked_by_indeterminate: list[str]`) rather than letting a missing value read as a pass.

**2.3 — Wire into the conductor.** The assessment runs as a pre-loop step feeding `Context`; register the evaluator as a tool on `AcraToolRegistry` alongside `get_credit_report` / `get_appraisal`; add a Governor gate that blocks any recommendation contradicting a deterministic VIOLATED. The existing `GovernorDecision.policy_violations` field is already the right shape to carry them.

**2.4 — Prompts.** `prompts/acra-dscr/{investigator,verifier,reasoner,governor,narrator}.md` are placeholders. The Reasoner and Governor prompts in particular must state that grid verdicts are **given, not inferred** — the model's job is to reason about what is missing, discrepant, or judgment-bearing, never to re-derive a cell.

---

## Phase 3 — UI, gold cases, and the LTV honesty problem

**3.1 — `SCENARIOS` entry** at `ui/registry.py:96` (fields defined `:23-56`; all targets lazy `(module, attr)` pairs). Set `pack_id: acra_dscr_core` — resolved lazily at `:78`, `FileNotFoundError → None`, so a broken manifest degrades rather than crashes. **No `app.py` edit** — tabs derive from `has_demo`/`has_dashboard`. Modes need no registration. Add `ui/common/data_loaders.py:137-148, 228-236` entries only if using the Dashboard eval stack. Route through `ui/dashboard_view.py:60`, not the legacy hardcoded router at `ui/pages/dashboard.py:25-41`.

**3.2 — Demo page**, ~300 lines. `ci_spread/ui/demo_page.py` is 3,101 lines; that is the anti-pattern. Show: case selector, grid resolution as *inputs → band keys → cell → verdict*, the composed cap with the binding rule named, generated conditions with citations, and the loop's judgment findings separately from the deterministic ones. **The separation is the demo's whole point** — an underwriter should see at a glance which findings are arithmetic and which are inference.

**3.3 — Gold cases** at `tests/eval/gold_cases/acra_dscr/` — already referenced by the manifest (`pass_threshold: 0.75`), required by the Concepts case-fleet view (`ui/concepts_view.py:277-280`). Seed from the five fixtures.

**3.4 — LTV.** Phases 0–2 take CLTV as an input or a `loan_amount / property_value` proxy. There is no appraisal-driven LTV calculator anywhere in the repo — only a book proxy and an explicit data-gap comment at `ui/property_case_page.py:83`. **CLTV is the primary axis of all 99 cells**, so a proxy means the grid is exercised against a number the underwriter would not accept. Includes the lien stack and the HELOC rule (CLTV on the greater of credit-line limit or current balance). Decision gate G2 in the program plan; the demo must label the proxy as a proxy until it lands.

**Out of scope, all phases:** Byte/LOS anything (no LOS connector exists in either repo — zero hits for Encompass, nCino, Blend, Byte), the ten vendors, broker outreach and the 48-hour escalation, closing and funding.

---

## Acceptance

1. `pytest tests/scenarios/acra_dscr/ -q` green (18), and green again after any japes IR change — this slice exercises three condition kinds, applicability pre-checks, band boundaries, NA sentinels, and the INDETERMINATE path in one file.
2. Every field read by the 19 rules resolves on the adapter output — asserted by test.
3. No `LoanCondition` is constructible without a `rule_id` and a policy ref.
4. For each of the five fixtures the demo shows resolved cell key, composed cap with the binding rule named, and cited conditions.
5. Governor blocks a recommendation that contradicts a deterministic VIOLATED — tested with a deliberately contradictory Reasoner output.
6. Deterministic findings and model findings are visually distinguishable in the demo.
7. `git diff --stat` touches exactly one pre-existing file outside `scenarios/acra_dscr/`: `ui/registry.py`.

## Sequencing

Phase 0 has no dependencies and can land immediately. Phase 1.1/1.2 are schema changes and should land together. Phase 2.2 (cap composition) is the design-bearing step — propose the composed-result shape before implementing it. Phase 3.4 is gated on a decision, not on code.
