# Code yield: measure it, run the draft's cases, harden the draft (sonnet-runtime, 2026-10-18)

Checked against `pipelines/policy/code.py`, `pack/rule_cases.py`, `fabric/canonical/python_check.py`, `rules/lib.py`,
`util/run_health.py`, `pack/ledger.py`. Order: 1, 2 (with the calculation tool), then 3 to 5; 6 later.

## 1. Coverage accounting (S, first)
Today: a job without code is a `Disposition` (`computable_no_code`, `not_computable`, ...) and a segment the generator
refused is only a name in `failed_segments`: no reason code. `_generate` raises `ValueError("... fails the static
check")`, the run records the segment name, the reason is lost.
Plan: `CodeOutcome(rule_id, reason)` with reason in `static_check | cases_failed | transient | uncodable | ok`
(`uncodable`: the model declined with a rationale). `ExtractedCandidates` and `ExtractionRun` carry
`unwritten: [{id, reason, detail}]` (detail trimmed, no clause text); `extraction_health` reads it (a `code_unwritten`
signal with the counts by reason); `jtbdset_lint`/coverage report the same per job. Tests: one per reason.

## 2. Run the draft's own cases before accepting it (S-M)
Verified: the model writes `PythonCase`s (`_DraftCase`) but `_generate` only runs `check_python_rule` and
`scale_problems` (static) and one repair; the cases are stored, never executed during generation. `run_rule_cases`
(`pack/rule_cases.py`) exists and is used by trials and library pins.
Plan: after the static check passes, run `run_rule_cases(rule, executor)`; on mismatches or exceptions send
expected-versus-got (and the exception text) through `policy_code/regenerate`, at most `CASE_REPAIR_ROUNDS` (named
constant, 2-3) rounds including the static one; a rule whose cases still fail is kept with the failing cases listed
(tolerant first: proposed with a warning in `unwritten`-style detail, `cases_failed`), not dropped. The executor is the
one the code step already holds (`python_executor`); no executor: today's behaviour. Tests: a draft with a wrong case
is repaired on round 2; a crash is fed back; cases that never pass are proposed with the warning.
**With it, the calculation tool** (macer-style): a bounded `calculate(expression, inputs)` tool the generator may call
while writing, with an output validator rejecting a metric that states a value but no calculation text or no tool call
(today only `calculation_context` presence is linted in `jtbdset_lint`/`jtbd.py`). `ToolRequiredValueError` stays
deferred unless this tool becomes its consumer.

## 3. Boundary cases (M)
Not present. From numeric literals in the rule's AST derive n-1, n, n+1 (and the field missing, and `None`), run them
through the executor, and report: crashes; `None` answered as VIOLATED where the library's convention is unknown
(`rules/lib.known/unknown`); a boundary the clause text does not print. Findings join the case report of item 2 as
warnings, not refusals. Lives beside `python_check.py`.

## 4. Schema and type contracts (M)
Partly covered: `check_python_rule` already refuses a read key that is not a declared field; `scale_problems` checks
percent versus fraction against declared units. Missing: a comparison whose literal type disagrees with the field's
declared type (`str` field compared to a number; `bool` to `"yes"`; a date compared to a day count). Plan: field
metadata gives the type; `python_check` adds `type_problems` the same way as `scale_problems`.

## 5. Deterministic templates (M-L)
Partly covered: `rules/lib.py` has `same`, `match`, `ratio`, `close`, `band`, `known/unknown/gaps`, and month and day
spans; `render_api()` shows them to the generator. Missing: threshold comparison with the unknown convention built in
(`at_least(value, threshold)`, `at_most`, `within`), and a membership helper that returns the library's unknown for a
missing value. Plan: add those helpers (library version bump is a user decision), name them in the prompt, and make
`python_check` prefer them (a lint note when a raw `>=` on a read value has no `known()` guard). Templates as pack data
(a rule kind with parameters) are a later step.

## 6. Later, uncertain
Dependency-ordered generation for chained jobs (L): needs a measured failure first. Ground-truth calibration over
`rule_trial.py`/`rule_fix.py` (patch only the failing rule, accept on net wins, holdout rollback): mostly orchestration;
plan after items 1 and 2 give a yield number.

## Small additions (macer survey)
- In-loop citation/fact validators against run context (page numbers within each document's page count, ids in the
  known set): validators on the job writer's output beside `unprinted_figures`; small.
- Flag always-flipping rules in replicate runs as rule-quality problems: reads the stability report of
  `plan_replicate_stability.md`; add a `rule_flips` finding to the job-writing quality plan.
