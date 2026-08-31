# Assessment: "Builder/Pack Studio: the architectural paradigm"

**Source doc:** [Notion](https://app.notion.com/p/3ae2471607bf8057a3d7dcd019826efd) (same author, same
"JazzX Platform v2.0" parent, references the earlier Studio doc directly)
**Assessed against:** live `japes` source, and against `claude/Studio_Notion_Doc_Assessment.md` (the
prior review)
**Date:** 2026-08-03

## Verdict

This is the architectural framing the first doc's Part A implicitly assumed but never stated. It's
tighter and, notably, resolves one of the two issues flagged in the prior review on its own: the
title itself is "Builder/Pack Studio," folding the two names together rather than leaving Studio
unpositioned relative to the roadmap's Pack Studio term. The five principles hold up well against
the actual code — better than a document at this altitude usually does, because several of its
"principles" are already true today, not aspirational.

## Principle-by-principle check against source

**§3.1 (four primitives: skills, guardrails, tools, content).** Matches exactly —
`Skill`/`GuardrailRegistry`/tool catalogs (japes+Kernel+MCP)/`KnowledgeBinding` are the real four
in `jazzx_sdk.agents.interactive`. No fifth primitive exists in the code either. Consistent.

**§3.2 (every primitive has two tiers: platform/locked, builder/scoped).** Does **not** exist yet
for `SkillRegistry` or `GuardrailRegistry` — both are flat name-keyed dicts with no tier field
today (confirmed in `jazzx_sdk/agents/interactive/registry.py`). This is a real gap, not a
description of current state, and the doc doesn't claim otherwise.

Worth knowing: **the tiering idiom already exists elsewhere in japes** —
`jazzx_sdk/tools/documents/templates.py`'s `TemplateRegistry` has exactly this shape today: a
`tier: int` per entry (1 = SDK-native, 2 = pack-config, 3 = borrower-supplied), `register(...,
tier=)`, and `tier_of(name)`. Extending `SkillRegistry`/`GuardrailRegistry` to carry the same
tier field, rather than designing new platform/builder machinery from scratch, is both cheaper and
keeps one tiering idiom in the codebase instead of two. Add to backlog (below).

**§3.3 (capability vs. knowledge — "it errors" vs. "it silently isn't there").** This is exactly
the P0 bug identified in the prior review: `resolve_knowledge`'s `docs:` branch emits filenames
only, so a missing/unfetched source degrades to "confident wrong answer," not an exception. This
doc names the general principle; the prior review already has the specific fix scoped as P0 in the
backlog. The two documents reinforce each other correctly — this isn't new information, but it's
independent confirmation that the prioritization is right.

**§3.4 (isolation is declared, not wired).** This is **already true today**, not just a design
principle — `InteractiveAgent._build_parent_tools` narrows the ambient `InvocationContext` to
exactly a skill's own declared `tools`/`references` while building its sub-agent, and a skill
refused at the `skill:<name>` hop is excluded from the tool list entirely (the parent model isn't
even told it exists). The doc is accurately describing standing behavior, not proposing new
behavior, for the *skill* case. It has NOT been extended to *content* yet — that's the same P0 gap
as §3.3, described from the isolation angle instead of the correctness angle.

**§3.5 (contracts at the edges — declared shape + platform-added evidence/cost/identity layer).**
Matches `InteractiveResponse` (carries `sources`, ids) + `SourceBuilder`/`AnchorRule` for the
evidence layer, and `output_schema` for the declared layer. Existing, not aspirational, for a
single assistant. Not yet extended to the composition case (§6) — see below.

## Where this doc raises something the first review didn't catch

**§6 ("an assistant can be another assistant's skill") is not yet supported by the `Skill` model.**
`Skill` has `instructions`/`tools`/`references`/`mcp_servers`/`model` — it wraps a sub-agent's
prompt and tool access, not a full `InteractiveAgentSpec` (no `guardrails`, no `knowledge`, no
`output_schema` field on `Skill`). So today, a skill can carry raw tools and reference text, but
you cannot nest one fully-specified, independently-grounded-and-guarded assistant inside another as
a skill without flattening away its guardrails and knowledge bindings. If "assistants compose into
apps" (§6, and the doc's own test of success — "whether the tenth one is boring to build") is a
real near-term goal, this is a concrete architectural gap worth scoping now rather than after
Studio's composer (§4, item 3) is built assuming it already works.

**§4 item 4 (publish gate) is partially built, not absent.** `ProfileRegistry.validate()` already
does "every reference resolves" (skills/guardrails/MCP servers, one aggregated error). It does
**not** yet check "any capability with side effects has been explicitly opted into" or "still
passes its evaluation set" — both called out in the doc as required. Scope the extension as
additive to `validate()`, not a new gate.

## Net assessment

This doc is a good higher-order companion to the first — it states the *why* behind primitives the
first doc treats as a config-surface enumeration, and it independently arrives at the same top
priority (knowledge/content binding) via a cleaner argument (the capability-vs-knowledge failure-mode
asymmetry). Two things to add to the backlog as a direct result of this doc; see
`claude/Japes_Enhancement_Backlog.md` for the full updated list.
