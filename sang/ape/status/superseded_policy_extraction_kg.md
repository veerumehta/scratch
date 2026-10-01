# Policy documents through the KG pipeline

**Question asked:** if jaci adds a scenario that takes several policy documents and runs them
through a CORTEX-equivalent pipeline to extract rules and relationships, what has to change in
`fabric.graph`, in `KGAgent`, and in the policy extraction pipeline?

**Short answer:** less than expected in the model layer, because the output contract already
exists and round-trips; more than expected in one narrow place, because `Proposal` is typed to
vocabulary and cannot carry a rule at all. Everything below is verified against the code on
`kg-2.5.0`, not inferred from the roadmap.

---

## 0. Verified starting state

| thing | state | evidence |
|---|---|---|
| `build_vocabulary_pipeline()` | ships | ingest → emit → observe → propose → decide → merge → finalize |
| `KGAgent` | ships | observe / propose / decide / merge / adopt + `StateMachine` |
| `Policy` / `Rule` / `Condition` | ships | 7 registered condition kinds |
| `load_policies(path)` | ships | YAML → `Policy`, "the declarative alternative to hand-built `Policy(...)` literals" |
| `DefaultPolicyExpert.from_policy_dir()` | ships | "a pack whose rules are entirely in YAML gets a working PolicyExpert with no Python" |
| rule extraction from documents | **does not exist** | jaci's `extract_policy.py` does checklist + playbook by regex; its own docstring: *"policy-with-rules is author-assisted"* |
| `Proposal` carrying a rule | **does not exist** | `kind: Literal["concept", "relationship"]` |

### Round-trip: verified clean

The pipeline's output contract is "emit YAML that `load_policies` validates", so it depends on
writing what it can read back. Checked against jaci's real authored packs rather than a
constructed fixture:

```
ci-spread-core/policies/conventions.yaml       5 policies   9 rules  OK
ci-spread-core/policies/core.yaml              1 policy     2 rules  OK
clinical-intake-core/policies/core.yaml        2 policies   8 rules  OK
dscr_core/policies/eligibility.yaml            1 policy    41 rules  OK
                                               5/5 files round-trip cleanly
```

`Policy → model_dump(mode="json", exclude_none=True) → YAML → load_policies` returns objects that
compare equal field-for-field. **Proven for 4 of the 7 condition kinds** — `expression` (43),
`matrix` (6), `ratio` (2), `all_of` (1), plus 8 unconditional rules. `natural_language`, `dsl` and
`any_of` are **not** covered by any authored pack, so they are untested rather than known-good, and
`natural_language` is the one the extraction path would lean on hardest. Cover it before relying on
it.

### Two defects found while checking

**1. `load_policies` returns `[]` for a non-policy YAML instead of refusing.** `checklist_ci.yaml`
— which is what jaci's *current* extractor emits — has top-level keys
`asset_id / kind / title / description / provenance / sections`. It is not policy-shaped, and the
loader silently yields nothing.

**2. Consequently `from_policy_dir` silently skips it.** Pointed at
`ci-spread-core/policies/`, it loads 6 policies and contributes 0 from the checklist, with no
warning. This is a live trap for exactly the design proposed here: extraction writes into
`policy/`, the expert globs `policy/*.yaml`, and a malformed or wrong-shaped emission disappears
without a sound. A file that parses as YAML but yields no policies should be a `Refusal`, not an
empty list.

---

## 1. `fabric.graph`

**The blocker.** `Proposal.kind` is `Literal["concept", "relationship"]` with `concept` /
`relationship` as the only payload slots. Widening it to `"rule"` with a `rule: Rule | None` slot
makes the entire existing lifecycle — admission thresholds, the persisted `ProposalStore`, the
review surface over the queue, the audit trail, `proposal_lifecycle` — apply to rules unchanged.
This is the highest-leverage change and most of the rest is downstream of it.

**Provenance is too weak for policy.** `Triple.source` is a bare string plus a `source_text`
excerpt. `RuleOutcome.citations` is already typed `list[SourceCoordinate]`, and 2.4.8 carried typed
locators (`ChunkLocator`, `ConversionRegion`, `PageLocator`) from conversion through extraction. A
rule that cannot name the clause it came from is not auditable, which for regulatory content is the
entire point. Carry `SourceCoordinate` on the assertion, not a filename.

**Merge has one target.** `KGAgent.merge` produces a `Vocabulary`. Accepted rule proposals need to
land as policy YAML instead. Either a second merge target or a generalised "merge accepted into X".

**Contradiction needs a policy-aware sibling, not a replacement.** `fabric.graph.case.Contradiction`
compares *assertions*. Two **rules** conflict differently — by precedence — and `PolicyType`
(regulatory / institutional / operational) and `PolicyScope` (institution / product / deal) already
encode the narrowing ladder. Reconcile with the existing type rather than growing a third
disagreement vocabulary; the deferred-patterns note made the same call about `CheckResult` and
cross-system `MISMATCH`.

---

## 2. `KGAgent`

`propose` is deterministic from the accumulator; `decide` is async and LLM-backed. For a vocabulary,
a proposal is a *name*. For a rule, **a proposal is only useful if `get_condition_evaluator(kind)`
can actually evaluate it** — that, not the text extraction, is the hard part.

**Recommended staging: extract as `natural_language`, then promote.** Make promotion to a
deterministic kind (`expression`, `ratio`, `matrix`) its own reviewable transition once thresholds
are identified, rather than forcing a brittle one-shot parse into an expression. This gives a rule a
legible maturity ladder, matches how a person actually reads a policy document, and means a
half-understood rule degrades to "stochastic but stated" instead of to garbage. It also fits the
existing `stochastic` flag on the evaluator protocol.

`adopt(vocabulary)` needs a policy counterpart. And the four capabilities
(construct / ground / assert / check) need a decision: rule extraction is best read as a
**specialisation of assert** — a rule is an assertion about obligation — rather than a fifth
capability.

---

## 3. The extraction pipeline

Belongs in japes as `build_policy_pipeline()`, mirroring the vocabulary one, **not** as another jaci
script. Two steps genuinely differ:

- **Segment by clause, not page.** Rule boundaries are structural (§ numbering, "must" / "shall");
  the existing splitter is page-oriented.
- **Lint before finalize — this is what ties the two arcs together.** `lint_pack`'s
  `unreachable_input` check already catches this exact failure: it found `FCCR` reading `taxes`
  when the ontology declares `tax_expense`. An extracted rule whose condition reads a field the
  pack's vocabulary does not supply is that same bug, arriving automatically instead of by hand.
  **Policy extraction should lint against the vocabulary the KG work builds, and refuse rules that
  cannot resolve.** This is the argument for doing it in japes at all: the two halves only close the
  loop if they live in the same place.

**What "several documents" adds** is precisely what the KG machinery exists for: agreement across
documents (`FrequencyAccumulator`), conflict (`Contradiction`), and precedence
(`PolicyType` / `PolicyScope`). A single-document extractor would need none of it.

**The missing hop is in the manifest, not the model.** `Pack.policy_registry` resolves
`manifest["policies"]["registry"]` through `_resolve(ref)` — a dotted path into *consumer* Python
(`jaci.pack.policy_registry.RULE_INDEX` is the live example). `manifest_loader.policies()` returns
whatever dict the pack declared, shape undefined. Nothing lets a manifest point at a policy
*directory*, though the loader that would consume one already works. Teaching the manifest
`policies: {dir: policy/}` — and having `Pack.policy_registry` build via `from_policy_dir` when it
is set — is small, and is the same code-as-config move as the rest of the collapse roadmap.

---

## 4. Is a Proposal always about a Policy? No — and the boundary matters

It is **not** the case that `Proposal` generalises to "anything the KG is unsure about". The
distinction that governs it:

> **A Proposal changes what is true for every future case. A case-level finding changes what is
> true for one case.**

`Vocabulary` is the type level; `CaseGraph` is the instance level. Both vocabulary concepts and
policy rules are **durable, cross-case artifacts** that outlive any one transaction and therefore
need curation, admission thresholds, and an approval queue with an audit trail. That is what
`Proposal` is for, and why extending it to rules is coherent.

**A loan's own data graph is a different lifecycle entirely.** You do not "curate" a borrower's NOI
into a shared artifact — you assert it with evidence, or you refuse. Nothing about that case
survives to the next one. The machinery for it already exists and is *not* proposal-shaped:

| case-level concern | mechanism | not |
|---|---|---|
| is this value trustworthy | `Assertion.confidence`, `AdmissionPolicy` / `admit` | a proposal |
| two documents disagree | `Contradiction` (`fabric.graph.case`), `ContradictionReport` | a proposal |
| what is missing | `Coverage` | a proposal |
| cannot be determined | typed `Refusal` | a proposal |
| a human must decide | **`jazzx_sdk.agents.adjudication`** (ships: agent, planner, partition, segment, impact, workspace) | a proposal |

Conflating the two would be an active bug, not just a modelling smudge: accepting a "proposal"
whose payload is one loan's income would mutate a shared artifact on the strength of a single
case. The queue's accept action is a schema/policy write; case facts must never reach it.

**Where the two legitimately touch** is the promotion path, and it is worth naming because it looks
like the same thing and is not. A pattern observed *across many cases* — a predicate the corpus
keeps asserting, a threshold three documents agree on — is exactly what `FrequencyAccumulator`
turns into a proposal. So evidence flows case graph → accumulator → proposal, but **an individual
case assertion never becomes a proposal on its own**. The accumulator crossing a threshold is the
boundary, and it is already the mechanism that enforces it.

So: for a loan's transaction graph, the equivalent of "propose" is **adjudicate**, and that chassis
is built. The right question for a loan scenario is not "where are its proposals" but "is its
`Coverage` complete, are its `Contradiction`s resolved, and what needs adjudication".

---

## 5. Sizing and order

| step | effort | note |
|---|---|---|
| `Proposal` widened to rules | small | unlocks the whole existing lifecycle |
| `load_policies` refuses non-policy YAML | small | fixes a live silent-skip |
| `natural_language` / `dsl` / `any_of` round-trip cover | small | closes the untested third |
| manifest `policies: {dir:}` hop | small | code-as-config, already has its loader |
| `SourceCoordinate` on assertions | medium | touches emit + grounding |
| `build_policy_pipeline` + clause segmentation | medium | mirrors an existing shape |
| policy-aware contradiction / precedence | medium | reuse `PolicyType`/`PolicyScope`, do not rebuild |
| condition promotion (NL → deterministic) | large | the genuinely new design |

**Suggested first cut:** `Proposal` + the two small loader fixes + a `natural_language`-only
pipeline ending at the lint gate. That is a demonstrable document → rule → pack path with an
audit trail, and it defers the one genuinely large design (condition promotion) until the cheap
half has proven the shape.
