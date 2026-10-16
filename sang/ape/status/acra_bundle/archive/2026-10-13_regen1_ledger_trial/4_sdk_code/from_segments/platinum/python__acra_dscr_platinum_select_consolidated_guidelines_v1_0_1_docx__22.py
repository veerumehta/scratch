# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.22
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶8
# reads: property_type, rural_property, occupancy_subtype, cltv_pct

import rules_lib

def check(ctx):
    property_type = ctx['property_type']
    rural_property = ctx['rural_property']
    occupancy_subtype = ctx['occupancy_subtype']

    missing = rules_lib.gaps(
        property_type=property_type,
        rural_property=rural_property,
        occupancy_subtype=occupancy_subtype,
    )
    if missing:
        return rules_lib.unknown(*missing)

    rural = rules_lib.flag(rural_property)
    if rural is None:
        return rules_lib.unknown('rural_property')

    if rural or rules_lib.same(
        property_type, 'Rural', 'Rural Property', 'Condotel', 'Non-Warrantable Condo'
    ) or rules_lib.same(occupancy_subtype, 'Short-Term Rental', 'STR'):
        return False

    if rules_lib.same(property_type, 'Two-Units', 'Warrantable Condo'):
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        within_limit = rules_lib.band(cltv_pct, [(75.00, True)], above=False)
        if within_limit is None:
            return rules_lib.unknown('cltv_pct')
        return within_limit

    if rules_lib.same(property_type, 'SFR', 'Townhome', 'PUD'):
        return True

    return rules_lib.unknown('property_type')
