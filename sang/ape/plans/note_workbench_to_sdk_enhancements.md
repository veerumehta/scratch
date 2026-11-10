# Workbench to SDK enhancement candidates

**Status: a note, nothing decided.** It queues no work. Each candidate needs the user's yes and, for anything past a fix, a plan
first. Direction: the reverse of the juno and workbench adoption plans. Where policy-workbench has something the SDK lacks, that is
an SDK candidate (consumer-neutral, SDK first, hosts adopt).

Written 2026-10-31 by sonnet-packs. Workbench: `/Users/sangit/src/policy-workbench/backend` (origin/main 82ec7d8d, working tree
read). SDK: `jazzx_sdk/` on branch `v2.6.8`.

## How this was checked

- Three read-only surveys, one per area group, each reading the workbench file and the SDK counterpart and grepping the SDK for the
  capability under other names. Nothing was run: no tests, no corpus, no measurement.
- I re-read three claims myself: the SDK has only transaction-scoped advisory locks (`fabric/db/locking.py:53,63`); `jtbdset_lint.py:197-211`
  makes an edge from any text mention of another job's mnemonic and emits `dependency-cycle` and `cross-section-dependency` as errors;
  `runs/store_db.py` carries `stop_requested` beside `RUNNING`. Everything else below is the surveys' reading, line numbers included.
- "SDK lacks it" means `jazzx_sdk/` lacks it. Plato (the server host tree) was not searched, so Plato may already hold some of these.
- Quoted workbench measurements (81 percent of targets trip two rules, 8 of 11 false edges, 65 to 120 s publish) are the workbench
  authors' own claims.
- The lint-gate half (run-specific detail, assistant voice, maintainer note, invisible characters, overlay dangling step, cross-section
  routing prose) was surveyed earlier and is not repeated.

## Already in the SDK (do not re-propose)

Much of the workbench's lifecycle is already ported, and in places the SDK is ahead:

| Workbench capability | SDK counterpart |
|---|---|
| G-numbered immutable guideline versions, race-safe numbering | `pack/guidelines_db.py:133` `publish` (max+1, retry on unique key, `GuidelineUnchanged`) |
| Withdraw rules (latest only, refused while a live set is certified) | `pack/guidelines.py:233,238,275`, `guidelines_db.py:265` |
| Pin and its validity | `pack/guidelines.py:106,255` (`pin_of`, `pin_problem`) |
| Section diff, stale marking, effective dating | `guidelines.py:197`, `guideline_extract.py:69`, `version_windows.py`, `activation_window.py` (SDK ahead) |
| Guarded fixers, relint before write, write at the revision read | `pack/lint_fix.py:200-320` |
| Lint comments, triage, filters, readiness | `lint_comments.py`, `lint_runs.py` |
| Review state machine with digest pin | `review.py:124,133` |
| Run lanes, heartbeat, reaper, journal, stop, drain, skip-locked claims | `runs/`, `fabric/db/locking.py` |
| Stale-run reclaim | `evaluation/_reclaim.py`, `runs/dispatcher.py:69` |
| Reviewer workbook, formula-safe cells, blank reviewer columns | `jtbd_compare.py:229`, `corrections_sheet.py` |
| Per-key lock across processes | `concurrency/guard.py:76` (Redis, fails open) |

## Workbench-specific, not candidates

Three-store reconciliation (Postgres, disk workspace, git): `reconcile.py`, `workspace_rehydrate.py`, `workspace_migration.py`,
`tombstones.py`, `staging_store.py` worktree lane. The SDK keeps drafts in Postgres and blobs in `fabric.blob`, so there is no
projection to reconcile. Also Knowledge Hub entity generation and MACER findings comparison (`eval_findings.py` G4), loan-package
cloning (only the pure id remap, 15 lines, could be lifted if a consumer asks), the git-branch publish machinery, child-session
isolation for the Claude CLI, xlsx cell diff, and the mortgage metric semantics in `audit_review.py`.

## Candidates, ranked by value

Size is lines of SDK code and tests excluded, per candidate. "Version" says whether it fits a patch release of the SDK (a fix
or one small module) or wants a minor.

| Rank | Id | Candidate | General | Size | Version |
|---|---|---|---|---|---|
| 1 | F1+F4 | Ontology source: fetch from the Knowledge Hub, corruption gate, provenance stamp, seed fallback, never raises | yes | ~250 + 30 | minor |
| 2 | B-C1 | Reference-classified job dependency edges and metric cycles | yes (cue list is pack data) | 120-180 | minor |
| 3 | A-C1 | Session-scoped advisory lock, try and poll, on a dedicated connection | yes | 60-90 | patch |
| 4 | B-D1a | Base-moved refusal and conflict-marker publish gate | yes | ~45 | patch |
| 5 | E1+E2 | Pre-flight retry with attempts and backoff; stop-requested stale run reaps as stopped | yes | ~80 + ~15 | patch |
| 6 | B-C6, C4, C3 | Pattern exemption in lint filters; remedy text on findings; fix-class metadata on codes | yes | 25 + 15 + 40 | patch |
| 7 | G2, G3 | Two-phase text-set reconcile with verify pass; value canonicalization with negation guard | yes | ~250, ~80 | minor |
| 8 | A-C2a | "Pack pinned behind latest guideline" report | yes | 40-60 | patch |
| 9 | B-C2 | Within-job repeated-block detection | yes | 70-100 | patch |
| 10 | F3, F2 | Budgeted catalog-to-prompt renderer; delta wiring at adoption | yes | ~150, ~60 | when an authoring agent needs it |
| 11 | B-D3, D4 | Reviewer "seen" tracking; comment side, quote anchor and comment events | yes | 60-90; ~65 | wait for a consumer |
| 12 | Rest | See "Deferred" | | | |

### 1. F1+F4 Ontology source (area F)

- Workbench: `app/services/ontology_refresh.py:57-98` `refresh_ontologies` (TTL-gated, `asyncio.Lock`, never raises, outcomes
  `adopted | unchanged | rejected: <reason> | unavailable`), `:140-183` `_adopt`, `:234-281` `_extract_schema` (nine envelope keys; a
  measured sandbox failure left the stamp on the bundled seed for weeks). `mpr/ontology_store.py:182-201` `reject_reason` (not an
  object, no `$defs`, under `MIN_ENTITIES` = 5, no entity with properties; corruption, not policy), `:105-127` `Stamp` (source, id,
  fetched_at, sha256, entity and field counts), `:305` atomic save that degrades to keep-previous. One stamped artifact feeds both
  the validator and the prompt builder.
- SDK today: `clients/knowledge_hub_client.py:1029` `read_ontology`, `:1881` `resolve_current_ontology`; `fabric/graph/store.py:437`
  `resolve_ontology` is a pass-through that raises. `pack/catalog_reference_db.py:95-130` is an immutable `(tenant, id, version)`
  library with a content digest but needs the caller to supply the schema, does not poll, and carries no seed or fetched provenance.
  Greps for `reject_reason`, `bundled_seed`, `fetched_at` found nothing; the SDK's own client names the field `json_ontology` on create
  but offers no read-side unwrap.
- Gap: a consumer-neutral source that fetches a named ontology, gates plausibility (floor and required entities as config), stamps
  provenance, keeps a local seed, never raises, and exposes a local read. Adoption can write into `DbCatalogReferenceStore`, which gives
  versioned history and the digest check; `vocab_compare.diff_catalogs` supplies the removal and addition delta (F2).
- General: yes. The two named ontologies and the `JTBDSet` requirement become config.
- Size: about 250 lines in one module (`pack/ontology_source.py` or `vocabulary/kh_source.py`) plus a config model, and about 30 for
  an `ontology_schema(body)` helper on the client.
- Not verified: whether Plato already polls the Knowledge Hub for ontologies; how a pack `catalog.json` relates to a hub ontology in
  Acra flows; `app/services/kh_config.py` (config lookup, workbench-specific) was not read in full; whether `diff_catalogs` accepts raw
  hub JSON Schema.

### 2. B-C1 Reference-classified dependency graph (area C)

- Workbench: `jtbd_audit/cycles.py:63-182` classifies each sentence naming another job as benign (disclaimer, anti-double-count,
  citation, ownership gate, data handoff) or dependency (routing, coupling, consumes verdict) and requires the cue to govern the
  mnemonic (`classify_reference` 117-182; `PATCHES.md` records 8 of 11 edges false without it). The edge keeps its evidence sentence
  (`:246-282`). A separate metric graph (`:285-307`, `app/services/metric_cycles.py:1-60`) treats a reference inside one job and a
  pointer ("same definition as X") as no input.
- SDK today (checked): `pack/jtbdset_lint.py:197-211` draws an edge for any mention plus `depends_on`, then `_cycles` (258-292) emits
  `dependency-cycle` and `cross-section-dependency` as errors. An ownership disclaimer is therefore an edge and can be a cycle error.
  No metric graph, no same-job exemption, no evidence sentence in the detail.
- Gap and generality: structure is general; the English cue vocabulary is authoring idiom, so it should be a pack-declared cue list
  (`export_profiles/` already carries per-consumer config, `jtbdset_lint.py:51-55`) or a model labeler like `jtbd_align.model_labeler`
  (`jtbd_align.py:151`), with regexes as the default.
- Size: 120 to 180 lines in `jtbdset_lint.py` or a new `pack/job_references.py`.
- Not verified: how often the SDK edge fires falsely on a real set. This is measurable at no spend by linting the current Acra bundle
  jobs and counting `dependency-cycle` hits against their sentences; I would do that before proposing the build.

### 3. A-C1 Session-scoped advisory lock (area B)

- Workbench: `scripted_staging_lock.py:34-47` (own connection, `pg_try_advisory_lock`, `SessionBusyError`, unlock in `finally`);
  `git_jobs.py:168,220` `session_advisory_lock` and the async form (poll with deadline, dedicated AUTOCOMMIT connection, `invalidate()`
  not `close()` on a failed unlock, connection stashed so a cancelled await still releases). Two more copies of the poll shape in
  `main.py:115` and `db/migrate.py:57`. It exists because a transaction lock is released by any commit and publish commits partway.
- SDK today (checked): only `advisory_xact_lock` and `try_advisory_xact_lock` (`fabric/db/locking.py:53,63`). `concurrency/guard.py` is
  Redis, message-shaped, and fails open on a Redis error, so it cannot guard a must-not-run-twice section.
- Gap: hold "one at a time per key across replicas" across commits, with try-and-refuse and poll-with-deadline forms, safe under
  cancellation.
- General: yes, the key is a string. Fits `fabric/db/locking.py` beside the other two. sqlite is a no-op like the transaction helpers.
- Size: 60 to 90 lines, async only, using the `DbStore.engine` property (`fabric/db/store.py:248`).
- Not verified: interaction of a long-held dedicated connection with `fabric/db/session_guard.py` and `shield.py` (unread); a pooler
  in transaction mode (for example pgbouncer) would break session locks, and the workbench's deployment pooler was not checked.

### 4. B-D1a Base-moved refusal and conflict-marker gate (area D)

- Workbench: `app/api/proposals.py:796-883` three-way baseline merge and conflict recompute; `services/git_provider.py:242-326`
  `has_conflict_markers` (loose, a gate) and the strict line form.
- SDK today: a draft records `base_version` (`pack/draft_db.py:70,206,266`) and a review does too (`review_db.py:53,130-143`), but
  nothing compares it to the pack's latest published version; `DraftMoved` (`draft_db.py:144`) covers concurrent edits within a
  draft only. Datasets already do this (`evaluation/datasets.py:31` `DatasetConflict`). No marker gate on publish.
- Gap: two drafts, or a draft and a direct publish, diverge silently and the later publish overwrites.
- General: yes. Size: about 30 lines for the refusal plus 15 for the marker gate. The merge itself (120 to 200 lines of pure-Python
  diff3, since `git merge-file` adds a runtime git dependency) is deferred: the SDK's unit is one pack with one active review, so
  multi-writer conflicts are rarer than in the workbench's shared baseline.
- Not verified: Plato's publish route (reviewed after approval, then `store.put`) was not read; if it already checks the base, this
  is moot. Whether the deployed image has git was not checked.

### 5. E1+E2 Run-layer retry and stop labeling (area E)

- Workbench: `policyforge/agent_jobs.py:609` `fail` and `:704-745` `fail_orphaned` requeue a job that never reached `started_at`
  (attempts below max, `run_after` backoff, ids cleared) and park a started job as failed; `mark_started` `:493` draws the boundary.
  `:654-701` `reap_stale_cancelling` settles a long-cancelling job as cancelled, with no crash text.
- SDK today: `runs/store_db.py:573-595` `reap_stale` marks every stale RUNNING run FAILED with `reaped_reason`, ignoring
  `stop_requested`. Greps for `max_attempts|run_after|attempts` in `runs/` found nothing; only `release` returns a claim to QUEUED
  (drain).
- Gap: E1 a run that died between claim and first step is failed and the caller must resubmit; E2 a run the user stopped then
  orphaned shows FAILED with a stale-heartbeat reason instead of stopped.
- General: yes. Size: E1 about 80 lines over `runs/schema.py`, `store.py`, `store_db.py` (attempts, max_attempts, not_before,
  started_at, a `mark_started`, requeue-or-fail in both stores' `reap_stale`, claims honoring `not_before`); E2 about 15 lines.
- Not verified: where `ChatCoordinator.execute` would signal "started" (the first journaled event is the natural point); whether the
  record needs a column or fits the `data` JSON; whether a host already treats FAILED plus `stop_requested` specially.

### 6. B-C6, C4, C3 Small lint additions (area C)

- Pattern exemption: workbench `audit_review.py:96-140,221-295`. SDK `lint_runs.py:173-226` `LintFilters.false_positives` match code
  plus subject exactly, so a rule-wide exemption needs one entry per subject. Add a `detail_matches` regex on a filter entry with the
  same mandatory reason, validated in `read_filters`. About 25 lines. The workbench's metric-arithmetic conditions stay out.
- Remedy: workbench `audit_comments.py:171-182` `body_for(detail, fix)`. SDK `lint_comments.py:77-79` `_body` is severity, code and
  detail only and `PackLintFinding` (`lint.py:25-35`) has no remedy. About 15 lines plus a per-code remedy table (the authored part).
- Fix class: workbench `slop_cleanup.py` DELETABLE vs REWRITE, `audit_autofix.py:391-411` `autofixable`, `slop_spans.py:57-90`
  policy-marker downgrade. SDK has `default_fixers` (`lint_fix.py:192`) and `UnknownFixer`, but a caller cannot ask whether a code is
  auto-fixable or judgement-only without trying. About 30 to 50 lines: a code table beside `CHECKS` and a `fixable(code)` helper. The
  lender-specific marker vocabulary stays pack data, not SDK data.
- Not verified: whether jaci or Plato derive any of this client-side; whether anyone has hit the per-subject filter burden.

### 7. G2, G3 Set reconcile and value equivalence (area G)

- G2: `eval_compare/eval_findings.py:2194` `llm_dedup_within_set`, `:1993` `_prematch`, `:2537` `llm_compare_dedup_sets` with a verify
  pass each way (`:2503`). SDK matchers work on `JtbdItem` structure (`jtbd_match.py`, `jtbd_align.py`); no within-set text dedup, no
  verification of "dropped" and "net-new" claims. Domain-neutral shape: strings in, `{in_both, only_a, only_b}` out, model injected
  like `jtbd_match`'s `tie_breaker`; reuse `text_similarity`. About 250 lines in `evaluation/set_reconcile.py`, prompts about 40.
- G3: `eval_findings.py:1668-1745,2701,2758` numeric-aware value normalization, a negation guard, and "resolve once, then read
  deterministically". SDK has no value-equality helper (`aggregate/reconcile.py` votes between values as given). About 80 lines in
  `evaluation/value_equivalence.py`.
- Not verified: the prompts and the verify decision (signatures and docstrings only, `:2537-2636` unread); any published false-drop
  rate; whether `evaluation/scorers.py` or `metrics.py` already normalize values; `finance/` was not searched.

### 8. A-C2a Behind-latest report

Workbench `guideline_governance.py:386` `out_of_date` derives, never stores, "live set assessed against an older G"; unpinned sets
are unknown, not stale. SDK `pin_problem` (`guidelines.py:255`) checks validity only; no comparison with the latest; the pieces
(`GuidelineStore.latest`, `pin_of`, `guideline_changes` `:294`) exist. About 40 to 60 lines in `guidelines.py`. The explicit
"certify forward" record (`:369`) conflicts with immutable manifests and is a design question for the user (mutable certification-event
table, or just publish a new pack version); I would build the report only. Not verified: whether Plato already shows this.

### 9. B-C2 Within-job repeat detection

Workbench `jtbd_audit/redundancy.py:37-168` (6-word shingles, Jaccard clusters by union-find, `self_repeats`). SDK
`text_similarity.py:23-52` has `tokens`, `jaccard`, `tfidf_vectors` but nothing flags a job repeating itself; `lint.py:497-520` covers
duplicate citations and padding only. About 70 to 100 lines, reusing `jaccard`; the 0.75 and 120-character defaults must become config
and are unmeasured on SDK text.

## Deferred (real, but cost high or demand unproven)

- Three-way text merge (A-C3, D1b): refuse-on-moved is the SDK's current choice; revisit when a flow hits `DraftMoved` often.
- One-shot secret hand-off through Redis with a TTL matching the token (A-C6, `background_jobs.py:120-171`): general and about 40 to
  60 lines, but security-sensitive and it may be moot if SDK workers get the user token another way (`server/inbound.py`,
  `scope_claims.py` unread).
- Byte-preserving span fixers (B-C7): a one-line fix is a whole-file diff today because `fix_file` re-dumps YAML (`lint_fix.py:240`,
  reports `reformatted`). 150 to 250 lines plus a dependency decision (`ruamel.yaml` under the `>=` rule). Benefit depends on how
  often reviewers see reformat noise.
- Fix-order scoring (B-C5), model-driven fix loop (B-C8), job-set fixers (B-C9), suggested version bump (A-C4, B-D2): no consumer has
  asked; D2 would derive from `ReleaseReport` (`release_report.py:230`) rather than the workbench's path count.
- Single-flight job helper (A-C5), disposable collection copy (A-C7), queue position (E3), result cache by input digest (G1),
  reviewer-column helper (G5), MLflow run-by-name (G6), token-from-usage context size (E5, only if `claude_agent_sdk` is adopted).

## Where this note could be wrong

- Plato was not searched; F1, E1, A-C2a, D1a and D2 are the likeliest to exist there already.
- `agent_jobs.py` (1,239 lines) was read in part; `eval_findings.py` (4,721) and `eval_findings_output.py` (2,020) were sampled;
  `app/api/proposals.py` (4,319) was read for about 700 lines (publish and raise bodies skimmed).
- Not read: `fabric/db/session_guard.py`, `shield.py`, `server/policy_extract_runs_db.py`, SDK server routes, `kh_config.py`
  beyond function names, `agents/interactive/inventory.py`, `util/xlsx_safe.py` body.
- No size has been tested; each is an estimate from reading.
- None of the quick, measurable ones were measured: the false-edge rate of the SDK mention graph (rank 2) is the first thing worth
  measuring, at no spend.

## Addendum 2026-10-31: false-edge rate of the mention graph (rank 2), measured

Read-only, no spend, `jazzx_sdk` untouched. Method: the edge loop of `jtbdset_lint.py:197-211` was reproduced outside the SDK (same
regex over each job's requirement texts, plus the evidence sentences), `lint_jtbdset` itself was run for the reported codes, and 45
edges were hand-labeled from the sentences that cite the other job.

### Counts

| Set | Jobs | Mention edges | Cross-section | Cycles reported |
|---|---|---|---|---|
| Pulte (kernel-lab `pulte-6-2-jtbds.json`, 115 jobs) | 115 | 192 | 0 | 7 |
| Acra standard (bundle `jtbdset_standard.json`) | 114 | 0 | 0 | 0 |
| Acra platinum (bundle `jtbdset_platinum_select.json`) | 81 | 0 | 0 | 0 |
| Workbench dev set (20 `.md` jobs under `dev/main`) | 20 | 0 | 0 | 0 |

- Only Pulte-style sets fire. Acra mnemonics are long dotted ids that prose never cites, and the workbench dev jobs cite no other job
  code at all, so the false-edge question is about short family mnemonics cited in prose (the Pulte catalog and anything imported
  from it). The jaci Pulte pack was not run separately: it carries the same 115 jobs the kernel-lab file does (not diffed line by line).
- 100 of the 192 edges have a reverse edge, which is what makes the cycles. `_cycles` returns whole strongly connected groups: the 7
  are groups of 2, 2, 2, 3, 4, 9 and 19 jobs.

### Hand labels (45 edges, random sample, seed 7, from the 192; labeled on the evidence sentences shown, first two per edge)

| Label | Edges | Share |
|---|---|---|
| Dependency (routes work to the other job, consumes its verdict or figure) | 16 | 36% |
| Ownership disclaimer ("handled independently by", out-of-scope lists, anti-double-count) | 20 | 44% |
| Cross-reference ("see X", "per X rules", citations) | 8 | 18% |
| Other (edge points the wrong way) | 1 | 2% |

- **False-edge rate: 29 of 45 = 64%** (about plus or minus 14 points at 95%, from the sample size alone). Counting four borderline
  cross-references that lean toward a dependency as real, it is 25 of 45 = 56%.
- A labeling choice that matters: an edge counts as a dependency if any of its shown sentences is one, and routing counts (the workbench
  treats routing, coupling and consumes-verdict as dependencies). Only the first two sentences per edge were read, so edges with more
  citations (up to 6) may hide a real dependency; the rate is, if anything, a little high.
- One labeler, one pass, no second read. The labels are in the scratchpad (`labels.txt`, 45 lines) and are not durable.

### Cycles

- 4 of the 7 were traced edge by edge and none is a real cycle: `IDN-NUS/SSA/SSV` (every edge is an out-of-scope list), `INS-FDC/FZD` (one
  edge is "does NOT own", the other a one-way gate), `LIA-PMT/REO` (both "owned by"), `LIA-BAS/DTI` (one real consume, one
  scoping sentence).
- The 3 large groups (4, 9 and 19 jobs: the gift and equity assets, the asset section, and the income section) were not traced edge by
  edge. Their sample edges are mostly disclaimers with a few real routes and consumes (income jobs consume `INC-VER`; `INC-OTH` routes out
  to `INC-SSA`, `INC-LTD`, `INC-ERA`, `INC-BOR`), so the groups are held together by mutual disclaimers. Whether any real cycle sits
  inside them is unmeasured.
- Every one of the 7 is an `error` today (`dependency-cycle`), so a consumer gating on errors would be blocked by all of them.

### Cue words that separate the classes (from the sentences, English authoring idiom)

- **Disclaimer (drop the edge):** "handled independently by", "responsibility of", "owned by", "does NOT (own|calculate)", "must not /
  may not also be counted", "anti-double-count", "separate from this JTBD", "reads the same ... independently", "do not condition for",
  "NOT a cross-section hand-off"; and a bullet that is only `... (XXX-NNN)` or `... - XXX-NNN` inside a "not owned" or scope list.
- **Cross-reference (no edge, or a weak one):** "see X", "(see X)", "per X rules", "per the corrected X rules", "implementation cells".
- **Dependency (keep):** "route (extracted types) to X", "route to X", an arrow `-> X`, "verified per X", "provisional until ... verified per
  X", "conditional on documentation", "that X publishes", "qualifying liabilities per X", "From the ... roster (X)", "when ... path is
  used (X)".
- One trap: "handled independently by X" also appears where the work really is handed over (`CRD-DERG` to `CRD-EXT`,
  `AST-DATP` flagging large deposits to `AST-NSUD`), so the cue needs the surrounding verb ("flagged for", "when this path is used").
- Direction: a mention in a list of downstream jobs ("before downstream jobs (X, Y) compute") is an edge from the producer to the
  consumer, the reverse of what the lint draws (`INC-EMP-DOC` to `INC-BON`).

### A crude cue check (not a proposal for the rule)

A two-regex classifier built from the cues above (dependency cues first, then disclaimer cues, else cross-reference), scored on the same 45
it was written from, agrees on 40: it keeps 13 of the 16 dependencies and wrongly keeps 2 non-dependencies. Applied to all 192 it keeps 59 (31%).
That is in-sample, so it shows the cues separate the classes rather than how well a classifier would do; it needs a held-out sample (not drawn).

### What this says for the build

- A mention is not a dependency: roughly two edges in three are not, on the only corpus where the lint fires. Suggested shape, unchanged
  from rank 2: classify the sentence, keep the sentence as the edge's evidence, report the classified graph, and keep `depends_on` as a
  hard edge.
- The cue list should be pack data (`export_profiles/`) with this list as the default, since the idiom is the authors', not the SDK's.
- Not measured: held-out accuracy, a second labeler, the large cycle groups, and any set outside these four.

### Addendum 2: held-out labels and the three large groups

Files (scratch, durable): `docs/status/edge_labels_pulte_batch1.tsv` (the first 45, my labels), `edge_labels_heldout_pulte.tsv` (45 more,
seed 11, none of batch 1), `edge_labels_pulte_groups_blind.tsv` (109 edges inside the three large groups). The last two were labeled
blind by a second labeler (a subagent given only the four class definitions, no cue list and no earlier labels), with a confidence per
edge; the sentences shown are the first three per edge.

- **Held-out rate:** 16 of 45 dependency (36%), 15 disclaimer, 13 cross-reference, 1 wrong direction. False-edge rate 64% again, so
  the first estimate held on a second sample and a second labeler.
- **Labeler agreement** on the 34 batch-1 edges the blind labeler also saw: 25 exact (74%), 28 on dependency versus not (82%). All six
  disagreements are the blind labeler calling dependency what I called disclaimer or cross-reference, on edges whose text mixes an
  ownership preamble ("does NOT calculate ... responsibility of the downstream JTBDs") with one real hook ("if INC-RET is unavailable",
  "route to INC-MIL"). The edge-level rule "any dependency sentence makes the edge a dependency" is therefore the source of most
  disagreement; classifying per sentence, and keeping the edge as the strongest sentence, is the stable shape.
- **Inside the groups the share is higher**, not lower: 58 of 105 edges in the 19-job income group are dependency (blind), 8 of 27 in the
  9-job asset group, 2 of 7 in the 4-job gift group. Those are not random samples of the 192, so they do not change the 64% estimate; they
  say the large groups contain real edges, mostly "verified per INC-VER" and "From the Set 0 roster (INC-META)".
- **Real cycles among dependency edges (blind labels, all 139 edges inside the three groups):**
  - 4-job gift group: one 2-cycle, `AST-GIFT` and `AST-GDNR`. `AST-GDNR` requires gift eligibility validated in `AST-GIFT` first (high);
    `AST-GIFT`'s confidence table reads "AST-GDNR source complete" (low). A mutual dependency in the text, not a deadlock.
  - 9-job asset group: no cycle. The dependency edges run one way from `AST-TYPE`, `AST-RSLE`, `AST-FCDP` toward `AST-DATP`, `AST-NSUD`,
    `AST-CRDPC`, `AST-EMP`, `AST-GRT` (8 edges); the cycle error comes only from disclaimers and cross-references.
  - 19-job income group: with every dependency edge (58) a 15-job group survives, held together by the hub `INC-VER` (consumed by
    nearly every income job, and routing back out to eight). Restricted to the 43 high-confidence edges, one 4-job cycle remains:
    `INC-META`, `INC-MIL`, `INC-VER`, `INC-WAG`, from two mutual pairs: `INC-META` routes VA income to `INC-MIL` and `INC-MIL` lists its
    components from the `INC-META` roster; `INC-VER` routes temporary-leave income to `INC-WAG` and `INC-WAG` is verified per `INC-VER`.
    Each is a hand-off plus a consume, which the text really says; whether that is a defect or just "verify, route, calculate" is a
    policy call, not a lint fact.
- Consequence for the 7 cycle errors: 4 are false, 1 (gift, 2 jobs) is a real mutual dependency, and 2 big groups reduce to a 4-job
  core (income) or to nothing (assets). Cycles on dependency edges alone are far fewer than the 7 reported, and the surviving ones
  are mutual hand-offs, so severity on `dependency-cycle` is a decision the user may want to make.
- Not done: a second labeler for batch 1, a third pass on the 19 low-confidence income edges, any set beyond Pulte.
