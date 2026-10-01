# Formal policy evaluation as a Verifier asset

Status: design note, 2026-09-26. Input: `docs/plans/learning/Formal Policy Evaluation — Architecture
Proposal.pptx.pdf` and PR #78 (Sourav, `formal`, being cut to Z3 only). Prior art: IIF v1.5
migration guide (`status/done_IIF_v1_5_Migration_Guide.md`: Verifier D56/D57), reasoning substrate
note (`status/done_design_note_reasoning_substrate.md`: VerifierMode migration).

## The claim

The proposal calls formal checking "a first-class evaluation type". In the cognitive-mode model it is
first a **Verifier** act (TRUST category) and only second a scorer. A solver attesting that a claim
holds over frozen evidence, or returning the case that breaks it, is what the Verifier does; the
eval scorer is a projection of that attestation, not the other way round.

## Mapping

| Proposal / PR #78 | Verifier model (exists today) |
|---|---|
| pass / fail / cannot_determine / error | `AttestationVerdict` PASS / FAIL / INDETERMINATE (+ PARTIAL), IIF D56. `cannot_determine` and `error` both map to INDETERMINATE; the four-state detail rides along. |
| "missing evidence returns Unknown, never Pass" | Same rule as `PythonEvaluator`'s withhold (not activated withholds an allow) and Verifier INDETERMINATE. One rule, three places: state it once. |
| `EngineRegistry` of adapters (`smt.z3`, ...) | The Verifier's **Verification Asset Registry** (IIF D57). Z3 is one asset; the LLM `VerifierMode` check (`method="source_integrity_check"`) is another; a python check is a third. Use `NamedRegistry`, per the PR note. |
| `FormalResult` | `Attestation` (`fabric/canonical/evidence.py`): `verdict`, `verifier_id`, `method=engine_id`, `checks_performed=[claim_id]`, `findings`. Missing: a structured witness (the counterexample). Today it would be flattened into `findings`. |
| `FormalReport` | `VerifierReport` (`modes/schemas.py`): per-id results, attestations, counts. |
| "the failed clause and the case that breaks it" | `Attestation.findings` plus witness, linked to the rule id the claim formalizes (`PythonCondition.derived_from` already models that link for python rules). |
| scorer / eval-service verdict | Projection: Attestation -> `ScorerResult` (PASS -> passed, FAIL -> failed, INDETERMINATE -> skipped) -> `ScorerVerdictV1` via the existing `scorer_result_to_verdict_v1`. |

## Where it plugs in

1. **Verifier mode.** `VerifierMode` is LLM-only (`kind=AGENT`, `has_tools=False`). Formal
   verification is deterministic. Either the mode contract allows deterministic assets (the
   Sentinel precedent: "can be pure Python or LLM-assisted"), or a deterministic verifier sits
   beside it producing the same `Attestation`. The investigation loop's `verifier` step and
   `on_mode_result` then carry formal attestations with no new plumbing.
2. **Policy conditions.** A `smt` condition kind registered with `register_condition_evaluator`,
   beside `python`, is the proposal's "approved policy to executable rule" proof case: the rule's
   verdict is SATISFIED / VIOLATED / INDETERMINATE with the existing not-activated semantics.
3. **Isolation.** Same seam as python rules and scorers: the host's executor. `LocalPythonExecutor`
   (2.5.6) runs `python -I -S`, which drops site-packages, so it cannot import `z3`. A formal asset
   needs either its own child (as PR #78's Plato worker does) or an executor variant without `-S`.
   Decide once, for all three kinds of untrusted/heavy check.
4. **Eval and eval-service.** Unchanged from the PR note: the scorer projection gives eval-service
   `ScorerVerdictV1`; eval-service freezes the facts and owns history (the proposal's split).

## Consequence for PR #78

The note sent to Sourav asks for a `FormalScorer`. Under this framing the primary output should be
an `Attestation` (per claim) with the scorer derived from it. Cheap to ask now, expensive after
merge. Open: whether `Attestation` gains a `witness` field (canonical schema change, cross-repo
via eval contracts) or the counterexample stays in `findings` / metadata for V1.

## V1 proof case fit

VP2 financial spreading is the live one: "Spread S-77 was promoted carrying an unapproved EBITDA
adjustment" is a FAIL attestation on `spread.promotion_gate` over the spread's trace, with the
promotion event as the witness. MACER fresh-run isolation and document admission are the same shape
over different evidence.
