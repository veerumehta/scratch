# rule: acra-standard.property_eligibility_and_property_specific_overlays.apply_state_and_declining_market_overlays.python
# origin: written from a job
# description: Python formalization of acra-standard.property_eligibility_and_property_specific_overlays.apply_state_and_declining_market_overlays
# reads: property_state
# implements job: acra-standard.property_eligibility_and_property_specific_overlays.apply_state_and_declining_market_overlays

import rules_lib

def check(ctx):
    property_state = ctx['property_state']
    missing = rules_lib.gaps(property_state=property_state)
    if missing:
        return rules_lib.unknown(*missing)
    return not rules_lib.same(property_state, 'SD')
