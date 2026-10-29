# Our jobs, platinum (81)

## acra-platinum.appraisal_review_property_eligibility.declining_market_cltv_reduction

**Purpose:** Apply the declining-market CLTV reduction and preserve the stated open question about how it combines with other caps.

1. Step 1 - Initial Document Review: Review the appraisal report for the property's market trend and review other applicable CLTV caps.
2. Step 2 - Eligibility Verification: If the market is declining, apply the stated -5% CLTV property/borrower full profile reduction.
3. Step 3 - Validation and Verification: Verify the declining-market finding and request Acra confirmation of how the reduction combines with other caps.
4. Step 4 - Final Determination: Record the reduction and keep the cap combination subject to Acra confirmation.

**Checks:**
- If the market is declining, the -5% CLTV property/borrower full profile reduction is applied, and how it combines with other caps is referred for Acra confirmation.

**Reads:** LoanCore.cltv_percent
**Missing data:** Whether the market is declining, Acra confirmation of how the reduction combines with other caps

## acra-platinum.appraisal_review_property_eligibility.ineligible_state

**Purpose:** Determine whether the subject property is in SD or a U.S. territory.

1. Step 1 - Initial Document Review: Review the appraisal report for the subject property's location.
2. Step 2 - Eligibility Verification: Compare the property state with the ineligible locations listed for non-owner-occupied properties.
3. Step 3 - Validation and Verification: Verify the state recorded for the subject property.
4. Step 4 - Final Determination: Determine whether the property is in SD or a U.S. territory.

**Checks:**
- SubjectProperty.state is not SD or a U.S. territory.

**Reads:** SubjectProperty.state

## acra-platinum.appraisal_review_property_eligibility.listed_for_sale_within_six_months

**Purpose:** Establish whether the property is considered listed for sale under §11.5.

1. Step 1 - Initial Document Review: Review the listing history for the last date the property was listed and the Application Date.
2. Step 2 - Eligibility Verification: Apply the six-month period measured from the last date of being listed to the Application Date.
3. Step 3 - Validation and Verification: Verify the listing dates against the listing history and Application Date.
4. Step 4 - Final Determination: Record whether the property was listed for sale in the last six months.

**Checks:**
- SubjectProperty.listed_for_sale_last_6_months correctly indicates whether the property was listed for sale in the last six months, measured from the last date of being listed to the Application Date.

**Reads:** SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Last date of being listed, Application Date

## acra-platinum.appraisal_review_property_eligibility.listed_investment_property_occupancy

**Purpose:** Check the occupancy requirements for listed investment properties.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review occupancy information and any lease or rent roll provided.
2. Step 2 - Eligibility Verification: If the property is an investment property, check that it is occupied by a tenant and is not vacant.
3. Step 3 - Validation and Verification: Verify the tenant occupancy and vacancy status using the reviewed evidence.
4. Step 4 - Final Determination: Record whether the requirement for a listed investment property is met.

**Checks:**
- If the listed property is an investment property, it is occupied by a tenant and is not vacant.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant

## acra-platinum.appraisal_review_property_eligibility.listed_property_amortization

**Purpose:** Check the listed-property loan term requirement.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review the loan terms.
2. Step 2 - Eligibility Verification: Check that the loan has a fully amortizing term; interest only is not available.
3. Step 3 - Validation and Verification: Verify whether the loan is interest only and whether its term is fully amortizing.
4. Step 4 - Final Determination: Record whether the loan meets the requirement.

**Checks:**
- The loan has a fully amortizing term and is not interest only.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, MortgageLoanInformation.is_interest_only, LoanCore.is_interest_only_10_40
**Missing data:** Whether the loan term is fully amortizing

## acra-platinum.appraisal_review_property_eligibility.listed_property_impounds

**Purpose:** Check the listed-property impound requirement.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review the loan's escrow and impound information.
2. Step 2 - Eligibility Verification: Check that impounds are required.
3. Step 3 - Validation and Verification: Verify whether impounds are required for the loan.
4. Step 4 - Final Determination: Record whether the requirement is met.

**Checks:**
- Impounds are required.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, LoanCore.is_escrow_waived
**Missing data:** Whether impounds are required

## acra-platinum.appraisal_review_property_eligibility.listed_property_lien_status

**Purpose:** Check the lien-status requirement for loans on properties listed for sale under §11.5.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review title information concerning the lien(s).
2. Step 2 - Eligibility Verification: Check that the property is not in default or otherwise delinquent on lien(s).
3. Step 3 - Validation and Verification: Verify the status of the lien(s) from the reviewed evidence.
4. Step 4 - Final Determination: Record whether the lien-status requirement is met.

**Checks:**
- The property is not in default or otherwise delinquent on lien(s).

**Reads:** SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Whether any lien is in default or otherwise delinquent

## acra-platinum.appraisal_review_property_eligibility.listed_property_maximum_ltv_cltv

**Purpose:** Verify the listed-property maximum LTV / CLTV of 65% using the required lesser value.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review the appraisal and listing history.
2. Step 2 - Eligibility Verification: Apply the maximum LTV / CLTV of 65% based on the lesser of (a) appraised value or (b) lowest recent listing price.
3. Step 3 - Validation and Verification: Verify the appraised value, lowest recent listing price, loan amount, and resulting LTV / CLTV.
4. Step 4 - Final Determination: Record whether the maximum is met using the required lesser value.

**Checks:**
- The LTV / CLTV is no more than 65% based on the lesser of the appraised value or the lowest recent listing price.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.appraised_value_usd, LoanCore.total_loan_amount_usd, LoanCore.cltv_percent
**Missing data:** Lowest recent listing price, LTV / CLTV calculated using the lesser of the appraised value or lowest recent listing price

## acra-platinum.appraisal_review_property_eligibility.listed_property_prepayment_penalty

**Purpose:** Check whether the prepayment penalty is at least three years or the property is in a state that does not allow prepayment penalties.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review the loan's prepayment penalty structure and the property state.
2. Step 2 - Eligibility Verification: Check for a prepayment penalty of at least three (3) years unless the property is in a state that does not allow prepayment penalties.
3. Step 3 - Validation and Verification: Verify the penalty term and whether the state does not allow prepayment penalties.
4. Step 4 - Final Determination: Record whether the requirement or stated exception applies.

**Checks:**
- The prepayment penalty is at least three (3) years, or the property is in a state that does not allow prepayment penalties.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, LoanCore.prepayment_penalty_structure, SubjectProperty.state
**Missing data:** Whether the property state does not allow prepayment penalties

## acra-platinum.appraisal_review_property_eligibility.listed_property_qualification

**Purpose:** Apply the listed-property loan qualification requirement, including the program channel minimum DSCR and the unresolved DTI alternative.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review the loan's qualification information and channel.
2. Step 2 - Eligibility Verification: Check qualification by either ≥ 1.0 DSCR, using the channel minimum DSCR of Wholesale 1.0 and Correspondent 1.2, or the 43% maximum DTI alternative identified as Q-14.
3. Step 3 - Validation and Verification: Verify the applicable DSCR or DTI calculation and the channel-specific minimum from the loan records.
4. Step 4 - Final Determination: Record whether one of the stated qualification alternatives is met; refer the DTI alternative as Q-14.

**Checks:**
- The loan qualifies as either (a) ≥ 1.0 DSCR, subject to the channel minimum DSCR of Wholesale 1.0 and Correspondent 1.2, or (b) 43% maximum DTI, with the DTI alternative identified as Q-14.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, LoanCore.channel, LoanCore.dscr_qualification_method, RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd
**Missing data:** Calculated DSCR, Calculated DTI, Whether the DTI alternative is approved under Q-14

## acra-platinum.appraisal_review_property_eligibility.listed_property_reserves

**Purpose:** Verify that twenty-four (24) months of reserves are required for the listed property.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review the reserves information.
2. Step 2 - Eligibility Verification: Check for twenty-four (24) months of reserves; cash-in-hand may be considered if otherwise consistent with the Guide.
3. Step 3 - Validation and Verification: Verify the reserve months and any cash-in-hand considered under the Guide.
4. Step 4 - Final Determination: Record whether the reserve requirement is met.

**Checks:**
- Reserves are at least twenty-four (24) months, with cash-in-hand considered only if otherwise consistent with the Guide.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
**Missing data:** Whether any cash-in-hand considered is otherwise consistent with the Guide, Evidence of reserves., Payment basis for calculating reserves.

## acra-platinum.appraisal_review_property_eligibility.listed_property_subordinate_financing

**Purpose:** Check the listed-property prohibition on subordinate financing.

1. Step 1 - Initial Document Review: For a property listed for sale in the last six months, review the title commitment and loan records for subordinate financing.
2. Step 2 - Eligibility Verification: Check that no subordinate financing is present.
3. Step 3 - Validation and Verification: Verify whether subordinate financing exists.
4. Step 4 - Final Determination: Record whether the requirement is met.

**Checks:**
- No subordinate financing is present.

**Reads:** SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Whether subordinate financing is present

## acra-platinum.appraisal_review_property_eligibility.property_type_status

**Purpose:** Determine the policy status of the subject property type without assuming that a feature not addressed is either eligible or ineligible.

1. Step 1 - Initial Document Review: Review the appraisal report for the subject property's type and features.
2. Step 2 - Eligibility Verification: Compare the reported type and features with the expressly eligible and expressly ineligible types in PLAT-7.1 and PLAT-7.2.
3. Step 3 - Validation and Verification: Identify whether the property type is expressly eligible, expressly ineligible, or not addressed in the Platinum Summary.
4. Step 4 - Final Determination: Record the applicable status; for features not addressed, refer the question as Q-07 rather than assuming either status.

**Checks:**
- The subject property type is classified as expressly eligible, expressly ineligible, or not addressed in the Platinum Summary.

**Reads:** SubjectProperty.property_type, SubjectProperty.is_mixed_use, SubjectProperty.number_of_units, SubjectProperty.is_rural

## acra-platinum.appraisal_review_property_eligibility.vacant_property_eligibility

**Purpose:** Determine whether the subject property meets the Platinum Summary's vacant-property restriction.

1. Step 1 - Initial Document Review: Review the appraisal report for the subject property's occupancy status.
2. Step 2 - Eligibility Verification: Apply the rule that vacant properties are ineligible.
3. Step 3 - Validation and Verification: Verify the reported vacancy status.
4. Step 4 - Final Determination: Determine whether the property is vacant.

**Checks:**
- SubjectProperty.is_vacant is false.

**Reads:** SubjectProperty.is_vacant

## acra-platinum.asset_assessment_assets_and_funds_to_close.funds_seasoning_verification_trigger

**Purpose:** Determine whether the loan meets a stated trigger requiring verification of seasoning of funds to close.

1. Initial Document Review: Review the transaction information and funds-to-close documentation available.
2. Eligibility Verification: Determine whether CLTV is over 70% and whether the transaction is a consumer transaction, or is a business purpose loan with funds to close over $50,000.
3. Validation and Verification: If a stated trigger applies, verify seasoning of funds to close using the applicable source-of-funds documentation.
4. Final Determination: Record whether seasoning verification is required and, when required, whether it is verified. Do not assign a consumer-transaction classification from the source, which leaves that question open.

**Checks:**
- CLTV is over 70% and the loan is a consumer transaction, or the loan is a business purpose loan with funds to close over $50,000 and CLTV is over 70%.
- When the stated trigger applies, seasoning of funds to close is verified.

**Reads:** LoanCore.cltv_percent, LoanCore.loan_purpose
**Missing data:** Whether the loan is a consumer transaction., Funds-to-close amount., Evidence establishing seasoning of funds to close.

## acra-platinum.asset_assessment_assets_and_funds_to_close.funds_to_close_documentation

**Purpose:** Verify the required minimum 30-days documentation for all transactions.

1. Initial Document Review: Review bank statement(s) or other submitted documentation for funds to close.
2. Eligibility Verification: Apply the minimum documentation requirement to the transaction.
3. Validation and Verification: Verify that the documentation covers a minimum of 30-days.
4. Final Determination: Record whether the minimum documentation requirement is met; do not infer an additional domestic-funds seasoning period.

**Checks:**
- Funds to close have a minimum of 30-days documentation.
**Missing data:** Documentation showing the funds to close and its coverage period.

## acra-platinum.asset_assessment_assets_and_funds_to_close.high_cltv_reserves

**Purpose:** Verify the stated six-month reserves requirement for loans with CLTV over 75.00%.

1. Initial Document Review: Review available documentation of assets and reserves.
2. Eligibility Verification: Determine whether CLTV is over 75.00%.
3. Validation and Verification: If CLTV is over 75.00%, verify six-months reserves. Do not assume a payment basis, which is not stated.
4. Final Determination: Record whether the stated reserve requirement is met, noting that the source does not state the payment basis.

**Checks:**
- CLTV is over 75.00%.
- When CLTV is over 75.00%, six-months reserves are verified.

**Reads:** LoanCore.cltv_percent
**Missing data:** Evidence of reserves., Payment basis for calculating reserves.

## acra-platinum.asset_assessment_assets_and_funds_to_close.own_funds_contribution

**Purpose:** Determine whether applicant(s) contribute a portion of their own sourced and seasoned funds equal to at least 10% of the purchase price.

1. Initial Document Review: Review the loan application and bank statement(s) for the transaction, the applicant's contribution, and the source and seasoning of funds.
2. Eligibility Verification: Determine whether the transaction is for an investment property.
3. Validation and Verification: Verify that applicant(s) contribute their own sourced and seasoned funds and that the contribution is at least 10% of the purchase price.
4. Final Determination: Record whether the required own-funds contribution is verified; do not infer gift documentation requirements beyond the Seller's Guide gift-fund section (Appendix B).

**Checks:**
- The transaction is an investment-property transaction.
- Applicant(s) contribute their own sourced and seasoned funds in an amount equal to at least 10% of the purchase price.

**Reads:** SubjectProperty.occupancy_subtype
**Missing data:** Purchase price., Amount and source of applicant(s)' own contribution., Evidence establishing seasoning of the contributed funds., Seller's Guide gift-fund documentation requirements (Appendix B).

## acra-platinum.asset_assessment_assets_and_funds_to_close.rent_loss_insurance_reserves

**Purpose:** Verify reserves equal to two (2) months for every one (1) month of rent loss insurance coverage not provided.

1. Initial Document Review: Review hazard insurance documentation and available documentation of assets and reserves.
2. Eligibility Verification: Determine whether rent loss insurance is required but cannot be obtained.
3. Validation and Verification: If rent loss insurance is required but cannot be obtained, verify two (2) months reserves for every one (1) month of coverage not provided.
4. Final Determination: Record whether the stated reserve requirement is met; do not assume a payment basis or a coverage period not established by the evidence.

**Checks:**
- Rent loss insurance is required but cannot be obtained.
- When rent loss insurance is required but cannot be obtained, reserves are verified at two (2) months for every one (1) month of coverage not provided.
**Missing data:** Whether rent loss insurance is required but cannot be obtained., Number of months of coverage not provided., Evidence of reserves and the payment basis for calculating reserves.

## acra-platinum.asset_assessment_assets_and_funds_to_close.rent_receipt_and_mortgage_history_reserves

**Purpose:** Verify the stated 12 months of the subject's payment in reserve when the specified conditions apply.

1. Initial Document Review: Review available rent, occupancy, mortgage-payment-history, and reserve documentation.
2. Eligibility Verification: Determine whether the property is tenant-occupied, there is forbearance or mortgage lates in the last 12 months, and the prior two months' rent was not received timely.
3. Validation and Verification: If all stated conditions apply, verify 12 months of the subject's payment in reserve; the reserve may be from the transaction's cash-in-hand.
4. Final Determination: Record whether the stated reserve requirement is met. Do not infer a relationship to 0x30x12 beyond the source's stated reference.

**Checks:**
- The property is tenant-occupied, there is forbearance or mortgage lates in the last 12 months, and the prior two months' rent was not received timely.
- When all stated conditions apply, 12 months of the subject's payment are verified in reserve.

**Reads:** SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, CreditReport.mortgage_0x30x24
**Missing data:** Whether there was forbearance or a mortgage late in the last 12 months., Whether the prior two months' rent was received timely., Evidence of reserves., The subject's payment amount and the payment basis for calculating reserves.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.borrower_and_guarantor_due_diligence

**Purpose:** Determine whether the required due diligence is current and covers the Key Principals and Entities identified by the guideline.

1. Initial Document Review: Review the loan file for borrower and guarantor due diligence and its date, and identify the entity, recourse guarantors, owners, and parties with managing control.
2. Eligibility Verification: For an entity borrower, identify the entity, recourse guarantors, and any party (individual or entity) that owns 20% or more of the entity directly or indirectly or has managing control. For an individual borrower, identify all such individuals.
3. Validation and Verification: Verify that due diligence is current as of the date of any loan approval or draw. Review any background checks ordered by Acra, which may be from Checkpoint, LexisNexis or another comparable provider and may include criminal history, OFAC searches, litigation, judgment, and lien searches.
4. Final Determination: Record whether due diligence is current and whether the required parties have been identified for review.

**Checks:**
- Borrower / Guarantor Due Diligence is current as of the date of any loan approval or draw.
- For an entity borrower, the entity, recourse guarantor(s), and any party (individual or entity) that owns 20% or more of the entity directly or indirectly or has managing control are included in the identified review population.
- For an individual borrower, all such individuals are included in the identified review population.

**Reads:** Borrower.entity_type
**Missing data:** The date of any loan approval or draw and the date and contents of borrower and guarantor due diligence., The identity of the entity, recourse guarantors, direct and indirect owners and their ownership percentages, and parties with managing control., For an individual borrower, the identities of all such individuals., Which background checks Acra ordered and their results, if any.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.direct_title_owner_as_borrower

**Purpose:** Determine whether all entities holding direct ownership of the subject property and appearing on title are borrowing entities.

1. Initial Document Review: Review the title commitment and entity documents to identify each proposed direct owner of the subject property.
2. Eligibility Verification: Identify each entity that will hold direct ownership of the subject property and will be on title.
3. Validation and Verification: Compare the direct owners shown in the title and entity documentation with the borrowing entity or entities shown in the loan file.
4. Final Determination: Record whether every entity that will be a direct owner on title is a borrowing entity.

**Checks:**
- Every entity that will hold direct ownership of the subject property and will be on title is a borrowing entity.

**Reads:** Borrower.entity_type
**Missing data:** The entities that will hold direct ownership of the subject property and appear on title., The borrower or borrowers identified for the loan.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.entity_borrower_eligibility

**Purpose:** Determine whether the borrowing entity is eligible for financing and may hold title under the stated entity eligibility rules.

1. Initial Document Review: Review the loan application and entity documents to identify the borrower, the entity’s formation and business location, the transaction purpose, the entity type, and any ownership nesting.
2. Eligibility Verification: Determine whether the transaction is business purpose and the property is exclusively an investment property; whether the borrower is a US formed and based Entity; and whether the entity type is allowed. Check for disallowed entity types and whether any subsidiary structure exceeds one wholly-owned subsidiary owned by individual(s).
3. Validation and Verification: Verify the entity type, formation and business location, transaction purpose, and ownership structure against the reviewed documents. Determine whether the entity is acceptable to Acra in its sole discretion.
4. Final Determination: Record whether the proposed borrowing entity satisfies the applicable entity eligibility requirements.

**Checks:**
- The transaction is business purpose and the property is exclusively an investment property.
- The borrower is a US formed and based Entity, and is not a foreign entity or foreign owned entity.
- The entity type is one of the allowed types and is not a disallowed type.
- Business entity nesting is limited to only one (1) wholly-owned subsidiary that in turn is owned by individual(s), with no multiple nesting or ownership by multiple entities, trusts, etcetera.
- The entity is acceptable to Acra in its sole discretion.

**Reads:** Borrower.entity_type, LoanCore.loan_purpose
**Missing data:** Transaction purpose and whether the property is exclusively an investment property., Whether the entity is US formed and based, or is foreign formed, foreign based, or foreign owned., The entity’s precise legal type, including whether an LLC is a series LLC., The entity ownership chain, including whether a subsidiary is wholly-owned and owned by individual(s), and whether any other entities or trusts own it., Acra’s determination whether the entity is acceptable in its sole discretion.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.entity_ownership_change_recognition

**Purpose:** Determine whether a change to an operating agreement or bylaws is excluded from consideration under the stated timing rule.

1. Initial Document Review: Review the operating agreement or bylaws and amendments for changes to ownership percentages.
2. Eligibility Verification: Determine whether a change was made with the intent of changing ownership percentages to circumvent required personal guarantors.
3. Validation and Verification: Compare the effective date of any such change with the Application Date and the application process.
4. Final Determination: Do not recognize a change made with that intent within 30 days prior to an Application Date or throughout the application process.

**Checks:**
- A change to the operating agreement or bylaws made with the intent of changing ownership percentages to circumvent required personal guarantors is not recognized if made within 30 days prior to an Application Date or throughout the application process.

**Reads:** Borrower.entity_type
**Missing data:** Whether an operating agreement or bylaws ownership-percentage change was made with the intent of circumventing required personal guarantors., The effective date of the change, the Application Date, and whether the change occurred throughout the application process.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.guarantor_homeownership_experience

**Purpose:** Determine whether at least one borrower or guarantor meets the stated prior-homeownership requirement.

1. Initial Document Review: Review the loan application and loan file for the borrower or guarantor’s homeownership attestation and evidence of prior homeownership.
2. Eligibility Verification: Identify whether at least one guarantor has prior homeownership experience and whether at least one borrower or guarantor attests on the application that they are not a first-time homebuyer.
3. Validation and Verification: If prior home ownership is not evident within the loan file, determine whether supporting documentation is needed and review any documentation obtained.
4. Final Determination: Record whether the required homeownership experience and application attestation are established.

**Checks:**
- At least one guarantor has prior homeownership experience.
- At least one (1) borrower / guarantor on the loan attests on the application that they are not a first-time homebuyer.

**Reads:** Borrower.is_first_time_homebuyer, Borrower.entity_type
**Missing data:** Which guarantor has prior homeownership experience and the evidence of that experience., Whether a borrower or guarantor attests on the application that they are not a first-time homebuyer.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.required_entity_documentation

**Purpose:** Determine whether the entity file contains the required documentation without relying on borrower letters excusing or waiving any required document.

1. Initial Document Review: Obtain and review the complete, legible formation documents and amendments; the applicable operating agreement or bylaws and amendments with referenced exhibits; ownership evidence; and the other entity documents required for this entity type and transaction.
2. Eligibility Verification: Confirm the operating agreement or bylaws states whether the entity is member or manager managed, authorizes borrowing money and entering into contracts for mortgage assets, and designates signers. Confirm ownership documentation identifies all persons and interests or provides compliant membership interest evidence. For corporations, review the required shareholder or stockholder certificates or stock ledger, including the required accounting of outstanding shares and any required Affidavit of Lost Stock Certificate. For S-corporations or Partnerships where both stock certificate and stock ledger are unavailable, review the specified K-1 statements and CPA or Tax Preparer letter.
3. Validation and Verification: Verify that entity-document names match identification, or review a letter of explanation addressing discrepancies; review a Certificate of Good Standing or equivalent valid within ninety (90) days of closing; review any required foreign qualification; review the IRS Form SS4 or TIN or EIN issuance letter, or an EIN exception request and letter of explanation submitted for Acra Legal Department review; and review the required Unanimous Written Consent / Board Resolution. If a Power of Attorney is used to designate an attorney in fact to execute a personal guarantee, review it for the stated purpose. Do not accept borrower letters stating required documents are not required, available, or excused.
4. Final Determination: Record whether each applicable required document and stated document content is present. Refer conflicts between formation documents and the Operating Agreement or Bylaws for additional information, and refer any additional-supporting-documentation requirement to Legal as applicable.

**Checks:**
- The complete, legible Certificate of Formation / Articles of Organization and all amendments thereto are present.
- The complete Operating Agreement for LLCs and Partnerships, or Bylaws for corporations, with all referenced exhibits and amendments, is present and contains the required management, borrowing, mortgage-asset contract, and signer provisions.
- The documentation evidencing ownership interests meets the stated requirements for the entity type.
- For an S or C Corporation, the required shareholder / stockholder certificates or stock ledger is present and accounts for all outstanding shares noted in the Certificate of Formation / Articles of Organization, including those held by the corporation; an Affidavit of Lost Stock Certificate is present when required.
- For an S-corporation or Partnership where both stock certificate and stock ledger are unavailable, the required most recent preceding tax year's K-1 statement for all members with 20% or more interest and the required CPA or Tax Preparer letter are present, including the stated alternative if the preceding year's taxes have not been filed.
- Names on the entity documents match the identification, or a letter of explanation addresses any discrepancy.
- A Certificate of Good Standing or equivalent document valid within ninety (90) days of the closing date is present.
- A Certificate of Foreign Qualification or other qualification to operate in the relevant state is present if the entity is formed in a state other than where business is conducted or the property is located.
- The entity’s IRS Form SS4 or Federal Taxpayer Identification Number (TIN) or Employer Identification Number (EIN) issuance letter is present, or an EIN exception request with a letter of explanation stating the applicable grounds is submitted for Acra's Legal Department review.
- A Unanimous Written Consent / Board Resolution signed by all members regardless of their percentage of interest authorizes the transaction with Acra Lending and identifies who is authorized to sign the loan documents on behalf of and to bind the entity.
- Any Power of Attorney used to designate an attorney in fact to execute a personal guarantee is utilized by the principal for that purpose.
- Borrower letters stating that required documents are not required, available, or excused are not accepted in place of the required documents.

**Reads:** Borrower.entity_type, Borrower.entity_documents_complete, Borrower.is_entity_borrower_1
**Missing data:** The complete applicable Operating Agreement or Bylaws, referenced exhibits, amendments, and required contents., Ownership-interest documents and, when applicable, share certificates, stock ledger, Affidavit of Lost Stock Certificate, K-1 statements, and CPA or Tax Preparer letter., Identification for comparison with names on entity documents and any letter of explanation., The Certificate of Good Standing or equivalent and its validity relative to the closing date., The entity’s formation state, state of business, property state, and any required qualification document., The entity’s SS4, TIN or EIN issuance letter, or EIN exception request and letter of explanation., The Unanimous Written Consent / Board Resolution and its signers and contents., Any Power of Attorney used for a personal guarantee., Whether formation documents conflict with the Operating Agreement or Bylaws, and any additional documentation Legal requires.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.required_entity_guarantors

**Purpose:** Determine whether the required individuals provide the required recourse guarantees for an entity borrower.

1. Initial Document Review: Review entity ownership documents and the loan file for direct and indirect ownership interests and submitted guarantees.
2. Eligibility Verification: Identify all individuals with direct or indirect ownership ≥ 20% of the entity borrower.
3. Validation and Verification: Verify that each identified individual provides an Acra approved recourse guarantee or Exhibit 7; where there are multiple guarantors, verify that all recourse is joint and several.
4. Final Determination: Record whether every required guarantee is present and meets the stated requirements.

**Checks:**
- All individuals with direct or indirect ownership ≥ 20% provide a recourse guarantee (Acra approved, or Exhibit 7).
- All recourse is joint and several where there are multiple guarantors.

**Reads:** Borrower.entity_type
**Missing data:** Each individual’s direct and indirect ownership percentage., The identity and number of guarantors., Whether each submitted guarantee is Acra approved or Exhibit 7., Whether the guarantees provide joint and several recourse when there are multiple guarantors.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.revocable_living_trust_title_vesting

**Purpose:** Determine whether title may vest in the proposed inter vivos revocable trust under the stated requirements.

1. Initial Document Review: Review the title commitment and the complete, legible Trust or Certification of Trust, and identify the Trustors, Trustees, beneficiaries, and trust terms.
2. Eligibility Verification: Verify that the Trust is valid under the laws of the state in which it is established; is revocable; is established by one or more natural persons and becomes effective during their lifetime; and has the individual(s) establishing the Trust as primary beneficiary.
3. Validation and Verification: Verify that the Trust or Certification of Trust contains every stated required item. Verify the Trustee’s authority and the provisions concerning beneficiary consent, lender risk, and creditor rights. If the Trustors and Trustees are not the same, obtain written exception by Acra Senior Management.
4. Final Determination: Record whether all applicable trust requirements are met; do not treat an irrevocable trust as permitted.

**Checks:**
- A complete, legible copy of the Trust or a Certification of Trust stating all required trust information is present.
- The Trust is valid under the laws of the state in which it is established.
- The Trust is revocable and can be changed or canceled at any time for any reason during a Trustor's lifetime.
- The Trust is established by one or more natural persons, solely or jointly, and becomes effective during the lifetime of the person(s) establishing it.
- The primary beneficiary of the Trust is the individual(s) establishing the Trust.
- Written exception by Acra Senior Management is obtained if the Trustor(s) and Trustee(s) are not the same.
- The Trust specifies the Trustee’s power to hold title and mortgage the property; that the beneficiary does not need to grant written consent for the Trust to borrow money, or that such consent has been granted in writing for purposes of the mortgage; that there is no unusual risk or impairment to the lender's rights; and that holding title in the Trust does not diminish the lender's rights as a creditor.

**Reads:** Borrower.entity_type
**Missing data:** The complete Trust or Certification of Trust and its required statements: existence and date; Trustor(s) and current Trustee(s); Trustee powers; revocability and the person holding the right to revoke; required signing Trustees; trust identification number; how title to Trust assets should be taken; and confirmation that the Trust has not been revoked, modified, or amended., The state where the Trust is established and whether it is valid under that state’s laws., Whether the Trust can be changed or canceled at any time for any reason during a Trustor's lifetime., Whether the Trust was established by natural person(s) and became effective during their lifetime., The primary beneficiary or beneficiaries of the Trust., Whether Trustor(s) and Trustee(s) are the same and, if not, whether Acra Senior Management provided written exception., The Trust provisions concerning title, mortgage authority, beneficiary consent, unusual risk or impairment, and the lender’s creditor rights., Whether Legal requires additional supporting documentation in its sole discretion.

## acra-platinum.compliance_and_closing_the_borrowing_entity_and_title.single_purpose_entity_qualification

**Purpose:** Determine whether an entity borrower qualifies as a single purpose entity (SPE).

1. Initial Document Review: Review entity documents for the entity’s assets and business activities.
2. Eligibility Verification: Determine whether the entity has no assets other than residential investment or rental properties and is engaged in the business of owning and operating residential investment or rental properties.
3. Validation and Verification: Verify the entity’s assets and activities against the entity documents and any other reviewed supporting documentation.
4. Final Determination: Record whether the entity meets the SPE requirement.

**Checks:**
- The entity has no assets other than residential investment or rental properties.
- The entity is engaged in the business of owning and operating residential investment or rental properties.

**Reads:** Borrower.entity_type
**Missing data:** The entity’s assets and whether any are other than residential investment or rental properties., Whether the entity is engaged in owning and operating residential investment or rental properties.

## acra-platinum.credit_review_analysis_credit.correspondent_cltv

**Purpose:** Check the Correspondent pricing limitation stated for decisioning scores from 700-719.

1. Initial Document Review: Review the credit report and loan application for the decisioning score and loan channel and the loan record for CLTV.
2. Eligibility Verification: Determine whether the loan is Correspondent and the decisioning score is within 700-719.
3. Validation and Verification: For a loan meeting both conditions, verify CLTV against the 60% limit.
4. Final Determination: Record whether the applicable 60% CLTV limit is met; if either applicability condition is absent, this limitation does not apply.

**Checks:**
- The loan is not Correspondent with a decisioning score from 700-719, or its CLTV is no greater than 60%.

**Reads:** LoanCore.channel, LoanCore.cltv_percent
**Missing data:** The established decisioning score, which is not held in a case field.

## acra-platinum.credit_review_analysis_credit.decisioning_score

**Purpose:** Establish the decisioning credit score used for the credit requirements.

1. Initial Document Review: Review the credit report and, for a loan closing in the name of an entity, the entity documents and loan application for the personal guarantors and ownership information.
2. Eligibility Verification: For a non-entity loan, identify the Primary Wage Earner middle score. For an entity loan, use the highest middle score of the personal guarantors when ownership percentages are equal; if ownership percentages differ, use the individual with the highest concentration of ownership.
3. Validation and Verification: Verify the score and, where applicable, ownership information against the reviewed documents. Do not assume a decisioning-score rule for one or two scores, no-score cases, or equal largest ownership interests where ownership is not equal across all guarantors; those matters are identified as requiring Acra confirmation.
4. Final Determination: Record the decisioning score only when the applicable selection rule establishes it; otherwise record that the score cannot be determined under the stated rule and that confirmation is requested.

**Checks:**
- The decisioning score is established using the applicable PLAT-6.1 selection rule, or an unresolved PLAT-6.1 case is identified for Acra confirmation.
**Missing data:** Primary Wage Earner identification where relevant; each relevant person's middle score; guarantor ownership percentages and ownership concentration; Acra confirmation for one-score, two-score, no-score, and equal-largest-ownership cases.

## acra-platinum.credit_review_analysis_credit.escrow_waiver_loan_amount

**Purpose:** Verify that an escrow-waiver loan does not exceed the stated maximum loan amount.

1. Initial Document Review: Review the loan record for escrow-waiver status and total loan amount.
2. Eligibility Verification: If escrow is waived, apply the maximum loan amount of $1.5M.
3. Validation and Verification: Compare the total loan amount with $1.5M when the waiver applies.
4. Final Determination: Record whether the applicable maximum is met.

**Checks:**
- LoanCore.is_escrow_waived is false, or LoanCore.total_loan_amount_usd is no greater than $1.5M.

**Reads:** LoanCore.is_escrow_waived, LoanCore.total_loan_amount_usd

## acra-platinum.credit_review_analysis_credit.escrow_waiver_mortgage_history

**Purpose:** Verify the stated mortgage-history requirement for an escrow waiver.

1. Initial Document Review: Review escrow-waiver status and the credit report's mortgage-history information.
2. Eligibility Verification: If escrow is waived, apply the stated “0x30x24 Mortgage History required” requirement.
3. Validation and Verification: Verify the reported mortgage history against the stated label; do not add a definition for the label.
4. Final Determination: Record whether the stated mortgage-history requirement is met.

**Checks:**
- LoanCore.is_escrow_waived is false, or CreditReport.mortgage_0x30x24 is true.

**Reads:** LoanCore.is_escrow_waived, CreditReport.mortgage_0x30x24

## acra-platinum.credit_review_analysis_credit.first_time_homebuyer

**Purpose:** Apply the Platinum First Time Homebuyer ineligibility.

1. Initial Document Review: Review the loan application for first-time-homebuyer information.
2. Eligibility Verification: Determine whether the borrower is a First Time Homebuyer (FTHB).
3. Validation and Verification: Verify the determination against the case information and reviewed application.
4. Final Determination: Record that an FTHB is ineligible for this program.

**Checks:**
- Borrower.is_first_time_homebuyer is false.

**Reads:** Borrower.is_first_time_homebuyer

## acra-platinum.credit_review_analysis_credit.housing_history_standard

**Purpose:** Apply the Platinum Summary housing-history standard as printed.

1. Initial Document Review: Review the credit report for the reported housing-history rating.
2. Eligibility Verification: Apply the stated standard “0x30x12”.
3. Validation and Verification: Compare the reported rating with the stated standard; do not infer a definition for “0x30x12”, which the source identifies as requiring Acra confirmation.
4. Final Determination: Record whether the stated label is met, and identify the unresolved definition for confirmation where it prevents verification.

**Checks:**
- The housing-history rating is established as meeting “0x30x12” under a confirmed definition.

**Reads:** CreditReport.housing_history_rating
**Missing data:** The definition of “0x30x12” and confirmation of whether the case's housing-history rating meets that definition.

## acra-platinum.credit_review_analysis_credit.minimum_decisioning_score

**Purpose:** Apply the Platinum minimum decisioning score requirement.

1. Initial Document Review: Review the credit report and the established decisioning score.
2. Eligibility Verification: Apply the minimum decisioning score of 700; the source states that no matrix row is below 700.
3. Validation and Verification: Verify the decisioning score against the reviewed credit information and the applicable score determination.
4. Final Determination: Record whether the decisioning score is at least 700.

**Checks:**
- The decisioning score is at least 700.
**Missing data:** The established decisioning score, which is not held in a case field.

## acra-platinum.credit_review_analysis_credit.mortgage_and_rental_history_documentation

**Purpose:** Determine whether the file contains the history documentation required for mortgage/rental rating and DSCR payment history.

1. Initial Document Review: Review all reported mortgages on credit and the file's documentation of mortgage and rental payment history over the last twelve (12) months.
2. Eligibility Verification: For DSCR loans, require documentation for the subject property, the borrower's and/or guarantor's primary residence, and second home(s), if any. Additional properties do not require housing history to be documented unless documents in the file suggest a major credit event has occurred. For mortgages not reported on credit, the file should contain documentation to evaluate history on the applicant's primary residence(s), any secondary residence(s), and the subject property.
3. Validation and Verification: Verify that the required property histories are documented and that the history can be evaluated. For a matured loan, use its maturity date for rating; verify that any extension of the maturity date is in writing.
4. Final Determination: Record whether the required history is documented and evaluable, and whether any applicable maturity-date extension is in writing.

**Checks:**
- The required mortgage and rental histories are documented for evaluation, and any extension of a matured loan's maturity date is in writing.

**Reads:** LoanCore.dscr_qualification_method
**Missing data:** Which properties are the borrower's and/or guarantor's primary residence(s), secondary residence(s), and second home(s); whether a loan has matured and its maturity date; whether any maturity-date extension exists and is in writing; whether file documents suggest a major credit event.

## acra-platinum.credit_review_analysis_credit.tradelines

**Purpose:** Verify the Platinum tradeline requirement.

1. Initial Document Review: Review the credit report for the number of repositories, tradelines, and history.
2. Eligibility Verification: Applicants with scores from 3 repositories have no tradeline overlay. Applicants with 2 or fewer scores must have 2 tradelines & 24 month history or 3 tradelines & 12 month history; applicants with one score are within “2 or fewer scores.”
3. Validation and Verification: Verify the applicable repository and tradeline requirement against the credit report.
4. Final Determination: Record whether the applicable tradeline requirement is met.

**Checks:**
- CreditReport.score_count is 3, or the applicant with 2 or fewer scores meets the stated tradeline requirement.

**Reads:** CreditReport.score_count, CreditReport.tradelines_meet_requirement
**Missing data:** For applicants with 2 or fewer scores, the number of tradelines and their history in months, if these are not represented by CreditReport.tradelines_meet_requirement.

## acra-platinum.identification_requirements.application_non_fthb_attestation

**Purpose:** Verify the application attestation requirement stated in PLAT-4.5 and attributed there to §3.12 and PLAT-5.9. Whether it applies to individual borrowers as well as entities is part of Q-13.

1. Initial Document Review: Review the loan application for a borrower or guarantor attestation concerning first-time-homebuyer status.
2. Eligibility Verification: Identify whether at least one borrower or guarantor is required to provide the stated attestation; applicability to individual borrowers as well as entities is part of Q-13.
3. Validation and Verification: Verify that at least one borrower / guarantor attests on the application that they are not a first-time homebuyer.
4. Final Determination: Determine whether the application attestation requirement is met.

**Checks:**
- At least one borrower / guarantor attests on the application that they are not a first-time homebuyer.

**Reads:** Borrower.is_first_time_homebuyer

## acra-platinum.identification_requirements.eligible_borrower_citizenship

**Purpose:** Determine whether the borrower is a US Citizen or Permanent Resident, the eligible citizenship types stated in PLAT-4.1.

1. Initial Document Review: Read the borrower's citizenship status recorded in the case.
2. Eligibility Verification: Compare the status with the two eligible types: US Citizen and Permanent Resident.
3. Validation and Verification: Establish whether the recorded status is one of those eligible types.
4. Final Determination: Determine whether the borrower meets the stated citizenship eligibility requirement.

**Checks:**
- Borrower.citizenship_status is US Citizen or Permanent Resident.

**Reads:** Borrower.citizenship_status

## acra-platinum.identification_requirements.first_time_homebuyer_eligibility

**Purpose:** Apply PLAT-4.4, which states that a First Time Homebuyer is ineligible and defines one as an application where all Applicants have never previously owned a home (real property).

1. Initial Document Review: Read the borrower's first-time-homebuyer status recorded in the case.
2. Eligibility Verification: Apply the source definition: an application where all Applicants have never previously owned a home (real property).
3. Validation and Verification: Establish whether the borrower is recorded as a first-time homebuyer.
4. Final Determination: Determine whether the borrower meets the program's first-time-homebuyer eligibility requirement.

**Checks:**
- Borrower.is_first_time_homebuyer is false.

**Reads:** Borrower.is_first_time_homebuyer

## acra-platinum.identification_requirements.guarantor_prior_homeownership

**Purpose:** Verify the §3.12 requirement stated in PLAT-4.5 that at least one guarantor have prior homeownership experience. Whether this applies to individual borrowers as well as entities is part of Q-13.

1. Initial Document Review: Review available information establishing guarantor homeownership history.
2. Eligibility Verification: Identify the guarantors for the case; the requirement is for at least one guarantor to have prior homeownership experience.
3. Validation and Verification: Verify whether at least one guarantor has prior homeownership experience. The source does not resolve whether the requirement applies to individual borrowers as well as entities; that question is part of Q-13.
4. Final Determination: Determine whether at least one guarantor has prior homeownership experience.

**Checks:**
- At least one guarantor has prior homeownership experience.
**Missing data:** Guarantor identity and prior homeownership history.

## acra-platinum.identification_requirements.permanent_resident_documents

**Purpose:** Verify the additional documentation requirement for a Permanent Resident stated in PLAT-4.2.

1. Initial Document Review: For a Permanent Resident, obtain and review the PRA ID and SSA card / SSA-89.
2. Eligibility Verification: Establish whether the borrower is a Permanent Resident; this document requirement applies to Permanent Residents.
3. Validation and Verification: Verify that the PRA ID is unexpired and that the borrower has an SSA card / SSA-89.
4. Final Determination: Determine whether the Permanent Resident documentation requirement is met.

**Checks:**
- If the borrower is a Permanent Resident, the borrower has an unexpired PRA ID and an SSA card / SSA-89.

**Reads:** Borrower.citizenship_status
**Missing data:** PRA ID and its expiration status; SSA card or SSA-89.

## acra-platinum.income_stability_sufficiency_analysis.calculate_dscr

**Purpose:** Establish the DSCR using the program's stated qualifying rent, denominator, and payment basis.

1. Step 1 - Initial Document Review: Review the Form 1007 or 1025 for market rent and any lease and rent-receipt evidence for actual rent being considered.
2. Step 2 - Eligibility Verification: Identify the market rent and actual rent amounts applicable to the calculation; actual rent must meet the program's stated documentation and lease-duration requirements and is for long-term rents only.
3. Step 3 - Validation and Verification: Calculate qualifying rent as the greater of market rent as established on the 1007 or 1025, or actual rent. Calculate the denominator using annual PITIA and subordinate financing, if applicable, and use the first payment due under the terms of the Note.
4. Step 4 - Final Determination: Record the resulting DSCR.

**Checks:**
- Qualifying rent is the greater of market rent as established on the 1007 or 1025, or actual rent.
- The denominator is the sum of annual principal, interest, real estate taxes, property insurance, homeowner's / condominium association fees (PITIA), and subordinate financing, if applicable.
- The DSCR utilizes the first payment due under the terms of the Note.
**Missing data:** Market rent established on the 1007 or 1025, Actual rent amount, if used, Annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees, Subordinate financing amount, if applicable, The first payment due under the terms of the Note, Calculated DSCR

## acra-platinum.income_stability_sufficiency_analysis.meet_channel_minimum_dscr

**Purpose:** Establish that the loan meets the applicable channel minimum DSCR.

1. Step 1 - Initial Document Review: Review the DSCR calculation and the loan's channel.
2. Step 2 - Eligibility Verification: Identify the applicable channel minimum: Correspondent ≥ 1.2; Wholesale ≥ 1.0.
3. Step 3 - Validation and Verification: Compare the calculated DSCR with the applicable channel minimum.
4. Step 4 - Final Determination: Record whether the loan meets the applicable channel minimum.

**Checks:**
- The calculated DSCR is at least 1.2 for Correspondent or at least 1.0 for Wholesale.

**Reads:** LoanCore.channel
**Missing data:** Calculated DSCR

## acra-platinum.income_stability_sufficiency_analysis.qualify_actual_rent

**Purpose:** Establish whether actual rent meets the program's stated documentation, lease-duration, and rental-term requirements.

1. Step 1 - Initial Document Review: Review the lease agreement and bank statements for the actual rent being considered.
2. Step 2 - Eligibility Verification: Confirm that actual rent is being used for a long-term rental, not a short-term rental.
3. Step 3 - Validation and Verification: Verify evidence of 2 months’ proof of receipts and that the lease is in place for at least 3 months after the loan closing.
4. Step 4 - Final Determination: Record whether the actual-rent requirements are met.

**Checks:**
- Actual rent is documented via evidence of 2 months’ proof of receipts.
- The lease is in place for at least 3 months after the loan closing.
- Actual rent is used for a long-term rent, not a short-term rental.
**Missing data:** Evidence of 2 months’ proof of actual-rent receipts, Lease end date relative to the loan closing, Whether the rent is long-term or short-term

## acra-platinum.income_stability_sufficiency_analysis.reject_short_term_rental

**Purpose:** Establish whether the subject property is ineligible because it is a short-term rental.

1. Step 1 - Initial Document Review: Review available rental documentation for the subject property's rental term.
2. Step 2 - Eligibility Verification: Determine whether the rental is short-term.
3. Step 3 - Validation and Verification: Verify the rental term using the available rental documentation.
4. Step 4 - Final Determination: Record whether the subject property's rental is short-term; short-term rentals are ineligible for the program.

**Checks:**
- The subject property is not a short-term rental.
**Missing data:** Whether the subject property's rental is short-term

## acra-platinum.income_stability_sufficiency_analysis.require_form_1007

**Purpose:** Establish that the required rent schedule is present.

1. Step 1 - Initial Document Review: Review the appraisal report for a Form 1007.
2. Step 2 - Eligibility Verification: Confirm the case is a DSCR transaction.
3. Step 3 - Validation and Verification: Verify that the report includes the Form 1007.
4. Step 4 - Final Determination: Record whether the required Form 1007 is present.

**Checks:**
- A Form 1007 is provided for the DSCR transaction.
**Missing data:** Whether the appraisal report contains a Form 1007

## acra-platinum.income_stability_sufficiency_analysis.support_excessive_lease_rent

**Purpose:** Establish that the required support for excessive monthly rent reflected on the lease is provided.

1. Step 1 - Initial Document Review: Review the lease agreement for monthly rent and the appraisal report, if provided, for a Form 1007.
2. Step 2 - Eligibility Verification: Determine whether this is a single-family investment property with excessive monthly rent payments reflected on the lease.
3. Step 3 - Validation and Verification: If the condition applies, verify documentation supporting that the monthly rent is typical for the area. Acceptable documentation may include classified ads from local newspapers, a 1007 completed by the appraiser, or a market rent survey completed by a local real estate company or rental management company familiar with the market rents in the area.
4. Step 4 - Final Determination: Record whether the required supporting documentation is provided when the condition applies.

**Checks:**
- For a single-family investment property with excessive monthly rent payments reflected on the lease, documentation supports that the monthly rent is typical for the area.

**Reads:** SubjectProperty.property_type, SubjectProperty.occupancy_subtype
**Missing data:** Whether monthly rent reflected on the lease is excessive for the area, Documentation supporting that the monthly rent is typical for the area

## acra-platinum.income_stability_sufficiency_analysis.verify_cash_out_lease

**Purpose:** Establish the current-lease requirement for cash-out refinances.

1. Step 1 - Initial Document Review: For a cash-out refinance, review the lease agreement for the subject property.
2. Step 2 - Eligibility Verification: Determine whether the loan purpose is cash-out refinance.
3. Step 3 - Validation and Verification: If the loan purpose is cash-out refinance, verify that a current lease agreement is provided.
4. Step 4 - Final Determination: Record whether the current-lease requirement is met when the loan purpose is cash-out refinance.

**Checks:**
- If the loan purpose is cash-out refinance, a current lease agreement is provided.

**Reads:** LoanCore.loan_purpose
**Missing data:** Whether the lease agreement is current

## acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability

**Purpose:** Determine whether rent loss insurance is required for the subject property.

1. Step 1 - Initial Document Review: Review the available case information for the subject property's unit count, occupancy, and whether its rents are used to qualify.
2. Step 2 - Eligibility Verification: Determine whether the property is a one- to four-unit non-owner occupied income property, whether subject property rents are used to qualify, and whether LTV exceeds 70%.
3. Step 3 - Validation and Verification: Apply the stated exemption for loans with ≤ 70% CLTV. If LTV is at or below 70% and CLTV is above 70%, request Acra confirmation (Q-10).
4. Step 4 - Final Determination: Record whether rent loss insurance is required, not required, or awaiting Acra confirmation for the specified LTV/CLTV case.

**Checks:**
- The subject property has one to four units.
- The subject property is non-owner occupied.
- Subject property rents are used to qualify.
- The loan's LTV is greater than 70%.
- The loan's CLTV is ≤ 70%.
- For a loan with LTV at or below 70% and CLTV above 70%, Acra confirmation has been obtained.

**Reads:** SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype, LoanCore.cltv_percent
**Missing data:** Whether subject property rents are used to qualify, The loan's LTV, Acra confirmation for the case with LTV at or below 70% and CLTV above 70%

## acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_coverage

**Purpose:** Determine whether the rent loss insurance coverage meets the stated coverage requirement.

1. Step 1 - Initial Document Review: Review the hazard insurance declarations for rent loss insurance and its stated coverage.
2. Step 2 - Eligibility Verification: Apply this review when rent loss insurance is required under the Rent Loss Insurance Applicability determination.
3. Step 3 - Validation and Verification: Verify from the declarations whether coverage is for rental losses incurred during rehabilitation following a casualty and whether six months of coverage is provided.
4. Step 4 - Final Determination: Record whether the required coverage is provided or whether the case must be assessed for the permitted reserve substitution.

**Checks:**
- The hazard insurance declarations establish rent loss insurance for rental losses incurred during rehabilitation following a casualty.
- The hazard insurance declarations establish six months of rent loss insurance coverage.
**Missing data:** Whether the policy covers rental losses incurred during rehabilitation following a casualty, The duration of rent loss insurance coverage

## acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_reserve_substitution

**Purpose:** Determine whether the permitted reserve substitution is sufficient when required rent loss insurance cannot be obtained.

1. Step 1 - Initial Document Review: Review the hazard insurance declarations for rent loss coverage provided and the coverage period not provided.
2. Step 2 - Eligibility Verification: Apply this review only when rent loss insurance is required and cannot be obtained.
3. Step 3 - Validation and Verification: Compare reserves to the required substitution of two months of reserves for every one month of rent loss coverage not provided.
4. Step 4 - Final Determination: Record whether the reserves meet the substitution amount, are awaiting the information needed to assess it, or are insufficient.

**Checks:**
- Required rent loss insurance cannot be obtained.
- Reserves are at least two months for every one month of rent loss coverage not provided.

**Reads:** RatioSet.reserves_months
**Missing data:** Whether required rent loss insurance cannot be obtained, The number of months of rent loss coverage not provided

## acra-platinum.loan_program_eligibility.borrower_citizenship

**Purpose:** Verify that the borrower meets the Platinum Select citizenship requirement.

1. Initial Document Review: Review the loan application and borrower-provided identity evidence for citizenship or residency status.
2. Eligibility Verification: Verify that the borrower is a US Citizen or Permanent Resident.
3. Validation and Verification: Compare the stated status with the borrower evidence.
4. Final Determination: Record whether the borrower meets the citizenship requirement.

**Checks:**
- Borrower.citizenship_status is US Citizen or Permanent Resident.

**Reads:** Borrower.citizenship_status

## acra-platinum.loan_program_eligibility.cash_out_current_lease

**Purpose:** Verify the required current lease agreement for a Cash-Out Refinance.

1. Initial Document Review: Review the loan application for the loan purpose and review the current lease agreement for the subject property.
2. Eligibility Verification: Apply this requirement to a Cash-Out Refinance.
3. Validation and Verification: Verify that a current lease agreement is present for the subject property.
4. Final Determination: Record whether the Cash-Out Refinance has a current lease agreement.

**Checks:**
- If LoanCore.loan_purpose is Cash-Out Refinance, a current lease agreement is present for the subject property.

**Reads:** LoanCore.loan_purpose, SubjectProperty.has_current_lease
**Missing data:** Whether the lease agreement is current

## acra-platinum.loan_program_eligibility.correspondent_fico_cltv_cap

**Purpose:** Verify the Correspondent CLTV restriction for loans with a score from 700 through 719.

1. Initial Document Review: Review the loan application and credit report for channel, representative score, and CLTV.
2. Eligibility Verification: Apply the 60% CLTV restriction when the channel is Correspondent and the score is 700-719 FICO.
3. Validation and Verification: Verify the recorded channel, score, and CLTV against the source evidence.
4. Final Determination: Record whether the applicable Correspondent restriction is met.

**Checks:**
- If LoanCore.channel is Correspondent and CreditReport.representative_score is from 700 through 719, LoanCore.cltv_percent is no more than 60%.

**Reads:** LoanCore.channel, CreditReport.representative_score, LoanCore.cltv_percent

## acra-platinum.loan_program_eligibility.delayed_financing_loan_cap

**Purpose:** Verify the published loan amount cap for Delayed Financing.

1. Initial Document Review: Review the loan application for the loan purpose and loan amount.
2. Eligibility Verification: Apply the $1.5MM cap to Delayed Financing.
3. Validation and Verification: Verify the recorded purpose and amount against the loan application.
4. Final Determination: Record whether the Delayed Financing loan amount is within the cap.

**Checks:**
- If LoanCore.loan_purpose is Delayed Financing, LoanCore.total_loan_amount_usd is no more than $1,500,000.

**Reads:** LoanCore.loan_purpose, LoanCore.total_loan_amount_usd

## acra-platinum.loan_program_eligibility.eligible_loan_purpose

**Purpose:** Determine the named fact of whether the loan purpose is eligible.

1. Initial Document Review: Review the loan application for the requested loan purpose.
2. Eligibility Verification: Compare the loan purpose with the eligible purposes: Purchase, Rate & Term Refinance, Cash-Out Refinance, and Delayed Financing.
3. Validation and Verification: Verify that the recorded loan purpose agrees with the loan application.
4. Final Determination: Record whether the loan purpose is eligible.

**Checks:**
- LoanCore.loan_purpose is Purchase, Rate & Term Refinance, Cash-Out Refinance, or Delayed Financing.

**Reads:** LoanCore.loan_purpose

## acra-platinum.loan_program_eligibility.eligible_location

**Purpose:** Verify the published ineligible-location restriction.

1. Initial Document Review: Review the loan application and appraisal report for the subject property location.
2. Eligibility Verification: Identify whether the property is in SD or U.S. Terrs.
3. Validation and Verification: Verify the recorded state against the property evidence.
4. Final Determination: Record whether the property is outside the listed ineligible locations.

**Checks:**
- SubjectProperty.state is not SD or U.S. Terrs.

**Reads:** SubjectProperty.state

## acra-platinum.loan_program_eligibility.eligible_property_type

**Purpose:** Determine the named fact of whether the subject property type is an eligible type.

1. Initial Document Review: Review the loan application and appraisal report for the subject property type.
2. Eligibility Verification: Compare the property type with the listed eligible types: SFR, Townhome, PUD, Warrantable Condo, and Two-Units.
3. Validation and Verification: Verify that the recorded property type agrees with the property evidence.
4. Final Determination: Record whether the subject property type is eligible.

**Checks:**
- SubjectProperty.property_type is SFR, Townhome, PUD, Warrantable Condo, or Two-Units.

**Reads:** SubjectProperty.property_type

## acra-platinum.loan_program_eligibility.first_time_homebuyer

**Purpose:** Determine whether the borrower is a first-time homebuyer and apply the stated ineligibility.

1. Initial Document Review: Review the loan application for the borrower's first-time homebuyer status.
2. Eligibility Verification: Apply the Platinum Select restriction that first-time homebuyers are ineligible.
3. Validation and Verification: Verify the recorded status against the loan application.
4. Final Determination: Record whether the borrower meets this eligibility requirement.

**Checks:**
- Borrower.is_first_time_homebuyer is false.

**Reads:** Borrower.is_first_time_homebuyer

## acra-platinum.loan_program_eligibility.interest_only_cltv_cap

**Purpose:** Verify the stated maximum CLTV for an Interest-Only (5 Yr Term) loan.

1. Initial Document Review: Review the loan application and mortgage loan information for interest-only status and CLTV.
2. Eligibility Verification: Apply the 75.00% maximum CLTV to Interest-Only (5 Yr Term).
3. Validation and Verification: Verify the product term and CLTV from the loan records.
4. Final Determination: Record whether the applicable maximum CLTV is met.

**Checks:**
- If MortgageLoanInformation.is_interest_only is true, LoanCore.cltv_percent is no more than 75.00%.

**Reads:** MortgageLoanInformation.is_interest_only, LoanCore.cltv_percent
**Missing data:** Whether the interest-only term is 5 Yr

## acra-platinum.loan_program_eligibility.interest_only_listed_for_sale_restriction

**Purpose:** Apply the restriction that Interest-Only is not available on a property listed for sale.

1. Initial Document Review: Review the loan application and listing history for interest-only status and listing status.
2. Eligibility Verification: Apply the restriction that Interest-Only is not available on a property listed for sale.
3. Validation and Verification: Verify the listing status from the listing history and the loan record.
4. Final Determination: Record whether the restriction is met.

**Checks:**
- If MortgageLoanInformation.is_interest_only is true, SubjectProperty.is_listed_for_sale is false.

**Reads:** MortgageLoanInformation.is_interest_only, SubjectProperty.is_listed_for_sale

## acra-platinum.loan_program_eligibility.listed_for_sale_cltv_cap

**Purpose:** Verify the stated LTV / CLTV maximum for a property listed for sale within six months.

1. Initial Document Review: Review listing history and the loan application for listing dates and CLTV.
2. Eligibility Verification: Apply the 65% LTV / CLTV maximum when the property was listed for sale within six months.
3. Validation and Verification: Verify the listing period and CLTV against the source evidence.
4. Final Determination: Record whether the applicable cap is met.

**Checks:**
- If SubjectProperty.listed_for_sale_last_6_months is true, LoanCore.cltv_percent is no more than 65%.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, LoanCore.cltv_percent

## acra-platinum.loan_program_eligibility.listed_for_sale_prepayment_term

**Purpose:** Verify the stated minimum prepayment penalty term when the property was listed for sale within six months.

1. Initial Document Review: Review listing history, the loan application, and the subject property state for the listing period, selected prepayment penalty term, and state.
2. Eligibility Verification: For a property listed for sale within six months, require a prepayment penalty of at least three (3) years unless the property is in a state that does not allow prepayment penalties.
3. Validation and Verification: Verify the listing period, selected term, and any applicable state restriction from the source evidence. Do not resolve an interaction between the state restriction and the minimum term beyond the source wording.
4. Final Determination: Record whether the stated minimum term applies and is met, subject to the printed state exception.

**Checks:**
- If SubjectProperty.listed_for_sale_last_6_months is true and the property is not in a state that does not allow prepayment penalties, the prepayment penalty term is at least three (3) years.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.state, LoanCore.prepayment_penalty_structure
**Missing data:** The selected prepayment penalty term, Whether the property is in a state that does not allow prepayment penalties, How a state restriction interacts with the three-year minimum

## acra-platinum.loan_program_eligibility.loan_amount_range_and_increment

**Purpose:** Verify that the loan amount meets the published minimum, maximum, and increment requirements.

1. Initial Document Review: Review the loan application for the requested loan amount.
2. Eligibility Verification: Check the minimum and maximum loan amounts and the required increments.
3. Validation and Verification: Compare the recorded loan amount with the loan application and test that it falls in the stated range and increments.
4. Final Determination: Record whether the loan amount meets all three requirements.

**Checks:**
- LoanCore.total_loan_amount_usd is at least $100,000.
- LoanCore.total_loan_amount_usd is no more than $2,000,000.
- LoanCore.total_loan_amount_usd is in $50 increments.

**Reads:** LoanCore.total_loan_amount_usd

## acra-platinum.loan_program_eligibility.loan_size_cltv_cap

**Purpose:** Verify the loan-size CLTV cap when the loan amount is below $350,000 or above $1,500,000.

1. Initial Document Review: Review the loan application for the loan amount and CLTV.
2. Eligibility Verification: Apply a maximum CLTV of 75.00% when the loan amount is below $350,000 or above $1,500,000.
3. Validation and Verification: Verify the loan amount and CLTV against the loan application and underwriting record.
4. Final Determination: Record whether an applicable loan-size cap is met.

**Checks:**
- If LoanCore.total_loan_amount_usd is below $350,000 or above $1,500,000, LoanCore.cltv_percent is no more than 75.00%.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.cltv_percent

## acra-platinum.loan_program_eligibility.matrix_fico_and_cltv

**Purpose:** Apply the printed FICO and CLTV matrix to the loan purpose and verify the applicable maximum CLTV.

1. Initial Document Review: Review the credit report and loan application for the representative score, loan purpose, and CLTV.
2. Eligibility Verification: Apply the printed matrix: at 730 and above, Purchase 80%, Rate & Term 80%, Cash-Out 75%; at 721–729, Purchase 80%, Rate & Term 80%, Cash-Out 65%; at 700–720, Purchase 80%, Rate & Term 80%, Cash-Out 55%. No row is printed below 700.
3. Validation and Verification: Verify the recorded score, purpose, and CLTV against the source evidence and the applicable printed matrix row.
4. Final Determination: Record whether the score has a printed row and the CLTV does not exceed its applicable matrix maximum.

**Checks:**
- CreditReport.representative_score is at least 700.
- For Purchase, Rate & Term Refinance, or Cash-Out Refinance with a representative score of at least 700, LoanCore.cltv_percent does not exceed the maximum in the applicable printed FICO row and loan-purpose column.

**Reads:** CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent

## acra-platinum.loan_program_eligibility.minimum_dscr

**Purpose:** Verify the minimum DSCR: Correspondent ≥ 1.2; Wholesale ≥ 1.0.

1. Initial Document Review: Review the loan application and underwriting record for channel and the DSCR and rent information used for qualification.
2. Eligibility Verification: Apply Correspondent ≥ 1.2 or Wholesale ≥ 1.0, as applicable.
3. Validation and Verification: Verify the DSCR value and the qualifying-rent basis. The qualifying rent is the greater of the market rent or actual rent.
4. Final Determination: Record whether the applicable minimum DSCR is met.

**Checks:**
- For a Correspondent loan, DSCR is at least 1.2.
- For a Wholesale loan, DSCR is at least 1.0.

**Reads:** LoanCore.channel
**Missing data:** The DSCR value used for qualification, Market rent, Actual rent, The qualifying-rent basis used in the DSCR

## acra-platinum.loan_program_eligibility.non_owner_occupied_status

**Purpose:** Determine the named fact of whether the property is non-owner occupied and leased and occupied as a principal year-round residence by individuals other than the owner.

1. Initial Document Review: Review the loan application and any lease agreement or rent roll for the subject property’s occupancy and lease information.
2. Eligibility Verification: Determine whether the property is non-owner occupied.
3. Validation and Verification: Verify from the occupancy and lease evidence whether the dwelling is leased and occupied as a principal year-round residence by individuals other than the owner.
4. Final Determination: Record whether the property meets the non-owner-occupied requirement.

**Checks:**
- SubjectProperty.occupancy_subtype indicates non-owner occupancy.
- The dwelling is leased and occupied as a principal year-round residence by individuals other than the owner.

**Reads:** SubjectProperty.occupancy_subtype
**Missing data:** Whether the dwelling is occupied as a principal year-round residence by individuals other than the owner

## acra-platinum.loan_program_eligibility.prepayment_structure

**Purpose:** Verify that the loan's prepayment penalty structure is one of the structures printed for Platinum Select.

1. Initial Document Review: Review the loan application for the selected prepayment penalty structure.
2. Eligibility Verification: Compare the selected structure with the structures printed: 5 Year 5% Fixed or Sequential Stepdown; 3 Year 5% Fixed or 3% Fixed; 2 Year 3% Fixed; 1 Year 3% Fixed; or No Prepay.
3. Validation and Verification: Verify the selected structure in the loan records against the printed list.
4. Final Determination: Record whether the selected structure is listed.

**Checks:**
- The selected prepayment penalty structure is one of the structures printed for Platinum Select.

**Reads:** LoanCore.prepayment_penalty_structure
**Missing data:** The selected prepayment penalty structure and its term

## acra-platinum.loan_program_eligibility.vacant_property_status

**Purpose:** Determine the named fact of whether the subject property is vacant.

1. Initial Document Review: Review the loan application and available property evidence for occupancy information.
2. Eligibility Verification: Determine whether the subject property is vacant.
3. Validation and Verification: Compare the recorded vacancy status with the property evidence.
4. Final Determination: Record whether the property is vacant.

**Checks:**
- SubjectProperty.is_vacant is false.

**Reads:** SubjectProperty.is_vacant

## acra-platinum.unassigned_provisions.dti_alternative_for_dscr_qualified_loans

**Purpose:** The sources do not establish whether the §11.5 43% DTI alternative applies to DSCR-qualified loans on Platinum Select.

1. Initial Document Review: Review the loan’s qualification method and any proposed DTI alternative.
2. Eligibility Verification: Identify whether a DTI alternative is being relied on for a DSCR-qualified loan.
3. Validation and Verification: Do not apply the DTI alternative or assume it is unavailable; mark its Platinum Select treatment as requiring confirmation.
4. Final Determination: Refer the open treatment for confirmation; do not determine compliance from the unanswered question.

**Checks:**
- A DTI alternative is being relied on for a DSCR-qualified loan.

**Reads:** LoanCore.dscr_qualification_method
**Missing data:** Whether a DTI alternative is being relied on for the loan.

## acra-platinum.unassigned_provisions.escrow_waiver_cltv_and_fico_limits

**Purpose:** The Platinum Summary does not state escrow-waiver CLTV and FICO limits; the applicable limits are an open question.

1. Initial Document Review: Review the escrow-waiver status, CLTV, and representative credit score.
2. Eligibility Verification: Identify whether an escrow waiver is requested or applies.
3. Validation and Verification: Do not import the Standard Summary figures or infer that no limits apply; mark the Platinum Select limits as requiring confirmation.
4. Final Determination: Refer the open limits for confirmation; do not determine compliance from the unanswered question.

**Checks:**
- LoanCore.is_escrow_waived is true.

**Reads:** LoanCore.is_escrow_waived, LoanCore.cltv_percent, CreditReport.representative_score

## acra-platinum.unassigned_provisions.interest_only_minimum_loan_amount_and_fico

**Purpose:** The Platinum Summary does not state an interest-only minimum loan amount or FICO requirement; the applicable parameters are an open question.

1. Initial Document Review: Review the loan product, loan amount, and representative credit score.
2. Eligibility Verification: Identify whether the loan is interest-only.
3. Validation and Verification: Do not import the Standard Summary figures or infer that no minimum applies; mark the Platinum Select parameters as requiring confirmation.
4. Final Determination: Refer the open parameters for confirmation; do not determine compliance from the unanswered question.

**Checks:**
- MortgageLoanInformation.is_interest_only is true.

**Reads:** MortgageLoanInformation.is_interest_only, LoanCore.total_loan_amount_usd, CreditReport.representative_score

## acra-platinum.unassigned_provisions.no_ratio_or_sub_1_0_dscr_treatment

**Purpose:** The Platinum Summary states channel minimum DSCRs but does not address No Ratio DSCR or ratios below those minimums; the treatment is an open question.

1. Initial Document Review: Review the loan’s DSCR qualification method, channel, and available rental-income and debt-service information.
2. Eligibility Verification: Identify whether the case involves No Ratio DSCR or a DSCR below the stated channel minimum.
3. Validation and Verification: Do not import the Standard Summary rule or treat the feature as prohibited; mark the Platinum Select treatment as requiring confirmation.
4. Final Determination: Refer the open treatment for confirmation; do not determine eligibility from the unanswered question.

**Checks:**
- The case involves No Ratio DSCR or a DSCR below the stated channel minimum.

**Reads:** LoanCore.dscr_qualification_method, LoanCore.channel
**Missing data:** The calculated DSCR and the qualifying rental-income and debt-service data needed to establish it.

## acra-platinum.unassigned_provisions.one_or_no_credit_score_treatment

**Purpose:** The Platinum Summary does not address the treatment of applicants with one or no credit score beyond the tradeline rule; the treatment is an open question.

1. Initial Document Review: Review the credit-score information for the applicant.
2. Eligibility Verification: Determine whether the applicant has one or no credit score.
3. Validation and Verification: Do not import the Standard Summary rule or infer a no-score pathway; mark the Platinum Select treatment as requiring confirmation.
4. Final Determination: Refer the open treatment for confirmation; do not determine eligibility from the unanswered question.

**Checks:**
- CreditReport.score_count is 1 or 0.

**Reads:** CreditReport.score_count

## acra-platinum.unassigned_provisions.reserves_where_no_trigger_applies

**Purpose:** The Platinum Summary does not state a reserve requirement where no listed trigger applies; whether a base requirement exists is an open question.

1. Initial Document Review: Review the CLTV and the information relevant to stated reserve triggers.
2. Eligibility Verification: Determine whether any stated reserve trigger applies and whether the case is at CLTV of 75.00% or below.
3. Validation and Verification: Do not infer a base reserve requirement or import a rule; mark the requirement where no trigger applies as requiring confirmation.
4. Final Determination: Refer the open requirement for confirmation; do not determine compliance from the unanswered question.

**Checks:**
- The case is at CLTV of 75.00% or below and no stated reserve trigger applies.

**Reads:** LoanCore.cltv_percent, RatioSet.reserves_months
**Missing data:** The information needed to establish whether any stated reserve trigger applies.

## acra-platinum.unassigned_provisions.seller_concession_treatment

**Purpose:** The Platinum Summary does not address seller concessions; the applicable limit is an open question.

1. Initial Document Review: Review the transaction information for seller concessions.
2. Eligibility Verification: Identify whether seller concessions are present or proposed.
3. Validation and Verification: Do not import the Standard Summary figure or treat the feature as prohibited; mark the Platinum Select limit as requiring confirmation.
4. Final Determination: Refer the open limit for confirmation; do not determine compliance from the unanswered question.

**Checks:**
- Seller concessions are present or proposed.
**Missing data:** Whether seller concessions are present or proposed, and their amount and the sale price.

## acra-platinum.unassigned_provisions.subordinate_financing_treatment

**Purpose:** The Platinum Summary does not address subordinate liens or restate the Standard Summary’s HELOC CLTV rule; the treatment is an open question.

1. Initial Document Review: Review the transaction and lien information for subordinate financing.
2. Eligibility Verification: Identify whether subordinate financing is present or proposed, including any HELOC.
3. Validation and Verification: Do not import the Standard Summary’s HELOC CLTV rule or infer that subordinate financing is permitted or prohibited; mark the treatment as requiring confirmation.
4. Final Determination: Refer the open treatment for confirmation; do not determine compliance from the unanswered question.

**Checks:**
- Subordinate financing is present or proposed.
**Missing data:** Whether subordinate financing is present or proposed, the lien type, and any applicable credit limit and balance.

## acra-platinum.unassigned_provisions.unaddressed_property_types

**Purpose:** The Platinum Summary does not list 3-4 unit properties, manufactured homes, mixed-use properties, or PUDtels; their Platinum Select treatment is an open question.

1. Initial Document Review: Review the subject-property information for unit count, property type, and mixed-use status.
2. Eligibility Verification: Identify whether the case involves a 3-4 unit property, manufactured home, mixed-use property, or PUDtel.
3. Validation and Verification: Do not import the Standard Summary treatment or treat the feature as prohibited; mark the Platinum Select treatment as requiring confirmation.
4. Final Determination: Refer the open treatment for confirmation; do not determine eligibility from the unanswered question.

**Checks:**
- The case involves a 3-4 unit property, manufactured home, mixed-use property, or PUDtel.

**Reads:** SubjectProperty.number_of_units, SubjectProperty.is_mixed_use, SubjectProperty.property_type
**Missing data:** Whether the property is a manufactured home or PUDtel.
