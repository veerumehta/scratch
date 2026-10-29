# rule: acra-platinum.appraisal_review_property_eligibility.ineligible_state.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.ineligible_state
# reads: SubjectProperty.state
# implements job: acra-platinum.appraisal_review_property_eligibility.ineligible_state

import rules_lib

def check(ctx):
    state = ctx['SubjectProperty.state']
    if not rules_lib.known(state):
        return False
    ineligible = rules_lib.same(
        state,
        'SD',
        'AS', 'GU', 'MP', 'PR', 'VI',
        'American Samoa', 'Guam', 'Northern Mariana Islands',
        'Puerto Rico', 'U.S. Virgin Islands', 'US Virgin Islands',
        'U.S. Terrs.', 'U.S. Territories', 'US Territories',
    )
    return not ineligible
