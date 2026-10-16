# rule: acra-platinum.funds_to_close_seasoning_and_reserves.escrow_waiver_and_listed_property_impounds.python
# origin: written from a job
# description: Python formalization of acra-platinum.funds_to_close_seasoning_and_reserves.escrow_waiver_and_listed_property_impounds
# reads: escrow_waiver_requested, loan_amount, mortgage_history_0x30x24
# implements job: acra-platinum.funds_to_close_seasoning_and_reserves.escrow_waiver_and_listed_property_impounds

import rules_lib

def check(ctx):
    escrow_waiver_requested = ctx['escrow_waiver_requested']
    waiver_requested = rules_lib.flag(escrow_waiver_requested)
    if waiver_requested is None:
        return rules_lib.unknown('escrow_waiver_requested')
    if not waiver_requested:
        return True

    loan_amount = ctx['loan_amount']
    mortgage_history_0x30x24 = ctx['mortgage_history_0x30x24']
    missing = rules_lib.gaps(
        loan_amount=loan_amount,
        mortgage_history_0x30x24=mortgage_history_0x30x24,
    )
    if missing:
        return rules_lib.unknown(*missing)

    mortgage_history_required = rules_lib.flag(mortgage_history_0x30x24)
    if mortgage_history_required is None:
        return rules_lib.unknown('mortgage_history_0x30x24')

    return loan_amount <= 1500000 and mortgage_history_required
