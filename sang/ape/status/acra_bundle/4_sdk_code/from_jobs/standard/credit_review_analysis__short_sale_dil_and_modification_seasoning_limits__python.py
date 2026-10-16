# rule: acra-standard.credit_review_analysis.short_sale_dil_and_modification_seasoning_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.short_sale_dil_and_modification_seasoning_limits
# reads: Borrower.months_since_short_sale_dil_or_modification, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis.short_sale_dil_and_modification_seasoning_limits

import rules_lib

def check(ctx):
    months = ctx['Borrower.months_since_short_sale_dil_or_modification']
    missing = rules_lib.gaps(months=months)
    if missing:
        return rules_lib.unknown(*missing)

    if months >= 24:
        return True

    purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'purchase'):
        purchase = True
        limit = 80 if months >= 12 else 75
    elif rules_lib.same(purpose, 'refinance', 'refi', 'refi r/t', 'refi c/o', 'rate & term refinance', 'rate and term refinance', 'cash-out refinance', 'cash out refinance'):
        purchase = False
        limit = 75 if months >= 12 else 70
    else:
        return True

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    return cltv <= limit
