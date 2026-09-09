# Claude Session Status

**Last Updated**: 2026-09-08

## Working Principles

**Critical: Use Professional Judgment**
- Do NOT blindly accept every user suggestion
- Push back when you see better alternatives or tradeoffs
- Explain architectural concerns, performance implications, security issues
- Present alternatives: "Your proposal has X benefit, but Y tradeoff. Consider Z instead?"
- The user WANTS critical thinking, not agreement
- If uncertain, present options with pros/cons and let user decide

## Sibling Repos (local checkouts)

Every JazzX repo is checked out at `/Users/sangit/src/<name>` — look there before reaching for the
GitHub API. `./scripts/local/sister_repo_activity.sh` surveys recent commits across them; per-repo
roles and the traps worth knowing (`assistant` vs `jazzx-assistant` are different repos) live in
memory rather than here, where the list only went stale.

## Related repos
- **jaci** (`/Users/sangit/src/jaci`) — the primary real consumer validating this version.
  Its `dev` venv has japes editable-installed against this checkout (`pip show japes` →
  `Editable project location: /Users/sangit/src/japes`), so it's always running live
  against whatever's in the working tree here, regardless of jaci's own git-pin/lockfile
  state (which is separately known-stale — see jaci's own CLAUDE.md).

## Notes
- Always update CLAUDE.md after significant discoveries or decisions
- This file is gitignored (see .gitignore:67) - local session tracking only
- Purpose: Maintain context across Claude sessions after accidental quits
- Keep this section current, not an append-only log — replace stale status rather than
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
repository** — so these files never enter japes' history (satisfying the "do not commit planning
documents" rule above) but are still version-controlled where they live. Treat them as tracked
files, not scratch.

**The lifecycle is a move, not a rewrite.** A file lands in `plans/` while it is live, and moves to
`status/` once it is done, stale, or superseded — renamed with the prefix that says which:
`done_*`, `superseded_*`, `stale_*`. Nothing is deleted, and nothing live sits in `status/`.

```
docs/plans/plan_<topic>.md          live: being written, argued, or built against
        └─► docs/status/done_<topic>.md        built and shipped
            docs/status/superseded_<topic>.md  a later plan replaced it
            docs/status/stale_<topic>.md       overtaken by events, not replaced
```

**Move with `git mv`, from the `.scratch` repo root** — a plain `mv` plus an untracked add loses the
rename, and the rename is the record of what happened to that plan:

```
git -C /Users/sangit/src/.scratch mv sang/ape/plans/plan_<topic>.md \
                                     sang/ape/status/done_<topic>.md
```

Naming: `plan_*` for a plan, `design_note_*` or `note_*` for an assessment that decides nothing.

**Read `status/` before writing a new plan.** It holds finished and superseded designs, which is
exactly where a new plan's prior art is — and a plan written without it duplicates work and
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
  AI-attribution marker — see "Documentation and attribution" below; commits should read as
  if the user wrote them)
- Before saying work is "ready to push" (or recommending it), check open Dependabot alerts
  on `main` (`gh api repos/JazzX-LLC/japes/dependabot/alerts -q '.[] | select(.state=="open")'`)
  — alerts reflect the default branch's dependency graph, not whatever branch is being worked
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
- Never `git checkout <file>` to undo a temporary change; it destroys uncommitted work in the same
  file. Copy the file aside and copy it back.
- Read (or check for) a file before `Write`. Assuming a module is new has clobbered an existing one.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

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
- Code should not look like it came from AI, including any comments or commits that say Co-authored
by Claude Sonnet etc
- CHANGELOG, README, and ARCHITECTURE md files should be regularly updated
- If signitificant changes, the bump up at least patch version. For major version update, enquire

## 6. Dependency version specs
- Use `>=` floors, never `^` or upper caps — don't lock us into a version ceiling. e.g.
`openai-agents = ">=0.17.0"`, not `^0.17.0`. (To pick up a newer release, update the installed/locked
version, not the spec.) Other JazzX repos may use `^`; in our repos prefer `>=`.

## 7. Symmetry & cross-cutting consistency

**Enumerate the family before editing, not after.** Grep for the pattern, list every hit, and fix
all of them in that change or say which you are leaving and why. "Check the siblings afterwards"
has been the rule here for months and still failed six times in one session -- gating one route and
not its twin, adding a guard to two of three functions, converting one call site of five. Every
instance was found by review a round later, after the work was reported done. An enumeration in the
message is the only version of this that holds.
- Japes is v2; the services built on it (juno, kernel, assistant, knowledge-hub) are still v1-shaped.
That gap is real leverage, not just cleanup debt — japes can absorb patterns those services already
proved out and make them the consistent default, rather than leaving each service to re-derive its
own version.
- When a fix or feature touches one client/module, ask "does this same gap exist in the sibling(s)?"
before calling the work done. Precedent: adding `request_headers_provider` to `KernelClient` because
`KnowledgeHubClient` already had it. The same question applies to any other family that shares a
shape — e.g. `fabric.db` vs `fabric.blob`, other client wrappers, conductor entry points.
- Check the full family, not just the nearest sibling. If three modules share a pattern and only one
got the fix, the other two are latent bugs until proven otherwise — not intentional differences.
- When a cross-repo survey (kernel/assistant/knowledge-hub/juno/macer) surfaces a gap, generalize it
into japes properly rather than patching only the one reported instance.
- Prefer the more architecturally consistent shape over the fastest patch, given japes's exposure
(number of existing external consumers depending on current behavior) is still comparatively small —
this is the window to fix a leaning wall, not wallpaper over it.
---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

