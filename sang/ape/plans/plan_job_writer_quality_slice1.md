# Job-writing quality, first slice: one unit one section, per-check units, coverage by check (sonnet-runtime, 2026-10-20)

Scope (opus-xrepo, user-approved routing): the first slice of `plan_JAPES_2_9_0_JOB_WRITER_COVERAGE_AND_CODABILITY.md` (read with
`Acra_JTBD_and_Code_Generation_Assessment.md`): W1, W2, and the coverage-by-check half of W6. Folds into 2.6.5; ignore the 2_9_0
name and any bump. W3, W4, W5, W7 and the fold change of W6 come later; nothing is built until this plan is answered. No
regeneration or model spend without the user's go.

User directive: no overfitting to Acra. Nothing below names an Acra section, mnemonic, figure or program in SDK code or prompts.
Behaviour that depends on a template reads it from the template or pack, and with no template extras every item still works
(tolerant first: proceed, record, surface). The Acra numbers in the source plan are acceptance data for one regeneration.

## Anchors at HEAD (v2.6.5, `77aba87b`..tip)

Hold (lines shifted by up to 10): `SectionSegmenter.segment` (`jtbd.py:276`, `grouped.setdefault(_slug(planned.name), ...)`, `assigned`
used only for `leftover`); `JtbdExtractor._candidate` (`cited = [...] or segment.parts` :544; `computable = None if reads else []`
:561; clause joined from `p.text` :569, stored under `LEDGER_KEY/CLAUSE_KEY`); `_DraftJob.computable_checks`/`source_units`
(:346/:351, per job, no per-check); `fold_duplicates` (`jtbd_fold.py:197` skips same section, different `_kind`, different figures;
scored on `_text()`); `code.codable` (:103) and `job_segment` (:83, renders `job_clause(rule)` whole); `ledger._disposition`
(`pack/ledger.py:437`); `extract.py:601` `extractor.fold` runs once after all sections; `plan_prompt.md` v1.0.0 line 6 ("may belong
to more than one"); `write_prompt.md` v1.2.0; `jtbdset.py:294` `section = ... or policy.name`.

Drift, to be built around:
1. `mnemonics.families` is `{section: {prefix: description}}` (`jtbd_shape.py:56`): descriptions are per prefix family, not per
   section. The source plan's "section descriptions from families" is wrong in shape. W1 below adds an optional
   `JtbdTemplate.section_definitions: {section: text}`, falls back to the joined family descriptions of that section, then to
   the name alone (today's behavior).
2. Unit labels (`U1..Un`) are assigned per run in document order (`jtbd.py:272`) and are not stable across runs. `check_units`
   therefore stores each unit's citation string (what the ledger's clause coverage is keyed by), with the label only in the
   writer's prompt.
3. The ledger clause is one joined string; "render only cited parts" needs the parts. W2 stores them structured (below).
4. The source plan's fold ranking (`limit > determination > verification ...`) and its consolidation prompt examples are
   mortgage vocabulary. Not in this slice; when W6's fold change comes, rank by the order of the template's `kinds`, and the
   consolidate prompts take their examples from the template, not the SDK.

## One definition of "covered by check" (shared with the code-yield and adjudication plans)

New module `jazzx_sdk/pack/coverage_by_check.py` (pure, no model): over a pack's jobs and the run's units.
- **unit**: a clause of a source document, keyed by its citation.
- **cited**: a unit in a job's `citations`.
- **checked**: a unit in `check_units[i]` of some job, for some check `i`.
- **cited only**: cited and not checked (the gap row).
- **decided by** (for a checked unit, from the job's own fields): `code` when check `i` is in `computable_checks` and the job has an
  implementing rule that was written (code-yield item 1's `CodeOutcome.reason == ok`); `procedure` otherwise (the check stays with a
  reviewer, or the rule was `cases_failed`/`uncodable`/`transient`/`static_check`, whose reason code the sheet shows).
A job with no `check_units` (written before this change, or imported) counts its citations as cited only; it never inflates
`checked`. Consumers: W6's Clauses sheet and Summary; code-yield's `unwritten` per job reads the same unit-to-job map so a gap
unit shows why its job has no code; the adjudication plan has no unit-coverage notion (its "cites" are evidence cites into case
documents, A1; A4 bins rules by section stem), so there is nothing to diverge today. A4's `bin_by_section` must use the same
section stem as `_section()` when it is built, and cite this definition if it ever reports coverage.

## Items

### W1. One unit, one section (S-M)
- `plan_prompt.md` 2.0.0: each unit belongs to exactly one section, the one whose jobs decide it; a unit supporting several goes to
  the section it most directly states a requirement for; each section's definition is given. `plan_instructions` untouched.
- `SectionSegmenter.segment`: keep a unit in the first section that claims it, record later claims on the segment
  (`shared_units: {unit citation: [other sections]}`); the loop stays a plain walk (no ranking model call).
- Taxonomy line: names plus definitions from `section_definitions`/families, per the drift note; no definitions, today's line.
- Tests: a plan listing U3 under two sections gives one segment holding it and `shared_units` naming the other section; a template
  with no definitions yields today's taxonomy line; one with families yields their descriptions.

### W2. Per-check units, headings in the clause, only what a check needs reaches the code writer (M)
- `_DraftJob.check_units: list[list[str]] | None`; `write_prompt.md` 1.3.0 asks for it ("for each check, the unit ids it decides").
  `_candidate`: `cited` = union of `check_units`, else `source_units`, else all parts as today, with a note when it falls back to all.
- Ledger extension keeps the cited parts structured (`CLAUSE_PARTS_KEY`: citation, heading, text per part, in order) beside the joined
  `clause`, which now renders a part's heading above its text when the heading differs from the marker (same rule as `_render_unit`).
  `jtbd` extension gets `check_units` (citations); both new keys go in `INTERNAL_JTBD_KEYS` (the export stays unchanged).
  `jtbd_fold._clause` and its merge (`:89`, `:168`) keep both keys when folding (a folded job's `check_units` is the union).
- `code.job_segment`: when the job has `check_units` and parts, render only the parts cited by checks it encodes (plus their
  headings); otherwise the whole clause as today. `CHECKS LEFT TO A REVIEWER` unchanged.
- Fixtures that assert exact clause text (`test_jtbd_fold.py`) gain the heading line. Prompt-version asserts in
  `test_policy_extraction_prompts.py` bump.
- Tests: a part with a heading appears above its text in the clause; fallback note when the writer names none; `job_segment`
  renders only the cited parts; fold keeps the union of `check_units`.

### W6a. Coverage by check: a Clauses sheet and Summary lines (M)
- `coverage_by_check.py` per the definition; `pack/ledger.py` builds it with the coverage report; sheet `Clauses` (unit citation, jobs
  citing, jobs checking, decided by, reason code when uncoded, status checked/cited only); Summary adds units, units checked,
  units cited only. `ClauseCoverage` dataclass on the report so the solution view and release report can read it later (sonnet-ui
  renders; no UI work here).
- Tests: a unit cited by a job but by none of its checks is a `cited only` row; a unit checked by a coded check says `code`, by
  an uncoded one `procedure` with the reason; a job with no `check_units` never counts as checked.

## Reconciliation answers (opus-xrepo's three points)
1. Coverage: one definition, above, in one module; code-yield and adjudication consume it, they do not define their own.
2. `derived:<rule_id>` (before W5): the assessment engine supplies one derived form today: `MetricDefinition`s in the assessment
   step's `metrics` file, evaluated over numeric inputs (`assessment._derive`, Decimal only) and added to the context by
   `definition.id`; a fact named there is exempt from the missing-input refusal (`_unstated_facts(..., derived)`).
   A determination's boolean verdict is not supplied to any other rule: `derivation_backlog` (`ledger.py:543`, jobs with
   `maps_to: derived_field` and no code) is a to-do list, not a runtime path. So `derived:<rule_id>` has no supplier; W5 must
   either lower a determination to a metric (only when expressible numerically from declared facts) or wait for engine work
   (a rule's outcome readable by name, with the refusal rules for it). Companion item 14's "map onto derived_field" is the same gap.
   Recommendation: W5 stays last and flagged; before it, a small plan for the engine side.
3. Companion item 9 (`data_mapping` with the full vocabulary): config, not an SDK workstream. The mechanism exists
   (`DataMapping`, `map_missing_reads`); its bar (`accept`, `ask`, `judge`) is already template-tunable. It only pays once the
   vocabulary is the full catalog (the source plan's decision 1); until then it maps against the 47-name list. Belongs as a line in
   the regeneration checklist (enable it in the trial template), and as W4's precondition, not a new workstream.

## Order and effort
1. Anchors re-run + `coverage_by_check.py` with its tests (S).
2. W1 (S-M). 3. W2 data model + `_candidate` + prompt + internal keys + fold union (M). 4. W2 `job_segment` (S).
5. W6a sheet and Summary (M). 6. CHANGELOG under [2.6.5], one commit per step, tests first, no regeneration.
Acceptance on a later regeneration (the user's go required): citations spanning several sections, `checked` vs `cited only` counts,
the Clauses sheet rows for the clauses the assessment names as unchecked. Not measurable without a run.
