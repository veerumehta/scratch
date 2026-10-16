# rule: acra-platinum.liabilities_assessment.listed_property_reserves.python
# origin: written from a job
# description: Python formalization of acra-platinum.liabilities_assessment.listed_property_reserves
# reads: SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
# implements job: acra-platinum.liabilities_assessment.listed_property_reserves

import rules_lib

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    listed = rules_lib.flag(listed)
    if listed is None:
        return rules_lib.unknown('listed')
    if not listed:
        return True

    reserves = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves=reserves)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves >= 24
