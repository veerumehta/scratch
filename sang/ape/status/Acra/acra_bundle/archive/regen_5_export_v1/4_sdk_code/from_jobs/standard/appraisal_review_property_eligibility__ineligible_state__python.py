# rule: acra-standard.appraisal_review_property_eligibility.ineligible_state.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.ineligible_state
# reads: SubjectProperty.state
# implements job: acra-standard.appraisal_review_property_eligibility.ineligible_state

import rules_lib

def check(ctx):
    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(state=state)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(state, 'SD')
