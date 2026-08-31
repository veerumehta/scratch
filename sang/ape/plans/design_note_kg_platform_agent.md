# Graph-shaped knowledge in japes v2

What the platform needs so that a **pack can be constructed** from a domain's own documents, and so
that **policy-governed, knowledge-intensive execution** in a regulated industry can be grounded,
cited and checked.

Written from source across k9, macer, cortex-suite and japes, plus the artifacts k9 and macer
exchange today. Nothing here has been implemented.

---

## The aim, and what the three PoCs are for

k9, cortex-suite and **macer's `kg` branch** are proofs of concept whose specific use cases may be
discarded entirely. They are read here as *evidence about which capabilities a platform needs* — not
as requirements to satisfy, not as codebases to consolidate. Where a PoC's shape and the platform's
shape disagree, the platform wins and the PoC changes or goes away.

**macer itself is in production**; only its `kg` branch is not. That distinction matters for how
freely its graph work can be reshaped (freely) versus the rest of it (not).

**This is a second pass, not a first.** These three repos have been analysed before, and a good deal
of japes' existing graph machinery already came from them — `Triple` carrying `confidence`,
`source`, `section`, `source_text` and `chunk_label`, `merge_subjects`, `format_triples_for_prompt`,
`KGStore` itself. So japes' graph layer is not a neutral baseline these PoCs sit above; it is the
*storage-level* result of an earlier absorption. What is proposed here is the next level up — the
lifecycle and admission machinery that was left out the first time.

The two things being built for are:

1. **Pack Studio — domain construction.** A pack is a domain: its concepts, relationships, policies,
   playbooks, schemas and skills. Today a pack manifest already declares an ontology
   (`ontology: {name, schema_path}`) and `PackLoader` registers it into fabric — but it arrives
   **hand-authored as a JSON file**. Deriving it from the domain's own documents, with curation, is
   the next step of the pack-author collapse that already took policies and evidence types from code
   into YAML.
2. **Execution in regulated, knowledge-intensive settings.** Grounded in the domain's vocabulary,
   asserting case facts with provenance, and checkable against policy with citations.

Everything below serves one of those two. The PoCs appear as evidence for specific claims.

## The four capabilities

| | What it does | Serves |
|---|---|---|
| **Construct** | derive a domain vocabulary from its documents, with human (or judged) curation | Studio |
| **Ground** | put that vocabulary in front of the model, as context and as a queryable tool | execution |
| **Assert** | record case facts as evidence with provenance back to a page and clause | execution |
| **Check** | evaluate assertions against policy, producing citable findings and contradictions | execution |

Each PoC did a slice, which is why none of them is the design: k9 did **construct**; macer did
**ground** and **assert**; cortex did **construct** for policy, plus a comparison layer that is a
special case of **check**.

**Check** is where regulated industries actually pay. An instance graph plus a policy graph plus an
evaluation is "this facility breaches covenant 6.1, here is the clause" — and japes already has most
of that half (`fabric.canonical.policy`, `ratio_evaluator`, `PolicyExpert`, and the locators just
landed). It is named here for completeness rather than because it needs new graph machinery.

## Two objects, not one

The split that makes the rest coherent:

| | **Schema graph** (the vocabulary) | **Instance graph** (the case) |
|---|---|---|
| Holds | concepts and relationships | assertions about one subject |
| Belongs to | a **pack** — it is a pack asset | a **case** — it is evidence |
| Lifecycle | a released artifact: versioned, reviewed, deployed, rolled back | provenance, confidence, refusal |
| japes shape | `AgentRelease` + `closure.py` + `GuidanceLifecycle`; declared in the pack manifest already | `CanonicalEvidenceObject`, `SourceCoordinate`, `Confidence`, `Refusal` |

japes has both shapes already, in different modules, with nothing binding graph work to either. An
ontology version is a release with a digest over a resolved closure — `closure.py` walks a reference
graph to a fixed point and digests it, which is exactly an ontology's shape. A triple is evidence
with a locator.

*Evidence from the PoCs:* k9 optimised for the schema graph, macer for the instance graph, cortex
collapsed them. Three independent efforts producing three shapes is the signal that the two objects
were never named.

## Construction is an admission lifecycle

A concept entering a pack's vocabulary is a governed act: it can be proposed, matched against what
exists, found to conflict, admitted, or refused. That is the same shape `DocumentAgent` applies to
extracted fields, and it has no home today.

**States: `proposed → accepted → merged`, plus `rejected`.** Several transitions reach `accepted`,
and the transition — not a separate state — is what records how:

| Admission policy | Trigger | Guard |
|---|---|---|
| Studio reviewer approves | `human` / reviewer | — |
| Seen often enough to be real | `system` | ≥N occurrences across ≥M sources |
| Judge model | `system` | verdict above a threshold |
| Trusted import | `system` | none |

One machine over `jazzx_sdk.statemachine`, transitions supplied as policy. `GUIDANCE_LIFECYCLE` is
the working precedent (`draft → approved → deployed`, with `discard` / `revise` / `deactivate`).

*Evidence from the PoCs:* k9's `ProposalStatus` is `PENDING | ACCEPTED | REJECTED | AUTO_ACCEPTED |
APPROVED`. Three of those are not states — they are one state reached three ways, with the trigger
smeared into the state name because there was nowhere to record it. `Transition` already carries
`trigger_type`, `actor_class` and `guard`. The four policies above are then a configuration, not
four implementations.

**Category (matched / new / conflicting) is a field, not a state.** It says what the proposal *is*,
not where it is in its life. Conflating the two is what produced a five-value enum.

## The accumulator

Some admission policies are only answerable **across a corpus**: "this relationship appears in
enough documents to be real" cannot be decided while looking at one. So construction is
**run-scoped**, with a pluggable accumulator:

- **consumes** assertions as they are produced across a run
- **groups** them by candidate concept
- **emits** proposals carrying occurrence evidence — count, distinct sources, which documents

That contract is what lets frequency, human approval and a judge all be guards over one machine,
because each reads the same evidence. It is also the piece with the least precedent in japes.

*Evidence from the PoCs:* macer's promotion set records `document_source: "MACER Discovery —
L1440721, L1440854, …"` across six loans, with `document_type: "predicate_discovery"`. The source is
a corpus, not a document; a document-scoped design could not have produced it.

### Occurrence evidence is first-class

Each promoted proposal today carries a `macer_metadata` bag holding `count`, `sources`,
`source_list`, `promoted_from`, `promoted_date` — all of it real provenance, in a key named after
the producing system, because the schema had nowhere to put it.

The platform types already cover this: `SourceCoordinate` for which document, `Confidence` for the
score, count and distinct sources as first-class accumulator evidence, a reasoning string as the
audit trail. **No metadata bag, and no platform equivalent of one** — a proposal is evidence-backed
or it is not admissible.

## Grounding, and the cost lever

The vocabulary reaches the model two ways, and both stay first-class:

- **as context** — compact prompt text describing what to look for
- **as a tool** — a graph the model queries mid-reasoning

japes has both halves (`format_triples_for_prompt`, the MCP/tool registry) and pairs neither.

This is not a convenience. The question behind it is **whether knowledge crafted separately from the
documents lets a cheaper model reach a frontier model's answer** — a cost lever, and a real one.

### The result so far, and what it demands of the design

The experiment has not yet produced a sufficient jump, and **the reason is a design constraint, not
a tuning problem**:

> KG extraction is a **lossy compression** of the documents. When the graph stood in for the source,
> the reasoner's confidence that *all relevant loan data was available* fell — and approvals came
> back **conditional** rather than approved.

Three things follow, and they are the most useful findings in this note:

1. **The graph must be additive, not substitutive.** A vocabulary or graph offered *alongside* the
   documents is a different intervention from one offered *instead of* them. The tool path does this
   naturally — the model still reads the source and queries the graph for what is hard to see across
   documents — while a context-only path tempts substitution to save tokens, which is exactly the
   trade that failed.
2. **Coverage has to be reportable.** A graph needs to say what it does *not* cover, at the graph
   level and not only per-triple. A reasoner that cannot tell a sparse graph from a complete one is
   right to lose confidence, and right to hedge.
3. **The metric is the decision, not the triples.** Precision and recall over extracted triples
   would have scored this experiment as a success. What actually regressed was downstream decision
   confidence — approvals turning conditional. Any evaluation of this capability has to score the
   decision, which japes' scorer stack can do and a graph-quality metric cannot.

That third point generalises past graphs: it is the shape of every "compress the context to save
cost" intervention.

The experiments will restart, and this work should help them — but the two can also grow separately,
so nothing here should be designed *around* that use case.

It also implies a measurable requirement either way: the agent must record **which path produced a
given assertion** — context or tool — or the comparison cannot be run.

## What the agent owns — and what it does not

**Assertion is `DocumentAgent`.** It already ingests, classifies, extracts under an admission floor
with attestation override, and emits an **ontology-scoped** typed object with provenance —
`emit_entity` takes an `ontology_id` today. Emitting triples is an extension of the emit step. No
second chassis.

**KGAgent owns construction**: the loop that turns a domain's documents into a pack's vocabulary.

1. **Propose** concepts and relationships, against the pack's current vocabulary when there is one
2. **Categorise** — matched / new / conflicting
3. **Accumulate** across the run
4. **Admit / refuse / attest** under the pack's admission policy
5. **Merge** accepted proposals into a new version of the pack's schema graph

That is the Studio's authoring engine. Its admission question — *should this enter the domain's
vocabulary* — has no home today, which is what earns it a chassis; assertion's question already has
one.

### One requirement that follows from the two objects

**Assertions must carry entity types.** A triple whose subject and object are proper nouns — a
borrower's name, a dollar amount — says nothing generalisable, so it can propose a *relationship*
but never a *concept*. Subject and object each need a type reference: an ontology class, or an
explicit `literal` / `instance` marker.

*Evidence from the PoCs:* macer's promotion set contains 30 relationship proposals and **zero**
entity proposals, for exactly this reason. My first reading was that concept and predicate discovery
are separate operations; that was wrong. The extractor was well placed to tag types — it already had
the ontology in context — and simply was not asked to.

## What japes already has

Not to be rebuilt:

- **Versioning** → `AgentRelease` + `closure.py`. A pack's ontology version is a release over its own
  closure.
- **Lifecycle** → `jazzx_sdk.statemachine`, with `GUIDANCE_LIFECYCLE` as precedent.
- **Admission** → `admission_floor`, `attestations` as the human override, `Refusal` with a reason
  code, `Confidence` with tiers.
- **Judging** → a `Scorer`. Match/conflict verdicts are `score(expected, actual) -> ScorerResult`.
- **Convergence loops** → `evaluation/optimization.py` is already score → propose → keep-best.
- **Set operations over versions** → the matcher-pluggable diff (see the cortex note).
- **Storage** → `fabric.graph.KGStore` for triples and ontologies; `fabric.entities` for typed
  objects.
- **Pack wiring** → the manifest already declares an ontology and the loader already registers it.

## Where the PoCs' own logic stands

Read as evidence, three modules are worth reading again if they are built on rather than replaced —
but none is a requirement:

- `refinement_engine.py` (k9, 1,020 lines): **zero domain terms, zero filesystem references** — the
  most portable thing across the three, and the same score/propose/keep-best shape as
  `optimization.py`.
- `proposal_manager.py` (k9, 1,246 lines, zero domain terms): the lifecycle above, hand-rolled, with
  storage hardcoded to `json.dump` under `data/ontologies`.
- `knowledge_graph_manager.py` (k9, 1,184 lines): mixed — platform logic, a Plotly surface, and
  persistence that overlaps `KGStore` directly.

Everything domain-specific — mortgage vocabularies, maturity thresholds, the JTBD and compliance
framings, the HTML visualisers, both k9 conductors, cortex's behaviour and domain taxonomies — stays
out, or becomes pack content registered the way signal tags now are.

## Sequence

1. **Name the two objects** and bind them to the release and evidence shapes. Everything assumes it.
2. **The proposal state machine**, transitions supplied as policy.
3. **The accumulator contract** — least precedent, decides the agent's boundary.
4. **KGAgent** over 1–3, reusing `DocumentAgent`'s admission machinery.
5. **Assertion typing** on `DocumentAgent`'s emit path, so construction can be fed by execution.
6. **Grounding pair** — vocabulary as context and as tool, with attribution of which produced what.

Studio needs 1–4. Execution needs 5–6. They are independent after step 1.

## Open questions

- **Does a convergence loop generalise, or is `optimization.py` enough?** Same shape over a different
  subject. A loop abstracted over "any subject" reads well and can serve neither case.
- **Is refusing a proposal the same object as refusing a field?** Same shape at least; whether one
  `Refusal` taxonomy covers both affects how much is shared.
- **An assertion that contradicts the vocabulary** is a data problem, not a vocabulary one — distinct
  from a conflicting *proposal*. Nothing handles it, and it arrives with the first real corpus.
- **How is coverage represented?** Following from the lossy-compression finding: a graph needs to
  report what it does not cover, and there is no precedent for that shape in japes. Per-triple
  confidence exists; graph-level coverage does not.

## Settled

- **The vocabulary versions with the pack.** Not independently, and a pack does not pin a separate
  vocabulary version. One release, one closure, one thing to roll back — which also removes the
  question of what happens when a pack and its vocabulary disagree about which version is current.

## Not verified

- Whether `PackLoader`'s ontology registration is exercised by any live pack, or only declared.
- Whether the pack manifest's `ontology` key can carry a version reference without a schema change.
- How much of the Studio's authoring surface already exists elsewhere and would collide with this.
