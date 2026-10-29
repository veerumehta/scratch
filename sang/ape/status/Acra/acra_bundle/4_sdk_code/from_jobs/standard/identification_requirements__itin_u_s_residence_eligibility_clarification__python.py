# rule: acra-standard.identification_requirements.itin_u_s_residence_eligibility_clarification.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.itin_u_s_residence_eligibility_clarification
# reads: Borrower.citizenship_status
# implements job: acra-standard.identification_requirements.itin_u_s_residence_eligibility_clarification

import rules_lib

def check(ctx):
    citizenship_status = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship_status=citizenship_status)
    if missing:
        return rules_lib.unknown(*missing)

    itin_holder = rules_lib.same(citizenship_status, 'ITIN', 'US resident ITIN')
    return (itin_holder, {'acra_confirmation_required': itin_holder,
                          'eligibility_determined': False if itin_holder else None})
