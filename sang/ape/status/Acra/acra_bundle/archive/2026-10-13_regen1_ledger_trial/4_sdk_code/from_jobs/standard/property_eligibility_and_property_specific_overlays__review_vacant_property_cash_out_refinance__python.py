# rule: acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_cash_out_refinance.python
# origin: written from a job
# description: Python formalization of acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_cash_out_refinance
# reads: fico, product_is_interest_only, reserves_months, loan_amount, ownership_months, cltv_pct
# implements job: acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_cash_out_refinance

import rules_lib


def check(ctx):
    fico = ctx['fico']
    interest_only = ctx['product_is_interest_only']
    reserves_months = ctx['reserves_months']
    loan_amount = ctx['loan_amount']
    ownership_months = ctx['ownership_months']

    missing = rules_lib.gaps(
        fico=fico,
        product_is_interest_only=interest_only,
        reserves_months=reserves_months,
        loan_amount=loan_amount,
        ownership_months=ownership_months,
    )
    if missing:
        return rules_lib.unknown(*missing)

    interest_only_flag = rules_lib.flag(interest_only)
    if interest_only_flag is None:
        return rules_lib.unknown('product_is_interest_only')

    if loan_amount < 1500000:
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        if cltv_pct > 60:
            return False

    return (
        fico >= 700
        and not interest_only_flag
        and reserves_months >= 6
        and ownership_months >= 15
    )
