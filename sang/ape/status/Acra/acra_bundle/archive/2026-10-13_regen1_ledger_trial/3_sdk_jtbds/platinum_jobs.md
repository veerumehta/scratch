# Our jobs, platinum (45)

## acra-platinum.borrower_eligibility_and_credit_history.borrower_citizenship_and_homeownership_eligibility

**Purpose:** Determine whether the borrower meets the stated citizenship and homeownership eligibility requirements.

1. Check whether the borrower is a US Citizen or Permanent Resident.
2. If the borrower is a Permanent Resident, verify an unexpired PRA ID and SSA card / SSA-89.
3. Check whether the application is for a First Time Homebuyer. Acra defines a First Time Home Buyer as “an application where all Applicants have never previously owned a home (real property)”.
4. Verify that at least one guarantor has prior homeownership experience and that at least one borrower / guarantor attests on the application that they are not a first-time homebuyer. Applicability of the guarantor requirements to individual borrowers as well as entities is part of Q-13.

**Checks:**
- The borrower’s citizenship type is US Citizen or Permanent Resident.
- If the borrower is a Permanent Resident, the borrower has an unexpired PRA ID and SSA card / SSA-89.
- The application is not a First Time Homebuyer application.
- At least one guarantor has prior homeownership experience.
- At least one borrower / guarantor attests on the application that they are not a first-time homebuyer.

**Reads:** citizenship_type, first_time_homebuyer, borrower_entity_type
**Missing data:** Unexpired PRA ID, SSA card / SSA-89, Prior homeownership history for at least one guarantor, Application attestation by at least one borrower / guarantor, Acra confirmation on whether the guarantor requirements apply to individual borrowers as well as entities (Q-13)

## acra-platinum.borrower_eligibility_and_credit_history.decisioning_score_and_tradelines

**Purpose:** Determine whether the applicant’s decisioning score and tradelines meet the Platinum Summary requirements.

1. For a loan that does not close in the name of an entity, identify the Primary Wage Earner middle score as the decisioning credit score.
2. For a loan that closes in the name of an entity, use the highest middle score of the personal guarantors, presuming equal percentages of ownership. If ownership percentages differ, use the individual with the highest concentration of ownership.
3. Check that the decisioning credit score is at least 700.
4. Apply the tradeline rule: applicants with scores from 3 repositories are acceptable with no tradeline overlay; applicants with 2 or fewer scores require 2 tradelines & 24 month history or 3 tradelines & 12 month history.
5. If the case has one score, treat it as within “2 or fewer scores” for the tradeline requirement. Do not infer a decisioning-score rule for one or two scores, a no-score pathway, how to identify the Primary Wage Earner without income documentation, or which score to use when two or more guarantors hold an equal largest ownership interest and ownership is not equal across all guarantors; those matters require Acra confirmation (Q-05).

**Checks:**
- The decisioning credit score is the Primary Wage Earner middle score, or, for an entity loan, the score selected using the stated personal-guarantor and ownership rule.
- The decisioning credit score is at least 700.
- Applicants with scores from 3 repositories are treated as acceptable with no tradeline overlay, and applicants with 2 or fewer scores meet 2 tradelines & 24 month history or 3 tradelines & 12 month history.

**Reads:** borrower_entity_type, credit_score_count, fico, entity_is_borrower_1, tradelines_meet_requirement
**Missing data:** Middle scores for the relevant applicant or personal guarantors, Income documentation needed to identify the Primary Wage Earner where not identified, Ownership percentages and the ownership concentration of each personal guarantor, Tradeline counts and history durations, Acra confirmation on decisioning-score treatment for one or two scores, any no-score pathway, identifying the Primary Wage Earner without income documentation, and equal largest guarantor ownership interests (Q-05)

## acra-platinum.borrower_eligibility_and_credit_history.escrow_waiver_eligibility

**Purpose:** Determine whether a requested escrow waiver meets the printed loan-amount, mortgage-history, and Section 35 requirements.

1. If no escrow waiver is requested, stop; this job does not apply.
2. For a requested waiver, verify that the loan amount does not exceed $1.5M.
3. Verify “0x30x24 Mortgage History required”.
4. Verify that the loan is not a Section 35 loan. “Section 35” is not defined in the sources; Acra confirmation is requested (Q-14). Do not apply a CLTV or FICO limit, as none is printed for the Platinum waiver.

**Checks:**
- If an escrow waiver is requested, the loan amount is no more than $1.5M.
- If an escrow waiver is requested, the required “0x30x24 Mortgage History” is met.
- If an escrow waiver is requested, the loan is not a Section 35 loan.

**Reads:** escrow_waiver_requested, loan_amount
**Missing data:** Mortgage-history details, Acra definition of “0x30x24” (Q-06), Information establishing whether the loan is a Section 35 loan, Acra confirmation on the meaning of “Section 35” (Q-14)

## acra-platinum.borrower_eligibility_and_credit_history.housing_history_and_previous_credit_events

**Purpose:** Determine whether the case meets the stated “0x30x12” housing-history and “48 Mo Seasoning” previous-credit-event requirements, subject to the requested clarifications.

1. Review the borrower’s housing history against the requirement labeled “0x30x12”.
2. Review applicable Previous Credit Events (PCEs) against the requirement labeled “48 Mo Seasoning”.
3. Do not assume which events are covered, the starting event or ending date, the month-counting convention, or the treatment of modifications and forbearance; Acra confirmation is requested (Q-06).

**Checks:**
- The housing history meets “0x30x12”.
- Applicable Previous Credit Events (PCEs) meet “48 Mo Seasoning”.

**Reads:** housing_history, bankruptcy_or_foreclosure, months_since_bankruptcy_or_foreclosure, short_sale_dil_or_modification, months_since_short_sale_dil_or_modification
**Missing data:** Acra definition of “0x30x12” and “0x30x24” (Q-06), Acra confirmation of which Previous Credit Events are covered, the starting event and ending date, the month-counting convention, and the treatment of modifications and forbearance (Q-06), Housing-history details, Previous credit-event details and dates

## acra-platinum.borrower_eligibility_and_credit_history.mortgage_and_rental_payment_history

**Purpose:** Determine whether the mortgage / rental rating review uses the required properties and history period, including the DSCR documentation scope.

1. For determining mortgage pricing, evaluate ratings for properties the borrower owns and / or rents over the last twelve (12) months.
2. Consider all reported mortgages on credit. Where the applicant has mortgages that are not reported, review documentation for the applicant’s primary residence(s), any secondary residence(s), and the subject property.
3. For DSCR loans, require documentation on the subject property, principal residence, and second home (if any) of the borrower and / or guarantor(s). Require payment history for the primary residence, subject property, and second homes, if applicable. Additional properties do not require housing history to be documented unless documents in the file suggest a major credit event has occurred, for example a foreclosure listing the borrower (individually or as guarantor) on the credit report.
4. For a loan that has matured, rate it based on the maturity date of the loan; any extensions of the maturity date must be in writing.

**Checks:**
- Mortgage / rental ratings for properties the borrower owns and / or rents over the last twelve (12) months have been evaluated.
- All reported mortgages on credit have been considered, and documentation is present to evaluate history on primary residence(s), any secondary residence(s), and the subject property where the applicant has mortgages that are not reported.
- For a DSCR loan, documentation and payment history cover the subject property, primary residence, and second home (if any) of the borrower and / or guarantor(s), with additional-property housing history documented when file documents suggest a major credit event has occurred.
- A matured loan is rated based on its maturity date, and any extension of the maturity date is in writing.

**Reads:** loan_purpose, housing_history, occupancy_subtype, property_type
**Missing data:** Mortgage and rental ratings for the last twelve (12) months, Reported mortgage information, Documentation of history for mortgages not reported on credit, DSCR payment-history documentation for the subject property, primary residence, and second home (if any), File documentation indicating whether a major credit event has occurred on an additional property, Loan maturity date, Written maturity-date extensions, if any

## acra-platinum.dscr_calculation_and_rent_evidence.calculate_dscr_and_test_the_channel_minimum

**Purpose:** Determine the qualifying DSCR and whether it meets the minimum for the loan channel.

1. Confirm the transaction is a DSCR transaction and identify whether the rental income is long-term or short-term.
2. Use the greater of market rent as established on the 1007 or 1025, or actual rent, as the qualifying rent.
3. If actual rent is used, verify evidence of 2 months’ proof of receipts and that the lease is in place for at least 3 months after loan closing.
4. Calculate the denominator using annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees (collectively, ‘PITIA’); include subordinate financing, if applicable.
5. Use the first payment due under the terms of the Note when calculating the DSCR. If the loan is interest-only, do not decide which payment enters the denominator; that question is identified as Q-21.
6. Compare the resulting DSCR with the applicable channel minimum: Correspondent ≥ 1.2; Wholesale ≥ 1.0.

**Checks:**
- The rental income used to qualify is long-term, not short-term.
- The qualifying rent is the greater of market rent established on the 1007 or 1025, or actual rent.
- If actual rent is used, evidence documents 2 months’ proof of receipts.
- If actual rent is used, the lease is in place for at least 3 months after loan closing.
- The denominator includes annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees, and includes subordinate financing if applicable.
- The DSCR calculation uses the first payment due under the terms of the Note.
- The DSCR is at least the applicable channel minimum: Correspondent ≥ 1.2; Wholesale ≥ 1.0.

**Reads:** channel, dscr_documentation_type, gross_rental_income, pitia, product_is_interest_only, interest_only_10_40, loan_purpose, property_type, residential_unit_count
**Missing data:** Rental term type (long-term or short-term), Market rent established on the 1007 or 1025, Actual rent amount, if used, Evidence of 2 months’ proof of actual-rent receipts, if actual rent is used, Lease term and loan closing date, if actual rent is used, Annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees, Subordinate financing amount, if applicable, First payment due under the terms of the Note, For an interest-only loan, Acra's answer to Q-21 on which payment enters the DSCR denominator

## acra-platinum.dscr_calculation_and_rent_evidence.verify_current_lease_for_cash_out_refinance

**Purpose:** Confirm that a cash-out refinance has the required current lease agreement.

1. Determine whether the loan purpose is cash-out refinance.
2. If it is a cash-out refinance, review the file for a current lease agreement.

**Checks:**
- If the loan purpose is cash-out refinance, a current lease agreement is provided.

**Reads:** loan_purpose, current_lease_in_place
**Missing data:** Current lease agreement, if the loan purpose is cash-out refinance

## acra-platinum.dscr_calculation_and_rent_evidence.verify_rent_schedule_and_rent_evidence

**Purpose:** Confirm the required 1007 and any applicable documentation supporting lease rent.

1. For a DSCR qualifying file, verify that a Single-Family Comparable Rent Schedule (FNMA Form 1007) is provided.
2. Verify that the 1007 is from the original appraiser or a state licensed appraiser.
3. For a lease-option purchase where the down payment required in §3.45 is generated from excess monthly rent contributions, verify that a 1007 is provided.
4. When proposed rental income is being used to qualify, verify that a 1007 is provided.
5. For a single family investment property with excessive monthly rent payments reflected on the lease, review documentation supporting that the monthly rent is typical for the area. Acceptable documentation may include classified ads from local newspapers, a 1007 completed by the appraiser, or a market rent survey completed by a local real estate company or rental management company familiar with market rents in the area.

**Checks:**
- A Single-Family Comparable Rent Schedule (FNMA Form 1007) is provided for the DSCR qualifying file.
- The 1007 is from the original appraiser or a state licensed appraiser.
- If the transaction is a lease-option purchase and the down payment required in §3.45 is generated from excess monthly rent contributions, a 1007 is provided.
- If proposed rental income is being used to qualify, a 1007 is provided.
- If a single family investment property's lease reflects excessive monthly rent payments, documentation supports that the monthly rent is typical for the area.

**Reads:** dscr_documentation_type, loan_purpose, property_type, residential_unit_count, gross_rental_income
**Missing data:** Form 1007 and its appraiser's identity and licensing status, Whether the transaction is a lease-option purchase, Whether the down payment required in §3.45 is generated from excess monthly rent contributions, Whether proposed rental income is being used to qualify, Lease rent and evidence needed to determine whether the monthly rent is excessive, If monthly rent is excessive, supporting documentation such as classified ads from local newspapers, a 1007 completed by the appraiser, or a market rent survey completed by a local real estate company or rental management company familiar with market rents in the area

## acra-platinum.dscr_calculation_and_rent_evidence.verify_required_housing_history

**Purpose:** Confirm the stated housing-history requirement without applying unresolved Seller's Guide alternatives.

1. Review the applicant's housing history.
2. Verify that it meets the Platinum Summary requirement of 0x30x12.
3. Do not treat the Seller's Guide alternatives for tenant-occupied properties with forbearance or mortgage lates within the last 12-months as established Platinum Select alternatives; their application is unresolved in Q-17.

**Checks:**
- The applicant meets the Platinum Summary requirement of 0x30x12.

**Reads:** housing_history, mortgage_history_0x30x24, bankruptcy_or_foreclosure, months_since_bankruptcy_or_foreclosure
**Missing data:** Housing-history information sufficient to establish 0x30x12, Acra's answer to Q-17 on whether the Seller's Guide alternatives apply on Platinum Select, which cases they cover, and whether “Applicant” includes guarantors of an entity borrower

## acra-platinum.entity_guarantor_and_trust_requirements.borrower_and_guarantor_due_diligence

**Purpose:** Determine whether due diligence meets PLAT-5.11 and whether the required parties are included in the background review described in PLAT-5.12.

1. Determine the date of loan approval or draw and verify that Borrower / Guarantor Due Diligence is current as of that date.
2. For an entity borrower, identify the entity, recourse guarantor(s), every party (individual or entity) owning 20% or more of the entity directly or indirectly, and every party with managing control.
3. For individual borrowers, identify all such individuals.
4. Verify that the background review covers the applicable Key Principals and Entities. The review may be ordered from Checkpoint, LexisNexis or another comparable provider and may include criminal history, OFAC searches, litigation, judgment, and lien searches.

**Checks:**
- Borrower / Guarantor Due Diligence is current as of the date of any loan approval or draw.
- For an entity borrower, the background-review scope includes the entity, recourse guarantor(s), all direct or indirect owners of 20% or more, and parties with managing control.
- For individual borrowers, the background-review scope includes all such individuals.
- The background review is of the Key Principals and Entities described in PLAT-5.12.

**Reads:** borrower_entity_type, entity_is_borrower_1
**Missing data:** date of loan approval or draw and date/status of Borrower / Guarantor Due Diligence, entity borrower status, entity identity, recourse guarantor(s), direct and indirect ownership percentages, and parties with managing control, individual borrower identities and applicable Key Principals and Entities, background-review records and parties reviewed

## acra-platinum.entity_guarantor_and_trust_requirements.borrower_citizenship_and_first_time_homebuyer_eligibility

**Purpose:** Determine whether the borrower meets the citizenship and first-time homebuyer requirements stated in PLAT-4.1 through PLAT-4.4.

1. Check whether the borrower is a US Citizen or Permanent Resident.
2. If the borrower is a Permanent Resident, verify an unexpired PRA ID and SSA card / SSA-89.
3. Determine whether the application meets Acra’s definition of a First Time Home Buyer: all Applicants have never previously owned a home (real property).
4. Apply the stated ineligibility of First Time Homebuyers for this program.

**Checks:**
- The borrower’s citizenship type is US Citizen or Permanent Resident.
- For a Permanent Resident, the PRA ID is unexpired and an SSA card / SSA-89 is provided.
- The borrower is not a First Time Homebuyer under Acra’s stated definition.

**Reads:** citizenship_type, first_time_homebuyer
**Missing data:** unexpired PRA ID, SSA card / SSA-89, whether all Applicants have never previously owned a home (real property), if not established by the case field

## acra-platinum.entity_guarantor_and_trust_requirements.entity_documentation

**Purpose:** Determine whether the entity documentation required by PLAT-5.10 is complete and acceptable for review under the stated requirements.

1. Obtain a complete, legible Certificate of Formation / Articles of Organization and all amendments.
2. For LLCs and Partnerships, obtain a complete, legible Operating Agreement with all referenced exhibits and all amendments; for corporations, obtain the Bylaws with all referenced exhibits and all amendments. Verify that the document states whether the entity is member or manager managed, authorizes borrowing money and entering into contracts for mortgage assets, and designates signers. Determine whether additional information is required if formation documents and the Operating Agreement or Bylaws conflict.
3. Obtain documentation evidencing all ownership interests. For LLCs and Partnerships, verify that the Operating Agreement identifies by name all persons and their ownership interest or attaches that information as an exhibit, or that membership interest certificates / units are provided in compliance with the Operating Agreement.
4. For S or C Corporations, obtain shareholder / stockholder certificates complying with the Bylaws, if any, or, if stock certificates are lost or unavailable, the corporation’s stock ledger. Verify that the certificate or ledger accounts for all outstanding shares noted in the Certificate of Formation / Articles of Organization, including those held by the corporation. If stock certificates are lost, destroyed, mutilated, or otherwise unavailable, obtain an Affidavit of Lost Stock Certificate.
5. For S-corporations or Partnerships where both stock certificate and stock ledger are unavailable, obtain the most recent preceding tax year's K-1 statement for all members with 20% or more interest and a letter from the CPA or Tax Preparer affirming current ownership interest; if the preceding year's taxes have not been filed, verify that the letter includes a statement to that effect.
6. Verify that names on entity documents match the identification; if they do not match exactly, obtain a letter of explanation addressing the discrepancy.
7. Obtain a Certificate of Good Standing or equivalent document valid within ninety (90) days of the closing date.
8. If the entity is formed in a state other than where business is conducted or the property is located, obtain a Certificate of Foreign Qualification or other qualification to operate in the state where business is being conducted.
9. Obtain the entity’s IRS Form SS4 or Federal Taxpayer Identification Number (TIN) or Employer Identification Number (EIN) issuance letter. If an EIN exception is requested, verify that it is submitted for review by Acra's Legal Department with a letter of explanation stating the applicable grounds.
10. Obtain a Unanimous Written Consent / Board Resolution signed by all members regardless of their percentage of interest, authorizing the transaction with Acra Lending and identifying who is authorized to sign the loan documents on behalf of and to bind the entity. Check whether the Operating Agreement or Bylaws require it even where ownership is held by one individual. Do not accept it to designate a signor on a personal guarantee.
11. If an attorney in fact is designated to execute a personal guarantee, verify that the principal utilizes a Power of Attorney for that designation.
12. Record any additional supporting documentation Legal conditions for in its sole discretion.

**Checks:**
- A complete, legible Certificate of Formation / Articles of Organization and all amendments are provided.
- The applicable Operating Agreement or Bylaws and all referenced exhibits and amendments are provided and contain the required management, borrowing, contracting, and signer provisions.
- Documentation evidences all ownership interests in the manner required for the entity type.
- The applicable corporate share evidence accounts for all outstanding shares, and an Affidavit of Lost Stock Certificate is provided when required.
- When both stock certificate and stock ledger are unavailable for an S-corporation or Partnership, the required K-1 statements and CPA or Tax Preparer letter are provided, including the required statement if the preceding year's taxes have not been filed.
- Names on entity documents match identification, or a letter of explanation addresses any exact-name discrepancy.
- A Certificate of Good Standing or equivalent is valid within ninety (90) days of the closing date.
- Where applicable, qualification to operate in the state where business is being conducted is documented.
- The entity’s IRS Form SS4 or TIN or EIN issuance letter is provided, or an EIN exception request with the required grounds letter is submitted for review by Acra's Legal Department.
- The required Unanimous Written Consent / Board Resolution is signed by all members, authorizes the transaction, and identifies the authorized loan-document signatory; it is not used to designate a personal-guarantee signor.
- A Power of Attorney is utilized by the principal to designate an attorney in fact to execute a personal guarantee, where applicable.
- Any additional supporting documentation required by Legal in its sole discretion is provided.

**Reads:** borrower_entity_type, entity_documents_complete
**Missing data:** entity formation documents and amendments, Operating Agreement or Bylaws, referenced exhibits, amendments, and any required additional information concerning conflicts, ownership-interest documentation, including applicable certificates or units, corporate stock certificates or stock ledger, outstanding-share accounting, and any required Affidavit of Lost Stock Certificate, applicable K-1 statements and CPA or Tax Preparer letter, including any required statement about taxes not filed, entity-document names, identification, and any required letter of explanation, closing date and Certificate of Good Standing or equivalent, entity formation state, state where business is conducted, property location, and any qualification document, IRS Form SS4, TIN or EIN issuance letter, or EIN exception request and grounds letter, Unanimous Written Consent / Board Resolution and Operating Agreement or Bylaws provisions concerning it, Power of Attorney, principal, and attorney in fact, where applicable, any additional supporting documentation Legal requires in its sole discretion

## acra-platinum.entity_guarantor_and_trust_requirements.entity_eligibility_and_guarantees

**Purpose:** Determine whether an entity borrower and its ownership and guarantee arrangements meet PLAT-5.1 through PLAT-5.9.

1. Determine whether the transaction is business purpose and concerns an investment property exclusively.
2. Confirm that collateral title will be held directly by individual person(s) or by an entity acceptable to Acra in its sole discretion.
3. For an entity borrower, identify every direct and indirect owner, each ownership percentage, and any party with managing control; determine which individuals have direct or indirect ownership ≥ 20%.
4. Verify that every individual with direct or indirect ownership ≥ 20% provides an Acra-approved recourse guarantee or Exhibit 7. If there are multiple guarantors, verify that recourse is joint and several.
5. Verify that the entity borrower is a single purpose entity with no assets other than residential investment or rental properties and is engaged in owning and operating residential investment or rental properties; verify that it is not a series limited liability company.
6. Identify every entity that will hold direct ownership of the subject property and be on title as a direct owner; verify that each is a borrowing entity.
7. Review operating-agreement or bylaw changes affecting ownership percentages and their timing in relation to the Application Date and application process; do not recognize changes made with intent to circumvent required personal guarantors or changes within 30 days prior to an Application Date or throughout the application process.
8. Verify that the entity is a US formed and based Entity and is not a foreign owned entity; verify that its type is one of the allowed types and is not a prohibited type.
9. Check that the structure does not involve a prohibited business entity arrangement: nesting is limited to only one (1) wholly-owned subsidiary owned by individual(s), and multiple nesting or ownership by multiple entities, trusts, etcetera are not acceptable.
10. Verify that at least one guarantor has prior homeownership experience and that at least one borrower / guarantor attests on the application that they are not a first-time homebuyer.

**Checks:**
- The transaction is a business purpose transaction involving an investment property exclusively.
- Collateral title is held directly by individual person(s) or by an entity acceptable to Acra in its sole discretion.
- Every individual with direct or indirect ownership ≥ 20% provides an Acra-approved recourse guarantee or Exhibit 7.
- Where there are multiple guarantors, all recourse is joint and several.
- The entity borrower is a single purpose entity as defined in PLAT-5.4 and is not a series limited liability company.
- Every entity that will hold direct ownership of the subject property and be on title as a direct owner is a borrowing entity.
- No ownership-percentage change with intent to circumvent required personal guarantors is recognized, and no such change is made within 30 days prior to an Application Date or throughout the application process.
- The entity is US formed and based, is not foreign owned, and is of an allowed type rather than a prohibited type.
- The entity ownership structure complies with the stated one-subsidiary limit and does not involve multiple nesting or ownership by multiple entities, trusts, etcetera.
- At least one guarantor has prior homeownership experience.
- At least one borrower / guarantor attests on the application that they are not a first-time homebuyer.

**Reads:** loan_purpose, property_type, borrower_entity_type, entity_is_borrower_1
**Missing data:** whether the transaction is business purpose and the property is exclusively an investment property, if not established by the case fields, title vesting and Acra’s determination whether an entity is acceptable in its sole discretion, all direct and indirect owners, their ownership percentages, and parties with managing control, recourse guarantees, whether each is Acra-approved or Exhibit 7, and whether multiple guarantors’ recourse is joint and several, entity assets and business activities; whether an LLC is a series LLC, all direct title holders and whether each is a borrowing entity, ownership-change purpose and dates, Application Date, and application-process dates, entity formation and base location, foreign ownership, and entity type details not held in the case fields, the complete entity ownership and nesting structure, guarantor prior homeownership experience, application attestation that a borrower / guarantor is not a first-time homebuyer

## acra-platinum.entity_guarantor_and_trust_requirements.revocable_living_trust_title_vesting

**Purpose:** Determine whether title vesting in an inter vivos revocable trust meets PLAT-5.13.

1. Determine whether title is to be vested in an inter vivos revocable trust; if so, obtain a complete, legible copy of the Trust or a Certification of Trust containing every item specified in PLAT-5.13.
2. Verify that the Trust is valid under the laws of the state in which it is established and is revocable, meaning it can be changed or canceled at any time for any reason during a Trustor's lifetime.
3. Verify that the Trust is established by one or more natural persons, solely or jointly, and becomes effective during the lifetime of the person(s) establishing it.
4. Verify that the primary beneficiary is the individual(s) establishing the Trust.
5. If the Trustor(s) and Trustee(s) are not the same, obtain written exception by Acra Senior Management.
6. Verify that the Trust specifies the Trustee’s power to hold title and mortgage the property; the beneficiary does not need to grant written consent for the Trust to borrow money or that consent has been granted in writing for purposes of the mortgage; there is no unusual risk or impairment to the lender's rights; and holding title in the Trust does not diminish the lender's rights as a creditor.
7. Record any additional supporting documentation Legal conditions for in its sole discretion.

**Checks:**
- A complete, legible copy of the Trust or a Certification of Trust states the existence and date of the Trust; Trustor(s) and current Trustee(s); Trustee powers; whether the Trust is revocable and, if so, who holds the right to revoke; required Trustee signers; Trust identification number; how title to Trust assets should be taken; and that the Trust has not been revoked, modified, or amended in any manner.
- The Trust is valid under the laws of the state in which it is established and is revocable as specified.
- The Trust is established by one or more natural persons, solely or jointly, and becomes effective during the lifetime of the person(s) establishing it.
- The primary beneficiary of the Trust is the individual(s) establishing the Trust.
- If the Trustor(s) and Trustee(s) are not the same, written exception by Acra Senior Management is obtained.
- The Trust contains all required provisions concerning the Trustee’s powers, beneficiary consent to borrowing, unusual risk or impairment to the lender's rights, and the lender's rights as a creditor.
- Any additional supporting documentation required by Legal in its sole discretion is provided.
**Missing data:** whether title is vested in an inter vivos revocable trust, Trust or Certification of Trust and all required statements and identifying information, state where the Trust is established and evidence of validity under that state’s laws, Trust terms establishing revocability and the right to revoke, identity and status of the natural-person Trustor(s), effective date, and primary beneficiary, Trustor(s), Trustee(s), and written exception by Acra Senior Management if they are not the same, Trust terms concerning Trustee powers, beneficiary consent, lender rights, and any unusual risk or impairment, any additional supporting documentation Legal requires in its sole discretion

## acra-platinum.funds_to_close_seasoning_and_reserves.escrow_waiver_and_listed_property_impounds

**Purpose:** Determine whether a requested escrow waiver meets the stated loan amount and mortgage-history requirements, account for the undefined Section 35 exclusion, and address the separate impound requirement for a property listed for sale.

1. If an escrow waiver is requested, check that the loan amount does not exceed $1.5M.
2. If an escrow waiver is requested, check for 0x30x24 Mortgage History.
3. If an escrow waiver is requested, determine whether the loan is a Section 35 loan; Section 35 loans are ineligible, but Section 35 is not defined in the source, so obtain Acra confirmation as needed.
4. Separately, if the property is listed for sale, require impounds.

**Checks:**
- If escrow_waiver_requested is true, loan_amount <= $1,500,000.
- If escrow_waiver_requested is true, mortgage_history_0x30x24 is true.
- If escrow_waiver_requested is true, the loan is not a Section 35 loan.
- If property_currently_listed_for_sale is true, impounds are in place.

**Reads:** escrow_waiver_requested, loan_amount, mortgage_history_0x30x24, property_currently_listed_for_sale
**Missing data:** Acra confirmation or other authoritative determination of whether the loan is a Section 35 loan, because Section 35 is not defined in the source., Whether required impounds are in place for a property listed for sale.

## acra-platinum.funds_to_close_seasoning_and_reserves.funds_held_in_a_foreign_bank_or_currency

**Purpose:** Assess the stated requirement for funds held in a foreign bank or currency and identify the Acra confirmation needed for eligible borrowers holding funds abroad.

1. Determine whether funds to close are held in a foreign bank or currency.
2. If funds are held in a foreign bank or currency, assess the stated requirement that they be repatriated at minimum three (3) business days prior to Closing.
3. Obtain Acra confirmation on whether this repatriation requirement applies to eligible borrowers holding funds abroad and what evidence and timing convention apply.
4. Do not apply the stated 60-day seasoning requirement to eligible borrowers; the source states it for Foreign Nationals only and does not restate it for eligible borrowers.

**Checks:**
- If funds to close are held in a foreign bank or currency, the stated repatriation timing of at minimum three (3) business days prior to Closing is addressed, subject to Acra confirmation of applicability, evidence, and timing convention.
- The 60-day seasoning requirement is not applied to an eligible borrower on the basis of this source.

**Reads:** citizenship_type
**Missing data:** Whether funds to close are held in a foreign bank or currency., Closing date and evidence of repatriation date., Acra confirmation on applicability of repatriation to eligible borrowers holding funds abroad, and on required evidence and timing convention.

## acra-platinum.funds_to_close_seasoning_and_reserves.funds_to_close_seasoning_and_documentation

**Purpose:** Determine whether verification of seasoning is required for funds to close and establish the universal minimum documentation period.

1. Determine whether the transaction is a consumer transaction or a business purpose loan; whether any loan on this program is a consumer transaction is unresolved in the source.
2. For a consumer transaction, if CLTV is over 70%, require verification of seasoning of funds to close.
3. For a business purpose loan, if funds to close are over $50,000 and CLTV is over 70%, require verification of seasoning of funds to close.
4. For all transactions, verify a minimum of 30-days documentation.
5. Do not impose a domestic-funds seasoning period beyond the 30-days documentation minimum without Acra confirmation.

**Checks:**
- For a consumer transaction with cltv_pct > 70%, verification of seasoning of funds to close is provided.
- For a business purpose loan with funds to close > $50,000 and cltv_pct > 70%, verification of seasoning of funds to close is provided.
- All transactions have a minimum of 30-days documentation.
- No domestic-funds seasoning period beyond the 30-days documentation minimum is applied without Acra confirmation.

**Reads:** cltv_pct, loan_purpose
**Missing data:** Whether the transaction is a consumer transaction or a business purpose loan, including Acra's determination of whether any loan on this program is a consumer transaction., Amount of funds to close., Documentation verifying seasoning of funds to close when a trigger applies., Documentation establishing at least 30-days., Acra confirmation on whether any seasoning period applies to domestic funds beyond the 30-days documentation minimum.

## acra-platinum.funds_to_close_seasoning_and_reserves.investment_property_gift_funds

**Purpose:** For an investment property, establish that applicant(s) contribute a minimum of 10% of the purchase price from their own sourced and seasoned funds.

1. Determine whether the transaction is an investment property.
2. If it is an investment property, verify the amount of the applicant(s)' own contribution against the purchase price.
3. Verify that the applicant(s)' contribution is their own funds and that those funds are sourced and seasoned.
4. Do not apply a treatment to seller concessions or other contributions; obtain Acra confirmation because the Platinum Summary does not address them.

**Checks:**
- If the transaction is an investment property, applicant(s)' own sourced and seasoned funds contributed to the transaction are at least 10% of the purchase price.
- The treatment of seller concessions and other contributions has been confirmed by Acra where relevant.

**Reads:** loan_purpose, occupancy_subtype
**Missing data:** Whether the transaction is an investment property, if not established by the case fields., Purchase price., Amount of applicant(s)' own funds contributed to the transaction., Documentation establishing the source and seasoning of those funds., Acra confirmation on treatment of seller concessions and other contributions, where relevant., Gift documentation requirements in the Seller's Guide gift-fund section (Appendix B).

## acra-platinum.funds_to_close_seasoning_and_reserves.loan_amount_limits

**Purpose:** Determine whether the loan amount meets the stated minimum, maximum, increment, and applicable maximum-CLTV requirements.

1. Check that the loan amount is between $100,000 and $2,000,000, inclusive.
2. Check that the loan amount is in $50 increments.
3. If the loan amount is less than $350,000 or greater than $1,500,000, check that CLTV does not exceed 75.00%.

**Checks:**
- $100,000 <= loan_amount <= $2,000,000.
- loan_amount is a multiple of $50.
- If loan_amount < $350,000 or loan_amount > $1,500,000, cltv_pct <= 75.00%.

**Reads:** loan_amount, cltv_pct

## acra-platinum.funds_to_close_seasoning_and_reserves.reserve_requirements_by_trigger

**Purpose:** Assess the reserve requirements stated for CLTV, property listed for sale, recent forbearance or mortgage lates with tenant occupancy, and unavailable rent loss insurance.

1. If CLTV is greater than 75.00%, check for 6-months Reserves required for CLTV > 75.00%.
2. If the property was listed for sale within six months, check for twenty-four (24) months of reserves. Cash-in-hand may be considered if otherwise consistent with the Guide.
3. Determine whether the property is tenant-occupied and whether there was forbearance or mortgage lates in the last 12 months without timely receipt of the prior two months' rent. If so, check for 12 months of the subject's payment in reserve; this may be from the transaction's cash-in-hand. The relationship to 0x30x12 is unresolved in the source.
4. If rent loss insurance is required but cannot be obtained, check for two (2) months reserves for every one (1) month of coverage not provided.
5. Do not assume a base reserve requirement at CLTV of 75.00% or below, a payment basis, permitted sources, whether overlapping triggers are cumulative, or whether reserves substituted for rent loss insurance are additional; obtain Acra confirmation.

**Checks:**
- If cltv_pct > 75.00%, reserves_months >= 6.
- If listed_for_sale_last_6_months is true, reserves_months >= 24.
- If there was forbearance or mortgage lates in the last 12 months, the subject is tenant-occupied, and the prior two months' rent was not received timely, 12 months of the subject's payment are held in reserve.
- If rent loss insurance is required but cannot be obtained, reserves equal two (2) months for every one (1) month of coverage not provided.
- The base reserve requirement at CLTV of 75.00% or below, payment basis, permitted sources, cumulative treatment of overlapping triggers, and treatment of reserves substituted for rent loss insurance as additional reserves have been confirmed by Acra where applicable.

**Reads:** cltv_pct, listed_for_sale_last_6_months, reserves_months, housing_history, current_lease_in_place, mortgage_history_0x30x24
**Missing data:** Whether there was forbearance or a mortgage late in the last 12 months., Whether the subject is tenant-occupied and whether the prior two months' rent was received timely., Subject payment amount and reserve amount available for that requirement., Whether rent loss insurance is required, whether it can be obtained, and the months of coverage not provided., Acra confirmation on the base requirement at CLTV of 75.00% or below, payment basis (including on an interest-only loan), permitted sources, cumulative treatment of overlapping triggers, and whether reserves substituted for rent loss insurance are additional., Whether cash-in-hand is otherwise consistent with the Guide, if relied on.

## acra-platinum.loan_amount_decisioning_score_and_cltv_limits.apply_cltv_limits

**Purpose:** Determine whether CLTV meets the matrix and the additional stated limits and adjustments.

1. Apply the matrix row for the decisioning score and loan purpose: 730 and above, 80% for Purchase, 80% for Rate & Term, and 75% for Cash-Out; 721 through 729, 80%, 80%, and 65%, respectively; 700 through 720 on a literal reading of the printed thresholds, 80%, 80%, and 55%, respectively.
2. Apply the 75.00% maximum CLTV when the loan amount is less than $350,000 or greater than $1,500,000.
3. Apply the 75.00% maximum CLTV for a Warrantable Condo or Two-Units property.
4. Apply the 75.00% maximum CLTV for Interest-Only (5 Yr Term).
5. Apply the 65% LTV / CLTV maximum when the property was listed for sale within six months.
6. For Correspondent loans with a score of 700-719, apply the stated 60% CLTV restriction; for a cash-out loan in that score range, do not use that restriction to raise the matrix’s 55% limit.
7. For a declining-market property, account for the stated -5% CLTV adjustment and obtain confirmation of how it combines with other caps.
8. Where the score is 720, or the Correspondent 700-719 restriction interacts with the matrix by purpose, obtain the requested Acra confirmation on treatment of the printed 721 threshold and the limits.

**Checks:**
- cltv_pct does not exceed the matrix maximum for the decisioning score and loan_purpose, using the printed thresholds literally.
- If loan_amount is less than $350,000 or greater than $1,500,000, cltv_pct does not exceed 75.00%.
- If property_type is Warrantable Condo or Two-Units, cltv_pct does not exceed 75.00%.
- If product_is_interest_only is true, cltv_pct does not exceed 75.00%.
- If listed_for_sale_last_6_months is true, cltv_pct does not exceed 65%.
- If channel is Correspondent and the decisioning score is from 700 through 719, cltv_pct does not exceed 60%; a cash-out case in this range must also meet the matrix maximum.
- If the property is in a declining market, the -5% CLTV adjustment is applied using the combination with other caps confirmed by Acra.
- If the case has a score of 720, or is a Correspondent case with a score of 700-719, the applicable Q-01 treatment has been confirmed by Acra.

**Reads:** cltv_pct, fico, loan_purpose, loan_amount, property_type, product_is_interest_only, listed_for_sale_last_6_months, channel
**Missing data:** Confirmation under Q-01 of whether the printed 721 threshold is intended and how a score of 720 is treated, including how the Correspondent restriction applies by purpose; whether the property is in a declining market and the property/borrower full profile needed for the -5% CLTV adjustment; confirmation under Q-08 of how that reduction combines with other caps.

## acra-platinum.loan_amount_decisioning_score_and_cltv_limits.determine_decisioning_score_and_tradelines

**Purpose:** Determine whether the decisioning score and tradelines meet PLAT-6.1 through PLAT-6.5.

1. Determine the decisioning score using the applicable PLAT-6.1 rule: the Primary Wage Earner middle score; for a loan closing in an entity’s name, the highest middle score of personal guarantors when ownership percentages are equal; or, when ownership percentages differ, the individual with the highest concentration of ownership.
2. Check that the decisioning score is at least 700.
3. For applicants with scores from 3 repositories, apply no tradeline overlay; for applicants with 2 or fewer scores, check the stated tradeline and history requirement.

**Checks:**
- The decisioning score is selected in accordance with PLAT-6.1.
- fico is at least 700.
- credit_score_count is 3, or credit_score_count is 2 or fewer and tradelines_meet_requirement is true.

**Reads:** borrower_entity_type, entity_is_borrower_1, ownership_months, credit_score_count, fico, tradelines_meet_requirement
**Missing data:** Middle scores for the relevant wage earner or personal guarantors; entity loan ownership percentages and guarantor ownership concentrations, as applicable; identification of the Primary Wage Earner; confirmation under Q-05 of how the decisioning score is set with one score or two scores, whether a no-score pathway exists, how the Primary Wage Earner is identified without income documentation, and whose score is used when two or more guarantors hold an equal largest ownership interest and ownership is not equal across all guarantors; for applicants with 2 or fewer scores, the tradeline count and history needed to establish 2 tradelines & 24 month history or 3 tradelines & 12 month history.

## acra-platinum.loan_amount_decisioning_score_and_cltv_limits.verify_applicant_contribution_when_gift_funds_are_used

**Purpose:** Determine whether applicants using gift funds for an investment property meet PLAT-1.15.

1. For investment-property gift funds, check that applicants contribute a portion of their own sourced and seasoned funds equal to at least 10% of the purchase price.
2. Check gift documentation against the Seller's Guide gift-fund section (Appendix B).

**Checks:**
- For an investment property using gift funds, applicants’ own sourced and seasoned funds are at least 10% of the purchase price.
- Gift documentation meets the Seller's Guide gift-fund requirements in Appendix B.
**Missing data:** Whether gift funds are used for an investment property; purchase price; amount and source of applicants’ own funds and evidence that those funds are seasoned; gift-fund documentation and the applicable Seller's Guide requirements in Appendix B.

## acra-platinum.loan_amount_decisioning_score_and_cltv_limits.verify_loan_amount

**Purpose:** Determine whether the loan amount meets PLAT-1.13.

1. Check that the loan amount is within the published range.
2. Check that the loan amount is in the published increment.

**Checks:**
- loan_amount is at least $100,000 and at most $2,000,000.
- loan_amount is in $50 increments.

**Reads:** loan_amount

## acra-platinum.prepayment_penalties_and_state_restrictions.match_printed_state_prepayment_restrictions

**Purpose:** Identify whether a restriction printed for the property's state matches the case; do not interpret what “BUY-OUT” requires without the requested Acra confirmation.

1. Compare the property's state and, where stated, the loan amount, interest rate, borrower entity type, residential status and unit count, and loan purpose with the printed state conditions.
2. If a printed condition matches, record the restriction exactly as printed and obtain Acra confirmation of what “BUY-OUT” requires (Q-19). For MS, record the printed alternative “BUY-OUT or 5 year (STEP)” for all Residential 1 unit; the source states no restrictions on 2+ units.
3. Do not infer that a state not listed, or a case that does not match a listed condition, has no other prepayment restriction.

**Checks:**
- The property state is AK and the property is Residential 1-4.
- The property state is IL and the loan is to an ENTITY OR INDIVIDUAL, is Residential 1-4, and the loan amount is ≤$250,000.
- The property state is IL and the loan is to an INDIVIDUAL, is Residential 1-4, the loan amount is >$250,000, and the interest rate is >8%.
- The property state is KS and the property is Residential 1-4.
- The property state is MD.
- The property state is MI and the property is Residential 1-4.
- The property state is MN and the property is Residential 1-4.
- The property state is MS and the property is Residential 1 unit.
- The property state is NJ and the loan is closing in the name of an INDIVIDUAL.
- The property state is NM and the property is Residential 1-4.
- The property state is OH and the property is Residential 1-2.
- The property state is PA, the loan is to an INDIVIDUAL, the property is Residential 1-2, and the loan amount is <$319,777.
- The property state is RI and the transaction is a PURCHASE transaction.
- The property state is VA and the property is Residential 1-4 closed in the name of an individual.
- The property state is VT and the loan amount is <$1 Million.

**Reads:** property_state, property_type, residential_unit_count, borrower_entity_type, loan_amount, interest_rate, loan_purpose
**Missing data:** Acra confirmation of what “BUY-OUT” requires (Q-19), if a printed restriction condition matches., The actual prepayment arrangement for the case, if needed to determine whether the matched restriction is met.

## acra-platinum.prepayment_penalties_and_state_restrictions.review_listed_for_sale_prepayment_minimum

**Purpose:** Apply the prepayment-penalty requirement for a property listed for sale within the last six months, subject to the stated applicability and state-restriction qualifications.

1. Determine whether the property was listed for sale in the last six months, measured from the last date of being listed to the Application Date.
2. If listed, resolve whether §11.5 applies to Platinum Select unchanged (Q-13).
3. If §11.5 applies, determine whether the prepayment penalty is at least three (3) years, unless the property is in a state that does not allow prepayment penalties. Resolve the state-restriction interaction identified in Q-19 where needed.

**Checks:**
- The property was listed for sale in the last six months, measured from the last date of being listed to the Application Date.
- §11.5 applies to Platinum Select unchanged.
- For a listed property to which §11.5 applies, the prepayment penalty is at least three (3) years, unless the property is in a state that does not allow prepayment penalties.

**Reads:** listed_for_sale_last_6_months, property_state
**Missing data:** Acra confirmation of whether §11.5 applies to Platinum Select unchanged (Q-13), if unresolved., The selected prepayment-penalty term and whether it is at least three (3) years., Whether the property is in a state that does not allow prepayment penalties and, if relevant, Acra confirmation of how the state restriction interacts with the minimum (Q-19).

## acra-platinum.products_arm_terms_and_interest_only_terms.confirm_subordinate_financing_permission

**Purpose:** Obtain Acra confirmation because the stated denominator treatment does not establish whether subordinate financing is permitted.

1. Establish whether subordinate financing is present or proposed.
2. If it is present or proposed, obtain Acra confirmation whether subordinate financing is permitted.

**Checks:**
- If subordinate financing is present or proposed, Acra has confirmed whether it is permitted.
**Missing data:** whether subordinate financing is present or proposed, Acra confirmation whether subordinate financing is permitted

## acra-platinum.products_arm_terms_and_interest_only_terms.resolve_interest_only_minimums_and_dti_treatment

**Purpose:** Resolve the source’s open questions about interest-only minimum loan amount, minimum FICO, and the applicability of the excerpt’s DTI calculation.

1. Establish whether the loan is interest-only.
2. Obtain Acra confirmation on whether a minimum loan amount applies to interest-only loans.
3. Obtain Acra confirmation on whether a minimum FICO applies to interest-only loans.
4. If the excerpt’s DTI calculation for interest-only loans is relevant, obtain Acra confirmation on whether that DTI-program provision applies.

**Checks:**
- Acra has confirmed whether a minimum loan amount applies to interest-only loans.
- Acra has confirmed whether a minimum FICO applies to interest-only loans.
- Acra has confirmed whether the excerpt’s DTI calculation for interest-only loans applies.

**Reads:** product_is_interest_only, loan_amount, fico
**Missing data:** Acra confirmation on whether a minimum loan amount applies to interest-only loans, Acra confirmation on whether a minimum FICO applies to interest-only loans, Acra confirmation on whether the excerpt’s DTI calculation for interest-only loans applies

## acra-platinum.products_arm_terms_and_interest_only_terms.verify_arm_requirements

**Purpose:** Determine whether a 5 Yr ARM product meets the Platinum Select ARM requirements.

1. Establish whether the selected product is a 5 Yr ARM or 5 Yr ARM Interest-Only product.
2. For an ARM product, review its index and caps.
3. Compare its margin with the required margin for the borrower’s FICO tier.

**Checks:**
- The ARM index is 1 Yr CMT.
- The ARM caps are 2/2/6.
- The ARM margin is 3.00 for FICO 760+, 3.25 for FICO 720-759, or 3.50 for FICO 700-719.

**Reads:** fico
**Missing data:** loan product type, ARM index, ARM caps, ARM margin

## acra-platinum.products_arm_terms_and_interest_only_terms.verify_eligible_product_type

**Purpose:** Determine whether the loan uses a product type eligible under Platinum Select.

1. Identify the loan’s product type.
2. Establish whether it is 30 Yr Fixed, 5 Yr ARM, 30 Yr Fixed Interest-Only, or 5 Yr ARM Interest-Only.

**Checks:**
- The loan’s product type is one of: 30 Yr Fixed, 5 Yr ARM, 30 Yr Fixed Interest-Only, or 5 Yr ARM Interest-Only.
**Missing data:** loan product type

## acra-platinum.products_arm_terms_and_interest_only_terms.verify_interest_only_payment_and_dscr_treatment

**Purpose:** Determine whether the interest-only payment mechanics and DSCR treatment are established for the loan.

1. Establish whether the loan is interest-only.
2. Review the interest-only payment terms at origination and the payment terms after the interest-only term.
3. Verify that Acra calculates DSCR utilizing the first payment due under the terms of the Note.
4. For an interest-only loan, obtain Acra confirmation of which payment enters the DSCR denominator; do not infer the answer from the stated DSCR and interest-only provisions.
5. Verify that the DSCR denominator includes annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees (PITIA), and subordinate financing if applicable.

**Checks:**
- The interest-only payment at origination is the amount sufficient to pay the accrued interest on the mortgage monthly.
- After the interest-only term, payments are recast to a fully amortized payment for the balance of the term ending at maturity.
- Acra calculates DSCR utilizing the first payment due under the terms of the Note.
- For an interest-only loan, Acra has confirmed which payment enters the DSCR denominator.
- The DSCR denominator includes annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees (PITIA), and subordinate financing if applicable.

**Reads:** product_is_interest_only
**Missing data:** Note payment schedule and first payment due, interest-only payment amount and term, Acra confirmation of which payment enters the DSCR denominator for an interest-only loan, annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees, whether subordinate financing applies and, if applicable, its payment amount

## acra-platinum.products_arm_terms_and_interest_only_terms.verify_interest_only_term_and_restrictions

**Purpose:** Determine whether an interest-only loan meets the stated term and property restrictions.

1. Establish whether the loan is an interest-only product.
2. Verify that the interest-only term is 5 Yr.
3. Verify that CLTV does not exceed the stated maximum.
4. Verify that the property is not listed for sale.

**Checks:**
- The interest-only term is 5 Yr.
- CLTV is no more than 75.00%.
- The property is not listed for sale.

**Reads:** product_is_interest_only, cltv_pct, property_currently_listed_for_sale
**Missing data:** interest-only term

## acra-platinum.program_and_transaction_eligibility.borrower_citizenship

**Purpose:** Determine whether the borrower meets the published citizenship requirement.

1. Compare the borrower citizenship type with the eligible borrower categories.

**Checks:**
- The borrower is a US Citizen or Permanent Resident.

**Reads:** citizenship_type

## acra-platinum.program_and_transaction_eligibility.channel_dscr_and_rent_documentation

**Purpose:** Determine whether the loan meets the applicable minimum DSCR and the required rent-documentation requirement.

1. Identify the applicable channel minimum: Correspondent ≥ 1.2 or Wholesale ≥ 1.0.
2. Determine whether the loan meets the applicable channel minimum DSCR.
3. Confirm that a 1007 is required on the DSCR transaction.
4. If the transaction is a business purpose transaction and the borrower qualifies using the subject property's actual or market cashflow, determine whether the borrower must execute a Business Purpose Attestation (Exhibit 8) or other similar attestation approved by Acra.

**Checks:**
- The DSCR meets the applicable channel minimum.
- A 1007 is required on the DSCR transaction.
- For a business purpose transaction qualifying on the subject property's actual or market cashflow, the borrower executes a Business Purpose Attestation (Exhibit 8) or other similar attestation approved by Acra.

**Reads:** channel, dscr_documentation_type, loan_purpose
**Missing data:** The DSCR ratio used to qualify the loan., The 1007 documentation and its established market-rent amount., Whether the transaction is a business purpose transaction and whether qualification uses the subject property's actual or market cashflow., The executed Business Purpose Attestation (Exhibit 8) or other similar attestation approved by Acra, when the stated condition applies.

## acra-platinum.program_and_transaction_eligibility.investment_property_transaction_requirements

**Purpose:** Determine whether the transaction meets the stated One- to Four-Family Rider and rent loss insurance requirements.

1. Determine whether the borrower is purchasing or refinancing a one- to four-family investment property.
2. For an applicable transaction, confirm that all borrowers execute a One- to Four-Family Rider with the loan documents.
3. For an applicable transaction, confirm rent loss insurance coverage per §23.40.

**Checks:**
- For a borrower purchasing or refinancing a one- to four-family investment property, all borrowers execute a One- to Four-Family Rider with the loan documents.
- For a borrower purchasing or refinancing a one- to four-family investment property, rent loss insurance coverage is provided per §23.40.

**Reads:** loan_purpose, residential_unit_count, occupancy_subtype
**Missing data:** Whether the One- to Four-Family Rider is executed by all borrowers with the loan documents., Whether rent loss insurance coverage per §23.40 is provided.

## acra-platinum.program_and_transaction_eligibility.loan_amount_fico_and_cltv_limits

**Purpose:** Determine whether the case meets the published loan amount, minimum FICO, and maximum CLTV requirements.

1. Check that the loan amount is within the published range and in $50 increments.
2. Check the FICO against the published minimum.
3. Apply the published maximum CLTV for the loan purpose and, for cash-out, the applicable FICO condition.

**Checks:**
- The loan amount is $100,000 to $2,000,000, in $50 increments.
- The FICO is at least 700.
- CLTV does not exceed 80% for purchase or rate & term, or 75% for cash-out at FICO 730 and above.

**Reads:** loan_amount, fico, cltv_pct, loan_purpose
**Missing data:** For a delayed-financing loan, the applicable matrix CLTV column and cash-in-hand rule; the source requests Acra confirmation on these points.

## acra-platinum.program_and_transaction_eligibility.loan_purpose_eligibility

**Purpose:** Determine whether the transaction has an eligible loan purpose and whether delayed financing is within its published cap.

1. Compare the loan purpose with the eligible loan purpose types.
2. If the loan purpose is Delayed Financing, compare the loan amount with the delayed-financing cap.
3. If the transaction is a cash-out refinance, determine whether a current lease agreement is in place.

**Checks:**
- The loan purpose is Purchase, Rate & Term Refinance, Cash-Out Refinance, or Delayed Financing.
- For Delayed Financing, the loan amount does not exceed $1.5MM.
- For a Cash-Out Refinance, a current lease agreement is in place.

**Reads:** loan_purpose, loan_amount, current_lease_in_place

## acra-platinum.program_and_transaction_eligibility.occupancy_and_property_eligibility

**Purpose:** Determine whether the subject property meets the program’s occupancy, property-type, and location requirements.

1. Determine whether the property is non-owner occupied.
2. Check whether the property is vacant.
3. Compare the property type with the eligible property types.
4. Compare the property state with the ineligible locations.

**Checks:**
- The property is non-owner occupied.
- The property is not vacant.
- The property type is SFR, Townhome, PUD, Warrantable Condo, or Two-Units.
- The property is not located in SD or a U.S. Terr.

**Reads:** occupancy_subtype, vacant_property, property_type, property_state

## acra-platinum.program_and_transaction_eligibility.product_and_prepayment_eligibility

**Purpose:** Determine whether the product and prepayment terms meet the published program requirements.

1. Determine whether the selected product is one of the published eligible products.
2. Determine whether the selected prepayment structure is one of the published structures and whether the applicable state restriction is met.

**Checks:**
- The product is 30 Yr Fixed, 5 Yr ARM, 30 Yr Fixed Interest-Only, or 5 Yr ARM Interest-Only.
- The prepayment structure is 5-, 3-, 2-, 1-year structures or No Prepay, subject to the 14 state restrictions.

**Reads:** product_is_interest_only, interest_only_10_40, interest_rate, property_state, prepayment_penalty_requested
**Missing data:** The selected product type and term., The selected prepayment structure., The state-by-state details of the 14 state restrictions.

## acra-platinum.property_eligibility_and_property_specific_conditions.application_and_schedule_of_real_estate_owned

**Purpose:** Determine whether the property disclosures include the holdings the policy requires to be listed.

1. Review the application or Schedule of Real Estate Owned.
2. Confirm that the subject property, principal residence, and second homes are listed.

**Checks:**
- The subject property is listed on the application or Schedule of Real Estate Owned.
- The borrower's principal residence, if any, is listed on the application or Schedule of Real Estate Owned.
- The borrower's second homes, if any, are listed on the application or Schedule of Real Estate Owned.
**Missing data:** Application or Schedule of Real Estate Owned, Borrower's principal residence and second-home information

## acra-platinum.property_eligibility_and_property_specific_conditions.channel_dscr_and_rent_documentation

**Purpose:** Determine whether the loan meets the stated DSCR qualification and appraisal-form requirements.

1. Identify the loan channel and apply its published minimum DSCR.
2. For a DSCR transaction, verify that a Form 1007 is provided.
3. For a two-unit property, if only a Form 1025 is provided, leave acceptance unresolved pending Acra confirmation.

**Checks:**
- For a Correspondent loan, the DSCR is at least 1.2.
- For a Wholesale loan, the DSCR is at least 1.0.
- A Form 1007 is provided on a DSCR transaction.
- For a two-unit property, a Form 1025 alone is accepted only if Acra confirms it satisfies the requirement.

**Reads:** channel, property_type, residential_unit_count
**Missing data:** Actual DSCR, Form 1007, Whether a Form 1025 alone satisfies the requirement for a two-unit property, Acra confirmation regarding No Ratio or sub-1.0 qualification

## acra-platinum.property_eligibility_and_property_specific_conditions.occupancy_purpose_and_vacancy

**Purpose:** Determine whether the transaction meets the stated occupancy, purpose, and vacancy requirements.

1. Confirm the property is non-owner occupied and meets the stated investment-property definition.
2. Confirm the loan purpose is eligible and apply the delayed-financing cap when applicable.
3. For a DSCR Cash-Out Refinance, confirm a current lease agreement is in place.
4. Confirm the property is not vacant.
5. If the borrower qualifies using the subject property's actual or market cashflow under a business purpose transaction, verify the required attestation is executed with the loan documents; do not assume every loan on the program is a business-purpose transaction.

**Checks:**
- The occupancy subtype is Non-Owner Occupied.
- The property is a one- to four-unit residential dwelling or a unit in a condominium complex or a PUD.
- The dwelling is owned by an individual who does not occupy it.
- The dwelling is leased and occupied as a principal year-round residence by individuals other than the owner.
- The loan purpose is Purchase, Rate & Term Refinance, Cash-Out Refinance, or Delayed Financing.
- If the loan purpose is Delayed Financing, the loan amount is no more than $1.5MM.
- If the loan purpose is Cash-Out Refinance, a current lease agreement is in place.
- The property is not vacant.
- If the borrower qualifies using the subject property's actual or market cashflow under a business purpose transaction, a Business Purpose Attestation (Exhibit 8) or other similar attestation approved by Acra is executed with the loan documents.

**Reads:** occupancy_subtype, loan_purpose, loan_amount, current_lease_in_place, vacant_property
**Missing data:** Property configuration and residential use, Individual ownership and owner-occupancy information, Lease and year-round principal-residence occupancy information, Whether the borrower qualifies using the subject property's actual or market cashflow under a business purpose transaction, Executed Business Purpose Attestation (Exhibit 8) or other similar attestation approved by Acra, Acra confirmation whether every loan on this program is a business-purpose transaction

## acra-platinum.property_eligibility_and_property_specific_conditions.properties_listed_for_sale

**Purpose:** Determine whether a property listed for sale in the last six months meets the listed-property conditions, while preserving the stated applicability uncertainty.

1. Determine whether the property was listed for sale in the last six months, measured from the last date listed to the Application Date.
2. If it was, obtain Acra confirmation whether §11.5 applies to Platinum Select unchanged.
3. If §11.5 applies, verify lien status, tenant occupancy for investment properties, the applicable channel DSCR, prepayment-penalty rule, reserves, amortization, LTV / CLTV limit, subordinate financing, and impounds.

**Checks:**
- The property has not been listed for sale in the last six months, measured from the last date of being listed to the Application Date, or is treated as a listed property for the following checks.
- Acra confirms whether §11.5 applies to Platinum Select unchanged.
- The property is not in default or otherwise delinquent on lien(s).
- If the property is an investment property, the subject is occupied by a tenant and is not vacant.
- The loan meets the applicable channel minimum DSCR: Correspondent ≥ 1.2 or Wholesale ≥ 1.0.
- The loan has a prepayment penalty of at least three (3) years unless the property is in a state that does not allow prepayment penalties.
- Twenty-four (24) months of reserves are provided.
- The loan has a fully amortizing term and is not interest only.
- Maximum LTV / CLTV is 65% based on the lesser of appraised value or lowest recent listing price.
- No subordinate financing is present.
- Impounds are in place.

**Reads:** listed_for_sale_last_6_months, property_currently_listed_for_sale, channel, vacant_property, current_lease_in_place, reserves_months, product_is_interest_only, interest_only_10_40, cltv_pct, property_value, prepayment_penalty_requested, property_state
**Missing data:** Last date the property was listed and Application Date, Acra confirmation whether §11.5 applies to Platinum Select unchanged, Whether the property is in default or otherwise delinquent on lien(s), Tenant occupancy information, Actual DSCR, Prepayment-penalty term, Whether the property is in a state that does not allow prepayment penalties, Appraised value and lowest recent listing price, LTV, Whether subordinate financing is present, Whether impounds are in place

## acra-platinum.property_eligibility_and_property_specific_conditions.property_type_and_location_eligibility

**Purpose:** Determine whether the property's type and location meet the published requirements and identify cases the Summary does not address.

1. Compare the property type with the expressly eligible and ineligible types.
2. For a Warrantable Condo or Two-Units, apply the stated maximum CLTV.
3. Identify whether the property has a feature the Summary marks as not addressed and leave that eligibility unresolved pending Acra confirmation.
4. Check the property state against the listed ineligible locations.
5. If the property is in a declining market, apply the stated CLTV reduction and obtain clarification on how it combines with other caps.

**Checks:**
- The property type is SFR, Townhome, PUD, Warrantable Condo, or Two-Units.
- The property type is not Rural Properties, Condotels, Non-Warrantable Condos, or Short-Term Rentals.
- If the property type is Warrantable Condo or Two-Units, CLTV is no more than 75.00%.
- A three- or four-unit property, manufactured home, mixed-use property, Adult Care / Assisted Living property, or PUDtel is not treated as eligible or ineligible without Acra confirmation.
- The property state is not SD or a U.S. Terr.
- If the property is in a declining market, the stated -5% CLTV property/borrower full profile reduction is applied.
- The application of the declining-market reduction in combination with other caps is confirmed by Acra.

**Reads:** property_type, residential_unit_count, cltv_pct, property_state, rural_property, mixed_use
**Missing data:** Whether any feature not addressed by the Platinum Summary applies, Acra confirmation for features not addressed by the Platinum Summary, Whether the property is in a declining market, Property/borrower full profile information needed for the declining-market reduction, Acra confirmation on how the declining-market reduction combines with other caps

## acra-platinum.property_eligibility_and_property_specific_conditions.rider_and_rent_loss_insurance

**Purpose:** Determine whether applicable one- to four-unit non-owner occupied income-property requirements are met.

1. For a borrower purchasing or refinancing a one- to four-family investment property, verify execution of the One- to Four-Family Rider with the loan documents.
2. Determine whether the six (6) months' rent loss insurance trigger applies: the property is a one- to four-unit non-owner occupied income property, LTV is greater than 70%, and subject property rents are used to qualify.
3. Apply the stated exemption for loans with ≤ 70% CLTV and leave the LTV-at-or-below-70% / CLTV-above-70% case unresolved pending Acra confirmation.
4. If rent loss insurance is required but cannot be obtained, verify the permitted reserve substitution for each month of coverage not provided.

**Checks:**
- A borrower purchasing or refinancing a one- to four-family investment property executes a One- to Four-Family Rider with the loan documents.
- Six (6) months' rent loss insurance is provided when the property is a one- to four-unit non-owner occupied income property with LTV > 70% and subject property rents are used to qualify.
- A loan with ≤ 70% CLTV is not required to carry rent loss insurance.
- The LTV-at-or-below-70% and CLTV-above-70% case is resolved by Acra confirmation.
- When required rent loss insurance cannot be obtained, the borrower provides two (2) months reserves for every one (1) month of rent loss coverage not provided.

**Reads:** occupancy_subtype, residential_unit_count, loan_purpose, cltv_pct, gross_rental_income, reserves_months
**Missing data:** Whether the property is an income property, Executed One- to Four-Family Rider, LTV, Whether subject property rents are used to qualify, Rent loss insurance coverage obtained, Acra confirmation for the LTV-at-or-below-70% and CLTV-above-70% case, Months of rent loss coverage not provided, Reserves available for the permitted substitution
