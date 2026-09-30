# Plan: declarative grounding for the chat lifecycle

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: G1-G4 built on `v2.5.7` 2026-09-30 (`480aa8be`, `9d9d492b`, `ec25d4a7`, `7d5832a7`,
`347e3be3`), under review. Not built: the `evidence` kind (`pipelines` cannot import `pack`), per-
source `tools`/`context` switches, source-vs-tool name lint. Plan dated 2026-09-30. Follows the chat runtime coordinator plan's Phase C (C7
declared the gate and turn policies; ground was left open). Prior art read first:
`plan_chat_runtime_coordinator.md` (C5 sessions, C7), `note_chat_pipeline_vs_assistant_turn.md`
("ground is a provider, not context"), `note_assistant_turn_requirements.md` (R6: per-source
progress and `required=`), `plan_assistant_ws_fabric_enablement.md` (grounding maps onto
`fabric.docs.materialize` / `fabric.entities`), `status/done_chat_turn_engine.md` (jazzx grounds
through a custom `ground` override emitting its own `GroundedContext`).

## What exists

japes:
- `ground_step` over `ChatTurn.sources` (label -> (thunk, default)) runs sources concurrently
  through `gather_degrading`, reports `SourceProgress`, and raises `GroundingRequiredError` for a
  required source that degraded. It writes `turn.grounded`, which **nothing reads**: the reference
  answer passes the agent only the messages.
- `InteractiveAgent` grounds on its own from `knowledge:` bindings (`resolve_knowledge`:
  sequential, no progress, no degrade or required semantics), injecting text into the system prompt;
  `Skill.reads` gives a skill `list_/read_/search_` tools over `fabric.docs`.
- Fetchers: `fabric.docs.materialize` (entity documents to a directory, concurrent, retried),
  `fabric.entities.filter/list_all`, `fabric.canonical.find`, `fabric.rag.search` (returns
  `Source`s), `pack.evidence_tools` connectors. `build_directory_tools` gives list/read/search over
  local directories. `runs.session` gives `ChatSession.resource` (a `SingleFlight`).
- Registries of declared kinds (`NamedRegistry` + an entry point + `freeze`): conductor kinds,
  guardrail kinds, evidence connectors.

jazzx-assistant (`origin/dev`): five hard-coded sources (findings, conditions, loan documents, LOS
entities, guidelines) fetched concurrently into a per-session directory
(`work_dir/{findings,conditions,LOAN,LOS,GUIDELINES}`), cached per session through a hand-built
single-flight (a degraded result is not cached), with ordered progress lanes. The model gets both:
manifests and indexes as skill references (prompt text) and twelve directory-bound tools, each
skill seeing only its own sources. The queue path grounds per turn into a temporary directory. Only
guidelines are optional; a total failure is a `grounding_failed` turn.

## The design

One concept: a **ground source**, declared by name with a `kind`, that produces a
`GroundedSource` for a turn. The lifecycle's existing `ground` stage runs the declared sources;
the answer stage receives what they produced. Nothing new executes sources: a declaration
compiles to `ChatTurn.sources`, so `ground_step`'s concurrency, progress, degrade and `required`
semantics apply unchanged.

### G1. Kinds, results, workspace, caching (`jazzx_sdk.pipelines.grounding`)

- `GroundedSource`: `name`, `kind`, `context` (prompt text: an index or manifest, may be empty),
  `directory` (files the source wrote under the workspace, or None), `sources` (`Source`s for
  citation), `count`, `degraded`, `detail`.
- `GroundedContext`: the turn's `GroundedSource`s by name, `failed` (names that degraded), and
  `workspace` (the directory root). This is what `ground` emits and `turn.grounded` holds, in place
  of today's untyped mapping; the reference answer reads it.
- `GroundKinds(NamedRegistry)`, entry point `jazzx_sdk.ground_kinds`, built-ins registered first
  and not overridable, then frozen: the conductor-kinds shape. A kind is
  `factory(config, *, fabric, scope, workspace, turn) -> async fetch(progress) -> GroundedSource`
  plus a static `problems(config)` for lint, as `conductor_problems` and `EvidenceTools.problems`
  do. A pack never names Python.
- Built-in kinds, each a thin adapter over an existing fetcher:
  - `documents`: `fabric.docs.materialize` of the entities `entity_type` + `where` names in
    `collection`, into `<workspace>/<name>/`; context = a manifest; directory tools.
  - `entities`: `fabric.entities.filter` per `entity_types`, one JSON file per entity; manifest;
    directory tools.
  - `canonical`: `fabric.canonical.find(model, where, limit)`, as JSON context text (what a
    `knowledge:` canonical binding does today).
  - `rag`: `fabric.rag.search(collection, query=the turn's message, limit)`, snippets as context
    and `Source`s. Query-dependent, so turn-scoped.
  - `evidence`: `pack.evidence_tools` types (fixture or connector), as JSON context.
- `$scope` substitution for every config value (`knowledge.subst`), and `admit_hop` checks
  (`documents:` / `entities:` / `canonical:` / `rag:` hops) before a fetch, as `resolve_knowledge`
  does.
- Workspace: `GroundWorkspace(root)`, an async context manager making `<root>/<id>/` and removing
  it on exit. Turn scope: one per turn (the queue path's `mkdtemp`). Session scope: owned by the
  `ChatSession` and removed on close (the socket path's `work_dir`).
- Caching per source, `cache: session | turn` (default `session` for `documents`, `entities`,
  `canonical`, `evidence`; `turn` for `rag`). A session-scoped source runs through
  `session.resource(f"ground:{name}", fetch, cacheable=lambda r: not r.degraded)`: started once,
  joined by concurrent turns with replayed progress, a degraded result not kept. Without a session,
  every source is turn-scoped.

### G2. Delivery to the model

- `InteractiveAgent.respond` / `respond_stream(grounding=GroundedContext | None)`:
  - each source's `context` is appended to the system prompt beside the knowledge-binding context,
    one `_GROUNDING_PREAMBLE` for both;
  - a source with a `directory` gets `list_<name>` / `read_<name>` / `search_<name>` tools
    (`build_directory_tools`, read cap from config), named as `Skill.reads` tools are;
  - its `sources` join the response's `Source`s for citation.
- `Skill.reads` may name a ground source: that skill's sub-agent gets that source's tools and
  context, as jazzx gives its loan and policy agents different sources.
- The reference `answer_step` / `answer_stream_step` pass `turn.grounded`. A custom answer reads it
  as before.

### G3. Declaration and hosting

- `ChatLifecycleSpec.ground`: `sources: {name: {kind, required, cache, tools, context, ...kind
  config}}`, strict per kind (each kind validates its own config). `declared_lifecycle` compiles it
  into a `GroundPlan` whose `sources_for(turn, fabric, session)` fills `ChatTurn.sources`.
- Progress: `ground_step` publishes each `SourceProgress` as a typed event
  (`{"ground": {"active", "source", "failed"}}`, `ephemeral`), which is what jazzx's status lanes
  read.
- A required source that degrades is `GroundingRequiredError`, a `ChatError` with
  `code="grounding_failed"`, `category="resource"`, as jazzx's turn fails today.
- Plato: a process-local `SessionRegistry` keyed by (tenant, assistant, session id) for
  session-scoped sources, reaped with the session TTL; the workspace root from settings. Pack
  check lints a declared ground (unknown kind, a kind's own problems, a `Skill.reads` naming no
  binding or source).

### G4. One grounding mechanism

`knowledge:` bindings compile into ground sources (`canonical` and `documents` kinds) when a
profile declares a lifecycle, so an agent run through the lifecycle has one grounding path with
progress, degrade and `required`; `InteractiveAgent._ground` stays as the path for an agent called
directly. A binding and a ground source with the same name is a lint error, not a double
injection.

## What jazzx-assistant changes (and why ours is better)

- Its five sources become declared sources: loan documents and guidelines are `documents`, LOS is
  `entities`; findings and conditions become its own registered kinds (entry point
  `jazzx_sdk.ground_kinds`), or `entities` with a manifest renderer if they fit. Gains: every source
  can be `required` or optional per assistant (today only guidelines are optional), and the list is
  data, so a second assistant reuses it without code.
- `start_grounding` / `GroundingRun` become `ChatSession.resource`: the same start-or-join,
  replayed progress and not-caching-degraded, maintained once.
- Its twelve directory tools and the skill references (`document_manifest`, `findings_index`)
  become each source's generated tools and `context`, scoped per skill through `Skill.reads`.
- The queue path uses the same declaration with turn scope, instead of a second code path.
- Its `GroundedContext` maps onto ours field for field (dirs -> `directory`, indexes -> `context`,
  `failed_sources` -> `failed`); the findings store and document mappings ride `detail`.

## Open questions

- Invalidation: jazzx never re-grounds a cached session source. A per-source `ttl_seconds` is a
  cheap addition; not built until something needs it.
- The `rag` kind's query is the turn's message; a declared query template is the obvious extension.
- Tool naming when a source name collides with a skill or binding tool name: lint, refuse.
