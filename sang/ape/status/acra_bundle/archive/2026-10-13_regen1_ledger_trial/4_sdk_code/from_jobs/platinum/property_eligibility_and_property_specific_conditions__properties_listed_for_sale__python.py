# rule: acra-platinum.property_eligibility_and_property_specific_conditions.properties_listed_for_sale.python
# origin: written from a job
# description: Python formalization of acra-platinum.property_eligibility_and_property_specific_conditions.properties_listed_for_sale
# reads: listed_for_sale_last_6_months
# implements job: acra-platinum.property_eligibility_and_property_specific_conditions.properties_listed_for_sale

import rules_lib

def check(ctx):
    listed_for_sale_last_6_months = ctx['listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed_for_sale_last_6_months=listed_for_sale_last_6_months)
    if missing:
        return rules_lib.unknown(*missing)
    listed = rules_lib.flag(listed_for_sale_last_6_months)
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')
    return True, {
        'listed_for_sale_last_6_months': listed,
        'treated_as_listed_property_for_following_checks': listed,
    }
