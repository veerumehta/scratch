# Integration checklist: starting a process (for the pack author)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Date: 2026-11-07. Replaces the 13 questions drafted for the Macer team, which are not sent and are not blockers: the SDK forwards a variables map and names no process variable, so each item below is something the pack author settles and writes into `profile/processes.yaml`, or checks on a dev engine. Questions the decision made moot are listed last.

For the field meanings see `docs/PROCESSES.md`; a worked example is `plato/data/sample_packs/pulte-home-mortgage-macer`.

## Settle and write into the spec

1. **Start variables.** Which are required and which have defaults; the minimal valid start for one case. Map the conversation values with `variables`, and write constants with `fixed`. The sample sets only what the QA suite showed (`loan_collection_id`, `operation`, `timeout_duration`); the ontology ids, guidelines collection, `jtbd_entity` and `config` object are per environment, so add them as `fixed` values or as more `variables` entries.
2. **Idempotency key.** What must not overlap (for Macer, a loan collection id: the process takes a per-loan collection lock). Write it as `idempotency: "{...}"`. The Flowable backend sends it as the business key and finds a live process by it; if the process holds its key in a variable instead, say so and the backend needs a variable search.
3. **Start call shape.** `runtime` (raw Flowable) or `process_start_api` (`{processType, processDefinitionKey, payload}` with a token). For the second: the `processType`, how the token is issued, and where the business key goes in the body (the backend sends a top-level `businessKey`, which is a guess to confirm).
4. **Cost note.** Free text shown before a start; a figure only if known. The sample states no figure.
5. **Outcome variables.** The variables a finished process sets that a user should see; list them in `outcome`. Empty shows whatever the engine reports.
6. **Failure shape.** How a failed run ends in the engine (an error end, or a normal end with a failure variable). The backend reads a deleted or cancelled instance as failed; a normal end with a failure variable reads as completed, with the variable in `outcome`.
7. **Waits inside the process.** Message names a person or system must answer; the Flowable backend can deliver a message to a waiting execution (`signal`).

## Check on a dev engine before relying on it

- A start with the minimal variables returns an instance id; a second start with the same key returns that instance (`already_running`).
- `status` shows running, then completed with the variables listed in `outcome`.
- A cancel ends the instance and releases the key.
- The tenant, identity and trace headers arrive on the engine's side.

## Resume of a waiting pipeline (S6)

The default is polling the process status; no change to the process is needed. A callback from the process to `POST /api/v1/runs/process-callback` is an optional faster path, with its own service token and scope. Neither is built yet; see the plan's status section.

## Moot after the decision

Whether Macer must add a callback service task (it need not); the polling interval to agree with them (a host setting); the per-environment variable list as a Macer deliverable (the pack author owns it); a cost figure as a blocker (a note, not a number).
