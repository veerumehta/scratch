# rule: acra-platinum.asset_assessment.listed_property_financing_and_impounds.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.listed_property_financing_and_impounds
# reads: LoanCore.is_escrow_waived
# implements job: acra-platinum.asset_assessment.listed_property_financing_and_impounds

import rules_lib

def check(ctx):
    escrow_waived = ctx['LoanCore.is_escrow_waived']
    missing = rules_lib.gaps(escrow_waived=escrow_waived)
    if missing:
        return rules_lib.unknown(*missing)
    waived = rules_lib.flag(escrow_waived)
    if waived is None:
        return rules_lib.unknown('LoanCore.is_escrow_waived')
    return not waived
