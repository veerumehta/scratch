# juno scan for Plato / SDK absorption (origin/main 9528dae1, 2026-10-13)

## 1. Functional map
- **Orchestrator + skills**: `app/copilot/agent.py`, `skills/tool_defs/run_skill.py` (4.4k lines), `skills/loader.py`, `skills/registry.py`, `skills/tool_registry.py`; 35 skill packages in `app/copilot/skills_data/*` (skill.yaml + SKILL.md + references).
- **Turn service / streaming**: `skill_service.py` (4.6k), `stream/` (queue, `journal.py`, `tail.py`, `hub.py` LISTEN/NOTIFY, `executor.py`, `reconciler.py`), async `runs/` with webhooks.
- **Human-in-the-loop**: `skills/tool_defs/dialogue_tools.py`, `user_cards.py`, `card_payloads.py`, `stream/card_crud.py`, `plan_questions.py`, `decision_memory.py`; browser holds `stream/client_tools.py`.
- **Build planning**: `plan_tools.py` (propose_plan gate), `plan_store.py`, `plan_graph.py`, `plan_evidence.py`, `plan_guards.py`, `preflight_safety.py`, `update_planning.py`.
- **UI coupling**: `context_tools.py` (page/form context), `navigation/open_screen.py`, `ui_notifications.py`, `notifications.py` (completion via notifications_hub).
- **Guardrails / hygiene**: `guardrails/input_guards.py`, `output_guards.py` (source-leak), `secret_redaction.py`, `search_snippets.py`.
- **Memory / learning**: `memory_tools.py` + `core/memory.py` (mem0/pgvector), `harness_learning/*` (offline reflection recommendations), `reflection_outcomes.py`.
- **Eval skills** (all over eval-service REST): `eval-specialist`, `eval-testcase-generator`, `eval-scorer-generator`, `eval-prompt-fixer`, `learning-specialist`; tools in `tool_defs/eval_tools.py` (4.3k).
- **Builder-Studio domain**: BPMN/DMN/Groovy/ELK tools, integration-tool codegen (`contract_validator.py`, `mapping_loader.py`), Kernel/Flowable/MLflow debuggers, `juno_tasks/` (Jira/GitHub job runner), `scheduler/`, profiles, Skill registry over Azure blob (`app/skill/`).

## 2. Worth absorbing (ranked)

1. **Structured mid-turn questions as tools** -- `dialogue_tools.py::ask_user_choice` (:212), `::ask_user_text` (:405), keyed answers reused across turns (`::_earlier_choice` :382, `decision_memory.py`), `user_cards.py::stop_at_questions` (:96). japes: partial. `agents/interactive/response.py:36` defines `Decision`/`needs_decision`, but nothing in `jazzx_sdk` or `plato` produces it (no tool, no answer path, no persistence). Value: authoring assistant asks "which pack / which document / approve this edit" as a card the page renders, answer validated against offered options, never re-asked. Dependency: none (Postgres plan row); in japes would sit on ChatTurnStore/session state. Size: medium.

2. **Cards persisted on the asking message** -- `stream/card_crud.py::get_card/latest_open_card/resolve/supersede`, `plan_questions.py::record_answers/supersede_open`, `card_payloads.py::canonical_arguments` (card drawn from the normalised args, not the model's raw ones). japes: no. Value: open questions survive reload/reconnect on the Plato page; stale cards superseded. Dependency: none. Size: small-medium (pairs with 1).

3. **Propose-then-approve gate before expensive work** -- `plan_tools.py::propose_plan` (:886), fingerprinted approval (`::_plan_fingerprint` :816, `::outdated_plan_error` :756), `plan_store.py` (multi-turn plan record). japes: no; `server/authoring_assistant.py` `start_extraction` runs immediately. Value: authoring assistant proposes "extract N documents into pack X, catalog+JTBD, est. cost" and runs only on approval; edits proceed against the approved fingerprint. Dependency: none. Size: medium (generalise as an SDK "approval tool" over item 1, not juno's BPMN plan schema).

4. **Prose-question recovery** -- `dialogue_tools.py::prose_question_prompt` (:472): if a task turn ends with a question in prose, re-prompt the model to ask it as a card. japes: no. Value: keeps item 1 honest in practice (juno saw it live). Dependency: none. Size: small.

5. **Page context to the model** -- `context_tools.py::get_ui_context` (:145), `::open_component` (:92): client sends `interaction_data` (route, entity id, form values) and a tool exposes it. japes: no equivalent (`runs/chat.py` ContextProvider is a runtime context manager, not client page state). Value: the assistant page knows the selected pack/draft/proposal without the user naming it. Dependency: none. Size: small.

6. **Browser-executed tools (hold)** -- `stream/client_tools.py::call_browser_tool` (:69), timeout `CLIENT_TOOL_TIMEOUT_S`. A tool emits an event and awaits the browser's answer mid-run. japes: no. Value: read live page state (unsaved edits in a rule editor) at the moment the model asks. Dependency: none; in-process by design. Size: small (needs a POST resolve route plus a status-event kind).

7. **Navigation tool** -- `navigation/open_screen.py::open_screen` (:209) with `matching.py` name matching; one-way `navigate` event. japes: no. Value: "open the DSCR pack's review queue" from chat. Dependency: none (Plato's own lists). Size: small; Plato-specific, keep in Plato not SDK.

8. **Eval authoring skills as prompts** -- `skills_data/eval-testcase-generator/SKILL.md` (previewable cases, save on ask), `eval-scorer-generator/SKILL.md` (NL to code or LLM-judge scorer draft), `eval-prompt-fixer/SKILL.md` (diagnosis + revised prompt + changes citing failing cases). japes: has stores, scorers, `optimization.py::propose_prompts`, `synthesize_cases_from_feedback`; no case generation from an assistant spec, no NL-to-scorer, no cited failure diagnosis. Value: the "test" half of the assistant page. Dependency: eval-service REST in juno; rebind tools to SDK `datasets`, `custom_scorers`, `experiments`. Size: medium (tools are new; prompts largely reusable, rewrite not copy).

9. **Name-contains secret redaction on structured data** -- `secret_redaction.py` (leaf-only, keeps schema shape). japes: mostly covered by `failures.py::redact_secrets/redact_fields`; check only whether juno's leaf-only rule over schemas/code is stricter. Size: small, low priority.

## 3. Not worth absorbing
- Resumable SSE journal/queue (`stream/*`), `runs/*`, `queue/*`: japes `runs` journal with `after_seq`, ChatCoordinator already cover it.
- `compaction.py`, `session.py`: japes `CompactionPolicy` and run_kit compaction exist.
- `search_snippets.py`: japes `tool_compression`/`read_reference` already caps and pages large outputs.
- `cost_hooks.py`, `trace/*` labels, `mlflow_trace_processor.py`: japes ModelCallLedger, status events, display names, CanonicalTrace.
- `output_guards.py`, `input_guards.py`: japes leak_check and gate; output guard is JazzX-source-specific.
- `memory_tools.py`, `core/memory.py`: mem0 + pgvector dependency; japes Memory Fabric and feedback cover it.
- `harness_learning/*`: Juno-reflection POC over mem0 and its own outbox; japes feedback + optimization are the SDK home; revisit only the "recommendation card" idea.
- `notifications.py`: depends on notifications_hub.
- `learning-specialist`, `eval-specialist` CRUD skills: thin wrappers over eval-service APIs japes already hosts.
- BPMN/DMN/Groovy/ELK, integration codegen, `contract_validator.py`, `mapping_loader.py`, Kernel/Flowable/MLflow debuggers, `juno_tasks/`, `scheduler/`, `build_workspace.py`, `app/skill/` blob registry, profiles: Builder-Studio- or service-specific, or japes packs/profiles already better.
- `sandbox/*` (OpenAI SandboxAgent capabilities): ties to SDK sandbox backends; japes python executor is the analogue.

## 4. Could not determine
- Whether juno's card answer path (`/approve` route, validation in `skill_service.py`) has edge cases worth copying; not read in full (4.6k lines).
- Frontend rendering contract for cards/navigation lives in another repo; not inspected.
- Active feature branches (BSD-5080 DMN, BSD-3273 clone, perf/bpmn-build) are all Builder-Studio domain; none read for generic primitives beyond commit subjects.
- The local `japes_v2` juno branch is old (tip is PR #203; main is at #354; dates not checked); no current japes adoption in juno beyond `core/jazzx_clients.py` (Knowledge Hub only).
