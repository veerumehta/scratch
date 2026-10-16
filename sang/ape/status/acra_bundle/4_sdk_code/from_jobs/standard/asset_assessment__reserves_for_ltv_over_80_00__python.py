# rule: acra-standard.asset_assessment.reserves_for_ltv_over_80_00.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.reserves_for_ltv_over_80_00
# reads: LoanCore.cltv_percent, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment.reserves_for_ltv_over_80_00

import rules_lib

def check(ctx):
    ltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(ltv=ltv)
    if missing:
        return rules_lib.unknown(*missing)

    trigger_applies = rules_lib.band(ltv, [(80.00, False)], above=True)
    if trigger_applies is None:
        return rules_lib.unknown('ltv')
    if not trigger_applies:
        return True

    reserves_months = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves_months >= 6
