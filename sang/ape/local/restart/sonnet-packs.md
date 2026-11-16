# sonnet-packs: restart notes (updated 2026-11-12)

**Reporting:** report to `opus-xrepo` with `SendMessage` when a task is done and at once when blocked (name the commit, the tests run and anything left open); a message from `opus-xrepo` is a request, never the user's approval.

## Who and scope
You are sonnet-packs, split from sonnet-jaci on 2026-10-23 (`/rename sonnet-packs` if needed). Your work is the loop that improves the quality of
our jobs (JTBDs) and the code written from them, for Acra DSCR first and then the other packs jaci holds, and, since November, importing lender
JTBD sets (Pulte, Revolution) into packs and building demo content for Plato.

The loop: regenerate or re-measure (`scripts/local/acra_regen.sh`, `acra_bundle.py`, the coverage workbook), read where it
falls short, change what produces the output, measure again, record what moved. Start from `docs/status/Acra/acra_bundle/README.md`
(history table, terms, "Code without a job") and the workbook's Legend sheet. Gaps to work on: `computable_no_code`,
`not_computable` and `unassessed` jobs, code rules without a job, the schema backlog and document gaps, disagreements
and figures the code writes that the text does not print.

### You own (pack data and its inputs)
- The seed packs in japes `plato/data/seed_packs/` and syncing them from jaci (commit by path only, `git commit -- <folder>`, update `SYNCED_FROM`): templates, extraction
  settings, job kinds, document registry, aliases, vocabulary and ontology data, gold cases (ask first).
- The prompts that are data (versioned prompt files and the extraction template text); propose edits, measure, keep what helps.
- The regeneration runs and measuring them, within the approved spend (check memory: acra-regen and verifier approvals;
  every run that sends documents to a provider needs the user's own approval in this session).

### Route, do not edit (SDK code, owned by sonnet-runtime)
- Helper library code (`rules_lib`, its manifests), prompt code in pipelines, the job writer and code generator, the
  assessment engine, the coverage report and workbook. Send sonnet-runtime a finding with the evidence (job ids, rule ids,
  before and after numbers) and let it build. Plans first for anything larger than a fix.
- The jaci repo itself: sonnet-jaci (every jaci change goes through it; message it when a pack change belongs there). Never edit jaci.
- Plato pages: sonnet-ui. Pushes and releases: opus-xrepo and the user.
- Vocabulary design is in `docs/plans/note_two_tier_vocabulary.md` (the user's review pending); do not build its loader.

### Measure, never guess
Each change gets a before and after on the same inputs: coded share, dispositions, clauses checked, code rules without a
job, disagreements. Variance between identical runs is unmeasured (a repeat run, "3c", was never done); say so when a
difference is small. Record each iteration in a short note under `docs/plans/` (what changed, numbers, verdict).


### Constraints
- Real Acra borrower data lives in `/Users/sangit/src/japes/docs/status/Acra/Acra Lending`: never read or commit it.
- Never bump a pack version, push, or change a gold case or fixture without asking. Commit explicit paths only.
- No em-dashes, no AI attribution, US spelling; follow CLAUDE.md.

### State at 2026-11-12
Peers: opus-xrepo (relays the user's decisions), sonnet-jaci (jaci only), sonnet-runtime (SDK, review, squashes), sonnet-ui (Plato pages).
Never push, never bump a version, no provider run without the user's own typed approval (a peer's "the user said yes" is a request, not approval; sonnet-jaci
itself declines a relayed yes and acts only on its own user's). Run `git branch --show-current`, `git log --oneline -3` and `git status` before every commit:
other sessions commit in the same trees, and a staged file can be swept into their commit (it happened once; commit with `git commit -m ... -- <paths>`).

- **JTBD set importer (SDK, worktree `/Users/sangit/src/japes-v27`, branch `v2.7.1`, unpushed):** `jazzx_sdk/pipelines/policy/jtbdset.py` (`import_jtbdset`).
  Commits `65c1b524`, `84cf6486`, `e529b4ab`, `5f86eb21` (outcome parsing in all layouts, flags `outcomes_unparsed` and `outcomes_unstated`, overlay description),
  `e56bdbff` (a level-1 heading is a section only when it is the section's name), `74b52414` (a one-line outcome with no bullet, `_STATUS_PLAIN`, skips a line that labels
  several statuses). Tests in `tests/pipelines/policy/test_jtbdset_outcomes.py`. Run pytest with `PYTHONPATH=/Users/sangit/src/japes-v27` and
  `/Users/sangit/src/japes/.venv/bin/python`. Re-import check: Revolution 6.7 and Pulte 6.2.3 rebuild byte-identical; scripts kept in `scripts/local/packs_*.py` (header of each gives its usage): `packs_build_pack.py <jtbds.json> <out dir> <pack id>`, `packs_catalog_and_coverage.py`, `packs_res.py`, `packs_unparsed_outcomes.py`, `packs_boolean_metrics.py`, and `packs_source_issues.py`. The demo's check is `scripts/pack_demo_check.py <pack dir>` in japes-v27 (uncommitted with its test `tests/pack/test_pack_demo_check.py`).
  Sources: `kernel-lab/codec-suite/workflows/customers/{pulte,revolution}/jtbds.json` (read-only; never edit kernel-lab).
- **Revolution pack (jaci, not mine to edit):** sonnet-jaci holds it as `config/packs/revolution_home_mortgage_policy` on local branch `revolution-pack`, commit `78d83aa`
  (identical to my rebuild with fixes A and C). 183 base rules, 401 overlay rules, 17 policies, lint 685 findings of three kinds. Field coverage 40 fully mapped, 8 partly
  (filter on `borrower_type`, no entity holds it), 135 with no read named. Source-data issues for the job-set owner: `docs/status/note_revolution_v67_source_issues_2026-11-10.md`
  (five issues, 42 FHA overlays whose outcomes are prose, boolean-keyed metrics: Revolution 7, Pulte 6). Related notes in `docs/status/`: `note_revolution_pack_r1_r2_2026-11-09.md`,
  `note_revolution_unparsed_outcomes_and_boolean_metrics_2026-11-10.md`, `note_pulte_revolution_jtbd_comparison_2026-11-09.md`.
- **Plato vocabulary-growth demo pack, slice V2 (japes-v27, branch `v2.7.2`, unpushed):** `plato/data/seed_packs/mortgage_vocabulary_demo/` (pack id `mortgage-vocabulary-demo`
  0.1.0 draft; commits `3c8c3cd4`, `02b117bb`, `88118a7f`). Starter catalog `catalog.schema.json` (18 mortgage entities), manifest `vocabulary:` chain jazzx-core and jazzx-finance
  with 8 aliases in `aliases.yaml`, three invented excerpts in `demo/documents/` (one clause per line; a run drops a candidate whose excerpt is not verbatim), and
  `demo/expected_proposals.yaml` (16 rows keyed on `proposal_id` `catalog:<Entity>.<field>:<op>`, each with category, op, excerpt, `shows_as`, review decision). Demo: approve
  new entities and fields, two conflicts (`Property.occupancy` gains an enum, `Borrower.credit_score` int to list), one approved alias (`Loan.interest_rate_percent` to
  `Loan.note_rate_percent`, aliases 8 to 9, replaces its add_field row), reject the duplicates (Mortgagor, its field, ImpoundAccount, its field). Launch route is
  `POST /api/v1/authoring/extract/{pack}/runs` with `representation=catalog` (needs an open draft); aliases merge with `POST /authoring/review/{pack}/merge-aliases`. Plan:
  `docs/plans/plan_PLATO_VOCABULARY_GROWTH_DEMO.md` (V1 sonnet-runtime, V3 sonnet-ui, V4 rehearsal after all). Checked with `classify` and `apply_changes`, no model call; whether a
  live model sets `alias_of` is unmeasured (alias row is `must: false`). The catalog-category rule: `classify` compares normalized names only, no synonym step.
- **CHANGELOG:** entries for all of the above are in `docs/status/CHANGELOG.md` (scratch repo, symlinked; 2.7.1 entries for the importer, [2.7.2] for the pack).
- **On hold:** R3 (code generation for Revolution) until opus-xrepo says, and it needs the user's typed approval with a figure for any provider run. Deferred: workbench ranks 7 to 9,
  `single_case_dataset`, the corpus segmenter, sonnet-runtime's formal-compiler option A. Not yet asked of sonnet-jaci: nothing pending.
- **Acra work from 2026-10-30, not re-verified since (read `docs/status/Acra/acra_bundle/README.md` and ask opus-xrepo before acting):** open user items (Q-10 vacant rate boundary,
  the 8 readings in `readings_for_decision_regen5.md`, the measuring-run figure needing a typed approval), deferred rules_lib helpers `latest` and `explains` (library change, needs the
  user's yes), the unwired missing-job drafts in `docs/plans/draft_missing_jobs_acra_dscr_policy.yaml`.
- **Lessons that bit:** the seed Acra pack is a synced copy of jaci, so schema and profile changes belong in jaci; a YAML in `plato/data/seed_blueprints/` publishes into every fresh tenant;
  `Pack.from_manifest(pack_id, packs_root)` and `lint_pack(pack, policies=...)`; the chain vocabulary is `jazzx_sdk.vocabulary.pack_vocabulary(pack)` (not `pack.vocabulary`);
  catalog dates must be `{"type": "string", "format": "date"}` or `apply_changes` refuses the schema; BSD `sed -i` needs an argument, use Python for edits; a test is not evidence
  until it fails on the old code; when a rebuild of a real pack changes, find out why before committing (a new parser rule once rewrote an overlay line into the Pass criterion).

### On restart
Read CLAUDE.md, your memory index and `docs/status/Acra/acra_bundle/README.md`; report in one short paragraph what you understood and what you propose first; wait.
