# rule: acra-platinum.prepayment_penalties_and_state_restrictions.review_listed_for_sale_prepayment_minimum.python
# origin: written from a job
# description: Python formalization of acra-platinum.prepayment_penalties_and_state_restrictions.review_listed_for_sale_prepayment_minimum
# reads: listed_for_sale_last_6_months
# implements job: acra-platinum.prepayment_penalties_and_state_restrictions.review_listed_for_sale_prepayment_minimum

import rules_lib

def check(ctx):
    listed_for_sale_last_6_months = ctx['listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed_for_sale_last_6_months=listed_for_sale_last_6_months)
    if missing:
        return rules_lib.unknown(*missing)
    listed = rules_lib.flag(listed_for_sale_last_6_months)
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')
    return listed
