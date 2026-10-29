# rule: acra-platinum.loan_program_eligibility.eligible_location.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.eligible_location
# reads: SubjectProperty.state
# implements job: acra-platinum.loan_program_eligibility.eligible_location

import rules_lib

def check(ctx):
    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(state=state)
    if missing:
        return rules_lib.unknown(*missing)
    return not rules_lib.same(
        state,
        'SD', 'South Dakota',
        'U.S. Terrs.', 'U.S. Territories',
        'PR', 'Puerto Rico',
        'GU', 'Guam',
        'VI', 'U.S. Virgin Islands', 'USVI',
        'AS', 'American Samoa',
        'MP', 'Northern Mariana Islands', 'CNMI',
    )
