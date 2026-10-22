# macer onto the japes SDK

Author: Virendra Mehta

Source: read-only survey of macer `main` (ebf64309) on 2026-10-22; counts and paths verified by grep, tests not run.

## State
- macer `main` pins japes at `64d9099e` (v2.4.9), twice (`pyproject.toml:26`, `:113` for `jazzx-eval-contracts`).
- Only `KnowledgeHubClient` and the queue handler types come from the SDK. The run kit, retries and input filter are local on `main`.
- An earlier adoption (run kit, commit `d2f21bd8`, 2026-06-22) lives on branch `platform_v2`, 25 ahead and 60 behind `main`. A local `japes_v2` branch (one commit, 2026-08-02, 27 behind, pin `4b088503`) exists.
- Decide: restart `JAPES_V2` from `main` (recommended), harvesting `platform_v2` commits where they still apply.
- Pin to a pushed rev: `be09cfa2` (origin/plato, 2.6.5), later revs as pushed.

## Slices (lowest risk first; parity = macer's own tests stay green)
1. Pin bump, relock, import-contract test. Parity: test_japes_handler, test_hub_read_retries, test_jtbd_setup.
2. Run kit: retrying, input filter, json schema output, validated output and `run_agent` become thin adapters over `agents/run_kit`. Parity: test_retry*, test_input_filter, test_json_schema_output, test_validated_output, test_incomplete_output, test_agent_utils. Check macer's tool-suppressing retries against the SDK's tool-free validation retries and `ExtraRound` budgets.
3. Call guard: deadline and stall limits on macer's model calls (additive).
4. Cost: `utils/cost.py` onto `llm/cost` and model cards. Gap check: cache-write rates and newest model rows.
5. Mock Knowledge Hub onto `clients/mocks.py` and `server/mock_knowledge_hub_app.py`.
6. MLflow and telemetry onto `observability`; the span-to-mode map stays local.
7. Settings and LLM config layered on `config/settings` and `llm/config`.
8. Evaluation: `scripts/eval_findings*.py` onto `evaluation/` (experiments, stability, variants, input overrides). Record golden outputs first; mlflow-skinny vs full is a decision.
9. Condition dedup and resolvers onto adjudication and engine modes. High risk: shadow mode first.

## Stays in macer
LOS and mortgage code (`los_entities`, `los_records`, `document_mappings`, `loan_manifest`, `loan_program_agent`, program blocks, `borrower_roster`, `findings_converter`), the REPL tool, headroom compression, rerun planning and the loan metric verifier (no SDK counterpart). Candidates to propose to the SDK: ranged or truncated document reads, an incremental rerun planner.

## First PR
Slice 1, then 3 and 2. Needs: relock (network and private client repo auth in Dockerfile and CI), Python 3.12, a check that macer's suite passes on the new rev.

## Unverified
Image size after the bump; macer retry semantics against the run kit; truncation behavior of SDK document tools; the Streamlit app and routes inside `japes/main.py`.
