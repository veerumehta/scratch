# acra-dscr-policy: map the document registry onto Acra's Master Taxonomy (plan only)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-10-17. Nothing adopted; `acra_dscr_policy` is untouched (pack_version 0.2.18). Asked
for by opus-xrepo; the user has not approved it. Memory `project_dscr_registry_bytepro` has the rules.

## 0. Sources and limits

- Read from local Plato (:8000, tenant `acra-lending`) with GET only: `/document-references`, then
  `/document-references/{id}?version=`. `acra-taxonomy@2026-10-17` has 152 entries in 19 categories,
  each with `code` (APP-001, ...), `aliases`, `cues`, `attributes.priority` (Core | Conditional).
  `bytepro@2026-07-29` has 471 entries (code = BytePro's own, category = its LoS group, applies_to
  consumer/commercial). The catalog-references route (`/catalogs/references`) is a different thing:
  it lists only `pack:ci-spread-core`.
- Not read: the real loan files under japes `docs/status/Acra/`. Nothing here was copied from the xlsx.
- Not checked: sonnet-runtime's claim that 141 of 152 entries are read by no job. Nothing below
  depends on it.
- Reading "the 11 coarse evidence types": `evidence_types.yaml` has 10 ids (nmls_verification,
  hoa_budget, hoa_financials, operating_agreement, articles_of_organization,
  certificate_of_good_standing, bank_statement, asset_statement, credit_report, appraisal), not 11.
  The 11 are the borrower-supplied and third-party entries of `document_types.yaml`, `loan_application`
  through `listing_history`, so that is what is mapped. The four closing entries (kind `closing`) are
  in section 3, and the finer `evidence_types.yaml` ids are in section 4.

## 1. The mapping

Convention: keep our slug as the stable id; the Taxonomy code is carried as the external id
(`x-source: acra-taxonomy@2026-10-17#<code>`, the shape Plato's adopt route writes); BytePro codes ride along as
further external ids/aliases. "Parent" is the Master Taxonomy category. Priority is Acra's, quoted.

| Our slug | Parent category | Primary entry (priority) | Related entries | BytePro codes |
|---|---|---|---|---|
| loan_application | Application | APP-001 Form 1003 (Core) | APP-002 URLA Lender Loan Information (Core), APP-003 Continuation Sheet (Conditional) | BrokerInitial1003, BrokerUpdated1003, Final1003 |
| appraisal_report | Property Valuation | VAL-001 Appraisal Report (Core) | VAL-002 Form 1004 (Core), VAL-003 Form 1073 condo (Conditional) | Appraisal, Appraisal1Final, Appraisal1PDF |
| lease_agreement | Rent & Lease | RNT-001 Residential Lease Agreement (Core) | | LeaseAgreement |
| rent_roll | Rent & Lease | RNT-002 Rent Roll or Rent Schedule (Conditional) | | MultiFamilyRentRoll (commercial only) |
| bank_statement | Assets & Reserves | AST-001 Bank Statement (Core) | | BankStatementAssets (not BankStatementIncome) |
| credit_report | Credit | CRD-001 Merged Infile Credit Report (Core) | CRD-002 Special Credit Report (Conditional) | CreditReport, BrokerCreditReport |
| entity_documents | Borrowing Entity | parent only, see 2.3 | ENT-001, ENT-003, ENT-004, ENT-005 (all Core); ENT-001A, ENT-002 (Conditional) | ArticlesofIncorp/Org, CertificateGoodStand, OperatingAgrmtByLaw |
| title_commitment | Title & Ownership | TTL-001 Preliminary Title Report or Commitment (Core) | TTL-005 Chain of Title (Core) | PreliminaryTitleRpt, ChainofTitle |
| hazard_insurance | Insurance | INS-005 Insurance Declarations Page (Core) | INS-001 Hazard Policy, INS-001B Rental Dwelling Policy, INS-002 Evidence of Insurance (all Core) | HazardInsPolicy |
| hoa_questionnaire | Condominium & HOA | HOA-002 Condominium Questionnaire (Conditional) | HOA-001 Resale Certificate, HOA-003 HOA Certification (Conditional) | HOACert, HOALitigation |
| listing_history | Property & Transaction | none, see 2.2 | PRP-003 Property Profile (Core) | none |

Notes on the table:
- appraisal_report: the cue cites "Freddie Mac Form 70 / Fannie Mae Form 1073". Acra's names are Form
  1004 (VAL-002) and Form 1073 (VAL-003); Form 70 is the Freddie number for the 1004. Worth a cue edit.
- VAL-004 and RNT-003 both carry the alias "Form 1007" (Single Family Comparable Rent Schedule; Market
  Rent Analysis). RNT-003 is Core and its cue says "the qualifying rent used in the DSCR calculation".
  Neither is a slug today. See question Q3.
- hazard_insurance: the cue is the declarations page, so INS-005 is primary; INS-001B (landlord policy)
  is the form a non-owner-occupied DSCR property actually carries.
- hoa_questionnaire: its cue also says "or the association's budget". Acra splits those (HOA-006 Budget,
  HOA-007 Financial Statements); the pack's `hoa_budget` / `hoa_financials` evidence ids match them 1:1.
- bank_statement: the pack's `asset_statement` evidence id has no entry of its own; AST-001 lists
  "Asset Statement" as an alias, so it folds into the same class.

## 2. The four job documents that matched no entry

Of the four, three have a clean home; one is a genuine gap.

1. **loan_application** -> APP-001 (Core), related APP-002/APP-003. It matched nothing only because no
   entry is named that; the entry exists (aliases URLA, Initial 1003, Broker Initial 1003). No change to
   the slug or its `yields`.
2. **listing_history** -> no entry in either reference. Searched both for listing, MLS, for sale. Nearest
   are PRP-003 Property Profile (Core, public-record summary), PRP-004 DataTree and PRP-006 Redfin
   ("online property-market and listing information", Conditional); BytePro has only `REOListingContract`
   (servicing, unrelated). Proposal: keep `listing_history` as a pack-local class with no Taxonomy id, set
   its parent to the Property & Transaction category, and ask Acra to add an entry (suggested: "Listing
   History or MLS Printout", Conditional, refinance only). Do not map it to PRP-006: that is one vendor's
   report, and the pack reads whether the property is listed, not who produced the page.
3. **entity_documents** -> a bundle, not one document: its cue lists articles, operating agreement, good
   standing, EIN letter. Propose it stays as the parent class and gains children, one per Acra entry:
   `articles_of_organization` (ENT-001), `certificate_of_good_standing` (ENT-003),
   `operating_agreement` (ENT-004), `ein_confirmation` (ENT-005). The first three slugs already exist as
   `evidence_types.yaml` ids, requested by DSCR-ENTITY-DOCS, so the document and evidence vocabularies would
   finally agree. ENT-008 Beneficial Ownership Certification and ENT-009 Entity Resolution (both Core) are
   not in the cue today and no rule reads them; leave them out until a rule does. Classification changes
   when a parent is split, so this needs the user's OK (Q2).
4. **title_agent_verification** -> TTL-008 Closing Protection Letter (Core). Its alias "Agency Verification
   Letter" is the cue's own wording, and BytePro has `ClosingProtectionLet` (group DOCS). Clean match.

## 3. The four closing entries (kind `closing`, read for nothing)

| Our slug | Entry | Priority | BytePro |
|---|---|---|---|
| borrower_authorization | LND-008 Automatic Mortgage Payment Authorization (aliases include ACH Mortgage Payment Authorization) | Conditional | ACH, ServicingACHform |
| certificate_of_completion | AUD-001 Electronic Signature Certificate (alias DocuSign Certificate) | Core | ESignAuditTrail, E-SignAuditLog |
| electronic_signature_disclosure | APP-009 Electronic Communications Consent Agreement (alias E-Sign Consent) | Core | none found |
| title_agent_verification | TTL-008 (section 2) | Core | ClosingProtectionLet |

## 4. Finer evidence ids (`evidence_types.yaml`)

hoa_budget -> HOA-006; hoa_financials -> HOA-007; operating_agreement -> ENT-004;
articles_of_organization -> ENT-001; certificate_of_good_standing -> ENT-003; bank_statement and
asset_statement -> AST-001; credit_report -> CRD-001; appraisal -> VAL-001. `nmls_verification` -> BRK-004
Branch NMLS Record (Core; BytePro BranchNMLS, BrokerNMLS, LONMLS) is the one that is not a loan document but
a lookup; map it for the id only.

## 5. Core vs Conditional and `required_classes`

Today: loan_application; any_of(lease_agreement, rent_roll); credit_report; any_of(entity_documents) when
the borrower is an llc, corporation or trust.

Do not derive this mechanically from Acra's priority. Core there means core to Acra's loan file in general
(a rate lock confirmation is Core), and many Core entries are read by no DSCR rule. What the mapping does
show:
- loan_application (APP-001 Core), credit_report (CRD-001 Core) and lease_agreement (RNT-001 Core) agree
  with Acra. rent_roll is Conditional, which agrees with it sitting in an any_of beside the lease.
- Entity: ENT-001, ENT-003, ENT-004 and ENT-005 are all Core. If entity_documents is split (2.3), the
  entity requirement could name the three children DSCR-ENTITY-DOCS already requires, as an all_of, rather
  than "any one entity document counts". Today any one document satisfies it. That is a behavior change.
- RNT-003 Market Rent Analysis is Core and feeds the qualifying rent. If DSCR needs it, it becomes a slug
  and joins the any_of with the lease and rent roll. Policy question, not a mapping one (Q3).
- Conditional entries (VAL-003 condo, HOA-*, ENT-001A) stay conditional on the loan's facts, as
  `hoa_questionnaire` is today.

## 6. How it would be adopted (after approval)

1. Via Plato's document catalog page or the adopt route, not by hand-editing `document_types.yaml`
   (the page writes `x-source` provenance and takes `if_match`). The client's `adopt_into_catalog`
   is for field catalogs, not document references; check which method the documents page uses first.
2. One pack_version bump (0.2.18 -> next patch) for the whole change, with the user's OK. Ids stay stable,
   a renamed id keeps the old in `aliases`, a dropped one is `retired: true`.
3. Keep `yields` as they are. The mapping adds parents and external ids; it does not change what any
   class is read for. Splitting entity_documents would need yields assigned to the children (today
   `Borrower.entity_type` only).
4. Re-run the DSCR tests and the pack check; classification tests may move if a cue is edited.
5. Never copy the xlsx files into jaci.

## 7. Questions for the user

- Q1. Approve the section 1 mapping as the basis for adoption?
- Q2. Split `entity_documents` into four children, or keep it a single bundle class with ENT-* as members?
- Q3. Does DSCR need Market Rent Analysis (RNT-003, Form 1007) as a document class and in the
  any_of(lease, rent roll)? If not, drop it from the mapping.
- Q4. For `listing_history`: ask Acra for a new entry, or keep it pack-local with no Taxonomy id?
