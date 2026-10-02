# A pack declares its case workflow: the `conductor_pipeline` kind

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, Rev 1 (2026-10-02), written against `v2.6.0` at `fab0793e`. **Decisions D1-D6
taken as recommended (2026-10-02).** Owner: the policy session
(CLAUDE.md "Who works on what"); §3.3 and §3.6 touch the runtime session's `runs/` and blob routes.

## 0. What this extends

- `plan_plato_domain_pack_runtime.md` §6 "Later": *a second conductor kind (`conductor_pipeline`:
  `ConductorEngine` over a pack `pipelines.yaml` with SDK step kinds -- ci-spread-core's shape)*. Its
  §9 sends C&I, CRE, AML and KYC here. This plan is that row.
- The same plan's §2 rule holds unchanged: **a pack is data; Plato never imports pack Python.** What a
  pack can run is a closed set of conductor kinds and step kinds shipped in `jazzx_sdk`, extended
  only by image-level entry points (`jazzx_sdk.conductor_kinds`, and the `jazzx_sdk.step_kinds` that
  §2 names but nothing implements yet).
- Already built and reused, not redesigned: `investigation_loop` (`pipelines/kinds.py`), its
  `policy_assessment` pre-loop step with the omitted-fact refusal, human checkpoints (`327a063a`:
  `SUSPENDED`, `/resume`), the runs layer (`CaseRunner`, journal, SSE, stop), `run_document` and
  `DocumentAgent`, `AdjudicationAgent` (a library: no conductor calls it), the JTBD extraction
  pipeline that writes procedure rules into a pack.
- `plan_v2_6_0.md` lists "documents upload (no design yet)" under human checkpoints. §3.3 is that
  design.

## 1. The gap

| Consumer | Needs | Today |
|---|---|---|
| DSCR (Acra) | the loan's documents in (appraisal, rent roll, leases), classified, facts extracted into the loan record; the JTBD rules adjudicated against those documents; then the existing grid and checkpoint | `investigation_loop` over a typed loan record and fixture evidence; no document step; JTBD rules are not run by any conductor |
| CRE | a policy check over the reasoner's underwritten figures, after the loop | pre-loop assessment only |
| C&I (ci-spread-core) | a 13-step pipeline: document intake, entity extraction, investigator, evidence, verifier, sentinel, playbook, reasoner, policy, governor, narrator, evaluator, persist | jaci Python behind `conductor.class:`, which Plato's check refuses |

`investigation_loop` is one fixed shape with one pre-loop slot. Each need above is a step before or
after it, so the kind that is missing is an ordered list of steps, each a configured SDK step kind.

## 2. Design

### 2.1 The manifest block

```yaml
conductor:
  kind: conductor_pipeline
  input_schema: schemas/loan_application.json
  subject_field: loan_id
  steps:                                   # or `pipeline: pipelines.yaml`, the same list in a file
    - id: documents
      kind: document_ingest
      agent: document_agent.yaml           # taxonomy, classifiers, extraction schemas
      fills: input                         # extracted fields fill what the record left out
    - id: assessment
      kind: policy_assessment              # the existing step, config unchanged
      metrics: metrics.yaml
      compose_caps: {compare_field: cltv_pct, strategy: min}
    - id: adjudication
      kind: adjudication
      agent: adjudication_agent.yaml       # AdjudicationAgentSpec: persona, mounts, segments, replicas
      rules: live                          # the selected program's live rules (JTBD / procedure)
      evidence: documents                  # mounts the classified documents by class
    - id: investigation
      kind: investigation                  # today's loop, as a step
      modes: {investigator: {}, verifier: {}, reasoner: {}, governor: {}}
      hypothesis_schema: schemas/hypothesis.json
      decision_schema: schemas/eligibility_recommendation.json
      evidence_tools: evidence_tools.yaml
      deterministic_verdict: authoritative
    - id: approval
      kind: human_checkpoint
      checkpoint: ELIGIBILITY_DECISION_APPROVAL
    - id: narrative
      kind: narrate
      when: "decision.decision == 'INELIGIBLE'"
```

`investigation_loop` stays as a kind: it is exactly `[policy_assessment?, investigation,
human_checkpoint?, narrate?]`, and DSCR's current manifest keeps working unchanged.

### 2.2 Step kinds

A closed set in `jazzx_sdk.pipelines.steps`, each a registered `StepKind`: a config model (validated
at publish), the state slots it reads and the slot it writes, and a runner. Registered through the
SDK at import and the `jazzx_sdk.step_kinds` entry point.

| Step kind | Wraps | Reads | Writes |
|---|---|---|---|
| `document_ingest` | `run_document` + `DocumentAgent` (convert, classify, extract) | `documents` (run input) | `documents` (classified, with markdown), `input` (filled fields, each with its source document) |
| `policy_assessment` | `pack.assessment.assess` (unchanged) | `input` | `assessment` |
| `adjudication` | `AdjudicationAgent.adjudicate` over `partition_rules`'s live set | `input`, `documents`, `assessment` | `adjudication` (rule outcomes, citations into documents) |
| `investigation` | the investigation loop's modes | `input`, `assessment`, `adjudication`, evidence tools | `decision`, `trace` |
| `policy_check` | `assess` over a named slot's figures (CRE's post-loop check) | a declared slot path, e.g. `decision.underwritten` | `checks.<id>` |
| `human_checkpoint` | the built suspension (`327a063a`) | `decision` | `decision` (resolution, approver) |
| `narrate` | `NarratorMode` | `decision`, everything prior | `narrative` |

C&I's remaining steps (entity extraction, sentinel, playbook, evaluator, persist) are Phase 5:
each becomes an SDK step kind where it is general, or an image-level plugin where it is jaci's.

### 2.3 State between steps

A typed `CaseState` with named slots (`input`, `documents`, `assessment`, `adjudication`, `decision`,
`checks`, `narrative`, `trace`), not a free dict. A step's declared reads and writes are checked at
publish: a step reading a slot no earlier step writes is a `conductor_unrunnable` finding, the
finding `conductor_problems` already raises for an unknown kind.

### 2.4 Verdict composition

In order of authority, fixed by the kind rather than configured:
1. `assessment` violations are authoritative where `deterministic_verdict: authoritative` (today's rule).
2. `adjudication` outcomes: a `FAIL` on a rule whose action is `deny` withholds an approval, like a
   deterministic violation; `INDETERMINATE` is attested and routes to the checkpoint.
3. `investigation`'s decision, gated by the governor.
4. `human_checkpoint` resolves the case; its resolution and approver are part of the record.

### 2.5 Facts from documents

`document_ingest` with `fills: input` merges each extracted field into the run's record only where
the submitted record left it out, recording the source document and page per field. The
omitted-fact refusal then runs on the merged record: a field neither the submitter nor the documents
supplied is refused before the LLM steps run, and a run whose documents might still supply it is not
refused at submit. A field the documents contradict (submitted 75% CLTV, appraisal implies 82%) is
attested as a conflict and goes to the checkpoint, never silently overwritten.

## 3. Phases

| Phase | Contents | Proves |
|---|---|---|
| 1 | `conductor_pipeline` kind; `StepKind` registry + entry point; `CaseState`; steps `policy_assessment`, `investigation`, `human_checkpoint`, `narrate`; publish-time slot check; `investigation_loop` re-expressed as a fixed pipeline | DSCR's current manifest and a `conductor_pipeline` manifest of the same steps give the same decision on the five gold cases |
| 2 | documents in (§3.3, §3.6) and the `document_ingest` step with `fills` | a DSCR run with the Acra sample appraisal fills `property_value` from it and cites the page |
| 3 | the `adjudication` step over the JTBD rules the authoring pipeline wrote into dscr-core | a DSCR run adjudicates its live rules against the run's documents, each outcome citing a document location |
| 4 | `policy_check` after the loop | CRE's check over the reasoner's underwritten figures |
| 5 | C&I's remaining step kinds, then ci-spread-core off `conductor.class:` | ci-spread-core publishes to Plato and runs there |

### 3.3 Documents in (Phase 2)

- `POST {prefix}/documents` stores an upload in the tenant's blob store (`fabric.blob`) and returns
  `{document_id, sha256, media_type}`. Tenant-scoped, size-capped from config.
- A case run's input carries `documents: [{document_id}]` (or a Knowledge Hub `collection_id`, which
  `DocTurn` already accepts). The run pins each document's sha256 next to the pack version, so a
  decision names the exact bytes it read.

### 3.6 Who touches what

Steps, kinds, state, the publish check and the dscr-core manifest are the policy session's. The
documents route, blob scoping and `CaseRunner`'s handling of a document-bearing input are the runtime
session's; Phase 2 starts by agreeing that interface with it.

## 4. Decisions

| # | Question | Decided (2026-10-02, as recommended) |
|---|---|---|
| D1 | Steps inline in the manifest, or `pipelines.yaml`? | Both, as `pipeline:` already reads for the policy assets: inline for short lists, a file for C&I's thirteen. |
| D2 | Typed `CaseState` or a free dict? | Typed: it is what makes the publish-time slot check possible. |
| D3 | Documents: blob upload, Knowledge Hub collection, or both? | Both; blob upload is new (§3.3), a collection is what `DocTurn` already takes. |
| D4 | Does an adjudication `FAIL` deny like a deterministic violation? | Yes for a `deny` rule; others attest and route to the checkpoint. |
| D5 | Keep `investigation_loop` as a kind? | Yes, as sugar for its fixed pipeline, so no manifest migrates. |
| D6 | A generic `POST /runs {pipeline, input}` over the catalog | After Phase 1, once step kinds are catalogued; not needed for any phase here. |

## 5. Acceptance

- Phase 1: the five DSCR gold cases give identical decisions, violations and binding caps under
  `investigation_loop` and under the equivalent `conductor_pipeline`; a manifest naming an unknown
  step kind, or a step reading an unwritten slot, fails `/packs/check` with a named finding.
- Phase 2: an upload round-trips through `/documents`; a run cites the page a filled field came from;
  a conflicting field reaches the checkpoint.
- Phase 3: each adjudicated live rule has an outcome with a document citation; a `deny` rule's
  `FAIL` blocks an approval.
- Phase 5: ci-spread-core has no `conductor.class:` and passes the publish check.

## 6. Not in this plan

- Executing pack-supplied Python (unchanged from the runtime plan's §2).
- A queue worker or multi-replica run dispatch.
- Acra's cap adjustments (declining market, waiting on their Q-07/Q-08).
- The jaci-side manifests: jaci authors them once each phase lands, through the jaci session.
