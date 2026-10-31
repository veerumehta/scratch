# Plan: structure-driven, batched section planning for a guide that does not fit one call (sonnet-runtime, 2026-10-30)

Plan and no-spend estimate only; nothing built, no provider call. For opus-xrepo's review, then the user's typed figure.
User direction (via opus-xrepo, 2026-10-30): build it so a Fannie-sized guide runs through extract, jtbd and code.

## 0. What I read, and what I did not find

Source named in the ask: `.../openai/pulte_fnma/agent-1-organized-documents`. **That directory does not exist.** The Fannie Mae source is
`.../openai/fannie_mae/agent-1-organized-documents/fannie_mae/` (read only; nothing copied). Measured, counts only:

| | |
|---|---|
| Files | 506 `.txt`: 5 parts, 17 subparts, 63 chapters, **409 topic files**, 11 table-of-contents pieces, a preface; plus `_metadata.json` and `_processing_results.json` (`total_chunks` 506) |
| Header of each file | `# Title`, `**Source:** fannie_mae.pdf`, `**Chunk ID:**`, `**Pages:**`, `**Section Path:**` (the Part / Subpart / Chapter / Topic path), then the text |
| Size of the topic text | 2.65 MB over 409 topics (median 5.7 KB, 90th percentile 11.3 KB, largest 20 KB): about 660 thousand tokens at 4 characters per token, about 465 thousand words at 5.7 bytes per word |
| By part (topic text, thousand tokens) | A 86, **B 434**, C 63, D 23, E 56 |
| B3 (underwriting borrowers; the chapters the Pulte JTBDs cite: 243 of about 290 cited references, then B7 12, B2 10, B5 9) | 106 topics over chapters B3-1 to B3-6: 1, 10, 42, 25, 20, 8 topics; about 139 thousand tokens |
| Chapter, subpart and part files | small (2 KB average): the headings and introductions, i.e. the guide's own taxonomy, not content |

The opus note said 1141 chunks and 424 topics; this tree has 506 chunks and 409 topics. **The versions differ:** the Rule Map and kernel-lab's graph are
on `fannie_mae_june_2026_selling_guide` (its chunks, per its metadata, at `openai/pulte_fnma/agent-1-organized-documents`, which is not on this disk),
while this tree is the March 4, 2026 guide; the two do not line up topic for topic. Which edition the blueprint uses is the user's call; the adapter
records the edition in the citation (section 2, item 8) so nothing mixes them. I use what I measured and say so. Licensing: this is Fannie
Mae's published Selling Guide (the table of contents says "Published March 4, 2026"); kernel-lab's README says individual projects carry their own
license and I found none in `cortex-suite`. I read it for sizing only and copy nothing; whether it may be fed to a provider is the user's call.

## 1. The failure today

`SectionSegmenter.segment` renders every unit into one `plan` call (`plan_prompt`: taxonomy plus all units). A guide of 660 thousand tokens cannot fit
a context window, so the call fails or is cut. Within one plan the one-home-per-unit rule is the `holder` map and `shared_units` records the
losers; both are per call.

## 2. Design

1. **Taxonomy from the guide's own headings.** A corpus adapter (`jazzx_sdk/pipelines/policy/structured_corpus.py`) reads a directory of text files whose
   header carries a `Section Path` (or any `(path, text)` list the host gives): one unit per topic file (`unit id` from the path, citation
   `<source>#<topic heading>` with the pages), `Part / Subpart / Chapter` from the path. Nothing Fannie-specific: the header keys are a
   declared reader (`section_path_header`), so another guide with a table of contents uses its own.
2. **Sections and definitions from headings.** With no `sections` in the pack's template, the chapters of the path are the section names and
   each chapter file's introduction (its text, cut at a named limit) is the section's definition (`section_definitions`), so the planner is told what
   belongs where as `_taxonomy` already does for a hand-written template.
3. **Planning per batch.** Units are grouped by chapter (a small chapter joins its neighbors, an over-large one splits at a topic boundary) into batches
   of at most `PLAN_BATCH_TOKENS`; one `plan` call per batch, in parallel up to the run's concurrency, each told its own chapter taxonomy.
4. **Cross-batch merge.** Batches are disjoint by construction (a unit is in one batch), so the one-home-per-unit rule holds across them; sections
   with the same slug merge across batches in first-seen order; `shared_units` and the second pass for unplaced units stay per batch (a unit a
   batch's plan leaves out is asked again once inside that batch, else goes to that chapter's own section, never to a global "Unassigned").
5. **Fail loud where a call would not fit.** Each plan call's size is estimated before it is sent (characters over a named divisor plus the prompt) and
   compared with `PLAN_MAX_INPUT_TOKENS` (from the model card's context window, minus an output reserve; a host constant otherwise); a batch over it
   is split once more at topic boundaries, and a single topic over it raises `PlanTooLarge` naming the unit and its size. Never truncates silently.
6. **Coverage paging.** `coverage_by_check` already returns a row per unit; thousands of rows go through `GET .../coverage?offset=&limit=` (with the
   summary always whole) and the workbook's Clauses sheet is written in one pass (no change: 409 to a few thousand rows is far under the sheet limit).
   The extraction run record keeps `segments_total` and a per-batch progress line so a long run reads as batches done.
7. **A writer-side cap (added on review).** The job writer makes one call per section, and a chapter is nowhere near Acra's sections: B3 is about 98 thousand
   words over six chapters and B3-3 alone (42 of 106 topics) is about 40 thousand words, against Acra's sections of about 1.3 thousand words on average
   (11,801 words over 9). A chapter that large would give the writer a far bigger input and, at 4.4 thousand output tokens per thousand words, an
   output of hundreds of jobs in one call. So a chapter is split into sections at topic boundaries to a named `WRITE_SECTION_MAX_TOKENS` (input
   tokens of its units, default sized so the expected output stays well inside the model's output limit: about 3 thousand words), the pieces named
   `<Chapter> (1 of 3)` and so on, each keeping the chapter's definition; a section over the cap by one topic that cannot be split raises
   `PlanTooLarge` naming the topic (the same fail-loud rule as the plan call). Code writing is per job and unchanged.
8. **One version per pack.** The corpus adapter records the guide's published date and edition (read from the file header or the table of contents'
   "Published ..." line, or given by the host) in every unit's citation, and refuses a corpus whose units carry two different editions, so a pack
   never mixes versions of a guide.

## 3. Tests that fail on the old planner (stubs behave like the real client)

A scripted planning agent that, like the real one, **refuses a call whose input is over a stated token cap** (raises the context error a provider raises).
(a) A corpus of units over the cap: the old `segment` fails on its one call, the batched one completes with every unit placed exactly once.
(b) Two batches that both name a section "Credit": one merged section, units not duplicated. (c) A single unit over the cap raises `PlanTooLarge` naming it.
(d) A unit the plan leaves out is asked again inside its own batch, not in another. (e) The corpus adapter reads the real header form (a fixture shaped like
the Fannie file: `Section Path`, `Pages`, `Chunk ID`). (f) Paged coverage returns the same rows as the whole.

## 4. No-spend estimate (basis: regen-6, measured 2026-10-29, `flex_gpt-6-luna`)

Measured jtbd-step rates on Acra (Standard 11,801 words, Platinum 10,220 words; the planner and the section writers together): **0.0021 to 0.0022 USD
per thousand guideline words**, output about 4.4 thousand tokens per thousand words, 107 and 100 jobs (**9.1 jobs per thousand words**), 38 to 39
minutes of wall time per run. Code step (`python_jobs`, regen-5): 0.135 USD for the 152 jobs of the two Platinum and Standard runs, **0.0009 USD per job**.

**Assumed (not measured on Fannie):** the same jobs per thousand words and the same cost per word as Acra's; input priced at the output rate (an
over-statement, since input is cheaper) for the planner's extra input; warm cache; one attempt per call (no retries); 5.7 bytes per word.

| | thousand words | planner input (thousand tokens) | jtbd step | jobs | code step | total | wall time (assumed linear, serial) |
|---|---|---|---|---|---|---|---|
| First slice, B3 only (106 topics) | about 98 | 139 | about 0.22 USD plus planner input about 0.06 = **0.28 USD** | about 890 | about 0.80 USD | **about 1.1 USD** | about 5.4 hours for jtbd, about the same again for code |
| Whole guide (409 topics) | about 465 | 660 | about 1.0 USD plus planner input about 0.30 = **1.3 USD** | about 4,200 | about 3.8 USD | **about 5.1 USD** | about 25 hours for jtbd |

**Call counts with the writer-side cap** (sections of at most about 3 thousand words; Acra made 11 and 13 calls for 9 and 11 sections, about 1.2 calls per
section, which I keep): B3 about 33 sections, so 6 plan calls plus about 40 write calls (Acra: 11), about 46 in all; the whole guide about 155
sections, so about 63 plan calls plus about 190 write calls, about 250. The cost lines above do not change with the splitting (the writer's cost is
output-dominated and scales with words, 0.0021 to 0.0022 USD per thousand words, not with calls); a small per-call overhead for the repeated section
definition is inside the 0.3x to 2x range below. The dry run reports the real section counts and replaces these.

Range: the job density is the biggest unknown (Fannie is more prose and more repetition than Acra's tables; I would expect 0.5 to 1.5 times Acra's), so
read the jobs and code columns as 0.5x to 1.5x; the planner and jtbd columns move with words only, within about 0.3x to 2x of the table. A
cold run adds the model's own cache misses (the regen-6 numbers include a partly warm cache). **No call is made until the user types a figure.**
Cheaper first steps that spend nothing: the corpus adapter and the batcher run on the real tree with a stub planner and report the batch sizes
and call counts.

9. **The typed figure is a stop condition, not a forecast (added on review).** An extraction run gains `budget_usd`: its `CallMeter` is built with
   `limit_usd` (as case runs already do with `JAPES_RUN_BUDGET_USD`), so the run stops at the first call that finds the measured spend at or past
   the ceiling (`BudgetExceeded`), fails with its usage and the batches and sections done kept, and a restart resumes from them (the progress records
   `segments`/`segments_total`). Today an extraction run has no ceiling (`policy_extract_api` builds its meter without one); a test fails on that.
   The ceiling is whatever the user types; the estimate is what I expect it to cost, not a bound.

## 5. Order
Plan review (done, three changes folded in), then: the corpus adapter and the batcher first, with the dry run on the real tree and a stub planner (batch
sizes, section counts and call counts; no spend), then the rest of the build with the tests above, then the user's typed figure for the B3 slice (jtbd
step only; the figure is the run's stop condition) before any provider call; code step and the other chapters are separate figures.

## 6. Built, and measured on the real tree (stub planner, no spend; 2026-10-30)

Built: `plan_limits.py` (named caps, `PlanTooLarge`, token-bounded splitting), `structured_corpus.py` (header reader, chapter grouping, edition check),
the batched `SectionSegmenter` (per-batch plan, per-batch second pass, writer-side `(k of n)` split), `budget_usd` on submit and on the three
routes and client methods (the run's meter carries it; the run's error says it stopped at the ceiling), and `?limit=&offset=` on both coverage
routes (job and clause rows paged; counts, summaries and the workbook whole).

Dry run, tree `fannie_mae/` (March 4, 2026 edition): B3 slice 6 chapters, 112 chunks, 131k tokens, 374 units, 4 plan batches, 37 writer sections;
whole guide 80 chapter groups, 489 chunks, 650k tokens, 2010 units, 14 plan batches, 211 writer sections.

**Finding: the hierarchy is not uniform.** Some parts hang topics directly under a part or subpart with no chapter between, so "a chapter per
group" needed a reader that takes every chunk under a chapter at any depth, and a chunk whose path has no chapter level is a group of its own. The `chapter_pattern` is a reader setting, not a constant.

Still open: which edition the blueprint uses (the Rule Map is on June 2026, this tree is March 2026), licensing for a provider call, and the
user's typed figure (the run's stop condition) before any call.
