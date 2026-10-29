# rule: acra-platinum.unassigned_provisions.interest_only_minimum_loan_amount_and_fico.python
# origin: written from a job
# description: Python formalization of acra-platinum.unassigned_provisions.interest_only_minimum_loan_amount_and_fico
# reads: MortgageLoanInformation.is_interest_only
# implements job: acra-platinum.unassigned_provisions.interest_only_minimum_loan_amount_and_fico

import rules_lib

def check(ctx):
    is_interest_only = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(is_interest_only=is_interest_only)
    if missing:
        return rules_lib.unknown(*missing)

    value = rules_lib.flag(is_interest_only)
    if value is None:
        return rules_lib.unknown('MortgageLoanInformation.is_interest_only')
    return value
