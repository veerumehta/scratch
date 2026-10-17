# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.28
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶14
# reads: listed_for_sale_last_6_months

import rules_lib

def check(ctx):
    listed = ctx['listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)

    listed = rules_lib.flag(listed)
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')
    if not listed:
        return True

    # The available fields do not state the penalty term, and the state
    # restriction interaction is flagged for Acra confirmation (Q-19).
    return rules_lib.unknown('prepayment_penalty_term_years', 'state restriction interaction')
