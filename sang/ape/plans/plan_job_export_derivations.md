# Plan: the rule-derivable parts of a job and its export (sonnet-runtime, 2026-10-29)

Plan only, no build, no spend. Source: sonnet-packs' `note_acra_vs_ours_differences_and_provenance.md` (sections C and D),
read against the code on `v2.6.7`. It folds into the job-identity work (P1, P2, P4 are in) and the aggregate-kind note.
Every piece below is derived from structured fields by code; the model fills fields, never the format.

## 1. What exists, what does not (read on v2.6.7)

| Piece (their convention) | Today | Gap |
|---|---|---|
| Prefix acronym, slug uniqueness | `fallback_prefix` (a section with no family), `mnemonic_for` (topic walk, 20 chars, never a number, unique) | a *topic-group* prefix needs a group name; the group is a judgment (pack data: `mnemonics.families` per section already takes several families). Reuse `fallback_prefix` on a declared group name: ~0.25 day, folded into item C |
| `sequence` | read on import (`_META`, priority); nothing assigns it on generation or export | assign it (below, B) |
| Requirement template (title, `### Step N - name`, `---`, DVR `TRUE/FALSE`, `### Pass` outcomes) | `_render` (`pipelines/policy/jtbdset.py:152`) writes `## Step N`, plain checks, `- **Pass**:` bullets | a guide-style renderer, opt-in per export profile (D) |
| `entity_types` | the writer proposes names, code keeps those in the template catalog | derive from the job's reads and metric keys (C) |
| `loan_metrics` | the writer proposes, code keeps keys in `template.metric_keys` | derive key, `_LM<N>` mnemonic, `{field}` description from the reads (C); label, threshold phrase, `calculation_context` stay model |
| Investor blocks | `programs` overlays, absent ones `NO_CHANGE` | nothing (their 4 of 5 blocks are empty; ours are program sets) |
| `notes` "Ontology gap" | none | emit when a read has no metric key (C) |
| Clause-to-job links | `coverage().clauses` has `cited_by`/`checked_by` as rule ids; the K-Studio sets carry no citations | key them by the job's exported mnemonic (A) |

## 2. The pieces, with sizes (all offline, no spend)

**A. Clause links keyed by mnemonic (0.5 day).** sonnet-packs' comparison keyed the clause-to-job map by position and linked 3 of
108 jobs. The SDK's `compare_clauses` keys by rule id, while an exported job is named by `jtbd.mnemonic` (else the rule id).
Add one resolver, `job_ref(rule)` = mnemonic else rule id, used by `ClauseCount` (`cited_by`, `checked_by` carry both) and by the
alignment rows, so a clause row lists the exported ids a reader sees. Test: a pack whose jobs have mnemonics lists them.

**B. `sequence` (0.5 day).** A pure function over a pack's jobs: within a section, a job's number is the rank of the
guideline position of the first clause it checks (the units are numbered in guideline order: `U1..Un`), ties by rule id; written
as `jtbd.sequence` at generation and stamped by the export when missing, the number only (the order is the guideline's). Test
offline on regen-5's rules: every job gets one, stable across runs; sonnet-packs' Spearman against theirs is then measurable.

**C. Derived metadata (1.5 days).**
- `entity_types`: the distinct catalog entities of the job's reads and metric keys, each with the template's per-pack description
  (`template.entities` already holds them), replacing the writer's list when the job reads a catalog field.
- `loan_metrics`: for each read that has a catalog `Entity.field` in `template.metric_keys`: `metric_key`, `metric_mnemonic`
  `<MNEMONIC with _>_LM<N>` (the 50-char cap stays), `description_template` with a `{field}` per key, `indicator_context` from the
  profile's fixed sentences plus the check's threshold. The profile text is pack data (Acra's are the guide's own example
  sentences); nothing is hard coded.
- `notes`: `Ontology gap: <read>` when a read has no metric key (59 of their notes say so).
- Group prefix: a job's `group` (pack data or the planner's field when it gives one) feeds `fallback_prefix`; no group, the
  section's prefix as now.
- Measured offline on regen-5's 195 jobs and compared with the counts in the note (their entity_types and metrics per job); the
  writer's own lists are the baseline.

**D. The guide's requirement template (1 day).** `_render` gains a style (`export_profiles/*.yaml: requirement_style: guide`;
default unchanged): `### Step N - <name>`, `---` between sections, each check as `<condition>: TRUE = pass, FALSE = fail`, outcomes
as `### Pass` with "Assign **Pass** when:" and the "There is no case for this outcome" line. The import side must round-trip
(`_SECTION`, `_WRITTEN_STEP`, the source-text digest); tests: render, then `import_jtbdset`, then render equal; a parser check of
their heading order on every job. Risk: a check that is not an observable condition renders a poor TRUE/FALSE line; the render
says nothing for a check without a condition and the lint reports the job.

**E. Aggregate kind, no-spend half (1 day, after the above).** The `aggregate` block as pack-authored job metadata, its lint
(`aggregate_contributor_missing`, open readings named), the export of the block, and the conditional flag from `open_readings`.
The writer producing the block waits on the user's writer-prompt decision (g); until then packs author it as data.

Total about 4.5 days, no spend. Order: A, B, C, D, E (A unblocks sonnet-packs' sequence measurement; B and C are no-risk
additions to the generator and the export; D touches the export format, so after the data pieces; E last because the writer half
waits). The identity regen measurements (about 0.65 USD, the user's approval) are independent; C and B are also measured on the
existing regen-5 rules without any run, so they need no new spend.

## 3. Needs judgment, not derived

- Topic grouping (which jobs share a prefix): a clustering choice; the SDK derives only the acronym and its uniqueness. The group
  is pack data (`mnemonics.families`, a job's `group`).
- Aggregate governing-cap jobs (E): which caps govern is the clause's statement or the user's reading; the SDK carries the
  block and the open readings, never picks one.
- Where to split a matrix or a document list: the row count of a clause table is countable; the split is a design choice. A
  lint can report a clause table with n rows and one job (`table_rows_one_job`); the split stays the writer's or the pack's.
- Fill or refer a figure the guideline leaves open: the user's reading (the readings file), not a rule.

## 4. Not in this plan
`figure_lint.py` (sonnet-packs' script, queued for 2.6.7 with its ledger links), the writer prompt edit and `slug` field (the
user's decision), A and E of the workspace plan (held).
