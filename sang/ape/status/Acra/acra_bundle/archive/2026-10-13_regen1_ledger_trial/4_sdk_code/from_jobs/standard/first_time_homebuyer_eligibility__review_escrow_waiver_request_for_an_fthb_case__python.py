# rule: acra-standard.first_time_homebuyer_eligibility.review_escrow_waiver_request_for_an_fthb_case.python
# origin: written from a job
# description: Python formalization of acra-standard.first_time_homebuyer_eligibility.review_escrow_waiver_request_for_an_fthb_case
# reads: first_time_homebuyer, escrow_waiver_requested
# implements job: acra-standard.first_time_homebuyer_eligibility.review_escrow_waiver_request_for_an_fthb_case

import rules_lib

def check(ctx):
    first_time_homebuyer = ctx['first_time_homebuyer']
    escrow_waiver_requested = ctx['escrow_waiver_requested']

    missing = rules_lib.gaps(
        first_time_homebuyer=first_time_homebuyer,
        escrow_waiver_requested=escrow_waiver_requested,
    )
    if missing:
        return rules_lib.unknown(*missing)

    first_time_homebuyer = rules_lib.flag(first_time_homebuyer)
    escrow_waiver_requested = rules_lib.flag(escrow_waiver_requested)
    if first_time_homebuyer is None or escrow_waiver_requested is None:
        unresolved = []
        if first_time_homebuyer is None:
            unresolved.append('first_time_homebuyer')
        if escrow_waiver_requested is None:
            unresolved.append('escrow_waiver_requested')
        return rules_lib.unknown(*unresolved)

    return first_time_homebuyer and escrow_waiver_requested
