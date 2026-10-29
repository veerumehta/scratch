# rule: acra-platinum.title_review.prior_homeownership_experience.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.prior_homeownership_experience
# reads: Borrower.is_first_time_homebuyer
# implements job: acra-platinum.title_review.prior_homeownership_experience

import rules_lib

def check(ctx):
    first_time = ctx['Borrower.is_first_time_homebuyer']
    missing = rules_lib.gaps(first_time=first_time)
    if missing:
        return rules_lib.unknown(*missing)
    first_time_flag = rules_lib.flag(first_time)
    if first_time_flag is None:
        return rules_lib.unknown('Borrower.is_first_time_homebuyer')
    return not first_time_flag
