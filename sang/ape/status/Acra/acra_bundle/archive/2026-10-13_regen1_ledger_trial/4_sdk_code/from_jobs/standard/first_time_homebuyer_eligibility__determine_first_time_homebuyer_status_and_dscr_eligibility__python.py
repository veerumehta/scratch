# rule: acra-standard.first_time_homebuyer_eligibility.determine_first_time_homebuyer_status_and_dscr_eligibility.python
# origin: written from a job
# description: Python formalization of acra-standard.first_time_homebuyer_eligibility.determine_first_time_homebuyer_status_and_dscr_eligibility
# reads: first_time_homebuyer, fico, cltv_pct, loan_amount, product_is_interest_only, reserves_months
# implements job: acra-standard.first_time_homebuyer_eligibility.determine_first_time_homebuyer_status_and_dscr_eligibility

import rules_lib


def check(ctx):
    first_time_homebuyer = ctx['first_time_homebuyer']
    fico = ctx['fico']
    cltv_pct = ctx['cltv_pct']
    loan_amount = ctx['loan_amount']
    product_is_interest_only = ctx['product_is_interest_only']
    reserves_months = ctx['reserves_months']

    missing = rules_lib.gaps(
        first_time_homebuyer=first_time_homebuyer,
        fico=fico,
        cltv_pct=cltv_pct,
        loan_amount=loan_amount,
        product_is_interest_only=product_is_interest_only,
        reserves_months=reserves_months,
    )
    if missing:
        return rules_lib.unknown(*missing)

    fthb_flag = rules_lib.flag(first_time_homebuyer)
    io_flag = rules_lib.flag(product_is_interest_only)
    if fthb_flag is None:
        return rules_lib.unknown('first_time_homebuyer')
    if io_flag is None:
        return rules_lib.unknown('product_is_interest_only')

    return (
        fthb_flag
        and fico >= 700
        and cltv_pct <= 70
        and loan_amount <= 1000000
        and not io_flag
        and reserves_months >= 6
    )
