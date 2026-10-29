# rule: acra-standard.asset_assessment.funds_seasoning_verification_trigger.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.funds_seasoning_verification_trigger
# reads: LoanCore.cltv_percent, LoanCore.loan_purpose
# implements job: acra-standard.asset_assessment.funds_seasoning_verification_trigger

import rules_lib

def check(ctx):
    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    over_70 = rules_lib.band(cltv, [(70, False)], above=True)
    if over_70 is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    if not over_70:
        return False

    purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)
    if rules_lib.same(purpose, 'consumer transaction'):
        return True
    if rules_lib.same(purpose, 'business purpose'):
        return rules_lib.unknown('funds_to_close')
    return rules_lib.unknown('consumer_or_business_classification')
