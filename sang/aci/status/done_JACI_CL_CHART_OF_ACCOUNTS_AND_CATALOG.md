# Done: Chart of Accounts and Metric Catalog as Pack Assets

Author: Virendra Mehta · Completed 2026-07-27
Repo: jaci · Landed: dev commits `27fa28e` (Phases 1-2), `93ca1ff` (Phase 3), `ab48022` (Phase 4)
+ japes dev `477f877` (`MetricDefinition.display_method`, cross-repo dependency)
Plan: docs/plans/plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md (superseded by this file)

All 4 phases landed. One correction to the plan's own premise, found during authoring; one
mid-flight fix to japes's `LineVocabulary` validator, found the same way.

## What shipped

- `config/packs/ci-spread-core/chart_of_accounts.yaml`: the single C&I chart of accounts (64
  entries), in the japes `LineVocabulary` schema — collapsing four separately-drifting alias
  copies (`dsl_catalog._CANDIDATES`, `spread_template.yaml`/`template.py`'s accepts/locator tuples
  — one copy in two forms — and a fourth this plan's own investigation found:
  `analytics.py`'s own inline candidate lists inside `compute_metrics()`, which the written plan's
  grounding notes didn't name). Classification follows PRD Appendix A verbatim, only where it
  calls out an explicit GAAP deviation.
- `analytics._vals`/`_vals_traced` resolve through the vocabulary (statement-scoped first,
  unscoped fallback for a concept that genuinely repeats across statements, e.g. `net_income`);
  `_vals_traced` reports the resolver's real `MatchKind` instead of an inferred bucket.
  `compute_cre_metrics` (CRE/REIT, explicitly out of scope) preserved on `_vals_legacy`, untouched.
  `spread_template.yaml`'s per-row `accepts` lists and `template.py`'s locator tuples both collapse
  to a single canonical key per row.
- `config/packs/ci-spread-core/metrics.yaml`: the 11 C&I metric definitions as pack data, loaded
  by `metrics_catalog.py` (`METRIC_CATALOG`/`METRIC_ORDER`). Execution order derived from the
  `CUSTOM_METRIC` binding graph, not hand-maintained; a circular reference fails to load via
  `jazzx_sdk.expressions.validate`. `dsl_catalog.py`'s `_DEFINITIONS`/`_ORDER`/`_METHOD` deleted in
  favor of the loaded catalog + the new `MetricDefinition.display_method` field (japes).
- `render_chart_of_accounts_and_metrics()` on `ci_spread`'s 🎯 Target Template tab: both pack
  YAMLs, raw-viewable, reading live from the loaded vocabulary/catalog.

## Correction to the plan's own premise

The plan named three alias copies; a fourth, real one existed and wasn't named:
`analytics.py`'s own inline candidate lists inside `compute_metrics()` (used by the legacy
float-based Streamlit-view path, separate from `dsl_catalog.py`). On inspection these weren't
semantically conflicting with the other copies — generally more complete, not contradictory — so
the union still worked, but the real key inventory was larger than estimated. Documented in the
chart_of_accounts.yaml header and the Phase 2 commit.

## Mid-flight fix to japes (found empirically, not anticipated)

While authoring the real chart of accounts, found that the same raw term legitimately means
different things in different statements (`accounts_receivable` as a balance-sheet balance vs. a
cash-flow change-in-AR line) — but `LineVocabulary`'s Phase-1 duplicate-alias validator (from
`plan_JAPES_2_2_0_LINE_VOCABULARY.md`, landed the same day) enforced global uniqueness, which
would have wrongly rejected this as an authoring mistake. Fixed in japes (commit `2401b90`,
before this plan's own Phase 1 could even load): alias uniqueness is now scoped per statement
type; canonical keys stay globally unique (`by_key()` has no statement type to disambiguate).
`analytics._vals`'s statement-scoped-then-unscoped two-tier resolve() (Phase 2) is the consumer-
side half of this same fix.

## Acceptance criteria — verified

- Phase 1: vocabulary loads, no duplicate aliases; every key referenced by all four historical
  copies resolves to exactly one entry (7 coverage tests, `test_chart_of_accounts.py`).
- Phase 2: full jaci suite passes (same 7 pre-existing unrelated failures — one of which,
  `test_insurance_cert_policy`'s arrow test, turned out to just need `streamlit` installed in this
  venv, a pre-existing gap unrelated to this work, fixed as a side effect); the sixteen-case
  `dsl_catalog` parity fixture still passes; `template_csv_text` for a representative 64-row
  fixture is byte-identical to a baseline captured before the change. Three rows needed a narrow,
  empirically-justified opt-in `allow_substring` (found via that exact diff, not guessed) to
  preserve output — documented inline in the YAML, per the user's explicit "tighten, accept the
  risk" decision on this exact tradeoff.
- Phase 3: YAML-loaded catalog computes identically to the retired `_DEFINITIONS`; a twelfth
  metric added to a fixture catalog computes correctly with no Python change (both as tests).
- Phase 4: a line/metric added to either pack YAML appears with no code change, verified against
  the loader mechanism directly. The Streamlit page itself boots without import/runtime errors
  (confirmed by starting the dev server); the rendered tab was **not** visually confirmed in a
  browser — no browser tool was available in this environment. Flagging this honestly rather than
  claiming full UI verification.

## Notes for next time

- The reclassification/break-out engine (FR-MAP-3/4), many-to-one rollups, per-case fixture
  crosswalks (`_CURATED_BS`/`_CURATED_METRIC` retirement), and any CRE pack vocabulary all remain
  explicitly out of scope, as the plan said.
- If someone gets hands-on time with the actual rendered Streamlit tab, worth a quick look to
  confirm the two new expanders read well next to the existing template-row table.
