# Domain tab: policy section, first slice

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-10-03. Nothing built. Depends on japes v2.6.1 (local, unpushed) reaching `plato`.

## Today

- `scenarios/shared/domain_tab.py:render_domain_tab(pack_dir, key=)` edits only the document taxonomy
  (`document_agent.yaml`). Called by the DSCR, CRE (two pages) and insurance demo pages.
- Policy rules come from `scripts/extract_policy.py policy`: in-process SDK pipeline, a DRAFT yaml in
  `output/policy_drafts/`, merged into the pack by hand. Per D3, C&I `core.yaml` stays hand-authored.

## What v2.6.1's client gives (`jazzx_plato_client/_authoring.py`)

`start_extraction` -> `extraction_run` (poll, or `stream_extraction_run`) -> `proposals` ->
`decide_proposal` / `proposal_comments` / `add_proposal_comment` -> `merge_rules` (check `reachable`)
-> `open_draft` / `write_draft_file` / `publish_draft`.

Gap to confirm: `start_extraction` takes `policy_id` and `representation` but no `reads` / `units`,
which the script passes via `JtbdTemplate`. Without them clauses that read no pack field get proposed.
Ask japes whether the route takes them, or whether the pack's declared fields are used instead.

## First slice (one scenario: DSCR, which already runs on Plato)

A "Policy" subsection under the Domain expander, shown only when "Run on: Plato" resolves a Plato.

1. **Upload + start.** File uploader (pdf/docx/md), policy id field, representation select (default
   `conditions`, matching the script). Start -> run id in session state.
2. **Progress.** Poll `extraction_run` on a rerun timer (stage, documents, segments, proposals,
   failed segments, lint findings).
3. **Review.** List `proposals(status=...)` with rule text, confidence, excerpt, source refs; buttons
   come from each proposal's `available_triggers` (do not hardcode trigger names); a comment thread.
4. **Merge to draft.** `merge_rules`; show added / replaced / skipped and warn loudly if
   `reachable` is false. Stop at the draft.

Out of slice: publishing (needs a `pack_version` bump and the accepted rules brought back into
`config/packs/`, since packs are jaci's source), pack review lifecycle, lint triage, JTBDSet export,
the other scenarios, and any in-process fallback (extraction has none).

## Shape

- New `scenarios/shared/policy_tab.py` with `render_policy_section(pack_id, *, key)`, called from
  `render_domain_tab` via an optional `pack_id` argument. Existing callers unchanged.
- Client access through the existing `scenarios/shared/plato.py` helpers (config, identity headers).
- Pure helpers (run status -> display, proposal -> row) kept free of Streamlit so they unit-test
  without a server; the page code stays thin.
- jaci's committed code cannot import the authoring methods until v2.6.1 is on `plato`. Until then
  build against the editable japes and keep the section behind a `hasattr(PlatoClient,
  "start_extraction")` check so the pin does not break the other pages.

## Verify

- Unit tests for the helpers with canned `ExtractionRun` / `ProposalView` / `RuleMergeResult` dicts.
- One `requires_plato` test: upload a small policy md for dscr-core, poll to done, accept one
  proposal, merge, assert `reachable`.
- Manual: run the DSCR page against a local Plato (`./scripts/plato-local.sh start` in japes).

## Open questions

1. `reads` / `units` on the extraction route (above).
2. Which pack first: dscr-core (Plato-resident, human checkpoint) is the proposal.
3. Does the draft-and-publish step belong in this tab or stay in repo workflow? Proposal: stay in
   repo; the tab ends at the draft and offers its rules file for download so they can be committed.
