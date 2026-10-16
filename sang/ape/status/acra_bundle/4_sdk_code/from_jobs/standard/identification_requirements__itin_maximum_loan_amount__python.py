# rule: acra-standard.identification_requirements.itin_maximum_loan_amount.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.itin_maximum_loan_amount
# reads: Borrower.citizenship_status, LoanCore.total_loan_amount_usd
# implements job: acra-standard.identification_requirements.itin_maximum_loan_amount

import rules_lib

def check(ctx):
    citizenship = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship=citizenship)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(citizenship, 'ITIN'):
        return True

    total_loan_amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(total_loan_amount=total_loan_amount)
    if missing:
        return rules_lib.unknown(*missing)

    return total_loan_amount <= 1_000_000.0
