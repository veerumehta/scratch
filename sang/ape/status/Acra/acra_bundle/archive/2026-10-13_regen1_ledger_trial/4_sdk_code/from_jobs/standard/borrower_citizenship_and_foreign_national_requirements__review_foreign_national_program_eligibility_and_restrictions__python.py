# rule: acra-standard.borrower_citizenship_and_foreign_national_requirements.review_foreign_national_program_eligibility_and_restrictions.python
# origin: written from a job
# description: Python formalization of acra-standard.borrower_citizenship_and_foreign_national_requirements.review_foreign_national_program_eligibility_and_restrictions
# reads: citizenship_type, occupancy_subtype, loan_purpose, cltv_pct, escrow_waiver_requested
# implements job: acra-standard.borrower_citizenship_and_foreign_national_requirements.review_foreign_national_program_eligibility_and_restrictions

import rules_lib

def check(ctx):
    citizenship_type = ctx['citizenship_type']
    occupancy_subtype = ctx['occupancy_subtype']
    is_foreign_national = rules_lib.same(citizenship_type, 'Foreign National')

    if is_foreign_national:
        loan_purpose = ctx['loan_purpose']
        cltv_pct = ctx['cltv_pct']
        escrow_waiver_requested = ctx['escrow_waiver_requested']
        missing = rules_lib.gaps(
            citizenship_type=citizenship_type,
            occupancy_subtype=occupancy_subtype,
            loan_purpose=loan_purpose,
            cltv_pct=cltv_pct,
            escrow_waiver_requested=escrow_waiver_requested,
        )
    else:
        missing = rules_lib.gaps(
            citizenship_type=citizenship_type,
            occupancy_subtype=occupancy_subtype,
        )

    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(occupancy_subtype, 'investment', 'investment property'):
        return False

    if not is_foreign_national:
        return True

    is_purchase = rules_lib.same(loan_purpose, 'purchase')
    is_refinance = rules_lib.same(
        loan_purpose,
        'refinance',
        'rate & term',
        'rate & term refinance',
        'cash-out',
        'cash-out refinance',
    )
    if not is_purchase and not is_refinance:
        return rules_lib.unknown('loan_purpose')

    cltv_limit = 70 if is_purchase else 65
    within_cltv_limit = rules_lib.band(cltv_pct, [(cltv_limit, True)], above=False)
    if within_cltv_limit is None:
        return rules_lib.unknown('cltv_pct')

    escrow_waiver = rules_lib.flag(escrow_waiver_requested)
    if escrow_waiver is None:
        return rules_lib.unknown('escrow_waiver_requested')

    return within_cltv_limit and not escrow_waiver
