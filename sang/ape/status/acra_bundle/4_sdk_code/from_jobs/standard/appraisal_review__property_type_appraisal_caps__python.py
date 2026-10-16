# rule: acra-standard.appraisal_review.property_type_appraisal_caps.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review.property_type_appraisal_caps
# reads: SubjectProperty.property_type, LoanCore.cltv_percent, LoanCore.loan_purpose, SubjectProperty.state
# implements job: acra-standard.appraisal_review.property_type_appraisal_caps

import rules_lib

def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(property_type=property_type, cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    non_warrantable = rules_lib.same(property_type, 'Non-Warrantable Condo')
    condotel = rules_lib.same(property_type, 'Condotel / PUDtel')
    two_to_four = rules_lib.same(property_type, '2-4 Unit', '2-4 Units')
    manufactured = rules_lib.same(property_type, 'Manufactured Home', 'Manufactured')
    warrantable = rules_lib.same(property_type, 'Warrantable Condo', 'Warrantable Condos')

    limit = None
    state = None
    if non_warrantable or condotel or manufactured:
        purpose = ctx['LoanCore.loan_purpose']
        missing = rules_lib.gaps(purpose=purpose)
        if missing:
            return rules_lib.unknown(*missing)

        if rules_lib.same(purpose, 'purchase'):
            if non_warrantable:
                limit = 80
            elif condotel:
                limit = 75
            else:
                limit = 65
        elif rules_lib.same(purpose, 'refi r/t', 'refinance r/t'):
            if non_warrantable:
                limit = 75
            elif condotel:
                limit = 70
            else:
                limit = 60
        elif rules_lib.same(purpose, 'refi c/o', 'refinance c/o'):
            if non_warrantable:
                limit = 75
            elif condotel:
                limit = 65
            else:
                limit = 60
        else:
            return False

        if non_warrantable or condotel:
            state = ctx['SubjectProperty.state']
            missing = rules_lib.gaps(state=state)
            if missing:
                return rules_lib.unknown(*missing)
            if rules_lib.same(state, 'Florida', 'FL'):
                limit -= 5

    elif two_to_four:
        limit = 80

    if warrantable and cltv > 80.00:
        state = ctx['SubjectProperty.state']
        missing = rules_lib.gaps(state=state)
        if missing:
            return rules_lib.unknown(*missing)

    if limit is not None and cltv > limit:
        return False

    if cltv > 80.00:
        if rules_lib.same(property_type, 'SFR', 'Townhome', 'PUD'):
            return True
        if warrantable and not rules_lib.same(state, 'Florida', 'FL'):
            return True
        return False

    return True
