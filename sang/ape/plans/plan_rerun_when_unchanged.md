# Plan: what a rerun does when nothing changed, as a setting (sonnet-runtime, 2026-10-30)

Plan only; nothing built. The user asked "is there a way to make this configurable?" about the rerun that finds nothing to redo.

## 1. What happens today (read from `pipelines/steps.py`, adjudication step)
A rerun (`rerun: {of, rejected}`) computes what changed (fields of the record, documents by sha256) and what the followed run never judged. When nothing changed, nothing
was rejected and every live rule has a prior verdict, the adjudication step copies the prior verdicts, asks no model, and reports `stop_reason: no_impacted_rules`.
That stop is **of the adjudication step only**: the run goes on through the rest of the conductor (narrative, governor, approval) over the copied verdicts.
So an unchanged rerun costs no adjudication but can still draft a narrative and wait for an underwriter again.

## 2. Proposed setting: `rerun.when_unchanged`
| Value | The run |
|---|---|
| `continue` (default, today's behavior) | copies the verdicts and finishes the conductor as now |
| `stop_copy` | ends at once as succeeded with the prior run's outcomes as its result; later steps do not run, no checkpoint is raised |
| `stop_empty` | ends at once as succeeded with no outcomes and `stop_reason: no_impacted_rules`; the caller reads the followed run for the verdicts |
Where it is set, in order of precedence: the submit body (`rerun: {of, rejected, when_unchanged}`), then the pack (`pack_manifest.yaml` `rerun: {when_unchanged: ...}`), then `continue`.
An unknown value is refused at submit (422) and by pack lint. Keyed only on `no_impacted_rules`; `nothing_applicable` and `all_segments_failed` are not unchanged runs and are untouched.

## 3. What is not yet known
- **How the conductor ends a run early.** Detection is inside the adjudication step; ending the run needs a halt signal from a step that the conductor honors (the approval and governor
  steps can block a run, but I have not read whether any step can end one as succeeded). I would read the conductor loop first; if there is none, the smallest addition is a typed
  `StepOutcome.halt` that the loop checks after each step, which is a conductor change and its own commit.
- **Which later steps a pack wants skipped.** `stop_copy` skips all of them. A pack that wants the narrative skipped but the governor kept is a different setting; I would not add it until a pack asks.

## 4. Risks to decide on
- **Time.** "Nothing changed" is computed from inputs only. A rule that reads the date (an expiry, a rate lock) can change its answer with no input change; `continue` and both stops
  carry the stale verdict. Today's behavior has the same gap; the setting does not fix or worsen it, but `stop_copy` removes the later steps that might have caught it.
- **Audit.** The chain of runs stays the history; a stopped run still records the followed run id, why it stopped, and (for `stop_copy`) that its outcomes are copies.
- **Approval.** `stop_copy` after an approved decision means no second approval for an unchanged case: usually right, but it is the user's rule to set, hence `continue` stays the default.

## 5. Build, when asked
Tests first (they fail on old code): each value on an unchanged rerun (steps run or not, outcomes, status, `stop_reason`); a changed rerun ignores the setting; precedence submit over
pack; an unknown value refused at submit and in lint. Then the setting, the conductor halt if needed, the client's `rerun` parameter, the CHANGELOG. No provider call is involved
(adjudication is already skipped on this path), so this needs no spend approval.
