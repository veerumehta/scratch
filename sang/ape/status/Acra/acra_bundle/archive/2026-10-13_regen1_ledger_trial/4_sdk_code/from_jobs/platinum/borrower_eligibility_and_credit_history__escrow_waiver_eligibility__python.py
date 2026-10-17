# rule: acra-platinum.borrower_eligibility_and_credit_history.escrow_waiver_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.borrower_eligibility_and_credit_history.escrow_waiver_eligibility
# reads: escrow_waiver_requested, loan_amount
# implements job: acra-platinum.borrower_eligibility_and_credit_history.escrow_waiver_eligibility

import rules_lib

def check(ctx):
    escrow_waiver_requested = ctx['escrow_waiver_requested']
    missing = rules_lib.gaps(escrow_waiver_requested=escrow_waiver_requested)
    if missing:
        return rules_lib.unknown(*missing)

    escrow_waiver_requested = rules_lib.flag(escrow_waiver_requested)
    if escrow_waiver_requested is None:
        return rules_lib.unknown('escrow_waiver_requested')
    if not escrow_waiver_requested:
        return True

    loan_amount = ctx['loan_amount']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)
    return loan_amount <= 1_500_000
