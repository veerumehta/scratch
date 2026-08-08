# Claude Session Status

**Last Updated**: 2026-08-07

## Working Principles

**Critical: Use Professional Judgment**
- Do NOT blindly accept every user suggestion
- Push back when you see better alternatives or tradeoffs
- Explain architectural concerns, performance implications, security issues
- Present alternatives: "Your proposal has X benefit, but Y tradeoff. Consider Z instead?"
- The user WANTS critical thinking, not agreement
- If uncertain, present options with pros/cons and let user decide

## Current Session Context

### Version Status: 2.3.4 (per `_version.py`); Phase 4 chassis work uncommitted on top
- **jazzx_sdk/_version.py**: single source of truth (`__version__`); `pyproject.toml`'s
  `version` must match — enforced by `tests/test_version_sync.py`. Currently `2.3.4`.
- **AdjudicationAgent chassis (Phase 4 of `docs/plans/reasoner-chassis-analysis.md`) — built,
  uncommitted.** New package `jazzx_sdk/agents/adjudication/` (`workspace.py` P4
  `EvidenceWorkspace`/`Mount`; `partition.py` P8 DETERMINISTIC/LIVE `Rule` split;
  `spec.py` `AdjudicationAgentSpec`; `pipeline.py` `run_segment` — P1 replication + P2 collapse
  over batched LIVE obligations; `agent.py` `AdjudicationAgent` facade). Closed one real P8 gap
  along the way: added `NaturalLanguageCondition`/`NaturalLanguageEvaluator` to
  `fabric.canonical.policy`/`condition_evaluator` (the `Condition` union had no LLM-backed kind).
  Added `name_patterns` to `observability.mlflow_bridge.span_to_trace_step`/
  `spans_to_canonical_trace` — its existing `mode_map` is keyed on span_type (`LLM`/`TOOL`/...),
  too coarse to tell an adjudicate call from an emit call apart (both are plain `LLM` spans);
  `agents/adjudication/tracing.py` supplies the chassis's own name-pattern list.
  `examples/adjudication_demo/` ships as the toy pack.
- **Phase 6 (P3/P7) also built, same session, uncommitted.** Reordering decision: benchmarking
  (Phase 0) and MACER-parity shadow-running (Phase 5) deferred to the end — MACER may never adopt
  this chassis, but the primitives are worth building for japes's other consumers regardless.
  `run_segment` now honors `Rule.applicability` (a real gap found this session — it didn't before);
  new `agents/adjudication/planner.py` (`SegmentPlanner`/`plan_or_fallback`, P7's fail-closed
  dynamic-segmentation seam) and `impact.py` (`impacted_rules`/`merge_with_carry_forward`/
  `RunMode`/`resolve_run_mode`, P3 keyed off `evidence_contract()` rather than MACER's document-
  triple join). Both wired into `AdjudicationAgent.adjudicate` as optional params
  (`planner`/`changed_fields`/`prior_outcomes`) — omitting all three is unchanged from Phase 4.
  Full suite green (2513 passed, 3 skipped). Phase 0/5 (benchmarking + MACER-parity validation)
  still not started — everything above is verified against toy/mocked evidence only. See
  `docs/plans/reasoner-chassis-analysis.md`'s 2026-08-07 "Phase 4 shipped"/"Reordering decision"/
  "Phase 6 shipped" notes for the full breakdown.
- **Three corrections landed 2026-08-08, from an independent completeness audit**
  (`design_note_mode_chassis_completeness.md`, `plan_JACI_CL_SPREAD_ADJUDICATION.md` in jaci —
  both verified against code before acting). (1) `replicas` default fixed `3` → `1` in
  `spec.py`/`pipeline.py`/`conductor/replication.py` — the shipped default contradicted
  `design_note_p1_p2_sizing.md`'s own measurement (zero variance reduction at 3.1x cost). (2)
  `ConditionEvaluator.stochastic` documented as currently redundant with `execution == LIVE`
  (verified true across all four registered evaluators) rather than wired into
  `partition_rules` — no evaluator yet needs the distinction, wiring it now would be an untested
  seam. (3) `modes/catalog.py`'s five AML literals (`canonical_produces`/`canonical_consumes`/
  `derived_object` on investigator/conductor/narrator) nulled per
  `domain-neutrality-and-config.md`'s fix #1 — verified nothing in `jazzx_sdk/` reads them first;
  `test_operational_modes.py` updated. Full suite still green (2513 passed, 3 skipped).
- **`EvaluatorMode` migrated onto `ReasoningAgent`, same audit, 2026-08-08.** The one EVOLVE-layer
  mode left out of the v2.3.0 five-mode migration: previously held its own `AsyncOpenAI` client
  (an Anthropic-only deployment couldn't run it at all) and parsed a bare `json.loads` with no
  retry — a truncated/malformed response either raised or silently yielded an empty
  `improvement_signals` list, stopping the compounding loop with no error anywhere. Now inherits
  `BaseMode`, constructor takes `ctx: HandlerContext` (matching the other five), `run()` returns
  `ModeResult` (was bare `EvaluationReport`) — verified zero real callers depended on the old
  shape (only docstring mentions + re-exports anywhere in japes). Caught a real, previously-latent
  bug along the way: a dict-typed field on any `output_type` pydantic model (typed or bare) breaks
  OpenAI's strict-schema mode outright (`additionalProperties should not be set`) — confirmed this
  would *also* break `NarratorMode`'s `NarrativeOutput.sections: dict[str, str]` in a real call;
  fixed only for the new `_EvaluatorLlmOutput` model via `AgentOutputSchema(...,
  strict_json_schema=False)`, scoped to this one call site. 8 new tests
  (`tests/test_evaluator_mode.py`), including a boundary contract test for the strict-schema bug
  (mocked-`ReasoningAgent` tests alone would never have caught it — none of them construct the
  real `AgentOutputSchema`).
- **`NarratorMode` got the same strict-schema fix, 2026-08-08.** `NarrativeOutput`'s
  `sections`/`citations`/`metadata` are all dict-typed — same `output_type=` fix
  (`AgentOutputSchema(NarrativeOutput, strict_json_schema=False)`), same blind spot in its
  existing test file (`test_narrator_mode_reasoning_agent.py` mocks at the `Runner.run()` level
  via the `runner=` test seam, so none of its tests ever reached the real
  `get_output_schema()`/`AgentOutputSchema` construction either) — added the same boundary
  contract test there.
- **`VerifierMode` got the same fix, 2026-08-08** — `VerifierReport`'s `evidence_results`/`notes`/
  `attestations` are all dict-typed, identical `AgentOutputSchema(..., strict_json_schema=False)`
  treatment, same test blind spot, same added contract test. Also cleaned up (while in the same
  method): the empty-evidence early return built `VerifierReport(evidence_id=..., status=...,
  quality_score=..., findings=..., flags=..., attestation=...)` — none of those are real
  `VerifierReport` fields; pydantic v2 silently ignores unknown kwargs by default (verified
  empirically — no crash), so this was always producing the same bare-defaults object a plain
  `VerifierReport()` would, just via misleading dead code. Not a behavior change, a clarity one.
  `GovernorMode`/`GovernorDecision` and `InvestigatorMode`/`HypothesisUpdate` remain clean
  (list/bool/str only, confirmed); `ReasonerMode`'s `output_schema` is pack-supplied, not an SDK
  schema, so not japes's to fix. Full suite green (2523 passed, 3 skipped).

Design docs (gitignored, `docs/plans/`): `reasoner-chassis-analysis.md` (P1/P2/P6/P8 build
sequence + Phase 4 chassis), `policy-ir-abstraction.md` (P8 detail),
`design_note_reasoning_substrate.md`.

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

