# rule: acra-platinum.loan_program_eligibility.first_time_homebuyer.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.first_time_homebuyer
# reads: Borrower.is_first_time_homebuyer
# implements job: acra-platinum.loan_program_eligibility.first_time_homebuyer

import rules_lib

def check(ctx):
    first_time_homebuyer = ctx['Borrower.is_first_time_homebuyer']
    missing = rules_lib.gaps(first_time_homebuyer=first_time_homebuyer)
    if missing:
        return rules_lib.unknown(*missing)
    first_time_homebuyer = rules_lib.flag(first_time_homebuyer)
    if first_time_homebuyer is None:
        return rules_lib.unknown('Borrower.is_first_time_homebuyer')
    return not first_time_homebuyer
