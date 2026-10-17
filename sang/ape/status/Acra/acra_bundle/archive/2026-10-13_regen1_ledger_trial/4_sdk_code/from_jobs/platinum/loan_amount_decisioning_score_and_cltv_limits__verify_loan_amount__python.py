# rule: acra-platinum.loan_amount_decisioning_score_and_cltv_limits.verify_loan_amount.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_amount_decisioning_score_and_cltv_limits.verify_loan_amount
# reads: loan_amount
# implements job: acra-platinum.loan_amount_decisioning_score_and_cltv_limits.verify_loan_amount

import rules_lib

def check(ctx):
    loan_amount = ctx['loan_amount']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)
    return 100000 <= loan_amount <= 2000000 and loan_amount % 50 == 0
