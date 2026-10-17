# rule: acra-platinum.products_arm_terms_and_interest_only_terms.verify_interest_only_term_and_restrictions.python
# origin: written from a job
# description: Python formalization of acra-platinum.products_arm_terms_and_interest_only_terms.verify_interest_only_term_and_restrictions
# reads: cltv_pct, property_currently_listed_for_sale
# implements job: acra-platinum.products_arm_terms_and_interest_only_terms.verify_interest_only_term_and_restrictions

import rules_lib

def check(ctx):
    cltv_pct = ctx['cltv_pct']
    property_currently_listed_for_sale = ctx['property_currently_listed_for_sale']

    missing = rules_lib.gaps(
        cltv_pct=cltv_pct,
        property_currently_listed_for_sale=property_currently_listed_for_sale,
    )
    if missing:
        return rules_lib.unknown(*missing)

    listed = rules_lib.flag(property_currently_listed_for_sale)
    if listed is None:
        return rules_lib.unknown('property_currently_listed_for_sale')

    return cltv_pct <= 75.00 and not listed
