# Plan: 2.6.9 (opus-xrepo, 2026-11-02)

Working branch `v2.6.9` (SDK 2.6.9; Plato and client version follow the user's call at the first commit), cut from the v2.6.8 tip after the squash lands. Nothing here is
started. Items 1 to 9 of `plan_2_6_8_carried_from_2_6_7` carry over unchanged (that file stays the detail for them); this plan adds the items raised since and sets order
and owners. Order is by what blocks a consumer or the release first.

## Gates (not built, decided by the user)

- **Common submodule 0.3.0.** Bump `common` from 25bf9d81 (0.2.0) to 0.4.0 (96b0495f, what the siblings pinned 2026-11-03; the earlier 0.3.0 target 5fa47753 is superseded): multi-tenancy foundations, default-off, but `core/db.py` gives every session
  `TenantAwareSession` and telemetry adds a span processor. Gate: `tests/test_common_submodule_deps.py`, the Plato boot-contract tests, and a full suite with tenancy off.
  Owner: sonnet-runtime.
- **Provider runs.** The classifier measurement of the two new Acra document types and the writer-prompt before/after run (about 0.13 USD) each wait for a typed approval
  with a figure. Nothing is spent by this plan.
- **Release flow.** The plato PR to dev, the tree-neutral records on plato and v2.6.9, and every push stay with the user.

## Carried from 2.6.7 (see `plan_2_6_8_carried_from_2_6_7`)

1. Provenance index and resolver. Owner: sonnet-runtime.
2. Job lint gates K3, K4, K7, K9, K10 (K8, K11, P1 measure-first; K1, K2, K5, K6 only if a real set shows them). Owner: sonnet-runtime.
3. Case and subject words beyond the metrics key (`loan:<id>` IRI prefix, `loan_number` kind, rag collection name). Owner: sonnet-runtime.
4. Server-side coverage filter. Owner: sonnet-ui with sonnet-runtime for the route.
5. Per-link API field, only if the Solution page needs it. Owner: sonnet-ui.
6. Pack-provided helpers: a question for the user, not a build.
7. Rules-library `latest(rows, stamp, order=None, ties=False)` and `explains(text, name=None, amount=None, on=None, large=None)`, one commit each with a test that
   fails without it, manifest 1.1.2 regenerated. Version: the library keeps growing on 1.1.2 while nothing uses it (user ruling 2026-11-02); bump to 1.1.3 only if the
   user decides one is needed. Both must pass the extreme-input probe (huge, NaN/sNaN, infinity, bool, mixed, long lists) before commit. Owner: sonnet-packs.
8. Review notes and `TODO(slug)` markers, including `runs/schema.py` (`max_attempts` retry branch). Read at the start of the round.
9. Cross-reference heading read as a topic in `markdown_guide.py`. Changes unit ids; state the effect on the Pulte pack and tell jaci to regenerate.

## Added since

10. **Markdown-guide cross-reference fold**: item 9 is built (76bf9c98 on v2.6.8; the Pulte topic index is already regenerated at 388 units in jaci cdfb516). Left: the
    `TODO(cross-reference-vs-repeated-id)` in `markdown_guide.py` (a genuine repeat of an id that another topic cites is folded); decide whether to keep it. jaci re-runs
    its index script only if unit ids change again.
11. **Test speed.** `test_concurrency` teardown waits 4 x 9.95 s, `test_import_each_package` 46.6 s, `test_chat_turn_store` 10 s. Fix the waits at the cause (a
    signalled shutdown, not a shorter sleep). Also the two 50 ms-TTL heartbeat tests, which are timing-sensitive. Owner: sonnet-runtime.
12. **CI Postgres service container**, so the 6 tests that skip without `JAPES_TEST_POSTGRES_URL` run in CI. Check the shard split afterwards; sharding stays the user's
    experiment (drop 90eb9cac's shape if it gains little).
13. **`check_new_models` cache** stores served ids, not requested ones (a stale "untracked model" warning for gpt-6.1-terra). Owner: sonnet-runtime.
14. **Thinking fill** for the Anthropic and Gemini models (OpenAI-shaped thinking landed in 2.6.8; live smoke passed 2026-11-02). Needs the LLM contract test plus a live
    smoke at a stated figure, per the standing rule.
15. **MACER steps** from `macer-japes-consolidation-roadmap` (deprioritized; take only what a consumer asks for). Open question first: the MACER metrics source.
16. **Workbench ranks 7 to 9** from `note_workbench_to_sdk_enhancements`: rank 7 (set reconcile and value equivalence) when a consumer asks; rank 8 (behind-latest pin
    report) is small and independent; rank 9 (within-job repeat detection) is measure-first, run on the Pulte and Acra sets before any gate, warning only. Also
    `single_case_dataset` with the corpus segmenter, deferred until the workbench commits to the SDK runner (sonnet-packs agrees). Open question for the user: must
    extracted jobs carry guide topic ids. No provider run needed.
17. **`page-harness-shared` TODO**, owner sonnet-ui.
18. **jaci re-lock**: done in the jaci working tree (uv.lock only, uncommitted; japes cb256157 to 433b89d2, plato client 0.2.6 to 0.2.8, pyasn1 0.6.5; openai and
    pydantic did not move). Left: the user's yes to commit, then the full `pre_push_check.sh`. Owner: sonnet-jaci.
19. **Parallel tests inside a job (pytest-xdist), from sibling repos.** kernel and juno run `-n auto --dist loadscope` (kernel gives each worker its own Postgres
    schema, sets the worker count from the container's CPU quota, and merges per-worker coverage files; juno adds `--reruns 3`); macer and jazzx-assistant carry the
    dependency. japes has no xdist (sharding by file in CI only; the 13 to 20 min serial time is the cost). Measure first: a local `-n 4 --dist loadscope` run of the
    full suite, then list the failures (shared ports, the Postgres tests via `JAPES_TEST_POSTGRES_URL`, `.plato-pack-blobs` and page-cache dirs, the 9.95 s
    teardown tests). Build only the isolation the failures call for (a per-worker schema and tmp dir keyed on `PYTEST_XDIST_WORKER`), then decide shards versus
    xdist versus both in CI. Fold with 11 and 12; owner sonnet-runtime. Older survey: `SIBLING_SURVEY_2026-09-02.md` (stale; a fresh one is item 20).
20. **Fresh sibling survey** for 2.6.9 (read only): what kernel, juno, jazzx-assistant, macer and knowledge-hub learned since 2026-09-02 that japes should absorb
    (CI, test isolation, config patterns). `scripts/local/sister_repo_activity.sh` is the start; output is a `note_*`, not a build. Owner: opus-xrepo.
    Done 2026-11-03: `status/note_sibling_survey_2026-11-03.md`. Changes to this plan: the common bump targets 0.4.0 (96b0495f), not 0.3.0; item 19 gains the
    collect-twice xdist check; item 14 gains `prefixItems` and the supports-thinking rule; new checks for eval comparison drift, mock KH parity and DocIntel 429 handling.
21. **Structured outputs: `prefixItems` and `oneOf`.** Add the `prefixItems` case and a fall-back rule to `jazzx_sdk/llm/structured.py` (sibling kernel b0e2d325 stops
    sending native structured outputs for those schemas); with 14, and a live smoke only on a typed figure. Also send thinking only to models whose card supports it
    (macer 628352f0). Owner: sonnet-runtime.
22. **Eval comparison drift check**: eval-service 9200af5, eafe21b, c945df0, 8059398, 039f67b against the SDK evaluation control plane; list gaps, fix by family. Owner:
    sonnet-runtime (read-only survey first).
23. **Mock Knowledge Hub parity**: update validation (2026-09-02 finding), versioned taxonomy and prompt APIs, synthetic-object marking, imdoc hiding, pipeline filter.
    Measure what the mock lacks before building. Owner: sonnet-runtime.
24. **DocIntel 429 handling**: honor `Retry-After` and back off (kernel 0b69854e, 704d2dbe); check the japes client. Owner: sonnet-runtime.
25. **CI hygiene from siblings**: a warn-only workflow that the `common` pin is on the latest release (assistant 2e7f6a1), after the common bump; compare test markers
    (`real_llm_call`, `integration`, `long_running`) with japes when 11, 12, 19 land. Owner: sonnet-runtime.
26. **Chat two-stage answer** (jazzx-assistant fast answer from prior findings): read-only look at the pattern and ask how their chat-pipeline migration went. Owner:
    opus-xrepo, then sonnet-runtime if worth absorbing. Also feedback labels (eval-service bf14628): decide if they belong in the SDK feedback service.
27. **Dependabot gate**: ask the siblings (knowledge_hub PAGI-2139) what gate they run; adopt for the pre-push alert check if it fits. Owner: opus-xrepo.

28. **Visible failure when a turn trace is not written** (carried to a later version, no code now): `TurnTrace.record` swallows a write failure and only logs it, so a
    lost trace is silent in the reply. Options to scope: a counter or metric on the failure, and an "unwritten" flag on the `trace_id` the reply carries. Settle first, from
    the new DEBUG line at record time, whether the cloud 401 was an empty identity (then the fix belongs at the caller) or a cleared one. Owner: sonnet-runtime.
29. **Clear logs by date range and type** (scoping only, user request via opus-xrepo; no code until the user decides). Owner: sonnet-runtime.
    - *Inventory (read from code, not measured).* Records that behave like logs, and what already removes them:
      run journal `turn_run` and `turn_run_event` (`purge_terminal(older_than_seconds)` on the store, called from `plato/jobs.py:80`; reaping of stale runs is separate);
      queue executions `japes_queue_execution` (`purge_completed`, the replay window); sessions `agent_session` (`reap_stale` by a `SessionReaper`);
      request idempotency `japes_request_idempotency` (expires by its window); conversation messages `conversation_message`; cost records `japes_turn_cost` and `cost_record`
      (no delete found); feedback `japes_feedback` and `japes_feedback_history` (delete by id or entity, not by range); config audit `config_audit_event` (no delete found);
      eval `eval_case_run` and `eval_experiment`; pack lint runs `pack_lint_run`; pack draft events `pack_draft_event`. In Knowledge Hub: canonical Trace, Decision, Evidence,
      Outcome objects in the canonical collection (no range delete found in the store). Blob: offloaded payloads, not inventoried. Not checked: Plato's own request logs and any
      cloud log stream, which live outside the SDK.
    - *Shape.* One admin operation: types (a closed list), `from` and `to`, tenant, `dry_run` defaulting to true and returning counts per type; a real run needs the dry-run's
      count echoed back as confirmation and writes one audit entry (who, tenant, types, range, counts). Each store gets one `purge_range(tenant, start, end)` beside its existing
      purge, one shape for Postgres, KH and blob (the symmetry rule), and the operation fans out over them.
    - *Safety.* Governance records (decisions, audit, canonical evidence and outcomes) are excluded unless the type is named explicitly, and never by a wildcard. Tenant
      required, identity required, an admin role gate, no unbounded range, no cross-tenant. Hard delete versus tombstone to settle. Zero-retention tools are unaffected.
    - *Where.* An SDK function per store plus the fan-out in `jazzx_sdk` (so any host has it), a Plato admin route over it (gated like the other admin routes), and a CLI script
      that calls the same function. No logic in the route or the script.
    - *Open for the user.* Which types count as "logs". Hard delete or tombstone. Whether the audit entry itself is ever deletable. Whether KH canonical objects are in scope
      (KH owns its own retention). Whether a range delete may cross an open run. Who may call it (platform admin only, or a tenant admin for their own tenant).

30. **Clear a case condition** (follow-up of the open-conditions slice, 2.7.0): no route sets an `OutcomeCondition.resolution` after a run; a reviewer route (and what it records, who, when, and how a rerun carries a resolved condition) is the next slice. Also `timing` and `party` on a missing-document condition once `ClassNeed` carries them. Owner: sonnet-runtime.

31. **Policy change to impact, the open-cases half** (catalog slice P6, 2.7.0): `pack/release_report.compare_packs` (served at `GET /packs/{id}/release-report`) already lists what a new version changes (jobs, rules, documents, catalog, coverage, and the gold cases whose answers move, without a model). Missing: "which open cases need a rerun", that is, finding the stored case runs of the old version that judged a rule the change touched and naming them for a rerun (the rerun submit and `impacted_rules` exist; nothing maps a pack change to stored runs). Not registered in the pipeline catalog, because the catalog lists runnable pipelines and this is a report. Owner: sonnet-runtime.
32. **Feedback to improvements, the glue** (catalog slice P6, 2.7.0): the parts exist but are not composed: an approved correction becomes a gold case (`pack/correction_cases.py`, `CorrectionCaseSync`), a correction is diagnosed to the layer to fix and a ranked fix list (`pack/diagnosis.py`, `diagnose`, `fix_list`), and eval signals become guidance proposals (`modes/evolve/curator.py`, `route_improvement_signals`, `synthesize_bucket`). Missing: one run that takes approved feedback through the three and files the proposals, and the knowledge-loop plan's change classes. Owner: sonnet-runtime, with the 2.7.1 plan.

## Order

1. Start 2.6.9 commit and this plan; read `accepted.md` and the TODO markers (8).
2. Release unblockers: 11, 12, 13, 19 (speed and CI), then 9/10 (unit ids change, so jaci hears early).
3. Consumer items: 1, 2, 3, then 4 and 5 if the Solution page asks.
4. The common bump (gated) once the suite is stable; thinking fill (14) with its smoke.
5. 7, 15, 16, 17 as capacity allows.

## Done when

Each item is committed with tests that failed against the old code, CHANGELOG entries carry line counts, the full suite passes on the new lock pins, and the full-range
adversarial review (run by the user from the review worktree) is clean.

## Open for the user

ACR push beside GHCR (INFRA-6028); workspace copy-on-write runtime on the Plato roadmap (BSD-5632); version numbers for Plato and client; the pack-helpers question (6); the MACER metrics source; guide topic ids on extracted jobs (16); the figure for each provider run.
