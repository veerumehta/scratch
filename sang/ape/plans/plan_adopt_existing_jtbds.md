# Plan: adopt an existing job set against the guide's units, with no model call (sonnet-runtime, 2026-10-30)

Plan only, for opus-xrepo's review; nothing built. Queued after batched planning. No provider call anywhere in this path.

## 1. Units without a planner
`read_structured_corpus` already yields each chunk as a topic with path, pages and edition. Add `corpus_units(corpus) -> list[Unit]`: one unit per
topic, id from the chunk path (`B3-6-05`-style when the heading carries it, else the slug of the path), citation `<source>#<topic>` plus edition.
No `SectionSegmenter`; the units are the reference list a mapping resolves against and the rows the Clauses sheet counts.

## 2. Mapping format (a JSON/YAML document the host supplies; prepared by jaci)
```
{"edition": "June 2026", "links": [
  {"job": "LTV-CAP", "check": 0, "units": ["B2-1.5-01"], "source": "declared", "status": "declared"},
  {"job": "LTV-CAP", "check": 1, "units": ["B3-6-05"], "source": "rulemap", "status": "unreviewed", "p": 0.91,
   "quote": "...", "path": "B3 > B3-6 > B3-6-05"}]}
```
`check` is the zero-based check index (omitted: the job's units as a whole, the same grain `CHECK_UNITS_KEY` has when a job has one check).
`source` names where the link came from (`declared`: the job set's own cited topic ids; `rulemap`); `status` is the only field coverage reads,
and has three values: `declared` (the set's authors stated it), `unreviewed` (a model's verdict, no person has looked) and `reviewed` (a person
confirmed an unreviewed link, by re-importing with the status changed; the row must carry `reviewer` and `date`, kept in `CHECK_LINKS_KEY`, else the
import refuses it). Declared and reviewed count alike.

## 3. Writing
`adopt_unit_links(policies, mapping, units)` (pure, no I/O): resolves each unit id against the corpus (an id with no unit is an error row, never
dropped), writes `CHECK_UNITS_KEY` (citations, so `coverage_by_check` and the Clauses sheet work unchanged) and a sibling `CHECK_LINKS_KEY`
holding per-check `{unit, source, status, p}`; both are internal keys, stripped on export like the others. Declared links need no model score; an
unreviewed link keeps its P(yes) and quote as evidence for the reviewer.

## 4. What coverage reports
- **Grain.** A link without a `check` index is job-grain and reads as cited only, never checked (a job with no per-check units never counts as
  checking). Only a check-grain declared or reviewed link makes a unit checked. The Pulte catalog's cited topic ids are per job, so expect the first
  report to show most units cited only or `linked_unreviewed`; that is the honest result and is not tuned. Tested.
- **Edition.** Each link may carry an edition; where both it and the unit's resolve and differ, the link is kept and marked `edition_mismatch`,
  counted separately in the summary (the same id can carry different text).
- Clause status keeps the existing meanings (checked: a job's check decides it; cited only; uncited), computed from **declared and reviewed** links.
- An unreviewed link puts the unit in a new status **`linked_unreviewed`** (counted in `clause_summary`, its own Clauses-sheet value, never in
  "checked"): so the headline "checked" cannot be inflated by model links, and the sheet shows how much would move on review.
- `ClauseCoverage` gains `link_status` per cited job (declared/unreviewed) and the top P(yes) of an unreviewed link.
- Paged with the batched-planning rows (already built).

## 5. The two queued defects, folded in
- Overlay policies get `overlay_id` (the program slug already used as `JTBD_PROGRAM_<slug>`), set where `import_jtbdset` builds the policy, so
  `check_pack_archive` stops warning `program_overlay_id_mismatch`. Test first on the kernel-lab `pulte-6-2-jtbds.json` shape.
- `effective_date`: caller-given, else derived from the artifact (its own date field, else a fixed epoch constant), never `now`; a test imports twice
  and compares the policies byte for byte (fails on old code).
I read both against the code before changing; the repro file is opened for its keys only.

## 6. Mapping sources (read-only; jaci prepares them, I only define the shape they land in)
1. Pulte catalog's cited topic ids (52 of 115 jobs): `declared`.
2. Rule Map `rulemap.json` (`rules`, `jtbds`, per-rule P(yes), quote, chunk path): `rulemap`, `unreviewed`. Its topic ids (`A1-1-01`, ...) are on
   the June 2026 guide; the corpus tree on disk is March 2026, so the adapter's edition check reports unresolved ids rather than guessing (open
   question for the user: which edition the units come from).
3. kernel-lab cortex-to-jtbds output (394): a different job set (older graph), so never job links or content; at most a unit-to-rule alias table
   (chunk path to rule id), and never a mapping status.

## 7. Not building
No conditional verdicts, no automatic promotion of unreviewed links, no model matching in this path (the existing alignment run stays the model route).
Tests: mapping resolution (unknown unit id errors), coverage statuses for declared vs unreviewed, export strips both keys, defects above.
