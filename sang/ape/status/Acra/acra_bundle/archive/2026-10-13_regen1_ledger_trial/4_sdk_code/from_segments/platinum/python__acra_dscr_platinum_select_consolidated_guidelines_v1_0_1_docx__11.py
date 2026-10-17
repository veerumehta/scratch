# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.11
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶12
# reads: occupancy_subtype

import rules_lib

def check(ctx):
    occupancy_subtype = ctx['occupancy_subtype']
    missing = rules_lib.gaps(occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    if rules_lib.same(occupancy_subtype, 'short-term rental', 'short-term rentals'):
        return False
    return rules_lib.unknown(
        'market rent',
        'actual-rent receipt evidence',
        'lease duration after closing',
        'rent term',
    )
