# rule: acra-platinum.loan_program_eligibility.property_eligibility_and_location.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.property_eligibility_and_location
# reads: SubjectProperty.state
# implements job: acra-platinum.loan_program_eligibility.property_eligibility_and_location

import rules_lib

def check(ctx):
    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(state=state)
    if missing:
        return rules_lib.unknown(*missing)
    return not rules_lib.same(state, 'SD', 'U.S. Terrs.')
