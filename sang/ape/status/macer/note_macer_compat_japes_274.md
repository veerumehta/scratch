# macer against japes 2.7.4: compatibility check

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Check of 2026-11-17, decides nothing. Throwaway only: `/tmp/macer_compat` (a local clone of macer at 47473a32), a uv venv with Python 3.12, japes from local `plato` 938dad03, no provider calls, no database, minimal environment (`env -i`). macer pins japes 64d9099e (2.4.9).

## Result

macer's unit suite (`tests/`, 3484 tests) passes on 2.7.4 once one import is changed and its dependencies are re-locked, except two tests that fail on a newer `openai-agents` (not a japes change). The SDK surface its entry point uses is unchanged.

## What breaks

1. `src/macer/japes/main.py:25`: `from jazzx_sdk.queue_processor import QueueSettings` raises `ModuleNotFoundError` (the module moved to `jazzx_sdk.queue.processor` in 2.5.0; `from jazzx_sdk import QueueSettings` also works). It takes down `macer.japes.main`, `tests/test_japes_handler.py`, `tests/test_extract_process_id.py` and `tests/test_condition_dedup_model.py` at collection. With the import fixed: 3482 passed, 2 failed (below).
2. The lock must move, and a partial bump does not install. japes 2.7.4 requires `openai-agents>=0.22.0`, which requires `openai>=3`; macer's lock has `openai-agents` 0.17.6, `openai` 2.43.0 and `litellm` 1.103.10, and that litellm requires `openai<3`. A fresh resolve works (`litellm` 1.109.1, `openai` 3.53.0, `openai-agents` 0.24.0). Also new floors: `opentelemetry-*>=1.45.2` and `0.66b2` (macer's `<1.46.0` bound allows 1.45.2), `soupsieve>=4.0.0`, and new core dependencies `aiosqlite`, `oauthlib`, `sqlmodel`.
3. Two macer tests fail on `openai-agents` 0.24.0 and pass on 0.22.0 (`tests/test_repl.py::TestPythonReplTool::test_python_repl_success` and `::test_python_repl_error_path`: `python_repl.on_invoke_tool(MagicMock(), ...)` now returns the generic tool-error text). japes itself locks 0.24.0. The fix is on macer's side (the test's mock context) or a pin to `<0.24` until then.
4. Dual ownership of `jazzx_eval_contracts`: macer declares `jazzx-eval-contracts` directly (`pyproject.toml:32`, git subdirectory source at its japes rev), and japes 2.7.4 now ships that package in its own wheel. Both would install the same directory. macer drops its direct dependency and its `[tool.uv.sources]` entry for it in the same change as the japes pin (the `TODO(bundled-package-dual-ownership)` case). Its comment at `pyproject.toml:189` about japes' path dependency goes with it.

## What does not change

- `Handler` (`startup`, `shutdown`, `handle`), `HandlerContext` (same 13 fields, including `invocation_id`, `message`, `security_context`, `runtime`), `ResponseMessage` (`header`, `payload`, `status`, `error`), `QueueSettings` (same fields and defaults) and `JazzXRuntime.run_once()` are identical between 2.4.9 and 2.7.4. `JazzXRuntime.__init__` only gains `mcp_server_allowed_hosts` and `mcp_server_allowed_origins`; every keyword macer passes (`handler`, `queue_settings`, `knowledge_hub_url`, `request_headers_provider`) is unchanged, so job mode (`run_once`) behaves as before.
- `common`: macer's own `common` submodule is pinned to 3cb0a55d (v0.5.0), the same sha japes 2.7.4 carries, so `common.core.ai_gateway` and `common.core.telemetry.conventions` (imported by macer) resolve to identical code.
- `KnowledgeHubClient` and `KnowledgeHubAccessError` import from the same paths.

## Not checked

The e2e and integration suites (they need deployed services), mypy and ruff (macer's CI runs them, not run here), and any macer behavior that depends on the generated Knowledge Hub client revision (macer pins client-api 0b14d3d1; japes 96c42edb).
