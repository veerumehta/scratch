# rule: acra-standard.credit_review_analysis.foreign_national_cltv_limit.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.foreign_national_cltv_limit
# reads: Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis.foreign_national_cltv_limit

import rules_lib

def check(ctx):
    citizenship = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship=citizenship)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(citizenship, 'Foreign National'):
        return True

    purpose = ctx['LoanCore.loan_purpose']
    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(purpose=purpose, cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'purchase'):
        limit = 70
    elif rules_lib.same(
        purpose,
        'refinance',
        'rate & term refinance',
        'rate/term refinance',
        'refinance rate & term',
        'refinance - rate & term',
        'cash-out refinance',
        'cash out refinance',
        'refinance cash-out',
        'refinance cash out',
        'cash-out',
        'cash out',
    ):
        limit = 65
    else:
        return True

    return cltv <= limit
