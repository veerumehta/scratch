# `jazzx-eval-scorers`: the scorers, without the SDK

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-30, building on `v2.6.0`. Decided by the user: pulled into 2.6.0, ahead of
the eval-service PR (option B in the step-7 discussion).

## Why

eval-service cannot take `japes` as a dependency: Python 3.11 vs >=3.12, `cryptography ^49` vs
`>=50`, both ship a top-level `common`, japes' path dependencies do not resolve for a git consumer,
and `import jazzx_sdk.evaluation.scorers` loads ~1,900 modules. Its scorer set is also richer than
the SDK's. A light distribution beside `jazzx_eval_contracts/` and `jazzx_plato_client/` fixes the
dependency and is where its primitives land.

## Shape

- `jazzx_eval_scorers/` (`jazzx-eval-scorers` 0.1.0): pydantic only, `python >=3.11`; extra
  `schema` for `jsonschema`. No `jazzx_sdk`, no `common`.
- Moves from the SDK: `scorers.py` (ScorerResult, Scorer, FunctionScorer, CompositeScorer,
  AdjudicatorScorer, policies, ScorerRegistry, ScorerSpec/build_composite, ScorerInfo) and
  `metrics.py`. The two SDK helpers they used are restated in the package (`call_maybe_async`
  semantics, a frozen-able name registry).
- The LLM judge takes an injected `judge(prompt) -> verdict` coroutine; the SDK's
  `LLMJudgeScorer(llm, ...)` and the `llm_judge` policy bind `structured_call` to it.
- New primitives from eval-service, reshaped to the `Scorer` protocol (config in the constructor,
  overridable from the score context as `ScorerSpec.params` does): `RegexScorer`,
  `ContainsScorer`, `SchemaComplianceScorer`, `ArrayScorer` with `EquivalenceRule`.
- SDK modules become re-exports; nothing that imports `jazzx_sdk.evaluation` breaks.
- Not moved: trajectory and operational scorers (need `CanonicalTrace`), QA and custom scorers.

## Then

eval-service PR: depend on `jazzx-eval-scorers` (git subdirectory) and swap its primitives,
starting with the exact/close ones; its MLflow judges and agent judge stay its own.
