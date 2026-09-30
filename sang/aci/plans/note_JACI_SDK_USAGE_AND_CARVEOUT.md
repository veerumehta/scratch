# Where jaci uses the SDK, and carving an authoring kit out of it

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: note (assessment, decides nothing), 2026-09-29. Measured against jaci `dev` `4db04c4` with
japes' local `v2.5.6` (`d46a9576`) installed editable. Next step, if taken: a japes plan in
`japes/docs/plans/` beside `plan_plato_domain_pack_runtime.md`.

## 1. The question

Does jaci use Plato for most of its work, as it should, and should we carve interfaces and
definitions out of the SDK so jaci authors need only those plus Plato, not the full SDK?

## 2. Answer: no — jaci runs almost everything in-process

**136 files** under `src/`, `ui/`, `scripts/` import `jazzx_sdk`, from **28 modules**. **4** touch
Plato: `scenarios/shared/plato.py`, `clinical_intake/plato_session.py`, `dscr/plato_review.py`,
`ci_spread/feedback.py`. Plato is an opt-in path ("Run on") for DSCR and clinical intake, plus
ci_spread feedback; every other scenario is in-process only.

By role (files overlap):

| Role | Main imports | ~Files | Belongs |
|---|---|---|---|
| Definitions | `fabric.canonical` (Policy 11, load_policies 8, DecimalValue 8, SourceCoordinate 7, Rule 7, Refusal 6, Confidence 6, PolicyRegistry 5, PolicyProfile 5), `modes.schemas` (EvidenceStatus 10, Context 9, LoopStatus 6, Hypothesis 6, Evidence 5), `expressions`, finance types (StatementType, LineVocabulary, FinancialSpread, SpreadPackage), `DocumentAgentSpec`/`InteractiveAgentSpec`, `ConductorPipeline`/`PipelineStep`/`ExecutionKind`, `events_domain` | ~60 | authoring kit |
| Execution | `modes.operational` (5 modes × 6 conductors, SentinelMode), `ConductorEngine`/`StepRegistry`/`Checkpointer`, `pipelines` (investigation_loop 6, document_ingest 4, financial_spread, chat), `DocumentAgent`/`InteractiveAgent`/`AgentExecutionService` (11), `DefaultPolicyExpert` (7), `tools` (BaseToolRegistry 5, extract, conversion/local_cache), `llm`, `KnowledgeFabric`/`local_fabric`, `finance.validation`/`excel` | ~70 | behind Plato |
| Hosting plumbing | `HandlerContext` (16), `ui.get_client_context`/`get_client_layer`, `serve`, settings router, `QueueSettings` | ~20 | mostly goes |
| Plato client | `PlatoClient`, `PlatoError` | 4 | authoring kit |

Also: jaci imports private SDK helpers (`finance.excel._write_trends/_write_statement_sheet/
_write_cover/_styles`) — no author should need those.

## 3. Why a subset is impossible today

Importing any definition module in a fresh process (jaci `.venv`):

- `fabric.canonical.policy` / `.profiles` / `.evidence` / `.decision`, `expressions.definition`,
  `manifest.assistant_manifest`, `modes.schemas`, `pack.schemas`, `clients.plato_client` →
  **~1,500 modules**, including FastAPI, httpx, Azure and `common` (via `jazzx_sdk/__init__.py`).
- `agents.interactive.spec` (`InteractiveAgentSpec`) → **~4,070 modules**, including the OpenAI
  Agents SDK and Anthropic.

So the carve-out is a move into a dependency-light package, not a re-export.

## 4. Precedent and proposal

japes already ships **`jazzx_eval_contracts`**: Pydantic-only ("no FastAPI, SQLModel, queues,
MLflow, Kernel clients, or JazzXRuntime"), versioned wire schemas with snapshot tests
(`tests/schema_snapshots/`, `scripts/regenerate_schema_snapshots.py`), and jaci already depends on
it (locked with japes).

Proposed, same shape:

- **`jazzx-pack-contracts`** (Pydantic only): the pack data model — Policy/Rule/conditions,
  PolicyProfile, MetricDefinition (+ the expression grammar's parse/validate, not evaluation),
  evidence types; manifest schemas — `pack_manifest`, `AssistantManifest`, the profile as data,
  `guardrails.yaml`, the `conductor:` block (`InvestigationLoopConfig`), `evidence_tools`; canonical
  objects — Evidence/Decision/Trace/Outcome, values, Refusal; static pack lint. `jazzx_sdk` depends
  on it and re-exports, so no SDK consumer breaks.
- **Plato client** in it or a sibling (httpx + contracts).
- **Plato for the rest:** validate with `POST /packs/check`, try deterministic rules with
  `POST /packs/{id}/assess`, run with the case-run and assistant routes. Rule *evaluation* stays on
  Plato — the kit defines, it does not evaluate.

## 5. What blocks jaci being "mostly Plato" (independent of the carve-out)

- **C&I** runs its own `ConductorEngine` pipeline with custom steps → needs the second conductor
  kind (`conductor_pipeline`, the japes plan's "Later" row).
- **CRE, insurance diligence, portfolio monitoring**: pages call `tools.extract`, `DocumentAgent`
  and spreading directly; Plato has no documents or spreading routes.
- **AML, KYC**: evidence from thread-local mock connectors (`tests/fixtures/test_context.py`) →
  needs evidence connectors packaged into the Plato image.
- **Earnings-Anthropic, KYC-Anthropic**: custom modes (governor/evaluator) → image plugins.
- **HITL** (C&I spread approval): suspend/resume inside the run — japes plan Phase 3.

## 6. Suggested order, and the open question

1. Carve `jazzx-pack-contracts` (mechanical, low risk). 2. jaci's packs and page render types
import it instead of the SDK. 3. Move scenarios to Plato one by one as kinds/routes land.

**Open (the user's call):** who are "jaci authors"? **Pack authors** — YAML + the contracts
package suffice. **Scenario developers** (pages, adapters) — also need the Plato client and the
types pages render. The answer sets the package boundary.

## 7. The minimal Plato client (added 2026-09-30)

What a caller needs to reach Plato without the rest of the SDK: a **`jazzx-plato-client`**
distribution, about 350 lines, depending on httpx and pydantic.

**In it:**

- **`PlatoClient` / `PlatoError`** (`jazzx_sdk/clients/plato_client.py`, 249 lines), copied
  whole. It imports only httpx, the standard library and `_header_hooks.install_request_headers_hook`,
  of which only the bare `httpx.AsyncClient` branch (~10 lines) is needed. It already covers every
  Plato call jaci makes — packs (list, check, publish, activate, archive, assess), case runs (submit,
  get, list, stream, stop), assistant sessions (create, get, end, close, outcome, record), chat,
  stream, resume, stop — and returns dicts, so no response models come with it.
- **Feedback.** The one Plato call not on `PlatoClient`: jaci posts via `FeedbackApiSink`
  (`evaluation/feedback_sink.py`), which drags in datasets → golden_cases, `feedback_records` →
  `feedback_quality` and `jazzx_sdk.identity`. Minimal form: a `PlatoClient.submit_feedback`
  posting to `/feedback` and returning a dict; `Feedback` (+ `Reaction`, `FeedbackSource`;
  pydantic only, keeping `for_turn`, leaving `from_case_result` and the stores); `EntityRef` (two
  fields); and the constants `ASSISTANT_ENTITY = "assistant"` and `TURN_METADATA_KEY = "turn"`,
  which jaci now imports from `jazzx_sdk.server.*` (~4,070 modules for two strings).
- **Optionally, pack packaging:** `pack_archive(folder) -> bytes` and `publish_pack(client, folder)`,
  now in jaci's `scenarios/shared/plato.py`. Every pack author needs them.

**Left behind:** `jazzx_sdk.identity`'s context variables (the caller passes a
`request_headers_provider`, as jaci's `caller_identity_headers()` already does); typed response
models (the pack's generated JSON schemas are the contract); the eval/dataset routes (jaci does not
call them); the Kernel and Knowledge Hub clients; the server tier.

**Why a copy, not a re-export:** importing `jazzx_sdk.clients.plato_client` loads **1,502
modules** (via `jazzx_sdk/__init__.py`: FastAPI, Azure, `common`); `jazzx_eval_contracts` loads
221. Same shape as that precedent: a sibling distribution in the japes repo with its own
`pyproject.toml`, and `jazzx_sdk.clients.plato_client` re-exporting it so no import breaks. The
test holding `DEFAULT_PREFIX` equal to the server's moves with it.

**What it does not do:** free jaci's current scenarios from the SDK. On the Plato path the pages
still turn Plato's dicts into jaci types whose modules (`dscr/schemas/dscr_schemas.py`,
`eligibility/assessment.py`, `dscr/conductor.py`, `clinical_intake/session.py`) import `jazzx_sdk`
for the in-process path. The kit suffices for a new Plato-only author and for
`scripts/publish_packs_to_plato.py`; existing scenarios need the full SDK until §5 is done.

**Bearing on §6's question:** a scenario developer needs this client kit; a pack author needs the
§4 contracts package plus the pack-packaging helpers above.

**Unchecked:** Plato's `/feedback` takes the SDK's `Feedback` shape, not
`jazzx_eval_contracts.FeedbackSubmissionV1`, so those wire contracts may not serve that route as
they stand.

**Packaging (decided 2026-09-30):** a separate artifact, built from the japes repo — its own
distribution and `pyproject.toml` beside `jazzx_eval_contracts`, not a new repo.

- *Why in japes:* the client restates Plato's routes, headers and stream format, and a test
  already holds its `DEFAULT_PREFIX` to the server's. In one repo a route change and its client
  change land together under one pre-push run; across two they drift until a page breaks. It
  also rides japes' existing branch flow (`v2.5.6` → `plato`/`dev`) instead of a second repo to
  pin in step.
- *Consumption:* jaci depends on it directly, not through japes —
  `jazzx-plato-client @ git+https://github.com/JazzX-LLC/japes.git@plato#subdirectory=jazzx_plato_client`
  (or a private index if one is adopted). `jazzx_sdk` takes it as a path dependency and
  re-exports it.
- *When to split it out:* consumers without japes repo access, a release cadence apart from
  Plato's, or a different owner. None holds today; moving a self-contained directory is cheap
  later.
- *Still to settle:* how the client declares the Plato API it speaks — version the two together,
  or check against Plato's `/health`/`/info` — so an old client fails clearly, not with a 404.
