# Status: PRD Completion (master/sequencing plan)

Author: Virendra Mehta · Updated 2026-08-01
Repo: jaci · Plan: docs/plans/plan_JACI_CL_PRD_COMPLETION.md

This plan sequences work that mostly landed via its own named child plans, each already tracked
by its own `done_`/`status_` file. This reconciles the master list against those, plus verifies
the items with no child plan of their own (2c, 2d, 3c, 4c) directly against real code rather than
trusting either the register or a general impression.

## Wave 1 — done via child plans

1a-1e (source precedence, addback library, disclosure check, reclassification, RB fixture) — each
has its own `done_` file already (`done_JACI_CL_ADDBACK_LIBRARY.md`,
`done_JACI_CL_RECLASSIFICATION_ENGINE.md`, `done_JACI_CL_RB_REFERENCE_CASE.md`,
`done_JACI_CL_VALIDATION_COMPLETION.md` covers the disclosure check). Not re-verified here.

## Wave 2 — governance completeness

- **2a (six severities)** — done. `validation.py`'s `Severity` enum has the six PRD severities
  plus `BLOCKING`/`ADVISORY` kept for one release as a documented legacy alias pair (its own
  docstring says so). `aggregate_status`/`promotion_refusal` gate through the state machine, not a
  UI `if`.
- **2b (provenance/assumption types, 8 values)** — partial, already self-documented. Checked
  `jazzx_sdk.fabric.canonical.evidence.ProvenanceType` directly: 8 members exist
  (`SOURCED`/`COMPUTED`/`REVIEWER_ENTERED`/`ASSUMPTION`/`EXPERT_ATTESTED`/`ADJUSTMENT_CANDIDATE`/
  `APPROVED_ADJUSTMENT`/`POLICY_ADJUSTED`), but the enum's own comment states this is **not** the
  PRD's exact eight — `UNSUPPORTED` is deliberately deferred "once a consumer needs it." A
  conscious, already-reasoned gap, not an oversight.
- **2c (audit debt: FR-VAL-1 through FR-VAL-6)** — not re-verified in this pass; the register
  itself is the source of truth for which of those six are still `audit` status. Flagging that
  this item was never independently checked here, rather than assuming it's fine.
- **2d (7-layer presentation, FR-MAP-7)** — **built, but a narrower, different shape than the PRD
  asks for.** Checked `EffectiveUnderwritingSpreadView`/`build_effective_view` directly
  (`promotion.py`): it's a base promotion plus its append-only override lineage (two states:
  original vs. superseded), not the seven named selectable views (Reported / Normalized /
  Bank-adjusted / Candidates / Underwritten / Covenant / Pro forma). The override-lineage feature
  is real and tested; FR-MAP-7's actual multi-layer selector is not built.

## Wave 3 — deliverable and review

- **3a (governed workbook)** — done, own `done_` file in japes
  (`done_JAPES_2_3_0_GOVERNED_WORKBOOK.md`).
- **3b (review surface)** — done, own `done_` file (`done_JACI_CL_REVIEW_SURFACE.md`).
- **3c (debt schedule and scenarios, FR-CNI-2/3)** — **not started.** Checked directly: the only
  "debt_schedule" hits in the codebase are `ci_spread/tools/registry.py`'s `get_debt_schedule`
  mock evidence-fetch tool (a document-intake stub returning a canned JSON blob) and its mention
  in `conductor.py`'s required-secondary-evidence set — neither is the actual feature (existing/
  proposed debt parsing, debt service computation, DSCR/FCCR/leverage recomputation under a new
  capital structure). The borrowing-base eligibility/reserve gap this item also names is likewise
  untouched.

## Wave 4 — structure and productization

- **4a (multi-entity/global cash flow)** — deferred by the plan's own text ("ontology-dependent");
  not re-verified, no reason to expect it's landed since nothing else in this session touched
  entity structures.
- **4b (template ingestion)** — deferred by the plan's own text ("lands last on purpose"); not
  re-verified.
- **4c (remaining ingestion/extraction)** — **partially closed, by a different plan.** "Special-
  instructions file as per-package overrides" is now real —
  `load_deal_special_instructions()`/the deal-scope tier, built this session by
  `plan_JACI_CL_POLICY_EXPERT.md` (Phase 1), not by this plan. Footnote binding, the Appendix-E
  document taxonomy, and UCA cash flow remain untouched.

## Net result

The master plan's own sequencing is still sound as a checklist, but most of its substance shipped
through child plans this reconciliation just points at rather than re-describing. The real,
concrete gaps still open, independent of any other plan: **2c** (needs the register re-checked,
not re-derived here), **2d**'s actual 7-layer selector (an override-lineage feature exists instead),
**3c** in full, and **4c**'s footnote binding / document taxonomy / UCA cash flow.
