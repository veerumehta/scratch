# rule: acra-platinum.funds_to_close_seasoning_and_reserves.reserve_requirements_by_trigger.python
# origin: written from a job
# description: Python formalization of acra-platinum.funds_to_close_seasoning_and_reserves.reserve_requirements_by_trigger
# reads: cltv_pct, listed_for_sale_last_6_months, reserves_months
# implements job: acra-platinum.funds_to_close_seasoning_and_reserves.reserve_requirements_by_trigger

import rules_lib

def check(ctx):
    cltv_pct = ctx['cltv_pct']
    listed_for_sale_last_6_months = ctx['listed_for_sale_last_6_months']
    reserves_months = ctx['reserves_months']

    missing = rules_lib.gaps(
        cltv_pct=cltv_pct,
        listed_for_sale_last_6_months=listed_for_sale_last_6_months,
        reserves_months=reserves_months,
    )
    if missing:
        return rules_lib.unknown(*missing)

    listed = rules_lib.flag(listed_for_sale_last_6_months)
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')

    if cltv_pct > 75.00 and reserves_months < 6:
        return False
    if listed and reserves_months < 24:
        return False
    return True
