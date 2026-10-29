# rule: acra-platinum.appraisal_review_property_eligibility.listed_property_amortization.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_property_amortization
# reads: SubjectProperty.listed_for_sale_last_6_months, MortgageLoanInformation.is_interest_only
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_property_amortization

import rules_lib

def check(ctx):
    listed_raw = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed_raw)
    if missing:
        return rules_lib.unknown(*missing)
    listed = rules_lib.flag(listed_raw)
    if listed is None:
        return rules_lib.unknown('SubjectProperty.listed_for_sale_last_6_months')
    if not listed:
        return True

    interest_only_raw = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(interest_only=interest_only_raw)
    if missing:
        return rules_lib.unknown(*missing)
    interest_only = rules_lib.flag(interest_only_raw)
    if interest_only is None:
        return rules_lib.unknown('MortgageLoanInformation.is_interest_only')
    return not interest_only
