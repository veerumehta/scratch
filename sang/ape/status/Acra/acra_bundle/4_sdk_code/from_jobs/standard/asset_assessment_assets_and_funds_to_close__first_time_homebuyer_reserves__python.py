# rule: acra-standard.asset_assessment_assets_and_funds_to_close.first_time_homebuyer_reserves.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment_assets_and_funds_to_close.first_time_homebuyer_reserves
# reads: Borrower.is_first_time_homebuyer, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment_assets_and_funds_to_close.first_time_homebuyer_reserves

import rules_lib

def check(ctx):
    is_first_time_homebuyer = ctx['Borrower.is_first_time_homebuyer']
    missing = rules_lib.gaps(is_first_time_homebuyer=is_first_time_homebuyer)
    if missing:
        return rules_lib.unknown(*missing)

    first_time = rules_lib.flag(is_first_time_homebuyer)
    if first_time is None:
        return rules_lib.unknown('Borrower.is_first_time_homebuyer')
    if not first_time:
        return True

    reserves_months = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)

    reserves = rules_lib.ratio(reserves_months, 1)
    if reserves is None:
        return rules_lib.unknown('RatioSet.reserves_months')
    return reserves >= 6
