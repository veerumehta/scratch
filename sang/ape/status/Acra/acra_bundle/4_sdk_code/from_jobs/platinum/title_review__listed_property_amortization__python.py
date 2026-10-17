# rule: acra-platinum.title_review.listed_property_amortization.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.listed_property_amortization
# reads: MortgageLoanInformation.is_interest_only
# implements job: acra-platinum.title_review.listed_property_amortization

import rules_lib

def check(ctx):
    interest_only = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(interest_only=interest_only)
    if missing:
        return rules_lib.unknown(*missing)
    interest_only = rules_lib.flag(interest_only)
    if interest_only is None:
        return rules_lib.unknown('interest_only')
    return not interest_only
