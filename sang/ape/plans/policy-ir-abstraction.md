# Policy IR: making the intermediate representation not matter

Companion to `reasoner-chassis-analysis.md`. Checked against `/Users/sangit/src/japes` v2.2.4 and
`/Users/sangit/src/macer` (japes 1.9.6).

> **P8 (§4.1/4.2/4.3 — the open Condition union, the ConditionEvaluator registry, RuleOutcome)
> shipped 2026-08-02** as part of the v2.3.0 local work (unpushed): `Condition` open union with
> `Expression`/`DslExpression`/`RatioCondition` + a discriminated-union `kind` tag (shape-sniffing
> fallback keeps pre-P8 dicts with no `kind` key validating unchanged); `fabric.canonical.
> condition_evaluator` registry (`register_condition_evaluator`/`get_condition_evaluator`) with
> the three built-in evaluators; `Rule.applicability` as the cheap pre-check field; `RuleOutcome`/
> `EvidenceContract`/`Verdict` types; `DefaultPolicyExpert.check_compliance` rewired off the closed
> `isinstance` branch, closing the `fields_claimed` hole for DSL/ratio conditions. §4.4 (cost
> partition) and §4.5 (compilation as an offline stage) are not built — no caller needs them yet.
> P1/P2/P6 (the ceiling extensions from `reasoner-chassis-analysis.md`) are next.

---

## 0. Summary

You're right that English JTBDs should be one option rather than the substrate, and japes has already
started building the seam — it just stopped at two representations and wired them with `isinstance`.
`fabric/canonical/policy.py` has `Rule` with `condition: Expression | DslExpression | None`,
`citations: list[str]` resolving into `Policy.source_refs`, `priority`, `action: RuleAction`, and
`Policy.exception_rules`. That is roughly 80% of the obligation model, already canonical, already
persisted.

So the recommendation is **not** to introduce an `Obligation` type. It is to:

1. Make `Rule.condition` an **open discriminated union** with a registry, instead of two hard-coded
   classes and an `isinstance` branch.
2. Define the **evaluator contract** — which is where the real design work is, not in the union.
3. Let **MACER's JTBD become one registered kind** (`natural_language`), so English is demoted from
   substrate to option, exactly as you framed it.
4. Make **compilation from source English documents an explicit, versioned, offline stage**, which
   MACER does not have at all.

The payoff is not tidiness. Tagging each rule with an execution kind lets the adjudicate stage
**partition by cost**: deterministic rules skip the LLM, skip document batching, and skip
ensembling. A pack that formalizes 70% of its policy stops paying `k × obligations` LLM calls for
that 70%. Today MACER pays full LLM price for every obligation including pure numeric comparisons.

---

## 1. What MACER actually does for a numeric threshold

Worth stating concretely, because it's the strongest argument for your position.

"Is DTI under the conforming threshold?" today:

1. The threshold exists **only as English prose** in `LoanMetricDefinition.indicator_context` —
   e.g. `"compare_to_dti_threshold"` (`data/ontologies/common/mortgage_jtbd_ontology_v1.json:437`),
   pasted verbatim into the prompt (`jtbd_agent.py:690-716`).
2. The LLM reads documents and extracts the inputs.
3. The LLM **writes Python**, executed by a restricted `exec()` sandbox (`tools/repl.py:252`) whose
   own docstring documents an escape via `fn.__closure__[0].cell_contents.__globals__`
   (`repl.py:115-124`).
4. Code's only contribution is checking that **step 3 happened at all** —
   `validate_calculation_markdown_against_context` raises if a metric has a value but
   `PYTHON_REPL_INVOKED` is False (`loan_metrics_utils.py:225-234`). And that check is disabled
   wholesale for Vertex models (`jtbd_agent.py:1693`).
5. The result lands in `LoanMetricValue.value: **str**` (`models/jtbd.py:167-223`) — `"43.5%"`.
   There is no numeric channel out of a JTBD at all.

Four stochastic hops and a sandbox for a `>=`. Nothing in the pipeline can answer "what threshold
was applied?" without re-reading prose. Meanwhile japes already ships `evaluate_ratio(...) ->
RatioResult{computed_value, threshold, direction, passed, margin, severity}`
(`tools/ratio_evaluator.py`) — typed, testable, free.

Three more MACER findings that support the same conclusion:

- **No applicability predicate exists.** Applicability is decided three different non-declarative
  ways: a **string prefix match** on LLM-merged prose (`jtbd_agent.py:1636` — `if
  jtbd_text.lower().startswith("not applicable")`), the optional orchestrator LLM, or the
  verification agent electing `NOT_APPLICABLE`. If the merge agent rephrases, the check silently
  misses.
- **Per-investor variants resolve through magic sentinels plus an LLM merge.** `"NO_CHANGE"` and
  `"NOT_APPLICABLE"` are string literals inside `requirement_text`; anything else triggers a
  `jtbd_text_determiner` LLM call that merges COMMON + investor prose (`jtbd_agent.py:769-864`).
  Policy variant selection is non-deterministic.
- **Provenance is declared and dead.** `InvestorRequirement.policy_references: list[PolicyReference]`
  with `{policy_ref, link, doc_id, short_desc}` exists — and grep finds **zero production readers**.
  The real citation is LLM-authored into `JTBDResult.policy_ref: str`, then post-processed by
  *another* LLM to strip the filename and keep the section code, falling back to `"N/A"`
  (`findings_converter.py:774-830`). Provenance is asserted and plausibility-checked, never carried.

`condition_mappings` is likewise declared-but-unread. So a subsuming abstraction can absorb these
slots cheaply — but must not assume existing data populates them.

---

## 2. What japes already has

`fabric/canonical/policy.py`:

```python
class Rule(BaseModel):
    rule_id: str
    condition: Optional[Union[Expression, DslExpression]]   # ← the seam, currently closed
    action: RuleAction            # allow|deny|escalate|require_approval|require_evidence|notify|log
    parameters: Optional[dict]    # approval_authority, evidence_types, fail_action, escalation_target…
    priority: int = 100
    description: str
    citations: list[str]          # ref_id values into parent Policy.source_refs[]
    domain_extensions: Optional[dict]

class Expression(BaseModel):     field: str; operator: ComparisonOperator; value: Any
class DslExpression(BaseModel):  formula: str      # AST-evaluated, jazzx_sdk/expressions/
```

`Policy` carries `rules`, **`exception_rules`**, `source_refs: list[SourceRef]`, `policy_type`,
`jurisdiction`, `scope: PolicyScope` (institution/product/deal), `effective_date`/`expiry_date`,
`supersedes`, `authority_matrix`. `SourceRef` = `{ref_id, title, authority, ref_type, section, url,
effective_date}`.

Adjacent assets that already exist and should be reused rather than reinvented:

| Asset | Location | Relevance |
|---|---|---|
| `evaluate_ratio` / `evaluate_covenant_policy` → `RatioResult` | `tools/ratio_evaluator.py` | The de-facto deterministic check evaluator. Already walks `policy.rules` duck-typed. |
| Expression DSL: `parse`, `evaluate`, `validate`, `MetricDefinition`, `EvaluationRefusal` | `jazzx_sdk/expressions/` | Real AST evaluator (not `eval`), with static validation for undefined refs, unit mismatch, circularity. |
| `SourceCoordinate` + `ProvenanceEntry` + `ProvenanceType` | `fabric/canonical/evidence.py` | The provenance invariant. `PageLocator`/`CellLocator`/`SectionLocator`, discriminated. |
| KH Rego: `evaluate_policy(collection_id, entity_names, rego_package_name, …)` | `clients/knowledge_hub_client.py`, `tools/policy.py` | Server-side OPA over KH entities, result written back as an entity. |
| `KGStore.query/traverse` over `Triple` | `fabric/graph/store.py` | Graph substrate. Filter-by-field, **no SPARQL anywhere in the repo**. |
| `PolicyProfile.get(key)` fail-closed | `fabric/canonical/profiles.py` | Named thresholds. |
| Statemachine guard lint | `statemachine/schema.py` | **Rejects bare numeric literals** in guards: `"use a profile key (e.g. 'profile:dscr_floor'), never a hard-coded threshold"`. Best existing precedent for threshold expression — adopt it. |

Two things to know before designing against this:

- **`fabric.opa` is an explicit stub.** Every method `raise NotImplementedError`. Its docstring
  states the intent: *"OPA/Rego enforcement is being reworked to arrive via the canonical `Policy`
  object (compiled/projected to Rego) rather than through standalone bundle uploads."* That
  projection does not exist. Rego today is only reachable via the KH round-trip.
- **The canonical `Policy` has no `rego`/`rdfs` field.** Those three parallel representations
  (`rego_rules`, `raw_policy`, `rdfs_rules`) live on the **KH-side policy record**, not the pydantic
  model. So KH already believes in multi-IR; the canonical layer hasn't caught up.

---

## 3. The actual gap

There is a `Rule` declaration and at least five evaluators — `_evaluate_condition`,
`_evaluate_dsl_condition`, `evaluate_covenant_policy`, `expressions.evaluate`, statemachine guards.
**There is no dispatch abstraction that selects an evaluator per rule.**
`DefaultPolicyExpert.check_compliance` (`experts/policy/default.py`) hard-codes it:

```python
if isinstance(rule.condition, DslExpression):  ...   # → _evaluate_dsl_condition
else:                                          ...   # → _evaluate_condition
```

And `evaluate_covenant_policy` does the other half of the anti-pattern — it **silently skips** rules
whose `condition.operator` isn't in `{">=", ">", "<=", "<"}`. Current dispatch is "branch on the two
you know, quietly ignore the rest." Adding kinds on top of that multiplies the problem.

Two second-order defects to fix while you're in there:

- **`fields_claimed` precedence has a hole.** `check_compliance` uses `fields_claimed: set[str]` so a
  higher-precedence policy owning a field makes lower ones skip it — but `DslExpression` conditions
  **bypass it entirely** (code comment: *"No single field to claim/skip"*). Every new kind
  reintroduces this hole unless the contract makes claimed fields explicit. `evidence_contract()`
  below is the fix.
- **`ExecutionKind` is descriptive only.** `ConductorEngine` never reads `step.execution` or
  `StepImpl.execution`; `validate_against_registry` checks `impl` and `emits` but not `execution`.
  Making it load-bearing at runtime would make the Reasoner its first consumer — worth flagging as a
  deliberate extension rather than assuming it already works.

---

## 4. The design

### 4.1 Open the union

```python
# fabric/canonical/policy.py
class ConditionBase(BaseModel):
    kind: str                          # discriminator, registry key
    claims: list[str] = []             # field paths this condition owns (fixes fields_claimed)

Condition = Annotated[Union[...registered...], Field(discriminator="kind")]

class Rule(BaseModel):
    condition: Condition | None
    applicability: Condition | None = None    # NEW — orthogonal to the condition
    ...
```

`applicability` separate from `condition` is the fix for MACER's three-mechanism applicability mess,
and it's usually the *cheap* one — `program == "FHA"`, `facility_type in [...]` — even when the
condition itself is LLM-evaluated. Evaluating applicability deterministically before dispatching a
LIVE condition is free savings.

Shipped kinds:

| `kind` | Payload | ExecutionKind | Stochastic |
|---|---|---|---|
| `expression` | `field, operator, value` (existing) | DETERMINISTIC | no |
| `dsl` | `formula` (existing, AST) | DETERMINISTIC | no |
| `ratio` | `numerator, denominator, threshold: profile:key, direction, warning_buffer` | DETERMINISTIC | no |
| `canonical_query` | `model, where: list[Predicate], expect` | DETERMINISTIC | no |
| `graph` | `subject/predicate pattern, traverse spec, expect` | DETERMINISTIC | no |
| `rego` | `package, rule_name, entity_names` | INTEGRATION | no |
| `decision_table` | DMN-shaped rows (Flowable is already in the stack) | DETERMINISTIC | no |
| `natural_language` | `text`, `variants: list[Variant]`, `evidence_hints` | LIVE | **yes** |
| `composite` | `gate: Condition`, `escalation: Condition` | derived | derived |

`composite` deserves emphasis: **mixed rules are the common case, not the exception.**
"DSCR ≥ 1.25 *unless the borrower demonstrates compensating factors*" is a deterministic gate plus an
LLM exception clause. `Policy.exception_rules` already exists as the slot for the second half. If the
gate passes, the LLM is never called — which is the majority of cases in practice.

Thresholds must be `profile:<key>` references, not literals, per the statemachine guard lint. That
gives you one place to see every threshold a pack applies, and makes "which thresholds changed?" a
diff rather than a grep.

### 4.2 The evaluator contract — where the design effort goes

A tagged union alone defers the problem. The content is here:

```python
class ConditionEvaluator(Protocol):
    kind: str
    execution: ExecutionKind
    stochastic: bool                    # → drives ensemble k; False forces k=1

    def evidence_contract(self, cond: Condition) -> EvidenceContract:
        """Static, no I/O. What this condition reads:
           - fields:     canonical entity field paths  (→ claims, → fine-grained impact)
           - doc_types:  unstructured evidence classes (→ coarse impact, → prefetch)
           - entities:   canonical types touched
           Called at pack-load for validation, and at plan time for impact resolution."""

    async def evaluate(self, cond: Condition, ctx: AdjudicationContext) -> RuleOutcome: ...

register_condition_evaluator(RatioEvaluator())   # NamedRegistry, same pattern as
                                                  # register_compaction_strategy / StepRegistry
```

`evidence_contract` being **static and I/O-free** is what makes the rest work: it feeds `claims`
(closing the `fields_claimed` hole), feeds impact resolution, feeds prefetch, and lets pack-load
reject a rule referencing a field the ontology doesn't have — the failure moves from run time to
build time.

An unknown `kind` must **raise**, not skip. That is the single most important behavioural difference
from `evaluate_covenant_policy` today.

### 4.3 `RuleOutcome` — required core, optional narrative

The hard part: a SQL rule yields a status and a number; an LLM yields observations, page-cited facts,
conditions, and a minority report. Union → deterministic rules emit mostly-empty findings.
Intersection → you throw away the LLM's value.

```python
class RuleOutcome(BaseModel):
    rule_id: str
    verdict: Verdict                       # core, closed: SATISFIED|VIOLATED|INDETERMINATE|NOT_APPLICABLE
    status: str                            # pack vocabulary: PASS/FAIL/CONDITIONAL, CLOSE/ESCALATE/SAR_REFER…
    action: RuleAction | None              # japes's existing allow|deny|escalate|require_approval|…
    inputs: dict[str, Any]                 # REQUIRED — values actually used, w/ threshold resolved
    citations: list[SourceCoordinate]      # REQUIRED — the invariant
    confidence: Confidence | None
    narrative: Narrative | None            # observations, facts, conditions, minority_report
    provenance: ProvenanceEntry
```

`verdict` (closed) and `status` (pack vocabulary) are deliberately separate — downstream governance
reads `verdict`, the domain UI reads `status`. `action` is orthogonal again: it's "what to do," not
"what's true." All three already have precedent in japes; keeping them distinct avoids the collapse
MACER made, where `status` carries all three meanings at once.

`inputs` is required and is the thing MACER cannot produce. It makes a deterministic finding
**reproducible** — you can re-derive it without an LLM — and it's what an auditor actually asks for.

Deterministic evaluators may **optionally** delegate narrative to a cheap "explain this outcome" LLM
pass. That's a much smaller call than adjudication, runs only for violations, and gets you readable
findings without giving up determinism on the verdict.

### 4.4 Cost partition — the strategic payoff

With `execution` and `stochastic` on the evaluator, the `adjudicate` stage partitions:

```
plan ──▶ partition by evaluator.execution
         │
         ├─ DETERMINISTIC / INTEGRATION ──▶ evaluate directly over canonical entities
         │                                   no LLM · no batching · k=1 · milliseconds
         │
         └─ LIVE ──────────────────────────▶ run_replicated_segments  (P1)
                                             batched prompts · k replicas · ensemble collapse (P2)
```

Deterministic rules read **extracted entities**, not documents — so the whole batching rationale
(amortize document reads) doesn't apply to them, and neither does ensembling. `k=3` on a `>=` is a
3× bill for zero variance reduction.

This also promotes `DocumentAgent` from a preliminary stage to the load-bearing substrate: the
quality of extraction now determines how much policy can be evaluated deterministically. That is a
better place to spend engineering effort than prompt-tuning an adjudicator.

And it makes impact resolution sharper. MACER joins on document classification and **fails open to
all sections** on an unknown type (`data/__init__.py:166-171`). A deterministic rule declares
`fields`, so impact becomes "did *this field* change in the extracted entity?" — precise instead of
conservative.

### 4.5 Compilation as an explicit offline stage

Your framing — "the intermediate representation of the multi-page original English documents used in
the domain pack" — implies a compiler. MACER has none: JTBDSets are hand-authored JSON fetched whole
from KH by UUID (`jtbd_setup.py:465`), and guidelines are downloaded *separately* for the agent to
read at verification time. Nothing connects a JTBD to the guideline text it came from.

```
source policy docs (pack)  ──▶  PolicyCompiler  ──▶  Policy{rules[]}  ──▶  reasoner (runtime)
        │                       ExecutionKind.OFFLINE_ASSET                  │
        │                       build time, versioned, diffable              │
        └──────────── SourceRef / SourceCoordinate ───────────────────────────┘
```

Four properties that matter:

1. **Build-time, not runtime.** The register is a reviewable artifact in the pack, diffable in a PR.
   Recommended over compile-on-ingest: this is where policy fidelity is won or lost, and it's the
   first thing an auditor asks to see. (Runtime compilation is the alternative if policy changes
   must land without a pack release — worth a deliberate decision, not a default.)
2. **Mixed output, with an honest fallback.** The compiler emits whatever kind each clause supports
   and falls back to `natural_language` when it can't formalize. You never have to formalize
   everything — which is what makes this adoptable rather than a boil-the-ocean rewrite.
3. **Coverage becomes a measurable pack quality metric.** "% of rules deterministic" is a governance
   artifact and a cost forecast in one number. It also gives a pack team a gradient to climb.
4. **Provenance is mandatory output.** Every emitted rule carries `citations` → `Policy.source_refs`
   → the source span. This is what makes policy-change impact analysis possible: source doc changed
   → which rules recompile → which findings are stale.

---

## 5. The counterargument, stated fairly

English obligations are not purely an anomaly to be engineered away, and the design shouldn't pretend
otherwise.

- They are **readable by the person accountable for the decision**. An underwriter can review a JTBD;
  they cannot review Rego.
- They are **authorable by a domain expert without an engineer**. A formalized register puts an
  engineer in the loop for every policy change — which in a regulated domain is a real throughput
  cost and a real staleness risk.
- They **degrade gracefully on novel cases**. A SQL rule on an unanticipated fact pattern returns the
  wrong answer confidently; an LLM tends to flag ambiguity.
- Much genuine policy is **irreducibly judgmental** — "reasonable explanation for the credit
  inquiry," "compensating factors," "adequate documentation." Formalizing these produces a precise
  answer to the wrong question.

So the goal isn't elimination. It's: **make the IR a per-rule choice, make the deterministic path the
default where the clause is expressible, and make the English path a first-class registered kind
rather than the substrate.** That is exactly the abstraction you asked for, and it happens to be the
cheap one too — the deterministic rules are the ones you were overpaying for.

One risk to name explicitly: an abstraction this shape can be **too thin**. If `condition` is
effectively `Any` plus a tag, the problem has been relocated, not solved. The load-bearing surfaces
are `evidence_contract()` and the `RuleOutcome` core (`verdict`, `inputs`, `citations`). If those two
are right, kinds are cheap to add. If they're vague, every new kind is a new special case and you've
rebuilt `isinstance` with extra steps.

---

## 6. Impact on the build plan

Slots into `reasoner-chassis-analysis.md` §7:

- **Phase 1 (SDK upgrade)** — unchanged, still the prerequisite.
- **Phase 2 (primitives)** — P2 `EnsembleCollapse` now keys off `evaluator.stochastic`. Small change,
  worth making before there are callers.
- **NEW, parallel with Phase 2 — `ConditionEvaluator` registry.** Open the union, define the
  contract, port the two existing evaluators onto it, delete the `isinstance` branch in
  `DefaultPolicyExpert`, fix the `fields_claimed` hole. Self-contained and useful to any pack that
  never adopts the Reasoner.
- **Phase 4 (chassis)** — `adjudicate` becomes the partitioning step of §4.4. Makes `ExecutionKind`
  load-bearing at runtime for the first time.
- **Phase 5 (mortgage pack)** — MACER's JTBDSet compiles to a `Policy` whose rules are
  `natural_language`, and the shadow-run diff is finding-for-finding identical **by construction**.
  Then formalize opportunistically: every `LoanMetricDefinition` with an `indicator_context`
  describing a numeric comparison is a `ratio` candidate. Measure cost per converted rule — that
  number is the business case for the whole exercise.
- **Phase 6 (impact)** — P3 gets the fine-grained field-level path from `evidence_contract()`.
- **Phase 3 (P6 grounding)** — unchanged, and note it now applies **only to the LIVE partition**,
  which shrinks its blast radius and its cost.

Open decision worth making deliberately rather than by default: **build-time vs. runtime
compilation** (§4.5, item 1). I'd recommend build-time, but if policy changes must land without a
pack release, that inverts and the register becomes a KH-resident artifact with its own versioning —
closer to what MACER does today, minus the hand-authoring.
