# Sibling repo survey, 2026-11-04

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Read only. Delta since `note_sibling_survey_2026-11-03.md`: `scripts/local/sister_repo_activity.sh --no-fetch --days 3` over the local clones the user
pulled (juno is on `JAPES_V2`, the rest on `main`), then `git show --stat` on the commits below and a grep of japes for each pattern. Nothing run against a
provider, no fetch. "Check" means not yet verified against japes; the clone pulls were not compared against `origin/main` commit by commit.

## Act on (small, consumer-neutral)

1. **Experiment slots leak when a run dies before invocation** (eval-service 78052ff, ac5e11d). A fanned-out run claimed by a worker that then dies holds its
   `max_concurrency` slot with nothing to time it out; the fix fails runs queued longer than a stale threshold (default 7200 s) with no invocation, both in the
   release pass and in a backstop sweep, and makes a terminal PATCH run the same completion check. japes has `evaluation/reclaim.py` and `_reclaim.py` and an
   `evaluation/experiments.py` that mentions queueing; check whether the SDK experiment runner caps in-flight runs and whether reclaim covers a queued run with no
   invocation. If the SDK fans out, the same leak applies.
2. **Custom scorer scripts get the run's trace, conversation and message ids** (eval-service 489c359, 117 lines in the orchestrator). Check
   `evaluation/custom_scorers.py`: does the scorer context carry the trace and conversation ids, so a script can read the run it scores? If not, add them to the
   context object (additive).
3. **Gateway routing by env var** (jazzx-assistant 980abca, docs only): it relies on the provider SDKs reading `OPENAI_BASE_URL` and `ANTHROPIC_BASE_URL`
   themselves. japes passes no `base_url` to the OpenAI or Anthropic clients (grep over `llm/` and `agents/` finds only the Ollama provider), so the native
   resolution holds in the code read; not proven at runtime. Belongs with the parked gateway thread; no action now.

## Check (read the diff before deciding)

4. **Tool-retry demands after max turns** (macer 85f6315f, +74/-12): the validated-output loop no longer demands a retry once turns are spent, and scopes mixed
   validator messages. Compare `jazzx_sdk` validated-output and agent-loop retry paths for the same demand-after-limit case.
5. **Dependency-order resolution of metric inputs and outputs, a "NOT APPLICABLE" prior-condition status, labeled metric links in the calculation breakdown**
   (macer 0d704e9d, 12b778c3, 1dd4bad6). These are MACER consolidation inputs, not SDK gaps by themselves: the metrics-source question and the MACER steps stay the
   user's decision. The labeled `metric:` link shape is worth reading when the SDK's calculation-breakdown provenance is next touched.
6. **Native tool `output_schema` registered from the docstring** (kernel 6e495089): juno's build generators needed it. japes already carries `output_schema` through
   the kernel client types; check only whether any japes-registered native tool still publishes `null`.
7. **Session id hashing, MD5 to SHA-256** (assistant 8d8af2d, CodeQL): grep of `jazzx_sdk`, `plato` and `common` finds no `md5` use. Nothing to do.

## Consider (not planned)

8. eval-service 823d634 (Macer clone remap rules), 236a308 (merge of the eval phase-3 sandbox branch), knowledge_hub 22affada (sandbox merge repair, common
   `f54f4c1`): service-side work, no SDK surface seen.
9. juno 8370f2f4 (reject script listeners that deploy but fail every run) and 0e8f73d7 (Codex model, effort and idle timeout from env): juno-internal.
10. kernel 378abce8 (backfill before each unique-key swap), knowledge_hub 781f5000 (test fixture): service-side.

## Standing

- common stays at 0.3.0 (`5fa47753`); the 0.4.0 pin is still only on an unmerged sibling branch, so nothing changed on that front in this delta.
