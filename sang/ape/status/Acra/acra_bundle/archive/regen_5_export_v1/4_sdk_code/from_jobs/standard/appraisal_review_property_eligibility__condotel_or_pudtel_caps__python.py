# rule: acra-standard.appraisal_review_property_eligibility.condotel_or_pudtel_caps.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.condotel_or_pudtel_caps
# reads: SubjectProperty.property_type, LoanCore.loan_purpose, LoanCore.cltv_percent, SubjectProperty.state
# implements job: acra-standard.appraisal_review_property_eligibility.condotel_or_pudtel_caps

import rules_lib

def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    missing = rules_lib.gaps(property_type=property_type)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(property_type, 'Condotel / PUDtel'):
        return True

    loan_purpose = ctx['LoanCore.loan_purpose']
    cltv_percent = ctx['LoanCore.cltv_percent']
    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(loan_purpose=loan_purpose, cltv_percent=cltv_percent, state=state)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'Purchase'):
        cap = 75
    elif rules_lib.same(loan_purpose, 'Refi R/T'):
        cap = 70
    elif rules_lib.same(loan_purpose, 'Refi C/O'):
        cap = 65
    else:
        return rules_lib.unknown('LoanCore.loan_purpose')

    cltv = rules_lib.percent(cltv_percent, 'percent')
    if cltv is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    if rules_lib.same(state, 'Florida', 'FL'):
        cap -= 5
    return cltv <= cap
