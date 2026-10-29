# Our jobs, standard (121)

## acra-standard.appraisal_review.actual_rent_evidence

**Purpose:** Verify the specified evidence of actual rent receipt and continuing lease term when actual rents exceed market rents.

1. Step 1 - Initial Document Review: Review the rent evidence and lease agreements for actual rents, market rents, receipt history, and lease term.
2. Step 2 - Eligibility Verification: Determine whether actual rents exceed market rents.
3. Step 3 - Validation and Verification: If actual rents exceed market rents, verify documentation of two (2) consecutive months proof of rental income receipt and lease agreement(s) to continue at a minimum of three (3) months after closing. Verify that security deposit does not count towards receipt and that rents are not prepaid.
4. Step 4 - Final Determination: Record whether the stated actual-rent evidence and lease conditions are met. Do not resolve whether STD-3.5 or STD-3.6 governs.

**Checks:**
- When actual rents exceed market rents, evidence documents two (2) consecutive months proof of rental income receipt and lease agreement(s) to continue at a minimum of three (3) months after closing; security deposit is not counted towards receipt, and rents are not prepaid.
**Missing data:** Actual rent and market rent amounts., The dates and amounts of rental income receipts and whether they represent two (2) consecutive months., Whether any receipt is a security deposit or prepaid rent., The lease end date and closing date., Which of STD-3.5 and STD-3.6 governs qualifying rent, and whether the stated evidence is sufficient or further approval is required.

## acra-standard.appraisal_review.excessive_lease_rent_support

**Purpose:** Determine whether documentation supports that excessive monthly rent reflected on the lease is typical for the area.

1. Step 1 - Initial Document Review: Review the lease for monthly rent and review any documentation submitted to support typical rent for the area.
2. Step 2 - Eligibility Verification: Determine whether the property is a single-family investment property and whether the lease reflects excessive monthly rent payments.
3. Step 3 - Validation and Verification: Verify that documentation supporting that the monthly rent is typical for the area is provided. Acceptable documentation may include classified ads from local newspapers, a Form 1007 completed by the appraiser, or a market rent survey completed by a local real estate company or rental management company familiar with market rents in the area.
4. Step 4 - Final Determination: Record whether the stated rent-support requirement is met.

**Checks:**
- If a single-family investment property's lease reflects excessive monthly rent payments, documentation supporting that the monthly rent is typical for the area is provided.

**Reads:** SubjectProperty.property_type
**Missing data:** Whether the property is an investment property., Whether monthly rent payments reflected on the lease are excessive., Whether any market rent survey provider is a local real estate company or rental management company familiar with market rents in the area.

## acra-standard.appraisal_review.listed_property_appraisal_limits

**Purpose:** Determine whether a loan on a property listed for sale in the last six months meets the stated appraisal-based maximum LTV/CLTV and related loan characteristics.

1. Step 1 - Initial Document Review: Review the appraisal report and listing history for appraised value, the last date listed, and the lowest recent listing price.
2. Step 2 - Eligibility Verification: Determine whether the property has been listed for sale in the last six months, measured from the last date of being listed to the Application Date.
3. Step 3 - Validation and Verification: If the property meets the listing-period test, verify that the loan meets the stated characteristics: the property is not in default or otherwise delinquent on lien(s); for investment properties, the subject is occupied by a tenant and is not vacant; the loan qualifies as either ≥ 1.0 DSCR or 43% maximum DTI; a prepayment penalty of at least three (3) years is present unless the property is in a state that does not allow prepayment penalties; twenty-four (24) months of reserves are present, with cash-in-hand considered if otherwise consistent with the Guide; the term is fully amortizing and not interest only; maximum LTV / CLTV is 65% based on the lesser of appraised value or lowest recent listing price; no subordinate financing is present; and impounds are present.
4. Step 4 - Final Determination: Record whether the listing-period test and all applicable stated loan characteristics are met.

**Checks:**
- The property has been listed for sale in the last six months, measured from the last date of being listed to the Application Date.
- For a property meeting the listing-period test, the property is not in default or otherwise delinquent on lien(s).
- For an investment property meeting the listing-period test, the subject is occupied by a tenant and is not vacant.
- For a property meeting the listing-period test, the loan qualifies as either ≥ 1.0 DSCR or 43% maximum DTI.
- For a property meeting the listing-period test, a prepayment penalty of at least three (3) years is present unless the property is in a state that does not allow prepayment penalties.
- For a property meeting the listing-period test, twenty-four (24) months of reserves are present, and cash-in-hand is considered only if otherwise consistent with the Guide.
- For a property meeting the listing-period test, the loan has a fully amortizing term and is not interest only.
- For a property meeting the listing-period test, maximum LTV / CLTV is 65% based on the lesser of appraised value or lowest recent listing price.
- For a property meeting the listing-period test, no subordinate financing is present.
- For a property meeting the listing-period test, impounds are present.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_listed_for_sale, SubjectProperty.is_vacant, SubjectProperty.occupancy_subtype, SubjectProperty.appraised_value_usd, LoanCore.cltv_percent, LoanCore.is_interest_only_10_40, MortgageLoanInformation.is_interest_only, SubjectProperty.state, RatioSet.reserves_months, LoanCore.prepayment_penalty_structure
**Missing data:** The last date of being listed and the Application Date., Whether the property is in default or otherwise delinquent on lien(s)., Whether the loan qualifies as either ≥ 1.0 DSCR or 43% maximum DTI., Prepayment penalty duration and whether the property is in a state that does not allow prepayment penalties., Whether reserves meet twenty-four (24) months and whether cash-in-hand is otherwise consistent with the Guide., Whether the loan term is fully amortizing., Whether subordinate financing is present., Whether impounds are present., The lowest recent listing price and the LTV / CLTV calculated using the lesser of that price or appraised value.

## acra-standard.appraisal_review.property_type_appraisal_caps

**Purpose:** Determine whether the property type and transaction meet the printed CLTV limits and eligibility restriction.

1. Step 1 - Initial Document Review: Review the appraisal report for property type and any property-specific classification relevant to the printed caps.
2. Step 2 - Eligibility Verification: Identify the property type, transaction purpose, and whether the property is in Florida or LTV is above 80.00%.
3. Step 3 - Validation and Verification: Verify the applicable printed cap: Non-Warrantable Condo — 80% purchase, 75% refinance R/T, 75% refinance C/O, with -5% CLTV for Florida properties and Min DSCR: 1.0; Condotel / PUDtel — 75% purchase, 70% refinance R/T, 65% refinance C/O, with -5% CLTV for Florida properties and Min DSCR: 1.0; 2-4 Unit — Max CLTV: 80%; Manufactured Home — 65% purchase, 60% refinance R/T, 60% refinance C/O. Verify that above 80.00% LTV only SFR, Warrantable Condos outside of Florida, Townhome and PUD are eligible.
4. Step 4 - Final Determination: Record whether the applicable printed cap and above-80.00% LTV eligibility restriction are met.

**Checks:**
- For a Non-Warrantable Condo, CLTV does not exceed 80% for purchase, 75% for refinance R/T, or 75% for refinance C/O, with -5% CLTV for Florida properties; Min DSCR: 1.0.
- For a Condotel / PUDtel, CLTV does not exceed 75% for purchase, 70% for refinance R/T, or 65% for refinance C/O, with -5% CLTV for Florida properties; Min DSCR: 1.0.
- For a 2-4 Unit property, CLTV does not exceed Max CLTV: 80%.
- For a Manufactured Home, CLTV does not exceed 65% for purchase, 60% for refinance R/T, or 60% for refinance C/O.
- Above 80.00% LTV, the property is only SFR, Warrantable Condo outside of Florida, Townhome or PUD.

**Reads:** SubjectProperty.property_type, SubjectProperty.state, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** DSCR for a Non-Warrantable Condo or Condotel / PUDtel., Whether a Warrantable Condo is outside of Florida., The property type classification where it is not stated in the case fields or appraisal report.

## acra-standard.appraisal_review.required_rent_schedule

**Purpose:** Determine whether the required Form 1007 has been provided for a DSCR transaction or an applicable single-family transaction.

1. Step 1 - Initial Document Review: Review the appraisal report for a Form 1007 and identify the property type and transaction information.
2. Step 2 - Eligibility Verification: Determine whether the transaction is a DSCR transaction or a single-family transaction that meets one of the stated Form 1007 triggers.
3. Step 3 - Validation and Verification: Verify that a required Form 1007 is provided. If a Form 1007 is provided, verify that it is from the original appraiser or any state licensed appraiser.
4. Step 4 - Final Determination: Record whether the applicable Form 1007 requirement is met.

**Checks:**
- A Form 1007 is provided for every DSCR transaction.
- For a single-family property, a Form 1007 is provided if the file is a DSCR qualifying file, the transaction is a lease-option purchase where the required down payment is generated from excess monthly rent contributions, or proposed rental income is being used to qualify.
- A provided Form 1007 is from the original appraiser or any state licensed appraiser.

**Reads:** SubjectProperty.property_type, LoanCore.dscr_qualification_method
**Missing data:** Whether the transaction is a DSCR transaction., Whether the file is a DSCR qualifying file., Whether a lease-option purchase down payment is generated from excess monthly rent contributions., Whether proposed rental income is being used to qualify., The appraiser's licensing status, if not stated in the appraisal report.

## acra-standard.appraisal_review.rural_or_unique_property_limits

**Purpose:** Determine whether a rural or unique property meets the stated maximum CLTV and minimum FICO and DSCR requirements, and identify when marketing time or functionality may require a further LTV reduction.

1. Step 1 - Initial Document Review: Review the appraisal report for rural or unique property characteristics, marketing time, and functionality.
2. Step 2 - Eligibility Verification: Determine whether the property is rural or unique and identify the transaction purpose.
3. Step 3 - Validation and Verification: Verify the applicable maximum CLTV, minimum FICO 700, and minimum DSCR 1.00. If marketing time is excessive or the property exhibits unusual, inadequate or peculiar functionality, determine whether LTV may be further reduced.
4. Step 4 - Final Determination: Record whether the applicable stated limits are met and whether a further LTV reduction is required.

**Checks:**
- For a rural or unique property, CLTV does not exceed 80% for purchase, 75% for refinance — rate & term, or 70% for refinance — cash-out, as applicable.
- For a rural or unique property, FICO is at least 700.
- For a rural or unique property, DSCR is at least 1.00.
- If marketing time is excessive or the property exhibits unusual, inadequate or peculiar functionality, any further LTV reduction required by the review is applied.

**Reads:** SubjectProperty.is_rural, SubjectProperty.state, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Whether the property is unique., Marketing time and whether it is excessive., Whether the property exhibits unusual, inadequate or peculiar functionality., FICO score., DSCR., Whether a further LTV reduction is required.

## acra-standard.appraisal_review.short_term_rental_appraisal_form

**Purpose:** Determine whether an STRpro or similar appraisal form is acceptable as a replacement to a Form 1007 for a property occupied as a short-term rental.

1. Step 1 - Initial Document Review: Review the appraisal report for the appraisal form used and its signature.
2. Step 2 - Eligibility Verification: Determine whether the property is occupied as a short-term rental.
3. Step 3 - Validation and Verification: If an STRpro or similar form is used as a replacement to a Form 1007, verify that it is signed by an appropriately licensed appraiser.
4. Step 4 - Final Determination: Record whether the stated short-term-rental appraisal-form requirement is met.

**Checks:**
- For a property occupied as a short-term rental, an STRpro or similar appraisal form used as a replacement to a Form 1007 is signed by an appropriately licensed appraiser.

**Reads:** SubjectProperty.property_type
**Missing data:** Whether the property is occupied as a short-term rental., Whether the appraisal form is an STRpro or similar form., The appraiser's licensing status, if not stated in the appraisal report.

## acra-standard.appraisal_review.vacant_purchase_rent_appraisal

**Purpose:** Determine whether qualifying rents for a vacant property purchase are taken from the applicable Form 1007 or Form 1025 appraisal report.

1. Step 1 - Initial Document Review: Review the appraisal report for a Form 1007 or Form 1025 and the stated qualifying rents.
2. Step 2 - Eligibility Verification: Determine whether the property is vacant and is being purchased.
3. Step 3 - Validation and Verification: Verify that qualifying rents are taken from the Form 1007 or Form 1025 appraisal report, as applicable.
4. Step 4 - Final Determination: Record whether the stated vacant-purchase qualifying-rent requirement is met.

**Checks:**
- If a vacant property is being purchased, qualifying rents are taken from the Form 1007 or Form 1025 appraisal report, as applicable.

**Reads:** SubjectProperty.is_vacant, LoanCore.loan_purpose
**Missing data:** Whether the transaction is a purchase., Which appraisal form is applicable.

## acra-standard.asset_assessment.first_time_homebuyer_reserves

**Purpose:** Determine whether the stated reserve requirement is met for a first-time homebuyer.

1. Initial Document Review: Review the case record and reserves documentation.
2. Eligibility Verification: Determine whether the borrower is a first-time homebuyer.
3. Validation and Verification: If the trigger applies, verify minimum six months reserves (“Requires 6mos Reserves”).
4. Final Determination: Pass only if the applicable reserve requirement is met.

**Checks:**
- When the borrower is a first-time homebuyer, reserves are at least six months.

**Reads:** Borrower.is_first_time_homebuyer, RatioSet.reserves_months
**Missing data:** Acra confirmation requested on the payment basis where only “months” is stated and treatment of overlapping triggers (Q-07)

## acra-standard.asset_assessment.foreign_account_currency_verification

**Purpose:** Determine whether assets held in foreign accounts are verified in U.S. Dollar equivalency at the current exchange rate.

1. Initial Document Review: Review the account statement and the currency and amount of the assets held.
2. Eligibility Verification: Apply this requirement when assets are held in foreign accounts.
3. Validation and Verification: Verify the U.S. Dollar equivalency at the current exchange rate via www.xe.com or the Wall Street Journal conversion table.
4. Final Determination: Pass only if the required equivalency is verified.

**Checks:**
- Assets held in foreign accounts are verified in U.S. Dollar equivalency at the current exchange rate via www.xe.com or the Wall Street Journal conversion table.
**Missing data:** Whether the account is a foreign account, Account currency and asset amount, Current exchange rate from www.xe.com or the Wall Street Journal conversion table, U.S. Dollar equivalency

## acra-standard.asset_assessment.foreign_account_statement_translation

**Purpose:** Determine whether required translations are provided for foreign-account bank statements.

1. Initial Document Review: Review the language of the foreign-account bank statements.
2. Eligibility Verification: Identify statements in any language other than English.
3. Validation and Verification: Verify that each statement in a language other than English is translated into English.
4. Final Determination: Pass if all applicable statements are translated into English.

**Checks:**
- Bank statements in any language other than English are translated into English.
**Missing data:** Language of each bank statement, English translation of each statement in a language other than English

## acra-standard.asset_assessment.foreign_account_statements_and_seasoning

**Purpose:** Determine whether the required documentation is provided for funds in a foreign account.

1. Initial Document Review: Review the two (2) most recent statements for the account serving as the source of funds.
2. Eligibility Verification: Determine whether the funds are seasoned for a minimum of sixty (60) days.
3. Validation and Verification: If the funds are not seasoned for a minimum of sixty (60) days, review a letter of explanation and information comprising a sixty (60) day chain of funds.
4. Final Determination: Pass only if the statements are provided and any required explanation and chain of funds are documented.

**Checks:**
- A copy of the two (2) most recent statements of the account is provided.
- If funds are not seasoned a minimum of sixty (60) days, a letter of explanation and information to comprise a sixty (60) day chain of funds are provided.
**Missing data:** Account seasoning period, Letter of explanation when funds are not seasoned a minimum of sixty (60) days, Information comprising a sixty (60) day chain of funds when required

## acra-standard.asset_assessment.foreign_funds_repatriation

**Purpose:** Determine whether the stated repatriation timing requirement is met for funds held in a foreign bank / currency.

1. Initial Document Review: Review account and repatriation documentation and the Closing date.
2. Eligibility Verification: Determine whether funds are held in a foreign bank / currency and whether the borrower is a Foreign National.
3. Validation and Verification: Verify repatriation at minimum three (3) business days prior to Closing where the requirement applies.
4. Final Determination: Determine whether the applicable repatriation requirement is met; obtain Acra confirmation on the stated scope and evidence question where needed.

**Checks:**
- Where applicable, funds held in a foreign bank / currency are repatriated at minimum three (3) business days prior to Closing.

**Reads:** Borrower.citizenship_status
**Missing data:** Whether the borrower holds funds abroad and whether the borrower is a Foreign National, Acra confirmation on whether the repatriation requirement applies to any borrower holding funds abroad or only to Foreign Nationals, Acra confirmation on what evidence applies, Repatriation date, Closing date

## acra-standard.asset_assessment.foreign_national_funds_seasoning

**Purpose:** Determine whether a Foreign National documents the required minimum seasoning of funds.

1. Initial Document Review: Review the borrower's status and the documentation establishing the seasoning of funds.
2. Eligibility Verification: Apply this requirement to Foreign Nationals regardless of LTV / CLTV.
3. Validation and Verification: Verify documentation of a minimum of 60 days seasoning.
4. Final Determination: Pass only if the minimum seasoning is documented.

**Checks:**
- A Foreign National documents a minimum of 60 days seasoning, regardless of LTV / CLTV.

**Reads:** Borrower.citizenship_status
**Missing data:** Whether the borrower is a Foreign National, Documentation of at least 60 days seasoning

## acra-standard.asset_assessment.funds_documentation_minimum

**Purpose:** Determine whether all transactions have a minimum of 30-days documentation.

1. Initial Document Review: Review the available documentation of funds.
2. Eligibility Verification: Apply the minimum documentation requirement to all transactions.
3. Validation and Verification: Verify that documentation covers a minimum of 30-days.
4. Final Determination: Pass only if the minimum documentation is provided.

**Checks:**
- The transaction has a minimum of 30-days documentation.
**Missing data:** Documentation covering a minimum of 30-days

## acra-standard.asset_assessment.funds_on_deposit_before_closing

**Purpose:** Determine whether sufficient funds to close are on deposit with the Escrow / Closing Agent at least three (3) business days before closing, counting Saturdays.

1. Initial Document Review: Review evidence of funds to close, the deposit, and the closing date.
2. Eligibility Verification: Determine the amount of funds required to close and the applicable closing date.
3. Validation and Verification: Verify that sufficient funds are on deposit with the Escrow / Closing Agent at least three (3) business days prior to closing, including Saturdays in the calculation.
4. Final Determination: Pass only if both sufficiency and timing are verified.

**Checks:**
- Sufficient funds to close are on deposit with the Escrow / Closing Agent at least three (3) business days prior to the closing date, including Saturdays in the calculation.
**Missing data:** Funds required to close, Amount deposited with the Escrow / Closing Agent, Deposit date, Closing date, Business-day calculation including Saturdays

## acra-standard.asset_assessment.funds_seasoning_verification_trigger

**Purpose:** Identify loans for which verification of seasoning of funds to close is required.

1. Initial Document Review: Review the CLTV, transaction type, and funds to close.
2. Eligibility Verification: Apply the stated trigger for consumer transactions and business purpose loans.
3. Validation and Verification: Determine whether the loan is over 70% CLTV and whether the applicable transaction and funds-to-close conditions are met.
4. Final Determination: Record whether verification of seasoning of funds to close is required.

**Checks:**
- For a consumer transaction, the loan is over 70% CLTV.
- For a business purpose loan, funds to close are over $50,000 and the loan is over 70% CLTV.

**Reads:** LoanCore.cltv_percent, LoanCore.loan_purpose
**Missing data:** Whether the loan is a consumer transaction or a business purpose loan, Funds to close, Acra confirmation requested on whether any loan on this program is a consumer transaction (Q-27)

## acra-standard.asset_assessment.listed_property_reserves

**Purpose:** Determine whether the stated reserve requirement is met for a property listed for sale within six months.

1. Initial Document Review: Review listing history and documentation of reserves or cash-in-hand.
2. Eligibility Verification: Determine whether the property was listed for sale within six months.
3. Validation and Verification: Verify Twenty-four (24) months of reserves; assess cash-in-hand only if otherwise consistent with the Guide.
4. Final Determination: Pass only if the applicable reserve requirement is met.

**Checks:**
- When the property was listed for sale within six months, Twenty-four (24) months of reserves are verified, with cash-in-hand considered only if otherwise consistent with the Guide.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
**Missing data:** Whether cash-in-hand is otherwise consistent with the Guide, Acra confirmation requested on treatment of overlapping triggers (Q-07)

## acra-standard.asset_assessment.loan_amount_limits

**Purpose:** Determine whether the loan amount meets STD-1.10.

1. Initial Document Review: Review the loan amount in the case record.
2. Eligibility Verification: Apply the minimum, maximum, and increment requirements to the loan amount.
3. Validation and Verification: Compare the loan amount with each stated requirement.
4. Final Determination: Pass only if all three requirements are met.

**Checks:**
- The loan amount is at least $100,000.
- The loan amount is no more than $3,000,000.
- The loan amount is in $50 increments.

**Reads:** LoanCore.total_loan_amount_usd

## acra-standard.asset_assessment.own_funds_contribution

**Purpose:** Determine whether the applicant contributes the required own funds when gift funds, an investment property, or a second home is involved.

1. Initial Document Review: Review the transaction details and documentation of the applicant's funds and any gift funds.
2. Eligibility Verification: Apply this requirement to gift funds, investment property, or second homes.
3. Validation and Verification: Verify that the applicant's own sourced and seasoned funds contributed to the transaction are at least 10% of the purchase price.
4. Final Determination: Pass only if the minimum own-funds contribution is verified.

**Checks:**
- For a transaction involving gift funds, an investment property, or a second home, the applicant contributes own sourced and seasoned funds of at least 10% of the purchase price.

**Reads:** LoanCore.loan_purpose, SubjectProperty.occupancy_subtype
**Missing data:** Whether the transaction involves gift funds, an investment property, or a second home, Purchase price, Amount of the applicant's own funds contributed, Evidence that the applicant's funds are sourced and seasoned, Seller's Guide gift-fund documentation requirements (Appendix B)

## acra-standard.asset_assessment.rent_loss_insurance_reserves

**Purpose:** Determine whether the stated reserve requirement is met when required rent loss insurance cannot be obtained.

1. Initial Document Review: Review the rent loss insurance requirement, evidence of coverage obtained or not obtained, and reserves documentation.
2. Eligibility Verification: Determine whether rent loss insurance is required but cannot be obtained.
3. Validation and Verification: Verify Two (2) months reserves for every one (1) month of coverage not provided.
4. Final Determination: Pass only if the stated reserves are verified; determine whether substituted reserves are additional only as directed by Acra confirmation.

**Checks:**
- When rent loss insurance is required but cannot be obtained, reserves are Two (2) months for every one (1) month of coverage not provided.

**Reads:** RatioSet.reserves_months
**Missing data:** Whether rent loss insurance is required, Whether the insurance cannot be obtained, Number of months of coverage not provided, Documentation of the corresponding reserves, Acra confirmation requested on whether reserves substituted for rent loss insurance are additional (Q-07)

## acra-standard.asset_assessment.reserves_for_fico_below_620

**Purpose:** Determine whether the stated reserve requirement is met for FICO < 620.

1. Initial Document Review: Review credit and reserves documentation.
2. Eligibility Verification: Determine whether FICO < 620.
3. Validation and Verification: If the trigger applies, verify 12 Months reserves.
4. Final Determination: Pass only if the applicable reserve requirement is verified.

**Checks:**
- When FICO < 620, 12 Months reserves are verified.

**Reads:** CreditReport.representative_score, RatioSet.reserves_months
**Missing data:** FICO score, Documentation of 12 Months reserves, Acra confirmation requested on the payment basis where only “months” is stated and treatment of overlapping triggers (Q-07)

## acra-standard.asset_assessment.reserves_for_ltv_over_80_00

**Purpose:** Determine whether the stated reserve requirement is met for LTV > 80.00%.

1. Initial Document Review: Review the LTV and reserves documentation.
2. Eligibility Verification: Determine whether LTV > 80.00%.
3. Validation and Verification: If the trigger applies, verify 6 months PITIA reserves.
4. Final Determination: Pass only if the applicable reserve requirement is verified.

**Checks:**
- When LTV > 80.00%, 6 months PITIA reserves are verified.

**Reads:** LoanCore.cltv_percent, RatioSet.reserves_months
**Missing data:** LTV, PITIA amount and documentation of 6 months PITIA reserves, Acra confirmation requested on the base requirement where no trigger applies, the payment basis where only “months” is stated, and treatment of overlapping triggers (Q-07)

## acra-standard.asset_assessment.seller_concession_cap

**Purpose:** Determine whether seller concessions and other contributions are limited to 3% of the sale price.

1. Initial Document Review: Review the reported seller concession and other contributions and the sale price.
2. Eligibility Verification: Apply the 3% limit to the sale price.
3. Validation and Verification: Compare the total seller concession and other contributions with 3% of the sale price.
4. Final Determination: Pass only if the limit is met.

**Checks:**
- Seller concessions and other contributions do not exceed 3% of the sale price.

**Reads:** LoanCore.seller_concession_percent
**Missing data:** Sale price, Total seller concession and other contributions

## acra-standard.asset_assessment.source_account_verification

**Purpose:** Determine whether a source account that must be verified is supported by an allowed form of verification.

1. Initial Document Review: Review whether the account serving as the source of funds must be verified.
2. Eligibility Verification: Apply this requirement to accounts serving as the source of funds that must be verified.
3. Validation and Verification: Verify the account with either a copy of the borrower's bank statement(s) for the most recent month(s), or a VOD reflecting a current and average balance for the most recent month(s).
4. Final Determination: Pass if either stated verification method is provided for the most recent month(s).

**Checks:**
- A source account that must be verified is supported by a bank statement for the most recent month(s) or a VOD reflecting a current and average balance for the most recent month(s).
**Missing data:** Whether the account must be verified, The most recent month(s) of bank statements or a VOD showing current and average balances for the most recent month(s)

## acra-standard.asset_assessment.tenant_rent_receipt_reserves

**Purpose:** Determine whether the stated reserve requirement is met when the trigger conditions apply.

1. Initial Document Review: Review the subject's occupancy, mortgage payment history, rent receipts, and reserves documentation.
2. Eligibility Verification: Determine whether there is forbearance or mortgage lates in the last 12 months, the subject is tenant-occupied, and the prior two months' rent was not received timely.
3. Validation and Verification: If all trigger conditions apply, verify 12 months of the subject's payment in reserve, which may be from the transaction's cash-in-hand.
4. Final Determination: Pass only if the applicable reserve amount is verified.

**Checks:**
- When there is forbearance or mortgage lates in the last 12 months, the subject is tenant-occupied, and the prior two months' rent was not received timely, 12 months of the subject's payment are in reserve, which may be from the transaction's cash-in-hand.

**Reads:** SubjectProperty.has_current_lease, CreditReport.mortgage_0x30x24, RatioSet.reserves_months
**Missing data:** Whether there was forbearance or a mortgage late in the last 12 months, Whether the prior two months' rent was received timely, Subject's payment amount, Whether cash-in-hand is from the transaction, Acra confirmation requested on the payment basis where only “months” is stated and treatment of overlapping triggers (Q-07)

## acra-standard.asset_assessment.vacant_cash_out_refinance_reserves

**Purpose:** Determine whether the stated reserve requirement is met for this vacant-property refinance trigger.

1. Initial Document Review: Review occupancy, refinance type, and reserves documentation.
2. Eligibility Verification: Determine whether the property is vacant and the transaction is a cash-out refinance.
3. Validation and Verification: If the trigger applies, verify 6 months reserves.
4. Final Determination: Pass only if the applicable reserve requirement is verified.

**Checks:**
- For a vacant property with a cash-out refinance, 6 months reserves are verified.

**Reads:** SubjectProperty.is_vacant, LoanCore.loan_purpose, RatioSet.reserves_months
**Missing data:** Whether the refinance is cash-out, Acra confirmation requested on the payment basis where only “months” is stated and treatment of overlapping triggers (Q-07)

## acra-standard.asset_assessment.vacant_rate_and_term_refinance_reserves

**Purpose:** Determine whether the stated reserve requirement is met for this vacant-property refinance trigger.

1. Initial Document Review: Review occupancy, refinance type, and reserves documentation.
2. Eligibility Verification: Determine whether the property is vacant and the transaction is a rate & term refinance.
3. Validation and Verification: If the trigger applies, verify minimum six months reserves.
4. Final Determination: Pass only if the applicable reserve requirement is verified.

**Checks:**
- For a vacant property with a rate & term refinance, reserves are at least six months.

**Reads:** SubjectProperty.is_vacant, LoanCore.loan_purpose, RatioSet.reserves_months
**Missing data:** Whether the refinance is rate & term, Acra confirmation requested on the payment basis where only “months” is stated and treatment of overlapping triggers (Q-07)

## acra-standard.compliance_and_closing.entity_documentation

**Purpose:** Determine whether the required entity documents are complete and meet the stated requirements.

1. Initial Document Review: Review the entity documents and identification for the required formation, governance, ownership, qualification, tax-identification, and transaction-authorization documents.
2. Eligibility Verification: Verify that the documents required for the entity type are provided, complete, legible, and include the contents specified by the policy.
3. Validation and Verification: Verify that entity names match identification or that a letter of explanation addresses a discrepancy; verify that the Certificate of Good Standing or equivalent is valid within ninety (90) days of the closing date; and review any applicable foreign qualification, EIN exception, or lost-stock-certificate documentation.
4. Final Determination: Determine whether the required entity documentation meets the stated requirements.

**Checks:**
- All required entity documentation applicable to the entity type is provided and meets the stated requirements.
- The entity documents state whether the entity is member or manager managed, authorize borrowing money and entering into contracts for mortgage assets, and designate signers, where those requirements apply.
- Ownership documentation accounts for the ownership interests as required for the entity type.
- The Certificate of Good Standing or equivalent is valid within ninety (90) days of the closing date.
- A Unanimous Written Consent / Board Resolution signed by all members authorizes the transaction with Acra Lending and identifies who is authorized to sign the loan documents on behalf of and to bind the entity.

**Reads:** Borrower.entity_type, Borrower.entity_documents_complete, Borrower.is_entity_borrower_1
**Missing data:** Complete, legible Certificate of Formation / Articles of Organization and all amendments, Complete, legible Operating Agreement with referenced exhibits, or Bylaws, and all amendments, Ownership-interest evidence applicable to the entity type, Stock certificates or stock ledger, and Affidavit of Lost Stock Certificate if required, For the stated S-corporation or Partnership circumstance, K-1 statements and CPA or Tax Preparer letter, Identification, Letter of explanation for any name discrepancy, Certificate of Good Standing or equivalent, Certificate of Foreign Qualification or other qualification, if applicable, IRS Form SS4, Federal Taxpayer Identification Number (TIN), or EIN issuance letter, Acra Legal Department review and letter of explanation for an EIN exception request, if applicable, Unanimous Written Consent / Board Resolution, Power of Attorney for an attorney in fact executing a personal guarantee, if applicable, Additional supporting documentation required by Legal, if any

## acra-standard.compliance_and_closing.foreign_account_funds

**Purpose:** Determine whether foreign-account funds are documented and available as required.

1. Initial Document Review: Review the two (2) most recent statements for the account and the evidence of funds to close.
2. Eligibility Verification: Verify U.S. Dollar equivalency at the current exchange rate for assets held in foreign accounts.
3. Validation and Verification: Verify that funds are seasoned a minimum of sixty (60) days or, if they are not, that a letter of explanation and information comprising a sixty (60) day chain of funds are provided; verify that statements in a language other than English are translated into English; and verify the required deposit or repatriation timing where applicable.
4. Final Determination: Determine whether the foreign-account funds meet the stated documentation and timing requirements.

**Checks:**
- Foreign-account assets are verified in U.S. Dollar equivalency at the current exchange rate via www.xe.com or the Wall Street Journal conversion table.
- A copy of the two (2) most recent statements of the account is provided.
- If funds are not seasoned a minimum of sixty (60) days, a letter of explanation and information to comprise a sixty (60) day chain of funds are provided.
- Bank statements in a language other than English are translated into English.
- Sufficient funds to close are on deposit with the Escrow / Closing Agent at least three (3) business days, including Saturdays for this calculation, prior to any closing date.
- Funds held in a foreign bank / currency are repatriated at minimum three (3) business days prior to Closing where the stated requirement applies.

**Reads:** Borrower.citizenship_status, LoanCore.cltv_percent
**Missing data:** Current exchange-rate conversion from www.xe.com or the Wall Street Journal conversion table, Two (2) most recent account statements, Letter of explanation and sixty (60) day chain of funds, if required, English translations of statements, if required, Closing date and evidence of funds deposited with the Escrow / Closing Agent, Evidence of repatriation and the applicable borrower status

## acra-standard.compliance_and_closing.foreign_national_closing_documents

**Purpose:** Determine whether the stated foreign-national closing requirements are met.

1. Initial Document Review: Review the current Passport, Visa, or ITIN; executed W-8 (BEN) IRS form; and title and closing agent evidence.
2. Eligibility Verification: Verify that the loan closes with a title and closing agent approved and / or vetted by Acra.
3. Validation and Verification: Review any Power of Attorney for conformity with Acra requirements and title-company acceptability; review any documents signed outside of the U.S. for the applicable notarization, acknowledgment, seal or apostille, and title-company acceptance requirements.
4. Final Determination: Determine whether the stated closing-document requirements are met.

**Checks:**
- A copy of a current Passport, Visa, or ITIN is provided.
- The loan closes with a title and closing agent approved and / or vetted by Acra.
- Any Power of Attorney conforms to Acra requirements and is acceptable to the title company.
- An executed W-8 (BEN) IRS form is provided.
- Documents signed outside of the U.S. meet the applicable acknowledgment and title-company acceptance requirements stated in the policy.

**Reads:** Borrower.citizenship_status
**Missing data:** Current Passport, Visa, or ITIN, Evidence that the title and closing agent is approved and / or vetted by Acra, Power of Attorney and evidence of title-company acceptance, if applicable, Executed W-8 (BEN) IRS form, Executed documents signed outside of the U.S., Embassy or consular acknowledgment certificate and seal, or authorized notary acknowledgment and English apostille, as applicable, Title-company acceptance

## acra-standard.compliance_and_closing.gift_funds_contribution

**Purpose:** Determine whether applicant(s) contribute the required portion of their own sourced and seasoned funds to the transaction.

1. Initial Document Review: Review the purchase-price and funds-to-close evidence.
2. Eligibility Verification: Determine whether the transaction is for an investment property or second home and includes gift funds.
3. Validation and Verification: Verify that applicant(s) contribute a portion of their own sourced and seasoned funds to the transaction at a minimum of 10% of the purchase price; review gift documentation requirements in the Seller's Guide gift-fund section.
4. Final Determination: Determine whether the stated gift-funds contribution requirement is met.

**Checks:**
- Applicant(s) contribute a portion of their own sourced and seasoned funds to the transaction at a minimum of 10% of the purchase price.

**Reads:** SubjectProperty.occupancy_subtype, LoanCore.loan_purpose
**Missing data:** Purchase price, Evidence of applicant(s)’ own sourced and seasoned funds, Gift-fund documentation requirements in the Seller's Guide gift-fund section

## acra-standard.compliance_and_closing.investment_occupancy

**Purpose:** Determine whether the subject property meets the stated investment-property definition.

1. Initial Document Review: Review the loan application and lease evidence for the subject property’s occupancy and use.
2. Eligibility Verification: Verify that the property is a one- to four-unit residential dwelling or a unit in a condominium complex or a PUD, is owned by an individual who does not occupy it, and is leased and occupied as a principal year-round residence to individuals other than the owner.
3. Validation and Verification: Confirm the occupancy and lease information against the reviewed evidence.
4. Final Determination: Determine whether the investment-property occupancy requirements are met.

**Checks:**
- The subject property is investment property and is not owner-occupied.
- The property meets the stated investment-property definition.

**Reads:** SubjectProperty.number_of_units, SubjectProperty.property_type, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant
**Missing data:** Evidence that the property is a unit in a condominium complex or a PUD, if applicable, Evidence of the owner’s identity and non-occupancy, Evidence that the tenant occupies the dwelling as a principal year-round residence

## acra-standard.compliance_and_closing.listed_property_amortization

**Purpose:** Determine whether the loan meets the listed-property amortization requirement.

1. Initial Document Review: Review the loan terms.
2. Eligibility Verification: Determine whether the property is subject to the listed-for-sale requirements.
3. Validation and Verification: Verify that the loan has a fully amortizing term and is not interest only.
4. Final Determination: Determine whether the listed-property amortization requirement is met.

**Checks:**
- The loan has a fully amortizing term.
- The loan is not interest only.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, MortgageLoanInformation.is_interest_only
**Missing data:** Loan term and amortization schedule

## acra-standard.compliance_and_closing.listed_property_maximum_cltv

**Purpose:** Determine whether the listed-property loan’s maximum LTV / CLTV requirement is met.

1. Initial Document Review: Review the appraisal and listing history.
2. Eligibility Verification: Determine whether the property is subject to the listed-for-sale requirements.
3. Validation and Verification: Determine the lesser of the appraised value and the lowest recent listing price and verify that the maximum LTV / CLTV is 65% based on that value.
4. Final Determination: Determine whether the listed-property maximum LTV / CLTV requirement is met.

**Checks:**
- The maximum LTV / CLTV is 65% based on the lesser of the appraised value or the lowest recent listing price.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.appraised_value_usd, LoanCore.cltv_percent
**Missing data:** Lowest recent listing price, Evidence supporting the LTV / CLTV calculation using the lesser of the appraised value or lowest recent listing price

## acra-standard.compliance_and_closing.listed_property_reserves

**Purpose:** Determine whether the required reserves are documented for a listed property.

1. Initial Document Review: Review the evidence of reserves.
2. Eligibility Verification: Determine whether the property is subject to the listed-for-sale requirements.
3. Validation and Verification: Verify that twenty-four (24) months of reserves are available.
4. Final Determination: Determine whether the listed-property reserve requirement is met.

**Checks:**
- Twenty-four (24) months of reserves are available.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
**Missing data:** Evidence supporting the reserve-month amount

## acra-standard.compliance_and_closing.listed_property_tenant_occupancy

**Purpose:** Determine whether an investment property listed for sale is occupied by a tenant and is not vacant.

1. Initial Document Review: Review the listing history and lease evidence.
2. Eligibility Verification: Determine whether the property has been listed for sale in the last six months, measured from the last date of being listed to the Application Date.
3. Validation and Verification: For an investment property subject to the listed-property requirements, verify that the subject is occupied by a tenant and is not vacant.
4. Final Determination: Determine whether the listed-property tenant-occupancy requirement is met.

**Checks:**
- The property has been listed for sale in the last six months, measured from the last date of being listed to the Application Date.
- If the listed property is an investment property, the subject is occupied by a tenant and is not vacant.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_vacant, SubjectProperty.has_current_lease, SubjectProperty.occupancy_subtype
**Missing data:** Last date the property was listed for sale, Application Date, Evidence that the tenant occupies the subject property

## acra-standard.credit_review_analysis.bankruptcy_and_foreclosure_seasoning_limits

**Purpose:** Check the printed maximum CLTV or ineligible result for the stated bankruptcy and foreclosure seasoning bands.

1. Step 1 - Initial Document Review: Review the loan application and credit information for bankruptcy or foreclosure history, seasoning, loan purpose, and CLTV.
2. Step 2 - Eligibility Verification: Apply this provision when the borrower has a bankruptcy or foreclosure.
3. Step 3 - Validation and Verification: Compare seasoning and loan purpose with the printed table: ≥ 36 Mo, No Restrictions; 24-35 Mo, 80% purchase / 75% refinance; 12-23 Mo, 65% purchase / 65% refinance; < 12 Mo, Ineligible.
4. Step 4 - Final Determination: Record whether the applicable printed restriction is met.

**Checks:**
- For seasoning ≥ 36 Mo, the table states No Restrictions.
- For seasoning 24-35 Mo, CLTV is no more than 80% for purchase or 75% for refinance — rate & term and cash-out.
- For seasoning 12-23 Mo, CLTV is no more than 65% for purchase or 65% for refinance — rate & term and cash-out.
- For seasoning < 12 Mo, the case is Ineligible.

**Reads:** Borrower.has_bankruptcy_or_foreclosure, Borrower.months_since_bankruptcy_or_foreclosure, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Bankruptcy or foreclosure seasoning as measured under Acra’s labels; definitions and measurement are subject to Acra confirmation → Q-05

## acra-standard.credit_review_analysis.citizenship_type_eligibility

**Purpose:** Determine whether the borrower’s citizenship type is eligible under STD-4.1.

1. Step 1 - Initial Document Review: Review the loan application for the borrower’s citizenship type.
2. Step 2 - Eligibility Verification: Compare the citizenship type with the types eligible under STD-4.1.
3. Step 3 - Validation and Verification: Verify the stated citizenship type from the application information.
4. Step 4 - Final Determination: Record whether the citizenship type is eligible.

**Checks:**
- Borrower citizenship type is US Citizen, Permanent Resident, Non-Permanent Resident, Foreign National, or ITIN.

**Reads:** Borrower.citizenship_status
**Missing data:** Borrower citizenship type as documented

## acra-standard.credit_review_analysis.credit_score_count_requirements

**Purpose:** Verify the applicable credit score-count requirement: 3 repositories, or the stated alternatives for applicants with 2 or fewer scores.

1. Step 1 - Initial Document Review: Review the credit report for the number of repository scores and the reported tradelines and their histories.
2. Step 2 - Eligibility Verification: For 3 repositories, apply the no-tradeline-overlay provision. For 2 or fewer scores, verify either 2 tradelines & 24 month history, or 3 tradelines & 12 month history.
3. Step 3 - Validation and Verification: Verify the score count and, where applicable, the tradeline counts and histories from the credit report.
4. Step 4 - Final Determination: Record whether the applicable score-count requirement is met.

**Checks:**
- If applicants have scores from 3 repositories, the score-count requirement is acceptable with no tradeline overlay.
- If applicants have 2 or fewer scores, they have 2 tradelines & 24 month history, or 3 tradelines & 12 month history.

**Reads:** CreditReport.score_count, CreditReport.tradelines_meet_requirement
**Missing data:** Repository score count and tradeline history details, if not held in the case fields

## acra-standard.credit_review_analysis.escrow_waiver_eligibility

**Purpose:** Determine whether the case meets the requirements printed for an escrow waiver.

1. Step 1 - Initial Document Review: Review the loan application and credit report for the waiver request, loan amount, CLTV, FICO, mortgage history, and citizenship type.
2. Step 2 - Eligibility Verification: Apply the printed escrow-waiver requirements to a requested waiver.
3. Step 3 - Validation and Verification: Verify each requirement: maximum loan amount $1.5M; maximum CLTV 80%; minimum FICO 700; mortgage history no worse than 0x30x24; Foreign National ineligible.
4. Step 4 - Final Determination: Record whether the waiver requirements are met. Separately note that interaction with impound requirements is referred for Acra confirmation → Q-15.

**Checks:**
- Loan amount is no more than $1.5M.
- CLTV is no more than 80%.
- FICO is at least 700.
- Mortgage history is no worse than 0x30x24.
- The borrower is not a Foreign National.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.cltv_percent, CreditReport.representative_score, CreditReport.mortgage_0x30x24, Borrower.citizenship_status, LoanCore.is_escrow_waived
**Missing data:** Whether an impound requirement interacts with an otherwise eligible waiver; Acra confirmation requested → Q-15

## acra-standard.credit_review_analysis.first_time_homebuyer_status

**Purpose:** Determine whether all Applicants have never previously owned a home (real property).

1. Step 1 - Initial Document Review: Review the loan application for information about each Applicant’s prior homeownership.
2. Step 2 - Eligibility Verification: Determine whether every Applicant has never previously owned a home (real property).
3. Step 3 - Validation and Verification: Verify the stated homeownership history using available application information.
4. Step 4 - Final Determination: Record whether the application meets Acra’s definition of a First Time Home Buyer.

**Checks:**
- Every Applicant has never previously owned a home (real property).

**Reads:** Borrower.is_first_time_homebuyer
**Missing data:** Each Applicant’s prior homeownership history

## acra-standard.credit_review_analysis.foreign_national_cltv_limit

**Purpose:** Check the Foreign National maximum CLTV limit: 70% for purchase and 65% for refinance — rate & term and cash-out.

1. Step 1 - Initial Document Review: Review the loan application for citizenship type, loan purpose, and the stated primary residence location.
2. Step 2 - Eligibility Verification: Apply this limit when the borrower is a Foreign National; the printed definition is borrowers whose Primary Residence is not located in the United States of America.
3. Step 3 - Validation and Verification: Compare the applicable maximum CLTV with the loan’s CLTV.
4. Step 4 - Final Determination: Record whether the applicable Foreign National maximum CLTV is met.

**Checks:**
- For a Foreign National, CLTV is no more than 70% for purchase or 65% for refinance — rate & term and cash-out.

**Reads:** Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Whether the borrower’s Primary Residence is located in the United States of America

## acra-standard.credit_review_analysis.interest_only_loan_amount_and_fico

**Purpose:** Check that an interest-only loan meets the STD-2.7 loan amount and FICO limits.

1. Step 1 - Initial Document Review: Review the loan application and credit report for interest-only status, loan amount, and FICO.
2. Step 2 - Eligibility Verification: Apply the limits to an interest-only loan.
3. Step 3 - Validation and Verification: Compare the loan amount and FICO with the printed limits.
4. Step 4 - Final Determination: Record whether all three limits are met.

**Checks:**
- For an interest-only loan, loan amount is at least $250,000.
- For an interest-only loan, loan amount is no more than $3,000,000.
- For an interest-only loan, FICO is at least 640.

**Reads:** MortgageLoanInformation.is_interest_only, LoanCore.total_loan_amount_usd, CreditReport.representative_score
**Missing data:** Decisioning FICO, if not held in the case fields

## acra-standard.credit_review_analysis.itin_loan_amount_and_fico_limits

**Purpose:** Check the ITIN maximum loan amount of $1.0M and minimum FICO 640.

1. Step 1 - Initial Document Review: Review the loan application and credit report for ITIN status, loan amount, and FICO information.
2. Step 2 - Eligibility Verification: Apply these limits to an ITIN borrower, subject to the source’s stated unresolved eligibility questions for US-resident ITIN holders.
3. Step 3 - Validation and Verification: Compare the loan amount and FICO with the printed limits.
4. Step 4 - Final Determination: Record whether the maximum loan amount and minimum FICO are met.

**Checks:**
- For an ITIN borrower, loan amount is no more than $1.0M.
- For an ITIN borrower, FICO is at least 640.

**Reads:** Borrower.citizenship_status, LoanCore.total_loan_amount_usd, CreditReport.representative_score
**Missing data:** Decisioning FICO, if not held in the case fields, Whether a US-resident ITIN holder is eligible; Acra confirmation requested → Q-03

## acra-standard.credit_review_analysis.loan_amount_below_200_000_cltv_limit

**Purpose:** Check the maximum CLTV of 80% for purchase and 75% for refinance — rate & term and cash-out when loan amount is below $200,000.

1. Step 1 - Initial Document Review: Review the loan application for loan amount and purpose.
2. Step 2 - Eligibility Verification: Apply this limit when loan amount is below $200,000.
3. Step 3 - Validation and Verification: Compare CLTV with the maximum for the loan purpose.
4. Step 4 - Final Determination: Record whether the applicable maximum CLTV is met.

**Checks:**
- If loan amount is below $200,000, CLTV is no more than 80% for purchase or 75% for refinance — rate & term and cash-out.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.loan_purpose, LoanCore.cltv_percent

## acra-standard.credit_review_analysis.loan_amount_over_2_000_000_dscr

**Purpose:** Check that a loan amount over $2,000,000 has 1.0 or greater DSCR.

1. Step 1 - Initial Document Review: Review the loan application and underwriting information for loan amount and DSCR.
2. Step 2 - Eligibility Verification: Apply this requirement when loan amount is over $2,000,000.
3. Step 3 - Validation and Verification: Verify the DSCR and compare it with 1.0.
4. Step 4 - Final Determination: Record whether the minimum DSCR is met.

**Checks:**
- If loan amount is over $2,000,000, DSCR is 1.0 or greater.

**Reads:** LoanCore.total_loan_amount_usd
**Missing data:** DSCR

## acra-standard.credit_review_analysis.non_permanent_resident_proof

**Purpose:** Verify the legal-residency proof required for a Non-Permanent Resident.

1. Step 1 - Initial Document Review: Review the provided proof of legal residency, which may include an unexpired employment authorization document (EAD) or valid visa.
2. Step 2 - Eligibility Verification: Confirm that the proof relates to the borrower identified as a Non-Permanent Resident.
3. Step 3 - Validation and Verification: Verify that proof of legal residency is provided and that an EAD, if used, is unexpired or a visa, if used, is valid.
4. Step 4 - Final Determination: Record whether proof of legal residency is provided.

**Checks:**
- The Non-Permanent Resident has proof of legal residency.

**Reads:** Borrower.citizenship_status
**Missing data:** Proof of legal residency and, where applicable, document expiration or validity

## acra-standard.credit_review_analysis.one_or_no_score_deficient_tradelines

**Purpose:** Verify the requirements printed for 1 or No Score / Deficient Tradelines.

1. Step 1 - Initial Document Review: Review the credit report and underwriting information for score count, tradeline status, CLTV, DSCR, and housing history.
2. Step 2 - Eligibility Verification: Apply this provision when the case has 1 or No Score / Deficient Tradelines.
3. Step 3 - Validation and Verification: Verify the printed requirements: Max 65% LTV/CLTV; DSCR Ratio ≥ 1.1; 24mos 0x30 housing history. Apply “1 Reported Score: Use Actual to Max 700; No Score: Price as 700 Tier”.
4. Step 4 - Final Determination: Record whether each applicable printed requirement is met; do not infer which score is the decisioning score.

**Checks:**
- For 1 or No Score / Deficient Tradelines, LTV/CLTV is no more than 65%.
- For 1 or No Score / Deficient Tradelines, DSCR Ratio is at least 1.1.
- For 1 or No Score / Deficient Tradelines, housing history is 24mos 0x30.
- For 1 Reported Score, use Actual to Max 700; for No Score, price as 700 Tier.

**Reads:** CreditReport.score_count, CreditReport.tradelines_meet_requirement, LoanCore.cltv_percent, CreditReport.housing_history_rating
**Missing data:** DSCR, Whether the case has deficient tradelines, The housing-history period and payment history, The score used for decisioning; Acra confirmation requested → Q-19

## acra-standard.credit_review_analysis.permanent_resident_documents

**Purpose:** Verify the required Permanent Resident identification and Social Security documentation.

1. Step 1 - Initial Document Review: For a Permanent Resident, review the unexpired PRA ID and SSA card / SSA-89.
2. Step 2 - Eligibility Verification: Confirm that the reviewed documents are for the borrower identified as a Permanent Resident.
3. Step 3 - Validation and Verification: Verify that the PRA ID is unexpired and that the SSA card / SSA-89 is provided.
4. Step 4 - Final Determination: Record whether both document requirements are met.

**Checks:**
- The Permanent Resident has an unexpired PRA ID and SSA card / SSA-89.

**Reads:** Borrower.citizenship_status
**Missing data:** PRA ID and its expiration date, SSA card or SSA-89

## acra-standard.credit_review_analysis.short_sale_dil_and_modification_seasoning_limits

**Purpose:** Check the printed maximum CLTV for short sale, deed-in-lieu, and modification seasoning bands.

1. Step 1 - Initial Document Review: Review the loan application and credit information for short sale, deed-in-lieu, or modification history, seasoning, loan purpose, and CLTV.
2. Step 2 - Eligibility Verification: Apply this provision when the borrower has a short sale, deed-in-lieu, or modification.
3. Step 3 - Validation and Verification: Compare seasoning and loan purpose with the printed table: ≥ 24 Mo, No Restrictions; 12-23 Mo, 80% purchase / 75% refinance; < 12 Mo, 75% purchase / 70% refinance.
4. Step 4 - Final Determination: Record whether the applicable printed restriction is met. Treat “FB Taken ≤6 Mos: Case-by-case” as requiring a case-by-case determination; the meaning and timing are subject to Acra confirmation → Q-05.

**Checks:**
- For seasoning ≥ 24 Mo, the table states No Restrictions.
- For seasoning 12-23 Mo, CLTV is no more than 80% for purchase or 75% for refinance — rate & term and cash-out.
- For seasoning < 12 Mo, CLTV is no more than 75% for purchase or 70% for refinance — rate & term and cash-out.

**Reads:** Borrower.has_short_sale_dil_or_modification, Borrower.months_since_short_sale_dil_or_modification, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Short sale, deed-in-lieu, or modification seasoning as measured under Acra’s labels; definitions and measurement are subject to Acra confirmation → Q-05, Whether “FB Taken ≤6 Mos” applies and its meaning and timing; Acra confirmation requested → Q-05

## acra-standard.identification_requirements.entity_certificate_of_good_standing

**Purpose:** Apply the Certificate of Good Standing requirement in U45.

1. Initial Document Review: Obtain and review the entity’s Certificate of Good Standing or equivalent document and the closing date.
2. Eligibility Verification: Confirm that the borrower is an entity borrower.
3. Validation and Verification: Verify that the document is valid within ninety (90) days of the closing date.
4. Final Determination: Record whether the required document is valid within the stated period.

**Checks:**
- A Certificate of Good Standing or equivalent document is valid within ninety (90) days of the closing date.

**Reads:** Borrower.is_entity_borrower_1, Borrower.entity_type
**Missing data:** Certificate of Good Standing or equivalent document, Document validity date, Closing date

## acra-standard.identification_requirements.entity_document_name_match

**Purpose:** Apply the entity document name requirement in U45.

1. Initial Document Review: Review the entity documents and identification.
2. Eligibility Verification: Confirm that the borrower is an entity borrower.
3. Validation and Verification: Compare names on the entity documents with identification; if they do not match exactly, verify that a letter of explanation addresses the discrepancy.
4. Final Determination: Record whether names match or the discrepancy is addressed by a letter of explanation.

**Checks:**
- Names on the entity documents match the identification, or a letter of explanation addresses any discrepancy.

**Reads:** Borrower.is_entity_borrower_1, Borrower.entity_type
**Missing data:** Names on entity documents, Names on identification, Letter of explanation addressing any name discrepancy, if applicable

## acra-standard.identification_requirements.entity_foreign_qualification

**Purpose:** Apply the entity qualification requirement in U45 when the entity is formed in a different state.

1. Initial Document Review: Review entity formation information and the state where business is being conducted or the property is located.
2. Eligibility Verification: Determine whether the entity was formed in a state other than where business is being conducted or where the property is located.
3. Validation and Verification: If the entity was formed in a different state, verify a Certificate of Foreign Qualification or other qualification to operate in the state where business is being conducted.
4. Final Determination: Record whether the applicable qualification document is provided.

**Checks:**
- If the entity is formed in a state other than where business is being conducted or where the property is located, a Certificate of Foreign Qualification or other qualification to operate in the state where business is being conducted is provided.

**Reads:** Borrower.is_entity_borrower_1, Borrower.entity_type, SubjectProperty.state
**Missing data:** Entity formation state, State where business is being conducted, Certificate of Foreign Qualification or other qualification to operate in the state where business is being conducted, if applicable

## acra-standard.identification_requirements.entity_power_of_attorney_for_personal_guarantee

**Purpose:** Apply the entity Power of Attorney requirement in U45 when a Power of Attorney is used for a personal guarantee.

1. Initial Document Review: Review any Power of Attorney used to execute a personal guarantee.
2. Eligibility Verification: Confirm that the borrower is an entity borrower and whether a Power of Attorney is used for the personal guarantee.
3. Validation and Verification: If used, verify that the principal utilizes the Power of Attorney to designate an attorney in fact to execute the personal guarantee; see §23.5(C).
4. Final Determination: Record whether the applicable Power of Attorney requirement is met.

**Checks:**
- If a Power of Attorney is used to execute a personal guarantee, the principal utilizes it to designate an attorney in fact to execute the personal guarantee.

**Reads:** Borrower.is_entity_borrower_1, Borrower.entity_type
**Missing data:** Power of Attorney used for a personal guarantee, if applicable, §23.5(C)

## acra-standard.identification_requirements.entity_tax_identification_document

**Purpose:** Apply the entity tax identification document requirement in U45.

1. Initial Document Review: Obtain and review the entity’s IRS Form SS4, Federal Taxpayer Identification Number (TIN), or Employer Identification Number (EIN) issuance letter.
2. Eligibility Verification: Confirm that the borrower is an entity borrower.
3. Validation and Verification: Verify that one of the listed entity tax identification items is provided. If an EIN exception is requested, verify that the request is submitted for review by Acra’s Legal Department with a letter of explanation stating the applicable grounds.
4. Final Determination: Record whether a listed item is provided or an EIN exception request has been submitted as stated.

**Checks:**
- The entity provides IRS Form SS4 or a Federal Taxpayer Identification Number (TIN) or Employer Identification Number (EIN) issuance letter, or an EIN exception request is submitted for review by Acra’s Legal Department with a letter of explanation stating the applicable grounds.

**Reads:** Borrower.is_entity_borrower_1, Borrower.entity_type
**Missing data:** IRS Form SS4 or Federal Taxpayer Identification Number (TIN) or Employer Identification Number (EIN) issuance letter, EIN exception request and letter of explanation stating the applicable grounds, if requested

## acra-standard.identification_requirements.entity_unanimous_written_consent_or_board_resolution

**Purpose:** Apply the entity authorization requirement in U45.

1. Initial Document Review: Obtain and review the Unanimous Written Consent / Board Resolution and the entity’s membership information.
2. Eligibility Verification: Confirm that the borrower is an entity borrower.
3. Validation and Verification: Verify that all members signed regardless of their percentage of interest, that the transaction with Acra Lending is authorized, and that the person authorized to sign the loan documents on behalf of and bind the entity is identified. Account for the stated possibility that the Operating Agreement or Bylaws may require it even where ownership is held by one individual. Verify that it does not designate a signor on a personal guarantee.
4. Final Determination: Record whether the consent or resolution contains the required signatures and authorizations.

**Checks:**
- The Unanimous Written Consent / Board Resolution is signed by all members regardless of their percentage of interest.
- The Unanimous Written Consent / Board Resolution authorizes the transaction with Acra Lending and identifies who is authorized to sign the loan documents on behalf of and to bind the entity.
- The Unanimous Written Consent / Board Resolution does not designate a signor on a personal guarantee.

**Reads:** Borrower.is_entity_borrower_1, Borrower.entity_type
**Missing data:** Unanimous Written Consent / Board Resolution, Entity membership and member signatures, Operating Agreement or Bylaws, if needed to determine whether the consent or resolution is required

## acra-standard.identification_requirements.foreign_national_approved_closing_agent

**Purpose:** Verify the closing agent requirement in STD-5.11.

1. Initial Document Review: Obtain and review evidence identifying the title and closing agent and its Acra approval and / or vetting.
2. Eligibility Verification: Confirm that the loan is being closed under the Foreign National Program.
3. Validation and Verification: Verify that the title and closing agent is approved and / or vetted by Acra.
4. Final Determination: Record whether the loan closes with an agent meeting the requirement.

**Checks:**
- The loan closes with a title and closing agent approved and / or vetted by Acra.

**Reads:** Borrower.citizenship_status
**Missing data:** Acra approval and / or vetting status of the title and closing agent

## acra-standard.identification_requirements.foreign_national_cltv_and_fico

**Purpose:** Verify the Foreign National Program CLTV and FICO requirements in STD-4.4.

1. Initial Document Review: Review the loan purpose, CLTV, and representative FICO score.
2. Eligibility Verification: Confirm that the borrower is a Foreign National.
3. Validation and Verification: Verify maximum CLTV 70% for purchase and 65% for refinance — rate & term and cash-out; verify that the loan is priced at FICO equal to 700.
4. Final Determination: Record whether the applicable maximum CLTV and FICO pricing requirement are met.

**Checks:**
- For a purchase, CLTV is no greater than 70%.
- For a refinance — rate & term and cash-out, CLTV is no greater than 65%.
- The loan is priced at FICO equal to 700.

**Reads:** Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent, CreditReport.representative_score

## acra-standard.identification_requirements.foreign_national_documents_signed_outside_u_s

**Purpose:** Apply the document execution requirements in STD-5.12 when documents are signed outside of the U.S.

1. Initial Document Review: Identify documents signed outside of the U.S., where they were signed, and their acknowledgment and authentication documents.
2. Eligibility Verification: Confirm whether the documents were signed outside of the U.S. and whether the country is party to the Hague Convention Treaty Abolishing the Requirement of Legalization for Foreign Public Documents.
3. Validation and Verification: For documents notarized by a U.S. embassy or consular official, verify that the certificate of acknowledgement includes the embassy or consular seal and is acceptable to the title company. For documents signed in a Hague Convention country, verify an authorized notary public’s completed and signed certificate of acknowledgment, authentication by apostille in English attached to the executed documents, and title company acceptance.
4. Final Determination: Record whether the applicable execution route’s requirements are met.

**Checks:**
- For documents notarized by a U.S. embassy or consular official, the certificate of acknowledgement includes the embassy or consular seal and is acceptable to the title company.
- For documents signed in a Hague Convention country, an authorized notary public has completed and signed the certificate of acknowledgment, authentication by apostille in English is attached to the executed documents, and the title company accepts it.

**Reads:** Borrower.citizenship_status
**Missing data:** Place of signing and whether the country is party to the Hague Convention Treaty Abolishing the Requirement of Legalization for Foreign Public Documents, Certificate of acknowledgment, Embassy or consular seal, if applicable, Apostille in English attached to executed documents, if applicable, Title company acceptance

## acra-standard.identification_requirements.foreign_national_executed_w_8_ben

**Purpose:** Verify the executed form required by STD-5.11.

1. Initial Document Review: Obtain and review the W-8 (BEN) IRS form.
2. Eligibility Verification: Confirm that the loan is being closed under the Foreign National Program.
3. Validation and Verification: Verify that the W-8 (BEN) IRS form is executed.
4. Final Determination: Record whether the executed form is provided.

**Checks:**
- An executed W-8 (BEN) IRS form is provided.

**Reads:** Borrower.citizenship_status
**Missing data:** Executed W-8 (BEN) IRS form

## acra-standard.identification_requirements.foreign_national_financial_position_review

**Purpose:** Apply the review scrutiny stated for applicants under the Foreign National Program.

1. Initial Document Review: Review information bearing on the applicant’s post-close financial position and exchange-rate exposure.
2. Eligibility Verification: Confirm that the application is being reviewed under the Foreign National Program.
3. Validation and Verification: Review the applicant’s post-close financial position and ability to mitigate exchange rate fluctuations with scrutiny.
4. Final Determination: Record the review conclusion.

**Checks:**
- The applicant’s post-close financial position and ability to mitigate exchange rate fluctuations have been reviewed with scrutiny.

**Reads:** Borrower.citizenship_status
**Missing data:** Applicant’s post-close financial position, Applicant’s ability to mitigate exchange rate fluctuations

## acra-standard.identification_requirements.foreign_national_identity_document

**Purpose:** Verify the identity document required by STD-5.11.

1. Initial Document Review: Obtain and review a copy of a current Passport, Visa, or ITIN.
2. Eligibility Verification: Confirm that the loan is being closed under the Foreign National Program.
3. Validation and Verification: Verify that the copy is of one of the listed documents and is current.
4. Final Determination: Record whether the required copy is provided and current.

**Checks:**
- A copy of a current Passport, Visa, or ITIN is provided.

**Reads:** Borrower.citizenship_status
**Missing data:** Copy of current Passport, Visa, or ITIN, Current status of the provided document

## acra-standard.identification_requirements.foreign_national_ofac_and_state_restrictions

**Purpose:** Resolve the Foreign National Program restrictions referenced in STD-5.5, which are not reproduced in the supplied text.

1. Initial Document Review: Identify whether the case is being reviewed under the Foreign National Program.
2. Eligibility Verification: Locate §3.10 for OFAC restrictions and state specific exclusions.
3. Validation and Verification: Review the applicable restrictions and exclusions in §3.10, Appendix B.
4. Final Determination: Record whether the case meets the applicable restrictions and exclusions.

**Checks:**
- The applicable OFAC restrictions and state specific exclusions in §3.10 have been reviewed and met.

**Reads:** Borrower.citizenship_status, SubjectProperty.state
**Missing data:** §3.10 OFAC restrictions and state specific exclusions (Appendix B)

## acra-standard.identification_requirements.foreign_national_power_of_attorney

**Purpose:** Apply the Foreign National Power of Attorney requirement in STD-5.11 when a Power of Attorney is provided.

1. Initial Document Review: Review any Power of Attorney used for the closing.
2. Eligibility Verification: Confirm that the loan is being closed under the Foreign National Program and whether a Power of Attorney is provided.
3. Validation and Verification: If provided, verify that the Power of Attorney conforms to Acra requirements and is acceptable to the title company.
4. Final Determination: Record whether a provided Power of Attorney meets both requirements.

**Checks:**
- If a Power of Attorney is provided, it conforms to Acra requirements and is acceptable to the title company.

**Reads:** Borrower.citizenship_status
**Missing data:** Power of Attorney, if provided, Acra requirements for the Power of Attorney, Title company acceptance

## acra-standard.identification_requirements.foreign_national_program_eligibility

**Purpose:** Verify the Foreign National Program eligibility requirements in STD-5.1 through STD-5.3.

1. Initial Document Review: Review the loan application and supporting information for citizenship type, place of residence, authorization to live or work in the U.S., and transaction purpose.
2. Eligibility Verification: For a Foreign National, verify that the transaction is business purpose only (i.e. investment property), that the borrower is a Non-Resident Alien not authorized to live or work in the U.S., and that the borrower resides outside of the U.S.
3. Validation and Verification: For an ITIN holder relying on the Foreign National Program, verify that the borrower resides outside of the U.S. For a true Foreign National, account for the stated allowance for periodic U.S. visits, limited personal use or investment property, and ownership of a U.S.-based business entity, while confirming residence outside the U.S.
4. Final Determination: Record whether the applicable Foreign National Program eligibility requirements are met.

**Checks:**
- A Foreign National’s transaction is business purpose only (i.e. investment property).
- A Foreign National is a Non-Resident Alien not authorized to live or work in the U.S. and resides outside of the U.S.
- An ITIN holder relying on the Foreign National Program resides outside of the U.S.

**Reads:** Borrower.citizenship_status, LoanCore.loan_purpose
**Missing data:** Borrower’s residence location, Whether the borrower is authorized to live in the U.S., Whether the borrower is authorized to work in the U.S., Whether the borrower is a Non-Resident Alien

## acra-standard.identification_requirements.itin_cltv_tier

**Purpose:** Verify the ITIN CLTV limits printed in STD-4.5 without interpreting the “FICO 700” tier beyond the text.

1. Initial Document Review: Review the representative FICO score, loan purpose, and CLTV.
2. Eligibility Verification: Confirm that the borrower is an ITIN holder.
3. Validation and Verification: Apply the printed tier and maximum CLTV: “FICO 700” — 70% purchase and 65% refinance — R/T and cash-out; “FICO 660 to 699” — 65% purchase and 60% refinance — R/T and cash-out; “FICO 640 to 659” — 60% purchase and 60% refinance — R/T and cash-out. Do not resolve the stated “FICO 700” ambiguity without Acra confirmation.
4. Final Determination: Record whether the applicable printed tier limit is met.

**Checks:**
- For “FICO 700”, purchase CLTV is no greater than 70%.
- For “FICO 700”, refinance — R/T and cash-out CLTV is no greater than 65%.
- For “FICO 660 to 699”, purchase CLTV is no greater than 65%.
- For “FICO 660 to 699”, refinance — R/T and cash-out CLTV is no greater than 60%.
- For “FICO 640 to 659”, purchase CLTV is no greater than 60%.
- For “FICO 640 to 659”, refinance — R/T and cash-out CLTV is no greater than 60%.

**Reads:** Borrower.citizenship_status, CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent

## acra-standard.identification_requirements.itin_maximum_loan_amount

**Purpose:** Apply the ITIN maximum loan amount in STD-4.5.

1. Initial Document Review: Review the total loan amount and borrower citizenship type.
2. Eligibility Verification: Confirm that the borrower is an ITIN holder.
3. Validation and Verification: Compare the total loan amount with the maximum loan amount $1.0M.
4. Final Determination: Record whether the loan amount is within the stated maximum.

**Checks:**
- The total loan amount is no greater than $1.0M.

**Reads:** Borrower.citizenship_status, LoanCore.total_loan_amount_usd

## acra-standard.identification_requirements.itin_minimum_fico

**Purpose:** Apply the ITIN minimum FICO in STD-4.5.

1. Initial Document Review: Review the representative credit score and borrower citizenship type.
2. Eligibility Verification: Confirm that the borrower is an ITIN holder.
3. Validation and Verification: Compare the representative credit score with the minimum FICO 640.
4. Final Determination: Record whether the minimum FICO is met.

**Checks:**
- The representative credit score is at least 640.

**Reads:** Borrower.citizenship_status, CreditReport.representative_score

## acra-standard.identification_requirements.itin_or_ssn_credit_reporting

**Purpose:** Apply STD-4.6’s credit reporting requirement for ITIN or SSN.

1. Initial Document Review: Review the credit report and the borrower’s applicable ITIN or SSN identification.
2. Eligibility Verification: Confirm that scores and tradelines are being used to meet requirements.
3. Validation and Verification: Verify that scores and tradelines are reported under the correct ITIN or SSN.
4. Final Determination: Record whether the reporting requirement is met.

**Checks:**
- Scores and tradelines are reported under the correct ITIN or SSN to meet requirements.

**Reads:** Borrower.citizenship_status, CreditReport.tradelines_meet_requirement
**Missing data:** Borrower’s ITIN or SSN identification and verification that the credit report’s scores and tradelines are reported under that correct identifier

## acra-standard.identification_requirements.itin_program_eligibility_clarification

**Purpose:** Resolve the two ITIN eligibility and tier ambiguities identified in STD-4.5.

1. Initial Document Review: Review the borrower’s ITIN status, residence, and applicable FICO tier.
2. Eligibility Verification: Identify whether the ITIN holder resides in the U.S. and whether the applicable tier is printed “FICO 700”.
3. Validation and Verification: Obtain Acra confirmation on whether a US-resident ITIN holder is eligible and whether “FICO 700” means 700 and above.
4. Final Determination: Record Acra’s confirmation before relying on either interpretation.

**Checks:**
- Acra has confirmed whether a US-resident ITIN holder is eligible.
- Acra has confirmed whether the “FICO 700” tier means 700 and above.

**Reads:** Borrower.citizenship_status
**Missing data:** Acra confirmation on US-resident ITIN holder eligibility, Acra confirmation on whether the “FICO 700” tier means 700 and above

## acra-standard.identification_requirements.non_permanent_resident_legal_residency

**Purpose:** Verify the legal residency documentation required under STD-4.3.

1. Initial Document Review: For a Non-Permanent Resident, obtain and review proof of legal residency.
2. Eligibility Verification: Confirm that the borrower’s citizenship type is Non-Permanent Resident.
3. Validation and Verification: Verify that proof of legal residency is provided; examples may include an unexpired employment authorization document (EAD) or valid visa.
4. Final Determination: Record whether proof of legal residency is provided.

**Checks:**
- The Non-Permanent Resident provides proof of legal residency.

**Reads:** Borrower.citizenship_status
**Missing data:** Proof of legal residency

## acra-standard.identification_requirements.non_permanent_resident_limits_clarification

**Purpose:** Resolve the stated ambiguity in the Non-Permanent Resident limits before applying them.

1. Initial Document Review: Review the Non-Permanent Resident limit printed as “Max Loan Amount: $1.5M: Max CLTV 80%”.
2. Eligibility Verification: Confirm that the borrower’s citizenship type is Non-Permanent Resident.
3. Validation and Verification: Obtain Acra confirmation on whether the printed amount and CLTV are two independent limits or one conditional limit.
4. Final Determination: Record the confirmation before applying the limit.

**Checks:**
- Acra has confirmed whether “Max Loan Amount: $1.5M: Max CLTV 80%” means two independent limits or one conditional limit.

**Reads:** Borrower.citizenship_status
**Missing data:** Acra confirmation on the interpretation of the printed Non-Permanent Resident limits

## acra-standard.identification_requirements.permanent_resident_identification

**Purpose:** Verify the identification documents required for a Permanent Resident under STD-4.2.

1. Initial Document Review: For a Permanent Resident, obtain and review a PRA ID and an SSA card / SSA-89.
2. Eligibility Verification: Confirm that the borrower’s citizenship type is Permanent Resident.
3. Validation and Verification: Verify that the PRA ID is unexpired and that the required SSA card / SSA-89 is provided.
4. Final Determination: Record whether both required items are provided and the PRA ID is unexpired.

**Checks:**
- A Permanent Resident provides an unexpired PRA ID and SSA card / SSA-89.

**Reads:** Borrower.citizenship_status
**Missing data:** PRA ID, PRA ID expiration status, SSA card / SSA-89

## acra-standard.income_stability_sufficiency_analysis.apply_minimum_dscr_requirements

**Purpose:** Determine whether a calculated DSCR meets the stated minimum for each applicable situation.

1. Initial Document Review: Review the DSCR calculation and information identifying the loan amount, credit file, property, occupancy, purpose, and borrower status.
2. Eligibility Verification: Identify each applicable situation: LTV above 80.00%; loan amount over $2,000,000; 1 or no score / deficient tradelines; rural / unique property; non-warrantable condo or condotel / PUDtel; first-time homebuyer; vacant-property rate & term refinance; vacant-property cash-out refinance; property listed for sale within six months; or mixed use, adult care or assisted living.
3. Validation and Verification: Verify the calculated DSCR against each applicable stated minimum: 1.20 for LTV above 80.00%; 1.0 for loan amount over $2,000,000; 1.1 for 1 or no score / deficient tradelines; 1.00 for rural / unique property; 1.0 for non-warrantable condo or condotel / PUDtel; 1.150 for first-time homebuyer; 1.000 for vacant-property rate & term refinance; 1.15 for vacant-property cash-out refinance; 1.0 for property listed for sale within six months; and 1.2 for mixed use, adult care or assisted living.
4. Final Determination: Record whether the calculated DSCR meets every minimum that applies. The stated DTI alternatives for vacant-property rate & term refinance and properties listed for sale are not resolved here; Acra confirmation is requested on those provisions.

**Checks:**
- If LTV is above 80.00%, calculated DSCR is at least 1.20.
- If the loan amount is over $2,000,000, calculated DSCR is at least 1.0.
- If there is 1 or no score / deficient tradelines, calculated DSCR is at least 1.1.
- If the property is rural / unique, calculated DSCR is at least 1.00.
- If the property is a non-warrantable condo or condotel / PUDtel, calculated DSCR is at least 1.0.
- If the borrower is a first-time homebuyer, calculated DSCR is at least 1.150.
- If the property is vacant and the transaction is a rate & term refinance, calculated DSCR is at least 1.000.
- If the property is vacant and the transaction is a cash-out refinance, calculated DSCR is at least 1.15.
- If the property was listed for sale within six months, calculated DSCR is at least 1.0.
- If the property is mixed use, adult care or assisted living, calculated DSCR is at least 1.2.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.loan_purpose, LoanCore.cltv_percent, SubjectProperty.property_type, SubjectProperty.is_rural, SubjectProperty.is_vacant, SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_listed_for_sale, SubjectProperty.is_mixed_use, SubjectProperty.occupancy_subtype, CreditReport.score_count, CreditReport.tradelines_meet_requirement, Borrower.is_first_time_homebuyer
**Missing data:** Calculated DSCR, LTV, Whether the transaction is a refinance and whether it is rate & term or cash-out, Whether the property is a non-warrantable condo or condotel / PUDtel, Whether a vacant-property refinance is being considered, Whether the property was listed for sale within six months, measured from the last date of being listed to the Application Date, Whether the property is adult care or assisted living

## acra-standard.income_stability_sufficiency_analysis.calculate_dscr

**Purpose:** Determine the calculated DSCR for a file qualifying using a calculated DSCR.

1. Initial Document Review: Review the rental-income and property-expense information used for the calculation.
2. Eligibility Verification: Confirm that the file qualifies using a calculated DSCR, rather than No Ratio DSCR.
3. Validation and Verification: Calculate DSCR by dividing the lesser of annual in-place rent or market rent by the sum of annual principal, interest, real estate taxes, property insurance, homeowner's / condominium association fees, and subordinate financing, if applicable. Use the first payment due under the terms of the Note.
4. Final Determination: Record the calculated DSCR. Do not calculate a DSCR for a No Ratio DSCR file. The guidelines do not resolve which payment enters the denominator for an interest-only loan.

**Checks:**
- For a file qualifying using a calculated DSCR, the calculated DSCR divides the lesser of annual in-place rent or market rent by annual PITIA, including subordinate financing if applicable.

**Reads:** LoanCore.dscr_qualification_method
**Missing data:** DSCR qualification method, if not recorded in the case field, Annual in-place rent, Market rent, Annual principal, Annual interest, Annual real estate taxes, Annual property insurance, Annual homeowner's / condominium association fees, Annual subordinate financing payment, if applicable, The applicable interest-only loan payment for the DSCR denominator, if applicable

## acra-standard.income_stability_sufficiency_analysis.verify_higher_actual_rent_evidence

**Purpose:** Determine whether the documentation stated for actual rents exceeding market rents is present.

1. Initial Document Review: Review the actual-rent and market-rent information, rental-income receipt evidence, and lease agreement(s).
2. Eligibility Verification: Determine whether actual rents exceed market rents.
3. Validation and Verification: If actual rents exceed market rents, verify two (2) consecutive months proof of rental income receipt and lease agreement(s) to continue at a minimum of three (3) months after closing. Do not count a Security Deposit towards receipt; rents cannot be prepaid.
4. Final Determination: Record whether the stated evidence and lease conditions are met. The guidelines do not select between the formula using the lesser of annual in-place rent or market rent and the provision allowing use of the higher of actual or market rents.

**Checks:**
- If actual rents exceed market rents, two (2) consecutive months proof of rental income receipt is documented, lease agreement(s) continue at a minimum of three (3) months after closing, no Security Deposit is counted towards receipt, and rents are not prepaid.
**Missing data:** Actual rent amount, Market rent amount, Closing date, Rental-income receipt dates and amounts, Whether any receipt is a Security Deposit, Whether rents have been prepaid, Lease end date

## acra-standard.income_stability_sufficiency_analysis.verify_rent_schedule

**Purpose:** Verify the required Single-Family Comparable Rent Schedule or the stated short-term-rental replacement.

1. Initial Document Review: Review the appraisal and rental-income evidence in the file.
2. Eligibility Verification: Determine whether the property is single family on a DSCR qualifying file, the transaction is a lease-option purchase using excess monthly rent contributions for the required down payment, or proposed rental income is being used to qualify.
3. Validation and Verification: For a single-family property, verify that a Single-Family Comparable Rent Schedule (FNMA Form 1007) is present. For a property occupied as a short-term rental, an STRpro or similar appraisal form may replace a 1007 if signed by an appropriately licensed appraiser. A 1007 may be from the original appraiser or any state licensed appraiser.
4. Final Determination: Record whether the applicable rent-schedule requirement is met.

**Checks:**
- A 1007 is present when required for a single-family DSCR qualifying file, a lease-option purchase using excess monthly rent contributions for the required down payment, or when proposed rental income is used to qualify, unless the stated short-term-rental replacement applies.

**Reads:** SubjectProperty.property_type, SubjectProperty.occupancy_subtype
**Missing data:** Whether proposed rental income is being used to qualify, Whether lease-option purchase down-payment funds are generated from excess monthly rent contributions, Whether the property is occupied as a short-term rental, Appraiser licensing status, Appraiser identity, to establish whether the appraiser is the original appraiser

## acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability

**Purpose:** Determine whether six (6) months' rent loss insurance is required for the subject property under the stated property, LTV, and rent-qualification conditions.

1. Step 1 - Initial Document Review: Review the case information for the subject property's number of units, occupancy subtype, CLTV, and DSCR qualification method.
2. Step 2 - Eligibility Verification: Establish whether the property is a one- to four-unit, non-owner-occupied income property; establish whether LTV is > 70% and subject property rents are used to qualify. The stated requirement includes No Ratio DSCR.
3. Step 3 - Validation and Verification: Check whether the loan has ≤ 70% CLTV. If LTV is at or below 70% while CLTV is above 70%, preserve the stated unresolved case for Acra confirmation.
4. Step 4 - Final Determination: Record whether the rent loss insurance requirement applies, does not apply, or cannot be determined without Acra confirmation or missing trigger information.

**Checks:**
- The subject property has one to four units.
- The subject property is non-owner occupied.
- The subject property is an income property.
- The subject property's LTV is > 70%.
- Subject property rents are used to qualify.
- The loan has ≤ 70% CLTV.

**Reads:** SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype, LoanCore.cltv_percent, LoanCore.dscr_qualification_method
**Missing data:** Subject property's LTV, Whether the subject property is an income property, Whether subject property rents are used to qualify

## acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_coverage_sufficiency

**Purpose:** Determine whether the rent loss insurance requirement is met by six (6) months' coverage or by the stated reserve substitution when the coverage cannot be obtained.

1. Step 1 - Initial Document Review: Review hazard insurance declarations for rent loss coverage and its duration.
2. Step 2 - Eligibility Verification: Confirm that the rent loss insurance requirement applies, using the Rent Loss Insurance Applicability determination.
3. Step 3 - Validation and Verification: Verify that rent loss insurance covers rental losses incurred during the period the property is being rehabilitated following a casualty. If six (6) months' coverage is not provided, establish whether the required coverage cannot be obtained and whether reserves provide two (2) months for every one (1) month of rent loss coverage not provided.
4. Step 4 - Final Determination: Record whether the required coverage or permitted reserve substitution is established.

**Checks:**
- Rent loss insurance covers rental losses incurred during the period the property is being rehabilitated following a casualty.
- The hazard insurance evidence establishes six (6) months' rent loss insurance coverage.
- Required rent loss insurance cannot be obtained.
- Reserves provide two (2) months for every one (1) month of rent loss coverage not provided.

**Reads:** RatioSet.reserves_months
**Missing data:** Whether required rent loss insurance can be obtained, Duration of rent loss insurance coverage provided, Number of months of rent loss coverage not provided

## acra-standard.liabilities_assessment.dscr_calculation

**Purpose:** Determine the DSCR using the calculation rule in STD-3.1 and the first-payment rule in STD-3.2.

1. Step 1 - Initial Document Review: Identify the rent, payment, PITIA, and, if applicable, subordinate-financing data needed for the calculation.
2. Step 2 - Eligibility Verification: Apply the lesser of annual in-place rent or market rent as the numerator.
3. Step 3 - Validation and Verification: Use the first payment due under the terms of the Note and include annual principal, interest, real estate taxes, property insurance, homeowner's / condominium association fees, and subordinate financing if applicable in the denominator.
4. Step 4 - Final Determination: Calculate the DSCR only when the required calculation inputs and market-rent method are available; otherwise identify the unresolved inputs or reference.

**Checks:**
- The numerator is the lesser of annual in-place rent or market rent.
- The denominator is the sum of annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees (PITIA), with subordinate financing included if applicable.
- The calculation utilizes the first payment due under the terms of the Note.
**Missing data:** annual in-place rent, market rent, the §14.14 market-rent method, the first payment due under the terms of the Note, annual principal, annual interest, annual real estate taxes, annual property insurance, annual homeowner's / condominium association fees, annual subordinate-financing amount, if applicable

## acra-standard.liabilities_assessment.heloc_cltv_basis

**Purpose:** Apply the stated HELOC CLTV calculation rule when subordinate/secondary financing is allowable.

1. Step 1 - Initial Document Review: Identify whether the subordinate/secondary financing is a HELOC and obtain its credit line limit and current credit line balance.
2. Step 2 - Eligibility Verification: Apply this rule only when the subordinate/secondary financing is allowable.
3. Step 3 - Validation and Verification: Compare the credit line limit with the current credit line balance and use the greater amount for CLTV eligibility.
4. Step 4 - Final Determination: Record the greater amount as the HELOC CLTV basis for eligibility.

**Checks:**
- For allowable subordinate/secondary financing that is a HELOC, CLTV for eligibility is calculated on the greater of the credit line limit or current credit line balance.
**Missing data:** whether the subordinate/secondary financing is a HELOC, credit line limit, current credit line balance, whether subordinate/secondary financing is allowable

## acra-standard.liabilities_assessment.interest_only_dscr_payment_basis_confirmation

**Purpose:** Resolve the payment-basis question identified for interest-only loans in STD-3.2.

1. Step 1 - Initial Document Review: Determine whether the loan is interest-only.
2. Step 2 - Eligibility Verification: For an interest-only loan, identify the unresolved question of which payment enters the DSCR denominator.
3. Step 3 - Validation and Verification: Obtain Acra confirmation of the payment basis for the DSCR denominator on an interest-only loan.
4. Step 4 - Final Determination: Record whether that confirmation has been obtained; do not select a payment basis without it.

**Checks:**
- Acra confirmation identifies which payment enters the DSCR denominator for an interest-only loan.

**Reads:** MortgageLoanInformation.is_interest_only
**Missing data:** Acra confirmation of the DSCR denominator payment basis for an interest-only loan

## acra-standard.liabilities_assessment.subordinate_financing_eligibility

**Purpose:** Determine whether subordinate financing may be used, subject to the stated prohibition and the requested Acra confirmation.

1. Step 1 - Initial Document Review: Identify whether subordinate financing is proposed and the relevant lien type and transaction.
2. Step 2 - Eligibility Verification: Do not allow subordinate financing on a property listed for sale.
3. Step 3 - Validation and Verification: For other cases, obtain Acra confirmation of whether subordinate financing is allowed on this program and for the relevant lien types and transactions.
4. Step 4 - Final Determination: Determine whether the proposed subordinate financing is prohibited, confirmed allowable, or remains subject to confirmation.

**Checks:**
- Subordinate financing is not used on a property listed for sale.
- Acra confirmation establishes whether the proposed subordinate financing is allowed on this program for the relevant lien type and transaction.

**Reads:** SubjectProperty.is_listed_for_sale
**Missing data:** whether subordinate financing is proposed, proposed subordinate-financing lien type, transaction type, Acra confirmation of program allowance for the relevant lien type and transaction

## acra-standard.loan_program_eligibility.additional_loan_amount_limits

**Purpose:** Determine whether the loan meets the additional loan-amount conditions below $200,000 and above $2,000,000.

1. Step 1 - Initial Document Review: Review the loan_application and underwriting qualification for loan amount, purpose, CLTV, and DSCR.
2. Step 2 - Eligibility Verification: For a loan amount < $200,000, apply maximum CLTV 80% for purchase and 75% for refinance — rate & term and cash-out. For a loan amount > $2,000,000, apply minimum DSCR 1.0 or greater.
3. Step 3 - Validation and Verification: Verify each applicable cap or minimum against the loan's values.
4. Step 4 - Final Determination: Determine whether all applicable additional loan-amount conditions are met.

**Checks:**
- If loan amount is < $200,000, CLTV does not exceed 80% for purchase or 75% for refinance — rate & term and cash-out.
- If loan amount is > $2,000,000, DSCR is 1.0 or greater.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** DSCR qualification result., Transaction-purpose classification if necessary to distinguish purchase from refinance.

## acra-standard.loan_program_eligibility.citizenship_category

**Purpose:** Identify whether the borrower has an eligible citizenship type and the applicable category-specific documentation requirements.

1. Step 1 - Initial Document Review: Review the loan_application and relevant borrower documentation for citizenship or residency category.
2. Step 2 - Eligibility Verification: Confirm whether the category is US Citizen, Permanent Resident, Non-Permanent Resident, Foreign National, or ITIN.
3. Step 3 - Validation and Verification: For a Permanent Resident, verify an unexpired PRA ID and SSA card / SSA-89. For a Non-Permanent Resident, verify proof of legal residency, which may include an unexpired employment authorization document (EAD) or valid visa.
4. Step 4 - Final Determination: Record the eligible category and whether its stated documentation requirement is met.

**Checks:**
- The borrower is a US Citizen, Permanent Resident, Non-Permanent Resident, Foreign National, or ITIN holder.
- A Permanent Resident has an unexpired PRA ID and SSA card / SSA-89.
- A Non-Permanent Resident has proof of legal residency.

**Reads:** Borrower.citizenship_status
**Missing data:** Borrower citizenship or residency evidence., For a Permanent Resident, PRA ID expiration and SSA card / SSA-89 evidence., For a Non-Permanent Resident, proof of legal residency.

## acra-standard.loan_program_eligibility.eligible_property_type

**Purpose:** Determine whether the property type is eligible and whether its stated CLTV cap is met.

1. Step 1 - Initial Document Review: Review the appraisal_report and loan_application for property type, units, location, purpose, and CLTV.
2. Step 2 - Eligibility Verification: Confirm the property type is SFR, Townhome, PUD, Warrantable Condo, Non-Warrantable Condo, Condotel / PUDtel, 2-4 Units, or Manufactured.
3. Step 3 - Validation and Verification: Apply the printed caps: Non-Warrantable Condo 80% purchase / 75% refinance and minimum DSCR 1.0; Condotel / PUDtel 75% purchase / 70% refinance rate & term / 65% refinance cash-out and minimum DSCR 1.0; 2-4 Unit maximum CLTV 80%; Manufactured Home 65% purchase / 60% refinance. Apply the Florida -5% CLTV adjustment for Non-Warrantable Condo and Condotel / PUDtel. Apply rural / unique property maximum CLTV 80% purchase / 75% refinance rate & term / 70% refinance cash-out, minimum FICO 700, and minimum DSCR 1.00. Above 80.00% LTV, only SFR, Warrantable Condos outside of Florida, Townhome and PUD are eligible.
4. Step 4 - Final Determination: Determine whether the property type is eligible and every applicable printed condition is met.

**Checks:**
- The property type is among the published eligible property types.
- The applicable printed property-type CLTV cap is met.
- For a Non-Warrantable Condo or Condotel / PUDtel, the applicable minimum DSCR is met.
- For rural / unique property, the minimum FICO and minimum DSCR are met and the applicable CLTV cap is met.
- If LTV is above 80.00%, the property is SFR, a Warrantable Condo outside of Florida, Townhome, or PUD.

**Reads:** SubjectProperty.property_type, SubjectProperty.number_of_units, SubjectProperty.state, SubjectProperty.is_rural, LoanCore.loan_purpose, LoanCore.cltv_percent, CreditReport.representative_score
**Missing data:** Appraisal evidence establishing the property type and, if applicable, rural / unique characteristics., DSCR result for applicable property-type minimums., FICO and transaction-purpose classification for applicable property-type limits.

## acra-standard.loan_program_eligibility.eligible_state

**Purpose:** Determine whether the subject property's state is eligible under the published location restriction.

1. Step 1 - Initial Document Review: Review the loan_application and appraisal_report for the subject property's location.
2. Step 2 - Eligibility Verification: Compare the subject property's state with the published ineligible state, SD.
3. Step 3 - Validation and Verification: Validate the state shown for the subject property.
4. Step 4 - Final Determination: Determine whether the property is outside SD.

**Checks:**
- The subject property is not located in SD.

**Reads:** SubjectProperty.state

## acra-standard.loan_program_eligibility.entity_borrower_eligibility

**Purpose:** Determine whether an entity borrower and its entity structure meet the stated entity eligibility requirements.

1. Step 1 - Initial Document Review: Review entity_documents and the loan_application for entity type, formation and base, purpose, assets, ownership, and title-holding entities.
2. Step 2 - Eligibility Verification: Verify that the entity is a permitted type, US formed and based, and not a foreign-owned entity; verify that an entity borrower is an SPE engaged in owning and operating residential investment or rental properties and has no assets other than residential investment or rental properties.
3. Step 3 - Validation and Verification: Verify that all entities holding direct ownership of the subject property are borrowing entities; exclude Cooperatives, Irrevocable Trusts, Land Trusts, IRAs, Non-Profit, and Joint Ventures; verify that nesting is limited to one (1) wholly-owned subsidiary owned by individual(s).
4. Step 4 - Final Determination: Determine whether the entity borrower and structure meet the stated requirements.

**Checks:**
- The entity is an allowed entity type and is US formed and based, and is not foreign owned.
- The entity borrower meets the stated SPE description and is not a series LLC.
- Every entity holding direct ownership of the subject property is a borrowing entity.
- The structure is not a prohibited entity type and does not exceed the stated nesting limit.

**Reads:** Borrower.entity_type, Borrower.is_entity_borrower_1, Borrower.entity_documents_complete
**Missing data:** Entity formation, base, ownership, entity type, assets, business activities, and nesting structure., Evidence identifying every direct owner of the subject property.

## acra-standard.loan_program_eligibility.entity_guarantees

**Purpose:** Determine whether required guarantees and the prior-homeownership attestation are present for an entity borrower.

1. Step 1 - Initial Document Review: Review the loan_application and entity_documents for direct and indirect ownership, guarantor identities, guarantees, homeownership attestation, and ownership changes.
2. Step 2 - Eligibility Verification: Verify that all individuals with direct or indirect ownership ≥ 20% provide a recourse guarantee, Acra approved or Exhibit 7; multiple guarantors' recourse is joint and several.
3. Step 3 - Validation and Verification: Verify that at least one guarantor has prior homeownership experience and that at least one borrower / guarantor attests on the application that they are not a first-time homebuyer. If prior home ownership is not evident within the loan file, the underwriter may condition for supporting documentation. Verify that ownership changes intended to circumvent required personal guarantors are not recognized if made within 30 days prior to an Application Date or throughout the application process.
4. Step 4 - Final Determination: Determine whether the applicable guarantees, attestation, and ownership-change requirements are met.

**Checks:**
- Every individual with direct or indirect ownership ≥ 20% provides the required recourse guarantee.
- At least one guarantor has prior homeownership experience.
- At least one borrower / guarantor attests on the application that they are not a first-time homebuyer.
- An ownership change intended to circumvent required personal guarantors made within 30 days prior to an Application Date or throughout the application process is not recognized.

**Reads:** Borrower.is_entity_borrower_1, Borrower.entity_documents_complete, Borrower.is_first_time_homebuyer
**Missing data:** Ownership percentages and dates and purposes of operating-agreement or bylaw changes., Executed guarantees and evidence of guarantor prior homeownership or the required application attestation.

## acra-standard.loan_program_eligibility.first_time_homebuyer_conditions

**Purpose:** Determine whether a first-time homebuyer meets the program's stated DSCR conditions.

1. Step 1 - Initial Document Review: Review the loan_application, credit_report, and supporting loan records for all applicants' homeownership history and the loan terms.
2. Step 2 - Eligibility Verification: Apply the definition that all Applicants have never previously owned a home (real property).
3. Step 3 - Validation and Verification: Verify minimum 700 FICO, maximum 70% CLTV, minimum DSCR of 1.150, maximum loan amount of $1,000,000, full amortization with no interest-only programs, impounds, and minimum six months reserves.
4. Step 4 - Final Determination: Determine whether the first-time homebuyer definition and all applicable DSCR conditions are met.

**Checks:**
- All Applicants have never previously owned a home (real property).
- FICO is at least 700.
- CLTV does not exceed 70%.
- DSCR is at least 1.150.
- Loan amount does not exceed $1,000,000.
- The loan is fully amortizing and is not interest-only.
- Impounds are required.
- Reserves are at least six months.

**Reads:** Borrower.is_first_time_homebuyer, CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.total_loan_amount_usd, MortgageLoanInformation.is_interest_only, LoanCore.is_escrow_waived, RatioSet.reserves_months
**Missing data:** All-applicant homeownership history., DSCR calculation or supporting qualification result., Evidence that impounds are required.

## acra-standard.loan_program_eligibility.foreign_national_eligibility

**Purpose:** Determine whether a Foreign National meets the stated residence and transaction-purpose requirements and apply the published CLTV limits.

1. Step 1 - Initial Document Review: Review the loan_application and supporting borrower documentation for residence, authorization to live or work in the U.S., and transaction purpose.
2. Step 2 - Eligibility Verification: Verify that the borrower resides outside the U.S., is not authorized to live or work in the U.S., and the transaction is for a business purpose (investment property).
3. Step 3 - Validation and Verification: Apply the stated Foreign National CLTV maximums: 70% for purchase and 65% for refinance — rate & term and cash-out. Verify the loan is priced at FICO equal to 700.
4. Step 4 - Final Determination: Determine whether the stated Foreign National requirements are met.

**Checks:**
- The borrower resides outside of the U.S.
- The borrower is not authorized to live or work in the U.S.
- The transaction is for a business purpose (investment property).
- The applicable CLTV does not exceed 70% for purchase or 65% for refinance — rate & term and cash-out.
- The loan is priced at FICO equal to 700.

**Reads:** Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Evidence of the borrower's residence and authorization to live or work in the U.S., Evidence establishing transaction business purpose., The loan's FICO pricing and applicable transaction-purpose classification.

## acra-standard.loan_program_eligibility.interest_only_eligibility

**Purpose:** Determine whether an interest-only loan meets the applicable published product and eligibility conditions.

1. Step 1 - Initial Document Review: Review the loan_application, credit_report, and appraisal_report for interest-only term, product, loan amount, FICO, CLTV, and property and borrower characteristics.
2. Step 2 - Eligibility Verification: Confirm the selected product is one of the published eligible interest-only products: 5 Yr / 30 year term on 5/1 or 7/1 ARM; 5 Yr / 30 Year Fixed; or 10 Yr / 40 Year Term.
3. Step 3 - Validation and Verification: Apply minimum loan amount $250,000 and minimum 640 credit score. For 10 Yr / 40 Year Term, also apply maximum 80% LTV / CLTV and maximum $3M loan amount. Interest-only is not available to first-time homebuyers, on vacant-property refinances, or on properties listed for sale.
4. Step 4 - Final Determination: Determine whether the applicable interest-only product conditions are met.

**Checks:**
- The selected interest-only product is a published eligible product.
- The loan amount is at least $250,000 and FICO is at least 640.
- For 10 Yr / 40 Year Term, loan amount does not exceed $3M and LTV / CLTV does not exceed 80%.
- The borrower is not a first-time homebuyer.
- The loan is not a refinance of a vacant property.
- The property is not listed for sale.

**Reads:** MortgageLoanInformation.is_interest_only, LoanCore.total_loan_amount_usd, CreditReport.representative_score, LoanCore.cltv_percent, Borrower.is_first_time_homebuyer, SubjectProperty.is_vacant, SubjectProperty.is_listed_for_sale
**Missing data:** Evidence of selected product and term., The loan's LTV for the 10 Yr / 40 Year Term, if not represented by CLTV.

## acra-standard.loan_program_eligibility.investment_occupancy

**Purpose:** Determine whether the subject meets the program's investment-property occupancy requirement.

1. Step 1 - Initial Document Review: Review the loan_application and any lease_agreement or rent_roll for evidence of the subject's occupancy and rental use.
2. Step 2 - Eligibility Verification: Verify that the property is investment property (non-owner occupied) and that it is a one- to four-unit residential dwelling, a condominium unit, or a PUD unit owned by an individual who does not occupy it.
3. Step 3 - Validation and Verification: Verify that the dwelling is leased and occupied as a principal year-round residence by individuals other than the owner.
4. Step 4 - Final Determination: Determine whether the investment-property occupancy requirement is met.

**Checks:**
- The subject is an investment property (non-owner occupied).
- The dwelling is leased and occupied as a principal year-round residence by individuals other than the owner.
- The dwelling or unit is within the eligible investment-property description.

**Reads:** SubjectProperty.occupancy_subtype, SubjectProperty.number_of_units, SubjectProperty.has_current_lease
**Missing data:** Evidence establishing whether the owner occupies the dwelling., Evidence establishing year-round tenant occupancy and the dwelling's principal-residence use.

## acra-standard.loan_program_eligibility.itin_limits

**Purpose:** Determine whether an ITIN loan meets the limits expressly printed for the ITIN program.

1. Step 1 - Initial Document Review: Review the loan_application and credit_report for ITIN status, loan amount, score, purpose, and CLTV.
2. Step 2 - Eligibility Verification: Apply the maximum loan amount of $1.0M and minimum FICO 640.
3. Step 3 - Validation and Verification: Apply the printed ITIN CLTV tier for the FICO and transaction purpose: “FICO 700” is 70% purchase and 65% refinance; FICO 660 to 699 is 65% purchase and 60% refinance; FICO 640 to 659 is 60% purchase and 60% refinance. Do not infer whether “FICO 700” means 700 and above or whether a US-resident ITIN holder is eligible.
4. Step 4 - Final Determination: Determine whether the stated limits are met and refer the unresolved eligibility questions for confirmation where they affect the case.

**Checks:**
- The loan amount does not exceed $1.0M.
- The borrower's FICO is at least 640.
- The CLTV does not exceed the applicable printed ITIN tier and transaction-purpose limit.
- Any determination of eligibility for a US-resident ITIN holder or application of the “FICO 700” tier is supported by Acra confirmation.

**Reads:** Borrower.citizenship_status, LoanCore.total_loan_amount_usd, CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Acra confirmation on whether a US-resident ITIN holder is eligible and whether the tier printed “FICO 700” means 700 and above, if either question affects the case.

## acra-standard.loan_program_eligibility.loan_amount

**Purpose:** Determine whether the loan amount meets the published minimum, maximum, and increment requirements, including the delayed-financing cap.

1. Step 1 - Initial Document Review: Review the loan_application for the requested loan amount and transaction purpose.
2. Step 2 - Eligibility Verification: Verify the amount against the published program range and increment requirement; for interest-only loans, also apply the interest-only amount limits.
3. Step 3 - Validation and Verification: For delayed financing, verify that the amount does not exceed the stated delayed-financing cap.
4. Step 4 - Final Determination: Determine whether all applicable loan-amount requirements are met.

**Checks:**
- The loan amount is from $100,000 to $3,000,000 and is in $50 increments.
- For an interest-only loan, the loan amount is at least $250,000 and no more than $3,000,000.
- For delayed financing, the loan amount is no more than $1.5MM.

**Reads:** LoanCore.total_loan_amount_usd, LoanCore.loan_purpose, LoanCore.is_delayed_financing, MortgageLoanInformation.is_interest_only

## acra-standard.loan_program_eligibility.matrix_fico_and_cltv

**Purpose:** Determine whether the applicable published matrix row permits the loan's FICO and CLTV.

1. Step 1 - Initial Document Review: Review the loan_application and credit_report for loan amount, representative score, transaction purpose, and CLTV.
2. Step 2 - Eligibility Verification: Select the published loan-amount tier, FICO row, and Purchase, Rate & Term, or Cash-Out column; apply NA entries as printed.
3. Step 3 - Validation and Verification: Verify that FICO and CLTV meet the applicable matrix entry. For loans ≤ $1,500,000 below 600, do not infer a published matrix value or eligibility; the source requests Acra confirmation.
4. Step 4 - Final Determination: Determine whether the applicable published matrix value is met, or refer an unresolved no-value case for confirmation.

**Checks:**
- The loan's FICO meets a published matrix row for the loan amount and transaction purpose.
- The loan's CLTV does not exceed the CLTV value in the applicable published matrix row.
- If a loan ≤ $1,500,000 has FICO below 600, Acra confirmation is obtained before determining eligibility.

**Reads:** LoanCore.total_loan_amount_usd, CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent
**Missing data:** Acra confirmation if the loan amount is ≤ $1,500,000 and FICO is below 600., Clarification of transaction-purpose classification if the loan does not map to a Purchase, Rate & Term, or Cash-Out column.

## acra-standard.loan_program_eligibility.mixed_use_property

**Purpose:** Determine whether the stated mixed-use minimum DSCR is met and identify the additional unreproduced conditions.

1. Step 1 - Initial Document Review: Review the appraisal_report and loan_application for commercial and residential use of the property.
2. Step 2 - Eligibility Verification: Verify whether a portion of the property's space is dedicated to commercial use and the rest to residential use.
3. Step 3 - Validation and Verification: For a mixed-use property, apply minimum DSCR ratio of 1.2 and identify that approval conditions in §10.7, including restrictions regarding Adult Care / Assisted Living Facilities, are not reproduced in the source.
4. Step 4 - Final Determination: Determine whether the minimum DSCR is met and refer unreproduced §10.7 conditions for review.

**Checks:**
- The mixed-use property meets the minimum DSCR ratio of 1.2.
- The conditions in §10.7, which are not reproduced, have been reviewed before approval.

**Reads:** SubjectProperty.is_mixed_use
**Missing data:** DSCR result., The unreproduced §10.7 conditions and evidence needed to assess them.

## acra-standard.loan_program_eligibility.prepayment_penalty_structure

**Purpose:** Determine whether the selected structure is published and meets stated transaction-specific minimum terms.

1. Step 1 - Initial Document Review: Review the loan_application for property state, transaction type, unit count, borrower or entity closing name, loan amount, interest rate, and selected prepayment penalty structure.
2. Step 2 - Eligibility Verification: Verify that the selected structure is one of the published structures: 5 Year 5% Fixed or Sequential Stepdown; 4 Year 5% Fixed or 3% Fixed; 3 Year 5% Fixed or 3% Fixed; 2 Year 3% Fixed; 1 Year 3% Fixed; or No Prepay.
3. Step 3 - Validation and Verification: Apply stated minimums: vacant-property rate & term refinance requires at least two years and vacant-property cash-out refinance at least three years, each where allowable; property listed for sale requires at least three years unless located in a state that does not allow prepayment penalties. Apply the printed state restrictions as written; the meaning of “BUY-OUT” and how state restrictions interact with the minimums require Acra confirmation.
4. Step 4 - Final Determination: Determine whether the selected structure meets applicable stated minimums and refer unresolved state-restriction interpretation for confirmation.

**Checks:**
- The selected prepayment penalty structure is one of the published structures.
- A vacant-property rate & term refinance has a prepayment penalty of at least two years where allowable.
- A vacant-property cash-out refinance has a prepayment penalty of at least three years where allowable.
- A property listed for sale has a prepayment penalty of at least three years unless the property is in a state that does not allow prepayment penalties.
- Any applicable printed state restriction is reviewed and any unresolved “BUY-OUT” interpretation or interaction with a stated minimum is referred for Acra confirmation.

**Reads:** LoanCore.prepayment_penalty_structure, SubjectProperty.state, SubjectProperty.number_of_units, LoanCore.loan_purpose, LoanCore.total_loan_amount_usd
**Missing data:** Evidence of selected prepayment structure, property state, and transaction details relevant to the printed state restrictions., Acra confirmation of what “BUY-OUT” requires and how a state restriction interacts with stated minimum terms.

## acra-standard.loan_program_eligibility.property_listed_for_sale

**Purpose:** Determine whether a property listed within the stated period meets the applicable loan conditions.

1. Step 1 - Initial Document Review: Review listing_history, loan_application, appraisal_report, and relevant lien and underwriting records for listing dates, occupancy, value, and loan terms.
2. Step 2 - Eligibility Verification: Treat a property as listed for sale if it was listed in the last six months, measured from the last date of being listed to the Application Date.
3. Step 3 - Validation and Verification: For a covered loan, verify that the property is not in default or delinquent on liens; an investment property is tenant-occupied and not vacant; qualification is ≥ 1.0 DSCR or 43% maximum DTI; PPP is at least three (3) years unless the property is in a state that does not allow prepayment penalties; reserves are twenty-four (24) months; the loan is fully amortizing and not interest only; maximum LTV / CLTV is 65% based on the lesser of appraised value or lowest recent listing price; no subordinate financing is allowed; and impounds are required.
4. Step 4 - Final Determination: Determine whether the applicable listed-property conditions are met.

**Checks:**
- The property was listed for sale within the last six months as measured from the last listing date to the Application Date.
- The property is not in default or otherwise delinquent on lien(s).
- For an investment property, the subject is occupied by a tenant and is not vacant.
- The loan qualifies as either ≥ 1.0 DSCR or 43% maximum DTI.
- The loan has a prepayment penalty of at least three (3) years unless the property is in a state that does not allow prepayment penalties.
- Reserves are twenty-four (24) months.
- The loan is fully amortizing and is not interest only.
- LTV / CLTV does not exceed 65% based on the lesser of appraised value or lowest recent listing price.
- No subordinate financing is allowed and impounds are required.

**Reads:** SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.is_listed_for_sale, SubjectProperty.is_vacant, SubjectProperty.has_current_lease, LoanCore.cltv_percent, LoanCore.prepayment_penalty_structure, MortgageLoanInformation.is_interest_only, RatioSet.reserves_months
**Missing data:** Application Date and last date of being listed., Lien status, tenant occupancy, qualification result, PPP, subordinate financing status, impound requirement, appraised value, and lowest recent listing price., Applicable state determination for whether it allows prepayment penalties.

## acra-standard.loan_program_eligibility.seller_contributions

**Purpose:** Determine whether seller concessions or other contributions are within the published limit.

1. Step 1 - Initial Document Review: Review the loan_application for the sale price and seller concessions or other contributions.
2. Step 2 - Eligibility Verification: Apply the 3% of sale price limit.
3. Step 3 - Validation and Verification: Verify the reported contribution amount against the sale price and applicable limit.
4. Step 4 - Final Determination: Determine whether the contribution limit is met.

**Checks:**
- Seller concessions or other contributions do not exceed 3% of the sale price.

**Reads:** LoanCore.seller_concession_percent
**Missing data:** Sale price., Seller-concession or other-contribution amount.

## acra-standard.loan_program_eligibility.vacant_property_refinance

**Purpose:** Determine whether a vacant-property refinance meets the conditions stated for its refinance type.

1. Step 1 - Initial Document Review: Review the loan_application, appraisal_report, and credit_report for vacancy, refinance type, loan amount, FICO, CLTV, and loan terms.
2. Step 2 - Eligibility Verification: Apply the rate & term refinance conditions: minimum 700 FICO; maximum $1,000,000 to maximum 70% CLTV; maximum $2,000,000 to maximum 65% CLTV; minimum 1.000 DSCR or maximum 40.0% DTI; minimum two-year prepayment penalty (where allowable); full amortization, no interest-only programs; impounds; and minimum six months reserves. Apply the stated cash-out refinance summary conditions: minimum 700 FICO; DSCR ≥ 1.15; ≥ 3-year PPP (where allowable); no interest only; impounds; 6 months reserves; maximum CLTV 60% for loan amounts under $1,500,000; and ≥15 months ownership.
3. Step 3 - Validation and Verification: Verify each applicable requirement. Refer the exact $1,000,000 and $2,000,000 rate & term treatment, cash-out loans of $1,500,000 or more, and how the 15 months are measured for Acra confirmation; the source does not resolve these points.
4. Step 4 - Final Determination: Determine whether the stated conditions are met or whether an unresolved limit or measurement requires confirmation.

**Checks:**
- A vacant-property refinance satisfies its applicable stated FICO, CLTV, loan amount, qualification, prepayment, amortization, impound, reserve, and ownership conditions.
- An unresolved exact loan-amount boundary, cash-out amount of $1,500,000 or more, or ownership-period measurement is referred for Acra confirmation.

**Reads:** SubjectProperty.is_vacant, LoanCore.loan_purpose, LoanCore.total_loan_amount_usd, CreditReport.representative_score, LoanCore.cltv_percent, MortgageLoanInformation.is_interest_only, LoanCore.prepayment_penalty_structure, RatioSet.reserves_months
**Missing data:** DSCR or DTI result, applicable PPP, impound requirement, and evidence of reserves and ownership period., Acra confirmation for treatment at exactly $1,000,000 and $2,000,000, cash-out loans of $1,500,000 or more, and how the 15 months are measured.

## acra-standard.property_tax_calculation.dscr_calculation

**Purpose:** Calculate DSCR with annual real estate taxes included in the denominator.

1. Step 1 - Initial Document Review: Gather the data needed for the DSCR calculation: annual in-place rent, market rent, the annual denominator amounts, and the first payment due under the terms of the Note. Identify whether the loan is interest-only.
2. Step 2 - Eligibility Verification: Use the lesser of annual in-place rent or market rent as the numerator. Include annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees in the denominator; include subordinate financing if applicable.
3. Step 3 - Validation and Verification: Divide the numerator by the denominator. If the loan is interest-only, obtain Acra confirmation of which payment enters the denominator. Apply the market rent reference §14.14 only when its applicable method is available; it is not reproduced in the excerpt.
4. Step 4 - Final Determination: Record the DSCR only when the required amounts and applicable calculation basis are available. Do not treat the subordinate-financing calculation rule as establishing that subordinate financing is permitted.

**Checks:**
- The numerator is the lesser of annual in-place rent or market rent.
- The denominator includes annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees.
- Subordinate financing is included in the denominator if applicable.
- The DSCR is the numerator divided by the denominator.
- The first payment due under the terms of the Note is used, subject to Acra confirmation of the payment basis for an interest-only loan.

**Reads:** MortgageLoanInformation.is_interest_only
**Missing data:** Annual in-place rent., Market rent and the applicable §14.14 method., Annual principal., Annual interest., Annual real estate taxes., Annual property insurance., Annual homeowner's / condominium association fees., Subordinate financing amount, if applicable., The first payment due under the terms of the Note., Acra confirmation of which payment enters the denominator for an interest-only loan, if applicable.

## acra-standard.title_review.additional_trust_documentation

**Purpose:** Determine whether any additional supporting documentation Legal conditions for has been provided.

1. Initial Document Review: Review the trust file and any conditions from Legal.
2. Eligibility Verification: Determine whether Legal has exercised its right to condition for additional supporting documentation.
3. Validation and Verification: If Legal has conditioned for additional supporting documentation, obtain and review the specified supporting documentation.
4. Final Determination: Record whether all additional documentation conditions have been cleared or no additional documentation was conditioned for.

**Checks:**
- If Legal has conditioned for additional supporting documentation, the specified supporting documentation has been provided.

**Reads:** Borrower.entity_type
**Missing data:** Whether Legal has conditioned for additional supporting documentation and, if so, the specified documentation.

## acra-standard.title_review.approved_title_and_closing_agent

**Purpose:** Determine whether the loan is closed with a title and closing agent approved and/or vetted by Acra.

1. Initial Document Review: Review the title and closing agent information and the closing file.
2. Eligibility Verification: Identify the title and closing agent for the loan.
3. Validation and Verification: Verify from Acra's records or title agent verification that the agent is approved and/or vetted by Acra.
4. Final Determination: Record whether the loan is closed with an approved and/or vetted agent.

**Checks:**
- The title and closing agent is approved and/or vetted by Acra.
**Missing data:** Acra's approval or vetting confirmation for the title and closing agent.

## acra-standard.title_review.business_entity_transaction

**Purpose:** Determine whether the business entity financing is for a business purpose transaction on investment properties exclusively.

1. Initial Document Review: Review the loan application and entity documents for the borrower type, transaction purpose, and subject-property use.
2. Eligibility Verification: Determine whether the borrower is a Business Entity and whether the transaction is a business purpose transaction on investment properties exclusively.
3. Validation and Verification: Compare the borrower type, loan purpose, and occupancy subtype recorded for the case with the reviewed documents.
4. Final Determination: Record whether the business entity transaction meets the stated eligibility requirement.

**Checks:**
- The borrower is a Business Entity.
- The transaction is a business purpose transaction on investment properties exclusively.

**Reads:** Borrower.entity_type, LoanCore.loan_purpose, SubjectProperty.occupancy_subtype

## acra-standard.title_review.closing_identification

**Purpose:** Determine whether the required identification copy is in the closing file.

1. Initial Document Review: Obtain and review a copy of the current Passport, Visa, or ITIN.
2. Eligibility Verification: Determine whether the copy is of a current Passport, Visa, or ITIN.
3. Validation and Verification: Verify the submitted copy is legible and identifies the document provided.
4. Final Determination: Record whether the required copy is present.

**Checks:**
- A copy of a current Passport, Visa, or ITIN is present.
**Missing data:** A copy of a current Passport, Visa, or ITIN.

## acra-standard.title_review.direct_title_owners

**Purpose:** Determine whether all entities that will hold direct ownership of the subject property and be on title as a direct owner are borrowing entities.

1. Initial Document Review: Review the title commitment and entity documents to identify direct owners of the subject property.
2. Eligibility Verification: Identify each entity that will hold direct ownership and be on title as a direct owner.
3. Validation and Verification: Compare the identified direct owners with the borrowing entities in the loan documents.
4. Final Determination: Record whether every such entity is a borrowing entity.

**Checks:**
- Every entity that will hold direct ownership of the subject property and be on title as a direct owner is a borrowing entity.

**Reads:** Borrower.entity_type
**Missing data:** The identity of each direct owner of the subject property and whether each is a borrowing entity, as established by the title commitment and entity documents.

## acra-standard.title_review.entity_owner_guarantees

**Purpose:** Determine whether an entity borrower has the required recourse guarantees from individuals with direct or indirect ownership ≥ 20%.

1. Initial Document Review: Review entity ownership records and the executed guarantees.
2. Eligibility Verification: Identify each individual with direct or indirect ownership ≥ 20% of the entity borrower.
3. Validation and Verification: Verify that each identified individual provided an Acra approved recourse guarantee or Exhibit 7; where there are multiple guarantors, verify that all recourse is joint and several.
4. Final Determination: Record whether the required guarantees are in place for all identified individuals.

**Checks:**
- Each individual with direct or indirect ownership ≥ 20% provided a recourse guarantee that is Acra approved or is Exhibit 7.
- If there are multiple guarantors, all recourse is joint and several.

**Reads:** Borrower.entity_type
**Missing data:** Direct and indirect ownership percentages; the identity of each individual at ≥ 20%; executed guarantee forms and whether they are Acra approved or Exhibit 7; and whether multiple guarantors' recourse is joint and several.

## acra-standard.title_review.entity_title_approval

**Purpose:** Determine whether an entity that holds title to the collateral is acceptable to Acra in its sole discretion.

1. Initial Document Review: Review the title commitment and entity documents to identify the proposed title holder.
2. Eligibility Verification: Determine whether title to the collateral will be held by an individual person or an entity.
3. Validation and Verification: If an entity will hold title, obtain and review Acra's determination of whether that entity is acceptable in its sole discretion.
4. Final Determination: Record whether the title holder meets the stated requirement.

**Checks:**
- The collateral title is held either directly by an individual person or by an entity acceptable to Acra in its sole discretion.

**Reads:** Borrower.entity_type
**Missing data:** Identity of each proposed title holder and Acra's determination whether an entity title holder is acceptable.

## acra-standard.title_review.executed_w8_form

**Purpose:** Determine whether the required executed W-8 (BEN) IRS form is in the closing file.

1. Initial Document Review: Obtain and review the W-8 (BEN) IRS form.
2. Eligibility Verification: Determine whether the form is executed.
3. Validation and Verification: Verify the form is the W-8 (BEN) IRS form and bears execution.
4. Final Determination: Record whether the executed form is present.

**Checks:**
- An executed W-8 (BEN) IRS form is present.
**Missing data:** The executed W-8 (BEN) IRS form.

## acra-standard.title_review.foreign_document_notarization

**Purpose:** Determine whether documents signed outside the U.S. have the required notarization and acknowledgment for the applicable signing location.

1. Initial Document Review: Identify documents signed outside the U.S., where they were signed, and the acknowledgment and authentication attached to each.
2. Eligibility Verification: Determine whether the signing country is a party to the Hague Convention Treaty Abolishing the Requirement of Legalization for Foreign Public Documents.
3. Validation and Verification: For documents signed outside the U.S., verify either that a U.S. embassy or consular official notarized them and the certificate of acknowledgement includes the embassy or consular seal and is acceptable to the title company, or, for a Hague Convention country, that an authorized notary public completed and signed the certificate of acknowledgment, authentication by apostille in English is attached to the executed documents, and the title company accepts it.
4. Final Determination: Record whether the applicable acknowledgment route and title company acceptance requirements are met.

**Checks:**
- If documents were signed outside the U.S. before a U.S. embassy or consular official, the certificate of acknowledgement includes the embassy or consular seal.
- If documents were signed outside the U.S. before a U.S. embassy or consular official, the certificate of acknowledgement is acceptable to the title company.
- If documents were signed in a country that is a party to the Hague Convention Treaty Abolishing the Requirement of Legalization for Foreign Public Documents, an authorized notary public completed and signed the certificate of acknowledgment.
- For documents signed in a Hague Convention country, authentication by apostille in English is attached to the executed documents.
- For documents signed in a Hague Convention country, the title company accepts the acknowledgment and apostille.
**Missing data:** Whether documents were signed outside the U.S.; country of signing and its Hague Convention status; notarization and certificate of acknowledgment; embassy or consular seal if applicable; apostille in English attached to executed documents if applicable; and title company acceptance.

## acra-standard.title_review.ownership_change_lookback

**Purpose:** Determine whether changes to operating agreements or bylaws intended to change ownership percentages to circumvent required personal guarantors occurred within the stated lookback period or during the application process.

1. Initial Document Review: Review the operating agreement or bylaws and their change history.
2. Eligibility Verification: Determine whether a change was intended to change ownership percentages to circumvent required personal guarantors.
3. Validation and Verification: Compare the effective dates of any such changes with the 30 days prior to an Application Date and the application process.
4. Final Determination: Do not recognize a change within the stated period and record the resulting ownership percentages for guarantee review.

**Checks:**
- No change to the operating agreement or bylaws intended to change ownership percentages to circumvent required personal guarantors occurred within 30 days prior to an Application Date or throughout the application process.

**Reads:** Borrower.entity_type
**Missing data:** Purpose and effective date of each relevant operating agreement or bylaw change; Application Date; and application-process dates.

## acra-standard.title_review.permitted_entity_type

**Purpose:** Determine whether the entity or guarantor type is permitted, including the restriction on series limited liability companies.

1. Initial Document Review: Review the entity documents for the entity or guarantor's legal type and formation details.
2. Eligibility Verification: Compare the legal type with the types allowed by the guidelines: Domestic Corporations (C and S Corp); single purpose Limited Liability Companies (LLC), excluding series LLC; Limited Liability Partnership (LLP); Limited Liability Limited Partnership (LLLP); General Partnership (GP); Limited Partnership (LP); and Sole Proprietorship.
3. Validation and Verification: Verify the legal type and whether an LLC is a series LLC from the entity documents.
4. Final Determination: Record whether the type is allowed.

**Checks:**
- The entity or guarantor type is one of the types allowed by the guidelines.
- If the type is a Limited Liability Company, it is not a series LLC.

**Reads:** Borrower.entity_type
**Missing data:** Entity or guarantor's legal type and whether a Limited Liability Company is a series LLC, as established by the entity documents.

## acra-standard.title_review.power_of_attorney

**Purpose:** Determine whether a Power of Attorney, if provided, meets both stated acceptability requirements.

1. Initial Document Review: Review any Power of Attorney in the closing file.
2. Eligibility Verification: Determine whether a Power of Attorney is being used.
3. Validation and Verification: If provided, verify that it conforms to Acra requirements and is acceptable to the title company.
4. Final Determination: Record whether the Power of Attorney meets both requirements or is not being used.

**Checks:**
- If a Power of Attorney is provided, it conforms to Acra requirements.
- If a Power of Attorney is provided, it is acceptable to the title company.
**Missing data:** Whether a Power of Attorney is used; Acra's requirements for the Power of Attorney; and title company acceptance.

## acra-standard.title_review.single_purpose_entity

**Purpose:** Determine whether an entity borrower meets the SPE requirement.

1. Initial Document Review: Review the entity documents for the entity's assets and business activities.
2. Eligibility Verification: Verify that the entity has no assets other than residential investment or rental properties and is engaged in owning and operating residential investment or rental properties.
3. Validation and Verification: Verify from the entity documents whether the entity is a series limited liability company.
4. Final Determination: Record whether the entity satisfies the SPE requirement and is not a series limited liability company.

**Checks:**
- The entity has no assets other than residential investment or rental properties.
- The entity is engaged in the business of owning and operating residential investment or rental properties.
- The entity is not a series limited liability company.

**Reads:** Borrower.entity_type
**Missing data:** The entity's assets, business activities, and whether it is a series limited liability company, as established by the entity documents.

## acra-standard.title_review.trust_documentation

**Purpose:** Determine whether the required trust document or certification and all listed trust details are present.

1. Initial Document Review: Review the complete, legible Trust copy or Certification of Trust.
2. Eligibility Verification: Determine whether the file contains one of those document forms.
3. Validation and Verification: Verify that the document states the existence and date of the Trust; Trustor(s) and current Trustee(s); Trustee powers; revocability and, if revocable, who holds the right to revoke; names and number of Trustees required to sign on behalf of the Trust; Trust identification number (a Social Security number or an IRS-issued Tax Identification Number); how title to Trust assets should be taken; and that the Trust has not been revoked, modified, or amended in any manner.
4. Final Determination: Record whether the Trust document or Certification of Trust is complete, legible, and includes every required item.

**Checks:**
- A complete, legible copy of the Trust or a Certification of Trust is provided.
- The Trust document or Certification of Trust states the existence and date of the Trust.
- The Trust document or Certification of Trust states the Trustor(s) and current Trustee(s).
- The Trust document or Certification of Trust states the powers of the Trustee.
- The Trust document or Certification of Trust states whether the Trust is revocable and, if revocable, who holds the right to revoke.
- The Trust document or Certification of Trust states the names and number of the Trustees required to sign on behalf of the Trust.
- The Trust document or Certification of Trust states the Trust identification number, which is a Social Security number or an IRS-issued Tax Identification Number.
- The Trust document or Certification of Trust states how title to the Trust assets should be taken.
- The Trust document or Certification of Trust states that the Trust has not been revoked, modified, or amended in any manner.

**Reads:** Borrower.entity_type
**Missing data:** A complete, legible Trust copy or Certification of Trust and each required statement in it.

## acra-standard.title_review.trust_validity_and_structure

**Purpose:** Determine whether the trust meets the stated validity, revocability, establishment, and primary beneficiary requirements.

1. Initial Document Review: Review the Trust or Certification of Trust for governing state, revocability, trustors, effective date, and beneficiaries.
2. Eligibility Verification: Verify that the Trust is valid under the laws of the state in which it is established; is revocable; was established by one or more natural persons, solely or jointly; and became effective during the lifetime of the person(s) establishing it.
3. Validation and Verification: Verify that the primary beneficiary of the Trust is the individual(s) establishing the Trust.
4. Final Determination: Record whether every stated trust structure requirement is met.

**Checks:**
- The Trust is valid under the laws of the state in which it is established.
- The Trust is revocable and can be changed or canceled at any time for any reason during a Trustor's lifetime.
- The Trust was established by one or more natural persons, solely or jointly.
- The Trust became effective during the lifetime of the person(s) establishing it.
- The primary beneficiary of the Trust is the individual(s) establishing the Trust.

**Reads:** Borrower.entity_type
**Missing data:** State of establishment and evidence of validity under that state's law; Trust revocability and terms; identity and status of establishing persons; effective date; and primary beneficiary.

## acra-standard.title_review.trustee_powers_and_lender_rights

**Purpose:** Determine whether the Trust contains all required terms concerning mortgage authority, beneficiary consent, risk, and lender rights.

1. Initial Document Review: Review the Trust for provisions concerning Trustee authority, beneficiary consent, lender risk, and creditor rights.
2. Eligibility Verification: Determine whether the Trust specifies that the Trustee has power to hold title and mortgage the property.
3. Validation and Verification: Verify that the Trust specifies either that the beneficiary does not need to grant written consent for the Trust to borrow money or that consent has been granted in writing for purposes of the mortgage; that there is no unusual risk or impairment to the lender's rights; and that holding title in the Trust does not diminish the lender's rights as a creditor.
4. Final Determination: Record whether all required terms are specified.

**Checks:**
- The Trust specifies that the Trustee has the power to hold title and mortgage the property.
- The Trust specifies that the beneficiary does not need to grant written consent for the Trust to borrow money, or that such consent has been granted in writing for purposes of the mortgage.
- The Trust specifies that there is no unusual risk or impairment to the lender's rights.
- The Trust specifies that holding title in the Trust does not diminish the lender's rights as a creditor.

**Reads:** Borrower.entity_type
**Missing data:** Trust provisions on Trustee powers, beneficiary consent, unusual risk or impairment to lender rights, and whether trust title diminishes lender rights as a creditor.

## acra-standard.title_review.trustor_trustee_exception

**Purpose:** Determine whether the required written exception is present when the Trustor(s) and Trustee(s) differ.

1. Initial Document Review: Review the Trust or Certification of Trust to identify the Trustor(s) and Trustee(s).
2. Eligibility Verification: Determine whether the Trustor(s) and Trustee(s) are the same.
3. Validation and Verification: If they are not the same, obtain and verify written exception by Acra Senior Management.
4. Final Determination: Record whether the exception requirement is satisfied or whether no exception is required.

**Checks:**
- If the Trustor(s) and Trustee(s) are not the same, written exception by Acra Senior Management has been obtained.

**Reads:** Borrower.entity_type
**Missing data:** Identity of the Trustor(s) and Trustee(s), and written exception by Acra Senior Management if they are not the same.

## acra-standard.title_review.us_entity_status

**Purpose:** Determine whether the entity borrower meets the US formation, location, and ownership restriction.

1. Initial Document Review: Review the entity documents for the entity's place of formation, place of business, and ownership.
2. Eligibility Verification: Verify that the borrower is a US formed and based Entity and is not a foreign entity or foreign owned entity.
3. Validation and Verification: Confirm the formation, base, and ownership information in the entity documents.
4. Final Determination: Record whether the borrower meets the US entity restriction.

**Checks:**
- The borrower is a US formed and based Entity and is not a foreign entity or foreign owned entity.

**Reads:** Borrower.entity_type
**Missing data:** Entity formation location, entity base, and whether the entity is foreign owned, as established by the entity documents.
