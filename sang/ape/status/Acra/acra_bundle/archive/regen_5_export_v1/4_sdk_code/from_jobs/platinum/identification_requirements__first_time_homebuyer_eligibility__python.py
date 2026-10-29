# rule: acra-platinum.identification_requirements.first_time_homebuyer_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.identification_requirements.first_time_homebuyer_eligibility
# reads: Borrower.is_first_time_homebuyer
# implements job: acra-platinum.identification_requirements.first_time_homebuyer_eligibility

import rules_lib

def check(ctx):
    is_first_time_homebuyer = ctx['Borrower.is_first_time_homebuyer']
    missing = rules_lib.gaps(is_first_time_homebuyer=is_first_time_homebuyer)
    if missing:
        return rules_lib.unknown(*missing)
    value = rules_lib.flag(is_first_time_homebuyer)
    if value is None:
        return rules_lib.unknown('Borrower.is_first_time_homebuyer')
    return value is False
