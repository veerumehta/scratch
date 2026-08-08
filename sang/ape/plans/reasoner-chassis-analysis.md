# From MACER to a JAPES Reasoner Chassis

**Deep analysis + concept map.** Read against source: `/Users/sangit/src/macer` (japes pinned at
`4b08850`, **v1.9.6**), `/Users/sangit/src/japes` (**v2.2.4**), juno architecture references.

> **Revision note.** An earlier draft of this document was written without access to the MACER
> source, from juno's architecture and debug references. Several load-bearing claims in it were
> wrong — the execution topology most of all. Everything below is checked against code, with
> `file:line`. §8 lists what changed and why, because the errors are instructive: they came from
> MACER's own `design/macer.md`, which is stale in the same places.

> **Companion docs.** `policy-ir-abstraction.md` — the pluggable policy-rule IR (P8).
> `domain-neutrality-and-config.md` — the SDK must not encode "mortgage" (or any domain) anywhere;
> a real violation of this rule was found in `jazzx_sdk/modes/catalog.py` and is fixed there (this
> claim was stale for a stretch — a completeness audit on 2026-08-07 caught that the fix hadn't
> actually landed yet despite this sentence; it landed for real 2026-08-08, see that doc's own
> status note). The domain flows through `Pack.domain`/`.segment`/`.regulatory_context` — already
> in the manifest schema, currently dead, needs wiring rather than a new mechanism.

> **P1/P2 shipped 2026-08-02** as part of the v2.3.0 local work (unpushed), right after P8:
> `jazzx_sdk.conductor.run_replicated_segments` (`conductor/replication.py` — `Segment`/`Replica`/
> `ReplicatedRun`/`ReplicaFailure`, built over the existing `fan_out` at both the segment and
> replica level) and `EnsembleCollapse` (`conductor/ensemble.py` — `DeterministicVote`/
> `AnyEscalate`/`LlmFold`, no registry — a pack picks its collapse strategy in code). `on_item`/
> `session_for` from this doc's original P1 signature sketch were dropped: `process` already
> receives `(segment, replica, precomputed)`, which is enough for a caller to close over its own
> session-binding without a dedicated parameter, and `StepObserver` (the closest existing type) is
> conductor-step-shaped, not item-shaped, so reusing it here would have been a category error
> rather than reuse. §4.4 (binding `k` to `llm/cost_tracker.py` budgets) is not wired — no caller
> exists yet to size it against.

> **P6 shipped 2026-08-02** (`jazzx_sdk/agents/reasoning/grounding.py`), right after P1/P2, closing
> out this doc's `P1/P2/P6/P8` build sequence. All four pluggable parts plus the gate: `Snippet`/
> `HeadingSnippetExtractor`, `KeywordPrefilter` (MACER's own weighting), `HeadingsOnlySelector`
> (built on `ReasoningAgent`, headings only, never body content), `InMemoryGroundingCache`
> (fingerprint-keyed via the existing `fabric.idempotency.content_fingerprint` — no TTL needed,
> a changed corpus just fingerprints differently), and `BrowseGate` (deny-only over the existing
> `authority.context` `InvocationContext`/`PermissionScope`, the same mechanism
> `InteractiveAgent._build_parent_tools` already uses — not a new gating mechanism). `page_ref`/
> `section_code` on `Snippet` are optional metadata a pack-supplied extractor can populate; the
> default `HeadingSnippetExtractor` leaves them `None` since no page/section concept exists
> anywhere else in the SDK to derive them from.

> **P5 shipped in full 2026-08-02/03** (this entry corrects the "half" note below, which is
> stale): `"segment_tail"` registered as a named compaction strategy
> (`jazzx_sdk.agents.interactive.memory.SegmentTailStrategy`) — the same algorithm
> `run_kit.strip_session` applies directly to a `SQLiteSession`, extracted into a shared pure
> function (`run_kit.segment_tail_items`) so both callers stay in sync. A no-op for a plain
> chat-style history with no `type` field (only meaningful for a Responses-API/agentic session's
> items) — documented, not a bug. **The other half also landed**: `"reasoning_group_evict"`
> (`jazzx_sdk/agents/interactive/memory.py`, `ReasoningGroupEvictStrategy`, backed by
> `run_kit._reasoning_item_groups`/`run_kit.evict_reasoning_groups`) — group-aware eviction of
> MACER's `input_filter.py` shape, budgeted on serialized-char-count (matching MACER's own
> byte-budget convention) rather than strict token-count, which is a fine fidelity gap, not a
> functional one. P3/P4/P7 remain unbuilt — no caller yet, and each needs the full
> `AdjudicationAgent` chassis this doc's own build sequence puts much later (Phase 4/6).
>
> **Verified 2026-08-07, re-reading this doc against current code (P1/P2/P6/P8 API surfaces,
> MACER's own `jtbd_runner.py`/`jtbd_agent.py`/`summarization_agent.py`/`guideline_enrichment.py`,
> and the 5 modes' actual implementations):** P1/P2 (`jazzx_sdk/conductor/replication.py`,
> `ensemble.py`) have zero drift from this doc's description — signatures, precompute-once-per-
> segment, failed-replica exclusion, `key_of`-based regrouping, all match. MACER's own adjudication
> logic is **unchanged** since this doc was written — the files moved into a `src/macer/jtbd/`
> subpackage but the last commit touching any of `jtbd_runner.py`/`jtbd_agent.py`/
> `summarization_agent.py`/`guideline_enrichment.py` predates this analysis (2026-07-28, before the
> 2026-08-01 draft). Nothing in §1/§2/§4/§8 needs re-checking against a moving target.
>
> **The crux, now precisely confirmed rather than assumed**: `jazzx_sdk/modes/operational/
> {reasoner,narrator,governor,investigator,verifier}.py` each construct exactly one
> `ReasoningAgent(...)` and call `.run()` **once**, in their own `run()` method. Zero references to
> `run_replicated_segments`, `EnsembleCollapse`, `PrecomputedGrounding`, or `BrowseGate` anywhere in
> `jazzx_sdk/modes/`. So: **P1/P2/P5/P6/P8 all exist and work as standalone primitives, but nothing
> wires them together, and nothing wires them into a mode.** `ReasoningAgent` + the five modes,
> as they exist today, cannot reproduce MACER's segment×replica×batch+grounding+ensemble topology —
> not because a primitive is missing, but because **Phase 4 — the chassis that wires them
> together — has not been started.** `jazzx_sdk/agents/adjudication/` does not exist.
> `examples/adjudication_demo/` (this doc's own Phase 4 deliverable) does not exist either; the
> only "adjudication" hit anywhere in japes is `tests/test_adjudication_policies.py`, which tests
> `jazzx_sdk.evaluation.scorers`' unrelated same-named scoring-composition policies, not this
> chassis. **Restated: Phases 0-3 of §7's build sequence are now fully done (P1/P2/P5/P6/P8);
> Phase 4 is the next and only remaining blocker before Phase 5 (the actual MACER-parity question)
> can even start.** See the new §4c below for what Phase 4 concretely requires, now that the
> primitives it wires together are no longer speculative.
>
> **Phase 4 shipped 2026-08-07.** `jazzx_sdk/agents/adjudication/` now exists, wiring P1/P2/P4/P8
> into the §4c plan exactly: `workspace.py` (`EvidenceWorkspace`/`Mount`, narrowing the ambient
> `PermissionScope` to a segment's mounts for the duration of its calls — P4), `partition.py`
> (`partition_rules`, splitting a segment's `Rule`s into DETERMINISTIC/LIVE by resolved
> `ConditionEvaluator.execution` — P8), `spec.py` (`AdjudicationAgentSpec`, domain-neutral —
> verified it never branches on `regime_values`/`status_vocabulary`, just stores them, per
> `domain-neutrality-and-config.md`), `pipeline.py` (`run_segment`, batching every LIVE obligation
> into one prompt per replica — MACER's own `verify_all_jtbds` shape — then P1 `replicated` +
> P2 `collapse`; DETERMINISTIC rules go straight through their evaluator, `k=1`, no LLM), and
> `agent.py` (`AdjudicationAgent`, fanning `run_segment` out across segments with `fan_out(...,
> degrade=True)` so one bad segment doesn't sink the case, then thin `ReasoningAgent`-based
> `_reconcile`/`_emit` defaults — pack-overridable seams, not `GovernorMode`/`NarratorMode`; see
> `agent.py`'s own docstring for why those modes are the wrong shape here).
>
> A new `NaturalLanguageCondition`/`NaturalLanguageEvaluator` closed the one real P8 gap this
> wiring surfaced: `Condition`'s union had no LLM-backed kind, so a chassis-level obligation had
> nowhere to declare itself LIVE. `RuleOutcome`s for a rule with `condition=None` are correctly
> never fabricated — confirmed against `DefaultPolicyExpert.check_compliance`'s own handling
> (skipped, not defaulted to `SATISFIED`) and matched exactly in `_evaluate_deterministic`.
>
> Mode-tagging for the Trace (this doc's own outstanding "so the Trace doesn't mislabel every LLM
> call 'reasoner'" problem) turned out to need a real mechanism addition, not just a config value:
> `mlflow_bridge`'s existing `mode_map` is keyed on span_type (`LLM`/`TOOL`/...), so `run_segment`'s
> adjudicate call and `AdjudicationAgent._emit`'s narrative call — both plain `LLM` spans — were
> indistinguishable to it. Added `name_patterns` (an ordered `(substring, mode)` list, checked
> against `span.name` before falling back to `mode_map`) to `span_to_trace_step`/
> `spans_to_canonical_trace`; `agents/adjudication/tracing.py`'s `adjudication_name_patterns()`
> supplies the chassis's own list (`":adjudicate:"` → REASONER, `":emit"` → NARRATOR). DETERMINISTIC
> obligations and the default no-op `_reconcile` produce no LLM span at all, so there is nothing to
> tag for them yet — a pack overriding `_reconcile` with a real call extends the list itself.
>
> `examples/adjudication_demo/` is the toy end-to-end pack this doc called for — a two-segment
> mortgage-underwriting demo (`income`/`property`, each mixing one DETERMINISTIC `Expression` and
> one LIVE `NaturalLanguageCondition`), mirroring `examples/loan_assistant/`'s spec-plus-harness
> shape. Full japes suite green throughout (2487 passed, 3 skipped, no failures) — no test outside
> the new files needed a change. **Phase 5 (the actual MACER-parity question — does this chassis,
> pointed at MACER's own real obligations/policy corpus, reproduce its behavior) is next and is
> explicitly not started**; everything above is verified against toy/mocked evidence, not MACER's
> real segments.
>
> **Reordering decision, 2026-08-07: benchmarking (Phase 0) and MACER-parity shadow-running
> (Phase 5) are deferred to the end, in favor of building P3/P7 next.** MACER may never adopt this
> chassis — that isn't the point. The primitives (P1/P2/P4/P6/P8, now P3/P7) generalize regardless
> of whether MACER specifically ends up calling them; other japes consumers benefit from them
> existing as SDK primitives independent of MACER-parity validation. Benchmarking and diff-based
> validation happen once, at the end, against whatever's been built by then — not gating every
> phase. §7 below is updated to reflect the new order (P3/P7 next, Phase 0/5 last).
>
> **Phase 6 (P3/P7) shipped 2026-08-07,** generalized rather than ported (both were designed to
> reuse existing SDK mechanisms instead of MACER's own domain-specific joins):
>
> **P7 split in two.** Applicability gating (the cheap half -- "filter inapplicable, zero LLM
> calls") turned out to be a real gap in `run_segment` itself, not a future planner feature: it
> didn't honor `Rule.applicability` at all, unlike `DefaultPolicyExpert.check_compliance`. Fixed
> directly in `pipeline.run_segment` (a new `_apply_applicability_gate`, run before the
> DETERMINISTIC/LIVE partition, for both partitions alike) -- an inapplicable rule now short-
> circuits to a real `RuleOutcome(verdict=NOT_APPLICABLE)` before ever reaching its condition,
> deterministic or LIVE. The genuinely pack-specific half -- case-profile-driven dynamic
> regrouping -- shipped as `agents/adjudication/planner.py`'s `SegmentPlanner` Protocol +
> `plan_or_fallback()`: the SDK owns only the fail-closed discipline (any planner exception or
> empty plan falls back to the static segment list, logged, never takes the run down); the case-
> profile logic itself is pack-side, deliberately not built here.
>
> **P3 generalized, not the document-classification-triple join.** `agents/adjudication/impact.py`
> keys impact off `ConditionEvaluator.evidence_contract()` (P8, already existed) instead of
> MACER's `reverse_document_mapping.json` -- "did this rule's applicability/condition read a field
> that changed" rather than a document-type lookup table, so it's reusable by any pack rather than
> tied to one mapping file's shape. A rule declaring no fields at all fails open (always re-
> checked), mirroring MACER's own "unknown document type → all sections" convention. Shipped
> `impacted_rules()`, `merge_with_carry_forward()`, and a `RunMode` enum +
> `resolve_run_mode()` matching MACER's own upgrade/downgrade rules (`INITIAL`+prior-run→
> `FORCED_FULL`, `INCREMENTAL`+no-prior-run→`INITIAL`) plus the doc's proposed `NO_OP` fourth mode
> for explicitly-empty impact.
>
> Both wired into `AdjudicationAgent.adjudicate` as optional keyword params (`planner`,
> `changed_fields`, `prior_outcomes`) -- omitting all three reproduces Phase 4's original behavior
> exactly (verified: all of Phase 4's original tests pass unchanged). Full japes suite green
> throughout (2513 passed, 3 skipped, no failures). Phase 0 and Phase 5 remain deferred, per the
> reordering decision above -- not started.
>
> **Two corrections landed 2026-08-08, from an independent completeness audit
> (`design_note_mode_chassis_completeness.md`).** First: the shipped chassis defaulted
> `replicas=3` in three places (`spec.py`, `pipeline.py`, `conductor/replication.py`), citing
> MACER's own default -- exactly the inherited-not-measured assumption
> `design_note_p1_p2_sizing.md` warns against (that note measured batched k=3 at **zero variance
> reduction, 3.1x cost**, and concludes "default `replicas=1`, not 3"). All three now default to
> 1; the toy demo pack's YAML followed suit. Second: §4c above describes `evaluator.stochastic` as
> what "selects which `EnsembleCollapse` a rule's kind should even reach" -- it doesn't;
> `partition_rules` routes on `execution` alone, and `stochastic` is read nowhere. Behavior matches
> the plan by coincidence, not by wiring: `execution == LIVE` and `stochastic == True` are
> perfectly correlated across all four registered evaluators today. Left unwired deliberately
> (verified there's no evaluator yet that's LIVE-but-not-`stochastic` to justify the seam) --
> documented instead, on the field itself, per the audit's own reasoning.

---

## 0. The thesis

MACER is not "a mortgage agent." Stripped of mortgage, it is a **bounded-obligation adjudicator**:
given a register of declarative obligations grouped into segments, a policy corpus whose applicable
subset depends on a detected regime, and a case evidence corpus, it produces one cited,
status-bearing finding per obligation — incrementally re-runnable, with human decisions carried
forward. AML alert dispositioning and commercial credit review are the same shape. The mortgage-ness
lives in four data artifacts: the obligation register, the regime detector, the policy bindings, and
the output ontology.

**MACER is already a JAPES client.** It imports `Handler`, `HandlerContext`, `JazzXRuntime`,
`ResponseMessage`, `QueueSettings`, `KnowledgeHubClient`, `resolve_model`, `build_model_settings`,
`strip_session`, `RawJsonSchemaOutput`, and `RetryingModel` from `jazzx_sdk`. So this is not a port.
It is **a two-major-version SDK upgrade (1.9.6 → 2.2.4) plus promotion of MACER's remaining private
machinery into chassis**. That reframing shortens the plan considerably and changes what "risk"
means: the risk is version skew and behaviour drift, not a rewrite.

Proposed name: **`AdjudicationAgent`** (`jazzx_sdk/agents/adjudication/`), third chassis beside
`InteractiveAgent` and `DocumentAgent`. Named for the shape of work, like its siblings — **not**
`ReasonerAgent`, which would claim one cognitive mode for something that spans five, and the wrong
one at that. See §4b; that section supersedes the naming in an earlier draft.

The platform vocabulary does say reasoner at the *deployment* boundary —
`flowable:type="reasoner"`, `serviceAlias=mortgage-reasoner`, juno's
`chore/rename-macer-ui-label-to-reasoner` branch. Keep those: they name the deployed mortgage
service, which is a pack instance, not the chassis.

---

## 1. The actual execution topology

This is the correction that matters most, because it inverts the design.

```
for each SECTION, in parallel                      bounded_gather(concurrency=6)
│                                                  jtbd_runner.py:971
│   ── sequential pre-compute, once per section ──
│      per-JTBD guideline enrichment → guideline_contexts[mnemonic]
│      jtbd_runner.py:340-402   (NOT replicated across the k runs)
│
└── for each REPLICA run_number 1..k, in parallel  bounded_gather(concurrency=3)
    │                                              jtbd_runner.py:448
    │   session = SQLiteSession(sha256(f"{run_id}:{section}:{run_number}")[:64])
    │   jtbd_runner.py:583 — own session, own OpenAI prompt_cache_key
    │
    └── ONE batched agent call: ALL applicable JTBDs of the section in a single prompt
        jtbd_runner.py:586 → verify_all_jtbds()  jtbd_agent.py:1595
        └── many tool turns; document reads amortize across every JTBD in the batch

════════════ global barrier: all sections × all replicas complete ════════════

regroup by (section, sequence, mnemonic)           jtbd_runner.py:1152
└── per-JTBD summarization LLM call, in parallel   bounded_gather(concurrency=20)
    jtbd_runner.py:1612 → SummarizationResult

condition-resolution phase, per JTBD, in parallel, each its OWN session
jtbd_runner.py:1364 — "unlike JTBDs within a section, there is no shared
context benefit"  manual_condition_resolver.py:157-160
```

Concurrency is derived, not configured (`jtbd_runner.py:766-772`):
`section_concurrency = macer_async_concurrency // num_parallel_inferences` = `20 // 3` = **6**.
Ceiling ≈ 18 concurrent verification agents.

**What this refutes.** The widely-repeated claim — including in `design/macer.md:2196` and in my own
first draft — that "JTBDs are sequential within a section over one shared accumulating session" is
**dead code**. The sequential `verify_jtbd()` still exists (`jtbd_agent.py:867`) and is still
exported, but has no caller in `src/`. It was replaced by `verify_all_jtbds`, whose docstring is
explicit (`jtbd_agent.py:1605`):

> "Verify all JTBDs in a section simultaneously in one agent call. **Replaces the one-at-a-time
> `verify_jtbd` loop used inside `_process_single_run`.** … All remaining JTBDs are batched into a
> single prompt so the agent can share document reads across requirements."

**What this means for the design.** The context-sharing unit is **the batched prompt**, not an
accumulating session. Amortization is achieved by putting many obligations in front of one agent
that reads each document once, and the *session* exists only to hold that single call's tool turns,
retries, and continuations. Meanwhile the axis of *replication* is the segment: k independent
samples of the whole batch, deliberately un-shared (distinct sessions, distinct cache keys). That is
a materially different primitive from the one I proposed on the strength of the stale doc.

---

## 2. MACER's real context-engineering stack

Six mechanisms, in rough order of value. Two of these I had no idea existed.

### 2.1 Precomputed grounding with a browsing gate — the crown jewel

`guideline_enrichment.py` + `guideline_snippet_extractor.py` + `design/guideline_caching.md`.
Per obligation, *before* any verification call:

1. **Parse** the policy corpus into `GuidelineSnippet(source_file, investor, heading, heading_level,
   content[:3000], page_ref, section_code)` — `#`/`##`/`###` blocks, bodies under 50 chars dropped,
   `###` inheriting the nearest `##` section code (`guideline_snippet_extractor.py:211`).
2. **Prefilter** by keyword overlap — heading+filename weighted ×2, first 500 body chars ×1, `+1.5`
   for `heading_level <= 2`, capped at 300 candidates (`guideline_enrichment.py:219-264`).
3. **Select** via a cheap `guideline_selector` agent shown **headings only**, returning ≤3 indices
   (`:267-346`). Any error → `[]` → fall back to browsing.
4. **Inject** as `## Pre-identified Relevant Guideline Sections` with an explicit "SKIP the CHECK
   GUIDELINES step" instruction (`:574-607`), threaded into the batched prompt at
   `jtbd_agent.py:1562`.
5. **Gate**: when *every* applicable obligation in the batch has a block,
   `set_block_guidelines_browsing(True)` (`jtbd_agent.py:1714`) makes `list_documents` /
   `search_documents` on `/guidelines` return a refusal until a `read_document` on `/guidelines`
   sets `_guidelines_read` (`tools/documents.py:130-141, 393-404`).
6. **Cache** in Redis, two tiers, keyed by a **content fingerprint** over the investor's snippet
   catalog so a corpus change invalidates automatically (`:359-394`, TTL 7 days).

This is the highest-leverage pattern in the codebase and it is completely absent from every
secondary doc. It is also the one thing here that generalizes with zero domain coupling: *precompute
per-item retrieval, inject it, and then close the door on the agent redundantly re-retrieving.* The
gate is what makes it a context-engineering mechanism rather than just a RAG step — without it the
agent browses anyway and you pay twice.

### 2.2 Tool-output compression with lossless recovery

`compression/headroom_store.py` — wraps the `headroom-ai` `SearchCompressor` (in-process, CPU-only)
around `search_documents` grep output, keeps the **full original** in a `ContextVar`-scoped dict,
and appends `[headroom: showing N of M matches; full results via read_reference("<key>")]`. The
`read_reference` tool (`tools/documents.py:327`) recovers it. Activated once per agent run via
`headroom_store_scope()` (`agent_utils.py:146`); suppressed via `without_compression()` for
determinism-sensitive agents (orchestrator, extraction). If compression yields no cache key it
returns the **raw** original — it never hands back unrecoverable truncation
(`headroom_store.py:172-176`).

This is the direct ancestor of japes `tools/tool_compression.py` (`ReferenceStore`,
`PreviewCompressor`) — lineage confirmed. The japes version is the generalization; MACER's adds the
footer-preservation trick for MLflow span truncation (`hooks.py:944-955`).

### 2.3 Session stripping — already in japes

`strip_session` is a **thin delegating wrapper** (`agent_utils.py:346`) over
`jazzx_sdk.agents.run_kit.strip_session`. The rule I claimed is correct: segment on `role=="user"`,
turn boundary on `type=="reasoning"`, keep the user item plus `turns[-1]`. But note it is called
**only** from the dead `verify_jtbd` path (`jtbd_agent.py:1024`) — the live batched path never calls
it. This gap is already closed in the SDK; nothing to build.

### 2.4 Input filter — reasoning-group eviction, and the doc lies about it

`input_filter.py`, wired as `RunConfig(call_model_input_filter=...)` so it runs before **every** LLM
call. Trigger is bytes of serialized JSON, not tokens:
`len(json.dumps(items).encode()) > max_size_kb * 1024`. Algorithm: classify items into groups (a
`reasoning` item opens a group; `function_call`/`function_call_output` extend it; `user` and
`message` items are never dropped and close the group), then **drop whole groups oldest-first**.

Two corrections. `MACER_MAX_SESSION_SIZE_KB` **defaults to 0 = disabled** (`settings.py:209`);
production sets 750 via `Dockerfile:76`. And `design/macer.md:2268-2285` describes "trim boundary
detection" with a helper `_is_valid_trim_boundary(items, index)` — **that function does not exist**.
I repeated that fiction in my first draft. The real mechanism is group eviction.

### 2.5 Prompt caching — two independent schemes

- **OpenAI**: `prompt_cache_key = session.session_id = sha256(f"{run_id}:{section}:{run_number}")[:64]`,
  resolved once and held constant across the whole retry/continuation loop
  (`agent_utils.py:100-117`) so retries stay on one backend machine. Per-*replica* granularity is
  deliberate — parallel replicas are meant to scatter.
- **Anthropic**: up to 4 `cache_control` breakpoints, **on messages only, never on tool
  definitions** (`models/anthropic.py:54-79`): last message, before the last user, before the
  second-to-last user, and the last system message. It's a `set`, so it can collapse to fewer.
  Injected by monkeypatching `litellm.acompletion` for the duration of the call.

Correction: `macer.models.anthropic.AnthropicModel` is **dead at runtime** — nothing constructs it.
`get_model()` delegates to `jazzx_sdk.agents.resolve_model`, which builds japes's own byte-equivalent
copy. Another gap already closed.

### 2.6 Read caps that force paging

`read_document` returns an **error**, not a truncation, above 10 KB, with `start_line`/`end_line`
paging (`tools/documents.py:275`). Small, and a good pattern: make the budget a hard failure the
agent must route around, not a silent degradation it can't see.

---

## 3. Concept map: MACER → JAPES v2.2.4

✅ exists · 🟡 seam exists, strategy to write · ❌ no primitive · ✔︎ already consumed by MACER today

| Capability | MACER | JAPES v2.2.4 | Fit |
|---|---|---|---|
| Queue job lifecycle | `japes/main.py`, `JazzXRuntime` | `JazzXRuntime.run_once()`, `serve()`, `job_id_for()` | ✔︎ |
| Model resolution / settings | delegates | `resolve_model`, `build_model_settings`, `RetryingModel` | ✔︎ |
| Session stripping | delegates | `run_kit.strip_session` | ✔︎ |
| KH access | `KnowledgeHubClient` | `fabric.entities` / `.docs` / `.collections` (v2 supersedes the raw client) | 🟡 upgrade |
| Structured output | `RawJsonSchemaOutput` | same + `output_schema=` on `AgentExecutionService.run` | ✔︎ |
| Tool-output compression | `compression/headroom_store.py` | `tools/tool_compression.py` — `ReferenceStore`, `PreviewCompressor` | ✅ (japes is the generalization) |
| Anthropic cache breakpoints | dead local copy | `agents/anthropic_model.py` (live) | ✅ |
| OpenAI cache key | `utils/cache_key.py` | `build_prompt_cache_key(*parts, max_len=64)` | ✅ |
| Doc classification / extraction | `classify.py`, `agents/mortgage.py` | **`DocumentAgent`** — `process_dir(incremental=True)`, `Manifest`, `SourceCoordinate`+`Confidence`, `Refusal` below floor | ✅ (better) |
| Per-item adjudication | `verify_all_jtbds` | `AgentExecutionService.run(output_schema=)`, `function_tool` | ✅ |
| Staging / branching / HITL | hand-rolled | `ConductorPipeline` + `ConductorEngine`, `step_guards`, `SuspendRun` → `resume_durable` | ✅ (better) |
| Observability | MLflow direct + `TraceHooks` | `RunTracer`/`MlflowTracer`, `STAGE_TAG_KEY`, `mlflow_bridge.spans_to_canonical_trace` | ✅ (better) |
| Per-turn config override | `japes/config_schema.py` | `InvocationConfig.from_payload().apply_to(spec)` | ✅ |
| Outer parallelism | `bounded_gather` | `conductor.fanout.fan_out(concurrency=, degrade=, tracer=)` | ✅ |
| Session per replica | `SQLiteSession` | `AgentExecutionService.bind_conversation(store, session_id, compaction=)` + `fabric.conversation` | ✅ (better — survives eviction) |
| **Segment × replica × batch topology** | `jtbd_runner.py` | — | ❌ **P1** |
| **Ensemble collapse** | `summarization_agent.py` | — | ❌ **P2** |
| **Precomputed grounding + browse gate** | `guideline_enrichment.py` | — | ❌ **P6** |
| **Dynamic segmentation / applicability** | `orchestrator_agent.py` | — | ❌ **P7** |
| **Impact resolution (incremental)** | `rerun_orchestrator.py` | `Manifest` is file-level only | ❌ **P3** |
| **Evidence workspace / mounts + gates** | `tools/documents.py` | `dir_tools`, `read_local_file`, `authority.admit_hop` | 🟡 **P4** |
| Reasoning-group input filter | `input_filter.py` | `CompactionPolicy` + `register_compaction_strategy` | ✅ **P5** (shipped, see update note) |
| Obligation register | `models/jtbd_ontology.py` | canonical `Policy{rules: list[Rule]}` — see companion doc `policy-ir-abstraction.md` | 🟡 |
| Rule-evaluator dispatch | n/a (English only) | `Rule.condition` is a closed 2-way union wired with `isinstance` | ❌ **P8** |
| Carry-forward / admissibility | 3 resolver modules | `SuspensionStore`, `ConversationStore.supersede`, `WriteOutcome` | 🟡 |

---

## 4. The primitives to build

### P1 — `run_replicated_segments`

Replaces my earlier `run_segments`, which solved a problem MACER no longer has.

```python
async def run_replicated_segments(
    segments: Sequence[Segment[I]],
    process: Callable[[Segment[I], Replica], Awaitable[Sequence[R]]],
    *,
    replicas: int = 3,
    precompute: Callable[[Segment[I]], Awaitable[P]] | None = None,  # once per segment
    session_for: Callable[[Segment[I], Replica], ConversationBinding],
    key_of: Callable[[R], ItemKey],                                  # regroup key
    segment_concurrency: int | None = None,   # default: total // replicas
    total_concurrency: int = 20,
    degrade: bool = True,
    tracer: RunTracer | None = None,
    on_item: StepObserver | None = None,
) -> ReplicatedRun[R]:   # .grouped: dict[ItemKey, list[R]]; .failed_replicas: dict
```

Built over `fan_out` at both levels so cancellation/drain semantics and per-item spans are inherited.
Four things the signature encodes that MACER learned the hard way:

- **`precompute` runs once per segment, outside the replica loop.** MACER does this for guideline
  enrichment (`jtbd_runner.py:340-402`) and it is the difference between paying for retrieval once
  and paying k times.
- **`session_for` is a callable of (segment, replica).** MACER needs *distinct* sessions per replica
  (so cache keys scatter) but the condition-resolution phase needs one session per *item* — and it
  says why: "unlike JTBDs within a section, there is no shared context benefit." A callable covers
  both without a second primitive.
- **`key_of` makes regrouping explicit.** MACER's key is `(section, sequence, mnemonic)` and its
  within-batch alignment is *positional* `zip` (`jtbd_runner.py:595`) with a NOT_APPLICABLE fallback
  when the model returns fewer results than asked (`jtbd_agent.py:1760-1777`). Positional alignment
  over an LLM-generated list is fragile; the chassis should require the model to echo the item key
  and validate, not zip.
- **`failed_replicas` is a first-class return.** See P2.

### P2 — `EnsembleCollapse`

MACER's collapse is one `summarize_jtbd_results` LLM call per item over the k samples
(`summarization_agent.py:355`). Voting is **prompt-driven, not code-counted**; the tie-break
priority `CONDITIONAL > FAIL > NOT_APPLICABLE > INFO > PASS` lives in the system prompt
(`summarization_agent.py:34-39`). Only loan metrics get deterministic reconciliation afterwards
(`loan_metrics_utils.py:657`).

The real output model (`models/jtbd.py:417-489`):

```python
class SummarizationResult(BaseModel):
    majority_status: Literal["PASS","FAIL","CONDITIONAL","NOT_APPLICABLE","INFO"]
    majority_report: str
    minority_report: str
    observations: list[str] = []
    facts: list[str] = []
    policy_ref: list[str] = []
    loan_metrics: list[LoanMetricValue] = []
    conditions: list[ConditionInfo] = []

    @model_validator(mode="after")
    def validate_conditions_match_status(self): ...   # CONDITIONAL ⟺ ≥1 condition
```

There is **no** `determination` and no `minority_status` field. I invented both in the first draft,
having taken them from juno's `macer-analyzer` skill, which regexes for them — apparently against an
older shape. Downstream, `status = majority_status` and
`description = majority_report + "\n\nALTERNATIVE VIEW:\n" + minority_report`
(`summarization_utils.py:167-193`).

**A real bug to fix in the chassis, not port.** When a replica exhausts retries, the runner
synthesizes one `status="ERROR"` row per item for that replica (`jtbd_runner.py:456-485`). Those
rows flow into `results_by_jtbd` and are handed to the summarization agent as if they were votes.
`ERROR` is not in the `Literal` and is not mentioned in the prompt, so **a failed replica silently
dilutes the vote**. Token accounting already excludes failed runs (`:490-508`) — the vote should
too. Hence `failed_replicas` in P1's return type, and:

```python
class EnsembleCollapse(Protocol):
    async def collapse(self, votes: Sequence[R], *, item: Item, excluded: Sequence[Failure]) -> Ensembled[R]: ...

class LlmFold(EnsembleCollapse):        # MACER's behaviour, minus the ERROR dilution
class DeterministicVote(EnsembleCollapse):   # priority-ordered status, no LLM call
class AnyEscalate(EnsembleCollapse):    # asymmetric-risk domains — see §6
```

Also worth surfacing: `k` × items is where the money goes. Bind it to `llm/cost_tracker.py` budgets
so it's a governed axis, not a config constant.

### P3 — `ImpactResolver`

My first draft guessed this joins on evidence types declared on the obligation. **It does not.**
`compute_impacted_sections` (`rerun_orchestrator.py:288-408`) joins on the **document
classification triple** — `lookup_sections_for_document(document_type, subtype, subsubtype)` against
`reverse_document_mapping.json`, with the `"null"` key deliberately **failing open to all sections**
for unknown types (`data/__init__.py:166-171`). Change detection is a timestamp comparison against
the prior FindingSet's `last_run_at`. LOS entities get the same treatment via
`reverse_los_entity_mapping.json`. The obligation register is not consulted here at all; JTBD-side
filtering happens later via `filter_sections_to_available` (`japes/main.py:1511`).

The preferred path is explicit rather than temporal:
`compute_impacted_sections_for_uploaded_docs` (`:508-604`) matches on
`entity_id ∈ uploaded_document_ids`. The chassis should make that the *only* path and treat
timestamps as a fallback — "what changed" should be told to the system, not inferred.

Run modes are `Literal["INITIAL","INCREMENTAL","FORCED_FULL"]` with a two-step decision: payload
flags first, then adjusted on FindingSet existence — INITIAL + existing set is **upgraded** to
FORCED_FULL; INCREMENTAL with no set is **downgraded** to INITIAL (`:718-750`). Add `NO_OP` as a
fourth: MACER expresses empty-impact as an early return (`japes/main.py:1521`) and no-evidence as an
exception (`NoDocumentsOrEntitiesError`); both should be run modes gated declaratively via
`ConductorEngine.step_guards`, so downstream stages record `skipped(note="guard")` instead of the
pipeline unwinding.

### P4 — `EvidenceWorkspace`

Named mounts with access classes, plus the two gate mechanisms MACER proved out: the **browse block**
(P6) and the **hard read cap that errors rather than truncates**. Wire admission to the authority
cascade that already exists — `admit_hop(f"mount:{name}")`, then
`permission_scope.narrow([...])` inside a segment, mirroring
`InteractiveAgent._build_parent_tools`.

### P5 — Two compaction strategies

`segment_tail` is **already in japes** (`run_kit.strip_session`) — register it as a named strategy
and delete MACER's wrapper. What is *not* in japes is the reasoning-group evictor from
`input_filter.py`; add it as `reasoning_group_evict`, and make it token-triggered rather than
byte-triggered while porting. Both go through `register_compaction_strategy`, alongside the existing
`"summarize"`, `"drop"`, `"responses"`.

### P6 — `PrecomputedGrounding`

§2.1, generalized. Four pluggable parts and one non-negotiable:

```python
class PrecomputedGrounding:
    extractor: SnippetExtractor       # corpus → snippets w/ heading + page_ref + section_code
    prefilter: CandidateFilter        # cheap lexical narrowing, capped
    selector: SnippetSelector         # LLM over HEADINGS ONLY, top-k
    cache: GroundingCache             # fingerprint-keyed; corpus change ⇒ invalidate
    gate: BrowseGate                  # ← the non-negotiable part
```

The gate is what makes this worth a primitive. Precomputed retrieval without it just adds tokens;
the agent browses anyway. MACER's escape hatch is the right shape too — block *listing and
searching*, allow a direct `read_document`, so the agent can still follow a citation it was given.

### P7 — `SegmentPlanner`

`orchestrator_agent.py` (documented in `design/orchestrator.md`, default-off via
`macer_use_orchestrator=False`, per-run gated by payload `use_orchestrator`). It reads a few key
documents, builds a case profile, then **regroups obligations by domain instead of by their static
section** and **filters out inapplicable ones** — which become synthetic NOT_APPLICABLE rows with no
LLM call at all (`jtbd_runner.py:900-935`). It runs `without_compression()` for determinism and
guards against hallucinated mnemonics via `set_valid_jtbd_mnemonics`. Best-effort: any failure or
empty plan silently falls back to static sections.

This deserves to be a chassis seam because the segment axis is exactly what a new domain will want
to control, and because "skip the obligation entirely" is the cheapest possible optimization —
strictly better than adjudicating it to NOT_APPLICABLE with k LLM calls. Keep the fallback-to-static
discipline; a planner that can fail closed is a planner that takes the whole run down.

---

### P8 — `ConditionEvaluator` registry (pluggable policy IR)

MACER's English JTBD should be **one registered rule kind, not the substrate**. japes already has
`Rule.condition: Expression | DslExpression` with `citations` → `Policy.source_refs`, but the union
is closed and dispatch is an `isinstance` branch in `DefaultPolicyExpert.check_compliance`. Opening
it lets `adjudicate` partition by execution kind — deterministic rules skip the LLM, skip batching,
and force `k=1` — which is where the cost actually goes.

Full design in the companion document **`policy-ir-abstraction.md`**. Two consequences for this
document: P2's `EnsembleCollapse` keys off `evaluator.stochastic`, and P6 grounding applies only to
the LIVE partition.

---

## 4b. It is not a Reasoner — it is a Conductor over five modes

`ReasonerAgent` was the wrong name and I'm retiring it. In japes's taxonomy a **mode** is a
single-step cognitive contract typed by canonical object I/O, not an agent: `ModeContract` is
`{mode_name, category, kind, canonical_produces, canonical_consumes, derived_object,
autonomy_default}`, and `BaseMode`'s entire abstract surface is `mode_name` plus
`run() -> ModeResult`. `Reasoner` specifically means `Evidence + Trace → Decision`, run **once on
converged state** — `ReasonerMode` docstring: *"analyzes converged case state and recommends Close
or Escalate."*

Map the pipeline stages onto the catalog and the chassis lands almost entirely outside THINK:

| Stage | Mode | Contract | Category |
|---|---|---|---|
| `extract` | **Verifier** | `Evidence → Attestation` | TRUST |
| `regime` | (deterministic routing) | — | — |
| `plan` | **Optimizer** | *"selecting which evidence to retrieve … how to allocate resources"* | EXECUTE |
| `adjudicate` — DETERMINISTIC partition | **Verifier** / **Governor** | rule vs. evidence, no LLM | TRUST |
| `adjudicate` — LIVE partition | **Reasoner** | `Evidence + Trace → Decision` | THINK |
| `reconcile` | **Governor** | *"policy enforcement and constraint checking"*; admissibility gates, human overrides | TRUST |
| `emit` | **Narrator** | `Decision + Evidence →` narrative (MACER LLM-writes finding titles/descriptions) | INTERACT |
| *the whole* | **Conductor** | `kind=ORCHESTRATOR`, `canonical_produces=None  # Orchestrator, not a producer` | EXECUTE |

Five modes across four categories, and only *one* of them is Reasoner. `extract` is Verifier by
construction — `DocumentAgent` already emits `FieldAttestation` and `Confidence` and refuses below
the admission floor, which is `Evidence → Attestation` exactly.

**The name gets more wrong as the design succeeds.** Every rule that P8 moves from
`natural_language` to a deterministic kind moves work out of Reasoner and into Verifier/Governor. A
well-formalized pack is *mostly* TRUST. Naming the chassis after the mode we're trying to use less
of would be a strange commitment.

It also breaks the sibling pattern. `DocumentAgent` and `InteractiveAgent` are named for the
**shape of work**, not a cognitive mode — "document" and "interactive" aren't in the catalog.
Borrowing mode vocabulary for the third chassis implies a correspondence the other two don't claim.

**Rename: `AdjudicationAgent`, in `jazzx_sdk/agents/adjudication/`**, with
`build_adjudication_pipeline()` alongside it — mirroring `agents/document/`'s split of `agent.py`
(ergonomic facade) and `pipeline.py` (the `ConductorPipeline` a pack can rewire). Adjudication is
the shape of work: apply rules to facts, reach a verdict. It claims no mode, and it is already what
the central stage is called.

### Where mode *does* matter: the Trace

Mode is **not load-bearing at runtime today**. Authority keys on
`decision_class × action_class × actor_class` and never sees mode; `MODE_REGISTRY` has no runtime
reader; `ModeContract.autonomy_default` is set on all 13 contracts and read nowhere; prompt
resolution keys on the mode *string*, and an uncatalogued name resolves fine. Mode buys a prompt
filename and a `TraceStep` enum value.

The `TraceStep` value is the point — it's the audit artifact. And there is a concrete trap:

```python
DEFAULT_SPAN_MODE_MAP = {"LLM": REASONER, "CHAT_MODEL": REASONER,
                         "TOOL": INVESTIGATOR, "RETRIEVER": INVESTIGATOR, "AGENT": INVESTIGATOR,
                         "CHAIN": CONDUCTOR, "WORKFLOW": CONDUCTOR}
```

Thirteen modes collapsed onto three, keyed on OTel span type. **If the chassis doesn't supply a
`mode_map`, every LLM call in its trace is labelled `reasoner`** — including the Governor gate and
the Narrator pass — and the Trace lies about what happened. `spans_to_canonical_trace(..., mode_map=)`
is documented as "the domain seam"; here, supplying it is mandatory rather than optional. Tag each
pipeline step with its mode and derive the map from the table above.

### The opportunity: make mode load-bearing for autonomy

Two disconnected autonomy encodings exist. `ModeContract.autonomy_default: int` (0–4) is dead data.
`AuthorityCell.autonomy_launch: AutonomyLevel` (`L0_ASSIST … L4_SELF_IMPROVEMENT`) is live and is the
resolver's currency. Nothing converts between them.

The P8 partition is the natural place to connect them, because it is *simultaneously* a cost
boundary and a governance boundary:

- A **DETERMINISTIC** rule check is reproducible from `RuleOutcome.inputs` without an LLM. Verifier
  work; can defensibly launch at a high autonomy rung.
- A **LIVE** judgment on "compensating factors" is Reasoner work, not reproducible; should cap lower
  and route to human review.

That gives a principled basis for per-obligation autonomy instead of one run-level setting, and would
make this chassis the first runtime consumer of mode. The existing guardrail bounds it: a
`CellKind.FINAL` cell *"must be human_only or launch at L0"*, so a committing adjudication can't be
autonomous regardless. Candidate cells can, and that's where the partition earns its keep.

Two things worth flagging to whoever owns the modes framework: `experts/README.md` still documents
"The 5 Platform Experts" against a live `EXPERT_REGISTRY` of **3** (governance, evidence, and
investigation moved to the Skills layer at IIF v1.5; `registry.py` now hard-errors on them). And the
13-mode list is duplicated verbatim in `modes/catalog.py` and `fabric/canonical/trace.py` with no
import linking them — they can drift silently.

---

## 4c. Phase 4, concretely (added 2026-08-07, now that P1/P2/P5/P6/P8 are no longer speculative)

The original Phase 4 entry in §7 was necessarily vague — "chassis (3-4 weeks) —
`AdjudicationAgentSpec`, `AdjudicationAgent`, P4 workspace, `build_adjudication_pipeline`" — written
before any primitive existed to wire. Now that P1/P2/P5/P6/P8 are real, confirmed, drift-free code,
Phase 4's job is specifically **wiring five already-built things and one not-yet-built thing**
together into one pipeline, not building six things from scratch. Concretely, per obligation-batch:

1. **Precompute** (P6, `PrecomputedGrounding`) — once per segment, before any replica runs. Already
   shippable standalone; the chassis just needs to call it as the pipeline's precompute step and
   pass its output into each replica's prompt, the same way `run_replicated_segments`'
   `precompute` parameter is already shaped to receive it (§4/P1 — `precompute` runs once per
   segment, outside the replica loop; this is not new wiring work on P1's side, just a caller).
2. **Partition by evaluator kind** (P8, `ConditionEvaluator.execution`) — split the segment's
   obligations into DETERMINISTIC (skip the LLM, skip replication, `k=1`, straight to
   `DefaultPolicyExpert.check_compliance`) and LIVE (needs `ReasoningAgent`). This is the one
   genuinely new piece of glue: nothing today reads `execution` to *route*, only to *evaluate*
   once already inside `check_compliance`. Small — a filter over `Policy.rules`, no new primitive.
3. **Replicated batch verification** (P1, `run_replicated_segments`) — the LIVE partition only.
   `process: (segment, replica) -> results` is where `ReasoningAgent.run(tools=[...])` actually
   gets called, batched (one call, many obligations, per MACER's `verify_all_jtbds` shape — §1).
   This is the other genuinely new piece: a `process` callable that builds the batched prompt from
   the LIVE obligations + P6's grounding output, and calls `ReasoningAgent.run()`. Everything
   *around* that call (session-per-replica via `session_for`, regrouping via `key_of`,
   `failed_replicas` exclusion) is already P1's job, unchanged.
4. **Collapse** (P2, `EnsembleCollapse`) — per obligation, over its `k` replica results.
   `evaluator.stochastic` (P8) selects which `EnsembleCollapse` a rule's kind should even reach —
   MACER's `AnyEscalate` for asymmetric-risk domains, `DeterministicVote` for a domain that wants no
   LLM in the loop at all (§6's per-pack table). Already shippable as-is; wiring is "call `.collapse()`
   after step 3, keyed by the obligation."
5. **Evidence workspace** (P4, still unbuilt) — the one primitive in this list that doesn't exist
   yet. Named mounts + access classes, plus the two gate mechanisms MACER proved out (browse block —
   already generalized as P6's `BrowseGate`; hard read cap that errors rather than truncates —
   not yet a primitive, currently just a pattern in `tools/documents.py`-equivalent code). Smaller
   than it looks: `admit_hop(f"mount:{name}")` + `permission_scope.narrow([...])` already exist in
   `authority.context`; P4 is mostly the *convention* of using them per-segment, not new mechanism.
6. **Reconcile + emit** (Governor/Narrator modes, unchanged) — these two modes' existing
   single-shot `ReasoningAgent.run()` calls slot in after step 4 without modification; they were
   never the missing piece.

**What this means for sizing**: steps 1, 4, and 6 are pure wiring (hours, not weeks) against
primitives that already work. Step 5 (P4) is genuinely unbuilt but small relative to the others.
Steps 2 and 3 are the real work — a router over `Policy.rules` by evaluator kind, and one
`process` callable that shapes the batched-prompt-plus-grounding call. That's a materially smaller
Phase 4 than "3-4 weeks" implied when nothing existed to wire; most of the estimate should now go to
`AdjudicationAgentSpec`/`build_adjudication_pipeline` as the actual new surface area (the
`ConductorPipeline` a pack rewires — mirroring `agents/document/`'s `agent.py`/`pipeline.py` split,
per §7's original framing) plus the `examples/adjudication_demo/` deliverable (still absent) and the
mode-tagging discipline in §4b (supplying `mode_map` to `spans_to_canonical_trace` — not yet done
because nothing calls it in this shape yet).

**Direct answer to "can ReasoningAgent + the five modes do MACER's actual job today":** no —
each mode is a single-shot wrapper (`jazzx_sdk/modes/operational/{reasoner,narrator,governor,
investigator,verifier}.py`, one `ReasoningAgent(...)` construction, one `.run()` call, zero
references to `run_replicated_segments`/`EnsembleCollapse`/`PrecomputedGrounding`/`BrowseGate`
anywhere in `jazzx_sdk/modes/`), so there is no segment×replica×batch topology, no grounding
injection, and no ensemble collapse in the current mode layer at all. The primitives that would
close that gap already exist and are verified drift-free against this doc; what's missing is Phase
4 itself — the pipeline that calls them in the right order — which has not been started.

---

## 5. What not to port

1. **ERROR replicas diluting the ensemble vote** (`jtbd_runner.py:456-485` → summarization). §4/P2.
2. **Per-field LLM conversion with silent defaults.** `findings_converter.py` (2,573 lines) logs
   `"conversion failed, using default"` as a routine WARN — degraded values written into a
   compliance artifact. Structured output direct to the canonical model, and a typed `Refusal` on
   failure, per japes's XF-1 discipline.
3. **Swallowed upload errors.** `Finding upload failed with exception` is counted while the run
   reports FINISHED. Use `WriteOutcome` and report `status="partial"`. (Caveat:
   `ResponseMessage.status` is an unconstrained `str` today — the three values are a docstring
   convention. Tighten to a `Literal` as part of this work.)
4. **Positional `zip` alignment** of model output to input items, with a silent NOT_APPLICABLE
   backfill when counts mismatch (`jtbd_agent.py:1760-1777`). Require the key in the output;
   validate.
5. **Local `SQLiteSession`.** Use `fabric.conversation` — inspectable, and survives the container
   eviction that `JAPES_VISIBILITY_TIMEOUT=2700` makes a live failure mode.
6. **Dead code presented as architecture.** `verify_jtbd`, `models/anthropic.py`, and the
   `strip_session` wrapper are all superseded but still exported, and `design/macer.md` documents
   the dead versions. Delete on the way through, or the next reader repeats my mistake.

Structurally: MACER is Tier-2 only. Build the chassis as **Tier 1 — a library with no runtime
opinion** (*"JAPES provides, the client owns"*), so one `AdjudicationAgent` serves a queue job, an
`/invoke` surface with SSE stage progress, and a CLI. `serve()` + `JAPES_RUN_MODE` already does the
mode selection. Stage-level streaming via `on_step` is the single most visible upgrade: MACER today
is an opaque 45-minute batch because it has no stage model.

---

## 6. Three packs on one chassis

| | **Mortgage** (MACER) | **AML** | **Commercial Lending** |
|---|---|---|---|
| Regime | FNMA / FMAC / FHA / VA | jurisdiction × program (BSA/AML, AMLD6, MAS 626) | facility type: C&I, CRE, ABL, SBA 7(a) |
| Segments | Appraisal, Income, Credit, Assets, Identity, Property | Customer Risk, Transaction Patterns, Sanctions/PEP, Source of Funds | Financials, Collateral, Covenants, Guarantors, Exceptions |
| Obligations | JTBDs (`INC-HIS`, `APR-CLT`) | alert-disposition rubric + CDD/EDD | credit-memo assertions + covenant tests |
| Policy mount | agency selling guides, FHFA limits | AML program, FATF/FinCEN, sanctions lists | credit policy, concentration limits |
| Status enum | PASS/FAIL/CONDITIONAL/N_A/INFO | CLOSE/ESCALATE/SAR_REFER/RFI/N_A | SATISFIED/EXCEPTION/WAIVED/RFI/N_A |
| Collapse | `LlmFold`, k=3 | **`AnyEscalate`** — asymmetric cost of a false negative | `DeterministicVote` + minority to committee |
| HITL | underwriter condition review | investigator disposition sign-off | credit officer exception approval |

**AML is the stress test.** It breaks the LLM-fold default on regulatory grounds, and its segments
are *not* evidence-disjoint the way mortgage's are — transaction patterns and source of funds read
the same data. Mortgage gets away with a lot because its sections partition cleanly; AML won't. That
is precisely why P1's `session_for` and P7's planner must be seams rather than fixed behaviour.

**Commercial lending stresses numerics** — DSCR, LTV, fixed-charge coverage, concentration ratios.
`tools/ratio_evaluator.py` and `tools/financial.py` already exist in japes; MACER's sandboxed
`python_repl` (`tools/repl.py`) should become a `scratch`-mount capability rather than be
reimplemented.

---

## 7. Build sequence

**Reordered 2026-08-07 (see the update note near the top): phase numbers below are kept stable
because code already cross-references them (e.g. `agent.py`'s docstring points at "Phase 6" for
P3's carry-forward) — but actual build order is now 1→2→3→4→**6**→5→0→7. Phase 6 (P3/P7) is next;
Phase 0 (benchmarking) and Phase 5 (MACER shadow-run diff) both move to the end, run once against
whatever's been built by then, not gating anything in between.**

**Phase 0 — measure the batching claim (1 week). DEFERRED TO END.** The batched-prompt design rests
on "share document reads across requirements" (`jtbd_agent.py:1611`). That benefit is **asserted in
a docstring and never measured** — no benchmark exists anywhere in the repo. It's also now testable
cheaply, because the dead `verify_jtbd` path is still there: run both, compare tokens, cost, wall
clock, and finding agreement. Also measure the k=3 ensemble's actual contribution — if replicas
agree ~always, k=3 is a 3× bill for variance reduction nobody needs. These two numbers would have
sized P1/P2 had this run first; run retrospectively instead, against whatever's shipped by then.

**Phase 1 — SDK upgrade, 1.9.6 → 2.2.4 (2–3 weeks). DONE.** Unglamorous and on the critical path for
everything else. Two majors of drift across `resolve_model`, `strip_session`, `KnowledgeHubClient` →
`fabric`, plus MACER's own `pydantic` deprecation suppressions. Delete the three dead modules while
you're in there. Nothing below is safe to start until this lands.

**Phase 2 — primitives (3–4 weeks). DONE.** P1, P2, P5 (both halves — see the 2026-08-07 update
note near the top). Self-contained, unit-testable against existing patterns
(`tests/test_fanout.py`, `test_compaction.py`, `test_conductor_engine.py`), useful independently of
the chassis. Verified zero API drift as of 2026-08-07.

**Phase 3 — P6 `PrecomputedGrounding` (2–3 weeks). DONE.** Broken out from the chassis because it
is the highest-value transferable asset and the one most likely to be wanted by a team that never
adopts the rest. Shipped standalone (`jazzx_sdk/agents/reasoning/grounding.py`).

**Phase 4 — chassis (3–4 weeks). DONE 2026-08-07.** `AdjudicationAgentSpec`, `AdjudicationAgent`,
P4 `EvidenceWorkspace`, `run_segment` (this doc's `build_adjudication_pipeline`) all shipped in
`jazzx_sdk/agents/adjudication/` — see the 2026-08-07 "Phase 4 shipped" update note near the top for
the full breakdown. Mode-tagging landed as a new `name_patterns` seam on `mlflow_bridge`
(`spans_to_canonical_trace`), not just a `mode_map` value — span_type alone can't tell an adjudicate
call from an emit call apart (both are plain `LLM` spans). `examples/adjudication_demo/` ships, the
way `examples/loan_assistant/` demonstrates `InteractiveAgent`. Extraction was not wired to
`DocumentAgent` in this pass — no caller needed it yet; still a fair follow-up if/when Phase 5 turns
up a real extraction step this chassis owns.

**Phase 5 — mortgage pack. DEFERRED TO END (was next; moved after Phase 6).** Obligation register,
regime detector, ontology bindings become pack data. Shadow-run against production MACER and diff
**finding-by-finding** — wall-clock and cost are not the acceptance bar; the disagreements are the
output. Run once P3/P7 exist too, not as a gate before them — MACER may never adopt this chassis;
the primitives are worth building for japes's other consumers regardless.

**Phase 6 — P3 impact + carry-forward, P7 planner. DONE 2026-08-07.** No longer "deliberately
last" — see the 2026-08-07 reordering note near the top for the full breakdown. `run_segment` now
honors `Rule.applicability` directly (the gap found this session); `agents/adjudication/
planner.py` (`SegmentPlanner`/`plan_or_fallback`) and `agents/adjudication/impact.py`
(`impacted_rules`/`merge_with_carry_forward`/`RunMode`/`resolve_run_mode`) both shipped, wired into
`AdjudicationAgent.adjudicate` as optional params. Both primitives generalize their MACER
counterpart rather than port it: P3 keys off `evidence_contract()` (P8) instead of MACER's
document-classification-triple join; P7's planner is a fail-closed harness around pack-supplied
case-profile logic, not MACER's `orchestrator_agent.py` itself.

**Phase 7 — AML pack.** First pack authored by someone who didn't write the chassis. The real test.

---

## 8. What changed from the pre-source draft

Kept here because the failure mode is reusable: every one of these came from trusting
`design/macer.md`, which is stale in exactly the places the code moved fastest.

| Claim | Reality |
|---|---|
| "JTBDs sequential within a section over a shared accumulating session" | Dead code. One batched call per (section, replica). `jtbd_agent.py:1595` |
| Ensemble samples per obligation | Replication unit is the **section**; per-item samples are a side effect. `jtbd_runner.py:431` |
| `determination`, `minority_status` fields | Don't exist. `majority_status`/`majority_report`/`minority_report`. `models/jtbd.py:417` |
| Majority computed in code | Prompt-driven; tie-break priority lives in the system prompt. `summarization_agent.py:34` |
| Input filter does "trim boundary detection" | `_is_valid_trim_boundary` doesn't exist. It's reasoning-group eviction. Default **0 = disabled** |
| 4 Anthropic cache breakpoints incl. tools | Messages only, never tools; "up to 4" — it's a `set`. And the module is dead; japes's copy is live |
| Impact joins on obligation-declared evidence types | Joins on document classification triple via reverse-mapping JSON, fail-open on unknown |
| Port MACER onto japes | MACER already **is** a japes client at 1.9.6; this is an upgrade + promotion |
| — | **Missed entirely:** `guideline_enrichment` (P6), `headroom_store`, `orchestrator_agent` (P7) |

Two other corrections worth carrying: `macer_async_concurrency` defaults to **20**, not 10
(`settings.py:235` vs `design/macer.md:2019`); and `MACER_SUMMARIZATION_CONCURRENCY`
(`design/macer.md:2072`) is not a setting — summarization uses `macer_async_concurrency` directly.

## Appendix — inconsistencies in the surrounding docs

- **Framework.** juno's `macer-analyzer/SKILL.md` says MACER "executes **LangGraph** agents." It's
  the OpenAI Agents SDK + LiteLLM. The skill is wrong.
- **Version skew.** japes repo **2.2.4**; MACER pins **1.9.6** (`4b08850`); juno's venv has 1.9.2.
  Package renamed `jazzx_runtime_sdk` → `jazzx_sdk` at 1.4.0.
- **Two meanings of JAPES.** Architecture docs: the Azure-Queue execution service. juno's
  integration spec: the Python client SDK. Same word, different layer.
- **Doc routing.** `jazzx-architecture/SKILL.md` routes "JAPES" to `kernel.md`, which never mentions
  JAPES.
- **Stale scaffolding.** japes `examples/document_analyzer/` still copies `jazzx_runtime_sdk/`. Use
  `examples/loan_assistant/` + `agents/document/pipeline.py`.
- **CI.** `Build-Push-Docker-Image-GHCR.yml` hard-codes an `image_context` enum
  (`root` | `document_analyzer`); the README's matrix is commented out. No root `Dockerfile` exists
  despite the `root` context expecting one.
- **MLflow API split.** juno's `macer-analyzer/scripts/*.py` use the 2.0 `get-trace-artifact`
  endpoint; `macer_tools.py` uses 3.0, and only the latter has the `params.message_trace_id`
  fallback.
