# jaci on Plato with no SDK: what packs can express as config, and the APIs Plato needs

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: note (inventory and proposal; decides nothing), 2026-09-30. Measured against jaci `dev`
(working tree) and japes local `v2.6.0`. It builds on `note_JACI_SDK_USAGE_AND_CARVEOUT.md`.

## 0. Ground rules (the user's, 2026-09-30)

- jaci uses **no `jazzx_sdk`**. It calls Plato only, through `jazzx-plato-client`, which carries
  every platform contract and API jaci needs.
- **Config before code.** Before any domain Python runs inside Plato, express as much as possible as
  pack config/data, executed by SDK agents (including platform agents) and pipelines.
- **Packs per customer.** A base pack `<domain>-core` (e.g. `cre-core`) holds what is shared. A
  customer pack `<customer>-<domain>-core` (e.g. `mesa-cre-core`) extends and specialises it.
  Plato's samples already follow the customer half.
- **Tenancy.** Dev Plato (local and dev-daily) is multi-tenant for convenience, and every request
  carries the page's tenant. Prod is single-tenant, like other JazzX services. A page's tenant
  comes from jaci configuration.
- **Samples are not jaci's.** Plato's sample packs seed Plato. jaci does not assume they exist; it
  publishes its own packs and finds them through the API.
- **Priority:** DSCR (Acra Lending), then healthcare (clinical intake), then CRE. CRE is the main
  reason for this work.

Legend: ✅ exists and runs on Plato from config · 🟡 exists in the SDK, but Plato does not run it
from config · 🆕 new, domain-agnostic feature.

---

## 1. What packs can express as config, and what runs it

### 1A. ✅ Runs on Plato from config today

| Config surface | Executor | Used by |
|---|---|---|
| `conductor: kind: investigation_loop`: input/hypothesis/decision schemas, `subject_field`, `modes.<m>.{model, temperature}`, `max_iterations`, `on_reasoner_failure`, `narrator_gate {governor_approved, decision_field, decision_in}`, `deterministic_verdict`, one `human_checkpoint` | SDK five shared modes over `pipelines.investigation_loop`, via `pipelines/kinds.py`; Plato case runs | DSCR; all investigation scenarios could |
| `pre_loop: policy_assessment` + `metrics.yaml` (MetricDefinition) + `compose_caps` + `programs:` overlays + `profiles:` | `pack/assessment.py`, DefaultPolicyExpert; `POST /packs/{id}/assess` | DSCR grid; CRE/C&I covenants could |
| Policies/rules, with conditions `expression`, `dsl`, `ratio`, `matrix`, `all_of`/`any_of`; precedence (overlays, `replaces`, `suppresses`) | DefaultPolicyExpert | all |
| `evidence_tools.yaml` sources `input` and `fixture` (keyed by subject, with `default`); UNAVAILABLE on failure | `pack/evidence_tools.py` | DSCR; AML/KYC/CRE fixtures convert mechanically |
| `mode_tuning/<mode>.md`, appended to the SDK base prompt | `compose_mode_prompt` | all |
| Assistant pack: `manifest.yaml` + `profile/` (persona, skills, knowledge bindings, `record:` with protocol and outcomes, `lifecycle:`) + `guardrails.yaml` (`policy_keywords`) | InteractiveAgent, chat pipeline, session recorder; Plato assistants routes | clinical intake; CRE/C&I "Jazz" could |
| JSON Schemas (subset: object, enum, anyOf, local `$ref`, min/max, default) | `pack/schemas.py` | all |
| Eval datasets and experiments for `assistant` and `pack` (assess only); custom scorers (natural language) | eval API | DSCR grid, clinical |

### 1B. 🟡 In the SDK as data or config, but Plato doesn't run it (needs a bridge, not new semantics)

1. **Document agent:** the `document_agent.yaml` taxonomy, confidence floors and templates
   (DocumentAgentSpec). Missing: extraction from a **pack JSON schema** (today it needs a
   Pydantic class) and a route or kind. Needed by CRE, C&I, insurance and portfolio monitoring.
2. **Finance assets:** `LineVocabulary` (chart of accounts), `WorkbookLayout`, `ControlKeys` +
   `SeverityPolicy`, `ExtractionTemplate` (statement anchors), `SourcePrecedencePolicy`. These are
   YAML-loadable, but have no manifest key, so a published pack doesn't carry them. jaci reads
   them by filesystem path from `ci-spread-core`, which can't work from a published pack.
3. **Governor inputs:** `authority_matrix`, `surface_bindings`, ClientOverlay and ExecutionProfile.
   GovernorMode accepts them, but `sdk_mode_factory` passes nothing, not even the policy registry,
   so citation and sunset checks are skipped on Plato.
4. **`evidence_types:`** is not given to the investigator.
5. **Assistant `output_schema`**: needs a SchemaRegistry built from the pack's JSON schemas.
   Skill `tools:` have no tool catalog in Plato.
6. **A reasoning agent in the case-run pre-loop.** Without it, `natural_language` and `procedure`
   rules always come back INDETERMINATE (TODO in `kinds.py`).
7. **Assess inputs:** a per-call `deal_policy` and profile, and multi-period or entity records
   (`ResolutionContext`). The SDK supports them; `/assess` does not.
8. **Scorers:** register regex, contains, schema and array in Plato. `EvalTemplate` YAML exists.
9. `StateMachine.from_records` and `EventCatalog.from_list` are data-shaped, but jaci builds them
   in Python. They need manifest keys.
10. Data that is loaded but never consumed: `diagnose_map`, `playbooks` (`DefaultPlaybookExpert`
    raises), `modes.<m>.tuning`, `experts`, `MetricDefinition.threshold/test_cases/approval_status`,
    `version_range`.

### 1C. 🆕 New domain-agnostic config features, in suggested build order

**Foundation (needed by everything):**

1. **Pack composition, base plus customer.** Extend `depends_on` with one entry marked as the
   base, pinned to an exact version (japes' suggestion). Per-asset merge rules, declared once in
   the SDK:
   - keyed tables merge by id; a child overrides only with `override: true` and removes with
     `remove: [ids]`;
   - policies: a child adds overlays and extends `programs:`, and replaces a parent policy only
     via `supersedes`; a lint checks a child narrows regulatory policy and never loosens it;
   - profiles: `extends: <parent profile_id>`, with per-key provenance;
   - mode_tuning and skills: `compose: append|replace`;
   - the conductor block: a child overrides scalar keys and `pre_loop` entries by id;
   - schemas: extended through `allOf`;
   - fixtures and cases: child only.

   Plato resolves the pair at publish and at activation, stores the closure digest on the
   activation so a run pins both packs, and serves the resolved view. Today only playbooks,
   evidence types and skills merge, only from an on-disk checkout; published packs don't resolve
   `depends_on`.
2. **Manifest asset keys**, so published packs carry their data: `vocabulary:`, top-level
   `metrics:`, `extraction_templates:`, `spread_templates:`, `workbook_layouts:` (with key-resolution
   lint), `validation:`, `adjustments:`, `state_machines:`, `events:`, `report_templates:`,
   `presentation:`, `gold_cases:` (seeded into an eval dataset).
3. **Grammar and schema:**
   - the expression grammar gains strings, booleans, `NOT`, `in`, dotted or JSON-pointer access,
     `abs`/`round`/`pow`/`pmt`, and a "skip when all inputs are missing" option;
   - JSON Schema gains `if/then` (conditional `required` and `default`), `minItems` and
     case-insensitive enums;
   - schema-derived models stop admitting nulls (a bug).

**Investigation loop** (DSCR, AML, KYC, C&I credit loop, CRE underwriting, earnings):

4. `convergence {min_iterations, min_distinct_evidence_types, required_all, required_any}`;
   `sentinel {signal_decay_threshold, confidence_change_threshold}`;
   `deadline_guard {field, within_hours}`.
5. Several ordered `human_checkpoints: [{name, after}]`.
6. `post_loop` steps: `policy_assessment over: decision` (facts from the input, attested evidence
   and the decision); `sensitivity {base, shocks, rule}`; `dependencies {list_field, type_field,
   map}`.
7. `on_governor_block {decision}`, `narrator_gate.any_of`, `narrator.artifact {type, audience}`,
   `governor_context` (rule parameters picked by a decision field), and per-run model overrides
   from an allow-list.
8. **A richer CaseResult:** `context {iteration_count, hypotheses, evidence}`,
   `termination_reason`, token usage. (The OpenAI failure attributed to `rich_evidence_requests` was
   already fixed in japes v2.5.6, `fc48deb4`; 2.6.0 also makes the shape configurable.)

**Evidence and documents:**

9. Evidence sources: `key_param`/`select_by`, `aliases:`, and
   `source: knowledge_hub_doc | document` (a document reference template with a fixture fallback).
10. Taxonomy `required_classes` and cardinality, emitting DATA_GAP findings; checklist rules
    `satisfied_by_doc_types`.
11. A deterministic table and field binding extraction spec (header match, row-key pattern, column
    map, label-anchored values, flag-from-note), as an alternative to LLM extraction. For T-12,
    CCC, loan agreements, SOV, flood and rent rolls.
12. **Conductor kind `document_review`:** classify, extract per class (pack schema), derive
    (metrics, `*_entities`), assess, decision table, report template. Covers portfolio monitoring
    and insurance diligence, and CRE intake.

**Finance and spreading (CRE, C&I):**

13. SDK data kinds for the engines jaci holds today: a line-adjustment library (add-backs:
    condition, cap, ceiling and enabled list from the profile), reclassification rules (move,
    split, conditional), breakouts, a governed correction layer (OVERRIDE provenance), and a
    record reconciliation spec (two records, a field list and tolerances, giving mismatches and an
    optional status action).
14. **Conductor kind `financial_spread`:** documents, structure (anchors + vocabulary), package,
    adjustments, metrics, validate (control keys + compliance with pinned policy versions), gate,
    human checkpoint (maker-checker roles; corrections in the resolution), affirm/promote
    (authority cells), then a workbook artifact.
15. A decision-table kind, a report-template asset, and review-queue ranking config.

**Evaluation and learning:**

16. Field-path scorers (`actual_path`/`expected_path`), `ratio`, `banded`, `at_least`; a
    `case_run` invoker; an `assistant_session` invoker (scripted turns); gold cases as a pack asset.
17. Curator signals, with tags declared in the pack; a guidance route; data-driven playbook
    recommendation from `diagnose_map`.

**Assistants:**

18. A declarative tool catalog that skills reference by name: assess, documents, KG/ontology,
    evidence sources, extraction.
19. Scripted replies per session, on a relaxed posture, for keyless demos;
    `record.summary_template`; YAML guardrail kinds (scope, grounded, regex, redaction); a chat gate
    that can escalate to a case run.

**Later:** a declarative pipeline (a built-in step-impl catalog plus guards in the expression
grammar), so a pack can declare a new flow without a new kind. `fan_out_aggregate` (earnings
sector spread).

### 1D. What still needs code, after 1A–1C

- **Connectors to real systems:** image entry points owned by the platform, not pack Python.
  Examples: an Integration Hub, a circuit breaker, Flowable.
- **Cross-source evidence reconciliation in AML** (`skills/evidence.py:165`): possibly covered by
  the reconciliation spec (13).
- **Page rendering:** stays in jaci; it needs only data from Plato.

Everything else in jaci's Python is either covered above or dead code to delete (see §4).

---

## 2. The APIs Plato needs

✅ exists · ➕ exists, needs an extension · ❌ missing. P = `/api/v1`. The scenario column lists
who needs it.

### 2.1 Platform and identity

| | Route | Needed by |
|---|---|---|
| ✅ | `GET /health`, `GET P/info` | all |
| ❌ | `GET P/whoami` → `{tenant_id, user_id, roles, may_author}` | all pages (resolved tenant; may it publish?) |
| ❌ | `GET P/info/catalog` → modes, conductor kinds, pre/post-loop kinds, condition kinds, guardrail kinds, evidence sources, scorers | platform page; tells authors what config is valid |

### 2.2 Packs

| | Route | Needed by |
|---|---|---|
| ✅ | `GET P/packs`, `POST P/packs/check`, `POST P/packs`, `POST P/packs/{id}/{v}/activate`, `GET P/packs/{id}/history`, `GET P/packs/{id}/{v}[?path=]`, `GET .../archive`, drafts CRUD + publish | all |
| ❌ | `GET P/packs/{id}/active` → `{version, content_digest, activated_at, by}` | all (pin a version, show what is live) |
| ➕ | `POST P/packs/check`: add `content_digest` | publish script (compare without downloading) |
| ❌ | `GET P/packs/{id}/{v}/resolved`: the effective layered pack, with provenance per asset | all customer packs |
| ❌ | `GET P/packs/{id}/{v}/describe`: parsed policies, profiles, ontology, conductor graph, modes, evidence types/tools, metrics, programs, checkpoints, schemas | Concepts and Domain tabs (they read pack files today) |
| ➕ | Publish and activate a closure (base first; the customer pins the base) | all customer packs |
| ❌ | `GET P/packs/{id}/policies?program_id=&resolve=true` → precedence, policies, conflicts, versions | C&I and CRE policy views |

### 2.3 Deterministic assessment

| | Route | Needed by |
|---|---|---|
| ✅ | `POST P/packs/{id}/assess?version=&reason=` | DSCR, CRE/C&I covenants |
| ➕ | body `deal_policy`, `profile_id`; `?series=true` (multi-period); `?persist=true` (records Decision/Outcome for assistant grounding) | CRE, C&I, portfolio monitoring |

### 2.4 Case runs and human checkpoints

| | Route | Needed by |
|---|---|---|
| ✅ | `POST P/packs/{id}/runs`, `GET P/runs`, `GET P/runs/{id}`, `.../stream`, `.../stop`, `.../resume`, `.../outcome` | DSCR, AML, KYC, C&I, CRE |
| ➕ | resume: `corrections[]`, `roles{}`; several checkpoints | C&I and CRE spreads, AML (L3 + SAR) |
| ➕ | outcome: `outcome_class`, `reason_code` | AML |
| ➕ | submit: per-run `modes` override (allow-listed) | KYC model benchmark |
| ❌ | `GET P/traces/{id}`, `GET P/decisions/{id}` (mount `trace_routes`), or `GET P/fabric/canonical/{type}?subject_id=` | Trace tabs everywhere |
| ❌ | `GET P/runs/{id}/artifacts/{name}` (workbook.xlsx, template.csv, credit memo) | C&I, CRE |
| ❌ | `POST P/runs/{id}/evidence {doc_id}` (append evidence and re-assess) | insurance diligence |
| ❌ | `GET P/packs/{id}/subjects?state=` (book view over runs) | portfolio monitoring |

### 2.5 Assistants

| | Route | Needed by |
|---|---|---|
| ✅ | chat, chat/stream, run stream/stop, sessions create/get/delete/close/outcome/record | clinical intake; CRE/C&I Jazz |
| ❌ | `GET P/assistants`, `GET P/assistants/{id}` (manifest, profile, protocol, guardrails, skills) | clinical, Concepts |
| ➕ | `pack_version` on session create; echo pack, version and digest on session and reply | clinical |
| ❌ | `GET .../sessions/{sid}/progress` (required, covered, missing, escalated rule), or on each reply | clinical |
| ➕ | scripted replies per session, on a relaxed posture | clinical keyless demo |

### 2.6 Documents (all missing; the biggest gap, and CRE's critical path)

| | Route | Needed by |
|---|---|---|
| ❌ | `POST P/documents` (file or zip, zip-slip guarded) → `{documents:[{doc_id, name, content_hash}]}`; `GET P/documents/{id}`, `.../markdown`, `.../json` | CRE, C&I, insurance, portfolio |
| ❌ | `POST/GET P/packets`, `GET P/packets/{name}` (named collections) | same; replaces KH packet push and the local cache |
| ❌ | `POST P/packs/{id}/documents/classify {doc_ids or packet}` → `{results, by_class, unresolved, missing_required}` | same |
| ❌ | `POST P/packs/{id}/documents/{doc_id}/extract {schema or doc_type}` → `{fields, confidence, source_coordinates, refusals}` | same; DSCR appraisal |

### 2.7 Spreading and finance compute (missing)

| | Route | Needed by |
|---|---|---|
| ❌ | spread runs through the `financial_spread` kind on the existing `POST P/packs/{id}/runs` | CRE, C&I |
| ❌ | `POST P/packs/{id}/compute/{metrics, normalize, validate, reconcile}` (interactive recompute without a run) | CRE, C&I |
| ❌ | `POST P/spreads/{ref}/{corrections, affirm, promote, override}`, `GET P/spreads/{subject}/effective` | C&I, CRE (governed promotion) |

### 2.8 Evaluation, feedback, learning

| | Route | Needed by |
|---|---|---|
| ✅ | `P/eval/datasets`, experiments, scorers, custom scorers, templates, baselines, optimizations | all |
| ➕ | experiment entities `case_run` and `assistant_session`; field-path, ratio, banded and at_least scorers; register regex/contains/schema/array | DSCR loop, AML, KYC, C&I, CRE, clinical |
| ✅ | `P/feedback` and `P/feedback-config` | C&I, CRE, clinical |
| ❌ | `POST P/signals` → routed buckets; `GET P/signals/buckets` (curator) | AML, C&I |
| ❌ | `GET/POST P/packs/{id}/guidance` | C&I |

### 2.9 Automation (threat intel only; a retire candidate)

| | Route |
|---|---|
| ❌ | `POST P/packs/{id}/automations/discovery/runs`, `GET P/packs/{id}/proposals`, approve/reject (approval writes a pack draft) |

### 2.10 `jazzx-plato-client`: what it must add

- **Methods** for every route above: today it has packs, assess, case runs, sessions, chat,
  feedback, health and info. It needs pack contents/history/drafts/active/resolved/describe, eval,
  documents, packets, compute, spreads, traces/decisions, assistants list, whoami and catalog. It
  also needs closure publishing and a `run_case` helper (submit, stream, await).
- **Typed contracts**, Pydantic only and platform-generic:
  - packs and runs: pack inventory, check report, info; run submit/view; stream frames;
    `CaseResult` + governor; resume/outcome requests; `PolicyAssessment`, Attestation, caps;
  - assistants: chat reply, session record, close response;
  - canonical objects: Evidence, Decision, Trace, Outcome, Refusal, Confidence, SourceCoordinate,
    DecimalValue;
  - documents: refs, classification, extraction;
  - finance: SpreadPackage, line items, MetricResult, ValidationFinding, Correction,
    SpreadDecision/PromotedSpread;
  - eval models; the feedback record.
- **Domain types are not in the client.** A loan, a CRE recommendation or an AML disposition comes
  from the pack's JSON schemas. jaci's pages use light models generated from those schemas or
  written against them.

---

## 3. Scenarios: readiness and order

| Scenario | Today on Plato | To go SDK-free | Notes |
|---|---|---|---|
| **DSCR** (1st) | grid (assess) + review (case run) | delete the in-process path; display via `describe`; gold cases into the pack; read `pack_id` and version from the manifest, not hardcoded (`plato_review.py:27`); appraisal extraction is dormant | almost all (1) already |
| **Clinical intake** (2nd) | full session lifecycle | delete the in-process session; `progress` route; scripted replies; session eval invoker; ids from the manifest (`plato_session.py:28`); fix the manifest version mismatch 0.1.2 vs 0.1.0-draft | almost all (1) already |
| **CRE** (3rd, the target) | nothing | make `cre_underwriting_core` a real pack (`cre-core` + `mesa-cre-core` + `maa-cre-core`); composition; manifest asset keys; document routes; `document_review` / `financial_spread` kinds; loop knobs (convergence, sentinel, post-loop sensitivity/dependencies); grammar | the pages never run the CRE conductor today; they are deterministic |
| C&I | feedback only | manifest Python pointers out (publish blocker); credit loop on investigation_loop + knobs; spreading needs `financial_spread` | actively maintained |
| AML | nothing | pack authoring + fixture conversion; loop knobs; case_run eval | demo and eval paths are broken today |
| KYC-Anthropic | nothing | close to investigation_loop; `governor_context`; policies into the pack | — |
| Portfolio monitoring, insurance diligence | nothing | `document_review` kind + documents | — |
| Earnings | nothing | single company: a day of pack authoring; sector: `fan_out_aggregate` | CLI only |
| KYC-OpenAI, threat intel | nothing | — | **retire candidates** (no UI, dormant) |

**Suggested order:**
1. DSCR and clinical intake SDK-free, needing only small additions: `active`, `describe`,
   `whoami`, `progress`, the eval entities and client contracts.
2. Composition and manifest asset keys.
3. Document routes and the `document_review` kind (CRE intake, insurance, portfolio).
4. Loop knobs and a richer CaseResult (CRE underwriting, AML, KYC, C&I credit).
5. The finance data kinds and the `financial_spread` kind (CRE, C&I spreads).
6. Learning routes. Retire or port the rest.

---

## 4. Found along the way (not fixed)

- **CRE:**
  - two contradictory policy sets: `cre_underwriting/policies/policies.yaml` (LTV ≤ 75%) and
    `commercial_lending/policies.py:351` (MAA term sheet, LTV ≤ 65%), which Mesa Verde is scored
    against;
  - Mesa Verde's unit count disagrees: 198 in `tools/registry.py:376`, 252 in `cases.py`;
  - `insurance_diligence/diligence.py` defaults `pack_id` to `cre-underwriting-core`.
- **C&I:** `pack_manifest.yaml:145-169` names Python, so publishing fails (`python_pointer`).
- **AML:**
  - every demo evidence request comes back UNAVAILABLE (`tools/registry.py:248` passes a dict where
    an EvidenceRequest is expected);
  - `run_eval.py:382/409` can't run;
  - nothing sets `sar_deadline`, so case_09's guard can't fire.
- **KYC-Anthropic:** `run_kyc_eval.py:141/143` is broken; the page never sets the active case, so
  it gets generic mocks.
- **KYC:** src imports tests; fixture keys and personas don't match the gold cases.
- **Earnings:** `conductor.py:209-219` ignores its tool registry and returns placeholder evidence.
- **japes:** `cltv_pct` rounds on Plato but not in-process. Two earlier claims were wrong on
  current japes:
  - the `rich_evidence_requests` OpenAI failure was fixed in v2.5.6 (`fc48deb4`);
  - schema-derived models admit null only where a schema allows it or a field is optional (pinned
    by `tests/test_pack_schemas.py:81`). The real trap is an author leaving a needed field out of
    `required`.
- **Dead code to delete rather than port:**
  - `src/jaci/modes/` (re-exports), `src/jaci/pack/policy_registry.py`;
  - AML `experts/`, `skills/`, `prompts/aml/` and duplicate schemas;
  - CRE `jazz_assistant.py`, `tools/mock_connectors.py`; the earnings `policies/registry.py`;
  - `threat_intel/schemas`; `template.py`'s in-code template fallback.

## 5. Open decisions

1. Composition through `depends_on` extended with a pinned base (japes' suggestion), or a new
   `extends:`.
2. Retire KYC-OpenAI and threat intel, and which other scenarios to port or archive.
3. Drop the in-process "Run on" option from DSCR and clinical intake, so pages always need a Plato
   (a local one for development).
4. Tests keep japes as a dev-only dependency (a real Plato in-process), while the runtime uses only
   the client.
5. Deterministic table/field binding (11) versus LLM schema extraction for T-12 and similar
   documents, or both.
