# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.31
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶17
# reads: property_state

import rules_lib

def check(ctx):
    property_state = ctx['property_state']
    missing = rules_lib.gaps(property_state=property_state)
    if missing:
        return rules_lib.unknown(*missing)
    return not rules_lib.same(property_state, 'SD')
