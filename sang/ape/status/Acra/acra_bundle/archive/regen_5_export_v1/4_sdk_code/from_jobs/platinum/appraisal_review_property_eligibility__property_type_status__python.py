# rule: acra-platinum.appraisal_review_property_eligibility.property_type_status.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.property_type_status
# reads: SubjectProperty.property_type
# implements job: acra-platinum.appraisal_review_property_eligibility.property_type_status

import rules_lib


def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    missing = rules_lib.gaps(property_type=property_type)
    if missing:
        return rules_lib.unknown(*missing)

    if any(rules_lib.same(property_type, value) for value in (
        'SFR', 'Townhome', 'PUD', 'Warrantable Condo', 'Two-Units'
    )):
        status = 'expressly eligible'
    elif any(rules_lib.same(property_type, value) for value in (
        'Rural Properties', 'Condotels', 'Non-Warrantable Condos',
        'Short-Term Rentals'
    )):
        status = 'expressly ineligible'
    else:
        status = 'not addressed'

    return True, {'property_type_status': status}
