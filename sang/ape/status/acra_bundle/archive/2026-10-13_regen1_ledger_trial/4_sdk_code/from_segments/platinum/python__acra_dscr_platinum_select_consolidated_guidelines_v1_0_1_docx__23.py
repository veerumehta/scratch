# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.23
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶9
# reads: property_type, rural_property, property_state, vacant_property, cltv_pct

import rules_lib


def check(ctx):
    property_type = ctx['property_type']
    rural_property = ctx['rural_property']
    property_state = ctx['property_state']
    vacant_property = ctx['vacant_property']

    missing = rules_lib.gaps(
        property_type=property_type,
        rural_property=rural_property,
        property_state=property_state,
        vacant_property=vacant_property,
    )
    if missing:
        return rules_lib.unknown(*missing)

    rural = rules_lib.flag(rural_property)
    vacant = rules_lib.flag(vacant_property)
    if rural is None:
        return rules_lib.unknown('rural_property')
    if vacant is None:
        return rules_lib.unknown('vacant_property')

    if rural or vacant or rules_lib.same(property_state, 'SD', 'U.S. Terrs.'):
        return False

    if rules_lib.same(
        property_type,
        'Rural Properties',
        'Condotels',
        'Non-Warrantable Condos',
        'Short-Term Rentals',
    ):
        return False

    if rules_lib.same(property_type, 'SFR', 'Townhome', 'PUD'):
        return True

    if rules_lib.same(property_type, 'Warrantable Condo', 'Two-Units'):
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        result = rules_lib.band(cltv_pct, [(75.00, True)], above=False)
        if result is None:
            return rules_lib.unknown('cltv_pct')
        return result

    # These property types are not addressed by the stated eligibility table.
    return rules_lib.unknown('property_type')
