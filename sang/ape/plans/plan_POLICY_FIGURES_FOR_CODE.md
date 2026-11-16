# plan_POLICY_FIGURES_FOR_CODE

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
Repo: japes (`jazzx_sdk`, `plato`); release placement is the user's call, recommended 2.7.4

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-15 drafted by sonnet-packs from the user's decision "B: figures found as a pre-process of code generation" (via opus-xrepo), after two read-only surveys: `note_generated_code_execution_survey_2026-11-15.md` and `note_figures_at_the_job_step_survey_2026-11-15.md` (with its A-versus-B addendum). Nothing built.

## Goal

The numbers a policy states (caps, floors, limits, rates) are found once, reviewed twice as their own set, and generated rules read an approved figure by reference instead of writing the number. When a policy document changes, every figure is compared with the new text and a changed or missing one is a conflict for a person; nothing updates silently. Code that disagrees with an approved figure or with the clause is flagged after generation.

## What the surveys established (measured on the Acra regen-5 export, 97 rules)

- The code writes 134 figure occurrences but only 37 distinct values; 21 values are used by two or more rules (65 and 75 in 13 rules each, 80 and 70 in 12). A value is not a meaning (the 12 rules that write 80 do not mean one cap), so a figure's identity cannot be its value or a model-chosen name.
- 69% of the occurrences are printed in the job's checks, 22% only in its steps or outcomes, 7% only in the clause, 2% nowhere; all 127 figures in the checks are printed in the clause. Only 5 of the 134 equal a value in the hand-written Acra profile.
- A generated rule reads only `{f: context[f] for f in reads}`; nothing puts a profile value under a read name. The static gate already allows any key named in `reads`.
- The scan `printed_numbers(text)` returns `{value: spelling}` with no unit or sentence; nothing finds figures with their context.

## Design

### Where the figures live (requirement 1)
**A pack data file of its own, `figures.yaml`, at the pack root, declared in the manifest (`figures: figures.yaml`) beside `policies`, `profiles` and `vocabulary`; not in the profile.** It sits with the code representation (the policies and their python rules) because it is derived from the same clauses and versions with the same pack version, so two pack versions compare with the existing keyed-set compare (`vocab_compare`, `diff_mappings`).

Why not `profile:<key>`: a `PolicyProfile` is an institution's flat `thresholds` (decimal strings), `confidence_floors`, `custom` and `tables`, read by `RatioCondition`; it has no place for the spelling, the unit, the clause sentence and unit it came from, the check it decides, an approval state and who approved it, and a pack may have no profile. Reusing it would also mix reviewed policy figures with unreviewed institutional tuning. A figure may carry an optional `profile_key` so an approved figure and a profile threshold that mean the same thing are linked (the 14 hand-written Acra thresholds, 5 distinct values, become linked figures), and a `RatioCondition` keeps resolving `profile:<key>` unchanged.

A figure record: `id` (a digest of `clause_unit`, `value`, `spelling`, so it is stable across reruns), `key` (a display name from the naming call, never the identity), `value`, `spelling`, `unit`, `clause_unit` (the guideline unit id), `sentence` (the evidence), `check` (the job and check index it decides), `qualifiers` (program, purpose, state, where the sentence says so), `profile_key` (optional), `state` (`proposed`, `approved`, `rejected`, `superseded`), `approved_by`, `approved_at`. "Rules that use it" is derived at read time from the rules' `figure:` reads, not stored, so it cannot drift.

### The finder (shared, one function, no model)
`jazzx_sdk/pipelines/policy/figures.py`: scan a clause's text and return candidates `{value, spelling, unit, clause_unit, sentence, span}` using the same number predicate the guard uses (`printed_numbers` and `_printed_values`, extended with position and the enclosing sentence), minus structural numbers (0, 1, 100) and section ids, dates and counts the scan can recognize deterministically. Everything else, including the guard's reverse check, calls this one function so there is no second finder.

### Naming and tying (one model call, proposals only)
One call per job's clause parts names each candidate and ties it to a check; it cannot add, change or drop a number (a name for a candidate the scan did not find is discarded). Output becomes `figure` proposals, never written to the pack until approved. Names vary run to run, so the match key on a rerun is the `id` digest, not the name.

### Review as its own set (requirement 2)
A figure proposal is a new proposal kind (`figure`, beside `catalog` and `document`) with ops `add_figure`, `change_value`, `retire`. A merge writes approved ones into the draft's `figures.yaml` (the pattern of `alias_merge`: a proposal that writes a file in the draft, not the catalog). The review view is a Plato page, **Figures**, listing every figure with value, spelling, unit, the clause sentence, the rules using it, the check it decides and its state, filterable by state and by program. Approving, rejecting and the conflicts go through the existing proposal review routes; the page adds a read route for the set. **What it needs from sonnet-ui:** the page itself (off the rail like the other pages, linked from Extraction and Coverage), the `?pack=&version=` prefill, the compare view for two versions, and a section for the policy-update report (slice 4); **from sonnet-runtime:** `GET packs/drafts/{pack}/figures`, `GET packs/{pack}/{version}/figures`, `GET packs/{pack}/figures/compare`, the proposal kind and its merge route, and client methods for each.

### Generated rules read an approved figure by reference (requirement 4)
The smallest design that keeps the sandbox closed: **a figure is a read.** A rule lists `figure:<id>` in `reads` and writes `ctx['figure:<id>']`; `PythonEvaluator` already passes only the declared reads, so the one new step is the assessment engine adding `context['figure:<id>'] = value` for each approved figure a rule's `reads` names (the same place that supplies `_policy_profile` today), through the existing JSON channel (`_json_read`). The child gets a number, nothing else: no profile object, no pack path, no new import, no file or network access, and no change to `check_python_rule` or `LocalPythonExecutor`. A `figure:` read of an unapproved or missing figure makes the rule withheld (indeterminate, "figure not approved"), never run with a guess; a tolerant mode may run a proposed value and say so. `lint.py` exempts the `figure:` prefix from the catalog-field check exactly as it does `derived:` (`lint.py:97`); coverage and the field-mapping report need the same one-line exemption (to be checked, not read).

### After generation: the contradiction guard (requirement 5)
`unprinted_figures` is replaced by a guard over the finder's output with three comparisons, recorded on the rule as findings (tolerant by default, strict as an opt-in): `figure_written_inline` (a written constant equals an approved figure's value: read it instead), `figure_unapproved` (a written constant is printed in the clause but is no approved figure: the finder proposes it), `figure_unprinted` (written and printed nowhere, today's note), and `figure_stale` (a rule reads a figure whose value is no longer printed at its unit in the current clause, which slice 4 raises).

### Policy updates are checked against the set (requirement 3)
**Reuse, do not invent.** `pack/guidelines.py` already versions a guideline set (`G1`, `G2`, content-digested), compares two versions by section (documents cut at headings), says which sections changed so re-extraction runs on those alone, and lets a pack declare the `guidelines: {set, version, digest}` it was certified against. `pack/release_report.py` already reports what a new pack version changes (jobs, rules, documents, catalog, coverage, gold cases) without spending, and `vocab_compare` / `diff_mappings` already give one compare shape (`added`, `removed`, `changed`, `excluded`, `replaced`) for any keyed set. So: when a guideline version is ingested the finder rescans its text (cheap, deterministic, no model), pairs each approved figure with the new text, and the figures section of the report is `vocab_compare` over the two sets. Pairing across versions cannot use the in-version match key (the value is what changes), so it uses **(clause unit, sentence with its numbers masked)**, falling back to `pack/text_similarity.py`; per figure the report says `unchanged`, `changed` (old and new value, spelling and sentence), `missing` from the new text, or `new`. A `changed` or `missing` figure files a `change_value` or `retire` proposal marked conflicting, for review; nothing is updated silently, and rules reading a `changed` figure are listed as affected. Domains where rates move are the case: the report is the thing a person opens first.

### Migration of the Acra regen-5 export
1. Run the finder over the export's jobs (their clauses are in `ledger.clause`) as a report only; no pack change. It lists the 134 uses against proposed figures and the 5 that already match a profile threshold.
2. The reviewer approves the figures into `figures.yaml` (the profile file is untouched; the 14 thresholds link by `profile_key`).
3. Until the 51 figure-bearing rules are regenerated with `figure:` reads, the guard reports `figure_written_inline` on them; the export keeps working as it is. Regeneration of those rules needs the user's typed approval with a figure, and code digests change so the rules supersede as for any fix.
4. The seed Acra pack is a synced copy of jaci: its `figures.yaml` and manifest key belong in jaci first (sonnet-jaci), then the sync. Revolution and Pulte jobs carry no figures: the finder runs on their imported clauses with no pack change.

## Slices (orderable; sizes are estimates with an anchor)

Anchors: the alias-proposal slice (new proposal path and merge) was +586 / -37 lines over 11 files; the Models page +522; the demo loader +467.

### F1. The finder and a report over regen-5 (no pack change)
- Owner: sonnet-runtime builds `figures.py` and its tests; sonnet-packs runs the report over regen-5 and records the numbers (distinct figures, per-clause counts, over-collection rate by hand sample). About +350 lines (finder 150, report script 80, tests 120), 3 files.
- Acceptance: tests fail first; the finder returns value, spelling, unit, clause unit and sentence for each number; structural numbers, section ids and dates are excluded by rule, and each exclusion has a test; the report over regen-5 reproduces 134 uses and 37 distinct values; no model call, no pack file written.

### F2. The `figures.yaml` set, the proposal kind, the merge and the review view
- Owners: sonnet-runtime (kind, naming call, merge, routes, client methods, lint), sonnet-packs (the `figures.yaml` format as pack data, the naming prompt as a versioned prompt file, the seed data and migration step 2), sonnet-ui (the Figures page). About +900 lines over about 14 files (kind and merge 450 on the alias anchor, naming call 120, routes and client 150, page 300 on the Models anchor).
- Acceptance: a rerun over unchanged text files nothing; a changed number files `change_value` marked conflicting; the merge writes only `figures.yaml` in the draft; the page lists every field named above; approve and reject use the existing review routes; the route-versus-client test passes; the naming call cannot add a number (test with a stub that returns an extra candidate).
- Spend: the naming call is the only paid step. Its cost is unmeasured; a measuring run needs the user's typed approval with a figure.

### F3. The run-time read and the generation prompt
- Owner: sonnet-runtime (assessment context, `figure:` lint exemption, withheld outcome, guard), sonnet-packs (the code prompt text and figure block in `job_segment`'s data). About +400 lines over about 8 files.
- Acceptance: a rule reading `ctx['figure:<id>']` gets the approved value through the executor with no change to `local_executor.py` or `python_check.py` (assert the diff touches neither); an unapproved read withholds the rule; the three guard findings are recorded; a regenerated rule from a pack with figures contains no inline policy number (measured on a sample, by the guard).
- Spend: a regeneration of any real pack needs the user's typed approval with a figure.

### F4. The policy-update comparison
- Owners: sonnet-runtime (the report and its route, built on `guidelines` compare, `release_report` and `vocab_compare`), sonnet-ui (the report section on the Figures page). About +450 lines over about 8 files.
- Acceptance: a new guideline version with one number changed, one sentence removed and one figure added reports exactly `changed`, `missing`, `new` and the rest `unchanged`, with old and new value and sentence; a changed or missing figure files a conflicting proposal and changes no pack file; rules reading a changed figure are listed; two versions with identical text report all `unchanged`.

## Order

F1, then F2, then F3, then F4. F1 ships as a report with no pack change; F4 needs F2's set and F3's `figure:` reads to name affected rules, so it is last. F2's UI and F3's runtime work can overlap once the proposal kind is fixed.

## Decisions for the user

1. **Own `figures.yaml` or reuse the profile** (recommended: own file, optional `profile_key` link; the profile keeps institution tuning).
2. **Release placement**: 2.7.4 (recommended), or fold into 2.7.3.
3. **An unapproved figure when a rule runs**: withhold the rule (recommended in strict postures) or run the proposed value with a note (tolerant default).
4. **Granularity of approval**: per figure (recommended, the most important items to check twice), or a batch per clause section with a per-figure override.
5. **Qualified figures** (by program, purpose, state, grids): start with scalar figures and a `qualifiers` text (recommended), or model grids as tables from the start (the profile already has `tables`).
6. **Who may approve a figure**: the same reviewers as jobs, or a separate role for figures.

## Out of scope

- Moving the profile's institution tuning into figures; changing `RatioCondition` or `profile:<key>`.
- Regenerating any real pack's jobs or code (separate approval).
- A change to the executor, the static gate or the posture gate.

## Not verified

- Over-collection rate of the deterministic scan (section ids, dates, counts): the first F1 measurement.
- The share of the 134 figures that belong to grids or qualified cells.
- That coverage, the field-mapping report and the export profiles tolerate a `figure:` read (only `lint.py` was read, which exempts `derived:`).
- The naming call's cost and its quality (whether it ties a figure to the right check).
- That job identity carries approved figures across job rewrites (not needed by this design, since figures live outside the jobs, but unchecked).
- Whether a pack with no profile or figures file loads cleanly with `figures:` added to its manifest.
