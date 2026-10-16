# rule: acra-standard.asset_assessment.first_time_homebuyer_reserves.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.first_time_homebuyer_reserves
# reads: Borrower.is_first_time_homebuyer, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment.first_time_homebuyer_reserves

import decimal
import rules_lib


def check(ctx):
    first_time = ctx['Borrower.is_first_time_homebuyer']
    missing = rules_lib.gaps(first_time=first_time)
    if missing:
        return rules_lib.unknown(*missing)

    first_time = rules_lib.flag(first_time)
    if first_time is None:
        return rules_lib.unknown('first_time')
    if not first_time:
        return True

    reserves = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves_months=reserves)
    if missing:
        return rules_lib.unknown(*missing)

    try:
        reserves = decimal.Decimal(str(reserves))
        if not reserves.is_finite():
            return rules_lib.unknown('reserves_months')
        return reserves >= decimal.Decimal('6')
    except (decimal.InvalidOperation, TypeError, ValueError):
        return rules_lib.unknown('reserves_months')
