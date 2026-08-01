# JAPES v1.13.0 - Governed Guidance Assets (Learning Loop)
## Claude Code Handoff

**Author:** Virendra Mehta
**Repo:** japes (`jazzx_sdk/`)
**Revision:** r3 - r2 folded in review corrections (lifecycle on `jazzx_sdk.statemachine`,
retrieval distinguishes access denial from transient failure, validator composes the
guardrail primitives, `scope` renamed `applicability`). r3 resolves the residual judgment
call: validator and conflict blocks on deploy are typed `Refusal`s, not exceptions -
consistent with the 1.10 refusal stance ("a refusal is a successful, auditable outcome,
never an exception") and the `GovernedAutomation` precedent (its drift conflict is a
`Refusal` with the receipt in `domain_extensions`; `server.py` maps returned Refusals to
HTTP statuses). Exceptions stay reserved for infrastructure and programming errors.
**IIF v1.5 reference:** Schema Spec §4 (GuidanceRef sub-schema), §6 (Outcome), §10.2 (Override Learning Rate), §10.4 (Guidance Effectiveness)
**Requirements input:** Jazz Assistant Learning Layer Track 1 PRD (Feedback-Driven Improvement, Notion). Per platform philosophy, the PRD is a requirements input to SDK evolution, not a Jazz-specific deliverable. Nothing mortgage-specific enters `jazzx_sdk/`.

---

## Why this matters

The EVOLVE loop in the SDK today has an ingress (`Feedback`/`FeedbackStore`), refinement
(`feedback_quality`), and a whole-prompt improvement path (`optimize_prompt` +
`PromptRegistry`). What it does not have is a home for the *unit of learning* the Track 1
PRD needs: a scoped, SME-approved guidance asset that is retrieved and injected per query,
not baked into a prompt.

`CanonicalDecision.guidance_refs` already exists and points at guidance assets by
`asset_id`/`asset_type`/`version` - but nothing in the SDK produces, governs, or retrieves
the assets those refs reference. Closing that gap makes Override Learning Rate (§10.2) and
Guidance Effectiveness (§10.4) computable, and gives every domain pack (Jazz Assistant, AML
playbook revisions, CID) the same governed learning loop without pack-side machinery.

The PRD's mortgage specifics (applicability = loan program / borrower type / goal,
personas, Feedback Manager UI) are all pack config or client-surface concerns. What
generalizes into the SDK: the asset object, its lifecycle, scoped retrieval, safety
validation and conflict seams, before/after validation, and compounding metrics.

---

## Current state (grounded 2026-07-15, v1.9.9)

- `jazzx_sdk/_version.py` - `__version__ = "1.9.9"`. Plan docs exist for 1.10.0
  (governed value/refusal), 1.11.0 (authority matrix / execution profile), 1.12.0
  (events / state machines / automation chassis). This plan takes the 1.13.0 slot and
  **depends on 1.10.0 (Refusal) and 1.12.0 (statemachine) having landed** - both are
  already present in the tree (`fabric/canonical/refusal.py`, `jazzx_sdk/statemachine/`).
- `jazzx_sdk/statemachine/` - `StateMachine`/`Transition` tables loaded as data
  (`from_records`/`from_csv`; trigger_type, guard, actor_class, cell_ref, emitted_event),
  and `engine.apply(machine, current_state, trigger, ctx) -> TransitionResult | Refusal` -
  a pure admissibility check enforcing terminal-immutability, human-only triggers,
  cell_ref -> authority resolver, fail-closed guards, and event emission. **The guidance
  lifecycle is expressed on this - not as a second mechanism.**
- `jazzx_sdk/agents/interactive/registry.py` - `Guardrail` (named check + phase),
  `GuardrailRegistry`, `llm_guardrail(llm, policy, ...)` and
  `scope_guardrail(llm, allowed_topics, ...)` - async LLM-classifier guardrails returning
  a block reason or None. **The guidance validator composes these.**
- `jazzx_sdk/clients/knowledge_hub_client.py` - `KnowledgeHubAccessError` (HTTP 401/403),
  raised precisely so a denial is never conflated with "not found"/"no results". The
  client's own except blocks re-raise it. **Guidance retrieval must preserve this.**
- `jazzx_sdk/evaluation/feedback.py` - `Feedback` (source/reaction/rating/text/category +
  subject/trace/decision/outcome/pack links), `FeedbackStore` ABC, `InProcessFeedbackStore`,
  `render_feedback`, `Feedback.to_signal()` -> `ImprovementSignal` for Curator routing.
  Durable backend in `feedback_db.py`.
- `jazzx_sdk/evaluation/feedback_quality.py` - `assess_feedback_quality`,
  `extract_actionable_items` (plain `structured_call` operations over rendered feedback).
- `jazzx_sdk/evaluation/optimization.py` - `optimize_prompt`, `ReflectiveOptimizer`,
  `PromptOptimizer` protocol, `TrainCase`, `synthesize_cases_from_feedback`.
- `jazzx_sdk/evaluation/prompt_registry.py` - `PromptRegistry` protocol, content-hash
  versioning (`content_version`), movable aliases, `promote()`. Approval gating is
  explicitly the caller's concern. This is the versioning pattern to mirror.
- `jazzx_sdk/evaluation/experiment/schema.py` - `ExperimentRun` with `dimensions` and
  content-addressed `case_set_hash`.
- `jazzx_sdk/fabric/canonical/decision.py` - `GuidanceRef` (asset_id, asset_type, version,
  relevance_score) and `CanonicalDecision.guidance_refs`.
- `jazzx_sdk/fabric/canonical/outcome.py` - `Outcome` with `learning_signals`,
  `human_override`, no guidance linkage (join through `decision_id` instead - see design
  decision 6).
- `jazzx_sdk/fabric/rag/store.py` - `RAGStore` with `search(collection_id, query, limit,
  metadata_filters)` and `retrieve_by_metadata`. Backing for the durable guidance store.
- No `guidance` or `learning` module anywhere under `jazzx_sdk/` (glob-verified).

---

## Design decisions

1. **New fabric store: `fabric.guidance`.** Guidance assets are governed knowledge assets
   queried at runtime - that is a fabric store, sibling to `rag`/`policy`/`docs`, not an
   evaluation concern. Module `jazzx_sdk/fabric/guidance/` exposed as
   `ctx.runtime.fabric.guidance`. Reference impl in-process; durable impl composes
   `RAGStore` (one dedicated collection, assets as documents with structured metadata) so
   no new Knowledge Hub client surface is needed.

2. **Applicability is pack-defined config, not schema.** The asset field is named
   `applicability: dict[str, str]` - NOT `scope`, which is already claimed twice (KH
   collection scope, authority scope). Example: `{"loan_program": "conventional",
   "borrower_type": "self_employed"}` for Jazz, `{"typology": "structuring"}` for AML.
   Applicability match = asset applicability is a subset of the query context. The SDK
   never enumerates the dimensions.

3. **Versioning mirrors `prompt_registry`.** Content-hash versions (reuse
   `content_version`), every edit is a new version linked by `supersedes`, rollback is
   re-deploying a prior version, deactivation removes from retrieval but preserves the
   record. No hard deletes. This composes with statemachine terminal-immutability:
   `deactivated` is terminal, and the engine's own refusal message says "supersede with a
   new object version rather than transition" - which is exactly our model.

4. **Lifecycle admission runs on `jazzx_sdk.statemachine`; guidance work is the
   post-admission action.** The lifecycle is a `StateMachine` transition table (data),
   admitted by `engine.apply` - which already gives us actor_class, human-only triggers,
   `cell_ref` -> authority resolver composition (the 1.11.0 matrix binds here, not via a
   parallel path), terminal-state immutability, guard evaluation, and typed `Refusal`s.
   The guidance-specific work (safety validation, conflict check, persistence) happens
   only after admission succeeds. No transition functions are hand-rolled.

5. **Safety validation composes the guardrail primitives; conflict detection is a
   deploy-time action.** `GuidanceValidator` protocol; the shipped implementation is
   `GuardrailGuidanceValidator`, composing `llm_guardrail`/`scope_guardrail` checks (one
   per category: prompt injection / exfiltration, PII, bias, inappropriate; off-topic via
   `scope_guardrail` over a caller-supplied topic list) rather than a fresh
   `structured_call` classifier. Clients bind their red-team pipeline to the same protocol
   instead where one exists. Deploy requires a validator unless explicitly waived
   (`allow_unvalidated=True`). Conflict detection is precision-first (obvious
   near-duplicates only, per PRD calibration): overlapping applicability + trigger
   similarity; produces a `ConflictReport`, resolution is the caller's choice (the SDK
   provides `supersede()`; "narrow applicability" and "deploy anyway" are an edit and a
   flag). **Both blocks are typed `Refusal`s, not exceptions** - a blocked deploy is a
   designed governance outcome the trace records (and the PRD's blocked-attempt audit
   log needs), same "you may not proceed" class as an authority refusal. Validator
   block: `reason_code="guidance_validation_blocked"`, `PRECONDITION_FAILED` (412),
   flags in `domain_extensions`, `remediation="edit the flagged content and re-save"`.
   Conflict: `reason_code="guidance_conflict"`, `POLICY_CONFLICT_UNRESOLVED` (409),
   `ConflictReport` in `domain_extensions`, remediation naming the four resolutions.
   SDK-level literal reason codes follow the established practice (`engine.apply`'s
   `no_transition`/`terminal_state`, `governed.py`'s `write_conflict`); packs may bind
   them into their `RefusalRegistry` for HTTP mapping.

6. **No canonical schema changes.** Guidance Effectiveness joins
   `Outcome.decision_id -> CanonicalDecision.guidance_refs`; `Outcome` is not modified.
   `GuidanceAsset` is a governed reusable asset (Schema Spec §10.3 vocabulary), not a new
   canonical object - no `Canonical*` prefix.

7. **Dependency direction unchanged.** Feedback Manager / Jazz Assistant / eval-service
   consume these primitives through their own services and `/api` surfaces. Nothing here
   imports from any domain pack. Intra-SDK: `fabric/guidance/validators.py` reaches the
   guardrail primitives via lazy import inside the constructor (the established pattern -
   see `feedback.to_signal()`) so fabric does not import the agents stack at module load.

---

## Change 1 - Guidance schema

Create `jazzx_sdk/fabric/guidance/schema.py`:

```python
class ConfidenceWeight(str, Enum):
    STRONG = "strong"        # always inject when applicability matches
    STANDARD = "standard"    # inject; model may adapt shape
    ADVISORY = "advisory"    # background context only

class GuidanceStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    DEACTIVATED = "deactivated"   # terminal - supersede, never edit

class GuidanceProvenance(BaseModel):
    feedback_id: str | None = None        # originating Feedback
    override_event_id: str | None = None  # or originating OverrideEvent
    approved_by: str = ""                 # actor id of approving reviewer
    edited: bool = False                  # reviewer edited vs approved as-is

class GuidanceAsset(BaseModel):
    asset_id: str                                  # f"guidance_{uuid4()}"
    asset_type: str = "learning"                   # feeds GuidanceRef.asset_type
    version: str                                   # content hash (content_version)
    supersedes: str | None = None                  # prior version id
    guidance: str                                  # the corrected/target behavior text
    trigger_patterns: list[str]                    # >= 1; example queries that should match
    applicability: dict[str, str] = {}             # pack-defined dims (NOT named "scope")
    confidence: ConfidenceWeight = ConfidenceWeight.STANDARD
    rationale: str = ""                            # caveat / why this is right (audit + model)
    status: GuidanceStatus = GuidanceStatus.DRAFT
    expires_at: datetime | None = None             # None = no expiry; default set by caller
    review_at: datetime | None = None
    provenance: GuidanceProvenance
    pack_id: str
    metadata: dict[str, Any] = {}
    created_at / updated_at: datetime
```

Include `is_active(now) -> bool` (deployed and not expired) and
`to_guidance_ref(relevance_score) -> GuidanceRef` (imports from
`fabric.canonical.decision`; maps asset_id/asset_type/version straight through).
Reuse `content_version` from `evaluation.prompt_registry` for `version` - do not
re-implement hashing.

---

## Change 2 - Guidance store

Create `jazzx_sdk/fabric/guidance/store.py`:

- `GuidanceStore` ABC, async, consistent with `FeedbackStore`/`ConversationStore`:
  `put(asset)`, `get(asset_id, version=None)` (None = latest), `list(pack_id=None,
  status=None, applicability=None)`, `versions(asset_id)`, `search(query, *, pack_id,
  applicability=None, k=8, status=DEPLOYED)` returning
  `list[tuple[GuidanceAsset, float]]`.
- `InProcessGuidanceStore` - reference impl. Semantic search degrades to token-overlap
  scoring over `trigger_patterns + guidance` (no network, deterministic, tests with
  `ScriptedLLM` elsewhere untouched).
- `RagGuidanceStore(rag: RAGStore, collection_id: str)` - durable impl. One document per
  asset version; `trigger_patterns + guidance` as document content for embedding;
  status/applicability/pack_id/expiry flattened into document metadata so `search()`
  pushes `metadata_filters` down to `RAGStore.search`. Applicability subset-match happens
  post-filter in Python (KH metadata filters are equality-only). Note in a code comment:
  this is O(same-pack deployed assets) per query - acceptable now, revisit if per-tenant
  asset counts approach the PRD's 10K NFR (pre-filter on equality dims first, which the
  metadata filter already enables).

Design intent: mirror how `rag/store.py` wraps the KH client - thin, raising
`KnowledgeFabricError` on backend failures, and **never catching
`KnowledgeHubAccessError` into a soft failure** (re-raise, matching the KH client's own
discipline).

---

## Change 3 - Lifecycle on the statemachine, validation and conflicts as actions

Create `jazzx_sdk/fabric/guidance/lifecycle.py`:

**The transition table is data** - a module-level `GUIDANCE_LIFECYCLE =
StateMachine.from_records("guidance_asset", [...])` with rows:

| from_state | to_state | trigger | trigger_type | actor_class | cell_ref | notes |
|---|---|---|---|---|---|---|
| draft | approved | approve | human | reviewer | (settable) | reviewer accepts |
| draft | deactivated | discard | human | reviewer | | draft withdrawn |
| approved | deployed | deploy | human | reviewer | (settable) | post-admission actions run |
| approved | draft | revise | human | reviewer | | back to editing |
| deployed | deactivated | deactivate | human | reviewer | | removed from retrieval |

`deactivated` has no outgoing rows, so the engine's terminal-immutability rule enforces
supersession for free. Packs may override the table (`from_csv` against their corpus
`state_machines.csv`) - the module constant is the default, not a hardcoded mechanism.
`cell_ref` values are left None in the SDK default; packs that bind an AuthorityMatrix
set them, and `engine.apply` composes with the authority resolver without any code here.

**`GuidanceLifecycle`** - thin coordinator, not a state machine:

```python
class GuidanceLifecycle:
    def __init__(self, store: GuidanceStore, *, machine: StateMachine = GUIDANCE_LIFECYCLE,
                 validator: GuidanceValidator | None = None,
                 conflict_threshold: float = 0.85): ...

    async def transition(self, asset_id: str, trigger: str, *,
                         ctx: TransitionContext,
                         allow_unvalidated: bool = False,
                         ignore_conflicts: bool = False) -> GuidanceAsset | Refusal: ...
```

Flow inside `transition`: load asset -> `engine.apply(machine, asset.status, trigger,
ctx)` -> if `Refusal`, return it unchanged (the engine's typed refusals are the
admission contract; do not wrap them) -> if admitted and the trigger is `deploy`, run
the post-admission actions in order, each returning a typed `Refusal` on block (never
raising - see design decision 5): (1) validator - block returns the
`guidance_validation_blocked` Refusal with flags in `domain_extensions` (a missing
validator is only acceptable with `allow_unvalidated=True`, else a
`PRECONDITION_FAILED` Refusal too); (2) `detect_conflicts` - a hit returns the
`guidance_conflict` Refusal carrying the `ConflictReport` unless `ignore_conflicts=True`
-> persist the new status via `store.put` -> return the updated asset. The return type
is uniformly `GuidanceAsset | Refusal`, matching `GovernedAutomation.run`'s
`Receipt | Refusal`. Refusals populate `trace_id`/`actor_ref` from the
`TransitionContext` so the block is recordable on the trace without caller effort.
Convenience wrappers `approve/deploy/deactivate` just call `transition` with the
trigger; `supersede(old_id, new_asset, ctx)` deploys the new (full action pipeline)
then deactivates the old, linking `supersedes` (a Refusal on the new asset's deploy
aborts before the old is touched); `rollback(asset_id, to_version, ctx)` re-deploys a
prior version's content as a new head version.

Callers construct `TransitionContext` with `human_initiated=True` and their actor_class -
reviewer actions are HUMAN-triggered rows, so programmatic invocation without
`human_initiated` is refused by the engine (Rule 2), which is exactly the PRD's
no-bypass posture.

**Validation** - same file or `validators.py`:

- `GuidanceValidator` protocol: `async validate(asset) -> ValidationResult`
  (`ok: bool`, `flags: list[ValidationFlag]` with category + reason).
- `GuardrailGuidanceValidator(llm, *, domain_topics: list[str], extra: list[Guardrail] = [])` -
  composes the existing primitives from `jazzx_sdk.agents.interactive.registry` (lazy
  import in `__init__`): `llm_guardrail` instances for injection/exfiltration, PII, bias,
  inappropriate (policy text per category lives here as the guardrail `policy` arg), and
  `scope_guardrail(llm, domain_topics)` for off-topic. Runs each check over
  `f"{asset.guidance}\n{asset.rationale}"`; a returned reason becomes a
  `ValidationFlag(category=guardrail.name, reason=...)`. No fresh verdict classifier is
  written - the categories are guardrail policies (config), not code.

**Conflicts:**

- `detect_conflicts(store, candidate, threshold) -> ConflictReport` - deployed assets in
  the same pack whose applicability overlaps (either subset of the other) AND trigger
  similarity >= threshold (default 0.85). Precision-first per PRD: flag obvious
  near-duplicates only; recall tuning waits for usage data.

---

## Change 4 - Retrieval and injection

Create `jazzx_sdk/fabric/guidance/retrieval.py`:

- `retrieve(store, query, *, pack_id, applicability=None, k=3, now=None) ->
  list[GuidanceMatch]` where `GuidanceMatch = (asset, relevance_score)`. Filters: status
  DEPLOYED, not expired, applicability subset-match.
- **Failure semantics - pinned explicitly.** Guidance is non-authoritative enrichment,
  so a *transient* backend failure (`KnowledgeFabricError`, timeouts) degrades to `[]`
  with a distinct log line ("no guidance applied: <error class>") - the PRD's
  zero-blocking NFR. But `KnowledgeHubAccessError` **propagates**: an authz/config
  denial must never be re-swallowed into silent `[]` - that is the exact failure class
  the KH client work just eliminated, and a blanket catch here would reintroduce it.
  Catch `KnowledgeFabricError` specifically; let `KnowledgeHubAccessError` (and anything
  else unexpected) rise. Test both paths.
- `render_guidance_block(matches) -> str` - the injection text. Grouped by confidence:
  STRONG rendered as directives, STANDARD as preferred patterns, ADVISORY as background
  context. Each entry cites `asset_id@version` inline so the trace is self-describing.
- `to_guidance_refs(matches) -> list[GuidanceRef]` - for the caller to attach to the
  `CanonicalDecision` / trace it emits. This line is what makes §10.4 computable.

Design intent: the runtime integration is three lines in a pack or assistant -
retrieve, render into the prompt, attach refs to the decision. No SDK runtime/mode
changes in this plan; an InteractiveAgent hook can follow as a separate additive plan
once Jazz Assistant integration surfaces real requirements.

---

## Change 5 - Fabric wiring

- `jazzx_sdk/fabric/guidance/__init__.py` - export schema, stores, lifecycle, retrieval.
- `jazzx_sdk/fabric/fabric.py` - add `guidance` as a named store, following exactly how
  `rag` is constructed and exposed (read the current wiring first; config toggle in
  `fabric/config.py` consistent with the other stores; default backend in-process,
  rag-backed when a collection is configured).
- `jazzx_sdk/fabric/__init__.py` - export surface consistent with existing stores.

---

## Change 6 - Feedback -> draft structuring (SBI)

Extend `jazzx_sdk/evaluation/feedback_quality.py` (same file - it is the home of
"domain-agnostic LLM operations over feedback"):

```python
class GuidanceDraft(BaseModel):
    situation: str; behavior: str; impact: str      # SBI decomposition
    guidance: str                                   # SBI-informed corrected-behavior text
    trigger_patterns: list[str]                     # suggested, >= 1
    applicability_hints: dict[str, str] = {}        # only keys from the vocabulary

async def structure_feedback(feedback, *, llm,
                             applicability_vocabulary: dict[str, list[str]] | None = None,
                             instructions: str = "", model=None) -> GuidanceDraft: ...
```

One `structured_call` that rewrites raw feedback into SBI form and proposes trigger
patterns + applicability hints constrained to the caller's vocabulary. `instructions`
carries reviewer steering ("narrow to self-employed"). This generalizes the PRD's
"Improve with Juno" into an SDK primitive; the ~8 percent SBI quality result is the
rationale for SBI being the target shape. Provide
`GuidanceDraft.to_asset(pack_id, provenance, ...)`.

---

## Change 7 - Before/after validation harness

Create `jazzx_sdk/evaluation/guidance_ab.py`:

- `async validate_guidance(asset, cases: list[TrainCase], predict_fn: PredictFn, *,
  scorer: Scorer | None = None, pack_id) -> GuidanceABResult`.
- Runs every case twice: baseline `predict_fn(inputs, "")` and candidate
  `predict_fn(inputs, render_guidance_block([...]))` - reusing `TrainCase`/`PredictFn`
  from `optimization.py` and `render_guidance_block` from Change 4. The second prompt arg
  carries the injection text; the caller's adapter decides where it lands.
- Result: per-case `(inputs, before, after, before_score?, after_score?)` pairs plus two
  linked `ExperimentRun` records sharing one `case_set_hash` (hash the case list -
  content-addressed, mirroring `GoldenCaseLoader.hash_cases`), dimensions
  `{"guidance_candidate": f"{asset.asset_id}@{asset.version}"}` vs `{"guidance_candidate":
  "none"}`. This is the PRD's pre-deployment BEFORE/AFTER as two comparable
  ExperimentRuns - no new comparison machinery.
- Include an over-fire affordance: cases whose `inputs` carry an applicability context
  that does NOT match the asset should produce `before == after` expectations for the
  caller to assert (the PRD's "does not over-fire" test).

---

## Change 8 - Compounding metrics

Create `jazzx_sdk/evaluation/compounding.py` - Schema Spec §10 formulas as plain
functions over stores/objects (do not redefine the formulas; targets and windows are
caller concerns):

- `override_learning_rate(overrides, assets)` - fraction of material overrides whose id
  appears in some asset's `provenance.override_event_id` (§10.2).
- `guidance_effectiveness(outcomes, decisions)` - groups outcomes by whether their
  decision carries `guidance_refs`, per asset; returns per-asset usage counts + outcome
  splits for the caller to compare against baselines (§10.4).
- `reusable_asset_growth(assets, period)` - (new - retired) / period (§10.3).

---

## Change 9 - Exports, version, tests

- `jazzx_sdk/evaluation/__init__.py` - export Changes 6-8 alongside the existing
  feedback/optimization names.
- `jazzx_sdk/__init__.py` / `_registry.py` - follow the existing pattern for new modules.
- `_version.py` + `pyproject.toml` -> `1.13.0` together (test_version_sync guards this).
- Tests (all runnable offline, `ScriptedLLM` for LLM seams):
  - `tests/fabric/guidance/test_schema.py`, `test_store.py`, `test_lifecycle.py`,
    `test_retrieval.py`
  - `tests/evaluation/test_structure_feedback.py`, `test_guidance_ab.py`,
    `test_compounding.py`

---

## Phases and acceptance checks

**Phase 1 - schema + stores (Changes 1, 2).**
Accept: asset round-trips through both stores; `versions()` ordered; content-hash dedup
(re-putting identical content yields the same version); in-process `search()` ranks a
trigger-pattern paraphrase above an unrelated asset; `RagGuidanceStore` re-raises
`KnowledgeHubAccessError` untouched.

**Phase 2 - lifecycle (Change 3).**
Accept: transition table loads through `StateMachine.from_records` and round-trips
`from_csv`; `deploy` on a draft returns the engine's `no_transition` Refusal;
`deactivated` asset returns the `terminal_state` Refusal (supersession message);
programmatic deploy without `human_initiated` returns the `human_only_transition`
Refusal; a `cell_ref`-bearing row consults the authority resolver when a matrix is in
ctx; `ScriptedLLM`-scripted guardrail flag returns the `guidance_validation_blocked`
Refusal (`PRECONDITION_FAILED`) with the category in `domain_extensions.flags` and the
asset still in `approved` status (nothing persisted); near-duplicate (overlapping
applicability + triggers) returns the `guidance_conflict` Refusal
(`POLICY_CONFLICT_UNRESOLVED`) carrying the `ConflictReport`, and `ignore_conflicts=True`
proceeds; no code path in `lifecycle.py` raises for a governance block (grep-level
check: `GuidanceValidationError`/`GuidanceConflictError` do not exist); `supersede`
deactivates old and links `supersedes`; `rollback` re-deploys a prior version as a new
head. The validator asserts it composed `Guardrail` objects (no local verdict
classifier).

**Phase 3 - retrieval (Change 4).**
Accept: expired and deactivated assets never retrieved; applicability subset-match
honored (asset `{a:1}` matches query `{a:1, b:2}`; asset `{a:1, b:3}` does not);
`render_guidance_block` orders STRONG before ADVISORY and cites `asset_id@version`;
`KnowledgeFabricError` from the store yields `[]` with the "no guidance applied" log;
`KnowledgeHubAccessError` propagates out of `retrieve` (explicit test);
`to_guidance_refs` produces valid `GuidanceRef` objects.

**Phase 4 - fabric wiring (Change 5).**
Accept: `fabric.guidance` resolves on the fabric object with defaults; rag-backed store
constructs from config; no import cycles (`python -c "import jazzx_sdk"` clean - in
particular, importing `fabric.guidance` must not import `jazzx_sdk.agents`).

**Phase 5 - evaluation integration (Changes 6, 7, 8).**
Accept: `structure_feedback` returns SBI fields + >= 1 trigger with applicability_hints
restricted to the vocabulary; `validate_guidance` returns paired outputs and two
ExperimentRuns sharing `case_set_hash` with distinct `guidance_candidate` dimensions;
compounding functions reproduce hand-computed values on small fixtures.

**Phase 6 - exports, version, full suite.**
Accept: full test suite green; version bumped in both files; new names importable from
their documented paths.

---

## Out of scope (deliberate)

- Feedback Manager / Jazz Assistant UI and service endpoints (client surfaces; they
  consume these primitives via their own `/api`)
- Mortgage applicability vocabulary, personas, severity taxonomies (pack config)
- Canonical schema changes (`Outcome` untouched; effectiveness joins through decision)
- InteractiveAgent auto-injection hook (separate additive plan once Jazz integration
  surfaces real requirements)
- Running deploys through the GovernedAutomation chassis (validate -> authority ->
  execute -> emit). The lifecycle already gets authority + events through the
  statemachine engine; chassis receipts/idempotency on deploys can be layered later if
  operational need appears - noted, not built
- Embedding-similarity conflict detection beyond the precision-first heuristic; recall
  tuning waits for usage data (PRD calibration stance)
- MLflow / eval-service backends (they conform to the store/validator/registry protocols
  client-side, per the SDK adoption policy)
- Multi-reviewer approval workflows (PRD: single SME approval for GA)
