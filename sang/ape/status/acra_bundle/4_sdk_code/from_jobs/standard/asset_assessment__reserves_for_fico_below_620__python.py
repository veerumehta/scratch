# rule: acra-standard.asset_assessment.reserves_for_fico_below_620.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.reserves_for_fico_below_620
# reads: CreditReport.representative_score, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment.reserves_for_fico_below_620

import rules_lib

def check(ctx):
    score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(score=score)
    if missing:
        return rules_lib.unknown(*missing)

    if score >= 620:
        return True

    reserves = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves=reserves)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves >= 12
