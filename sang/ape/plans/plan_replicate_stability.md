# Replicate stability on experiments (sonnet-runtime, 2026-10-17)

Exists: `noise_floor_from` on a comparison (a completed repeat of the baseline: same entity, same dataset) turns the
repeat's per-case score differences into a noise floor. Missing: a report over N repeats of one variant (more than the
single pair a noise floor needs), per metric and per case.

## Design
- `experiment_stability(experiments: list[Experiment]) -> StabilityReport` (SDK, `evaluation/stability.py`): refuses
  runs that are not repeats of one entity, config and dataset digest. Per metric: mean, standard deviation, min, max
  over the repeats' aggregate score. Per case: how many repeats passed, and a **flip** when the verdict differs across
  repeats; the report lists the flipping case ids and the flip rate (flips / cases). Output also carries each metric's
  `unstable` flag against a named threshold constant (spread over mean), tolerant first: a flag, not a refusal.
- Route `GET /eval/experiments/{id}/stability?repeats=id,id,...` (default: every completed experiment sharing the
  entity, config digest and dataset digest) and the comparison reads the same report for its baseline.
- Xlsx sheet in the comparison export (metric rows, flipping cases).
- Client `experiment_stability`; the page (sonnet-ui) draws the table.
## Tests
Two identical repeats: zero spread and no flips; one flipping case is listed; mixed datasets refused by name;
a single run answers "needs at least two".
## Not built
Cross-model variance, significance tests beyond the existing stats module.

## Delta 2026-10-20: variant-by-case matrix, spans and the comparison-versus-range rule

From a read of a sibling's comparative report renderer (a version-by-loan matrix over repeated runs). Improved on, not copied; the
plan below is consumer-neutral and names no source. What it shows we lack: our reports show one number per variant, and the
stability report above covers one variant's repeats only. What it hard-codes and we must not: the version list, the case list,
series labels, collection over ssh, literal row-count assertions (172, 95, 77) standing in for "same dataset", and a hand-written
verdict paragraph.

1. **Stored per-run record** (SDK, beside `evaluation/stability.py`): `RunRecord{run_id, variant, repeat_group, dataset_digest,
   config_digest, code_revision (+ dirty flag), status, cost_usd, seconds, cases: {case_id: {n, d, verdict}}}`. Written from what
   an experiment already holds (usage, duration, per-case scores); a regeneration or a case run writes the same record from its run
   record. "Same dataset" is the digest, not a count. A run that did not finish OK is kept and shown, excluded from spans with its
   reason (the source refused the whole report; we show and exclude).
2. **Span statistics, per metric and per variant**: n, mean, min, max, standard deviation; rates keep n and d per run and the span
   is of the per-run rate; a variant whose runs disagree on d is flagged (a denominator that moves is itself a finding); n=1 reads
   "one run, spread unmeasured" and never a span. Cost and seconds get the same span (mean, min to max). Per case: the pass count
   over repeats and a flip flag (already in this plan); the matrix cell shows the case's min to max.
3. **Comparison versus range** (the rule the two-arm regeneration and the e2e variants use): a contrast is computed between a
   baseline variant and each other, generated from a declared order, not hand-picked pairs. Verdict is one of `separated` (the two
   runs-ranges do not overlap, with the gap and its direction), `overlapping`, `unmeasurable` (either n=1). A move is claimed only
   when `separated` with n>=2 on both sides. When a variant's runs span more than one code revision the cell says so (the revision
   set comes from the records, not from a note). Mean change is shown beside the verdict, never instead of it. The verdict is
   rendered by code from the numbers; there is no authored conclusion paragraph.
4. **Matrix view for Plato's comparison and release reports**: rows are variants, columns are cases, each cell the case's score
   with its min to max over repeats, plus per-variant columns for total score (span), cost (span), seconds (span), runs, failed
   runs and revisions. One xlsx sheet ("Variants by cases") in the comparison export and one table in the release report; the same
   shape feeds the end-to-end variant report (V1 to V5, hybrid, both) and a regeneration's arms, whose first consumers are the two
   slice-1 arms (variant = arm, one repeat each).
5. **Chart**: a range-bar per variant (min to max with the mean marked), baseline range shaded so overlap is visible; page work
   for sonnet-ui over the same JSON, the SDK ships the numbers and the verdicts, not an SVG.
6. **Tests**: spans over fixed records (n=1, n=3, differing d); the three verdicts including a touching boundary (equal edges
   overlap); a runs-range spanning two revisions is flagged; a run that failed is excluded and listed; two datasets (different
   digests) refused by name; the matrix sums equal the per-variant totals.
Effort: S-M on top of the stability report (records and spans M, matrix and route S, xlsx S). Page work follows with sonnet-ui.
