# rule: acra-platinum.title_review.listed_property_maximum_ltv_cltv.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.listed_property_maximum_ltv_cltv
# reads: LoanCore.cltv_percent
# implements job: acra-platinum.title_review.listed_property_maximum_ltv_cltv

import rules_lib

def check(ctx):
    cltv_percent = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv_percent=cltv_percent)
    if missing:
        return rules_lib.unknown(*missing)
    return cltv_percent <= 65
