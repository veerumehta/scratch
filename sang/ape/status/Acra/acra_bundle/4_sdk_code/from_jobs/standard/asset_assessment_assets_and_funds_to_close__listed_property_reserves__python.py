# rule: acra-standard.asset_assessment_assets_and_funds_to_close.listed_property_reserves.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment_assets_and_funds_to_close.listed_property_reserves
# reads: SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment_assets_and_funds_to_close.listed_property_reserves

import decimal
import rules_lib


def check(ctx):
    listed = rules_lib.flag(ctx['SubjectProperty.listed_for_sale_last_6_months'])
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)

    if not listed:
        return True

    reserves = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves=reserves)
    if missing:
        return rules_lib.unknown(*missing)

    try:
        reserves = decimal.Decimal(str(reserves))
    except (decimal.InvalidOperation, TypeError, ValueError):
        return rules_lib.unknown('reserves')

    return reserves >= 24
