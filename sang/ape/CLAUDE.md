# Claude Session Status

**Last Updated**: 2026-09-28

## Where things stand

**Working branch is `v2.5.8`** (cut 2026-09-30 from `dev` at `2a2ad60b`, PR #86's 2.5.7 squash; no
shared history with `v2.5.7`; SDK 2.5.8, Plato 0.1.9; plan `plans/plan_v2_5_8.md`). `0d730452`
(cherry-pick of `28587bb9`: pack programs lint, DSCR seed regrouped) owes a review
(`REVIEW_UPSTREAM=origin/dev`). The first cut is kept as `backup/v2.5.8-from-v2.5.7`. Release flow:
working branch -> plato -> PR to dev -> squash -> PR dev -> main, recording each squash back down;
the next version is cut from `dev` once the squash lands.

**Working branch is `v2.5.6`**, on `dev` at the PR #78 formal squash (`7a7a0950`). Its first
slice (python executor) is squashed to `dev` (`da9a709d`) and `plato` (`6701d711`). Plato stays
0.1.7 by decision. Main release: `/tmp/japes_release_v255_to_main.sh` (v2.5.5 + formal to `main`
without 2.5.6) is written, for the user to run.

**Plato domain pack runtime** (`plans/plan_plato_domain_pack_runtime.md`, Rev 2): Phases 0, 1 and 2
built on `v2.5.6`, local and unpushed, folded (with the PR #82 follow-ups and the chat lifecycle) into one commit `ab080492` on top of `acb22f78`; squashed to `plato` as `43c13d18` (pushed). PR #85 (formal checks over canonical policy, Sourav) squash-merged to `plato` as `a1c099e3` and brought into `v2.5.6` as `99a0ef16` (tree copy). The #85 follow-ups (threshold required, fact catalog via `pack.schemas`, Plato-compiled packs only) and jaci's Plato pilot findings 1-5 (`status/done_plato_pilot_findings.md`) are fixed on `v2.5.6`, `9d840189..d7afdddc`, reviewed clean; squashed to local `plato` as `54ad90de`, push script /tmp/japes_push_plato_256b.sh
(the commit whose tree is dev's `da9a709d`); the 20 original commits are on
`backup/v2.5.6-pre-squash` (tip `c1fd38d8`). Reviewed clean in two ranges (to `7e99aeb9`, then
`4766c97a..c1fd38d8`). On top, `3c1cc377` answers PR #82's bot findings (reviewed clean);
PR #82 (`release/v2.5.5` to main) squash-merges as is, reply text in `/tmp/pr82_triage.md`.
Then the chat lifecycle for jazzx-assistant (their Notion ask, review in
`/tmp/japes_256_chat_requirements_review.md`), `d7238eaa..df4bd2a6`, reviewed clean after 4 rounds:
stream waits for its engine, `ChatRun`/`run_chat_lifecycle`/`stream_chat_lifecycle` with the old
runners as adapters, `prepare`, `ChatError`/`chat_step_error`, completion on every path plus
`cancel_after_answer`, `persistence="caller"` + `persist_failure`. Adoption note:
`/tmp/jazzx_assistant_chat_lifecycle.md`. A full-range review
(`REVIEW_UPSTREAM=origin/dev`) is still owed before squashing to `dev`/`plato`. Phase 3 (human checkpoints, `SUSPENDED`, `/resume`) next.

**Acra DSCR programs** (2026-09-30, local, unpushed): in the v2.5.6 squash `fc48deb4` are the
seed split (`DSCR_PROCESS` core, `DSCR_STANDARD`, `DSCR_PLATINUM_SELECT`) and `assess`'s refusal of
omitted or non-nullable-null facts. On `v2.5.7` after its squash, `28587bb9`: lint reads a pack's
own policies for program checks, `rule_repeated_across_programs`, `MatrixAxis.domain_extensions`
band edges in the drift lint, the conductor raw-input decision, and the seed with PPP rules once in
`DSCR_PROCESS` and linked loan bounds; not yet on `dev`/`plato`. jaci branch `acra-programs` tip
`f3873da` needs it. Open: cap adjustments (declining market, Q-07/Q-08).

**Chat runtime coordinator** (jazzx-assistant's second Notion page, `plans/plan_chat_runtime_coordinator.md`):
Phase A (`b255d181..1da37c9d`) and Phase B B1-B5 (`aa59ddc6..cf3baa3a`: finish, admit, stop
reasons/deadlines, lanes, `runs.ChatCoordinator`, `RunWorker`/`settle_runs`; Plato `chat/stream`
runs on the coordinator) built on `v2.5.6`, local and unpushed; full Phase B review clean after 3
rounds. Tests also run on Postgres via `JAPES_TEST_POSTGRES_URL` (`daa41fc9`). Squashed to local
`plato` as `9a7042f2` (tree = v2.5.6 `9fae6002`, parent `origin/plato` `a1c099e3`, replacing the
never-pushed `54ad90de`, kept as `backup/plato-54ad90de`); push script `/tmp/japes_push_plato_256c.sh`.
Phase C (sessions/resources, outlets) not started.

**v2.5.7** (branch cut from `dev` at `428ee718` on 2026-09-29, SDK 2.5.7, Plato 0.1.8; plan in
`plans/plan_v2_5_7.md`). v2.5.6 is on `main` via PR #81 (squash-merged 2026-09-29); the user still
runs steps 4-5 of `/tmp/japes_release_v256_to_main.sh` to record that squash on `dev`. Done on
v2.5.7: section 1 (token accounting, held background tasks), 2 (KH policy/Rego surface removed;
no policy table, the pack store is the policy store), 3 (runs: first terminal write wins,
release on close, reaper TTL vs pool wait, claim headroom), 4 (audit items; 4.9, Platinum
Select's optional inputs, waits on a decision with Acra), 5 (sibling finds: deterministic
pack archive, caller headers on the feedback sink and eval-service client, MCP Host/Origin
checks plus the mcp 1.x start fix, `InputFilter` elision stubs with content-derived reference
ids), reviewed clean over `46c8e29a..d321abb9`; 6 (hybrid assessment `assess(reasoning_agent=)` +
`?reason=true`, the `conditions` extraction representation, evaluator-vs-Z3 agreement test and the
`JsonRulePack.overlays` fix), `a2aafc69..b518dd12`, reviewed clean. Then Z3 covers the whole DSCR
seed (in/not_in, any_of, ratio, 512-rule cap, contradiction pruning; exact ratios in `evaluate_ratio`),
`5d30990e..097c3015`; then the Postgres advisory-lock test, Plato extraction lint against the
tenant's draft (`ExtractionRun.linted`), uncomputable ratios withheld per rule, `097c3015..4e2067cb`;
all reviewed clean. Then the rest of the chat runtime page (the coordinator plan's Phase C, C1-C7:
deadlines, indeterminate commits and reconcile, four persistence policies, duplicate turns and
namespaced keys, sessions/single-flight/context providers, typed events and bounded outlets, a
profile `lifecycle:` block Plato runs), Plato's blocking `/chat` on the lifecycle, and model cards
(Sonnet 5.5 the Anthropic default, GPT-6.1 Sol), `4e2067cb..b3c1d36f`, reviewed clean. Then
declarative grounding (`status/done_declarative_grounding.md`, G1-G4: `pipelines.grounding` kinds,
`GroundedContext` to the agent per skill, `lifecycle.ground` on Plato, `knowledge:` compiled into
ground sources; a skill-less agent gets files inline), `b3c1d36f..6ec19406`, reviewed clean. Then
model defaults from the config table (dashed Anthropic ids, GPT-6 `max_completion_tokens`, no
retired defaults), one installed-kinds loader, and declarative compose
(`status/done_declarative_compose.md`: present/cite/humanize/leak_check, `DeliveryCheck`s),
`6ec19406..e037e55c`, reviewed clean. Then the preliminary answer (`status/done_preliminary_answer.md`:
`on_skill_result`, `Skill.timeout_seconds`, `lifecycle.preliminary`), `e037e55c..406c182d`, reviewed
clean. Then the Notion page's last gaps (`status/done_chat_turn_store.md`: `runs.ChatTurnStore`
begin/commit/fail/interrupt/reconcile, `caller_managed`, retained follow-ups, `interrupt_on_abandon`),
`406c182d..31e68dee`, reviewed clean. Then the trim (`3ca4448f`, `b2a7f53a`: every 2.5.7 docstring and
comment, README, docs/, examples/, package and pack READMEs cut to terse references; rationale lives in
the CHANGELOG since the SDK ships), and the final review over `428ee718..HEAD` with its fixes (`c606fc06`:
no refused request params to Anthropic, `reconcile(outcome=)`), re-reviewed clean. 2.5.7 is ready to
squash; only 4.9 (Acra) and the deferral TODOs remain. jazzx-assistant pins
`main` at v2.5.0, so 2.5.7 reaches them only through a dev->main release. CHANGELOG entries carry line counts; jazzx-assistant adoption note
`/tmp/jazzx_assistant_declared_grounding.md`. Squash script
`/tmp/japes_record_and_squash_257.sh` (the #81 record is on dev, `f910a0c9`) waits until 2.5.7 is done;
open: 4.9 (Acra decision), the deferral TODOs. Nothing pushed.

Work lands on `v2.5.6` and reaches `dev` and `plato` by periodic squash merges. The v2.5.5
paragraphs below describe what shipped in it.

**v2.5.5's primary item, the chat pipeline as an application turn engine, is built** (local,
unpushed, `a1aa7f79`..`f70c8f10`): `compose`/`persist` stages, `overrides=`, `pipeline_for`,
`error_code`, `GateDecision.verdict`/`refusal`, `ChatTurn.metadata`/`publish`. Design and the
jazzx-assistant mapping in `status/done_chat_turn_engine.md`; next is jazzx-assistant adopting it.

**Eval control plane moving into the SDK** (decided 2026-09-25; Plato and eval-service become thin
hosts, eval-service eventually retired). Plan in `plans/plan_sdk_eval_control_plane.md`. Steps 1-6
built on `v2.5.5` (datasets, experiments, custom scorers, Plato hosting, comparison, optimization;
`server/eval_api.py`); adversarial review clean after 4 rounds. `plato` was pushed at `188d1c2e`, one
squash commit with v2.5.5's tree at that point. Step 7 is queued as a branch in eval-service.

**Feedback service moving into the SDK** (decided 2026-09-26). Plan in `plans/plan_feedback_service.md`.
Steps 1-7 (records, config, processing, Plato hosting, retrieval/export/aggregate, into learning,
semantic via fabric.rag) built on `v2.5.5`. Step 8 (turn injection) waits on PR #54. Adversarial review
over the feedback range (`51b0b572..6a166508`) clean after 4 rounds. `plato` is pushed at `07919ee2`; local `d0e2543b`
on top carries PR #75 rounds 6-9 (tree = v2.5.5), awaiting `scripts/local/push_plato_feedback.sh`.
Round 9 is `f7510cb3` on local `dev` (carried to v2.5.5 as `9ffce263` + `2ab89df8`, the latter
withholding eval/feedback reads), from a full-range review of `origin/main..dev` that is now clean;
awaiting `scripts/local/push_dev_pr75_r9.sh`. **Run the full-range review
(`REVIEW_UPSTREAM=origin/main`) before a PR round, not only per-commit ones:** per-commit reviews
cannot see untouched code, which is what the bot kept finding. `scripts/local/pr_new_comments.sh <pr>` lists bot comments
since your last reply; `scripts/local/resolve_pr75_threads.py` replies to and resolves threads.
PR fix rounds go on `dev` first.

**`plato` is ahead of `dev`** by v2.5.5 (one squash commit, pushed 2026-09-26), which also carried
`cryptography >=50.0.0` and `mlflow >=3.16.1` over. `dev` gets v2.5.5 when you squash it there.

**`origin/main` is an ancestor of `dev` again** (`record_squash_on_main.sh`, run after PR #74
merged). The next `dev -> main` starts from there rather than replaying from v2.5.3.

**Squash merges break ancestry, so `git log A ^B` overstates what is missing.** Compare trees:
walk the source branch for the commit whose tree matches the target, and take the delta from
there. A `git merge --squash` from a long-diverged branch hits stale-base conflicts every time;
where the target provably carries no work of its own, `git read-tree -u --reset <source>` is exact
and conflict-free. **Check that precondition first** -- `dev` had diverged with a security fix
`v2.5.4` lacked, and a tree copy there would have reverted three CVE alerts.

## The adversarial review runs on Claude

`scripts/local/adversarial_review.sh` drives `claude -p` by default (`REVIEW_ENGINE=claude`),
pinned to `claude-opus-5-5` at high effort and read-only (`dontAsk` plus an allow-list of read and
`git` tools). `REVIEW_ENGINE=codex` runs `codex exec` instead, on Codex's own configured default
model and effort unless `REVIEW_MODEL` / `REVIEW_EFFORT` are set; Codex hit its quota on
2026-09-25, which is what prompted the switch. Claude reads this file directly; `AGENTS.md` is a
gitignored symlink to it for Codex.

Findings weighed and closed live in `scripts/local/.reviews/accepted.md`; the loop reads it and
will not re-report them. Two are recorded there now, both deliberate breaking changes to import
paths in an unreleased version.

## Working Principles

**Critical: Use Professional Judgment**
- Do NOT blindly accept every user suggestion
- Push back when you see better alternatives or tradeoffs
- Explain architectural concerns, performance implications, security issues
- Present alternatives: "Your proposal has X benefit, but Y tradeoff. Consider Z instead?"
- The user WANTS critical thinking, not agreement
- If uncertain, present options with pros/cons and let user decide

## Sibling Repos (local checkouts)

Every JazzX repo is checked out at `/Users/sangit/src/<name>` -- look there before reaching for the
GitHub API. `./scripts/local/sister_repo_activity.sh` surveys recent commits across them; per-repo
roles and the traps worth knowing (`assistant` vs `jazzx-assistant` are different repos) live in
memory rather than here, where the list only went stale.

## Related repos
- **jaci** (`/Users/sangit/src/jaci`) -- the primary real consumer validating this version.
  **Its venv is not editable against this checkout** (checked 2026-09-26): `pip show japes` reports
  a site-packages install of 2.5.3, so jaci does not see v2.5.5 work (eval, feedback,
  `FeedbackApiSink`). Run jaci tests against the working tree with
  `PYTHONPATH=/Users/sangit/src/japes .venv/bin/python -m pytest ...`, and for a live demo install
  editable (`uv pip install -e ../japes` in jaci). The ci_spread feedback-to-Plato wiring is
  uncommitted in jaci's tree.

## Notes
- Always update CLAUDE.md after significant discoveries or decisions
- This file is gitignored (see .gitignore:67) - local session tracking only
- Purpose: Maintain context across Claude sessions after accidental quits
- Keep this section current, not an append-only log -- replace stale status rather than
  stacking a new dated section on top of old ones; git history already has the archive.

---

## Documentation Standards

### What Goes Where

**Commit to Repository:**
- ✅ **CHANGELOG.md** - All user-facing changes, new features, breaking changes
- ✅ **README.md** - Current version, quick start, high-level capabilities
- ✅ **ARCHITECTURE.md** - System design, patterns, technical decisions
- ✅ **docs/** - User guides, tutorials, integration examples

**DO NOT Commit:**
- ❌ **Planning documents** - Analysis reports, comparison docs, decision matrices
- ❌ **Temporary reports** - Branch analysis, migration planning, feasibility studies
- ❌ **AI conversation artifacts** - Claude work summaries, task breakdowns

### Rationale

**Planning documents are transient:**
- They capture a moment in time during development
- They become outdated as soon as decisions are implemented
- They add noise to the repository history
- They don't help users understand the current system

**Commit the outcomes, not the planning:**
- ✅ Decision → Document in ARCHITECTURE.md with rationale
- ✅ New feature → Document in CHANGELOG.md with usage
- ✅ API changes → Update README.md and relevant docs
- ❌ "Should we do X or Y?" analysis → Use for decision, discard after

### Examples

**WRONG:**
```
docs/
├── macer_kg_vs_dev_report.md          ❌ Transient analysis
├── document_chunking_evaluation.md    ❌ Planning document
└── migration_options_comparison.md    ❌ Decision matrix
```

**RIGHT:**
```
CHANGELOG.md                           ✅ "Added document chunking framework"
ARCHITECTURE.md                        ✅ "Document Module Design"
docs/DOCUMENT_CHUNKING.md             ✅ "How to use chunking in your pack"
```

### Plan and status files

Plans and design notes live in **`docs/plans/`**, never in `docs/` itself. Both `docs/plans` and
`docs/status` are symlinks into `/Users/sangit/src/.scratch/sang/ape/`, which is **its own git
repository** -- so these files never enter japes' history (satisfying the "do not commit planning
documents" rule above) but are still version-controlled where they live. Treat them as tracked
files, not scratch.

**The lifecycle is a move, not a rewrite.** A file lands in `plans/` while it is live, and moves to
`status/` once it is done, stale, or superseded -- renamed with the prefix that says which:
`done_*`, `superseded_*`, `stale_*`. Nothing is deleted, and nothing live sits in `status/`.

```
docs/plans/plan_<topic>.md          live: being written, argued, or built against
        └─► docs/status/done_<topic>.md        built and shipped
            docs/status/superseded_<topic>.md  a later plan replaced it
            docs/status/stale_<topic>.md       overtaken by events, not replaced
```

**Move with `git mv`, from the `.scratch` repo root** -- a plain `mv` plus an untracked add loses the
rename, and the rename is the record of what happened to that plan:

```
git -C /Users/sangit/src/.scratch mv sang/ape/plans/plan_<topic>.md \
                                     sang/ape/status/done_<topic>.md
```

Naming: `plan_*` for a plan, `design_note_*` or `note_*` for an assessment that decides nothing.

**Read `status/` before writing a new plan.** It holds finished and superseded designs, which is
exactly where a new plan's prior art is -- and a plan written without it duplicates work and
contradicts decisions already made. `PLATO_PACK_TABLE_DESIGN.md` was written twice for this reason.
Grep both directories for the subject first; if a status doc covers it, revise against that doc
rather than starting from the code.

### Development Workflow

When implementing a new feature:

1. **Analyze** - Create the planning doc in `docs/plans/` (see "Plan and status files" above)
2. **Decide** - Document the decision and rationale in ARCHITECTURE.md
3. **Implement** - Write code and tests
4. **Document** - Update CHANGELOG.md, README.md, and user guides
5. **Commit** - Commit code + documentation (NOT planning docs)
6. **NEVER PUSH** - ⚠️ **CRITICAL: Never run `git push` without explicit user approval**

### Git Commit and Push Policy

**Commits: ✅ ALLOWED**
- Create commits with descriptive messages
- Stage changes with `git add`
- Use the commit workflow from system instructions

**Pushing: ❌ FORBIDDEN WITHOUT APPROVAL**
- **NEVER** run `git push` without explicit user request
- **NEVER** run `git push origin <branch>` automatically
- User must review commits and decide when to push
- User needs to verify attribution and commit messages (no Co-Authored-By trailer or other
  AI-attribution marker -- see "Documentation and attribution" below; commits should read as
  if the user wrote them)
- Before saying work is "ready to push" (or recommending it), check open Dependabot alerts
  on `main` (`gh api repos/JazzX-LLC/japes/dependabot/alerts -q '.[] | select(.state=="open")'`)
  -- alerts reflect the default branch's dependency graph, not whatever branch is being worked
  on, so they're easy to miss otherwise. Flag anything open, don't just push past it.

**Rationale:**
- User needs to review all commits before they go to remote
- Attribution must be verified
- Commit messages may need adjustment
- User controls when work is shared with team

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

Mechanics that have cost real work here:
- Apply edits one at a time, writing each immediately. A helper that batches five and writes once
  at the end discards all five when the third pattern misses -- and the fixes get reported as done.
- Never `git checkout -- <file>` to undo a temporary change; it destroys uncommitted work in the
  same file. Copy the file aside and copy it back. (`git checkout <rev> -- <file>` is a different
  command and is safe: it restores a named commit's version deliberately. The dangerous one is the
  form with no revision, which silently takes HEAD. Both were used in one session and only the
  first cost anything -- twice.)
- Read (or check for) a file before `Write`. Assuming a module is new has clobbered an existing one.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

**The exception, and it is the one that has cost the most.** When the change answers a review
finding that names a family -- one call site of thirteen, one of four `applies_to` lists, one of two
sibling docstrings -- the family is the unit of the fix, not the site the finding happened to cite.
"Surgical" then means every member, or an explicit note of which ones you are leaving and why (§8).
Read instead as "change only what was reported", this section licenses exactly the one-site edit §8
forbids, and it wins, because the reported site is concrete and the family is not yet enumerated.
Five consecutive review rounds went that way: each fix was locally correct, and what broke every
time was the invariant across them.

## 4. Goal-Driven Execution

**A test is not evidence until two things are true: it fails against the old code, and its stubs
behave the way production does.** The second is the one that slips. A stub that raises where the
real client returns `None` exercises a branch production can never reach -- green test, live bug.
If a test passes on the first run against code you believe is broken, the test is wrong.

**On the second review finding against code you just wrote, simplify it rather than add a case.**
Four rounds went into one test guard, each version defeated by a shape the last had not considered;
the honest version was one assertion on the thing that had actually broken. And do not state a
*because* you have not measured -- an argument from "ruff would wrap this line" turned out to be
false by 5 characters.

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Documentation and attribution

Every rule here is checkable against a diff, and the review is expected to check them.

- **No em-dashes.** Not in code, comments, docstrings, commit messages, the CHANGELOG, docs or
  chat. Recast the sentence, or use a comma, colon, full stop, parentheses or ` -- `. A blind
  sweep picks the wrong punctuation, so `scripts/local/dedash.py` takes a hand-written mapping
  and reports whatever it did not cover.
- **Every new file's docstring carries `Author: Virendra Mehta <virendra.mehta@jazzx.ai>`.**
  Verified by `scripts/local/check_attribution.py`.
- **No AI attribution anywhere, ever.** No `Co-Authored-By` trailer, no "generated by", no model
  name in a comment, a commit, a docstring or a file header. Nothing in the repository should
  suggest how the code was written.
- **Never bump a version without being asked.** Not patch, not minor, not major. This is the
  standing rule and it overrides anything in this file that reads otherwise: work folds into the
  version already in progress, and cutting a new one is a decision the user makes out loud.
- **Comments state what is true now.** No archaeology: do not describe what the old code did, do
  not say "this replaced X", and do not survey a function's callers in its docstring. The reason a
  rule exists is worth one clause; the story of how it got there belongs in git and the CHANGELOG.
- **Commit messages are the headline and nothing else.** Detail goes in the CHANGELOG, which may
  be as expansive as it needs to be.
- **Never name a gitignored file in a commit message or a code comment.** `plan_*.md`,
  `done_*.md`, `docs/status/CHANGELOG.md` and this file are all gitignored, so a reference to one
  is a dangling pointer for everybody but the author.
- **No magic numbers.** Page sizes, timeouts, retry counts, size caps and thresholds come from
  config or a named constant that says what it is, never a bare literal at the use site.
- CHANGELOG, README, and ARCHITECTURE md files should be regularly updated.

## 6. Dependency version specs
- Use `>=` floors, never `^` or upper caps -- don't lock us into a version ceiling. e.g.
`openai-agents = ">=0.17.0"`, not `^0.17.0`. (To pick up a newer release, update the installed/locked
version, not the spec.) Other JazzX repos may use `^`; in our repos prefer `>=`.

## 7. Closing a review finding: TODO slugs

The adversarial review keys every finding `path :: slug`. **Use that same slug in the `TODO(...)`
that closes it**, so the deferral names the finding rather than leaving the reviewer to infer the
connection: a finding keyed `checklist_ci.yaml :: orphaned-wrap-fragments` is answered by
`TODO(orphaned-wrap-fragments): <why, and what would change it>` in that file.

**This works in YAML.** A `# TODO(slug)` comment in pack data is read and honoured exactly as one
in Python is -- `TODO(conductor-pipeline-from-yaml)` in `ci-spread-core/pack_manifest.yaml` has been
picked up under `CHECKED:` and not re-reported. Findings in pack YAML repeat because nobody wrote
a TODO, not because the file cannot hold one.

**Never use a structured field for this.** `notes:` was tried on two rules in `conventions.yaml`
and pydantic dropped both -- `Rule` takes the default `extra="ignore"`, so the keys read like model
fields while being invisible to every consumer. `Threshold` fails the other way, with
`extra="forbid"`, where an undeclared key is a hard error. A comment has neither failure mode.

Two closures, and they mean different things:
- `TODO(slug)` in the file -- deferred, still intended, with the reason. The default for pack data,
  because it sits at the row a future author edits.
- `.reviews/accepted.md` -- weighed and being lived with, no intent to fix. For findings with
  nothing to fix, like an extraction artifact in a vendored corpus nobody will re-run. A `high`
  never belongs there.

Both are claims about blast radius, and the reviewer checks them. A TODO whose claim has stopped
holding is raised again, correctly -- so when a fix makes one stale, update it in the same pass.

## 8. Symmetry & cross-cutting consistency

**Enumerate the family before editing, not after.** Grep for the pattern, list every hit, and fix
all of them in that change or say which you are leaving and why. "Check the siblings afterwards"
has been the rule here for months and still failed six times in one session -- gating one route and
not its twin, adding a guard to two of three functions, converting one call site of five. Every
instance was found by review a round later, after the work was reported done. An enumeration in the
message is the only version of this that holds.
- Japes is v2; the services built on it (juno, kernel, assistant, knowledge-hub) are still v1-shaped.
That gap is real leverage, not just cleanup debt -- japes can absorb patterns those services already
proved out and make them the consistent default, rather than leaving each service to re-derive its
own version.
- When a fix or feature touches one client/module, ask "does this same gap exist in the sibling(s)?"
before calling the work done. Precedent: adding `request_headers_provider` to `KernelClient` because
`KnowledgeHubClient` already had it. The same question applies to any other family that shares a
shape -- e.g. `fabric.db` vs `fabric.blob`, other client wrappers, conductor entry points.
- Check the full family, not just the nearest sibling. If three modules share a pattern and only one
got the fix, the other two are latent bugs until proven otherwise -- not intentional differences.
- When a cross-repo survey (kernel/assistant/knowledge-hub/juno/macer) surfaces a gap, generalize it
into japes properly rather than patching only the one reported instance.
- Prefer the more architecturally consistent shape over the fastest patch, given japes's exposure
(number of existing external consumers depending on current behavior) is still comparatively small --
this is the window to fix a leaning wall, not wallpaper over it.

## 9. Checking your own fix before you commit it

Most of what review finds in a fix is in lines the fix itself wrote, in three shapes. All three are
checkable from the fix's own diff in under a minute, and none of them is a judgement call -- each is
a command you either ran or did not.

**The prose your fix adds is a claim, not a description of it.** List what you just wrote --
`git diff -U0 | grep '^+' | grep -E '#|"""|description:'` -- and for each line name what would
falsify it, then check that. "All four `applies_to` lists" → count them. "is the only one in this
playbook" → grep the playbook. "validates the name separately and loudly" → find the construction
site. This one fails reliably when skipped, for a specific reason: the sentence was written from the
intent, so re-reading it confirms the intent. It is falsifiable only against the code. Five of the
last sixteen review findings were sentences a fix had just added, each wider than what the fix did.

**Look for the rule before writing one.** Before adding a predicate, a parse or a lookup inside a
fix, grep the module -- and the module it imports from -- for the one that already exists. `env_text`
was re-implemented as `os.getenv` plus two `.strip()` calls twice, in the same file as `env_text`,
with the docstring citing it by name as the reason the rule exists. In tests this is absolute: never
assert a literal that the code derives from a named source. `assert code == 6`, where the sibling
test reads `rule.job_exit`, is how a contract goes stale with the whole suite green.

**A behavior change is a change to whatever declares that behavior.** Before committing one, ask
what owns it -- a contract object, a table, an enum, a rendered doc -- and grep for the old value.
`plato/__main__.py:20` already states this for boot policy ("A change to the policy is a change to
`BOOT_CONTRACT`") and it was missed anyway: `run_role` began exiting 6, the contract row still said
`SERVES`, `docs/DEPLOYMENT_ENV.md` rendered from that stale row, and every test compared the
artifacts to each other rather than to observed behavior -- so all three agreed, all three were
wrong, and CI could not see it. When the tests derive from the artifact under test, nothing detects
drift between the artifact and the code; at least one assertion has to come from running the thing.

Run all three against the fix's delta, not the branch. The delta is small by construction -- the
review loop's rounds are 120 to 500 lines -- and every instance above was a `BLOCK` one round later,
at the cost of a full fix cycle.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

