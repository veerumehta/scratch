# rule: acra-platinum.asset_assessment.listed_property_reserves.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.listed_property_reserves
# reads: SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
# implements job: acra-platinum.asset_assessment.listed_property_reserves

import rules_lib

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)

    listed_flag = rules_lib.flag(listed)
    if listed_flag is None:
        return rules_lib.unknown('SubjectProperty.listed_for_sale_last_6_months')
    if not listed_flag:
        return True

    reserves_months = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves_months >= 24
