# plan_JAPES_2_9_0_JOB_WRITER_COVERAGE_AND_CODABILITY

Author: Virendra Mehta
Repo: japes (`jazzx_sdk`, `plato`), working tree at 2.6.5
Companion: `claude/Acra_JTBD_and_Code_Generation_Assessment.md` (the findings this plan acts on)

## Why

The Acra regeneration (`acra-regen-3b`) produced 231 jobs and 99 code rules. The assessment traced the shortfall to five mechanisms in our own pipeline, not to model skill: units planned into several sections and written once per section; computability decided once by the job writer and never revisited; the ledger clause stripped of headings and table labels; coverage counted by citation rather than by check; and an export that drops the section, the metrics and the step numbering. This plan changes those five, in `jazzx_sdk/pipelines/policy/`, `jazzx_sdk/pack/ledger.py`, `jazzx_sdk/pipelines/policy/jtbdset.py` and four prompt files, so the next regeneration is measurably better before any pack or schema work.

What this plan does not do: bind the Acra template to the canonical object schema (a pack change that needs the canonical catalog file, listed under "Decisions needed"), or change the assessment engine, Plato routes or the kernel.

## Confirmed against current code

Read before writing this plan: `jazzx_sdk/pipelines/policy/jtbd.py` (633 lines), `jtbd_fold.py` (269), `jtbd_data.py` (134), `jtbd_shape.py`, `jtbdset.py` (323), `code.py` (316), `ledger.py` (34), `extract.py` lines 134-160 and 590-630, `jazzx_sdk/pack/ledger.py` lines 330-450, `jazzx_sdk/pack/catalog.py` lines 118-160, `jazzx_sdk/prompts/files/policy_jtbd/*.md`, `policy_code/job_prompt.md`, `plato/data/seed_packs/acra_dscr_policy/jtbd_template.yaml`, `tests/` names.

Anchors the plan relies on, as they stand:

- `jtbd.py` `SectionSegmenter.segment()`: `grouped.setdefault(_slug(planned.name), ...)[1].extend(ids)` with no cross-section de-duplication; `assigned` is used only to compute `leftover`.
- `jtbd.py` `JtbdExtractor._candidate()`: `cited = [...] or segment.parts`; `extensions[LEDGER_KEY] = {CLAUSE_KEY: "\n\n".join(p.text for p in cited if p.text)}`; `computable = None if reads else []` and the writer's list is kept only when `reads` is non-empty.
- `jtbd.py` `_DraftJob`: `computable_checks: list[int] | None`, `source_units: list[str]` (per job, not per check).
- `jtbd_fold.py` `fold_duplicates()`: skips a pair when `_kind(a) != _kind(b)` or `figured[i] != figured[j]`; scores `jaccard` over `_text()` = description + purpose.
- `code.py` `codable()`: `condition.computable_checks != [] and (condition.checks or job_clause(rule))`; `job_segment()` renders `job_clause(rule)` whole; `JobCodeExtractor.extract()` drops a draft with no declared reads.
- `jazzx_sdk/pack/ledger.py` `_disposition()`: `[]` with `missing_reads` is `not_computable`; `None` is `unassessed`.
- `jtbdset.py` `export_jtbdset()`: `section = policy.domain_extensions.get("section") or policy.name`; `_render()` emits `## Step` for a step whose first line is not a `#`/`##` heading starting with "step"; `_META` already carries `loan_metrics` through `**meta`.
- `extract.py` `extract_step()` line 601: `extractor.fold` runs once over all candidates after every section is written. This is where a program-wide pass hooks in.
- `plan_prompt.md` v1.0.0: "a unit may belong to more than one" section. `write_prompt.md` v1.2.0 asks for computable positions and `source_units` per job.

## Workstreams

### W1. One unit, one section

File: `jazzx_sdk/prompts/files/policy_jtbd/plan_prompt.md`
Anchor: the sentence "a unit may belong to more than one".
Change: replace with: each unit belongs to exactly one section, the one whose jobs will decide it; a unit that supports several sections goes to the one it most directly states a requirement for. Add a line that the planner is given each section's definition. Bump the file's `version` to 2.0.0.
Intent: duplication at the source.

File: `jazzx_sdk/pipelines/policy/jtbd.py`
Anchor: `SectionSegmenter.segment()`, the loop over `plan.sections`.
Change: keep a unit in the first section that claims it and drop later claims; record the dropped claims on the returned segments (a `shared_units: dict[str, list[str]]`, unit label to the other sections that asked for it) so the cross-section pass in W3 can see them. Pass the template's section descriptions to the planner: build `taxonomy` from `template.mnemonics.families` descriptions when present (today only the names reach the prompt), falling back to names.
Intent: enforce the prompt; give the planner the definitions it needs to file correctly (DSCR under Property Tax Calculation is a symptom of names without definitions).

Test: `tests/test_policy_jtbd.py`: a plan that lists U3 under two sections yields U3 in one segment only, and the second section's `shared_units` names it.

### W2. Citations and clause per check, with headings

File: `jazzx_sdk/pipelines/policy/jtbd.py`
Anchor: `_DraftJob` and `JtbdExtractor._candidate()`.
Change: add `check_units: list[list[str]] | None` to `_DraftJob` (unit labels per check, same index as `checks`); `write_prompt.md` asks for it ("for each check, the ids of the units it decides"), version 1.3.0. In `_candidate()`: `cited` becomes the union of `check_units` when given, else `source_units`, else `segment.parts` as today, and a note is appended when the fallback to all parts is taken. The ledger clause is rendered with each part's heading: for each cited part, `heading` on its own line above `text` when `heading` differs from `marker` (the same shape `_render_unit()` gives the writer). Store `check_units` in the `jtbd` extension under a new key `CHECK_UNITS_KEY = "check_units"` and add it to `jtbdset.py` `INTERNAL_JTBD_KEYS`.
Intent: per-check provenance for W4's coverage, and the matrix tier labels reach the code writer.

File: `jazzx_sdk/pipelines/policy/code.py`
Anchor: `job_segment()`.
Change: when the job carries `check_units` and the ledger clause carries per-part structure, render only the parts cited by the checks to encode (plus their headings); otherwise the whole clause as today. Keep `CHECKS LEFT TO A REVIEWER` as is.
Intent: the code writer sees the clauses its checks need, not a seven-clause wall.

Tests: `tests/test_policy_jtbd.py`: a cited part with heading "Loan amount <= $1,500,000" appears in the ledger clause above its table. `tests/test_job_code.py`: `job_segment()` of a job whose computable checks cite U2 only renders U2 and its heading.

Note for the ledger: `jtbd_fold._figures()` and `conditions.unprinted_figures()` read figures from the clause; headings add the tier figures, which is wanted. `tests/test_jtbd_fold.py` fixtures that assert exact clause text need the heading line added.

### W3. Program-wide pass: definitions and aggregators

File: `jazzx_sdk/pipelines/policy/jtbd.py`
Anchor: new method `JtbdExtractor.consolidate(candidates, shared_units)` beside `fold()`; `extract.py` `extract_step()` line 601 calls it after `fold` when the extractor has it.
Change: one model call per program over a compact listing of every job (id, section, kind, skill, checks, reads) and the `shared_units` from W1, with two prompts in a new `policy_jtbd/consolidate_*.md` pair: (a) name the determinations the set should have as jobs of kind `determination` and which existing jobs should cite each by name instead of re-deriving it (citizenship class, foreign national, ITIN, first-time homebuyer, listed for sale, business purpose, channel, qualification method); (b) name the aggregators the set lacks (final maximum CLTV as the minimum of every cap the limit jobs state, final minimum FICO as the maximum of every floor, total reserves as the sum of every trigger, governing minimum DSCR), each as a job of kind `limit` whose checks reference the contributing job ids. The pass returns new `_DraftJob`s (written through `_candidate()` with the units the contributing jobs cite) and a list of `(job_id, determination_id)` rewrites; a rewritten job gets the determination's name appended to its `reads` as `derived:<determination rule_id>` and a note. The template gains `consolidate: bool` (default false) so packs opt in.
Intent: the two shapes the hand-built set has and ours lacks; derived fields for W5's code writer.

Test: `tests/test_policy_jtbd.py`: with a stub reasoning agent returning one determination and one aggregator, the candidate list grows by two, both carry `job_kind`, and the rewritten job's reads include the `derived:` entry.

### W4. Computability as a second pass, per check

File: `jazzx_sdk/pipelines/policy/jtbd.py` (new module `jtbd_computable.py` beside `jtbd_data.py`)
Anchor: called from `JtbdExtractor.extract()` after `_with_data_mapped()` and before `_candidate()`, and from W3 for the new jobs.
Change: a per-job model call with the job's checks, its reads after data mapping, the full `template.reads` list with units, and the `derived:` names from W3, returning per check one of `computable`, `partial` (with the sub-predicate the fields decide and the residue left to a reviewer, as text), `needs_field` (with the field name it would need, in Entity.field form), `judgment`. Store the result in the `jtbd` extension under `CHECK_COMPUTABILITY_KEY = "check_computability"` (add to `INTERNAL_JTBD_KEYS`); set `condition.computable_checks` to the indices marked `computable` or `partial`; append `needs_field` names to `missing_reads` in Entity.field form so `jtbd_data.map_missing_reads()` and the schema backlog see field names rather than prose. Keep the writer's own `computable_checks` only as a fallback when the pass is off (`template.computability: bool`, default false).
Intent: `[]` stops being terminal; partial checks (the 65% cap without the listing-price basis) get coded; the schema backlog becomes a field list.

File: `jazzx_sdk/pipelines/policy/code.py`
Anchor: `job_segment()` and `JOB_SCOPE_NOTE`.
Change: for a `partial` check, render the sub-predicate as the check to encode and the residue under `CHECKS LEFT TO A REVIEWER`. `codable()` is unchanged in form; it now admits the jobs the pass marked.
Intent: partial code with an honest scope.

File: `jazzx_sdk/pack/ledger.py`
Anchor: `_disposition()`.
Change: when the job carries `check_computability`, count `partial` as computable for the `code` vs `code_and_procedure` split, and add a column to the Jobs sheet (`ledger.py` ~line 647 header list) `needs fields` listing the `needs_field` names.
Intent: the coverage workbook says which fields would unlock which jobs.

Tests: new `tests/test_jtbd_computable.py`: a job with reads {`listed_for_sale_last_6_months`, `occupancy_subtype`, `is_vacant`} and the check "if listed and investment then tenant-occupied and not vacant" comes back `computable` from a stub judge and `computable_checks == [0]`; a check marked `needs_field: SubjectProperty.lowest_listing_price_usd` lands in `missing_reads` verbatim. `tests/test_ledger.py`: a `partial`-only job with code is `code_and_procedure`, not `not_computable`.

### W5. Code that says what it left out, and reads derived fields

File: `jazzx_sdk/prompts/files/policy_code/job_prompt.md`
Anchor: the sentence allowing `(bool, dict)`.
Change: require the dict form when any check is left to a reviewer: `{"decided": [check texts], "left_to_reviewer": [check texts]}` on every return path except `rules_lib.unknown`. Version 1.1.0.

File: `jazzx_sdk/pack/ledger.py`
Anchor: the per-rule row written beside the job (where `disagreements` and `figures not printed` are filled).
Change: a `left to reviewer` column read from the rule's `check_computability` residue (not from running the code), so a four-of-ten rule is labelled as such in the workbook and in `rule_view`.
Intent: a True from partial code is not read as a pass.

File: `jazzx_sdk/pipelines/policy/code.py`
Anchor: `PythonExtractor.__init__` `reads` and `_checked()`.
Change: accept `derived:<rule_id>` names in `reads`; `context_keys()` already keeps only declared names, so declare the derived names alongside the catalog ones when the job cites them, and render them in `described_fields()` as "a determination this pack makes: <skill of that job>". The assessment engine's handling of derived fields is out of scope here; this makes the code writer able to name them.
Intent: thirty rules stop re-deriving citizenship from `citizenship_status`.

Test: `tests/test_job_code.py`: a job reading `derived:acra-standard.identification_requirements.foreign_national_status` passes the static check when the draft reads it.

### W6. Fold that folds, and coverage by check

File: `jazzx_sdk/pipelines/policy/jtbd_fold.py`
Anchor: `fold_duplicates()` pair filter and `_text()`.
Change: drop the `_kind(a) != _kind(b)` skip (keep the figure test); score on checks (`" ".join(condition.checks)`) rather than description + purpose, with description + purpose as the tie-breaker when checks are empty; when a judge is asked, show it the clause ids both jobs cite (from W2's per-check units) with the text. When two jobs of different kinds fold, the survivor keeps the kind the template ranks as stronger (`limit` > `determination` > `verification` > `condition` > `judgment`) and a note records the other. Bump `FoldConfig` with `by_checks: bool = True`.
Intent: the Platinum listed-for-sale restatements (three sections, different kinds, same checks) fold.

File: `jazzx_sdk/pack/ledger.py`
Anchor: the coverage report builder (the code that fills `coverage_trial.xlsx`'s Summary and Jobs sheets).
Change: add a `Clauses` sheet: one row per unit label/citation in the run, the jobs whose `check_units` cite it, and `checked` yes/no. A unit cited by jobs but by none of their checks is a gap row. Add to Summary: units, units checked, units cited only.
Intent: citation coverage (116 of 123) stops standing in for check coverage; the declining-market clause shows as a gap.

Tests: `tests/test_jtbd_fold.py`: two jobs of kinds `limit` and `verification`, same checks, different sections, fold with `how == "overlap"`. `tests/test_ledger.py`: a unit cited by a job but by none of its `check_units` appears on the Clauses sheet with `checked == no`.

### W7. Export in the consumer's shape

File: `jazzx_sdk/pipelines/policy/jtbdset.py`
Anchor: `export_jtbdset()` `section = ...` and `_render()`.
Change: section from the job itself when the policy has none: the `jtbd` meta `section` if set, else the second-to-last `rule_id` segment titled (the same rule `jazzx_sdk/pack/ledger.py::_section()` uses; move that helper to `jtbd_shape.py` and use it in both). In `_render()`, number steps from the template's `step_outline` when a step's first line is "Step N - <stage>: ..." (the shape the writer produces): emit `### Step N - <stage>` then the body, under one `## Steps` heading, so the export matches `requirement_template`. When the job has `reads` and `check_computability`, render Deterministic Validation Rules as `- <Entity.field> <relation> <figure>: TRUE = pass, FALSE = fail` for computable checks (from the sub-predicate text the W4 pass returns) and prose for the rest. `loan_metrics` already pass through `_META`; confirm the writer is asked for them (`_shape_guide` only asks when `template.metric_keys` is non-empty, which `bound_to_catalog` fills) and add a lint finding in `jtbdset_lint.py` when a job of kind `limit` exports no metric.
Intent: the exported set reads like the hand-built one to KStudio.

Tests: `tests/test_jtbdset.py` and `tests/test_plato_jtbdset_export.py`: an extracted job under `acra-standard.appraisal_review.x` exports `section == "Appraisal Review"`; a step "Step 2 - Eligibility Verification: ..." exports under `### Step 2 - Eligibility Verification`.

## Order

W1 and W2 first (small, prompt plus `_candidate`, and everything else reads their outputs). Then W4 (the gate), W6 (fold and the Clauses sheet), W7 (export). W3 and W5 last; they are the only ones that add a model pass and a new read form, and they can ship behind their template flags.

## Acceptance checks (run on a regeneration of `acra-dscr-policy` with the same inputs)

- Citations spanning more than one section: Standard 18 of 46 today; target under 5. Platinum 23 of 35; target under 5.
- Jobs from the Platinum listed-for-sale clause: 32 today; target under 8, with one determination (`listed for sale`) and the per-condition jobs citing it.
- Near-duplicate pairs (check-text Jaccard >= 0.6): 13 and 22 today; target under 5 each after fold.
- Jobs with reads and `computable_checks == []`: 56 and 19 today; target under 10 each, the rest reclassified `partial` or `needs_field`.
- Coded jobs: 43 and 56 today; target 70 or more each, with `left to reviewer` filled on every partial rule.
- `loan_program_eligibility.matrix_fico_and_cltv.python` resolves the loan-amount tier (its source no longer votes across three tables); the case $1.2M, 700 FICO, purchase, 78% CLTV returns True.
- Clauses sheet shows STD-1.14 / STD-8.4 (declining market) and PLAT-1.17 / PLAT-7.3 as `checked == yes` or as explicit gap rows; no clause is reported covered by citation alone.
- Export: every job's `section` is one of the template's eleven; steps are numbered; `loan_metrics` present on every job of kind `limit` or the lint names it.
- Existing tests pass: `tests/test_policy_jtbd.py`, `test_jtbd_fold.py`, `test_jtbd_data_mapping.py`, `test_job_code.py`, `test_ledger.py`, `test_jtbdset.py`, `test_plato_jtbdset_export.py`, `test_policy_extraction_prompts.py` (prompt version bumps are asserted there).

## Decisions needed before W3/W5 ship

1. Catalog: bind `acra_dscr_policy/jtbd_template.yaml` to the canonical object schema (the `Canonical_Object_Schema_Specification_v1_0` entities) with the current 47 fields declared as derived determinations over it. This needs the canonical catalog as a JSON Schema file in the pack; `JtbdTemplate.bound_to_catalog()` and `catalog_reads()` already consume that form. Without it, W4's `needs_field` names will point at fields no catalog holds and W5's derived reads are the only new vocabulary.
2. Document-presence fields: whether `DocumentRegistry` exposes per-type presence and key attributes as readable fields (`Documents.<id>.present`, `.issued_date`). Most uncoded verifications wait on this.
3. Open points (corrected 2026-10-22: both JTBD sets were written from the same consolidated guidelines, so this is not an input choice). Whether the writer is told to decide a check on the printed text and carry a Q-xx question as an open item on the job, rather than writing "do not resolve" steps and a missing-data line that also blocks code. A prompt line in `write_prompt.md` plus an `open_items` list in the `jtbd` extension; small enough to fold into W4.
