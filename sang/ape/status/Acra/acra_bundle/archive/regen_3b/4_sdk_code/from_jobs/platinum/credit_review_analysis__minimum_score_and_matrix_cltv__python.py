# rule: acra-platinum.credit_review_analysis.minimum_score_and_matrix_cltv.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis.minimum_score_and_matrix_cltv
# reads: CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.loan_purpose
# implements job: acra-platinum.credit_review_analysis.minimum_score_and_matrix_cltv

import rules_lib

def check(ctx):
    score = ctx['CreditReport.representative_score']
    cltv = ctx['LoanCore.cltv_percent']
    purpose = ctx['LoanCore.loan_purpose']

    missing = rules_lib.gaps(score=score, cltv=cltv, loan_purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    # The 700 row applies through 720; the next printed threshold is 721.
    tier = rules_lib.band(score, [(699, 0), (720, 700), (729, 721)], above=730)
    if tier is None:
        return rules_lib.unknown('score')
    if tier == 0:
        return False

    if rules_lib.same(purpose, 'purchase') or rules_lib.same(purpose, 'rate & term'):
        maximum = 80
    elif rules_lib.same(purpose, 'cash-out'):
        maximum = rules_lib.band(score, [(720, 55), (729, 65)], above=75)
        if maximum is None:
            return rules_lib.unknown('score')
    else:
        return rules_lib.unknown('loan_purpose')

    within_maximum = rules_lib.band(cltv, [(maximum, True)], above=False)
    if within_maximum is None:
        return rules_lib.unknown('cltv')
    return within_maximum
