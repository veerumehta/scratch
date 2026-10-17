# rule: acra-standard.loan_amount_fico_and_matrix_leverage.loan_amount_and_seller_concessions.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_amount_fico_and_matrix_leverage.loan_amount_and_seller_concessions
# reads: loan_amount, seller_concession_pct
# implements job: acra-standard.loan_amount_fico_and_matrix_leverage.loan_amount_and_seller_concessions

import rules_lib

def check(ctx):
    loan_amount = ctx['loan_amount']
    seller_concession_pct = ctx['seller_concession_pct']
    missing = rules_lib.gaps(loan_amount=loan_amount, seller_concession_pct=seller_concession_pct)
    if missing:
        return rules_lib.unknown(*missing)
    return (
        loan_amount >= 100000
        and loan_amount <= 3000000
        and loan_amount % 50 == 0
        and seller_concession_pct <= 3
    )
