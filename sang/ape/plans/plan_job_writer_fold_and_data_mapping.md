# Plan: job writer folds duplicate jobs across sections and maps missing data to catalog fields

Status: plan, not built. Branch `v2.6.3` (SDK 2.6.3, Plato 0.2.4), local. Owner sonnet-runtime.
Source: Acra regeneration 2 (`local/coverage/regen_2/`, trial `acra-regen-2`: 130 jobs against Acra's 128, code decides
at least part of 58%, lacks data 34%); `plan_programme_oct.md` (opus-xrepo open items); `plan_document_registry_and_job_shape.md`
(D1-D4, the job shape this extends). Prior art read: `pack/jtbd_match.py` (content matching across two sets),
`pack/text_similarity.py`, `pack/ledger.py` (coverage rows, `schema_backlog`), `pipelines/policy/jtbd.py`.

## 1. What the regen shows (270 job rows over the sets)

- **Duplicates across sections.** Jobs are written one section at a time (`JtbdExtractor.extract(segment)`), so a rule
  stated in two sections is written twice. In regen 2, 45 pairs of jobs in different sections of one policy have
  description token overlap (Jaccard) of 0.6 or more; the top ones are verbatim or near-verbatim: the 65% maximum LTV
  check in the asset and liabilities sections, "not in an ineligible location" in appraisal review and loan program
  eligibility, and several "listed for sale within six months" checks (impounds, amortization, subordinate financing,
  prepayment term) between appraisal review and liabilities. Each duplicate is a second job to maintain, to run and
  to pay for, and a second row in Acra's comparison.
- **Missing data that names a catalog field.** A job's `missing_reads` is free text the writer produced because the name
  it wanted was not in `template.reads`. The coverage `schema_backlog` is that text counted: "calculated DSCR" 11 jobs,
  "DSCR" 8, "LTV" 8, "FICO" 5, "Application Date" 3, "Closing date" 3, "Purchase price" 3. Most of these have a catalog
  field. Each one that does should be a `read` (so the job becomes computable), not missing data.
  (The separate `unsupplied_reads` list, such as `LoanCore.cltv_percent` in 60 jobs, is about case data the extraction does
  not yet fill; it is not this plan.)

## 2. Design

Both are code over the writer's output, not prompt changes, so they are deterministic, cost no tokens where lexical
evidence is clear, and apply to any pack. Settings are pack data in `jtbd_template.yaml` (`fold:` and `data_mapping:`
blocks, all optional; absent means today's behaviour). Tolerant first: each action is recorded on the job and surfaced;
`strict:` per block makes a doubtful case refuse instead.

### F. Fold duplicates across sections

New `pipelines/policy/jtbd_fold.py`, run once over a policy's candidates after every section has been written (the
extraction run already holds them all before the proposals are stored; the single-requirement ledger writer is untouched).

1. **Candidates.** Pairs of jobs of the same policy in different sections, of the same kind. Score by the description's
   token Jaccard, the shared `reads`, and the same figures (`text_similarity.figures`, so "65%" and "75.00%" never fold);
   a pair needs the same set of figures.
2. **Decision.** Score at or above `accept` (default 0.8, as the `match_items` convention) folds without asking; between
   `ask` (0.6) and `accept` goes to a model judge when the extraction has one ("same requirement, yes or no"), and is left
   alone when not (recorded as a possible duplicate). The judge is the same seam `jtbd_match` uses.
3. **Fold.** One job survives: the one in the section whose type or name best fits the requirement (the pack's
   `section_types` order, else the first). It keeps its id and gains the other's cited units and citations (so it cites every
   clause that states it), the union of `reads`, `evidence_types` and `missing_reads`, and the stricter `action`. Its
   `domain_extensions.jtbd` records `folded_from: [{id, section}]`; the dropped job's id is not reused. The reasoning
   line says what folded and why. The dropped job never reaches the proposal store.
4. **Surface.** The run's result lists folds and possible duplicates; the coverage page and workbook get a "Folded" column
   and count. A rerun that finds the same pair folds it the same way (stable survivor by the rule in 3).

### M. Map missing data to catalog fields

New `pipelines/policy/jtbd_data.py`, run per job after it is written (so it also serves the single-job rewrite).

1. **Match.** Each `missing_reads` string is matched to the template's catalog: field names and `Entity.field` keys, with
   the catalog's descriptions when it has them. Normalise (case, spacing, `_`, a trailing "amount" or "date" word kept),
   exact and token-set match first, then the closest field by token overlap; a clear single winner is taken.
2. **Move.** A mapped string leaves `missing_reads` and its field joins `reads` (when the template's `reads` holds it).
   `computable_checks` is recomputed only where the writer stated none (it stays the model's claim otherwise), and the
   job's note says "data mapped: <text> -> <field>".
3. **Close calls and no match.** A close call goes to the model judge when one is given, else it stays missing data with a
   note naming the candidate. No match stays missing data (it is the schema backlog, which is the right place for it).
4. **Derived data.** "Calculated DSCR" names a derived figure: when the pack's `kinds` has a determination kind that maps to
   `DERIVED_FIELD`, a mapped string that the catalog holds as a derived field is read through it; otherwise nothing special.

### Placement and contract

- `JtbdExtractor` gets `data_mapping` applied inside `_candidate` (a per-job step); folding is a function over
  `list[RuleCandidate]` called by the run after the segment loop, and by nothing else.
- No change to `Rule`, `ProcedureCondition` or the coverage row shape beyond: `folded_from` in the job meta, a `mapped_reads`
  note list, and two coverage columns.
- Prompts: none. (If the writer still emits many unmappable strings, that is a prompt question for later, with the numbers.)

## 3. Build order (one commit each, tests first)

1. M: matcher, move, note; tests on the regen's own strings (the strings above) against a small catalog fixture.
2. F: pair scoring and fold; tests on the verbatim pairs, the different-figures pair that must not fold, the survivor rule,
   the citations union.
3. Run wiring, the result lists, the coverage columns and sheet, client fields.
4. CHANGELOG with line counts, plan to `status/` on landing.
5. Then opus-xrepo reruns the regen and compares to regen 2: job count, partial share, `schema_backlog` size, duplicates.

## 4. How we know it helped (the numbers, not a claim)

Regen rerun against regen 2 (same documents, same models): jobs (130 now; Acra 128), pairs of 0.6+ overlap across sections
(45 now; target near 0 for the verbatim ones), `schema_backlog` entries that name a catalog field (target 0), computable
share (code decides at least part: 58% now). A fold that merges two jobs Acra keeps apart shows as a regression in the
Acra comparison and is reported.

## 5. Not in this plan

Folding within a section, merging different-figure variants (those are the variant dimension), the unsupplied-reads list,
the model-written prompt changes, per-program deduplication across policies.

## 6. Decisions owed

1. **Post-pass, not prompt.** Code over the output (recommended), or also a second prompt listing the catalog fields with
   descriptions so the writer names them itself?
2. **Thresholds.** Fold at 0.8 and ask a judge from 0.6 (recommended), or fold only verbatim (1.0) and list the rest?
3. **Survivor.** The job in the section the pack's `section_types` ranks first, else the first written (recommended), or the
   one with the most reads?
4. **Judge cost.** Use a model judge for close calls (recommended: in regen 2, 17 pairs score 0.8 or more and 28 between 0.6 and 0.8, so about 28 judge calls),
   or lexical only and a possible-duplicate list?
5. **Strict.** A per-block `strict:` that refuses a doubtful fold or mapping (recommended), or none?

## 7. Built (2026-10-15, `v2.6.3`, `d514b989`, `7503dc7f`, `6bb516c0`)

All five decisions as recommended. Deviations:
- Strict means only a clear lexical match is applied; a judge's answer is never applied (not "refuse a doubtful case").
- The surviving job keeps its own `action`; the plan said the stricter, but actions have no order to compare by.
- Matching reads the catalog's bare field names only (`template.reads`); it does not see descriptions, because the
  template does not carry them. A text whose words are a part of a field name ("LTV" for `ltv_percent`) is a close call.
- No judge for a pair the same figures rule excluded; a pair with different figures is never listed.
- The blocks are pack data: a pack opts in by adding `data_mapping:` and `fold:` to its `jtbd_template.yaml`. The Acra
  seed is synced from the pack's owner, so the regen's trial pack needs them added there (snippet in the hand-off).
