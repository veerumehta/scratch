# rule: acra-platinum.loan_program_eligibility.product_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.product_eligibility
# reads: MortgageLoanInformation.is_interest_only, SubjectProperty.is_listed_for_sale
# implements job: acra-platinum.loan_program_eligibility.product_eligibility

import rules_lib

def check(ctx):
    interest_only = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(interest_only=interest_only)
    if missing:
        return rules_lib.unknown(*missing)
    interest_only = rules_lib.flag(interest_only)
    if interest_only is None:
        return rules_lib.unknown('interest_only')
    if not interest_only:
        return True

    listed_for_sale = ctx['SubjectProperty.is_listed_for_sale']
    missing = rules_lib.gaps(listed_for_sale=listed_for_sale)
    if missing:
        return rules_lib.unknown(*missing)
    listed_for_sale = rules_lib.flag(listed_for_sale)
    if listed_for_sale is None:
        return rules_lib.unknown('listed_for_sale')
    return not listed_for_sale
