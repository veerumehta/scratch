# rule: acra-standard.asset_assessment.vacant_rate_and_term_refinance_reserves.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.vacant_rate_and_term_refinance_reserves
# reads: SubjectProperty.is_vacant, LoanCore.loan_purpose, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment.vacant_rate_and_term_refinance_reserves

import rules_lib

def check(ctx):
    vacant = ctx['SubjectProperty.is_vacant']
    missing = rules_lib.gaps(vacant=vacant)
    if missing:
        return rules_lib.unknown(*missing)
    vacant_flag = rules_lib.flag(vacant)
    if vacant_flag is None:
        return rules_lib.unknown('vacant')
    if not vacant_flag:
        return True

    purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(purpose, 'rate & term refinance', 'rate and term refinance'):
        return True

    reserves = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves=reserves)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves >= 6
