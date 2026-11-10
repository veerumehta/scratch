# Sibling repo survey, 2026-11-05

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Read only. Delta since `note_sibling_survey_2026-11-04.md`: `scripts/local/sister_repo_activity.sh --no-fetch --days 2` over the local clones, then
`git show --stat` on the commits named, `gh pr list` (read) and a trial `git merge-tree` of each open sibling branch into `origin/plato` a88afb27. Nothing run
against a provider. Diffs were read for the two japes branches only; the rest is commit headlines.

## Act on (people outside this team are changing japes)

1. **PR #108, `ai-gateway-migration` -> main (ukwal, 2 commits, 15 files, +548/-24)**: routes the native OpenAI and Anthropic clients through the AI Gateway
   when `AI_GATEWAY_BASE_HOST` and `AI_GATEWAY_API_KEY` are set, behind the Flipt flag `ai-gateway-japes` (`FLIPT_URL`, `FLIPT_API_KEY`). New
   `jazzx_sdk/llm/ai_gateway_flag.py` (a Flipt client), `llm/config.py` (+70), changes in `llm/manager.py`, `llm/providers/{openai,anthropic}.py`,
   `agents/{openai,anthropic}_provider.py`, `agents/models.py`, `agents/service.py`, `runtime/launcher.py`, `plato/wiring/default.py`, `introspection.py`, and
   `tests/test_ai_gateway.py` (327). It merges into `origin/plato` a88afb27 with no conflicts. jazzx-assistant de44051 and juno 0c394b14, 61fc9b30 already
   document or use these vars as "the vars japes now reads", so the siblings are building against a branch that is not on `main`. Questions for the user:
   (a) the SDK taking a feature-flag service (Flipt) as a dependency of the LLM path (a fail-closed 30 s cache is described in juno's twin); (b) the flag and
   env names are consumer-shaped (`ai-gateway-japes`); (c) this is the parked gateway thread, now with a PR; (d) the PR targets `main`, not `plato`, so merging
   it there puts commits on `main` that `plato` and `dev` lack (record `main` on `dev`, `dev` on `plato`, as after #107).
2. **PR #101, `feat/BSD-5632-japes-workspace-context` -> main (madhuripenikalapati-jazzx, 3 commits, 2 files, +107)**: `jazzx_sdk/workspace_claim.py` declares a
   `sub_tenant_id` scope claim (header `x-sub-tenant-id`, uuid, kernel only) with `register_workspace_claim()`, on the existing `scope_claims` machinery.
   Merges clean into `plato`. It is the right mechanism, but the SDK docs say it names no claim (a host declares each). The module names one, so the claim
   belongs in the host, or the SDK needs a stated exception. Same `main`-target note as #108.
3. **PR #66, `feat/llm-pricing-provider-seam` -> plato (id-jazzx)**: "public per-million pricing row plus a neutral `register_pricing_table`". Not read. It
   touches the model cards and pricing path; check it before the `gemini-omni-1.2-flash` card work.

## Check

4. **eval-service 6f3380f** (tests for how clone filter layers combine per run): service-side, nothing seen for the SDK.
5. **macer 2b55000d and the refs-in-conditions merge** (dedup action-key join, action gate, single-call reconcile; refs in conditions): MACER consolidation
   inputs. The MACER steps stay the user's decision.
6. **knowledge_hub 21d74d4a, 5924f328** (jsonl and json parsing support): an ingestion format change. Check whether the SDK's document tools or the KH client
   list the accepted formats anywhere that now needs a line.

## Consider (not planned)

7. kernel a8bad514 (read_pdf_page fallback) and 085dba2b, assistant c09e668 (refuse duplicate rows before tenant-leading unique keys): service-side, same
   BSD-5859 and BSD-5862 line as the previous note.

## Standing

- common stays at 0.3.0 (`5fa47753`); no change in this delta.
- Open PRs against japes by others: #108, #101, #71, #66, #55 (CI and coverage). Only #108 and #101 touch the SDK.
