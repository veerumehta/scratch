# Plan: UAF Phase 1 — the uncontroversial additive deltas

> **Status (2026-08-12): not started.** Scoped from the Notion PRD *Unified Assistant Framework —
> Platform v2.0* (fetched 2026-08-12) read against this working tree (HEAD `90475da`, 2.3.6+).
> Every code claim below was read in the tree and re-verified by an independent adversarial pass.
> Companion doc: `UAF_PRD_vs_JAPES_Gap_and_Pushback.md` (the full goal-by-goal gap table and the
> four design objections). **This plan deliberately contains none of the four contested items** —
> see "Explicitly out of scope" at the end. Everything here is additive, defensible on its own
> merits regardless of how the contested questions resolve, and independently shippable.

Target version: **2.4.0** — additive throughout except Phase 5, which changes a default
(a safety-floor guardrail becomes auto-injected). A minor bump is the right gate for that, and
external consumers pin refs (macer, jazzx-assistant) or float on `main` (juno), so only jaci's
live path install sees it immediately.

## Framing: what "additive" means here, and why the split matters

The PRD reads as if UAF starts from zero. It does not — roughly 65–70% of its Phase 1 already
exists in `jazzx_sdk`, in several places in a more governed form than the PRD specifies. That
makes the PRD's goal list a bad work breakdown: it mixes (a) fields and wiring we should just add,
(b) things already built and mislabeled as later-phase, and (c) four design choices that contradict
load-bearing decisions in this tree.

This plan is only (a). Sequencing (a) first is not deferral of the argument — it is the opposite:
every phase below ships value while the contested questions are open, and none of them prejudges
an answer. Phase 3 in particular is written so that it stays correct whichever way the IO-contract
question goes, by adding the *record* and refusing to touch the *execution path*.

---

## Phase 1 — Manifest basic information (PRD Goal 1)

**Files:** `jazzx_sdk/manifest/assistant_manifest.py`, `jazzx_sdk/manifest/loader.py`,
`jazzx_sdk/manifest/spec_binding.py`

`AssistantManifest` today carries `assistant_id`, `archetype_type`, `pack_id`,
`pack_version_range`, `primary_persona`, `integration_surface`, `allowed_skills`,
`in_scope_action_classes`, `out_of_scope_action_classes`, `autonomy_level`,
`governance_profile_ref`, `profile_ref`. The PRD's mandatory bar needs three fields that do not
exist: a human `name`, a `description` (the prompt that drives routing, out-of-scope handling and
skill recommendation), and a conversational/non-conversational `type`.

1. Add `name: str` and `description: str`. Both required — that is the PRD's bar and there is no
   sensible default for either. `assistant_id` stays the machine identifier; `name` is display.
   → verify: a fixture manifest without them fails `AssistantManifest` construction with a field
   error naming the field.
2. Do **not** add a `type` enum. Conversationality is already derived from `integration_surface`
   via `spec_binding._CONVERSATIONAL_SURFACES` and gated on a `ConversationStore` being present.
   Expose it as a read-only property — `AssistantManifest.is_conversational` — delegating to that
   same constant, so there is exactly one definition and a third enum never appears next to
   `ArchetypeType` (7 values) and `SurfaceType` (5, with `GATEWAY` deliberately excluded from
   `_SURFACE_DEFAULTS`). Move `_CONVERSATIONAL_SURFACES` to `surface_types.py` if the import
   direction requires it; do not duplicate it.
   → verify: parametrized test over all five `SurfaceType` values asserting the property matches
   `_CONVERSATIONAL_SURFACES` membership, and that `bind_spec`'s surface defaults are unchanged.
3. `primary_persona` and `archetype_type` are declared and **read nowhere** in the SDK today
   (grep confirms: only their declarations in `assistant_manifest.py:34,37`). Do not wire persona
   into `bind_spec` in this phase — `bind_spec`'s docstring states persona/model/knowledge/
   compaction are "profile concerns the manifest has no opinion on," and changing that is part of
   the contested manifest-vs-profile question. Instead add a **cross-validation** check in
   `load_manifest`: if `primary_persona` is set and the resolved profile's persona is empty, fail
   with both names in the message. That converts a dead field into a checked one without deciding
   who owns persona.
   → verify: a manifest with `primary_persona` against a persona-less profile fails
   `load_manifest` with a message naming the manifest field and the profile.
4. Mandatory-bar gate in `load_manifest` (not in the Pydantic model — reference resolution is the
   loader's job by this module's own docstring): `allowed_skills` must be non-empty after
   narrowing. Today it defaults to `[]` and nothing rejects it, so a zero-skill assistant deploys
   and answers everything from the parent model. Fold the failure into the existing aggregated
   `ValueError` rather than raising early, matching the current fail-loud style.
   → verify: a manifest with `allowed_skills: []` fails, and a manifest with a skill list whose
   intersection with the profile is empty fails with the intersection shown.

**Acceptance:** a manifest missing name, description, or a non-empty effective skill list is
rejected at load with the exact field and reason; `is_conversational` has one definition; no
existing fixture in `tests/fixtures/manifest_binding/` breaks except by gaining the two new
required fields.

---

## Phase 2 — Close the three silent-degradation paths in the loader (PRD Goal 1)

**File:** `jazzx_sdk/manifest/loader.py`

The PRD's bar is "it never half-works silently." `resolve_pack` violates it three ways, in
increasing severity:

1. Missing pack → `logger.warning` + `return None`.
2. Unsatisfied `pack_version_range` → `logger.warning` + `return None`.
3. **Unparseable `pack_version_range` → `except InvalidSpecifier`, warning, and `return pack`
   anyway.** An assistant binds to a pack whose version constraint was never evaluated. This is
   the sharpest instance in the repo and it is a two-line fix.

Make all three raise. Keep `resolve_pack` async and opt-in as it is; the change is the failure
mode, not the call shape. The stated rationale for the current behavior is consistency with
`DomainPackStore.get` — that consistency is the wrong thing to preserve at a deploy gate, and the
plan should say so in the docstring rather than silently diverge.

→ verify: three tests, one per path, each asserting a raise with the pack id and the offending
range in the message. Then grep for `resolve_pack` callers and confirm none depended on `None`
(expected: none outside `manifest/` and tests).

**Acceptance:** no path through `load_manifest`/`resolve_pack` returns a usable object after
logging a warning about the thing that makes it unusable.

---

## Phase 3 — The skill record: metadata only, execution path untouched (PRD Goals 2, 4)

**Files:** `jazzx_sdk/agents/interactive/spec.py` (`Skill`),
`jazzx_sdk/agents/interactive/registry.py`, `jazzx_sdk/agents/interactive/inventory.py`

`Skill` carries `name`, `instructions`, `description`, `tools`, `references`, `reads`,
`mcp_servers`, `model`, `max_turns`, `tool_use_behavior`, `spec_ref`. The PRD's catalog entry
additionally needs: what it invokes, inputs/outputs, who can see it, and a version. All four are
absent.

Add them **as declared metadata only.** This phase must not touch `_build_parent_tools`. Tool
signature generation from declared IO is the contested item (see "Explicitly out of scope") and
tangling the two would make this phase unshippable while that argument runs.

1. `version: str` — content-addressed or explicit, but required to be stable and comparable.
   Packs are versioned today; skills are not, which makes "new versions don't break old ones"
   (Goal 2) unrepresentable.
2. `visibility: list[str] | None` — the build-time half of Goal 9. Roles that may see and attach
   this skill. `None` = visible wherever the registry is visible (preserves today's behavior for
   every existing registration).
3. `invokes: str | None` — an explicit statement of what is behind the skill, in the PRD's own
   "what's behind it" sense. Today it is *implied* by which of `tools`/`spec_ref`/`mcp_servers` is
   populated, which is exactly the kind of inference a catalog UI should not have to make.
4. `inputs: dict | None` / `outputs: dict | None` — JSON Schema. **Optional, unvalidated at
   runtime in this phase, and documented as such in the field docstring.** They exist so the
   catalog and the eventual docs generator have a source; nothing reads them yet.

Then: surface all four through `SkillInventory` / `build_inventory` / `catalog_text`, and add
`visibility` filtering to `SkillRegistry.names()` as an optional `roles=` argument (default `None`
= no filtering, so no caller changes).

Also add a skill **asset** channel to packs: `PackManifestLoader` has no skills accessor and
`merged_assets` covers only `playbooks`/`evidence_types` (`pack/manifest_loader.py:195-205`), so
`SkillRegistry.load_dir` is the only bulk path and a pack cannot ship skills. Note
`DomainPack.skill_bundle_version` already exists and is mandatory for a CERTIFIED pack
(`fabric/canonical/derived.py:626,674-682`) — the version field is there, the asset channel is not.
Follow the existing fragment-scoped, provenance-stamped, collision-fail-loud import discipline
exactly; do not invent a second merge rule for skills.

→ verify: round-trip a skill YAML carrying all four new fields through `load_dir` →
`build_inventory` → `catalog_text` and assert each appears; assert `names(roles=[...])` filters and
that `names()` with no argument is byte-identical to today's output for the existing fixtures;
assert a pack shipping two skill fragments with a colliding name fails loud with both provenances.

**Acceptance:** the catalog can answer every question the PRD's skill record asks, `Skill` has a
version, and `_build_parent_tools` is unchanged (diff it to prove this).

---

## Phase 4 — Build-time skill recommender (PRD Goal 3)

**Files:** new `jazzx_sdk/agents/interactive/recommend.py`; reference
`jazzx_sdk/agents/interactive/router.py`

`_IntentFirstRouter.select()` is ~40 lines: one structured LLM call over
`SkillRegistry.catalog_text(allowed)` with a confidence floor. The recommender is the same shape
with a different input — *(description, persona) → ranked skills* instead of *query → skill* — and
a different lifecycle (build-time, not per-turn).

Do not generalize the `Router` protocol to cover both. Routing selects for execution and is on the
hot path; recommendation ranks for a human and is not. Sharing the protocol would put build-time
concerns in the turn loop, which `router.py`'s own docstring argues against. Share the
`catalog_text` rendering and the structured-output pattern; keep the seams separate.

- Input: the manifest `description` (Phase 1) and persona text; the allowed-skill set after
  `visibility` filtering (Phase 3) — a builder is never recommended a skill their role cannot see.
- Output: ranked `(skill_name, score, one_line_rationale)`, plus the full unranked catalog so
  "View all skills" is always available. Never a filtered-down set masquerading as the catalog.
- Depends on Phases 1 and 3. Blocked on neither contested question.

→ verify: `ScriptedLLM` test asserting rank order for a hand-built catalog; a test asserting a
role-invisible skill never appears in either the ranked list or the full list; a test asserting the
full catalog is returned alongside the ranking.

**Acceptance:** given a description and persona, the top skills come back with rationales, the
full catalog is always available, and access control is respected.

---

## Phase 5 — The always-on guardrail floor (PRD Goal 8, the part we agree with)

**Files:** `jazzx_sdk/agents/interactive/spec.py`, `jazzx_sdk/manifest/spec_binding.py`,
`jazzx_sdk/agents/interactive/safety.py`

We reject guardrails-as-skills (a skill is model-selectable and therefore skippable, which is the
opposite of a floor — see the companion memo). We fully agree with the floor itself, and it does
not exist today: `spec.guardrails` defaults empty (`spec.py:187`), and `bind_spec` force-injects
only `SCOPE_GUARDRAIL_NAME="manifest_scope"`. An assistant can currently deploy with no guardrail
but the keyword scope check.

1. Register a platform-tier (tier 1) safety-floor `Guardrail` and force-prepend it in `bind_spec`
   next to the scope guardrail, using the same `_ensure_scope_guardrail_registered` pattern. Tier 1
   means a builder-tier registration cannot shadow it without an explicit override —
   `_TieredRegistry` already enforces this and is stricter than `TemplateRegistry`.
2. No manifest opt-out. Do not add a field for one; the absence of the field *is* the guarantee.
3. `safety.py:with_safety()` stays what it is — a prompt fragment. A prompt is not a control, and
   the plan should not let it be counted as one.
4. **This is the one behavior change in this plan.** Every existing consumer gains a guardrail they
   did not have. Land it with the minor bump, call it out in CHANGELOG, and run jaci's suite before
   pushing, since jaci's live path install picks it up immediately.

The red-teaming gateway itself is a separate deliverable: nothing in this repo integrates it (grep
finds only curator and test prose). Build the floor as a `Guardrail` whose `check` can delegate to
an external gateway — `registry.py:llm_guardrail` already demonstrates the shape — so the gateway
lands as a wiring change, not a framework change, and the seam is the same one a customer-specific
guardrail agent will use.

→ verify: a spec with `guardrails={}` bound through `bind_spec` has the floor present and running;
a tier-3 registration under the floor's name is refused without `allow_override=True`; the floor
short-circuits before grounding on the input phase (existing `_run_guardrails` ordering).

**Acceptance:** no manifest can produce an agent without the safety floor, and no builder-tier
registration can silently replace it.

---

## Phase 6 — Out-of-scope handling made configurable, still a guardrail (PRD Goal 7)

**File:** `jazzx_sdk/agents/interactive/scope.py`

The shipped default is weaker than the PRD assumes: case-insensitive substring matching on
out-of-scope action-class words that **defaults to allow** when nothing matches, `model=` accepted
and ignored, and the decline text hardcoded in `_check`. "A mortgage assistant never answers
what's the weather" does not hold today.

1. Make the decline message, tone, and an optional redirect target configurable on the guardrail
   (from the manifest/profile), replacing the hardcoded string. Additive, defaulted to today's text.
2. Make the LLM-backed check selectable rather than dead: `registry.py:scope_guardrail(llm, ...)`
   already exists and is the description-driven behavior the PRD wants. Wire `model=`/`llm=` through
   so passing one selects it, and **fail loud if a model is supplied and cannot be used** rather
   than silently keyword-matching — the current silent ignore is the worst of both.
3. Keep the default fail-open-to-allow behavior *for now* and document it explicitly as a known
   weakness with a pointer to this plan. Flipping it to deny-by-default is a real behavior change
   for every existing consumer and belongs with the description-driven check, not ahead of it.
4. Do not make out-of-scope handling a swappable *skill*. Same skippability objection as Phase 5.

→ verify: a custom decline message appears verbatim in the refusal; supplying a model routes to the
LLM check (asserted with `ScriptedLLM`); supplying an unusable model raises at build time rather
than degrading; the default path's behavior is byte-identical to today.

**Acceptance:** out-of-scope response text and strategy are configuration, the LLM variant is
reachable by configuration, and nothing silently ignores a supplied model.

---

## Phase 7 — Put the agentic path on the LLM Gateway (PRD Goal 6)

**Files:** `jazzx_sdk/agents/interactive/agent.py`, `jazzx_sdk/agents/service.py`,
`jazzx_sdk/agents/interactive/factory.py`

The PRD says every model call goes through the Gateway. Today that is *half* true, which is worse
than either extreme for reasoning about cost and failover:

- The skill-less/grounded path **is** on it: `respond` branches at `agent.py:236-243` →
  `_respond_single_shot` → `agents/service.py:218-256` delegates to `LLMManager` when there are no
  tools and one is wired; `interactive/factory.py:36` wires it on the manifest path.
- The **agentic/skills path bypasses it** via `build_agent`, so exactly the assistants the PRD
  cares about get no fallback chain, no `HealthMonitor` circuit breaker, and no `CostTracker`.

Also de-hardcode the `"gpt-5.2"` literal, which appears at **three** sites — `agent.py:578`
(the sub-agent model in `_build_parent_tools`), `agent.py:897`, `agent.py:915`. `spec.model`
itself already defaults to `None` (`spec.py:157`). Putting only `_build_agentic` on the Gateway
would leave every skill sub-agent on the literal, which is the failure mode to avoid.

1. Resolve the model through one helper that consults `spec.model` then the Gateway's
   `task_routing`, and call it from all three sites.
2. Route the agentic path's model calls through `LLMManager` where the openai-agents integration
   allows it; where it does not, record explicitly in the docstring which calls remain outside and
   why, so the gap is visible instead of assumed closed.
3. `llm/routing.py:RoutingStrategy` is exported and referenced nowhere else. Either consume it here
   or mark it deprecated with a pointer to `LLMManager`; do not leave two routing models in the
   tree — that is how the third one gets written.

→ verify: a cost-tracking test asserting a skills-path turn produces `CostTracker` entries (it
produces none today); a fallback test asserting provider failover on the agentic path; grep
asserting zero remaining `"gpt-5.2"` literals in `jazzx_sdk/`.

**Acceptance:** a skills-path turn is visible to `CostTracker` and survives a provider failure; no
model literal remains in the interactive path.

---

## Phase 8 — Session lifecycle (PRD Goal 10)

**Files:** new `jazzx_sdk/agents/interactive/session.py`; reference
`jazzx_sdk/runs/dispatcher.py`, `jazzx_sdk/fabric/conversation_store.py`

Conversation handling is ~80% there — `ConversationStore` with In-process/LocalFile/Compacting/
Masking variants, durable `SqlConversationStore` with a lossless archive/overlay split, declarative
`CompactionPolicy`, resumable durable SSE with cooperative stop and one-active-run-per-conversation.
What is missing is the *session record*: `session_id` is caller-supplied, there is no
`created_at`/`last_active_at`, no TTL, no expiry, no resume.

Do not invent the sweeper. `runs/dispatcher.py:68-75` already has
`Reaper(store, ttl_seconds, interval_seconds)` → `store.reap_stale(ttl)`. Copy that shape.

1. `SessionStore` alongside `ConversationStore` (not inside it — a session is lifecycle metadata,
   a conversation is content, and `SqlConversationStore` deliberately has no timestamps).
   `create` / `touch` / `get` / `expire`, with `created_at` and `last_active_at`.
2. Session-expiry TTL configurable, defaulted to today's effective behavior (no expiry) so
   existing consumers are unaffected until they opt in.
3. A `Reaper`-shaped sweeper over `reap_stale`.
4. Resume = `get` on a live session returning its conversation id; expiry is a state transition,
   not a delete, so an audit trail survives.

→ verify: a session expires after TTL and a subsequent turn starts a fresh conversation; `touch` on
each turn keeps it alive; the sweeper reaps only past-TTL sessions; default configuration changes
no existing test.

**Acceptance:** sessions start, resume, and expire on a configured TTL, with the default preserving
current behavior.

---

## Phase 9 — Reserve the reasoning stream event (PRD Goal 10, "reserve API space")

**Files:** `common/core/streaming/models.py`, `jazzx_sdk/agents/interactive/response.py`

`StreamEventType` has eight members and no reasoning/thinking event. Tool streaming is already
built (`stream_hooks.py`, `streaming/publisher.py`, `sse_reader.py`, journal resume), so only the
event type is missing — and the PRD asks only that space be reserved.

The catch: `StreamEventType` lives in **`common/`, a git submodule pointing at a separate
`JazzX-LLC/common` repo** with other consumers. Adding a member is a shared-package change, not a
japes-local one. Sequence it as such: propose the member upstream, land it there, bump the
submodule. Do not shadow the enum locally to avoid the coordination — a second definition of a
stream event vocabulary is exactly the kind of drift the symmetry principle in CLAUDE.md is about.

→ verify: a consumer that does not understand the new event type ignores it without error (forward
compatibility is the whole point of reserving); nothing in `jazzx_sdk/` emits it yet.

**Acceptance:** the event type exists in the shared vocabulary and is unemitted, so thinking-mode
can land later without a breaking change.

---

## Phase 10 — Trace the two decisions that are currently invisible (PRD Goals 6, 7, 8, 12)

**Files:** `jazzx_sdk/agents/interactive/agent.py`,
`jazzx_sdk/observability/{agent_hooks,mlflow_bridge}.py`; reference
`jazzx_sdk/agents/adjudication/tracing.py`

Two decisions leave no record: the router's skill selection (`_select_skills` returns a list and
records nothing; note it only runs on the agentic paths, `agent.py:938,975` — a skill-less
assistant never routes at all) and guardrail verdicts (`_run_guardrails` sets `blocked`/
`block_reason` on the response and `agent.last_guardrail_refusal`, nothing durable). The PRD needs
both for audit, and "which skill and why" is the single most-asked debugging question.

Scope this phase to **emission through the existing span path**, and leave the format-of-record
question out of it. There is already an agent-side precedent for span→`TraceStep` promotion:
`agents/adjudication/tracing.py:26 adjudication_name_patterns()` feeding
`spans_to_canonical_trace(name_patterns=...)`, added because `mode_map` keyed on span_type is too
coarse to tell two plain `LLM` spans apart. Follow it exactly.

1. Emit a span for the router decision carrying the candidate set, the chosen skill(s), the
   confidence, and the router name.
2. Emit a span for each guardrail verdict carrying guardrail name, phase, and refusal class.
3. Add an `interactive_name_patterns()` alongside the adjudication one so both promote through
   `mlflow_bridge` with the same mechanism.
4. Add a read-only trace lookup route over the existing `TraceStore` facade (`put_trace`/`trace`,
   `store/core.py:255`, already indexed on `workflow_id`/`case_id`/`status` with `Op`/`Page`
   support). Lookup only — the PRD asks for "a basic way to look traces up," and a write path here
   would prejudge the format question.

**Do not** extend `TraceStep` in this phase. It is `extra="forbid"` and deliberately has no
`domain_extensions` (only `CanonicalTrace` does — `trace.py:213-216,431`, which calls a per-step
extensions dict "the most common v1.5 failure mode"). The sanctioned per-step hatch is
`CanonicalTrace.metadata` keyed by `step_id` via `TraceStepContextHelper` (`trace.py:486-596`);
anything beyond that is a governed cross-team change to a schema declared frozen at Spec v1.5.
Whether a conversational turn becomes a `CanonicalTrace` at all is a decision, not a task — it is
listed below.

→ verify: a turn that routes and refuses produces both spans with the asserted fields; the promoted
`TraceStep`s carry distinguishable names via the new pattern list; the lookup route returns a
stored trace by id and 404s cleanly on a miss.

**Acceptance:** for any turn, the chosen skill and every guardrail verdict are recoverable from the
trace, and no frozen schema was edited to get there.

---

## Phase 11 — Require an invocation context at every service entry point (PRD Goal 9)

**Files:** `jazzx_sdk/authority/context.py`, `jazzx_sdk/server/app.py`,
`jazzx_sdk/runs/server.py`, `jazzx_sdk/handlers.py`

The hard part of RBAC is done and is better than the PRD describes: `PermissionScope`
(`admits()` exact+prefix, deny-wins, `narrow()` that cannot widen), `InvocationContext` with
ContextVar propagation and `descend()`, and real call sites — `_check_turn_entry`
(`assistant:<name>`), `_build_parent_tools` (`skill:<name>`, where **a refused skill is never even
exposed to the model**, then narrowed to exactly `tool:`/`ref:`/`doc_source:`),
`_build_composed_skill_tool` (`assistant:<spec_ref>`).

The gap is not the helper, it is the entry point. `admit_hop` fails open when no context is ambient
(`context.py:210-211`) while `check_hop` raises (`:166-173`). Nothing *requires* a service entry
point to establish a context, so an unauthenticated call path silently gets the fail-open branch.

1. Middleware on `server/app.py` and `runs/server.py` that establishes an `InvocationContext` from
   the already-captured identity headers (`handlers.py:148 capture_identity_headers`,
   `:321 KERNEL_HEADER_ALLOWLIST` = `x-security-context`, `x-request-project-id`) and **rejects the
   request** when it cannot.
2. Leave `admit_hop`'s fail-open semantics alone. It is the documented opt-in wrapper and in-process
   library callers depend on it. Fixing the entry point removes the exposure without breaking them.
3. Do not put `fabric/opa/store.py:OpaBundleStore` on this list. Its methods raise
   `NotImplementedError` deliberately — its own docstring (`store.py:12-18`) points at the working
   surface (`KnowledgeHubClient.get_policy_bundle`/`update_bundle`/`evaluate_policy`/
   `create_policy`) and notes bundle-upload is being superseded by canonical `Policy`. Treating it
   as a build item inverts a decision already made.
4. Keto is likewise **not** a build item: a full integration already ships in `common/core/keto/`
   (`authorization.py` `check_permission`/`batch_check_permission`/`require_project_permission`,
   `dependencies.py` FastAPI deps, `runtime.py` clients, `CommonSettings.keto`). Scope it as wiring.
   **Keycloak is genuinely absent** — no OIDC/JWT verification anywhere, identity is header-borne —
   and that is a real deliverable, but it is a service-boundary decision (who verifies the token)
   and is listed below rather than assumed here.

→ verify: a request with no identity headers is rejected at the entry point rather than reaching a
fail-open `admit_hop`; an in-process library caller with no ambient context still works unchanged.

**Acceptance:** no HTTP path reaches skill invocation without an `InvocationContext`, and
in-process callers are unaffected.

---

## Phase 12 — Manifest store with versioning and rollback (PRD Goals 1, 15)

**Files:** new `jazzx_sdk/manifest/store.py`; reference `jazzx_sdk/fabric/db`,
`jazzx_sdk/fabric/guidance/lifecycle.py`

`load_manifest(path, ...)` reads from a file. There is no hosted store, no version history, and no
assistant-level rollback — the only `rollback` in the repo is
`fabric/guidance/lifecycle.py:235 rollback(asset_id, to_version)`. Yet "keep the old version warm,
have a one-click way back" is a Phase-1 acceptance item in the PRD, and "rollback is tested and
documented, not theoretical" is one of its stated outcomes.

This is additive and, importantly, **agnostic to the contested manifest-vs-profile question**:
store the `(manifest, profile_ref)` pair as one immutable versioned record. If the two artifacts
later merge, the record shape still holds; if they stay separate, it holds too.

1. `AssistantManifestStore`: `put` (returns a new immutable version), `get(assistant_id,
   version=None)`, `history(assistant_id)`, `rollback(assistant_id, to_version)`.
2. Model the lifecycle on `GuidanceLifecycle`, which already has approve/deploy/rollback with
   content-addressed versions — do not design a second lifecycle vocabulary. Reuse its status
   progression shape.
3. Every `put` runs the Phase 1/2 validation. An unstorable manifest is a feature, in the same
   spirit as `ProfileRegistry`'s unpublishable profile.
4. `rollback` is a new version pointing at old content, never a mutation or a delete — the audit
   trail is the point.

→ verify: `put` → `rollback` → `get` returns the prior content as a new version with history
intact; an invalid manifest is rejected by `put` with the Phase 1 aggregated error; concurrent
`put`s do not interleave versions.

**Acceptance:** an assistant's configuration history is queryable and reversible, and rollback is
exercised by a test rather than described in a runbook.

---

## Phase 13 — Generalize the A/B harness to manifests, wire the ≥95% gate (PRD Goal 15)

**Files:** `jazzx_sdk/evaluation/guidance_ab.py`, `jazzx_sdk/evaluation/pass_bars.py`

Almost everything the migration proof needs exists: `EvaluationHarness` /`EvaluationConfig`/
`EvaluationResults.pass_rate`, `golden_cases/` with `TruthMode` (including
`SHADOW_OBSERVATIONAL`), content-hash case-set lineage and `diff_case_sets`, `ExperimentRun` keyed
on `case_set_hash`, `l3_review/` (`L3Review`, `ReviewAgreement`) for SME comparison, and
`pass_bars.py` (`PassBar`, `run_corpus_eval`, `CorpusEvalResult.bars_met`) — which is literally the
≥95% mechanism the PRD's success metric asks for.

The one gap: `guidance_ab.py` is parameterized on a **guidance asset** (`validate_guidance(asset,
...)`), not on two specs or manifests. Generalize the comparison subject.

1. Extract the baseline-vs-candidate-on-identical-cases core so the subject is a callable, then
   express both the existing guidance case and a new manifest-vs-manifest case on it. Keep the
   per-case `over_fired()` regression flag — per-case regression detection is the part that makes
   an aggregate pass rate trustworthy.
2. Wire a `PassBar` for the PRD's ≥95% match so the gate is executable, not prose.
3. Do not build shadow-traffic teeing. `SHADOW_OBSERVATIONAL` exists as a case *label* only; a real
   tee is a deployment concern with nothing in this repo to build on, and pretending otherwise
   would make the plan's estimate wrong.

→ verify: the existing guidance A/B tests pass unchanged against the refactored core (this is the
regression proof for the extraction); a manifest-vs-manifest run over one case set produces two
`ExperimentRun`s sharing a `case_set_hash`; a candidate below the bar fails `bars_met`.

**Acceptance:** "old assistant vs new assistant on the golden set, ≥95%, with per-case regressions
named" is one command, and the guidance A/B path is unchanged.

---

## Sequencing

Phases 1–3 are the spine: Phase 4 needs 1 and 3, Phase 12 needs 1 and 2. Everything else is
independent and can run in parallel by owner:

- **Manifest track:** 1 → 2 → 12
- **Catalog track:** 3 → 4
- **Guardrail track:** 5 → 6 (6 is small; 5 carries the behavior change and the version gate)
- **Independent, any order:** 7 (Gateway), 8 (sessions), 10 (trace spans), 11 (context middleware),
  13 (A/B harness)
- **Cross-repo, start the conversation early:** 9 (`common/` submodule)

Phase 5 is the only phase that changes existing behavior, so it sets the version bump; land it
early enough that jaci exercises it for a while before anything promotes.

Per CLAUDE.md: full suite green after every phase (baseline 2589 passed, 3 skipped), `-X importtime`
diffed against `docs/_importtime_baseline.txt` for any phase touching import structure (3, 8, 12),
CHANGELOG updated per phase, `>=` dependency floors, and nothing pushed or committed without the
push gate.

---

## Explicitly out of scope — and why

**The four contested design items** (full argument in the companion memo; they belong in a design
note that gets settled, not a build plan):

1. **Guardrails as skills.** A skill is model-selectable and therefore skippable, which contradicts
   the PRD's own "always on, no manifest can turn it off." Phase 5 delivers the floor the PRD
   actually wants without this.
2. **"One shared orchestrator, builder picks only the LLM."** Understates four existing
   orchestration layers (pluggable `Router`, `tool_use_behavior`, the 13-mode registry with
   `ModeKind.ORCHESTRATOR`, and `conductor/` with pipeline/fanout/ensemble/replication/suspension).
   The right wording is "one *default* orchestrator; routing is a named registered policy" —
   `intent_first`, the PRD's own Phase-2 classifier routing, already ships today.
3. **"An assistant is one manifest."** Collapses the deliberate governance-envelope /
   execution-profile split that `bind_spec` enforces fail-closed ("widening is a certification
   violation"). This is `Japes_Enhancement_Backlog` P1, open since 2026-08-03, and it is now on the
   critical path: **settle it before Builder Studio starts UI work**, because reworking an authoring
   form after the schema question costs more than deciding first. Note also that the PRD's manifest
   omits `autonomy_level`, which is mandatory today and load-bearing in `authority/`.
4. **Per-skill IO contracts and generated tool signatures.** "No forced common IO shape" reads in
   code as *no schema at all*, which contradicts Goal 14's need for declared inputs and outputs per
   endpoint. Our position: the record carries JSON Schema **auto-derived from the wrapped
   agent/tool/process**, and the def-backed and `spec_ref` branches of `_build_parent_tools` get
   real typed signatures — generalizing what the bare-name branch (`agent.py:667-671`) already does,
   since it is the one shape that keeps its native signature today. Phase 3 adds the record fields
   so this stays unblocked; it deliberately does not touch execution.

**Blocked on someone else, not on us:**

5. **Per-skill action APIs and the multi-tenant assistant-id-addressed service.** This is the PRD's
   actual Phase-1 product outcome, and the substrate is closer than it looks: `ProfileRegistry`
   already hosts many agents against one shared `SkillRegistry`, `build_from_manifest` produces a
   live agent with no handler code, and `GovernedRouter.governed_post/get` supplies the governed
   route primitive (X-Trace-Id required, Idempotency-Key on mutating, `cell_ref`). But
   `server/app.py` is one handler per process with no assistant lookup, `add_api_route` appears
   exactly once in the tree (`governed_http.py:100`), and route generation needs item 4 settled
   first. Sequence it immediately after item 4, not before.
6. **Starting a process.** Goal 5 makes skill→process one of three first-class cases, and "Fetch
   Loan Conditions" is both the async exemplar *and* the non-conversational Phase-1 proof. Nothing
   in this repo can start a BPMN process: `tools/platform/workflow.py` is read-only (four functions),
   and the only `runtime/process-instances` touch repo-wide is a GET on `.../variables`
   (`workflow.py:240`) — no POST anywhere, including `common/` and `tests/`. Whether Kernel owns
   this or a new client does is an unresolved cross-team dependency. **Name an owner before Phase 1
   is committed to**, or two of the PRD's acceptance criteria have no backend.
7. **Keycloak / OIDC.** Genuinely absent; identity is header-borne. Who verifies the token is a
   service-boundary decision, not a japes delta.
8. **Multi-session and user-level memory.** Correctly deferred by the PRD and by this tree —
   `spec.py:184` already reserves `memory: MemoryBinding` for the Memory Fabric. Note one nuance for
   whoever picks it up: `MaskingConversationStore`/`OutputMaskPolicy` already enforces "what the
   user may see" at the store layer, which sits awkwardly with the PRD's "that is not memory at
   all — it is checked live per request."
9. **The trace format of record.** Whether a conversational turn becomes a `CanonicalTrace` (via
   `mlflow_bridge`, whose `spans_to_canonical_trace` + `name_patterns` already do the mechanical
   work) or gets a third format. Cheap to decide now, expensive later, and Phase 10 is written to
   stay correct either way.

**Already built — do not re-plan these.** The PRD defers nine things this tree already has:
Governor + Verifier machinery (`modes/operational/{governor,verifier}.py`, `GovernorDecision`/
`VerifierReport`, the 5-level `AutonomyLevel` ladder, `authority/resolver.py`,
`automation/governed.py`, `server/governed_http.py`); classifier-based routing
(`router.py:intent_first`); golden-dataset simulation (`harness/`, `golden_cases/versioning.py`,
`experiment/`, `pass_bars.py`); the approved-feedback learning loop, governed end to end
(`fabric/guidance/` with lifecycle, `GuardrailGuidanceValidator`, `ConflictReport`, expiry,
provenance, effectiveness attribution, and drafts-only Curator); domain packs for language and
state-policy variability (`pack/manifest_loader.py` fragment overlays, `regulatory_context`,
`fabric/canonical/policy.py` jurisdiction); tool streaming (`stream_hooks.py`, `streaming/`,
journal resume); skill certification skeleton (`certification_status`, `_TieredRegistry`);
A/B comparison (`guidance_ab.py`); and effectively assistant package export (`launcher.py`'s
one-image/three-shapes `JAPES_RUN_MODE`). The PRD correctly identifies only two things as missing
that really are: BYO-framework adapters (no LangChain/Semantic Kernel/Claude-SDK adapter anywhere)
and skill versioning (Phase 3 here).

**One PRD claim to correct in the PRD itself:** *"every new assistant needs its own code package on
Azure"* is true of the three legacy assistants and false as a description of the required work. In
this tree an assistant is already YAML — an `AssistantManifest` plus a profile directory plus a
pack, bound at runtime by `build_from_manifest`, many per process via `ProfileRegistry`. What is
genuinely absent is a hosted manifest store (Phase 12) and an assistant-id-addressed HTTP surface
(item 5). The distinction matters for the estimate: "8 days and 81 lines of code" is the legacy
path's cost, not this SDK's.
