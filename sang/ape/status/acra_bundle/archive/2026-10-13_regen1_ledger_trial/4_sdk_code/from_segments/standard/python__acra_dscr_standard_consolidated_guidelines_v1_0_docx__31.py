# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.31
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶10
# reads: listed_for_sale_last_6_months

import rules_lib

def check(ctx):
    listed = ctx['listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.flag(listed)
