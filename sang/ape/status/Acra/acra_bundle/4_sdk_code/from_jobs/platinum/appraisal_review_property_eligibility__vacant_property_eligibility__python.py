# rule: acra-platinum.appraisal_review_property_eligibility.vacant_property_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.vacant_property_eligibility
# reads: SubjectProperty.is_vacant
# implements job: acra-platinum.appraisal_review_property_eligibility.vacant_property_eligibility

import rules_lib

def check(ctx):
    is_vacant = rules_lib.flag(ctx['SubjectProperty.is_vacant'])
    missing = rules_lib.gaps(is_vacant=is_vacant)
    if missing:
        return rules_lib.unknown(*missing)
    return not is_vacant
