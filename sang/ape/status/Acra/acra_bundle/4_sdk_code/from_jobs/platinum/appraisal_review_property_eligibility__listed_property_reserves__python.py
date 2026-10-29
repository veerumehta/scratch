# rule: acra-platinum.appraisal_review_property_eligibility.listed_property_reserves.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_property_reserves
# reads: SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_property_reserves

import rules_lib

def check(ctx):
    listed_raw = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed_raw)
    if missing:
        return rules_lib.unknown(*missing)

    listed = rules_lib.flag(listed_raw)
    if listed is None:
        return rules_lib.unknown('listed')
    if not listed:
        return True

    reserves = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves=reserves)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves >= 24
