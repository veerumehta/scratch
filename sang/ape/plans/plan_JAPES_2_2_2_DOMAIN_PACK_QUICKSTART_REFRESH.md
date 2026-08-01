# Plan: Domain Pack Quickstart refresh to 2.2.2

Author: Virendra Mehta · 2026-07-29
Repo: japes · Baseline: 2.2.2 (dev) · Docs-only, no version bump
Scope decision: patch in place. The structural split of this ~1,250-line file into a short quickstart plus siblings is deliberately deferred to a separate plan so the two changes stay reviewable independently.

Driver: `docs/DOMAIN_PACK_QUICKSTART.md` still opens with "**Architecture (JAPES 1.8.x)**" while `jazzx_sdk/_version.py` is at `2.2.2`. Everything the 2.0.0 line added (authority matrix, execution profiles, events and state machines, the governed automation chassis, refusal primitives, pack composition) and everything 2.1.x-2.2.x added (structured failure classification, the document chassis, the expression DSL, the finance period and vocabulary modules, guidance injection) is absent from the onboarding document a new pack team reads first. Two of its links are broken. One of its fabric accessors no longer exists and raises `AttributeError` if a reader copies it.

Second driver: the Jazz Assistant write-up (Notion, "Building the Jazz Assistant on JAPES based jazzx-sdk", 29 July 2026) is the first independent build on this SDK by an engineer who did not write it. Its observed numbers and its six adoption lessons are better evidence than the unsourced effort claims currently in this doc, and its gaps-closed-additively account is the honest thing to tell the next team. Folding it in is in scope.

## Grounding notes (verified 2026-07-29 against dev)

Read before editing. Several of these contradict what the current doc says, and one contradicts what a careless reader of the CHANGELOG would assume.

- `jazzx_sdk/_version.py` is `2.2.2`. `README.md` says "Current Version: 2.1.3 (July 2026)" and is itself stale; fixing the README version line is in scope for Phase 1 because the quickstart sends readers there first.
- There is no `CHANGELOG.md` at repo root. It lives at `docs/status/CHANGELOG.md`. The quickstart links `../CHANGELOG.md` twice.
- `docs/ARCHITECTURE.md` is listed twice in Essential Reading, as items 8 and 10, with different descriptions.
- **`fabric.policy` does not exist.** No attribute, no property, no alias; accessing it raises. The live accessor is `fabric.opa` (`OpaBundleStore`). The name survives only in two stale SDK docstrings; do not propagate them. The real accessors on `KnowledgeFabric` are `canonical`, `graph`, `rag`, `opa`, `collections`, `entities`, `guidance`, `db`, `blob`, `conversation`, plus properties `docs`, `pack`, `kh`. `platform_catalog.FABRIC_SURFACES` lists six of those; the catalog is the doc's source of truth for the enumerated list, not the full attribute set.
- **There is no class named `AuthorityMatrix`.** It is `AuthorityMatrixV2`, and it lives in `jazzx_sdk/fabric/canonical/authority.py` alongside `AuthorityCell`, `CellKind`, `DecisionClass`. `ExecutionProfile`, `SurfaceBinding`, `ClientOverlay`, `PolicyProfile` are in `jazzx_sdk/fabric/canonical/profiles.py`. `jazzx_sdk/authority/` is only the three-symbol resolver: `EffectiveAuthority`, `resolve_effective_autonomy`, `check_action`.
- `jazzx_sdk/fabric/pack/` is a back-compat shim re-exporting from `jazzx_sdk.pack`. The doc's `from jazzx_sdk.fabric.pack import DomainPackFabric` still works but should be rewritten to `from jazzx_sdk.pack import ...`. Both `DomainPackFabric(pack_yaml_path, fabric)` and `DomainPackHelper.from_yaml(manifest_path) -> DomainPack` exist with those exact names.
- **Pack composition has no symbol called `compose`, `capability`, or `seam`.** The code words are the manifest key `depends_on:`, `PackDependency` (`pack_id`, `version_range`, `fragments`), `FRAGMENT_KINDS = {"evidence_types", "policies", "playbooks", "mode_tuning", "ontology"}`, `PackManifestLoader.resolve_dependencies(packs_root)` and `.merged_assets(packs_root, kind)`. Only `playbooks` and `evidence_types` merge today; merged assets are stamped with `source_pack_id` / `source_pack_version`. The cross-pack *step* seam is separate and lives in conductor: `StepRegistry`, `StepImpl`, `PipelineStep.impl`.
- Conductor confirms `BaseConductor`, `ConductorPipeline`, `PipelineStep`, `Loop`, `ExecutionKind`, `Checkpointer` unchanged. New since the doc was written: `ConductorEngine`, `ConductorState`, `ConductorRun`, `ExecutedStep`, `StepEvent`, `StepObserver`, `SuspendRun`, `Suspension`, `DurableSuspension`, `SuspensionStore`, `SuspensionStatus`, `InProcessSuspensionStore`. `DbSuspensionStore` is deliberately not re-exported (SQLAlchemy opt-in); cite `jazzx_sdk.conductor.suspension_store_db`. The `TurnRun*` family is a different package, `jazzx_sdk/runs/`, not conductor.
- `EXPERT_REGISTRY` has exactly three keys: `policy`, `playbook`, `discovery`. The doc's Step 5 line "AML ships ~5 experts" describes a pack's own decomposition, not the SDK registry; leave the claim but make the distinction explicit so a reader does not go looking for five expert contracts.
- **Prompt resolution has two functions with two different layouts, and the doc conflates them.** `resolve_mode_prompt(mode_name, pack_id=None, pack_root=None)` searches `{pack_root}/prompts/{pack_id}/{mode}.md` then `{pack_root}/prompts/{mode}.md` then `jazzx_sdk/modes/prompts/fallbacks/{mode}.md`, and raises `FileNotFoundError` if none. `compose_mode_prompt(mode_name, *, pack_id=None, packs_root=None, base_dir=None)` is the two-layer composer, reading base `modes/prompts/{mode}.md` and appending `{packs_root}/{pack_id}/mode_tuning/{mode}.md` under a `## Domain Configuration` header. The doc's "Two-Layer Prompts" section describes `compose_mode_prompt`'s behavior but tells the reader to call `resolve_mode_prompt`. `make_prompt_resolver(packs_root, *, base_dir=None)` exists for the injection case.
- `jazzx_sdk/modes/prompts/` holds base prompts for **7 modes only** (`evaluator`, `governor`, `investigator`, `narrator`, `reasoner`, `sentinel`, `verifier`). `fallbacks/` holds all 13. The doc's `cat jazzx_sdk/modes/prompts/investigator.md` is valid, but any phrasing implying a base prompt exists for every mode is wrong.
- `InteractiveAgentSpec` has far more fields than the doc's Step 8 shows. Full list: `name`, `persona`, `model`, `max_tokens`, `max_turns`, `scope`, `knowledge`, `guidance_pack_id`, `guidance_applicability`, `skills`, `skill_defs`, `mcp_servers`, `conversation`, `compaction`, `temperature`, `reasoning_effort`, `service_tier`, `stream`, `stream_tool_events`, `guardrails`. **`stream_tool_events` is a real field** - it is the one-line switch the Notion write-up singles out. `InteractiveResponse` carries `answer`, `output`, `sources`, `guidance_refs`, `usage`, `blocked`, `block_reason`, `conversation_id`, `message_id`, `trace_id`.
- `examples/loan_assistant/` exists (`README.md`, `harness.py`, `test_loan_assistant.py`, `profile/profile.yaml`, `profile/persona.md`, `profile/skills/loan_lookup.yaml`). It is the worked version of the doc's Step 8 and the doc does not link to it.
- `Pack.agent` resolves the manifest's `agent:` key to an `InteractiveAgentSpec.from_dir(...)`, so the assistant-over-a-pack path is now first-class in `Pack` rather than something a pack wires itself.
- `jazzx_sdk.failures` exports `FailureCode` (10 members), `StructuredFailure` (`code`, `message`, `details`, `action`), `FailureRule`, `classify_failure`, `register_failure_rule`, `redact_secrets`, `redact_code_blocks`, `redact_fields`, `SENSITIVE_KEY_NAMES`.
- `jazzx_sdk.automation` exports `AutomationHandler`, `AutomationTrigger`, `AutomationRunRecord`, `Receipt`, `ReceiptStatus`, `IdempotencyStore`, `InProcessIdempotencyStore`, `EntityIdempotencyStore`, `GovernedAutomation`, `GovernedRequest`. `AutomationHandler` extends `BaseHandler`, not `Handler`. **`AutomationHandler.stage_output()` is still a TODO stub that only logs** - it does not write to the fabric. Do not document it as if it does.
- `jazzx_sdk.statemachine` is explicitly "admissibility at the write boundary, not orchestration" (`StateMachine`, `Transition`, `TriggerType`, `evaluate_guard`, `TransitionContext`, `TransitionResult`, `apply`). If it goes in the doc, that boundary has to go in with it, or packs will reach for it as a conductor.
- `AutonomyLevel` is a 5-member enum (`L0_ASSIST` .. `L4_SELF_IMPROVEMENT`) with `.to_numeric()` / `.from_numeric()`. The doc's governance manifest example uses `supported_autonomy_range: { min: 0, max: 2 }`; confirm against `DomainPackHelper.from_yaml`'s validation whether the numeric form is still what the manifest takes before touching that block.
- `jazzx_sdk.modes` is not imported by `import jazzx_sdk`, and `InteractiveAgent` is not a top-level export. Import paths in examples must be the real submodule paths.
- `pyproject.toml` names the package `japes`. The quickstart's `poetry add jazzx-runtime-sdk --git ...` is wrong.
- Unverified, verify before editing the blocks that use them: `CanonicalEvidenceObject`, `fabric.canonical.put_case_file` / `put_outcome` / `put_domain_pack` signatures, `DefaultDiscoveryExpert.from_config`, and whether the `v1.5 manifest minimums` block in the governance-manifest example still matches `DomainPackHelper`'s fail-closed check. Do not assume any of these from the current doc text.
- Separately: memory of record says DiscoveryExpert is intended to move from the Expert surface to an Automation-surface Conductor, and `experts/__init__.py` has not caught up. Phase 3 must not deepen the doc's investment in DiscoveryExpert-as-Expert; see the note there.

## Phase 1 - Correctness pass

The smallest change that stops the document actively misleading a reader. No new sections.

Anchors and edits:

- Header block, the line `> **Architecture (JAPES 1.8.x):**`. Rewrite the version marker to `2.2.x` and extend the substrate sentence to name what has since landed: authority and execution profiles, the governed automation chassis, structured failures, pack composition via `depends_on`, and the expression and finance modules. Keep the sentence's existing shape - it is a signpost, not a feature list; one clause per new area, no more.
- Both links to the root changelog: Essential Reading item 9 is `**9. [CHANGELOG.md](../CHANGELOG.md)**`, and Reference > Key Documentation is `- [CHANGELOG](../CHANGELOG.md) - Version history`. The link texts differ; the target is wrong in both. Repoint to `status/CHANGELOG.md` (both live under `docs/`, so the relative path is a sibling, not `../`).
- Essential Reading items 8 and 10 both point at `ARCHITECTURE.md`. Delete item 10 and renumber, or replace item 10 with `docs/LOCAL_TESTING.md` and `docs/SETTINGS_CONFIGURATION.md`, which exist and are not linked anywhere in this file. Prefer the replacement; the "only if extending the platform itself" framing item 10 carries is worth keeping on item 8 instead.
- Quick Start Step 1, `poetry add jazzx-runtime-sdk --git https://github.com/JazzX-LLC/japes.git`. The package is `japes`.
- Quick Start callout, "Do the 7-step design before tuning anything for real." There are eight steps. Either say eight or say "the design pass"; the latter survives the next step being added.
- Time-to-value header block, "**Time to production-ready domain pack:** 2-3 weeks". Handled in Phase 5, not here - it needs the Notion figures to replace it with, and an unsourced number should not be swapped for a differently unsourced number.
- All version markers of the form `v0.3.4+`, `v1.1.2+`, `v1.4.1+`, `v1.9.0+`. Each one is a claim about when a capability became available, and each is now old enough to be noise rather than signal for a team adopting at 2.2.x. Drop the marker where the capability is simply current, and keep it only where a reader on an older pin genuinely needs to know. Do not mass-delete without that judgment.
- The `**Breaking Changes:**` list under the fabric section stops at v1.4.1. Either extend it through 2.x or replace it with a pointer to `docs/status/CHANGELOG.md`. Prefer the pointer: this doc cannot stay a second changelog.
- `README.md`, the "Current Version: 2.1.3 (July 2026)" line. Out of this file but in scope, because Essential Reading item 1 sends every new reader there.

Acceptance: every relative link in the file resolves to a file that exists. No `1.8.x`, no `jazzx-runtime-sdk`, no `7-step`. The README version matches `_version.py`.

## Phase 2 - Fabric surface and prompt resolution

Two corrections where a reader who copies the doc gets a runtime error rather than a stale idea. These are separated from Phase 1 because they change example code, not just prose.

**Fabric.** The section "Using the Fabric in Your Domain Pack" opens with "five stores" and lists `policy - Rego/OPA governance bundles`. Rewrite against `platform_catalog.FABRIC_SURFACES`: `canonical`, `graph`, `rag`, `docs`, `entities`, `opa`. Mention `guidance` and `db` as additional accessors with a one-line purpose each, since both now carry documented pack-facing behavior (guidance injection; the `DbTurnRunStore` / `DbSuspensionStore` / `DbMaterializeManifestStore` pattern). Do not enumerate `blob`, `collections`, `conversation`, `pack`, `kh` here - they are real but not part of the pack-authoring path this doc teaches.

Prefer sourcing the list from `platform_catalog` in prose ("the catalog enumerates ...") so the next surface addition does not silently orphan this paragraph again.

**Prompt resolution.** Split the "Two-Layer Prompts: Base + Pack Tuning" section's single conflated story into the two real functions. State plainly which layout each expects, that `resolve_mode_prompt` raises `FileNotFoundError` rather than returning empty, and that base prompts exist for 7 modes while fallbacks exist for all 13. Fix the code block at the end of that section, which calls `resolve_mode_prompt` while describing composition. Fix the same call in "Your First Mode: Investigator" Step 2's `default_resolver`, and consider pointing it at `make_prompt_resolver` instead, which is what that closure is hand-rolling.

Then fix Troubleshooting item 1, "Mode prompt not found", which currently gives advice for only one of the two layouts.

Acceptance: no occurrence of `fabric.policy` remains. Every fabric accessor named in the doc exists on `KnowledgeFabric`. The prompt section names both functions, their layouts differ visibly, and the code blocks call the one they describe.

## Phase 3 - The 2.0-2.2 capability gap

New material. This is the bulk of the work and the part most likely to bloat the file, so the constraint is: **each capability gets a short subsection that says what it is, when a pack needs it, the exact import path, and a pointer onward. No tutorials.** A capability that needs a tutorial needs its own doc.

Place these as a new top-level section after "Using the Fabric in Your Domain Pack" and before "Testing Your Domain Pack". Suggested title: "Governance and execution primitives (2.0+)".

Subsections, in this order:

1. **Authority and execution profiles.** `AuthorityMatrixV2` / `AuthorityCell` / `DecisionClass` from `jazzx_sdk.fabric.canonical.authority`; `ExecutionProfile` / `SurfaceBinding` / `ClientOverlay` / `PolicyProfile` from `.profiles`; the resolver `check_action(...) -> EffectiveAuthority | Refusal` and `resolve_effective_autonomy(...)` from `jazzx_sdk.authority`. The point to land: autonomy is no longer a single ceiling on the pack manifest, it is resolved per decision cell from four layers, and the resolver returns a typed `Refusal` rather than raising. Note `AuthorityMatrixV2.from_csv` / `.from_yaml`, because that is how a pack actually authors one.
2. **Refusal as a return type.** `Refusal` / `RefusalClass` from `jazzx_sdk.fabric.canonical.refusal`. Cross-reference the finance and expression modules, which both return typed refusals rather than `None` or a silent zero. This is a design principle a pack team needs early, not an API detail: a governed function that cannot answer says so in the type.
3. **Structured failures.** `jazzx_sdk.failures`: `classify_failure`, `StructuredFailure`, `FailureCode`, `register_failure_rule` for pack-specific rules, and the three redaction helpers. Pair the redaction helpers with `agents.interactive.redact_before`, since that is the composition they exist for.
4. **State machines and the governed automation chassis.** `jazzx_sdk.statemachine` with its stated boundary quoted, then `jazzx_sdk.automation`: `GovernedAutomation` (idempotency, authority check, read-before-write drift detection, receipt, emit) and `GovernedRequest` / `Receipt` / `ReceiptStatus` / the three idempotency stores. Flag explicitly that `AutomationHandler.stage_output()` is a stub today.
5. **Pack composition.** `depends_on:`, `PackDependency`, `FRAGMENT_KINDS`, `resolve_dependencies`, `merged_assets`. State the current limit honestly: only `playbooks` and `evidence_types` merge. Mention `source_pack_id` stamping, since a pack team reviewing merged assets will want to know provenance survives.
6. **Durable conductor runs.** Extend the existing methodology Step 4 rather than duplicating it here: `SuspendRun`, `Suspension`, `SuspensionStore`, `DurableSuspension`, and the `jazzx_sdk.conductor.suspension_store_db.DbSuspensionStore` full path with its SQLAlchemy caveat. Also name `ConductorEngine` / `StepObserver` / `StepEvent`, which is how a pack streams step progress without the bespoke transport the assistant originally wrote.
7. **The document chassis.** `jazzx_sdk.agents.document` - `DocumentAgent`, `process_dir`, `process_package`, the `single` / `package` / `collection` / `refuse` routes, `DirectoryResult.failures` carrying `StructuredFailure`. This is a whole capability class the doc has no mention of, and a large fraction of pack work is document ingestion.
8. **Expressions and finance.** `jazzx_sdk.expressions` (`MetricDefinition`, `InputBinding`, `BindingKind`, `parse`, `evaluate`, `validate`) and `jazzx_sdk.finance` (`periods`: `Period`, `PeriodSet`, `LineSemantics`, `Assurance`, `construct_ltm`; `vocabulary`: `LineVocabulary`, `LineDefinition`, `resolve`). Frame these as domain-specific rather than universal - a financial-spreading pack needs them and an AML pack does not - so the doc does not read as if every pack must adopt them. The transferable point is the pattern: a pack's chart of accounts is declared, versioned data, not three private alias dicts.
9. **Guidance injection.** `fabric.guidance`, `GuidanceAsset` / `GuidanceStatus` / `GuidanceLifecycle`, `InteractiveAgentSpec.guidance_pack_id`, `InteractiveResponse.guidance_refs`, and the two backends (`rag` default, `eval_service`). Connect it to the existing methodology Step 6 - this is the mechanism by which the Curator's proposals reach a running agent, and Step 6 currently describes the compounding loop with no runtime hook.

On the existing "External Knowledge Acquisition with DiscoveryExpert" section: leave it functionally as-is, correct the version marker per Phase 1, and add one sentence noting the surface is expected to move from Expert to Automation. Do not expand it. Verify `DefaultDiscoveryExpert.from_config`'s signature before touching the code block; the doc's `kernel_client=ctx.runtime.kernel` inside `startup()` is suspicious because `ctx` is not in scope there.

Acceptance: each of the nine subsections is under roughly 15 lines. Every import path in them is copy-pasteable and resolves. No subsection contains a multi-step tutorial. The DiscoveryExpert section is not longer than it was.

## Phase 4 - The assistant surface and the worked example

Methodology Step 8 is the doc's weakest section relative to what the SDK now does, and it is the section the Notion write-up is direct evidence about.

- Retitle away from "(optional)" and drop the `v1.9.0+` marker. An assistant over a pack is a first-class delivery shape now, not an optional extra.
- Expand `profile.yaml` to show the fields a real profile uses: `model`, `skills` as named sub-agents with their own tool allow-lists, `stream_tool_events: true`, `guardrails` with `input` / `output` lists, and `conversation` / `compaction` for threaded sessions. Keep it one block; the point is that topology is data.
- Note `Pack.agent` - a pack manifest's `agent:` key resolves to an `InteractiveAgentSpec` automatically, so a pack ships its assistant rather than a sibling service wiring one.
- Add `InteractiveResponse`'s real fields, in particular `blocked` / `block_reason` (a guardrail decision is a normal return, not an exception) and `guidance_refs`.
- Link `examples/loan_assistant/` explicitly, and add it to Essential Reading beside `examples/document_analyzer/`. It is the worked version of this section and currently invisible.
- One paragraph on scaling down and up, which the existing section gets right: no `skills` gives grounded Q&A, `skills` gives the agentic loop, same profile shape.

Acceptance: a reader can get from Step 8 to a running assistant by opening one linked example. Every field shown in the `profile.yaml` block exists on `InteractiveAgentSpec`.

## Phase 5 - Fold in the Jazz Assistant evidence

The Notion write-up is one service by one engineer. It is real measurement of one build, not a platform guarantee, and the doc must say so wherever it uses the numbers. That framing is not a hedge - overclaiming here is exactly what makes the next team distrust the rest of the document.

- Header block. Replace "**Time to production-ready domain pack:** 2-3 weeks" with the observed shape, attributed: roughly 8 engineer-days to a grounded multi-agent vertical slice and 11 to a tested v1, from the first service built on the SDK by an engineer who did not write it. Keep "Time to first working handler: 30 minutes" - the Quick Start supports it.
- New short subsection at the end of the Crafting Methodology, before Prerequisites. Working title: "What one team's first build looked like". Carry across, compressed:
  - Design before code. Roughly two days locking layer ordering and failure semantics, and no tooling compresses it. This reinforces the methodology's own design-first stance with evidence.
  - The gate runs before grounding, so a refused turn costs zero retrieval. This is a concrete, transferable ordering decision and belongs near methodology Step 4's dominant-versus-secondary-workflow note.
  - Citations computed deterministically in code, never generated by the model. Same category - a guarantee you do not delegate to a model.
  - Test-to-product ratio above 1:1 (roughly 6,800 lines of tests and service doubles against the product code). Frame as where the saved time went, which is the doc's Step 6 argument.
  - Agent topology as data: the multi-agent architecture was 81 lines plus four config files. This is methodology Step 5's claim with a number behind it.
  - Budget an upgrade day. The SDK moves; a mid-build version bump cost about a day with the full suite passing. Report gaps upstream rather than working around them - three locally-built helpers were superseded by native equivalents and deleted, and two extensions went upstream.
- Prerequisites section. Add the staffing observation, carefully: one engineer can own a service of this shape end to end **given SME access and a platform layer that already exists**. The write-up itself insists on that qualifier and the doc must keep it.
- Do not import the with-and-without comparison table or the 60% / 3x figures. Those are that author's estimate of a counterfactual, clearly labelled as such in the source, and an onboarding guide is the wrong place for an adoption argument. Cite the observed column only.

Acceptance: every number carried across is attributable to the source and marked as one service's experience. No counterfactual estimates appear. The methodology's existing claims are supported by the new evidence rather than restated beside it.

## Phase 6 - Verification

- Every relative link resolves to an existing file. Mechanical check over the whole file, not just links this plan touched.
- Every `jazzx_sdk.*` import path in the document is importable at 2.2.2. Extract them and check; several predate the module reorganizations and will not have been caught by reading alone.
- Every attribute accessed on `ctx.runtime.fabric` exists on `KnowledgeFabric`.
- Every field shown in a `profile.yaml` or manifest YAML block exists on the model that loads it.
- Punctuation: the existing file uses em-dashes throughout, so added prose should match the file it lands in rather than the Notion convention. Do not mass-convert the existing ones; that is churn in a diff that needs to be readable.
- Diff review: confirm the file did not grow past roughly 1,400 lines. If it did, Phase 3 broke its own constraint and the overflow is the trigger for the deferred split plan rather than something to absorb here.

## Out of scope

The structural split into a short quickstart plus reference siblings - a separate plan, deliberately, so the correctness pass lands reviewable on its own. Any change to `jazzx_sdk/` itself; the two stale docstrings naming a `policy` store are noted in grounding but fixing them is a separate, trivial commit. Any JACI-side change. Rewriting `docs/ARCHITECTURE.md`, which has its own drift and its own plan to be written. Updating the Notion page.

## Sequencing

Phases 1 and 2 are independent and can land together as one correctness commit. Phase 3 is the largest and should land alone so it can be reviewed as an addition. Phase 4 depends on Phase 3 only for the guidance cross-reference and can otherwise land in parallel. Phase 5 touches prose in three places and should land last, because its framing depends on what Phases 3 and 4 actually claim. Phase 6 runs against the merged result, not per-phase.
