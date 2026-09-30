# v2.5.7: follow-ups from the 2.5.6 audits, the policy store, and sibling finds

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Branch `v2.5.7`, cut from `dev` at `428ee718` (2.5.6 in review as PR #81) on 2026-09-29. Plato
stays 0.1.8 until something Plato-visible lands. Sources: the full-range audit of 2.5.6 (the
orphaned pre-push review, slices 1-8), the PR #81 bot rounds, the push reviews, and the sibling
survey of 2026-09-29.

## 1. Small correctness fixes (first, independent)

1.1 Cache-write tokens on the Agents SDK path: `agents/run_kit.py` `_usage_to_token_usage` sets
    `cache_creation_tokens` (macer fixed the same; `llm/providers/openai.py` already reads it).
1.2 Compaction trigger: `llm/cost_tracker.py` `latest_input_tokens` counts the whole prompt, not
    only fresh input (policy-workbench measured the gap with caching on).
1.3 Keep references to fire-and-forget tasks: `server/run_routes.py` (`on_start`) and
    `plato/api/runs.py` (`_drain`).

## 2. Policy store without Knowledge Hub (decided 2026-09-29)

KH removed its policy/rego APIs; the next client-api pin bump fails the whole KH client import.
2.1 The KH client's policy/rego/models imports become an optional group: the client stays up
    when they are gone.
2.2 Retire the KH policy surface: the client's policy and bundle methods,
    `tools/knowledge_hub/policy.py`, the MCP policy tools, and the `fabric.opa` placeholder.
2.3 Dropped (decided 2026-09-29): the pack store (`DbPackVersionStore`) is the policy store of
    record, and policy drafts live in the draft store. `fabric.canonical.store.PolicyStore` stays on
    KH entities (the entity API, not the removed policy API), alongside the other canonical objects.
Rego, if wanted later, is a compiled projection of canonical policy (as the Z3 rule packs are).

## 3. Runs layer

3.1 A store-level "finish unless terminal", shared by `ResilientRunner`, `CaseRunner` and
    `ChatCoordinator` (`TODO(terminal-check-not-under-lock)`, `TODO(reaped-run-overwritten-on-return)`).
3.2 A run claimed while `close` runs is settled too (`RunWorker`, `ChatCoordinator.close`).
3.3 Heartbeat hardening (juno): an optional heartbeat session factory, a boot check that the
    reaper's TTL clears the DB pool timeout, a reap reason naming the stale claim.
3.4 `RunWorker` claim headroom (policy-workbench): stop claiming a long run near the lifetime end.

## 4. Audit items

4.1 Formal `check_rules` treats an NA matrix cell (`always_false`) as intended, not as an
    infeasible scope.
4.2 Mode `temperature` for non-reasoner modes: honoured or refused, not silently dropped.
4.3 One `policy_assessment` kind constant (manifest loader, kinds, assessment), and the fact
    catalog's metric read shared with `assessment._metrics`.
4.4 `AssessmentSpec` validated at load/publish (a misspelt key fails there, not at first assess).
4.5 Plato's runs route bounds its echoed errors (`reason(exc, limit=...)`), as packs does.
4.6 Feedback retrieval follows the current layer's RAG store (`TODO(feedback-rag-bound-at-boot)`;
    `RagFeedbackIndex` keys its collection cache on the store).
4.7 A non-path `PackSource`'s guardrails are read (`TODO(packsource-guardrails-dropped)`), and a
    linter crash is not an `unloadable` pack (`TODO(lint-crash-blocks-publish)`).
4.8 A session closed with no turns is not "complete"; an empty nested gold mapping is not vacuous.
4.10 Done: `formulate_json_policy` names the candidate for an unsupported kind or operator.
     Refusing the whole draft for a bad candidate is the formulation's design (its tests pin it:
     invented quote, missing binding, mistyped value), so candidates are not skipped.
4.9 Platinum Select's optional inputs (`channel`, `rural_property`, `housing_history`, ...): the
    missing-input policy question (`TODO(absent-channel-escapes-correspondent)`), with Acra.

## 5. Sibling finds

5.1 `InputFilter` tool-output elision stubs (macer), over the existing `ReferenceStore`.
5.2 `FeedbackApiSink` takes a caller-headers provider, as `PlatoClient` does (jaci subclasses it).
5.3 `pack_archive` deterministic (fixed mtimes).
5.4 MCP server Host/Origin checks (eval-service) before any off-loopback bind.

## 6. Hybrid policy evaluation (direction, 2026-09-29)

Deterministic engines (canonical conditions, Z3, Rego if a consumer appears) complemented by
JTBD/reasoning-LLM. Candidates, larger and later in 2.5.7 or after:
6.1 A hybrid assessment: deterministic rules first, `natural_language` rules through adjudication,
    one verdict with each rule's engine named.
6.2 Extraction proposes a deterministic condition wherever the text allows one.
6.3 Engine agreement: evaluator vs Z3 on the gold cases for rules both can decide.

## Not in 2.5.7

jazzx-assistant transport adapter over `ChatTurnHandle.events` (after it bumps off 2.5.0);
Phase C of the chat runtime (sessions/resources); human-approval pause/resume (Plato Phase 3).
