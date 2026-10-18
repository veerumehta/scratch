# Plato client adoption: where jaci still calls the SDK for something Plato serves

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
Repo: jaci (read against japes `jazzx_plato_client/` and `plato/api/` as checked out)
Date: 2026-10-15, revised 2026-10-17 (gaps closed in client 0.2.5)
Status: plan; adoption starts after the next `plato` pin

jaci is configuration, the SDK holds the logic, and `jazzx-plato-client` is the thin wire to Plato.
This audit lists every place in `src/`, `scripts/` and the app-path tests where jaci imports
`jazzx_sdk` or a Plato server module (`plato.*`) for work a Plato route and a client method
already do, what must stay on the SDK, and what the client or Plato lacks.

Ground truth: `PlatoClient` (`client.py` plus the `_authoring`, `_eval`, `_feedback` mixins) and
the routes in `plato/api/` (case runs, documents, chat sessions, packs, authoring, guidelines) and
`jazzx_sdk/server/` (feedback, eval, traces, whoami, extraction) that Plato mounts.

Client behaviour every replacement inherits: `X-Tenant-Id` per client (jaci picks it per pack,
`PACK_TENANTS`); a fresh `X-Trace-Id` per call; an `Idempotency-Key` on every mutating call unless
the caller passes one; identity headers only through `request_headers_provider` (jaci's
`open_plato` forwards `x-security-context`, `x-user-*` and a bearer token); SSE parsed into dicts
with `from_seq` resume; no retries; every non-2xx raises `PlatoError` (an `httpx.HTTPError`).

## Already right

- **Pack publish, check, activate:** `scripts/publish_packs_to_plato.py` through
  `jazzx_plato_client.packs.publish_pack` (`POST /packs/check`, `POST /packs`,
  `POST /packs/{id}/{v}/activate`), one tenant per pack.
- **Pack files and roots:** `jaci/paths.py`, `common/utils/models.py:10`, the AML and DSCR pages use
  `jazzx_plato_client.packs` (no SDK).
- **Case runs:** `dscr/plato_review.py`, `aml/plato_review.py`, `shared/plato_runs.py`
  (`submit_case_run`, `stream_case_run`, `case_run`, `resume_case_run`), version pinned from the
  manifest, idempotency key passed through.
- **Assess:** `tests/integration/test_plato_pilots.py:57` (`assess`).
- **Recorded chat sessions:** `clinical_intake/plato_session.py` (`create_session`, `chat`,
  `close_session`, `session_outcome`, `session_record`).
- **Policy authoring:** `shared/policy_tab.py` (`start_extraction`, `extraction_run`, `proposals`,
  `decide_proposal`, `open_draft`, `merge_rules`, `draft`, `publish_draft`, `activate_pack`).
- **Evals:** `tests/eval/run_eval_plato.py`, `run_dscr_eval_plato.py` (datasets, experiments,
  `describe_pack`).
- **Feedback:** `ci_spread/feedback.py:31` `PlatoFeedbackSink` (`submit_feedback`).
- **Health:** `shared/plato.py:181` `plato_status` (`health`).

Refinements to these, no SDK involved:
- `shared/plato_runs.py:33`: after a resume the journal is replayed from seq 0 and skipped;
  `stream_case_run(run_id, from_seq=...)` reads only what is new.
- `ci_spread/feedback.py:53`: builds its own `PlatoClient` and headers, repeating `open_plato`.
- `whoami` is never called: `plato_status` proves Plato answers, not which tenant and identity it
  resolved. `GET /whoami` would show both on the page.
- Plato paths still load the SDK at import: `aml/plato_review.py` through `aml/__init__.py` and
  `jaci/schemas/__init__.py:27`; `clinical_intake/plato_session.py:24` through
  `session.handoff_summary` (`session.py:25-37`). DSCR's path is clean.

## (a) Replace now

| Call site | What it does | Client method (route) | Behaviour difference |
|---|---|---|---|
| `scripts/extract_policy.py:247-285` (`policy` mode) | In-process policy pipeline (`run_policy_extract`, `default_components("conditions")`, `JtbdTemplate(reads, units)`), writes a DRAFT yaml | `open_draft` (`POST /packs/drafts/{id}`), `write_draft_file` for `jtbd_template.yaml` (reads, units), `start_extraction(representation="conditions")` (`POST /authoring/extract/{id}/runs`), `stream_extraction_run`, `proposals` | Proposals land in the tenant's review queue, not a local file; reads and units come from the draft's template, not flags; model is Plato's unless `model=` is passed; streamed progress; auto idempotency key; identity via `open_plato` |
| `clinical_intake/ui/demo_page.py:54-81`, `session.py:25-37` | Keyless in-process intake: `local_fabric`, `ScriptedLLM`, `build_interactive_agent`, local guardrails | `create_session(..., scripted_replies=persona["agent_replies"])`, `chat`, `close_session`, `session_outcome` | Needs a reachable Plato; free play needs a reply list, not a callable; guardrails run from the published pack |
| `clinical_intake/plato_session.py:69` `completeness()` | Counts covered sections locally from the protocol | `session_progress` (`GET /assistants/{id}/sessions/{sid}/progress`) | One round trip per render; shows Plato's own figure between turns |
| `tests/eval/run_clinical_intake_eval.py:20-32` | Persona eval on the in-process session | Sessions with `scripted_replies`, as `test_plato_pilots.py` does | Needs Plato; results come from Plato's recorded chain |
| `tests/eval/run_cre_eval.py:15,144` | `EvaluationHarness` over `CREConductor` | `create_dataset` / `replace_cases`, `create_experiment`, `start_experiment`, `experiment`, `experiment_cases` (`/eval/...`), pattern of `run_eval_plato.py` | Scorers are Plato's template; results in Plato, not MLflow; pack published under `mesa-verde` first |
| `cre_underwriting/ui/property_case_page.py:71`, `ui/demo_page.py:66` | `evaluate_covenant_policy` over `capabilities` covenant policy | `assess("cre-underwriting-core", inputs)` (`POST /packs/{id}/assess`) | Rules come from the pack's `policies/cre_policies.yaml`, not `covenant_policy()`: confirm parity before switching |
| `ci_spread/ui/demo_page.py:803,889`, `ui/dashboard.py:322`, `tests/eval/run_ci_eval.py:17,234` | `CIConductor` in-process (runs `pipelines.yaml` `credit_analysis`) | `upload_document` (`POST /documents`), `submit_case_run("ci-spread-core", ...)`, `stream_case_run`, `resume_case_run`; evals as above; model picker via `models()` and `submit_case_run(model=)` | Plato runs the manifest's `conductor:` block, which writes no KG triples yet (`TODO(ci-entity-extraction-plugin)`); documents are named by id. Priority after DSCR and CRE: leave `TODO(ci-spread-on-plato)` |
| `ci_spread/ui/demo_page.py:824` | Checkpoint trail via `Pack.case_contexts()` on a local fabric | `case_run_chain` (`GET /runs/{id}/chain`), the run journal | Follows the row above |
| `ci_spread/feedback.py:60-72` `SessionFeedbackStore` | `InProcessFeedbackStore` when no Plato answers | `submit_feedback` only (already the sink) | Tolerant first: keep it only for an assumed localhost Plato that is down, then drop |
| `capabilities/commercial_lending/hitl_approval.py:281` | `Feedback.for_turn` into an injected store | `submit_feedback(turn_feedback(..., category=, subject_id=, metadata=))` through `PlatoFeedbackSink` | Dict body; Plato assigns and returns the record; idempotent on `feedback_id` |
| `ci_spread/ui/demo_page.py:320` | Imports `Reaction` for two constants | Plain `"positive"` / `"negative"` in `turn_feedback` | None (see gap 5) |

## (b) Must stay on the SDK

| Call site | Reason |
|---|---|
| `tests/scenarios/dscr/pack_assessment.py:23,30`, `test_dscr_standard.py:132,149`, `test_dscr_platinum.py:103`, `test_cre_pack.py:25,35`, `test_dscr_pack_assessment.py:43` | Assess in-process on purpose: rule checks without a Plato |
| `tests/unit/test_ci_pack_schemas.py:46-47`, `test_cre_pack.py:49-50` | Offline pre-publish gate (`check_pack_archive`, `conductor_problems`); `check_pack` needs a live Plato |
| `tests/scenarios/dscr/test_profile_literal_drift.py:32,81` | Reads policy-lint internals; no route exposes them |
| `src/jaci/scenarios/dscr/eligibility/programs.py:10-12` | Pack internals (`overlay_map`, policy registry) used only by tests; belongs under `tests/`; an app would read `describe_pack` |
| `tests/unit/test_ci_spread_feedback.py:37-42` | Boots `plato.app` in-process to drive the sink against the real routes |
| `tests/eval/test_clinical_intake_gold.py:10-26` | Offline suite counterpart of `test_plato_pilots.py` |
| `capabilities/*/provides.py`, `capabilities/registry.py`, `commercial_lending/cl_capability.py`, `hitl_approval.py:34`, `cl_events.py`, `pipeline_objects.py`, `promotion.py`; `cl_of_core` names `CL_SPREAD_PIPELINE` | Step kinds jaci registers in its own process; Plato runs only kinds its image installs |
| `kyc/`, `kyc_anthropic/`, `earnings_anthropic/`, `portfolio_monitoring/`, `threat_intel/` conductors and `run_kyc_eval*.py`, `eval_reporter.py` | No pack Plato can run; stay until each scenario gets one |
| `ci_spread/ui/demo_page.py:380,462,493,560,718`, `cre_underwriting/document_intake.py:20`, `property_case_page.py:150`, `insurance_diligence/document_intake.py:19`, `ui/demo_page.py:74,140` | Standalone document classify and extract; no route (gap 1) |
| `ci_spread/ui/demo_page.py:221-223`, `credit_outcome.py:123-205`, `cre_underwriting/ui/property_case_page.py:101-103` | Chat grounded on a locally seeded Decision/Outcome; blocked by gap 4 (and gap 3 for guidance) |
| `ci_spread/demo_correction_to_guidance.py:19-23` | Feedback to draft guidance; gap 3 |
| `jaci/schemas/__init__.py`, `scenarios/*/schemas`, `jaci/modes/*`, `jaci/pack/policy_registry.py`, `jazzx_sdk.finance` users | Schema, model and computation types of in-process scenarios |
| `japes_handler.py:17-18`, `main.py:24-68`, `settings_fields.py:14` | jaci's own server, queue and settings router, not a Plato call; retire with the last in-process scenario |
| `shared/fabric.py:29-34`, `shared/packet_picker.py:76`, `shared/document_upload.py:46` | Knowledge Hub fabric for in-process scenarios; a Plato run uses `upload_document` instead (gap 2 for reuse) |
| `common/utils/models.py:11`, `capabilities/commercial_lending/ui/shared.py:128` | Model choice for in-process modes; a Plato run uses `models()` |

## (c) Gaps: closed in client 0.2.5 (japes v2.6.4)

All five gaps and both client behaviours are built on japes v2.6.4, local and unpushed. They ship
with the next `plato` pin as `jazzx-plato-client` 0.2.5. Signatures below were read from that
branch's client. Nothing changes in jaci until jaci is relocked to that pin.

| Gap | Now in the client | jaci adoption |
|---|---|---|
| 1. Standalone classify and extract | `classify_document(pack_id, document_id, version=, engine=)`, `read_document(pack_id, document_id, **options)`: queue a run of the pack's `document_ingest` step (`POST /documents/{id}/read`, options `step`, `split`, `engine`); output `{kind, items, usage, settings, step}` | CRE (`cre_underwriting/document_intake.py:20,50`) and insurance diligence intake call `run_document` in-process: upload, then `read_document` against their pack. C&I intake (`commercial_lending/pipeline.py:95,154`) follows once `ci-spread-core` is published with its `document_ingest` step |
| 2. List and group documents | `upload_document(data, filename=, subject=, labels=)`, `documents(subject=, label=, limit=, after=)`, `label_document(id, subject=, ...)` (`GET /documents`, `PATCH /documents/{id}`) | The document packet flow (`shared/document_upload.py`, `commercial_lending/document_packet.py`, `shared/packet_picker.py`) keeps ids itself and stores packets in the Knowledge Hub; a packet becomes a subject plus a label, listed with `documents(subject=...)`. Keep `config/demo_document_packets.json` as the demo seed |
| 3. Governed guidance | `guidance`, `guidance_asset`, `put_guidance`, `approve_guidance`, `deploy_guidance(allow_unvalidated=, ignore_conflicts=)`, `deactivate_guidance`, `draft_guidance_from_feedback` under `/packs/{id}/guidance` | Only assistants whose profile names the pack as `guidance_pack_id` get it, built per tenant. Deploy needs a validator, or `allow_unvalidated` where no model is wired. First use: the C&I and CRE chat assistants, fed from reviewed feedback (`draft_guidance_from_feedback`) |
| 4. Outcome outside a run | `record_outcome(subject_id, pack_id, result=, ..., observed_at=)` (`POST /subjects/{id}/outcomes`) writes a Trace, a Decision and an Outcome; the `canonical` ground kind reads them by subject | The grounded chats (C&I and CRE `jazz_assistant`) record the in-process spread or underwriting result before chatting, so `chat(scope={"loan_id": ...})` answers on it. Decisions are keyed by pack id, as run decisions are |
| 5. Reaction values | `contracts.REACTIONS` (`positive`, `negative`, `neutral`), the SDK enum's values; `turn_feedback` refuses others; `process_feedback(feedback_id)` | Drop `jazzx_sdk.evaluation.feedback.Reaction` at `commercial_lending/hitl_approval.py:281` and `ci_spread/ui/demo_page.py:320`; use the strings, checked against `REACTIONS` |

Client behaviours:
- `follow_case_run(run_id, from_seq=last)` resumes without replaying. jaci's own loop
  (`shared/plato_runs.py:23`, used by `dscr/plato_review.py:91,111`) skips the replayed history by
  hand; replace it with the client method and keep the last `seq` seen.
- `RetryPolicy` is opt-in and off by default. Leave it off for page calls, where a
  failure should show; turn it on for batch scripts (`publish_packs_to_plato.py`, the eval runners).

Also new, not adopted yet:
- A document catalog with the BytePro list as a reference (`/document-catalog/ui`). It feeds the
  DSCR registry work, which waits on it (plan first, then the user).
- Assessment engine modes: `job`, `code`, `hybrid` and `both`. DSCR keeps its current engine until
  the regenerated Acra jobs are compared.

## Next steps

Before the pin: none of the below. After jaci is relocked to the `plato` pin carrying client 0.2.5:

1. Small and safe:
   - Replace `shared/plato_runs.follow_case_run` with the client's `from_seq` resume.
   - Use `REACTIONS` instead of the SDK `Reaction` enum.
   - Call `whoami` in `plato_status`.
   - Move `dscr/eligibility/programs.py` under `tests/`.
2. Clinical intake: replace the in-process demo with `create_session(scripted_replies=...)`, use
   `session_progress` for completeness, and move `handoff_summary` to an SDK-free module. Then port
   `run_clinical_intake_eval.py` and delete the in-process branch.
3. Cut the SDK out of AML's Plato import path (`aml/__init__.py`, `jaci.schemas`), so a Plato page
   imports no SDK, as DSCR already does.
4. Documents:
   - CRE and insurance diligence intake read through `upload_document` and `read_document`.
   - Document packets become subjects and labels (`documents(subject=, label=)`). The Knowledge
     Hub packet store stays only where a page still needs it offline.
5. Grounded chats: `record_outcome` for the C&I and CRE results, so `chat(scope=...)` is grounded
   on Plato. Then guidance, with `draft_guidance_from_feedback` from reviewed feedback, approve and
   deploy.
6. `extract_policy.py policy`: route through the draft and `start_extraction` (the Domain tab's
   path), and retire the in-process pipeline.
7. CRE: check `cre_policies.yaml` against `covenant_policy("cre")`, then score with `assess`, and
   port `run_cre_eval.py` to Plato experiments.
8. Feedback: route `hitl_approval` through `PlatoFeedbackSink`, and `PlatoFeedbackSink` through
   `open_plato`. Keep `SessionFeedbackStore` only for a down localhost.
9. C&I on Plato (`ci-spread-core` already declares a `conductor_pipeline`): after DSCR and CRE.
   Leave `TODO(ci-spread-on-plato)` at `ci_spread/ui/demo_page.py:803` in the meantime.
