# rule: acra-standard.appraisal_review_property_eligibility.2_4_unit_cltv_cap.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.2_4_unit_cltv_cap
# reads: SubjectProperty.property_type, LoanCore.cltv_percent
# implements job: acra-standard.appraisal_review_property_eligibility.2_4_unit_cltv_cap

import rules_lib

def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    cltv_percent = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(property_type=property_type, cltv_percent=cltv_percent)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(property_type, '2-4 Unit', '2-4 Units'):
        return True

    cltv = rules_lib.percent(cltv_percent, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv_percent')
    return cltv <= 80
