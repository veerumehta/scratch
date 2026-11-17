# Poetry consumers and the two path dependencies

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Scope note, 2026-11-16. Decides nothing; the recommendation is at the end. Tests ran in `/tmp/poetry_scope_jp` (throwaway repo copies, Poetry 1.8.3 from a venv, uv 0.13.5).

## The problem

`pyproject.toml` declares `jazzx-eval-contracts` (extra `schema`) and `jazzx-plato-client` as `{ path = "...", develop = true }`. A Poetry consumer of japes as a git dependency locks them as directory sources and, on a clean install, looks for them under the consumer root (`Path /app/jazzx_eval_contracts ... does not exist`). Reproduced here with Poetry 1.8.3: `poetry lock` succeeds, `poetry install` fails. uv locks them as `git+...?subdirectory=` and works.

## 1. What consumes them

Both are hard imports of the core install, so neither can become an optional extra without making those imports lazy.

- `jazzx_eval_contracts`: 11 modules in `jazzx_sdk/evaluation/` (`scorers`, `metrics`, `agent_judge`, `judge_cache`, `citation_scorer`, `attribution_protocols`, `eval_service_adapters`, `custom_scorers`, `feedback/sink`), 16 test files.
- `jazzx_plato_client`: `jazzx_sdk/clients/plato_client.py`, `jazzx_sdk/pack/roots.py` (and `pack/store.py` mirrors its archive rules).
- Outside japes: `jaci` imports `jazzx_plato_client` (Dockerfile probe, `paths.py`, `publish_packs_to_plato.py`); `kernel-lab/codec-suite/workflows` declares both as git-subdirectory pins beside `japes`; `jazzx-assistant` and `juno` get them only through japes. `eval-service` depends on neither today.
- The core dependencies already cover what the two need (`pydantic`, `httpx`, `pyyaml`, `jsonschema`), so bundling adds no dependency.

## 2. Options

| | Poetry 1.8.3 consumer | uv consumer | Cost and risk |
|---|---|---|---|
| (a) publish to a feed | works | works | No Python package feed exists: CI publishes container images to GHCR only, and client-api is consumed as git subdirectory pins. A feed is new infrastructure, a release step per bump, and drift between the feed version and the repo. Not tested; heaviest. |
| (b) japes pins its own subdirectories by git rev | not tested; fails by construction | works | The rev must name a commit that already exists, so each release depends on its predecessor (chicken-and-egg), and the pin and the code drift apart. A consumer-side git subdirectory pin was already shown not to override the path source (opus-xrepo's repro). |
| (c) fold into `jazzx_sdk` as subpackages | works | works | Renames every import in jaci, kernel-lab and the tests; breaks `jazzx_plato_client`'s "no JazzX SDK" promise and eval-service's pydantic-only contracts. Largest change. |
| (d) optional extras | works | works | Needs both imports made lazy in the core; `jazzx_sdk.evaluation` and `jazzx_sdk.clients.plato_client` would fail without the extra. Not cheap. |
| (e) ship both inside the japes wheel | **works (tested)** | **works (tested)** | Two `packages = [{include = ..., from = ...}]` entries, two dependency lines removed. Import names unchanged. |

### (e) as tested

In a copy of the repo with the two dependency lines removed and `packages` extended with `{include = "jazzx_eval_contracts", from = "jazzx_eval_contracts"}` and `{include = "jazzx_plato_client", from = "jazzx_plato_client"}`:

- Poetry 1.8.3: `poetry lock` and a clean `poetry install` succeed, and `import jazzx_eval_contracts, jazzx_plato_client` resolves from site-packages. The as-is variant fails exactly as reported.
- uv: `uv lock` and `uv sync` succeed on the same repo, imports resolve.
- `poetry build -f wheel`: the wheel holds `jazzx_sdk`, `plato`, `common`, `jazzx_eval_contracts` (15 files) and `jazzx_plato_client` (10 files), and no tests or scripts.
- The two standalone distributions stay as they are in their own directories: `kernel-lab` keeps installing them by git subdirectory pin, and eval-service can depend on the contracts alone later. Version drift is gone for the bundled copy (one wheel, one release).

Known edges of (e), none blocking:

- An environment that holds both japes and a standalone `jazzx-eval-contracts` or `jazzx-plato-client` installs the same package twice (the later install wins). Pin both to the same rev or drop the standalone pin (`kernel-lab` is the only such consumer; it also depends on japes).
- `Dockerfile` can drop the first `COPY` of the two directories (they no longer need to resolve as path dependencies); the later `COPY` of their inner package directories stays. `import-boundaries.yml` and `.importlinter` treat them as separate roots and are unchanged.
- `poetry.lock` is regenerated (Poetry 2.x): the two directory entries leave it, nothing else moves.
- A consumer's existing lock still carries the old directory entries until it re-locks against the new japes.

## 3. Recommendation

(e). It is the only option that is cheap, keeps every import name, and works for both tools. It is not breaking for jaci, jazzx-assistant, juno (their imports stay, and their next re-lock drops the directory entries), Plato (it ships the same code), or eval-service (it does not depend on either).

A follow-up for later, not needed now: if `eval-service` starts depending on the contracts, it uses the standalone distribution by git subdirectory pin, as `kernel-lab` does.

One slip during the test: Poetry 1.8.3 inherited `VIRTUAL_ENV` from my shell and installed into `/Users/sangit/src/japes/.venv`; I restored that venv (japes editable from `japes-v27`, stray bundled files removed) and verified the imports resolve to the checkout.
