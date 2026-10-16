# rule: acra-standard.credit_housing_history_and_escrow_waiver.review_escrow_waiver_eligibility.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_housing_history_and_escrow_waiver.review_escrow_waiver_eligibility
# reads: escrow_waiver_requested, loan_amount, cltv_pct, fico, mortgage_history_0x30x24, citizenship_type
# implements job: acra-standard.credit_housing_history_and_escrow_waiver.review_escrow_waiver_eligibility

import rules_lib


def check(ctx):
    escrow_waiver_requested = ctx['escrow_waiver_requested']
    missing = rules_lib.gaps(escrow_waiver_requested=escrow_waiver_requested)
    if missing:
        return rules_lib.unknown(*missing)

    escrow_waiver_requested = rules_lib.flag(escrow_waiver_requested)
    if escrow_waiver_requested is None:
        return rules_lib.unknown('escrow_waiver_requested')
    if not escrow_waiver_requested:
        return True

    loan_amount = ctx['loan_amount']
    cltv_pct = ctx['cltv_pct']
    fico = ctx['fico']
    mortgage_history_0x30x24 = ctx['mortgage_history_0x30x24']
    citizenship_type = ctx['citizenship_type']
    missing = rules_lib.gaps(
        loan_amount=loan_amount,
        cltv_pct=cltv_pct,
        fico=fico,
        mortgage_history_0x30x24=mortgage_history_0x30x24,
        citizenship_type=citizenship_type,
    )
    if missing:
        return rules_lib.unknown(*missing)

    mortgage_history_0x30x24 = rules_lib.flag(mortgage_history_0x30x24)
    if mortgage_history_0x30x24 is None:
        return rules_lib.unknown('mortgage_history_0x30x24')

    return (
        loan_amount <= 1500000
        and cltv_pct <= 80
        and fico >= 700
        and mortgage_history_0x30x24
        and not rules_lib.same(citizenship_type, 'Foreign National')
    )
