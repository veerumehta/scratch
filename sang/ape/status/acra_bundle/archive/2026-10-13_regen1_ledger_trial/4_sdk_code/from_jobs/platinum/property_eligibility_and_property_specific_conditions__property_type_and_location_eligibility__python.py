# rule: acra-platinum.property_eligibility_and_property_specific_conditions.property_type_and_location_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.property_eligibility_and_property_specific_conditions.property_type_and_location_eligibility
# reads: property_type, property_state, cltv_pct
# implements job: acra-platinum.property_eligibility_and_property_specific_conditions.property_type_and_location_eligibility

import rules_lib


def check(ctx):
    property_type = ctx['property_type']
    property_state = ctx['property_state']
    missing = rules_lib.gaps(property_type=property_type, property_state=property_state)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(property_state, 'SD', 'U.S. Terrs'):
        return (False, {'property_type_status': 'not evaluated', 'property_state': property_state})

    eligible_types = ('SFR', 'Townhome', 'PUD', 'Warrantable Condo', 'Two-Units')
    ineligible_types = ('Rural Properties', 'Condotels', 'Non-Warrantable Condos', 'Short-Term Rentals')
    if rules_lib.same(property_type, *ineligible_types):
        return (False, {'property_type_status': 'ineligible', 'property_state': property_state})

    if rules_lib.same(property_type, 'Warrantable Condo', 'Two-Units'):
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        return (cltv_pct <= 75.00, {
            'property_type_status': 'eligible',
            'property_state': property_state,
            'cltv_pct': cltv_pct,
            'max_cltv_pct': 75.00,
        })

    if rules_lib.same(property_type, *eligible_types):
        return (True, {'property_type_status': 'eligible', 'property_state': property_state})

    # Unlisted property types are not treated as ineligible; their status needs review.
    return (True, {'property_type_status': 'not addressed; review required', 'property_state': property_state})
