# rule: acra-standard.credit_review_analysis_credit.escrow_waiver_maximum_loan_amount.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis_credit.escrow_waiver_maximum_loan_amount
# reads: LoanCore.is_escrow_waived, LoanCore.total_loan_amount_usd
# implements job: acra-standard.credit_review_analysis_credit.escrow_waiver_maximum_loan_amount

import rules_lib

def check(ctx):
    waived = rules_lib.flag(ctx['LoanCore.is_escrow_waived'])
    missing = rules_lib.gaps(is_escrow_waived=waived)
    if missing:
        return rules_lib.unknown(*missing)
    if not waived:
        return True
    amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(total_loan_amount_usd=amount)
    if missing:
        return rules_lib.unknown(*missing)
    return amount <= 1500000
