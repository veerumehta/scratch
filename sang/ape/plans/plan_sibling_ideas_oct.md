# Plan: ideas from the October sibling survey, built on v2.6.2

Status: approved by the user (relayed by the cross-repo session); built back to back on `v2.6.2`,
one review at the end after a full suite run. Source repos are never named in code, comments or
commits; each item below cites its source only here, verified against the checkouts on 2026-10-10.
Read first: `status/done_rule_trials_and_library.md` and `status/design_rule_trials_and_library.md`
(trial, gate, fix, provenance), `status/done_sdk_eval_control_plane.md` (datasets, experiments,
scorers), the chat lifecycle docs (`status/done_chat_*`), `plans/plan_case_rerun.md`.

Rule for every item: port the idea, not the code; improve on it; a test must fail on the old code;
behaviour is declared in the object that owns it (contract, table, docs), not only in prose.

## Source cites (verified)

Paths are relative to each checkout; the survey's cites lacked the `workflows/` segment for the
codec checkout.

| Item | Source |
|---|---|
| silver reference | codec-suite `workflows/proposals/gt-free-calibration.md:7-48` (the executive decision and optimization contract), `workflows/calibrator_agents/silver_scoring.py` (255 lines), `silver_reference.py` (603) |
| extraction proxies | `workflows/data_extractor_agents/evidence.py` (167), `demand_coverage.py` (480), `focused_reads.py` (350); `workflows/proposals/extractor-optimization.md:567-590` (section 10, the ground-truth-free track) |
| run health | `workflows/shared/run_health.py` (473) |
| fix ledger | `workflows/calibrator_agents/fix_ledger.py` (240) |
| lint autofix and review | policy-workbench `origin/dev`: `backend/app/services/audit_autofix.py` (713), `slop_cleanup.py` (488), `cross_policy_audit.py` (693), `audit_comments.py` (182), `jtbd_audit_cache.py` (146) |
| guideline versioning | policy-workbench `origin/dev`: `guideline_governance.py` (486), `guideline_versioning.py` (1422) |
| judge cache and spend cap | macer `origin/feat/standalone-loan-scorer`: `evals/loan_scorer/src/loan_scorer/{comparison,cli,adapter}.py` |
| chat runtime | jazzx-assistant `origin/dev`: `src/jazzx_assistant/core/progress/relay.py`, `core/progress/status.py`, `schemas/status_vocabulary.py`, `ingress/ws/session/grounding.py`, `ingress/ws/turn/title.py`, `ingress/auth/identity.py`, `core/engine.py` |
| eval retirement | eval-service `app/evals/comparison.py` and the rest of `app/evals/` |

## Tier 1: rules and documents

**P1 Silver reference.** A reference built without gold: where two systems agree the case is
`silver_consensus`; where they disagree a blinded judge panel decides (`silver_adjudicated`) or the
case is `unresolved` and excluded. The reference is frozen (digest, version) before any candidate is
generated; train, validation and holdout manifests are fixed with it. Acceptance is
`net_known_gain = fixes - regressions` over known results with zero consensus regressions.
Improvement: keyed by (dataset case, rule) so it serves rule trials (the two systems are the published
pack and a candidate overlay, or two model runs), not only a single-metric status. Lands in
`jazzx_sdk/evaluation/silver.py`, dataset manifests, pass bars on experiments, and the trial view
(`gold` source shows `silver`). No real gold is read; the reference records its provenance per case.

**P2 Baseline-pinned acceptance.** A rule proposal or repair is accepted only with zero new failures
over a pinned baseline (a frozen trial result), and a repair carries a test that fails before and
passes after. Lands in the merge gate (`trial_ref` gains `baseline`, `new_failures`) and the R5 fix
(`fix_proposal` refuses a repair with no failing-before case and records the case). Setting stays
`PLATO_REQUIRE_TRIAL`; the pass bar is part of the trial ref, not a second setting.

**P3 Extraction proxies.** (a) Quote verification: the quote is on the cited page, and supports the
value (normalised comparison of the value with the quote's tokens, units and sign), closing
`TODO(quote-not-checked-against-value)`. (b) Demand coverage: of the fields the pack's rules read, how
many extraction filled, with a reason code on every demanded null (`not_in_documents`, `ambiguous`,
`truncated`, `low_confidence`, `belongs_to_other_class`). (c) Focused reads: one cheap call per
document to fill demanded gaps, disagreements with the first read recorded, never overwritten.
Improvement: demand is derived from `rule_reads` and the evidence contracts, not a hand table.

**P4 Run health, generic.** `jazzx_sdk/util/run_health.py` already has extraction-run signals. Lift it
to a layer: `HealthSignal(level CRITICAL|WARN|INFO, code, detail, evidence)`, stage-end derivations
(zero model calls, budget starvation), and a final gate `PASS | PASS_WITH_WARNINGS | RETRYABLE | FAIL`
where CRITICAL fails the run. Apply to case runs and experiments (a run reports health beside status).

**P5 Lint autofix and review.** Pure, guarded fixers: written only if the file still parses, nothing
outside the fixer's allowed fields changed, and re-lint shows fewer findings of that rule and no more of
any other. Findings become anchored review comments (anchor, not array index); a content-hash memo so
unchanged policies are not re-linted; a readiness score gating "send for review", separate from
advisory findings; duplicate findings folded; per-rule retire and false-positive filters; triage
decisions carried forward by anchor.

**P6 Judge cache and spend cap.** SHA-256 judge cache (a replay makes no call), a reservation-based
`max_cost` ceiling that stops before a call it cannot afford, and many-to-many matching with `missed`
and `unrequested` buckets. Lands under `evaluation/` beside `LLMJudgeScorer` and the adjudication
scorers; the cache is a store (db table via the fabric store pattern), keyed by judge prompt digest,
model and inputs.

**P7 Guideline versioning.** Policy and guideline source documents become versioned, content-digested
artifacts per tenant (`GuidelineStore`: id, version, digest, blob pointer, parent, created_by).
Extraction runs, proposals and published pack versions record the guideline version and digest they came
from; a pack can pin "certified against guideline vN". Diffing two versions yields changed sections;
re-extraction runs only on those (reusing the segmenter and the case-rerun document focus). Rollback of
a version is refused while a live pack depends on it. Shown on the packs and ontology pages. New table
and migration; no data migration (existing runs record no guideline).

## Tier 2: chat runtime (for the jazzx-assistant upgrade; they pin 2.5.7)

Streaming rewriter across chunk boundaries (display names in streamed reasoning and text); a status
event with activity lanes and a vocabulary; session-shared single-flight grounding; conversation
titles (`TurnStore.set_title`); a public raw security-context decode (non-UUID subjects stay as given,
not `None`); a public typed `ChatStageError`; a per-turn persona-suffix hook; spans recording why
feedback guidance was or was not applied; approved-only and entity-scoped static feedback in the eval
client; `assert_models_priced` in `llm.cost`; an optional compact activity summary on the final result.
Socket.IO bidirectional route last, optional. Each lands in the existing chat lifecycle and has an
adoption note line.

## Tier 3: eval-service retirement

McNemar exact test and comparison export (ZIP/CSV); an agent judge (tool allow-list, `max_steps`)
with `call_scorer` / `judge_with_rubric`; GEPA and MetaPrompt optimiser backends (target score,
no-improvement stop) and synthetic cases from approved feedback; calibration-loop memory (a fix ledger:
attempted fixes with outcomes, planner expected against actual lift, prompt writes refused when they
drop front matter or headers); a classification-match scorer; CSV dataset import/export and
best-effort MLflow sync; clone-exclusion rules; process-run comparison (path diff and align, boundary
events, step timing, definition diff); webhooks; a backstop deadline worker; a parity audit for
cutover; sanitised scorer failures. Later or optional: background compare jobs with history, the judge
scorecard, byte-exact prompt snapshot tests.

## Order and gates

P1, P2, P3, P4, P5, P6, P7, then tier 2, then tier 3. Within a tier the order above. Each phase: build,
test (fails on old code), CHANGELOG entry with line counts, commit on `v2.6.2`. One full suite run, then
one review over the range at the end; findings fixed on `v2.6.2`; then the local `plato` squash and a
push script (the user runs it).

## Decisions only the user can make (asked when reached, not before)

- P7: whether rollback of a guideline version is refused or only warned when a *draft* (not a live
  pack) depends on it (proposed: refuse for live, warn for draft).
- Tier 3 webhooks: which events and where they may post (outbound network; deployed posture refuses
  without an allow-list).
- Tier 2 Socket.IO route: whether to build it at all.
- Any model spend (judge panels, focused reads against real documents): a ceiling from the user.
