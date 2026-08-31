# The learning pipeline: what exists, what runs, what does not

Written to answer a question that was deferred until this was understood: should japes drop
`japes_feedback` the way kernel dropped its feedback tables? That answer is at the end, and it
depends on facts about the rest of the loop rather than on the table itself.

Read against the current working tree. Verified by reading source and grepping callers across
japes and jaci; nothing here was run end to end, because as far as I can tell nothing ever has.

---

## The loop, as the code itself describes it

`modes/evolve/curator.py` states the intended shape, and the rest of the tree matches it:

```
  run  ──►  Eval        ──►  Signals   ──►  Curator      ──►  Draft asset
            (EvaluatorMode)   (tagged)      L1 route          (DRAFT)
                                            L2 synthesise          │
                                                                   ▼
  Promoted  ◄──  Approve/deploy  ◄──  Validate the candidate  ◄──  SME review
  (DEPLOYED)     (GuidanceLifecycle)  (guidance_ab, pass_bars)      (human gate)
```

Feedback enters from the side, not the top: `Feedback.to_signal()` turns a human correction into
the same `ImprovementSignal` an evaluation produces, so overrides and eval findings converge on one
routing path. That is a genuinely good piece of design and it is fully built.

## What is built

Substantial and, as far as the unit tests go, sound. Roughly 5,000 lines across `evaluation/` plus
the EVOLVE modes.

| Stage | Where | State |
|---|---|---|
| Golden cases | `evaluation/golden_cases/` | schema, loader, validator, set-versioning + diffs |
| Harness | `evaluation/harness/` | config, runner, results aggregation |
| Scoring | `scorers.py`, `metrics.py`, `trajectory.py`, `operational.py`, `qa.py`, `gate_eval.py` | LLM-judge, adjudicator, trajectory, cost/latency/topology |
| Pass bars | `pass_bars.py` | corpus-level bars and violations |
| L3 human review | `l3_review/` | schema + storage |
| Feedback | `feedback.py`, `feedback_db.py`, `feedback_quality.py`, `feedback_text.py` | in-process + durable stores, LLM quality assessment, actionable-item extraction |
| Signal routing | `modes/evolve/curator.py` | L1 tag routing (no LLM), L2 LLM synthesis to a DRAFT asset |
| Candidate validation | `guidance_ab.py` | before/after harness, AB pass bars |
| Prompt optimisation | `optimization.py` | score → propose → keep best, incl. `ReflectiveOptimizer` |
| Prompt versioning | `prompt_registry.py`, `prompt_registry_db.py` | versioned, aliased, promote |
| Experiment record | `experiment/`, `reporters/mlflow.py` | ExperimentRun + MLflow bridge |
| Compounding metrics | `compounding.py` | override learning rate, guidance effectiveness, asset growth |
| eval-service boundary | `eval_service_adapters.py`, `feedback_sink.py` | every japes-type ↔ wire-contract translation, in one auditable file |

## What actually runs

This is where the assessment turns.

**Nothing in japes composes the loop.** The only reference from one stage to another is a docstring
cross-reference in `eval_service_adapters.py`. That is defensible on its own — japes provides,
the client composes, per the adoption policy — so the question becomes what the client does.

**jaci composes the first half, once, in a demo.** `scenarios/ci_spread/demo_correction_to_guidance.py`
runs correction → `synthesize_bucket` → DRAFT asset. That path is real.

**The second half has no caller anywhere.** Grepping jaci for the validate-and-promote surface:

- `run_ab_comparison` — no usage
- `check_ab_bars` — no usage
- `PromptRegistry` / `promote` — no usage

Each is built and has a japes unit test. None has ever been called by a consumer.

**And the two places that touch promotion both go around it:**

1. `demo_correction_to_guidance.py:112` **prints** the approve/deploy calls as instructional text
   rather than executing them. The demo stops at DRAFT and narrates the rest.
2. `credit_outcome.py:201` constructs a `GuidanceAsset` with `status=GuidanceStatus.DEPLOYED`
   directly, bypassing `GuidanceLifecycle` entirely.

So the one place in the estate where guidance actually reaches DEPLOYED does not pass through the
gate built to govern that transition. The lifecycle is not being *violated* — nothing is enforcing
it, which is the more useful way to say it.

**Two curator entry points have no test at all**: `route_improvement_signals` and
`process_evaluation_report` — the whole of Layer 1, the non-LLM routing that everything downstream
depends on.

## What this means

The pipeline is not half-built. It is **fully built and half-wired**, which is a different problem
and a more expensive one, because the unused half looks finished. Unit tests pass against every
stage in isolation, so nothing signals that the stages have never been connected.

The specific risk: the stages were built at different times against an evolving idea of the loop,
and the interfaces between them have never been forced to agree by an actual run. A composition
attempt is the only thing that will surface where they do not.

**The stale README is a symptom worth naming.** `evaluation/README.md` still says "Status: Phase 1
Complete (v1.6.0)" and lists L3 review, the harness, and UI patterns as "coming", while all three
shipped. Anyone orienting from the doc concludes the opposite of the truth.

## The `japes_feedback` question

**Recommendation: keep it, and do not read kernel's deletion as precedent.**

Kernel deleted a feedback table that was a *production write target* it had stopped using. japes'
is explicitly not that. The boundary is already decided and documented in `feedback_sink.py`:
eval-service is the production source of truth for feedback that counts toward institutional
learning; japes' local stores exist for offline and test use, and the referenced plan names
"making japes local feedback storage a second production source of truth" as an explicit non-goal.

`feedback_db.py` goes further and enforces it: `assert_not_eval_service_database` refuses to start
against a database that already owns a `feedback` table, precisely so the two never become two
writers of one table.

So the table is not vestigial and not a duplicate; it is the offline half of a boundary that has
already been drawn deliberately. Deleting it would remove the ability to exercise the loop without
standing up eval-service — which, given that the loop has never been run end to end, is the
capability most needed right now, not least needed.

Worth revisiting if and only if the composition work below shows the local store is never the one
used.

## The loop, now composed

`tests/test_learning_loop_end_to_end.py` runs the chain against in-process stores and a scripted
model: feedback -> signal -> route -> synthesise -> A/B validate -> pass bars -> approve -> deploy.
It passes. Four findings came out of the handoffs, none visible from any single stage:

1. **Routing discards the provenance the evidence-backed path attaches.** `ImprovementSignal`
   carries `attribution_id` and `evidence_ids`; `learning_candidate_to_signal` exists to populate
   them; Layer 1 then flattens the signal to `signal_tag` + `signal_text`. A governed candidate and
   a raw thumbs-down reach synthesis indistinguishable. **This is the one that matters** -- the
   governance work upstream is undone by the stage immediately after it.
2. **`Feedback.from_case_result()` produces a signal the router rejects** (`category="eval_fail"`
   becomes a tag outside the closed set). The automated half of the loop discards every signal it
   creates; human feedback survives only because a human picks a valid tag.
3. **Layer 1 and Layer 2 do not compose** -- routing returns `CuratorQueueEntry`, synthesis takes
   `ImprovementSignal`, nothing converts. A caller must keep the originals.
4. **The vocabulary is AML-specific** in a module documented as generic.

## How this would work in jazzx-assistant

Different from jaci, and more interesting: **jazzx-assistant is the only consumer that closes the
last mile.** jaci exercises the first half (correction -> DRAFT). The assistant is the only place
where approved learning actually changes live behaviour -- `handler._maybe_inject_feedback` appends
approved feedback to the orchestrator's system prompt.

Its gating is the best in the estate and worth copying rather than changing: a global operator
kill-switch *and* the agent's own `use_feedback` flag read from kernel, fail-closed at every step
(no kernel URL means skip, not proceed), and eval-service's per-entity `max_results` treated as
untrusted input with its own clamp.

**But the loop's output is not what it reads.** The pipeline produces a `GuidanceAsset` that
reaches `DEPLOYED` and is retrievable through `fabric.guidance.retrieve` /
`render_guidance_block`. jazzx-assistant reads eval-service *feedback rows* flagged
`kernel.is_static:true` through its own HTTP client. Those are two different formats from two
different stores. **A fully working curator loop would still not reach this service.** That is the
structural gap, and it is larger than any of the four found above.

Three consequences worth stating plainly:

- **There is no capture path.** A user correcting the assistant mid-conversation produces nothing:
  no `Feedback`, no signal, no write anywhere. The service is read-only with respect to learning,
  so the richest source of correction in the estate is discarded at the point of generation.
- **The service duplicates `clients/eval_service_client.py`.** japes ships `EvalServiceClient`
  with `get_feedback_config` / `find_similar`; the assistant has its own with a different read set.
  Consolidation should move *toward* the assistant's version, not away: it carries hardening japes'
  lacks, including catching `httpx.InvalidURL`, which is not an `httpx.HTTPError` subclass and
  would otherwise escape into a live turn.
- **Its japes footprint is four imports** (`HandlerContext`, `ResponseMessage`, `BaseHandler`,
  `compute_cost_from_metrics`, plus streaming). Everything about feedback is its own code. That is
  the measure of how little of this pipeline is actually reusable as shipped.

If the goal is a closed loop that includes this service, the order is: give it a capture path
(`FeedbackSink` already exists and is the right shape), then decide whether guidance assets and
eval-service feedback rows converge on one format or the assistant learns to read both. The second
is a real architectural decision and should not be made by whoever happens to wire it first.

## What I would do next, in order

1. ~~Compose the loop once, end to end, in a test.~~ **Done** -- see above.
2. **Decide what the tag vocabulary is for**, which resolves findings 2 and 4 together. Then fix
   the provenance drop (finding 1), which is the one with governance consequences.
3. **Test Layer 1.** `route_improvement_signals` and `process_evaluation_report` have none, and
   everything downstream is built on them.
4. **Decide whether `GuidanceLifecycle` is advisory or mandatory**, then make `credit_outcome.py`
   consistent with the answer. Right now the gate exists and is skipped, which is the worst of the
   two options because it reads as governed and is not.
5. **Fix `evaluation/README.md`.** It actively misinforms.
6. **Then** revisit `japes_feedback` with evidence from (1).

## Not verified

- Whether eval-service's own pipeline duplicates any japes stage (the adapters suggest a clean
  split, but I read only japes' side of the boundary).
- Whether jaci's demo path has ever been run against a live LLM, or only in the demo's own fixture.
- Whether the `ReflectiveOptimizer` / `optimize_prompt` sub-loop, which jaci does call from
  `hitl_approval.py`, closes on its own — it may be a complete smaller loop independent of the
  curator path, in which case the estate has two learning loops with different shapes.
