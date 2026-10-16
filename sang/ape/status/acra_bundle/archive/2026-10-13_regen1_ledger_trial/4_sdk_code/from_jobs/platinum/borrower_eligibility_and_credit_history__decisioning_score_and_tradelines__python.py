# rule: acra-platinum.borrower_eligibility_and_credit_history.decisioning_score_and_tradelines.python
# origin: written from a job
# description: Python formalization of acra-platinum.borrower_eligibility_and_credit_history.decisioning_score_and_tradelines
# reads: fico
# implements job: acra-platinum.borrower_eligibility_and_credit_history.decisioning_score_and_tradelines

import rules_lib

def check(ctx):
    fico = ctx['fico']
    missing = rules_lib.gaps(fico=fico)
    if missing:
        return rules_lib.unknown(*missing)
    return fico >= 700
