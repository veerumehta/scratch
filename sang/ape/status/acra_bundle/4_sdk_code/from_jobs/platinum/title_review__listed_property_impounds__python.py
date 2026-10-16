# rule: acra-platinum.title_review.listed_property_impounds.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.listed_property_impounds
# reads: LoanCore.is_escrow_waived
# implements job: acra-platinum.title_review.listed_property_impounds

import rules_lib

def check(ctx):
    is_escrow_waived = rules_lib.flag(ctx['LoanCore.is_escrow_waived'])
    missing = rules_lib.gaps(is_escrow_waived=is_escrow_waived)
    if missing:
        return rules_lib.unknown(*missing)
    return not is_escrow_waived
