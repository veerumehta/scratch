# Findings weighed and closed without a fix. One `path :: slug` per line; lines starting with # are the reasoning.

# mock-latest-default-diverges (NOTE, low), 2026-11-11, v2.7.1 whole-range review.
# The in-memory MockKnowledgeHubClient lists every version when `latest` is not named, as it always did; the real hub defaults to
# latest=true. Kept on purpose: a caller that names nothing has always got every row from the mock, and changing the default would
# change every local-mode test that lists entities. Blast radius checked: the one fabric caller that depends on the difference,
# EntityStore._find_by_fingerprint, names latest=False explicitly; the HTTP mock app's facade path sends latest=true, so the two
# mock paths disagree only for a hand-built in-memory call that names nothing.
jazzx_sdk/clients/mocks.py :: mock-latest-default-diverges

# strict-view-skips-non-coroutines (NOTE, low), 2026-11-12, v2.7.2 whole-range review.
# StrictKnowledgeHubClient wraps coroutine methods only, as its docstring says. Blast radius checked: KnowledgeHubClient has no async
# generator method and only two plain methods (`generated_client`, `strict`), neither of which calls the hub, so no outage path
# escapes the strict flag today. Revisit when a streaming method is added.
jazzx_sdk/clients/knowledge_hub_client.py :: strict-view-skips-non-coroutines

# pack-dir-overcrowded (PLACEMENT, low), 2026-11-12, v2.7.2 whole-range review.
# alias_merge.py writes pack draft files and sits beside catalog_merge.py, its sibling and its imports' home. jazzx_sdk/pack/ already
# holds about 97 modules before this file; splitting the package is its own change (every importer moves), not part of this round.
# Blast radius checked: one importing module (`server/vocabulary_review.py`), two docstring mentions in `pack/`, and the tests.
jazzx_sdk/pack/alias_merge.py :: pack-dir-overcrowded

# agents-sdk-wal-floor-unchecked (NOTE, low), 2026-11-16, v2.7.2 sqlite hardening review.
# create_agent_session leaves its engine to the Agents SDK, which sets WAL and a 5 second busy timeout on a sqlite file engine itself
# (confirmed in the locked 0.24.0). pyproject.toml asks only for openai-agents >=0.22.0 and the hook was not checked there. Blast
# radius: the agent-session engine's journal mode and timeout on a consumer that resolves an older floor release; no other engine
# reads it. Weighed: no intent to pin the floor now; a TODO in engine.py would move the reviewed tip.
jazzx_sdk/fabric/db/engine.py :: agents-sdk-wal-floor-unchecked

# rag-search-outage-not-wrapped (DEFECT as filed, 2026-11-16, v2.7.3 whole-range review): not a defect.
# `RagGuidanceStore.search` reads through `RAGStore.retrieve_by_metadata`, which wraps every failure in `KnowledgeFabricError` and
# lets only an access denial pass (`KH_PASS_THROUGH`), so `retrieve` already degrades a Knowledge Hub outage and an access denial
# still stops the run. `tests/fabric/guidance/test_db_store_search_failure.py` pins both over the real `RAGStore`.
jazzx_sdk/fabric/guidance/store.py :: rag-search-outage-not-wrapped

# draft-written-reported-failed (NOTE, low), 2026-11-16, v2.7.3 whole-range review.
# If `propose_change` raises after `synthesize_bucket` stored the draft, the pack is reported failed while a draft exists, and its
# corrections count as named. Weighed: the draft is in the tenant's list for a person to approve or discard, and a change
# proposal can be attached by hand; `propose_change` raises only on a store failure, which `failed` reports. Blast radius: the one
# sweep job (`plato/jobs.py`). No intent to change it now.
jazzx_sdk/pack/guidance_sweep.py :: draft-written-reported-failed

# persist-factory-errors-swallowed (NOTE, low), 2026-11-16, v2.7.3 whole-range review.
# `persist_step` still skips the side-branch persist for a factory failure other than `ConflictingHistoryError`; that is the
# stated design (a factory that needs what a skipped stage would have grounded must not cost the refusal) and the failure is logged.
# Blast radius: refusal and escalation turns of a host that passes an agent factory.
jazzx_sdk/pipelines/chat/engine.py :: persist-factory-errors-swallowed

# paren-figure-depends-on-wrap (NOTE, low), 2026-11-17, v2.7.4 delta review.
# A parenthesized number inside a line is left out as a list marker, and the same one opening a wrapped line is kept; the
# inside-a-line rule is the existing, stated one, and the wrapped case now gives the right answer.
# Blast radius: `six (6) months` style restatements in `scan_figures` readers; no figure is invented.
jazzx_sdk/pipelines/policy/figures.py :: paren-figure-depends-on-wrap

# offset-walk-skips-on-mutation (NOTE, low), 2026-11-17, v2.7.4 delta review.
# `query_all` freezes the window with `until` but a record soft-deleted or moved off `approved` during the walk shifts later
# offsets by one, so one record is skipped until the next sweep.
# Blast radius: `guidance_sweep` and `guidance_uplift`, one record on a concurrent review change.
jazzx_sdk/evaluation/feedback/paging.py :: offset-walk-skips-on-mutation

# common-pointer-not-committed (NOTE), 2026-11-18, v2.7.5 review.
# The reviewer saw the review worktree's `common` at e5f29d9a against the recorded 3cb0a55d. The recorded pointer carries every signature
# `CommonGatewayRoute` uses (`use_ai_gateway(flag_key, settings=None)`, `ause_ai_gateway`, `async_openai_client(settings=None, **kwargs)`,
# `openai_base_url`, `api_key`: checked with `git show 3cb0a55d:core/ai_gateway/__init__.py`); the review worktree's submodule was
# stale and was moved to the recorded sha.
# Blast radius: none for a clean checkout; the review worktree only.
jazzx_sdk/llm/gateway/common.py :: common-pointer-not-committed
