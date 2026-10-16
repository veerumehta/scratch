# rule: acra-platinum.credit_review_analysis.property_listed_for_sale.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis.property_listed_for_sale
# reads: SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months, MortgageLoanInformation.is_interest_only, LoanCore.is_escrow_waived, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant
# implements job: acra-platinum.credit_review_analysis.property_listed_for_sale

import rules_lib

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    listed_flag = rules_lib.flag(listed)
    if listed_flag is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')

    if not listed_flag:
        return (True, {'subject_to_listed_for_sale_requirements': False})

    reserves = ctx['RatioSet.reserves_months']
    interest_only = ctx['MortgageLoanInformation.is_interest_only']
    escrow_waived = ctx['LoanCore.is_escrow_waived']
    occupancy = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(
        reserves=reserves,
        interest_only=interest_only,
        escrow_waived=escrow_waived,
        occupancy=occupancy,
    )
    if missing:
        return rules_lib.unknown(*missing)

    interest_only_flag = rules_lib.flag(interest_only)
    escrow_waived_flag = rules_lib.flag(escrow_waived)
    if interest_only_flag is None:
        return rules_lib.unknown('interest_only')
    if escrow_waived_flag is None:
        return rules_lib.unknown('escrow_waived')

    reserve_ok = reserves >= 24
    interest_ok = not interest_only_flag
    impounds_ok = not escrow_waived_flag
    results = {
        'subject_to_listed_for_sale_requirements': True,
        'reserves_at_least_24_months': reserve_ok,
        'not_interest_only': interest_ok,
        'impounds_provided': impounds_ok,
    }

    if rules_lib.same(occupancy, 'investment', 'investment property'):
        has_lease = ctx['SubjectProperty.has_current_lease']
        vacant = ctx['SubjectProperty.is_vacant']
        missing = rules_lib.gaps(has_lease=has_lease, vacant=vacant)
        if missing:
            return rules_lib.unknown(*missing)
        has_lease_flag = rules_lib.flag(has_lease)
        vacant_flag = rules_lib.flag(vacant)
        if has_lease_flag is None:
            return rules_lib.unknown('has_current_lease')
        if vacant_flag is None:
            return rules_lib.unknown('is_vacant')
        results['investment_tenant_occupied_and_not_vacant'] = has_lease_flag and not vacant_flag

    return (all(value for key, value in results.items() if key != 'subject_to_listed_for_sale_requirements'), results)
