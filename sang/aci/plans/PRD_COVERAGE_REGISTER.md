# Financial Spreading PRD v0.4 - Coverage Register

Author: Virendra Mehta · 2026-07-29
Status: reference register, not a plan. Companion to `CL_SOURCE_RECONCILIATION.md`.

Source: `Financial_Spreading_PRD_v0_4_2.docx`, section 7. Counts extracted programmatically: **122 requirements, 85 P0, 31 P1, 6 P2**.

Weighted coverage (`done` = 1.0, `partial` = 0.5, `none` = 0): **P0 61%** (was 42% before Wave 1 —
see the 2026-07-29 re-audit below). All-priorities figure not recomputed in this pass; treat 35%
as stale until it is.

Status vocabulary. `done` implemented with tests. `partial` meaningfully present but incomplete. `none` not started.

**Audit debt resolved 2026-07-29** by reading `validation.py`. The previous revision scored FR-VAL-1 through 6 provisionally at 0.5. The audit was wrong in both directions and the headline number is unchanged only by coincidence:

- FR-VAL-6 cross-document consistency is `done` (`detect_cross_document_contradictions`).
- FR-VAL-2 cross-foot is `partial`, balance-sheet only, additive subtotals only; its own docstring defers income-statement sequential subtotals.
- FR-VAL-1 balance control, FR-VAL-3 cash-flow tie, FR-VAL-4 equity roll-forward and FR-VAL-5 period continuity are **absent entirely**. VAL P0 coverage is 28%, not the 39% recorded before.
- Offsetting upgrades found in the same read: `detect_cross_period_addbacks` exists, so FR-ADJ-4 and FR-VAL-7 are `partial` not `none`. `detect_staleness` and `detect_precedence_violations` exist, so FR-SRC-2 and FR-SRC-4 are `partial` not `none`. SRC rose to 38%, ADJ to 14%.

**Wave 1 re-audit, 2026-07-29 (second pass, same day)**, done properly this time: read the actual
PRD requirement text (`docs/plans/Financial Spreading PRD v0.4 2.pdf`, section 7) per requirement
ID, not the register's own summary prose, against the code that shipped in Wave 1
(`done_JAPES_2_3_0_SOURCE_PRECEDENCE.md`, `done_JACI_CL_ADDBACK_LIBRARY.md`,
`done_JACI_CL_VALIDATION_COMPLETION.md`, `done_JACI_CL_RECLASSIFICATION_ENGINE.md`,
`done_JACI_CL_RB_REFERENCE_CASE.md` — all in `docs/status/`). Same method the original
"audit debt resolved" pass above used, applied to the wave that just landed.

**One false premise found and corrected, not just a status update.** FR-VAL-1's own PRD text
reads: *"Balance control: Total assets = total liabilities + equity, per period, within tolerance
(the RB spread carries a balance-control = 0 row)."* The PRD itself says RB's balance control
**ties exactly** — there never was a "balance-control discrepancy" in the reference workbook to
find. `plan_JACI_CL_RB_REFERENCE_CASE.md`'s own grounding notes asked for one anyway (likely
conflating it with FR-VAL-3's cash-tie rounding gap, which the PRD *does* name for RB: *"the RB
statements show $1–$2 ending-cash rounding in some years"* — exactly what
`done_JACI_CL_RB_REFERENCE_CASE.md` tested and found). The equity-roll-forward finding
`done_JACI_CL_RB_REFERENCE_CASE.md` reported instead of a balance-control break was the right
call independent of this — it's just worth recording that the plan's original ask was never
achievable as stated, not merely narrowly missed.

**Real-data-verified vs. capability-only, stated per item, not just per area.** Following directly
from a desktop-app review catching this exact conflation in Wave 1e's own done doc: a `done`
status below means the code exists and has passing tests — synthetic fixtures, in most areas.
Items marked **(RB)** below were additionally exercised against real Regional Bank figures in
`test_rb_reference_case.py`; that is a strictly stronger claim, and the two should not be
conflated when quoting this register.

- **SRC (was 38%, now 100%, 4/4 P0)**: FR-SRC-1 assurance labeling — done (RB). FR-SRC-2
  precedence-as-config, applied and recorded — done (the requirement's own text is about the
  resolution engine, not about FR-ING-3's separate, unbuilt instructions-file ingestion; noting
  the boundary rather than silently assuming FR-ING-3 is also covered). FR-SRC-3 policy-driven LTM
  construction — done (RB, reproduces the PRD's own worked example: *"Revenue 57,581 + (61,443 −
  44,326) = 74,698"*, exactly). FR-SRC-5 the RB worked profile itself — done (RB; every assurance
  level in the PRD's own FR-SRC-5 text — 2018/19 reviewed, 2020/21 audited, 9-mo 2022 compilation,
  9-mo 2023 company-prepared, 2022/2023 audited — confirmed against the actual opinion letters).
  FR-SRC-4 (P1, not P0, so it doesn't move this number) has its finding-emission mechanism
  (`SourcePrecedenceFinding`) shipped and japes-unit-tested, but not specifically asserted against
  RB in the jaci-side test — flagged rather than assumed.
- **ADJ (was 14%, now 100%, 7/7 P0)**: FR-ADJ-2/3/5/6/7 done directly per
  `done_JACI_CL_ADDBACK_LIBRARY.md`'s own "Covers" line; FR-ADJ-7 and the bad-debt half of ADJ-4
  are (RB) via the real $2,331,124 relief refund and the real (corrected — see that file) bad-debt
  figures. FR-ADJ-4 done (extended in Wave 1c). FR-ADJ-1 (EBITDA build, itemized/sourced,
  reported→adjustments→adjusted) is done as a direct consequence of ADJ-2/3/5's shipped
  machinery (`apply_normalization`'s own derivation shape) — no plan explicitly named FR-ADJ-1,
  this is my own read of the shipped code against the requirement text, flagged as such rather
  than presented as a plan's own claim.
- **VAL (was 28%, now 83%, 7 done + 1 partial / 9 P0)**: FR-VAL-1 (RB — see the false-premise note
  below; balance control ties on all six real periods), FR-VAL-3 (RB, the PRD's own named RB
  cash-tie fact), FR-VAL-4 (RB — see the same-day correction below: ties against the complete
  audited data, correctly flags a gap against the analyst's own incomplete spreadsheet tab), 5, 7
  (RB, the PRD's own named RB bad-debt case), 8 (RB, the PRD's own named RB $573K), 10 all done;
  FR-VAL-6 already done pre-Wave-1, unchanged. **FR-VAL-2 stays partial, not done** —
  `detect_income_statement_cross_foot` (Wave 1c) closes the income-statement half its own
  docstring named as a gap, but cross-footing still doesn't cover cash-flow-statement subtotals
  (operating/investing/financing activities) at all; "every subtotal" in the requirement
  text isn't fully met yet.
- **MAP (was 58%, now 92%, 5 done + 1 partial / 6 P0)**: FR-MAP-3, FR-MAP-4 done per
  `done_JACI_CL_RECLASSIFICATION_ENGINE.md`'s own "Covers" line (synthetic-fixture-tested; RB has
  no balance sheet as canonical keys, so not (RB) for this borrower specifically). **FR-MAP-6
  stays partial** — reclassifications now carry rationale/source (inspectable/logged, matching the
  requirement's first half) and `ReclassificationRule.overridable` is declared, but nothing
  consumes that flag yet, and "learn and persist borrower/industry-specific mappings" is explicitly
  out of scope per the plan's own text — the second sentence of FR-MAP-6 remains unbuilt.
- **RAT (was 50%, now 75%, 1 done + 1 partial / 2 P0)**: FR-RAT-2's core ask — `tangible_net_worth`
  as its own computed metric — is done and verified against real YETI figures (not RB). **Staying
  partial, not done**: the requirement's own text is "so liquidity and leverage reflect the
  conservative bank view" — a purpose clause, not just "compute the number" — and the existing
  `debt_to_equity` metric still divides by raw `total_stockholders_equity`, not
  `tangible_net_worth`. The number exists; nothing consumes it yet.
- **SPR not re-scored this pass** (unchanged at 50%, out of the four areas asked for): FR-MAP-3/4
  landing removes the blocking *dependency* for FR-SPR-1/2 (per
  `plan_JACI_CL_RECLASSIFICATION_ENGINE.md`'s own "Unblocks" line and
  `standardized_template_rows`), but doesn't itself add common-size columns or YoY growth, which
  the requirement text also asks for. Unblocked ≠ complete; left stale deliberately rather than
  guessed.

Net: **P0 weighted sum rose from 35.7 to 51.7 (of 85), 42% → 61%.** Shown as a delta, not just a
new headline, so the arithmetic can be checked: SRC +2.5, ADJ +6.0, VAL +5.0, MAP +2.0, RAT +0.5.

## By area, P0 only

Table below reflects the pre-Wave-1 audit; SRC/ADJ/VAL/MAP/RAT rows are stale against it (see the
2026-07-29 re-audit above for their current done/partial/none split and P0%). Not rewriting the
table in place — the delta write-up above is the source of truth for those five rows until a full
table regeneration; this avoids quietly losing the pre-Wave-1 baseline the delta is computed
against.

| Area | n | P0 | done | partial | audit | none | P0 cov (pre-Wave-1) |
|---|---|---|---|---|---|---|---|
| PER periods, LTM | 10 | 8 | 7 | 2 | 0 | 1 | 94% |
| CUS custom metrics | 11 | 8 | 4 | 4 | 0 | 3 | 62% |
| MAP mapping | 8 | 6 | 3 | 2 | 0 | 3 | 58% → **92%** |
| SPR spreading | 4 | 4 | 1 | 2 | 0 | 1 | 50% (unblocked, not re-scored) |
| RAT ratios | 3 | 2 | 1 | 0 | 0 | 2 | 50% → **75%** |
| SOP policy config | 6 | 3 | 0 | 5 | 0 | 1 | 50% |
| AUD traceability | 4 | 4 | 0 | 4 | 0 | 0 | 50% |
| EXT extraction | 11 | 8 | 1 | 6 | 0 | 4 | 44% |
| VAL validation | 10 | 9 | 1 | 3 | 0 | 6 | 28% → **83%** |
| ING ingestion | 7 | 6 | 1 | 4 | 0 | 2 | 33% |
| CNI C&I specifics | 6 | 3 | 1 | 2 | 0 | 3 | 33% |
| SRC assurance, precedence | 5 | 4 | 0 | 4 | 0 | 1 | 38% → **100%** |
| HIL human review | 5 | 4 | 0 | 2 | 0 | 3 | 25% → **100%** |
| OUT export | 6 | 3 | 0 | 2 | 0 | 4 | 17% → **100%** |
| ADJ adjustments | 8 | 7 | 0 | 2 | 0 | 6 | 14% → **100%** |
| CON multi-entity | 5 | 3 | 0 | 0 | 0 | 5 | 0% |
| GCF global cash flow | 4 | 3 | 0 | 0 | 0 | 4 | 0% |
| CRE (post-MVP) | 9 | 0 | 0 | 2 | 0 | 7 | 0% |

## What the distribution says

**Stale as of the Wave 1 re-audit above** — written when ADJ/SRC/MAP/VAL were the worst areas;
that is no longer true (ADJ and SRC are now the *best*, ADJ having gone from the register's own
named "highest-leverage" gap to fully closed). Kept for history rather than deleted. The current
worst-P0 areas are **CON (0%) and GCF (0%)**, unchanged by Wave 1 and explicitly out of scope for
it (both need entity relationships, i.e. the ontology becomes load-bearing). OUT went 17% → 100%
in Wave 3a (`plan_JAPES_2_3_0_GOVERNED_WORKBOOK.md`) and HIL went 25% → 100% in Wave 3b
(`plan_JACI_CL_REVIEW_SURFACE.md`), both per the "New code" list below. Original
(now-superseded) paragraph below:

The average hides the shape. Three areas carry 13 untouched P0 requirements between them: ADJ at 7%, CON at 0%, GCF at 0%. ADJ is the outlier worth noting, because the machinery it needs already exists. The expression DSL supports conditionals and caps, so FR-ADJ-4 and FR-ADJ-6 are expressible today. Nothing has been authored. That makes ADJ the highest-leverage area in the register: seven P0 requirements, mostly authoring against landed primitives.

CON and GCF are different. They need entity relationships, which means the ontology becomes load-bearing. Global cash flow combines borrower, guarantors and affiliates with elimination of intercompany items, which no output template can express.

PER at 94% is the one area that is effectively finished. Its residual is FR-PER-7 (period column labelling, a UI concern) and FR-PER-9 (irregular calendars, explicitly deferred).

## Done (19)

FR-ING-7, FR-EXT-5, FR-MAP-1, FR-MAP-2, FR-MAP-5, FR-SPR-4, FR-PER-1 through FR-PER-6, FR-PER-8, FR-RAT-1, FR-CUS-1, FR-CUS-2, FR-CUS-7, FR-CUS-10, FR-CNI-1.

## P0 gaps with no plan covering them

Grouped by whether the work is authoring against landed machinery or new code. **Resolved by
Wave 1 (2026-07-29), struck through; left in place for history rather than deleted:**

**Authoring.** ~~FR-ADJ-2 add-back library.~~ ~~FR-ADJ-5 house EBITDA definitions including RB's CIT EBITDA.~~ ~~FR-ADJ-6 caps and conditions.~~ ~~FR-ADJ-7 relief and one-time income tagging.~~ ~~FR-MAP-3 reclassification rules from Appendix A.~~ ~~FR-MAP-4 break-out rules.~~ FR-RAT-2 tangible net worth — the number itself is done, but not yet wired into `debt_to_equity`, so this stays open (partial, see the Wave 1 re-audit above). FR-CUS-8 remaining starter-library metrics (EBITDAR, lease-adjusted leverage, debt yield, borrowing-base availability) — EBITDAR done, the rest still open. FR-ING-4 document taxonomy from Appendix E — still open. ~~FR-SRC-2 precedence ranking as config.~~

**New code.** ~~FR-SRC-1/2/3 assurance detection and the precedence resolver~~, explicitly scoped out of the period model plan and never picked up until Wave 1a. ~~FR-ADJ-3 candidate-versus-approved layer with a promotion gate.~~ ~~FR-ADJ-4 cross-period consistency check.~~ ~~FR-VAL-7 adjustment consistency.~~ ~~FR-VAL-8 disclosure check for unrecorded obligations.~~ ~~FR-VAL-10 six severities and a delivery gate.~~ FR-EXT-4 footnote binding — still open (FR-VAL-8's `DisclosedObligation` is the typed interface it will fill, per `done_JACI_CL_VALIDATION_COMPLETION.md`). FR-EXT-8 Excel formula and hardcode extraction. FR-ING-2 and FR-CUS-3 template ingestion. FR-AUD-2 provenance enum extension and the assumption value type — provenance enum extension done (FR-ADJ-3's candidate/approved values), assumption value type still open. FR-CNI-2/3 debt schedule and proposed-debt scenarios. FR-SPR-3 UCA cash flow. ~~FR-HIL-1/2/3/4 risk-ranked review queue, corrections + re-propagation, click-to-source, maker-checker~~ (Wave 3b, `plan_JACI_CL_REVIEW_SURFACE.md`) — `Correction`/`apply_corrections` (a governed override layer, re-validated rather than rectified by fiat), `rank_for_review` (severity + confidence + magnitude + the covenant-feeding binding closure), `resolve_source_region`/`reverse_lookup`, and three-actor maker-checker roles (self-review policy read from the profile) are all done and tested against real jaci objects, including a real covenant-test-flip on correction and a content-identical exception summary vs. the governed workbook's own Exceptions sheet. The actual Streamlit side-by-side source view (`ui/shared.py`) is not wired — same deliberate UI-wiring deferral as FR-OUT-1/2/3 below, for the same reason (the UI's current data model is the provenance-free `FinancialSpread`, not `SpreadPackage`). ~~FR-OUT-1/2/3 governed workbook~~ (Wave 3a, `plan_JAPES_2_3_0_GOVERNED_WORKBOOK.md`) — the reporter, pack layout, and all three requirements' mechanics are done and tested against real jaci objects; the existing Streamlit download buttons (`ui/shared.py`) still call the old `FinancialSpread`-only exporter, deliberately not migrated in this pass (a separate UI-wiring task, not part of the plan's own stated acceptance). FR-CON and FR-GCF, both ontology-dependent — untouched, explicitly out of scope for Wave 1.

## Plan coverage

Landed: `plan_JAPES_2_2_0_PERIOD_MODEL.md`, `plan_JAPES_2_2_0_EXPRESSION_DSL.md`, `plan_JAPES_2_2_0_LINE_VOCABULARY.md`, `plan_JACI_CL_SPREAD_TEMPLATE_ASSET.md`, `plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md`, `plan_JAPES_2_3_0_GOVERNED_WORKBOOK.md` (Wave 3a), `plan_JACI_CL_REVIEW_SURFACE.md` (Wave 3b).

Open: `plan_JACI_CL_PRD_DEMO_ARC.md` covers demo surfaces, not PRD requirements. `plan_conductor_collapse.md` is orthogonal.

**No plan covers any item in the gap list above.** `plan_JACI_CL_PRD_COMPLETION.md` sequences them.

## Plans covering the gap list

Written 2026-07-29, all five landed (`plan_JAPES_2_3_0_SOURCE_PRECEDENCE.md` 1a,
`plan_JACI_CL_ADDBACK_LIBRARY.md` 1b, `plan_JACI_CL_VALIDATION_COMPLETION.md` 1c,
`plan_JACI_CL_RECLASSIFICATION_ENGINE.md` 1d, `plan_JACI_CL_RB_REFERENCE_CASE.md` 1e — all jaci
unpushed except 1a in japes, unpushed; no version bump on either repo). **Re-audited the same
day** (the "Wave 1 re-audit, 2026-07-29 (second pass, same day)" section near the top of this
file has the full per-requirement detail and the delta math); SRC/ADJ/VAL/MAP/RAT are no longer
stale.

`plan_JACI_CL_RB_REFERENCE_CASE.md` (1e)'s gate test passes, closing Wave 1 (1a-1e) as planned
work. **Update, same day, second pass**: the earnings-vs-leverage/coverage gap identified when
this was first landed (only 11 income-statement canonical keys existed for RB, so fixed-charge
coverage/leverage/current ratio/FR-VAL-1 balance control were implemented-and-tested-on-synthetic-
data-only) **is now closed** — real balance-sheet figures for all six periods (extracted directly
from the raw PDFs for the two interim periods, which needed it most: stock lines take the latest
balance, so LTM Sep-2023 leverage specifically depends on the 9/30/23 balance sheet). Balance
control ties exactly on all six real periods (confirming the PRD's own FR-VAL-1 text: RB's
balance-control row really is zero, so the original plan's "reproduce a balance-control
discrepancy" ask was never achievable — see the false-premise note below); leverage, current
ratio, and fixed-charge coverage all now compute on real figures. See
`docs/status/done_JACI_CL_RB_REFERENCE_CASE.md` for the full account, including a second real
correction this same extension surfaced (the equity-roll-forward finding was mis-attributed — it
traces to one spreadsheet tab's own simplification, not the underlying audited financials, which
tie exactly once their own capital-contributions figure is included).

Wave 1's planned phases are complete; the register's own P0 number is current (61%, re-audited);
the exit criterion is now proven on real numbers for both halves (earnings and leverage/coverage/
liquidity) — what remains open is narrower: full granular balance-sheet cross-footing, and
matching the reference workbook's own house EBITDAR/FCC definitions specifically (already declared
gaps, not exit-criterion blockers). Waves 2 through 4 have no plans yet.

## Governed-pipeline wiring gap, found and closed, 2026-08-08

A gap on a different axis than the ones above, caught by `design_note_mode_chassis_completeness.md`
§2.1 (a completeness audit against the japes `AdjudicationAgent` chassis, not this register) and
closed the same day, `plan_JACI_CL_SPREAD_ADJUDICATION.md` Phase 0.

**The gap.** FR-VAL-1/3/4/5's four arithmetic controls (`detect_balance_control`/`_cash_flow_tie`/
`_equity_rollforward`/`_period_continuity`) run only when `validate_package(...,
control_tolerance=...)` gets a non-`None` value. From the Wave 1 landing (2026-07-29) through
2026-08-08, `credit_validation/provides.py`'s `validate()` — the step the *governed pipeline*
(`run_cl_spread`) actually calls — never passed one, and `CLSpreadContext` had no field to carry
it. So the four controls were **implemented, unit-tested, and even RB-verified**
(`test_rb_reference_case.py` calls the detectors directly) — the basis for the 2026-07-29 `done
(RB)` scoring above — but were **unreachable through the one path a real deployment actually
runs**. `done (RB)` was correct against this register's own stated bar ("implemented with tests");
it did not mean "live in the governed pipeline," and a reader could reasonably have assumed
otherwise. That's the same failure mode the "real vs. synthetic" (RB) distinction exists to name,
on a different axis: **unit-verified vs. pipeline-reachable** are not the same claim either.

**The fix.** `CLSpreadContext.control_tolerance: Decimal | None = None` added; threaded through
`credit_validation/provides.py` into `validate_package()`. 2 regression tests
(`tests/unit/test_cl_capability.py`) cover both directions: off by default (matching "tolerance is
institution policy, never a module default" — no value invented here), and the finding surfaces
when a caller sets one.

**Does the P0 number move?** No net change, but not because nothing happened — record why, per
this register's own second lesson (say precisely what's proven, not a single pass/fail headline).
Before 2026-08-08: `done (RB)` was true under "implemented with tests," false under "reachable in
the governed pipeline" — a real gap the register's status vocabulary had no word for. After: both
are true. FR-VAL-1/3/4/5 stay scored `done (RB)`; the VAL P0 figure (83%, 7 done + 1 partial / 9)
and the P0 headline (61%) are unchanged. What changed is that the `done (RB)` claim is now fully
true rather than true-with-an-unstated-caveat.

**Update, same day, second pass.** The demo path (`scenarios/ci_spread/ui/demo_page.py`) now sets
`control_tolerance=Decimal("2")` on its `CLSpreadContext`, so the four controls run for real in the
one live-demo call site, not just when a caller explicitly opts in. `$2` matches the PRD's own
documented RB rounding fact ("$1-2 ending-cash rounding in some years") — a placeholder grounded in
real source text, not an invented number, pending a real institution-configured threshold (there is
still no `arithmetic_control_tolerance` in any pack's `PolicyProfile` — this is a literal in the one
call site, not pack data yet). "Reachable" is now also "on in the one real run that exists."

## Lesson recorded

The `audit` status was worth having. Four requirements scored provisionally at 0.5 were absent, and three scored at `none` already existed. A coverage claim assembled from recollection of a codebase is unreliable in both directions, and the areas where confidence feels highest are not the ones where it is warranted. Read the file.

**Second lesson, 2026-07-29 (Wave 1 re-audit).** A plan's own grounding notes can also be wrong
about the source material, not just about the code — FR-VAL-1's actual PRD text said RB's balance
control ties exactly; the plan asked for a discrepancy that was never there. Read the actual
source document (the PRD PDF itself lives in this repo, `docs/plans/Financial Spreading PRD v0.4
2.pdf`) per requirement, not a plan's summary of it, the same way the first lesson says to read
the code rather than recollect it. And: "the test passes" and "the PRD claim is met" are different
claims when the test's own fixture only covers part of what the claim needs (here: 11
income-statement keys, no balance-sheet keys) — say which parts are proven on real data versus
synthetic fixtures only, per requirement, not as one pass/fail headline for the whole area.

**Third lesson, same day, same extension.** Closing the balance-sheet gap above required reading
the audited statements' own "Statement of Changes in Members' Equity" — a document that existed
in the package the whole time but hadn't been fully read yet. It showed a $195,585 capital
contribution reported explicitly, which meant the equity-roll-forward "discrepancy" reported
earlier that same day was misattributed: real gap, wrong source (one spreadsheet tab's own
simplification, not the underlying financial statements, which tie exactly). A fixture built from
only part of a real document package can still be wrong in the same way a fixture built from no
real data at all can — "real, not synthetic" is not the same guarantee as "complete." Keep reading
until a claim traces to its actual source, not just to *a* source.
