# Plato service Phases 3 and 4: generated skill routes, process-start, trace of record

Live plan, runtime session. Source of scope: `plans/Plato/plan_JAPES_PLATO_SERVICE.md` §Phase 3,
§Phase 4. Written 2026-10-02 from the v2.6.0 tree; start a fresh session from this file.

## Decisions (made 2026-10-02)

| # | Decision | Outcome |
|---|---|---|
| UAF-9 | Trace format of record | **`CanonicalTrace`.** Release and skill versions ride `VersionBundle.extra` and `CanonicalTrace.metadata` (Spec-v1.5 frozen `trace.py`); named fields would be a cross-team spec change. MLflow/OTel traces stay observability, not the record. |
| D4 | Per-skill IO on the execution path | **Staged.** Stage 1: invoke routes and OpenAPI only for skills with a typed signature today, or a hand-declared schema. Stage 2: derive schemas and typed signatures for the `as_tool` and `spec_ref` branches of `_build_parent_tools`, as its own commit with the full suite plus dependent packs. |
| D3 | Who owns process-start | **Deferred.** Revisit when a consumer exists and the BPMN runtime's URL, auth and a test instance are provided; Plato is the intended owner then. |

## Order

Phase 4 first: it is M, its gate has a recommendation, and it closes `TODO(stream-release-id)`
(`plato/api/assistants.py`).

### Phase 4 — trace of record (M)

**Done 2026-10-02, `7bba88aa`** (`agents.interactive.turn_trace`, Plato `GET {prefix}/traces/{id}`,
`release_id`/`trace_id` on the stream end, client `trace`/`ChatStreamEnd`). Not in it: `GET /decisions/{id}`.

Today: assistant releases exist (`manifest/store.py` `release_id`, `server/assistant_runtime.py`
returns it with the agent; `/chat` names it). A streamed turn binds its agent when the worker
claims it, so its release belongs on the terminal event the coordinator writes.

1. Persist a `CanonicalTrace` per chat turn (blocking and streamed), serving it under `/v1` by
   extending the existing trace lookup (find where `trace_routes` lives now; it moved from
   `observability/`).
2. Stamp `agent_release_id` and each invoked skill's version into `VersionBundle.extra`; per-step
   refs via `CanonicalTrace.metadata[step_id]` (`TraceStepContextHelper`).
3. Stamp `cost.MODEL_DATA_VERSION` beside the model pins.
4. A legacy (unreleased) definition's trace carries `legacy_unversioned` and no release id.
5. The streamed turn's terminal event carries `release_id`; remove `TODO(stream-release-id)`.
6. Client: trace read method + contract; `ChatTurn`/stream terminal contract gains `release_id`.

Acceptance: a released assistant's trace names its release and every skill version invoked; a
legacy one is marked; the interactive suite passes with no releases present.

### Phase 3 — generated skill routes, async operations, OpenAPI (L; process-start deferred)

Stage 1 (D4):
1. `POST /v1/assistants/{id}/skills/{skill}/invoke` per skill from the resolved release, on
   `GovernedRouter`, body validated against the input schema, honouring `Skill.visibility`; only
   skills with a typed signature or a declared schema get a route, the rest are listed as not
   invocable.
2. `POST .../actions` -> 202 + operation ref; `GET /v1/operations/{id}` (reuse `runs/` for the
   operation record rather than a new store).
3. Per-assistant OpenAPI from `describe()`.

Stage 2 (D4; its own commit):
4. Derived skill IO schemas from the wrapped agent/tool.
5. Typed signatures for the `as_tool` and `spec_ref` branches of `_build_parent_tools`; every
   skill then gets a route.

Deferred (D3): the process-start client.

Acceptance (the plan's): a frontend builds a screen from the generated docs alone; a malformed
body is refused before a model; adding a skill changes no code in `plato/`; an async action
reaches a terminal state. (Process-start acceptance waits with D3.)

## Split

All runtime session (Plato infra, chat lifecycle, agents/interactive, observability). Client
methods and contracts land with each route.
