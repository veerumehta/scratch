# Our jobs, standard (65)

## acra-standard.borrower_citizenship_and_foreign_national_requirements.review_foreign_national_program_eligibility_and_restrictions

**Purpose:** Establish whether a Foreign National or qualifying ITIN borrower meets the foreign-national program requirements stated in the section.

1. Determine whether the Foreign National or ITIN borrower meets the stated residence and authorization requirements.
2. Verify that the transaction is business purpose and concerns an investment property.
3. Apply the stated Foreign National CLTV limit for the transaction type and the stated FICO pricing requirement.
4. Check the escrow-waiver restriction and resolve the stated Credit Requirements restriction question.
5. Review the required post-close financial position and ability to mitigate exchange-rate fluctuations.
6. Review the referenced OFAC restrictions and state-specific exclusions.

**Checks:**
- A Foreign National is a Non-Resident Alien not authorized to live or work in the U.S. and resides outside of the U.S.; an ITIN holder is eligible under this program only if the borrower resides outside of the U.S.
- The transaction is business purpose and is an investment property.
- For a Foreign National, CLTV is no more than 70% for purchase or 65% for refinance — rate & term and cash-out.
- For a Foreign National, the loan is priced at FICO equal to 700.
- A Foreign National is not receiving an escrow waiver.
- Acra has confirmed the scope of the Credit Requirements panel’s statement “Foreign National ineligible”.
- The applicant’s post-close financial position and ability to mitigate exchange rate fluctuations have been reviewed with scrutiny.
- The applicable OFAC restrictions and state-specific exclusions have been reviewed.

**Reads:** citizenship_type, loan_purpose, occupancy_subtype, cltv_pct, escrow_waiver_requested, property_state, fico
**Missing data:** Whether the borrower resides outside the U.S., Whether a Foreign National is authorized to live or work in the U.S., Whether the transaction is business purpose and the property is an investment property, if not established by the case fields, Loan pricing basis showing pricing at FICO equal to 700, Acra confirmation of the scope of “Foreign National ineligible” under Credit Requirements, Post-close financial position, Applicant’s ability to mitigate exchange-rate fluctuations, OFAC restrictions referred to in §3.10, State-specific exclusions referred to in §3.10

## acra-standard.borrower_citizenship_and_foreign_national_requirements.verify_citizenship_type_and_citizenship_specific_requirements

**Purpose:** Establish whether the borrower has an eligible citizenship type and meets the requirements stated for that type.

1. Check that the borrower’s citizenship type is one of the eligible types.
2. For a Permanent Resident, verify the required identification and Social Security documentation.
3. For a Non-Permanent Resident, verify proof of legal residency and resolve the stated limit interpretation.
4. For an ITIN borrower, check the stated loan amount, FICO, and CLTV limits, and resolve the stated eligibility and tier questions.
5. For an ITIN borrower, verify that scores and tradelines are reported under the correct ITIN or SSN.

**Checks:**
- citizenship_type is one of: US Citizen, Permanent Resident, Non-Permanent Resident, Foreign National, ITIN.
- If citizenship_type is Permanent Resident, the borrower has an unexpired PRA ID and SSA card / SSA-89.
- If citizenship_type is Non-Permanent Resident, the borrower has proof of legal residency, which may include an unexpired employment authorization document (EAD) or valid visa.
- If citizenship_type is Non-Permanent Resident, Acra has confirmed how to apply the printed limit “Max Loan Amount: $1.5M: Max CLTV 80%”.
- If citizenship_type is ITIN, loan_amount is no more than $1.0M.
- If citizenship_type is ITIN, FICO is at least 640.
- If citizenship_type is ITIN, CLTV meets the printed tier for the applicable FICO and transaction: “FICO 700” is 70% purchase and 65% refinance — R/T and cash-out; “FICO 660 to 699” is 65% purchase and 60% refinance — R/T and cash-out; “FICO 640 to 659” is 60% purchase and 60% refinance — R/T and cash-out.
- If citizenship_type is ITIN, Acra has confirmed whether a US-resident ITIN holder is eligible and whether the tier printed “FICO 700” means 700 and above.
- If citizenship_type is ITIN, scores and tradelines are reported under the correct ITIN or SSN to meet requirements.

**Reads:** citizenship_type, loan_amount, fico, cltv_pct, loan_purpose
**Missing data:** Unexpired PRA ID, SSA card or SSA-89, Proof of legal residency, Acra confirmation of how to apply “Max Loan Amount: $1.5M: Max CLTV 80%”, Acra confirmation of whether a US-resident ITIN holder is eligible and whether “FICO 700” means 700 and above, Documentation showing the scores and tradelines are reported under the correct ITIN or SSN, Borrower’s residence in or outside the United States, if needed for the ITIN eligibility question

## acra-standard.borrower_citizenship_and_foreign_national_requirements.verify_foreign_national_closing_documents

**Purpose:** Establish that the Foreign National’s required closing documents and any applicable signing formalities meet the stated requirements.

1. Verify a copy of the required current identity or tax document.
2. Verify the title and closing agent is approved and / or vetted by Acra.
3. If a Power of Attorney is used, verify its acceptability under Acra requirements and to the title company.
4. Verify an executed W-8 (BEN) IRS form.
5. If documents are signed outside the U.S., verify the applicable stated notarization and title-company acceptance requirements.

**Checks:**
- A copy of a current Passport, Visa, or ITIN is provided.
- The loan closes with a title and closing agent approved and / or vetted by Acra.
- If a Power of Attorney is used, it conforms to Acra requirements and is acceptable to the title company.
- An executed W-8 (BEN) IRS form is provided.
- For documents signed outside of the U.S. and notarized by a U.S. embassy or consular official, the certificate of acknowledgement includes the embassy or consular seal and is acceptable to the title company.
- For documents signed in a country that is party to the Hague Convention Treaty Abolishing the Requirement of Legalization for Foreign Public Documents, the certificate of acknowledgment is completed and signed by an authorized notary public, authenticated by apostille in English, attached to the executed documents, and acceptable to the title company.

**Reads:** citizenship_type
**Missing data:** Copy of current Passport, Visa, or ITIN, Acra approval or vetting of the title and closing agent, Power of Attorney, if used, Evidence that the Power of Attorney conforms to Acra requirements, Title-company acceptance of the Power of Attorney, if used, Executed W-8 (BEN) IRS form, Whether documents are signed outside of the U.S., Embassy or consular notarization and certificate of acknowledgement, if that route is used, Whether the signing country is party to the Hague Convention Treaty Abolishing the Requirement of Legalization for Foreign Public Documents, Authorized-notary certificate of acknowledgment, English apostille, attachment to executed documents, and title-company acceptance, if the Hague Convention route is used

## acra-standard.borrower_citizenship_and_foreign_national_requirements.verify_foreign_national_credit_references

**Purpose:** Establish that the Foreign National satisfies one of the permitted credit-reference alternatives.

1. Determine whether at least one of the four stated credit-reference alternatives is documented.
2. If relying on a U.S. credit report, verify its trade-line count and the minimum age of one trade line.

**Checks:**
- At least one of the following is documented: a U.S. credit report with at least two (2) trade lines and a minimum age of two (2) years for one trade line; an international credit report; an original credit reference letter from an internationally known financial institution; or a bank statement documenting a foreign financial banking relationship for the past 60 days.
- If relying on a U.S. credit report, it has at least two (2) trade lines and one trade line has a minimum age of two (2) years.

**Reads:** citizenship_type
**Missing data:** U.S. credit report and trade-line ages, if used, International credit report, if used, Original credit reference letter from an internationally known financial institution, if used, Bank statement documenting a foreign financial banking relationship for the past 60 days, if used

## acra-standard.borrower_citizenship_and_foreign_national_requirements.verify_foreign_national_funds_and_account_documentation

**Purpose:** Establish that foreign-national funds meet the stated verification, deposit, seasoning, and documentation requirements.

1. Verify foreign-account assets in U.S. Dollar equivalency using the current exchange rate from www.xe.com or the Wall Street Journal conversion table.
2. Verify sufficient funds to close are on deposit with the Escrow / Closing Agent at least three (3) business days before closing, counting Saturdays for this calculation.
3. Verify the required seasoning and, for funds held in a foreign bank / currency, repatriation timing.
4. Review the account statements and, if funds are not seasoned a minimum of sixty (60) days, the required letter of explanation and chain of funds.
5. Verify English translations for bank statements in any language other than English.

**Checks:**
- Assets held in foreign accounts are verified in U.S. Dollar equivalency at the current exchange rate via www.xe.com or the Wall Street Journal conversion table.
- Sufficient funds to close are on deposit with the Escrow / Closing Agent at least three (3) business days prior to any closing date, including Saturdays for this calculation.
- Foreign Nationals document a minimum of 60 days seasoning, regardless of LTV / CLTV.
- Funds held in a foreign bank / currency are repatriated at minimum three (3) business days prior to Closing.
- A copy of the two (2) most recent statements of the account is provided.
- If funds are not seasoned a minimum of sixty (60) days, a letter of explanation is provided along with the information to comprise a sixty (60) day chain of funds.
- Bank statements in any language other than English are translated into English.

**Reads:** citizenship_type, cltv_pct
**Missing data:** Foreign account statements and balances, Current exchange rate from www.xe.com or the Wall Street Journal conversion table, Funds required to close, Closing date and deposit date, Evidence of funds’ seasoning period, Evidence of foreign-bank / currency funds repatriation date, Two most recent statements of the account, Letter of explanation, if funds are not seasoned a minimum of sixty (60) days, Information comprising a sixty (60) day chain of funds, if required, English translation of bank statements not in English

## acra-standard.credit_housing_history_and_escrow_waiver.apply_mortgage_history_restrictions

**Purpose:** Apply the mortgage history restrictions and their printed CLTV limits.

1. Identify the applicable printed mortgage-history label and the loan purpose.
2. Apply the printed maximum CLTV for that label and purpose: 1x30x12 — 80% Purchase, 75% Refi R/T, Refi C/O; 0x60x12 — 75% Purchase, 70% Refi R/T, Refi C/O; 0x90x12 — 65% for both; 0x120x12 — Ineligible for both.
3. Confirm the applicable CLTV does not exceed the printed maximum, or that the case is not in a category printed as Ineligible.

**Checks:**
- The applicable printed mortgage-history label and loan-purpose column permit the case's CLTV; 0x120x12 is Ineligible.

**Reads:** housing_history, loan_purpose, cltv_pct
**Missing data:** Applicable printed mortgage-history label, Acra definitions of the mortgage-history labels and how seasoning is measured, Loan-purpose classification as Purchase, Refi R/T, or Refi C/O

## acra-standard.credit_housing_history_and_escrow_waiver.identify_separate_impound_requirements

**Purpose:** Check the impound requirements stated separately for first-time homebuyers, vacant-property refinances, and properties listed for sale, without resolving their interaction with an otherwise eligible escrow waiver.

1. Check whether the borrower is a first-time homebuyer; impounds are separately required for first-time homebuyers.
2. For a refinance of a vacant property, check that impounds are required.
3. For a property listed for sale, check that impounds are required.
4. If an otherwise eligible escrow waiver is requested in any applicable circumstance, obtain Acra confirmation on how the separate impound requirement interacts with the waiver.

**Checks:**
- If the borrower is a first-time homebuyer, the separately stated impound requirement is met.
- If the loan is a refinance of a vacant property, the separately stated impound requirement is met.
- If the property is listed for sale, the separately stated impound requirement is met.
- Where an otherwise eligible waiver and a separate impound requirement coincide, their interaction is confirmed by Acra.

**Reads:** first_time_homebuyer, vacant_property, loan_purpose, property_currently_listed_for_sale, escrow_waiver_requested
**Missing data:** Impound status, Acra confirmation on how separately required impounds interact with an otherwise eligible waiver

## acra-standard.credit_housing_history_and_escrow_waiver.review_bankruptcy_and_foreclosure_restrictions

**Purpose:** Determine whether the case meets the bankruptcy and foreclosure restrictions for its loan purpose and CLTV.

1. Determine whether bankruptcy or foreclosure applies and identify its seasoning as printed.
2. For ≥ 36 Mo, apply No Restrictions; for 24-35 Mo, apply Max CLTV 80% Purchase or 75% Refi R/T, Refi C/O; for 12-23 Mo, apply Max CLTV 65% for both; for < 12 Mo, apply Ineligible.
3. For a seasoning band with a maximum CLTV, compare the case CLTV with the maximum for the loan purpose.

**Checks:**
- If bankruptcy or foreclosure applies, its printed seasoning band permits the case: ≥ 36 Mo is No Restrictions; 24-35 Mo has a maximum CLTV of 80% Purchase or 75% Refi R/T, Refi C/O; 12-23 Mo has a maximum CLTV of 65% for both; < 12 Mo is Ineligible.

**Reads:** bankruptcy_or_foreclosure, months_since_bankruptcy_or_foreclosure, loan_purpose, cltv_pct
**Missing data:** Loan-purpose classification as Purchase, Refi R/T, or Refi C/O

## acra-standard.credit_housing_history_and_escrow_waiver.review_escrow_waiver_eligibility

**Purpose:** Determine whether a requested escrow waiver meets the stated eligibility requirements.

1. If an escrow waiver is requested, check the maximum loan amount of $1.5M and maximum CLTV of 80%.
2. Check the minimum FICO of 700.
3. Check that mortgage history is no worse than 0x30x24.
4. Check that the borrower is not Foreign National.

**Checks:**
- If an escrow waiver is requested, loan amount is no greater than $1.5M.
- If an escrow waiver is requested, CLTV is no greater than 80%.
- If an escrow waiver is requested, FICO is at least 700.
- If an escrow waiver is requested, mortgage history is no worse than 0x30x24.
- If an escrow waiver is requested, the borrower is not Foreign National.

**Reads:** escrow_waiver_requested, loan_amount, cltv_pct, fico, mortgage_history_0x30x24, citizenship_type

## acra-standard.credit_housing_history_and_escrow_waiver.review_mortgage_and_rental_rating_history

**Purpose:** Determine whether the history needed to evaluate mortgage pricing and DSCR payment history has been documented for the properties specified by the guidelines.

1. Evaluate the ratings for properties the borrower owns and / or rents over the last twelve (12) months.
2. Consider all reported mortgages on credit.
3. Where the applicant has mortgages that are not reported, check that the file contains documentation to evaluate history on the applicant's primary residence(s), any secondary residence(s), and the subject property.
4. For DSCR loans, check documentation on the subject property, principal residence, and second home (if any) of the borrower and / or guarantor(s).
5. For DSCR loans, do not require housing history documentation for additional properties unless documents in the file suggest a major credit event has occurred.
6. For DSCR loans, check payment history for the primary residence, subject property, and second homes, if applicable.
7. For loans that have matured, rate the loan based on the maturity date; check that any extensions of the maturity date are in writing.

**Checks:**
- Ratings for properties the borrower owns and / or rents over the last twelve (12) months are evaluated.
- All reported mortgages on credit are considered.
- Where mortgages are not reported, the file contains documentation to evaluate history on the applicant's primary residence(s), any secondary residence(s), and the subject property.
- For a DSCR loan, documentation covers the subject property, principal residence, and second home (if any) of the borrower and / or guarantor(s).
- For a DSCR loan, additional properties are not required to have housing history documented unless documents in the file suggest a major credit event has occurred.
- For a DSCR loan, payment history is available for the primary residence, subject property, and second homes, if applicable.
- For a loan that has matured, the rating is based on the maturity date and any extension of the maturity date is in writing.

**Reads:** housing_history, loan_purpose, dscr_documentation_type
**Missing data:** Mortgage and rental ratings for properties owned and / or rented over the last twelve (12) months, Reported mortgage list, Documentation of history for any unreported mortgages on primary residence(s), secondary residence(s), and subject property, Whether the loan is a DSCR loan, Documentation of DSCR housing and payment history for the subject property, principal residence, and second home (if any), File documents indicating whether a major credit event has occurred on an additional property, Loan maturity date and written maturity-date extensions, if any

## acra-standard.credit_housing_history_and_escrow_waiver.review_scores_tradelines_and_reserves

**Purpose:** Determine whether the score and tradeline requirements are met, apply the stated overlays when applicable, and verify the reserve requirement for FICO below 620.

1. Review the number of repositories reporting scores and the tradeline information.
2. If there are scores from 3 repositories, apply the stated acceptable-with-no-tradeline-overlay treatment.
3. If there are 2 or fewer scores, check for either 2 tradelines & 24 month history or 3 tradelines & 12 month history.
4. If there is 1 or No Score / Deficient Tradelines, check each of the three printed entries: Max 65% LTV/CLTV; DSCR Ratio ≥ 1.1; 24mos 0x30 housing history.
5. Verify that scores & tradelines are reported under the correct ITIN or SSN.
6. If FICO is < 620, verify 12 months of reserves.

**Checks:**
- Applicants with scores from 3 repositories are treated as acceptable with no tradeline overlay.
- For applicants with 2 or fewer scores, either 2 tradelines & 24 month history or 3 tradelines & 12 month history is met.
- For 1 or No Score / Deficient Tradelines, CLTV is no greater than 65%.
- For 1 or No Score / Deficient Tradelines, DSCR Ratio is ≥ 1.1.
- For 1 or No Score / Deficient Tradelines, 24mos 0x30 housing history is met.
- Scores & tradelines are reported under the correct ITIN or SSN.
- If FICO is < 620, reserves are at least 12 months.

**Reads:** credit_score_count, tradelines_meet_requirement, cltv_pct, dscr_documentation_type, mortgage_history_0x30x24, fico, reserves_months
**Missing data:** Number of tradelines, Tradeline history duration, DSCR Ratio, Credit report showing whether the 24mos 0x30 housing history requirement is met, Credit-score and tradeline reports identifying the correct ITIN or SSN

## acra-standard.credit_housing_history_and_escrow_waiver.review_short_sale_deed_in_lieu_and_modification_restrictions

**Purpose:** Determine whether the case meets the printed restrictions for these previous credit events.

1. Determine whether a short sale, deed-in-lieu, or modification applies and identify its seasoning as printed.
2. For ≥ 24 Mo, apply No Restrictions; for 12-23 Mo, apply Max CLTV 80% Purchase or 75% Refi R/T, Refi C/O; for < 12 Mo, apply Max CLTV 75% Purchase or 70% Refi R/T, Refi C/O.
3. For a seasoning band with a maximum CLTV, compare the case CLTV with the maximum for the loan purpose.

**Checks:**
- If a short sale, deed-in-lieu, or modification applies, its printed seasoning band permits the case: ≥ 24 Mo is No Restrictions; 12-23 Mo has a maximum CLTV of 80% Purchase or 75% Refi R/T, Refi C/O; < 12 Mo has a maximum CLTV of 75% Purchase or 70% Refi R/T, Refi C/O.

**Reads:** short_sale_dil_or_modification, months_since_short_sale_dil_or_modification, loan_purpose, cltv_pct
**Missing data:** Loan-purpose classification as Purchase, Refi R/T, or Refi C/O

## acra-standard.cross_cutting_published_caps_and_score_thresholds.apply_published_cltv_caps

**Purpose:** Check the published CLTV caps and adjustments collected in this section; the section does not specify how to combine multiple applicable caps or adjustments.

1. Identify the applicable published cap row or rows using the case facts and the conditions stated in the tables.
2. For each applicable row, use the cap for the case's loan purpose (Purchase, Rate & Term, or Cash-Out). Preserve the table's stated amount and FICO bands, caps, and NA entries.
3. Compare the case's CLTV with the applicable cap or caps. Do not resolve the effect of multiple applicable caps or adjustments using this section; their combination is identified as Q-07.

**Checks:**
- For every applicable published cap row with a numeric cap, the case CLTV does not exceed that row's cap for the case's loan purpose.

**Reads:** cltv_pct, loan_purpose, loan_amount, fico, citizenship_type, credit_score_count, tradelines_meet_requirement, mortgage_history_0x30x24, bankruptcy_or_foreclosure, months_since_bankruptcy_or_foreclosure, short_sale_dil_or_modification, months_since_short_sale_dil_or_modification, rural_property, property_type, property_state, first_time_homebuyer, vacant_property, listed_for_sale_last_6_months, escrow_waiver_requested, interest_only_10_40, product_is_interest_only
**Missing data:** The Q-07 rule for how caps and adjustments combine when more than one applies., DSCR value or confirmation of No Ratio., Whether the rental is short-term., Whether the borrower is an ITIN borrower., Whether the property is a Non-Warrantable Condo, Condotel / PUDtel, or Manufactured Home; whether a property is unique; and the property classification needed to identify the applicable property-type row., Whether the property is in a declining market., Any other facts needed to establish the conditions of a published cap row that are not represented by the available case fields.

## acra-standard.cross_cutting_published_caps_and_score_thresholds.apply_published_minimum_fico_thresholds

**Purpose:** Check the minimum FICO thresholds collected in this section, distinguishing the Foreign National pricing statement from a stated minimum.

1. Identify which features in the published minimum-FICO table apply to the case, using the stated feature conditions and loan-amount bands.
2. For each applicable feature with a stated minimum, compare the case FICO with that minimum.
3. Treat Foreign National as “Priced at FICO 700; no minimum stated”; do not treat that entry as a stated minimum FICO threshold.

**Checks:**
- For every applicable feature with a stated minimum FICO, the case FICO is at least that minimum.

**Reads:** fico, loan_amount, interest_only_10_40, product_is_interest_only, first_time_homebuyer, vacant_property, loan_purpose, rural_property, citizenship_type
**Missing data:** DSCR value or confirmation of No Ratio., Whether the rental is short-term., Whether the borrower is an ITIN borrower., Any facts needed to establish a listed feature that are not represented by the available case fields.

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.apply_ratio_dependent_qualification_conditions

**Purpose:** Check the ratio-dependent minimums and restrictions collected in the program provisions.

1. Determine which stated situations apply: LTV above 80.00%; loan amount over $2,000,000; 1 or no score / deficient tradelines; rural / unique property; non-warrantable condo or condotel / PUDtel; first-time homebuyer; vacant property refinance purpose; property listed for sale within six months; or mixed use, adult care or assisted living.
2. For each applicable situation, compare DSCR with the stated minimum.
3. For LTV above 80.00%, also check the stated 6 months PITIA reserves and property-type limitation: SFR, Warrantable Condos outside of Florida, Townhome, PUD.

**Checks:**
- If LTV is above 80.00%, DSCR is at least 1.20.
- If LTV is above 80.00%, reserves are 6 months PITIA.
- If LTV is above 80.00%, the property is limited to SFR, Warrantable Condos outside of Florida, Townhome, PUD.
- If the loan amount is over $2,000,000, DSCR is at least 1.0.
- If there is 1 or no score / deficient tradelines, DSCR is at least 1.1.
- If the property is rural / unique, DSCR is at least 1.00.
- If the property is a non-warrantable condo; condotel / PUDtel, DSCR is at least 1.0.
- If the borrower is a first-time homebuyer, DSCR is at least 1.150.
- If the property is vacant and the transaction is a rate & term refinance, DSCR is at least 1.000 (“OR Maximum 40.0% DTI”).
- If the property is vacant and the transaction is a cash-out refinance, DSCR is at least 1.15.
- If the property was listed for sale within six months, DSCR is at least 1.0 (“or (b) 43% maximum DTI”).
- If the property is mixed use, adult care or assisted living, DSCR is at least 1.2.

**Reads:** loan_amount, credit_score_count, tradelines_meet_requirement, rural_property, property_type, first_time_homebuyer, vacant_property, loan_purpose, property_currently_listed_for_sale, listed_for_sale_last_6_months, mixed_use, cltv_pct, reserves_months, pitia, fico
**Missing data:** LTV, calculated DSCR, whether property is rural / unique, whether a condo is warrantable, whether the property is a condotel / PUDtel, whether the property is adult care or assisted living, whether the applicable DTI alternative is met, PITIA reserve amount and the reserve-month calculation

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.calculate_dscr

**Purpose:** Calculate the DSCR for a file where a ratio is calculated.

1. Identify annual in-place rent and market rent.
2. Use the lesser of those rent amounts as the numerator.
3. Determine the denominator from annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees; include subordinate financing if applicable.
4. Use the first payment due under the terms of the Note, then calculate the ratio.

**Checks:**
- The numerator is the lesser of annual in-place rent or market rent.
- The denominator includes annual principal, interest, real estate taxes, property insurance, and homeowner's / condominium association fees, plus subordinate financing if applicable.
- The calculation uses the first payment due under the terms of the Note.

**Reads:** dscr_documentation_type, gross_rental_income, pitia, interest_rate, product_is_interest_only, interest_only_10_40
**Missing data:** annual in-place rent, market rent, annual principal payment, annual interest payment, annual real estate taxes, annual property insurance, annual homeowner's / condominium association fees, subordinate financing amount, if applicable, first payment due under the Note

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.review_no_ratio_dscr_files

**Purpose:** Check No Ratio file requirements without calculating a DSCR.

1. Determine whether the file is designated No Ratio.
2. Do not calculate a DSCR for a No Ratio file; review the required 1007.
3. Do not require proof of actual rents under the No Ratio provision.
4. Apply the stated No Ratio maximum CLTV by transaction purpose and minimum FICO.

**Checks:**
- A No Ratio file does not have a calculated DSCR.
- A 1007 is provided for a No Ratio file.
- Proof of actual rents is not required for a No Ratio file.
- For No Ratio purchase, CLTV is no more than 75%.
- For No Ratio refinance — rate & term, CLTV is no more than 70%.
- For No Ratio refinance — cash-out, CLTV is no more than 65%.
- FICO is at least 640.

**Reads:** dscr_documentation_type, loan_purpose, cltv_pct, fico
**Missing data:** 1007, whether the transaction is rate & term or cash-out refinance

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.review_qualifying_rent_and_actual_rent_evidence

**Purpose:** Check the rent evidence requirements stated for actual rents without selecting between the section's differing rent formulations.

1. Determine whether actual rents exceed market rents.
2. If actual rents exceed market rents, review the proof of rental income receipt and lease agreement(s).
3. Confirm the receipt evidence covers two (2) consecutive months, the lease agreement(s) continue at a minimum of three (3) months after closing, and the rents are not prepaid; do not count a Security Deposit as receipt.

**Checks:**
- Where actual rents exceed market rents, evidence of actual rents is documented via two (2) consecutive months proof of rental income receipt.
- Where actual rents exceed market rents, lease agreement(s) continue at a minimum of three (3) months after closing.
- A Security Deposit is not counted towards receipt, and the rents are not prepaid.

**Reads:** gross_rental_income, current_lease_in_place, vacant_property, loan_purpose, dscr_documentation_type
**Missing data:** market rent, actual rent amount and rental period, two (2) consecutive months proof of rental income receipt, lease agreement(s) and their end date, closing date, whether any rent is prepaid, whether any amount counted as receipt is a Security Deposit

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.review_rent_support_for_excessive_lease_rents

**Purpose:** Check the stated support requirement when a lease reflects excessive monthly rent payments.

1. Determine whether the property is a single-family investment property and whether its lease reflects excessive monthly rent payments.
2. If so, review documentation supporting that the monthly rent is typical for the area.
3. Identify whether the support is classified ads from local newspapers, a 1007 completed by the appraiser, or a market rent survey completed by a local real estate company or rental management company familiar with rents in the area.

**Checks:**
- A single-family investment property with excessive monthly rent payments reflected on the lease has documentation supporting that the monthly rent is typical for the area.
- The documentation reviewed is one of the stated examples: classified ads from local newspapers, a 1007 completed by the appraiser, or a market rent survey completed by a local real estate company or rental management company familiar with the market rents in the area.

**Reads:** property_type, residential_unit_count, occupancy_subtype, current_lease_in_place, gross_rental_income
**Missing data:** whether the property is an investment property, lease and monthly rent amount, whether the lease rent is excessive, documentation supporting typical rent for the area, local market rent information, identity and familiarity with the area of the real estate company or rental management company

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.review_required_rent_schedules

**Purpose:** Check when a Single-Family Comparable Rent Schedule is required and whether the 1007 is from an allowed appraiser.

1. Determine whether the property is single family and whether the file is a DSCR qualifying file.
2. For a single-family property, also determine whether the transaction is a lease-option purchase with the required down payment generated from excess monthly rent contributions, or proposed rental income is being used to qualify.
3. When a stated trigger applies, review the Form 1007 and identify who prepared it.

**Checks:**
- A Form 1007 is provided for a single-family property on a DSCR qualifying file.
- A Form 1007 is provided for a single-family lease-option purchase transaction where the down payment required in §3.45 is generated from excess monthly rent contributions.
- A Form 1007 is provided when proposed rental income is being used to qualify.
- A Form 1007 is from the original appraiser or any state licensed appraiser.

**Reads:** property_type, residential_unit_count, loan_purpose, gross_rental_income, dscr_documentation_type
**Missing data:** whether the property is single family, whether the file is a DSCR qualifying file, whether the transaction is a lease-option purchase, whether the down payment required in §3.45 is generated from excess monthly rent contributions, whether proposed rental income is being used to qualify, Form 1007, identity and licensing status of the appraiser

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.review_rider_and_rent_loss_insurance

**Purpose:** Confirm the required loan-document rider and rent loss coverage for covered purchase or refinance transactions, including No Ratio DSCR.

1. Determine whether the borrower is purchasing or refinancing a one- to four-family investment property.
2. If so, check that all borrowers execute a One- to Four-Family Rider with the loan documents and provide rent loss insurance coverage per §23.40.
3. For a No Ratio DSCR file, apply the stated rent loss insurance requirement.

**Checks:**
- All borrowers purchasing or refinancing a one- to four-family investment property execute a One- to Four-Family Rider with the loan documents.
- All borrowers purchasing or refinancing a one- to four-family investment property provide rent loss insurance coverage per §23.40.
- Rent loss insurance applies to No Ratio DSCR.

**Reads:** loan_purpose, residential_unit_count, occupancy_subtype, dscr_documentation_type, borrower_entity_type
**Missing data:** whether the property is an investment property, loan documents and executed One- to Four-Family Rider, rent loss insurance coverage per §23.40, identity of all borrowers

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.review_short_term_rental_requirements

**Purpose:** Review the specified short-term-rental evidence options and qualification limits.

1. Determine whether the property is occupied as a short-term rental and identify the transaction as a purchase or refinance.
2. If an STRpro or similar appraisal form is used as a replacement to a 1007, confirm it is signed by an appropriately licensed appraiser.
3. If actual rents are documented using a 12-month ledger, review whether it is from a condotel management company, property manager, AirBnB, VRBO, etcetera.
4. Apply the short-term-rental CLTV limit for the transaction type and check the minimum FICO.

**Checks:**
- An STRpro or similar appraisal form used as a replacement to a 1007 is signed by an appropriately licensed appraiser.
- For a short-term rental purchase, CLTV is no more than 75%.
- For a short-term rental refinance, CLTV is no more than 70%.
- FICO is at least 640.
- A 12-month ledger used as documentation for actual rents is from a condotel management company, property manager, AirBnB, VRBO, etcetera.

**Reads:** occupancy_subtype, loan_purpose, cltv_pct, fico, dscr_documentation_type
**Missing data:** whether the property is occupied as a short-term rental, STRpro or similar appraisal form, if used, appraiser signature and licensing status, 12-month ledger, if used, ledger source, transaction type

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.review_tenant_rent_evidence_after_recent_mortgage_events

**Purpose:** Apply the rent-evidence requirement when an Applicant has had forbearance or mortgage lates within the last 12-months.

1. Determine whether the Applicant has had forbearance or mortgage lates within the last 12-months and whether the property is tenant occupied.
2. If both apply, review either timely receipt for the prior two (2) months rental payments or 12-months of the subject's payment in reserve.
3. If the reserve alternative is used, include reserves that may be from transaction's cash-in-hand.

**Checks:**
- If the Applicant has had forbearance or mortgage lates within the last 12-months and the property is tenant occupied, documentation shows timely receipt for the prior two (2) months rental payments or 12-months of the subject's payment in reserve.
- The 12-months of the subject's payment in reserve may be from transaction's cash-in-hand.

**Reads:** occupancy_subtype, current_lease_in_place, housing_history, mortgage_history_0x30x24, reserves_months, dscr_documentation_type
**Missing data:** whether the Applicant has had forbearance or mortgage lates within the last 12-months, documentation of timely receipt for the prior two (2) months rental payments, documentation of 12-months of the subject's payment in reserve, source of reserves

## acra-standard.dscr_qualification_rental_income_and_rent_evidence.review_vacant_property_qualifying_rent

**Purpose:** Check the qualifying-rent documentation required for a vacant property being purchased or used as the subject of an Acra loan.

1. Determine whether the property is vacant and whether it is being purchased.
2. If a vacant property is being purchased, review the qualifying rents in the 1007 or 1025 Appraisal report, as applicable.
3. If rental income from the purchase of a vacant property is for the subject of an Acra loan, check for a 1007 survey.

**Checks:**
- For a vacant property being purchased, qualifying rents are taken from the 1007 or 1025 Appraisal report, as applicable.
- Rental income from the purchase of a vacant property requires a 1007 survey if it is the subject of an Acra loan.

**Reads:** vacant_property, loan_purpose, property_type, residential_unit_count, gross_rental_income
**Missing data:** 1007 or 1025 Appraisal report, as applicable, 1007 survey, whether the property is the subject of an Acra loan

## acra-standard.entity_borrowers_guarantors_and_trusts.borrower_guarantor_due_diligence

**Purpose:** Determine whether borrower / guarantor due diligence is current at the required event and whether the required Key Principals and Entities are within the background review scope.

1. Confirm borrower / guarantor due diligence is current as of the date of any loan approval or draw, applying the schedule referred to in the guideline when available.
2. For an entity borrower, confirm Acra reviews the entity, the recourse guarantor(s), and any party (individual or entity) that owns 20% or more of the entity directly or indirectly or has managing control.
3. For an individual borrower, confirm Acra reviews all such individuals.
4. Note that Acra may order background checks on all Key Principals and Entities from Checkpoint, LexisNexis or another comparable provider, including criminal history, OFAC searches, litigation, judgment, and lien searches.

**Checks:**
- Borrower / Guarantor Due Diligence is current as of the date of any loan approval or draw, as required by the applicable schedule.
- For an entity borrower, the background review scope includes the entity, the recourse guarantor(s), and any party (individual or entity) that owns 20% or more of the entity directly or indirectly or has managing control.
- For an individual borrower, the background review scope includes all such individuals.
- The review recognizes that Acra may order background checks on all Key Principals and Entities from Checkpoint, LexisNexis or another comparable provider, including criminal history, OFAC searches, litigation, judgment, and lien searches.

**Reads:** borrower_entity_type
**Missing data:** The due diligence status and date, the date of any loan approval or draw, and the schedule referred to in the guideline, which is not reproduced in the excerpt., Whether the borrower is an entity or individual; the recourse guarantors; direct and indirect ownership interests; managing control; and the entities and individuals included in the background review., Whether Acra ordered background checks, the provider used, and the scope and results of any checks.

## acra-standard.entity_borrowers_guarantors_and_trusts.entity_documentation

**Purpose:** Determine whether the entity borrower has provided the entity documentation required without exception and whether applicable conditional documents or additional information are required.

1. Confirm that the complete, legible Certificate of Formation / Articles of Organization and all amendments are provided.
2. For LLCs and Partnerships, confirm the complete Operating Agreement with all referenced exhibits and all amendments is provided; for corporations, confirm the complete Bylaws with all referenced exhibits and all amendments are provided.
3. Confirm the Operating Agreement or Bylaws states whether the entity is member or manager managed, contains authorization to borrow money and enter into contracts for mortgage assets, and designates signers.
4. If the formation documents and the Operating Agreement or Bylaws conflict, determine whether additional information is required.
5. Confirm documentation evidencing all ownership interests is provided in the form specified for the entity type.
6. For S or C Corporations, confirm the applicable shareholder / stockholder certificates or stock ledger and any required Affidavit of Lost Stock Certificate are provided and account for all outstanding shares noted in the Certificate of Formation / Articles of Organization, including those held by the corporation.
7. For S-corporations or Partnerships where both stock certificate and stock ledger are unavailable, confirm the specified K-1 statements and CPA or Tax Preparer letter are provided.
8. Confirm names on the entity documents match the identification, or, if they do not match exactly, a letter of explanation addresses the discrepancy.
9. Confirm a Certificate of Good Standing or equivalent document is valid within ninety (90) days of the closing date.
10. If the entity is formed in a state other than where business is performed or where the property is located, confirm a Certificate of Foreign Qualification or other qualification to operate in the state where business is being conducted is provided.
11. Confirm the entity's IRS Form SS4 or Federal Taxpayer Identification Number (TIN) or Employer Identification Number (EIN) issuance letter is provided; if an EIN exception is requested, confirm it is submitted for review by Acra's Legal Department with a letter of explanation stating the applicable grounds.
12. Confirm a Unanimous Written Consent / Board Resolution signed by all members regardless of their percentage of interest authorizes the transaction with Acra Lending and identifies who is authorized to sign the loan documents on behalf of and to bind the entity.
13. Confirm a Unanimous Written Consent / Board Resolution is not used to designate a signor on a personal guarantee.
14. If a principal uses an attorney in fact to execute a personal guarantee, confirm a Power of Attorney is utilized by the principal to designate that attorney in fact.
15. Do not accept borrower letters stating required documents are not required, available, or excused from providing them; note that Legal reserves the right to condition for additional supporting documentation as determined in its sole discretion.

**Checks:**
- A complete, legible copy of the Certificate of Formation / Articles of Organization and all amendments thereto is provided.
- The applicable Operating Agreement for LLCs and Partnerships, or Bylaws for corporations, is complete with all referenced exhibits, legible, and includes all amendments.
- The Operating Agreement or Bylaws states whether the entity is member or manager managed, contains authorization to borrow money and enter into contracts for mortgage assets, and designates signers.
- Any additional information required because the formation documents and the Operating Agreement or Bylaws conflict is provided.
- All documentation evidencing ownership interests is provided.
- For LLCs and Partnerships, the Operating Agreement identifies, or attaches as an exhibit, all persons by name with their ownership interest, or copies of the membership interest certificates / units in compliance with the Operating Agreement are provided.
- For S or C Corporations, shareholder / stockholder certificates that comply with the Bylaws, if any, or, if stock certificates are lost or unavailable, the corporation's stock ledger is provided.
- For S or C Corporations, the certificate or ledger accounts for all outstanding shares noted in the Certificate of Formation / Articles of Organization, including those held by the corporation.
- If stock certificates are lost, destroyed, mutilated, or otherwise unavailable, an Affidavit of Lost Stock Certificate is provided.
- For S-corporations or Partnerships where both stock certificate and stock ledger are unavailable, the most recent preceding tax year's K-1 statement for all members with 20% or more interest is provided.
- For S-corporations or Partnerships where both stock certificate and stock ledger are unavailable, a letter from the CPA or Tax Preparer affirming current ownership interest is provided, with a statement to that effect if the preceding year's taxes have not been filed.
- Names on the entity documents match the identification, or a letter of explanation addresses any failure to match exactly.
- A Certificate of Good Standing or equivalent document is valid within ninety (90) days of the closing date.
- If the entity is formed in a state other than where business is performed or where the property is located, a Certificate of Foreign Qualification or other qualification to operate in the state where business is being conducted is provided.
- The entity's IRS Form SS4 or Federal Taxpayer Identification Number (TIN) or Employer Identification Number (EIN) issuance letter is provided, or an EIN exception request is submitted for review by Acra's Legal Department with a letter of explanation stating the applicable grounds.
- A Unanimous Written Consent / Board Resolution signed by all members regardless of their percentage of interest authorizes the transaction with Acra Lending.
- The Unanimous Written Consent / Board Resolution identifies who is authorized to sign the loan documents on behalf of and to bind the entity.
- The Unanimous Written Consent / Board Resolution is not used to designate a signor on a personal guarantee.
- If a principal uses an attorney in fact to execute a personal guarantee, a Power of Attorney is utilized by the principal to designate the attorney in fact.
- Borrower letters stating that required documents are not required, available, or excused from providing them are not accepted.

**Reads:** borrower_entity_type, entity_documents_complete
**Missing data:** The entity type and the complete entity documentation, including formation documents, operating agreement or bylaws and amendments, exhibits, ownership evidence, identification, and any applicable corporate, tax, qualification, consent, or power-of-attorney documents., Whether formation documents conflict with the Operating Agreement or Bylaws and whether additional information is required., Whether stock certificates are lost, destroyed, mutilated, or otherwise unavailable; whether both stock certificate and stock ledger are unavailable; and, where applicable, the K-1 statements, tax-filing status, CPA or Tax Preparer letter, and Affidavit of Lost Stock Certificate., The closing date and the validity date of the Certificate of Good Standing or equivalent document., The entity formation state, the state where business is performed, and the state where the property is located., Whether an EIN exception is requested and its submission and letter of explanation., The members' signatures, the contents of the Unanimous Written Consent / Board Resolution, and whether a principal uses an attorney in fact to execute a personal guarantee., Whether borrower letters purport to excuse required documents and whether Legal conditions for additional supporting documentation.

## acra-standard.entity_borrowers_guarantors_and_trusts.entity_eligibility_and_guarantees

**Purpose:** Determine whether an entity borrower, its ownership structure, and its guarantors meet the entity eligibility and guarantee requirements.

1. Confirm the transaction is a business purpose transaction for investment properties exclusively.
2. Confirm the collateral title is held directly by individual person(s) or by an entity acceptable to Acra in its sole discretion.
3. Confirm the entity is US formed and based and is not a foreign owned entity.
4. Confirm the entity or guarantor type is allowed and is not a prohibited type.
5. For an entity borrower, confirm it is a single purpose entity with no assets other than residential investment or rental properties and that it is engaged in owning and operating residential investment or rental properties.
6. Confirm the entity borrower is not a series limited liability company.
7. Confirm every entity that will hold direct ownership of the subject property and be on title as a direct owner is a borrowing entity.
8. Confirm any business entity nesting is limited to one (1) wholly-owned subsidiary owned by individual(s), with no multiple nesting or ownership by multiple entities, trusts, etcetera.
9. Confirm all individuals with direct or indirect ownership ≥ 20% provide a recourse guarantee (Acra approved, or Exhibit 7).
10. If there are multiple guarantors, confirm all recourse is joint and several.
11. Confirm changes to the operating agreement or bylaws intended to change ownership percentages to circumvent required personal guarantors are not considered; changes within 30 days prior to an Application Date or throughout the application process will not be recognized by Acra Lending.
12. Confirm at least one guarantor has prior homeownership experience.
13. Confirm at least one (1) borrower / guarantor on the loan attests on the application that they are not a first-time homebuyer; if prior home ownership is not evident within the loan file, note that the underwriter reserves the right to condition for supporting documentation.

**Checks:**
- The transaction is a business purpose transaction for investment properties exclusively.
- Title to the collateral is held either directly by individual person(s) or by an entity acceptable to Acra in its sole discretion.
- The entity is US formed and based and is not a foreign owned entity.
- The entity or guarantor type is among Domestic Corporations (C and S Corp), single purpose Limited Liability Companies (LLC) excluding series LLC, Limited Liability Partnership (LLP), Limited Liability Limited Partnership (LLLP), General Partnership (GP), Limited Partnership (LP), or Sole Proprietorship, and is not a Cooperative, Irrevocable Trust, Land Trust, IRA, Non-Profit, or Joint Venture.
- The entity borrower has no assets other than residential investment or rental properties.
- The entity borrower is engaged in the business of owning and operating residential investment or rental properties.
- The entity borrower is not a series limited liability company.
- Every entity that will hold direct ownership of the subject property and be on title as a direct owner is a borrowing entity.
- Business entity nesting is limited to only one (1) wholly-owned subsidiary that in turn is owned by individual(s), with no multiple nesting or ownership by multiple entities, trusts, etcetera.
- All individuals with direct or indirect ownership ≥ 20% provide a recourse guarantee (Acra approved, or Exhibit 7).
- All recourse is joint and several in the case of multiple guarantors.
- Changes to the operating agreement or bylaws with the intent of changing ownership percentages to circumvent required personal guarantors are not considered.
- Changes to ownership percentages within 30 days prior to an Application Date or throughout the application process are not recognized by Acra Lending.
- At least one guarantor has prior homeownership experience.
- At least one (1) borrower / guarantor on the loan attests on the application that they are not a first-time homebuyer.

**Reads:** borrower_entity_type
**Missing data:** Whether the transaction is for business purpose and the property is exclusively an investment property., Whether the entity is acceptable to Acra in its sole discretion., Whether the entity is US formed and based, is foreign owned, and meets the precise permitted or prohibited entity categories., The entity's assets and business activities; whether it is a series LLC; and the ownership, title, and borrowing-entity structure, including any nesting., Direct and indirect ownership interests and recourse guarantees, including whether guarantees are Acra approved or on Exhibit 7 and whether multiple guarantors' recourse is joint and several., The intent and dates of operating agreement or bylaw changes relative to the Application Date and application process., Prior homeownership evidence, the loan-file contents, and the borrower / guarantor application attestation.

## acra-standard.entity_borrowers_guarantors_and_trusts.revocable_living_trust_title_vesting

**Purpose:** Determine whether title vesting in an inter vivos revocable trust meets each stated requirement.

1. Confirm a complete, legible copy of the Trust or a Certification of Trust containing every specified item is provided.
2. Confirm the Trust is valid under the laws of the state in which it is established.
3. Confirm the Trust is revocable and can be changed or canceled at any time for any reason during a Trustor's lifetime.
4. Confirm the Trust is established by one or more natural persons, solely or jointly, and becomes effective during the lifetime of the person(s) establishing it.
5. Confirm the primary beneficiary of the Trust is the individual(s) establishing the Trust.
6. If the Trustor(s) and Trustee(s) are not the same, confirm written exception by Acra Senior Management is obtained.
7. Confirm the Trust contains each required provision concerning the Trustee's power, beneficiary consent, lender rights, and title.
8. Note that Legal reserves the right to condition for additional supporting documentation as determined in its sole discretion.

**Checks:**
- A complete, legible copy of the Trust or a Certification of Trust states the existence and date of the Trust; the Trustor(s) and current Trustee(s); the powers of the Trustee; whether the Trust is revocable and, if revocable, who holds the right to revoke; the names and number of Trustees required to sign on behalf of the Trust; the Trust identification number (a Social Security number or an IRS-issued Tax Identification Number); how title to the Trust assets should be taken; and that the Trust has not been revoked, modified, or amended in any manner.
- The Trust is valid under the laws of the state in which it is established.
- The Trust is revocable, meaning it can be changed or canceled at any time for any reason during a Trustor's lifetime.
- The Trust is established by one or more natural persons, solely or jointly (Grantor, Trustor, or Settlor), and becomes effective during the lifetime of the person(s) establishing it.
- The primary beneficiary of the Trust is the individual(s) establishing the Trust.
- If the Trustor(s) and Trustee(s) are not the same, written exception by Acra Senior Management is obtained.
- The Trust specifies that the Trustee has the power to hold title and mortgage the property.
- The Trust specifies that the beneficiary does not need to grant written consent for the Trust to borrow money, or that such consent has been granted in writing for purposes of the mortgage.
- The Trust specifies that there is no unusual risk or impairment to the lender's rights.
- The Trust specifies that holding title in the Trust does not diminish the lender's rights as a creditor.
**Missing data:** Whether title is vested in an inter vivos revocable trust and the complete Trust or Certification of Trust., The Trust's existence and date, Trustor(s), Trustee(s), Trustee powers, revocability and right to revoke, required Trustee signers, identification number, title instructions, and statement that the Trust has not been revoked, modified, or amended., The state in which the Trust is established and whether it is valid under that state's laws., Whether the Trust is changeable or cancelable at any time for any reason during a Trustor's lifetime, who established it, and when it became effective., The primary beneficiary and whether the Trustor(s) and Trustee(s) are the same; if not, the written Acra Senior Management exception., The Trust provisions on holding title, mortgaging the property, beneficiary consent, unusual risk or impairment to lender rights, and lender rights as a creditor., Whether Legal conditions for additional supporting documentation.

## acra-standard.first_time_homebuyer_eligibility.apply_the_fthb_investment_property_dti_limit

**Purpose:** Determine whether the applicable FTHB investment-property DTI limit is met.

1. Determine whether the case is a first-time homebuyer purchasing an Investment property and the loan is qualifying via DTI program.
2. If those conditions hold, establish that DTI is no more than 43.0%.

**Checks:**
- The case is a first-time homebuyer purchasing an Investment property and the loan is qualifying via DTI program.
- For an applicable case, DTI is no more than 43.0%.

**Reads:** first_time_homebuyer, loan_purpose, occupancy_subtype
**Missing data:** Whether the loan is qualifying via DTI program., DTI value., Confirmation that the case is a purchase of an Investment property, if loan_purpose and occupancy_subtype do not establish this.

## acra-standard.first_time_homebuyer_eligibility.determine_first_time_homebuyer_status_and_dscr_eligibility

**Purpose:** Determine whether a first-time homebuyer meets the stated DSCR-program requirements.

1. Determine whether the application is for a first-time homebuyer: Acra defines a First Time Home Buyers (‘FTHB’) as an application where all Applicants have never previously owned a home (real property).
2. For a first-time homebuyer under the DSCR program, establish that the FICO score is at least 700.
3. Establish that CLTV is no more than 70%.
4. Establish that DSCR is at least 1.150.
5. Establish that the loan amount is no more than $1,000,000.
6. Establish that the loan is fully amortizing and is not an interest-only program.
7. Establish that impounds are in place.
8. Establish that reserves are at least six months.

**Checks:**
- Every Applicant has never previously owned a home (real property).
- FICO score is at least 700.
- CLTV is no more than 70%.
- DSCR is at least 1.150.
- Loan amount is no more than $1,000,000.
- The loan is fully amortizing and is not an interest-only program.
- Impounds are in place.
- Reserves are at least six months.

**Reads:** first_time_homebuyer, fico, cltv_pct, loan_amount, product_is_interest_only, interest_only_10_40, reserves_months
**Missing data:** Confirmation that every Applicant has never previously owned a home (real property), if the first_time_homebuyer field does not establish this for all Applicants., DSCR value or qualification determination., Whether impounds are in place.

## acra-standard.first_time_homebuyer_eligibility.review_entity_guarantor_homeownership_requirement

**Purpose:** Determine whether the stated guarantor requirement is established for an entity borrower and retain the requested Acra confirmation on how it interacts with FTHB eligibility.

1. If the borrower is an entity, establish that at least one guarantor has prior homeownership experience.
2. Establish that at least one borrower / guarantor on the loan attests on the application that they are not a first-time homebuyer.
3. If prior home ownership is not evident within the loan file, note that the underwriter reserves the right to condition for supporting documentation.
4. For an entity FTHB case, retain the unresolved Acra confirmation requested on how the entity guarantor requirement and the first-time-homebuyer allowance interact (Q-09).

**Checks:**
- For an entity borrower, at least one guarantor has prior homeownership experience.
- For an entity borrower, at least one borrower / guarantor on the loan attests on the application that they are not a first-time homebuyer.
- If prior home ownership is not evident within the loan file, supporting documentation is conditioned if the underwriter exercises that reserved right.
- For an entity FTHB case, the interaction of the entity guarantor requirement and the FTHB allowance is not treated as resolved without Acra confirmation.

**Reads:** borrower_entity_type, first_time_homebuyer
**Missing data:** Whether at least one guarantor has prior homeownership experience., Whether at least one borrower / guarantor attests on the application that they are not a first-time homebuyer., Whether prior home ownership is evident within the loan file and whether the underwriter conditions for supporting documentation., Acra confirmation on the interaction of the entity guarantor requirement and the first-time-homebuyer allowance (Q-09).

## acra-standard.first_time_homebuyer_eligibility.review_escrow_waiver_request_for_an_fthb_case

**Purpose:** Avoid treating an escrow waiver as resolving or overriding the FTHB impound requirement without Acra confirmation.

1. Determine whether the case is a first-time homebuyer and an escrow waiver is requested.
2. For an FTHB case, establish that impounds are required.
3. If an escrow waiver is requested, retain the unresolved Acra confirmation requested on how the FTHB impound requirement interacts with an otherwise eligible waiver (Q-15).

**Checks:**
- The case is a first-time homebuyer and an escrow waiver is requested.
- For an FTHB case, impounds are required.
- If an FTHB case requests an escrow waiver, the interaction is not treated as resolved without Acra confirmation (Q-15).

**Reads:** first_time_homebuyer, escrow_waiver_requested
**Missing data:** Whether impounds are in place., Acra confirmation on how the FTHB impound requirement interacts with an otherwise eligible escrow waiver (Q-15).

## acra-standard.funds_to_close_seasoning_and_reserves.foreign_account_funds_and_closing_timing

**Purpose:** Determine whether foreign-account funds and funds held by Foreign Nationals meet the stated verification and closing requirements.

1. For assets held in foreign accounts, verify U.S. Dollar equivalency using the current exchange rate via www.xe.com or the Wall Street Journal conversion table.
2. Verify that sufficient funds to close are on deposit with the Escrow / Closing Agent at least three (3) business days, including Saturdays for this calculation, prior to any closing date.
3. Obtain a copy of the two (2) most recent statements of the account. Translate bank statements in any language other than English into English.
4. If funds are not seasoned a minimum of sixty (60) days, obtain a letter of explanation and information comprising a sixty (60) day chain of funds.
5. For Foreign Nationals, verify a minimum of 60 days seasoning regardless of LTV / CLTV.
6. For funds held in a foreign bank / currency, verify repatriation at minimum three (3) business days prior to Closing; the scope of this requirement and applicable evidence are subject to the Acra confirmation requested in Q-12.

**Checks:**
- Foreign-account assets are verified in U.S. Dollar equivalency at the current exchange rate via www.xe.com or the Wall Street Journal conversion table.
- Sufficient funds to close are on deposit with the Escrow / Closing Agent at least three (3) business days, including Saturdays for this calculation, prior to any closing date.
- The two (2) most recent statements of the account are provided.
- Any bank statement in a language other than English is translated into English.
- Where funds are not seasoned a minimum of sixty (60) days, a letter of explanation and information comprising a sixty (60) day chain of funds are provided.
- A Foreign National documents a minimum of 60 days seasoning regardless of LTV / CLTV.
- Funds held in a foreign bank / currency are repatriated at minimum three (3) business days prior to Closing, subject to the unresolved scope and evidence question in Q-12.

**Reads:** citizenship_type, cltv_pct
**Missing data:** Whether assets are held in a foreign account, Current exchange rate and conversion verification, Sufficient funds-to-close amount and deposit record, Closing date and business-day calculation, including Saturdays, Two (2) most recent account statements, Statement language and English translation, if required, Funds seasoning history, Letter of explanation and information comprising a sixty (60) day chain of funds, when required, Whether the borrower is a Foreign National, Whether funds are held in a foreign bank / currency, Repatriation record and timing, Scope of the repatriation requirement and applicable evidence (Acra confirmation requested in Q-12)

## acra-standard.funds_to_close_seasoning_and_reserves.funds_to_close_and_seasoning_documentation

**Purpose:** Determine whether funds to close are documented for the required period and whether seasoning verification is required under the stated transaction and CLTV conditions.

1. Require a minimum of 30-days documentation for all transactions.
2. Determine whether the seasoning-verification trigger applies: loans over 70% CLTV for consumer transactions, or business purpose loans where funds to close are over $50,000 and over 70% CLTV.
3. Where source-account verification is required, review the borrower's bank statement(s) for the most recent month(s), or a VOD reflecting a current and average balance for the most recent month(s).
4. For funds not seasoned a minimum of sixty (60) days, review a letter of explanation and information comprising a sixty (60) day chain of funds where the applicable source-account requirements call for them.
5. Do not impose a domestic seasoning period beyond the stated 30-days documentation minimum absent the requested Acra confirmation.

**Checks:**
- The transaction has a minimum of 30-days documentation.
- For a consumer transaction over 70% CLTV, seasoning of funds to close is verified.
- For a business purpose loan, if funds to close are over $50,000 and CLTV is over 70%, seasoning of funds to close is verified.
- Where source-account verification is required, the account is verified by the stated bank statement(s) or VOD option.
- Where funds are not seasoned a minimum of sixty (60) days and the stated account-documentation condition applies, a letter of explanation and information comprising a sixty (60) day chain of funds are provided.

**Reads:** cltv_pct, loan_purpose
**Missing data:** Documentation establishing a minimum of 30-days, Whether the transaction is a consumer transaction, Whether the loan is business purpose, Funds-to-close amount, Seasoning period applicable to domestic funds beyond the 30-days documentation minimum (Acra confirmation requested in Q-12), Bank statement(s) for the most recent month(s), or VOD with current and average balance for the most recent month(s), Funds seasoning history, Letter of explanation, when required, Information comprising a sixty (60) day chain of funds, when required

## acra-standard.funds_to_close_seasoning_and_reserves.loan_amount_concessions_and_applicant_funds

**Purpose:** Determine whether the loan amount, seller concessions, and applicant funds meet the requirements stated for these transactions.

1. Compare the loan amount with the stated minimum and maximum and check that it is in $50 increments.
2. Compare seller concessions and other contributions with the stated limit of 3% of the sale price.
3. For a transaction to which the applicant-contribution requirement applies, verify that the applicant contributes at least 10% of the purchase price in the applicant's own sourced and seasoned funds.
4. If gift funds are used, review the gift documentation required by the Seller's Guide gift-fund section; that section is not reproduced here.

**Checks:**
- The loan amount is at least $100,000.
- The loan amount is no more than $3,000,000.
- The loan amount is in $50 increments.
- Seller concessions / other contributions do not exceed 3% of the sale price.
- The applicant's own sourced and seasoned funds contributed to the transaction are at least 10% of the purchase price when the applicant-contribution requirement applies.
- When gift funds are used, the gift documentation meets the Seller's Guide gift-fund requirements.

**Reads:** loan_amount, seller_concession_pct, loan_purpose, occupancy_subtype
**Missing data:** Sale price, Purchase price, Whether the applicant-contribution requirement applies to this transaction, Amount of applicant's own sourced and seasoned funds contributed, Gift funds used and amount, Gift-fund documentation requirements from the Seller's Guide (Appendix B)

## acra-standard.funds_to_close_seasoning_and_reserves.reserve_requirements_by_trigger

**Purpose:** Determine whether the reserve requirements stated for applicable loan, borrower, and property circumstances are met.

1. Determine whether LTV is > 80.00%; if so, verify 6 months PITIA reserves.
2. Determine whether FICO is < 620; if so, apply the stated 12 Months reserve requirement without assuming a payment basis not stated in the source.
3. For a first-time homebuyer, verify Minimum six months reserves (“Requires 6mos Reserves”).
4. For a vacant property, determine whether the transaction is a rate & term refinance or cash-out refinance and apply the corresponding stated minimum six months reserves or 6 months reserves.
5. If the property was listed for sale within six months, verify Twenty-four (24) months of reserves; cash-in-hand may be considered if otherwise consistent with the Guide.
6. For forbearance or mortgage lates in the last 12 months, where the subject is tenant-occupied and the prior two months' rent were not timely received, verify 12 months of the subject's payment in reserve; this may be from the transaction's cash-in-hand.
7. If rent loss insurance is required but cannot be obtained, verify Two (2) months reserves for every one (1) month of coverage not provided.
8. Do not infer a base reserve requirement, a payment basis where only “months” is stated, permitted sources, whether overlapping triggers are cumulative, or whether reserves substituted for rent loss insurance are additional; Acra confirmation is requested in Q-07.

**Checks:**
- If LTV is > 80.00%, 6 months PITIA reserves are held.
- If FICO is < 620, the stated 12 Months reserve requirement is met; its payment basis is not specified in the source.
- A first-time homebuyer has Minimum six months reserves (“Requires 6mos Reserves”).
- For a vacant property — rate & term refinance, Minimum six months reserves are held.
- For a vacant property — cash-out refinance, 6 months reserves are held.
- If the property was listed for sale within six months, Twenty-four (24) months of reserves are held, with cash-in-hand considered only if otherwise consistent with the Guide.
- If forbearance or mortgage lates in the last 12 months, tenant-occupied subject, and no timely receipt of the prior two months' rent all apply, 12 months of the subject's payment are held in reserve; the reserve may be from the transaction's cash-in-hand.
- If rent loss insurance is required but cannot be obtained, Two (2) months reserves are held for every one (1) month of coverage not provided.

**Reads:** fico, first_time_homebuyer, vacant_property, loan_purpose, property_currently_listed_for_sale, listed_for_sale_last_6_months, housing_history, mortgage_history_0x30x24, current_lease_in_place, occupancy_subtype, reserves_months, pitia
**Missing data:** LTV (the available case field is CLTV, not LTV), Reserve amount and records supporting the stated reserve requirement, Payment basis for the FICO < 620 trigger's 12 Months requirement (Acra confirmation requested in Q-07), Whether vacant property is a rate & term refinance or cash-out refinance, Whether cash-in-hand is otherwise consistent with the Guide, Whether forbearance occurred or mortgage lates occurred in the last 12 months, Whether the subject is tenant-occupied and whether the prior two months' rent were timely received, Subject payment amount and reserve records, Whether rent loss insurance is required, whether it can be obtained, and months of coverage not provided, Base reserve requirement where no trigger applies; payment basis where only “months” is stated; permitted sources; whether overlapping triggers are cumulative; whether reserves substituted for rent loss insurance are additional (Acra confirmation requested in Q-07)

## acra-standard.loan_amount_fico_and_matrix_leverage.gift_contribution

**Purpose:** Determine whether the stated minimum contribution requirement for gifting is met, without adding gift-documentation requirements not reproduced in the source.

1. Determine whether gifting is used.
2. If gifting is used, verify that the borrower contributes at least 10% of the purchase price from the borrower’s own sourced and seasoned funds.
3. Note that gift documentation requirements are in the Seller's Guide gift-fund section and are not reproduced in the supplied source.

**Checks:**
- If gifting is used, the borrower’s own sourced and seasoned funds contribute at least 10% of the purchase price.
**Missing data:** whether gifting is used, purchase price, amount of the borrower’s own contribution, whether those funds are the borrower’s own sourced and seasoned funds, Seller's Guide gift-fund documentation requirements

## acra-standard.loan_amount_fico_and_matrix_leverage.investment_property_matrix_leverage

**Purpose:** Determine the published maximum CLTV for the applicable Investment Property matrix entry and whether the case CLTV is within that value.

1. Confirm whether the case is subject to the Investment Property matrix.
2. Select the loan-amount tier: loan_amount ≤ $1,500,000; $1,500,001–$2,000,000; or $2,000,001–$3,000,000.
3. Select the transaction column corresponding to Purchase, Rate & Term, or Cash-Out.
4. For the selected tier and transaction column, select the row whose minimum-FICO threshold is the greatest threshold at or below fico; a score at or above a threshold and below the next higher threshold takes that row.
5. Read the cell at the selected row and column. Record NA where printed. For loans of $1,500,000 or less, record that there is no published matrix value below 600.
6. If the selected cell is a numeric percentage, compare cltv_pct with that percentage.

**Checks:**
- The case’s loan amount, FICO, and transaction type identify one matrix tier, row, and column.
- The selected matrix cell is a published numeric percentage, rather than NA or a case with no published matrix value.
- If the selected matrix cell is a numeric percentage, cltv_pct does not exceed that percentage.

**Reads:** loan_amount, fico, loan_purpose, cltv_pct
**Missing data:** whether the property is an Investment Property, if not established by the case, confirmation of eligibility where the matrix has no published value below 600 for a loan of $1,500,000 or less (Q-16), Acra confirmation of the treatment of matrix footnotes 1 and 2 and the use of LTV footnotes with a CLTV matrix (Q-17)

## acra-standard.loan_amount_fico_and_matrix_leverage.loan_amount_and_seller_concessions

**Purpose:** Determine whether the loan amount and seller concessions meet the requirements in STD-1.10 and STD-1.11.

1. Compare loan_amount with the minimum and maximum loan amounts in STD-1.10.
2. Check whether loan_amount is in $50 increments.
3. Compare seller_concession_pct with the limit in STD-1.11.

**Checks:**
- loan_amount is at least $100,000.
- loan_amount is no more than $3,000,000.
- loan_amount is a multiple of $50.
- seller_concession_pct is no more than 3%.

**Reads:** loan_amount, seller_concession_pct

## acra-standard.loan_amount_fico_and_matrix_leverage.loan_amount_conditions_and_matrix_footnotes

**Purpose:** Determine whether the case meets the additional loan-amount conditions and whether the stated matrix cash-in-hand footnote applies.

1. If loan_amount is less than $200,000, apply the maximum CLTV of 80% for Purchase or 75% for refinance (Rate & Term and Cash-Out).
2. If loan_amount is greater than $2,000,000, verify that DSCR is 1.0 or greater.
3. If the loan is interest-only, verify the minimum loan amount of $250,000, maximum loan amount of $3,000,000, and minimum FICO of 640.
4. If delayed financing applies, apply the stated $1.5MM cap.
5. For Cash-Out, where LTV is greater than 65%, apply footnote 1: maximum cash-in-hand is $1,000,000 for loans ≥ $1,500,000 and $500,000 for loans < $1,500,000.
6. Note footnote 2 as printed: “When LTV ≤ 65%, unlimited cash-in-hand allowed”. The source requests Acra confirmation on whether footnote 2 applies to every tier or only the tier bearing its marker, and why the footnotes use LTV while the matrix is labelled CLTV.

**Checks:**
- If loan_amount is less than $200,000 and loan_purpose is Purchase, cltv_pct is no more than 80%.
- If loan_amount is less than $200,000 and loan_purpose is Rate & Term or Cash-Out, cltv_pct is no more than 75%.
- If loan_amount is greater than $2,000,000, DSCR is at least 1.0.
- If the loan is interest-only, loan_amount is at least $250,000.
- If the loan is interest-only, loan_amount is no more than $3,000,000.
- If the loan is interest-only, fico is at least 640.
- If delayed financing applies, loan_amount is no more than $1.5MM.
- If the loan is Cash-Out and LTV is greater than 65%, cash-in-hand is no more than the applicable footnote 1 cap.
- The applicable treatment of footnote 2 and the LTV-versus-CLTV footnotes is confirmed where needed.

**Reads:** loan_amount, loan_purpose, cltv_pct, fico, product_is_interest_only, delayed_financing
**Missing data:** DSCR, whether the loan is interest-only, if not established by product_is_interest_only, LTV, cash-in-hand amount, Acra confirmation of footnote 2 scope and the use of LTV footnotes with the CLTV matrix (Q-17)

## acra-standard.prepayment_penalty_structures_and_state_restrictions.apply_transaction_minimum_terms

**Purpose:** Establish whether the minimum terms stated for particular transactions are met, subject to the stated “where allowable” and state-interaction qualifications.

1. Determine whether the case is a vacant-property rate & term refinance, a vacant-property cash-out refinance, or a property listed for sale.
2. For a vacant-property rate & term refinance, verify a term of at least two years, “where allowable.”
3. For a vacant-property cash-out refinance, verify a term of at least three years, “where allowable.”
4. For a property listed for sale, verify a term of at least three years unless the property is located in a state that does not allow prepayment penalties.
5. For a minimum whose interaction with a state restriction needs confirmation, request Acra confirmation as indicated by Q-24.

**Checks:**
- The case is a vacant-property rate & term refinance.
- The case is a vacant-property cash-out refinance.
- The property is listed for sale.
- If the case is a vacant-property rate & term refinance, the selected term is at least two years where allowable.
- If the case is a vacant-property cash-out refinance, the selected term is at least three years where allowable.
- If the property is listed for sale and is not located in a state that does not allow prepayment penalties, the selected term is at least three years.
- Any applicable state-restriction interaction with a minimum term has the Acra confirmation requested by Q-24.

**Reads:** vacant_property, loan_purpose, property_currently_listed_for_sale, property_state
**Missing data:** Selected prepayment penalty term., Whether the selected term is allowable for the vacant-property transaction., Whether the property is located in a state that does not allow prepayment penalties., Acra confirmation on how the state restriction interacts with the applicable minimum term.

## acra-standard.prepayment_penalty_structures_and_state_restrictions.check_listed_prepayment_penalty_structures

**Purpose:** Establish whether the selected structure is one of the listed structures.

1. Obtain the selected prepayment penalty term and structure.
2. Verify that it matches one of the options printed for that term in STD-11.1, including “No Prepay” as a listed structure.

**Checks:**
- The selected prepayment penalty term and structure match an option printed for that term in STD-11.1.

**Reads:** prepayment_penalty_requested
**Missing data:** Selected prepayment penalty term and structure.

## acra-standard.prepayment_penalty_structures_and_state_restrictions.screen_state_prepayment_restrictions

**Purpose:** Identify whether a printed state restriction applies and route restrictions requiring Acra confirmation for review.

1. If no prepayment penalty is requested, treat this job as not applicable.
2. Compare the case fields with each state restriction printed in STD-11.3.
3. For an applicable BUY-OUT restriction, request Acra confirmation as indicated by Q-24; do not infer what “BUY-OUT” requires.
4. For Mississippi, establish whether the residential 1-unit restriction applies and obtain the selected structure to assess the printed “BUY-OUT or 5 year (STEP)” wording. Do not apply that restriction to 2+ units.

**Checks:**
- Alaska restriction applies: the property is in Alaska and is Residential 1-4.
- Illinois clause 1 applies: the property is in Illinois, is Residential 1-4, the loan is to an ENTITY OR INDIVIDUAL, and the loan amount is ≤$250,000.
- Illinois clause 2 applies: the property is in Illinois, is Residential 1-4, the loan is to an INDIVIDUAL, the loan amount is >$250,000, and the interest rate is >8%.
- Kansas restriction applies: the property is in Kansas and is Residential 1-4.
- Maryland restriction applies: the property is in Maryland.
- Michigan restriction applies: the property is in Michigan and is Residential 1-4.
- Minnesota restriction applies: the property is in Minnesota and is Residential 1-4.
- Mississippi restriction applies: the property is in Mississippi and is Residential 1 unit.
- New Jersey restriction applies: the property is in New Jersey and the loan is closing in the name of an INDIVIDUAL.
- New Mexico restriction applies: the property is in New Mexico and is Residential 1-4.
- Ohio restriction applies: the property is in Ohio and is Residential 1-2.
- Pennsylvania restriction applies: the property is in Pennsylvania, is Residential 1-2, the loan is to an INDIVIDUAL, and the loan amount is <$319,777.
- Rhode Island restriction applies: the property is in Rhode Island and the transaction is a PURCHASE.
- Virginia restriction applies: the property is in Virginia, is Residential 1-4, and is closed in the name of an individual.
- Vermont restriction applies: the property is in Vermont and the loan amount is < $1 Million.
- For any applicable BUY-OUT restriction, Acra confirmation has been requested as indicated by Q-24.
- For an applicable Mississippi restriction, the selected structure has been reviewed against the printed “BUY-OUT or 5 year (STEP)” wording.

**Reads:** prepayment_penalty_requested, property_state, property_type, residential_unit_count, borrower_entity_type, loan_amount, interest_rate, loan_purpose
**Missing data:** Selected prepayment penalty structure, including whether it is “BUY-OUT” or 5 year (STEP)., Acra confirmation on what “BUY-OUT” requires.

## acra-standard.products_interest_only_terms_and_subordinate_financing.apply_interest_only_payment_mechanics

**Purpose:** Ensure the interest-only payment is calculated and recast as described, and that DSCR uses the first payment due under the Note.

1. Verify that the interest-only payment is calculated as the amount sufficient to pay the accrued interest on the mortgage monthly at the time of origination.
2. After the interest-only term, verify that payments are recast to a fully amortized payment for the balance of the term ending at maturity.
3. Verify that Acra calculates DSCR using the first payment due under the Note.

**Checks:**
- The interest-only payment is calculated as the amount sufficient to pay the accrued interest on the mortgage monthly at the time of origination.
- After the interest-only term, payments are recast to a fully amortized payment for the balance of the term ending at maturity.
- Acra calculates DSCR using the first payment due under the Note.

**Reads:** interest_rate, loan_amount, pitia, product_is_interest_only
**Missing data:** Interest-only payment calculation and payment schedule at origination., Interest-only term, balance used for recast, remaining term, and maturity date., Note payment schedule identifying the first payment due., Q-26 guidance identifying which payment enters the denominator on an interest-only loan.

## acra-standard.products_interest_only_terms_and_subordinate_financing.review_subordinate_financing_and_heloc_cltv

**Purpose:** Determine whether subordinate financing is prohibited on a listed-for-sale property and, when applicable, whether HELOC CLTV uses the greater of the credit line limit or current balance.

1. Determine whether subordinate or secondary financing is present and whether it is allowable for this program, lien type, and transaction.
2. Verify that no subordinate financing is present on a property listed for sale.
3. If subordinate or secondary financing is allowable and is a HELOC, verify that CLTV for eligibility is calculated on the greater of the credit line limit or current credit line balance.

**Checks:**
- The subordinate or secondary financing's allowability for this program, lien type, and transaction is established.
- No subordinate financing is present on a property listed for sale.
- If subordinate or secondary financing is allowable and is a HELOC, CLTV for eligibility is calculated on the greater of the credit line limit or current credit line balance.

**Reads:** cltv_pct, property_currently_listed_for_sale
**Missing data:** Whether subordinate or secondary financing is present and its lien type., Whether subordinate or secondary financing is allowable for this program, lien type, and transaction; Acra confirmation is requested., Applicable leverage and payment rules for subordinate financing., For a HELOC, the credit line limit and current credit line balance.

## acra-standard.products_interest_only_terms_and_subordinate_financing.verify_eligible_products_and_arm_terms

**Purpose:** Determine whether the selected product is eligible and whether an ARM meets the specified index, caps, and FICO-based margin requirements.

1. Verify that the selected product is one of the eligible product types: 30 Yr Fixed; 5/1 ARM; 7/1 ARM; Interest Only (5 Yr / 30 year term, available on 5/1 or 7/1 ARM); Interest Only (5 Yr / 30 Year Fixed); Interest Only (10 Yr / 40 Year Term).
2. For an ARM, verify that the index is 1 Yr CMT.
3. For an ARM, verify that the caps are 2/2/6.
4. For an ARM, verify that the margin matches the FICO tier: 3.00 (FICO 760+), 3.25 (FICO 720-759), 3.50 (FICO 700-719), 3.75 (FICO 680-699), 4.00 (FICO 660-679), 4.25 (FICO 640-659), or 5.00 (FICO 600-639).

**Checks:**
- The selected product is one of the eligible product types listed in the step.
- If the selected product is an ARM, its index is 1 Yr CMT.
- If the selected product is an ARM, its caps are 2/2/6.
- If the selected product is an ARM, its margin matches the applicable FICO tier.

**Reads:** fico, product_is_interest_only
**Missing data:** Selected product type, including whether it is an ARM and its term and fixed or ARM type., ARM index., ARM caps., ARM margin.

## acra-standard.products_interest_only_terms_and_subordinate_financing.verify_interest_only_eligibility

**Purpose:** Determine whether an interest-only loan meets the requirements for its term and is not subject to a stated prohibition.

1. For Interest Only, 5 Yr / 30 Year Fixed or 5/1 and 7/1 ARM, verify minimum loan ≥ $250K and minimum 640 credit score.
2. For Interest Only, 10 Yr / 40 Year Term, verify minimum loan ≥ $250K, minimum 640 credit score, maximum 80% LTV / CLTV, and maximum $3M loan amount.
3. Verify that the interest-only loan is not for a first-time homebuyer.
4. Verify that the interest-only loan is not a vacant-property refinance.
5. Verify that the interest-only loan is not on a property listed for sale.

**Checks:**
- For an Interest Only, 5 Yr / 30 Year Fixed or 5/1 and 7/1 ARM loan, loan_amount is ≥ $250K.
- For an interest-only loan, fico is at least 640.
- For an Interest Only, 10 Yr / 40 Year Term loan, loan_amount is ≥ $250K.
- For an Interest Only, 10 Yr / 40 Year Term loan, cltv_pct is no greater than 80% LTV / CLTV.
- For an Interest Only, 10 Yr / 40 Year Term loan, loan_amount is no greater than $3M.
- The interest-only loan is not for a first-time homebuyer.
- The interest-only loan is not a vacant-property refinance.
- The interest-only loan is not on a property listed for sale.

**Reads:** fico, first_time_homebuyer, interest_only_10_40, loan_amount, loan_purpose, product_is_interest_only, property_currently_listed_for_sale, vacant_property, cltv_pct

## acra-standard.program_scope_occupancy_and_transaction_setup.check_published_program_scope

**Purpose:** Establish whether the case meets the program-scope values stated in the published summary.

1. Check the loan amount against the published range and increment.
2. Check the minimum FICO that applies to the loan amount.
3. Check the property type, state, and borrower citizenship against the published lists.
4. For delayed financing, apply the published loan-amount cap.
5. Apply the published CLTV values where their stated amount and FICO conditions apply.
6. Check the product and prepayment option against the published options and restrictions.

**Checks:**
- Loan amount is from $100,000 to $3,000,000, in $50 increments.
- FICO is at least 600 for loans ≤ $1,500,000; 620 for $1,500,001–$2,000,000; or 700 for $2,000,001–$3,000,000.
- Property type is SFR, Townhome, PUD, Warrantable Condo, Non-Warrantable Condo, Condotel / PUDtel, 2-4 Units, or Manufactured.
- Property state is not SD.
- Borrower citizenship is US Citizen, Permanent Resident, Non-Permanent Resident, Foreign National, or ITIN.
- If delayed financing, loan amount is no more than $1.5MM.
- For loans ≤ $1,500,000 at FICO 720+, CLTV is no more than 85% for purchase or 80% for rate & term or cash-out.
- The product is 30 Yr Fixed; 5/1 and 7/1 ARM; or Interest Only 5 Yr / 30 and 10 Yr / 40.
- The prepayment option is a 5-, 4-, 3-, 2-, 1-year structure or No Prepay, and applicable state restrictions are met.

**Reads:** loan_amount, fico, property_type, property_state, citizenship_type, delayed_financing, loan_purpose, cltv_pct
**Missing data:** Selected product and product term, Selected prepayment structure, The 14-state prepayment restriction requirements

## acra-standard.program_scope_occupancy_and_transaction_setup.complete_dscr_transaction_setup

**Purpose:** Check the required rent appraisal and, where applicable, business-purpose attestation, rider, and rent loss insurance requirements.

1. Require a 1007 on DSCR transactions, including No Ratio DSCR.
2. For a borrower qualifying using the subject property's actual or market cashflow under a business purpose transaction, require execution with loan documents of a Business Purpose Attestation (Exhibit 8) or other similar attestation approved by Acra; do not assume from this excerpt that every program loan is a business-purpose transaction.
3. For all borrowers purchasing or refinancing a one- to four-family investment property, require a One- to Four-Family Rider with the loan documents and rent loss insurance coverage per §23.40.

**Checks:**
- A 1007 is required on the DSCR transaction, including a No Ratio DSCR transaction.
- If the borrower qualifies using the subject property's actual or market cashflow under a business purpose transaction, the borrower executes with loan documents a Business Purpose Attestation (Exhibit 8) or other similar attestation approved by Acra.
- All borrowers purchasing or refinancing a one- to four-family investment property execute a One- to Four-Family Rider with the loan documents.
- Rent loss insurance coverage is provided per §23.40 for borrowers purchasing or refinancing a one- to four-family investment property.

**Reads:** dscr_documentation_type, loan_purpose, residential_unit_count, occupancy_subtype
**Missing data:** Whether the transaction is a business purpose transaction and whether qualification uses actual or market cashflow, Execution of the required attestation, where applicable, Execution of the One- to Four-Family Rider by all applicable borrowers, Rent loss insurance coverage and the requirements of §23.40

## acra-standard.program_scope_occupancy_and_transaction_setup.limit_application_and_real_estate_owned_listings

**Purpose:** Establish that only the property types specified by the guideline are required to be listed.

1. Check the properties required to be listed on the application or Schedule of Real Estate Owned.
2. Limit the required listings to the subject property, principal residence, and second homes.

**Checks:**
- Only the subject property, principal residence, and second homes are required to be listed on the application or Schedule of Real Estate Owned.

**Reads:** housing_history
**Missing data:** Properties listed on the application or Schedule of Real Estate Owned

## acra-standard.program_scope_occupancy_and_transaction_setup.set_rent_based_qualification

**Purpose:** Establish the permitted qualification method and follow the stated income-documentation and DTI instructions.

1. Qualify the loan on the subject property's rent rather than the borrower's income.
2. Identify whether the loan qualifies using a calculated DSCR or as No Ratio DSCR, where no ratio is calculated.
3. For calculated DSCR, apply the stated minimum when LTV is above 80%; where DSCR is below 1.0, apply the stated caps.
4. Do not require borrowing entity income documentation.
5. For applicants qualifying using a DSCR, do not calculate DTI; income or employment listed on an application is superfluous to the underwrite and may be left blank, and if represented, a DTI should not be calculated.

**Checks:**
- Qualification is based on the subject property's rent rather than the borrower's income.
- The qualification method is either calculated DSCR or No Ratio DSCR, where no ratio is calculated.
- If LTV is above 80%, calculated DSCR is at least 1.20.
- If DSCR is below 1.0, the applicable caps are met.
- Borrowing entity income documentation is not required.
- For applicants qualifying using a DSCR, DTI is not calculated.

**Reads:** dscr_documentation_type, gross_rental_income
**Missing data:** Calculated DSCR, if applicable, LTV, if applicable, The caps applicable when DSCR is below 1.0

## acra-standard.program_scope_occupancy_and_transaction_setup.verify_investment_property_occupancy

**Purpose:** Establish that the property is investment property and is non-owner occupied as required by the program.

1. Confirm the occupancy is investment property (non-owner occupied) only.
2. Confirm the property fits the stated one- to four-unit residential dwelling or condominium-complex/PUD-unit description.
3. Confirm the owner does not occupy the dwelling.
4. Confirm the dwelling is leased.
5. Confirm it is occupied as a principal year-round residence by individuals other than the owner.

**Checks:**
- Occupancy is investment property (non-owner occupied).
- The property is a one- to four-unit residential dwelling or a unit in a condominium complex or a PUD.
- The individual owner does not occupy the dwelling.
- The dwelling is leased.
- The dwelling is occupied as a principal year-round residence by individuals other than the owner.

**Reads:** occupancy_subtype, residential_unit_count, property_type, current_lease_in_place, vacant_property
**Missing data:** Confirmation that the individual owner does not occupy the dwelling, Confirmation that the dwelling is leased and occupied by individuals other than the owner as their principal year-round residence

## acra-standard.property_eligibility_and_property_specific_overlays.apply_above_80_00_ltv_property_restriction

**Purpose:** Determine whether a property with LTV above 80.00% is among the types permitted by the stated restriction.

1. Determine whether LTV is above 80.00%.
2. If LTV is above 80.00%, verify that the property is SFR, Warrantable Condo outside of Florida, Townhome or PUD.

**Checks:**
- If LTV is above 80.00%, the property is SFR, Townhome, PUD, or a Warrantable Condo outside of Florida.

**Reads:** property_type, property_state
**Missing data:** LTV

## acra-standard.property_eligibility_and_property_specific_overlays.apply_rural_or_unique_property_overlay

**Purpose:** Determine whether an applicable rural or unique property meets its printed CLTV, FICO and DSCR requirements.

1. Determine whether the property is rural or unique.
2. For an applicable property, compare CLTV with the maximum: 80% for purchase, 75% for refinance — rate & term, or 70% for refinance — cash-out.
3. Verify minimum FICO 700.
4. Verify minimum DSCR 1.00.
5. Determine whether marketing time is excessive or the property exhibits unusual, inadequate or peculiar functionality; if so, review whether LTV may be further reduced.

**Checks:**
- If the property is rural or unique, CLTV does not exceed the maximum for its purpose: 80% for purchase, 75% for refinance — rate & term, or 70% for refinance — cash-out.
- If the property is rural or unique, FICO is at least 700.
- If the property is rural or unique, DSCR is at least 1.00.
- If marketing time is excessive or the property exhibits unusual, inadequate or peculiar functionality, any further LTV reduction determined to apply is applied.

**Reads:** rural_property, loan_purpose, cltv_pct, fico
**Missing data:** DSCR calculation or documentation, Whether marketing time is excessive, Whether the property exhibits unusual, inadequate or peculiar functionality, Any determination of a further LTV reduction

## acra-standard.property_eligibility_and_property_specific_overlays.apply_state_and_declining_market_overlays

**Purpose:** Determine whether the property is in the ineligible state and apply the stated declining-market CLTV overlay where applicable.

1. Check the subject property state; a property in SD is ineligible.
2. Determine whether the subject property is in a declining market.
3. For a declining-market property, apply the stated “-5% CLTV property/borrower full profile” overlay; obtain Acra confirmation on how the reduction combines with other caps.

**Checks:**
- The subject property is not in SD.
- If the property is in a declining market, the “-5% CLTV property/borrower full profile” overlay is applied.
- If the property is in a declining market, Acra has confirmed how the reduction combines with other caps.

**Reads:** property_state, cltv_pct, property_type, loan_purpose
**Missing data:** Whether the subject property is in a declining market, Acra confirmation on how the declining-market reduction combines with other caps, The applicable CLTV cap and property/borrower full profile used to apply the reduction

## acra-standard.property_eligibility_and_property_specific_overlays.check_property_type_eligibility_and_caps

**Purpose:** Determine whether the property type is eligible and whether the applicable printed type cap and Florida condition are met.

1. Check whether the property type is one of: SFR, Townhome, PUD, Warrantable Condo, Non-Warrantable Condo, Condotel / PUDtel, 2-4 Units, Manufactured.
2. For a Non-Warrantable Condo, compare CLTV with the printed cap: 80% for Purchase, 75% for Refi R/T, or 75% for Refi C/O.
3. For a Condotel / PUDtel, compare CLTV with the printed cap: 75% for Purchase, 70% for Refi R/T, or 65% for Refi C/O.
4. For a 2-4 Unit property, apply the printed “Max CLTV: 80%” cap, with no purpose split.
5. For a Manufactured Home, compare CLTV with the printed cap: 65% for Purchase, 60% for Refi R/T, or 60% for Refi C/O.
6. For a Florida Non-Warrantable Condo or Condotel / PUDtel, apply the printed “-5% CLTV” condition.
7. For a Non-Warrantable Condo or Condotel / PUDtel, verify the printed Min DSCR: 1.0 condition.

**Checks:**
- The property type is on the printed eligible property types list.
- A Non-Warrantable Condo meets the printed cap for its loan purpose: 80% for Purchase, 75% for Refi R/T, or 75% for Refi C/O.
- A Condotel / PUDtel meets the printed cap for its loan purpose: 75% for Purchase, 70% for Refi R/T, or 65% for Refi C/O.
- A 2-4 Unit property meets the printed “Max CLTV: 80%” cap.
- A Manufactured Home meets the printed cap for its loan purpose: 65% for Purchase, 60% for Refi R/T, or 60% for Refi C/O.
- For a Florida Non-Warrantable Condo or Condotel / PUDtel, the printed “-5% CLTV” condition is applied.
- A Non-Warrantable Condo or Condotel / PUDtel has Min DSCR: 1.0.

**Reads:** property_type, loan_purpose, property_state, cltv_pct
**Missing data:** DSCR calculation or documentation for the Min DSCR: 1.0 condition

## acra-standard.property_eligibility_and_property_specific_overlays.confirm_dscr_rent_documentation

**Purpose:** Determine whether a DSCR transaction has the required Form 1007 documentation, including a No Ratio DSCR transaction.

1. Determine whether the transaction is a DSCR transaction, including whether it is No Ratio DSCR.
2. For a DSCR transaction, verify that a Form 1007 is provided.
3. For a 2-4 unit property where Form 1025 is offered as satisfying the requirement, obtain Acra confirmation; the policy does not resolve whether Form 1025 satisfies it.

**Checks:**
- For a DSCR transaction, a Form 1007 is provided, including for No Ratio DSCR.
- For a 2-4 unit property relying on Form 1025 instead of Form 1007, Acra has confirmed whether Form 1025 satisfies the requirement.

**Reads:** dscr_documentation_type, property_type
**Missing data:** Whether the transaction is DSCR, including No Ratio DSCR, Form 1007, Whether Form 1025 is being offered instead of Form 1007, Acra confirmation on whether Form 1025 satisfies the requirement for a 2-4 unit property

## acra-standard.property_eligibility_and_property_specific_overlays.determine_rent_loss_insurance_requirement

**Purpose:** Determine whether six (6) months' rent loss insurance is required and whether the stated reserve substitution applies.

1. Determine whether the property is a one- to four-unit non-owner occupied income property.
2. Determine whether LTV is > 70% and subject property rents are used to qualify, including No Ratio DSCR.
3. If the stated conditions apply, require six (6) months' rent loss insurance.
4. Apply the printed exemption: loans with ≤ 70% CLTV are not required to carry rent loss insurance. Obtain Acra confirmation for the case of LTV at or below 70% with CLTV above 70%.
5. If rent loss insurance is required but cannot be obtained, allow the borrower to substitute two (2) months reserves for every one (1) month of rent loss coverage not provided.

**Checks:**
- The property is a one- to four-unit non-owner occupied income property when the insurance trigger is applied.
- Where LTV is > 70% and subject property rents are used to qualify, six (6) months' rent loss insurance is provided.
- Loans with ≤ 70% CLTV are not required to carry rent loss insurance.
- For LTV at or below 70% with CLTV above 70%, Acra has confirmed the treatment.
- When required rent loss insurance cannot be obtained, the borrower provides two (2) months reserves for every one (1) month of rent loss coverage not provided.

**Reads:** residential_unit_count, occupancy_subtype, cltv_pct, dscr_documentation_type, gross_rental_income
**Missing data:** LTV, Whether the property is an income property and non-owner occupied, Whether subject property rents are used to qualify, including No Ratio DSCR, Rent loss insurance coverage and whether it can be obtained, Acra confirmation for LTV at or below 70% with CLTV above 70%, Reserves available for any substitution

## acra-standard.property_eligibility_and_property_specific_overlays.review_mixed_use_property

**Purpose:** Determine whether a mixed-use property meets the stated minimum DSCR and whether the conditions referenced in §10.7 have been reviewed.

1. Determine whether the property is mixed use, meaning a portion of its space is dedicated to commercial use and the rest to residential use.
2. For a mixed-use property, verify a minimum DSCR ratio of 1.2.
3. Review the conditions in §10.7, including the restrictions regarding Adult Care / Assisted Living Facilities; the section is not reproduced in the source excerpt.

**Checks:**
- A mixed-use property has a minimum DSCR ratio of 1.2.
- The applicable conditions and restrictions in §10.7 have been reviewed.

**Reads:** mixed_use
**Missing data:** DSCR calculation or documentation, The complete §10.7 conditions and restrictions, including those regarding Adult Care / Assisted Living Facilities, Property-use information establishing the commercial and residential portions

## acra-standard.property_eligibility_and_property_specific_overlays.review_property_listed_for_sale

**Purpose:** Determine whether the §11.5 requirements for a property listed for sale apply and are met.

1. Determine whether the property was listed for sale in the last six months, measured from the last date of being listed to the Application Date.
2. For a property in scope, verify that the property is not in default or otherwise delinquent on lien(s).
3. For an investment property in scope, verify that the subject is occupied by a tenant and is not vacant.
4. Verify qualification as either ≥ 1.0 DSCR or 43% maximum DTI.
5. Verify a prepayment penalty of at least three (3) years unless the property is in a state that does not allow prepayment penalties.
6. Verify twenty-four (24) months of reserves; cash-in-hand may be considered if otherwise consistent with the Guide.
7. Verify a fully amortizing term and no interest only.
8. Verify maximum LTV / CLTV of 65% based on the lesser of appraised value or lowest recent listing price.
9. Verify no subordinate financing and impounds.

**Checks:**
- The property was listed for sale in the last six months, measured from the last date of being listed to the Application Date, for this overlay to apply.
- The property is not in default or otherwise delinquent on lien(s).
- For an investment property, the subject is occupied by a tenant and is not vacant.
- The loan qualifies as either ≥ 1.0 DSCR or 43% maximum DTI.
- A prepayment penalty of at least three (3) years is in place unless the property is in a state that does not allow prepayment penalties.
- Reserves are twenty-four (24) months, with cash-in-hand considered only if otherwise consistent with the Guide.
- The loan has a fully amortizing term.
- The loan is not interest only.
- LTV / CLTV does not exceed 65% based on the lesser of appraised value or lowest recent listing price.
- No subordinate financing is present.
- Impounds are in place.

**Reads:** listed_for_sale_last_6_months, loan_purpose, occupancy_subtype, current_lease_in_place, vacant_property, reserves_months, product_is_interest_only, cltv_pct, property_value, property_state
**Missing data:** Last date the property was listed for sale, Application Date, Lien status and default or delinquency information, Whether the property is an investment property and evidence of tenant occupancy, DSCR calculation or documentation, DTI calculation or documentation, Prepayment penalty duration, Whether the property state does not allow prepayment penalties, Reserve documentation and whether cash-in-hand is consistent with the Guide, Amortization terms, Appraised value and lowest recent listing price, Subordinate financing information, Impound status

## acra-standard.property_eligibility_and_property_specific_overlays.review_required_property_listings

**Purpose:** Determine whether the reviewer applies only the stated property-listing requirement.

1. Review the property-listing requirement on the application or Schedule of Real Estate Owned.
2. Require listing only of the subject property, principal residence and second homes.

**Checks:**
- The properties required to be listed on the application or Schedule of Real Estate Owned are limited to the subject property, principal residence and second homes.
**Missing data:** Application or Schedule of Real Estate Owned, Identification of the subject property, principal residence and second homes

## acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_cash_out_refinance

**Purpose:** Determine whether a vacant-property cash-out refinance meets the Summary conditions stated in the source.

1. Determine whether the property is vacant and the transaction is a cash-out refinance.
2. Verify minimum 700 FICO.
3. Verify DSCR ≥ 1.15.
4. Verify ≥ 3-year PPP where allowable.
5. Verify no interest only, impounds required, and 6 months reserves.
6. For a loan amount under $1,500,000, verify Max CLTV 60%.
7. Verify ≥15 months ownership.
8. Obtain Acra confirmation for loans of $1,500,000 or more and for how the 15 months are measured.

**Checks:**
- FICO is at least 700.
- DSCR is ≥ 1.15.
- A ≥ 3-year PPP is in place where allowable.
- The loan is not interest only.
- Impounds are in place.
- Reserves are at least 6 months.
- For a loan amount under $1,500,000, CLTV does not exceed 60%.
- Ownership is ≥15 months.
- Acra has confirmed treatment for loans of $1,500,000 or more and how the 15 months are measured.

**Reads:** vacant_property, loan_purpose, fico, loan_amount, cltv_pct, product_is_interest_only, reserves_months, ownership_months
**Missing data:** DSCR calculation or documentation, PPP duration and whether it is allowable, Impound status, Acra confirmation for loans of $1,500,000 or more, Acra confirmation on how the 15 months of ownership are measured

## acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_purchase

**Purpose:** Determine whether a vacant property purchase is permitted and whether qualifying rents come from the stated source.

1. Determine whether the property is vacant and the transaction is a purchase.
2. For a vacant property purchase, verify that qualifying rents are taken from the 1007 or 1025.

**Checks:**
- For a vacant property purchase, qualifying rents are taken from the 1007 or 1025.

**Reads:** vacant_property, loan_purpose
**Missing data:** Form 1007 or Form 1025 showing qualifying rents

## acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_rate_and_term_refinance

**Purpose:** Determine whether a vacant-property rate and term refinance meets §10.17 as printed.

1. Determine whether the property is vacant and the transaction is a rate and term refinance.
2. Verify minimum 700 FICO score.
3. Apply the printed loan-amount and CLTV limits: maximum $1,000,000 to maximum 70% CLTV; maximum $2,000,000 to maximum 65% CLTV.
4. Verify minimum 1.000 DSCR or maximum 40.0% DTI.
5. Verify a minimum two-year prepayment penalty where allowable.
6. Verify full amortization and no interest-only program.
7. Verify impounds and minimum six months reserves.
8. Obtain Acra confirmation for treatment at exactly $1,000,000 and $2,000,000.

**Checks:**
- FICO is at least 700.
- The loan amount and CLTV meet the applicable printed limits: maximum $1,000,000 to maximum 70% CLTV; maximum $2,000,000 to maximum 65% CLTV.
- DSCR is at least 1.000 or DTI is no more than 40.0%.
- A minimum two-year prepayment penalty is in place where allowable.
- The loan is fully amortizing.
- The loan is not an interest-only program.
- Impounds are in place.
- Reserves are at least six months.
- Acra has confirmed treatment if the loan amount is exactly $1,000,000 or $2,000,000.

**Reads:** vacant_property, loan_purpose, fico, loan_amount, cltv_pct, product_is_interest_only, reserves_months
**Missing data:** DSCR calculation or documentation, DTI calculation or documentation, Prepayment penalty duration and whether it is allowable, Amortization terms, Impound status, Acra confirmation for treatment at exactly $1,000,000 or $2,000,000

## acra-standard.property_eligibility_and_property_specific_overlays.verify_investment_property_rider

**Purpose:** Determine whether each borrower in scope executes the required rider with the loan documents.

1. Determine whether the borrower is purchasing or refinancing a one- to four-family investment property.
2. For each borrower in scope, verify execution of a One- to Four-Family Rider with the loan documents.

**Checks:**
- Each borrower purchasing or refinancing a one- to four-family investment property executes a One- to Four-Family Rider with the loan documents.

**Reads:** loan_purpose, property_type, occupancy_subtype
**Missing data:** Whether the property is an investment property, Whether the transaction is a purchase or refinance, Executed loan documents and One- to Four-Family Rider
