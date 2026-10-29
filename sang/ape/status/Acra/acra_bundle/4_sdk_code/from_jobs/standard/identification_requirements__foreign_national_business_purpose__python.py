# rule: acra-standard.identification_requirements.foreign_national_business_purpose.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.foreign_national_business_purpose
# reads: SubjectProperty.occupancy_subtype
# implements job: acra-standard.identification_requirements.foreign_national_business_purpose

import rules_lib

def check(ctx):
    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(occupancy_subtype, 'investment')
