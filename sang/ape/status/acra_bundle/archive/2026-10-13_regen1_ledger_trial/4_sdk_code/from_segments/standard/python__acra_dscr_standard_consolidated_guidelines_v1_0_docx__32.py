# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.32
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶11
# reads: cltv_pct

import rules_lib

def check(ctx):
    cltv_pct = ctx['cltv_pct']
    missing = rules_lib.gaps(cltv_pct=cltv_pct)
    if missing:
        return rules_lib.unknown(*missing)
    return (cltv_pct <= 70, {'cltv_pct': cltv_pct})
