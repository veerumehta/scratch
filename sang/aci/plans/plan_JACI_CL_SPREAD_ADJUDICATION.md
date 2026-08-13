# plan_JACI_CL_SPREAD_ADJUDICATION

Repo: `jaci`, branch `dev` (v0.19.1 @ `f56baf9`, 18 commits ahead of origin, unpushed).
Depends on `japes` ≥ 2.3.4 (chassis shipped, uncommitted); Phase 6 additionally wants japes 2.4.0
Phase 2. **Revision 2** — reconciled against `aci/plans/` + `aci/status/` and `ape/plans/`.
Findings: `plans/design_note_mode_chassis_completeness.md` §2.

**Read first:** `plans/PRD_COVERAGE_REGISTER.md` (and its three recorded lessons — any coverage claim
here will be held to them), `plans/CL_SOURCE_RECONCILIATION.md`, `status/status_JACI_CL_MVDP_VP2_WEDGE.md`
(the XF-1/XF-2 acceptance criteria), `status/status_JACI_CL_PRD_COMPLETION.md`, and in japes:
`plans/design_note_p1_p2_sizing.md` (Phase 5 below turns entirely on it),
`jazzx_sdk/agents/adjudication/`, `examples/adjudication_demo/`.

**Where this lands.** The CL track is between waves — `PRD_COVERAGE_REGISTER.md:193-197`: *"Wave 1's
planned phases are complete… **Waves 2 through 4 have no plans yet.**"* Attention has moved to
AML/KYC (`[Unreleased]` in the CHANGELOG). Nothing here contradicts a committed plan. Two things it
must coordinate with: `plan_conductor_collapse.md` steps 4-6 (which own `run_spread`'s conductor
collapse and the eval-harness `conductor_factory` — *"one graded execution path"*), and Wave 4b,
which already owns customer-workbook template parsing.

**Conventions.** `aci/CLAUDE.md`: commits allowed, **`git push` forbidden** without explicit request;
"fix the bug" means write the reproducing test first; no abstractions for single-use code; mention
unrelated dead code, don't delete it; no AI attribution in code or commits. Do not name plan files in
source comments (`docs/plans/` is gitignored — `status_JACI_CL_PRD_DEMO_ARC.md:56-62`).

**Framing.** jaci imports neither `jazzx_sdk.agents.reasoning` nor `jazzx_sdk.agents.adjudication`;
"adjudication", "replication", and ensemble collapse have zero hits anywhere in the CL corpus. This
is new territory, not a duplicate track. Phases 0-2 are small and fix live defects; 3-4 are the
adoption; 5 is deliberately a measurement, not a build.

**Do not** route the spread through `ReasonerMode` / `GovernorMode` / `NarratorMode`. Those are
generic over `Context`/`Hypothesis`/`Decision`. The recorded decision rule is
`plan_caller_migration_jaci_k9.md:127-130`: *"investigation shape = hypotheses + evidence attestation
+ iterate-to-convergence. Transactional shape = single-pass input→output(s), no hypotheses, no
loop"* — and it explicitly assigns `ci_spread` to `TransactionContext[LoanApplication, CreditDecision]`.
`AdjudicationAgent`'s own docstring reaches the same conclusion from the other side: mode is not
load-bearing at runtime; what matters is tagging the trace correctly.

---

## Phase 0 — P0 defect: the four arithmetic controls never run

**DONE 2026-08-08.** `control_tolerance: Decimal | None = None` added to `CLSpreadContext`,
threaded through in `credit_validation/provides.py`. 2 new regression tests in
`tests/unit/test_cl_capability.py` (`test_control_tolerance_none_by_default_leaves_
balance_control_dead`, `test_control_tolerance_set_surfaces_balance_control`). Full suite green
(806 passed, 8 skipped, 4 xfailed, 1 xpassed -- the xpass is an unrelated, already-tracked
live-integration flake, not from this change).

**Same day, second pass.** The plumbing alone left every real call site still not exercising the
four controls -- `demo_page.py` built a `CLSpreadContext` without one. Wired
`control_tolerance=Decimal("2")` directly into `demo_page.py`'s construction (matching the PRD's
own documented RB rounding fact, "$1-2 ending-cash rounding in some years" -- a placeholder
grounded in real source text, not an invented number). Still no `PolicyProfile`-sourced default --
no such profile object flows through this pipeline yet, and building that threading mechanism now
would be ahead of any caller who needs it. Register re-scored
(`PRD_COVERAGE_REGISTER.md`'s new "Governed-pipeline wiring gap" section): P0 headline (61%) and
VAL (83%) don't move -- `done (RB)` was already true under the register's own "implemented with
tests" bar; what changed is that the claim no longer has an unstated reachability caveat.

**Files:** `capabilities/commercial_lending/cl_capability.py` (`CLSpreadContext`, `:31-46`),
`capabilities/credit_validation/provides.py:22-36`.

`validate_package()` runs `detect_balance_control` (FR-VAL-1), `detect_cash_flow_tie` (FR-VAL-3),
`detect_equity_rollforward` (FR-VAL-4), `detect_period_continuity` (FR-VAL-5) **only when
`control_tolerance is not None`**. `credit_validation/provides.py:36` never passes one and
`CLSpreadContext` has no field for it. They fire only from tests that call the detectors directly.

The gate was a deliberate design call — `status/done_JACI_CL_VALIDATION_COMPLETION.md:14-16`:
*"`None` by default — off, since tolerance is institution policy, never a module default."* Correct.
Nobody then supplied the policy value. `done_JACI_CL_POLICY_EXPERT.md:191-197` is the most recent doc
to modify that exact call site and never mentions it.

**Do:** add `control_tolerance: Decimal | None = None` to `CLSpreadContext`; source the default from
the pack `PolicyProfile` thresholds under `arithmetic_control_tolerance` (same mechanism the RB test
uses for `ltm_reproduction_tolerance`, so it stays pack data and never a literal); pass it through in
`credit_validation/provides.py`.

**Test first, per CLAUDE.md §4:** `tests/unit/test_cl_capability.py` — an unbalanced-balance-sheet
`SpreadPackage` through `run_cl_spread` must produce the `detect_balance_control` finding. It
currently produces nothing; that assertion is the regression guard.

**Then update the register.** `PRD_COVERAGE_REGISTER.md:67-71` scores FR-VAL-1/3/4/5 as done, several
marked `(RB)`. Re-score honestly and move the 61% P0 headline with it. The register's own second
lesson is the case: *"'the test passes' and 'the PRD claim is met' are different claims."*

**While you're there, note but don't fix:** FR-VAL-2 is recorded partial (cash-flow-statement
subtotals still uncovered), and FR-VAL-9 is absent from the Wave-1 re-audit enumeration with no
explanation.

---

## Phase 1 — P0: replace the last hand-rolled LLM call

**File:** `capabilities/commercial_lending/pipeline.py:24-39, 145-200`

`run_entity_extraction` is the only hand-written LLM prompt left in `src/`: `_ENTITY_PROMPT` /
`_ENTITY_SYSTEM` constants, a raw `LLMManager().run(...)`, a bare `json.loads`. No schema, no
`Refusal`, no confidence, no token accounting.

**Do:** define `_ExtractedEntities` (borrower, facility, collateral, parties, covenants, line items,
dates — mirror what the prose prompt asks for) and route through
`ReasoningAgent(ctx.runtime.agents, model=...).run(name="cl:entities", instructions=_ENTITY_SYSTEM,
query=..., output_type=_ExtractedEntities)`. Return a `Refusal` on unparseable output rather than
raising — jaci already uses `fabric.canonical.refusal` in 16 places. Attach `TokenUsage` to the run.

**Test:** scripted malformed-then-valid retries and succeeds; persistently malformed yields a
`Refusal`.

---

## Phase 2 — `structure_statement` under `ReasoningAgent`

**Files:** japes `jazzx_sdk/finance/structure.py`; jaci `capabilities/commercial_lending/spreader.py:83-137`.

The one LLM call in the spreader that matters — located grid → typed `Statement` — runs through a bare
`llm.run`. A malformed grid or a statement large enough to hit the output cap fails with no repair.

**Do in japes first** (it is an SDK function): add an optional `reasoning: ReasoningAgent | None = None`
to `structure_statement`; when supplied, route through it with `output_type=StructuredStatement`,
keeping the existing `llm` path as default so no caller breaks. Then pass one from `spreader.py`.

**Note for the japes side:** `domain-neutrality-and-config.md:54-63` already flags
`STATEMENT_STRUCTURE_SYSTEM = "You are a credit analyst spreading financial statements..."` as a
runtime-affecting domain leak left as a deliberate judgment call. Don't fix it as a side effect;
don't make it worse.

**Tests:** japes — schema-failure-then-success retry, truncation retry. jaci — the YETI FY2025 fixture
still produces an identical `FinancialSpread` (happy-path regression guard).

---

## Phase 3 — validation as an obligation register

The highest-value phase, and it is close to free: `partition_rules` routes deterministic conditions to
the no-LLM partition at `k=1`, so the 13 deterministic detectors keep behaving exactly as they do.

**New:** `capabilities/commercial_lending/adjudication/` — `__init__.py`, `obligations.py`, `agent.py`,
`adjudication.yaml`, `persona.md`. Model the folder on `japes/examples/adjudication_demo/` exactly.

**3.1 — map the 17 detectors to `Rule` objects.** Partition once, by hand, recording the reasoning.

*DETERMINISTIC* (`Expression` conditions over the `SpreadPackage`/metrics context, no LLM):
`detect_content_free_stubs`, `detect_scale_errors`, `detect_hardcoded_plugs`,
`detect_income_statement_cross_foot`, `detect_balance_control`, `detect_cash_flow_tie`,
`detect_equity_rollforward`, `detect_period_continuity`, `detect_reconciliation_mismatches`,
`detect_staleness`, `detect_precedence_violations`, `detect_cross_period_addbacks`,
`detect_cross_period_addback_inconsistency`.

*LIVE* (`NaturalLanguageCondition`, genuine judgment over evidence): `detect_sign_label_errors`,
`detect_undisclosed_obligations`, `detect_cross_document_contradictions`, and residual
`policy_violations_to_findings` cases.

Each LIVE rule's `reads` must name exactly the context fields it needs. This is load-bearing, not
cosmetic: `impact.py::_rule_fields` derives incremental-rerun impact from `evidence_contract().fields`,
so an under-declared rule is wrongly skipped on a re-run and a rule declaring nothing is treated as
always-impacted (fail open). Get them right at authoring time.

**3.2 — segments.** Per statement (`is` / `bs` / `cf`) plus `cross_statement` for the controls that
span statements. Statement grouping matches how evidence loads, which is what makes the batched call
cheap. Note that `reasoner-chassis-analysis.md` §6 proposes a different CL segmentation — *Financials,
Collateral, Covenants, Guarantors, Exceptions* — which is the right shape for a full credit-memo
adjudicator. Statement-level is the right shape for *spread validation specifically*. Say so in the
spec, so the two don't get conflated later.

**3.3 — collapse.** `DeterministicVote` with the priority ordered by the PRD's six severities
(FR-VAL-10), most severe first — no LLM call, and it reproduces macer's precedence table without
macer's problem of that table living in a prompt string. §6's CL row prescribes exactly
`DeterministicVote` + minority to committee. Wrap in `AnyEscalate` for the severity that must never
be diluted.

**3.4 — spec.** `adjudication.yaml`: `name: cl-spread-adjudicator`, **`replicas: 1`** (see Phase 5 —
do not copy the chassis default), `status_vocabulary` = the six PRD severities, `mounts: [statements,
policy, chart_of_accounts]`, `segments: [is, bs, cf, cross_statement]`. Load via
`AdjudicationAgentSpec.from_dir`.

**3.5 — supply the trace mode map. Not optional.** `reasoner-chassis-analysis.md` §4b: `DEFAULT_SPAN_MODE_MAP`
collapses 13 modes onto 3 by OTel span type, so *"if the chassis doesn't supply a `mode_map`, every
LLM call in its trace is labelled `reasoner` — including the Governor gate and the Narrator pass — and
the Trace lies about what happened."* Use `adjudication_name_patterns` from
`jazzx_sdk/agents/adjudication/tracing.py` and tag each step. For a regulated artifact this is a
correctness requirement, not observability polish.

**3.6 — wire as a step impl.** Register `cl.adjudicate` in `capabilities/credit_validation/provides.py`
and add it to `config/packs/cl_of_core/pipelines.yaml` after `validate`. Run both initially and diff.

**3.7 — equivalence gate.** `tests/unit/test_spread_adjudication.py`: on the RB reference case and
YETI FY2025, the DETERMINISTIC partition must produce a findings set **identical** to today's
`validate_package()` output. That is the entire safety argument. Only then remove `validate`.

**3.8 — `EvidenceWorkspace`.** One per segment over its mounts, so an income-statement rule cannot
reach the loan agreement. Apply `enforce_read_cap` to any document read handed to a LIVE call —
error rather than truncate, the discipline macer proved and jaci lacks.

---

## Phase 4 — real `_reconcile`: jaci already has it

`AdjudicationAgent._reconcile` is a no-op passthrough. jaci's `hitl_approval.py` (maker-checker over
`AuthorityMatrixV2` + `check_action`), `corrections.py` (per-correction override lineage), and
`promotion.py` (affirmation gates) are the real implementation.

**Do:** subclass `AdjudicationAgent` in `adjudication/agent.py`; override `_reconcile` to apply, in
order: carried-forward human affirmations from a prior run; an exclusion pass modelled on macer's
`ExclusionIndex` ("a reviewer rejected this evidence for this finding, so it may not justify that
finding again") implemented as a deterministic post-pass over `RuleOutcome`s **and** as a prompt rule
— the two-layer structure is the point, the prompt layer alone is not a control; then the authority
check deciding auto-resolve vs review queue. Override `_emit` to produce the review-queue-ranked
narrative via `review_ranking.py`.

Keep it in jaci until stable against the RB reference case. This is the input to japes' eventual
`_reconcile` promotion — prototype here, promote there, not the reverse.

---

## Phase 5 — per-cell confidence: measure before you build

**This phase is deliberately a measurement, not a replication build.** Revision 1 of this plan
recommended k=3 replication. That contradicts japes' own `design_note_p1_p2_sizing.md`, which
measured 3 batched replicas agreeing 9/9 — *"zero measured variance reduction, at the full 3.1x cost
multiplier"* — and concluded *"a chassis primitive shouldn't bake in an unmeasured assumption."*

**5.1 — the defect, which is real regardless.** `spread_package.py:46-48` stamps
`_SOURCED_SCORE = 0.98` on every as-reported cell. Against floors `{high: 0.9, medium: 0.7, low: 0.0}`
no cell can fall below any floor — so the wedge's own acceptance criterion **XF-2**
(`status_JACI_CL_MVDP_VP2_WEDGE.md:44`: *"Sub-confidence admission is a Refusal: values below profile
floor refuse admission per cell `cl.eadm.003`… silent low-confidence writes must be zero"*) passes
vacuously and can never fire. Four shipped features rank on that constant: `rank_for_review`, the
governed workbook's cell notes, demo-arc Phase 3's template confidence column, and the Streamlit
confidence-weight slider. No document anywhere acknowledges the value is fixed.

**5.2 — the cheap fix first, before any replication.** Confidence should reflect *how the value was
obtained*, which jaci already knows and discards: `spreader_template_trace()` records the real
`MatchKind` per row (`exact_key` / `alias_key` / `exact_label` / `normalized_label` / `substring` /
`unmatched`). A substring match is not as trustworthy as an exact key match. Derive the score from
`MatchKind` plus whether the value is grounded verbatim in the source text (reuse
`DocumentAgent._grounded`). Deterministic, free, and it makes XF-2 able to fire.

**5.3 — then measure replication, on a spreading fixture.** Run the Phase-0-style comparison japes
never ran on a numeric-extraction workload: `structure_statement` at k=1 vs k=3 over the RB package
and YETI FY2025, comparing cell agreement, tokens, cost, wall-clock. The sizing note's own caveat is
that its measurement covered *"closer to mechanical verification than genuine judgment"* — statement
structuring may behave differently, and that is exactly the open question it names. **Write the
numbers down. Then decide.**

**5.4 — only if 5.3 shows real disagreement.** Wire `reconcile_packages()` — jaci's per-`(statement,
line, period)` voter, built and never invoked outside `test_spread_package.py`, with **zero mentions
anywhere in the planning corpus** — as the collapse step. Adopt macer's two-stage rule explicitly:
value wins on frequency with **provenance excluded from the winner fields**, so a citation can never
buy a value the win; then the displayed row is chosen among value-agreeing replicas *with* provenance
included, and all display fields copy from that one row. Persist `votes_considered` / `votes_excluded`
so a 2-of-3 split is visible — macer's documented weakness is that its split ratio isn't persisted.
Gate on `evaluator.stochastic`, per japes 2.4.0 Phase 1.

---

## Phase 6 — evaluation: row-by-row accuracy

There is **no harness that scores spreading output row-by-row against an analyst spread**. What
exists: a 4-key `_YETI_TRUTH` dict in `demo_page.py:26-32`; a 30-row `_YETI_SEC_ASFILED` table
rendered but never asserted; `test_rb_reference_case.py`, which reproduces the LTM income-statement
column exactly but is a *reconstruction test from six hand-built `SourceStatement`s*, and whose RB
template is *"deliberately not wired into `template.py`'s YETI-shaped render pipeline"*; and
`run_ci_eval.py`, whose `CIExpected` has no spread-accuracy field at all.
`docs/ci_spread/YETI_Spread_Template.csv` is referenced by nothing.

**Do:** (1) move `_YETI_TRUTH` and `_YETI_SEC_ASFILED` out of `demo_page.py` into
`tests/eval/gold_cases/ci/yeti_asfiled.yaml` — ground truth living in a UI module is the root cause
of its never being asserted. (2) Add `SpreadExpected` to `tests/eval/ci_golden_case.py` (expected
values keyed by `(statement, key, period)` + tolerance) and a `spread_accuracy` metric to
`run_ci_eval.py`. (3) Coordinate with `plan_conductor_collapse.md` step 6, which already reserves a
generic `conductor_factory` for *"one graded execution path"* — this metric should land inside it,
not beside it. (4) Only after japes 2.4.0 Phase 2, use `EvaluatorMode` for the qualitative scorecard
the YETI charter asks for; before that migration it can silently return an empty `improvement_signals`
list and make the weekly baseline meaningless.

---

## Order and gates

| Phase | Gate |
|---|---|
| 0 controls | unbalanced-BS fixture produces the finding through `run_cl_spread`; register re-scored |
| 1 entity extraction | malformed output yields a `Refusal` |
| 2 structure_statement | YETI FY2025 spread unchanged; retry test green |
| 3 obligation register | DETERMINISTIC partition byte-identical to `validate_package()` on RB + YETI; trace mode map supplied |
| 4 `_reconcile` | RB case round-trips a human affirmation and an evidence rejection |
| 5.2 confidence | XF-2 can fire: a substring-matched cell falls below the `high` floor |
| 5.3 measurement | k=1 vs k=3 numbers recorded on RB + YETI |
| 6 evaluation | `spread_accuracy` reported for YETI; ground truth out of the UI module |

0, 1, 2 are independent and small. 3 gates 4. 5.2 is independent of everything and should probably go
first — it is a few hours and it un-breaks an acceptance criterion.
