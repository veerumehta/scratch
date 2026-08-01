# Done: Expression DSL and Metric Definition Schema

Author: Virendra Mehta · Completed 2026-07-26
Repo: japes (Phases 1-5) + jaci (Phase 6, cross-repo) · Landed: japes 2.2.0 (dev, commit
`ce169d6`, squashed), jaci dev commit `3ba2e17`
Plan: docs/plans/plan_JAPES_2_2_0_EXPRESSION_DSL.md (superseded by this file)

All 6 phases landed. One deviation from the written plan, in Phase 6 — see below.

## What shipped

- `jazzx_sdk/expressions/definition.py`: `MetricDefinition`, `InputBinding`, `BindingKind`
  (assumptions are a distinct kind per FR-CUS-6), `MetricTestCase`, `PeriodBasis`, `Polarity`,
  `ApprovalStatus`.
- `jazzx_sdk/expressions/parse.py`: hand-written recursive-descent parser (not `eval()`) —
  arithmetic, `prior`/`ltm`/`avg`/`cagr` (multi-period), `if`/`min`/`max`/`cap`, an explicit
  aggregation-function stub for cross-entity references.
- `jazzx_sdk/expressions/evaluate.py`: `evaluate()` — governed `MetricResult` with full
  derivation/provenance and weakest-input confidence; typed `Refusal`s (never `None`/silent-zero)
  for a missing input, below-floor confidence, or division by zero. Also
  `evaluate_over_namespace()` — a separate, lightweight evaluator over a flat `{field: value}`
  dict for the Phase 5 policy-condition use case.
- `jazzx_sdk/expressions/validate.py`: `validate()` — undefined references, unit mismatches,
  unreachable conditional branches, circular metric references (DFS).
- Phase 5: `jazzx_sdk.fabric.canonical.policy.DslExpression`; `Rule.condition` widened to
  `Optional[Union[Expression, DslExpression]]`; `DefaultPolicyExpert.check_compliance()` and
  `PolicyRegistry`'s backward-compat clause shim (`_build_clauses_shim()`) both fixed to branch
  on the condition's type (found and fixed **two** sites, confirmed via repo-wide grep there
  wasn't a third).
- Phase 6 (jaci): `jaci/capabilities/commercial_lending/dsl_catalog.py` — the C&I metric catalog
  (EBITDA, free cash flow, funded debt, 3 margins, EBITDA margin, current ratio, debt-to-equity,
  leverage, revenue growth) re-expressed as `MetricDefinition`s, wired in behind
  `compute_metric_results(..., use_dsl=True)` (default stays the legacy Decimal path for one
  release).
- ~60 new tests across `tests/test_expressions_*.py` (japes) + `tests/unit/test_metric_result.py`
  parametrized over both paths (jaci).

## Acceptance criteria — verified

- Phase 2/3: the real PRD Appendix B (Adjusted Fixed Charge Coverage) parses and evaluates to
  `6.67` exactly, deriving from its multi-step numerator/denominator; FR-ADJ-4 (conditional
  bad-debt addback, lazy branch evaluation) and FR-ADJ-6 (owner-comp capped at policy limit) both
  covered by name.
- Phase 4: a deliberately circular pair of definitions fails validation naming both.
- Phase 5: every existing policy in jaci's AML, KYC, and C&I registries loads and evaluates
  identically — confirmed by installing japes 2.2.0 into jaci's venv and running jaci's **full**
  test suite (only 7 pre-existing, unrelated failures: an Anthropic-reasoner call-signature
  mismatch, a naive/aware-datetime bug in `jazzx_sdk/automation/schemas.py`, and a missing
  `streamlit` module in the venv — none touch `Policy`/`Rule`/canonical objects). One new C&I
  rule expressed in the DSL (`leverage_x <= 3.5 OR covenant_waived == 1`) evaluates against a
  fixture in `tests/test_default_policy_expert.py`.

## Deviation from the plan — Phase 6's "gold cases"

The plan's Phase 6 acceptance criterion says: *"the ported catalog produces values identical to
the Python implementation across all five C&I gold cases, asserted as a test rather than
sampled."* No such gold-case corpus exists for `compute_metric_results` specifically — it's
checked at the time the plan was authored, before this session actually located the function. The
real state of the repo:

- `compute_metric_results` (the governed, Decimal-exact `metric_result.py` path this plan targets)
  is exercised by exactly **one** synthetic fixture, in `tests/unit/test_metric_result.py` — it
  isn't wired into any live scenario yet.
- jaci's actual "C&I gold cases" (`tests/eval/gold_cases/ci/case_01_yeti.json`,
  `tests/fixtures/golden_cases/ci_spread/yeti_abl.json`, MAA) belong to a *different* code path
  (`ci_spread/credit_outcome.py::yeti_credit_outcome`), which reads pre-computed ratios straight
  out of `yeti_financials.json` — it never calls `compute_metric_results` or `analytics.py` at
  all, so there is nothing there to port or verify against.

Given that, Phase 6 was verified the honest way available: `test_metric_result.py`'s existing
8 tests were parametrized over `use_dsl=[False, True]` (16 cases total, all passing) — proving the
DSL path byte-identical to the legacy path on the one fixture that actually exercises this
function. If a real multi-case C&I gold corpus for `compute_metric_results` gets built later,
re-run this same parametrization against it.

## Notes for next time

- FR-CUS-9 (governance/scoping of metrics across institution/product/deal) and FR-CUS-11
  (natural-language metric assist) remain explicitly out of scope, as the plan said.
- `jazzx_sdk.expressions`'s cross-entity aggregation functions (`sum_entities` etc.) are parsed
  but refuse at evaluation time — no multi-entity `ResolutionContext` exists yet.
