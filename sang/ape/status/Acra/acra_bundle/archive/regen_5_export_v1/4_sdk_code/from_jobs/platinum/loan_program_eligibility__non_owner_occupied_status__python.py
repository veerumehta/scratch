# rule: acra-platinum.loan_program_eligibility.non_owner_occupied_status.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.non_owner_occupied_status
# reads: SubjectProperty.occupancy_subtype
# implements job: acra-platinum.loan_program_eligibility.non_owner_occupied_status

import rules_lib

def check(ctx):
    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(occupancy_subtype, 'non-owner occupied')
