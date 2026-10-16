# rule: acra-standard.funds_to_close_seasoning_and_reserves.loan_amount_concessions_and_applicant_funds.python
# origin: written from a job
# description: Python formalization of acra-standard.funds_to_close_seasoning_and_reserves.loan_amount_concessions_and_applicant_funds
# reads: loan_amount, seller_concession_pct
# implements job: acra-standard.funds_to_close_seasoning_and_reserves.loan_amount_concessions_and_applicant_funds

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
