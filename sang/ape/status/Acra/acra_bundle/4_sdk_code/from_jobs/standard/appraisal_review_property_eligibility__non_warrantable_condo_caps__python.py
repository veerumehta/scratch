# rule: acra-standard.appraisal_review_property_eligibility.non_warrantable_condo_caps.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.non_warrantable_condo_caps
# reads: SubjectProperty.property_type, LoanCore.loan_purpose, LoanCore.cltv_percent, SubjectProperty.state
# implements job: acra-standard.appraisal_review_property_eligibility.non_warrantable_condo_caps

import rules_lib


def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    if not rules_lib.known(property_type):
        return rules_lib.unknown('SubjectProperty.property_type')
    if not rules_lib.same(property_type, 'Non-Warrantable Condo'):
        return True

    purpose = ctx['LoanCore.loan_purpose']
    cltv_raw = ctx['LoanCore.cltv_percent']
    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(purpose=purpose, cltv=cltv_raw, state=state)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'Purchase'):
        cap = 80
    elif rules_lib.same(purpose, 'Refi R/T'):
        cap = 75
    elif rules_lib.same(purpose, 'Refi C/O'):
        cap = 75
    else:
        return rules_lib.unknown('LoanCore.loan_purpose')

    if rules_lib.same(state, 'Florida'):
        cap -= 5

    cltv = rules_lib.percent(cltv_raw, 'percent')
    if cltv is None:
        return rules_lib.unknown('LoanCore.cltv_percent')

    # The allowed case fields do not provide a DSCR value or define how to
    # calculate one, so the printed minimum DSCR condition remains for review.
    return (cltv <= cap, {'cltv_percent': cltv, 'cltv_cap_percent': cap, 'min_dscr_review': 1.0})
