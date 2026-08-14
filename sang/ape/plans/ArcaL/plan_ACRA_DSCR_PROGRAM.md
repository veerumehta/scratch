# plan_ACRA_DSCR_PROGRAM — master plan

**Owner:** Virendra Mehta · **Rev:** 1, 2026-08-13
**Scope:** everything needed to stand up Acra Lending Commercial DSCR on Platform v2 / JAPES SDK, from IR fixes through scenario build, governance artifacts, and the client-facing engagement plan.
**Verified against:** japes 2.4.1 (`577c28d`) + the uncommitted `MatrixCondition` change set; jaci `5719cf4`.

This is the index and the sequencing. It does not repeat the detail in the sub-plans — each step names the document that carries it.

---

## 1. Document set

| # | Document | What it is | Destination | Status |
|---|---|---|---|---|
| **D1** | `Acra_DSCR_on_Platform_v2_Reuse_and_Build_Plan.md` | Reuse map, gap list, scenario verdict, what to change in the Acra deck | `jaci/docs/plans/` (already referenced by the pack manifest header) | rev 2, code-verified |
| **D2** | `plan_JAPES_POLICY_IR_AUTHORING_DEFECTS.md` | Two fail-late IR defects + the composite-applicability decision | `japes/` (repo root, matching `plan_JAPES_1_5_0_*` convention) | ready |
| **D3** | `plan_JACI_ACRA_DSCR_SCENARIO.md` | 4-phase scenario build, verified wiring points, acceptance | `jaci/docs/plans/` | ready |
| **D4** | `acra_dscr_profile.yaml` | 5 profile tables — 99-cell CLTV grid, 6 thresholds, 11 scalars | `jaci/config/packs/acra_dscr_core/profiles/` | verified green |
| **D5** | `eligibility.yaml` | 19 rules — 5 matrix, 4 ratio, 10 expression | `jaci/config/packs/acra_dscr_core/policies/` | verified green |
| **D6** | `test_acra_eligibility.py` | 17 behavioural cases + grid completeness | `jaci/tests/scenarios/acra_dscr/` | 18/18 pass |
| **D7** | `ENCODING_NOTES.md` | Band semantics, cell-key contract, NA discipline, 2 defects, 4 modelling gaps | `jaci/config/packs/acra_dscr_core/` | ready |
| **D8** | ABA binding worksheets ×6 + relay family | Governance artifacts per assistant archetype | project docs | **not written** — step C1 |
| **D9** | Certified Client Overlay | Where Acra's grid and state rules legally live per ABA §11.1 | project docs | **not written** — step C2 |

D1 is the argument. D2 and D3 are the executable plans. D4–D7 are the artifacts D3 phase 0 places. D8–D9 are the governance track that has to exist before anything is called certified.

---

## 2. Dependency graph

```
A1 ─┐
A2 ─┴─→ B5 (unwind workarounds)
A3 ────→ B3 (violation rendering in the demo)
A4 ────→ C2-full (prepay family, FL modifiers)   [DECISION GATE]

B0 ──→ B1 ──→ B2 ──→ B3
                     └──→ B4 (LTV)                [DECISION GATE]
B0 ──────────────────────→ C2 (overlay content)

C0 ──→ C1 ──→ C3                                  [C0 = D7-blocker below]

D-track (client-facing) runs parallel; only Dk1 depends on B-track evidence.
```

**B0 has no dependencies and should land first** — it is four files and a test run.

---

## 3. Track A — japes IR (owner: the Claude Code session already in japes)

Carried by **D2**. Do not start these from this session; hand D2 over whole.

| Step | Item | Size | Blocks |
|---|---|---|---|
| **A1** | Narrow `RatioCondition.direction` to `>=` / `<=` at the model boundary | S | B5 |
| **A2** | Cast only for ordering operators; `==`/`!=` on raw values; type mismatch → INDETERMINATE | S | B5 |
| **A3** | Render `matrix` violations from `RuleOutcome.inputs` (`cell_key`, `cell_value`) instead of a bare kind string | S | B3 quality |
| **A4** | `AllOf` / `AnyOf` composite applicability | M + design | C2-full |
| **A5** | Lint: policy literal vs diverging `profile.custom` twin | S | — |

**A4 is a decision, not a ticket.** The evaluator is easy; trace composition is not — an underwriter must be able to see *which* limb failed, or the audit trail degrades to "composite violated," which is worse than the workaround it replaces. Settle verdict algebra (INDETERMINATE dominates SATISFIED in `AllOf`) and `evidence_contract()` union semantics before writing code. Until A4 lands, the 13-state prepayment family and the Florida −5% modifiers cannot be authored honestly.

**Regression bar for the whole track:** `test_condition_evaluator.py` (40 tests, 13 matrix), `test_default_policy_expert.py`, **and D6**. D6 is a useful second consumer — it exercises three condition kinds, applicability pre-checks, band boundaries, NA sentinels, and the INDETERMINATE path in one file.

---

## 4. Track B — jaci scenario (owner: a Claude Code session in jaci)

Carried by **D3**. Hand over D3 + D4–D7 together.

| Step | Item | Depends | Acceptance |
|---|---|---|---|
| **B0** | Place D4–D7; point `pack_manifest.yaml` at them | — | `pytest tests/scenarios/acra_dscr/ -q` → 18 passed |
| **B1** | Scenario package: schemas, policy registry, `cases.py` (5 synthetic loans) | B0 | Test asserts every field read by the 19 rules exists on `AcraLoanCase` |
| **B2** | Evaluation loop, **cap composition**, condition generation with citations | B1 | Composed cap names the binding rule; INDETERMINATE caps don't silently drop out of `min()` |
| **B3** | `SCENARIOS` entry (`ui/registry.py:96`), demo page (~300 lines), gold cases | B2 | `git diff --stat` touches exactly one pre-existing file |
| **B4** | Appraisal-driven LTV/CLTV calculator + lien stack + HELOC rule | B2 | **DECISION GATE** — see §6 |
| **B5** | Unwind the four `in`-list workarounds and the `0.9999` ceiling | A1, A2 | D6 still green after rewrite to plain `==` |

**B2 is the step with real design content.** Everything else is wiring. Cap composition (`min()` across satisfied cap rules, binding rule named) is undesigned anywhere in the platform today and this scenario is where it gets owned.

---

## 5. Track C — governance

**C0 — unblock first.** The `InteractiveAgentSpec` vs `AssistantManifest` question (canonical, or generation relationship?) has been open since 2026-08-03 and is a hard prerequisite for authoring six bindings. Do not start C1 until it is answered; six worksheets authored against the wrong artifact is six worksheets to redo.

| Step | Item | Depends | Notes |
|---|---|---|---|
| **C0** | Resolve `InteractiveAgentSpec` vs `AssistantManifest` | — | Architecture call |
| **C1** | Six ABA worksheets + relay family | C0 | Scope below |
| **C2** | Certified Client Overlay carrying the grid, overlay families, state rules | B0 | Content is D4/D5; ABA §11.1 is the legal home |
| **C3** | Relay integration suite — handoff payload contracts across the five handoffs | C1 | §10.1 makes it mandatory for relay bindings |

**C1 scope, first pass.** Six archetypes (Loan Officer, Processor, Underwriter, Legal/Entity, Closer, Post-Closing) × four load-bearing sections — §3 scope worksheet, §4.3 action classes, §7.2 authority matrix, §8.2 handoff matrix. Not the full 12-section certification set; that is C1b once the first pass survives review. Fixed decisions to carry into every worksheet:

- `human_only_decision_classes` = the credit decision itself, plus any adverse action (NOIA / 10-day letter, third-notice cancellation).
- Byte condition write-back is a `write-back` action class requiring `reversible` + `mandatory_trace_event`.
- External communication is prohibited unless expressly exposed — so broker outreach and the 48-hour escalation must be an exposed cell per binding or they're disallowed by default.
- Autonomy proposals seed from CRE §8 automation percentages (Processor 80%, Underwriter 60% recommend-only, Compliance/Legal 85%) as `annex_ceiling` proposals subject to §10.6 promotion gates — never as go-live postures.

**C2 is the load-bearing governance call.** Acra's numbers belong in the overlay, not the ABA, or one client gets hardcoded into pack semantics — the exact failure the "no CL Domain Pack yet" decision was written to prevent. `SkillRegistry`'s tier guard (`allow_override=True` required) is what makes §11.2 mechanical rather than aspirational.

---

## 6. Decision gates

| Gate | Question | Blocks | Recommendation |
|---|---|---|---|
| **G1** | Fund `AllOf`/`AnyOf`, or accept option B (state as a matrix axis, ~50× cells) / option C (DSL applicability)? | A4, full program encoding | **A** — registry is open, `MatrixCondition` proved the path; B and C both destroy reviewability |
| **G2** | Who funds the LTV calculator — Acra Phase 3 as the deck says, or moved forward? | B4, deck credibility | **Move forward.** LTV is the primary axis of all 99 grid cells; assessing eligibility on a book-LTV proxy is not a demo you want in front of underwriters |
| **G3** | `InteractiveAgentSpec` vs `AssistantManifest` | C1 | Open since 2026-08-03; needs a name against it |
| **G4** | Sequencing vs YETI — Acra downstream, or parallel with a shared hardening backlog? | staffing | Acra consumes what YETI hardens; it is a lighthouse and hardening case, and the sequencing should say so explicitly |
| **G5** | Does Byte expose condition webhooks and two-way sync at Acra's plan tier? | the deck's Phase 2 | Ask Acra now — it is question 1 on deck slide 26, and Phase 2's five-week window is a guess until answered |

---

## 7. Track D — client-facing engagement

Carried by **D1 §7**. Independent of A–C except where noted.

| Step | Item |
|---|---|
| **Dk1** | Re-aim Phase 0: compress splitting/classification to a week-1 spike on real *scanned* packages; spend the remaining three weeks proving guideline-assessment fidelity against the grid, with every condition citing the directive it failed. B0–B2 is the evidence that this is achievable |
| **Dk2** | Convert Phase 2 to spike-then-commit pending G5 |
| **Dk3** | Move LTV forward in the deck (G2) |
| **Dk4** | Add the entity → prepayment-penalty coupling to the process view — vesting drives PPP buyout in 4+ states, and the deck treats Legal/Entity as a parallel lane with no downstream pricing effect |
| **Dk5** | Add a DocIntel cost-per-package line; price it in week 1 — `split_document` raises on scanned files and broker DSCR packages are scan-heavy |
| **Dk6** | Restate accuracy as a tracked curve with a weekly baseline, not a go-live SLA |

---

## 8. How to hand this to Claude Code

One track per session, in this order. Each line is the handoff.

1. **japes session (already running):** "Execute `plan_JAPES_POLICY_IR_AUTHORING_DEFECTS.md`, steps A1–A3. A4 needs a design decision first — bring back a recommendation on trace composition, don't implement."
2. **jaci session, new:** "Execute `plan_JACI_ACRA_DSCR_SCENARIO.md` phase 0 only. The four artifacts are attached. Stop at green tests and report."
3. **jaci session, continue:** "Phases 1–3. Phase 2 cap composition is the design-bearing step — propose the composed-result shape before implementing."
4. **After A1/A2 land:** "Step B5: unwind the workarounds in `ENCODING_NOTES.md` §2, confirm D6 still green."
5. **Governance (not Claude Code — human):** G3, then C1.

**Standing constraints for every session:**

- Don't fold anything into `cre_underwriting` (D3 §1 has the three reasons).
- Don't imitate `cl_of_core` / `cl_sp_core` — draft scaffolds with no consumer, `governance_chain: DEFERRED`, non-existent gold-case dirs. The only thing worth copying is the `depends_on` fragment pattern.
- Don't "clean up" the four `in`-list workarounds or the `0.9999` ceiling before A1/A2 land — they'll break.
- Don't reorder `MatrixCondition.axes` on an authored table — cell keys are `|`-joined in axis order, and reordering silently invalidates all 99.
- Synthetic loan data only. No Acra files in the repo, redacted or otherwise.

---

## 9. What "done" means for this phase

Not the Acra engagement — this phase's bar is narrower and worth stating so it can be hit:

1. An Acra underwriter can look at the demo, pick a loan, and see the grid resolve the way they would resolve it by hand off the DSCR Program Summary PDF — including the boundary cases and the ineligible cells.
2. Every generated condition cites the directive it failed. Conditions that cannot cite one are not issuable.
3. When two caps bind, the composed result names which one bound and why.
4. The whole thing survives an IR change without silent drift, because D6 runs against it.

That is the honest Phase 0 outcome, and it is a stronger thing to show Acra than a document classifier.
