# rule: acra-standard.identification_requirements.itin_loan_amount_and_minimum_fico.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.itin_loan_amount_and_minimum_fico
# reads: Borrower.citizenship_status, LoanCore.total_loan_amount_usd, CreditReport.representative_score
# implements job: acra-standard.identification_requirements.itin_loan_amount_and_minimum_fico

import rules_lib


def check(ctx):
    citizenship_status = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship_status=citizenship_status)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(citizenship_status, 'ITIN'):
        return True

    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    representative_score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(loan_amount=loan_amount, representative_score=representative_score)
    if missing:
        return rules_lib.unknown(*missing)

    return loan_amount <= 1000000 and representative_score >= 640
