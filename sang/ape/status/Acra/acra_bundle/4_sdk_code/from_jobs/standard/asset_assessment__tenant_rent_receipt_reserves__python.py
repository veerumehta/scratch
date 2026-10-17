# rule: acra-standard.asset_assessment.tenant_rent_receipt_reserves.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.tenant_rent_receipt_reserves
# reads: RatioSet.reserves_months
# implements job: acra-standard.asset_assessment.tenant_rent_receipt_reserves

import rules_lib

def check(ctx):
    reserves_months = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves_months >= 12
