# rule: acra-standard.loan_program_eligibility.foreign_national_eligibility.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.foreign_national_eligibility
# reads: Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.loan_program_eligibility.foreign_national_eligibility

import rules_lib

def check(ctx):
    citizenship_status = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship_status=citizenship_status)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(citizenship_status, 'Foreign National'):
        return True

    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'purchase'):
        limit = 70
    elif rules_lib.same(
        loan_purpose,
        'rate & term',
        'rate & term refinance',
        'rate/term refinance',
        'cash-out',
        'cash-out refinance',
    ):
        limit = 65
    else:
        return True

    cltv_percent = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv_percent=cltv_percent)
    if missing:
        return rules_lib.unknown(*missing)

    return cltv_percent <= limit
