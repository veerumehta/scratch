# Plan: Acra classification-and-splitting golden dataset and eval experiment

sonnet-ui, 2026-10-17. Status: PLAN FOR APPROVAL, nothing has been run and no loan file has been opened. Source:
`status/Acra/Updated_Loan_Document_Taxonomy.xlsx` (sheets Classification, Master Taxonomy). Loan files stay in
`status/Acra/Acra Lending/loans/` (ignored); everything generated goes to `status/Acra/Acra Lending/golden/` (ignored),
none of it into the japes tree, a commit, /tmp or chat.

## 1. What the sheet holds (counted, no loan content read)
- Classification: six Parts (Part 1, 2, 3b, 4, 5, 6) of page ranges with a label and a confidence; **112** ranges
  (62 `pp. a-b`, 50 single `p. n`; the brief said 113), **56** distinct labels (the brief said 57), 9 ranges
  labelled `Unclassified / Source Review Required`. **Pages are 0-based** (each Part starts at page 0).
- Pages covered per Part: 101, 90 (page 33 has no row), 52, 117, 35, 69 = 463 pages. No range overlaps another.
- Master Taxonomy: 152 entries (ID, category, sub-category, aliases, guidance, priority).
- Five loan PDFs sit in `loans/`; there are six Parts. Which Part is which file (and what 3b is, a second chunk of one
  file or a sixth) is not stated and I will not open the PDFs to find out. Step 0 below settles it from page counts.

## 2. Label to Master ID table (for your review; nothing guessed)
Rule: exact name match, else same sub-category under a renamed category (one candidate only), else a single-alias
match flagged CONFIRM. Anything else is NEEDS DECISION with the three closest master names shown as candidates only,
not applied. "Unspecified ..." labels name no form, so they are scored on category only. The machine-readable copy
is `golden/label_mapping.csv`; edit the `master_id` column there and the dataset builder reads it.

Totals: 13 exact, 20 category renamed, 3 alias (CONFIRM), 10 NEEDS DECISION, 9 category-only, 1 unclassified.

| Acra label | Ranges | Status | Master ID | Master name / candidates |
|---|---|---|---|---|
| Assets / Bank Statement | 4 | category renamed | AST-001 | Assets & Reserves / Bank Statement |
| Unclassified / Source Review Required | 9 | unclassified |  |  |
| Credit / Lender Credit Report | 1 | alias: CONFIRM | CRD-001 | Credit / Merged Infile Credit Report |
| Disclosures / Unspecified Disclosure | 5 | category-only |  |  |
| Credit / Unspecified Credit Document | 4 | category-only |  |  |
| Disclosures / Initial Disclosure Package | 5 | NEEDS DECISION |  | CLS-005 Initial Escrow Account Disclosure Statement ; CLS-002 Closing Disclosure ; CLS-013 Closing Package |
| Closing & Settlement / Escrow Instructions | 2 | exact | CLS-006 | Closing & Settlement / Escrow Instructions |
| Title & Ownership / Warranty Deed | 1 | exact | TTL-006 | Title & Ownership / Warranty Deed |
| Insurance / Hazard Insurance Policy | 1 | exact | INS-001 | Insurance / Hazard Insurance Policy |
| Loan Documents / Promissory Note | 7 | exact | LND-001 | Loan Documents / Promissory Note |
| Closing & Settlement / Wire Instructions | 2 | exact | CLS-010 | Closing & Settlement / Wire Instructions |
| Title / Unspecified Title Document | 3 | category-only |  |  |
| Loan Documents / Deed of Trust | 3 | exact | LND-004A | Loan Documents / Deed of Trust |
| Closing & Settlement / Unspecified Closing Document | 2 | category-only |  |  |
| Title / Final Title Insurance Policy | 1 | category renamed | TTL-002 | Title & Ownership / Final Title Insurance Policy |
| Closing & Settlement / Estimated HUD-1 Settlement Statement | 1 | NEEDS DECISION |  | CLS-003 HUD-1 Settlement Statement ; CLS-004 ALTA Settlement Statement ; HOA-005 HOA Ledger or Account Statement |
| Property / Unspecified Property or Collateral Document | 5 | category-only |  |  |
| Loan Documents / Executed Document Package | 1 | NEEDS DECISION |  | LND-006 Executed Loan Document Package ; CLS-013 Closing Package ; BRK-003 Broker Submission Package |
| Application / Unspecified Application Document | 2 | category-only |  |  |
| Application / Uniform Residential Loan Application (Form 1003) | 7 | exact | APP-001 | Application / Uniform Residential Loan Application (Form 1003) |
| Broker / Broker Submission Documents | 2 | NEEDS DECISION |  | BRK-003 Broker Submission Package ; VAL-009 UCDP Submission Summary Report ; UND-007 Loan Document Request |
| Closing & Settlement / Final HUD-1 Settlement Statement | 3 | NEEDS DECISION |  | CLS-003 HUD-1 Settlement Statement ; CLS-004 ALTA Settlement Statement ; HOA-005 HOA Ledger or Account Statement |
| Title / Chain of Title | 1 | category renamed | TTL-005 | Title & Ownership / Chain of Title |
| Property / Property Profile | 2 | category renamed | PRP-003 | Property & Transaction / Property Profile |
| Closing & Settlement / Closing Package | 1 | exact | CLS-013 | Closing & Settlement / Closing Package |
| Disclosures / State-Specific Disclosure | 1 | NEEDS DECISION |  | CLS-002 Closing Disclosure ; IDV-004 USA Patriot Act Information Disclosure ; CLS-008 Specific Closing Instructions |
| Property Valuation / Appraisal Report | 2 | exact | VAL-001 | Property Valuation / Appraisal Report |
| Fraud & Compliance / Fraud Detection Report (DataV) | 1 | NEEDS DECISION |  | IDV-010 Fraud Detection Report ; CRD-006 Real Estate Owned Report ; PRP-004 Property Data Report (DataTree) |
| Loan Administration / Unspecified Administrative Document | 2 | category-only |  |  |
| Quality Control / Watchlist Clearance | 1 | alias: CONFIRM | IDV-006 | Identity & Compliance / Watchlist Match Report |
| Property Valuation / Automated Valuation Model (AVM) | 1 | exact | VAL-010 | Property Valuation / Automated Valuation Model (AVM) |
| Servicing / Unspecified Servicing Document | 1 | category-only |  |  |
| Pricing & Eligibility / Pricing Details | 1 | category renamed | UND-003 | Underwriting & Pricing / Pricing Details |
| Pricing & Lock / Rate Lock Request | 1 | category renamed | UND-004 | Underwriting & Pricing / Rate Lock Request |
| Broker / Broker Fee Worksheet | 2 | category renamed | BRK-001 | Broker & Licensing / Broker Fee Worksheet |
| Broker / Broker Fee Validation | 2 | category renamed | BRK-002 | Broker & Licensing / Broker Fee Validation |
| Underwriting Decision / Loan Approval | 1 | alias: CONFIRM | UND-001 | Underwriting & Pricing / Conditional Loan Approval |
| Assets / Funds-to-Close Verification | 1 | category renamed | AST-003 | Assets & Reserves / Funds-to-Close Verification |
| Underwriting Decision / Counteroffer | 1 | category renamed | UND-002 | Underwriting & Pricing / Counteroffer |
| Title / Preliminary Title Report or Commitment | 1 | category renamed | TTL-001 | Title & Ownership / Preliminary Title Report or Commitment |
| Taxes / Property Tax Certificate | 1 | exact | TAX-001 | Taxes / Property Tax Certificate |
| Property / Property Data Report (DataTree) | 1 | category renamed | PRP-004 | Property & Transaction / Property Data Report (DataTree) |
| Taxes & Insurance / Unspecified Tax or Insurance Document | 2 | category-only |  |  |
| Disclosures / Proof of Disclosure Delivery | 1 | category renamed | AUD-004 | Electronic Records & Audit / Proof of Disclosure Delivery |
| Property / Property Report (Redfin) | 1 | category renamed | PRP-006 | Property & Transaction / Property Report (Redfin) |
| Disclosures / Equal Credit Opportunity Act (ECOA) Package | 1 | NEEDS DECISION |  | CRD-002 Special Credit Report ; LND-006 Executed Loan Document Package ; CRD-001 Merged Infile Credit Report |
| Licensing & Registration / Branch NMLS Record | 1 | category renamed | BRK-004 | Broker & Licensing / Branch NMLS Record |
| Credit / Credit Authorization | 1 | exact | CRD-005 | Credit / Credit Authorization |
| Loan Processing / Rework Request | 1 | category renamed | UND-008 | Underwriting & Pricing / Rework Request |
| Borrowing Entity / Articles of Incorporation or Organization | 1 | NEEDS DECISION |  | ENT-001A Articles of Incorporation ; ENT-001 Articles of Organization ; ENT-002 Certificate of Organization |
| Borrowing Entity / EIN Confirmation | 1 | exact | ENT-005 | Borrowing Entity / EIN Confirmation |
| Identity Verification / Government-Issued Identification | 2 | category renamed | IDV-001 | Identity & Compliance / Government-Issued Identification |
| Property / Property Report (SiteX) | 1 | category renamed | PRP-005 | Property & Transaction / Property Report (SiteX) |
| Borrowing Entity / Certificate of Good Standing | 1 | NEEDS DECISION |  | ENT-003 Certificate of Good Standing or Existence ; ENT-002 Certificate of Organization ; PRP-008 Certificate of Occupancy |
| Disclosures / Appraisal Delivery Waiver | 1 | category renamed | VAL-007 | Property Valuation / Appraisal Delivery Waiver |
| Loan Processing / Loan Document Request | 1 | category renamed | UND-007 | Underwriting & Pricing / Loan Document Request |

## 3. How the run works (all inside Plato; I read no page)
0. **Inventory, no model:** upload nothing; a local script prints only the page count of each loan PDF (integers) so
   Parts map to files by page count (a Part's pages = max page + 1). If a Part matches no file, it is dropped and
   listed. If you prefer I do not even count pages, tell me which Part is which file.
1. **Pack and taxonomy:** a scratch draft pack whose document registry is the Master Taxonomy adopted by the
   document-catalog routes (so the classifier's classes are the master IDs; sonnet-runtime is loading the reference).
   The pack's document_ingest runs with `split: true`, as `acra_full_package_split.py` does.
2. **Dataset:** one GoldenCase per loan file: input = the case record (empty) plus `documents: [{document_id}]` (the
   file uploaded to local Plato's document store: this is the only copy and it stays under the documents blob dir);
   expected = the Part's ranges, each `{pages, master_id | category | unclassified, confidence}` with pages converted
   to the pipeline's 1-based numbering (+1; verified by total page count). Stored with the SDK dataset routes, entity
   `case_run`, and a JSON copy in `golden/`.
3. **Experiment:** the `case_run` invoker over the dataset on local Plato, one case per loan, scored by custom
   Python scorers (below) that read the run's `output.documents.items` (class, page span, review pages).

## 4. Scorers (per page and per range; aggregate figures only in anything I report)
- **Page class accuracy:** share of expected pages whose predicted class equals the expected master ID; a
  category-only page counts as right when the predicted class is in the expected category; unclassified and
  NEEDS DECISION pages are excluded from the denominator and reported separately.
- **Range class accuracy:** a range is right when one predicted segment covers at least 80% of its pages with the
  right class (80% a named constant).
- **Boundary agreement:** expected cut points (each range start after the first) against predicted segment starts:
  precision, recall and F1 exact, and within one page.
- **Unclassified rate:** share of pages the pipeline left `unknown`, overall and on the expected-classified pages;
  and, on Acra's 9 "source review required" ranges, the share the pipeline also flagged unknown or for review.
- **Disagreements report:** per range, expected vs predicted class and spans, as labels and page numbers only (no
  text, no names), written to `golden/results/`.

## 5. Cost and exposure (the reason for approval)
- Document content goes to the model providers Plato already uses (vision split, optionally DocIntel). About 463
  pages: the precedent run cost a few tenths of a dollar per ~430 pages at the vision model's rate, capped at 5 USD by
  the spec's vision budget; DocIntel (`engine=docintel`) prices per page and is the dearer path.
- A rerun re-reads unchanged documents from the case-rerun reuse, so scorer changes cost nothing.

## 6. Please decide
1. Approve the mapping rules, and settle the 10 NEEDS DECISION and 3 CONFIRM labels (or say "leave excluded").
2. Approve step 0 (page counts only) and the first run's providers: vision (default) and a 5 USD ceiling.
3. Part 3b and the sixth Part against five files: which files do the Parts belong to (or let step 0 decide).
