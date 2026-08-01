# Plan: Regional Bank Reference Case and Exit Criterion

Author: Virendra Mehta · 2026-07-29
Repo: jaci · Baseline: 0.9.8 (dev)
Depends on: all of Wave 1. This plan is the acceptance harness for the wave, so it is written first and executed last.

Driver: Wave 1e of `plan_JACI_CL_PRD_COMPLETION.md`. The PRD's MVP exit criterion is reproducing the Regional Bank C&I working spread at LTM Sep-2023, and nothing in the repo targets it. Every worked case is YETI. This plan makes the exit criterion an executable test rather than a paragraph in a requirements document.

> **Status (2026-07-29): DONE, all 5 phases (jaci, unpushed, no version bump). The Phase 5 gate
> test passes** — Wave 1 (1a-1e) is complete, which per this plan's own framing is the point.
>
> The grounding note's own "$11.4MM of related-party receivables in 2020" is wrong — the real
> package (`docs/LoanSamples/Regional Bank/`, already in the repo, not something this phase
> fetched) has that figure in **2023** (`Balance Sheet-Input!N28` = $11,378,858); 2020's own figure
> is $3,053,249. Found by reading the actual reference workbook rather than trusting the plan's
> own prose. All other PRD facts named in the grounding notes verified exactly against the real
> documents: the assurance stack (opinion-letter titles checked directly — reviewed/audited/
> audited/compilation/company-prepared, confirmed for every period), the $2,331,124 relief refund
> and ~$573,000 unrecorded tax (both verbatim in "2022 and 2023.pdf" note 24), the CIT EBITDA
> formula, and the LTM sign-error note (`O4`'s stated formula and `J4`'s actual formula are
> genuinely different, confirmed algebraically, not just by inspection).
>
> - **Phase 1**: `PROVENANCE.yaml`, one entry per file, traces each figure to its source document
>   and assurance level. Per the user's own correction mid-phase, this is a source-to-figure
>   traceability record, not a real-vs-synthetic compliance attestation — the plan's literal
>   phrasing asked for the latter; the user redirected to the former, and the file reflects that.
> - **Phase 2**: `spread_template_rb.yaml` transcribes the reference spread's own "First Citizens
>   Format" tab row for row (36 rows). 21 bind to a chart-of-accounts key or metric id; 15 are
>   explicitly unbound with a stated reason, falling into three real gaps this phase's own
>   instruction anticipated ("that is a finding about the vocabulary or the metric catalog"): no
>   margin metric exists for several house definitions, several rows need the add-back/
>   normalization layer composed at render time rather than a static DSL formula (Adjustments/Adj.
>   EBITDA/Adj. EBITDAR/the FCC calculation), and the reference spread reports some balance-sheet
>   lines as combined aggregates with no single matching canonical key. A new `rb_template.py`
>   loader validates the binding set; deliberately not wired into `template.py`'s YETI-shaped
>   render pipeline, which doesn't compose the add-back layer today.
> - **Phase 3**: six real `SourceStatement`s (one per source document), resolved through
>   `resolve_sources`/`construct_ltm_from_sources` (Wave 1a), reproduce the reference workbook's
>   own LTM Sep-2023 column exactly, line for line, not approximately. The sign trap is asserted
>   algebraically (the note's formula and the cell's formula are shown to differ, then the SDK's
>   own output is shown to match the cell, not the note). The compilation's missing cash-flow
>   statement is asserted to refuse, not silently skip.
> - **Phase 4**: all three exit-criterion findings raised on real figures (bad debt present in
>   every year, applied in one; the $573K tax; the $2,331,124 relief refund tagged as a candidate,
>   not yet approved into a covenant metric). Of the two reference-workbook discrepancies: the
>   cash-tie break is exact and literal (a real $1-2 rounding gap between the cash-flow statement's
>   computed ending cash and the balance sheet's reported cash, present in three of five years).
>   The "balance-control discrepancy" is **not** a literal assets ≠ liabilities+equity break — the
>   workbook's own balance-control check row is zero every year — so this reports the more precise,
>   fully-provable thing actually found instead: a $195,585 equity-roll-forward gap in FY2023,
>   which traces exactly to a capital injection (`Cash Flows!N34`) that the balance sheet's own
>   back-solved "Distributions" line silently nets in rather than reporting separately. Reported
>   as what it is (FR-VAL-4) rather than overclaiming a FR-VAL-1 finding not independently verified
>   from the underlying documents.
> - **Phase 5**: one test, passing, covering LTM reproduction within a stated (zero) tolerance,
>   provenance/confidence on every cell, CIT EBITDA matching the reference exactly, and all three
>   findings plus both discrepancies raised. EBITDAR/CIT FCC reproduction against the reference
>   workbook is explicitly declared out of scope for this pass (same normalization-layer gap
>   Phase 2's unbound rows already name), not silently attempted and left wrong.
> - 12 new tests (`test_rb_reference_case.py`); full jaci suite 586 passed, 2 skipped, no
>   regressions.

## Grounding notes (verified 2026-07-29 against dev)

- `config/packs/ci-spread-core/pack_manifest.yaml` already carries an `rb_ci` policy overlay with `applies_to_program_ids: [RB-CI-001, RB-CI-002]`. The overlay exists; there is no RB borrower, package, template or fixture.
- `docs/LoanSamples/YETI/yeti_financials.json` is the only financials fixture in the repo. The other four C&I gold cases carry an `application` block of aggregates with no statements, so there is no per-line-item corpus for any borrower but YETI.
- `config/packs/ci-spread-core/spread_template.yaml` is the YETI-shaped template. Templates are pack assets, so a second one is a sibling file, not a schema change.
- `construct_ltm` is complete with guardrails, refusals and mixed-assurance sets, and has no UI.
- The PRD supplies these RB specifics, all of which become assertions: the assurance stack of 2018 and 2019 reviewed, 2020 and 2021 audited, the nine-month 2022 comparative a compilation and the nine-month 2023 stub company-prepared; CIT EBITDA as gross profit less SG&A less rent; the relief refund of $2,331,124; roughly $573K of disclosed but unrecorded tax; roughly $11.4MM of related-party receivables in 2020; a balance-control discrepancy and a cash-tie discrepancy carried in the reference spread itself; the nine-month 2022 compilation omitting the statement of cash flows; and a workbook note stating the LTM formula with the wrong sign while its computed cell is correct.

## Phase 1 - The package and its provenance

Register the RB package under `docs/LoanSamples/` with a provenance file recording, explicitly: whether each document is a real masked customer artifact or synthesized to the RB profile, who supplied it, and the date received.

State this per document, not per package. The PRD describes RB as a real customer verified against audited statements with identity masked, and some documents may arrive synthesized while others are real. A demo narrated as "the real customer package" when half of it was generated is the kind of claim that does not survive one question from the room.

Where a document is synthesized, the provenance file records which PRD-stated facts it was built to satisfy, so a later reader can tell an intended fixture property from an accident of generation.

Acceptance: every file in the package has a provenance entry. A test fails if a package document lacks one.

## Phase 2 - The RB template as a pack asset

Author RB's spread layout as `config/packs/ci-spread-core/spread_template_rb.yaml`, including the custom EBITDA, EBITDAR and fixed-charge-coverage tab the exit criterion names.

This is deliberately authoring, not ingestion. FR-ING-2 and FR-CUS-3 call template ingestion the MVP anchor, and Wave 4b builds it. Reproducing RB's spread requires RB's template; it does not require that template to have been parsed. Authoring it by hand also exercises the schema that the ingester will later have to emit, which is the right order.

Row bindings reference canonical chart-of-accounts keys and metric ids. If a row cannot be expressed that way, that is a finding about the vocabulary or the metric catalog, not a reason to add a special case here. Record it and fix it upstream.

Acceptance: the template loads, every row binds to a resolvable key or metric id, and the unbound set is empty or explicitly enumerated with a reason.

## Phase 3 - The assurance stack and the LTM column

Register the six source statements with their assurance levels, and construct LTM Sep-2023 through the precedence resolver rather than by passing components in.

Three assertions the PRD sets out directly:

- The anchor is the audited full year and the current interim is the company-prepared stub, chosen by policy rather than by the caller.
- The constructed period's assurance is the set of its components, not the best of them, and the column label says so.
- The nine-month 2022 compilation omits the statement of cash flows, so income-statement LTM computes while any cash-flow-derived or fixed-charge-derived LTM figure is marked as requiring an explicit approved derivation. It must not tie out silently. `construct_ltm` already implements this; this phase proves it against the real stack.

The sign-label trap is already covered by a japes regression test. Assert it here too at the pack level, because the trap is that a human note in *this* workbook states the formula wrongly, and the pack-level assertion is what proves we did not transcribe it.

Acceptance: the LTM column constructs from resolver-chosen components, reports three assurance levels, and emits the cash-flow-gap finding. No cash-flow-derived LTM figure is written without an approved derivation.

## Phase 4 - The three exit-criterion findings

Each becomes a gold case with the finding as its assertion.

- **Bad-debt inconsistency.** The add-back applied in one period with the line present and non-trivial in the others. Depends on the extension in `plan_JACI_CL_ADDBACK_LIBRARY.md` Phase 4, since the existing detector cannot see this case.
- **Unrecorded tax obligation.** Roughly $573K disclosed and absent from the balance sheet, with leverage recomputed including it and reported beside the reported figure. Depends on `plan_JACI_CL_VALIDATION_COMPLETION.md` Phase 3.
- **Relief refund.** The $2,331,124 tagged as one-time income per FR-ADJ-7, and excluded from the recurring earnings base.

Also assert the two discrepancies the PRD says the reference workbook itself carries: the balance-control break and the cash-tie break. These are findings we should raise *against the human spread*, and getting them right is a stronger demonstration than matching it. If our figures agree with the reference workbook on those two cells, one of us is wrong and it is worth knowing which.

Acceptance: three findings raised with severities, and the two reference-workbook discrepancies detected and reported rather than reproduced.

## Phase 5 - The exit criterion as one test

A single test asserting the whole gate: the RB LTM Sep-2023 spread reproduces within rounding, every populated cell carries a source coordinate and a confidence, the CIT EBITDA and EBITDAR and FCC tab computes, and the three findings are raised.

Within rounding needs a stated number rather than a gesture. Take the tolerance from the profile, and where our figure and the reference differ by more than it, the test reports the cell, both values and the derivation. A red test that says only "spread does not match" is not worth having.

Acceptance: the test exists and its failures are diagnostic. It is expected to fail until Wave 1 completes, which is the point; it is the wave's definition of done.

## Out of scope

Template ingestion (Wave 4b). Multi-entity and related-party structure, so the $11.4MM related-party receivable is spread and reclassified per Appendix A but its affiliate relationship is not modeled; that is FR-CON and Wave 4a. Guarantor and global cash flow. The governed workbook export. Any CRE requirement.

## Sequencing

Phase 1 first and it can start immediately, since the provenance discipline should be in place before documents arrive rather than reconstructed after. Phase 2 is authoring and depends only on the landed vocabulary. Phases 3 and 4 depend on the rest of Wave 1 and are the acceptance harness for it. Phase 5 is written early and expected red; treat it as the wave's tracking signal rather than a task.
