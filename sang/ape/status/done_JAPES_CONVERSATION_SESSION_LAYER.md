# plan_JAPES_CONVERSATION_SESSION_LAYER.md

**Status:** Draft for discussion (supersedes the #4/#7 sketch in plan_JAPES_CONVERSATION_COMPRESSION follow-ups)
**Author:** (Veeru / Claude session 2026-06-24)

## Why this exists

The 1.9.4 work added japes-native session memory + compaction (`MemoryStore`, `CompactionStrategy`,
lossless `supersede`/`load_raw`). Reviewing juno + KH + the agent-execution service showed that
abstraction is at the wrong layer for the agentic path. This redesigns it around the *concept*, not
any one SDK.

## Findings (ground truth, 2026-06-24)

- **`AgentExecutionService.run()` has no session.** It's the provider-portable generic tier: takes a
  `messages` list (+ tools/schema/provider/model/tool_executor). Stateless. (`service.py:127`)
- **Two InteractiveAgent paths.** `_respond_single_shot` → `agents.run()` (no `Runner`, no framework
  session — history is whatever's in `messages`, which is why a bespoke `MemoryStore` default exists).
  `_respond_agentic` → `agents.openai.build_agent()` + `Runner` (OpenAI Agents SDK; can take a `Session`).
- **The grounded-Q&A path is LLM, just non-*agentic*.** Its custom store exists because it bypasses the
  `Runner`, not because it's a non-LLM flow.
- **juno persists to its own Postgres, not KH.** `PostgresCopilotSession` (`app/copilot/session.py`)
  implements the OpenAI Agents SDK `Session` protocol (`get_items`/`add_items`/`pop_item`/
  `clear_session`), storing every SDK item to `copilot_session_items` via the shared `common.core.db`
  (SQLModel/alembic). Lossless = `clear_session()` soft-deletes (`is_summarized=True`). Item fidelity =
  preserves `function_call`↔`function_call_output` pairing + masks large outputs so the Responses API
  never 400s. Compaction = wraps it in `agents.memory.OpenAIResponsesCompactionSession` with a
  token-authoritative trigger (char/4 only as turn-1 fallback). base_session=raw PG, compaction_session
  =the wrapper.
- **KH is platform persistence too** (entity store on PG JSONB, collections, FS) — but is **not** used
  for sessions in juno. Whether sessions *should* live in KH vs a separate pg is **OPEN** (offline
  discussion; see Open Decisions).

## Principle: concept-first, substrate-second

Our abstractions must name the **concept**, not pass through the current SDK's nouns. If we swap the
OpenAI Agents SDK for the Anthropic SDK or LangGraph tomorrow, the concept layer and all pack/agent code
stay put; only an adapter changes. So: no `Session` in our core names (that's an SDK noun); no leaking
of OpenAI Responses item shapes into the core.

## The model

**`memory` is the general concept (reserved for v2 Memory Fabric); what we have today is conversation
continuity.** So we name the current layer for the conversation, and don't spend the `memory` namespace
on a threading toggle. A future general `memory: MemoryBinding` (semantic/episodic/KH-backed) is a
*sibling* concept, not built here.

```
   memory  (RESERVED: v2 Memory Fabric — knowledge bindings, durable episodic/semantic recall)
      ┆ (sibling concept, not built here)
   conversation  (what we build now: turn continuity + a bounded working view + lossless archive)
       │ persisted by        │ bounded by              │ bound to substrate by
   ConversationStore    CompactionPolicy (config)   ConversationBinding   [P2]
   (turn store;         + CompactionStrategy (how)  (the only SDK-aware layer)
    load/append/        - summarize | drop |        - OpenAIAgentsBinding (impl agents SDK
    load_raw/supersede)   token ("responses")         Session protocol)
   - InProcess (default)  - juno token trigger       - AnthropicBinding (messages)
   - pg via common.core.db  upstreams here           - LangGraphBinding (checkpointer) [future]
     (provisional std; swappable to KH)
   - CompactingConversationStore = a wrapper applying a CompactionStrategy to any store
                          ▲ AgentExecutionService owns the conversation + binding factories
```

### Concepts (naming ADOPTED 2026-06-24)

Principle: name the *concept*, not the mechanism. `memory` is the general concept (the v2 Memory Fabric:
knowledge bindings, durable episodic/semantic recall) — so it's **reserved**, not spent on a
conversation-threading toggle. What we have today is **conversation continuity**, named as such.

- **`memory`** (reserved) — the general recall substrate (Memory Fabric / `MemoryBinding`). Not used by
  this layer; held for v2 so the namespace is free when real memory arrives.
- **`ConversationStore`** (ABC; was `MemoryStore`) — persistence of a conversation's turns. Lossless
  shape kept: `load`=working view, `load_raw`=archive, `append`, `supersede`(replace working), `clear`.
  Backends pluggable; default provisional = pg via `common.core.db`, swappable to KH.
- **`InProcessConversationStore`** (was `InMemoryStore`) — process-local default. ("in-memory" was an
  impl detail masquerading as a concept, and collides with `memory`.)
- **`CompactingConversationStore`** (was `CompactingMemoryStore`) — a **wrapper** that applies a
  `CompactionStrategy` to any `ConversationStore`. Kept as a wrapper (composition), *not* collapsed into
  the base — so a store can exist with no compaction, and any backend gets compaction for free.
- **`CompactionPolicy`** (Pydantic config; was `CompressionConfig`) — declarative *what* (strategy /
  trigger / max_messages / keep_recent / max_chars / model). "Compression" is token-pruning jargon; we
  do *compaction* (shrink the working view, keep the archive).
- **`CompactionStrategy`** (ABC) — the pluggable *how* (kept; GoF Strategy). Impls
  **`SummarizeStrategy`** / **`DropStrategy`** (was `SummarizeCompaction`/`DropCompaction`, renamed for
  consistency with the ABC). Registry (`register_compaction_strategy`/`build_compaction_strategy`) and
  `llm_summarizer` unchanged. juno's token-authoritative strategy registers here as `"responses"`.
- **`Conversation`** (aggregate; P2+) — *optional* convenience that bundles a `ConversationStore` +
  `CompactionPolicy` + `ConversationBinding` behind one handle; introduce only when the binding work
  needs it. Holds provider-neutral **`ConversationItem`**s (message / tool call / tool result /
  reasoning — *not* OpenAI Responses shapes; old #4).
- **`ConversationBinding`** (port; P2) — the *only* SDK-aware layer. Maps a conversation to whatever the
  substrate calls a session (`OpenAIAgentsBinding` etc.). `AgentExecutionService` owns the factory.

### Spec fields (ADOPTED)

```
InteractiveAgentSpec
  conversation: bool = False          # was: memory: "none"|"session"  — enable turn threading
  compaction: CompactionPolicy | None # was: compression: CompressionConfig
  knowledge: list[KnowledgeBinding]   # unchanged (grounding — "memory" in the broad sense)
  # reserved: memory: MemoryBinding   # v2 Memory Fabric; intentionally not used yet
```
(Value choice: `conversation: bool` since it's binary; `"off"/"on"` is the alt. Not `"session"` — that
mismatches the field name.)

### Ownership / wiring

`AgentExecutionService` gains a conversation factory (concept-level), e.g.:

```python
conv = agents.conversation(session_id, store=..., compaction=...)   # concept object
# agentic path: AES binds it to the substrate the Runner needs
binding = agents.bind_conversation(conv)        # -> OpenAIAgentsBinding today
result = await Runner.run(agent, input=..., session=binding)
# single-shot path: no Runner — just read the working view
result = await agents.run(system_prompt=..., messages=conv.working_items())
```

Both InteractiveAgent paths share one conversation; only the agentic path needs a `ConversationBinding`.
`run()` stays stateless/provider-portable (no session param) — the agent assembles `messages` from the
store's working view, exactly as today, so the generic tier doesn't grow an SDK dependency.

## How juno upstreams

- `PostgresCopilotSession` → a **pg `ConversationStore`** on `common.core.db` (its soft-delete *is* the
  lossless `supersede`/`load_raw`).
- `OpenAIResponsesCompactionSession` + token trigger → a `"responses"` **`CompactionStrategy`** +
  the **`OpenAIAgentsBinding`** (which is where Responses item-pairing/masking belongs).
- Net: juno keeps its battle-tested code; japes gains it as the reference implementation behind the
  concept ports; macer/assistant get it by config, not by re-deriving.

## Rename map (ADOPTED — full delta vs shipped 1.9.4)

| Shipped 1.9.4 | Adopted | Why |
|---|---|---|
| `spec.memory: "none"\|"session"` | `spec.conversation: bool` | it's conversation continuity, not memory; frees `memory` for v2 |
| (n/a) | `spec.memory: MemoryBinding` *(reserved)* | v2 Memory Fabric namespace, held open |
| `spec.compression: CompressionConfig` | `spec.compaction: CompactionPolicy` | we compact, not compress (token jargon) |
| `MemoryStore` | `ConversationStore` | it stores conversation turns; "memory" overclaims |
| `InMemoryStore` | `InProcessConversationStore` | "in-memory" = impl detail; collides with `memory` |
| `CompactingMemoryStore` | `CompactingConversationStore` | wrapper over any store + a strategy |
| `CompressionConfig` | `CompactionPolicy` | declarative config = a policy; not "compression" |
| `CompactionStrategy` (ABC) | *unchanged* | already the right concept (GoF Strategy) |
| `SummarizeCompaction`/`DropCompaction` | `SummarizeStrategy`/`DropStrategy` | consistency with the ABC |
| `register_/build_compaction_strategy`, `llm_summarizer` | *unchanged* | correct as factory/registry names |

New (P2+, additive): `ConversationBinding` (+ `OpenAIAgentsBinding`), optional `Conversation` aggregate,
`ConversationItem` model, AES conversation/binding factories.

## Decisions made

- **Concept-layer naming, not mechanism.** `memory` is the general concept (v2 Memory Fabric) and is
  **reserved**; today's layer is *conversation continuity* and is named for it. See the rename map.
- **Renaming is free.** All the renamed symbols (`MemoryStore`/`InMemoryStore`/`CompactingMemoryStore`/
  `CompressionConfig`/`CompactionStrategy` impls) and the spec fields (`memory`/`compression`) are used
  **only inside japes** (SDK + its 2 tests). Verified 2026-06-24: no consumer (jaci, k9, juno, macer,
  alt checkouts) imports the symbols; jaci uses `InteractiveAgentSpec` but never sets `memory`/
  `compression`; no YAML profile uses those keys. → clean rename, **no deprecation shims, no migration.**
- **Persistence default (provisional): pg over `common.core.db`** — adopt juno's approach as the default
  `ConversationStore` backend, but **keep it behind the port** so we can switch to a KH-backed store if
  db-over-KH becomes the platform standard. `InProcessConversationStore` stays the zero-config default
  until the pg store lands; KH remains a candidate backend, not ruled out.

## Resolved: persistence placement (2026-06-24, after the cross-repo persistence research)

- **Conversation = relational, via `common.core.db`** (the established pattern — juno already keeps it
  there as `copilot_session_items`; KH fronts *knowledge* — docs/entities/policy — not chat scrollback).
- **Exposed through `fabric`**: add `fabric.conversation` so the backend is a fabric-managed detail
  (placement layer — extends fabric's existing `backing` + `retrieval_mode` pattern). Caller (juno)
  uses `ctx.runtime.fabric.conversation`; never touches `common.core.db` or KH directly.
- **No db-name config needed for starters.** `common.core.db` is already env-scoped per service
  (`DB_ASYNC_CONNECTION_STR`), so `SqlConversationStore` uses the ambient session factory → the
  service's own db (`juno_db` etc.) automatically. Defer a configurable db-name / per-store placement
  policy / KH placement until a concrete need (the "accept a db name" hook is conditional + later).
- **Default offline = `InProcessConversationStore`** (SDK/standalone has no DB), mirroring how no
  `kh_client` falls back to Mock. Sql store is opt-in by services that have `common.core.db` configured.
- **Table DDL is the service's alembic**, not the SDK: japes ships the `SqlConversationStore` + its
  SQLModel model; the service imports the model's metadata into its alembic to create the table.
- **Reserved general `memory: MemoryBinding` → KH** (semantic/durable tier), not conversation.

## Open decisions (NOT settled here)

1. ~~Is db-over-KH the eventual standard?~~ **Resolved above** — conversation→`common.core.db`;
   KH = the reserved durable-memory tier. Per-store placement config deferred until needed.
2. **Single-shot unification** — keep the Runner-less single-shot path reading `working_items()`, or
   route it through a tool-less `Runner` so there's literally one code path. (Lean: keep it read-only;
   it's simpler and avoids a Runner for a single completion.)
3. **`ConversationItem` granularity** — how much of the provider-neutral item model to build now vs when
   item-fidelity (old #4) is actually needed for the agentic path.
4. **`spec.conversation` value** — `bool` (lean) vs `"off"/"on"` string.

## Phasing

- **P0 (rename, no behavior change): ✅ DONE 2026-06-24.** Applied the Rename map (spec fields +
  store/config/strategy names) across spec.py / agent.py / memory.py / both `__init__.py` exports +
  tests (test_session_memory.py updated, test_compression_config.py → test_compaction.py). No shims.
  50 tests pass; jaci/juno editable venvs verified live. Folded into japes 1.9.4 (unpushed).
- **P1: ✅ DONE 2026-06-24.** Extracted the wiring to `build_conversation_store(spec, store, agents)`
  (in memory.py); `AgentExecutionService.conversation_store(spec, store)` is the owned factory;
  `InteractiveAgent` wires its store through the shared impl (stays decoupled from requiring the method
  on a duck-typed runner). Functionally identical. No `Conversation` aggregate yet (not needed until P2).
- **P2: A-set DONE 2026-06-24** (structure built; B/C stubbed). `ConversationBinding` ABC +
  `OpenAIAgentsBinding` (adapts `ConversationStore` → agents SDK `Session`, lossless soft-clear) in
  binding.py; `AES.bind_conversation`; `_respond_agentic` hands the Runner `session=` when conversation
  is active (input = new turn only; session persists). Stubbed: `_to/_from_responses_items` item
  fidelity (B — fill from juno: pairing/masking) and the pg/KH store backend (C — offline call).
  *Remaining P2 (gated):* fill the fidelity seam with juno's code (or accept juno's Session directly).
- **P3: prototype DONE 2026-06-24 (v1.9.5, local commit c5e515b).** `fabric.conversation` on
  `KnowledgeFabric` (placement-managed; default `InProcessConversationStore`, `conversation_backend="sql"`
  → `SqlConversationStore`); `SqlConversationStore` = lossless store on `common.core.db` (plain SQLAlchemy
  2.0; `conversation_message` archive + `conversation_overlay` working view; resolves to the service's
  own db via `DB_ASYNC_CONNECTION_STR`, no db-name config). 5 tests + a DB round-trip (skips w/o
  aiosqlite). *Remaining P3:* the consuming service wires its alembic at `SqlConversationStore.metadata`
  (juno) + optionally upstream juno's token policy as the `"responses"` strategy.
- **P4 (later):** `ConversationItem` provider-neutral model + per-binding serialization (old #4),
  defense-in-depth + telemetry (old #5/#6).
