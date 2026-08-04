# Claude Session Status

**Last Updated**: 2026-08-02

## Working Principles

**Critical: Use Professional Judgment**
- Do NOT blindly accept every user suggestion
- Push back when you see better alternatives or tradeoffs
- Explain architectural concerns, performance implications, security issues
- Present alternatives: "Your proposal has X benefit, but Y tradeoff. Consider Z instead?"
- The user WANTS critical thinking, not agreement
- If uncertain, present options with pros/cons and let user decide

## Current Session Context

### Version Status: 2.3.0 pushed; 2.3.1 in progress (local, unpushed)
- **jazzx_sdk/_version.py**: single source of truth (`__version__`); `pyproject.toml`'s
  `version` must match — enforced by `tests/test_version_sync.py`.
- **v2.3.0 is pushed** — `dev` and `origin/dev` both at `2e997b9`. No longer amendable;
  anything new is a fresh commit. (The commit went through several rounds of `--amend`
  locally before pushing — the SDK-layout refactor got folded in during one of them, per
  the entry below — so its final pushed SHA doesn't match earlier SHAs referenced in this
  file's own history; that's expected, not a discrepancy to chase.)
- **v2.3.1** (local, unpushed) — `docs/plans/REFACTOR-2.4-subpackage-interiors.md` Phases 6, 7,
  and 11, landed as a patch not a minor bump. Phase 6 (`e1207da`): closed the `llm`/
  `agents.interactive`/`tools`/`fabric.canonical` facades, made `DbCostRecordStore`+providers
  lazy, status-marked five staged-capability surfaces, deleted `tools/kg_store.py` (a 1.6.7-era
  shim). The plan's two open judgment calls got settled first (`a765e90`) with real caller
  evidence, not guessed: `conversion.convert_document` is the canonical local-document-read
  entry point (`read_local_file` has zero real callers, `convert_document` has 2 japes + 7 jaci);
  `ratio_evaluator.py` stays in `tools/` whole, not split into `fabric/` — it has zero
  `fabric.canonical` imports, unlike `assessment.py`. Phase 7 (`f1623a9`): `fabric/canonical/
  store.py` (1,596 LOC, 13 copy-pasted CRUD classes) split into a `store/` package around one
  generic `_EntityStore`; verified identical KH call shapes for all 13 types via a recording
  fake client. Phase 11 (`29f6a9a`, `0104f6a`): evicted `financial.py`/`filings.py`/
  `assessment.py` out of `tools/` into `finance/`/`fabric/`, then regrouped the rest of `tools/`
  (24 flat modules) into `documents/`/`knowledge_hub/`/`platform/`/`agent/` subpackages,
  splitting the old flat `documents.py` three ways in the process. See `docs/status/
  CHANGELOG.md`'s `[2.3.1]` entry for the full list. Skipped: `base_registry.py`'s eviction (the
  plan's weakest-justified move, no unambiguous target) and the `providers/{base,stub}.py`
  further nesting under `documents/` (real risk for small discoverability benefit) — both
  deliberate, not oversights. Phases 8–10 and 12 (docs) of that plan are not started.
  jaci needed real fixes at every phase (submodule pins on moved modules) since it runs on a
  live path install of this working tree — all landed on jaci's own `dev` immediately.

### What v2.3.0 actually is
One arc: generalize the execution mechanism (`ReasoningAgent`, provider-portable —
OpenAI and Anthropic through the same call shape), then build the next chassis
generation on top of it, then close every real gap jaci's live validation surfaced.

- `jazzx_sdk.agents.reasoning.ReasoningAgent` — floor+ceiling reasoning primitive over
  `AgentExecutionService`/`run_kit`. All five operational modes (Reasoner/Investigator/
  Governor/Verifier/Narrator) now call it; `AgentExecutionService.run()`'s own no-tools
  retry path was fixed to match. Returns real `TokenUsage` (fresh input/output + cached/
  reasoning breakdown) as a 3rd return value — `ModeResult.tokens_used`/`.token_usage`
  are now populated for real (were dead — always 0/None — since the migration itself,
  found only via a live jaci run, not any mock).
- P8 (`fabric.canonical.condition_evaluator`) — `Rule.condition`/`.applicability` open onto
  a registered `ConditionEvaluator` union (`Expression`/`DslExpression`/`RatioCondition`).
- P1/P2 (`jazzx_sdk.conductor`) — `run_replicated_segments` + `EnsembleCollapse`: segment ×
  replica × regroup topology over `fan_out`, failed replicas excluded from the vote.
- P6 (`jazzx_sdk.agents.reasoning.grounding`) — `PrecomputedGrounding` + `BrowseGate`:
  heading-scoped snippet extraction, keyword prefilter, headings-only LLM selector,
  fingerprint-keyed cache, deny-only browse gate over `authority.context`.
- `InvestigatorMode` now takes a required `hypothesis_content_type` constructor arg —
  the bare `THypothesisContent` TypeVar it used to parameterize `HypothesisUpdate[...]`
  with produces a `content` field schema with no `"type"` key, silently accepted by a
  mocked runner but rejected outright by OpenAI's strict structured-outputs validation.
  Found via a real jaci gold-case run, not any existing test. All jaci callers updated.

Design docs (gitignored, `docs/plans/`): `reasoner-chassis-analysis.md` (P1/P2/P6/P8 build
sequence), `policy-ir-abstraction.md` (P8 detail), `design_note_reasoning_substrate.md`.

### Related repos
- **jaci** (`/Users/sangit/src/jaci`) — the primary real consumer validating this version.
  Its `dev` venv has japes editable-installed against this checkout (`pip show japes` →
  `Editable project location: /Users/sangit/src/japes`), so it's always running live
  against whatever's in the working tree here, regardless of jaci's own git-pin/lockfile
  state (which is separately known-stale — see jaci's own CLAUDE.md).

### sdk-layout refactor — folded into the v2.3.0 commit
Module-reorganization only, no behavior/API change — per `docs/plans/REFACTOR-2.3-sdk-layout.md`
(gitignored). Built and verified on `refactor/sdk-layout-2.3` first (branched from `dev`@`33f1605`)
deliberately, not applied to `dev` directly: macer/jaci/juno run live `.pth` path installs against
this working tree, so a direct `dev` edit would have hit them immediately with no version-bump
gate. All 5 phases done and verified independently (full suite green throughout, `-X importtime`
diffed against a Phase-0 baseline after every phase — confirms no new eager dependency, and that
`mlflow` actually *left* the eager path — import-boundary suite green, a live `create_app()` smoke
test against `/health`/`/invoke`/`/stream`). `git merge --squash` + `git commit --amend`'d into the
same `dev` commit as the rest of v2.3.0 — deliberately, since a minor bump is exactly the point
at which a layout change like this is acceptable to make. That commit is now pushed (see Version
Status above); the refactor branch itself was fully folded and has since been deleted. Two
jaci-side one-line fixes (settings_fields.py, demo_page.py) landed immediately on jaci's own
`dev`, since jaci's live path install saw the new layout right away rather than waiting for a
japes push. Of the other external consumers: macer and jazzx-assistant are both pinned to specific
refs (not floating), so this doesn't reach them until they bump; juno floats on `main` (not `dev`),
so it's untouched until this promotes there.

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

### Development Workflow

When implementing a new feature:

1. **Analyze** - Create planning docs in `/tmp/` if needed (or docs/plan_*.md which is gitignored)
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

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

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

