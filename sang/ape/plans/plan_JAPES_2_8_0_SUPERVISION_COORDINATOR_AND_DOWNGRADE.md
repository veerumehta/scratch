# plan_JAPES_2_8_0_SUPERVISION_COORDINATOR_AND_DOWNGRADE - a coordinator that decides what it has earned, and a machine that watches the machine

Repo: `japes`. Consumers to check: `jaci` (`capabilities/commercial_lending/promotion.py` is the code this plan generalizes), `jazzx-assistant`.

Author: Virendra Mehta. Written against `japes` HEAD `3647d21a` (`2.6.4`), anchors read at that commit. Source: Deck 4 section 4 (slides 64 to 75) and slide 84 (what "decides" must mean).

## TLDR

The deck says supervision is three responsibilities: a coordinator (AI or human) that plans, allocates, tracks and decides within its earned cells; a human on the record who makes the protected calls through reason-coded supersession; and system oversight where the Sentinel downgrades automatically and the Evaluator attests but never promotes. The SDK has the authority side of this (cells, the narrowing chain, `downgrades` as a resolver input, `OverrideEvent` with reason codes, `Checkpointer` in the Conductor, receipts on automations) and jaci has a complete, tested supersession path for one object, the spread. Three things are missing: the coordinator's objects (work plan, work item, readiness, escalation ladder) and the maker-checker rule; the wire from a `SentinelResult` to a recorded runtime downgrade on the execution profile; and a generic supersession primitive so every protected decision, not only the spread, gets "the analyst's object is never edited".

## What exists at HEAD

- `authority/resolver.py:35` `resolve_effective_autonomy(cell, binding, overlay, ep, downgrades)`: most-restrictive intersection across cell, surface binding, client overlay, execution profile and runtime downgrades; `contributing_layers` records which layer decided; `human_only` forces L0. `rg -n "runtime_downgrades|downgrades=" jazzx_sdk` outside the resolver and tests returns nothing: no caller passes a downgrade today.
- `modes/operational/sentinel.py:27` `SentinelMetrics`, `:48` `SentinelResult`, `:58` `SentinelMode.run`, `_compute_metrics` (`:186`). Produces metrics; changes nothing.
- `modes/evolve/evaluator.py`; `evaluation/` gold and silver cases, experiments, corrections.
- `conductor/checkpoint.py:26` `Checkpointer`; `conductor/suspension_store.py` durable human checkpoints; `conductor/pipeline.py`, `engine.py`.
- `automation/schemas.py:121` `Receipt` with `idempotency_key`, `ReceiptStatus` (`:115`); `automation/governed.py`.
- `fabric/canonical` `OverrideEvent` with the eight reason codes and `superseding_decision_id` (Schema v1.0 §5).
- `manifest/autonomy.py` five-level ladder, numeric 0 to 4.
- jaci `capabilities/commercial_lending/promotion.py`: `SpreadDecision` (`:43`), `affirm_spread` (`:56`, refuses `HUMAN_ONLY_ACTION`, `AUTHORITY_EXCEEDED`, `PRECONDITION_FAILED`), `PromotionLedger` (`:83`), `promote_spread` (`:97`, idempotent), `SpreadOverrideEvent` (`:139`), `override_spread` (`:152`), `EffectiveUnderwritingSpreadView` (`:168`), `build_effective_view` (`:186`).
- `runs/` carries a `readiness` word in `worker.py` and `chat.py`; verify before P2 whether it means run readiness (it does not mean case readiness).

## Gaps

| # | Gap | Slides |
|---|---|---|
| S1 | No generic supersession: affirm, promote, supersede, effective view exist for the spread in jaci only | 68, 69, 71 |
| S2 | No coordinator objects: work plan, work item with owner and next step, readiness state, escalation ladder; no maker-checker rule | 65, 66, 67, 72 |
| S3 | Sentinel to downgrade is not wired; no `RuntimeDowngrade` record with its trigger, scope, and re-evaluation path | 74, 75 |
| S4 | The six meanings of "decides" (analysis, calculation, evidence finding, recommendation, operative determination, executable action) are not a typed output contract; `OutputClassification` has six values that do not line up with them | 84 |
| S5 | Break-glass access (dual control, time-boxed, logged, never decision authority) has no primitive | 75 |

## Phase 1 - generic supersession (M)

Lift jaci's `promotion.py` into `jazzx_sdk/authority/supersession.py` with the object made generic:

```python
class AffirmedRecord(BaseModel):        # the human's immutable object (spread, finding, narrative draft)
    record_id: str; subject_ref: str; payload_ref: str; cell_ref: str
    affirmed_by: str; actor_class: str; affirmed_at: datetime
    version_bundle: VersionBundle

def affirm(*, matrix, cell_ref, actor, evidence_floor_met: bool, ...) -> AffirmedRecord | Refusal
def supersede(*, prior: AffirmedRecord | SupersessionEvent, scope: str, reason_code: OverrideReasonCode,
              values_ref: str, actor, matrix) -> SupersessionEvent | Refusal   # a new record, never an edit
def effective_view(subject_ref) -> EffectiveView     # derived: original, each supersession, effective values, lineage
```

`SupersessionEvent` is a canonical `OverrideEvent` with `override_type=decision_override` and `superseding_decision_id` set; do not add a second event shape. Rules from slide 68, as tests: the affirmed record is byte-identical before and after any supersession (replay test); no supersession without a reason code from the controlled list; the effective view names every applied supersession and who made it; escalation to a more senior cell creates a new supersession, never an edit; there is no "reject the override" path. The same rules hold when the superseding actor is an AI coordinator: it may flag and route a disagreement, it may not settle it (`actor_class` of the superseder must be human for a protected cell; the resolver's `human_only` already says which).

jaci then re-implements `promotion.py` as a thin binding over this primitive; its existing tests are the acceptance suite.

## Phase 2 - coordinator objects and the maker-checker rule (M)

`jazzx_sdk/conductor/coordination.py`:

```python
class WorkItem(BaseModel):      # one row of the slide 72 working view
    item_id: str; case_ref: str; finding: str; next_step: str; owner: ActorRef
    cell_ref: str | None          # the cell the next step needs; None for a human-only hand-off
    blocking: bool; due: datetime | None

class ReadinessState(StrEnum):   # per case, per gate
    READY = "ready"; BLOCKED = "blocked"; AT_RISK = "at_risk"; HANDED_OFF = "handed_off"

class WorkPlan(BaseModel):
    plan_id: str; case_ref: str; items: list[WorkItem]; readiness: dict[str, ReadinessState]
    coordinator: ActorRef; revision: int

class EscalationLadder(BaseModel):   # pack-declared, slide 67
    rungs: list[EscalationRung]      # case coordinator -> portfolio coordinator -> human supervisor -> forum
```

The coordinator is a co-worker cast in this role: an `InteractiveAgentSpec` or pipeline whose cells are `plan`, `assign`, `replan`, `request_review`, `escalate`, `approve_routine` (each a registered cell in the matrix, each earnable). Two rules enforced in code, not prompt: the coordinator cannot hold a protected cell (`human_only` cells are absent from its binding at load, refused at runtime), and it cannot approve work it directed or prepared itself (maker-checker: an `approve_*` cell invocation whose `WorkItem.owner` equals the coordinator's `ActorRef` is a `Refusal`, reason `self_approval`).

Every `WorkItem` must have an owner and a next step inside that owner's authority: a plan with an unowned flag or a next step naming a cell the owner does not hold fails validation (slide 72 "no flag without an owner, no owner without a next step, no next step outside its authority").

Acceptance: the slide 67 story runs as a test: Sentinel flags the stuck step, the coordinator re-sequences, opens a chase task for the RM co-worker, accepts the hand-off packet (an earned routine cell), requests the underwriter's review on the contradiction (a hand-off, not a decision), and the affirmation stays human; a coordinator attempting the affirmation is refused `HUMAN_ONLY_ACTION`; self-approval is refused.

## Phase 3 - Sentinel to runtime downgrade (S to M)

`authority/downgrade.py`:

```python
class DowngradeTrigger(StrEnum): EXTRACTION_DRIFT = ...; OVERRIDE_SPIKE = ...; RECEIPT_FAILURE = ...; CONFIDENCE_MISCALIBRATION = ...; STUCK_WORK = ...; MANUAL = ...   # a platform owner's kill switch
class RuntimeDowngrade(BaseModel):
    downgrade_id: str; cell_ref: str; scope: Literal["cell", "surface", "pack"]; to_level: AutonomyLevel  # recommend (slide 74), or refuse for a manual kill switch
    trigger: DowngradeTrigger; evidence: SentinelResult | None; applied_by: ActorRef | None; reason: str | None; applied_at: datetime   # evidence for Sentinel triggers; actor and reason for MANUAL
    reevaluation: str      # what evidence lifts it; "seconds down, weeks up"
    lifted_at: datetime | None; lifted_by: ActorRef | None   # lifting is a promotion: forum, never Sentinel
```

Wire: `SentinelMode.run` emits a `LoopSignal` (from the knowledge-loop plan) and, when a configured threshold is crossed (pack data, like the ECAP thresholds in the AML appendix), a `RuntimeDowngrade`. The execution profile's `cell_activations` is read through a `DowngradeStore` so `resolve_effective_autonomy` receives the active downgrades in its existing `downgrades` argument. Nothing in the resolver changes. A downgrade is applied automatically and lifted only through the promotion forum (slide 74 "seconds down, weeks up"); the Evaluator attests the evidence for lifting, never lifts.

The same record carries the manual kill switch a platform owner needs: `trigger=MANUAL`, tenant-scoped, on one action class or cell, to `recommend` or `refuse`, with the actor and a reason, applied through a Plato route and visible on every resolution it affects. It is lifted by the same forum path as an automatic downgrade, so a kill switch cannot be quietly switched off by the person who threw it. Budgets and spend ceilings stay where they are (`llm/` gateway); this record is the authority-side switch, not the cost-side one.

Acceptance: an override rate above the pack threshold on a cell drops that cell to `recommend` on the next resolution, with the downgrade and its trigger in `contributing_layers.runtime_downgrades`; a manual kill switch on an action class refuses every action in that class for that tenant on the next resolution and is recorded with the actor and reason; a lift attempted by the Sentinel, the Evaluator or the actor who threw a manual switch is refused; the trace step for the downgraded action shows the effective level and the downgrade id.

## Phase 4 - the six output kinds (S)

`experts/base.py` `OutputClassification` is the IIF 1.5 MSC §7.5 vocabulary and stays. Add `DecisionKind` on canonical `Decision` (and on the co-worker output contract): `analysis`, `calculation`, `evidence_finding`, `recommendation`, `operative_determination`, `executable_action`, with the mapping to `OutputClassification` fixed in one table (`recommendation` is a `decision_candidate`, `operative_determination` is a Decision under a final cell, `executable_action` is an automation with a receipt). The Governor refuses an `operative_determination` from an actor whose effective level on that cell is below execute, and refuses an `executable_action` with no `Receipt`. The slide 84 CRE sizing example (calculation, evidence finding, recommendation; the determination is the credit officer's) is the test.

## Phase 5 - break-glass (S)

`authority/break_glass.py`: a dual-control, time-boxed grant of visibility (never of a decision cell) with both approvers, the scope, the expiry and the reason in a `ConfigAuditEvent`; expiry is enforced on every hop, not only at grant. Slide 75 gives the three shapes (dual-control emergency access, supervisor visibility for triage with a four-hour ceiling, manager visibility on a stuck case).

## Decisions this plan does not make

- Whether the coordinator runs as a pipeline on the Conductor or as an `InteractiveAgent`; both can hold the same cells. Default: pipeline for queue and portfolio coordinators, agent for the case coordinator.
- Which thresholds trigger a downgrade: pack data, never SDK constants (the RBAC spec's rule 1).
- Whether `RuntimeDowngrade` is tenant-scoped on Plato; it must be, and the tenancy shape follows the 2.6.0 plan's D3.

## Sequencing

P1 first (it unblocks jaci's reuse and the Expert plan's "caller's own Verifier attests" story). P3 second; it is small and the deck leans on it. P2 third. P4 and P5 independent.

## Guardrails

- Do not change `resolve_effective_autonomy`; feed its existing `downgrades` argument.
- Do not add a second override event type; `SupersessionEvent` is an `OverrideEvent`.
- Protected cells never appear in a coordinator's binding; enforce at load and at runtime, both.
- Re-verify anchors at HEAD per phase; commits only, no push.
