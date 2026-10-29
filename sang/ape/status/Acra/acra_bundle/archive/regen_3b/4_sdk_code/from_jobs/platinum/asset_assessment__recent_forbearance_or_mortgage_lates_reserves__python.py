# rule: acra-platinum.asset_assessment.recent_forbearance_or_mortgage_lates_reserves.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.recent_forbearance_or_mortgage_lates_reserves
# reads: SubjectProperty.occupancy_subtype, RatioSet.reserves_months
# implements job: acra-platinum.asset_assessment.recent_forbearance_or_mortgage_lates_reserves

import rules_lib

def check(ctx):
    occupancy = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(occupancy=occupancy)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(occupancy, 'tenant occupied'):
        return True

    reserves = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves=reserves)
    if missing:
        return rules_lib.unknown(*missing)

    return reserves >= 12
