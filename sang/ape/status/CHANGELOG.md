# Changelog

All notable changes to JAPES (JazzX SDK) will be documented in this file.

## [Unreleased]

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
