# plan_ACRA_DSCR_PROGRAM — master plan, rev 2

**Owner:** Virendra Mehta · **Rev 2:** 2026-08-13, status-corrected against the repos
**Baseline:** japes `44f9b55` · jaci `de2609d`

Rev 1's status table was wrong in both directions — it marked artifacts "verified green" that exist only as delivered files rather than on disk, and marked japes work "ready" that had already landed. Corrected below. Rev 1's §8 handoff instructions are withdrawn; use §8 here.

---

## 1. What actually landed since rev 1

**japes** — three commits, all of them things rev 1 listed as open:

| Commit | What |
|---|---|
| `272f1e3` | `MatrixCondition` (P8, D2) + fixes the latent `IN`/`NOT_IN`/`CONTAINS` gap |
| `e777bbf` | **HITL suspend now allowed inside a conductor `Loop`** |
| `44f9b55` | `RatioCondition.direction` over-typing + `Expression` float-cast — A1 and A2 |

`e777bbf` closes one of the two structural blockers flagged in the build plan. Acra's conditions loop ("same-day review, no queuing") and per-property exception approvals are loops; suspend inside them raising was going to be discovered in week 9. It is now not a constraint.

**jaci** — `de2609d` carved the `acra_dscr` scenario skeleton: 601 LOC, `AcraDSCRConductor` on `jazzx_sdk.pipelines.investigation_loop`, five modes, schemas, a two-tool mock registry, and the pack manifest. Built directly on the shared primitive rather than hand-rolled — the first of the six scenarios to do so.

## 2. Document set — corrected status

| # | Document | Status | Where it lives |
|---|---|---|---|
| **D1** | `Acra_DSCR_on_Platform_v2_Reuse_and_Build_Plan.md` | rev 2, code-verified. Two of its gap items now closed by `e777bbf` / `44f9b55` — needs a status pass | project + `jaci/docs/plans/` (referenced by the pack manifest) |
| **D2** | `plan_JAPES_POLICY_IR_AUTHORING_DEFECTS.md` | **P1, P2 DONE** (`44f9b55`). P3 (AllOf/AnyOf) open — decision gate. P4a, P4b open | japes |
| **D3** | `plan_JACI_ACRA_DSCR_SCENARIO.md` | **rev 2** — rewritten against `de2609d`. Rev 1 withdrawn (written blind to the skeleton) | `jaci/docs/plans/` |
| **D4** | `acra_dscr_profile.yaml` — 99-cell grid, 5 tables | **authored and verified in sandbox; NOT on disk.** Placing it is D3 phase 0 | → `config/packs/acra_dscr_core/profiles/` |
| **D5** | `eligibility.yaml` — 19 rules | same | → `config/packs/acra_dscr_core/policies/` |
| **D6** | `test_acra_eligibility.py` — 17 cases + completeness | same (18/18 green against `44f9b55`'s predecessor state) | → `tests/scenarios/acra_dscr/` |
| **D7** | `ENCODING_NOTES.md` | same; §2 needs "fixed in `44f9b55`" annotations rather than deletion | → `config/packs/acra_dscr_core/` |
| **D8** | Six ABA worksheets + relay family | **not written** — blocked on G3 | project docs |
| **D9** | Certified Client Overlay | **not written** | project docs |

**Reading the status column:** *verified* means the artifact was executed against the real evaluators and passed. *On disk* means it exists in a repo. D4–D7 are verified and not on disk. Rev 1 collapsed those two into one word, which is the error that prompted this revision.

## 3. The architecture question — settled, and it was not a fork

Rev 1's D3 proposed a standalone deterministic evaluation loop; the skeleton built an LLM mode loop. These read as competing architectures. They are two layers, and the resolution is composition, not selection.

**The eligibility grid is arithmetic, not judgment** — 99 numeric cells, band lookups, fail-closed comparisons. Running it through modes makes a deterministic answer nondeterministic, spends a model call per evaluation, and breaks the citation chain that is the whole answer to Acra's over-conditioning problem. **And a pure rule loop cannot do what modes are for**: cross-document discrepancy detection, entity and title review, evidence sufficiency, narrative.

So: **deterministic pre-loop step + registered tool; modes for judgment; Governor enforces the deterministic verdicts.** Precedent in the platform's own decisions — computed rows deterministic via the expression DSL and never model-inferred (the RB/Mesa Verde invariants), and "deterministic pre-pass before any model call" as the recorded `TemplateFillAgent` build order.

**Nothing in the skeleton needs undoing.** The skeleton's own docstring already defers "the policy corpus (MatrixCondition-based eligibility grid)" as separate work — D4/D5 *are* that corpus. Full detail in D3 rev 2 §1.

## 4. Track A — japes

| Step | Item | Status |
|---|---|---|
| A1 | `RatioCondition.direction` narrowing | **done** `44f9b55` |
| A2 | `Expression` cast only for ordering operators | **done** `44f9b55` |
| A3 | Render matrix violations | **open.** Narrower than D2 states it: `_condition_label` already renders correctly because `MatrixEvaluator.evidence_contract()` returns non-empty fields. Only `_describe_condition` (the "what was required" side) falls through to the bare kind string, plus `policy_registry.py`'s legacy shim — which omits `natural_language` too, by design. So the fix is one function, and the shim may be correct to leave alone |
| A4 | `AllOf` / `AnyOf` composite applicability | **open — decision gate G1.** The evaluator is easy; trace composition is not. An underwriter must see *which* limb failed, or the audit trail degrades to "composite violated." Settle verdict algebra (INDETERMINATE dominates SATISFIED in `AllOf`) and `evidence_contract()` union semantics before code |
| A5 | Policy-literal vs `profile.custom` drift lint | open, small |

**Regression bar:** `test_condition_evaluator.py`, `test_default_policy_expert.py`, and — once landed — D6.

## 5. Track B — jaci

Carried by **D3 rev 2**. Phase 0 has no dependencies.

| Step | Item | Depends |
|---|---|---|
| B0 | Place D4–D7; point the manifest at them; **un-scar the four `in`-list workarounds and the `0.9999` inversion now that A1/A2 landed** | — |
| B1 | Context adapter (7 field mismatches, 5 missing fields), citations on `LoanCondition`, `cases.py` fixtures | B0 |
| B2 | Evaluation step, **cap composition**, tool registration, Governor gate, real prompts | B1 |
| B3 | `SCENARIOS` entry, demo page, gold cases | B2 |
| B4 | Appraisal-driven LTV/CLTV | **G2** |

B2's cap composition is the only step with genuine design content; the rest is binding.

## 6. Track C — governance

Unchanged from rev 1 and still blocked at the front: **G3** (`InteractiveAgentSpec` vs `AssistantManifest`, open since 2026-08-03) gates C1. Six worksheets authored against the wrong artifact is six worksheets to redo.

C1 first pass = six archetypes × four load-bearing ABA sections (§3 scope, §4.3 action classes, §7.2 authority matrix, §8.2 handoffs). Fixed decisions to carry into all six: `human_only` = the credit decision and any adverse action; Byte write-back is `reversible` + `mandatory_trace_event`; external communication disallowed unless expressly exposed; autonomy proposals from CRE §8 percentages as ceilings subject to §10.6 gates, never as go-live postures.

C2 (Certified Client Overlay) is where D4/D5 legally belong — Acra's numbers in the overlay, not the pack, per ABA §11.1.

## 7. Decision gates

| Gate | Question | Blocks | Recommendation |
|---|---|---|---|
| **G1** | Fund `AllOf`/`AnyOf`, or accept a state axis (~50× cells) / DSL applicability? | A4, prepay family + FL modifiers | **Build it** — registry is open, `MatrixCondition` proved the path; both alternatives destroy reviewability |
| **G2** | Who funds the LTV calculator? | B4, deck credibility | **Move it forward.** It is the primary axis of all 99 cells; a book proxy is not a number an underwriter accepts |
| **G3** | `InteractiveAgentSpec` vs `AssistantManifest` | C1 | Needs a name against it |
| **G4** | Acra sequencing vs YETI | staffing | Acra consumes what YETI hardens — say so explicitly |
| **G5** | Byte condition webhooks / two-way sync at Acra's plan tier? | deck Phase 2 | Ask Acra now; it is question 1 on their own slide 26 |

## 8. Handoff — rev 2

1. **jaci session:** "Execute `plan_JACI_ACRA_DSCR_SCENARIO.md` rev 2, phase 0. The four artifacts are attached. A1/A2 landed in japes `44f9b55`, so also un-scar the workarounds in `ENCODING_NOTES.md` §2 and confirm 18/18 still green. Stop and report."
2. **jaci session, continue:** "Phases 1–2. Phase 1.1's field-mismatch table is concrete — write the every-field-resolves test first. Phase 2.2 cap composition is design-bearing: propose the composed-result shape before implementing."
3. **japes session:** "D2 A3 only — and note the finding that `_condition_label` already works; it is `_describe_condition` that needs the fix. A4 needs a recommendation on trace composition before any code."
4. **jaci session:** "Phase 3, minus 3.4 pending G2."
5. **Human, not a session:** G3, then C1.

**Standing constraints:**

- Don't fold into `cre_underwriting` (D3 §1 rev 1 reasoning still holds: no pack manifest, 16 Mesa Verde references, `insurance_diligence` precedent).
- Don't imitate `cl_of_core` / `cl_sp_core` — draft scaffolds, no consumer, `governance_chain: DEFERRED`. Only the `depends_on` fragment pattern is worth copying.
- Don't reorder `MatrixCondition.axes` on an authored table — cell keys are `|`-joined in axis order; reordering silently invalidates all 99.
- Grid verdicts are given, not inferred. No mode re-derives a cell.
- Synthetic loan data only.
- **Re-verify before executing.** Both repos moved twice during the authoring of these documents. Any plan more than a day old should have its baseline commit checked first — this revision exists because that did not happen.

## 9. What "done" means for this phase

1. An Acra underwriter picks a loan in the demo and sees the grid resolve the way they would resolve it by hand off the DSCR Program Summary PDF — boundary cases and ineligible cells included.
2. Every condition cites the directive it failed; conditions that cannot cite one are not constructible.
3. When two caps bind, the composed result names which one bound and why.
4. Deterministic findings and model judgment are visually distinguishable.
5. The whole thing survives an IR change without silent drift, because D6 runs against it.
