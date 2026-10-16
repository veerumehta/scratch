# rule: acra-platinum.loan_program_eligibility.vacant_property_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.vacant_property_eligibility
# reads: SubjectProperty.is_vacant
# implements job: acra-platinum.loan_program_eligibility.vacant_property_eligibility

import rules_lib


def check(ctx):
    is_vacant = ctx['SubjectProperty.is_vacant']
    missing = rules_lib.gaps(is_vacant=is_vacant)
    if missing:
        return rules_lib.unknown(*missing)

    vacant = rules_lib.flag(is_vacant)
    if vacant is None:
        return rules_lib.unknown('is_vacant')
    return not vacant
