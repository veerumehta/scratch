# Plan: the SDK's adjudication agent as a superset of macer's

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Plan only, no code. Source: `docs/status/macer/note_macer_vs_adjudication_agent_parity_2026-11-18.md` (the table rows are cited as T2, O5 and so on). The goal is that other use cases run the SDK agent instead of going to macer, so every macer capability either exists in the SDK or is built here. Rules for each item: improve, do not copy; no consumer names in SDK code; pack data over code; a test that fails on the old code; no provider call to build (a measuring run is a separate, typed approval).

Related earlier work, not moved: `docs/plans/plan_adjudication_evidence_scoping.md`, `docs/plans/plan_adjudication_hardening.md`, `docs/status/note_case_file_to_conditions_design_2026-11-06.md`.

## Two corrections to the parity note, found while planning

- **T2 and S4 overstated a gap.** The SDK has a calculation tool: `jazzx_sdk/tools/calculate.py` (`Calculator`, `CalculationLog` with `has_result`, `calculate_tool`), used by `pipelines/policy/code.py`. Adjudication does not give it to the model (`_evidence_tools`, `agents/adjudication/segment.py:520-526`), and has no field for extracted values. The gap is wiring and a place for the values, not a missing tool.
- **R4 overstated a gap.** `evaluation/experiment_comparison.py` compares a candidate with a baseline case by case with a measured noise floor and a McNemar test on flips (`compare_experiments`, `noise_floor_from`), and it reads cost. What it lacks is a per-rule verdict comparison over repeats.

## Items

Sizes are estimated from comparable features in the CHANGELOG (learning loop L1: +341 / -11 lines, 11 files; recipes gaps R2.x: +150 to +400 lines each). A session is one working session of the runtime owner, code and tests together.

### A. Calculation and extracted values with provenance (parity T2, S4)

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

- **Design.** When a roster of subject tokens is present, `_BatchCondition.subject` becomes a `Literal` of the tokens through a cached `create_model` keyed by the token set, so the schema is byte-identical across turns (prompt-cache routing) and the model cannot write a wrong token. The validator stays as the backstop for an empty roster and for a prior condition's token.
- **Placement.** `agents/adjudication/segment.py` plus a small helper beside it; tests in `tests/agents/adjudication/`.
- **Tests.** Fail on old code: the built schema lists exactly the tokens; two builds for the same set return the same schema object; a strict schema build still passes (the pattern of the macer schema tests, `tests/test_agent_output_schemas.py` on the macer branch).
- **Size and sessions.** About 120 + 120 lines; half a session. **Depends on.** Nothing. **Spend.** None.

## Not in this plan

Smaller absorbs from the parity note, each its own change: a browse gate wired into adjudication (T9); a retrieval handle for a capped search result (T10); the input filter on by default (L10); a rendered-prompt snapshot test (C7); the rerun ledger of documents considered per section (C5); a guideline-selection step (C4); Gemini truncation (`agents/gemini_native.py` reads a `MAX_TOKENS` finish as completed); metering the usage of a truncated OpenAI attempt; segment concurrency as a spec field (R3).

## Recommendation

- **Fits 2.7.5:** E only. It is small, offline, no spend and no pack contract change. 2.7.5 already carries four parity commits and the squash is waiting; adding more than E delays it.
- **2.8:** A first (it unblocks the metric half of any macer-like result), then C (cheap and it makes every later change measurable), D, B1, B4, then B2 and B3 (B3 waits on the feedback-surface decision).
- **Typed spend, all in 2.8:** the measuring runs for A, B1, B2, C's baseline and D. Nothing here needs spend to build.
- **Order of evidence.** Before A, B2 or D, decide with the user whether a before and after on one fixed case set is wanted, since each of them changes what the model sees or does.
