# Institutional Intelligence Architecture Drift Audit — v1.5 Pre-Freeze Synthesis

## Executive Summary

The JAPES **platform schema layer is contract-mature and largely conformant**: the five canonical nouns (`Policy/Evidence/Decision/Trace/Outcome`) and eight derived objects are correctly typed, each carrying `pack_id` and the cross-linkage triad, and the v1.5 TraceStep discipline (the single most-common v1.5 failure) is implemented correctly at the schema layer (`trace.py:177` `extra='forbid'`, no version-bundle/metadata/domain_extensions dict on TraceStep, 13-mode enum only). The promotion, outcome-linkage, and fabric surface contracts are all defined correctly. **The platform is ready to be frozen on most axes — with three named exceptions that must be fixed first (below).**

The **scenarios tell a starkly different story**. Of seven scenarios, exactly **one (AML) is genuinely platform-aligned** in its type/promotion plumbing; it is the only scenario that parameterizes the generic `Context[T,T,T]`, ships explicit `to_canonical_decision`/`Outcome.from_case_file` promotion methods, single-sources its primitives via SDK re-export shims, and registers a real canonical Policy registry. The remaining six scenarios (kyc, kyc_anthropic, earnings_anthropic, cre_underwriting, ci_spread, threat_intel) are **demo-first**: they bypass the governance spine to varying degrees. Two of them (cre_underwriting, threat_intel) get the *cognitive shape* right but nothing else; the others fail nearly every axis.

The dominant cross-cutting failures, in order of how damaging they are to the compounding-learning thesis:

1. **Outcome orphaning is near-universal.** Six of seven scenarios never create or link an `Outcome` (the seventh, AML, only closes the loop in its eval harness — the live handler calls `put_case_file` without `outcome=`, `japes_handler.py:181`). **No scenario closes the compounding loop in its production path.** If the v1.x contract is frozen now, "Decisions not linked to Outcomes = no compounding" (Migration Guide:268) becomes the de facto operating reality.
2. **No scenario registers a real DomainPack.** Zero scenarios emit a `DomainPack` object/manifest. `pack_id` is a bare string literal everywhere, frequently **inconsistent within a single scenario** (hyphen vs underscore: AML `aml-investigation-core` vs `aml_investigation_core`; kyc `kyc-openai-core` vs `kyc-investigation-core`; kyc_anthropic, earnings, all the same pattern). Autonomy ceilings are hardcoded literals in code. The entire Mode Governance Spine (per-Pack Registry + Authority Matrix + D63 Evaluation Asset Registry + v1.5 manifest minimums) is absent across the board.
3. **Policy-in-prompts / policy-in-code is systemic.** Every scenario hardcodes binding thresholds — in Python (AML `governance.py`, ci_spread `conductor.py`, threat_intel `handler.py:348`) or in LLM prompts (kyc, kyc_anthropic, cre_underwriting, earnings_anthropic). cre_underwriting is the most dangerous: its prompt thresholds **diverge from its own governed PolicyRegistry** (debt-yield 10% in prompt vs 8% in registry), and the prompt wins the binding call.
4. **LLM output is treated as operative authority (5.1).** No scenario fires an Authority Matrix gate. The Governor's free-text JSON `approved` boolean is consumed directly as the operative decision in kyc, kyc_anthropic, and earnings_anthropic. No scenario tags Skill/Expert output as a Decision Candidate before it becomes operative (the one exception: cre_underwriting and kyc_anthropic's PolicyExpert correctly stamp GUIDANCE_REFS — but kyc_anthropic never calls it).

**Bottom line for the freeze decision:** the canonical contracts are sound enough to freeze *after* three platform fixes (operational `Outcome`/`Attestation` collisions, `Freshness` duplication, `fabric.pack` wiring). But freezing the contracts will not by itself produce conformant scenarios — six of seven need substantial promotion + pack-registration + policy-externalization work, and AML needs its live outcome-linkage and TraceStep emission completed. **Do not let the demo-first scenario patterns calcify; they currently bypass the very governance the platform was built to enforce.**

## Drift Matrix

| Target | promotion | fabric-access | pack-registration | schema-duality | cognitive-shape | charter-nonbypass |
|---|---|---|---|---|---|---|
| **japes-platform** (schema layer) | conformant | conformant | na | partial/high | conformant/low | conformant |
| **aml** | partial/high | conformant/low | **missing/critical** | conformant/low | conformant | drift/high |
| **kyc** | **missing/critical** | drift/high | **missing/critical** | drift/high | drift/high | drift/high |
| **kyc_anthropic** | **missing/critical** | drift/high | partial/high | drift/medium | drift/high | drift/high |
| **earnings_anthropic** | **missing/critical** | **missing/critical** | **missing/critical** | drift/high | drift/high | drift/high |
| **cre_underwriting** | drift/critical | drift/high | **missing/critical** | partial/medium | conformant | drift/high |
| **ci_spread** | **missing/critical** | **missing/critical** | **missing/critical** | drift/high | **missing/critical** | drift/high |
| **threat_intel** | **missing/critical** | **missing/critical** | **missing/critical** | partial/medium | **missing/critical** | drift/high |

Status legend: `conformant` = meets contract; `partial` = contract defined but incompletely applied; `drift` = present but violating; `missing` = absent entirely; `na` = judged at another layer.

## Per-Axis Cross-Cutting Narrative

**Axis 1 — Canonical Promotion & Outcome Linkage (the worst axis overall).** The platform defines the contract correctly (Decision triad `decision.py:85-93`+`:127`; Outcome required `decision_id`/`trace_id` `outcome.py:61-66`; `put_case_file` persistence `store.py:1185-1241`; documented promotion hooks). **Only AML implements real promotion methods** (`to_canonical_decision` `case_context.py:364`, `Outcome.from_case_file` `schemas/outcome.py:64`) with cross-linkage backfill — but even AML's live handler never passes `outcome=` to `put_case_file` (`japes_handler.py:181`), so the loop closes only in eval. The other six emit operational Pydantic/plain-Python forms as the terminal record and never create an Outcome. cre_underwriting is uniquely bad: its lone `CanonicalTrace` construction (`conductor.py:562-578`) is **dead code that raises ValidationError** (6 required fields missing, 6 nonexistent fields passed) and is only `logger.info`'d. This is the axis most likely to cement a non-compounding system if frozen.

**Axis 2 — Knowledge/Semantic Access Through Fabric.** Platform facade is correct (canonical nouns vs capability verbs cleanly split, raw `.kh` gated to non-semantic). **AML is the only conformant scenario** (`fabric.docs.get` for evidence, `fabric.canonical.put_case_file`/`preload_policies`). The pattern degrades by severity: kyc/kyc_anthropic/cre use `fabric.docs` *when a fabric is passed* but default to `use_mocks=True` in the production constructor, so the live branch is never exercised; earnings_anthropic/ci_spread/threat_intel have **zero fabric usage at all** — ci_spread stores `ctx` and never reads it (`conductor.py:40`), threat_intel's staging write is an explicit TODO stub (`jazzx_sdk/automation/handler.py:180-182`). Several still consult policy via `fabric.docs` or direct module import rather than `fabric.policy`.

**Axis 3 — Real DomainPack Registration (universal failure).** The platform defines `DomainPack` (`derived.py:547-563`) and a `DomainPackStore`, but **note the v1.5 manifest-minimum version fields are not present on the base model**. No scenario registers a pack. kyc_anthropic and cre_underwriting have real canonical PolicyRegistries + (kyc_anthropic) an AuthMatrix, but no Pack object binds them — "governed policy exists, no Pack identity." Autonomy ceilings are orphaned literals (`autonomy_ceiling=2` in AML/CRE; prompt text in kyc; LLM-emitted field in earnings). D63 Evaluation Asset Registry is absent everywhere despite eval modes existing in several scenarios.

**Axis 4 — Operational vs Canonical Type Discipline.** The platform itself carries the worst single instance: `modes/schemas.py` re-declares **Attestation (line 78, divergent: free `str` verdict vs canonical `AttestationVerdict` enum at `evidence.py:35`)**, **Freshness (line 110, identical duplicate of `evidence.py:60`)**, and an operational **Outcome (line 613)** that name-collides with canonical Outcome and lacks decision_id/trace_id/pack_id — and exports it in `__all__`, risking silent shadowing. The correct pattern exists right beside it (EvaluationReport consolidated to `derived.py`), proving intent but not applied. AML resolves this exemplarily via re-export shims. Demo scenarios mostly avoid *re-declaring* primitives (because they have no evidence layer at all) but ship parallel ad-hoc forms (triplicated GovernorDecision in kyc; unqualified `CaseFile` collisions in cre_underwriting `case_context.py:252` and ci_spread `schemas.py:87`; `RiskHypothesis(dict)` subclasses in kyc_anthropic).

**Axis 5 — Investigation/Hypothesis-Elimination Loop Conformance.** The platform's `Context[T,T,T]` (`schemas.py:321-379`) is genuinely the universal shape, but its field vocabulary (hypotheses/evidence/verifier_reports/decision + iteration_count/loop_status + ACTIVE/CONFIRMED/ELIMINATED) **hard-encodes specifically the investigation loop** — a one-shot/transactional domain must still adopt hypothesis vocabulary. **AML and cre_underwriting conform decisively** (real multi-iteration Investigator→evidence→Verifier→Reasoner loops with convergence guards). Everyone else bypasses: kyc/kyc_anthropic/earnings run bespoke plain-Python `ReviewContext` classes over dict-lists that *mimic* the loop shape but never type Hypothesis/Evidence or track elimination; ci_spread and threat_intel are outright one-shot linear pipelines (ci_spread hardcodes `iterations=1`; threat_intel is `scan→assess→propose`). Notably, the declared `KYCContext` alias (`japes_types.py:142`) is never used by *either* kyc scenario, and binds to the wrong scenario's types for kyc_anthropic.

**Axis 6 — Charter 5.x Non-Bypass.** Platform schema layer is clean (TraceStep discipline correct; policy/authority in governed typed objects). **Every scenario drifts.** Two recurring violations: (5.3) policy thresholds hardcoded in code or prompts — universal; (5.1) LLM/mode output consumed as operative authority with no Authority Matrix gate — kyc, kyc_anthropic, earnings, ci_spread. The TraceStep-version-bundle anti-pattern (the named most-common v1.5 failure) **cannot fire in most scenarios because they emit no TraceStep at all** — which is itself a hole, not a pass. AML is the exception that proves it: it correctly does not redeclare TraceStep, but its Conductor emits zero TraceSteps and constructs a `CanonicalTrace` missing the v1.5-required base fields (status/started_at/pack_version/binding_id/deployment_id).

## Cognitive-Shape Finding

See the dedicated verdict field. In short: the evidence supports interpretation **(b)** — `Context[T,T,T]` is the *investigation-loop* contract, not a neutral universal operational contract. The scenarios that fit naturally are investigative (AML, cre_underwriting); the scenarios that bypass it are precisely the transactional/one-shot ones (ci_spread credit decisioning, threat_intel automation) where the hypothesis-elimination vocabulary is a poor fit and was abandoned rather than adopted.

---

## Prioritized Remediation Backlog (32 items)


### CRITICAL

- **AML-04** — AML: register a real DomainPack and reconcile pack_id slug
  - axis: `pack-registration` | scope: `scenario:aml`
  - fix: Create a DomainPack manifest (pack_id, pack_version, domain_thesis, scope_boundary, supported_autonomy_range{min,max}, cognitive_mode_activations) registered via fabric.pack, with a per-mode Authority Matrix and D63 Evaluation Asset Registry. Move autonomy ceilings out of code (governance.py risk_ceiling_map, conductor.py:166) into supported_autonomy_range + Authority Matrix. Fix the slug inconsistency (aml-investigation-core vs aml_investigation_core). Depends on PLAT-02/PLAT-03.
- **PLAT-01** — Consolidate Attestation/Freshness/Outcome — delete operational re-declarations in modes/schemas.py, import from fabric.canonical
  - axis: `schema-duality` | scope: `platform`
  - fix: Remove the duplicate Attestation (schemas.py:78), Freshness (schemas.py:110), and operational Outcome (schemas.py:613) from modes/schemas.py and import the single-source canonical versions (evidence.py:30,60; outcome.py:29), following the proven EvaluationReport pattern (derived.py:484). If a runtime/operational attestation verdict truly needs to stay free-string, qualify it (e.g. OperationalAttestation) and reconcile the verdict typing to AttestationVerdict; do NOT leave two divergent Attestation.verdict types or a linkage-less class literally named Outcome exported in __all__. FREEZE-BLOCKER.
- **PLAT-02** — Add v1.5 manifest-minimum version fields to the base DomainPack model
  - axis: `pack-registration` | scope: `platform`
  - fix: Add skill_bundle_version, per_pack_registry_versions, authority_matrix_versions, shared_entity_ontology_version, ipdv_policy_version to DomainPack (derived.py:547-563) so packs can declare them on the typed model. This is a prerequisite for every scenario's pack-registration fix (SCN-PACK-*). FREEZE-BLOCKER (the manifest schema must be final before packs bind to it).
- **SCN-CISPREAD-01** — ci_spread: integrate with the platform — currently zero jazzx_sdk imports
  - axis: `promotion` | scope: `scenario:ci_spread`
  - fix: Entire scenario has no jazzx_sdk/jaci.schemas imports; ctx is stored but never read (conductor.py:40). This is a UI demo, not a Domain Pack. Decide whether to (a) promote it to a real pack — wire Context, fabric, canonical Decision/Outcome, DomainPack — or (b) explicitly de-scope it from the conformance set. Given PLAT-04, ci_spread (one-shot credit decisioning) may be the case for the transactional contract rather than the investigation loop.
- **SCN-CRE-01** — cre_underwriting: fix the broken CanonicalTrace and add promotion + Outcome
  - axis: `promotion` | scope: `scenario:cre_underwriting`
  - fix: conductor.py:562-578 constructs CanonicalTrace with 6 required fields missing and 6 nonexistent fields passed (raises ValidationError) and only logs it. Fix the construction, add a to_canonical_decision on UnderwritingRecommendation, create+link an Outcome, and persist via the canonical store. The cognitive loop is already strong — this is the missing governed tail. Depends on XCUT-OUTCOME-01.
- **SCN-CRE-02** — cre_underwriting: collapse the two policy sources of truth (prompt thresholds vs PolicyRegistry)
  - axis: `charter-nonbypass` | scope: `scenario:cre_underwriting`
  - fix: governor.md/reasoner.md embed binding thresholds (LTV 75%, DSCR 1.25x, debt-yield 10%, occupancy 90%) that DIVERGE from the governed PolicyRegistry (debt-yield 8%, occupancy 0.85) — and the prompt wins the binding block decision (conductor.py:459-474). Read thresholds from fabric.policy/PolicyRegistry only; delete the prompt-embedded numbers. The advisory PolicyExpert GUIDANCE_REFS boundary is already correct — preserve it.
- **SCN-EARN-01** — earnings_anthropic: build the full canonical chain and wire fabric access
  - axis: `promotion` | scope: `scenario:earnings_anthropic`
  - fix: Zero fabric usage; returns an operational EarningsReviewFile with canonical_trace=None (conductor.py:296) and no Outcome. Replace the scenario-local CanonicalTrace/GovernorDecision/EarningsAssessment forks with canonical types + domain_extensions, emit a real Decision/Trace/Outcome, wire evidence through fabric (currently inline placeholder dicts, conductor.py:199-206 TODO). Depends on XCUT-OUTCOME-01, XCUT-FABRIC-01.
- **SCN-EARN-02** — earnings_anthropic: register DomainPack and remove LLM-emitted autonomy + prompt policy
  - axis: `pack-registration` | scope: `scenario:earnings_anthropic`
  - fix: No DomainPack; pack_id is a bare string and inconsistent (earnings-anthropic-research in __init__ vs earnings-review in code). autonomy_level is an LLM-emitted Literal (earnings_schemas.py:200) — move to supported_autonomy_range + Authority Matrix. Move policy dataclasses (policies/registry.py MI-002) out of Governor prompts (governor.py:101-115) into fabric.policy. Add D63 registry. Depends on PLAT-02/PLAT-03.
- **SCN-KYC-02** — kyc: add canonical promotion + Outcome and implement the documented triad backfill
  - axis: `promotion` | scope: `scenario:kyc`
  - fix: No Outcome/Trace/CanonicalDecision is emitted; the ad-hoc ReviewFile is the terminal record. The decision_id/policy_refs/evidence_refs/trace_id triad on RiskTierRecommendation (kyc_schemas.py:157-184) is documented as 'Backfilled by Conductor' but NO backfill code exists. Implement promotion to CanonicalDecision, create+link an Outcome, and actually populate the triad. Depends on XCUT-OUTCOME-01, SCN-KYC-01.
- **SCN-KYCA-01** — kyc_anthropic: emit canonical Decision/Trace/Outcome and persist via store
  - axis: `promotion` | scope: `scenario:kyc_anthropic`
  - fix: run_review returns a plain ReviewFile (conductor.py:82-98) with no Decision/Trace/Outcome and no store write. The ReviewRecommendation triad (kyc_anthropic_schemas.py:323-328) is decorative (trace_id='' default, never backfilled). Add promotion + Outcome creation + store persistence. Depends on XCUT-OUTCOME-01.
- **SCN-THREAT-01** — threat_intel: define the automation-surface governed-output contract (promotion + fabric)
  - axis: `promotion` | scope: `scenario:threat_intel`
  - fix: Proposals are emitted as model_dump() dicts (handler.py:216-221) into a stubbed staging method (jazzx_sdk/automation/handler.py:180-182 TODO 'Write to Knowledge Fabric'). No Decision/Outcome/Trace, no fabric. Implement the staging write to fabric, and define how an automation surface produces governed objects (likely UpdateProposals as Decision Candidates promoted only after human/Authority-Matrix review). Tied to PLAT-04 (automation is the clearest non-investigation contract case).
- **SCN-THREAT-03** — threat_intel: register a DomainPack (or formally classify as a non-pack automation surface)
  - axis: `pack-registration` | scope: `scenario:threat_intel`
  - fix: pack_id is a bare string used to format asset-path slugs (handler.py:89,383-391); no manifest, no autonomy range, no registries. Either register a real DomainPack or, per PLAT-04, formally classify automation surfaces as a distinct governed object type with their own manifest minimums. Depends on PLAT-02/PLAT-03/PLAT-04.
- **XCUT-OUTCOME-01** — Establish the production outcome-linkage pattern (live Outcome creation on case completion)
  - axis: `promotion` | scope: `cross-cutting`
  - fix: Define and document the canonical 'Conductor promotes + creates Outcome at case completion' pattern in the live handler path (not just eval). Reference impl on AML: have Conductor.run_investigation call Outcome.from_case_file(...) and pass outcome= to put_case_file (fix japes_handler.py:181). This pattern is the unblocker for every scenario's promotion fix. Sequence: PLAT-01 then this. FREEZE-RELEVANT (the promotion contract and its reference usage should be settled before freeze).

### HIGH

- **AML-01** — AML: link Outcome in the live handler path
  - axis: `promotion` | scope: `scenario:aml`
  - fix: In the production workflow create an Outcome via the existing schemas/outcome.py:64 from_case_file and pass it to put_case_file (japes_handler.py:181 currently omits outcome=). Closes the compounding loop in production, not only in eval. Depends on XCUT-OUTCOME-01.
- **AML-02** — AML: emit TraceSteps and construct a v1.5-valid CanonicalTrace
  - axis: `charter-nonbypass` | scope: `scenario:aml`
  - fix: The Conductor builds CanonicalTrace (conductor.py:298-310) missing required base fields status/started_at/pack_version/binding_id/deployment_id (raises ValidationError) and leaves steps[] empty. Populate the required base fields, emit a TraceStep per mode invocation using the 13-mode enum, and push per-step version/IPDV context to Trace.metadata via TraceStepContextHelper. This is the template other packs will copy — fix it first.
- **AML-03** — AML: externalize Governance thresholds to the existing canonical Policy registry
  - axis: `charter-nonbypass` | scope: `scenario:aml`
  - fix: governance.py hardcodes 48h, min_attested=3, confidence 0.70/0.85, and risk_ceiling_map despite policies/registry.py + AuthMatrix existing. Make enforce() actually evaluate rules from the canonical Policy registry (the :233 comment admits it only records policy_id). Removes the 5.3 policy-in-code violation in the reference scenario.
- **AML-05** — AML: classify Expert/mode outputs as Decision Candidates and add an Authority Matrix gate
  - axis: `charter-nonbypass` | scope: `scenario:aml`
  - fix: Set output_classification on Skill/Expert outputs and require an Authority Matrix / Governor gate before a candidate becomes operative (currently governor_result.output consumed directly, conductor.py:337; zero output_classification matches). Depends on AML-04 (Authority Matrix must exist).
- **PLAT-04** — Decide and document the cognitive-shape scope: investigation-loop contract vs universal operational contract
  - axis: `cognitive-shape` | scope: `platform`
  - fix: Per the cognitive_shape_verdict, Context[T,T,T] is the investigation-loop contract, not a universal one. Either (i) introduce a lighter operational/transactional contract for one-shot and automation surfaces (legitimizing ci_spread/threat_intel), or (ii) formally document that transactional domains must adopt a single-iteration degenerate hypothesis form. Settle this BEFORE FREEZE — it determines whether ci_spread/threat_intel are 'bypass' or 'correct for a different contract.'
- **SCN-CISPREAD-02** — ci_spread: remove the fabricated 'governance trace' UI (telemetry-as-authority, 5.5)
  - axis: `charter-nonbypass` | scope: `scenario:ci_spread`
  - fix: ui/demo_page.py:322-345 renders a hardcoded list of (mode,title,detail) tuples and static PASS/FAIL policy strings ('Leverage 0.27x vs <=3.0x — PASS') as if a governance authority surface — violates IEF Bright Line 3. Either drive the trace from a real emitted Trace or clearly label it as a non-authoritative mock; do not present static UI strings as governance output.
- **SCN-CISPREAD-03** — ci_spread: qualify the CaseFile collision and externalize hardcoded thresholds
  - axis: `schema-duality` | scope: `scenario:ci_spread`
  - fix: schemas.py:87 class CaseFile shadows the generic runtime CaseFile unqualified — rename/qualify. Move hardcoded advance rates (0.85/0.50, conductor.py:82-83), leverage ceiling (3.0x, conductor.py:158), and covenant constants out of code into fabric.policy.
- **SCN-EARN-03** — earnings_anthropic: parameterize Context[T,T,T]
  - axis: `cognitive-shape` | scope: `scenario:earnings_anthropic`
  - fix: Replace plain-Python ReviewContext (conductor.py:44) with a Context parameterization; type hypotheses/evidence (currently raw dict lists overwritten each iteration, conductor.py:189) and implement real elimination/loop_status instead of trusting the LLM's 'converged' flag.
- **SCN-KYC-01** — kyc: replace bespoke ReviewContext with Context[T,T,T] and fix the schema-mismatch bug
  - axis: `cognitive-shape` | scope: `scenario:kyc`
  - fix: Runtime state is hand-rolled (conductor.py:41 ReviewContext over dict lists) and the declared KYCContext (japes_types.py:142) is unused. Wire KYCContext = Context[ReviewTrigger, RiskFactorContent, RiskTierRecommendation]. Fix the guaranteed AttributeError: conductor.py:277/318/338-339 reference recommendation.risk_rating/disposition but RiskTierRecommendation only has risk_tier/edd_decision (kyc_schemas.py:136-138) — the loop cannot currently complete.
- **SCN-KYC-03** — kyc: de-duplicate the triplicated GovernorDecision and stop forking Decision fields
  - axis: `schema-duality` | scope: `scenario:kyc`
  - fix: Three parallel GovernorDecision definitions exist (conductor.py:69, JAPESGovernorDecision via japes_types.py:37, KYCGovernorDecision kyc_schemas.py:201). Consolidate to the platform GovernorDecision. Stop forking canonical Decision fields onto RiskTierRecommendation (kyc_schemas.py:155-198); ride domain_extensions or promote to CanonicalDecision.
- **SCN-KYC-04** — kyc: move risk-tier rubric and autonomy ceilings out of Governor/Reasoner prompts
  - axis: `charter-nonbypass` | scope: `scenario:kyc`
  - fix: governor.py:88-112 and reasoner.py:108-153 embed LOW/MEDIUM/HIGH/PROHIBITED thresholds and L0-L3 autonomy ceilings in prompts; the Governor LLM JSON is consumed as the operative gate (conductor.py:300-306). Load thresholds from fabric.policy; add an Authority Matrix gate; tag outputs as Decision Candidates.
- **SCN-KYCA-02** — kyc_anthropic: actually consult the existing AuthMatrix and call the PolicyExpert
  - axis: `charter-nonbypass` | scope: `scenario:kyc_anthropic`
  - fix: A real AuthMatrix exists (registry.py:153-181) but is never consulted; authority comes from the Governor LLM's free-text 'approved' boolean (governor.py:217). Wire the AuthMatrix gate. The PolicyExpert correctly stamps GUIDANCE_REFS (experts/policy.py:45) but is never invoked — call it. Move the in-prompt gate rules (governor.py:163-189, reasoner.py:157-168) to fabric.policy.
- **SCN-KYCA-03** — kyc_anthropic: parameterize Context[T,T,T] and remove dict-subclass models
  - axis: `cognitive-shape` | scope: `scenario:kyc_anthropic`
  - fix: Replace bespoke ReviewContext (conductor.py:44) with a real Context parameterization (note KYCContext alias binds to the OTHER kyc scenario's types — needs its own alias). Replace RiskHypothesis(dict)/RiskHypothesisUpdate(dict) (investigator.py:33-48) and the two GovernorDecision classes with typed Hypothesis/Evidence/platform GovernorDecision.
- **SCN-KYCA-04** — kyc_anthropic: register a DomainPack to bind its existing Policy registry + AuthMatrix
  - axis: `pack-registration` | scope: `scenario:kyc_anthropic`
  - fix: Strongest policy infra of any demo scenario (4 canonical Policies + AuthMatrix) but no DomainPack binds it. Create a DomainPack manifest with identity fields + D63 Evaluation Asset Registry + v1.5 manifest minimums, registered via fabric.pack. Fix pack_id slug drift (kyc-anthropic-cdd-lifecycle vs kyc_anthropic_cdd_lifecycle). Depends on PLAT-02/PLAT-03.
- **SCN-THREAT-02** — threat_intel: gate DiscoveryExpert outputs and externalize the relevance threshold
  - axis: `charter-nonbypass` | scope: `scenario:threat_intel`
  - fix: DiscoveryExpert .assess/.propose outputs drive staged proposals with no output_classification=Decision Candidate and no Authority Matrix gate (handler.py:343-357). The relevance threshold (>=0.5, handler.py:348) and finding-type-to-asset routing (handler.py:383-391) are hardcoded — move to fabric.policy. Classify Expert outputs as Decision Candidates.
- **XCUT-FABRIC-01** — Remove use_mocks=True production defaults; gate mocks behind a test/use_mocks boundary
  - axis: `fabric-access` | scope: `cross-cutting`
  - fix: kyc (conductor.py:147), kyc_anthropic (conductor.py:142), cre_underwriting (conductor.py:106), and AML (conductor.py:94 default) construct ToolRegistry(use_mocks=True) in the production path. Default production constructors to a real fabric instance; confine mocks to tests. Many scenarios already have a 'if self.fabric: fabric.docs.get' branch that is simply never reached because no fabric is passed — wiring the fabric makes the existing correct branch live.

### MEDIUM

- **PLAT-03** — Wire fabric.pack as a store property on the KnowledgeFabric facade
  - axis: `pack-registration` | scope: `platform`
  - fix: Surface the existing fabric/pack/ module as a .pack property on KnowledgeFabric (fabric.py) per ARCHITECTURE.md:257-262, exposing a DomainPack loader/registration entry point (YAML-driven init + DomainPackStore registration). Without this, scenarios have no facade-level path to register a pack. Fix before freeze so pack-registration remediation has a real target. FREEZE-BLOCKER for the pack-registration contract surface.
- **SCN-CRE-03** — cre_underwriting: qualify the unqualified CaseFile collision
  - axis: `schema-duality` | scope: `scenario:cre_underwriting`
  - fix: Rename the scenario's class CaseFile (case_context.py:252, re-exported __init__.py:35,49) to a qualified name (CanonicalCaseFile or CRECaseFile) per the 1.4.3 rename decision so it no longer shadows the generic runtime CaseFile (modes/schemas.py:583).

### LOW

- **PLAT-05** — Tighten the 'TraceStep frozen' intent — reconcile inline JAPES scalar fields
  - axis: `charter-nonbypass` | scope: `platform`
  - fix: TraceStep carries typed scalars iteration/duration_ms/notes (trace.py:211-223) labeled 'domain extensions'. They don't violate extra='forbid' (no dict), but they stretch the frozen-schema intent. Before freeze, either bless these explicitly in the TraceStep contract docstring as permanent platform fields or move them off. Low severity; decide so the frozen contract is unambiguous.