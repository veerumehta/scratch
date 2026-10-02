# Plato service Phases 3 and 4: generated skill routes, process-start, trace of record

Live plan, runtime session. Source of scope: `plans/Plato/plan_JAPES_PLATO_SERVICE.md` §Phase 3,
§Phase 4. Written 2026-10-02 from the v2.6.0 tree; start a fresh session from this file.

## Gates (decide before building)

| # | Decision | Gates | Recommendation |
|---|---|---|---|
| UAF-9 | Trace format of record | Phase 4 | `CanonicalTrace` (the companion doc's recommendation). Release and skill versions ride `VersionBundle.extra` and `CanonicalTrace.metadata` (Spec-v1.5 frozen `trace.py`). |
| D4 | Per-skill IO on the execution path | Phase 3 tasks 1-3, 5 | Derive `Skill.inputs`/`outputs` JSON Schema from the wrapped agent/tool; give the `as_tool` and `spec_ref` branches of `_build_parent_tools` typed signatures. The deepest change (every assistant's tool path): its own commit, full suite plus dependent packs. |
| D3 | Who owns process-start (`runtime/process-instances`) | Phase 3 task 6 | Plato, as a credentialed outbound client; needs the BPMN runtime's URL, auth and a test instance. Without those, defer task 6. |

## Order

Phase 4 first: it is M, its gate has a recommendation, and it closes `TODO(stream-release-id)`
(`plato/api/assistants.py`).

### Phase 4 — trace of record (M)

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

### Phase 3 — generated skill routes, async operations, OpenAPI, process-start (L)

1. Derived skill IO schemas (D4).
2. Typed signatures in `_build_parent_tools` (D4; own commit).
3. `POST /v1/assistants/{id}/skills/{skill}/invoke` per skill from the resolved release, on
   `GovernedRouter`, body validated against the input schema, honouring `Skill.visibility`.
4. `POST .../actions` -> 202 + operation ref; `GET /v1/operations/{id}` (reuse `runs/` for the
   operation record rather than a new store).
5. Per-assistant OpenAPI from `describe()`.
6. Process-start client (D3).

Acceptance (the plan's): a frontend builds a screen from the generated docs alone; a malformed
body is refused before a model; adding a skill changes no code in `plato/`; an async action
reaches a terminal state; a process instance starts and its completion is observed.

## Split

All runtime session (Plato infra, chat lifecycle, agents/interactive, observability). Client
methods and contracts land with each route.
