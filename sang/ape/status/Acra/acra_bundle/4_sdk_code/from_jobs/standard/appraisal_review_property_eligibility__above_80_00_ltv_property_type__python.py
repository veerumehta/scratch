# rule: acra-standard.appraisal_review_property_eligibility.above_80_00_ltv_property_type.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.above_80_00_ltv_property_type
# reads: LoanCore.cltv_percent, SubjectProperty.property_type, SubjectProperty.state
# implements job: acra-standard.appraisal_review_property_eligibility.above_80_00_ltv_property_type

import rules_lib

def check(ctx):
    ltv = rules_lib.percent(ctx['LoanCore.cltv_percent'], 'percent')
    missing = rules_lib.gaps(ltv=ltv)
    if missing:
        return rules_lib.unknown(*missing)

    if ltv <= 80.00:
        return True

    property_type = ctx['SubjectProperty.property_type']
    missing = rules_lib.gaps(property_type=property_type)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(property_type, 'SFR', 'Townhome', 'PUD'):
        return True
    if rules_lib.same(property_type, 'Warrantable Condo', 'Warrantable Condos'):
        state = ctx['SubjectProperty.state']
        missing = rules_lib.gaps(state=state)
        if missing:
            return rules_lib.unknown(*missing)
        return not rules_lib.same(state, 'Florida')
    return False
