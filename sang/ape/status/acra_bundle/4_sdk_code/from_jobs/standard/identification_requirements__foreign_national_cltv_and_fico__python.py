# rule: acra-standard.identification_requirements.foreign_national_cltv_and_fico.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.foreign_national_cltv_and_fico
# reads: Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent, CreditReport.representative_score
# implements job: acra-standard.identification_requirements.foreign_national_cltv_and_fico

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
    score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(purpose=purpose, cltv=cltv, score=score)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'purchase'):
        cltv_limit = 70
    elif rules_lib.same(
        purpose,
        'refinance rate & term', 'rate & term refinance', 'rate & term',
        'refinance rate and term', 'rate and term refinance',
        'refinance cash-out', 'cash-out refinance', 'cash-out',
    ):
        cltv_limit = 65
    else:
        cltv_limit = None

    return score == 700 and (cltv_limit is None or cltv <= cltv_limit)
