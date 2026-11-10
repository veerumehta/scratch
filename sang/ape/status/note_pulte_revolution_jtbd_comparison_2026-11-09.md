# Pulte and Revolution JTBD sets compared (read-only analysis, 2026-11-09)

Question: how different are the two lenders' JTBD sets, and what would a shared base pack plus a thin
per-lender overlay hold? Read: the JTBD and policy definition files only (no loan folder, SME workbook,
GT.csv or calibration table). Counts come from a throwaway script over the JSON and YAML; nothing in jaci
or kernel-lab was edited.

## The three artifacts, and where Pulte's set lives

| Artifact | Where | Size |
|---|---|---|
| Pulte 6.2.3 | `kernel-lab/codec-suite/workflows/customers/pulte/jtbds.json` (version 6.2.3, 115 jobs). `customer.toml` also names `pulte-6-2-jtbds.json` as the *reference* (worked examples for generation, release `codec-pulte-6-2-v1.6.0`); that file is `kernel-lab/codec-core/workflows/pulte-6-2-jtbds.json` and is version **6.2.0**, also 115 jobs. | 115 jobs, 11 sections |
| Revolution v6.7 | `customers/revolution/jtbds.json` (version 6.7.0, title "Revolution JTBD V6.7") | 183 jobs, 12 sections |
| jaci Pulte pack | `jaci/config/packs/pulte_home_mortgage_policy` 0.2.2 draft, 15 policy files; blueprint `pulte-home-mortgage` 0.1.0 (policy `>=0.1`, assistant `pulte-home-mortgage-core` `>=1.2`, guideline set `fannie-mae-selling-guide`) | 115 base jobs plus 177 program overlay rules |

Both CODEC files share one schema per job: `mnemonic`, `section`, `section_type`, `skill` (the job's name),
`source` (BASELINE, NEW, EXTENDED), `assistant`, `requirements` (one text per investor: COMMON, FNMA,
FHLMC, FHA, VA, and USDA for Revolution), `loan_metrics`.

## Correction: the jaci Pulte pack is the same lineage as CODEC's set

It is not independent. The 15 files are a conversion of CODEC's Pulte JTBDs, with the Fannie Selling Guide attached afterwards as
coverage and citations:
- The 11 institution-scope policies hold 115 rules whose `rule_id` is the Pulte mnemonic. The set of ids equals
  the 6.2.3 set and the 6.2.0 set exactly (they have the same 115 mnemonics), and the policy names and counts per section
  match 6.2.3 (13, 15, 12, 8, 4, 20, 11, 8, 6, 3, 15).
- Each rule is a `procedure` condition, so the job text is carried as the steps; `domain_extensions.jtbd` keeps the `sequence`,
  `section_type`, `source`, `assistant` and `loan_metrics` fields of the CODEC job.
- The 4 product-scope policies (`JTBD_PROGRAM_FNMA` 9, `FHLMC` 53, `FHA` 58, `VA` 57 = 177 rules) are the per-investor
  texts of the same jobs, named `<mnemonic>.<PROGRAM>` with `overlays: <mnemonic>`.
  Only the investor texts that say something are kept (9 of 115 jobs for FNMA, which is why FNMA is thin).
- `coverage/pulte_jtbd_guide_mapping.yaml` says so itself: "Mapping data for adopting Pulte's existing JTBD set", and one
  status reads "cortex-to-jtbds lineage: the job IS the graph rule".
- Text check: after normalizing whitespace, 47 of 115 jaci `steps` equal the 6.2.3 COMMON text (44 equal 6.2.0). The rest differ,
  most likely because jaci splits a job into `purpose`, `steps`, `checks`, `outcomes` instead of one text blob. I did not
  diagnose the other 68, so I cannot say which CODEC release it was cut from, only that the ids and sections match both.
- Git: pack added 2026-10-30 ("Add the Pulte home mortgage policy and assistant packs"), 0.2.2 on 2026-11-01.

So "the SDK has no Pulte JTBDs" is right for japes itself, but jaci holds them, and they are CODEC's 115. The brief's
"written from the Fannie Mae Selling Guide" is only half true: the jobs come from CODEC, the guide is the coverage target.

## Pulte 6.2.3 against Revolution v6.7

- By mnemonic: **107 shared** (93% of Pulte's 115), **8 Pulte-only**, **76 Revolution-only**. Every shared mnemonic is in the
  same section, and 106 of 107 have the identical `skill` name (the one exception differs in wording only).
- By requirement text: **0 of 107** shared jobs have equal COMMON text after whitespace normalization. A cheap similarity upper bound
  averages 0.85 for COMMON and 0.88 for FNMA, 0.78 FHLMC, 0.74 VA and only **0.44 for FHA**. So the
  shared jobs have the same intent and structure, but each lender's text was rewritten, and Revolution rewrote FHA most.
- So Revolution v6.7 is a **superset by job id, and a different (deeper) branching of the same base**, not an independent set.
  The base is the same 107 jobs; the 76 additions are structure for what Revolution originates.

Sections:

| Section | Pulte | Revolution | Revolution-only jobs |
|---|---|---|---|
| Compliance and Closing | 12 | 37 | 27 (FHA/VA/USDA forms and certifications, HMDA, OFAC, TRID LE, RTC, NJ commitment, escrow waiver) |
| Appraisal Review | 13 | 34 | 21 (UAD 2.6/3.6, waiver/ACE, recert, septic, well, termite, MPR, tiering, FHA anti-flip) |
| Loan Program Eligibility | 6 | 18 | 12 (FHA 203k, FHA ARM, VA cash-out, VA IRRRL, USDA, investment property, buydown, community property) |
| Credit Review and Analysis | 8 | 12 | 8, and Pulte has 4 that Revolution lacks |
| Income Stability and Sufficiency | 20 | 23 | 3 (trust income, new employees, USDA income limit) |
| Insurance Coverage | 11 | 13 | 2 (FHA MIP, UFMIP) |
| Condo Project Review | 0 | 3 | 3 (a new section) |
| Liabilities | 8 | 6 | 0, and Pulte has 2 that Revolution lacks |
| Asset, Title, Identification, Property Tax | 15, 15, 4, 3 | same | 0 |

Pulte-only (8): `COM-ATR`, `COM-FRAUD`, `CRD-AU`, `CRD-CPIR`, `CRD-DCAM`, `CRD-REP`, `LIA-REO`, `LIA-SECASSET`.
At least two look renamed rather than dropped (`COM-FRAUD` and Revolution's `COM-FRD`; `CRD-AU` and `CRD-DUF`, AUS findings);
I did not check the other six against Revolution's text.

Programs: both carry the same four investor texts (COMMON, FNMA, FHLMC, FHA, VA) on every job; Revolution adds **USDA** on all 183.
Revolution's extra jobs are overwhelmingly **government-program** depth (FHA, VA, USDA) plus conventional appraisal and compliance mechanics.
Pulte's own set says it "originates conventional (Fannie Mae) with Pulte overlays", so its FHA and VA texts are thin by design.
Metrics: 173 metric keys in Pulte, 177 in Revolution, 152 shared.

## Lender policy against guide content

The JTBD text itself does not separate them: both lenders write lender practice into the same requirement text.
- Pulte: 36 of 115 jobs mention Pulte, with sections such as "Pulte practice (SME answers and Pulte's file decisions, ...)" and "Pulte overlays".
- Revolution: 58 of 183 mention Revolution, e.g. "Revolution overlay", "Revolution Mortgage approved AMC list", "Revolution Mortgage Production Help Desk",
  the 210-day seasoning rule, the credit-score stance ("No minimum credit score is set by rule").
- Neither set mentions the other lender (0 hits), so no cross-contamination to clean up.
- Reading it: guide content = the shared mnemonics, steps and agency rules (Fannie, Freddie, FHA, VA, USDA requirements);
  lender policy = the overlay passages, approved lists, thresholds, who performs a step, and which jobs exist at all (the 76 and the 8).
  The split above is my reading of headings and phrases, not a measured classification; some "lender" differences (FHA depth) may be
  guide content one lender chose to write out and the other did not.

## What a shared base plus thin overlay would hold

- **Base (shared domain pack):** the 107 shared jobs as the common base, with the guide-derived program texts (FNMA, FHLMC, FHA, VA, USDA) as
  product-scope overlays, exactly the shape jaci's pack already has. Plus the shared metrics (152 keys), the catalog schema, the guide
  coverage files, the investor and document vocabulary.
- **Per lender (kept lender-specific):** the lender-practice passages now inlined in the job texts (Pulte's 36, Revolution's 58), approved lists and
  thresholds, the job-existence differences (Pulte's 8, Revolution's 76, and the new Condo Project section), the FHA/VA/USDA depth that only Revolution
  originates, lender names and document forms.
- **The cost:** the work is untangling, not just packaging. Because no shared job has identical text, the lender passages must be
  extracted out of 107 jobs in each set before the base is truly shared; until then the base is "same ids, two texts".
  Revolution's 76 extra jobs, being government-program and compliance depth, could instead be a second shared
  pack (government programs) that Pulte simply does not include, which fits their count better than treating them as Revolution-only.

## How the SDK's blueprint expresses it

The blueprint chain (`jazzx_sdk/pack/blueprint_chain.py`) is **not** the mechanism for this content split. It narrows authority, not policy: each layer
(domain pack `authority_matrix`, `surface_bindings`, `client_overlay`, `execution_profile`) may only narrow autonomy levels, with `human_only` forcing L0.
A client overlay there can say "Revolution requires a human on X", but cannot add or reword a job.

The pieces that do carry the content split already exist:
- A blueprint has an optional **`core`** role ("a shared domain pack the policy builds on"), a `policy` role (the client's pack), `assistant`
  and `reference`. A shared base pack as `core` plus a thin per-lender `policy` pack fits it; `guideline_set` is shared.
- Inside a pack, policy `scope: institution` is core and `scope: product` is a program overlay claimed through the manifest `programs:` map, which is
  how jaci's pack already carries FNMA/FHLMC/FHA/VA. A lender overlay would be product-scope policies, or a separate lender-scope policy file.
- Publishing to its own tenant (as jaci does for Pulte) keeps the two lenders' versions apart.
- Caveat I would check before designing: how `core` and `policy` packs are merged at run and activation time (the blueprint docstring says a blueprint
  "does not compose" its members), and whether a lender pack can override a base job by id. I did not read that code path; I dropped the `core`
  member on the Acra starter earlier for a different reason (no shared pack existed), so nothing in the seeds exercises it.

The chain would then express the lenders' differing autonomy and approval stance (e.g. which jobs are human-only for Revolution), layered on the same base.

## Not checked

Equality of 6 of the Pulte-only jobs against Revolution; the cause of the 68 jaci steps that differ from the CODEC text; any run behavior; the SME
workbook and calibration material (deliberately not opened).
