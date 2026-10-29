# rule: acra-platinum.loan_program_eligibility.matrix_cltv_limit.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.matrix_cltv_limit
# reads: CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.loan_purpose
# implements job: acra-platinum.loan_program_eligibility.matrix_cltv_limit

import rules_lib

def check(ctx):
    score = ctx['CreditReport.representative_score']
    cltv = ctx['LoanCore.cltv_percent']
    purpose = ctx['LoanCore.loan_purpose']

    missing = rules_lib.gaps(representative_score=score, cltv_percent=cltv, loan_purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    cash_out_limit = rules_lib.band(score, [(720, 0.55), (729, 0.65)], above=0.75)
    if cash_out_limit is None:
        return rules_lib.unknown('representative_score')
    if score < 700:
        return False

    if rules_lib.same(purpose, 'purchase') or rules_lib.same(purpose, 'rate & term'):
        limit = 0.80
    elif rules_lib.same(purpose, 'cash-out'):
        limit = cash_out_limit
    else:
        return False

    meets_limit = rules_lib.band(cltv, [(limit, True)], above=False)
    if meets_limit is None:
        return rules_lib.unknown('cltv_percent')
    return meets_limit
