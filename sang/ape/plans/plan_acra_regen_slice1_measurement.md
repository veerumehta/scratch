# Acra regeneration after slice 1: checklist, measurement plan, noise, cost (sonnet-runtime, 2026-10-20)

Runs once slice 1 (steps 1 to 5 of `plan_job_writer_quality_slice1.md`) is built and reviewed by me. Nothing runs before the
user's go for the spend. Policy documents only; no loan files; outputs only under the ignored Acra folders
(`scripts/local/coverage/regen_4*`, `docs/status/Acra/`).

## 1. Checklist (one variable: our code)

1. Same input as the baseline `acra-regen-3b`: the synced seed `plato/data/seed_packs/acra_dscr_policy` (consolidated
   guidelines v1.0). No source change.
2. Same template flags as 3b: `ACRA_TEMPLATE_EXTRA=/Users/sangit/src/.scratch/sang/ape/local/acra/acra_template_extra.yaml`
   (the `/tmp` copy is gone): `fold: {accept 0.8, ask 0.6, judge true}` and `data_mapping: {accept 0.8, ask 0.4, judge true}`.
   Slice 1 adds no template flag; `section_definitions` stays unset, so the planner gets the family descriptions (the
   consumer's own words, already in the seed's `mnemonics.families`).
3. Local Plato must run the slice-1 code. The running process predates `v2.6.5`: it needs a restart from the shared checkout
   (`v2.6.5`, tree clean at that point). I do not restart it; opus-xrepo does, or says so.
4. Harness: the existing `scripts/local/acra_regen.sh <trial-pack-id> <out-dir>` (seed, 4 extractions, merge-jobs, code,
   align, coverage), with `ACRA_TEMPLATE_EXTRA` set, trial id `acra-regen-4a` (repeat: `acra-regen-4b`), out
   `scripts/local/coverage/regen_4a`. Phases append to `regen_log.jsonl`. The harness records failed segments only in its log:
   after the run, retry connection-error failures with `acra_ledger_live.py retry-failed` (as for 3b) and say so in the table.
5. Copy the trial's job files to `regen_4a/jobs/` (as `acra_bundle.py` does) so the measurement reads files, not Plato.
6. After the run: `scripts/local/costs/acra_cost_ledger.py` (no model spend), then the before/after note under `docs/plans`.

## 2. Measurement

Reader: `scripts/local/acra_regen_measure.py <dir>` (written now, files only). Run on the 3b bundle jobs it reproduces the
assessment's numbers exactly (Standard 18 of 46 citations span sections, worst citation 16 jobs, 13 near-duplicate pairs, 56 jobs
with reads and none computable; Platinum 23 of 35, 32, 22, 19), which is the check that the reader measures what the plan means.
"Platinum listed-for-sale job count" is measured as the most jobs one citation has (32 today), with no Acra phrase in the
measure; `--clause REGEX` stays available.

| Metric | Baseline (3b bundle; regen 2 where noted) | Slice 1 expected to move? | Target |
|---|---|---|---|
| Citations spanning more than one section | Std 18/46, Plat 23/35 | Yes (W1) | under 5 each |
| Most jobs from one citation | Std 16, Plat 32 | Yes (W1) | Plat under 8 |
| Near-duplicate pairs (check Jaccard >= 0.6) | Std 13, Plat 22 | Partly (W1; fold change is later) | under 5 each is the plan's number; the fold half is not in this slice, so read a smaller drop honestly |
| Clauses sheet: units, checked, cited only | none (new) | Yes (W2, W6a) | a first measurement; every declining-market-style clause shows as checked or an explicit gap row; no clause reported covered by citation alone |
| Jobs that cite all units of their section (fallback taken) | not recorded | New note count from W2 | the share the writer names no check units for |
| Unwritten code by reason (static_check, cases_failed, transient, uncodable) | not recorded (built after 3b) | First measurement (code yield 1-2) | none; baseline for the next run |
| Case mismatches kept on rules, disagreements, unprinted figures | 3b: disagreements 6 to 9, unprinted jobs 10 to 13 | First measurement of cases-before-accept | informational |
| Coded share (code + code_and_procedure) | regen 2: 0.556; 3b: 0.475, 0.500 after retry | Secondary (fewer duplicate jobs, headings reach the writer) | not an acceptance number |

Read from the run records (read-only API on the run ids in `state.json`) for the `unwritten` reasons; from the rules' ledger keys
for case mismatches.

NOT expected to move in this slice (later workstreams): jobs with reads and no computable check (56 and 19: W4), left-to-reviewer
labelling and partial-check code (W4, W5), `derived:` reads (W5, behind an engine plan), consolidation determinations and
aggregators (W3), export section, step numbering and metrics (W7), fold across kinds (W6 fold change), data vocabulary and
document-presence fields (the catalog decision). The matrix-rule acceptance case ($1.2M, 700 FICO, purchase, 78% CLTV) is W2's
headings-in-the-clause effect: expected to improve but it is a spot check, not a counted metric.

## 3. Noise

Baseline variance is thin: regen 1 gave 110 and 159 jtbd proposals for Standard on two runs the same week, regen 2 gave 130, 3b
121; coded share was 0.556 (regen 2), 0.475 and 0.500 (3b, 12 jobs lost to connection errors). The replicate-stability plan does
not supply a bar: it scores repeated experiment cases (per-case flips), not extraction counts.
Judgement rule, proposed:
- Structural properties W1 enforces in code (a unit sits in one section; `shared_units` records the rest) are deterministic: one
  run decides them (citations spanning sections must fall to near zero, not "by a margin").
- Statistical metrics (near-duplicate pairs, the worst citation, jobs, coded share, unwritten counts): run the after arm twice
  (A1, A2). A movement is claimed only when both A1 and A2 lie outside the range of the historical baselines (min to max of
  regen 1, 2, 3b) and the baseline-to-after gap exceeds |A1 - A2|. Otherwise it is reported as "within noise".
- A repeat costs about what the run costs (below) and about 1.5 to 3 hours, so the second arm is worth taking: one decision for
  the user (a single run answers the structural question only).

## 4. Cost and time estimate

Source: regen 2's Acra cost ledger rows (the model is `flex_gpt-6-luna` throughout) and the 3b run records (`runs.json`; the 3b
ledger rows are not in the ledger yet, which the rebuild fixes). Per full regeneration:

| Phase | Cost | Elapsed |
|---|---|---|
| jtbd extraction (2 policies) | 0.053 (3b records: 0.026 + 0.025) | 20 to 60 min (parallel) |
| segment code extraction (2 policies) | 0.061 (3b: 0.037 + 0.026) | 50 to 110 min (the long pole; parallel with nothing after jtbd) |
| code from jobs (2 policies) | 0.087 | 35 to 40 min |
| alignment | 0.026 | 6 min |
| retry of connection failures (3b: 10 segments) | about 0.02 | 5 to 10 min |
| Total | about 0.23, 0.25 with the retry | 1.7 to 3.1 hours wall clock (regen 2: extraction alone 140 min; 3b: 66 min) |

Slice 1 adds no model call (W1 and W6a are model-free; W2 asks the writer for `check_units`, a few output tokens per job), so
the estimate for slice 1 is the same plus under 5%: about 0.25. A repeat costs the same. Two arms: about 0.5 and 3 to 6 hours,
mostly waiting; the spend is cents because the model is the cheap flex tier. The ledger rebuild and the measurement cost nothing.
Open risk, from 3b: provider connection errors lost 12 code jobs while the run reported success; budget one retry phase.

## 5. After the run

Rebuild the ledger; write `docs/plans/note_acra_regen_slice1_results.md` with the before/after table and the A1/A2 spread;
update the CHANGELOG line counts if the run changes nothing in code (it does not). Never push.
