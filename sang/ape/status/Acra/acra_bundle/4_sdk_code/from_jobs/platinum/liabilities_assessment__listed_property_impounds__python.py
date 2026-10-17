# rule: acra-platinum.liabilities_assessment.listed_property_impounds.python
# origin: written from a job
# description: Python formalization of acra-platinum.liabilities_assessment.listed_property_impounds
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.is_escrow_waived
# implements job: acra-platinum.liabilities_assessment.listed_property_impounds

import rules_lib

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)

    listed = rules_lib.flag(listed)
    if listed is None:
        return rules_lib.unknown('SubjectProperty.listed_for_sale_last_6_months')
    if not listed:
        return True

    waived = ctx['LoanCore.is_escrow_waived']
    missing = rules_lib.gaps(waived=waived)
    if missing:
        return rules_lib.unknown(*missing)

    waived = rules_lib.flag(waived)
    if waived is None:
        return rules_lib.unknown('LoanCore.is_escrow_waived')
    return not waived
