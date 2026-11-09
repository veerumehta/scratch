# macer onto the japes SDK

Author: Virendra Mehta

Source: read-only survey of macer `main` (ebf64309) on 2026-10-22, refreshed 2026-11-09 against japes 2.7.0 (`main` 2c8274b0): macer's pin and file names re-read, SDK anchors checked by path at the 2.7 tree; tests not run on either side. This plan is for the macer team to execute in the macer repo; japes sessions never edit macer.

## Status and modifications

- 2026-11-09 updated from 2.6.5 to 2.7.0. Changes: the pin target is the 2.7.0 `main` commit (2c8274b0), not a plato sha (the old text named `be09cfa2`, a plato rev; pinned revs are `main` commits or tags); slice 2 anchor is `jazzx_sdk/agents/run_kit.py` (a module, the old text said `agents/run_kit` as a package); slice 3 anchor is `jazzx_sdk/agents/call_guard.py`; slice 9 gains the SDK's adjudication package and the duplicate-condition merge; a new slice 10 for starting and waiting on Macer as a process; a sequencing note for the AI Gateway work now on both sides.
- Not re-surveyed: macer's non-`main` branches beyond their names, test results, image size, anything that landed on macer after 2026-11-05 on branches that are not `main`.

## State

- macer `main` (local ref 034ddd1d, 2026-11-05) still pins japes at `64d9099e` (v2.4.9), twice (`pyproject.toml:26` and `:130` for `jazzx-eval-contracts`, the `[tool.uv.sources]` rev). Three minor lines behind 2.7.0 (2.5, 2.6, 2.7) and every patch release between.
- Only `KnowledgeHubClient` and the queue handler types come from the SDK. The run kit, retries and input filter are local on `main`.
- An earlier adoption (run kit, commit `d2f21bd8`, 2026-06-22) lives on branch `platform_v2`; a local `japes_v2` branch exists (pin `4b088503`). Newer branches: `ai-gateway-migration` (macer's own AI Gateway change, same author as the one on japes), `anmol/refactor-agents`, `anmol/refactor-llm`, `anmol/refactor-tools`, `local_runner`, `umang/e2e-instance-agnostic`.
- macer already drives a Flowable engine from its QA suite (`e2e/qa_automation_suite/src/api/flowable_client.py`), which is the process the SDK can now start.
- Decide: restart `JAPES_V2` from `main` (recommended), harvesting `platform_v2` commits where they still apply; check whether `anmol/refactor-*` already did part of slices 2, 4 and 7 before redoing them.

## What 2.7.0 changes for this plan

- Three minor lines of changes arrive at once on the pin bump. Read `docs/status/CHANGELOG.md` from 2.5.x to 2.7.0 first. Known breaking items for a host: five tenant-keyed stores take a required `tenant_id` (only if macer uses the SDK's stores; most likely it does not); pipeline ids were renamed with one deprecation warning per old id; converted documents stage as `.japes/<file name>.md`.
- New and relevant: the process launcher (`jazzx_sdk/processes/`), duplicate-condition merge in the adjudication recipes, the document processing pipeline, the evaluation control plane (`jazzx_sdk/evaluation/`), `jazzx_sdk/scope_claims.py` for forwarded scope claims.

## Slices (lowest risk first; parity = macer's own tests stay green)

1. Pin bump to the 2.7.0 `main` commit (2c8274b0), relock, import-contract test. Parity: test_japes_handler, test_hub_read_retries, test_jtbd_setup. Run the full suite once on the new pin before any other slice.
2. Run kit: retrying, input filter, json schema output, validated output and `run_agent` become thin adapters over `jazzx_sdk/agents/run_kit.py`. Parity: test_retry*, test_input_filter, test_json_schema_output, test_validated_output, test_incomplete_output, test_agent_utils. Check macer's tool-suppressing retries against the SDK's tool-free validation retries and `ExtraRound` budgets.
3. Call guard: deadline and stall limits on macer's model calls (`jazzx_sdk/agents/call_guard.py`, additive).
4. Cost: `utils/cost.py` onto `jazzx_sdk/llm/cost.py` and model cards. Gap check: cache-write rates and newest model rows.
5. Mock Knowledge Hub onto `jazzx_sdk/clients/mocks.py` and `jazzx_sdk/server/mock_knowledge_hub_app.py`.
6. MLflow and telemetry onto `jazzx_sdk/observability`; the span-to-mode map stays local.
7. Settings and LLM config layered on `jazzx_sdk/config/settings.py` and `jazzx_sdk/llm/config.py`.
8. Evaluation: `scripts/eval_findings*.py` onto `jazzx_sdk/evaluation/` (experiments, stability, variants, input overrides, `adjudication_scorers.py`). Record golden outputs first; mlflow-skinny vs full is a decision.
9. Condition dedup and resolvers onto the adjudication package (`jazzx_sdk/agents/adjudication/`: conditions, planner, evidence scope, impact, vocabulary) and its duplicate-condition merge (on by default). High risk: shadow mode first, compare against `design/condition_dedup.md` and the `condition_dedup_testbed` data.
10. Macer as a process: no macer code change is required for the SDK to start and wait on a Macer run. The pack author fills the checklist in `docs/status/note_process_integration_checklist.md` in japes (start variables, idempotency key per loan collection, start call shape, outcome variables, failure shape, waits). The default resume is polling; a callback from a service task is optional. A worked example is the sample pack `pulte-home-mortgage-macer`.

Sequencing: slices 1 to 3 and 10 are independent of the rest. The AI Gateway work (macer's `ai-gateway-migration` and japes's branch of the same name) both use `common.core.ai_gateway`; land the pin bump (slice 1) before either gateway change so the two do not diverge on the common version.

## Stays in macer

LOS and mortgage code (`los_entities`, `los_records`, `document_mappings`, `loan_manifest`, `loan_program_agent`, program blocks, `borrower_roster`, `findings_converter`), the REPL tool, headroom compression, rerun planning and the loan metric verifier (no SDK counterpart). Candidates to propose to the SDK: ranged or truncated document reads, an incremental rerun planner.

## First PR

Slice 1, then 3 and 2. Needs: relock (network and private client repo auth in Dockerfile and CI), Python 3.12, a check that macer's suite passes on the new rev.

## Unverified

Image size after the bump; macer retry semantics against the run kit; truncation behavior of SDK document tools; the Streamlit app and routes inside `japes/main.py`; whether `anmol/refactor-*` overlaps slices 2, 4 and 7; whether the jump from 2.4.9 needs intermediate pins.
