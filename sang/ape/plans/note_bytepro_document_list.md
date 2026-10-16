# Note: BytePro document list (Acra LoS), assessment for the pack's document registry

Author: opus-xrepo, 2026-10-16. Source: `docs/BytePro Consumer & Commercial Document List (7.29.2026).xlsx`.

## What the list is
- Two sheets, Consumer (455 rows) and Commercial (463), columns Category, Name, Code, Only One Approved. Acra's
  DSCR business loans sit in Commercial (Consumer differs by 8 documents out; Commercial adds 16: Commercial
  Application, Schedule of Real Estate Owned, Multi-Family Rent Roll, Scope of Work - ARV, the ENTITY set, EIN
  Verification, Referral Agreement/Invoice, Feasibility Report).
- This is the LoS's document-type catalog: the labels an uploader or a processor picks, and the codes the LoS
  stores. It is not a guideline: it says nothing about when a document is needed.
- Categories (Commercial): SERV 206 (servicing, default, foreclosure: out of scope for origination), LENDER 46,
  PROP 42, DISC 35 (disclosures), INC 21, DOCS 17, CRED 16, MISC 15, BROKER 14, T&I 13, ASSET 12, TITLE 11,
  ENTITY 10, APP 4, QC 1. About 257 rows are origination-relevant, 206 are servicing.
- "Only One Approved" (X, 46 rows) means at most one accepted instance per loan: Final Title Policy, Approval,
  Appraisal 1/2 - Final, Broker Initial 1003, Income Analysis (UW), Fraud Report, NMLS records, POA acceptance...
- Code is at most 20 characters, truncated (96 rows are exactly 20), so it is a LoS key and not a readable id. It
  must be kept verbatim to round-trip with BytePro.
- Noise a classifier must not learn from: variants of one document (Appraisal 1 PDF / XML / Final, Closing
  Package Scanned / Signed), invoices and checklists (Appraisal Invoice, Insurance Checklist), internal records
  (Funder Balancing Statement INTERNAL USE ONLY), a few state-specific documents (CA, TX, IL), and categories that
  differ between sheets (Articles of Incorp/Org APP vs ENTITY).

## Against the pack today
- The Acra seed registry has 15 types (loan_application, bank_statement, ...); the jobs name only 11 evidence
  types, all coarse (Entity documents 37 jobs, Bank statement 42, Credit report 32, Appraisal report 30, ...).
- BytePro is much finer: Entity documents alone is 10+ BytePro types (Operating Agreement, Certificate of Good
  Standing, EIN Number, Articles, Corporate Resolution, Trust Documents...); Appraisal is about 19 (Appraisal,
  1007/rent schedule, AVM, SSR, UCDP summary, collateral review...); Credit about 18; Insurance 12; Title 14.
- Fuzzy name matching of the 11 job-referenced names to BytePro found good matches for Lease Agreement (exact),
  Bank Statement (Assets), Hazard Insurance Policy, Preliminary Title Report/Commitment, Credit Report; "Listing
  history" and "Rent roll" have no real BytePro twin (the best hit was wrong), so those need a human map.
- DocumentType has: id, label, aliases, parent (category), kind, cues, yields, valid_for_days, sensitive, retired,
  replaced_by, x-source. It has no LoS code, no single-instance flag and no loan-type scope, and unknown keys are
  dropped silently (`DocumentType` has no `extra="forbid"`).

## How jaci should send it (proposal)
1. Reference library, not hand-copied YAML: load the two sheets as one reference (versioned `bytepro@2026-07-29`,
   Commercial and Consumer as `applies_to` scopes) and adopt entries into the pack's `document_types.yaml` with
   `x-source: bytepro@...#<code>`, the way catalog fields are adopted. Never edit the list by hand in the pack.
2. Adopt only origination-relevant categories by default; SERV, most DISC, QC stay in the reference and are
   offered but not adopted (they only add classifier classes that no rule reads).
3. Per adopted entry the pack carries: id (stable slug), label = BytePro name, `aliases` = BytePro name, the
   code (new field `los_code`), parent = BytePro category mapped to the pack's tree, kind, cues, yields.
4. Mapping layer: one of our coarse evidence types may map to many BytePro types (evidence type `entity_documents`
   -> 10 BytePro entity types). Two directions are needed: classifier output (fine BytePro type) to evidence type
   (what a job requests), and evidence type to the BytePro types that satisfy it (what a request tells the
   processor to upload). Today only the first exists as `parent`.
5. `Only One Approved` becomes `single_instance: true`: a second document of that type is a conflict to surface,
   and a "latest one wins" rule for the evidence picker.
6. Output side: every job's reference documents should print the BytePro name and code so the processor requests
   exactly what the LoS calls it (condition letters, document requests).

## What to mine
- A bundle gap list: jobs name documents BytePro has no type for (Listing history, Rent roll as a single type,
  Entity documents as a set), and BytePro types no job reads (candidates for missed requirements, e.g. Property
  Operating Statement, HOA Litigation, Flood Certification, Schedule of Real Estate Owned, Satisfaction of
  Mortgage, Notice of Lien).
- A checklist per loan type: Commercial vs Consumer differences (ENTITY set, Commercial Application, SREO,
  Multi-Family Rent Roll) tell which documents a DSCR/entity loan carries that a consumer loan does not.
- Cues for the classifier: names and categories are the only text; real cues need sample documents.
- Single-instance documents imply conflict checks (two Final appraisals, two 1003s).

## Needs from sonnet-runtime / sonnet-ui (plan first)
- `los_code`, `single_instance`, `applies_to` (loan type) on DocumentType and in the registry lint (and out of the
  silent-drop path), reference-library kind for document catalogs, adopt route like `catalog_adopt`, and the
  two-way evidence type mapping.
- Plato page: browse the reference, adopt, show unmapped job documents.

## Needs from the user
- Confirm Commercial is the sheet for Acra's DSCR loans; which categories Acra's processors actually use at
  intake; the right BytePro type for "Listing history", "Rent roll" and the evidence-type groupings.
