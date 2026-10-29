# rule: acra-platinum.appraisal_review_property_eligibility.listed_property_lien_status.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_property_lien_status
# reads: SubjectProperty.listed_for_sale_last_6_months
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_property_lien_status

import rules_lib

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    listed_flag = rules_lib.flag(listed)
    if listed_flag is None:
        return rules_lib.unknown('SubjectProperty.listed_for_sale_last_6_months')
    if not listed_flag:
        return True
    return rules_lib.unknown('lien_status')
