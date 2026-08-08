# plan_JAPES_TEMPLATE_FILL_AGENT — processed document + output template → filled template

Repos: `japes` (the agent, the registry work), `jaci` (first consumer: CL spread).
**Revision 2** — reconciled against `ape/plans/` and `aci/plans/`. Assumes `japes` ≥ 2.3.4.
Companion to `plan_JACI_CL_SPREAD_ADJUDICATION.md`.

**Read first:** `ape/plans/REFACTOR-2.3-sdk-layout.md` §9.1 (P8, module placement) and §4.6 (the
Unified Documents ruling) — they determine where this code may live; `REFACTOR-2.4-subpackage-interiors.md`
§10 (P10, capability ahead of demand); `ape/plans/plan_assistant_sourav.md` §P2 and its
"Not recommended as-is" list; `aci/plans/plan_JACI_CL_PRD_COMPLETION.md` Wave 4b;
`aci/plans/plan_JACI_CL_PRD_DEMO_ARC.md:87`. In code: `jazzx_sdk/agents/document/agent.py`,
`jazzx_sdk/tools/documents/{extraction,templates}.py`, `jazzx_sdk/finance/{vocabulary,workbook,structure}.py`,
`jazzx_sdk/agents/interactive/{spec,registry,reads}.py`, and jaci's
`capabilities/commercial_lending/template.py` + `config/packs/ci-spread-core/spread_template.yaml`.

---

## Three things to settle before writing code

### 1. Two different objects are both called "template"

- **`ExtractionTemplate`** (`tools/documents/extraction.py:95`) — `RegionAnchor`s saying *where to
  find things in a source document*. Input-side. Shipped 1.8.6 and described then as *"generalizes
  the financial-statement spreader so domain packs feed a declarative template instead of
  hand-rolling the search."*
- **The output template** — the customer's own layout: their rows, their order, their labels, their
  semantics. jaci's `spread_template.yaml` is exactly this, with locators `("is"|"bs"|"cf", key)` for
  statement lines and `("m", metric_key, fmt)` for metrics. Output-side. No SDK home.

This plan builds the output-side primitive. jaci has it, bound hard to `FinancialSpread`.

Carry jaci's invariant verbatim: `spreader_template_trace()` emits, per row, the real `MatchKind`
(`exact_key` / `alias_key` / `exact_label` / `normalized_label` / `substring` / `unmatched`) plus
provenance and confidence, and **every template row is present, populated or not, so the unmatched
set is enumerable and never a silent blank**. That is the product requirement.

### 2. Where it may live — `jazzx_sdk/templates/` is ruled out

Revision 1 proposed a top-level `jazzx_sdk/templates/`. Three rules forbid it:

- **P8 (`REFACTOR-2.3` §9.1):** *"A module lives at the root of `jazzx_sdk` only if (a) it is
  cross-cutting foundation… The test for (a) is mechanical: the module imports nothing from
  `jazzx_sdk.*`, and two or more subpackages import it."* This imports from `finance`, `agents`, and
  `expressions`, and has one consumer. Fails both limbs.
- **The Unified Documents ruling** (ARCHITECTURE.md:554-555, quoted at `REFACTOR-2.3` §4.6): *"not a
  separate `documents/` package; there is no `jazzx_sdk.documents`."*
- **Name collision.** `jazzx_sdk/templating` (sandboxed Jinja2, 2.3.4) and
  `tools/documents/templates.py` already exist. P8 again: *"If a module needs a suffix to avoid
  colliding with a sibling, the namespace is wrong, not the name."*

**Everything in this plan lives under `jazzx_sdk/agents/template_fill/`** — a fifth `agents/` sibling
alongside `interactive/`, `document/`, `reasoning/`, `adjudication/`, all named for the shape of
work, per `design_note_reasoning_substrate.md:198-200`. The output-template schema is a module
inside it (`template.py`), not a package of its own.

**P10 obligation** (`REFACTOR-2.4` §10): a capability shipped ahead of demand must be *reachable*
(exported from `agents/__init__.py`), *marked* (a one-line module-docstring status note naming what
it waits on), and *fail-fast if callable but incomplete*. Skip this and the next audit proposes
deleting it — `REFACTOR-2.4` §14 records exactly that happening to `llm/routing.py`.

**Sequencing hazard:** `jazzx_sdk/agents/` currently carries the whole uncommitted `adjudication/`
package. Land or stash that deliberately before adding a sibling.

### 3. This is a transactional shape, not a cognitive mode

The recorded decision rule (`plan_caller_migration_jaci_k9.md:127-130`, from JAPES 1.6.3 PLAT-04):
*"investigation shape = hypotheses + evidence attestation + iterate-to-convergence. Transactional
shape = single-pass input→output(s), no hypotheses, no loop."* Template filling is transactional.
It gets no entry in `MODE_REGISTRY`, claims no mode, and is named for its work — the same argument
`reasoner-chassis-analysis.md` §4b used to rename `ReasonerAgent` to `AdjudicationAgent`.

It must still supply a trace mode map. §4b: `DEFAULT_SPAN_MODE_MAP` collapses 13 modes onto 3 by span
type, so without one *"every LLM call in its trace is labelled `reasoner`… and the Trace lies about
what happened."* Use the `name_patterns` seam `adjudication/tracing.py` established.

---

## Answering the objection this will draw

`aci/plans/plan_JACI_CL_PRD_DEMO_ARC.md:87` states a prohibition that sounds like it forbids this:

> **Do not add a `cited_rows` field and do not ask the credit-phase prompt to emit row keys.**
> `row_key` is `(section, label)`… a presentation construct owned by the pack's output template.
> Emitting it from a cognitive mode couples the reasoner to one institution's layout, so a relabelled
> row silently breaks citation. Asking a free-text reasoning prompt to also emit structured references
> is the prompt-fragility pattern we avoid.

It doesn't, and the distinction is worth stating in the code:

1. **The prohibition is about a cognitive mode leaking layout.** The credit reasoner's job is
   judgment; making it also emit presentation keys couples judgment to layout. `TemplateFillAgent`
   *is* the presentation layer — the template is its input contract, not a leak. No cognitive mode
   learns anything about the layout because of it.
2. **It echoes `TemplateField.key`, never `row_key`.** `key` is the canonical, stable identifier;
   `(section, label)` is not. The failure the prohibition names — *"a relabelled row silently breaks
   citation"* — cannot happen, because relabelling changes `label` and leaves `key` alone.
3. **It is validated, not trusted.** An unrecognized or missing key is `status="unmatched"`, never a
   silent drop, so a fragile emission fails loudly.

---

## Phase 1 — `OutputTemplate`

**File:** `jazzx_sdk/agents/template_fill/template.py`

```python
class TemplateField(BaseModel):
    key: str                      # canonical, stable identifier
    label: str                    # the customer's label, verbatim
    section: str | None = None
    order: int                    # layout is part of the deliverable
    dtype: str = "decimal"        # decimal | date | text | enum | bool
    unit: str | None = None
    required: bool = False
    aliases: list[str] = []
    description: str = ""         # the FDE's words, model-facing
    derivation: str | None = None # Expression DSL, when computed rather than extracted
    enum_values: list[str] = []
    columns: list[str] = []

class OutputTemplate(BaseModel):
    name: str
    version: str = "0.1.0"
    fields: list[TemplateField]
    columns: list[str] = []
    vocabulary_ref: str | None = None
    notes: str = ""
```

Rules, each with its reason:

- **`derivation` is an Expression DSL string, never free text.** `jazzx_sdk.expressions` has
  `validate` and `evaluate`; jaci's `dsl_catalog.py`/`metrics_catalog.py` prove the pattern. A
  computed row must be deterministic and statically validatable at publish time, never an LLM guess.
  Most important line in the schema.
- **`aliases` feed `finance.vocabulary.resolve()`, they don't replace it.** That module already owns
  matching and reports `MatchKind`. Per-template aliases are extra `LineDefinition` entries layered
  over the pack vocabulary. Building a second matcher is the "third re-derivation" objection
  `plan_assistant_sourav.md:76-79` raises about grounding.
- **No finance types in this module.** It must serve a credit memo, a KYC file summary, an insurance
  certificate schedule. A `Statement` or `DecimalValue` import here is a bug. `finance/workbook.py`
  set the precedent — *"type against the shape, not the pack"* (`Protocol` structural typing).

**Registry:** `OutputTemplateRegistry` in the same package, tiered 1/2/3 like `SkillRegistry`, with
`SkillRegistry`'s refuse-to-shadow guard rather than `TemplateRegistry`'s silent overwrite (a known
defect — `plan_assistant_sourav.md:143`). Do **not** design the tiering from scratch: that doc's
"Not recommended as-is" list says *"port `TemplateRegistry`'s existing tier convention."* Extract
`_TieredRegistry` from `agents/interactive/registry.py:38` into `jazzx_sdk/_registry.py` once.

**Tests:** `tests/test_output_template.py` — YAML round-trip; a `derivation` failing
`expressions.validate` is rejected at load, not at fill time; tier shadowing refused.

---

## Phase 2 — `TemplateFillAgent`

**Files:** `jazzx_sdk/agents/template_fill/{agent,spec,result}.py`

Mirror `DocumentAgent`: facade orchestrates, per-group fill does the work. Constructor-injected with
`AgentExecutionService`. All model calls through `ReasoningAgent` — never a bare `llm.run`.

**Spec.** `TemplateFillAgentSpec`: `name`, `persona`, `model`, `group_by` (`section`|`none`|`column`),
`max_fields_per_call`, `require_grounding`, `confidence_floor`, `mounts`, `skills`, and
**`replicas: int = 1`**. One is the default on purpose — `design_note_p1_p2_sizing.md` measured k=3 at
zero variance reduction and 3.1× cost, and concluded *"a chassis primitive shouldn't bake in an
unmeasured assumption."* Do not copy `AdjudicationAgentSpec`'s 3. `from_dir` (`fill.yaml` +
`persona.md` + `skills/`) follows `InteractiveAgentSpec.from_dir` and `AdjudicationAgentSpec.from_dir`
— do not invent a third loading convention.

**Result.** `FilledField(key, value, match: MatchKind, provenance, confidence, derivation, assumption,
rationale, status)` where `status ∈ {populated, unmatched, refused, assumed}`; `FilledTemplate(template,
fields, unmatched, refusals, usage)`.

**Invariant, asserted not documented:** `len(result.fields) == len(template.fields)` with equal key
sets. Add `assert_template_complete()` in the shape of `agents/document/agent.py::assert_provenance_complete`
(the XF-1 gate) and call it at the end of `fill()`.

`assumption` is FR-CUS-6: an assumed or allocated input is marked, with an editable value and a
rationale, and never presented as reported.

**Flow.**

1. **Resolve the source.** Accept a `DocumentResult`, a `SourceFile`, or markdown. Delegate to
   `DocumentAgent` for conversion — do not re-implement it.
2. **Deterministic pre-pass, before any model call.** For every field, try `finance.vocabulary.resolve()`
   against the document's extracted structure and the field's `aliases`; record the real `MatchKind`.
   Everything resolving `exact_key` or `alias_key` is done, no LLM. This is `partition_rules`' split
   applied to template filling and it is where the cost savings are. On a well-authored chart of
   accounts most rows should never reach a model.
3. **Group the remainder** by `group_by`, capped at `max_fields_per_call`; one `ReasoningAgent.run`
   per group over a `create_model`-built Pydantic type for exactly that group's fields, so schema
   failure gets feedback-and-retry for free. **Require the model to echo each `key` and validate it**
   — never positional alignment. `agents/adjudication/pipeline.py:44-53` encodes this lesson from
   macer's fragile zip-with-`NOT_APPLICABLE`-backfill; don't re-derive it the hard way.
   Batching is the measured win: 2.1× fewer tokens, 2.6× faster, identical findings.
4. **Never fabricate a miss.** An omitted field is `status="unmatched"`, not a synthesized null that
   reads as "checked and absent." A group whose source region is empty returns an explicit
   `UNAVAILABLE:` marker plus the instruction not to ask the user to upload anything — the trap
   `agents/interactive/reads.py` already handles for knowledge.
5. **Grounding check.** Reuse `agents/document/agent.py::_grounded` (`:67`) — verbatim
   case-insensitive presence, tolerating `1,000`/`$1,000`. Ungrounded values are confidence-capped,
   not admitted at full score. Free, and the only hallucination check that costs nothing.
6. **Computed fields last**, via `expressions.evaluate` over the populated fields. A derivation with a
   missing input yields `status="unmatched"` naming the input — never a silent zero (jaci FR-CUS-10).
7. **Evidence narrowing.** Wrap the fill in `EvidenceWorkspace(spec.mounts).open()`; apply
   `enforce_read_cap` to document reads. Reuse; don't rebuild.

**Tests:** `tests/test_template_fill_agent.py` — the deterministic pre-pass resolves with **zero**
model calls; an omitted field yields `unmatched` and the completeness invariant still holds; an
ungrounded value is capped; a derivation with a missing input names it; `from_dir` loads a folder.

---

## Phase 3 — template induction: how Wave 4b gets delivered

**Position this as Wave 4b's delivery mechanism, not a rival track.** `aci/plans/plan_JACI_CL_PRD_COMPLETION.md:63-65`
already owns it:

> Parse a customer workbook's labels, structure and formulas, detect hardcodes and plugs, map
> referenced lines to the chart of accounts, and emit a `spread_template.yaml` plus metric
> definitions. FR-ING-2, FR-EXT-8, FR-CUS-3. This is the PRD's declared anchor and **it lands last on
> purpose**… Building the generator before the target schema has been proven by hand is the wrong
> order.

That precondition is now satisfied: Wave 1e authored the RB template by hand, 36 rows transcribed
from the analyst's "First Citizens Format" tab, 21 bound to a chart-of-accounts key or metric id and
15 explicitly unbound with stated reasons. Say so when proposing this — 4b's own gate has opened.

**File:** `jazzx_sdk/agents/template_fill/induction.py`, plus CLI verbs.

**Deterministic first.** For `.xlsx`, walk the sheet — `finance.workbook`'s `WorkbookLayout` already
models sheets/rows/bindings, and openpyxl gives merged ranges, indent levels, number formats, and
formulas. Section structure, row order, `unit` (from number format), and `derivation` (from the cell
formula, translated to the Expression DSL) are all *derivable*. A row whose formula is `=B12-B18`
arrives as a `derivation`, not as an extracted field. Ask a model for none of this.

**Model second, semantics only.** One `ReasoningAgent` call per section proposing `key`, `dtype`,
`description`, `aliases` for rows the deterministic pass couldn't type, and mapping to the pack
`LineVocabulary`. Bounded, structured, one schema.

**FDE review gate — non-negotiable.** An induced template is `status="draft"` and cannot register
above tier 3 until a human promotes it.

```
jazzx template induce  <source.xlsx> --pack ci-spread-core -o draft.yaml
jazzx template review  draft.yaml          # diff vs pack vocabulary; list low-confidence fields
jazzx template validate draft.yaml         # expressions.validate on every derivation; dtype/unit checks
jazzx template publish draft.yaml --tier 2 # requires --approved-by; stamps version + source hash
```

`publish` runs `validate` first and refuses on failure — the fail-fast-on-structure-then-evaluate
shape `ProfileRegistry.publish()` already uses. Record `approved_by` and the source artifact hash;
"which customer file did this layout come from" is an audit question that will be asked.

**Pack Studio positioning — CLI and SDK only, no UI.** `plan_assistant_sourav.md` §P2 ("Position
'Studio' relative to Pack Studio before further design work") is **still open**, and its
recommendation is to harden the SDK and prove it with YETI *before investing further in Pack Studio
surface*. Its "Not recommended as-is" list adds: *"Do not start Studio UI work on
`InteractiveAgentSpec` authoring until the `AssistantManifest` relationship is decided."* The CLI is
the FDE surface; a UI is a later skin over the same verbs, and proposing one now walks into an open
question. Note also that jaci's corpus has **zero hits for "FDE"** — this vocabulary is new there.

**Tests:** `tests/test_template_induction.py` — a fixture `.xlsx` with merged headers, an indented
section, and one formula row: the formula becomes a `derivation`, the number format becomes a `unit`,
and publishing an unvalidated draft is refused.

---

## Phase 4 — the skills registry as the per-customer overlay

**The problem.** Every institution has quirks that live in neither the template nor the chart of
accounts: "this borrower's accountant books the revolver under long-term debt, reclass it";
"officers' comp is inside SG&A, break it out"; "prefer the tax return over the reviewed statement for
this segment." Today those become prompt edits or code branches. Neither is governable.

**The mechanism.** `SkillRegistry` is already tiered for exactly this — tier 1 platform / 2 pack
config / 3 builder, with a hard refusal when a less-trusted tier shadows a more-trusted name unless
`allow_override=True` (`agents/interactive/registry.py:50-58`). That maps one-to-one onto the
Assistant Binding Annex's overlay rules: §11.1 what overlays may narrow, §11.2 what they may not
change. A customer overlay is a tier-3 skill; it may add and narrow, never silently replace.

**The design decision, stated explicitly.** `Skill` is consumed today by `InteractiveAgent`, where a
skill with a definition becomes a scoped sub-agent exposed as a tool. `TemplateFillAgent` has no
parent model choosing tools.

**Recommended:** reuse `Skill` and add `TemplateFillAgent` as a second consumer with different
semantics — a skill's `instructions` are a *prompt overlay* on the field group it scopes, and `reads`
generate the same `list_/read_/search_` triple `agents/interactive/reads.py` already builds. One new
optional field:

```python
applies_to: list[str] = Field(default_factory=list)  # OutputTemplate field keys / sections this
# skill scopes. Empty = whole template. Honored by TemplateFillAgent; ignored by InteractiveAgent.
```

One optional field whose docstring names its consumer is far cheaper than a parallel `MappingSkill`
type, and keeps one registry, one tiering rule, one `validate()`. Reject the separate-registry
alternative unless `applies_to` proves insufficient in practice. Note the risk in §Risks.

**Resolution in the fill flow.** For each field group, collect every allow-listed skill whose
`applies_to` intersects it (plus empty-`applies_to` skills), order **tier 1 → 2 → 3** so the customer
overlay is read last and is the most specific instruction the model sees, and append under a
delimited heading. Record applied skill names and tiers on each `FilledField.rationale` — an FDE
debugging a wrong cell needs to know which overlay produced it, and a reviewer needs it for audit.

**The FDE loop.**

```
jazzx skill new  reclass-revolver --pack ci-spread-core --tier 3 --applies-to bs.long_term_debt,bs.revolver
jazzx skill validate --pack ci-spread-core
jazzx fill --template rb.yaml --doc <pkg> --skills reclass-revolver --dry-run
```

`--dry-run` prints the per-field diff against the previous run: which fields changed, and which skill
applied to each. That diff *is* the feedback loop, and it is what makes case-by-case skill authoring
safe rather than superstitious.

Close the loop through existing machinery: an FDE correction becomes an `ImprovementSignal`
(`jazzx_sdk.evaluation.feedback`, which jaci already uses in five places), the Curator routes it, and
`synthesize_bucket` drafts a candidate skill for SME review. That path depends on japes 2.4.0
Phases 2-3 — today `EvaluatorMode` can silently return an empty `improvement_signals` list and stop
the loop with no error.

**Tests:** `tests/test_template_fill_skills.py` — a tier-3 skill scoped to two keys affects only those
groups' prompts; tier ordering places the overlay last; tier-3 shadowing a tier-1 name is refused;
applied skill names appear in the result.

---

## Phase 5 — first consumer: jaci CL spread

`capabilities/commercial_lending/template.py` becomes a thin adapter: `spread_template.yaml` →
`OutputTemplate` (locators `("is"|"bs"|"cf", key)` and `("m", metric_key, fmt)` map to
`TemplateField.key` + `derivation` + `unit` directly); `spreader_template_trace()` becomes
`FilledTemplate` → the existing trace dict, so nothing downstream changes shape.

**Gate:** `tests/unit/test_rb_reference_case.py` must reproduce `_RB_LTM_EXPECTED` at the pack's
`ltm_reproduction_tolerance` **through the new agent**, with `cit_ebitda == 11810` still holding.
That is the MVP exit criterion and the only acceptance gate that matters here. Note the RB template
is currently *"deliberately not wired into `template.py`'s YETI-shaped render pipeline"* — this phase
is where that changes, so expect the wiring to be the real work.

**Then generalize outward, deliberately non-financially** — the CRE property case summary or the KYC
file summary. A second finance consumer will not surface the finance assumptions still leaking into
the schema. This is the abstraction's only real test.

---

## Sequencing

| Phase | Depends on | Gate |
|---|---|---|
| 1 `OutputTemplate` | `_TieredRegistry` extracted; `agents/adjudication/` landed or stashed | YAML round-trip; invalid `derivation` rejected at load; P10 marker present |
| 2 `TemplateFillAgent` | 1 | zero model calls when the pre-pass resolves everything; completeness invariant asserted; trace mode map supplied |
| 3 induction + CLI | 1 | Excel formula → `derivation`; unvalidated draft refused at publish |
| 4 skills overlay | 2 | tier ordering + shadow refusal; `--dry-run` names the applied skill |
| 5 jaci adapter | 2, 4 | RB reference case passes through the new agent |

Phases 1-2 are load-bearing. Phase 3 is what makes it sellable and is Wave 4b's delivery. Phase 4 is
what makes it survive the tenth customer — which is, per the Builder/Pack Studio paradigm doc's own
test, *"whether the tenth one is boring to build."*

---

## Risks

**Scope creep into a spreading engine.** `OutputTemplate` must stay dumb. Period construction, source
precedence, LTM roll-forward, assurance ranking all live in `jazzx_sdk.finance.periods` and belong to
the finance pack. The test is Phase 5's second consumer: if it can't be non-financial, the
abstraction leaked.

**The `Skill` overload.** Two consumers with different semantics on one model is the right trade, but
the docstring must say which consumer honors which field, and `ProfileRegistry.validate()` should
warn when a skill carrying `applies_to` is allow-listed on an `InteractiveAgentSpec` that will ignore
it. Silent no-ops in a governance registry are how drift starts.

**Capability ahead of demand.** Until Phase 5 lands there is no consumer. P10 makes that legitimate —
but only if the module is exported, marked with what it waits on, and fails with a typed error rather
than silently. Without the marker the next audit reads it as dead code.
