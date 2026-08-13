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

Instead: a new `ArtifactStore` (working name — final name TBD at implementation time, candidate
homes: `jazzx_sdk.fabric.artifacts` alongside `fabric.blob`/`fabric.entities`, or nested under
`jazzx_sdk.agents.interactive` if it turns out to be too `InteractiveAgent`-specific to belong in
`fabric` proper — implementation should re-derive this after point 2 is nailed down). Adopts
Kernel's fields directly, since nothing in this tree already provides this shape (confirmed by
grep — `TraceStep.inputs`/`outputs` are refs with no store behind them today, exactly the gap this
closes):

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
`CaseFile` promotes to `CanonicalCaseFile`). The artifact store is the operational tier; that
promotion is a pack's opt-in choice, not something `InteractiveAgent` or the store itself needs to
know about.

## 2. Mechanism

**Decision: a sibling ambient context, propagated with the identical idiom `InvocationContext`
already uses — not a new field on `InvocationContext` itself.**

`InvocationContext`'s own docstring frames it as "one authorization context for a request." Artifact
storage is a second, genuinely different concern (what state is visible, not what actions are
admitted); folding it into `InvocationContext` would blur that single responsibility for no benefit,
since the two concerns don't need to change in lockstep (a hop can narrow permissions without an
artifact scope existing at all, and vice versa in principle).

Concretely: an `ArtifactScope` (a narrowed view over one root `ArtifactStore`, scoped to one turn —
see below) gets its own `ContextVar`, with `set_artifact_scope`/`get_artifact_scope`/
`reset_artifact_scope` mirroring `authority.context`'s `set_/get_/reset_invocation_context` exactly
— same shape, same file-local pattern, deliberately not a novel propagation mechanism.

Threaded at the *same* call sites `InvocationContext` narrows at today:
- `_build_parent_tools`'s per-skill narrowing block (`agent.py:~620-660`) gains a second
  `token2 = set_artifact_scope(...)` alongside its existing `token = set_invocation_context(...)`,
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
explicitly — that's not this store's own concern, same separation `InvocationContext` itself
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
