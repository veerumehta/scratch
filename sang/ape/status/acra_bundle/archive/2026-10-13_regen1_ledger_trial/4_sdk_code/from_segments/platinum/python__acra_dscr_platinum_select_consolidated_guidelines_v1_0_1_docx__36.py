# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.36
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶22
# reads: cltv_pct, reserves_months

import rules_lib

def check(ctx):
    cltv_pct = ctx['cltv_pct']
    reserves_months = ctx['reserves_months']
    missing = rules_lib.gaps(cltv_pct=cltv_pct, reserves_months=reserves_months)
    if missing:
        return rules_lib.unknown(*missing)
    return cltv_pct <= 75.00 or reserves_months >= 6
