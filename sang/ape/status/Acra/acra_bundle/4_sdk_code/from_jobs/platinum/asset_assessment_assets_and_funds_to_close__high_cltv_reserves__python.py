# rule: acra-platinum.asset_assessment_assets_and_funds_to_close.high_cltv_reserves.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment_assets_and_funds_to_close.high_cltv_reserves
# reads: LoanCore.cltv_percent
# implements job: acra-platinum.asset_assessment_assets_and_funds_to_close.high_cltv_reserves

import rules_lib

def check(ctx):
    cltv_raw = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv_raw)
    if missing:
        return rules_lib.unknown(*missing)
    cltv = rules_lib.percent(cltv_raw, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv')
    return cltv > 75.00
