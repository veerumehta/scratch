# rule: acra-standard.appraisal_review_property_eligibility.listed_property_eligibility_conditions.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.listed_property_eligibility_conditions
# reads: LoanCore.cltv_percent, RatioSet.reserves_months, RatioSet.total_monthly_obligation_usd, RatioSet.total_monthly_income_usd, MortgageLoanInformation.is_interest_only, LoanCore.is_escrow_waived, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant
# implements job: acra-standard.appraisal_review_property_eligibility.listed_property_eligibility_conditions

import rules_lib


def check(ctx):
    cltv = ctx['LoanCore.cltv_percent']
    reserves = ctx['RatioSet.reserves_months']
    obligations = ctx['RatioSet.total_monthly_obligation_usd']
    income = ctx['RatioSet.total_monthly_income_usd']
    interest_only = ctx['MortgageLoanInformation.is_interest_only']
    escrow_waived = ctx['LoanCore.is_escrow_waived']
    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']

    missing = rules_lib.gaps(
        cltv=cltv,
        reserves=reserves,
        obligations=obligations,
        income=income,
        interest_only=interest_only,
        escrow_waived=escrow_waived,
        occupancy_subtype=occupancy_subtype,
    )
    if missing:
        return rules_lib.unknown(*missing)

    failures = []
    undecided = []

    cltv_percent = rules_lib.percent(cltv, 'percent')
    ltv_ok = rules_lib.band(cltv_percent, [(65, True)], above=False)
    if ltv_ok is None:
        undecided.append('cltv')
    elif not ltv_ok:
        failures.append('cltv')

    # The 24-month minimum is inclusive; band alone puts its upper edge
    # in the first band, so explicitly accept equality.
    reserves_ok = rules_lib.band(reserves, [(24, False)], above=True)
    if rules_lib.close(reserves, 24) is True:
        reserves_ok = True
    if reserves_ok is None:
        undecided.append('reserves')
    elif not reserves_ok:
        failures.append('reserves')

    interest_only_flag = rules_lib.flag(interest_only)
    if interest_only_flag is None:
        undecided.append('interest_only')
    elif interest_only_flag:
        failures.append('interest_only')

    escrow_waived_flag = rules_lib.flag(escrow_waived)
    if escrow_waived_flag is None:
        undecided.append('escrow_waived')
    elif escrow_waived_flag:
        failures.append('escrow_waived')

    if rules_lib.same(occupancy_subtype, 'investment'):
        has_current_lease = ctx['SubjectProperty.has_current_lease']
        is_vacant = ctx['SubjectProperty.is_vacant']
        missing = rules_lib.gaps(
            has_current_lease=has_current_lease,
            is_vacant=is_vacant,
        )
        if missing:
            return rules_lib.unknown(*missing)
        lease_flag = rules_lib.flag(has_current_lease)
        vacant_flag = rules_lib.flag(is_vacant)
        if lease_flag is None:
            undecided.append('has_current_lease')
        elif not lease_flag:
            failures.append('has_current_lease')
        if vacant_flag is None:
            undecided.append('is_vacant')
        elif vacant_flag:
            failures.append('is_vacant')

    dti_ratio = rules_lib.ratio(obligations, income)
    dti_percent = None if dti_ratio is None else dti_ratio * 100
    dti_ok = rules_lib.band(dti_percent, [(43, True)], above=False)
    if dti_ok is None:
        undecided.append('DTI qualification')
    elif not dti_ok:
        undecided.append('DSCR qualification')

    if failures:
        return False
    if undecided:
        return rules_lib.unknown(*undecided)
    return True
