# Engineering Queue from the Eval-Service / JAPES Convergence Analysis

> **Status (2026-08-13): 0.2 shipped, in v2.4.0 (pushed)** — execution-state vs quality-verdict
> separation in `CaseResult`/`EvaluationResults`, plus the wire-adapter fix that was already
> conflating them. **0.1 disputed, not a mechanical fix** — verified `EvalServiceGuidanceStore`'s
> hardcoded `DEPLOYED`/`STANDARD`/`1.0` values are each a considered decision (own code comments),
> not an oversight; the lifecycle-state (`DEPLOYED`) piece is worth fixing, confidence/relevance
> less clearly so — needs a real decision, not just applying the queue's literal ask.
> **0.3 could not be located** in this codebase at all — may describe eval-service-side code.
> **0.4, 3.3, and all of Tier 1/2/4 remain untouched.**

**Date:** 2026-08-12 · **Scope:** actionable coding tasks arising from the convergence proposal, our response to it, and the source verification pass.
**Companion to:** `claude/Japes_Enhancement_Backlog.md` (from the Studio review — different source, no overlap except where noted).

**Provenance key** — **[P]** from the convergence proposal · **[V]** found in our source verification · **[R]** our recommendation / dissent · **[P+V]** proposal names it, we confirmed it in code.

**Repo key** — `japes` = `/Users/sangit/src/japes` · `juno` = `/Users/sangit/src/juno` · `contracts` = `japes/jazzx_eval_contracts/`

---

## Already done — remove from any existing backlog

**`replicas` default corrected.** **[V]** Commit `56700fe`, 2026-08-10, changed `replicas: int = 3` → `1` in `agents/adjudication/spec.py`, `agents/adjudication/pipeline.py` and `conductor/replication.py`, and put the measurement in the docstring. Anything still carrying "fix replicas=3" is stale — close it.

---

## Tier 0 — do now, no dependencies, small

### 0.1 Stop `EvalServiceGuidanceStore` fabricating governance metadata **[P+V]**

- **Repo/file:** `japes` — `jazzx_sdk/fabric/guidance/eval_service_store.py`
- **Problem:** it *"fabricates trigger patterns from feedback text, uses `STANDARD` confidence, marks results `DEPLOYED`, and returns flat score `1.0` because the eval API omits those concepts."* The SDK is stamping guidance `DEPLOYED` that nobody deployed.
- **Change:** return explicit `UNKNOWN` / `None` for lifecycle state, confidence and relevance where the eval API does not supply them. Do not synthesise trigger patterns. Let the consumer decide what an unknown means.
- **Why not wait for `ApprovedLearningAssetV1`:** the proposal sequences this behind that contract; we disagree (response §4). The misrepresentation is live now and the fix is independent.
- **Acceptance:** no code path in this store produces a lifecycle, confidence or relevance value not present in the upstream response; a test asserts `UNKNOWN` propagates rather than a default.
- **Size:** hours. **Blocked by:** nothing.

### 0.2 Separate execution state from quality verdict in `CaseResult` **[P]**

- **Repo:** `japes` — `CaseResult` and its aggregate adapter
- **Problem:** *"`CaseResult` and its aggregate adapter still overload `passed` when errors exist"*, against invariant 10: *"Execution failure and quality failure remain independent. A successfully executed response can fail evaluation; an infrastructure failure normally has no quality verdict."*
- **Change:** persist `CaseEvaluationV1` independently of run status; `passed` reflects quality only; infrastructure failure yields no quality verdict rather than `passed=False`.
- **Acceptance:** a case that errors mid-run produces a run status of failed and **no** quality verdict; a case that completes and scores below bar produces status succeeded and `passed=False`.
- **Size:** small. **Blocked by:** nothing.

### 0.3 Guard against self-binding in source identity **[P]**

- **Repo:** `japes` (and the eval-service side of the contract)
- **Problem:** the rule *"a feedback item's own local ID is never used as a placeholder entity binding"* / *"do not bind a feedback item to itself"* implies the current fallback can do exactly that.
- **Change:** make entity resolution failure explicit — raise or return an unresolved marker. Never invent a UUID or bind a message ID as an agent *"merely to satisfy the type system."*
- **Acceptance:** unresolvable entity context produces a typed unresolved result, and a test asserts the feedback's own ID never appears as its entity binding.
- **Size:** small. **Blocked by:** nothing.

### 0.4 Resolve the `feedback` table-name collision **[P]**

- **Repos:** `japes` (`DbFeedbackStore`) and `eval-service`
- **Problem:** *"both implementations currently claim a table named `feedback` with different schemas and lifecycle ownership."* `DbFeedbackStore` must remain *"a standalone/offline Japes repository… It must not be attached to eval-service's database."*
- **Change:** namespace or rename the JAPES-side table; add a guard or documented refusal if pointed at an eval-service database.
- **Acceptance:** the two can coexist in one Postgres instance without collision; a test or migration note records the boundary.
- **Size:** small, but coordinate with eval-service. **Blocked by:** nothing.

---

## Tier 1 — the contract-acceptance slice (gates everything downstream)

The proposal is explicit: *"The generic attribution spine follows only after that acceptance path is durable and idempotent."* Nothing in Tier 2 should start before this lands.

### 1.1 Publish and pin `jazzx-eval-contracts`, with the floor on the contracts package only **[P, amended R]**

- **Repo:** `contracts`
- **Proposal says:** *"lower its Python floor to match eval-service 3.11, unless eval-service is deliberately upgraded first."*
- **We propose instead:** set `requires-python >= 3.11` on **`jazzx-eval-contracts` only**; leave the JAPES floor untouched. Evidence is in the proposal itself — the schema snapshots *"18/18 pass in isolated Python 3.11 and 3.12 checks."* Lowering the whole SDK to match one consumer defeats the point of the split distribution and collides with existing dependency constraints.
- **Acceptance:** contracts package publishes and installs on 3.11 and 3.12 with pydantic only; JAPES's own floor unchanged; snapshot tests green on both.
- **Size:** small. **Decision needed first:** yes — this is the cross-team call. **Blocked by:** agreement with eval-service.

### 1.2 Split `FeedbackSink` from local repository semantics **[P+V]**

- **Repo:** `japes` — `jazzx_sdk/evaluation/feedback_sink.py`
- **Problem:** the prototype *"currently inherits the broad local `FeedbackStore`, regenerates submission event IDs indirectly, omits identity headers, and targets a response shape eval-service does not serve."*
- **Four sub-tasks, all required for the first proof:**
  1. Split the write-sink ABC from `LocalFeedbackRepository` query/delete semantics.
  2. Make `event_id` **stable across retries** — idempotency depends on it.
  3. Propagate request identity / security headers on `EvalServiceFeedbackSink`.
  4. Point it at the agreed V1 acceptance route and the response shape eval-service actually serves.
- **Acceptance (the proposal's own first proof):** a JAPES interactive response submits `thumbs_down` with a typed rating, registered entity UUID, opaque conversation/message refs, generic trace refs, propagated identity and a stable event ID; **a forced ambiguous retry produces exactly one eval-service feedback row and returns the same `FeedbackAcceptedV1`.**
- **Size:** medium. **Blocked by:** 1.1, and the agreed route existing on the eval-service side.

### 1.3 Stop implicit neutral creation on service-backed interactive paths **[P]**

- **Repo:** `japes`
- **Problem:** legacy `Reaction` remains positive/negative/neutral while the V1 contract emits up/down and rejects neutral.
- **Change:** no implicit neutral on any service-backed path; preserve explicit local legacy compatibility.
- **Acceptance:** a service-backed interactive path cannot emit neutral; local/offline path unchanged.
- **Size:** small. **Blocked by:** 1.2 (same code area).

### 1.4 Chase the five submission blockers **[P]**

- **Not code yet.** The proposal gates the slice on *"the five submission blockers identified in the 2.3.6 reconciliation"* → `JAPES_2_3_6_RECONCILIATION.md`. We have not located that document. **Someone needs to find it, confirm the five, and check whether 1.2's sub-tasks are the same five or additional to them.**

---

## Tier 2 — the attribution and learning spine (after Tier 1)

### 2.1 Add and consume `ApprovedLearningAssetV1` **[P]**

- **Repos:** `contracts` + `japes`
- **Problem:** *"Japes 2.3.6 ships every item below except `ApprovedLearningAssetV1`; that read contract remains required."* Its absence is why 0.1 exists.
- **Change:** define the read contract with real provenance, confidence, scope, version and relevance score; consume it in the guidance adapter so the fabricated fallbacks from 0.1 can be deleted rather than merely marked unknown.
- **Acceptance:** the guidance store returns upstream-supplied lifecycle/confidence/relevance; the `UNKNOWN` fallback path from 0.1 becomes unreachable in the service-backed case.
- **Size:** medium. **Blocked by:** 1.1, and eval-service publishing the approved-learning read endpoint.

### 2.2 Carry learning-candidate ID and version into `GuidanceProvenance` **[P]**

- **Repo:** `japes`
- **Acceptance:** a synthesised `GuidanceAsset` can be traced back to the `LearningCandidateV1` that produced it, by ID and version.
- **Size:** small. **Blocked by:** 2.1.

### 2.3 Deprecate `Feedback.to_signal()` for service-backed feedback **[P]**

- **Repo:** `japes`
- **Rationale:** *"The current behavior—negative means high priority, everything else low—does not know the affected component, evidence, confidence, safe scope, or whether the feedback is actionable."* The reaction handler *"must not call `Feedback.to_signal()` and treat a complaint as a known change target."*
- **Change:** route production conversion through `LearningCandidateV1` → `ImprovementSignal` (carrying `feedback_id` + `attribution_id` + evidence provenance) → Curator. Keep `to_signal()` explicitly labelled local/offline.
- **Size:** medium. **Blocked by:** 2.1, and the eval-service attribution coordinator existing.

### 2.4 Complete execution-result mapping and scorer version/threshold on the wire **[P]**

- **Repo:** `japes` + `contracts`
- **Our amendment (response §1):** if you accept that thresholds are domain policy, the wire result should carry `policy_ref` + `policy_version` rather than a raw threshold value authored in the control plane.
- **Size:** medium. **Blocked by:** the ownership decision in response §1.

---

## Tier 3 — our additions, not in the proposal

These govern **invocation and observability** of the learning code, which the proposal does not cover (it governs provenance and promotion). Independent of Tier 1 and 2 — can run in parallel.

### 3.1 Put `EvaluatorMode` on the governed path **[R]**

- **Repo:** `japes` — `jazzx_sdk/modes/evolve/`
- **Problem:** `EvaluatorMode` never migrated to `BaseMode`. It constructs its own `AsyncOpenAI` client and hand-parses JSON, bypassing the LLM Gateway, `resolve_model`, retry and token accounting. **A truncated response silently yields `improvement_signals=[]`** — the compounding loop stops with no error anywhere.
- **Change:** migrate onto `BaseMode` / `ReasoningAgent`; use `resolve_model`; add retry; **raise a typed error on truncation rather than returning an empty signal list.**
- **Acceptance:** a truncated or malformed response raises rather than returning empty; token usage appears in accounting; the model is resolved through the gateway.
- **Also relevant to the proposal's own stance:** *"Analyzer prompts and artifacts are auditable and versioned. Prompt injection in source evidence is treated as untrusted data"* — an ungoverned client bypasses exactly that auditing.
- **Size:** medium. **Blocked by:** nothing.

### 3.2 Put `Curator.synthesize_bucket` on the same path **[R]**

- **Repo:** `japes` — `jazzx_sdk/modes/evolve/curator.py`
- **Problem:** third execution path, no retry, no truncation handling, no token accounting. Curator is also only half-built — *"Layer 1 routing operational, Layer 2 LLM synthesis deferred."*
- **Size:** medium. **Blocked by:** 3.1 (same pattern).

### 3.3 Make knowledge failures loud **[R, P0 in the existing backlog]**

- **Repo:** `japes` — `jazzx_sdk/agents/interactive/knowledge.py` (`resolve_knowledge`, `docs:` branch)
- **Status correction:** the *replacement* already shipped — `Skill.reads` generates per-source list/read/search tools over `fabric.docs` (landed v2.3.2). The legacy push path is still in the tree and still fails quietly: it appends `[doc] {name}` with no content, and swallows any listing exception as best-effort.
- **Change, in order:** (a) migrate remaining callers onto `reads:`; (b) then make the legacy branch fail loud. **(b) is breaking** — follow the precedent set for mode prompts: a `strict_*` flag, a new typed error, a CHANGELOG "Breaking" heading, and pre-landing checks against dependent packs.
- **Do not put a day estimate on this** — there is no tracked, sized plan for the push-path migration.
- **Size:** unknown until callers are enumerated. **Blocked by:** a caller audit.

### 3.4 Make `BaseMode.system_prompt` fail loud on a missing pack asset **[R]**

- **Repo:** `japes` — `jazzx_sdk/modes/base.py`
- **Problem:** it catches `FileNotFoundError` and substitutes a nine-word generic prompt, contradicting `resolve_mode_prompt`'s documented contract that it raises. A pack with a misnamed mode file runs on a generic prompt and reports nothing.
- **Change:** same `strict_prompts` flag pattern as 3.3(b).
- **Size:** small. **Blocked by:** the same breaking-change discipline.

---

## Tier 4 — Juno-side, governance gaps

### 4.1 Make the prompt commit an enforced gate, not a convention **[V]**

- **Repo:** `juno` — `app/copilot/skills/tool_defs/eval_tools.py` (`commit_eval_optimized_prompt`), calling `POST /api/v1/agents/{agent_id}/prompt`
- **Problem:** it writes the **live** agent configuration. The response model is `{agent_id, optimization_run_id, prompt_committed, committed_at, agent_name}` — no draft, no candidate, no pending state. The only guard is prompt prose: *"This is the only destructive step — always ask before doing it."* A model that ignores that text commits straight to live.
- **Contrast:** `eval-prompt-fixer` has a real UI accept/reject diff before Apply. That path *is* human-gated. The pattern exists; it just isn't used here.
- **Change (pick one):** (a) write a draft/candidate requiring an explicit second action; or (b) route through the same accept/reject diff surface as `eval-prompt-fixer`.
- **Why it matters:** invariant 9 — *"No direct feedback-to-production-learning path. Raw feedback may create a draft candidate, never an approved or deployed asset."* This is arguably a live violation, and it belongs on the proposal's gap list.
- **Size:** small–medium. **Blocked by:** a product call on which option.

### 4.2 Add a reviewer gate to platform promotion **[V]**

- **Repo:** `juno` — `app/skill/service.py` (`promote_to_platform`, `_check_owner`), `app/skill/api.py`
- **Problem:** the only authorization on promoting a personal skill to **platform scope** is authorship. The author of a personal skill can promote it platform-wide unilaterally. Identity comes from an `X-User-Id` header — service-internal trust, not independently verified.
- **Change:** require a reviewer/admin role for `scope: user → platform`. Leave `draft → published` as-is.
- **Size:** small. **Blocked by:** whether a role model exists to check against.

### 4.3 Adapt Juno's meta-profile analysis behind `AttributionAnalyzer` **[P]**

- **Repo:** `juno` + eval-service
- **Change:** wrap the evidence-matrix output as `FeedbackAttributionV1`; register Juno as an `EvidenceProvider`; retire the Juno-only dispatch path so *"the eval-service public resource is `attribution`, not `juno_analysis`."*
- **Size:** large; mostly eval-service work. **Blocked by:** Tier 1.

---

## Sequencing summary

```
Tier 0  (4 tasks, all small, no blockers)  ──►  start immediately
Tier 3  (4 tasks, parallel track)          ──►  start immediately, independent of contracts
Tier 1  (contract acceptance slice)        ──►  needs the 3.11 floor decision + eval-service route
Tier 2  (attribution/learning spine)       ──►  strictly after Tier 1
Tier 4  (Juno governance)                  ──►  4.1 and 4.2 now; 4.3 after Tier 1
```

**Two decisions gate real work:** the Python-floor question (1.1) and the scorer-threshold ownership question (2.4, response §1). Both belong in the working session with the proposal's authors.

**One thing to find:** `JAPES_2_3_6_RECONCILIATION.md` and its five submission blockers (1.4).

---

## Notes for whoever picks these up

- Tier 0 and Tier 3 are safe to hand to a coding agent with the file paths above; each has a stated acceptance condition.
- Tier 1 and 2 are contract work and should not be started by an agent working alone — they need the cross-team route and schema agreed first.
- 3.3(b) and 3.4 are **breaking changes**. The house pattern for these is already established (strict flag + typed error + CHANGELOG "Breaking" + dependent-pack checks); follow it rather than inventing a new one.
- Verify current state before starting anything here. Between our first read and the verification pass, the SDK moved from 2.3.6 to 2.4.0 and one backlog item (`replicas`) was fixed underneath us.
