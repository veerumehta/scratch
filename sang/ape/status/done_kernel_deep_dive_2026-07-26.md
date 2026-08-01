# Kernel deep dive — what else generalizes into japes

**Status:** done (2026-07-26) — see backlog below.

## Why

Recurring light surveys of kernel/juno/assistant/jazzx-assistant (this one included) catch what's in
recent commit titles, but kernel is the oldest and most capability-dense of the four services — its
`app/` tree has whole subsystems (MCP client, a notepad concept, two stream-shaped directories,
telemetry, resource management) that a commit-log skim won't surface if they haven't changed
recently. A structural, module-by-module pass is worth doing once, separate from the recurring
"what changed lately" survey.

## Scope

Kernel's `app/` subsystems, compared against japes's current SDK surface
(`jazzx_sdk/{clients,conductor,fabric,tools,llm,runs,agents,connectors,experts,modes}` +
`observability.py`/`concurrency.py`/`handlers.py`/`tracing.py`/`client_layer.py`):

- `app/mcp_client` — does japes have any MCP (Model Context Protocol) tool-calling support at all?
  If kernel's is the only implementation across all four services, this is a strong SDK candidate.
- `app/notepad` — undocumented from the directory name alone; find out what capability this is
  before judging whether it generalizes.
- `app/stream` vs `app/streaming` — two separately-named directories; likely one is the newer
  `/api/v1/stream` API (added recently, per `32a3df7e`) and the other is older/internal. Understand
  the split before comparing either against japes's own streaming (`agents.interactive`'s
  `respond_stream`, `jazzx_sdk.channels.websocket`/`webhook`).
- `app/collection` — collection-level Knowledge Hub operations; compare against
  `KnowledgeHubClient`'s current method surface for gaps (create/list/manage collections).
- `app/telemetry` vs `jazzx_sdk/observability.py` + `tracing.py` — compare depth; kernel is a much
  older, more battle-tested telemetry surface.
- `tests/resource_manager` (no matching `app/` dir seen at top level — find where this actually
  lives) — likely connection/resource pooling; relevant given this session's finding that
  `KernelClient` had no pool-limit cap until today.
- `common/middleware`, `common/core` — kernel's own foundational layer; check for patterns already
  proven here that `fabric.*` doesn't yet have an equivalent of.

Explicitly out of scope: kernel's own business/domain logic (prompt content, routing rules, Azure
Functions deployment glue, Celery task specifics) — only the *pattern*, not the domain content,
is a candidate.

## Method

Per subsystem: (1) does japes have an analogous primitive at all — if not, is it multi-consumer-relevant
(candidate) or kernel-specific (skip)? (2) if japes has one, is kernel's more mature/battle-tested in a
way worth backporting? (3) cross-check the "don't generalize unhit problems" test — would a second
consumer besides kernel actually hit this gap, or is it speculative?

## Deliverable

A ranked backlog (mirrors the existing cross-repo survey approach), each item scored on: consumer
impact, effort, and risk of touching a shared primitive. Top 2-3 items get taken to actual PRs;
the rest get logged for later.

## Result

**Build (real PRs):**
1. **MCP client support.** Kernel's `app/mcp_client/` is a real MCP client (YAML-config server
   registry + discovery); japes has only the *server* side today (`create_mcp_server`), zero
   client-side MCP consumption. Not speculative — any japes agent hitting a third-party MCP server
   (GitHub, Slack, Azure) has no path today. Cheaper than it looks: `openai-agents` (already wrapped
   by `jazzx_sdk.agents.run_kit`) ships native `MCPServerSse`/`MCPServerStdio`/`MCPServerStreamableHttp`
   — the work is a thin config/discovery layer over that, using kernel's YAML-config pattern as
   reference, not its transport code. Needs an allowlist for the new external-server trust boundary.
2. **Notepad-style scratch KV store.** Kernel's `app/notepad/` is an agent-scoped KV store with
   blob overflow for large values and parent/child sharing across sub-invocations, plus ready agent
   tools. No japes equivalent composing `fabric.db`+`fabric.blob` into this shape. Build as a thin
   `NotepadStore` over existing fabric primitives, not a port of kernel's tables.
3. **Multi-key LLM provider rotation.** `app/llm/key_manager.py::APIKeyManager` spreads calls across
   `PROVIDER_API_KEY`/`_1`/`_2`/... to dodge per-key rate limits. Small, cheap, real pain point — fold
   in alongside `llm/routing.py`'s `RetryStrategy`.

**Skip / already closed:**
- `app/stream` vs `app/streaming` — resolved: `streaming` is the mature contextvar-based
  `StreamPublisher`, `stream` is a newer narrow Redis-XADD HTTP layer on top. Neither worth
  backporting — japes's explicit-generator `respond_stream` is architecturally cleaner than kernel's
  global-contextvar approach (which kernel itself had to work around elsewhere).
- `app/collection` — kernel-specific legacy DB-collection CRUD mid-migration to KH; no generalizable
  pattern, japes talks to KH directly already.
- `app/telemetry` — already closed; its one exportable idea (OTel env-leak sanitizer) is already in
  `jazzx_sdk/tracing.py::sanitize_leaked_otel_env_vars`. Japes's own tracing is already more developed.
- `common/middleware/context_headers.py` — same goal as japes's `request_headers_provider`/
  `CallerIdentity`; japes's explicit-provider design avoids the contextvar fragility noted above.
- `common/core/pagerduty` — ops/infra-specific, out of SDK scope.
- The guessed `tests/resource_manager` location was a red herring (covers `key_manager.py`, not
  connection pooling — see item 3).
- `document_utils/format_detection.py` — trivial magic-byte sniffing, superseded by japes's own
  doc-tier routing.

Not superseded: `plan_agent_definition_store_and_facade.md` (the agent-definition-registry gap this
deep dive deliberately didn't re-litigate) stays separately held.
