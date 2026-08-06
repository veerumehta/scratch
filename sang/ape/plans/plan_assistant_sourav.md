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

> **Status (2026-08-04): DONE (`00630ae`).** Implemented as the full `reads:` design, not the
> minimal stopgap: `Skill.reads` + `KnowledgeBinding.name` (new schema fields, `spec.py`), a new
> `jazzx_sdk/agents/interactive/reads.py` (`build_read_tools` — closure-bound `list_<name>`/
> `read_<name>`/`search_<name>` `@function_tool`s per source), and `agent.py` wiring: `scope`
> threaded through `_build_parent_tools`/`_build_agentic`/`_respond_agentic`/`_stream_agentic`/
> `run()`/`respond_stream()`, gated via a new `doc_source:{name}` selector through the existing
> `admit_hop`/`PermissionScope.narrow()` cascade (same mechanism as `tool:`/`ref:`). Acceptance
> items covered: empty source and no-match search both return explicit `UNAVAILABLE:` strings
> (never silently empty); `read_<name>` rejects any `document_id` not in that source's own
> `list_<name>` output (the KH-backed equivalent of a path-escape guard — no local directory
> exists here to escape); byte cap is a closure constant, not in the tool schema. One acceptance
> item doesn't literally apply: "directory torn down before vs. after the agent call" assumes
> local-directory materialization, but `fabric.docs.get()` is a per-call KH fetch with nothing to
> tear down — documented in `reads.py`'s module docstring rather than silently skipped. 11 new
> tests (`tests/test_agent_reads.py`, unit + `InteractiveAgent` integration incl. a
> `PermissionScope`-refusal case); full suite 2280 passed (was 2269), no regressions.

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

> **Status (2026-08-04): DONE (`3de2ff5`), option (a) for `build_summary_index`.** Folded
> `build_summary_index` into `reads.py`'s `list_<name>`/`search_<name>` rendering (its output is
> now a markdown table, not a hand-rolled "id: name" line) — that helper's first real internal
> consumer, resolving its "ahead of demand" status honestly rather than leaving a second
> index-renderer to re-derive. `select_items` does **not** fold in: it selects from an
> already-in-memory `{id: item}` dict, while `read_tool` does a remote per-id `fabric.docs.get`
> fetch — a different mechanism, documented as such rather than silently dropped; it stays
> ahead-of-demand for a client agent that already holds its items in memory.
>
> Also found and fixed a real inaccuracy while here: `tools/agent/grounding.py`'s own docstring
> claimed `agents/reasoning/grounding.py` (`PrecomputedGrounding`/`BrowseGate`) "is wired" — grep
> shows zero real callers beyond its own test file, contradicting the claim. Corrected the
> docstring rather than propagating it. **`PrecomputedGrounding`/`BrowseGate` themselves are still
> unwired** — genuinely out of scope here (a different use case: whole-corpus LLM-selection +
> browse-gate ahead of one reasoning call, not a per-source list/read/search tool), not something
> this fold should force into `reads.py`. Updated 2 test assertions for the new table format; full
> suite 2280 passed (unchanged count — a fold, not new coverage), no regressions.

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

> **Status (2026-08-04): DONE (`cdf7ee8`), option 3.** Kept the two schemas separate and added the
> boot-time cross-validation the acceptance criterion asks for: `load_manifest()` gained an
> optional `profile_registry` param — when given, checks `manifest.profile_ref` (falling back to
> `assistant_id`) resolves in the `ProfileRegistry`, and that `manifest.allowed_skills` is a subset
> of that profile's `spec.skills`, raising one aggregated `ValueError` for every problem found
> (skills + profile mismatch together, not fail-fast on the first). 4 new tests in
> `tests/test_assistant_primitives.py`; full suite green at the time.

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

> **Status (2026-08-04): DONE (`fae9516`).** New `_TieredRegistry` mixin (deliberately not
> inheriting `NamedRegistry` itself, to avoid a duplicate-base MRO clash when combined as
> `(mixin, NamedRegistry[T])`) ported onto both: `register(..., tier=)` (default `tier=3`,
> `load_dir(..., tier=2)` default) and `tier_of(name)` (3 for unregistered), same 1/2/3
> platform/pack-config/builder convention as `TemplateRegistry`. Went one step past the literal
> reference pattern: `TemplateRegistry`'s own `_put` silently overwrites regardless of tier — fine
> for a single-author extraction-template catalog, not for a shared skill/guardrail catalog a
> less-trusted builder registers into — so a tier-3 registration over an existing tier-1/2 name
> now raises unless `allow_override=True` is passed explicitly (the plan's own acceptance
> criterion asked for exactly this). Same-tier reload and promotion-to-a-stricter-tier are both
> left unblocked (not shadowing risks). 5 new tests in `tests/test_skill_registry.py`; full suite
> 2285 passed (was 2280), no regressions.

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

> **Status (2026-08-04): DONE (`db98b47`).** Design decision (recorded here rather than a separate
> design-note file): `Skill.spec_ref: str | None` names a full `InteractiveAgentSpec`, resolved
> from a new `InteractiveAgent(profile_registry=...)` ctor param (a `ProfileRegistry`). When set,
> `_build_parent_tools` skips the raw-instructions sub-agent path entirely and instead builds a
> plain `@function_tool` (via new `_build_composed_skill_tool`) that runs the nested spec's own
> full `InteractiveAgent.respond()` turn — its own guardrails/knowledge/output_schema all apply,
> which is the whole point (a flattened `tools`/`references` skill loses all of that). Exposed via
> a hand-built `@function_tool`, not `Agent.as_tool()` — `InteractiveAgent` isn't an Agents-SDK
> `Agent`, there's nothing for `as_tool()` to wrap.
>
> Real design call made, not guessed: no manual `PermissionScope.narrow()` around the nested
> call, unlike the `tool:`/`ref:`/`doc_source:` narrowing `_build_parent_tools` does for a
> raw-instructions skill. The nested `respond()` runs under the *same* ambient
> `InvocationContext`, and its own `_check_turn_entry` already checks `assistant:<spec_ref>`
> against it — narrowing to just that one selector would have incorrectly blocked the nested
> assistant's own internal `skill:`/`tool:`/`doc_source:` hops, which need the broader ambient
> scope, not a scope narrowed to a selector that's never their prefix. A refusal there returns a
> blocked `InteractiveResponse` (not an exception, per the refusal-is-an-outcome principle), whose
> `.answer` surfaces as the tool's plain string result. Still pre-checked once, redundantly but
> cheaply, for least-privilege UX: a refused `assistant:<spec_ref>` excludes the tool from the
> parent's list entirely, matching the existing `skill:<name>` exclusion one level up.
>
> A misconfigured `spec_ref` (no `profile_registry`, or an unresolvable name) logs and skips that
> one skill rather than raising — a full nested assistant is heavier to typo than a catalog tool
> name, so failing soft is the safer default here (mirrors `_build_read_tools`'s posture, not
> `_resolve_tool`'s). 5 new tests (`tests/test_agent_composed_skill.py`, incl. one proving the
> nested assistant's own guardrail still fires — the exact thing a flattened skill would lose);
> full suite 2290 passed (was 2285), no regressions.
>
> **Deferred, noted not silently dropped:** no conversation/session continuity across turns for
> the nested call (each invocation is a stateless one-shot `respond()`); `Skill` doesn't validate
> that `spec_ref` is mutually exclusive with `tools`/`references`/`reads`/`instructions` (combining
> both silently ignores the latter, per `_build_parent_tools`'s branch order).

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

> **Status (2026-08-04): DONE for (b)/(c)/(d) of the 4 checks; (a) deliberately deferred
> (`ea1cb88`).** The architecture doc lists 4 publish checks: (1) references resolve — already
> done — (2) contracts coherent, (3) side-effecting capabilities opted-in, (4) eval set passes.
>
> - **References resolve, extended**: `validate()` now also catches a dangling `spec_ref` (the
>   P2-composition feature shipped just before this one) — a real gap, since spec_ref shipped
>   with no boot-time check of its own.
> - **Contracts coherent, concretized**: interpreted as "the composition graph must be a DAG" —
>   a skill's `spec_ref` forming a cycle (A wraps B wraps A) recurses forever at runtime, not just
>   misbehaves. New DFS cycle detection in `validate()`, reporting the actual cycle chain. Chose
>   this over a vaguer "declared input/output contract coherence" reading because it's concrete,
>   real, and directly enabled by the composition feature just shipped — not speculative.
> - **Eval set passes → a hook, not a hard-wire**: new `publish()` (async, wraps `validate()`)
>   takes an optional `evaluator(name, spec) -> reason | None` (sync or async, same block-reason
>   convention as a `GuardrailCheck`), aggregating every failing profile into one error.
>   Deliberately not wired to `jazzx_sdk.evaluation.EvaluationHarness` — that's pack/conductor-
>   shaped (`pack_id`, `golden_cases_dir`); no profile here has a bound golden-case-set concept of
>   its own, and assuming one would be an unjustified coupling. A caller with a real eval set
>   wires it in as a thin lambda over its own harness — the plan's own wording ("a hook to run")
>   asked for the extension point, not a full eval-binding subsystem.
> - **(a) side-effect classification — deliberately skipped**, per the plan's own explicit
>   sequencing warning: confirmed by grep, not assumed, that no `side_effect`/`SideEffect` concept
>   exists anywhere in `jazzx_sdk.tools` yet, and the Studio doc itself calls that tiering "the
>   largest open area in the design." Building it as a side effect of this gate would be exactly
>   the kind of ahead-of-its-real-shape work this SDK avoids elsewhere.
>
> `publish()` runs `validate()` first and lets it raise before touching the evaluator — fail fast
> on cheap structural checks before any (potentially LLM-driven) evaluation call, rather than
> forcing one aggregated exception across both. 8 new tests (dangling spec_ref, cycle, DAG
> false-positive check, publish sequencing, aggregation, sync-evaluator support); full suite 2298
> passed (was 2290), no regressions.

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

> **Status (2026-08-04): DONE (`18ff3d6`).** `scripts/new_assistant_scaffold.py <domain-name>`
> emits `profile/{profile.yaml,persona.md}`, `harness.py`, `handler.py`, `test_<domain>.py`, and a
> `README.md` under `examples/<domain>/`. Real design calls made, not guessed:
>
> - **Generated profile is deliberately skill-less.** `jazzx_sdk.llm.scripted.ScriptedLLM` only
>   covers the single-shot path (per its own docstring) — a skill-bearing default would need the
>   Agents-SDK `Runner` faked too, and the generator can't invent a real tool implementation for
>   an arbitrary domain name anyway. `loan_assistant` stays the reference for adding `skills:`
>   once a real tool exists; the generated README says so explicitly.
> - **The "six `HandlerContext` calls"** the plan's task names (from the external Studio doc, which
>   I can't read directly) are grounded in what `jazzx_sdk.handlers.HandlerContext` actually
>   defines, not guessed at: `ctx.message`, `ctx.runtime`, the three callables
>   (`extend_visibility`/`log_metric`/`update_status`), and building the `ResponseMessage` off
>   `ctx.message.header`. The generated `handler.py` marks all six inline (1-6), including
>   `ctx.extend_visibility` as the easy-to-miss one, per the plan's own callout.
> - **Verified end-to-end, not just written**: generated straight into the real `examples/`
>   (needed since the output imports as `examples.<domain>...`, not importable from an arbitrary
>   tmp dir), ran its own `pytest` — all 4 generated tests passed with no API key — then removed
>   it. Codified as `tests/test_new_assistant_scaffold.py`'s `generated_example` fixture (subprocess-
>   runs the generated test file, asserts `"4 passed"`) so this stays covered, not a one-off manual
>   check. 6 tests total (name normalization, file-set + no-leftover-template-artifact checks,
>   overwrite guard, the end-to-end run); full suite 2304 passed (was 2298), no regressions.
> - Real bug caught and fixed before shipping: an early draft escaped every markdown backtick in
>   the templates (`\`` instead of `` ` ``) out of habit — caught by grepping the generated output
>   for stray backslashes, not by assumption.
> - Not documented in `scripts/README.md` deliberately — that file's actual scope is the Docker
>   build/push/deploy scripts; `update_model_pricing.py` (an existing script in the same
>   directory) isn't listed there either, so adding an entry would be inconsistent with the doc's
>   real scope, not filling a gap.

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

> **Status (2026-08-04): DONE for the genuinely-shared half (`8cc91c8`); the other half correctly
> doesn't generalize.** Inspected `jazzx-assistant` directly (it's on disk at
> `/Users/sangit/src/jazzx-assistant`, not a hypothetical) rather than guessing at its shape:
>
> - **`mock_knowledge_hub`'s underlying data/logic was already solved, unbeknownst to the plan.**
>   `jazzx_sdk.clients.mocks.MockKnowledgeHubClient` already covers the full surface
>   jazzx-assistant's hand-rolled FastAPI app implements (`list_documents`/`download_documents`/
>   `read_entities`/`create_entity`/`read_entity`/`update_entity`/`read_ontology`/`get_collection`,
>   file-backed via its own `data_dir`) — confirmed by inspection, and jazzx-assistant's own pinned
>   japes rev (`v2.1.2`) already had every one of those methods per `git log`. It didn't need to
>   rebuild the mock's *logic*; it needed the mock reachable over **HTTP** (a devcontainer/browser/
>   non-Python caller can't reach an in-process Python object) — that's the real, narrow gap.
> - New `jazzx_sdk.server.create_knowledge_hub_mock_app(client=None, **client_kwargs)`: a FastAPI
>   adapter serving any `KnowledgeHubLike`-conforming delegate (a fresh `MockKnowledgeHubClient` by
>   default) over routes matching the real KH API 1:1 with `KnowledgeHubClient`'s own paths. A pack
>   gets a working HTTP mock "by configuration" (`data_dir=...`, or its own delegate) exactly per
>   the plan's acceptance criterion. Lives under `jazzx_sdk.server` (not `clients/mocks.py`) since
>   it needs fastapi, which tier-1/2 code must stay free of; wired into `server/__init__.py`'s
>   existing lazy-import dict, fastapi import kept function-local, matching `.web`/`.settings_api`'s
>   own convention — verified `tests/test_import_boundary.py` still passes.
> - **`mock_assistant_api` and the devcontainer/compose stack deliberately NOT generalized** — a
>   real correction to the plan's own framing, not a shortcut. `mock_assistant_api` mocks
>   jazzx-assistant's *own* conversation/message/chat/SSE ingress API for *its own* frontend; there
>   is no shared japes client behind it, so — unlike Knowledge Hub — every pack's own frontend
>   contract differs by definition and there's nothing to extract. The devcontainer/compose part is
>   deploy infrastructure, not SDK code; the new `create_knowledge_hub_mock_app` is exactly what a
>   pack's own compose file would point a container at, not a replacement for writing that
>   container. Forcing either into a shared japes primitive would have been exactly the kind of
>   speculative abstraction this SDK avoids elsewhere.
> - 11 new tests (`tests/test_mock_knowledge_hub_app.py`) — health check, security-context
>   enforcement + opt-out, collection/document/download/entity/ontology round-trips, 400/404
>   mapping (tested against a minimal fake for the two methods where the *default*
>   `MockKnowledgeHubClient` itself never returns falsy — a real, correctly-diagnosed behavior of
>   that mock, not an adapter bug), and `data_dir=` file-backed persistence. Full suite 2315 passed
>   (was 2304), no regressions.

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