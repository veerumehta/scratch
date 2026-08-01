# Plan: PRD Completion, Sequenced to the MVP Exit Criterion

Author: Virendra Mehta · 2026-07-29
Repo: jaci and japes · Baselines: jaci 0.9.8, japes 2.2.0
Depends on: nothing unlanded. Reads against `PRD_COVERAGE_REGISTER.md` (2026-07-29) and `CL_SOURCE_RECONCILIATION.md`.

Driver: P0 coverage of the Financial Spreading PRD is 42% weighted, and no plan covers any remaining P0 gap. This plan sequences the gap list to the PRD's own MVP exit criterion rather than to area order, so that progress is measurable against the gate the PRD actually sets.

**Target, stated explicitly because all current work diverges from it.** The PRD's MVP exit criterion is reproducing the Regional Bank C&I working spread at LTM Sep-2023, including the custom EBITDA/EBITDAR/FCC tab, within rounding, fully traceable, with the bad-debt add-back inconsistency and the unrecorded-tax and relief items flagged. Every worked case we have is YETI. This plan adopts RB as the target. If that is wrong, stop and re-sequence, because it drives the whole wave order.

**Scope note on template ingestion.** FR-ING-2 and FR-CUS-3 call template ingestion the MVP anchor. Reproducing RB's spread needs RB's template, but it does not need the template *parsed*. Wave 1 authors RB's template as pack YAML, which is legitimate for the exit criterion. Ingestion is productization and sits in Wave 4. Do not conflate them; authoring is days and parsing formulas out of a customer workbook is not.

## Wave 1 - The exit criterion

Every item here is named in the exit criterion. Nothing else is.

**1a. Assurance and source precedence (japes).** The gap I scoped out of the period model plan and never returned to. `Assurance` and `ASSURANCE_RANK` exist; the resolver does not. Add per-statement and per-period assurance attribution, a `SourcePrecedencePolicy` on the profile, and a resolver that records which source won and why. The ranking is config; the resolver is machinery. FR-SRC-1, FR-SRC-2, FR-SRC-3.

The RB profile is the acceptance case: 2018 and 2019 reviewed, 2020 and 2021 audited, the 9-month 2022 comparative a compilation, the 9-month 2023 stub company-prepared. `construct_ltm` already returns mixed assurance as a set; this wave makes the component selection policy-driven rather than caller-supplied.

**1b. Add-back library and consistency (jaci pack, plus one small japes piece).** Seven P0 requirements, the worst-covered area in the register, and mostly authoring because the DSL already supports conditionals and caps.

- `addbacks.yaml`: non-cash, non-recurring, owner-discretionary, with caps and conditions expressed in the DSL. FR-ADJ-2, FR-ADJ-6.
- House definitions authored as metric definitions, including RB's CIT EBITDA as Gross Profit less SG&A less Rent, plus EBITDAR and the fixed-charge variants. FR-ADJ-5, FR-CUS-8.
- Relief and one-time income tagging, including the RB relief refund. FR-ADJ-7.
- Candidate versus lender-approved as distinct layers with a promotion gate, so a candidate cannot reach an official or covenant metric without approval. This is the japes piece. FR-ADJ-3.
- Cross-period consistency check: an add-back applied in one period is flagged unless treated consistently across all periods. FR-ADJ-4 and FR-VAL-7 are the same check surfaced twice; implement once.

The bad-debt inconsistency in the exit criterion is exactly this last item. It is the most persuasive beat in the demo and a real judgment error in a real customer spread, so treat its fixture as permanent.

**1c. Disclosure check (jaci).** Flag a disclosed obligation absent from the balance sheet, the RB figure being roughly $573K, so it is not omitted from leverage. FR-VAL-8.

**1d. Reclassifications and break-outs (jaci pack, plus an applier).** Appendix A as declarative rules over the classifications `chart_of_accounts.yaml` already declares, plus the engine that applies them into the as-spread layer without touching as-reported. Break-outs for officer comp out of SG&A, D&A across COGS and opex, embedded interest. FR-MAP-3, FR-MAP-4. Unblocks FR-SPR-1, FR-SPR-2 and FR-RAT-2, which all depend on reclassified inputs.

**1e. RB template and fixture (jaci pack).** RB's spread layout authored as a `spread_template.yaml` sibling, and the RB package registered as a gold case with the three exit-criterion findings as assertions.

Wave 1 acceptance: the RB LTM Sep-2023 spread reproduces within rounding, every cell traces to a source coordinate, and the bad-debt inconsistency, the unrecorded obligation and the relief refund are all flagged with severities.

## Wave 2 - Governance completeness

**2a. Finding severity and delivery gate (japes).** Six severities replacing the current blocking-and-advisory pair, plus an aggregate spread status that gates promotion through the state machine rather than an `if` in UI code. FR-VAL-10.

**2b. Provenance and assumption types (japes).** Extend `ProvenanceType` to the PRD's eight values. Make assumption a value type that can never render as a reported figure, enforced by the type system rather than the UI. The `ASSUMPTION` binding kind already exists in the DSL; this closes the other half. FR-AUD-2, FR-CUS-6.

**2c. Audit debt.** Read `validation.py` and resolve FR-VAL-1 through FR-VAL-6 from `audit` to a real status. Implement whatever is missing. Do this before anyone quotes the register externally.

**2d. Layered presentations (jaci).** Reported, Normalized, Bank-adjusted, Candidates, Underwritten, Covenant, Pro forma as selectable views over one spread. FR-MAP-7.

## Wave 3 - Deliverable and review

**3a. Governed workbook export (japes reporter plus pack layout).** The named worksheets, cell notes carrying confidence and provenance and source, traffic-light tiers, an exceptions sheet with links, and the Moody's-style reported/adjustment/adjusted presentation. Engine in japes, tab layout in the pack. FR-OUT-1, FR-OUT-2, FR-OUT-3.

**3b. Review surface (jaci app).** Risk-ranked queue, click-to-source using the coordinates that already exist, inline override with author, timestamp, superseded value and rationale, re-propagation. FR-HIL-1, FR-HIL-2, FR-HIL-3.

**3c. Debt schedule and scenarios (jaci).** Existing and proposed debt parsing, debt service, and recomputation of DSCR, FCCR and leverage under a new structure. FR-CNI-2, FR-CNI-3. Also closes the borrowing-base eligibility and reserve gap standing since the first review of this scenario.

## Wave 4 - Structure and productization

**4a. Multi-entity and global cash flow (jaci, ontology-dependent).** Parent, subsidiary, affiliate, VIE, guarantor structures with ownership percentages; related-party linkages surfaced across statements and notes; entity-level spreading rolled to a combining view with eliminations; guarantor PFS and personal income; global DSCR. FR-CON-1 through FR-CON-4, FR-GCF-1 through FR-GCF-3.

Prerequisite from the ontology stance: retire the hand-mirrored spread, metrics and decision layers in `ontology/ci_lending.yaml`, which duplicate canonical code schemas, and keep the domain entities. Subtract before adding.

**4b. Template ingestion (japes).** Parse a customer workbook's labels, structure and formulas, detect hardcodes and plugs, map referenced lines to the chart of accounts, and emit a `spread_template.yaml` plus metric definitions. FR-ING-2, FR-EXT-8, FR-CUS-3.

This is the PRD's declared anchor and it lands last on purpose. It is a generator for artifacts whose schemas Wave 1 will have exercised against a real institution. Building the generator before the target schema has been proven by hand is the wrong order.

**4c. Remaining ingestion and extraction.** Special-instructions file as per-package overrides, footnote binding to line items, document taxonomy from Appendix E, UCA cash flow. FR-ING-3, FR-EXT-4, FR-ING-4, FR-SPR-3.

## Out of scope

All CRE requirements (FR-CRE, 9 items, all P1 or P2, post-MVP by the PRD's own sequencing). All P2 items. RMA peer benchmarking (FR-MAP-8, FR-RAT-3). Natural-language metric assist (FR-CUS-11). Projections (FR-CNI-6). Corpus register import, which is `plan_JACI_CL_PACK_FOUNDATION.md` Phases 2 through 5 and needs the Phase 3 rescope flagged in its status doc first.

## Sequencing and expected movement

Wave 1 is the only wave with a hard external gate, so it goes first and alone. On the register's weighting it moves P0 coverage from 42% to roughly 70%, because it closes ADJ almost entirely, SRC, and the MAP reclassification gap, which together account for 16 P0 requirements.

Wave 2 is governance completeness and carries the audit debt; it is where the coverage number becomes trustworthy rather than merely higher. Wave 3 is what makes the output deliverable to a customer rather than demonstrable in a tab. Wave 4 is the largest and least urgent, and 4b should not start before Wave 1 has proven the schema it generates.

Each wave item wants its own plan doc before execution. This document is the sequence, not the instructions.
