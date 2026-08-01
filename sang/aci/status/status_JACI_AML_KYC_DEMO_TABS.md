# JACI - AML & KYC-Anthropic Demo Tabs

**Author:** Veeru
**Branch:** dev (jaci repo)
**Status:** ✅ Shipped — this doc is a retrospective record of the design, not a pending plan.

---

## Why this matters

AML and KYC-Anthropic were JACI's earliest two scenarios. Every later scenario (ci_spread,
cre_underwriting, insurance_diligence, portfolio_monitoring, clinical_intake) got a polished,
interactive single-case "Demo" tab; AML and KYC-Anthropic never did — they only had a Dashboard
(eval/analytics) tab. `app.py` only renders a Demo tab `if scenario.has_demo` (i.e. `ui/registry.py`
sets a `demo_target`), so selecting "AML" or "KYC-Anthropic" showed Concepts → Dashboard only, with
no way to run a single case interactively and watch the conductor work. Both scenarios already had
working conductors, gold-case fleets, and mock tool registries — the gap was purely a missing UI
module + one registry entry each, not missing platform capability.

Goal: bring AML and KYC-Anthropic up to the same demo standard as the later scenarios, so a user can
pick a gold case, run the real conductor loop live (real LLM calls, mocked evidence tools), and see
the resulting decision.

## Verified facts grounding this design

- **Routing**: `app.py:117-131` adds a Demo tab only if `scenario.has_demo` (`ui/registry.py`
  `demo_target` set). Both scenarios already had `dashboard_target` and `pipeline_target`
  (`AML_PIPELINE`, `KYC_PIPELINE`) wired — only `demo_target` needed adding.
- **No shared demo-scaffolding module exists.** Every `demo_page.py` in this repo is bespoke,
  following a loose convention (case-picker via `st.sidebar.radio` + `st.button` → `st.spinner` →
  `st.session_state[...]` → `st.rerun()` → render from session_state). `cre_underwriting/ui/demo_page.py`
  was the closest structural template (dashboard+demo coexist, similar size); `ci_spread/ui/demo_page.py`
  (`~490-620`) was the template for the actual async-conductor-invocation idiom.
- **Conductor entry points** (verified against source, both take `**kwargs` straight into
  `__init__`, no `fabric` param needed — unlike ci_spread):
  - `src/jaci/scenarios/aml/conductor.py:545` — `async def run_investigation(alert: AlertTrigger, **kwargs) -> CaseFile`
  - `src/jaci/scenarios/kyc_anthropic/conductor.py:365` — `async def run_review(trigger: ReviewTrigger, **kwargs) -> ReviewFile`
  - Both conductors default `tool_registry` to mocks internally (`tool_registry or ToolRegistry(use_mocks=True)` /
    `... or KYCToolRegistry(use_mocks=True)`) if not passed, so the demo can pass one explicitly for
    clarity or rely on the default — either works.
- **AML mock tools are case-fixture-routed; this matters.** `tests/fixtures/case_fixtures.py:FIXTURES`
  is keyed by `"case_01"`..`"case_11"` (matches `case_id` in each `trigger.json` exactly).
  `tests/fixtures/test_context.py` exposes `set_active_case_id(case_id)` / `clear_active_case_id()`.
  The AML demo must call these around the conductor run, or every case gets generic placeholder
  evidence instead of its real structuring/PEP/layering pattern.
- **KYC mock tools are not case-routed** — `kyc/tools/kyc_mock_connectors.py` (reused by
  `kyc_anthropic`) returns templated data from query params alone. This is an existing limitation of
  the eval harness itself (`tests/eval/run_kyc_eval.py` runs the same way), not something the demo
  fixes — called out honestly in the demo's Overview tab, same as `cre_underwriting`'s Trace tab
  calls out its own stubs.
- **Gold-case fleets** are directory-per-case (not the flat-file layout ci_spread/cre use):
  - AML: `tests/eval/gold_cases/aml/case_01..case_11/trigger.json` (11 cases). Top-level keys:
    `case_id, label, typology, description, difficulty, expected_outcome, expected_loop, alert`.
    `alert` maps onto `AlertTrigger` (`src/jaci/scenarios/aml/schemas/case_context.py:48`) but
    `alert_timestamp` is a `"...Z"` string needing `datetime.fromisoformat(ts.replace("Z", "+00:00"))`
    before `AlertTrigger.model_validate(...)` — exactly as `tests/eval/run_eval.py:293-297` does it.
  - KYC-Anthropic: `tests/eval/gold_cases/kyc_anthropic/case_01..case_10/{trigger.json, evidence.json,
    README.md, documents/}` (10 cases). Top-level keys of `trigger.json`: `review_trigger,
    customer_profile, expected_outcome`. `ReviewTrigger(**gold_case["review_trigger"])` works directly,
    no timestamp preprocessing needed.
  - `ui/common/data_loaders.py::load_gold_cases()` is dead code for this shape (globs `*.json` against
    these now-directory-based folders, silently returns nothing) — not used; each new `demo_page.py`
    has its own small module-local loader, mirroring `tests/eval/run_eval.py:55-68`'s directory-walk.
- **Runtime ctx**: no fabric needed. Built via `jazzx_sdk.ui.get_client_context()` (falls back to
  `SimpleNamespace(runtime=ClientLayer())` if that helper isn't present in the installed SDK version) —
  same mechanism ci_spread's `_build_runtime_ctx()` uses, minus its provider-key-picker specifics
  (AML/KYC use fixed model tiers, not a switchable `_llm.py`).
- **Schemas** (field names verified against source, used for result rendering):
  - AML `CaseFile`: `.case_context` (`.evidence`, `.hypotheses`, `.iteration_count`, `.loop_status`),
    `.disposition` (`.recommendation` enum close/escalate, `.confidence`, `.rationale`,
    `.confirmed_typology`, `.policy_clauses_cited`), `.governor_decision` (`.approved`,
    `.blocking_reason`, `.required_actions`, `.policy_violations`), `.sar_draft` (optional).
  - KYC `ReviewFile`: `.review_context` (`.iteration_count`, `.hypotheses`, `.evidence`),
    `.recommendation` (`.risk_rating`, `.disposition`, `.confidence`, `.rationale`,
    `.missing_documents`, `.escalation_reasons`, `.screening_hits`), `.governor_decision`
    (same 4 attrs as AML's), `.narrative`.
- **`_conductor_graph(pipeline, ...)`** (`ui/concepts_view.py:106`) is reused directly for a Trace
  tab against the already-registered `AML_PIPELINE` / `KYC_PIPELINE`.

## What was built

### `src/jaci/scenarios/aml/ui/demo_page.py` (new)

`render_demo_page(scenario: str)` — guards on `scenario == "AML"` (bails with `st.info(...)`
otherwise, matching the stale-label pattern other dashboard+demo scenarios use). Structure:
- Module-local `_load_aml_cases()` — walks `tests/eval/gold_cases/aml/case_*/trigger.json`.
- `_build_runtime_ctx()` — `get_client_context()` with the `ClientLayer` fallback.
- `async def _run_investigation_async(case)` — builds `AlertTrigger` (with the timestamp fix), calls
  `set_active_case_id(case["case_id"])`, runs `run_investigation(alert, ctx=..., tool_registry=ToolRegistry(use_mocks=True))`
  inside try/except (catches into `{"case_file": None, "error": traceback.format_exc()}`), always
  `clear_active_case_id()` in `finally`.
- `_run_conductor(case)` — sync `asyncio.run(...)` wrapper for Streamlit.
- `_render_result(result, case)` — recommendation badge, confidence/iteration/evidence-count metrics,
  expected-vs-actual comparison caption, expanders for rationale, governor decision, hypotheses table,
  evidence table, SAR draft (if present).
- `render_demo_page`: `st.sidebar.radio` case picker over `{case_id — alert_type (label)}` →
  `st.tabs(["🏠 Overview", "▶ Investigation", "🔗 Trace"])`. Overview explains the loop and the
  fixture-routing behavior. Investigation tab shows the raw alert, a "▶ Run investigation" button
  (session-state keyed per case_id so switching cases doesn't show stale results), and the rendered
  result. Trace tab shows `_conductor_graph(AML_PIPELINE)` plus a pointer back to the Investigation
  tab for this run's step outcomes.

### `src/jaci/scenarios/kyc_anthropic/ui/demo_page.py` (new)

Same shape, scoped to KYC:
- Guards on `scenario == "KYC-Anthropic"`.
- `_load_kyc_cases()` walks `tests/eval/gold_cases/kyc_anthropic/case_*/trigger.json`, stamping
  `_case_id` from the directory name onto each loaded dict.
- `_run_review_async(case)` builds `ReviewTrigger(**case["review_trigger"])`, calls
  `run_review(trigger, ctx=..., tool_registry=KYCToolRegistry(use_mocks=True))` — no active-case-id
  routing (KYC mocks don't support it; Overview tab says so plainly).
- `_render_result` shows disposition badge, risk rating/confidence/iteration metrics, expected-vs-actual
  caption, rationale/escalation-reasons/missing-docs expander, governor decision expander, screening
  hits table, narrative expander (EDD escalations).
- Same tab layout (Overview / ▶ Review / 🔗 Trace using `KYC_PIPELINE`).

### `ui/registry.py`

Added one `demo_target=` line to each existing `Scenario(...)` entry (kyc_anthropic and aml):
```python
demo_target=("jaci.scenarios.kyc_anthropic.ui.demo_page", "render_demo_page"),
demo_target=("jaci.scenarios.aml.ui.demo_page", "render_demo_page"),
```

### `src/jaci/scenarios/aml/ui/__init__.py` and `src/jaci/scenarios/kyc_anthropic/ui/__init__.py`

Exported `render_demo_page` alongside the existing dashboard `render`, for parity with
`cre_underwriting/ui/__init__.py`'s convention.

## Verification performed

1. **Loader + trigger-construction smoke test** (no LLM calls): both loaders run and every case's
   trigger builds successfully (11 AML cases, 10 KYC cases).
2. **Real end-to-end conductor run** (live LLM) on a first gold case per scenario — this surfaced a
   real, pre-existing platform bug (see below), fixed separately in japes.
3. **`streamlit run app.py` click-through**: AML and KYC-Anthropic both show a new Demo tab between
   Concepts and Dashboard; case picker, run button, and result rendering all confirmed working; the
   Trace tab's pipeline diagram renders for both.

## Follow-on finding (fixed in japes, not this repo)

The AML live-run smoke test exposed a real bug one layer down: `AMLConductor` wires japes's generic
operational modes (`InvestigatorMode`/`ReasonerMode`/`GovernorMode`/`Sentinel`) directly, but AML's
own `EvidenceObject` schema used domain field names (`verifier_status`, `source_system`, `content`,
`retrieved_at`) instead of the generic `Evidence` schema's names (`status`, `source`, `data`,
`timestamp`, `quality_score`) those modes expect — every investigation degraded to a fallback
"close, confidence 0.3" result instead of a real analysis. Fixed in japes by adding read-only
compatibility-alias properties on `EvidenceObject` (`jazzx_sdk` side, not jaci) — no jaci changes
needed once the japes pin picks it up.
