## Move macer from japes 2.4.9 to japes 2.7.4

macer now pins japes `c60775fb`, the 2.7.4 squash on japes `main` (JazzX-LLC/japes PR #123).

### What changes

1. `src/macer/japes/main.py`: `QueueSettings` is imported from `jazzx_sdk` (`jazzx_sdk.queue_processor` no longer exists; the module moved in japes 2.5.0).
2. `tests/test_repl.py`: the two `python_repl` tests call the tool with a real `ToolContext` instead of a `MagicMock`. A mock context fails on `openai-agents` 0.24. Test-only; no pin on `openai-agents`.
3. `pyproject.toml`: the direct `jazzx-eval-contracts` dependency, its `[tool.uv.sources]` entry and its override are gone. japes 2.7.4 ships that package inside its own wheel, so keeping both would put two distributions on one directory.
4. The `common` submodule is no longer vendored. japes ships `common` at the same sha macer pinned (3cb0a55d, v0.5.0), so `common.core.ai_gateway` and `common.core.telemetry.conventions` resolve from the japes install. Removed: the gitlink and `.gitmodules`, the Dockerfile `COPY common` and `PYTHONPATH`, `submodules: true` in the four workflows, and `.` from `dev-mode-dirs`.
5. The japes pin and `uv.lock`.

### Why

macer imports only a handful of SDK names (`Handler`, `HandlerContext`, `JazzXRuntime`, `ResponseMessage`, `QueueSettings`, `KnowledgeHubClient`, `KnowledgeHubAccessError`). They are the same between 2.4.9 and 2.7.4 apart from the one import path above; `JazzXRuntime.__init__` only gains two optional arguments macer does not pass.

### Lock effects

- `openai` 2.43 to 3.54, `openai-agents` 0.17.6 to 0.24.0, `litellm` 1.103.10 to 1.109.1. They move together: japes needs `openai-agents>=0.22.0`, which needs `openai>=3`, and an older `litellm` requires `openai<3`.
- `opentelemetry-*` 1.45.1 to 1.45.2, `soupsieve` 2.9.2 to 4.1.1. New: `aiosqlite`, `oauthlib`, `sqlmodel`.
- `jazzx-eval-contracts` leaves the lock as a separate package (it comes from the japes wheel); the lock holds no directory or local-path sources.
- The Kernel and Knowledge Hub client revisions move to the ones japes pins (client-api 96c42edb). macer's only direct use of a generated client is `e2e/hub.py` (`create_collection`); its request body and call still work at that revision.
- Leaves the lock because they are japes extras now: `anthropic`, `beautifulsoup4`, `lxml`, `pymupdf`, `python-docx`, `feedparser` and a few others. macer imports none of them. Use `japes[documents]` or `japes[anthropic]` in the dependency line if they are wanted at runtime.

### Verified, and not

- Verified: the unit suite (`tests/`, 3484 tests) passes on the exact lock, in a clean `uv sync --frozen` environment, with no database variables and no provider calls, and with no repo-root `common/` directory. A smoke import of the SDK names above, `jazzx_eval_contracts`, `jazzx_plato_client` and `common.core.ai_gateway` works on that environment. The four changed workflow files parse as YAML.
- NOT verified: the e2e and integration suites (they need deployed services), mypy and ruff in CI, a Docker build, and the CI runs themselves.

### For a decision

- The workflows' checkout step still passes `token: ${{ secrets.DEVOPS_JAZZX_TOKEN }}`. It was there for the private `common` submodule; the same token also serves the private japes and client-api dependencies in later steps, so I left it. Drop it from the checkout if you prefer the default token.

### Follow-up

A second PR can replace macer's direct `common.core.ai_gateway` calls (routing decision, settings, embeddings base URL) with `jazzx_sdk.llm.gateway`. That needs japes 2.7.5 (route settings and an embeddings accessor).
