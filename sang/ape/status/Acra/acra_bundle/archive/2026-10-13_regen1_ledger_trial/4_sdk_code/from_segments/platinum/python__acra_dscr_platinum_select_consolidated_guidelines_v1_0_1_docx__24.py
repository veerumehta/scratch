# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.24
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶10
# reads: cltv_pct

import rules_lib

def check(ctx):
    cltv_pct = ctx['cltv_pct']
    missing = rules_lib.gaps(cltv_pct=cltv_pct)
    if missing:
        return rules_lib.unknown(*missing)
    return cltv_pct <= 70
