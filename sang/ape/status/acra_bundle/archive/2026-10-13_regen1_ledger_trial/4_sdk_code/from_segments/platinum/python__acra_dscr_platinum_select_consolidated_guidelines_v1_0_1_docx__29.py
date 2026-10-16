# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.29
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶15
# reads: listed_for_sale_last_6_months, cltv_pct

import rules_lib

def check(ctx):
    listed_raw = ctx['listed_for_sale_last_6_months']
    cltv_pct = ctx['cltv_pct']
    missing = rules_lib.gaps(listed_for_sale_last_6_months=listed_raw, cltv_pct=cltv_pct)
    if missing:
        return rules_lib.unknown(*missing)

    listed = rules_lib.flag(listed_raw)
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')
    if not listed:
        return True
    return cltv_pct <= 65
