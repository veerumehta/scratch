# rule: acra-standard.asset_assessment.vacant_cash_out_refinance_reserves.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.vacant_cash_out_refinance_reserves
# reads: SubjectProperty.is_vacant, LoanCore.loan_purpose, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment.vacant_cash_out_refinance_reserves

import rules_lib

def check(ctx):
    vacant_raw = ctx['SubjectProperty.is_vacant']
    purpose = ctx['LoanCore.loan_purpose']
    reserves = ctx['RatioSet.reserves_months']

    missing = rules_lib.gaps(vacant_raw=vacant_raw, purpose=purpose, reserves=reserves)
    if missing:
        return rules_lib.unknown(*missing)

    vacant = rules_lib.flag(vacant_raw)
    if vacant is None:
        return rules_lib.unknown('SubjectProperty.is_vacant')

    if not vacant or not rules_lib.same(purpose, 'cash-out refinance'):
        return True

    return reserves >= 6
