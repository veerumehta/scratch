# rule: acra-standard.asset_assessment_assets_and_funds_to_close.vacant_property_refinance_reserves.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment_assets_and_funds_to_close.vacant_property_refinance_reserves
# reads: SubjectProperty.is_vacant, LoanCore.loan_purpose, RatioSet.reserves_months
# implements job: acra-standard.asset_assessment_assets_and_funds_to_close.vacant_property_refinance_reserves

import rules_lib

def check(ctx):
    is_vacant = ctx['SubjectProperty.is_vacant']
    missing = rules_lib.gaps(is_vacant=is_vacant)
    if missing:
        return rules_lib.unknown(*missing)
    vacant = rules_lib.flag(is_vacant)
    if vacant is None:
        return rules_lib.unknown('is_vacant')
    if not vacant:
        return True

    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    rate_term = rules_lib.same(
        loan_purpose,
        'rate & term refinance',
        'rate and term refinance',
        'rate term refinance',
    )
    cash_out = rules_lib.same(
        loan_purpose,
        'cash-out refinance',
        'cash out refinance',
    )
    if not rate_term and not cash_out:
        return True

    reserves_months = ctx['RatioSet.reserves_months']
    missing = rules_lib.gaps(reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)
    return reserves_months >= 6
