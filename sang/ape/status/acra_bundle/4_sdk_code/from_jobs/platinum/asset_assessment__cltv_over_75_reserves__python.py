# rule: acra-platinum.asset_assessment.cltv_over_75_reserves.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.cltv_over_75_reserves
# reads: LoanCore.cltv_percent, RatioSet.reserves_months
# implements job: acra-platinum.asset_assessment.cltv_over_75_reserves

import rules_lib

def check(ctx):
    cltv = ctx['LoanCore.cltv_percent']
    reserves = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(cltv=cltv, reserves=reserves)
    if missing:
        return rules_lib.unknown(*missing)
    return cltv <= 75.00 or reserves >= 6
