# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.38
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶17
# reads: escrow_waiver_requested, fico

import rules_lib

def check(ctx):
    escrow_waiver_requested = ctx['escrow_waiver_requested']
    fico = ctx['fico']
    missing = rules_lib.gaps(escrow_waiver_requested=escrow_waiver_requested, fico=fico)
    if missing:
        return rules_lib.unknown(*missing)

    requested = rules_lib.flag(escrow_waiver_requested)
    if requested is None:
        return rules_lib.unknown('escrow_waiver_requested')
    if not requested:
        return True
    return fico >= 700
