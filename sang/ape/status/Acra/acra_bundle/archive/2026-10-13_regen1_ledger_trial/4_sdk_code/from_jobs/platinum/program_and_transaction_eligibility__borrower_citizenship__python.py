# rule: acra-platinum.program_and_transaction_eligibility.borrower_citizenship.python
# origin: written from a job
# description: Python formalization of acra-platinum.program_and_transaction_eligibility.borrower_citizenship
# reads: citizenship_type
# implements job: acra-platinum.program_and_transaction_eligibility.borrower_citizenship

import rules_lib

def check(ctx):
    citizenship_type = ctx['citizenship_type']
    missing = rules_lib.gaps(citizenship_type=citizenship_type)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(citizenship_type, 'US Citizen', 'Permanent Resident')
