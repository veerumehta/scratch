# Caller Migration Plan — jaci & k9 (downstream of JAPES freeze-prep)

**Status:** ✅ FULL CLEAN PASS COMPLETE (2026-06-07). jaci: 317 passed, 17 skipped
(all env/API-key), 0 non-env failures. k9: 62 passed, 0 failures. All changes
UNCOMMITTED in both repos pending review (do not push).

## Residual observations (not failures; tracked for follow-up)

- **AML-02 (audit):** jaci's `CanonicalTrace` requires the v1.5 base fields
  (status/started_at/pack_version/binding_id/deployment_id) but the AML Conductor
  doesn't populate them — only the eval test fixture now does. The Conductor should
  populate real values (or the domain trace should default them). Open governance call.
- **Stray `.bak` artifacts** beyond the deleted `kyc_registry.py.bak`: `.env.bak`,
  `tests/unit/test_policy_clause.py.bak`, `prompts/gpt-5.2.bak`, `prompts/gpt-5.4-mini.bak`,
  `tests/fixtures/policy_registry.py.backup`. Left in place (only kyc_registry.py.bak
  was named for deletion); review/remove as desired.

## What was done this pass (summary)

- Conductor: register only Policy/Playbook Expert surfaces (`_register_aml_pack_experts`);
  Investigative/Governance/Evidence stay Skills, out of ExpertRegistry.
- Tool tests migrated off `use_mocks` to fabric TEST mode (`tests/fixtures/tool_fabric/`);
  `mock_connectors.py` marked deprecated.
- Policy shim: fixed `AML_POLICIES` (AML-only), added `REGISTRY` alias, get_rule/get_policy
  fall-through, get_clause sunset/legacy warnings; updated stale count/type test expectations
  to the real merged composition (AML 4 + KYC 4 = 8).
- CaseContext: added `case_id` property; tests use `.open()` API + full canonical objects.
- Curator: jaci `process_evaluation_report` now parses bracket-tagged string signals.
- prompt_loader: fixed `repo_root` (was off by one → tuning never appended).
- API-key tests marked `@pytest.mark.requires_api_key` (conftest skips without key).

---
(original plan below)

**Status:** ONGOING — accumulates as JAPES-side freeze-prep lands. Execute against
the caller repos *after* the JAPES platform changes are complete.

**Repos:** `../jaci`, `../k9` (also check `../k9-ui`, `../pers-k9` if they import jazzx_sdk).

**Purpose:** Each PLAT-/XCUT- change to the JAPES schema layer has downstream
consequences in the Domain Pack repos. This plan records those consequences so the
caller updates can be done in one coordinated pass without re-deriving the impact.

---

## How to use this doc

For each completed JAPES change below: status legend — `[ ]` not started · `[~]`
in progress · `[x]` done. Verify each caller item with the listed check before
marking done. Add new sections as further JAPES changes land.

---

## From JAPES 1.6.3 — PLAT-01 (schema consolidation)

`Attestation`, `Freshness`, `Outcome` are now single-sourced in `fabric.canonical`
and re-exported from `modes.schemas`. Identity-equal: `modes.schemas.Outcome is
fabric.canonical.outcome.Outcome`.

**Blast radius is small** — most jaci usage already sources canonical:

- [ ] **jaci `src/jaci/schemas/japes_types.py:38`** — the `Outcome` re-export from
  `jazzx_sdk.modes.schemas` now resolves to canonical `Outcome` (typed
  `outcome_type`, required `decision_id`/`trace_id`), not the old operational
  `outcome_class` shape. **Action:** repoint explicitly to
  `from jazzx_sdk.fabric.canonical import Outcome`, or drop the re-export (it is
  vestigial — nothing constructs `japes_types.Outcome`).
  **Verify:** `grep -rn "japes_types import Outcome\|japes_types.Outcome" ../jaci`
  returns no live consumers; `python -c "import jaci.schemas.japes_types"` clean.

- [x] **jaci `scenarios/aml/schemas/outcome.py` + eval tests** (`outcome_class=`
  sites) — these use jaci's OWN `Outcome(_OutcomeBase)` subclass that already
  extends canonical `Outcome`. **No change needed** (confirmed not modes-sourced).

- [x] **Attestation / Freshness** — jaci sources these from `jaci.schemas.evidence`
  (canonical re-export); no `modes.schemas` imports of them in jaci or k9.
  **No change needed.**

- [ ] **k9 full sweep** — initial grep found no `modes.schemas` imports of
  Attestation/Freshness/Outcome and no operational `outcome_class=` construction,
  but k9 was not exhaustively audited. **Action:** confirm during the caller pass.
  **Verify:** `grep -rn "modes.schemas import" ../k9 ../k9-ui ../pers-k9 | grep -iE "outcome|attestation|freshness"` empty.

---

## From JAPES 1.6.3 — PLAT-02 (DomainPack v1.5 manifest)

Additive on the platform side (new fields + `DomainPackHelper`), so **nothing
breaks**. The downstream work is *adoption* — this overlaps the drift-audit
pack-registration backlog (SCN-*-PACK items in `plan_II_drift_audit_2026-06-07.md`).

- [ ] **Each certifiable jaci scenario registers a typed DomainPack** via
  `DomainPackHelper.from_yaml(manifest)` → `fabric.canonical.put_domain_pack(pack)`
  at handler startup. Author a governance-manifest YAML per scenario carrying the
  v1.5 minimums (registry/matrix versions per activated mode + D63, SEO/IPDV/skill
  bundle versions). See `DOMAIN_PACK_QUICKSTART.md` two-step pattern.
  Priority order from the audit: aml (reference) → cre_underwriting → kyc_anthropic
  (strongest policy infra) → others.
- [ ] **Move autonomy ceilings out of code literals** into
  `supported_autonomy_range` + Authority Matrix (audit AML-04, SCN-EARN-02).
- [ ] **Integration checkpoint:** first real-KH `put_domain_pack` write — verify KH
  accepts `ontology_id=None` for `canonical_domain_pack`, or thread an ontology id.

---

## From JAPES 1.6.3 — PLAT-04 (cognitive-shape scoping + TransactionContext)

`Context[T,T,T]` is now scoped as the investigation contract; new
`TransactionContext[TInput, TOutput]` is the single-pass shape for transactional/
automation surfaces. Additive on the platform side — **nothing breaks** — but the
bypassing scenarios should adopt the right contract instead of hand-rolling state.

- [ ] **ci_spread → `TransactionContext[LoanApplication, CreditDecision]`** — replace
  the bespoke single-pass flow (conductor stores `ctx` but never reads it;
  `iterations=1`) with `TransactionContext`. Also rename its colliding
  `class CaseFile` (schemas.py:87) to a qualified name (audit SCN-CISPREAD-03), and
  decide promotion: emit canonical Decision/Outcome or formally de-scope as a demo.
- [ ] **threat_intel → `TransactionContext[ScanConfig, UpdateProposal]`** — model the
  scan→assess→propose run as a single-pass producer with N outputs. Classify the
  Expert outputs as Decision Candidates and gate them (audit SCN-THREAT-02); define
  the governed-output promotion (UpdateProposals → reviewed Decisions).
- [ ] **kyc / kyc_anthropic / earnings** — these ARE investigative; they should adopt
  the typed `InvestigationContext` (= `Context`) properly rather than dict-list
  mimics (audit SCN-KYC-01, SCN-KYCA-03, SCN-EARN-03). Not TransactionContext.
- [ ] **cre_underwriting** — already fits the investigation loop; no shape change,
  but rename its colliding `class CaseFile` (case_context.py:252) per SCN-CRE-03.

**Decision aid:** investigation shape = hypotheses + evidence attestation +
iterate-to-convergence. Transactional shape = single-pass input→output(s), no
hypotheses, no loop. See `DOMAIN_PACK_QUICKSTART.md` "Choosing a cognitive shape".

## From JAPES — XCUT-OUTCOME-01 (live outcome linkage)

**JAPES-side status: COMPLETE (docs only).** The platform mechanism already
existed — `put_case_file(outcome=)` and the deferred `put_outcome(outcome,
ontology_id)` (store.py:1130), with the canonical `Outcome` enforcing
`decision_id`/`trace_id` linkage at construction. No platform code change was
needed; the two-phase pattern is now documented in
`DOMAIN_PACK_QUICKSTART.md` ("Closing the Compounding Loop").

**Correction to the audit's one-liner.** AML-01 / XCUT-OUTCOME-01 in
`plan_II_drift_audit_2026-06-07.md` say "Conductor calls `from_case_file` and
passes `outcome=` to `put_case_file`." That is mis-specified: the Outcome depends
on the human-review result (`sar_filed`, `human_override`), which does **not**
exist when `run_investigation` finishes. The correct shape is **two-phase**:

- **Phase 1 (already correct)** — `japes_handler.py:181` persists Decision+Trace
  via `put_case_file` at case completion. Leave `outcome` omitted here. **No change.**
- **Phase 2 (the actual gap)** — there is no live review-completion path that
  creates the Outcome; only the eval harness does (via gold labels). 

**Caller work (jaci):**

- [ ] Add a **review-completion handler** (L3/FIU/BPMN) that, on human review of a
  case, calls `Outcome.from_case_file(case_file, sar_filed=..., human_override=...)`
  (jaci `scenarios/aml/schemas/outcome.py:65`, already exists) and persists via
  `ctx.runtime.fabric.canonical.put_outcome(outcome, CANONICAL_ONTOLOGY_ID)`.
  **Verify:** a reviewed case yields a persisted `canonical_outcome` entity whose
  `decision_id`/`trace_id` match the Phase-1 Decision/Trace.
- [ ] Repeat the Phase-2 review-completion path for each scenario that reaches a
  human-review stage (audit: 6 of 7 scenarios currently never create an Outcome).
- [ ] **Design note for jaci:** decide where the review-completion event lives
  (BPMN handler vs. a dedicated review endpoint). The eval harness's synthetic
  `from_case_file(human_reviewer_id="eval_harness")` call is the template.

**Platform decision (resolved):** `from_case_file` stays **pack-owned** (the
review-result → `Outcome.result` mapping is domain-specific). JAPES does not add a
generic factory — the canonical `Outcome` constructor already enforces linkage,
and `put_outcome` is the documented deferred entry point.

---

## Reference

- Drift audit + full backlog: `docs/plan_II_drift_audit_2026-06-07.md`
- Pack manifest + registration pattern: `docs/DOMAIN_PACK_QUICKSTART.md`
- Changelog for the platform changes driving this: `CHANGELOG.md` [1.6.3]
