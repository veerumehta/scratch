# Plan: 2.6.9 (opus-xrepo, 2026-11-02)

Working branch `v2.6.9` (SDK 2.6.9; Plato and client version follow the user's call at the first commit), cut from the v2.6.8 tip after the squash lands. Nothing here is
started. Items 1 to 9 of `plan_2_6_8_carried_from_2_6_7` carry over unchanged (that file stays the detail for them); this plan adds the items raised since and sets order
and owners. Order is by what blocks a consumer or the release first.

## Gates (not built, decided by the user)

- **Common submodule 0.3.0.** Bump `common` from 25bf9d81 (0.2.0) to 0.3.0 main (5fa47753): multi-tenancy foundations, default-off, but `core/db.py` gives every session
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

## Order

1. Start 2.6.9 commit and this plan; read `accepted.md` and the TODO markers (8).
2. Release unblockers: 11, 12, 13 (speed and CI), then 9/10 (unit ids change, so jaci hears early).
3. Consumer items: 1, 2, 3, then 4 and 5 if the Solution page asks.
4. The common bump (gated) once the suite is stable; thinking fill (14) with its smoke.
5. 7, 15, 16, 17 as capacity allows.

## Done when

Each item is committed with tests that failed against the old code, CHANGELOG entries carry line counts, the full suite passes on the new lock pins, and the full-range
adversarial review (run by the user from the review worktree) is clean.

## Open for the user

Version numbers for Plato and client; the pack-helpers question (6); the MACER metrics source; guide topic ids on extracted jobs (16); the figure for each provider run.
