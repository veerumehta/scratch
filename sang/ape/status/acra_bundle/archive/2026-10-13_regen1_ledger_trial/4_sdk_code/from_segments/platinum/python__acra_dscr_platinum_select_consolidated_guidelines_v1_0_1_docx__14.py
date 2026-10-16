# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.14
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶15
# reads: first_time_homebuyer

import rules_lib

def check(ctx):
    first_time_homebuyer = ctx['first_time_homebuyer']
    missing = rules_lib.gaps(first_time_homebuyer=first_time_homebuyer)
    if missing:
        return rules_lib.unknown(*missing)
    first_time_homebuyer = rules_lib.flag(first_time_homebuyer)
    if first_time_homebuyer is None:
        return rules_lib.unknown('first_time_homebuyer')
    return not first_time_homebuyer
