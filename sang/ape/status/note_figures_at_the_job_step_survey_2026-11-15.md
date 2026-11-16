# Finding the figures at the job step: what exists, what is missing, the smallest change (survey, 2026-11-15)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>. Read-only follow-up to `note_generated_code_execution_survey_2026-11-15.md`. Decides nothing, builds nothing.
Marks: **[code]** read in source; **[run]** measured by a script over the Acra regen-5 export (scratchpad scripts, not in the repo; 97 rules, 51 of
which write at least one figure); **[doc]** from a docstring or the brief. The user's idea: policy to jobs to code, so figures (thresholds, caps,
limits) are found at the job step, approved there into pack data, and code generation takes them and flags a contradiction.

## Answers

**(1) What carries the figure the generated code uses: the job text, mostly; the clause is the fallback.** [code] `job_segment()` builds the
writer's input from the job's `purpose`, the checks to encode (prose strings, with a partial check's `decided` text), the checks left to a reviewer,
and then `SOURCE CLAUSE:` (the parts of the clause the encoded checks cite, else the whole clause). Both channels reach the prompt, and the guard
`unprinted_figures(draft.source, segment.text, ...)` compares the code's figures to that whole segment text (checks and clause together), not to the
clause alone; its findings are stored on the rule (`unprinted_figures` in the ledger key) as a note for a reviewer, not a refusal. [run] Of the 134
non-structural figures the 51 figure-bearing rules write: **93 (69%)** are printed in the job's `checks`, **29 (22%)** only in its purpose, steps or
outcomes, **9 (7%)** only in the source clause (the job step lost them), **3 (2%)** nowhere in the job or the clause (derived or invented). Structural
figures (0, 1, 100) are not counted, as in the guard.

**(2) Does the job step record a figure per check: no.** [code] A job (`_DraftJob`, `ProcedureCondition`) holds `checks: list[str]` (prose),
`computable_checks` (indices), `check_units` (clause unit ids per check), `subject_metrics` (keys and templates), `reads`, `missing_reads`, outcomes with
a prose `criterion`. There is no numeric field. `jtbd_consolidate` plans "aggregators" (a figure that is the minimum of caps several jobs state) as jobs,
by names, with no value. [run] The job step does not invent figures: all **127** non-structural numbers printed in the checks of these 97 jobs are also
printed in their source clause (0 misses by the same `printed_numbers` predicate the guard uses). So a job-step check "figure is in the clause" would
have found nothing to flag on this export.

**(3) Profile values: hand-authored, no review route.** [code] A `PolicyProfile` (`fabric/canonical/profiles.py`: `thresholds`, `confidence_floors`,
`custom`, `tables`) is a YAML file in the pack (`profiles/dscr_profile.yaml`, 14 `thresholds` entries for Acra DSCR). `RatioCondition.threshold` must be
`profile:<key>` and `RatioEvaluator` resolves it at run time from `context["_policy_profile"]`; `assessment.py` puts the pack's profile there. Proposal
kinds are `concept`, `relationship`, `rule`, `catalog`, `document` (`fabric/graph/proposal.py`): **none for a profile value or a figure**, so nothing like
`merge-catalog` exists for them; profile edits are draft-file edits that go through the draft's review like any file. Not confirmed: that
`pipelines/policy/conditions.py` names `profile:<name>`; it contains no `profile` reference (the `profile:` handling is in `policy.py` and
`condition_evaluator.py`). `find_profile_literal_drift` (`policy_lint.py`) compares an expression's declared `profile_custom_key` literal with
`profile.custom`; it has no caller outside the package's exports.

**(4) Can a generated rule read a profile value at run time: not today.** [code] `PythonEvaluator.evaluate` passes the child only
`{f: context[f] for f in condition.reads}`; the child never sees the profile or the pack. The static gate allows `ctx['key']` only for keys named in
`reads`, so the mechanism to deliver a value exists (name it in `reads`, put it in the context), but nothing puts a profile value under a read name, and
`render_api()` (the helper list the writer sees) says nothing about profile keys. A job's own determination can already be read as `derived:<rule_id>`
(`DERIVED_READ_PREFIX`), a computed result, not a constant.

**(5) Where a contradiction would be detected.**
- Code figure vs the text it was written from: exists (`unprinted_figures`), as a note. [run] 12 of the 134 figures are not in the job text; 9 of those are in
  the clause, 3 are in neither.
- Job figure vs the clause: no gate exists; the check above is a few lines over existing predicates (`printed_numbers`, `_printed_values`), and would run
  at the job step.
- Code figure vs an approved job or profile figure: impossible today, because no approved figure exists as data. With the change below it is
  "a written constant that is not structural and not read by name".

## The smallest change that makes jobs the one place figures are found and approved

Keep figures on the job, in pack data, and let the existing job review be the approval (no new proposal kind):

1. **Record.** Add an optional `figures: [{key, value, unit, check, cite}]` to the job record (`_DraftJob` and the job's `domain_extensions['jtbd']`), written
   by the existing job-writing call. At the job step, verify each value is printed in the cited clause (`_printed_values`, existing); one that is not is a
   finding on the job. Approval is the reviewer's pass over the job in the draft, as today.
2. **Deliver.** At assessment, put each job figure into the context under a read name (for example `figure:<rule_id>.<key>`); the code rule lists it in
   `reads` and reads `ctx['figure:...']`. The executor, static gate and JSON path need no change (the gate already allows any key named in `reads`).
3. **Generate.** `job_segment()` adds a `FIGURES (read these by name; do not write the number):` block; the code prompt says so.
4. **Flag.** Extend the guard: a written non-structural constant that equals no approved figure is `figure_not_approved`; one that equals an approved figure
   but is written inline is `figure_written_inline`. Recorded, not refused, with a strict mode as an opt in (tolerant first).

Not covered by a scalar figure: values that vary by program, purpose or state (the Acra grids; `band` tables), which the profile's `tables` already model.
Those need a `figures` shape that holds a table, or stay in profiles. Not measured: how many of the 134 figures belong to such grids.

## What it breaks

- **Existing packs and jobs:** nothing, if `figures` is optional and absent means today's behavior. Revolution and Pulte job sets carry no figures; their
  importer is unchanged.
- **The Acra regen-5 export:** its 97 rules write literals, so under step 4 every figure-bearing rule (51) would carry the inline finding until regenerated;
  a regeneration needs the user's typed approval with a figure. A rule's `reads` would also include `figure:` names, which `reads` consumers must accept:
  the catalog field-coverage and `reads`-against-catalog lint treat a read as a case field and would call it unmapped (not read to confirm; to check
  before building). A rule's code digest changes on regeneration, so proposals supersede as they do for any fix.
- **Prompts:** `policy_code` prompt versions change, and the bundle's per-stage prompt version with them.
- **Jaci:** the seed Acra pack is a synced copy; job and profile changes belong in jaci first (sonnet-jaci), not in the SDK session.

## Verified and not

Verified by reading: the segment text, the guard and where its findings go, the job and condition models, proposal kinds, profile structure and
resolution, the evaluator's context, the static gate's key rule. Verified by running a script: the 134, 127 and 12 figure counts. Not verified: the
grid share; consumers of `reads` (coverage, lint, export) beyond the two named; whether the job-writing prompt could carry a `figures` field without
lowering job quality (no regen run); anything in kernel-lab.

## Addendum: two placements compared (A at the job step, B a pre-process at the start of code generation)

Extra measurements, [run] over the same 97 rules: the code writes **134 figure occurrences but only 37 distinct values**; 21 values are used by two or
more rules (65 and 75 in 13 rules each, 80 and 70 in 12, 700 and 2 in 7, 1500000 and 6 in 6). Only **5 of the 134** occurrences equal a value in the
hand-written Acra profile (5 distinct thresholds, the DSCR floors), so the profile does not yet hold the LTV and CLTV caps. A value is not a meaning:
the 12 rules that write 80 do not all mean one cap (a 2-4 unit CLTV cap, other grid cells), so a figure's identity cannot be its value. The existing
scan `printed_numbers(text)` returns `{value: spelling}` with no position or sentence, so either placement needs a scan that also returns the unit and
sentence each number sits in (the one shared finder).

| | A: at the job step | B: pre-process at generation, proposed as profile values |
|---|---|---|
| **Needs to change** | The job-writing prompt and record (`_DraftJob`, job extension) gain `figures`; a per-job verify against the clause; delivery at assessment; code prompt and guard. The job prompt is the largest and most quality-sensitive prompt (every job set depends on it). | A finder (deterministic scan with unit and sentence, shared), one naming call (name each candidate, tie it to a check), a new proposal kind for a figure (today: concept, relationship, rule, catalog, document) with a merge that writes the draft's profile `thresholds`, the review surface, delivery at assessment, code prompt and guard. Size anchor: the alias-proposal slice (a new proposal path plus merge) was +586 / -37 lines over 11 files. |
| **Reruns** | Figures are written again with the job; an approved value lives on the job, so a job rewrite loses it unless job identity carries it forward (not checked). The model may name or round differently each time. | The scan is deterministic over the clause; an approved profile value is matched by (clause unit, value, spelling), not by name, so a rerun that finds the same number files nothing, and a changed number files a conflict against the approved value (the catalog `conflicting` pattern). Names vary run to run (the vocabulary retest saw this), so the name must not be the identity. |
| **Existing packs without regenerating jobs** | None: needs the jobs rewritten, or a backfill, which is B's finder. | All packs that keep clause text: jobs carry `ledger.clause` and an imported job keeps its whole requirement (`codable` docstring), so the Acra seed, the Revolution and the Pulte sets can be scanned as they are. A pack with no profile file gets one created. |
| **Where a contradiction is detected after generation** | The guard compares code figures to the job's own figures; a cap two jobs state differently is not seen. | The same guard compares code figures to the approved profile values, and a value shared by many rules is one entry, so two rules reading different values for one key cannot happen; the unwired `find_profile_literal_drift` lint has a place to run. |
| **Main risk** | Job-writing quality and cost move; every existing pack stays unbenefited until jobs are regenerated. | The scan over-collects (section ids like STD-8.1, dates, counts), so the naming call and the reviewer carry the filtering; qualified figures (by program, purpose, state, the grids) need key names that carry the qualifier, and a grid is not a scalar. |

**Recommendation: B first, then A only if wanted.** B works on today's packs with no job rewrite, puts a figure used by many rules in one approvable place
(37 values behind 134 uses), reuses the existing `profile:<key>` mechanism and the catalog's conflict pattern for reruns, and leaves the most fragile
prompt alone. Build the finder once (scan with unit and sentence, returning candidates) in the policy pipeline package; A then becomes a small step later:
the job step writes `figures: [key]` as references to approved profile keys (a name, never a value), by calling the same finder over the clause. Order:
(1) finder and its tests, no model; (2) naming call and the figure proposal kind and merge; (3) delivery at assessment and the prompt; (4) the guard.
Steps 1 and 4 can ship before 2 and 3, as a report only: the finder over regen-5 would list the 134 uses and the proposed keys with no change to any pack.
Not measured: how many figures are grid cells; the cost of the naming call; whether a pack without a profile file loads cleanly with one added.
