# ReasoningAgent, the cognitive modes, and the adjudication chassis — completeness assessment

Author: Claude (Cowork) for Virendra Mehta · 2026-08-08
Audited against: `japes` 2.3.4 (working tree), `jaci` v0.19.1 `dev` @ `f56baf9`, `macer` (working tree)
Every claim below is grounded in a file read during this session; where something is absent, the
grep that established the absence is named. `japes/docs/plans/` and `jaci/docs/plans/` are symlinks
to a path outside the mounted folders, so the design docs those modules cite (notably
`reasoner-chassis-analysis.md`) could not be read — the assessment is against code and docstrings.

---

## TLDR

The ReasoningAgent migration is complete for the five LLM-driven operational modes and correctly
skipped for the one deterministic mode. It is **not** complete for the EVOLVE category: `EvaluatorMode`
still constructs its own `AsyncOpenAI` client, doesn't inherit `BaseMode`, and returns no
`ModeResult` — so the compounding loop is the one part of the platform with no gateway governance,
no retry discipline, and no token accounting. That is precisely the loop the strategy deck names as a
"double down."

Second, the migration bought only the *floor*. Every one of the eight implemented modes calls
`ReasoningAgent` with no tools, no grounding, and no replication (`has_tools` returns `False` in all
six operational modes; verified). The ceiling the docstring promises is real and well-built, but it
lives outside `ReasoningAgent` in `conductor/replication.py`, `conductor/ensemble.py`, and
`reasoning/grounding.py`, and the only consumer that assembles it is `AdjudicationAgent`.

Third, `jaci` imports neither `ReasoningAgent` nor `AdjudicationAgent` — `grep -rn "adjudicat"`
across the whole jaci repo returns zero hits, not even a comment. The CL spread track, which is the
live commercial-lending work, reaches `ReasoningAgent` only transitively through the mode classes.
So the two newest and strongest primitives in the SDK have no application consumer.

Fourth, and most consequential for the spread use case: `AdjudicationAgent` is an almost exact
structural match for the **validation** half of financial spreading, and for the parts of spreading
that today have no adjudication at all. jaci has 17 validation detectors, a governed
`SpreadPackage`, a `reconcile_packages` multi-pass voter that is *built but never invoked outside
tests*, and a `Confidence` that is a hard-coded `0.98` on every cell. `AdjudicationAgent` +
`run_replicated_segments` + `EnsembleCollapse` is the shape that turns all of that into one governed
run with real per-cell confidence.

---

## 1. How complete is the ReasoningAgent / cognitive-mode implementation

### 1.1 What exists

`jazzx_sdk/agents/reasoning/agent.py` is 147 lines and does one thing well. `ReasoningAgent.run()`
resolves a model through the shared `resolve_model()` — the same function
`AgentExecutionService.openai.build_agent()` uses — and delegates to
`jazzx_sdk/agents/run_kit.py::run_agent()`. It is constructor-injected with an
`AgentExecutionService`, matching how `InteractiveAgent` and `DocumentAgent` already take
`agents=ctx.runtime.agents`. It returns `(final_output, session, TokenUsage)`.

The design note in the docstring is worth repeating because it is the actual justification for the
migration and it is accurate: the old generic tier gave callers "a plain model with no
`RetryingModel`, a hand-rolled retry loop that string-matches the lowered exception text for
`429`/`500`/`rate limit`, and no handling at all for a schema-validation failure or a truncated
response" (`reasoning/agent.py:5-10`). Every mode used to call that. So the migration is a real
robustness upgrade, not a refactor for tidiness.

`jazzx_sdk/modes/catalog.py` declares all 13 Charter modes with category, kind, canonical I/O, and
`autonomy_default`. Eight have live implementations:

| Category | Mode | Implementation | LLM path |
|---|---|---|---|
| THINK | investigator | `modes/operational/investigator.py` | ReasoningAgent (`:123`, call at `:218`) |
| THINK | reasoner | `modes/operational/reasoner.py` | ReasoningAgent (`:100`, call at `:180`) |
| THINK | simulator | — | not implemented |
| TRUST | governor | `modes/operational/governor.py` | ReasoningAgent (`:105`, call at `:212`) |
| TRUST | verifier | `modes/operational/verifier.py` | ReasoningAgent (`:90`, call at `:171`) |
| TRUST | sentinel | `modes/operational/sentinel.py` | none — deterministic by design |
| EXECUTE | conductor | `jazzx_sdk/conductor/` (not a `BaseMode`) | n/a — orchestrator |
| EXECUTE | optimizer | — | not implemented |
| INTERACT | narrator | `modes/operational/narrator.py` | ReasoningAgent (`:94`, call at `:165`) |
| INTERACT | influencer | — | not implemented |
| INTERACT | negotiator | — | not implemented |
| EVOLVE | evaluator | `modes/evolve/evaluator.py` | **raw `AsyncOpenAI`** — see §1.2 |
| EVOLVE | curator | `modes/evolve/curator.py` | `structured_call` (Layer 2 only) |

All five migrated modes use an identical, deliberate lazy-construction idiom — the `ReasoningAgent`
is built on first use, not in `__init__`, so a caller that only inspects `MODE_REGISTRY` metadata or
binds `ctx` after construction isn't forced to have a live runtime. The comment explaining this is
repeated verbatim in all five files. That consistency is good; it also means the pattern is a
copy-paste, which is worth collapsing into `BaseMode` (see the plan).

Each migrated mode also now threads real `TokenUsage` back through `ModeResult.token_usage`
(`modes/base.py:47-54`), with `tokens_used` kept as the back-compat int.

### 1.2 Gap A (material): EVOLVE never migrated

`EvaluatorMode` is the standout. Three separate problems, all verified by reading
`modes/evolve/evaluator.py`:

1. **It does not inherit `BaseMode`.** The class line is
   `class EvaluatorMode(Generic[TInput, THypothesisContent, TDecision]):` (`:32`). So it has no
   `mode_name`, no `system_prompt` property, no `has_tools`, and it returns an `EvaluationReport`
   directly rather than a `ModeResult`. It is a mode by naming convention only.
2. **It constructs its own provider client.**
   `self.client = client or AsyncOpenAI(api_key=getattr(settings, 'openai_api_key', None))` (`:94`).
   That bypasses `AgentExecutionService`, `resolve_model`, `RetryingModel`, and the LLM Gateway
   entirely. An Anthropic-only or Gemini-only deployment cannot run the Evaluator at all. Given that
   the v2.0 deck lists the LLM Gateway (routing, budgets, cost attribution) as service 01 and
   "cost-per-outcome instrumentation" as a double-down, a hard `AsyncOpenAI` in the mode that closes
   the learning loop is the single most out-of-policy line in the modes package.
3. **It parses JSON by hand with no schema and no repair.**
   `response_format={"type": "json_object"}` then `json.loads(...)` then `.get()` on every field
   (`:126-137`, `:147-156`). A malformed or truncated response raises or silently yields `None` for
   `qualitative_assessment` and an empty `improvement_signals` list. This is exactly the
   schema-validation-failure and truncation case `ReasoningAgent` exists to handle. A silently empty
   `improvement_signals` list means the Curator gets nothing to route and the compounding loop
   quietly stops compounding — a failure that produces no error anywhere.

`Curator.synthesize_bucket` (`modes/evolve/curator.py:240-276`) is a lesser version of the same:
it uses `jazzx_sdk/llm/structured_call.py`, which does validate against a Pydantic schema, but has
no retry, no truncation handling, and no token accounting. Layer 1 routing is pure Python and
correctly needs no LLM.

The net effect: **`ModeResult.token_usage`'s promise — "ReasoningAgent-backed modes do" — is exactly
true, and the EVOLVE category is the exception.** Cost per outcome is unmeasurable for the part of
the platform whose entire job is to measure outcomes.

### 1.3 Gap B (structural): the catalog is inert

`MODE_REGISTRY` is declarative and nothing consumes its semantics. Verified by grep:
`autonomy_default`, `canonical_produces`, and `derived_object` appear in `modes/catalog.py` and
nowhere else in `jazzx_sdk/` (the only other hits are `experts/catalog.py`'s parallel, separate
`ExpertContract` fields). `MODE_REGISTRY` itself is referenced only by `modes/stubs.py` (for the
error message) and by docstrings.

Consequences:

- There is no `get_mode_impl(name)`. The catalog says thirteen modes exist; the code offers no way
  to ask which of them you can actually run. `NotImplementedMode` exists as the answer, but you only
  discover the gap by calling `await mode.run()` and catching `ModeNotImplementedError`.
- The Assistant Binding Annex §6.1 defines a **mode composition matrix** as a normative,
  certifiable part of an assistant's contract, and §12 is a certification checklist.
  `ProfileRegistry.validate()` cross-checks skills, guardrails, MCP servers, and the
  assistant-as-skill composition DAG — but there is no equivalent check that a declared mode
  resolves to a live implementation. An ABA binding record can therefore name `simulator` in its
  composition matrix, pass every automated check the SDK has, and fail at runtime.
- `autonomy_default` is the natural bridge to `AuthorityMatrixV2` / `check_action` — the ladder
  (L0 Assist / L1 Recommend / L2 Execute-with-approval) is the same idea. Today the two live in
  different files with no relationship. `GovernorMode` does consult `check_action` before its LLM
  step (`governor.py:129`, `:237-273`), which is the right shape; the catalog's own autonomy
  defaults just aren't part of it.

### 1.4 Gap C (correctness, same class as the known P0): prompt resolution fails silently

`BaseMode.system_prompt` (`modes/base.py:132-152`):

```python
try:
    self._system_prompt = self._prompt_resolver(self.mode_name, self.pack_id)
    ...
except FileNotFoundError as e:
    logger.warning(f"Prompt file not found: {e}")
    self._system_prompt = f"You are the {self.mode_name} mode."
```

A pack whose mode asset is missing or misnamed does not fail. It runs with a nine-word generic
prompt and produces confident, ungrounded output. This is the identical failure mode the
`Builder_Pack_Studio_Paradigm_Assessment` names as the platform's stated principle — *capability
fails loud, knowledge fails silently* — and which the japes backlog scoped as **P0** for
`resolve_knowledge()`'s `docs:` branch. The same bug exists here, in the base class every mode
inherits, and it is not on the backlog.

Note the asymmetry with `EvaluatorMode`, which *does* fail loud: it raises `ValueError` if
`prompt_resolver` or `model_tier_parser` is absent (`evaluator.py:75-84`). The mode that didn't
migrate has the better failure discipline on this axis. Both should be loud.

### 1.5 Gap D: nobody uses the ceiling

`ReasoningAgent`'s docstring promises "the same call with `tools=[...]` — MaxTurns continuation,
batched multi-item prompts, and (once built) precomputed grounding / ensemble replication layered
on top." All of that machinery now exists:

- `agents/reasoning/grounding.py` — `PrecomputedGrounding`, `BrowseGate`, `HeadingsOnlySelector`,
  `KeywordPrefilter`, `InMemoryGroundingCache` (macer's retrieval-then-lockdown pattern,
  generalized).
- `conductor/replication.py` — `run_replicated_segments`, with `failed_replicas` as a first-class
  return so a failed replica can't dilute a vote.
- `conductor/ensemble.py` — `DeterministicVote`, `AnyEscalate`, `LlmFold`.

But `ReasoningAgent` itself references none of them, and every mode passes `tools=None`. All six
operational modes' `has_tools` return `False` (verified). The ceiling is therefore assembled by
callers, and there is exactly one caller: `agents/adjudication/pipeline.py::run_segment`.

This isn't necessarily wrong — keeping the primitive thin and composing above it is defensible, and
it is what `AdjudicationAgent` demonstrates. But the docstring reads as if the ceiling is *in* the
agent, and the practical situation is that no cognitive mode has ever exercised grounding,
replication, or collapse. Any claim that "the modes are on the new chassis" should be read as "the
modes are on the new chassis's floor."

### 1.6 What the migration genuinely got right

Worth stating plainly, because it is the part to defend:

- Sentinel was correctly *not* migrated. It is `ModeKind.DETERMINISTIC` and pure Python for speed
  (`sentinel.py:56`). Migrating it would have been cargo cult.
- `GovernorMode` short-circuits to a typed `Refusal` on an inadmissible action *before* any LLM step
  (`governor.py:129`, `:259`). Policy-as-runtime that spends no tokens on a decision it isn't
  allowed to make is exactly right, and it is the pattern the other TRUST modes should copy.
- The `(final_output, session, usage)` tuple means token accounting is structural, not opt-in.
- `run_kit.run_agent` centralizes the four retry categories through
  `jazzx_sdk.failures.classify_failure` rather than macer's string-matching. This is macer's
  `agent_utils.run_agent` promoted into the SDK and improved — the single most valuable thing the
  chassis work extracted.

---

## 2. Using this in jaci — commercial lending, and specifically spreading

### 2.1 The current state, bluntly

jaci does not import `jazzx_sdk.agents.reasoning` anywhere. Five docstring mentions, zero imports.
It reaches `ReasoningAgent` only transitively: importing `InvestigatorMode` gets you one at run
time. `jazzx_sdk.agents.adjudication` has zero references of any kind — `grep -rn "adjudicat"`
across the entire repo (excluding `.venv`) returns nothing.

Meanwhile the CL spread pipeline's only remaining hand-written LLM call is
`capabilities/commercial_lending/pipeline.py:145-200` (`run_entity_extraction`) — a raw
`LLMManager().run(...)` with `_ENTITY_PROMPT`/`_ENTITY_SYSTEM` string constants and a bare
`json.loads`, with no output schema, no `Refusal` on parse failure, and no confidence. That is the
generic-tier problem the whole `ReasoningAgent` migration was undertaken to eliminate, still live in
the flagship use case.

And `structure_statement` — the one LLM call in the spreader that actually matters — lives in
`jazzx_sdk.finance.structure` and is invoked directly by `spreader.py:83-137`, not through
`ReasoningAgent`. So the spread's structuring step has no retry-on-schema-failure and no truncation
handling, on a call whose output is a whole statement grid.

### 2.2 Where ReasoningAgent belongs in the spread pipeline

The `CL_SPREAD_PIPELINE` is `ingest → classify → spread → metrics → validate → gate`. Three of those
six steps make model calls or should:

**`cl.classify`** is today a filename-keyword match (`pipeline.py:41-49`). The PRD's FR-SRC-1
requires detecting and labelling assurance level per statement/period (audited / reviewed /
compiled / tax / company-prepared / internal interim / management schedule / derived), and FR-SRC-2
requires applying a user-supplied source precedence. Neither is derivable from a filename. This is a
`ReasoningAgent` floor call with a small closed-vocabulary output schema, and it is a genuinely
missing P0 requirement, not a refactor.

**`cl.spread`** — `structure_statement` should route through `ReasoningAgent` rather than a bare
`llm.run`. The immediate wins are the ones the docstring lists: schema-validation feedback-and-retry
when the model returns a malformed grid, truncation retry when a large statement blows the output
budget, and a real `TokenUsage` per statement so cost-per-spread becomes measurable. The ceiling
matters here too: a statement grid is exactly the kind of extraction where `run_replicated_segments`
with `k=3` and a per-cell `EnsembleCollapse` turns jaci's constant `Confidence(0.98)` into a real
agreement signal. `reconcile_packages` in `spread_package.py:248` already does per-`(statement,
line, period)` voting and is **built but never invoked outside `tests/unit/test_spread_package.py`**
— it is one wiring change away from being the collapse step.

**`cl.validate`** — the four arithmetic controls (`detect_balance_control`, `detect_cash_flow_tie`,
`detect_equity_rollforward`, `detect_period_continuity`) only run when `control_tolerance is not
None`, and `credit_validation/provides.py:36` never passes one, and `CLSpreadContext` has no field
for it. **Those four detectors are dead in the governed pipeline.** They are exercised only from
tests. That is a one-line-plus-one-field fix and it should happen before any of the more interesting
work.

### 2.3 Which cognitive mode maps to what — and the honest answer about modes

The YETI charter assigns Stage 3 to "Cognitive Mode: Reasoner (spreading reasoner); Cognitive Mode:
Evaluator (grade vs ground truth); Cognitive Mode: Sentinel (citation and trace)." Read against the
code, that mapping is aspirational in a specific way worth naming.

`ReasonerMode`, `InvestigatorMode`, `GovernorMode`, `VerifierMode` and `NarratorMode` are all
generic over `Context` / `Hypothesis` / `Decision` — the AML/KYC investigation-loop canonical
objects. A spread is not that shape. `AdjudicationAgent`'s own docstring makes this point about
itself and resolves it the right way: it uses thin `ReasoningAgent`-based `_reconcile`/`_emit`
defaults "not the heavier `GovernorMode`/`NarratorMode` classes — those are shaped around the
AML/KYC investigation loop's `Context`/`Hypothesis`/`Decision` canonical objects, a different data
shape than a bare `list[RuleOutcome]`" and notes that "mode is not load-bearing at runtime… what
matters is tagging each step's *trace* with the right mode string" (`adjudication/agent.py:8-17`).

That is the correct guidance for CL spreading too. **Do not force the spread pipeline through the
investigation-loop mode classes.** Use `ReasoningAgent` directly, tag the trace with the mode name,
and let the mode taxonomy be a governance vocabulary rather than a runtime dispatch. The one
exception is `EvaluatorMode`, which genuinely maps — but only after §1.2's gaps are closed, and jaci
already subclasses it at `scenarios/ci_spread/modes/evaluator.py`.

`SentinelMode` maps to the spread's provenance/XF-1 assertions (`assert_xf1`,
`incomplete_line_items`, `float_value_leaks`) — which are already deterministic Python, which is
exactly what `ModeKind.DETERMINISTIC` means. That mapping is already satisfied in substance; it just
isn't labelled.

### 2.4 Other CL use cases with the same shape

Beyond spreading, three live jaci surfaces have the same "one prompt, structured output, needs
retry and token accounting" profile and none of them uses `ReasoningAgent`:

- **Covenant compliance** (`validation.check_compliance` against configured definitions,
  PRD FR-CUS-4). Deterministic today where definitions are configured; the deferred part —
  parsing covenant definitions out of loan agreements — is a natural `ReasoningAgent` ceiling call
  with `EvidenceWorkspace` narrowing to the agreement document.
- **Add-back adjudication** (`addback_library.py`'s candidate/approved gate, FR-ADJ). Deciding
  whether a claimed add-back is supportable from the package is a per-item judgment over shared
  evidence — the exact batched shape `run_segment` implements.
- **Break-outs and reclassifications** (FR-MAP-3/4: officers' comp out of SG&A, D&A across COGS and
  opex, interest embedded in COGS). Today rule-driven from pack YAML. The residual cases the rules
  miss are per-line judgments over one statement — again the batched shape.

---

## 3. Learning from macer: where AdjudicationAgent fits in jaci

### 3.1 What macer actually is, structurally

Stripped of mortgage vocabulary, macer is: *for each section of an obligation register, run one
batched LLM call that verifies every obligation in that section against shared case evidence; do
that k=3 times independently; adjudicate the k results per obligation with a safety-biased
precedence order; preserve the dissent; then reconcile against the previous run and against
human vetoes.*

Its five adjudication mechanisms, in the order they matter:

1. **Cross-run consensus** — an LLM `summarization_agent` counts votes and applies a precedence
   table (`CONDITIONAL > FAIL > NOT_APPLICABLE > INFO > PASS`) that exists only in a prompt string.
   Minority view preserved in `minority_report`.
2. **Loan-metric reconciliation** — real deterministic voting code with a two-stage design:
   value wins on frequency → completeness → earliest run, with **provenance deliberately excluded**
   so a citation can never flip which value wins; then among value-agreeing runs, the one that cited
   a source wins the display row (`loan_metrics_utils.py:491-500, 576-634`).
3. **Across-time reconciliation** — previous vs current conditions, with the LLM trusted only for
   resolution status and never for content, plus a safety net that re-adds anything the model
   silently dropped.
4. **Human veto as hard precedence** — an `ExclusionIndex` of underwriter-rejected evidence, applied
   both as a prompt instruction and as a deterministic post-hoc revert.
5. **Validators as a retry channel** — Pydantic `model_validator` raises → `ModelBehaviorError` →
   corrective message injected → retry. Includes an anti-hallucination check that cited page numbers
   must exist in the referenced document.

macer's own documented weakness: "15-18% of JTBDs produce 2-1 splits in every experiment — coin
flips at the PASS/CONDITIONAL boundary," and the split ratio is not persisted as a field.

### 3.2 What japes generalized, and what it fixed

`agents/adjudication/` is a careful generalization and it improves on the original in four specific
places, each of which is worth knowing because they are the arguments for adopting it:

- **`rule_id` echo instead of positional zip.** `_BatchItemVerdict` requires the model to echo
  `rule_id` and validates it (`pipeline.py:44-53`). macer aligns results positionally and backfills
  missing ones with `NOT_APPLICABLE` — a silent-degradation path. japes drops an unreturned
  obligation from the vote instead (`pipeline.py:171`), and emits `INDETERMINATE` if every replica
  dropped it (`pipeline.py:192-195`).
- **Failed replicas excluded, not synthesized.** macer's failed replica synthesizes an `ERROR` vote
  that still dilutes the fold. `run_replicated_segments` returns `failed_replicas` separately, and
  every `EnsembleCollapse` takes it as `excluded` for bookkeeping but never votes on it.
- **Collapse is a strategy, not a prompt.** `DeterministicVote` implements macer's precedence table
  with no LLM call at all; `AnyEscalate` handles asymmetric risk (one flagged replica wins outright);
  `LlmFold` preserves macer's behaviour where you want it. macer's precedence lives in a prompt
  string in two places.
- **Vote accounting is first-class.** `Ensembled(result, votes_considered, votes_excluded)` — the
  2-1-split visibility macer lacks.

Plus two things macer proved and japes made reusable: `EvidenceWorkspace` (P4) narrows evidence
access per segment through the same `PermissionScope`/`admit_hop` cascade `InteractiveAgent` uses
for skills, and `ReadTooLarge`/`enforce_read_cap` errors rather than truncating silently. And
`impact.py` (P3) reframes incremental re-run from macer's document-mapping-file join to
"which context fields does this rule's condition read" via `evidence_contract()` — domain-neutral.

Honest gaps in the chassis: `AdjudicationAgent._reconcile` is a no-op passthrough (`agent.py:138`);
there is no analogue of macer's exclusion index, its across-time condition resolver, or its
citation-page validator. The docstring says so.

### 3.3 The parallel jaci use case: spread validation as adjudication

The structural match is close enough to be worth stating as a mapping.

| macer | japes chassis | jaci CL spread |
|---|---|---|
| JTBD (one obligation) | `Rule` in a `SegmentSpec` | one `ValidationFinding` check, or one add-back candidate, or one covenant test |
| Section / domain | `SegmentSpec.key` | statement (IS/BS/CF), or PRD requirement family (FR-VAL / FR-MAP / FR-ADJ) |
| Loan file + guidelines | `context` + `EvidenceWorkspace` mounts | `SpreadPackage` + source markdown + pack policy assets |
| Guideline retrieval → lockdown | `PrecomputedGrounding` + `BrowseGate` | chart of accounts + policy YAML, precomputed per statement |
| `verify_all_jtbds` batch | `_render_batch_prompt` / `run_segment` | one call per statement covering every judgment-requiring check on it |
| 3 parallel inferences | `run_replicated_segments(replicas=3)` | 3 extraction/judgment passes — what `reconcile_packages` already anticipates |
| `summarization_agent` majority | `DeterministicVote(priority=[...])` | severity precedence over the PRD's six severities (FR-VAL-10) |
| `minority_report` | `Ensembled.votes_excluded` + votes | per-cell confidence, replacing the constant `0.98` |
| UW-rejected evidence gate | *(not in chassis)* | `hitl_approval` / `corrections.py` override lineage — jaci has this and the SDK doesn't |
| Incremental rerun by changed docs | `impacted_rules(changed_fields)` | re-spread when one filing is restated; `merge_spreads` already says "restatements win" |

Three concrete adoption targets, in order of value:

**(a) Validation as an obligation register.** jaci's 17 detectors are deterministic Python. Under the
chassis they become `Rule` objects whose `condition` is an `Expression` — which `partition_rules`
routes to the DETERMINISTIC partition, `k=1`, **no LLM call and no cost**. The judgment-requiring
checks (`detect_cross_document_contradictions`, `detect_undisclosed_obligations`,
`detect_sign_label_errors`) become `NaturalLanguageCondition` rules in the LIVE partition, batched
and replicated. One run produces both, with one uniform `RuleOutcome` stream, one trace, and per-rule
vote accounting. This is the single highest-value move: it costs jaci almost nothing (the
deterministic detectors keep working exactly as they do) and it gives the judgment cases the full
ensemble discipline for the first time.

**(b) Per-cell confidence from replication.** `spread_package.py:46-48`'s `_SOURCED_SCORE = 0.98` on
every cell means `Confidence` carries no signal, which the RB reference test can't use and the
review queue can't rank on. Running `structure_statement` under `run_replicated_segments` with
`key_of=lambda cell: (statement, line_key, period)` and collapsing with a value-frequency strategy —
adopting macer's two-stage rule that *provenance is excluded from deciding which value wins, then
included in deciding which run's row is displayed* — turns `Confidence` into agreement-derived. That
directly serves the PRD's "High/Med/Low confidence surfaced via cell notes" and the risk-ranked
review queue (FR-HIL-1).

**(c) Incremental re-spread.** `impacted_rules` + `merge_with_carry_forward` + `resolve_run_mode`
give you "one filing was restated, re-run only what reads it." jaci's `merge_spreads` already
encodes "restatements win"; the chassis supplies the run-mode discipline around it.

### 3.4 What jaci should contribute back

The traffic isn't one-way. jaci has two things the chassis explicitly lacks:

- **`_reconcile` is a no-op in the SDK**, and jaci's `hitl_approval.py` / `corrections.py` /
  `promotion.py` are a working maker-checker with `AuthorityMatrixV2` + `check_action` and
  per-correction override lineage. That is the real `_reconcile`. It should be prototyped as a jaci
  subclass and then promoted.
- **macer's exclusion-index pattern has no SDK home**, and jaci's correction lineage is the closest
  existing thing. "A human rejected this evidence for this finding; never let it justify that
  finding again" is a domain-neutral governance primitive and it belongs next to
  `EvidenceWorkspace`.

---

## Summary of findings, ranked

1. **`EvaluatorMode` bypasses the platform** — own `AsyncOpenAI` client, no `BaseMode`, no
   `ModeResult`, hand-parsed JSON. The compounding loop has no gateway governance, no retry, no
   token accounting. (§1.2)
2. **Four arithmetic controls are dead in jaci's governed pipeline** — `control_tolerance` is never
   passed. A shipped validation requirement silently doesn't run. (§2.2)
3. **`BaseMode.system_prompt` fails silently on a missing pack asset** — same bug class as the
   known P0 in `resolve_knowledge()`, in the base class every mode inherits. (§1.4)
4. **jaci uses neither `ReasoningAgent` nor `AdjudicationAgent`** while its flagship pipeline still
   carries a raw `LLMManager().run()` + `json.loads` extraction call. (§2.1)
5. **`MODE_REGISTRY` is inert** — no implementation resolution, no validation that an ABA
   composition matrix names runnable modes, `autonomy_default` unconsumed. (§1.3)
6. **No mode exercises the ceiling** — grounding, replication, and collapse exist and are used only
   by `AdjudicationAgent`. (§1.5)
7. **`reconcile_packages` and `Confidence` are the missing link** — jaci built the multi-pass voter
   and never invoked it; every cell's confidence is a constant. (§3.3b)
8. **`AdjudicationAgent._reconcile` is a no-op** and jaci already has the real implementation in its
   HITL/promotion layer. (§3.4)
