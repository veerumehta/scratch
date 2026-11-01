# SDK verbs for the Plato policy-to-JTBD surfaces: rulings and order

**Status:** review of `plan_plato_policy_to_jtbd_surfaces.md`, 2026-10-31. Author: sonnet-runtime. Queues SDK work for 2.6.8; nothing built yet. Marks: [V] checked in code
this session, [U] not verified.

## Rulings on the findings

1. **`metrics_key`.** It stays a `JtbdTemplate` field (`jtbd.py:170`), the pack's one setting; writers use it and readers take the asked, default or
   legacy name (`metrics_key.py`). No `ExportProfile` override: no consumer needs a name other than the pack's, and a consumer that did would
   be served by a rename at export, which we build when one asks. Plato shows it read-only. (Differs from opus-xrepo's lean on purpose: an
   unhit need.)
2. **Ontology source lifetime.** Build the `OntologySource` per request from the draft's files, not per process: its memory holds nothing a
   draft file does not, and its TTL clock has no meaning across requests. Config lives in the draft manifest's `catalog_source:` block, the seed
   is the draft's `catalog.schema.json`. Refresh returns outcome plus diff and writes nothing; a separate apply writes `stamped_catalog` and answers
   409 on a conflicting field. Diff by `vocab_compare.diff_catalogs` [V it takes catalogs through `catalog_to_ontology`; [U] not run on a real Hub document].
3. **Three verbs adoption needs** (text variant of the reader; adopt plus single-link review; write-back): all three are right, as text-in text-out
   verbs over the draft's files (a draft holds text files; the policy serializer is `policy.model_dump(mode="json", exclude_none=True)` dumped as
   YAML, `jtbd_import.py:241` [V]). Reviewer and date are arguments the route fills from `acting_user_id` and the server clock; the SDK verb has no
   default for either (a `reviewed` `UnitLink` already refuses without them). YAML comments and key order in a rewritten policy file are not kept [U
   how much the real files carry].
4. **Guide storage.** Not in the draft; agreed. Draft limits [V]: 1 MiB per file, 500 files, and no total-bytes cap in `draft_db.py`. Links carry the
   `SourceRef` (topic id, edition, byte span). A reviewer reading unit text in Plato needs a resolver: `DbGuidelineStore.read_file(version, path)` [V]
   already returns the bytes of a published guide, so a minimal resolver (`resolve_unit(store, set_id, ref) -> text`, slicing the span and checking the
   edition) is about 60 lines and needs no topic index. The index (carried item 1) is a different, larger piece; the minimal resolver can go in
   2.6.8 after the verbs below, and the index later.
5. **Extraction.** (a) A no-call `plan_estimate` is right: `SectionSegmenter.units()` and `_batches()` [V] already compute the units and plan batches
   without a model call, so the verb is a thin wrapper (about 100 lines with tests) returning units, plan batches, plan input tokens, and write-stage
   input tokens as the units' tokens again. It is a lower bound (outputs, retries and shared units are not in it) and says so; it is not the
   ceiling, which stays `budget_usd`. (b) Batch counters and per-batch cost in `_progress_fields` [V it carries segments only]: about 30 lines, in. (c)
   `SectionSegmenter` taking a `StructuredCorpus` (one planner, topic ids kept on jobs) is a real change to extraction planning (two planners today,
   `plan_batches` unused by it): not 2.6.8; it needs the user's decision on whether extracted jobs should carry guide topic ids or whether adoption by
   mapping is enough. [U] whether partial proposals survive a ceiling stop.
6. **Draft rule serializer and total cap**: checked above (serializer is the dump in `jtbd_import.py`; no total-bytes cap exists, only the per-file and
   per-count ones).

## Order for the SDK side (smallest first; what each unblocks)

| # | Verb | Size | Unblocks | When |
|---|---|---|---|---|
| 1 | `parse_markdown_guide(text, guide=, edition=)` beside `read_markdown_guide` | about 15 lines | (a) preview | 2.6.8 |
| 2 | `dump_export_profile(profile) -> yaml` (comments are not kept; the page says so) | about 10 lines | (c) profile editor | 2.6.8 |
| 3 | `catalog_stamp(files)` and `propose_refresh(files, kh)` returning outcome, stamp, diff, stamped document, writing nothing | about 60 lines | (b) source panel | 2.6.8 |
| 4 | `adopt_links_into_files(files, corpus, mapping)` and `review_link(files, job, unit, check, source, reviewer, date)`, text in and out | about 120 lines | (a) write and review | 2.6.8 |
| 5 | `plan_estimate(...)` plus batch counters and per-batch cost in the run progress | about 130 lines | (d) estimate and progress | 2.6.8 |
| 6 | `resolve_unit(store, set_id, ref)` (minimal resolver) | about 60 lines | per-link unit text drawer | 2.6.8 if time, else 2.6.9 |
| 7 | Corpus-input segmenter | larger | extraction that keeps topic ids | later, user decision |

## Asks rejected, and why

- **Cap or time-bound a caller's `MarkdownGuide` regex.** Python's `re` has no timeout and a length cap does not bound backtracking. Instead no caller
  string reaches a pattern: the route uses the default (Selling Guide) patterns, and another guide's patterns come from a pack-declared guide profile
  file in the draft, reviewed like any pack file (a later verb, only when a second guide needs it).
- **A `reference_cues` schema export.** `ReferenceCues.model_json_schema()` already is the schema [V pydantic model, `job_references.py`].
- **An `ExportProfile.metrics_key`.** See ruling 1.
- **Raising `PLATO_DRAFT_FILE_MAX_BYTES` or storing the guide in the draft.** A deployment-wide change for one file; the guide belongs in the guideline set.
