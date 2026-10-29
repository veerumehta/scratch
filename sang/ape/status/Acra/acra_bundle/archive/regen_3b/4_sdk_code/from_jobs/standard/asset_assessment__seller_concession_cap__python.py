# rule: acra-standard.asset_assessment.seller_concession_cap.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.seller_concession_cap
# reads: LoanCore.seller_concession_percent
# implements job: acra-standard.asset_assessment.seller_concession_cap

import rules_lib

def check(ctx):
    seller_concession_percent = ctx['LoanCore.seller_concession_percent']
    missing = rules_lib.gaps(seller_concession_percent=seller_concession_percent)
    if missing:
        return rules_lib.unknown(*missing)
    return (seller_concession_percent <= 3, {'seller_concession_percent': seller_concession_percent, 'maximum_percent': 3})
