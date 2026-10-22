# Seven ideas: rule correctness and evaluation (sonnet-runtime, 2026-10-22)

Plan only, after the fifteenth-review push and the loan-2 write-up. In order of value. Each item says what exists (grepped at `v2.6.5`),
what is missing, the step and the effort. Generic; no source named.

## 1. An independent case author (S-M)
Exists: `pipelines/policy/code.py` takes the code and its cases from one draft call (`_DRAFT_CODE_SCHEMA`); `pack/rule_cases.py`
`run_rule_cases` runs a rule's own cases through the executor; `pack/boundary_cases.py` adds probes from the code.
Missing: cases written without seeing the code.
- A second reasoning call per rule, given only the clause text and the declared fields and units, returning cases in the same shape.
- Both sets run through `run_rule_cases`; a case the code disagrees with is a finding `independent_case_mismatch` (a review flag,
  like the boundary findings, in the rule's `domain_extensions`), never a refusal.
- Off by default (`independent_cases: true` on the template). Cost: one call per rule; measure the share of rules with a mismatch
  and how many are real on the Acra pack before turning it on anywhere.

## 2. A unit helper for the runtime (S)
Exists: `scale_problems` (`pipelines/policy/conditions.py`) statically refuses a comparison of a `percent` field with figures all
below 1 (and the reverse); the template declares `units`; boundary probes exist.
Missing: a runtime helper in `rules/lib.py` (it has `norm`, `ratio`, `close`, none for scale) and boundary probes on both scales.
- `percent(value, scale)`: returns the value on 0-100 whatever scale it arrived on, using the declared unit when the caller has
  it, and refusing (`unknown`) an ambiguous 1 to 100 value rather than guessing; precision kept as given.
- Boundary probes for a unit-declared field try both scales at the threshold.
- First read what `scale_problems` already catches on the 3b rules; build only the gap.

## 3. Citation lint (S, verify first)
Exists: a `Rule` carries `citations: list[str]` (the parent policy's `source_refs`); `pack/lint.py` has `duplicate_citation`;
`ModalClauseExtractor` and `PythonExtractor` set `citations=[segment.citation]`. `python_check.py` knows nothing of citations.
Missing: a lint that a generated rule has at least one citation. Check what `lint.py` already flags before adding a code; the
"violating path names its clause" form needs result detail our rule outcomes do not carry, so it is out unless a rule's finding
text can name `citations[0]`.
- Step: `rule_without_citation` (warning) in `pack/lint.py` for a rule with a `derived_from` or a clause origin and no citations.

## 4. Patch history for repairs (M)
Exists: `pack/rule_trial.py` `proposal_digest` dedupes a proposal; `pack/rule_fix.py` `fix_proposal` feeds back the trial view
(`trial_feedback`). Nothing records a change that was tried and failed.
- A record per attempt on the proposal's own store row (no new table): target rule, digest of the change, the trial verdict, and
  the failing cases before and after (the delta), keyed by the digest of the clause text.
- `fix_proposal` lists the earlier failed changes for that clause in its feedback and refuses a change whose digest is on the
  failed list. A policy edit changes the clause digest, which clears the history.
- Cost: none in calls; a column on the proposal row and a migration. Needs real corrections to be useful (as C4 does).

## 5. A shared pairing helper in `rules/lib.py` (M, defer)
Exists: `pack/jtbd_match.py` pairs two job sets (id or skill, then close text, then a model tie-break); nothing in `rules/lib.py`.
No generated rule has needed to pair two record lists yet, so building it now generalizes an unhit problem. Recommendation: build when a
rule needs it; the shape is `pair(a, b, key, tolerance)`: by key, then numeric within tolerance, then word overlap, one-to-one.

## 6. Run-level input overrides for experiments (S-M)
Exists: `server/agent_overrides.py` (`AgentOverrides`, from `config["agent_overrides"]`, applied by `agent_with_overrides` in
`eval_api`) changes the assistant; nothing changes a case's input.
- `config["input_overrides"] = {"all": {path: value}, "cases": {case_id: {path: value}}}`, validated like `AgentOverrides` (a bad
  path or a non-mapping is refused by name). A path is dotted; a segment into a string that holds JSON parses it, sets, and
  writes it back as JSON.
- Applied in `ExperimentRunner` to a deep copy of each case's input just before the invoker runs, so the dataset and its forks
  are never changed.
- Identity: it is part of `config`, so `repeat_identity` (the config digest) already separates runs with different overrides and
  the variants spans follow; test that two runs differing only in an override are not repeats.
- Sits beside `agent_overrides` in the same `config`, one validator module each.

## 7. A verifier that decides only the disagreements (S-M)
Exists: `pack/engine_modes.py` `both` mode lists each pair's two verdicts; `hybrid` has a primary decide. In the loan-2
end-to-end report 12 of 43 and 11 of 56 pairs disagree.
- After `both` has paired code and job, a verifier `ReasoningAgent` call per disagreement, given the requirement text and the
  evidence both read (the job's cited pages, the fields the code read), answers satisfied, violated or indeterminate.
- If the verifier agrees with one side, that verdict stands, marked `verified_by`; if it agrees with neither (or is indeterminate)
  the pair stays a disagreement. Never changes an agreeing pair.
- `verify_disagreements: true` on the step (off by default). Cost: one call per disagreement, so about 23 calls on the loan-2
  report (roughly 1 to 2 USD with document evidence); measure agreement rate before using it as a gate.

## Order and effort
1 (S-M), 2 (S), 6 (S-M), 7 (S-M), 3 (S, after the lint check), 4 (M, when corrections exist), 5 (deferred). Each with tests first
and its own commit; details in the CHANGELOG.
