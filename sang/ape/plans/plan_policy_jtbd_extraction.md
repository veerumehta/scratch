# JTBD extraction: a second representation out of policy_extract, reviewed in Plato, stored in the pack

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-24. Written against japes `5534f5e` on `v2.5.4`, and policy-workbench at its
local checkout.

> **Progress (v2.5.4, local, unpushed):** steps 1-4 built (`procedure` kind + evaluator, `Segmenter`,
> `policy_jtbd` segmenter/extractor/template + `scripts/policy_jtbd_extract.py`, `rule_merge`). Step 5's
> SDK half built: `Rule.replaces`, `Policy.suppresses`, field-claiming retired, `dangling_relation`
> lint; jaci CRE/CI overlays migrated (uncommitted in jaci, which is on `dev`). Open: dscr-core split
> (content scope question), live smoke on Acra docs, steps 6-11.

Prior art read first: `policy-ir-abstraction.md` (P8 shipped: open `Condition` union,
`natural_language` kind), `plan_policy_extraction_kg.md` (why `Proposal(kind="rule")` exists and
the lint gate), `plan_plato_authoring.md` (draft to immutable version). Nothing here overturns them.

## 0. Correcting the premise

`policy_extract.py` does **not** produce a knowledge graph. It produces `Proposal(kind="rule")`
carrying `Rule`s whose condition is `NaturalLanguageCondition`, assembled into a DRAFT `Policy`, and
lints them against the pack's vocabulary. It borrows the KG *lifecycle* (`fabric.graph.proposal`,
`admit`, `ProposalStore`); the KG *representation* is `vocabulary_build.py`.

So a JTBD is closer to what exists than it looks: a `natural_language` rule is already a one-line
JTBD, and `NaturalLanguageCondition`'s docstring says so. What is missing is the richer shape,
a real extractor, a way to write accepted rules into a pack, and a review surface.

Also verified: nothing calls `run_policy_extract` outside tests. jaci's `scripts/extract_policy.py`
(regex, writes YAML into the pack directly) is still the live path. Room to reshape freely.

## 1. What "multiple representations" should mean

Not variant copies of `policy_extract.py`. The governed spine (ingest, propose, admit, lint,
finalize, store) is identical across representations; what varies is two seams:

| seam | today | varies by representation |
|---|---|---|
| **Segmenter**: document(s) to units of work | `clause_segments` (regex, clause-level) | JTBD is section-level and synthesizes across clauses (a planner, as in policy-workbench) |
| **Extractor**: unit to `RuleCandidate`s | `ObligationExtractor` protocol, `ModalClauseExtractor` floor | JTBD extractor emits a `procedure` rule; "code" emits `expression`/`dsl`/`ratio` |

| representation | what it emits | status |
|---|---|---|
| KG / vocabulary | `Proposal(kind=concept/relationship)` | ships (`vocabulary_build`) |
| obligation (today) | `natural_language` rule per clause | ships, floor extractor only |
| **JTBD** | `procedure` rule per job (this plan) | new |
| code | `python` rule generated from a JTBD or clause (§2b); `expression` / `dsl` / `ratio` where the clause fits them | not built |

The representation is a per-rule property (`condition.kind`), which is what lets one `Policy` mix
them and lets adjudication partition by cost. Keep it there rather than inventing a policy-level
"representation" type.

## 2. What policy-workbench does, and what to take

Forging: planner LLM produces a plain-text plan (sections, ~8-10 JTBDs each, regex-parsed);
up to 4 parallel writer agents (claude-agent-sdk / openai-agents) write tagged Markdown files into
a staging dir via an MCP `write_file` tool; an LLM evaluator flags ambiguous sentences. Review is
per **file** accept/reject of staged changes, then a PR-style proposal (diff, comments, publish,
rollback). Published set goes to KH as a JTBDSet; MACER executes it.

**Take:** planner then parallel writers; staging with accept/reject; ambiguity evaluator as a
review aid; the four-outcome vocabulary (Pass / Conditional / Fail / Not Applicable).

**Improve, do not copy:**

- **No source provenance there.** A JTBD cannot name the span it came from. We carry
  `SourceCoordinate` per rule; this is the audit property, and the extractor must return it.
- **Program variants as sentinel blocks** (`<COMMON>`, `<FNMA>`, `NO_CHANGE`, merged by an LLM at
  runtime). `policy-ir-abstraction.md` §1 already calls this non-deterministic. We express a
  variant as a program-scoped policy whose rules each declare their relation to the base
  (§2a). Deterministic selection, no merge call.
- **Mortgage hardcoding** (investor tags, 11 section types, roles, four-step outline in prompts).
  All of it becomes pack-supplied: the JTBD template and section taxonomy are a pack skill/prompt,
  so patient intake is a different pack, not a different pipeline.
- **Metric blocks** (`<metric>` with `indicator_context` prose). These are `ratio`/`expression`
  rule candidates, emitted as separate rules with `reads` naming vocabulary fields, so the lint gate
  bites on them.
- **Per-file review granularity.** We review per rule (proposal), which the `ProposalStore` and
  `admit` already support.

## 2a. Policy variation: one axis, several delta kinds

Checked against Acra's two consolidations (`~/Docs/ArcaL/Acra_DSCR_{Standard,Platinum_Select}_
Consolidated_Guidelines_v1_0.docx`, Platinum §11.3 and Appendix B) and the SDK's overlay path
(`experts/policy/default.py` `resolve` / `check_compliance`, `pack/pack.py` scope split).

**Program variation is not a separate thing from policy variation.** A program is one level of the
scope ladder `PolicyScope` already has (institution, product, deal); FNMA/FHA in policy-workbench
and Standard/Platinum at Acra are the same axis. One mechanism for "which rulebook applies".

**Structure at Acra is siblings over a shared base, not base plus overlay.** Each program is its
Program Summary over the Seller's Guide excerpt, and "matrices control where cited, the full Guide
controls over the excerpt". Platinum is not Standard-tightened: its qualifying rent ("greater of
market or actual") is *looser* than Standard's §5.32 lesser-of. Modelling Platinum as a delta on
Standard would encode that backwards. So: `seller_guide` (institution scope, shared), plus
`standard` and `platinum_select` (product scope), each relating to the guide, not to each other.

**What the delta has to express.** The §11.3 table and Appendix B contain six kinds:

| kind | Acra example | mechanism |
|---|---|---|
| same rule, different number | min FICO 600 vs 700; max loan $3M vs $2M; CLTV grid; ARM margins | one `PolicyProfile` per program; rule shared. Exists. |
| same rule, different set | citizenship (5 types vs 2); property types; ineligible states | profile-supplied set, `IN` operator. Exists. |
| added | Correspondent DSCR >= 1.2; cash-out needs current lease | program rule with no base counterpart. Exists. |
| replaced | mortgage history tiered to 0x90x12 vs flat 0x30x12; PCE tiers vs 48 months | program rule that names the base rule it replaces. **Missing.** |
| suppressed | Guide §3.13 FTHB allowance, §3.10 foreign nationals, §10.17 vacant refi: inapplicable on Platinum | explicit "base rule X does not apply here, because Y". **Missing.** |
| tightened / composed | declining market -5%; loan-size caps; IO 75% | caps compose by `min()` across every applicable rule, base and program. **Missing in SDK** (jaci `compose_caps` does it by hand). |

Plus one state that is not a delta: **unaddressed**. Platinum's rule is "silence is neither
permission nor prohibition" (§11.2); 22 open questions (Appendix A). A base rule a program neither
restates nor excludes must be visibly "inherited, unconfirmed", not silently in force.

**The current SDK override is wrong for two of the six.** Precedence today is *field-claiming*:
once a higher-precedence policy has a rule reading `cltv_pct`, every lower-precedence rule reading
`cltv_pct` is skipped. That is replace-by-field, implicit:
- **Tightening breaks.** A Platinum declining-market cap on `cltv_pct` would switch off the Guide's
  and matrix's `cltv_pct` rules instead of composing with them, in the permissive direction.
- **Replace is too coarse.** It suppresses every base rule sharing a field, not the one being
  replaced; nothing records which base rule was meant.

**Proposal.** Keep the scope ladder and `overlay_map`; make the relation explicit per rule:

```yaml
- rule_id: PLAT-6.6
  relation: {replaces: GUIDE-4.15-HOUSING-TIERS}   # or suppresses: [...], reason: "..."
- rule_id: PLAT-1.17
  relation: {composes: max_cltv}                   # joins the min() over the max_cltv family
```

- `relation` absent means **adds** (the default, matches today for rules on new fields).
- `replaces` / `suppresses` are by rule id and lint-checked (the target must exist in a lower
  scope). Suppression carries a reason and a citation; that is Appendix B as data.
- `composes: <family>` makes cap composition an SDK rule, not a jaci module; the binding rule is
  reported, as `compose_caps` does now.
- Field-claiming is retired, not kept alongside; two precedence mechanisms is the drift risk.
- Channel (Correspondent vs Wholesale), purpose and property type are **not** scope levels. They
  are in-program conditions, so they are `applicability` on a rule. A scope level is "which
  rulebook"; applicability is "which rules in it".
- "Unaddressed" is computed, not authored: base rules with no program rule relating to them, in a
  program whose policy declares `inherit: confirm`. Reported as an open question on the review
  surface.

**What it means for extraction.** Extracting a program document runs against its base: the JTBD
extractor is given the base policy and emits each program rule with its relation, and a
suppression list. That is exactly the work JazzX did by hand in the two consolidations (§11.3,
Appendix B), so those docs are the gold set for the extractor's first eval.

## 2b. Generated Python as a representation

Decided 2026-09-24: generating Python is allowed; how the product runs it is decided later. So
generation, storage, review and checking are built now, and execution is a seam.

- **`PythonCondition`** (`kind: python`): `source` (one module), `entrypoint` (a function of the
  case context returning a verdict and inputs), `reads`, `derived_from` (the rule id it formalizes,
  usually a `procedure`), and `cases` (context/expected-verdict pairs the generator wrote alongside).
- **`PythonExecutor` protocol**, resolved from context like the reasoning agent. The registered
  evaluator returns INDETERMINATE (`policy_not_activated`) when none is configured, so a pack
  carrying Python loads, lints and publishes everywhere and runs only where an executor is
  installed. Which executor ships (subprocess sandbox, a separate service, WASM) is the product
  decision this defers.
- **Checked at publish, without executing:** parses; one entrypoint with the declared signature;
  every name it reads from the context is in `reads`, and every `reads` field is in the pack
  vocabulary (the existing lint); no imports outside an allowlist; no `exec`/`eval`/`open`/dunder
  access. This is a static gate, not a sandbox, and says so. MACER's `exec()` sandbox had a
  documented escape; nothing here relies on in-process restriction.
- **Promotion is differential.** A generated rule is proposed beside the rule it formalizes, and
  review shows both verdicts on the generator's `cases` and on the pack's gold cases. It replaces
  (`Rule.replaces`) its source only when accepted, so the English rule stays the fallback and the
  audit anchor.
- Generation is one more extractor over the existing spine (`PythonExtractor`: rule in, candidate
  out), so proposal, admission, lint and review are unchanged.

## 3. The JTBD shape

**Recommendation: a new registered condition kind, `procedure`**, not new fields on `Rule` and not a
standalone `Jtbd` type (findings-are-canonical-decisions rule: no parallel type).

```python
class ProcedureCondition(BaseModel):
    kind: Literal["procedure"] = "procedure"
    purpose: str
    evidence_types: list[str]          # pack evidence_types refs, lintable; "Reference Documents"
    steps: list[str]                   # ordered instructions the LLM follows
    determinations: list[str] = []     # boolean predicates stated in prose ("Deterministic Validation Rules")
    outcomes: dict[str, str]           # Verdict name to its criterion text
    reads: list[str]                   # same contract as NaturalLanguageCondition
```

- `Rule.description` holds the one-line skill; `Rule.citations` + a typed coordinate hold
  provenance; `Rule.applicability` holds "does this job apply"; section is the owning `Policy`.
- Evaluator: `ProcedureEvaluator`, `stochastic=True`, `ExecutionKind.LIVE`, delegating to the same
  `ReasoningAgent` path `NaturalLanguageEvaluator` uses, with the steps/outcomes rendered into the
  prompt and the verdict mapped onto `Verdict`. `evidence_contract` returns `reads` plus
  `evidence_types`.
- Why not reuse `NaturalLanguageCondition` with a longer `text`: steps, evidence types and outcomes
  are what a reviewer edits and what lint can check. Flattening them into prose loses both.

Alternative considered: `Rule.parameters` as a dict. Rejected: untyped, `extra="ignore"`-style
invisibility (CLAUDE.md §7 precedent).

## 4. Pipeline

`build_policy_pipeline(representation=...)` keeps one spine; the representation picks the
segmenter and extractor. Concretely:

1. Add a `Segmenter` protocol next to `ObligationExtractor`; `clause_segments` becomes
   `ClauseSegmenter`. Add `PlannedSectionSegmenter`: one LLM call over the corpus returns sections
   plus the source coordinates each section draws on (structured output, not regex over a plan).
2. `JtbdExtractor(ObligationExtractor)`: per section, one LLM call with structured output
   returning `ProcedureCondition`s plus citations. Parallelism via the conductor, bounded by config.
   Uses `jazzx_sdk.tools.extract` / the SDK LLM layer, not claude-agent-sdk writers with a file
   tool; the pipeline owns persistence, the model only returns objects.
3. Template, section taxonomy and outcome wording come from the pack (`skills:` / prompt ref in the
   manifest). The SDK ships a neutral default.
4. Optional `evaluate_ambiguity` step (policy-workbench's evaluator) annotating proposals, not
   gating them.
5. Dedupe: `rule_id` is derived from section + normalized skill, so a re-run re-proposes the same
   id and the store remembers rejections (the existing property).
6. Lint unchanged, plus: `evidence_types` must exist in the pack.

Fix while there: the extractor currently gets no LLM context and `extract_step` swallows
exceptions silently; count skipped segments on `CorpusObligations`.

## 5. Storage in the pack

- **Format:** one policy YAML per extraction at `policies/<policy_id>.yaml`. Not a `jtbd/`
  subfolder: the manifest's `policies.dir` glob is not recursive, so a subfolder would publish and
  never load. `merge_rules_into_draft` reports reachability for this reason.
- **The missing hop:** "accepted rule proposals into draft files". Add `merge_rules(accepted,
  draft)` in `jazzx_sdk.pack` (sibling of `KGAgent.merge` for vocabulary): groups accepted rules by
  policy, renders YAML via `model_dump(mode="json", exclude_none=True)`, writes
  `pack_draft_file` rows through `DbPackDraftStore.write_file`. Publish stays the existing
  draft-to-immutable-version route. Nothing is enforced until publish.
- **Round-trip test first:** `natural_language` was never round-trip covered
  (`plan_policy_extraction_kg.md` §0); `procedure` must be, before anything writes it.
- Stays DRAFT on extraction; the Policy becomes ACTIVE only via the pack version's publish, not per
  rule.

## 6. The SDK owns authoring; Plato and policy-workbench are shells

Decided 2026-09-24: the heavy lifting lives in `jazzx_sdk`; Plato and policy-workbench supply
config, identity and a UI. Policy-workbench is then asked to switch to the SDK. This matches the
SDK adoption policy (japes provides, client owns) and the draft/inventory lifts already done.

**The SDK surface** (all host-free except the router factories, which are server tier):

| piece | state | where |
|---|---|---|
| extraction pipeline, segmenters, extractors, variation lint | new (§2a, §4) | `pipelines.policy_extract` |
| proposal store | ships (`DbProposalStore`) | `fabric.graph` |
| proposal review router, pluggable merge target | generalize `create_vocabulary_review_router` | `server` |
| extraction trigger router (upload docs, enqueue run, poll status) | new | `server` |
| pack draft store + publish to immutable version | ships (`DbPackDraftStore`, `draft_archive`) | `pack` |
| accepted rules into draft files | new (`merge_rules`, §5) | `pack` |
| review comments, anchored to a proposal or a draft file line | new store | `pack` |
| draft review state (draft, in_review, published) | planned in `plan_plato_authoring.md` §3 | `pack` |
| JTBDSet import (their existing content into `procedure` rules), export while MACER consumes it | new adapter | `pipelines` or `pack` |

**What stays in a shell:** the UI; identity (the routers take an actor resolver, as the review
router already does); deployment posture; which model (config, through the SDK LLM layer);
branding; anything mortgage-specific (their investor tags, section enum, four-step template become
*pack* content, not SDK or shell code).

**Their chat agents are replaced, not lifted:** the authoring chat runs on `pipelines.chat` +
`InteractiveAgent` (decided 2026-09-24). **OpenAI models only** for extraction and chat;
Anthropic support, if needed later, comes from the agent execution service rather than from this
work. So neither claude-agent-sdk nor `AnthropicNativeModel` is in scope, and their writers'
file-tool model goes away because the pipeline returns objects. Mapping of their router and five sub-agents:

| theirs | ours |
|---|---|
| intent router (`classify_intent.md`) | `structured_classifier_gate` |
| `policy_creator` (planner + file-writing writers) | tool that enqueues the extraction pipeline; escalate route, returns a run id |
| `policy_modifier` | tool that files a `Proposal` against an existing rule (edit, replace, suppress); never writes the draft |
| `policy_evaluator` | tool running the ambiguity step over a rule or a draft |
| `policy_advisor` / `general` | direct route, grounded on the pack's policies and source docs as knowledge sources |

The rule that holds this together: **chat writes only proposals.** Everything the agent changes
lands in the same review queue extraction fills, so there is one approval path, one audit trail,
and no agent-only write route (their `agent_staged_changes` becomes proposals). Agent spec,
prompts and tool bindings are pack or shell config, not SDK code.

**Deliberately not lifted:** their git content backend, membership tables, Lexical editor. Lifting to policy-workbench's full 32-table feature list is the failure
mode; lift what both shells need, and let a second real need pull in the rest.

**Proof it is thin:** every router factory mounts in a bare FastAPI app in its test, with no Plato
import (the vocabulary review tests already do this). Plato is the first shell; the switch ask to
policy-workbench goes out once Plato runs the full loop, since until a second shell adopts, "thin"
is an untested claim.

**Plato, concretely:**
1. Mount the review and extraction routers, gated by `_refuse_unless_author` like the draft routes.
2. Extraction runs on the queue, not in the request; a corpus run is minutes.
3. UI first cut in `packs.html`: proposals grouped by section; each card shows skill, steps,
   outcomes, the source excerpt and citation, the rule's relation to the base (§2a), lint findings,
   ambiguity notes, open questions; accept / reject / edit-then-accept; merge into draft; publish.
   The SPA (`plan_plato_authoring.md` §4) is the long-term home and should not block this.

**Policy-workbench, when it switches:** import its published JTBDSets into a pack (one-time), point
its forging at the SDK pipeline, back its review screens with the SDK routers, keep MACER fed via
the exporter until MACER reads `Policy` directly.

## 7. Runtime (for completeness, mostly exists)

`DefaultPolicyExpert.check_compliance` dispatches by kind, so a published `procedure` rule is
evaluated by `ProcedureEvaluator` against a case, and `agents/adjudication/segment.py` already
batches LIVE obligations MACER-style. Output is `RuleOutcome` per rule, which is the per-JTBD
finding MACER produces, with citations it does not have.

## 8. Order of work

1. `ProcedureCondition` + evaluator registration + YAML round-trip test. Small.
2. `Segmenter` protocol, `ClauseSegmenter` refactor (no behavior change, existing tests pass).
3. `PlannedSectionSegmenter` + `JtbdExtractor` + pack-supplied template; neutral default template.
   Gated live smoke on Acra's Platinum Select summary + Guide excerpt, the primary scenario.
4. `merge_rules` into a draft + round-trip through publish and `Pack.policy_registry`.
5. Variation (§2a): `relation` on `Rule`, `composes` families, retire field-claiming, lint.
   Proven on dscr-core split into guide + standard + platinum_select, scored against the two
   consolidations.
6. SDK routers (review, extraction trigger) + comments store; mounted bare in tests.
7. Authoring chat: the four tools (extract, propose-edit, evaluate, grounded answer) + classifier
   gate on `pipelines.chat`; spec as config.
8. Plato shell: mount, `packs.html` review panel with the chat beside it.
9. jaci: replace `scripts/extract_policy.py` usage for one pack.
10. JTBDSet import/export adapter; then the switch ask to policy-workbench.
11. `PythonCondition` + static publish check + `PythonExecutor` seam (no executor shipped) +
    `PythonExtractor`, with differential review against the source rule (§2b).
12. Later: `ProcedureEvaluator` quality eval against MACER findings on the same loan; promotion of
    metric rules to `ratio`; choose and ship a `PythonExecutor`.

## 9. Open decisions

- **`procedure` kind vs richer `NaturalLanguageCondition`** (§3). Recommend the new kind.
- **Variants** (§2a): decided 2026-09-24. Field-claiming is retired for explicit per-rule relations,
  and dscr-core is split into guide + standard + platinum_select as the proving ground.
- **Review UI in `packs.html` now vs wait for the SPA.** Recommend `packs.html` now.
- **Does extraction run in Plato's process or on the queue?** Recommend queue; a corpus run is
  minutes.
- **One draft per (tenant, pack)** means extraction and hand-editing share a draft. Acceptable for
  now; per-user drafts are already an open question in the authoring plan.

## 10. What would make this wrong

- If the policy-workbench team declines the switch, §6's router factories still serve Plato, but
  the JTBDSet adapter becomes a permanent sync path, not a migration bridge. Ask early.
- If their content has to stay git-backed (their `CONTENT_BACKEND=git`), the draft store needs a
  storage seam it does not have today; `DbPackDraftStore` is DB-only.
- If MACER cannot move off JTBDSet, the exporter is permanent and mortgage-shaped. Acceptable, but
  it then belongs in the mortgage pack, not the SDK.
