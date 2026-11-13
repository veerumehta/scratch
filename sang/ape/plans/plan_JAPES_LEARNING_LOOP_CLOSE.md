# plan_JAPES_LEARNING_LOOP_CLOSE

Author: Virendra Mehta · 2026-11-10 · Status: not started

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-10 drafted from a read of `main` (2.7.0). Complements `plan_JAPES_2_7_1_KNOWLEDGE_LOOP_CHANGE_CLASSES.md` (change classes, gates, forum approval, proposal and signal records, citation index); nothing here repeats that plan.
- 2026-11-13 L1 landed (`eff41245`, v2.7.3): deployed guidance per segment in `AdjudicationAgent` (`guidance_pack_id`, `guidance_applicability`, `AdjudicationAgent(..., guidance=store)`), refs on judged verdicts under `inputs["guidance_refs"]`, case decision `guidance_refs`. Retrieval runs before the fan-out (an access denial must stop the run); the plan's `run_segment` does the prompt and refs, not the retrieval. Refs are on model-judged verdicts only. The query adds each rule's description to the ids and section.
- 2026-11-13 L2 landed (`b95f6413`, v2.7.3): decided with the user that the feedback store is the queue (Layer 1 buckets are in-memory and nothing stored them; no table added). An approved correction becomes a `rule_correction` signal with case, rule, run and pack ids, filed with the new `route_signal`; the feedback router's `on_change` routes it, guarded. The plan's `Feedback.from_case_result` is for eval results; corrections already are `Feedback`, so `to_signal()` is the successor. L3 needs a "drafted" marker (the draft asset's provenance is the candidate) and a per-pack grouping.
- 2026-11-13 L4 landed (`v2.7.3`): the plan's with/without comparison cannot move a gold answer (gold cases are assessed with no model; guidance reaches only model-judged verdicts), so with the user's decision L4 is an observed uplift (`pack/guidance_uplift.py`, a `guidance` section in the release report) and not a counterfactual re-run. The re-run needs each gold case's documents and a typed spend cap, and is not built.
- 2026-11-13 L3 landed (`v2.7.3`): `jazzx_sdk/modes/evolve/sweep.py` and `job:guidance-sweep`. The "marked so the next sweep skips it" is the proposal naming the correction ids (no new table); the cap is one `CallMeter` across the run and the job exits 3 unless `PLATO_GUIDANCE_SWEEP_MAX_USD` is set. Per pack, not per tag. Not run live.

## Goal

Close the learning loop the deck now shows: signals, Curator draft, human approval, guidance used in context, checked on gold cases. Today chat uses deployed guidance and a person or a batch job starts drafting. Case runs and ACER do not read deployed guidance, case corrections do not feed the Curator on their own, nothing sweeps full buckets, and nothing measures whether guidance helps.

## Before starting

Verify in this order: the latest CHANGELOG entries, this plan, `plan_JAPES_2_7_1_KNOWLEDGE_LOOP_CHANGE_CLASSES.md`, then the source. Where 2.7.1 has landed parts of this (for example proposal records), build on them rather than beside them.

## What exists on main (2.7.0)

- `modes/evolve/curator.py`: Layer 1 routes `ImprovementSignal`s into buckets by tag with no model call and logs when a bucket reaches `synthesis_threshold`; Layer 2 `synthesize_bucket` drafts one `GuidanceAsset` at `DRAFT` through `ReasoningAgent`. It never approves or deploys.
- `modes/evolve/evaluator.py`: now runs through `ReasoningAgent`; an exhausted retry is a failed `ModeResult`, not a silent empty signal list.
- `fabric/guidance/`: `GuidanceAsset`, `GuidanceLifecycle` (draft, approved, deployed, deactivated; reviewer only), `retrieval.retrieve` and `render_guidance_block`, `GuidanceRef` on the decision.
- `agents/interactive/agent.py`: `_apply_guidance` (top three deployed, in-scope, unexpired items into the prompt, traced) and `_apply_feedback` (approved feedback as a prompt block).
- `plato/api/guidance.py`: list, get, put, transitions, and `POST .../guidance/from-feedback`, which calls `synthesize_bucket` on reviewed feedback.
- Case runs: the `playbook` step returns playbook guidance refs (`pipelines/steps.py` around 2423); ACER takes only the pack `persona` (`agents/adjudication/spec.py` around 76). Neither retrieves deployed `GuidanceAsset`s.
- Gold cases from corrections and the release report (`pack/correction_cases.py`, `pack/release_report.py`).

## Slices

### L1. Deployed guidance in case runs and ACER
- In `agents/adjudication/segment.py` (`run_segment`), when the spec names a guidance pack, retrieve deployed guidance per segment with the segment's rule ids and section as the query and applicability, render it after the persona, and record `GuidanceRef`s on each outcome the segment produces. Same retrieval and failure rules as `_apply_guidance` (best effort; an access denial propagates).
- Add the field to `AdjudicationAgentSpec` (`guidance_pack_id`, `guidance_applicability`), mirroring the interactive spec; off unless set.
- Intent: guidance an SME approved reaches verdicts, and each verdict says which guidance shaped it.
- Acceptance: a test pack with one deployed item shows it in the segment prompt and its ref on the outcomes; with no guidance store the run is unchanged; a draft item is never used.

### L2. Case corrections become signals automatically
- When a reviewer corrects a case outcome (the correction route that already writes a gold case), also emit an `ImprovementSignal` through `Feedback.from_case_result` (or its successor in 2.7.1) and route it with Curator Layer 1. No model call.
- Intent: the most valuable signal, an expert overriding a verdict, enters the loop without someone filing feedback separately.
- Acceptance: a correction produces one routed signal with the case, rule and outcome ids; routing failures are logged and never block the correction.

### L3. A scheduled sweep that drafts, never approves
- A Plato job, beside `job:run-reaper`, that finds buckets at or over `synthesis_threshold`, calls `synthesize_bucket` once per bucket and leaves the asset at `DRAFT`. Bounded by a per-run model spend cap from configuration; off by default.
- Intent: drafts appear for review without someone remembering to start them.
- Acceptance: a bucket over threshold produces one draft per sweep and is marked so the next sweep skips it; the cap stops the sweep cleanly; nothing reaches `approved`.

### L4. Measure whether guidance helps
- Extend the release report (`pack/release_report.py`) to compare a pack version with and without a set of deployed guidance on the same gold cases: newly passing, newly failing, unchanged, per guidance item where possible.
- Record applied guidance refs in run metrics so a regression can be traced to the item that caused it.
- Intent: the "Evaluator proves uplift" step the loop promises, as a number.
- Acceptance: a report on a test pack shows a guidance item that fixes one gold case and breaks none; a deliberately harmful item shows as newly failing.

### L5. Register Feedback to Improvements
- Once L2 to L4 stand, register `feedback_to_improvements` in the pipeline catalog (carried item 32 from `plan_JAPES_PIPELINE_NAMES_AND_CATALOG.md` P6): signals in, routed and drafted guidance out, with the measurement attached, ending at a reviewer pause.
- Acceptance: the catalog lists it as Input to Output with output kind `proposals`; a run on a test corpus ends paused for review with drafts and their measured effect.

### L6. A review page in Plato
- A Plato page listing draft guidance per pack with its signals, rationale and the L4 measurement, and approve, revise and reject actions through the existing transition routes.
- Acceptance: a reviewer can approve a draft from the page; the audit trail shows the actor.

## Order

L1 and L2 first (they make the loop real for case work), then L4, then L3, then L5 and L6.

## Not verified

Whether 2.7.1 work already changed `Feedback.to_signal` or added proposal records on a branch; whether any consumer calls `synthesize_bucket` outside the Plato route.
