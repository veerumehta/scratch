# rule: acra-platinum.liabilities_assessment.listed_property_amortization.python
# origin: written from a job
# description: Python formalization of acra-platinum.liabilities_assessment.listed_property_amortization
# reads: SubjectProperty.listed_for_sale_last_6_months, MortgageLoanInformation.is_interest_only
# implements job: acra-platinum.liabilities_assessment.listed_property_amortization

import rules_lib


def check(ctx):
    listed = rules_lib.flag(ctx['SubjectProperty.listed_for_sale_last_6_months'])
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    if not listed:
        return True

    interest_only = rules_lib.flag(ctx['MortgageLoanInformation.is_interest_only'])
    missing = rules_lib.gaps(interest_only=interest_only)
    if missing:
        return rules_lib.unknown(*missing)
    return not interest_only
