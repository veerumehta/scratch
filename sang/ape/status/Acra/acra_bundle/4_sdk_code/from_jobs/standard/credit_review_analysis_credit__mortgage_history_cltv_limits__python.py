# rule: acra-standard.credit_review_analysis_credit.mortgage_history_cltv_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis_credit.mortgage_history_cltv_limits
# reads: CreditReport.housing_history_rating, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis_credit.mortgage_history_cltv_limits

import rules_lib


def check(ctx):
    history = ctx['CreditReport.housing_history_rating']
    purpose = ctx['LoanCore.loan_purpose']
    cltv_raw = ctx['LoanCore.cltv_percent']

    missing = rules_lib.gaps(history=history, purpose=purpose, cltv_raw=cltv_raw)
    if missing:
        return rules_lib.unknown(*missing)

    cltv = rules_lib.percent(cltv_raw, 'percent')
    if cltv is None:
        return rules_lib.unknown('LoanCore.cltv_percent')

    if rules_lib.same(purpose, 'Purchase'):
        purchase = True
    elif rules_lib.same(purpose, 'Refi R/T', 'Refi C/O'):
        purchase = False
    else:
        return rules_lib.unknown('LoanCore.loan_purpose')

    if rules_lib.same(history, '1x30x12'):
        maximum = 80 if purchase else 75
    elif rules_lib.same(history, '0x60x12'):
        maximum = 75 if purchase else 70
    elif rules_lib.same(history, '0x90x12'):
        maximum = 65
    elif rules_lib.same(history, '0x120x12'):
        return False
    else:
        return rules_lib.unknown('CreditReport.housing_history_rating')

    return cltv <= maximum
