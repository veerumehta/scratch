# Plan: the SDK's adjudication agent as a superset of macer's

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Plan only, no code. Source: `docs/status/macer/note_macer_vs_adjudication_agent_parity_2026-11-18.md` (the table rows are cited as T2, O5 and so on). The goal is that other use cases run the SDK agent instead of going to macer, so every macer capability either exists in the SDK or is built here. Rules for each item: improve, do not copy; no consumer names in SDK code; pack data over code; a test that fails on the old code; no provider call to build (a measuring run is a separate, typed approval).

Related earlier work, not moved: `docs/plans/plan_adjudication_evidence_scoping.md`, `docs/plans/plan_adjudication_hardening.md`, `docs/status/note_case_file_to_conditions_design_2026-11-06.md`.

## Two corrections to the parity note, found while planning

- **T2 and S4 overstated a gap.** The SDK has a calculation tool: `jazzx_sdk/tools/calculate.py` (`Calculator`, `CalculationLog` with `has_result`, `calculate_tool`), used by `pipelines/policy/code.py`. Adjudication does not give it to the model (`_evidence_tools`, `agents/adjudication/segment.py:520-526`), and has no field for extracted values. The gap is wiring and a place for the values, not a missing tool.
- **R4 overstated a gap.** `evaluation/experiment_comparison.py` compares a candidate with a baseline case by case with a measured noise floor and a McNemar test on flips (`compare_experiments`, `noise_floor_from`), and it reads cost. What it lacks is a per-rule verdict comparison over repeats.

- **C4 overstated a gap.** A pluggable guideline selector exists: `SnippetSelector` in `jazzx_sdk/agents/reasoning/grounding.py` with `HeadingsOnlySelector` (a model picks from headings alone, any failure falls back to no selection) and `TopRankedSelector`, plus a `GroundingCache` seam with an in-memory cache. What is missing is a way for a pack to choose the selector (the case step hard-wires `TopRankedSelector`, `pipelines/steps.py:1853`) and a persistent cache.

## Items

Sizes are estimated from comparable features in the CHANGELOG (learning loop L1: +341 / -11 lines, 11 files; recipes gaps R2.x: +150 to +400 lines each). A session is one working session of the runtime owner, code and tests together.

### A. Calculation and extracted values with provenance (parity T2, S4)

Two steps. **A1** is built: `evidence.calculator` (default off) gives tools mode the existing calculator and records its calls on each outcome's `inputs` under `calculations`. **A2** is the rest below. The calculator already shares the SDK's metric DSL (`jazzx_sdk/expressions`) with formula conditions and derived metrics; `finance/metrics.py` is separate float arithmetic and `pipelines/financial/spread.py` assembles spreads, so A2's declared values should name expressions in that DSL and not reach into either.

- **Design.** A rule or condition declares the values it extracts as pack data: a key, a description, optionally a unit. The verdict item gains `extracted: list[ExtractedValue]`, each with the declared key, a decimal value as text, cites (document and page, validated by the same checks as verdict cites), and the calculation steps. In tools mode the model gets `calculate_tool` (a `CalculationLog` per replica); a value that claims a calculation must equal a successful call in that log (`CalculationLog.has_result`), otherwise the validator raises a tool-required error so the retry sends the model back to the tool (the mechanism exists, `agents/run_kit.py:241-243,275-276`, and no adjudication validator uses it yet). A key outside the declared set, or a value that is not a number where a number is declared, is an ordinary validation error. In inline mode there are no tools: a value carries cites only and says so. Across replicas the value with most support stands, ties to the most complete, and the dissenting values stay in `inputs` (macer picks silently).
- **Improves on macer.** The declared set is pack data, not a code list; a calculation is checked against what ran, not against a flag that Python was invoked; dissent is recorded.
- **Placement.** New `jazzx_sdk/agents/adjudication/extraction.py` (the directory holds 14 files; this starts no cluster, it belongs to the segment's output). The declared-values field goes on the canonical condition in `fabric/canonical/policy.py` (27 files) with a lint rule in `policy_lint.py`. `tools/calculate.py` stays as it is. Tests: new files in `tests/agents/adjudication/` (2 files today), named for the area.
- **Tests.** Fail on old code: a declared value comes back on the outcome; an undeclared key is refused; a claimed calculation with no matching call sends the model to the tool (through a scripted model and the real runner, as `tests/agents/test_reasoning_trace_hooks.py` does); replicas disagree and the dissent is kept.
- **Size and sessions.** About 350 lines of code and 300 of tests; 1.5 sessions.
- **Depends on.** Nothing in the SDK. A pack schema change, so a decision on the pack contract version.
- **Spend.** None to build. Measuring extraction accuracy on a fixture needs a typed figure.

### B. Condition lifecycle beyond one run (parity O3, O5, O6)

Four parts, buildable one at a time. The SDK keeps `restates` and `resolved` in the same call and exact-identity merge today (`agents/adjudication/admissibility.py:38-79`, `segment.py:566-580`).

- **B1. Semantic dedup.** A `ConditionMatcher` seam in the admissibility pass: today's exact identity stays the default; a pack can name an embedding matcher that partitions hard by `(kind, subject_id)`, compares by cosine above a configured threshold, and asks a model only for the ambiguous band. An `Embedder` protocol goes in `llm/` beside the provider seam, with the OpenAI and gateway embedding calls behind it, so no clustering library is added. Placement: `agents/adjudication/condition_match.py` and `llm/embeddings.py` (`llm/` holds 35 files). Tests: a fake embedder, offline. About 450 + 400 lines; 2 sessions. Spend: none to build; embedding calls for a measuring run need a typed figure (small).
- **B2. An evidence-searching resolver.** For each open condition on a rerun, one call with the evidence tools reads the new documents and answers a closed schema: the condition id, resolved or not, cites, a note. It resolves only on evidence, never on absence. It reuses the segment's cite validators and tool setup. Placement: `agents/adjudication/resolver.py`, switched on by a spec field. About 500 + 400 lines; 2 sessions. Depends on A only for shared validators. Spend: typed, for any run.
- **B3. Conditions made by a person.** A condition's origin (`model` or `reviewer`) is recorded on `OutcomeCondition`, and the resolver takes a variant for a reviewer-made one. Needs a decision first: where a reviewer's condition enters (the feedback surface). About 200 + 200 lines; 1 session after the decision; depends on B2.
- **B4. Support and dispute per condition, as data.** From the votes already computed, record per condition which replicas raised it and which did not (`_vote_tally` in `segment.py:615-624`), and derive `contested` and `unopposed` in code; no summarizer call and no nine-label vocabulary. Only meaningful with `replicas` above 1 (the default is 1, spec `replicas`). About 250 + 250 lines; 1 session.
- **Improves on macer.** No second model call to reconcile replicas; the labels are counts a reviewer can check; the matcher is pluggable.

### C. Verdict-level regression comparison (parity R4)

- **Design.** A pure function over two sets of repeated adjudication outputs: per rule, the baseline's modal verdict and its share, the candidate's share of that verdict, and a classification (`same`, `possible`, `changed`) by a shift threshold and a minimum repeat count, both named constants set in config; a cost-ratio warning from the cost the experiment already stores. A pack-declared forbidden-pattern check (a leak check) reads the output text and is a scorer, not code that knows which values to hide. Reported through the existing comparison export so it sits beside `compare_experiments`.
- **Improves on macer.** It runs beside ground-truth scoring and the noise floor instead of alone ("same as main is not correct").
- **Placement.** New `jazzx_sdk/evaluation/adjudication_regression.py` (88 files in `evaluation/`; it joins the `adjudication_scorers.py` cluster). Tests in a new `tests/evaluation/` (the area has none today; eval tests sit flat in `tests/`, say so in the commit).
- **Tests.** Fail on old code: a rule whose modal verdict moves across repeats is `changed`; fewer repeats than the minimum is `possible`; a cost ratio over the threshold warns.
- **Size and sessions.** About 300 + 300 lines; 1 session.
- **Depends on.** Nothing. **Spend.** None to build; a baseline needs repeated runs (macer's smoke suite states 15 to 20 USD and 20 to 40 minutes for three repeats of one case), typed.

### D. A shipped applicability planner (parity C3)

- **Design.** A built-in planner behind the existing seam (`SegmentPlanner`, `agents/adjudication/planner.py:58-86`, default off and fail closed): one call with the evidence tools reads the case and answers with the applicable rule ids as a closed enum built from the catalog, so an unknown id cannot be written; a second short call fills the reason for each skip. Rule descriptions come from pack data. A rule skipped on a first run is recorded as not applicable with the reason; a rerun skip leaves the earlier verdict.
- **Placement.** `agents/adjudication/planner_agent.py`, registered through `register_installed`, with its prompt under `prompts/files/adjudication/`.
- **Tests.** Fail on old code: the enum refuses an unknown id; a planner failure falls back to the full catalog; a skip carries its reason. Scripted model, offline.
- **Size and sessions.** About 350 + 350 lines; 1.5 sessions. **Depends on.** The output controls (committed in 2.7.5). **Spend.** Typed, to measure applicability accuracy against running every rule.

### E. A subject enum in the schema (parity S6)

Built: `_scoped_verdict(tokens)` in `agents/adjudication/segment.py` limits a condition's subject to the roster tokens or empty, cached by the token set; tests in `tests/agents/adjudication/test_adjudication_subject_enum.py`.

### F. A guideline-selection step a pack chooses, and search results retrievable in full (parity C4, T10)

- **F1. Selector as pack data.** The selector seam and an LLM selector exist (`SnippetSelector`, `HeadingsOnlySelector`, `GroundingCache`). The change: `EvidenceSpec.grounding` names the selector (`top_ranked`, the default, or `headings`) and the cache, so a pack picks it without code; a failed selection already falls back to no selection. A persistent `GroundingCache` (the in-memory one is process-local) is a pack-supplied implementation of the same two methods; the SDK ships none. Placement: `agents/adjudication/spec.py` and `pipelines/steps.py:1843-1858`; `agents/reasoning/` holds 3 files and is unchanged. Tests, failing on old code: a spec naming `headings` reaches `PrecomputedGrounding` with that selector (scripted model); an unknown name is refused; the default is unchanged. About 80 + 100 lines; half a session. Depends on nothing. Spend: none to build; measuring whether a model-picked selection beats top-ranked on a fixture needs a typed figure.
- **F2. A capped search result that can be read in full.** Today a result over `SEARCH_RESULT_MAX_LINES` (200) is cut with "narrow the pattern" and the rest is lost (`agents/adjudication/segment.py:517-531`, through `build_source_tools(compress_search_output=)`). The change: a per-run holder keeps the full output under an id, the cut result ends with that id, and a `read_reference(ref)` tool returns the full text (an unknown id says so, as text). No compression library: the cap and the retrieval are the whole feature, and a pack can still pass its own compressor through the existing hook. The holder is scoped to the run (a context variable set around the segment, as `_CITE_CHECKS` is), not process-wide. Placement: `tools/agent/dir_tools.py` (5 files in `tools/agent/`), the cap function in `segment.py`; tests in `tests/tools/` (new file, the directory now exists). Tests, failing on old code: a search over the cap returns the first lines and an id; `read_reference` returns all lines; an id from another run is refused; the tool goes through the real SDK entry point. About 150 + 150 lines; 1 session. Depends on nothing. Spend: none.

### G. Session size and read-tool hygiene defaults (parity L10, C7)

- **G1. The input filter on by default.** `InputFilter` exists and is stronger than macer's (it stubs the oldest tool outputs first, then drops the oldest reasoning groups; `agents/run_kit.py:476`), but `max_session_size_kb` defaults to 0 (off, `run_kit.py:656`). The change: the default comes from config as a named constant with an environment override, and 0 still turns it off; the adjudication call passes it. Choosing the number needs a measurement of real session sizes (macer uses 750 KB; that is a starting value to test, not a finding). The filter only acts above the limit, so a short session is untouched. Placement: `agents/run_kit.py` and `config/envvars.py` usage as `JAPES_CALL_DEADLINE_SECONDS` does; tests in `tests/` beside `test_agents_run_kit.py`. Tests, failing on old code: a session over the default is shrunk and its user items stay; 0 is a pass-through; the environment value wins. About 60 + 80 lines; half a session. Depends on a decision on the default. Spend: none to build.
- **G2. A rendered-prompt snapshot test (built: `tests/agents/adjudication/test_adjudication_prompt_snapshots.py`).** The prompts are versioned files composed with provenance, but nothing pins the text a segment sends. The change: a test renders `_render_batch_prompt` and the composed instructions for a fixed rule set (inline and tools mode, with and without a roster, with a rerun focus) and compares them with checked-in files, so a prompt change shows in review as a diff. Placement: `tests/agents/adjudication/` (a snapshot folder beside it, as `tests/` already has `test_loop_snapshot.py`). Tests: the snapshot test is the test; it must fail when a prompt line changes. About 60 lines plus the snapshot files; half a session. Depends on nothing. Spend: none.

## Not in this plan

Smaller absorbs from the parity note, each its own change: a browse gate wired into adjudication (T9); the rerun ledger of documents considered per section (C5); metering a truncated attempt's usage is not possible from the SDK error (recorded as an incomplete call instead); `KernelModel` marks no truncation (not checked whether the kernel response has a finish reason); segment concurrency as a spec field (R3).

## Which can be built offline now, and where they fit

Every item builds offline with no provider call; spend appears only when a measuring run is wanted. What differs is whether a change alters what the model sees, so it needs a measurement first, or touches a pack contract.

| Item | Changes model-visible behavior | Pack contract | Fits |
|---|---|---|---|
| E | no (built) | no | 2.7.5, done |
| A1 calculation wired in, default off | only when a spec turns it on | no (an `EvidenceSpec` flag) | 2.7.5, built |
| A2 extracted values | yes | yes (declared values on a condition) | 2.8 |
| Served-tier costing, phase 2 (read the tier the response names on the agent-tier path by wrapping the SDK client, price by it, mark an unconfirmed tier; Anthropic `usage.service_tier`, Gemini `traffic_type`) | no | no | early 2.7.x, first with `std` stages 1 and 2 |
| `std` stages 1 and 2 (the registry; the DSL resolves through it; `docs/status/computation/note_shared_function_library_design_2026-11-18.md`) | no | no | early 2.7.x, first |
| C regression comparison | no | no | early 2.7.x |
| D applicability planner | yes, when a pack opts in | no | 2.8 (value shows only when measured) |
| B1 semantic dedup | yes | no | 2.8 (needs an embedding seam in `llm/`) |
| B2, B3 resolvers | yes | B3 yes | 2.8 |
| B4 support and dispute | no (computed from votes) | no | early 2.7.x, useful only with `replicas` above 1 |
| F1 selector as pack data | no by default | no | early 2.7.x |
| F2 capped search retrievable | yes (the model can fetch the rest) | no | early 2.7.x |
| G1 input filter default | yes for long sessions only | no | early 2.7.x, after choosing the default |
| G2 prompt snapshot test | no | no | 2.7.5, built (tests only) |

**Recommendation on A (calculation wired into adjudication).** Split it. **A1** gives the segment's tools-mode tool list the existing `calculate_tool` behind `EvidenceSpec.calculator`, default off, and records the `CalculationLog` calls on each outcome's `inputs` so a reviewer sees what the model computed. It adds no field to the answer, no pack contract change and no behavior change unless a spec turns it on; about 80 + 100 lines, half a session, and it fits 2.7.5. **A2** (declared extracted values, the validator that a claimed calculation matches a call, replica dissent) changes the answer schema and the pack, so it waits for 2.8 and for a decision on the pack contract version. Doing A1 now also makes the 2.8 work measurable: a spec that turns the calculator on can be compared with one that does not.
