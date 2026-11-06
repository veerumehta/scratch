# plan_JAPES_DOCUMENT_PROCESSING_PIPELINE

Author: Virendra Mehta · 2026-11-06 · Status: done on v2.7.0 (S1 to S10; unpushed)

## Goal

Build one complete, reusable document processing pipeline in the SDK that does, by default, everything the document processing agent and the case-run ingest step can already do. Today the `document_ingest` reference pipeline only routes inputs (`pipelines/document/ingest.py:18-21`), while the case-run `DocumentIngestStep` (`pipelines/steps.py`, around 991-1025) carries most of the business logic. The result should be a pipeline a pack can run as-is, with every stage visible, traced and swappable.

## Before starting

Verify in this order: the latest CHANGELOG entries, this plan, then the source. Line numbers below come from a read on 2026-11-06 and may have moved. Re-check each anchor before editing.

## Constraints

- `run_document(...)` and `build_document_pipeline()` keep their signatures and current behavior for existing callers. The new stages switch on through the pack spec or `DocTurn` fields; nothing that works today changes output.
- The heavy work stays in `DocumentAgent` and the document tools. The pipeline owns order, routing, review pauses and emit.
- One implementation of each step. Where the case-run step and the reference pipeline both need a behavior (precedence, conflicts, cost), move it into a shared step both call.
- No values below the admission floor are written. Refusals stay typed.
- Plan docs carry no release or version guidance.

## Target stages

```
intake → assess → read → split → classify → completeness → extract → reconcile → recall → review → emit → finalize
```

| Stage | What it does | Source today |
|---|---|---|
| intake | Single file, package or collection (folder, Knowledge Hub collection, zip, URL list, blob set); any supported file type | `ingest.py` detect; `agent.py` process_dir |
| assess | Per page: digital, scanned or bad text | `tools/documents/pages/assess.py` |
| read | Text layer, vision model or DocIntel OCR per page; fallback engine; budget; page cache | `pages/engine.py`, `pages/readers.py`, `pages/budget.py`, `pages/cache.py` |
| split | Package into documents with identity and continuation checks | `tools/documents/split.py` |
| classify | Hierarchical taxonomy descent, floor per level | `tools/documents/classify.py` |
| completeness | Present, missing and unexpected types against the pack's required list | `agents/document/completeness.py` |
| extract | Template per class, provenance and confidence per field, refusal below floor | `agent.py` process, `tools/documents/extract.py` |
| reconcile | Precedence across documents, single-copy conflicts, per-engine cost | `steps.py` DocumentIngestStep (around 1262-1324, 1451-1468, 1627) |
| recall | Why each needed field is still empty; optional focused re-read | `agent.py` (around 565-620) |
| review | Pause for a person on refusals, flagged pages, conflicts or missing documents; resume with attestations | conductor suspend and resume; `FieldAttestation` |
| emit | Write results to the fabric with provenance | `ingest.py` emit |

## Slices

Each slice ships with its tests and leaves the suite green.

### S1. Pipeline skeleton and registry entry
- New `jazzx_sdk/pipelines/document/process.py` with `build_document_processing_pipeline()` and `run_document_processing(...)`, following the shape of `ingest.py` and `pipelines/chat/engine.py`.
- Register `document_processing` in `pipelines/catalog.py` with the full stage list above, optional stages marked as such, matching the catalog's "maximal set" rule.
- Stages that are not yet implemented pass through and are traced as skipped.
- Acceptance: `tests/test_pipeline_catalog.py` builds the pipeline with every flag on and the step ids match the registry.

### S2. Same page reading for every input shape
- Fix the gap where `process_dir` converts first and hands text to `process`, which skips the per-page engine path (`agent.py`, around 471 and 1017-1020). Folder, collection and zip runs must use assess and read exactly as single files do.
- Default file pattern covers every supported type, not `*.pdf` only (`agent.py` around 914, `ingest.py` around 112).
- Acceptance: a folder with one scanned PDF and no staged `.md` produces the same fields as processing that file alone; a folder with DOCX and XLSX files processes them.

### S3. Package detection by default
- Provide a default detector built on `split.py` (page count, page-level class changes, identity changes) so `package` is chosen without pack code. Packs can still supply their own.
- `refuse` is reachable by default for encrypted, unsupported or empty inputs.
- Acceptance: a combined loan package PDF routes to `package` and splits into its documents with no custom `detect()`.

### S4. Completeness on when the pack declares it
- If the pack or `DocTurn` declares required document types, run completeness after classify and include the report in the result. Respect a pack `min_confidence` (default today is 0.0 in `completeness.py` around 33).
- Acceptance: a package missing a required type reports it as missing; one with an extra type reports it as unexpected.

### S5. Reconcile as a shared step
- Move precedence, single-copy conflict and per-engine cost logic out of the case-run `DocumentIngestStep` into a reusable reconcile step. The case-run step calls it; the new pipeline runs it.
- Acceptance: existing case-run tests pass unchanged; the pipeline reports which document won each conflicting field and why.

### S6. Recall and review
- Wire the recall pass as a stage that runs when the pack names the fields its rules need.
- Add a review stage that suspends the run when any of these is present: refusals on required fields, flagged split pages, unresolved conflicts, missing required documents. Resume accepts attestations and continues from reconcile.
- Acceptance: a run with a refused required field suspends with a typed reason; resuming with an attestation admits the field and completes.

### S7. Tables from digital PDFs
- Digital PDFs currently convert in text mode and carry `"tables": []` (`conversion.py` around 496 and 575). Keep table structure for digital pages so extraction can cite cells.
- Acceptance: a digital PDF with a rate table yields table cells with page and cell locators.

### S8. Locators from the source
- Carry locators from the read step instead of searching for them after extraction (see `note_CORTEX_DOCUMENT_AGENTS.md`). Use the chunked path's chunk locators as the starting point (`extract.py` around 322-328).
- Acceptance: every admitted field has a locator that resolves to the exact page region it came from; no post-hoc text search.

### S9. Measurement hook
- Emit per-run metrics that the classification eval needs: per-document class and confidence, split boundaries, refusals, cost by engine, run-to-run diff key. Feed `plan_acra_classification_eval.md`.
- Acceptance: two runs on the same input produce a stable diff report; differences are listed by document and page.

### S10. Retire the routing-only path
- Make `document_ingest` call `document_processing` with only intake, read, classify, extract and emit switched on, so existing callers get the same results through one implementation. Mark `document_ingest` as the minimal profile in the registry.
- Acceptance: all existing `document_ingest` tests pass unchanged.

## Out of scope

- New lending document templates (pack work).
- Replacing production doc processing or imdoc. This pipeline is the SDK's own path.

## Done when

A pack runs `document_processing` on a mixed folder of loan documents, digital and scanned, and gets split, classified, complete-or-not, extracted, reconciled fields with page and cell locators, and the run pauses for review only where it should. Status lines on the deck's document processing slide can then move from "In progress" to "Ready to pilot".

## Outcome

Commits on `v2.7.0`: S2, S3, S4, S7 933f1df1; S5 4aa5e500; S9 441863dd; S6 8a874cea; S1 aef8fc20; S10 d4152cc0; S8 cf667c99.

Where the build differs from the plan:

- S1: assess, read, split, classify, completeness and extract are not separate pipeline steps. They run inside `DocumentAgent.process` and are traced as its spans. The pipeline steps are intake, package | collection | single | refuse, reconcile, recall, review, admit, emit, finalize.
- S3: the default detector (`detect_input`) is opt-in on `document_ingest` so existing callers keep their routing; `document_processing` uses it by default.
- S6: the recall pass already runs inside `process` when the spec names demanded fields, so the recall stage reports only.
- S8: acceptance is a page plus a character span, no bounding boxes. `locator_mode` is `quote_anchored` (default) or `page_aligned` (one call per page), per spec, per turn and per call.
- S10: the registry rename and alias were done with the catalog work; `documents_to_fields` is described as the minimal profile and a test pins its steps against the processing pipeline's. Step ids and `run_document` are unchanged.
- Not run: the classification eval (needs the user's typed approval with a figure; sonnet-ui owns it) and any provider run.
