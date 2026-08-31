# Done: assistant-as-skill composition (`Skill.spec_ref`)

> **Status (2026-08-25): closed, both halves.** `plans/Japes_Enhancement_Backlog.md`'s P2 is
> struck through and points here.
>
> Surfaced while running the K7 cross-check, which showed the item had been overtaken: the backlog
> described it as unbuilt and the code already had it. Every claim below was verified against the
> tree rather than against the backlog's own text, which is what caught that two of the three
> fields it asked for were already handled and the third was in a different class entirely.

Origin: the Studio architecture doc's §6 ("an assistant can be another assistant's skill"), read
in `plans/Builder_Pack_Studio_Paradigm_Assessment.md`, which raised it as the gap that document
caught and the earlier review had not.

## The item as filed

> **Problem:** the architecture doc's §6 ("an assistant can be another assistant's skill... fix it
> once, everything improves") and its definition of success ("assistants compose into apps without
> bespoke integration work") assume a fully-specified, independently-grounded-and-guarded assistant
> can be nested as a skill. Today's `Skill` model only carries
> `instructions`/`tools`/`references`/`mcp_servers`/`model` -- no `guardrails`, no `knowledge`, no
> `output_schema`. Nesting a full `InteractiveAgentSpec` as another's skill today means flattening
> away its guardrails and knowledge bindings, which defeats the isolation/grounding work done
> elsewhere.
>
> **Task:** scope (design note first, then implementation) how a `Skill` can wrap a full
> `InteractiveAgentSpec` -- likely a new `Skill.spec_ref: str | None` (or similar) resolved against
> `ProfileRegistry`, executed as its own fully-guarded `InteractiveAgent` turn and exposed to the
> parent via the existing `as_tool` pattern, rather than collapsing to raw instructions+tools.
>
> **Acceptance:** a design note deciding the `Skill`-wraps-`InteractiveAgentSpec` shape, or an
> explicit decision to defer composition and say so in the composer's scope.

## What shipped

The proposed shape, essentially verbatim:

- **`Skill.spec_ref: str | None`** on the model, resolved against `ProfileRegistry`.
- **`InteractiveAgent._build_composed_skill_tool`** runs it as its own `InteractiveAgent` turn and
  exposes it to the parent through `as_tool`, rather than flattening to instructions plus tools.
- `ProfileRegistry` supplies the resolution; a `spec_ref` naming nothing is skipped with a warning
  rather than raising, because composition is opt-in per deployment.

`Skill` has also grown well past what the item listed: `reads`, `version`, `visibility`, `invokes`,
`inputs`, `outputs`, `reasoning_effort`, `max_turns`, `stream_reasoning`, `tool_use_behavior`.

The acceptance asked for a design note deciding the shape, or an explicit deferral. The shape was
decided and built, which clears the bar the item set.

## The remaining half, closed 2026-08-25

The item named three fields whose absence flattens a nested assistant. Checked against the tree
before building anything, and **two of the three were already wrong**:

- **`guardrails`: already applied.** A `spec_ref` skill resolves a full `InteractiveAgentSpec`,
  which carries its own `guardrails`, and the nested agent is built with the shared guardrail
  catalog, so the referenced assistant's declarations resolve normally. Adding `Skill.guardrails`
  would have duplicated what the referenced spec owns, with no rule for which wins.
- **`knowledge`: already applied**, for the same reason: it is a field on the referenced spec, and
  the nested agent gets the fabric.
- **`output_schema`: genuinely missing, but not from `Skill`.** `InteractiveAgentSpec` had no such
  field at all. Structured output was a constructor argument only, so a composed assistant, built
  from a spec and never from a constructor argument, could not have one by any route.

The backlog was written before `spec_ref` existed, when the only composition path *was* flattening.
`spec_ref` did not satisfy two thirds of the item so much as make them obsolete.

**What was built instead:**

- `InteractiveAgentSpec.output_schema: str | None`, a name rather than a dotted import path. A spec
  is data, written in YAML and read back from a store; a dotted path would turn configuration into
  arbitrary code execution, and configuration is what a tenant is allowed to add.
- `SchemaRegistry(NamedRegistry[type])`, the same name-keyed shape as `router`/`guardrails`/
  `skills`, refusing anything that is not a `BaseModel` subclass at registration rather than
  failing mid-turn. It inherits `freeze()` with the rest of the family.
- Resolution in `InteractiveAgent.__init__`: an explicit `output_schema=` argument still wins, so
  every existing caller is unchanged. An unresolvable name warns and returns text rather than
  raising, since raising would make adding the field a breaking change for any deployment shipping
  a spec that names a schema it has not registered.
- The nested agent inherits the catalog, without which a composed spec could name a schema that
  never resolves.

**Two docstrings were wrong and are corrected.** `_build_composed_skill_tool` and
`Skill.spec_ref`'s comment both claimed "its own guardrails, knowledge bindings, and output_schema
all apply, not flattened away". True for the first two, false for the third until now.

**What crosses to the parent is JSON text, not an object.** A function tool returns a string to the
model by construction, and `InteractiveResponse.answer` already holds the schema's JSON when a turn
ran with one. So the parent receives something parseable instead of prose, which is the benefit; a
typed object crossing that boundary is not available under the Agents SDK tool contract.

12 tests in `tests/test_spec_output_schema.py`.

## Cross-reference

- `plans/Japes_Enhancement_Backlog.md` -- P2, now closed with a pointer here.
- `plans/Builder_Pack_Studio_Paradigm_Assessment.md` -- §6, the origin.
- `plans/Plato/design_note_k7_parent_child_artifacts.md` -- C5 records the cross-check that found
  this item was already met.
