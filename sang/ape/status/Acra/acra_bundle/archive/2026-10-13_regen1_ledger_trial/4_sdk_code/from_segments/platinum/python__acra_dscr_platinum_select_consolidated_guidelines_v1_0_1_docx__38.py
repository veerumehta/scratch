# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.38
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶24
# reads: escrow_waiver_requested

import rules_lib

def check(ctx):
    escrow_waiver_requested = ctx['escrow_waiver_requested']
    missing = rules_lib.gaps(escrow_waiver_requested=escrow_waiver_requested)
    if missing:
        return rules_lib.unknown(*missing)
    requested = rules_lib.flag(escrow_waiver_requested)
    if requested is None:
        return rules_lib.unknown('escrow_waiver_requested')
    if not requested:
        return True
    return rules_lib.unknown('Section 35 status')
