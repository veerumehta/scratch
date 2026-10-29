# rule: acra-standard.identification_requirements.borrower_citizenship_type.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.borrower_citizenship_type
# reads: Borrower.citizenship_status
# implements job: acra-standard.identification_requirements.borrower_citizenship_type

import rules_lib

def check(ctx):
    citizenship_status = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship_status=citizenship_status)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(
        citizenship_status,
        'US Citizen',
        'Permanent Resident',
        'Non-Permanent Resident',
        'Foreign National',
        'ITIN',
    )
