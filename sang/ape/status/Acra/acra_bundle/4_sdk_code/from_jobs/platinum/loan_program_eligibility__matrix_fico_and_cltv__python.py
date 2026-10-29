# rule: acra-platinum.loan_program_eligibility.matrix_fico_and_cltv.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.matrix_fico_and_cltv
# reads: CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-platinum.loan_program_eligibility.matrix_fico_and_cltv

import rules_lib


def check(ctx):
    score = ctx['CreditReport.representative_score']
    purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(representative_score=score, loan_purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    try:
        if score < 700:
            return False
        if score >= 730:
            row = 730
        elif score >= 721:
            row = 721
        else:
            row = 700
    except (TypeError, ValueError):
        return rules_lib.unknown('representative_score')

    if rules_lib.same(purpose, 'purchase'):
        maximum = 80
    elif rules_lib.same(purpose, 'rate & term refinance', 'rate & term'):
        maximum = 80
    elif rules_lib.same(purpose, 'cash-out refinance', 'cash-out'):
        maximum = {730: 75, 721: 65, 700: 55}[row]
    else:
        return True

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv_percent=cltv)
    if missing:
        return rules_lib.unknown(*missing)
    cltv_value = rules_lib.percent(cltv, 'percent')
    if cltv_value is None:
        return rules_lib.unknown('cltv_percent')
    return cltv_value <= maximum
