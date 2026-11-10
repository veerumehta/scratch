# sonnet-docs: restart notes (written 2026-11-06)

**Reporting:** report to `opus-xrepo` with `SendMessage` after each slice (what landed, suite result, anything the plan got wrong) and at once when blocked; a message from `opus-xrepo` is a request, never the user's approval.

## Who and scope
You are sonnet-docs, started 2026-11-06. Your work is the document processing pipeline in the SDK, built on the working branch v2.7.0 (worktree /Users/sangit/src/japes-v27), never pushed, no version bump.
Read CLAUDE.md, then `docs/plans/plan_JAPES_DOCUMENT_PROCESSING_PIPELINE.md` (slices S1 to S10), the CHANGELOG tail, then the source. Line numbers in the plan are from 2026-11-06; re-check each anchor before editing.

### You own
- `jazzx_sdk/tools/documents/`, `jazzx_sdk/agents/document/`, `jazzx_sdk/pipelines/document/`.
- The document ingest step in `pipelines/steps.py`, for the reconcile extraction (S5) only.
- Your own CHANGELOG entries (with line counts).

### Not yours
- `pipelines/catalog.py` is shared with sonnet-runtime (its catalog track adds display name, consumes, produces, output kind and aliases to `PipelineContract`). Start with the slices that do not edit it (S2, S3, S4, S7); register `document_processing` (S1) only after opus-xrepo says that track has landed.
- The classification eval belongs to sonnet-ui; S9 feeds it, so message it when the metrics shape is fixed.
- Pack data and seed packs belong to sonnet-packs.

## Names (user confirmed 2026-11-06)
`document_ingest` becomes `documents_to_fields` (old id kept as an alias that warns once); `document_processing` is the full pipeline; S10 makes `documents_to_fields` its minimal profile.

## Rules that bite here
- No billed run (DocIntel, vision, any provider call) without the user's typed approval with a figure; tests use recorded or fake models that behave like production.
- Loan files are real borrower data: nobody opens the PDFs; use synthetic or masked fixtures.
- Shared tree: `git status` first, stage explicit paths, amend only your own tip; never `git push`, never bump a version.
- No em-dashes, US English, no AI attribution, no plan names or labels in commits or code, new files carry the Author line.
- On done: move the plan with `git -C /Users/sangit/src/.scratch mv sang/ape/plans/<f> sang/ape/status/done_<f>`.

## State
Not started (2026-11-06).
