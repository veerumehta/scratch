# rule: acra-standard.loan_program_eligibility.itin_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.itin_limits
# reads: LoanCore.total_loan_amount_usd, CreditReport.representative_score, LoanCore.cltv_percent, LoanCore.loan_purpose
# implements job: acra-standard.loan_program_eligibility.itin_limits

import rules_lib

def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    fico = ctx['CreditReport.representative_score']
    cltv = ctx['LoanCore.cltv_percent']
    purpose = ctx['LoanCore.loan_purpose']

    missing = rules_lib.gaps(amount=amount, fico=fico, cltv=cltv, purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if amount > 1000000 or fico < 640:
        return False

    limits = rules_lib.band(
        fico,
        [(659, (60, 60)), (699, (65, 60)), (700, (70, 65))],
    )
    # The printed “FICO 700” tier is not extended to higher scores here;
    # that application is left for Acra confirmation.
    if limits is None:
        return True

    if rules_lib.same(purpose, 'purchase'):
        purpose_index = 0
    elif rules_lib.same(purpose, 'refinance', 'rate & term', 'rate and term', 'r/t', 'cash-out', 'cash out'):
        purpose_index = 1
    else:
        return rules_lib.unknown('LoanCore.loan_purpose (unrecognized purpose)')

    return cltv <= limits[purpose_index]
