# macer's adjudication agent against the SDK's `AdjudicationAgent`: is the SDK a superset?

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Survey note, 2026-11-18, brought to the 2.7.5 state at tip `f353700e` (both suites green there: 14141 passed, 36 skipped). Decides nothing; no loan run, no provider call. Read-only surveys of macer (`japes-2.7.4`, `src/macer/`) and japes (`v2.7.5`, `jazzx_sdk/`), plus targeted checks I ran offline (named below); rows say what 2.7.5 changed and the commit. Earlier answers: `plans/note_sibling_parity.md` (2026-10-12) and `plans/note_parity_adjudication_20261012.md`; this note re-checks them against the code as it is today.

## Why the framing changed

macer may not adopt `AdjudicationAgent`. Other use cases (Acra, healthcare) will run the SDK agent instead of going to macer, so the SDK has to hold every capability macer has, or list it as a gap. Rule for the gaps: absorb the capability, improve it, do not copy it, and keep consumer names out of SDK code.

**Verdict.** Not yet a superset. The SDK is equal or ahead on verdict handling, cites, rerun impact, evidence rejection, vote tallies, replica failure visibility, cost provenance and pricing. 2.7.5 closes four of the ten gaps this note first listed: output control (spec fields `reasoning_effort`, `verbosity`, `max_output_tokens`), the truncation path (an SDK incomplete or failed raise maps to `IncompleteOutputError` on OpenAI Responses and Chat Completions, and a Gemini `MAX_TOKENS` finish reads as incomplete), the tool failure text on the adjudication tools, and the schema-level subject enum. It half-closes two more: trace hooks attach to adjudication but stay off until a host installs a tracer, and the calculation tool can be turned on for adjudication (default off) without a field for extracted values. Still open: extracted values with a metric-key rule, condition lifecycle beyond one run, a built-in applicability planner, a pack-selectable guideline selector, retrieval of a capped search result, the input filter on by default, and a per-rule verdict comparison over repeats (the experiment-level comparison exists). The plan for the open items is `plans/adjudication/plan_adjudication_superset_of_macer_2026-11-18.md`.

## How this was surveyed, and what could not be verified

Three read-only survey agents (macer side, japes side, upstream-package insulation) each reported file:line facts; I spot-checked the claims this note leans on and ran four offline probes with no provider call:

1. `_looks_like_tool_error` on openai-agents 0.24.0 (run in the japes venv).
2. Whether macer's guideline-browsing gate opens after a read through the real tool wrapper (macer, on a throwaway env at the PR lock, tmp dir only; the gate stayed closed, see row T9).
3. That openai-agents 0.24.0 raises on a non-streaming Responses with status `incomplete` (read `agents/models/openai_responses.py:888-890`).
4. Where `tool_error_text` is and is not used (grep).

Plainly, not verified:

- **macer survey read macer's own `.venv`, which holds openai-agents 0.17.7**, not the PR lock (0.24.0). Statements about the SDK default tool-error text in the macer survey describe 0.17.7. On 0.24.0 it is the fixed sentence (verified).
- Lines marked `~` are the survey's approximate lines.
- How the SDK builds the provider request from `output_type`, and whether `tool_choice="none"` is honored on the OpenAI Responses and Claude gateway wires: not read.
- Which Claude route production uses (`GatewayRoute` is installed by the host).
- Whether `AdjudicationInvoker` (`pack/eval_invoker.py`) runs under a `CallMeter` and call deadline, and whether any host builds `AgentTraceHooks` for adjudication (searched `jazzx_sdk` only).
- macer: `common.core.ai_gateway` (outside `src/macer`), the middle of `BATCH_SYSTEM_PROMPT`, most of `condition_dedup/`, `rerun/` bodies, `findings_converter.py` beyond a skim, and every test body.
- japes: test fixture contents, `server/eval_wiring.py`, the full `MODEL_PRICING` table.
- Nothing here measures quality. No claim below says macer's output is better or worse.

## 1. Parity table

Direction: **macer adopt** (macer should take the SDK's way), **SDK absorb** (the SDK should take macer's capability, improved), **equal**. Paths: macer under `src/macer/`, japes under `jazzx_sdk/`.

### Loop, budget, retries

| # | Stage | macer | japes | Gap | Direction |
|---|---|---|---|---|---|
| L1 | Turn budget | 100 default (`agents/agent_utils.py:217`, `runtime/config/defaults.yaml:34`; payload 1 to 1000, `japes/config_schema.py:45-50`) | 30 (`agents/run_kit.py:636`, `agents/adjudication/spec.py:39`, per spec) | defaults differ; both configurable | equal |
| L2 | After MaxTurnsExceeded | continuation attempt `{name}_final`, tools dropped, 1 turn, "do NOT call tools" directive (`agent_utils.py:241-248,303-328`) | same shape (`run_kit.py:730-738,771-776`) | none | equal |
| L3 | Retry bound | 3 failed attempts per class, independent counters (`agent_utils.py:232-236`) | same counters (`run_kit.py:716-720`), plus a separate budget of 2 for cite feedback (`run_kit.py:791-794`, `adjudication/segment.py:124`) | none | equal (SDK ahead) |
| L4 | Validation retry | only the feedback is resent; tools kept, `tool_choice="none"` (`agent_utils.py:257-266,340-376`) | same (`run_kit.py:591-604,744-750`) | none | equal |
| L5 | A fixable error that needs a tool | `ToolRetryRequiredError`: unknown cited filename sends the model to `list_documents`, a page out of range to `read_document`, missing calculation to `python_repl` (`agents/validated_output.py:48-73`, `jtbd/jtbd_utils.py:~587-593`, `jtbd/loan_metrics_utils.py:~224-249`) | mechanism exists (`run_kit.py:241-243,275-276`); no adjudication validator raises it (`segment.py:186-191` uses `ExtraRoundValueError`); I did not verify whether cite feedback keeps tools callable in tools mode | a bad cite in tools mode may not send the model back to the document tools (still unverified) | SDK absorb |
| L6 | Transient API errors | two layers: `Retry` 3 retries, 30 to 180 s (`agent_utils.py:160-167`) and `RetryingModel` 4 attempts, 45 to 300 s (`agents/__init__.py:305-307`, `models/retrying.py:104`); comment admits they multiply (`agent_utils.py:155-157`) | two layers: `run_kit` 3 tries, 2 to 30 s (`run_kit.py:109-114,779`) and `RetryingModel` 3 attempts, 10 to 300 s (`agents/models.py:132-260`, `concurrency/rate_limit.py:38-41`) | both stack on an outage; neither caps the total | equal (both should cap) |
| L7 | Reasoning-item 400 recovery | replaces the orphaned item and retries (`models/retrying.py:67-101,188-207`) | same (`agents/models.py:42-46,92-99,236-244`) | both match OpenAI's literal message | equal |
| L8 | Truncated output | `IncompleteOutputError` when a message has status `incomplete`, retry with "be more concise", tools off (`models/retrying.py:38-64`, `agent_utils.py:378-403`); the SDK's terminal-status raise pre-empted it on openai-agents 0.22.0 and later, fixed on the PR branch in `7abbba0b` (counted by `incomplete_output_errors`; `incomplete_responses` does not fire for these, since the SDK raises before a response exists) | the same design (`agents/models.py:73-85,250-259`, `run_kit.py:607-619,804-811`); 2.7.5 maps the SDK's incomplete or failed raise to `IncompleteOutputError` on Responses (blocking and streamed) and Chat Completions or Fireworks (`af8fab29`), and a Gemini `MAX_TOKENS` finish to incomplete, blocking and streamed (`ae2d880d`); gateway and native Claude already marked incomplete; the truncated OpenAI attempt's usage is not on the SDK error, so it is recorded as an incomplete call with cost marked an upper bound (`3d3e9e1a`) | closed in the SDK; macer closed on its PR branch (local until pushed). Left: a streamed Gemini answer cut off before any text emits `output_item.done` with no `added` before it; `KernelModel` marks no truncation (not checked whether the kernel response carries a finish reason) | equal |
| L9 | Output cap | `max_tokens` 64000 on every request (`agents/__init__.py:381,409`, `defaults.yaml:36`) | `max_output_tokens` is a spec field, unset means unchanged (`89d0bcd3`); native Claude was never capped at 4096 when a card exists: it takes the card limit (128000 for `claude-sonnet-5-5` and `claude-opus-5-5`) and 4096 only for a model with no card (`agents/anthropic_native.py:22,218,234-239`, a test pins it) | a spec now sets a per-step cap; no default cap | equal (SDK has the setting, macer pins 64000) |
| L10 | Session size | `InputFilter` drops oldest reasoning groups above 750 KB (`input_filter.py:30-184`) | same filter, off by default (`run_kit.py:696-700`); the filter is stronger than macer's | default off; the number needs a measurement, 750 KB is only a starting value | SDK absorb the default (plan item G1, early 2.7.x) |
| L11 | Per-call time bound | none beyond client timeouts 500 or 900 s (`agents/__init__.py:152-169`) | 4500 s deadline for case runs (`agents/call_guard.py:34-46`, `pipelines/kinds.py:773,824,865`); not verified for `AdjudicationInvoker` | macer has no bound | macer adopt |

### Tools

| # | Stage | macer | japes | Gap | Direction |
|---|---|---|---|---|---|
| T1 | Tool set | list, read, search, `read_reference`, `python_repl` over four sources (`jtbd/jtbd_agent.py:~1960`, `tools/documents.py:252-690`, `tools/repl.py:299`) | list, read, search over one mounted directory (`tools/agent/dir_tools.py:421-552`); inline mode has no tools (`segment.py:736`); tools mode can add the calculation tool behind `EvidenceSpec.calculator`, default off | no retrieval of a capped search result | SDK absorb |
| T2 | Calculation | `python_repl`: restricted exec, 30 s, injected tools, `calculation_markdown` required for metrics (`tools/repl.py:48-102,236-237`, `models/jtbd.py:435`) | `tools/calculate.py` (`Calculator`, `CalculationLog.has_result`, `calculate_tool`), used by `pipelines/policy/code.py`; in 2.7.5 adjudication can use it behind `EvidenceSpec.calculator` (default off) and each outcome's inputs record the logged calls under `calculations` | no field for extracted values and no claimed-calculation check (plan item A2, 2.8) | SDK absorb (improve: a sandboxed calculation hook, not a copy of this exec) |
| T3 | Read cap | 10 KB literal, whole lines, continue footer (`tools/documents.py:363`) | 10 KB from the spec, same footer (`adjudication/spec.py:37`, `dir_tools.py:245-269`); the spec docstring (`spec.py:36`) still says a larger read errors | macer hard-codes | macer adopt |
| T4 | Error convention | expected errors returned as `Error: ...` text (`tools/documents.py:214,326,520`); `python_repl` returns `--- Error ---` (`tools/repl.py`); no `failure_error_function` (grep) | same for `dir_tools` (`dir_tools.py:148-243`); no `failure_error_function` or `tool_error_formatter` anywhere in `jazzx_sdk` (grep) | unexpected exceptions reach the model as the SDK's fixed sentence on 0.24.0 in both | equal |
| T5 | Error helper | none | `tool_error_text` keeps the old wording with the message, in `failures.py` (the `jazzx_sdk` root) since 2.7.5, and scrubs credentials; the adjudication tools use it on 21 sites, including the skill `as_tool` (`395353d3`, `be1602cc`) | none | equal (SDK ahead) |
| T6 | Recognizing a tool error in streams | n/a | `_looks_like_tool_error` (`agents/interactive/stream_hooks.py:31-38`) probes the default at import; verified on 0.24.0: the default sentence and `tool_error_text` output both match; `Error: ...` and `--- Error ---` text do not | an `Error:` string reads as success in the stream | SDK improve |
| T7 | Invalid tool arguments | SDK redacts the validation detail (0.19.4 and later): the model gets only "An error occurred while running the tool. Please try again." (probed on the PR lock) | same SDK behavior | none | equal |
| T8 | Path safety | `read_document` had no `..` or absolute-path check; a leading `-` pattern reaches grep as an option (`documents.py:~521-555`); fixed on the PR branch: `read_document` in `7cf91e2a`, `write_document` in `55c3fae1` (one shared `_is_within` check on resolved paths; the old `startswith` check let a sibling directory such as `output_evil` through) | rejects `..` and absolute paths (`dir_tools.py:148-155`), explicit `-e` for grep (`dir_tools.py:317-343`) | macer's grep option case is not fixed; the path fixes are local until pushed | macer adopt |
| T9 | Guideline-browsing gate | blocks list and search on guidelines until one is read (`tools/documents.py:41,196-207,502-513`). The flag was set inside a sync tool that the SDK runs in a worker thread, so it never reached later calls (verified offline on the PR lock); fixed on the PR branch in `19ab3914` with the flag held in a mutable holder placed in the context, tested through the tool wrappers | `BrowseGate` exists (`agents/reasoning/grounding.py:222`) but is not wired into adjudication | japes has no gate in adjudication | SDK absorb a wired gate |
| T10 | Search output size | headroom compression with a `read_reference` retrieval (`compression/headroom_store.py:154-191`, `defaults.yaml:104-111`) | cut at 200 lines with "narrow the pattern" (`segment.py:503-512`) | no way to get the cut part back | SDK absorb (plan item F2, early 2.7.x: a per-run holder behind a `read_reference` tool, no compression library) |

### Structured outputs

| # | Stage | macer | japes | Gap | Direction |
|---|---|---|---|---|---|
| S1 | Validated output | `ValidatedOutput` over `AgentOutputSchema`; feedback is `loc: msg`, at most 8, never values (`agents/validated_output.py:95-181`) | same (`run_kit.py:262,292-310`, max 8) | none | equal |
| S2 | Schema strictness | strict; every static and token-scoped schema builds on the PR lock (my tests `tests/test_agent_output_schemas.py`, 24 pass, commit `d2ba5f30`) | `_BatchVerdict` strict, all properties required (`segment.py:203`; probed by the japes survey) | none | equal |
| S3 | Raw schema output | `RawJsonSchemaOutput` for the findings converter only (`agents/json_schema_output.py:13-87`) | exists (`run_kit.py:191-224`), unused in adjudication | none | equal |
| S4 | Output rules | CONDITIONAL needs conditions, metric keys, borrower ids, calculation markdown, page numbers and citations (`models/jtbd.py:372-459`) | conditions fit the rule, cites fit the run (`segment.py:179-191,457-469`) | japes has no metric-key or calculation rule and no field for extracted values (plan item A2, 2.8); macer silently repairs `[Page N]` to `[Page 1]` for one-page documents (`jtbd_utils.py`) | SDK absorb metric rules; macer adopt cite-feedback rounds |
| S5 | Cites that fail | feedback every time, up to the retry bound | first 2 responses get feedback, later ones stand with `cites_unverified`, which can downgrade the verdict (`segment.py:457-469,818-820`, `admissibility.py:22-35`) | none | macer adopt |
| S6 | Subject or borrower ids | token enum in the schema itself (`Literal[BOWW1...]`, `models/jtbd.py:671-754`, cached with `lru_cache`) | a run with subjects builds the verdict type with the subject enum in the schema (`15c0c433`); a run with no subjects keeps `_BatchVerdict` and the validator; a subject written with surrounding spaces is now refused, which costs a retry, not a wrong answer | none | equal |

### Context assembly

| # | Stage | macer | japes | Gap | Direction |
|---|---|---|---|---|---|
| C1 | Unit of work | one agent call per section and replica, all applicable rules together (`jtbd/jtbd_agent.py:1681-1796`) | one per segment and replica, all live rules (`segment.py:539-581`) | none | equal |
| C2 | Evidence scoping | per-section routing of documents and entities (`jtbd/sections.py:93-166`) | scoped per segment, shared evidence hoisted once (`segment.py:529-557`), bins by section (`adjudication/planner.py:106-128`), evidence contract per rule | none | equal (SDK ahead) |
| C3 | Applicability | LLM planner with a closed mnemonic enum, on by default (`jtbd/planner/runtime/planner_agent.py`, `defaults.yaml:63`) | per-rule applicability gate (`segment.py:650-671`) and a `SegmentPlanner` plugin point, no built-in planner (`planner.py:58-86`) | no shipped LLM triage (plan item D, 2.8) | SDK absorb |
| C4 | Guideline context | an LLM picks up to 3 snippets per rule from a heading catalog, cached in Redis (`jtbd/guideline_enrichment.py:219-267,377`) | a pluggable selector exists: `SnippetSelector` in `agents/reasoning/grounding.py` with `HeadingsOnlySelector` (an LLM picks from headings only, a failure falls back to none) and `TopRankedSelector`, plus a `GroundingCache` seam; adjudication uses top-k grounding (`pipelines/steps.py:1843-1858`) and learned guidance retrieval (`adjudication/guidance.py:29-43`) | a pack cannot choose the selector (`pipelines/steps.py:1853` hard-wires `TopRankedSelector`) and there is no persistent cache (plan item F1, early 2.7.x) | SDK absorb (let a pack choose; do not copy the Redis cache) |
| C5 | Reruns | three modes, change-focus preamble, previous finding in the prompt (`jtbd/run_mode.py:40-70`, `jtbd/rerun/change_focus.py`) | four modes with `NO_OP`, impact by evidence-contract fields, carry-forward, document focus, prior conditions (`adjudication/impact.py:31-96`, `pipelines/steps.py:1805,1958-1967`) | macer has per-section document history and a rerun ledger (`jtbd/rerun/document_history.py`), japes copies one prior run | SDK absorb the ledger (noted 2026-10-14) |
| C6 | Rejected evidence | an exclusion index used by the resolver and the converter, not the verifier prompt (`models/evidence_exclusion.py`) | told in the prompt, and a verdict resting only on rejected cites becomes INDETERMINATE (`segment.py:594-612`) | none | macer adopt |
| C7 | Prompt control | byte-for-byte snapshot tests (`tests/test_prompt_snapshots.py`) | versioned prompt files, composed with provenance, `behaviour_digest` per step (`prompts/compose.py:46-56`, `agents/metering.py:201-214`); a rendered-prompt snapshot test (plan item G2, built in 2.7.5) | none | equal |
| C8 | Subjects | borrower roster with tokens (`jtbd/borrower_roster.py`) | subject tokens (`segment.py:562-563`) | none | equal |
| C9 | Program detection | an agent reads the application (`jtbd/loan_program_agent.py`) | supplied by the pack | consumer-specific | equal (pack data) |

### Conditions and outcomes

| # | Stage | macer | japes | Gap | Direction |
|---|---|---|---|---|---|
| O1 | Vocabulary | PASS, FAIL, CONDITIONAL, NOT_APPLICABLE, INFO, plus a synthetic ERROR (`jtbd/jtbd_utils.py:~624`) | closed `Verdict`: satisfied, violated, indeterminate, not_applicable, with a reason enum (`fabric/canonical/policy.py:53-71`) | INFO has no verdict of its own (I did not check how a pack maps it) | to discuss |
| O2 | Replica vote | code majority, tie priority CONDITIONAL, FAIL, NOT_APPLICABLE, INFO, PASS (`jtbd/condition_labels.py:42-54`); default 3 replicas | most-adverse or majority with a tie order, tally and dissent recorded (`pipelines/steps.py:1521-1540`, `conductor/strategies/ensemble.py:35-88`, `segment.py:615-624`); default 1 replica | defaults differ | equal (SDK ahead) |
| O3 | Reconciling replicas | a tool-less summarizer, code overrides its status, labels from evidence (Mandatory, Majority, Corroborated, Contested, Cleared and four more) (`jtbd/section_summarization.py:314-371`, `condition_labels.py:81-172`) | union of conditions from votes that reached the winning status (`segment.py:262-309`) | no evidence-backed support or dispute per condition | SDK absorb (improve: fewer labels, counts as data) |
| O4 | Condition type | three types, timing, party, ids above a watermark (`models/jtbd.py:116-233`, `jtbd/summarization_utils.py:65`) | canonical `OutcomeCondition` with kind, timing, party, resolution, subject, documents; vocabulary as pack data; ids above a watermark (`policy.py:233-246`, `adjudication/conditions.py`, `segment.py:229-259`) | none | equal (SDK ahead) |
| O5 | Dedup | semantic: embeddings, HDBSCAN, LLM clustering, reason gate, across sections and runs (`jtbd/condition_dedup/pipeline.py`) | exact identity within a run (`adjudication/admissibility.py:38-79`) | two conditions worded differently stay two | SDK absorb (improve: an embedding seam, no clustering dependency) |
| O6 | Condition resolution on reruns | LLM resolver, a document-searching resolver per open cluster, a resolver for underwriter-made conditions (`jtbd/condition_resolver.py`, `cluster_condition_resolver.py`, `manual_condition_resolver.py`) | the same call states `restates` and `resolved` (`segment.py:566-580`) | no evidence-searching resolver, no manual-condition path | SDK absorb |
| O7 | Unverified cites | rejected or repaired | downgraded to INDETERMINATE (`admissibility.py:22-35`) | none | macer adopt |
| O8 | Failed replica or section | ERROR rows, dropped later (`jtbd/section_outcome.py`) | `ReplicaFailure` not voted; rule with no votes becomes INDETERMINATE with a reason (`segment.py:834-842`, `agents/replication.py:77-89`) | macer drops what japes keeps visible | macer adopt |

### Models and routes

| # | Stage | macer | japes | Gap | Direction |
|---|---|---|---|---|---|
| M1 | Routes | OpenAI Responses, Claude via litellm or the gateway, Fireworks (`agents/__init__.py:285-339`) | OpenAI Responses, native Claude or gateway Claude, native Gemini incl. Vertex, Fireworks (`agents/models.py:350-428`) | none (japes has no litellm) | equal (SDK ahead) |
| M2 | Reasoning effort, verbosity, truncation | effort high, verbosity low, truncation disabled from run settings (`agents/__init__.py:342-415`, `defaults.yaml`) | the spec carries `reasoning_effort`, `verbosity` and `max_output_tokens`; unset means the provider default as before (`89d0bcd3`) | a spec can now pin what macer pins | equal |
| M3 | Flex tier | `flex_` prefix, 900 s timeout | `with_cost_tier` (`agents/models.py:332-347`) | none | equal |
| M4 | Cache keys | per replica from run, section and run number (`utils/cache_key.py:50-69`) | one per call, held across its retries (`run_kit.py:685-694`) | replicas do not share a key in japes | equal |
| M5 | Claude cache breakpoints | up to 4 (`models/anthropic.py:30-87`) | system, last two user turns, final (`agents/anthropic_native.py:70-86`) | none | equal |
| M6 | Fireworks | two-step split (`models/fireworks.py`) | same, ported (`agents/fireworks.py:115-161`) | none | equal |

### Cost, tracing, concurrency, evaluation

| # | Stage | macer | japes | Gap | Direction |
|---|---|---|---|---|---|
| R1 | Spans | one trace per `run_agent` with agent, `llm_N` and tool spans, tool arguments and output excerpts (`hooks.py:110-132,331-431,573-609`) | `AgentTraceHooks` (`observability/agent_hooks.py:69`) can be installed with `use_trace_hooks` and `resolve_trace_hooks`, `ReasoningAgent` runs under them, and retry counters sit on the hooks (`7992f1d9`); off until a host installs a tracer, and nothing in the repo selects a tracer backend; `adjudication/tracing.py` name patterns still have no caller | the cost of one rule's judgment is visible per call or tool only once a host installs the hooks | SDK absorb (host side) |
| R2 | Cost and cache accounting | per call at `hooks.py:441-571`; cost rounded to 2 decimals per hook and 4 in `run_metrics.json`, so two totals differ (`hooks.py:207-264`, `jtbd/jtbd_utils.py:46`); own price table last updated March 2026 (`utils/cost.py`) | `CallMeter` prices each call, buckets include cache writes, marks unpriced models as an upper bound, `BudgetExceeded` (`agents/metering.py:79-214`, `llm/cost.py:340-390`); price data with provenance (`note_pricing_parity_with_macer_2026_11_17.md`) | japes: failed attempts are missing from segment usage (`TODO(segment-usage-excludes-failed-attempts)`, `pipelines/steps.py:1916`); a truncated attempt that recovers is now recorded on the meter as an incomplete call, cost an upper bound (`3d3e9e1a`); I did not check whether that closes the TODO | macer adopt |
| R3 | Concurrency | sections 20 // 3 = 6, replicas 3 (`jtbd/jtbd_runner.py:~969,~485`) | segments 6, replicas 1 (`adjudication/agent.py:43`) | segment concurrency is a constant, not set by the spec | equal |
| R4 | Regression eval | candidate against baseline over repeats: per-rule shift of the modal verdict at 2/3 with at least 3 repeats, token-leak FAIL, cost over 1.25 times WARN; it says "same as main is not correct" (`evals/regression/compare.py:~173-203`, README) | golden verdict agreement, vote stability, condition typing, correction scoring, guidance uplift (`evaluation/adjudication_scorers.py`, `pack/correction_scorer.py`, `pack/guidance_uplift.py`); stability across repeats (`evaluation/stability.py`) | japes scores against truth but `evaluation/experiment_comparison.py` (`compare_experiments`, measured noise floor, McNemar on flips, cost) compares experiments, but the per-rule verdict comparison over repeats is missing; macer has no truth | SDK absorb the comparison; macer adopt truth scoring |

## 2. What macer has that the SDK lacked (absorb, improve, do not copy)

Shipped in 2.7.5:

1. **Output control per step.** `reasoning_effort`, `verbosity` and `max_output_tokens` on the spec; unset changes nothing. (L9, M2.)
2. **Truncation recovery that works on the current SDK.** The agents SDK's terminal `incomplete` or `failed` raise maps to `IncompleteOutputError` for every consumer; Gemini `MAX_TOKENS` reads as incomplete. (L8.)
3. **Per-call and per-tool spans,** in part: `AgentTraceHooks` attach to adjudication, off until a host installs a tracer. (R1.)
4. **Schema-level subject enum** for small rosters. (S6.)
5. **The calculation tool in adjudication,** in part: opt-in, calls recorded on each outcome's inputs. Extracted values stay open. (T2.)
6. **Failure text on the adjudication tools** and a **rendered-prompt snapshot test.** (T5, C7.)

Open, with the plan item that carries each (`plans/adjudication/plan_adjudication_superset_of_macer_2026-11-18.md`):

7. **Extracted values with provenance, a metric-key rule and a claimed-calculation check;** a pack declares the metric, not code. (T2, S4; item A2, 2.8.)
8. **Condition lifecycle across runs:** semantic dedup behind an embedding seam, an evidence-searching resolver, a resolver for human-made conditions, and support or dispute counts per condition. (O3, O5, O6; items B1 to B4, B4 early 2.7.x, the rest 2.8; B3 waits on where a reviewer's condition enters.)
9. **Applicability triage** shipped as a built-in planner using the existing plugin point. (C3; item D, 2.8.)
10. **A pack-selectable guideline selector,** and **search results retrievable in full** after a cap. (C4, T10; items F1 and F2, early 2.7.x.)
11. **Per-rule verdict comparison over repeats** (baseline against candidate) with cost ratio and a leak check, on top of the existing experiment comparison. (R4; item C, early 2.7.x.)
12. **The input filter on by default,** with a measured number. (L10; item G1, early 2.7.x.)

SDK items that macer should take: cite-feedback rounds and unverified-cite downgrade (S5, O7), visible INDETERMINATE for a failed rule (O8), field-level rerun impact (C5), path checks in the read tool (T8), a per-call deadline (L11), budget guard (R2), pricing with provenance (R2).

## 3. What blocks macer adopting the SDK agent

1. **A different status vocabulary and result shape.** `JTBDResult` (five statuses, loan metrics, `policy_ref`, observations, facts) against `RuleOutcome` and `Verdict`. A mapping layer and a metric channel are needed first.
2. **Loan metrics and extracted values** (T2, S4): the calculation tool is opt-in for adjudication now, but there is no extracted-values field or metric-key rule, so the metric half of every macer result would still be lost.
3. **Condition lifecycle** (O3, O5, O6): macer's dedup, resolvers and labels sit after the verdict and have no SDK counterpart.
4. **Observability contract:** macer's MLflow spans and per-run metrics (`hooks.py`) are consumed by its regression eval and run records; the SDK adjudication has trace hooks that a host must install, and no tracer backend is selected in the repo (R1).
5. **Output control:** macer pins effort, verbosity and a 64000 cap (M2, L9); a spec can now carry the same settings, so a mapping is needed, not a feature.
6. **Routing and runtime:** macer reads its AI Gateway flag through `common.core.ai_gateway`, caches guideline selection in Redis, and runs under the queue; the SDK's gateway route is installed by the host.
7. **Dependency posture:** macer keeps litellm and an SDK floor of `>=0.6.1`; the SDK agent needs openai-agents 0.22 or later and openai 3 (see section 4).
8. **Evidence:** a before and after on one loan set under the same model settings, which needs your typed approval and was not run.

Defects found in macer on the way, for the macer team: the browsing gate (T9, fixed on the PR branch), no path check in `read_document` and `write_document` (T8, fixed on the PR branch), the SDK-raised truncation not reaching the retry (L8, fixed on the PR branch), a stale "sequential" docstring in `jtbd/jtbd_runner.py:~68`, and a runner comment ("clustering failure has no fallback") that `llm_cluster` contradicts by treating a failed block as singletons (`jtbd/condition_dedup/clustering.py:~160-175`). The PR-branch fixes are local commits until pushed.

## 4. How the SDK handles upstream package changes

For a team adopting the SDK. CHANGELOG references are the entry's first words and its heading in `docs/status/CHANGELOG.md`.

### Lead example: own the thin connector (litellm)

Verified before writing: `pyproject.toml` has no litellm dependency or extra (only the comment at lines 123-125); `poetry.lock` has no litellm package (its one `litellm` string, line 3838, is openai-agents' own optional-extra declaration); there is no `import litellm` in `jazzx_sdk`, `plato`, tests or scripts. Remaining mentions are comments about the gateway and one stored-name prefix that `llm/model_identity.py:9` strips so old recorded names still resolve.

- **What was done.** The connectors litellm gave (Claude, Gemini, Gemini on Vertex) were written in the SDK: `agents/anthropic_native.py`, `agents/gemini_native.py`, `llm/providers/gemini.py` (`build_genai_client`). CHANGELOG [2.5.0] "LiteLLM is gone, and `openai-agents` moves 0.20 -> 0.22 with `openai` 2.x -> 3.3."
- **Why.** Not size: every litellm release through 1.98.0 pinned `openai<3.0.0`, which held openai-agents at 0.20 (`pyproject.toml:123-125`). One optional dependency set the floor for the whole SDK.
- **The size claim is not measured.** The lock went from 177 to 171 packages in the removal commit (`c3efbfd0`, litellm 1.89.2 before), but that commit is a 376-file squash with other changes, so the net is not attributable. Do not quote a number.
- **What remains.** litellm survives only as the platform AI Gateway host the SDK talks to over the OpenAI wire (`llm/gateway/`, `agents/anthropic_gateway.py`). The SDK reads its usage shapes (`llm/gateway/anthropic_chat.py:88-124`) and imports nothing. CHANGELOG [2.7.1] "AI Gateway (platform PR #108, ported".
- **Contrast.** macer keeps litellm, so its lock absorbs every litellm release (1.103.10 to 1.109.1 in this PR) and carries a patch of `litellm.acompletion` (`models/anthropic.py:158-216`).

### Per package

| Package | Layer that absorbs the change | Guard tests | Not yet insulated |
|---|---|---|---|
| openai | provider seam `llm/providers/openai.py` (usage normalizer `extract_usage:39-72` reads cache writes under either of two names, `getattr` defaults so a rename gives 0); model factory `agents/models.py:393-406`; failure classification by `isinstance` plus status (`agents/run_kit.py:162-171`) | `tests/test_openai_cache_write_cost.py`, `tests/test_cache_write_1h_pricing.py`, gateway usage mapping `tests/llm/gateway/test_ai_gateway.py:362-365,572-574`; opt-in live smoke `tests/test_llm_live_smoke.py` (never in CI) | error-text matching: `llm/providers/openai.py:178-192`, `agents/openai_provider.py:380-392`, `llm/routing.py:257-269`; the orphaned-reasoning message regex (`agents/models.py:42-46`); context-length substrings (`agents/interactive/responses_compaction.py:196-216`); in-place edit of a usage object (`llm/gateway/anthropic_chat.py:104-124`); the openai 3.x trust-store change has no test; no signature-binding test for openai (anthropic has one) |
| openai-agents | model seam `agents/models.py`; subclass-based models (`agents/fireworks.py:31`, `agents/anthropic_gateway.py:41`); runner seam `agents/run_kit.py:40-45`; tool-error wording kept by `tool_error_text` (`failures.py`), CHANGELOG [2.6.8] "A failed tool hands the model its error message through one helper" | `tests/test_tool_stream_hooks.py:58-65` calls the real SDK default so the test tracks its wording; `tests/test_function_tool_from_schema.py:55,67`; gateway runs through a real Agents SDK run (`tests/llm/gateway/test_ai_gateway.py:558-596`); the lock-pin suite; CHANGELOG [2.6.8] "The lock moves openai 3.3.0 to 3.42.0, openai-agents 0.22.3 to 0.24.0" reports 3 failures found and fixed | reads a default message string: `stream_hooks.py:22,35` (`default_tool_error_function(None, ...)` with a `None` context, a literal "An error occurred"); the SDK's terminal `incomplete` raise is mapped to `IncompleteOutputError` since 2.7.5 (L8), with `KernelModel` and a streamed Gemini cut-off left; private imports `agents.util._json._to_dump_compatible` and `Converter.items_to_messages` keyword arguments (`agents/anthropic_gateway.py:196-208`); no test pins an SDK version |
| litellm | none needed (see above); gateway field mapping `llm/gateway/anthropic_chat.py` | `tests/llm/gateway/test_ai_gateway.py`, `test_route_settings.py`; the gateway live smoke is not run (CHANGELOG [2.7.2] "Carried from 2.7.1 and not done") | usage field names come from fabricated payloads; one-hour cache writes are costed as standard (`llm/providers/anthropic_gateway.py:151`); `TODO(gateway-response-format-forced-tool)` |
| anthropic | provider seam `llm/providers/anthropic.py`; compat shim `llm/anthropic_wire.py:15-39` (1.0 dropped sampling parameters; `wire_params` moves them into `extra_body` on 1.x); optional extra | `tests/test_anthropic_wire.py:39-47` binds `inspect.signature` of the installed `messages.create`; `tests/test_anthropic_native.py`; CHANGELOG [2.6.0] "anthropic 1.x compatibility"; opt-in live smoke | CI never installs anthropic 1.x (lock 0.111.0); raw event type strings (`agents/anthropic_native.py:308-312,403,581`); every anthropic test mocks the client |
| httpx and httpx2 | the SDK builds its clients with `api_key`, `timeout`, `base_url` only and never passes `http_client=` (`llm/providers/openai.py:167`, `llm/providers/anthropic.py:61`), so openai 3.x and anthropic 1.x moving to httpx2 does not reach SDK code; `httpx` stays for the SDK's own clients (`pyproject.toml:30`); error mapping into SDK types (`clients/knowledge_hub_client.py:78-83`); the 422 check `_refuse_validation_error` (`knowledge_hub_client.py:65-71`) | `tests/clients/test_kh_refused_request_is_not_data.py` and `test_kernel_refused_request_is_not_data.py` run the real client over a mock transport (CHANGELOG [2.7.5] "A request the Hub or kernel refuses with 422 raises or fails as documented"); `tests/test_kh_client_security_context.py:34-39` binds the generated signatures | wraps `send` on the generated client (`knowledge_hub_client.py:667-684`); private `_get_kwargs` of generated endpoints (`clients/kernel_admin.py:104,221,325`); the trust-store change has no guard |
| packaging | removed the dependence: `is_pack_version` parses with `Version` instead of probing an empty `SpecifierSet`, which packaging 26 stopped rejecting (`pack/store.py:253-282`); CHANGELOG [2.7.4] "A pack version is PEP 440 when it parses, not when an empty specifier lets it through"; no floor added | `tests/pack/test_version_validity.py`, `tests/test_plato_blueprints_api.py:307-330`; effective only on packaging 26, and the lock pins 25.0, so CI would not have failed on the old code | the only detection was a local environment ahead of the lock |

### Policy

- **Floors, not caps.** `openai-agents >=0.22.0` (`pyproject.toml:126`), `anthropic >=0.69.0` optional (`:127`), `httpx >=0.27.0` (`:30`); no upper cap on those lines; the comment at `:123-125` records that the last ceiling was removed. The one exception is a git rev pin for the two generated clients (`:102,104`).
- **Lock day to day.** CI installs from `poetry.lock` (`.github/workflows/tests.yml:130,181`, poetry 2.4.1, Python 3.12). A lock bump is for a needed fix, a security advisory or a floor change; a bug found under a newer version is fixed in code so it works across the range (`note_local_versions_vs_lock_and_a_latest_run.md`, rule 3).
- **Local drift check.** `scripts/local/pre_push_check.sh` flags packages behind or ahead of the lock and names the ones that matter (packaging, openai, openai-agents, anthropic, pydantic and others); `--ci-versions` runs the suite on the lock's pins. These scripts are not in the repo.
- **Latest-run is a note, not a job.** Consumers resolve fresh against the floors and do not use our lock, so a test at lock pins can miss a newer-release defect. No CI job tests the latest resolved versions or the lowest versions; a weekly non-blocking workflow is proposed in the note and not built. Both the packaging defect and the incomplete-response gap above were found by looking ahead of the lock, not by CI.
- **Dependabot.** There is no `dependabot.yml`; alerts are handled as CHANGELOG "Dependabot:" entries that raise a floor and run a selective lock update.
- **Other guards.** `tests/test_ci_extras_coverage.py` (every extra is installed in CI or excluded with a reason), `.github/workflows/model-pricing-staleness.yml`.

### What to tell a new team

Own the thin connector where the dependency's value is small (litellm); put every upstream shape behind one seam (usage, errors, names); bind a test to the real upstream (a signature, a default message) so a change fails a test and not a customer; keep floors without caps and the lock for day to day; and run the suite ahead of the lock before a release, because the two defects this note found were visible only there. Where the SDK still reads a default message string or a private attribute (the table's last column), treat it as open work.
