# Rules, trials and the helper library: the design as built (v2.6.2)

The plan is `done_rule_trials_and_library.md`. This describes what exists, where, and what it does
not do. Measured numbers are in `ape/local/mining/` (`r0_report.md`, `r3_baseline.md`).

## The flow

```
extract -> trial -> judge -> fix -> (re-trial) -> merge (gated) -> publish
```

A python rule is a function `check(ctx)` over declared `reads`, run in a hardened child process. It
returns `True`, `False`, or `rules_lib.unknown(*missing)` ("cannot tell").

## The ladder

A rule is written in the lowest rung that can state it: (1) conditions (Z3-compilable, exact),
(2) python with the helper library (deterministic, tested), (3) live (a model judges at run time).
Today the rung is reported per rule outcome (`PolicyAssessment.engines[rule].kind`) and per trial row
(`rung`); the extraction prompt does not yet prefer rung 1 (not built: no evidence it mis-chooses).

## The helper library: `jazzx_sdk/rules/lib.py`

One stdlib-free source file, delivered whole into the executor's child as the module `rules_lib` (the
child has no SDK). `LIB_VERSION` changes when an answer a helper gives changes. Scope came from mining
(R0): 51 generated rules had no date handling, no unit conversion, no helper function, one import. What
they repeated: enum spelling (`loan_purpose` in five spellings), missing-field handling (all 51 read
with `ctx['x']`, none could say unknown), a handful of ratios. So: `known`, `gaps`, `unknown`, `norm`,
`same`, `match`, `ratio`. Nothing is added until rules repeat it.

- `import rules_lib` is in `ALLOWED_IMPORTS`; the static check accepts it and still forbids passing
  `ctx` on, so the reads a rule declares are the reads it makes (`gaps(a=a, b=b)` takes values).
- Delivery: the executor passes the library text in the child's setup, executes it into a fresh module
  before the audit hook is installed. Each run gets a fresh child, so a rule cannot alter the library
  for the next.
- Pinning: `PythonCondition.lib_version`, set by the extractor when the source imports the library.
  Lint (`rule_library_pin`, warning) flags a pin that is not the delivered version;
  `retest_library_pins` (`pack/rule_cases.py`) re-runs those rules' generated cases and lists the ones
  whose answers changed.
- Prompt: `policy_code/prompt.md` v1.1.0 renders the API from the library's docstrings
  (`rules/api.py`), so the model is told what exists.
- Not done: sharing the helpers with the expression evaluator (only `ratio` overlaps, and it has one
  consumer); date, unit and rounding helpers (none appeared).

## The unknown verdict

`(None, {"missing": [...]})` from the child becomes an indeterminate outcome with reason
`EVIDENCE_MISSING` and `missing_fields`, which an assessment reports as `pending_evidence`. The
evaluator already withheld a rule whose declared reads were absent; the library extends that to
values that are present but not stated (`None`, blank, `"unspecified"`, `"unknown"`).

## Trial: `jazzx_sdk/pack/rule_trial.py`

`overlay_pack(pack, proposals, policy_id=)` copies the pack to a temp directory, merges the proposals
(as if accepted) into the file holding the policy with `merge_rules_into_draft` (so a trial judges what
a merge would publish), cuts the conductor to `document_ingest` + `policy_assessment`, and points the
assessed program at the policy. No store is written; a proposal whose rule id collides replaces the
published rule and the row says so.

`RuleTrialInvoker` (eval entity `rule_trial`, id = pack id; config `proposal_ids`, `policy_id`, a pin
`version` or `draft`): `run_case` on the overlay, then `assess` the same record on the published pack,
so the case's decision is reported with and without the proposals. Output per case:
`proposals[id] = {verdict, outcome, rung, replaced, digest, reads, missing}`, `allowed`,
`published_allowed`. Ingest is the only model cost. Not built: reuse of a prior read through
`RerunBasis` (each trial case re-reads its documents).

Gold is per rule: a dataset case's `expected = {"rules": {proposal_or_rule_id: verdict}}`. The
`trial_agreement` scorer (registered in `standard_scorers`) counts `agree`, `disagree`,
`unexpected_indeterminate`; a case with no per-rule gold is not applicable. Boundary false fails need a
rule's threshold, which a trial row does not carry: not computed.

Judge: `GET .../authoring/review/{pack}/proposals/{id}/trials` returns `latest_trial(...)`: the newest
completed trial whose rows carry the proposal's current content digest, per case with reads, gold, the
decision with and without, and `highlight` (`disagree`, `unexpected_indeterminate`). The proposals tab
shows it under "Trial". A rule trial is started like any experiment and takes the reviewer role.

## Provenance: `jazzx_sdk/pack/rule_reads.py`

Every active rule's reads (its condition's evidence contract) with the source of each value: a document
and page (`documents.filled`), the submitted record, or a derived metric, plus the fields nothing
supplied. Built in the policy-assessment step from what the run already holds, stored on
`PolicyAssessment.reads`, shown on the runs page ("What each rule read"), and the source of a trial
row's `reads`.

## Fix: `jazzx_sdk/pack/rule_fix.py`

`POST .../proposals/{id}/expand` (from the current code) and `/redo` (from the clause) regenerate a
python rule with the reviewer's note and the failing trial cases (values read, gold, missing fields) in
the prompt (`policy_code/regenerate.md`). The result is a new proposal, never an edit: same rule id (so
merging it replaces the old rule), id `<root>~N`, `derived_from`, the note in `feedback`; the old one
gets `superseded_by` and is skipped by merge (route and `merge_rules_into_draft`). A re-trial of the new
proposal over the same dataset starts automatically when there was a prior trial. Deviation from the
plan: a redo regenerates from the proposal's stored excerpt, not from the documents (the run's
documents are not kept), so it cannot recover from a bad excerpt.

## Merge gating

`PLATO_REQUIRE_TRIAL` (default on when deployed, off locally): `merge-rules` refuses a proposal no
completed trial judged at its current content digest (409 naming them), and a merged rule records
`domain_extensions.trial_ref = {trial_id, passed, cases, indeterminate}`. A changed or re-extracted
proposal has a new digest, so its old trial no longer counts.

## The executor on Linux

Layers: static check (`check_python_rule`), the audit hook in the child, rlimits (CPU, AS, NOFILE,
FSIZE, NPROC), and `unshare(CLONE_NEWUSER|CLONE_NEWNET)`. The last two are kernel layers that quietly
no-op where the platform refuses them (macOS; a default container seccomp profile; root bypasses
`RLIMIT_NPROC`). `probe_isolation()` runs a child through the executor's own setup and asks the
kernel: can it reach a loopback listener, can it fork. In a deployed posture, when either holds
nothing, `local_python_executor()` returns None: python rules are withheld (assessments report them
pending), the boot log says why, `/info` carries `python_rules: {available, withheld_because}`, and
readiness is unaffected (`BOOT_CONTRACT` row; `docs/DEPLOYMENT_ENV.md` regenerated). Locally nothing is
probed. `/tmp/japes_executor_linux_check.sh` (needs Docker running and the Plato image) runs the probe,
the posture decision and nine escape attempts under five container variants; memory is not enforced on
macOS, so that attempt reads NOT REFUSED there and is the Linux job's to prove.

## A bug the trial found

`PythonEvaluator` handed reads to the child uncoerced, and a typed fact catalog normalises numbers to
`Decimal`, which JSON cannot carry: the rule was "not activated" on every loan whose figures came
through the catalog. 35 of 51 generated rules were inert. Reads now arrive as `int` (whole) or `float`.

## Known limits

- The synthetic gold loans are records, not documents; the document half of a trial is unproven until a
  sanitized package arrives (plan decision 1).
- No per-rule gold exists yet for DSCR: the baseline can only say the decision-level gold is contradicted.
- A quote-grounded document field proves the quoted words exist, not that they support the value
  (`TODO(quote-not-checked-against-value)`).
- The before/after of regenerating the 51 with the library prompt is not measured (needs a model-spend
  ceiling from the user).
