# Sibling repo survey, 2026-11-10

Author: Virendra Mehta

Written by opus-xrepo from the local checkouts after the user's pull (no fetch), all refs, last 6 days, with the **full commit message bodies read** for all eight repos (macer 45 commits, eval-service 30, client-api 18, kernel 9, knowledge_hub 9, assistant 8, juno 5, jazzx-assistant 2). Diffs were not read. Nothing was run. `[V]` stated in a commit body, `[U]` not verified.

## japes-relevant findings

### AI Gateway (macer, juno, eval-service, kernel, jazzx-assistant)
- All use Flipt flag `ai-gateway-<service>` (30 s cache, fail closed to the direct path) and `common.core.ai_gateway` pinned at `e5f29d9` (common#268, "v0.5.0 once released") [V]. Same pin and design as our port.
- Claude on the gateway runs on the OpenAI chat completions format everywhere [V]. macer's body is the most detailed: `GatewayAnthropicModel` over `OpenAIChatCompletionsModel` keeps the same `cache_control` breakpoints on `get_response` and `stream_response`, replays thinking blocks on tool turns as `LitellmModel` does, and drops OpenAI-only verbosity; the client cache key includes the route so a flag flip never reuses a client for the other endpoint; embeddings keep litellm with `api_base={host}/v1` [V]. Check our gateway agent path for each of these (cache breakpoints, thinking replay on tool turns, route in the cache key).
- juno: the gateway now supports `/v1/responses/compact`, so compaction, Whisper and mem0 route through it [V]. [U] whether our session compaction path uses it.
- jazzx-assistant pins japes at the head of PR #108's branch (`f129712`, "every model, Claude included, on the OpenAI SDK through the gateway"), lock shows japes 2.7.0 and plato-client 0.3.0 [V]. It repins after our 2.7.1 release; PR #108 and #101 are closed as superseded (user's GitHub action).
- Model ids: macer stopped normalizing dashes to dots so names stay as the vendor gives them; kernel uses unprefixed model names on the gateway [V]. Check ours keeps ids as given.

### macer MA-4125 (income worksheet), which is Policy to Code and ACER territory
- The formula engine runs before the policy agents; every JTBD in a section that owns formula metrics now receives the engine's results as settled facts ahead of its guideline snippets. Reason: the agents worked out income, debt and DTI themselves and disagreed with the engine ($7,009 against the worksheet's $6,927.22) [V]. Our `case_to_verdicts` runs code as code and ACER for the rest; [U] whether ACER receives code-computed metrics as settled facts. This is the same idea as the rules library and deserves a check.
- Superseded conditions: when a prior condition still applies but the new evaluation states a different amount, percentage, date or count, the old condition is cleared ("Superseded: ...", `superseded_by`) and the new one raised; the post-step adds the replacement if the model omits it. A bug found live: dedup clustered the stale and replacement conditions, a cluster's sources share one resolution, so the replacement was stamped resolved; fix moves the replacement into a new open cluster [V]. ACER also merges duplicate conditions and carries only changed rules forward; check the same cluster-shares-one-resolution failure there.
- Program from the invocation, not inferred: the engine re-derived the program from LoanCore and fell back to FNMA, so a Freddie Mac loan's agents and formulas used different rules; fixed by taking the invoking `loan_program` [V]. Matches our overlays: the program must be an input to a run, never inferred, with no silent default.
- Tool-required retries: a retry that fails a tool-required rule gets only the named tools, must call them once, then answers (replaces a 15-turn cap) [V]. Compare with our retry handling.
- Cost: unrounded `cost_usd`, per-span breakdown, `mlflow.llm.cost` span attribute with tier and flex pricing [V]. The shape E5 in the Nov 10 enablers plan asks for.
- macer's QA suite deletes collections directly and in parallel ("updating deletion logic, delete collection directly", "making deletion parallel") [V from headlines]; it does not use bulk entity delete. Its local runner (`scripts/local_jtbd_queue_run.py`) runs the worker in-process against a mock Knowledge Hub and Azurite [V].

### client-api
- `d58290d` (the user's own commit, 2026-11-05) regenerates the knowledge-hub client from knowledge_hub `54eb6a44`: LLM references, synthetic cleanup, **async bulk delete**, duplicate-name error [V]. That is the 202 model our facade needed; it is on a branch, and bot revs regenerate from it. Client regeneration went manual-only then automated again (`automate-client-regeneration`, PR #78) [V]. Our facade reads the status code, so churn cannot break it; the ask to merge, tag the pinned rev and declare the 202 stands.

### kernel (BSD-5632 is the workspace ticket)
- Discarding a workspace searched one MLflow experiment per call (about 56 ms each, thousands of experiments), outlasted Builder Studio's 60 s cleanup timeout and returned 502; now 100 experiments per call [V]. `kernel_openapi_schema.yaml` gained `discardWorkspace` [V]. [U] whether `KernelClient` needs a method for it.
- Deleting a workspace's own agent or tool returned 500 after the delete had succeeded (the response was read after the tombstone) [V]. Lesson for the bulk-delete facade: a 5xx on a destructive call does not prove nothing was deleted, which supports "raise, never auto-retry, verify by read".
- `read_pdf_page` fell back to the local `_assistant_parsing` LLM when the collection's LLM id does not exist in a workspace kernel [V]; LLM ids differ across hosts and workspaces, so our packs must reference LLMs by name.

### knowledge_hub
- `PROCESSING_PIPELINE_FILTER_ENABLED` now defaults to false: a document or entity listing that passes no `processing_pipeline` returns every row, tagged or not; an explicit `processing_pipeline` is always honored [V]. Our document pipeline reads and the 2.6.9 coverage filters may now see more rows than before when they pass none; check what japes passes.
- MA-4692: `latest=True` entity listings resolve in SQL (`DISTINCT ON (name)`); without `orderby` pages are now ordered by id, and with `orderby` values sort natively, not by their `str()` form [V]. An unfiltered request had OOM-killed a 2 GiB pod (about 389k entities). Check callers of `read_entities_v2` that rely on name order; our `EntityStore.list` default limit is bounded.

### assistant
- Phase-3 tenancy (common v0.4.0): tenant columns, tenant-leading unique keys that keep the original constraint names, composite tenant FKs and RLS on 26 tables [V]. Two lessons relevant to our tenant-keyed stores: `TenantAwareSession` runs its `set_config` when a transaction begins, so `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE` fails with `ActiveSQLTransactionError`; set the isolation on the connection instead. And a migration must refuse duplicate rows before building tenant-leading unique keys, not stop halfway. [U] whether Plato's migrations or stores use either pattern.
- `delete_project` returned 500 for any project with invocations or message traces (FKs without cascade); 28 of 55 projects failed in one cleanup [V]. The same class of failure as a bulk delete over linked rows.
- The Jazz App gateway now sets `payload.collectionId` on processes it starts, so the process knows which collection the app may read; the gateway owns the value so an app cannot point a process at a collection it may not use [V]. Compare with our process launcher payload (2.7.0); the SDK should not let a caller choose the collection.
- Parent-team access flipped (security fix): a parent team's members now get its sub-teams' projects, not the reverse [V]. Nothing for japes unless we model team hierarchy.

### eval-service
- Experiment fan-out: one queue message per run, `max_concurrency` per experiment (cap 50, 422 outside range), atomic claim under a row lock, a sweep that fails runs queued longer than 7200 s with no invocation, PATCH to a terminal status frees the slot [V]. Also: weight scorers as shares of the test case score (BSD-5821), per-run sub-agent config overrides recorded at run start (BSD-5815), run-level custom aggregators pinned at creation and replayable [V]. [U] parity with our evaluation control plane (max in flight, stale sweep, shares, pinned aggregators). Shares-of-score matches the weighting in the rubric slice of the Nov 10 enablers plan.

## Follow-ups, none started
1. Check our gateway agent path against macer's cache breakpoints, thinking replay and route-in-cache-key; check model ids pass through unchanged.
2. Read ACER and `case_to_verdicts` for settled-fact metrics and for the cluster-shares-one-resolution bug.
3. Read what japes passes for `processing_pipeline` and which callers rely on `latest` ordering.
4. Read `KernelClient` against `discardWorkspace`.
5. Compare eval-service's concurrency, sweep, shares and aggregators with our control plane.
6. Ask common's owners to tag v0.5.0 (already queued).
7. Read Plato's migrations for the `SET TRANSACTION` and duplicate-key patterns.
8. Not covered: repos were not fetched, diffs were not read.
