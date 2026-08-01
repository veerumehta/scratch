# Plan: JAPES 2.0.0 Domain Events, State Machines, and Automation Chassis

Author: Virendra Mehta · 2026-07-13 · Rev 2026-07-14 (per Claude Code review: flowable boundary resolved, envelope relationship pinned) · Rev 2026-07-15 (re-versioned onto the 2.0.0 line per repo practice)
Repo: japes (jazzx_sdk) · Baseline: 2.0.0 line (additive) · Companions: plan_JAPES_2_0_0 governed-value plan (VersionBundle, Refusal), plan_JAPES_2_0_0 authority plan (AuthorityCell, resolver)
Driver: the Commercial Lending corpus demands (a) 47 domain events on a standard envelope {event_id, event, occurred_at, trace_id, version_bundle, payload}, (b) 30 object state machines / 166 transitions where guards name PolicyProfile keys and human-only transitions have no programmatic path, (c) governed automations with idempotency keys, receipts, drift-conflict detection, and compensation, and (d) HTTP conventions (X-Trace-Id/X-Actor-Ref/X-Surface-Ref headers, Idempotency-Key on mutating ops, typed 403/409/412). The envelope, the transition engine, the receipt discipline, and the header conventions are invariant machinery. Event names, transition tables, and connector mappings are pack data (JACI).

Grounding notes (verified 2026-07-13 against dev):
- No domain event envelope exists. events.py is an inbound HTTP->QueueMessage router. models.py MessageHeader is the queue envelope; derived.py CaseFileEvent is close in spirit but case-scoped. docs/plan_unified_envelope.md is partial (traceparent done).
- channels/ has Channel protocol + WebhookChannel (HMAC, retry) - a ready outbound leg for event delivery.
- No state-machine primitive; states are bare enums; conductor/ is procedural; OverrideEvent records state_before/state_after without enforcement.
- automation/ exists (handler.py, schemas.py) but has no idempotency, receipt, or compensation constructs.
- server.py create_app: POST /invoke, GET /health, GET /stream/{id}; no header conventions, no idempotency middleware.

## Phase 1 - DomainEvent envelope and catalog

New module jazzx_sdk/events_domain.py (avoid colliding with events.py; re-export from __init__).
- DomainEvent: event_id (uuid), event (dotted name str), occurred_at (datetime), trace_id (str), version_bundle (VersionBundle), payload (dict). Frozen, extra=forbid on the envelope; payload is free-form dict validated by catalog schema when present.
- EventCatalog: loadable registry mapping event name -> {payload_schema (JSON Schema dict|None), description, channel}. from_dir(path) reading YAML/JSON files, and from_index(index_json_path) accepting the corpus event_index.json format directly so JACI does not have to transform it. validate(event: DomainEvent) checks the name is registered and payload conforms when a schema exists; unregistered names raise fail-closed (packs must declare their vocabulary).
- EventEmitter: thin publisher wired to channels/ (build_channel) plus an in-process subscriber list for tests and conductor coupling. emit(event) appends a TraceStep-visible record: caller passes the active trace context; emitter never invents trace_ids.
- AsyncAPI export is OUT (deferred); the catalog stores enough (name, channel, schema) to generate it later.
- Relationship to the queue envelope (models.py MessageHeader), stated so the two never drift the way the Macer tracking did: two envelopes by design. MessageHeader wraps an invocation (someone asked us to do something); DomainEvent wraps a fact (something happened). Shared conventions are pinned: DomainEvent.trace_id uses the same trace vocabulary as CanonicalTrace and MessageHeader.Tracking (provide a traceparent<->trace_id mapping helper beside the existing W3C handling), and version_bundle is the typed VersionBundle from the values plan wherever it appears.

Acceptance: catalog loads a fixture index of 3 events; a DomainEvent emitted during a queue invocation carries the invocation's trace_id (contract test); emitting an unregistered event raises; emitting a registered event with bad payload raises with schema path; WebhookChannel delivery test reuses existing channel test doubles.

## Phase 2 - Data-driven state machines

Boundary with Flowable and conductor (resolved 2026-07-14; settle-before-code condition met): flowable-core (the sibling BPMN/DMN/CMMN engine repo JAPES already integrates with via tools/workflow.py and the flowable MessageSource) owns process orchestration: activity sequencing, human task routing, process-level timers, long-running flows (e.g. mortgage-app-fulfilment-process). conductor/ owns in-SDK procedural pipelines. The TransitionEngine here owns neither. It is object-lifecycle admissibility only: a synchronous, pure check at the write boundary answering "is this state change legal for this object, by this actor, under this profile". It has no run loop, executes no activities, schedules nothing, and never decides what happens next. TIMER/EVENT trigger_types describe the legal cause of a transition; the machinery that fires at a time or on an event lives in flowable/conductor/queue, which then attempts the transition and is validated like any other caller (flowable delegates calling JAPES endpoints hit the same server-side enforcement). One guard language per concern: object-transition guards use profile-key expressions only; BPMN/DMN conditions remain flowable's language. They do not overlap because object guards are write preconditions, not flow conditions.

New package jazzx_sdk/statemachine/ (schema.py, engine.py).
- TriggerType str-enum: SYSTEM, HUMAN, API, TIMER, EVENT.
- Transition: object_type, from_state, to_state, trigger_type, trigger, guard (str|None, a PolicyProfile key expression), actor_class (str|None), cell_ref (str|None), emitted_event (str|None), notes. Frozen.
- StateMachine: object_type, transitions, states (derived), terminal_states (states with no outgoing transitions). from_records(list[dict]) and from_csv(path) accepting the corpus state_machines.csv column set directly.
- TransitionEngine: apply(machine, current_state, trigger, ctx) -> TransitionResult | Refusal where ctx carries {actor_class, trigger_type, profile: PolicyProfile, matrix: AuthorityMatrixV2|None, emitter: EventEmitter|None}.
  Enforcement rules (each one a corpus invariant):
  1. No matching transition -> Refusal(OUT_OF_SCOPE) naming the attempted edge.
  2. trigger_type HUMAN transitions refuse programmatic invocation: ctx must present actor evidence (actor_class human role + explicit human_initiated flag) else Refusal(HUMAN_ONLY_ACTION); when cell_ref set, also consult the authority resolver.
  3. Guards resolve against PolicyProfile.get(key); a guard naming a missing key fails closed. Guards never contain numeric literals; engine rejects a guard string containing a bare number at load time (lint check in from_records).
  4. Terminal states are immutable: apply() on a terminal state refuses; the documented alternative is supersession (new object version with lineage), not an edit.
  5. On success, if emitted_event is set and emitter provided, emit through the Phase 1 catalog.
- Storage integration is deliberately light: the engine is pure; canonical stores keep owning persistence. Add a helper guard_transition(store_update_fn) decorator for stores that want enforcement at write time.

Acceptance: fixture CSV with 6 transitions across 2 objects; tests for each of the five rules; loading a guard "ratio > 1.25" fails the numeric-literal lint while "ratio > profile:dscr_floor" passes.

## Phase 3 - Automation chassis

Extend jazzx_sdk/automation/.
- schemas.py additions: Receipt {receipt_id, idempotency_key, matrix_cell_ref, target_system, target_record, pre_write_value, post_write_value, conflict_detected (bool), rollback_ref (str|None), status (RECEIPTED/BOUNCED/COMPENSATED), occurred_at, trace_id, version_bundle}. The rule in the docstring: no receipt means the write did not happen.
- New automation/governed.py GovernedAutomation base: run(request) template method enforcing, in order: idempotency check (key store lookup; duplicate returns the original Receipt, no re-execution), authority check via resolver (cell_ref required on every side-effecting request; refusals returned typed), read-before-write drift check (fetch current target value; mismatch vs expected -> Refusal(PRECONDITION_FAILED) with conflict_detected receipt, routed to human), execute, receipt, emit event. compensate(receipt) abstract hook; at-least-once consumers must be idempotent by construction of the key.
- IdempotencyStore protocol + InProcess and fabric.entities-backed implementations (EntityStore already gives typed JSONB CRUD).
- Poison handling: leave queue-level retry/poison to the host queue (queue_processor.py); the chassis records attempt_count on the receipt.

Acceptance: double-submit same idempotency_key executes once and returns identical receipt; drift test (target mutated between read and write window simulated) yields conflict receipt + typed refusal; human-only cell_ref write attempt yields 403-class refusal and a logged attempt.

## Phase 4 - Governed HTTP conventions

server.py additions (all opt-in via ServerSettings flags so existing deployments are untouched):
- Middleware reading/propagating X-Trace-Id, X-Actor-Ref, X-Surface-Ref into a request context (ContextVar, mirroring the security-context pattern JACI uses); generated trace_id when absent on non-governed routes, required (400) on governed routes.
- Idempotency-Key required on mutating governed routes; wired to IdempotencyStore.
- Typed error mapping already lands in the values plan (Refusal -> status); extend to the 409 already-processed idempotent-replay response shape (returns original result, 200 or 409 per route declaration).
- extra_routes stays the mechanism for domain routers; add a GovernedRouter helper (APIRouter subclass) that applies the above per-route declarations so JACI's /api router declares {mutating: bool, cell_ref: str|None} per endpoint instead of re-implementing checks.

Acceptance: contract test hitting a GovernedRouter route without Idempotency-Key gets 400; with duplicate key gets replay semantics; headers round-trip into TraceStep context.

## Out of scope

The 47 event names/schemas, 166 transitions, connector field mappings, LOS adapters (all JACI pack data / scenario code); AsyncAPI and OpenAPI document generation (deferred; catalog and GovernedRouter store the inputs); scheduler/timer infrastructure for TIMER triggers (host concern).

## Sequencing

Phase 1 and 2 are independent of each other; Phase 3 needs Phase 1 (events) + authority plan Phase 4 (resolver); Phase 4 needs the values plan Phase 3 (Refusal mapping). All additive; no version breaker in this plan.
