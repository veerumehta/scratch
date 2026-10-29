# rule: acra-platinum.credit_review_analysis.fthb_status.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis.fthb_status
# reads: Borrower.is_first_time_homebuyer
# implements job: acra-platinum.credit_review_analysis.fthb_status

import rules_lib

def check(ctx):
    is_first_time_homebuyer = ctx['Borrower.is_first_time_homebuyer']
    missing = rules_lib.gaps(is_first_time_homebuyer=is_first_time_homebuyer)
    if missing:
        return rules_lib.unknown(*missing)
    fthb = rules_lib.flag(is_first_time_homebuyer)
    if fthb is None:
        return rules_lib.unknown('is_first_time_homebuyer')
    return not fthb
