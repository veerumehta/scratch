# rule: acra-standard.appraisal_review_property_eligibility.eligible_property_type.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.eligible_property_type
# reads: SubjectProperty.property_type
# implements job: acra-standard.appraisal_review_property_eligibility.eligible_property_type

import rules_lib

def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    missing = rules_lib.gaps(property_type=property_type)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.match(property_type, (
        'SFR',
        'Townhome',
        'PUD',
        'Warrantable Condo',
        'Non-Warrantable Condo',
        'Condotel / PUDtel',
        '2-4 Units',
        'Manufactured',
    )) is not None
