# rule: acra-platinum.loan_program_eligibility.interest_only_listed_for_sale_restriction.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.interest_only_listed_for_sale_restriction
# reads: MortgageLoanInformation.is_interest_only, SubjectProperty.is_listed_for_sale
# implements job: acra-platinum.loan_program_eligibility.interest_only_listed_for_sale_restriction

import rules_lib

def check(ctx):
    interest_only = rules_lib.flag(ctx['MortgageLoanInformation.is_interest_only'])
    listed_for_sale = rules_lib.flag(ctx['SubjectProperty.is_listed_for_sale'])
    missing = rules_lib.gaps(interest_only=interest_only, listed_for_sale=listed_for_sale)
    if missing:
        return rules_lib.unknown(*missing)
    return not interest_only or not listed_for_sale
