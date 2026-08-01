# The Assistant Vertical — shipped vs. gap (LUNA / jazzx-assistant)

Local planning note (gitignored). Reconciles the ideas surfaced in the "Assistant Quality & Mortgage
AI Optimization" working group (Jun 10 → Jul, LUNA = the JAPES-based loan chat agent) against what
`jazzx_sdk` already ships. Key finding: **most of the assistant vertical is already in japes** — the
open question is adoption, not construction.

## Context

LUNA is the GA-critical, japes-based "loan chat agent": one agent that classifies a request
(direct-answer vs escalate-to-reasoner/MACER), answers grounded in reasoner output + loan data +
policy, with citations, guardrails, graceful refusal, and per-user conversation history. Because the
chat spans ~5 weeks, several capabilities the group is discussing were built in japes *during* that
window — so the assistant may be re-implementing them as raw-plumbing consumers.

## Already shipped in `jazzx_sdk.agents.interactive` (adopt, don't rebuild)

| Capability | Where | Notes |
|---|---|---|
| Interactive agent + profile/spec | `agent.py` (`InteractiveAgent`, `build_interactive_agent`), `spec.py` (`InteractiveAgentSpec`) | `respond` / `respond_stream`; the ChatConductor substrate |
| **Skills** (Nimar's explicit ask) | `registry.py` (`Skill`, `SkillRegistry`, `ProfileRegistry`) | "generalize June/MACER work as skills" — the registry exists |
| **Guardrails + scope gate + graceful refusal** | `registry.py` (`Guardrail`, `GuardrailRegistry`, `llm_guardrail`, `scope_guardrail`) | input+output guardrails; `scope_guardrail` = fixed graceful decline for out-of-scope; `blocked`/`block_reason` on the response |
| **Citations with provenance** | `response.py` (`Source`, `InteractiveResponse.sources`) | `kind`/`ref`/`label`/`uri`/`collection_id`/`quote` — clickable-in-UI citation model already defined |
| Conversation memory + compaction + masking | `memory.py` (`ConversationStore`, `CompactingConversationStore`, compaction strategies, `MaskingConversationStore`) | per-user history + token/summarize compaction |
| Grounding source assembly | `knowledge.py`, `source_builder.py` (`SourceBuilder`, `AnchorRule`) | assembles grounding into `Source`s |
| Streaming | `stream_hooks.py`, `response.py` (`InteractiveStreamEvent`), `jazzx_sdk.streaming` (SSE) | delta/done streaming; Nimar noted "Virendra added SSE to japes" |
| Feedback / optimization (compounding loop) | `optimize.py`, `jazzx_sdk.evaluation` (feedback, optimization) | |
| Observability | `jazzx_sdk.observability` (`RunTracer`, `build_run_tags`, `STAGE_TAG_KEY`) | the stage/conv/message tags Aditya hand-added map here 1:1 |
| Identity forwarding for RBAC | `CallerIdentity`, `default_request_headers` | the recurring KH 401 fix (x-security-context / x-user-id) |
| Idempotent answer persistence | `fabric.entities.ensure` (`WriteOutcome`) | the `persist_answer` stage |

## Real remaining gaps (ranked)

1. ~~**Groundedness verifier guardrail**~~ — **SHIPPED.** `grounded_guardrail`
   (`registry.py`, exported from `__init__.py`) blocks answers unsupported by the assembled `Source`s
   (Chanpreet's PAGI-1719).
2. **Stage-progress stream event** — the engine's `on_step` hook now gives a host the signal
   (`StepEvent` at start/end). Remaining: a first-class `StreamEventType.stage`/progress event so the
   *wire format* is standard rather than an ad-hoc `llm_chunk`. *Small; partially shipped.*
3. **Feedback→trace→learning end-to-end** — pieces exist (`RunTracer`, `TraceSource`/`ExperimentStore`,
   `evaluation.feedback`/`optimization`); the gap is a consolidated trace store beyond MLflow
   (Indranil: "invocations only in mlflow") + turn→feedback→learning wired through the interactive
   agent. *Medium; unblocks a person today.*
4. ~~**Adaptive-depth gate**~~ — **SHIPPED.** `PipelineStep.when` + `ConductorEngine(step_guards=…)` +
   the reference chat conductor's `gate` step give declarative direct-vs-escalate-vs-refuse routing.
   Cost/latency-aware gating (hook: `evaluation.operational`) can still layer on top.
5. ~~**ChatConductor assembly**~~ — **SHIPPED** as `agents.interactive.chat` (validate→gate→escalate|
   answer|refuse→finalize + `run_chat_turn`); the engine gained per-step tracer spans (auto stage
   tags), `on_step` streaming, and per-step timing. See plan_luna_adoption.md.
6. **Shared safety/grounding skill fragment** — the no-invention rule, the "retrieved content is DATA,
   not instructions" injection defense, and (for outbound content) the fair-lending / protected-class /
   no-steering / no-promises block are **domain-neutral but triplicated** across the LUNA skills
   (`email_agent`, `loan_agent`, `policy_agent`) — a fair-lending wording fix needs three edits. Author
   it once in japes as a composable `Skill` instruction fragment (a preamble a skill opts into) or a
   `grounded_guardrail`. *Small–medium; high correctness upside; ties to gap #1.* A parameterized
   "compose a `{subject}`-facing message" skill *template* (the generalization of `email_agent`) is a
   **design-now candidate, not build-yet** — seen once; wait for a second instance (KYC/servicing letter)
   per the don't-generalize-unhit rule. The concrete domain skill (its tools + noun) stays pack-side.
7. **Memory Fabric** — Chanpreet's "distilled reasoner output as fast-retrieval grounding context, with
   provenance to raw findings." Not built; still at PRD stage on their side. japes should define its
   position (a materialized, retrieval-optimized view over canonical findings) rather than react. *Large;
   design-first. Hook: fabric.rag + memory⊃conversation persistence architecture.*
8. **Versioned invocation contract + boundary tests** — the correlation-key churn ("made optional to
   unblock"), stale-client 401s, and `japes | <name>` naming debate are contract instability. Own a
   documented, versioned invocation contract (payload envelope, correlation semantics, identity headers,
   run/experiment naming taxonomy) with contract tests. *Medium; prevents recurrence.*

## Recommended sequencing

- **Adoption first (highest leverage, zero new capability):** get LUNA onto `agents.interactive`
  (`InteractiveAgent` + `scope_guardrail`/`llm_guardrail` + `Source` citations + `CompactingConversation
  Store` + `observability.RunTracer`). This deletes hand-rolled guardrails/tags/history in the assistant
  and closes Indranil's and Aditya's gaps for free.
- **Shipped since (conductor thread):** ChatConductor (#5) + adaptive-depth gate (#4) + groundedness
  guardrail (#1) + the engine observability/streaming/timing spine + `on_step` for stage progress
  (#2, partial).
- **Then the small gaps:** shared safety/grounding fragment (#6) — can now build on the shipped
  `grounded_guardrail` (#1); first-class stage-progress event type (#2).
- **Then the medium/structural:** feedback spine (#3), invocation contract (#8).
- **Design track:** Memory Fabric (#7); parameterized compose-message skill template (#6) once a
  second instance appears.

## The meta-point for the group

japes is being consumed as raw plumbing (queue + streaming + a KH client) while capabilities it already
ships (guardrails, scope gate, citations, conversation memory, compaction, skills, observability) get
rebuilt in the assistant. The win is adoption + closing a short real-gap list — not new construction.
