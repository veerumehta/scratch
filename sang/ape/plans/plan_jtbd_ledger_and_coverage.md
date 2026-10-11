# Plan: a JTBD ledger, JTBD to code, coverage as a count, and list-first authoring pages

Status: approved 2026-10-11 (opus-xrepo, from the user's direction); decisions taken (below), routed
to sonnet-runtime. Not started. Evidence: `plans/note_acra_jtbd_rules_review.md` (the Acra review) and
`ape/local/coverage/review_20261011/`. Prior art: `plan_policy_jtbd_extraction.md`,
`plan_dscr_programs_compare.md` (JTBDSet import, `jtbd_match`, `jtbd_compare`), `plan_plato_ui.md`
(static pages, U1-U7), `plan_plato_authoring_review.md` (reviews, comments, lint triage).

## Why

The review showed the two extraction paths are good at different things:
- **Document to JTBD** is a reliable inventory: 97% of Acra's hand-built jobs matched, nothing
  invented, no parts lost in either run.
- **Document segment to code** is per segment, not per requirement: rules overlap, mostly cover part
  of a job, lose parts to the undeclared-reads check, and coverage can only be measured afterwards by
  a model alignment that moves between runs.
- **Each path catches what the other misses.** Segment to code found two Standard requirements the
  jobs lacked (rule 18, tradelines; rule 38, FICO 700 for an escrow waiver); about half of the jobs
  have no rule, mostly because the schema cannot decide them.

So: the jobs become the record (the ledger), code is generated per job where a job is computable,
segment to code stays as a cross-check whose orphans feed the ledger, and coverage is a count over
the ledger. The goal underneath is CPU-first assessment: every computable check runs as code with no
model, and only each job's remainder goes to a model, with the boundary visible per job.

## The ledger

A pack's ledger is its jobs (procedure rules, as `import_jtbdset` already writes them, from our JTBD
extraction or an imported JTBDSet such as Acra's). Each job carries:
- **checks**, each with `reads` and `computable` (the JTBD step states them separately, so code can
  target a check rather than a whole job);
- **links**: the code rules that implement it (`implements: [job_id#check]` on the rule);
- **program scope**: core, or an overlay (from the job-level program comparison);
- **disposition**, derived, not stored: `code` (every computable check has a rule), `code+procedure`
  (some checks code, the rest procedure), `procedure` (nothing computable), `not_computable` with the
  missing fields named (the schema backlog), `unreviewed`.

## Capabilities, in build order

| # | What | Notes |
|---|---|---|
| L1 | JTBD extraction states checks with `reads` and `computable` | template and prompt; reads validated against the schema; a job's reads widen to what its code reads (same fix as undeclared reads) |
| L2 | **JTBD to code**: `PythonExtractor` input mode taking one job (and check) plus the clause it cites, beside the segment mode | shares the prompt shape, static checks, `rules_lib`, cases; the rule records `implements`; the clause matters: summaries lose table detail and exact thresholds |
| L3 | Gates on generated rules, both modes | units (percent field against a literal in (0, 1]: in progress), numbers in the code but not in the clause, undeclared reads with a repair turn |
| L4 | **Cross-check**: segment to code aligned to the ledger | the alignment in `ape/local/acra_coverage_report.py` moves into the SDK; a rule matching no job proposes a job from its clause (accept or reject); where both paths encode one check, their numbers are compared and a disagreement is a finding |
| L5 | **Coverage as a count**: `GET /packs/{id}/coverage` (draft or version), client method, xlsx | per job disposition, per section and program, totals, the schema backlog (missing fields with how many jobs each would unlock), generated-rule gate failures |
| L6 | **Job-level comparison** (programs; ours against another set) | promote the many-to-many aligner (`ape/local/acra_compare_sets.py`: same / differs / partial / none with what differs) beside `jtbd_compare`, whose one-to-one pairing fails across grains (Acra 123 jobs against our 68); program scope (core or overlay) is decided from it |
| L7 | Authoring pages (below) | |

## Authoring pages: lists first

Today the packs page (`plato/static/packs.html`, about 2,100 lines) carries packs, drafts, extraction
runs, the proposal queue, guidelines and blueprints; panels expand into each other, and the only list
of work is the approval queue. The user wants to go over lists in the UI itself.

Principles: one table per surface; counts and filters at the top; a row expands in place to its
detail (clause, checks, linked rules, code) and collapses back; actions sit on the row or a selection
(accept, reject, link, regenerate), so approval is a filter (`status: proposed`) and an action, not
the page's shape; deep links per row; xlsx export of what is filtered.

- **Coverage** (`/coverage/ui`): the ledger as a table. Columns: section, job, program scope,
  disposition, checks (computable / total), linked rules, missing fields, gate failures, status.
  Filters by each column; header counts are the L5 tally. Row detail: the clause, the checks, each
  linked rule's code and cases, the cross-check's verdict.
- **Compare** (`/compare/ui`): two sets (programs, or ours against an imported set) as one table of
  left items with their best relation and the note of what differs; filter by relation; the
  right-only items at the end.
- **Extraction** (`/extraction/ui`): runs (the existing panel moved out of the packs page), each
  run's parts and failures, and its proposals as a filtered view of the ledger.
- **Packs** keeps packs, drafts, guidelines and blueprints.

Static pages stay, as `plan_plato_ui.md` decided: a sortable, filterable table with in-place rows is
plain JS over one JSON route. If row editing (checks, links) grows beyond that, it is the trigger for
the React decision that plan deferred.

## Decisions (the user's, 2026-10-11)

1. **The ledger's storage**: the draft's procedure rules plus `implements` links on code rules. No
   new table; the ledger is versioned and published with the pack.
2. **Acra's ledger**: Acra's own 123 Standard / 108 Platinum jobs are the record; our extracted
   JTBDs and segment to code are cross-checks.
3. **UI**: static pages, as above. React is revisited only if row editing outgrows them.

## Tests

L2 against a fixture job whose clause carries a table: the rule holds the table's numbers. L3: the
Acra rule 10 shape (percent field against 0.80) is refused. L4: a fixture where segment code encodes
a requirement no job states proposes that job; a fixture where the two paths disagree on a threshold
reports it. L5: dispositions computed on a fixture ledger match a hand count, and the route agrees
with the SDK function. Pages: the existing static-page guards (scripts parse, no placeholder left).
