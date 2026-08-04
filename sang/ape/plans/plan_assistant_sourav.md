# japes enhancement backlog — arising from the Studio design-doc review

Source: assessment of two Notion docs by the same author — "Building blocks for assistants: the
Studio surface and the FDE path" and "Builder/Pack Studio: the architectural paradigm" — against
live japes source (2026-08-03). See `claude/Studio_Notion_Doc_Assessment.md` and
`claude/Builder_Pack_Studio_Paradigm_Assessment.md` for the full reviews. Each task below is
written to be picked up directly (by an engineer or by Claude in a coding session against the
`japes` repo, `dev` branch).

Priority order reflects: (1) fix the real correctness gap, (2) close drift risk before more code
is written on top of inconsistent primitives, (3) new authoring surface.

---

## P0 — Fix: docs-grounding delivers no content

**File:** `jazzx_sdk/agents/interactive/knowledge.py`, `resolve_knowledge()`

**Problem:** the `docs:` branch of a `KnowledgeBinding` emits only `[doc] {name}` per document —
filename only. An agent grounded this way can name a document and read none of it; it will
sometimes answer as if the content is absent, which is a correctness bug. Both source docs
independently flag this as the top-priority gap — the architecture doc frames it as the general
principle (capability fails loud, knowledge fails silently), the Studio doc as the specific fix.

**Fix direction:** implement the `reads:` concept from the design docs, but as a thin layer over
the *existing* isolation primitive rather than a new one:
- Generate a per-source `list`/`read`/`search` tool triple bound (by closure) to the resolved
  docs collection.
- Gate each generated tool's selector through `jazzx_sdk.authority.context.PermissionScope` /
  `admit_hop` — the same mechanism `InteractiveAgent._build_parent_tools` already uses to narrow a
  skill's ambient context to exactly its own declared `tools`/`references` (this is "isolation
  declared, not wired" already working today for skills; extend it to content, don't reinvent it),
  and that `agents/reasoning/grounding.py`'s `BrowseGate` already uses for denying browse tools
  mid-call.
- Each generated tool must implement the three traps called out in the Studio doc §10: return an
  explicit `UNAVAILABLE: …` (and instruct the model not to ask the user to upload anything) when a
  source has zero files; same explicit-miss behavior when a `file_pattern` matches nothing; and the
  bound directory/handle must outlive the agent call, not the handler (tie teardown to the response
  being sent, not to handler return).
- Add a per-read byte cap bound at build time (not surfaced to the model-facing schema) and a
  path-escape guard, per the Studio doc §11.

**Acceptance:** a `KnowledgeBinding(docs=...)` with a `reads:`-style declaration on a `Skill`
produces working `list_<source>`/`read_<source>`/`search_<source>` tools whose isolation is
enforced via `PermissionScope`, with test coverage for: empty source, no-match search, and a
directory torn down before vs. after the agent call completes.

---

## P1 — Consolidate the two grounding/index primitives

**Files:** `jazzx_sdk/tools/agent/grounding.py` (index-then-fetch, unused), `jazzx_sdk/agents/reasoning/grounding.py` (`PrecomputedGrounding`, wired)

**Problem:** `tools/agent/grounding.py` is explicitly marked "provided ahead of demand — not yet
exercised" and does almost the same job (compact index + on-demand full fetch) as the P0 work
above will need. Leaving both in the tree risks a third re-derivation the next time someone needs
"give the model an index, fetch on demand."

**Task:** either (a) fold `build_summary_index`/`select_items` into the P0 `reads:` implementation
as its index-rendering step, or (b) if it's genuinely superseded, mark it deprecated with a
pointer to the new home. Do not ship P0 alongside an unreferenced near-duplicate.

**Acceptance:** one canonical "index + on-demand fetch" code path; the other is either consumed or
explicitly deprecated with a docstring pointer.

---

## P1 — Reconcile `InteractiveAgentSpec`/`Skill` with `AssistantManifest`

**Files:** `jazzx_sdk/agents/interactive/spec.py`, `jazzx_sdk/manifest/assistant_manifest.py`, `jazzx_sdk/manifest/loader.py`

**Problem:** two declarative "describe an assistant" schemas exist and both reference
`SkillRegistry` by name (`spec.skills` vs. `manifest.allowed_skills`) with no documented
relationship. `AssistantManifest` carries governance fields (autonomy ceiling, archetype) that
`InteractiveAgentSpec` doesn't; `InteractiveAgentSpec` carries execution fields (model, guardrails,
knowledge, conversation) that `AssistantManifest` doesn't.

**Task:** produce a short design note (or extend this backlog) deciding one of:
1. `AssistantManifest` is the governance envelope; it *references* an `InteractiveAgentSpec` (or a
   profile directory) rather than duplicating `allowed_skills`.
2. `InteractiveAgentSpec` gains the governance fields and `AssistantManifest` is deprecated/merged.
3. They stay separate but `ProfileRegistry.validate()` / `load_manifest()` cross-validate each
   other (e.g. manifest's `allowed_skills` must be a subset of the spec's `skills`).

Whichever direction is picked, any Studio work that authors "the profile" needs to know which
schema it's writing before UI work starts.

**Acceptance:** a written decision, plus (if divergence is kept) a boot-time cross-validation check
analogous to `ProfileRegistry.validate()`.

---

## P1 — Add tiering to `SkillRegistry` / `GuardrailRegistry` — reuse the existing pattern

**Files:** `jazzx_sdk/agents/interactive/registry.py`, `jazzx_sdk/tools/documents/templates.py` (reference pattern)

**Problem:** the architecture doc's §3.2 (every primitive has a platform/locked tier and a
builder/scoped tier) is not yet implemented for skills or guardrails — both registries are flat
name-keyed dicts today, no tier field.

**Do not design this from scratch.** `TemplateRegistry` (`jazzx_sdk/tools/documents/templates.py`)
already implements exactly this shape: `register(name, obj, tier=)`, an internal `_tiers` map,
and `tier_of(name)` (tier 1 = SDK-native, 2 = pack-config, 3 = borrower-supplied). Port the same
shape onto `SkillRegistry`/`GuardrailRegistry`: a locked/platform tier that a builder-tier
registration cannot silently shadow or override without an explicit promotion action, plus a
`tier_of(name)` query so `ProfileRegistry.validate()` and any future "promote to platform" UI can
tell which tier a reference resolved from.

**Acceptance:** `SkillRegistry`/`GuardrailRegistry` support `register(..., tier=)` and `tier_of()`
with the same three-tier convention as `TemplateRegistry`; a builder-tier registration cannot
overwrite a platform-tier name of the same key without an explicit override path.

---

## P2 — Scope "assistant-as-skill" composition (architecture doc §6)

**File:** `jazzx_sdk/agents/interactive/spec.py` (`Skill` model)

**Problem:** the architecture doc's §6 ("an assistant can be another assistant's skill... fix it
once, everything improves") and its definition of success ("assistants compose into apps without
bespoke integration work") assume a fully-specified, independently-grounded-and-guarded assistant
can be nested as a skill. Today's `Skill` model only carries `instructions`/`tools`/`references`/
`mcp_servers`/`model` — no `guardrails`, no `knowledge`, no `output_schema`. Nesting a full
`InteractiveAgentSpec` as another's skill today means flattening away its guardrails and knowledge
bindings, which defeats the isolation/grounding work done elsewhere.

**Task:** scope (design note first, then implementation) how a `Skill` can wrap a full
`InteractiveAgentSpec` — likely a new `Skill.spec_ref: str | None` (or similar) resolved against
`ProfileRegistry`, executed as its own fully-guarded `InteractiveAgent` turn and exposed to the
parent via the existing `as_tool` pattern, rather than collapsing to raw instructions+tools. Do
this scoping before the Studio composer (§4 item 3 of the architecture doc) is built assuming
composition already works.

**Acceptance:** a design note deciding the `Skill`-wraps-`InteractiveAgentSpec` shape, or an
explicit decision to defer composition and say so in the composer's scope.

---

## P2 — Extend `ProfileRegistry.validate()` into the full publish gate

**File:** `jazzx_sdk/agents/interactive/registry.py`

**Problem:** the architecture doc's §4 item 4 (publish gate) asks for four checks: references
resolve, contracts are coherent, side-effecting capabilities are explicitly opted into, and the
evaluation set still passes. `ProfileRegistry.validate()` already does the first (one aggregated
error listing every dangling skill/guardrail/MCP reference) — the other three don't exist yet.

**Task:** extend `validate()` (or a new `publish()` wrapping it) to also check: (a) a tool's
declared side-effect classification (this presupposes the tool-registry side-effect tiering the
Studio doc's §3.3 calls "the largest open area in the design" — sequence accordingly, this task
depends on that work existing first), (b) declared input/output contract coherence across
composed assistants, and (c) a hook to run the profile's bound evaluation set and block publish on
failure, matching the architecture doc's "an unpublishable profile is a feature."

**Acceptance:** publishing a profile with an unclassified side-effecting tool, or with a failing
bound evaluation set, is rejected with a specific reason — not silently allowed.

---

## P2 — Studio tool-catalog: build on `discovery.py`, don't re-scope it

**Files:** `jazzx_sdk/tools/platform/discovery.py`, `jazzx_sdk/clients/kernel_client.py`

**Problem:** the design doc's §3.3 asks Studio to "browse a registered tool catalog (name,
description, args) per pack/deployment" as if from scratch. `discover_tools`/`get_tool_config`
and `kernel_client.list_tools()`/`get_tool()` already provide this against Kernel.

**Task:** when Studio's tool-catalog UI is built, scope it as: (1) a UI over the existing
`discover_tools`/`kernel_client` calls for Kernel tools, (2) a separate, new listing for
in-process/pack tools (which have no existing catalog — this part is genuinely new, per the design
doc's "japes needs its own tool registry in addition to Kernel's"), and (3) an MCP server catalog
(names resolved from `spec.mcp_servers`/`skill.mcp_servers`, likely also new). Don't build a fourth
Kernel-tool-listing mechanism.

**Acceptance:** Studio's tool picker calls the existing Kernel discovery path for Kernel tools;
a new, explicitly-scoped `ToolRegistry` covers only in-process/pack tools.

---

## P2 — Position "Studio" relative to Pack Studio before further design work

**Not a code task — a scoping/comms task.**

**Problem:** `JazzX Update 4272026 v4.pdf` already communicates "Pack Studio" (re-scoped from v1.0
Builder Studio) as the sanctioned roadmap term, with a much broader scope (policy ingestion,
playbook authoring, evidence-schema builder, capability catalog, integration generator, eval-suite
builder, packaging). The first Notion doc's "Studio" — persona/skills/guardrails/knowledge
authoring for one `InteractiveAgentSpec` — is a slice of that, but never says so. The second doc
(the architecture one) partially resolves this on its own by titling itself "Builder/Pack Studio,"
but doesn't spell out where the boundary sits relative to the roadmap deck's broader scope (policy
ingestion, playbook authoring, etc. — nothing in either Notion doc covers those).

There is also an explicit leadership caution (`Commercial Lending via Platform 2.0 with YETI.md`):
harden the SDK and prove it with YETI before investing further in Pack Studio surface.

**Task:** before committing engineering time to the Studio config-surface items (skills editor,
tool assignment UI, guardrail authoring, the composer, the publish gate), get an explicit answer
to: is this "Studio" (a) the near-term assistant-profile module of Pack Studio, scoped narrowly on
purpose, or (b) work that should wait behind the YETI-hardening milestone. Record the answer in
the project so it doesn't get re-litigated per PR.

---

## P3 — Scaffold generator (Studio doc's own top pick, §7)

**Problem:** the design doc itself flags this as "probably the highest-leverage thing we could
ship" — the middle rung between the 20-line `examples/loan_assistant/` snippet and the 80-file
`jazzx-assistant` production pack.

**Task:** a generator (CLI or script) that emits: a profile folder (`profile.yaml`/`persona.md`/
`skills/*.yaml`), a `harness.py` wiring tool/guardrail catalogs, a `test_*.py` using `ScriptedLLM`,
and a handler stub implementing `BaseHandler.handle` with the six `HandlerContext` calls an FDE
must make (per the design doc §8 — including `ctx.extend_visibility`, the easy-to-miss one). Model
it on the delta between `examples/loan_assistant/` and `jazzx-assistant`.

**Acceptance:** running the generator against a new domain name produces a runnable
`python -m examples.<name>.harness` that passes its own scripted-LLM test out of the box.

---

## P3 — Reusable mock harness (Studio doc §12, §17)

**Problem:** `jazzx-assistant` hand-rolls `mock_assistant_api` + `mock_knowledge_hub` + a
devcontainer compose stack; the design doc's own drift table (§17) lists this as something "every
pack rebuilds" that should be a shared primitive.

**Task:** extract a reusable mock-service harness (assistant API + knowledge hub mocks +
devcontainer compose) into japes proper, parametrized per pack, following the same pattern already
used for `CollectorChannel` (the in-process mock for channels) and `CREToolRegistry(use_mocks=True)`
(the in-process mock for CRE tools).

**Acceptance:** a new pack gets working mocks by configuration, not by copy-pasting
`jazzx-assistant`'s.

---

## Not recommended as-is

- **Do not** implement `reads:`/tool isolation as a bespoke closure-binding scheme independent of
  `PermissionScope`. (See P0.)
- **Do not** design platform/builder tiering for skills and guardrails from scratch — port
  `TemplateRegistry`'s existing tier convention. (See P1.)
- **Do not** build a new Kernel-tool-catalog browser independent of `discovery.py`/`kernel_client`.
  (See P2.)
- **Do not** start Studio UI work on `InteractiveAgentSpec` authoring until the `AssistantManifest`
  relationship is decided — reworking the UI after the schema question is settled is more
  expensive than settling it first.
- **Do not** build the composer (architecture doc §4 item 3) assuming assistant-as-skill
  composition already works — it doesn't, on the current `Skill` model. Scope that first. (See P2.)