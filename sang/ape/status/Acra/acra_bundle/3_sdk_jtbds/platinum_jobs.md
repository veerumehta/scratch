# Our jobs, platinum (110)

## acra-platinum.appraisal_review.actual_rent_lease_term

**Purpose:** Verify the lease-duration requirement for actual rent used in qualifying.

1. Initial Document Review: Review the lease agreement and identify the loan closing date and lease end date.
2. Eligibility Verification: Determine whether actual rent is being used and whether the rent is for a long-term rental.
3. Validation and Verification: Verify that the lease is in place for at least 3 months after the loan closing.
4. Final Determination: Record whether the lease meets the stated duration requirement.

**Checks:**
- Actual rent is being used for a long-term rental.
- The lease is in place for at least 3 months after the loan closing.
**Missing data:** Whether actual rent is being used, Whether the rental is long-term, Lease end date, Loan closing date

## acra-platinum.appraisal_review.actual_rent_receipts

**Purpose:** Verify the evidence of actual rent receipts required when actual rent is used.

1. Initial Document Review: Review bank statements and other rent evidence in the file.
2. Eligibility Verification: Determine whether actual rent is being used and whether the rent is for a long-term rental.
3. Validation and Verification: Verify that evidence documents 2 months’ proof of receipts.
4. Final Determination: Record whether the required proof of receipts is documented.

**Checks:**
- Actual rent is being used for a long-term rental.
- Evidence documents 2 months’ proof of receipts.
**Missing data:** Whether actual rent is being used, Whether the rental is long-term, Evidence of 2 months’ proof of receipts

## acra-platinum.appraisal_review.cash_out_refinance_lease

**Purpose:** Verify the current lease agreement requirement for cash-out refinances.

1. Initial Document Review: Review the file for a lease agreement for the subject property.
2. Eligibility Verification: Determine whether the loan purpose is cash-out refinance.
3. Validation and Verification: If applicable, verify that a current lease agreement is provided.
4. Final Determination: Record whether the required current lease agreement is provided.

**Checks:**
- The loan purpose is cash-out refinance.
- A current lease agreement is provided.

**Reads:** LoanCore.loan_purpose
**Missing data:** Whether a current lease agreement is provided, Whether the lease agreement is current

## acra-platinum.appraisal_review.excessive_lease_rent_support

**Purpose:** Verify the required support for monthly rent reflected on the lease as typical for the area.

1. Initial Document Review: Review the lease agreement for monthly rent payments and supporting rent documentation.
2. Eligibility Verification: Determine whether the subject property is a single family investment property and the lease reflects excessive monthly rent payments.
3. Validation and Verification: If applicable, verify that documentation supports that the monthly rent is typical for the area. Acceptable documentation may include classified ads from local newspapers, a 1007 completed by the appraiser, or a market rent survey completed by a local real estate company or rental management company familiar with the market rents in the area.
4. Final Determination: Record whether the required support is documented.

**Checks:**
- The subject property is a single family investment property and the lease reflects excessive monthly rent payments.
- Documentation supports that the monthly rent is typical for the area.

**Reads:** SubjectProperty.property_type, SubjectProperty.occupancy_subtype
**Missing data:** Whether the subject property is an investment property, Whether the lease reflects excessive monthly rent payments, Whether the monthly rent is typical for the area

## acra-platinum.appraisal_review.qualifying_rent_selection

**Purpose:** Verify the rent amount used to calculate the DSCR.

1. Initial Document Review: Review the appraisal report and any lease agreement or rent roll documenting rent for the subject property.
2. Eligibility Verification: Determine whether the loan is a DSCR transaction.
3. Validation and Verification: Verify that the DSCR uses the greater of market rent as established on the 1007 or 1025, or actual rent.
4. Final Determination: Record whether the rent used for the DSCR meets the stated requirement.

**Checks:**
- The DSCR uses the greater of market rent as established on the 1007 or 1025, or actual rent.

**Reads:** LoanCore.dscr_qualification_method
**Missing data:** Market rent established on the 1007 or 1025, Actual rent, Rent amount used to calculate the DSCR

## acra-platinum.appraisal_review.short_term_rental_eligibility

**Purpose:** Determine whether the property meets the program’s short-term rental eligibility requirement.

1. Initial Document Review: Review available lease agreements and rent evidence for the subject property.
2. Eligibility Verification: Determine whether the subject property is a short-term rental.
3. Validation and Verification: Verify the rental term from the reviewed evidence.
4. Final Determination: Record whether the subject property is eligible under the short-term rental requirement.

**Checks:**
- The subject property is not a short-term rental.
**Missing data:** Whether the subject property is a short-term rental, Rental term

## acra-platinum.appraisal_review.single_family_rent_schedule

**Purpose:** Verify the required FNMA Form 1007 for applicable single family properties.

1. Initial Document Review: Review the appraisal report for the Single-Family Comparable Rent Schedule (FNMA Form 1007).
2. Eligibility Verification: Determine whether the subject property is single family and whether any of the stated triggers applies: the file qualifies using DSCR; the transaction is a lease-option purchase and the down payment required in §3.45 is generated from excess monthly rent contributions; or proposed rental income is being used to qualify.
3. Validation and Verification: If a trigger applies, verify that Form 1007 is provided. Verify that it is from the original appraiser or any state licensed appraiser.
4. Final Determination: Record whether the required Form 1007 is provided and meets the stated requirement.

**Checks:**
- The subject property is single family.
- The file qualifies using DSCR, or the transaction is a lease-option purchase and the down payment required in §3.45 is generated from excess monthly rent contributions, or proposed rental income is being used to qualify.
- When a trigger applies, Form 1007 is provided.
- The Form 1007 is from the original appraiser or any state licensed appraiser.

**Reads:** SubjectProperty.property_type, LoanCore.dscr_qualification_method
**Missing data:** Whether the transaction is a lease-option purchase, Whether the down payment required in §3.45 is generated from excess monthly rent contributions, Whether proposed rental income is being used to qualify, Whether Form 1007 is provided, Whether Form 1007 is from the original appraiser or a state licensed appraiser

## acra-platinum.asset_assessment.cltv_over_75_reserves

**Purpose:** Assess the stated reserve trigger for loans with CLTV > 75.00%.

1. Initial Document Review: Review bank statements for reserve information.
2. Eligibility Verification: Determine whether CLTV is > 75.00%.
3. Validation and Verification: If triggered, verify six months of reserves.
4. Final Determination: Record whether the stated reserve requirement is met.

**Checks:**
- When CLTV is > 75.00%, six months of reserves are available.

**Reads:** LoanCore.cltv_percent, RatioSet.reserves_months
**Missing data:** Verified reserve amount expressed in months

## acra-platinum.asset_assessment.funds_to_close_seasoning_verification

**Purpose:** Assess the stated funds-to-close verification triggers and the minimum 30-days documentation requirement.

1. Initial Document Review: Review the bank statement for the most recent month(s) and identify the source account(s) for funds to close.
2. Eligibility Verification: Determine whether the transaction is a consumer transaction, or a business purpose loan where funds to close are over $50,000 and CLTV is over 70%. Whether any loan on this program is a consumer transaction is unresolved in the source.
3. Validation and Verification: Where account(s) serving as the source of funds must be verified, review bank statement(s) for the most recent month(s), or a VOD reflecting a current and average balance for the most recent month(s). Verify that all transactions have a minimum of 30-days documentation.
4. Final Determination: Record whether the applicable funds-to-close verification and minimum documentation requirements are met.

**Checks:**
- Seasoning of funds to close is verified on loans over 70% CLTV for consumer transactions, or on business purpose loans where funds to close are over $50,000 and over 70% CLTV.
- All transactions have a minimum of 30-days documentation.

**Reads:** LoanCore.cltv_percent
**Missing data:** Whether the transaction is a consumer transaction, Whether the loan is a business purpose loan, Amount of funds to close, Account(s) serving as the source of funds, Documentation covering at least 30-days

## acra-platinum.asset_assessment.investment_property_gift_contribution

**Purpose:** Assess the stated own-funds contribution requirement for investment-property gift funds.

1. Initial Document Review: Review the loan application and bank statement for information about the applicants' contribution to the transaction.
2. Eligibility Verification: Determine whether the transaction is for an investment property.
3. Validation and Verification: Verify that applicants contribute a portion of their own sourced and seasoned funds equal to at least 10% of the purchase price.
4. Final Determination: Record whether the stated own-funds contribution requirement is met.

**Checks:**
- For an investment property, applicants contribute their own sourced and seasoned funds equal to at least 10% of the purchase price.

**Reads:** SubjectProperty.occupancy_subtype
**Missing data:** Purchase price, Amount of applicants' own funds contributed, Evidence that contributed funds are the applicants' own sourced and seasoned funds

## acra-platinum.asset_assessment.listed_property_amortization

**Purpose:** Assess the stated loan-term characteristics for properties considered under §11.5.

1. Initial Document Review: Review the loan application for the loan's amortization terms.
2. Eligibility Verification: Determine whether the property is considered under the listed-property requirements.
3. Validation and Verification: Verify that the loan has a fully amortizing term and is not interest only.
4. Final Determination: Record whether both stated loan-term characteristics are met.

**Checks:**
- The loan has a fully amortizing term and is not interest only.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, MortgageLoanInformation.is_interest_only
**Missing data:** Whether the loan has a fully amortizing term

## acra-platinum.asset_assessment.listed_property_financing_and_impounds

**Purpose:** Assess the stated subordinate-financing and impound characteristics for properties considered under §11.5.

1. Initial Document Review: Review the title commitment and loan application for subordinate financing and impound information.
2. Eligibility Verification: Determine whether the property is considered under the listed-property requirements.
3. Validation and Verification: Verify that there is no subordinate financing and that impounds are required.
4. Final Determination: Record whether both stated characteristics are met.

**Checks:**
- There is no subordinate financing.
- Impounds are required.

**Reads:** SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Whether subordinate financing exists, Whether impounds are required for the loan

## acra-platinum.asset_assessment.listed_property_ltv_and_cltv

**Purpose:** Assess the stated LTV / CLTV limit and valuation basis for properties considered under §11.5.

1. Initial Document Review: Review the appraisal report and listing history for valuation information.
2. Eligibility Verification: Determine whether the property is considered under the listed-property requirements.
3. Validation and Verification: Verify that maximum LTV / CLTV is 65% based on the lesser of appraised value or lowest recent listing price.
4. Final Determination: Record whether the stated maximum is met using the required valuation basis.

**Checks:**
- Maximum LTV / CLTV is 65% based on the lesser of appraised value or lowest recent listing price.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.appraised_value_usd, LoanCore.cltv_percent
**Missing data:** LTV, Lowest recent listing price

## acra-platinum.asset_assessment.listed_property_occupancy

**Purpose:** Assess the stated occupancy and vacancy characteristics for an investment property considered under §11.5.

1. Initial Document Review: Review the lease agreement or rent roll for tenant occupancy information.
2. Eligibility Verification: Determine whether the property is an investment property considered under the listed-property requirements.
3. Validation and Verification: Verify that the subject is occupied by a tenant and is not vacant.
4. Final Determination: Record whether both occupancy characteristics are met.

**Checks:**
- For an investment property considered under the listed-property requirements, the subject is occupied by a tenant and is not vacant.

**Reads:** SubjectProperty.occupancy_subtype, SubjectProperty.is_vacant, SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Whether a tenant occupies the subject property

## acra-platinum.asset_assessment.listed_property_prepayment_penalty

**Purpose:** Assess the stated prepayment penalty requirement for properties considered under §11.5.

1. Initial Document Review: Review the loan application for the prepayment penalty structure.
2. Eligibility Verification: Determine whether the property is considered under the listed-property requirements and identify the property's state.
3. Validation and Verification: Verify that the prepayment penalty is at least three (3) years unless the property is in a state that does not allow prepayment penalties.
4. Final Determination: Record whether the stated penalty requirement or exception is met.

**Checks:**
- The prepayment penalty is at least three (3) years unless the property is in a state that does not allow prepayment penalties.

**Reads:** LoanCore.prepayment_penalty_structure, SubjectProperty.state, SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Whether the property's state does not allow prepayment penalties

## acra-platinum.asset_assessment.listed_property_qualification

**Purpose:** Assess the stated qualification alternatives for properties considered under §11.5.

1. Initial Document Review: Review the loan application and rent roll for qualification information.
2. Eligibility Verification: Determine whether the property is considered under the listed-property requirements and identify the loan channel.
3. Validation and Verification: Verify qualification by either DSCR of at least 1.0, with the channel minimum DSCR applying (Wholesale 1.0 and Correspondent 1.2), or the 43% maximum DTI alternative.
4. Final Determination: Record whether either stated qualification alternative is met.

**Checks:**
- The loan qualifies by either the applicable channel minimum DSCR or the 43% maximum DTI alternative.

**Reads:** LoanCore.channel, SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Calculated DSCR, Whether the loan meets the applicable channel minimum DSCR, DTI, Whether the DTI alternative applies to this program

## acra-platinum.asset_assessment.listed_property_reserves

**Purpose:** Assess the stated reserve requirement for properties considered under §11.5.

1. Initial Document Review: Review bank statements for reserve information.
2. Eligibility Verification: Determine whether the property is considered under the listed-property requirements.
3. Validation and Verification: Verify that twenty-four (24) months of reserves are available; cash-in-hand may be considered if otherwise consistent with the Guide.
4. Final Determination: Record whether the stated reserve requirement is met.

**Checks:**
- Twenty-four (24) months of reserves are available, with cash-in-hand considered only if otherwise consistent with the Guide.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
**Missing data:** Verified reserve amount expressed in months, Whether cash-in-hand is otherwise consistent with the Guide

## acra-platinum.asset_assessment.listed_property_status

**Purpose:** Determine the listed-for-sale status used by the stated §11.5 requirements.

1. Initial Document Review: Review listing history for the property's listing dates.
2. Eligibility Verification: Determine whether the property was listed for sale in the last six months, measured from the last date of being listed to the Application Date.
3. Validation and Verification: Compare the listing history with the Application Date.
4. Final Determination: Record whether the property meets the stated listed-for-sale definition.

**Checks:**
- The property was listed for sale in the last six months, measured from the last date of being listed to the Application Date.

**Reads:** SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Last date the property was listed for sale, Application Date

## acra-platinum.asset_assessment.loan_amount_requirements

**Purpose:** Determine whether the loan amount and, where applicable, CLTV meet PLAT-1.13 and PLAT-1.14.

1. Initial Document Review: Review the loan application for the requested loan amount.
2. Eligibility Verification: Determine whether the loan amount is at least $100,000 and no more than $2,000,000, and is in $50 increments.
3. Validation and Verification: For a loan amount below $350,000 or above $1,500,000, verify that CLTV does not exceed 75.00%.
4. Final Determination: Record whether the applicable loan amount and CLTV requirements are met.

**Checks:**
- The loan amount is at least $100,000, no more than $2,000,000, and in $50 increments.
- If the loan amount is below $350,000 or above $1,500,000, CLTV is no more than 75.00%.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.cltv_percent

## acra-platinum.asset_assessment.recent_forbearance_or_mortgage_lates_reserves

**Purpose:** Assess the reserve provision stated for tenant-occupied subjects with forbearance or mortgage lates in the last 12 months, without timely receipt of the prior two months' rent.

1. Initial Document Review: Review the lease agreement, rent roll, and bank statement for tenant occupancy, rent receipts, and reserves.
2. Eligibility Verification: Determine whether the subject is tenant occupied and whether forbearance or mortgage lates occurred within the last 12 months.
3. Validation and Verification: If the prior two months' rent were not timely received, verify 12 months of the subject's payment in reserve; this may be from the transaction's cash-in-hand.
4. Final Determination: Record whether the stated reserve provision is met. The source does not resolve how this provision relates to the required “0x30x12” housing history or which cases it covers.

**Checks:**
- For a tenant-occupied subject with forbearance or mortgage lates within the last 12 months and without timely receipt of the prior two months' rent, 12 months of the subject's payment are in reserve; cash-in-hand may be used.

**Reads:** SubjectProperty.occupancy_subtype, SubjectProperty.is_vacant, CreditReport.housing_history_rating
**Missing data:** Whether forbearance occurred within the last 12 months, Whether mortgage lates occurred within the last 12 months, Subject's payment amount, Whether the prior two months' rent were timely received, Verified reserve amount in months of the subject's payment, Whether transaction cash-in-hand is available

## acra-platinum.asset_assessment.rent_loss_insurance

**Purpose:** Assess whether rent loss insurance is required and, when required, whether the stated coverage is provided.

1. Initial Document Review: Review the hazard insurance declarations for rent loss insurance coverage.
2. Eligibility Verification: Determine whether the property is a one- to four-unit non-owner occupied income property, whether LTV is greater than 70%, and whether subject property rents are used to qualify. Apply the stated exemption that loans with ≤ 70% CLTV are not required to carry rent loss insurance.
3. Validation and Verification: If the requirement applies, verify six (6) months' rent loss insurance coverage.
4. Final Determination: Record whether required coverage is provided or the stated CLTV exemption applies.

**Checks:**
- Six (6) months' rent loss insurance is provided when the property is a one- to four-unit non-owner occupied income property with LTV > 70% and subject property rents are used to qualify, except that loans with ≤ 70% CLTV are not required to carry rent loss insurance.

**Reads:** SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype, LoanCore.cltv_percent
**Missing data:** LTV, Whether subject property rents are used to qualify, Whether the property is an income property

## acra-platinum.asset_assessment.rent_loss_insurance_reserve_substitute

**Purpose:** Assess the stated reserve substitution when required rent loss insurance cannot be obtained.

1. Initial Document Review: Review hazard insurance declarations and bank statements for coverage and reserves.
2. Eligibility Verification: Determine whether rent loss insurance is required and cannot be obtained.
3. Validation and Verification: Verify two (2) months reserves for every one (1) month of rent loss coverage not provided.
4. Final Determination: Record whether the stated reserve substitution is met.

**Checks:**
- When required rent loss insurance cannot be obtained, reserves equal two (2) months for every one (1) month of coverage not provided.

**Reads:** SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype, LoanCore.cltv_percent, RatioSet.reserves_months
**Missing data:** Whether required rent loss insurance cannot be obtained, Months of rent loss coverage not provided, Verified reserve amount expressed in months

## acra-platinum.compliance_and_closing.cash_out_lease_verification

**Purpose:** Establish the current-lease requirement for DSCR Cash-Out Refinance Transactions.

1. Initial Document Review: Review the lease agreement for the subject property.
2. Eligibility Verification: Determine whether the loan is a Cash-Out Refinance qualifying using DSCR.
3. Validation and Verification: Verify that the lease agreement is current.
4. Final Determination: Determine whether the current-lease requirement is met.

**Checks:**
- A current lease agreement is present for a DSCR Cash-Out Refinance transaction.

**Reads:** LoanCore.loan_purpose, LoanCore.dscr_qualification_method
**Missing data:** Whether the transaction qualifies using DSCR., Whether the lease agreement is current., Whether the lease agreement is current

## acra-platinum.compliance_and_closing.entity_documentation_package

**Purpose:** Establish that the required entity documentation has been provided without exception, subject to the stated EIN exception process and Legal's right to condition for additional documentation.

1. Initial Document Review: Collect and review the entity's formation documents and amendments; Operating Agreement with referenced exhibits for LLCs and Partnerships or Bylaws for corporations and amendments; ownership-interest evidence; applicable stock certificates, stock ledger, K-1 statements, CPA or Tax Preparer letter, and Affidavit of Lost Stock Certificate; identification; Certificate of Good Standing or equivalent; applicable foreign qualification; IRS Form SS4, TIN, or EIN issuance letter; Unanimous Written Consent / Board Resolution; and any required Power of Attorney.
2. Eligibility Verification: Confirm the required documents are provided without relying on borrower letters stating that documents are not required, available, or excused. Confirm that applicable Operating Agreements or Bylaws state whether the entity is member or manager managed, authorize borrowing money and entering into contracts for mortgage assets, and designate signers.
3. Validation and Verification: Verify legibility, completeness, required ownership information, matching names or a letter of explanation, Certificate of Good Standing validity within ninety (90) days of the closing date, applicable foreign qualification, and the required authorization and signer information. Apply the stated ownership-evidence requirements for LLCs, Partnerships, S or C Corporations, and the stated S-corporation or Partnership fallback when both stock certificate and stock ledger are unavailable. An EIN exception request may be submitted for review by Acra's Legal Department with a letter of explanation stating the applicable grounds. Do not use a Unanimous Written Consent / Board Resolution to designate a signor on a personal guarantee. Obtain a Power of Attorney when a principal designates an attorney in fact to execute a personal guarantee. Refer additional supporting-documentation requests to Legal as applicable.
4. Final Determination: Determine whether the required entity documentation has been provided and meets the applicable stated requirements.

**Checks:**
- The required entity documents are provided, complete, legible, and satisfy the applicable content, ownership, name, timing, qualification, authorization, and signer requirements.

**Reads:** Borrower.entity_documents_complete, Borrower.entity_type
**Missing data:** The applicable entity type and document requirements; the documents and amendments provided; their legibility and contents; identity-name comparison; closing date; ownership evidence; and whether an EIN exception request or Power of Attorney applies.

## acra-platinum.compliance_and_closing.entity_due_diligence_currency

**Purpose:** Establish the required currency and scope of borrower / guarantor due diligence.

1. Initial Document Review: Review the due-diligence records and the loan approval or draw date.
2. Eligibility Verification: Identify the Key Principals and Entities that must be covered: for entity borrowers, the entity, recourse guarantor(s), and any party that owns 20% or more of the entity directly or indirectly or has managing control; for individual borrowers, all such individuals.
3. Validation and Verification: Verify that borrower / guarantor due diligence is current as of the date of any loan approval or draw. Review the background checks if ordered, including their stated scope.
4. Final Determination: Determine whether the required due diligence is current and covers the applicable parties.

**Checks:**
- Borrower / Guarantor Due Diligence is current as of the date of any loan approval or draw.
- The due-diligence review covers the applicable Key Principals and Entities.

**Reads:** Borrower.entity_type
**Missing data:** Loan approval or draw date; due-diligence dates and results; borrower type; ownership percentages and control; and the parties covered by the review.

## acra-platinum.compliance_and_closing.entity_guarantor_requirements

**Purpose:** Establish the entity-borrower guarantor requirements.

1. Initial Document Review: Review entity ownership documents, the application, and recourse guarantees.
2. Eligibility Verification: Identify all individuals with direct or indirect ownership ≥ 20% of the entity and identify the guarantors.
3. Validation and Verification: Verify that each identified individual provides an Acra approved guarantee or Exhibit 7; where there are multiple guarantors, verify that recourse is joint and several. Verify that at least one borrower / guarantor attests on the application that they are not a first-time homebuyer; if prior home ownership is not evident within the loan file, condition for supporting documentation as permitted by the guideline.
4. Final Determination: Determine whether the guarantor requirements are met.

**Checks:**
- All individuals with direct or indirect ownership ≥ 20% provide an Acra approved guarantee or Exhibit 7.
- Recourse is joint and several when there are multiple guarantors.
- At least one guarantor has prior homeownership experience, with the required application attestation and supporting documentation when prior home ownership is not evident within the loan file.

**Reads:** Borrower.is_first_time_homebuyer, Borrower.entity_type
**Missing data:** Ownership percentages and whether ownership is direct or indirect., Guarantee documents and whether multiple guarantors have joint and several recourse., The application attestation and, if prior home ownership is not evident within the loan file, supporting documentation.

## acra-platinum.compliance_and_closing.entity_spe_and_ownership_structure

**Purpose:** Establish the stated entity structure requirements for an entity borrower.

1. Initial Document Review: Review entity documents and the ownership structure.
2. Eligibility Verification: Determine whether the entity is a single purpose entity engaged in owning and operating residential investment or rental properties and has no assets other than residential investment or rental properties.
3. Validation and Verification: Verify that every entity holding direct ownership of the subject property and appearing on title as a direct owner is a borrowing entity; verify that any entity nesting is limited to one wholly-owned subsidiary owned by individual(s), with no multiple nesting or ownership by multiple entities, trusts, etcetera.
4. Final Determination: Determine whether the entity structure requirements are met.

**Checks:**
- The entity has no assets other than residential investment or rental properties and is engaged in the business of owning and operating residential investment or rental properties.
- Every entity holding direct ownership of the subject property and appearing on title as a direct owner is a borrowing entity.
- Business entity nesting is limited to only one (1) wholly-owned subsidiary that in turn is owned by individual(s); there is no multiple nesting or ownership by multiple entities, trusts, etcetera.

**Reads:** Borrower.entity_type, Borrower.entity_documents_complete
**Missing data:** Entity assets and business activities., Direct property ownership, title-holding entities, and entity borrowing status., The complete entity ownership and nesting structure.

## acra-platinum.compliance_and_closing.entity_type_eligibility

**Purpose:** Determine whether the entity borrower meets the stated entity-type requirements.

1. Initial Document Review: Review entity documents for the entity's type, formation, and ownership.
2. Eligibility Verification: Compare the entity type with the allowed and not-allowed types stated in the guidelines.
3. Validation and Verification: Verify from the entity documents that the entity is US formed and based and is not a foreign owned entity.
4. Final Determination: Determine whether the entity meets the stated entity-type requirements.

**Checks:**
- The entity type is one of the allowed types and is not a series LLC, Cooperative, Irrevocable Trust, Land Trust, IRA, Non-Profit, or Joint Venture.
- The entity is US formed and based and is not a foreign owned entity.

**Reads:** Borrower.entity_type
**Missing data:** Entity formation and ownership evidence establishing whether it is US formed and based and whether it is foreign owned.

## acra-platinum.compliance_and_closing.escrow_waiver_eligibility

**Purpose:** Apply the stated escrow-waiver requirements without adding a CLTV or FICO limit.

1. Initial Document Review: Review loan amount, mortgage history, and any available information about Section 35 eligibility.
2. Eligibility Verification: Determine whether the requested escrow waiver is subject to the stated escrow-waiver requirements.
3. Validation and Verification: Verify the loan amount does not exceed $1.5M and that 0x30x24 Mortgage History is met; determine whether the loan is a Section 35 loan.
4. Final Determination: Determine whether the stated escrow-waiver requirements are met. Do not apply a CLTV or FICO limit not printed for the Platinum waiver.

**Checks:**
- LoanCore.total_loan_amount_usd is no more than $1.5M.
- The required 0x30x24 Mortgage History is met.
- The loan is not a Section 35 loan.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.is_escrow_waived, CreditReport.mortgage_0x30x24
**Missing data:** Mortgage history evidence establishing 0x30x24 Mortgage History; whether the loan is a Section 35 loan (Section 35 is not defined in the sources).

## acra-platinum.compliance_and_closing.funds_documentation_minimum

**Purpose:** Apply the minimum documentation requirement stated for all transactions.

1. Initial Document Review: Review the documentation for funds to close.
2. Eligibility Verification: Apply the requirement to the transaction.
3. Validation and Verification: Verify that the documentation covers a minimum of 30 days.
4. Final Determination: Determine whether the minimum documentation requirement is met.

**Checks:**
- Documentation for funds to close covers a minimum of 30 days.
**Missing data:** The funds-to-close documentation and the dates it covers.

## acra-platinum.compliance_and_closing.investment_gift_funds_contribution

**Purpose:** Apply the minimum own-funds contribution requirement for investment-property gift funds.

1. Initial Document Review: Review documentation of funds contributed to the transaction and the purchase price.
2. Eligibility Verification: Determine whether gift funds are being used for an investment-property transaction.
3. Validation and Verification: Verify the applicant(s) contribute a portion of their own sourced and seasoned funds at a minimum of 10% of the purchase price.
4. Final Determination: Determine whether the minimum own-funds contribution requirement is met.

**Checks:**
- The applicant(s) contribute their own sourced and seasoned funds to the transaction in an amount of at least 10% of the purchase price.

**Reads:** LoanCore.loan_purpose, SubjectProperty.occupancy_subtype
**Missing data:** Purchase price; amount of applicant-contributed funds; source and seasoning evidence for those funds; and whether gift funds are used.

## acra-platinum.compliance_and_closing.listed_property_requirements

**Purpose:** Determine whether the loan meets the stated §11.5 requirements for a property listed for sale in the last six months.

1. Initial Document Review: Review the listing history, lien status, occupancy, qualification, loan terms, reserves, value, financing, and impound information.
2. Eligibility Verification: Determine whether the property has been listed for sale in the last six months, measured from the last date of being listed to the Application Date.
3. Validation and Verification: For an applicable property, verify it is not in default or otherwise delinquent on lien(s); for an investment property, verify it is occupied by a tenant and is not vacant; verify qualification as either ≥ 1.0 DSCR or 43% maximum DTI, applying the channel minimum DSCR of Wholesale 1.0 and Correspondent 1.2; verify twenty-four (24) months of reserves; a fully amortizing term and no interest only; maximum LTV / CLTV of 65% based on the lesser of appraised value or lowest recent listing price; no subordinate financing; and impounds. Cash-in-hand may be considered if otherwise consistent with the Guide.
4. Final Determination: Determine whether the applicable listed-property requirements are met. The source states that whether §11.5 applies to Platinum Select unchanged is part of Q-13; the DTI alternative is Q-14.

**Checks:**
- The property has been listed for sale in the last six months measured from the last date of being listed to the Application Date, or the job is not applicable.
- The property is not in default or otherwise delinquent on lien(s).
- If the property is an investment property, it is occupied by a tenant and is not vacant.
- The loan qualifies as either ≥ 1.0 DSCR or 43% maximum DTI, applying the channel minimum DSCR of Wholesale 1.0 and Correspondent 1.2.
- The loan has twenty-four (24) months of reserves.
- The loan has a fully amortizing term and is not interest only.
- LTV / CLTV is no more than 65% based on the lesser of appraised value or lowest recent listing price.
- There is no subordinate financing.
- Impounds are in place.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_vacant, SubjectProperty.has_current_lease, LoanCore.channel, LoanCore.cltv_percent, LoanCore.is_interest_only_10_40, MortgageLoanInformation.is_interest_only, SubjectProperty.appraised_value_usd, RatioSet.reserves_months
**Missing data:** Application Date and last date listed; lien default or delinquency status; tenant occupancy; DSCR or DTI qualification and the applicable program channel minimum; lowest recent listing price; subordinate financing; and impound status.

## acra-platinum.compliance_and_closing.prepayment_penalty_requirements

**Purpose:** Apply the printed prepayment penalty structures, the listed-property minimum, and the state restrictions as printed.

1. Initial Document Review: Review the selected prepayment penalty structure, property listing history, state, property type, unit count, loan purpose, borrower/entity status, loan amount, and interest rate.
2. Eligibility Verification: Determine whether the property was listed for sale within six months and whether a printed state restriction applies.
3. Validation and Verification: Verify that a property listed for sale within six months has a prepayment penalty of at least three (3) years unless it is in a state that does not allow prepayment penalties. Compare the selected structure with the structures printed for 5 Year, 3 Year, 2 Year, 1 Year, and No Prepay. Apply the state restrictions using their exact printed wording; do not infer what BUY-OUT requires. The source asks for Acra confirmation about availability of a 4-year structure and how a state restriction interacts with the three-year minimum.
4. Final Determination: Determine whether the selected structure meets the applicable stated requirements, and flag unresolved Acra confirmation questions rather than resolving them by assumption.

**Checks:**
- If the property was listed for sale within six months, the prepayment penalty is at least three (3) years unless the property is in a state that does not allow prepayment penalties.
- The selected structure is one of the structures printed: 5 Year 5% Fixed (5% / 5% / 5% / 5% / 5%) or Sequential Stepdown (5% / 4% / 3% / 2% / 1%); 3 Year 5% Fixed (5% / 5% / 5%) or 3% Fixed (3% / 3% / 3%); 2 Year 3% Fixed (3% / 3%); 1 Year 3% Fixed (3%); or No Prepay.
- The selected prepayment structure complies with the restriction printed for the subject property's state, property type, unit count, transaction, borrower/entity status, loan amount, and interest rate, as applicable.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.state, SubjectProperty.property_type, SubjectProperty.number_of_units, LoanCore.loan_purpose, Borrower.entity_type, LoanCore.total_loan_amount_usd, LoanCore.note_rate_percent, LoanCore.prepayment_penalty_structure
**Missing data:** Whether the property is in a state that does not allow prepayment penalties; the exact selected structure and term; whether the property was listed for sale within six months; and, where relevant, transaction and borrower/entity details. The meaning of BUY-OUT and the interaction between state restrictions and the three-year minimum require Acra confirmation.

## acra-platinum.compliance_and_closing.revocable_trust_vesting

**Purpose:** Determine whether title vesting in an inter vivos revocable trust is permitted under the stated requirements.

1. Initial Document Review: Review the complete, legible Trust or Certification of Trust and any written Acra Senior Management exception.
2. Eligibility Verification: Verify the Trust is valid under the laws of the state in which it is established, revocable, established by one or more natural persons, and effective during the lifetime of the person(s) establishing it; verify that the primary beneficiary is the individual(s) establishing the Trust.
3. Validation and Verification: Verify the Trust or Certification of Trust includes every stated item: existence and date; Trustor(s) and current Trustee(s); Trustee powers; revocability and who holds the right to revoke; required number and names of signing Trustees; Trust identification number; how title to Trust assets is taken; and a statement that the Trust has not been revoked, modified, or amended. Verify the stated mortgage, beneficiary-consent, lender-risk, and creditor-rights provisions. Obtain written exception by Acra Senior Management if the Trustor(s) and Trustee(s) are not the same. Note that Legal reserves the right to condition for additional supporting documentation.
4. Final Determination: Determine whether all stated requirements for permitted trust vesting are met.

**Checks:**
- The Trust or Certification of Trust contains all required information and statements.
- The Trust is valid under the laws of the state in which it is established, is revocable, and is established by one or more natural persons and effective during their lifetime.
- The primary beneficiary is the individual(s) establishing the Trust.
- If the Trustor(s) and Trustee(s) are not the same, written exception by Acra Senior Management has been obtained.
- The Trust specifies the required Trustee power, beneficiary-consent, lender-risk, and creditor-rights provisions.

**Reads:** Borrower.entity_type
**Missing data:** Trust and Certification of Trust contents; state-law validity; Trustor(s), Trustee(s), beneficiaries, and signing requirements; and any written Acra Senior Management exception.

## acra-platinum.compliance_and_closing.vacant_property_eligibility

**Purpose:** Apply the requirement that vacant properties are ineligible.

1. Initial Document Review: Review the subject-property occupancy information.
2. Eligibility Verification: Determine whether the subject property is vacant.
3. Validation and Verification: Compare the vacancy status with the case field.
4. Final Determination: Treat a vacant property as ineligible.

**Checks:**
- SubjectProperty.is_vacant is false.

**Reads:** SubjectProperty.is_vacant

## acra-platinum.credit_review_analysis.decisioning_score

**Purpose:** Determine the credit score used for decisioning under the program's stated rules.

1. Step 1 - Initial Document Review: Review the credit_report and, for an entity loan, entity_documents for the borrowers' and personal guarantors' credit scores and ownership percentages. Review the loan_application for income and borrower information.
2. Step 2 - Eligibility Verification: For a non-entity loan, identify the Primary Wage Earner and that person's middle score. For a loan closing in the name of an entity, use the highest middle score of the personal guarantors if ownership percentages are equal; if they differ, use the individual with the highest concentration of ownership.
3. Step 3 - Validation and Verification: Where there is one score, two scores, no income documentation to identify the Primary Wage Earner, or two or more guarantors with an equal largest ownership interest and ownership not equal across all guarantors, do not infer a score-selection rule not stated in the source.
4. Step 4 - Final Determination: Record the decisioning score only when it can be established under the stated rule; otherwise record that the source does not resolve the score-selection issue.

**Checks:**
- The decisioning score is established using the applicable stated rule: the Primary Wage Earner's middle score, or the entity guarantor score rule where applicable.

**Reads:** Borrower.entity_type, Borrower.entity_documents_complete, Borrower.is_entity_borrower_1, CreditReport.score_count, CreditReport.representative_score
**Missing data:** Individual middle scores, Primary Wage Earner identification, Guarantor ownership percentages, Confirmation of the decisioning score for one-score or two-score files, files with no income documentation, and equal-largest-ownership ties

## acra-platinum.credit_review_analysis.escrow_waiver

**Purpose:** Determine whether an escrow waiver meets the requirements stated for the Platinum waiver.

1. Step 1 - Initial Document Review: If an escrow waiver is requested, review the loan_application and credit_report for loan amount and mortgage history.
2. Step 2 - Eligibility Verification: Verify that the maximum loan amount is $1.5M and that “0x30x24 Mortgage History” is required. Section 35 loans are ineligible.
3. Step 3 - Validation and Verification: Verify the mortgage-history record. Do not define “0x30x24” or “Section 35”; Acra confirmation is requested on the applicable interpretation. A property listed for sale has separately required impounds.
4. Step 4 - Final Determination: Record whether the waiver meets the stated requirements, and identify any unresolved definition or classification.

**Checks:**
- If an escrow waiver is requested, the loan amount does not exceed $1.5M.
- If an escrow waiver is requested, the required “0x30x24 Mortgage History” is met.
- If an escrow waiver is requested, the loan is not a Section 35 loan.
- Impounds are required on a property listed for sale.

**Reads:** LoanCore.is_escrow_waived, LoanCore.total_loan_amount_usd, CreditReport.mortgage_0x30x24, SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Acra confirmation of the definition of “0x30x24”, Acra confirmation of the meaning and identification of “Section 35”

## acra-platinum.credit_review_analysis.fthb_status

**Purpose:** Establish whether the borrower is a first-time homebuyer, which is ineligible for this program.

1. Step 1 - Initial Document Review: Review the loan_application for borrower information relevant to first-time homebuyer status.
2. Step 2 - Eligibility Verification: Determine whether Borrower.is_first_time_homebuyer is true.
3. Step 3 - Validation and Verification: Confirm the case field agrees with the reviewed application information; resolve any discrepancy.
4. Step 4 - Final Determination: Record whether the borrower is a first-time homebuyer.

**Checks:**
- Borrower.is_first_time_homebuyer is false.

**Reads:** Borrower.is_first_time_homebuyer

## acra-platinum.credit_review_analysis.housing_history

**Purpose:** Determine whether housing history satisfies the program's stated “0x30x12” requirement.

1. Step 1 - Initial Document Review: Review the credit_report and documentation of housing payment history applicable to the borrower and guarantors.
2. Step 2 - Eligibility Verification: Apply the stated Housing History requirement, “0x30x12”.
3. Step 3 - Validation and Verification: Verify the reported history. Do not supply a definition of “0x30x12”; Acra confirmation is requested on its definition.
4. Step 4 - Final Determination: Record whether the requirement can be verified under the stated standard, and identify any unresolved interpretation.

**Checks:**
- The applicable housing history meets “0x30x12” as defined by Acra.

**Reads:** CreditReport.housing_history_rating, CreditReport.mortgage_0x30x24
**Missing data:** Housing-history records for the applicable period, Acra confirmation of the definition of “0x30x12”

## acra-platinum.credit_review_analysis.loan_amount

**Purpose:** Determine whether the loan amount meets the published loan amount requirements.

1. Step 1 - Initial Document Review: Review the loan_application for the requested loan amount.
2. Step 2 - Eligibility Verification: Verify that the loan amount is from $100,000 to $2,000,000 and is in $50 increments.
3. Step 3 - Validation and Verification: Compare the loan amount in the application with LoanCore.total_loan_amount_usd.
4. Step 4 - Final Determination: Record whether the amount and increment requirements are met.

**Checks:**
- LoanCore.total_loan_amount_usd is from $100,000 to $2,000,000, inclusive, and is in $50 increments.

**Reads:** LoanCore.total_loan_amount_usd

## acra-platinum.credit_review_analysis.minimum_score_and_matrix_cltv

**Purpose:** Determine whether the decisioning score meets the stated minimum and whether CLTV is within the applicable printed matrix maximum.

1. Step 1 - Initial Document Review: Review the credit_report and loan_application for the score and loan purpose used in the case.
2. Step 2 - Eligibility Verification: Use the decisioning score determined under the Decisioning Score job. The minimum decisioning score is 700. Apply the printed matrix for loans ≤ $2,000,000: at 730 and above, maximum CLTV is 80% purchase, 80% rate & term, and 75% cash-out; at 721–729, it is 80%, 80%, and 65%, respectively; on a literal reading, scores 700–720 take the 700 row, with maxima of 80%, 80%, and 55%, respectively.
3. Step 3 - Validation and Verification: Compare the case CLTV with the maximum for the applicable score and loan purpose. Do not normalize the printed 721 threshold to 720. Acra confirmation is requested on how score 720 is treated.
4. Step 4 - Final Determination: Record whether the minimum score is met and whether the applicable matrix CLTV maximum is met.

**Checks:**
- The decisioning score is at least 700 and LoanCore.cltv_percent does not exceed the printed matrix maximum for the score and LoanCore.loan_purpose.

**Reads:** CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.loan_purpose, LoanCore.total_loan_amount_usd
**Missing data:** Confirmation from Acra on whether the printed 721 threshold is intended and how a score of 720 is treated

## acra-platinum.credit_review_analysis.mortgage_and_rental_history

**Purpose:** Determine whether the required mortgage and rental history has been documented and evaluated for the applicable properties.

1. Step 1 - Initial Document Review: Review the credit_report for all reported mortgages and review available records for mortgages not reported and for rental history.
2. Step 2 - Eligibility Verification: For DSCR loans, require documentation of payment history for the subject property, primary residence, and second homes, if applicable. Additional properties do not require documented housing history unless documents in the file suggest a major credit event has occurred.
3. Step 3 - Validation and Verification: Evaluate the ratings for properties the borrower owns and/or rents over the last twelve (12) months. For mortgages not reported on credit, the file should contain documentation to evaluate the history on the applicant's primary residence(s), any secondary residence(s), and the subject property. Rate a matured loan based on its maturity date; any extension of the maturity date must be in writing.
4. Step 4 - Final Determination: Record whether the required history was documented and evaluated for the applicable properties and whether any maturity-date extension is in writing.

**Checks:**
- The required mortgage and rental history for the applicable properties is documented and evaluated over the last twelve (12) months.
- Any matured loan is rated based on its maturity date, and any extension of the maturity date is in writing.
- Additional properties not required for DSCR housing-history documentation are not required unless file documents suggest a major credit event.

**Reads:** LoanCore.dscr_qualification_method, SubjectProperty.has_current_lease
**Missing data:** Mortgage and rental payment history for applicable properties, Written maturity-date extension, if any, Documents, if any, suggesting a major credit event

## acra-platinum.credit_review_analysis.previous_credit_events

**Purpose:** Determine whether the applicable previous credit events meet the stated seasoning requirement.

1. Step 1 - Initial Document Review: Review the credit_report and relevant supporting records for previous credit events.
2. Step 2 - Eligibility Verification: Apply the stated requirement, “48 Mo Seasoning”.
3. Step 3 - Validation and Verification: Verify the event and dates from the records. Do not infer which events are covered, the starting event or ending date, the month-counting convention, or the treatment of modifications and forbearance; Acra confirmation is requested on these points.
4. Step 4 - Final Determination: Record whether the requirement is verified under Acra's confirmed interpretation, or identify the unresolved interpretation.

**Checks:**
- Each applicable previous credit event meets “48 Mo Seasoning” under Acra's confirmed event and date-counting rules.

**Reads:** Borrower.has_bankruptcy_or_foreclosure, Borrower.months_since_bankruptcy_or_foreclosure, Borrower.has_short_sale_dil_or_modification, Borrower.months_since_short_sale_dil_or_modification
**Missing data:** Records establishing applicable previous credit events and their dates, Acra confirmation of covered events, starting event, ending date, month-counting convention, and treatment of modifications and forbearance

## acra-platinum.credit_review_analysis.property_listed_for_sale

**Purpose:** Determine whether the property is subject to the listed-for-sale requirements and whether each stated characteristic is met.

1. Step 1 - Initial Document Review: Review the listing_history for listing dates and prices, the loan_application for the Application Date and loan terms, and the applicable property, lien, reserve, and payment-history records.
2. Step 2 - Eligibility Verification: Treat the property as listed for sale under §11.5 if it was listed for sale in the last six months, measured from the last date of being listed to the Application Date. Whether §11.5 applies to Platinum Select unchanged is part of Q-13.
3. Step 3 - Validation and Verification: For a property meeting the trigger, verify that it is not in default or otherwise delinquent on lien(s); for an investment property, verify that the subject is occupied by a tenant and is not vacant; verify qualification as either ≥ 1.0 DSCR or 43% maximum DTI, with the program's channel minimum DSCR applying (Wholesale 1.0 and Correspondent 1.2) and the DTI alternative unresolved as Q-14. Verify a prepayment penalty of at least three (3) years unless the property is in a state that does not allow prepayment penalties; twenty-four (24) months of reserves; a fully amortizing term; maximum LTV / CLTV of 65% based on the lesser of appraised value or lowest recent listing price; no subordinate financing; and required impounds. Interest only is not available.
4. Step 4 - Final Determination: Record whether the six-month trigger applies and whether every applicable stated characteristic is met. Do not resolve the stated Q-13 or Q-14 questions without confirmation.

**Checks:**
- The property was listed for sale in the last six months, measured from the last date of being listed to the Application Date, for the §11.5 requirements to apply.
- The property is not in default or otherwise delinquent on lien(s).
- If the property is an investment property, the subject is occupied by a tenant and is not vacant.
- The loan qualifies as either ≥ 1.0 DSCR or 43% maximum DTI, subject to the stated channel minimum DSCR and unresolved Q-14 treatment of the DTI alternative.
- The prepayment penalty is at least three (3) years unless the property is in a state that does not allow prepayment penalties.
- Twenty-four (24) months of reserves are provided.
- The loan has a fully amortizing term and is not interest only.
- LTV / CLTV is no more than 65% based on the lesser of appraised value or lowest recent listing price.
- There is no subordinate financing.
- Impounds are provided.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_listed_for_sale, SubjectProperty.is_vacant, SubjectProperty.occupancy_subtype, SubjectProperty.appraised_value_usd, LoanCore.cltv_percent, LoanCore.dscr_qualification_method, LoanCore.prepayment_penalty_structure, LoanCore.is_interest_only_10_40, MortgageLoanInformation.is_interest_only, LoanCore.note_rate_percent, RatioSet.reserves_months, SubjectProperty.state, SubjectProperty.is_mixed_use, LoanCore.channel
**Missing data:** Last date of listing and Application Date, Lowest recent listing price, Lien status and delinquency, DSCR value or DTI value, Acra confirmation on the DTI alternative (Q-14), State prepayment-penalty restriction determination, Evidence of twenty-four (24) months of reserves, Evidence of subordinate financing status and impounds, Acra confirmation whether §11.5 applies to Platinum Select unchanged (Q-13)

## acra-platinum.credit_review_analysis.tradelines

**Purpose:** Determine whether the applicant meets the tradeline and history requirement for the stated score-count category.

1. Step 1 - Initial Document Review: Review the credit_report for the applicant's repository scores, tradeline count, and history.
2. Step 2 - Eligibility Verification: Applicants with scores from 3 repositories are acceptable with no tradeline overlay. Applicants with 2 or fewer scores must meet 2 tradelines and 24 month history or 3 tradelines and 12 month history.
3. Step 3 - Validation and Verification: Verify the repository count and applicable tradeline and history facts from the credit_report; do not treat the case's summary field as a substitute for review where the underlying facts are unavailable.
4. Step 4 - Final Determination: Record whether the applicable tradeline requirement is met.

**Checks:**
- The applicant either has scores from 3 repositories, or has 2 or fewer scores and meets 2 tradelines and 24 month history or 3 tradelines and 12 month history.

**Reads:** CreditReport.score_count, CreditReport.tradelines_meet_requirement
**Missing data:** Underlying number of tradelines, Length of tradeline history

## acra-platinum.identification_requirements.borrower_guarantor_due_diligence_currency

**Purpose:** Establish whether Borrower / Guarantor Due Diligence is current at the required point in time.

1. Initial Document Review: Review the available Borrower / Guarantor Due Diligence information.
2. Eligibility Verification: Identify the date of any loan approval or draw and the date as of which the due diligence is current.
3. Validation and Verification: Verify that the Borrower / Guarantor Due Diligence is current as of the date of any loan approval or draw.
4. Final Determination: Record whether the due diligence meets the currency requirement.

**Checks:**
- Borrower / Guarantor Due Diligence is current as of the date of any loan approval or draw.
**Missing data:** Borrower / Guarantor Due Diligence information and its currency date, Date of loan approval or draw

## acra-platinum.identification_requirements.eligible_citizenship_type

**Purpose:** Establish whether the borrower has an eligible citizenship type.

1. Initial Document Review: Review the borrower’s citizenship information in the loan application.
2. Eligibility Verification: Compare the citizenship type with the eligible types: US Citizen and Permanent Resident. Non-permanent residents, foreign nationals and ITIN borrowers are not among the listed eligible types.
3. Validation and Verification: Verify the citizenship type recorded for the borrower.
4. Final Determination: Record whether the borrower’s citizenship type is eligible.

**Checks:**
- Borrower citizenship type is US Citizen or Permanent Resident.

**Reads:** Borrower.citizenship_status

## acra-platinum.identification_requirements.entity_borrower_homeownership_and_attestation

**Purpose:** Establish whether an entity-borrower case meets the stated guarantor homeownership and application-attestation requirements.

1. Initial Document Review: For an entity borrower, review the application for a borrower / guarantor attestation that they are not a first-time homebuyer, and review available information about guarantor homeownership experience.
2. Eligibility Verification: Confirm that at least one guarantor has prior homeownership experience and at least one borrower / guarantor attests on the application that they are not a first-time homebuyer.
3. Validation and Verification: Verify the prior homeownership experience and the application attestation.
4. Final Determination: Record whether both requirements are met. The source identifies whether the requirement also applies to individual borrowers as part of Q-13; do not extend this job to individual borrowers.

**Checks:**
- At least one guarantor has prior homeownership experience.
- At least one borrower / guarantor attests on the application that they are not a first-time homebuyer.

**Reads:** Borrower.entity_type, Borrower.is_first_time_homebuyer
**Missing data:** Evidence of prior homeownership for each guarantor

## acra-platinum.identification_requirements.entity_documentation

**Purpose:** Establish whether the entity borrower has provided the required entity documentation.

1. Initial Document Review: For an entity borrower, review the entity documents. Verify a complete, legible Certificate of Formation / Articles of Organization and all amendments. Verify a complete, legible Operating Agreement for LLCs and Partnerships, or Bylaws for corporations, with all referenced exhibits and amendments. The Operating Agreement or Bylaws must state whether the entity is member or manager managed, contain authorization to borrow money and enter into contracts for mortgage assets, and designate signers. Verify documentation evidencing ownership interests: for LLCs and Partnerships, the Operating Agreement must identify by name all persons with their ownership interest, or attach that information as an exhibit, or provide membership interest certificates / units in compliance with the Operating Agreement. For S or C Corporations, verify shareholder / stockholder certificates that comply with the Bylaws, if any, or the stock ledger if certificates are lost or unavailable; the certificate or ledger must account for all outstanding shares noted in the formation document, including those held by the corporation. If stock certificates are lost, destroyed, mutilated, or otherwise unavailable, verify an Affidavit of Lost Stock Certificate. For S-corporations or Partnerships where both stock certificate and stock ledger are unavailable, verify the most recent preceding tax year's K-1 statement for all members with 20% or more interest and a letter from the CPA or Tax Preparer affirming current ownership interest, with a statement to that effect if the preceding year's taxes have not been filed.
2. Eligibility Verification: Verify that names on entity documents match the identification; if they do not match exactly, verify a letter of explanation addressing the discrepancy. Verify a Certificate of Good Standing or equivalent valid within ninety (90) days of the closing date. If the entity is formed in a state other than where business is performed or where the property is located, verify a Certificate of Foreign Qualification or other qualification to operate in the state where business is being conducted. Verify IRS Form SS4 or a Federal Taxpayer Identification Number (TIN) or Employer Identification Number (EIN) issuance letter for the entity. An EIN exception request may be submitted for review by Acra's Legal Department with a letter of explanation stating the applicable grounds. Verify a Unanimous Written Consent / Board Resolution signed by all members regardless of their percentage of interest, authorizing the transaction with Acra Lending and identifying who is authorized to sign the loan documents on behalf of and to bind the entity. Check whether it is required by the Operating Agreement or Bylaws even where ownership is held by one individual. It cannot designate a signor on a personal guarantee, only an authorized signor for the loan documents signed by the entity. If a Power of Attorney is used to designate an attorney in fact to execute a personal guarantee, verify that it is utilized by the principal; see §23.5(C), not reproduced (Appendix B).
3. Validation and Verification: Do not accept borrower letters stating that required documents are not required, available, or excused from providing such documents. If the formation documents and the Operating Agreement or Bylaws conflict, additional information may be required. Legal reserves the right to condition for additional supporting documentation as determined in its sole discretion.
4. Final Determination: Record whether all required documentation applicable to the entity and the stated document-specific requirements have been verified, and identify any outstanding conditions or additional information requested.

**Checks:**
- The complete, legible formation document and all amendments are provided.
- The applicable Operating Agreement or Bylaws and all referenced exhibits and amendments meet the stated requirements.
- The applicable documentation evidencing ownership interests is provided and meets the stated requirements.
- The applicable corporate share documentation is provided and meets the stated requirements, including an Affidavit of Lost Stock Certificate when required.
- For an S-corporation or Partnership where both stock certificate and stock ledger are unavailable, the required K-1 statements and CPA or Tax Preparer letter are provided.
- Entity document names match identification, or a letter of explanation addresses any exact-name discrepancy.
- A Certificate of Good Standing or equivalent valid within ninety (90) days of the closing date is provided.
- If applicable, a Certificate of Foreign Qualification or other qualification to operate in the state where business is being conducted is provided.
- IRS Form SS4 or a Federal Taxpayer Identification Number (TIN) or Employer Identification Number (EIN) issuance letter is provided, or an EIN exception request with a letter of explanation stating the applicable grounds is submitted for review by Acra's Legal Department.
- The required Unanimous Written Consent / Board Resolution is provided and meets the stated requirements.
- If a Power of Attorney is used to designate an attorney in fact to execute a personal guarantee, it is utilized by the principal.
- No borrower letter states that required documents are not required, available, or excused from providing such documents.

**Reads:** Borrower.entity_type, Borrower.entity_documents_complete
**Missing data:** Entity formation documents and amendments, Operating Agreement or Bylaws, referenced exhibits and amendments, Ownership-interest documentation, Applicable shareholder / stockholder certificates, stock ledger, Affidavit of Lost Stock Certificate, K-1 statements and CPA or Tax Preparer letter, Identification for comparison with entity document names, Closing date, Qualification-to-operate documentation, where applicable, IRS Form SS4, TIN or EIN issuance letter, or EIN exception request and letter of explanation, Unanimous Written Consent / Board Resolution, Power of Attorney, if used for a personal guarantee, Any additional information or supporting documentation requested

## acra-platinum.identification_requirements.first_time_homebuyer_eligibility

**Purpose:** Establish whether the borrower is ineligible because the borrower is a First Time Home Buyer.

1. Initial Document Review: Review the application information used to identify whether all Applicants have never previously owned a home (real property).
2. Eligibility Verification: Apply Acra’s definition: a First Time Home Buyer is an application where all Applicants have never previously owned a home (real property). First Time Homebuyer (FTHB) is ineligible for this program.
3. Validation and Verification: Verify the recorded first-time homebuyer status against the application information.
4. Final Determination: Record whether the borrower is a First Time Home Buyer for this program.

**Checks:**
- Borrower is not a First Time Home Buyer.

**Reads:** Borrower.is_first_time_homebuyer

## acra-platinum.identification_requirements.key_principals_and_entities_background_review

**Purpose:** Establish whether Acra’s background review covers the Key Principals and Entities specified by the guideline.

1. Initial Document Review: Review available information identifying the borrower, recourse guarantors, owners, and parties with managing control.
2. Eligibility Verification: For an entity borrower, identify the entity, recourse guarantor(s), and any party (individual or entity) that owns 20% or more of the entity directly or indirectly or has managing control. For individual borrowers, identify all such individuals.
3. Validation and Verification: Review the background of the applicable Key Principals and Entities. Acra may order background checks on all Key Principals and Entities from Checkpoint, LexisNexis or another comparable provider, including criminal history, OFAC searches, litigation, judgment, and lien searches.
4. Final Determination: Record whether the background review covers the applicable Key Principals and Entities. Do not treat ordering a background check as mandatory; the source says Acra may order one.

**Checks:**
- Acra’s background review covers the entity, recourse guarantor(s), and each party that owns 20% or more directly or indirectly or has managing control, for an entity borrower.
- Acra’s background review covers all such individuals, for individual borrowers.

**Reads:** Borrower.entity_type
**Missing data:** Identity of the entity, recourse guarantor(s), direct and indirect owners and parties with managing control, Ownership percentages and control information, Background review information for applicable Key Principals and Entities

## acra-platinum.identification_requirements.permanent_resident_documentation

**Purpose:** Verify that a Permanent Resident has the required immigration and Social Security documentation.

1. Initial Document Review: If the borrower is a Permanent Resident, obtain and review the PRA ID and SSA card / SSA-89.
2. Eligibility Verification: Confirm that the borrower is a Permanent Resident.
3. Validation and Verification: Verify that the PRA ID is unexpired and that the SSA card / SSA-89 is provided.
4. Final Determination: Record whether both required items are verified.

**Checks:**
- For a Permanent Resident, an unexpired PRA ID and SSA card / SSA-89 are provided.

**Reads:** Borrower.citizenship_status
**Missing data:** PRA ID and its expiration date, SSA card / SSA-89

## acra-platinum.income_stability_sufficiency_analysis.actual_rent_evidence

**Purpose:** Verify that actual rent meets the Platinum Select documentation and lease-duration requirements when actual rent is used.

1. Initial Document Review: Review the lease_agreement and bank_statement when actual rent is used.
2. Eligibility Verification: Determine whether actual rent is used and whether it is long-term rent; actual-rent treatment is not appropriate for short-term rentals.
3. Validation and Verification: Verify evidence of 2 months’ proof of receipts and that the lease is in place for at least 3 months after the loan closing.
4. Final Determination: Record whether all applicable actual-rent requirements are met.

**Checks:**
- When actual rent is used, it is long-term rent.
- When actual rent is used, it is documented via evidence of 2 months’ proof of receipts.
- When actual rent is used, the lease is in place for at least 3 months after the loan closing.
**Missing data:** Whether actual rent is used, Whether the rent is long-term, Evidence of 2 months’ proof of receipts, Loan closing date, Lease end date

## acra-platinum.income_stability_sufficiency_analysis.channel_minimum_dscr

**Purpose:** Determine whether the loan meets the applicable Platinum Select minimum DSCR.

1. Initial Document Review: Review the DSCR calculation and identify the loan channel.
2. Eligibility Verification: Apply the Correspondent minimum of ≥ 1.2 or the Wholesale minimum of ≥ 1.0, as applicable.
3. Validation and Verification: Compare the calculated DSCR with the applicable channel minimum.
4. Final Determination: Record whether the DSCR meets the applicable minimum.

**Checks:**
- LoanCore.channel is Correspondent or Wholesale.
- The DSCR is ≥ 1.2 for Correspondent or ≥ 1.0 for Wholesale.

**Reads:** LoanCore.channel
**Missing data:** Calculated DSCR

## acra-platinum.income_stability_sufficiency_analysis.dscr_calculation

**Purpose:** Calculate the DSCR using the program's qualifying rent and the denominator specified in the Seller's Guide excerpt.

1. Initial Document Review: Review the available qualifying-rent and payment information.
2. Eligibility Verification: Identify qualifying rent and the annual payment components used in the denominator.
3. Validation and Verification: Calculate the denominator as the sum of annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees (collectively, PITIA); include subordinate financing, if applicable.
4. Final Determination: Calculate DSCR using qualifying rent and the annual PITIA denominator.

**Checks:**
- The DSCR uses qualifying rent and a denominator comprising annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees, with subordinate financing included if applicable.
**Missing data:** Qualifying rent, Annual principal, Annual interest, Annual real estate taxes, Annual property insurance, Annual homeowner's / condominium association fees, Whether subordinate financing applies, Annual subordinate financing payment, if applicable

## acra-platinum.income_stability_sufficiency_analysis.qualifying_rent_selection

**Purpose:** Determine the rent used when calculating the DSCR.

1. Initial Document Review: Review the appraisal_report for market rent established on the 1007 or 1025 and review the lease_agreement and bank_statement for actual rent evidence.
2. Eligibility Verification: Identify the market rent and actual rent available for the subject property.
3. Validation and Verification: Compare the market rent and actual rent.
4. Final Determination: Record the greater of the market rent established on the 1007 or 1025, or actual rent, as qualifying rent.

**Checks:**
- The qualifying rent is the greater of market rent established on the 1007 or 1025, or actual rent.
**Missing data:** Market rent established on the 1007 or 1025, Actual rent

## acra-platinum.income_stability_sufficiency_analysis.required_1007

**Purpose:** Verify the required Single-Family Comparable Rent Schedule (FNMA Form 1007).

1. Initial Document Review: Review the appraisal_report for the Single-Family Comparable Rent Schedule (FNMA Form 1007).
2. Eligibility Verification: Apply the 1007 requirement to the DSCR transaction.
3. Validation and Verification: Verify that the 1007 is present; it may be from the original appraiser or any state licensed appraiser.
4. Final Determination: Record whether the required 1007 is present.

**Checks:**
- The DSCR transaction has a 1007 from the original appraiser or any state licensed appraiser.
**Missing data:** Whether the appraisal_report contains a 1007, Whether the appraiser is the original appraiser or a state licensed appraiser

## acra-platinum.income_stability_sufficiency_analysis.short_term_rental_eligibility

**Purpose:** Determine whether the subject rental is ineligible as a short-term rental.

1. Initial Document Review: Review the lease_agreement and rent_roll for the rental arrangement.
2. Eligibility Verification: Determine whether the rental is short-term.
3. Validation and Verification: Verify the rental term against the reviewed records.
4. Final Determination: Record whether the rental is short-term; short-term rentals are ineligible for the program.

**Checks:**
- The subject rental is not short-term.
**Missing data:** Whether the rental is short-term

## acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability

**Purpose:** Determine whether the rent loss insurance requirement applies to the subject property.

1. Initial Document Review: Review the available case information for the subject property’s unit count and occupancy.
2. Eligibility Verification: Determine whether the property is a one- to four-unit non-owner occupied income property, whether its LTV is greater than 70%, and whether subject property rents are used to qualify.
3. Validation and Verification: Establish each applicability predicate from the available case fields and any required additional data.
4. Final Determination: Record whether the rent loss insurance requirement applies.

**Checks:**
- The subject property has one to four units.
- The subject property is non-owner occupied.
- The subject property is an income property.
- The subject property LTV is greater than 70%.
- Subject property rents are used to qualify.

**Reads:** SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype
**Missing data:** Whether the subject property is an income property, Subject property LTV, Whether subject property rents are used to qualify

## acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_sufficiency

**Purpose:** Verify the required rent loss insurance coverage, or the permitted reserves substitution, when the Rent Loss Insurance Applicability determination applies.

1. Initial Document Review: Review the hazard insurance declarations for rent loss insurance coverage and the period of coverage provided.
2. Eligibility Verification: Confirm that the Rent Loss Insurance Applicability determination applies.
3. Validation and Verification: Verify that the coverage is for rental losses incurred during rehabilitation following a casualty. Verify six (6) months' coverage, or, when required coverage cannot be obtained, that reserves substitute two (2) months for every one (1) month of rent loss coverage not provided.
4. Final Determination: Record whether the required coverage or permitted reserves substitution is satisfied.

**Checks:**
- The hazard insurance provides rent loss insurance covering rental losses incurred during the period a property is being rehabilitated following a casualty.
- The rent loss insurance provides six (6) months' coverage, or, when required coverage cannot be obtained, reserves provide two (2) months for every one (1) month of rent loss coverage not provided.

**Reads:** LoanCore.cltv_percent, SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype, RatioSet.reserves_months
**Missing data:** Whether required rent loss insurance coverage can be obtained

## acra-platinum.liabilities_assessment.dscr_denominator

**Purpose:** Establish the denominator calculation stated for DSCR and preserve the unresolved interest-only payment question.

1. Initial Document Review: Identify the annual principal, interest, real estate taxes, property insurance, homeowner's / condominium association fees, and any applicable subordinate financing used in the calculation.
2. Eligibility Verification: Apply this calculation rule when DSCR is calculated.
3. Validation and Verification: Verify that the denominator is the sum of those listed components. Acra calculates DSCR utilizing the first payment due under the terms of the Note. For an interest-only loan, do not resolve which payment enters the denominator; Acra confirmation is requested (Q-21).
4. Final Determination: Record the denominator calculation, or record that the interest-only payment basis awaits Acra confirmation.

**Checks:**
- The DSCR denominator is the sum of annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees; subordinate financing, if applicable, is also included.

**Reads:** MortgageLoanInformation.is_interest_only, LoanCore.is_interest_only_10_40
**Missing data:** Annual principal and interest amounts used in the denominator, Real estate taxes, property insurance, and homeowner's / condominium association fees used in the denominator, Applicable subordinate financing amount, For an interest-only loan, Acra confirmation of which payment enters the denominator (Q-21)

## acra-platinum.liabilities_assessment.listed_investment_property_occupancy

**Purpose:** Establish the required occupancy status for a listed investment property.

1. Initial Document Review: Review any lease agreement and rent roll for the subject property.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months and is an investment property.
3. Validation and Verification: Verify from the reviewed evidence that a tenant occupies the subject property and check the case field for vacancy status.
4. Final Determination: Determine whether the subject is occupied by a tenant and is not vacant.

**Checks:**
- If the property was listed for sale in the last six months and is an investment property, the subject is occupied by a tenant and is not vacant.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.occupancy_subtype, SubjectProperty.is_vacant

## acra-platinum.liabilities_assessment.listed_property_amortization

**Purpose:** Establish whether the listed-property amortization requirement is met.

1. Initial Document Review: Review the loan application for the loan's payment structure.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months.
3. Validation and Verification: Verify whether the loan is interest only.
4. Final Determination: Determine whether the loan has a fully amortizing term and is not interest only.

**Checks:**
- If the property was listed for sale in the last six months, the loan has a fully amortizing term and is not interest only.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, MortgageLoanInformation.is_interest_only, LoanCore.is_interest_only_10_40

## acra-platinum.liabilities_assessment.listed_property_impounds

**Purpose:** Establish whether the listed-property impound requirement is met.

1. Initial Document Review: Review the loan application for the escrow election.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months.
3. Validation and Verification: Check whether impounds are waived.
4. Final Determination: Determine whether impounds are required.

**Checks:**
- If the property was listed for sale in the last six months, impounds are required.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, LoanCore.is_escrow_waived

## acra-platinum.liabilities_assessment.listed_property_lien_status

**Purpose:** Establish the required status of liens on a listed property.

1. Initial Document Review: Review the title commitment and credit report for information about liens on the subject property.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months.
3. Validation and Verification: Verify the status of the liens shown in the reviewed records.
4. Final Determination: Determine whether the liens are not in default or otherwise delinquent.

**Checks:**
- If the property was listed for sale in the last six months, its liens are not in default or otherwise delinquent.

**Reads:** SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Current default or delinquency status of each lien

## acra-platinum.liabilities_assessment.listed_property_ltv_and_cltv

**Purpose:** Establish whether the listed-property maximum LTV / CLTV requirement is met on the stated valuation basis.

1. Initial Document Review: Review the appraisal report and listing history for the appraised value and recent listing prices.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months.
3. Validation and Verification: Verify that LTV / CLTV does not exceed 65% based on the lesser of the appraised value or lowest recent listing price.
4. Final Determination: Determine whether the stated maximum is met on the required valuation basis.

**Checks:**
- If the property was listed for sale in the last six months, maximum LTV / CLTV is 65% based on the lesser of (a) appraised value or (b) lowest recent listing price.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.appraised_value_usd, LoanCore.cltv_percent
**Missing data:** LTV on the required valuation basis, Lowest recent listing price

## acra-platinum.liabilities_assessment.listed_property_prepayment_penalty

**Purpose:** Establish whether the listed-property prepayment-penalty requirement is met or the stated exception applies.

1. Initial Document Review: Review the loan application for the prepayment penalty structure.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months.
3. Validation and Verification: Verify whether the penalty is at least three (3) years or whether the property is in a state that does not allow prepayment penalties.
4. Final Determination: Determine whether the stated requirement or exception applies.

**Checks:**
- If the property was listed for sale in the last six months, the prepayment penalty is at least three (3) years unless the property is in a state that does not allow prepayment penalties.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, LoanCore.prepayment_penalty_structure, SubjectProperty.state
**Missing data:** Whether the property's state does not allow prepayment penalties

## acra-platinum.liabilities_assessment.listed_property_qualification

**Purpose:** Establish the stated qualification requirement for a listed property without resolving the requested Acra confirmation on the DTI alternative or interest-only DSCR calculation.

1. Initial Document Review: Review the loan application and rent roll for the information used to assess qualification.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months. The stated alternatives are ≥ 1.0 DSCR or 43% maximum DTI; the channel minimum DSCR applies, Wholesale 1.0 and Correspondent 1.2.
3. Validation and Verification: Verify qualification against the stated DSCR or DTI alternative. Do not resolve the requested Acra confirmation for the DTI alternative (Q-14) or, for an interest-only loan, the payment used in the DSCR denominator (Q-21).
4. Final Determination: Record whether a stated qualification alternative is met, or whether the case depends on a requested confirmation.

**Checks:**
- If the property was listed for sale in the last six months, the loan qualifies under the applicable stated alternative: DSCR meets the channel minimum (Wholesale 1.0 or Correspondent 1.2), or DTI is no more than 43%.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, LoanCore.channel, LoanCore.dscr_qualification_method, RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd, MortgageLoanInformation.is_interest_only, LoanCore.is_interest_only_10_40
**Missing data:** Qualifying DSCR and the data needed to verify it, DTI alternative applicability pending Acra confirmation (Q-14), For an interest-only loan, Acra confirmation of the payment used in the DSCR denominator (Q-21)

## acra-platinum.liabilities_assessment.listed_property_reserves

**Purpose:** Establish whether the required reserves are present for a listed property.

1. Initial Document Review: Review bank statements for reserve information.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months.
3. Validation and Verification: Verify the reserve amount in months against the 24-month requirement.
4. Final Determination: Determine whether 24 months of reserves are present.

**Checks:**
- If the property was listed for sale in the last six months, reserves are at least twenty-four (24) months.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months

## acra-platinum.liabilities_assessment.listed_property_subordinate_financing

**Purpose:** Establish whether the listed-property prohibition on subordinate financing is met.

1. Initial Document Review: Review the title commitment for subordinate financing or subordinate liens.
2. Eligibility Verification: Apply this requirement when the property was listed for sale in the last six months.
3. Validation and Verification: Verify whether subordinate financing is present.
4. Final Determination: Determine whether subordinate financing is absent.

**Checks:**
- If the property was listed for sale in the last six months, no subordinate financing is present.

**Reads:** SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Whether subordinate financing is present

## acra-platinum.liabilities_assessment.property_listed_within_six_months

**Purpose:** Establish whether the listed-property requirements apply.

1. Initial Document Review: Read the case field indicating whether the property was listed for sale in the last 6 months.
2. Eligibility Verification: Apply the six-month period measured from the last date of being listed to the Application Date.
3. Validation and Verification: Confirm the case field represents that defined period.
4. Final Determination: Record whether the property was listed within the six-month period.

**Checks:**
- SubjectProperty.listed_for_sale_last_6_months is true when the property was listed for sale in the last six months, measured from the last date of being listed to the Application Date.

**Reads:** SubjectProperty.listed_for_sale_last_6_months

## acra-platinum.loan_program_eligibility.channel_minimum_dscr

**Purpose:** Decide whether the loan meets the channel-specific minimum DSCR requirement.

1. Step 1 - Initial Document Review: Review the loan application and rent evidence used to qualify the subject property.
2. Step 2 - Eligibility Verification: Identify the channel and the applicable minimum: Correspondent ≥ 1.2 or Wholesale ≥ 1.0.
3. Step 3 - Validation and Verification: Verify the calculated DSCR and its qualifying method against the supporting rent and loan information.
4. Step 4 - Final Determination: Record whether the applicable minimum DSCR is met.

**Checks:**
- The calculated DSCR is at least 1.2 for Correspondent or at least 1.0 for Wholesale.

**Reads:** LoanCore.channel, LoanCore.dscr_qualification_method
**Missing data:** calculated DSCR, channel-specific DSCR minimum comparison result

## acra-platinum.loan_program_eligibility.citizenship_eligibility

**Purpose:** Decide whether the borrower meets the Platinum Select citizenship requirements.

1. Step 1 - Initial Document Review: Review the loan application and borrower citizenship documentation.
2. Step 2 - Eligibility Verification: Verify that the borrower is a US Citizen or Permanent Resident; non-permanent residents, foreign nationals, and ITIN borrowers are not among the listed eligible types.
3. Step 3 - Validation and Verification: For a Permanent Resident, verify an unexpired PRA ID and SSA card / SSA-89.
4. Step 4 - Final Determination: Record whether the citizenship requirement and any applicable Permanent Resident documentation requirement are met.

**Checks:**
- The borrower is a US Citizen or Permanent Resident.
- If the borrower is a Permanent Resident, the borrower has an unexpired PRA ID and SSA card / SSA-89.

**Reads:** Borrower.citizenship_status
**Missing data:** PRA ID expiry status, SSA card / SSA-89 documentation

## acra-platinum.loan_program_eligibility.eligible_loan_purpose

**Purpose:** Decide whether the loan purpose is eligible under the program.

1. Step 1 - Initial Document Review: Review the loan application for the stated loan purpose.
2. Step 2 - Eligibility Verification: Compare the purpose with Purchase, Rate & Term Refinance, Cash-Out Refinance, and Delayed Financing.
3. Step 3 - Validation and Verification: Verify the stated purpose against the transaction records.
4. Step 4 - Final Determination: Record whether the purpose is one of the listed eligible purposes.

**Checks:**
- The loan purpose is Purchase, Rate & Term Refinance, Cash-Out Refinance, or Delayed Financing.

**Reads:** LoanCore.loan_purpose, LoanCore.is_delayed_financing

## acra-platinum.loan_program_eligibility.entity_borrower_eligibility

**Purpose:** Decide whether the entity borrower meets the stated entity-type and entity-document requirements.

1. Step 1 - Initial Document Review: Review entity documents and the loan application for entity type and formation, ownership, and purpose information.
2. Step 2 - Eligibility Verification: Verify that the borrower entity is an allowed type, is US formed and based, and is not a foreign entity or foreign owned entity. Check that it is a single purpose entity engaged in owning and operating residential investment or rental properties, with no assets other than residential investment or rental properties; series LLCs are not allowed.
3. Step 3 - Validation and Verification: Verify that each entity holding direct ownership of the subject property and on title as a direct owner is a borrowing entity. Review the entity structure for the stated nesting limitation and prohibited entity types.
4. Step 4 - Final Determination: Record whether the entity eligibility requirements are met.

**Checks:**
- The entity borrower is an allowed type, is US formed and based, and is not foreign owned.
- The entity borrower meets the stated single purpose entity requirements and is not a series LLC.
- Each entity holding direct ownership of the subject property and on title as a direct owner is a borrowing entity.
- The entity is not a prohibited type and its nesting does not exceed one (1) wholly-owned subsidiary owned by individual(s).

**Reads:** Borrower.entity_type, Borrower.entity_documents_complete, Borrower.is_entity_borrower_1
**Missing data:** entity formation and ownership records, entity assets and business activities, direct and indirect ownership structure, whether any direct title-holding entity is a borrowing entity, whether the entity is a prohibited type or has a disallowed nested ownership structure

## acra-platinum.loan_program_eligibility.entity_guarantees_and_attestation

**Purpose:** Decide whether the required entity guarantees and application attestation are provided.

1. Step 1 - Initial Document Review: Review entity ownership documents, guarantees, and the loan application.
2. Step 2 - Eligibility Verification: Identify all individuals with direct or indirect ownership ≥ 20% and verify that each provides a recourse guarantee that is Acra approved, or Exhibit 7. Recourse is joint and several when there are multiple guarantors.
3. Step 3 - Validation and Verification: Verify that at least one guarantor has prior homeownership experience and at least one borrower / guarantor attests on the application that they are not a first-time homebuyer. If prior home ownership is not evident within the loan file, the underwriter reserves the right to condition for supporting documentation.
4. Step 4 - Final Determination: Record whether the required guarantees and attestation are evidenced.

**Checks:**
- Every individual with direct or indirect ownership ≥ 20% provides a required recourse guarantee.
- At least one guarantor has prior homeownership experience.
- At least one borrower / guarantor on the loan attests on the application that they are not a first-time homebuyer.

**Reads:** Borrower.entity_type, Borrower.entity_documents_complete, Borrower.is_entity_borrower_1
**Missing data:** direct and indirect ownership percentages, guarantee documents and Acra approval status, guarantor prior homeownership evidence, application attestation

## acra-platinum.loan_program_eligibility.escrow_waiver

**Purpose:** Decide whether a requested escrow waiver meets the stated Platinum Select requirements.

1. Step 1 - Initial Document Review: Review the loan application, mortgage history, and escrow waiver request.
2. Step 2 - Eligibility Verification: Verify that the loan amount is no more than $1.5M and that 0x30x24 Mortgage History is required.
3. Step 3 - Validation and Verification: Verify the mortgage history and loan amount against the supporting records.
4. Step 4 - Final Determination: Record whether the stated escrow waiver requirements are met.

**Checks:**
- The loan amount is no more than $1.5M.
- The required 0x30x24 Mortgage History is met.

**Reads:** LoanCore.is_escrow_waived, LoanCore.total_loan_amount_usd, CreditReport.mortgage_0x30x24

## acra-platinum.loan_program_eligibility.first_time_homebuyer_eligibility

**Purpose:** Decide whether the applicant is ineligible as a first-time homebuyer.

1. Step 1 - Initial Document Review: Review the loan application for the first-time homebuyer attestation and prior homeownership information.
2. Step 2 - Eligibility Verification: Apply Acra’s definition: an application where all Applicants have never previously owned a home (real property) is a First Time Home Buyer; First Time Homebuyer (FTHB) is ineligible.
3. Step 3 - Validation and Verification: Verify the attestation and review supporting evidence of prior homeownership where available.
4. Step 4 - Final Determination: Record whether the applicant meets the FTHB definition.

**Checks:**
- The application is not an application where all Applicants have never previously owned a home (real property).

**Reads:** Borrower.is_first_time_homebuyer
**Missing data:** prior homeownership history of all Applicants

## acra-platinum.loan_program_eligibility.listed_for_sale_requirements

**Purpose:** Decide whether a loan on a property listed for sale within six months meets the stated listed-property requirements.

1. Step 1 - Initial Document Review: Review listing history, loan and lien information, occupancy and rent evidence, credit or reserve evidence, appraisal, and loan terms.
2. Step 2 - Eligibility Verification: Determine whether the property has been listed for sale in the last six months, measured from the last date of being listed to the Application Date. If so, verify the stated requirements: no default or other delinquency on lien(s); tenant occupied and not vacant for an investment property; channel minimum DSCR; prepayment penalty of at least three (3) years unless the property is in a state that does not allow prepayment penalties; twenty-four (24) months of reserves; fully amortizing term; maximum LTV / CLTV 65% based on the lesser of appraised value or lowest recent listing price; no subordinate financing; and impounds.
3. Step 3 - Validation and Verification: Verify each applicable listed-property requirement against the supporting records. Interest only is not available on a property listed for sale.
4. Step 4 - Final Determination: Record whether the listed-property requirements are met when the property is within the stated six-month period.

**Checks:**
- If the property has been listed for sale in the last six months, measured from the last date of being listed to the Application Date, all applicable stated listed-property requirements are met.
- If the property has been listed for sale within six months, the loan is not interest only.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_listed_for_sale, SubjectProperty.is_vacant, SubjectProperty.has_current_lease, LoanCore.channel, LoanCore.cltv_percent, LoanCore.is_interest_only_10_40, MortgageLoanInformation.is_interest_only, RatioSet.reserves_months, LoanCore.prepayment_penalty_structure, SubjectProperty.appraised_value_usd
**Missing data:** Application Date, last date listed for sale, lien default or delinquency status, tenant occupancy evidence, prepayment penalty term and state allowance, reserves evidence, fully amortizing term evidence, subordinate financing status, impound status, lowest recent listing price, whether impounds are in place

## acra-platinum.loan_program_eligibility.loan_amount_requirements

**Purpose:** Decide whether the loan amount is within the published program range and in a permitted increment.

1. Step 1 - Initial Document Review: Review the loan application for the requested loan amount.
2. Step 2 - Eligibility Verification: Check that the amount is from $100,000 to $2,000,000 and is in $50 increments.
3. Step 3 - Validation and Verification: Verify the amount against the transaction and underwriting records.
4. Step 4 - Final Determination: Record whether all stated loan-amount requirements are met.

**Checks:**
- The loan amount is at least $100,000 and no more than $2,000,000.
- The loan amount is in $50 increments.

**Reads:** LoanCore.total_loan_amount_usd

## acra-platinum.loan_program_eligibility.matrix_cltv_limit

**Purpose:** Decide whether the loan meets the applicable printed matrix CLTV maximum.

1. Step 1 - Initial Document Review: Review the loan application, credit report, and appraisal report for loan purpose, scores, CLTV, and value.
2. Step 2 - Eligibility Verification: Use the printed matrix row for the applicable FICO threshold and the applicable Purchase, Rate & Term, or Cash-Out column. The printed thresholds are 730, 721, and 700; no row is printed below 700.
3. Step 3 - Validation and Verification: Verify the representative decisioning score, applicable purpose, and CLTV used for the comparison.
4. Step 4 - Final Determination: Record whether the CLTV is no greater than the applicable matrix maximum.

**Checks:**
- The representative FICO is at least 700.
- The loan CLTV does not exceed the matrix maximum for the applicable FICO row and loan purpose: at 730 and above, 80% Purchase / 80% Rate & Term / 75% Cash-Out; at 721–729, 80% / 80% / 65%; at 700–720, 80% / 80% / 55%.

**Reads:** CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** CLTV used for underwriting

## acra-platinum.loan_program_eligibility.non_owner_occupancy

**Purpose:** Decide whether the property is non-owner occupied as required for the program.

1. Step 1 - Initial Document Review: Review the loan application and any lease agreement or rent roll for evidence of occupancy and tenancy.
2. Step 2 - Eligibility Verification: Determine whether the subject property is non-owner occupied.
3. Step 3 - Validation and Verification: Reconcile the stated occupancy with the available tenancy and property records.
4. Step 4 - Final Determination: Record whether the non-owner-occupied requirement is met.

**Checks:**
- The subject property is non-owner occupied.

**Reads:** SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease
**Missing data:** evidence of who occupies the property and whether the owner occupies it

## acra-platinum.loan_program_eligibility.prepayment_penalty_requirements

**Purpose:** Decide whether the loan’s prepayment penalty structure meets the printed program requirements and applicable restriction.

1. Step 1 - Initial Document Review: Review the loan application, note terms, property location, loan amount, purpose, occupancy or borrower type, and unit count.
2. Step 2 - Eligibility Verification: Compare the selected structure with the structures printed: 5 Year 5% Fixed (5% / 5% / 5% / 5% / 5%) or Sequential Stepdown (5% / 4% / 3% / 2% / 1%); 3 Year 5% Fixed (5% / 5% / 5%) or 3% Fixed (3% / 3% / 3%); 2 Year 3% Fixed (3% / 3%); 1 Year 3% Fixed (3%); or No Prepay. Apply the printed state restriction for the property state and transaction facts.
3. Step 3 - Validation and Verification: Verify the selected structure and all facts needed to apply the state restriction. For a property listed for sale within six months, verify a prepayment penalty of at least three (3) years unless the property is in a state that does not allow prepayment penalties.
4. Step 4 - Final Determination: Record whether the selected structure complies with the printed structure and applicable printed restrictions.

**Checks:**
- The prepayment penalty structure is one of the structures printed for Platinum Select.
- The selected structure satisfies the printed state restriction applicable to the property and transaction facts.
- For a property listed for sale within six months, the prepayment penalty is at least three (3) years unless the property is in a state that does not allow prepayment penalties.

**Reads:** SubjectProperty.state, SubjectProperty.number_of_units, LoanCore.total_loan_amount_usd, LoanCore.loan_purpose, Borrower.entity_type, Borrower.is_entity_borrower_1, LoanCore.prepayment_penalty_structure, SubjectProperty.listed_for_sale_last_6_months
**Missing data:** selected prepayment penalty percentages and term, borrower or title holder type relevant to state restriction, interest rate for the Illinois restriction, transaction facts needed to apply the printed state restrictions, whether the property state does not allow prepayment penalties

## acra-platinum.loan_program_eligibility.product_eligibility

**Purpose:** Decide whether the selected product and any interest-only terms meet the stated product requirements.

1. Step 1 - Initial Document Review: Review the loan application and note terms for product, ARM terms, and interest-only status.
2. Step 2 - Eligibility Verification: Verify that the product is 30 Yr Fixed, 5 Yr ARM, 30 Yr Fixed Interest-Only, or 5 Yr ARM Interest-Only. For an ARM, verify Index 1 Yr CMT; Caps 2/2/6; and the printed margin: 3.00 (FICO 760+), 3.25 (FICO 720-759), or 3.50 (FICO 700-719).
3. Step 3 - Validation and Verification: For Interest-Only, verify the 5 Yr Term and maximum CLTV 75.00%; verify that the property is not listed for sale. The minimum loan amount or minimum FICO for interest-only is not specified here.
4. Step 4 - Final Determination: Record whether the selected product and applicable printed terms meet the requirements.

**Checks:**
- The product is one of the four listed eligible product types.
- If the product is an ARM, its Index is 1 Yr CMT, Caps are 2/2/6, and its margin matches the printed FICO band.
- If the product is Interest-Only, it has a 5 Yr Term and CLTV no greater than 75.00%.
- An Interest-Only loan is not on a property listed for sale.

**Reads:** CreditReport.representative_score, LoanCore.note_rate_percent, LoanCore.cltv_percent, MortgageLoanInformation.is_interest_only, LoanCore.is_interest_only_10_40, SubjectProperty.is_listed_for_sale
**Missing data:** selected product type, ARM index and caps, ARM margin, Interest-Only term, CLTV used for the Interest-Only maximum comparison

## acra-platinum.loan_program_eligibility.property_eligibility_and_location

**Purpose:** Decide whether the subject property is an eligible type and is not in a listed ineligible category or location.

1. Step 1 - Initial Document Review: Review the loan application, appraisal report, and title commitment for the property type, unit count, location, and property characteristics.
2. Step 2 - Eligibility Verification: Verify that the property type is SFR, Townhome, PUD, Warrantable Condo, or Two-Units; verify it is not Rural, a Condotel, a Non-Warrantable Condo, or a Short-Term Rental; and verify the location is not SD or U.S. Terrs.
3. Step 3 - Validation and Verification: Verify the property classification and location against the available property records.
4. Step 4 - Final Determination: Record whether the property meets the stated eligibility requirements.

**Checks:**
- The property type is SFR, Townhome, PUD, Warrantable Condo, or Two-Units.
- The property is not Rural, a Condotel, a Non-Warrantable Condo, or a Short-Term Rental.
- The property is not located in SD or U.S. Terrs.

**Reads:** SubjectProperty.property_type, SubjectProperty.number_of_units, SubjectProperty.is_rural, SubjectProperty.is_mixed_use, SubjectProperty.state
**Missing data:** whether the property is a Condotel, Non-Warrantable Condo, or Short-Term Rental, property classification as eligible or ineligible where the case field does not specify it

## acra-platinum.loan_program_eligibility.vacant_property_eligibility

**Purpose:** Decide whether the property meets the program’s vacancy requirement.

1. Step 1 - Initial Document Review: Review the loan application and available lease or rent-roll evidence for current occupancy.
2. Step 2 - Eligibility Verification: Determine whether the property is vacant.
3. Step 3 - Validation and Verification: Verify the occupancy information against the available property and tenancy evidence.
4. Step 4 - Final Determination: Record whether the property is ineligible because it is vacant.

**Checks:**
- The subject property is not vacant.

**Reads:** SubjectProperty.is_vacant, SubjectProperty.has_current_lease

## acra-platinum.property_tax_calculation.dscr_denominator_composition

**Purpose:** Determine whether the DSCR denominator includes the components specified in the source.

1. Step 1 - Initial Document Review: Identify the inputs used for the DSCR denominator; this source does not specify documents to review.
2. Step 2 - Eligibility Verification: Identify whether subordinate financing is applicable to the calculation.
3. Step 3 - Validation and Verification: Verify that the denominator is the sum of annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees, and includes subordinate financing if applicable.
4. Step 4 - Final Determination: Determine whether the denominator follows those components.

**Checks:**
- The denominator is the sum of annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees.
- Subordinate financing is included in the denominator if applicable.
**Missing data:** annual principal, annual interest, annual real estate taxes, annual property insurance, annual homeowner's / condominium association fees, whether subordinate financing is applicable, subordinate financing amount, if applicable

## acra-platinum.property_tax_calculation.dscr_first_payment_basis

**Purpose:** Determine whether the DSCR calculation uses the first payment due under the terms of the Note.

1. Step 1 - Initial Document Review: Identify the first payment due under the terms of the Note; this source does not specify documents to review.
2. Step 2 - Eligibility Verification: Establish the payment applicable under the terms of the Note.
3. Step 3 - Validation and Verification: Verify that the DSCR calculation uses the first payment due under the terms of the Note.
4. Step 4 - Final Determination: Determine whether the DSCR calculation uses that first payment.

**Checks:**
- The DSCR calculation uses the first payment due under the terms of the Note.
**Missing data:** the first payment due under the terms of the Note

## acra-platinum.property_tax_calculation.interest_only_payment_treatment

**Purpose:** Resolve the source's open question about the DSCR denominator payment for an interest-only loan.

1. Step 1 - Initial Document Review: Determine whether the loan is interest-only from the case field.
2. Step 2 - Eligibility Verification: If the loan is interest-only, identify the payment sufficient to pay accrued interest to the mortgage on a monthly basis at the time of origination, as defined in §7.5.
3. Step 3 - Validation and Verification: For an interest-only loan, obtain Acra confirmation of which payment enters the DSCR denominator, as requested in Q-21.
4. Step 4 - Final Determination: If applicable, determine whether the confirmation has been obtained and its answer applied to the DSCR denominator.

**Checks:**
- MortgageLoanInformation.is_interest_only is true.
- If the loan is interest-only, Acra confirmation identifies which payment enters the DSCR denominator and that treatment is applied.

**Reads:** MortgageLoanInformation.is_interest_only
**Missing data:** the payment sufficient to pay the accrued interest to the mortgage on a monthly basis at the time of origination, Acra confirmation of which payment enters the DSCR denominator on an interest-only loan

## acra-platinum.property_tax_calculation.subordinate_financing_permission

**Purpose:** Resolve the source's open questions about permission for subordinate financing and the Standard Summary's HELOC calculation.

1. Step 1 - Initial Document Review: Identify whether subordinate financing is involved; this source does not specify documents to review.
2. Step 2 - Eligibility Verification: Do not treat the denominator calculation rule as establishing that a subordinate lien is permitted.
3. Step 3 - Validation and Verification: Obtain Acra confirmation on whether subordinate financing is permitted and, where relevant, on the HELOC calculation, as requested in Q-15.
4. Step 4 - Final Determination: Determine whether the requested confirmation has been obtained and applied.

**Checks:**
- Acra confirmation addresses whether subordinate financing is permitted and, where relevant, the HELOC calculation.
- The denominator calculation rule is not treated as establishing that a subordinate lien is permitted.
**Missing data:** whether subordinate financing is involved, Acra confirmation on whether subordinate financing is permitted, Acra confirmation on the HELOC calculation, if relevant

## acra-platinum.title_review.business_purpose_entity_use

**Purpose:** Determine whether the business entity financing is for a business purpose transaction involving an investment property.

1. Step 1 - Initial Document Review: Review the loan application and entity_documents for the transaction purpose and property use.
2. Step 2 - Eligibility Verification: Verify that the transaction is business purpose and the property is an investment property.
3. Step 3 - Validation and Verification: Resolve any conflict in the purpose or property-use information.
4. Step 4 - Final Determination: Determine whether the stated business-entity use is eligible.

**Checks:**
- The transaction is a business purpose transaction involving an investment property.

**Reads:** LoanCore.loan_purpose, SubjectProperty.occupancy_subtype
**Missing data:** Evidence that the transaction is business purpose, Evidence that the property is an investment property

## acra-platinum.title_review.direct_owners_as_borrowers

**Purpose:** Determine whether all direct entity owners on title are borrowing entities.

1. Step 1 - Initial Document Review: Review title_commitment and entity_documents to identify each direct owner of the subject property.
2. Step 2 - Eligibility Verification: Verify that every entity holding direct ownership and appearing on title is a borrowing entity.
3. Step 3 - Validation and Verification: Reconcile the title holders with the borrowing entities in the loan file.
4. Step 4 - Final Determination: Determine whether every required direct-owner entity is a borrowing entity.

**Checks:**
- Every entity that will hold direct ownership of the subject property and be on title as a direct owner is a borrowing entity.

**Reads:** Borrower.entity_type
**Missing data:** Names of all direct owners who will appear on title, Identification of which direct owners are borrowing entities

## acra-platinum.title_review.entity_documentation

**Purpose:** Determine whether the required entity documentation is provided and satisfies PLAT-5.10 and the related entity-document requirements.

1. Step 1 - Initial Document Review: Review the complete, legible Certificate of Formation / Articles of Organization and amendments; applicable Operating Agreement or Bylaws and amendments with referenced exhibits; ownership-interest evidence; and the applicable certificates, ledger, affidavit, K-1 statements, and CPA or Tax Preparer letter described in PLAT-5.10.
2. Step 2 - Eligibility Verification: Review name consistency with identification, the Certificate of Good Standing or equivalent valid within ninety (90) days of the closing date, any required foreign qualification, IRS Form SS4 or TIN / EIN issuance letter, and the Unanimous Written Consent / Board Resolution.
3. Step 3 - Validation and Verification: Verify the Operating Agreement or Bylaws states management type, authorization to borrow money and enter into contracts for mortgage assets, and designated signers; verify ownership evidence, required authorizations, and any required discrepancy letter, Power of Attorney, or additional supporting documentation. Do not accept borrower letters stating that required documents are not required, available, or excused from providing them.
4. Step 4 - Final Determination: Determine whether all required documents and contents are present and acceptable, without exception.

**Checks:**
- All entity documents required by PLAT-5.10 and the related requirements in U31 are provided, legible where required, complete where required, current where specified, consistent, and contain the required information and authorization.

**Reads:** Borrower.entity_type, Borrower.entity_documents_complete
**Missing data:** Certificate of Formation / Articles of Organization and all amendments, Operating Agreement or Bylaws, referenced exhibits, and all amendments, Ownership-interest evidence and applicable stock certificates, stock ledger, Affidavit of Lost Stock Certificate, K-1 statements, and CPA or Tax Preparer letter, Identification for name comparison and any letter of explanation, Certificate of Good Standing or equivalent and closing date, Foreign qualification documentation, if required, IRS Form SS4 or TIN / EIN issuance letter, or an EIN exception request and letter of explanation submitted for Legal Department review, Unanimous Written Consent / Board Resolution, Power of Attorney when used to designate an attorney in fact to execute a personal guarantee, Any additional supporting documentation conditioned for by Legal

## acra-platinum.title_review.entity_form_eligibility

**Purpose:** Determine whether the entity borrower has an allowed entity / guarantor type.

1. Step 1 - Initial Document Review: Review entity_documents for the borrower’s entity type.
2. Step 2 - Eligibility Verification: Compare the entity type with the types allowed by PLAT-5.7.
3. Step 3 - Validation and Verification: Confirm the entity type against Borrower.entity_type.
4. Step 4 - Final Determination: Determine whether the entity type is allowed.

**Checks:**
- Borrower.entity_type is one of the entity / guarantor types allowed by PLAT-5.7.

**Reads:** Borrower.entity_type

## acra-platinum.title_review.entity_ownership_structure

**Purpose:** Determine whether the entity structure complies with PLAT-5.8.

1. Step 1 - Initial Document Review: Review entity_documents for entity types and the complete ownership structure.
2. Step 2 - Eligibility Verification: Verify that the structure does not include a Cooperative, Irrevocable Trust, Land Trust, IRA, Non-Profit, or Joint Venture.
3. Step 3 - Validation and Verification: Verify that any business entity nesting is limited to only one (1) wholly-owned subsidiary, which in turn is owned by individual(s), with no multiple nesting or ownership by multiple entities, trusts, etcetera.
4. Step 4 - Final Determination: Determine whether the entity structure is permitted.

**Checks:**
- The structure includes none of the prohibited entity types and any business entity nesting is limited to only one (1) wholly-owned subsidiary owned by individual(s), with no multiple nesting or ownership by multiple entities, trusts, etcetera.

**Reads:** Borrower.entity_type
**Missing data:** All entity types in the structure, Complete entity ownership and subsidiary relationships

## acra-platinum.title_review.entity_title_holder

**Purpose:** Determine whether the proposed title holder meets the title-holder requirement.

1. Step 1 - Initial Document Review: Review title_commitment and entity_documents for the proposed title holder.
2. Step 2 - Eligibility Verification: Verify that the title holder is either individual person(s) directly or an entity acceptable to Acra in its sole discretion.
3. Step 3 - Validation and Verification: Obtain and review Acra’s acceptability decision if the title holder is an entity.
4. Step 4 - Final Determination: Determine whether the proposed title holder is permitted.

**Checks:**
- The collateral title will be held directly by individual person(s) or by an entity acceptable to Acra in its sole discretion.

**Reads:** Borrower.entity_type
**Missing data:** Proposed title holder, Acra’s determination of whether the proposed entity is acceptable

## acra-platinum.title_review.listed_investment_property_occupancy

**Purpose:** Determine whether the tenant occupancy requirement for a listed investment property is met.

1. Step 1 - Initial Document Review: Review lease_agreement and rent_roll for tenant occupancy.
2. Step 2 - Eligibility Verification: Verify that the listed investment property is occupied by a tenant and is not vacant.
3. Step 3 - Validation and Verification: Reconcile the occupancy evidence with the subject-property information.
4. Step 4 - Final Determination: Determine whether the tenant occupancy requirement is met.

**Checks:**
- For an investment property subject to §11.5, the subject is occupied by a tenant and is not vacant.

**Reads:** SubjectProperty.has_current_lease, SubjectProperty.is_vacant, SubjectProperty.occupancy_subtype
**Missing data:** Evidence that the subject is an investment property, Evidence of current tenant occupancy

## acra-platinum.title_review.listed_property_amortization

**Purpose:** Determine whether the fully amortizing term requirement is met for a listed property.

1. Step 1 - Initial Document Review: Review the loan terms.
2. Step 2 - Eligibility Verification: Verify that the loan has a fully amortizing term and is not interest only.
3. Step 3 - Validation and Verification: Reconcile the stated loan terms with the loan file.
4. Step 4 - Final Determination: Determine whether the amortization requirement is met.

**Checks:**
- The loan has a fully amortizing term and is not interest only.

**Reads:** MortgageLoanInformation.is_interest_only, LoanCore.is_interest_only_10_40

## acra-platinum.title_review.listed_property_impounds

**Purpose:** Determine whether the listed-property impound requirement is met.

1. Step 1 - Initial Document Review: Review the loan file for impound requirements and arrangements.
2. Step 2 - Eligibility Verification: Verify that impounds are required.
3. Step 3 - Validation and Verification: Verify the loan file reflects the required impounds.
4. Step 4 - Final Determination: Determine whether the impound requirement is met.

**Checks:**
- Impounds are required for the loan.

**Reads:** LoanCore.is_escrow_waived
**Missing data:** Loan-file evidence that impounds are required

## acra-platinum.title_review.listed_property_lien_status

**Purpose:** Determine whether the lien status requirement for a property listed for sale is met.

1. Step 1 - Initial Document Review: Review available lien and loan records for the subject property.
2. Step 2 - Eligibility Verification: Verify that the property is not in default or otherwise delinquent on lien(s).
3. Step 3 - Validation and Verification: Resolve any conflicting lien-status information.
4. Step 4 - Final Determination: Determine whether the lien status requirement is met.

**Checks:**
- The property is not in default or otherwise delinquent on lien(s).
**Missing data:** Current status of each lien on the subject property

## acra-platinum.title_review.listed_property_maximum_ltv_cltv

**Purpose:** Determine whether the listed-property maximum LTV / CLTV requirement is met.

1. Step 1 - Initial Document Review: Review the appraisal_report, listing_history, and loan amount information.
2. Step 2 - Eligibility Verification: Verify that maximum LTV / CLTV is 65% based on the lesser of appraised value or lowest recent listing price.
3. Step 3 - Validation and Verification: Verify the appraised value, lowest recent listing price, and calculation basis.
4. Step 4 - Final Determination: Determine whether the maximum LTV / CLTV requirement is met.

**Checks:**
- The LTV / CLTV does not exceed 65% based on the lesser of appraised value or lowest recent listing price.

**Reads:** LoanCore.cltv_percent, LoanCore.total_loan_amount_usd, SubjectProperty.appraised_value_usd
**Missing data:** Lowest recent listing price

## acra-platinum.title_review.listed_property_prepayment_penalty

**Purpose:** Determine whether the listed-property prepayment-penalty requirement is met.

1. Step 1 - Initial Document Review: Review the loan terms and property state information.
2. Step 2 - Eligibility Verification: Verify a prepayment penalty of at least three (3) years, unless the property is in a state that does not allow prepayment penalties.
3. Step 3 - Validation and Verification: Verify the prepayment penalty structure and whether the property’s state does not allow prepayment penalties.
4. Step 4 - Final Determination: Determine whether the prepayment-penalty requirement is met.

**Checks:**
- The loan has a prepayment penalty of at least three (3) years, or the property is in a state that does not allow prepayment penalties.

**Reads:** LoanCore.prepayment_penalty_structure, SubjectProperty.state
**Missing data:** Whether the property’s state does not allow prepayment penalties

## acra-platinum.title_review.listed_property_qualification

**Purpose:** Determine whether the listed-property loan meets one of the stated qualification alternatives.

1. Step 1 - Initial Document Review: Review loan_application and the loan file for the applicable DSCR or DTI qualification information.
2. Step 2 - Eligibility Verification: Verify qualification under either ≥ 1.0 DSCR or 43% maximum DTI; for this program the channel minimum DSCR applies, Wholesale 1.0 and Correspondent 1.2.
3. Step 3 - Validation and Verification: Validate the applicable qualification using the supporting loan information and the channel. The DTI alternative is Q-14.
4. Step 4 - Final Determination: Determine whether either permitted qualification alternative is met.

**Checks:**
- The loan qualifies as either ≥ 1.0 DSCR, subject to the channel minimum DSCR (Wholesale 1.0 and Correspondent 1.2), or 43% maximum DTI.

**Reads:** LoanCore.channel, LoanCore.dscr_qualification_method, RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd
**Missing data:** DSCR qualification information and supporting data, Applicable channel minimum DSCR, The qualification criteria for the DTI alternative identified as Q-14

## acra-platinum.title_review.listed_property_reserves

**Purpose:** Determine whether the listed-property reserve requirement is met.

1. Step 1 - Initial Document Review: Review the reserve information in the loan file.
2. Step 2 - Eligibility Verification: Verify that twenty-four (24) months of reserves are required.
3. Step 3 - Validation and Verification: Compare the available reserves with twenty-four (24) months; cash-in-hand may be considered if otherwise consistent with the Guide.
4. Step 4 - Final Determination: Determine whether the reserve requirement is met.

**Checks:**
- Reserves are at least twenty-four (24) months, with cash-in-hand considered only if otherwise consistent with the Guide.

**Reads:** RatioSet.reserves_months
**Missing data:** Whether any cash-in-hand being considered is otherwise consistent with the Guide

## acra-platinum.title_review.listed_property_subordinate_financing

**Purpose:** Determine whether the listed-property subordinate-financing restriction is met.

1. Step 1 - Initial Document Review: Review title_commitment and the loan file for subordinate financing.
2. Step 2 - Eligibility Verification: Verify that no subordinate financing is present.
3. Step 3 - Validation and Verification: Reconcile the title and loan information for subordinate financing.
4. Step 4 - Final Determination: Determine whether the restriction is met.

**Checks:**
- No subordinate financing is present.
**Missing data:** Whether subordinate financing is present

## acra-platinum.title_review.prior_homeownership_experience

**Purpose:** Determine whether the required prior homeownership experience is attested to on the application and address the stated documentation condition when applicable.

1. Step 1 - Initial Document Review: Review the loan application for the borrower / guarantor homebuyer attestation and the loan file for evidence of prior home ownership.
2. Step 2 - Eligibility Verification: Verify that at least one borrower / guarantor attests on the application that they are not a first-time homebuyer.
3. Step 3 - Validation and Verification: If prior home ownership is not evident within the loan file, determine whether supporting documentation is required by the underwriter and, if conditioned, review it.
4. Step 4 - Final Determination: Determine whether the attestation requirement is met and any condition for supporting documentation is cleared.

**Checks:**
- At least one borrower / guarantor attests on the application that they are not a first-time homebuyer; if prior home ownership is not evident within the loan file, any underwriter condition for supporting documentation is cleared.

**Reads:** Borrower.is_first_time_homebuyer
**Missing data:** Application attestation by a borrower / guarantor, Evidence of prior home ownership within the loan file, Whether the underwriter has conditioned for supporting documentation and, if so, the supporting documentation

## acra-platinum.title_review.required_entity_guarantees

**Purpose:** Determine whether the entity borrower has the required recourse guarantees from its qualifying owners.

1. Step 1 - Initial Document Review: Review entity_documents and the recourse guarantees for ownership interests and guarantor coverage.
2. Step 2 - Eligibility Verification: Identify every individual with direct or indirect ownership ≥ 20% and verify that each provides an Acra approved, or Exhibit 7, recourse guarantee.
3. Step 3 - Validation and Verification: If there are multiple guarantors, verify that all recourse is joint and several.
4. Step 4 - Final Determination: Determine whether the required guarantees are provided.

**Checks:**
- Every individual with direct or indirect ownership ≥ 20% provides an Acra approved, or Exhibit 7, recourse guarantee, and all recourse is joint and several when there are multiple guarantors.

**Reads:** Borrower.entity_documents_complete, Borrower.is_entity_borrower_1
**Missing data:** Each individual’s direct and indirect ownership percentage, Guarantee documents and whether they are Acra approved or Exhibit 7, Whether recourse is joint and several for multiple guarantors

## acra-platinum.title_review.revocable_living_trust_vesting

**Purpose:** Determine whether title vesting in the inter vivos revocable trust satisfies PLAT-5.13.

1. Step 1 - Initial Document Review: Review the complete, legible Trust or Certification of Trust and the title documents.
2. Step 2 - Eligibility Verification: Verify the Trust’s required contents, validity under the laws of the state in which it is established, revocability, establishment by natural person(s) during their lifetime, and that the primary beneficiary is the individual(s) establishing it.
3. Step 3 - Validation and Verification: Verify the Trustee powers and required lender protections; if the Trustor(s) and Trustee(s) are not the same, obtain written exception by Acra Senior Management. Review any additional supporting documentation conditioned for by Legal.
4. Step 4 - Final Determination: Determine whether all trust vesting requirements are met.

**Checks:**
- The Trust satisfies all requirements stated in PLAT-5.13, including required documentation and trust provisions, and written exception by Acra Senior Management is obtained if the Trustor(s) and Trustee(s) are not the same.

**Reads:** Borrower.entity_type
**Missing data:** Complete Trust or Certification of Trust and its required contents, Evidence that the Trust is valid under the laws of the state in which it is established, Evidence of revocability, establishment, lifetime effectiveness, and primary beneficiary, Trust provisions on Trustee authority, beneficiary consent, lender risk, and creditor rights, Written exception by Acra Senior Management if Trustor(s) and Trustee(s) are not the same, Any additional supporting documentation conditioned for by Legal

## acra-platinum.title_review.single_purpose_entity

**Purpose:** Determine whether the entity borrower meets the single purpose entity requirement.

1. Step 1 - Initial Document Review: Review entity_documents for the entity’s assets, activities, and organizational form.
2. Step 2 - Eligibility Verification: Verify that the entity has no assets other than residential investment or rental properties and is engaged in owning and operating residential investment or rental properties.
3. Step 3 - Validation and Verification: Verify that the entity is not a series limited liability company.
4. Step 4 - Final Determination: Determine whether the entity meets the single purpose entity requirement.

**Checks:**
- The entity has no assets other than residential investment or rental properties, is engaged in the business of owning and operating residential investment or rental properties, and is not a series limited liability company.

**Reads:** Borrower.entity_type
**Missing data:** Entity assets, Entity business activities, Whether the LLC is a series LLC

## acra-platinum.title_review.us_entity_eligibility

**Purpose:** Determine whether the entity borrower meets PLAT-5.7’s US formation, base, and ownership requirements.

1. Step 1 - Initial Document Review: Review entity_documents for evidence of formation, business base, and ownership.
2. Step 2 - Eligibility Verification: Verify that the borrower is a US formed and based Entity and is not a foreign entity or foreign owned entity.
3. Step 3 - Validation and Verification: Resolve any discrepancy in the formation, business base, or ownership evidence.
4. Step 4 - Final Determination: Determine whether the US entity eligibility requirement is met.

**Checks:**
- The borrower entity is US formed and based, and is not a foreign entity or foreign owned entity.

**Reads:** Borrower.entity_type
**Missing data:** Entity formation location, Entity business base, Entity ownership and whether any ownership is foreign
