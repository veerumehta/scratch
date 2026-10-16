# rule: acra-standard.loan_program_eligibility.eligible_state.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.eligible_state
# reads: SubjectProperty.state
# implements job: acra-standard.loan_program_eligibility.eligible_state

import rules_lib

def check(ctx):
    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(state=state)
    if missing:
        return rules_lib.unknown(*missing)
    return not rules_lib.same(state, 'SD')
