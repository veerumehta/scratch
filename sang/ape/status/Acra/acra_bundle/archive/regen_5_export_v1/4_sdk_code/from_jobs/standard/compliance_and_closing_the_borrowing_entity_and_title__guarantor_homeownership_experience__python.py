# rule: acra-standard.compliance_and_closing_the_borrowing_entity_and_title.guarantor_homeownership_experience.python
# origin: written from a job
# description: Python formalization of acra-standard.compliance_and_closing_the_borrowing_entity_and_title.guarantor_homeownership_experience
# reads: Borrower.is_first_time_homebuyer
# implements job: acra-standard.compliance_and_closing_the_borrowing_entity_and_title.guarantor_homeownership_experience

import rules_lib

def check(ctx):
    borrower_is_first_time_homebuyer = ctx['Borrower.is_first_time_homebuyer']
    missing = rules_lib.gaps(borrower_is_first_time_homebuyer=borrower_is_first_time_homebuyer)
    if missing:
        return rules_lib.unknown(*missing)

    attested_status = rules_lib.flag(borrower_is_first_time_homebuyer)
    if attested_status is None:
        return rules_lib.unknown('borrower_is_first_time_homebuyer')
    return not attested_status
