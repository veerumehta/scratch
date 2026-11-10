# Plan: 2.6.9 scope (opus-xrepo, 2026-11-02)

Starts from `origin/plato` 433b89d2 (2.6.8 follow-up on the squash de4a8be8). Nothing here is started. Branch `v2.6.9` is cut only on the user's go; the
version bump (SDK 2.6.9; whether Plato and the client move is the user's call) is the branch's first commit, committed by sonnet-runtime after the user says
yes in that session. Order is by what blocks a consumer first, then by risk. The carried list from 2.6.7 (`plan_2_6_8_carried_from_2_6_7`, items 1 to 9)
is still the base; this plan adds what 2.6.8 produced.

## A. Gated platform bumps (runtime)

1. **`common` 0.2.0 to 0.3.0** (pin 25bf9d81 to 5fa47753 on common main). 46 commits, 67 files, +11,093 / -33, additive; the files japes imports are
   untouched except `core/db.py` (every session becomes `TenantAwareSession`), `utils/telemetry.py` and `core/log_settings.py` (span processor, log
   attributes, OTLP metrics opt-in). Gates: `tests/test_common_submodule_deps.py`, Plato boot-contract and schema-version tests, a full suite with
   `DB_TENANCY_MODE=off` and `IDENTITY_MODE=legacy`, a test that opens a session through the common backend and behaves as before with tenancy off, and a
   look at whether the tenancy session needs `PLATFORM_TENANT_ID` in Plato's environment. Compare against `origin/main`, never the local perf branch.
   Target CONFIRMED after a fetch (2026-11-03): common `origin/main` is 5fa47753, 0.3.0, tag `v0.3.0`. The 0.4.0 head 96b0495f the siblings pin is only
   on the unmerged branch `feat/BSD-5538-phase3-v0.4.0`; revisit when it merges and is tagged (its start-up refusal with `PLATFORM_TENANT_ID` unset
   needs a read against Plato's boot tests then).
2. **Local environment**: the venv is at the old pins; a `poetry install` is the user's. Not a task.

## B. CI and test health (runtime)

3. **Sharded CI check**: read the first PR run (both shards under 25 min, aggregator `pytest` green). Rebalance `scripts/shard_weights.json` from the CI
   durations if one shard is slow; the weights are local macOS timings. Drop the sharding if it gained little.
4. **Test speed**: `tests/test_concurrency.py` teardown waits (4 x 9.95 s), `tests/test_import_each_package.py` (46.6 s), `tests/test_chat_turn_store.py`
   close test (10 s). Expected saving about 1.5 to 2 of 13 minutes. Measure before changing; prove edits against a broken implementation.
5. **Flaky timing tests**: `tests/test_runs_slow_turn_not_reaped.py` lines 68 and 123 (50 ms TTL, 10 to 20 ms heartbeat, assert NOT reaped).
6. **CI Postgres service container**: six tests skip in CI for want of `JAPES_TEST_POSTGRES_URL` (key lock, advisory locks, row locks, pool leak).
7. **`scripts/check_new_models.py`**: cache the served ids and recompute against the current `model_data.json`, so adding a row clears the warning at once.
8. **Local pre-push tooling** (scripts/local, scratch repo): set the client's `PYTHONPATH` when the checkout is not the one the venv installs from; the shim
   line already prepends. Optional.

## C. Policy-to-jobs and Plato surfaces (runtime, ui, packs)

9. Carried items 1 to 9 from 2.6.7 as written there: provenance index and resolver, lint gates K3 K4 K7 K9 K10, the case and subject words, the coverage
   page's server-side filter, a per-link API field (only if the Solution page needs it), pack-provided helpers (a question, not a build), `latest` and
   `explains` helpers (rules library stays on 1.1.2 by the user's 2026-11-02 ruling), the TODO(slug) markers (92 slugs, 101 markers in the tree at
   2026-11-02), the cross-reference heading read as a topic.
10. **`single_case_dataset` and the corpus segmenter**; blocked on the user's answer whether extracted jobs carry guide topic ids.
11. **MACER steps 1 and 2** (metrics source): recommendation extract-then-compute; needs the user's decision and approval. The income-worksheet
    helpers landed in 2.6.8 (`edate`, `eomonth`, rounding, `total` and friends); the rest of macer's `feat/income-worksheet-formula-metrics`
    (`metric_kind` formula and choice in the job schema, entity-backed evaluation) is an SDK plan, not built.
12. **Workbench adoption**: ranks 7 to 9; `build_agent` replaces its OpenAI provider (steps 0 to 2 of the adoption plan), then a measured side-by-side
    against its Claude Agent SDK path. The six workbench questions and eight juno questions remain with the user.
13. **Model layer**: Anthropic and Gemini thinking fill beyond what 2.6.8 added; compaction and a session store for the SDK path are not built.
14. **`page-harness-shared`** test helper TODO and the Plato browser click-through (adoption, lint and profile editor, ontology Source panel,
    extraction budget, links list, tenant switch) that no round has done.
15. **`runs/schema.py` `TODO(turn-run-max-attempts-unset)`** retry branch.

## D. Jaci and other repos

16. jaci: re-lock (`openai`, `pydantic`, `pyasn1` moved), push `dev` (4 commits ahead of origin/dev 770ce78). sonnet-jaci.
17. Hub ontology answers (Pulte's ontology version, the 46 missing filter fields, `LoanCore.total_undisclosed_monthly_payment_usd`, the bare `Borrower`
    key, the 69 jobs without `loan_metrics`); Pulte income-type enum.

## E. Juno-driven SDK items (runtime; user decision 2026-11-03: juno accepts only what is on main, so these ship in 2.6.9)

18. **Installable by a poetry git consumer**: `jazzx-eval-contracts` and `jazzx-plato-client` are path dependencies (`pyproject.toml:101-102`), so a
    poetry git lock fails. Git subdirectory dependencies or optional extras (the user chose subdirectory deps earlier, deferred); Plato's Dockerfile and
    `import-boundaries.yml` change with it. Juno can pin the main commit meanwhile (no `v2.6.x` tag exists; the user creates tags).
19. **Kernel strict-posture guard**: `client_layer.py:221-226` falls back to `MockKernelClient` silently where Knowledge Hub raises under `strict_mode()`;
    give Kernel the same guard.
20. **Knowledge Hub 5xx and timeouts**: verify what the client does today (juno's doc says `[]`); if so, an opt-in strict flag that raises, default unchanged.
21. **Optional**: a hub read-by-id that answers `None`, so a host can drop its `get_document` special case (`fabric.docs.get` raises on a missing document).
    Not ours: the release tag (user), `ChatCoordinator` writing to a host's own run tables (juno's trial decides).

## Decisions needed from the user before work starts

- Which of A to D go into 2.6.9 and in what order (A1 and B are small and independent; C is the large part).
- Cut `v2.6.9` from origin/plato now? Version scheme for Plato and the client.
- C10, C11, C12 each need a user answer first (see above).
- Anything needing a provider call waits for the user's typed approval of a figure.
