# rule: acra-platinum.title_review.listed_property_reserves.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.listed_property_reserves
# reads: SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
# implements job: acra-platinum.title_review.listed_property_reserves

import rules_lib

def check(ctx):
    listed_for_sale_last_6_months = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed_for_sale_last_6_months=listed_for_sale_last_6_months)
    if missing:
        return rules_lib.unknown(*missing)

    listed_for_sale_last_6_months = rules_lib.flag(listed_for_sale_last_6_months)
    if listed_for_sale_last_6_months is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')
    if not listed_for_sale_last_6_months:
        return True

    reserves_months = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)

    return reserves_months >= 24
