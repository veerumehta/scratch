# Plan: Kernel salvage — SDK hardening carried over from the v1 kernel

> **Status (2026-08-12): not started.** Scoped from the Notion page *⌨️ JazzX Kernel Developed
> Architecture* (Engineering Wiki, snapshot 2026-03-09) read against this working tree
> (HEAD `90475da`, 2.3.6+). Companion assessment: `Kernel_Salvage_Assessment_for_JAPES.md` — the
> full capability-by-capability comparison, including the ~20 Kernel features deliberately **not**
> carried over. Every code claim below was read in the tree and spot-verified by grep.

**Deliberately a separate plan file from `plan_uaf_phase1_additive.md`** — that plan is being worked
on concurrently, and these phases are independent of it. Phase IDs here are prefixed `K` so the two
plans can be referenced in the same conversation without collision. Only two items interact with the
UAF plan at all, and both are called out inline (K9, K10).

Target version: **2.4.0** (same minor as the UAF additive plan; everything here is additive or a
defect fix, with no default-behavior change).

## Why these, and why now

JAPES supersedes Kernel's architecture comprehensively — plan rows, the Celery/Redis broker,
polymorphic `Response`, per-agent LLM rows, `learning_strategy`, SPARQL-as-policy-engine are all
either already replaced by something with real consumers (`conductor/`, `runs/`, `fabric/canonical/`,
`authority/`, `evaluation/`, Azure Storage Queue + `common`'s `RetryPolicy`) or were v1 aspirations
that never acquired any. The assessment doc lists those and closes them out.

What remains is this plan. Two framings matter for sequencing:

**Six of these are latent defects, not features.** K1–K6 each describe something that is either
already broken in the tree or silently loses a record. They should run regardless of how any UAF
question resolves, and several are a day's work each. K1 in particular gates a migration: moving
agents off Kernel's LLM rows onto `spec.model` + the Gateway is currently a *downgrade* in resilience
for any assistant with skills, because two of three providers have no retry.

**One is real architecture.** K7 (parent → sub-agent context inheritance) is the only genuine
architectural hole the Kernel comparison surfaced, and it gets a design note before code.

---

## K1 — Provider-uniform retry and backoff at the Gateway

**Files:** `jazzx_sdk/llm/manager.py`, `jazzx_sdk/llm/routing.py`,
`jazzx_sdk/llm/providers/{openai,anthropic,gemini,local}.py`

Retry exists in exactly one place: `providers/openai.py:141 _call_with_retry` (429, exponential
backoff + jitter, 3 attempts). Grep for `retry` across `llm/providers/` matches **only
`openai.py`** — Anthropic and Gemini have none. Meanwhile `llm/routing.py:206 RetryConfig` and
`:218 RetryStrategy` are implemented, exported from `llm/__init__.py:56`, and **instantiated
nowhere** in the tree. Kernel's design is better here on a structural point: backoff belonged to the
gateway, uniformly, not to each provider adapter.

1. Wire `RetryStrategy` into `LLMManager`'s provider-execution path so every provider inherits it.
   Do **not** add a third per-provider copy — that is how this drifted in the first place.
2. Fold `providers/openai.py:_call_with_retry` into the shared path and delete it, so there is one
   retry policy rather than two with different parameters. This is an orphan created by our own
   change, so removing it is in scope per the surgical-changes rule.
3. Compose with, don't duplicate, `llm/health.py:HealthMonitor` — retry handles a transient 429,
   the circuit breaker handles a sick provider. Make the interaction explicit in the docstring
   (retry exhausted → report to `HealthMonitor` → failover chain), because two overlapping
   resilience mechanisms with no stated relationship is how one gets bypassed.

→ verify: a scripted 429-then-success against each of the three providers retries and succeeds
(three tests, one per provider — the Anthropic and Gemini cases fail today); retry exhaustion marks
the provider in `HealthMonitor` and triggers failover; grep asserts one retry implementation.

**Acceptance:** every provider retries a transient rate limit identically, and `RetryStrategy` is no
longer dead code.

---

## K2 — Approver identity on the approval record

**Files:** `jazzx_sdk/conductor/suspension_store.py`, `suspension_store_db.py`,
`jazzx_sdk/fabric/canonical/trace.py`

`DurableSuspension` is better machinery than Kernel's nullable `approved_at` — atomically claimable,
heartbeated, `reap_stale`-able, `mark_resumed`. But the resolution field is `resolution: Any`. There
is no approver identity, class, timestamp, or authority basis: repo-wide, `approver` appears only on
a reporting artifact (`fabric/canonical/derived.py:411`) and in `conductor/engine.py` docstrings.
Kernel recorded `approver_id`, `approver_type`, `approved_at` on the step itself. For a SAR filing or
a credit decision, "a human approved this step — who, when, under what authority" has to be *in* the
record, and today it is an untyped blob.

1. Add typed `approver_ref`, `approver_class`, `approved_at`, `authority_basis` to
   `DurableSuspension` (and the DB row). Keep `resolution` for the payload; these are about *who*,
   not *what*.
2. **Reuse the existing vocabulary rather than inventing a second one.**
   `trace.py:OverrideEvent` already has `overriding_actor` / `authority_basis` / `reason_code` for
   post-hoc overrides — the same concepts. Same field names, same enums.
3. Mirror the approver fields onto the `TraceStep` that suspended, so an audit read of the trace
   alone answers the question without joining to the suspension store. This touches the frozen
   schema — see K10; if the governed change is not yet approved, land step 1 and 2 and record the
   trace mirror as blocked rather than working around it.
4. While here, record but do not fix: `conductor/engine.py:302` raises if a suspend occurs inside a
   `Loop` ("HITL suspend is supported only for top-level steps"). That is a real constraint on any
   review-inside-a-loop workflow and deserves its own scoping — mention it, don't expand this phase.

→ verify: resolving a suspension without approver fields is rejected; a resolved suspension's
approver survives a store round-trip; an audit read of the trace surfaces the approver (once K10
lands); `OverrideEvent` and the new fields use identical enum values (asserted, not assumed).

**Acceptance:** no human approval enters the record anonymously.

---

## K3 — Tool timeout and a normalized result envelope

**File:** `jazzx_sdk/tools/base_registry.py`

`BaseToolRegistry` gives registration, discovery, a circuit breaker (`_max_failures=3`,
`reset_circuit_breaker`, `get_circuit_breaker_status`) and mock/real switching — but no timeout, no
result normalization, and no per-tool duration tracking. Kernel's Unified Tool Executor had all
three. Note what is *not* missing: schema-from-signature is already handled by the Agents SDK's
`function_tool` (re-exported at `agents/run_kit.py:34`, used at `agents/interactive/reads.py:99,118,148`),
so parameter validation is covered on the agent path and only the registry path needs anything.

This phase also closes a gap the UAF gap analysis flagged from the other direction: error envelopes
are inconsistent today — `tools/platform/workflow.py` swallows exceptions into `{"error": …}` dicts
while `clients/kernel_client.py` raises. One envelope fixes both.

1. Add a per-tool timeout to `BaseToolRegistry.execute`, defaulted so no existing registration
   changes behavior, and surface exhaustion as a structured timeout result rather than a hang.
2. A single result envelope — success/failure, value, error class, duration — applied on the way out
   of `execute`. Normalize the two existing shapes onto it.
3. Add `stop_on_fail` as a **per-tool** declared policy (Kernel had it on both `Tool` and `Agent`).
   The agent-level flag is superseded by `ConductorState.halt`; the per-tool one has no declarative
   expression in JAPES today. Default preserves current behavior.
4. Ask the sibling question before calling this done (CLAUDE.md §7): the same missing-timeout shape
   may exist in `clients/` wrappers and `connectors/`. Check the family; note what you find.

→ verify: a tool that hangs past its timeout returns a structured timeout, not a stall; a raising
tool and an `{"error": …}`-returning tool produce identical envelopes; `stop_on_fail` halts the flow
and its absence does not; existing tool tests pass unchanged.

**Acceptance:** every tool result has one shape, and no tool can hang a run indefinitely.

---

## K4 — Durable idempotency for the queue processor

**Files:** `jazzx_sdk/queue_processor.py`, `jazzx_sdk/automation/idempotency.py`

The queue path is otherwise equal-or-better than Kernel's Celery setup: Azure Storage Queue with a
2700s visibility timeout (`queue_processor.py:67`), `extend_visibility` (`:158`),
`get_queue_properties` → `approximate_message_count` for queue depth (`:284-315`), explicit
`delete_message` after success (`:432`) for at-least-once, and `RetryPolicy`/`ExponentialBackoff`/
dequeue-count routing/dead-lettering in `common/core/queue/base_queue_handler.py:47-198`.

The defect: `queue_processor.py:95 _processed_message_ids` is an **in-memory** set. It resets on
restart, so at-least-once delivery currently means at-least-once *duplicate processing* across
restarts — for a queue whose visibility timeout is 45 minutes, a redeploy mid-flight replays work.
`automation/idempotency.py` and `fabric/idempotency.py` already implement durable idempotency; this
is wiring, not building.

→ verify: a message processed, then the processor restarted, then the same message redelivered — is
not reprocessed (this fails today); the durable store is consulted before the in-memory fast path,
not instead of it.

**Acceptance:** duplicate delivery is idempotent across a process restart.

---

## K5 — Wire `blob.offload()` at the two write boundaries

**Files:** `jazzx_sdk/fabric/blob/store.py` (no change), `jazzx_sdk/fabric/conversation_store.py`,
wherever tool results are persisted (see K3's envelope)

`BlobStore.offload(value, threshold_bytes=, dedup=)` / `materialize()` is implemented and documented
with a usage example in its own module docstring — and grep finds **no caller anywhere in
`jazzx_sdk/`**. Kernel's thresholds (>100KB response, >100KB notepad artifact, >250KB tool output)
are exactly the wiring JAPES is missing.

Scope this to the **write** side only. On reads into a model, JAPES' cap-and-fail-loud discipline is
the better one (`agents/adjudication/workspace.py:enforce_read_cap`/`ReadTooLarge`,
`tools/agent/dir_tools.py:238`) and Kernel's silent read overflow should not be ported. But on
writes, a hard failure *loses the record*, which is the opposite of what an audit trail is for.

1. Conversation-message persistence: offload oversized message payloads, store the pointer.
2. Persisted tool results (K3's envelope is the natural place).
3. Thresholds configurable, defaulted generously enough that no current workload changes behavior.
4. `materialize()` on read, transparently — a caller should not need to know a value was offloaded.

→ verify: a message larger than the threshold round-trips through the store and materializes byte-
identically; a message below it is stored inline (no behavior change); the NUL-sanitization boundary
added in HEAD still applies to the pointer write.

**Acceptance:** an oversized write is stored, not lost, and the caller cannot tell.

---

## K6 — LLM invocation ledger: correlation and payload references

**Files:** `jazzx_sdk/llm/cost_store_db.py`, `jazzx_sdk/llm/cost_tracker.py`

Cost accounting is durable, queryable, and richer than Kernel's — `CostRecord` has a six-way token
split (input/output/cached/cache_creation/reasoning) versus Kernel's `in_tokens`/`out_tokens`, and
`CostRecordRow` is indexed on timestamp/user_id/project_id with a `list()` query surface.

What Kernel's `LLMInvocation` had and this does not: the **request and response payloads**, per-call
status/error/latency, and **any id joining a call to the step that made it** — `CostRecord` carries
only a free `metadata` dict. So "what exactly was sent to the model when this decision was made" is
currently unanswerable from the record. That is a question an examiner asks.

1. Add `trace_id` / `step_id` correlation columns to `CostRecordRow` and populate them from the
   ambient context.
2. Add per-call status, error class, and latency.
3. Store request/response as **references**, with payloads offloaded through `fabric.blob` — K5's
   first real customer. Do not inline model payloads into a relational row.
4. Retention and redaction are a real question here, not a footnote: model payloads may contain
   borrower PII. Reuse the existing masking discipline (`MaskingConversationStore`/`OutputMaskPolicy`)
   rather than inventing a second redaction path, and make retention configurable.

→ verify: a turn's LLM calls are retrievable by `trace_id`; payload refs materialize; a failed call
records status and error; masking applies to offloaded payloads (assert on the stored bytes, not the
API return).

**Acceptance:** every model call is reconstructible and joinable to the step that made it.

---

## K7 — Parent → sub-agent context inheritance (design note first)

**Files:** design note first; then new `fabric` store + `jazzx_sdk/agents/interactive/agent.py`

This is the one genuine architectural hole. Trace what crosses the boundary today:

- Non-`spec_ref` skill (`agent.py:543 _build_parent_tools`): the sub-agent is built with its own
  instructions, eagerly-inlined references, resolved tools and `reads` tools, and a model — then
  exposed via `as_tool`. From the parent it receives **only the argument string the parent LLM writes
  into the tool call.** Its intermediate state is discarded; the parent sees the returned string.
- `spec_ref` skill (`:717 _build_composed_skill_tool`): `composed_tool(query)` calls
  `nested.respond([{"role":"user","content":query}], scope=scope or {})` — so **`query` plus the
  scope dict** cross, and the return is `reply.answer`, a string.

Authorization, by contrast, cascades properly: `authority/context.py`'s `InvocationContext` /
`PermissionScope` inherits and narrows via `descend()`, and a refused skill is never even exposed to
the model. **State has no counterpart to that cascade.** Consequence: every sub-agent re-derives what
the parent already established — re-reads the same documents, re-extracts the same fields — and
everything it learns dies at the `as_tool` return. On a mortgage file that is waste. On an AML
investigation across a dozen evidence sources it is the difference between one pass and N.

**Write the design note before any code.** Points it must settle:

1. **Shape.** Kernel's answer was a keyed artifact store (key; type text/file/json; `source_id`/
   `source_type` provenance; `tag`) with a `parent_id` chain. Two things make this an extension of an
   existing idiom rather than a new concept: `fabric/canonical/derived.py:225 CaseContext` already
   carries `parent_case_id` + `evidence_bundle` + `decisions_history` and is checkpointed by
   `conductor/checkpoint.py:Checkpointer`; and `TraceStep`'s `inputs`/`outputs` refs already gesture
   at per-artifact provenance with no store behind them. Decide whether this is a new store, an
   extension of `CaseContext`, or a `fabric` store that `CaseContext` composes.
2. **Mechanism.** Thread it through `_build_parent_tools` / `_build_composed_skill_tool` **alongside**
   the `InvocationContext` cascade — same call sites, second axis. The authorization cascade is the
   working precedent for how a per-hop inherited-and-narrowed thing is done in this tree; follow it
   rather than inventing a parallel propagation path.
3. **Visibility is an authorization question, not a storage one.** A sub-agent's read of a parent
   artifact must go through `PermissionScope`, or this becomes a way around the narrowing that
   `_build_parent_tools` carefully does today. Get this wrong and the feature is a security
   regression.
4. **Write-back.** Whether a sub-agent's artifacts are visible to the parent after return (Kernel's
   isolated-child-state answer was: child reads parent, parent does not read child). Decide
   explicitly; the current behavior is "nothing crosses," so either direction is a change.
5. **What not to port:** Kernel's OData-on-notepads (`jazzx_sdk/odata.py` + `EntityStore.filter`
   already cover it) and its untyped `creator_source` enum.

→ verify (design note): a written decision on all five points, reviewed against
`Builder_Pack_Studio_Paradigm_Assessment` §6 and the `Skill`-composition item in
`Japes_Enhancement_Backlog` P2, since a `Skill` that can carry inherited context interacts with the
still-open assistant-as-skill composition question.
→ verify (implementation): a parent writes an artifact, a sub-agent reads it without re-deriving it;
a sub-agent cannot read an artifact outside its narrowed scope; the existing string-only path still
works for skills that declare no artifact reads.

**Acceptance:** a design note settling all five points, then an implementation where a sub-agent
reads parent-established context under the same narrowing that governs its tools.

**Size: large.** Scope as its own effort; do not fold into a sprint alongside K1–K6.

---

## K8 — Enforced source attribution on retrieval

**Files:** `jazzx_sdk/fabric/rag/store.py`, `jazzx_sdk/fabric/docs/store.py`

Kernel's documented retrieval assembled context **with source attribution**. JAPES delegates embed/
index/retrieve/rerank to Knowledge Hub — which is the *intended* end state, not a gap (Kernel's own
doc says these "will migrate to KF") — but `RAGStore.search` (`:117-157`) returns KH's raw result
list through `listing(results)` with **no citation contract**. The only trace of the intent is a
comment at `fabric/docs/store.py:59` (`entity_id  # KH entity wrapper id (for citation)`).

For SAR narratives and adjudication output, unattributed retrieval is a compliance defect. And
because this property was Kernel's and is nobody's stated deliverable on the KF side, it is exactly
the kind of thing a migration loses silently.

1. Type `RAGStore.search`'s return with a mandatory citation — at minimum `(document_id, chunk_id,
   score)` — rather than passing dicts through.
2. Make it a hard contract: a KH result that cannot be attributed fails loud rather than arriving as
   an uncited snippet. An uncited chunk reaching a SAR narrative is worse than a missing one.
3. Raise it as an explicit **migration exit criterion** for the Kernel→KF work, not just a japes-side
   type change — the SDK can only enforce what KH returns.

→ verify: a well-formed KH result produces a typed citation; a result missing document/chunk identity
raises with the offending payload named; grounding paths that consume `search` compile against the
new type (this will surface every current consumer that silently ignored provenance).

**Acceptance:** no retrieved content can reach a model or a document without a resolvable source.

---

## K9 — `Skill.input_schema` and tool `output_schema` *(gated on the UAF IO decision)*

**Files:** `jazzx_sdk/agents/interactive/spec.py`, `jazzx_sdk/tools/base_registry.py`

Kernel v1 declared `input_schema` **and** `output_schema` on `Agent`, and `output_schema` on `Tool`.
JAPES has `output_schema` at the **turn** level (`agents/interactive/agent.py:103,182,351`,
`llm/providers/openai.py:190`) but `Skill` has no IO fields and `BaseToolRegistry` has no schema
field, so def-backed and `spec_ref` skills are all `(query: str) -> str`.

This is listed here for one reason: **a v1 service that already shipped per-agent and per-tool
schemas is the strongest available evidence that declared IO is not optional** — which is the
substance of pushback #4 in the UAF gap analysis. Phase 3 of `plan_uaf_phase1_additive.md` adds the
skill record fields as metadata; this phase is the tool-side half plus `input_schema`.

**Do not start until the UAF IO-contract question is settled.** If it resolves the way the
assessment recommends (JSON Schema auto-derived from the wrapped agent/tool/process), this phase is
small and mostly mechanical. If it resolves the other way, this phase should not exist.

→ verify (once unblocked): a tool declaring `output_schema` validates its result; a skill declaring
`input_schema` rejects a malformed invocation at the boundary rather than inside the model call.

---

## K10 — `parent_step_id` + concurrency ordinal on `TraceStep` *(governed schema change)*

**File:** `jazzx_sdk/fabric/canonical/trace.py`

Kernel's `Step` had `parent_step_id`, `order`, and `concurrent_order`. JAPES has the concurrency
(`conductor/fanout.py:fan_out(concurrency=8)`, `ensemble.py`, `replication.py`) but not the record of
it: `conductor/engine.py:80 ExecutedStep` is **in-memory only, never persisted**, and `TraceStep`
has `sequence` and `iteration` but no parent link and no concurrency group. So a fan-out's structure
is not reconstructible from the audit record — you can see five steps, not that they were five
parallel branches of one.

The catch: `TraceStep` is `extra="forbid"`, deliberately has **no** `domain_extensions`
(`trace.py:213-216`, which calls a per-step extensions dict "the most common v1.5 failure mode"),
and the schema is declared **frozen at Schema Spec v1.5**. Adding two fields is therefore a governed
cross-team spec change, not a code edit.

1. Start the governed change conversation early — it is cheap now and expensive once more packs
   depend on the current shape.
2. Interim, if the change is not approved: record the parent/concurrency relationship in
   `CanonicalTrace.metadata` keyed by `step_id` via `TraceStepContextHelper` (`trace.py:486-596`),
   which is the sanctioned hatch. Do **not** add a per-step extensions dict.
3. K2's trace mirror depends on this same decision — bundle them into one spec request rather than
   two.

→ verify: a `fan_out` of five branches is reconstructible from the persisted trace as one group of
five, not five unrelated steps.

---

## K11 — Smaller carry-overs

Each is small and independent; batch them as one pass per owner.

| Item | File | Note |
|---|---|---|
| **Tenant-ID propagation** | `common/middleware/context_headers.py:132 HeaderMiddleware`, `jazzx_sdk/handlers.py:321 KERNEL_HEADER_ALLOWLIST`, `server/governed_http.py`, `observability/log.py` | Kernel propagated tenant + correlation + trace context at the gateway. JAPES has correlation (`X-Correlation-Key`) and trace (`X-Trace-Id`/`X-Span-Id`) but **no tenant axis**. Multi-tenant AML/CRE needs it in the context, in `GovernedRouter`, and in structured logs. Cheapest it will ever be. Note it crosses into `common/` (shared submodule) |
| **OTel metric emission** | `jazzx_sdk/observability/telemetry.py` | JAPES is already on the same OTel stack Kernel names — `common/pyproject.toml:44-55` pins `opentelemetry-{api,sdk} ^1.31.1`, the FastAPI/HTTPX/SQLAlchemy/Redis/Celery instrumentations, and `azure-monitor-opentelemetry-exporter`. But it emits **spans only, no metrics**. The data already exists (`llm/health.py:ProviderMetrics`, `llm/cost_tracker.py`, `queue_processor.get_queue_properties`) and is never exported. Kernel's metric set is the right list: LLM latency, tokens per provider, tool duration, queue depth, error rate by component, throughput |
| **MCP composite namespacing** | `jazzx_sdk/agents/interactive/registry.py:191-219` | JAPES is an MCP *server* (`mcp/server.py`) and delegates client duties to the Agents SDK (`agents/openai_provider.py:140`). Kernel used composite namespaced identifiers; JAPES has none, so a tool-name collision across two MCP servers is silent today. Refresh cadence (Kernel's 3600s) is a service concern — skip it |
| **Azure OpenAI provider** | `jazzx_sdk/llm/providers/` | Zero hits for `AzureOpenAI` in `jazzx_sdk/` or `common/`. A thin subclass of the OpenAI provider, and it is the enterprise-deployment default (managed endpoints, private networking, Entra ID). Do this after K1 so it inherits the shared retry rather than a fourth copy |
| **Embeddings in the Gateway** | `jazzx_sdk/llm/` | No embed call anywhere in the SDK — embedding lives entirely inside KH. Fine until something needs to embed *outside* KH (eval similarity, dedupe, routing), which is imminent. Thin, provider-backed, no index |
| **Security-headers middleware** | `jazzx_sdk/server/app.py` | CSP / HSTS / X-Frame-Options / X-Content-Type-Options: **zero occurrences** in `jazzx_sdk/` or `common/`. Normally an ingress concern — except `launcher.py`'s `server` mode and `server/web.py:mount_spa` serve a built SPA **from this app**, so a browser receives these responses directly. ~20 lines, gated to SPA-serving mode |
| **PDF merge, HTML→PDF, Markdown conversion** | `jazzx_sdk/tools/documents/` | Kernel native tools with no JAPES counterpart. Trivial; only worth doing if a pack actually asks |
| **Chunking strategies + per-document flags** | `jazzx_sdk/tools/documents/chunking.py` | `DocumentChunker` has **one** strategy (`section_headers`). Kernel had recursive-character, semantic, and markdown-aware. One strategy is thin for SAR narrative documents. Also port `storage_only` / `build_knowledge_graph` per-document flags (zero hits today) — they are the cost-control surface on a large AML corpus |
| **Server-side graph pushdown** | `jazzx_sdk/fabric/graph/store.py` | `KGStore.query()` filters server-side by substring then does text search **client-side** and slices in Python; `traverse(max_hops)` is N round trips. Fine for a mortgage file, will not survive an AML entity graph. Port as a pushdown on the KH triple endpoint (or an optional SPARQL backend behind the existing interface) — **not** as a policy engine; the typed `Condition` IR + `condition_evaluator` registry stays |
| **Decide `fabric/opa`** | `jazzx_sdk/fabric/opa/store.py` | Every method raises `NotImplementedError`. Its own docstring (`:12-18`) points at the working surface (`KnowledgeHubClient.get_policy_bundle`/`update_bundle`/`evaluate_policy`/`create_policy`) and notes bundle-upload is being deliberately superseded by canonical `Policy`. Wire it or delete it — a raising placeholder reads as capability that isn't there |

---

## Sequencing

**Sprint 1 — the defect batch (run regardless of any UAF decision):** K1, K3, K4, K5, K6, plus K2
steps 1–2. All small, all independently verifiable, several are latent bugs. K5 lands before K6
step 3, since K6's payload refs are K5's first customer.

**Start immediately, in parallel, non-code:** the K10 governed schema request (bundle K2's trace
mirror into it), and the K7 design note.

**Sprint 2:** K8 (needs the KF-side conversation started, so open that with the migration owners
when Sprint 1 starts), K11's tenant-ID and OTel-metrics items, Azure OpenAI provider after K1.

**Blocked, do not start:** K9 until the UAF IO-contract decision. K7 implementation until its design
note is signed off.

Per CLAUDE.md: full suite green after every phase (baseline 2589 passed, 3 skipped); `-X importtime`
diffed against `docs/_importtime_baseline.txt` for K5, K6 and K7 (new stores touch import
structure); CHANGELOG per phase; `>=` dependency floors; `common/` changes (K11 tenant ID) go
upstream to the shared repo first, then a submodule bump — do not shadow shared types locally;
nothing pushed or committed without the push gate.

---

## Explicitly not carried over from Kernel

Recorded here so it does not get re-litigated per PR — full reasoning in
`Kernel_Salvage_Assessment_for_JAPES.md`:

Celery/Redis broker (superseded by Azure Storage Queue + `common`'s `RetryPolicy`/`ExponentialBackoff`
+ `runs/` claim-heartbeat-reaper); persisted LLM-generated plan rows and "multiple alternative plans
per invocation" (`conductor/` authored `Pipeline` + `ensemble`/`replication` are better and have
consumers); polymorphic `Response` row and `quality: int` (typed `Outcome`/`Decision`/`TurnRunEvent`;
`evaluation/` scorers); `learning_strategy`/`learning_config` (v1 aspiration — `fabric/guidance/` +
`evaluation/` cover the real need *with* an approval lifecycle); agent `type` enum; notepad OData;
**SPARQL as a policy engine** (the typed `Condition` IR is testable and replayable, and a future
`rego` kind slots in without a triple store); local response caching (provider-native prompt caching
is the better shape); runtime capability probing (`llm/model_cards.py:ModelCard` declares statically);
per-agent LLM rows; `max_steps` (superseded by `max_turns` + `Loop.max_iterations`);
`context_management_config` (superseded by `CompactionPolicy`'s strategy registry);
`callable_agent_ids` (superseded by `Skill.spec_ref` + `ProfileRegistry`); document reranking and
index-type selection (Knowledge Hub owns the index); Python Sandbox hosting and Integration Hub
(service-layer — though note the SDK has **no client** to either, and if Builder Studio's
"contribute a tool" story includes user-authored Python, a sandbox client is an unowned deliverable).

**One Kernel principle to reject explicitly:** *"Fine-Grained Optimization: per-agent LLM
selection."* JAPES has this and it is a liability at scale, not a feature — per-agent model pinning
is how the tree ended up with three hardcoded `"gpt-5.2"` literals (`agent.py:578,897,915`) and a
Gateway covering half the paths. `task_routing` + `ModelCard` is the better answer: declare what the
task needs, let the Gateway choose.

**Two Kernel principles worth lifting verbatim into `docs/ARCHITECTURE.md`** (which reads from the v1
vantage and needs a refresh regardless): *"High-Auditability — complete traceability through
immutable audit trails and execution provenance tracking for regulatory compliance"* (JAPES delivers
more of this than Kernel did — `CanonicalTrace`, `OverrideEvent`, `VersionBundle`, the autonomy
ladder — but never states it as a principle, so K2 and K6 read as oversights instead of violations of
a standard); and *"Cloud Agnostic — abstraction layers enabling deployment across Azure/AWS/GCP"*
(worth stating precisely because the tree is drifting the other way: Azure Storage Queue, Azure Blob,
Azure DocIntel and the Azure Monitor exporter are all core today; the queue and blob layers are
already behind interfaces, and saying so as a principle is what keeps them that way).
