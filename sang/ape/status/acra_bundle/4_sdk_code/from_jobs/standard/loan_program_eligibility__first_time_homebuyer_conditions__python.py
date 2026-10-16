# rule: acra-standard.loan_program_eligibility.first_time_homebuyer_conditions.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.first_time_homebuyer_conditions
# reads: CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.total_loan_amount_usd, MortgageLoanInformation.is_interest_only, RatioSet.reserves_months
# implements job: acra-standard.loan_program_eligibility.first_time_homebuyer_conditions

import rules_lib

def check(ctx):
    representative_score = ctx['CreditReport.representative_score']
    cltv_percent = ctx['LoanCore.cltv_percent']
    total_loan_amount_usd = ctx['LoanCore.total_loan_amount_usd']
    is_interest_only = ctx['MortgageLoanInformation.is_interest_only']
    reserves_months = ctx['RatioSet.reserves_months']

    missing = rules_lib.gaps(
        representative_score=representative_score,
        cltv_percent=cltv_percent,
        total_loan_amount_usd=total_loan_amount_usd,
        is_interest_only=is_interest_only,
        reserves_months=reserves_months,
    )
    if missing:
        return rules_lib.unknown(*missing)

    is_interest_only = rules_lib.flag(is_interest_only)
    if is_interest_only is None:
        return rules_lib.unknown('MortgageLoanInformation.is_interest_only')

    return (
        representative_score >= 700
        and cltv_percent <= 70
        and total_loan_amount_usd <= 1_000_000
        and not is_interest_only
        and reserves_months >= 6
    )
