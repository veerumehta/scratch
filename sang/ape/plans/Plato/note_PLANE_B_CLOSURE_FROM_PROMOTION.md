# What `promotion.py` already knows about closure, and what Plane B has to match

Author: Virendra Mehta · 2026-08-24 · input to Plato Plane B / Phase 2

**Read against** `assistant` HEAD `616c752` (2026-08-21), `app/assistant/promotion.py`, 1117 lines.
Companion to `Plato_Service_Architecture_and_Build_Plan.md` §4 Plane B and
`plan_JAPES_PLATO_SERVICE.md` Phase 2 task 9, which says to read this file in full before designing
the publish path. This is that read, reduced to what changes Plato's design.

**Status of the source.** Not stagnant. Two fixes landed in the four days before this note
(`2bfd241`, `616c752`), both closing closure-completeness gaps found in production. That matters
more than the line count: every fix is a requirement Plato inherits, and the list is still growing.

---

## 1. The claim this note tests

The charter states Plane B is done when `promotion.py` can be **retired** against Plato rather than
coexisting with it, and that this is a better acceptance test than anything we would have invented.
It is. But the plan's summary of what to carry forward is one sentence:

> publish routes each part of a bundle to whichever service owns that asset kind (kernel for
> agents/tools/LLMs, Flowable for BPMN/DMN, KH for collections), with the assistant row created last
> so a partial failure is resumable.

That is true and it is not the hard part. The hard part is **what belongs in the bundle at all**,
and `promotion.py` has four answers Plato's `closure_digest` cannot reach by walking declared
references.

---

## 2. The closure is not the declared graph

Plato's Phase 2 task 4 says: *resolve, then freeze — manifest, profile, every skill, every
`spec_ref` child, the pack version, model pins.* Every item on that list is something an asset
**declares**. `promotion.py` learned the hard way that the declared graph is a subset.

### 2.1 A process references tools and agents by name, outside any declared list

`2bfd241`, verbatim:

> Service tasks and call activities can reference a tool or agent directly by name, independent of
> any agent's `tools`/`callable_agent_ids` list. Those refs were never resolved or bundled on
> export, so cross-instance import deployed the BPMN but never created what it actually calls at
> runtime.

A release that froze only the declared graph would pass every validation, produce a stable digest,
and deploy a process that fails on its first service task. **The digest would be reproducible and
wrong**, which is worse than unstable: a reproducible wrong digest is trusted.

**For Plato:** the closure walk has to include references reachable through *artifact content*, not
only through model fields. If a release carries a BPMN, the tools and agents that BPMN names are
part of its closure.

### 2.2 The reference graph is transitive, cyclic, and needs a fixed point

`expand_process_closure` walks `callActivity` → process and `decisionRef` → decision from a seed
set, as a fixed point over a visited set *"so cycles terminate"*. A process calls a process calls a
decision. One level of resolution is not resolution.

**For Plato:** `closure_digest` is over a transitively-closed graph with cycle handling, not a
one-level expansion of an asset's fields. The plan's insistence on an **explicitly ordered** graph
matters doubly here: a fixed-point walk over a set has no inherent order, so the ordering has to be
imposed at serialization or the digest is unstable across runs on identical input.

### 2.3 Some references cannot be resolved at all, and that must be loud

`bpmn_references` returns warnings rather than dropping what it cannot resolve:

> Only static attribute values are returned. Expression-valued references (for example
> `calledElement="${nextProcess}"`) cannot be resolved without running the process, so they are
> reported as warnings instead of being silently dropped.

This is the same discipline japes already applies elsewhere: `RatioCondition` refuses to invent a
threshold, `get_model_card` returns `None` rather than a fabricated card, `ControlKeys` no-ops
rather than guessing a canonical line.

**For Plato:** a release whose closure contains an unresolvable reference is a distinct outcome
from a complete one. It is neither a success nor an exception — it is the shape `Refusal` exists
for, and `jazzx_sdk.statemachine` already gives blocked-promotion a designed governance outcome
rather than a 500. **A release with unresolved references must not be promotable to production**,
which is the same rule the plan already states for floating external dependencies.

### 2.4 Identity is not consistent across the estate

`expand_process_closure`'s own docstring:

> Seeds are matched against the BPMN process id first and its `name` second, because
> `assistant_process` rows are not guaranteed to hold a flowable key: Builder Studio's create path
> stores the process *display name* in `process_id` and leaves `definition_key` empty.

So a stored reference may be a key or a display name, and resolution has to try both, then **refuse
on ambiguity** when a name matches more than one definition.

**For Plato:** this is a data-quality fact about what Studio has already written, and it survives
D2 either way. If Studio writes to Plato's API, the API needs a resolution rule for existing rows;
if Studio keeps its store, Plato reads those rows and needs the same rule. Either way, **the digest
must be computed over resolved identity**, or two releases naming the same process differently
produce different digests for identical content.

`616c752` adds a second instance: `{{TOOL_X}}` env aliases are resolved **at export time**, not
stored resolved. A frozen release that captured the alias rather than its resolution is not
reproducible across environments, which is precisely what a release is for.

---

## 3. What this changes in the plan

| Plan item | Change |
|---|---|
| Phase 2 task 3, `closure_digest` over an ordered resolved graph | Add: the graph is transitive with cycles, so the walk is a fixed point and the ordering is imposed at serialization, not inherited from traversal |
| Phase 2 task 4, resolve then freeze | Add: content-derived references (BPMN service tasks, call activities, decision refs) are part of the closure, not only declared fields |
| Phase 2 task 4 | Add: identity resolution by key then name, refusing on ambiguity; alias expansion happens before freezing |
| Phase 2 acceptance | Add: a release carrying an unresolvable reference is refused for production promotion and says which reference |
| Phase 2 task 9 | Superseded by this note for the closure half; the routing/ordering half of that task stands as written |

**One acceptance test worth adding**, because it is the failure `2bfd241` actually shipped:

> A release whose BPMN names a tool that no declared list mentions still carries that tool in its
> closure, and importing the release into an empty environment produces a process that runs.

---

## 4. What not to carry

`promotion.py` is a **name-keyed** system: it resolves agents, roles and collections by name and
creates them if absent (`resolve_or_create_roles`, `resolve_or_create_collections`,
`_find_agent_by_name`). That is the workaround, not the design — it exists because no immutable
release primitive was available. Plato's releases are digest-addressed, and create-if-absent by
name is exactly the upsert-by-name that Phase 2 task 7 already says is **not admissible for a
versioned asset**.

Carry the closure walk and the refusal discipline. Do not carry name-keyed resolution.

---

## 5. Open, and worth answering before Phase 2 designs the schema

- **Does a Plato release carry BPMN at all, or reference a Flowable deployment id?** If it
  references, the closure digest covers a pointer and Flowable owns the content, which reopens
  "what does rollback mean" for the process half. `promotion.py` bundles the bytes.
- **Who resolves `{{TOOL_X}}`-style aliases under Plato** — the publisher, as today, or the runtime
  at bind time? Publisher-side keeps the release reproducible; runtime-side keeps it portable
  across environments with different tool ids. These are in tension and the answer is a decision,
  not a detail.
- **Is `assistant`'s `assistant_process` table in scope for D2?** It holds the process references
  whose identity is inconsistent, and nothing in the D1/D2 framing currently names it.
