# LUNA adoption sketch — jazzx-assistant on the japes chat conductor

Local note (gitignored). Shows exactly how the `jazzx-assistant` (LUNA) repo adopts the japes
reference chat conductor (`jazzx_sdk.agents.interactive.chat`) + the engine's tracer/on_step spine,
replacing its hand-built stage pipeline. Primitives stay in japes; LUNA supplies only domain hooks.

## Stage mapping — LUNA's hand-built stages → japes

| LUNA stage (Aditya's mlflow `stage` tag) | Becomes | Who owns it |
|---|---|---|
| `validate` (Input Payload Validation) | `validate` step | japes reference (override for domain checks) |
| `fetch_conversation` (Fetch Conversation) | `InteractiveAgent.respond(session_id=…)` loads history | **japes (subsumed)** |
| `gating_agent` (Run Gating) | `classify` hook → `GateDecision` | **LUNA** (its router) |
| `grounding_data_download` (Download Grounding Docs) | agent knowledge binding + `scope`, or a custom `ground` step | LUNA config (fabric knowledge) |
| `assistant_agent` (Run Interactive Agent) | `answer` step → `InteractiveAgent.respond` | **japes (subsumed)** |
| `build_citations` (Build Citations) | `InteractiveResponse.sources` (the `Source` model) | **japes (subsumed)** |
| `deliver_answer` (Answer) | `finalize` step + stream | japes + LUNA stream sink |
| `persist_answer` (Persist Answer) | agent turn-persist (`ConversationStore`) + optional answer-entity via `fabric.entities.ensure` | japes + LUNA (ontology id) |
| _(escalate to reasoner/MACER)_ | `escalate` hook (guarded on route) | **LUNA** (its MACER call) |

Net: LUNA keeps **two** domain hooks (`classify`, `escalate`) + config. Everything else is japes.

## The sketch (in the jazzx-assistant repo)

```python
from jazzx_sdk.agents.interactive import (
    InteractiveAgent, InteractiveAgentSpec,
    ChatTurn, GateDecision, build_chat_pipeline, build_chat_components, run_chat_turn,
    InteractiveResponse,
)
from jazzx_sdk.observability import MlflowTracer, build_run_tags
from jazzx_sdk import CallerIdentity

# 1) The loan answering agent — japes-shipped; grounding/guardrails/sources/history are its job.
def loan_agent(runtime) -> InteractiveAgent:
    spec = InteractiveAgentSpec.from_yaml("resources/agents/jazz_assistant.yaml")  # persona/model/knowledge/guardrails
    return InteractiveAgent(
        spec,
        agents=runtime.agents,
        fabric=runtime.fabric,                      # knowledge bindings ground from the loan collection
        guardrails=runtime.guardrails,              # incl. scope_guardrail(topics=[…]) for graceful refusal
        store=runtime.conversation_store,           # respond(session_id=…) loads + persists the turn
    )

# 2) LUNA's router — the gating agent. Returns direct / escalate / refuse.
async def classify(turn: ChatTurn) -> GateDecision:
    verdict = await gating_agent.run(turn.message, scope=turn.scope)   # LUNA's existing classifier
    if not verdict.in_scope:
        return GateDecision(route="refuse", reason=verdict.reason)     # → graceful decline
    return GateDecision(route="escalate" if verdict.needs_reasoner else "direct")

# 3) LUNA's escalation — the MACER / reasoner run (the deep path).
async def escalate(turn: ChatTurn) -> InteractiveResponse:
    findings = await run_macer(turn.scope["loan_id"], turn.message)     # LUNA's reasoner call
    return InteractiveResponse(answer=findings.answer, sources=findings.citations, usage=findings.usage)

# 4) One turn — tracer + stage-progress streaming come for free from the engine.
async def handle_turn(ctx, payload) -> InteractiveResponse:
    turn = ChatTurn(
        message=payload["message"], scope={"loan_id": payload["loan_id"]},
        session_id=payload["conversation_id"], conversation_id=payload["conversation_id"],
        identity=CallerIdentity.from_context(),
    )
    pipeline   = build_chat_pipeline()
    components = build_chat_components(agent=loan_agent(ctx.runtime), classify=classify, escalate=escalate)

    tracer = MlflowTracer(experiment="japes | jazzx-assistant")
    tags = build_run_tags(trace_id=payload["trace_id"],
                          extra={"conversation_id": payload["conversation_id"],
                                 "message_id": payload["message_id"]})

    async def on_step(ev):   # ev: StepEvent — stream stage progress to the UI
        if ev.kind == "start":
            await publish_progress(ctx.streaming_id, stage=ev.phase or ev.id, label=ev.label)

    async with tracer.run(name=payload["trace_id"], tags=tags):
        return await run_chat_turn(turn, pipeline=pipeline, components=components,
                                   tracer=tracer, on_step=on_step)
```

## What LUNA deletes by adopting

- Hand-added mlflow `stage` tags + conv/message run tags → **from the engine** (`tracer` per step, `build_run_tags`). Closes Aditya's tagging + Indranil's trace-query gaps.
- Hand-wired guardrails / scope gate / graceful refusal → `scope_guardrail`/`llm_guardrail` + the `refuse` route.
- Hand-built citation assembly → `InteractiveResponse.sources` (`Source`).
- Blocking mlflow calls on the agent loop → the offload (already shipped).
- The `x-security-context`/`x-user-id` forwarding that caused the recurring 401 → `CallerIdentity` / `default_request_headers` (+ the pending KH client bump, now GA-blocking).

## Gaps LUNA still needs japes for (tracked)

- ~~**Groundedness verifier** guardrail ("block ungrounded before it reaches the user",
  PAGI-1719)~~ — shipped: `grounded_guardrail` (`jazzx_sdk/agents/interactive/registry.py`), an
  async output `Guardrail` that blocks an answer the grounding context doesn't support.
- **Stage-progress stream event type** — `on_step` gives LUNA the signal; a first-class
  `StreamEventType.stage`/progress event would standardise the wire format vs an ad-hoc `llm_chunk`.
- **KH client bump** — v2 idempotent endpoints + identity params (see plan_kh_client_bump.md).
- **Answer-entity persistence** — if LUNA persists the answer as a KH entity (its `persist_answer` +
  "ontology id for the answer entity"), wire `fabric.entities.ensure` in a custom `finalize`/persist step.
