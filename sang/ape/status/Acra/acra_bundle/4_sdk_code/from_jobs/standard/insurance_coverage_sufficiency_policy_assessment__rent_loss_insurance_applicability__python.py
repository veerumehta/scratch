# rule: acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability.python
# origin: written from a job
# description: Python formalization of acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability
# reads: LoanCore.cltv_percent
# implements job: acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability

import rules_lib

def check(ctx):
    cltv_raw = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv_raw=cltv_raw)
    if missing:
        return rules_lib.unknown(*missing)
    cltv = rules_lib.percent(cltv_raw, 'percent')
    if cltv is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    return cltv <= 70
