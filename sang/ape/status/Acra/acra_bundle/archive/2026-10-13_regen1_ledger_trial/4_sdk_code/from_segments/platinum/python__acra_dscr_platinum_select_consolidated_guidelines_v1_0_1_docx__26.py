# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.26
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶12
# reads: cltv_pct, listed_for_sale_last_6_months, reserves_months

import rules_lib


def check(ctx):
    cltv_pct = ctx['cltv_pct']
    listed_for_sale_last_6_months = ctx['listed_for_sale_last_6_months']
    reserves_months = ctx['reserves_months']

    missing = rules_lib.gaps(
        cltv_pct=cltv_pct,
        listed_for_sale_last_6_months=listed_for_sale_last_6_months,
        reserves_months=reserves_months,
    )
    if missing:
        return rules_lib.unknown(*missing)

    cltv_above_75 = rules_lib.band(cltv_pct, [(75.00, False)], above=True)
    listed = rules_lib.flag(listed_for_sale_last_6_months)
    reserve_value = rules_lib.ratio(reserves_months, 1)

    if cltv_above_75 is None:
        return rules_lib.unknown('cltv_pct')
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')
    if reserve_value is None:
        return rules_lib.unknown('reserves_months')

    if cltv_above_75 and listed:
        return rules_lib.unknown('overlapping_reserve_treatment')
    if cltv_above_75:
        return reserve_value >= 6
    if listed:
        return reserve_value >= 24

    return rules_lib.unknown('base_reserve_requirement')
