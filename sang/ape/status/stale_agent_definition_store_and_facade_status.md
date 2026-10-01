# Status: AgentDefinitionStore + a unified "invoke agent by name" facade

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_agent_definition_store_and_facade.md

**Part 1 (`AgentDefinitionStore`) done and tested. Part 2 (the facade) and Part 3
(`import_from_kernel`) not started** — checked directly, not assumed: `AgentExecutionService` has
none of `_registry`/`_kernel_client`/`_run_from_spec` the plan's own Part 2 pseudocode references
as if they already existed. Wiring them in is a real design decision, not a mechanical addition,
for the reason below.

## Part 1 — `AgentDefinitionStore` (done)

- `jazzx_sdk/agents/definition_store.py`: `AgentDefinition{name, backend: Literal["kernel",
  "japes"], spec: InteractiveAgentSpec | None, kernel_agent_id: UUID | None, created_at,
  updated_at}`, `AgentDefinitionStore` Protocol (`get`/`put`/`list`/`delete` — no claim/heartbeat/
  reap, exactly per the plan's own "this is a plain name-keyed registry" scoping), and
  `InProcessAgentDefinitionStore`. Exported from `jazzx_sdk.agents`.
- `jazzx_sdk/agents/definition_store_db.py`: `DbAgentDefinitionStore` on `fabric.db` — mirrors
  `DbTurnRunStore`'s pattern (a JSON `data` column plus one indexed `backend` column; `put()` uses
  `session.merge()` for a clean insert-or-update on the `name` primary key, bumping `updated_at`
  the same way the in-process store does, so both backends behave identically on overwrite).
  Lazy-imported, not re-exported from `jazzx_sdk.agents.__init__` — same SQLAlchemy-opt-in split as
  `DbTurnRunStore`/`DbSuspensionStore`.
- 10 new tests (`tests/test_agent_definition_store.py`): both backends' get/put/list/delete,
  `put()` bumping `updated_at` on overwrite, a kernel-backed definition carrying no `spec`, and —
  for the Db backend specifically — put-overwrite actually replacing a `japes`-backed definition
  with a `kernel`-backed one under the same name (not just re-saving the same shape). Db tests use
  the same `DbStore(backend="sqlite")` + `await db.create_all()` pattern as
  `test_resilient_runs.py`'s `DbTurnRunStore` tests.

## Part 2 — the facade (not started; a real gap, not a checklist item)

The plan's own Part 2 sketch writes `AgentExecutionService.invoke()` as if `self._registry`
(an `AgentDefinitionStore`), `self._kernel_client` (a `KernelClient`), and `self._run_from_spec`
(a spec-execution path) already existed on the class. Checked `jazzx_sdk/agents/service.py`
directly: **none of the three exist.** `AgentExecutionService.run()` is the low-level,
provider-portable `(system_prompt, messages) -> AgentResult` API — it has no concept of a named,
spec-backed agent at all. The actual "run from an `InteractiveAgentSpec`" path lives in
`InteractiveAgent`/`build_interactive_agent` (`jazzx_sdk/agents/interactive/`), a different,
heavier object that also needs a `skill_registry` and a guardrails catalog — dependencies a bare
`invoke(name, input_text)` call has no natural source for today (a `HandlerContext`-driven call
has them; a bare name-based facade call doesn't say where they'd come from).

This is not a mechanical "wire it up" gap the way Phase 1's registry one-liners in the jaci
Concepts-tab-parity plan were — building `_run_from_spec` correctly means deciding where
`skill_registry`/guardrails come from for a name-invoked agent, which the plan itself doesn't
specify and which affects the shape of `AgentDefinition` and/or the facade's own signature. Left
unstarted rather than guessed at.

## Part 3 — `import_from_kernel` (not started; blocked on Part 2, and on the plan's own open items)

Depends on Part 2 existing first (there's nothing to register a translated definition *into* as a
running capability without it), and the plan's own text already flags two of its inputs as
unresolved: the autonomy-tier mapping (japes's Authority Matrix vs. kernel's 4-tier enum) and the
handoffs mapping (`callable_agent_ids` -> Agents-SDK `Handoff`, which needs target agents already
resolvable — a chicken/egg ordering question). Neither decided here.

## Deliberately not done / not decided (stated, not silently dropped)

- The shadow-record-vs-live-KernelClient-lookup question for `list()`/discovery of kernel-hosted
  definitions — the plan itself says "not settled here"; still not settled.
- Autonomy mapping, handoffs mapping — the plan's own explicitly-open items, untouched.
- Full japes-suite verification alongside `tests/test_kernel_client_invoke_agent.py` (per the
  plan's own verification step): 2038 passed (up from 2028 before this — the 10 new tests), 3
  skipped, no regressions.
