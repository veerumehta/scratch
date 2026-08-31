# Design note — K7: parent → sub-agent context inheritance

Status: design decisions settled below; **no implementation in this pass** (plan explicitly scopes
K7 as "design note first... size: large... do not fold into a sprint alongside K1-K6/K8/K10").

## The gap, restated precisely

Authorization cascades from parent to sub-agent today (`InvocationContext`/`PermissionScope` via
`descend()`/`narrow()`, checked at `admit_hop`). State does not. Every sub-agent built by
`InteractiveAgent._build_parent_tools` or `_build_composed_skill_tool` starts from nothing but the
argument string (or `query` + `scope` dict, for a `spec_ref` composed skill) the parent LLM wrote
into the tool call — everything the parent already read, extracted, or decided is invisible to it,
and everything the sub-agent itself derives is discarded the moment `as_tool` returns a string.
Cheap waste on a single document turn; on a multi-source investigation it's the difference between
one pass over the evidence and N independent ones.

## 1. Shape

**Decision: a new, small, purpose-built `fabric` store — not an extension of `CaseContext`.**

`CaseContext` (`fabric/canonical/derived.py:225`) was the obvious first candidate — it already has
`parent_case_id`, an open `domain_extensions: dict[str, Any]` (unlike `TraceStep`, which forbids
one), and is periodically checkpointed via `conductor/checkpoint.py::Checkpointer.emit()`. But it's
the wrong layer for this: `CaseContext` is case/Conductor-scoped (one per `case_id`, checkpointed by
a Conductor loop), while the K7 gap is `InteractiveAgent`-scoped — a plain chat assistant using
`_build_parent_tools` has no `CaseContext` and no Conductor loop at all. Making `InteractiveAgent`
depend on `CaseContext` to fix a turn-level problem would be the wrong direction of coupling (the
generic agent layer reaching down into a domain-pack/conductor concept it doesn't otherwise need).

Instead: a new `TurnWorkspace` (renamed from `ArtifactStore` on 2026-08-25; `fabric.canonical`
already owns that name for a finished output document, see C1. Home:
`jazzx_sdk.agents.interactive`, settled in C1). Adopts Kernel's fields directly: nothing in this
tree provides this *shape*, though the original grep checked only the shape and not the
namespace, which is how the name collision was missed. `TraceStep.inputs`/`outputs` are refs
with no store behind them today, exactly the gap this closes:

```
key: str                                    # unique within one artifact scope (see §2)
value_type: Literal["text", "file", "json"]
value: Any                                  # inline, OR a fabric.blob pointer (K5's offload/
                                             # materialize, reused verbatim — not a second
                                             # offload mechanism) for anything large
source_id: str                              # which step/skill produced this
source_type: str                            # "skill" | "tool" | ... — reuse ActorRef's own
                                             # vocabulary rather than inventing a parallel one
                                             # (see §5 — this directly supersedes Kernel's
                                             # untyped creator_source enum)
tag: str | None = None
parent_id: str | None = None                # chain to the artifact this one derived from, if any
                                             # (distinct from the skill-call parent/child axis,
                                             # which §2's scoping handles separately)
```

**Composes with `CaseContext`, does not extend it.** A pack running a Conductor loop that already
checkpoints `CaseContext` may choose to promote an artifact scope's contents into
`case_ctx.domain_extensions["artifacts"]` at checkpoint time — the same "operational form now,
promoted to canonical form at checkpoint/completion" pattern this codebase already applies elsewhere
in this exact file (an AML pack's own operational context promotes to `CaseContext`; operational
`CaseFile` promotes to `CanonicalCaseFile`). The turn workspace is the operational tier; that
promotion is a pack's opt-in choice, not something `InteractiveAgent` or the workspace itself needs to
know about.

## 2. Mechanism

**Decision: a sibling ambient context, propagated with the identical idiom `InvocationContext`
already uses — not a new field on `InvocationContext` itself.**

`InvocationContext`'s own docstring frames it as "one authorization context for a request." Artifact
storage is a second, genuinely different concern (what state is visible, not what actions are
admitted); folding it into `InvocationContext` would blur that single responsibility for no benefit,
since the two concerns don't need to change in lockstep (a hop can narrow permissions without an
artifact scope existing at all, and vice versa in principle).

Concretely: a `TurnWorkspaceScope` (a narrowed view over one root `TurnWorkspace`, scoped to one turn,
see below) gets its own `ContextVar`, with `set_turn_workspace`/`get_turn_workspace`/
`reset_turn_workspace` mirroring `authority.context`'s `set_/get_/reset_invocation_context` exactly
— same shape, same file-local pattern, deliberately not a novel propagation mechanism.

Threaded at the *same* call sites `InvocationContext` narrows at today:
- `_build_parent_tools`'s per-skill narrowing block (`agent.py:~620-660`) gains a second
  `token2 = set_turn_workspace(...)` alongside its existing `token = set_invocation_context(...)`,
  reset together in the same `finally`.
- `_build_composed_skill_tool` — unlike its authorization treatment (deliberately *no* extra
  narrowing there, since the nested `InteractiveAgent`'s own `_check_turn_entry` re-checks the
  ambient context itself) — *does* need an explicit narrow/pass-through decision for the artifact
  axis, since a nested `InteractiveAgent.respond()` call has no equivalent of "ambient context
  already covers it" for artifact visibility. Concrete mechanism TBD at implementation time; the
  design intent is: the nested assistant's own declared `reads_artifacts` (see §3) still gates what
  it sees, the same rule as a raw-instructions skill.

**Scope lifetime: one root `respond()` call (a turn), not cross-turn.** Mirrors
`InvocationContext.trace_id`'s own natural scope (one invocation). A caller wanting artifacts to
persist *across* turns of one conversation composes this with `ConversationStore`/checkpointing
explicitly — that's not the workspace's own concern, same separation `InvocationContext` itself
already keeps from `ConversationStore`.

## 3. Visibility is authorization, not storage

**Decision: reuse `PermissionScope`/`admit_hop`, generalized via a new `artifact:<key>` selector
family — directly mirroring `agents/adjudication/workspace.py::EvidenceWorkspace`'s existing
`mount:<name>` pattern**, not a new gating mechanism:

- `EvidenceWorkspace.open()` narrows the ambient context to exactly `[mount:<name> for name in
  mounts]` for a `with` block, via `ctx.permission_scope.narrow(...)` + `descend()` — literally the
  primitive K7 needs, one level removed from evidence mounts to parent artifacts.
- `Skill` gains a new field, `reads_artifacts: list[str] = []`, alongside its existing
  `tools`/`references`/`reads` — enumerating which of the *parent's* artifact keys this skill may
  read. `_build_parent_tools`' narrowing block treats it exactly like `reads` treats
  `doc_source:<s>` today: `declared = [..., *[f"artifact:{k}" for k in sdef.reads_artifacts]]`,
  narrowed, then each name re-checked via `admit_hop(f"artifact:{k}")` before being exposed.
- **Writing** a new artifact under a sub-agent's *own* namespace is always allowed within its own
  scope — a sub-agent can always record what it derived; narrowing only ever restricts *reading the
  parent's* prior state. A skill that declares no `reads_artifacts` sees none of the parent's
  artifacts — the same "nothing crosses unless declared" default `tools`/`references`/`reads`
  already enforce, so this is additive to the narrowing contract, not a new kind of gate.

Get this wrong (e.g. a sub-agent inheriting the parent's full artifact set unnarrowed) and this
becomes a way around the least-privilege narrowing `_build_parent_tools` already does — explicitly
named in the plan as the failure mode to avoid, and the reason this whole axis rides the same
`PermissionScope` rather than a parallel, unchecked pass-through.

## 4. Write-back

**Decision: one-directional, matching Kernel's own answer exactly — child reads parent; parent does
not read child's artifacts.** Only the sub-agent's existing return value (the `as_tool` string, or
`reply.answer` for a composed skill) crosses back, unchanged from today.

Chosen over two-way sync because: (a) it's the smaller, safer change — a parent that never declares
artifacts for a skill to read sees zero behavior change, and a parent's own state can't be corrupted
by a sub-agent's derivations without an explicit new write path; (b) it matches the existing
directional asymmetry `InteractiveAgent` already has for authorization (a narrowed child cannot
widen its own scope back up for the parent); (c) a symmetric answer needs its own conflict/merge
policy (what if two sibling sub-agents write artifacts with the same key derived from the same
parent state?) that a one-directional answer avoids entirely. Two-way sync, if ever wanted, is a
distinct, separately-scoped follow-up — not bundled into this decision.

## 5. What not to port

Confirmed, not ported:
- **Kernel's OData-on-notepads query surface.** `jazzx_sdk/odata.py` + `EntityStore.filter` already
  cover structured querying over stored objects; a second query language for one store type would
  be exactly the "multiple ways to do the same thing" this codebase has been actively closing this
  session (see K1's retry-implementation consolidation).
- **Kernel's untyped `creator_source` enum.** This design's `source_id`/`source_type` fields (§1)
  already cover "who produced this," and `source_type` should draw its vocabulary from `ActorRef`'s
  existing typed `actor_type` values (`fabric/canonical/trace.py`) rather than a new, parallel,
  untyped enum — the same reuse-don't-duplicate call K2 already made for `DurableSuspension`'s
  approver fields against `OverrideEvent`'s vocabulary.

## Cross-checks the plan asks for — not completed

The plan's own verify criterion for this design note is review against
`Builder_Pack_Studio_Paradigm_Assessment §6` and the `Skill`-composition item in
`Japes_Enhancement_Backlog P2`. Searched this repo (including gitignored `docs/plans/`) for both —
neither document is present on disk. This note has **not** been checked against them. Before this
design is acted on, a human reviewer with access to those documents should confirm §2's exact
propagation mechanism and §3's `reads_artifacts` field naming don't conflict with whatever the
still-open assistant-as-skill composition question in that backlog item already assumes.

## Verify criteria for the (not-yet-started) implementation

Recorded here so they aren't re-derived later:
- A parent writes an artifact; a sub-agent that declares `reads_artifacts` including that key reads
  it without re-deriving it.
- A sub-agent that does *not* declare a given key cannot read it, even if the parent's own scope
  admits it — narrowing, not just declaration, gates visibility (mirrors `EvidenceWorkspace`).
- The existing string-only path (a skill declaring no `reads_artifacts`) is byte-identical to
  today — this whole axis is additive.

## Acceptance (this note)

All five points settled above. Implementation is out of scope for this pass — "size: large,
scope as its own effort" per the plan.

---

# Continuation, 2026-08-25

Written against `japes` `plato`@`77cdcb9`. The five decisions above stand. This adds one correction
the original note got wrong, closes the mechanism §2 left open, and reconciles the design against
work that has landed since it was written.

## C1. `ArtifactStore` is already taken, and §1's grep claim is wrong

§1 says the fields are adopted from Kernel "since nothing in this tree already provides this shape
(confirmed by grep)". The shape half of that is right. The name half is not:

- `jazzx_sdk.fabric.canonical.Artifact` exists (`derived.py:370`), is exported from
  `fabric.canonical.__init__`, and is Schema Spec v1.0 §7.4 Derived Object 4.
- `ArtifactStore` exists (`fabric/canonical/store/`), and is reachable as `store.artifact` on the
  canonical store facade.

They are genuinely different things that share a word. The canonical `Artifact` is a **finished
output document** (SAR narrative, credit memo, audit packet) with citations, disclosures and
decision/evidence refs: the deliverable at the end of a case, durable and auditable. K7's is
**intermediate derived state**, scoped to one turn, that a parent hands a child so it does not
re-derive what has already been worked out.

So the design is not redundant, but the name is unusable, and the original line reads as though the
namespace had been checked when only the shape was. Correcting the record matters more than the
rename: a future reader would otherwise trust that grep.

**Rename: `TurnWorkspace`**, with `TurnWorkspaceScope` for the narrowed per-skill view. It puts the
lifetime in the name, which is the property most likely to be misread (§2 already scopes it to one
`respond()` call, and "artifact" suggests something that outlives the turn, which is exactly what
the canonical `Artifact` is). It also joins the family it actually belongs to:
`agents/adjudication/workspace.py::EvidenceWorkspace` is the pattern §3 already borrows.

**This also settles §1's open "candidate homes" question**: `jazzx_sdk/agents/interactive/`, not
`fabric/`. §2 bounds the lifetime to one `respond()` call, and `respond()` is an `InteractiveAgent`
concept. `fabric` is where durable, cross-turn, canonical state lives, and putting turn-scoped
scratch state beside `fabric.blob`/`fabric.entities` would invite exactly the confusion the rename
is meant to remove. A pack that wants an entry to outlive the turn promotes it, which §1 already
describes.

## C2. Closing §2's open item: the composed-skill boundary

§2 left `_build_composed_skill_tool`'s mechanism "TBD at implementation time". It is decidable now,
and the answer is not the obvious one.

A `ContextVar` set in the parent's task is **already visible** inside the nested
`InteractiveAgent.respond()` call, because the composed tool awaits it on the same task. So the
default behaviour is full pass-through: the nested assistant would see every one of the parent's
workspace entries, unnarrowed. That is the precise failure §3 names as the thing to avoid, and it
happens by *inaction* rather than by a wrong line of code, which makes it the dangerous kind.

**Decision: `_build_composed_skill_tool` must narrow explicitly, and its default with no
declaration is an empty scope, not an inherited one.** This is a real asymmetry with how the same
call site treats authorization, and the asymmetry is deliberate: authorization can safely
pass through because the nested agent's own `_check_turn_entry` re-checks the ambient context, so
there is a second gate. Workspace visibility has no second gate: whatever the ContextVar holds when
`respond()` runs is what the nested agent can read. Nothing downstream will catch an over-wide
scope, so the narrowing has to be unconditional at the boundary.

Verify criterion, added to the list below: a composed `spec_ref` skill that declares no
`reads_artifacts` reads nothing, asserted by a test that would pass trivially if the narrowing were
deleted only because the assertion is on the *nested* agent's view, not the parent's.

## C3. Reconciling with the per-turn tool catalog (landed 2026-08-24)

`InteractiveAgent`'s `tools=` now accepts a zero-arg callable resolved per turn, so one bound agent
can serve turns whose tools differ. That is the same family of problem as K7: per-turn state
reaching an agent that outlives the turn. The question is whether K7 should ride it rather than add
a second mechanism.

**It should not, and the reason is directional.** The tool provider is a *pull*, evaluated when the
agent builds its own tools, answering "what can I call this turn". K7 is a *push* that has to cross
a boundary mid-turn, from a parent into a child that the parent is invoking. A provider callable
cannot express "and the child sees a narrowed subset of what I derived", which is the entire point.

They stay separate, and both remain per-turn, which is the consistency worth having. Worth stating
because the next person to read both will reasonably ask.

## C4. A workspace is not a registry

Registries can now be sealed (`NamedRegistry.freeze()`), and a deployment composes skills and
prompts per tenant and then freezes before serving. A `TurnWorkspace` is the opposite kind of
thing: it is created per turn, written during it, and discarded. **Nothing derived at runtime
belongs in a registry, and nothing frozen at boot belongs in a workspace.** Stated because both now
exist, both hold named things, and the freeze exists precisely so that what an instance can reach
stops moving once it serves.

## C5. Cross-checks: performed 2026-08-25, both pass

Both documents were supplied on 2026-08-25 and read in full. The two confirmations the original
note asked for hold. Recording what was actually checked, since "no conflict" is worth as little as
the search behind it.

**Both documents are stale on their central claims**, which matters before quoting either as
authority:

- The assessment's §3.2 says tiering "does **not** exist yet for `SkillRegistry` or
  `GuardrailRegistry` -- both are flat name-keyed dicts with no tier field today". It exists now
  (`_TieredRegistry`, `tier_of`), and has since gained a freeze (C4).
- The backlog's P2 proposes "likely a new `Skill.spec_ref: str | None` (or similar) resolved
  against `ProfileRegistry`, executed as its own fully-guarded `InteractiveAgent` turn and exposed
  to the parent via the existing `as_tool` pattern". That is shipped: `Skill.spec_ref` exists and
  `_build_composed_skill_tool` is exactly the described execution path. **P2's stated acceptance is
  met**, and the item was closed on 2026-08-25 with the record in
  `status/done_skill_spec_ref_composition.md`.

### Confirmation 1: §2's propagation mechanism against the assessment's §6

**Passes, and the assessment strengthens the design rather than merely permitting it.**

The assessment's §3.4 finds that isolation-is-declared is *already standing behaviour* for skills:
`_build_parent_tools` narrows the ambient `InvocationContext` to a skill's declared
`tools`/`references`, and a skill refused at its `skill:<name>` hop is excluded from the tool list
entirely. It then says, explicitly: *"It has NOT been extended to content yet."*

K7's §2 threads the turn workspace through that same mechanism, at that same call site, for
content. So it is not a parallel mechanism competing with an assumed one; it is the extension the
assessment names as missing, built the way the assessment says isolation is already done. Nothing
in §6 assumes a different propagation shape.

### Confirmation 2: §3's `reads_artifacts` against the backlog's P2

**No collision, and one design question the original note did not ask.**

P2's field is `spec_ref`; K7's is `reads_artifacts`. Different names, different purposes, no
conflict. But `Skill` already carries a **`reads`** field, narrowed as `doc_source:<s>` in exactly
the pattern §3 proposes to copy for `artifact:<k>` (`agent.py:706`, `:723`). Two adjacent
list-of-strings fields, both meaning "what this skill may read", differing only in what backs them.

Worth deciding at implementation rather than inheriting: **is `reads_artifacts` a second field or a
second selector prefix inside `reads`?** A single `reads` carrying `doc_source:x` and `artifact:y`
keeps one declaration surface and one narrowing loop; two fields keep each one's vocabulary
unprefixed and obvious to a pack author. This note's §3 assumed the second without weighing the
first. Not a conflict with P2, so it does not block, but it is the shape question a reviewer of §3
should be given rather than left to discover.

### P2's other half, checked and closed the same day

The original reading of P2 said `Skill` carries no `guardrails`, `knowledge` or `output_schema`, and
that this constrained C2. Checked against the tree rather than taken from the backlog: two thirds
of it was stale. A `spec_ref` skill resolves a full `InteractiveAgentSpec`, whose own `guardrails`
and `knowledge` apply through the shared catalog and fabric, so a composed assistant is **not**
unguarded. Only `output_schema` was genuinely absent, and from `InteractiveAgentSpec` rather than
from `Skill`; it now exists as `spec.output_schema` resolved against a `SchemaRegistry`
(`status/done_skill_spec_ref_composition.md`).

**C2 stands unchanged, for its own reason rather than this one.** The nested turn does re-check
authorization through its own `_check_turn_entry`, which is why `_build_composed_skill_tool`
deliberately does not narrow the authorization axis. It has no equivalent second gate for
*workspace visibility*: whatever the ContextVar holds when `respond()` runs is what the nested agent
reads. That is the argument, and it does not depend on the nested assistant being unguarded.

## Verify criteria, extended

Adding to the three already recorded:

- A composed `spec_ref` skill declaring no `reads_artifacts` reads nothing from the parent's
  workspace, asserted against the nested agent's own view (C2).
- Deleting the narrowing at the composed-skill boundary fails a test. Given C2's failure mode is
  inaction, a test that only passes when the code is present is not enough; it has to fail when the
  code is removed.
- The canonical `Artifact` path is untouched: a pack producing a credit memo behaves identically
  with a workspace present and absent (C1).
- Whichever of the two shapes C5 raises is chosen, a skill declaring nothing reads nothing: the
  default must not differ between a `reads`-prefixed and a separate-field implementation.
