# Done: InteractiveAgent Guidance Hook + eval-service-backed GuidanceStore

Author: Virendra Mehta (via session) · Completed 2026-07-27
Repo: japes · Landed on dev: `46adf8f` (Phase 1), `2b2f467` (Phase 2), `820fbc5` (Phase 3),
`e60e24f` (Phase 4) · Baseline: 2.2.1 (dev) · Line: 2.3.0 (confirm before branching)

All 4 phases landed, back-to-back, no deviations from the plan.
Depends on: `fabric.guidance` (docs/status/done_JAPES_GOVERNED_GUIDANCE_ASSETS.md, landed and
already wired into `Fabric`/`FabricConfig` — verified below). Touches no other unreleased plan.

Driver: `jazzx-assistant` PR #6 (github.com/JazzX-LLC/jazzx-assistant/pull/6, "runtime feedback
injection") reimplements — from scratch, against `eval-service`, with none of japes's governance —
exactly what `fabric.guidance` already does: retrieve approved guidance relevant to a query and
inject it into the system prompt at turn time. The `fabric.guidance` design doc explicitly
anticipated this and explicitly deferred it: *"an InteractiveAgent hook can follow as a separate
additive plan once Jazz Assistant integration surfaces real requirements."* Those requirements
have now surfaced, from a second independent build rather than from this plan being executed
first. This plan closes that gap the right way: wire the hook `fabric.guidance` was always meant
to have, and give it a `GuidanceStore` backend that reads from `eval-service`'s retrieval (which is
genuinely better than japes's own reference retrieval — LLM context-summarization + lexical/
semantic hybrid, backed by real Postgres+embeddings, already proven by kernel in production) —
so the governance (lifecycle, safety validation, conflict detection, versioning, effectiveness
linkage) and the retrieval quality stop being a choice between one or the other.

## Grounding notes (verified 2026-07-27 against dev / local checkouts)

- `jazzx_sdk/fabric/guidance/{schema,store,lifecycle,retrieval}.py` (672 lines, 3 test files) is
  real, shipped, tested code — not just the design doc. `GuidanceStore` is a full async ABC
  (`put`/`get`/`versions`/`list`/`search`, all abstract). `InProcessGuidanceStore` (token-overlap)
  and `RagGuidanceStore(rag, collection_id)` (durable, KH-backed) are the two shipped
  implementations. `retrieval.retrieve(store, query, *, pack_id, applicability=None, k=3, now=None)`
  degrades to `[]` on `KnowledgeFabricError`, lets `KnowledgeHubAccessError` propagate.
  `render_guidance_block(matches)` groups by `ConfidenceWeight` (STRONG/STANDARD/ADVISORY), each
  line citing `asset_id@version`. `to_guidance_refs(matches)` produces `GuidanceRef`s for
  `CanonicalDecision.guidance_refs` (Guidance Effectiveness, §10.4).
- `fabric.guidance` **is already wired** into the platform: `Fabric.guidance` (in `fabric.py`) is a
  real attribute — `RagGuidanceStore(self.rag, config.guidance_collection_id)` when RAG is
  configured, else `None`. `FabricConfig.guidance_collection_id` exists (env
  `JAPES_KH_GUIDANCE_COLLECTION_ID`/`KH_GUIDANCE_COLLECTION_ID`). Exported from
  `jazzx_sdk/fabric/__init__.py`. **What's missing is exactly and only the InteractiveAgent
  consumption side** — confirmed by grep: zero references to "guidance" anywhere under
  `jazzx_sdk/agents/`.
- `jazzx_sdk/agents/interactive/agent.py::respond()`/`respond_stream()` both do
  `context, sources = await self._ground(scope)` then `instructions = self.spec.persona` (+
  `_GROUNDING_PREAMBLE` + context, when non-empty) before running the turn. `self._fabric` is
  already held on the instance (used by `_ground` → `resolve_knowledge(self.spec.knowledge, scope,
  self._fabric)`, in `knowledge.py`). This is the exact precedent to mirror for guidance — a new
  resolution step alongside `_ground`, not a caller-side wrapper (unlike PR #6's approach, which
  wraps the *caller's* orchestrator invocation because InteractiveAgent has no such hook itself).
- `InteractiveAgentSpec` (`spec.py`) has `knowledge: list[KnowledgeBinding]` triggering `_ground`,
  but no guidance-scoping field. `InteractiveResponse` (`response.py`) has `sources: list[Source]`
  (knowledge citations) but no field for `GuidanceRef`s — needed so a caller can attach them to
  whatever `CanonicalDecision` it builds downstream, per `fabric.guidance`'s own stated intent.
- `jazzx-assistant` PR #6 (`eval_service_client.py`, `handler.py`): `EvalServiceClient.
  get_feedback_config(entity_type, entity_id)` → `GET /api/v1/feedback/feedback-config` (dict with
  `dynamic_feedback_injection_position`, `inject_dynamic_feedback_template`,
  `similarity_threshold`, `max_results`, or `None` on 404/error); `find_similar(entity_type,
  entity_id, query, top_n, threshold)` → `POST /api/v1/feedback/similar` (list of feedback-item
  dicts, or `[]` on error). Both swallow every httpx/JSON error uniformly — no split between
  "transient failure" and "access denied," unlike `fabric.guidance.retrieve`'s explicit split.
  `_maybe_inject_feedback` gates on: flag on, `eval_service_url` set, `agent_id` present, config
  exists with `dynamic_feedback_injection_position == "system_prompt_append"` (v1 only supports
  this position), `find_similar` returns ≥1 item — then mutates
  `orchestrator.spec.persona = orchestrator.spec.persona + block` via `model_copy`.
- `eval-service` (`app/feedback/api.py`, `app/feedback/models.py`): `POST /api/v1/feedback/similar`
  is real, in production for kernel ("kernel's dynamic feedback injector is the first caller"):
  resolves `FeedbackConfig` (per-entity, falling back to global) → renders `(system_prompt,
  messages)` into one text blob → LLM-summarizes it (`config.summary_llm_id`) → lexical-then-
  cosine-rerank retrieval (`retrieval_mode`: `combined`/`lexical`/`semantic`) → returns matches
  closest-first, capped at `top_n`/`max_results`. `FeedbackConfig` has a real review gate
  (`FeedbackDisplayStatus`: `pending_review`/`under_review`/`approved`/`rejected`, with a
  `FeedbackStatusHistory` audit trail) but **no versioning, no supersession, no safety validation,
  no conflict detection** — a shallower gate than `fabric.guidance`'s lifecycle statemachine.
  `FeedbackInjectionPosition`'s own docstring: "kernel/eval-service do not share an llm table" and
  "eval-service stores the value but does not act on it" — confirming injection logic is,
  by eval-service's own design, a **consumer-side** concern (kernel has one, PR #6 built a second,
  independent one; this plan builds a third, shared, governed one in japes).

## Design decision — what this plan does and does not unify

`eval-service`'s `Feedback`/`FeedbackConfig` and japes's `GuidanceAsset` are two different objects
with two different review models (a display-status flag vs. a full lifecycle statemachine with
versioning/safety-validation/conflict-detection). **This plan does not merge them.** It builds a
one-way, read-only bridge: japes reads eval-service's already-approved feedback through the
`GuidanceStore` interface, gaining `fabric.guidance`'s confidence-weighted rendering and
`GuidanceRef` effectiveness linkage on top of eval-service's better retrieval. It does not push
japes-authored `GuidanceAsset`s into eval-service, and it does not attempt to reconcile the two
lifecycle models into one. Whether that deeper unification is worth doing is a bigger, separate
question for whoever owns both systems — flagged here, not decided here.

## Phase 1 — the InteractiveAgent hook (no eval-service dependency yet)

Add `InteractiveAgentSpec.guidance_pack_id: str | None = None` (mirrors the `pack_id` parameter
`retrieval.retrieve()` already requires) and `InteractiveAgentSpec.guidance_applicability:
dict[str, str] = {}` (passed through to `retrieve()`'s `applicability` subset-match).

In `agent.py`: a new `_apply_guidance(query, scope) -> tuple[str, list[GuidanceRef]]` alongside
`_ground`, called from both `respond()` and `respond_stream()` right after `_ground()` resolves
`instructions`. `query` is `_last_user_text(messages)` (already computed elsewhere in the file for
guardrails — reuse it, don't recompute). Returns `("", [])` when `self.spec.guidance_pack_id` is
`None` or `self._fabric.guidance` is `None` (no fabric configured — same "additive, opt-in, never
raises" posture `_ground` already has for knowledge). Otherwise: `matches =
await retrieval.retrieve(self._fabric.guidance, query, pack_id=self.spec.guidance_pack_id,
applicability=self.spec.guidance_applicability, k=3)`, then `render_guidance_block(matches)` +
`retrieval.to_guidance_refs(matches)`. Append the rendered block to `instructions` the same way
grounding context is appended (after it, not before — grounding is factual context, guidance is
behavioral instruction, and the existing `_GROUNDING_PREAMBLE` framing shouldn't apply to it).

Add `InteractiveResponse.guidance_refs: list[GuidanceRef] = Field(default_factory=list)` —
additive; a caller attaches these to its own `CanonicalDecision` exactly as `fabric.guidance`'s
retrieval module always said a caller should, but now the SDK hands them over already-computed
instead of requiring the caller to run `retrieve()`/`to_guidance_refs()` itself.

Acceptance: an `InteractiveAgent` with `guidance_pack_id` set and a fabric whose `.guidance` is an
`InProcessGuidanceStore` seeded with one deployed, applicable asset appends the rendered block to
the system prompt actually sent to the LLM (assert on the captured `instructions`/`system_prompt`
argument, mirroring how `_ground`'s existing tests assert on grounding context) and returns that
asset's ref in `InteractiveResponse.guidance_refs`. Omitting `guidance_pack_id` — the overwhelming
majority of today's specs — is provably byte-identical to current behavior (no fabric.guidance
call attempted at all, not just an empty result).

## Phase 2 — a general-purpose eval-service read client

New `jazzx_sdk/clients/eval_service_client.py`: `EvalServiceClient.get_feedback_config(entity_type,
entity_id)` / `.find_similar(entity_type, entity_id, *, query=None, top_n=None, threshold=None)`,
generalizing PR #6's client (same shape, same best-effort swallow-and-log posture, same
`httpx.MockTransport`-testable constructor) to platform level so a *third* consumer never
reimplements it a third time. This is a pure client — no `GuidanceStore` semantics here, no
`fabric.guidance` imports; it belongs beside `KnowledgeHubClient` in `jazzx_sdk/clients/`, not
inside `fabric/guidance/`.

Design intent for the docstring: eval-service is the shared source of truth for feedback data
across kernel, jazzx-assistant, and (via this client) japes; this client is the one place that
knows its wire format, so a future eval-service API change is one file to update, not N.

Acceptance: `httpx.MockTransport`-driven tests for both calls (200/404/error for config;
list/`{"items":...}`/`{"results":...}`/error for similar — mirroring the response-shape
flexibility PR #6's own tests already established as real, not hypothetical).

## Phase 3 — `EvalServiceGuidanceStore`

New `jazzx_sdk/fabric/guidance/eval_service_store.py`: `EvalServiceGuidanceStore(client:
EvalServiceClient, *, entity_type: str = "agent")` implementing `GuidanceStore.search()` only —
`put`/`get`/`versions`/`list` raise `NotImplementedError` with a message naming this store
read-only-by-design (eval-service-sourced feedback is authored/reviewed in eval-service's own UI,
not through japes's lifecycle; this store's only job is making it retrievable through the same
seam `fabric.guidance` already exposes). Flag this ABC-vs-read-only-adapter tension explicitly in
the module docstring rather than papering over it — splitting `GuidanceStore` into a narrower
searchable-only protocol is a legitimate follow-up if a second read-only backend ever shows up,
not something to speculate into existence for one caller now.

`search(query, *, pack_id, applicability=None, k=8, status=DEPLOYED)`: calls
`client.get_feedback_config(entity_type, pack_id)`; returns `[]` if no config or no
`dynamic_feedback_injection_position` (mirrors PR #6's own gate — an entity not enrolled for
injection in eval-service shouldn't silently get japes-side guidance either). Else calls
`client.find_similar(entity_type, pack_id, query=query, top_n=k, threshold=cfg.get
("similarity_threshold"))` and adapts each item into a `GuidanceAsset`: `guidance` from
`feedback_text` (fallback `actionable_item`), `trigger_patterns=[guidance[:200]]` (eval-service has
no separate trigger-pattern concept — the guidance text itself is the closest analog, truncated so
it stays a *pattern*, not the full text duplicated), `confidence=ConfidenceWeight.STANDARD` always
(eval-service has no confidence-weight concept; STANDARD is the least presumptive default —
neither forcing a directive nor burying it as background), `status=GuidanceStatus.DEPLOYED` always
(eval-service already filtered to approved), `version` synthesized from the item's own id/updated-
at (eval-service has no content-hash versioning), `provenance.feedback_id` set to the eval-service
item's id, `pack_id` passed through unchanged. `applicability` is ignored (eval-service's own
`entity_type`/`entity_id` scoping already did the narrowing before this store ever sees a result;
layering japes's subset-match on top would either no-op or incorrectly filter data eval-service
already scoped correctly).

Fabric wiring: `FabricConfig` gains `guidance_backend: Literal["rag", "eval_service", "none"] =
"rag"` and `eval_service_url: str | None = None` (env `JAPES_EVAL_SERVICE_URL`); `Fabric.__init__`
picks the store accordingly (`"eval_service"` requires `eval_service_url` set — a `ValueError` at
construction time, not a silent fallback, if it's misconfigured). Default stays `"rag"` — no
existing deployment's behavior changes.

Acceptance: `retrieve()`/`render_guidance_block()`/`to_guidance_refs()` (unchanged from Phase 1)
work identically against an `EvalServiceGuidanceStore` backed by a `MockTransport` fixture as they
do against `InProcessGuidanceStore` — same primitives, different backend, proving the seam.

## Phase 4 — end-to-end proof

A test-only fixture wiring `InteractiveAgentSpec(guidance_pack_id=..., ...)` against a `Fabric`
whose `.guidance` is an `EvalServiceGuidanceStore` on a mocked eval-service transport, through a
full `respond()` call with a `ScriptedLLM` (existing test double), asserting: the rendered guidance
block appears in the actual prompt sent to the LLM, and `InteractiveResponse.guidance_refs` names
the eval-service feedback item's synthesized asset id. This is the concrete "three lines in an
assistant" the original `fabric.guidance` design doc promised, finally proven against a real
backend rather than only the in-process one.

## Out of scope

- Migrating `jazzx-assistant` PR #6 itself onto this hook. That PR is shipped/in-review in a repo
  this plan doesn't own; the right next step is proposing a follow-up PR to that team once this
  plan lands, not silently rewriting their code from here.
- Any change to `eval-service` or to kernel's existing (first) consumer of `/feedback/similar`.
- Reconciling eval-service's `FeedbackConfig`/`display_status` review model with `fabric.guidance`'s
  lifecycle statemachine into one system (see Design decision above).
- Improving `InProcessGuidanceStore`'s own retrieval quality (token-overlap) — orthogonal; Phase 3
  gives callers a better-retrieval option without touching the reference implementation.
- Any jaci-side production feature. Phase 4's fixture is SDK-level proof, not a scenario UI change.

## Sequencing

Phase 1 has no eval-service dependency and is the highest-value piece alone — it closes the actual
gap (`fabric.guidance` has no runtime hook) using only what's already shipped, and should land
first regardless of whether Phases 2-3 follow immediately. Phase 2 is a small, self-contained
client and can proceed in parallel with Phase 1. Phase 3 depends on both. Phase 4 depends on all
three and is the acceptance gate for the plan's own claim (governance and retrieval quality
shouldn't be a tradeoff) — don't skip it, since an untested Phase 3 adapter is exactly where a
silent mismatch between eval-service's response shape and `GuidanceAsset`'s required fields would
hide.
