# rule: acra-standard.loan_program_eligibility.loan_amount_below_200_000_cltv_limit.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.loan_amount_below_200_000_cltv_limit
# reads: LoanCore.total_loan_amount_usd, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.loan_program_eligibility.loan_amount_below_200_000_cltv_limit

import rules_lib

def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    purpose = ctx['LoanCore.loan_purpose']

    missing = rules_lib.gaps(amount=amount, purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if amount >= 200000:
        return True

    if rules_lib.same(purpose, 'purchase'):
        limit = 80
    elif rules_lib.same(purpose, 'rate & term', 'cash-out', 'cash-out refinance'):
        limit = 75
    else:
        return True

    cltv_percent = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv_percent=cltv_percent)
    if missing:
        return rules_lib.unknown(*missing)

    cltv = rules_lib.percent(cltv_percent, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv_percent')
    return cltv <= limit
