# Plan: v2.6.1

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: branch `v2.6.1` cut 2026-10-03 from `dev` at `b316b5d3` (PR #88's squash of 2.6.0, `ec16ee93`,
plus the record of `main`'s `ae974845`). Version numbers not bumped: SDK 2.6.0, Plato 0.2.0, client
0.2.0 until the user says so. Carried in: `cd053934` (feedback export window docstring).

## Flow

`v2.6.1` -> `plato` -> `dev` -> `main`. After every squash PR lands, record it back on the branch it
came from with a tree-preserving merge (`git commit-tree <src>^{tree} -p <src> -p <squash>`):
`plato` after a `plato`->`dev` squash, `dev` after a `dev`->`main` squash. Before any PR, check the
head contains the base (`git merge-base --is-ancestor origin/<base> <head>`). Run the full-range
review (`REVIEW_UPSTREAM=origin/dev`) before opening the PR, not only incremental rounds.

## Decisions wanted

| # | Question | Recommendation |
|---|---|---|
| D1 | fastapi/starlette out of core dependencies (A1) | **Yes (2026-10-03).** Breaking for a consumer relying on japes for fastapi; juno, macer, jazzx-assistant declare their own. |
| D2 | anthropic lock 0.111 -> 1.x (A2) | **Yes (2026-10-03)**, with the live smoke; jaci is pinned `<1.0` and is no constraint. |
| D3 | Which deferred TODO groups (D) are in scope | **Concurrency and safety (2026-10-03)**; leave the rest. |
| D4 | Policy-owned items (F) | The policy session's call; listed so nothing is lost. |

## A. Dependencies

1. **fastapi and starlette into extras** (`server`, `plato`). Since `common` `0cc5712` (#229), no
   `common` module japes reaches imports fastapi, and neither does the SDK core (`jazzx_sdk`,
   `agents.interactive`, `pipelines.chat`, `pack`, `fabric.db`, `runs`, `config`, `observability`,
   `conductor`, each checked in a fresh interpreter). Module-scope importers: `server/` (10 files)
   and `config/posture.py` (not loaded by `config`). Work: move the two declarations; make
   `posture.py` import fastapi lazily or move it under `server`; a guard test that the core imports
   load no `fastapi` (pattern: `test_no_backend_on_the_eager_path`); rewrite the stale
   `pyproject.toml` comment on `opentelemetry-instrumentation-fastapi` (it cites an unguarded
   `common` import that is gone) or drop that extra if nothing ships the instrumentor.
   Consumers checked 2026-10-03: juno declares fastapi/starlette/uvicorn itself (19 importing
   files); macer imports it only in `mock_knowledge_hub` (dev extra; its container installs it);
   jazzx-assistant declares it.
2. **anthropic 1.x lock bump + gated live smoke.** Code is 1.x-compatible since 2.5.8.
3. **`TODO(kh-client-bump)`**: KH client pin (`pyproject.toml`), and with it KH's rego removal.
   Check what moved in `client-api` first.

## B. 2.6.0 review leftovers (low)

1. `facts-recursive-ref-unrefused`: `schema_facts`/`fact_type` follow a ref-only cycle to
   `RecursionError`; give `fact_type` the in-progress set `_unbounded` uses.
2. `spec-ref-ignored-list-incomplete`: `Skill.spec_ref`'s comment; state what a composed skill
   honours (`inputs`, `description`, timeouts) instead of listing what it ignores.
3. `TODO(bare-tool-route-requires-defaults)`: route body from the tool's non-strict schema, or drop
   defaulted parameters from `required`.
4. `TODO(inline-schema-refs-unresolved)`: lift `$defs` into OpenAPI `components`.

## C. Phase 3/4 leftovers (`plan_plato_phases_3_4.md`)

1. A live parent-model call carrying structured args to a typed skill (stage 2's acceptance names
   it; only the tool boundary is tested).
2. `GET {prefix}/decisions/{id}` (Phase 4 left it out).
3. Process-start stays deferred (that plan's D3).

## D. Deferred runtime TODOs (by group)

- **Concurrency:** `activation-merge-lost-update`, `draft-merge-lost-update`,
  `supersede-check-outside-admit-lock`, `concurrent-close-writes-twice`, `publish-tick-tie`.
- **Safety:** `dns-rebinding`, `is-private-ip-v4-only`, `allow-hosts-port`, `path-userinfo-last-at`,
  `jwks-discovery`, `jwks-error-detail`, `frozen-settings`.
- **Plato wiring/migrations:** `azure-blob-container-singleton`, `bound-missing-config`,
  `partial-registration-marker`, `switched-store-not-backfilled`, `migration-concurrent-index`,
  `migration-target-not-enforced`, `migration-engine-ignores-test-dsn`.
- **Other:** streamed agentic usage, scripted sessions per replica, executor Linux layers
  (`/tmp/japes_executor_linux_check.sh`), `export-window-not-insert-stable`.

## E. Test hygiene

1. Run the suite with no provider keys before a PR (CI has none; three tests reached a real
   provider in 2.6.0 and failed only there). Candidate: a pre-PR step that unsets
   `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`/`AZURE_OPENAI_API_KEY`.
2. `_skilled_deployment` builds a real OpenAI provider; give the stubbed tests an agents service
   that never constructs one, then drop the placeholder key.

## F. Policy session (listed, not owned here)

`python-rules-assessed-twice`, `python-percent-unguarded`, `reasoned-assess-runs-twice`,
`case-run-assess-unreasoned`, `activation-vs-active-rules`, `rule-reads-not-json-coerced`,
`threshold-grid-provenance`, `composite-live-child-unflagged`, `locator-printed-ref`,
`documents-converted-twice`, the `ci-*` seed TODOs, `seed-digest-drift`, `seed-pack-vendoring`.
Awaiting the user: `missing_inputs: default` for assess, the `dscr_core` seed refresh, jaci's
later batches, eval step 7, Acra 4.9 and caps.
