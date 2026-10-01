# MACER and JUNO - Alignment with JAPES v2 Canonical Concepts

**Author:** Virendra Mehta
**Companion plan:** `docs/plans/plan_MACER_2_0_CANONICAL_MIGRATION.md`
**Scope:** Living reference for how MACER and JUNO relate to the IIF canonical
object model and JAPES SDK v2. Updated as the platform evolves.

---

## 1. Why this doc exists

MACER and JUNO were built before the IIF canonical object schema was frozen.
Both services use terminology and data structures that predate the five canonical
objects (Policy, Evidence, Decision, Trace, Outcome) and the eight derived objects.

This document maps the pre-existing constructs in each service to their canonical
equivalents, identifies gaps, and states what each service needs to change to
become a first-class participant in the governed learning loop.

---

## 2. MACER

### What MACER is (v1)

MACER is the mortgage document verification engine. It ingests loan documents,
classifies them against the Jazz Taxonomy, runs Jobs-to-be-Done (JTBD)
verification tasks against GSE guidelines (Fannie Mae, Freddie Mac, FHA, VA),
and produces structured findings.

In v1, MACER is a standalone pipeline. Its output is a set of bespoke Finding
and FindingSet entities stored in the Knowledge Hub under a custom ontology.

### What MACER becomes (v2)

In v2, MACER becomes the Mortgage Domain Pack's primary Reasoner. It is no longer
a standalone pipeline - it is one execution runtime among potentially many. Its
output must conform to the canonical object schema so the Governor, compounding
loop, and JUNO can operate on it uniformly alongside outputs from other packs.

---

### 2.1 Canonical object mapping

#### Finding => Decision

A MACER Finding is a per-JTBD judgment: given a policy requirement and the
loan's documents, what is the verdict? That is precisely what a canonical
Decision represents.

| MACER Finding concept | Canonical object / field |
|---|---|
| status (PASS/FAIL/CONDITIONAL/NOT_APPLICABLE/INFO) | Decision.recommendation |
| Rationale text (description) | Decision.rationale |
| GSE guideline reference (policy_ref[]) | Decision.policy_refs[] - each PolicyReference resolves to a versioned Policy object |
| Document extractions (observations[]) | Evidence objects, verification_status: unverified, linked via Decision.evidence_refs[] |
| Confirmed facts (facts[]) | Evidence objects, verification_status: verified, linked via Decision.evidence_refs[] |
| Computed ratios (loan_metrics[]) | Evidence objects, evidence_type: computed, calculation chain in TraceStep |
| Unresolvable condition (conditions[]) | Decision.recommendation: require_approval + CaseContext.pending_dependencies[] |
| JTBD identity (mnemonic, section, section_type) | Decision.domain_extensions - pack-specific, does not override canonical fields |
| Run reference (process_instance_id) | Decision.trace_id pointing to the canonical Trace |

The status-to-recommendation mapping:

| MACER status | Canonical recommendation | Notes |
|---|---|---|
| PASS | allow | Requirements fully met |
| FAIL | deny | Irredeemable failure |
| CONDITIONAL | require_approval | Conditions must be cleared before funding |
| NOT_APPLICABLE | not_applicable | JTBD does not apply to this loan type |
| INFO | info | Informational only, no disposition |

#### FindingSet => CaseFile (derived object)

FindingSet is a per-run container grouping findings by JTBD mnemonic. In
canonical terms this is a CaseFile derived object: an assembled record of all
Decisions for one case, scoped to one evaluation run.

| MACER FindingSet concept | Canonical derived object / field |
|---|---|
| loan_id | CaseFile.case_id |
| findings[] (JtbdFindingGroup array) | CaseFile.decision_refs[] |
| jtbd_set_id | CaseFile.domain_extensions.jtbd_set_id |
| manual_conditions[] | CaseFile.domain_extensions.manual_conditions |
| Run metadata (title, created_at) | CaseFile.domain_extensions.run_name, timestamps |

#### JTBDs and the taxonomy => Policy + CaseContext

The JTBD taxonomy CSV files (income.csv, credit.csv, etc.) are the MISMO-anchored
ontology that drives what verification tasks exist. In canonical terms:

- Each JTBD requirement maps to a Policy object owned by the Mortgage Domain Pack.
  The policy encodes the rule condition (e.g. "2-year employment history required
  for wage earner income") and its GSE source citation in source_refs.
- The JTBD mnemonic (INC-HIS, APR-PTY, etc.) is stored in Policy.domain_extensions.jtbd_mnemonic.
- The CaseContext object for each MACER run carries active_policies[] pointing to
  the relevant policy objects, and domain_extensions.jtbd_group_plan carrying the
  orchestrator's section grouping decision.

#### GSE guidelines => Policy objects

Fannie Mae, Freddie Mac, FHA, and VA guidelines are not single Policy objects.
They decompose into a family of versioned Policy objects - one per distinct
enforceable rule family (LTV schedule, income documentation, appraisal standards,
etc.).

Key schema fields:

- policy_type: regulatory for GSE rules
- source_refs[] carries the guide title, edition, and section code
  (e.g. "FNMA Selling Guide Nov 2025, B3-3.1-07")
- jurisdiction: "US" for federal programs
- effective_date / expiry_date / supersedes handle guide version updates
- overlay_id on the Policy object carries the lender's certified client overlay
  when the lender has tightened a threshold (e.g. LTV 97% to 95%)

The policy_ref string MACER agents currently produce (e.g. "Fannie Mae Selling
Guide.md [Page 316] B3-3.1-07 Verbal Verification of Employment") must be
resolved to a policy_id at conversion time. The PolicyResolver class
(Phase 3 of the migration plan) handles this lookup.

#### MLflow spans => Trace + TraceStep

MACER already instruments every section run with @mlflow.trace decorators.
These spans map directly to canonical TraceStep objects:

- Each section (_process_section_traced) is one TraceStep
- Span inputs/outputs carry the evidence and decision payload
- The MLflow run_id becomes Trace.trace_id
- Token cost and latency in span metadata become TraceStep.metrics

The canonical Trace is the audit-ready version of what MLflow already captures.
No new instrumentation is needed - the migration is about emitting the governed
object from existing span data.

---

### 2.2 What MACER does NOT need to change

- The JTBD verification agent logic (jtbd_agent.py, jtbd_runner.py) does not
  change. It still produces JTBDResult Pydantic objects. The canonical mapping
  happens in findings_converter.py, not in the agent.
- The document classification taxonomy (CSV files) is preserved as-is. Taxonomy
  entries become the MISMO SEO class anchors in the pack manifest.
- The findings CSV format is preserved for the CLI eval workflow.
- The bespoke Finding / FindingSet KH upload path stays alive during the
  v1-to-v2 transition period, controlled by MACER_EMIT_CANONICAL env var.

---

### 2.3 New patterns MACER must adopt

1. Policy object awareness. The findings_converter.py needs a PolicyResolver
   that maps section codes from policy_ref strings to canonical policy_id values.
   Initially this can be a YAML-backed registry; eventually it queries the pack's
   policy fabric.

2. Evidence provenance discipline. The distinction between observations (raw
   extractions, unverified) and facts (confirmed, verified) must be preserved in
   canonical Evidence objects via verification_status. This is already in the
   MACER model - it must be maintained in the canonical output.

3. Condition routing. CONDITIONAL findings with conditions[] must populate
   CaseContext.pending_dependencies[] so the Flowable process can wait on
   condition resolution. The responsible_party field on each condition maps to
   the authority_matrix entry on the governing Policy object.

4. Trace linkage closure. Every canonical Decision emitted must carry trace_id
   pointing to the Trace for that run. Every Evidence object must carry trace_id
   as well. Without these links the compounding loop is broken.

---

## 3. JUNO

### What JUNO is

JUNO is the JazzX AI assistant platform - a skills-based agent service that
exposes domain capabilities to human users. Skills are discrete units of
capability (e.g. macer-analyzer, jazzx-architecture, eval-specialist). Each
skill has a SKILL.md instruction set and an optional skill.yaml declaring tools
and MCP servers.

JUNO interacts with MACER primarily through the macer-analyzer skill, which
reads MLflow traces and artifacts to surface MACER run results to users.

### 3.1 What needs to update in JUNO

#### macer-analyzer skill

The macer-analyzer skill currently reads MACER v1 output: Finding entities,
FindingSet containers, and MLflow traces. After the canonical migration, the
relevant artifacts are canonical Decision, Evidence, and Trace objects.

Required updates to skills_data/macer-analyzer/SKILL.md:

1. Add a section describing the canonical object chain and how to interpret it:
   - Decision objects are the primary output (one per JTBD mnemonic)
   - Evidence objects are the document citations linked to each Decision
   - Trace is the per-run audit record; steps map to sections
   - CaseFile is the run container (replaces FindingSet)

2. Update the prime_trace_summary interpretation: the canonical CaseFile
   replaces FindingSet as the top-level run container. The decision_refs[]
   on the CaseFile are the canonical equivalents of finding_ids.

3. Add a PHASE 1b step: when a CaseFile entity is available in KH, prefer
   reading canonical objects over FindingSet/Finding entities.

4. Status breakdown vocabulary: map canonical recommendation values back to
   the PASS/FAIL/CONDITIONAL display language users expect.

During the transition period (while MACER_EMIT_CANONICAL is being ramped),
the skill must handle both v1 Finding entities and v2 canonical objects
gracefully - check for canonical objects first, fall back to v1 if absent.

#### jazzx-architecture skill

The references/macer.md reference doc in skills_data/jazzx-architecture/
needs to be updated to reflect:

1. MACER is now a Domain Pack, not a standalone pipeline. Reference the
   canonical object chain and how MACER emits each object.
2. The JTBD -> Policy mapping: JTBDs are the runtime expression of Policy objects.
3. The Finding -> Decision mapping: the v1 terminology maps to canonical terms
   as documented in Section 2.1 above.
4. Remove or update the v1 JTBDResult Pydantic model diagram - replace with
   the canonical output schema.
5. Add a "Canonical output" section with the five objects and what each contains
   for a mortgage underwriting run.

#### New skill: mortgage-pack-analyzer (future)

Once the Mortgage Domain Pack is live, a dedicated skill for pack-level analysis
should be created. Unlike macer-analyzer (which focuses on MLflow execution),
mortgage-pack-analyzer would:

- Read canonical Decision and Evidence objects from KH
- Surface policy compliance chains (Decision.policy_refs -> Policy.source_refs)
- Present override events and exception approvals
- Show outcome linkage when post-close results feed back

This skill is not part of the current migration scope. It is noted here as the
natural next step once canonical output is stable.

---

### 3.2 What JUNO does NOT need to change

- The skills framework itself (agent.py, skill loader, profile system) is
  unchanged by the canonical migration.
- Skills that do not interact with MACER output are unaffected.
- The MLflow integration (mlflow_gateway.py, mlflow_trace_processor.py)
  continues to work as-is - canonical Trace objects complement MLflow, they
  do not replace it.

---

## 4. Shared terminology reference

This table is the authoritative mapping between MACER v1 terminology, JUNO skill
language, and canonical object language. Use this when updating skill instructions
or when writing documentation that spans both services.

| MACER v1 term | JUNO skill language | Canonical term | Notes |
|---|---|---|---|
| Finding | Finding / Determination | Decision | One per JTBD |
| FindingSet | Execution summary | CaseFile | One per run |
| Observation | Document citation | Evidence (unverified) | Raw extraction |
| Fact | Confirmed value | Evidence (verified) | Cross-checked |
| Loan metric (LTV, DTI) | Key indicator | Evidence (computed) | Calculated from facts |
| Policy ref / section code | Guideline reference | Policy.source_refs | Versioned policy object |
| Condition | Open item | pending_dependency | Blocks funding |
| Responsible party | Assignee | authority_matrix entry | Who clears the condition |
| JTBD mnemonic | Verification task | Decision.domain_extensions.jtbd_mnemonic | Pack-specific |
| Section | Analysis domain | TraceStep | Income, Credit, Appraisal, etc. |
| Run | Execution | Trace | MLflow run = canonical Trace |
| Process instance ID | Run ID | Trace.trace_id | Links decisions to trace |
| PASS | Approved | Decision.recommendation: allow | |
| FAIL | Rejected | Decision.recommendation: deny | |
| CONDITIONAL | Suspended / Open items | Decision.recommendation: require_approval | |
| NOT_APPLICABLE | N/A | Decision.recommendation: not_applicable | |

---

## 5. Open questions

1. Policy YAML authorship. The policy YAML files for Phase 3 need domain SME
   review. LLM-bootstrapped content is a starting point; human review moves the
   SME bottleneck from blocking to refining.

2. Canonical ontology ID in KH. The canonical ontology (Decision, Evidence,
   Trace, Outcome, CaseFile) needs to be registered in the production Knowledge
   Hub before Phase 2 can deploy. This is a platform ops task, not a code task.

3. Transition period duration. The v1 FindingSet path stays live until the
   JUNO macer-analyzer skill and any downstream Flowable processes consuming
   FindingSet entities are migrated. Timeline TBD.

4. Outcome linkage. The Outcome object (post-close results: buyback events,
   investor rejection, QC failure) is not yet wired. MACER emits no Outcome today.
   This requires a separate integration with the loan servicing system. Deferred
   to a future plan.
