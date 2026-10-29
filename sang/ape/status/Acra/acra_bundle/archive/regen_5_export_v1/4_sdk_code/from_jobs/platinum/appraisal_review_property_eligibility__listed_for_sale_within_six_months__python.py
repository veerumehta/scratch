# rule: acra-platinum.appraisal_review_property_eligibility.listed_for_sale_within_six_months.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_for_sale_within_six_months
# reads: SubjectProperty.listed_for_sale_last_6_months
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_for_sale_within_six_months

import rules_lib


def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    result = rules_lib.flag(listed)
    if result is None:
        return rules_lib.unknown('SubjectProperty.listed_for_sale_last_6_months')
    return result
