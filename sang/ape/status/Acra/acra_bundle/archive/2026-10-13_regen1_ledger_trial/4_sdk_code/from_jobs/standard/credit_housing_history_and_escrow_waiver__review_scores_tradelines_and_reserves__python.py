# rule: acra-standard.credit_housing_history_and_escrow_waiver.review_scores_tradelines_and_reserves.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_housing_history_and_escrow_waiver.review_scores_tradelines_and_reserves
# reads: fico, reserves_months
# implements job: acra-standard.credit_housing_history_and_escrow_waiver.review_scores_tradelines_and_reserves

import rules_lib

def check(ctx):
    fico = ctx['fico']
    reserves_months = ctx['reserves_months']
    missing = rules_lib.gaps(fico=fico, reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves_months >= 12 if fico < 620 else True
