# rule: acra-standard.credit_review_analysis_credit.bankruptcy_and_foreclosure_cltv_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis_credit.bankruptcy_and_foreclosure_cltv_limits
# reads: Borrower.has_bankruptcy_or_foreclosure, Borrower.months_since_bankruptcy_or_foreclosure, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis_credit.bankruptcy_and_foreclosure_cltv_limits

import rules_lib

def check(ctx):
    has_history = ctx['Borrower.has_bankruptcy_or_foreclosure']
    months = ctx['Borrower.months_since_bankruptcy_or_foreclosure']
    purpose = ctx['LoanCore.loan_purpose']
    cltv = ctx['LoanCore.cltv_percent']

    missing = rules_lib.gaps(
        has_history=has_history,
        months=months,
        purpose=purpose,
        cltv=cltv,
    )
    if missing:
        return rules_lib.unknown(*missing)

    has_history = rules_lib.flag(has_history)
    if has_history is None:
        return rules_lib.unknown('Borrower.has_bankruptcy_or_foreclosure')
    if not has_history:
        return True

    if rules_lib.same(purpose, 'purchase'):
        purchase = True
    elif rules_lib.same(purpose, 'refi r/t', 'refi c/o'):
        purchase = False
    else:
        return rules_lib.unknown('LoanCore.loan_purpose')

    cltv_percent = rules_lib.percent(cltv, 'percent')
    if cltv_percent is None:
        return rules_lib.unknown('LoanCore.cltv_percent')

    if months < 12:
        return False
    if months < 24:
        maximum = 65
    elif months < 36:
        maximum = 80 if purchase else 75
    else:
        return True

    return cltv_percent <= maximum
