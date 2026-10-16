# rule: acra-platinum.borrower_eligibility_and_credit_history.borrower_citizenship_and_homeownership_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.borrower_eligibility_and_credit_history.borrower_citizenship_and_homeownership_eligibility
# reads: citizenship_type, first_time_homebuyer
# implements job: acra-platinum.borrower_eligibility_and_credit_history.borrower_citizenship_and_homeownership_eligibility

import rules_lib

def check(ctx):
    citizenship_type = ctx['citizenship_type']
    first_time_homebuyer = ctx['first_time_homebuyer']

    missing = rules_lib.gaps(
        citizenship_type=citizenship_type,
        first_time_homebuyer=first_time_homebuyer,
    )
    if missing:
        return rules_lib.unknown(*missing)

    is_first_time_homebuyer = rules_lib.flag(first_time_homebuyer)
    if is_first_time_homebuyer is None:
        return rules_lib.unknown('first_time_homebuyer')

    return (
        rules_lib.same(citizenship_type, 'US Citizen', 'Permanent Resident')
        and not is_first_time_homebuyer
    )
