# jazzx_sdk layout refactor — 2.3.0

**Owner:** Virendra Mehta
**Status:** Draft plan, not yet executed. Fact-checked against the working tree — see §12.
**Target release:** 2.3.0
**Scope:** directory/module placement inside `jazzx_sdk/` only. No behaviour change, no API semantics change.

---

## 1. Verdict

The subpackages are sound. `fabric/`, `evaluation/`, `llm/`, `agents/`, `modes/`, `experts/`, `conductor/` each have coherent internal shape, and the four-way `modes / experts / skills / agents` split is a real distinction (cognition primitive / orchestration surface / pack-implementable contract / LLM execution), not accidental drift.

The problem is the **root namespace**: 34 flat modules totalling 365 KiB, including the largest root-level file (`mock_services.py`, 63.4 KiB — third largest in the package overall, after `clients/knowledge_hub_client.py` at 89.8 KiB and `fabric/canonical/store.py` at 64.4 KiB) and a 41 KiB file holding five unrelated concerns (`tracing.py`).

The clearest evidence that the flat root has become load-bearing is that the code has started **inventing names to work around it**. `events_domain.py` exists only because `events.py` took the name, and its own docstring (lines 11–12) says so. Three unrelated modules are called some variant of "models". Three unrelated modules are called `server.py`.

`docs/ARCHITECTURE.md` is silent on whether the flat root is intentional — there is no statement defending it and none acknowledging it as debt. The refactor therefore contradicts no written principle, but it also has no written guidance to follow. §9 adds that guidance.

---

## 2. Headline: no breaking-change announcement is required

This was the open question. It resolves **no**, provided the plan below is followed as written.

The externally-owned consumers are `macer`, `juno`, and `jazzx-assistant`. Their dependency on the **root namespace** is six modules, none of which moves:

| Consumer | Root module | How reached | Breaks? |
|---|---|---|---|
| `macer` | `models` | `from jazzx_sdk.models import MessageHeader, MessageSource, MessageType, QueueMessage, Tracking` — **explicit submodule path** | No — does not move |
| `macer` | `queue_processor` | `from jazzx_sdk.queue_processor import QueueSettings` — **explicit submodule path** | No — does not move |
| `macer` | `handlers`, `runtime` | via the `jazzx_sdk` package root | No — root re-exports preserved |
| `juno` | `client_layer` | `from jazzx_sdk.client_layer import ClientLayer` (2 files; juno's *only* jazzx_sdk dependency) | No — does not move |
| `jazzx-assistant` | `handlers`, `models`, `queue_processor`, `runtime`, `concurrency` | mix of root and submodule paths | No — none move |

They also depend on **subpackages**, none of which is restructured here:

- `macer` → `jazzx_sdk.clients` (5 files: `findings_converter.py:49`, `jtbd_setup.py:25`, `los_entities.py:27`, `jtbd/rerun_orchestrator.py:61`, `utils/hub.py:10`)
- `jazzx-assistant` → `jazzx_sdk.agents` / `.agents.interactive` / `.agents.models` (5 files), `jazzx_sdk.clients.knowledge_hub_client`, `jazzx_sdk.tools`, `jazzx_sdk.streaming`, and **`jazzx_sdk.llm.cost`** (`src/jazzx_assistant/handler.py:31`)

That last one is worth noting: jazzx-assistant already imports `llm.cost` directly, which is the *destination* of the `utils/` migration in Phase 4. It is ahead of us, not behind.

**Every path the external consumers touch survives unchanged.** This is a design constraint on the plan, not a coincidence — it is the reason `messaging/` was dropped (§4.1).

Internally-owned consumers (`jaci`, `k9`, and japes' own `tests/`, `examples/`, `scripts/`) absorb the churn. `jaci`'s exposure is four one-line edits; `k9`'s is zero (§7.2).

### 2.1 Operational hazard that matters more than the pins

`macer/.venv`, `jaci/.venv`, and `juno/.venv` each contain a `site-packages/japes.pth` whose sole content is `/Users/sangit/src/japes`. Locally these three repos are **live path installs pointing at the working tree**. The git pins below give no local protection: the moment the refactor lands in the working copy, those three see it. (`jazzx-assistant` has no `.pth` — it has a real non-editable copy in site-packages.)

| Repo | Declared dependency | Ref type | Locked version |
|---|---|---|---|
| `macer` | `japes @ git+…@4b0885035ff6db1ab9f146d836254fb9eff76668` | pinned SHA | 1.9.8 |
| `jazzx-assistant` | `japes[mlflow]`, `[tool.uv.sources] rev = "4335551c96c3fb3e9eb1d569392f5df2b67ac514"` | pinned rev | 2.1.2 |
| `juno` | `japes = { git = …, branch = "main" }` | **floating `main`** | 1.4.5 |
| `jaci` | `japes[litellm] @ git+…@dev` | **floating `dev`** | 2.2.1 (`poetry.lock:1905`) / **2.0.0** @ `c5b972c2` (`uv.lock:1438`) |

⚠️ `jaci` has two lockfiles that disagree, and every repo's installed `dist-info` disagrees with its own lock (macer 2.2.4, jaci 2.2.4, juno 1.9.2, jazzx-assistant 1.9.8). Given the `.pth` overrides this is mostly moot, but do not treat any single lockfile as ground truth. All four are pinned *below* 2.3.0, so none sees this release until it chooses to.

Consequences for sequencing:

- **Do not land this on `dev` or `main` directly.** `jaci` floats on `dev` and `juno` floats on `main`; a merge to either breaks them on next resolve with no version-bump gate.
- Land on `refactor/sdk-layout-2.3`, get japes green, then merge to `dev` in the same window as the `jaci` fixes (§7.2).
- Anyone doing local cross-repo work against the `.pth` installs needs a heads-up regardless of the announcement decision. That is a Slack message, not a release note.

---

## 3. What moves

Four groupings. Everything else stays.

### 3.1 `observability/` — absorbs five root modules

`logging.py`, `tracing.py`, `observability.py`, `trace_source.py`, `mlflow_bridge.py` are four genuinely distinct concerns (emit logs / infra+agent spans / per-turn run tracer / read back into `CanonicalTrace`) plus one MLflow adapter. Their docstrings already cross-reference each other to explain the split — `observability.py:3` calls itself *"the missing middle in japes' tracing story"*, `trace_source.py:3` calls itself *"the read-back counterpart to `observability.RunTracer`"*. The boundary is deliberate. The flat layout is what makes it read as redundant.

```
observability/
├── __init__.py           # re-exports the eager-safe surface only — see §5.2
├── log.py                ← logging.py
├── telemetry.py          ← tracing.py · setup_telemetry, get_tracer, trace_method,
│                           async_trace_method (296), get_current_trace_id,
│                           get_current_span_id, add_span_attribute, record_event,
│                           _setup_instrumentations
├── agents_tracing.py     ← tracing.py · setup_agents_tracing, add_agents_trace_processor,
│                           extract_token_usage (692), _HAS_AGENTS (740)
├── agent_hooks.py        ← tracing.py · AgentTraceHooks, MlflowTraceHooks,
│                           _build_agent_trace_hooks (743), _build_mlflow_trace_hooks (933),
│                           _MissingExtra (1006), module __getattr__ (1013)   [LAZY ONLY]
├── _mlflow_runtime.py    ← tracing.py:682–689 · the module-scope mlflow try/except and the
│                           globals it binds: _mlflow, _mlflow_entities, _MlflowClient,
│                           _HAS_MLFLOW (687)                                  [LAZY ONLY]
├── trace_context.py      ← tracing.py · attach_incoming_trace_context (417),
│                           inject_current_trace_context (469),
│                           _attach_incoming_trace_context
├── mlflow_env.py         ← tracing.py · sanitize_leaked_otel_env_vars,
│                           flush_mlflow_async_trace_queue, _OTEL_LEAK_ENV_VARS,
│                           _MLFLOW_HTTP_REQUEST_TIMEOUT_S
├── run_tracer.py         ← observability.py  (RunTracer, RunHandle, SpanHandle, NoOpTracer,
│                           MlflowTracer, build_run_tags, resolve_tracer, _MlflowRun, _MlflowSpan)
├── trace_source.py       ← trace_source.py
└── mlflow_bridge.py      ← mlflow_bridge.py
```

Four things to note.

**The `agents_tracing.py` / `agent_hooks.py` split is not cosmetic.** Today `setup_agents_tracing` is imported eagerly by root `__init__.py:96` while `AgentTraceHooks` from the *same file* must be lazy, because it pulls `openai-agents`. That invariant currently holds by careful construction inside `tracing.py` (`_build_*` factories + a module-level `__getattr__` at line 1013 + `_MissingExtra`, and `_HAS_AGENTS` computed via `find_spec` rather than an import). Splitting the file makes it hold *structurally*: `agent_hooks.py` is never referenced from any `__init__.py`, so it cannot regress.

**`_mlflow_runtime.py` fixes a pre-existing eager-import wart, and that is a deliberate side effect.** `tracing.py:682–689` is a **module-scope** `try: import mlflow …`. Because root imports `tracing` eagerly, `import jazzx_sdk` **already imports mlflow today** whenever the `mlflow` extra is installed. Only `_build_mlflow_trace_hooks` (line 933) reads the resulting globals, and that is lazy-only — so isolating the try/except into `_mlflow_runtime.py`, imported only by `agent_hooks.py`, takes mlflow off the eager path.

⚠️ **Must verify before executing:** grep that nothing on the eager path reads `_HAS_MLFLOW`, `_mlflow`, `_mlflow_entities`, or `_MlflowClient`. If `extract_token_usage` or `mlflow_env.py` reads any of them, `_mlflow_runtime.py` becomes eager again and this side effect does not materialise. That is acceptable — the split is still correct — but Phase 1's verification must then not claim mlflow left the eager path.

**`observability.py` → `observability/` is a same-name module→package conversion.** Both cannot exist. Create the directory and `__init__.py` and `git mv jazzx_sdk/observability.py jazzx_sdk/observability/run_tracer.py` in a **single commit**, never as two.

**`log.py` is a readability rename, not a bug fix.** `jazzx_sdk/logging.py` does *not* shadow stdlib `logging` — `tracing.py:21`'s `import logging` already resolves to stdlib under Python 3 absolute imports. Rename it because `jazzx_sdk.observability.logging` would read badly, not because anything is broken.

### 3.2 `server/` — absorbs five root modules

All five are tier-3 concerns currently scattered across the root.

```
server/
├── __init__.py           # MUST be lazy-only — see §5.1
├── app.py                ← server.py          (ServerSettings, InvokeRequest, create_app)
├── web.py                ← web.py             (mount_spa)
├── governed_http.py      ← governed_http.py   (GovernedRouter, get_governed_context,
│                           set_governed_context, clear_governed_context)
├── settings_api.py       ← settings_api.py    (SettingField, SettingsStore,
│                           EnvFileSettingsStore, create_settings_router)
└── inbound.py            ← events.py          (event_router)
```

Precision on the fastapi dependency, because §5.1's warning depends on it: **module-scope** fastapi imports exist in `server.py:13`, `governed_http.py:20`, and `events.py:20`. `web.py:44` and `settings_api.py:99` import it **function-locally**, so importing those two pulls no fastapi today. Only `server.py` reaches uvicorn.

(Pre-existing bug worth a ticket: `events.py:13`'s docstring claims *"fastapi is imported inside the factory (Tier-3)"*, contradicted by its own line 20.)

`events.py` → `server/inbound.py` deserves justification: it is a FastAPI `APIRouter` factory, i.e. inbound HTTP transport, not an events abstraction. `ARCHITECTURE.md:160` canonicalises the path `jazzx_sdk.events.event_router`, so this **invalidates a documented public path**. Only two japes test files import it and no external consumer does, so the cost is one doc edit. See §4.2 for why the freed-up `events` name is *not* reused in 2.3.

### 3.3 Database session factories → `fabric/db/engine.py`

`tracing.py` lines **586–664** contain `_ensure_async_driver` (586), `create_agent_session` (593), `create_session_engine` (626), and the deprecated aliases `create_postgres_session` (652) / `create_postgres_engine` (660). Creating a SQLAlchemy engine is not tracing. `ARCHITECTURE.md:356–357` is explicit about the right home: *"a service reaches its own relational database **through** fabric, never importing `common.core.db` directly."*

```
fabric/db/engine.py     ← tracing.py lines 586–664
```

⚠️ **`_ensure_async_driver` (586) must move with them.** Both public factories call it. Moving only 593–664 raises `NameError` at first use.

**No lazy-import gymnastics are needed.** `jazzx_sdk.fabric` — including `fabric.db`, via `fabric/__init__.py:26` — is **already** on the eager base import path, by three independent routes:

- `__init__.py:121` → `trace_source.py:16` → `from jazzx_sdk.fabric.canonical.trace import CanonicalTrace` (module scope)
- `__init__.py:160` → `tools/__init__.py:63` → `jazzx_sdk.fabric.graph.triple`
- `__init__.py:172` → `pack/helper.py:21` and `pack/loader.py:18` → `jazzx_sdk.fabric.canonical.derived`, `jazzx_sdk.fabric.fabric`

So root `__init__.py` lines 105–108 simply retarget:

```python
from jazzx_sdk.fabric.db.engine import (
    create_agent_session, create_session_engine,
    create_postgres_session, create_postgres_engine,
)
```

`__all__` entries 275–278 are unchanged. No `_LAZY_ATTRS` change. Import cost is identical before and after.

### 3.4 `kernel_llm_model.py` → `agents/kernel_model.py`

Zero consumers anywhere — this, `settings.py`, and `_registry.py` are the only root modules with no importer outside their own package. (Several other root modules have zero *external* consumers but do have internal ones; §7.1 lists them.)

It subclasses the openai-agents `Model` ABC at line 14 (`from agents import Model`, module scope), which is what `agents/models.py:153`'s `RetryingModel(Model)` does. Taxonomy by base class puts it in `agents/`. Note `agents/anthropic_model.py:101` subclasses `LitellmModel`, not `Model` directly — so "peer of anthropic_model" is loose; "peer of `RetryingModel`" is exact.

It does **not** belong in `llm/providers/` despite the doc's provider taxonomy (ARCHITECTURE.md 432–436): it does not implement `BaseProvider`, and filing an agents-runtime adapter under the lower LLM layer would invert the documented two-layer rule (line 425: *"Foundational multi-provider LLM service below Agent Execution Layer"*).

The module-scope `from agents import Model` is safe only because `jazzx_sdk.agents` is **not** on the eager path (verified). **Do not add `kernel_model` to `agents/__init__.py`'s re-exports** if that would drag it anywhere eager; leave it reachable by full path only.

While moving it, ticket — do not silently fix — the pre-existing defects: `ModelResponse(content=…, raw_response=…)` at line 138 is not the real Agents-SDK signature; `stream_response` yields the whole response as one event (line 185); four open TODOs; no tool/handoff/`output_schema` support (TODO at 122).

### 3.5 `mock_services.py` → `clients/mocks.py`, and `deployed_posture` out of it

63.4 KiB of dev/test doubles at the top of the public package. The audit turned up something worse than misplacement: **the SDK's own production code imports its mocks module.**

- `jazzx_sdk/client_layer.py:273, 509, 515, 521`
- `jazzx_sdk/fabric/__init__.py:64`
- `jazzx_sdk/fabric/fabric.py:109, 296`
- `jazzx_sdk/settings_api.py:101`

And `settings_api.py:101` sources the **production** fail-safe `deployed_posture()` from it.

```
clients/mocks.py        ← mock_services.py
env.py                  ← mock_services.deployed_posture
```

✅ **The §3.5 content audit passed.** `mock_services.py` contains exactly `deployed_posture`, `MockKernelClient`, `_schema_for_entity_type`, `MockKnowledgeHubClient`, `MockProcessClient` — all client doubles. No mock stores, no mock fabric surfaces. `clients/mocks.py` is the right destination and **no `testing/` package is needed.** (`MockProcessClient` has no non-mock sibling in `clients/`, which is a curiosity, not a blocker.)

No cycle: `mock_services.py`'s only internal import is `jazzx_sdk.env`, function-local at line 34. `clients/` does not import it today.

**Real call-site count: 26 hit lines across 18 japes files + 1 jaci file** — 13 japes test files, 5 non-test japes sites (the four SDK modules above plus `scripts/check_kh_connection.py:29`), and `jaci/src/jaci/scenarios/ci_spread/ui/demo_page.py:137`. All ours, all mechanical, but the four in-SDK sites make this a *production* edit, not a test-only one. Note japes tests import the private `_schema_for_entity_type` (`tests/test_mock_entity_validation.py:10`).

`deployed_posture` has **four** call sites, not one: `settings_api.py:101`, `client_layer.py:273`, `fabric/fabric.py:109`, `tests/test_integration_followups.py:173`.

---

## 4. What deliberately does **not** move

Five candidates were rejected or deferred on evidence. Recording the reasoning so they don't get re-proposed.

### 4.1 `messaging/` (`models.py` + `handlers.py` + `queue_processor.py`) — rejected

Four independent reasons, any one sufficient:

1. **It is the only proposal that breaks an external consumer.** `macer` path-couples to `jazzx_sdk.models` and `jazzx_sdk.queue_processor`. Dropping `messaging/` is what turns this refactor from "announce a breaking change" into "no announcement".
2. **The handler interface is above all transports, not inside one.** ARCHITECTURE.md:1119 — *"The handler interface is the only contract."* Line 175 — *"Because every path (Job Mode, Server Mode `/invoke`, inbound `event_router`) invokes the wrapped `Handler`, wrapping once covers them all."* Filing `Handler` inside a transport package inverts that.
3. **The name is actively misleading.** `channels/` already exists and ARCHITECTURE.md:166 calls it *"**Message** channels"*. A package called `messaging/` containing neither `channels` nor `events` will mislead every reader.
4. **It sits on the hot import path.** All three are eagerly imported by root `__init__.py` (46, 57, 80). A `messaging/__init__.py` would load for every Tier-1 consumer, buying nothing.

`handlers.py` is still 21.4 KiB mixing the Handler protocol with identity/header propagation. That is a **file-internal** split (`handlers.py` + `identity.py`, both at root, `handlers` re-exporting) and is deferred to 2.4 — it is the most widely imported root module in the estate (81 import lines across 64 files repo-wide; 44 lines in japes, 37 outside it), and japes tests reach the private `_security_context_headers` (`tests/test_consistency_enrichment.py:66`).

### 4.2 `events_domain.py` → `events.py` — deferred to 2.4

The rename is right: the `_domain` suffix is a workaround, not a design. But doing it in the same release that frees the `events` name creates a **silent semantic swap** — `from jazzx_sdk.events import event_router` would raise `ImportError: cannot import name` against a module that exists but now means something entirely different, instead of a clean `ModuleNotFoundError`. `jaci` has four files importing `events_domain`.

Two-step instead:

- **2.3** — router moves to `server/inbound.py`; `jazzx_sdk.events` ceases to exist; `events_domain.py` stays put.
- **2.4** — with `jazzx_sdk.events` absent for a full version, promote `events_domain.py` → `events/`, moving its W3C traceparent helpers (`trace_id_from_traceparent`, `traceparent_from_tracking`, `otel_ids_from_tracking`) to `observability/trace_context.py` where that vocabulary already lives.

### 4.3 `portfolio.py` → `fabric/collections/` or `finance/` — rejected, stays at root

Corrected reasoning (an earlier draft of this plan got the evidence wrong on both alternatives):

- **`fabric/collections/` contradicts its documented charter.** ARCHITECTURE.md:376–377 defines it as *"collection-level operations **not specific to a single store's typed model**"*. `Portfolio` is precisely a typed model.
- **`finance/` is a charter mismatch too, though not an import-safety one.** `finance/__init__.py` is *"Financial spreading: the reusable schema, export, and metrics for lending packs"* — portfolio monitoring is not spreading. Note that the import-safety objection does **not** hold: `finance/excel.py` imports openpyxl function-locally (lines 23, 37, 69, 89, 124; its docstring at line 7 says so explicitly), and `jazzx_sdk.finance` is already eager anyway via `trace_source` → `fabric.canonical.condition_evaluator:19` → `expressions/evaluate.py:34` → `finance.vocabulary`.
- **Root is correct on the merits.** `portfolio.py` imports nothing from `jazzx_sdk`. Zero internal dependencies is the root-foundation test in P8 (§9.1). It passes.

### 4.4 `platform_catalog.py` → `modes/` — rejected; fix the duplication instead

`modes/catalog.py:70` already defines `MODE_REGISTRY` with exactly 13 mode contracts. `modes/platform_catalog.py` next to it is a naming collision waiting to confuse, and the module is genuinely platform-wide — it aggregates `MODES`, `MODE_KINDS`, `MODE_KIND_LABELS`, `MODE_GROUPS`, `EXPERTS`, `FABRIC_SURFACES`, `CANONICAL_OBJECTS`. Filing a platform-wide inventory under one domain contradicts the doc's per-domain registry pattern (`MODE_REGISTRY` in `modes`, `EXPERT_REGISTRY` in `experts`, `CONNECTOR_REGISTRY` in `connectors`).

The real defect is not location — it is that `platform_catalog.MODES` **restates** the 13 keys `modes/catalog.py` owns (verified set-identical). Fix that instead: derive `MODES` from `modes.catalog.MODE_REGISTRY` and keep only the presentation layer (emoji display labels, `MODE_GROUPS`) local.

⚠️ `jaci/ui/platform_view.py:71–81` imports seven symbols from it inside a `try/except ImportError` with a hardcoded local fallback that sets `_SOURCE = "local fallback …"`. If this module ever moves or loses a symbol, jaci degrades **silently** to stale data rather than failing. Worth fixing on the jaci side independently.

### 4.5 `odata.py` — stays at root, on the merits

An earlier draft called this a low-value deferral based on "one consumer (a japes test)". That was wrong. There are three, two of them production SDK modules in **different subpackages**:

- `jazzx_sdk/fabric/canonical/store.py:33`
- `jazzx_sdk/tools/discovery.py:19`
- `tests/test_odata.py:3`

A 650-byte string helper shared by two subpackages and depending on nothing is exactly what the root is for. It also sits on the eager base import path via `tools` → `tools.discovery`. It stays, and P8 (§9.1) explains why.

### 4.6 Preempting the `documents/` objection

ARCHITECTURE.md:554–555 is an explicit refusal to create a subpackage: *"Lives in one module, `jazzx_sdk/tools/documents.py`, re-exported from `jazzx_sdk.tools` — not a separate `documents/` package; there is no `jazzx_sdk.documents`."*

A reviewer will cite this. The distinction, on the record: **that ruling is about not fragmenting one cohesive module into a package. This refactor is about grouping already-separate sibling modules.** The documents ruling opposes splitting; it says nothing about grouping. `server/` absorbs five existing files and creates none. `observability/` absorbs five and *does* split one — but `tracing.py`'s split is demanded by the tier model, not by tidiness: the eager/lazy boundary inside that file is currently maintained by hand, and §3.1 makes it structural.

---

## 5. The two invariants that must not regress

### 5.1 P5 — tiers 1 and 2 stay server-free

`server/__init__.py` is the single highest-risk file in this refactor. If it eagerly re-exports from `app.py`, importing *any* `server/` submodule pulls fastapi and uvicorn, and P5 is violated at the package level.

It must be lazy-only:

```python
"""Tier-3 server runtime. Nothing here is imported eagerly by jazzx_sdk/__init__.py.

WARNING: this __init__ must never import .app, .governed_http, or .inbound at module
scope — all three import fastapi at module scope, and .app reaches uvicorn. (.web and
.settings_api import fastapi function-locally, but keep them lazy here too, for one
rule rather than two.) Tiers 1 and 2 — jazzx_sdk.contracts / .evaluation / .runtime —
must stay server-free: see docs/ARCHITECTURE.md P5 and tests/test_import_boundary.py.
"""

from typing import Any

_LAZY: dict[str, str] = {
    "ServerSettings":         "jazzx_sdk.server.app",
    "InvokeRequest":          "jazzx_sdk.server.app",
    "create_app":             "jazzx_sdk.server.app",
    "mount_spa":              "jazzx_sdk.server.web",
    "GovernedRouter":         "jazzx_sdk.server.governed_http",
    "get_governed_context":   "jazzx_sdk.server.governed_http",
    "set_governed_context":   "jazzx_sdk.server.governed_http",
    "clear_governed_context": "jazzx_sdk.server.governed_http",
    "SettingField":           "jazzx_sdk.server.settings_api",
    "SettingsStore":          "jazzx_sdk.server.settings_api",
    "EnvFileSettingsStore":   "jazzx_sdk.server.settings_api",
    "create_settings_router": "jazzx_sdk.server.settings_api",
    "event_router":           "jazzx_sdk.server.inbound",
}

def __getattr__(name: str) -> Any:
    if name in _LAZY:
        import importlib
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__() -> list[str]:
    return sorted(_LAZY)
```

Useful side effect: this dict is what keeps `jaci/src/jaci/main.py:31` and `k9`'s three server tests working with **zero edits** (§7.2).

### 5.2 `observability/__init__.py` — eager-safe surface only, and no `trace_source`

Two exclusions, for different reasons.

**Exclude `agent_hooks` and `_mlflow_runtime`** — they pull openai-agents and mlflow. That is the whole point of §3.1.

**Exclude `trace_source` — this one is subtle and would introduce a fragile cycle.** Today `observability.py` imports only `jazzx_sdk.concurrency` (line 22), while `trace_source.py:16` imports `fabric.canonical.trace` at module scope. If `observability/__init__.py` re-exported `trace_source`, then `import jazzx_sdk.observability` would pull `fabric.canonical` → `fabric/canonical/condition_evaluator.py:18` → `from jazzx_sdk.conductor.pipeline import ExecutionKind`. And `conductor/engine.py:43`, `conductor/fanout.py:18`, `conductor/replication.py:34` all import `jazzx_sdk.observability` — giving **conductor → observability → fabric → conductor**, which would survive only because `conductor/__init__.py` happens to import `.pipeline` (line 9) before `.engine` (line 17). Anyone reordering that file would break the package.

So: `observability/__init__.py` re-exports from `log`, `telemetry`, `mlflow_env`, `agents_tracing`, `trace_context`, and `run_tracer` only. Root `__init__.py` keeps importing `TraceSource` / `MlflowTraceSource` by full path, exactly mirroring today's line 121:

```python
from jazzx_sdk.observability import (           # replaces lines 86–120
    setup_logger, get_logger, LogFormat, SDKLogger,
    sanitize_leaked_otel_env_vars, flush_mlflow_async_trace_queue,
    setup_telemetry, setup_agents_tracing, add_agents_trace_processor,
    get_tracer, trace_method, async_trace_method,
    get_current_trace_id, get_current_span_id, add_span_attribute, record_event,
    RunTracer, RunHandle, SpanHandle, NoOpTracer, MlflowTracer,
    build_run_tags, resolve_tracer,
)
from jazzx_sdk.observability.trace_source import TraceSource, MlflowTraceSource   # was line 121
```

Note `mlflow_bridge` is **not** on the eager path today either — `trace_source.py:36` imports it function-locally. Do not re-export it from `__init__.py`; that would newly eagerise it.

This collapses four import blocks (lines 86–120, 35 lines) into one, and preserves the existing dependency graph exactly.

---

## 6. The import-boundary guard fails *vacuously* — fix this first

`tests/test_import_boundary.py` is the mechanism ARCHITECTURE.md:54 cites as enforcing the tier model. It names modules by literal dotted string:

```python
_SERVER_STACK = ("uvicorn", "jazzx_sdk.server", "jazzx_sdk.web",
                 "jazzx_sdk.launcher", "jazzx_sdk.mcp.server")
```

and asserts none of them land in `sys.modules`.

**If `jazzx_sdk.web` moves and nobody updates this tuple, the string never appears in `sys.modules`, `_probe` returns `""`, and the test passes — forever, for the wrong reason.** Green tests, dead guard. A real regression (uvicorn pulled into tier 1) would go undetected until someone noticed container size or cold-start time.

This is the most dangerous single item in the refactor, and it is dangerous *whether or not* someone remembers to update the tuple — because nothing forces them to. Harden it before moving anything:

```python
def test_server_stack_entries_all_resolve():
    """Guard the guard: every _SERVER_STACK entry must name a real module.

    Without this, moving or renaming a module silently turns the boundary tests into
    no-ops that pass vacuously — the string simply never appears in sys.modules.

    Note find_spec("jazzx_sdk.mcp.server") imports the parent package jazzx_sdk.mcp
    into *this* process. Harmless: the boundary probes above each run in a fresh
    subprocess, so pytest-process pollution cannot affect them.
    """
    import importlib.util
    for mod in _SERVER_STACK:
        assert importlib.util.find_spec(mod) is not None, (
            f"{mod} in _SERVER_STACK does not exist — the import-boundary tests "
            f"are passing vacuously. Update _SERVER_STACK."
        )
```

Then, in the same commit as the `server/` move, change **only the `web` entry**:

```python
_SERVER_STACK = ("uvicorn", "jazzx_sdk.server", "jazzx_sdk.server.web",
                 "jazzx_sdk.launcher", "jazzx_sdk.mcp.server")
```

⚠️ **Keep the bare `"jazzx_sdk.server"` entry.** An earlier draft replaced it with `"jazzx_sdk.server.app"`; that is strictly *weaker*. Once `server/` is a package, importing any submodule puts `jazzx_sdk.server` in `sys.modules`, so the bare entry becomes a **broader** sentinel that also catches a tier-1 regression arriving via `server/governed_http.py` or `server/inbound.py` — both of which import fastapi at module scope. Narrowing it to `.app` would blind the guard to exactly those two.

Two related notes:

- `launcher.py` **stays at root.** It is in `_SERVER_STACK` and in `_LAZY_ATTRS`, and `tests/test_launcher.py:24` monkeypatches it by string. Moving it into `server/` would split the tier-3 stack across two locations and weaken what the guard locks, for no gain. Accept the asymmetry.
- `contracts.py` and `runtime.py` also stay at root. `test_contracts_surface_is_server_free` and `test_queue_runtime_import_is_server_free` `_probe` them by literal import in a subprocess and assert `returncode == 0`, so moving either **hard-fails** rather than failing vacuously. (Hard-fail is the better failure mode, but neither needs to move.)
- `find_spec("uvicorn")` is safe: uvicorn is a non-optional dependency (`pyproject.toml:24`).

---

## 7. Consumer impact

### 7.1 Path changes, complete list

Counts are verified hit-line/file counts, `.venv` / `__pycache__` / `node_modules` excluded. "In-SDK" means inside `jazzx_sdk/` itself — these are production edits, and an earlier draft of this plan omitted most of them.

| Old path | New path | External | In-SDK | japes tests/examples/scripts | jaci / k9 |
|---|---|---|---|---|---|
| `jazzx_sdk.logging` | `jazzx_sdk.observability.log` | 0 | 0 | 2 | – |
| `jazzx_sdk.tracing` | `jazzx_sdk.observability.{telemetry,agents_tracing,agent_hooks,trace_context,mlflow_env}` | 0 | **5** — `handlers.py:273`, `runtime.py:311`, `server.py:160`, `events.py:121`, `agents/interactive/agent.py:45` | 6 | – |
| `jazzx_sdk.tracing` (DB factories) | `jazzx_sdk.fabric.db.engine` | 0 | 1 (`__init__.py:105–108`) | 2 | – |
| `jazzx_sdk.observability` | `jazzx_sdk.observability` (module → package, same symbols) | 0 | 3 (`conductor/{engine,fanout,replication}.py`) | 3 | **k9 3 — no edit** |
| `jazzx_sdk.trace_source` | `jazzx_sdk.observability.trace_source` | 0 | 1 (`__init__.py:121`) | 1 | – |
| `jazzx_sdk.mlflow_bridge` | `jazzx_sdk.observability.mlflow_bridge` | 0 | 1 (`trace_source.py:36`) | 1 | – |
| `jazzx_sdk.server` | `jazzx_sdk.server` (module → lazy package, same symbols) | 0 | 0 | 6 | jaci 1, **k9 3 — no edit** |
| `jazzx_sdk.web` | `jazzx_sdk.server.web` | 0 | 0 | 2 | – |
| `jazzx_sdk.governed_http` | `jazzx_sdk.server.governed_http` | 0 | 1 (`runs/server.py:20`) | 1 | – |
| `jazzx_sdk.settings_api` | `jazzx_sdk.server.settings_api` | 0 | 0 | 1 | **jaci 1** |
| `jazzx_sdk.events` | `jazzx_sdk.server.inbound` | 0 | 0 | 2 | – |
| `jazzx_sdk.kernel_llm_model` | `jazzx_sdk.agents.kernel_model` | 0 | 0 | 0 | – |
| `jazzx_sdk.mock_services` | `jazzx_sdk.clients.mocks` | 0 | **4** — `client_layer.py`, `fabric/__init__.py:64`, `fabric/fabric.py`, `settings_api.py:101` | 13 tests + `scripts/check_kh_connection.py:29` | **jaci 1** |
| `mock_services.deployed_posture` | `jazzx_sdk.env.deployed_posture` | 0 | **3** — `settings_api.py:101`, `client_layer.py:273`, `fabric/fabric.py:109` | 1 | – |
| `jazzx_sdk.utils` | `jazzx_sdk.llm.cost` / `.llm.model_identity` | 0 | 1 (`__init__.py:179`) | 0 | **jaci 2** |

**External sites: zero across the board.** That is the plan's central claim and §2 is its evidence.

### 7.2 `jaci` — four files; `k9` — none

| Repo | File | Change |
|---|---|---|
| jaci | `src/jaci/settings_fields.py:14` | `from jazzx_sdk.settings_api import …` → `from jazzx_sdk.server import …` (also update the docstring mention at line 5) |
| jaci | `src/jaci/settings.py:13` | `from jazzx_sdk.utils import parse_model_tier` → `from jazzx_sdk.llm.model_identity import parse_model_tier` |
| jaci | `src/jaci/hooks.py:22` | `from jazzx_sdk.utils import compute_cost_from_metrics` → `from jazzx_sdk.llm.cost import compute_cost_from_metrics` |
| jaci | `src/jaci/scenarios/ci_spread/ui/demo_page.py:137` | `from jazzx_sdk.mock_services import MockKnowledgeHubClient` → `from jazzx_sdk.clients.mocks import …` |

`jaci`'s other 202 files / 496 jazzx_sdk import lines are untouched, including all 30 files importing `HandlerContext` and all 5 importing `jazzx_sdk.ui`.

**`k9` needs no edits, but only because of the package re-exports.** It was scanned (an earlier draft wrongly listed it as unscannable). Its six touchpoints all resolve through §5.1's `_LAZY` dict or §5.2's `observability/__init__.py`:

- `src/ontology_generator/japes/handler.py:25` — `from jazzx_sdk.observability import RunTracer, build_run_tags, resolve_tracer`
- `scripts/demo_gold_cases_observability.py:42` — `from jazzx_sdk.observability import RunHandle, RunTracer, SpanHandle`
- `tests/unit/japes/test_handler.py:389` — `from jazzx_sdk.observability import NoOpTracer`
- `tests/test_api_server.py:14` — `from jazzx_sdk.server import ServerSettings, create_app`
- `tests/integration/test_ontology_upload.py:14, :22` — `from jazzx_sdk.server import create_app` / `ServerSettings`

This makes `create_app` in the `_LAZY` dict and the seven `run_tracer` symbols in `observability/__init__.py` **load-bearing for k9**. Do not trim either surface.

### 7.3 String-based monkeypatch targets — the silent breakers

`monkeypatch.setattr("dotted.path", …)` does not follow re-exports. These break silently:

| Site | Target | Status |
|---|---|---|
| `tests/test_kernel_client_headers.py:152` | `"jazzx_sdk.tracing.inject_current_trace_context"` | **BREAKS** → `"jazzx_sdk.observability.trace_context.inject_current_trace_context"` |
| `tests/test_completion_hooks.py:78` | `"jazzx_sdk.failures.classify_failure"` | safe — `failures.py` stays |
| `tests/test_launcher.py:24` | `"jazzx_sdk.launcher.launch_streamlit"` | safe — `launcher.py` stays |
| `tests/test_failures.py:206`, `test_trace_context_propagation.py:190`, `test_integration_followups.py:11,29` | `import jazzx_sdk.failures as …` / `jazzx_sdk.handlers as …` | safe — both stay |
| `tests/test_queue_processor.py:14`, `test_channels.py:18` | `from jazzx_sdk import net_safety` + `setattr(net_safety, …)` | safe — module object, and stays |

Also: japes tests import the privates `_HAS_AGENTS` and `_HAS_MLFLOW` from `jazzx_sdk.tracing`. They land in `observability/agents_tracing.py` and `observability/_mlflow_runtime.py` respectively; update the tests.

Merge gate: `rg -n 'monkeypatch\.setattr\("jazzx_sdk\.'` must return zero hits naming a moved module.

---

## 8. Phases

Each phase is independently mergeable and leaves the tree green. Phase 0 is worth landing on its own regardless of whether the rest proceeds.

### Phase 0 — bugs and guard hardening (no moves)

1. **Delete the phantom import.** `__init__.py:192` has `from jazzx_sdk.agent_utils import DebugHooks, DebugHooksStats, LLMTurnStats, create_size_limit_filter` inside a `try/except ImportError`. There is no `jazzx_sdk/agent_utils`, so `_AGENT_UTILS_AVAILABLE` is permanently `False` and all four names permanently `None` — silently dead. **Delete the block.**
   ⚠️ Related and already broken: `examples/document_analyzer/handler.py:35` has a live `from jazzx_sdk.agent_utils import DebugHooks, create_size_limit_filter`, which raises today. The example ships its own local `examples/document_analyzer/agent_utils/` package (`__init__.py`, `hooks.py`, `input_filter.py`) supplying exactly those names. Repoint the example at its own package; that is the whole fix.
2. **Route the public API off its own deprecated shim.** `utils/__init__.py` is a pure re-export of `llm.cost` + `llm.model_identity`, and root `__init__.py:179` still imports from `jazzx_sdk.utils`. Point it at the real modules.
3. **Add `test_server_stack_entries_all_resolve`** (§6). This must land *before* any move.
4. **Add a root `__all__` regression test.** Nothing currently asserts on `jazzx_sdk.__all__` (116 entries), so an accidental removal from the public surface is caught by nobody. Snapshot it.
5. **Capture an eager-import baseline.** `python -X importtime -c "import jazzx_sdk" 2>&1 | awk '{print $NF}' | sort -u > docs/_importtime_baseline.txt` (or equivalent). Every later phase diffs against this. This replaces absolute claims like "no mlflow on the eager path" — which is currently **false**, since `tracing.py:682–689` imports mlflow at module scope — with a relative check that cannot be wrong about the starting state.
6. **Move `deployed_posture()` out of `mock_services.py` into `env.py`** and update its **four** call sites (`settings_api.py:101`, `client_layer.py:273`, `fabric/fabric.py:109`, `tests/test_integration_followups.py:173`). A production fail-safe should not be sourced from a mocks module. Safe: it depends on nothing but `env()`.

**Verify:** full suite; `python -c "import jazzx_sdk"` clean; `pytest tests/test_import_boundary.py -v` shows the new test passing non-vacuously; baseline file committed.

### Phase 1 — `observability/`

Create the package, `git mv` the five modules, split `tracing.py` per §3.1 (including `_mlflow_runtime.py` and its must-verify grep), write `__init__.py` per §5.2, collapse root `__init__.py` lines 86–120, retarget the two `_LAZY_ATTRS` hooks entries to `jazzx_sdk.observability.agent_hooks`.

Rewrite **all eleven** importers, not just the tests: the five in-SDK sites (`handlers.py:273`, `runtime.py:311`, `server.py:160`, `events.py:121`, `agents/interactive/agent.py:45`), the six japes tests/examples, the `test_kernel_client_headers.py:152` monkeypatch string, and the `_HAS_AGENTS` / `_HAS_MLFLOW` test imports.

**Verify:** full import-boundary suite; `-X importtime` diff against the Phase 0 baseline must show **no additions** (and, if the `_mlflow_runtime` grep came back clean, mlflow *removed* — a win to record, not a requirement); `__all__` snapshot unchanged; confirm `from jazzx_sdk.observability import RunTracer, NoOpTracer, RunHandle, SpanHandle, build_run_tags, resolve_tracer` still works for k9.

### Phase 2 — `server/`

Create the package with the lazy `__init__.py` from §5.1, `git mv` the five modules, update `_SERVER_STACK`'s `web` entry only (§6), update `_LAZY_ATTRS`, rewrite the two in-SDK/japes importers of `governed_http` and the japes-internal `web` / `events` imports.

**Verify:** import-boundary suite; `test_server_symbols_still_resolve_lazily` green; `-X importtime` diff clean; actually start the server and hit `/health`, `/invoke`, `/stream`; confirm `from jazzx_sdk.server import ServerSettings` (jaci) and `from jazzx_sdk.server import ServerSettings, create_app` (k9) both resolve.

### Phase 3 — targeted moves

`fabric/db/engine.py` (lines **586**–664, including `_ensure_async_driver` — §3.3), `agents/kernel_model.py`, `clients/mocks.py` with its **18 japes + 1 jaci** call sites, four of them inside the SDK.

**Verify:** full suite; `-X importtime` diff clean; `rg -n 'jazzx_sdk\.mock_services'` returns zero across japes, jaci, and k9.

### Phase 4 — shim removal

⚠️ **None of these three shims is dead code.** An earlier draft called them dead and would have broken the build.

1. `llm/sanitize.py` is imported by **production** code at `llm/__init__.py:37`, and `tests/test_llm_sanitize.py:31` asserts *"re-export still works"*. Repoint `llm/__init__.py` at `jazzx_sdk.sanitize`, delete or rewrite the test, then delete the shim.
2. `fabric/pack/__init__.py` is imported by `tests/test_domain_pack_helper.py:6`. Repoint the test at `jazzx_sdk.pack`, then delete.
3. `utils/` — delete only after Phase 0 step 2 **and** the two jaci edits (§7.2) have landed.

**Verify:** `rg -n 'jazzx_sdk\.(utils|llm\.sanitize|fabric\.pack)'` returns zero across japes, jaci, and k9. Note jazzx-assistant already imports `jazzx_sdk.llm.cost` directly (`handler.py:31`) and is unaffected.

### Phase 5 — documentation

1. Rewrite the Repository Structure tree, ARCHITECTURE.md:906–939. It is already severely stale — it lists 7 root modules (including `__init__.py`) and 2 subpackages against a real 34 and 23.
2. Bump ARCHITECTURE.md:4 from `2.1.3` to `2.3.0`. (`pyproject.toml` and `_version.py` already say 2.3.0.)
3. Fix moved-module references: line 1083 (`tracing.py`'s `create_agent_session`), line 160 (`jazzx_sdk.events.event_router`).
4. Add the two policy sections in §9. P1–P7 exist, so a new **P8** numbers correctly.
5. `japes/CLAUDE.md` is a symlink to `/Users/foo/src/research/.scratch/sang/ape/CLAUDE.md`, outside this repo. Its content could not be verified from this session; check and update it wherever it actually lives.

### Deferred to 2.4

`events_domain.py` → `events/` (§4.2) · `handlers.py` internal split (§4.1) · `platform_catalog.MODES` deriving from `modes.catalog` (§4.4) · the `kernel_model.py` correctness fixes (§3.4) · `events.py:13`'s wrong docstring (§3.2) · `jaci/ui/platform_view.py`'s silent fallback (§4.4).

---

## 9. Policy the doc is missing

`docs/ARCHITECTURE.md` has no module-placement policy and no deprecation policy. That is why the root drifted: there was no written rule to violate. Add both.

### 9.1 Module placement

> **P8 — Placement follows concern; the root is for foundation and entry points only.**
> A module lives at the root of `jazzx_sdk` only if (a) it is cross-cutting foundation that
> subpackages depend on and that depends on no subpackage — `env`, `sanitize`, `concurrency`,
> `failures`, `odata`, `portfolio`, `_registry`, `_version`, `contracts` — or (b) it is a tier entry
> point: `runtime`, `client_layer`, `settings`, `launcher`. The test for (a) is mechanical: the
> module imports nothing from `jazzx_sdk.*`, and two or more subpackages import it.
> Everything else lives in the subpackage matching its concern.
>
> Three or more root modules sharing a concern is a subpackage, not a naming convention. If a module
> needs a suffix to avoid colliding with a sibling (`events_domain`), the namespace is wrong, not the
> name.
>
> This does not license splitting a cohesive module into a package — see the Unified Documents
> ruling. Group siblings; do not fragment single modules. The one exception is a file whose contents
> straddle a tier boundary that is currently maintained by hand (`tracing.py`'s eager/lazy split):
> there, splitting makes an invariant structural rather than conventional.

### 9.2 Deprecation

There is already house style to codify: `tracing.py:652–664` keeps `create_postgres_session` / `create_postgres_engine` as thin aliases that `warnings.warn(…, DeprecationWarning)` and delegate.

> **Deprecation policy.** A renamed or relocated public symbol keeps a delegating alias at its old
> path for one minor version, emitting `DeprecationWarning` naming the new path (pattern:
> `jazzx_sdk/fabric/db/engine.py`'s postgres aliases). Removal happens in the following minor.
> A relocated *module* whose old path has zero import sites outside this repo may be moved without
> an alias, provided the audit establishing "zero" is recorded in the release notes.

Note the doc currently holds both stances unreconciled — *"Clean break from legacy - no backward compatibility cruft"* (383) versus *"Backward compatibility maintained"* (1005, 1013). Pick one and say which applies where.

---

## 10. Risk register

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Import-boundary guard passes vacuously after a move | **High** — silent loss of P5 enforcement | Phase 0 step 3 lands the existence assertion *before* any move; §6 keeps the bare `"jazzx_sdk.server"` sentinel |
| 2 | `server/__init__.py` eagerly imports `app.py` → fastapi/uvicorn on the Tier-1 path | **High** | Lazy-only `__init__` (§5.1) + the guard + importtime diff in Phase 2 |
| 3 | `observability/__init__.py` reaches `agent_hooks` or `_mlflow_runtime` → openai-agents/mlflow eagerly | **High** | Structural split (§3.1); both referenced only from `_LAZY_ATTRS` / `agent_hooks` |
| 4 | `observability/__init__.py` re-exports `trace_source` → **conductor → observability → fabric → conductor**, surviving only on `conductor/__init__.py` line ordering | **High** | §5.2 excludes `trace_source`; root imports it by full path, preserving today's graph exactly |
| 5 | Moving `tracing.py:593–664` without `_ensure_async_driver` (586) → `NameError` at first use | Medium | Range corrected to 586–664 (§3.3) |
| 6 | `mock_services` move is a **production** edit — 4 in-SDK call sites, incl. `fabric/__init__.py` | Medium | §7.1 lists all 18+1; Phase 3 verify greps to zero |
| 7 | Local `.pth` installs in macer/jaci/juno break the moment this lands in the working tree | Medium | Land on a branch, not `dev`/`main`; Slack the three repo owners before merge |
| 8 | `jaci` (`@dev`) and `juno` (`main`) float — a merge breaks them with no version gate | Medium | Merge to `dev` in the same window as the §7.2 jaci fixes |
| 9 | String monkeypatch targets break silently | Medium | §7.3 table + the `rg` merge gate |
| 10 | Phase 4 deletes shims that production code imports | Medium | §8 Phase 4 repoints `llm/__init__.py:37` and `tests/test_domain_pack_helper.py:6` first |
| 11 | `git mv` on the `observability.py` → `observability/` same-name conversion | Low | Single commit, directory + `__init__.py` created first (§3.1) |
| 12 | Trimming `_LAZY`/`observability.__init__` breaks k9 silently | Low | §7.2 marks `create_app` and the seven `run_tracer` symbols load-bearing |
| 13 | Reviewer cites the `documents/` no-subpackage precedent | Low | §4.6 is on the record |

---

## 11. Open questions

1. **Does anything on the eager path read `_HAS_MLFLOW` / `_mlflow` / `_mlflow_entities` / `_MlflowClient`?** Decides whether `_mlflow_runtime.py` can stay lazy and mlflow leaves the base import (§3.1 must-verify).
2. **`handlers.py`'s 21.4 KiB / two concerns** — split in 2.4 as `handlers.py` + `identity.py`, or leave it? 81 import lines across 64 files argues for care, not for never.
3. **Should `jazzx_sdk.contracts` grow** to cover the Tier-1 surface consumers currently reach via the package root? Out of scope here, but `macer` and `jazzx-assistant` both mix root imports with submodule imports, which suggests `contracts` is not carrying the weight P5 intends.
4. **`MockProcessClient` has no non-mock sibling in `clients/`.** Is there a missing real client, or is the mock vestigial?
5. **Should the eager mlflow import be treated as a bug in its own right?** It predates this refactor and affects anyone installing `japes[mlflow]` — including jazzx-assistant.

---

## 12. Verification record

This plan was drafted from a module-by-module audit, then fact-checked against the working tree with a static module-scope import walker. The check found ~20 defects in the first draft; all are corrected above. The corrections that changed a *conclusion*, rather than a number, were:

| First draft claimed | Actually |
|---|---|
| root `__init__.py` does not eagerly import `jazzx_sdk.fabric`, so the DB factories need an eager→lazy conversion | `fabric` (and `fabric.db`) is eager by three routes; the move is a plain retarget (§3.3) |
| `mlflow` is off the eager path | `tracing.py:682–689` imports it at module scope; `import jazzx_sdk` already pulls mlflow when the extra is installed (§3.1, Phase 0 step 5) |
| `mlflow_bridge` is eager via `trace_source`, so re-exporting it is status quo | `trace_source.py:36` imports it function-locally; re-exporting would newly eagerise it (§5.2) |
| `finance/` is unusable because `excel.py` pulls openpyxl eagerly | openpyxl is function-local; `finance` is already eager anyway. `portfolio` stays at root on charter grounds, not import grounds (§4.3) |
| `odata.py` has one consumer (a test) and is a low-value deferral | Three, two of them production SDK modules in different subpackages — it is correctly at root (§4.5) |
| `k9` is unscanned and unscannable | Scanned; 6 touchpoints, all surviving via package re-exports, which makes those re-exports load-bearing (§7.2) |
| `_SERVER_STACK` should become `"jazzx_sdk.server.app"` | That is strictly weaker; keep the bare `"jazzx_sdk.server"` (§6) |
| `llm/sanitize.py`, `fabric/pack/__init__.py`, `utils/` are dead shims, safe to delete | All three have live importers, one in production code (§8 Phase 4) |
| `mock_services` has 15 call sites, all tests | 26 lines / 18 japes files + 1 jaci, including four inside the SDK (§3.5) |
| no `agent_utils` exists under `japes/` | `examples/document_analyzer/agent_utils/` does, and the example has a live broken import of the SDK path (§8 Phase 0 step 1) |

**Confirmed accurate:** every `jazzx_sdk/__init__.py` line reference (46, 57, 78, 79, 80, 86–120, 96, 105–108, 112–120, 121, 173, 179, 192, 275–278, 350, `_LAZY_ATTRS` 357–367); every `docs/ARCHITECTURE.md` line reference; `tests/test_import_boundary.py`'s contents and its vacuous-pass mechanism; the symbol inventories of `observability.py`, `governed_http.py`, `settings_api.py`, `events.py`, `web.py`, `server.py`, and the full distribution of `tracing.py`'s symbols; the lazy mechanism protecting `AgentTraceHooks`/`MlflowTraceHooks`; the `.pth` live installs and all four dependency pins; `queue_processor.py:20–21`'s module-scope `common.core.queue` import; the `platform_catalog` / `modes.catalog` 13-key duplication; `mock_services.py`'s content audit; and the `kernel_llm_model.py` defect list.

**Could not be verified:** `CLAUDE.md`'s content (symlink outside reachable paths). Whether `import agents` *executes* `import uvicorn` — dependency metadata supports it (`openai_agents` → `mcp>=1.19.0` → `uvicorn>=0.31.1`) but it was not confirmed at runtime.
