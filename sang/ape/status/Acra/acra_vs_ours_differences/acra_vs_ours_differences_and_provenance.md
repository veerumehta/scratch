# Acra's K-Studio JTBD sets against ours: every difference, where it came from, whether we can derive it

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
Written 2026-10-29 by sonnet-packs. Read-only analysis, no run, no spend. Counts only; nothing here touches loan data.

## 0. Scope, sources and how far to trust it

| | File | Jobs |
|---|---|---|
| theirs, Standard v9 (9.0.0, received 2026-10-05) | `acra_bundle/2_kstudio_jtbds/standard_v9.json` | 123 |
| theirs, Standard v17 (17.0.0, received 2026-10-27, stated as Fable 5.1) | `standard_v17.json` (same as `docs/acra-v1/Acra-Standard-JTBDs.json`) | 124 |
| theirs, Platinum Select v7 (7.0.0, received 2026-10-05) | `platinum_select_v7.json` | 108 |
| ours, regen-5 Standard / Platinum (trial pack `acra-regen-5`, `flex_gpt-6-luna`, SDK 2.6.6) | `3_sdk_jtbds/jtbdset_standard.json`, `jtbdset_platinum_select.json` | 114 / 81 |

Pipeline sources read for provenance (policy-workbench, branch `JAPES_V2`, `backend/`): `policyforge/prompts/ontology/JTBD_ONTOLOGY_GUIDE.md` (the guide),
`mortgage_jtbd_ontology_v1.json` (the schema), `mortgage_ontology_v2.json` (entities), `policy_creator/writer_system.md` and `planner_system.md`,
`policy_modifier/file_creator_system.md`, `mpr/jtbd_resolver.py` and `mpr/patterns.py` (the export parser). Also our `jtbd_template.yaml`, sonnet-runtime's
`note_job_identity_equivalence.md`, my regen-5 comparison workbook, and, for the Revolution shape only, kernel-lab's `jtbds_revolution.json` (a legacy v1.0.1 set of 157
jobs; the v6.7 set is not in the repo, so every "Revolution" statement below is about that older file).

**Reliability.** Counts in section A come from scripts over the five JSON files and are complete (every job). Statements about what the home-mortgage side
"defines" are read from the workbench files and are one reader, complete for those files. Provenance is a claim about which source states or implies the convention;
it is not proof of who or what produced Acra's file. Acra's generation run is not visible to us, so "who wrote it" is unknown wherever no source states it. Model effects:
theirs is stated as Fable 5.1 (v17 only; v9 "Fable, version not stated"; v7 not stated), ours is Luna. Nothing below is credited to a model, because no run isolates it
(variance between identical runs is unmeasured on our side, and theirs has one run per version).

**Provenance labels used in section B:**
`GUIDE` = the home-mortgage JTBD ontology guide or its schema. `WRITER` = the policy-workbench writer, planner or modifier prompt. `EXPORT` = workbench export/import code
(the parser that reads and numbers files). `K-STUDIO` = a Knowledge Studio tool default (not visible in the repo; inferred only where the file shape forces it).
`ACRA` = an Acra-specific edit or choice, visible as a difference between their own versions. `UNKNOWN`.

## A. Differences, one row per dimension

### A1. Header and identity

| # | Dimension | v9 | v17 | v7 | ours (regen-5) | Notes and evidence |
|---|---|---|---|---|---|---|
| 1 | File title / description | `...Standard-DSCR-JTBDs-Fable-Improved` | `...Standard-DSCR-JTBDs-2-Fable` (description ends `-Improved`) | `...Platinum-DSCR-Fable-improved` | n/a | Their names carry the model ("Fable") and "Improved". |
| 2 | Jobs | 123 | 124 | 108 | 114 / 81 | Standard: 114 ours vs 124 theirs; Platinum: 81 ours vs 108 theirs. |
| 3 | Distinct sections | 8 | 8 | 7 (no Identification Requirements) | 8 / 9 (Platinum adds "Unassigned Provisions", 9 jobs) | Their sections are the same closed list in all three; 38 of 114 Standard and 24 of 81 Platinum of ours carry a name from it, the rest carry the policy's long name (e.g. "Appraisal Review Property Eligibility"). |
| 4 | Jobs per section (Standard) | LPE 31, Ident 20, Compliance 19, Income 17, Credit 12, Appraisal 11, Assets 9, Insurance 4 | LPE 35, Compliance 25, Income 16, Appraisal 14, Credit 13, Ident 11, Assets 6, Insurance 4 | Platinum: LPE 39, Compliance 19, Credit 15, Income 13, Appraisal 9, Assets 9, Insurance 4 | Std: Ident 25, Credit 21, Appraisal 16, Assets 14, LPE 13, Compliance 12, Income 9, Insurance 4 | Same clause lands in the same section for 53 of 80 matched Platinum clauses and 70 of 104 Standard ones (my workbook, one reader). |
| 5 | `section_type` values | 8 values from the schema's standard list (Eligibility, Identification, Compliance, Income, Credit, Collateral, Assets, Insurance) | same 8 | 7 | 9 free strings, some long ("property eligibility", "Asset Assessment: assets and funds to close", "Compliance and Closing: the borrowing entity and title", "Unassigned provision") | The schema allows any string of 3+ characters, so ours is legal but not the standard list. |
| 6 | Mnemonic form | `PREFIX-SLUG`, 123 unique | 124 unique, 120 two-part (4 have a second hyphen, e.g. `PGE-DSCR-ELECT`) | 108 unique | 114 / 81 unique, all two-part but the "prefix" is the string `acra-standard` or `acra-platinum` followed by a dotted rule id | See A2. |
| 7 | Prefix count and size | 12 prefixes, 1 to 18 jobs each (BET 18, DSCR 16, LPE 13, CRD 12) | 21 prefixes, 1 to 13 jobs each (CRD 13, BCE 9, LAC 8, BWE 8) | 11 prefixes (LPE 19, BET 18, CRD 15, DSCR 13) | 8 (one per section family), 4 to 63 jobs each | A prefix lives in one section except one prefix per version (v9 `LFC`, v17 `FNP`, v7 none). |
| 8 | Slug length | median 9, 4 to 15 | median 7, 5 to 12 | median 9, 4 to 15 | median 65 (Std), 62 (Plat), 2 to 108 | Ours is the tail of the rule id. |
| 9 | Mnemonic length | median 13, max 19 | median 12, max 16 | median 13, max 19 | median 70, max 113 | |
| 10 | Mnemonics shared between the two programs | 71 shared with v7 | 4 shared with v7 | (same 71 with v9) | 8 shared by both programs (own mnemonics 85) | v7 was built on v9's identities (same section for 69 of the 71, same metric keys for 57, same COMMON text for 0, same skill text for 7). v17 was not built on v9: 4 shared mnemonics of 124, 8 identical skill texts. |
| 11 | `sequence` | present, 1..n per section, contiguous, file grouped by section (7 section changes in file order) | same | same | absent | `sequence` is a required field in the schema; ours omits it. |
| 12 | Source (`source`) | NEW on all | NEW | NEW | NEW | Schema also allows BASELINE and EXTENDED. |
| 13 | Assistant list | Underwriter 99, Processor 19, Officer 5 | 102 / 12 / 10 | 88 / 10 / 10 | Standard: Underwriter 98, Processor 16, no Officer. Platinum: Underwriter 80, Processor 1 | Ours uses two of the three allowed values. |

### A2. Job body

| # | Dimension | v9 | v17 | v7 | ours | Notes and evidence |
|---|---|---|---|---|---|---|
| 14 | Requirement blocks | 5 per job: COMMON, FNMA, FHLMC, FHA, VA | same | same | 3 per job: COMMON, Standard, Platinum | In theirs, every non-COMMON block is `NO_CHANGE` (492 of 492 in v9, 496 of 496 in v17, 432 of 432 in v7). In ours every non-COMMON block is `NO_CHANGE` too (228 of 228, 162 of 162). |
| 15 | Title line | `# <Title> - Base Version` on all | same | same | same, but the title is the whole skill sentence ("# Apply the stated declining-market CLTV reduction and obtain confirmation on its combination with other caps. - Base Version") | Title length median 53 / 59.5 / 52 chars (theirs) vs 105.5 / 119 (ours). |
| 16 | Skill | one sentence, "Confirms ...", median 236 chars; 2 over 400 | median 208; 4 over 400 | median 188; 1 over 400 | imperative ("Apply ... and obtain ..."), median 88.5 (Std) / 102 (Plat) | The schema's cap is 500 characters and the writer's is 400. |
| 17 | COMMON length (chars) | median 1,812 (1,233 to 3,459) | 2,790 (1,733 to 4,328) | 2,358 (1,342 to 3,883) | 1,317 (774 to 4,866) / 1,256 | v17 is about 50% longer than v9. |
| 18 | Step headings | `### Step 1 - Initial Document Review` ... on all | same | same | `## Step 1` .. `## Step 4` (72 Std / 57 Plat) or `## Step 1: Initial Document Review` (42 / 24) | The guide and writer both fix `### Step N - <name>`. |
| 19 | Horizontal rule `---` between sections | 0 | 124 | 8 | 0 | The writer's template shows `---` between Reference Documents, Steps, DVR and Outcomes. v17 matches it on every job; v9 on none. |
| 20 | Deterministic Validation Rules syntax | `condition: TRUE = pass, FALSE = fail`, TRUE on 123 and FALSE on 118 | TRUE 124, FALSE 104 | TRUE 108, FALSE 108 | plain sentences, no TRUE/FALSE on any job; median 1 rule per job (theirs 2 / 3 / 2) | The guide fixes `- <observable condition>: TRUE = <result>, FALSE = <result>`. |
| 21 | Outcome syntax | `### Pass` with "Assign **Pass** when:" (121 of 123) | 123 | 108 | `- **Pass**: ...` bullets on all | The guide and writer fix four `###` outcome headings. |
| 22 | "There is no case for this outcome" | 71 jobs, 89 uses | 58, 74 | 83, 108 | 73, 101 / 76, 117 | The guide's sentence; both sides use it. |
| 23 | Reference documents | one `###` category per job (median 1); document-named bullets ("LOS transmittal (1008)" 35 jobs, "Credit Report" 20, "Appraisal Report" 14, "Note" 11) | entity-named bullets more common ("RatioSet Calculation Record", "AppraisalSummary Record"); `1008` on 0 jobs | document-named (Credit Report 23, Loan Application (1003) 20, Appraisal Report 16, LOS 14) | `### Other documents` on 89 of 114 and 65 of 81, with a few bullets | The writer says to list standard documents (LOS, DU/LP, Credit Report ...). |
| 24 | Cross-references inside the text | 66 of 123 jobs name another job's mnemonic; `§` section refs on 74; Q-nn refs on 63 | 26; 14; 43 | 8; 4; 12 | 0; 4-5; 8 / 5 | The writer says each rule must be self-contained and never delegate to another section. |
| 25 | `Entity.field` tokens in text | on 84 of 123 jobs | 32 | 20 | on 5 (Std), 27 (Plat) | |
| 26 | Figures and caps | filled where the guideline prints them; open questions are conditional outcomes | same | same | open questions become separate referral jobs (11 Platinum, 7 Standard); one cap or footnote often missing as a job | See A4. |

### A3. Metadata blocks (theirs have them, ours do not)

| # | Dimension | v9 | v17 | v7 | ours |
|---|---|---|---|---|---|
| 27 | `loan_metrics` | 100 metrics, at most 4 per job | 180, at most 6 | 89, at most 2 | none |
| 28 | `metric_key` form | `Entity.field`, all dotted; filtered `Entity[k=v].field` on 5; nested (2+ dots) on 1 | filtered 9, nested 1 | filtered 4, nested 1 | n/a |
| 29 | `metric_mnemonic` | `<MNEMONIC with _ for ->_LM<N>` on 100 of 100 (e.g. `PRE_RURAL_LM1`) | 180 of 180 | 26 of 89 (63 use a shortened stem, e.g. `PRE_CONDOCLTV_LM1` for `PRE-CONDO-CLTV`) | n/a |
| 30 | `indicator_context` wording | "Indicator is 'Pass' when ..." 69; "Do not populate borrower_ids for this unified metric under any circumstance" on 100 of 100 | 103 and 180 of 180; "on mismatch use document-extracted value" 21 | 83 and 88 of 89; "on mismatch..." 12 | n/a |
| 31 | `description_template` with `{placeholder}` | 100 of 100 | 180 of 180 | 89 of 89 | n/a |
| 32 | `calculation_context` | on 21 metrics | 10 | 12 | n/a |
| 33 | `entity_types` | 2 per job median, max 5 | same | same | none |
| 34 | `entity_types` names | LoanCore 68, Borrower 55, SubjectProperty 34, CreditReport 29, RatioSet 27 ... 15 distinct | 14 distinct (no `CondoProject`) | 14 distinct | n/a |
| 35 | `entity_description` text | one fixed text per entity across all jobs, and the text is DSCR-specific ("RatioSet: Qualifying ratios: DSCR inputs, PITIA, reserves in months, DTI (not used for DSCR)") | same | same | n/a |
| 36 | `extraction_targets` | 52 entries (47 ASK_USER, 5 AUTO_APPROVE; UPDATE 39, CREATE+UPDATE 13) | 14 (10 / 4) | 57 (53 / 4) | on 71 of 114 and 57 of 81 jobs, mode ASK_USER, operation UPDATE |
| 37 | `notes` | on 20 jobs; 18 say "Ontology gap" | 35; 28 | 24; 13 | none |
| 38 | `document_types`, `condition_mappings` | none | none | none | none |

### A4. Coverage and structure

| # | Dimension | theirs | ours | Evidence |
|---|---|---|---|---|
| 39 | Clauses covered (Standard 123, Platinum 94 numbered) | 119 and 92 | 105 and 82 | my workbook, sheet 2; one reader. Nothing of ours is unmatched to a clause. |
| 40 | Gaps in ours (no job) | | ARM terms, state prepayment restrictions, One- to Four-Family Rider, REO listing scope, Business Purpose Attestation, cash-in-hand footnotes (both programs); HELOC CLTV and excessive lease rent (Standard); previous credit events and the Condo and Two-Unit 75% cap (Platinum) | workbook "Gaps in ours" |
| 41 | Aggregate "governing" jobs | present in v9 (7 jobs matching governing, lowest, consolidated, aggregate), v17 (6), v7 (3) | 1 (Std), 2 (Plat) | keyword count over skill and title, so an upper bound for both sides |
| 42 | Granularity | entity documents: 9 jobs vs our 1 (Standard 6.10, Platinum 5.10); matrix tiers 4 vs 1; listed-for-sale loan conditions on Standard split finer | listed-for-sale on Platinum 12 vs 5; per-check overlays (escrow waiver, 1 or no score, reserve triggers) | workbook sheet 3 |
| 43 | Near-duplicate checks | 12 of 124 (Standard), 4 of 108 (Platinum); v7 has 8 repeated titles | 17 of 114, 14 of 81 | workbook sheet 6; v9 and v17 have no repeated titles |
| 44 | Filled vs referred figures | fills some the guideline leaves open (interest-only minimums $100,000 and FICO 700; "no ratio" fails the file; DTI alternative dropped) | refers each to the guideline's open question (Q-09, Q-12, Q-14) | `readings_for_decision_regen5.md` (8 readings) |
| 45 | Program overlays | none: every FNMA, FHLMC, FHA and VA block is `NO_CHANGE` | none: every Standard and Platinum block is `NO_CHANGE`, and the two programs are separate sets with a `program` key per job | A2 row 14 |
| 46 | Extra keys | none beyond the schema | `rule_id` and `program` on every job | export keying (`ee9f8015`) |

### A5. What changed between their v9 and v17 (the best evidence of what people or the tool edited)

v17 is a regeneration, not a patch of v9: of 124 jobs, 4 mnemonics and 8 skill texts are shared with v9, and the best title-and-skill token overlap of a v17 job with any v9 job has a median of 0.42 (43 of 124 at 0.5 or above, 96 at 0.3 or above; 91 distinct v9 jobs are the closest match of at least one v17 job, 4 of them for two or more). Changes that can be counted:

| Dimension | v9 | v17 |
|---|---|---|
| Prefix families | 12 | 21; only 5 prefixes are in both (AFC, CMP, CRD, DSCR, RLI) |
| Slug median | 9 | 7 |
| Jobs per section | Ident 20, Compliance 19 | Ident 11, Compliance 25 (the v9 `FN` jobs sit in Identification; in v17 the `FNC` and `FNP` jobs are mostly in Compliance) |
| `loan_metrics` | 100 | 180 |
| `extraction_targets` | 52 | 14 |
| `notes` ("Ontology gap") | 20 (18) | 35 (28) |
| COMMON length median | 1,812 | 2,790 |
| Mentions of the LOS transmittal "1008" | 35 jobs | 0 |
| Jobs citing another job's mnemonic in text | 66 | 26 |
| Section sign refs | 74 | 14 |
| `---` separators | 0 | 124 |
| `CondoProject` in `entity_types` | yes | no; a v17 note says "the CondoProject entity is not part of the Knowledge Hub ontology", while the workbench `mortgage_ontology_v2.json` does contain it |
| Officer-assigned jobs | 5 | 10 |

## B. Provenance of each convention in theirs

The label says which source states or implies the convention; the quote is the evidence.

| Convention (theirs) | Provenance | Evidence | Reliability |
|---|---|---|---|
| Closed list of 8 section names | GUIDE | Guide "Section family" table (lines 71 to 85) lists 11 names; Acra uses 8 of them verbatim (7 in Platinum). `mpr/patterns.py:23-36` `SECTION_TYPE_TO_SECTION` is the same closed mapping. | complete |
| `section_type` from a standard list; Appraisal Review is `Collateral` | GUIDE, EXPORT | Schema enum lists `Collateral` and has no `Appraisal`; the guide's table says `Appraisal`; `SECTION_TYPE_TO_SECTION` maps both to Appraisal Review; the writer prompt example says "folder `Appraisal Review`, `<section_type>Collateral</section_type>`" (writer line 29). | complete |
| `source: NEW` | GUIDE, WRITER | Guide line 87; writer line 52 "`NEW` for all agent-created JTBDs". | complete |
| Assistants Underwriter / Processor / Officer | GUIDE | Guide lines 90 to 96; schema enum. | complete |
| Investor columns COMMON, FNMA, FHLMC, FHA, VA, all non-COMMON `NO_CHANGE` | GUIDE, WRITER, EXPORT | Guide line 39 ("The program blocks are `COMMON`, `FNMA`, `FHLMC`, `FHA`, and `VA`"); writer line 151 ("Every program column ... MUST be present ... write the literal body `NO_CHANGE`"); `INVESTOR_ORDER` in `patterns.py:8`. The writer today also lists `USDA`; Acra's sets have no USDA block, so they come from a version of the prompts (or a tool) before USDA was added; which is unknown. | complete for the fact; version UNKNOWN |
| `# <Skill Name> - Base Version`, Purpose, Reference Documents, 4 steps, DVR, Outcomes with four categories | GUIDE, WRITER | Guide lines 113 to 143; writer lines 177 to 259 (the `COMMON` template, including the `---` separators between sections and "There is no case for this outcome"). | complete |
| `TRUE = pass, FALSE = fail` rule syntax | GUIDE, WRITER | Guide line 133; writer "Reserve explicit boolean TRUE/FALSE predicate formatting for program-specific overlay columns" yet Acra puts it in COMMON on every job (124 of 124 in v17): so Acra follows the guide's template, not the writer's narrower NOTE. | complete |
| Step bullets that name a document and a field ("AppraisalSummary record identifies ..." in v17) | WRITER | Writer line 218: "Each bullet must name (1) the specific document or data source ... (2) the specific field". More visible in v17 than v9. | one reader, sampled |
| Rules self-contained, no cross-references | WRITER | Writer line 227: "Never write rules of the form 'satisfies the predicate defined in [column/section X]'". v9 cites other jobs by mnemonic on 66 jobs; v17 on 26; v7 on 8. Consistent with the prompts being enforced harder over time, or with an Acra cleanup; which is UNKNOWN. | complete counts, cause UNKNOWN |
| `---` separators | WRITER (template), ACRA (v9 omits them) | Writer template shows `---` between sections; v17 has it on 124 of 124, v9 on 0. | complete |
| Mnemonic is `<PREFIX>-<SUFFIX>`, taken from the file name | GUIDE, EXPORT | Guide lines 98 to 111; `mpr/jtbd_resolver.py:26-39`: "The filename stem IS the mnemonic ('APR-PTY.md' -> ("APR-PTY", 0))". | complete |
| A 3 to 4 letter prefix | GUIDE, WRITER | Guide: "`SECTION_PREFIX` is the 3-4 letter family mnemonic"; writer line 40: "a 3-4 letter abbreviation of the section/domain". | complete |
| Many prefixes per section (topic groups: AFC, BET, BOR, FN, LFC, PPT in v9; 21 in v17) | ACRA (probably) / UNKNOWN | The guide and writer describe one prefix per section family ("reuse an existing mnemonic if the file belongs to that family"). Revolution's legacy set has one prefix per section (12 of 12 sections). Acra's multi-prefix scheme has no source in the pipeline files. Our `jtbd_template.yaml` `families` block was derived from Acra's v9 and v7 prefixes. | complete for the contrast; origin UNKNOWN |
| Slug of 5 to 10 characters | WRITER | Writer line 41: "a 5-10 character abbreviation". v17 median 7 (5 to 12), v9 and v7 median 9 (4 to 15). Revolution's legacy slug median is 3. | complete |
| Uniqueness without a sequence number | GUIDE, WRITER | Guide: "Never invent a sequence number to disambiguate"; writer line 42 repeats it. Acra's mnemonics are unique in all three sets. | complete |
| `sequence` 1..n per section, contiguous | EXPORT | `jtbd_resolver.py:26-31`: "the real sequence number lives in the backend (`jtbd_sequences`) and is overlaid at export time"; the schema requires `sequence` (minimum 1). So the number is assigned by the tool, not authored. | complete |
| `loan_metrics` blocks, XML sub-tags, `metric_key` from the ontology paths | GUIDE, WRITER | Guide lines 145 to 212; writer lines 262 to 288. Filtered (`Asset[borrower_type=Primary].current_balance_usd`) and nested (`LoanCore.down_payment.total_amount_usd`) are in the guide's three formats; Acra uses both (filtered on 18 metrics across the sets, nested on 3). | complete |
| `metric_mnemonic` = `<JTBD mnemonic>_LM<N>` | GUIDE | Guide line 207: "convention: `{JTBD_MNEMONIC}_LM{N}`, max 50 chars"; schema says the same and "unique across the entire JTBD set". 100 of 100 in v9 and 180 of 180 in v17; v7 shortens the stem on 63 of 89. | complete |
| `indicator_context` text | GUIDE | The sentences "Indicator is 'Pass' when ...; 'Fail' otherwise. Cross-verify with ...; on mismatch use document-extracted value. Do not populate borrower_ids for this unified metric under any circumstance." are the guide's own example (guide line 195). The last sentence is on 100 of 100 (v9), 180 of 180 (v17), 88 of 89 (v7). | complete |
| `description_template` `{placeholder}` | GUIDE | Guide line 196 | complete |
| `entity_types` list restricted to 14 names | WRITER | Planner line 105, creator line 242, modifier line 220 list the same 14; Acra also uses `ClosingFee`, `CondoProject`, `MortgageLoanInformation`, `RateLockAgreement`, `RealEstateOwned`, which are in `mortgage_ontology_v2.json` but not in the 14 (so the prompt list lags the ontology, or the author drew from the ontology). | complete |
| One fixed `entity_description` per entity, with DSCR wording | ACRA / K-STUDIO / UNKNOWN | The schema only says "Loan entity reference mapping to Vesta API schema"; the ontology v2 descriptions are different (e.g. SubjectProperty "Subject property being financed"). The DSCR-specific text appears nowhere in the workbench files searched. | complete search of workbench `*.py`, `*.md`, `*.json`; origin UNKNOWN |
| `extraction_targets` | EXPORT (parser), origin UNKNOWN | `patterns.py:42-58` parses `<extraction_targets>` blocks; the writer, planner and creator prompts do not tell the author to write them. Counts swing 52 to 14 between v9 and v17. | writer silent; who adds them UNKNOWN |
| `notes` ("Ontology gap ...") | ACRA / the generating model, UNKNOWN | The schema allows a free `notes` string for "SMEs and developers"; the writer is silent. 59 of the 79 notes across the sets contain an "Ontology gap" statement and 36 contain a recommendation. | complete counts, origin UNKNOWN |
| The "Q-nn" confirmations cited in text | ACRA's guideline | The guideline itself prints "Acra confirmation requested -> Q-nn"; theirs cites them on 63 (v9) and 43 (v17) jobs, ours on 8 and 5. | complete counts |
| "Improved" in the titles and description | UNKNOWN | "Improved" is on all three titles or descriptions. No source file explains it. It may be a K-STUDIO action name or an Acra label. | UNKNOWN |
| `1008` ("LOS transmittal (1008)") in v9 on 35 jobs, 0 in v17 and v7 | home-mortgage vocabulary | Form 1008 is the agency transmittal; an investor-property DSCR program has no use for it. It disappears in later versions. | complete counts, reading of meaning is mine |
| Platinum v7 built on Standard v9 identities | ACRA process | 71 shared mnemonics, same section on 69, same `loan_metrics` keys on 57, text different on all 71. The method (copy then regenerate? modifier flow?) is UNKNOWN. | complete counts |

## C. Can it be derived algorithmically?

Each row gives the rule in two lines and how to test it on their sets. "Human" means a judgment a rule cannot make from the text.

| Convention | Derivable? | Rule | Test on their sets |
|---|---|---|---|
| Section from the closed list | Yes | Map each unit to a section by its guideline heading or a classifier over the closed list (`section_types` already maps section to `section_type`); fall back to the nearest listed name. | Take the clause headings of the guideline, derive a section per matched clause, and compare with their section per job. My workbook has 53 of 80 (Platinum) and 70 of 104 (Standard) agreeing, which is the floor for a naive rule; the rest is the entity-clause and foreign-national placement, which is Acra's choice (human). |
| `section_type` from section | Yes | Fixed table (guide), `SECTION_TYPE_TO_SECTION` inverse. | 124 of 124 and 108 of 108 in v17 and v7 already follow it (Collateral for Appraisal Review). |
| Prefix = acronym of a topic group | Partly | Initials of the significant words of the group name, 3 to 4 letters, unique across the pack (sonnet-runtime's note, part 2). | Their group names are not in the files, so the test is indirect: for the prefixes whose meaning I can read (`AFC` assets and funds to close, `BET` borrowing entity and title, `RLI` rent loss insurance, `LPE` loan program eligibility), check the acronym; for the others (`PET`, `PVL`, `LAC`, `LAL`, `PIO`, `BWE`, `PGE`, `DRT`, `DSR`) no group label exists to test against. Reading the 21 v17 groups by title, a group is a 4 to 13 job cluster of one topic; membership is a clustering judgment, not a function of the text. |
| Slug = compressed key phrase | Partly | A key phrase of 5 to 9 characters from the job name (consonants or initials), unique within the prefix; a model proposes, the SDK checks length and uniqueness. | v17 slugs are 5 to 12 characters (median 7); check what share are a prefix of, or an initial-letter abbreviation of, the job's title words. Not run. |
| Sequence | Yes (as a number), human (as an order) | Assign 1..n per section in the order the guideline presents the clauses a job checks. | Take the first matched clause of each job in a section and correlate with `sequence` (Spearman). I started it from the Platinum clause links and linked only 3 of 108 jobs by mnemonic, so it is untested; it needs the clause-to-job map re-keyed by mnemonic. |
| Requirement template (title, 4 steps, DVR, outcomes) | Yes | A fixed renderer from structured fields (purpose, steps, checks, outcomes); the model fills the fields. | 100% of their jobs match the headings except the minor `---` separator rule; a parser check of heading order passes or fails per job. Ours fails the heading form on all 195 jobs (A2 rows 18 to 21). |
| TRUE/FALSE rule syntax | Yes | Render each check as `<condition>: TRUE = pass, FALSE = fail` from the structured check. | Parse their DVR bullets: the share with the `TRUE =` form is 124 of 124 (v17). |
| `loan_metrics` | Mostly | Metrics are the facts a job's checks read: `metric_key` is the check's `Entity.field`, `metric_mnemonic` is `<mnemonic>_LM<N>`, `description_template` has a `{field}` per key; `indicator_context` from a fixed sentence plus the threshold. | For each v17 job compare `metric_key` with the case fields in its DVR and the `Entity.field` tokens in its text. The label, the threshold phrase and `calculation_context` stay model or human. |
| `entity_types` | Yes | The distinct entities of the job's `reads` and `metric_keys`, each with a fixed per-pack description. | Compare each job's `entity_types` with the entities of its metrics: 1 of 89 metrics in v7, 0 of 100 and 0 of 180 in v9 and v17 name an entity missing from the job's list. |
| `extraction_targets` | Yes in shape | One target per entity the job's documents yield; mode and operations from a pack default. | Compare to their 52 / 14 / 57 entries; the swing between versions says their rule is not stable (unknown). |
| Investor blocks | Yes | A profile maps program to block; absent overlays render `NO_CHANGE`. | Already so (every non-COMMON block `NO_CHANGE`). |
| Cap and footnote completeness (every printed figure decided by some job) | Yes | Extract every figure, cap and footnote of a clause, map each to a check, and report unmapped ones (sonnet-runtime has `figure_lint.py`). | Run the lint on their v17 and on our regen-5; the count of unmapped figures is the measure. I read 8 gaps in ours by hand; the lint has not been run. |
| Aggregate "governing cap" jobs | No, partly human | Where a clause gives several caps and says which governs, one job with `min`; where it is silent the choice is the user's reading (my readings 3 and 8). | List their jobs matching governing and aggregate wording (6 in v17) and check whether each rests on a clause statement or an author's choice. |
| Granularity (entity documents 9 vs 1; matrix tiers 4 vs 1) | Partly | Split a matrix into one job per tier and a document list into one job per document when the clause lists them as separate rows. | Count rows in each clause table against jobs; theirs split finer on entity documents and matrix tiers. Where to split is a design choice (human), the count of rows is not. |
| `notes` ("Ontology gap ...") | Yes | Emit when a check has no `Entity.field` in the ontology; text from the check. | 59 of the notes across the sets say so; compare with the checks that have no metric. |

## D. Home-mortgage side versus Acra specific, for CRE

**What the home-mortgage side plausibly defines (Acra inherited it):**
- the JTBD schema and its field set (`sequence`, `mnemonic`, `section`, `section_type`, `skill`, `source`, `assistant`, `requirements`, `entity_types`, `loan_metrics`, `extraction_targets`, `notes`, `condition_mappings`, `document_types`);
- the 11 section families and the section to `section_type` table;
- the investor columns FNMA, FHLMC, FHA, VA (and USDA in later prompts) with `NO_CHANGE`; for Acra these are always empty, so 4 of 5 columns carry no information;
- the COMMON template (four steps, TRUE/FALSE rules, four outcomes, "There is no case for this outcome");
- the metric block (key formats, `_LM<N>` mnemonic, the `indicator_context` sentences, the `borrower_ids` line);
- a prefix per section (Revolution's legacy set: 12 prefixes for 12 sections, slugs of 3 letters);
- `source` BASELINE, EXTENDED and NEW, and the three assistant personas;
- home-mortgage vocabulary: the LOS transmittal 1008, DU, LP, AUS, Closing Disclosure and QM/ATR in the prompts and ontology (1008 on 35 v9 jobs; none of ours).

**What is Acra or commercial-lending specific:**
- the program split (Standard and Platinum Select) as two sets; the home-mortgage side has one set with investor columns, so Acra reuses it as one set per program;
- the topic-group prefixes (12 in v9, 21 in v17) and the `entity_description` text about DSCR, PITIA and prepayment;
- the guideline's open questions (Q-01 to Q-19) cited in text, and the decision to fill or refer them;
- DSCR, entity borrowers, foreign nationals, guarantors, prepayment penalties and rent-loss insurance as topics (the sections they land in differ between v9 and v17);
- `RatioSet`, `CondoProject` and `MortgageLoanInformation` entities used for DSCR inputs.

**For CRE.** Keep the schema, section list, template and metric block conventions (all derivable from structured fields); do not inherit the investor columns (use program or product variants, which our template already does); expect a topic-group prefix scheme to be a design decision of the customer, not a derivation, and derive only its acronym and uniqueness. `loan_metrics`, `entity_types` and `extraction_targets` are derivable from the checks' fields once a CRE entity schema exists; the CRE ontology gap notes are the first thing a CRE run would produce.

## E. Findings in order of importance

1. v17 is a regeneration of v9, not an edit: 4 of 124 mnemonics and 8 skill texts are shared. Their identities are not stable across versions, which is also why equivalence has to be judged by what a job checks.
2. v7 (Platinum) was built on v9's identities: 71 of 108 mnemonics shared, 69 in the same section, 0 with the same COMMON text.
3. Almost every structural convention of theirs is in the workbench guide or writer prompt: sections, section_type, investor columns, template, metric blocks. Only the prefix families, the DSCR entity descriptions and the figure choices have no source.
4. The `indicator_context` sentences and the `borrower_ids` line are the guide's own example, on 100 of 100 (v9) and 180 of 180 (v17) metrics.
5. `sequence` is assigned by the workbench export (DB table), not authored; it needs no model and ours omits a required field.
6. Their prefix scheme departs from the guide (one prefix per section): 12 prefixes in v9, 21 in v17. Revolution's legacy set has one per section. The scheme has no source in the pipeline files.
7. The format differences in ours (step headings, rule syntax, outcome bullets, title, no metrics, no entity types, three blocks, no sequence) are template and export choices, not model effects; v17 follows the writer template more closely than v9 does (`---` on 124 of 124 against 0, fewer cross-references).
8. The substantive gaps in ours are coverage: no job on 11 published items; 17 and 14 near-duplicate pairs; 18 referral jobs where theirs fill or encode a conditional outcome.
9. Their `extraction_targets` swing from 52 to 14 between v9 and v17 and the writer prompt never asks for them, so we cannot say what rule produces them.
10. The unknowns that matter: who wrote the topic-group prefixes, the entity descriptions, the notes and the `extraction_targets`, and what "Improved" means in the titles. Acra's team or the Knowledge Studio tool can answer these in one question each.

## F. What this asks of others

Nothing is built here. For sonnet-runtime: the identity rules (prefix acronym, slug length and uniqueness, sequence by guideline order) and the renderer that emits the guide's template, TRUE/FALSE syntax, metric blocks and entity types are the derivable parts; they belong in the export and `jtbdset.py`, and each can be tested on their three sets as in section C. For the user, if worth asking Acra: who authored the topic-group prefixes and the `entity_description` text, whether `extraction_targets` come from the tool, and what produced v17 from v9.
