# rule: acra-platinum.unassigned_provisions.escrow_waiver_cltv_and_fico_limits.python
# origin: written from a job
# description: Python formalization of acra-platinum.unassigned_provisions.escrow_waiver_cltv_and_fico_limits
# reads: LoanCore.is_escrow_waived
# implements job: acra-platinum.unassigned_provisions.escrow_waiver_cltv_and_fico_limits

import rules_lib

def check(ctx):
    is_escrow_waived = ctx['LoanCore.is_escrow_waived']
    missing = rules_lib.gaps(is_escrow_waived=is_escrow_waived)
    if missing:
        return rules_lib.unknown(*missing)
    waived = rules_lib.flag(is_escrow_waived)
    if waived is None:
        return rules_lib.unknown('is_escrow_waived')
    return waived is True
