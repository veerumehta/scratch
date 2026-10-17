# rule: acra-standard.identification_requirements.itin_cltv_tier.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.itin_cltv_tier
# reads: Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent, CreditReport.representative_score
# implements job: acra-standard.identification_requirements.itin_cltv_tier

import rules_lib

def check(ctx):
    citizenship = ctx['Borrower.citizenship_status']
    loan_purpose = ctx['LoanCore.loan_purpose']
    cltv = ctx['LoanCore.cltv_percent']
    score = ctx['CreditReport.representative_score']

    missing = rules_lib.gaps(
        citizenship=citizenship,
        loan_purpose=loan_purpose,
        cltv=cltv,
        score=score,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(citizenship, 'ITIN'):
        return True

    if rules_lib.same(loan_purpose, 'purchase'):
        transaction = 'purchase'
    elif rules_lib.same(
        loan_purpose,
        'refinance',
        'rate and term refinance',
        'rate/term refinance',
        'R/T refinance',
        'cash-out refinance',
        'cash out refinance',
    ):
        transaction = 'refinance'
    else:
        return True

    score_band = rules_lib.band(
        score,
        [(659, '640-659'), (699, '660-699'), (700, '700')],
        above='outside',
    )
    if score_band is None:
        return rules_lib.unknown('score')
    if score_band == '640-659' and score < 640:
        return True
    if score_band == 'outside':
        return True

    limits = {
        ('700', 'purchase'): 70,
        ('700', 'refinance'): 65,
        ('660-699', 'purchase'): 65,
        ('660-699', 'refinance'): 60,
        ('640-659', 'purchase'): 60,
        ('640-659', 'refinance'): 60,
    }
    limit = limits[(score_band, transaction)]
    result = rules_lib.band(cltv, [(limit, True)], above=False)
    if result is None:
        return rules_lib.unknown('cltv')
    return result
