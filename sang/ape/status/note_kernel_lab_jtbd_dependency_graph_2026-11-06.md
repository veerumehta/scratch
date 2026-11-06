# Note: kernel-lab `jtbd-dependency-graph` against our job and code path (2026-11-06)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

A note for 2.7.0 scoping. It decides nothing and queues no work. Read-only: nothing was run, committed or sent to a provider.
Sibling: `/Users/sangit/src/kernel-lab/jtbd-dependency-graph` (last commit 2026-08-26). Terms: the sibling says "loan"; this note says
"case" except where it quotes the sibling.

## 1. What it models

A draft dependency graph over a JTBD set, built from two workbooks, and an incremental re-evaluation engine over it.

- **Inputs.** `Pulte Jtbd v4.1 8 23 2026 1.xlsx` (a file name; sheets `JTBDs (by section)`, columns A to S: section, section_type,
  mnemonic, jtbd_numbers, jtbd_status, skill, Name, Timing, Edited, comments, Business Metrics, IS INFO, base text, four program
  overlay texts, comment, supplemental text; and `Loan Metrics`, columns A to H: section, job mnemonic, metric mnemonic, metric key,
  label, indicator context, calculation context, notes). `loan_file_timelines.xlsx` (sheets `Overview` plus one per case, columns A to O:
  Seq, Timestamp, Type, Name, Category, Batch #, JTBD Sections, Actor, Actor hash, Source, Pages, Size, Active, Removed, Event detail).
- **Job order and prerequisites.** Job to job edges, split into four scheduling types (`GATES`, `PRODUCES_FOR`, `MUST_CONSULT`,
  `ROUTES_TO`, each pointing prerequisite to consumer) and three that never schedule (`CROSS_CHECKS`, `OWNS_CONDITION_FOR`,
  `REFERENCES`). A scheduling edge is meant to carry the output keys it consumes, an activation predicate and an on-missing-upstream
  effect. Output contracts come from the metric keys (one producer per key, else `ambiguous_output_authority`).
- **Document prerequisites.** Per job, requirement groups of document types (`ALL_OF`, `ANY_OF`, `AT_LEAST_N`, `EXACTLY_ONE`,
  `OPTIONAL_SET`), with three separate axes: business obligation (required, conditional, optional), reasoning necessity (must-have,
  supporting) and missing effect (block, defer, condition, ignore, not applicable); cardinality and a selection policy (latest active).
- **Timing and stages.** Mostly not modeled. The `Timing` column is stored on the job and no code reads it. Timeline rows other than
  `File upload` (84 milestones in the design's count) are skipped by the extractor, so case stages are not in the graph; only document
  events are: arrived, updated, removed, reactivated, reclassified (updated is inferred from a repeated name and category).
- **Runtime.** A document event finds the jobs whose requirement groups changed (direct), walks scheduling edges for the downstream
  closure, runs the induced subgraph in topological order, skips a job whose input fingerprint is unchanged, and stops a branch whose
  consumed output keys did not change. The result is an impact report (direct, potential, recomputed, skipped, pruned, blocked,
  review-required, causal paths, latencies, recompute ratio). A full recompute is the correctness oracle. Domain reasoners are injected
  per job; the default raises, which the engine records as review-required, and an unapproved graph refuses to execute.
- **Outputs.** A versioned graph (SQLite), candidates for review, a validation report (cycles by Tarjan SCC, unknown targets,
  duplicate edges, route edges without predicates, authority, provenance), a semantic diff between graph versions, a JSON dispatcher
  and optional HTTP adapter, a CLI (ingest, replay, event) and a static HTML map.
- **Size.** About 5,800 lines, no third-party dependencies, 25 tests. The design (810 lines) is far ahead of the code: its metrics
  service, document registry, review service, migration and canary phases are plan only.

The design's figures for the draft graph (115 jobs in 11 sections, 164 metric rows, 409 requirement candidates, 118 scheduling edges,
406 non-scheduling links, 3 executable cycles, 204 duplicate-edge warnings, 112 route edges without predicates, 13 unresolved targets,
1,383 timeline events in 5 case sheets) are the repo's own; I did not re-measure them.

## 2. How a job's dependencies are derived, and the stated confidence

- **No dependency column.** The workbook has no prerequisite or depends-on column; the only structured link is the metric sheet's
  job-to-metric-key mapping. Edges come from prose.
- **Rules only, no model.** `extractor.py` scans each narrative column for mnemonic-shaped tokens and classifies the sentence around
  each by regular expression: "must consult", "authoritative" or "downstream propagation" gives `MUST_CONSULT` (direction by which side
  the verb faces); "upstream gate" or "route(s) to" gives `ROUTES_TO`; "depends on" gives `PRODUCES_FOR` with the cited job upstream;
  anything else is `REFERENCES` with the note "mnemonic mention without an explicit dependency verb". A token that is not a known job
  and has no verb is dropped; one with a verb is kept as `REQUIRES_REVIEW`. No LLM call exists anywhere in the repo.
- **Documents** are bullets under headings that match "reference documents", "required inputs" and similar; obligation and missing
  effect come from keywords ("optional", "if applicable", "must", "required"); every group is `ALL_OF` (the compiler never emits the
  other four rules).
- **Stated confidence.** Per candidate: 0.8 for a resolved edge with an explicit verb, 0.65 with an ambiguity note, 0.45 unresolved;
  document candidates 0.6 (required) or 0.75; cell-level evidence references for every record. Everything starts `PROPOSED`; nothing
  is promoted silently, `publish` with proposed items raises, and the README says the workbooks are "proposed source evidence". The
  design says shared fields and co-arrival may only create review candidates. The repo states no measured precision or recall: the
  design promises per-field precision and recall, and the tests are 25 unit tests on synthetic fixtures, none on the real workbook.
- **Two gaps in the code against its own design** (read from `compiler.py`, `service.py`): a compiled edge is built without output keys
  or an activation predicate, and the only review action (`decide_candidate`) changes a status, so no edge can be given a contract
  through the service; approved publication then fails `missing_output_contract` for every scheduling edge. And the extractor takes the
  Timing column but nothing uses it.

## 3. What our path has for the same need

| Need | Ours | Verdict |
|---|---|---|
| Job to job edges from prose | `pack/job_references.py`: every sentence naming another job is classed by cue as dependency, downstream, disclaimer, reference or unclassified; the strongest sentence names the edge and is kept as evidence; a declared `depends_on` outranks them; the cue lists are pack data in an export profile. Measured on the Pulte set: 192 mention edges, 64% false before classification, on two hand-labeled samples of 45 (`note_workbench_to_sdk_enhancements`, addenda) | Covered, and measured; their verbs are a narrower cue list with no measurement. Nothing in our authoring path writes `depends_on`, so declared edges exist only if a consumer's set carries them |
| Edge review states | Lint findings (`cross-section-dependency` error; `dependency-cycle`, `possible-*` warnings), severity per consumer profile; no stored approve or reject per edge | Real gap, only if edges become executable |
| Cycles | `jtbdset_lint` cycle check over the classified edges | Covered |
| Output keys and one producer | `metric-key-owned-twice`, `metric-key-shared`, ontology membership | Covered for ownership; no edge says which key a downstream job consumes |
| Document taxonomy | `pack/document_registry.py`: ids never reused, aliases, retired and `replaced_by`, category, cues, `yields` (catalog fields), staleness | Covered, richer than their label canonicalization |
| Job to document link | A job lists `evidence_types` it reviews and `reads` (context fields); a rule's reads are in `rule_reads`; the registry maps a document to the fields it yields, so document to field to rule to job is derivable | Derivable, not materialized: no reverse index and no obligation or missing-effect per document |
| Missing input | `IndeterminateReason.EVIDENCE_MISSING` and the library's unknown-is-None convention; `pack/demand.py` reports which demanded fields a case lacks and why | Covered for fields; the block, defer, condition axis is not modeled |
| Coverage | `ledger.coverage`, `coverage_by_check` (units by job and check) | Covered; different question (guideline clauses checked), not document impact |
| JTBD set model | The exported set (`jtbdset_export`, one set per program): jobs with requirements, metrics, mnemonic, section; programs as variants | Covered; their four overlay columns correspond to our variants and program sets |
| Order of work | Conductor config is the step order of one case run (`ConductorPipelineConfig.steps`); assessment runs a section of jobs per prompt with no job-to-job order | Real gap if a job must wait for another's verdict; I found no topological order over jobs anywhere |
| Case timeline | None: no document event, arrival time or removal model in the SDK. `pack/version_windows.py` selects a pack version by case date; case runs pin a pack digest and can rerun (a rerun naming `latest` follows the newest completed run) | Real gap for event-driven re-evaluation; their timeline model is also thin (uploads only) |
| Re-evaluate only what a change affects | Rerun of a whole case run; no impact analysis from a changed document to the jobs it feeds; no per-job input fingerprint for case runs (fingerprints exist elsewhere in the SDK, for other purposes) | Real gap; the largest piece of their design |
| Timing and stages of a case | Not modeled by either side | Not a gap to copy |

## 4. SDK ideas, consumer-neutral and sized (not proposed for building yet)

1. **A job graph module over what exists** (about 150 to 250 lines plus 100 to 150 of tests; a minor). Pure functions over the exported
   set and `job_references`: adjacency over dependency and declared edges, `upstream` and `downstream` closures, topological frontiers,
   the cycle report, and a longest-path depth, each edge keeping its evidence sentence. No runtime, no storage, no new schema. It
   would give the 2.6.8 job lint a readable "order" and a place for a page to draw from. Prerequisites: the cue-classified edges stay
   advisory until the false-edge rate is acceptable on a second set (only Pulte fired; ours produced zero mention edges).
2. **A document to job demand index with an impact preview** (about 100 to 150 lines plus tests, on top of 1; a minor). From the
   registry's `yields`, a job's `evidence_types` and `reads`, answer "which jobs read this document directly" and, through 1, "which
   jobs could change". Returns direct, closure and paths only; it executes nothing. Obligation and missing effect would be new job
   fields and are a separate decision.

A third piece, per-job input fingerprints with output-key pruning, is the part that saves work, but it needs a case event model and a
decision on how an LLM job's reads are known (a code rule's reads are declared; a job's are not). It is a plan, not an idea at this
size, and the sibling's own engine has it only against injected reasoners and synthetic fixtures.

**Leave in the sibling:** the OOXML reader, the two workbook extractors and their column positions, the customer's document label
taxonomy, timeline replay and the upload-batch handling, the HTML report, the SQLite store and HTTP adapter, the review queue.
**Do not copy:** the compiler's all-`ALL_OF` groups, the unused Timing column, and a mention-only edge with a verb as the sole
evidence (our measured rate says that is not enough).

## 5. What I did not read or run

- Read in full: README, the design, `extractor.py`, `compiler.py`, `models.py`, `reasoner.py`, `graph.py`, `predicates.py`,
  `service.py`. Skimmed: `tests/test_extractor.py` (head), test names in `test_reasoner.py`, `test_graph.py`, `test_compiler.py`,
  the head of `scripts/benchmark_incremental.py`, and a grep of `src`, `scripts` and `pyproject.toml` for any model call (none; no
  dependencies).
- Not read: `storage.py`, `api.py`, `http_server.py`, `cli.py`, `xlsx.py` internals (used only to print sheet names and the header
  row of each sheet, with a scratch script that never printed a data row), `scripts/generate_html_report.py`, the HTML report, and the
  tests for storage, API, report, XLSX and HTTP.
- Not read: any cell below row 1 of either workbook, so the job text, the metric rows and the case timeline rows were not opened;
  extraction was not run, so every figure in section 1 is the design's. No case document was opened.
- On our side not read in depth: the K gates in the 2.6.9 plan (item 2), the conductor's runtime, how assessment orders or batches
  jobs beyond finding no dependency order, the review store, and the Plato job pages. Nothing run: neither the sibling's tests nor ours.
