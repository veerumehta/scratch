# rule: acra-platinum.loan_program_eligibility.borrower_citizenship.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.borrower_citizenship
# reads: Borrower.citizenship_status
# implements job: acra-platinum.loan_program_eligibility.borrower_citizenship

import rules_lib

def check(ctx):
    citizenship_status = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship_status=citizenship_status)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(citizenship_status, 'US Citizen', 'Permanent Resident')
