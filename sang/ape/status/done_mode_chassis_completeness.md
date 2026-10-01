# Design note — ReasoningAgent, the cognitive modes, and the adjudication chassis: what's actually left

Author: Claude (Cowork) for Virendra Mehta · 2026-08-08 · **Revision 2**
Audited against: `japes` 2.3.4 working tree (Phase 4/6 chassis work uncommitted), `jaci` v0.19.1
`dev` @ `f56baf9`, `macer` working tree, and the full `ape/` + `aci/` plans and status corpora.

**Revision note.** Revision 1 was written without access to `ape/plans/` and `aci/plans/`, which are
symlinked outside the repos. Three of its findings were re-derivations of positions the design notes
already hold, and one framed a deliberate design decision as a gap. Those are corrected here and
listed in §5, because the corrections are the useful part. Four findings survive unchanged and three
are new, all verified against code this session.

Following the repo convention (`ape/CLAUDE.md`: commit outcomes, not planning; `docs/plan*` and
`docs/status*` are gitignored in both repos), this note lives in the plans folder, not in a tracked
`docs/` path.

---

## TLDR

Seven findings, ranked. Four are new to the corpus; three sharpen something already recorded.

1. **`EvaluatorMode` never migrated and nobody noticed** — own `AsyncOpenAI` client, no `BaseMode`,
   hand-parsed JSON. Absent from every plan: not scheduled, not deferred, no reason given. The
   compounding loop is the one part of the platform with no gateway governance, no retry, and no
   token accounting. `ape/CLAUDE.md` §7 ("check the full family, not just the nearest sibling") is
   the rule this violates.
2. **`replicas: int = 3` contradicts your own measurement.** `design_note_p1_p2_sizing.md` says
   plainly: *"Default `replicas=1`, not 3. MACER's k=3 was inherited, not measured… A chassis
   primitive shouldn't bake in an unmeasured assumption."* The shipped chassis defaults to 3 in
   three places. And `ConditionEvaluator.stochastic` — the field the same note names as the gate —
   exists and is read by nothing.
3. **jaci's four arithmetic controls never run in the governed pipeline**, and the coverage register
   scores them as done.
4. **`reasoner-chassis-analysis.md` claims a domain-neutrality violation in `modes/catalog.py`
   "is fixed there." It is not.** Verified: the AML literals are all still present.
5. **`BaseMode.system_prompt` silently swallows a missing pack asset** — and contradicts
   `resolve_mode_prompt`'s own documented contract, which is that it raises.
6. **The 13-mode list exists in three unlinked places.** The chassis doc flags two of them; there
   is a third.
7. **jaci's constant `Confidence(0.98)` makes the XF-2 refusal gate structurally unreachable** — the
   MVDP wedge's own acceptance criterion cannot fire.

---

## 1. The ReasoningAgent migration

### 1.1 It is complete for what it scoped, and the scope was stated

Five operational modes migrated (Reasoner, Investigator, Governor, Verifier, Narrator), shipped
v2.3.0 on 2026-08-02, commit `7f270b5`, suite 2168 → 2195. Sentinel was correctly excluded —
`ModeKind.DETERMINISTIC`, pure Python for speed. All five use an identical lazy-construction idiom
so a caller that only reads `MODE_REGISTRY` metadata isn't forced to have a live runtime, and all
five now thread real `TokenUsage` into `ModeResult`.

The justification holds up. `design_note_reasoning_substrate.md:166-194` establishes by reading, not
inference, that the generic tier retried by *"lowercasing the exception and string-matching `429` /
`500` / `rate limit`"* with *"no handling at all for `ModelBehaviorError`, `MaxTurnsExceeded`, or
truncated output."* That was a real defect on the path every mode used.

### 1.2 Finding 1 — EVOLVE never migrated, and it is absent from every plan

`EvaluatorMode` (`jazzx_sdk/modes/evolve/evaluator.py`):

- `class EvaluatorMode(Generic[TInput, THypothesisContent, TDecision])` (`:32`) — **does not inherit
  `BaseMode`.** No `mode_name`, no `system_prompt` property, no `has_tools`, returns an
  `EvaluationReport` rather than a `ModeResult`.
- `self.client = client or AsyncOpenAI(api_key=getattr(settings, 'openai_api_key', None))` (`:94`) —
  bypasses `AgentExecutionService`, `resolve_model`, `RetryingModel`, and the LLM Gateway. An
  Anthropic-only deployment cannot run it. This matters more than it looks: `aci/CLAUDE.md:181-200`
  records that `AnthropicConductor` and `MixedModelHooks` were *deleted* from jaci on 2026-08-02
  precisely because `ReasoningAgent` resolves models across providers. The Evaluator is the one mode
  that didn't get that benefit.
- `response_format={"type": "json_object"}` → `json.loads` → `.get()` per field (`:126-156`). A
  truncated or malformed response either raises or silently yields `improvement_signals=[]`. **A
  silently empty signals list stops the compounding loop with no error anywhere** — the Curator gets
  nothing to route, and the weekly baseline the YETI charter asks for quietly becomes meaningless.

`Curator.synthesize_bucket` is a lesser version, and it is on a *third* execution path: it takes an
`LLMManager`-shaped `llm=` and goes through `jazzx_sdk/llm/structured_call.py`, which validates a
schema but has no retry, no truncation handling, and no token accounting. The reasoning-substrate
note's gap analysis surveyed callers of `ctx.runtime.agents.run(...)` — so this path was never
audited at all, not even to be dismissed.

**Why this is worth raising rather than shrugging at.** The words `EvaluatorMode`, `Curator`, and
`modes.evolve` appear zero times across `design_note_reasoning_substrate.md`,
`design_note_p1_p2_sizing.md`, `ape/CLAUDE.md`, and both REFACTOR plans. Every scoping sentence says
"the five." This is not a deferral with a rationale; it is a family that was never enumerated. That
is exactly the situation `ape/CLAUDE.md` §7 names: *"If three modules share a pattern and only one
got the fix, the other two are latent bugs until proven otherwise."*

One nuance in fairness: `platform_catalog.MODE_KINDS` classifies `curator` as `python` and
`evaluator` as `hybrid`, versus `agent` for the five. So "not a full LLM agent" is a recorded
position. It justifies Curator's Layer 1 being pure Python. It does not justify a hard-wired
`AsyncOpenAI` in the hybrid one.

### 1.3 Finding 2 — `replicas=3` contradicts the measurement, and `stochastic` is dead

This is the finding I'd act on first after the Evaluator, because it is your own recorded
conclusion being overridden by a shipped default.

`design_note_p1_p2_sizing.md` (2026-08-02) measured batched-vs-sequential and k=3-vs-k=1 on
`integ_data/loan_1_sarah`:

> Batching: ~2.1x fewer tokens, ~2.6x faster, **identical findings** both ways. k=3 ensemble: 3
> independent batched replicas agreed on every JTBD, 9/9 — **zero measured variance reduction, at
> the full 3.1x cost multiplier.**

And its P2 sizing conclusions, verbatim: *"**Default `replicas=1`, not 3.** MACER's k=3 was
inherited, not measured… A chassis primitive shouldn't bake in an unmeasured assumption."* /
*"**Gate replication on `evaluator.stochastic` (P8)**"* — `stochastic=False` forces k=1
unconditionally; `stochastic=True` makes k pack-tunable *"with **no** SDK-shipped default of '3'."*

Verified against the shipped chassis:

| Location | Value |
|---|---|
| `agents/adjudication/spec.py:59` | `replicas: int = 3` |
| `agents/adjudication/pipeline.py:132` | `replicas: int = 3` |
| `conductor/replication.py:84` | `replicas: int = 3` |
| `agents/adjudication/spec.py:46` (docstring) | *"Ensemble size `k` for the LIVE partition (MACER's default is 3)."* |

The docstring cites MACER's default as the justification — which is precisely the inherited,
unmeasured assumption the note says not to bake in.

And the gate exists. `fabric/canonical/condition_evaluator.py:44` declares `stochastic: bool`;
`:82`, `:119`, `:177` set it `False`; `:262` (`NaturalLanguageConditionEvaluator`) sets it `True`.
`partition_rules` (`agents/adjudication/partition.py:35-39`) reads `evaluator.execution` and
**never reads `evaluator.stochastic`**. So the field is declared, plumbed, and dropped — which
`domain-neutrality-and-config.md` §2 names as this SDK's characteristic failure mode, *"a pattern
worth naming once it's the second time you've found it."* This is the third time.

The fourth sizing conclusion is also unbuilt and is the more interesting one: *"escalate-on-
disagreement… start at a low `k` (1 or 2), and only spend more replicas (or route to a human) when a
cheap secondary signal suggests real uncertainty."* `AnyEscalate` exists but collapses votes you have
already paid for; it does not *decide to buy more*. That is a genuinely absent primitive.

**Consequence for anyone adopting the chassis:** a pack that takes the defaults pays 3× for a
benefit measured at zero on the one fixture anyone has run. The batching win is separately proven
and large. Recommend both differently.

### 1.4 Finding 4 — the chassis doc says a domain violation is fixed; it is not

`reasoner-chassis-analysis.md`, header companion-docs blockquote:

> `domain-neutrality-and-config.md` — the SDK must not encode "mortgage" (or any domain) anywhere;
> a real violation of this rule was found in `jazzx_sdk/modes/catalog.py` **and is fixed there**.

Verified against `jazzx_sdk/modes/catalog.py` in the current tree — all still present:

```
:78   canonical_consumes=["Alert"],          # investigator
:79   derived_object="case_file",            # investigator
:141  derived_object="case_file",            # conductor
:160  canonical_produces=["SARDraft"],       # narrator
:162  derived_object="sar_draft",            # narrator
```

`domain-neutrality-and-config.md` §1 identifies exactly these five and prescribes the fix
(`None`, following the pattern the four unimplemented modes already got right). §4 lists it as fix
#1 of three, sized at *"a few hours for #1 and #3."* There is no status file for that doc, no
`> Status` blockquote inside it, and no CHANGELOG entry referencing `MODE_REGISTRY`,
`canonical_produces`, or a domain-neutrality lint.

Two reasons this is worth more than its size. First, a doc asserting a fix that didn't land is worse
than a doc with an open TODO — the next reader stops checking. Second, the same doc's §4 fix #3 is
an **AST-based** neutrality lint (deliberately not grep, because the `modes/schemas.py` and
`skills/*/base.py` docstrings intentionally show AML/Mortgage/Healthcare side by side as a positive
pattern). That lint is what stops this recurring, and it is the cheap half.

### 1.5 Finding 5 — `BaseMode.system_prompt` contradicts its own resolver's contract

`jazzx_sdk/modes/base.py:132-152` catches `FileNotFoundError`, logs a warning, and substitutes
`f"You are the {self.mode_name} mode."`. A pack with a misnamed asset runs on a nine-word generic
prompt and reports nothing.

What makes this a defect rather than a design choice is that the layer below documents the opposite.
`plan_JAPES_2_2_2_DOMAIN_PACK_QUICKSTART_REFRESH.md:24`: *"`resolve_mode_prompt` … **raises
`FileNotFoundError` if none**"*, and the doc-fix instruction at `:64` is to *"State plainly … that
`resolve_mode_prompt` raises `FileNotFoundError` rather than returning empty."* The resolver is
designed to fail loud; `BaseMode` catches the signal and discards it.

Two conventions make this reportable: `REFACTOR-2.4:491` — *"failing with a typed error rather than
silently"*; and the principle `plan_assistant_sourav.md:40` invokes to justify the `resolve_knowledge`
P0 — *"capability fails loud, knowledge fails silently."* A mode prompt is knowledge.

`BaseMode` appears in no current plan at all — only in `status/done_JAPESv1.2-AgentExecutionLayer-DesignSpec.md`
(2026-05-31), a pre-1.4.0 architecture sketch.

### 1.6 Finding 6 — three unlinked copies of the 13-mode list

`reasoner-chassis-analysis.md` §4b flags two: *"the 13-mode list is duplicated verbatim in
`modes/catalog.py` and `fabric/canonical/trace.py` with no import linking them — they can drift
silently."* There is a third: `jazzx_sdk/platform_catalog.py:20` `MODES`, which `REFACTOR-2.3` §4.4
confirms is set-identical and proposes deriving from `MODE_REGISTRY` — deferred to 2.4, then not
scheduled in any 2.4 phase, so currently orphaned between two plans.

The blast radius is documented: `jaci/ui/platform_view.py:71-81` imports seven symbols from
`platform_catalog` inside `try/except ImportError` with a hardcoded fallback, so a drift there makes
jaci *"degrade **silently** to stale data rather than failing."*

### 1.7 Corrected: the "modes don't use the ceiling" observation

Revision 1 listed this as a gap. **It isn't one, and the corpus is ahead of it.**

`reasoner-chassis-analysis.md` §4c states the same fact and answers it:

> **Direct answer to "can ReasoningAgent + the five modes do MACER's actual job today":** no — each
> mode is a single-shot wrapper … so there is no segment×replica×batch topology, no grounding
> injection, and no ensemble collapse in the current mode layer at all. The primitives that would
> close that gap already exist … what's missing is Phase 4 itself.

Phase 4 *is* `AdjudicationAgent`, and it shipped 2026-08-07. And `design_note_reasoning_substrate.md:245-248`
holds the position deliberately: the modes' *"Conductor supplies evidence, agent has no tools"* shape
and MACER's *"agent gathers its own evidence in-session"* shape are *"both real, valid patterns for
different needs — **this substrate should support both, not force a migration off one shape.**"*

So `has_tools == False` across the operational modes is the design, not an omission. The only
residual is cosmetic: `ReasoningAgent`'s docstring says the ceiling is "layered on top" of the same
call, which reads as if it lives inside the agent. It is composed above it, by `run_segment`. A
one-paragraph docstring amendment, not a work item.

### 1.8 Corrected: "`MODE_REGISTRY` is inert"

Also a re-derivation. §4b says it first and better: *"Mode is **not load-bearing at runtime today**.
Authority keys on `decision_class × action_class × actor_class` and never sees mode; `MODE_REGISTRY`
has no runtime reader; `ModeContract.autonomy_default` is set on all 13 contracts and read nowhere;
prompt resolution keys on the mode *string*… Mode buys a prompt filename and a `TraceStep` enum
value."*

Two things I'd carry forward from it rather than restate:

**The trace trap, which is the actionable part.** `DEFAULT_SPAN_MODE_MAP` collapses 13 modes onto 3,
keyed on OTel span type. *"If the chassis doesn't supply a `mode_map`, every LLM call in its trace is
labelled `reasoner`* — including the Governor gate and the Narrator pass — *and the Trace lies about
what happened.*" This landed as `adjudication/tracing.py`'s `adjudication_name_patterns` seam,
because span type alone can't separate an adjudicate call from an emit call. **Any new consumer of
the chassis must supply it**, which is a concrete instruction for jaci and for a template-fill agent,
not a philosophical point.

**The autonomy opportunity, which is the good idea nobody has taken.** §4b's proposal is that the P8
DETERMINISTIC/LIVE partition is *simultaneously a cost boundary and a governance boundary* — a
deterministic rule check is reproducible from `RuleOutcome.inputs` without an LLM and can defensibly
launch at a higher autonomy rung; a LIVE judgment should cap lower and route to review. That is the
principled bridge between the two disconnected autonomy encodings (`ModeContract.autonomy_default`,
dead; `AuthorityCell.autonomy_launch`, live), bounded by the existing guardrail that a
`CellKind.FINAL` cell must be human-only or L0. It would make the chassis the first runtime consumer
of mode. Nothing schedules it.

---

## 2. jaci and commercial lending

### 2.1 Finding 3 — the four arithmetic controls are dead, and the register says they're done

`validate_package()` runs `detect_balance_control` (FR-VAL-1), `detect_cash_flow_tie` (FR-VAL-3),
`detect_equity_rollforward` (FR-VAL-4) and `detect_period_continuity` (FR-VAL-5) **only when
`control_tolerance is not None`**. `capabilities/credit_validation/provides.py:36` never passes one,
and `CLSpreadContext` has no field to carry it. They fire only from
`tests/unit/test_rb_reference_case.py` and `test_validation.py`, which call the detectors directly.

The design was deliberate — `aci/status/done_JACI_CL_VALIDATION_COMPLETION.md:14-16`: *"gated behind
`validate_package`'s new `control_tolerance` param (`None` by default — off, since tolerance is
institution policy, never a module default)."* Correct call. Nobody then supplied the policy value.

Two pieces of confirming evidence that this went unseen: `done_JACI_CL_POLICY_EXPERT.md:191-197` is
the most recent doc to modify that exact call site (it made `validate` async and added
`compliance_result=`), discusses the seam in detail, and never mentions `control_tolerance`. And
`PRD_COVERAGE_REGISTER.md:67-71` scores FR-VAL-1/3/4/5 **done, several marked (RB)**.

**Consequence:** FR-VAL P0 coverage drops from 83%, and the headline 61% P0 number moves with it.
The register's own second recorded lesson is the exact warning: *"'the test passes' and 'the PRD
claim is met' are different claims when the test's own fixture only covers part of what the claim
needs."*

This is the same defect class jaci has already caught twice by reading real output — v0.13.0's three
guaranteed-false BLOCKING findings on every real YETI run, and v0.14.0's two run paths where only one
populated the governed session state. It lands in familiar territory.

### 2.2 Finding 7 — constant confidence makes the wedge's own acceptance gate unreachable

`spread_package.py:46-48`: `_SOURCED_SCORE = 0.98`, stamped on every as-reported cell.

`status_JACI_CL_MVDP_VP2_WEDGE.md:44`, acceptance criterion **XF-2**: *"Sub-confidence admission is a
Refusal: values below profile floor refuse admission per cell `cl.eadm.003`… silent low-confidence
writes must be zero."*

A constant 0.98 against floors of `{high: 0.9, medium: 0.7, low: 0.0}` means no cell can ever fall
below any floor. XF-2 passes vacuously and can never fire. XF-1 (every cell carries provenance and
confidence) is genuinely met; XF-2 is met only because the quantity it gates on is a constant.

Four shipped features consume that constant as if it were signal: `rank_for_review` ranks on cell
confidence; the governed workbook writes it into cell notes; demo-arc Phase 3 renders it as a
template column; and the Streamlit review queue exposes a confidence weight slider showing *"the raw
cell confidence."* All four are ranking on a constant.

No document anywhere acknowledges the value is fixed — zero hits for `0.98` or "constant confidence"
across the whole `aci/` corpus. And `reconcile_packages()`, jaci's own multi-pass per-cell voter, has
**zero mentions anywhere in the corpus** and is called only from `test_spread_package.py`.

### 2.3 jaci uses neither new primitive

No import of `jazzx_sdk.agents.reasoning` (five docstring mentions, zero imports; it is reached only
transitively through the mode classes). Zero hits of any kind for adjudication, replication, or
ensemble collapse in a CL context. The three `ReasoningAgent` mentions in `aci/CLAUDE.md` are all
about AML provider portability.

Meanwhile `capabilities/commercial_lending/pipeline.py:145-200` (`run_entity_extraction`) is still a
raw `LLMManager().run(...)` with prompt string constants and a bare `json.loads` — no schema, no
`Refusal`, no confidence. It is the only hand-written LLM prompt left in `src/`, and it is the exact
generic-tier problem the migration was undertaken to remove.

### 2.4 Where the chassis fits — and the doc already says so

`reasoner-chassis-analysis.md` §6 gives commercial lending its own column: segments *Financials,
Collateral, Covenants, Guarantors, Exceptions*; obligations *credit-memo assertions + covenant
tests*; status enum *SATISFIED/EXCEPTION/WAIVED/RFI/N_A*; collapse **`DeterministicVote` + minority
to committee**; HITL *credit officer exception approval*. And: *"Commercial lending stresses
numerics… `tools/ratio_evaluator.py` and `tools/financial.py` already exist in japes; MACER's
sandboxed `python_repl` should become a `scratch`-mount capability rather than be reimplemented."*

So the pack shape is designed. What is absent is any plan to build it, and the CL track is between
waves — `PRD_COVERAGE_REGISTER.md:193-197`: *"Wave 1's planned phases are complete… **Waves 2 through
4 have no plans yet.**"* Proposals land in an open slot, not against a committed plan.

The mapping from macer's shape to jaci's validation layer holds, with one correction from §1.3: the
**batching** half is measured and strong (2.1× fewer tokens, 2.6× faster, identical findings), and
the **replication** half is measured at zero benefit and 3.1× cost on the only fixture anyone has
run. Adopt them at different confidence levels.

---

## 3. What macer contributes that the chassis still lacks

The chassis generalizes macer well and fixes four real defects on the way (`rule_id` echo instead of
positional zip; failed replicas excluded rather than synthesized as diluting votes; collapse as a
strategy object rather than a prompt string; vote accounting as `Ensembled.votes_considered` /
`votes_excluded`, which is the 2-1-split visibility macer's own eval doc says it lacks).

Two macer mechanisms have no SDK home and both are domain-neutral:

- **Human-veto exclusion.** macer's `ExclusionIndex` — "a reviewer rejected this evidence for this
  finding; never let it justify that finding again" — applied as a prompt rule *and* as a
  deterministic post-hoc revert. The two-layer structure is the point; the prompt layer alone is not
  a control.
- **Two-stage value voting with provenance quarantine** (`loan_metrics_utils.py:491-500, 576-634`):
  value wins on frequency, with provenance *excluded* from the winner fields so a citation can never
  buy a value the win; then among value-agreeing runs, the one that cited a source wins the displayed
  row. That separation is a genuinely reusable idea and nothing in the chassis expresses it.

`AdjudicationAgent._reconcile` is a no-op passthrough and its docstring says so. jaci's
`hitl_approval.py` / `corrections.py` / `promotion.py` — maker-checker over `AuthorityMatrixV2` +
`check_action`, with per-correction override lineage — is the real implementation. Prototype there,
promote after.

---

## 4. Findings, ranked

| # | Finding | New? | Where |
|---|---|---|---|
| 1 | `EvaluatorMode` bypasses the platform; EVOLVE absent from every plan | new | §1.2 |
| 2 | `replicas=3` contradicts the measured sizing note; `stochastic` declared and unread | new | §1.3 |
| 3 | jaci's four arithmetic controls never run; register scores them done | new | §2.1 |
| 4 | Chassis doc claims a `modes/catalog.py` domain fix that didn't land | new | §1.4 |
| 5 | `BaseMode.system_prompt` contradicts `resolve_mode_prompt`'s documented contract | sharpens | §1.5 |
| 6 | Three unlinked copies of the 13-mode list | sharpens (2 of 3 known) | §1.6 |
| 7 | Constant `Confidence(0.98)` makes XF-2 vacuous; four features rank on it | new | §2.2 |

---

## 5. Corrections to revision 1

Recorded because the failure mode is reusable, in the spirit of the chassis doc's own §8.

| Rev 1 claim | Correction |
|---|---|
| "No mode exercises the ceiling" listed as a gap | Deliberate and recorded. `design_note_reasoning_substrate.md:245-248` says the substrate must support both shapes and not force a migration; §4c gives the same answer and names Phase 4 (= `AdjudicationAgent`, shipped 2026-08-07) as the resolution. Demoted to a docstring nit. |
| "`MODE_REGISTRY` is inert" presented as a finding | Re-derivation of §4b, which says it first and adds the two things worth carrying: the `mode_map` trace trap, and the autonomy-bridge opportunity via the P8 partition. |
| Cited "`domain-neutrality-and-config.md` §3 and §6" | That doc has five sections (§0–§4); **there is no §6**. The §6 references in the corpus point at the *chassis* doc's §6 (three packs on one chassis). §3 was cited correctly. |
| Recommended k=3 replication for jaci spreading confidence | Contradicts `design_note_p1_p2_sizing.md`'s measurement (zero variance reduction, 3.1× cost). Batching is proven; replication must be gated on `stochastic` and measured on a spreading fixture first. See §1.3. |
| Proposed a top-level `jazzx_sdk/templates/` package | Violates `REFACTOR-2.3` P8 (module placement) and the Unified Documents ruling, and collides with the existing `jazzx_sdk/templating` and `tools/documents/templates.py`. Relocated into `jazzx_sdk/agents/template_fill/`. |
| Treated jaci's missing CL plan docs as lost | They aren't. The repo convention supersedes a plan in place with its `done_`/`status_` counterpart in `aci/status/`. All eleven survive. |
