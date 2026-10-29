# rule: acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability.python
# origin: written from a job
# description: Python formalization of acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability
# reads: SubjectProperty.number_of_units, LoanCore.cltv_percent
# implements job: acra-standard.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability

import rules_lib

def check(ctx):
    units = ctx['SubjectProperty.number_of_units']
    cltv = ctx['LoanCore.cltv_percent']

    missing = rules_lib.gaps(units=units, cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    return 1 <= units <= 4 and cltv <= 70
