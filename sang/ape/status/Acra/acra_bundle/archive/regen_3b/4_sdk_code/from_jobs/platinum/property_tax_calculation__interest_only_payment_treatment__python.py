# rule: acra-platinum.property_tax_calculation.interest_only_payment_treatment.python
# origin: written from a job
# description: Python formalization of acra-platinum.property_tax_calculation.interest_only_payment_treatment
# reads: MortgageLoanInformation.is_interest_only
# implements job: acra-platinum.property_tax_calculation.interest_only_payment_treatment

import rules_lib

def check(ctx):
    is_interest_only = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(is_interest_only=is_interest_only)
    if missing:
        return rules_lib.unknown(*missing)
    is_interest_only = rules_lib.flag(is_interest_only)
    if is_interest_only is None:
        return rules_lib.unknown('MortgageLoanInformation.is_interest_only')
    return is_interest_only
