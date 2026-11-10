# Lender-practice passages in the Pulte and Revolution JTBD sets (slice S0, read-only, 2026-11-09)

Inputs: kernel-lab Pulte 6.2.3 (`customers/pulte/jtbds.json`, 115 jobs) and Revolution v6.7 (`customers/revolution/jtbds.json`, 183 jobs),
job definitions only. jaci's Pulte pack was not scanned separately: its 115 base rules are the same texts as Pulte's
(see `note_pulte_revolution_jtbd_comparison_2026-11-09.md`), so it adds no passages. No loan folder, SME workbook, GT.csv or
calibration table was opened; no model call; nothing edited in jaci or kernel-lab; nothing committed.

Full list (214 rows: lender, job, section, which investor text, unit, call, confidence, effect, reason, 240-character excerpt):
`note_lender_practice_passages_pulte_revolution_2026-11-09.csv`. The calls are made by rules over headings and phrases (below), then
checked by hand on the groups called out here; they are candidates for a lender SME, not a verdict.

## How a job's text is organized (this decides how the split works)

Each job has one text per investor. `COMMON` is the main text (median 10.6K characters in Pulte, 12K in Revolution) and is written for
conventional lending with a Fannie lean (Pulte COMMON: about 460 Fannie/DU mentions, 60 Freddie). The other investor texts are **deltas
on COMMON**: most are a 9-character `NO_CHANGE` stub, and only the ones with real content are program text.

| Investor text | Pulte: jobs with real text, characters | Revolution: jobs with real text, characters |
|---|---|---|
| COMMON | 115, 1.51M | 183, 2.71M |
| FNMA | 8, 7K | 1, 3K |
| FHLMC | 53, 55K | 42, 62K |
| FHA | 56, 57K | 111, 182K |
| VA | 56, 52K | 46, 63K |
| USDA | none | 20, 20K |

Revolution also has 20 jobs that are government-only by name (`COM-FHA-*`, `LPE-FHA-203K`, `LPE-VA-*`, `INS-FHA-*`, `COM-GOV-LP`, `LPE-USDA`,
`INC-USDA-ELIG`, ...); Pulte has 2 (`APR-AVA`, `INC-VA-RES`). Government material also sits inline in COMMON (Revolution COMMON cites HUD 4000.1 160
times and USDA 64 times), so a government base needs extraction from COMMON as well as from the FHA/VA/USDA columns.

## Method

A unit is a heading section whose heading names the lender (the whole section), or else a single paragraph or bullet that names the lender
(Pulte; Revolution or "RM"). Calls:
- **lender, high:** the heading says "<Lender> overlay" or "practice", or the line says "Pulte overlay", "(Pulte, SME F8)", "CONDITION (Pulte)",
  "Pulte requires", "Revolution policy", "RM IU eligibility".
- **lender, medium:** a lender-owned process, system or dated internal document (Help Desk, Encompass, Condo Review Team, approved AMC list, job aids, checklists).
- **lender, low:** the lender is named with no marker.
- **guide (labelled overlay), medium:** an FHA, VA, USDA, FNMA or FHLMC column section under a "(Revolution overlay)" heading that cites the agency handbook.
- **scope boilerplate:** the stock sentence "Pulte originates conventional (Fannie Mae) with Pulte overlays; apply Pulte overlays where stricter" and the "Cross-reference scope note".
  These name the lender but state scope; they are not practice.
Effect (addition, tightening, loosening) is by keyword on the passage and is the weakest column: use it only where the hand-reviewed table below says so.

## Counts

| | Pulte | Revolution |
|---|---|---|
| Jobs naming the lender | 36 | 59 (57 by name, 2 by the abbreviation RM only; the earlier 58 counted a different pattern) |
| Of those, jobs with only the stock scope sentence | 7 (`COM-ATR`, `COM-HOEPA`, `COM-HPML`, `CRD-DERG`, `CRD-REP`, `LIA-IRS`, `LIA-PITIA`) | 0 |
| Jobs with real lender-practice passages | 29 | 59 |
| Units (passages) | 85, of which 16 are stock scope sentences, 69 real | 129 |
| Lender, high / medium / low | 66 / 0 / 3 | 69 / 11 / 11 |
| Guide text under an overlay label | 0 | 37 (33 USDA, 3 FHA, 1 FNMA) |
| Where the unit sits | all 69 in COMMON | 73 COMMON, 34 USDA, 8 FHA, 7 VA, 4 FHLMC, 3 FNMA |

Where Pulte's passages are: income (INC-WAG, INC-BON, INC-SEL, INC-ERA, INC-RNT, INC-SSA, INC-RET, INC-OTH, INC-INI, INC-VER), assets (AST-TYPE, AST-DATP,
AST-EMIP, AST-GIFT, AST-RSLE), eligibility and appraisal (LPE-DTMC, LPE-NBA, LPE-PSRR, LPE-AMLV, APR-IPT, APR-BASE), credit (CRD-BAS, CRD-CPIR), identity
(IDN-DPV), compliance (COM-ECOA, COM-DEC), liabilities (LIA-REO, LIA-SECASSET), insurance (INS-PMI-ELG). Pulte states its marker in three forms: headings ("Pulte
FNMA Overlay", "Pulte practice (SME answers and Pulte's file decisions, October 2026)"), inline "(Pulte, SME F1-F3)" tags, and "CONDITION (Pulte)" lines.
Revolution's are mostly "(Revolution overlay)" headings, dated "Revolution Mortgage Policy, Updated <date>" blocks (appraisal transfer, escrow waiver, 4506-C and
transcripts, family-employed raise, buydown, homeownership education), and Condo Review Team process text.

## Add, tighten or loosen: reviewed cases

The rule being tested is "a lender overlay may only add or tighten". Keyword calls were 22 Pulte and 34 Revolution tightening, with the rest additions, process or
mixed. Hand-reading the 14 passages the keywords called loosening found:

| Job | Lender | Passage | Reading |
|---|---|---|---|
| APR-BASE | Pulte | "Pulte FNMA Overlay: Postponed Improvements ... the cost cap is raised from 10% to 15%" | **Loosening of the Fannie guide.** The overlay's own text says it raises a cap. This is the clearest case the add-or-tighten rule would reject. |
| AST-TYPE | Pulte | "Provisional Retirement Valuation ... replaces the interim cap that applied only until the terms were reviewed" | Replaces an earlier Pulte rule; direction against the guide unclear; needs the SME. |
| INS-PMI-ELG | Pulte | "all MI types are acceptable per Pulte policy" | Likely restates what the guide permits; if the guide allows all types it is neither. |
| INC-FAM | Revolution | "Family-Employed Borrower, Mid-Year Raise: Revolution Mortgage permits the use of the new, higher income, subject to documentation" | Direction against the guide unclear; may be a permission the guide also gives. Needs the SME. |
| APR-META | Revolution | "Conventional Appraisal Transfer Policy: accepts transferred appraisals ... subject to ... a lender-to-lender-to-Revolution chain is NOT eligible" | An added condition set on a permission; a tightening in effect. |
| AST-TYPE | Revolution | "Reps-and-warrants asset overlay: do not condition ... access/sourcing items" | **Loosens conditioning** (drops conditions), though the text says it does not change agency eligibility; the word "overlay" here does not mean tightening. |
| INC-RNT | Revolution | "will no longer permit market rent in lieu of the full lease + Schedule E" | Tightening. |
| COM-EW | Revolution | "escrow waiver NOT PERMITTED at LTV > 90%. NO EXCEPTION" | Tightening (lender threshold on a waiver the guide allows). |
| LPE-BUYDOWN | Revolution | "REJECT borrower-funded buydowns (Revolution overlay, not currently allowed)" | Tightening. |
| LPE-GLPC | Revolution | "Assigned purchase contracts permitted only on Freddie Mac loans delivered via LPA" | Tightening. |

So the add-or-tighten rule will have to be checked passage by passage: at least APR-BASE (Pulte) and the Revolution reps-and-warrants asset text move the
other way, and several are unclear.

## Common to both lenders

- By job: **14 jobs** carry lender passages in both sets (`APR-BASE`, `APR-IPT`, `AST-DATP`, `AST-RSLE`, `AST-TYPE`, `CRD-BAS`, `INC-INI`, `INC-RNT`, `INC-SEL`, `INC-VER`, `INC-WAG`,
  `LPE-AMLV`, `LPE-DTMC`, `LPE-NBA`). The topics are alike but the passages differ: each lender wrote its own overlay on the same job.
- By text: of 144 non-boilerplate excerpts, 11 have 60% or more of their 5-word shingles in the other lender's same-named job. Reading them: 8 are **base text swept into a Pulte unit**
  (a paragraph of guide text that merely sits next to an inline "Pulte FNMA Overlay" heading in the flattened text: LPE-DTMC, LPE-NBA, LPE-PSRR, INC-BON, and the
  matching INC-VER one in Revolution). These are guide content mis-flagged by unit granularity. The other 3 are real lender passages **that both sets share almost word for word**:
  the self-employed conditions in INC-SEL (a business-entity 4506-C, W-2 for officer compensation from an own S-corporation, and business active within 30 days of the note date).
  In Pulte they read "CONDITION (Pulte)" and "PULTE OVERLAY"; with the lender name normalized, the same wording is found in Revolution's INC-SEL. Revolution's text looks derived from
  Pulte's, so this is lender practice that two lenders hold in common, or one lender's text copied; ask the SMEs which.
- Related: the 30-day business-existence window in Revolution's FHA text is called "FHA's OWN AGENCY requirement, not merely the Revolution overlay (Fannie's window is 120 days)".
  A rule that looks like Pulte's practice is in part FHA agency content. Expect more of these where one lender's overlay equals a government agency's rule.

## What would sit in a base of its own

- **Fannie Mae and conventional-wide:** the COMMON text of both sets is the conventional baseline with a Fannie lean, and the FNMA column is nearly empty
  (8 Pulte jobs, 1 Revolution job). So the Fannie base is essentially COMMON minus its lender passages and minus the government material inline in it.
- **Freddie Mac:** the FHLMC column (53 Pulte jobs, 55K characters; 42 Revolution jobs, 62K) is a delta on COMMON that mostly cites the Freddie Guide and LPA. It is a clean candidate for a
  Freddie base overlay, with only a few Revolution lines (4 units, "assigned contracts" and rental specifics) that are lender.
- **Government programs:**
  - FHA: Pulte 57K characters; Revolution 182K (111 jobs), plus the government-only jobs by name listed below. It cites HUD 4000.1 about 40 times in Pulte and 257 in Revolution; almost all is agency content.
  - VA: Pulte 52K (56 jobs), Revolution 63K (46 jobs, 32 citations of the Lenders Handbook and Pamphlet 26-7).
  - USDA: Revolution only, 20K characters in 20 jobs.
  - The 20 Revolution government-only jobs (FHA streamline, 203k, FHA ARM, VA cash-out, VA IRRRL, MIP and UFMIP, GOV lead-paint, USDA income limit, USDA program) would be the
    spine of a government base, and Pulte has none of them.

## Is USDA part of the government family?

Yes by Revolution's own grouping, with one caution. Revolution's jobs group it ("On FHA/VA/USDA purchases", "Condo Review FHA / VA / USDA Process Overlay"), and it shares
CAIVRS and the guarantee model. In the texts, 33 of the 34 USDA sections sit under a "(Revolution overlay)" heading but cite USDA's handbook (HB-1-3555 appears 87 times). That means
**Revolution labels guide-derived program text as an overlay**, so counting "(Revolution overlay)" headings as lender policy would overstate lender content by about 37 units.
Pulte has no USDA text, so a government base would have USDA as a third program next to FHA and VA with only one lender's wording behind it.

## What a lender SME or studio owner must review before any split

1. **The meaning of "overlay".** Confirm per lender whether a "(Lender overlay)" heading means a lender rule or just a program delta (the USDA, FHA and VA sections suggest the latter in Revolution).
2. **The 37 Revolution program sections** called "guide (labelled overlay)": is each the agency rule, or the lender's tightening of it?
3. **The loosening candidates**: APR-BASE (10% to 15% cap), the Revolution reps-and-warrants asset text, and the unclear INC-FAM, AST-TYPE (provisional retirement), INS-PMI-ELG. Decide whether the add-or-tighten
   rule is enforced as a refusal, or the lender must justify these.
4. **The 25 lender calls with low or medium confidence** (3 Pulte, 22 Revolution): the SME should read them first.
5. **The INC-SEL shared conditions**: who owns them (one lender's text copied, or a shared industry practice).
6. **Passages at unit boundaries**: about 8 Pulte units are guide text beside an overlay heading, so the passage must be cut at the heading, not the paragraph, before any extraction.
7. **Pulte's SME-derived practice** ("Pulte practice (SME answers ..., October 2026)", tags SME F1 to F17): these are file-decision rules learned from loans, not written policy;
   the lender owner should say whether they are policy at all.
8. **The 7 Pulte jobs with only the scope sentence**: the sentence "apply overlays where stricter" has no passage behind it; confirm that it is a statement of scope and drop it from the base.
9. **Whether government material inline in COMMON** (Revolution COMMON: 160 HUD 4000.1 citations) belongs to the government base.

## Not done

No passage was re-read against the Selling Guide or the agency handbooks (the guide text is not in these files), so "guide" means "the text cites an agency source", not "verified equal to it".
Add-versus-tighten is keyword-based outside the table above. The jaci pack was not scanned separately.
