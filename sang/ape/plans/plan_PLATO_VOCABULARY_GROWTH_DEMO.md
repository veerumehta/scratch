# plan_PLATO_VOCABULARY_GROWTH_DEMO

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
Repo: japes (`jazzx_sdk`, `plato`), version in progress 2.7.2

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-11 drafted by opus-xrepo from a read of japes (plato tip after the 2.7.1 push) and the k9 sibling repo. Nothing run, nothing built.
- 2026-11-11 V2 built by sonnet-packs (uncommitted): pack `mortgage-vocabulary-demo` at `plato/data/seed_packs/mortgage_vocabulary_demo/` (18 concepts, 3 invented documents, `demo/expected_proposals.yaml`). It loads, lints clean and seeds. The plan assumed a concept under another name arrives as `matched`; the accumulator has no synonym step, so it arrives as `new` and the reviewer rejects it as a duplicate, and a `matched` candidate is dropped from the queue.

- 2026-11-11 sonnet-ui read-only check: `ontology.html` shows only catalog proposals from extraction runs (no concept or relationship proposals, no version compare); `ProposalView` already carries kind, category, concept, relationship, reasoning, excerpt, source_refs, occurrences, run_id and human-only `available_triggers`; the review `merge` returns a `MergeView` and cuts no version by design; Plato builds the review router without `vocabulary_for`, so the concept merge route looks unmounted; nothing in `plato/` or the client mentions `documents_to_vocabulary`. So "Plato mounts it" under What exists holds for the catalog proposals only. Six questions went to sonnet-runtime as part of V1.

- 2026-11-11 V1 report (sonnet-runtime, read only, no spend): review `summary` and `proposals` serve (filters status, kind, category, representation, run_id); a refused trigger is 409 `{message, reason_code: trigger_not_available | transition_refused, status, available_triggers}`; `POST .../review/{pack}/merge` is 404 (vocabulary_for not passed in `plato/api/authoring.py`); `/api/v1/processes` is 404 (no launchers set, and the conductor launcher runs a pack's conductor, not a catalog pipeline); the extraction run's REPRESENTATIONS has no vocabulary entry, so `documents_to_vocabulary` cannot launch from Plato; `tests/test_vocabulary_pipeline.py` passes (26) with a mock model, not run against Plato's proposal store. Gaps: (1) add a vocabulary representation to the extraction run, proposals only; (2) mount the concept merge; (3) merge returns an in-memory graph vocabulary and the compare view reads published pack versions, with no serializer between them. Option A: merge writes accepted rows into the draft catalog, then the existing publish cuts the version. Option B: KGAgent emits `kind=catalog` proposals, so `ontology.html` and `merge-catalog` already cover queue and merge (much smaller). Decision with the user.

- 2026-11-11 decisions (user): Option B for the launch (KGAgent emits catalog proposals through a "vocabulary" representation on the extraction run; review and merge on `ontology.html`; the catalog compare there shows the entities); content rework is fine; the demo must also show vocabulary terms and aliases changing, so it ends with both compares (`ontology.html` catalog, `vocabulary.html` terms and aliases) and an alias document is approved as an alias if the pipeline can propose one (sonnet-runtime checking; the term and alias path is not built until the shape is confirmed). Store wake-up added to the 2.7.2 queue.

## Goal

A demo in the Plato UI of what the k9 demo showed: take a pack with a starter ontology, add new policy or other documents, run the knowledge graph agent (`KGAgent`, through the `documents_to_vocabulary` pipeline), and put the proposed ontology enhancements in front of a human who approves or rejects each one, ending in a new vocabulary version. The SDK does the work; Plato renders it.

## What exists

- `jazzx_sdk/agents/graph/agent.py` (`KGAgent`): observe a corpus, propose what the vocabulary lacks, decide each proposal under the pack's admission policy, merge accepted ones into a new version. Merging is separate from accepting.
- Catalog entry `documents_to_vocabulary` (alias `vocabulary_build`, output kind `proposals`, steps ingest, emit, observe, propose, decide, merge, finalize; entrypoint `run_vocabulary_build`).
- `jazzx_sdk/server/vocabulary_review.py`: a review router over a proposal queue. A decision goes through the pack's lifecycle machine, only human triggers are offered, the actor comes from the request context. Plato mounts it in `plato/api/authoring.py` (the router at line 75, `ReviewMerger` at line 145).
- Plato pages `vocabulary.html` (core catalog, version compare, a pack's vocabulary, aliases) and `ontology.html`.
- k9 (sibling, reference only): its Streamlit pages for ontologies, policies and proposals, and its `docs/demo_inputs/` excerpts. Do not port k9 code; the SDK pipeline is the base.

## What is missing

1. A page to start a vocabulary run on chosen documents and to follow it.
2. A proposal queue page: each proposal with its kind (matched, new, conflicting), rationale and evidence, with approve and reject, then merge into a new version.
3. Demo content: a starter ontology and two or three short new documents, packaged so the demo is repeatable.
4. Proof that the pieces work together in a running Plato.

## Slices

### V1. Verify the path end to end (sonnet-runtime, first)
- In a running Plato (never restart it mid-run), check that the proposal-review routes serve and that `documents_to_vocabulary` can be launched through the process launcher or a route, against a pack with a store the review router can read. Report which routes, what a launch returns, where proposals land, and what a merge needs.
- If a piece is missing (a launch route, a store binding, a merge hook), list it with a file and a proposed shape; build only what sits in runtime paths (`runs/`, launcher, pipelines, infrastructure) and tell `sonnet-ui` the contract.
- Acceptance: a written report with the exact calls, run against a mock or recorded model, no provider spend.

### V2. Demo content (sonnet-packs)
- A demo pack under seed data: a starter ontology small enough to read on screen (about 15 to 25 concepts in one lending domain), and two or three short documents (policy excerpts) that each imply a few concepts the ontology lacks, at least one clearly new, one matching an existing concept under another name, and one conflicting with an existing definition.
- Use only public or invented text; no loan files or borrower data.
- Record in the pack what each document is expected to propose, so a run can be checked against it.
- Acceptance: the pack loads and lints; the expected proposals are written down per document.

### V3. The Grow vocabulary page (sonnet-ui, after V1 names the contract)
- A page in the Author rail group: choose a pack and its documents, start the run, show progress, then the proposal queue with kind, rationale, evidence and approve and reject (human triggers only, as the review contract offers them), then a merge action that cuts the new version and links to the version compare already on the vocabulary page.
- Reuse existing page helpers and the rail; no new framework. Errors render by their reason code as the Guidance page does.
- Acceptance: with a recorded run, a reviewer can approve one proposal, reject another, merge, and see the new version in the compare view; the audit shows the actor.

### V4. Rehearsal (all, after V1 to V3)
- A scripted walk-through in the order the demo is shown, with the expected screen at each step, run once against a recorded model, then once live under a typed spend cap.
- Acceptance: the script runs clean twice; one live run costs under the typed cap.

## Order

V1 and V2 in parallel. V3 starts when V1 reports. V4 last.

## Decisions for the user

1. **Spend:** a typed dollar figure for the live rehearsal run (V4). Nothing live runs before it.
2. **Domain:** which lending domain the starter ontology covers (mortgage is assumed).
3. **Where merged versions land:** a draft of the demo pack, or a copy per demo run so the demo resets cleanly (a copy is assumed).

## Out of scope

- Porting k9's backend, Streamlit pages or its RDF/OWL generator.
- Multi-domain bridging and the evaluation dashboards in the k9 roadmap.
- Changing KGAgent's admission rules.

## Not verified

- That the review routes serve in a running Plato and read a store the pipeline writes.
- That `documents_to_vocabulary` can be launched from Plato today.
- What `ontology.html` already shows of proposals.
- Whether the lifecycle machine for vocabulary proposals allows the approve and reject triggers the page needs.
