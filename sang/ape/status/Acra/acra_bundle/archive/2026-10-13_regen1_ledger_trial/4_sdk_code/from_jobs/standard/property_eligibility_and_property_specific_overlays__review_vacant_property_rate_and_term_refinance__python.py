# rule: acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_rate_and_term_refinance.python
# origin: written from a job
# description: Python formalization of acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_rate_and_term_refinance
# reads: fico, product_is_interest_only, reserves_months
# implements job: acra-standard.property_eligibility_and_property_specific_overlays.review_vacant_property_rate_and_term_refinance

import rules_lib

def check(ctx):
    fico = ctx['fico']
    product_is_interest_only = ctx['product_is_interest_only']
    reserves_months = ctx['reserves_months']

    missing = rules_lib.gaps(
        fico=fico,
        product_is_interest_only=product_is_interest_only,
        reserves_months=reserves_months,
    )
    if missing:
        return rules_lib.unknown(*missing)

    interest_only = rules_lib.flag(product_is_interest_only)
    if interest_only is None:
        return rules_lib.unknown('product_is_interest_only')

    return fico >= 700 and not interest_only and reserves_months >= 6
