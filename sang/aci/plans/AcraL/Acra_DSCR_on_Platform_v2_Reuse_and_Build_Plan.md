# Acra DSCR on Platform v2 / JAPES SDK — Reuse Map, Gap List, and Build Plan

Author: Virendra Mehta · 2026-08-13 (rev 2, code-verified) · Sources: `CommercialDSCRLoanProcessFlow from Acra July 2026.pptx` (23 slides), `JazzX – Acra Proposed Deployment Approach.pdf` (28 slides, Aug 2026), `acrawsratematrixdscrsummary.pdf` (DSCR Program Summary, version 6.15.2026 V1.1)

**Audited against code, not docs:** japes `2.4.1` (HEAD `3dfe178`), jaci HEAD `5719cf4`. Four claims from the 2.3.6-era project docs are now stale and are corrected below — all in the same direction: plumbing that was "declared but unwired" got wired.

## TLDR

The Acra deck's 18-week, four-phase plan is **credibly fast for Phase 0 and Phase 1, and not credible as written for Phases 2 and 3** — a clean inversion of where the deck puts its risk. Phase 0 (split, classify, index, assess against one investor's guidelines, no integrations) is the part the SDK already largely ships, and Acra's rate matrix is an unusually tractable policy corpus: a bounded, versioned grid, not 327 prose directives. Phases 2 and 3 rest on things that **do not exist in either repo**: an LOS/Byte adapter, any Integration Hub client, and an appraisal-driven LTV calculator.

Three verified findings that change the plan:

1. **Carve a new `acra_dscr` scenario.** Verified cheap: the only mandatory wiring is one entry in the `SCENARIOS` list at `jaci/src/jaci/ui/registry.py:96`. Verified expensive to fold in: `cre_underwriting` has no pack manifest at all, so there is no overlay slot to hang Acra on, and its mock connectors hardcode Mesa Verde in 16 places.
2. **The eligibility grid needs one new `Condition` kind.** The policy IR ships exactly four kinds and no matrix/table/lookup among them. Acra's 78-cell grid is expressible today only as 78 rules with 78 profile keys, or as `if()` chains that bury the numbers in formula strings. A `MatrixCondition` is additive — `register_condition_evaluator` is genuinely open — and is the single highest-leverage platform ask this engagement generates.
3. **Two structural blockers nobody had on the list.** HITL suspend raises inside a `Loop` (`japes/jazzx_sdk/conductor/engine.py:310-315`), which is exactly the shape of Acra's per-condition and per-property exception approvals; and `search_<name>` on a docs source is **metadata-only** (`agents/interactive/reads.py:69-70`), so retrieving a guideline or overlay *by content* has no fabric primitive behind it.

## 1. What Acra is actually asking for

| # | Block | Anchored in |
|---|---|---|
| B1 | Split / classify / index to Acra's taxonomy | Setup Stage 1 offshore indexing; Phase 1 |
| B2 | Guideline assessment vs. investor eligibility matrix | UW Stage 2 "program eligibility"; Phase 0 + 2 |
| B3 | Missing-doc conditions → broker outreach protocol | Slides 6, 8 (6-point checklist, 48-hour escalation) |
| B4 | Cross-document discrepancy conditions | Slide 11 (DataVerify, title transfers, LLC as Borrower 1) |
| B5 | Bidirectional Byte condition sync | Phase 2; Byte Doc Drawer Commercial v2.0 |
| B6 | Third-party vendor orders | SiteX, DataTree, Clear Capital, DataVerify, Funding Shield, PB&G, NMLS, Salesforce, USPS, Redfin |
| B7 | DSCR / LTV / reserves / NOI worksheets, auditable | Phase 3 |
| B8 | Six role assistants + handoffs | Deck slide 6 |

## 2. The policy corpus is the good news

The DSCR Program Summary is materially easier to formalize than the CRE precedent (327 UW directives across 5 asset classes), and this is the strongest argument for a short Phase 0.

Counted from the document:

- **78 grid cells** — three loan-amount bands (≤$1.5M, $1.5M–$2M, $2M–$3M) × FICO tiers (10 / 10 / 6) × three purposes (Purchase, R&T, Cash-Out), including explicit `NA` cells (band 2 at 620 R&T/C-O; band 2 <620; band 3 <700).
- **~15 overlay families**, each already a max-CLTV / min-FICO / min-DSCR triple: citizenship (5 types; Foreign National priced at FICO 700), property type (8 types; non-warrantable condo, condotel/PUDtel, manufactured, 2–4 unit, each with its own caps plus a **−5% CLTV Florida modifier**), occupancy (STR; vacant-property R&T and C-O rules), location (ineligible AK/ND/SD; declining market −5%; rural/unique), credit events (mortgage history 1x30x12 → 0x120x12 ineligible; BK/FC by months; short sale/DIL/mod), tradelines and thin-file, escrow waiver, FTHB, product/ARM (margin by FICO band, 2/2/6 caps, 1-yr CMT), IO minimums.
- **Cross-cutting DSCR gates**: LTV > 80% → min DSCR 1.20 **and** 6 months PITIA reserves **and** property type restricted to SFR / warrantable condo outside Florida / townhome / PUD; DSCR < 1.0 or No Ratio → CLTV 75/70/65, min FICO 640; loan > $2M → DSCR ≥ 1.0; FICO < 620 → 12 months reserves.
- **14 prepay-penalty rules across 13 states**, several conditioned on entity-vs-individual vesting, loan amount, and rate (Illinois has two rules; Pennsylvania keys on `<$319,777`).

Three properties make this cheap: it is **already versioned** (`6.15.2026 V1.1`), so it maps onto Policy versioning without inventing change control; the rules are **numeric and testable**, so they land as typed `Rule` records rather than `NaturalLanguageCondition`; and the **PPP state rules are a jurisdiction filter**, which is what ABA §7.1 `jurisdiction_filter` and overlay §11.1 "jurisdiction selection" exist for.

Do not lose the tail: entity-vs-individual vesting drives PPP buyout in 4+ states, so the Legal/Entity assistant's output is an **input to a pricing-adjacent rule**, not a parallel workstream. That coupling is absent from the Acra deck.

### 2.1 How the grid actually encodes — and the one platform ask

`fabric/canonical/policy.py` ships exactly **four** Condition kinds: `Expression` (flat field/op/value, `:155`), `DslExpression` (`:180`), `RatioCondition` (`:195` — threshold must be `profile:<key>`, never a literal), `NaturalLanguageCondition` (`:224`). The registry is open and keyed on kind (`condition_evaluator.py:68-81`); an unregistered kind raises a deliberate `KeyError`. `Rule.applicability` — a second orthogonal Condition acting as a cheap "does this rule apply" pre-check — is what makes the overlay families tractable.

Two encodings are possible today, and both are bad:

- **78 rules**, each `applicability` a band/tier/purpose predicate and `condition` a `RatioCondition` with `threshold="profile:ltv_1m_fico740_purchase"` → 78 profile keys. Governance-reviewable, unmaintainable, and `PolicyProfile.get()` is a flat single-level fail-closed lookup (`fabric/canonical/profiles.py:52-60`), so there is no nesting to lean on.
- **~15 rules** with nested `if()` chains over band and FICO → compact, but buries the 78 numbers inside formula strings and defeats the `RatioCondition` "never a literal" discipline that exists precisely so thresholds stay reviewable.

**Ask: a `MatrixCondition` / `TableCondition` kind (declared axes + banded cells) plus profile support for table-valued keys, and secondarily a set-membership operator** (there is no `in` over 13 states without 13 rules or a DSL `or` chain). This is additive, not a platform rewrite, and it generalizes immediately — every investor grid, rate sheet, and pricing matrix in mortgage and non-QM has this shape. Frame it as platform work Acra funds, not Acra-specific work.

## 3. Reuse map — verified

| Block | Shipped and reusable (verified) | Net-new for Acra |
|---|---|---|
| B1 | `jazzx_sdk/agents/document/` — 970 LOC, the most disciplined subsystem in the tree. Ingest→classify→extract→emit (`agent.py:4-6`), `SourceCoordinate`+`Confidence` per value, typed `Refusal` below floor, `admission_floor=0.7` / `ungrounded_score=0.5` (`spec.py:11,29-32`), `FieldAttestation` override (`schema.py:71`), content-addressed ingest `src_{sha256[:16]}` (`schema.py:44-45`), `split_document` outline-first then per-page LLM (`tools/documents/split.py:94-130`), `check_completeness` → `{required, present, missing, unexpected, by_type, is_complete}` (`completeness.py:20-58`). **New since the docs:** `manifest.py` content-hash incremental reprocessing, `spec.chunk_chars`, `templates`/`collection_id`/`ontology_id` routing | `TEMPLATES._TIER1` holds exactly `10-k` and `financial-statements` (`tools/documents/templates.py:77-92`) — **zero mortgage content**. Every Acra type (lease, rent roll, Form 1007, appraisal, title, Operating Agreement, Articles, Good Standing, HOA budget, DataTree tax cert, flood cert) is tier-2 pack work via `register_dict` / `load_yaml(path, tier=2)`. Acra's taxonomy does not exist yet — deck slide 20 lists it as an input to request |
| B2 | Four-kind typed policy IR + open registry; `Rule.applicability`; `AuthorityMatrixV2`; jaci `capabilities/commercial_lending/policies.py:339-358` threshold-rule eval with `ComparisonOperator` covenant tuples (`COV-dscr` GTE 1.25, `COV-ltv` LTE 65.0, `COV-debt-yield` GTE 8.0) | **No eligibility/guideline/rate-grid concept exists anywhere** — repo-wide zero hits for eligibility matrix, rate sheet, pricing grid. Every "matrix" hit is the *authority* matrix (a who-may-act grid, not a credit grid). Plus the `MatrixCondition` ask in §2.1 |
| B3, B4 | Real typed conditions in jaci: `ConditionType` = prior_to_closing / prior_to_funding / post_closing / ongoing_covenant (`cre_underwriting/schemas/case_context.py:61-67`), `LoanCondition` (`:201-212`), `UnderwritingRecommendation.max_ltv/min_dscr/conditions/exceptions_requested` (`:215-240`). Byte PTC/PTF maps onto the first two buckets directly. Canonical `Decision`/`Outcome`, `OverrideEvent` 8-code taxonomy, `check_completeness` for missing-doc detection | Acra's discrepancy set: lease rent vs. Form 1007 market rent variance; borrower/entity name across 1003 / entity docs / title / credit; LLC-as-Borrower-1; expiry rules (credit report, appraisal, Good Standing). Note "stipulation" has **zero hits** repo-wide — vocabulary alignment with Acra needed early |
| B5 | The surrounding machinery only: `conductor` pipelines, `SuspendRun`/`DurableSuspension`, `CaseContext`. **Corrected:** idempotency is now wired — `QueueProcessor(idempotency_store=…)` consulted at `queue_processor.py:163-164`, written at `:370-376`, with `EntityIdempotencyStore` and `DbIdempotencyStore` backends | **The whole adapter.** No Integration Hub client (`tools/base_registry.py:45-57` — it appears only inside the class docstring's example); `connectors/` is `api_poller, base, catalog, rss_feed, web_search`; zero hits for Encompass, nCino, Blend, Byte. **And the idempotency default is `None`**, so unless Acra's sync explicitly passes a store, restarts re-process and duplicate condition writes |
| B6 | Generic REST connectors; mock connector pattern (`cre_underwriting/tools/mock_connectors.py`) | 10 vendors, several **portal-only** (DataTree vendor-restricted, PB&G a portal). `BaseToolRegistry.register_tool` has `timeout` and `stop_on_fail` but **no schema field** (`:85-93`) — no IO contract for vendor payloads |
| B7 | Expression DSL, full (`jazzx_sdk/expressions/{parse,evaluate,validate,definition}.py`, `if/min/max/cap/prior/avg/cagr/ltm/sum_entities`, `evaluate.py:279-321`); `LineVocabulary` (`finance/vocabulary.py`); `WorkbookLayout` + `load_workbook_layout` (`finance/workbook.py:163-174`); real DSCR computation in three places (`cre_underwriting/operating_spread.py:22,49` from parsed T-12; `portfolio_monitoring/monitoring.py:24-43` `DscrReconciliation` with bank-side vs. attested and `in_breach`; `capabilities/commercial_lending/analytics.py:266`) | **`OutputTemplate`, `TemplateField`, `TemplateFillAgent`, `FilledTemplate`, `induce_template`, `Skill.applies_to`, `detect_scale_errors`, `detect_hardcoded_plugs` — all zero hits. Still proposed, not shipped.** And **there is no appraisal-driven LTV calculator**: `ui/property_case_page.py:83` `"ltv_pct": None  # purchase price assumed -> needs appraisal (data gap)`, `demo_page.py:44` "book LTV proxy… true LTV needs an appraisal", `max_ltv: 0.75` hardcoded in a mock at `tools/registry.py:505`. LTV is the *primary* Acra grid axis, so this is a real build, not a reuse |
| B8 | `InteractiveAgent`/`InteractiveAgentSpec`/`Skill`; `ProfileRegistry.validate()`; `as_tool` sub-agents; `Skill.spec_ref` composed skills; `PermissionScope` (deny-wins, `narrow()` never widens); `resolve_effective_autonomy`. **Corrected:** `Skill` now has `inputs`/`outputs`/`version`/`visibility`/`invokes` — but the docstring says outright "Optional and UNVALIDATED at runtime… nothing reads it yet". `Skill.reads` IS shipped and generates authority-gated `list_/read_/search_` tools over `fabric.docs` (`agents/interactive/reads.py:54-74`) | Six ABAs + one relay family (§6). And the legacy push path is still unfixed: `knowledge.py:115` still emits `f"[doc] {name}"` — filename only, no content |

## 4. The items that will actually cost money

Revised against code. Four doc-era gaps are now closed; two new structural ones surfaced.

**Still real, ordered by how much they block:**

1. **Byte adapter (B5).** The largest unbudgeted item, and there is no substrate to start from. Verify against Byte's contract, not the deck: does Byte expose webhooks for `condition cleared / waived`, or is this polling? The deck's own slide 26 asks this, which means it is unknown, which means Phase 2's five-week window is a guess. Pass an `IdempotencyStore` explicitly — the default is `None`.
2. **HITL suspend cannot occur inside a `Loop`.** `conductor/engine.py:310-315` raises `RuntimeError("conductor: approval suspend requested inside loop … supported only for top-level steps")`. Acra's conditions loop (slide 10 step 03, "no queuing, no delay") and any per-property exception approval are loops. Either a platform fix or a pipeline shape that flattens approvals to top level — decide deliberately, don't discover it in week 9.
3. **No appraisal-driven LTV.** LTV/CLTV is the primary axis of all 78 cells and there is no calculator, only a book-LTV proxy and an explicit `# data gap` comment. Includes the lien-stack and HELOC rule (CLTV computed on the greater of credit-line limit or current balance).
4. **`MatrixCondition` for the eligibility grid** (§2.1).
5. **Content search over guidelines has no primitive.** `search_<name>` is metadata-only, id/name (`reads.py:69-70`). Retrieving "which overlay applies to a non-warrantable condo in Florida" by content needs either a `fabric` content-search primitive or the pack pre-indexing the grid as structured rules — the latter is the better answer and reinforces the `MatrixCondition` ask.
6. **No parent→sub-agent state channel.** Only the LLM-authored argument string plus `scope` crosses; sub-agent state dies at the `as_tool` return. With six assistants over one loan file, each re-reads and re-extracts. Hits hardest because Acra's design point is **concurrent** AM and UW work (slides 12–13), not sequential.
7. **Prompt corpus and the scanned-document path.** The precedent build's "declarative" pack data is 63 KB / 1,400+ lines of hand-tuned adversarial prose — "none of it transfers to another domain." Budget a fresh DSCR corpus. And `split_document` raises `DocumentNotReadableError` on scanned files (`split.py:114-118`); split does **not** auto-invoke DocIntel, the caller must convert first (`conversion.py:15`, `docintel_azure.py`, tiered fallback tested). Broker-submitted DSCR packages are scan-heavy: **price DocIntel per package in week 1**.
8. **No approver enforcement.** `DurableSuspension` now carries `approver_ref: ActorRef`, `authority_basis`, `approved_at` (`conductor/suspension_store.py:56-65`) — but all three default to `None` and nothing forces an approver on resume. `resolution` is still `Any | None`. For Acra's "defensible audit trail for every cancellation decision," make these required at the pack boundary.
9. **`fabric/opa/store.py:34-55`** — still four `raise NotImplementedError(_NOT_WIRED)`. Relevant if Rego-backed policy was assumed anywhere in the plan.

**Closed since the docs — remove from the risk register:** retry now wraps every provider at `llm/manager.py:579-586` (`routing.py:1-24` formally deprecates `RetryConfig`/`RetryStrategy`); idempotency has two durable backends and a real constructor seam; `DurableSuspension` gained approver fields; RAG attribution now **fails loud** — `fabric/rag/store.py:28-45` raises `KnowledgeFabricError` on an unresolvable `document_id` ("an unattributed chunk reaching a SAR narrative … is worse than a missing one").

## 5. Where it lives: verdict and wiring cost

**Carve a new `acra_dscr` scenario. Do not fold into `cre_underwriting`.**

Scenarios are cheap and numerous — 12 on disk (`aml` 6,483 LOC, `ci_spread` 5,992, `cre_underwriting` 4,002, `earnings_anthropic` 3,900, down to `clinical_intake` 521; `kyc` and `threat_intel` exist but are unregistered and effectively dead). There is **no scenario base class and no auto-discovery** — `src/jaci/scenarios/__init__.py` is a docstring.

**Evidence against fold-in:**

- `cre_underwriting` has **no pack manifest at all** — `config/packs/cre_underwriting_core/` contains only `mode_tuning/`, and its policies live in-scenario at `policies/policies.yaml` (`CRE_CORE_COVERAGE_POLICY` DSCR≥1.25 at `:15-24`). The overlay mechanism that would make fold-in cheap **is not in use there**, so there is no `policies.overlays` slot to hang Acra on.
- Customer content is baked into the mock layer: `property_name: "Mesa Verde Apartments"` at four sites in `tools/registry.py` (`:374/:400/:427/:491`), `max_ltv: 0.75` hardcoded at `:505`, and a two-item literal deal selector at `ui/demo_page.py:149` — 16 Mesa Verde hits total. Threading a second customer's layout through that is exactly the coupling the CL demo plan prohibits.
- Precedent: `insurance_diligence` (1,007 LOC) was split **out** of `cre_underwriting` for this reason — `cases.py:6`, "Insurance-compliance diligence lives in its own scenario."

**Evidence that carve-out is cheap — the full wiring checklist:**

1. **`ui/registry.py:96` `SCENARIOS`** — one `Scenario(...)` entry (`key, label, icon, display, dashboard_target, demo_target, pack_id, gold_dir, pipeline_target, focus_pipeline_target, focus_handoff, policy_resolution_target`, defined `:23-56`; all targets lazy `(module, attr)` pairs). **This is the only mandatory edit** — nav, landing, Concepts, and Dashboard all derive from it.
2. `ui/common/data_loaders.py:137-148, 228-236` — string-literal `scenario ==` branches for trigger-field filtering and gold-case dirs; needed if using the Dashboard eval stack.
3. `tests/eval/gold_cases/<gold_dir>/` — JSON gold cases; required for the Concepts case-fleet view (`ui/concepts_view.py:277-280`).
4. `ui/pages/dashboard.py:25-41` — a second, redundant hardcoded router paralleling `ui/dashboard_view.py:60`. Only if routed through it. *(Worth deleting rather than extending.)*
5. Optional pack at `config/packs/acra_dscr_core/pack_manifest.yaml`, resolved lazily at `ui/registry.py:78`; `FileNotFoundError` → `None`, so a pack is genuinely optional. `app.py` needs **no edit** — tabs derive from `has_demo`/`has_dashboard`. Modes need no registration.

**Reuse without forking:** the mass is not `scenarios/shared/` (244 LOC — `fabric.py` KH/mock switch, `document_upload.py`, `packet_picker.py`, used by 4 scenarios) but `src/jaci/capabilities/commercial_lending/` — **6,984 LOC across 32 modules** (`spreader`, `template`, `validation` 805, `policies` 525, `docintel`, `document_packet`, `metric_result`, `promotion`, `hitl_approval`, `excel`, `workbook_layout`), plus the split `document_intake` / `financial_spreading` / `credit_validation` capabilities. Copy the `LoanCondition` / `ConditionType` / `UnderwritingRecommendation` schemas from `cre_underwriting/schemas/case_context.py`, and follow the `cases.py` data-seam discipline ("adding a property case = a new record here, no new code") so Acra's fixtures never leak into code.

**Do give Acra a real pack** with `depends_on` fragments — the pattern at `config/packs/cl_of_core/pack_manifest.yaml:34-38`, resolved by `japes/jazzx_sdk/pack/pack.py:127-157`. It is the only working reuse-by-reference seam in the repo, and it is how the eligibility grid stays overlay-shaped instead of becoming scenario code. Note `cl_of_core` and `cl_sp_core` are `0.1.0-draft` scaffolds with **no consuming scenario**, experts pointing back at `ci_spread`'s `CIPolicyExpert`, `governance_chain: DEFERRED`, and non-existent gold-case dirs — don't mistake them for a template to imitate.

**Middle path if speed to an Acra-visible demo dominates:** run Phase 0 as a spike inside `cre_underwriting` and carve at the Phase 0 → Phase 1 boundary, with the carve as a written exit criterion rather than a later discovery.

## 6. Governance: six ABAs, one overlay, one relay family

Narrowing order is `Pack semantics + Schema → ABA → Overlay → JAP → Runbooks`; no lower layer may widen a higher one.

- **The eligibility grid, overlay families, and PPP state rules belong in the Certified Client Overlay, not the ABA.** §11.1 permits an overlay to narrow thresholds, routing, role mappings, jurisdiction selection, template selection, and evidence-source activation. Putting Acra's numbers in the ABA hardcodes one client into the pack — the failure mode the CL decision was written to prevent. `SkillRegistry`'s tier guard (`allow_override=True` required) is what makes §11.2 mechanical rather than aspirational.
- **`human_only_decision_classes`: the credit decision itself, and any adverse action** — Acra's NOIA / 10-day letter and the third-notice cancellation. Assemble evidence, prepare artifacts, recommend; never draft, release, or execute.
- **Two authority cells need care.** Byte condition write-back is a `write-back` action class requiring `reversible` + `mandatory_trace_event` — a cleared condition pushed to the LOS is operationally material. External communication is prohibited unless expressly exposed, so the broker-outreach emails and 48-hour escalation must be an exposed cell per binding or they are disallowed by default.
- **Non-bypass invariants give the condition engine its contract**: no Decision without `policy_refs`, `evidence_refs`, `trace_id`, `produced_by`. Every auto-generated condition must cite the matrix directive it failed (Policy) plus the missing or conflicting document (Evidence). This is also the honest answer to Acra's over-conditioning concern (slide 10): **a condition that cannot cite a directive should not be issuable.**
- **Relay family across the five handoffs.** `required_payload` is a contract, not a suggestion; an incomplete payload triggers the documented bounce-back rather than silent reconstruction — the mechanism behind the CRE "eliminates send-backs" claim. Peer bindings are jointly binding, so changing one handoff payload can force recertification of neighbors. Budget that coupling.
- **Autonomy proposals** seeded from CRE §8 automation percentages — Processor 80% (doc classification), Underwriter 60% (recommend-only on eligibility), Compliance/Legal 85% — as `annex_ceiling` proposals subject to §10.6 promotion gates, never as go-live postures.
- **Recertification will fire** on each new licensed state and on the Byte write connector's higher-risk data access.

## 7. What to change in the Acra deck before it goes back out

1. **Re-aim Phase 0.** As scoped it spends four weeks validating splitting and classification — the part closest to shipped (970 LOC, disciplined, tested). Compress that to a week-1 spike on real *scanned* Acra packages, and spend the remaining three weeks proving **guideline-assessment fidelity against the rate matrix**: the 78 cells plus the DSCR gates, with every condition citing the directive it failed. That is what Acra's underwriters will judge, and where the residual uncertainty sits.
2. **Stop presenting Phases 2/3 as five-week increments** until the Byte contract questions on slide 26 are answered — specifically webhooks vs. polling, and whether two-way condition sync exists at Acra's plan tier. Convert Phase 2 to spike-then-commit.
3. **Move LTV forward.** Phase 3 lists LTV/CLTV calculation, but LTV is the primary axis of the Phase 0/2 eligibility assessment and no calculator exists. Either it moves to Phase 0/1 or Phase 2's condition generation runs on a proxy.
4. **Add the entity → PPP coupling** to the process view.
5. **Add a DocIntel cost-per-package line.** Prohibitive per-package cost is a stated go/no-go for the free-bookmark path.
6. **Set accuracy as a tracked curve with a weekly baseline, not a go-live SLA** — consistent with the recorded YETI decision, and safer to commit to.
7. **Say the reuse story explicitly.** Acra is delivered pack-thin: client overlay + six ABAs + tier-3 skills over primitives hardened on YETI. "Same pack underneath, client overlays on top" is both the honest sequencing and the stronger commercial story than a bespoke build.

## 8. Open questions and decisions needed

| # | Question | Owner | Blocks |
|---|---|---|---|
| D1 | ~~Separate scenario or fold in?~~ **Resolved: carve `acra_dscr`.** Remaining: does it get a real `acra_dscr_core` pack with `depends_on`, or start pack-less like `cre_underwriting`? | Eng lead | Whether the grid is overlay-shaped or scenario code |
| D2 | Fund `MatrixCondition` + table-valued profiles + set-membership operator as platform work? | Architecture | How the 78 cells are authored and reviewed |
| D3 | Fix suspend-inside-`Loop`, or flatten Acra's approvals to top-level steps? | SDK owner | Conditions loop, per-property exceptions |
| D4 | Does Byte expose condition webhooks and two-way sync at Acra's plan tier? | Acra + Byte | Phase 2 feasibility |
| D5 | Which of the 10 vendors are API-capable vs. portal-only? | Acra | Phase 3 scope; which steps stay human-led |
| D6 | Who funds `OutputTemplate` / `TemplateFillAgent` (still zero hits in tree) — Acra Phase 3 or platform? | Product | Worksheet delivery |
| D7 | `InteractiveAgentSpec` vs. `AssistantManifest` — canonical, or generation relationship? Unmoved since 2026-08-03 | Architecture | Authoring six Acra bindings |
| D8 | Sequencing against YETI: strictly downstream, or parallel with a shared hardening backlog? | Leadership | Staffing; the "Acra cannot be the SDK-proving vehicle" constraint |

*Method note: the two agents that verified this found the tree unusually easy to scope against, because its docstrings are honestly self-deprecating — `llm/routing.py:1-24` says of its own exports "never adopted by any real caller (confirmed by grep, not assumed)," and `Skill.inputs`/`outputs` say "nothing reads it yet." Where the seams are fake, the code says so. Re-verify before estimating: the SDK moved 2.3.6 → 2.4.1 while these reviews were being written.*
