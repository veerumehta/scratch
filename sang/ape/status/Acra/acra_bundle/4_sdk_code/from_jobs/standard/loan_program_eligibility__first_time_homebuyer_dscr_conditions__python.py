# rule: acra-standard.loan_program_eligibility.first_time_homebuyer_dscr_conditions.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.first_time_homebuyer_dscr_conditions
# reads: CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.total_loan_amount_usd, MortgageLoanInformation.is_interest_only, LoanCore.is_escrow_waived, RatioSet.reserves_months
# implements job: acra-standard.loan_program_eligibility.first_time_homebuyer_dscr_conditions

import rules_lib

def check(ctx):
    fico = ctx['CreditReport.representative_score']
    cltv = ctx['LoanCore.cltv_percent']
    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    interest_only = ctx['MortgageLoanInformation.is_interest_only']
    escrow_waived = ctx['LoanCore.is_escrow_waived']
    reserves = ctx['RatioSet.reserves_months']

    missing = rules_lib.gaps(
        fico=fico,
        cltv=cltv,
        loan_amount=loan_amount,
        interest_only=interest_only,
        escrow_waived=escrow_waived,
        reserves=reserves,
    )
    if missing:
        return rules_lib.unknown(*missing)

    cltv_value = rules_lib.percent(cltv, 'percent')
    interest_only_flag = rules_lib.flag(interest_only)
    escrow_waived_flag = rules_lib.flag(escrow_waived)
    if cltv_value is None:
        return rules_lib.unknown('cltv')
    if interest_only_flag is None:
        return rules_lib.unknown('interest_only')
    if escrow_waived_flag is None:
        return rules_lib.unknown('escrow_waived')

    return (
        fico >= 700
        and cltv_value <= 70
        and loan_amount <= 1000000
        and not interest_only_flag
        and not escrow_waived_flag
        and reserves >= 6
    )
