# rule: acra-platinum.appraisal_review_property_eligibility.listed_property_subordinate_financing.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_property_subordinate_financing
# reads: SubjectProperty.listed_for_sale_last_6_months
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_property_subordinate_financing

import rules_lib

def check(ctx):
    listed = rules_lib.flag(ctx['SubjectProperty.listed_for_sale_last_6_months'])
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    if listed:
        return rules_lib.unknown('subordinate financing')
    return True
