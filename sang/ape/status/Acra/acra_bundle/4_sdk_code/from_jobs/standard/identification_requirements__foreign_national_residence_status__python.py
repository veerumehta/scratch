# rule: acra-standard.identification_requirements.foreign_national_residence_status.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.foreign_national_residence_status
# reads: Borrower.citizenship_status
# implements job: acra-standard.identification_requirements.foreign_national_residence_status

import rules_lib

def check(ctx):
    citizenship = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship=citizenship)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(citizenship, 'Foreign National')
