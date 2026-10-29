# rule: acra-platinum.appraisal_review_property_eligibility.listed_property_maximum_ltv_cltv.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_property_maximum_ltv_cltv
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.cltv_percent
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_property_maximum_ltv_cltv

import rules_lib


def check(ctx):
    listed = rules_lib.flag(ctx['SubjectProperty.listed_for_sale_last_6_months'])
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    if not listed:
        return True

    cltv = rules_lib.percent(ctx['LoanCore.cltv_percent'], 'percent')
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)
    return cltv <= 65
