# rule: acra-standard.appraisal_review_property_eligibility.manufactured_home_caps.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.manufactured_home_caps
# reads: SubjectProperty.property_type, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.appraisal_review_property_eligibility.manufactured_home_caps

import rules_lib


def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    missing = rules_lib.gaps(property_type=property_type)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(property_type, 'Manufactured', 'Manufactured Home'):
        return True

    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'Purchase'):
        cap = 65
    elif rules_lib.same(loan_purpose, 'Refi R/T'):
        cap = 60
    elif rules_lib.same(loan_purpose, 'Refi C/O'):
        cap = 60
    else:
        return True

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    cltv_percent = rules_lib.percent(cltv, 'percent')
    if cltv_percent is None:
        return rules_lib.unknown('cltv')
    return cltv_percent <= cap
