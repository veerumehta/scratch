# Our jobs, standard (114)

## acra-standard.appraisal_review_property_eligibility.2_4_unit_cltv_cap

**Purpose:** Determine whether a 2-4 Unit property meets the STD-8.1 maximum CLTV.

1. Step 1 - Initial Document Review: Review the appraisal_report for property type and loan records for CLTV.
2. Step 2 - Eligibility Verification: Apply the printed “Max CLTV: 80%” without a purpose split.
3. Step 3 - Validation and Verification: Verify property type and CLTV in the case record.
4. Step 4 - Final Determination: Record whether CLTV is within the printed maximum.

**Checks:**
- For a 2-4 Unit property, CLTV does not exceed 80%.

**Reads:** SubjectProperty.property_type, LoanCore.cltv_percent

## acra-standard.appraisal_review_property_eligibility.above_80_00_ltv_property_type

**Purpose:** Determine whether a property with LTV above 80.00% is one of the types permitted by STD-8.2.

1. Step 1 - Initial Document Review: Review the appraisal_report for property type and appraised value, and review loan records for LTV.
2. Step 2 - Eligibility Verification: Apply the STD-8.2 restriction if LTV is above 80.00%.
3. Step 3 - Validation and Verification: Verify the loan's LTV and property type in the case record.
4. Step 4 - Final Determination: Record whether the property type meets the restriction.

**Checks:**
- If LTV is above 80.00%, the property type is SFR, Warrantable Condo outside of Florida, Townhome, or PUD.

**Reads:** SubjectProperty.property_type, SubjectProperty.state, SubjectProperty.appraised_value_usd
**Missing data:** LTV; whether the property is a Warrantable Condo; whether the property is outside of Florida.

## acra-standard.appraisal_review_property_eligibility.condotel_or_pudtel_caps

**Purpose:** Determine whether a Condotel / PUDtel meets the applicable STD-8.1 limits and printed conditions.

1. Step 1 - Initial Document Review: Review the appraisal_report for property type and location, and review loan records for loan purpose and CLTV.
2. Step 2 - Eligibility Verification: Identify the purchase, Refi R/T, or Refi C/O cap and the Florida condition printed in STD-8.1.
3. Step 3 - Validation and Verification: Verify CLTV, loan purpose, state, and minimum DSCR information.
4. Step 4 - Final Determination: Record whether the applicable cap and conditions are met.

**Checks:**
- For a Condotel / PUDtel, CLTV does not exceed 75% for Purchase, 70% for Refi R/T, or 65% for Refi C/O; for Florida properties, apply “-5% CLTV” and “Min DSCR: 1.0”.

**Reads:** SubjectProperty.property_type, SubjectProperty.state, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Whether loan purpose is Purchase, Refi R/T, or Refi C/O; minimum DSCR; how the Florida “-5% CLTV” applies.

## acra-standard.appraisal_review_property_eligibility.declining_market_reduction

**Purpose:** Determine how the stated declining-market reduction applies to the property and borrower full profile and whether confirmation is needed for its combination with other caps.

1. Step 1 - Initial Document Review: Review the appraisal_report and other applicable property and borrower information for declining-market status.
2. Step 2 - Eligibility Verification: Apply “-5% CLTV property/borrower full profile”.
3. Step 3 - Validation and Verification: Request Acra confirmation on how this reduction combines with other caps, as directed to Q-07.
4. Step 4 - Final Determination: Record the reduction and the confirmation result.

**Checks:**
- For a declining market, “-5% CLTV property/borrower full profile” is applied.
- Acra confirmation is obtained on how the reduction combines with other caps.

**Reads:** SubjectProperty.appraised_value_usd, LoanCore.cltv_percent
**Missing data:** Whether the market is declining; property/borrower full profile; Acra confirmation on combination with other caps (Q-07).

## acra-standard.appraisal_review_property_eligibility.eligible_property_type

**Purpose:** Establish the property's eligibility classification under STD-8.1.

1. Step 1 - Initial Document Review: Review the appraisal_report for the subject property type.
2. Step 2 - Eligibility Verification: Compare the property type with the types listed in STD-8.1.
3. Step 3 - Validation and Verification: Verify the property type in the case record.
4. Step 4 - Final Determination: Record whether the type is listed as eligible.

**Checks:**
- SubjectProperty.property_type is SFR, Townhome, PUD, Warrantable Condo, Non-Warrantable Condo, Condotel / PUDtel, 2-4 Units, or Manufactured.

**Reads:** SubjectProperty.property_type

## acra-standard.appraisal_review_property_eligibility.ineligible_state

**Purpose:** Establish whether the subject property is located in SD, which STD-1.13 identifies as ineligible.

1. Step 1 - Initial Document Review: Review the appraisal_report for the subject property location.
2. Step 2 - Eligibility Verification: Identify the subject property's state.
3. Step 3 - Validation and Verification: Verify the state against the case record.
4. Step 4 - Final Determination: Record whether the subject property is in SD.

**Checks:**
- SubjectProperty.state is SD.

**Reads:** SubjectProperty.state

## acra-standard.appraisal_review_property_eligibility.listed_for_sale_determination

**Purpose:** Establish whether the property is considered listed for sale under STD-8.8.

1. Step 1 - Initial Document Review: Review listing_history for the listing dates.
2. Step 2 - Eligibility Verification: Measure from the last date of being listed to the Application Date.
3. Step 3 - Validation and Verification: Verify the listing lookback against the case record.
4. Step 4 - Final Determination: Record whether the property is considered listed for sale under §11.5.

**Checks:**
- The property has been listed for sale in the last six months, measured from the last date of being listed to the Application Date.

**Reads:** SubjectProperty.listed_for_sale_last_6_months
**Missing data:** Last date of being listed; Application Date.

## acra-standard.appraisal_review_property_eligibility.listed_property_eligibility_conditions

**Purpose:** Determine whether a property considered listed for sale meets the stated lien, occupancy, qualification, prepayment, reserves, amortization, LTV/CLTV, subordinate-financing, and impound requirements.

1. Step 1 - Initial Document Review: Review listing_history, appraisal_report, credit and loan records, and documents establishing lien status, occupancy, prepayment penalty, reserves, subordinate financing, and impounds.
2. Step 2 - Eligibility Verification: Verify each applicable STD-8.9 condition, including the lesser-of value basis for the 65% maximum LTV / CLTV.
3. Step 3 - Validation and Verification: Verify qualification by ≥ 1.0 DSCR or 43% maximum DTI, and verify the property's state for the prepayment-penalty exception.
4. Step 4 - Final Determination: Record whether all applicable listed-property conditions are met.

**Checks:**
- The property is not in default or otherwise delinquent on lien(s).
- For investment properties, the subject is occupied by a tenant and is not vacant.
- The loan qualifies as either ≥ 1.0 DSCR or 43% maximum DTI (Q-14).
- A prepayment penalty of at least three (3) years is required unless the property is in a state that does not allow prepayment penalties.
- Twenty-four (24) months of reserves are required; cash-in-hand may be considered if otherwise consistent with the Guide.
- The loan has a fully amortizing term; interest only is not available.
- Maximum LTV / CLTV is 65% based on the lesser of appraised value or lowest recent listing price.
- No subordinate financing is allowed.
- Impounds are required.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_vacant, SubjectProperty.occupancy_subtype, SubjectProperty.appraised_value_usd, SubjectProperty.state, LoanCore.cltv_percent, MortgageLoanInformation.is_interest_only, LoanCore.prepayment_penalty_structure, RatioSet.reserves_months
**Missing data:** Lien default or delinquency status; whether the property is an investment property and tenant occupied; DSCR or DTI; whether the state allows prepayment penalties; prepayment-penalty term; reserves and whether cash-in-hand is consistent with the Guide; amortization; lowest recent listing price; subordinate financing; impounds.

## acra-standard.appraisal_review_property_eligibility.manufactured_home_caps

**Purpose:** Determine whether a Manufactured Home meets the applicable STD-8.1 CLTV cap.

1. Step 1 - Initial Document Review: Review the appraisal_report for property type and loan records for loan purpose and CLTV.
2. Step 2 - Eligibility Verification: Identify the purchase, Refi R/T, or Refi C/O cap in STD-8.1.
3. Step 3 - Validation and Verification: Verify property type, loan purpose, and CLTV in the case record.
4. Step 4 - Final Determination: Record whether CLTV is within the applicable cap.

**Checks:**
- For a Manufactured Home, CLTV does not exceed 65% for Purchase, 60% for Refi R/T, or 60% for Refi C/O.

**Reads:** SubjectProperty.property_type, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Whether loan purpose is Purchase, Refi R/T, or Refi C/O.

## acra-standard.appraisal_review_property_eligibility.mixed_use_determination

**Purpose:** Establish whether part of the property's space is dedicated to commercial use and the rest to residential use.

1. Step 1 - Initial Document Review: Review the appraisal_report for the property's use and space allocation.
2. Step 2 - Eligibility Verification: Determine whether a portion is dedicated to commercial use and the rest to residential use.
3. Step 3 - Validation and Verification: Verify the mixed-use classification in the case record.
4. Step 4 - Final Determination: Record whether the property meets the stated mixed-use definition.

**Checks:**
- A portion of the property's space is dedicated to commercial use and the rest is dedicated to residential use.

**Reads:** SubjectProperty.is_mixed_use

## acra-standard.appraisal_review_property_eligibility.mixed_use_requirements

**Purpose:** Determine whether a mixed-use property meets the stated minimum DSCR and the conditions referenced in STD-8.10.

1. Step 1 - Initial Document Review: Review the appraisal_report and loan records for DSCR and the applicable §10.7 requirements.
2. Step 2 - Eligibility Verification: Apply the minimum DSCR ratio of 1.2 and the conditions outlined in §10.7, including restrictions regarding Adult Care / Assisted Living Facilities.
3. Step 3 - Validation and Verification: Verify the DSCR and obtain the requirements from §10.7, which is not reproduced in the source excerpt.
4. Step 4 - Final Determination: Record whether the requirements are met or remain subject to the missing §10.7 requirements.

**Checks:**
- The property meets a minimum DSCR ratio of 1.2.
- The property meets the conditions outlined in §10.7, including all restrictions regarding Adult Care / Assisted Living Facilities.

**Reads:** SubjectProperty.is_mixed_use
**Missing data:** DSCR; the conditions and restrictions in §10.7, which is not reproduced.

## acra-standard.appraisal_review_property_eligibility.non_warrantable_condo_caps

**Purpose:** Determine whether a Non-Warrantable Condo meets the applicable STD-8.1 limits and printed conditions.

1. Step 1 - Initial Document Review: Review the appraisal_report for property type and location, and review loan records for loan purpose and CLTV.
2. Step 2 - Eligibility Verification: Identify the purchase, Refi R/T, or Refi C/O cap and the Florida condition printed in STD-8.1.
3. Step 3 - Validation and Verification: Verify CLTV, loan purpose, state, and minimum DSCR information.
4. Step 4 - Final Determination: Record whether the applicable cap and conditions are met.

**Checks:**
- For a Non-Warrantable Condo, CLTV does not exceed 80% for Purchase, 75% for Refi R/T, or 75% for Refi C/O; for Florida properties, apply “-5% CLTV” and “Min DSCR: 1.0”.

**Reads:** SubjectProperty.property_type, SubjectProperty.state, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Whether loan purpose is Purchase, Refi R/T, or Refi C/O; minimum DSCR; how the Florida “-5% CLTV” applies.

## acra-standard.appraisal_review_property_eligibility.rural_or_unique_property_limits

**Purpose:** Determine whether a rural or unique property meets the limits and stated review conditions in STD-8.3.

1. Step 1 - Initial Document Review: Review the appraisal_report for rural or unusual, inadequate, or peculiar functionality; review loan records for loan purpose, CLTV, score, and DSCR.
2. Step 2 - Eligibility Verification: Apply the purchase, refinance rate & term, or refinance cash-out maximum CLTV, minimum FICO 700, and minimum DSCR 1.00.
3. Step 3 - Validation and Verification: Verify the stated limits and determine whether marketing time is excessive or functionality may call for further LTV reduction.
4. Step 4 - Final Determination: Record whether the stated limits are met and whether further review is needed.

**Checks:**
- For a rural / unique property, CLTV does not exceed 80% for purchase, 75% for refinance — rate & term, or 70% for refinance — cash-out.
- Minimum FICO is 700.
- Minimum DSCR is 1.00.
- If marketing time is excessive or property exhibits unusual, inadequate or peculiar functionality, any further LTV reduction is addressed.

**Reads:** SubjectProperty.is_rural, LoanCore.loan_purpose, LoanCore.cltv_percent, CreditReport.representative_score
**Missing data:** Whether the property is unique; whether loan purpose is purchase, refinance — rate & term, or refinance — cash-out; FICO; DSCR; marketing time assessment; assessment of unusual, inadequate or peculiar functionality; any further LTV reduction.

## acra-standard.appraisal_review_property_eligibility.vacant_property_cash_out_refinance

**Purpose:** Determine whether a vacant-property cash-out refinance meets the requirements stated in STD-8.7 and the Summary.

1. Step 1 - Initial Document Review: Review property, credit, loan, ownership, prepayment-penalty, impound, and reserve records.
2. Step 2 - Eligibility Verification: Apply the stated score, DSCR, prepayment penalty, interest-only, impound, reserves, CLTV, and ownership requirements.
3. Step 3 - Validation and Verification: Request Acra confirmation for loans of $1,500,000 or more and for how the 15 months are measured, as directed to Q-10.
4. Step 4 - Final Determination: Record whether the applicable requirements are met and any confirmation remains outstanding.

**Checks:**
- Minimum 700 FICO.
- DSCR ≥ 1.15.
- ≥ 3-year PPP (where allowable).
- No interest only.
- Impounds required.
- 6 months reserves.
- “Max CLTV 60% for loan amounts under $1,500,000”; loans of $1,500,000 or more require Acra confirmation (Q-10).
- Requires ≥15 months ownership; how the 15 months are measured requires Acra confirmation (Q-10).

**Reads:** SubjectProperty.is_vacant, LoanCore.loan_purpose, LoanCore.cltv_percent, LoanCore.total_loan_amount_usd, CreditReport.representative_score, MortgageLoanInformation.is_interest_only, LoanCore.prepayment_penalty_structure, RatioSet.reserves_months, SubjectProperty.ownership_months
**Missing data:** Whether the transaction is cash-out refinance; FICO; DSCR; whether prepayment penalties are allowable; PPP term; impounds; reserves; confirmation for loan amount of $1,500,000 or more; ownership months and confirmation on how the 15 months are measured.

## acra-standard.appraisal_review_property_eligibility.vacant_property_purchase_rents

**Purpose:** Establish that qualifying rents for a vacant property purchase are taken from the 1007 or 1025.

1. Step 1 - Initial Document Review: Review the 1007 or 1025 for qualifying rents.
2. Step 2 - Eligibility Verification: Confirm the transaction is a purchase of a vacant property.
3. Step 3 - Validation and Verification: Verify that qualifying rents are taken from the 1007 or 1025.
4. Step 4 - Final Determination: Record whether the rent source requirement is met.

**Checks:**
- For a vacant property purchase, qualifying rents are taken from the 1007 or 1025.

**Reads:** SubjectProperty.is_vacant, LoanCore.loan_purpose
**Missing data:** 1007 or 1025 qualifying-rent information.

## acra-standard.appraisal_review_property_eligibility.vacant_property_rate_and_term_refinance

**Purpose:** Determine whether a vacant-property rate and term refinance meets STD-8.6.

1. Step 1 - Initial Document Review: Review property, credit, loan, and reserve records; obtain required prepayment-penalty and impound information.
2. Step 2 - Eligibility Verification: Apply the stated FICO, loan-amount/CLTV, DSCR or DTI, prepayment penalty, amortization, impound, and reserves requirements.
3. Step 3 - Validation and Verification: Verify whether the loan amount is exactly $1,000,000 or $2,000,000 and request Acra confirmation as directed to Q-10.
4. Step 4 - Final Determination: Record whether the applicable requirements are met and any confirmation remains outstanding.

**Checks:**
- Minimum 700 FICO score.
- Maximum $1,000,000 to maximum 70% CLTV; maximum $2,000,000 to maximum 65% CLTV; treatment at exactly $1,000,000 and $2,000,000 requires Acra confirmation (Q-10).
- Minimum 1.000 DSCR or maximum 40.0% DTI (Q-14).
- Minimum two-year prepayment penalty (where allowable).
- Full amortization required; no interest-only programs.
- Impounds required.
- Minimum six months reserves.

**Reads:** SubjectProperty.is_vacant, LoanCore.loan_purpose, LoanCore.cltv_percent, LoanCore.total_loan_amount_usd, CreditReport.representative_score, MortgageLoanInformation.is_interest_only, LoanCore.prepayment_penalty_structure, RatioSet.reserves_months
**Missing data:** Whether the transaction is rate and term refinance; FICO; loan-amount boundary treatment confirmation (Q-10); DSCR or DTI; whether prepayment penalties are allowable; prepayment-penalty term; amortization; impounds; reserves.

## acra-standard.asset_assessment_assets_and_funds_to_close.borrower_contribution_with_gift_funds

**Purpose:** Determine whether the applicant contributes a minimum of 10% of the purchase price from their own sourced and seasoned funds when gift funds are used.

1. Step 1 - Initial Document Review: Review bank_statement and the loan_application for gift funds and the applicant's own funds contributed to the transaction.
2. Step 2 - Eligibility Verification: If gift funds are used, identify the applicant's own sourced and seasoned funds and the purchase price.
3. Step 3 - Validation and Verification: Verify the applicant's own sourced and seasoned contribution is at least 10% of the purchase price.
4. Step 4 - Final Determination: Determine whether the required own-funds contribution is established, or whether the job does not apply because gift funds are not used.

**Checks:**
- If gift funds are used, the applicant contributes own sourced and seasoned funds of at least 10% of the purchase price.
**Missing data:** Whether gift funds are used, Amount of applicant's own funds contributed, Source and seasoning of applicant's own funds, Purchase price

## acra-standard.asset_assessment_assets_and_funds_to_close.fico_reserve_trigger

**Purpose:** Determine whether the stated reserve requirement is met when FICO is below 620.

1. Step 1 - Initial Document Review: Review credit_report and bank_statement for FICO and reserves.
2. Step 2 - Eligibility Verification: Determine whether FICO is below 620.
3. Step 3 - Validation and Verification: If FICO is below 620, verify 12 Months reserves.
4. Step 4 - Final Determination: Determine whether the applicable reserve requirement is met, or whether the job does not apply.

**Checks:**
- If FICO is below 620, 12 Months reserves are established.

**Reads:** RatioSet.reserves_months
**Missing data:** FICO

## acra-standard.asset_assessment_assets_and_funds_to_close.first_time_homebuyer_reserves

**Purpose:** Determine whether a first-time homebuyer has the stated minimum six months reserves.

1. Step 1 - Initial Document Review: Review bank_statement for reserve funds.
2. Step 2 - Eligibility Verification: Determine whether the borrower is a first-time homebuyer.
3. Step 3 - Validation and Verification: If the borrower is a first-time homebuyer, verify minimum six months reserves.
4. Step 4 - Final Determination: Determine whether the reserve requirement is met, or whether the job does not apply.

**Checks:**
- Borrower.is_first_time_homebuyer is true only if RatioSet.reserves_months is at least 6.

**Reads:** Borrower.is_first_time_homebuyer, RatioSet.reserves_months

## acra-standard.asset_assessment_assets_and_funds_to_close.forbearance_or_mortgage_late_reserves

**Purpose:** Determine whether the stated 12 months of the subject's payment in reserve is met when the forbearance or mortgage-late trigger applies.

1. Step 1 - Initial Document Review: Review credit_report, lease_agreement, rent_roll, and bank_statement for mortgage history, occupancy, rent receipt, and reserves.
2. Step 2 - Eligibility Verification: Determine whether there was forbearance or mortgage lates in the last 12 months, the subject is tenant-occupied, and the prior two months' rent was not received timely.
3. Step 3 - Validation and Verification: If all stated trigger conditions apply, verify 12 months of the subject's payment in reserve, which may be from the transaction's cash-in-hand.
4. Step 4 - Final Determination: Determine whether the applicable reserve requirement is met, or whether the job does not apply.

**Checks:**
- If there was forbearance or mortgage lates in the last 12 months, the subject is tenant-occupied, and the prior two months' rent was not received timely, 12 months of the subject's payment are in reserve, which may be from the transaction's cash-in-hand.
**Missing data:** Whether there was forbearance or mortgage lates in the last 12 months, Whether the subject is tenant-occupied, Whether the prior two months' rent was received timely, Subject payment amount, Whether transaction cash-in-hand is included in reserves

## acra-standard.asset_assessment_assets_and_funds_to_close.foreign_funds_repatriation

**Purpose:** Determine whether funds held in a foreign bank or currency are repatriated at minimum three (3) business days prior to Closing.

1. Step 1 - Initial Document Review: Review bank_statement and closing records for funds held in a foreign bank or currency and their transfer to the closing account.
2. Step 2 - Eligibility Verification: Determine whether funds to close are held in a foreign bank or currency.
3. Step 3 - Validation and Verification: If funds are held in a foreign bank or currency, verify they are repatriated at minimum three (3) business days prior to Closing.
4. Step 4 - Final Determination: Determine whether the repatriation timing requirement is met, or whether the job does not apply.

**Checks:**
- If funds to close are held in a foreign bank or currency, they are repatriated at minimum three (3) business days prior to Closing.
**Missing data:** Whether funds to close are held in a foreign bank or currency, Date funds are repatriated, Closing date

## acra-standard.asset_assessment_assets_and_funds_to_close.foreign_national_funds_seasoning

**Purpose:** Determine whether a Foreign National has documented a minimum of 60 days seasoning of funds held in a foreign bank or currency.

1. Step 1 - Initial Document Review: Review bank_statement for funds to close and their seasoning.
2. Step 2 - Eligibility Verification: Determine whether the applicant is a Foreign National and whether funds to close are held in a foreign bank or currency.
3. Step 3 - Validation and Verification: For Foreign Nationals, verify a minimum of 60 days seasoning regardless of LTV / CLTV.
4. Step 4 - Final Determination: Determine whether the stated seasoning is documented, or whether the job does not apply.

**Checks:**
- For a Foreign National, funds held in a foreign bank or currency are documented with a minimum of 60 days seasoning, regardless of LTV / CLTV.
**Missing data:** Whether the applicant is a Foreign National, Whether funds to close are held in a foreign bank or currency, Dates establishing funds seasoning

## acra-standard.asset_assessment_assets_and_funds_to_close.funds_to_close_documentation_minimum

**Purpose:** Determine whether the required minimum 30-days documentation for funds to close is provided.

1. Step 1 - Initial Document Review: Review bank_statement or other account documentation for the source of funds to close.
2. Step 2 - Eligibility Verification: Identify the account or accounts serving as the source of funds to close.
3. Step 3 - Validation and Verification: Verify that documentation covers a minimum of 30 days.
4. Step 4 - Final Determination: Determine whether the minimum documentation requirement is met.

**Checks:**
- Documentation for funds to close covers a minimum of 30 days.
**Missing data:** Dates covered by funds-to-close documentation

## acra-standard.asset_assessment_assets_and_funds_to_close.funds_to_close_seasoning_trigger

**Purpose:** Determine whether the loan meets a stated seasoning trigger and, if it does, verify seasoning of funds to close.

1. Step 1 - Initial Document Review: Review bank_statement and transaction records for funds to close and their seasoning.
2. Step 2 - Eligibility Verification: Determine whether this is a consumer transaction with CLTV over 70%, or a business purpose loan with funds to close over $50,000 and CLTV over 70%.
3. Step 3 - Validation and Verification: If either stated trigger applies, verify seasoning of funds to close.
4. Step 4 - Final Determination: Determine whether the applicable trigger and its seasoning verification requirement are met.

**Checks:**
- The loan is a consumer transaction with CLTV over 70%, or is a business purpose loan with funds to close over $50,000 and CLTV over 70%.
- If a stated trigger applies, seasoning of funds to close is verified.

**Reads:** LoanCore.cltv_percent
**Missing data:** Whether the transaction is a consumer transaction or business purpose loan, Funds-to-close amount, Evidence of funds-to-close seasoning

## acra-standard.asset_assessment_assets_and_funds_to_close.listed_property_reserves

**Purpose:** Determine whether the stated Twenty-four (24) months of reserves requirement is met when the property was listed for sale within six months.

1. Step 1 - Initial Document Review: Review listing_history and bank_statement for listing history and reserve funds; identify any cash-in-hand offered as reserves.
2. Step 2 - Eligibility Verification: Determine whether the property was listed for sale within six months.
3. Step 3 - Validation and Verification: If the property was listed for sale within six months, verify Twenty-four (24) months of reserves; cash-in-hand may be considered if otherwise consistent with the Guide.
4. Step 4 - Final Determination: Determine whether the stated reserve requirement is met, or whether the job does not apply.

**Checks:**
- If the property was listed for sale within six months, Twenty-four (24) months of reserves are established, including cash-in-hand only if it is otherwise consistent with the Guide.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
**Missing data:** Whether any cash-in-hand is otherwise consistent with the Guide

## acra-standard.asset_assessment_assets_and_funds_to_close.loan_amount_limits

**Purpose:** Determine whether the loan amount meets the stated loan amount limits.

1. Step 1 - Initial Document Review: Review the loan_application for the loan amount.
2. Step 2 - Eligibility Verification: Confirm the loan amount is at least $100,000 and no more than $3,000,000.
3. Step 3 - Validation and Verification: Confirm the loan amount is in $50 increments.
4. Step 4 - Final Determination: Determine whether all loan amount requirements are met.

**Checks:**
- LoanCore.total_loan_amount_usd is at least $100,000.
- LoanCore.total_loan_amount_usd is no more than $3,000,000.
- LoanCore.total_loan_amount_usd is in $50 increments.

**Reads:** LoanCore.total_loan_amount_usd

## acra-standard.asset_assessment_assets_and_funds_to_close.ltv_reserve_trigger

**Purpose:** Determine whether the stated reserve requirement is met when LTV is over 80.00%.

1. Step 1 - Initial Document Review: Review bank_statement for reserves and loan records for LTV and the payment amount.
2. Step 2 - Eligibility Verification: Determine whether LTV is over 80.00%.
3. Step 3 - Validation and Verification: If LTV is over 80.00%, verify 6 months PITIA reserves.
4. Step 4 - Final Determination: Determine whether the applicable reserve requirement is met, or whether the job does not apply.

**Checks:**
- If LTV is over 80.00%, 6 months PITIA reserves are established.
**Missing data:** LTV, PITIA amount and evidence that reserves are measured against PITIA

## acra-standard.asset_assessment_assets_and_funds_to_close.seller_concession_limit

**Purpose:** Determine whether seller concessions and other contributions are limited to 3% of the sale price.

1. Step 1 - Initial Document Review: Review the loan_application for the seller concession or other contribution.
2. Step 2 - Eligibility Verification: Identify the sale price and the seller concession or other contribution amount.
3. Step 3 - Validation and Verification: Compare the contribution with the 3% limit.
4. Step 4 - Final Determination: Determine whether the contribution is within the stated limit.

**Checks:**
- Seller concessions and other contributions do not exceed 3% of the sale price.
**Missing data:** Sale price, Seller concession or other contribution amount

## acra-standard.asset_assessment_assets_and_funds_to_close.unavailable_rent_loss_insurance_reserves

**Purpose:** Determine whether the required reserves for rent loss insurance coverage not provided are established.

1. Step 1 - Initial Document Review: Review hazard_insurance and bank_statement for required rent loss insurance, coverage obtained, and reserves.
2. Step 2 - Eligibility Verification: Determine whether rent loss insurance is required and cannot be obtained, and identify the month(s) of coverage not provided.
3. Step 3 - Validation and Verification: If rent loss insurance is required but cannot be obtained, verify Two (2) months reserves for every one (1) month of coverage not provided.
4. Step 4 - Final Determination: Determine whether the applicable reserve requirement is met, or whether the job does not apply.

**Checks:**
- If rent loss insurance is required but cannot be obtained, reserves equal Two (2) months for every one (1) month of coverage not provided.
**Missing data:** Whether rent loss insurance is required, Whether required rent loss insurance cannot be obtained, Number of months of coverage not provided

## acra-standard.asset_assessment_assets_and_funds_to_close.vacant_property_refinance_reserves

**Purpose:** Determine whether the stated reserve requirement is met for a vacant property rate & term refinance or cash-out refinance.

1. Step 1 - Initial Document Review: Review bank_statement for reserve funds and the loan_application for refinance purpose.
2. Step 2 - Eligibility Verification: Determine whether the property is vacant and whether the refinance is rate & term or cash-out.
3. Step 3 - Validation and Verification: For a vacant property rate & term refinance, verify minimum six months reserves; for a vacant property cash-out refinance, verify 6 months reserves.
4. Step 4 - Final Determination: Determine whether the applicable reserve requirement is met, or whether the job does not apply.

**Checks:**
- A vacant property rate & term refinance has minimum six months reserves.
- A vacant property cash-out refinance has 6 months reserves.

**Reads:** SubjectProperty.is_vacant, RatioSet.reserves_months, LoanCore.loan_purpose
**Missing data:** Whether the refinance is rate & term or cash-out

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.borrower_and_guarantor_due_diligence_currency

**Purpose:** Determine whether required borrower and guarantor due diligence is current at the specified time.

1. Step 1 - Initial Document Review: Review the lender-held due diligence record and identify the applicable loan approval or draw date.
2. Step 2 - Eligibility Verification: Identify the due diligence required by the applicable schedule.
3. Step 3 - Validation and Verification: Compare the due diligence record dates with the applicable schedule and the date of any loan approval or draw.
4. Step 4 - Final Determination: Record whether borrower and guarantor due diligence is current as of the relevant date.

**Checks:**
- Borrower and guarantor due diligence is current as of the date of any loan approval or draw as outlined in the applicable schedule.
**Missing data:** applicable due diligence schedule, due diligence completion dates and results, loan approval date or draw date

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.direct_title_owners_as_borrowers

**Purpose:** Determine whether all direct-owner entities required by the rule are borrowing entities.

1. Step 1 - Initial Document Review: Review the title commitment and entity_documents to identify every direct owner of the subject property shown on title and each owner’s type.
2. Step 2 - Eligibility Verification: Identify each direct owner that is an entity and verify whether it is a borrowing entity.
3. Step 3 - Validation and Verification: Reconcile the direct owners shown in the title commitment with the entity ownership information in the entity documents.
4. Step 4 - Final Determination: Record whether every entity holding direct ownership on title is a borrowing entity.

**Checks:**
- Every entity with direct ownership of the subject property that is on title as a direct owner is a borrowing entity.
**Missing data:** identity and type of each direct owner on title, whether each direct-owner entity is a borrowing entity

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.entity_documentation

**Purpose:** Determine whether the entity has provided the required documentation without relying on borrower letters excusing missing documents.

1. Step 1 - Initial Document Review: Obtain and review the entity_documents, including formation documents and amendments, the applicable Operating Agreement or Bylaws and amendments, ownership evidence, and all other documents required by STD-6.10.
2. Step 2 - Eligibility Verification: Verify that the entity has provided the complete, legible documents applicable to its legal form, including the required ownership evidence and any applicable corporation or tax-year ownership evidence.
3. Step 3 - Validation and Verification: Verify name matching or a letter of explanation; the good-standing validity period; any required foreign qualification; the entity’s SS4, TIN, or EIN issuance letter or a submitted exception request; unanimous written consent or board resolution; and any required power of attorney. Do not accept a borrower letter stating required documents are not required, available, or excused.
4. Step 4 - Final Determination: Record whether all applicable required documents and contents are present; refer any additional supporting-documentation condition to Legal as stated.

**Checks:**
- A complete, legible Certificate of Formation or Articles of Organization and all amendments is provided.
- For an LLC or Partnership, a complete, legible Operating Agreement with all referenced exhibits and amendments is provided; for a corporation, complete, legible Bylaws with all referenced exhibits and amendments are provided.
- The Operating Agreement or Bylaws states whether the entity is member or manager managed, contains authorization to borrow money and enter into contracts for mortgage assets, and designates signers.
- All documentation evidencing ownership interests is provided; for LLCs and Partnerships, the Operating Agreement identifies or attaches all persons by name with their ownership interest, or membership interest certificates or units compliant with the Operating Agreement are provided.
- For an S or C Corporation, compliant shareholder or stockholder certificates are provided, if any, or the stock ledger is provided if certificates are lost or unavailable; the certificate or ledger accounts for all outstanding shares noted in the formation documents, including those held by the corporation; and an Affidavit of Lost Stock Certificate is provided if stock certificates are lost, destroyed, mutilated, or otherwise unavailable.
- For an S-corporation or Partnership where both stock certificate and stock ledger are unavailable, the most recent preceding tax year's K-1 statement for all members with 20% or more interest and a letter from the CPA or Tax Preparer affirming current ownership interest are provided; if the preceding year's taxes have not been filed, the letter includes a statement to that effect.
- Names on the entity documents match the identification, or a letter of explanation addresses any discrepancy.
- A Certificate of Good Standing or equivalent document valid within ninety (90) days of the closing date is provided.
- If the entity is formed in a state other than where business is conducted or where the property is located, a Certificate of Foreign Qualification or other qualification to operate in the applicable state is provided.
- The entity’s IRS Form SS4, Federal Taxpayer Identification Number (TIN), or Employer Identification Number (EIN) issuance letter is provided, or an EIN exception request is submitted for review by Acra's Legal Department with a letter of explanation stating the applicable grounds.
- A Unanimous Written Consent or Board Resolution signed by all members regardless of their percentage of interest authorizes the transaction with Acra Lending and identifies who is authorized to sign the loan documents on behalf of and to bind the entity.
- A Power of Attorney is utilized by the principal to designate an attorney in fact to execute a personal guarantee when required for that purpose.
- A borrower letter is not used to state that required entity documents are not required, available, or excused.

**Reads:** Borrower.entity_documents_complete
**Missing data:** entity legal form, formation documents and all amendments, Operating Agreement or Bylaws, referenced exhibits, and amendments, entity management structure, borrowing and contracting authority, and designated signers, ownership interests and supporting ownership records, applicable corporation stock records and any Affidavit of Lost Stock Certificate, availability of stock certificates and stock ledger; preceding tax-year filing status; K-1 statements; CPA or Tax Preparer letter, identification names and entity document names, closing date and Certificate of Good Standing or equivalent validity date, formation state, business state, and property state, entity tax identification documentation or EIN exception request and grounds, all-member consent or board resolution and authorized signers, principal, attorney in fact, and applicable Power of Attorney, any additional supporting documentation required by Legal

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.entity_form_and_status_eligibility

**Purpose:** Determine whether the entity meets Acra’s stated entity-type and US-status requirements.

1. Step 1 - Initial Document Review: Review entity_documents for the entity’s legal form, formation, and business location; review the loan application for the entity’s ownership.
2. Step 2 - Eligibility Verification: Compare the entity’s legal form with the allowed types and exclusions in STD-6.7 and STD-6.8. Verify that the entity is US formed and based and is not foreign owned.
3. Step 3 - Validation and Verification: Resolve any discrepancy between the entity documents and the application using the entity documents; do not treat an excluded entity type as eligible.
4. Step 4 - Final Determination: Record whether the entity meets the entity-type and US-status requirements.

**Checks:**
- The entity is a Domestic Corporation (C or S Corp), a single purpose Limited Liability Company (LLC) other than a series LLC, an LLP, an LLLP, a GP, an LP, or a Sole Proprietorship.
- The entity is not a Cooperative, Irrevocable Trust, Land Trust, IRA, Non-Profit, or Joint Venture.
- The entity is US formed and based and is not foreign owned.
**Missing data:** entity legal form, entity formation location, entity business location, entity ownership and foreign-ownership status

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.entity_ownership_structure

**Purpose:** Determine whether the entity ownership structure meets Acra’s stated nesting limits.

1. Step 1 - Initial Document Review: Review entity_documents identifying the entity’s direct and indirect owners and any subsidiary relationships.
2. Step 2 - Eligibility Verification: Trace the ownership structure and identify the number of subsidiary levels and the owners of any subsidiary.
3. Step 3 - Validation and Verification: Verify from the entity documents whether any subsidiary is wholly owned and whether it is owned by individuals; identify any ownership by multiple entities or trusts.
4. Step 4 - Final Determination: Record whether the structure is within the stated nesting limit.

**Checks:**
- Business entity nesting is limited to only one wholly-owned subsidiary, which in turn is owned by individual(s), with no multiple nesting or ownership by multiple entities, trusts, etcetera.
**Missing data:** entity ownership structure, including direct and indirect owners, subsidiary ownership percentages and owners

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.guarantor_homeownership_experience

**Purpose:** Determine whether the required prior-homeownership experience is attested and supported as required.

1. Step 1 - Initial Document Review: Review the loan application for the borrower or guarantor attestation and review the loan file for evidence of prior homeownership.
2. Step 2 - Eligibility Verification: Verify that at least one borrower or guarantor attests on the application that they are not a first-time homebuyer.
3. Step 3 - Validation and Verification: If prior homeownership is not evident within the loan file, condition for supporting documentation and verify that it is provided.
4. Step 4 - Final Determination: Record whether the attestation is present and whether required supporting documentation has been provided.

**Checks:**
- At least one borrower or guarantor on the loan attests on the application that they are not a first-time homebuyer.
- If prior homeownership is not evident within the loan file, supporting documentation required by the underwriter is provided.

**Reads:** Borrower.is_first_time_homebuyer
**Missing data:** identity of borrower or guarantor making the attestation, application attestation, evidence of prior homeownership in the loan file, supporting documentation if conditioned

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.key_principal_and_entity_background_review

**Purpose:** Determine whether the required background review covers the parties identified in the guideline.

1. Step 1 - Initial Document Review: Review the lender-held background review record and the entity ownership and control information.
2. Step 2 - Eligibility Verification: For an entity borrower, identify the entity, recourse guarantors, and any individual or entity owning 20% or more directly or indirectly or having managing control; for an individual borrower, identify all such individuals.
3. Step 3 - Validation and Verification: Verify that the background review covers the applicable parties and review its stated scope, which may include criminal history, OFAC searches, litigation, judgment, and lien searches.
4. Step 4 - Final Determination: Record whether the background review covers the applicable Key Principals and Entities.

**Checks:**
- The background review covers the entity, recourse guarantors, and any party (individual or entity) that owns 20% or more of the entity directly or indirectly or has managing control for an entity borrower; for an individual borrower, it covers all such individuals.

**Reads:** Borrower.entity_type
**Missing data:** recourse guarantors, direct and indirect owners and ownership percentages, parties with managing control, background review results and parties covered

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.ownership_change_lookback

**Purpose:** Determine whether a stated ownership change is subject to Acra’s non-recognition rule.

1. Step 1 - Initial Document Review: Review entity_documents for operating agreement or bylaw changes to ownership percentages and review the application record for the Application Date and application-process period.
2. Step 2 - Eligibility Verification: Identify whether an ownership-percentage change was made with the intent of changing ownership percentages to circumvent required personal guarantors.
3. Step 3 - Validation and Verification: For such a change, compare its effective date with the 30 days prior to an Application Date and determine whether it occurred throughout the application process.
4. Step 4 - Final Determination: Do not recognize a change meeting the stated intent and timing rule; record the result.

**Checks:**
- A change to the operating agreement or bylaws intended to change ownership percentages to circumvent required personal guarantors is not recognized by Acra if it occurred within 30 days prior to an Application Date or throughout the application process.
**Missing data:** ownership-percentage change and its intent, date of ownership change, Application Date, application-process period

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.recourse_guarantees_for_entity_owners

**Purpose:** Determine whether the entity borrower’s required owner guarantees are provided under the stated terms.

1. Step 1 - Initial Document Review: Review entity_documents for all direct and indirect individual owners, their ownership interests, and the recourse guarantees provided.
2. Step 2 - Eligibility Verification: Identify every individual with direct or indirect ownership ≥ 20% and verify that each is required to provide a recourse guarantee.
3. Step 3 - Validation and Verification: Verify that each required guarantee is Acra approved or on Exhibit 7; where there are multiple guarantors, verify that recourse is joint and several.
4. Step 4 - Final Determination: Record whether all required guarantees and the applicable recourse terms are present.

**Checks:**
- Every individual with direct or indirect ownership ≥ 20% provides a recourse guarantee that is Acra approved or on Exhibit 7.
- If there are multiple guarantors, all recourse is joint and several.
**Missing data:** identity and direct and indirect ownership percentage of each individual owner, recourse guarantees and whether they are Acra approved or on Exhibit 7, number of guarantors and recourse terms

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.revocable_living_trust_vesting

**Purpose:** Determine whether title vesting in the trust meets the stated conditions.

1. Step 1 - Initial Document Review: Review the title commitment and the complete trust or Certification of Trust, together with any supporting documentation and written exception.
2. Step 2 - Eligibility Verification: Verify the trust document contents, trust validity and revocability, trustors, beneficiaries, trustee powers, and any required written exception.
3. Step 3 - Validation and Verification: Verify the required provisions concerning title, mortgage authority, beneficiary consent, lender rights, and whether the trust has been revoked, modified, or amended; identify any additional documentation Legal requires.
4. Step 4 - Final Determination: Record whether every applicable trust condition is met and whether any required written exception or conditioned supporting documentation remains outstanding.

**Checks:**
- A complete, legible copy of the Trust or a Certification of Trust is provided, stating the Trust’s existence and date; Trustor(s) and current Trustee(s); Trustee powers; whether the Trust is revocable and, if so, who holds the right to revoke; names and number of Trustees required to sign; Trust identification number (a Social Security number or an IRS-issued Tax Identification Number); how title to Trust assets should be taken; and that the Trust has not been revoked, modified, or amended in any manner.
- The Trust is valid under the laws of the state in which it is established.
- The Trust is revocable, meaning it can be changed or canceled at any time for any reason during a Trustor's lifetime; it is not irrevocable.
- The Trust is established by one or more natural persons, solely or jointly (Grantor, Trustor, or Settlor), and becomes effective during the lifetime of the person(s) establishing it.
- The primary beneficiary of the Trust is the individual(s) establishing the Trust.
- If the Trustor(s) and Trustee(s) are not the same, written exception by Acra Senior Management is obtained.
- The Trust specifies that the Trustee has the power to hold title and mortgage the property; that the beneficiary does not need to grant written consent for the Trust to borrow money, or that such consent has been granted in writing for purposes of the mortgage; that there is no unusual risk or impairment to the lender's rights; and that holding title in the Trust does not diminish the lender's rights as a creditor.
- Any additional supporting documentation for which Legal conditions is provided.
**Missing data:** trust document or Certification of Trust and all required contents, state where the Trust is established and evidence of validity under that state’s laws, revocability and right to revoke, Trustor(s), Trustee(s), and beneficiary identities, Trustee powers and required signing number, Trust identification number and title-taking instructions, Trust effective date and Trustor lifetime status, written Acra Senior Management exception if Trustor(s) and Trustee(s) differ, required trust provisions on title, mortgage authority, beneficiary consent, unusual risk, and lender creditor rights, any additional supporting documentation required by Legal

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.single_purpose_entity_eligibility

**Purpose:** Determine whether an entity borrower meets the stated SPE requirements.

1. Step 1 - Initial Document Review: Review entity_documents for the entity’s assets and business activities and identify whether it is a series limited liability company.
2. Step 2 - Eligibility Verification: Verify that the entity has no assets other than residential investment or rental properties and is engaged in owning and operating residential investment or rental properties.
3. Step 3 - Validation and Verification: Compare the asset and business-activity information in the entity documents and resolve any discrepancies relevant to the SPE requirement.
4. Step 4 - Final Determination: Record whether the entity meets the SPE requirement and is not a series limited liability company.

**Checks:**
- The entity has no assets other than residential investment or rental properties and is engaged in the business of owning and operating residential investment or rental properties.
- The entity is not a series limited liability company.
**Missing data:** entity assets, entity business activities, whether the LLC is a series LLC

## acra-standard.compliance_and_closing_the_borrowing_entity_and_title.title_holder_acceptability

**Purpose:** Determine whether the proposed title holder is permitted under the stated title-holding rule.

1. Step 1 - Initial Document Review: Review the title commitment to identify the proposed title holder and review entity_documents if the title holder is an entity.
2. Step 2 - Eligibility Verification: Determine whether the title holder is an individual person or an entity requiring Acra’s acceptance.
3. Step 3 - Validation and Verification: For an entity title holder, obtain and review Acra’s decision on acceptability; do not substitute a reviewer’s acceptance for Acra’s sole discretion.
4. Step 4 - Final Determination: Record whether the title holder is an individual or an entity accepted by Acra.

**Checks:**
- The collateral title is held either directly by an individual person or persons, or by an entity acceptable to Acra in its sole discretion.
**Missing data:** identity and legal form of the proposed title holder, Acra’s acceptability decision if the title holder is an entity

## acra-standard.credit_review_analysis_credit.bankruptcy_and_foreclosure_cltv_limits

**Purpose:** Determine whether CLTV meets the printed bankruptcy and foreclosure restriction for the applicable seasoning and purpose.

1. Initial Document Review: Review the credit report and file for bankruptcy or foreclosure history and its seasoning.
2. Eligibility Verification: Establish whether the borrower has had bankruptcy or foreclosure and identify the applicable loan purpose.
3. Validation and Verification: Apply the printed limits: ≥ 36 Mo—No Restrictions for both purposes; 24-35 Mo—80% Purchase, 75% Refi R/T, Refi C/O; 12-23 Mo—65% for both; < 12 Mo—Ineligible for both.
4. Final Determination: Determine whether the applicable printed restriction is met.

**Checks:**
- For the applicable printed seasoning and loan-purpose column, CLTV does not exceed the listed maximum; < 12 Mo is Ineligible.

**Reads:** Borrower.has_bankruptcy_or_foreclosure, Borrower.months_since_bankruptcy_or_foreclosure, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** the applicable seasoning as printed, whether the reported event is bankruptcy or foreclosure

## acra-standard.credit_review_analysis_credit.correct_itin_or_ssn_reporting

**Purpose:** Confirm the credit-reporting identity requirement for scores and tradelines.

1. Initial Document Review: Review the credit report and loan application for reported scores, tradelines, and the borrower's ITIN or SSN.
2. Eligibility Verification: Identify the ITIN or SSN that applies to the borrower.
3. Validation and Verification: Compare the identity under which scores and tradelines are reported with the borrower's correct ITIN or SSN.
4. Final Determination: Confirm that scores and tradelines are reported under the correct ITIN or SSN.

**Checks:**
- Scores and tradelines are reported under the correct ITIN or SSN.
**Missing data:** the borrower's correct ITIN or SSN, the ITIN or SSN under which scores and tradelines are reported

## acra-standard.credit_review_analysis_credit.dscr_housing_history_documentation_scope

**Purpose:** Confirm the housing-history documentation scope stated for DSCR loans.

1. Initial Document Review: Review the file for housing-history documentation and any documents suggesting a major credit event.
2. Eligibility Verification: Establish whether the loan is a DSCR loan and identify the borrower's and/or guarantors' subject property, principal residence, second home (if any), and additional properties.
3. Validation and Verification: Verify payment history documentation for the primary residence, subject property, and second homes, if applicable. Do not require documentation for additional properties unless documents in the file suggest a major credit event has occurred.
4. Final Determination: Confirm that the DSCR housing-history documentation scope is met.

**Checks:**
- For a DSCR loan, payment history is documented for the primary residence, subject property, and second homes, if applicable; additional properties are documented only if documents in the file suggest a major credit event has occurred.
**Missing data:** whether the loan is a DSCR loan, the primary residence, subject property, and any second homes of the borrower and/or guarantors, whether documents in the file suggest a major credit event has occurred, whether payment history documentation is present for each required property

## acra-standard.credit_review_analysis_credit.escrow_waiver_cltv_maximum

**Purpose:** Verify that an escrow-waiver loan does not exceed the stated maximum CLTV.

1. Initial Document Review: Review the loan file for escrow-waiver status and CLTV.
2. Eligibility Verification: Establish whether an escrow waiver is requested.
3. Validation and Verification: Compare CLTV with the maximum CLTV 80%.
4. Final Determination: Confirm whether the maximum CLTV is met.

**Checks:**
- If an escrow waiver is requested, CLTV is no more than 80%.

**Reads:** LoanCore.is_escrow_waived, LoanCore.cltv_percent

## acra-standard.credit_review_analysis_credit.escrow_waiver_maximum_loan_amount

**Purpose:** Verify that an escrow-waiver loan does not exceed the stated maximum loan amount.

1. Initial Document Review: Review the loan file for escrow-waiver status and total loan amount.
2. Eligibility Verification: Establish whether an escrow waiver is requested.
3. Validation and Verification: Compare the total loan amount with the maximum loan amount $1.5M.
4. Final Determination: Confirm whether the maximum loan amount is met.

**Checks:**
- If an escrow waiver is requested, total loan amount is no more than $1.5M.

**Reads:** LoanCore.is_escrow_waived, LoanCore.total_loan_amount_usd

## acra-standard.credit_review_analysis_credit.escrow_waiver_minimum_fico

**Purpose:** Verify that an escrow-waiver loan meets the stated minimum FICO.

1. Initial Document Review: Review the credit report for the applicable FICO and the loan file for escrow-waiver status.
2. Eligibility Verification: Establish whether an escrow waiver is requested.
3. Validation and Verification: Verify that FICO is at least 700.
4. Final Determination: Confirm whether the minimum FICO is met.

**Checks:**
- If an escrow waiver is requested, FICO is at least 700.

**Reads:** LoanCore.is_escrow_waived, CreditReport.representative_score
**Missing data:** which FICO is used for the escrow waiver requirement

## acra-standard.credit_review_analysis_credit.escrow_waiver_mortgage_history

**Purpose:** Confirm the stated mortgage-history requirement for an escrow waiver.

1. Initial Document Review: Review the credit report for mortgage history and the loan file for escrow-waiver status.
2. Eligibility Verification: Establish whether an escrow waiver is requested.
3. Validation and Verification: Verify that mortgage history is no worse than 0x30x24.
4. Final Determination: Confirm whether the mortgage-history requirement is met.

**Checks:**
- If an escrow waiver is requested, mortgage history is no worse than 0x30x24.

**Reads:** LoanCore.is_escrow_waived, CreditReport.mortgage_0x30x24
**Missing data:** whether mortgage history is no worse than 0x30x24

## acra-standard.credit_review_analysis_credit.foreign_national_escrow_waiver_exclusion

**Purpose:** Apply the stated Foreign National exclusion from escrow-waiver eligibility.

1. Initial Document Review: Review the loan file for escrow-waiver status and citizenship status.
2. Eligibility Verification: Establish whether the borrower is a Foreign National.
3. Validation and Verification: Verify that a Foreign National is not eligible for the escrow waiver.
4. Final Determination: Confirm whether the Foreign National exclusion is met.

**Checks:**
- A Foreign National is not eligible for the escrow waiver.

**Reads:** Borrower.citizenship_status, LoanCore.is_escrow_waived
**Missing data:** whether Borrower.citizenship_status identifies the borrower as a Foreign National

## acra-standard.credit_review_analysis_credit.low_or_no_score_cltv_limit

**Purpose:** Verify the stated Max 65% LTV/CLTV overlay where the 1 or No Score / Deficient Tradelines rule applies.

1. Initial Document Review: Review the credit report for score and tradeline information.
2. Eligibility Verification: Establish whether the file is within 1 or No Score / Deficient Tradelines.
3. Validation and Verification: Compare the loan's CLTV with the printed Max 65% LTV/CLTV.
4. Final Determination: Confirm whether the applicable CLTV limit is met.

**Checks:**
- If 1 or No Score / Deficient Tradelines applies, CLTV does not exceed 65%.

**Reads:** LoanCore.cltv_percent, CreditReport.score_count
**Missing data:** whether the file has deficient tradelines

## acra-standard.credit_review_analysis_credit.low_or_no_score_dscr_minimum

**Purpose:** Verify the stated DSCR Ratio ≥ 1.1 overlay where the 1 or No Score / Deficient Tradelines rule applies.

1. Initial Document Review: Review the credit report for score and tradeline information and the file for the DSCR Ratio.
2. Eligibility Verification: Establish whether the file is within 1 or No Score / Deficient Tradelines.
3. Validation and Verification: Verify that the DSCR Ratio is ≥ 1.1.
4. Final Determination: Confirm whether the applicable DSCR Ratio requirement is met.

**Checks:**
- If 1 or No Score / Deficient Tradelines applies, DSCR Ratio is ≥ 1.1.

**Reads:** CreditReport.score_count
**Missing data:** whether the file has deficient tradelines, the DSCR Ratio

## acra-standard.credit_review_analysis_credit.low_or_no_score_housing_history

**Purpose:** Verify the stated housing-history overlay where the 1 or No Score / Deficient Tradelines rule applies.

1. Initial Document Review: Review the credit report for score, tradeline, and housing-history information.
2. Eligibility Verification: Establish whether the file is within 1 or No Score / Deficient Tradelines.
3. Validation and Verification: Verify the printed requirement of 24mos 0x30 housing history.
4. Final Determination: Confirm whether the applicable housing-history requirement is met.

**Checks:**
- If 1 or No Score / Deficient Tradelines applies, the file meets 24mos 0x30 housing history.

**Reads:** CreditReport.score_count, CreditReport.mortgage_0x30x24
**Missing data:** whether the file has deficient tradelines, whether the file meets 24mos 0x30 housing history

## acra-standard.credit_review_analysis_credit.matured_loan_rating_date

**Purpose:** Confirm the stated mortgage-rating basis for loans that have matured.

1. Initial Document Review: Review loan records and any written maturity extensions.
2. Eligibility Verification: Establish whether the loan has matured.
3. Validation and Verification: For a loan that has matured, verify that it is rated based on the maturity date and that any extension of the maturity date is in writing.
4. Final Determination: Confirm that the stated maturity-date basis and written-extension requirement are met.

**Checks:**
- A loan that has matured is rated based on its maturity date, and any extension of the maturity date is in writing.
**Missing data:** whether the loan has matured, the loan's maturity date, whether an extension exists, whether any extension is in writing, the rating based on the maturity date

## acra-standard.credit_review_analysis_credit.mortgage_and_rental_rating_review

**Purpose:** Verify the required evaluation of mortgage and rental ratings for mortgage pricing.

1. Initial Document Review: Review credit reports and file documentation for properties the borrower owns and/or rents over the last twelve (12) months.
2. Eligibility Verification: Identify all reported mortgages and identify mortgages that are not reported.
3. Validation and Verification: Consider all reported mortgages. Where the applicant has mortgages that are not reported, verify that the file contains documentation to evaluate history on the applicant's primary residence(s), any secondary residence(s), and the subject property. Evaluate the ratings for properties the borrower owns and/or rents over the last twelve (12) months.
4. Final Determination: Confirm that the rating used for determining mortgage pricing reflects the required evaluation.

**Checks:**
- The mortgage / rental rating for determining mortgage pricing is determined by evaluating ratings for properties the borrower owns and/or rents over the last twelve (12) months, considering all reported mortgages and, where mortgages are not reported, the specified property-history documentation.
**Missing data:** which properties the borrower owns and/or rents over the last twelve (12) months, all reported mortgages, whether the applicant has mortgages that are not reported, whether documentation evaluates history on the applicant's primary residence(s), any secondary residence(s), and the subject property, the rating used for determining mortgage pricing

## acra-standard.credit_review_analysis_credit.mortgage_history_cltv_limits

**Purpose:** Determine whether CLTV meets the mortgage history restriction printed for the applicable label and purpose.

1. Initial Document Review: Review the credit report for the mortgage-history label.
2. Eligibility Verification: Identify the applicable loan purpose and printed mortgage-history label. The labels are Acra's; their definitions and how seasoning is measured are identified as Acra confirmation requested → Q-05.
3. Validation and Verification: Apply the printed limits: 1x30x12—80% Purchase, 75% Refi R/T, Refi C/O; 0x60x12—75% Purchase, 70% Refi R/T, Refi C/O; 0x90x12—65% for both; 0x120x12—Ineligible for both. Where the Summary prints a single figure without a purpose split (“Max CLTV: 65%”), it is shown in both columns.
4. Final Determination: Determine whether the applicable printed limit is met.

**Checks:**
- For the applicable printed mortgage-history label and loan-purpose column, CLTV does not exceed the listed maximum; 0x120x12 is Ineligible.

**Reads:** CreditReport.housing_history_rating, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** the applicable printed mortgage-history label, the loan-purpose column applicable to the printed table, the definitions of Acra's labels and how seasoning is measured (Acra confirmation requested → Q-05)

## acra-standard.credit_review_analysis_credit.no_score_pricing

**Purpose:** Confirm that a No Score file is priced as 700 Tier.

1. Initial Document Review: Review the credit report and file pricing information.
2. Eligibility Verification: Establish whether the file has No Score.
3. Validation and Verification: Verify that the file is priced as 700 Tier.
4. Final Determination: Confirm the printed instruction is applied to the file.

**Checks:**
- For No Score, the file is priced as 700 Tier.

**Reads:** CreditReport.score_count
**Missing data:** whether the file is priced as 700 Tier

## acra-standard.credit_review_analysis_credit.one_reported_score_pricing

**Purpose:** Confirm that the stated instruction for 1 Reported Score is applied, without resolving which score is the decisioning score.

1. Initial Document Review: Review the credit report and file pricing information.
2. Eligibility Verification: Establish whether the file has 1 Reported Score.
3. Validation and Verification: Verify that the instruction “Use Actual to Max 700” is applied; do not decide which score is the decisioning score, an issue identified as Acra confirmation requested → Q-19.
4. Final Determination: Confirm the printed instruction is applied to the file.

**Checks:**
- For 1 Reported Score, pricing follows “Use Actual to Max 700”.

**Reads:** CreditReport.score_count
**Missing data:** the score used for pricing, whether pricing follows “Use Actual to Max 700”, which score is the decisioning score (Acra confirmation requested → Q-19)

## acra-standard.credit_review_analysis_credit.rental_payment_or_reserve_evidence

**Purpose:** For an Applicant with forbearance or mortgage lates within the last 12-months, verify the required documentation for a Tenant occupied property.

1. Initial Document Review: Review the file for documentation of the subject property's rental payments or payment reserve.
2. Eligibility Verification: Establish whether the Applicant has had forbearance or mortgage lates within the last 12-months and whether the property is Tenant occupied.
3. Validation and Verification: If both conditions apply, verify documentation of either timely receipt for the prior two (2) months rental payments or 12-months of subject's payment in reserve, which may be from transaction's cash-in-hand.
4. Final Determination: Confirm that an applicable documentation alternative is met; do not resolve whether Applicant includes guarantors of an entity borrower, which is identified as Acra confirmation requested → Q-20.

**Checks:**
- If the condition applies, documentation establishes either timely receipt for the prior two (2) months rental payments or 12-months of subject's payment in reserve.
**Missing data:** whether the Applicant has had forbearance or mortgage lates within the last 12-months, whether the property is Tenant occupied, whether timely receipt for the prior two (2) months rental payments is documented, whether 12-months of subject's payment in reserve is documented, whether Applicant includes guarantors of an entity borrower (Acra confirmation requested → Q-20)

## acra-standard.credit_review_analysis_credit.reserves_for_fico_below_620

**Purpose:** Confirm that a file with FICO below 620 has 12 months of reserves.

1. Initial Document Review: Review the credit report and reserve documentation.
2. Eligibility Verification: Establish whether FICO is below 620.
3. Validation and Verification: Verify that reserves are 12 months when FICO is below 620.
4. Final Determination: Confirm whether the reserve requirement is met.

**Checks:**
- If FICO is below 620, reserves are 12 months.

**Reads:** CreditReport.representative_score, RatioSet.reserves_months
**Missing data:** whether reserves are 12 months, which FICO is used for this requirement

## acra-standard.credit_review_analysis_credit.short_sale_deed_in_lieu_and_modification_cltv_limits

**Purpose:** Determine whether CLTV meets the printed restriction for an applicable short sale, deed-in-lieu or modification.

1. Initial Document Review: Review the credit report and file for short sale, deed-in-lieu or modification history and its seasoning.
2. Eligibility Verification: Establish whether the borrower has had a short sale, deed-in-lieu or modification and identify the applicable loan purpose.
3. Validation and Verification: Apply the printed limits: ≥ 24 Mo—No Restrictions for both purposes; 12-23 Mo—80% Purchase, 75% Refi R/T, Refi C/O; < 12 Mo—75% Purchase, 70% Refi R/T, Refi C/O.
4. Final Determination: Determine whether the applicable printed restriction is met.

**Checks:**
- For the applicable printed seasoning and loan-purpose column, CLTV does not exceed the listed maximum.

**Reads:** Borrower.has_short_sale_dil_or_modification, Borrower.months_since_short_sale_dil_or_modification, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** the applicable seasoning as printed, whether the reported event is a short sale, deed-in-lieu or modification

## acra-standard.credit_review_analysis_credit.three_repository_scores

**Purpose:** Determine whether the applicant meets the stated three-repository credit rule.

1. Initial Document Review: Review the credit report for the repositories reporting scores.
2. Eligibility Verification: Establish whether scores are reported from 3 repositories.
3. Validation and Verification: Verify the repository count from the credit report.
4. Final Determination: Treat applicants with scores from 3 repositories as acceptable with no tradeline overlay.

**Checks:**
- If scores are reported from 3 repositories, the file is treated as acceptable with no tradeline overlay.
**Missing data:** the number of repositories reporting scores

## acra-standard.credit_review_analysis_credit.two_or_fewer_scores_tradelines

**Purpose:** Determine whether the stated tradeline rule is met when an applicant has 2 or fewer scores.

1. Initial Document Review: Review the credit report and supporting file documentation for score count, tradeline count, and history.
2. Eligibility Verification: Establish whether the applicant has 2 or fewer scores.
3. Validation and Verification: Verify either 2 tradelines & 24 month history or 3 tradelines & 12 month history.
4. Final Determination: Treat an applicant meeting either alternative as acceptable with no tradeline overlay.

**Checks:**
- If the applicant has 2 or fewer scores, the file establishes either 2 tradelines & 24 month history or 3 tradelines & 12 month history.

**Reads:** CreditReport.score_count
**Missing data:** the number and history of tradelines

## acra-standard.identification_requirements.approved_foreign_national_closing_agent

**Purpose:** Verify the title and closing agent requirement in STD-5.11.

1. Initial Document Review: Review the title and closing agent information.
2. Eligibility Verification: Identify the agent who will handle the closing.
3. Validation and Verification: Verify that the title and closing agent is approved and / or vetted by Acra.
4. Final Determination: Record whether the agent requirement is met.

**Checks:**
- The loan closes with a title and closing agent approved and / or vetted by Acra.

**Reads:** Borrower.citizenship_status
**Missing data:** Title and closing agent identity, Acra approval and / or vetting verification

## acra-standard.identification_requirements.borrower_citizenship_type

**Purpose:** Identify the borrower's citizenship type and determine whether it is an eligible type.

1. Initial Document Review: Review the case's recorded borrower citizenship type.
2. Eligibility Verification: Determine whether it is US Citizen, Permanent Resident, Non-Permanent Resident, Foreign National, or ITIN.
3. Validation and Verification: Compare Borrower.citizenship_status with the eligible types.
4. Final Determination: Record whether the borrower's citizenship type is eligible under STD-4.1.

**Checks:**
- Borrower.citizenship_status is US Citizen, Permanent Resident, Non-Permanent Resident, Foreign National, or ITIN.

**Reads:** Borrower.citizenship_status

## acra-standard.identification_requirements.foreign_account_currency_conversion

**Purpose:** Verify foreign-account assets in U.S. Dollar equivalency at the current exchange rate.

1. Initial Document Review: Review evidence of assets held in foreign accounts and the exchange-rate source used.
2. Eligibility Verification: Confirm that the assets are held in a foreign account.
3. Validation and Verification: Verify U.S. Dollar equivalency at the current exchange rate via www.xe.com or the Wall Street Journal conversion table.
4. Final Determination: Record whether the currency conversion is verified as required.

**Checks:**
- Assets held in foreign accounts are verified in U.S. Dollar equivalency at the current exchange rate via www.xe.com or the Wall Street Journal conversion table.

**Reads:** Borrower.citizenship_status
**Missing data:** Current exchange rate from www.xe.com or the Wall Street Journal conversion table, Foreign-account asset amount and its U.S. Dollar equivalency

## acra-standard.identification_requirements.foreign_account_statements

**Purpose:** Verify receipt of the account statements required by STD-5.8.

1. Initial Document Review: Review the statements for the account holding the funds.
2. Eligibility Verification: Confirm that two (2) statements are provided and identify their dates.
3. Validation and Verification: Verify that they are the two (2) most recent statements of that account.
4. Final Determination: Record whether the required statements are present.

**Checks:**
- A copy of the two (2) most recent statements of the account is provided.

**Reads:** Borrower.citizenship_status
**Missing data:** Two (2) most recent statements of the account

## acra-standard.identification_requirements.foreign_bank_statement_translation

**Purpose:** Apply the translation requirement in STD-5.8.

1. Initial Document Review: Review the language of each bank statement.
2. Eligibility Verification: Identify whether any statement is in a language other than English.
3. Validation and Verification: If a statement is in a language other than English, verify that it has been translated into English.
4. Final Determination: Record whether the applicable translation requirement is met.

**Checks:**
- Each bank statement in a language other than English is translated into English.

**Reads:** Borrower.citizenship_status
**Missing data:** English translation of each bank statement written in a language other than English

## acra-standard.identification_requirements.foreign_funds_deposit_timing

**Purpose:** Verify the funds-to-close deposit timing required by STD-5.7.

1. Initial Document Review: Review evidence of funds to close on deposit with the Escrow / Closing Agent and the closing date.
2. Eligibility Verification: Confirm the funds are sufficient to close.
3. Validation and Verification: Verify that the funds were on deposit at least three (3) business days before any closing date, including Saturdays in the calculation.
4. Final Determination: Record whether the deposit timing requirement is met.

**Checks:**
- Sufficient funds to close are on deposit with the Escrow / Closing Agent at least three (3) business days before closing, including Saturdays in the calculation.

**Reads:** Borrower.citizenship_status
**Missing data:** Amount of funds to close and amount on deposit, Deposit date, Closing date

## acra-standard.identification_requirements.foreign_funds_repatriation

**Purpose:** Verify the foreign-funds repatriation timing specified by STD-5.9.

1. Initial Document Review: Review evidence of funds held in a foreign bank or currency, repatriation, and the Closing date.
2. Eligibility Verification: Confirm that funds are held in a foreign bank or currency.
3. Validation and Verification: Verify that the funds were repatriated at least three (3) business days prior to Closing.
4. Final Determination: Record whether the repatriation timing requirement is met.

**Checks:**
- Funds held in a foreign bank or currency are repatriated at least three (3) business days prior to Closing.

**Reads:** Borrower.citizenship_status
**Missing data:** Evidence that funds held in a foreign bank or currency were repatriated, Repatriation date, Closing date

## acra-standard.identification_requirements.foreign_funds_seasoning

**Purpose:** Verify the seasoning requirement and any applicable supporting documentation.

1. Initial Document Review: Review account statements and the available funds history.
2. Eligibility Verification: For Foreign Nationals, apply the minimum 60 days seasoning requirement regardless of LTV / CLTV.
3. Validation and Verification: If funds are not seasoned a minimum of sixty (60) days, verify a letter of explanation and information to comprise a sixty (60) day chain of funds.
4. Final Determination: Record whether the seasoning requirement and any applicable supporting documentation are verified.

**Checks:**
- Foreign National funds are seasoned a minimum of 60 days, or, if not seasoned a minimum of sixty (60) days, a letter of explanation and information to comprise a sixty (60) day chain of funds are provided.

**Reads:** Borrower.citizenship_status
**Missing data:** Funds history establishing seasoning period, Letter of explanation if funds are not seasoned a minimum of sixty (60) days, Information to comprise a sixty (60) day chain of funds if funds are not seasoned a minimum of sixty (60) days

## acra-standard.identification_requirements.foreign_national_business_purpose

**Purpose:** Determine whether a Foreign National transaction is a business purpose transaction, i.e. an investment property transaction.

1. Initial Document Review: Review the transaction purpose and property use information.
2. Eligibility Verification: For a Foreign National, confirm that the transaction is for business purpose only; STD-5.1 gives investment properties as the example.
3. Validation and Verification: Verify the transaction's business-purpose status.
4. Final Determination: Record whether the business-purpose requirement is met.

**Checks:**
- The Foreign National transaction is for business purpose only.

**Reads:** Borrower.citizenship_status, LoanCore.loan_purpose, SubjectProperty.occupancy_subtype
**Missing data:** Evidence establishing whether the transaction is for business purpose

## acra-standard.identification_requirements.foreign_national_credit_reference

**Purpose:** Verify that a Foreign National provides one accepted credit-reference alternative.

1. Initial Document Review: Review the available U.S. credit report, international credit report, original international financial institution credit reference letter, and bank statement evidence.
2. Eligibility Verification: Determine whether at least one STD-5.10 alternative is provided.
3. Validation and Verification: For the U.S. credit report alternative, verify at least two (2) trade lines and a minimum age of two (2) years for one trade line. For the other alternatives, verify that the document is an international credit report, an original credit reference letter from an internationally known financial institution, or a bank statement documenting a foreign financial banking relationship for the past 60 days.
4. Final Determination: Record whether at least one alternative is verified.

**Checks:**
- At least one STD-5.10 credit-reference alternative is verified: a U.S. credit report with at least two (2) trade lines and minimum age of two (2) years for one trade line; an international credit report; an original credit reference letter from an internationally known financial institution; or a bank statement documenting a foreign financial banking relationship for the past 60 days.

**Reads:** Borrower.citizenship_status, CreditReport.score_count, CreditReport.tradelines_meet_requirement
**Missing data:** Age of at least one trade line on the U.S. credit report, International credit report, if used, Original credit reference letter from an internationally known financial institution, if used, Evidence that a bank statement documents a foreign financial banking relationship for the past 60 days, if used

## acra-standard.identification_requirements.foreign_national_fico_pricing

**Purpose:** Verify the Foreign National pricing requirement in STD-4.4.

1. Initial Document Review: Review the representative score and loan pricing information.
2. Eligibility Verification: Confirm that the borrower is a Foreign National.
3. Validation and Verification: Verify that the loan is priced at FICO equal to 700.
4. Final Determination: Record whether the pricing requirement is verified.

**Checks:**
- The Foreign National loan is priced at FICO equal to 700.

**Reads:** Borrower.citizenship_status, CreditReport.representative_score
**Missing data:** Loan pricing information establishing pricing at FICO equal to 700

## acra-standard.identification_requirements.foreign_national_financial_position_review

**Purpose:** Make the review required by STD-5.4.

1. Initial Document Review: Review information relevant to the applicant's post-close financial position and exchange rate exposure.
2. Eligibility Verification: Confirm that the review concerns a Foreign National applicant.
3. Validation and Verification: Review with scrutiny the post-close financial position and the applicant's ability to mitigate exchange rate fluctuations.
4. Final Determination: Record whether the required scrutiny review was completed.

**Checks:**
- The applicant's post-close financial position and ability to mitigate exchange rate fluctuations have been reviewed with scrutiny.

**Reads:** Borrower.citizenship_status
**Missing data:** Information establishing the applicant's post-close financial position, Information establishing the applicant's ability to mitigate exchange rate fluctuations

## acra-standard.identification_requirements.foreign_national_identity_document

**Purpose:** Verify the identity document required by STD-5.11.

1. Initial Document Review: Review the submitted copy of a Passport, Visa, or ITIN.
2. Eligibility Verification: Confirm that the document is current.
3. Validation and Verification: Verify the document copy and its current status.
4. Final Determination: Record whether a current required document is verified.

**Checks:**
- A copy of a current Passport, Visa, or ITIN is provided.

**Reads:** Borrower.citizenship_status
**Missing data:** Copy of a current Passport, Visa, or ITIN

## acra-standard.identification_requirements.foreign_national_maximum_cltv

**Purpose:** Determine whether the Foreign National transaction meets the stated maximum CLTV.

1. Initial Document Review: Review the transaction type and CLTV.
2. Eligibility Verification: Confirm that the borrower is a Foreign National and identify whether the transaction is purchase or refinance — rate & term and cash-out.
3. Validation and Verification: Compare CLTV with the stated maximum: 70% for purchase or 65% for refinance — rate & term and cash-out.
4. Final Determination: Record whether the applicable stated maximum is met.

**Checks:**
- For a purchase, CLTV is no more than 70%; for a refinance — rate & term and cash-out, CLTV is no more than 65%.

**Reads:** Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent

## acra-standard.identification_requirements.foreign_national_power_of_attorney

**Purpose:** Verify the conditional Power of Attorney requirement in STD-5.11.

1. Initial Document Review: Determine whether a Power of Attorney is used and, if so, review it.
2. Eligibility Verification: If a Power of Attorney is used, assess conformity with Acra requirements and title company acceptability.
3. Validation and Verification: Verify both required conditions for a Power of Attorney that is used.
4. Final Determination: Record whether the conditional requirement is met.

**Checks:**
- If a Power of Attorney is used, it conforms to Acra requirements and is acceptable to the title company.

**Reads:** Borrower.citizenship_status
**Missing data:** Power of Attorney, if used, Acra conformity verification, if a Power of Attorney is used, Title company acceptance, if a Power of Attorney is used

## acra-standard.identification_requirements.foreign_national_residence_status

**Purpose:** Determine whether the Foreign National borrower resides outside the U.S. and is not authorized to live or work in the U.S.

1. Initial Document Review: Review available information about the borrower's primary residence and authorization to live or work in the U.S.
2. Eligibility Verification: Assess the STD-4.4 description that the borrower's Primary Residence is not located in the United States of America and the STD-5.2 description of a Non-Resident Alien not authorized to live or work in the U.S. who must reside outside the U.S.
3. Validation and Verification: Resolve whether the borrower meets those stated facts; do not treat periodic U.S. visits, limited personal use or investment, or ownership of a U.S.-based business entity as disqualifying by themselves.
4. Final Determination: Record whether the borrower meets the stated Foreign National residence and authorization description.

**Checks:**
- The borrower resides outside the U.S., has a Primary Residence not located in the United States of America, and is not authorized to live or work in the U.S.

**Reads:** Borrower.citizenship_status
**Missing data:** Borrower's country of residence and location of Primary Residence, Whether the borrower is authorized to live or work in the U.S.

## acra-standard.identification_requirements.foreign_national_w_8

**Purpose:** Verify the executed W-8 (BEN) IRS form required by STD-5.11.

1. Initial Document Review: Review the submitted W-8 (BEN) IRS form.
2. Eligibility Verification: Confirm that the form is executed.
3. Validation and Verification: Verify the executed form.
4. Final Determination: Record whether the executed form is verified.

**Checks:**
- An executed W-8 (BEN) IRS form is provided.

**Reads:** Borrower.citizenship_status
**Missing data:** Executed W-8 (BEN) IRS form

## acra-standard.identification_requirements.foreign_signed_documents_acknowledgment

**Purpose:** Verify the STD-5.12 acknowledgment requirements for documents signed outside the U.S.

1. Initial Document Review: Identify whether documents are signed outside the U.S. and review the acknowledgment and authentication provided.
2. Eligibility Verification: Determine which stated route applies: notarization by a U.S. embassy or consular official, or signing in a country that is party to the Hague Convention Treaty Abolishing the Requirement of Legalization for Foreign Public Documents.
3. Validation and Verification: For the embassy or consular route, verify the certificate of acknowledgement includes the embassy or consular seal and is acceptable to the title company. For the Hague Convention route, verify an authorized notary public completed and signed the certificate of acknowledgment, authentication by apostille in English is attached to the executed documents, and the title company accepts it.
4. Final Determination: Record whether the applicable route's stated requirements are verified.

**Checks:**
- For documents signed outside the U.S., the applicable STD-5.12 acknowledgment route and its stated requirements are met.

**Reads:** Borrower.citizenship_status
**Missing data:** Whether documents were signed outside the U.S. and, if so, the country of signing, Certificate of acknowledgement and embassy or consular seal, if the embassy or consular route is used, Title company acceptance, if the embassy or consular route is used, Authorized notary public's completed and signed certificate of acknowledgment, English apostille attached to the executed documents, and title company acceptance, if the Hague Convention route is used

## acra-standard.identification_requirements.itin_foreign_national_eligibility

**Purpose:** Apply STD-5.3's stated condition for ITIN holders' eligibility for the Foreign National Program.

1. Initial Document Review: For an ITIN holder reviewed for the Foreign National Program, review information about residence.
2. Eligibility Verification: Confirm whether the ITIN holder resides outside of the U.S.
3. Validation and Verification: Verify the residence information.
4. Final Determination: Record whether the STD-5.3 residence condition is met.

**Checks:**
- The ITIN holder resides outside of the U.S.

**Reads:** Borrower.citizenship_status
**Missing data:** ITIN holder's country of residence

## acra-standard.identification_requirements.itin_loan_amount_and_minimum_fico

**Purpose:** Determine whether the ITIN loan amount and representative score meet the stated limits.

1. Initial Document Review: Review the ITIN borrower's loan amount and representative score.
2. Eligibility Verification: Confirm that the borrower is an ITIN holder.
3. Validation and Verification: Compare the loan amount with the maximum loan amount $1.0M and the FICO score with minimum FICO 640.
4. Final Determination: Record whether both stated limits are met.

**Checks:**
- The ITIN loan amount is no more than $1.0M and the representative FICO score is at least 640.

**Reads:** Borrower.citizenship_status, LoanCore.total_loan_amount_usd, CreditReport.representative_score

## acra-standard.identification_requirements.itin_maximum_cltv

**Purpose:** Preserve the printed ITIN CLTV matrix and route its unresolved tier interpretation for Acra confirmation.

1. Initial Document Review: Review the ITIN borrower's FICO, transaction type, and CLTV.
2. Eligibility Verification: Confirm that the borrower is an ITIN holder.
3. Validation and Verification: Preserve the printed tiers: “FICO 700” — 70% purchase and 65% refinance — R/T and cash-out; “FICO 660 to 699” — 65% purchase and 60% refinance — R/T and cash-out; “FICO 640 to 659” — 60% purchase and 60% refinance — R/T and cash-out. Do not interpret whether “FICO 700” means 700 and above; obtain Acra confirmation.
4. Final Determination: Apply the tier only as confirmed by Acra.

**Checks:**
- Acra confirmation resolves whether the printed “FICO 700” tier means 700 and above before that tier is applied.

**Reads:** Borrower.citizenship_status, CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Acra confirmation on whether the printed “FICO 700” tier means 700 and above

## acra-standard.identification_requirements.itin_u_s_residence_eligibility_clarification

**Purpose:** Preserve the source's unresolved question about whether a U.S.-resident ITIN holder is eligible.

1. Initial Document Review: Review the ITIN borrower's residence information.
2. Eligibility Verification: Determine whether the borrower resides in the U.S. or outside the U.S.
3. Validation and Verification: For a U.S.-resident ITIN holder, do not determine eligibility from the unresolved source text; obtain Acra confirmation.
4. Final Determination: Record the residence and any Acra confirmation.

**Checks:**
- For a U.S.-resident ITIN holder, Acra confirmation resolves whether the borrower is eligible.

**Reads:** Borrower.citizenship_status
**Missing data:** ITIN holder's country of residence, Acra confirmation of whether a U.S.-resident ITIN holder is eligible

## acra-standard.identification_requirements.non_permanent_resident_limits

**Purpose:** Address the STD-4.3 printed limits while preserving the source's unresolved question about their meaning.

1. Initial Document Review: Review the Non-Permanent Resident loan terms and the printed limit text.
2. Eligibility Verification: Confirm that the borrower is recorded as a Non-Permanent Resident.
3. Validation and Verification: Preserve the printed text “Max Loan Amount: $1.5M: Max CLTV 80%” without deciding whether it states two independent limits or one conditional limit.
4. Final Determination: Obtain or record Acra confirmation of the limit's meaning before applying it.

**Checks:**
- Acra confirmation resolves whether the printed text “Max Loan Amount: $1.5M: Max CLTV 80%” is two independent limits or one conditional limit.

**Reads:** Borrower.citizenship_status
**Missing data:** Acra confirmation of the meaning of the printed Non-Permanent Resident limits

## acra-standard.identification_requirements.non_permanent_resident_residency_proof

**Purpose:** Verify the legal-residency proof required by STD-4.3.

1. Initial Document Review: For a borrower recorded as a Non-Permanent Resident, review proof of legal residency.
2. Eligibility Verification: Check whether the proof includes an unexpired employment authorization document (EAD) or valid visa, which are examples listed in STD-4.3.
3. Validation and Verification: Verify the residency proof and any stated expiration or validity.
4. Final Determination: Record whether proof of legal residency is verified.

**Checks:**
- The Non-Permanent Resident provides proof of legal residency.

**Reads:** Borrower.citizenship_status
**Missing data:** Proof of legal residency, such as an unexpired employment authorization document (EAD) or valid visa

## acra-standard.identification_requirements.permanent_resident_documents

**Purpose:** Verify the Permanent Resident documentation required by STD-4.2.

1. Initial Document Review: For a borrower recorded as a Permanent Resident, obtain and review the PRA ID and SSA card or SSA-89.
2. Eligibility Verification: Confirm that the PRA ID is unexpired and that an SSA card or SSA-89 is present.
3. Validation and Verification: Verify the documents and their stated validity.
4. Final Determination: Record whether both required items are verified.

**Checks:**
- The Permanent Resident has an unexpired PRA ID and an SSA card or SSA-89.

**Reads:** Borrower.citizenship_status
**Missing data:** PRA ID and its expiration date, SSA card or SSA-89

## acra-standard.income_stability_sufficiency_analysis.apply_dscr_below_one_or_no_ratio_limits

**Purpose:** Determine whether a DSCR below 1.0 or No Ratio transaction meets the applicable CLTV and FICO limits.

1. Initial Document Review: Review the loan_application and credit_report for transaction and credit information.
2. Eligibility Verification: Determine whether DSCR is below 1.0 or the file is No Ratio, and identify purchase, rate & term refinance, or cash-out refinance.
3. Validation and Verification: Compare CLTV with the applicable maximum and FICO with the minimum.
4. Final Determination: Record whether all applicable limits are met.

**Checks:**
- For DSCR below 1.0 or No Ratio, purchase CLTV is no more than 75%.
- For DSCR below 1.0 or No Ratio, refinance — rate & term CLTV is no more than 70%.
- For DSCR below 1.0 or No Ratio, refinance — cash-out CLTV is no more than 65%.
- For DSCR below 1.0 or No Ratio, FICO is at least 640.

**Reads:** LoanCore.cltv_percent, LoanCore.loan_purpose, CreditReport.representative_score, LoanCore.dscr_qualification_method
**Missing data:** Calculated DSCR, Whether the file is No Ratio, FICO

## acra-standard.income_stability_sufficiency_analysis.apply_scenario_specific_minimum_dscr

**Purpose:** Determine whether the loan meets the minimum DSCR and reserve requirements stated for the applicable program scenarios.

1. Initial Document Review: Review the loan_application, appraisal_report, and credit_report for transaction, property, and credit information.
2. Eligibility Verification: Identify each applicable scenario listed in the checks, including any scenario requiring data not held in the case fields.
3. Validation and Verification: Compare DSCR with each applicable minimum and verify the stated reserves requirement when LTV is above 80.00%.
4. Final Determination: Record whether every applicable minimum DSCR and reserve requirement is met. Do not resolve the stated Q-14 alternatives by assumption.

**Checks:**
- If LTV is above 80.00%, DSCR is at least 1.20.
- If LTV is above 80.00%, reserves are at least 6 months PITIA.
- If loan amount is over $2,000,000, DSCR is at least 1.0.
- If there is 1 or no score / deficient tradelines, DSCR is at least 1.1.
- If the property is rural / unique, DSCR is at least 1.00.
- If the property is a non-warrantable condo; condotel / PUDtel, DSCR is at least 1.0.
- If the borrower is a first-time homebuyer, DSCR is at least 1.150.
- For a vacant property, rate & term refinance, DSCR is at least 1.000; the stated “OR Maximum 40.0% DTI” alternative is not resolved here.
- For a vacant property, cash-out refinance, DSCR is at least 1.15.
- If the property was listed for sale within six months, DSCR is at least 1.0; the stated “or (b) 43% maximum DTI” alternative is not resolved here.
- For mixed use, adult care or assisted living, DSCR is at least 1.2.

**Reads:** LoanCore.total_loan_amount_usd, CreditReport.score_count, CreditReport.tradelines_meet_requirement, Borrower.is_first_time_homebuyer, SubjectProperty.is_vacant, LoanCore.loan_purpose, SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_mixed_use, SubjectProperty.is_rural, LoanCore.cltv_percent, RatioSet.reserves_months
**Missing data:** LTV, Calculated DSCR, PITIA reserves amount, Whether the property is unique, Whether the property is a non-warrantable condo, condotel, or PUDtel, Whether the property is used for adult care or assisted living, Whether “OR Maximum 40.0% DTI” or “or (b) 43% maximum DTI” applies

## acra-standard.income_stability_sufficiency_analysis.apply_short_term_rental_limits

**Purpose:** Determine whether a short-term-rental purchase or refinance meets the stated CLTV and FICO limits.

1. Initial Document Review: Review the loan_application and credit_report for transaction and credit information.
2. Eligibility Verification: Determine whether the property qualifies with short-term rentals and whether the transaction is a purchase or refinance.
3. Validation and Verification: Compare CLTV with the applicable maximum and compare FICO with the minimum.
4. Final Determination: Record whether all applicable short-term rental limits are met.

**Checks:**
- For a purchase qualifying with short-term rentals, CLTV is no more than 75%.
- For a refinance qualifying with short-term rentals, CLTV is no more than 70%.
- For a transaction qualifying with short-term rentals, FICO is at least 640.

**Reads:** LoanCore.cltv_percent, LoanCore.loan_purpose, CreditReport.representative_score
**Missing data:** Whether the property qualifies with short-term rentals, Whether the transaction is a purchase or refinance, FICO

## acra-standard.income_stability_sufficiency_analysis.calculate_dscr

**Purpose:** Determine the DSCR for the loan using the stated formula and payment basis.

1. Initial Document Review: Review the appraisal_report and any lease_agreement, bank_statement, hazard_insurance, and hoa_questionnaire available for the rent and PITIA information.
2. Eligibility Verification: Identify annual in-place rent, market rent, and the first payment due under the Note; include subordinate financing, if applicable, in the denominator.
3. Validation and Verification: Calculate annual PITIA as annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees; use the lesser of annual in-place rent or market rent as the numerator.
4. Final Determination: Divide the qualifying annual rent by annual PITIA and record the resulting DSCR. Do not resolve the stated interest-only payment question by assumption.

**Checks:**
- The numerator is the lesser of annual in-place rent or market rent.
- The denominator is the sum of annual principal, interest, real estate taxes, property insurance, homeowner's / condominium association fees, and subordinate financing if applicable.
- The DSCR uses the first payment due under the terms of the Note.
**Missing data:** Annual in-place rent, Market rent, Annual principal, Annual interest, Annual real estate taxes, Annual property insurance, Annual homeowner's / condominium association fees, Subordinate financing amount, if applicable, First payment due under the Note, Which payment enters the denominator for an interest-only loan

## acra-standard.income_stability_sufficiency_analysis.verify_higher_actual_rent_evidence

**Purpose:** Determine whether the stated evidence for actual rents exceeding market rents is documented.

1. Initial Document Review: Review the lease_agreement and bank_statement for the rental income evidence.
2. Eligibility Verification: Establish whether actual rents exceed market rents.
3. Validation and Verification: If actual rents exceed market rents, verify two consecutive months proof of rental income receipt and lease agreement(s) continuing at a minimum of three (3) months after closing. Verify that security deposits are not counted toward receipt and rents are not prepaid.
4. Final Determination: Record whether each applicable evidence requirement is met.

**Checks:**
- If actual rents exceed market rents, two (2) consecutive months proof of rental income receipt is documented, excluding security deposits and prepaid rents.
- If actual rents exceed market rents, lease agreement(s) continue at a minimum of three (3) months after closing.
**Missing data:** Actual rent, Market rent, Rental receipt dates and amounts, Lease end date or dates, Closing date, Whether a receipt is a security deposit or prepaid rent

## acra-standard.income_stability_sufficiency_analysis.verify_required_1007

**Purpose:** Determine whether the required 1007 is provided in the applicable DSCR and single-family scenarios.

1. Initial Document Review: Review the appraisal_report for a Form 1007.
2. Eligibility Verification: Determine whether the loan is a DSCR transaction, including No Ratio DSCR, or whether it is a single-family file with proposed rental income or a lease-option transaction where the down payment required in §3.45 is generated from excess monthly rent contributions.
3. Validation and Verification: For a single-family property, verify that the Form 1007 is from the original appraiser or any state licensed appraiser. Do not treat a Form 1025 as satisfying the requirement unless that is confirmed by Acra.
4. Final Determination: Record whether the applicable 1007 requirement is met.

**Checks:**
- A Form 1007 is provided on every DSCR transaction, including No Ratio DSCR.
- For a single-family property in a stated §14.12 scenario, the required Form 1007 is provided and is from the original appraiser or any state licensed appraiser.

**Reads:** LoanCore.dscr_qualification_method, SubjectProperty.property_type
**Missing data:** Whether the transaction is a DSCR transaction, Whether proposed rental income is being used to qualify, Whether the transaction is a lease-option purchase whose required down payment is generated from excess monthly rent contributions, Whether the property is single-family

## acra-standard.income_stability_sufficiency_analysis.verify_short_term_rental_appraisal

**Purpose:** Determine whether an appraisal form used instead of a 1007 for a short-term rental meets the stated form and signature requirements.

1. Initial Document Review: Review the appraisal_report for an STRpro or similar appraisal form.
2. Eligibility Verification: Determine whether the property is occupied as a short-term rental.
3. Validation and Verification: If it is, verify that the STRpro or similar appraisal form is signed by an appropriately licensed appraiser.
4. Final Determination: Record whether the applicable short-term rental appraisal-form requirement is met.

**Checks:**
- For a property occupied as a short-term rental, an STRpro or similar appraisal form used as a replacement to a 1007 is signed by an appropriately licensed appraiser.
**Missing data:** Whether the property is occupied as a short-term rental, Whether the appraisal form is being used as a replacement to a 1007, Whether the appraiser is appropriately licensed

## acra-standard.income_stability_sufficiency_analysis.verify_short_term_rental_ledger

**Purpose:** Determine whether the stated short-term rental ledger documentation is present when it is used to document actual rents.

1. Initial Document Review: Review any 12-month rental ledger provided by a condotel management company, property manager, AirBnB, VRBO, or similar source.
2. Eligibility Verification: Determine whether actual rents for a short-term rental are being documented with the ledger.
3. Validation and Verification: Verify that the ledger covers 12 months and is from a stated or similar source.
4. Final Determination: Record the ledger as documentation for actual rents; do not infer how it establishes qualifying rent or how the receipt and lease conditions apply.

**Checks:**
- A ledger used as documentation for actual rents for a short-term rental covers 12 months and is from a condotel management company, property manager, AirBnB, VRBO, or similar source.
**Missing data:** Whether actual rents for a short-term rental are being documented with a ledger, Ledger period, Ledger source

## acra-standard.income_stability_sufficiency_analysis.verify_vacant_property_rent_source

**Purpose:** Determine whether qualifying rents for a vacant-property purchase are taken from the applicable appraisal rent schedule.

1. Initial Document Review: Review the appraisal_report for a Form 1007 or Form 1025, as applicable.
2. Eligibility Verification: Determine whether the property is vacant and being purchased.
3. Validation and Verification: Verify that qualifying rents are taken from the applicable Form 1007 or Form 1025. For rental income from the purchase of a vacant property that is the subject of an Acra loan, verify the 1007 survey requirement.
4. Final Determination: Record whether the applicable appraisal rent-source requirement is met.

**Checks:**
- For a vacant-property purchase, qualifying rents are taken from the applicable Form 1007 or Form 1025.
- Rental income from the purchase of a vacant property that is the subject of an Acra loan has a 1007 survey.

**Reads:** SubjectProperty.is_vacant, LoanCore.loan_purpose
**Missing data:** Which appraisal form is applicable, Whether the property is the subject of an Acra loan

## acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_coverage_scope

**Purpose:** Verify the stated coverage scope of rent loss insurance when the requirement applies.

1. Initial Document Review: Review the hazard insurance declarations for rent loss coverage terms.
2. Eligibility Verification: Confirm that the rent loss insurance requirement applies to the case.
3. Validation and Verification: Verify that the coverage is for rental losses incurred during rehabilitation following a casualty.
4. Final Determination: Record whether the insurance evidence establishes the stated rent loss coverage scope.

**Checks:**
- The policy covers rental losses incurred during rehabilitation following a casualty.
**Missing data:** Whether the policy covers rental losses incurred during rehabilitation following a casualty

## acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability

**Purpose:** Determine whether six (6) months' rent loss insurance is required for the subject property.

1. Initial Document Review: Review the available case information for the subject property's occupancy, unit count, and qualification method.
2. Eligibility Verification: Determine whether the subject property is a one- to four-unit non-owner occupied income property and whether subject property rents are used to qualify; include No Ratio DSCR when assessing rent use.
3. Validation and Verification: Determine whether LTV is > 70% and whether CLTV is ≤ 70%. If LTV is at or below 70% while CLTV is above 70%, request Acra confirmation.
4. Final Determination: Record whether the six (6) months' rent loss insurance requirement applies, does not apply, or awaits the requested Acra confirmation.

**Checks:**
- The subject property is non-owner occupied.
- The subject property is an income property.
- The subject property has one to four units.
- Subject property rents are used to qualify, including No Ratio DSCR.
- LTV is > 70%.
- CLTV is ≤ 70%.
- LTV is at or below 70% while CLTV is above 70%.

**Reads:** SubjectProperty.occupancy_subtype, SubjectProperty.number_of_units, LoanCore.dscr_qualification_method, LoanCore.cltv_percent
**Missing data:** Whether the subject property is an income property, Whether subject property rents are used to qualify, LTV, Acra confirmation for the case where LTV is at or below 70% and CLTV is above 70%

## acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_reserve_substitution

**Purpose:** Determine whether the borrower has the reserves required for the permitted rent loss insurance substitution.

1. Initial Document Review: Review the hazard insurance declarations for the amount of rent loss coverage not provided.
2. Eligibility Verification: Confirm that rent loss insurance is required and cannot be obtained.
3. Validation and Verification: Compare reserves with the requirement of two (2) months reserves for every one (1) month of rent loss coverage not provided.
4. Final Determination: Record whether the reserve substitution meets the stated amount.

**Checks:**
- Reserves are at least two (2) months for every one (1) month of rent loss coverage not provided.

**Reads:** RatioSet.reserves_months
**Missing data:** Number of months of rent loss coverage not provided

## acra-standard.insurance_coverage_sufficiency_policy_assessment.six_month_rent_loss_coverage

**Purpose:** Determine whether the required six (6) months' rent loss insurance coverage is provided.

1. Initial Document Review: Review the hazard insurance declarations for the rent loss coverage period.
2. Eligibility Verification: Confirm that the rent loss insurance requirement applies to the case.
3. Validation and Verification: Verify whether six (6) months' rent loss insurance coverage is provided.
4. Final Determination: Record whether the required coverage period is provided or whether the borrower may use the reserve substitution addressed by the separate reserve-substitution job.

**Checks:**
- Six (6) months' rent loss insurance coverage is provided.
**Missing data:** Number of months of rent loss insurance coverage provided

## acra-standard.loan_program_eligibility.delayed_financing_loan_amount_cap

**Purpose:** Determine whether a delayed-financing loan is capped at $1.5MM.

1. Initial Document Review: Review the loan application for delayed-financing status and loan amount.
2. Eligibility Verification: Determine whether the transaction is delayed financing.
3. Validation and Verification: If delayed financing applies, verify that the loan amount does not exceed $1.5MM.
4. Final Determination: Record whether the delayed-financing cap is met.

**Checks:**
- If the loan is delayed financing, the loan amount does not exceed $1.5MM.

**Reads:** LoanCore.is_delayed_financing, LoanCore.total_loan_amount_usd

## acra-standard.loan_program_eligibility.first_time_homebuyer_dscr_conditions

**Purpose:** Determine whether a First Time Home Buyers DSCR loan meets the stated FICO, CLTV, DSCR, loan amount, amortization, impound, and reserve requirements.

1. Initial Document Review: Review the loan application, credit_report, and available DSCR and reserve information.
2. Eligibility Verification: Apply this job only when the application is a First Time Home Buyers application and the loan qualifies by DSCR.
3. Validation and Verification: Verify minimum 700 FICO, maximum 70% CLTV, minimum DSCR of 1.150, maximum loan amount of $1,000,000, full amortization with no interest-only programs, impounds, and minimum six months reserves.
4. Final Determination: Record whether every stated first-time-homebuyer DSCR condition is met.

**Checks:**
- Representative FICO is at least 700.
- CLTV is no greater than 70%.
- DSCR is at least 1.150.
- Loan amount is no greater than $1,000,000.
- The loan is fully amortizing and is not an interest-only program.
- Impounds are required.
- Reserves are at least six months.

**Reads:** Borrower.is_first_time_homebuyer, LoanCore.dscr_qualification_method, CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.total_loan_amount_usd, MortgageLoanInformation.is_interest_only, LoanCore.is_escrow_waived, RatioSet.reserves_months
**Missing data:** Calculated DSCR

## acra-standard.loan_program_eligibility.first_time_homebuyer_status

**Purpose:** Establish the First Time Home Buyers fact used by the program's first-time-homebuyer requirements.

1. Initial Document Review: Review the loan application for each Applicant's prior homeownership history.
2. Eligibility Verification: Apply Acra's definition that all Applicants must have never previously owned a home (real property).
3. Validation and Verification: Verify the reported history for all Applicants.
4. Final Determination: Record whether the application is a First Time Home Buyers application under Acra's definition.

**Checks:**
- All Applicants have never previously owned a home (real property).

**Reads:** Borrower.is_first_time_homebuyer
**Missing data:** Prior homeownership history for all Applicants

## acra-standard.loan_program_eligibility.interest_only_10_yr_40_year_term_limits

**Purpose:** Verify the maximum 80% LTV / CLTV and maximum $3M loan amount for the 10 Yr / 40 Year Term interest-only product.

1. Initial Document Review: Review the loan application for 10 Yr / 40 Year Term interest-only status, CLTV, and loan amount.
2. Eligibility Verification: Determine whether the loan is Interest Only, 10 Yr / 40 Year Term.
3. Validation and Verification: Verify maximum 80% LTV / CLTV and maximum $3M loan amount.
4. Final Determination: Record whether both stated limits are met.

**Checks:**
- If the loan is Interest Only, 10 Yr / 40 Year Term, CLTV is no greater than 80%.
- If the loan is Interest Only, 10 Yr / 40 Year Term, loan amount is no greater than $3M.

**Reads:** LoanCore.is_interest_only_10_40, LoanCore.cltv_percent, LoanCore.total_loan_amount_usd

## acra-standard.loan_program_eligibility.interest_only_availability_restrictions

**Purpose:** Determine whether an interest-only loan is barred because the borrower is a first-time homebuyer, the refinance is on a vacant property, or the property is listed for sale.

1. Initial Document Review: Review the loan application for interest-only status, first-time-homebuyer status, loan purpose, vacancy, and listing status.
2. Eligibility Verification: Determine whether the loan is interest-only and whether any stated restriction applies.
3. Validation and Verification: Verify that an interest-only loan is not for a first-time homebuyer, a vacant-property refinance, or a property listed for sale.
4. Final Determination: Record whether any stated restriction makes interest-only unavailable.

**Checks:**
- If the loan is interest-only, the borrower is not a first-time homebuyer.
- If the loan is interest-only and the loan purpose is a refinance, the property is not vacant.
- If the loan is interest-only, the property is not listed for sale.

**Reads:** MortgageLoanInformation.is_interest_only, Borrower.is_first_time_homebuyer, LoanCore.loan_purpose, SubjectProperty.is_vacant, SubjectProperty.is_listed_for_sale

## acra-standard.loan_program_eligibility.interest_only_loan_amount_and_credit_minimums

**Purpose:** Apply the interest-only minimum and maximum loan amounts and minimum FICO stated in the program and product requirements.

1. Initial Document Review: Review the loan application and credit_report for interest-only status, loan amount, and representative FICO.
2. Eligibility Verification: Determine whether the loan is an interest-only loan.
3. Validation and Verification: Verify minimum loan amount $250,000, maximum loan amount $3,000,000, and minimum FICO 640.
4. Final Determination: Record whether the applicable interest-only amount and credit requirements are met.

**Checks:**
- If the loan is interest-only, the loan amount is at least $250,000.
- If the loan is interest-only, the loan amount is no greater than $3,000,000.
- If the loan is interest-only, representative FICO is at least 640.

**Reads:** MortgageLoanInformation.is_interest_only, LoanCore.is_interest_only_10_40, LoanCore.total_loan_amount_usd, CreditReport.representative_score

## acra-standard.loan_program_eligibility.investment_property_fico_and_cltv_matrix

**Purpose:** Determine the published matrix CLTV limit for the loan's loan-amount tier, representative FICO, and transaction column.

1. Initial Document Review: Review the loan application and credit_report for loan amount, loan purpose, and representative FICO.
2. Eligibility Verification: Select the printed loan-amount tier, minimum-FICO row, and Purchase, Rate & Term, or Cash-Out column that apply.
3. Validation and Verification: Compare the proposed CLTV with the selected matrix value; treat NA as NA. For loans of $1,500,000 or less with a score below 600, note that no row is printed and the document requests Acra confirmation on eligibility.
4. Final Determination: Record whether the published matrix value permits the proposed CLTV, or whether Acra confirmation is required because no row is printed.

**Checks:**
- Where the matrix prints a value for the loan amount, representative FICO, and loan purpose, the proposed CLTV does not exceed that value.
- For loans of $1,500,000 or less with a score below 600, Acra confirmation is obtained because no row is printed and eligibility is not stated.

**Reads:** LoanCore.total_loan_amount_usd, CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Acra confirmation of eligibility for loans of $1,500,000 or less with a score below 600

## acra-standard.loan_program_eligibility.investment_property_status

**Purpose:** Establish whether the property is eligible as an investment property under STD-1.1 and STD-1.2.

1. Initial Document Review: Review the loan application and lease_agreement for the subject property's occupancy and lease information.
2. Eligibility Verification: Determine whether the property is a one- to four-unit residential dwelling or a unit in a condominium complex or a PUD.
3. Validation and Verification: Verify that the dwelling is leased and occupied as a principal year-round residence to individuals other than the owner, and that the owner does not occupy it.
4. Final Determination: Record whether the subject property meets the investment-property definition.

**Checks:**
- The property is a one- to four-unit residential dwelling or a unit in a condominium complex or a PUD.
- The dwelling is not occupied by its owner.
- The dwelling is leased and occupied as a principal year-round residence to individuals other than the owner.

**Reads:** SubjectProperty.property_type, SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease
**Missing data:** Whether the owner occupies the dwelling, Whether the dwelling is occupied as a principal year-round residence by individuals other than the owner

## acra-standard.loan_program_eligibility.loan_amount_above_2_000_000_dscr_requirement

**Purpose:** Determine whether a loan amount above $2,000,000 has 1.0 or greater DSCR.

1. Initial Document Review: Review the loan application and the DSCR calculation.
2. Eligibility Verification: Determine whether the loan amount is above $2,000,000.
3. Validation and Verification: For a loan amount above $2,000,000, verify that DSCR is 1.0 or greater.
4. Final Determination: Record whether the required DSCR is met.

**Checks:**
- If the loan amount is above $2,000,000, DSCR is 1.0 or greater.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.dscr_qualification_method
**Missing data:** Calculated DSCR

## acra-standard.loan_program_eligibility.loan_amount_below_200_000_cltv_limit

**Purpose:** Verify the loan-specific CLTV cap for loan amounts below $200,000.

1. Initial Document Review: Review the loan application for loan amount, loan purpose, and CLTV.
2. Eligibility Verification: Determine whether the loan amount is below $200,000 and whether the transaction is purchase or refinance.
3. Validation and Verification: Apply maximum CLTV 80% for purchase and 75% for refinance (rate & term and cash-out).
4. Final Determination: Record whether the applicable maximum CLTV is met.

**Checks:**
- If the loan amount is below $200,000 and the loan purpose is purchase, CLTV is no greater than 80%.
- If the loan amount is below $200,000 and the loan purpose is rate & term or cash-out refinance, CLTV is no greater than 75%.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.loan_purpose, LoanCore.cltv_percent

## acra-standard.loan_program_eligibility.prepayment_penalty_minimum_terms

**Purpose:** Apply the minimum terms stated for the specified transactions, subject to the printed qualifications.

1. Initial Document Review: Review the loan application for loan purpose, vacancy, listing status, state, and prepayment penalty term.
2. Eligibility Verification: Determine whether the transaction is a vacant-property rate & term refinance, vacant-property cash-out refinance, or involves a property listed for sale.
3. Validation and Verification: Verify at least two years for vacant-property rate & term refinance and at least three years for vacant-property cash-out refinance, each “where allowable”; verify at least three years for a property listed for sale unless the property is located in a state that does not allow prepayment penalties. Do not resolve the stated Acra-confirmation question about how a state restriction interacts with these minimums.
4. Final Determination: Record compliance with an applicable minimum or identify that Acra confirmation is required for the state interaction.

**Checks:**
- If the transaction is a vacant-property rate & term refinance where allowable, the prepayment penalty term is at least two years.
- If the transaction is a vacant-property cash-out refinance where allowable, the prepayment penalty term is at least three years.
- If the property is listed for sale and is not in a state that does not allow prepayment penalties, the prepayment penalty term is at least three years.
- If a state restriction applies to an applicable minimum, Acra confirmation is obtained on how the restriction interacts with that minimum.

**Reads:** LoanCore.loan_purpose, SubjectProperty.is_vacant, SubjectProperty.is_listed_for_sale, SubjectProperty.state, LoanCore.prepayment_penalty_structure
**Missing data:** Whether a vacant-property refinance is allowable, Whether the property is located in a state that does not allow prepayment penalties, Acra confirmation of how a state restriction interacts with the stated minimum terms, The selected prepayment penalty term as documented

## acra-standard.loan_program_eligibility.prepayment_penalty_structure

**Purpose:** Determine whether the selected term and structure match a listed prepayment penalty structure.

1. Initial Document Review: Review the loan application for the selected prepayment penalty structure.
2. Eligibility Verification: Compare the selected term and structure with the structures printed in the guidelines.
3. Validation and Verification: Verify the structure against the printed 5 Year, 4 Year, 3 Year, 2 Year, 1 Year, or No Prepay entries.
4. Final Determination: Record whether the selected structure is listed.

**Checks:**
- The selected prepayment penalty term and structure match a structure printed in STD-11.1.

**Reads:** LoanCore.prepayment_penalty_structure
**Missing data:** The selected prepayment penalty term and structure as documented

## acra-standard.loan_program_eligibility.qualification_method

**Purpose:** Record the program's qualification method before applying the applicable qualification requirements.

1. Initial Document Review: Review the loan application for the stated DSCR qualification method.
2. Eligibility Verification: Identify whether the loan qualifies by a calculated DSCR or as No Ratio DSCR.
3. Validation and Verification: Verify the method against the case record.
4. Final Determination: Record the qualification method.

**Checks:**
- The loan qualification method is either calculated DSCR or No Ratio DSCR.

**Reads:** LoanCore.dscr_qualification_method
