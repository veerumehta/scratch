# plan_JAPES_PROCESS_ENGINE_START_AND_SIGNAL

Author: Virendra Mehta · 2026-11-07 · Status: done in the SDK (S1 to S7), revised 2026-11-07 (generic launcher)

## Status and modifications

How to use this section: the plan author may read it and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-07: not started. Decision: in 2.7.0, owned by `sonnet-runtime` after its queue (R4, R6, then the policy composites). An idle session may take slices S1 to S3 by assignment from `opus-xrepo`; S6 and S7 touch Plato routes and the client and stay with `sonnet-runtime`.
- 2026-11-07 modification: nothing in the code is specific to one process. A named process is pack configuration (`ProcessSpec`), so a Macer review, a document-processing run or any pipeline is launched the same way.
- 2026-11-07 modification: the calls sit behind a small `ProcessLauncher` protocol with two backends now (Flowable, conductor) and a shape that a Temporal backend could implement later. Temporal is not built.
- 2026-11-07 modification: the idempotency identity is a key the spec supplies, not a Flowable business key. For Macer it is the loan collection id (macer takes a per-loan collection lock, so two runs on one loan must not overlap).
- 2026-11-07 modification: Flowable has two start shapes. Raw Flowable takes `variables: [{name, value}]` at `/flowable/process-api/runtime/process-instances`. The Jaxi process-start API takes `{processType, processDefinitionKey, payload: {...}}` at `/flowable/api/process/start` and needs an auth token. Both are chosen by configuration, never by environment name.
- 2026-11-07 open: the scope check. A scope per process key does not fit `scope_claims.py` well (a host declares each claim by name; a message carries at most 16). Settled in S4: a `process:<name>` selector axis (see the S4 line).
- 2026-11-07 open: outcome variables and the callback depend on the Macer team (see Inputs needed).
- 2026-11-07 S1 done (0d47c64a): `jazzx_sdk/processes/` with the protocol, `ProcessSpec`, a freezable registry and the shared contract test class (`tests/process_launcher_contract.py`) with a fake backend. Choice: the idempotency template and start-variable mapping live on the spec (`idempotency_key`, `start_variables`); the pack-load hook is `registry.validate(specs)`, called by S4 where packs bind specs. S2 and S3 next.
- 2026-11-07 S2 done (f16c2153), S3 done (af50f0a2). Plan deviations: (a) the conductor `ref` is a pack id and start is a case run through `CaseRunService` (no suspension-store lookup exists by run, and a run's checkpoint is answered through the run service), (b) a conductor signal answers a human checkpoint, so it needs a named approver (identity) and a `CheckpointResolution`; with none it is refused, so a bot cannot approve, (c) Flowable idempotency queries `runtime/process-instances` by business key and process key on the injected client rather than `search_process_instances`, (d) the key is stored as the Flowable business key in both start shapes, and for `process_start_api` its placement is a guess (top-level `businessKey`) to confirm with the Process Engine team, (e) a conductor cancel is cooperative (the run stops at its next step), so the contract has an optional `after_cancel` hook, (f) conductor idempotency is look-then-submit, not atomic. S4 next; it settles the scope-claim design.
- 2026-11-07 S4 done (8a58c92e). Plan corrections: (a) the confirmation is the interactive agent's approval card (`require_approval`), not the chat pipeline's gate step, which is a routing classifier; where no turn desk exists a start that needs confirming is refused, (b) the open scope-claim question is settled without scope claims: claims are forwarded headers, so permission is a new `process:<name>` selector axis on the existing `PermissionScope` (`ProcessSpec.scope` is unused and can be dropped), (c) tools are catalog tools named by spec name, bound as bare skill names the way `authoring_tools` is. Left for S5: a pack file that declares specs and the audit sink wired to the governed record.
- 2026-11-07 S7 done (a9ae3382). Plan deviations: (a) the SAIG path is dedicated routes (`/processes`), not `invoke_skill`: the skill invoke route runs a model turn with no way to carry an approval, so a programmatic start would be nondeterministic and could never confirm; the caller's `confirm: true` is the acknowledgement, (b) assistants on Plato use the S4 tools by a host passing `process_tools(...)` as agent `tools` and listing the names as skills, with no Plato code, (c) the router is not mounted in `create_plato_app`: it needs `specs_for(tenant)`, which is the pack declaration still to build in S5. Left: S5 (pack file for specs, Macer and document specs, audit sink to the governed record, app mount) and S6 (needs the Macer callback).
- 2026-11-07 S5 done in part (ff90d06a). Built: the pack declaration (`profile/processes.yaml`, direct-tool skills generated from it, bound by `build_from_manifest` from a host's `process_launchers`), the runtime's per-tenant specs, the app mount, the pack check binding with `UnwiredLaunchers`, and a Macer review sample pack. Deviations: (a) the Macer spec is a new sample pack, not an edit of the Home Mortgage intake pack, so a host with no process engine can still publish the intake pack, (b) only the start variables read from the Macer suite are set (`loan_collection_id`, `operation`, `timeout_duration`); the rest wait for the Macer team, (c) no document-processing spec ships, since no shipped pack is one, (d) an unregistered backend fails at bind, not at pack load, because backends are host wiring; the pack check does not know them. Left: the Macer team's variables, a real deployment's launcher wiring, and the dev-environment run of the acceptance. S6 needs the Macer callback.
- 2026-11-07 decision (user, relayed by `opus-xrepo`): S5 closes as configuration only (start variables, cost note and key are `ProcessSpec` fields the pack or caller supplies; the SDK forwards a variables map and names no process variable); S6 ships with the polling sweep as the default resume path and the callback endpoint optional, needing no change in the process; `status` returns what the engine exposes in `outcome` and `detail`, and a spec may list `outcome` variables to show; the Macer questions become an integration checklist (`docs/status/note_process_integration_checklist.md`), not blockers, and are not sent. Done for it (cea08eae): `ProcessSpec.outcome`, applied in the tools and the routes, and `docs/PROCESSES.md`; the sample pack and its README line already exist. S5 is closed. Still SDK work: S6 (below).
- 2026-11-07 S6 done (ce61227f, docs 5 commits later). User decision: the sweep resumes as a named service actor (`process-wait-sweep`, actor type `service`), not a person. Built: the `process` step kind (`spec` inline in the step, `wait`), `resume_process_case`, `CaseRunService.resume_finished_processes` and `resume_waiting_instance`, the sweep in `job:run-reaper`, and the optional `POST /runs/process-callback` (scope `process:callback`, backend asked, no outcome in the body). Deviations: (a) the spec lives in the step, not looked up by name, because a domain pack has no access to the assistant's specs, (b) a person's checkpoint resume of a process-waiting run is refused, (c) a process the backend cleanly answers it does not know resumes its run as `not_found` (user decision), while an unreachable backend leaves it waiting. The plan is complete; Macer variables are the pack author's checklist.

## Goal

Let a chat assistant, or any pipeline step, start a long-running process and follow it to completion, whatever runs it: a Process Engine (Flowable) process, one of our own conductor pipelines, or later another engine. The first use is starting a Macer review from chat ("run the Macer review on loan 1234") and reporting its status and outcome. The same path then serves document processing and any other invokable work, from Plato for any assistant and for SAIG companies through plato-client.

## Where things stand

`jazzx_sdk/tools/platform/workflow.py` reads from the Process Engine only:

- `fetch_process_definition(process_key)`
- `fetch_process_xml(process_key)`
- `fetch_process_variables(process_instance_id)`
- `search_process_instances(process_key, business_key, variable_name, variable_value, finished, limit)`

Each opens its own `httpx.AsyncClient`, reads `JAPES_PROCESS_ENGINE_BASE_URL` / `PROCESS_ENGINE_BASE_URL` through `get_flowable_base_url()`, sends no identity or tenant headers, and returns a dict with `found` and `error` rather than raising.

Nothing starts a process, sends it a message, or waits for it. No launcher abstraction exists. The conductor already has durable pauses (`conductor/suspension_store.py`: `SuspensionStore` protocol, `DurableSuspension`; `conductor/suspension_store_db.py`: claim, heartbeat, `mark_resumed`, `reap_stale`), which the conductor backend and S6 reuse.

## Facts read from the macer repository (2026-11-07, `macer/e2e/qa_automation_suite`)

- Process key `macerMasterProcess`, set per environment in `test_data/envs/<env>.json` (`process_keys`); it is a configured value, not built per run.
- Start variables seen in the QA payloads: `loan_collection_id`, `operation` (`jtbd_agent`), `findings_ontology`, `mortgage_ontology`, `docs_ontology`, `jtbd_entity`, `guidelines_collection_id`, `timeout_duration` (`PT2H`), `force_full_run`, `include_previous_context`, and a `config` object (model name, reasoning effort, verbosity, max turns, max session size).
- The start response carries a process instance id; the trace id is `trace-{process_instance_id}`.
- A run costs real model spend (the suite keeps a session budget), so a confirmation should show a cost note.
- Not found there: a business key, process variables that carry outcomes (the suite reads results from MLflow, traces and the Knowledge Hub), or a callback service task.

## Before starting

Verify in this order: the latest CHANGELOG entries, this plan, then the source. Confirm that `workflow.py` still has only the read functions above and that nothing added a start call since 2026-11-07. Check how the interactive agent binds pack and spec tools today (`jazzx_sdk/agents/interactive/`) and follow that pattern in S4; do not invent a second registration path. Grep `jazzx_sdk/__init__.py` and the package exports before adding the new module.

## Design

New module `jazzx_sdk/processes/`.

- `ProcessLauncher` (Protocol), async, no raises for expected outcomes:
  - `start(ref, variables, *, idempotency_key, caller) -> StartResult` (`started`, `instance_id`, `already_running`, `error`).
  - `status(instance_id) -> ProcessStatus` (`found`, `state`, `started_at`, `ended_at`, `current_activities`, `outcome`, `detail`).
  - `signal(instance_id, name, variables=None) -> SignalResult` (`delivered`, `error`): a message event, a resume, or a Temporal signal.
  - `cancel(instance_id) -> CancelResult`.
- `ProcessState`: `running`, `completed`, `failed`, `suspended`, `not_found`. Backend-specific detail goes in the opaque `detail` mapping, never into the shared states.
- `ProcessSpec` (declared by a pack): `name`, `backend`, `ref` (the backend's own identifier: a process key or a pipeline id), `variables` (how conversation or case values map to start variables), `idempotency` (the variable or template that forms the key), `scope`, `confirm` (default true), `cost_note`, `wait` (default false).
- A registry maps a backend name to a launcher; a spec naming an unregistered backend fails at pack load, not at call time. No ref is callable unless a pack lists it.

## Inputs needed from the Macer team (the Macer entry and S6 only)

- Whether the process sets outcome variables a status call can read, and which.
- Whether they will add a final service task that calls the Plato callback endpoint (S6).
- Confirmation of the start variables above for each environment, and which are required.

S1 to S4 do not wait on these; test against a sample process deployed to a dev Process Engine and against a fake pipeline.

## Slices

### S1. Launcher protocol, spec and registry
- `jazzx_sdk/processes/` with the types above, a registry, and a shared contract test class that every backend must pass.
- Intent: one place for what "launch a process" means, with no engine named in it.
- Acceptance: a fake backend passes the contract tests (start, already running, status per state, signal delivered, signal with nothing waiting, cancel); a spec naming an unknown backend fails at load.

### S2. Flowable backend
- One module-level helper in `workflow.py` builds the HTTP client and applies `install_request_headers_hook` from `jazzx_sdk/clients/_header_hooks.py`, so identity, tenant and trace headers reach the Process Engine; move the existing read functions onto it. Their dict return style stays so current callers are unaffected.
- Start shape and endpoint come from configuration (`runtime` or `process_start_api`, base URL and path), with the token supplied through the existing client auth. Idempotent: before starting, `search_process_instances(business_key=<idempotency key>, finished=False)`; if one runs, return it with `already_running`.
- `signal` finds the execution waiting on the message (`GET .../runtime/executions?processInstanceId=...&messageEventSubscriptionName=...`) and sends `PUT .../executions/{id}` with `action: messageEventReceived`. `status` maps the runtime and history APIs to `ProcessState`.
- Acceptance: mocked-transport tests for both start shapes, already running, message delivered and no waiting execution, status running and completed, and headers on every request; the contract tests pass.

### S3. Conductor backend
- `ref` is a registered pipeline id; `start` runs it through the existing run machinery (no new run store), `status` reads the run record and the suspension store, `signal` claims the suspension and calls `mark_resumed` with the variables as the resolution. Nothing is added to the conductor itself.
- Intent: our own multi-step pipelines (document processing, policy extraction, case pipelines) start from chat or another step by the same call as an external process.
- Acceptance: a fake pipeline with a review step is started, reports `suspended`, resumes on `signal`, and reports `completed` with its outcome; the contract tests pass.

### S4. Process skills for assistants
- Two generic skills wrap the launcher, named by the pack for each spec (for example `start_review`, `review_status`). Bind them the way the interactive agent binds pack and spec tools today.
- Confirmation: start skills ask the user to confirm (showing the spec's cost note) through the chat pipeline's existing gate step; status skills need none.
- Permissions: check the caller's scope claims (`jazzx_sdk/scope_claims.py`) before starting; deny with a clear refusal, not an error. Settle the claim design (see open items).
- Audit: record each start (backend, ref, idempotency key, instance id, caller, whether already running) on the run's trace and in the governed record.
- Acceptance: an Underwriter-assistant test pack lists one sample process; "start the review for loan 1234" asks to confirm, starts once, and a second identical turn reports the running instance. A caller without the scope gets a refusal. The same skills run a conductor-backend spec with no code change.

### S5. Macer and document processing as configuration
- Add the Macer spec to the Home Mortgage assistant pack: `backend: flowable`, `ref: macerMasterProcess`, the start variables mapped from the case, the idempotency key from the loan collection id, a cost note. Add one document-processing spec on the conductor backend to show the same skills launch it. No code change in the SDK.
- The reply after starting gives the instance id and says the process is running; `review_status` reports running, completed (with the outcome variables the process sets) or failed.
- Acceptance: on a dev environment with Macer deployed, starting from chat creates one Macer process for the loan and the status skill reports completion and outcome; the document spec runs end to end on a fake model.

### S6. Pause and resume on completion
- A pipeline step that starts a process can choose `wait: true`: it starts the process, creates a `DurableSuspension` keyed by backend and instance id, and suspends the run.
- A Plato resume endpoint, `POST /runs/process-callback` in `plato/api/runs.py`, takes `{backend, instance_id, outcome_variables}`, finds the suspension, claims it, calls `mark_resumed` with the variables as the resolution, and resumes the run. It accepts only callers with a `process:callback` scope and is idempotent. The conductor backend resumes internally and does not use the endpoint.
- Fallback for processes without a callback: a sweep that checks `status` for suspended runs waiting on a process and resumes them on completion. Reuse `reap_stale` timing settings; do not add a scheduler.
- Acceptance: a case pipeline with a `wait: true` step suspends after starting the sample process, resumes when the callback arrives, and records the outcome; the sweep resumes a run whose process has no callback.

### S7. Through Plato and plato-client
- Expose the S4 skills through Plato's skill API so any assistant on Plato can use them by pack configuration.
- Add `start_process` and `process_status` to `jazzx-plato-client` beside `invoke_skill`, calling the same Plato endpoints, so a SAIG company can trigger the processes its tenant allows without the SDK.
- Acceptance: a plato-client call starts the sample process for a tenant whose pack allows it and is refused for a tenant whose pack does not.

## Order

S1, then S2 and S3 (independent, either order), then S4, then S5 and S7, then S6 once the Macer team agrees to the callback step.

## Done when

A user can ask the Home Mortgage assistant to run the Macer review on a loan, confirm, and later ask for and receive its outcome; the same skills start a document-processing pipeline; a case pipeline can wait on a process and resume with its result; and the same calls work through Plato and plato-client under each tenant's pack permissions. Nothing in the SDK names Macer.
