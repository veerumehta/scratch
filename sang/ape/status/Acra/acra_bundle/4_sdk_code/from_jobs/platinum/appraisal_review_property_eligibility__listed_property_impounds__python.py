# rule: acra-platinum.appraisal_review_property_eligibility.listed_property_impounds.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_property_impounds
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.is_escrow_waived
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_property_impounds

import rules_lib

def check(ctx):
    listed = rules_lib.flag(ctx['SubjectProperty.listed_for_sale_last_6_months'])
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    if not listed:
        return True
    escrow_waived = rules_lib.flag(ctx['LoanCore.is_escrow_waived'])
    missing = rules_lib.gaps(escrow_waived=escrow_waived)
    if missing:
        return rules_lib.unknown(*missing)
    return not escrow_waived
