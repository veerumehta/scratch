# Assessment engine modes: code_only, jobs_only, hybrid, both

Plan, sonnet-runtime, 2026-10-17, from opus-xrepo's request. Branch `v2.6.4`. Status: written, decisions for the user
in section 8; nothing built. Owner: sonnet-runtime (SDK `assess`, case runs, eval invoker).

## 1. Golden set (placeholder)

- Golden loan(s) with expected verdicts: **TODO(golden-set-location): the user will download them and put them under
  docs/ or another path; record the path here.**
- Sanitized Acra loan package: **TODO(golden-set-location): same.**

The acceptance test (section 7) cannot be written until these exist.

## 2. What happens today when a job and its code are both in force (read from the code)

- `assess()` builds the in-force policies and runs `DefaultPolicyExpert.check_compliance`, which walks every active
  rule of every policy and evaluates it by its own condition kind (`procedure` by the reasoning agent, `python` by the
  executor, comparisons and matrices by their evaluators). Nothing pairs a job with its code at run time:
  `condition.derived_from` is read only by the ledger, coverage, bundle, rule view, `rule_fix` and the release report.
- A job and its code are two rules with two ids. If both are in force and both fail, `violations` gets two entries
  (one per rule id, not de-duplicated) and `applied_policies` lists both. So a requirement can be counted twice.
- Missing data is handled per rule: an INDETERMINATE outcome that is not a gate (`gate_blocks`) is skipped
  ("replaces nothing, so the base rule runs"); one that is a gate withholds the allow and is listed in `refusals`.
- The only displacement mechanism is `replaces` / `suppresses`, and it works across policies, not inside one: a
  policy's replacements are merged into `superseded` after its own rules have run ("rules in one policy never
  displace each other"). A code rule that `replaces` its job would therefore skip the job only if the two sit in
  different policies, the code's policy first by precedence. That is the nearest thing to `hybrid` that exists, and
  nothing writes it: written code rules carry `derived_from`, not `replaces`.
- Per-rule results already exist: `PolicyAssessment.outcomes` (verdict per rule, with the fields read) and
  `engines` (the kind of each rule, and whether it is live). Neither says which engine *decided* a requirement.

To confirm by a run before the build (first test of the build): two rules, one job-shaped and one code-shaped,
both failing in one policy, give two violations; the same pair split across two policies with `replaces` gives one.

## 3. Pairing

- A job is a procedure rule (`ledger.is_job`). Its code is the python rules with `derived_from == job.rule_id`,
  plus the rules the stored ledger matched to it (`pack/ledger.py`, the `by_job` map: `derived_from` first, then
  ledger matches). One function, `job_code_pairs(pack) -> {job_rule_id: [code_rule_id, ...]}`, reused by the modes,
  coverage and the release report (they compute it today from the same two sources).
- Several code rules for one job: the group is one code verdict. Definite only when every rule in it is definite;
  VIOLATED when any is violated, SATISFIED when all are satisfied; any INDETERMINATE (missing data, unreadable fact,
  CONDITION_UNEVALUABLE, executor error) makes the group indeterminate, which falls back to the job (`hybrid`) and is
  shown as such (`both`). Conservative: a job is skipped only when all of its code agreed to decide.
- Code with no job (`derived_from` empty, no ledger match) and jobs with no code are unpaired: they run as they are
  in `hybrid` and `both`.

## 4. Modes (SDK)

`assess(..., engine_mode="hybrid")`. Today's behaviour (everything in force runs, no pairing) stays selectable as
`all`. A pack's `assessment` step may declare `engine_mode:` as its default; the request overrides it. Same field on case runs
(`policy_assessment` step) and the eval invoker.

1. `code_only`: rules whose kind is not `procedure`. Jobs with no code are listed under `not_covered` and not run;
   jobs with code are represented by it.
2. `jobs_only`: `procedure` rules only; code ignored.
3. `hybrid`: per pair, evaluate the code group first. Definite: that verdict stands, the job is skipped, the outcome
   says `decided_by: code`. Indeterminate: the job runs, `decided_by: job`, `fell_back: true` with the reason.
   Unpaired rules run as they are. Implementation: two passes over the same prepared context. Pass A evaluates
   the non-procedure rules; pass B evaluates the procedure rules not decided by pass A. The compliance results merge
   (violations, refusals, applied, outcomes) with one entry per requirement. No change to `check_compliance`'s own
   loop; the pass split filters the policies handed to it (`materialize_policy` output), so the displacement rules
   of section 2 are untouched.
4. `both`: both passes run for every pair, nothing merged: each pair is a row `{job, code_rules, code_verdict,
   job_verdict, agree}`. `allowed` and `violations` come from the stated primary (`primary: jobs` by default,
   `code` allowed), so the answer stays defined; the other engine's findings are in the rows only.

Record on every outcome: `decided_by` (`code`, `job`, `none`), and on the assessment an `engine_summary`:
`{mode, decided_by_code, decided_by_job, fell_back, not_covered, disagreements, pairs}` (all counts, usable as eval
metrics). A pack with no code has no pairs, so `hybrid` runs it exactly as `all` does; a pack with jobs and code stops counting a
requirement twice. Without an executor the code is withheld, so its jobs run (the fallback).

## 5. Where it surfaces

- `PolicyAssessment.engine_mode`, `.engine_summary`, `.comparison` (the `both` rows) and `decided_by` on `outcomes`;
  `CaseResult` carries the same; the client contracts gain them (open models).
- Eval: a scorer family reading `engine_summary` (share decided by code, fell-back share, disagreement rate) plus the
  existing verdict scorers against the golden set's expected verdicts, per mode.
- Runs page: a column for the engine that decided, and the comparison rows for a `both` run (sonnet-ui).
- Lint: a finding `job_and_code_both_in_force` for a pack whose step selects `all` with job and code both in force,
  since it can count a requirement twice (a warning, tolerant first; `strict` refuses).

## 6. SDK, pack data, and what the Acra seed adopts

- SDK: the modes, `job_code_pairs`, `decided_by`, `engine_summary`, the comparison rows, the scorers, the lint finding.
- Pack data: an optional `assessment.engine_mode` and `primary` default. Nothing domain- or client-named.
- Acra seed (synced from jaci): nothing required. `hybrid` is the default and its written code already carries
  `derived_from`; a pack that wants today's behaviour sets `engine_mode: all`.

## 7. Tests and acceptance

- Unit (fail on the old code): double counting today (two violations for a paired failing job and code); `code_only`
  reports unpaired jobs as not covered and runs none; `jobs_only` ignores code; `hybrid` skips a job its code decided
  and runs one whose code is indeterminate on each of missing data, unreadable fact, CONDITION_UNEVALUABLE and an
  executor error; several code rules, one indeterminate, falls back; `both` returns both verdicts and the stated
  primary's `allowed`; `decided_by` and the counts on every path; a pack with no code gives the same result under `hybrid` and `all`; `engine_mode: all` is today's result for a pack with both.
- Stubs shaped like production: the executor and reasoning agent fakes return what the real ones do (an
  INDETERMINATE outcome, not an exception, for missing data).
- Acceptance: the Acra golden loan(s) in all four modes against the expected verdicts: per mode, verdicts right,
  `engine_summary`, and the `both` disagreements read by a person. Blocked on the golden set (section 1).

## 8. Decisions

1. **Default: `hybrid` (user, 2026-10-17: code is to replace jobs in the end).** `all` is today's behaviour, selectable.
   Consequences to carry: a pack with no code is unchanged; a pack with both now gets one verdict per requirement and
   `decided_by` on its outcomes; consumers that read `violations` see one entry where they saw two; a deployment with
   no executor falls back to the jobs. CHANGELOG states the default change; the client contracts are open models, so
   no consumer breaks on the new fields.
2. **What counts as code in `code_only`.** Every non-procedure rule (recommended: it is what the request says, and
   threshold and matrix rules are code too), or only the python rules written from jobs? Open.
3. **Several code rules for one job.** One group verdict, any indeterminate falls back (recommended), or each code
   rule decides alone? Open.
4. **`both`'s primary.** Jobs (recommended, as requested), with `code` selectable per request. Open.
5. **The lint finding.** A warning for `all` with job and code both in force (recommended; tolerant first). Open.
