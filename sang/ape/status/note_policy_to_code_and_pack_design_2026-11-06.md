# Design note: the composite pipelines `policy_to_code` and `policy_to_pack` (sonnet-runtime, 2026-11-06)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

For the user's decision before P4 is built. Read from the `v2.7.0` tree at `304fac8b`; nothing was run. "Read" means I opened the code; "inferred" is marked.

## 1. What the plan asks for

Catalog plan P4: `policy_to_code` is Policy to JTBDs, a review pause, then JTBDs to Code, as one run; `policy_to_pack` stands a domain up from its policy: document list, data catalog, rules or JTBDs, review, then a draft pack ready to publish. "Pipelines whose steps call the child pipelines, with a review pause between producing proposals and using them." Acceptance: `policy_to_code` on the Acra corpus suspends after the JTBDs, resumes on approval and produces code proposals; `policy_to_pack` produces a draft pack with a document list, a catalog and rules.

## 2. How that happens today (read)

It is done by a person across routes, each a separate run:
1. `POST {prefix}/{pack}/runs` with `representation=jtbd` (`server/policy_extract_api.py:628`) files proposals in the proposal store.
2. A reviewer decides each proposal (`/review/{pack}/proposals/{id}/decision`, see the authoring tests), then `POST /review/{pack}/merge-rules` writes the accepted ones into the pack's draft policy file.
3. `POST {prefix}/{pack}/job-runs` (`:675`, representation `python_jobs`) reads the draft's job rules (`jobs=` names which; empty means all) and files code proposals; the run reads the pack, not documents (`READS_PACK`).
4. Catalog and document-list runs (`representation` `catalog`, `documents`) are the same kind of run and file proposals too.
A run record (`ExtractionRun`) carries one `representation` and one status (`running`, `succeeded`, `failed`); there is no parent/child link and no "waiting" status (`server/policy_extract_runs.py`). The case pipelines have a real pause (a human checkpoint with the suspension store), but extraction runs are not conductor runs and do not use it.

## 3. The gap

Nothing chains the runs, waits for the review, merges what was accepted, or starts the second run from the merge. "A review pause between producing proposals and using them" has no home in the extraction run model.

## 4. Options

**A. A parent run in the extraction service (the plan's shape).** `ExtractionRun` gains `kind` (`single`, `composite`), `parent_id`, and a status `awaiting_review`. `POST {prefix}/{pack}/policy-to-code` starts the JTBD run as the first child; when it succeeds the parent goes to `awaiting_review`. `POST {prefix}/runs/{id}/continue` refuses while any of the first child's proposals is undecided, merges the accepted ones into the draft, and starts the `python_jobs` child with those job ids; the parent follows the child to a final status and shows `children`. `policy_to_pack` is the same with three first children (document list, catalog, JTBDs) and no second run: the pause ends with the draft pack built from the accepted proposals. Cost: a migration (`extraction_run` gains the columns), the continue route, the reclaim sweep learning that `awaiting_review` is not stale, a client method, and tests. Roughly one slice and a half; the riskiest part is the merge step, which today is a reviewer's explicit action.

**B. A client-side function in `jazzx_plato_client` that calls the existing routes in order and waits.** `policy_to_code(pack, policy, documents)` submits the JTBD run, polls it, then waits (the caller's own wait, returning "awaiting review" to the caller with the proposal set id), and on `.continue_(...)` merges and starts the code run. No server change, no migration, no new status. The registry entry would describe a recipe, not a server pipeline. Cost: about a third of option A. It does not give Plato a single run to show on the Runs page, and the pause lives in the caller.

**C. A conductor pipeline over the suspension store.** Express the composite as a `ConductorPipeline` (steps `jtbds`, `review` with a suspend, `code`), the way the case pipelines suspend at a human checkpoint. This reuses suspend and resume and the resume route, but extraction runs would have to become conductor runs (a different run store and stream), so it moves more than it adds.

Recommendation: **A for `policy_to_code`**, built so `policy_to_pack` is the same mechanism with different children; B only if the user wants the registry names now and the server change later.

## 5. Open questions for the user

1. A, B or C? (A is my recommendation; it is the plan's shape and shows on the Runs page.)
2. What does "approved" mean for the pause: every proposal of the JTBD run decided (accepted or rejected), or at least one accepted? I recommend every proposal decided, so a half-reviewed set does not silently feed the code run.
3. Should `continue` do the merge into the draft itself, or require the reviewer to have run merge-rules? Doing it in `continue` makes the composite self-contained; leaving it keeps the existing explicit review action. I recommend `continue` merges, with the merge result stated on the parent.
4. `policy_to_pack` ends with a draft ready to publish, never published: confirm publishing stays a person's action.
5. One budget: should the parent's `budget_usd` cap the children together (the sum), or does each child keep its own?
6. The run cap (`MAX_RUNS`, counted over running runs): a parent that waits for review should not count, only its running child; confirm.

## 6. Not verified

Whether the merge route can be called from the service without the reviewer's identity (it takes the acting user, inferred from the other review routes); how many proposals the Acra JTBD run files (the 37 jobs in the seed are already published, so a real run on that corpus would re-derive them); the Plato Runs page's handling of a new status.

## 7. Decisions (the user, typed, 2026-11-07)

1. **One composite, `policy_to_pack`, with an optional code stage; no `policy_to_code` preset.** A name that says "pack" must end in the whole pack, so a truncated outcome would need another name. The shape is a parent run in the extraction service (option A): `kind`, `parent_id`, status `awaiting_review`, a `continue` route.
2. **A pause is finished when at least one proposal of the stage is accepted** (the user chose this over "every proposal decided"). Read as: undecided proposals stay in the queue, are not merged, and can be decided later; the code stage needs at least one accepted job.
3. **`continue` merges the accepted proposals into the draft as the continuing reviewer; publishing stays a person's action.** Tested with two reviewer identities.
4. **The parent's `budget_usd` caps all children together; a parent in `awaiting_review` does not count against `MAX_RUNS`, and the stale-run sweep skips it.**
5. **The code stage is on by default; `code: false` on submit ends the run at the draft pack.** With it on, the parent pauses a second time after the code proposals.
6. Lookups of parent and children are tenant-scoped; the schema change is a Plato migration (next free number); acceptance uses a fake model.
