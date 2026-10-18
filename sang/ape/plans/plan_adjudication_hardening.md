# Adjudication hardening (sonnet-runtime, 2026-10-18)

Verified by grep in `agents/adjudication/`, `agents/run_kit.py`, `agents/models.py`, `conductor/strategies/ensemble.py`.

## A1. Cite validation (S-M): not covered
`_BatchItemVerdict.valid_cites()` parses each cite with `EvidenceCite.model_validate` and `continue`s on failure: a cite
that does not parse, names an unknown document or a page past the document's end is dropped silently, and a verdict left
with no evidence after the drops is not flagged. Plan: validate in the verdict model's `model_validator` (so the existing
retry-with-feedback loop re-asks): unknown document first (against the run's document ids/aliases), then page outside
1..`page_count`, then page 0, each message naming the cite; the document page counts come from the evidence workspace
(`workspace.py`) through the validator's closure (a context var set by the segment run, so the pydantic model stays pure).
A verdict whose evidence is empty after validation and whose status needs evidence gets its own message. Tolerant after the
retries are spent: keep the verdict, mark `cites_unverified` in its narrative, never drop silently. Tests: each of the three
failures is fed back and corrected on retry; exhausted retries keep the verdict marked.

## A2. Tool-suppressed retry (S): not covered, and the premise holds
`run_agent` retries a schema (`ModelBehaviorError`) or truncated response with `tools=current_tools` unchanged, so a retry
can reopen the whole tool loop (and `tool_choice` is never set anywhere in the SDK). Plan: on a validation retry run with
`tool_choice="none"` and the feedback "fix the output, do not call tools"; a validator raises `ToolRequiredValueError` (a
`ValueError` subclass) to keep tools on for that retry; it is checked before the error cap. Where it applies: `run_agent`
and `run_with_recovery`; the model settings carry `tool_choice`. The calculation tool of the code yield plan is the first
consumer. Tests: a retry after a schema failure carries `tool_choice="none"`; a `ToolRequiredValueError` keeps tools;
the first attempt is unchanged. Reopens the deferred item.

## A3. Orphaned-reasoning 400: already covered
`agents/models.py` reads the item id from the 400 (`_orphaned_reasoning_id`), replaces the reasoning item with a
continuation message (`_strip_reasoning_item`) and retries (RetryingModel). Nothing to build.

## A4. Section-sized work units (S): not covered
`plan_or_fallback` returns the planner's plan or the static catalog; nothing re-bins by section. Plan: an optional
`bin_by_section` step after planning: group rules by their own section stem, largest first, split a group above a
named `MAX_UNIT_RULES`, fixed unit names (`<section>#<n>`), so no free-form large session and A/B cost runs compare.
Default off; on by a spec flag. Tests: deterministic names and order; oversize split; off leaves the plan unchanged.

## A5. Tie toward the conditional verdict: already covered (report only)
`adjudication_vote()` is `DeterministicVote(ADJUDICATION_PRIORITY)`: violated, then indeterminate, then satisfied, then
not_applicable (a lower index wins), so adverse beats clean regardless of majority; among votes of one status the one with
the most conditions open wins (then the status's name). A conditional pass therefore beats a clean pass. `EnsembleCollapse`
itself is only the protocol; `DeterministicVote` is the default collapse.

## Eval notes recorded for scoring and defaults (no build)
Retrieval beside full document tools regressed 43% of rules (it helped only when it replaced or gated document access);
a small model gave 11-21 false PASSes and is not viable for verification; reference verdicts taken from other experiments
had 12 errors in 157 rules and need a document-level review before they are a gold set.
