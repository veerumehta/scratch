# macer's rerun cost work and its JAPES design against the SDK (sonnet-runtime, 2026-10-28)

Read-only note; nothing built, no action on macer. Sources: macer `design/rerun_cost_optimization.md` (661 lines; the
opus note said 221, that is the diff), `design/japes.md` (1067), commits 43e2f51d, 365a1993, 2e962b0e, f1fd4093.

## 1. Rerun cost: macer against our case rerun

| macer mechanism | what it does | ours |
|---|---|---|
| Run mode gate (INITIAL / INCREMENTAL / FORCED_FULL from payload flags and an existing FindingSet) | one branch decides; nothing rerun-shaped exists on the other modes | `rerun` in the submit body names the run to follow; none = initial; `RerunBasis.full` = a different pack version, nothing carried. **Gap:** the caller must name the basis; macer infers it from the loan's FindingSet |
| Change detection: new documents against a recorded scope (`LoanDocumentScope`, source ids) plus LOS entities by `updated_at` against `last_run_at` | fewer sections | documents by digest (`RerunBasis.items`, an unchanged file reuses its items; split pieces are byte-identical since 5b5d35f6, so a piece is recognized), record fields by value (`changed_fields` against `basis.record`). No clock anywhere, so macer's A20/A25 (clock skew, entity edited mid-run) cannot happen |
| Section scope, `skip_jtbd` (no impacted section = stop, success, nothing saved) | the "nothing to save" stop | `impacted_rules` narrows adjudication to rules reading a changed field or a new/changed document, and "nothing moved: the prior verdicts stand" costs no model call. **Gap:** only the adjudication step stops; the investigation loop, verifier, reasoner, governor and narrator still run (about 0.08 USD and minutes of wall time on loan-2, measured) |
| Planner "nothing applicable" stop, `all_jtbds_failed` stop | typed stop reasons on the run | we have `failed_segments`, health codes (`run_degraded`, `unresolved_gaps`) and a `degraded` status, no `stop_reason` on a case run's outcome |
| One work unit per section, fixed names, largest first | stable units, no model-chosen partition | `bin_by_section` (units by the job's section, max 10 rules, fixed order and names): same idea, with a cap macer deliberately does not have |
| Document focus (cited / NEW+relevant / NEW+other / uncited count), byte-pinned prompt text | where to look first | `DocumentFocus` (new documents, per-rule prior cites); no uncited bucket, no snapshot-pinned preamble. macer's open point "rejected evidence still offered as CITED" is already handled here (`rejected` in the basis, `_without_rejected`) |
| Previous-findings walk-back (past skip/ERROR rows, bounded by the last FORCED_FULL) | newest evaluated finding per mnemonic | not needed: the basis carries the followed run's outcomes directly, and a rerun saves no skip rows either |
| Conditions as a parallel track (`MergedConditionSet`, dedup) | carry open conditions across runs | condition ids with a watermark continue across reruns (`assign_condition_ids`, `_carry_conditions`); no dedup track (deferred on merit earlier) |
| `read_document` serves a prefix under the byte cap with a continuation footer | a long read costs one call, not a refusal | `read_document` (`tools/agent/dir_tools.py`) **refuses** over the cap with "specify a range"; the model pays a wasted turn |
| Retry with `tool_choice="none"` unless the error needs a tool (`ToolRetryRequiredError`) | cheaper, cache-safe schema retries | already ours: `run_kit` (`ToolRequiredValueError`, `retry_without_tools`, `tool_choice="none"`, same reason: cache prefix and "tool not found") |
| Rules needing a tool are reported first under the error cap | the one instruction the model cannot infer survives the cap | **Gap:** `_issues` lists `errors[:MAX_FEEDBACK_ERRORS]` in order |
| Consolidated retry (`utils/retry.py`) | one retry helper | `is_transient_error`, `run_with_recovery`, call guard (deadline per attempt, incomplete-call counting): ours is wider |

What we have that macer lacks: the page cache and deterministic pieces (a warm rerun's ingest is ~0.27 USD against 3.40
cold, measured), DocIntel and failed-attempt metering with a per-run ceiling, per-program adjudication, usage kept on a failed or
cancelled run, RBAC and the context policy, rejected-evidence-aware reruns, tool-result compression with a reference store.

**Worth taking into the SDK** (small to large):
1. `read_document` serves a prefix with a continuation footer instead of refusing (dir tools; a few lines and a test).
2. Tool-required validation errors first under the feedback cap (`run_kit._issues`).
3. A run-level "nothing to save": a rerun whose record fields, documents and rejections did not move ends after the
   adjudication step with a typed outcome (`unchanged`, pointing at the basis) instead of running the loop and narrative.
   Decision for the user: the audit trail of a no-op run (a result that copies the basis, or none).
4. `rerun: "latest"`: the basis resolved to the newest completed run of the same subject and pack version, so a host does
   not have to hold run ids (macer's FindingSet inference, without a second entity).
5. A `stop_reason` on a case run's outcome (`no_impacted_rules`, `nothing_applicable`, `all_segments_failed`) next to health codes.
Not worth taking: the walk-back (no consumer without skip rows), timestamp-based LOS detection, the preamble's wording
(behaviour-bearing prose of macer's agents; ours would be written and measured for our own adjudication prompt).

## 2. macer's JAPES design: what is SDK-shaped

macer is a thin consumer (pinned japes 2.4.9; imports `JazzXRuntime`, `Handler`, `HandlerContext`, `ResponseMessage`,
`QueueSettings`). Each piece, and where we already have it:

| macer piece | SDK-shaped? | the SDK's equivalent |
|---|---|---|
| `invokeAgent` message with `operation` (`jtbd_agent`, `entity_extraction`) | yes | the handler seam is unchanged; in v2 a loan is a case run (`POST /packs/{id}/runs` or a queue message into `CaseRunService`), `entity_extraction` = the document step (`document_ingest`, `read_document`) |
| Findings as KH entities (`Finding`, `FindingSet`, 3028-line `findings_converter`) | the decision record is; the KH entity shape is macer's | an adjudicated `RuleOutcome` already carries verdict, status, action, citations (document, page, ref), confidence, conditions with ids; the run is the set. v2 keeps the KH entities only if downstream readers need them: a small emitter (`DocumentAgent.emit_entity` pattern, `fabric.entities`) from outcomes, not a rewrite of the converter's input side |
| Rerun detection (INITIAL / INCREMENTAL / FORCED_FULL, `force_full_run`, `include_previous_context`) | yes | `rerun` basis (+ the `latest` item above); FORCED_FULL = no basis; macer's "INITIAL with a FindingSet becomes FORCED_FULL" is the host's choice of basis |
| Runtime LLM config from the message (`config_schema.py`, extra fields refused, ranges, logged to MLflow) | yes | submit body `model`, `mode_overrides {mode: {model, temperature}}`, `engine`; `RunSettings`; the unknown-field refusal is `extra="forbid"` on the request models (eval-override alignment note already queued) |
| LiteLLM routing by model-name prefix | yes | `infer_provider` and the model cards (`flex_`, provider by name; litellm an optional extra); no new work |
| Graceful shutdown + MLflow run status | yes | queue processor shutdown, `ResilientRunner` (heartbeat, interrupted), a cancelled case run now keeps its usage; the MLflow run tracer (`observability/backends/mlflow`) closes a run with its status: check the mapping when macer adopts it |
| Ontology/entity fields as UUID or unique name (`resolve_ids_or_names`) | yes, generic | not in `KnowledgeHubClient` today (callers pass ids): worth a client method (`resolve_ontology(name_or_id)`, OData `name eq`) |
| Zero-documents handling, no-data early exit | partly | `required_when: documents`, `missing` classes, `_skip("the case names no documents")`, health `unresolved_gaps` |
| LOS entity download (23 types, parallel) and ontology derivation | host side | in v2 the loan record is the case `input` the host assembles before submit; the SDK diffs fields |
| Document download retry, local directories, `dir_tools` | host side / SDK | `DocumentSource` (blob), `read_text`, directory tools for evidence |
| Orchestrator planner, section summarization, condition dedup | macer's behaviour | not SDK: the planner is replaced by the rule-impact narrowing; dedup stays macer's until a consumer asks (deferred on merit) |

## 3. Migration path and where JAPES_V2 starts

1. **Pin bump** 2.4.9 to the current 2.6.x on macer's own branch: the five names it imports exist; leaf modules moved
   (`jazzx_sdk.util.*`), run macer's tests. No behaviour change. This is the start line.
2. **A pack for macer's JTBDSet**: `import_jtbdset` writes the K-Studio set as procedure rules (programs as overlays);
   `conductor_pipeline`: `document_ingest` (split, classify) then `adjudication` (units by section) and `narrate`. macer's
   section types and mnemonics are the rule ids; this is what the Acra pipeline already does.
3. **A/B on one section**, macer's output against the case run's adjudicated outcomes, with the aligned compare and
   eval overrides we have (verdict agreement per requirement, as in the loan-2 code-versus-job table). This is where
   macer's agent prompts and ours differ (their tool-driven read sessions against our inline or tools evidence); decide
   from the measured agreement, not the design.
4. **Findings emitter** from case outputs to `Finding` and `FindingSet` for any consumer still reading KH entities; retire
   the converter's input half as the pipeline moves over.
5. **Reruns**: basis from the loan's latest run (item 4 above), documents by digest, LOS by fields; drop `LoanDocumentScope`
   and the clock assumptions A20/A25. Take items 1 to 3 of section 1 first so a rerun is as cheap as macer's.
6. **Config, shutdown, MLflow**: map the message `config` to the submit body; adopt the queue processor's shutdown; check
   MLflow status on interrupt.

JAPES_V2 starts at step 2 once step 1 is green: the first thing that exists only in v2 is the pack and its case run;
steps 3 and 4 decide whether macer's agents or ours do the evaluation, which is the part not decided by the SDK.
Risks: findings shape differences (observations/facts with page refs against outcome cites), condition dedup has no SDK
home, and the DocIntel/vision cost model differs (macer reads through its own tools; our run meters and caps it).
