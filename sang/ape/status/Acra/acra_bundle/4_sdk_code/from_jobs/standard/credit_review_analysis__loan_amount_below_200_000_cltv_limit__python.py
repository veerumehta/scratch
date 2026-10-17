# rule: acra-standard.credit_review_analysis.loan_amount_below_200_000_cltv_limit.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.loan_amount_below_200_000_cltv_limit
# reads: LoanCore.total_loan_amount_usd, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis.loan_amount_below_200_000_cltv_limit

import rules_lib


def check(ctx):
    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)

    if loan_amount >= 200000:
        return True

    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'purchase'):
        limit = 80
    elif rules_lib.same(
        loan_purpose,
        'refinance',
        'rate & term refinance',
        'rate and term refinance',
        'refinance rate & term',
        'refinance rate and term',
        'cash-out refinance',
        'cash out refinance',
        'refinance cash-out',
        'refinance cash out',
    ):
        limit = 75
    else:
        return True

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    return cltv <= limit
