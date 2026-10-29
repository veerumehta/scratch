# rule: acra-standard.loan_program_eligibility.interest_only_10_yr_40_year_term_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.interest_only_10_yr_40_year_term_limits
# reads: LoanCore.is_interest_only_10_40, LoanCore.cltv_percent, LoanCore.total_loan_amount_usd
# implements job: acra-standard.loan_program_eligibility.interest_only_10_yr_40_year_term_limits

import rules_lib

def check(ctx):
    product = rules_lib.flag(ctx['LoanCore.is_interest_only_10_40'])
    missing = rules_lib.gaps(product=product)
    if missing:
        return rules_lib.unknown(*missing)
    if not product:
        return True

    cltv = ctx['LoanCore.cltv_percent']
    amount = ctx['LoanCore.total_loan_amount_usd']
    cltv_percent = rules_lib.percent(cltv, 'percent')
    missing = rules_lib.gaps(cltv_percent=cltv_percent, amount=amount)
    if missing:
        return rules_lib.unknown(*missing)
    return cltv_percent <= 80 and amount <= 3000000
