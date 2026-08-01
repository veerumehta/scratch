# Plan: Reclassification and Break-Out Engine

Author: Virendra Mehta · 2026-07-29
Repo: jaci · Baseline: 0.9.8 (dev)
Depends on: plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md (landed; supplies canonical keys and Appendix A classifications on every entry).

Driver: Wave 1d of `plan_JACI_CL_PRD_COMPLETION.md`. FR-MAP-3 and FR-MAP-4 are the two remaining P0 gaps in an area otherwise at 58%, and they gate FR-SPR-1, FR-SPR-2 and FR-RAT-2, all of which need reclassified inputs. Appendix A is the PRD's largest single appendix and none of it is implemented.

Covers FR-MAP-3, FR-MAP-4. Unblocks FR-SPR-1, FR-SPR-2, FR-RAT-2.

> **Status (2026-07-29): DONE, all 4 phases (jaci, unpushed, no version bump).** One design fork
> surfaced before any code was written and was resolved with the user rather than guessed, because
> it shaped every phase downstream: `detect_hardcoded_plugs` groups by `SpreadLineItem.section`
> (the as-reported physical grouping in the source document), a different concept from Appendix
> A's classification taxonomy this plan reclassifies into. Making that detector literally stay
> silent on a reclassified package (the plan's own Phase 2 acceptance wording) requires a genuine
> alternate `SpreadPackage` projection, not just adjustment records — the user chose that fuller,
> more faithful path over a lightweight numbers-only one, and `project_effective_package` /
> `project_breakouts` are it.
> - **Phase 1** (`reclassification.py`, `reclassifications.yaml`): three rule shapes (move / split /
>   conditional_move) as pack data. `ClassificationCategory` uses six distinct values (current/non-
>   current/intangible-asset, current/non-current-liability, net-worth) rather than a shared
>   current/non-current pair, so a rule's target is unambiguous without inspecting which side of
>   the balance sheet its source line sits on. Conditions are DSL expressions over `{"flag": 0|1}`,
>   mirroring `addback_library.py`'s own convention rather than inventing a second one. 8 new
>   chart-of-accounts keys Appendix A names but nothing previously modeled (restricted cash, CSV of
>   life insurance, deposits/deferred charges, related-party A/R and notes, third-party notes
>   receivable, related-party debt, reserves, subordinated debt) — pack-evolution, not scope creep,
>   since the rules need a canonical key to bind to. 19 rules cover every Appendix A row named in
>   this plan's grounding notes, asserted by an enumeration test. The unrelated-party term-debt
>   "split" is two confirmatory moves, not a runtime split — jaci already models CPLTD and
>   long-term-debt-net-of-current as two separate canonical keys, so there's nothing left to divide
>   at runtime for that specific row.
> - **Phase 2** (`apply_reclassifications` / `project_effective_package`): a MOVE/resolved
>   CONDITIONAL_MOVE emits one adjustment; a SPLIT emits two, asserted to sum to the original
>   exactly. The projection relabels a reclassified line's section to its target category and
>   recomputes only the three chart-of-accounts subtotals with an existing home
>   (`total_current_assets`/`total_current_liabilities`/`total_stockholders_equity`); the three
>   categories with no declared subtotal counterpart (non-current asset, intangible, non-current
>   liability) get relabeled with nothing to check against — `detect_hardcoded_plugs`'s own
>   zero-subtotals-means-nothing-to-check guard handles that case already, so no synthetic subtotal
>   needed there. `detect_hardcoded_plugs` runs against the projected package unmodified in the
>   tests and stays silent; total assets is provably unchanged (never touched); current assets
>   changes exactly by what moved.
> - **Phase 3** (`breakouts.py`, `breakouts.yaml`): all 4 Appendix A cases. 3 new chart-of-accounts
>   keys the break-out targets need. `owner_compensation` is the *exact* key `addbacks.yaml`
>   (Wave 1b) already sources from — coordinated, not a parallel set. An unresolved break-out
>   (no fact supplied) leaves the parent line completely untouched, never estimated. The combined
>   interest/amortization split's three adjustments (two targets, one parent-reduction) sum to
>   zero exactly. "D&A wherever it sits" has no parent to reduce (`parent_key: null`) — purely
>   additive visibility, not a reallocation.
> - **Phase 4**: `tangible_net_worth` authored as a pure DSL metric (`metrics.yaml`), the "where
>   policy requires" clause a DSL `if()` reading an `ASSUMPTION` binding rather than new Python —
>   verified against real YETI FY2023 10-K figures (`723,610 - 54,293 - 117,629 = 551,688`), not
>   an invented fixture. FR-SPR-1/2's "point spread_template.yaml at effective classifications"
>   turned out to need no template edits at all: the template's existing rows already reference the
>   same canonical keys `project_effective_package` updates in place, so a new
>   `standardized_template_rows` composes reclassification + the existing unmodified template
>   render — "pointing" is which package backs the render, not new rows.
> - 32 new tests (`test_reclassification.py` ×15, `test_breakouts.py` ×5, plus 2 existing suites
>   updated for the new metric/key counts); full jaci suite 574 passed, 2 skipped, no regressions.

## Grounding notes (verified 2026-07-29 against dev)

- `chart_of_accounts.yaml` already declares an Appendix A classification on every one of its 64 entries. The taxonomy exists; nothing applies it. That was deliberate in the chart-of-accounts plan, which declared classifications so this engine would have something to bind to.
- `capabilities/commercial_lending/normalize.py` `NormalizationAdjustment` has `kind: Literal["add_back", "reclassification"]`, so the type exists. But `apply_normalization` sums only `add_back` entries and records reclassifications in the derivation as **deliberately net-neutral to the target**. Reclassification is therefore representable and inert. This plan makes it act.
- Net-neutral to a *metric total* is correct and must stay correct. A reclassification moves a value between balance-sheet categories; it does not change total assets. What it changes is every subtotal and every ratio that reads a category. That distinction is the whole design problem here.
- `detect_hardcoded_plugs` in `validation.py` compares a section's subtotal against its components as-reported. Once reclassification moves a line between sections, that check must run against the as-spread layer or it will fire on every reclassified section.
- Appendix A rules, verbatim in shape: prepaid expenses, restricted and sinking-fund cash, cash surrender value of life insurance, deposits and long-term deferred charges, and related-party A/R and notes all move to non-current. Third-party notes receivable split current at twelve months. Goodwill, patents, trademarks and capitalized costs become intangible. CPLTD current. Unrelated-party term debt splits current portion and non-current by maturity. Related-party debt is current unless subordinated to the bank. Reserves are current or non-current per expected payment timing. Subordinated debt is non-current and may be equity-like per policy. Capital stock, surplus and retained earnings are net worth.
- Income-statement break-outs named: officers' and owner compensation, all D&A wherever it sits, interest embedded in COGS, and splitting combined interest-expense-and-amortization-of-debt-costs into components.

## Phase 1 - Reclassification rules as pack data

New `config/packs/ci-spread-core/reclassifications.yaml`. Each rule declares: id, the canonical source key or a classification it matches on, the target classification, a condition in the DSL where the rule is conditional, a rationale string carried onto the adjustment, and whether the rule is a default the customer template may override.

Three rule shapes, because Appendix A contains three and collapsing them loses information:

- **Move.** A whole line changes classification. Prepaid to non-current.
- **Split.** One line divides across two classifications by a criterion, typically maturity. Third-party notes receivable at twelve months; term debt into current portion and non-current.
- **Conditional move.** Classification depends on a fact outside the line. Related-party debt is current unless subordinated to the bank; related-party A/R is non-current unless genuinely trade, in which case it stays and is flagged.

That last case is worth care. Appendix A says "if truly trade, keep as trade but flag." A rule that silently keeps the line and emits nothing has lost the instruction. Keeping and flagging is an outcome, not a no-op.

Reserves are the other awkward one: current or non-current per expected payment timing, which is not derivable from the line. Model it as a conditional move whose condition references an input that may be absent, and emit an unresolved-classification finding when it is. Do not default it silently either way.

Acceptance: every Appendix A row maps to exactly one rule, asserted by a test that enumerates the appendix rows against the loaded rules. Every rule's source key resolves to a chart-of-accounts entry.

## Phase 2 - The applier

`apply_reclassifications(package, *, rules, profile) -> list[NormalizationAdjustment]`, then extend `apply_normalization` so reclassification adjustments act.

The invariant to hold, stated as the design intent: as-reported is never mutated. Reclassification produces an as-spread layer where a line's *effective classification* differs from its reported one, with the reported classification and the rule that changed it both retained. FR-MAP-5 is already satisfied for add-backs; this extends the same guarantee.

Consequences to handle rather than discover:

- Subtotals must recompute from effective classifications, not reported ones. This is the real work; the classification move itself is trivial.
- Totals must not change. A test should assert total assets is identical before and after reclassification while current assets is not. If total assets moves, a rule is dropping or duplicating a value.
- Splits produce two adjustments from one line and must sum to the original exactly, in `Decimal`. Assert this per split rather than trusting it.
- `detect_hardcoded_plugs` and the Phase 2 cross-foot from the validation plan must run against effective classifications once this lands, or they will fire on every reclassified section. Coordinate; do not let this land while that check reads reported classifications.

Acceptance: total assets unchanged, current assets changed, every split summing exactly, and the existing balance-sheet subtotal detector silent on the reclassified YETI package.

## Phase 3 - Break-outs

`breakouts.yaml` plus an applier for the four Appendix A cases: officers' and owner compensation out of SG&A, all D&A wherever it sits, interest embedded in COGS, and splitting combined interest and amortization of debt costs.

A break-out differs from a split in where the information comes from. A split divides a line by a criterion the line carries, such as maturity. A break-out extracts a component that is *not separately reported*, so its amount comes from a note, a schedule, or an assumption. That means a break-out is frequently an assumption input, and it must carry that provenance rather than presenting as a reported figure.

Where the amount is unavailable, emit the break-out as unresolved with the parent line untouched. Do not estimate. An unbroken-out SG&A is a known limitation; a guessed officer comp is a fabricated number inside a credit decision.

Break-outs feed FR-ADJ-2's owner-compensation add-back, so coordinate the key names with `plan_JACI_CL_ADDBACK_LIBRARY.md` Phase 2 rather than inventing a parallel set.

Acceptance: a fixture with officer comp disclosed in a note breaks out with assumption provenance and SG&A reduced by exactly that amount, with the operating income subtotal unchanged. A fixture without the disclosure produces an unresolved finding and an untouched SG&A.

## Phase 4 - Tangible net worth and the standardized statements

With effective classifications available, close the three requirements that were waiting on them.

- FR-RAT-2 tangible net worth: net worth less intangibles, and less disallowed related-party receivables where policy requires. Author as a metric definition, not code. The "where policy requires" clause is a DSL condition reading a profile flag.
- FR-SPR-1 and FR-SPR-2: the standardized balance sheet and income statement now reflect reclassified placement rather than reported placement. Largely a matter of pointing `spread_template.yaml` rows at effective classifications.

Acceptance: tangible net worth on the YETI package excludes intangibles and matches a hand-computed figure. The standardized balance sheet's current-assets subtotal reflects the reclassifications from Phase 2.

## Out of scope

RMA peer-category mapping (FR-MAP-8, P1). Learning and persisting borrower-specific mapping corrections (FR-MAP-6's second sentence). Layered presentations (FR-MAP-7, Wave 2d), which consumes this layer rather than building it. Customer-template override of default rules; the rules declare which are overridable, but the override path arrives with template ingestion in Wave 4b.

## Sequencing

Phase 1 is authoring and can start immediately. Phase 2 is the substance and its subtotal recomputation is where the risk sits, so land it with the totals-unchanged assertion before anything consumes it. Phase 3 is independent of Phase 2 and can run in parallel, but its key names must be agreed with the add-back plan first. Phase 4 depends on Phase 2 and is mostly authoring.

Coordination note: this plan and `plan_JACI_CL_VALIDATION_COMPLETION.md` both touch how subtotals are computed and checked. Whichever lands second must re-point the other's checks at effective classifications. Do not run them in parallel sessions.
