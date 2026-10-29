# rule: acra-standard.asset_assessment_assets_and_funds_to_close.fico_reserve_trigger.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment_assets_and_funds_to_close.fico_reserve_trigger
# reads: CreditReport.representative_score, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment_assets_and_funds_to_close.fico_reserve_trigger

import rules_lib


def check(ctx):
    score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(score=score)
    if missing:
        return rules_lib.unknown(*missing)

    if score >= 620:
        return True

    reserves_months = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)

    return reserves_months >= 12
