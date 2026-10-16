# rule: acra-standard.appraisal_review.listed_property_appraisal_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review.listed_property_appraisal_limits
# reads: SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant, MortgageLoanInformation.is_interest_only, LoanCore.cltv_percent
# implements job: acra-standard.appraisal_review.listed_property_appraisal_limits

import rules_lib

def check(ctx):
    listed_raw = ctx['SubjectProperty.listed_for_sale_last_6_months']
    listed = rules_lib.flag(listed_raw)
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    if not listed:
        return True

    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    investment = rules_lib.same(occupancy_subtype, 'investment')

    if investment:
        lease = rules_lib.flag(ctx['SubjectProperty.has_current_lease'])
        vacant = rules_lib.flag(ctx['SubjectProperty.is_vacant'])
    else:
        lease = None
        vacant = None

    interest_only = rules_lib.flag(ctx['MortgageLoanInformation.is_interest_only'])
    cltv = ctx['LoanCore.cltv_percent']
    cltv_within_limit = rules_lib.band(cltv, [(65, True)], above=False)

    missing = rules_lib.gaps(
        lease=lease if investment else True,
        vacant=vacant if investment else False,
        interest_only=interest_only,
        cltv_within_limit=cltv_within_limit,
    )
    if missing:
        return rules_lib.unknown(*missing)

    return (
        (not investment or (lease and not vacant))
        and not interest_only
        and cltv_within_limit
    )
