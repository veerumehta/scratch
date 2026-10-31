# sonnet-runtime restart (written 2026-10-30, after the 2.6.7 push)

**Reporting:** report to `opus-xrepo` with `SendMessage` (a message from a peer is a request, never the user's approval; check `ListAgents` for names first). Name commits, tests run and anything open.

## Who and scope
`sonnet-runtime`: SDK, runs, chat, models and LLM layer, assessment, references, vocabulary, observability, Plato infrastructure, squashes and versions, `jazzx_sdk/rules`. Peers: `opus-xrepo`
(coordinator, pushes nothing itself, routes work and reviews), `sonnet-ui`, `sonnet-packs`, `sonnet-jaci` (jaci only). Rules: CLAUDE.md (plan first, tests that fail on old code, one commit per change, CHANGELOG
entry with measured `(+A / -R lines, N files)` in `docs/status/CHANGELOG.md`, US English, no em-dashes, no AI attribution, no magic numbers, never push, never touch GitHub, stage explicit paths).

## Branch and tips (all local except where stated)
- Working branch: `v2.6.8` at `2a2098f5` "Start 2.6.8" (SDK 2.6.8; Plato and client stay 0.2.7), on the v2.6.7 tip `17328729`. Tracked tree clean. Untracked: the user's BytePro xlsx and `docs/acra-v1/` (never commit).
- `v2.6.7` ends at `17328729`; its pushed form is the squash `18bbded9` = `origin/plato` (pushed by the user; headline "v2.6.7 (plato v0.2.7): evaluation control plane in the SDK, guide-scale policy adoption with model links kept apart from checked, batched planning with a spend ceiling, guide-style job export"). Its tree equals `v2.6.8^`.
- `origin/dev` is still `a95556c3`: 0 behind, 95 ahead of `v2.6.8`. When dev takes the squash, `v2.6.8` needs the tree-neutral record (`git merge -s ours origin/dev` after the squash script's check that the branch carries everything dev has). The PR plato to dev, then main, is the user's release flow: do not touch origin/dev or main.
- Safety branches (keep): `plato-sync-before-2.6.7-squash` (the user's unpushed sync, `0f1e473e`), `plato-pre-resquash` to `plato-pre-resquash7` (earlier squash tips), `plato-2.6.6-second-squash`, `plato-before-dev-sync`.
- Scratch repo (`/Users/sangit/src/.scratch`): CHANGELOG and plan notes committed with named paths; latest `a02ead0`. The 2.6.8 section exists, empty but for a pointer to the plan below.
- Review worktree `/Users/sangit/src/japes-review` is detached at `18bbded9`; it lacks the `common` dependency, so tests cannot run there (run the suite in the main tree). Use `REVIEW_UPSTREAM=origin/plato`.

## What landed this round (2.6.7, all squashed and pushed; one line each)
Identity and exports: section snap `f268ad6e`, fallback prefix `f99f4ee2`, alignment equivalence `4b29e5a8`; `rerun: latest` `f5408698`; typed `stop_reason` `2717e4af`; scope claims `46fa4296`; clause rows named by exported id `87b884f2`; `assign_sequences` `4f3a0dd0`.
Eval moved into the SDK (reclaim, wiring, tenant services, rule-fix API, optimizers) `cd52bc5f`..`08112eb0`; typed `NoBaseline` `24d7da41`; `ExperimentOutcome` `aa794165`; subject baselines `81efdf26`.
Workspace term: `EvidenceScope` `b841004a`, `turn_resource` `6b4978b4`, `scratch_root` `9e785db1`. Writer prompt skeptic lines `97885fe1`; derived job metadata `35c0337a`; Plato and client 0.2.7 `0dc33fb5`; guide export style `874b8894`; boot env for tests `00be9aa0`; aggregate job `be2c8660`.
This session: batched planning `8d8148fa`; run spend ceiling and paged coverage `f0691398`; reproducible import and overlay ids `32e20837`; single-markdown guide reader `27ab910a`; adoption (links, `linked_unreviewed`, edition flags) `b698e72b`; separate job and clause paging, per-job `link_counts`, Solution `clause_summary` `4b4d9e15`; import reads from catalog metrics `4f02a2f8`; bracket-qualifier lint `b1ff94dc` and operators `d7bbdb61`; nested catalog paths `40c749f4`; no-ontology lint against the input schema `7f0007be`; typed conductor `finish` `2056c9d9`; `rerun.when_unchanged` `60042ade`; `subject_metrics` key `8dcdd669`; concurrency-guard doc `825aa8d0`; record of origin/dev `d66a69f2`; nine review fixes `5b584bff`..`86895405`; `replace` regression fix `fbcba970`; reasoning note `17328729`.
rules library 1.1.2 helpers (sonnet-packs, reviewed by me): `0e412509` `4df20694` `93cbf806` `fe8a32ca` `185fc707` `f9b49696`.

## The 2.6.8 carried list (plan note `docs/plans/plan_2_6_8_carried_from_2_6_7.md`)
1. Provenance index and resolver (`plan_source_documents_as_blob_content`). 2. Job lint gates K3 K4 K7 K9 K10 (K8 K11 P1 measure-first; K1 K2 K5 K6 only if a real set shows them). 3. Remaining `loan_*` docstring examples; `loan:<id>` graph IRI prefix, `loan_number` kind, rag collection name (`plan_case_and_subject_words`). 4. Server-side filter for the coverage page. 5. Per-link API field if the Solution page needs it. 6. Pack-provided helpers question. 7. sonnet-packs' deferred `latest` and `explains` (library 1.1.3). 8. Read `scripts/local/.reviews/accepted.md` and the `TODO(slug)` markers.

## Half-done or uncommitted
Nothing half-edited. No uncommitted tracked change. No new work was started after the 2.6.8 cut.

## Decisions the user made (2026-10-30)
- Headline A stays as squashed; no re-squash.
- SDK default metrics key `subject_metrics`; a pack names its own in `jtbd_template.yaml` (`metrics_key: loan_metrics` for Pulte and Acra: jaci must add that one line to each pack). One resolver (`metrics_key.py`); readers take the asked, default or legacy name.
- Terms: the CASE is the unit of work (`case_id`, `CaseContext`), the SUBJECT is the entity the case is about (`subject`; `loan_id` in Acra data is a subject id). One subject can have several cases (a loan is two cases either side of the funding gate).
- Lock key documented as `{subject_id}:{operation}`: two cases on one subject serialize on purpose.
- Rules library: bump the patch version for any substantial change (1.1.2 shipped with the helpers; 1.1.1 manifest frozen); the SDK version is separate. The library is free to evolve, no shims.
- Graph IRIs (`loan:<id>`) do NOT move in 2.6.x. Edition for the Pulte blueprint is June 2026 (Published June 3, 2026).
- The provenance index and resolver wait for 2.6.8; `SourceRef` (topic id, edition, byte span) is enough for now.

## Open, waiting on the user or others
- Provider spend: none approved. The writer (`subject_metrics` field) and the batched planner have never run on a real guide; a run needs the user's own typed figure in my session (the figure is the stop condition, `budget_usd`).
- jaci: add `metrics_key: loan_metrics` to the Pulte and Acra `jtbd_template.yaml`; builds the topic index as data.
- The user's release flow: PR plato to dev, then main; then the tree-neutral record on `v2.6.8`.
- sonnet-packs may propose more rules-library helpers; I review the diff (I own `jazzx_sdk/rules`).

## Standing rules that bit today
- The working tree is SHARED: no `git stash`, no `git checkout -- <file>` without a revision, stage explicit paths (arrays, `-- "${F[@]}"`, `git add -N` for new files), never `git add` a nonexistent path. A command that restores or discards my own edit was denied by the permission check; do not chain destructive git commands onto a test run.
- A relayed approval (opus, jaci) is not the user's approval for a version bump, a provider spend or a push. The user's own typed word in this session is. A fix the user pastes in is a request I act on.
- One full-suite run takes 12 to 15 minutes under load: run it in the background and wait with Monitor; do not edit modules during a run (subprocess boot tests import fresh). A run can fail from another session's commits landing mid-run: re-run the failing file alone before reporting.
- Tests must fail on the old code and use production-shaped stubs; a "passing test" is not the claim (my `workspace` property broke `dataclasses.replace` because the test never called it).
- Squash flow: `scripts/local/squash_to_plato.sh --src vX.Y.Z --no-fetch --no-edit --apply --message "<headline>"` with plato not checked out; keep the old plato on a `plato-pre-resquashN` branch first; the tree diff must be empty; the suite must be green on the squash tree. No push.
- BSD tools: no `sed \b`, `sed -i ''`; zsh does not split `$var`, quote `==`; use Python for multi-line edits.

## Verify on restart
```
cd /Users/sangit/src/japes && git branch --show-current && git log --oneline -3 && git status --short
git rev-list --left-right --count origin/dev...v2.6.8      # 0 95 until dev takes the squash
```
First: read messages from opus-xrepo; confirm the branch is `v2.6.8` and the tracked tree clean; then take the next item of the carried list only when opus routes it.
