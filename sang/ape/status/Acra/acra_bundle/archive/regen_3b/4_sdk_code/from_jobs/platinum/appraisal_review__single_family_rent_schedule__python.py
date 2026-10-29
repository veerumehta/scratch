# rule: acra-platinum.appraisal_review.single_family_rent_schedule.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review.single_family_rent_schedule
# reads: SubjectProperty.property_type
# implements job: acra-platinum.appraisal_review.single_family_rent_schedule

import rules_lib

def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    missing = rules_lib.gaps(property_type=property_type)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(property_type, 'single family')
