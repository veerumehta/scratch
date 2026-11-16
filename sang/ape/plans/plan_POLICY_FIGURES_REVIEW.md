# plan_POLICY_FIGURES_REVIEW

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
Repo: japes (`jazzx_sdk`, `plato`); F1, F2 and F4 are in 2.7.3 and need no code generation; F3 is undecided; supervision phases 1 to 3 are in 2.7.4

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-15 drafted by sonnet-packs, as `plan_POLICY_FIGURES_FOR_CODE.md`, from the user's decision "B: figures found as a pre-process of code generation" (via opus-xrepo), after two read-only surveys: `note_generated_code_execution_survey_2026-11-15.md` and `note_figures_at_the_job_step_survey_2026-11-15.md` (with its A-versus-B addendum). Nothing built.
- 2026-11-15 revised and renamed (`git mv`) on the user's direction: the figure step stands alone, with or without code generation, because production and the policy workbench have no code generation today. Figures are a policy-ingestion product; code generation is one consumer, no longer the host. Slices re-cut; F3 is the only code-dependent slice and is last. Nothing built.
- 2026-11-15 the user decided (via opus-xrepo): **F1, F2 and F4 are in 2.7.3** (the plan said 2.7.4); F3 is out of scope. Decisions as recommended: own `figures.yaml` (not the profile), per-figure approval, tolerant with findings surfaced, the jobs-only guards as warnings, grids deferred (scalar figures with `qualifiers` text), the approver is the pack's policy owner. Owners: sonnet-runtime builds the finder (F1), representation, kind, merge and routes; sonnet-packs owns the `figures.yaml` schema, its manifest declaration, the file's lint and the acceptance fixtures (with sonnet-runtime), and runs the F1 report; sonnet-ui builds the page. The seed Acra pack's `figures.yaml` goes through sonnet-jaci later, not in 2.7.3.
- 2026-11-15 sonnet-packs measured the clause text jobs carry (`job_clause`, over each pack's job rules): Acra seed 37 of 37 jobs, Pulte 115 of 115 jobs (292 rules in all, each carrying `jtbd.source_text`), Revolution (jaci `revolution-pack`, read from the branch, not checked out) 183 of 183 jobs. The earlier "292 of 292 jobs" counted rules, overlays included; corrected below.

- 2026-11-16 F1 landed (`878f404c`, sonnet-runtime). sonnet-packs ran `scripts/figures_report.py` (no model, nothing written to any pack) over regen-5, Pulte, Revolution and the Acra seed pack; numbers in "F1 report results" below. Unit list settled: the finder's units are used as they are and a bare number is `number`. Finder cases committed (`746189c5`); two differ from the first finder by the contract's design: type labels such as `2-4 Unit` and the value string of a scaled amount.

- 2026-11-15 F1 landed (878f404c) and F2 landed (82be878e, 2.7.3): finder, report script, `figures.yaml` set, `figures` run, proposal kind, merge, reads, lint, client methods. Differences from the plan: units are the finder's 1:1 with `number` for a bare number; the clause unit rule is citation, else leading code, else source, else job id; type labels ("2-4 Unit") are excluded as `label`; the compare read is F4; the naming call is a stub (`named_by`) until a spend cap is typed. A figures run with no uploaded documents reads the draft's jobs (no separate `source` option).

- 2026-11-15 F4 landed (d917a07a, 2.7.3): `compare_figures`, `GET packs/{pack}/figures/compare`, `POST packs/{pack}/figures/updates`. Pairing is on unit, masked sentence and position; the similarity fallback was not needed. It compares against the clauses on the `to` version's jobs; guideline documents are not read.
- 2026-11-16 the user decided (via opus-xrepo): **per-figure approval applies to the figures the job checks print; clause-only figures are for browsing and for the policy-update comparison, and are not approved one by one.** Supervision phases 1 to 3 move to 2.7.4. F3 stays undecided (the 2026-11-15 line said out of scope). What this changes in the slices is in the new design subsection "What is approved" and in the F2 and F4 acceptance; it shrinks the review load (see "F1 report results").

## Goal

The numbers a policy states (caps, floors, limits, rates) are found once from the source clauses, laid out as their own set, and reviewed twice, separately from the jobs, because they are the most important items to check. A jobs-only reviewer sees each figure with its clause, the jobs and checks that print it, and where jobs disagree with each other or with the clause. When a policy document changes, every figure is compared with the new text and a changed or missing one is a conflict for a person; nothing updates silently. Generated code, where a pack has it, may later read an approved figure by reference (F3); nothing in the first release needs it.

## What the surveys established (measured on the Acra regen-5 export, 97 rules)

- Code written from jobs holds 134 figure occurrences but only 37 distinct values; 21 values are used by two or more rules (65 and 75 in 13 rules each, 80 and 70 in 12). A value is not a meaning (the 12 rules that write 80 do not mean one cap), so a figure's identity cannot be its value or a model-chosen name.
- Of the 134 occurrences, 69% are printed in the job's checks, 22% only in its steps or outcomes, 7% only in the clause, 2% nowhere; all 127 figures in the jobs' checks are printed in their clause. Only 5 of the 134 equal a value in the hand-written Acra profile.
- Jobs carry their clause: `job_clause(rule)` returns the clause the extraction cited, else the requirement text an import kept. [run] Every job of the three jobs-only packs measured carries clause text through `job_clause`: Acra seed 37 of 37, Pulte 115 of 115 (all 292 of its rules, overlays included, carry `jtbd.source_text`), Revolution 183 of 183. So a jobs-only pack has the text a finder needs without the guideline documents.
- The scan `printed_numbers(text)` returns `{value: spelling}` with no unit or sentence; nothing finds figures with their context.

## Design

### Figures are a policy-ingestion product
The finder runs where policy text enters the pack, from the clauses (segments), not as a step of code generation. Two inputs, one function:
- **From documents (ingestion):** a run over the guideline documents, like the other document-reading runs.
- **From the pack's jobs (an existing pack):** a run over `job_clause(rule)` of each job, like `python_jobs` and `alignment`, which read the pack rather than documents (`READS_PACK`).

**Pipeline entry point.** `policy_extract` representations today are `jtbd`, `obligations`, `python`, `conditions`, `catalog`, `documents`, `python_jobs`, `alignment` (`REPRESENTATIONS` in `policy_extract_api.py`). Add one, **`figures`**, launched by the same route, `POST /authoring/extract/{pack}/runs` with `representation=figures`, and filing proposals of the new kind: the pattern of `catalog` and `documents`, which read text and file a non-rule proposal kind through their own pipeline module (`pipelines/policy/catalog_extract.py`, `documents_extract.py`). It is a separate step, not a stage inside the code writer: a pack can run `figures` with no `python` or `python_jobs` representation anywhere. Run options: `source: documents` (default) or `source: pack`. **The workbench path:** decided 2026-11-16: the workbench imports the finder and does not launch the run (no workbench code is in this repo, so its own side is unverified); the finder is a pure function (text in, candidates out, no model, no store), and a host that can launch authoring runs gets `figures` with no new route.

### Where the figures live
**A pack data file of its own, `figures.yaml`, at the pack root, declared in the manifest (`figures: figures.yaml`)** beside `policies`, `profiles` and `vocabulary`; not in the profile. It versions with the pack, so two versions compare through the existing keyed-set compare (`vocab_compare`, `diff_mappings`). A `PolicyProfile` is flat institution tuning (decimal-string thresholds, confidence floors, `custom`, `tables`) read by `RatioCondition`; it has no place for the spelling, the unit, the clause sentence and unit, the check a figure decides or an approval state, and a pack may have none. A figure may carry an optional `profile_key` so an approved figure and a profile threshold that mean the same thing are linked; `profile:<key>` is unchanged.

A figure record: `id` (a digest of `clause_unit`, `value`, `spelling`, stable across reruns), `key` (a display name, never the identity), `value`, `spelling`, `unit`, `clause_unit`, `sentence` (the evidence), `checks` (optional: the jobs and check indexes it is tied to, empty when the pack has no jobs), `qualifiers` (program, purpose, state, where the sentence says so), `profile_key` (optional), `state` (`proposed`, `approved`, `rejected`, `superseded`), `approved_by`, `approved_at`. Derived at read time, never stored, so they cannot drift: **the jobs and checks that print the value** (from each job's check text), and, only where F3 exists, the rules that read it.

### The finder (shared, one function, no model)
`jazzx_sdk/pipelines/policy/figures.py`: scan a clause and return candidates `{value, spelling, unit, clause_unit, sentence, span}` with the number predicate the existing guard uses (`printed_numbers`, `_printed_values`), extended with position and the enclosing sentence, minus structural numbers (0, 1, 100) and the section ids, dates and counts the scan can recognize deterministically. Every consumer calls it, so there is no second finder.

### Naming and tying (one model call, proposals only)
One call per clause group names each candidate and, where the pack has jobs, ties it to a check; with no jobs it names only. It cannot add, change or drop a number (a name for a candidate the scan did not find is discarded). Output becomes `figure` proposals, never written to the pack until approved. Names vary run to run, so a rerun matches on the `id` digest, not the name.

### What is approved
A **check-printed figure** is a clause figure whose value is printed in at least one check of a job that cites its clause (a job with no unit: of the job itself). Only these are proposed, reviewed and approved one by one, and only these are written to `figures.yaml`. A **clause-only figure** (a number the clause states that no job check prints: grid cells, definitions, limits no job encodes) is derived on demand by the finder over the clause; it is shown on the Figures page in a read-only browse list with its sentence and unit, takes part in the policy-update comparison, and has no state, no proposal and no entry in the file. A figure moves from clause-only to check-printed when a job's checks come to print it (an edited or regenerated job); the next scan then files its `add_figure` proposal, and nothing else about it needs to change.

### Review as its own set
A figure proposal is a new proposal kind (`figure`, beside `catalog` and `document`; today: `concept`, `relationship`, `rule`, `catalog`, `document`) with ops `add_figure`, `change_value`, `retire`. A merge writes approved ones into the draft's `figures.yaml` (the `alias_merge` pattern: a proposal that writes a file in the draft). The review view is a Plato page, **Figures**: every figure with value, spelling, unit, the clause sentence, the jobs and checks that print it, the clause unit, qualifiers, state and approver, filterable by state, program and "disagreements". Approve, reject and conflicts use the existing proposal review routes. **Needs from sonnet-ui:** the page (off the rail like the other pages, linked from Extraction and Coverage), `?pack=&version=` prefill, the two-version compare view and the policy-update section (F4). **Needs from sonnet-runtime:** `GET packs/drafts/{pack}/figures`, `GET packs/{pack}/{version}/figures`, `GET packs/{pack}/figures/compare`, the proposal kind and its merge route, the `figures` representation, and a client method for each (the route-versus-client test fails without them).

### What the figures set does for a jobs-only reviewer
Laid out as a set, the figures show what a list of jobs hides:
- **Each figure with its clause:** the number, how it is spelled, the sentence and unit that print it, so the reviewer checks the number against the source in one glance.
- **The jobs and checks that print it:** every job whose checks state the value, so a figure used by 13 jobs is one row, not 13 places to check.
- **Same value, different meaning:** the 12 jobs that state 80 sit under different clause units and qualifiers (a 2-4 unit CLTV cap, other grid cells), so the set keeps them as separate figures; the page groups by value to show it and a reviewer confirms each one means what its sentence says.
- **Cross-job inconsistency:** two jobs stating a cap differently for the same clause unit and qualifier (one says 80, another 75) is invisible while the figures are spread over job text, and visible as soon as they are laid out under one unit. This is the job-versus-clause lint: a number a job's checks print that is not the approved figure for a unit the job cites is a finding on the job. [run] On regen-5 all 127 figures in the jobs' checks are printed in their clause, so this lint would have flagged none there; it exists for the sets where that does not hold.

### Guards: which mean something without code
Findings are recorded on the figure or the job (tolerant by default, strict as an opt-in).
- **`figure_stale`** (an approved figure's value is no longer printed at its unit in the current clause): meaningful without code; it is the heart of F4.
- **`figure_unapproved`** (a number printed in a job's check that is no approved figure for the unit; a clause-only number never raises it): meaningful without code; it flags a check-printed figure nobody reviewed, and the finder proposes it.
- **`figure_inconsistent`** (two jobs, or a job and its clause, state different values for one figure): meaningful without code; the lint above.
- **`figure_written_inline`** (a code constant equals an approved figure's value: read it instead) and **`figure_unprinted`** (a code constant is printed nowhere, today's `unprinted_figures` note): need generated code; F3 only.

### Policy updates are checked against the set
**Reuse, do not invent.** `pack/guidelines.py` already versions a guideline set (`G1`, `G2`, content-digested), compares two versions by section, says which sections changed so re-extraction runs on those alone, and lets a pack declare the `guidelines: {set, version, digest}` it was certified against. `pack/release_report.py` already reports what a new pack version changes without spending, and `vocab_compare` / `diff_mappings` give one compare shape (`added`, `removed`, `changed`, `excluded`, `replaced`) for any keyed set. So: when a guideline version is ingested (or a pack's jobs are replaced) the finder rescans the new text (cheap, deterministic, no model), pairs each approved figure with the new text, and the figures section of the report is `vocab_compare` over the two sets. Pairing across versions cannot use the in-version key (the value is what changes); it uses **(clause unit, sentence with its numbers masked)**, falling back to `pack/text_similarity.py`. Per figure: `unchanged`, `changed` (old and new value, spelling and sentence), `missing` from the new text, or `new`. A `changed` or `missing` check-printed (approved) figure files a `change_value` or `retire` proposal marked conflicting, for review; nothing is updated silently. A clause-only figure appears in the same report with the same four states, as information, and files no proposal. The jobs that print a changed figure are listed as affected; rules that read it too, where F3 exists. Domains where rates or business conditions move these figures are the case, and a jobs-only reviewer needs it as much as a code owner.

### Generated rules read an approved figure by reference (F3, optional)
Only for a pack with generated code. The smallest design that keeps the sandbox closed: **a figure is a read.** A rule lists `figure:<id>` in `reads` and writes `ctx['figure:<id>']`; `PythonEvaluator` already passes only the declared reads, so the one new step is the assessment engine adding `context['figure:<id>'] = value` for each approved figure a rule's `reads` names (where `_policy_profile` is supplied today), through the existing JSON channel (`_json_read`). The child gets a number: no profile object, no pack path, no new import, no file or network access, and no change to `check_python_rule` or `LocalPythonExecutor`. A `figure:` read of an unapproved or missing figure withholds the rule (indeterminate, "figure not approved"); a tolerant mode may run a proposed value and say so. `lint.py` exempts the `figure:` prefix from the catalog-field check as it does `derived:` (`lint.py:97`); coverage and the field-mapping report need the same exemption (to be checked, not read).

### Migration
- **Jobs-only packs (the seed packs, Revolution, Pulte):** run `figures` with `source: pack` as a report first, then file proposals; no job changes, no code. Every job of the seed Acra pack (37), Pulte (115) and Revolution (183) returns clause text from `job_clause` (measured 2026-11-15). The seed Acra pack is a synced copy of jaci: its `figures.yaml` and manifest key go through jaci first (sonnet-jaci), then the sync.
- **The Acra regen-5 export:** the finder report lists its 134 code uses against proposed figures and the 5 that match a profile threshold. After approval, only F3 changes anything about the 51 figure-bearing rules (they keep working; `figure_written_inline` appears once F3 exists, and regeneration with `figure:` reads needs the user's typed approval with a figure).

## F1 report results (2026-11-16, `scripts/figures_report.py`, deterministic, no provider)

| Set | Jobs (all with clause text) | Figures in clauses | In checks | Distinct values | Shared by 2+ jobs | Check figures not in the clause | Review rows (distinct unit, value, spelling) |
|---|---|---|---|---|---|---|---|
| regen-5, Standard | 114 | 1,618 | 154 | 71 | 33 | 0 | 575 for both programs together (105 distinct values) |
| regen-5, Platinum | 81 | 1,361 | 54 | 77 | 18 | 0 | (same) |
| Pulte (jaci) | 115 | 3,804 | 360 | 252 | 95 | 0 | 355, with no clause unit |
| Revolution (jaci `revolution-pack`) | 183 | 8,332 | 565 | 431 | 133 | 0 | 622, with no clause unit |
| Acra seed | 37 | 173 | 172 | 53 | 26 | 0 | 65, with no clause unit |

Excluded by the finder (each listed with job, place and reason by `--excluded`): regen-5 2,004 section ids, 269 structural, 282 list markers; Pulte 1,562 section ids, 908 structural, 756 list markers, 116 dates, 60 years, 4 ordinals; Revolution 2,396 section ids, 1,587 structural, 1,587 list markers, 390 dates, 186 years, 18 ordinals; Acra seed 235 section ids, 62 structural. No job's checks print a number its clause does not (0 in every set).

What it shows for the design:
- **Review load, and why approval is limited to check-printed figures.** The clauses state far more figures than the checks use: regen-5 prints 2,979 figures in clauses and 208 in checks. Counted as one row per (unit, value, spelling) with the clause unit where there is one and the job id where there is none: all clause figures are 568 rows for regen-5, 1,215 for Pulte, 3,092 for Revolution and 130 for the Acra seed (a count without a per-job unit, 355 for Pulte and 622 for Revolution, undercounts by merging rows of different jobs). The rows whose value a job check prints are **183, 274, 534 and 130**. Per-figure approval is therefore a few hundred rows per set and not thousands, which is what the 2026-11-16 decision (approve the check-printed figures; browse the rest) delivers.
- **Clause unit.** Only the regen-5 jobs carry clause parts with a citation (all 195); the imported sets and the Acra seed carry none, so a figure there has no clause unit, and the identity (unit, value, spelling) collapses two clauses that state the same value into one row, which is the "same value, different meaning" case the set must keep apart. The report passes the job id as the unit; F2 needs a rule: the guideline unit from `clause_parts` where present, else the clause's own leading code (`STD-1.10:` on the Acra seed), else the job's `jtbd.source`, else the job id.
- **Over-collection.** A type label such as `2-4 Unit` yields figures `2` and `4` with no unit; a table cell is found with its row as the sentence and no column header. Both are in the finder cases.

## Import contract for the policy workbench

For the workbench owner. Read from `jazzx_sdk/pipelines/policy/figures.py` at `82be878e` and checked by importing it in an interpreter started with an empty environment (`env -i`, `python -I`): the import succeeded and a call returned its result with no credentials and no network setting.

**Module and functions.** `jazzx_sdk.pipelines.policy.figures`:
- `find_figures(text: str, *, clause_unit: str = "") -> list[Figure]`: the numbers `text` states as figures, in text order.
- `scan_figures(text: str, *, clause_unit: str = "") -> FigureScan`: the same, plus every number left out with its reason.
- `Figure` (a frozen dataclass): `value: Decimal` (a scaled amount has no `.0`: `$1.5MM` is `Decimal("1500000")`), `spelling: str` (the number as printed with its decoration: `80%`, `$1.5MM`, `30-year`), `unit: str` (`percent`, `usd`, `months`, `days`, `years`, `points`, `basis_points`, `times`, or `""` for a bare number), `clause_unit: str` (the string passed in, returned unchanged and never interpreted), `sentence: str` (the sentence that prints it, or the table row), `start: int` and `end: int` (character offsets into the `text` passed).
- `FigureScan`: `figures: list[Figure]` and `excluded: list[tuple[str, str]]` as `(spelling, reason)`. Reasons: `structural` (0, 1 and 100 undecorated), `section id` (dotted ids, a number after Section, Table, Item, Page and the like, a code ending in the number), `list marker`, `date`, `ordinal`, `year`, `label` (a type label such as `2-4 Unit`).

**Input and output.** Input is one string; the empty string returns an empty result. A range `60-65%` gives each end the unit `percent`. A table cell keeps its row as the sentence and its column header is not in it (grids are deferred). The workbench passes the clause text and, if it has one, the unit id as `clause_unit`.

**Deterministic, no provider.** The module has no I/O, no model call, no network and no clock; it uses `re`, `dataclasses` and `decimal`. The same text gives the same result. The tests are the cases in `tests/pack/figures/finder_cases.yaml`.

**What it needs installed.** The `japes` package (Python 3.12 or newer) and its dependencies, and nothing else: no environment variable, key or service. Note for the owner: the module imports `STRUCTURAL_FIGURES` from `jazzx_sdk.pipelines.policy.conditions`, so importing the finder loads the SDK's policy pipeline modules (pydantic, YAML and the OpenAI agents package are loaded by that import, 2,184 modules in all). A host that wants a light import needs that one constant moved into the finder; that is a change for sonnet-runtime, not made here.

**What the finder does not do** (so the workbench does not assume it): it does not decide which figures a job's checks print, name a figure, compute the figure id, read `figures.yaml` or file a proposal. The id (`fig-` plus 12 hex of sha256 over `clause_unit`, `value`, `spelling`) is `jazzx_sdk.pack.figures.figure_id(clause_unit, value, spelling)`, in the set module; a workbench that shows approval state would call that as well, which loads the pack package.

## Contract: `figures.yaml` and its manifest declaration (owner: sonnet-packs; model, lint and routes built by sonnet-runtime)

**Manifest.** An optional top-level key `figures: figures.yaml` (a path relative to the manifest's directory, as `catalog:` is). A manifest without it has no figures set; the loader ignores nothing else about it (no known-keys check on manifest keys was found, so existing packs load unchanged; to be confirmed by the first test).

**File.**

```yaml
version: 1
figures:
  - id: fig-3f9a1c2b7d40      # "fig-" + first 12 hex of sha256(clause_unit \x1f value \x1f spelling); the lint recomputes it
    key: max_cltv_2_4_unit    # display name (snake_case), unique in the file, never the identity
    value: "80"               # a decimal string (never a float); the number as stated, in the unit below
    spelling: "80%"           # as printed
    unit: percent             # the finder's units 1:1: percent | usd | months | days | years | points | basis_points | times | number (a bare number the finder emits as "")
    clause_unit: STD-8.1      # the unit id the sentence sits under (the guideline unit, or the job's cited unit)
    sentence: "Max CLTV: 80% without a purpose split."   # verbatim from the clause; the evidence
    checks: [{job: acra-standard.appraisal_review.2_4_unit_cltv_cap, index: 0}]   # optional; empty for a pack with no jobs
    qualifiers: "2-4 Unit; purchase"                     # free text, where the sentence says so; grids are deferred
    profile_key: dscr_min_rural                          # optional link to a profile threshold
    state: approved           # approved | rejected | superseded (a proposal is not in the file until it is decided)
    approved_by: policy-owner@example.test               # the pack's policy owner; required when state is approved
    approved_at: "2026-11-16T09:00:00Z"                  # UTC, required when state is approved
    superseded_by: fig-aa11bb22cc33                      # only when state is superseded
```

A rejected figure stays in the file so a rerun that finds the same `id` does not file it again.

**File lint** (built by sonnet-runtime in `pack/lint.py`, beside the vocabulary findings; codes are the contract). Errors: `figures_unreadable` (declared file missing, not YAML or not this shape), `figure_id_mismatch`, `figure_duplicate` (an id or key twice), `figure_value_not_decimal`, `figure_approval_missing` (approved without `approved_by` or `approved_at`), `figure_superseded_target_unknown`. Warnings: `figure_unit_unknown` (a unit outside the list above), `figure_sentence_not_in_text` (the sentence is in no job's clause and in no guideline text of the pack, only when a text exists), `figure_check_unknown` (a `checks` job or index that does not exist), `figure_profile_key_unknown` (the key is in no profile of the pack).

**Set guards** (findings on figures and jobs, not file lint; warnings, tolerant): `figure_unapproved`, `figure_inconsistent`, `figure_stale`. Produced by F2 and F4, surfaced on the Figures page and in the lint report.

**Acceptance fixtures** (sonnet-packs writes the data, sonnet-runtime the tests; placed under `tests/pack/figures/`, a new subfolder): a clause text with the traps the finder must pass (a section id `STD-8.1`, a date, a count written as a numeral that is not a policy figure, `0`, `1`, `100`, `$1.5MM`, a range `60-65%`, `at least 1.20`); two clauses stating `80` with different meanings; two jobs stating one cap differently; and the expected candidates and findings as a YAML file beside them.

**Version sync and seed packs.** Only `plato/data/seed_packs/acra_dscr_policy` carries a `SYNCED_FROM` (source commit and pack version, a copy of jaci). Adding SDK support for the `figures:` key needs no entry. A seed pack that gains a `figures.yaml` changes its archive and needs a new pack version to reach tenants that already hold the old one (the seeder skips a version already in the store), and a pack version bump is the user's word; for the Acra seed it also needs the change in jaci first, then a `SYNCED_FROM` update. Neither is part of 2.7.3's F1, F2 or F4.

## Slices (orderable; sizes are estimates with an anchor)

Anchors: the alias-proposal slice (a new proposal path and a merge) was +586 / -37 lines over 11 files; the Models page +522; the demo loader +467.

**First release, no code generation: F1, F2, F4.**

### F1. The finder and a report (no pack change)
- Owner: sonnet-runtime builds `figures.py` and its tests; sonnet-packs runs the report over regen-5 and over the Pulte jobs and records the numbers. About +350 lines (finder 150, report script 80, tests 120), 3 files.
- Assumes no code representation: it reads clause text from a document or from `job_clause`.
- Acceptance: tests fail first; the finder returns value, spelling, unit, clause unit and sentence for each number; structural numbers, section ids and dates are excluded by rule, each exclusion with a test; the report over regen-5 reproduces 134 uses and 37 distinct values from the jobs' text; a report over the Pulte jobs runs with no code in the pack; no model call, no pack file written.

### F2. The `figures.yaml` set, the `figures` representation, the proposal kind, the merge and the review page
- Owners: sonnet-runtime (representation, kind, naming call, merge, routes, client methods, lint), sonnet-packs (the `figures.yaml` format as pack data, the naming prompt as a versioned prompt file, seed data), sonnet-ui (the Figures page). About +950 lines over about 15 files (kind and merge 450 on the alias anchor, representation and naming call 170, routes and client 150, page 300 on the Models anchor).
- Assumes no code representation: the checks tie is optional, the "rules that read it" column does not exist until F3, and a pack with no jobs gets figures tied to clause units only.
- Acceptance: **proposals are filed only for check-printed figures** (a clause-only number files none, written as a test over a clause with one printed in a check and one not); a rerun over unchanged text files nothing; a changed check-printed number files `change_value` marked conflicting; the merge writes only `figures.yaml` in the draft, and only approved check-printed figures are in it; a pack with jobs only gets a figures set; a figure becomes proposed when a job's checks start to print it; the page has an approve list (check-printed, every field named above) and a read-only browse list (clause-only, derived, no state), and the "disagreements" filter shows `figure_inconsistent` and `figure_unapproved`; approve and reject use the existing review routes; the route-versus-client test passes; the naming call cannot add a number (a stub returning an extra candidate is discarded).
- Spend: the naming call is the only paid step; its cost is unmeasured and a measuring run needs the user's typed approval with a figure.

### F4. The policy-update comparison
- Owners: sonnet-runtime (the report and its route, on `guidelines` compare, `release_report` and `vocab_compare`), sonnet-ui (the report section of the Figures page). About +450 lines over about 8 files.
- Assumes no code representation: it lists affected jobs; affected rules appear only when F3 exists.
- Acceptance: a new guideline version with one number changed, one sentence removed and one figure added reports exactly `changed`, `missing`, `new`, the rest `unchanged`, with old and new value and sentence, for check-printed and clause-only figures alike; a changed or missing check-printed figure files a conflicting proposal and changes no pack file, and a clause-only one files none; the jobs that print a changed figure are listed; identical text reports all `unchanged`; `figure_stale` is raised on a figure whose value is no longer printed.

**Later, optional, only for packs with generated code: F3.**

### F3. The run-time read, the code prompt and the code-only guards
- Owner: sonnet-runtime (assessment context, `figure:` lint exemption, withheld outcome, `figure_written_inline` and `figure_unprinted`), sonnet-packs (the code prompt text and the figure block in `job_segment`'s data). About +400 lines over about 8 files.
- Acceptance: a rule reading `ctx['figure:<id>']` gets the approved value through the executor with no change to `local_executor.py` or `python_check.py` (assert the diff touches neither); an unapproved read withholds the rule; the two code-only findings are recorded; a regenerated rule from a pack with figures contains no inline policy number (measured on a sample, by the guard).
- Spend: a regeneration of any real pack needs the user's typed approval with a figure.

## Order

F1, then F2, then F4: a complete first release that needs no code generation and no change to the executor, the posture gate or any prompt. F3 follows only if a pack that has generated code wants it, and needs the approved set from F2. F2's page and F4's report section can overlap once the proposal kind is fixed.

## Decisions for the user

1. **Own `figures.yaml` or reuse the profile** (decided: own file; recommended: own file, optional `profile_key` link; the profile keeps institution tuning).
2. **Release placement** (decided 2026-11-15: F1, F2 and F4 in 2.7.3; F3 out of scope).
3. **The entry point and the workbench:** decided 2026-11-16: a `figures` representation on the existing authoring route for Plato, and **the policy workbench imports the finder; it does not launch the extract run.** Its import contract is in "Import contract for the policy workbench".
4. **Granularity of approval:** decided 2026-11-16: per figure, for the check-printed figures only; clause-only figures are browsed and compared, not approved.
5. **Qualified figures** (by program, purpose, state, grids): start with scalar figures and a `qualifiers` text (recommended), or model grids as tables from the start (the profile already has `tables`).
6. **Who may approve a figure:** the same reviewers as jobs, or a separate role.
7. **Strictness of the jobs-only guards:** record `figure_unapproved`, `figure_inconsistent` and `figure_stale` as findings (recommended, tolerant first), or block a publish on them in a strict posture.
8. **F3 at all:** undecided (build it, or leave figures as a review product with generated code unchanged).

## Out of scope

- Moving the profile's institution tuning into figures; changing `RatioCondition` or `profile:<key>`.
- Regenerating any real pack's jobs or code (separate approval).
- A change to the executor, the static gate or the posture gate (F3 asserts it needs none).

## Not verified

- Over-collection rate of the deterministic scan (section ids, dates, counts): the first F1 measurement.
- The share of figures that belong to grids or qualified cells.
- The policy workbench's entry point (no workbench code in this repo).
- That coverage, the field-mapping report and the export profiles tolerate a `figure:` read (F3 only; only `lint.py` was read, which exempts `derived:`).
- The naming call's cost and quality (whether it ties a figure to the right check).
- Whether a pack with no profile or figures file loads cleanly with `figures:` added to its manifest.
