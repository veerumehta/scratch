# Layering audit of what 2.7.3 added under plato/

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Audit of 2026-11-17, read-only, decides nothing, moves nothing. Rule: logic lives in `jazzx_sdk`; `plato/` is the hosted shell (routes, page wiring, boot, job entry points, seed and demo data); `jazzx_sdk` never imports `plato`. Range: 870cb2f4..c2797d3e (+3113 / -76 lines under `plato/`, of which 730 are the recorded demo proposals and about 600 are static pages and demo manifests). 2.7.4 added one Plato line (the version). Test per item: would a second host need the same behavior, and does it touch HTTP types?

## Verdicts

| Where | What it is | Verdict |
|---|---|---|
| `plato/api/figures.py` `_version` (closure, 22 lines) | Materialize a published pack version, find the manifest-declared figures file (or `figures.yaml`), refuse a path outside the pack, read figures and policy rules. Only the 404/409 mapping is HTTP. | **Move.** `read_version_figures(store, pack_id, version) -> (figures, rules)` beside `read_draft_figures` in `jazzx_sdk/pack/figures.py`, raising `KeyError`/`ValueError`; Plato maps them to 404/422. Any host that publishes packs and reads their figures needs it. |
| `plato/api/guidance.py` `guidance_evidence` (handler, about 40 lines) and `_newest_published` | Builds what a reviewer weighs a draft against: for each signal of the asset, the feedback record's review status and each correction's rule, given and expected verdict; plus the uplift baseline of the newest published version. The loop over `signals_of` and `feedback.get` has no HTTP in it. | **Move the evidence builder** (`guidance_evidence(asset, feedback, uplift) -> dict`, next to `fabric/guidance/loop.py`), keep the route (posture check, tenant, 404) in Plato. `_newest_published` is a two-line use of `published_newest_first`: keep. |
| `plato/jobs.py` `sweep_guidance_drafts` (24 lines) | Loop over tenants with one shared spend budget, calling the SDK's `sweep_guidance` per tenant, continuing past a failure. | **Move the loop** (`sweep_guidance_tenants(...)` in `jazzx_sdk/pack/guidance_sweep.py`); keep the job role `job:guidance-sweep`, its env variable and the exit codes in Plato (entry point). |
| `plato/boot/wake.py` `listening(stores)` (19 lines) | Start the wake of each store that has one under a timeout, stop those that started on exit. No HTTP. | **Move** next to `PgWake` in `jazzx_sdk/runs/wakeup.py`; a second host with a run store and followers needs the same block. Plato's boot keeps the call. |
| `plato/api/demos.py` replay handler (about 15 lines inside the route) | Read the recorded proposals file, validate each, file only the ones not yet in the store as one proposal set. | **Move the filing** (`file_recorded_proposals(store, pack_id, run_id, proposals)`), keep the route and the manifest lookup. Small; take it only with the next change here. |
| `plato/api/model_overlay.py` `overlay_lifespan` (28 lines; added in 2.5.3, not 2.7.3) | Apply the durable overlays at startup, then keep applying them (`OverlayRefresher`); cancel and await on exit. Only the tenant binding (`DEFAULT_TENANT`) is Plato's. | **Move** to `jazzx_sdk/llm/model_overlay_db.py` taking the tenant; any host that mounts the overlay table needs the same startup and loop. |
| `plato/api/model_overlay.py` bulk, history, compare, pricing handlers | HTTP wrappers: payload checks, posture (`withheld`), `HTTPException` mapping. The logic they call (`check_overlay_rows`, `put_many`, `apply_overlays`, `compare_overlays`, `pricing_table`, `is_shipped`) is already in `jazzx_sdk.llm.model_overlay_db`. | **Keep.** |
| `plato/demos.py` (manifest loader, `validate_demo`, placeholders, nav pages) and `plato/api/demos.py` `usable_demos`, `_status`, `prepare` | Plato's pages, seed set and `plato/data/demos`; the checks are against Plato's own pages and seed packs. | **Keep.** |
| `plato/wiring/contract.py` `checked_local_executor(...)` | One call to the SDK's executor with Plato's two messages. | **Keep** (wiring). |
| `plato/api/figures.py` `_compared`, `_tenant`, `_unreadable` | A 422 check, two calls into the SDK, an exception mapping. | **Keep.** |
| `plato/jobs.py` other jobs (`run_job` 71 lines, `sweep_process_waits` 29, `prune_draft_history` 23, `sweep_sessions` 17, `process_feedback` 14, `sweep_runs` 13, `reclaim_eval_work` 6) | Existing before 2.7.3. Read only for size; not audited for body versus call. | Not judged. |

## What the check sees

`scripts/local/check_plato_layering.py` (warn-only step 2g of the push check) on 870cb2f4..c2797d3e lists five functions of 15 or more lines that name no HTTP type: `validate_demo` (keep), `sweep_guidance_drafts` (move), `usable_demos` (keep), `listening` (move), `create_demos_router._status` (keep). It does not see `_version` (it raises `HTTPException`), `guidance_evidence` and the replay filing (they sit inside route handlers), or `overlay_lifespan` (older than the range). So the scan finds the standalone helpers; the logic that rides inside a handler is left to the reviewer prompt line (a [SYMMETRY] finding for non-hosting logic added under `plato/`), which is why that line exists as well. Size limit: 15 lines, a named constant.

## Cost if taken

Five small moves (about 120 lines in total, each with its tests moving with it): `read_version_figures`, the evidence builder, `sweep_guidance_tenants`, `listening`, `overlay_lifespan` (plus the replay filing if wanted). None changes behavior; each leaves a one-line call in Plato. Order by value: `read_version_figures` and `listening` first (two hosts could already use them), then the evidence builder, the sweep loop and the lifespan.
