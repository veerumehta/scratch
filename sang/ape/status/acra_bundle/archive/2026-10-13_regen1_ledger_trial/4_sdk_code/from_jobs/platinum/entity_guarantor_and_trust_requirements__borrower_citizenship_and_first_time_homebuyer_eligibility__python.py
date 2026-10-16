# rule: acra-platinum.entity_guarantor_and_trust_requirements.borrower_citizenship_and_first_time_homebuyer_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.entity_guarantor_and_trust_requirements.borrower_citizenship_and_first_time_homebuyer_eligibility
# reads: citizenship_type, first_time_homebuyer
# implements job: acra-platinum.entity_guarantor_and_trust_requirements.borrower_citizenship_and_first_time_homebuyer_eligibility

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

    first_time = rules_lib.flag(first_time_homebuyer)
    if first_time is None:
        return rules_lib.unknown('first_time_homebuyer')

    eligible_citizenship = rules_lib.same(
        citizenship_type, 'US Citizen', 'Permanent Resident'
    )
    return eligible_citizenship and not first_time
