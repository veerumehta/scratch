# Sibling repo survey, 2026-11-03

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Read only. `scripts/local/sister_repo_activity.sh --no-fetch --days 61` over juno, eval-service, macer, kernel, client-api, knowledge_hub, jazzx-assistant and
assistant (jaci is ours). About 500 commits since the 2026-09-02 survey. Local clones, no fetch; findings come from commit headlines plus the few diffs named below.
Nothing was run against a provider. "Check" means not yet verified against japes.

## Act on (plan items change)

1. **The `common` target stays 0.3.0 (corrected after a fetch, 2026-11-03).** juno, eval-service, kernel, knowledge_hub and assistant pinned common `96b0495f`
   (`version = "0.4.0"`), but it is only on the unmerged branch `origin/feat/BSD-5538-phase3-v0.4.0` (branched from main's 3f70d3cb). `origin/main` is `5fa47753`,
   version 0.3.0, tagged `v0.3.0`: that remains the gated bump's target. 0.4.0 adds tenancy guards, a guard CLI and reusable workflow, tenant-leading unique swaps
   and tenant FKs, and a start-up refusal when `PLATFORM_TENANT_ID` is unset while the service maps tenant tables. Revisit it once 0.4.0 merges and is tagged, and
   read that refusal against Plato's boot-contract tests then.
2. **xdist traps for item 19.** juno 07470784 (`fixed parametrize values so xdist workers collect the same tests`): a parametrize list built from random or unordered
   values makes workers collect different tests and xdist aborts. Run `pytest --collect-only` twice and diff before trusting `-n`. kernel and juno also use
   `--dist loadscope`, per-worker Postgres schemas, `--reruns 3` (juno) and `--durations=20` (kernel). Already on the plan as 19.
3. **Structured outputs and `oneOf` or `prefixItems`.** kernel b0e2d325 stops sending native structured outputs for schemas with `oneOf` or `prefixItems` (touches
   both its OpenAI and Anthropic output-schema modules, with tests). japes `jazzx_sdk/llm/structured.py` walks `oneOf` (lines 127 to 182) but has no `prefixItems`
   handling and no fall-back rule. Check against a real provider schema; it belongs with the thinking-fill item (14), which already needs a live smoke.
4. **Thinking only where supported.** macer 628352f0 sends `reasoning_effort` only to models that support thinking. Same family as item 14; the model cards
   should answer it, not a hand list.
5. **CI warns when `common` is behind the latest release.** assistant 2e7f6a1 (`common-pin.yml`, warn only, 17 lines). Cheap to adopt once the common bump lands.
6. **Eval comparison drift.** eval-service 9200af5 (report scoring differences in comparisons instead of rejecting them), eafe21b (honor explicit scorer pass
   verdicts), c945df0 (rank digit-letter model tokens such as `gpt-4o` in the override guard), 8059398 (compare process experiments by outcome, execution path,
   definition changes and noise floor), 039f67b (finalize stuck process evals). japes took the eval control plane in 2.6.7; check each of these against
   `jazzx_sdk` evaluation code (the symmetry question).

## Consider (not yet on the plan)

7. **Two-stage chat answer.** jazzx-assistant b0656f3 and 08775da: publish a quick answer from prior findings before the full one; the fast agent gets a one-line
   index per finding and one `get_findings` tool call. A chat-pipeline pattern, and jazzx-assistant now runs on japes chat pipelines (2882dc8, 1eb6d72), so it is a
   consumer: ask how the migration went and what they patched around.
8. **Knowledge Hub parity of japes' mock.** KH added versioned taxonomy and prompt APIs (client-api regenerated 4 times), synthetic-object marking and default
   hiding (51218ecc), imdoc entity hiding (61def01f), a processing-pipeline filter setting, and editable collection display names. The 2026-09-02 survey found the mock
   weaker than real KH on update validation; check that fix landed and whether the mock covers the new surface.
9. **Workspace copy-on-write runtime (BSD-5632).** kernel 181573df, assistant 83bfc20, knowledge_hub 965faee6 and juno 8622a975 each added a workspace-owned shared
   runtime (copy-on-write, discard, workspace context in workers and traces). Not a japes feature today; it matters for the common bump (items 1 above) and for any
   Plato multi-tenant plan. Surface to the user as a question, not a build.
10. **Image push to ACR beside GHCR** (INFRA-6028: kernel, knowledge_hub, assistant). japes' two image workflows push GHCR only. An infra decision for the user.
11. **Document-intelligence retry.** kernel 0b69854e and 704d2dbe honor ADI's `Retry-After` on 429 and add backoff; macer 6f67560a and 44fa9a0d consolidate retry
    logic. Check japes' DocIntel client for the same 429 handling (the Acra billed run is the exposure).
12. **Dependabot gate.** knowledge_hub PAGI-2139 calls its dependency bump a "Dependabot security gate" and many sibling commits carry `security-fix`. Ask whether a
    gate exists in their CI that japes could reuse for the pre-push alert check in CLAUDE.md.
13. **Test hygiene.** kernel tags `real_llm_call`, `integration` and `long_running` and excludes the first from the unit job (7a8d19d5); knowledge_hub split its API
    tests (#363). Compare with japes' markers when sharding is reviewed (items 11, 12, 19).
14. **Feedback labels and RCA clustering.** eval-service bf14628 and juno 7739f71f add feedback labels, assignments and a daily labeling job. japes' feedback service
    lives in the SDK (Plato hosts); check whether labels belong there.

## No action

kernel removed its Knowledge Hub implementation and `kh_redirect` (KH cleanup 3/3). macer's work is its own product (cluster verdicts, planner, QA suite); its
`reasoning argues for its pick` extraction change and `name and link the metrics a formula metric reads` are the MACER steps (item 15) to read when that item is taken.
juno is copilot and BPMN work with no SDK overlap beyond the xdist commit above. client-api is generated clients.
