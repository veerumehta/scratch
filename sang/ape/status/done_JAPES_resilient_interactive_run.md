# Plan: Resilient Interactive Runs (stop / resume / durable turn)

Design pass (no code yet). Repo: japes (jazzx_sdk). Driver: juno's queue-backed run execution
(cooperative cancel + event journal + per-conversation turn queue + reaper) — the machinery is generic;
generalize it so InteractiveAgent can become the durable backbone juno (and other assistants) build on.

## Problem

`InteractiveAgent.respond_stream` is an async generator coupled to the request. Three gaps:
1. **No resume.** A dropped connection loses in-flight output. `stream_invocation_sse(replay, tail)`
   backfills from Redis, but the Redis stream is ephemeral/trimmed (maxlen) — replay doesn't survive a
   pod restart or a long reconnect gap.
2. **No stop.** A turn can't be cancelled mid-flight; `asyncio` `task.cancel()` would abort finalization
   (partial output lost, conversation left inconsistent).
3. **No per-conversation serialization.** Two turns on the same conversation interleave/race.

## Goals / non-goals

Goals: a durable turn record + append-only event journal; **cooperative** cancel; resumable stream that
survives restart; per-conversation FIFO; pluggable stores (InProcess + fabric.db); cross-pod stop.

Non-goals: replacing the queue/job runtime; flowable orchestration; byte-identical replay; a general
workflow engine. Boundary: this is **conversation-turn** resilience for InteractiveAgent — distinct from
the job runtime (invocations) and from the state-machine/automation chassis (which govern object writes).

## Grounding (verified against dev)

- `InteractiveAgent.respond` / `respond_stream` exist; `respond_stream` yields `InteractiveStreamEvent`
  (deltas then a terminal `done`), request-coupled.
- `streaming.StreamPublisher` (Redis) + `stream_invocation_sse(replay=, tail=)` give live tail +
  browser-reconnect backfill — but over an ephemeral Redis stream.
- `fabric.db` gives `Repository[T]` + `register_metadata` + `session()` (sqlite|common backends);
  `SqlConversationStore` already rides `fabric.db`.
- `ConversationStore` + the Session seam own turn history/persistence.
- `automation.IdempotencyStore` / `GovernedAutomation` set the "protocol + InProcess + fabric.db-backed"
  pattern to mirror; `governed_http` sets the request-context + `X-Trace-Id` conventions to reuse.

## Architectural consistency (generalize + extend, don't transcribe juno)

juno is the inspiration; the machinery must land as an extension of japes' own architecture, not juno's
shape re-expressed. Concretely:
- **Reuse japes' run/trace vocabulary, don't invent a parallel one.** The turn-run is keyed to
  `trace_id` (a `CanonicalTrace` already models a run's trace). Name it `TurnRun` (or `InteractiveRun`),
  NOT `Run` — `ExperimentRun` (evaluation) and `ConductorRun` (conductor) already exist; `Run` collides.
- **The journal mirrors the existing typed stream events, not a new event language.** `TurnRunEvent`
  wraps the `StreamPublisher` taxonomy (`LLMChunkEvent`/`ToolStartEvent`/`DoneEvent`, `EVENT_FIELD`) +
  `trace_id`/`seq` — it is the *durable mirror* of the live stream, so live and replay speak one vocabulary.
- **Reconcile with the existing queue runtime — principle, not option.** japes already has
  `queue_processor`; the turn dispatcher should reuse/compose with it, not stand up a parallel worker.
  (If it can't cleanly, say why in the decision below — but the default is reuse.)
- **Stores follow the established pattern:** protocol + `InProcess` + `fabric.db`-backed, mirroring
  `IdempotencyStore`/`ConversationStore` (not bespoke tables + hand-rolled CRUD).
- **Streaming reuses `stream_invocation_sse`;** the journal is added only as the durable replay source
  behind it (japes already had replay+tail — the delta is durability, nothing re-ported).

## Core model

- **TurnRun** (durable; `fabric.db` Repository): `run_id`, `trace_id` (ties to `CanonicalTrace`),
  `conversation_id` (correlation_key), `status` (`queued|running|interrupted|completed|failed`),
  `claim_token`, `heartbeat_at`, `stop_requested` (bool), `input` (turn request), `partial_output`,
  `error`, timestamps.
- **TurnRunEvent** (append-only journal): `run_id`, `seq` (monotonic per run, writer-owned), plus the
  **existing typed stream event** (`StreamPublisher` taxonomy) and `created_at`. The **durable** backing
  for resumable streaming — Redis stays the fast live path; the journal is the source of truth for replay,
  in the same event vocabulary as the live stream.

## Phase 1 — TurnRun + TurnRunEvent + TurnRunStore
`TurnRunStore` protocol (`create`/`get`/`append_event`/`events_since(cursor)`/`update_status`/`heartbeat`/
`request_stop`/`claim_next`) with `InProcessTurnRunStore` + `DbTurnRunStore` (fabric.db), mirroring
`IdempotencyStore`. `register_metadata` so a service's alembic sees the tables.
Acceptance: create→append→`events_since` round-trips; status transitions; InProcess/Db parity contract test.

## Phase 2 — ResilientRunner (cooperative cancel + journal)
Wraps `respond_stream`: for each event → append a `RunEvent` + publish to `StreamPublisher` (live) +
update `partial_output`; **between events poll `stop_requested`** (or a passed `asyncio.Event`). On stop:
break, finalize gracefully (persist partial to the conversation store, journal a terminal `interrupted`
event, `status=interrupted`) — **never** `task.cancel()`. Renew `heartbeat_at`+`claim_token` periodically.
Cross-pod stop: `request_stop(run_id)` sets `stop_requested=true` durably; the running worker (maybe a
different pod) polls it (optional fast nudge via Redis/LISTEN-NOTIFY later; poll is the floor).
Acceptance: a mid-stream stop yields `status=interrupted` with partial persisted + terminal journal event;
finalization runs; no `CancelledError` leaks / partial corruption.

## Phase 3 — Resumable stream (journal-backed) — the headline value
`resume(run_id, from_seq)` → replay `RunEvents` since `from_seq` (durable, survives restart) then tail
live. The client tracks `last_seq`; a reconnect replays the gap then follows. Bridge: `stream_invocation_sse`
already does replay+tail over Redis; add the **journal** as the durable replay source when Redis has
trimmed/expired.
Acceptance: kill the live stream mid-turn → `resume(from_seq)` delivers missed events + continues to
`done`, including after a simulated Redis flush (journal replay).

## Phase 4 — Turn queue + dispatcher + reaper (production hardening)
Per-conversation FIFO: at most one `running` run per conversation (Db: a partial unique index on
`conversation_id WHERE status='running'`; InProcess: an in-memory lock). New turns enqueue (`queued`);
a dispatcher claims the next when the current terminates. `claim_next`: atomic `UPDATE … SET
status='running', claim_token=… WHERE status='queued' ORDER BY created_at LIMIT 1 … FOR UPDATE SKIP
LOCKED RETURNING`. Reaper: requeue/fail runs with a stale `heartbeat_at`, **claim-fenced** (reap only if
`claim_token` unchanged since observed) so a healthy renewed run isn't reaped (juno's `dfb3f85a` fix).
Acceptance: two concurrent turns on one conversation run sequentially; a stalled run is reaped/requeued;
a renewed run is spared.

## Phase 5 (optional) — server wiring
Endpoints via `GovernedRouter`/`extra_routes`: start run / stop run / stream+resume run; reuse
`X-Trace-Id` + the governed-HTTP conventions.

## Open decisions
- **Tail wakeup:** poll journal vs Redis pub/sub vs Postgres LISTEN/NOTIFY. Start: Redis live + journal
  replay; add LISTEN/NOTIFY later for cross-pod tail without Redis.
- **Partial output home:** on the Run record (simple, for in-flight) vs the conversation store (single
  source). Lean: `Run.partial_output` in-flight; the final answer lands in the conversation store on
  completion as normal.
- **Cancel signal API:** durable `stop_requested` (cross-pod) vs `asyncio.Event` (same-process) —
  support both (Event in-process, flag cross-pod).
- **Cadence:** heartbeat ~10s, reap after ~3× missed (defaults; tunable).
- **How to reuse the queue runtime** (reconciliation is a principle, not a yes/no): does a `queued`
  `TurnRun` dispatch through the existing `queue_processor` (preferred — one worker model), or does that
  couple turn-lifecycle to job-invocation semantics badly enough to justify a thin fabric.db dispatcher
  that still shares the claim/heartbeat/reaper helpers? Default: reuse; document the seam if it can't.

## Sequencing / effort
Phases 1–2 are the core (durable turn + cooperative stop + journal); Phase 3 delivers the headline
(resume); Phase 4 is production hardening. All additive, no breaking change. Effort medium-high — the DB
schema + worker lifecycle (claim/heartbeat/reaper) are the real cost, not the runner logic.
