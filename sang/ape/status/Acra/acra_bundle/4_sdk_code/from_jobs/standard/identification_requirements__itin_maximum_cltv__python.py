# rule: acra-standard.identification_requirements.itin_maximum_cltv.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.itin_maximum_cltv
# reads: Borrower.citizenship_status, CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.loan_purpose
# implements job: acra-standard.identification_requirements.itin_maximum_cltv

import rules_lib


def check(ctx):
    citizenship = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship=citizenship)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(citizenship, 'ITIN'):
        return True

    score = ctx['CreditReport.representative_score']
    cltv = ctx['LoanCore.cltv_percent']
    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(score=score, cltv=cltv, loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    purchase = rules_lib.same(loan_purpose, 'purchase')
    refinance = rules_lib.same(loan_purpose, 'refinance', 'R/T', 'rate & term', 'cash-out')
    if not purchase and not refinance:
        return rules_lib.unknown('loan_purpose')

    below_minimum = rules_lib.band(score, [(639, True)], above=False)
    if below_minimum is None:
        return rules_lib.unknown('score')
    if below_minimum:
        return False

    tier_cap = rules_lib.band(score, [(659, 60), (699, 65)], above=None)
    if tier_cap is None:
        return rules_lib.unknown('Acra confirmation on whether the printed FICO 700 tier means 700 and above')

    cap = tier_cap if purchase and tier_cap == 65 else 60
    cltv_value = rules_lib.percent(cltv, 'percent')
    if cltv_value is None:
        return rules_lib.unknown('cltv')
    return cltv_value <= cap
