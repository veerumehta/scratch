# rule: acra-standard.funds_to_close_seasoning_and_reserves.reserve_requirements_by_trigger.python
# origin: written from a job
# description: Python formalization of acra-standard.funds_to_close_seasoning_and_reserves.reserve_requirements_by_trigger
# reads: fico, first_time_homebuyer, listed_for_sale_last_6_months, reserves_months
# implements job: acra-standard.funds_to_close_seasoning_and_reserves.reserve_requirements_by_trigger

import rules_lib

def check(ctx):
    fico = ctx['fico']
    first_time_homebuyer = ctx['first_time_homebuyer']
    listed_for_sale_last_6_months = ctx['listed_for_sale_last_6_months']
    reserves_months = ctx['reserves_months']

    missing = rules_lib.gaps(
        fico=fico,
        first_time_homebuyer=first_time_homebuyer,
        listed_for_sale_last_6_months=listed_for_sale_last_6_months,
        reserves_months=reserves_months,
    )
    if missing:
        return rules_lib.unknown(*missing)

    first_time = rules_lib.flag(first_time_homebuyer)
    listed = rules_lib.flag(listed_for_sale_last_6_months)
    undecided = []
    if first_time is None:
        undecided.append('first_time_homebuyer')
    if listed is None:
        undecided.append('listed_for_sale_last_6_months')
    if undecided:
        return rules_lib.unknown(*undecided)

    return not (
        (fico < 620 and reserves_months < 12)
        or (first_time and reserves_months < 6)
        or (listed and reserves_months < 24)
    )
