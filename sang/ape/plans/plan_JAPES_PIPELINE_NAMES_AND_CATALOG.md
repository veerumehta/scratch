# plan_JAPES_PIPELINE_NAMES_AND_CATALOG

Author: Virendra Mehta · 2026-11-06 · Status: proposal, names to confirm before building

## Status and modifications

How to use this section: the plan author may read it and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last. Branch: v2.7.0, nothing pushed. Target: all of this plan lands in 2.7.0 (user decision 2026-11-06).

- 2026-11-07 owner `sonnet-runtime` (Track B). Names confirmed by the user as written. Done: P1 d7dd9f20; P2 and P3 b36efe32 (ten new ids, every earlier id an alias with one deprecation warning per process); P5 65ba37cd (`case_to_verdicts` preset) and 84679caa (`case_file_to_conditions` preset and the `conditions` step); P6 checked, nothing registered.
- 2026-11-07 modification: `policy_extract` maps by `representation` to `policy_to_rules`, `policy_to_jtbds`, `jtbds_to_code` instead of forwarding, because the run server picks step components by representation over one shared pipeline. The representations `python`, `conditions` and `alignment` have no id and stay reachable by representation only (naming them is the user's call). `policy_to_catalog` and `policy_to_document_list` are plain functions, so their entries have no builder.
- 2026-11-07 modification: `case_update_to_verdicts` is not a preset; a rerun submit is the update mode and the `case_to_verdicts` entry says so. `case_file_to_conditions` is documents, assessment, adjudication, conditions (no approval step); a missing required document is a condition (id `D-<class>`), conditions carry the outcome's citations; clearing a condition is read-only (no route sets `resolution`, carried item 30). Pack manifest `kind:` lines are case step kinds, a separate namespace, and were not renamed.
- 2026-11-07 P6: `policy_change_to_impact` has its comparison (`compare_packs`, release report) but not "which open cases need a rerun"; `feedback_to_improvements` has parts but no composing run; carried as items 31 and 32; neither is registered.
- 2026-11-07 P4 done (4e66bb91, 69f487d3), as one composite `policy_to_pack` with an optional code stage and no `policy_to_code` preset (user decision 2026-11-07: a name that says pack must end in the pack). Changes to the earlier answers: a pause is finished at at least one accepted proposal of the stage (not every proposal decided); the three review merges became one `ReviewMerger` that the merge routes and `continue` both call; the extraction run gained `kind`, `parent_id`, `code`, `awaiting`, `stages`, `merged` and the status `awaiting_review` (migration 0040, checked on sqlite and Postgres); a parent is settled from its children when read and is skipped by the stale-run sweep. Routes `POST {prefix}/{pack}/policy-to-pack` and `POST {prefix}/runs/{id}/continue`; client `start_policy_to_pack` and `continue_extraction_run`. Not done: a catalog entry (the registry lists step pipelines with builders, and this is a run of the extraction service), a Plato page for the pause, a prose doc for the routes.

## Goal

Make every pipeline's name say what goes in and what comes out, and add the pipelines that are missing. Today one name can hide several outputs: `policy_extract` produces rules, JTBDs or code depending on a `representation` setting, and `catalog_extract` and `documents_extract` are two more outputs from the same policy text under different names. A reader cannot tell from the names that policy can become JTBDs, a data catalog, a document list or code.

## Naming rule

- **Display name:** "Input to Output", for example "Policy to JTBDs". Plain nouns a business reader knows.
- **Id:** the same words in snake case, `policy_to_jtbds`.
- **Registry fields:** every entry states what it consumes, what it produces, and whether the output is a set of proposals that waits for review or a finished result.
- **Old ids:** each stays as an alias that logs a deprecation warning once, so no caller breaks.

## Renames

| Today | New name | Id | In → out | Output |
|---|---|---|---|---|
| `policy_extract` (rules) | Policy to Rules | `policy_to_rules` | policy documents → rules, each checked against the pack's vocabulary | Proposals |
| `policy_extract` (procedure) | Policy to JTBDs | `policy_to_jtbds` | policy documents → JTBDs with data mapping and computability | Proposals |
| `policy_extract` (python) | JTBDs to Code | `jtbds_to_code` | reviewed JTBDs → tested Python rules on the helper library | Proposals |
| `catalog_extract` | Policy to Data Catalog | `policy_to_catalog` | policy documents → the entities and fields the policy reads | Proposals |
| `documents_extract` | Policy to Document List | `policy_to_document_list` | policy documents → the documents the policy requires | Proposals |
| `vocabulary_build` | Documents to Vocabulary | `documents_to_vocabulary` | a document corpus → new concepts and relationships for the knowledge graph | Proposals |
| `document_ingest` | Documents to Fields | `documents_to_fields` | files, packages or folders → extracted fields with page and confidence | Result |
| `chat` | Question to Answer | `question_to_answer` | a user turn → a grounded, cited answer | Result |
| `financial_spread` | Filings to Spread | `filings_to_spread` | financial filings → a standardized spread | Result |
| `investigation_loop` | Case to Decision | `case_to_decision` | a case → investigated, verified, governed decision with narrative | Result |

The policy authoring chat stays a chat, not a pipeline.

## New pipelines

Most are compositions of pieces that already exist. Status is from a code read on 2026-11-06.

| New pipeline | Id | What it does | Built from | Status |
|---|---|---|---|---|
| Policy to Code | `policy_to_code` | Policy to JTBDs, a review pause, then JTBDs to Code, as one run | `pipelines/policy/jtbd*.py`, `code.py`, conductor suspend and resume | Pieces exist; composition new |
| Policy to Pack | `policy_to_pack` | Stand up a domain from its policy: document list, data catalog, rules or JTBDs, review, then a draft pack ready to publish | the four policy pipelines; Plato authoring (`merge_rules`, `publish_draft`) | Pieces exist; composition new |
| Case to Verdicts | `case_to_verdicts` | Documents to Fields, rules that need no model, ACER for the rest, review, narrative | case step kinds `document_ingest`, `policy_assessment`, `adjudication`, `human_checkpoint`, `narrate` (`pipelines/steps.py`, `kinds.py`) | Steps exist; named preset new |
| Case File to Conditions | `case_file_to_conditions` | A loan or case file to the list of open conditions to clear, each citing its rule and evidence | Case to Verdicts plus completeness and ACER's structured conditions | Composition new |
| Case Update to Verdicts | `case_update_to_verdicts` | Re-judge only the rules a changed input affects, carry the rest forward | `pipelines/rerun.py`, `agents/adjudication/impact.py` | Logic exists; pipeline new |
| Policy Change to Impact | `policy_change_to_impact` | Compare two policy versions: which rules changed and which open cases need a rerun | JTBD set compare (`note_jobset_version_compare.md`), `impacted_rules` | Partly exists; check status |
| Feedback to Improvements | `feedback_to_improvements` | Approved feedback becomes gold cases and proposed guidance changes | knowledge loop (`plan_JAPES_2_7_1_KNOWLEDGE_LOOP_CHANGE_CLASSES.md`), curator functions | Check status before building |

Filings to Spread gains `validate` and `package` stages under `plan_JAPES_RECIPES_GAPS.md` R1, not a new name.

## Before starting

Verify in this order: the latest CHANGELOG entries, this plan, then the source. Confirm the names with the SDK owner before slice P2; the names appear in decks and pack manifests.

## Slices

### P1. Registry carries meaning
- Extend `PipelineContract` in `jazzx_sdk/pipelines/catalog.py` with `display_name`, `consumes`, `produces`, `output_kind` (`proposals` or `result`) and `aliases`.
- Add a function that lists pipelines as a table (name, in, out, output kind) for docs and for Plato's catalog page.
- Acceptance: the catalog test checks every entry has all fields and that display names follow "Input to Output".

### P2. Split policy_extract by output
- Register `policy_to_rules`, `policy_to_jtbds` and `jtbds_to_code` as separate entries that share the existing stages. Each fixes its own representation; no `representation` switch at the call site.
- Bring `catalog_extract` and `documents_extract` into the registry as `policy_to_catalog` and `policy_to_document_list`, with stage names that describe their steps (read parts, check excerpts, join names, classify, file proposals).
- `run_policy_extract(..., representation=...)` keeps working and forwards to the matching pipeline.
- Acceptance: each new id runs on the existing Acra test corpus and gives the same proposals as the old call with the matching representation.

### P3. Renames with aliases
- Rename the remaining ids in the table above. Old ids resolve through `aliases` with a one-time deprecation warning. Builder and `run_*` function names stay; add new names beside them.
- Update pack manifests in the repo's seed and sample packs to the new ids.
- Acceptance: the full suite passes; a pack using an old id loads and warns once.

### P4. Composite pipelines
- Add `policy_to_code` and `policy_to_pack` as pipelines whose steps call the child pipelines, with a review pause between producing proposals and using them.
- Acceptance: `policy_to_code` on the Acra corpus suspends after JTBDs, resumes on approval and produces code proposals; `policy_to_pack` produces a draft pack with document list, catalog and rules.

### P5. Case presets
- Ship `case_to_verdicts`, `case_file_to_conditions` and `case_update_to_verdicts` as named presets of the case pipeline (`conductor_pipeline` kind) so a pack can name one instead of listing steps.
- Acceptance: a pack that names `case_to_verdicts` runs the same steps as the DSCR seed pack's hand-written list.

### P6. Change and learning pipelines
- Check the current state of JTBD set comparison and the knowledge loop, then add `policy_change_to_impact` and `feedback_to_improvements` where the pieces exist. Record anything still missing as a follow-up rather than building it here.

## Order

P1, then P2 and P3 together, then P5 (small and visible), then P4, then P6.

## Done when

Every pipeline in the registry reads as "Input to Output", the deck's agent slides use those names, and a pack author can pick a pipeline by what it produces.
