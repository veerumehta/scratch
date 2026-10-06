# Plan: selectable models and versioned prompts, the cross-repo part

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: SDK first slice built on the `v2.6.1` working tree (2026-10-06, sonnet-runtime), committed by the user's `/tmp/japes_commit_models_prompts.sh`; sibling steps not started. Companion to `plan_models_prompts_defaults.md` (the SDK and Plato
build, runtime session). This file covers the sibling repos: what each does today, who adopts what,
what the SDK must offer so adoption is config, and what the SDK work would break. Written from five
read-only surveys (jaci, jazzx-assistant, juno, macer + macer-japes, and kernel, eval-service,
policy-workbench, assistant, knowledge_hub, k9, common) on 2026-10-06; file:line evidence is in
the survey notes, key sites are cited below.

## 1. What each repo does today

| Repo | SDK coupling | Model selection | Prompts | Provenance on outputs |
|---|---|---|---|---|
| jaci | heavy, editable | Six mechanisms: env via `resolve_model("JACI")`; UI sidebar writing `JACI_LLM_*` (`commercial_lending/ui/shared.py:121`); per-mode constructor defaults (`ci_spread/conductor.py:124`); pack YAML `conductor.modes.<m>.model`; hardcoded benchmark constants; an unused `.env.template` per-mode list | Mode prompts via SDK `compose_mode_prompt` with a silent fallback to a legacy local `prompts/` tree (`common/utils/prompt_loader.py:10-70`); 28 pack `mode_tuning/*.md`; about 60 legacy `prompts/v2.x` files selected by `settings.prompt_version`; about 6 inline constants; imports the SDK's `statement_prompt_preview` by name (`spreader.py:29`) | Pack id, version, digest, trace id only; no model or prompt anywhere; `CaseResult.usage` never read; `backfill_experiments.py` guesses `prompt_version` from timestamps |
| jazzx-assistant | medium, pinned japes 2.5.0 (`ef01fe00`) | Env `JAZZ_ASSISTANT_MODEL_NAME`, per-request `config.model_name`; gate model separate env; profile omits `model` | Own files: `persona.md`, three skill YAMLs, `gate/prompts/classifier_v1.md` (the only versioned one); persona composed per turn with loan context and remote feedback fragments | `model_name` on MLflow params, spans and the persisted `AssistantAnswer`; no prompt version, not even the gate's; reads `reply.usage` as numeric metrics and prices it with `compute_cost_from_metrics`; mutates `MODEL_PRICING` in place |
| juno | one import (`ClientLayer`, Knowledge Hub), tracks japes `main` unpinned | Own constants and profile/skill YAML via OpenAI Agents SDK and an MLflow gateway | Own `prompt.md`/`SKILL.md` files plus a few constants; a DB skill registry | Model on MLflow spans and DB rows; no prompt version |
| macer | handler, runtime, `KnowledgeHubClient` | Global env model plus two per-phase overrides (one hardcoded) | All Python constants, no versioning; snapshot tests only | Settings as MLflow params plus git SHA; per-phase override models not recorded |
| macer-japes | stale fork on `jazzx_runtime_sdk` | Global env | Constants | Settings params |
| k9 | broad (LLMManager, server, tracing, fabric) | Hardcoded `gpt-4o` constructor defaults | `templates/*.txt` by path | None |
| kernel | none (deprecating, absorb lens) | `llm` table, per-agent FK, layered model-catalog resolver | DB `agent_prompt` plus MLflow prompt registry | `version_hash` over prompt and every behaviour-affecting param, linked to traces |
| eval-service | none (retiring into the SDK) | Per-run overrides | MLflow registry, `agents.<name>.system_prompt`, `@staging` alias from the optimizer | `optimization.*` run tags |
| policy-workbench | none (moving onto Plato, D1) | Env plus per-request | `.md` files via `load_prompt()` | Model on root span only |
| knowledge_hub | none | Per-collection `*_llm_id` | A DB `prompt`/`prompt_version` store (semver, draft/publish, `content_digest`, fork lineage), apparently unused at runtime | None |
| assistant, common | none | pass-through / none | YAML bundles / none | None |

Nobody records which prompt produced an output. The only prior art for doing so is kernel's
`version_hash`.

## 2. Who adopts what

| Repo | Prompt loader + `(name, version, digest)` | Model selection | Why |
|---|---|---|---|
| jaci | Yes, fully | Yes | Main SDK consumer, not a compat constraint; its six model mechanisms and two prompt trees are the drift the SDK work exists to remove. |
| jazzx-assistant | Provenance only, by config: digests of its own persona, skills and gate prompt, through the profile loader | Keep its env and request override; take the SDK's selectable list only if it wants a picker | Canonical assistant; its prompts are product-owned and composed per turn. Reaches it only through a `dev` to `main` release. |
| Plato and policy-workbench | Plato is the SDK work itself; the workbench retires onto Plato (D1), so it adopts nothing separately | Same | |
| juno | No | No | Owns its stack (Agents SDK, MLflow gateway); one SDK import. Revisit only if it asks. |
| macer, macer-japes | No | No | MACER is deprioritized; the adjudication chassis is the successor. |
| k9 | Optional, later | Optional, later | Low priority; its templates and `gpt-4o` default are its own. |
| kernel, eval-service, knowledge_hub | Absorb designs, no adoption | Absorb kernel's model table shape only if a tenant model table is ever wanted | Deprecating or retiring. |

**Absorb, not adopt** (from the surveys):
- kernel `version_hash`: one digest over the rendered prompt and every behaviour-affecting parameter
  (model, sampling params, tools, schemas). Worth having beside the prompt digest (decision U1).
- kernel: registry writes are fire-and-forget, gated by config, never fail the runtime path.
- eval-service: the optimizer registers candidates under an alias (`staging`) and promotion writes
  back. The defaults plan's P3 already says this; keep the alias name.
- knowledge_hub: draft/publish, semver, `content_digest`, `derived_from` lineage. A possible
  later backend for the registry (decision U3), not needed for files.

## 3. What the SDK must offer so adoption is config, not code

| # | API | Serves |
|---|---|---|
| A1 | `load_prompt(name, *, pack=None, **fields) -> RenderedPrompt(text, ref)`, where `ref = PromptRef(name, version, digest, source)` and `source` is `sdk`, `pack`, `consumer` or `inline`. Lookup order: pack `prompts/`, then consumer roots, then SDK files. | all |
| A2 | Consumer prompt roots by config (`JAPES_PROMPT_ROOTS` or an argument), so a consumer's own `.md` files get the same `PromptRef` without moving into the SDK. | jaci, jazzx-assistant |
| A3 | `InteractiveAgentSpec.from_dir` computes a `PromptRef` for the persona and each skill automatically, and the agent stamps them on its turn's provenance. A raw `persona=` string gets `source="inline"` with a digest only. | jazzx-assistant at zero code |
| A4 | Composition: a persona built from a base plus fragments (loan context, feedback) records the base ref plus each fragment's digest, not one opaque hash. | jazzx-assistant |
| A5 | Registration is never required. Unregistered prompts still get a digest. Registry writes never fail a run. | jazzx-assistant, kernel lesson |
| A6 | `select_model(step, *, request=None, pack=None, tenant=None)` with one order: request, then step override, then pack/profile, then tenant default, then env (`resolve_model(prefix)` keeps consumer prefixes such as `JACI`), then provider default. Returns the model and where it came from. | jaci, Plato |
| A7 | `selectable_models()`: model cards (plus overlay) whose provider has a key. Pricing a consumer adds at runtime must be visible to it, or there should be a supported way to add a card instead of mutating `MODEL_PRICING`. | Plato UI, jazzx-assistant |
| A8 | Provenance lives in its own field (`provenance: [StepProvenance]`), not inside `usage`. `usage` stays numeric. Published as a contract in `jazzx-plato-client`. | jazzx-assistant's cost code, jaci pages |
| A9 | `compose_mode_prompt` raises when the base prompt is missing. Already true (`FileNotFoundError`); the silent fallback is jaci's own `prompt_loader.py`, so the fix is jaci's. | jaci |

**Stays consumer-owned:** domain prompt content (jaci pack tuning, assistant persona and skills, juno
profiles, k9 templates); which model a product uses; MLflow experiment and tag names; UI.

**Built in the first slice:** A1/A2 (`jazzx_sdk.prompts.load_prompt`, `PromptRef`; lookup pack `prompts/`, then `JAPES_PROMPT_ROOTS`, then SDK files; no front-matter version means the content hash), A5 (`register_best_effort`; `DbPromptRegistry` tenant-keyed, migration 0021; Plato registers prompt files at startup), A6/A7 (`jazzx_sdk.llm.selection`: `select_model`, `selectable_models`, `check_selectable`; `register_model_card` is the supported way to add a card), A8 (`provenance: [StepProvenance]` beside numeric `usage` on `ExtractionRun` and `CaseResult`, plus `CaseResult.model`; in the client contracts). Model choice reaches `ReasoningAgent` through a `RunSettings` context variable. **Not built:** A3/A4 (needed before jazzx-assistant's step 3); investigation-mode prompts recorded as `inline` digests, document-step and condition-evaluator prompts still code.

## 4. What the SDK work would break, by repo

| Repo | Break | Owner action |
|---|---|---|
| jaci | If `compose_mode_prompt` stops finding a base prompt, `prompt_loader.py` silently drops to legacy `prompts/` with different content. | SDK: A9. jaci: delete the fallback and the legacy `prompts/v2.x` tree. |
| jaci | `spreader.py:29,47` imports `jazzx_sdk.finance.structure.statement_prompt_preview` by name; moving that prompt to a file must keep the function or tell jaci. | SDK keeps the name (it returns a preview, not a constant). |
| jaci | The `acra-lending` default tenant: ci-spread has no `PACK_TENANTS` entry (`shared/plato.py:134`), so its fallback tenant moves; a Plato without `acra-lending` breaks DSCR (already in review `20261006T042009Z`). | jaci: pin ci-spread's tenant. SDK: none. |
| jaci | Renaming or nesting `ExtractionRun` fields it reads (`status`, `stage`, `documents`, `segments`, `proposals`, `failed_segments`, `error`) or case-run fields (`output.decision`, `trace_id`, `version`, `content_digest`). Adding fields is safe. | SDK: add only. |
| jazzx-assistant | Mandatory registration would break its per-turn composed persona and its raw-string gate spec. | SDK: A5. |
| jazzx-assistant | Non-numeric keys in `usage` survive its filter but reach `compute_cost_from_metrics`; a model or prompt entry there could change cost silently. | SDK: A8. |
| jazzx-assistant | Pinned at 2.5.0; none of this reaches it until `dev` goes to `main`, and that release carries every 2.5.x and 2.6.x break at once. | User: release timing (U4). |
| juno | Tracks japes `main` unpinned; only `ClientLayer(knowledge_hub_url=, request_headers_provider=)` and `.knowledge_hub` matter. Unaffected by this work. | None. |
| k9 | Only if `LLMManager`, `RunTracer`/`SpanHandle`/`NoOpTracer`, `ResponseMessage` or `HandlerContext` change shape. This plan does not. | None. |
| macer, macer-japes, kernel, eval-service, policy-workbench, knowledge_hub | No compile-time coupling to the touched code. | None. |

## 5. Migration order

1. **SDK** (runtime session, defaults plan P1 to P3) with A1 to A9. A3, A8 and A9 are the ones the
   siblings depend on; build them in the first prompt slice, not later.
2. **jaci** (through the jaci session): one model mechanism (pack YAML per mode plus `JACI_LLM_MODEL`;
   drop the per-mode constructor defaults, the sidebar env writes in favour of the SDK's selectable
   list, and the unused `.env.template` entries); delete the legacy prompt fallback and tree; show
   model and prompt provenance on run views and in downloads; pin ci-spread's tenant. Breaking for
   jaci, which is fine.
3. **jazzx-assistant**, after the next `dev` to `main` release: provenance at zero code via A3/A4;
   load the gate prompt through A1 with its version; store prompt refs on `AssistantAnswer` beside
   `model_name`. Through its own team, with an adoption note written from here.
4. **Absorb** kernel's behaviour digest (if U1 is yes) and eval-service's alias convention into the
   SDK; nothing changes in those repos.
5. juno, k9, macer: nothing planned.

## 6. Decisions for the user (all answered 2026-10-06)

| # | Question | Recommendation |
|---|---|---|
| U1 | Digest scope: prompt text only, or also a behaviour digest over prompt, model, sampling params and tools (kernel's `version_hash`)? **Decided:** both, prompt digest plus a per-step `behaviour_digest`. |
| U2 | Should the SDK loader serve consumers' own prompt files (A2), or only SDK and pack prompts? **Decided:** yes. |
| U3 | Registry backend: the SDK's existing `prompt_registry_db`, or knowledge_hub's versioned prompt store? **Decided:** the SDK's own registry. |
| U4 | When does jazzx-assistant get this: next `dev` to `main` release, or a targeted backport? **Decided:** next `dev` to `main` release, no backport to 2.5.0. Adoption note `/tmp/jazzx_assistant_models_prompts.md`, forwarded by the user. |
| U5 | jaci's six model mechanisms: collapse to pack YAML plus env as in step 2? | Yes. |
| U6 | Do juno or k9 get an invitation to adopt provenance, or are they left alone? **Decided:** left alone for now. |
