# plan_JAPES_NOV10_ROADMAP_ENABLERS

Author: Virendra Mehta · 2026-11-10 · Status: not started

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-10 drafted from the Nov 10 platform update deck (SharePoint, "JazzX Platform vNext Update Nov 10 - DRAFT") and a read of `main` (SDK 2.7.0, Plato 0.3.0). The deck's SDK slides came from our own deck and are not covered here. This plan covers what the other slides ask of the platform and what the SDK can build so those items run on it.

## Goal

The Nov 10 deck lays out four roadmaps that sit outside the SDK slides:

1. Training a reasoner with SFT and then RL (slides 4 to 16).
2. The platform roadmap: BAF, runtime, knowledge representation, coworker framework, extensibility and infra layers (slide 39).
3. The learning architecture (slides 43 and 44).
4. A learning roadmap with four rows (slide 45): in-context feedback, feedback for reasoners, the Context Engineering Loop (CEL), and evaluation and governance.

This plan turns the parts the SDK can carry into slices. Model training itself, staffing and model serving infrastructure are not SDK work. Data, rubrics, rollouts, attribution, experiments and governed release are SDK work.

## Before starting

Verify in this order:

1. The latest CHANGELOG entries.
2. This plan.
3. `plan_JAPES_LEARNING_LOOP_CLOSE.md` (L1 to L6: guidance in ACER and case runs, corrections become signals, scheduled draft sweep, uplift in the release report, `feedback_to_improvements`, Plato review page).
4. `plan_JAPES_2_7_1_KNOWLEDGE_LOOP_CHANGE_CLASSES.md` (change classes, gates, forum approval, proposal records).
5. The source.

Nothing here repeats those two plans. Where a slice needs one of their pieces, it names it and builds on it.

## What the deck asks for, and what exists on main

| Deck item | Where in the deck | What exists in the SDK (2.7.0) |
|---|---|---|
| Training data: obfuscation, masked sensitive fields, normalized schema, JSONL export; gate on privacy and schema checks | RL milestone 1 (slide 15) | `tools/retention.py` `RetentionPolicy` (zero data retention per tool, fail-safe on replay), `failures.redact_secrets`, `redact_fields`. Canonical `TraceStep`/`ToolCall` keep digests only, never raw inputs or outputs. No training-trace export. |
| A rubric per loan: weighted yes/no checks, named penalties, each independently gradeable; used for evaluation and as the RL reward | slides 8 and 45 | `evaluation/agent_judge.py` (`AgentJudgeScorer`, `judge_with_rubric_tool`, free-text rubric), `custom_scorers.py`, `CachedJudge` with a spend ceiling. No rubric as data with weights and penalties. |
| Several rollouts per case, scored, compared with the group average | slides 6, 7, 13 | ACER replicas collapse by vote; `evaluation/stability.py`, `variants.py`, `experiments.py`. No rollout group with rubric scores and advantages. |
| SFT model benchmarked against current models; validation split held out | slide 15 | `silver.py` (frozen reference, train, validation and holdout manifests), `experiment_comparison.py`, `VersionBundle.model_versions` per role. |
| Feedback at the condition, attributed to a JTBD, grouped by topic (DTI, self-employed income) | slide 45, reasoner row | `evaluation/feedback/corrections.py` (a reviewer's correction of one rule's answer on a case run), feedback API (similar, aggregate, duplicates, review). Curator buckets by a closed tag set. |
| Learning run: grouped feedback drafts a policy directive change; before and after on the feedback loans and the golden set; ships as a new policy version with rollback after an SME confirms | slide 45, reasoner row | Policy to Pack proposals and `decide_proposal`; release report on gold cases; pack versions with rollback in Plato. Nothing that drafts a JTBD change from grouped feedback. |
| Per-condition scoring: resolved, unchanged, changed but not resolved | slide 45, evaluation row | Release report and `guidance_ab.run_ab_comparison` give newly passing, newly failing and unchanged. No "changed but not resolved". |
| Before and after test per feedback item, with rewordings and scope checks | slide 45, in-context row | `guidance_ab.validate_guidance` (before and after on the same cases, over-firing shows as regressions). No rewordings or out-of-scope probes. |
| Scope per feedback (lender, program, borrower type) with a review date | slide 45, in-context row | `GuidanceAsset.applicability` (pack-defined dimensions), expiry, overlap check in `lifecycle.py`. Not verified: a review date distinct from expiry. |
| Implicit signals: retries, undo, overrides, abandonment, verified completion; hold back low-quality signals | slides 44 and 45 | `FeedbackSource` is `user`, `system`, `judge`; `feedback/quality.py` scores usefulness with a model. No implicit signal kinds. |
| Attribution agent: explain one run and name the likely faulty component (rule or overlay, extraction, classification, model), with evidence for and against | slides 44 and 45, CEL row | `evaluation/attribution_protocols.py`: `EvidenceProvider` and `AttributionAnalyzer` protocols. No concrete provider or analyzer ships. |
| Cohort analyzer drafts hypotheses; SME picks experiments within a budget; experiment learner tests a change on saved cases | slide 45, CEL row | `optimization_jobs.py` (`OptimizationRunner`, `FixLedger`), `ExperimentRunner`, `pass_bars.py`. No cohort analysis or hypothesis records. |
| Learning memory: sessions, learnings and failed attempts logged for the next run | slide 44 | `compounding.py` metrics (provided ahead of demand). No record of attempted and failed changes. |
| Replay a Decision from its Trace; recorded Outcomes per loan; versioned policies | slide 39, BAF row | Governed record (pending QA), `VersionBundle` on runs and decisions, `Outcome.reviewer_answer`. Not verified: a replay entry point. |
| External agent frameworks (LangChain) under the same traces, feedback and approvals | slide 39, extensibility row | Azure isolated containers (extension runtime), queue jobs. Nothing in `jazzx_sdk` imports LangChain. |
| Ontology builder as configuration; reuse a customer's existing ontology | slide 39, knowledge representation row | Pack ontology and catalog, Documents to Vocabulary, `plan_ontology_source.md`, `plan_pack_ontology_authoring.md`. Not verified: importing OWL, RDF or JSON-LD. |
| Declare a coworker: process, agents, tools, integrations; route to sub-agents through a skill catalog; feedback and reflection in chat | slide 39, coworker row | Unified Assistant Framework (in progress), skill routing in the interactive agent, process launcher (2.7.0). |
| Per-step cost and latency for every run; model routing; SRMs behind the gateway | slide 39, infra row | `TokenUsage`, `ToolCall.cost_amount` and `latency_ms`, metering per call. Not verified: a per-run cost and latency report, or a custom model endpoint per agent role. |

## Slices

### Track A. Data and rewards for SFT and RL

The RL plan waits on staffing. The SDK can have its inputs ready so milestone 1 starts on a working exporter.

#### A1. Rubric as pack data, and a rubric scorer

- **Model.** Add `evaluation/rubric.py`:
  - `Rubric` (id, version, case or case-type key, criteria).
  - `RubricCriterion`, with:
    - `id` and `text`
    - `points`, positive or negative; a negative value is a named penalty
    - `kind`: `fact`, `citation`, `judgment` or `penalty`
    - an optional deterministic check: field, operator, value, tolerance
    - `cites`: the documents or policy refs the criterion expects
- **Storage.** Rubrics live in the pack under `rubrics/`, keyed by case id or by case type. Load them with the pack and lint them:
  - every criterion must be yes or no
  - every penalty must name the error it penalizes
  - weights must sum to a stated maximum
- **Scorer.** `RubricScorer` grades each criterion on its own:
  - It runs the deterministic check when one is given.
  - Otherwise it asks the `ReasoningAgent` a yes or no question with the evidence. A `CachedJudge` with its spend ceiling may stand in.
  - It returns per-criterion results with reasons, a raw total and a normalized score.
  - An undecided criterion is reported as such, never scored as 0.
- **Integration.** Register the scorer in the scorer catalog so experiments, the release report and A3 can all use it.
- **Intent.** One rubric serves evaluation now and becomes the RL reward later, as slide 45's evaluation row asks.
- **Acceptance:**
  - The two worked examples on slide 8 (assets to close, income qualification) load as rubrics in a test pack.
  - A trace that states the right figures and cites the right documents scores the positive points.
  - A trace that clears income despite a VOE end date takes the -50 penalty.
  - The lint rejects a criterion with no yes or no form.

#### A2. Training-trace export with obfuscation

- **Capture (opt-in).** Add a transcript capture for agent runs (`ReasoningAgent`, ACER segments, interactive turns). It keeps the full model-visible sequence: system, user, assistant reasoning and messages, tool calls and tool results.
  - Canonical traces hold digests only, so this is a separate, opt-in record.
  - It is written through `RetentionPolicy`, so a zero-retention tool's payloads never reach it, including on replay.
- **Export.** `export_training_traces(run_ids, *, obfuscation, mask)` writes JSONL. Each record carries:
  - the messages, with a per-message `train` flag (model-generated true; system, user and tool results false)
  - the `VersionBundle`
  - case and rule ids
  - the rubric score from A1 when one exists
- **Obfuscation.** A pack-declared obfuscation map lists fields and patterns:
  - names, SSNs, account numbers, addresses, employer names
  - a consistent pseudonym per value within one trace and across one export, so reasoning that compares two documents still reads
  - amounts and dates left alone unless the map says otherwise
- **Gate.** Before any file is written, check privacy and schema:
  - no value from the map survives
  - no zero-retention payload is present
  - every record validates against the schema
  - A failed check writes nothing and reports the offending record ids.
- **Intent.** RL milestone 1's deliverable ("safe, consistent training traces") as an SDK function, with its gate built in.
- **Acceptance:**
  - A test run with a synthetic borrower exports a JSONL whose records validate.
  - The same name maps to the same pseudonym everywhere in one export.
  - A planted SSN fails the gate.
  - A zero-retention tool's output is absent.
  - Context messages carry `train: false`.

#### A3. Rollout groups scored by rubric

- **Function.** `run_rollouts(case_ids, agent_spec, *, n, model, rubric_source, budget)` runs each case `n` times with one named model and the same tools and evidence the agent uses at run time.
  - Each trace is scored with A1.
  - The function computes each group's mean and each trace's advantage (score minus group mean).
  - It writes rollout groups as JSONL through A2's exporter and gate.
- **Reuse.** Build on the experiment runner and ACER's replica machinery rather than a new loop. Record cost per rollout.
- **Spend.** The budget is a hard stop. Every model-backed run needs the user's typed approval with a dollar figure in the session that runs it.
- **Intent.** The data a GRPO-style trainer consumes, produced by our own agents on our own cases. Training stays outside the SDK.
- **Acceptance:**
  - On a test case with a fake model returning four fixed traces scored 82, 78, 61 and 59, the group mean is 70 and the advantages are +12, +8, -9 and -11.
  - A group whose traces all score the same is flagged as carrying no signal.
  - The budget stops a run cleanly.

#### A4. A trained model as a choice per agent role

- **Config.** Let an agent spec or pack execution profile name the model per role, including a fine-tuned model served behind the LLM gateway. `VersionBundle.model_versions` already records it.
- **Comparison.** Compare a candidate model against the current one with the existing experiment comparison on the `silver.py` holdout manifest, scored with A1.
- **Intent.** "Benchmark against current models" and "validated SFT winner selected" (milestone 2) on the same harness as everything else.
- **Acceptance:** an experiment comparing two models on a frozen holdout reports per-case deltas and refuses a reference whose digest changed.
- **Not verified:** whether the gateway client accepts a custom endpoint per role today.

### Track B. Feedback that changes the reasoning

Slide 45's second row. L2 in the learning-loop plan makes corrections into signals; this track takes them to a policy change.

#### B1. Feedback at the condition

- **Fields.** Extend the correction record (`feedback/corrections.py`) and `Feedback` with:
  - target refs: case, rule or JTBD id, condition id
  - the reviewer's "what should have happened"
  - a topic
- **Topics.** Topics come from a pack-defined list (for example DTI, self-employed income, assets), not the Curator's closed signal tags.
- **Acceptance:** a correction on one ACER condition stores its JTBD id and topic, and the feedback API filters and aggregates by both.

#### B2. Group by JTBD and topic

- Let the Curator route by JTBD and topic as well as by tag, so a bucket holds every correction on one directive.
- **Acceptance:** five corrections on two JTBDs land in two buckets, with counts and the cases they came from.

#### B3. Learning run: from grouped feedback to a policy change

- **Pipeline.** Add a Conductor pipeline `feedback_to_policy_change`. Steps:
  1. Read a bucket.
  2. Draft a change to the JTBD, its checks or its generated code. This is a proposal through the Policy to Pack proposal records, never a direct edit.
  3. Regenerate code for the changed job.
  4. Run before and after on the bucket's cases and on the pack's golden set.
  5. Pause for review.
  6. On approval, publish a new pack version with a rollback point.
- **Intent.** The SDK form of "a model drafts the policy directive change from the grouped feedback".
- **Acceptance:**
  - On a test pack, a bucket of corrections about a threshold produces one proposal.
  - The before and after shows the bucket's cases fixed and no golden case broken.
  - Nothing changes until approval.
  - Rollback restores the earlier version.

#### B4. Per-condition outcome classes

- Add "changed but not resolved" to the release report and `guidance_ab` results, next to resolved (newly passing), regressed and unchanged.
- Report resolution rate and time from feedback to live.
- **Acceptance:** a case whose verdict changed but still disagrees with the expected answer is reported as changed but not resolved, not as unchanged or resolved.

### Track C. In-context learning, governed

Slide 45's first row. L1 and L4 of the learning-loop plan put guidance into case runs and measure it; this track adds the governance the row lists.

#### C1. Rewordings and scope probes in the before and after

- **Inputs.** `validate_guidance` takes, for each guidance item:
  - generated rewordings of the queries it was made from
  - probes just outside its applicability (another lender, another program)
- **Pass condition.** It passes only if:
  - the rewordings improve
  - the probes are unchanged
  - nothing regresses
- **Spend.** Rewording generation counts against the run budget.
- **Acceptance:** an item scoped to one lender that changes another lender's answer fails on the probe.

#### C2. Review date and retrieval misses

- **Review date.** Give `GuidanceAsset` a review date, separate from expiry. Past it, the item is still served but listed for review.
- **Retrieval misses.** When guidance retrieval fails, the turn still answers; check this holds and log the miss with the pack, the query and the reason.
- **Acceptance:** an item past its review date appears in the review list and is still injected; a forced store failure produces an answer and one logged miss.

#### C3. Implicit signals, with a hold-back bar

- **Kinds.** Add implicit feedback kinds: retry, undo, override, abandonment, verified completion.
  - A caller reports them with run and turn ids; they carry no free text.
- **Bar.** The Curator counts them toward a bucket only past a configurable bar (count and share of runs).
- **Quality.** `feedback/quality.py` is not called on them.
- **Acceptance:**
  - Three overrides on one rule stay below a bar of five and draft nothing.
  - Six cross it and route.
  - Verified completions count as positive evidence for deployed guidance in `compounding.guidance_effectiveness`.

### Track D. Context Engineering Loop

Slide 45's third row and slide 44. It builds on the attribution seam that already exists.

#### D1. The first attribution analyzer and evidence providers

- **Providers.** Implement `EvidenceProvider`s over what the SDK already records:
  - the governed record (decision, evidence, trace)
  - document processing run metrics and refusals
  - code-versus-model routing in Case to Verdicts
  - the rule and its overlays
- **Analyzer.** Implement an `AttributionAnalyzer` on the `ReasoningAgent` that, for one run with an expected answer:
  - names the likely component (rule or overlay, extraction, classification, model)
  - gives evidence for and against, with alternatives
  - proposes a fix and the test that would show it
- **Records.** Use the `jazzx_eval_contracts` attribution records. A provider that cannot reach its source records that, never "no issue".
- **Acceptance:**
  - Three planted faults are each attributed to the right component, with the evidence cited: a wrong threshold in a rule, a missed field in extraction, a misclassified document.
  - An unreachable source shows as unavailable.

#### D2. Cohort analysis to hypotheses

- **Function.** `analyze_cohorts(run_ids, by=...)` compares runs grouped by rule, document type, program or model version.
- **Hypotheses.** It drafts hypotheses only where a cohort differs from the rest beyond a stated bar. Each hypothesis is a record with:
  - evidence
  - the D1 attribution for sample runs
  - a proposed change
  - the cases to test it on
  - an estimated cost
- **Intent.** The analyzer that "compares cohorts across runs and drafts hypotheses and experiments with evidence".
- **Acceptance:** on a synthetic history where one program fails one rule twice as often, one hypothesis names that rule and program; a history with no real difference produces none.

#### D3. Bounded experiments an SME starts

- **Run.** An SME selects hypotheses and sets a budget. Each runs as an experiment on saved cases through the existing runner and `OptimizationRunner`.
- **Report.** Accuracy, regressions, cost and latency, plus B4's outcome classes.
- **End state.** The run ends paused for approval of the exact version, with a rollback point. Approval follows the change classes in the 2.7.1 plan.
- **Acceptance:** the budget stops a run with partial results kept; an approved change ships as one pack version; a rejected one changes nothing.

#### D4. Learning memory

- **Record.** Keep every attempt: hypothesis, change, result, approver or rejection, and why. Hypothesis drafting (D2) reads it, so a change that failed on the same cohort is not proposed again unless the evidence changed.
- **Reporting.** Feed `compounding.py` so the compounding metrics run on real history.
- **Acceptance:** a rejected change on one rule and cohort is not re-proposed on the next run over the same data, and is re-proposed after new corrections arrive.

### Track E. Platform roadmap items the SDK can carry

From slide 39. Each is smaller here because the other plans already hold most of the work.

#### E1. Replay a decision from its trace

- **Function.** `replay_decision(decision_id, *, pin="recorded" | "current")`:
  - reruns the decision with the recorded `VersionBundle` (pack, prompts, models, overlay) and the recorded evidence ids
  - compares the result with the recorded decision
  - writes the replay as its own trace linked to the original
- **Acceptance:**
  - With everything pinned, the replay matches on a deterministic test.
  - With the current pack, a changed rule shows as a difference naming the rule.
- **Not verified:** whether evidence is retrievable by id for every run kind.

#### E2. External agent frameworks under governance

- **Adapter.** A thin adapter that runs a LangChain agent (in-process, or in the extension container) and, for each run:
  - emits a canonical trace
  - accepts feedback through the feedback API
  - applies deployed guidance through a prompt hook
  - goes through the same approvals for guidance and pack changes
- **First target.** The agents the SymphonyAI financial services and RhythmX teams already run.
- **Acceptance:** a sample LangChain agent's run appears with steps, model and cost in the same trace format, accepts a thumbs-down, and picks up a deployed guidance item.
- **Decision for the user:** in-process or extension container first.

#### E3. Import a customer's ontology

- Read OWL, RDF or JSON-LD into a pack catalog as proposals through the same review as Documents to Vocabulary, with a mapping report: matched, new, conflicting.
- Ties to the k9 conversion in `plan_ontology_source.md`; do that one first if it has not landed.
- **Acceptance:** a small OWL file with ten classes imports as ten proposals; accepted ones appear in the next catalog version.

#### E4. Coworker declaration

- **Manifest.** Extend the assistant manifest (Unified Assistant Framework) to declare:
  - the processes it may start (2.7.0 launcher)
  - the sub-agents it routes to through the skill catalog
  - its tools and integrations
  - a feedback and reflection handler on each turn that writes C3 implicit signals
- **Acceptance:** a manifest with one process and two sub-agents loads, routes a question to the right sub-agent, starts the process after user approval, and records an implicit retry.

#### E5. Per-run cost and latency

- A run report that sums `TokenUsage`, `cost_amount` and `latency_ms` by step and by model for pipelines, ACER and interactive turns, served by Plato and plato-client `cost_stats`.
- **Acceptance:** one Case to Verdicts run reports cost and latency per segment and per model, and totals match the metered calls.

#### E6. Link directives into the knowledge graph

- Add JTBD and rule nodes to the case graph, linked to the catalog concepts they read and to the case facts they were judged on.
- Then one query answers "which directives touched this fact, and what did they decide".
- Builds on the case graph and catalog `reads` that already exist.
- **Acceptance:** for one Acra case, the graph links a loan-amount fact to LPE-LOAN-AMT-STD and its verdict, and the link survives a pack version change as a versioned edge.

## The SDK and managed runtime roadmap slide (slide 39), reconciled

Their phases (Today, POCs on the SDK, first SDK solutions in production, SAI Group and partners on the runtime) are not ours (Today, Consolidate, Share, Host optional). Their "Supported today" means functional; ours separates in production, QA done and pending QA. The rows below compare substance, not phase labels.

| Row | Item on the slide | Where we stand | In sync? | Gap and how it is filled, or why not |
|---|---|---|---|---|
| BAF | Five objects implemented; each Decision links its Evidence and Trace (Today) | Built in the SDK as the governed record, pending QA | Yes, but the status differs | Show it as pending QA, not as a supported baseline. |
| BAF | SDK APIs to create, read and link the objects (Phase 1) | Built (canonical store puts and reads, recorder chain), pending QA | Yes, and earlier than shown | None. |
| BAF | DSCR and servicing (loss mitigation) POCs on the objects (Phase 1) | Acra DSCR uses some of the SDK, not in production; no servicing pack in the SDK | Partly | Loss mitigation is not in any SDK plan. It needs an owner and a pack before it can run on the SDK. |
| BAF | Versioned policies, recorded Outcomes per loan, replay a Decision from its Trace (Phase 2) | Pack versions and Outcomes built, pending QA; no replay | Partly | E1. |
| Runtime | "Orchestration via Plato, an obfuscated runtime that protects JazzX IP" | Plato is the Container: it hosts the SDK behind an API. Orchestration is Conductor and Flowable. IP is protected because our code stays with us and callers use an API. | No, on three counts | Use "Container", not "runtime". Do not describe Plato as orchestration. Name API-only access as the IP protection. |
| Runtime | JTBDs created via the SDK run on Plato; output aligned with mortgage (Today) | Policy to Pack runs in Plato, pending QA; Plato in QA | Yes | None. |
| Runtime | Policy to executable Python; scored against the same SME ground truth (Phase 1) | Built, pending QA; measurement planned (`plan_revolution_codec_vs_sdk_comparison.md`, measurement plan M2) | Yes | None beyond those plans. |
| Runtime | Obfuscated build for customer deployments (Phase 2) | Not planned. It contradicts "our code stays with us; they use an API". | No | Needs a decision: an obfuscated build only matters if we install in a customer's environment. If that is a real requirement, it is a packaging and licensing project for Plato, not an SDK feature. Otherwise drop it from the slide. |
| Runtime | SDK at GA level; integrated with Builder and Knowledge Studio (Phase 2) | Knowledge Studio uses a small SDK subset; Policy to Code in Knowledge Studio is our Share phase; Builder Studio publishes to Plato | Yes | None. |
| Runtime | Reasoner and coworkers exposed as APIs (Phase 3) | Plato already exposes assistants, skills, case runs and processes through its API and plato-client, pending QA | Yes, but much earlier than shown | Move it to Phase 1 or Today (pending QA). |
| Knowledge representation | Basic POC: early ontology generation (Today) | The SDK has ontology discovery and extension and a case graph, both built and pending QA; k9 generates ontologies | Understated | Show the SDK capability as built, pending QA. |
| Knowledge representation | Loss mitigation ontology; dynamic generation and maintenance (Phase 1) | Documents to Vocabulary does generation and maintenance | Partly | The loss mitigation ontology needs a corpus and an owner; the SDK side is ready. |
| Knowledge representation | Ontology builder as configuration; reuse a customer ontology (Phase 2) | Pack catalog and ontology are configuration; no import | Partly | E3. |
| Knowledge representation | Loan facts, documents and directives linked in one graph (Phase 3) | Facts and documents are linked in the case graph; directives are not | Partly | E6. |
| Coworker framework | Coworkers built per application; Jazz Q&A (Today) | Jazz Assistant runs on the SDK's interactive agent in production | Yes | Say Jazz Assistant is on the SDK. |
| Coworker framework | Routing by skill catalog; feedback and reflection in chat (Phase 1) | Skill routing built; feedback API built; reflection handler not built | Partly | E4 (feedback and reflection handler writing implicit signals). |
| Coworker framework | Declare a coworker: process, agents, tools, integrations; screens from UX templates in Builder Studio (Phase 2) | Unified Assistant Framework in progress; processes launchable since 2.7.0 | Yes | E4 for the declaration. Screens are Builder Studio's. |
| Coworker framework | Any application and channel; voice, images, video (Phase 3) | Images handled by the document agent; voice and video not | Partly | Not planned in the SDK now. It follows model support and a concrete use case; no slice until there is one. |
| Extensibility service | Isolated custom workloads beside the platform; queue based (Today) | Azure services with isolated containers, in production (Macer, Juno) | Yes | None. |
| Extensibility service | External frameworks under the same traces, feedback and approvals; each extension adopts the SDK contract once (Phase 1) | Not built | No, gap | E2. |
| Extensibility service | SymphonyAI Financial Services and RhythmX run LangChain agents on the service (Phase 2) | Our deck says SAIG companies use our capabilities through Plato | Compatible, not stated | Both routes hold: Plato for using our capabilities, the extension service for running their code on our platform. Our Plato slide should name the second route. |
| Extensibility service | Partner program in JazzX Studio (Phase 3) | Not SDK work | n/a | Product and partner program; out of SDK scope. |
| Infra layers | Tools and MLflow traces open to SDK apps (Today) | Yes, in production through the Library | Yes | None. |
| Infra layers | LLM gateway, memory, model picking and routing (Phase 1) | Gateway client arrives in the next release; session memory and compaction built; routing per role recorded | Partly | Long-term memory across assistants is not in an SDK plan. It needs a decision on whether the SDK owns it or calls a memory service. |
| Infra layers | Per-step cost and latency per run; versioned deployments with rollback (Phase 2) | Cost and latency metered per call; pack and assistant versions with rollback built in Plato, pending QA | Partly, rollback earlier than shown | E5 for the per-run report. Show rollback as built, pending QA. |
| Infra layers | SRMs behind the gateway; industry controls (Phase 3) | Not SDK work beyond choosing a model per role | Partly | A4 covers model choice; serving and controls are out of SDK scope. |

## Order

1. A1 and A2. They serve evaluation now and RL milestone 1 when it is staffed.
2. B1, B2 and B4.
3. C2 and C3.
4. A3 and D1.
5. B3 and C1.
6. D2 to D4.
7. A4 and E1 to E6 as their owners ask; E1 and E2 first among them, because the slide places them earliest.

L1 and L2 of `plan_JAPES_LEARNING_LOOP_CLOSE.md` come before B3 and C1.

## Decisions for the user

1. **Obfuscation standard.** Which fields are masked, and whether pseudonyms or redaction, for mortgage and commercial lending packs. This decides A2.
2. **Who trains.** The team and environment that consume A2 and A3's files. The SDK stops at the files and the evaluation of the trained model (A4).
3. **Where B3's change lands.** In the pack directly, or as a proposal Knowledge Studio reviews. Knowledge Studio uses its own code for JTBD review today.
4. **LangChain path.** In-process or extension container first (E2), and which SAIG team's agent is the first target.
5. **Obfuscated build.** Keep it on the roadmap (a customer-installed Plato) or drop it in favor of API-only access.
6. **Servicing and long-term memory.** Owners for the loss mitigation pack and ontology, and whether long-term memory is SDK work or a separate service.
7. **Spend.** A typed figure for each model-backed run (A3 rollouts, C1 rewordings, D1 to D3), given in the session that runs it.

## Out of scope

- Training, LoRA adapters, the RL trainer and its staleness correction.
- Model serving and SRM hosting.
- The obfuscated build of Plato for customer deployment.
- Industry controls (ISO, GSE).

## Not verified

- Where raw run transcripts are kept today (MLflow or a run journal), which decides how A2 captures them.
- Whether ACER's replica path can be reused for A3 without changes.
- Whether `GuidanceAsset` has a review date distinct from expiry.
- Whether the gateway client takes a custom endpoint per role.
- Whether evidence can be fetched by id for every run kind (E1).
