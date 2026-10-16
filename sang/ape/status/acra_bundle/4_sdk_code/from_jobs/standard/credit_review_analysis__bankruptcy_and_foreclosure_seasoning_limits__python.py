# rule: acra-standard.credit_review_analysis.bankruptcy_and_foreclosure_seasoning_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.bankruptcy_and_foreclosure_seasoning_limits
# reads: Borrower.months_since_bankruptcy_or_foreclosure, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis.bankruptcy_and_foreclosure_seasoning_limits

import rules_lib


def check(ctx):
    months = ctx['Borrower.months_since_bankruptcy_or_foreclosure']
    missing = rules_lib.gaps(**{'Borrower.months_since_bankruptcy_or_foreclosure': months})
    if missing:
        return rules_lib.unknown(*missing)

    if months >= 36:
        return True
    if months < 12:
        return False

    purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(**{'LoanCore.loan_purpose': purpose})
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'purchase'):
        limit = 80 if months >= 24 else 65
    elif any(rules_lib.same(purpose, option) for option in (
        'refinance',
        'refi r/t',
        'refi c/o',
        'refinance rate & term',
        'refinance cash out',
        'rate & term',
        'cash out',
    )):
        limit = 75 if months >= 24 else 65
    else:
        return True

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(**{'LoanCore.cltv_percent': cltv})
    if missing:
        return rules_lib.unknown(*missing)

    return cltv <= limit
