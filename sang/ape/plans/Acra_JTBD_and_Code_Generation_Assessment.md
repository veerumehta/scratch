# Acra DSCR: hand-built JTBDs vs SDK JTBDs vs generated code

Author: Virendra Mehta
Scope: `acra_bundle` (trial pack `acra-regen-3b`) and the japes policy pipeline (`jazzx_sdk/pipelines/policy/`, `jazzx_sdk/pack/ledger.py`, seed pack `acra_dscr_policy`).

## TLDR

The two JTBD sets differ for three reasons, in this order of weight. First, they treat the consolidation's open questions differently: both sets were written from the same consolidated guidelines v1.0 (the hand-built set cites the consolidation's own section numbers and its Appendix B.3), but where the consolidation parks a point as a Q-xx question, the hand-built set makes a call and the SDK set writes the hedge into the job. Second, the SDK writes jobs one section at a time and the planner is told a clause "may belong to more than one" section, so one clause is written as a job in up to six sections (the Platinum listed-for-sale clause alone yields 32 jobs); the fold step catches almost none of these because it requires the same kind, the same figures and 80% word overlap. Third, the SDK job is pinned to a 47-field case record that was reverse-engineered from our hand-coded policies, while the hand-built set is written against the canonical loan object (Asset, Liability, RealEstateOwned, AppraisalSummary, dates, amounts). Only 10 of the fields the two sets reason over are shared, and the hand-built set's own notes record the mirror-image gap: it lacks the derived fields (entity borrower, qualification method, listing history) that our record has, and we lack the canonical ones it has. The hand-built set is also not a clean reference; Platinum declares nine of its 108 jobs as duplicates kept on instruction.

Code was generated for 99 of 231 jobs (43 Standard, 56 Platinum). It was not generated for the rest for one mechanical reason: the writer declared no computable check (`computable_checks: []`) for 75 jobs that do read fields, and 30 jobs read no field at all. The writer is conservative, and in several cases wrong (jobs whose checks are fully decidable from the fields they read were marked not computable). Where code exists it covers 79 of 129 checks on Standard and 37 of 111 on Platinum; the rest is left to a reviewer. The biggest quality defect in the generated code is input fidelity, not model skill: the clause handed to the code writer drops the headings that label tables, so the FICO/CLTV matrix rule cannot tell which loan-amount tier applies and hedges with an all/any vote.

The fixes are in the SDK, not in prompting alone: (1) bind the Acra template to the canonical object schema, not the 47-field record, and tell the writer how to treat an unresolved point (decide on the printed text and flag the question, rather than refuse); (2) assign each unit to one section and write cross-section jobs from a shared unit view, which removes the duplication at the source; (3) make computability a per-check decision made by a second pass with the catalog in hand, not a side output of the job writer; (4) carry headings and table context into the ledger clause; (5) measure coverage per clause, not per citation, since citation coverage reads 116/123 while real check coverage is materially lower (the declining-market -5% CLTV rule is cited by seven jobs and checked by none).

## 1. What is in the bundle

| | Standard | Platinum |
|---|---|---|
| Hand-built JTBDs (KStudio, "Fable-improved" v9) | 123 | 108 |
| SDK jobs (procedure rules) | 121 | 110 |
| SDK python rules written from jobs | 43 | 56 |
| Checks across SDK jobs | 289 | 197 |
| Checks the writer marked computable | 79 | 37 |
| Clauses in the consolidated guideline (STD-x.y / PLAT-x.y) | 123 | 94 |

The counts match by coincidence. The two sets partition the policy differently, so a job in one set is rarely one job in the other.

## 2. The two JTBD sets: how they differ and why

### 2.1 Same source, different posture on open points

Correction (2026-10-22): an earlier version of this section said the hand-built set was written from Acra's originals rather than our consolidated guidelines, citing South Dakota, the Family Rider, ARM margins, the 8.17.2026 summary and the Correspondent channel as absent from the consolidation. Checked term by term, every one of them is in the consolidation (South Dakota as "SD" in STD-1.13 and PLAT-1.16; the Rider, Exhibit 8, 1 Yr CMT, 2/2/6 and both summary dates in the Standard document; Correspondent 19 times in the Platinum one). The evidence runs the other way: LFC-FICO-FINAL, LFC-DSCR-FINAL and AFC-RESERVE-TOTAL cite the consolidation's own section numbers (§12.2, §3.18, §9.2, which do not exist in Acra's guide), and the note on AFC-UNACCEPT-SRC repeats the consolidation's Appendix B.3 ("Seller's Guide material referred to but not reproduced"). Both sets were written from the same consolidated guidelines v1.0.

What does differ is how each set treats the consolidation's open points. The consolidated document is a review draft: it quotes the Acra text, numbers it, and parks unresolved points as Q-xx questions. The SDK jobs inherit that posture: several instruct "Do not resolve whether STD-3.5 or STD-3.6 governs" and list "Acra confirmation requested (Q-21)" as missing data, which also marks the check not computable. The hand-built set makes the call on the printed text (DSCR-QUALRENT picks the lesser-of formula and names the exception; CMP-SRC-VERSION pins the source versions) and leaves the question as a note. That is a writer-prompt and template matter: the writer should decide on what is printed and carry the open question as a flag on the job, not as a reason to withhold a check.

### 2.2 Different unit of work

Hand-built jobs are concept-anchored. Each one is one underwriting decision with a stable mnemonic, and the set has three shapes the SDK set lacks:

- Definitions as their own jobs: PRE-LISTDEF (is it "listed for sale"), BOR-FN-DEF, BOR-ITIN-DEF, BOR-FTHB-DEF, LPE-BIZ-CONSUMER, LPE-CHANNEL. Downstream jobs cite the defined fact instead of re-deriving it.
- Aggregators: LFC-CLTV-FINAL (lowest of every cap), LFC-FICO-FINAL (highest floor), AFC-RESERVE-TOTAL (sum of reserve triggers), LFC-DSCR-FINAL. These are the jobs that turn a pile of overlays into one answer.
- Loan metrics with indicator context and description templates on 90 of 123 jobs, plus extraction targets per entity.

SDK jobs are clause-anchored and section-scoped. A job is "what this section's units require", written by a model that sees one section and nothing else. The template does declare kinds (determination, limit, verification, condition, judgment) and asks for determinations first, and the run did produce 31 determinations, but they are not reused: Standard has `credit_review_analysis.citizenship_type_eligibility`, `loan_program_eligibility.citizenship_category` and `identification_requirements.*` all re-deriving citizenship, and nothing aggregates caps. The export (`jtbdset.json`) carries no `loan_metrics` and no `extraction_targets`, its Deterministic Validation Rules are prose rather than field expressions on 222 of 231 jobs, and every step is headed "## Step" with no number, so the KStudio shape is not met even where the content is.

### 2.3 Duplication across sections

This is the largest structural difference and it is caused by two lines of our own code and prompt.

`policy_jtbd/plan_prompt.md`: "Every unit that states a requirement belongs to at least one section; a unit may belong to more than one." `SectionSegmenter.segment()` honours that and never de-duplicates a unit across sections. Then `JtbdExtractor.extract()` writes each section in isolation.

Measured on the bundle:

| | Standard | Platinum |
|---|---|---|
| Citations that span more than one section | 18 of 46 | 23 of 35 |
| Jobs from the single worst clause | 16 (citizenship types, 3 sections) | 32 (listed for sale, 6 sections) |
| Near-duplicate job pairs (check text, Jaccard >= 0.6) | 13 | 22 |
| Jobs the fold step removed | 1 | 2 |

Platinum has `listed_property_reserves` under asset_assessment and title_review, `listed_property_amortization` under asset_assessment, liabilities_assessment and title_review (one pair is word-for-word identical), `listed_property_prepayment_penalty` under three sections, and so on. The fold step (`jtbd_fold.fold_duplicates`) only merges pairs with the same `job_kind`, the same printed figures and >= 0.8 Jaccard on skill + purpose, or 0.6 with a judge. Restatements routinely land as different kinds (limit vs verification vs condition), so they never fold. The fold is treating a symptom; the planner is the cause.

### 2.4 Section assignment drifts from the taxonomy

The planner is given the hand-built taxonomy as a hint ("Use these section names where they fit") but has no definitions for them, so it files by surface association. DSCR calculation lands under Property Tax Calculation (both programs), citizenship under Credit Review, foreign-national closing documents under Title Review, vacant-property rules under Compliance and Closing. The hand-built set has no Title Review, Liabilities or Property Tax sections at all for this program; the SDK set puts 20 Platinum jobs under Title Review. Mnemonics follow the section, so a wrong section gives a wrong family (TTL-, LIA-, TAX- prefixes that Acra's set never uses).

### 2.5 Different data vocabulary

The SDK writer may only read fields in `jtbd_template.yaml` `reads` (47 names, bound from `schemas/loan_application.json`, 54 fields). That record was built backwards from the policies we hand-coded earlier, so it is full of pre-digested booleans: `tradelines_meet_requirement`, `entity_documents_complete`, `mortgage_0x30x24`, `listed_for_sale_last_6_months`. The judgment the job should encode has been pushed into the field name. There is no DSCR field, no rent, no PITIA, no purchase price, no listing price, no dates, no reserves in dollars, no document-presence facts.

The hand-built set writes its deterministic rules against the canonical object (50 distinct field paths on Standard, including `RealEstateOwned[is_subject_property=True].gross_rental_income_usd`, `LoanCore.application_date`, `LoanCore.expected_closing_date`, `LoanCore.interest_only_period_months`). Overlap between the two vocabularies is 10 fields on Standard and 8 on Platinum. The SDK's own coverage workbook lists 503 distinct "data no field holds" strings across 231 jobs: closing date, lowest listing price, purchase price, calculated DSCR, lease end date, annual P&I, taxes, insurance, HOA. These are ordinary canonical fields we already have in the mortgage schema.

### 2.6 What the hand-built set says about itself

The jaci copies (`jaci/config/packs/dscr_core/policies/acra_New_Guideline_JTBD*.json`) are byte-identical to the bundle's. In that pack they sit beside the 42 hand-coded rules of `eligibility.yaml` but the manifest does not reference them and the loader skips them by shape (`is_policy_document`), so jaci holds them as reference material, not as a loaded corpus. The route by which they enter a pack is japes' `jtbd_import` (core for jobs identical in both programs, an overlay per program for the rest).

Each file carries a `notes` field on 20 Standard and 24 Platinum jobs, and those notes change the picture in two ways.

First, the hand-built set is not a clean reference. Platinum declares nine jobs as duplicates "retained per instruction" (LPE-DECL-MKT of PRE-DECLMKT, LPE-VACANT of PRE-VACANT, LPE-MIN-DSCR of DSCR-MINRATIO, LPE-GIFT-MIN of AFC-GIFT-MIN, LPE-INELIG-LOC of PRE-LOCATION, LPE-SIZE-CLTV of LFC-AMT-STEPDN, LPE-CO-LEASE/DSCR-CO-LEASE, BOR-GUAR-ATTEST of BET-FTHB-ATTEST, CRD-PCESEASON of CRD-PCE-SEASON). So the 108 is nearer 99 distinct decisions, and the Loan Program Eligibility section (39 jobs) is where the restatements were parked. Our set's cross-section duplication is worse in degree, not different in kind, and whatever fold we build should run on an imported set too.

Second, the hand-built set hit the ontology from the other side. Its notes record gaps in mortgage_ontology_v2: no entity-borrower value in `Borrower.borrower_type`, no entity ownership percent, no listing history or last listing date, no statement dates on Asset, no lease end date, no business-purpose flag, no DSCR qualification method, and subject state unreachable because `SubjectProperty.address` is a `$ref` the validator does not resolve. Several of those are exactly the fields our 47-field record has (`Borrower.entity_type`, `Borrower.is_entity_borrower_1`, `LoanCore.dscr_qualification_method`, `SubjectProperty.state`, `SubjectProperty.listed_for_sale_last_6_months`), and the rest are on our schema backlog too (lowest listing price, closing date, lease end date). The two sets name the same missing facts from opposite ends: theirs has the canonical object and lacks the derived layer; ours has the derived layer and lacks the canonical object. The right catalog is the union, with the derived fields declared as determinations over the canonical ones (item 7 below). The AFC-UNACCEPT-SRC note, which repeats the consolidation's Appendix B.3 wording, is one of the signs that the hand-built set was written from the consolidation (see 2.1).

### 2.7 Clause coverage is overstated

The ledger reports 116 of 123 Standard clauses and 91 of 94 Platinum clauses cited by some job. That is citation coverage. `JtbdExtractor._candidate()` cites the units the writer named in `source_units`, and when it names none, cites every unit of the section. 71 of 121 Standard jobs cite four or more clauses; 33 cite seven or more. So "cited" does not mean "checked". Test case: STD-1.14 / STD-8.4, the declining-market -5% CLTV reduction. Seven Standard jobs and four Platinum jobs cite it; none of their checks, steps or purpose mention it. The same holds for the 1x30x12 mortgage-history tiers, the Standard ARM margin table, and No Ratio on Platinum (10 mentions in the guide, zero jobs). These are limits, the kind the template says expects code.

## 3. The generated code: what was coded and why the rest was not

### 3.1 The gate

`code.codable(rule)` admits a job when it is a job, has checks or a clause, and `computable_checks != []`. `_candidate()` forces `computable_checks = []` whenever the job reads no declared field. `JobCodeExtractor.extract()` then drops any draft whose code reads none of the declared fields. So the entire decision is: did the writer name at least one catalog field, and did it index at least one check as computable.

What that produced:

| Writer's assessment | has reads | code | Standard | Platinum |
|---|---|---|---|---|
| some checks computable | yes | yes | 33 | 30 |
| not assessed (None) | yes | yes | 10 | 26 |
| not assessed (None) | yes | no (draft read no declared field, or rejected) | 7 | 20 |
| none computable ([]) | yes | no | 56 | 19 |
| none computable ([]) | no | no | 15 | 15 |

Two things stand out. The 75 jobs that read fields but were declared "none computable" are the bulk of the gap, and the declaration is unreliable. `acra-platinum.liabilities_assessment.listed_investment_property_occupancy` reads `listed_for_sale_last_6_months`, `occupancy_subtype` and `is_vacant`, its single check is "if listed and investment then tenant-occupied and not vacant", and it is marked not computable. `compliance_and_closing.listed_property_maximum_cltv` reads `cltv_percent` and the 65% cap and is marked not computable because the "lesser of appraised value or lowest listing price" basis has no field, even though the cap itself is decidable and the hand-built set codes exactly that. The writer prompt defines computable as "comparisons over those case fields alone decide, with no document to read and no judgment to make"; any residual document step makes the whole check non-computable in the writer's reading.

The second thing: 36 jobs where the writer said nothing (`None`) were coded anyway, and `codable()` treats "unassessed" as "try". That is the right default and it worked; the asymmetry is that an explicit `[]` is final and nothing re-examines it.

By kind, coded share is 49 of 62 limits, 15 of 31 determinations, 28 of 115 verifications, 7 of 21 conditions, 0 of 2 judgments. Verifications dominate the uncoded set, and most of them are document-presence checks ("an executed W-8 BEN is provided"). Those are computable the moment the case record has a document inventory, which the document registry already models.

### 3.2 Partial code is the norm

Code "from a job" encodes only the checks indexed as computable. The Standard listed-for-sale job has ten checks; its python rule decides four (listed, tenant-occupied, not IO, CLTV <= 65) and returns True for a case that violates the other six (lien delinquent, no 24 months reserves, subordinate financing present, no impounds, PPP under three years, DSCR below 1.0). That is by design (`JOB_SCOPE_NOTE`: never fail a case for the others), and the disposition `code_and_procedure` records it. But the reviewer-facing output does not say which six, and a rule that returns True while six conditions are unverified reads as a pass. Overall: Standard coded jobs carry 129 checks of which 79 are decided; Platinum 111 of which 37.

### 3.3 Input fidelity defects in the code path

The clause the code writer sees is `ledger.clause`, built in `_candidate()` as `"\n\n".join(p.text for p in cited)`. It drops `heading`, which `_render_unit()` does give the job writer. The matrix rule shows the cost: the three FICO/CLTV tables arrive without their "Loan amount <= $1,500,000 / $1,500,001-$2,000,000 / $2,000,001-$3,000,000" headings, the generated code comments "the excerpt prints the three tables but does not print their loan-amount tier labels", and it returns True only if the CLTV passes all three tables, False only if it fails all three, and unknown otherwise. For a $1.2M loan at 700 FICO and 78% CLTV purchase the printed answer is pass (80%); the code answers unknown. The hand-built LFC-FICO-MTX gets this right in one sentence.

Other defects of the same family: jobs that cite seven or more clauses pass a wall of text to the code writer, so the model picks figures from the wrong clause (one Standard and one Platinum rule carry figures the text does not print, flagged by `unprinted_figures`); and the `(bool, dict)` reporting form is rarely used, so the trace does not say which value tripped.

What works well and should be kept: the static check (allowed imports, forbidden names, reads derived from the source), the `rules_lib` idioms (gaps/unknown, same, band), the self-written cases with a repair loop (zero case mismatches survived in the bundle), and the tier/band helpers for thresholds.

## 4. What to change

### 4.1 JTBD generation

1. Tell the writer what to do with an open point. The consolidated guideline is a review artifact with Q-xx questions; today the writer turns each one into "do not resolve" steps and a missing-data line, which also blocks code. Add to `write_prompt.md` (or the pack's `instructions`) that a check is written on the text as printed, and that a question the document raises about it is recorded on the job as an open item, not as a reason to leave the check undecided. Resolving the Q-xx items into the document before a run is still worth doing, but it is not a precondition for the SDK set to match the hand-built one.

2. One unit, one home. Change `plan_prompt.md` to assign each unit to exactly one section and `SectionSegmenter.segment()` to enforce it (first assignment wins, or the planner ranks). Give the planner the section definitions from the template (`families` descriptions are already there and are not shown to it). This removes most duplication at the source and makes the fold a safety net rather than a filter.

3. Write cross-cutting jobs from a shared view. After section writing, run a second pass over all jobs of the program with the whole unit list, producing the two shapes the hand-built set has and ours lacks: definitions (determinations that others cite by name, with `maps_to: derived_field` wired so a later job's read of `Borrower.is_foreign_national` resolves to it) and aggregators (CLTV final, FICO final, reserves total, DSCR minimum). The template already has `kinds` and `_determinations_first`; what is missing is a pass that sees the whole program.

4. Replace citation coverage with clause coverage. For each unit, ask whether some job's checks decide it (a cheap model call per unit against the jobs that cite it, or lexical figure matching as a first cut). Report uncited-by-check units as gaps in `coverage_trial.xlsx`. Require the writer to name `source_units` per check, not per job, and stop defaulting to "all units of the section" when it names none.

5. Fix the fold so it folds. Drop the same-kind requirement (restatements land as different kinds), compare on checks rather than skill + purpose, and let the judge see the clause ids both jobs cite (two jobs citing the same STD-x.y with similar checks are one job). Rank survivors by the template's section order, which is already there.

6. Export in the consumer's shape. `jtbdset_export` should fill `section` from the job's section (today it is the program name), number steps per `step_outline`, emit `loan_metrics` from the metrics the writer named (the template asks for them; the export discards them), and write Deterministic Validation Rules as field expressions when the job has reads.

### 4.2 Data vocabulary

7. Bind the Acra template to the canonical object schema, not `loan_application.json`. The mortgage canonical schema (LoanCore, Borrower, Asset, Liability, RealEstateOwned, AppraisalSummary, HazardInsurance, TitleInformation, CondoProject, MortgageLoanInformation) is what the hand-built set writes against and what our extraction already fills. The 47-field record should become the derived layer on top of it (`derived_field` is the right home for `listed_for_sale_last_6_months`, `is_first_time_homebuyer`, `tradelines_meet_requirement`), not the vocabulary. The 503-line schema backlog is the shopping list; most of it is already a canonical field.

8. Add document-presence facts. Most uncoded verifications are "document X is on file". The document registry knows the types; expose per-type presence and key attributes (`Documents.w8_ben.present`, `Documents.good_standing.issued_date`) as readable fields, and the writer can mark those checks computable.

9. Turn on `data_mapping` with the full vocabulary and lower its bar. It mapped three texts in this run because the target list was 47 names. With the canonical fields, "Closing date", "Purchase price", "Calculated DSCR" map directly.

### 4.3 Code generation

10. Make computability a second pass, per check, with the catalog. Today it is a side output of the job writer, binary per check, and `[]` is final. Replace with a small call per job after data mapping: for each check, the fields it needs, which exist, and whether the check decides with those fields alone or decides a sub-predicate (the 65% cap without the listing-price basis). Record `computable`, `partially_computable` (with the sub-predicate), `needs_field` (with the field named), and `judgment`. `codable()` then admits `computable` and `partially_computable`, and `[]` is never a terminal state while a check names an existing field.

11. Carry structure into the ledger clause. `_candidate()` should store each cited part with its heading and table context (the `(under: heading)` line the writer already gets), and `job_clause()` should render it. The matrix rule becomes correct with no model change.

12. Narrow what the code writer sees. Pass only the units the job's computable checks cite, not every unit the job cites. Seven-clause walls are where unprinted figures come from.

13. Make partial code say what it did not decide. The python rule should return `(verdict, {"decided": [...], "left_to_reviewer": [...]})` using the `(bool, dict)` form the prompt already allows, and the ledger should surface "left to reviewer" per rule so a True from a four-of-ten rule is not read as a pass.

14. Give the code writer the derived fields. Once determinations map to derived fields (item 3), the code writer can read `Borrower.is_foreign_national` rather than re-deriving it from `citizenship_status` in thirty rules, and aggregator jobs become one function over the caps the limit rules emit (the pack's `compose_caps` already does min-of-caps at run time; the jobs should mirror it).

### 4.4 Sequence

Items 2, 4, 5, 11 and 12 are code-only changes in `jtbd.py`, `jtbd_fold.py`, `code.py` and the two prompts, and can be done before the next regeneration. Item 7 is the one that changes the numbers most (it unlocks items 8, 9, 10, 13) and is a pack change plus `bound_to_catalog`. Item 1 is a prompt line and a job field. Item 3 and item 6 are the ones that make the SDK set look like the hand-built set to its consumer.

## 5. Evidence index

- Bundle: `acra_bundle/README.md`, `3_sdk_jtbds/*_policy.yaml` (fields `reads`, `computable_checks`, `missing_reads`, `domain_extensions.ledger.clause`), `3_sdk_jtbds/ledger.yaml`, `5_comparison/coverage_trial.xlsx` (Summary, Schema backlog, Documents, Derivations sheets), `4_sdk_code/from_jobs/standard/loan_program_eligibility__matrix_fico_and_cltv__python.py`.
- SDK: `jazzx_sdk/pipelines/policy/jtbd.py` (`SectionSegmenter.segment`, `JtbdExtractor._candidate`), `jtbd_fold.py` (`fold_duplicates`), `jtbd_data.py`, `code.py` (`codable`, `job_segment`, `JobCodeExtractor`), `jazzx_sdk/pack/ledger.py` (dispositions), `jazzx_sdk/prompts/files/policy_jtbd/plan_prompt.md`, `write_prompt.md`, `policy_code/job_prompt.md`.
- jaci: `config/packs/dscr_core/policies/acra_New_Guideline_JTBD.json` and `_Platinum.json` (identical to the bundle copies; `notes` fields), `pack_manifest.yaml` (does not declare them), `policies/eligibility.yaml` (42 hand-coded rules).
- Pack: `plato/data/seed_packs/acra_dscr_policy/jtbd_template.yaml` (47 reads, no `fold`/`data_mapping` in the seed; the trial pack had both on, with 3 folds and 7 mappings), `schemas/loan_application.json` (54 fields).
