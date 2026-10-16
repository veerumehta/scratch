# rule: acra-platinum.credit_review_analysis.escrow_waiver.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis.escrow_waiver
# reads: LoanCore.is_escrow_waived, LoanCore.total_loan_amount_usd
# implements job: acra-platinum.credit_review_analysis.escrow_waiver

import rules_lib

def check(ctx):
    escrow_waived = ctx['LoanCore.is_escrow_waived']
    escrow_waived = rules_lib.flag(escrow_waived)
    if escrow_waived is None:
        return rules_lib.unknown('LoanCore.is_escrow_waived')
    if not escrow_waived:
        return True

    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)
    return loan_amount <= 1500000
