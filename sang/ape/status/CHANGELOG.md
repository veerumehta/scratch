# Changelog

All notable changes to JAPES (JazzX SDK) will be documented in this file.

## [Unreleased]

- **Two document-ingest gaps closed, found while reviewing real client documents against the
  pipeline.** (1) **`convert_document` gained `.pptx` support** — new `_pptx_to_markdown`
  (`python-pptx`, new optional `pptx` extra), one `## Slide N` section per slide, text frames and
  tables rendered in original shape (z-)order (no pandoc path: pandoc can write pptx but not read
  it). (2) **`split_document`'s page-classification fallback (used when a combined PDF has no
  outline/bookmarks) is no longer fully sequential.** It ran one `classify_document` LLM call per
  page in a plain loop — for a real multi-hundred-page combined loan-document package with no
  bookmarks, that's hundreds of sequential calls just to segment it before any extraction starts.
  Now dispatched via the existing `jazzx_sdk.conductor.fan_out` (order-preserving, bounded
  concurrency — same primitive `DocumentAgent.process_package`/`process_dir` already use for their
  own fan-outs). New `split_document(..., concurrency: int = 8)`, and
  `DocumentAgent.process_package`'s existing `concurrency` param now also bounds this pass, not
  just its own post-split per-segment fan-out. 5 new tests (`tests/test_split.py`,
  `tests/test_tools/test_conversion.py`). Full suite green (3115 passed, 3 skipped, no
  regressions).

- **Follow-on to the reasoning-summary streaming work above: closes the per-agent-attribution gap
  it explicitly left open, plus three more issues from the same external review.** (1)
  **Agent attribution.** `common.core.streaming.ReasoningEvent` gained `agent`/`agent_label`
  fields (bumped `common` submodule pin) — the gap really did need a schema change there
  (verified empirically before touching the submodule: constructing `ReasoningEvent(...,
  agent=...)` against the unmodified class silently dropped the kwarg, pydantic's default
  `extra="ignore"`). `publish_reasoning_delta` now takes `agent: str | None`; the top-level drain
  passes the parent agent's own `.name`, and each skill's `on_stream` closure passes
  `stream_event["agent"].name` — the OpenAI Agents SDK's own `AgentToolStreamEvent["agent"]`,
  the actual emitting sub-agent, not assumed to equal the parent. Degrades silently against an
  older pinned `common` (unrecognized constructor kwarg, same as `ReasoningEvent` itself being
  absent). (2) **Per-skill `Skill.stream_reasoning: bool | None`** — overrides the parent
  `InteractiveAgentSpec.stream_reasoning` for just that skill when set; `None` inherits
  unchanged. (3) **The streamed reasoning path now gets the same retry `run_with_recovery`
  already gives the non-streamed path** (`ModelBehaviorError` schema-validation retry,
  `IncompleteOutputError` truncation retry, `APIStatusError` backoff) — turning on
  `stream_reasoning` was silently trading this away, since `_respond_agentic` called
  `_run_streamed_once` directly instead of wrapping it. Only the context-window-fallback tier
  stays skipped (retries via forced session compaction, not meaningful mid-stream). (4) **New
  `StreamPublisher(event_transformer=...)` hook** — runs on every event immediately before
  publish (sync or async, via `concurrency.call_maybe_async`); return the event unchanged, a
  modified one, or `None` to suppress. Fail-closed on a transformer exception: suppresses rather
  than publishing the untransformed original, since a transformer may exist specifically to
  redact. Closes a real gap: japes published `ReasoningEvent`s straight to Redis with no
  interception point, so a consuming service couldn't humanize, redact, or gate reasoning content
  reaching a UI. 11 new/updated tests across `tests/test_sse_streaming.py` and
  `tests/test_interactive_agent.py`. Full suite green (3112 passed, 3 skipped, no regressions).

- **New `jazzx_sdk.authority.resolve_authority` — closes a real gap in the RBAC/authority survey:
  `fabric.canonical.policy.AuthMatrix`/`AuthorityEntry` (role, `action_scope`, threshold
  `ceiling`, `escalation_target`, `delegation_chain`) was schema only — nothing in the SDK
  actually walked it.** Distinct from `authority.resolver`'s `check_action`/`AuthorityMatrixV2`
  (autonomy *ceilings* — how much an AI decision can act without a human, across
  binding/overlay/profile layers): this resolves human **approval authority** — which role in a
  compliance-style delegation chain (an L1 investigator escalating to L2, then to a BSA officer)
  actually covers a decision's attributes, given the role attempting it. Walks
  `escalation_target` from the starting role until a `ceiling` covers the case or the chain
  refuses — numeric ceiling dimensions compare by magnitude; a non-numeric one (e.g. a
  categorical `risk_tier`) needs a caller-supplied rank (`tier_orders`) since the SDK can't know
  a domain's ordering, same discipline `authority.context.PermissionScope` already applies to its
  own opaque resource selectors — and fails **closed** (escalates) rather than guessing when it
  can't rank a value. Returns the resolving `AuthorityEntry` plus the `escalation_path` walked (an
  audit trail, not just yes/no) or a typed `Refusal` — reusing the existing `RefusalClass` taxonomy
  (`OUT_OF_SCOPE` for an unknown role/action, `AUTHORITY_EXCEEDED` when the chain dead-ends with
  nowhere left to escalate, `POLICY_CONFLICT_UNRESOLVED` for a matrix bug — an escalation cycle or
  a pathologically long chain), matching `check_action`'s own established return-shape convention
  exactly. 17 new tests (`test_authority_delegation.py`). Full suite green (3103 passed, 3
  skipped, no regressions).
- **Three findings from surveying `kernel`'s recent history for japes evolution opportunities,
  all built.** (1) `QueueProcessor.process_loop` no longer treats every dequeue error the same —
  `kernel`'s `common` submodule grew a permanent/transient distinction after a real incident
  (retrying a bad-credentials or missing-queue error forever at the same fixed poll cadence);
  japes' own queue processor didn't have this independent of whatever `common` has. New
  `dequeue_message` classification (via the already-existing `jazzx_sdk.failures.classify_failure`
  taxonomy — status-code 401/403/5xx already covered there; 404 checked directly since a missing
  queue is unambiguous, unlike `classify_failure`'s other, more general callers) sets
  `last_dequeue_error` and tracks a consecutive-error streak; `process_loop` backs off
  exponentially (`jazzx_sdk.concurrency.backoff_delay`, capped at 5 minutes) on any dequeue error
  instead of `poll_interval` — a genuinely empty queue is unaffected, byte-identical to before.
  (2) New `jazzx_sdk.failures.redact_for_zero_retention(value)` — the whole-value **substitution**
  counterpart to `redact_fields`/`redact_code_blocks`'s content-**scanning** redaction (those scrub
  known-sensitive substrings from a payload that's still stored; this is for a caller-declared
  policy — "do not persist this tool's args/response at all" — replacing the whole value
  regardless of content). `kernel` built a per-tool zero-data-retention flag doing exactly this;
  japes had the scan-and-scrub half of this family but not the substitution half. Deliberately just
  the mechanism, not a "which tools are ZDR" policy API — that's pack/service data japes doesn't
  own. (3) `DbStore.get_session()`'s docstring now warns explicitly against manually driving the
  generator outside a real DI framework's teardown guarantee — `kernel` just fixed the exact
  incident this enables in production (an early return abandoning the generator mid-yield, pool
  exhaustion since cleanup then only runs on GC): 47 files, 186 call sites. Japes' shape is
  identical; the context-manager alternative (`DbStore.session()`, already the documented default)
  was already correct, this closes the gap where the risky path wasn't warned against by name.
  34 new tests (`test_queue_processor.py`, `test_failures.py`, `test_fabric_db.py`). Full suite
  green (3086 passed, 3 skipped, no regressions).
- **New `jazzx_sdk.fabric.db.session_guard` — catch a DB session held open across a slow call
  ("transaction islands"), at the point of misuse instead of minutes later as a killed
  connection.** A DB session/transaction left open while awaiting an LLM call, a tool/sub-agent
  run, an MCP round trip, or an SSE yield ties up a connection (and, on Postgres, an open
  transaction) for however long that call takes — under
  `idle_in_transaction_session_timeout` the connection is killed out from under the caller,
  typically losing whatever the call produced with no clear error at the point that caused it. A
  subtle, load-dependent failure mode (SQLAlchemy autobegins a transaction on the first
  statement, not on session-open, so it's easy to write by accident) that's hard to reproduce
  outside production LLM latencies — surfaced by a real, well-evidenced incident in `juno`'s own
  history (its postmortem-driven fix there: an enforced three-phase
  prepare-with-db/run-without-db/finalize-with-fresh-db invariant). Checked `jazzx_sdk/fabric/db/`
  first — no equivalent guard existed, and japes' own `DbStore`/`SqlConversationStore` are the
  identical shape (a DB row read/written around a potentially long-running operation), so any
  pack using them today has the same latent exposure. New `assert_no_open_db_session(label)` —
  call immediately before the slow operation; raises `DbSessionHeldError` right there if a
  session is still open, turning a load-dependent production incident into an immediate,
  deterministic, testable failure. `DbStore.session()` and `SqlConversationStore`'s two session
  paths (`fabric.db`-backed and the raw-sessionmaker fallback) now track their own lifetime via
  `track_open_session()` automatically — no caller-side change needed for the assertion to see
  them; per-task via `contextvars` (concurrent tasks never see each other's open sessions) and
  nesting-safe. 10 new tests (`test_session_guard.py`, `test_fabric_db.py`,
  `test_fabric_conversation.py`). Full suite green (3077 passed, 3 skipped, no regressions).
- **New `jazzx_sdk.concurrency_guard.ConcurrencyGuard`** — a Redis `SET NX EX` lock keyed by a
  caller-extracted business key, wired as an optional `QueueProcessor(concurrency_guard=...)`
  param (mirrors how `idempotency_store` is already wired). Distinct problem from
  `automation.idempotency.IdempotencyStore`: that answers "have I already processed *this exact
  message*" (same message id, redelivery/retry dedup); this answers "is a run already in
  progress for *this business key*" — two genuinely different messages (a double-submit, a
  legitimate re-invocation) that both target the same downstream resource (a case, a loan, a
  conversation) can race even though neither is a redelivery of the other. Generalized from a
  design built for one caller's own hardcoded key (`loan_collection_id`, gated on a specific
  routing target) into a caller-parameterized primitive: `key_extractor(message) -> str | None`
  decides both which messages need guarding at all and what key identifies "the same resource"
  — the mechanism (owner-safe Lua-script release/extend so one worker can never touch another's
  lock, TTL matched to typical queue visibility timeouts, fail-open on a Redis error rather than
  stalling all queue processing on one dependency) is the platform's; the key policy is the
  caller's. Motivated by the same structural risk showing up anywhere a queue-driven, case-keyed
  conductor run exists — `AdjudicationAgent`-shaped scenarios included, not just the original's
  single caller. Checked the one live production consumer this generalizes from directly (its
  own worker code, not just the stale, never-merged design it came from) and found two follow-on
  gaps worth closing in the same pass, not deferred: (1) no backend existed for tests/single-
  worker dev without standing up real Redis — new `InProcessConcurrencyGuard` (an `asyncio.Lock`
  per key, explicitly documented as carrying no cross-process guarantee at all), with both
  implementations now formalized behind a `ConcurrencyGuardProtocol` `QueueProcessor` accepts,
  matching the `IdempotencyStore`-family Protocol convention already used elsewhere in this SDK.
  (2) The module docstring now explicitly warns against scoping `key_extractor` to a resource id
  alone (e.g. just a loan id) — two *unrelated* operations sharing a resource (an ad-hoc Q&A
  query and a scheduled job for the same loan) aren't duplicates and would be wrongly serialized;
  recommends `(resource, operation)` instead, matching what the original single-caller design
  was itself careful about (gated on a specific routing target, not the resource id alone) —
  care a naive generalization could otherwise have quietly dropped. 32 new tests
  (`test_concurrency_guard.py`, `test_queue_processor.py`). Full suite green (3067 passed, 3
  skipped, no regressions).
- **`DocumentAgentSpec.classify_max_chars`** — a per-agent override for `classify_document`'s
  text-sample cap, previously hardcoded at 8000 chars with no way for `DocumentAgent.classify()`
  to raise it. Prompted by a real report: a healthcare document misclassified even after adding a
  taxonomy class for it. Traced through the actual classify/extract contract to confirm two
  separate things: (1) `DocumentAgentSpec.taxonomy` is genuinely domain-builder-supplied (defaults
  to empty; `classify_document` raises if empty) — expected, not a bug; (2) extraction needs its
  own caller-supplied schema independent of the taxonomy (`DocumentAgent.process(schema=None)`
  skips extraction entirely) — a mismatched/generic schema there, not a japes bug, is the more
  likely explanation for a separately-reported extraction-mislabeling case. But classification
  itself had a real, confirmed gap: `classify_document`'s LLM call only ever sees the document's
  first 8000 characters, and nothing in `DocumentAgentSpec` could raise that — a document whose
  type-identifying content sits past the first few pages is architecturally invisible to the
  classifier regardless of taxonomy quality. New `classify_max_chars: int | None = None` on
  `DocumentAgentSpec`, threaded through `DocumentAgent.classify()`; unset behaves exactly as
  before (classify_document's own 8000 default). 2 new tests (`test_document_agent.py`). Full
  suite green (3035 passed, 3 skipped, no regressions).
- **Per-skill `max_turns` now falls back to the parent's own resolved turn budget, not the SDK's
  bare default of 10.** The other half of this session's earlier `InteractiveAgent` MaxTurns fix
  — that one only raised the *parent* orchestrator's `Runner.run`/`run_streamed` default (10 →
  30); a skill's own sub-agent run (`Agent.as_tool(max_turns=...)`) still passed an unset
  `Skill.max_turns` straight through as `None`, landing on the SDK's bare 10. Surfaced by a real
  consumer independently hitting it: their skill YAMLs each hand-set `max_turns: 50` with a
  comment explaining the exact same gap, on every one of their skills. `_build_parent_tools` now
  resolves a `default_skill_max_turns` once (mirroring `spec.max_turns` unset →
  `_DEFAULT_AGENTIC_MAX_TURNS`, same as the parent) and a skill without its own `max_turns`
  inherits that — same fallback shape `model` already uses. 2 new/updated tests
  (`test_interactive_agent.py`). Full suite green (3033 passed, 3 skipped, no regressions).
- **Dependabot: mlflow/sqlparse floors bumped, closing 5 open alerts (1 critical, 3 high, 1
  medium).** `mlflow` floor `>=2.9` → `>=3.15.0` (fixes the critical unauthenticated SSRF in
  webhook delivery — `_validate_webhook_url` bypassed via unvalidated redirects/DNS rebinding).
  `sqlparse` — pulled in transitively by mlflow-skinny (`>=0.4.0,<1`, no upper cap) — gets a new
  explicit floor `>=0.6.0`, closing 3 ReDoS/CPU-DoS alerts plus an unescaped-backslash SQL-breakout
  one, matching the file's existing convention of pinning vulnerable transitive deps explicitly.
  `poetry lock` resolves cleanly with no forced regression elsewhere (`cryptography` stays at
  48.0.1 — the separate, already-documented, not-yet-fixable alert #98 is untouched). Verified
  by actually installing the `mlflow` extra (not just trusting the lock solve) and confirming
  `mlflow`/`mlflow-skinny` land on 3.15.1 and `sqlparse` on 0.6.0. Full suite re-confirmed against
  this repo's real baseline dev extras (`finance` + `templating`; `mlflow`/`azure` are
  genuinely absent by design — those tests exercise the extra-not-installed fallback path) —
  3032 passed, 3 skipped, byte-identical to before the bump.

## [2.4.2] - 2026-08-17

- **`ConductorEngine` gains opt-in step-failure recovery (`on_step_error`); the reference chat
  pipeline (`pipelines/chat.py`) wires a default one.** Follow-on to the `InteractiveAgent`
  MaxTurns fix above: asked whether the reference chat pipeline shared the same class of
  problem. It didn't share that *specific* bug (`answer_step` calls `agent.respond()` directly, so
  it already inherited the fix for free) — but reading `ConductorEngine._run_step` found the same
  *shape* of gap one layer up: a step component's exception was never caught anywhere in the
  engine (only `SuspendRun`, a control signal, was special-cased), so any step failing propagated
  raw out of `run()`/`resume()`. New `on_step_error` constructor param (`StepErrorHandler`, opt-in,
  default `None` — every existing pipeline is byte-identical): on a step exception (never
  `SuspendRun`), it's handed `(step, state, exc)`; its return value becomes the step's emitted
  output exactly as if the step had returned normally, and the run continues (`ExecutedStep`/
  `StepEvent` get a new `"errored"` status alongside `ran`/`skipped`/`halted`, so a recovered step
  is distinguishable from a clean one in a trace). The handler re-raising propagates unchanged.
  `pipelines/chat.py` wires this by default (`default_step_error`, overridable via
  `run_chat_turn(on_step_error=...)`, `None` to opt out): a degraded `InteractiveResponse`
  (reusing `incomplete`/`incomplete_reason`, the same fields the `InteractiveAgent` fix added)
  instead of a crash. Caught a real correctness trap while designing this, not just implementing
  it: a naive version that let the substitute value flow through normally would silently break
  `chat_guards()`'s `_route`, which expects a `GateDecision` in `state.emitted["gate"]` — a gate
  failure recovered that way would crash the *next* step's guard instead of the step itself. Fixed
  by having `default_step_error` always set `state.halt = True`, so no downstream guard ever runs
  against a substituted value regardless of which step failed; `run_chat_turn` falls back to
  scanning `emitted` for the `InteractiveResponse` when `finalize` didn't get to run because of the
  halt. 9 new tests across `test_conductor_engine.py`/`test_interactive_chat.py` (including one
  that pins down the gate-failure/guard-crash trap as a regression case). Full suite green (3032
  passed, 3 skipped, no regressions).
- **`InteractiveAgent` agentic-path latency/robustness pass.** Prompted by a production report of
  an assistant chat regularly taking >60s/query, then a direct question of whether "interactive"
  had any architectural landmines. Audited retry scoping, model/effort tiering, tool-call
  concurrency, fast-path routing, and MaxTurns handling against the actual code (not assumed);
  most were already fine (tool calls already run concurrently via the SDK's own executor; a
  nested skill's failure is already absorbed by the SDK's `as_tool` error handling, not a full
  outer-run redo). Two real gaps, both fixed: (1) the agentic path had **no MaxTurns handling at
  all** — `run_with_recovery` deliberately excludes `MaxTurnsExceeded` (rebuilding the agent isn't
  its job), so an unset `spec.max_turns` fell through to the SDK's bare default of 10 (tuned for a
  single-purpose agent, not one that may delegate through a nested skill sub-agent's own turns) and
  a genuinely complex multi-tool turn raised `MaxTurnsExceeded` straight out of `respond()`
  uncaught — a hard crash, not a slow answer. Now: an unset `spec.max_turns` defaults to 30
  (matching `run_agent`'s own tuned default) instead of the SDK's bare 10, and `_respond_agentic`
  catches `MaxTurnsExceeded` and returns a typed degraded `InteractiveResponse` (new
  `incomplete`/`incomplete_reason` fields, same shape as the existing `blocked`/`block_reason`)
  instead of propagating the raw SDK exception. (2) `Skill` had a per-skill `model` override but no
  `reasoning_effort` override — a routing/classification-style skill or a deterministic-lookup
  skill had no way to run cheaper/faster than the parent orchestrator without also switching
  models. New `Skill.reasoning_effort: str | None`, threaded into that skill's sub-agent's own
  `ModelSettings` (built fresh via `build_model_settings` when set; unset skills keep inheriting
  the parent's `ModelSettings` unchanged). 3 new/updated tests in `test_interactive_agent.py`.
  Full suite green (3024 passed, 3 skipped, no regressions).
- **`MlflowTracer` self-sanitizes leaked OTLP env vars; new `enable_mlflow_agent_autolog()`.**
  Surveyed a companion service's own tracing package (already using `InteractiveAgent`) for
  japes evolution opportunities and found `sanitize_leaked_otel_env_vars` (added earlier — strips
  the `OTEL_EXPORTER_OTLP_ENDPOINT` vars Azure Container Apps injects platform-wide, which
  otherwise silently break MLflow's span exporter) was never actually called by anything in
  japes, `MlflowTracer` included — confirmed via a full-package grep. Its own docstring claims
  to spare every consumer from reinventing the guard, but two companion services had each
  carried an independent copy anyway, since the one class that should self-apply it didn't.
  Now wired into `MlflowTracer._mf()`, once, before the first real `import mlflow` is cached —
  scoped exactly to the MLflow-tracing case the function's docstring already carves out (an
  injected `mlflow_module`, e.g. tests, is untouched; OTel infra tracing is untouched). Second
  gap from the same survey: no toggle for `mlflow.openai.autolog()` (nested-agent-call MLflow
  tracing) existed in japes at all — every consumer wanting it had to hand-roll the idempotent
  enable-once wrapper themselves. New `enable_mlflow_agent_autolog()` in
  `observability.mlflow_env`, alongside the existing `flush_mlflow_async_trace_queue` (same
  "process-level MLflow hygiene, call once" style) — idempotent, best-effort, never raises.
  Both re-exported from `jazzx_sdk.observability` and the SDK root. 5 new tests
  (`test_observability.py`, `test_otel_tracking.py`). Full suite green (3022 passed, 3 skipped,
  no regressions).
- **`ScorerResult` gains `findings: list[Finding]`.** Same `policy-workbench` survey, its third
  candidate: `policy_evaluator`'s `EvaluationIssue` (phrase/issue/suggestion triplet, an LLM
  flagging specific spans) is a recurring "list of flagged items" shape `ScorerResult` had no
  first-class slot for — every consumer was left to invent its own triplet in the freeform
  `metadata` bag. New `Finding` model (`subject`/`description`/`suggestion`/`severity`, all but
  `subject`/`description` optional) + `ScorerResult.findings`, defaulting to `[]` (existing
  callers unaffected). `CompositeScorer` and every built-in adjudication policy (`_adjudicated`)
  now union `findings` from applicable (non-skipped) sub-scorer results into their own verdict —
  same skip-exclusion rule the score/pass aggregation already uses. `AdjudicatorScorer` fills
  `findings` from the inline sub-results only when a custom `adjudicate` callable left them
  empty — never overwrites what the callable set itself. Kept the eval-service convergence
  contract (`scorer_result_to_verdict_v1`, "lossless adapter", Phase 4 acceptance criterion #13)
  actually lossless: `findings` didn't exist when that contract was negotiated and
  `ScorerVerdictV1` has no dedicated wire field for it — extending that cross-repo contract is
  out of scope for a japes-side change alone, so it's folded into `metadata["findings"]`
  (a list of dicts) instead, verified round-trip in `test_scoring_execution_adapters.py`. Both
  `jazzx_sdk.evaluation` and `jazzx_sdk.contracts` re-export `Finding` alongside `ScorerResult`.
  12 new/updated tests across `test_scorers.py`/`test_scoring_execution_adapters.py`. Full suite
  green (3017 passed, 3 skipped, no regressions).
- **`fan_out` gains `skip_if` — resumable fan-outs.** Surfaced by surveying `policy-workbench`
  (a real, independent multi-agent app, no japes awareness) for japes evolution opportunities:
  its `policy_creator` agent hand-rolls exactly this via `_staged_jtbd_files`/
  `_staged_section_files` — re-scanning a tmp/ staging dir on every call to know which
  plan-items (sections) a prior partial run already finished, so a retry doesn't redo completed
  work. `fan_out` itself had no such notion (single-shot, in-memory, verified by reading it
  directly rather than assumed). `skip_if(item, index)` — sync or async, dispatched via the
  existing `concurrency.call_maybe_async` — runs before `process`; a truthy result skips that
  item entirely (`process` never called), its slot is `None` (same convention `degrade`'s
  failure path already uses), and the skipped item still opens a tracer span (`inputs={...,
  "skipped": True}`) so it reads as "known done" in a trace, not silently absent. `None`
  default: byte-identical to before. Considered and deliberately did NOT build a bundled
  "plan → dispatch → synthesize" pipeline primitive for the same survey's other candidate
  (`policy_modifier`/`policy_creator` both hand-roll that shape too) — once `skip_if` exists,
  the remaining pieces (`output_schema` for the structured plan, `run_with_recovery` for retry,
  dict-based dispatch-by-field) are already a few lines of ordinary caller code over existing
  primitives; a new abstraction for that would be premature (no second real japes-side
  consumer asking for it, unlike `investigation_loop`, which unified 6 *existing* hand-rolled
  loops within this codebase before being built). 7 new tests (`tests/test_fanout.py`). Full
  suite green (3011 passed, 3 skipped, no regressions).
- **`InteractiveAgent` reasoning-summary streaming.** Prompted by an external review of three
  specific gaps (hardcoded `Reasoning.summary="auto"`, `respond()` had no way to observe
  reasoning deltas, nested skill sub-agents had no reasoning visibility at all); verified each
  against code, then generalized into one consistent mechanism rather than three separate
  patches. `build_model_settings` gained `reasoning_summary` (e.g. `"concise"`), threaded
  through new `InteractiveAgentSpec.reasoning_summary`. New `InteractiveAgentSpec.
  stream_reasoning: bool` mirrors `stream_tool_events`'s exact scope (parent run + every skill
  sub-agent) via the mechanism each actually requires: `_respond_agentic` switches its internal
  `_run_once` to `Runner.run_streamed` + a full `stream_events()` drain only when set (`respond()`'s
  return contract is unchanged; `run_with_recovery`/context-window-fallback retry don't apply in
  that mode — the same tradeoff `_stream_agentic` already documents, for the same reason), and
  `_build_parent_tools` passes `on_stream=` to each skill's `sub_agent.as_tool(...)`. One shared
  classifier, `stream_hooks.reasoning_delta_text`/`publish_reasoning_delta`, serves both call
  sites — `AgentToolStreamEvent["event"]` is the identical `RawResponsesStreamEvent` shape the
  top-level drain already handles (verified against the installed SDK). Reasoning deltas
  publish through the same `publish_event` sink `ToolStreamHooks` already uses, not a second
  generator-yield channel — using `common.core.streaming.ReasoningEvent` (already reserved
  ahead of any producer in `common`'s own history), imported guarded like `FinalResultEvent` so
  an older pinned `common` degrades to a silent no-op. Real, not papered over: neither
  `ReasoningEvent` nor `ToolStartEvent`/`ToolEndEvent` carry a per-event agent-attribution
  field, so nested skill reasoning publishes unattributed today — a pre-existing gap across the
  whole event family, not new here; fixing it needs a `common` schema change, out of scope for
  a japes-side pass. 10 new tests (`tests/test_reasoning_stream_hooks.py`,
  `tests/test_agent_models.py`, `tests/test_interactive_agent.py`). Full suite green (2998
  passed, 3 skipped).
- **New `jazzx_sdk.tools.documents.local_cache`** — the local dev/demo document cache (a git-
  committed filename→remote-doc-id manifest that hydrates a stubbed local file from a shared
  Knowledge Hub on demand) generalized from a jaci-specific module. Nothing in the original was
  domain-specific — pure filename↔doc-id bookkeeping — so this is a direct lift:
  `manifest_path`/`read_manifest_entry`/`record_push` (two independently-mergeable tiers,
  derived-markdown and raw-original), `ensure_local_cache`/`ensure_local_caches` (two-tier pull,
  cheapest first), `StalenessInfo`/`check_staleness` (cheap metadata-only mismatch check, never
  auto-resolves). Composes ahead of `convert_document` as a separate async pre-step (same
  "sync callers, async fabric fetch" reasoning the original had) rather than a `fabric=` param
  on `convert_document` itself. Re-exported from `jazzx_sdk.tools`. 10 new tests
  (`tests/test_local_cache.py`).
- **`DocumentAgent.process_dir(collection_id=...)` now has a real Knowledge-Hub-backed
  integration test**, not just a hand-rolled fake `DocStore`. Confirms the full path —
  `sync_collection` → `MockKnowledgeHubClient.list_documents`/`materialize`'s download →
  classification — actually works end-to-end, not just that `process_dir` calls
  `sync_collection` correctly (`tests/test_doc_pipeline_gaps.py`).
- **`MockKnowledgeHubClient` now persists documents and ontologies, not just entities (issue
  #57 part a).** `_load_from_data_dir` already loaded all three from `data_dir` on startup, but
  only entity mutations wrote back — a document or ontology created/updated/deleted during a
  session vanished the moment the process restarted (every Streamlit rerun, or any multi-
  process pipeline). `_persist_entities` generalized into a shared `_persist(store_attr,
  filename)` helper (`_persist_ontologies` reuses it directly); documents get their own
  `_persist_documents` since `content` is arbitrary bytes (PDFs, zips, not just UTF-8 text) —
  base64-encoded before `json.dumps`, decoded back on load, rather than silently mangled by
  `json.dumps(..., default=str)`'s `str(b'...')` fallback. Wired into every mutator:
  `create_document`/`update_document`/`delete_document` (`create_document_v2`'s idempotent-hit
  branch needs nothing new — it returns an existing record, doesn't mutate) and
  `create_ontology`/`upload_ontology`/`update_ontology`/`delete_ontology`. Found and left alone
  along the way: `get_document`'s docstring promises `None` on a miss but actually fabricates a
  fake document — pre-existing, unrelated, not touched. 10 new tests
  (`tests/test_mock_kh_persistence.py`, new file), each constructing a fresh client against the
  same `data_dir` to prove the write actually crossed a process boundary, not just an in-memory
  round-trip.
- **`FabricConfig.validate_for_mode()` no longer requires `knowledge_hub_url` when a client is
  already supplied (issue #57 part b).** STRICT/CACHED's `knowledge_hub_url` check exists so
  *something* can build a client from it; a caller who already constructed one (real or Mock)
  and hands it straight to `KnowledgeFabric(kh_client=..., config=...)` doesn't need it —
  before this fix that caller had to pass a throwaway URL string (e.g. jaci's
  `shared/fabric.py::build_fabric` used `knowledge_hub_url="mock://local-kh"`, "never dialed")
  just to pass validation. New `validate_for_mode(*, has_client: bool = False)` param, defaults
  to the old strict behavior (`from_env()`'s own call site, which never sees a client, is
  unaffected); `KnowledgeFabric.__init__` now passes `has_client=kh_client is not None`. 9 new
  tests (`tests/test_fabric_config.py`, new file — no prior dedicated coverage of this method).
- **`AllOfCondition`/`AnyOfCondition` — composite `Condition` combinators (P8,
  `ENCODING_NOTES.md` G1 / `policy-ir-abstraction.md` P3).** Several real conjunctive rules
  (e.g. "warrantable condo outside Florida," a multi-field prepayment-penalty gate) had no
  honest encoding: folding the extra predicate into a `MatrixCondition` axis multiplies cells
  and destroys reviewability; burying it in a `DslExpression` formula defeats the same
  reviewability discipline `RatioCondition`'s `profile:` rule protects. `AllOf`/`AnyOf` nest any
  existing kind, including each other (depth-capped at 5), and must be authored with an
  explicit `kind:` — unlike `matrix`'s axes-key sniff, a bare `conditions: [...]` list can't
  structurally distinguish the two. Verdict algebra: `AllOf` is `VIOLATED` if any child is,
  else `INDETERMINATE` if any child is (dominates `SATISFIED` — the safe direction), else
  `SATISFIED`; `AnyOf` mirrors it. Every child evaluates unconditionally, never short-circuited,
  so `RuleOutcome.inputs["limbs"]` always shows every limb's own state. `evidence_contract()` is
  the union of every child's contract, so `check_compliance`'s cross-policy field-claiming
  precedence still works for a composite. Dispatches through the existing
  `get_condition_evaluator(kind)` registry — `DefaultPolicyExpert.check_compliance` needed zero
  edits. Known, documented limitation (not fixed this pass): `execution`/`stochastic` are fixed
  DETERMINISTIC/False class attributes looked up by `kind` alone, so a composite nesting a
  `natural_language` (LIVE) child would still evaluate correctly but be misclassified as
  DETERMINISTIC by the adjudication chassis's `partition_rules` — deferred until a real
  composite mixes LIVE and DETERMINISTIC children. 19 new tests across
  `test_condition_evaluator.py`, `test_default_policy_expert.py`, `test_adjudication_
  partition.py`.

- **`find_profile_literal_drift`/`assert_no_profile_literal_drift`** (P8, `policy-ir-
  abstraction.md` P4a) — a new `jazzx_sdk/fabric/canonical/policy_lint.py`. `RatioCondition.
  threshold` must be `profile:<key>` so thresholds stay reviewable in one place; `Expression.
  value` takes bare literals, so a pack that duplicates a literal into `PolicyProfile.custom`
  for review has nothing enforcing the two stay equal. The lint checks any `Expression`
  declaring `domain_extensions["profile_custom_key"]` against its named `PolicyProfile.custom`
  twin — no schema change (`Expression.domain_extensions` already existed). 8 new tests.

- **`MatrixCondition` — a table-valued `Condition` kind (P8, D2).** Generalizes
  `RatioCondition`'s single `profile:<key>` threshold to a lookup keyed by N axes (e.g.
  loan-amount band x FICO tier x purpose), each independently numeric-banded or categorical —
  the primitive an eligibility grid needs instead of dozens of near-duplicate rules or DSL
  `if()` chains that bury the numbers. Resolved cell values live in a new
  `PolicyProfile.tables` bucket (`profile_table:<name>` reference, fail-closed
  `PolicyProfile.get_table()`) — never a literal, same discipline `RatioCondition` already
  enforces. An explicit `NA`/`False`/`None` cell evaluates to `VIOLATED` (the grid gave a real
  answer), not `INDETERMINATE`. Fully additive: `DefaultPolicyExpert.check_compliance` and the
  adjudication chassis's `partition_rules`/`impacted_rules` all dispatch via the existing
  `get_condition_evaluator(kind)` registry, so zero other call sites changed.
- Fixed a real, latent gap in `ExpressionEvaluator`: `ComparisonOperator.IN`/`NOT_IN`/`CONTAINS`
  were declared on the enum but never implemented — an `Expression(operator=IN, ...)` silently
  evaluated as always-`VIOLATED`. Now implemented (skips the numeric cast for these operators),
  closing the "N states → N rules" gap directly on the existing `Expression` kind.
- **HITL suspend now works inside a `Loop`** (D3). `ConductorEngine` previously converted a
  `SuspendRun` raised from a loop's body straight into a `RuntimeError` ("supported only for
  top-level steps"). `_run_loop` now catches a mid-body suspend per-step and can be re-entered
  from that exact point on resume — finishing the interrupted iteration's remaining steps
  without re-running the ones before it, then continuing the loop (convergence/max-iterations)
  and the rest of the pipeline completely normally. `Suspension`/`DurableSuspension` gained
  `loop_id`/`loop_iteration` (both additive, `None` for a top-level suspend — no DB migration,
  `DurableSuspension` round-trips through one JSON column). New `ConductorPipeline.get_loop()`.
  A second suspend inside the same resumed loop, and `resume_durable` through a loop suspend,
  both just work — no special-casing needed beyond the one resume path.
- **Two bug fixes to the condition-evaluator kinds landed alongside D2/D3, reported externally:**
  - `RatioCondition.direction` was typed `ComparisonOperator` (9 values) while
    `RatioEvaluator.evaluate()` only ever handled 2 (`RatioDirection`'s `>=`/`<=`) — a strict
    operator like `<` validated fine at construction and then raised `ValueError` at first
    evaluation. Narrowed the field to `RatioDirection` directly (pydantic now rejects an invalid
    value at construction, naming both legal values), plus a validator explaining *why* only
    `>=`/`<=` are evaluable (margin-to-threshold semantics) and pointing to `Expression` for a
    genuinely strict comparison. Non-breaking — every existing call site already used `>=`/`<=`.
  - `ExpressionEvaluator.evaluate()` unconditionally `float()`-cast the actual value for every
    non-membership operator, so a string-typed field (`citizenship_type == "itin"`) raised
    `ValueError` instead of evaluating. `==`/`!=` now compare raw values (no implicit numeric
    coercion — `"5" == 5` is correctly `VIOLATED`, a deliberate behavior change); ordering
    operators (`>`,`>=`,`<`,`<=`) still cast, but a cast/comparison failure is now
    `INDETERMINATE` rather than a raise, matching `DslEvaluator`'s existing convention for
    unresolvable data.
- Fixed `DefaultPolicyExpert._build_rationale` crashing (`ValueError`) on any non-numeric
  violation value (e.g. `property_state == "AK"`) — found while validating a real policy corpus
  authored against the fixes above. `_build_rationale` unconditionally `.4g`-formatted each
  violation's `actual` value, an assumption the `Expression` float-cast bug had made
  unreachable until now (a non-numeric `actual` used to raise before ever reaching this code).
  Now formats real numbers with `.4g` and everything else via `str()`. 2 new tests.
- `_describe_condition` no longer renders a `matrix` violation as the bare string `"matrix"` —
  it now names the resolved cell and value from `RuleOutcome.inputs` (e.g. `"cltv_pct <= 75
  (cell la_le_1_5m|640|purchase)"` instead of just `"matrix"`), which is load-bearing for any
  pack whose over-conditioning story depends on every violation citing what it actually failed.
  `_condition_label` needed no change — it already rendered correctly for `matrix`
  (`MatrixEvaluator.evidence_contract()` returns non-empty axis fields). 3 new tests.

## [2.4.0] - 2026-08-13

**Unified Assistant Framework ships, plus a full reliability hardening
pass.** Skill catalog, versioned manifest lifecycle with rollback, and
guardrail-gated PassBar promotion (UAF, 13 phases) -- backed by SDK-wide
reliability hardening: unified retry across every LLM provider, approver
identity on suspensions, tool timeout + a non-raising result envelope,
durable queue idempotency, blob offload at conversation/turn-event write
boundaries, an LLM invocation ledger, fan-out parent/ordinal tracing, and
an enforced RAG citation contract. Plus execution-state vs quality-verdict
separation in the eval harness, trace_id continuity on the runs API, a
wasted-probe fix in `DocStore.materialize()`, and financial-spread
vocabulary-gap tracking.

`DocStore.materialize()` skips its own metadata probe when the manifest
store can't possibly use the answer

Reported: with `NullMaterializeManifestStore` configured, `materialize()`
still ran one `get_document_metadata` HTTP call per unique document on
every call -- for zero possible benefit. `NullMaterializeManifestStore`'s
own docstring already promises "no persistence at all... every call
re-downloads everything (no skip-if-unchanged)" -- `manifest.load()`
always returns `{}` and `manifest.save()` discards, so the probe's answer
could never change the always-download outcome. Verified exactly as
reported before touching anything (`store.py:870-895`, `:963-972`).

Considered and rejected a new `skip_unchanged` public parameter (the
reported fix): it would give a caller two independently-settable things
that have to agree (`manifest_store=NullMaterializeManifestStore()` *and*
`skip_unchanged=False`) to get what picking the Null store alone should
already guarantee -- set one without the other and the same silent-waste
bug reappears, just harder to spot. Fixed instead by having the code
honor the promise `NullMaterializeManifestStore` already documents:
`probe_worthwhile = bool(get_metadata) and not
isinstance(manifest, NullMaterializeManifestStore)` gates the probe, the
`_needs_download` fallback, and the trailing manifest-save loop -- no new
public parameter, nothing for a caller to remember to keep in sync.
`sync_collection()` delegates to `materialize()`, so it's covered too;
confirmed it has no duplicate probe logic of its own.

2 new tests (test_fabric_materialize_idempotent.py: the probe is skipped
entirely with the Null store -- `metadata_calls == 0` -- and a regression
guard confirming the default `FileMaterializeManifestStore` still probes
normally).

`FinancialSpread.vocabulary_gaps` -- additive field so a caller aggregating
`structure_statement()` across a spread's statements (jaci's `spreader.py`
is the intended first consumer) has somewhere to carry
`StructuredStatement.vocabulary_gaps` forward without inventing a second
return value or a side channel

`structure_statement()` already tracked unresolved vocabulary keys per
statement (`StructuredStatement.vocabulary_gaps`, existing) but nothing
aggregated them once multiple statements get assembled into one
`FinancialSpread` -- there was no field to put them in. Followed the
exact forward-ref pattern `period_set`/`SpreadLine.semantics` already
established (`spread.py` can't import `structure.py` at runtime without
a cycle -- `structure.py` already sits downstream via `vocabulary.py` ->
`periods.py`), including the same "which module's rebuild call resolves
it" question the `period_set` precedent had already answered: extended
`periods.py`'s existing bottom-of-file `model_rebuild()` block (not a
new one in `structure.py`) to also import `VocabularyGap` and include it
in `_types_namespace` -- a second, separate `force=True` rebuild call in
a different module would have needed to re-supply `PeriodSet` too, or
risk clobbering the already-resolved `period_set` field.

3 new tests (test_finance_periods.py: unaffected-when-absent, additive,
and import-order-independent -- mirroring the three existing `period_set`
tests exactly). Full suite green (2836 passed, 3 skipped).

Eng-queue 0.2 (docs/plans/engineering_queue.md, from the eval-service
convergence analysis): separate execution state from quality verdict in
`CaseResult`/`EvaluationResults`, and fix the one place it was already
live on the wire

`EvaluationHarness._run_single_case`/`_run_cases_parallel` both set
`CaseResult.passed=False` when the conductor raised -- indistinguishable
from a case that ran to completion and genuinely scored below bar.
Traced the actual blast radius before deciding how invasive a fix could
be: `CaseResult.passed` has exactly 3 real consumers in `jazzx_sdk/`
(`harness/runner.py`'s own aggregation, `harness/results.py`'s
truth-mode breakdown, `eval_service_adapters.py`'s wire adapter) --
`pass_bars.py`'s `.passed` usages are on the unrelated `ScorerResult`
type, not `CaseResult`, confirmed by reading the code rather than
assuming from the name.

- `CaseResult.passed` widened from `bool` to `bool | None` --
  `None` now means "execution failed before quality could be evaluated,"
  distinct from `False` ("ran, scored below bar"). Backward compatible:
  every existing caller passing an explicit `bool` is unaffected; `if
  result.passed` / `not result.passed` treat `None` and `False`
  identically (both falsy), so nothing downstream silently breaks on the
  widened type.
- Both exception-handling `CaseResult(...)` construction sites in
  `harness/runner.py` now set `passed=None` instead of `passed=False`.
- `EvaluationResults` gained `errored_cases: int` -- the subset of
  `failed_cases` that never got a quality verdict at all.
  `failed_cases`/`pass_rate` keep their exact existing formulas (`total -
  passed`), so no existing consumer of those two fields sees a behavior
  change; `errored_cases` is purely additive, for a caller that wants to
  tell "the pack scored badly" apart from "the harness broke."
- **The one place this was already live and misrepresenting state on an
  actual wire contract, not just internally:**
  `eval_service_adapters.py::case_result_to_evaluation_v1` mapped
  `passed=False` (execution failure included) straight to
  `QualityVerdict.FAIL` -- reporting an unscored case to eval-service as
  a scored-and-failed one. Fixed to map `passed is None` to
  `QualityVerdict.SKIP`, a value that already existed in
  `jazzx_eval_contracts` for exactly this ("Aggregate quality decision
  for a completed case -- independent of execution/runtime state," per
  `CaseEvaluationV1`'s own docstring) -- the contract already modeled
  this distinction; only the Japes-side adapter hadn't caught up to it.
- Scoped out, not silently dropped: eval-service's wire contract also has
  a full `ExecutionResultV1` (status/output/failure/trace_refs) that
  nothing in `jazzx_sdk/` currently builds at all -- a separate,
  larger adapter-completeness item, not part of this fix.

5 new tests (test_evaluation/test_runner_failures.py +2 new aggregation
tests, 2 existing assertions corrected from `passed is False` to `passed
is None` to match the intended fix; test_scoring_execution_adapters.py
+1). Full suite green (2831 passed, 3 skipped).

trace_id continuity: runs/server.py's `start()` route now defaults
`TurnRun.trace_id` from the same governed trace context the request was
already resolved under

Follow-up to K6's own noted finding: this codebase has (at least) three
independent trace_id holders -- `authority.context.InvocationContext.trace_id`,
OpenTelemetry's `observability.telemetry.get_current_trace_id()`, and
`runs.schema.TurnRun.trace_id` -- and K6 flagged, without resolving, that
they aren't uniformly wired together. Traced each pairwise relationship
through real code paths before deciding what (if anything) needed fixing,
rather than treating "three things share a name" as automatically a bug:

- InvocationContext vs OTel's trace id: **legitimately separate, correctly
  left alone.** Different concepts that happen to share a name -- one
  identifies a distributed-tracing span tree (OTel's own instrumentation,
  typically W3C `traceparent`), the other a governed request's
  authorization scope (`X-Trace-Id`). No code anywhere threads one into
  the other; there's no missing link to add.
- OTel vs `TurnRun.trace_id`: same verdict, different layers (span tree
  vs. durable turn record), never connected, nothing to fix.
- **InvocationContext/governed-http's trace context vs `TurnRun.trace_id`:
  a real, confirmed gap.** `governed_http.py`'s dependency already
  resolves a trace_id per request (`X-Trace-Id`, or a generated one if
  absent) into `_trace_id_var` (`set_governed_context`) -- but
  `runs/server.py`'s `start()` route only ever used
  `StartRunRequest.trace_id`, a separate JSON body field with no
  connection to it. A caller could send `X-Trace-Id: abc` and either omit
  `trace_id` from the body or send a disagreeing `"trace_id": "xyz"`, and
  `TurnRun.trace_id` would end up `None` or `"xyz"` while the same
  request was governed under `"abc"` -- no code anywhere reconciling
  them. Confirmed this is exactly the kind of drift K6's own `trace_id`
  default (from ambient `InvocationContext`) was already at risk of being
  inert against on this exact route, since `runs/server.py` doesn't opt
  into `require_identity=True` either.
- Fixed with the existing precedent already in the same file
  (`governed_http.py`'s own header-vs-explicit backfill at its
  `require_identity` branch): `start()` now defaults
  `trace_id = body.trace_id or get_governed_context()["trace_id"]` --
  an explicit body value still wins (same "explicit beats ambient" rule
  K6 established), but omitting it no longer silently loses the
  trace_id the request was already governed under. Deliberately did NOT
  flip `require_identity=True` on this router -- that additionally
  requires identity headers and would be a real, separate behavior
  change (401 on requests lacking them) for something this fix doesn't
  need.

2 new tests (test_runs_server.py +2: header-default and explicit-wins).
Full suite green (2828 passed, 3 skipped).

Kernel salvage K7 (design note only, no code -- plan explicitly scopes this
"size: large, its own effort, not folded into K1-K6/K8/K10"): parent-to-
sub-agent state inheritance, docs/plans/design_note_k7_parent_child_artifacts.md

Authorization already cascades parent-to-child (`InvocationContext`/
`PermissionScope` via `descend()`/`narrow()`); state has no counterpart --
every sub-agent `_build_parent_tools`/`_build_composed_skill_tool` builds
starts from nothing but the tool-call argument string, and everything it
derives is discarded when `as_tool` returns. All five points the plan
required settled:

- **Shape**: a new, small `fabric` store (working name `ArtifactStore`),
  NOT an extension of `CaseContext` as first considered -- `CaseContext`
  is Conductor/case-scoped, while the gap is `InteractiveAgent`-scoped (a
  plain chat assistant has no `CaseContext` at all); forcing that
  dependency would be the wrong coupling direction. Composes with
  `CaseContext` for packs that want case-level durability (a checkpoint
  step may promote artifacts into `domain_extensions["artifacts"]`, the
  same operational-to-canonical promotion pattern this file already uses
  elsewhere) rather than being folded into it.
- **Mechanism**: a sibling ambient ContextVar (`set_/get_/reset_
  artifact_scope`), propagated with the identical idiom
  `authority.context`'s own `InvocationContext` trio already uses, at the
  same `_build_parent_tools` call sites -- not a field bolted onto
  `InvocationContext` itself, which would blur its single "authorization
  context" responsibility for no benefit.
- **Visibility = authorization**: reuses `PermissionScope`/`admit_hop`
  directly, generalized via a new `artifact:<key>` selector family --
  found `agents/adjudication/workspace.py::EvidenceWorkspace`'s existing
  `mount:<name>` pattern is *exactly* this one level removed (same
  `narrow()`+`descend()` shape); a new `Skill.reads_artifacts` field
  gates parent-artifact visibility the same way `reads` already gates
  `doc_source:` today.
- **Write-back**: one-directional (child reads parent; parent never reads
  child), matching Kernel's own answer -- the smaller, safer change, and
  avoids inventing a same-key write-conflict policy a two-way answer
  would need.
- **What not to port**: Kernel's OData-on-notepads (odata.py +
  EntityStore.filter already cover it) and its untyped `creator_source`
  enum (this design's `source_type` should reuse `ActorRef`'s existing
  typed vocabulary, the same reuse call K2 already made for
  `DurableSuspension`'s approver fields).
- Explicitly flagged, not glossed over: the plan's own required cross-
  check against `Builder_Pack_Studio_Paradigm_Assessment §6` and the
  `Skill`-composition item in `Japes_Enhancement_Backlog P2` could not be
  done -- neither document exists anywhere in this repo (searched,
  including gitignored docs/plans/). Recorded as a required step before
  anyone acts on this design, not silently skipped.

No code changes; no new tests (design note only, per the plan's own
scoping). Full suite unaffected (2826 passed, 3 skipped, unchanged from
K8).

Kernel salvage K8: enforced source attribution on `RAGStore.search` --
reused the existing `Source` citation type, and fixed a live crash bug
found while verifying the plan's premise

`RAGStore.search()` called `self._kh.search_documents(collection_id=,
query=, limit=, metadata_filters=)` -- kwargs neither the real
`KnowledgeHubClient.search_documents(collection_id, query)` (no
limit/metadata_filters at all -- "controlled by KH's own service
configuration, not by the client," per its own docstring) nor
`MockKnowledgeHubClient`'s (`top_k`/`filters`, different names) accept.
Every real call would `TypeError` before a citation question was ever
reached -- confirmed via `test_integration_followups.py`'s own tracked
mock/real param-drift set (a *different*, already-known issue: mock vs.
real disagreeing with each other, not a caller passing kwargs neither
one has). Zero existing test coverage exercised the real path, only a
guidance-store test double.

- `search()` now calls `search_documents(collection_id=, query=)` only;
  `limit` is enforced client-side by truncating the result list (the
  method's own documented contract, restored rather than silently
  broken); a non-empty `metadata_filters` is logged (not silently
  dropped with zero signal) since KH has no server-side parameter for it.
- Return type changed from `list[dict[str, Any]]` to `list[Source]` --
  reused `agents.interactive.response.Source` (kind/ref/label/uri/
  collection_id/quote/locator), the SDK's one existing citation type,
  rather than inventing a second one. Added `score: float | None` to
  `Source` (the one field K8's "document_id/chunk_id/score" ask needed
  that `Source` didn't already have); `chunk_id`, when present, folds
  into `ref` as `"{document_id}#{chunk_id}"` rather than a new field --
  none of `Source.locator`'s existing `Locator` union members
  (page/cell/section) fit a RAG chunk id, and KH doesn't always return
  one.
- Hard contract: a result with no resolvable document identity
  (`document_id`/`id`/`doc_id`, in that order) raises `KnowledgeFabricError`
  naming the offending payload, rather than silently becoming an uncited
  snippet -- reaching a SAR narrative or adjudication output unattributed
  is worse than not reaching it at all.
- Checked `fabric/docs/store.py` (the plan's other named file): its own
  citation-relevant piece, `MaterializedDoc.entity_id`, is on the
  materialize/download path, which already carries `entity_id` for
  citation -- not the search/retrieval gap K8 is about. No change needed
  there; confirmed, not skipped silently.
- Not done, per the plan's own framing: raising this as an explicit
  Kernel→KF migration exit criterion (an SDK type change can only
  enforce what KH actually returns) is a cross-team conversation, not a
  code change.

7 new tests (test_rag_store.py, new file). Full suite green (2826
passed, 3 skipped).

Kernel salvage K10: `parent_step_id` + concurrency ordinal via the
sanctioned metadata hatch, not a governed `TraceStep` schema change --
also closes K2's deferred step 3

`TraceStep` is `extra="forbid"`, frozen at Schema Spec v1.5, with no
`domain_extensions` (its own docstring calls a per-step extensions dict
"the most common v1.5 failure mode") -- so `parent_step_id`/`order`/
`concurrent_order` can't just be added as fields. The plan's own fallback
was to use `TraceStepContextHelper`'s existing `Trace.metadata` hatch
instead of waiting on a governed spec change, and to bundle this with K2's
deferred step 3 (mirroring an approver onto the suspending step) into one
request rather than two.

- New `TraceStepContextHelper.set_fanout_context(step_id, *,
  parent_step_id, concurrency_ordinal, group_size=None)` -- a typed method
  alongside the existing `set_version_bundle`/`set_ipdv_context` (this is
  an SDK/platform-level concept, not a Domain Pack's, so it gets its own
  method rather than riding the pack-specific `set_domain_context` hatch
  under a fake pack_id).
- `conductor.fanout.fan_out()` gained optional `trace`/`parent_step_id`/
  `step_id_of` params. When all three are given, each item that produces
  a result (via `step_id_of(result)`) records itself as one branch of
  `parent_step_id` automatically -- a fan_out of five branches is
  reconstructible from the persisted trace as one group of five, matching
  the plan's own verify criterion directly (tested against exactly that
  scenario). All three default to `None`: unchanged from before this
  option existed. `step_id_of` returning `None` for a given result (not
  every fan_out item necessarily produces its own `TraceStep`) is skipped,
  not an error.
- K2 step 3, closed as already-satisfied rather than needing new code:
  `ConductorEngine` deliberately has no `CanonicalTrace` of its own --
  its own module docstring says that mapping "stays pack-side" (it keeps
  a generic, schema-light `ExecutedStep` record instead). K2 already put
  `approver_ref`/`authority_basis`/`approved_at` on `DurableSuspension`,
  keyed by the same `step_id` a pack's own trace already uses. A pack
  building its `CanonicalTrace` from `ExecutedStep`/`DurableSuspension`
  already has everything needed to call
  `TraceStepContextHelper.set_domain_context` itself -- no new SDK
  coupling between the engine and `CanonicalTrace` was actually missing;
  wiring one in would have crossed the engine's own stated boundary for
  no gain.
- Not done, left as the plan's own next step: raising `parent_step_id`/
  `order`/`concurrent_order` as an actual governed Schema Spec change
  request bundling K2+K10 (a cross-team conversation, not a code change).

3 new tests (test_fanout.py +3, covering the exact "5 branches, one
group" scenario, the not-all-three-params no-op case, and the
step_id_of-returns-None skip case). Full suite green (2819 passed, 3
skipped).

Kernel salvage K6: LLM invocation ledger -- correlation, status/error/
latency, and payload references, minus a redaction claim that didn't hold
up on inspection

The plan's fourth point said "reuse the existing masking discipline
(MaskingConversationStore/OutputMaskPolicy)... for [payload] redaction."
Read both before wiring anything: `OutputMaskPolicy` truncates large
tool-call outputs at *read* time so an LLM's context window doesn't
balloon -- a context-size control, not a redaction mechanism, and not
applicable to a durable write. It doesn't address the plan's own stated
concern (borrower PII in a persisted payload) at all. Also found a second,
unrelated "trace_id" already in the tree -- OpenTelemetry's
`observability.telemetry.get_current_trace_id()`, a distinct span-level
concept from `authority.context.InvocationContext.trace_id` -- and had to
pick one deliberately rather than silently picking whichever compiled
first.

- `CostRecord`/`CostRecordRow` gained `trace_id` (indexed column -- "a
  turn's LLM calls are retrievable by trace_id"), `step_id`, `status`,
  `error_class`, `latency_ms`, `request_ref`, `response_ref`. All-default
  dataclass fields, so an old row missing them still validates
  (`CostRecord(**row.data)` fills in defaults) -- no migration needed for
  existing archives.
- `CostTracker.record()` defaults `trace_id` from the ambient
  `authority.context.get_invocation_context()` when not passed explicitly
  -- chosen over OTel's `get_current_trace_id()` (a lower-level,
  observability-layer concept, not this governance ledger's) and over
  threading `TurnRun.trace_id` through several call layers (LLMManager has
  no reachable ambient access to it). `step_id` has no ambient source in
  this codebase today, so it's explicit-only.
- `LLMManager.run()` now records status="success"/"failure" with
  latency_ms on *every* call, not just successes -- previously a failed
  call (primary or fallback) left zero cost-ledger trace of the attempt
  ever happening; a new caller-visible behavior once a cost_tracker is
  configured (which is already opt-in), not a silent addition. Gained
  `trace_id`/`step_id` passthrough params.
- Actual redaction: `CostTracker` gained an optional `blob`
  (`fabric.blob.BlobStore`) param -- K5's second real customer.
  `request_payload`/`response_payload`, when given and `blob` is
  configured, are scrubbed with `jazzx_sdk.failures.redact_secrets`
  (credential-shaped text -- Bearer tokens, JWTs, key=value secrets) then
  offloaded as references, never inlined raw. Documented explicitly, not
  glossed over: this is **not** a general PII redactor -- a borrower's
  name/SSN/account number in free-text payload content passes through
  unredacted. No existing primitive in this codebase does that job; it's
  a real, separate, unbuilt gap, not something this pass closes.
- Retention: `DbCostRecordStore.clear(before=...)` already is the
  configurable-retention lever the plan asked for -- confirmed, not
  rebuilt. An ops job schedules it periodically.

14 new tests (test_cost_store.py +9, test_llm_manager_ledger.py new x5).
Full suite green (2816 passed, 3 skipped).

Kernel salvage K5: wire `fabric.blob.offload()`/`materialize()` at the two
real write boundaries -- one of which the plan misnamed

`BlobStore.offload()`/`materialize()` was implemented, documented, and
had zero callers anywhere in jazzx_sdk/ -- confirmed via grep before
touching anything. The plan named its two boundaries as "conversation-
message persistence" and "persisted tool results (K3's envelope is the
natural place)." The first checked out as named. The second didn't:
researched whether `BaseToolRegistry`/`ToolResult` (K3's envelope) is
persisted anywhere, and it isn't -- it's a pure in-memory return value to
the caller within one request, nothing writes it to a store.
`fabric/canonical/trace.py`'s `ToolCall` deliberately stores only
`inputs_digest`/`outputs_digest` (hashes, "never raw data" per its own
field docstring) -- no overflow risk there by design. The real analogue of
"a persisted tool result" is `runs/store_db.py`'s
`TurnRunEventRecord.data.event` -- a journaled stream event, one row per
delta/tool-output/done event, and that file's own `_sanitized_dump`
docstring already said as much ("a run's data column can carry arbitrary
LLM/tool output verbatim").

- `fabric/conversation_store.py::SqlConversationStore` gained an optional
  `blob`/`blob_threshold_bytes` constructor param. `append`/`supersede`
  offload each oversized message/overlay item to a `{"__blob__": ...}`
  pointer after NUL-sanitization (so the offloaded blob content is also
  NUL-free, not just what stays inline); `load`/`load_raw` materialize
  transparently -- a caller cannot tell a value was offloaded, and gets
  the byte-identical value back either way. `blob=None` (default):
  unchanged from before this option existed.
- `runs/store_db.py::DbTurnRunStore` gained the same optional params,
  scoped to `TurnRunEventRecord.data.event` only (not
  `TurnRunRecord.data`'s whole-run snapshot, e.g. `partial_output` -- a
  separate, broader concern left out of this pass, noted here rather than
  silently skipped). `append_event`'s own return value is never a pointer
  (only the row write is offloaded); `events_since` materializes.
- Also fixed, in the two files this touched anyway: a code comment in
  `conversation_store.py` (and its test file) named another repo's PR
  number -- against this session's own standing rule that code
  comments/commit messages never carry cross-repo references (CHANGELOG
  is the one place that's fine). Pre-existing, not introduced this
  session, but directly in the diff hunk being edited.
- Out of scope, noted rather than silently dropped: purging a terminal run
  (`purge_terminal`) does not delete blobs its events offloaded to --
  orphaned-blob GC is a separate concern this pass doesn't address.

10 new tests (test_fabric_conversation.py +6, test_resilient_runs.py +4).
Full suite green (2802 passed, 3 skipped).

Kernel salvage K4: durable idempotency for the queue processor, and a real
gap the plan's own "this is wiring, not building" framing missed

The plan pointed at `automation/idempotency.py`'s `IdempotencyStore`/
`EntityIdempotencyStore` as the existing durable primitive to wire in.
Checked before wiring anything: that store's value type is hard-typed to
`Receipt` -- a governed-write proof-of-side-effect record with fields
(`matrix_cell_ref`, `target_system`, `rollback_ref`, `version_bundle`, ...)
that have no meaning for "has this raw queue message ID already been
processed." Forcing queue_processor.py to construct fake `Receipt`s just to
reuse the storage mechanism would have been exactly the kind of
architecturally-unsound reuse to push back on, not build. `fabric/
idempotency.py` (the plan's other named primitive) turned out to be pure
computation (`content_fingerprint`/`WriteOutcome`), not a store at all --
nothing to wire.

- Genericized `IdempotencyStore` (Protocol), `InProcessIdempotencyStore`,
  and `EntityIdempotencyStore` in automation/idempotency.py over the stored
  value type (`Receipt` stays the default everywhere, so
  GovernedAutomation and every existing caller are byte-identical to
  before). A store now persists any pydantic model, not just Receipt.
- New `automation/idempotency_db.py::DbIdempotencyStore` -- the
  fabric.db-backed (sqlite|postgres, no Knowledge Hub round-trip) sibling
  of EntityIdempotencyStore, completing the InProcess/Entity/Db triad that
  runs.store/conductor.suspension_store already have (runs/store.py's own
  docstring says it mirrors IdempotencyStore's shape -- ironic that the
  original was itself one backend short of its own mirror). Imported
  lazily from its own module, not re-exported by automation's `__init__`,
  matching DbSuspensionStore/DbTurnRunStore's established "SQLAlchemy
  stays opt-in" convention.
- New `queue_processor.py::ProcessedMarker` (just a message_id) -- the
  right-sized value type for this use, not a repurposed Receipt.
  QueueProcessor gained an optional `idempotency_store` param (`None`
  default: unchanged, in-memory-only, the pre-K4 behavior).
  `dequeue_message` checks the in-memory set first (no I/O), then the
  durable store when configured -- catches redelivery after a restart or
  from a second worker process, which the in-memory set alone cannot.
  `delete_message` writes the durable marker after the queue delete
  succeeds; a durable-store write failure is logged loudly but does not
  turn an already-successful delete into a reported failure.
  create_queue_processor() passes the option through.
- Verified against the plan's own acceptance criterion directly: a message
  processed by one QueueProcessor instance, then a second instance (a
  restart, in effect -- fresh in-memory set) receiving the same message
  redelivered, does not reprocess it. A companion test proves the failure
  mode without a durable store configured (redelivery after a restart
  *does* reprocess), so the fix is demonstrated against a real regression,
  not just a happy path.

13 new tests (test_automation_idempotency.py new x8, test_queue_processor.py
+5). Full suite green (2792 passed, 3 skipped).

Kernel salvage K3: per-tool timeout, non-raising ToolResult envelope,
stop_on_fail -- extended to the connectors/ sibling per the plan's own
symmetry check (docs/plans/plan_kernel_salvage_hardening.md)

BaseToolRegistry.execute_request() could hang forever on a slow handler --
call_maybe_async already offloads a blocking sync handler off the event
loop, but neither branch had a bound. And execute_request()'s raise-based
contract meant a caller wanting to inspect a failure without a try/except,
or to try several tools and keep going, had nothing but the always-succeeds
execute() -> Evidence(status=UNAVAILABLE) adapter, which swallows every
failure the same way regardless of severity.

- register_tool() gained optional timeout (seconds, applied via
  call_maybe_async's existing timeout= support -- no new dispatch logic)
  and stop_on_fail (bool) kwargs. Both default to values that leave every
  existing registered tool byte-identical to before (unbounded, swallowed
  into UNAVAILABLE evidence).
- New jazzx_sdk.tools.ToolResult (ok/value/error/error_class/duration_ms)
  and BaseToolRegistry.execute_request_enveloped() -- calls the existing
  execute_request() and catches its exception into a ToolResult rather than
  reimplementing tool lookup/circuit-breaker/timeout logic a second time.
  execute_request()'s raise-based contract is completely untouched;
  existing callers and tests pass unmodified.
- execute()'s except-block now re-raises instead of degrading to
  UNAVAILABLE evidence when the failing tool was registered with
  stop_on_fail=True -- for a tool whose absence should abort the run rather
  than continue silently.
- ToolResult.from_call() is also a standalone adapter over any raise-based
  callable, sync or async -- kernel_client.py's 13+ raise sites are
  deliberately NOT rewritten to this shape (too large/risky a change to an
  already-widely-used client for this pass); a caller that wants an
  enveloped result from one of its methods wraps the call with
  ToolResult.from_call(client.some_method, ...) instead. Documented
  directly in kernel_client.py's module docstring so the omission reads as
  a decision, not a gap.
- tools/platform/workflow.py's search_process_instances() was the one of
  its 4 functions missing the found key the other 3 already carry (a real,
  narrow inconsistency, not a full envelope rewrite of all 4) -- added
  (True on a successful search, even with zero matches; False on error).
- Followed the plan's own "check the sibling family" note into
  connectors/base.py (BaseSourceConnector.fetch(), used by DiscoveryExpert)
  and found the same unbounded-call gap, worse: scan() awaits each source
  sequentially with no bound on either the async or the legacy-sync-callable
  path. Fixed at the real call site rather than adding a fetch_with_timeout
  wrapper nobody would call: DiscoveryExpert.scan() now invokes each source
  via call_maybe_async(..., timeout=config.source_timeout), a new optional
  ScanConfig field (None default: unbounded, unchanged). A timed-out source
  is caught by scan()'s existing per-source except-block and skipped like
  any other source failure -- the rest of the scan continues.

17 new tests (test_base_tool_registry_execute.py +9, test_tool_result.py
new x5, test_tools_workflow.py +1, test_discovery_expert.py +2). Full suite
green (2779 passed, 3 skipped).

Kernel salvage K2 (steps 1-2): approver identity on suspension records

DurableSuspension's resolution field was `resolution: Any` -- no approver
identity, class, timestamp, or authority basis, so "a human approved this
step -- who, when, under what authority" wasn't in the record for a SAR
filing or credit decision, only an untyped blob.

- DurableSuspension (conductor/suspension_store.py) gained approver_ref
  (ActorRef | None), authority_basis (str | None), approved_at
  (datetime | None). Reused trace.py's OverrideEvent vocabulary verbatim,
  not a second one -- ActorRef (already has actor_type="human" as a
  documented valid literal) and authority_basis: str are literally the same
  types, confirmed by a dedicated test comparing the two models' field
  annotations directly, not just similarly-named fields. Deliberately did
  NOT add a separate approver_class field the plan's own wording named --
  ActorRef.actor_type already covers that; a second flat field next to a
  typed object that already carries it would be the exact kind of
  duplicate-vocabulary problem this phase is trying to close. Also
  deliberately did NOT reuse OverrideReasonCode for an approval reason --
  checked its values (compensating_factor, missing_evidence, ...) and
  they're about why someone overrode a system output, not why someone
  approved a step; a category mismatch, not a clean fit like the other two.
- SuspensionStore.mark_resumed (Protocol + InProcessSuspensionStore +
  DbSuspensionStore) gained optional approver_ref/authority_basis kwargs;
  approved_at is set automatically when an approver_ref is supplied.
  ConductorEngine.resume_durable -- the caller-facing entry point a human
  actually calls to resolve a suspended HITL step -- threads them through.
  All additive: a suspension resumed without an approval identity (today's
  every caller) is byte-identical to before, confirmed by a dedicated
  unaffected-default test on both backends.
- Step 3 (mirror the approver onto the TraceStep that suspended) folds into
  the K10 work (next) rather than waiting on a governed schema request --
  research this session found the existing TraceStepContextHelper.
  set_domain_context hatch already covers this without touching TraceStep's
  frozen schema at all, so the "blocked on K10" framing in the original plan
  no longer applies once K10 lands via that path.
- Step 4 (conductor/engine.py's "HITL suspend is supported only for
  top-level steps" -- a Loop can't contain one) is a real, separate
  constraint, recorded here rather than fixed -- out of scope for this pass.

25 new/updated tests (test_conductor_engine.py +2, test_suspension_store.py
+5, run against both InProcessSuspensionStore and the sqlite-backed
DbSuspensionStore where applicable). Full suite green (2761 passed, 3
skipped).

Kernel salvage K1: provider-uniform retry at the Gateway (docs/plans/
plan_kernel_salvage_hardening.md), corrected against a critical read rather
than implemented as literally scoped

The plan's own suggestion ("wire RetryStrategy into LLMManager") turned out
to be wrong -- research before writing any code found FOUR retry
implementations already in the tree, not the two the plan compared:
jazzx_sdk.concurrency.retry_async/backoff_delay (generic, already used in
channels/webhook.py, channels/websocket.py, fabric/docs/store.py -- the
plan didn't know about this one), agents.models.RetryingModel
(Agents-SDK-Model-protocol-specific, hand-rolled for input-mutation and
streaming reasons that are real and don't generalize), providers/openai.py's
own _call_with_retry (fragile str(e).lower() substring matching, a third
formula), and llm/routing.py's RetryConfig/RetryStrategy (dead, zero
callers, same file as the RoutingStrategy already deprecated this session).
Wiring the dead one in, as literally suggested, would have added a FIFTH
implementation instead of consolidating.

- New jazzx_sdk.concurrency.is_transient_error(err) -- the one shared
  retryable-classification (429/5xx/408 status code, or a known transient
  exception class name), extracted from RetryingModel's own (better) private
  _is_retryable rather than openai.py's substring approach. RetryingModel
  now calls this shared predicate instead of its own copy -- confirmed
  behavior-preserving via its full existing test suite re-run unchanged.
- LLMManager gained retry_attempts/retry_base_delay/retry_max_delay
  constructor params (defaults 3/5.0/60.0 -- exactly OpenAI's own prior
  retry defaults, so existing OpenAI-only deployments see no behavior
  change). _execute_with_provider -- the one call site every provider
  (openai/anthropic/gemini/local) already funnels through for both the
  primary and fallback attempt -- now wraps provider.run() in
  concurrency.retry_async(..., retryable=is_transient_error), uniformly.
  Anthropic/Gemini/local, which had zero retry coverage before, now get the
  same coverage OpenAI always had. Composes explicitly with the existing
  HealthMonitor/failover machinery, which was already correct and needed no
  changes: retry_async only retries the *same* provider a few times for a
  blip; run()'s own primary->fallback logic (unchanged) still decides
  whether to jump to a different provider once retries here are exhausted.
- providers/openai.py's _call_with_retry (hand-rolled loop + asyncio.sleep +
  substring-matched retryable check) is gone. Renamed to
  _create_completion, now a single non-retrying call -- kept as a named
  method (not inlined) because it's still the one place a cost-optimized-
  capacity error gets classified into CostOptimizedCapacityExhaustedError
  before it would otherwise reach the new generic retry loop, which must
  never retry it (a capacity signal, not a transient blip). Confirmed
  is_transient_error correctly excludes it (not a matched status code or
  exception class name) without any special-casing needed in the retry
  wrapper itself.
- llm/routing.py's RetryConfig/RetryStrategy formally deprecated (same
  treatment as RoutingStrategy) -- confirmed zero real callers before
  deprecating, not assumed; left in place as exported public API, documented
  as superseded by LLMManager's new retry params +
  concurrency.retry_async/is_transient_error.
- Idempotency was flagged during the same critical read as looking like a
  similar "too many ways to do the same thing" problem
  (automation.idempotency.IdempotencyStore vs fabric.idempotency), but
  checked and confirmed to be two *correctly* separated concerns instead
  (caller-key request-replay vs content-hash write-dedup) -- not touched
  here; the actual fix for that pairing is queue_processor.py adopting the
  first one it currently uses neither of (a separate, still-pending item).

18 new tests (test_llm_retry.py, new file, 9 tests -- including the plan's
own three verify criteria: 429-then-success across all three providers, one
test per provider; retry-exhaustion-triggers-failover with HealthMonitor
assertions; grep-based regression proof that no hand-rolled retry loop
remains; test_concurrency.py gained 9 for is_transient_error). Full suite
green (2754 passed, 3 skipped).

UAF plan Phase 13 (final phase of docs/plans/plan_uaf_phase1_additive.md): generalize the A/B
harness to manifests, wire the >=95% PassBar gate

The last of the 13-phase UAF additive plan. Almost everything the migration
proof needed already existed (EvaluationHarness/EvaluationResults.pass_rate,
golden_cases/ with TruthMode, content-hash case-set lineage, ExperimentRun
keyed on case_set_hash, pass_bars.py's PassBar/run_corpus_eval/
CorpusEvalResult.bars_met -- literally the >=95% mechanism the PRD's success
metric asks for). The one real gap: guidance_ab.py was parameterized on a
guidance asset only (validate_guidance(asset, ...)), not on two specs or
manifests.

- jazzx_sdk/evaluation/guidance_ab.py: extracted the baseline-vs-candidate-
  on-identical-cases core into run_ab_comparison(cases, baseline, candidate,
  *, subject_id, pack_id, ...) -- baseline/candidate are each a plain
  (inputs) -> actual callable (sync or async), so what varies between arms
  (a guidance block, a manifest binding, anything) is entirely the caller's
  concern. validate_guidance is now a thin wrapper closing over the guidance
  block; its own return shape (GuidanceABResult, field name asset_id) is
  byte-identical to before -- confirmed by re-running the full existing
  guidance A/B test suite unchanged (9 tests), the regression proof for the
  extraction per the plan's own verify criterion.
- New compare_manifests(baseline_manifest, candidate_manifest, cases,
  run_turn, *, pack_id, scorer=None) -- "old assistant vs new assistant on
  the golden set" as one function call. run_turn(manifest, inputs) -> actual
  is the caller's own agent-execution call (e.g. via build_from_manifest);
  this harness only compares scored outcomes, it does not build or bind
  agents itself -- kept it a pure comparison harness rather than growing an
  execution engine. Produces two ExperimentRuns sharing one case_set_hash,
  tagged with manifest_assistant_id and content-hash version tags for both
  arms (same content_version formula manifest.store.ManifestRecord uses,
  duplicated rather than importing manifest.store into evaluation/ for two
  lines of hashing).
- Kept the per-case over_fired() flag on both the generalized ABResult and
  the unchanged GuidanceABResult -- per-case regression detection is what
  makes an aggregate pass rate trustworthy, explicitly called out in the
  plan as the part not to lose in the generalization.
- New ABResult.match_rate property (fraction of cases the candidate didn't
  regress) and check_ab_bars(result, bars=None) wiring the PRD's own ">=95%
  match" success metric as an executable PassBar gate
  (DEFAULT_AB_PASS_BAR = PassBar(metric="match_rate", minimum=0.95)) instead
  of leaving it as prose. Shares its min/max comparison logic with
  run_corpus_eval's own per-group bar check via a newly-extracted, now-public
  pass_bars.check_metric_bar(bar, metrics_dict, label=...) -- one bar-check
  implementation, not two; confirmed behavior-preserving via the full
  existing pass_bars test suite (6 tests) re-run unchanged.
- Explicitly not built, per the plan's own instruction: shadow-traffic
  teeing. SHADOW_OBSERVATIONAL exists as a golden-case label only; a real
  tee is a deployment concern with nothing in this repo to build on.

17 new tests (test_ab_comparison.py, new file, 7 tests; test_pass_bars.py
gained 4 for check_metric_bar). Full suite green (2739 passed, 3 skipped).

This closes out plan_uaf_phase1_additive.md's 13 phases (1-13, all shipped
across this and prior sessions). Two smaller adjacent items were reviewed
but deliberately not started this session: Phase 9's common/ submodule diff
is committed locally (branch reserve-reasoning-stream-event, commit
cffefc4) but not pushed upstream -- needs a human to submit it to
JazzX-LLC/common before japes' own submodule pointer can bump; and the
separate plan_kernel_salvage_hardening.md (11 more items, K1-K11) was read
and is a real, well-scoped follow-on, but wasn't authorized for execution
this session and several of its own highest-value items (K7, K9, K10)
explicitly call for a design note or governed schema approval before code.

UAF plan Phase 12: manifest store with versioning and rollback

load_manifest(path, ...) reads from a file; there was no hosted store, no
version history, and no assistant-level rollback -- the only rollback in the
repo before this was fabric.guidance.lifecycle.GuidanceLifecycle.rollback.
Yet "keep the old version warm, have a one-click way back" is a PRD Phase-1
acceptance item, and this is additive/agnostic to the still-open
manifest-vs-profile question (AssistantManifest.profile_ref already carries
the profile binding as a plain field, so no separate wrapper struct was
needed for "the (manifest, profile_ref) pair").

- Extracted load_manifest's inline aggregated-check body into a new,
  standalone jazzx_sdk.manifest.loader.validate_manifest(manifest,
  skill_registry, profile_registry=None) -- load_manifest is now a thin
  read-file + construct + call-this wrapper. Confirmed behavior-preserving:
  the full existing manifest/loader test suite (42 tests) re-run unchanged.
  This is what lets AssistantManifestStore.put run the exact same Phase 1/2
  gate against an already-constructed manifest, with no file round-trip.
- New jazzx_sdk/manifest/store.py: ManifestRecord (immutable
  record_id/assistant_id/version/manifest/supersedes/status/created_at),
  AssistantManifestStore (put/get/history/rollback) +
  InProcessAssistantManifestStore. version is a content hash via the same
  evaluation.prompt_registry.content_version fabric.guidance.GuidanceAsset
  already uses -- reusing the versioning *vocabulary*, deliberately not the
  full TransitionEngine-admitted draft/approved/deployed/deactivated state
  machine, since that machine encodes a human-reviewer approval workflow
  Phase 12 never asked for (put/get/history/rollback only). Two states
  instead: active (current head) / superseded (kept for history, never
  deleted or mutated) -- the right-sized shape for what was actually
  requested, not a copy of GuidanceLifecycle's full surface.
- Every put() always creates a brand-new record and becomes head, demoting
  the prior head to superseded -- matches the plan's own wording literally
  ("put (returns a new immutable version)"), no content-addressed dedup-on-
  put logic (GuidanceStore's own put dedupes identical-version content by
  design; that nuance wasn't asked for here and would have fought against
  rollback needing its own new record even when content is byte-identical
  to an older one). version (the content-hash tag) may legitimately repeat
  across distinct records -- e.g. a rollback to earlier identical content --
  since record_id, not version, is the true per-entry identity.
- rollback(assistant_id, to_version, *, skill_registry, profile_registry=None)
  is literally get(to_version) + put(that content) -- reruns put's full
  validation gate rather than bypassing it, since the registries a
  deployment validates against may have drifted since the content was last
  active; a rollback to now-invalid content fails loud too, not silently.
  Never mutates or deletes the version being rolled back to.
- InProcessAssistantManifestStore.put is asyncio.Lock-serialized so the
  read-current-head-then-append sequence is atomic per call -- verified with
  a real 10-way concurrent-put test (not just asserted): no two records ever
  point at the same supersedes predecessor, exactly one record ends up
  ACTIVE, and none of the 10 concurrent puts is lost.

18 new tests total (9 in test_manifest_store.py, new file; the existing
42-test manifest/loader suite re-run to confirm the validate_manifest
extraction is behavior-preserving). Full suite green (2728 passed, 3
skipped).

UAF plan Phase 10: trace the two decisions that were previously invisible
(router selection, guardrail verdicts)

Two decisions left no record: the router's skill selection
(_select_skills returns a list and records nothing -- runs only on the
agentic paths, so a skill-less assistant never routes at all) and guardrail
verdicts (_run_guardrails sets blocked/block_reason on the response and
last_guardrail_refusal, nothing durable). "Which skill and why" is the
single most-asked debugging question.

- InteractiveAgent gained a new optional tracer= constructor param
  (jazzx_sdk.observability.RunTracer, NoOpTracer default -- same pattern
  DocumentAgent already uses). Deliberately distinct from the existing
  hooks/run_hooks params: those cover the OpenAI Agents SDK's own
  agent/llm/tool span tree via MlflowTraceHooks, which only fires inside the
  SDK's own Runner loop -- routing and guardrails both run as plain Python
  calls outside that loop entirely, so they need RunTracer's separate,
  simpler per-turn span path (observability/run_tracer.py) instead. No
  wiring into MlflowTraceHooks was needed or attempted.
- _select_skills emits one span per turn (f"{spec.name}:route") carrying the
  router name, the candidate set (spec.skills), and the chosen skill(s).
  Confidence is deliberately NOT recorded: the Router protocol's select()
  returns only list[str] | None with no slot for a score
  (_IntentFirstRouter computes one internally but never surfaces it) --
  extending that protocol's return shape is a separate, bigger change this
  phase does not make. The span carries what's actually available rather
  than inventing a field.
- _run_guardrails emits one span per guardrail *evaluated*, not just the one
  that blocks (f"{spec.name}:guardrail:{name}"), carrying guardrail name,
  phase, whether it blocked, and (when the check returned a typed Refusal)
  its reason_class -- so a guardrail verdict is durable even when it
  *passed*, not just when it refused.
- New jazzx_sdk/agents/interactive/tracing.py: interactive_name_patterns(),
  mirroring agents/adjudication/tracing.py's adjudication_name_patterns()
  exactly (same precedent: mlflow_bridge's span_type-keyed mode_map can't
  distinguish two spans of the same generic kind). route spans map to
  CONDUCTOR (EXECUTE-layer orchestration/dispatch), guardrail spans to
  SENTINEL (TRUST-layer monitoring). No change needed to mlflow_bridge.py
  itself -- name_patterns was already the extensibility seam.
- New jazzx_sdk/observability/trace_routes.py: trace_router(canonical_objects=...)
  -- a read-only GET /traces/{trace_id} route on a GovernedRouter, mirroring
  runs/server.py's shape exactly. Lookup only, deliberately -- a write path
  would prejudge the still-open trace-format-of-record question. 404s
  cleanly on a miss. Not imported from observability/__init__.py (same
  eager-import discipline as runs/server.py/trace_source -- fastapi and
  fabric.canonical stay off the `import jazzx_sdk` path); import by full
  path.
- TraceStep (fabric/canonical/trace.py) intentionally untouched -- frozen at
  Schema Spec v1.5, extra="forbid", no domain_extensions by design. Nothing
  in this phase needed to touch it; all three deliverables land through the
  existing span/name-pattern/lookup seams.

13 new tests (test_interactive_tracing.py, test_interactive_agent_tracing.py,
test_trace_routes.py -- new files). Full suite green (2719 passed, 3
skipped).

UAF plan Phase 9: reserve the reasoning stream event (prep only, needs a
human to submit upstream)

StreamEventType (common/core/streaming/models.py) has eight members and no
reasoning/thinking event; tool streaming is already fully built on the japes
side (stream_hooks.py, streaming/publisher.py, sse_reader.py, journal
resume), so only the event type itself was missing from the shared
vocabulary. The catch, stated in the plan itself: StreamEventType lives in
common/, a git submodule pointing at a separate JazzX-LLC/common repo with
other consumers -- adding a member there is a shared-package change, not a
japes-local one, and needs upstream coordination this session can't do
alone.

- Added StreamEventType.reasoning + a new ReasoningEvent class (same shape as
  LLMChunkEvent -- a text delta) to common/core/streaming/models.py, exported
  from common/core/streaming/__init__.py, added to the StreamEventModel
  discriminated union. 4 new tests in common/tests/streaming/test_models.py
  (round-trip, dict-resolution, and a regression test proving the existing
  eight members are unaffected). Nothing in jazzx_sdk/ emits it yet, matching
  the plan's own "reserve API space" framing -- deliberately not wired into
  japes' own ToolStreamHooks/InteractiveStreamEvent in this pass.
- **Committed locally within the common/ submodule's own git history only**,
  on a new branch (reserve-reasoning-stream-event, commit cffefc4) --
  NOT pushed to JazzX-LLC/common, and japes' own submodule pointer is
  deliberately NOT bumped (`git status` at the japes root shows common as
  locally modified/dirty, nothing staged or committed here). This diff needs
  a human to review, open against JazzX-LLC/common, and land there before
  japes' submodule pin can be bumped to reference a real, shared commit.
- Symmetry check run before finishing: no other file in jazzx_sdk/ depends
  on StreamEventType/StreamEventModel beyond streaming/publisher.py and
  streaming/__init__.py (both re-export only, no behavior depends on the
  member count), so this addition is safe against the rest of the japes tree
  as-is, independent of whether/when it lands upstream.

Full japes suite + the 4 new common/ tests together: 2725 passed, 3 skipped.

UAF plan Phase 8: session lifecycle (SessionStore + Reaper-shaped sweeper)

Conversation *content* handling was already ~80% there (ConversationStore
variants, durable SqlConversationStore, CompactionPolicy, resumable durable
SSE with cooperative stop). Missing: the session *record* -- session_id is
caller-supplied with no created_at/last_active_at, no TTL, no expiry, no
resume signal.

- New jazzx_sdk/agents/interactive/session.py: SessionRecord
  (session_id/conversation_id/created_at/last_active_at/status), SessionStore
  Protocol (create/touch/get/expire/reap_stale) + InProcessSessionStore, and
  SessionReaper -- deliberately copying runs/dispatcher.py's Reaper shape
  exactly (sweep()/run_forever() over a store's own reap_stale) rather than
  inventing a second sweeper design. Deliberately a separate store from
  ConversationStore, not folded into it -- a session is lifecycle metadata, a
  conversation is content; SqlConversationStore has no timestamps of its own
  on purpose, this is where they belong.
- expire() is a state transition (status -> EXPIRED), never a delete or
  mutation of conversation_id/created_at -- the audit trail survives. touch()
  never revives an already-expired session (returns None), so a caller's own
  get()/touch() result is the resume-vs-fresh-conversation signal ("Resume =
  get on a live session returning its conversation id").
- reap_stale fencing mirrors InProcessTurnRunStore's own reap_stale exactly:
  each session's staleness is re-checked fresh, immediately before its own
  write, not against a snapshot captured at sweep-loop start -- guards the
  same production race (a concurrent touch() landing during an earlier
  iteration's yield point must not be reaped off stale data). Regression test
  for this race included, mirroring the existing TurnRunStore one.
- No new caller wires this in yet -- SessionStore/SessionReaper are additive,
  standalone, opt-in. "Default configuration changes no existing test" holds
  trivially: nothing existing constructs one. Only an in-process backend
  ships (matching TurnRunStore's own InProcess/Db split) -- a fabric.db-backed
  durable variant is a documented, not-yet-built extension point, since
  nothing in this phase's verify criteria requires durability.

14 new tests (test_session_store.py, new file). Full suite green (2709
passed, 3 skipped).

UAF plan Phase 7 (conservative scope): de-hardcode the agentic path's model
literal, deprecate the unused RoutingStrategy

Scoped deliberately narrower than the plan's literal ask, per an explicit
decision made before starting (docs/plans/plan_uaf_phase1_additive.md's own
Phase 7 asks for the agentic path's model *calls* to route through LLMManager
for CostTracker/failover coverage). Investigated first: today's agentic path
builds a real OpenAI Agents SDK Agent via OpenAIProvider's own bare
AsyncOpenAI client, completely bypassing LLMManager -- and there is no
adapter anywhere between LLMManager's call shape (prompt/system_prompt/
messages -> one completion) and the Agents SDK's Model protocol (a
tool-calling loop, streaming, structured output natively integrated with
Runner). Building one is a real, materially larger change to every
skill-based turn's live execution path for every consumer. Given this was
going to land unsupervised, went conservative: de-hardcode the literal only,
document the gap explicitly, leave the real Model-adapter build as flagged
future work rather than rushing it through.

- New jazzx_sdk.agents.models.resolve_agent_model_name(spec_model, *,
  gateway=None, task_type="agentic", default="gpt-5.2") -> str. Replaces the
  three independent `self.spec.model or "gpt-5.2"` literals in
  agents/interactive/agent.py (parent agent build, sub-agent skill build, and
  ResponsesCompaction's model). Precedence: spec_model always wins (unchanged
  from before); else, when a gateway (LLMManager) is wired and its
  task_routing names "openai" as the primary provider for task_type, that
  provider's PROVIDER_DEFAULT_MODEL entry; else the same "gpt-5.2" literal as
  before. With no spec.model and no gateway wired (today's every existing
  caller), byte-identical to the code it replaces -- confirmed via the full
  existing interactive-agent suite re-run unchanged, not just asserted.
- New public properties closing the read-access gap this needed:
  LLMManager.task_routing (read-only copy of the configured routing table,
  mirroring the existing health_monitor/cost_tracker property convention) and
  AgentExecutionService.llm_manager (mirrors .openai/.anthropic). Both
  additive, zero behavior change for any existing caller.
- llm/routing.py's RoutingStrategy formally deprecated in favor of
  LLMManager.task_routing, resolving a reconciliation the module's own
  docstring had left open ("settle which is the intended surface before a
  client builds against this module"). Confirmed zero real callers of
  RoutingStrategy anywhere in jazzx_sdk before deprecating, not assumed --
  left in place (exported public API a downstream consumer may already
  import) but documented as superseded, so no third routing model gets
  written against it later. RetryConfig/RetryStrategy in the same file are a
  separate, unrelated concern and not touched by this note.
- gpt-5.2 literal confirmed zero remaining occurrences in the three files
  Phase 7 named (agent.py/service.py/factory.py) -- a regression test greps
  for it. Deliberately NOT extended repo-wide: ReasoningAgent, the
  AdjudicationAgent chassis, EvolveMode's evaluator, and
  OpenAIProvider.build_agent's own default parameter each carry their own
  independent "gpt-5.2" default and are outside Phase 7's named scope --
  left untouched rather than folding an unrelated, unreviewed change into
  this pass.

14 new tests (test_agent_models.py, tests/agents/test_service.py,
test_llm_provider_routing.py, test_interactive_agent.py -- including one
exercising a real LLMManager wired end-to-end through InteractiveAgent and
asserting the resolved model reaches the actual build_agent call). Full
suite green (2695 passed, 3 skipped).

UAF plan Phase 1: manifest name/description, is_conversational, persona
cross-validation, softened mandatory-skills gate

The last of the manifest-track UAF phases (docs/plans/plan_uaf_phase1_additive.md),
done out of the plan's own suggested order since Phase 4 (already shipped,
decoupled) and Phase 12 (next) both depend on it.

- AssistantManifest gained two required fields: name (human display; assistant_id
  stays the machine identifier) and description (the prompt that drives routing,
  out-of-scope handling, and agents.interactive.recommend's skill recommender --
  both required, no sensible default for either). Breaking for any existing
  AssistantManifest(...) construction that omits them -- every test fixture in
  this repo constructing one (4 test files, 1 YAML fixture) updated.
- New AssistantManifest.is_conversational property, delegating to a single
  CONVERSATIONAL_SURFACES constant. Moved from spec_binding.py (private
  _CONVERSATIONAL_SURFACES) to manifest/surface_types.py to avoid a manifest ->
  spec_binding import cycle (spec_binding already imports AssistantManifest at
  module level) -- spec_binding._apply_surface_defaults now imports the same
  public constant rather than defining its own, so there remains exactly one
  definition of "conversational," not two.
- load_manifest cross-validates primary_persona against the resolved profile's
  persona (only when profile_registry is given): primary_persona set but the
  profile has none now raises, naming both. Previously a dead field -- nothing
  in the SDK read it.
- Mandatory-skills gate, deliberately NOT the plan's literal "allowed_skills must
  always be non-empty" -- InteractiveAgentSpec's own docstring designs for a
  skills-less, single-shot grounded-Q&A shape, and the literal gate would have
  broken that pattern for every existing zero-skill manifest. Softened to two
  narrower, concretely-justified signals instead: an ORCHESTRATOR archetype
  (whose entire purpose is directing other skills/sub-agents) declaring no
  allowed_skills at all (checkable without a profile_registry), and, when one is
  given, a resolved profile that itself declares spec.skills but ends up with
  none of them allowed by the manifest -- a real mismatch, not a legitimate
  skills-less design. A SPECIALIST/etc. manifest with allowed_skills=[] and a
  skills-less profile is still accepted.

33 new tests (test_assistant_primitives.py); ~20 existing manifest-construction
call sites across 4 test files + 1 YAML fixture updated for the two new
required fields. Full suite green (2681 passed, 3 skipped).

UAF plan Phase 3 + Phase 4: skill record metadata, build-time skill recommender

Two more priority-sequenced phases from the 13-phase UAF additive plan
(docs/plans/plan_uaf_phase1_additive.md). Note on sequencing: Phase 4's own
spec lists it as depending on Phase 1 (manifest name/description) as well as
Phase 3; Phase 1 hasn't been built yet (an earlier session prioritized 2 and
11 first). recommend_skills() below takes description/persona as plain string
arguments rather than pulling them from AssistantManifest, so the capability
ships now, decoupled from Phase 1 -- wiring manifest.description through is a
trivial follow-up once Phase 1 lands, not a redesign.

Phase 3 -- Skill (spec.py) gained five metadata fields, declared only, none of
them touching execution: version (a stable, comparable version identifier;
"new versions don't break old ones" was unrepresentable without it),
visibility (roles that may see/attach the skill; None = visible wherever the
registry is visible, today's behavior for every existing registration),
invokes (explicit statement of what's behind the skill -- previously only
implied by which of tools/spec_ref/mcp_servers was populated), and
inputs/outputs (JSON Schema, optional and unvalidated at runtime in this
phase -- exist so a catalog/docs generator has a source; nothing reads them
yet). _build_parent_tools (agent.py) is unchanged -- confirmed via `git diff
--stat`, zero lines touched, per the plan's own acceptance criterion.

- SkillRegistry.names() gained an optional roles= kwarg (default None -> no
  filtering, byte-identical to today) implementing the visibility filter;
  catalog_text() appends "(vX, invokes=Y)" only when a skill actually
  declares those fields, so a skill declaring neither renders byte-identical
  to before this phase (confirmed against the existing exact-string test).
- SkillInventory/build_inventory surface all five new fields for a
  sub_agent-kind skill; a bare-name tool-kind skill has no Skill object to
  read them from, so they stay None there, matching existing behavior for
  that branch.
- New skill asset channel on packs: PackManifestLoader.skills() (inline list
  or a relative-path YAML file, mirroring evidence_types() exactly -- same
  convention, not a second one), FRAGMENT_KINDS gained "skills", and
  merged_assets() now supports kind="skills" (id field "name") through the
  same fragment-scoped, provenance-stamped, collision-fail-loud merge every
  other kind already uses. New Pack.skills property mirrors Pack.evidence_types.
  Deliberately distinct from an agent's own skill_defs (Pack.agent's
  InteractiveAgentSpec.from_dir already loads those) -- these are pack-level
  importable declarations another pack can pull in via depends_on/fragments,
  not one agent profile's resolved catalog.

36 new tests (test_interactive_agent.py, test_skill_registry.py,
test_pack_composition.py, test_pack_manifest_loader.py); one existing
exact-set test (test_fragment_kinds_constant) updated for the new fragment
kind.

Phase 4 -- new jazzx_sdk.agents.interactive.recommend module:
recommend_skills(llm, *, description, persona, registry, allowed=None,
roles=None, model=None, prompt=None) -> RecommendationResult. Same shape as
router.py's _IntentFirstRouter (one structured LLM call over
SkillRegistry.catalog_text) with a different input (description/persona
instead of a per-turn query) and a different lifecycle (build-time, not the
turn's hot path). Deliberately not a Router -- sharing that protocol would
put a build-time concern in the turn loop, which router.py's own docstring
already argues against; shares catalog_text's rendering and the
structured_call pattern instead, not the protocol.

- RecommendationResult carries both `ranked` (score + one-line rationale per
  skill, from the LLM) and the full `catalog` (every name the caller's
  roles/allowed filters admit) -- "View all skills" is always available,
  never a filtered-down set standing in for the catalog.
- roles= threads straight into SkillRegistry.names()/catalog_text() (Phase
  3's visibility filter) before the LLM ever sees the catalog, so a
  role-invisible skill is never in the prompt; the ranked list is additionally
  filtered against the same role-filtered name set as a second guard against
  a hallucinated skill_name the LLM might still produce. An empty
  (post-filter) catalog short-circuits to an empty result with no LLM call at
  all.

6 new tests (test_skill_recommender.py, new file), including rank order via
ScriptedLLM, a role-invisible skill never appearing in either the ranked or
full list, and the full catalog always being returned alongside the ranking.

62 new/updated tests total across both phases. Full suite green (2673 passed,
3 skipped).

UAF plan Phase 5 + Phase 6: always-on safety-floor guardrail, configurable
out-of-scope handling

Two more priority-sequenced phases from the 13-phase UAF additive plan
(docs/plans/plan_uaf_phase1_additive.md).

Phase 5 -- an assistant could previously deploy with no guardrail but the
keyword-matched manifest scope check (spec.guardrails defaulted empty; bind_spec
force-injected only the scope guardrail's name). New always-on platform-tier
safety floor closes that:

- jazzx_sdk.agents.interactive.safety: new SAFETY_FLOOR_GUARDRAIL_NAME
  ("platform_safety_floor") and build_safety_floor_guardrail(*, check=None) --
  a real, enforced Guardrail, deliberately distinct from the module's existing
  SAFETY_INSTRUCTIONS/with_safety (prompt text, never enforced; the module
  docstring now states the distinction explicitly so the two are never
  conflated). check= is the seam for an external moderation/red-teaming
  gateway (same GuardrailCheck contract registry.llm_guardrail already
  demonstrates); with none supplied, the check never blocks -- the floor is a
  structural guarantee only, since no gateway ships in this repo. Wiring a
  real one in later is a one-line change to this call's check=, not new
  framework plumbing -- the gateway integration itself stays a separate,
  future deliverable, not built here.
- manifest.spec_binding.bind_spec: force-prepends SAFETY_FLOOR_GUARDRAIL_NAME
  onto both guardrails["input"] and ["output"] (ahead of the scope guardrail),
  via a new shared _prepend_guardrail_if_missing helper (also now used for the
  scope guardrail's own prepend, replacing near-duplicate inline logic). No
  AssistantManifest field opts out -- the absence of one is the guarantee.
- manifest.spec_binding.build_from_manifest: new _ensure_safety_floor_registered
  (mirrors the existing _ensure_scope_guardrail_registered's shape) registers
  the built Guardrail into the catalog at tier 1 -- registry._TieredRegistry
  already refuses a less-trusted tier registering over a more-trusted name
  unless allow_override=True is passed explicitly; this is the first caller
  that actually uses tier=1.
- The one behavior change in this plan, as flagged by the plan itself: every
  existing manifest-bound consumer now gains this guardrail (structurally
  present, never blocks without a configured gateway). Two existing tests
  asserting exact guardrails["input"] contents updated for the new
  floor-first ordering.

Phase 6 -- the shipped scope-guardrail default was weaker than assumed:
case-insensitive substring matching against out_of_scope_action_classes that
defaults to allow when nothing matches, model= accepted and silently ignored,
decline text hardcoded. "A mortgage assistant never answers what's the
weather" did not hold.

- jazzx_sdk.agents.interactive.scope.build_scope_guardrail: new decline_message/
  redirect_target/llm params. decline_message, when set, replaces the built-in
  decline text verbatim on both the keyword-match and LLM paths; redirect_target
  replaces the Refusal.remediation field's built-in text. llm (a real
  LLMManager or a ScriptedLLM) routes the check entirely through
  registry.scope_guardrail (the existing LLM-backed, description-driven
  variant, reasoning about in_scope as the allowed-topic list) instead of the
  default keyword match, with model then selecting that call's model. Passing
  model without llm now raises at build time -- silently ignoring an unusable
  model (the old behavior) was worse than failing loud. All four params
  default to None/absent, reproducing today's exact text and keyword-match
  behavior unchanged. The module docstring now states the fail-open-to-allow
  default explicitly as a known, deliberate weakness rather than leaving it
  implicit -- flipping to deny-by-default would be a real behavior change for
  every existing consumer and isn't done here.
- jazzx_sdk.manifest.assistant_manifest.AssistantManifest: three new optional
  fields (all None by default, preserving today's behavior exactly) --
  out_of_scope_decline_message, out_of_scope_redirect,
  out_of_scope_check_model. manifest.spec_binding._ensure_scope_guardrail_registered
  forwards all three into build_scope_guardrail, plus a new llm= param peeked
  (not popped) from build_from_manifest's **extra["llm_manager"] the same way
  store= already is -- so a manifest declaring out_of_scope_check_model but
  built without an llm_manager= raises at build time rather than silently
  falling back to keyword matching.

26 new tests (test_safety_floor.py new; test_interactive_scope.py grew from 5
to 17). Full suite green (2651 passed, 3 skipped).

UAF plan Phase 2 + Phase 11: manifest silent-degradation, InvocationContext at
every service entry point

Two priority-sequenced phases from the 13-phase UAF additive plan
(docs/plans/plan_uaf_phase1_additive.md), chosen because both are live
correctness/security bugs rather than feature gaps.

Phase 2 -- jazzx_sdk.manifest.loader.resolve_pack no longer degrades silently.
Previously: a missing pack_id logged a warning and returned None (every caller
had to remember to null-check); an out-of-range pack_version_range logged a
warning and returned the pack anyway; an unparseable pack_version_range (e.g. a
typo) fell all the way through the except InvalidSpecifier branch and returned
the pack with the version constraint never evaluated at all -- the sharpest of
the three, since nothing about it looked like a failure. All three now raise
ValueError naming the assistant, pack, and (where relevant) the offending
range -- a manifest bound to a pack is a deploy-time gate, not a lookup a
caller null-checks. 3 tests rewritten from *_returns_none to *_raises, 1 new
test for the invalid-specifier path (17 passing in
test_assistant_primitives.py; 41 across the broader manifest suite).

Phase 11 -- an unauthenticated HTTP call path previously reached
authority.context.admit_hop's fail-open branch (no ambient InvocationContext
-> admitted) with nothing at any entry point requiring one be established
first. The authorization primitives themselves (PermissionScope.admits/narrow,
InvocationContext, check_hop, admit_hop) were already correct and already used
at real call sites (_check_turn_entry, _build_parent_tools,
_build_composed_skill_tool) -- the gap was purely that no entry point ever
built the context admit_hop/check_hop check against.

- jazzx_sdk.handlers: extracted _decode_security_context_value(sc) as a pure
  helper from _decoded_security_context's decode loop (zero behavior change --
  confirmed via the existing 31-test identity/RBAC suite re-run unchanged), and
  added identity_from_headers(headers) -- the same
  x-security-context-first/x-user-*-fallback resolution order as
  get_current_user_id/email/name, parameterized for an explicit header mapping
  (a live request's own headers) instead of the ambient ContextVar path those
  three read. The three existing accessors are deliberately left as-is, not
  unified onto this -- their ambient-priority chain (live request > manual
  security_context > restored propagated headers) differs meaningfully from a
  one-shot explicit-mapping resolution, and unifying them was judged too risky
  given how widely they're relied on for RBAC.
- jazzx_sdk.authority.context: PermissionScope.unrestricted() classmethod
  (resource_selectors=[""] -- "" is a prefix of every string, so it admits
  unconditionally via the existing _matches_any/startswith("") mechanics; no
  new matching logic invented). New build_invocation_context_from_headers(
  headers, *, actor_class="human", permission_scope=None) -- the shared
  entry-point constructor: resolves identity via handlers.identity_from_headers,
  returns None when nothing resolves (caller decides what that means), defaults
  permission_scope to unrestricted() since an authenticating entry point has no
  selector grammar of its own to narrow by yet.
- jazzx_sdk.server.app.ServerSettings: new require_identity: bool = False.
  Opt-in, not on by default -- jaci's own japesClient.ts sends identity headers
  as a caller-supplied option, not unconditionally on every call today, and the
  same is true for other consumers as far as could be confirmed from this repo
  alone; flipping the flag on is a per-deployment decision once that
  deployment's callers are confirmed to send identity. When True, new
  middleware on create_app() rejects any request other than /health with 401 if
  it carries no identity headers, and establishes an InvocationContext for the
  request's duration (set/cleared around call_next, mirroring
  ResilientRunner's existing set/get/clear pattern) when it does. Also
  registered common.middleware.context_headers.HeaderMiddleware in create_app
  unconditionally (non-rejecting -- it only populates a ContextVar) -- a
  pre-existing comment in the /invoke handler claimed inbound identity headers
  "are already captured by common's HeaderMiddleware"; grepped the whole repo
  and confirmed that middleware was never actually registered anywhere, so
  handlers._default_request_headers's primary source (and therefore RBAC
  forwarding to Knowledge Hub) was silently getting nothing from it for any app
  built via create_app alone. Fixed as a safe, additive, in-scope correction
  rather than deferred, since it only closes a gap the existing comment already
  assumed was closed.
- jazzx_sdk.server.governed_http.GovernedRouter: matching require_identity:
  bool = False constructor param, same opt-in default, enforced inside the
  existing governed() dependency's try/finally alongside
  set_governed_context/clear_governed_context -- covers runs/server.py's
  /runs routes the same way ServerSettings.require_identity covers the plain
  /invoke path.
- admit_hop's fail-open semantics when no context is ambient at all are
  deliberately unchanged -- it's the documented opt-in wrapper in-process
  library callers depend on; fixing the entry point removes the exposure
  without breaking them, per the plan's own explicit instruction.

19 new/updated tests across test_server.py (TestRequireIdentity),
test_governed_http.py, test_invocation_context.py
(TestBuildInvocationContextFromHeaders + unrestricted()), and
test_identity_propagation.py (identity_from_headers). Full suite green (2631
passed, 3 skipped).

DocumentAgent: downloadable/blob sources, one-call front door

Closed three source-description gaps in DocumentAgent's existing conductor-routed
pipeline (DocTurn/run_document), after confirming how much of the "fat agent" shape
(spec + turn, mirroring InteractiveAgentSpec + respond()) it already had -- most of
it: DocumentAgentSpec (policy: taxonomy, confidence floors, template mapping,
YAML-loadable), and DocTurn already unified a folder/KH-collection/standalone-zip
into one auto-routed "collection" branch over process_dir's incremental,
manifest-cached, concurrent-fan-out machinery. Template-if-available routing
(route_template) was also already correct -- confirmed, not changed.

- jazzx_sdk.tools.documents.local: new download_to_file/download_files -- raw-bytes
  downloads sharing read_from_url's SSRF guard. Extracted the shared, per-redirect-
  hop-validated GET into a private _safe_fetch both functions build on (read_from_url
  itself unchanged in behavior; its own SSRF test suite re-run unchanged as
  confirmation). Concurrent downloads use the same jazzx_sdk.conductor.fan_out
  primitive process_package's segment fan-out already uses; a failing URL is skipped
  (degrade=True) rather than sinking the batch. Filenames: the response's
  Content-Disposition filename if present, else the URL path's basename --
  Path(...).name strips any embedded path components first, so a malicious
  filename="../../etc/passwd" header can't escape the destination directory.
  Collisions get a short URL-hash suffix. Re-exported from jazzx_sdk.tools.
- DocumentAgent.materialize_blob_to(pointer, dest, *, filename): durable
  blob-to-file materialization -- the counterpart to the existing process_blob,
  which only ever materializes to a temp dir for the duration of one process() call.
- DocTurn gained urls: list[str] and blob_pointers: dict[str, str] (pointer ->
  filename; required per-pointer since a blob key carries no extension and
  convert_document routes on it). Both auto-route to the existing "collection"
  branch in detect_step; process_collection_step materializes them into a scratch
  dir (fan_out-bounded by turn.concurrency) before delegating to the unchanged
  process_dir. A downloaded .zip is unpacked by process_dir's existing
  include_zips handling for free -- no new zip logic needed.
- DocumentAgent.run(turn: DocTurn, *, tracer=None, on_step=None, detect=None,
  **pipeline_kwargs): one-call front door wrapping build_document_pipeline +
  build_document_components + run_document, mirroring InteractiveAgent.respond()'s
  ergonomics (today's alternative is three separate calls). Locally imports
  pipeline.py inside the method to avoid a circular top-level import (pipeline.py
  already imports unpack_zip from agent.py).

Designed in plan mode first given the multi-file scope; plan preserved at
~/.claude/plans/atomic-doodling-sun.md. 25 new tests (test_download_files.py new;
additions to test_document_pipeline.py, test_document_agent.py). Full suite green
(2612 passed, 3 skipped).

run_with_recovery -- schema-validation/truncated-output/API-status retry for a
caller that builds its own Agent

InteractiveAgent had none of run_agent's recoverable-failure handling
(ModelBehaviorError / IncompleteOutputError / APIStatusError) because it builds its
own Agent (skills-as-sub-agents) and calls Runner.run() directly instead of going
through run_agent, which owns Agent construction itself. Confirmed by reading the
code, not assumed: InteractiveAgent._respond_agentic called Runner.run() with zero
exception handling for any of the three; a schema-validation failure propagated
straight up uncaught.

- New jazzx_sdk.agents.run_kit.run_with_recovery(run_once, *, feedback, name,
  max_retries=3, on_retry=None): the same retry mechanism as run_agent
  (ModelBehaviorError feedback-and-retry, IncompleteOutputError feedback-and-retry,
  APIStatusError backoff) over a caller-supplied run_once()/feedback() instead of
  owning Agent construction. Deliberately does not retry MaxTurnsExceeded --
  recovering from that needs rebuilding the Agent with different tools/query, which
  isn't this primitive's job when the caller already owns construction; stays
  run_agent-only.
- run_agent's own two feedback-message bodies (schema-validation / truncated-output)
  extracted into shared _model_behavior_feedback/_incomplete_output_feedback helpers
  so wording can't drift between the two entry points. run_agent's control flow and
  retry-counting semantics are otherwise untouched -- its existing 33 tests re-run
  unchanged, confirming the refactor is behavior-neutral.
- Wired into InteractiveAgent._respond_agentic: feedback appends the retry message to
  the active session when one exists, or to the input list directly when the call is
  stateless (no conversation). Composes with the existing context-window-overflow
  fallback as the inner retry (schema/truncation/status) under the outer one
  (compaction + one retry). Not wired into _stream_agentic, which already documents
  why: can't retry after partial output has started streaming to the caller.
- Checked DocumentAgent: needs no change. Its classify/extract already route through
  AgentExecutionService -> OpenAIProvider's no-tools/single-message fast path ->
  run_agent, so they already get this retry. run_with_recovery exists for whenever
  it (or a future agent) builds its own Agent directly the way InteractiveAgent does.

jazzx_sdk.__all__ (via jazzx_sdk.agents) gained run_with_recovery. 8 new tests in
test_agents_run_kit.py, 2 in test_interactive_agent.py (stateless + active-session
retry proven through respond() itself, not just the primitive in isolation). Full
suite green (2597 passed, 3 skipped).

Sanitize NUL bytes at every JSON-column SQL write boundary; add call_maybe_async

fabric.entities already sanitized (strip_nulls) at its write boundary; audited every
other mapped_column(JSON) store in jazzx_sdk and found six more that didn't --
SqlConversationStore, DbFeedbackStore, DbPromptRegistry (sanitizes before hashing so
version stays consistent with what's stored), DbSuspensionStore, DbTurnRunStore (seven
internal call sites collapsed onto one _sanitized_dump helper), DbAgentDefinitionStore,
and DbCostRecordStore's one open metadata field. All seven now strip NUL bytes (real or
escaped-literal-text) before writing -- Postgres text/jsonb reject the raw byte outright.

New jazzx_sdk.concurrency.call_maybe_async(fn, *args, timeout=None) decides sync-vs-async
before invoking a caller-pluggable callable (never calls it eagerly), offloads a sync
callable off the event loop, and uniformly times out either branch. Replaced twelve
hand-rolled isawaitable/iscoroutinefunction dispatch sites with it across tool/scorer/
document/interactive-agent/evaluation call sites, including conductor/engine.py's step/
guard/loop-convergence dispatch -- the core path every pack conductor run goes through,
where the old eager-call shape let a blocking sync component or observer stall the loop
before on_step_timeout ever got a chance to bound it. Removed the now-dead _maybe_await
helper and simplified _emit_step_event's timeout branching in the same pass.

## [2.4.1] - 2026-08-13

**Mode chassis plan complete (all 7 phases), a new `jazzx_sdk.pipelines` home for
japes' "reference pipeline" family, and two portable cross-instance
primitives.** `Curator.synthesize_bucket` migrated onto `ReasoningAgent` --
the last cognitive mode still bypassing it -- alongside `TurnRunStore.
latest_run()` (reconnecting-caller state) and a generic bundle/publish
primitive for cross-instance promotion (`jazzx_sdk.manifest`). Plus a
symmetry pass triggered by consolidating `chat.py`/`document/pipeline.py`
into `jazzx_sdk/pipelines/`: closed a three-way "pipeline.py" naming
collision across the SDK and brought `DocumentAgentSpec` in line with its
sibling fat-agent families.

Collapse six duplicate `_reasoning` lazy-property copies into `BaseMode`; derive
`platform_catalog.MODES` from `modes.catalog.MODE_REGISTRY`

The identical lazy `_reasoning` property (plus its identical justification comment)
was independently declared in `VerifierMode`, `InvestigatorMode`, `GovernorMode`,
`ReasonerMode`, `NarratorMode`, and `EvaluatorMode` -- six copies of "construct the
`ReasoningAgent` on first use, not at `__init__` time." Moved to `BaseMode` once:
a `ctx: HandlerContext | None = None` class attribute, `self._reasoning_agent = None`
in `__init__`, and one `_reasoning` property reading `self.ctx.runtime.agents` /
`self.api_model_name`, raising a clear `RuntimeError` if `ctx` is unbound instead of
an opaque `AttributeError`. Deleted all six copies. Pure deduplication -- the full
mode test suite (239 tests) passes unchanged.

`platform_catalog.MODES` was a third, unlinked copy of "what modes exist," hand-
maintained alongside `modes.catalog.MODE_REGISTRY` and `fabric.canonical.trace`'s
`TraceStepMode` enum -- three lists that could silently drift. `MODES` now derives
its key set and descriptions from `MODE_REGISTRY` directly; only the emoji/display-
name presentation layer (which `MODE_REGISTRY` doesn't carry) stays a local dict.
`TraceStepMode` stays a separate enum rather than importing `modes` into it --
`trace.py` is a canonical-object module, and that edge would add an undocumented
cycle risk into `fabric.canonical` -- so a new test asserts the two stay set-
identical instead of deriving one from the other. Checked `jaci/ui/platform_view.py`'s
try/except-fallback import of seven `platform_catalog` symbols: every name it
imports is still exported unchanged.

2 new tests in test_platform_catalog.py (MODES tracks MODE_REGISTRY;
TraceStepMode/MODE_REGISTRY set-identity). Full suite green (2838 passed, 3 skipped).

`Curator.synthesize_bucket` migrated onto `ReasoningAgent` -- the last of the seven cognitive
modes still bypassing it

`synthesize_bucket` (Curator's Layer 2 LLM synthesis step) called a bare `llm.run()` via
`jazzx_sdk.llm.structured_call` -- no retry, no truncation handling, no token accounting, the
same gap `EvaluatorMode` had before its own v2.4.0 migration. Added `agents:
AgentExecutionService | None` alongside the existing `llm: Any | None` (both now optional;
exactly one must be given, enforced with a `ValueError`). The `agents=` path constructs a
`ReasoningAgent` and routes through `name=f"curator:synthesize:{tag}",
output_type=_SynthesizedGuidance` -- the same retry-with-feedback-on-schema-failure and
truncation-retry handling the other six modes have, plus real token usage, recorded on the
returned asset's `metadata["tokens_used"]` (nowhere else to put it -- `GuidanceAsset` has no
dedicated usage field, and inventing one for a single caller wasn't warranted). The `llm=` path
stays for one release, now emitting a `DeprecationWarning` -- jaci's
`scenarios/ci_spread/demo_correction_to_guidance.py` and `tests/unit/test_hitl_approval.py` both
call it and are left unmigrated deliberately; the deprecation window is exactly for callers like
that.

5 new tests in test_curator_synthesis.py: the `agents=` path (asset content + token-usage
metadata, via the same monkeypatched-`ReasoningAgent` seam `test_evaluator_mode.py` established),
the deprecation warning on `llm=`, and the neither/both `ValueError` guard. Full suite green
(2841 passed, 3 skipped).

`TurnRunStore.latest_run(conversation_id)` -- the most recent run for a conversation, regardless
of status

Surveyed juno's recent commits for expansion ideas: a reconnecting chat UI needs to render "what's
happening now" for a conversation, and was reaching for a separately-tracked `last_message` status
field that can drift from the run record itself. `TurnRunStore` already had `has_active_run() ->
bool` but nothing that returns the run -- added `latest_run(conversation_id) -> TurnRun | None`,
the most recently created run regardless of status (QUEUED/RUNNING/terminal), so a caller reads
state from the source of truth instead of a second, driftable copy. Implemented on both backends:
`InProcessTurnRunStore` (max by `created_at` over the conversation's runs) and `DbTurnRunStore`
(one indexed query -- `conversation_id` and `created_at` were already indexed columns on
`TurnRunRecord` for `has_active_run`/FIFO ordering, so this adds no new index).

4 new tests in test_resilient_runs.py (both backends: returns the newest run by `created_at`
across multiple runs and multiple conversations, `None` for an unknown conversation). Full suite
green (2844 passed, 3 skipped).

`jazzx_sdk.manifest.bundle`/`.publish` -- a portable, retry-safe cross-instance promotion
primitive, generalized from `assistant`'s working export/publish pattern

Surveyed `assistant`'s recent commits for expansion ideas: `app/assistant/promotion.py` exports an
assistant's full dependency closure into one portable zip, then publishes each part into another
instance's owning service -- proven, working, ~1100 lines. Read it in full before generalizing
anything: most of it (BPMN/Flowable closure-walking, kernel's agent-config YAML shape, Knowledge
Hub collection resolution, Role CRUD) is `assistant`-repo domain specifics with no japes
equivalent -- porting that would be dead code in an SDK with no BPMN/Flowable/KH-collection
consumer. What's genuinely portable: the in-memory zip-slip-safe bundle format, a per-asset-type
`Publisher` protocol (each publisher owns its own conflict policy -- upsert, skip-duplicate,
reuse-by-name; `promote()` has no opinion on it), and the retry-safety convention itself -- every
`Publisher` is idempotent, and the caller writes its "roll-up" record only *after* `promote()`
returns successfully, mirroring `assistant`'s own "create the assistant row last" trick that makes
a failed publish resumable with the same bundle.

Scoped deliberately narrow: `jazzx_sdk.manifest.AssistantManifest` (skills + pack_id +
profile_ref) has no established "dependency closure" concept the way `assistant`'s `Assistant` row
does -- guessing at one now would be inventing structure a real consumer might want differently.
Shipped the generic primitive plus exactly one real, already-upsert-shaped reference
implementation instead of speculating further:

- `jazzx_sdk/manifest/bundle.py` -- `pack_bundle`/`unpack_bundle`, in-memory (no filesystem
  intermediate, unlike the document pipeline's disk-oriented `unpack_zip`), zip-slip-safe on
  unpack, plus a `BundleManifest` top-level entry (name/groups/warnings) so a receiving side can
  introspect a bundle without guessing from entry names.
- `jazzx_sdk/manifest/publish.py` -- `Publisher` protocol, `PublishResult`/`PromotionResult`, and
  `promote(groups, publishers=..., order=...)`, the ordered orchestrator. Fails loud (not silent
  drop) on a group with no registered publisher.
- `jazzx_sdk/manifest/publishers.py` -- `AgentDefinitionStorePublisher`, wrapping the already
  upsert-by-name `AgentDefinitionStore.put` (no new conflict policy needed). The one concrete
  implementation proving the protocol against a real store, not an abstraction with zero
  implementations.

18 new tests (test_manifest_bundle.py, test_manifest_publish.py): pack/unpack round-trip, empty
groups, zip-slip/absolute-path/non-zip/missing-manifest rejection; `promote()` ordering, missing-
publisher failure, result aggregation; `AgentDefinitionStorePublisher` upsert-by-name, retry
idempotency, entry-name-vs-definition-name decoupling, malformed-entry rejection; one end-to-end
bundle-to-store test. Full suite green (2862 passed, 3 skipped).

New `jazzx_sdk/pipelines/` package -- one home and one catalog for japes' "reference pipeline"
family, plus a symmetry cleanup found while designing it

Two reference pipelines already existed -- `chat.py` (wraps `InteractiveAgent`) and
`document/pipeline.py` (wraps `DocumentAgent`) -- built independently, in the same shape (a thin
`ConductorPipeline` + step functions + a per-invocation "Turn" dataclass + a `run_X()` wrapper),
without ever cross-referencing each other. Neither had a discovery point (no catalog entry the
way modes/experts/fabric-surfaces already get from `platform_catalog.py`), and "pipeline.py" as a
filename already meant three different things in the SDK: the `ConductorPipeline` primitive
itself (`conductor/pipeline.py`), a reference-pipeline instance built from it
(`document/pipeline.py`), and an unrelated bespoke batch pipeline that doesn't use
`ConductorPipeline` at all (`adjudication/pipeline.py`).

Moved both into a new `jazzx_sdk/pipelines/` package, sibling to `agents/`/`modes/`/`conductor/`
-- not just future multi-owner pipelines, all of them, since a lightly-used pipeline today could
grow to span more than one agent over time, at which point "whose package does it live in" stops
having a good answer. `agents/document/pipeline.py` renamed to `pipelines/document_ingest.py` on
the move (matching its own docstring's self-description); `chat.py` kept its name (already
domain-named, no collision) and just moved. Clean move, no re-export shim left at the old paths
(CLAUDE.md's own anti-pattern list names "re-exporting types" as a backwards-compatibility hack
to avoid) -- every japes-internal and jaci caller fixed in this pass.

New `jazzx_sdk/pipelines/catalog.py` -- `PipelineContract`/`PIPELINE_REGISTRY`, mirroring
`jazzx_sdk/modes/catalog.py`'s `ModeContract`/`MODE_REGISTRY` shape exactly: module path, the
primitive(s) wrapped, turn type, step ids, entrypoint. References pipelines by import path rather
than physically containing their code, same as `MODE_REGISTRY` does for modes. `platform_catalog.
PIPELINES` (id -> description) derives from it, same pattern just shipped for `MODES` earlier in
this version. Deliberately lightweight: `jazzx_sdk/pipelines/__init__.py` only imports the
catalog, not `chat.py`/`document_ingest.py` themselves -- matches `jazzx_sdk/modes/__init__.py`'s
own convention of never eagerly importing its heavy per-mode implementations just to expose the
registry; confirmed empirically (no `InteractiveAgent`/`DocumentAgent` modules load transitively
via `platform_catalog.PIPELINES`).

Auditing every repeated filename across `jazzx_sdk/` (14 `base.py`, 12 `store.py`, 4 `catalog.py`,
4 `agent.py`, 3 `pipeline.py`, 3 `engine.py`, 3 `loader.py`, 7 `schema.py` + 4 `schemas.py`, ...)
to check whether "pipeline.py" was a one-off or a symptom found two more real instances of the
same failure mode (same filename, genuinely different structural role -- not just "same name,
same convention, different domain," which every other repeated name turned out to be):

- `agents/adjudication/pipeline.py` -> `agents/adjudication/segment.py` (matching its own
  `run_segment` entrypoint) -- fully closes the "pipeline.py means two things" collision this
  pass started from, rather than narrowing it. Internal-only, no jaci consumer.
- `DocumentAgentSpec` extracted from `agent.py` (651 lines, largest of the three fat-agent
  `agent.py` files) into a new `agents/document/spec.py`, matching `InteractiveAgentSpec`/
  `AdjudicationAgentSpec`'s already-dedicated `spec.py` convention.

Assessed and deliberately left alone: `schema.py`/`schemas.py`'s singular/plural spelling split
(11 files, zero semantic ambiguity, high churn for a cosmetic fix); `manifest/store.py` and
`runs/store.py` being the only two `store.py`s not nested under `fabric/` (possibly intentional --
a standing persistence-architecture note distinguishes service-owned-db from fabric-as-HTTP-
domain-service as two deliberate patterns -- flagged, not touched; moving an established
top-level package is a materially bigger, riskier change than anything else in this pass).

New `tests/test_pipeline_catalog.py` (registry shape, contract accuracy, every registered module
path actually importable) plus a `platform_catalog.PIPELINES` tracking test in
`test_platform_catalog.py`. `tests/test_adjudication_pipeline.py` renamed to
`test_adjudication_segment.py`. Full suite green (2869 passed, 3 skipped).

New `jazzx_sdk/pipelines/investigation_loop.py` -- the third reference pipeline, generalizing a
shape five jaci scenarios independently hand-rolled

Deep-read all five jaci investigation-loop conductors (AML, KYC, CRE-underwriting,
KYC-Anthropic, earnings_anthropic) plus `jazzx_sdk/conductor/{base,engine,checkpoint}.py` and
every operational mode's real constructor/`run()` signature before designing anything.
`BaseConductor` is a bare 27-line ABC; `ConductorEngine` already has native loop-until-converged
support (no pack hand-rolls a `while` loop except the pre-migration KYC baseline). All five
conductors share one real skeleton -- six modes constructed once and cached on `self`, near-
identical `_step_investigator`/`_step_evidence`/`_step_verifier` bodies, the same
`pipeline.model_copy` -> override `max_iterations` -> `ConductorEngine(...).run(context=ctx)` ->
assemble a pack-owned result object from `run.emitted_for(...)` skeleton -- but diverge on real,
load-bearing behavior: convergence representation (`LoopStatus` enum vs. a bespoke boolean
flag), convergence policy (trust the LLM's own claim vs. AML/CRE's deterministic
evidence-type-count + iteration floor), Sentinel presence (also where the per-iteration
checkpoint fires, in the two conductors that have one), checkpointing (zero in three of five),
a deadline guard (AML-only), reasoner-failure policy (halt vs. synthesize-a-fallback), and the
narrator-gate predicate (every pack has its own "is this the escalating outcome" check).

`InvestigationSpec` -- six already-constructed mode instances (mode construction is already
adequately generic via each `Mode.__init__`'s own kwargs) plus the hooks where the five
conductors actually diverge: `fulfill_evidence` (required, 100% pack-owned -- every real tool
registry has a different `execute()` signature), `sentinel` (optional), `is_active`/
`mark_converged`/`mark_guard_fired` (convergence-state indirection -- defaults read/write the
SDK's own `Context.loop_status` field directly, so any `Context` subclass works with zero
overrides; a pack with a bespoke convergence field overrides these three instead of forcing a
canonical shape), `convergence_gate` (default: trust the LLM), `deadline_guard` (default: never
fires), `on_reasoner_failure` (default: `None`, leaving the reasoner step's output `None`),
`narrator_gate` (default: governor-approved only), `checkpoint` (default: none, called from the
Sentinel step only -- matches every real conductor's own behavior, confirmed no conductor
checkpoints per-iteration without a Sentinel present). Deliberately not part of this primitive:
a `persist` step -- a pack's final checkpoint is tangled up with its own `CanonicalTrace`
construction (different fields, a termination-reason map specific to its own status
vocabulary); `build_investigation_pipeline` declares an optional `persist` step id a pack can
bind its own component to, same as `document_ingest.py`'s optional `package`/`collection` steps.
Registered in `PIPELINE_REGISTRY`.

15 new tests (`test_investigation_loop.py`, fake modes matching the six real signatures):
convergence-gate override, default hooks against `Context.loop_status`, Sentinel wired only
when set, checkpoint firing only via an active Sentinel pass (confirmed against AML's own real
behavior -- no checkpoint on the converging iteration either), narrator-gate suppression,
reasoner-failure fallback, deadline-guard short-circuit, `persist` skippable/bindable. Plus a
`test_pipeline_catalog.py` entry. Full suite green (2885 passed, 3 skipped).

Proof-of-concept migration (jaci, same day): `EarningsAnthropicConductor` -- the simplest of the
five (no Sentinel, no checkpoint, no deadline guard) -- now builds an `InvestigationSpec` instead
of hand-rolling `_components()`/`_step_*` methods; existing tests pass unchanged (parity, not a
behavior change). AML/CRE/KYC-Anthropic/KYC-plain migrations are explicitly deferred, separate,
higher-risk follow-on work once this primitive is proven -- KYC-plain additionally needs its own
prior migration onto `ConductorEngine` before it's even a candidate.

`jazzx_sdk/pipelines/investigation_loop.py` gains two additive extension points, closing the gap
between the proof-of-concept (earnings_anthropic) and the primitive's actual first-class target
(CRE) -- found by reading CRE's real, current code, not the earlier survey summary

`InvestigationSpec.halt_on_reasoner_failure: bool = False` -- CRE halts the whole run on reasoner
failure (`ConductorState.halt = True`, downstream steps recorded halted) instead of the
fallback-and-continue every other conductor uses; `on_reasoner_failure`'s existing contract is
unchanged, this is a new, independent branch in `reasoner_step`.

`build_investigation_pipeline(post_loop_steps=...)` replaces the hardcoded
`reasoner -> governor -> narrator` triplet with a pack-supplied sequence (default unchanged) --
CRE interleaves three deterministic, non-generalizable steps (DSCR stress-test math, an advisory
policy check, dependency-condition mapping) in a specific order the fixed triplet couldn't
express. `build_investigation_components(spec, overrides=...)` replaces the narrower
`persist=` param with a general override map, merged last -- lets a pack add step ids the
primitive doesn't define, or replace a generic step wholesale (CRE's real `governor` step
mutates the reasoner's own decision object and `ctx.loop_status` in place rather than returning
a decision, and its `narrator` step builds a credit-memo `Artifact`, not just a narrative --
neither fits the generic step's contract at all). Not used by any other caller today, so a safe,
non-breaking widening; updated the one existing `persist=` test to the new kwarg name.

4 new tests (`halt_on_reasoner_failure` sets `state.halt`/leaves reasoner output `None`, and the
false-path still falls through to `on_reasoner_failure`; `overrides=` replacing a generic step
wholesale; `post_loop_steps` producing a declared custom sequence). Full suite green (2889
passed, 3 skipped).

`CREConductor` migrated (jaci, same day) -- the primitive's actual first-class target, not
another proof-of-concept. `_step_investigator`/`_step_evidence`/`_step_verifier`/`_step_sentinel`/
`_step_reasoner`/`_components()` replaced by an `InvestigationSpec`;
`_step_stress`/`_step_policy`/`_step_governor`/`_step_dependencies`/`_step_narrator`/
`_step_persist` kept verbatim as `overrides=` -- genuinely pack-specific, exactly what the
primitive was designed to leave pack-owned. `describe()` returns the generic pipeline instead of
the YAML-loaded `CRE_PIPELINE` (kept as a module symbol solely for `ui/registry.py`'s diagram
lookup, same pattern earnings_anthropic's migration established). `CRE_PIPELINE` uses
`ctx.loop_status` directly (the SDK `Context` base's own field) -- exactly what the primitive's
default `is_active`/`mark_converged`/`mark_guard_fired` hooks already read/write, so CRE needed
zero overrides there, unlike earnings_anthropic's bespoke boolean flag. Existing offline
orchestration tests (`tests/unit/test_cre_conductor_engine.py`) pass unchanged -- parity, not a
behavior change.

`InvestigationSpec.on_mode_result` -- one more additive hook, for `AMLConductor`'s migration

AML accumulates real LLM token usage per mode (`ctx.metadata["token_usage_by_mode"]`) after every
investigator/verifier/reasoner/governor/narrator call, feeding a cost-tracking eval
(`tests/eval/test_anthropic_token_tracking.py` in jaci, gated behind a live-API-key marker so not
in the offline suite, but a real, tested feature not to be silently dropped). No existing hook
covered "do something with every mode's raw result" -- `on_mode_result: Callable[[ctx, step_name,
result], None] | None = None`, called from those five generic steps only (not Sentinel's, which
is deterministic/non-LLM and has nothing to accumulate). Default `None` -- no-op, unchanged
behavior for `chat`/`document_ingest`/earnings_anthropic/CRE. 2 new tests. Full suite green (2891
passed, 3 skipped).

`AMLConductor` migrated (jaci, same day) -- structurally the closest of the four migrated so far
to CRE (deterministic convergence floor, Sentinel + checkpointing, `ctx.loop_status` used
directly, zero overrides for the convergence-state hooks) but without CRE's extra steps or
mutate-in-place governor -- its governor/narrator instead follow earnings_anthropic's pattern
exactly (generic steps mid-run; the pack remaps/gates in its own post-processing). First real use
of `deadline_guard` (AML's SAR-deadline check) and `on_mode_result` outside their own test
coverage. `_step_investigator`/`_step_evidence`/`_step_verifier`/`_step_sentinel`/
`_step_reasoner`/`_step_governor`/`_step_narrator`/`_components()` replaced by an
`InvestigationSpec`; `_step_persist` kept verbatim as the one `overrides=` entry. Existing offline
orchestration tests (`tests/unit/test_aml_conductor_engine.py`) pass unchanged.

## [2.3.5] - 2026-08-10

Agent identity for eval/feedback attribution; per-skill/parent tool_use_behavior

- InteractiveAgentSpec.agent_id: a stable identity carrier for eval/feedback attribution.
  None -> falls back to spec.name (InteractiveResponse.agent_id, stamped on every turn).
  spec_binding.bind_spec() now carries manifest.assistant_id onto spec.agent_id when the
  profile didn't set one explicitly -- closes a real gap where the manifest layer already
  had a proper assistant_id, but it was dropped during manifest -> spec narrowing and never
  reached the running agent. Feedback.agent_id threaded through for_turn()/
  InteractiveResponse.feedback() so feedback records carry the same attribution as the turn.
- Skill.tool_use_behavior / InteractiveAgentSpec.tool_use_behavior: per-skill and parent-level
  overrides for Agent.tool_use_behavior ("stop_on_first_tool" skips the extra LLM round-trip
  when a tool's own output is the final answer, e.g. a deterministic lookup skill). Mirrors
  the existing max_turns override shape; both default to unset (SDK default, byte-identical
  behavior for existing specs).

Fix replicas default, document stochastic, close domain-neutrality gap; migrate
EvaluatorMode/NarratorMode/VerifierMode onto ReasoningAgent; fix BaseMode silent fallback

From an independent completeness audit against the AdjudicationAgent chassis:

- replicas default 3 -> 1 across spec.py/pipeline.py/conductor/replication.py. The
  shipped default contradicted this repo's own measurement (batched k=3 on a real
  fixture: zero variance reduction, 3.1x cost) -- an inherited-not-measured
  assumption, not a tuned one.
- ConditionEvaluator.stochastic documented as currently redundant with
  execution == LIVE across all four registered evaluators, rather than wired into
  partition_rules -- no evaluator yet needs the distinction; wiring it now would be
  an untested seam with no behavior to justify it.
- modes/catalog.py: nulled five AML literals (canonical_produces/canonical_consumes/
  derived_object on investigator/conductor/narrator) that had no business being in a
  domain-neutral mode registry -- verified nothing in jazzx_sdk reads them first.
- EvaluatorMode migrated onto ReasoningAgent: now inherits BaseMode, constructor takes
  ctx: HandlerContext, run() returns ModeResult. Previously held its own AsyncOpenAI
  client (unusable on an Anthropic-only deployment) and parsed a bare json.loads with
  no retry -- a truncated/malformed response either raised or silently produced an
  empty improvement_signals list, stopping the compounding loop with no error
  anywhere.
- Caught along the way: a dict-typed output_type field (typed or bare) breaks
  OpenAI's strict-schema mode outright. Fixed for the new _EvaluatorLlmOutput model,
  then found and fixed the same pre-existing bug in NarratorMode (NarrativeOutput)
  and VerifierMode (VerifierReport). Also cleaned up VerifierMode's empty-batch
  return, which built its result with six kwargs that aren't real fields on that
  model -- pydantic silently dropped them, so this was always producing the same
  bare-defaults object a plain call would, just via misleading dead code.
- BaseMode.system_prompt no longer swallows a missing pack asset: was catching
  FileNotFoundError and substituting a fabricated "You are the {mode} mode." prompt.
  resolve_mode_prompt documents raising as its actual contract; every mode's run()
  already wraps this access in a broad except Exception, so this now surfaces as a
  real, checkable failure instead of a silent bad prompt.


Add AdjudicationAgent chassis (jazzx_sdk.agents.adjudication)

  Per-segment obligation checking: batched replicated verification for           
  LLM-evaluated obligations, direct evaluation for deterministic ones,           
  scoped evidence access per segment, applicability gating, incremental          
  re-run support, and a fail-closed dynamic segment planner. New                 
  NaturalLanguageCondition evaluator; Trace mode-tagging fix for                 
  mlflow_bridge; toy demo pack.

  Per-segment obligation checking with replicated variance reduction --
  generalizes MACER's own section x replica x batch-verify shape into a
  reusable, domain-neutral SDK primitive.

  - workspace.py: EvidenceWorkspace/Mount -- narrows the ambient
    PermissionScope to a segment's mounts for the duration of its calls,
    restored after.
  - partition.py: partition_rules splits a segment's Rule objects into
    DETERMINISTIC/LIVE by resolved ConditionEvaluator.execution.
  - spec.py: AdjudicationAgentSpec -- domain-neutral pack config (persona,
    model, replicas, regime_values/status_vocabulary carried verbatim,
    never branched on), with from_dir(yaml + persona.md) loading.
  - pipeline.py: run_segment -- batches every LIVE obligation into one
    prompt per replica, replicates (P1 run_replicated_segments), collapses
    per obligation (P2 EnsembleCollapse); DETERMINISTIC rules go straight
    through their own evaluator, no LLM. A rule with condition=None is
    skipped, matching DefaultPolicyExpert.check_compliance exactly.
  - agent.py: AdjudicationAgent facade -- fans run_segment out across
    segments (one bad segment doesn't sink the case), reconciles, emits a
    narrative. A narrative-generation failure never discards already-
    computed outcomes.
  - fabric.canonical.policy/condition_evaluator: new NaturalLanguageCondition
    kind + NaturalLanguageEvaluator (LIVE, stochastic) -- the Condition
    union had no LLM-backed kind for a chassis-level obligation to declare
    itself LIVE with.
  - observability.mlflow_bridge: new name_patterns parameter on
    span_to_trace_step/spans_to_canonical_trace -- the existing mode_map
    is keyed on span_type (LLM/TOOL/...), too coarse to tell an adjudicate
    call from an emit call apart (both are plain LLM spans); name_patterns
    matches on the agent/session name instead, checked first.
  - examples/adjudication_demo: toy two-segment mortgage-underwriting pack
    (mirrors examples/loan_assistant's spec-plus-harness shape).

Add P3/P7 (impact resolution + segment planning) to the AdjudicationAgent
chassis

  Generalizes MACER's rerun_orchestrator.py/orchestrator_agent.py rather
  than porting them -- MACER may never adopt this chassis, but the
  primitives are useful to japes's other consumers regardless.

  - pipeline.run_segment: now honors Rule.applicability (a real gap --
    it didn't before, unlike DefaultPolicyExpert.check_compliance). An
    inapplicable rule short-circuits to RuleOutcome(verdict=NOT_APPLICABLE)
    before reaching its condition, deterministic or LIVE, no LLM call.
  - New agents.adjudication.planner: SegmentPlanner protocol +
    plan_or_fallback -- the SDK owns the fail-closed discipline (planner
    exception or empty plan falls back to the static segment list); the
    case-profile/regrouping logic itself stays pack-side.
  - New agents.adjudication.impact: impacted_rules() keys off
    ConditionEvaluator.evidence_contract() (P8) instead of MACER's
    document-classification-triple mapping file -- reusable by any pack.
    merge_with_carry_forward() + a RunMode enum/resolve_run_mode()
    matching MACER's own INITIAL/INCREMENTAL/FORCED_FULL upgrade-downgrade
    rules, plus a NO_OP mode for explicitly-empty impact.
  - AdjudicationAgent.adjudicate: new optional planner/changed_fields/
    prior_outcomes params wire both in; omitting all three is unchanged
    from the prior release.

Fix replicas default, document stochastic, close a domain-neutrality gap
(from an independent completeness audit against the chassis work above)

  - agents.adjudication.spec/pipeline, conductor.replication: replicas
    default 3 -> 1. The shipped default contradicted this repo's own
    measurement (batched k=3 on a real fixture: zero variance reduction,
    3.1x cost) -- an inherited-not-measured assumption, not a tuned one.
  - fabric.canonical.condition_evaluator.ConditionEvaluator.stochastic:
    documented, not wired -- it's currently redundant with
    execution == LIVE across all four registered evaluators, so gating
    partition_rules on it today would be an untested seam with no
    behavior to justify it.
  - modes/catalog.py: nulled five AML literals (canonical_produces/
    canonical_consumes/derived_object on investigator/conductor/
    narrator) that had no business being in a domain-neutral mode
    registry -- verified nothing in jazzx_sdk reads them first.

Migrate EvaluatorMode onto ReasoningAgent

  The one EVOLVE-layer mode left out of the v2.3.0 five-mode migration.
  Previously held its own AsyncOpenAI client (unusable on an
  Anthropic-only deployment) and parsed a bare json.loads with no
  retry -- a truncated/malformed response either raised or silently
  produced an empty improvement_signals list, stopping the compounding
  loop with no error anywhere.

  - modes/evolve/evaluator.py: now inherits BaseMode; constructor takes
    ctx: HandlerContext (matching the other five modes); run() returns
    ModeResult instead of a bare EvaluationReport. No real caller
    depended on the old shape (verified zero constructor call sites
    anywhere in japes beyond docstring mentions and re-exports).
  - Caught along the way: a dict-typed output_type field (typed or
    bare) breaks OpenAI's strict-schema mode outright
    ("additionalProperties should not be set") -- confirmed this would
    also break NarratorMode's NarrativeOutput.sections in a real call.
    Fixed only for the new _EvaluatorLlmOutput model via
    AgentOutputSchema(..., strict_json_schema=False); NarratorMode's
    pre-existing instance of the same bug is untouched, out of scope.

Fix the same strict-schema bug in NarratorMode

  - modes/operational/narrator.py: NarrativeOutput's sections/
    citations/metadata are all dict-typed -- same AgentOutputSchema(...,
    strict_json_schema=False) fix. The existing test file mocked at the
    Runner.run() level (the ReasoningAgent.run(runner=...) test seam),
    so it never reached the real get_output_schema()/AgentOutputSchema
    construction either -- added the same boundary contract test.
  - Found, then fixed same-session: VerifierMode/VerifierReport has the
    identical bug (evidence_results/notes/attestations all dict-typed).
    GovernorMode/GovernorDecision and InvestigatorMode/HypothesisUpdate
    are clean (list/bool/str only); ReasonerMode's output_schema is
    pack-supplied, not an SDK schema.

Fix the same strict-schema bug in VerifierMode

  - modes/operational/verifier.py: same AgentOutputSchema(...,
    strict_json_schema=False) fix, same test blind spot, same added
    contract test.
  - Cleaned up (not a behavior change): the empty-evidence early return
    built VerifierReport(evidence_id=..., status=..., quality_score=...,
    findings=..., flags=..., attestation=...) -- none of those are real
    VerifierReport fields; pydantic v2 silently ignores unknown kwargs,
    so this always produced the same bare-defaults object a plain
    VerifierReport() would, just via misleading dead code.

Fix BaseMode.system_prompt silently swallowing a missing pack asset

  Was: catch FileNotFoundError, log a warning, substitute a fabricated
  "You are the {mode_name} mode." prompt. resolve_mode_prompt documents
  its own contract as raising on a genuine miss; BaseMode was silently
  defeating that -- a mode running on a fabricated prompt with no
  visible error is a capability failing silently, not loud.

  - modes/base.py: system_prompt now lets FileNotFoundError propagate.
    Every mode's run() already wraps this access in a broad except
    Exception -> ModeResult(success=False, error=...), so this surfaces
    as a real, checkable failure instead of a crash or a silent bad
    prompt.

## 2.3.4
Generalize install_request_headers_hook for bare httpx clients

  Detects a bare httpx.AsyncClient/httpx.Client (not just a generated
  AuthenticatedClient/Client wrapper) and installs the hook directly on
  its own event_hooks["request"] -- covers a consumer building a plain
  httpx client by hand (e.g. jazzx-assistant's assistant_client.py)
  without needing a generated-client wrapper to hang the hook off of.

  Export install_request_headers_hook, add KernelClient.get_agent, add
  render_prompt_template
  
  - clients.__init__: install_request_headers_hook is now public -- a
    consumer wrapping their own raw generated client (not going through
    KernelClient/KnowledgeHubClient) can harden it the same way, instead
    of hand-rolling per-call header injection.
  - KernelClient.get_agent(name): mirrors get_tool(), reuses the same
    search_agent_by_name endpoint invoke_agent already uses internally.
  - New jazzx_sdk.templating.render_prompt_template: sandboxed Jinja2
    rendering of untrusted templates into prompts, fail-soft on any
    error (bad syntax, sandbox violation, jinja2 not installed). New
    optional 'templating' extra (jinja2), lazy-imported. Exported from
    jazzx_sdk.templating and the top-level jazzx_sdk package.


  Bump patch version to 2.3.4
  
  - fabric.canonical.store.core.PolicyStore.list_policies: paginate                                
    read_entities (was capped at limit=500, silently dropping policies                             
    beyond the first page).                                                                        
  - tools.documents.classifiers.classify_llm: completeness_passed was                              
    vacuously True for a document type with no registered classifier                               
    (required=[] -> not [] == True even though nothing was extracted).                             
  - server.governed_http: clear_governed_context() now runs on early                               
    400/409 exits too, not just the happy path (set_governed_context and                           
    the mutating-idempotency check moved inside the try/finally).                                  
  - tools.agent.dir_tools.build_directory_tools: show_hidden: bool =                               
    False -- dotfiles excluded from list_documents/search_documents by                             
    default (write_document also refuses to create one), with an opt-in                            
    for a caller with a legitimate dotfile.                                                        
  - fabric.fabric.KnowledgeFabric: accepts manifest_store, threaded to                             
    the lazily-constructed DocStore. Added NullMaterializeManifestStore                            
    (jazzx_sdk.fabric.docs) as a first-class no-persistence option. 

## 2.3.3 contd.
 Generalize escaped-literal-text stripping beyond NUL to surrogates and C0
  controls 
  
  sanitize.py: the double-JSON-encode mechanism that surfaces a NUL's
  "\u0000" escape as literal text applies equally to lone surrogates and
  C0 controls. _SURROGATE_LITERAL/_CONTROL_LITERAL now strip those forms
  too (control literals still opt-in via strip_control, matching the
  real-byte behavior). Both derived from the same code-point sets as the 
  real-character checks, so the two can't drift apart. 

  Fix bot-reported gaps: SSRF scheme allowlist, PreflightGate empty-refusal fail-open, sync_collection page_size drift, dir_tools path-containment bypass

  - net_safety.validate_url_safe + tools/documents/local._validate_url_safe:
    reject non-http(s) schemes (file://, gopher://, ...), not just private IPs.
    Documented (TODO) the separate, still-open DNS-rebinding gap in is_private_ip.
  - PreflightGate.evaluate: an empty-string refusal now still blocks (falls
    back to fallback_refusal) instead of silently passing the turn through --
    matches the class's own documented contract (None = pass, any string = block).
  - fabric.docs.store.sync_collection: page_size 100 -> 1000, matching the
    other 5 KH pagination fixes (was an unintentional drift, no server cap).
  - tools.agent.dir_tools._safe_relative: path-containment check now uses
    parents-based comparison instead of a naive string prefix, closing a 
    symlink-escape bypass via a sibling directory sharing root's name as a 
    prefix (same pattern as the existing zip-slip guard).
- **Fixed** — `python` floor raised to `>=3.12` (was `>=3.11`, already broken for Claude via `ReasoningAgent`/litellm; no real consumer runs 3.11).
- **Fixed** — `DslEvaluator.evidence_contract` now calls `jazzx_sdk.expressions.parse.identifiers()` (existed all along, just never wired) — a DSL rule now correctly claims its referenced fields, fixing policy precedence (a deal-level DSL rule no longer lets a lower overlay rule also fire on the same field).
- **Fixed** — `InteractiveAgent._skill_instructions` now gates `Skill.references` through `admit_hop` like `tools`/`reads` already do — a caller denied `ref:x` could previously still receive its content.
- **Fixed** — `_series_value` (time-series formulas: `prior`/`avg`/`cagr`/`ltm`) now enforces `confidence_floor`, matching the plain-field-lookup path.
- **Added** — `PreflightGate`/`PreflightGateDecision` (`jazzx_sdk.agents.interactive`) — a generic pre-agent classification gate (one LLM round-trip: structured verdict + deterministic output-guardrail refusal mapping), generalized from jazzx-assistant's hand-built mortgage-safety gate.
- **Added** — `Source.locator` (`jazzx_sdk.agents.interactive.response`) — citations can now carry a page/cell/section `Locator`, same union `SourceCoordinate` already uses; `SourceBuilder` passes it through unchanged.

Known limitation, not fixed: Dependabot alert #98 (`cryptography>=50.0.0`) still deferred — mlflow caps `cryptography<50` through at least 3.15.1. Also flagged, not yet fixed: `sync_collection()` fetches only the first 100 KH documents (no pagination) and resolves duplicate filenames by list order rather than doc id, which can silently mismatch content on a re-sync.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.3] - 2026-08-05

- **Added** — `EvidenceRequestSpec`/`RichHypothesisUpdate` + `InvestigatorMode(rich_evidence_requests=True)`: lets a domain's Investigator keep LLM-authored per-request `query_params` (e.g. which policy clause to fetch) instead of the bare `evidence_requests: list[str]` AML/CRE use. Existing callers unaffected.
- **Added** — `GovernorDecision.required_actions` — real downstream consumers (KYC-Anthropic/Earnings-Anthropic UIs) read this; the shared `GovernorMode` didn't carry it.
- **Added** — `run_kit.run_agent` now stabilizes `prompt_cache_key` across every retry/continuation of a run when the caller didn't set one, generalizing a mechanism MACER's own `agent_utils.run_agent` proved out; no `ReasoningAgent`-backed mode set one before.
- **Added** — `ReasoningGroupEvictStrategy` (`jazzx_sdk.agents.interactive`) — a `reasoning_group_evict` `CompactionStrategy`, porting MACER's `input_filter.py` group-eviction algorithm as token-triggered (via `max_chars`) instead of byte-triggered. `run_kit.evict_reasoning_groups` is the shared, budget-agnostic algorithm behind both this and the existing byte-triggered `InputFilter`.
- **Fixed** — Dependabot: bumped `aiohttp>=3.14.3` (OOB heap read, WebSocket request smuggling, unnegotiated compressed frames) and `gitpython>=3.1.57` (arbitrary file truncation/read/overwrite via unguarded git options), clearing 6 of 7 open alerts. `cryptography>=50.0.0` (alert #98, Bleichenbacher oracle) deferred: every mlflow release through 3.15.1 caps `cryptography<50`, so bumping it now would silently downgrade mlflow 3.14.0→3.2.0. Revisit once mlflow ships a compatible release.

## [2.3.2] - 2026-08-04

`docs/plans/plan_assistant_sourav.md` (Studio design-doc review — P0/P1/P2/P3 code items, all
done) + `docs/plans/plan_kh_client_bump.md` (KH v2 idempotency — entity + document sides, plus
identity/RBAC verification).

- **Added** — `Skill.reads` (`jazzx_sdk/agents/interactive/{spec,reads,agent}.py`): a skill
  declares which `KnowledgeBinding`s (by new `KnowledgeBinding.name`) it needs on-demand tool
  access to; `InteractiveAgent` generates a closure-bound `list_<name>`/`read_<name>`/
  `search_<name>` `@function_tool` triple per binding at build time, gated through the existing
  `admit_hop`/`PermissionScope.narrow()` cascade via a new `doc_source:<name>` selector. Fixes a
  real correctness gap: the push-based `docs:` grounding path (`resolve_knowledge`) only ever
  emitted `"[doc] {name}"` per document — filename only — so a grounded agent could name a
  document and read none of its content. `list_`/`search_` rendering reuses
  `tools.agent.grounding.build_summary_index` (that helper's first real internal consumer,
  closing a second near-duplicate index-renderer risk); `select_items` doesn't fold in (in-memory
  dict select vs. `reads`' remote per-id fetch — a different mechanism).
- **Added** — `Skill.spec_ref` (assistant-as-skill composition, architecture doc §6): a skill can
  name a full `InteractiveAgentSpec` (resolved via a new `InteractiveAgent(profile_registry=...)`
  param) and run it as its own independently-guarded turn — its own guardrails/knowledge/
  output_schema all apply, unlike a flattened `tools`/`references` skill — exposed to the parent
  as a plain `@function_tool` (there's no Agents-SDK `Agent` object to wrap via `as_tool()`). No
  manual permission-scope narrowing needed: the nested turn runs under the same ambient
  `InvocationContext`, and its own `_check_turn_entry` already checks `assistant:<spec_ref>`.
- **Added** — `ProfileRegistry.validate()` now also checks the `spec_ref` composition graph: a
  dangling reference (doesn't resolve within the same registry) or a cycle (A wraps B wraps A,
  which would recurse forever at runtime) both fail validation with the actual cycle chain named.
  New `ProfileRegistry.publish()` (async) runs `validate()` first, then an optional
  `evaluator(name, spec) -> reason | None` hook (the same block-reason convention as a
  `GuardrailCheck`) — a caller-supplied extension point, not a hard-wire to
  `jazzx_sdk.evaluation`'s pack/conductor-shaped `EvaluationHarness`. Side-effect classification
  (the architecture doc's 3rd publish check) is explicitly not implemented — no such concept
  exists anywhere in `jazzx_sdk.tools` yet.
- **Added** — `SkillRegistry`/`GuardrailRegistry` tiering: `register(..., tier=)` (default 3) /
  `tier_of(name)`, the same 1/2/3 platform/pack-config/builder convention as
  `tools.documents.templates.TemplateRegistry`. Goes one step past that reference pattern: a
  less-trusted tier registering over an existing more-trusted name now raises unless
  `allow_override=True` is passed explicitly (`TemplateRegistry`'s own bare `_put` has no such
  guard).
- **Added** — `jazzx_sdk.server.create_knowledge_hub_mock_app(client=None, **client_kwargs)`: a
  FastAPI adapter serving any `KnowledgeHubLike` delegate (a fresh `MockKnowledgeHubClient` by
  default — already covers `list_documents`/`download_documents`/`read_entities`/`create_entity`/
  etc., file-backed via `data_dir=`) over HTTP routes matching the real KH API 1:1. Closes "every
  pack rebuilds a mock KH server" (jazzx-assistant's own hand-rolled `mock_knowledge_hub` FastAPI
  app + `FileBackedStore` was the motivating case) without generalizing the parts that don't
  generalize: a pack's own product-specific API mock (e.g. jazzx-assistant's `mock_assistant_api`
  — no shared japes client behind it) and devcontainer/compose templates (deploy infra, not SDK
  code) both stay pack-owned.
- **Added** — `scripts/new_assistant_scaffold.py <domain-name>`: generates
  `examples/<domain>/{profile/{profile.yaml,persona.md},harness.py,handler.py,test_<domain>.py,
  README.md}` — the middle rung between the 20-line `examples/loan_assistant/` snippet and a full
  production pack. Generated profile is deliberately skill-less so its test can use
  `jazzx_sdk.llm.scripted.ScriptedLLM` directly (keyless, no live model) — `ScriptedLLM` only
  covers the single-shot path, not the agentic Runner path. `handler.py` demonstrates the six
  `HandlerContext` touchpoints (`ctx.message`, `ctx.runtime`, `ctx.extend_visibility`/
  `log_metric`/`update_status`, and building the response off `ctx.message.header`), marked 1-6
  inline.
- **Added** — `handlers.propagated_headers`: context-manager counterpart to
  `set_propagated_headers`/`clear_propagated_headers` (sync + async, clears even on exception),
  mirroring `security_context`'s exact shape — juno had independently hand-rolled the identical
  capture/restore pattern for the same queue-worker identity-propagation problem this module
  already solves.
- **Fixed** — `InProcessTurnRunStore.reap_stale` (`jazzx_sdk/runs/store.py`) swept off a
  `list(self._runs.values())` snapshot taken at loop start; a concurrent `heartbeat()` renewing a
  *later* run in the same sweep, landing during an *earlier* run's `await self.update(...)` (the
  loop's only yield point), still got reaped off stale data. Prompted by a real juno production
  incident (#227). Fix: re-read each run fresh from `self._runs` immediately before its own
  staleness check/write, matching what `store_db.py`'s row-locked `reap_stale` already does for
  the DB backend.
- **Fixed** — `EntityStore.ensure(idempotency_key=...)` (`jazzx_sdk/fabric/entities/store.py`)
  never actually deduped by key: `_find_by_fingerprint` only ever matched a candidate's *content*
  hash, but a key-derived fingerprint is never equal to a content hash, so two calls with the same
  key but different content silently created two entities instead of one — despite `ensure()`'s
  own docstring promising the opposite. Fixed: an explicit `idempotency_key` now matches by
  `(collection_id, name)` instead of content (there's nowhere else to persist an arbitrary caller
  key remotely — `json_value` must conform to the caller's ontology schema).
- **Added** — KH v2 idempotent-create wiring, entity side
  (`jazzx_sdk/clients/knowledge_hub_client.py::create_entity_v2` now returns `(entity, created)`
  instead of just `entity` — the native 201-vs-200 signal — and `EntityStore.ensure()` prefers it
  over the pre-check+v1 path when available and no explicit `idempotency_key` is given).
- **Added** — KH v2 idempotent-create wiring, document side: no generated binding exists for
  document create anywhere in `client-api` (checked the pinned rev and its latest available
  commit) — unlike entities, whose v2 bindings already existed unwired.
  `KnowledgeHubClient.create_document_v2` is hand-rolled directly against the shared httpx client
  (same `_MultipartBody` file-part encoding v1's generated binding uses, so the existing
  request-headers-provider and denied-response hooks still apply); meant to be replaced by a real
  generated binding once `client-api` regenerates. `DocStore.ensure()` prefers it the same way,
  hydrating a 200 idempotent-hit's id-only response via the existing `_outcome()` re-fetch.
  `MockKnowledgeHubClient` gets `create_entity_v2`/`create_document_v2` for parity, signatures
  exact-matching the real client's per the existing mock/real parameter-drift contract test.
- **Verified** — KH v2 bump identity/RBAC step: `x-user-id` forwarding on every KH write path
  (`create_entity`, `create_entity_v2`, `update_entity`, `create_document`, `create_document_v2`)
  and `read_entity` 401/403 → `KnowledgeHubAccessError` (404 staying a plain miss, never conflated
  with denial) were asserted in the plan but never exercised end-to-end against a real
  `KnowledgeHubClient` call — new `httpx.MockTransport` round-trip tests close that gap. No code
  change; both claims held. Cross-checked KH's own server source directly:
  `common/core/dependencies.py::get_current_user_id_optional` reads the literal `x-user-id`
  header and `api_v2.py` stamps it onto `created_by_user_id`/`updated_by_user_id`.

## [2.3.1] - 2026-08-02

`docs/plans/REFACTOR-2.4-subpackage-interiors.md`, Phases 6, 7, and 11 — landed as a patch rather
than a minor bump (module-layout reorganization + one facade-closure pass, no public behavior
change beyond what's called out below).

- **Changed** (Phase 6 — facade closure) — closed the `llm`/`agents.interactive`/`tools`/
  `fabric.canonical` package facades (cost math, model identity, provider ABC, routing types,
  router/scope/knowledge, `processors`, `Predicate` all now reachable from their package root
  instead of forcing submodule pins). Made `DbCostRecordStore` and the four LLM providers lazy
  (PEP 562), matching the SDK's `_db` convention — `import jazzx_sdk.llm` no longer pulls
  SQLAlchemy or a vendor SDK unconditionally.
- **Fixed** — an `ImportError` escaping `__getattr__` for a missing optional LLM provider extra,
  which broke `hasattr()`/`dir()` instead of just failing on construction.
- **Added** — status-marker docstrings on five real-but-unexercised surfaces (`llm/routing.py`,
  `evaluation/compounding.py`, `tools/{grounding,tool_compression,dir_tools}.py`, `skills/`), per
  the "capability shipped ahead of demand" convention, so a future audit doesn't mistake staged
  work for dead code.
- **Removed** — `tools/kg_store.py`, a 25-line back-compat shim for symbols already removed in
  1.6.7; its two real tests retargeted at `fabric.graph.triple` directly rather than deleted.
- **Changed** (Phase 7 — `fabric/canonical/store.py` split) — 1,596 LOC of 13 copy-pasted CRUD
  store classes collapsed to a generic `_EntityStore` base plus thin per-type subclasses in a new
  `store/` package (`_base.py`/`core.py`/`derived.py`/`facade.py`). `PolicyStore` kept fully
  bespoke (different method names, its own OData-escaping, a richer collection description) since
  forcing it into the generic shape would have papered over real differences. All 14 public names
  unchanged; verified identical KH call shapes for all 13 types via a recording fake KH client.
- **Changed** (Phase 11 — `tools/` regroup) — `tools/` (24 flat modules, 255 KB) regrouped into
  `documents/` (the document-processing cluster, plus the flat `documents.py`'s local-file half
  now `documents/local.py` and chunking now `documents/chunking.py`), `knowledge_hub/` (ontology,
  policy, knowledge_graph, plus `documents.py`'s KH-callable half), `platform/` (discovery,
  workflow), and `agent/` (grounding, tool_compression, dir_tools). Evicted `financial.py` ->
  `finance/metrics.py` (fixed `finance/__init__.py`'s inverted dependency on `tools/`),
  `filings.py` + `EdgarFallbackSource` -> `finance/filings.py` (untangles conversion.py's routing
  from SEC-specific ingestion), `assessment.py` -> `fabric/assessment.py`. Renamed the private
  `documents._extract_text_from_html` to public `documents/local.py::extract_text_from_html`,
  closing the one real cross-module private-name reach the split surfaced.
  `tools/__init__.py`'s 116-name facade re-exports every moved name unchanged.

## [2.3.0] - 2026-08-02

Split out of what had been accumulating as 2.2.4 — this is everything from the MACER-onto-
`jazzx_sdk.agents` migration prep through the new chassis it enabled, one coherent arc
("generalize the execution mechanism, then build the third chassis on it"). 2.2.4 shipped
separately first with just the original policy/manifest/hooks/SSRF/agent-definition-store bundle.

- **Added** — `jazzx_sdk.agents.ReasoningAgent` (`agents/reasoning/`): a new chassis alongside
  `InteractiveAgent`/`DocumentAgent`, constructor-injected with `AgentExecutionService` like its
  siblings. One primitive serves both a floor (a robust single-shot structured call — retry,
  schema-validation feedback, and truncated-output feedback via `run_kit.run_agent`, none of
  which the existing generic tier or any of the five operational modes have today) and a ceiling
  (the same call with `tools=[...]`, the agentic/batchable shape MACER's migration proved out).
  Resolves models via the SDK's existing shared `resolve_model` — no new retry/model-resolution
  implementation. Design: `docs/plans/design_note_reasoning_substrate.md`.
- **Changed** — All five operational modes (`ReasonerMode`, `InvestigatorMode`, `GovernorMode`,
  `VerifierMode`, `NarratorMode`) now call `ReasoningAgent` instead of `AgentExecutionService`'s
  generic tier, so a schema-validation failure, truncated output, or transient error gets
  retried-with-feedback instead of failing the mode outright. No public constructor/`.run()`
  signature change on any of them; each mode's own short-circuit path (Governor's authority gate,
  Verifier's empty-batch return) is untouched and still bypasses the LLM entirely.
- **Fixed** — `AgentExecutionService.run()`'s generic tier (`OpenAIProvider.run()`) gets the same
  retry/schema-feedback fix for its no-tools, single-message case — the shape every real caller
  uses. `output_type=` now goes straight to the real `Agent`, so a schema mismatch retries with
  feedback instead of a hand-parsed raw string with no correction path. The tool-calling branch
  (no real caller exercises it — `tool_executor` was never wired to anything) and
  `AnthropicProvider.run()` (a fundamentally different, non-Agents-SDK implementation) are out of
  scope, for real architectural reasons, not oversights. Also fixed two confirmed-dead branches
  found along the way: `agent.temperature`/`agent.max_tokens` being set as attributes `Agent`'s
  dataclass doesn't have (silently inert), and empty `result.messages`/`result.tool_calls` reads
  (`RunResult` has neither field).
- **Added** — `Rule.condition`/`Rule.applicability` open onto a registered, pluggable `Condition`
  union (`fabric.canonical.condition_evaluator`) instead of a closed `Union[Expression,
  DslExpression]`: a `ConditionEvaluator` registry (`register_condition_evaluator`/
  `get_condition_evaluator`, mirroring the existing compaction-strategy registry) with three
  built-ins (`ExpressionEvaluator`, `DslEvaluator`, `RatioEvaluator` — the last wrapping
  `tools.ratio_evaluator.evaluate_ratio`, threshold resolved via the existing `profile:<key>`
  convention against a `PolicyProfile` passed through the evaluation context). New `RuleOutcome`
  (`verdict`: closed governance-facing enum, vs `status`: pack-vocabulary string — deliberately
  separate fields) and `EvidenceContract` (what a condition reads, computed statically) types.
  `Rule.applicability` is a new, orthogonal field: a cheap pre-check evaluated before `condition`,
  so an inapplicable rule costs nothing. `DefaultPolicyExpert.check_compliance` now dispatches
  every condition kind through the registry, which also closes a real gap: DSL/ratio conditions
  now participate in cross-policy field-precedence (`fields_claimed`) the same way flat
  `Expression` conditions always have — previously only `Expression` conditions could be claimed/
  skipped by a higher-precedence policy. A discriminated-union `kind` tag (with shape-sniffing
  fallback for pre-P8 dicts with no `kind` key) keeps every existing pack-authored condition —
  Python or YAML — validating unchanged. Also fixed the same closed-`isinstance` gap in
  `PolicyRegistry`'s legacy `policy_clauses` shim, which would otherwise crash constructing a
  registry containing any `RatioCondition` rule. Design: `docs/plans/policy-ir-abstraction.md`.
- **Added** — `jazzx_sdk.conductor.run_replicated_segments` (P1) and `EnsembleCollapse` (P2), the
  segment × replica × regroup topology MACER's `jtbd_runner.py`/`summarization_agent.py` hand-roll
  today. `run_replicated_segments` is built over the existing `fan_out` at both the segment and
  replica level: `precompute` runs once per segment (not once per replica), a caller-supplied
  `key_of` regroups every replica's results explicitly rather than by position, and a failing
  replica is recorded as a `ReplicaFailure` and excluded from the regroup rather than sinking its
  siblings or synthesizing a vote. `EnsembleCollapse` (`DeterministicVote`, `AnyEscalate`,
  `LlmFold`) then folds a regrouped item's votes into one result, deliberately excluding any
  `ReplicaFailure` from the fold — fixing the real bug in MACER's own collapse, where a replica
  that exhausted retries synthesized an `ERROR` vote that still diluted the majority. No registry
  for `EnsembleCollapse` (unlike the P8 `ConditionEvaluator`): a pack picks its collapse strategy
  in code, not from pack-authored data. Design: `docs/plans/reasoner-chassis-analysis.md` §4/P1/P2.
- **Added** — `jazzx_sdk.agents.reasoning.PrecomputedGrounding` (P6): generalizes MACER's
  `guideline_enrichment.py` — parse a corpus into heading-scoped `Snippet`s once
  (`HeadingSnippetExtractor`), cheaply prefilter by keyword overlap (`KeywordPrefilter`, MACER's
  own weighting), select the top few via an LLM shown headings only, never body content
  (`HeadingsOnlySelector`, built on `ReasoningAgent`), and cache the parse by a content fingerprint
  so a corpus change invalidates automatically with no TTL needed (`InMemoryGroundingCache`). The
  non-negotiable part is `BrowseGate`: closes a pack's own list/search tool selectors for the
  duration of the call that consumes the selection, via the same `InvocationContext`/
  `PermissionScope` mechanism `InteractiveAgent._build_parent_tools` already uses — a no-op when no
  `InvocationContext` is ambient, same convention as `admit_hop`. Deny-only, so a direct
  `read_document` a caller wants to keep available (to follow a citation) stays admitted. Every
  part (extractor/prefilter/selector/cache) is swappable; `gate` composes separately since closing
  the door wraps the *consuming* call, not `ground()` itself. Distinct from the existing
  `tools.grounding` (`build_summary_index`/`select_items`): that has no LLM selection step, no
  cache, and no gate. Design: `docs/plans/reasoner-chassis-analysis.md` §2.1/§4/P6.
- **Added** — `"segment_tail"` registered as a named `register_compaction_strategy` entry
  (`jazzx_sdk.agents.interactive.memory.SegmentTailStrategy`), alongside the existing
  `"summarize"`/`"drop"`. Same algorithm `run_kit.strip_session` already applies directly to a
  `SQLiteSession` — user items + the last assistant turn per segment, no LLM call — extracted
  into a shared pure function (`run_kit.segment_tail_items`) so `strip_session` and the new
  strategy can't drift apart. Meaningful for a `ConversationStore` backing a Responses-API/
  agentic session (items carry a `type`); a documented no-op for a plain chat-style history with
  no `type` field. Design: `docs/plans/reasoner-chassis-analysis.md` §4/P5 (half — the other half,
  MACER's `reasoning_group_evict` byte-triggered evictor, is separate, unbuilt work).

Step 2 of the MACER-onto-`jazzx_sdk.agents` migration (a japes-side prerequisite; MACER itself not
touched yet). Prompted by a kernel-vs-japes sweep that led into comparing MACER's own hand-rolled
OpenAI-Agents-SDK code against this module — `run_kit.py`/`models.py` were originally lifted from
MACER's code; this closes the gap that opened since, and modernizes `run_kit.py` onto primitives
that didn't exist when it was lifted (`jazzx_sdk.concurrency.backoff_delay`, `jazzx_sdk.failures`'
structured classification) rather than porting MACER's older shape unchanged. No existing callers
of `run_agent`/`resolve_model` (confirmed) — zero back-compat risk.

- **Added** — `resolve_model()` now handles Gemini and any `litellm/<provider>/<model>`-prefixed
  name via the OpenAI Agents SDK's own generic `LitellmModel` (previously `NotImplementedError` for
  Gemini). Bare Gemini names default to LiteLLM's `gemini/` prefix; Vertex AI's project/location-
  scoped routing needs the explicit `litellm/vertex_ai/<model>` form. Requires the existing
  `litellm` extra.
- **Added** — `run_agent()` gains a fourth retry category, `IncompleteOutputError` (a truncated
  response), alongside `MaxTurnsExceeded`/`ModelBehaviorError`/`APIStatusError` — feeds a "write
  shorter" correction back into the session and retries, mirroring the existing schema-validation
  retry shape.
- **Changed** — `run_agent`'s `on_retry(event, attempt, failure)` now hands the callback a
  `jazzx_sdk.failures.StructuredFailure` (via `classify_failure`) instead of the bare exception —
  one shared failure taxonomy across the model layer (`RetryingModel`) and this run loop, not two
  ad hoc vocabularies. New failure rules registered for the three run-loop-specific exception types
  (mapping `APIStatusError` 429→`RATE_LIMITED`, 408→`TIMEOUT`, else→`PROVIDER_ERROR`, carefully
  scoped to not shadow the existing built-in 401/403/5xx classification).
- **Fixed** — `run_agent`'s own retry backoff was a bespoke, non-jittered exponential formula;
  now uses `jazzx_sdk.concurrency.backoff_delay` + jitter, matching `RetryingModel`'s own formula
  instead of a second, slightly different one.
- **Fixed** — the `ModelBehaviorError` retry branch fed the raw validation-error text back into the
  conversation session verbatim; now passed through `redact_secrets` first, in case the error text
  ever echoes a credential-shaped value from the model's own (rejected) output.
- **Changed** — `on_retry(event, attempt, failure)` gains a fourth positional arg, the raw
  exception, alongside the `StructuredFailure` — a caller wiring its own tracer (e.g. MLflow spans)
  needs the live exception object for `span.record_exception`, which a serializable value type
  can't carry. Upstreamed while doing step 5 of the MACER migration (MACER's `TraceHooks`
  integration is the first real caller). No existing callers besides japes' own tests — zero
  back-compat risk.
- **Changed** — upstreamed MACER's more directive `ModelBehaviorError`/`IncompleteOutputError`
  session-feedback wording (found more effective in MACER's own production use) in place of the
  generic placeholder text.
- **Fixed** — an exhausted `APIStatusError` retry loop re-raised the bare exception with no
  `request_id`; now enriches the message with it (mirroring MACER's own behavior), so a provider
  support ticket has something to reference.
- **Added** — `tests/test_retrying_model.py` (57 tests), ported from MACER's own equivalent file
  while doing step 5 of the migration (delegating MACER's `run_agent` retry loop to this module) —
  MACER's `RetryingModel` was a byte-identical duplicate of this module's own, now replaced there
  with a re-export shim, so its white-box coverage (status-code/header extraction, backoff/jitter,
  orphaned-reasoning-item retry, streaming retry-before/after-yielding) had no remaining home but
  here.
- **Added** — `build_directory_tools()` gained `write_document` (via a new `output_dir` param) and
  a `compress_search_output` hook for `search_documents`, plus `extended_regexp` support (grep
  `-E`) — step 8 of the MACER migration: comparing this factory against MACER's own
  `tools/documents.py` found real capability gaps (not a duplicate, unlike steps 1/3/4), so these
  were upstreamed rather than dismissed. MACER's own tool is unchanged — the gate/enum/settings
  coupling and `read_reference` retrieval tool that go with its own headroom compressor stay
  domain-specific, not moved here.
- **Added** — `tests/test_raw_json_schema_output.py` (16 tests) and
  `tests/test_incomplete_output_detection.py` (9 tests), ported from MACER while doing step 9 of
  the migration (deleting MACER's now-hollowed-out `json_schema_output.py`/`models/retrying.py`
  re-export shims) — both had more thorough coverage of these shared classes
  (`RawJsonSchemaOutput`; `find_incomplete_output_message`/`RetryingModel`'s incomplete-output
  handling) than this module's own existing tests.
- 13 new tests across `test_agent_models.py`/`test_agents_run_kit.py`.

`docs/plans/plan_assistant_ws_fabric_enablement.md` W3 (of W1-W4; W1/W2/W4 not started — real
accumulated open design questions, see `docs/status/status_assistant_ws_fabric_enablement.md`).

- **Added** — `jazzx_sdk.security_context(value)`: a per-turn security-context manager supporting
  both `with` and `async with` (checked directly that a plain `@contextmanager` doesn't support
  `async with` at all, so built as a class implementing both protocols), for a caller dispatching
  many turns on one long-lived task (e.g. a per-session WebSocket worker) where set/clear-in-finally
  would otherwise be hand-rolled per dispatch. Verified concurrent-task isolation directly. 5 tests.

`docs/plans/plan_JAPES_1_9_X_DIRECTORY_BACKED_TOOLS.md` complete. See
`docs/status/done_JAPES_1_9_X_DIRECTORY_BACKED_TOOLS.md`.

- **Added** — `jazzx_sdk.tools.build_directory_tools`/`DirectoryToolSet`: a source-keyed
  `@function_tool` factory (list/read/search over named local directories) for download-then-agent
  solutions, built exactly per the plan's own design. Found and fixed two real bugs the plan itself
  didn't catch: its acceptance tests called `@function_tool`-wrapped tools directly (a
  `FunctionTool` is not callable — fixed by invoking through the real `on_invoke_tool` path), and
  its module-level `agents` import broke the SDK's tier-1/tier-2 "server-free" import boundary
  (`agents` transitively pulls `uvicorn`) — fixed by deferring the import into the factory
  function, matching the lazy-import convention sibling `tools/*.py` files already use. 13 tests.

- **Changed** — `jazzx_sdk`'s root namespace regrouped from 34 flat modules into `observability/`
  and `server/` subpackages plus three targeted moves (`fabric/db/engine.py`,
  `agents/kernel_model.py`, `clients/mocks.py`) — pure module-layout reorganization, no behavior
  or public-symbol change. `tracing.py` (five unrelated concerns in one 1029-line file) split
  along its existing eager/lazy boundary, which is now structural (a lazy module simply isn't
  referenced from any `__init__.py`) rather than hand-maintained. Landed on
  `refactor/sdk-layout-2.3`, not `dev` directly, because macer/jaci/juno run live path installs
  against this working tree. Hardened `tests/test_import_boundary.py` against passing vacuously
  after a module move/rename, and added a `jazzx_sdk.__all__` snapshot test — neither existed
  before. Removed three now-dead back-compat shims (`llm/sanitize.py`, `fabric/pack/__init__.py`,
  `utils/`) after repointing their last real callers, two of them in jaci. Full design/rationale:
  `docs/plans/REFACTOR-2.3-sdk-layout.md` (gitignored).

## [2.2.4] - 2026-08-01

`docs/plans/plan_agent_definition_store_and_facade.md` Part 1 (of 3; Parts 2-3 not started — the
facade needs real design decisions the plan itself leaves open). See
`docs/status/status_agent_definition_store_and_facade.md`.

- **Added** — `jazzx_sdk.agents.AgentDefinition`/`AgentDefinitionStore`/
  `InProcessAgentDefinitionStore`, plus a `fabric.db`-backed `DbAgentDefinitionStore`
  (`jazzx_sdk.agents.definition_store_db`, lazy-imported): a persisted, name-keyed registry of
  agent definitions that can point at either a japes-native `InteractiveAgentSpec` or an opaque
  kernel-hosted agent id — the one real gap identified against kernel's own agent model, everything
  else already having a more general japes-native equivalent. 10 new tests.

`docs/plans/plan_invocation_completion_hooks.md` core mechanism. See
`docs/status/status_invocation_completion_hooks.md` for full detail, including an open decision
(deliberately not made) on whether this should absorb the existing `webhook_url` field.

- **Added** — `MessageHeader.on_complete_hook` (`HookSpec{channel, config}`): a per-invocation,
  caller-selected completion notifier that names any channel `build_channel()` supports (not just
  webhook), delivered via new `jazzx_sdk.channels.notify.deliver_completion_hook` at all three
  entry points that produce a `ResponseMessage` (queue runtime, server `/invoke`, inbound event
  router) — wider coverage than the existing webhook-only, queue-path-only `webhook_url`. A
  failing response's payload carries a `classify_failure`-derived, redacted `{code, message,
  action}` rather than a raw exception string. Best-effort throughout: a bad channel name or a
  failed delivery is logged, never raised into the invocation's own response. 9 new tests.

- **Fixed** — a real, live SSRF gap in `jazzx_sdk.channels.WebhookChannel`: neither the channel
  itself nor `QueueProcessor._deliver_webhook` (the `header.webhook_url` push-notification path
  shipped in 2.2.2) validated the caller-supplied URL before POSTing to it — a caller could point
  japes's own infrastructure at a private/internal address (e.g. a cloud metadata endpoint).
  Found while researching `docs/plans/plan_invocation_completion_hooks.md`'s own explicitly-flagged
  SSRF prerequisite for a *new* hook mechanism, then discovering the identical, already-shipped gap
  in the existing one. Fixed by extracting `read_from_url`'s tested SSRF guard
  (`_is_private_ip`/`_validate_url_safe`) out of `jazzx_sdk/tools/documents.py` into a new shared
  `jazzx_sdk/net_safety.py` (`is_private_ip`/`validate_url_safe`), and calling it from
  `WebhookChannel.send()` before every POST. `documents.py` keeps a thin local
  `_validate_url_safe` aliasing the shared `is_private_ip` so its own existing monkeypatch-based
  test keeps working unchanged. 2 new tests cover a private channel URL and a private per-message
  `target` override, both refused before any request is made.

- **Fixed** — `jazzx_sdk.manifest.spec_binding`'s surface-defaults table had two real deviations
  from its own design, found by checking the plan's own named acceptance tests against what was
  actually implemented rather than trusting that the code existing meant it was correct. (1)
  `stream` was defaulted `True` for `WORKSPACE`/`ASSISTANT`, contradicting the explicit "advisory,
  never default it" rule (`respond_stream()` can't produce structured output) — no surface
  defaults `stream` now. (2) `conversation` was defaulted `True` unconditionally, with no check
  for whether a `ConversationStore` was actually supplied — a spec that reads as memory-enabled
  but isn't, since `InteractiveAgent._conversation_active()` also needs a `session_id` per call.
  `bind_spec()`/`build_from_manifest()` gained a `store=` parameter: `conversation` now defaults
  `True` only when a store is passed through, otherwise it stays `False` with a warning naming
  both requirements. No live consumer of this feature exists yet in either repo, so the corrected
  (safer) default carries zero regression risk to anything already running on it.

- **Added** — `jazzx_sdk.llm.structured.IncompleteOutputError` (a `StructuredOutputError`
  subclass) and `validate(..., truncated=)`: a response cut off at the output token limit is now
  classified distinctly from malformed JSON, so callers stop retrying a truncation with
  "fix your JSON" feedback that can't help. Provider-agnostic — `ProviderResult.truncated` and
  each of the four `llm/providers/*` map their own signal into it (OpenAI `finish_reason ==
  "length"`, Anthropic `stop_reason == "max_tokens"`, Gemini `finish_reason == MAX_TOKENS`, Ollama
  `done_reason == "length"`). Registered with `jazzx_sdk.failures.classify_failure` under a new
  `FailureCode.INCOMPLETE_OUTPUT`, alongside `jazzx_sdk.agents.models.IncompleteOutputError`
  (the pre-existing OpenAI-Agents-SDK-layer equivalent, now classified the same way). Found via a
  survey of a sibling service (macer) that had already fixed the identical misdiagnosis on its own
  Agents-SDK path; this closes the equivalent gap on japes' separate direct-provider-call path.
- **Fixed** — a pre-existing test-isolation bug in `tests/test_failures.py`: `_clear_pack_rules()`
  did a blanket `.clear()` of the shared pack-rule lists instead of removing only the rule(s) the
  test itself added, silently wiping any rule registered permanently at import time by production
  code. Harmless until this change, since nothing previously registered a rule that way. Now
  removes by name.
- `jazzx_sdk.fabric.canonical.policy.PolicyScope` (`institution`/`product`/`deal`) added to the
  canonical `Policy` model; `DefaultPolicyExpert.resolve()`/`check_compliance()` gained an
  optional ephemeral `deal_policy` parameter (never persisted into the registry) so a caller can
  layer a deal-specific override above a program overlay without a pack-side subclass.

## [2.2.3] - 2026-07-30

- **Added** — `jazzx_sdk.authority.context` (plan_JAPES_2_5_0_INVOCATION_AUTHORIZATION.md):
  `InvocationContext`/`PermissionScope`, cascaded per-request authorization checked at every hop
  from an assistant turn to a skill sub-agent to a tool call to a conductor step, rather than each
  hop trusting the last. Canonical-independent: `PermissionScope` (tier one) is always checked; an
  `AuthorityMatrixV2` (tier two) is an additional narrowing layer only when a pack is bound, so a
  plain assistant with no decision classes is still protected. `check_hop`/`admit_hop` delegate to
  the existing `check_action` rather than reimplementing its logic. Propagates across the same
  async-dispatch boundary `capture_identity_headers`/`set_propagated_headers` already solved for
  identity (`ResilientRunner.create_run`/`execute`, `TurnRun.invocation_context`). Opt-in: every
  hop is a no-op when no context is set, so no existing caller's behavior changes.
- **Changed** — `InteractiveAgent`'s turn entry, skill/tool resolution (`_build_parent_tools`),
  and knowledge-binding resolution (`resolve_knowledge`) now check the ambient
  `InvocationContext` when one is set. A skill sub-agent's own tool resolution runs under a
  *narrowed* context (its own declared `tools`/`references` only), so it cannot reach a tool its
  definition didn't declare even if the parent could. A refused skill/tool is excluded from the
  built tool list (least-privilege) rather than surfaced as an in-band tool-call result — see
  `done_JAPES_2_5_0_INVOCATION_AUTHORIZATION.md` for why the plan's literal "returns as a tool
  result" framing wasn't achievable without deeper Agents-SDK internals than this pass takes on.
  `statemachine.engine.apply`/`automation.governed.GovernedAutomation.run` prefer the ambient
  context over their own explicit matrix/actor-class arguments when one is set, falling back
  unchanged when not.
- **Added** — `ProvenanceType.OVERRIDE` (FR-HIL-3): a human-entered correction over a
  promoted-track spread, distinct from `REVIEWER_ENTERED` because an override always supersedes a
  specific existing value.
- **Changed** — `jazzx_sdk.finance.workbook.suggested_action`/`locator_text` promoted from
  module-private to public: a caller's own per-spread exception summary can now render identically
  to the governed workbook's own Exceptions sheet by sharing these two functions instead of
  re-deriving the same text independently.
- **Fixed** — `GovernedWorkbook`'s cell/findings hyperlinks now use an internal `Hyperlink(location=...)`
  reference instead of a plain string assignment, which serialized as an external OOXML
  relationship (`TargetMode="External"`) some readers refuse to navigate. Also fixed the Sources
  and Provenance sheet's own title being clobbered by its header row.
- **Added** — `jazzx_sdk.finance.workbook.GovernedWorkbook`: a layout-driven Excel reporter over
  governed (confidence + provenance + source-coordinate complete) inputs, distinct from the
  existing plain `FinancialSpread`-only exporter. Structural `typing.Protocol` inputs so a
  jaci-defined `SpreadPackage`/`MetricResult`/etc. satisfies it without japes depending on jaci.
  Cell-level notes/tier borders/provenance styling/source hyperlinks (FR-OUT-2), an Inputs sheet +
  live-formula display sheets (FR-OUT-1), and a reported/adjustment/adjusted bridge read straight
  from the engine's own derivation, never recomputed (FR-OUT-3). `WorkbookLayout`/`load_workbook_layout`/
  `default_layout` for pack-authored or package-derived sheet layouts.
- **Fixed** — `jazzx_sdk.finance.excel._write_trends` now carries its analytics-caption line
  (`"Computed in-sheet from the Income Statement..."`), matching jaci's own copy that this
  dedup pass discovered had silently diverged from japes'.
- **Added** — `jazzx_sdk.finance.periods`: assurance attribution and source precedence (FR-SRC-1/2/3).
  `SourceStatement` (a document's account of a period, distinct from the period itself);
  `SourcePrecedencePolicy` on `PolicyProfile` (institution-declared ranking, fail-closed —
  `ASSURANCE_RANK` is never a silent fallback); `resolve_sources` (picks the winning source,
  reports losers, refuses unresolvable ties); `construct_ltm_from_sources` (policy-driven LTM
  beside the existing explicit-component `construct_ltm`, plus FR-SRC-4 findings for a
  lower-assurance interim or stale data). Verified against the PRD's RB profile.
- **Added** — `ProvenanceType` gains `ADJUSTMENT_CANDIDATE`, `APPROVED_ADJUSTMENT`,
  `POLICY_ADJUSTED` (FR-ADJ-3), the candidate/approved distinction for a normalization
  adjustment — used by jaci's `apply_normalization` to refuse a candidate add-back flowing into
  an official/covenant-bound metric.
- **Added** — `jazzx_sdk.manifest.spec_binding.bind_spec`/`build_from_manifest`
  (plan_JAPES_2_4_0_ASSISTANT_MANIFEST_BINDING.md): wires `AssistantManifest` into the interactive
  agent runtime for the first time. `bind_spec` narrows an `InteractiveAgentSpec` by a manifest
  (fails closed on any skill outside `allowed_skills`, applies a per-`SurfaceType` defaults table
  for `conversation`/`stream`/`stream_tool_events`, attaches the new stock scope guardrail).
  `build_from_manifest` resolves `manifest.profile_ref` (new field, falls back to `assistant_id`)
  against a `ProfileRegistry` and builds a running `InteractiveAgent` in one call.
- **Added** — `jazzx_sdk.agents.interactive.scope.build_scope_guardrail`: turns a manifest's
  `in_scope_action_classes`/`out_of_scope_action_classes` into a real gate (a deterministic
  keyword match against declared out-of-scope classes, returning a typed `Refusal` with
  `RefusalClass.OUT_OF_SCOPE`) instead of `with_safety`'s advisory prompt text.
- **Added** — `InteractiveAgentSpec.router` (default `"default_llm"`, resolved at wire time —
  same pattern as `CompactionPolicy.strategy`): names the agentic path's skill pre-selection
  policy. `jazzx_sdk.agents.interactive.router`: `default_llm` (today's behavior, no-op),
  `intent_first` (a one-call classifier narrowing the exposed sub-agent tools for a turn, `None`
  on low confidence).
- **Changed** — `InteractiveAgent._run_guardrails` accepts a typed `Refusal` return from a
  guardrail check (alongside the existing bare-string contract): `Refusal.message` surfaces as
  before, and the full object is retrievable via the new `agent.last_guardrail_refusal`.

## [2.2.2] - 2026-07-28

- **Fixed** — Caller identity no longer silently drops across the queue/async-dispatch task
  boundary. `jazzx_sdk.runs.ResilientRunner.create_run` now captures the submitting caller's
  identity headers (`capture_identity_headers`, new); `execute` restores them
  (`set_propagated_headers`/`clear_propagated_headers`, new) around the dispatched turn, so every
  downstream KH/kernel call the turn makes forwards the right caller even when drained by a
  different async task or worker than the one that created it. `default_request_headers` and the
  `get_current_user_id/email/name` accessors both fall back to the restored set — outbound headers
  and identity-attribution code stay consistent. Root-caused from a corroborated cross-repo pattern
  (juno #242 hit this live).
- **Added** — Webhook push notification for queue-based invocations. `MessageHeader.webhook_url`
  (+ optional `webhook_secret`) opts an invocation into a push notification on completion —
  `QueueProcessor.send_response` delivers it via `jazzx_sdk.channels.WebhookChannel` (retry + HMAC
  signing), additive to the response queue, never a substitute for it. A caller that previously had
  to hand-roll delivery, idempotency, and retry itself (assistant's own webhook deliverer had
  neither) now gets both for free from `build_invocation(webhook_url=...)`.
- **Added** — `ScorerResult.skipped` — a scorer can now report "not applicable to this case"
  (e.g. groundedness with no retrieval context) distinct from a failure. `CompositeScorer` and the
  built-in adjudication policies (`all_pass`/`any_pass`/`k_of_n`/`weighted_threshold`) exclude
  skipped sub-results from their pass/score aggregation and required-scorer veto, and propagate
  `skipped=True` themselves when every sub-result skipped, so a skip never shrinks an achievable
  pass rate or counts as a failure.

## [2.2.1] - 2026-07-27

- **Added** — `jazzx_sdk.clients.EvalServiceClient` (Phase 2 of `plan_JAPES_2_3_0_GUIDANCE_
  INJECTION_HOOK.md`): a general-purpose, best-effort read client for eval-service's feedback
  endpoints (`get_feedback_config`, `find_similar`), generalizing jazzx-assistant PR #6's own copy
  to platform level so a third consumer never reimplements it a third time (kernel has one, PR #6
  built a second). Every httpx/JSON error degrades to `None`/`[]`, never raises;
  `httpx.MockTransport`-testable, no generated client to wrap (eval-service ships none).
- **Added** — Phase 1 of `plan_JAPES_2_3_0_GUIDANCE_INJECTION_HOOK.md`: `InteractiveAgent`
  now applies `jazzx_sdk.fabric.guidance` at turn time — the runtime hook that plan's own design
  doc (`done_JAPES_GOVERNED_GUIDANCE_ASSETS.md`) explicitly deferred. New
  `InteractiveAgentSpec.guidance_pack_id`/`guidance_applicability` (both additive, default off — no
  `fabric.guidance` call is attempted at all unless `guidance_pack_id` is set, so every existing
  spec is unchanged, not just "empty guidance"). `respond()`/`respond_stream()` retrieve deployed,
  applicable guidance, append the confidence-grouped rendered block to the system prompt after
  grounding context, and return the applied `GuidanceRef`s on the new
  `InteractiveResponse.guidance_refs` for a caller to attach to its own `CanonicalDecision` (making
  Guidance Effectiveness, IIF Schema Spec §10.4, computable). Mirrors `_ground`'s exact posture: a
  spec declaring `guidance_pack_id` with no fabric raises (real misconfiguration); a fabric present
  with no configured guidance store returns empty (a valid, unconfigured state). Phase 4
  (end-to-end proof) remains open.
- **Added** — `jazzx_sdk.fabric.guidance.eval_service_store.EvalServiceGuidanceStore` (Phase 3 of
  `plan_JAPES_2_3_0_GUIDANCE_INJECTION_HOOK.md`): adapts `EvalServiceClient`'s retrieval into the
  same `GuidanceStore` seam `fabric.guidance` exposes everywhere else — `search()` only;
  `put`/`get`/`versions`/`list` raise `NotImplementedError` naming the store read-only by design
  (eval-service-sourced feedback is authored/reviewed in eval-service's own UI, not through japes's
  lifecycle). `FabricConfig.guidance_backend` (`"rag"` default / `"eval_service"` / `"none"`) +
  `eval_service_url` (env `JAPES_EVAL_SERVICE_URL`) select the backend; misconfiguring
  `"eval_service"` without a URL raises at construction time. Backend selection is independent of
  whether a KH client is configured, since eval-service needs no KH backing at all.
- **Added** — Phase 4 (final) of `done_JAPES_2_3_0_GUIDANCE_INJECTION_HOOK.md`: an end-to-end test
  proving `InteractiveAgent.respond()` applies guidance sourced from a mocked eval-service transport
  (via `EvalServiceGuidanceStore`) exactly as it already did for `InProcessGuidanceStore` — the
  rendered guidance block reaches the actual prompt sent to the LLM, and `guidance_refs` names the
  eval-service feedback item's synthesized asset id. Closes the plan: governance-side rendering/refs
  now proven identical across both `GuidanceStore` backends, not just the in-process reference one.
- **Added** — `MetricDefinition.display_method: str = ""` (plan_JACI_CL_CHART_OF_ACCOUNTS_AND_
  CATALOG.md Phase 3) — a human display label for how a formula combines its inputs (e.g.
  `"ratio"`/`"percent"`/`"sum"`), display metadata only, never interpreted by the evaluator.
  Replaces a pack's own module-level id-to-label dict for this purpose.
- **Added** — `jazzx_sdk.finance.vocabulary` (plan_JAPES_2_2_0_LINE_VOCABULARY.md, Phases 1-2):
  `LineVocabulary`/`LineDefinition`/`Recognition` — a pack's declared, versioned chart-of-accounts
  vocabulary (the SDK ships none; three private alias-list copies already exist in JACI alone,
  none of which are enforced to agree), and `resolve()` — matches a raw (key, label) pair against
  it, returning a `Resolution` naming the exact `MatchKind` (`exact_key`/`alias_key`/`exact_label`/
  `normalized_label`/`substring`/`unmatched`) and matched term. Substring matching is opt-in per
  line, never a global fallback; two lines matching at the same strength resolve to `unmatched`
  naming both, rather than silently picking the first.
- **Added** — Phase 3 of `LINE_VOCABULARY`: `structure_statement(..., vocabulary=...)` — when
  supplied, the extraction prompt carries the statement type's closed set of canonical keys
  instead of letting the model invent one, with an explicit escape (null key, label kept) when
  nothing fits. A key the model returns anyway that still doesn't resolve is never silently
  accepted — nulled and recorded in the new `StructuredStatement.vocabulary_gaps`
  (`VocabularyGap`). The vocabulary also populates each line's `SpreadLine.semantics`. Omitting
  `vocabulary` leaves behavior exactly as before.
- **Added** — Phase 4: `ResolutionContext.vocabulary` — a `SCOA_LINE`/`DOCUMENT_FIELD` binding's
  canonical `ref` now resolves through a supplied `LineVocabulary` rather than requiring `lines`
  to already be keyed by that ref, letting a caller's private candidate map be deleted rather than
  moved. Proved by rewriting JACI's `dsl_catalog.py` to use a vocabulary instead of its own
  `_CANDIDATES` dict — the existing sixteen-case parametrized fixture (`test_metric_result.py`)
  still passes byte-identical. `None` (default): no behavior change. `LINE_VOCABULARY` is now
  fully landed (all 4 phases).
- **Fixed** — `LineVocabulary`'s duplicate-key/-alias validator now scopes alias uniqueness *per
  statement type* rather than globally (canonical keys themselves stay globally unique, since
  `by_key()` has no statement type to disambiguate). Found while authoring JACI's real chart of
  accounts: the same raw term legitimately means different things in different statements (e.g.
  `accounts_receivable` as a balance-sheet balance vs. a cash-flow change-in-AR line) — the
  original global check would have wrongly rejected that as a collision.
- **Fixed** — `SpreadLine.semantics: LineSemantics | None` — the flow/stock override from Phase 2
  of the period-model work now lives on the line itself, not only as a `construct_ltm(...,
  line_semantics=...)` call-time dict. A durable per-line correction (e.g. a balance-sheet memo
  line that's actually a flow amount) shouldn't depend on every caller remembering to pass the
  override at call time. `_semantics_for()` checks the call-time dict first (for a one-off
  override a caller doesn't control the line data for), then the line's own `semantics`, then the
  per-statement-type default — additive, no existing behavior changes.

## [2.2.0] - 2026-07-26

- **Added** — `jazzx_sdk.finance.periods` (Financial Spreading PRD v0.4 §7.6, FR-PER): `Period`
  (identity = date range + kind, not the display label) and `PeriodSet` (aligns periods across
  differing fiscal calendars onto one timeline); `LineSemantics` (flow/stock, defaulted per
  `StatementType`, overridable per line); `Assurance` (audited/reviewed/compiled/tax/
  company_prepared/internal_interim/management_schedule/derived, ordered to match FR-SRC-2's
  default source-precedence hierarchy) + `ASSURANCE_RANK`; `construct_ltm()` (flow lines by
  addition of the current interim + the prior year's non-overlapping tail, stock lines at the most
  recent period-end, never a roll-forward) with typed `Refusal` guardrails (mismatched fiscal
  cutoff, unequal interim lengths, missing prior-year interim — never fabricated). Verified against
  the PRD's real Appendix D worked example (RB LTM Sept-2023): Revenue 57,581 + (61,443 - 44,326) =
  74,698, computed exactly; a permanent regression test (FR-PER-6) guards against ever
  transcribing the reference workbook's incorrectly-signed human note instead of the verified
  (and different) formula. `FinancialSpread.period_set` added alongside the existing
  `periods: list[str]` — additive, no existing caller (JACI's `analytics.py`/`template.py`/
  Streamlit views/Excel export) changes; verified against JACI's full test suite with zero JACI
  changes.
- **Added** — `jazzx_sdk.expressions` (Financial Spreading PRD v0.4 §7.7, FR-CUS): `MetricDefinition`/
  `InputBinding`/`BindingKind` (assumptions are a distinct binding kind per FR-CUS-6 — an assumed
  input can never render as a reported figure); `parse()` — a small hand-written recursive-descent
  grammar, not `eval()` (arithmetic, multi-period refs `prior`/`ltm`/`avg`/`cagr`, lazily-evaluated
  `if`/`min`/`max`/`cap`, cross-entity aggregation left as an explicit refusal stub); `evaluate()` —
  a governed `MetricResult` with full input/derivation provenance and weakest-input confidence,
  typed `Refusal`s (never `None`/silent-zero) for a missing required input, below-floor confidence,
  or division by zero; `validate()` — undefined references, unit mismatches, unreachable
  conditional branches, and circular metric references (DFS over the `CUSTOM_METRIC` graph), all
  checked before the evaluator ever runs (FR-CUS-10). Verified against the PRD's real Appendix B
  worked example (Adjusted Fixed Charge Coverage: `6.67`) and the two named grammar cases (FR-ADJ-4
  conditional bad-debt addback; FR-ADJ-6 owner-comp capped at policy limit).
- **Changed** — the canonical `Policy`/`Rule` condition type widened from `Expression` alone to
  `Optional[Union[Expression, DslExpression]]` (new `jazzx_sdk.fabric.canonical.DslExpression`, a
  DSL-authored boolean formula over context fields), so a policy rule can now express compound
  conditions (`leverage_x <= 3.5 OR covenant_waived == 1`) that don't fit a single flat
  field/operator/value triple. Evaluated via a new, separate `evaluate_over_namespace()` — a
  lightweight AST walk over a flat `{field: value}` dict, distinct from the full
  `MetricDefinition`/`ResolutionContext` machinery, since a policy condition reads context fields
  directly rather than resolving chart-of-accounts bindings. `DefaultPolicyExpert.check_compliance()`
  and `PolicyRegistry`'s backward-compat clause shim both branch on the condition's type; the
  existing flat-`Expression` path is byte-for-byte unchanged. Additive — every existing
  flat-`Expression` policy in JACI's AML, KYC, and C&I registries loads and evaluates identically
  (verified against JACI's full test suite with zero JACI changes).

## [2.1.5] - 2026-07-26

- **Fixed** — `_html_to_markdown` (pandoc path) and `_extract_text_from_html` (fallback path) let
  hidden HTML content (`style="display:none"`, `visibility:hidden`, the `hidden` attribute) leak
  into "faithful" conversion output — e.g. a SEC 10-K's inline-XBRL fact block, which filers wrap
  in a hidden `<div>` at the top of the body: raw taxonomy references and context IDs with no
  reader-visible content, dumped ahead of the actual statements. New shared
  `documents.strip_hidden_elements(soup)` removes it via a real parser (a regex can't reliably
  balance nested divs); extends the existing `<script>`/`<style>`-stripping precedent rather than
  contradicting the "never drop content" faithful-conversion contract — hidden content is
  presentational plumbing a reader never sees, not narrative text. Verified against a real 10-K:
  every one of 755 real financial figures preserved identically; only the hidden XBRL block and
  empty hidden spacer `<td>`s were removed.
- **Added** — `AzureDocIntelligenceProvider.convert_to_json()` / `analyze_result_to_json()` — a
  page-structured JSON view (role-classified paragraphs, raw table cells) alongside the existing
  markdown transform, sharing the same `analyze()` call. `DocumentIntelligenceProvider` gained an
  optional `convert_to_json()` (default: unsupported); `LocalStubProvider` (renamed from
  `LocalMarkdownStubProvider`, now that it stubs both formats) mirrors it with a co-located
  `<stem>.json` stub. Every page has a stable schema (fields always present, never conditionally
  omitted), unlike kernel's v1 dynamic-shape equivalent.
- **Added** — `jazzx_sdk.tools.extraction.locate_regions_from_json` / `ExtractionTemplate.locate_json`
  / `flatten_table_from_json` — JSON-sourced counterparts to the markdown/HTML region+table locators,
  for a document converted via `analyze_result_to_json()` (DocIntel/scanned fallback) instead of
  markdown: table-mode anchors read Azure's real table cells directly (a markdown rendering has no
  `<table>` tags for the HTML-based locator to find), and window-mode search reuses the existing
  text-window logic over a plain-text flattening of the JSON. Same anchors/templates work with either
  locator.
- **Fixed** — `DocumentAgent`'s per-field grounding check (`_grounded`) treated every whole-number
  float as ungrounded: `str(1000.0)` is `"1000.0"`, and digit-stripping the `.` left a spurious extra
  digit (`"10000"`) that could never match the source's real digit run (`"1,000"` → `"1000"`) —
  silently capping confidence below the admission floor and refusing the value. Financial figures are
  commonly whole numbers, so this was a systemic false-refusal risk for exactly the kind of data
  `DocumentAgent` is meant to extract with confidence.
- **Added** — the document pipeline (`agents.document.pipeline`) gained a `collection` route alongside
  `single`/`package`/`refuse`, fanning out via `DocumentAgent.process_dir`: a folder of documents
  (`DocTurn.folder_path`), a whole Knowledge Hub collection (`collection_id`, synced into `folder_path`
  first via `process_dir`'s existing sync), or a standalone zip archive (`file_path` ending `.zip`,
  unpacked into a scratch dir under `work_dir` first). No custom `detect()` needed for any of the three
  — the route is inferred from which `DocTurn` fields are populated; a custom `detect()` is only for
  package-vs-single on a combined single file, which can't be inferred from shape alone.
  `agent.py::_unpack_zip` renamed to `unpack_zip` (now shared with the pipeline's zip-unpack case).
  `DocTurn.degrade` changed to `bool | None = None` — a real bug caught before it shipped: forwarding a
  shared `False` default to both routes silently overrode `process_dir`'s own better default (`True`,
  one bad file in a folder shouldn't sink the batch) with `process_package`'s (`False`, a bad segment
  does call the whole combined document into question) whenever a `DocTurn` didn't set `degrade`
  explicitly. `None` now means "let the underlying `DocumentAgent` method's own default stand."

## [2.1.4] - 2026-07-25

- **Fixed** — `KnowledgeHubClient.create_document()` and `.upload_ontology()` (both file-upload
  methods) no longer rely on the generated client's own `Body*.to_multipart()`, which regressed for
  *every* binary-file-upload endpoint on `client-api@main` (commit `4bcf1f4` / PR #61, unfixed as of
  2026-07-25 — confirmed on both `BodyUploadBinaryDocument` and `BodyUploadOntology`): it stopped
  calling `File.to_tuple()` and instead sends `str(File(...)).encode()` — a Python repr of the wrapper
  object, not the real bytes. A small upload "succeeded" with the repr string stored instead of the
  actual content; a larger one 400'd (`"Part exceeded maximum size of 1024KB"`) once the
  ~3-4x-inflated repr crossed the multipart part-size limit. Both methods now build the multipart
  payload themselves via one shared, tested primitive (`_MultipartBody`), independent of whichever
  commit of the generated client is installed.
- **Changed** — `kernel-client`/`knowledge-hub-client` pinned to a fixed commit (`rev=`) instead of
  tracking `client-api@main` (`branch=`); `knowledge-hub-client` specifically pinned to the last commit
  confirmed *before* the regression above, so a future `poetry lock`/`poetry update` on it can't
  silently reintroduce the bug the way tracking `main` would.
- **Changed** — `fabric.graph.upload_ontology` renamed to `register_ontology_from_files` — pairs with
  the existing `register_ontology` (same underlying concept — both `create_ontology`/`upload_ontology`
  return the same `OntologyRead` shape server-side — sourced from raw file bytes instead of an
  already-parsed string/dict) rather than mirroring the KH client method's name verbatim.
  `_from_files` (not `_files`) deliberately: "register_ontology_files" reads as "register the files";
  the qualifier needs to mark *how*, not *what*. No consumer used the old name.
- **Added** — `agents.interactive.redact_before(guardrail, redact)`: wraps any `Guardrail` (an LLM
  classifier or a plain check) so it runs against redacted text instead of the raw text — for a
  leak-detection guardrail that can't reliably tell "known-safe content, already delivered elsewhere"
  apart from an actual leak, and shouldn't be asked to via a prompt instruction alone (a
  non-deterministic judgment call). Composes with `jazzx_sdk.failures.redact_secrets` (existing),
  the two new redaction utilities below, or a caller's own `str -> str` function.
- **Added** — `jazzx_sdk.failures.redact_code_blocks(text, suspicious_markers=, placeholder=)`: masks
  every fenced code block in `text`, so a legitimate reply containing generated code doesn't trip a
  classifier's "framing text + adjacent code block" leak heuristic. A block containing a
  `suspicious_markers` substring is left unredacted (a safety net — real leaked content must still
  reach whatever scans the text next).
- **Added** — `jazzx_sdk.failures.redact_fields(payload, paths, suspicious_markers=, placeholder=)`:
  the structured-payload counterpart — redacts known-safe string fields at dot-paths into a nested
  dict/mapping (copy-on-write; same suspicious-markers safety net), for content delivered to a caller
  through another channel already (e.g. generated code also handed to a UI's Apply button via a
  separate field) before it's serialized into text a guardrail or an LLM's context will see.
- **Added** — `modes.evolve.synthesize_bucket(signals, llm=, pack_id=, store=)`: the Curator's Layer 2
  synthesis (previously a `NotImplementedError` stub) — LLM-deduplicates a batch of same-tag
  `ImprovementSignal`s into one draft `GuidanceAsset`, persisted at `GuidanceStatus.DRAFT` for SME
  review via `GuidanceLifecycle`. Takes the universal `ImprovementSignal` shape, so it works the same
  whether signals came from eval-report routing or straight from `Feedback.to_signal()` (a red-teaming
  or in-context-correction batch). `ImprovementSignal` gained `feedback_id` so that provenance survives
  from `Feedback` through to the synthesized asset's `provenance.feedback_id`/`metadata.feedback_ids`.

## [2.1.3] - 2026-07-24

- **Fixed** — `KernelClient.invoke_agent()` imported names that don't match the current generated client; rewritten against the real contract (agent-name resolution, typed `messages`, async invoke-then-poll, response fetch). `session_id` is accepted but now a documented no-op (kernel has no server-side session concept on this endpoint).
- **Added** — `DocumentAgent.process_dir(on_progress=...)`: per-file progress callback for folder batch runs (the conductor-wrapped single-document path already streamed via `on_step`; the batch entry point had no equivalent). Best-effort — an observer error is logged, never breaks the batch.
- **Added** — `DocumentAgent.process_dir` now classifies per-file failures via `jazzx_sdk.failures.classify_failure`; `DirectoryResult.failures` (filename -> `StructuredFailure`) alongside the existing `failed` list, and the failure detail is persisted in `manifest.json` for later inspection.
- **Changed** — `kernel-client`'s git pin bumped to `client-api@main`'s current tip; no code changes needed (the shapes `invoke_agent()` was already written against are unchanged at the new commit).
- **Added** — `KnowledgeHubClient.get_document_metadata()` / `fabric.docs.DocStore.get_metadata()`: fetch a document's metadata (created_at/updated_at/doc_type/size_bytes/sha256/user metadata) without downloading its content. Wraps KH's dedicated `get_document_metadata` endpoint (already used by kernel's own agent tool of the same purpose), lighter than `get_document()`.
- **Added** — `DocStore.materialize()` is now idempotent across interrupted/repeated runs, when the KH client supports `get_document_metadata` (feature-detected; unaffected otherwise). Each doc's current hash (sha256, falling back to `updated_at`) is checked against a small manifest before downloading — unchanged docs with their target file still on disk are skipped. `materialize()` also gained `binary=True` (writes raw bytes instead of decoding as text — needed for PDFs/DOCX).
- **Added** — `DocStore.sync_collection(collection_id, output_dir)`: the collection-level counterpart to `materialize()` — lists a KH collection and syncs every document to `output_dir` by name, idempotently (same manifest-based skip). `DocumentAgent.process_dir(collection_id=...)` uses it to source a folder run's inputs from a KH collection instead of (or in addition to) whatever's already local; requires `docs=` (a `DocStore`) passed to `DocumentAgent()`.
- **Added** — `DbMaterializeManifestStore` (`fabric.docs.manifest_store_db`): persists `materialize()`/`sync_collection()`'s doc-hash manifest in `fabric.db` instead of a local file, keyed by a caller-chosen `scope` (defaults to `collection_id` for `sync_collection`) instead of the local `output_dir` path. Note: this survives a manifest lookup across a fresh `output_dir`, but a doc whose local file is actually gone (e.g. an ACA Job's per-execution `/tmp`, wiped between retries) is still re-downloaded — a hash match can't substitute for bytes that are no longer on disk. No new "japes db" needed: this reuses the same fabric.db pattern as `DbTurnRunStore`/`DbSuspensionStore` (japes owns a small SQLAlchemy table; the consuming service's alembic — or `fabric.db.create_all()` in dev/test — creates it).

## [2.1.2] - 2026-07-21

- **Fixed** — `HandlerContext.job_id` was the queue transport id in queue mode, the business id elsewhere; unified via `job_id_for()`. Transport id moved to `queue_message_id`.
- **Fixed** — inbound `traceparent` was never attached to the active OTel context; `attach_incoming_trace_context` now does, at all three entry points.
- **Fixed** — outbound calls never propagated the active trace; `inject_current_trace_context` closes it via `default_request_headers()`.
- **Fixed** — trace propagation was entangled with the kernel identity allowlist; decoupled via `with_trace_context`.
- **Added** — `KernelClient.request_headers_provider` (PAGI-1612 allowlist), matching `KnowledgeHubClient`.
- **Added** — `KnowledgeHubClient.create_entity_v2` / `read_entities_v2` for KH's v2 entity API.
- **Fixed** — `pillow` >=12.3.0: clears 13 Dependabot alerts (transitive via `matplotlib`).
- **Fixed** — `ConductorEngine.resume()` was reusable; a `Suspension` is now single-use (rejects a second resume).
- **Fixed** — a stalled `on_step` observer could block a conductor step indefinitely; now bounded by `on_step_timeout`.
- **Fixed** — `fan_out` left siblings running after a failure; now cancels and drains them before propagating.
- **Added** — `ConductorEngine.resume_durable` + `SuspensionStore`/`InProcessSuspensionStore`/`DbSuspensionStore`: an atomic-claim durable resume path for HITL suspensions across processes (non-BPMN case).
- **Added** — `timeout` on `run_offloaded`/`best_effort`/`BestEffortBackend._offload`/`_best_effort`/`_background`: a stalled backend call degrades/raises after the bound instead of hanging the caller forever. Opt-in (`None` default preserves prior behavior).
- **Changed** — `DbTurnRunStore`/`DbSuspensionStore`'s duplicated `FOR UPDATE SKIP LOCKED` + sqlite-fallback logic factored into `fabric.db.locking.skip_locked_first`/`skip_locked_all`; no behavior change.
- **Fixed** — `KernelClient` had no connection-pool cap (inherited httpx's default 100 max connections); now defaults to 20/10, matching `KnowledgeHubClient`, with an overridable `limits=` param.
- **Fixed** — a slow claimer's late `heartbeat`/`mark_resumed`/`mark_failed` could silently resurrect a `TurnRun`/`Suspension` already reaped to `FAILED` (claim_token survives reap; only status changes) — a lost-update under unlocked read-then-write. All four stores (`InProcessTurnRunStore`, `DbTurnRunStore`, `InProcessSuspensionStore`, `DbSuspensionStore`) now fence on terminal status too, and the DB stores read-modify-write under a blocking row lock (`fabric.db.locking.blocking_locked_first`/`_all`).
- **Added** — `flush_mlflow_async_trace_queue()`: drains MLflow's async trace-export queue and pins `MLFLOW_HTTP_REQUEST_TIMEOUT` before a worker process exits, so a recycled Celery worker doesn't drop buffered spans (traces stuck "in-progress" with no data).
- **Added** — `MessageHeader.session_id`: a dedicated conversation-stable key for handler memory-keying, distinct from `correlation_key` (which stays request-unique). `correlation_key`'s docstring no longer recommends repurposing it for this.
- **Added** — `JapesQueueClient`: the producer-side counterpart to `QueueProcessor` — `enqueue_invocation` + `await_response` for a caller that invokes japes over the queue and waits for the correlated reply, instead of hand-rolling a response-queue poll loop.
- **Added** — `jazzx_sdk.failures`: `classify_failure`/`StructuredFailure`/`FailureCode` (type-based classification with a regex fallback, pack-extensible via `register_failure_rule`) and `redact_secrets`. Wired into `CaseResult`/`ExperimentRun`/`EvaluationHarness` so a failed eval run carries a structured code/message/action, not just a raw string. `mlflow_bridge`'s sensitive-key list now sources from the same `SENSITIVE_KEY_NAMES`.
- **Fixed** — `gitpython` >=3.1.52, `pyasn1` >=0.6.4, `setuptools` >=83.0.0: clears the remaining 7 open Dependabot alerts (env-var exfiltration, git-option command injection, ASN.1 resource exhaustion, sdist exclusion bypass; all transitive).

## [2.1.1] - 2026-07-20

- **Added** — **feedback on interactive-agent turns** — `InteractiveResponse` now carries the turn identity (`conversation_id` / `message_id` / `trace_id`), stamped on every reply by `respond`/`respond_stream` (both gained optional `conversation_id`/`trace_id` args; `conversation_id` defaults to `session_id`). `response.feedback(reaction=…, rating=…, text=…)` builds a `Feedback` linked to that exact turn — so a chat UI can wire thumbs/ratings/corrections into the feedback→trace→learning spine in one line, instead of hand-threading identifiers.
- **Added** — **human-in-the-loop suspend/resume in the conductor** — a step can `raise SuspendRun(key, reason=, payload=)` to pause a run and hand off to a human (e.g. an SME approving a flagged spread). `ConductorEngine.run()` returns a `ConductorRun` with `status == "suspended"` and a `Suspension` (the payload to show the approver + the captured run state); `engine.resume(suspension, resolution)` continues from the next step with the decision injected as the suspended step's output (a downstream step can `state.halt` on rejection). In-process by default; the `Suspension` is persistable for cross-restart resume. Suspend is supported for top-level steps (raising inside a loop is rejected with a clear error).
- **Added** — **DOCX + ZIP intake** — `convert_document` now handles `.docx` (pandoc → table-preserving markdown, `python-docx` fallback). `DocumentAgent.process_dir(..., include_zips=True)` unpacks any `*.zip` container into `output_dir/_unpacked/<stem>/` and processes its `pattern`-matching contents recursively (unpacking is incremental on the zip's content hash; unpacked files are keyed `<stem>/<relative path>`). Closes the plan's PDF/DOCX/ZIP input requirement.
- **Added** — **structure-aware chunking** — `chunk_by_headings` splits a large untemplated doc along its markdown heading tree (chapters/sections/sub-sections — what a table of contents renders) instead of arbitrary character windows, so a chunk is a coherent unit (a statement stays with its heading). It keeps whole sections together, descends into sub-sections only when a section alone exceeds the budget, and falls back to character slicing for heading-less spans (offset-based → chunks concatenate back to the original). It's now the default chunker for `extract(..., chunk_chars=…)`; `chunker=` accepts `_chunk_by_chars` or any `(text, max_chars) -> list[str]`.
- **Added** — **package completeness check** — `check_completeness(results, required, min_confidence=…)` → `CompletenessReport` reconciles the doc types `process_dir` found against a required-doc-type checklist: `present` / `missing` / `unexpected`, plus `by_type` (which files satisfy each type) and `is_complete`. The "is this loan package complete?" gate for a classified folder (Stage 1).
- **Added** — **document pipeline: incremental folder ingestion + chunked untemplated extraction** — the raw-folder-of-PDFs flow. `DocumentAgent.process_dir(folder, pattern="*.pdf", output_dir=".japes", …)` lists a directory and processes each file (per-file tracer span, bounded concurrency), writing the `<stem>.md` conversion + `<stem>.result.json` + a `manifest.json` under `output_dir`. A `<stem>.md` already staged in `output_dir` (e.g. copied from blob) is **reused** as the conversion, skipping DocIntel/OCR. **Incremental/resumable**: a file whose content hash still matches a `complete` manifest entry is skipped; a new/overwritten (changed-hash)/previously-failed file is (re)processed — the manifest is a recreatable content-hash cache (losing it costs redo, not information). Classify-only by default (identify a folder's docs) or extract each with a shared `schema`; returns a `DirectoryResult` (processed/skipped/failed). And `extract(..., chunk_chars=…)` (also `DocumentAgentSpec.chunk_chars`) chunks a large *untemplated* readable doc, extracts each chunk, and merges field-wise — so a big doc without a template no longer overflows the model context (the templated path already narrows to located regions).
- **Added** — **feedback→trace→learning spine**: `Feedback` now carries the chat-turn linkage (`conversation_id` / `message_id`, alongside the existing `trace_id`), with `Feedback.for_turn(...)` to capture it and `FeedbackStore.list(conversation_id=/message_id=/trace_id=)` (in-process + `fabric.db`, indexed) to retrieve a turn's or conversation's feedback. Closes the gap between per-turn feedback and the run that produced it: capture (linked to the run's conv/message/trace tags) → query → `synthesize_cases_from_feedback` → `optimize_prompt`, and `Feedback.trace_id` resolves to the full trace via `TraceSource`.
- **Added** — **versioned invocation contract + boundary tests**: the queue envelope now carries a canonical `INVOCATION_CONTRACT_VERSION` (single source on `MessageHeader.version` / `build_invocation`), `models.py` documents the contract (envelope, correlation-key semantics, identity/security-context, distributed tracing, forward-compat), and `tests/test_invocation_contract.py` freezes the wire shape — a dropped/renamed field, a version bump, or correlation-key churn now fails a test instead of drifting silently across producer/consumer versions. Unknown fields are tolerated on parse (a newer producer never breaks an older consumer).
- **Added** — **groundedness guardrail + shared safety fragment** (`agents.interactive`): `grounded_guardrail(llm, get_context=…)` — an output guardrail that blocks an answer making claims its grounding context doesn't support (the "don't let an ungrounded/hallucinated answer reach the user" gate; passes when there's no context to check). And `with_safety(instructions)` / `SAFETY_INSTRUCTIONS` — the domain-neutral no-invention / retrieved-content-is-data injection-defense / no-bias-or-steering / stay-in-scope prose, authored once and composed into a skill's instructions instead of copy-pasted per skill.
- **Changed** — **env-var naming consolidated** onto the `JAPES_`-preferred convention via one resolver (`jazzx_sdk.env.env(*names, default=)` — first name set wins). Every japes-owned config var now accepts a `JAPES_`-prefixed name (preferred) with its legacy name as a back-compat fallback: fabric KG defaults (`JAPES_KH_COLLECTION_ID | KH_COLLECTION_ID`, `JAPES_KH_ONTOLOGY_ID`, `JAPES_FABRIC_MODE | FABRIC_MODE`), fabric persistence (`JAPES_CONVERSATION_BACKEND | JAZZX_CONVERSATION_BACKEND`, `JAPES_DB_BACKEND | JAZZX_DB_BACKEND`, `…_DB_SQLITE_PATH`, `…_BLOB_BACKEND`, `…_BLOB_CONTAINER`), KH URL/token/user/security-context, `JAPES_MOCK_KH_DATA_DIR`, `JAPES_PROCESS_ENGINE_BASE_URL`, and the Azure storage vars. Existing (bare / `JAZZX_` / `AZURE_`) names keep working. Vendor/ecosystem-standard vars (`OPENAI_API_KEY`, `OTEL_*`, `AZURE_DOCUMENT_INTELLIGENCE_*`, `DATABASE_URL`, …) are deliberately left un-prefixed. Scattered `os.getenv("JAPES_X") or os.getenv("X")` chains routed through the resolver; `.env.template` + README reflect the canonical names.
- **Fixed** — **`.env.template` was stale and used wrong var names** (reported): it listed `JAPES_AZURE_STORAGE_ACCOUNT_URL` / `JAPES_USE_MANAGED_IDENTITY`, which the queue settings reader never honored — a user copying it would omit the *required* storage URL and hit a startup error. Regenerated it to be complete and correct (grouped; newer vars commented-optional), and reconciled the README + `settings.py` docstring. To honor the intended `JAPES_`-namespacing convention uniformly, `create_queue_settings_from_env` now accepts `JAPES_AZURE_STORAGE_ACCOUNT_URL` / `JAPES_AZURE_STORAGE_CONNECTION_STRING` / `JAPES_USE_MANAGED_IDENTITY` as **preferred aliases** (bare `AZURE_*` remains the fallback), matching how KH/security vars already resolve (`JAPES_` first, bare second).
- **Added** — **`KernelClient.call_parallel`** — run a mix of kernel tool + agent calls concurrently (bounded, order-preserved, optional per-call degrade), built over `conductor.fan_out`. The client-side ergonomic equivalent of kernel's `parallel_tool_agent_execution`, via `KernelToolCall` / `KernelAgentCall` specs — eases migrating kernel workflows that use parallel tool/agent execution onto japes.
- **Changed** — **web search is now backend-agnostic** — a `WebSearchProvider` seam (like `DocumentIntelligenceProvider`) instead of a hardcoded vendor tool. `KernelWebSearchProvider` (default when a kernel client is present) targets a configurable kernel search tool (default `perplexity_search`), and native providers (Tavily/Google/direct API) can implement the same seam without kernel. `WebSearchConnector` composes a provider + native `read_from_url`. Fixes a latent bug: the connector previously called a non-existent kernel tool `web_search` (kernel's is `perplexity_search`), silently returning no results in real mode.
- **Changed** — model-name identity/normalization split out of `llm/cost.py` into a new leaf `llm/model_identity.py` (`provider_for_model`, `parse_model_tier`, `normalize_model_name`). `cost.py` predates model cards and had become a catch-all (pricing data + cost calc + identity utils); the identity helpers are now their own layer that both `cost.py` and `model_cards.py` build on (no cycle). Pure internal cohesion — the public API (`jazzx_sdk.parse_model_tier` / `normalize_model_name`, `jazzx_sdk.utils.*`) is unchanged; no back-compat shims (nothing outside imported these from `llm.cost`).

## [2.1.0] - 2026-07-19

Platform durability & robustness enhancements — proactively hardening the SDK's runtime primitives so they hold up as usage scales.

- **Added** — **durable-runs hardening** (`jazzx_sdk.runs`): the turn-run store gains production-grade durability. `request_stop_conversation(conversation_id)` atomically stops a whole conversation — cancels its queued turns (new terminal `TurnRunStatus.CANCELLED`) and cooperatively stops the running one, in one locked transaction so a queued turn can't slip into RUNNING mid-stop (surfaced on `ResilientRunner`). `purge_terminal(older_than_seconds)` adds journal retention (the event journal is a delivery buffer, not the transcript). And `reap_stale` is now a **fenced** sweep — it locks stale rows (`FOR UPDATE`) and finalizes them in the same transaction, re-evaluating `heartbeat_at < cutoff` under the lock so a run whose heartbeat was renewed concurrently is never retired; the reaper is safe to run aggressively at real concurrency.
- **Added** — **caller-identity resolution** as a platform capability (`jazzx_sdk.get_current_user_id/email/name`): japes already *forwards* `x-security-context` / `x-user-*` downstream; it now also *resolves* the caller from that context (decoded `userId`/`userEmail`/`userName`, raw `x-user-*` fallback), so a pack attributes authorship/creator/audit by asking the platform instead of hand-rolling a base64/JSON parse. Works across HTTP / queue / event paths.
- **Added** — **MLflow-tracing robustness** (`tracing.sanitize_leaked_otel_env_vars()`): japes owns the guard that strips a platform-injected `OTEL_EXPORTER_OTLP_ENDPOINT` / `..._TRACES_ENDPOINT` (e.g. Azure Container Apps) before MLflow tracer init, so a leaked endpoint can't silently swap MLflow's exporter for a missing gRPC OTLP one and drop every span. Not auto-invoked (`setup_telemetry` uses the OTLP endpoint legitimately); call it at startup.
- **Added** — **runtime observability tracer** (`jazzx_sdk.observability`): a backend-agnostic `RunTracer` for the per-turn lifecycle — start a run correlated to the incoming trace, tag it once (`build_run_tags`: identity `incoming.*` + caller business tags), open best-effort sub-`span`s carrying a filterable `stage` label, and log params/metrics/artifacts. `NoOpTracer` is the default (every call no-ops, so a handler wraps every turn without branching on whether tracing is on); `MlflowTracer` is one backend (lazy `mlflow` extra, best-effort — a backend failure degrades to no-op, never breaks the turn), and an OTel/App-Insights backend can implement the same base. Complements `MlflowTraceHooks` (the agent span tree) by owning the run/tag/stage layer callers otherwise reinvent.
- **Added** — **`clients.KnowledgeHubLike`** — a `runtime_checkable` Protocol naming the Knowledge Hub surface the fabric layer depends on. The fabric stores (canonical/graph/rag/docs/entities/collections/opa) and the KH-backed `tools` now annotate the *role* rather than the concrete `KnowledgeHubClient`, and both the real client and the in-memory `MockKnowledgeHubClient` are checked against the contract (a `issubclass` drift guard, so a dropped method fails a test instead of at runtime against one backend). `fabric.kh_status` keys off a robust `is_mock` flag instead of sniffing the class name.
- **Changed** — agent-session helpers are now **backend-neutral**: `tracing.create_agent_session` / `create_session_engine` accept any async SQLAlchemy URL (SQLite for dev/tests, Postgres, …) and add the asyncpg driver only for the postgres scheme — fixing the prior helpers' hard rejection of a valid `sqlite+aiosqlite://` URL. `create_postgres_session` / `create_postgres_engine` remain as deprecated aliases.
- **Added** — **`tracing.AgentTraceHooks`** — the OpenAI-Agents-SDK workflow→agent→llm→tool span tree is now a backend-agnostic base: the span-tree bookkeeping, callback flow, and token/cost accumulation live once in `AgentTraceHooks`, and a backend implements only four span primitives (`_begin_root` / `_start_span` / `_end_span` / `_finish_root`). `MlflowTraceHooks` is that base against MLflow (behaviour unchanged); an OTel/App-Insights backend implements the same base. Both are built lazily so `import jazzx_sdk` stays free of openai-agents (and its transitive uvicorn).
- **Added** — **reference chat conductor** (`agents.interactive.chat`): the reusable shape of a conversational turn as a `ConductorPipeline` (validate → gate → escalate | answer | refuse → finalize) + reference step-impls. A consumer supplies only the domain hooks — a router (`classify`) and an escalation callable — plus an `InteractiveAgent`, then runs `run_chat_turn(...)`; it gets per-stage traces, stage-progress streaming, and declarative routing for free. Deliberately thin: the direct path delegates to `InteractiveAgent.respond` (which already does grounding, guardrails, sources, and history), and escalation routes to a heavier engine the pack provides. japes ships the primitives + reference; assistants (loan chat, jaci scenarios) adopt it as config.
- **Added** — **reference document conductor** (`agents.document.pipeline`): the document analogue of the chat conductor — `build_document_pipeline` (detect → package | single | refuse → emit → finalize) + reference step-impls + `run_document`. Classification-driven routing via the gate; thin — the heavy work stays in the well-tested `DocumentAgent`. `DocumentAgent.process_package` now fans out over segments **concurrently** with a per-segment tracer span (via a new `tracer=` on `DocumentAgent`), and `process` opens `convert`/`classify`/`extract` spans for per-stage latency attribution. Domain-agnostic (taxonomy/classifiers/schema are pack-supplied), so any jaci domain configures it rather than wiring bespoke agents.
- **Added** — **`conductor.fan_out`** — the missing map-over-items primitive (the engine's `Loop` is converge-until, not map): runs an async processor over a collection with bounded concurrency, a per-item tracer span, and optional per-item degrade. Turns one emitted collection into N results (a document package → N constituents, a batch → N records).
- **Added** — **conductor step guards** (declarative branching): `PipelineStep.when` carries a human/BPMN-readable guard condition and `ConductorEngine(step_guards={...})` binds the executable predicate per step id — a step whose guard is false is recorded as `skipped(guard)` and emits no progress events. This is how a pipeline branches (e.g. a gate routing direct-answer vs escalate-to-reasoner vs refuse). Mirrors the existing `Loop.convergence` + `loop_converged` split (descriptor stays declarative/renderable; the logic is testable code — no expression-eval DSL).
- **Added** — **`ConductorEngine` observability + streaming wiring** (once, for every conductor): the engine now optionally takes a `RunTracer` and a `StepObserver`. Each step opens a tracer span tagged with its `stage` (its `phase` or id) — so per-stage traces come from the engine instead of being hand-tagged per service — and fires a `StepEvent` at start/end that a host can stream as progress ("Gating… / Grounding… / Answering…"). `ExecutedStep` now carries `started_at`/`completed_at`/`duration_ms` for per-stage latency attribution. Both hooks default to no-ops (existing callers unaffected, zero cost); the observer is best-effort and never breaks the run. The pack-specific `ConductorRun → CanonicalTrace` mapping intentionally stays pack-side (its mode/actor/autonomy are domain semantics the descriptor doesn't carry).
- **Added** — **best-effort backend contract** (`jazzx_sdk.concurrency`): `run_offloaded` (run a blocking backend call off the event loop), `best_effort` (offload **and** swallow — a side effect that must never block the loop nor break the turn), and the `BestEffortBackend` mixin (`_offload` / `_best_effort` / `_background` / `_drain`) that formalizes both guarantees plus a drained-at-boundary background-task tracker. Backend-neutral — no vendor in the contract.
- **Changed** — observability/tracing backends now honour that contract, so MLflow I/O no longer stalls the agent loop. `MlflowTraceHooks` runs its per-step span start/end off the loop (opt-in via `AgentTraceHooks._offload_blocking`, so any blocking backend inherits it); `MlflowTracer.run`/`span` offload their MLflow calls; and `RunHandle.log_params/metrics/dict` are backgrounded and drained before `end_run` (non-blocking, and never logged after the run closes). Behaviour is unchanged — only where the blocking work runs.
- **Changed** — bumped the `common` submodule pin to pick up platform fixes (telemetry fallback-handler recursion guard, settings deprecation, dependency vulnerabilities) and the new `final_result` streaming event. `jazzx_sdk.streaming` now re-exports `FinalResultEvent` (guarded — still imports against an older common). The Redis→SSE reader was already forward-compatible with unknown event types (raw pass-through, terminates only on `done`/`error`); covered by a test so a newer producer's events are never dropped by an older japes.
- **Added** — **idempotent, provenance-carrying writes across the fabric** (`fabric.idempotency`): idempotency and audit provenance are now a single write concern with one contract spanning every fabric store, instead of a per-backend bolt-on. `content_fingerprint` computes a stable, backend-portable SHA-256 key *client-side* (so dedup works before the write and against a backend that hasn't adopted native content-hashing); `WriteOutcome` returns the full object, its ref, a `created` flag, the fingerprint, and `Provenance` — so a caller learns created-vs-existing without reading an HTTP status or reconciling an id-only response. `fabric.entities.ensure(...)` and `fabric.docs.ensure(...)` create-once/return-existing against the Knowledge Hub (pre-check by hash + lost-race re-resolve), and `fabric.db.Repository.ensure(obj, key=...)` gives the relational store the same contract (unique-constraint race re-resolved, not raised). Document dedup now stamps *both* our `content_hash` and KH's native `sha256` key so the two dedup paths agree on document identity.
- **Added** — **`CallerIdentity`** (`jazzx_sdk.CallerIdentity`): the identity accessors bundled into one resolved value — `CallerIdentity.from_context()` (HTTP/queue/event), `.user_id/.email/.name`, `.is_anonymous`, and `.propagation_headers()` (the live outbound identity set). `Repository` auto-stamps `created_by_user_id`/`created_by` audit columns from it when a model exposes them (opt-in by column presence). The header-provider helper is now public as `default_request_headers`.
- **Added** — **read-back bases `TraceSource` and `evaluation.ExperimentStore`** — the write side already had pluggable backends (`RunTracer`, `EvaluationReporter`); the read side now matches. `TraceSource.read_trace(...)` reconstructs a completed run into a fabric `CanonicalTrace` (so `Decision.trace_id` resolves to a real Trace wherever the run was recorded); `ExperimentStore.write/read` persists and reconstructs an `ExperimentRun`. `MlflowTraceSource` / `MlflowExperimentStore` are the first backends; the MLflow translation stays in the `mlflow_bridge` helpers.

## [2.0.0] - 2026-07-16

A governed-composition release. Documents, packs, and pipelines become composable with provenance and
confidence carried end to end: a **document-processing chassis** that refuses sub-floor values rather than
writing them degraded; **pack composition** (`depends_on` fragment merge + a conductor `StepRegistry` so
capabilities publish step impls packs weave by reference); **governed guidance assets** (the retrieve-and-
inject learning loop); **multi-pass reconciliation**; plus platform additions (prompt-cache-key routing,
OTLP tracking→traceparent, tool-output compression). Additive except one behavioral change — `fabric.rag`
now **propagates** `KnowledgeHubAccessError` (401/403) instead of swallowing it as an empty result
(see Fixed), so an access denial surfaces rather than silently mis-driving an agent.

### Platform additions
- **Added** — prompt-cache-key routing: `agents.build_prompt_cache_key(*parts)` (deterministic, ≤64-char, provider-safe) + a `prompt_cache_key` param on `build_model_settings` (threaded to the OpenAI `extra_args`), so the repeated turns of one logical inference route to the same backend prompt cache.
- **Added** — OTLP trace-context propagation: `events_domain.otel_ids_from_tracking` / `traceparent_from_tracking` derive a stable W3C/OTel `(trace_id, span_id)` (and `traceparent`) from an opaque upstream tracking id, so a non-OTel identifier (e.g. a process-engine run id) joins one continuous distributed trace instead of each hop starting a fresh root span.
- **Added** — tool-output compression: `tools.compression_scope` / `compress_tool_output` / `read_reference` — a run-scoped `ReferenceStore` offloads large tool outputs and injects a compact head/tail preview + a reference marker into context, with `read_reference` as the agent's escape hatch to pull the full output back. Pluggable `ToolOutputCompressor` (default `PreviewCompressor`, dependency-free; a semantic backend like headroom drops in). Opt-in; passthrough outside a scope.
- **Added** — `channels.WebSocketChannel`: outbound delivery over a `ws(s)://` connection (the persistent-connection counterpart to `WebhookChannel`), registered as `"websocket"`. Same `ChannelMessage` body + optional HMAC signature (handshake header) + retry; uses `aiohttp` (already core). Additive — `WebhookChannel` (HTTP POST, Slack/Teams) stays.

### Document-processing chassis
- **Added** — `jazzx_sdk.agents.document`: a declarative `DocumentAgent` that composes the document tools (`convert_document` → `classify_document` → `extract`) into an ingest → classify → extract → emit flow whose every emitted value carries a `SourceCoordinate` + `Confidence` (tier via `PolicyProfile` floors). A value below the admission floor is **refused** as a typed `Refusal` (`SUB_CONFIDENCE_EVIDENCE`), never written as a degraded value — the XF-1 discipline. Generic `SourceFile` (content-addressed, idempotent), `ExtractedField`, `DocumentResult`; `assert_provenance_complete` gate; `register_document_steps` publishes `doc.process` as a `StepRegistry` impl so any pack pipeline can weave document processing by reference.
- **Added** — `DocumentAgent` **classify → template routing**: extraction is routed to a template by the classified doc type (`DocumentAgentSpec.templates` mapping, else the label if it names a registered template, normalising `_`↔`-`, else schema-only tier-3); a routed template that fits nothing falls back to schema-only, a caller-supplied template still overrides. The chosen template is recorded on `DocumentResult.extraction_template`.
- **Added** — `DocumentAgent` **per-field extraction confidence** (refusal is now per-field, not all-or-nothing): each field scores at `extract_score`, capped at `ungrounded_score` when the value isn't grounded in the source text (a cheap hallucination check — verbatim or digit-run match, so `1000` matches `$1,000`), with explicit `field_scores` overrides for pack-known-reliable fields.
- **Added** — `DocumentAgent.process_package(pdf, schemas=…)`: **combined-document split + fan-out**. Splits a combined PDF into constituent documents (`split_document` — outline or page-classification, no DocIntel), then runs `process` on each; `schemas` maps a doc-type label → extraction schema (a segment whose split label has a schema is extracted, others classify-only). Returns a `PackageResult` (the combined-file anchor + a provenance-complete `DocumentResult` per constituent, each with its own source anchor + page range). `register_document_steps` also publishes `doc.process_package` as a `StepRegistry` impl (`emits: PackageResult`).
- **Added** — `tools.AzureDocIntelligenceProvider`: the cloud-OCR implementation of the `DocumentIntelligenceProvider` (`di_provider`) seam — the opt-in last-resort fallback for scanned/rasterized documents (v2 stays readable-first). `convert(file_path)` reads bytes → Azure Document Intelligence (`prebuilt-layout`) → section-aware markdown. Split into a **pure** `analyze_result_to_markdown(result)` transform (sections → paragraphs/tables/figures, `**[Page N]**` markers, markdown escaping — duck-typed, no `azure` import) plus a thin client wrapper (endpoint/model from args or `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`/`_MODEL_ID`, injectable client). New optional `azure` extra (`pip install 'japes[azure]'`).
- **Added** — `DocumentAgent` **authority-gated admission**: a sub-floor value that would be refused can instead be **admitted by an authorized attestation**. `process`/`extract` accept `attestations` (field → `FieldAttestation(actor_class, human_initiated)`); a sub-floor field with an attestation that passes `authority.check_action` on the spec's `cell_ref` is admitted and marked `ExtractedField.attested_by` (the honest extractor score is kept — the admission is the attester's), otherwise it is still refused. Construct with `DocumentAgent(spec, authority=<AuthorityMatrixV2>)`.
- **Added** — `DocumentAgent.emit_entity(result, …)` + `materialize(result, schema)`: **emit the typed domain object to `fabric.entities`**. `materialize` assembles the schema instance from the *admitted* fields (refused fields omitted, never defaulted-in); `emit_entity` persists it, but when `schema` validation fails because a required field was refused it returns a typed `Refusal` (`PRECONDITION_FAILED`) instead of writing a partial/degraded object. The stored `json_value` is the domain object plus collision-safe `_source_file_id` / `_doc_type` / `_provenance` keys (pydantic field names can't start with `_`), so provenance is retained at rest; `entity_type` defaults to the classified doc type and `collection_id`/`ontology_id` fall back to the spec.

### Pack composition — dependency & fragment merge
- **Added** — `depends_on:` manifest key + `PackManifestLoader.resolve_dependencies` (ordered closure, deps before dependents, cycle detection → `PackDependencyError` naming the path) and `merged_assets(kind)` (fragment merge for playbooks/evidence_types: honors each edge's `fragments` filter, stamps `source_pack_id`/`source_pack_version`, and fails loud on an asset-id collision — no last-writer-wins). `Pack.playbooks`/`.evidence_types` return the merged view when the pack declares dependencies (`Pack.from_manifest(resolve_deps=)`); byte-identical local list otherwise. Re-declaring an imported id is a collision (fails loud); genuine narrowing stays in the Pack→SBA→Overlay→EP chain, not manifest merge. Unblocks JACI's `cl_of_core`/`cl_sp_core` importing shared ci-spread-core playbooks.

### Pack composition — conductor step registry
- **Added** — `jazzx_sdk.conductor.StepRegistry`: cross-pack step binding so a capability module can publish a named step implementation any pack pipeline weaves in by reference. `PipelineStep.impl` (optional) names a registered impl; `ConductorEngine(..., registry=)` resolves it when the scenario didn't bind that step id (explicit `components` still win, so a scenario can override a capability step). `register` fails loud on a conflicting re-registration; `ConductorPipeline.validate_against_registry` / `from_yaml(registry=)` catches unknown impls and `emits` mismatches at load. Pipelines without `impl` are byte-identical (unchanged behavior).

### Multi-pass reconciliation
- **Added** — `jazzx_sdk.reconcile`: vote N candidate observations of the same fact down to one **single-source** winner (value and every co-travelling field come from one pass, so a value can't be paired with a mismatched calculation or citation). Domain-agnostic `Candidate[T]`/`make_candidate`/`reconcile`/`reconcile_grouped`; deterministic verdict-agnostic vote with empty-dedup, core-completeness tiebreak (provenance excluded so a citation can't flip the value), representative selection (provenance included), earliest-source final tiebreak. Returns an auditable `Reconciliation` (vote counts, tie flag), not just the winner. First consumer: commercial-lending spreading over parallel extraction passes.

### Governed guidance assets (learning loop)
- **Added** — `fabric.guidance`: SME-approved, scoped guidance retrieved and injected per query (not baked into a prompt). `GuidanceAsset` (content-addressed `version` via `content_version`; `applicability` dims are pack-defined, never enumerated by the SDK; `to_guidance_ref` feeds `CanonicalDecision.guidance_refs` so effectiveness is computable). `GuidanceStore` (protocol + `InProcessGuidanceStore` + `RagGuidanceStore` over one KH collection). Wired onto `KnowledgeFabric` as `fabric.guidance` (config `guidance_collection_id`).
- **Added** — lifecycle admitted by `jazzx_sdk.statemachine` (`GUIDANCE_LIFECYCLE` table + engine): `GuidanceLifecycle` is a thin coordinator, not its own state machine. Deploy runs post-admission gates that return typed `Refusal`s (not exceptions): validation (`guidance_validation_blocked`/PRECONDITION_FAILED, flags in `domain_extensions`) and conflict (`guidance_conflict`/POLICY_CONFLICT_UNRESOLVED, `ConflictReport`). `GuardrailGuidanceValidator` composes the existing guardrail primitives; `detect_conflicts` flags near-duplicates (applicability overlap + trigger similarity). `supersede`/`rollback` never hard-delete.
- **Added** — `fabric.guidance.retrieve`/`render_guidance_block`/`to_guidance_refs`: best-effort retrieval that degrades to *no guidance applied* on fabric failure but lets `KnowledgeHubAccessError` propagate.
- **Added** — EVOLVE/PROVE integration: `evaluation.structure_feedback` (feedback → review-ready `GuidanceDraft` → `to_asset`), `evaluation.validate_guidance` (before/after harness over `PredictFn`/`TrainCase`; two `ExperimentRun`s sharing a `case_set_hash`; surfaces over-firing as per-case regressions), and compounding metrics `override_learning_rate`/`guidance_effectiveness`/`reusable_asset_growth`.

### Fixed
- **Fixed** — `fabric.rag` now re-raises `KnowledgeHubAccessError` instead of rewrapping it as `KnowledgeFabricError`, so an access denial isn't masked as an empty result at the fabric boundary (the KH-client discipline, extended to the RAG store).

## [1.9.9] - 2026-07-09

### Resilient interactive runs
- **Added** — `jazzx_sdk.runs`: durable, stoppable, resumable InteractiveAgent turns. `TurnRun` (keyed to `trace_id`; named to avoid the `ExperimentRun`/`ConductorRun` collision) + an append-only `TurnRunEvent` journal mirroring the live `InteractiveStreamEvent` vocabulary; `TurnRunStore` (protocol + `InProcess` + fabric.db `DbTurnRunStore`, with claim/heartbeat/stop-flag/`has_active_run`/`reap_stale`); `ResilientRunner.execute` (journals every event, tees to an optional live sink, snapshots partial, **cooperatively** stops via the durable `stop_requested` flag — never `task.cancel`) and `resume` (journal replay-then-follow, surviving reconnect/restart). Dispatch reuses the existing queue runtime; stop is a durable cross-pod flag. `TurnDispatcher` enforces per-conversation FIFO (durable `claim_next`: single-running + oldest-queued, so concurrent workers can't double-run a turn; different conversations run concurrently) and `Reaper` fails runs with a stale heartbeat (claim-fenced) on a loop. `runs.server.run_router` mounts governed start/stop/stream (SSE resume) endpoints via `GovernedRouter` (`serve(extra_routes=…)`): start enqueues (a queue worker drains), stop sets the durable flag, stream resumes the journal.

### InteractiveAgent & grounding
- **Added** — per-skill model override: `Skill.model` sets the model for that skill's sub-agent (else it inherits the parent agent's model) — different models for different sub-agents, declared as data.
- **Added** — `agents.interactive.SourceBuilder`: deterministically derive an answer's `Source`s by scanning for grounded anchors (finding mnemonics, filenames, entity ids) and resolving them, de-duped — sources are never invented. Pluggable anchor rules + an `add_index` convenience (longest-anchor-wins). (`Source` = InteractiveAgent provenance, distinct from the canonical `Citation` claim→evidence type.)
- **Added** — `tools.build_summary_index` + `tools.select_items`: the index + on-demand-fetch grounding pattern — inject a compact index into the persona (via `reference_loader`), fetch full detail only for the items the agent needs.

### Knowledge Hub client
- **Added** — typed `KnowledgeHubAccessError` (base `KnowledgeHubError`): a `401`/`403` from any KH endpoint now raises instead of being swallowed as `None`/`[]`/`False`, so an authorization denial is never conflated with "not found"/"no results" (which could silently mis-drive an agent). Enforced systemically at one choke point — a response event hook covering entities, documents, downloads, collections, ontology, policy, graph — and the client's `except` blocks re-raise it; fabric surfaces propagate it. A real 404 still maps to `None`.
- **Added** — `create_document(indexing_enabled=True)` (threaded through `fabric.docs.put`): KH flipped its upload server-default to `false`, which would silently leave japes-uploaded docs unindexed (RAG breaks). japes now sends the flag explicitly; it's feature-detected onto the generated client (body field or endpoint param) so it takes effect automatically once the client is regenerated, and warns once until then. See `docs/plans/plan_kh_client_bump.md`.

### Security
- **Fixed** — `tools.read_from_url` followed redirects automatically and validated the target only after the fetch, so a public URL redirecting to an internal address (e.g. cloud metadata) was still requested (SSRF-via-redirect). Redirects are now followed manually, validating each hop's host before fetching it, with a bounded redirect count.
- **Fixed** — a test validated a provenance URL by substring (`"claude.com" in url`); now checks the parsed hostname (CodeQL incomplete-URL-sanitization).

### Evaluation / EVOLVE loop
- **Added** — composable scorer contract (`evaluation.scorers`): optional `describe()`, `as_tool_schema()`, `ScorerSpec` + `build_composite()`; `ScorerResult` reconciled as the canonical shape with `evaluator_type`/`metrics`/`confidence`.
- **Added** — trajectory scorers (`evaluation.trajectory`): `ToolChoiceScorer`/`TrajectoryOrderScorer`/`StepEfficiencyScorer`/`ForbiddenToolScorer` over a `CanonicalTrace` + per-case `ExpectedTrajectory`.
- **Added** — adjudication policies: `all_pass`/`any_pass`/`k_of_n`/`majority`/`weighted_threshold`/`llm_judge` via `ADJUDICATION_POLICIES` + `adjudication_policy()`/`register_adjudication_policy()`; `AdjudicatorScorer.from_policy(...)`.
- **Changed** — `CostScorer` also prices LLM token usage (new optional `TokenUsage`/`model` on `ToolCall`) via `llm.compute_cost`, with a per-model breakdown; reports `cost_total_usd`/`cost_llm_usd`/`cost_tool_usd`.
- **Added** — feedback text normalization (`evaluation.feedback_text`): `normalize_feedback_text`/`extract_feedback_fields` unwrap a JSON-envelope payload; `render_feedback` applies it.
- **Added** — operational scorers (`evaluation.operational`): `LatencyScorer`/`CostScorer`/`TopologyScorer` over a run's `CanonicalTrace`, plus `aggregate_operational(traces)` (cross-trace, true wall-clock latency). `EvaluationResults.pass_rate` auto-derives from counts.
- **Added** — prompt optimization (`evaluation.optimization`): `optimize_prompt(...)` with the default `ReflectiveOptimizer` (LLM hill-climb) behind a `PromptOptimizer` protocol; `Feedback` objects and `synthesize_cases_from_feedback` feed it. `interactive_predict_fn` wires it to `InteractiveAgent`.
- **Added** — `EvalTemplate`/`EvalTemplateRegistry` (data-defined scorer bundles) and a `PromptRegistry` protocol (`InProcess`/`Db` + `promote()`).
- **Added** — feedback-quality LLM ops (`assess_feedback_quality`/`extract_actionable_items`) + shared `render_feedback`.
- **Added** — conversational-QA eval (`evaluation.qa`): `qa_case`, `AnswerCorrectnessScorer`, `CitationCoverageScorer`, `qa_scorers`.

### Domain events, state machines & automation chassis
- **Added** — `jazzx_sdk.events_domain`: `DomainEvent` envelope (frozen; carries `trace_id` + typed `VersionBundle`), `EventCatalog` (`from_index`/`from_dir`; fail-closed on unregistered names, JSON-Schema payload validation), `EventEmitter` (catalog-validated, in-process subscribers + `channels` delivery), and `traceparent`↔`trace_id` helpers. Distinct from the queue envelope (invocation vs fact).
- **Added** — `jazzx_sdk.statemachine`: data-driven object-lifecycle machines (`Transition`/`StateMachine`, `from_csv`) + a pure `TransitionEngine` (`apply` → `TransitionResult | Refusal`) enforcing the five corpus invariants (no-transition→OUT_OF_SCOPE, human-trigger refuses programmatic, profile-key guards fail-closed with a numeric-literal load-time lint, terminal states immutable, emit-on-success). Admissibility at the write boundary — not orchestration (flowable) or pipelines (conductor).
- **Added** — automation chassis (`jazzx_sdk.automation`): `Receipt`/`ReceiptStatus` (no receipt = no write), `IdempotencyStore` (`InProcess` + `EntityIdempotencyStore` on `fabric.entities`), and `GovernedAutomation` — a `run()` template enforcing idempotency → authority (`check_action`) → read-before-write drift (conflict → typed refusal) → execute → receipt → emit.
- **Added** — governed HTTP conventions (`jazzx_sdk.governed_http`): a `GovernedRouter` (mount via `serve(extra_routes=…)`) whose routes declare `mutating`/`cell_ref` and enforce `X-Trace-Id` (400 if absent) + `Idempotency-Key` on mutating routes with 409 replay of a prior receipt; `X-Trace-Id`/`X-Actor-Ref`/`X-Surface-Ref` propagate into a request-scoped context (cleared per request).

### Authority matrix & execution profile
- **Changed** — `manifest.AutonomyLevel` unified to one five-level ladder (`L0_ASSIST`…`L4_SELF_IMPROVEMENT`) with `to_numeric()`/`from_numeric()` (numeric is the storage form). Pre-1.11 value strings (`l0_advisory`…) still deserialize via `_missing_` (DeprecationWarning), each preserving its numeric level. `SurfaceType` gains `ASSISTANT`.
- **Added** — `fabric.canonical.authority`: `DecisionClass`, `AuthorityCell` (candidate/final kind by suffix; a final cell must be human-only or L0), `AuthorityMatrixV2` (`from_records`/`from_csv`, fail-closed `require_cell`). Distinct from `policy.AuthMatrix` (per-policy delegation).
- **Added** — `fabric.canonical.profiles`: `PolicyProfile` (fail-closed `get`, no SDK-default thresholds), `ClientOverlay`, `ExecutionProfile`, `SurfaceBinding` (YAML-loadable; fields beyond the resolver's consumption ride `extra`/`custom`).
- **Added** — `jazzx_sdk.authority`: `resolve_effective_autonomy` (most-restrictive intersection across cell/binding/overlay/EP + downgrades; human-only forces L0; records `contributing_layers`) and `check_action` → `EffectiveAuthority | Refusal`.
- **Added** — Governor integration: `GovernorMode(authority_matrix=…, surface_binding=…, client_overlay=…, execution_profile=…)` runs the authority check before any LLM step and short-circuits to a typed Refusal when inadmissible (absent a matrix, behavior unchanged); `BaseGovernanceSkill.ceiling_from_effective(...)` bridges an `EffectiveAuthority` to a `CeilingResult`; `PackManifestLoader` learns optional `authority_matrix`/`surface_bindings` keys.

### Governed value primitives
- **Added** — `fabric.canonical.Money`/`DecimalValue` (+ `Rounding`): exact-decimal values (reject floats, verbatim string serialization, no exponent input), currency-aware Money with derived `minor_units`, and minimal arithmetic requiring explicit rounding + mixed-currency guard. For governed values, not telemetry.
- **Added** — `fabric.canonical.Refusal` (+ `RefusalClass`, `RefusalRegistry`): typed refusals as first-class auditable outcomes (never exceptions); pack-loadable reason-code vocab over the SDK-owned class taxonomy. `server.py` `/invoke` maps a handler-returned `Refusal` to its HTTP status (registry override, else class default) — completed, not errored.
- **Added** — provenance/confidence on `fabric.canonical.evidence`: `SourceCoordinate` (typed document/workbook/section locators), `ProvenanceType` enum + extended `ProvenanceEntry`, `ConfidenceTier`/`Confidence` + `resolve_tier(score, floors)` (fail-closed; floors are profile data, no SDK defaults), optional `CanonicalEvidenceObject.confidence_detail`.
- **Added** — typed `fabric.canonical.VersionBundle` (`model_versions` required); `set_version_bundle` accepts it (stored as a dict, legacy kwargs kept); optional `version_bundle` on `CanonicalDecision`/`Artifact`/`ExperimentRun`. `finance.SpreadLine` gains additive `values_decimal` (float `values` unchanged; flip deferred). All surfaced via `jazzx_sdk.contracts`.
- **Fixed** — `modes/evolve/evaluator.py` read non-existent `outcome.outcome_class`/`.metadata`; now reads `result`/`learning_signals` with a getattr fallback.

### Queue envelope
- **Added** — `Tracking.traceparent` (W3C) + `build_invocation(traceparent=…)` for cross-service trace continuity; a boundary contract test pins the envelope to flowable-core's Macer schema (nested `header.tracking`, snake_case, flat root `status`/`error`).

### Fabric
- **Added** — `fabric.blob.offload(..., dedup=True)`: content-addressed (sha256) offload so identical payloads collapse to one blob and a retried offload is idempotent.

### Channels
- **Added** — `jazzx_sdk.channels`: outbound message channels (the send-out counterpart to `connectors`). `Channel` protocol + `ChannelMessage`/`ChannelResult`, a `build_channel`/`register_channel` registry, a generic `WebhookChannel` (HTTP POST + optional HMAC signature + retry; also covers Slack/Teams incoming-webhook URLs), and a keyless `CollectorChannel` for tests.

### Inbound events
- **Added** — `jazzx_sdk.events.event_router(...)`: a mountable inbound-event `APIRouter` (via `serve(extra_routes=…)`) that maps an HTTP event → `QueueMessage` → `Handler`. `mode="enqueue"` (default; 202 + caller-supplied `enqueue`) or `"sync"` (invoke inline, resolving handler/client_layer from `app.state`); optional `auth` dependency and `to_payload` transform.
- **Added** — `channels.notify_on_complete(handler, channel, …)`: a `Handler` decorator that sends the result to a channel after each `handle()` (best-effort; never breaks the response), across queue/server/event paths. Optional `when` predicate + `to_message`.

### Library adoption / layering
- **Added** — `jazzx_sdk.contracts`: server-free import surface (canonical DTOs, scorer/optimization contracts, `Feedback`); SDK Adoption Policy (tiers + P1–P7) in ARCHITECTURE.md.
- **Changed** — SDK/contract and queue layers no longer load the server stack at import (Tier-3 symbols lazy via PEP 562); locked by import-boundary tests.

### Persistence behind fabric
- **Added** — `fabric.db` (`session`/`get_session`/`engine`/`register_metadata`/`repository`, `db_backend="common"|"sqlite"`) and `fabric.blob` (`put`/`get`/`delete` + `offload`/`materialize`, `blob_backend="local"|"azure"`). Sqlmodel-free.
- **Added** — durable stores on `fabric.db`: `DbFeedbackStore` (FeedbackStore now async) and `DbCostRecordStore` (write-through cost history).

### Conversation / interactive agent
- **Added** — `MaskingConversationStore` + pluggable `MaskPolicy` (default `OutputMaskPolicy`); composes with `CompactingConversationStore`.
- **Added** — bidirectional `Session ⟷ ConversationStore` seam: public `ConversationStoreSession` + `InteractiveAgent(session_factory=…)`.
- **Added** — `InvocationConfig`: per-invocation runtime config on the wire (`payload.data.config`); `apply_to(spec)`.
- **Added** — `scope_guardrail`, agent inventory/introspection (`describe()` across spec/agent/`ProfileRegistry`), and richer `InteractiveResponse.sources` citations (`label`/`uri`/`collection_id`/`quote`).
- **Fixed** — `ToolStreamHooks.on_tool_end` classifies tool success best-effort instead of hard-coding `success=True`.

### LLM / model data
- **Changed** — model pricing + card facts live in `model_data.json` (loaded via `_model_data.py`); `scripts/update_model_pricing.py` reconciles against vendor pages. Reconciled pricing (2026-07); added the current Claude tier.
- **Added** — model-card registry (`get_model_card`/`list_model_cards`/`context_window_for`), deprecation tracking (`is_deprecated`/`DEPRECATED_MODELS`), pricing provenance (`pricing_source`).
- **Added** — text sanitization (`jazzx_sdk.sanitize`): `sanitize_text`/`strip_nulls` strip NUL + lone surrogates (opt-in control chars), applied at `LLMManager.run` and `fabric.entities` writes.
- **Added** — `structured_call(llm, prompt, schema)`; `cost_tracker_token_source` + token-compaction API exports.

### Fabric / docs / streaming
- **Changed** — fabric surfaces enforce their return contract (`fabric._contract`, raises `TypeError` on a leaked shape); + a KH-client return-shape contract test.
- **Changed** — `fabric.docs.materialize`: `doc_id_field` fallback paths, whole-entity naming callbacks, transient-download retries; content-hash dedup now paginates.
- **Added** — `local_fabric(seed_dir=…)` + Mock local store serves documents (offline fabric round-trip).
- **Added** — streaming: `stream_invocation_sse(tail=…, named_events=True)`, `StreamPublisher.from_url`, `@jazzx/japes-client` (JS thin client).
- **Changed** — `tools.discover_agents`/`discover_tools` pass through `invocation_count` + `rank_by_usage`.

### Runtime / server / security
- **Added** — settings API (`settings_api.create_settings_router`, pluggable `SettingsStore`) + `serve(extra_routes=…)`.
- **Changed** — RBAC identity forwarding is automatic (runtime sets security context before `handle()`); added `clear_security_context()` lifecycle reset.
- **Fixed** — `ClientLayer.knowledge_hub` raises (no silent Mock fallback) under a production posture.
- **Security** — OData literal escaping (`escape_odata_literal`), settings-API auth + prod-posture PATCH refusal, `mount_spa` path confinement via `StaticFiles`, and 3 resolved CodeQL alerts (PR #47).
- **Added** — `retry_async`/`backoff_delay`; `PackManifestLoader.describe()` + a Naming Conventions section in ARCHITECTURE.

## [1.9.8] - 2026-07-04

The interactive-agent & client-substrate release — grows japes into the substrate assistant-style clients build thinly on.

- **Added** — end-to-end streaming: `InteractiveAgent.respond_stream(...)` (single-shot + agentic), `LLMManager.run_stream` + provider streaming, `ScriptedLLM.run_stream`; tool streaming (`ToolStreamHooks`, `spec.stream_tool_events`) and ergonomics (`set_stream_context`/`publish_event`/`clear_stream_context`, `StreamPublisher(enabled=, maxlen=)`). XADD field key standardized to `"data"` (`streaming.EVENT_FIELD`).
- **Added** — structured output from `InteractiveAgent` (`respond(output_schema=…)` → `InteractiveResponse.output`); `spec.max_turns`; single-shot now threads the full model/settings like the agentic path.
- **Added** — `agents.run` first-class `temperature`/`reasoning_effort`/`service_tier`/`verbosity` (forwarded only when set; per-provider mapping on the LLM path, `model_settings` on the agentic path).
- **Added** — async guardrails; `llm_guardrail(llm, policy, …)` (LLM classifier/moderation as a reusable guardrail).
- **Added** — the `server` shape can front a built SPA (`ServerSettings.static_dir`/`spa_fallback`, `jazzx_sdk.mount_spa`).
- **Added** — `build_invocation(...)` (construct an invocation `QueueMessage` without re-declaring the envelope); `gather_degrading`/`degrade` (resilient concurrent fan-out).
- **Changed** — `MessageHeader`: accepts `x_security_context` input alias; `correlation_key`/`message_id` optional (default fresh UUID, never None).

## [1.9.7] - 2026-07-02

Evaluation + INTERACT primitives, config-over-code, and compounding-loop building blocks. Several concepts adapted from eval-service (reimplemented, not copied).

- **Added** — `jazzx_sdk.evaluation.scorers`: structured `Scorer`/`ScorerResult` (score/passed/comment/metadata) with weighted+required `CompositeScorer`, `AdjudicatorScorer`, `ScorerRegistry`, and `FunctionScorer.from_metric` adapters; `EvaluationHarness(scorers=...)` records `CaseResult.scorer_results`. Generalizes the flat `metric_functions`.
- **Added** — `LLMJudgeScorer`: an LLM-backed `Scorer` (the ready judge behind `AdjudicatorScorer`); works with a real `LLMManager` or a `ScriptedLLM` (keyless).
- **Added** — schema-validated golden cases: `GoldenCaseValidator.validate_schema(cases, input_schema=, expected_schema=)` (JSON-Schema check, meta-validated, non-fatal) + `GoldenCaseLoader.load_schema` (`_schema.json` sidecar). `load_cases`/`hash_cases` now skip `_`-prefixed sidecars.
- **Added** — case-set versioning: `diff_case_sets` / `CaseSetDiff` (added/removed/changed-with-fields + `summary()`) and `CaseSetVersion` / `describe_case_set` (content hash + count + lineage + change summary) — a pure diff over golden-case sets (no DB).
- **Added** — `jazzx_sdk.evaluation.feedback`: typed `Feedback` learning signal with `from_case_result` auto-emit and `to_signal()` → EVOLVE `ImprovementSignal`; pluggable `FeedbackStore` (`InProcessFeedbackStore` default).
- **Added** — `GoldenCase.from_outcome` / `from_override`: promote a production outcome or a human override into a gold case (the "outcomes/overrides flow into better gold sets" building block).
- **Added** — `jazzx_sdk.llm.ScriptedLLM`: a keyless, deterministic `LLMManager` double (canned replies in order or via callable; structured-output aware; records `.calls`) — run/demo/test InteractiveAgents without API keys.
- **Added** — `jazzx_sdk.agents.build_interactive_agent(spec, fabric=, llm_manager=, ...)`: one-call factory for a grounded ("jazz") `InteractiveAgent` (wires `AgentExecutionService`; extra kwargs pass through).
- **Added** — `Pack.agent` / PackLoader `agent:` support: a pack's `agent:` manifest section resolves natively to an `InteractiveAgentSpec` (the INTERACT counterpart to `conductor:`); build a live agent with `build_interactive_agent(pack.agent, ...)`.

## [1.9.6] - 2026-06-28

- **Added** — SSE streaming: `stream_invocation_sse` + gated `GET /stream/{streaming_id}` (`create_app(stream_client=...)`), client-supplied `streaming_id`. See README / ARCHITECTURE.
- **Added** — `fabric.entities.list_all` (auto-paginating) and `fabric.docs.materialize` (download KH entity documents to a named local dir; unzips archives) + `MaterializedDoc`.
- **Fixed** — `EvaluatorMode` constructed `EvaluationReport` without the required `pack_id` (runtime `ValidationError`); `L3ReviewStorage` read case results under the wrong key (`cases` vs `case_results`).
- **Added** — assistant surface primitives (`jazzx_sdk.manifest`): `AssistantManifest` + `ArchetypeType`/`AutonomyLevel`/`SurfaceType`; `load_manifest` (sync, skill fail-fast) + `resolve_pack` (async, opt-in).
- **Added** — `ExperimentRun` (`jazzx_sdk.evaluation.experiment`): comparison/index record over eval runs, auto-created by `EvaluationHarness`; adds `GoldenCaseLoader.hash_cases`, `EvaluationConfig.dimensions`, lazy `mlflow_bridge`.
- **Added** — `EvaluationHarness` gate `gate_claims` (signature-based dispatch; role-aware-gating forward-compat).
- **Added** — `fabric.entities` (`EntityStore`): first-class generic typed-entity CRUD, replacing the raw `fabric.kh` escape hatch.
- **Added** — `InteractiveAgent` `hooks` + `model_settings`; `InteractiveAgentSpec.reasoning_effort`/`service_tier`; `Skill.mcp_servers`.
- **Added** — `fabric.pack` property; `Outcome.from_context(...)` factory.
- **Added** — `jazzx_sdk.streaming.StreamPublisher` over `common`'s `RedisStreamClient` (optional `streaming` extra); typed events re-exported from `common.core.streaming`.
- **Added** — security-context propagation (`set/get_security_context`); `ClientLayer` forwards the full inbound identity set (incl. `x-user-id`) for RBAC-enabled KH.
- **Added** — `KnowledgeHubClient.get_document_content`/`get_run_findings` wrappers; per-group imports with diagnostics; mock/real parameter contract test (dev).
- **Changed** — KH/fabric return-shape cleanup: `create_entity`/`update_entity` return `dict` (not raw `Response`); deletes return `bool`; single-resource reads return `Optional[dict]` (None on miss); `get_policy_bundle` returns `Optional[bytes]`.
- **Changed** — renamed `fabric.policy` to `fabric.opa` (`OpaBundleStore`) to disambiguate from the canonical `Policy`; placeholder pending the OPA-via-canonical-Policy rework.
- **Changed** — `datetime.utcnow()` to tz-aware `datetime.now(timezone.utc)` across `jazzx_sdk`; `Policy.is_active` tolerates a naive `expiry_date`.
- **Changed** — `KnowledgeFabric` refuses the in-process Mock under a production posture (`JAPES_ENV`/`ENVIRONMENT`/`APP_ENV`).
- **Fixed** — `ExpertRegistry.get_expert(evidence|governance|investigative)` now raises a clear `ValueError` (those moved to `jazzx_sdk.skills.*` in 1.5.0), not `ImportError`.

## [1.9.5] - 2026-06-25

- **Added** — `fabric.conversation`: fabric-managed conversation memory; `FabricConfig.conversation_backend` = `in_process`/`local`/`sql` (lossless file or `common.core.db`).
- **Added** — token-authoritative agentic compaction: `CompactionPolicy(strategy="responses")` (compacts on input-tokens over threshold, Responses-API item fidelity, overflow-retry + mid-flow guard) + compaction telemetry.
- **Fixed** — session conforms to the openai-agents 0.17.x `Session` protocol; `AnthropicProvider` lazy-inits (no raise when the key is unset).

## [1.9.4] - 2026-06-24

- **Added** — conversation memory for `InteractiveAgent`, declared on the spec: `conversation` (enable turn-threading) + `compaction` (`CompactionPolicy`). `ConversationStore` (default `InProcessConversationStore`) is lossless — `load` serves the working view, `load_raw` the full archive, `supersede` replaces the working view in place. Compaction strategies are pluggable via a registry (`CompactionStrategy` + `register_compaction_strategy`/`build_compaction_strategy`); built-ins `summarize` (LLM; count/char/both trigger) and `drop` (sliding window). `AgentExecutionService.conversation_store(spec, store)` wires the store and policy.
- **Added** — `ConversationBinding` + `OpenAIAgentsBinding` (+ `AgentExecutionService.bind_conversation`): adapts a `ConversationStore` to the OpenAI Agents SDK `Session` protocol (`get_items`/`add_items`/`pop_item`/`clear_session`), so the agentic path runs with substrate-managed history and persistence while the archive stays in the store. Provider-specific item serialization is isolated behind hooks on the binding.
- **Changed** — renamed the conversation/compaction surface to concept names: `spec.memory` → `spec.conversation`; `spec.compression`/`CompressionConfig` → `spec.compaction`/`CompactionPolicy`; `MemoryStore` → `ConversationStore`; `InMemoryStore` → `InProcessConversationStore`; `CompactingMemoryStore` → `CompactingConversationStore`; `SummarizeCompaction`/`DropCompaction` → `SummarizeStrategy`/`DropStrategy`; `InteractiveAgent(memory=…)` → `(store=…)`. `memory` is reserved for a future durable-recall binding.
- **Added** — `finance.structure_statement`: the LLM convert step of spreading (located/flattened grid → typed `Statement` + periods/units), with the domain structuring prompt (`STATEMENT_STRUCTURE_SYSTEM`/`STATEMENT_STRUCTURE_PROMPT`) and a `statement_prompt_preview()` for UI display. Completes the spreading pipeline in the SDK — packs supply only the per-segment anchors; the schema, structuring, export, and metrics are all SDK-owned.
- **Added** — `Portfolio[T]`: a generic collection-of-transactions aggregate (`state_counts`/`in_state`/`group_by`/`total`/`where`/`filter`/`batch`; attr/dict-key/callable accessors) for book-level views over many transactions (e.g. a loan book).

## [1.9.2] - 2026-06-20

- **Changed** — bump `common` submodule to `a436b9e` (OTel queue tracing); the queue consumer now handles its decoded-dict content.
- **Fixed** — `queue_processor.dequeue_message` accepts message content as a dict or a JSON string (provider/common-version dependent); previously `json.loads` on a dict failed and the message was dropped as malformed.

- **Added** — `InteractiveAgent` input/output guardrails (`blocked=True` on trip); `examples/loan_assistant`.
- **Added** — `fabric.local_fabric` + `CanonicalObjectStore.put`: seed canonical objects into an in-memory fabric.
- **Added** — `tools.build_assessment` → the canonical chain Policy→Evidence→Decision→Trace→Outcome.
- **Added** — `tools.extract(doc, schema, template=…)`: typed document extraction — templated or schema-only for unknown readable formats; readable-first triage (`is_readable`/`require_readable` → `DocumentNotReadableError`, DocIntel an explicit fallback).
- **Added** — `tools.classify_document(doc, taxonomy)`: classify a document into a caller-supplied taxonomy (LLM over readable text; label validated, `"unknown"` fallback). `DocumentClassifierRegistry` gains `classify_llm`/`taxonomy` (generic-LLM routing via `classify_document`/`extract`); `BaseDocumentClassifier` gains optional `description`/`schema` — one classification surface, generic engines + typed registry layered.
- **Added** — `tools.split_document(pdf, taxonomy)`: split a combined PDF into labelled segments (bookmarks, else page-classification with run-smoothing; no DocIntel) + `write_segments`.
- **Added** — `tools.TEMPLATES` extraction-template registry: tier-1 SDK defaults (`10-k`, `financial-statements`) ⊕ pack-registered; `extract`/`extract_financials` accept a template by name.
- **Added** — `tools.filings`: SEC 10-K → typed `Financials` (`fetch_10k`/`extract_financials`/`process_10k`).
- **Added** — document **tier routing** (additive; `convert_document`/`classify_document` unchanged): `classify_document` runs a zero-cost filename heuristic before the LLM; `TEMPLATES` tags each template with a tier (1 SDK-native / 2 pack-config / 3 borrower); `tools.fallback_sources` (`OnlineFallbackSource`/`FallbackSourceRegistry` + SDK `EdgarFallbackSource`); `tools.convert_with_fallback` → `ConversionResult` routes direct → online-fallback (canonical digital version, bypassing DocIntel) → DocIntel.
- **Added** — `conductor.ConductorEngine`: drives a `ConductorPipeline` descriptor as execution (Stage 2) — walks steps in order, repeats loop groups to convergence (per-loop predicate + `max_iterations`), threads emitted objects via `ConductorState`, records a `ConductorRun`. A pack supplies step id → component; the engine owns the sequencing + loop a pack conductor's `run()` hand-writes today. Unwired steps are skipped (incremental adoption).

## [1.9.1] - 2026-06-19

- **Changed** — `InteractiveAgent` skill defs run as isolated sub-agents via `Agent.as_tool`; bare skill names stay direct tools. `Skill` gains `description`.
- **Added** — `InteractiveAgent` skill catalog: `SkillRegistry` (shared, filterable; `load_dir`/`catalog_text`) — `spec.skills` resolves against it; spec gains `mcp_servers`; `Skill` gains `references`.
- **Added** — `ProfileRegistry`: host many named `InteractiveAgentSpec` profiles resolved by name (`load_dir` over `profile.yaml` folders / `*.yaml`); `validate(skills=, guardrails=, mcp_servers=)` cross-checks every profile's references against the catalogs at boot, raising once with all dangling refs (+ guardrail phase mismatches).
- **Added** — `GuardrailRegistry`/`Guardrail`: one phase-aware guardrail catalog; `InteractiveAgent` accepts it or a `{name: callable}` dict.
- **Added** — session memory: `spec.memory="session"` + a pluggable `MemoryStore` (`InMemoryStore` default); `respond(session_id=…)` loads prior turns and persists the new one (blocked turns excluded).
- **Added** — `CompactingMemoryStore` + `llm_summarizer`: a `MemoryStore` wrapper that summarizes the oldest turns past a budget and keeps recent ones — compaction is transparent to the agent.
- **Added** — skill `references` ground their sub-agent (loaded into its prompt via `reference_loader`, default `to_markdown`); the parent prompt auto-lists available skills; `CompactingMemoryStore` gains a `max_chars` size/token-budget trigger.
- **Changed** — Skill/Profile/Guardrail/Template registries share a `NamedRegistry` base (consistent `get`/`names`/`__contains__`); `ProfileRegistry` gains `register_dict`, `DocumentClassifierRegistry` a `names()` alias.
- **Added** — `convert_document` handles Excel (`.xlsx`/`.xlsm`) → markdown (needs `openpyxl`).

## [1.9.0] - 2026-06-19

Profile-driven **interactive agents** — stand up a knowledge-grounded query agent from a declarative profile. (Road to 2.0.)

- **Added** — `InteractiveAgent` (`jazzx_sdk.agents.interactive`): a data-defined (`InteractiveAgentSpec`), fabric-grounded, scoped query agent; `.respond()` does single-shot grounded Q&A or an agentic skills loop. Lazy-loaded.
- **Added** — `fabric.canonical.find(Model, where=…) -> Page[T]`: typed query over canonical objects (`Outcome`/`Evidence`/`Trace`/`Decision`/`Policy`), plus `required_indexes()`/`index_schema()`. Additive.

## [1.8.9] - 2026-06-18

OpenAI-Agents-SDK enablement kit — ready-wired model setup, retry, Claude wiring, and observability for clients driving `Agent`/`Runner` directly.

- **Added** — `jazzx_sdk.agents.models`: `resolve_model()`/`build_model_settings()`/`RetryingModel` (transient, orphaned-reasoning, and truncated-output handling).
- **Added** — `AgentExecutionService.openai.build_agent(...)` → a ready-wired `Agent` (caller drives `Runner`).
- **Added** — `jazzx_sdk.agents.AnthropicModel`: Claude as a `Model` in the OpenAI Agents SDK, via LiteLLM (`litellm` extra).
- **Added** — `jazzx_sdk.tracing.MlflowTraceHooks`: nested MLflow spans + token/cost accounting (`mlflow` extra).
- **Changed** — `import jazzx_sdk` no longer eagerly pulls the agents/modes stack; loads lazily.
- **Changed** — dependency floors: `openai-agents>=0.17.0`, `anthropic>=0.69.0`.
- **Fixed** — bounded `python` to `>=3.11,<4.0` so `poetry lock` resolves.

## [1.8.8] - 2026-06-17

- **Added** — `EvidenceTypeRegistry` + `EvidenceTypeDef` + `load_evidence_types(path)` (`jazzx_sdk.fabric.canonical`): a pack's evidence vocabulary authored as YAML (id + description + data-shape `fields` + `requestable`) instead of a per-pack `EvidenceType` enum. Adding a source becomes a YAML edit. Case-insensitive lookup; mirrors the PolicyRegistry / `load_policies` pattern. `Evidence`/`CanonicalEvidenceObject.evidence_type` stay plain strings — this is the authoritative vocabulary they're drawn from.
- **Changed** — `BaseToolRegistry` takes an optional `evidence_types=` registry. `get_available_tools()` is now concrete (no longer abstract): returns the registry's `requestable_ids()` if set, else the registered tools' evidence types — packs stop hand-maintaining the list. New `validate_evidence_types()` flags drift (a tool for an undeclared type; a requestable type with no tool), `raise_on_error=` optional.
- **Changed** — `InvestigatorMode` accepts `evidence_types=` and injects the requestable types (id + description) into its prompt, so the pack's `evidence_types.yaml` is the single source of the requestable vocabulary rather than a hand-maintained list in the mode tuning. Omitted → prior behavior (vocabulary stays in the tuning prose).
- **Changed** — `DefaultPolicyExpert` now works with zero subclassing for the common case. Configure it from pack data — `registry` (a `PolicyRegistry`/`list[Policy]`), `core_policy_ids`, `overlay_map` — and it runs built-in overlay-aware `resolve()` (core + program overlays, precedence, conflict/staleness detection) and condition-gate `check_compliance()` (field-precedence across policies; two-tier gates within a policy), stamping `GUIDANCE_REFS` on every response. No registry configured → both stay no-ops (legacy KH-tool-backed behavior preserved). `DefaultPolicyExpert.from_policy_dir(dir)` hydrates every `*.yaml` in a pack's policy dir.
- **Added** — `ExpertRegistry.register_instance(type, expert)`: register a pre-configured Expert instance (e.g. a data-hydrated `DefaultPolicyExpert`) so `get_expert()` serves it — lets a pack stay subclass-free yet still route through the registry.

## [1.8.7] - 2026-06-16

- **Fixed** — `KnowledgeHubClient.read_entities()` returned `[]` on a successful 200 because the generated `_parse_response` for `GET /reasoning/entities` has no 2xx branch (`parsed` is None). Now recovers the entity list from the raw 2xx body (bare array or `{entities:[…]}`) before treating it as empty — also unblocks `read_triples`/`fabric.graph`, which ride on it. Bumps `pyjwt` floor to `>=2.13.0`. (Cherry-picked from #40 on main.)
- **Added** — `jazzx_sdk.fabric.canonical.load_policies(path)`: load canonical `Policy` objects from a YAML file (a top-level list or a `policies:` mapping; `model_validate` per policy handles nested rules, source refs, escalation/authority, enums), so packs author policy sets as data instead of in-code `Policy(...)` literals.
- **Added** — `ConductorPipeline.from_yaml(path, name=...)`: load a conductor pipeline from a declarative YAML (or select one of several nested under a top-level `pipelines:` map), so packs can own pipelines as data instead of in-code `ConductorPipeline(...)` literals.
- **Added** — `jazzx_sdk.evaluation.metrics`: generic metric primitives (`exact_match` / `within_tolerance` / `set_coverage`) that pack `metric_functions` compose. Replaces the broken docstring reference to a non-existent `metrics.DecisionAccuracy`.
- **Changed** — `jazzx_sdk.evaluation` is now a single front door: docstring maps the L1/L2/L3 layers + run aggregate (`EvaluationResults`) vs per-case canonical artifact (`EvaluationReport`), and re-exports `EvaluatorMode` (modes.evolve) and `EvaluationReport` (fabric.canonical) so the whole framework is reachable from one import. Guardrail test asserts the front door stays complete.
- **Added** — L2/EVOLVE hook in the harness: optional `evaluate_fn(case_file, golden_case) -> dict` run post-case (the pack owns the Outcome + EvaluatorMode + Curator), stored on `CaseResult.evaluation`. Makes the previously-dead `evaluator_factory` placeholder real.
- **Added** — token/cost capture in the harness: optional `token_metrics_fn(case_file)` (mirrors `case_detail_fn`) populates `CaseResult.token_metrics`, summed onto `EvaluationResults.token_metrics`; `MlflowReporter` logs them. Lets packs route per-case usage (tokens, cost, llm_calls) through the standard results instead of a bespoke aggregator.
- **Added** — `jazzx_sdk.evaluation.reporters.mlflow.MlflowReporter`: an optional `EvaluationReporter` that publishes a run to MLflow (config/labels → params/tags, pass-rate/averages/summary → metrics, results JSON → artifact, run id → `external_ref`). Behind the `mlflow` extra (`pip install 'jazzx_sdk[mlflow]'`); core stays MLflow-free.
- **Added** — `jazzx_sdk.evaluation.EvaluationReporter`: pluggable persistence/publish backend for the evaluation harness (`report(results)` once; optional `report_case(...)` streaming). `EvaluationHarness` now accepts a `reporter=` and calls it; `report()`'s return is stored on the new `EvaluationResults.external_ref`. Built-in JSON `save()` stays the default local sink; MLflow / eval-service become reporters outside the SDK.

## [1.8.6] - 2026-06-15

- **Added** — env-driven LLM resolution in `jazzx_sdk.llm` (`resolve_provider` / `resolve_model` / `resolve_key` / `ensure_provider_key` / `llm_from_env`): build an `LLMManager` from `{PREFIX}_LLM_PROVIDER` / `{PREFIX}_LLM_MODEL` + standard provider key envs (with nearest-`.env` fallback). Prefix-namespaced so multiple apps coexist.
- **Added** — `jazzx_sdk.fabric.FabricConfig.from_env()` + `fabric_from_env()`: build a fabric from `FABRIC_MODE` / `JAPES_KNOWLEDGE_HUB_URL`|`KNOWLEDGE_HUB_URL` / `KH_API_KEY` / `LOCAL_DATA_DIR` / `GOLDEN_CASES_DIR`. Also fixed `validate_for_mode` to not `AttributeError` on the error path when `retrieval_mode` is a coerced str.
- **Added** — `jazzx_sdk.modes.compose_mode_prompt` / `make_prompt_resolver`: assemble a mode's system prompt as **platform base ⊕ pack `mode_tuning`** (distinct from the single-file `resolve_mode_prompt`), so packs get the same base+skill composition instead of hand-rolling it.
- **Added** — `tools.extraction`: template-based document region location + extraction. `RegionAnchor` / `ExtractionTemplate` declare how to find a region in a converted (markdown/iXBRL) doc — title cues + signature line items, `window` or `table`-stitch mode, and a `start_after` skip marker (e.g. skip MD&A to the auditor's report). `locate_region` / `flatten_region` / `structure_region` locate it, flatten the HTML to `label | v | v` rows, and LLM-structure those rows into JSON. Generalizes the financial-statement spreader so domain packs feed a declarative template instead of hand-rolling the search.
- **Added** — `PipelineStep.phase` (optional): a label for grouping a conductor's steps into a few phases (e.g. Intake / Investigate / Synthesize / Govern / Record) so a long flat step list can render as a handful of labelled clusters. Backward-compatible (None → ungrouped).
- **Added** — `platform_catalog.MODE_KINDS` / `MODE_KIND_LABELS`: classify each cognitive mode by how it's implemented today — `agent` (LLM), `rule` (deterministic guards, e.g. sentinel), `python` (orchestration/logic, e.g. conductor/curator), `hybrid` (e.g. evaluator), `planned` (stub). Lets UIs answer "which modes are real LLM agents vs deterministic code vs not-yet-built" without guessing.
- **Docs** — `DOMAIN_PACK_QUICKSTART.md`: added a design-first "Domain Pack Crafting Methodology" (policies→PolicyExpert, playbooks→PlaybookExpert, ontology, conductor for dominant+secondary workflows, specialize canonical objects/modes/experts, gold cases + metrics + compounding loop, then flow gold cases through before real transactions), grounded in the JACI reference packs and current SDK substrate (`platform_catalog`, `Pack`, `conductor`, experts, evaluation). Refreshed the stale version banner.

## [1.8.5] - 2026-06-14

- **Added** — UI KH path (`jazzx_sdk.ui`) now sends both caller-identity headers when set: `x-user-id` (`JAPES_KH_USER_ID`/`KH_USER_ID`, for Keto) and `x-security-context` (`JAPES_SECURITY_CONTEXT`/`SECURITY_CONTEXT`, the process-engine token — env-sourced since the UI has no per-message context). Distinct keys, each independent, so no conflict.
- **Fixed** — OpenAI agent provider (tool-loop path) read the agent result from a nonexistent `result.data`, falling back to `str(RunResult)` (`"RunResult:\n- Last agent..."`) → structured-output parsing always failed. Now reads `result.final_output` and parses via the shared `validate` helper (accepts instance / dict / JSON text). This had broken every mode that runs through the agent tool path (investigator, etc.) on OpenAI.

## [1.8.4] - 2026-06-14

- **Added** — Gemini provider (`jazzx_sdk.llm.providers.gemini.GeminiProvider`): text + native structured output (`response_schema`), wired into `LLMManager` (`gemini_api_key`, `_get_provider`, model→provider inference for `gemini-*`). Reads `GEMINI_API_KEY`/`GOOGLE_API_KEY`. Optional dep via the `[gemini]` extra (`google-genai`).
- **Added** — `jazzx_sdk.conductor.Checkpointer`: reusable versioned `CaseContext` checkpoint emission for conductors. Owns the generic plumbing (monotonic seq, versioned id `ctx_{case_id}_{seq:02d}`, best-effort persist that never aborts the loop, trace stamping); a scenario supplies only the domain mapping + one `await cp.emit(case_ctx)` per iteration boundary. Lifts the pattern prototyped in jaci's ci_spread into the SDK.
- **Added** — `CaseContextStore.latest(case_id)` and `Pack.resume(case_id)`: recover the newest checkpoint for a case to restart a loop (checkpoints were audit-only before).
- **Fixed** — OpenAI provider sent a `flex_`-prefixed model alias (e.g. `flex_gpt-5.4`) to the API verbatim → `model_not_found` 404, and never sent `service_tier`. It now resolves the alias via `parse_model_tier` to the base model + `service_tier="flex"` (japes owns the translation; callers pass the alias directly).
- **Fixed** — `get_client_layer()` now sends KH caller identity (`x-user-id` from `JAPES_KH_USER_ID` / `KH_USER_ID`, via `request_headers_provider`) — KH authorizes via Ory Keto keyed on `x-user-id`, so without it every call was 401 (`auth=none`). Also passes an optional bearer token (`JAPES_KNOWLEDGE_HUB_TOKEN` / `KNOWLEDGE_HUB_TOKEN`). Unset = unchanged. (The `x-user-id` user must have Keto project access to the target collections.)
- **Fixed** — `LLMManager` now infers the provider from the model name when no `provider=` is given (a `claude-*` model routes to Anthropic, a `gpt`/o-series to OpenAI) instead of always falling back to `default_provider` (= openai). This was the anthropic dev-daily failure: a direct `LLMManager().run(model="claude-…")` sent claude to OpenAI. Explicit `provider=` and task routing still take precedence.
- **Tests** — added provider boundary-contract tests (assert the model/`service_tier`/token params we actually send — catches this class without live calls), provider-routing tests (model→provider inference), and an opt-in live smoke test per provider (`RUN_LIVE_LLM=1` + key; cheap nano/haiku model, tiny prompt).

## [1.8.3] - 2026-06-13

- **Added** — `jazzx_sdk.platform_catalog`: the reusable-substrate inventory (13 cognitive modes grouped by faculty, experts derived from `EXPERT_REGISTRY`, 5 fabric surfaces, 13 canonical objects) for UIs/docs to render instead of hand-maintaining drift-prone lists.
- **Changed** — `ExecutionKind` now describes a step's *intended wiring* only: `live` / `deterministic` / `offline_asset` / `integration`. Dropped `stubbed` / `mock` — whether a step ran as a stub in a given environment is a property of that run's trace, not of the conductor design.

## [1.8.2] - 2026-06-12

- **Added** — `jazzx_sdk.evaluation.load_run_history` / `RunHistory`: aggregate a pack's eval runs over time, sliceable by run `labels` (model, prompt_version, dataset, …). Runs now carry `labels` (from `EvaluationConfig`).
- **Added** — `jazzx_sdk.conductor`: declarative `ConductorPipeline` descriptor (steps, canonical-object lineage, execution kind, sub-actions, loop groups) + `BaseConductor.describe()` contract. Static counterpart of `CanonicalTrace`; one source for the conductor diagram instead of a hand mirror. Execution stays pack-defined.
- **Added** — `jazzx_sdk.pack.Pack`: access object for a domain behind one handle. Authored half — policies → `PolicyRegistry`, conductor → `ConductorPipeline`, ontology, playbooks (via manifest `policies.registry` / `conductor.pipeline` pointers). Runtime half — `pack.bind(runtime)` then `record()` / `trace(id)` / `case(id)` / `case_context(id)` / `traces()` / `cases()` / `case_contexts()` / `live_policies()` / `runs(dir)` for the audit traversal. Distinct from the canonical `DomainPack` governance record (composed, not merged).
- **Added** — `TraceStore.list` / `CaseFileStore.list` / `CaseContextStore.list` (`pack_id=…`) — pack-scoped listing (mirrors `list_policies`).

## [1.8.1] - 2026-06-12

- **Added** — `jazzx_sdk.finance`: `FinancialSpread` schema + Excel/CSV export (reusable spreading; `[finance]` extra for openpyxl).
- **Added** — `jazzx_sdk.tools.financial`: credit-metric computations (complements `ratio_evaluator`).
- **Added** — `PackManifestLoader` metadata accessors.
- **Added** — KH URL also reads the platform's `KNOWLEDGE_HUB_URL` (prefers `JAPES_KNOWLEDGE_HUB_URL`).
- **Added** — Streamlit launcher reverse-proxy env: `JAPES_UI_BASE_URL_PATH` / `JAPES_UI_BEHIND_PROXY` / `JAPES_UI_EXTRA_ARGS`.
- **Added** — launch-time startup self-check (mode, KH URL + connectivity, provider keys, UI flags).
- **Fixed** — mode schemas migrated off deprecated `pydantic.generics.GenericModel` to pydantic-v2 native generics.
- **Changed** — dependency specs use `>=` floors instead of `^` caps.

## [1.8.0] - 2026-06-12

Structured-output contract: providers return a validated instance or raise `StructuredOutputError`. OpenAI 3-tier negotiation (fixes broken native output), Anthropic native tool-use; new `jazzx_sdk/llm/structured.py`.

## [1.7.2] - 2026-06-12

`EvaluationHarness(case_detail_fn=...)` + `CaseResult.case_detail`: optional per-case snapshot (hypotheses/evidence/decision) for eval UIs.

## [1.7.1] - 2026-06-12

Moved `jazzx_sdk.fabric.pack` → top-level `jazzx_sdk.pack` (back-compat shim kept); added `PackManifestLoader`.

## [1.7.0] - 2026-06-11

`fabric.docs` named collections + content-hash dedupe; `fabric.kh_status()` connectivity probe.

## [1.6.9] - 2026-06-11

`serve()` / `launch_streamlit()` — one `JAPES_RUN_MODE` entrypoint (queue/server/ui); `jazzx_sdk.ui.get_client_layer()` for Streamlit.

## [1.6.8] - 2026-06-11

Document tools: `convert_document()` faithful router (scanned detection, table extraction); `ratio_evaluator.evaluate_value()` / `evaluate_covenant_policy()`.

## [1.6.7] - 2026-06-09

KG consolidation: `fabric.graph` is the one KG surface (triple CRUD, agent tools); offline Mock backs graph/canonical/rag/policy; removed legacy `*KGStore`.

## [1.6.6] - 2026-06-09

Closed the last `fabric.*` gaps that forced callers to `fabric.kh`: `fabric.docs.retrieve` / `download`, and `fabric.graph.update_ontology` / `delete_ontology` / `upload_ontology`.

## [1.6.5] - 2026-06-08

- **Added** — `fabric.graph` is the complete KG/triple/ontology entry point: `delete_triple`, `list_ontologies`, `resolve_ontology`; collection/ontology defaulting on `KGStore` (env `KH_COLLECTION_ID` / `KH_ONTOLOGY_ID`, per-call override, clear error if unresolved).
- **Fixed** — `KGStore.add_triple` delegates to `create_triple` (was a stale stub); `register_ontology` / `get_ontology` repointed to the real ontology API (id, not name; no `version` arg).
- **Note** — The KG is entity-backed (`entity_type="triple"`); Fuseki/RDF in the KH repo is inert leftover.

## [1.6.4] - 2026-06-08

Platform gaps surfaced by the C&I pack build (additive, backward-compatible):
- OpenAI provider selects `max_completion_tokens` vs `max_tokens` per model (gpt-5.x/o-series/flex were broken).
- `Context` loop methods (`apply_hypothesis_update`, `add_evidence`, `apply_verifier_report`, `pending_*`) on the base class; `BaseToolRegistry.execute(evidence_type, query_params) -> Evidence`; `CanonicalTrace.for_pack(...)`.

## [1.6.3] - 2026-06-07

Canonical schema consolidation + DomainPack v1.5 manifest, freeze-prep for v1.5 contracts:
- DomainPack v1.5 manifest minimums (per-mode registry/matrix versions; fail-closed for CERTIFIED packs); `DomainPackHelper.from_yaml()`.
- `TransactionContext` / `TransactionStatus` (single-pass operational contract) + `InvestigationContext` alias for `Context`.
- Single source of truth for `Attestation`/`Freshness`/`Outcome` (re-exported from `fabric.canonical`); TraceStep observability fields documented.

## [1.6.2] - 2026-06-06

Evaluation Framework (Phase 3): `EvaluationHarness` / `EvaluationConfig` / `EvaluationResults` / `CaseResult` — systematic L1→L2 execution (sequential/parallel) with metrics and JSON save/load.

## [1.6.1] - 2026-06-06

Evaluation Framework (Phase 2): L3 review infrastructure — `L3Review`, `ReviewAgreement`, `IssueType`, `L3ReviewStorage`, `L3ReviewSummary`, CSV export.

## [1.6.0] - 2026-06-06

Evaluation Framework (Phase 1): golden cases — `GoldenCase[TInput, TExpected]`, `GoldenCaseLoader`, `GoldenCaseValidator` under `jazzx_sdk/evaluation/`. Pydantic v2 patterns.

## [1.5.1] - 2026-06-04

Fabric retrieval modes: `FabricConfig` + `RetrievalMode` (STRICT/CACHED/LOCAL/TEST) with `for_production`/`for_development`/`for_testing` factories; `DocStore` routes by mode; KH client optional for LOCAL/TEST. `DocStore.get(location=)` and `local_dir` deprecated. Backward compatible.

## [1.5.0] - 2026-06-03

**Breaking** — IIF v1.5 Expert/Skill restructure: Governance/Evidence/Investigation move to `jazzx_sdk/skills/`; EXPERT_REGISTRY 6→3; TraceStep frozen; `experts` re-exports skills.

## [1.4.5] - 2026-06-09

**Breaking** — Removed the `jazzx_runtime_sdk` backward-compat alias. `import jazzx_runtime_sdk` now fails; use `jazzx_sdk` (renamed in 1.4.0). Consumers must update imports.

## [1.4.4] - 2026-06-09

Made the `jazzx_runtime_sdk` alias survive wheel packaging (real shim package + meta-path finder mapping every submodule to the same `jazzx_sdk` objects); emits `DeprecationWarning`. (Superseded by 1.4.5.)

## [1.4.3] - 2026-06-03

Schema Spec v1.0 completion: eight derived canonical objects (`CaseContext`, `CanonicalCaseFile`, `ScenarioReport`, `Artifact`, `EngagementPlan`, `AgreementRecord`, `EvaluationReport`, `DomainPack`) + KH-backed stores; TraceStep / CanonicalTrace / OverrideEvent aligned to §5-7. Canonical fabric now 5 core + 8 derived.

## [1.4.2] - 2026-05-31

**Breaking** — Document module consolidation to 2 modules: removed `jazzx_sdk/documents/`; all ops in `tools/documents.py`. `fabric.docs` gains local filesystem storage via `location="local"|"hub"`.

## [1.4.1] - 2026-05-31

Added `fabric.docs` governed document store (5th fabric store; `DocType` vocabulary, `put/get/list/delete`, `MockDocStore`; k9 migrated). **Breaking**: removed duplicate `jazzx_sdk.document/` module.

## [1.4.0] - 2026-05-31

**Breaking** — Package renamed `jazzx_runtime_sdk` → `jazzx_sdk`. Introduced the Knowledge Fabric (`ctx.runtime.fabric`): `canonical`, `graph`, `rag`, `policy` stores + Domain Pack loader (`fabric.pack.DomainPackFabric`). `.knowledge_hub` unchanged.

## [1.3.0 and earlier] - 2025-12 -> 2026-05

Pre-1.4.0 history (package `jazzx_runtime_sdk`, before the `jazzx_sdk` rename) is condensed. That line built the foundation carried forward today: queue/server runtime + Handler + service clients + tracing (1.0.0); the 13-mode cognition framework and operational/EVOLVE modes (0.3.x); canonical objects + `CanonicalObjectStore` (0.2.x); the tool registry and KH tool layer (0.4.x); the expert layer (0.5.0); discovery/workflow tools (0.6.0); and 1.1-1.3 platform services (agents/LLM, documents, connectors, KG store, unified `service_tier`). Full detail in `git log`.
