# Plan — JAPES MLflow → canonical Trace bridge (macer/juno enablement #1)

## The invariant (governs every item in the macer→japes consolidation)

> **JAPES owns the execution *mechanism*, fully parameterized** (size_kb, max_turns, retries,
> continuation-tool *slot*, span→mode *mapping*, ontology *schema*).
> **The pack owns the *policy*** (prompts, output schemas, the tool set it injects, field-level
> conversion, the concrete ontology it registers).

Anywhere a "port to JAPES" would carry a domain opinion (a mortgage span→mode rule, a findings
category enum, a JTBD trim boundary), that opinion stays in the pack as an injected parameter or
registered data — not in platform code.

## #1 — MLflow → canonical Trace bridge

Closes the **Trace** leg of the canonical chain: macer/juno already instrument runs with MLflow
spans; this turns those spans into a `CanonicalTrace` so `Decision.trace_id` points at a real
Trace (alignment doc §2: "MLflow spans map directly to TraceStep; no new instrumentation").

### Components (this slice)
- `RunContext` — run identity handle (run_id, mlflow_client, experiment_id, run_name, output_dir).
- `safe_link_traces_to_run`, `safe_update_current_trace` — best-effort (survive MLflow buffer TTL).
- `log_artifact_with_retry` — exponential backoff for flaky artifact stores.
- **`spans_to_canonical_trace` / `span_to_trace_step`** — the core. `span_type → TraceStepMode`
  is an **injected mapping** (`mode_map`, with a neutral `DEFAULT_SPAN_MODE_MAP` + `default_mode`)
  — the seam that keeps this domain-clean. `actor`/`autonomy_level` are parameters too.
- `mlflow_run_to_canonical_trace(run_id, client, …)` — thin fetch-then-delegate (best-effort).

### The cut (what is NOT in this bridge)
- No mortgage/JTBD span semantics. The mapping of *which* macer section/span → which cognitive
  mode is the pack's `mode_map`, supplied at call time. The default map is generic and overridable.
- Cost/latency land on `ToolCall` (schema's home), not invented fields.

### Deferred (next slices)
- Run lifecycle (`create_run` / `terminate_with_metrics` + global metric roll-up).
- Decision/Evidence emit already started on macer `platform_v2`; CaseFile too.

## Sequencing
#1 (this) → then the **agents execution kit** (raw-JSON-schema output, generic session +
continuation loop, `@function_tool` re-export). Per the audit, macer's `InputFilter`/`strip_session`
are already generic (move wholesale, parameterized); the domain mass is the call-site
prompts/schemas + injected `continuation_tools` — those stay in the pack.
