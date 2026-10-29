# rule: acra-platinum.compliance_and_closing.vacant_property_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.compliance_and_closing.vacant_property_eligibility
# reads: SubjectProperty.is_vacant
# implements job: acra-platinum.compliance_and_closing.vacant_property_eligibility

import rules_lib

def check(ctx):
    vacant = ctx['SubjectProperty.is_vacant']
    missing = rules_lib.gaps(vacant=vacant)
    if missing:
        return rules_lib.unknown(*missing)
    vacant = rules_lib.flag(vacant)
    if vacant is None:
        return rules_lib.unknown('SubjectProperty.is_vacant')
    return not vacant
